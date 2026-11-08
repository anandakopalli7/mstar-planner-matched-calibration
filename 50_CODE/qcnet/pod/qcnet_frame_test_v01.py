"""qcnet_frame_test_v01 (QCNet arm, 2 Nov 2026): frame-convention unit test of the QCNet output conversion (P7 C.3, "identity case").

QCNet is built to be invariant to rotations and translations of the whole scene. If the conversion world = R(theta) local + p0
and Sigma = R(theta) diag(2 b^2) R(theta)^T is right, then rotating and translating the scene's agents AND map by (phi, t)
gives world-frame outputs mu' = R(phi) mu + t and Sigma' = R(phi) Sigma R(phi)^T and identical mixture weights. A sign error in
theta would break this. Output against output only: no ground truth after the origin is read.
Usage: python -I qcnet_frame_test_v01.py --qcnet <repo> --ckpt <ckpt> --data <val dir> --out <json> [--origins 4] [--device cpu]
"""
import argparse
import json
import os
import sys

import numpy as np


def rot(phi):
    return np.array([[np.cos(phi), -np.sin(phi)], [np.sin(phi), np.cos(phi)]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qcnet", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--origins", type=int, default=4)
    ap.add_argument("--device", default="cpu")
    ap.add_argument("--phi", type=float, default=0.7)
    a = ap.parse_args()
    sys.path.insert(0, a.qcnet)
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import torch
    from torch_geometric.data import HeteroData
    import qcnet_av2_infer_v01 as Q
    device = torch.device(a.device)
    ds = Q.make_dataset_helper("/tmp/qcnet_frame_test_scratch")
    model, _ = Q.load_model(a.qcnet, a.ckpt, device)
    log = sorted(os.listdir(a.data))[0]
    sweeps, av, gt, _, map_path = Q.load_log(a.data, log, "gt", None)
    mfeat, _, city, _ = Q.map_features(ds, map_path)
    R, t = rot(a.phi), np.array([123.4, -56.7])

    def map_moved():
        m = {k: (dict(v) if isinstance(v, dict) else v) for k, v in mfeat.items()}
        for node in ("map_polygon", "map_point"):
            p = m[node]["position"].clone()
            xy = p[:, :2].double().numpy() @ R.T + t
            p[:, :2] = torch.from_numpy(xy).float()
            m[node]["position"] = p
            m[node]["orientation"] = torch.atan2(torch.sin(m[node]["orientation"] + a.phi), torch.cos(m[node]["orientation"] + a.phi))
        return m

    mfeat2 = map_moved()
    res = {"log": log, "phi": a.phi, "t": t.tolist(), "origins": [], "max_abs_mu_diff_m": 0.0, "max_abs_cov_diff_m2": 0.0, "max_abs_pi_diff": 0.0}
    n_done = 0
    for s in range(5, len(sweeps), 5):
        if n_done >= a.origins:
            break
        t0 = int(sweeps[s])
        if Q.target_sweep(sweeps, t0)[0] is None:
            continue
        grid = Q.step_grid(sweeps, t0)
        df = Q.scene_df(grid, av, gt, gt["in_sq"])
        df2 = df.copy()
        xy = df[["position_x", "position_y"]].to_numpy() @ R.T + t
        df2["position_x"], df2["position_y"] = xy[:, 0], xy[:, 1]
        v = df[["velocity_x", "velocity_y"]].to_numpy() @ R.T
        df2["velocity_x"], df2["velocity_y"] = v[:, 0], v[:, 1]
        df2["heading"] = np.arctan2(np.sin(df["heading"] + a.phi), np.cos(df["heading"] + a.phi))
        outs = []
        for d, mf in ((df, mfeat), (df2, mfeat2)):
            af = ds.get_agent_features(d)
            dd = {"scenario_id": "frametest", "city": city, "agent": af}
            dd.update(mf)
            loc, sc, lg, hd, ps, ptr = Q.forward(model, [HeteroData(dd)], device)
            items = [k for k, aid in enumerate(af["id"]) if aid != "AV" and bool(af["valid_mask"][k, Q.NH - 1])]
            der = Q.derive(loc[items, :, Q.FUT_IDX], sc[items, :, Q.FUT_IDX], lg[items], hd[items, Q.NH - 1], ps[items, Q.NH - 1, :2])
            bad = Q.derive(loc[items, :, Q.FUT_IDX], sc[items, :, Q.FUT_IDX], lg[items], -hd[items, Q.NH - 1], ps[items, Q.NH - 1, :2])
            outs.append((der, bad))
        (o1, b1), (o2, b2) = outs
        res.setdefault("negative_control_wrong_sign_max_abs_mu_diff_m", 0.0)
        res["negative_control_wrong_sign_max_abs_mu_diff_m"] = max(res["negative_control_wrong_sign_max_abs_mu_diff_m"],
                                                                   float(np.abs(b2["loc"] - (np.einsum("ij,nkj->nki", R, b1["loc"]) + t)).max()))
        mu_pred = np.einsum("ij,nkj->nki", R, o1["loc"]) + t
        cov_pred = np.einsum("ij,nkjl,ml->nkim", R, o1["cov_modes"], R)
        dm = float(np.abs(o2["loc"] - mu_pred).max()); dc = float(np.abs(o2["cov_modes"] - cov_pred).max()); dp = float(np.abs(o2["pi"] - o1["pi"]).max())
        res["origins"].append({"t0": t0, "items": int(len(o1["pi"])), "max_abs_mu_diff_m": dm, "max_abs_cov_diff_m2": dc, "max_abs_pi_diff": dp})
        res["max_abs_mu_diff_m"] = max(res["max_abs_mu_diff_m"], dm); res["max_abs_cov_diff_m2"] = max(res["max_abs_cov_diff_m2"], dc); res["max_abs_pi_diff"] = max(res["max_abs_pi_diff"], dp)
        n_done += 1
    # negative control: the same comparison with the wrong rotation sign R(-theta) must fail, so the test has power
    res["passed"] = bool(res["max_abs_mu_diff_m"] < 0.05 and res["max_abs_pi_diff"] < 1e-2 and res["negative_control_wrong_sign_max_abs_mu_diff_m"] > 0.5)
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res), flush=True)
    print("FRAME TEST DONE", flush=True)


if __name__ == "__main__":
    main()
