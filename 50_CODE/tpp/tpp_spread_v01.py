#!/usr/bin/env python3
"""TPP arm spread of the predictor's own outputs (Claude line, v01, 2 Nov 2026): seed against seed and platform against
platform, on the same records. Self-consistency only: no ground truth is read, no outcome is computed.
For each pair of runs (rows aligned by scene, k, h, pair; status ok in both; step 4 = 2.0 s unless --all-steps):
  * the statistics of tpp_xplat_compare_v01 (max abs of V1 / V2 mean and covariance differences, max relative
    covariance difference = max |dS| / max |S_ref| per row);
  * the distribution of the per-row relative V2 covariance difference (quantiles, share > 1 %, > 5 %);
  * where the large ones sit: the reference V2's smallest eigenvalue, condition number and trace, the largest weight,
    the node type, the history length, for rows above 5 % against all rows (medians), and the 10 largest rows;
  * the same for the V2 projected standard deviation along the item normal a* (sqrt(a*' S a* + 0.1^2)), which is what
    the audit consumes: the per-item relative difference of sd.
Usage: python -I tpp_spread_v01.py --keys <k> --pair NAME RUN_A RUN_B [--pair ...] --out <json> [--keys-b <k2> for runs of
       another platform whose keys file differs]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_common_v01 as C  # noqa: E402


def align(ka, za, kb, zb):
    def key(kz, z):
        n = kz["scene_names"]
        sel = z["rec_index"]
        return {(str(n[s]), int(k), int(h), int(p)): i for i, (s, k, h, p) in
                enumerate(zip(kz["rec_s"][sel], kz["rec_k"][sel], kz["rec_h"][sel], kz["rec_pair"][sel]))}
    ia, ib = key(ka, za), key(kb, zb)
    com = sorted(set(ia) & set(ib))
    return np.array([ia[c] for c in com], int), np.array([ib[c] for c in com], int)


def q(x):
    return {p: float(np.quantile(x, p / 100.0)) for p in (50, 90, 99)} if len(x) else {}


def spread(ka, za, kb, zb, all_steps=False):
    a, b = align(ka, za, kb, zb)
    ok = (za["status"][a] == C.ST_OK) & (zb["status"][b] == C.ST_OK)
    if not all_steps:
        ok &= za["step"][a] == 4
    a, b = a[ok], b[ok]
    SA, SB = za["v2_cov"][a], zb["v2_cov"][b]
    rel = np.max(np.abs(SA - SB), -1) / np.maximum(np.max(np.abs(SA), -1), 1e-12)
    absd = np.max(np.abs(SA - SB), -1)
    lam_min = C.min_eig_2x2(SA)
    tr = SA[:, 0] + SA[:, 2]
    lam_max = tr - lam_min
    cond = lam_max / np.maximum(lam_min, 1e-12)
    rec = za["rec_index"][a]
    # sd along the item normals (relied axis of each record): a* from the keys
    yaw, rel_ax = ka["rec_yaw"][rec], ka["rec_rel"][rec]
    sg = np.where(rel_ax == 0, ka["rec_sign_long"][rec], ka["rec_sign_lat"][rec])
    ax = np.where(rel_ax[:, None] == 0, np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1)) * sg[:, None]

    def sd(S):
        return np.sqrt(ax[:, 0] ** 2 * S[:, 0] + 2 * ax[:, 0] * ax[:, 1] * S[:, 1] + ax[:, 1] ** 2 * S[:, 2] + 0.01)
    sd_rel = np.abs(sd(SA) - sd(SB)) / sd(SA)
    big = rel > 0.05
    typ = ka["rec_tpp_type"][rec]
    feats = {"v2_min_eig_m2": lam_min, "v2_cond": cond, "v2_trace_m2": tr, "w_max": za["w_max"][a], "hist": za["hist"][a].astype(float)}
    out = {"rows": int(len(a)), "v2_mean_max_abs_m": float(np.max(np.abs(za["v2_mu"][a] - zb["v2_mu"][b]))) if len(a) else 0.0,
           "v2_cov_max_abs_m2": float(absd.max()) if len(a) else 0.0, "v2_cov_max_rel": float(rel.max()) if len(a) else 0.0,
           "v1_mean_max_abs_m": float(np.max(np.abs(za["v1_mu"][a] - zb["v1_mu"][b]))) if len(a) else 0.0,
           "v1_cov_max_rel": float(np.max(np.max(np.abs(za["v1_cov"][a] - zb["v1_cov"][b]), -1)
                                          / np.maximum(np.max(np.abs(za["v1_cov"][a]), -1), 1e-12))) if len(a) else 0.0,
           "v2_cov_rel_quantiles": q(rel), "share_rel_gt_1pct": float(np.mean(rel > 0.01)), "share_rel_gt_5pct": float(np.mean(big)),
           "sd_along_normal_rel": {"max": float(sd_rel.max()) if len(a) else 0.0, **q(sd_rel), "share_gt_1pct": float(np.mean(sd_rel > 0.01))},
           "rows_rel_gt_5pct_by_type": {C.TPP_TYPE_NAMES[t]: int(np.sum(big & (typ == t))) for t in (0, 1)},
           "rows_by_type": {C.TPP_TYPE_NAMES[t]: int(np.sum(typ == t)) for t in (0, 1)},
           "median_features_rel_gt_5pct": {k: float(np.median(v[big])) if big.any() else None for k, v in feats.items()},
           "median_features_all": {k: float(np.median(v)) for k, v in feats.items()},
           "top10": [{"rel": float(rel[i]), "abs_m2": float(absd[i]), "min_eig_m2": float(lam_min[i]), "cond": float(cond[i]),
                      "trace_m2": float(tr[i]), "w_max": float(za["w_max"][a][i]), "type": C.TPP_TYPE_NAMES[int(typ[i])],
                      "hist": int(za["hist"][a][i]), "sd_rel": float(sd_rel[i])} for i in np.argsort(-rel)[:10]]}
    # correlation of the relative difference with conditioning (rank based)
    if len(a) > 10:
        r1, r2 = np.argsort(np.argsort(rel)), np.argsort(np.argsort(cond))
        out["spearman_rel_vs_cond"] = float(np.corrcoef(r1, r2)[0, 1])
        r3 = np.argsort(np.argsort(tr))
        out["spearman_rel_vs_trace"] = float(np.corrcoef(r1, r3)[0, 1])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pair", nargs=5, action="append", metavar=("NAME", "KEYS_A", "RUN_A", "KEYS_B", "RUN_B"), required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {}
    for name, k1, r1, k2, r2 in a.pair:
        ka, kb = np.load(k1, allow_pickle=False), np.load(k2, allow_pickle=False)
        za, zb = np.load(r1, allow_pickle=False), np.load(r2, allow_pickle=False)
        res[name] = spread(ka, za, kb, zb)
    out = {"note": "predictor self-consistency only; no ground truth read", "pairs": res,
           "script_sha256": C.sha256_path(os.path.abspath(__file__))}
    json.dump(out, open(a.out, "w"), indent=1)
    for n, r in res.items():
        print(n, json.dumps({k: r[k] for k in ("rows", "v2_mean_max_abs_m", "v2_cov_max_abs_m2", "v2_cov_max_rel", "v1_cov_max_rel",
                                                "share_rel_gt_1pct", "share_rel_gt_5pct")}), "sd_rel_max", round(r["sd_along_normal_rel"]["max"], 4),
              "sd_rel_p99", round(r["sd_along_normal_rel"].get(99, 0), 4))
    print("TPP SPREAD V01 DONE")


if __name__ == "__main__":
    main()
