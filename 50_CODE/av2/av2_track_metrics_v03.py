#!/usr/bin/env python3
"""av2_track_metrics_v03 (v02 + a counting accumulator, 1 Nov 2026): at every recall threshold the CLEAR counts
(matches, switches, misses, false positives, objects, frames) come from CountAcc, a line-for-line copy of
motmetrics.mot.MOTAccumulator.update (CANMOT's vendored motmetrics 1.1.3: carry forward previous pairs, then the same
motmetrics.lap.linear_sum_assignment on the same masked distance matrix, SWITCH if the object's previous hypothesis differs)
that keeps counts instead of a pandas event table. MOTAR, MOTA, recall (= (matches + switches) / objects) and FAF follow the
devkit / motmetrics formulas. The motmetrics accumulator (v02's Acc) is used once, at the best-MOTA threshold, for
MT, ML, FRAG, TID, LGD and as a cross-check of the counts there. Validated on nuScenes val against CANMOT's reference.

av2_track_metrics_v02 (v01 + two exact speed-ups, 1 Nov 2026): (i) the per-frame 'RAW' events (all object x hypothesis
pairs) are dropped from the accumulator right after each update: none of the metrics computed here reads them (they use
df.noraw; num_frames' frame set is unchanged because every updated frame also has a MATCH/SWITCH/MISS/FP event);
(ii) the per-object metrics (MT, ML, FRAG, TID, LGD; loops over objects) are computed only at the best-MOTA threshold, the
only place they are reported; the threshold choice uses MOTA, which is computed at every threshold. Validated against
CANMOT's reference evaluation on nuScenes val like v01.

av2_track_metrics_v01: nuScenes-protocol tracking metrics (AMOTA, MOTA, MOTAR, recall, TP/FP/FN, IDS, FRAG, MT/ML, FAF)
for exports in the x1_export_v06 format, on Argoverse 2 or nuScenes ground truth in the x1_gt_prep format
(Claude line, 1 Nov 2026). Shim S6 of AV2_TRACKER_PORT_DESIGN_v01.md.

Why a re-implementation: CANMOT's modified devkit computes NEES, Mahalanobis inside/outside shares and a chi-square test
on every matched true positive inside TrackingEvaluation.accumulate_threshold (an outcome quantity under D15 section 4),
and the av2 tracking evaluator is not installed. This module follows the devkit's tracking_nips_2019 protocol step by step
(nuscenes/eval/common/loaders.filter_eval_boxes; nuscenes/eval/tracking/loaders.create_tracks and interpolate_tracks;
nuscenes/eval/tracking/algo.TrackingEvaluation.accumulate / accumulate_threshold / compute_thresholds;
nuscenes/eval/tracking/evaluate.TrackingEval.evaluate aggregation) and uses the devkit's own MOTAccumulatorCustom and
create_motmetrics, but computes ONLY the CLEAR/AMOTA counts: no NEES, no TP translation/scale/orientation/velocity errors,
no MOTP/AMOTP (the localisation means are not computed, so no distance summary leaves this module).
Only the centre-distance matching itself uses distances (2 m gate), as every tracking metric does.

Protocol: classes bicycle, bus, car, motorcycle, pedestrian, trailer, truck; class ranges 50/40 m (BEV distance from the
ego pose translation, strict <); GT boxes with num_pts == 0 removed; bicycle/motorcycle boxes whose centre lies in a
bicycle rack removed (BEV test; AV2 has no racks); prediction scores averaged per track; GT and predicted tracks
interpolated over missing frames exactly as the devkit; 40 recall thresholds from 0.1; centre distance < 2 m.
Validation: on the nuScenes val export of T1 this reproduces CANMOT's reference evaluation (see --check-reference).

Usage: python -I -B av2_track_metrics_v01.py --gt <gt json> --exports <worker dirs...> --out <json> [--check-reference <json>]
"""
import argparse
import gzip
import json
import math
import os
import sys
import time
import warnings
from bisect import bisect
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import av2_common_v01 as C  # noqa: E402

sys.path.insert(0, os.path.join(C.W_ROOT, "50_CODE", "third_party", "CANMOT", "src"))
import canmot  # noqa: E402,F401  (puts the pinned devkit on sys.path)
from nuscenes.eval.tracking.mot import MOTAccumulatorCustom  # noqa: E402
from nuscenes.eval.tracking.utils import create_motmetrics  # noqa: E402

CLASSES = ["bicycle", "bus", "car", "motorcycle", "pedestrian", "trailer", "truck"]
CLASS_RANGE = C.CLASS_RANGE
DIST_TH = 2.0
MIN_RECALL = 0.1
NUM_THRESHOLDS = 40
# MOT_METRIC_MAP of the devkit without 'motp_custom' (MOTP is a localisation mean; not computed here)
MOT_METRIC_MAP = {"num_frames": "", "num_objects": "gt", "num_predictions": "", "num_matches": "tp", "motar": "motar",
                  "mota_custom": "mota", "faf": "faf", "mostly_tracked": "mt", "mostly_lost": "ml",
                  "num_false_positives": "fp", "num_misses": "fn", "num_switches": "ids",
                  "num_fragmentations_custom": "frag", "recall": "recall", "tid": "tid", "lgd": "lgd"}
PER_OBJECT = ("mostly_tracked", "mostly_lost", "num_fragmentations_custom", "tid", "lgd")
CHEAP = [k for k in MOT_METRIC_MAP if k not in PER_OBJECT]


class Acc(MOTAccumulatorCustom):
    """MOTAccumulatorCustom without the RAW events (speed-up (i))."""

    def update(self, oids, hids, dists, frameid=None):
        n0 = len(self._events)
        r = super().update(oids, hids, dists, frameid=frameid)
        keep = [k for k in range(n0, len(self._events)) if self._events[k][0] != "RAW"]
        self._events[n0:] = [self._events[k] for k in keep]
        self._indices[n0:] = [self._indices[k] for k in keep]
        self.dirty_events = True
        return r



class CountAcc:
    """motmetrics.mot.MOTAccumulator.update (max_switch_time = inf), counts only."""

    def __init__(self):
        from motmetrics.lap import linear_sum_assignment
        self.lsa = linear_sum_assignment
        self.m, self.last = {}, {}
        self.c = {"MATCH": 0, "SWITCH": 0, "MISS": 0, "FP": 0, "frames": 0}

    def update(self, oids, hids, dists):
        """Returns the hypothesis ids of this frame's MATCH events (not SWITCH)."""
        no, nh = len(oids), len(hids)
        self.c["frames"] += 1
        dists = np.atleast_2d(dists).astype(float).reshape(no, nh).copy()
        om, hm = [False] * no, [False] * nh
        matched_h = []
        if no * nh > 0:
            for i in range(no):
                if oids[i] not in self.m:
                    continue
                hprev = self.m[oids[i]]
                js = [j for j in range(nh) if not hm[j] and hids[j] == hprev]
                if not js:
                    continue
                j = js[0]
                if np.isfinite(dists[i, j]):
                    om[i], hm[j] = True, True
                    self.m[oids[i]] = hids[j]
                    self.c["MATCH"] += 1
                    matched_h.append(hids[j])
            dists[np.array(om, bool), :] = np.nan
            dists[:, np.array(hm, bool)] = np.nan
            rids, cids = self.lsa(dists)
            for i, j in zip(rids, cids):
                if not np.isfinite(dists[i, j]):
                    continue
                o, h = oids[i], hids[j]
                cat = "SWITCH" if (o in self.m and self.m[o] != h) else "MATCH"
                self.c[cat] += 1
                if cat == "MATCH":
                    matched_h.append(h)
                om[i], hm[j] = True, True
                self.m[o] = h
        self.c["MISS"] += om.count(False)
        self.c["FP"] += hm.count(False)
        return matched_h


def counts_threshold(tracks_gt, tracks_pred, cls, threshold):
    from sklearn.metrics.pairwise import euclidean_distances
    tot = {"MATCH": 0, "SWITCH": 0, "MISS": 0, "FP": 0, "frames": 0}
    scores = []
    for sc in tracks_gt:
        acc = CountAcc()
        sg, sp = tracks_gt[sc], tracks_pred[sc]
        for ts in sg.keys():
            fg = [b for b in sg[ts] if b.name == cls]
            fp = [b for b in sp[ts] if b.name == cls]
            if threshold is not None:
                fp = [b for b in fp if b.score >= threshold]
            gids, pids = [b.tid for b in fg], [b.tid for b in fp]
            if not gids and not pids:
                continue
            if not fg or not fp:
                d = np.ones((0, 0))
            else:
                d = euclidean_distances(np.array([[b.x, b.y] for b in fg]), np.array([[b.x, b.y] for b in fp]))
            d[d >= DIST_TH] = np.nan
            mh_ = acc.update(gids, pids, d)
            if threshold is None:
                mids = set(mh_)
                scores.extend([b.score for b in fp if b.tid in mids])
        for k in tot:
            tot[k] += acc.c[k]
    return tot, scores


def cheap_from_counts(c):
    nm, ns, nmiss, nfp, nfr = c["MATCH"], c["SWITCH"], c["MISS"], c["FP"], c["frames"]
    nobj = nm + ns + nmiss
    rec = nm / nobj if nobj else float("nan")
    den = rec * nobj
    motar = float("nan") if den == 0 or nobj == 0 else max(0.0, 1 - ((nmiss + ns + nfp) - (1 - rec) * nobj) / den)
    return {"gt": float(nobj), "tp": float(nm), "motar": motar,
            "mota": max(0.0, 1.0 - (nmiss + ns + nfp) / nobj) if nobj else float("nan"),
            "faf": nfp / nfr * 100 if nfr else float("nan"), "fp": float(nfp), "fn": float(nmiss), "ids": float(ns),
            "recall": (nm + ns) / nobj if nobj else float("nan")}

METRIC_WORST = {"amota": 0.0, "recall": 0.0, "motar": 0.0, "mota": 0.0, "mt": 0.0, "ml": -1.0, "faf": 500, "gt": -1,
                "tp": 0.0, "fp": -1.0, "fn": -1.0, "ids": -1.0, "frag": -1.0, "tid": 20, "lgd": 20}


def in_rect(px, py, cx, cy, yaw, length, width):
    c, s = math.cos(yaw), math.sin(yaw)
    dx, dy = px - cx, py - cy
    return abs(c * dx + s * dy) <= length / 2 and abs(-s * dx + c * dy) <= width / 2


class Box:
    __slots__ = ("tid", "name", "x", "y", "score")

    def __init__(self, tid, name, x, y, score):
        self.tid, self.name, self.x, self.y, self.score = tid, name, x, y, score


def load_gt_tracks(gt_path):
    g = json.load(open(gt_path))
    samples = {s["token"]: s for s in g["samples"]}
    racks = defaultdict(list)
    for r in g.get("bicycle_racks", []):
        racks[r["sample_token"]].append(r)
    scene_ts = defaultdict(list)
    for s in g["samples"]:
        scene_ts[s["scene"]].append((s["index"], s["timestamp"], s["token"]))
    for sc in scene_ts:
        scene_ts[sc].sort()
    by_sample = defaultdict(list)
    n_in, n_kept = 0, 0
    for a in g["annotations"]:
        if a["tracking_name"] not in CLASSES:
            continue
        n_in += 1
        smp = samples[a["sample_token"]]
        ex, ey = smp["ego_xyz"][0], smp["ego_xyz"][1]
        if not math.hypot(a["translation"][0] - ex, a["translation"][1] - ey) < CLASS_RANGE[a["tracking_name"]]:
            continue
        if a["num_pts"] == 0:
            continue
        if a["tracking_name"] in ("bicycle", "motorcycle") and any(
                in_rect(a["translation"][0], a["translation"][1], q["translation"][0], q["translation"][1], q["yaw"], q["size"][1], q["size"][0])
                for q in racks.get(a["sample_token"], [])):
            continue
        n_kept += 1
        by_sample[a["sample_token"]].append(Box(a["instance_token"], a["tracking_name"], a["translation"][0], a["translation"][1], -1.0))
    del g
    return samples, racks, scene_ts, by_sample, {"gt_boxes_tracking_classes": n_in, "gt_boxes_after_filters": n_kept}


def load_pred_tracks(worker_dirs, samples, racks):
    by_sample = defaultdict(list)
    n_in, n_kept, tokens = 0, 0, set()
    for w in worker_dirs:
        rec = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert rec["status_X1_gates"] == "PASS", "export failed its gates: " + w
        for p in json.load(open(os.path.join(w, "x1_per_frame.json"))):
            if not p.get("error"):
                tokens.add(p["token"])
        with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                n_in += 1
                smp = samples[r["sample_token"]]
                nm = r["tracking_name"]
                x, y = r["translation"][0], r["translation"][1]
                if not math.hypot(x - smp["ego_xyz"][0], y - smp["ego_xyz"][1]) < CLASS_RANGE[nm]:
                    continue
                if nm in ("bicycle", "motorcycle") and any(
                        in_rect(x, y, q["translation"][0], q["translation"][1], q["yaw"], q["size"][1], q["size"][0])
                        for q in racks.get(r["sample_token"], [])):
                    continue
                n_kept += 1
                by_sample[r["sample_token"]].append(Box(r["tracking_id"], nm, x, y, float(r["tracking_score"])))
    return by_sample, tokens, {"pred_boxes_in": n_in, "pred_boxes_after_filters": n_kept}


def create_tracks(by_sample, scene_ts, gt):
    """devkit create_tracks + interpolate_tracks (translation and score are the only fields the metrics read)."""
    tracks = {}
    for sc, lst in scene_ts.items():
        st = {ts: list(by_sample.get(tok, [])) for _, ts, tok in lst}
        if not gt:
            sc_scores = defaultdict(list)
            for boxes in st.values():
                for b in boxes:
                    sc_scores[b.tid].append(b.score)
            avg = {k: float(np.mean(v)) for k, v in sc_scores.items()}
            for boxes in st.values():
                for b in boxes:
                    b.score = avg[b.tid]
        by_id, ts_by_id = defaultdict(list), defaultdict(list)
        for ts, boxes in st.items():
            for b in boxes:
                by_id[b.tid].append(b)
                ts_by_id[b.tid].append(ts)
        for ts in list(st.keys()):
            for tid, tr in by_id.items():
                tl = ts_by_id[tid]
                if tl[0] <= ts <= tl[-1] and ts not in tl:
                    ri = bisect(tl, ts)
                    li = ri - 1
                    rr = float(tl[ri] - ts) / (tl[ri] - tl[li])
                    lb, rb = tr[li], tr[ri]
                    st[ts].append(Box(rb.tid, rb.name, (1.0 - rr) * lb.x + rr * rb.x, (1.0 - rr) * lb.y + rr * rb.y,
                                      (1.0 - rr) * lb.score + rr * rb.score))
        tracks[sc] = st
    return tracks


def accumulate_threshold(tracks_gt, tracks_pred, cls, threshold):
    from sklearn.metrics.pairwise import euclidean_distances
    accs, scores = [], []
    for sc in tracks_gt:
        acc = Acc()
        frame_id = 0
        sg, sp = tracks_gt[sc], tracks_pred[sc]
        for ts in sg.keys():
            fg = [b for b in sg[ts] if b.name == cls]
            fp = [b for b in sp[ts] if b.name == cls]
            if threshold is not None:
                fp = [b for b in fp if b.score >= threshold]
            gids, pids = [b.tid for b in fg], [b.tid for b in fp]
            if not gids and not pids:
                continue
            if not fg or not fp:
                d = np.ones((0, 0))
            else:
                d = euclidean_distances(np.array([[b.x, b.y] for b in fg]), np.array([[b.x, b.y] for b in fp]))
            d[d >= DIST_TH] = np.nan
            acc.update(gids, pids, d, frameid=frame_id)
            if threshold is None:
                ev = acc.events.loc[frame_id]
                mids = set(ev[ev.Type == "MATCH"].HId.values)
                scores.extend([b.score for b in fp if b.tid in mids])
            frame_id += 1
        accs.append(acc)
    return MOTAccumulatorCustom.merge_event_dataframes(accs), scores


def compute_thresholds(tracks_gt, tracks_pred, cls, gt_box_count):
    _, scores = counts_threshold(tracks_gt, tracks_pred, cls, None)
    if len(scores) == 0:
        return [np.nan] * NUM_THRESHOLDS, [np.nan] * NUM_THRESHOLDS
    scores = np.array(scores)
    scores.sort()
    scores = scores[::-1]
    rec = np.array(range(1, len(scores) + 1)) / gt_box_count
    rec_interp = np.linspace(MIN_RECALL, 1, NUM_THRESHOLDS).round(12)
    thresholds = np.interp(rec_interp, rec, scores, right=0)
    thresholds[rec_interp > np.max(rec)] = np.nan
    thresholds, rec_interp = list(thresholds.tolist()), list(rec_interp.tolist())
    thresholds.reverse()
    rec_interp.reverse()
    return thresholds, rec_interp


def evaluate_class(tracks_gt, tracks_pred, cls):
    gt_count, gt_ids = 0, set()
    for st in tracks_gt.values():
        for boxes in st.values():
            for b in boxes:
                if b.name == cls:
                    gt_count += 1
                    gt_ids.add(b.tid)
    if gt_count == 0:
        return None
    import pandas
    mh = create_motmetrics()
    thresholds, recalls = compute_thresholds(tracks_gt, tracks_pred, cls, gt_count)
    summaries, th_done = [], []
    for t, th in enumerate(thresholds):
        if np.isnan(th) or th in thresholds[:t]:
            continue
        cnt, _ = counts_threshold(tracks_gt, tracks_pred, cls, th)
        summaries.append(cheap_from_counts(cnt))
        th_done.append(th)
    unachieved = len([t for t in thresholds if np.isnan(t)])
    valid = [t for t in thresholds if not np.isnan(t)]
    assert valid == sorted(valid)
    rep = [int(np.sum(np.array(thresholds) == t)) for t in np.unique(valid)]
    summary = summaries if summaries else None

    def worst_of(name):
        worst = METRIC_WORST[name]
        if worst == -1:
            worst = {"ml": len(gt_ids), "gt": gt_count, "fn": gt_count}.get(name, np.nan)
        return worst

    def expand(vals):
        vals = np.concatenate([[v] * r for v, r in zip(vals, rep)])
        out_ = [np.nan] * unachieved + list(vals)
        assert len(out_) == NUM_THRESHOLDS
        return out_
    md = {}
    for mot_name in CHEAP:
        name = MOT_METRIC_MAP[mot_name]
        if name == "":
            continue
        md[name] = [worst_of(name)] * NUM_THRESHOLDS if summary is None else expand([x[name] for x in summary])
    out = {"gt_boxes": gt_count, "gt_tracks": len(gt_ids)}
    mota = np.array(md["mota"], dtype=float)
    best = None if np.all(np.isnan(mota)) else int(np.nanargmax(mota))
    if best is not None:
        for name in md:
            out[name] = float(md[name][best])
        out["best_threshold"] = float(thresholds[best])
        if summary is not None:
            acc, _ = accumulate_threshold(tracks_gt, tracks_pred, cls, thresholds[best])
            s_best = mh.compute(acc, metrics=list(PER_OBJECT) + CHEAP, name="best")
            for mot_name in PER_OBJECT:
                out[MOT_METRIC_MAP[mot_name]] = float(s_best.get(mot_name).values[0])
            out["crosscheck_motmetrics_at_best"] = {MOT_METRIC_MAP[k]: float(s_best.get(k).values[0]) for k in CHEAP if MOT_METRIC_MAP[k]}
            out["crosscheck_equal"] = all(abs(out["crosscheck_motmetrics_at_best"][k] - out[k]) <= 1e-12 * max(1.0, abs(out[k]))
                                          for k in out["crosscheck_motmetrics_at_best"] if k in out)
        else:
            for mot_name in PER_OBJECT:
                out[MOT_METRIC_MAP[mot_name]] = float(worst_of(MOT_METRIC_MAP[mot_name]))
    motar = np.array(md["motar"], dtype=float)
    if np.all(np.isnan(motar)):
        out["amota"] = float("nan")
    else:
        motar[np.isnan(motar)] = METRIC_WORST["amota"]
        out["amota"] = float(np.nanmean(motar))
    out["recall_thresholds_achieved"] = NUM_THRESHOLDS - unachieved
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--exports", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--classes", nargs="*", default=CLASSES)
    ap.add_argument("--check-reference", default=None, help="CANMOT reference JSON (devkit evaluation) to compare with")
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    t0 = time.time()
    warnings.filterwarnings("ignore")
    samples, racks, scene_ts, gt_by_sample, st_gt = load_gt_tracks(a.gt)
    pred_by_sample, tokens, st_pr = load_pred_tracks(a.exports, samples, racks)
    assert tokens == set(samples), "exported tokens differ from the GT samples (%d vs %d)" % (len(tokens), len(samples))
    tracks_gt = create_tracks(gt_by_sample, scene_ts, gt=True)
    tracks_pred = create_tracks(pred_by_sample, scene_ts, gt=False)
    print("loaded %.0f s" % (time.time() - t0), flush=True)
    res = {"label": a.label, "gt": os.path.abspath(a.gt), "exports": [os.path.abspath(w) for w in a.exports],
           "protocol": "nuScenes tracking_nips_2019 (centre distance 2 m, class ranges, 40 recall thresholds); "
                       "no NEES, no TP errors, no MOTP/AMOTP (av2_track_metrics_v03)",
           "counts": dict(st_gt, **st_pr, scenes=len(scene_ts), frames=len(samples)), "per_class": {}}
    for cls in a.classes:
        r = evaluate_class(tracks_gt, tracks_pred, cls)
        res["per_class"][cls] = r
        print(cls, None if r is None else {k: r.get(k) for k in ("amota", "mota", "recall", "ids", "tp", "fp", "fn", "gt")},
              "%.0f s" % (time.time() - t0), flush=True)
    if a.check_reference:
        ref = json.load(open(a.check_reference))["label_metrics"]  # fixed 2 Nov: per-class values live here
        cmp = {}
        for cls in a.classes:
            r = res["per_class"].get(cls) or {}
            cmp[cls] = {m: {"ours": r.get(m), "reference": ref[m].get(cls),
                            "equal": (r.get(m) is not None and ref[m].get(cls) is not None
                                      and abs(r.get(m) - ref[m].get(cls)) <= 1e-9 * max(1.0, abs(ref[m].get(cls))))}
                        for m in ("amota", "mota", "motar", "recall", "tp", "fp", "fn", "ids", "frag", "gt", "mt", "ml", "faf")}
        res["reference_check"] = {"reference": os.path.abspath(a.check_reference), "per_class": cmp,
                                  "all_equal": all(v["equal"] for c in cmp.values() for v in c.values())}
        print("reference check all equal:", res["reference_check"]["all_equal"], flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print("METRICS DONE %.0f s" % (time.time() - t0), flush=True)


if __name__ == "__main__":
    sys.exit(main())
