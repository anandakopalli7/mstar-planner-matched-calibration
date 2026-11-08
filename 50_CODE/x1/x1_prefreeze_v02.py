#!/usr/bin/env python3
"""X1 pre-freeze steps v02 (Claude line, 30 Oct 2026). No ground-truth residual is computed or written here.
  selftest : known-answer synthetic tests of x1_lib_v02 (code checks; never evidence)
  sizes    : per-cell item and scene counts, per-scene counts, median exported SD, orientation null E0/m0 (sigma_a 0.10, 0.20)
  fwer     : family-wise false-FAILS rate of the primary sup-t rule at the observed cell sizes (R03 M3)
  oc       : Q4 operating characteristics at the observed per-scene counts (R03 m17)
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_lib_v02 as L  # noqa: E402


def selftest():
    rng = np.random.default_rng(7)
    res = {}
    # C1 artefact reproduced without the separating filter: ego inside the slab (sep 0, hsum 0) -> 0.10
    n = 50000
    one = lambda sep, hsum, var=0.25: {"all": {k: np.full(n, v) for k, v in dict(a0=1.0, a1=0.0, sep=sep, hsum=hsum, var=var, sa=0.0,
                                                                          sxx=var, sxy=0.0, syy=var).items()}}
    e0, _ = L.orientation_null({"c": one(0.0, 0.0)}, rng, n_draw=4)["c"]
    res["C1_artefact_E0"], res["C1_artefact_ok"] = e0, abs(e0 - 0.10) < 0.004
    # separating filter with a large separation -> 0.05
    e1, m1 = L.orientation_null({"c": one(10.0, 2.0)}, rng, n_draw=4)["c"]
    res["C1_separating_E0"], res["C1_separating_ok"] = e1, abs(e1 - 0.05) < 0.003 and abs(m1 - L.Z95) < 0.03
    # |mu| < 1.645 SD with the filter: compare with brute force
    sep, hsum, sd = 0.5, 0.3, 0.5
    e2, _ = L.orientation_null({"c": one(sep, hsum)}, rng, n_draw=8)["c"]
    x = rng.normal(0, sd, 2_000_000)
    sp = sep - x
    k = np.abs(sp) > hsum
    bf = np.mean((np.where(sp >= 0, 1, -1) * (-x) / sd)[k] > L.Z95)
    res["C1_small_mu_E0"], res["C1_small_mu_bruteforce"] = e2, float(bf)
    res["C1_small_mu_ok"] = abs(e2 - bf) < 0.006
    # inflation
    V = rng.uniform(0.05, 1.0, 200000)
    D = rng.normal(0, np.sqrt(2.5 * V))
    s_hat, cap = L.inflation_needed(D, V, np.zeros_like(V))
    res["infl_s"], res["infl_ok"] = s_hat, abs(s_hat / 2.5 - 1) < 0.03 and not cap
    # CRC held-out scene loss <= delta on average
    held = []
    for _ in range(200):
        S = 80
        eff = rng.normal(0, 0.4, S)
        s = np.repeat(np.arange(S), rng.integers(5, 40, S))
        U = eff[s] + rng.normal(0, 1, len(s))
        perm = rng.permutation(S)
        mc = np.isin(s, perm[:40])
        c = L.crc_threshold(U[mc], s[mc])
        st, ut = s[~mc], np.unique(s[~mc])
        held.append(np.mean([np.mean(U[~mc][st == j] > c) for j in ut]))
    res["crc_heldout"], res["crc_ok"] = float(np.mean(held)), float(np.mean(held)) <= 0.055
    # orientation and separation geometry: object 10 m ahead, ego centre at origin heading +x
    row = {"yaw": 0.0, "eyaw": 0.0, "cx": 0.0, "cy": 0.0, "mx": 10.0, "my": 0.0, "l": 4.0, "w": 2.0}
    cand = {name: (a, sep, hsum) for name, a, sep, hsum in L.axis_candidates(row)}
    res["geom_long_sep"], res["geom_long_hsum"] = cand["long"][1], cand["long"][2]
    res["geom_ok"] = abs(cand["long"][1] + 10.0) < 1e-12 and abs(cand["long"][2] - (2.0 + L.EGO_L / 2 + L.BUFFER)) < 1e-12 \
        and abs(cand["lat"][1]) < 1e-12
    # in-path with the ego-centre offset
    from shapely.prepared import prep
    cg = L.ego_corridor(0, 0, 0, 10.0, 0.0)
    pc = prep(cg)
    res["inpath_ok"] = L.object_in_path(pc, 50, 1.39, 0, 20, 0, 0, 0, 0, 1.8, 4.5) and not L.object_in_path(pc, 50, 1.39, 0, 20, 30, 0, 0, 0, 1.8, 4.5)
    # simultaneous band coverage, 1000 replications, B = 2000
    cover = 0
    for _ in range(1000):
        src = rng.normal(0, 1, (150, 18))
        est = src.mean(0)
        W = L.boot_weights(150, 2000, rng)
        lo, hi, _, _ = L.sup_t_band(est, (W @ src) / 150)
        cover += int(np.all((lo <= 0) & (hi >= 0)))
    res["supt_coverage_1000"] = cover / 1000
    res["supt_ok"] = 0.936 <= cover / 1000 <= 0.964
    res["ALL_OK"] = all(v for k, v in res.items() if k.endswith("_ok"))
    return res


def sizes(export, gt, meta, horizon=None):
    recs = [r for e in export for r in L.load_export(e)]
    samples, gtb, racks = L.load_gt(gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    rows, st = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    rng = np.random.default_rng(L.SEED)
    fams = {"t0": rows}
    if horizon:
        hr, hst = L.build_horizon_rows(rows, L.load_horizon(horizon), samples, gtb, racks)
        fams["h2s"] = hr
    out = {"pairing_stats_counts_only": {k: v for k, v in st.items() if k in (
        "records_k_ge_1", "frame0_records", "inpath_records", "paired_inpath", "unpaired", "censored", "track_in_rack", "id_switches")},
           "Q1_paired_share_of_inpath": st.get("paired_inpath", 0) / max(st.get("inpath_records", 1), 1), "families": {}}
    for fam, frows in fams.items():
      out["families"][fam] = {"cells": {}}
      for sa in (0.10, 0.20):
        cells, scenes, logs = L.cell_items(frows, sigma_a=sa)
        null = L.orientation_null(cells, rng)
        for c in L.CELLS:
            d = cells[c]
            key = "|".join(c)
            entry = out["families"][fam]["cells"].setdefault(key, {})
            if sa == 0.10:
                cnt = np.bincount(d["s"], minlength=len(scenes)) if d["n"] else np.zeros(len(scenes), int)
                entry.update({"items": d["n"], "scenes": d["n_scenes"], "per_scene_counts": cnt.tolist(),
                              "median_exported_sd_m": float(np.median(np.sqrt(d["V"] + d["SA"] ** 2))) if d["n"] else None,
                              "eligible": d["n_scenes"] >= L.MIN_SCENES})
            entry["E0_sigma_%.2f" % sa], entry["m0_sigma_%.2f" % sa] = null[c]
    out["n_scenes"], out["n_logs"] = len(scenes), len(logs)
    out["inputs"] = {"export_sha256": [L.sha256_path(e) for e in export], "gt_sha256": L.sha256_path(gt)}
    return out


def fwer(sz, reps=500, B=2000, tau=0.5, logit=False, level=0.975, alpha=0.025):
    rng = np.random.default_rng(L.SEED + 1)
    cells = [c for c, v in sz["cells"].items() if v["eligible"]]
    if not cells:
        return {"eligible_cells": 0, "ok": True, "note": "no eligible cell"}
    counts = np.array([sz["cells"][c]["per_scene_counts"] for c in cells], dtype=float).T  # (S, G)
    S, G = counts.shape
    a0 = brentq(lambda a_: np.mean(expit(a_ + rng.normal(0, tau, 200000))) - 0.05, -10, 0)
    anyfail = 0
    for _ in range(reps):
        b = math.sqrt(tau ** 2 / 2) * (rng.normal(0, 1, (S, 1)) + rng.normal(0, 1, (S, G)))
        exc = rng.binomial(counts.astype(int), expit(a0 + b)).astype(float)
        est = exc.sum(0) / np.maximum(counts.sum(0), 1)
        W = L.boot_weights(S, B, rng)
        boot = (W @ exc) / np.maximum(W @ counts, 1e-12)
        lo, hi, _, zero = L.sup_t_band(est, boot, logit=logit, level=level)
        v = L.verdicts(est, lo, hi, zero, np.full(G, L.DELTA))
        anyfail += int("FAILS" in v)
    rate = anyfail / reps
    mc_se = math.sqrt(alpha * (1 - alpha) / reps)
    return {"eligible_cells": G, "reps": reps, "B": B, "tau_logit": tau, "logit_band": logit, "level": level, "P_any_FAILS": rate,
            "limit": alpha + 2 * mc_se, "ok": rate <= alpha + 2 * mc_se}


def oc_q4(sz, reps=200, B=200, icc=0.1):
    rng = np.random.default_rng(L.SEED + 2)
    cells = [c for c, v in sz["cells"].items() if v["eligible"]]
    if len(cells) < 2:
        return {"note": "fewer than 2 eligible cells", "targets_met": False}
    sd_med = float(np.median([sz["cells"][c]["median_exported_sd_m"] for c in cells]))
    cnts = [np.array(sz["cells"][c]["per_scene_counts"]) for c in cells]
    S = len(cnts[0])
    n_star = min(sz["cells"][c]["scenes"] for c in cells)
    out = {"eligible_cells": len(cells), "sd_med_m": sd_med, "n_star": n_star, "reps": reps, "B": B, "icc": icc}
    for label, spread_m in (("H0_true", 0.0), ("H_2h0", 2 * L.H0)):
        shifts = np.linspace(-spread_m / sd_med / 2, spread_m / sd_med / 2, len(cells))
        vs = []
        for _ in range(reps):
            b = rng.normal(0, math.sqrt(icc), S)
            cu, cs = [], []
            for cnt, sh in zip(cnts, shifts):
                s = np.repeat(np.arange(S), cnt)
                cu.append(b[s] + rng.normal(0, math.sqrt(1 - icc), len(s)) + sh)
                cs.append(s)
            vs.append(q4(cu, cs, S, sd_med, n_star, rng, B=B, reps_point=10, reps_boot=3)["verdict"])
        out[label] = {v: vs.count(v) / reps for v in ("MATERIAL", "IMMATERIAL", "INCONCLUSIVE")}
    out["false_material_rate"] = out["H0_true"]["MATERIAL"]
    out["false_immaterial_rate"] = out["H_2h0"]["IMMATERIAL"]
    out["targets_met"] = out["false_material_rate"] <= 0.10 and out["false_immaterial_rate"] <= 0.10
    return out


def q95_sub(U, s, n_star, rng, reps):
    sc = np.unique(s)
    if len(sc) <= n_star:
        return float(np.quantile(U, 0.95))
    return float(np.mean([np.quantile(U[np.isin(s, rng.choice(sc, n_star, replace=False))], 0.95) for _ in range(reps)]))


def q4(cells_U, cells_s, S, sd_med, n_star, rng, B=500, reps_point=50, reps_boot=10):
    m = [q95_sub(U, s, n_star, rng, reps_point) for U, s in zip(cells_U, cells_s)]
    point = (max(m) - min(m)) * sd_med
    boots = []
    for _ in range(B):
        cnt = np.bincount(rng.integers(0, S, S), minlength=S)
        bu, bs = [], []
        for U, s in zip(cells_U, cells_s):
            rep = cnt[s]
            idx = np.repeat(np.arange(len(U)), rep)
            cp = np.concatenate([np.arange(r) for r in rep]) if len(rep) else np.array([], int)
            bu.append(U[idx]); bs.append(s[idx] * 1000 + cp)
        mm = [q95_sub(U, s, n_star, rng, reps_boot) for U, s in zip(bu, bs)]
        boots.append((max(mm) - min(mm)) * sd_med)
    lo, hi = np.quantile(boots, [0.025, 0.975])
    return {"H_m": point, "ci": [float(lo), float(hi)], "verdict": "MATERIAL" if lo > L.H0 else ("IMMATERIAL" if hi < L.H0 else "INCONCLUSIVE"),
            "m_hat_subsampled": m, "n_star": n_star}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["selftest", "sizes", "fwer", "oc"])
    ap.add_argument("--export", nargs="+")
    ap.add_argument("--gt")
    ap.add_argument("--meta")
    ap.add_argument("--sizes")
    ap.add_argument("--horizon")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    if a.mode == "selftest":
        res = selftest()
    elif a.mode == "sizes":
        res = sizes(a.export, a.gt, a.meta, a.horizon)
    else:
        allsz = json.load(open(a.sizes))
        res = {}
        for fam, sz in allsz["families"].items():
            sz = dict(sz, n_scenes=allsz.get("n_scenes"))
            if a.mode == "fwer":
                r1 = fwer(sz)
                fr = {"primary_linear_band": r1}
                if not r1["ok"]:
                    fr["fallback_logit_band"] = fwer(sz, logit=True)
                fr["robustness_tau_1.0"] = fwer(sz, tau=1.0, logit=not r1["ok"])
                res[fam] = fr
            else:
                res[fam] = oc_q4(sz)
        if a.mode == "fwer":
            res["primary_linear_band"] = {"ok": all(res[f]["primary_linear_band"]["ok"] for f in allsz["families"])}
        else:
            res["targets_met"] = all(res[f].get("targets_met", False) for f in allsz["families"])
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    show = {k: v for k, v in res.items() if k != "cells"}
    print(json.dumps(show, default=float)[:2500])


if __name__ == "__main__":
    sys.exit(main())
