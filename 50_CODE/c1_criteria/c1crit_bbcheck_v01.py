#!/usr/bin/env python3
"""c1crit_bbcheck_v01 (5 Nov 2026): the lead's item 1 (C1_CRITERIA_EVIDENCE_REVIEW_v01 section 6 and 3.1; plan C6c), on the nuScenes
K8 development data only: for M*, B4 and B6 on PD7 and SD1_7 (PD added), T1 and T3,
  (a) the planning summaries the review names for the pooled ANOVA ICC (Ridout, Demetrio and Firth 1999): the upper limit of the
      80 % and 90 % log-cluster bootstrap intervals (the 90th and 95th percentiles of the bootstrap distribution), and the 75th
      percentile of the per-cell estimates; the bootstrap reuses c1crit_rho_v01's draws exactly (seed [20261205, i, 1], B = 1000),
      and the 95 % interval is asserted equal to the rho checkpoint's;
  (b) a beta-binomial fit check per evaluable cell with exceedances: per-cell maximum likelihood (mu, rho) (c1crit_rho_v01.bb_fit),
      then (i) the observed between-scene variance of the per-scene rates against the model's mean of mu (1 - mu) (rho + (1 - rho)
      / n_s), and (ii) the observed number of scenes with no exceedance against the model's sum_s B(alpha, n_s + beta) / B(alpha,
      beta). The same two checks under the pooled common-rho fit with rho = 0.5 (the rule's value) show what 0.5 implies.
Output: 60_RESULTS/c1_criteria_sensitivity_v01/bbcheck_v01.json (one run; deterministic). Usage: python -B c1crit_bbcheck_v01.py
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_rho_v01 as R  # noqa: E402
import numpy as np  # noqa: E402
from scipy.special import betaln  # noqa: E402

A = C.A
ARMS = ("Mstar", "B4", "B6")


def p0_model(n, mu, rho):
    th = (1 - rho) / rho
    a, b = mu * th, (1 - mu) * th
    return np.exp(betaln(a, n + b) - betaln(a, b))


def main():
    t0 = time.time()
    out = {"stamp": "c1crit_bbcheck_v01: nuScenes development data only", "trackers": {}}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        rng = np.random.default_rng([R.SEED_CI, dev.i, 1])
        Wl = rng.multinomial(dev.n_logs, np.full(dev.n_logs, 1.0 / dev.n_logs), size=R.B_ANOVA).astype(float)
        Wci = Wl[:, dev.log_idx]
        t = {}
        for arm in ARMS:
            with open(os.path.join(R.CKPT, "rho_%s_%s.json" % (tag, arm))) as f:
                ck = json.load(f)
            for p in C.POPS:
                lab = C.LAB[p]
                N, X = dev.N[p][C.ARMS.index(arm)], dev.X[p][C.ARMS.index(arm)]
                ev = A.evaluable(N, dev.scenes, dev.log_idx)
                use = ev & (X.sum(0) > 0) & (X.sum(0) < N.sum(0))
                cols = np.flatnonzero(use)
                one = np.ones((1, N.shape[0]))
                P0 = R.anova_parts(N, X, one)
                Pb = R.anova_parts(N, X, Wci)
                pooled = float(R.anova_rho(*[q[0][cols].sum() for q in P0]))
                pb = R.anova_rho(*[q[:, cols].sum(1) for q in Pb])
                ci95 = [float(x) for x in np.nanquantile(pb, [0.025, 0.975])]
                same = ck["pops"][lab]["anova_pooled_ci95"] is not None and np.allclose(ci95, ck["pops"][lab]["anova_pooled_ci95"], atol=1e-12)
                rc = R.anova_rho(*[q[0] for q in P0])[cols]
                cells, fit = {}, []
                for j in cols:
                    m = N[:, j] > 0
                    n_, x_ = N[m, j], X[m, j]
                    rho_j, _ = R.bb_fit([n_], [x_], [np.ones(len(n_))])
                    r_ = x_ / n_          # the model checks use the scene-level mean (the rule's estimand) as mu
                    var_obs = float(np.var(r_, ddof=1))
                    mu_s = float(r_.mean())
                    var_mod = float(np.mean(mu_s * (1 - mu_s) * (rho_j + (1 - rho_j) / n_)))
                    var_05 = float(np.mean(mu_s * (1 - mu_s) * (0.5 + 0.5 / n_)))
                    z_obs = int((x_ == 0).sum())
                    z_mod = float(p0_model(n_, max(mu_s, 1e-9), max(rho_j, 1e-6)).sum())
                    z_05 = float(p0_model(n_, max(mu_s, 1e-9), 0.5).sum())
                    cells[C.CELL_NAMES[j]] = {"scenes": int(m.sum()), "E": mu_s, "bb_rho": rho_j, "anova_rho": float(rc[list(cols).index(j)]),
                                              "var_obs": var_obs, "var_model_bb": var_mod, "var_model_rho0.5": var_05,
                                              "zero_scenes_obs": z_obs, "zero_scenes_model_bb": z_mod, "zero_scenes_model_rho0.5": z_05}
                    fit.append((var_obs / var_mod if var_mod > 0 else np.nan, var_obs / var_05 if var_05 > 0 else np.nan,
                                z_obs / z_mod if z_mod > 0 else np.nan, z_obs / z_05 if z_05 > 0 else np.nan, int(m.sum())))
                fa = np.array(fit, float) if fit else np.zeros((0, 5))
                t["%s|%s" % (arm, lab)] = {
                    "cells_used": int(len(cols)), "anova_pooled": pooled, "anova_pooled_ci95": ci95, "ci95_equals_rho_checkpoint": bool(same),
                    "anova_pooled_upper80": float(np.nanquantile(pb, 0.90)), "anova_pooled_upper90": float(np.nanquantile(pb, 0.95)),
                    "anova_cell_p75": float(np.quantile(rc, 0.75)) if len(rc) else None,
                    "bb_cell_p75": float(np.quantile([c["bb_rho"] for c in cells.values()], 0.75)) if cells else None,
                    "fit_var_ratio_obs_over_bb_median": float(np.nanmedian(fa[:, 0])) if len(fa) else None,
                    "fit_var_ratio_obs_over_rho05_median": float(np.nanmedian(fa[:, 1])) if len(fa) else None,
                    "fit_zero_ratio_obs_over_bb_median": float(np.nanmedian(fa[:, 2])) if len(fa) else None,
                    "fit_zero_ratio_obs_over_rho05_median": float(np.nanmedian(fa[:, 3])) if len(fa) else None,
                    "cells": cells}
                print(tag, arm, lab, round(pooled, 3), [round(x, 3) for x in ci95], same, flush=True)
        out["trackers"][tag] = t
    out["seconds"] = time.time() - t0
    C.jdump(os.path.join(C.OUT, "bbcheck_v01.json"), out)
    print("BBCHECK DONE", round(out["seconds"], 1), "s")


if __name__ == "__main__":
    main()
