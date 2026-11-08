#!/usr/bin/env python3
"""av2_ab3dmot_v05 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md sections 6, 7, 9) = av2_ab3dmot_v04 with:
  * --detector {lt3d, owncp} (av2_common_v02.det_sources; owncp = val150 + held225 npz, SHA-256 checked against
    av2_common_v02.DET_SHA256); --logs-file for the log set (default: v04's 150 val log folders, asserted 150);
    poses through av2_common_v02.log_dir and frames from av2_common_v02.frame_timestamps;
  * each worker loads only its own logs' detections (memory); each log's rows and their order are v04's;
    "detections_score_gt_0p1" is still counted over every row of the source(s);
  * per-log checkpoints in <out>/parts_worker<i>/: the log's det, kf and horizon lines, its per-frame records, stat deltas,
    non-PD count and KalmanBoxTracker.count before and after the log (the only cross-log state: AB3DMOT.reset() rebuilds
    every per-class tracker). On a restart a log is reused when its key (settings, sources, frames, count before) and its
    parts' decompressed SHA-256 match (hashes of the bytes the text-mode gzip writers emit: CR LF on Windows, as v04's); the counter is restored before the next log is tracked. The outputs are then
    assembled in log order, exactly the lines v04 writes, and the parts folder is removed;
  * the record's "dataset" is "av2_sensor_val" when every log of the log set is a val log (as v04), otherwise
    "av2_sensor_val_train"; harness "av2_ab3dmot_v05"; a "v05" block (sources, log file, checkpoint use);
  * --test-stop-after N (tests only): exit 3 after N newly tracked logs, before assembling (a simulated crash).
Everything else, the loop body (LT3D test_tracker.py's, line for line), shims L1 and L2 and the export format, is v04's.

av2_ab3dmot_v04 (2 Nov 2026) = v03 plus an exact speed-up and a log list (v03 was stopped on purpose: 650 s on its second
log). Shim L2, installed in memory (LT3D's file is not edited): tracking.ab3dmot.associate_detections_to_tracks is replaced by a
copy that computes iou3d only for (detection, track) pairs whose bird's-eye-view circumscribed circles overlap and leaves 0
for the others. LT3D's iou3d is exactly 0.0 for such pairs (polygon_clip returns None for disjoint convex footprints, so the
intersection area and the IoU are 0.0), so the IoU matrix, the matching and every output are unchanged; the copy is
otherwise line for line. --fast toggles the shim (off reproduces v03); test_av2_ab3dmot_fast_v01 compares the two on logs.
--logs runs an explicit list of logs (tests).
av2_ab3dmot_v03 (= v02, never run, with the log bounds taken over all 150 logs instead of the worker's subset).
av2_ab3dmot_v02 (2 Nov 2026; v01 was stopped after its first log: 250 s per log on all 26 categories). Two changes:
  (i) after test_tracker's score and top-500 filters (applied over all 26 categories, as LT3D does), only the 12 AV2
      categories of the tracker-input mapping (design 4.2) are passed to AB3DMOT. AB3DMOT tracks every category with its own
      independent single-class tracker, so the tracks of these categories are those of a 26-category run up to the
      track-id labels (KalmanBoxTracker.count is global);
  (ii) --worker i --n-workers N runs the logs i, i + N, ... (one tracker reset per log, so logs are independent) and
      writes worker<i> exports and horizon8_ab3dmot_kf_worker<i>.jsonl.gz.
Everything else is v01's.
av2_ab3dmot_v01: LT3D's AB3DMOT (the public AV2 baseline tracker; D16 Choice 11) on the LT3D CenterPoint detections at 2 Hz
(Claude line, 2 Nov 2026). Runs in 50_CODE/env/ab3dmot310 (numpy 1.23.5, scipy 1.10.1, numba 0.58.1 as on the LT3D pod;
filterpy 1.4.5) with python -I.

The tracker is LT3D's own code, imported unchanged from 50_CODE/third_party_av2/LT3D (commit e33189aa, tracking/ab3dmot.py);
LT3D's data/utils.py is replaced by the stand-in 50_CODE/av2/shims_lt3d/data/utils.py (two functions copied verbatim; the
original imports mmdet3d for a class list). The driving loop is LT3D tracking/test_tracker.py's, line for line:
  * all 26 AV2 categories, one single-class AB3DMOT per category, max_age 3 (test_tracker's --max_track_age default),
    detections with score > 0.1, the top 500 per frame, one tracker reset per log, tracks kept when active;
  * detections in the city frame as LT3D's transform_to_global_reference (R t + p; yaw + atan2(R10, R00), wrapped; velocity
    rotated), from the same detection table and the same 4,806 frames as T1/T3;
  * scores averaged over each track afterwards (LT3D tracking/utils.average_scores_across_track).
Read-only capture (no tracker code changed): after each step, each active track's Kalman state x (10: x y z yaw l w h and
per-frame velocities), covariance P and the filter's F and Q. Two exports in the x1_export_v06 line format (mapped tracking
classes only, design 4.2; the tracker itself ran on all 26 categories):
  ab3dmot_det: translation, size, yaw = the associated detection's (LT3D's output; its tracking metrics are the baseline's);
  ab3dmot_kf : translation, size, yaw = the filter's posterior state (the original AB3DMOT output); used for stage A.
Both carry velocity = state velocity / 0.5 s (AB3DMOT's step is one 2 Hz frame), cov9 = H P H' (7 x 7: x y z yaw l w h),
state10 = x, P10 = P. A horizon8 file (the 8 planner steps) is the filter's own propagation, x <- F x, P <- F P F' + Q per
0.5 s step, aligned line for line with the ab3dmot_kf export. No ground truth is read.
Usage: ab3dmot310/python -I -B av2_ab3dmot_v01.py --out <dir>
"""
import argparse
import datetime as dt
import gzip
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
import av2_common_v02 as C  # noqa: E402
from av2_feather_v01 import read_feather  # noqa: E402

sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "third_party_av2", "LT3D"))
sys.path.insert(0, os.path.join(HERE, "shims_lt3d"))          # 'data' resolves to the stand-in
from tracking.ab3dmot import AB3DMOT  # noqa: E402

AV2_CATEGORIES = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST", "MOTORCYCLIST", "WHEELED_RIDER", "BOLLARD", "CONSTRUCTION_CONE",
                  "SIGN", "CONSTRUCTION_BARREL", "STOP_SIGN", "MOBILE_PEDESTRIAN_CROSSING_SIGN", "LARGE_VEHICLE", "BUS", "BOX_TRUCK",
                  "TRUCK", "VEHICULAR_TRAILER", "TRUCK_CAB", "SCHOOL_BUS", "ARTICULATED_BUS", "MESSAGE_BOARD_TRAILER", "BICYCLE",
                  "MOTORCYCLE", "WHEELED_DEVICE", "WHEELCHAIR", "STROLLER", "DOG")
SCORE_THRESHOLD, KEEP_TOP_K, MAX_AGE = 0.1, 500, 3
STEP_S = 0.5
KEYS8 = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
H7 = np.eye(7, 10)


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def install_fast_association():
    """Shim L2 (exact): see the header."""
    import tracking.ab3dmot as AB
    from scipy.optimize import linear_sum_assignment

    def circles(c8):
        # bird's-eye-view footprint in the (x, z) coordinates iou3d uses: corners 0-3
        fp = c8[:, :4][:, :, [0, 2]]
        ctr = fp.mean(axis=1)
        rad = np.sqrt(((fp - ctr[:, None, :]) ** 2).sum(-1)).max(axis=1)
        return ctr, rad

    def associate_detections_to_tracks(detections, tracks, iou_threshold=0.1, match_algorithm="greedy"):
        if len(tracks) == 0:
            return (np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 8, 3), dtype=int))
        iou_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)
        distance_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)
        if len(detections):
            cd, rd = circles(np.asarray(detections))
            ct, rt = circles(np.asarray(tracks))
            near = np.sqrt(((cd[:, None, :] - ct[None, :, :]) ** 2).sum(-1)) <= rd[:, None] + rt[None, :] + 1e-6
            for d, t in zip(*np.nonzero(near)):
                iou_matrix[d, t] = AB.iou3d(detections[d], tracks[t])[0]
        distance_matrix = -iou_matrix
        if match_algorithm == "greedy":
            matched_indices = AB.greedy_match(distance_matrix)
        elif match_algorithm == "hungarian":
            matched_indices = linear_sum_assignment(distance_matrix)
            matched_indices = np.stack(matched_indices, axis=-1)
        else:
            raise ValueError()
        unmatched_detections = []
        for d, det in enumerate(detections):
            if d not in matched_indices[:, 0]:
                unmatched_detections.append(d)
        unmatched_tracks = []
        for t, trk in enumerate(tracks):
            if len(matched_indices) == 0 or (t not in matched_indices[:, 1]):
                unmatched_tracks.append(t)
        matches = []
        for m in matched_indices:
            match = True
            if iou_matrix[m[0], m[1]] < iou_threshold:
                match = False
            if not match:
                unmatched_detections.append(m[0])
                unmatched_tracks.append(m[1])
            else:
                matches.append(m.reshape(1, 2))
        if len(matches) == 0:
            matches = np.empty((0, 2), dtype=int)
        else:
            matches = np.concatenate(matches, axis=0)
        return matches, np.array(unmatched_detections), np.array(unmatched_tracks)

    AB.associate_detections_to_tracks = associate_detections_to_tracks
    return "tracking.ab3dmot.associate_detections_to_tracks"


def wrap_pi(theta):
    theta = np.remainder(theta, 2 * np.pi)
    theta[theta > np.pi] -= 2 * np.pi
    return theta


def yaw_quat(yaw):
    return [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]


def gz_sha256(path):
    """SHA-256 and byte count of a gzip file's decompressed content (v05)."""
    h, n = hashlib.sha256(), 0
    with gzip.open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
            n += len(b)
    return h.hexdigest(), n


def write_json_atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def main():
    import tracking.ab3dmot as AB
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--n-workers", type=int, default=1)
    ap.add_argument("--fast", action="store_true")
    ap.add_argument("--logs", nargs="*", default=None)
    ap.add_argument("--detector", default="lt3d", choices=("lt3d", "owncp"))                     # v05
    ap.add_argument("--logs-file", default=None, help="v05: JSON list of log ids or an object with 'logs' (default: the 150 val logs)")
    ap.add_argument("--test-stop-after", type=int, default=0, help="v05 tests only: exit 3 after N newly tracked logs")
    a = ap.parse_args()
    t0 = time.time()
    srcs = C.det_sources(a.detector)
    src_shas = [sha256_path(p) for p in srcs]
    if a.detector in C.DET_SHA256:
        assert tuple(src_shas) == tuple(C.DET_SHA256[a.detector]), "source SHA-256 differs from SHA256SUMS: %s" % src_shas
    if a.logs_file:
        all_logs = C.read_logs_file(a.logs_file)
    else:
        all_logs = sorted(d for d in os.listdir(C.AV2_VAL) if os.path.isdir(os.path.join(C.AV2_VAL, d)))
        assert len(all_logs) == 150
    logs = all_logs[a.worker::a.n_workers] if not a.logs else [x for x in all_logs if x in set(a.logs)]
    dataset = "av2_sensor_val" if all(C.log_part(x) == "val150" for x in all_logs) else "av2_sensor_val_train"
    out = os.path.abspath(a.out)
    dirs = {v: os.path.join(out, "ab3dmot_" + v, "worker%d" % a.worker) for v in ("det", "kf")}
    for d in dirs.values():
        if os.path.exists(os.path.join(d, "x1_export_record.json")):
            raise SystemExit("refused: %s already holds an export record (v05 never overwrites)" % d)
        os.makedirs(d, exist_ok=True)
    pdir = os.path.join(out, "parts_worker%d" % a.worker)
    os.makedirs(pdir, exist_ok=True)
    # v04's detections_score_gt_0p1: over every row of the source(s)
    n_in = 0
    for p in srcs:
        n_in += int(np.sum(C.npz_select(p, "score") > SCORE_THRESHOLD))
    # v05: load only this worker's logs (memory); each log's rows and their order are v04's
    cats = np.array(AV2_CATEGORIES)
    sorted_cats = np.sort(cats)
    larr = np.array(sorted(logs))
    parts = []
    for p in srcs:
        score = C.npz_select(p, "score").astype(np.float64)
        keep = score > SCORE_THRESHOLD
        del score
        keep &= C.npz_select(p, "log_id", transform=lambda x: np.isin(x, larr))
        Kp = {"code": C.npz_select(p, "category", keep=keep, transform=lambda x: np.searchsorted(sorted_cats, x).astype(np.int16)),
              "lg": C.npz_select(p, "log_id", keep=keep), "ts": C.npz_select(p, "timestamp_ns", keep=keep).astype(np.int64)}
        for c in ("tx_m", "ty_m", "tz_m", "length_m", "width_m", "height_m", "qw", "qx", "qy", "qz", "vx", "vy", "score"):
            Kp[c] = C.npz_select(p, c, keep=keep).astype(np.float64)
        parts.append(Kp)
        del keep
    K = {c: np.concatenate([Kp[c] for Kp in parts]) for c in parts[0]} if len(parts) > 1 else parts[0]
    del parts
    K["name"] = sorted_cats[K["code"]]
    print("detections with score > 0.1: %d in all sources, %d in this worker's %d logs (%.0f s)" % (n_in, len(K["ts"]), len(logs), time.time() - t0), flush=True)
    if a.fast:
        install_fast_association()
    order = np.lexsort((np.arange(len(K["ts"])), K["ts"], K["lg"]))
    for k_ in K:
        K[k_] = K[k_][order]
    bounds = np.append(np.searchsorted(K["lg"], np.array(all_logs), side="left"), len(K["lg"]))
    tracker = AB3DMOT(classes=list(AV2_CATEGORIES), max_age=MAX_AGE)
    ck_base = {"harness": "av2_ab3dmot_v05 (checkpoint hash fix)", "detector": a.detector, "sources_sha256": src_shas, "fast": bool(a.fast),
               "score_threshold": SCORE_THRESHOLD, "keep_top_k": KEEP_TOP_K, "max_age": MAX_AGE, "worker": a.worker,
               "n_workers": a.n_workers}
    per_frame, st, nonpd = [], defaultdict(int), 0
    reused, ran, log_seconds = [], [], {}
    running_count = 0
    for lg in logs:
        li = all_logs.index(lg)
        frames = C.frame_timestamps(lg)
        key = json.loads(json.dumps(dict(ck_base, log=lg, seq_id=li, frames=[int(t) for t in frames], count_before=running_count)))
        files = {v: os.path.join(pdir, "%s.%s.jsonl.gz" % (lg, v)) for v in ("det", "kf", "hz")}
        spath = os.path.join(pdir, lg + ".state.json")
        if os.path.exists(spath) and all(os.path.exists(f) for f in files.values()):
            S_ = json.load(open(spath))
            if S_.get("key") == key and all(list(gz_sha256(files[v])) == S_["sha256"][v] for v in files):
                per_frame += S_["per_frame"]
                for k_, v_ in S_["st"].items():
                    st[k_] += v_
                nonpd += S_["nonpd"]
                running_count = S_["count_after"]
                reused.append(lg)
                log_seconds[lg] = S_["seconds"]
                continue
        tl0 = time.time()
        AB.KalmanBoxTracker.count = running_count          # v05: the only cross-log state (track numbering)
        P = C.Poses(read_feather(os.path.join(C.log_dir(lg), "city_SE3_egovehicle.feather")))
        s0, s1 = bounds[li], bounds[li + 1]
        tracker.reset()
        last_t = frames[0]
        recs = []
        pf_l, st_l = [], defaultdict(int)
        for fi, t in enumerate(frames):
            sel = np.arange(s0, s1)[K["ts"][s0:s1] == t]
            n = len(sel)
            if n:
                i = P.index(np.full(n, t))
                R = C.qrot_matrix(P.q[i])
                tr = np.einsum("nij,nj->ni", R, np.stack([K["tx_m"][sel], K["ty_m"][sel], K["tz_m"][sel]], 1)) + P.p[i]
                q = np.stack([K["qw"][sel], K["qx"][sel], K["qy"][sel], K["qz"][sel]], 1)
                yaw_e = C.qyaw(q)
                e2c = np.arctan2(R[:, 1, 0], R[:, 0, 0])
                v3 = np.stack([K["vx"][sel], K["vy"][sel], np.zeros(n)], 1)
                frame = {"translation_m": tr, "size": np.stack([K["length_m"][sel], K["width_m"][sel], K["height_m"][sel]], 1),
                         "yaw": wrap_pi(yaw_e + e2c), "velocity_m_per_s": np.einsum("nij,nj->ni", R, v3),
                         "label": np.array([AV2_CATEGORIES.index(x) for x in K["name"][sel]], int), "name": K["name"][sel].astype(object),
                         "score": K["score"][sel], "timestamp_ns": int(t), "seq_id": lg}
            else:
                frame = {"translation_m": np.zeros((0, 3)), "size": np.zeros((0, 3)), "yaw": np.zeros(0), "velocity_m_per_s": np.zeros((0, 3)),
                         "label": np.zeros(0, int), "name": np.zeros(0, dtype=object), "score": np.zeros(0), "timestamp_ns": int(t), "seq_id": lg}
            # test_tracker.py loop body
            time_delta_seconds = (t - last_t) * 1e-9
            last_t = t
            fp = {k_: (v[frame["score"] > SCORE_THRESHOLD] if isinstance(v, np.ndarray) else v) for k_, v in frame.items()}
            kk = min(len(fp["score"]), KEEP_TOP_K) - 1
            if len(fp["score"]):
                m_ = fp["score"] >= -np.partition(-fp["score"], kk)[kk]
                fp = {k_: (v[m_] if isinstance(v, np.ndarray) else v) for k_, v in fp.items()}
            mapped = np.array([str(x) in C.TRACKER_MAP for x in fp["name"]], bool) if len(fp["score"]) else np.zeros(0, bool)
            st_l["dets_after_topk"] += int(len(fp["score"]))
            fp = {k_: (v[mapped] if isinstance(v, np.ndarray) else v) for k_, v in fp.items()}   # v02 (i)
            st_l["dets_to_tracker_mapped"] += int(len(fp["score"]))
            track_frame = tracker.step(fp, time_delta_seconds)
            if "active" in track_frame and len(np.atleast_1d(track_frame.get("track_id", []))):
                act = track_frame["active"] > 0
                track_frame = {k_: (v[act] if isinstance(v, np.ndarray) else v) for k_, v in track_frame.items()}
            else:
                track_frame = {"track_id": np.zeros(0, int)}
            # read-only capture of each active track's filter
            kf_of = {}
            for name, sct in tracker.trackers.items():
                for trk in sct.tracks:
                    if trk.time_since_update == 0:
                        kf_of[int(trk.id)] = (np.array(trk.kf.x, float).reshape(-1), np.array(trk.kf.P, float), np.array(trk.kf.F, float),
                                              np.array(trk.kf.Q, float))
            ids = np.atleast_1d(track_frame["track_id"]).astype(int) if len(np.atleast_1d(track_frame["track_id"])) else np.zeros(0, int)
            for j, tid in enumerate(ids):
                x, Pm, F, Q = kf_of[int(tid)]
                recs.append({"fi": fi, "t": int(t), "tid": int(tid), "name": str(track_frame["name"][j]),
                             "det_tr": track_frame["translation_m"][j].tolist(), "det_size": track_frame["size"][j].tolist(),
                             "det_yaw": float(track_frame["yaw"][j]), "det_score": float(track_frame["score"][j]),
                             "x": x, "P": Pm, "F": F, "Q": Q})
            pf_l.append({"scene": lg, "seq_id": li, "frame_id": fi, "token": C.token(lg, t), "timestamp_ns": int(t),
                         "dets_in": n, "dets_tracker": int(len(fp["score"])), "tracks_active": int(len(ids))})
            st_l["frames"] += 1
        # LT3D average_scores_across_track
        sc_by = defaultdict(list)
        for r in recs:
            sc_by[r["tid"]].append(r["det_score"])
        avg = {k_: float(np.mean(v)) for k_, v in sc_by.items()}
        st_l["records_all_categories"] += len(recs)
        # v04's export loop for this log: exports (mapped classes only) and the horizon8 lines aligned with the kf export
        hs = {v: hashlib.sha256() for v in files}
        nb = {v: 0 for v in files}
        nonpd_l = 0
        fo = {v: gzip.open(files[v], "wt", encoding="utf-8", compresslevel=6) for v in ("det", "kf")}
        fo["hz"] = gzip.open(files["hz"], "wt")

        def put(v, s_):
            fo[v].write(s_)
            b_ = s_.replace("\n", os.linesep).encode("utf-8")   # text-mode gzip (as v04's) writes os.linesep
            hs[v].update(b_)
            nb[v] += len(b_)
        for r in recs:
            nm = C.TRACKER_MAP.get(r["name"])
            if nm is None:
                continue
            x, Pm, F, Q = r["x"], r["P"], r["F"], r["Q"]
            cov = H7 @ Pm @ H7.T
            try:
                np.linalg.cholesky(cov[:2, :2])
            except np.linalg.LinAlgError:
                nonpd_l += 1
            vel = [float(x[7]) / STEP_S, float(x[8]) / STEP_S]
            tok = C.token(lg, r["t"])
            base = {"scene": lg, "seq_id": li, "frame_id": r["fi"], "sample_token": tok, "tracking_id": str(r["tid"]), "tracking_name": nm,
                    "tracking_score": avg[r["tid"]], "detection_score": r["det_score"], "velocity": vel, "cov9": cov.tolist(),
                    "state10": x.tolist(), "P10": Pm.tolist(), "pool": "active", "category": r["name"]}
            l_, w_, h_ = r["det_size"]
            ld = dict(base, translation=r["det_tr"], size=[w_, l_, h_], rotation=yaw_quat(r["det_yaw"]))
            lk = dict(base, translation=[float(x[0]), float(x[1]), float(x[2])], size=[float(x[5]), float(x[4]), float(x[6])],
                      rotation=yaw_quat(float(x[3])))
            put("det", json.dumps(ld) + "\n")
            put("kf", json.dumps(lk) + "\n")
            st_l["records_mapped"] += 1
            # the filter's own propagation, 8 steps of one frame (0.5 s)
            xs, Ps = x.reshape(-1, 1).copy(), Pm.copy()
            h = {"scene": lg, "k": r["fi"], "tid": str(r["tid"])}
            for step in range(1, 9):
                xs = F @ xs
                Ps = F @ Ps @ F.T + Q
                h[KEYS8[step - 1]] = [float(xs[0, 0]), float(xs[1, 0]), float(Ps[0, 0]), float(Ps[0, 1]), float(Ps[1, 1])]
            put("hz", json.dumps(h) + "\n")
        for f_ in fo.values():
            f_.close()
        count_after = int(AB.KalmanBoxTracker.count)
        S_ = {"key": key, "per_frame": pf_l, "st": dict(st_l), "nonpd": nonpd_l, "count_after": count_after,
              "sha256": {v: [hs[v].hexdigest(), nb[v]] for v in files}, "seconds": round(time.time() - tl0, 1)}
        write_json_atomic(spath, S_)
        per_frame += pf_l
        for k_, v_ in st_l.items():
            st[k_] += v_
        nonpd += nonpd_l
        running_count = count_after
        ran.append(lg)
        log_seconds[lg] = S_["seconds"]
        del recs
        print("log %d/%d %s %.0f s" % (logs.index(lg) + 1, len(logs), lg, time.time() - t0), flush=True)
        if a.test_stop_after and len(ran) >= a.test_stop_after:
            print("TEST STOP after %d newly tracked logs (simulated crash; no assembly)" % len(ran), flush=True)
            sys.stdout.flush()
            os._exit(3)
    # assembly: the parts in log order (v04 wrote the same lines in the same order)
    outs = {"det": os.path.join(dirs["det"], "x1_tracks.jsonl.gz"), "kf": os.path.join(dirs["kf"], "x1_tracks.jsonl.gz"),
            "hz": os.path.join(out, "horizon8_ab3dmot_kf_worker%d.jsonl.gz" % a.worker)}
    dec = {}
    for v, path in outs.items():
        hh = hashlib.sha256()
        with gzip.open(path, "wb", compresslevel=6 if v != "hz" else 9) as g:
            for lg in logs:
                with gzip.open(os.path.join(pdir, "%s.%s.jsonl.gz" % (lg, v)), "rb") as f:
                    for b in iter(lambda: f.read(1 << 20), b""):
                        g.write(b)
                        hh.update(b)
        dec[v] = hh.hexdigest()
    for v, d in dirs.items():
        json.dump(per_frame, open(os.path.join(d, "x1_per_frame.json"), "w"))
        n_exp = sum(len(C.frame_timestamps(x)) for x in logs)
        frames_ok = len(per_frame) == n_exp and len({p["token"] for p in per_frame}) == n_exp
        rec = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "harness_version": "av2_ab3dmot_v05", "fast_association_shim_L2": bool(a.fast), "logs": logs, "worker": a.worker, "n_workers": a.n_workers,
               "dataset": dataset, "detector": a.detector, "tracker": "LT3D AB3DMOT (commit e33189aa) variant " + v,
               "resolved_config": {"experiment_id": "lt3d/ab3dmot", "basic": {"has_velo": True, "LiDAR_interval": STEP_S}},
               "settings": {"score_threshold": SCORE_THRESHOLD, "keep_top_k": KEEP_TOP_K, "max_age": MAX_AGE, "classes": list(AV2_CATEGORIES)},
               "stats": dict(st, nonpd_xy_cov=nonpd, detections_score_gt_0p1=n_in),
               "criteria": {"frames_complete": frames_ok, "xy_cov_pd": nonpd == 0},
               "status_X1_gates": "PASS" if frames_ok and nonpd == 0 else "FAIL",
               "shims": {"L1": "LT3D data/utils.py replaced by shims_lt3d/data/utils.py (two functions verbatim; mmdet3d not imported)"},
               "lt3d_files_sha256": {f: sha256_path(os.path.join(W_ROOT, "50_CODE", "third_party_av2", "LT3D", "tracking", f)) for f in ("ab3dmot.py", "test_tracker.py", "utils.py")},
               "wall_seconds": round(time.time() - t0, 1)}
        rec["output_sha256"] = {"x1_tracks.jsonl.gz": sha256_path(os.path.join(d, "x1_tracks.jsonl.gz")),
                                "x1_tracks.jsonl (decompressed)": dec[v]}
        rec["v05"] = {"sources": [os.path.abspath(p) for p in srcs], "sources_sha256": src_shas,
                      "logs_file": os.path.abspath(a.logs_file) if a.logs_file else None,
                      "logs_file_sha256": sha256_path(a.logs_file) if a.logs_file else None,
                      "horizon8_file": outs["hz"], "horizon8_decompressed_sha256": dec["hz"],
                      "logs_reused_from_checkpoints": reused, "logs_tracked_in_this_process": ran,
                      "tracking_seconds_per_log": log_seconds, "kalman_box_tracker_count_end": running_count}
        json.dump(rec, open(os.path.join(d, "x1_export_record.json"), "w"), indent=1)
    import shutil
    shutil.rmtree(pdir, ignore_errors=True)
    print(json.dumps(dict(st, nonpd=nonpd)), "%.0f s" % (time.time() - t0))
    print("AB3DMOT V05 DONE")


if __name__ == "__main__":
    sys.exit(main())
