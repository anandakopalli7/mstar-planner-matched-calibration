#!/usr/bin/env python3
"""Unit and Monte Carlo tests of m_lib_v01 on simulated item tables (Claude line, v01, 31 Oct 2026).
Simulated data only: no real annotation, export or residual is read. Writes a JSON report.
Usage: python test_m_units_v01.py --out <json>
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m_lib_v01 as M  # noqa: E402


def sim_items(rng, n_logs=50, scenes_per_log=14, tau=None, log_sd=0.0, items_per_scene=40, turn_share=0.15):
    """Item table with strata car x {<20, 20-40} x {long, lat} x {static, straight, turning, new} and pedestrians.
    U = tau(stratum) * N(0,1) (+ a log effect); sd = 0.3-0.8; D = U * sd."""
    S = n_logs * scenes_per_log
    scene_log = np.repeat(np.arange(n_logs), scenes_per_log)
    leff = rng.normal(0, log_sd, n_logs)
    n = S * items_per_scene
    s = np.repeat(np.arange(S), items_per_scene)
    g = np.where(rng.random(n) < 0.8, 0, 1)
    r = rng.integers(0, 2, n)
    a = rng.integers(0, 2, n)
    u = rng.random(n)
    mot = np.where(u < 0.35, 0, np.where(u < 0.35 + (0.6 - turn_share), 1, np.where(u < 0.95, 2, 3)))
    spd = np.where(mot == 0, rng.uniform(0, 0.9, n), rng.uniform(1.5, 12, n))
    om = np.where(mot == 2, rng.choice([-1, 1], n) * rng.uniform(0.12, 0.4, n), rng.uniform(-0.08, 0.08, n))
    om = np.where(mot == 3, np.nan, om)
    if tau is None:
        tau = lambda g_, a_, m_: np.where(a_ == 1, np.where(m_ == 2, 2.6, np.where(m_ == 0, 0.6, 1.2)), np.where(m_ == 0, 0.5, 0.9))
    U = tau(g, a, mot) * (rng.standard_normal(n) + leff[scene_log[s]])
    V = rng.uniform(0.3, 0.8, n) ** 2
    sd = np.sqrt(V + M.SIGMA_A ** 2)
    items = {"s": s, "lg": scene_log[s], "g": g, "r": r, "a": a, "spd": spd, "om": om, "omv": om.copy(), "V": V,
             "contested": np.zeros(n, bool), "D": U * sd, "scene_log_idx": scene_log, "n_scenes": S, "n_logs": n_logs}
    nr = S * 10
    rs = np.repeat(np.arange(S), 10)
    sxx, syy = rng.uniform(0.1, 0.5, nr), rng.uniform(0.1, 0.5, nr)
    recs = {"s": rs, "g": np.zeros(nr, int), "r": rng.integers(0, 2, nr), "sxx": sxx, "sxy": np.zeros(nr), "syy": syy,
            "dx": 2 * np.sqrt(sxx + M.SIGMA_A ** 2) * rng.standard_normal(nr), "dy": 2 * np.sqrt(syy + M.SIGMA_A ** 2) * rng.standard_normal(nr),
            "contested": np.zeros(nr, bool)}
    return items, recs, mot


def fold_eval(items, recs, cfg, rng_label, B=300, ev=None, folds=None):
    P = M.prepare(items, recs, cfg)
    names = ["sc%d" % i for i in range(items["n_scenes"])]
    slog = {nm: "log%d" % items["scene_log_idx"][i] for i, nm in enumerate(names)}
    if folds is None:
        folds, _ = M.log_folds(names, slog)
    marg = {m: np.full(len(items["D"]), np.nan) for m in M.METHODS}
    for f in range(M.K_FOLDS):
        cal = folds != f
        fit = M.fit_methods(items, recs, P, cal, cfg)
        sel = ~cal[items["s"]]
        for k, v in M.margins(items, P, fit, sel).items():
            marg[k][sel] = v
    if ev is None:
        cnt = M.counts_by_l0(items, P["m"])
        rev = {M.l0_name(i): i for i in range(M.N_L0)}
        ev = sorted(rev[k] for k, v in cnt.items() if v["scenes"] >= M.N_EVAL)
    W = M.boot_scene_weights(items, B, np.random.default_rng(abs(hash(rng_label)) % 2 ** 32))
    st = M.eval_stats(items, P, marg, ev, W)
    st["hypotheses"] = M.hypotheses(st)
    return st, P, marg


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=100)
    a = ap.parse_args()
    out, ok = {}, {}

    # T11 motion state and T12 half-angle wrap
    it = {"spd": np.array([0.5, 2, 2, 2, 0.2]), "om": np.array([0.5, 0.05, -0.2, np.nan, np.nan])}
    ok["T11_motion_state"] = M.motion_state(it).tolist() == [0, 1, 2, 3, 0]
    ok["T12_wrap_half"] = abs(M.wrap_half(math.pi - 0.01)) < 0.02 and abs(M.wrap_half(0.3) - 0.3) < 1e-12

    # T6 PM2 deployable covariance
    rng = np.random.default_rng(1)
    worst = 0.0
    for _ in range(200):
        A = rng.normal(size=(2, 2))
        S = A @ A.T + 0.01 * np.eye(2)
        yaw, cl, ct = rng.uniform(-3, 3), rng.uniform(0.5, 6), rng.uniform(0.5, 6)
        St = M.deploy_covariance(S, yaw, cl, ct)
        for c, ax in ((cl, np.array([math.cos(yaw), math.sin(yaw)])), (ct, np.array([-math.sin(yaw), math.cos(yaw)]))):
            worst = max(worst, abs(M.Z * math.sqrt(ax @ St @ ax) - c * math.sqrt(ax @ S @ ax + M.SIGMA_A ** 2)))
        assert np.linalg.eigvalsh(St).min() > -1e-12
    out["T6_max_abs_error_m"] = worst
    ok["T6_PM2"] = worst < 1e-9

    # T7 folds
    names = ["sc%d" % i for i in range(700)]
    rs = np.random.default_rng(2)
    slog = {nm: "log%d" % min(49, int(rs.integers(0, 50))) for nm in names}
    folds, load = M.log_folds(names, slog)
    disjoint = all(len({folds[i] for i, nm in enumerate(names) if slog[nm] == lg}) == 1 for lg in set(slog.values()))
    out["T7_fold_loads"] = load
    ok["T7_folds"] = disjoint and sum(load) == 700 and max(load) - min(load) <= max(np.unique(list(slog.values()), return_counts=True)[1])

    # T8 fallback and T9 ordering of B3 / B6c
    items, recs, mot = sim_items(np.random.default_rng(3), turn_share=0.01)
    P = M.prepare(items, recs, {})
    fit = M.fit_methods(items, recs, P, np.ones(items["n_scenes"], bool), {})
    cnt = M.counts_by_l0(items, P["m"])
    sparse = [i for i in range(M.N_L0) if M.l0_name(i) in cnt and cnt[M.l0_name(i)]["scenes"] < M.N_CRC]
    dense = [i for i in range(M.N_L0) if M.l0_name(i) in cnt and cnt[M.l0_name(i)]["scenes"] >= M.N_CRC]
    out["T8_sparse_strata"] = [M.l0_name(i) for i in sparse]
    ok["T8_fallback"] = bool(sparse) and all(fit["Mstar_src"][i] >= 1 for i in sparse) and all(fit["Mstar_src"][i] == 0 for i in dense)
    ok["T9_B3_B6c_dominate"] = bool(np.all(fit["B3"] >= fit["Mstar"]) and np.all(fit["B6c"] >= fit["Mstar"]))

    # T4 NEES: residuals drawn with covariance 4 (S + sa^2 I) -> k = ANEES/2 near 4
    ok["T4_nees_k"] = abs(fit["B1_k"]["global"] - 4.0) < 0.15
    out["T4_k"] = fit["B1_k"]["global"]

    # T5 learned scale recovers the planted scale ratio, lateral turning vs lateral straight (2.6 / 1.2), on data with
    # enough turning items
    it5, rc5, mot5 = sim_items(np.random.default_rng(6))
    P5 = M.prepare(it5, rc5, {})
    f5 = M.fit_methods(it5, rc5, P5, np.ones(it5["n_scenes"], bool), {})
    sc5 = np.exp(M.phi(it5, P5["m"], P5["sd"], np.ones(len(it5["D"]), bool)) @ f5["scale_beta"])
    lat = it5["a"] == 1
    ratio = sc5[lat & (mot5 == 2)].mean() / sc5[lat & (mot5 == 1)].mean()
    out["T5_scale_ratio_turn_vs_straight_lat"] = float(ratio)
    ok["T5_scale_ratio"] = abs(ratio / (2.6 / 1.2) - 1) < 0.15

    # T10 eval_stats sanity: huge margins -> 0 exceedance; zero margins with D > 0 -> share of positive D
    ev = [i for i in dense][:6]
    W = M.boot_scene_weights(items, 50, np.random.default_rng(4))
    big = {"X": np.full(len(items["D"]), 1e9), "Y": np.zeros(len(items["D"]))}
    st = M.eval_stats(items, P, big, ev, W)
    l0 = P["lv"][0]
    manual = []
    for g in ev:
        sel = l0 == g
        sh = [np.mean(items["D"][sel & (items["s"] == j)] > 0) for j in np.unique(items["s"][sel])]
        manual.append(np.mean(sh))
    ok["T10_eval_stats"] = (st["methods"]["X"]["E_bar"] == 0.0 and
                            np.allclose([st["methods"]["Y"]["strata"][M.l0_name(g)]["E_scene"] for g in ev], manual))

    # T1 validity of M* (i.i.d. scenes), T2 FWER of the simultaneous bound for an oracle, T3 power for B6 (HM3)
    R = a.reps
    exc, fwer_hits, hm3_hits, hm1_hits = [], 0, 0, 0
    for rep in range(R):
        rr = np.random.default_rng(1000 + rep)
        items, recs, mot = sim_items(rr)
        st, P, marg = fold_eval(items, recs, {}, "rep%d" % rep, B=300)
        exc.append([st["methods"]["Mstar"]["strata"][k]["E_scene"] for k in st["evaluated_strata"]])
        hm1_hits += int(st["hypotheses"]["HM1"])
        hm3_hits += int(st["hypotheses"]["HM3"])
        # oracle: margin at the true 95 % quantile of each item's own distribution
        tau = np.where(items["a"] == 1, np.where(mot == 2, 2.6, np.where(mot == 0, 0.6, 1.2)), np.where(mot == 0, 0.5, 0.9))
        sd = np.sqrt(items["V"] + M.SIGMA_A ** 2)
        orc = {"O": M.Z * tau * sd}
        W = M.boot_scene_weights(items, 300, np.random.default_rng(5000 + rep))
        so = M.eval_stats(items, P, orc, strata_from(st), W)
        fwer_hits += int(so["methods"]["O"]["any_sig_under"])
    exc = np.array(exc)
    out["T1_mean_E_scene_per_stratum"] = exc.mean(0).round(4).tolist()
    out["T1_max_mean"] = float(exc.mean(0).max())
    out["T1_mcse"] = float(exc.std(0, ddof=1).max() / math.sqrt(R))
    ok["T1_validity"] = out["T1_max_mean"] <= M.DELTA + 3 * out["T1_mcse"]
    out["T2_fwer_oracle"] = fwer_hits / R
    ok["T2_fwer"] = out["T2_fwer_oracle"] <= 0.05 + 3 * math.sqrt(0.05 * 0.95 / R)
    out["T3_power_HM3"] = hm3_hits / R
    ok["T3_power"] = out["T3_power_HM3"] >= 0.8
    out["T1b_HM1_rate"] = hm1_hits / R
    ok["T1b_HM1_rate"] = out["T1b_HM1_rate"] >= 0.85

    # T13 log heterogeneity (informational): log random effect sd 0.3
    exl = []
    for rep in range(min(R, 40)):
        items, recs, mot = sim_items(np.random.default_rng(9000 + rep), log_sd=0.3)
        st, _, _ = fold_eval(items, recs, {}, "lrep%d" % rep, B=100)
        exl.append([st["methods"]["Mstar"]["E_bar"], st["methods"]["Mstar_log"]["E_bar"]])
    out["T13_log_effect_mean_Ebar_Mstar_Mstarlog"] = np.mean(exl, 0).round(4).tolist()

    ok = {k: bool(v) for k, v in ok.items()}
    out["ok"] = ok
    out["all_ok"] = all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(ok), "ALL OK" if out["all_ok"] else "SOME FAILED")


def strata_from(st):
    rev = {M.l0_name(i): i for i in range(M.N_L0)}
    return [rev[k] for k in st["evaluated_strata"]]


if __name__ == "__main__":
    sys.exit(main())
