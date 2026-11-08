"""qcnet_av2_infer_v01 (QCNet arm, 2 Nov 2026): QCNet (AV2 checkpoint) on the 2 Hz origins of AV2 Sensor val,
with ground-truth (--source gt) or 10 Hz tracker (--source trk) histories. Design: 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md.

Per log: the log's sweeps, ego poses, annotations and vector map; QCNet's own map features once per log (they do not depend
on the origin); per 2 Hz origin (every 5th sweep from sweep 0) one test-split scene of 50 historical steps on the nominal
0.1 s grid (nearest sweep within 20 ms), built with QCNet's own ArgoverseV2Dataset.get_agent_features; batched forward in
eval mode; for every item agent the six modes at future step 19 (2.0 s): world-frame locations, agent-frame Laplace scales,
mixture weights; per-mode covariance R(theta) diag(2 b^2) R(theta)^T; V1 (most likely mode) and V2 (moment-matched).

Outcome-blind (design section 0): no GT position after the origin is read. The target sweep is found by timestamp only; the
item's presence there is read as existence with num_interior_pts >= 1 (a set of uuids), never its position. Checks: finite,
positive definite. Output: one pickle-free npz per log under --out/per_log, merged by --merge.

Usage:
  python -I qcnet_av2_infer_v01.py --qcnet <repo> --ckpt <ckpt> --data <val dir> --source gt|trk [--trk <dir of per-log npz>]
         --out <dir> [--batch 4] [--logs N] [--bscheck]
  python -I qcnet_av2_infer_v01.py --merge --out <dir> --source gt|trk --name <file.npz>
"""
import argparse
import glob
import json
import math
import os
import sys
import time

import numpy as np

STEP_NS = 100_000_000
TOL_NS = 20_000_000
HORIZON_NS = 2_000_000_000
NH = 50
FUT_IDX = 19
ORIGIN_EVERY = 5
CLASSES3 = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST")
QTYPE = {"REGULAR_VEHICLE": "vehicle", "PEDESTRIAN": "pedestrian", "BICYCLIST": "cyclist", "AV": "vehicle"}
RANGE_M = 54.0
GATE_M = 2.0
VEL_MAX_DT_S = 0.25


# ---------------------------------------------------------------- geometry
def quat_to_mat(q):
    """(N, 4) w-first unit quaternions -> (N, 3, 3) rotation matrices."""
    q = np.asarray(q, np.float64)
    q = q / np.linalg.norm(q, axis=1, keepdims=True)
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    R = np.empty((len(q), 3, 3))
    R[:, 0, 0] = 1 - 2 * (y * y + z * z); R[:, 0, 1] = 2 * (x * y - z * w); R[:, 0, 2] = 2 * (x * z + y * w)
    R[:, 1, 0] = 2 * (x * y + z * w); R[:, 1, 1] = 1 - 2 * (x * x + z * z); R[:, 1, 2] = 2 * (y * z - x * w)
    R[:, 2, 0] = 2 * (x * z - y * w); R[:, 2, 1] = 2 * (y * z + x * w); R[:, 2, 2] = 1 - 2 * (x * x + y * y)
    return R


def backward_velocity(ids, ts, x, y):
    """Causal velocity: (p_i - p_prev) / dt to the same id's previous row if dt <= 0.25 s, else 0. Rows sorted by (id, ts)."""
    vx = np.zeros(len(ts)); vy = np.zeros(len(ts))
    same = np.r_[False, ids[1:] == ids[:-1]]
    dt = np.r_[0.0, (ts[1:] - ts[:-1]) * 1e-9]
    ok = same & (dt > 0) & (dt <= VEL_MAX_DT_S)
    i = np.nonzero(ok)[0]
    vx[i] = (x[i] - x[i - 1]) / dt[i]
    vy[i] = (y[i] - y[i - 1]) / dt[i]
    return vx, vy


# ---------------------------------------------------------------- per-log tables
def load_log(data_dir, log, source, trk_dir):
    import pandas as pd
    d = os.path.join(data_dir, log)
    sweeps = np.array(sorted(int(f.split(".")[0]) for f in os.listdir(os.path.join(d, "sensors", "lidar")) if f.endswith(".feather")), np.int64)
    pose = pd.read_feather(os.path.join(d, "city_SE3_egovehicle.feather"))
    pose = pose[pose["timestamp_ns"].isin(sweeps)].sort_values("timestamp_ns").reset_index(drop=True)
    assert len(pose) == len(sweeps), (log, "pose missing for some sweeps")
    Rp = quat_to_mat(pose[["qw", "qx", "qy", "qz"]].to_numpy())
    tp = pose[["tx_m", "ty_m", "tz_m"]].to_numpy(np.float64)
    pose_idx = {int(t): k for k, t in enumerate(pose["timestamp_ns"].to_numpy())}
    av = {"ts": pose["timestamp_ns"].to_numpy(np.int64), "x": tp[:, 0], "y": tp[:, 1], "yaw": np.arctan2(Rp[:, 1, 0], Rp[:, 0, 0])}
    av["vx"], av["vy"] = backward_velocity(np.zeros(len(sweeps), np.int64), av["ts"], av["x"], av["y"])

    ann = pd.read_feather(os.path.join(d, "annotations.feather"))
    ann = ann[ann["category"].isin(CLASSES3)].reset_index(drop=True)
    k = np.array([pose_idx[int(t)] for t in ann["timestamp_ns"].to_numpy()], np.int64)
    t_ego = ann[["tx_m", "ty_m", "tz_m"]].to_numpy(np.float64)
    t_city = np.einsum("nij,nj->ni", Rp[k], t_ego) + tp[k]
    R_city = np.einsum("nij,njk->nik", Rp[k], quat_to_mat(ann[["qw", "qx", "qy", "qz"]].to_numpy()))
    gt = {"ts": ann["timestamp_ns"].to_numpy(np.int64), "id": ann["track_uuid"].to_numpy().astype(str),
          "cat": ann["category"].to_numpy().astype(str), "x": t_city[:, 0], "y": t_city[:, 1],
          "yaw": np.arctan2(R_city[:, 1, 0], R_city[:, 0, 0]), "npts": ann["num_interior_pts"].to_numpy(np.int64),
          "in_sq": (np.abs(t_ego[:, 0]) <= RANGE_M) & (np.abs(t_ego[:, 1]) <= RANGE_M)}
    o = np.lexsort((gt["ts"], gt["id"]))
    gt = {kk: v[o] for kk, v in gt.items()}
    gt["vx"], gt["vy"] = backward_velocity(gt["id"], gt["ts"], gt["x"], gt["y"])

    trk = None
    if source == "trk":
        z = np.load(os.path.join(trk_dir, "trk10_%s.npz" % log), allow_pickle=False)
        keep = np.isin(z["name"], CLASSES3)
        trk = {"ts": z["ts"][keep].astype(np.int64), "id": np.char.add("t", z["track_id"][keep].astype(str)),
               "cat": z["name"][keep].astype(str), "x": z["x"][keep].astype(np.float64), "y": z["y"][keep].astype(np.float64),
               "yaw": z["yaw"][keep].astype(np.float64), "vx": z["vx"][keep].astype(np.float64), "vy": z["vy"][keep].astype(np.float64),
               "tid": z["track_id"][keep].astype(np.int64)}
    maps = sorted(glob.glob(os.path.join(d, "map", "log_map_archive_*.json")))
    assert maps, (log, "no log map")
    return sweeps, av, gt, trk, maps[0]


def map_features(ds, map_path):
    from av2.map.map_api import ArgoverseStaticMap
    from av2.map.map_primitives import Polyline
    from av2.utils.io import read_json_file
    map_data = read_json_file(map_path)
    lss = list(map_data["lane_segments"].values())
    has_cl = len(lss) > 0 and all("centerline" in ls for ls in lss)
    map_api = ArgoverseStaticMap.from_json(__import__("pathlib").Path(map_path))
    if has_cl:
        centerlines = {ls["id"]: Polyline.from_json_data(ls["centerline"]) for ls in lss}
    else:
        class _XYZ:  # the av2 API's own centerline (compute_midpoint_line of the two boundaries)
            def __init__(self, xyz):
                self.xyz = xyz
        centerlines = {lid: _XYZ(map_api.get_lane_segment_centerline(lid)) for lid in map_api.vector_lane_segments}
    feats = ds.get_map_features(map_api, centerlines)
    city = os.path.basename(map_path).split("____")[-1].split("_city")[0] if "____" in map_path else "unknown"
    return feats, has_cl, city, int(feats["map_polygon"]["num_nodes"])


def step_grid(sweeps, t0):
    nominal = t0 - STEP_NS * (NH - 1 - np.arange(NH, dtype=np.int64))
    j = np.clip(np.searchsorted(sweeps, nominal), 1, len(sweeps) - 1)
    jj = np.where(np.abs(sweeps[j - 1] - nominal) <= np.abs(sweeps[j] - nominal), j - 1, j)
    ok = np.abs(sweeps[jj] - nominal) <= TOL_NS
    return np.where(ok, sweeps[jj], -1)


def target_sweep(sweeps, t0):
    nominal = t0 + HORIZON_NS
    j = int(np.argmin(np.abs(sweeps - nominal)))
    return (int(sweeps[j]), (int(sweeps[j]) - nominal) / 1e6) if abs(int(sweeps[j]) - nominal) <= TOL_NS else (None, None)


def scene_df(step_ts, av, tab, use_mask):
    """AV2-MF-schema DataFrame for one scene: AV + the source's agents at the grid's sweeps."""
    import pandas as pd
    ts2step = {int(t): i for i, t in enumerate(step_ts) if t >= 0}
    rows = []
    a = np.isin(av["ts"], list(ts2step))
    for i in np.nonzero(a)[0]:
        rows.append(("AV", "vehicle", 2, ts2step[int(av["ts"][i])], av["x"][i], av["y"][i], av["yaw"][i], av["vx"][i], av["vy"][i]))
    m = np.isin(tab["ts"], list(ts2step)) & use_mask
    for i in np.nonzero(m)[0]:
        rows.append((tab["id"][i], QTYPE[tab["cat"][i]], 2, ts2step[int(tab["ts"][i])], tab["x"][i], tab["y"][i], tab["yaw"][i], tab["vx"][i], tab["vy"][i]))
    df = pd.DataFrame(rows, columns=["track_id", "object_type", "object_category", "timestep", "position_x", "position_y", "heading", "velocity_x", "velocity_y"])
    df["timestep"] = df["timestep"].astype(np.int64)
    return df


def hungarian(trk_xy, gt_xy):
    from scipy.optimize import linear_sum_assignment
    if len(trk_xy) == 0 or len(gt_xy) == 0:
        return []
    D = np.linalg.norm(trk_xy[:, None, :] - gt_xy[None, :, :], axis=-1)
    r, c = linear_sum_assignment(np.where(D <= GATE_M, D, 1e6))
    return [(int(i), int(j)) for i, j in zip(r, c) if D[i, j] <= GATE_M]


# ---------------------------------------------------------------- model
def make_dataset_helper(scratch):
    from datasets.argoverse_v2_dataset import ArgoverseV2Dataset

    class _DS(ArgoverseV2Dataset):  # QCNet's feature code; downloading and processing switched off
        def _download(self):
            pass

        def _process(self):
            pass

    return _DS(root=scratch, split="test", raw_dir=os.path.join(scratch, "raw_none"), processed_dir=os.path.join(scratch, "proc_none"))


def load_model(qcnet, ckpt, device):
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # after the QCNet root, so QCNet's modules win
    from qcnet_ckpt_verify_v01 import load_ckpt
    from predictors import QCNet
    ck, how = load_ckpt(ckpt)
    model = QCNet(**dict(ck["hyper_parameters"]))
    model.load_state_dict(ck["state_dict"], strict=True)
    model.eval().to(device)
    return model, how


def forward(model, datas, device):
    import torch
    from torch_geometric.data import Batch
    b = Batch.from_data_list(datas).to(device)
    b["agent"]["av_index"] += b["agent"]["ptr"][:-1]  # as QCNet.test_step
    with torch.no_grad():
        pred = model(b)
    return (pred["loc_refine_pos"][..., :2].double().cpu().numpy(), pred["scale_refine_pos"][..., :2].double().cpu().numpy(),
            pred["pi"].double().cpu().numpy(), b["agent"]["heading"].double().cpu().numpy(), b["agent"]["position"].double().cpu().numpy(),
            b["agent"]["ptr"].cpu().numpy())


def derive(loc_l, b, logits, theta, p0):
    """loc_l, b: (n, 6, 2) agent frame at step 19; logits (n, 6); theta (n,); p0 (n, 2)."""
    c, s = np.cos(theta), np.sin(theta)
    R = np.stack([np.stack([c, -s], -1), np.stack([s, c], -1)], -2)  # (n, 2, 2): world = R local + p0
    loc = np.einsum("nij,nkj->nki", R, loc_l) + p0[:, None, :]
    pi = np.exp(logits - logits.max(1, keepdims=True)); pi = pi / pi.sum(1, keepdims=True)
    D = np.zeros(b.shape[:2] + (2, 2)); D[..., 0, 0] = 2 * b[..., 0] ** 2; D[..., 1, 1] = 2 * b[..., 1] ** 2
    cov = np.einsum("nij,nkjl,nml->nkim", R, D, R)
    k1 = pi.argmax(1)
    ar = np.arange(len(pi))
    v1_mu, v1_cov = loc[ar, k1], cov[ar, k1]
    v2_mu = np.einsum("nk,nki->ni", pi, loc)
    dd = loc - v2_mu[:, None, :]
    v2_cov = np.einsum("nk,nkij->nij", pi, cov + dd[..., :, None] * dd[..., None, :])
    def pd(m):
        m = 0.5 * (m + np.swapaxes(m, -1, -2))
        return np.linalg.eigvalsh(m)[..., 0] > 0
    allf = np.isfinite(loc).all((1, 2)) & np.isfinite(b).all((1, 2)) & np.isfinite(pi).all(1) & np.isfinite(v2_cov).all((1, 2))
    return dict(loc=loc, scale=b, pi=pi, cov_modes=cov, v1_mode=k1.astype(np.int8), v1_mu=v1_mu, v1_cov=v1_cov, v2_mu=v2_mu, v2_cov=v2_cov,
                finite=allf, pd_modes=pd(cov).all(1), pd_v1=pd(v1_cov), pd_v2=pd(v2_cov))


# ---------------------------------------------------------------- main loop
def run_log(log, A, ds, model, device):
    import torch
    from torch_geometric.data import HeteroData
    t_log = time.time()
    sweeps, av, gt, trk, map_path = load_log(A.data, log, A.source, A.trk)
    mfeat, has_cl, city, n_poly = map_features(ds, map_path)
    tab = gt if A.source == "gt" else trk
    use_mask = gt["in_sq"] if A.source == "gt" else np.ones(len(trk["ts"]), bool)
    vis_key = set(zip(gt["ts"][gt["npts"] >= 1].tolist(), gt["id"][gt["npts"] >= 1].tolist()))
    scenes, items, cnt = [], [], {"origins": 0, "origins_no_target": 0, "trk_at_origin": 0, "trk_matched": 0, "gt_visible_at_origin": 0, "gt_visible_in_square": 0}
    for s in range(0, len(sweeps), ORIGIN_EVERY):
        t0 = int(sweeps[s]); cnt["origins"] += 1
        tt, jit = target_sweep(sweeps, t0)
        if tt is None:
            cnt["origins_no_target"] += 1
            continue
        grid = step_grid(sweeps, t0)
        assert grid[-1] == t0
        g0 = (gt["ts"] == t0) & (gt["npts"] >= 1)
        cnt["gt_visible_at_origin"] += int(g0.sum()); cnt["gt_visible_in_square"] += int((g0 & gt["in_sq"]).sum())
        pairs = []  # (agent id in scene, gt index)
        if A.source == "gt":
            pairs = [(gt["id"][i], i) for i in np.nonzero(g0 & gt["in_sq"])[0]]
        else:
            r0 = np.nonzero(trk["ts"] == t0)[0]
            cnt["trk_at_origin"] += len(r0)
            for c in CLASSES3:
                rt = r0[trk["cat"][r0] == c]
                rg = np.nonzero(g0 & (gt["cat"] == c))[0]
                for i, j in hungarian(np.c_[trk["x"][rt], trk["y"][rt]], np.c_[gt["x"][rg], gt["y"][rg]]):
                    pairs.append((trk["id"][rt[i]], rg[j], int(trk["tid"][rt[i]])))
            cnt["trk_matched"] += len(pairs)
        if not pairs:
            continue
        df = scene_df(grid, av, tab, use_mask)
        af = ds.get_agent_features(df)
        valid_raw = np.zeros((af["num_nodes"], NH), bool)
        idmap = {aid: k for k, aid in enumerate(af["id"])}
        for aid, step in zip(df["track_id"].to_numpy(), df["timestep"].to_numpy()):
            valid_raw[idmap[aid], step] = True
        dd = {"scenario_id": "%s_%d_%s" % (log, t0, A.source), "city": city, "agent": af}
        dd.update(mfeat)  # map features (edge-type keys are tuples), shared by the log's scenes
        data = HeteroData(dd)
        scenes.append(data)
        for p in pairs:
            aid, gi = p[0], p[1]
            k = idmap[aid]
            items.append({"scene": len(scenes) - 1, "local": k, "sample_token": "%s_%d" % (log, t0), "log_id": log, "origin_ts": t0,
                          "instance_token": gt["id"][gi], "category": gt["cat"][gi], "target_ts": tt, "jitter_ms": jit,
                          "n_hist": int(valid_raw[k].sum()), "vec_valid_now": bool(valid_raw[k, NH - 2] and valid_raw[k, NH - 1]),
                          "vis_target": (tt, gt["id"][gi]) in vis_key, "num_pts_origin": int(gt["npts"][gi]),
                          "track_id": p[2] if len(p) > 2 else -1, "n_agents_scene": int(af["num_nodes"])})
    out = []
    i = 0
    B = A.batch
    while i < len(scenes):
        chunk = scenes[i:i + B]
        try:
            loc, sc, lg, hd, ps, ptr = forward(model, chunk, device)
        except torch.cuda.OutOfMemoryError:
            torch.cuda.empty_cache()
            if B == 1:
                raise
            B = max(1, B // 2)
            print("OOM at batch", len(chunk), "-> batch", B, flush=True)
            continue
        out.append((i, loc, sc, lg, hd, ps, ptr))
        i += len(chunk)
    rows = {k: [] for k in ("sample_token", "log_id", "origin_ts", "instance_token", "category", "target_ts", "jitter_ms", "n_hist",
                            "vec_valid_now", "vis_target", "num_pts_origin", "track_id", "n_agents_scene")}
    g_loc, g_b, g_lg, g_th, g_p0 = [], [], [], [], []
    for (i0, loc, sc, lg, hd, ps, ptr) in out:
        for it in items:
            if not (i0 <= it["scene"] < i0 + len(ptr) - 1):
                continue
            gidx = int(ptr[it["scene"] - i0]) + it["local"]
            g_loc.append(loc[gidx, :, FUT_IDX]); g_b.append(sc[gidx, :, FUT_IDX]); g_lg.append(lg[gidx])
            g_th.append(hd[gidx, NH - 1]); g_p0.append(ps[gidx, NH - 1, :2])
            for k in rows:
                rows[k].append(it[k])
    res = {k: np.asarray(v) for k, v in rows.items()}
    if len(g_loc):
        der = derive(np.stack(g_loc), np.stack(g_b), np.stack(g_lg), np.asarray(g_th), np.stack(g_p0))
        res.update(der)
        res["theta"] = np.asarray(g_th); res["p0"] = np.stack(g_p0)
    meta = dict(cnt, log=log, items=len(rows["sample_token"]), scenes=len(scenes), polygons=n_poly, map_has_centerline=has_cl,
                city=city, seconds=time.time() - t_log, final_batch=B)
    return res, meta


def merge(A):
    parts = sorted(glob.glob(os.path.join(A.out, "per_log", "%s_*.npz" % A.source)))
    keys = None
    acc = {}
    for p in parts:
        z = np.load(p, allow_pickle=False)
        if "sample_token" not in z.files or len(z["sample_token"]) == 0:
            continue
        keys = keys or z.files
        for k in keys:
            acc.setdefault(k, []).append(z[k])
    res = {k: np.concatenate(v) for k, v in acc.items()}
    for k, v in res.items():
        if v.dtype == object:
            res[k] = v.astype(str)
    key = np.char.add(np.char.add(res["sample_token"].astype(str), "|"), res["instance_token"].astype(str))
    assert len(np.unique(key)) == len(key), "duplicate item keys"
    np.savez_compressed(os.path.join(A.out, A.name), **res)
    metas = [json.load(open(m)) for m in sorted(glob.glob(os.path.join(A.out, "per_log", "%s_*.json" % A.source)))]
    tot = {k: sum(m[k] for m in metas) for k in ("origins", "origins_no_target", "trk_at_origin", "trk_matched", "gt_visible_at_origin", "gt_visible_in_square", "items", "scenes")}
    tot["logs"] = len(metas)
    tot["map_has_centerline_logs"] = sum(bool(m["map_has_centerline"]) for m in metas)
    tot["seconds"] = sum(m["seconds"] for m in metas)
    tot["finite_all"] = bool(res["finite"].all()); tot["pd_v1_all"] = bool(res["pd_v1"].all()); tot["pd_v2_all"] = bool(res["pd_v2"].all()); tot["pd_modes_all"] = bool(res["pd_modes"].all())
    tot["non_finite_rows"] = int((~res["finite"]).sum()); tot["non_pd_v2_rows"] = int((~res["pd_v2"]).sum())
    with open(os.path.join(A.out, A.name.replace(".npz", "_summary.json")), "w") as f:
        json.dump(tot, f, indent=1)
    print(json.dumps(tot), flush=True)
    print("MERGE DONE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qcnet")
    ap.add_argument("--ckpt")
    ap.add_argument("--data")
    ap.add_argument("--source", choices=["gt", "trk"], required=True)
    ap.add_argument("--trk")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=4)
    ap.add_argument("--logs", type=int, default=0)
    ap.add_argument("--bscheck", action="store_true")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--name", default="")
    A = ap.parse_args()
    if A.merge:
        return merge(A)
    sys.path.insert(0, A.qcnet)
    import torch
    torch.set_grad_enabled(False)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    os.makedirs(os.path.join(A.out, "per_log"), exist_ok=True)
    ds = make_dataset_helper(os.path.join(A.out, "_qcnet_scratch"))
    model, how = load_model(A.qcnet, A.ckpt, device)
    print("model loaded via", how, "device", device, flush=True)
    logs = sorted(os.listdir(A.data))
    if A.logs:
        logs = logs[: A.logs]
    if A.bscheck:  # batching must not change outputs (output against output)
        B0 = A.batch
        A.batch = 1
        r1, _ = run_log(logs[0], A, ds, model, device)
        A.batch = B0
        rB, _ = run_log(logs[0], A, ds, model, device)
        rec = {k: float(np.abs(r1[k] - rB[k]).max()) for k in ("loc", "scale", "pi", "v2_cov")}
        rec.update(log=logs[0], items=int(len(r1["sample_token"])), batch=B0)
        json.dump(rec, open(os.path.join(A.out, "bscheck_%s.json" % A.source), "w"), indent=1)
        print("BSCHECK", json.dumps(rec), flush=True)
        return
    t0 = time.time()
    for n, log in enumerate(logs):
        p = os.path.join(A.out, "per_log", "%s_%s.npz" % (A.source, log))
        if os.path.exists(p):
            continue
        res, meta = run_log(log, A, ds, model, device)
        np.savez_compressed(p + ".part.npz", **res)
        os.replace(p + ".part.npz", p)
        json.dump(meta, open(p.replace(".npz", ".json"), "w"), indent=1)
        print("%d/%d %s items=%d scenes=%d polys=%d cl=%s %.1fs (total %.0fs)" % (n + 1, len(logs), log, meta["items"], meta["scenes"], meta["polygons"], meta["map_has_centerline"], meta["seconds"], time.time() - t0), flush=True)
    print("INFER DONE", A.source, flush=True)


if __name__ == "__main__":
    main()
