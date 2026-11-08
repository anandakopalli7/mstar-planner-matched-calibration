#!/usr/bin/env python3
"""av2_ab3dmot_v03 (= v02, never run, with the log bounds taken over all 150 logs instead of the worker's subset).
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
import av2_common_v01 as C  # noqa: E402
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


def wrap_pi(theta):
    theta = np.remainder(theta, 2 * np.pi)
    theta[theta > np.pi] -= 2 * np.pi
    return theta


def yaw_quat(yaw):
    return [math.cos(yaw / 2), 0.0, 0.0, math.sin(yaw / 2)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--worker", type=int, default=0)
    ap.add_argument("--n-workers", type=int, default=1)
    a = ap.parse_args()
    t0 = time.time()
    src = C.DET_PATHS["lt3d"]
    score = C.npz_select(src, "score").astype(np.float64)
    keep = score > SCORE_THRESHOLD
    del score
    cats = np.array(AV2_CATEGORIES)
    K = {"code": C.npz_select(src, "category", keep=keep, transform=lambda x: np.searchsorted(np.sort(cats), x).astype(np.int16)),
         "lg": C.npz_select(src, "log_id", keep=keep), "ts": C.npz_select(src, "timestamp_ns", keep=keep).astype(np.int64)}
    for c in ("tx_m", "ty_m", "tz_m", "length_m", "width_m", "height_m", "qw", "qx", "qy", "qz", "vx", "vy", "score"):
        K[c] = C.npz_select(src, c, keep=keep).astype(np.float64)
    sorted_cats = np.sort(cats)
    K["name"] = sorted_cats[K["code"]]
    n_in = int(keep.sum())
    print("detections with score > 0.1: %d (%.0f s)" % (n_in, time.time() - t0), flush=True)
    all_logs = sorted(d for d in os.listdir(C.AV2_VAL) if os.path.isdir(os.path.join(C.AV2_VAL, d)))
    assert len(all_logs) == 150
    logs = all_logs[a.worker::a.n_workers]
    order = np.lexsort((np.arange(len(K["ts"])), K["ts"], K["lg"]))
    for k_ in K:
        K[k_] = K[k_][order]
    bounds = np.append(np.searchsorted(K["lg"], np.array(all_logs), side="left"), len(K["lg"]))
    tracker = AB3DMOT(classes=list(AV2_CATEGORIES), max_age=MAX_AGE)
    out = os.path.abspath(a.out)
    dirs = {v: os.path.join(out, "ab3dmot_" + v, "worker%d" % a.worker) for v in ("det", "kf")}
    for d in dirs.values():
        os.makedirs(d, exist_ok=True)
    per_frame, lines_by_log, st = [], {}, defaultdict(int)
    for lg in logs:
        li = all_logs.index(lg)
        P = C.Poses(read_feather(os.path.join(C.AV2_VAL, lg, "city_SE3_egovehicle.feather")))
        s0, s1 = bounds[li], bounds[li + 1]
        frames = C.frame_timestamps(lg)
        tracker.reset()
        last_t = frames[0]
        recs = []
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
            st["dets_after_topk"] += int(len(fp["score"]))
            fp = {k_: (v[mapped] if isinstance(v, np.ndarray) else v) for k_, v in fp.items()}   # v02 (i)
            st["dets_to_tracker_mapped"] += int(len(fp["score"]))
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
            per_frame.append({"scene": lg, "seq_id": li, "frame_id": fi, "token": C.token(lg, t), "timestamp_ns": int(t),
                              "dets_in": n, "dets_tracker": int(len(fp["score"])), "tracks_active": int(len(ids))})
            st["frames"] += 1
        # LT3D average_scores_across_track
        sc_by = defaultdict(list)
        for r in recs:
            sc_by[r["tid"]].append(r["det_score"])
        avg = {k_: float(np.mean(v)) for k_, v in sc_by.items()}
        lines_by_log[lg] = (li, recs, avg)
        st["records_all_categories"] += len(recs)
        print("log %d/%d %s %.0f s" % (logs.index(lg) + 1, len(logs), lg, time.time() - t0), flush=True)
    # exports (mapped classes only) and the horizon8 file aligned with the kf export
    files = {v: gzip.open(os.path.join(dirs[v], "x1_tracks.jsonl.gz"), "wt", encoding="utf-8", compresslevel=6) for v in dirs}
    hz = gzip.open(os.path.join(out, "horizon8_ab3dmot_kf_worker%d.jsonl.gz" % a.worker), "wt")
    nonpd = 0
    for lg in logs:
        li, recs, avg = lines_by_log[lg]
        for r in recs:
            nm = C.TRACKER_MAP.get(r["name"])
            if nm is None:
                continue
            x, Pm, F, Q = r["x"], r["P"], r["F"], r["Q"]
            cov = H7 @ Pm @ H7.T
            try:
                np.linalg.cholesky(cov[:2, :2])
            except np.linalg.LinAlgError:
                nonpd += 1
            vel = [float(x[7]) / STEP_S, float(x[8]) / STEP_S]
            tok = C.token(lg, r["t"])
            base = {"scene": lg, "seq_id": li, "frame_id": r["fi"], "sample_token": tok, "tracking_id": str(r["tid"]), "tracking_name": nm,
                    "tracking_score": avg[r["tid"]], "detection_score": r["det_score"], "velocity": vel, "cov9": cov.tolist(),
                    "state10": x.tolist(), "P10": Pm.tolist(), "pool": "active", "category": r["name"]}
            l_, w_, h_ = r["det_size"]
            ld = dict(base, translation=r["det_tr"], size=[w_, l_, h_], rotation=yaw_quat(r["det_yaw"]))
            lk = dict(base, translation=[float(x[0]), float(x[1]), float(x[2])], size=[float(x[5]), float(x[4]), float(x[6])],
                      rotation=yaw_quat(float(x[3])))
            files["det"].write(json.dumps(ld) + "\n")
            files["kf"].write(json.dumps(lk) + "\n")
            st["records_mapped"] += 1
            # the filter's own propagation, 8 steps of one frame (0.5 s)
            xs, Ps = x.reshape(-1, 1).copy(), Pm.copy()
            h = {"scene": lg, "k": r["fi"], "tid": str(r["tid"])}
            for step in range(1, 9):
                xs = F @ xs
                Ps = F @ Ps @ F.T + Q
                h[KEYS8[step - 1]] = [float(xs[0, 0]), float(xs[1, 0]), float(Ps[0, 0]), float(Ps[0, 1]), float(Ps[1, 1])]
            hz.write(json.dumps(h) + "\n")
    for f in files.values():
        f.close()
    hz.close()
    for v, d in dirs.items():
        json.dump(per_frame, open(os.path.join(d, "x1_per_frame.json"), "w"))
        n_exp = sum(len(C.frame_timestamps(x)) for x in logs)
        frames_ok = len(per_frame) == n_exp and len({p["token"] for p in per_frame}) == n_exp
        rec = {"timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "harness_version": "av2_ab3dmot_v03", "logs": logs, "worker": a.worker, "n_workers": a.n_workers,
               "dataset": "av2_sensor_val", "detector": "lt3d", "tracker": "LT3D AB3DMOT (commit e33189aa) variant " + v,
               "resolved_config": {"experiment_id": "lt3d/ab3dmot", "basic": {"has_velo": True, "LiDAR_interval": STEP_S}},
               "settings": {"score_threshold": SCORE_THRESHOLD, "keep_top_k": KEEP_TOP_K, "max_age": MAX_AGE, "classes": list(AV2_CATEGORIES)},
               "stats": dict(st, nonpd_xy_cov=nonpd, detections_score_gt_0p1=n_in),
               "criteria": {"frames_complete": frames_ok, "xy_cov_pd": nonpd == 0},
               "status_X1_gates": "PASS" if frames_ok and nonpd == 0 else "FAIL",
               "shims": {"L1": "LT3D data/utils.py replaced by shims_lt3d/data/utils.py (two functions verbatim; mmdet3d not imported)"},
               "lt3d_files_sha256": {f: sha256_path(os.path.join(W_ROOT, "50_CODE", "third_party_av2", "LT3D", "tracking", f)) for f in ("ab3dmot.py", "test_tracker.py", "utils.py")},
               "wall_seconds": round(time.time() - t0, 1)}
        rec["output_sha256"] = {"x1_tracks.jsonl.gz": sha256_path(os.path.join(d, "x1_tracks.jsonl.gz"))}
        json.dump(rec, open(os.path.join(d, "x1_export_record.json"), "w"), indent=1)
    print(json.dumps(dict(st, nonpd=nonpd)), "%.0f s" % (time.time() - t0))
    print("AB3DMOT V03 DONE")


if __name__ == "__main__":
    sys.exit(main())
