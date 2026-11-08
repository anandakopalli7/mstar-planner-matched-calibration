"""qcnet_frame_test_v03 (QCNet arm, 2 Nov 2026): exact frame-convention unit test of the QCNet output conversion.

Why v03. v01 (float32) and v02 (float64 model) rotated the scene by 0.7 rad and translated it by (123.4, -56.7) m; outputs moved
by up to 0.16 m (median ~0.03 m) and mixture weights by up to 0.62, and a repeat of the same scene gave identical outputs.
A pure translation did the same. Cause: QCNet's agent features are built in float32 from city coordinates (~6,700 m, grid
0.5 mm), and the angle between an agent's heading and its near-zero motion vector (parked or slow objects) is an input, so
re-rounding under an arbitrary shift changes it. v02's float64 model did not help, because the features are rounded to float32
in QCNet's own get_agent_features before the model sees them.

v03 therefore uses transformations that float arithmetic represents EXACTLY, so that QCNet's inputs are transformed exactly and
any output mismatch can only come from the conversion:
  (A) rotation by +90 degrees about the origin: (x, y) -> (-y, x) for agents, velocities and the map (swap and negation);
      headings and orientations + pi/2 (rounding ~1e-7 rad)
  (B) translation by a power-of-two shift that keeps every coordinate in its float32 binade (so float32 values shift exactly)
Pass: mu' = R mu + t within 2 cm and pi within 1e-3 for both; negative control: the conversion with the wrong sign R(-theta)
fails (A) by more than 0.5 m. Output against output only; no ground truth after the origin is read.
Usage: python -I qcnet_frame_test_v03.py --qcnet <repo> --ckpt <ckpt> --data <val dir> --out <json> [--origins 4]
"""
import argparse
import json
import math
import os
import sys

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qcnet", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--origins", type=int, default=4)
    a = ap.parse_args()
    sys.path.insert(0, a.qcnet)
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    import torch
    from torch_geometric.data import HeteroData
    import qcnet_av2_infer_v01 as Q
    dev = torch.device("cpu")
    ds = Q.make_dataset_helper("/tmp/qcnet_frame_test_v03_scratch")
    model, _ = Q.load_model(a.qcnet, a.ckpt, dev)
    log = sorted(os.listdir(a.data))[0]
    sweeps, av, gt, _, map_path = Q.load_log(a.data, log, "gt", None)
    mfeat, _, city, _ = Q.map_features(ds, map_path)

    def binade_shift(vals):
        """largest power-of-two shift s (<= 512) such that every |v| and |v + s| share a float32 binade."""
        v = np.asarray(vals, np.float64)
        for s in (512.0, 256.0, 128.0, 64.0, 32.0, 16.0, 8.0, 4.0, 2.0, 1.0):
            if np.all(v > 0) and np.all(np.floor(np.log2(v)) == np.floor(np.log2(v + s))):
                return s
            if np.all(v < 0) and np.all(np.floor(np.log2(-v)) == np.floor(np.log2(-(v + s * -1)))):
                return -s
        return None

    def transform(df, kind, t=None):
        d2 = df.copy()
        m = {k: (dict(v) if isinstance(v, dict) else v) for k, v in mfeat.items()}
        if kind == "rot90":
            d2["position_x"], d2["position_y"] = -df["position_y"].to_numpy(), df["position_x"].to_numpy()
            d2["velocity_x"], d2["velocity_y"] = -df["velocity_y"].to_numpy(), df["velocity_x"].to_numpy()
            h = df["heading"].to_numpy() + math.pi / 2
            d2["heading"] = np.arctan2(np.sin(h), np.cos(h))
            for node in ("map_polygon", "map_point"):
                p = m[node]["position"].clone()
                p[:, 0], p[:, 1] = -m[node]["position"][:, 1], m[node]["position"][:, 0]
                m[node]["position"] = p
                o = m[node]["orientation"].double() + math.pi / 2
                m[node]["orientation"] = torch.atan2(torch.sin(o), torch.cos(o)).float()
        else:
            d2["position_x"] = df["position_x"].to_numpy() + t[0]
            d2["position_y"] = df["position_y"].to_numpy() + t[1]
            for node in ("map_polygon", "map_point"):
                p = m[node]["position"].clone()
                p[:, 0] += float(t[0]); p[:, 1] += float(t[1])
                m[node]["position"] = p
        return d2, m

    def run(d, m):
        af = ds.get_agent_features(d)
        dd = {"scenario_id": "frametest", "city": city, "agent": af}
        dd.update(m)
        loc, sc, lg, hd, ps, ptr = Q.forward(model, [HeteroData(dd)], dev)
        it = [k for k, aid in enumerate(af["id"]) if aid != "AV" and bool(af["valid_mask"][k, Q.NH - 1])]
        args = (loc[it, :, Q.FUT_IDX], sc[it, :, Q.FUT_IDX], lg[it], hd[it, Q.NH - 1], ps[it, Q.NH - 1, :2])
        good = Q.derive(*args)
        bad = Q.derive(args[0], args[1], args[2], -args[3], args[4])
        return good, bad

    res = {"log": log, "origins": [], "rot90": {"max_abs_mu_diff_m": 0.0, "max_abs_cov_diff_m2": 0.0, "max_abs_pi_diff": 0.0, "negative_control_max_abs_mu_diff_m": 0.0},
           "translate": {"max_abs_mu_diff_m": 0.0, "max_abs_cov_diff_m2": 0.0, "max_abs_pi_diff": 0.0}}
    n_done = 0
    for s in range(5, len(sweeps), 5):
        if n_done >= a.origins:
            break
        t0 = int(sweeps[s])
        if Q.target_sweep(sweeps, t0)[0] is None:
            continue
        df = Q.scene_df(Q.step_grid(sweeps, t0), av, gt, gt["in_sq"])
        g0, b0 = run(df, mfeat)
        rec = {"t0": t0, "items": int(len(g0["pi"]))}
        # (A) rotation by +90 degrees
        g1, b1 = run(*transform(df, "rot90"))
        R = np.array([[0.0, -1.0], [1.0, 0.0]])
        mu_p = np.einsum("ij,nkj->nki", R, g0["loc"])
        cov_p = np.einsum("ij,nkjl,ml->nkim", R, g0["cov_modes"], R)
        r = res["rot90"]
        r["max_abs_mu_diff_m"] = max(r["max_abs_mu_diff_m"], float(np.abs(g1["loc"] - mu_p).max()))
        r["max_abs_cov_diff_m2"] = max(r["max_abs_cov_diff_m2"], float(np.abs(g1["cov_modes"] - cov_p).max()))
        r["max_abs_pi_diff"] = max(r["max_abs_pi_diff"], float(np.abs(g1["pi"] - g0["pi"]).max()))
        r["negative_control_max_abs_mu_diff_m"] = max(r["negative_control_max_abs_mu_diff_m"], float(np.abs(b1["loc"] - np.einsum("ij,nkj->nki", R, b0["loc"])).max()))
        # (B) exact translation
        xs = np.r_[df["position_x"].to_numpy(), mfeat["map_polygon"]["position"][:, 0].double().numpy(), mfeat["map_point"]["position"][:, 0].double().numpy()]
        ys = np.r_[df["position_y"].to_numpy(), mfeat["map_polygon"]["position"][:, 1].double().numpy(), mfeat["map_point"]["position"][:, 1].double().numpy()]
        t = (binade_shift(xs), binade_shift(ys))
        rec["translation"] = t
        if t[0] is not None and t[1] is not None:
            g2, _ = run(*transform(df, "translate", t))
            q = res["translate"]
            q["max_abs_mu_diff_m"] = max(q["max_abs_mu_diff_m"], float(np.abs(g2["loc"] - (g0["loc"] + np.array(t))).max()))
            q["max_abs_cov_diff_m2"] = max(q["max_abs_cov_diff_m2"], float(np.abs(g2["cov_modes"] - g0["cov_modes"]).max()))
            q["max_abs_pi_diff"] = max(q["max_abs_pi_diff"], float(np.abs(g2["pi"] - g0["pi"]).max()))
        res["origins"].append(rec)
        n_done += 1
    r, q = res["rot90"], res["translate"]
    res["passed"] = bool(r["max_abs_mu_diff_m"] < 0.02 and r["max_abs_pi_diff"] < 1e-3 and q["max_abs_mu_diff_m"] < 0.02 and q["max_abs_pi_diff"] < 1e-3
                         and r["negative_control_max_abs_mu_diff_m"] > 0.5 and all(o["translation"][0] is not None for o in res["origins"]))
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res), flush=True)
    print("FRAME TEST DONE", flush=True)


if __name__ == "__main__":
    main()
