#!/usr/bin/env python3
"""av2_counts_v01: outcome-blind COUNTS for the AV2 tracker runs (Claude line, 1 Nov 2026). Design section 9.

Computed from tracker outputs and ground-truth association only:
  * frames, logs, export records, records at k >= 1, tracks, per tracking class;
  * x1_lib_v03.build_table's association counts (persistent per-class Hungarian pairing, 2 m gate; in-path from estimates
    and ego poses; unpaired, censored-at-k, id switches, duplicates). The per-record association flags resid_gt_gate and
    contested that build_table also sets are NOT aggregated or written;
  * items at the current-estimate geometry (the t = 0 family): (record, axis) pairs passing x1_lib_v03.axis_candidates'
    separating-axis filter (estimate and ego pose only), per analysis group x range bin x axis x motion state
    (m_lib_v04.motion_features / motion_state on the track's own estimates) x population (in-path / not in-path)
    x pairing (paired at k / not paired), with the number of logs (= scenes) per stratum;
  * horizon availability, existence only: whether the k + 4 frame exists in the log and whether the paired track_uuid is
    annotated there with num_interior_pts >= 1 (the nuScenes "censored at the 2 s horizon" count). horizon_availability()
    receives only the set of (sample token, uuid) keys with points; it never sees a future position.
Never computed: any residual, projected error, U, exceedance, margin, NEES, coverage, or the h = 2 s predicted geometry
(that needs av2_horizon_prep_v01.propagate, not run on AV2 here).
Reuses (import only): m_data_v04.load_export_v2 (export reader + Poly-MOT CTRA velocity fix), x1_lib_v03.load_gt,
build_table, axis_candidates, range_bin, m_lib_v04.motion_index, motion_features, motion_state. m_data_v04.load_split is
NOT used (it calls build_horizon_rows, which reads the future GT position).

Usage: python -I -B av2_counts_v01.py --gt <gt json> --tracker t1 --detector lt3d --exports <worker dirs> --out <json>
       python -I -B av2_counts_v01.py --merge <part jsons...> --out <AV2_TRACKER_COUNTS_v01.json>
"""
import argparse
import datetime as dt
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import av2_common_v01 as C  # noqa: E402

sys.path.insert(0, os.path.join(C.W_ROOT, "50_CODE", "m"))
sys.path.insert(0, os.path.join(C.W_ROOT, "50_CODE", "x1"))
import m_data_v04 as MD  # noqa: E402
import m_lib_v04 as M  # noqa: E402
import x1_lib_v03 as L  # noqa: E402

EXPERIMENTS = {"t1": "paper/local/canmot/sc", "t2": "paper/local/sample/trainval", "t3": "paper/baseline/poly_mot"}
GROUPS = ["car", "pedestrian", "cyclist", "motorcyclist_descr", "large_descr"]
RANGES = L.RANGES
AXES = L.AXES
MOTIONS = M.MOTIONS
H_STEPS = 4


def horizon_availability(paired_keys, frames_per_log, ann_keys_with_points, steps=H_STEPS):
    """paired_keys: iterable of (log, k, uuid). Returns per key: 'no_future_frame', 'censored_at_horizon' or 'available'.
    Uses only frame indices and the existence of (sample token at k + steps, uuid) with >= 1 interior point."""
    out = {}
    for log, k, uuid in paired_keys:
        if k + steps >= frames_per_log[log]["n"]:
            out[(log, k, uuid)] = "no_future_frame"
        elif (frames_per_log[log]["tokens"][k + steps], uuid) in ann_keys_with_points:
            out[(log, k, uuid)] = "available"
        else:
            out[(log, k, uuid)] = "censored_at_horizon"
    return out


def run_one(a):
    t0 = time.time()
    exp = EXPERIMENTS[a.tracker]
    recs, fixed = [], 0
    per_frame_rows = 0
    for w in a.exports:
        er = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert er["status_X1_gates"] == "PASS" and er["resolved_config"]["experiment_id"] == exp and er["detector"] == a.detector, w
        rw, fw = MD.load_export_v2(os.path.join(w, "x1_tracks.jsonl.gz"), exp)
        recs += rw
        fixed += fw
        per_frame_rows += len([p for p in json.load(open(os.path.join(w, "x1_per_frame.json"))) if not p.get("error")])
    samples, gtb, racks = L.load_gt(a.gt)
    assert per_frame_rows == len(samples), "frames exported %d != GT samples %d" % (per_frame_rows, len(samples))
    logs = sorted({s["scene"] for s in samples.values()})
    scene_log = {lg: lg for lg in logs}
    frames_per_log = defaultdict(lambda: {"n": 0, "tokens": {}})
    for s in samples.values():
        frames_per_log[s["scene"]]["tokens"][s["index"]] = s["token"]
    for lg in frames_per_log:
        frames_per_log[lg]["n"] = len(frames_per_log[lg]["tokens"])
    out = {"tracker": a.tracker, "experiment": exp, "detector": a.detector, "frames": len(samples), "logs": len(logs),
           "export_records": len(recs), "ctra_velocity_corrected": fixed,
           "tracks": len({(r["scene"], r["tid"]) for r in recs})}
    by_name = defaultdict(int)
    tracks_by_name = defaultdict(set)
    for r in recs:
        by_name[r["name"]] += 1
        tracks_by_name[r["name"]].add((r["scene"], r["tid"]))
    out["export_records_by_class"] = dict(by_name)
    out["tracks_by_class"] = {k: len(v) for k, v in tracks_by_name.items()}
    mi = M.motion_index(recs, samples)
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log, keep_unpaired=True)
    del recs
    out["association"] = {k: v for k, v in pst.items()}  # counts only (no distance)
    # ground-truth objects available for pairing at k >= 1 (num_pts >= 1), per class: a GT-side count
    gt_obj = defaultdict(int)
    for tok, anns in gtb.items():
        if samples[tok]["index"] >= 1:
            for x in anns:
                if x["num_pts"] >= 1:
                    gt_obj[x["tracking_name"]] += 1
    out["gt_annotations_k_ge_1_with_points"] = dict(gt_obj)
    ann_keys = {(tok, x["instance_token"]) for tok, anns in gtb.items() for x in anns if x["num_pts"] >= 1}
    paired_rows = [r for r in rows if r["paired"]]
    hav = horizon_availability([(r["scene"], r["k"], r["inst"]) for r in paired_rows], frames_per_log, ann_keys)
    del ann_keys
    # per-record and per-item tallies
    rec_tab = defaultdict(int)
    item_n = defaultdict(int)
    item_logs = defaultdict(set)
    for r in rows:
        g = C.ANALYSIS_GROUP[r["name"]]
        pop = "inpath" if r["inpath"] else "not_inpath"
        pr = "paired" if r["paired"] else "not_paired"  # not_paired = never paired, or paired object absent at k (pst counts both)
        spd, om, omv, omc, chord = M.motion_features(mi, r["scene"], r["tid"], r["k"])
        m = int(M.motion_state({"spd": np.array([spd]), "omc": np.array([omc])})[0])
        mname = MOTIONS[m]
        hz = hav.get((r["scene"], r["k"], r["inst"])) if r["paired"] else "not_paired"
        rec_tab[(g, r["range"], mname, pop, pr, hz)] += 1
        for name, av, sep, hsum in L.axis_candidates(r):
            if abs(sep) <= hsum:
                continue
            key = (g, r["range"], name, mname, pop, pr, hz)
            item_n[key] += 1
            item_logs[key].add(r["scene"])
    del rows, mi

    def nest(tab, logs_tab=None):
        res = []
        for key in sorted(tab):
            d = dict(zip(("group", "range", "axis", "motion", "population", "pairing", "horizon")
                         if logs_tab is not None else ("group", "range", "motion", "population", "pairing", "horizon"), key))
            d["n"] = tab[key]
            if logs_tab is not None:
                d["logs"] = len(logs_tab[key])
            res.append(d)
        return res
    out["records_table"] = nest(rec_tab)
    out["items_table"] = nest(item_n, item_logs)
    # marginal summaries
    summ = defaultdict(lambda: defaultdict(int))
    summ_logs = defaultdict(lambda: defaultdict(set))
    for key, n in item_n.items():
        g, rg, ax, mo, pop, pr, hz = key
        if pr != "paired":
            continue
        for lab, k2 in (("paired_items_by_group_range_axis_population", (g, rg, ax, pop)),
                        ("paired_items_by_group_range_population", (g, rg, pop)),
                        ("paired_items_by_group_axis_motion_population", (g, ax, mo, pop)),
                        ("paired_horizon_available_items_by_group_range_axis_population", (g, rg, ax, pop) if hz == "available" else None)):
            if k2 is None:
                continue
            summ[lab]["|".join(k2)] += n
            summ_logs[lab]["|".join(k2)] |= item_logs[key]
    out["summaries"] = {lab: {k: {"items": v, "logs": len(summ_logs[lab][k])} for k, v in sorted(d.items())} for lab, d in summ.items()}
    hz_tot = defaultdict(int)
    for r_key, n in rec_tab.items():
        hz_tot[r_key[5]] += n
    out["records_by_horizon_status"] = dict(hz_tot)
    out["wall_seconds"] = round(time.time() - t0, 1)
    out["outcome_statement"] = ("counts only: no residual, projected error, U, exceedance, margin, NEES or coverage computed; "
                                "build_table's resid_gt_gate and contested flags not aggregated; horizon availability by existence only")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt")
    ap.add_argument("--tracker", choices=sorted(EXPERIMENTS))
    ap.add_argument("--detector", choices=sorted(C.DET_PATHS))
    ap.add_argument("--exports", nargs="*")
    ap.add_argument("--merge", nargs="*")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.merge:
        parts = [json.load(open(p)) for p in a.merge]
        head = {}
        for p in parts:
            key = "%s_%s" % (p["tracker"], p["detector"])
            s = p["summaries"]["paired_items_by_group_range_population"]
            head[key] = {rg: s.get("car|%s|inpath" % rg, {"items": 0, "logs": 0}) for rg in RANGES}
        res = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "script": "av2_counts_v01",
               "design": "50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md",
               "outcome_statement": parts[0]["outcome_statement"] if parts else None,
               "headline_car_inpath_paired_items_t0_by_range": head,
               "runs": {"%s_%s" % (p["tracker"], p["detector"]): p for p in parts}}
        with open(a.out, "w") as f:
            json.dump(res, f, indent=1)
        print(json.dumps(head, indent=1))
        return 0
    out = run_one(a)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("tracker", "detector", "frames", "logs", "export_records", "tracks", "association",
                                           "records_by_horizon_status", "wall_seconds")}, default=str), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
