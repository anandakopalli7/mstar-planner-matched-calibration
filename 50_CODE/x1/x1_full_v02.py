#!/usr/bin/env python3
"""X1 full analysis v02 (Claude line, 30 Oct 2026): sections 8-15 of 40_PROTOCOL/X1_PREREGISTRATION_v02.md.
Two pre-registered families, t = 0 (tracker output) and h2s (prediction 2 s ahead with CANMOT's own model), Bonferroni:
simultaneous bands at 97.5 % and the material-margin lower bound at 1.25 % in each family; G1 holds if either family meets
section 15. Refuses to run unless the pre-registration hash equals its .sha256 sidecar and every file listed in its section 0
block has the recorded SHA-256. Seeds: one generator seeded 20261030 consumed in the order of this file; the 75/75 split
uses its own generator with the same seed.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_lib_v02 as L  # noqa: E402
import x1_prefreeze_v02 as PF  # noqa: E402

B_EXC, B_PRICE = 2000, 500
LEVEL = 0.975
DELTA_LO_Q = 0.0125
SIGMA_GRID = [0.10, 0.15, 0.20, 0.30, 0.50, 0.75, 1.00]


def check_freeze(prereg):
    side = open(prereg.replace(".md", ".sha256")).read().split()[0]
    if L.sha256_path(prereg) != side:
        raise SystemExit("pre-registration hash mismatch")
    txt = open(prereg, encoding="utf-8").read()
    block = txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
    meta = {}
    for ln in block.strip().splitlines():
        if not ln.strip() or ln.startswith("#") or ln.startswith("("):
            continue
        h, p = ln.split("  ", 1)
        if h == "setting":
            k, v = p.split("=", 1)
            meta[k.strip()] = v.strip()
        elif L.sha256_path(p.strip()) != h:
            raise SystemExit("frozen file changed: " + p)
    return side, meta


def band_verdicts(cells, elig, n_scenes, thr, W, logit):
    est, exc, tot, out = {}, {}, {}, {}
    for c in L.CELLS:
        d = cells[c]
        if d["n"] == 0:
            continue
        e = L.sums_by(d["s"], (d["U"] > L.Z95).astype(float), n_scenes)
        t = L.sums_by(d["s"], np.ones(d["n"]), n_scenes)
        exc[c], tot[c], est[c] = e, t, float(e.sum() / t.sum())
        m = t > 0
        out["|".join(c)] = {"E_rec": est[c], "E_scene": float(np.mean(e[m] / t[m])), "n": d["n"], "scenes": d["n_scenes"],
                            "threshold": thr.get(c, L.DELTA)}
    el = [c for c in elig if c in est]
    if el:
        boot = np.column_stack([(W @ exc[c]) / np.maximum(W @ tot[c], 1e-12) for c in el])
        e = np.array([est[c] for c in el])
        lo, hi, q, zero = L.sup_t_band(e, boot, logit=logit, level=LEVEL)
        vs = L.verdicts(e, lo, hi, zero, np.array([thr.get(c, L.DELTA) for c in el]))
        for c, l_, h_, z0, v in zip(el, lo, hi, zero, vs):
            out["|".join(c)].update({"lo": float(l_), "hi": float(h_), "zero_se": bool(z0), "verdict": v})
        out["_q"] = q
    return out


def analyse_cells(rows, sigma_a, rng, n_scenes, scene_names, logit, W, sigma_fn=None, **kw):
    cells, scenes, logs = L.cell_items(rows, sigma_a=sigma_a, sigma_fn=sigma_fn, **kw)
    null = L.orientation_null(cells, rng)
    thr = {c: max(L.DELTA, null[c][0]) if null[c][0] is not None else L.DELTA for c in L.CELLS}
    elig = [c for c in L.CELLS if cells[c]["n_scenes"] >= L.MIN_SCENES]
    sidx = {s: i for i, s in enumerate(scene_names)}
    remap = np.array([sidx[s] for s in scenes])
    for c in L.CELLS:
        if cells[c]["n"]:
            cells[c]["s"] = remap[cells[c]["s"]]
    return cells, null, thr, elig, band_verdicts(cells, elig, n_scenes, thr, W, logit)


def nees(rows, sigma_a, scene_names, W):
    sidx = {s: i for i, s in enumerate(scene_names)}
    acc = {}
    for r in rows:
        if not (r["paired"] and r["inpath"]):
            continue
        sxx, sxy, syy = r["S"]
        S = np.array([[sxx + sigma_a ** 2, sxy], [sxy, syy + sigma_a ** 2]])
        d = np.array([r["gx"] - r["mx"], r["gy"] - r["my"]])
        a = acc.setdefault((r["group"], r["range"]), [np.zeros(len(scene_names)), np.zeros(len(scene_names))])
        a[0][sidx[r["scene"]]] += float(d @ np.linalg.solve(S, d))
        a[1][sidx[r["scene"]]] += 1
    out = {}
    for key, (es, ns) in acc.items():
        boot = (W @ es) / np.maximum(W @ ns, 1e-12)
        lo, hi = np.quantile(boot, [0.025, 0.975])
        out["|".join(key)] = {"ANEES": float(es.sum() / ns.sum()), "ci": [float(lo), float(hi)], "n": int(ns.sum()),
                              "scenes": int((ns > 0).sum()),
                              "verdict": "OVERCONFIDENT" if lo > 2 else ("UNDERCONFIDENT" if hi < 2 else "CONSISTENT")}
    return out


def price_point(cells, elig, m0):
    p = {}
    for c in elig:
        d = cells[c]
        m = float(np.quantile(d["U"], 0.95))
        sd = float(np.median(np.sqrt(d["V"] + d["SA"] ** 2)))
        s, cap = L.inflation_needed(d["D"], d["V"], d["SA"])
        p[c] = {"m_hat": m, "SD_m": sd, "Delta_m": (m - max(L.Z95, m0[c] if m0[c] is not None else L.Z95)) * sd,
                "s_needed": s, "s_cap_hit": cap}
    if not p:
        return p, None, None
    cs, ss = max(v["m_hat"] for v in p.values()), max(v["s_needed"] for v in p.values())
    for c in elig:
        d = cells[c]
        p[c]["global_mult_overmargin_m"] = (cs - p[c]["m_hat"]) * p[c]["SD_m"]
        p[c]["global_infl_overmargin_m"] = float(np.median(L.Z95 * (np.sqrt(ss * d["V"] + d["SA"] ** 2) - np.sqrt(p[c]["s_needed"] * d["V"] + d["SA"] ** 2))))
    return p, cs, ss


def prices(cells, elig, m0, n_scenes, rng):
    point, cs, ss = price_point(cells, elig, m0)
    keys = ["m_hat", "Delta_m", "s_needed", "global_mult_overmargin_m", "global_infl_overmargin_m"]
    boots, dropped = {c: {k: [] for k in keys} for c in elig}, 0
    for _ in range(B_PRICE):
        cnt = np.bincount(rng.integers(0, n_scenes, n_scenes), minlength=n_scenes)
        bc = {c: L.expand(cells[c], cnt) for c in elig}
        if any(bc[c]["n"] == 0 for c in elig):
            dropped += 1
            continue
        p, _, _ = price_point(bc, elig, m0)
        for c in elig:
            for k in keys:
                boots[c][k].append(p[c][k])
    out = {"|".join(c): dict({k: {"point": point[c][k], "ci": [float(np.quantile(boots[c][k], 0.025)), float(np.quantile(boots[c][k], 0.975))],
                                  "lo_bonf": float(np.quantile(boots[c][k], DELTA_LO_Q))} for k in keys},
                             SD_m=point[c]["SD_m"], s_cap_hit=point[c]["s_cap_hit"]) for c in elig}
    return out, cs, ss, dropped


def fit_methods(cells, elig, cal_mask):
    fit, q, sn, pu, ps = {"crc": {}}, {}, {}, [], []
    for c in elig:
        d, m = cells[c], cal_mask[c]
        if m.sum() == 0:
            continue
        if len(np.unique(d["s"][m])) >= L.MIN_SCENES:
            fit["crc"][c] = L.crc_threshold(d["U"][m], d["s"][m])
        q[c] = float(np.quantile(d["U"][m], 0.95))
        sn[c] = L.inflation_needed(d["D"][m], d["V"][m], d["SA"][m])[0]
        pu.append(d["U"][m]); ps.append(d["s"][m])
    fit["c_star"] = max(q.values()) if q else None
    fit["s_star"] = max(sn.values()) if sn else None
    fit["pooled"] = L.crc_threshold(np.concatenate(pu), np.concatenate(ps)) if pu else None
    fit["certified_global"] = max(v for v in fit["crc"].values() if v is not None) if any(v is not None for v in fit["crc"].values()) else None
    return fit


def evaluate_methods(cells, elig, test_mask, fit):
    out = {}
    for c in elig:
        d, m = cells[c], test_mask[c]
        if m.sum() == 0:
            continue
        U, D, V, SA, s = d["U"][m], d["D"][m], d["V"][m], d["SA"][m], d["s"][m]
        sd = np.sqrt(V + SA ** 2)
        us = np.unique(s)

        def summ(ex, margin):
            sc_ex = np.array([ex[s == j].sum() for j in us], float)
            sc_n = np.array([(s == j).sum() for j in us], float)
            brng = np.random.default_rng(L.SEED + 7)
            bw = brng.multinomial(len(us), np.full(len(us), 1.0 / len(us)), size=500).astype(float)
            lo = float(np.quantile((bw @ sc_ex) / np.maximum(bw @ sc_n, 1e-12), 0.05))
            return {"exc_rec": float(np.mean(ex)), "exc_rec_lo95": lo, "exc_scene": float(np.mean(sc_ex / sc_n)),
                    "margin_median_m": float(np.median(margin)), "margin_mean_m": float(np.mean(margin))}
        row = {"n_test": int(m.sum()), "test_scenes": int(len(us))}
        if fit["crc"].get(c) is not None:
            row["crc_stratum"] = summ(U > fit["crc"][c], fit["crc"][c] * sd)
        if fit["c_star"] is not None:
            row["global_multiplier"] = summ(U > fit["c_star"], fit["c_star"] * sd)
        if fit["s_star"] is not None:
            thr = L.Z95 * np.sqrt(fit["s_star"] * V + SA ** 2)
            row["global_inflation"] = summ(D > thr, thr)
        if fit["pooled"] is not None:
            row["pooled_conformal"] = summ(U > fit["pooled"], fit["pooled"] * sd)
        if fit.get("certified_global") is not None:
            row["certified_global_multiplier"] = summ(U > fit["certified_global"], fit["certified_global"] * sd)
        row["uncalibrated"] = summ(U > L.Z95, L.Z95 * sd)
        out["|".join(c)] = row
    return out


def certification(cells, elig, scene_names, scene_log):
    n = len(scene_names)
    perm = np.random.default_rng(L.SEED).permutation(n)
    cal = perm[: n // 2].tolist()
    cm = {c: np.isin(cells[c]["s"], cal) for c in elig}
    fit = fit_methods(cells, elig, cm)
    res = {"split_seed": L.SEED, "fit": {"crc": {"|".join(c): v for c, v in fit["crc"].items()}, "c_star": fit["c_star"],
                                          "s_star": fit["s_star"], "pooled": fit["pooled"], "certified_global": fit.get("certified_global")},
           "held_out": evaluate_methods(cells, elig, {c: ~cm[c] for c in elig}, fit)}
    lolo = {}
    for lg in sorted(set(scene_log[s] for s in scene_names)):
        tidx = [i for i, s in enumerate(scene_names) if scene_log[s] == lg]
        tm = {c: np.isin(cells[c]["s"], tidx) for c in elig}
        f = fit_methods(cells, elig, {c: ~tm[c] for c in elig})
        lolo[lg] = {"n_scenes": len(tidx), "cells": evaluate_methods(cells, elig, tm, f)}
    res["leave_one_log_out"] = lolo
    ho = res["held_out"]
    crc_cells = [k for k, v in ho.items() if "crc_stratum" in v]
    k5 = {}
    if crc_cells:
        k5["a_mean_crc_scene_exc"] = float(np.mean([ho[k]["crc_stratum"]["exc_scene"] for k in crc_cells]))
        k5["a_ok"] = k5["a_mean_crc_scene_exc"] <= L.DELTA + 0.01
        tot = lambda meth: sum(ho[k][meth]["margin_mean_m"] * ho[k]["n_test"] for k in crc_cells if meth in ho[k])
        k5["b_total_margin_crc"], k5["b_total_margin_cstar"], k5["b_total_margin_sstar"] = tot("crc_stratum"), tot("global_multiplier"), tot("global_inflation")
        k5["b_total_margin_certified_global"] = tot("certified_global_multiplier")
        k5["b_note"] = "magnitude only (R04 m9): (ii) and (iii) are uncertified; vs the certified global multiplier the saving is the Thm 4 price"
        k5["c_cells_significantly_undercovered"] = [k for k in ho for m_ in ("pooled_conformal", "uncalibrated")
                                                    if ho[k].get(m_, {}).get("exc_rec_lo95", 0) > L.DELTA]
        k5["c_ok"] = len(k5["c_cells_significantly_undercovered"]) > 0
        k5["K5_supported"] = bool(k5["a_ok"] and k5["c_ok"])
    res["K5"] = k5
    return res


def family(label, rows, rows4, rowsr, scene_names, scene_log, logit, W, WL, rng, oc):
    res = {"label": label}
    n_sc = len(scene_names)
    cells, null, thr, elig, prim = analyse_cells(rows, 0.10, rng, n_sc, scene_names, logit, W)
    res["primary"], res["eligible"] = prim, ["|".join(c) for c in elig]
    res["orientation_null"] = {"|".join(c): {"E0": null[c][0], "m0": null[c][1]} for c in L.CELLS}
    for dlt, key in ((0.01, "delta_0.01"), (0.005, "delta_0.005")):
        z = float(L.norm.ppf(1 - dlt))
        res["estimates_" + key] = {"|".join(c): float(np.mean(cells[c]["U"] > z)) for c in L.CELLS if cells[c]["n"]}
    res["log_cluster_band"] = {k: v.get("verdict") for k, v in band_verdicts(cells, elig, n_sc, thr, WL, logit).items() if not k.startswith("_")}
    ne = nees(rows, 0.10, scene_names, W)
    res["nees"] = ne
    types = {"type_I": [], "type_II": [], "power_only": []}
    for c in elig:
        pv, nv = prim["|".join(c)].get("verdict"), ne.get("|".join(c[:2]), {}).get("verdict")
        if pv == "FAILS" and nv != "OVERCONFIDENT":
            types["type_I"].append("|".join(c))
        elif pv == "OVERCOVERS" and nv == "OVERCONFIDENT":
            types["type_II"].append("|".join(c))
        elif (pv == "CONSISTENT") != (nv == "CONSISTENT"):
            types["power_only"].append("|".join(c))
    res["nees_disagreement"] = types
    m0 = {c: null[c][1] for c in L.CELLS}
    pr, cs, ss, dropped = prices(cells, elig, m0, n_sc, rng)
    res["prices"] = {"cells": pr, "c_star_all": cs, "s_star_all": ss, "dropped_replicates": dropped}
    if len(elig) >= 2:
        sd_med = float(np.median([pr["|".join(c)]["SD_m"] for c in elig]))
        n_star = min(cells[c]["n_scenes"] for c in elig)
        q4 = PF.q4([cells[c]["U"] for c in elig], [cells[c]["s"] for c in elig], n_sc, sd_med, n_star, rng, B=500, reps_point=50, reps_boot=10)
        if not oc.get("targets_met", False):
            q4["verdict"] = "UNDERPOWERED"
        res["Q4"] = q4
    res["certification"] = certification(cells, elig, scene_names, scene_log)
    cells0, null0, _, elig0, _ = analyse_cells(rows, 0.0, rng, n_sc, scene_names, logit, W)
    pr0, _, _, _ = prices(cells0, elig0, {c: null0[c][1] for c in L.CELLS}, n_sc, rng)
    res["prices_sigma0"] = pr0
    res["certification_sigma0"] = certification(cells0, elig0, scene_names, scene_log)
    res["K5_both_sigma"] = bool(res["certification"]["K5"].get("K5_supported") and res["certification_sigma0"]["K5"].get("K5_supported"))
    sens, by_sigma = {}, {}
    for sa in sorted(set([0.0, 0.05, 0.20] + SIGMA_GRID)):
        _, _, _, _, b_ = analyse_cells(rows, sa, rng, n_sc, scene_names, logit, W)
        by_sigma[sa] = b_
        if sa in (0.0, 0.05, 0.20):
            sens["sigma_a=%.2f" % sa] = {k: {kk: v.get(kk) for kk in ("E_rec", "threshold", "verdict")} for k, v in b_.items() if not k.startswith("_")}
    sfn = lambda r: 0.10 * (1 + math.hypot(r["mx"] - r["cx"], r["my"] - r["cy"]) / 40) * (1.5 if r["group"] == "large" else 1.0)
    _, _, _, _, b_ = analyse_cells(rows, 0.10, rng, n_sc, scene_names, logit, W, sigma_fn=sfn)
    sens["sigma_a_range_size"] = {k: {kk: v.get(kk) for kk in ("E_rec", "verdict")} for k, v in b_.items() if not k.startswith("_")}
    fails = [c for c in elig if prim["|".join(c)].get("verdict") == "FAILS"]
    tip = {}
    for c in fails:
        key = "|".join(c)
        vt = next((sa for sa in SIGMA_GRID if by_sigma[sa].get(key, {}).get("verdict") != "FAILS"), None)
        lo_, hi_ = 0.0, 2.0
        d0 = cells[c]

        def pt(sa, d0=d0, c=c):
            allc = dict(d0["all"])
            allc["sa"] = np.full_like(allc["var"], sa)
            nl = L.orientation_null({c: {"all": allc}}, rng)[c][0] or L.DELTA
            return float(np.mean(d0["D"] / np.sqrt(d0["V"] + sa ** 2) > L.Z95)) <= max(L.DELTA, nl)
        if not pt(hi_):
            ptip = "> 2.0"
        else:
            for _ in range(12):
                mid = (lo_ + hi_) / 2
                if pt(mid):
                    hi_ = mid
                else:
                    lo_ = mid
            ptip = hi_
        tip[key] = {"point_tipping_sigma_a_m": ptip, "verdict_tipping_sigma_a_m": vt if vt is not None else "> 1.00"}
    sens["tipping"] = tip
    for lab, rr in (("gate_4m", rows4), ("per_frame_rematch", rowsr)):
        _, _, _, _, bx = analyse_cells(rr, 0.10, rng, n_sc, scene_names, logit, W)
        sens[lab] = {k: {kk: v.get(kk) for kk in ("E_rec", "verdict", "scenes")} for k, v in bx.items() if not k.startswith("_")}
    for lab, kw in (("contested_excluded", {"exclude_contested": True}), ("first_records_excluded", {"exclude_first": True}),
                    ("all_objects", {"inpath_only": False})):
        _, _, _, _, bx = analyse_cells(rows, 0.10, rng, n_sc, scene_names, logit, W, **kw)
        sens[lab] = {k: {kk: v.get(kk) for kk in ("E_rec", "verdict", "scenes")} for k, v in bx.items() if not k.startswith("_")}
    ct, sct, _ = L.cell_items(rows, sigma_a=0.10, orient="truth")
    sidx = {s: i for i, s in enumerate(scene_names)}
    for c in L.CELLS:
        if ct[c]["n"]:
            ct[c]["s"] = np.array([sidx[sct[i]] for i in ct[c]["s"]])
    elig_t = [c for c in L.CELLS if ct[c]["n_scenes"] >= L.MIN_SCENES]
    sens["truth_oriented_not_measurable"] = {k: {kk: v.get(kk) for kk in ("E_rec", "verdict")} for k, v in
                                             band_verdicts(ct, elig_t, n_sc, {}, W, logit).items() if not k.startswith("_")}
    mix = {}
    for c in L.CELLS:
        if cells[c]["n"]:
            u, n = np.unique(cells[c]["names"], return_counts=True)
            exc = cells[c]["U"] > L.Z95
            mix["|".join(c)] = {"classes": dict(zip(u.tolist(), n.tolist())),
                                "share_of_exceedances_from_drifted_pairs": float(cells[c]["drift"][exc].mean()) if exc.any() else None}
    sens["cell_composition"] = mix
    res["sensitivities"] = sens
    s020, cex = by_sigma[0.20], sens["contested_excluded"]
    fail_groups = {"|".join(x[:2]) for x in fails}
    g1 = []
    for c in fails:
        key = "|".join(c)
        nv = ne.get("|".join(c[:2]), {})
        b2 = bool(nv) and any(h != "|".join(c[:2]) and v["scenes"] >= L.MIN_SCENES and h not in fail_groups and v["ci"][0] > nv["ci"][1]
                              for h, v in ne.items())
        row = {"cell": key, "a1": True, "a2_material": pr[key]["Delta_m"]["lo_bonf"] > L.H0,
               "a3_sigma_0.20": s020.get(key, {}).get("verdict") == "FAILS",
               "a4_contested_excluded": cex.get(key, {}).get("verdict") == "FAILS",
               "a5_truth_oriented_fails": sens["truth_oriented_not_measurable"].get(key, {}).get("verdict") == "FAILS",
               "b1_nees_not_overconfident": nv.get("verdict") in ("CONSISTENT", "UNDERCONFIDENT"), "b2_nees_ranks_wrongly": b2}
        row["holds"] = bool(row["a2_material"] and row["a3_sigma_0.20"] and row["a4_contested_excluded"] and row["a5_truth_oriented_fails"]
                            and (row["b1_nees_not_overconfident"] or b2))
        g1.append(row)
    res["G1_family"] = {"candidate_cells": g1, "holds": any(x["holds"] for x in g1)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--oc", required=True)
    ap.add_argument("--horizon", default=None, help="x1_horizon_prep_v01 output (required for the real run)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pre_sha, settings = check_freeze(a.prereg)
    logit = settings.get("band", "linear") == "logit"
    t0 = time.time()
    rng = np.random.default_rng(L.SEED)
    res = {"prereg_sha256": pre_sha, "band": "logit" if logit else "linear", "band_level": LEVEL}
    tokens, recs = set(), []
    for w in a.workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r["status_X1_gates"] == "PASS", "export worker failed Q0: " + w
        pf = json.load(open(os.path.join(w, "x1_per_frame.json")))
        wt = [p["token"] for p in pf if not p.get("error")]
        assert not (set(wt) & tokens), "token exported twice"
        tokens |= set(wt)
        recs += L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
    assert len(tokens) == 6019, "union does not cover the 6019 val tokens"
    samples, gtb, racks = L.load_gt(a.gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(a.meta, "scene.json")))}
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    rows4, pst4 = L.build_table(recs, samples, gtb, racks, gate=4.0, scene_log=scene_log)
    rowsr, pstr = L.build_table(recs, samples, gtb, racks, persistent=False, scene_log=scene_log)
    res["pairing"], res["pairing_gate4"], res["pairing_rematch"] = pst, pst4, pstr
    c6 = [r["c6"] for r in rows if r["c6"] is not None and not r["first"]]
    res["Q0"] = {"tokens": len(tokens), "records": len(recs), "C6_max_abs_m_non_birth": float(max(c6)) if c6 else None,
                 "C6_pass": bool(c6) and max(c6) <= 1e-6}
    res["Q1_paired_share_of_inpath"] = pst.get("paired_inpath", 0) / max(pst.get("inpath_records", 1), 1)
    scene_names = sorted({r["scene"] for r in rows})
    logs = sorted(set(scene_log[s] for s in scene_names))
    scene_log_idx = np.array([logs.index(scene_log[s]) for s in scene_names])
    W = L.boot_weights(len(scene_names), B_EXC, rng)
    WL = L.log_cluster_weights(scene_log_idx, len(logs), B_EXC, rng)
    oc = json.load(open(a.oc))
    res["family_t0"] = family("t0", rows, rows4, rowsr, scene_names, scene_log, logit, W, WL, rng, oc.get("t0", oc))
    print("family t0 %.0f s" % (time.time() - t0), flush=True)
    holds = [res["family_t0"]["G1_family"]["holds"]]
    if a.horizon:
        pred = L.load_horizon(a.horizon)
        hr, hst = L.build_horizon_rows(rows, pred, samples, gtb, racks)
        hr4, _ = L.build_horizon_rows(rows4, pred, samples, gtb, racks)
        hrr, _ = L.build_horizon_rows(rowsr, pred, samples, gtb, racks)
        res["horizon_rows"] = hst
        res["family_h2s"] = family("h2s", hr, hr4, hrr, scene_names, scene_log, logit, W, WL, rng, oc.get("h2s", oc))
        holds.append(res["family_h2s"]["G1_family"]["holds"])
        print("family h2s %.0f s" % (time.time() - t0), flush=True)
    res["G1"] = {"family_holds": holds, "G1_holds": any(holds),
                 "rule": "Bonferroni over two pre-registered families (t0, h2s): bands at 97.5 %, material lower bound at 1.25 %"}
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res["G1"], default=float), flush=True)


if __name__ == "__main__":
    sys.exit(main())
