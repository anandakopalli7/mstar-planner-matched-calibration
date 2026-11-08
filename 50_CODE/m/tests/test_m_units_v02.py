#!/usr/bin/env python3
"""Unit and Monte Carlo tests of m_lib_v02 on simulated item tables (Claude line, v02, 31 Oct 2026). Simulated data only.
v02 follows R07: seeds from zlib.crc32 (m15), checks of the new parts (cells, paired contrasts, zero-SE rule, refit-CV
folds, B9, B10), and the size criterion reported as a number (M5).
Usage: python test_m_units_v02.py --reps 200 --out <json>
"""
import argparse
import json
import math
import os
import sys
import zlib

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m_lib_v02 as M  # noqa: E402

TAU = lambda g_, a_, m_: np.where(a_ == 1, np.where(m_ == 2, 2.6, np.where(m_ == 0, 0.6, 1.2)), np.where(m_ == 0, 0.5, 0.9))


def rng_of(label):
    return np.random.default_rng([M.SEED, zlib.crc32(label.encode())])


def sim_items(rng, n_logs=50, scenes_per_log=14, tau=TAU, log_sd=0.0, items_per_scene=40, turn_share=0.15):
    """Strata car/pedestrian x {<20, 20-40} x {long, lat} x {static, straight, turning, new}; U = tau(stratum) N(0,1)
    (+ a log effect); sd = 0.3-0.8 m; D = U sd. Records for B1/B9: residual covariance 4 (S + sa^2 I)."""
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


def names_logs(items):
    names = ["sc%04d" % i for i in range(items["n_scenes"])]
    return names, {nm: "log%03d" % items["scene_log_idx"][i] for i, nm in enumerate(names)}


def one_cv_fixed(items, recs, label, B=300):
    """One 5-fold log split, fixed-rule inference on E1 cells with the standard paired contrasts."""
    P = M.prepare(items, recs, {})
    names, slog = names_logs(items)
    folds, _ = M.log_folds(names, slog)
    exc, marg, src = M.cv_once(items, recs, P, {}, folds)
    cells = M.make_cells(items, P["m"], "E1")
    st = M.eval_stats(items, P, marg, cells, M.boot_scene_weights(items, B, rng_of(label)), exc_frac=exc, pairs=M.standard_pairs(cells))
    return st, P, marg, exc, cells, src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=200)
    a = ap.parse_args()
    out, ok = {}, {}

    it = {"g": np.array([0, 0, 0, 0, 0, 1, 1]), "spd": np.array([0.5, 2, 2, 2, 0.2, 2, 2]),
          "om": np.array([0.5, 0.05, -0.2, np.nan, np.nan, 0.5, 0.0]), "omv": np.array([0, 0, 0, 0, 0, 0.0, 0.5])}
    ok["T11_motion_state_default"] = M.motion_state(it).tolist() == [0, 1, 2, 3, 0, 1, 2]
    ok["T11b_motion_state_yaw_all"] = M.motion_state(it, omega="om").tolist() == [0, 1, 2, 3, 0, 2, 1]
    ok["T12_wrap_half"] = abs(M.wrap_half(math.pi - 0.01)) < 0.02 and abs(M.wrap_half(0.3) - 0.3) < 1e-12

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
    neg = M.deploy_covariance(np.eye(2), 0.0, -1.0, 1.0)
    ok["T6_PM2"] = worst < 1e-9 and np.linalg.eigvalsh(neg).min() > 0

    names = ["sc%d" % i for i in range(700)]
    rs = np.random.default_rng(2)
    slog = {nm: "log%d" % min(49, int(rs.integers(0, 50))) for nm in names}
    folds, load = M.log_folds(names, slog)
    disjoint = all(len({folds[i] for i, nm in enumerate(names) if slog[nm] == lg}) == 1 for lg in set(slog.values()))
    out["T7_fold_loads"] = load
    ok["T7_folds"] = disjoint and sum(load) == 700 and max(load) - min(load) <= max(np.unique(list(slog.values()), return_counts=True)[1])

    items, recs, mot = sim_items(np.random.default_rng(3), turn_share=0.01)
    mult = np.random.default_rng(5).multinomial(items["n_logs"], np.full(items["n_logs"], 1 / items["n_logs"]))
    tb, tbr = M.resample_logs(items, recs, mult)
    fb = M.folds_by_original_log(tb, seed=9)
    orig_scene_log = tb["orig_log"][tb["scene_log_idx"]]
    ok["T7b_refit_folds"] = all(len(set(fb[orig_scene_log == o])) == 1 for o in np.unique(orig_scene_log)) and \
        np.array_equal(items["scene_log_idx"][tb["orig_scene"]], orig_scene_log) and len(set(fb)) == M.K_FOLDS

    P = M.prepare(items, recs, {})
    fit = M.fit_methods(items, recs, P, np.ones(items["n_scenes"], bool), {})
    cnt = M.counts_by_l0(items, P["m"])
    sparse = [i for i in range(M.N_L0) if M.l0_name(i) in cnt and cnt[M.l0_name(i)]["scenes"] < M.N_CRC]
    dense = [i for i in range(M.N_L0) if M.l0_name(i) in cnt and cnt[M.l0_name(i)]["scenes"] >= M.N_CRC]
    ok["T8_fallback"] = bool(sparse) and all(fit["Mstar_src"][i] >= 1 for i in sparse) and all(fit["Mstar_src"][i] == 0 for i in dense)
    ok["T9_B3_B6c_dominate"] = bool(np.all(fit["B3"] >= fit["Mstar"]) and np.all(fit["B6c"] >= fit["Mstar"]))
    ok["T4_nees_k"] = abs(fit["B1_k"]["global"] - 4.0) < 0.15
    out["T4_k"] = fit["B1_k"]["global"]
    nrm = np.hypot(recs["dx"], recs["dy"])
    ok["T20_B9_radius"] = abs(np.mean(nrm > fit["B9"]) - 0.05) < 0.01
    out["T20_B9_in_sample_exceedance"] = float(np.mean(nrm > fit["B9"]))

    it5, rc5, mot5 = sim_items(np.random.default_rng(6))
    P5 = M.prepare(it5, rc5, {})
    f5 = M.fit_methods(it5, rc5, P5, np.ones(it5["n_scenes"], bool), {})
    sc5 = np.exp(M.phi(it5, P5["m"], P5["sd"], np.ones(len(it5["D"]), bool)) @ f5["scale_beta"])
    lat = it5["a"] == 1
    ratio = sc5[lat & (mot5 == 2)].mean() / sc5[lat & (mot5 == 1)].mean()
    out["T5_scale_ratio_turn_vs_straight_lat"] = float(ratio)
    ok["T5_scale_ratio"] = abs(ratio / (2.6 / 1.2) - 1) < 0.15

    cells = M.make_cells(it5, P5["m"], "E1")
    l0 = P5["lv"][0]
    lgs = it5["scene_log_idx"][it5["s"]]
    ok["T17_cells"] = all(len(np.unique(it5["s"][np.isin(l0, ids)])) >= 39 and len(np.unique(lgs[np.isin(l0, ids)])) >= 8 for _, ids in cells) \
        and len({x for _, ids in cells for x in ids}) == sum(len(ids) for _, ids in cells)
    W = M.boot_scene_weights(it5, 60, np.random.default_rng(4))
    big = {"X": np.full(len(it5["D"]), 1e9), "Y": np.zeros(len(it5["D"])), "Zm": np.full(len(it5["D"]), -1e9)}
    single = [(n, ids) for n, ids in cells if len(ids) == 1][:6]
    st = M.eval_stats(it5, P5, big, single, W, pairs=[("Y", "X", list(range(len(single))), "Y-X")])
    manual = [np.mean([np.mean(it5["D"][(l0 == ids[0]) & (it5["s"] == j)] > 0) for j in np.unique(it5["s"][l0 == ids[0]])]) for _, ids in single]
    ok["T10_eval_stats"] = st["methods"]["X"]["E_bar"] == 0.0 and np.allclose([st["methods"]["Y"]["cells"][n]["E_scene"] for n, _ in single], manual)
    ok["T18_paired"] = all(abs(v["diff"] - st["methods"]["Y"]["cells"][c]["E_scene"]) < 1e-12 and v["positive"] for c, v in st["paired"]["Y-X"]["cells"].items())
    ok["T19_zero_se_flag"] = all(v["sig_under"] for v in st["methods"]["Zm"]["cells"].values()) and not st["methods"]["X"]["any_sig_under"]

    st6, P6, marg6, exc6, cells6, src6 = one_cv_fixed(it5, rc5, "cv-check", B=50)
    ok["T22_cv_once_all_held_out"] = bool(np.all(src6 >= 0))
    out["T21_B10_mean_E"] = st6["methods"]["B10"]["E_bar"]
    out["T21_Mstar_mean_E"] = st6["methods"]["Mstar"]["E_bar"]

    R = a.reps
    exc_cells, fl_m, fwer, hm3 = [], 0, 0, 0
    for rep in range(R):
        it, rc, mot = sim_items(np.random.default_rng(1000 + rep))
        st, P, marg, exc, cells, _ = one_cv_fixed(it, rc, "rep%d" % rep, B=300)
        exc_cells.append([st["methods"]["Mstar"]["cells"][n]["E_scene"] for n, ids in cells if len(ids) == 1])
        fl_m += int(st["methods"]["Mstar"]["any_sig_under"])
        hm3 += int(bool(M.failures([st], "B6", "B6-Mstar|car turning")))
        sd = np.sqrt(it["V"] + M.SIGMA_A ** 2)
        orc = {"O": M.Z * TAU(it["g"], it["a"], mot) * sd}
        so = M.eval_stats(it, P, orc, cells, M.boot_scene_weights(it, 300, rng_of("oracle%d" % rep)))
        fwer += int(so["methods"]["O"]["any_sig_under"])
    exc_cells = np.array(exc_cells)
    out["T1_max_mean_E"] = float(exc_cells.mean(0).max())
    out["T1_mcse"] = float(exc_cells.std(0, ddof=1).max() / math.sqrt(R))
    ok["T1_validity"] = out["T1_max_mean_E"] <= M.DELTA + 3 * out["T1_mcse"]
    out["T2_size_oracle"] = fwer / R
    ok["T2_size_not_anticonservative"] = out["T2_size_oracle"] <= 0.08
    out["T1b_Mstar_flag_rate"] = fl_m / R
    ok["T1b_Mstar_flag_rate"] = out["T1b_Mstar_flag_rate"] <= 0.10
    out["T3_power_HM3_paired"] = hm3 / R
    ok["T3_power"] = out["T3_power_HM3_paired"] >= 0.8

    ok = {k: bool(v) for k, v in ok.items()}
    out["ok"], out["all_ok"] = ok, all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(ok), "ALL OK" if out["all_ok"] else "SOME FAILED")


if __name__ == "__main__":
    sys.exit(main())
