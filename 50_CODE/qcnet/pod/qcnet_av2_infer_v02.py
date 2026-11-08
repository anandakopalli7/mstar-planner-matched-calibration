"""qcnet_av2_infer_v02 (QCNet arm, addendum A, 2 Nov 2026): qcnet_av2_infer_v01 with every scene re-centred on the ego
position at its origin t0 (D16 v04 Choice 17; design addendum A2), sweeps from the v01 fetch manifest (no lidar on the pod),
and the matched-AB3DMOT tracker files (addendum A1). Everything else is v01's code, imported from qcnet_av2_infer_v01.

Re-centring: o = ego (x, y) at t0 (float64). Agents: positions - o in float64 before QCNet's get_agent_features. Map: every
(x, y) point of the log map JSON - o in float64, parsed by av2's ArgoverseStaticMap.from_json from a temporary file, av2's
centerlines, QCNet's get_map_features per scene. Back to the city frame: mu = R(theta) loc + p0 + o (float64); Sigma unchanged.
Scenes are built by CPU worker processes (forked before CUDA is touched) while the GPU runs the model.
Outcome-blind as v01: no GT position after t0 is read; the target is found by timestamp; visibility at the target by existence.
Usage:
  python -I qcnet_av2_infer_v02.py --qcnet <repo> --ckpt <ckpt> --data <val dir> --sweeps <sweeps_by_log.json> --source gt|trk
         [--trk <dir of trk10_<log>.npz>] --out <dir> [--batch 4] [--workers 8] [--logs N]
  python -I qcnet_av2_infer_v02.py --merge --out <dir> --source gt|trk --name <file.npz>
"""
import argparse
import copy
import glob
import json
import os
import sys
import tempfile
import time

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
A = None
_DS = None


def V1():
    import qcnet_av2_infer_v01 as Q  # v01 helpers (imported after the QCNet root is on sys.path)
    return Q


def load_log(log):
    """v01's load_log with the sweep list from the manifest instead of the lidar folder."""
    import pandas as pd
    Q = V1()
    d = os.path.join(A.data, log)
    sweeps = np.array(json.load(open(A.sweeps))[log], np.int64)
    pose = pd.read_feather(os.path.join(d, "city_SE3_egovehicle.feather"))
    pose = pose[pose["timestamp_ns"].isin(sweeps)].sort_values("timestamp_ns").reset_index(drop=True)
    assert len(pose) == len(sweeps), (log, "pose missing for some sweeps")
    Rp = Q.quat_to_mat(pose[["qw", "qx", "qy", "qz"]].to_numpy())
    tp = pose[["tx_m", "ty_m", "tz_m"]].to_numpy(np.float64)
    pose_idx = {int(t): k for k, t in enumerate(pose["timestamp_ns"].to_numpy())}
    av = {"ts": pose["timestamp_ns"].to_numpy(np.int64), "x": tp[:, 0], "y": tp[:, 1], "yaw": np.arctan2(Rp[:, 1, 0], Rp[:, 0, 0])}
    av["vx"], av["vy"] = Q.backward_velocity(np.zeros(len(sweeps), np.int64), av["ts"], av["x"], av["y"])
    ann = pd.read_feather(os.path.join(d, "annotations.feather"))
    ann = ann[ann["category"].isin(Q.CLASSES3)].reset_index(drop=True)
    k = np.array([pose_idx[int(t)] for t in ann["timestamp_ns"].to_numpy()], np.int64)
    t_ego = ann[["tx_m", "ty_m", "tz_m"]].to_numpy(np.float64)
    t_city = np.einsum("nij,nj->ni", Rp[k], t_ego) + tp[k]
    R_city = np.einsum("nij,njk->nik", Rp[k], Q.quat_to_mat(ann[["qw", "qx", "qy", "qz"]].to_numpy()))
    gt = {"ts": ann["timestamp_ns"].to_numpy(np.int64), "id": ann["track_uuid"].to_numpy().astype(str),
          "cat": ann["category"].to_numpy().astype(str), "x": t_city[:, 0], "y": t_city[:, 1],
          "yaw": np.arctan2(R_city[:, 1, 0], R_city[:, 0, 0]), "npts": ann["num_interior_pts"].to_numpy(np.int64),
          "in_sq": (np.abs(t_ego[:, 0]) <= Q.RANGE_M) & (np.abs(t_ego[:, 1]) <= Q.RANGE_M)}
    o = np.lexsort((gt["ts"], gt["id"]))
    gt = {kk: v[o] for kk, v in gt.items()}
    gt["vx"], gt["vy"] = Q.backward_velocity(gt["id"], gt["ts"], gt["x"], gt["y"])
    trk = None
    if A.source == "trk":
        z = np.load(os.path.join(A.trk, "trk10_%s.npz" % log), allow_pickle=False)
        keep = np.isin(z["name"], Q.CLASSES3)
        trk = {"ts": z["ts"][keep].astype(np.int64), "id": np.char.add("t", z["track_id"][keep].astype(str)),
               "cat": z["name"][keep].astype(str), "x": z["x"][keep].astype(np.float64), "y": z["y"][keep].astype(np.float64),
               "yaw": z["yaw"][keep].astype(np.float64), "vx": z["vx"][keep].astype(np.float64), "vy": z["vy"][keep].astype(np.float64),
               "tid": z["track_id"][keep].astype(np.int64)}
    maps = sorted(glob.glob(os.path.join(d, "map", "log_map_archive_*.json")))
    assert maps, (log, "no log map")
    return sweeps, av, gt, trk, maps[0]


def shift_points(obj, ox, oy):
    """Copy of a map JSON object with every {x, y, ...} point moved by (-ox, -oy), in float64."""
    if isinstance(obj, dict):
        if "x" in obj and "y" in obj and isinstance(obj["x"], (int, float)):
            d = dict(obj)
            d["x"] = float(obj["x"]) - ox
            d["y"] = float(obj["y"]) - oy
            return d
        return {k: shift_points(v, ox, oy) for k, v in obj.items()}
    if isinstance(obj, list):
        return [shift_points(v, ox, oy) for v in obj]
    return obj


def map_features_shifted(ds, map_json, map_name, ox, oy, tmpdir):
    """QCNet's map features of the log map moved by (-ox, -oy) (av2's parser and centerlines, as v01)."""
    from pathlib import Path
    from av2.map.map_api import ArgoverseStaticMap
    p = os.path.join(tmpdir, map_name)
    with open(p, "w") as f:
        json.dump(shift_points(map_json, ox, oy), f)
    map_api = ArgoverseStaticMap.from_json(Path(p))

    class _XYZ:
        def __init__(self, xyz):
            self.xyz = xyz
    centerlines = {lid: _XYZ(map_api.get_lane_segment_centerline(lid)) for lid in map_api.vector_lane_segments}
    feats = ds.get_map_features(map_api, centerlines)
    os.remove(p)
    return feats


def scene_df_recentred(step_ts, av, tab, use_mask, ox, oy):
    df = V1().scene_df(step_ts, av, tab, use_mask)
    df["position_x"] = df["position_x"].to_numpy(np.float64) - ox  # float64, before QCNet's float32 cast
    df["position_y"] = df["position_y"].to_numpy(np.float64) - oy
    return df


def build_log(log, tables=None, map_override=None, origins=None):
    """CPU part for one log: scenes (HeteroData) and item records, re-centred. tables / map_override: frame tests only."""
    global _DS
    from torch_geometric.data import HeteroData
    Q = V1()
    if _DS is None:
        _DS = Q.make_dataset_helper(os.path.join(tempfile.gettempdir(), "qcnet_v02_ds_%d" % os.getpid()))
    ds = _DS
    t_log = time.time()
    sweeps, av, gt, trk, map_path = load_log(log) if tables is None else tables
    map_json = json.load(open(map_path)) if map_override is None else map_override
    has_cl = all("centerline" in ls for ls in map_json["lane_segments"].values()) and len(map_json["lane_segments"]) > 0
    assert not has_cl, "a Sensor log map with centerlines: v01's rule would read them; not expected (0/150 in v01)"
    city = os.path.basename(map_path).split("____")[-1].split("_city")[0] if "____" in map_path else "unknown"
    tmpdir = tempfile.mkdtemp(prefix="qcnet_map_%d_" % os.getpid())
    tab = gt if A.source == "gt" else trk
    use_mask = gt["in_sq"] if A.source == "gt" else np.ones(len(trk["ts"]), bool)
    vis_key = set(zip(gt["ts"][gt["npts"] >= 1].tolist(), gt["id"][gt["npts"] >= 1].tolist()))
    av_by_ts = {int(t): i for i, t in enumerate(av["ts"])}
    scenes, items = [], []
    cnt = {"origins": 0, "origins_no_target": 0, "trk_at_origin": 0, "trk_matched": 0, "gt_visible_at_origin": 0, "gt_visible_in_square": 0}
    polys = []
    sel = range(0, len(sweeps), Q.ORIGIN_EVERY) if origins is None else origins
    for s in sel:
        t0 = int(sweeps[s]); cnt["origins"] += 1
        tt, jit = Q.target_sweep(sweeps, t0)
        if tt is None:
            cnt["origins_no_target"] += 1
            continue
        grid = Q.step_grid(sweeps, t0)
        g0 = (gt["ts"] == t0) & (gt["npts"] >= 1)
        cnt["gt_visible_at_origin"] += int(g0.sum()); cnt["gt_visible_in_square"] += int((g0 & gt["in_sq"]).sum())
        if A.source == "gt":
            pairs = [(gt["id"][i], i, -1) for i in np.nonzero(g0 & gt["in_sq"])[0]]
        else:
            pairs = []
            r0 = np.nonzero(trk["ts"] == t0)[0]
            cnt["trk_at_origin"] += len(r0)
            for c in Q.CLASSES3:
                rt = r0[trk["cat"][r0] == c]
                rg = np.nonzero(g0 & (gt["cat"] == c))[0]
                for i, j in Q.hungarian(np.c_[trk["x"][rt], trk["y"][rt]], np.c_[gt["x"][rg], gt["y"][rg]]):
                    pairs.append((trk["id"][rt[i]], rg[j], int(trk["tid"][rt[i]])))
            cnt["trk_matched"] += len(pairs)
        if not pairs:
            continue
        ia = av_by_ts[t0]
        ox, oy = float(av["x"][ia]), float(av["y"][ia])
        df = scene_df_recentred(grid, av, tab, use_mask, ox, oy)
        af = ds.get_agent_features(df)
        mfeat = map_features_shifted(ds, map_json, os.path.basename(map_path), ox, oy, tmpdir)
        polys.append(int(mfeat["map_polygon"]["num_nodes"]))
        valid_raw = np.zeros((af["num_nodes"], Q.NH), bool)
        idmap = {aid: k for k, aid in enumerate(af["id"])}
        for aid, step in zip(df["track_id"].to_numpy(), df["timestep"].to_numpy()):
            valid_raw[idmap[aid], step] = True
        dd = {"scenario_id": "%s_%d_%s" % (log, t0, A.source), "city": city, "agent": af}
        dd.update(mfeat)
        scenes.append(HeteroData(dd))
        for aid, gi, tid in pairs:
            k = idmap[aid]
            items.append({"scene": len(scenes) - 1, "local": k, "sample_token": "%s_%d" % (log, t0), "log_id": log, "origin_ts": t0,
                          "instance_token": gt["id"][gi], "category": gt["cat"][gi], "target_ts": tt, "jitter_ms": jit,
                          "n_hist": int(valid_raw[k].sum()), "vec_valid_now": bool(valid_raw[k, Q.NH - 2] and valid_raw[k, Q.NH - 1]),
                          "vis_target": (tt, gt["id"][gi]) in vis_key, "num_pts_origin": int(gt["npts"][gi]),
                          "track_id": tid, "n_agents_scene": int(af["num_nodes"]), "origin_x": ox, "origin_y": oy})
    os.rmdir(tmpdir)
    meta = dict(cnt, log=log, items=len(items), scenes=len(scenes), polygons_median=float(np.median(polys)) if polys else 0.0,
                map_has_centerline=False, city=city, build_seconds=time.time() - t_log, recentred=True)
    return log, scenes, items, meta


def infer_log(model, device, scenes, items, batch):
    import torch
    Q = V1()
    out, i, B = [], 0, batch
    while i < len(scenes):
        chunk = scenes[i:i + B]
        try:
            res = Q.forward(model, chunk, device)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if B == 1:
                raise
            B = max(1, B // 2)
            print("OOM -> batch", B, flush=True)
            continue
        out.append((i,) + res)
        i += len(chunk)
    keys = ("sample_token", "log_id", "origin_ts", "instance_token", "category", "target_ts", "jitter_ms", "n_hist", "vec_valid_now",
            "vis_target", "num_pts_origin", "track_id", "n_agents_scene", "origin_x", "origin_y")
    rows = {k: [] for k in keys}
    g = {"loc": [], "b": [], "lg": [], "th": [], "p0": []}
    for (i0, loc, sc, lg, hd, ps, ptr) in out:
        for it in items:
            if not (i0 <= it["scene"] < i0 + len(ptr) - 1):
                continue
            gidx = int(ptr[it["scene"] - i0]) + it["local"]
            g["loc"].append(loc[gidx, :, Q.FUT_IDX]); g["b"].append(sc[gidx, :, Q.FUT_IDX]); g["lg"].append(lg[gidx])
            g["th"].append(hd[gidx, Q.NH - 1]); g["p0"].append(ps[gidx, Q.NH - 1, :2])
            for k in keys:
                rows[k].append(it[k])
    res = {k: np.asarray(v) for k, v in rows.items()}
    if g["loc"]:
        der = Q.derive(np.stack(g["loc"]), np.stack(g["b"]), np.stack(g["lg"]), np.asarray(g["th"]), np.stack(g["p0"]))
        o = np.stack([res["origin_x"], res["origin_y"]], 1)
        der["loc"] = der["loc"] + o[:, None, :]  # back to the city frame, float64
        der["v1_mu"] = der["v1_mu"] + o
        der["v2_mu"] = der["v2_mu"] + o
        res.update(der)
        res["theta"] = np.asarray(g["th"])
        res["p0_local"] = np.stack(g["p0"])
        res["p0"] = res["p0_local"] + o
    return res, B


def merge():
    parts = sorted(glob.glob(os.path.join(A.out, "per_log", "%s_*.npz" % A.source)))
    acc, keys = {}, None
    for p in parts:
        z = np.load(p, allow_pickle=False)
        if "sample_token" not in z.files or len(z["sample_token"]) == 0:
            continue
        keys = keys or z.files
        for k in keys:
            acc.setdefault(k, []).append(z[k])
    res = {k: np.concatenate(v) for k, v in acc.items()}
    key = np.char.add(np.char.add(res["sample_token"].astype(str), "|"), res["instance_token"].astype(str))
    assert len(np.unique(key)) == len(key), "duplicate item keys"
    np.savez_compressed(os.path.join(A.out, A.name), **res)
    metas = [json.load(open(m)) for m in sorted(glob.glob(os.path.join(A.out, "per_log", "%s_*.json" % A.source)))]
    tot = {k: sum(m[k] for m in metas) for k in ("origins", "origins_no_target", "trk_at_origin", "trk_matched", "gt_visible_at_origin", "gt_visible_in_square", "items", "scenes")}
    tot.update(logs=len(metas), recentred=True, build_seconds=sum(m["build_seconds"] for m in metas), infer_seconds=sum(m.get("infer_seconds", 0) for m in metas),
               finite_all=bool(res["finite"].all()), pd_v1_all=bool(res["pd_v1"].all()), pd_v2_all=bool(res["pd_v2"].all()), pd_modes_all=bool(res["pd_modes"].all()),
               non_finite_rows=int((~res["finite"]).sum()), non_pd_v2_rows=int((~res["pd_v2"]).sum()))
    json.dump(tot, open(os.path.join(A.out, A.name.replace(".npz", "_summary.json")), "w"), indent=1)
    print(json.dumps(tot), flush=True)
    print("MERGE DONE", flush=True)


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--qcnet")
    ap.add_argument("--ckpt")
    ap.add_argument("--data")
    ap.add_argument("--sweeps")
    ap.add_argument("--source", choices=["gt", "trk"], required=True)
    ap.add_argument("--trk")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--logs", type=int, default=0)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--name", default="")
    A = ap.parse_args()
    if A.merge:
        return merge()
    sys.path.insert(0, A.qcnet)
    from multiprocessing import get_context
    os.makedirs(os.path.join(A.out, "per_log"), exist_ok=True)
    logs = sorted(json.load(open(A.sweeps)))
    if A.logs:
        logs = logs[: A.logs]
    todo = [l for l in logs if not os.path.exists(os.path.join(A.out, "per_log", "%s_%s.npz" % (A.source, l)))]
    pool = get_context("fork").Pool(A.workers)  # forked before CUDA is initialised; workers only build scenes on the CPU
    import torch
    torch.set_grad_enabled(False)
    device = torch.device("cuda")
    model, how = V1().load_model(A.qcnet, A.ckpt, device)
    print("model loaded via", how, "logs to do", len(todo), flush=True)
    t0 = time.time()
    for n, (log, scenes, items, meta) in enumerate(pool.imap(build_log, todo, chunksize=1)):
        ti = time.time()
        res, B = infer_log(model, device, scenes, items, A.batch)
        meta["infer_seconds"] = time.time() - ti
        meta["final_batch"] = B
        p = os.path.join(A.out, "per_log", "%s_%s.npz" % (A.source, log))
        np.savez_compressed(p + ".part.npz", **res)
        os.replace(p + ".part.npz", p)
        json.dump(meta, open(p.replace(".npz", ".json"), "w"), indent=1)
        print("%d/%d %s items=%d scenes=%d build %.1fs infer %.1fs (total %.0fs)" % (n + 1, len(todo), log, meta["items"], meta["scenes"], meta["build_seconds"], meta["infer_seconds"], time.time() - t0), flush=True)
    pool.close()
    pool.join()
    print("INFER DONE", A.source, flush=True)


if __name__ == "__main__":
    main()
