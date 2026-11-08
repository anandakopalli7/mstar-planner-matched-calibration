#!/usr/bin/env python3
"""c1crit_rstar_v02 (5 Nov 2026): the lead's final check of rule set R* (computations A to E), on nuScenes K8 development data
ONLY (the K8 Linux replicate and its v03 analysis; the K8 joint run for H3). No Argoverse 2 file of any kind is read. Outputs go to
60_RESULTS/c1_criteria_sensitivity_v02/ only; v01's files are read (the development caches), never written.

R* (as the lead stated it):
  1 power: P 0.15, rho 0.5, power >= 0.80, 2000 datasets, 500 weights, TARGET-ONLY planting with every other cell planted at
    exactly delta (beta-binomial, same rho), outcome-free (power_target_delta below; v01's power_target used M*'s estimates);
  2 F_MIN 6 on PD7 and SD1_7, PD >= 1 evaluable cell; evaluable >= 39 units (unchanged);
  3 flags against M* (cell, family, pooled LB): one-sided 0.95 sup-t (unchanged);
  4 comparator removal: each of the 9 conditions at one-sided 1 - 0.025 / 9;
  5 Form B superiority: UB^{1 - 0.025 / |V_t|}(Delta_t(c)) < 0;
  6 HK1c: pooled UB at the calibrated level L <= delta + 0.03 (L from part A by the lead's rule);
  7 H3: V^J removal at 1 - 0.025 / 3 per pooled condition; superiority at 1 - 0.025 / |V^J|; ValidJ's UB at L;
  8 Form C and H10's NI part: UB^{0.975}.
Reused code (imported, unchanged): k6_analyse_v02 (rates, flag, evaluable, power_family), m_lib_v04._simul, k8_analyse_v03.hk1_rule
(for the 0.95 parts), k8_analyse_v04 (dec_rows, v2_tables: the joint loss), c1_power_counts_v02 (load_tracker, run_oc, validity,
forms, ablation_fails), c1_power_counts_v03.cap_mstar, c1_analyse_v02.paired, and c1crit_common_v01 / c1crit_power2_v01 (v01, read
only). New code: power_target_delta, the R* status, and validity_rstar / forms_rstar for the OC (each asserted to reproduce the
coded v02 function at the old levels before use).
Parts (each checkpointed in 60_RESULTS/c1_criteria_sensitivity_v02/<part>_ckpt/):
  A  coverage of the coded pooled UB at 375 units, levels 0.95 / 0.975 / 0.99 / 0.995, every arm's pooled cell per population and
     tracker (all 30 decision-mode arms); rule 6 -> L. Seeds [20261301, i, 375].
  B  coverage of the paired percentile UB at 375 units (levels 0.975, 0.9875) of Delta = f_M* - f_c, truth = the 840-scene mean.
     Seeds [20261302, i, arm index].
  CP R*'s power families (target-only, others at delta) for the arms in --arms. Seeds [20261303, i, arm index, k].
  C  the development verdict under R*.
  D  the OC at 375 units under R* (c1_power_counts_v02.run_oc with validity / forms replaced by the R* versions; analytic family).
     Seeds [20261304, variant index].
  E  the Monte Carlo SE of Form B's bound (B = 2000) at 1 - 0.025 / |V_t|: 500 independent log-bootstrap seed sets
     [20261305, i, s], and the Andrews-Buchinsky (2000) order-statistic formula.
Usage: python -B c1crit_rstar_v02.py <part> [options]
"""
import argparse
import json
import math
import os
import sys
import time
import warnings

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A, K8, PC2, CA2 = C.A, C.K8, C.PC2, C.CA2
M = A.M
OUT2 = os.path.join(C.W_ROOT, "60_RESULTS", "c1_criteria_sensitivity_v02")
CACHE2 = os.path.join(OUT2, "cache")
DELTA = C.DELTA
FLAG_M = 0.95
REMOVE_EACH = 1 - 0.025 / 9
REMOVE_J = 1 - 0.025 / 3
SUPER_ALPHA = 0.025
LEVEL_C = 0.975
LEVELS_A = (0.95, 0.975, 0.99, 0.995)
BRADLEY_A = 0.9625
N_UNITS = 375
P_RSTAR, RHO_RSTAR, REPS_RSTAR, NW_RSTAR = 0.15, 0.5, 2000, 500
INV = {v: k for k, v in C.LAB.items()}
JOINT_RUNS = os.path.join(C.W_ROOT, "70_TESTS", "k8_joint_v01_linux", "full_v02fits", "runs")


def ck(part):
    d = os.path.join(OUT2, part + "_ckpt")
    os.makedirs(d, exist_ok=True)
    return d


def done(path):
    return os.path.exists(path)


# ================================================================== A: pooled-UB coverage at 375 units
def all_arm_pooled(tag):
    """Per arm (every decision-mode arm but LOG, plus RETUNED) and population: the per-scene pooled records and exceedances, from
    c1_power_counts_v02.load_tracker with its ARMS list widened in this process (restored after)."""
    path = os.path.join(CACHE2, "pooled_all_arms_%s_v02.npz" % tag)
    if done(path):
        z = np.load(path)
        return list(z["arms"]), {p: (z["N_" + C.LAB[p]], z["X_" + C.LAB[p]]) for p in C.POPS}
    J = C.load_analysis()
    arms = [a for a in K8.S.ARMS if a != "LOG"] + ["RETUNED"]
    old = PC2.ARMS
    try:
        PC2.ARMS = arms
        scenes, tab, _F = PC2.load_tracker(tag, J["decide"][tag]["retune"]["arm_of_scene"])
    finally:
        PC2.ARMS = old
    del _F
    dev = C.Dev(tag)
    assert list(scenes) == list(dev.scenes)
    out = {}
    arrs = {"arms": np.array(arms)}
    for p in C.POPS:
        N, X = tab[p][0].sum(2), tab[p][1].sum(2)              # arm x scene
        for a in C.ARMS:                                        # the cache's 8 arms must agree
            assert np.array_equal(N[arms.index(a)], dev.N[p][C.ARMS.index(a)].sum(1))
            assert np.array_equal(X[arms.index(a)], dev.X[p][C.ARMS.index(a)].sum(1))
        out[p] = (N, X)
        arrs["N_" + C.LAB[p]], arrs["X_" + C.LAB[p]] = N, X
    np.savez_compressed(path, **arrs)
    return arms, out


def part_a(reps, boot):
    d = ck("A")
    for tag in C.TAGS:
        path = os.path.join(d, "A_%s.json" % tag)
        if done(path):
            print("skip (checkpoint)", path, flush=True)
            continue
        t0 = time.time()
        i = C.TIDX[tag]
        arms, tab = all_arm_pooled(tag)
        cells = []
        for p in C.POPS:
            N, X = tab[p]
            for k, a in enumerate(arms):
                m = N[k] > 0
                r = X[k][m] / N[k][m]
                if m.sum() >= 39:
                    cells.append((a, C.LAB[p], r, float(r.mean()), int(m.sum())))
        nc = len(cells)
        truth = np.array([c[3] for c in cells])
        rng = np.random.default_rng([20261301, i, N_UNITS])
        n = N_UNITS
        rows = np.repeat(np.arange(boot), n) * n
        cov = {L: np.zeros(nc) for L in LEVELS_A}
        zse = np.zeros(nc)
        for _ in range(reps):
            V = np.empty((nc, n))
            for c in range(nc):
                rr = cells[c][2]
                V[c] = rr[rng.integers(0, len(rr), n)]
            idx = rng.integers(0, n, boot * n)
            cnt = np.bincount(rows + idx, minlength=boot * n).reshape(boot, n).astype(float)
            est = V.mean(1)
            bt = (cnt @ V.T) / n
            se = np.std(bt, axis=0, ddof=1)
            ok = se > 0
            qs = np.quantile(bt, [1 - L for L in LEVELS_A], axis=0)
            for li, L in enumerate(LEVELS_A):
                ub = np.where(ok, 2 * est - qs[li], est)                   # the coded (A.flag 'upper') bound of one cell
                cov[L] += ub >= truth - 1e-15
            zse += ~ok
        res = {"tracker": tag, "n_units": n, "reps": reps, "boot": boot, "seed": [20261301, i, N_UNITS],
               "cells": [{"arm": c[0], "pop": c[1], "truth": c[3], "scenes": c[4],
                          "coverage": {str(L): float(cov[L][j] / reps) for L in LEVELS_A}, "zero_se": float(zse[j] / reps)}
                         for j, c in enumerate(cells)], "seconds": time.time() - t0}
        C.jdump(path, res)
        print("A", tag, nc, "cells", round(res["seconds"], 1), "s", flush=True)
    # rule 6
    rows = []
    for tag in C.TAGS:
        with open(os.path.join(d, "A_%s.json" % tag)) as f:
            rows += [dict(c, tracker=tag) for c in json.load(f)["cells"]]
    summ = {}
    for band, lo, hi in (("0.02-0.10", 0.02, 0.10), ("0.06-0.10", 0.06, 0.10)):
        for subset, arms in (("all_arms", None), ("formB_arms", set(C.ARMS))):
            for tag in C.TAGS:
                for lab in ("PD7", "SD1_7", "PD"):
                    sel = [c for c in rows if c["tracker"] == tag and c["pop"] == lab and lo <= c["truth"] < hi
                           and (arms is None or c["arm"] in arms)]
                    key = "%s|%s|%s|%s" % (band, subset, tag, lab)
                    summ[key] = {"cells": len(sel), "arms": [c["arm"] for c in sel],
                                 "mean": {str(L): (float(np.mean([c["coverage"][str(L)] for c in sel])) if sel else None) for L in LEVELS_A},
                                 "min": {str(L): (float(np.min([c["coverage"][str(L)] for c in sel])) if sel else None) for L in LEVELS_A}}

    def choose(stat, subset):
        for L in (0.975, 0.99, 0.995):
            vals = [summ["0.02-0.10|%s|%s|%s" % (subset, t, p)][stat][str(L)] for t in C.TAGS for p in ("PD7", "SD1_7", "PD")]
            if all(v is not None and v >= BRADLEY_A for v in vals):
                return L, True
        return 0.995, False
    rule = {}
    for stat in ("mean", "min"):
        for subset in ("all_arms", "formB_arms"):
            L, met = choose(stat, subset)
            rule["%s|%s" % (stat, subset)] = {"L": L, "criterion_met": met}
    out = {"summary": summ, "rule6": rule, "rule6_primary": "mean over the cells in the band, all arms (each of 3 populations x 2 trackers)",
           "L": rule["mean|all_arms"]["L"], "bradley_threshold": BRADLEY_A}
    C.jdump(os.path.join(OUT2, "A_hk1c_level_v02.json"), out)
    print("A rule 6:", rule, flush=True)
    return out


# ================================================================== B: paired-difference UB coverage at 375 units
B_COMPS = {"t1": ("B3", "B4", "B6"), "t3": ("B0", "B3", "B4", "B6")}


def part_b(reps, boot):
    d = ck("B")
    out = {}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        i = dev.i
        for c in B_COMPS[tag]:
            path = os.path.join(d, "B_%s_%s.json" % (tag, c))
            if done(path):
                with open(path) as f:
                    out["%s|%s" % (tag, c)] = json.load(f)
                continue
            t0 = time.time()
            dvec = dev.rate["Mstar"] - dev.rate[c]
            truth = float(dvec.mean())
            seed = [20261302, i, C.ARMS.index(c)]
            rng = np.random.default_rng(seed)
            n = N_UNITS
            rows = np.repeat(np.arange(boot), n) * n
            hits = {0.975: 0, 0.9875: 0}
            ubs = {0.975: [], 0.9875: []}
            for _ in range(reps):
                v = dvec[rng.integers(0, len(dvec), n)]
                idx = rng.integers(0, n, boot * n)
                cnt = np.bincount(rows + idx, minlength=boot * n).reshape(boot, n).astype(float)
                bm = (cnt @ v) / n
                for L in hits:
                    u = float(np.quantile(bm, L))
                    hits[L] += u >= truth - 1e-15
                    ubs[L].append(u)
            r = {"tracker": tag, "comparator": c, "truth": truth, "reps": reps, "boot": boot, "seed": seed, "n_units": n,
                 "coverage": {str(L): hits[L] / reps for L in hits}, "mean_ub": {str(L): float(np.mean(ubs[L])) for L in hits},
                 "share_ub_below_0": {str(L): float(np.mean(np.array(ubs[L]) < 0)) for L in hits}, "seconds": time.time() - t0}
            C.jdump(path, r)
            out["%s|%s" % (tag, c)] = r
            print("B", tag, c, r["coverage"], round(r["seconds"], 1), "s", flush=True)
    C.jdump(os.path.join(OUT2, "B_paired_coverage_v02.json"), out)
    return out


# ================================================================== CP: R*'s power families
def power_target_delta(N, ev, W, rng, P, rho, reps):
    """Target-only planting with every other cell at exactly delta (R* item 1): per dataset every cell with records is drawn from
    Beta(mean delta, ICC rho) per scene and Binomial(n, .); then for each evaluable cell j in turn only cell j is redrawn at P,
    and j counts if it is flagged in the all-evaluable one-sided sup-t at 0.95 (m_lib_v04._simul; zero SE flags iff E > delta)."""
    fam = np.flatnonzero(ev)
    S_, J = N.shape
    th = (1 - rho) / rho
    hits = np.zeros(J)
    Ni = N.astype(int)
    pres = (N > 0).astype(float)
    one = np.ones((1, S_))
    den_one, den_W = one @ pres, W @ pres
    for _ in range(reps):
        Pb = rng.beta(DELTA * th, (1 - DELTA) * th, size=(S_, J))
        Xb = rng.binomial(Ni, Pb).astype(float)
        pb = np.divide(Xb, N, out=np.zeros_like(Xb), where=N > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            est_b = ((one @ pb) / den_one)[0][fam]
            boot_b = ((W @ pb) / den_W)[:, fam]
        Pt = rng.beta(P * th, (1 - P) * th, size=(S_, len(fam)))
        Nf = N[:, fam]
        Xt = rng.binomial(Ni[:, fam], Pt).astype(float)
        pt = np.divide(Xt, Nf, out=np.zeros_like(Xt), where=Nf > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            est_t = ((one @ pt) / den_one[:, fam])[0]
            boot_t = (W @ pt) / den_W[:, fam]
        for ii in range(len(fam)):
            e = est_b.copy()
            b = boot_b.copy()
            e[ii], b[:, ii] = est_t[ii], boot_t[:, ii]
            lb, se, q, ok = M._simul(e, b, 0.95, "lower")
            hits[fam[ii]] += bool((ok[ii] and lb[ii] > DELTA) or ((not ok[ii]) and e[ii] > DELTA))
    return hits / reps


def part_cp(arms, tags, reps, P=P_RSTAR, rho=RHO_RSTAR):
    d = ck("CP")
    for tag in tags:
        dev = C.Dev(tag)
        W, _ = dev.weights()
        for arm in arms:
            for lab in ("PD7", "SD1_7", "PD"):
                path = os.path.join(d, "CP_%s_%s_%s_P%.3f_r%d.json" % (tag, arm, lab, P, reps))
                if done(path):
                    print("skip (checkpoint)", path, flush=True)
                    continue
                t0 = time.time()
                p = INV[lab]
                N = dev.N[p][C.ARMS.index(arm)]
                ev = A.evaluable(N, dev.scenes, dev.log_idx)
                k = ("PD7", "SD1_7", "PD").index(lab)
                seed = [20261303, dev.i, C.ARMS.index(arm), k] + ([] if P == P_RSTAR else [int(round(P * 1000))])
                pw = power_target_delta(N, ev, W[:NW_RSTAR], np.random.default_rng(seed), P, rho, reps)
                qual = ev & (pw >= 0.80)
                rec = N.sum(0)
                r = {"tracker": tag, "arm": arm, "pop": lab, "P": P, "rho": rho, "reps": reps, "weights": NW_RSTAR, "seed": seed,
                     "power": {C.CELL_NAMES[j]: float(pw[j]) for j in np.flatnonzero(ev)},
                     "family": [C.CELL_NAMES[j] for j in np.flatnonzero(qual)], "family_size": int(qual.sum()),
                     "record_share": float(rec[qual].sum() / rec.sum()), "evaluable": int(ev.sum()), "seconds": time.time() - t0}
                C.jdump(path, r)
                print("CP", tag, arm, lab, r["family_size"], round(r["record_share"], 3), round(r["seconds"], 1), "s", flush=True)


# ================================================================== C: the development verdict under R*
def flags_at(N, X, scenes, log_idx, W, fam_names, level):
    """Every R* condition of one arm in one population at one level: all-evaluable cell flags, flags of a given family, pooled."""
    one = np.ones((1, N.shape[0]))
    ev = np.flatnonzero(A.evaluable(N, scenes, log_idx))
    est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
    out = {"evaluable": int(len(ev)), "cell_flags": [], "family_flags": None, "pooled": None}
    if len(ev):
        sig = A.flag(est, boot, ev, level)[3]
        out["cell_flags"] = [C.CELL_NAMES[ev[i]] for i in np.flatnonzero(sig)]
    if fam_names is not None:
        fam = np.array([C.CELL_NAMES.index(c) for c in fam_names], int)
        out["family_flags"] = [C.CELL_NAMES[fam[i]] for i in np.flatnonzero(A.flag(est, boot, fam, level)[3])] if len(fam) else []
    Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
    if A.evaluable(Np, scenes, log_idx)[0]:
        e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
        lb, ub, se, sig, q = A.flag(e1, b1, np.array([0]), level)
        out["pooled"] = {"E": float(e1[0]), "lb": float(lb[0]), "flagged": bool(sig[0])}
    return out


def pooled_ub(N, X, W, level):
    one = np.ones((1, N.shape[0]))
    Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
    e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
    return float(A.flag(e1, b1, np.array([0]), level)[1][0]), float(e1[0])


def cp_family(tag, arm, lab):
    path = os.path.join(OUT2, "CP_ckpt", "CP_%s_%s_%s_P%.3f_r%d.json" % (tag, arm, lab, P_RSTAR, REPS_RSTAR))
    if not done(path):
        return None
    with open(path) as f:
        return json.load(f)


def joint_tables(tag):
    """Per arm of the K8 joint run: the scene x 1 V2 tables (N, X) of PD7, SD1_7, PD (k8_analyse_v04.v2_tables) and the per-scene
    infeasible rate; scenes in K8's order (asserted equal to the development scenes)."""
    import k8_analyse_v04 as K4
    eps = []
    with open(os.path.join(JOINT_RUNS, "episodes_%s_decide.jsonl" % tag)) as f:
        for line in f:
            o = json.loads(line)
            if o.get("entered") and o["scene"] not in K4.DEV_SCENES and o["arm"] != "LOG":
                eps.append(o)
    dev = C.Dev(tag)
    keys = sorted({(o["scene"], o["delay_kf"]) for o in eps})
    assert [k[0] for k in keys] == list(dev.scenes)
    kidx = {k: i for i, k in enumerate(keys)}
    z = np.load(os.path.join(JOINT_RUNS, "decisions_%s_decide.npz" % tag), allow_pickle=False)
    D = {k: z[k] for k in z.files}
    rows = K4.dec_rows(D, eps, kidx)
    tabs, rate = {}, {}
    inf = {(o["scene"], o["arm"]): o["infeasible_frames"] / max(o["frames"], 1) for o in eps}
    for a, (r, kix) in rows.items():
        tabs[a] = {}
        for p in C.POPS:
            c4, obs = K4.V2_DECIDE[p]
            N, X, _, _ = K4.v2_tables(r, kix, len(keys), c4, obs)
            tabs[a][p] = (N, X)
        rate[a] = np.array([inf[(s, a)] for s in dev.scenes])
    return tabs, rate


def part_c(L):
    out = {"L": L, "levels": {"flag_against_Mstar": FLAG_M, "removal_each": REMOVE_EACH, "superiority_alpha": SUPER_ALPHA,
                              "form_C_H10": LEVEL_C, "H3_removal_each": REMOVE_J}, "trackers": {}}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        W, _ = dev.weights()
        t = {"arms": {}}
        status = {}
        for arm in C.ARMS:
            a = {"pops": {}}
            removed = []
            for p in C.POPS:
                lab = C.LAB[p]
                N, X = dev.T(arm)[p]
                fam = cp_family(tag, arm, lab)
                fam_names = None if fam is None else fam["family"]
                if arm == "Mstar":
                    fl = flags_at(N, X, dev.scenes, dev.log_idx, W, fam_names, FLAG_M)
                    ub, e = pooled_ub(N, X, W, L)
                    fl.update({"pooled_ub_at_L": ub, "HK1c": bool(ub <= DELTA + 0.03),
                               "family_size": None if fam is None else fam["family_size"],
                               "record_share": None if fam is None else fam["record_share"],
                               "floor": (None if fam is None else fam["family_size"] >= 6) if lab != "PD" else fl["evaluable"] >= 1})
                    fl["ok"] = bool(not fl["cell_flags"] and not (fl["family_flags"] or []) and fl["pooled"] is not None
                                    and not fl["pooled"]["flagged"] and fl["floor"] and fl["HK1c"])
                else:
                    fl = flags_at(N, X, dev.scenes, dev.log_idx, W, fam_names, REMOVE_EACH)
                    fl.update({"family_size": None if fam is None else fam["family_size"]})
                    if fl["cell_flags"]:
                        removed.append("%s: cell flag at 1-0.025/9 (%s)" % (lab, ", ".join(fl["cell_flags"])))
                    if fl["family_flags"]:
                        removed.append("%s: family flag at 1-0.025/9 (%s)" % (lab, ", ".join(fl["family_flags"])))
                    if fl["pooled"] is not None and fl["pooled"]["flagged"]:
                        removed.append("%s: pooled LB at 1-0.025/9 > delta" % lab)
                a["pops"][lab] = fl
            if arm == "Mstar":
                a["valid"] = bool(all(a["pops"][l]["ok"] for l in ("PD7", "SD1_7", "PD")))
                status[arm] = a["valid"]
            else:
                a["removed"] = bool(removed)
                a["removed_by"] = removed
                a["family_computed_all_pops"] = all(a["pops"][l]["family_size"] is not None for l in ("PD7", "SD1_7", "PD"))
                status[arm] = a["removed"]
            t["arms"][arm] = a
        V = [c for c in C.COMPS if not t["arms"][c]["removed"]]
        lvl = 1 - SUPER_ALPHA / max(len(V), 1)
        fb = {c: CA2.paired(dev.rate, W, "Mstar", c, lvl) for c in V}
        t["V_t"] = V
        t["formB"] = {"level": lvl, "ub": {c: v["ub"] for c, v in fb.items()},
                      "met": bool(t["arms"]["Mstar"]["valid"] and all(v["ub"] < 0 for v in fb.values())), "vacuous": not V}
        fa = {c: CA2.paired(dev.rate, W, "Mstar", c, 1 - 0.05 / 4)["ub"] for c in ("B0", "B1", "B4", "B9")}
        fa25 = {c: CA2.paired(dev.rate, W, "Mstar", c, 1 - 0.025 / 4)["ub"] for c in ("B0", "B1", "B4", "B9")}
        t["formA_descriptive"] = {"ub_at_1-0.05/4": fa, "met": bool(t["arms"]["Mstar"]["valid"] and all(u < 0 for u in fa.values())),
                                  "ub_at_1-0.025/4": fa25, "met_at_0.025": bool(t["arms"]["Mstar"]["valid"] and all(u < 0 for u in fa25.values()))}
        rc = CA2.paired(dev.rate, W, "Mstar", "B4", LEVEL_C)
        t["formC"] = {"ub_0.975": rc["ub"], "mean_diff": rc["mean_diff"], "met": bool(rc["ub"] <= 0.03)}
        r6 = CA2.paired(dev.rate, W, "Mstar", "B6", LEVEL_C)
        # H10's ablation part (unchanged levels: B6 flagged at 0.95, M* not, paired sup-t LB > 0), via c1_power_counts_v02.ablation_fails
        det = {}
        for arm in ("B6", "Mstar"):
            N, X = dev.T(arm)["PD7_primary"]
            one = np.ones((1, N.shape[0]))
            est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
            ev = np.flatnonzero(A.evaluable(N, dev.scenes, dev.log_idx))
            det[arm] = {"PD7_primary": {"_cells": (est, boot, ev, A.flag(est, boot, ev, 0.95)[3])}}
        abl = PC2.ablation_fails(det["B6"], det["Mstar"])
        t["H10"] = {"ablation_part": bool(abl), "ni_ub_0.975": r6["ub"], "ni_met": bool(r6["ub"] <= 0.03), "holds": bool(abl and r6["ub"] <= 0.03)}
        # H3 on the K8 joint run
        try:
            jt, jrate = joint_tables(tag)
            jstat = {}
            for arm, tb in jt.items():
                rr = {}
                for p in C.POPS:
                    N, X = tb[p]
                    one = np.ones((1, N.shape[0]))
                    est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
                    ev = bool(A.evaluable(N, dev.scenes, dev.log_idx)[0])
                    lb95, ub95, _, sig95, _ = A.flag(est, boot, np.array([0]), 0.95)
                    lbr, _, _, sigr, _ = A.flag(est, boot, np.array([0]), REMOVE_J)
                    ubL = float(A.flag(est, boot, np.array([0]), L)[1][0])
                    rr[C.LAB[p]] = {"E": float(est[0]), "evaluable": ev, "lb95": float(lb95[0]), "ub95": float(ub95[0]),
                                    "flag95": bool(sig95[0]), "lb_removal": float(lbr[0]), "removed_flag": bool(sigr[0]), "ub_at_L": ubL}
                jstat[arm] = rr
            KJ = [c for c in CA2.KJ_SET if c in jstat]
            m = "MstarJx"
            validJ = all(jstat[m][l]["evaluable"] and not jstat[m][l]["flag95"] and jstat[m][l]["ub_at_L"] <= DELTA + 0.03 for l in ("PD7", "SD1_7", "PD"))
            VJ = [c for c in KJ if not any(jstat[c][l]["removed_flag"] for l in ("PD7", "SD1_7", "PD"))]
            lvlJ = 1 - SUPER_ALPHA / max(len(VJ), 1)
            sup = {c: CA2.paired(jrate, W, m, c, lvlJ)["ub"] for c in VJ}
            t["H3"] = {"ValidJ_MstarJx": bool(validJ), "V_J": VJ, "missing": [c for c in CA2.KJ_SET if c not in jstat], "level": lvlJ,
                       "ub": sup, "holds": bool(validJ and all(u < 0 for u in sup.values())), "joint_status": jstat,
                       "reproduces_stored_0.95_bounds": None}
            # check against the stored joint analysis (0.95 bounds)
            with open(os.path.join(C.W_ROOT, "70_TESTS", "k8_joint_v01_linux", "full_v02fits", "k8_joint_analysis_v04.json")) as f:
                vb = json.load(f)["decide"][tag]["joint_loss"]["validity_by_arm"]
            diffs = [abs(vb[a]["pops"][INV[l]]["lb_one_sided_0.95"] - jstat[a][l]["lb95"]) for a in jstat for l in ("PD7", "SD1_7", "PD")
                     if a in vb and vb[a]["pops"][INV[l]].get("lb_one_sided_0.95") is not None]
            t["H3"]["reproduces_stored_0.95_bounds"] = bool(max(diffs) < 1e-9)
            t["H3"]["max_abs_diff_vs_stored"] = float(max(diffs))
        except Exception as ex:      # reported, never silent
            t["H3"] = {"error": "%s: %s" % (type(ex).__name__, ex)}
        out["trackers"][tag] = t
        print("C", tag, "Valid(M*)", t["arms"]["Mstar"]["valid"], "V_t", V, "Form B", t["formB"]["met"], "Form C", t["formC"]["met"],
              "H3", t["H3"].get("holds"), flush=True)
    C.jdump(os.path.join(OUT2, "C_verdict_rstar_v02.json"), out)
    return out


# ================================================================== D: OC at 375 units under R*
_VALIDITY_V02 = PC2.validity
_FORMS_V02 = PC2.forms
SIDE = []                      # (family size, record share) of every validity call, in run_oc's call order


def validity_rstar(T, W, ev_fn, levels=None):
    """c1_power_counts_v02.validity with R*'s levels: M*'s flags at FLAG_M (0.95), the HK1c upper bound at L, and the comparators'
    'shown' (removal) at REMOVE_EACH; 'strict' (validity) keeps 0.95 flags and the floor, as in R*. levels = (flag, hk1c, remove)."""
    lf, lh, lr = levels or (FLAG_M, RSTAR_L[0], REMOVE_EACH)
    U = W.shape[1]
    one = np.ones((1, U))
    strict, shown, nofloor = True, False, True
    det = {}
    fams = []
    for p in PC2.CONF_POPS:
        N, X = T[p]
        ev = ev_fn(N)
        fam = np.flatnonzero(ev)
        est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
        nfl, nfl_r = 0, 0
        sig = np.zeros(0, bool)
        if len(fam):
            _, _, _, sig, _ = A.flag(est, boot, fam, lf)
            nfl = int(sig.sum())
            nfl_r = nfl if lr == lf else int(A.flag(est, boot, fam, lr)[3].sum())
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        evp = bool(ev_fn(Np)[0])
        pfl, pfl_r, hk1c = False, False, False
        if evp:
            e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
            _, _, _, sigp, _ = A.flag(e1, b1, np.array([0]), lf)
            pfl = bool(sigp[0])
            pfl_r = pfl if lr == lf else bool(A.flag(e1, b1, np.array([0]), lr)[3][0])
            hk1c = bool(A.flag(e1, b1, np.array([0]), lh)[1][0] <= DELTA + 0.03)
        fq = np.flatnonzero(PC2.power_family_analytic(N, ev))
        ffl, ffl_r = 0, 0
        if len(fq):
            _, _, _, sigf, _ = A.flag(est, boot, fq, lf)
            ffl = int(sigf.sum())
            ffl_r = ffl if lr == lf else int(A.flag(est, boot, fq, lr)[3].sum())
        floor_ok = (len(fq) >= PC2.F_MIN) if p in PC2.FLOOR_POPS else True
        a_ok = nfl == 0 and len(fam) >= 1 and floor_ok and ffl == 0
        strict &= a_ok and evp and not pfl and hk1c
        nofloor &= nfl == 0 and len(fam) >= 1 and ffl == 0 and evp and not pfl and hk1c
        shown |= nfl_r > 0 or ffl_r > 0 or pfl_r          # R* (and v07d): removal by a flag only, never by HK1c
        rec = N.sum(0)
        fams.append((len(fq), float(rec[fq].sum() / rec.sum()) if rec.sum() > 0 else None))
        det[p] = {"evaluable": int(len(fam)), "flagged": nfl, "family": int(len(fq)), "family_flagged": ffl,
                  "pooled_flagged": pfl, "hk1c": hk1c, "floor_ok": bool(floor_ok), "_cells": (est, boot, fam, sig)}
    det["_nofloor"] = bool(nofloor)
    SIDE.append(fams)
    return bool(strict), bool(shown), det


RSTAR_L = [0.975]


def forms_rstar(f, W, strict, shown, c_val):
    """c1_power_counts_v02.forms with R*'s levels: Form B at 1 - 0.025/|V|, Form C and H10's NI at 0.975 (Holm-worst variants at
    0.025/5). Keys as v02's, so run_oc aggregates them unchanged."""
    wsum = W.sum(1)

    def ub(b, level):
        dd = f[:, 0] - f[:, PC2.ARMS.index(b)]
        return float(dd.mean()), float(np.quantile((W @ dd) / wsum, level))
    V9 = [c for c in PC2.COMPS_B if not shown[c]]
    lvl = 1 - SUPER_ALPHA / max(len(V9), 1)
    beats9 = {c: ub(c, lvl)[1] < 0 for c in V9}
    formB9 = strict["Mstar"] and all(beats9.values())
    Vlit = [c for c in PC2.COMPS_B if strict[c]]
    lvl2 = 1 - SUPER_ALPHA / max(len(Vlit), 1)
    formBlit = strict["Mstar"] and all(ub(c, lvl2)[1] < 0 for c in Vlit)
    formA = strict["Mstar"] and all(ub(c, 1 - 0.05 / 4)[1] < 0 for c in PC2.COMPS_A)
    d4 = ub("B4", LEVEL_C)
    d6 = ub("B6", LEVEL_C)
    return {"formB": bool(formB9), "formB_literal": bool(formBlit), "formA": bool(formA), "formC": bool(d4[1] <= c_val),
            "formC_holm_worst": bool(ub("B4", 1 - 0.025 / 5)[1] <= c_val), "V": V9, "beats": beats9, "Mstar_minus_B4": d4[0],
            "Mstar_minus_B6": d6[0], "ni_B6_005": bool(d6[1] <= PC2.NI_B6), "ni_B6_holm": bool(ub("B6", 1 - 0.025 / 5)[1] <= PC2.NI_B6)}


def check_rstar_functions(trk):
    """validity_rstar at the old levels (0.95 everywhere, HK1c at 0.95, removal including HK1c is v07c's; we compare strict,
    the flag counts and floors, which are level-identical) and forms_rstar's arithmetic, on the 840 development scenes."""
    rng = np.random.default_rng([20261304, 99])
    bad = []
    for tag in C.TAGS:
        d = trk[tag]
        n = len(d["scenes"])
        Wl = rng.multinomial(n, np.full(n, 1.0 / n), size=200).astype(float)

        def ev_fn(N):
            return (N > 0).sum(0) >= PC2.MIN_UNITS
        for i, a in enumerate(PC2.ARMS):
            Ti = {p: (d["tab"][p][0][i], d["tab"][p][1][i]) for p in PC2.CONF_POPS}
            s0, sh0, d0 = _VALIDITY_V02(Ti, Wl, ev_fn)
            s1, sh1, d1 = validity_rstar(Ti, Wl, ev_fn, levels=(0.95, 0.95, 0.95))
            sh0_7d = any(d0[p]["flagged"] > 0 or d0[p]["family_flagged"] > 0 or d0[p]["pooled_flagged"] for p in PC2.CONF_POPS)
            if s0 != s1 or sh0_7d != sh1 or any(d0[p][k] != d1[p][k] for p in PC2.CONF_POPS
                                                 for k in ("evaluable", "flagged", "family", "family_flagged", "pooled_flagged", "hk1c", "floor_ok")):
                bad.append((tag, a))
    SIDE.clear()
    return bad


def part_d(reps, variants):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    import c1_power_counts_v03 as V3
    d = ck("D")
    J = C.load_analysis()
    trk = {}
    for tag in C.TAGS:
        scenes, tab, F = PC2.load_tracker(tag, J["decide"][tag]["retune"]["arm_of_scene"])
        log_idx, logs = PC2.log_map(scenes)
        trk[tag] = {"scenes": scenes, "tab": tab, "F": F, "log_idx": log_idx, "c": 0.03, "lay": None}
    del J
    bad = check_rstar_functions(trk)
    assert not bad, "validity_rstar does not reproduce c1_power_counts_v02.validity at the old levels: %s" % bad
    allv = ["plugin", "capped", "plugin_P0.12", "capped_P0.12"]
    for var in variants:
        path = os.path.join(d, "D_%s.json" % var)
        if done(path):
            print("skip (checkpoint)", path, flush=True)
            continue
        t0 = time.time()
        vi = allv.index(var)
        seed = [20261304, vi]
        rng = np.random.default_rng(seed)
        oldP = PC2.POWER_P
        PC2.validity, PC2.forms = validity_rstar, forms_rstar
        if "P0.12" in var:
            PC2.POWER_P = 0.12
        SIDE.clear()
        try:
            tk, caps = (V3.cap_mstar(trk, np.random.default_rng(seed + [7])) if var.startswith("capped") else (trk, None))
            res = PC2.run_oc(tk, "scene", False, 1.0, reps, rng, N_UNITS)
        finally:
            PC2.validity, PC2.forms, PC2.POWER_P = _VALIDITY_V02, _FORMS_V02, oldP
        # SIDE: per rep, t1 then t3, 8 arms each in PC2.ARMS order (M* first)
        na = len(PC2.ARMS)
        assert len(SIDE) == reps * 2 * na
        fam_m = {t: {lab: [] for lab in ("PD7", "SD1_7", "PD")} for t in C.TAGS}
        for r_ in range(reps):
            for ti, t in enumerate(C.TAGS):
                e = SIDE[(r_ * 2 + ti) * na]
                for k, lab in enumerate(("PD7", "SD1_7", "PD")):
                    fam_m[t][lab].append(e[k])
        cov = {}
        for t in C.TAGS:
            cov[t] = {}
            for lab in ("PD7", "SD1_7", "PD"):
                sz = np.array([x[0] for x in fam_m[t][lab]], float)
                sh = np.array([np.nan if x[1] is None else x[1] for x in fam_m[t][lab]], float)
                cov[t][lab] = {"family_median": float(np.median(sz)), "family_p10": float(np.quantile(sz, 0.1)),
                               "P_family_ge_6": float(np.mean(sz >= 6)), "record_share_median": float(np.nanmedian(sh)),
                               "record_share_p10": float(np.nanquantile(sh, 0.1))}
        res.update({"variant": var, "seed": seed, "caps": caps, "L": RSTAR_L[0], "P_power": 0.12 if "P0.12" in var else 0.15,
                    "P_H1_fails": 1.0 - res["P_H1"], "Mstar_family_and_record_share": cov, "seconds": time.time() - t0,
                    "power_family_note": "analytic (c1_power_counts_v02.power_family_analytic: per-cell normal power at P against the Sidak "
                                         "critical value of the evaluable family); the other cells' means do not enter it, so it stands for "
                                         "target-only planting with the others at delta, up to the analytic approximation (quantified in C)"})
        C.jdump(path, res)
        print("D", var, "P_H1", res["P_H1"], {t: res[t]["P_Mstar_failure_reason"] for t in C.TAGS}, round(res["seconds"], 1), "s", flush=True)


# ================================================================== E: MC SE of Form B's bound
def part_e(V_by_tag, nsets, boot):
    out = {}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        V = V_by_tag[tag]
        if not V:
            out[tag] = {"V_t": [], "note": "V_t empty: Form B part (ii) vacuous, no bound"}
            continue
        lvl = 1 - SUPER_ALPHA / len(V)
        _, Wl0 = dev.weights()
        res = {"V_t": V, "level": lvl, "sets": nsets, "B": boot, "seed": "[20261305, i, s], s = 0..%d" % (nsets - 1), "by_comparator": {}}
        for c in V:
            dvec = dev.rate["Mstar"] - dev.rate[c]
            Wd = Wl0[:, dev.log_idx]
            bm0 = (Wd @ dvec) / Wd.sum(1)
            u0 = float(np.quantile(bm0, lvl))
            us = []
            for s in range(nsets):
                rng = np.random.default_rng([20261305, dev.i, s])
                Wl = rng.multinomial(dev.n_logs, np.full(dev.n_logs, 1.0 / dev.n_logs), size=boot).astype(float)
                Ws = Wl[:, dev.log_idx]
                bm = (Ws @ dvec) / Ws.sum(1)
                us.append(float(np.quantile(bm, lvl)))
            us = np.array(us)
            # Andrews-Buchinsky: the bound is an order statistic; SE ~ sqrt(tau (1 - tau) / B) / f(q_tau), f by a Gaussian kernel
            sd = np.std(bm0, ddof=1)
            h = 1.06 * sd * boot ** (-0.2)
            f = float(np.mean(np.exp(-0.5 * ((bm0 - u0) / h) ** 2)) / (h * math.sqrt(2 * math.pi)))
            se_ab = math.sqrt(lvl * (1 - lvl) / boot) / f
            res["by_comparator"][c] = {"ub_k8_seed": u0, "mean_over_sets": float(us.mean()), "mc_se_over_sets": float(us.std(ddof=1)),
                                       "mc_se_andrews_buchinsky": se_ab, "distance_from_0": -u0,
                                       "distance_in_mc_se": float(-u0 / max(us.std(ddof=1), 1e-12)),
                                       "share_of_sets_with_ub_ge_0": float(np.mean(us >= 0)), "range_over_sets": [float(us.min()), float(us.max())]}
            print("E", tag, c, res["by_comparator"][c], flush=True)
        out[tag] = res
    C.jdump(os.path.join(OUT2, "E_formB_mc_v02.json"), out)
    return out


def main(argv=None):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("part", choices=["A", "B", "CP", "C", "D", "E"])
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--arms", default="Mstar")
    ap.add_argument("--tags", default="t1,t3")
    ap.add_argument("--L", type=float, default=None)
    ap.add_argument("--variants", default="plugin,capped,plugin_P0.12,capped_P0.12")
    ap.add_argument("--sets", type=int, default=500)
    a = ap.parse_args(argv)
    os.makedirs(OUT2, exist_ok=True)
    os.makedirs(CACHE2, exist_ok=True)
    t0 = time.time()
    if a.part in ("C", "D") and a.L is None:
        with open(os.path.join(OUT2, "A_hk1c_level_v02.json")) as f:
            a.L = json.load(f)["L"]
    if a.L is not None:
        RSTAR_L[0] = a.L
    if a.part == "A":
        part_a(a.reps, a.boot)
    elif a.part == "B":
        part_b(a.reps, a.boot)
    elif a.part == "CP":
        part_cp(a.arms.split(","), a.tags.split(","), a.reps)
    elif a.part == "C":
        part_c(a.L)
    elif a.part == "D":
        part_d(a.reps, a.variants.split(","))
    elif a.part == "E":
        with open(os.path.join(OUT2, "C_verdict_rstar_v02.json")) as f:
            cv = json.load(f)
        part_e({t: cv["trackers"][t]["V_t"] for t in C.TAGS}, a.sets, a.boot)
    print("PART %s DONE" % a.part, round(time.time() - t0, 1), "s", flush=True)


if __name__ == "__main__":
    main()
