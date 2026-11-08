#!/usr/bin/env python3
"""c1crit_rstar_hk1c_v02 (5 Nov 2026): supplement to part A of c1crit_rstar_v02 near the HK1c boundary. Part A's band [0.06, 0.10)
holds few real pooled cells (T3: 0 or 1), so here every development pooled cell with truth in [0.02, 0.10) (part A's cells, all 30
arms, per population and tracker) is rescaled to a finite-population mean of exactly 0.08 (= delta + 0.03, the HK1c boundary; the
scene rates multiplied by 0.08 / mu, capped at 1, with the cap's loss redistributed as in c1crit_size_v01) and the coverage of the
coded pooled UB at 375 units is measured at the levels 0.95 / 0.975 / 0.99 / 0.995 (2000 simulated sets, B = 2000; seeds
[20261306, i, 375]). This keeps each real cell's zero inflation and skew and moves only its level. nuScenes development data only.
Output: 60_RESULTS/c1_criteria_sensitivity_v02/A2_hk1c_boundary_v02.json. Usage: python -B c1crit_rstar_hk1c_v02.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_rstar_v02 as R  # noqa: E402
import numpy as np  # noqa: E402

TARGET = 0.08


def rescale(r, target):
    s = np.minimum(r * target / r.mean(), 1.0)
    for _ in range(10):
        gap = target - s.mean()
        free = s < 1.0
        if abs(gap) < 1e-12 or not free.any():
            break
        s[free] = np.minimum(s[free] * (1 + gap / max(s[free].mean() * free.mean(), 1e-12)), 1.0)
    return s


def main(reps=2000, boot=2000):
    out = {"target_truth": TARGET, "n_units": R.N_UNITS, "reps": reps, "boot": boot, "trackers": {}}
    for tag in C.TAGS:
        t0 = time.time()
        i = C.TIDX[tag]
        arms, tab = R.all_arm_pooled(tag)
        cells = []
        for p in C.POPS:
            N, X = tab[p]
            for k, a in enumerate(arms):
                m = N[k] > 0
                if m.sum() < 39:
                    continue
                r = X[k][m] / N[k][m]
                if 0.02 <= r.mean() < 0.10:
                    s = rescale(r, TARGET)
                    cells.append((a, C.LAB[p], s, float(s.mean()), float(r.mean())))
        nc = len(cells)
        truth = np.array([c[3] for c in cells])
        rng = np.random.default_rng([20261306, i, R.N_UNITS])
        n = R.N_UNITS
        rows = np.repeat(np.arange(boot), n) * n
        cov = {L: np.zeros(nc) for L in R.LEVELS_A}
        for _ in range(reps):
            V = np.empty((nc, n))
            for c in range(nc):
                V[c] = cells[c][2][rng.integers(0, len(cells[c][2]), n)]
            idx = rng.integers(0, n, boot * n)
            cnt = np.bincount(rows + idx, minlength=boot * n).reshape(boot, n).astype(float)
            est = V.mean(1)
            bt = (cnt @ V.T) / n
            se = np.std(bt, axis=0, ddof=1)
            ok = se > 0
            qs = np.quantile(bt, [1 - L for L in R.LEVELS_A], axis=0)
            for li, L in enumerate(R.LEVELS_A):
                cov[L] += np.where(ok, 2 * est - qs[li], est) >= truth - 1e-15
        cl = [{"arm": c[0], "pop": c[1], "rescaled_truth": c[3], "original_truth": c[4],
               "coverage": {str(L): float(cov[L][j] / reps) for L in R.LEVELS_A}} for j, c in enumerate(cells)]
        summ = {}
        for lab in ("PD7", "SD1_7", "PD"):
            sel = [c for c in cl if c["pop"] == lab]
            summ[lab] = {"cells": len(sel), "mean": {str(L): float(np.mean([c["coverage"][str(L)] for c in sel])) for L in R.LEVELS_A},
                         "min": {str(L): float(np.min([c["coverage"][str(L)] for c in sel])) for L in R.LEVELS_A}}
        out["trackers"][tag] = {"seed": [20261306, i, R.N_UNITS], "cells": cl, "summary": summ, "seconds": time.time() - t0}
        print(tag, nc, "cells", summ, round(time.time() - t0, 1), "s", flush=True)
    C.jdump(os.path.join(R.OUT2, "A2_hk1c_boundary_v02.json"), out)
    print("A2 DONE")


if __name__ == "__main__":
    main()
