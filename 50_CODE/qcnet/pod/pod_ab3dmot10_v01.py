"""pod_ab3dmot10_v01 (QCNet arm, 2 Nov 2026): LT3D's AB3DMOT at 10 Hz on LT3D CenterPoint detections of every sweep.
Design: 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md section 8.

Per log, in the LT3D venv (LT3D root on sys.path; its tracking/ and data/ modules at commit e33189aa):
  frames  = data.utils.unpack_predictions(outputs, AV2_CLASS_NAMES), with seq_id and timestamp_ns from the infos (as
            data.av2_adapter.av2_load_predictions_and_labels does through annotate_frame_metadata), grouped and time-sorted
            by data.utils.group_frames, moved to the city frame by data.av2_adapter.transform_to_global_reference
  loop    = tracking/test_tracker.py's loop: score > 0.1 over all classes, top 500 per frame, tracker.step(..., dt),
            keep active tracks; AB3DMOT(classes=the three analysis classes, max_age=3) (one independent SingleClassMOT per
            class, so tracking only these three gives the same tracks for them as tracking all 26)
  ids     = KalmanBoxTracker.count reset to 0 per log, so a log's ids do not depend on which worker ran it
  output  = trk10_<log>.npz (pickle-free): ts, track_id, name, x, y, z, yaw, vx, vy, l, w, h, score (the matched detection)
--shim: tracking.ab3dmot.associate_detections_to_tracks replaced by a copy that skips iou3d for pairs whose BEV
footprints cannot overlap (iou3d returns exactly 0.0 there); --equiv N runs the first N logs both ways and compares.
Usage: python pod_ab3dmot10_v01.py --lt3d <root> --per-log <dir> --data <val dir> --out <dir> --procs N [--shim] [--equiv N]
"""
import argparse
import json
import os
import pickle
import sys
import time
from multiprocessing import Pool

import numpy as np

CLASSES3 = ["REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST"]
SCORE_THRESHOLD, KEEP_TOP_K, MAX_AGE = 0.1, 500, 3  # test_tracker.py defaults
A = None


def set_association(shim):
    """Select LT3D's native association or the exact-zero shim for this job (workers are reused across jobs)."""
    import tracking.ab3dmot as ab
    if not hasattr(ab, "_native_associate"):
        ab._native_associate = ab.associate_detections_to_tracks
        ab._shim_associate = make_shim(ab)
    ab.associate_detections_to_tracks = ab._shim_associate if shim else ab._native_associate


def make_shim(ab):
    from scipy.optimize import linear_sum_assignment
    orig_iou3d = ab.iou3d

    def bev_disc(c8):
        # kitti-camera corners (8, 3); BEV = (x, z) of the 4 bottom corners
        q = c8[:4][:, [0, 2]]
        ctr = q.mean(0)
        return ctr, np.sqrt(((q - ctr) ** 2).sum(1)).max()

    def associate_fast(detections, tracks, iou_threshold=0.1, match_algorithm="greedy"):
        # line-for-line copy of tracking.ab3dmot.associate_detections_to_tracks, except the iou_matrix loop
        if len(tracks) == 0:
            return (np.empty((0, 2), dtype=int), np.arange(len(detections)), np.empty((0, 8, 3), dtype=int))
        iou_matrix = np.zeros((len(detections), len(tracks)), dtype=np.float32)
        dd = [bev_disc(d) for d in detections]
        tt = [bev_disc(t) for t in tracks]
        for d, det in enumerate(detections):
            for t, trk in enumerate(tracks):
                if np.sqrt(((dd[d][0] - tt[t][0]) ** 2).sum()) > dd[d][1] + tt[t][1] + 0.01:
                    vol = ab.box3d_vol(det) + ab.box3d_vol(trk)
                    if vol > 0:
                        continue  # disjoint footprints: iou3d would return exactly 0.0
                iou_matrix[d, t] = orig_iou3d(det, trk)[0]
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


def track_log(log, shim, out_dir):
    set_association(shim)
    import tracking.ab3dmot as ab
    from data.utils import AV2_CLASS_NAMES, group_frames, index_array_values, unpack_predictions
    from data.av2_adapter import read_city_SE3_ego_by_seq_id, transform_to_global_reference
    t0 = time.time()
    d = pickle.load(open(os.path.join(A.per_log, log + ".pkl"), "rb"))
    frames = unpack_predictions(d["outputs"], AV2_CLASS_NAMES)
    for f, info in zip(frames, d["infos"]):
        f["seq_id"] = info["log_id"]
        f["timestamp_ns"] = info["timestamp"]
    seqs = group_frames(frames)
    assert list(seqs) == [log]
    seqs = transform_to_global_reference(seqs, read_city_SE3_ego_by_seq_id(A.data, seq_ids=[log]))
    frames = seqs[log]
    ab.KalmanBoxTracker.count = 0
    tracker = ab.AB3DMOT(classes=CLASSES3, max_age=MAX_AGE)
    tracker.reset()
    last_t = frames[0]["timestamp_ns"]
    out = {k: [] for k in ("ts", "track_id", "name", "x", "y", "z", "yaw", "vx", "vy", "l", "w", "h", "score")}
    n_in = 0
    for frame in frames:
        time_delta_seconds = (frame["timestamp_ns"] - last_t) * 1e-9
        last_t = frame["timestamp_ns"]
        filtered = index_array_values(frame, frame["score"] > SCORE_THRESHOLD)
        if len(filtered["score"]) > 0:
            k = min(len(filtered["score"]), KEEP_TOP_K) - 1
            filtered = index_array_values(filtered, filtered["score"] >= -np.partition(-filtered["score"], k)[k])
        n_in += int(np.isin(filtered["name"], CLASSES3).sum())
        tf = tracker.step(filtered, time_delta_seconds)
        if not tf or "active" not in tf:
            continue
        tf = index_array_values(tf, tf["active"] > 0)
        n = len(tf["track_id"])
        if n == 0:
            continue
        out["ts"].append(np.full(n, frame["timestamp_ns"], np.int64))
        out["track_id"].append(tf["track_id"].astype(np.int64))
        out["name"].append(tf["name"].astype(str))
        out["x"].append(tf["translation_m"][:, 0]); out["y"].append(tf["translation_m"][:, 1]); out["z"].append(tf["translation_m"][:, 2])
        out["yaw"].append(tf["yaw"]); out["vx"].append(tf["velocity_m_per_s"][:, 0]); out["vy"].append(tf["velocity_m_per_s"][:, 1])
        out["l"].append(tf["size"][:, 0]); out["w"].append(tf["size"][:, 1]); out["h"].append(tf["size"][:, 2])
        out["score"].append(tf["score"])
    res = {k: (np.concatenate(v) if v else np.zeros(0)) for k, v in out.items()}
    res["name"] = res["name"].astype(str)
    os.makedirs(out_dir, exist_ok=True)
    p = os.path.join(out_dir, "trk10_%s.npz" % log)
    np.savez_compressed(p + ".part.npz", **res)
    os.replace(p + ".part.npz", p)
    meta = {"log": log, "frames": len(frames), "dets_in_3cls_after_filter": n_in, "track_rows": int(len(res["ts"])),
            "tracks": int(len(np.unique(res["track_id"]))) if len(res["track_id"]) else 0, "seconds": time.time() - t0, "shim": shim}
    json.dump(meta, open(p.replace(".npz", ".json"), "w"))
    return meta


def _job(args):
    return track_log(*args)


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--per-log", dest="per_log", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=8)
    ap.add_argument("--shim", action="store_true")
    ap.add_argument("--equiv", type=int, default=0)
    A = ap.parse_args()
    sys.path.insert(0, A.lt3d)
    os.chdir(A.lt3d)
    logs = sorted(f[:-4] for f in os.listdir(A.per_log) if f.endswith(".pkl"))
    if A.equiv:
        sel = logs[: A.equiv]
        with Pool(min(A.procs, 2 * len(sel))) as pool:
            ma = pool.map(_job, [(l, False, os.path.join(A.out, "equiv_native")) for l in sel] + [(l, True, os.path.join(A.out, "equiv_shim")) for l in sel], chunksize=1)
        rec = {"logs": sel, "identical": True, "seconds_native": sum(m["seconds"] for m in ma[: len(sel)]), "seconds_shim": sum(m["seconds"] for m in ma[len(sel):])}
        for l in sel:
            a = np.load(os.path.join(A.out, "equiv_native", "trk10_%s.npz" % l), allow_pickle=False)
            b = np.load(os.path.join(A.out, "equiv_shim", "trk10_%s.npz" % l), allow_pickle=False)
            same = all(a[k].shape == b[k].shape and (a[k] == b[k]).all() for k in a.files)
            rec[l] = {"rows": int(len(a["ts"])), "identical": bool(same)}
            rec["identical"] &= bool(same)
        json.dump(rec, open(os.path.join(A.out, "ab3dmot_equiv_v01.json"), "w"), indent=1)
        print(json.dumps(rec), flush=True)
        print("EQUIV DONE" if rec["identical"] else "EQUIV FAILED", flush=True)
        return
    todo = [l for l in logs if not os.path.exists(os.path.join(A.out, "logs10", "trk10_%s.npz" % l))]
    t0 = time.time()
    with Pool(A.procs) as pool:
        for n, m in enumerate(pool.imap_unordered(_job, [(l, A.shim, os.path.join(A.out, "logs10")) for l in todo], chunksize=1)):
            print("%d/%d %s rows=%d tracks=%d %.0fs (wall %.0fs)" % (n + 1, len(todo), m["log"], m["track_rows"], m["tracks"], m["seconds"], time.time() - t0), flush=True)
    print("TRACK10 DONE", flush=True)


if __name__ == "__main__":
    main()
