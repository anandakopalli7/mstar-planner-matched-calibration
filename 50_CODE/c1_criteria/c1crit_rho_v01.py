#!/usr/bin/env python3
"""c1crit_rho_v01 (5 Nov 2026): question 1, the within-scene correlation rho of record exceedance indicators, on the nuScenes
K8 development data only (840 scenes, 68 logs, decision mode, T1 and T3), per arm, population and cell.

The power rule (k6_analyse_v02.power_family) draws, per scene and cell, P ~ Beta(mean 0.15, intra-scene correlation rho = 0.5)
and X ~ Bin(n, P). So the rho it assumes is the intraclass correlation of the binary exceedance indicators of the records of one
scene within one cell (cluster = scene x cell). Three estimators:
  1. ANOVA ICC for binary data (Fleiss 1981; Ridout, Demetrio and Firth 1999, Biometrics 55:137-148): per cell, and pooled
     within a population over cells (stratified one-way ANOVA: cell-specific means, the sums of squares and degrees of freedom
     summed over cells). Cells used for pooling: evaluable (>= 39 scenes from >= 8 logs) with 0 < exceedances < records.
  2. Beta-binomial maximum likelihood (Williams 1975; Crowder 1978): pooled per population with a common rho and cell-specific
     means (the power rule's model), and per cell with its own rho. Same cells.
  3. The implied rho: the rho at which the power model's variance of the cell estimate, mu (1 - mu) / S^2 * sum_s (rho +
     (1 - rho) / n_s) at mu = the cell's estimate, equals the cell's log-bootstrap variance on the real data (K8 v03 weights).
     It is the rho that makes the power rule's simulated precision equal the real precision (it absorbs scene-within-log
     correlation, which AV2's one-scene logs do not have).
CIs: log-cluster bootstrap (resample the 68 logs), percentile 95 %; ANOVA B = 1000, pooled beta-binomial B = BB_B.
Seeds (recorded): CI bootstrap default_rng([20261205, i, 1]); the implied rho uses K8 v03's own weights [20261106, i, 0].
Checkpoint: one JSON per tracker x arm in rho_ckpt/; a rerun resumes.
Usage: python -B c1crit_rho_v01.py [--bb-b 200] [--arms Mstar,B4,...] [--tags t1,t3]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402
from scipy.optimize import minimize  # noqa: E402
from scipy.special import gammaln, digamma  # noqa: E402

A = C.A
SEED_CI = 20261205
B_ANOVA = 1000
CKPT = os.path.join(C.OUT, "rho_ckpt")
BANDS = ((0.0, 0.03), (0.03, 0.08), (0.08, 0.30), (0.30, 1.01))


def anova_parts(N, X, Wt):
    """Weighted (frequency weights per scene, rows of Wt) one-way ANOVA pieces per cell: SSB, SSW, dfB, dfW, n0num."""
    pres = (N > 0).astype(float)
    a1 = np.divide(X * X, N, out=np.zeros_like(X), where=N > 0)
    k = Wt @ pres
    Nt = Wt @ N
    Xt = Wt @ X
    sx2n = Wt @ a1
    sn2 = Wt @ (N * N)
    with np.errstate(invalid="ignore", divide="ignore"):
        SSB = sx2n - Xt * Xt / Nt
        n0num = Nt - sn2 / Nt
    SSW = Xt - sx2n
    return SSB, SSW, k - 1, Nt - k, n0num


def anova_rho(SSB, SSW, dfB, dfW, n0num):
    with np.errstate(invalid="ignore", divide="ignore"):
        MSB, MSW, n0 = SSB / dfB, SSW / dfW, n0num / dfB
        return (MSB - MSW) / (MSB + (n0 - 1) * MSW)


def bb_negll(params, n, x, w, J):
    """Negative beta-binomial log-likelihood (binomial coefficients dropped) and gradient. params = [logit mu_1..J, log theta];
    n, x, w: lists per cell of arrays (records, exceedances, weights)."""
    v = params[-1]
    th = np.exp(v)
    ll, g = 0.0, np.zeros(J + 1)
    for j in range(J):
        mu = 1.0 / (1.0 + np.exp(-params[j]))
        mu = min(max(mu, 1e-12), 1 - 1e-12)
        a, b = mu * th, (1 - mu) * th
        nn, xx, ww = n[j], x[j], w[j]
        ll += np.sum(ww * (gammaln(xx + a) + gammaln(nn - xx + b) - gammaln(nn + a + b) - gammaln(a) - gammaln(b) + gammaln(a + b)))
        ga = np.sum(ww * (digamma(xx + a) - digamma(nn + a + b) - digamma(a) + digamma(a + b)))
        gb = np.sum(ww * (digamma(nn - xx + b) - digamma(nn + a + b) - digamma(b) + digamma(a + b)))
        g[j] = th * mu * (1 - mu) * (ga - gb)
        g[J] += a * ga + b * gb
    return -ll, -g


def bb_fit(n, x, w, rho0=0.1):
    """Common-rho beta-binomial MLE over the cells in n, x, w. Returns rho (and the fitted means)."""
    J = len(n)
    mu0 = [max(min(np.sum(w[j] * x[j]) / max(np.sum(w[j] * n[j]), 1e-12), 1 - 1e-6), 1e-6) for j in range(J)]
    p0 = np.r_[np.log(np.array(mu0) / (1 - np.array(mu0))), np.log((1 - rho0) / rho0)]
    bounds = [(-20, 20)] * J + [(-8, 18)]
    r = minimize(bb_negll, p0, args=(n, x, w, J), jac=True, method="L-BFGS-B", bounds=bounds, options={"maxiter": 500})
    th = np.exp(r.x[-1])
    return float(1.0 / (1.0 + th)), bool(r.success)


def cell_lists(N, X, cols, wscene=None):
    n, x, w = [], [], []
    for j in cols:
        m = N[:, j] > 0
        if wscene is not None:
            m = m & (wscene > 0)
        n.append(N[m, j])
        x.append(X[m, j])
        w.append(np.ones(int(m.sum())) if wscene is None else wscene[m])
    return n, x, w


def implied_rho(N, X, W):
    """Per cell: (estimate, bootstrap SE, S, H, implied rho)."""
    one = np.ones((1, N.shape[0]))
    est = A.rates(N, X, one)[0]
    boot = A.rates(N, X, W)
    se = np.nanstd(boot, axis=0, ddof=1)
    S = (N > 0).sum(0).astype(float)
    H = np.where(N > 0, 1.0 / np.where(N > 0, N, 1.0), 0.0).sum(0)
    with np.errstate(invalid="ignore", divide="ignore"):
        rho = (S * S * se * se / (est * (1 - est)) - H) / (S - H)
    return est, se, S, H, rho


def pct(a, q):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return [float(x) for x in np.quantile(a, q)] if len(a) else None


def one_arm(dev, arm, Wk8, Wci_scene, bb_b, rng_bb):
    res = {"tracker": dev.tag, "arm": arm, "pops": {}}
    for p in C.POPS:
        N, X = dev.N[p][C.ARMS.index(arm)], dev.X[p][C.ARMS.index(arm)]
        ev = A.evaluable(N, dev.scenes, dev.log_idx)
        tot_n, tot_x = N.sum(0), X.sum(0)
        use = ev & (tot_x > 0) & (tot_x < tot_n)
        cols = np.flatnonzero(use)
        # ANOVA, point and bootstrap
        one = np.ones((1, N.shape[0]))
        P0 = anova_parts(N, X, one)
        rho_cell = anova_rho(*[q[0] for q in P0])
        Pb = anova_parts(N, X, Wci_scene)
        rho_cell_b = anova_rho(*Pb)
        pooled = anova_rho(*[q[0][cols].sum() for q in P0]) if len(cols) else np.nan
        pooled_b = anova_rho(*[q[:, cols].sum(1) for q in Pb]) if len(cols) else np.full(len(Wci_scene), np.nan)
        # implied rho (K8 weights)
        est, se, S, H, rimp = implied_rho(N, X, Wk8)
        # beta-binomial pooled MLE and bootstrap
        bb = bbok = None
        bb_boot = []
        if len(cols):
            n_, x_, w_ = cell_lists(N, X, cols)
            bb, bbok = bb_fit(n_, x_, w_)
            for b in range(bb_b):
                ws = Wci_scene[b]
                n_, x_, w_ = cell_lists(N, X, cols, ws)
                bb_boot.append(bb_fit(n_, x_, w_, rho0=max(bb, 1e-3))[0])
        # per-cell beta-binomial (own rho)
        bb_cell = {}
        for j in cols:
            n_, x_, w_ = cell_lists(N, X, [j])
            bb_cell[C.CELL_NAMES[j]] = bb_fit(n_, x_, w_)[0]
        cells = {}
        for j in range(N.shape[1]):
            if S[j] < 2:
                continue
            nm = C.CELL_NAMES[j]
            cells[nm] = {"evaluable": bool(ev[j]), "used_for_pooling": bool(use[j]), "scenes": int(S[j]), "records": int(tot_n[j]),
                         "exceed": int(tot_x[j]), "E": float(est[j]) if np.isfinite(est[j]) else None,
                         "se_boot_k8": float(se[j]) if np.isfinite(se[j]) else None,
                         "anova_rho": float(rho_cell[j]) if np.isfinite(rho_cell[j]) else None,
                         "anova_rho_ci95": pct(rho_cell_b[:, j], [0.025, 0.975]) if use[j] else None,
                         "bb_rho": bb_cell.get(nm), "implied_rho": float(rimp[j]) if np.isfinite(rimp[j]) else None,
                         "median_records_per_scene": float(np.median(N[N[:, j] > 0, j]))}
        imp_ev = rimp[use]
        res["pops"][C.LAB[p]] = {
            "cells_used": int(len(cols)), "evaluable": int(ev.sum()),
            "anova_pooled": float(pooled), "anova_pooled_ci95": pct(pooled_b, [0.025, 0.975]),
            "bb_pooled": bb, "bb_pooled_converged": bbok, "bb_pooled_ci95": pct(bb_boot, [0.025, 0.975]) if bb_boot else None,
            "bb_boot_B": len(bb_boot),
            "anova_cell_median": pct(rho_cell[use], [0.5])[0] if len(cols) else None,
            "anova_cell_iqr": pct(rho_cell[use], [0.25, 0.75]) if len(cols) else None,
            "bb_cell_median": float(np.median(list(bb_cell.values()))) if bb_cell else None,
            "implied_cell_median": pct(imp_ev, [0.5])[0] if len(cols) else None,
            "implied_cell_iqr": pct(imp_ev, [0.25, 0.75]) if len(cols) else None,
            "implied_cell_max": float(np.nanmax(imp_ev)) if len(cols) else None,
            "cells": cells}
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--bb-b", type=int, default=200)
    ap.add_argument("--arms", default=",".join(C.ARMS))
    ap.add_argument("--tags", default="t1,t3")
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    for tag in a.tags.split(","):
        dev = C.Dev(tag)
        Wk8, _ = dev.weights()
        rng = np.random.default_rng([SEED_CI, dev.i, 1])
        Wl = rng.multinomial(dev.n_logs, np.full(dev.n_logs, 1.0 / dev.n_logs), size=B_ANOVA).astype(float)
        Wci = Wl[:, dev.log_idx]
        for arm in a.arms.split(","):
            path = os.path.join(CKPT, "rho_%s_%s.json" % (tag, arm))
            if os.path.exists(path):
                print("skip (checkpoint)", tag, arm, flush=True)
                continue
            t1 = time.time()
            r = one_arm(dev, arm, Wk8, Wci, a.bb_b, None)
            r["seeds"] = {"ci_bootstrap": [SEED_CI, dev.i, 1], "B_anova": B_ANOVA, "B_bb": a.bb_b, "implied_rho_weights": [C.SEED_BOOT_K8, dev.i, 0]}
            r["seconds"] = time.time() - t1
            C.jdump(path, r)
            print(tag, arm, {k: (v["anova_pooled"], v["bb_pooled"], v["implied_cell_median"]) for k, v in r["pops"].items()},
                  round(r["seconds"], 1), "s", flush=True)
    print("RHO DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
