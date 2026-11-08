"""pod_ab3dmot10_v02 (QCNet arm, addendum A, 2 Nov 2026): LT3D's AB3DMOT at 10 Hz from the v01 detection table, in two modes.

Design: 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_ADDENDUM_A_v01.md section A1.
  released  score > 0.1, top 500 per sweep, max_age 3 for every class, no hit rule (tracking/test_tracker.py defaults = v01)
  matched   score >= 0.1, top 500, max_age car 75 / pedestrian 50 / cyclist 50 sweeps (T1's 7.5 s / 5 s / 5 s), min_hits 3 with
            AB3DMOT's rule hits >= 3 or frame_count <= 3 (eddyhkchiu/mahalanobis_3d_multi_object_tracking main.py line 587)
Input: av2val10_lt3d_centerpoint_dets_s010_v01.npz (all classes, score >= 0.1, AV2 table format), converted back to LT3D's
tracker frame format (translation (tx, ty, tz - h/2), size (l, w, h), yaw = wrap_pi(2 atan2(qz, qw)), velocity (vx, vy),
float32 as in LT3D's unpack_predictions), sweeps from the v01 fetch manifest (empty sweeps kept), then LT3D's own
transform_to_global_reference, group order and tracker loop (as pod_ab3dmot10_v01.py).
Shim v02: the v01 exact-zero rule vectorised (pairs whose BEV discs are farther apart than the sum of their radii + 1 cm and
whose volumes are positive get IoU 0.0 without iou3d). Sub-commands:
  prep    --dets <npz> --manifest <csv> --work <dir>        per-log npz of detections + per-log sweep lists
  run     --mode released|matched [--logs N] [--shim]       -> <out>/<mode>/trk10_<log>.npz (+ .json)
  equiv   --mode matched --logs 3                           native vs shim, must be identical
  replay  --ref <v01 trk10 npz> --logs 10                   released mode vs the v01 output (path check)
"""
import argparse
import csv
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

CLASSES3 = ["REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST"]
MODES = {
    "released": {"op": "gt", "floor": 0.1, "topk": 500, "max_age": {"REGULAR_VEHICLE": 3, "PEDESTRIAN": 3, "BICYCLIST": 3}, "min_hits": None},
    "matched": {"op": "ge", "floor": 0.1, "topk": 500, "max_age": {"REGULAR_VEHICLE": 75, "PEDESTRIAN": 50, "BICYCLIST": 50}, "min_hits": 3},
}
A = None


def set_association(shim):
    import tracking.ab3dmot as ab
    if not hasattr(ab, "_native_associate"):
        ab._native_associate = ab.associate_detections_to_tracks
        ab._shim_associate = make_shim(ab)
    ab.associate_detections_to_tracks = ab._shim_associate if shim else ab._native_associate


def make_shim(ab):
    from scipy.optimize import linear_sum_assignment
    orig_iou3d = ab.iou3d

    def discs(c8s):
        q = np.asarray(c8s)[:, :4][:, :, [0, 2]]
        ctr = q.mean(1)
        return ctr, np.sqrt(((q - ctr[:, None, :]) ** 2).sum(-1)).max(1)

    def associate_fast(detections, tracks, iou_threshold=0.1, match_algorithm="greedy"):
        # copy of tracking.ab3dmot.associate_detections_to_tracks; only the iou_matrix construction differs
        if len(tracks) == 0:
            return (np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 8, 3), dtype=int))
        iou_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)
        if len(detections) > 0:
            dc, dr = discs(detections)
            tc, tr = discs(tracks)
            far = np.sqrt(((dc[:, None, :] - tc[None, :, :]) ** 2).sum(-1)) > dr[:, None] + tr[None, :] + 0.01
            dv = np.array([ab.box3d_vol(d) for d in detections])
            tv = np.array([ab.box3d_vol(t) for t in tracks])
            skip = far & ((dv[:, None] + tv[None, :]) > 0)
            for d, t in zip(*np.nonzero(~skip)):
                iou_matrix[d, t] = orig_iou3d(detections[d], tracks[t])[0]
        distance_matrix = -iou_matrix
        if match_algorithm == "greedy":
            matched_indices = ab.greedy_match(distance_matrix)
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

    return associate_fast


def cmd_prep():
    z = np.load(A.dets, allow_pickle=False)
    logs_col = z["log_id"]
    order = np.argsort(logs_col, kind="stable")
    cols = [c for c in z.files]
    data = {c: z[c][order] for c in cols}
    logs = np.unique(data["log_id"])
    st = np.searchsorted(data["log_id"], logs, "left")
    en = np.searchsorted(data["log_id"], logs, "right")
    os.makedirs(os.path.join(A.work, "dets"), exist_ok=True)
    for lg, s, e in zip(logs, st, en):
        np.savez(os.path.join(A.work, "dets", "%s.npz" % lg), **{c: data[c][s:e] for c in cols if c != "log_id"})
    sweeps = {}
    with open(A.manifest) as f:
        for row in csv.DictReader(f):
            k = row["key"]
            if "/sensors/lidar/" in k and k.endswith(".feather"):
                lg = k.split("/")[4]
                sweeps.setdefault(lg, []).append(int(os.path.basename(k).split(".")[0]))
    sweeps = {lg: sorted(v) for lg, v in sweeps.items()}
    json.dump(sweeps, open(os.path.join(A.work, "sweeps_by_log.json"), "w"))
    print("logs with detections", len(logs), "logs with sweeps", len(sweeps), "sweeps", sum(len(v) for v in sweeps.values()), flush=True)
    print("PREP DONE", flush=True)


def frames_for_log(log):
    from data.utils import AV2_CLASS_NAMES, group_frames, wrap_pi
    from data.av2_adapter import read_city_SE3_ego_by_seq_id, transform_to_global_reference
    sweeps = json.load(open(os.path.join(A.work, "sweeps_by_log.json")))[log]
    z = np.load(os.path.join(A.work, "dets", "%s.npz" % log), allow_pickle=False)
    ts = z["timestamp_ns"]
    o = np.argsort(ts, kind="stable")  # stable: keeps the detector's order within a sweep
    d = {c: z[c][o] for c in z.files}
    ts = d["timestamp_ns"]
    cls = list(AV2_CLASS_NAMES)
    frames = []
    for t in sweeps:
        s, e = np.searchsorted(ts, t, "left"), np.searchsorted(ts, t, "right")
        h = d["height_m"][s:e].astype(np.float64)
        trans = np.stack([d["tx_m"][s:e].astype(np.float64), d["ty_m"][s:e].astype(np.float64), d["tz_m"][s:e] - h / 2], 1).astype(np.float32)
        size = np.stack([d["length_m"][s:e], d["width_m"][s:e], d["height_m"][s:e]], 1).astype(np.float32)
        yaw = wrap_pi((2 * np.arctan2(d["qz"][s:e], d["qw"][s:e])).astype(np.float32))
        frames.append({"translation_m": trans.reshape(-1, 3), "size": size.reshape(-1, 3), "yaw": yaw,
                       "velocity_m_per_s": np.stack([d["vx"][s:e], d["vy"][s:e]], 1).astype(np.float32).reshape(-1, 2),
                       "label": np.array([cls.index(c) for c in d["category"][s:e]], dtype=np.int64),
                       "name": d["category"][s:e].astype(str), "score": d["score"][s:e].astype(np.float32),
                       "seq_id": log, "timestamp_ns": int(t)})
    seqs = group_frames(frames)
    seqs = transform_to_global_reference(seqs, read_city_SE3_ego_by_seq_id(A.data, seq_ids=[log]))
    return seqs[log]


def track_log(log, mode_name, shim, out_dir):
    set_association(shim)
    import tracking.ab3dmot as ab
    from data.utils import index_array_values
    M = MODES[mode_name]
    t0 = time.time()
    frames = frames_for_log(log)
    ab.KalmanBoxTracker.count = 0
    tracker = ab.AB3DMOT(classes=CLASSES3, max_age=3)
    tracker.reset()
    for c in CLASSES3:
        tracker.trackers[c].max_age = M["max_age"][c]
    last_t = frames[0]["timestamp_ns"]
    out = {k: [] for k in ("ts", "track_id", "name", "x", "y", "z", "yaw", "vx", "vy", "l", "w", "h", "score", "hits")}
    n_in = topk_bind = held_back = 0
    for fi, frame in enumerate(frames, start=1):
        dt = (frame["timestamp_ns"] - last_t) * 1e-9
        last_t = frame["timestamp_ns"]
        keep = frame["score"] > M["floor"] if M["op"] == "gt" else frame["score"] >= M["floor"]
        filtered = index_array_values(frame, keep)
        if len(filtered["score"]) > 0:
            topk_bind += int(len(filtered["score"]) > M["topk"])
            k = min(len(filtered["score"]), M["topk"]) - 1
            filtered = index_array_values(filtered, filtered["score"] >= -np.partition(-filtered["score"], k)[k])
        n_in += int(np.isin(filtered["name"], CLASSES3).sum())
        tf = tracker.step(filtered, dt)
        if not tf or "active" not in tf:
            continue
        tf = index_array_values(tf, tf["active"] > 0)
        if len(tf["track_id"]) == 0:
            continue
        hits_by_id = {trk.id: trk.hits for c in CLASSES3 for trk in tracker.trackers[c].tracks}
        hits = np.array([hits_by_id[int(i)] for i in tf["track_id"]], dtype=np.int64)
        if M["min_hits"] is not None:
            pub = (hits >= M["min_hits"]) | (fi <= M["min_hits"])
            held_back += int((~pub).sum())
            tf = index_array_values(tf, pub)
            hits = hits[pub]
        n = len(tf["track_id"])
        if n == 0:
            continue
        out["ts"].append(np.full(n, frame["timestamp_ns"], np.int64))
        out["track_id"].append(tf["track_id"].astype(np.int64))
        out["name"].append(tf["name"].astype(str))
        out["x"].append(tf["translation_m"][:, 0]); out["y"].append(tf["translation_m"][:, 1]); out["z"].append(tf["translation_m"][:, 2])
        out["yaw"].append(tf["yaw"]); out["vx"].append(tf["velocity_m_per_s"][:, 0]); out["vy"].append(tf["velocity_m_per_s"][:, 1])
        out["l"].append(tf["size"][:, 0]); out["w"].append(tf["size"][:, 1]); out["h"].append(tf["size"][:, 2])
        out["score"].append(tf["score"]); out["hits"].append(hits)
    res = {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in out.items()}
    res["name"] = res["name"].astype(str)
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "trk10_%s.npz" % log)
    np.savez_compressed(p + ".part.npz", **res)
    os.replace(p + ".part.npz", p)
    meta = {"log": log, "mode": mode_name, "frames": len(frames), "dets_in_3cls_after_filter": n_in, "topk_binding_sweeps": topk_bind,
            "rows_held_back_by_min_hits": held_back, "track_rows": int(len(res["ts"])),
            "tracks": int(len(np.unique(res["track_id"]))) if len(res["track_id"]) else 0, "seconds": time.time() - t0, "shim": shim}
    json.dump(meta, open(p.replace(".npz", ".json"), "w"))
    return meta


def _job(args):
    return track_log(*args)


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prep", "run", "equiv", "replay"])
    ap.add_argument("--lt3d")
    ap.add_argument("--data")
    ap.add_argument("--work", required=True)
    ap.add_argument("--out")
    ap.add_argument("--dets")
    ap.add_argument("--manifest")
    ap.add_argument("--ref")
    ap.add_argument("--mode", choices=sorted(MODES), default="matched")
    ap.add_argument("--logs", type=int, default=0)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--shim", action="store_true")
    A = ap.parse_args()
    if A.cmd == "prep":
        return cmd_prep()
    sys.path.insert(0, A.lt3d)
    os.chdir(A.lt3d)
    logs = sorted(json.load(open(os.path.join(A.work, "sweeps_by_log.json"))))
    if A.logs:
        logs = logs[: A.logs]
    if A.cmd == "equiv":
        jobs = [(l, A.mode, False, os.path.join(A.out, "equiv_native")) for l in logs] + [(l, A.mode, True, os.path.join(A.out, "equiv_shim")) for l in logs]
        with Pool(min(A.procs, len(jobs))) as pool:
            ma = pool.map(_job, jobs, chunksize=1)
        rec = {"mode": A.mode, "logs": logs, "identical": True, "seconds_native": sum(m["seconds"] for m in ma[: len(logs)]), "seconds_shim": sum(m["seconds"] for m in ma[len(logs):])}
        for l in logs:
            a = np.load(os.path.join(A.out, "equiv_native", "trk10_%s.npz" % l), allow_pickle=False)
            b = np.load(os.path.join(A.out, "equiv_shim", "trk10_%s.npz" % l), allow_pickle=False)
            same = all(a[k].shape == b[k].shape and (a[k] == b[k]).all() for k in a.files)
            rec[l] = {"rows": int(len(a["ts"])), "identical": bool(same)}
            rec["identical"] &= bool(same)
        json.dump(rec, open(os.path.join(A.out, "ab3dmot_v02_equiv_%s.json" % A.mode), "w"), indent=1)
        print(json.dumps(rec), flush=True)
        print("EQUIV DONE" if rec["identical"] else "EQUIV FAILED", flush=True)
        return
    if A.cmd == "replay":
        jobs = [(l, "released", A.shim, os.path.join(A.out, "replay_released")) for l in logs]
        with Pool(min(A.procs, len(jobs))) as pool:
            pool.map(_job, jobs, chunksize=1)
        ref = np.load(A.ref, allow_pickle=False)
        rec = {"logs": logs, "per_log": {}}
        allsame = True
        for l in logs:
            m = ref["log_id"] == l
            r = {k: ref[k][m] for k in ("ts", "track_id", "name", "x", "y", "z", "yaw", "vx", "vy", "l", "w", "h", "score")}
            n = np.load(os.path.join(A.out, "replay_released", "trk10_%s.npz" % l), allow_pickle=False)
            same_rows = len(r["ts"]) == len(n["ts"])
            d = {"rows_v01": int(len(r["ts"])), "rows_replay": int(len(n["ts"])), "same_rows": bool(same_rows)}
            if same_rows:
                d["same_ts_ids_names"] = bool((r["ts"] == n["ts"]).all() and (r["track_id"] == n["track_id"]).all() and (r["name"] == n["name"]).all())
                d["max_abs_diff"] = {k: float(np.abs(r[k].astype(np.float64) - n[k].astype(np.float64)).max()) if len(r[k]) else 0.0 for k in ("x", "y", "z", "yaw", "vx", "vy", "l", "w", "h", "score")}
                allsame &= d["same_ts_ids_names"]
            else:
                allsame = False
            rec["per_log"][l] = d
        rec["all_same_rows_ids"] = bool(allsame)
        json.dump(rec, open(os.path.join(A.out, "ab3dmot_v02_replay_released.json"), "w"), indent=1)
        print(json.dumps({"all_same_rows_ids": rec["all_same_rows_ids"]}), flush=True)
        print("REPLAY DONE", flush=True)
        return
    od = os.path.join(A.out, A.mode)
    todo = [l for l in logs if not os.path.exists(os.path.join(od, "trk10_%s.npz" % l))]
    t0 = time.time()
    with Pool(A.procs) as pool:
        for n, m in enumerate(pool.imap_unordered(_job, [(l, A.mode, A.shim, od) for l in todo], chunksize=1)):
            print("%d/%d %s rows=%d tracks=%d held_back=%d topk_bind=%d %.0fs (wall %.0fs)" % (n + 1, len(todo), m["log"], m["track_rows"], m["tracks"],
                  m["rows_held_back_by_min_hits"], m["topk_binding_sweeps"], m["seconds"], time.time() - t0), flush=True)
    print("TRACK10 DONE", A.mode, flush=True)


if __name__ == "__main__":
    main()
