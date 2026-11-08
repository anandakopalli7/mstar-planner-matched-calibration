"""qcnet_frame_test_v05 (QCNet arm, addendum A, 2 Nov 2026) = qcnet_frame_test_v04 run on qcnet_av2_infer_v03 (v04 imported v02,
whose pool transport failed). qcnet_frame_test_v04: frame tests UNDER RE-CENTRING (design addendum A2).

The whole v02 pipeline (tables -> re-centred scenes -> QCNet -> back to the city frame) is run on the original city-frame
tables and map of log 0, and on the same tables and map transformed in the city frame by
  (a) translation by (123.4, -56.7) m, (b) rotation by 0.7 rad about the city origin, (c) rotation by exactly +90 degrees.
Agents: x, y and velocities transformed, headings + phi; map: every (x, y) point of the log map JSON transformed (float64).
Expected: mu' = R mu + t, Sigma' = R Sigma R^T, pi' = pi, within float32 rounding at local magnitudes. Negative control: the
conversion with the wrong rotation sign (local = R(theta)^T (mu - p0), mapped back with R(-theta)) must miss (b) by > 0.5 m.
Output against output only; no ground truth after the origin is read.
Usage: python -I qcnet_frame_test_v04.py --qcnet <repo> --ckpt <ckpt> --data <val dir> --sweeps <json> --out <json> [--device cuda]
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def rot(phi):
    return np.array([[math.cos(phi), -math.sin(phi)], [math.sin(phi), math.cos(phi)]])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--qcnet", required=True)
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--data", required=True)
    ap.add_argument("--sweeps", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--device", default="cuda")
    a = ap.parse_args()
    sys.path.insert(0, a.qcnet)
    import torch
    import qcnet_av2_infer_v03 as Q2
    Q2.A = argparse.Namespace(data=a.data, sweeps=a.sweeps, source="gt", trk=None)
    Q = Q2.V1()
    device = torch.device(a.device)
    model, _ = Q.load_model(a.qcnet, a.ckpt, device)
    log = sorted(json.load(open(a.sweeps)))[0]
    sweeps, av, gt, trk, map_path = Q2.load_log(log)
    map_json = json.load(open(map_path))
    origins = [5, 10, 15, 20]

    def run(tables, mj):
        _, scenes, items, _ = Q2.build_log(log, tables=tables, map_override=mj, origins=origins)
        res, _ = Q2.infer_log(model, device, scenes, items, 4)
        return res

    def transform(R, t, phi):
        def tf_tab(tb):
            d = dict(tb)
            xy = np.stack([tb["x"], tb["y"]], 1) @ R.T + t
            d["x"], d["y"] = xy[:, 0], xy[:, 1]
            v = np.stack([tb["vx"], tb["vy"]], 1) @ R.T
            d["vx"], d["vy"] = v[:, 0], v[:, 1]
            h = tb["yaw"] + phi
            d["yaw"] = np.arctan2(np.sin(h), np.cos(h))
            return d

        def tf_map(obj):
            if isinstance(obj, dict):
                if "x" in obj and "y" in obj and isinstance(obj["x"], (int, float)):
                    q = dict(obj)
                    p = R @ np.array([float(obj["x"]), float(obj["y"])]) + t
                    q["x"], q["y"] = float(p[0]), float(p[1])
                    return q
                return {k: tf_map(v) for k, v in obj.items()}
            if isinstance(obj, list):
                return [tf_map(v) for v in obj]
            return obj
        return (sweeps, tf_tab(av), tf_tab(gt), None, map_path), tf_map(map_json)

    base = run((sweeps, av, gt, None, map_path), map_json)
    res = {"log": log, "origins": origins, "items": int(len(base["pi"])), "cases": {}}
    cases = {"translate": (np.eye(2), np.array([123.4, -56.7]), 0.0), "rotate_0.7rad": (rot(0.7), np.zeros(2), 0.7),
             "rotate_90deg": (np.array([[0.0, -1.0], [1.0, 0.0]]), np.zeros(2), math.pi / 2)}
    for name, (R, t, phi) in cases.items():
        tables, mj = transform(R, t, phi)
        o = run(tables, mj)
        mu_p = np.einsum("ij,nkj->nki", R, base["loc"]) + t
        cov_p = np.einsum("ij,nkjl,ml->nkim", R, base["cov_modes"], R)
        dmu = np.abs(o["loc"] - mu_p).max(axis=(1, 2))
        c = {"max_abs_mu_diff_m": float(dmu.max()), "median_abs_mu_diff_m": float(np.median(dmu)),
             "max_abs_cov_diff_m2": float(np.abs(o["cov_modes"] - cov_p).max()), "max_abs_pi_diff": float(np.abs(o["pi"] - base["pi"]).max()),
             "max_abs_v2_mu_diff_m": float(np.abs(o["v2_mu"] - (base["v2_mu"] @ R.T + t)).max())}
        if phi != 0.0:
            def wrong(r):
                c_, s_ = np.cos(r["theta"]), np.sin(r["theta"])
                Rt = np.stack([np.stack([c_, -s_], -1), np.stack([s_, c_], -1)], -2)
                local = np.einsum("nji,nkj->nki", Rt, r["loc"] - r["p0"][:, None, :])  # R(theta)^T (mu - p0)
                Rw = np.stack([np.stack([c_, s_], -1), np.stack([-s_, c_], -1)], -2)  # R(-theta)
                return np.einsum("nij,nkj->nki", Rw, local) + r["p0"][:, None, :]
            c["negative_control_wrong_sign_max_abs_mu_diff_m"] = float(np.abs(wrong(o) - (np.einsum("ij,nkj->nki", R, wrong(base)) + t)).max())
        res["cases"][name] = c
    r = res["cases"]
    res["passed"] = bool(r["translate"]["max_abs_mu_diff_m"] < 0.01 and r["rotate_90deg"]["max_abs_mu_diff_m"] < 0.01
                         and r["rotate_0.7rad"]["negative_control_wrong_sign_max_abs_mu_diff_m"] > 0.5)
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res), flush=True)
    print("FRAME TEST DONE", flush=True)


if __name__ == "__main__":
    main()
