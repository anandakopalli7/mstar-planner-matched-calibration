#!/usr/bin/env python3
"""c1crit_removal_v01 (5 Nov 2026): the lead's item 6 (C1_CRITERIA_EVIDENCE_REVIEW_v01 section 6 and 3.3; plan C9c):
P(removal from V_t) for a comparator whose true exceedance is exactly delta in every cell, across the nine removal conditions
(PD7, SD1_7, PD x {a flag in the all-evaluable family, a flag in the power-qualified family, the pooled lower bound > delta}),
at the comparator's own development record counts. nuScenes K8 development data only (T1, T3; 840 scenes, 68 logs).

The populations overlap (PD7 = SD1_7 + far, PD = in-path), so the records are split into the four quadrants (near/far x in-path
or not; k8_analyse_v03.CELLS4 index near * 2 + in-path) with c1_power_counts_v02.load_tracker on quadrant masks (k6_analyse_v02.mask,
the populations' own specification restricted by gap and in-path), and the quadrant sums are asserted equal to the PD7, SD1_7 and
PD tables. A planted dataset draws, per scene and cell, P ~ Beta(mean delta, intra-scene correlation rho) shared by the quadrants
(the power rule's model) and X ~ Bin(n, P) per quadrant; the three populations are the quadrant sums. The rule's flags are
k6_analyse_v02.flag with the K8 v03 bootstrap weights (B = 2000, [20261106, i, 0]); the evaluable cells come from the counts; the
power-qualified family is the comparator's development family (c1crit_sweep_v01 baseline: rho 0.5, P 0.15, 200 datasets).
Reported: each condition's rate, P(any of the nine) at the rule's per-condition 0.95, and at a familywise level over the nine
conditions (each at 1 - 0.05 / 9, Bonferroni; R20 / review option (ii)).
Seeds default_rng([20261211, i, arm index, round(10000 rho)]); R = --reps. Checkpoint: one JSON per (tracker, arm, rho) in
removal_ckpt/; the quadrant tables are cached in cache/dev_quadrants_<tag>_v01.npz.
Usage: python -B c1crit_removal_v01.py [--rhos 0.5,<rho_hat>] [--arms B0,B3,B4,B6,Mstar] [--reps 500]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A, PC2 = C.A, C.PC2
SEED = 20261211
CKPT = os.path.join(C.OUT, "removal_ckpt")
QUADS = ("Q_far_nip", "Q_far_ip", "Q_near_nip", "Q_near_ip")        # index near * 2 + in-path
QSPEC = {"Q_far_nip": dict(offset=(0,), inpath=(0,), gap=(2,), steps=A.STEPS_CC),
         "Q_far_ip": dict(offset=(0,), inpath=(1,), gap=(2,), steps=A.STEPS_CC),
         "Q_near_nip": dict(offset=(0,), inpath=(0,), gap=(0, 1), steps=A.STEPS_CC),
         "Q_near_ip": dict(offset=(0,), inpath=(1,), gap=(0, 1), steps=A.STEPS_CC)}
POP_Q = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3)}
LEVEL_FW = 1 - 0.05 / 9


def quad_path(tag):
    return os.path.join(C.CACHE, "dev_quadrants_%s_v01.npz" % tag)


def build_quadrants(tag, J):
    old = (PC2.CONF_POPS, PC2.POP_SPEC)
    try:
        PC2.CONF_POPS = QUADS
        PC2.POP_SPEC = dict(QSPEC)
        scenes, tab, _F = PC2.load_tracker(tag, J["decide"][tag]["retune"]["arm_of_scene"])
    finally:
        PC2.CONF_POPS, PC2.POP_SPEC = old
    del _F
    Nq = np.stack([tab[q][0] for q in QUADS], 0)          # quad x arm x scene x cell
    Xq = np.stack([tab[q][1] for q in QUADS], 0)
    dev = C.Dev(tag)
    assert list(scenes) == list(dev.scenes)
    for p, qs in POP_Q.items():
        assert np.array_equal(Nq[list(qs)].sum(0), dev.N[p]), "quadrant records do not add up to " + p
        assert np.array_equal(Xq[list(qs)].sum(0), dev.X[p]), "quadrant exceedances do not add up to " + p
    np.savez_compressed(quad_path(tag), N=Nq, X=Xq)


def flags_one(N, X, ev_fam, pw_fam, W, levels):
    one = np.ones((1, N.shape[0]))
    est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
    out = {}
    Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
    for lv in levels:
        c1 = c2 = c3 = False
        if len(ev_fam):
            c1 = bool(A.flag(est, boot, ev_fam, lv)[3].any())
        if len(pw_fam):
            c2 = bool(A.flag(est, boot, pw_fam, lv)[3].any())
        e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
        c3 = bool(A.flag(e1, b1, np.array([0]), lv)[3][0])
        out[lv] = (c1, c2, c3)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rhos", default="0.5")
    ap.add_argument("--arms", default="B0,B3,B4,B6,Mstar")
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--tags", default="t1,t3")
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    J = None
    t0 = time.time()
    for tag in a.tags.split(","):
        if not os.path.exists(quad_path(tag)):
            J = J or C.load_analysis()
            build_quadrants(tag, J)
        z = np.load(quad_path(tag))
        Nq_all = z["N"]
        dev = C.Dev(tag)
        W, _ = dev.weights()
        bpath = os.path.join(C.OUT, "sweep_ckpt", "sweep_%s_rho0.5000_p0.1500.json" % tag)
        with open(bpath) as f:
            base = json.load(f)["hk1"]
        for arm in a.arms.split(","):
            k = C.ARMS.index(arm)
            Nq = Nq_all[:, k]                                   # quad x scene x cell
            for rho in [float(x) for x in a.rhos.split(",")]:
                path = os.path.join(CKPT, "removal_%s_%s_rho%.4f.json" % (tag, arm, rho))
                if os.path.exists(path):
                    print("skip (checkpoint)", tag, arm, rho, flush=True)
                    continue
                t1 = time.time()
                seed = [SEED, dev.i, k, int(round(rho * 10000))]
                rng = np.random.default_rng(seed)
                th = (1 - rho) / rho
                fams = {}
                for p, qs in POP_Q.items():
                    N = Nq[list(qs)].sum(0)
                    ev = A.evaluable(N, dev.scenes, dev.log_idx)
                    pw = np.array([C.CELL_NAMES.index(c) for c in base[arm]["pops"][C.LAB[p]]["family"]], int)
                    fams[p] = (np.flatnonzero(ev), pw)
                cnt = {lv: np.zeros((3, 3)) for lv in (0.95, LEVEL_FW)}
                anyc = {lv: 0 for lv in (0.95, LEVEL_FW)}
                Ni = Nq.astype(np.int64)
                for _ in range(a.reps):
                    P = rng.beta(C.DELTA * th, (1 - C.DELTA) * th, size=Nq.shape[1:])
                    Xq = rng.binomial(Ni, P[None]).astype(float)
                    hit = {lv: np.zeros((3, 3), bool) for lv in cnt}
                    for pi, (p, qs) in enumerate(POP_Q.items()):
                        r = flags_one(Nq[list(qs)].sum(0), Xq[list(qs)].sum(0), fams[p][0], fams[p][1], W, tuple(cnt))
                        for lv in cnt:
                            hit[lv][pi] = r[lv]
                    for lv in cnt:
                        cnt[lv] += hit[lv]
                        anyc[lv] += bool(hit[lv].any())
                res = {"tracker": tag, "arm": arm, "rho": rho, "reps": a.reps, "seed": seed, "B": int(W.shape[0]),
                       "family_sizes": {C.LAB[p]: int(len(fams[p][1])) for p in POP_Q},
                       "evaluable": {C.LAB[p]: int(len(fams[p][0])) for p in POP_Q},
                       "conditions": ["all-evaluable cell flag", "power-family cell flag", "pooled lower bound > delta"]}
                for lv, lab in ((0.95, "rule_0.95_each"), (LEVEL_FW, "familywise_bonferroni_9")):
                    res[lab] = {"level_each": lv, "P_removed": anyc[lv] / a.reps,
                                "P_by_condition": {C.LAB[p]: (cnt[lv][pi] / a.reps).tolist() for pi, p in enumerate(POP_Q)}}
                res["seconds"] = time.time() - t1
                C.jdump(path, res)
                print(tag, arm, rho, res["rule_0.95_each"]["P_removed"], res["familywise_bonferroni_9"]["P_removed"],
                      round(res["seconds"], 1), "s", flush=True)
    print("REMOVAL DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
