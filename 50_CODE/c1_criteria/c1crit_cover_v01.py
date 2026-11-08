#!/usr/bin/env python3
"""c1crit_cover_v01 (5 Nov 2026): question 3, coverage of the one-sided 95 % log-bootstrap bound of one cell's scene-level
exceedance as a function of the number of units (scenes = logs, as on AV2) in the cell. nuScenes K8 development data only.

Design. A "large" development cell (>= MIN_S scenes with records; every arm in ARMS_USED, PD7, SD1_7, PD, T1 and T3) is a finite
population of per-scene rates r_s = x_s / n_s; its truth is their mean (the estimand of k6_analyse_v02.rates). A simulated cell
draws n scenes with replacement (i.i.d. from the cell's empirical distribution, so the expectation of the estimate is exactly the
truth); each scene is its own unit (log), as on AV2. The estimate is the mean of the n rates; B = 2000 unit-bootstrap means
(multinomial resampling of the n units, as A.keys_and_weights does over logs). Four one-sided 95 % bounds:
  percentile  LB = Q0.05(boot),           UB = Q0.95(boot)
  coded       LB = 2 est - Q0.95(boot),   UB = 2 est - Q0.05(boot)   (m_lib_v04._simul / k6_analyse_v02.flag for ONE cell:
              est -/+ q se with q the 0.95 quantile of the standardised bootstrap deviation; zero SE gives the estimate itself)
Coverage: P(LB <= truth) (a false flag is LB > truth) and P(UB >= truth) (HK1c and the descriptive upper bound), nominal 0.95.
n in {10, 20, 30, 39, 50, 75, 100, 150}; R = 2000 simulated cells per (tracker, n), the same draws used for every cell.
Seeds: default_rng([20261206, i, n]) (i = 0 T1, 1 T3). Checkpoint: one JSON per (tracker, n) in cover_ckpt/.
Usage: python -B c1crit_cover_v01.py [--reps 2000] [--boot 2000]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

SEED = 20261206
NS = (10, 20, 30, 39, 50, 75, 100, 150)
MIN_S = 300
ARMS_USED = C.ARMS
CKPT = os.path.join(C.OUT, "cover_ckpt")


def cells_of(dev):
    """The large cells: list of (arm, pop label, cell name, rates array, truth, zero share)."""
    out = []
    for arm in ARMS_USED:
        k = C.ARMS.index(arm)
        for p in C.POPS:
            N, X = dev.N[p][k], dev.X[p][k]
            for j in range(N.shape[1]):
                m = N[:, j] > 0
                if m.sum() < MIN_S:
                    continue
                r = X[m, j] / N[m, j]
                out.append((arm, C.LAB[p], C.CELL_NAMES[j], r, float(r.mean()), float(np.mean(r == 0))))
    return out


def run_n(cells, n, reps, B, seed):
    rng = np.random.default_rng(seed)
    nc = len(cells)
    truth = np.array([c[4] for c in cells])
    cov = {k: np.zeros(nc) for k in ("lb_pct", "ub_pct", "lb_coded", "ub_coded")}
    zero_se = np.zeros(nc)
    est_sum = np.zeros(nc)
    rows = np.repeat(np.arange(B), n) * n
    for _ in range(reps):
        V = np.empty((nc, n))
        for c in range(nc):
            r = cells[c][3]
            V[c] = r[rng.integers(0, len(r), n)]
        idx = rng.integers(0, n, B * n)
        cnt = np.bincount(rows + idx, minlength=B * n).reshape(B, n).astype(float)
        est = V.mean(1)
        boot = (cnt @ V.T) / n                                  # B x cells
        q05, q95 = np.quantile(boot, [0.05, 0.95], axis=0)
        se = np.std(boot, axis=0, ddof=1)
        ok = se > 0
        lb_c = np.where(ok, 2 * est - q95, est)
        ub_c = np.where(ok, 2 * est - q05, est)
        lb_p = np.where(ok, q05, est)
        ub_p = np.where(ok, q95, est)
        cov["lb_pct"] += lb_p <= truth + 1e-15
        cov["ub_pct"] += ub_p >= truth - 1e-15
        cov["lb_coded"] += lb_c <= truth + 1e-15
        cov["ub_coded"] += ub_c >= truth - 1e-15
        zero_se += ~ok
        est_sum += est
    return {k: (v / reps).tolist() for k, v in cov.items()}, (zero_se / reps).tolist(), (est_sum / reps - truth).tolist()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--boot", type=int, default=2000)
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    for tag in C.TAGS:
        dev = C.Dev(tag)
        cells = cells_of(dev)
        meta = [{"arm": c[0], "pop": c[1], "cell": c[2], "scenes": int(len(c[3])), "truth": c[4], "zero_share": c[5],
                 "sd_rate": float(np.std(c[3]))} for c in cells]
        for n in NS:
            path = os.path.join(CKPT, "cover_%s_n%03d.json" % (tag, n))
            if os.path.exists(path):
                print("skip (checkpoint)", tag, n, flush=True)
                continue
            t1 = time.time()
            seed = [SEED, dev.i, n]
            cov, zse, bias = run_n(cells, n, a.reps, a.boot, seed)
            res = {"tracker": tag, "n": n, "reps": a.reps, "boot": a.boot, "seed": seed, "min_scenes_for_large_cell": MIN_S,
                   "cells": meta, "coverage": cov, "zero_se_share": zse, "mean_bias": bias, "seconds": time.time() - t1}
            C.jdump(path, res)
            print(tag, n, {k: round(float(np.mean(v)), 4) for k, v in cov.items()}, len(cells), "cells", round(res["seconds"], 1), "s",
                  flush=True)
    print("COVER DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
