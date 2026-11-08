#!/usr/bin/env python3
"""X1 full analysis (Claude line, v01, 30 Oct 2026): sections 7-15 of 40_PROTOCOL/X1_PREREGISTRATION_v01.md.
Refuses to run unless the pre-registration file hash equals the frozen value in X1_PREREGISTRATION_v01.sha256.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_analysis_v01 as X  # noqa: E402

B_EXC, B_PRICE, B_Q4 = 2000, 500, 500


def per_cell(rows, sigma_a, inpath_only=True, pool=None):
    data, scenes = X.cell_arrays(rows, sigma_a=sigma_a, inpath_only=inpath_only, pool=pool)
    out = {}
    for c in X.CELLS:
        D, V, s = data[c]["D"], data[c]["V"], data[c]["s"]
        U = D / np.sqrt(V + sigma_a ** 2) if len(D) else D
        out[c] = {"D": D, "V": V, "s": s, "U": U, "n_scenes": int(len(np.unique(s))), "n": int(len(D))}
    return out, scenes


def exceedance_block(cells, n_scenes, thr, rng, eligible):
    est, sw, exc_l, tot_l = {}, {}, {}, {}
    for c in X.CELLS:
        d = cells[c]
        if d["n"] == 0:
            continue
        exc, tot = X.exceed_counts(d["U"], d["s"], n_scenes, thr)
        exc_l[c], tot_l[c] = exc, tot
        est[c] = float(exc.sum() / tot.sum())
        m = tot > 0
        sw[c] = float(np.mean(exc[m] / tot[m]))
    elig = [c for c in eligible if c in est]
    res = {"|".join(c): {"E_inst": est[c], "E_scene": sw[c], "n": cells[c]["n"], "scenes": cells[c]["n_scenes"]} for c in est}
    if elig:
        W = X.boot_weights(n_scenes, B_EXC, rng)
        boot = np.column_stack([(W @ exc_l[c]) / np.maximum(W @ tot_l[c], 1e-12) for c in elig])
        e = np.array([est[c] for c in elig])
        lo, hi, q = X.simultaneous_bounds(e, boot)
        for c, l_, h_ in zip(elig, lo, hi):
            v = "FAILS" if l_ > X.DELTA else ("OVERCOVERS" if h_ < X.DELTA else "CONSISTENT")
            res["|".join(c)].update({"sim_lo": float(l_), "sim_hi": float(h_), "verdict": v})
        res["_maxt_q"] = q
    return res


def nees_block(rows, sigma_a, n_scenes, scene_index, rng):
    acc = {}
    for r in rows:
        if not r["inpath"]:
            continue
        sxx, sxy, syy = r["S"]
        S = np.array([[sxx + sigma_a ** 2, sxy], [sxy, syy + sigma_a ** 2]])
        d = np.array([r["gx"] - r["mx"], r["gy"] - r["my"]])
        e = float(d @ np.linalg.solve(S, d))
        key = (r["group"], r["range"])
        a = acc.setdefault(key, (np.zeros(n_scenes), np.zeros(n_scenes)))
        a[0][scene_index[r["scene"]]] += e
        a[1][scene_index[r["scene"]]] += 1
    W = X.boot_weights(n_scenes, B_EXC, rng)
    out = {}
    for key, (es, ns) in acc.items():
        anees = float(es.sum() / ns.sum())
        boot = (W @ es) / np.maximum(W @ ns, 1e-12)
        lo, hi = np.quantile(boot, [0.025, 0.975])
        v = "OVERCONFIDENT" if lo > 2 else ("UNDERCONFIDENT" if hi < 2 else "CONSISTENT")
        out["|".join(key)] = {"ANEES": anees, "ci": [float(lo), float(hi)], "verdict": v, "n": int(ns.sum())}
    return out


def expand(d, cnt):
    rep = cnt[d["s"]]
    idx = np.repeat(np.arange(d["n"]), rep)
    copy = np.concatenate([np.arange(k) for k in rep]) if d["n"] else np.array([], int)
    return {"D": d["D"][idx], "V": d["V"][idx], "U": d["U"][idx], "s": d["s"][idx] * 1000 + copy, "n": len(idx)}


def prices(cells_d, elig, sigma_a):
    m = {c: float(np.quantile(cells_d[c]["U"], 0.95)) for c in elig}
    sd = {c: float(np.median(np.sqrt(cells_d[c]["V"] + sigma_a ** 2))) for c in elig}
    s_need = {c: X.inflation_needed(cells_d[c]["D"], cells_d[c]["V"], sigma_a) for c in elig}
    c_star, s_star = max(m.values()), max(s_need.values())
    out = {}
    for c in elig:
        V = cells_d[c]["V"]
        infl_over = float(np.median(X.Z95 * (np.sqrt(s_star * V + sigma_a ** 2) - np.sqrt(s_need[c] * V + sigma_a ** 2))))
        out[c] = {"m_hat": m[c], "SD_m": sd[c], "extra_margin_needed_m": (m[c] - X.Z95) * sd[c],
                  "global_multiplier_overmargin_m": (c_star - m[c]) * sd[c], "s_needed": s_need[c],
                  "global_inflation_overmargin_m": infl_over}
    return out, c_star, s_star


def prices_block(cells, elig, n_scenes, sigma_a, rng):
    point, c_star, s_star = prices(cells, elig, sigma_a)
    keys = ["m_hat", "extra_margin_needed_m", "global_multiplier_overmargin_m", "s_needed", "global_inflation_overmargin_m"]
    boots = {c: {k: [] for k in keys} for c in elig}
    for _ in range(B_PRICE):
        cnt = np.bincount(rng.integers(0, n_scenes, n_scenes), minlength=n_scenes)
        bc = {c: expand(cells[c], cnt) for c in elig}
        if any(bc[c]["n"] == 0 for c in elig):
            continue
        p, _, _ = prices(bc, elig, sigma_a)
        for c in elig:
            for k in keys:
                boots[c][k].append(p[c][k])
    out = {}
    for c in elig:
        out["|".join(c)] = {k: {"point": point[c][k], "ci": [float(np.quantile(boots[c][k], 0.025)), float(np.quantile(boots[c][k], 0.975))]}
                            for k in keys}
        out["|".join(c)]["SD_m"] = point[c]["SD_m"]
    return out, c_star, s_star


def certification(cells, elig, scene_names, scene_log, c_star, s_star, sigma_a, rng):
    n_sc = len(scene_names)
    perm = np.random.default_rng(X.SEED).permutation(n_sc)
    cal_set, test_set = set(perm[: n_sc // 2]), set(perm[n_sc // 2:])
    out = {"split_seed": X.SEED, "cells": {}}
    for c in elig:
        d = cells[c]
        mc = np.isin(d["s"], list(cal_set))
        mt = np.isin(d["s"], list(test_set))
        ncal = len(np.unique(d["s"][mc]))
        row = {"cal_scenes": int(ncal), "test_scenes": int(len(np.unique(d["s"][mt])))}
        def held(thr_fn):
            ex = thr_fn(d, mt)
            st = d["s"][mt]
            us = np.unique(st)
            return {"inst": float(np.mean(ex)), "scene": float(np.mean([np.mean(ex[st == j]) for j in us]))}
        if ncal >= X.MIN_SCENES:
            ch = X.crc_threshold(d["U"][mc], d["s"][mc])
            row["c_hat"] = ch
            row["heldout_crc"] = held(lambda d_, m_: d_["U"][m_] > ch)
        row["heldout_uncalibrated_z"] = held(lambda d_, m_: d_["U"][m_] > X.Z95)
        row["heldout_global_multiplier"] = held(lambda d_, m_: d_["U"][m_] > c_star)
        row["heldout_global_inflation"] = held(lambda d_, m_: d_["D"][m_] > X.Z95 * np.sqrt(s_star * d_["V"][m_] + sigma_a ** 2))
        out["cells"]["|".join(c)] = row
    # leave-one-log-out
    logs = sorted(set(scene_log.values()))
    lolo = {}
    for c in elig:
        d = cells[c]
        vals = []
        for lg in logs:
            test_idx = [i for i, s in enumerate(scene_names) if scene_log[s] == lg]
            mt = np.isin(d["s"], test_idx)
            mc = ~mt
            if mt.sum() == 0 or len(np.unique(d["s"][mc])) < X.MIN_SCENES:
                continue
            ch = X.crc_threshold(d["U"][mc], d["s"][mc])
            vals.append(float(np.mean(d["U"][mt] > ch)))
        if vals:
            lolo["|".join(c)] = {"logs": len(vals), "mean": float(np.mean(vals)), "min": float(np.min(vals)), "max": float(np.max(vals))}
    out["leave_one_log_out"] = lolo
    return out


def tipping_sigma(rows, cell):
    lo, hi = 0.0, 2.0
    def point(sa):
        data, _ = X.cell_arrays(rows, sigma_a=sa)
        D, V = data[cell]["D"], data[cell]["V"]
        return np.mean(D / np.sqrt(V + sa ** 2) > X.Z95)
    if point(hi) > X.DELTA:
        return None
    for _ in range(25):
        mid = (lo + hi) / 2
        if point(mid) <= X.DELTA:
            hi = mid
        else:
            lo = mid
    return hi


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--export", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True, help="v1.0-trainval dir (scene.json for logs)")
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--oc", required=True, help="Q4 operating-characteristics json")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    frozen = open(a.prereg.replace(".md", ".sha256")).read().split()[0]
    if X.sha256_path(a.prereg) != frozen:
        raise SystemExit("pre-registration hash mismatch: refusing to run")
    t0 = time.time()
    rng = np.random.default_rng(X.SEED)
    res = {"prereg_sha256": frozen, "export_sha256": X.sha256_path(a.export), "gt_sha256": X.sha256_path(a.gt)}
    recs = X.load_export(a.export)
    samples, gtb = X.load_gt(a.gt)
    rows, pst = X.build_table(recs, samples, gtb, gate=2.0)
    res["pairing"] = pst
    scenes_json = json.load(open(os.path.join(a.meta, "scene.json")))
    scene_log = {s["name"]: s["log_token"] for s in scenes_json}
    cells, scene_names = per_cell(rows, X.SIGMA_A)
    n_scenes = len(scene_names)
    sidx = {s: i for i, s in enumerate(scene_names)}
    elig = [c for c in X.CELLS if cells[c]["n_scenes"] >= X.MIN_SCENES]
    res["eligible_cells"] = ["|".join(c) for c in elig]
    inpath_n = sum(1 for r in rows if r["inpath"])
    res["Q1_inpath_records"] = inpath_n
    # section 7
    res["primary"] = exceedance_block(cells, n_scenes, X.Z95, rng, elig)
    res["estimates_delta_0.01"] = {k: v["E_inst"] for k, v in exceedance_block(cells, n_scenes, float(X.norm.ppf(0.99)), rng, []).items() if not k.startswith("_")}
    res["estimates_delta_0.005"] = {k: v["E_inst"] for k, v in exceedance_block(cells, n_scenes, float(X.norm.ppf(0.995)), rng, []).items() if not k.startswith("_")}
    print("primary done %.0f s" % (time.time() - t0), flush=True)
    # section 8
    nees = nees_block(rows, X.SIGMA_A, n_scenes, sidx, rng)
    res["nees"] = nees
    mapping = {"OVERCONFIDENT": "FAILS", "CONSISTENT": "CONSISTENT", "UNDERCONFIDENT": "OVERCOVERS"}
    disagree = []
    for c in elig:
        pv = res["primary"]["|".join(c)].get("verdict")
        nv = nees.get("|".join(c[:2]), {}).get("verdict")
        if pv and nv and mapping[nv] != pv:
            disagree.append({"cell": "|".join(c), "projected": pv, "nees": nv})
    res["nees_disagreement"] = {"k": len(disagree), "cells": disagree}
    print("nees done %.0f s" % (time.time() - t0), flush=True)
    # section 9
    pr, c_star, s_star = prices_block(cells, elig, n_scenes, X.SIGMA_A, rng)
    res["prices"] = {"cells": pr, "c_star": c_star, "s_star": s_star}
    print("prices done %.0f s" % (time.time() - t0), flush=True)
    # section 10
    oc = json.load(open(a.oc))
    sd_med = float(np.median([pr["|".join(c)]["SD_m"] for c in elig])) if elig else None
    if len(elig) >= 2:
        n_star = min(cells[c]["n_scenes"] for c in elig)
        q4 = X.q4_with_bootstrap([cells[c]["U"] for c in elig], [cells[c]["s"] for c in elig], n_scenes, sd_med, n_star, rng,
                                 B=B_Q4, reps_point=50, reps_boot=10)
        if not oc.get("targets_met", False):
            q4["verdict_as_registered"] = "UNDERPOWERED (OC targets not met before freeze); estimates only"
            q4["verdict"] = "UNDERPOWERED"
        res["Q4"] = q4
    print("Q4 done %.0f s" % (time.time() - t0), flush=True)
    # section 11
    res["certification"] = certification(cells, elig, scene_names, scene_log, c_star, s_star, X.SIGMA_A, rng)
    print("certification done %.0f s" % (time.time() - t0), flush=True)
    # section 13 sensitivities (point estimates and verdicts)
    sens = {}
    for sa in (0.0, 0.05, 0.20):
        cs, _ = per_cell(rows, sa)
        sens["sigma_a=%.2f" % sa] = {k: {kk: v.get(kk) for kk in ("E_inst", "verdict")} for k, v in
                                     exceedance_block(cs, n_scenes, X.Z95, rng, elig).items() if not k.startswith("_")}
    rows4, pst4 = X.build_table(recs, samples, gtb, gate=4.0)
    cs4, sn4 = per_cell(rows4, X.SIGMA_A)
    sens["gate_4m"] = {"pairing": pst4, "cells": {k: {kk: v.get(kk) for kk in ("E_inst", "verdict")} for k, v in
                       exceedance_block(cs4, len(sn4), X.Z95, rng, elig).items() if not k.startswith("_")}}
    csa, sna = per_cell(rows, X.SIGMA_A, inpath_only=False)
    elig_a = [c for c in X.CELLS if csa[c]["n_scenes"] >= X.MIN_SCENES]
    sens["all_objects"] = {k: {kk: v.get(kk) for kk in ("E_inst", "verdict", "n", "scenes")} for k, v in
                           exceedance_block(csa, len(sna), X.Z95, rng, elig_a).items() if not k.startswith("_")}
    csp, snp = per_cell(rows, X.SIGMA_A, pool="active_tras")
    elig_p = [c for c in X.CELLS if csp[c]["n_scenes"] >= X.MIN_SCENES]
    sens["active_pool_only"] = {k: {kk: v.get(kk) for kk in ("E_inst", "verdict", "n")} for k, v in
                                exceedance_block(csp, len(snp), X.Z95, rng, elig_p).items() if not k.startswith("_")}
    fails = [c for c in elig if res["primary"]["|".join(c)].get("verdict") == "FAILS"]
    sens["tipping_sigma_a_m"] = {"|".join(c): tipping_sigma(rows, c) for c in fails}
    res["sensitivities"] = sens
    # section 15
    a_ok = len(fails) >= 1
    b_ok = res["nees_disagreement"]["k"] >= 1 or res.get("Q4", {}).get("verdict") == "MATERIAL"
    res["G1"] = {"a_any_cell_fails": a_ok, "fails_cells": ["|".join(c) for c in fails],
                 "b_nees_disagree_or_Q4_material": b_ok, "G1_holds": bool(a_ok and b_ok)}
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res["G1"]), flush=True)


if __name__ == "__main__":
    sys.exit(main())
