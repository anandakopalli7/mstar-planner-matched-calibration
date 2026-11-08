#!/usr/bin/env python3
"""c1crit_cover2_v01 (5 Nov 2026): question 3, two follow-ups to c1crit_cover_v01 (same design, same estimators; nuScenes K8
development data only).
  Part POOLED: the pooled cell of each arm x population (per scene: all its cells' records and exceedances summed; every scene
    with records), n in {39, 75, 150, 375}: the coverage of the one-sided 95 % bounds that HK1c (upper) and NoFlag_pool (lower)
    use, at AV2's planned 375 units and below.
  Part SIMUL: the large cells of c1crit_cover_v01, n in {39, 75, 150}, with the bootstrap quantile at the per-cell level of a
    Sidak split over 32 cells (1 - 0.05 / 32 approximately: 0.95 ** (1 / 32) = 0.99840), the strength of the sup-t quantile of an
    all-evaluable family of 32 cells. It shows whether the simultaneous bounds (the flags; the descriptive U_max of Choice 47f)
    reach 95 % per cell where the single-cell 95 % bound does not.
Bounds as in c1crit_cover_v01 (percentile and coded). R = 2000, B = 2000. Seeds: default_rng([20261208, i, n, part]) with part
0 POOLED, 1 SIMUL. Checkpoint: one JSON per (part, tracker, n) in cover2_ckpt/.
Usage: python -B c1crit_cover2_v01.py [--reps 2000] [--boot 2000]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_cover_v01 as CV  # noqa: E402
import numpy as np  # noqa: E402

SEED = 20261208
CKPT = os.path.join(C.OUT, "cover2_ckpt")
NS_POOLED = (39, 75, 150, 375)
NS_SIMUL = (39, 75, 150)
LEVEL_SIMUL = 0.95 ** (1.0 / 32)


def pooled_cells(dev):
    out = []
    for arm in C.ARMS:
        k = C.ARMS.index(arm)
        for p in C.POPS:
            N, X = dev.N[p][k].sum(1), dev.X[p][k].sum(1)
            m = N > 0
            r = X[m] / N[m]
            out.append((arm, C.LAB[p], "pooled", r, float(r.mean()), float(np.mean(r == 0))))
    return out


def run_n_level(cells, n, reps, B, seed, level):
    """As c1crit_cover_v01.run_n, with the one-sided bounds at an arbitrary level."""
    rng = np.random.default_rng(seed)
    nc = len(cells)
    truth = np.array([c[4] for c in cells])
    cov = {k: np.zeros(nc) for k in ("lb_pct", "ub_pct", "lb_coded", "ub_coded")}
    rows = np.repeat(np.arange(B), n) * n
    lo, hi = 1 - level, level
    for _ in range(reps):
        V = np.empty((nc, n))
        for c in range(nc):
            r = cells[c][3]
            V[c] = r[rng.integers(0, len(r), n)]
        idx = rng.integers(0, n, B * n)
        cnt = np.bincount(rows + idx, minlength=B * n).reshape(B, n).astype(float)
        est = V.mean(1)
        boot = (cnt @ V.T) / n
        qlo, qhi = np.quantile(boot, [lo, hi], axis=0)
        se = np.std(boot, axis=0, ddof=1)
        ok = se > 0
        cov["lb_pct"] += np.where(ok, qlo, est) <= truth + 1e-15
        cov["ub_pct"] += np.where(ok, qhi, est) >= truth - 1e-15
        cov["lb_coded"] += np.where(ok, 2 * est - qhi, est) <= truth + 1e-15
        cov["ub_coded"] += np.where(ok, 2 * est - qlo, est) >= truth - 1e-15
    return {k: (v / reps).tolist() for k, v in cov.items()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    for tag in C.TAGS:
        dev = C.Dev(tag)
        for part, cells, ns, level in (("POOLED", pooled_cells(dev), NS_POOLED, 0.95), ("SIMUL", CV.cells_of(dev), NS_SIMUL, LEVEL_SIMUL)):
            meta = [{"arm": c[0], "pop": c[1], "cell": c[2], "scenes": int(len(c[3])), "truth": c[4], "zero_share": c[5]} for c in cells]
            for n in ns:
                path = os.path.join(CKPT, "cover2_%s_%s_n%03d.json" % (part, tag, n))
                if os.path.exists(path):
                    print("skip (checkpoint)", part, tag, n, flush=True)
                    continue
                t1 = time.time()
                seed = [SEED, dev.i, n, 0 if part == "POOLED" else 1]
                cov = run_n_level(cells, n, a.reps, a.boot, seed, level)
                res = {"part": part, "tracker": tag, "n": n, "level": level, "reps": a.reps, "boot": a.boot, "seed": seed,
                       "cells": meta, "coverage": cov, "seconds": time.time() - t1}
                C.jdump(path, res)
                print(part, tag, n, {k: round(float(np.mean(v)), 4) for k, v in cov.items()}, len(cells), "cells",
                      round(res["seconds"], 1), "s", flush=True)
    print("COVER2 DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
