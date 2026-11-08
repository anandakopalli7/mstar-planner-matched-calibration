#!/usr/bin/env python3
"""c1crit_rstar2_v03 (5 Nov 2026): development check v03 of rule set R*2 = R* (c1crit_rstar_v02) changed by D16 v33 Choice 52(c), (d).
nuScenes K8 development data ONLY (the K8 Linux replicate, its v03 analysis, the K8 joint run). No Argoverse 2 file of any kind is
read. Outputs only in 60_RESULTS/c1_criteria_sensitivity_v03/; v01 and v02 files are read, never written.

R*2's levels: flags against M* at 0.95 (cell, family, pooled LB); HK1c pooled UB at L = 0.995 <= delta + 0.03; comparator removal
from V_t: each of 9 conditions at 1 - 0.0125/9; Form B UB^{1 - 0.0125/|V_t|}(Delta) < 0; Form C and H10's NI at 0.975; H3: V^J
removal at 1 - 0.0025/3 per pooled condition, H3's p = min(1, 2 |V^J| max_c p_c) with p_c the share of bootstrap means >= 0,
judged at the Holm levels 0.005, 0.00625, 0.00833, 0.0125, 0.025; B = 20000 for every observed-data bootstrap; the power rule keeps
2000 datasets and the first 500 weights (target-only, others at delta: c1crit_rstar_v02.power_target_delta).
Reused (imported, unchanged): c1crit_common_v01 (data, status), c1crit_rstar_v02 (flags_at, pooled_ub, joint_tables,
power_target_delta, validity_rstar, forms_rstar, check_rstar_functions), k6_analyse_v02 (rates, flag, evaluable), m_lib_v04._simul,
c1_analyse_v02.paired, c1_power_counts_v02 (load_tracker, run_oc, ablation_fails), c1_power_counts_v03.cap_mstar.
New: rates_log / paired_log (the same estimators computed from log-level sums, B x 68 instead of B x 840; asserted equal to
k6_analyse_v02.rates and c1_analyse_v02.paired on the primary weights before E3 uses them).
Parts: CP3 (M*'s families on the v03 weights' first 500), C3 (the verdict), E3 (seed-set stability), A3 (M*'s pooled-UB coverage at
B = 20000), D3 (the OC at 375 units, in checkpointed chunks).
Seeds: primary weights [20261401, i, 0] (i = 0 T1, 1 T3), B = 20000; CP3 [20261405, i, k]; E3 [20261402, i, s], s = 1..S;
D3 [20261403, variant, chunk] (cap [.., 7]); A3 [20261404, i]. Usage: python -B c1crit_rstar2_v03.py <part> [options]
"""
import argparse
import json
import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_rstar_v02 as R2  # noqa: E402
import numpy as np  # noqa: E402

A, PC2, CA2 = C.A, C.PC2, C.CA2
M = A.M
OUT3 = os.path.join(C.W_ROOT, "60_RESULTS", "c1_criteria_sensitivity_v03")
DELTA = C.DELTA
B3 = 20000
FLAG_M = 0.95
L_HK1C = 0.995
REMOVE = 1 - 0.0125 / 9
SUPER = 0.0125
REMOVE_J = 1 - 0.0025 / 3
LEVEL_C = 0.975
HOLM = (0.005, 0.00625, 0.025 / 3, 0.0125, 0.025)
INV = R2.INV
POPL = ("PD7", "SD1_7", "PD")


def ck(part):
    d = os.path.join(OUT3, part + "_ckpt")
    os.makedirs(d, exist_ok=True)
    return d


def weights_log(dev, seed, B=B3):
    rng = np.random.default_rng(seed)
    return rng.multinomial(dev.n_logs, np.full(dev.n_logs, 1.0 / dev.n_logs), size=B).astype(float)


def G_of(dev):
    G = np.zeros((dev.n_logs, len(dev.scenes)))
    G[dev.log_idx, np.arange(len(dev.scenes))] = 1.0
    return G


def rates_log(N, X, Wl, G):
    """k6_analyse_v02.rates(N, X, Wl[:, log_idx]) from log-level sums (identical estimator)."""
    p = np.divide(X, N, out=np.zeros_like(X), where=N > 0)
    pres = (N > 0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (Wl @ (G @ p)) / (Wl @ (G @ pres))


def paired_log(rate, Wl, G, a, b, level):
    d = np.asarray(rate[a], float) - np.asarray(rate[b], float)
    bm = (Wl @ (G @ d)) / (Wl @ G.sum(1))
    return {"mean_diff": float(d.mean()), "ub": float(np.quantile(bm, level)), "p_lt0": float(np.mean(bm >= 0)), "_bm": bm}


def families(tag):
    """M*: CP3 (v03 weights); B0, B3: v02's CP (K8 weights); others: none (removed by cell flags; reported)."""
    out = {}
    for arm in C.ARMS:
        for lab in POPL:
            f = None
            if arm == "Mstar":
                p = os.path.join(OUT3, "CP3_ckpt", "CP3_%s_Mstar_%s.json" % (tag, lab))
                if os.path.exists(p):
                    with open(p) as fh:
                        f = json.load(fh)
            if f is None:
                f = R2.cp_family(tag, arm, lab)
            out[(arm, lab)] = f
    return out


# ------------------------------------------------------------------ CP3
def part_cp3(tags):
    d = ck("CP3")
    for tag in tags:
        dev = C.Dev(tag)
        Wl = weights_log(dev, [20261401, dev.i, 0])
        W500 = Wl[:500][:, dev.log_idx]
        for k, lab in enumerate(POPL):
            path = os.path.join(d, "CP3_%s_Mstar_%s.json" % (tag, lab))
            if os.path.exists(path):
                continue
            t0 = time.time()
            N = dev.N[INV[lab]][C.ARMS.index("Mstar")]
            ev = A.evaluable(N, dev.scenes, dev.log_idx)
            seed = [20261405, dev.i, k]
            pw = R2.power_target_delta(N, ev, W500, np.random.default_rng(seed), 0.15, 0.5, 2000)
            qual = ev & (pw >= 0.80)
            rec = N.sum(0)
            r = {"tracker": tag, "arm": "Mstar", "pop": lab, "seed": seed, "weights": "first 500 of [20261401, i, 0], B = 20000",
                 "power": {C.CELL_NAMES[j]: float(pw[j]) for j in np.flatnonzero(ev)}, "family": [C.CELL_NAMES[j] for j in np.flatnonzero(qual)],
                 "family_size": int(qual.sum()), "record_share": float(rec[qual].sum() / rec.sum()), "seconds": time.time() - t0}
            C.jdump(path, r)
            print("CP3", tag, lab, r["family_size"], round(r["record_share"], 3), round(r["seconds"], 1), "s", flush=True)


# ------------------------------------------------------------------ the verdict for one weight set (C3 uses it with full W; E3 with log sums)
def verdict(dev, Wl, fams, jt=None, jrate=None, fast=False):
    G = G_of(dev)
    W = None if fast else Wl[:, dev.log_idx]
    one = np.ones((1, len(dev.scenes)))

    def rb(N, X):
        return rates_log(N, X, Wl, G) if fast else A.rates(N, X, W)

    def pr(rate, a, b, level):
        return paired_log(rate, Wl, G, a, b, level) if fast else CA2.paired(rate, W, a, b, level)
    t = {"arms": {}}
    for arm in C.ARMS:
        a = {"pops": {}}
        removed = []
        for p in C.POPS:
            lab = C.LAB[p]
            N, X = dev.T(arm)[p]
            ev = np.flatnonzero(A.evaluable(N, dev.scenes, dev.log_idx))
            est, boot = A.rates(N, X, one)[0], rb(N, X)
            fam = fams.get((arm, lab))
            famidx = None if fam is None else np.array([C.CELL_NAMES.index(c) for c in fam["family"]], int)
            Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
            e1, b1 = A.rates(Np, Xp, one)[0], rb(Np, Xp)
            lev = FLAG_M if arm == "Mstar" else REMOVE
            r = {"evaluable": int(len(ev))}
            cf = A.flag(est, boot, ev, lev) if len(ev) else None
            r["cell_flags"] = [C.CELL_NAMES[ev[i]] for i in np.flatnonzero(cf[3])] if cf is not None else []
            if cf is not None:
                se = cf[2]
                okc = se > 0
                tt = np.where(okc, (est[ev] - DELTA) / np.where(okc, se, 1.0), -np.inf)
                r["max_t_minus_q"] = float(np.max(tt) - cf[4]) if np.isfinite(cf[4]) else None
            r["family_size"] = None if fam is None else fam["family_size"]
            r["family_flags"] = None
            if famidx is not None and len(famidx):
                r["family_flags"] = [C.CELL_NAMES[famidx[i]] for i in np.flatnonzero(A.flag(est, boot, famidx, lev)[3])]
            lbp, ubp, _, sgp, _ = A.flag(e1, b1, np.array([0]), lev)
            r["pooled"] = {"E": float(e1[0]), "lb": float(lbp[0]), "flagged": bool(sgp[0])}
            if arm == "Mstar":
                ubL = float(A.flag(e1, b1, np.array([0]), L_HK1C)[1][0])
                r["pooled_ub_at_L"] = ubL
                r["HK1c"] = bool(ubL <= DELTA + 0.03)
                r["floor"] = (r["family_size"] is not None and r["family_size"] >= 6) if lab != "PD" else len(ev) >= 1
                r["ok"] = bool(not r["cell_flags"] and not (r["family_flags"] or []) and not r["pooled"]["flagged"] and r["floor"] and r["HK1c"])
            else:
                if r["cell_flags"]:
                    removed.append("%s cell" % lab)
                if r["family_flags"]:
                    removed.append("%s family" % lab)
                if r["pooled"]["flagged"]:
                    removed.append("%s pooled" % lab)
            a["pops"][lab] = r
        if arm == "Mstar":
            a["valid"] = bool(all(a["pops"][l]["ok"] for l in POPL))
        else:
            a["removed"] = bool(removed)
            a["removed_by"] = removed
        t["arms"][arm] = a
    V = [c for c in C.COMPS if not t["arms"][c]["removed"]]
    lvl = 1 - SUPER / max(len(V), 1)
    fb = {c: pr(dev.rate, "Mstar", c, lvl) for c in V}
    t["V_t"] = V
    t["formB"] = {"level": lvl, "ub": {c: v["ub"] for c, v in fb.items()},
                  "met": bool(t["arms"]["Mstar"]["valid"] and all(v["ub"] < 0 for v in fb.values())), "vacuous": not V}
    t["formA"] = {c: pr(dev.rate, "Mstar", c, 1 - 0.05 / 4)["ub"] for c in ("B0", "B1", "B4", "B9")}
    t["formA_met"] = bool(t["arms"]["Mstar"]["valid"] and all(u < 0 for u in t["formA"].values()))
    rc = pr(dev.rate, "Mstar", "B4", LEVEL_C)
    t["formC"] = {"ub_0.975": rc["ub"], "met": bool(rc["ub"] <= 0.03)}
    r6 = pr(dev.rate, "Mstar", "B6", LEVEL_C)
    det = {}
    for arm in ("B6", "Mstar"):
        N, X = dev.T(arm)["PD7_primary"]
        est, boot = A.rates(N, X, one)[0], rb(N, X)
        ev = np.flatnonzero(A.evaluable(N, dev.scenes, dev.log_idx))
        det[arm] = {"PD7_primary": {"_cells": (est, boot, ev, A.flag(est, boot, ev, 0.95)[3])}}
    abl = PC2.ablation_fails(det["B6"], det["Mstar"])
    t["H10"] = {"ablation_part": bool(abl), "ni_ub_0.975": r6["ub"], "holds": bool(abl and r6["ub"] <= 0.03)}
    if jt is not None:
        js = {}
        for arm, tb in jt.items():
            rr = {}
            for p in C.POPS:
                N, X = tb[p]
                est, boot = A.rates(N, X, one)[0], rb(N, X)
                lb95, ub95, _, s95, _ = A.flag(est, boot, np.array([0]), 0.95)
                lbr, _, _, sr, _ = A.flag(est, boot, np.array([0]), REMOVE_J)
                rr[C.LAB[p]] = {"E": float(est[0]), "evaluable": bool(A.evaluable(N, dev.scenes, dev.log_idx)[0]), "flag95": bool(s95[0]),
                                "lb_removal": float(lbr[0]), "removed": bool(sr[0]), "ub_at_L": float(A.flag(est, boot, np.array([0]), L_HK1C)[1][0])}
            js[arm] = rr
        m = "MstarJx"
        validJ = all(js[m][l]["evaluable"] and not js[m][l]["flag95"] and js[m][l]["ub_at_L"] <= DELTA + 0.03 for l in POPL)
        KJ = [c for c in CA2.KJ_SET if c in js]
        VJ = [c for c in KJ if not any(js[c][l]["removed"] for l in POPL)]
        pc = {c: pr(jrate, m, c, 0.5) for c in VJ}
        pH3 = min(1.0, 2 * len(VJ) * max(v["p_lt0"] for v in pc.values())) if VJ else 1.0
        t["H3"] = {"ValidJ_MstarJx": bool(validJ), "V_J": VJ, "missing": [c for c in CA2.KJ_SET if c not in js],
                   "p_c": {c: v["p_lt0"] for c, v in pc.items()}, "p_H3_doubled": pH3,
                   "passes_at": {"%.5f" % al: bool(validJ and VJ and pH3 <= al) for al in HOLM},
                   "ub_at_holm_level": {"%.5f" % al: {c: float(np.quantile(v["_bm"], 1 - al / (2 * len(VJ)))) for c, v in pc.items()} for al in HOLM} if VJ else {},
                   "joint": js}
        t["H3"]["bound_vs_p_agree"] = {k: bool(all(u < 0 for u in v.values()) == t["H3"]["passes_at"][k] or not validJ)
                                       for k, v in t["H3"]["ub_at_holm_level"].items()}
    return t


def part_c3():
    out = {"B": B3, "levels": {"flag_Mstar": FLAG_M, "HK1c_L": L_HK1C, "removal_each": REMOVE, "formB_alpha": SUPER,
                               "H3_removal_each": REMOVE_J, "formC_H10": LEVEL_C, "holm_levels": HOLM}, "trackers": {}}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        Wl = weights_log(dev, [20261401, dev.i, 0])
        # the log-sum estimators used by E3 must equal the reused ones on these weights
        G = G_of(dev)
        N, X = dev.T("B6")["PD7_primary"]
        assert np.allclose(rates_log(N, X, Wl, G), A.rates(N, X, Wl[:, dev.log_idx]), rtol=1e-12, atol=1e-14, equal_nan=True)
        pa = CA2.paired(dev.rate, Wl[:, dev.log_idx], "Mstar", "B3", 0.99)
        pb = paired_log(dev.rate, Wl, G, "Mstar", "B3", 0.99)
        assert abs(pa["ub"] - pb["ub"]) < 1e-12 and abs(pa["p_lt0"] - pb["p_lt0"]) < 1e-12
        fams = families(tag)
        jt, jrate = R2.joint_tables(tag)
        t = verdict(dev, Wl, fams, jt, jrate, fast=False)
        t["families_used"] = {"%s|%s" % k: (None if v is None else {"size": v["family_size"], "share": v["record_share"],
                                                                     "source": "v03 CP3" if isinstance(v.get("weights"), str) else "v02 CP"})
                              for k, v in fams.items() if v is not None}
        t["seed"] = [20261401, dev.i, 0]
        out["trackers"][tag] = t
        print("C3", tag, "Valid", t["arms"]["Mstar"]["valid"], "V_t", t["V_t"], "FormB", t["formB"], "H3", t["H3"]["V_J"], t["H3"]["p_H3_doubled"], flush=True)
    C.jdump(os.path.join(OUT3, "C3_verdict_rstar2_v03.json"), out)


def part_e3(s_from, s_to):
    d = ck("E3")
    for tag in C.TAGS:
        dev = C.Dev(tag)
        fams = families(tag)
        jt, jrate = R2.joint_tables(tag)
        for s in range(s_from, s_to + 1):
            path = os.path.join(d, "E3_%s_s%03d.json" % (tag, s))
            if os.path.exists(path):
                continue
            t0 = time.time()
            Wl = weights_log(dev, [20261402, dev.i, s])
            t = verdict(dev, Wl, fams, jt, jrate, fast=True)
            slim = {"valid": t["arms"]["Mstar"]["valid"], "V_t": t["V_t"], "formB_ub": t["formB"]["ub"], "formB_met": t["formB"]["met"],
                    "formC_ub": t["formC"]["ub_0.975"], "H10_ni_ub": t["H10"]["ni_ub_0.975"], "H10": t["H10"]["holds"],
                    "hk1c_ub": {l: t["arms"]["Mstar"]["pops"][l]["pooled_ub_at_L"] for l in POPL},
                    "Mstar_cell_flags": {l: t["arms"]["Mstar"]["pops"][l]["cell_flags"] for l in POPL},
                    "removed_by": {c: t["arms"][c]["removed_by"] for c in C.COMPS},
                    "max_t_minus_q": {c: {l: t["arms"][c]["pops"][l].get("max_t_minus_q") for l in POPL} for c in C.COMPS},
                    "V_J": t["H3"]["V_J"], "p_H3": t["H3"]["p_H3_doubled"], "H3_passes": t["H3"]["passes_at"],
                    "H3_ub_0.0125": t["H3"]["ub_at_holm_level"].get("%.5f" % 0.0125),
                    "J_lb_removal": {c: {l: t["H3"]["joint"][c][l]["lb_removal"] for l in POPL} for c in t["H3"]["joint"]},
                    "seed": [20261402, dev.i, s], "seconds": time.time() - t0}
            C.jdump(path, slim)
            print("E3", tag, s, slim["V_t"], slim["V_J"], round(slim["seconds"], 1), "s", flush=True)


def part_a3(reps):
    d = ck("A3")
    for tag in C.TAGS:
        path = os.path.join(d, "A3_%s.json" % tag)
        if os.path.exists(path):
            continue
        t0 = time.time()
        dev = C.Dev(tag)
        cells = []
        for p in C.POPS:
            N, X = dev.T("Mstar")[p]
            Np, Xp = N.sum(1), X.sum(1)
            m = Np > 0
            r = Xp[m] / Np[m]
            cells.append((C.LAB[p], r, float(r.mean())))
        truth = np.array([c[2] for c in cells])
        n = R2.N_UNITS
        rng = np.random.default_rng([20261404, dev.i])
        rows = np.repeat(np.arange(B3), n) * n
        hit = np.zeros(len(cells))
        hit95 = np.zeros(len(cells))
        for _ in range(reps):
            V = np.stack([c[1][rng.integers(0, len(c[1]), n)] for c in cells])
            idx = rng.integers(0, n, B3 * n)
            cnt = np.bincount(rows + idx, minlength=B3 * n).reshape(B3, n).astype(float)
            est = V.mean(1)
            bt = (cnt @ V.T) / n
            se = np.std(bt, axis=0, ddof=1)
            ok = se > 0
            q005, q05 = np.quantile(bt, [1 - L_HK1C, 0.05], axis=0)
            hit += np.where(ok, 2 * est - q005, est) >= truth - 1e-15
            hit95 += np.where(ok, 2 * est - q05, est) >= truth - 1e-15
        r = {"tracker": tag, "B": B3, "reps": reps, "n_units": n, "seed": [20261404, dev.i],
             "cells": {c[0]: {"truth": c[2], "coverage_0.995": float(hit[j] / reps), "coverage_0.95": float(hit95[j] / reps)} for j, c in enumerate(cells)},
             "seconds": time.time() - t0}
        C.jdump(path, r)
        print("A3", tag, r["cells"], round(r["seconds"], 1), "s", flush=True)


# ------------------------------------------------------------------ D3: OC in checkpointed chunks
def part_d3(variants, chunks, reps_chunk, boot):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    import c1_power_counts_v03 as V3
    d = ck("D3")
    J = C.load_analysis()
    trk = {}
    for tag in C.TAGS:
        scenes, tab, F = PC2.load_tracker(tag, J["decide"][tag]["retune"]["arm_of_scene"])
        log_idx, logs = PC2.log_map(scenes)
        trk[tag] = {"scenes": scenes, "tab": tab, "F": F, "log_idx": log_idx, "c": 0.03, "lay": None}
    del J
    bad = R2.check_rstar_functions(trk)
    assert not bad, bad
    allv = ["plugin", "capped"]
    old = (R2.REMOVE_EACH, R2.SUPER_ALPHA, R2.RSTAR_L[0], PC2.B_OC, PC2.validity, PC2.forms)
    R2.REMOVE_EACH, R2.SUPER_ALPHA, R2.RSTAR_L[0], PC2.B_OC = REMOVE, SUPER, L_HK1C, boot
    PC2.validity, PC2.forms = R2.validity_rstar, R2.forms_rstar
    try:
        for var in variants:
            vi = allv.index(var)
            for ch in chunks:
                path = os.path.join(d, "D3_%s_c%02d.json" % (var, ch))
                if os.path.exists(path):
                    continue
                t0 = time.time()
                seed = [20261403, vi, ch]
                tk, caps = (V3.cap_mstar(trk, np.random.default_rng([20261403, vi, 7])) if var == "capped" else (trk, None))
                R2.SIDE.clear()
                res = PC2.run_oc(tk, "scene", False, 1.0, reps_chunk, np.random.default_rng(seed), R2.N_UNITS)
                na = len(PC2.ARMS)
                fam = {t: {lab: [R2.SIDE[(r_ * 2 + ti) * na][k] for r_ in range(reps_chunk)] for k, lab in enumerate(POPL)}
                       for ti, t in enumerate(C.TAGS)}
                res.update({"variant": var, "chunk": ch, "seed": seed, "boot": boot, "reps": reps_chunk, "caps": caps,
                            "Mstar_family_record": fam, "seconds": time.time() - t0})
                C.jdump(path, res)
                print("D3", var, ch, "P_H1", res["P_H1"], round(res["seconds"], 1), "s", flush=True)
    finally:
        R2.REMOVE_EACH, R2.SUPER_ALPHA, R2.RSTAR_L[0], PC2.B_OC, PC2.validity, PC2.forms = old


def main(argv=None):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=["CP3", "C3", "E3", "A3", "D3"])
    ap.add_argument("--tags", default="t1,t3")
    ap.add_argument("--s-from", type=int, default=1)
    ap.add_argument("--s-to", type=int, default=100)
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--variants", default="plugin,capped")
    ap.add_argument("--chunks", default="0-11")
    ap.add_argument("--reps-chunk", type=int, default=25)
    ap.add_argument("--boot", type=int, default=B3)
    a = ap.parse_args(argv)
    os.makedirs(OUT3, exist_ok=True)
    t0 = time.time()
    if a.part == "CP3":
        part_cp3(a.tags.split(","))
    elif a.part == "C3":
        part_c3()
    elif a.part == "E3":
        part_e3(a.s_from, a.s_to)
    elif a.part == "A3":
        part_a3(a.reps)
    elif a.part == "D3":
        lo, hi = (int(x) for x in a.chunks.split("-"))
        part_d3(a.variants.split(","), list(range(lo, hi + 1)), a.reps_chunk, a.boot)
    print("PART %s DONE" % a.part, round(time.time() - t0, 1), "s", flush=True)


if __name__ == "__main__":
    main()
