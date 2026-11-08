#!/usr/bin/env python3
"""c1crit_size_v01 (5 Nov 2026): the lead's item 5 (C1_CRITERIA_EVIDENCE_REVIEW_v01 section 6; plan C2, C5): the actual one-sided
size of the cell flag at a true delta, as a function of the number of units (logs; a log is a scene, as on AV2) per cell, judged
against Bradley's liberal band [0.025, 0.075]. nuScenes K8 development data only.

Planting delta, two ways:
  EMP  (empirical shapes) The large development cells (>= 300 scenes, every arm, T1 and T3) whose scene-level exceedance is in
       [0.03, 0.08] give the shape of the per-scene rate distribution (zero inflation, skew, scene heterogeneity). Each is
       rescaled to a finite-population mean of exactly delta (r_s * delta / mu, capped at 1, then the cap's loss redistributed by
       one more rescaling of the uncapped scenes). A synthetic cell draws G units i.i.d. from one rescaled shape.
  BB   (parametric) beta-binomial with mean delta and rho in --rhos; each unit's record count drawn from the pooled development
       records-per-scene distribution of the same large cells.
A synthetic family holds K = 32 independent cells (shapes drawn at random); the flag is the rule's: one-sided sup-t at 0.95
over the family's cells (m_lib_v04._simul, studentised by the bootstrap SE; zero SE flags only if E > delta), B = 2000 unit
bootstrap weights shared by the family's cells. Reported: the per-cell flag rate and the familywise size P(any flag) for
families of K = 1 (a single cell; the one-sided 95 % bound), 8, 16 and 32 cells (the first K cells of each family).
G in {10, 20, 30, 39, 50, 80, 150}; R = 2000 families per (variant, G). Seeds default_rng([20261210, v, G]), v = 0 for EMP and
round(10000 rho) for BB (recorded). Checkpoint: one JSON per (variant, G) in size_ckpt/
Usage: python -B c1crit_size_v01.py [--rhos 0.5,<rho_hat>] [--reps 2000]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A = C.A
M = A.M
SEED = 20261210
CKPT = os.path.join(C.OUT, "size_ckpt")
GS = (10, 20, 30, 39, 50, 80, 150)
KS = (1, 8, 16, 32)
B = 2000


def shapes():
    """Rescaled per-scene rate arrays (mean exactly delta) and the records-per-scene pool."""
    out, npool, meta = [], [], []
    for tag in C.TAGS:
        dev = C.Dev(tag)
        for arm in C.ARMS:
            k = C.ARMS.index(arm)
            for p in C.POPS:
                N, X = dev.N[p][k], dev.X[p][k]
                for j in range(N.shape[1]):
                    m = N[:, j] > 0
                    if m.sum() < 300:
                        continue
                    r = X[m, j] / N[m, j]
                    mu = r.mean()
                    if not (0.03 <= mu <= 0.08):
                        continue
                    s = np.minimum(r * C.DELTA / mu, 1.0)
                    for _ in range(5):
                        gap = C.DELTA - s.mean()
                        free = s < 1.0
                        if abs(gap) < 1e-12 or not free.any():
                            break
                        s[free] = np.minimum(s[free] * (1 + gap / max(s[free].mean() * free.mean(), 1e-12)), 1.0)
                    out.append(s)
                    npool.append(N[m, j])
                    meta.append({"tracker": tag, "arm": arm, "pop": C.LAB[p], "cell": C.CELL_NAMES[j], "scenes": int(m.sum()),
                                 "mu": float(mu), "zero_share": float(np.mean(r == 0)), "rescaled_mean": float(s.mean())})
    return out, np.concatenate(npool), meta


def run(variant, G, reps, rng, shp, npool, rho=None):
    K = max(KS)
    rows = np.repeat(np.arange(B), G) * G
    fam_any = {k: 0 for k in KS}
    cell_flags = {k: 0.0 for k in KS}
    th = None if rho is None else (1 - rho) / rho
    for _ in range(reps):
        if variant == "EMP":
            pick = rng.integers(0, len(shp), K)
            V = np.empty((K, G))
            for c in range(K):
                s = shp[pick[c]]
                V[c] = s[rng.integers(0, len(s), G)]
        else:
            n = npool[rng.integers(0, len(npool), (K, G))].astype(int)
            P = rng.beta(C.DELTA * th, (1 - C.DELTA) * th, size=(K, G))
            V = rng.binomial(n, P) / n
        idx = rng.integers(0, G, B * G)
        cnt = np.bincount(rows + idx, minlength=B * G).reshape(B, G).astype(float)
        est = V.mean(1)
        boot = (cnt @ V.T) / G
        for k in KS:
            lb, se, q, ok = M._simul(est[:k], boot[:, :k], 0.95, "lower")
            sig = (ok & (lb > C.DELTA)) | (~ok & (est[:k] > C.DELTA))
            fam_any[k] += bool(sig.any())
            cell_flags[k] += float(sig.mean())
    return {"familywise_size": {k: fam_any[k] / reps for k in KS}, "per_cell_flag_rate": {k: cell_flags[k] / reps for k in KS}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rhos", default="0.5")
    ap.add_argument("--reps", type=int, default=2000)
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    shp, npool, meta = shapes()
    mpath = os.path.join(CKPT, "shapes_meta.json")
    if not os.path.exists(mpath):
        C.jdump(mpath, {"shapes": meta, "n_shapes": len(shp), "records_pool": int(len(npool)),
                        "records_per_scene_median": float(np.median(npool))})
    variants = [("EMP", None)] + [("BB", float(r)) for r in a.rhos.split(",")]
    for vi, (var, rho) in enumerate(variants):
        for G in GS:
            name = "size_%s%s_G%03d" % (var, "" if rho is None else "_rho%.4f" % rho, G)
            path = os.path.join(CKPT, name + ".json")
            if os.path.exists(path):
                print("skip (checkpoint)", name, flush=True)
                continue
            t1 = time.time()
            seed = [SEED, vi if rho is None else int(round(rho * 10000)), G]
            res = run(var, G, a.reps, np.random.default_rng(seed), shp, npool, rho)
            res.update({"variant": var, "rho": rho, "G": G, "reps": a.reps, "B": B, "seed": seed, "n_shapes": len(shp),
                        "bradley_band": [0.025, 0.075], "seconds": time.time() - t1})
            C.jdump(path, res)
            print(name, res["familywise_size"], {k: round(v, 4) for k, v in res["per_cell_flag_rate"].items()}, round(res["seconds"], 1),
                  "s", flush=True)
    print("SIZE DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
