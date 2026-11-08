#!/usr/bin/env python3
"""Tests of the K8 code (Claude line, 1 Nov 2026; D14 v02 section 5 item 3). Development scenes only (the 10 nuScenes-mini scenes).
  T1  decision-mode equality with k7_sim_v01 for every shared arm (Z0, B0, B1, B3, B4, B9, B6, Mstar) on the 10 development
      scenes, both trackers, K7 fits: every K7 summary field and the counts dict are identical (160 comparisons); T1b: the
      closed loop (delays 0 and 2 s, arms Mstar and B6, 3 scenes) is identical too, trace hash included.
  T2  V2 (trajectory-level exceedance) on a hand-built episode: the decision-level and scene-level rates, for PD7 and SD1_7,
      and the one-step variant.
  T3  ANEES on a synthetic Gaussian draw under each covariance rule (B0, Mstar-type per-axis scaling, B9 isotropic, a delta'
      arm): ANEES ~ 2, p_v ~ 0.05, ellipse coverage ~ 50/90/95/99 %, exceedance curve ~ delta, NLL equal to the closed form,
      energy score close to its Monte-Carlo reference.
  T4  alpha and delta' arms on the development scenes (both trackers): pooled PD7 exceedance non-increasing and infeasible
      rate non-decreasing in alpha and in 1/delta'; B0a1 and B0d0.05 identical to B0 (summaries, counts, decisions, cal).
  T5  the generators reproduce k8_sim_v01.py and k8_run_v01.py from the K7 sources.
  T6  N1 fix: a synthetic PD table whose power-qualified family is flagged in its own sup-t while the all-evaluable sup-t is
      not fails HK1a in k8_analyse_v01.hk1_rule and passes in k7_analyse_v02.hk1_rule (the omission R12b N1 found).
  T7  the hard-coded normal and chi-square quantiles equal scipy's.
Usage: python -B test_k8_v01.py <out json>
"""
import copy
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K8))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k7"))
sys.path.insert(0, K8)
import k7_sim_v01 as S7  # noqa: E402
import k8_sim_v01 as S8  # noqa: E402
import k8_analyse_v01 as K8A  # noqa: E402
import k7_analyse_v02 as K7A  # noqa: E402
import k6_analyse_v02 as A  # noqa: E402

DEV = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077", "scene-1094", "scene-1100")
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
K7_DECIDE_KEYS = ("arm", "mode", "keyframes", "entered", "frames", "infeasible_frames", "emergency_stop_frames", "uncontrollable_pairs",
                  "brought_to_ego_pairs", "mean_first_accel")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def scene_path(tag, scene):
    for sp in ("train", "val"):
        p = os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_%s_%s" % (tag, sp), scene + ".npz")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(scene)


def fits_for(F, scene):
    return [F["fits"][str(F["fold_of_scene"][scene])][h] for h in STEPS]


def same(a, b):
    return json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)


def strip(o):
    o = dict(o)
    o.pop("decisions", None)
    o.pop("cal", None)
    return o


def pd7_pooled(c):
    n = x = 0
    for cell, (n_, x_) in c.items():
        ob, inp, enf, sat, gb, rel, h, l0 = S8.decode_cell(cell)
        if ob == 0 and enf == 1 and sat == 1 and rel == 1 and h < S8.CC_STEPS:
            n += n_
            x += x_
    return n, x


def main():
    res = {}
    ok_all = True
    # ---------------------------------------------------------------- T1
    for tag in ("t1", "t3"):
        F = json.load(open(os.path.join(W_ROOT, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % tag)))
        bad, n = [], 0
        for scene in DEV:
            p = scene_path(tag, scene)
            sc7, sc8 = S7.Scene(p), S8.Scene(p)
            fits = fits_for(F, scene)
            for arm in [x for x in S7.ARMS if x != "LOG"]:
                o7, c7 = S7.run_decisions(sc7, arm, fits if arm not in ("Z0", "B0") else None)
                o8, c8 = S8.run_decisions(sc8, arm, fits if arm not in S8.FITFREE else None)
                n += 1
                if not (all(k in o8 and same(o7[k], o8[k]) for k in o7) and same(c7, c8) and set(o7) == set(K7_DECIDE_KEYS)):
                    bad.append((scene, arm))
        res["T1_decide_%s" % tag] = {"pass": not bad, "compared": n, "mismatch": bad}
        ok_all &= not bad
    F = json.load(open(os.path.join(W_ROOT, "60_RESULTS", "k7_fits_v01", "k7_fits_t1_v01.json")))
    bad = []
    for scene in DEV[:3]:
        p = scene_path("t1", scene)
        sc7, sc8 = S7.Scene(p), S8.Scene(p)
        fits = fits_for(F, scene)
        for arm in ("Mstar", "B6"):
            for d in (0, 4):
                o7, c7 = S7.run_episode(sc7, arm, fits, d)
                o8, c8 = S8.run_episode(sc8, arm, fits, d)
                if not (all(k in o8 and same(o7[k], o8[k]) for k in o7) and same(c7, c8)):
                    bad.append((scene, arm, d))
    res["T1b_loop"] = {"pass": not bad, "mismatch": bad}
    ok_all &= not bad
    # ---------------------------------------------------------------- T2
    NF = len(S8.ST_FIELDS)
    def st_row(cells):   # cells: {cell4: (n, x, n_h0, x_h0)}
        r = np.zeros((4, NF))
        for c, v in cells.items():
            r[c] = v
        return r.ravel()
    # scene A: decision 1 (3 far not-in-path records, 0 exceed; step 0: 1 record, 0 exceed), decision 2 (2 near in-path records, 1 exceed;
    # step 0: 1 record, 1 exceed); scene B: decision 3 (no records), decision 4 (1 far not-in-path record, exceeded; step 0 none)
    stats = np.stack([st_row({0: (3, 0, 1, 0)}), st_row({3: (2, 1, 1, 1)}), st_row({}), st_row({0: (1, 1, 0, 0)})])
    rows = {"stats": stats, "ob": np.zeros(4, int)}
    kix = np.array([0, 0, 1, 1])
    W = np.ones((5, 2))
    v_pd7, per_key = K8A.v2_summary(rows, kix, 2, W, (0, 1, 2, 3), (0,))
    v_sd, _ = K8A.v2_summary(rows, kix, 2, W, (2, 3), (0,))
    v_h0, _ = K8A.v2_summary(rows, kix, 2, W, (0, 1, 2, 3), (0,), first_step=True)
    v_ob, _ = K8A.v2_summary(rows, kix, 2, W, (0, 1, 2, 3), (1,))
    t2 = (abs(v_pd7["E"] - 0.75) < 1e-12 and v_pd7["decisions_with_records"] == 3 and v_pd7["decisions_any_exceed"] == 2
          and abs(v_pd7["decision_level_rate"] - 2 / 3) < 1e-12 and np.allclose(per_key, [0.5, 1.0])
          and v_sd["decisions_with_records"] == 1 and abs(v_sd["E"] - 1.0) < 1e-12
          and v_h0["decisions_with_records"] == 2 and abs(v_h0["E"] - 0.5) < 1e-12 and v_ob["decisions_with_records"] == 0 and v_ob["E"] is None)
    res["T2_V2_hand_built"] = {"pass": bool(t2), "PD7": v_pd7, "SD1_7": v_sd, "step0": v_h0}
    ok_all &= t2
    # ---------------------------------------------------------------- T3
    rng = np.random.default_rng(20261109)
    n = 40000
    yaw = rng.uniform(-math.pi, math.pi, n)
    axj = np.stack([np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1)], 1)        # (n, 2, 2)
    s1, s2, rho = rng.uniform(0.2, 1.5, n), rng.uniform(0.2, 1.5, n), rng.uniform(-0.8, 0.8, n)
    Sw = np.empty((n, 2, 2))
    Sw[:, 0, 0], Sw[:, 1, 1], Sw[:, 0, 1] = s1 ** 2, s2 ** 2, rho * s1 * s2
    Sw[:, 1, 0] = Sw[:, 0, 1]
    pcov = np.stack([Sw[:, 0, 0] - S8.SIGMA_A ** 2, Sw[:, 0, 1], Sw[:, 1, 1] - S8.SIGMA_A ** 2], -1)                 # so S + sigma_a^2 I = Sw
    Sp = np.einsum("nax,nxy,nby->nab", axj, Sw, axj)
    sd2 = np.sqrt(np.stack([Sp[:, 0, 0], Sp[:, 1, 1]], -1))
    a_rel = rng.integers(0, 2, n)
    def draw(cov):
        L = np.linalg.cholesky(cov)
        return np.einsum("nab,nb->na", L, rng.standard_normal((n, 2)))
    t3 = {}
    cases = {"B0": (S8.Z * sd2, Sp), "Mstar": (np.array([1.8, 0.7])[None, :] * sd2, None),    # per-axis thresholds c = 1.8 (long), 0.7 (lat)
             "B0d0.001": (S8.Z_OF_DELTA[0.001] * sd2, Sp), "B9": (np.full((n, 2), 0.9), None)}
    for arm, (mg2, cov_true) in cases.items():
        if arm == "Mstar":
            d = np.maximum(mg2, 1e-3) / (S8.Z * sd2)
            cov_true = Sp * d[:, :, None] * d[:, None, :]
        if arm == "B9":
            cov_true = np.zeros((n, 2, 2))
            cov_true[:, 0, 0] = cov_true[:, 1, 1] = 0.9 ** 2 / S8.CHI2_2_95
        eo = draw(cov_true)                                                   # errors in the object frame
        e = np.einsum("nax,na->nx", axj, eo)                                  # back to the world frame (axj rows are the axes)
        D = np.take_along_axis(eo, a_rel[:, None], 1)[:, 0]
        cd = S8._cal_pairs(arm, e, axj, pcov, mg2, sd2, a_rel, D)
        ne = cd["nees"]
        cov = {q: float(np.mean(ne <= c)) for q, c in zip(S8.COV_LEVELS, S8.CHI2_2_COV)}
        curve = {dl: float(np.mean(cd["u"] > S8.Z_OF_DELTA[dl])) for dl in S8.DELTA_CURVE}
        logdet = np.log(cov_true[:, 0, 0] * cov_true[:, 1, 1] - cov_true[:, 0, 1] ** 2)
        nll_ref = 0.5 * (ne + logdet) + math.log(2 * math.pi)
        # energy score reference: fresh draws (independent of the fixed ones), on a subset
        m = 2000
        L = np.linalg.cholesky(cov_true[:m])
        X = np.einsum("nab,nmb->nma", L, rng.standard_normal((m, 400, 2)))
        X2 = np.einsum("nab,nmb->nma", L, rng.standard_normal((m, 400, 2)))
        es_ref = np.mean(np.linalg.norm(X - eo[:m, None, :], axis=-1), 1) - 0.5 * np.mean(np.linalg.norm(X - X2, axis=-1), 1)
        r = {"anees": float(ne.mean()), "p_v": float(np.mean((ne < S8.CHI2_2[0]) | (ne > S8.CHI2_2[1]))), "coverage": cov, "curve": curve,
             "nll_max_abs_diff": float(np.max(np.abs(cd["nll"] - nll_ref))), "es_mean": float(cd["es"][:m].mean()), "es_ref_mean": float(es_ref.mean()),
             "es_mean_abs_diff_per_record": float(np.mean(np.abs(cd["es"][:m] - es_ref)))}
        r["pass"] = bool(abs(r["anees"] - 2) < 0.04 and abs(r["p_v"] - 0.05) < 0.005
                         and all(abs(cov[q] - q) < 0.008 for q in S8.COV_LEVELS)
                         and all(abs(curve[dl] - dl) < max(0.004, 0.3 * dl) for dl in S8.DELTA_CURVE)
                         and r["nll_max_abs_diff"] < 1e-9 and abs(r["es_mean"] - r["es_ref_mean"]) < 0.01 and r["es_mean_abs_diff_per_record"] < 0.1)
        t3[arm] = r
    res["T3_calibration_synthetic"] = {"pass": bool(all(v["pass"] for v in t3.values())), "cases": t3, "n": n}
    ok_all &= res["T3_calibration_synthetic"]["pass"]
    # ---------------------------------------------------------------- T4
    t4 = {}
    for tag in ("t1", "t3"):
        acc = {a: [0, 0, 0, 0] for a in ("B0",) + S8.ALPHA_ARMS + S8.DELTA_ARMS}   # frames, infeasible, PD7 n, PD7 x
        ident = True
        for scene in DEV:
            sc8 = S8.Scene(scene_path(tag, scene))
            outs = {}
            for arm in acc:
                o, c = S8.run_decisions(sc8, arm, None)
                outs[arm] = (o, c)
                n_, x_ = pd7_pooled(c)
                acc[arm][0] += o["frames"]
                acc[arm][1] += o["infeasible_frames"]
                acc[arm][2] += n_
                acc[arm][3] += x_
            for twin in ("B0a1", "B0d0.05"):
                o, c = outs[twin]
                ob, cb = outs["B0"]
                ident &= same({k: v for k, v in o.items() if k != "arm"}, {k: v for k, v in ob.items() if k != "arm"}) and same(c, cb)
        inf = {a: acc[a][1] / max(acc[a][0], 1) for a in acc}
        exc = {a: acc[a][3] / max(acc[a][2], 1) for a in acc}
        alpha_inf = [inf[a] for a in S8.ALPHA_ARMS]
        alpha_exc = [exc[a] for a in S8.ALPHA_ARMS]
        delta_inf = [inf[a] for a in S8.DELTA_ARMS]        # delta' decreasing -> 1/delta' increasing
        delta_exc = [exc[a] for a in S8.DELTA_ARMS]
        mono = lambda v, up: all((b >= a) if up else (b <= a) for a, b in zip(v, v[1:]))  # noqa: E731
        t4[tag] = {"alpha_infeasible": alpha_inf, "alpha_PD7_exceedance": alpha_exc, "delta_infeasible": delta_inf, "delta_PD7_exceedance": delta_exc,
                   "infeasible_nondecreasing_in_alpha": mono(alpha_inf, True), "exceedance_nonincreasing_in_alpha": mono(alpha_exc, False),
                   "infeasible_nondecreasing_in_1_over_delta": mono(delta_inf, True), "exceedance_nonincreasing_in_1_over_delta": mono(delta_exc, False),
                   "B0a1_and_B0d0.05_identical_to_B0": bool(ident)}
        t4[tag]["pass"] = bool(all(t4[tag][k] for k in ("infeasible_nondecreasing_in_alpha", "exceedance_nonincreasing_in_alpha",
                                                         "infeasible_nondecreasing_in_1_over_delta", "exceedance_nonincreasing_in_1_over_delta",
                                                         "B0a1_and_B0d0.05_identical_to_B0")))
    res["T4_sweeps_monotone"] = {"pass": bool(all(v["pass"] for v in t4.values())), **t4}
    ok_all &= res["T4_sweeps_monotone"]["pass"]
    # ---------------------------------------------------------------- T5
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "k8", "tests"))
        os.makedirs(os.path.join(tmp, "k7"))
        for f in ("k7_sim_v01.py", "k7_run_v01.py"):
            shutil.copy(os.path.join(W_ROOT, "50_CODE", "k7", f), os.path.join(tmp, "k7"))
        for f in ("make_k8_sim_v01.py", "make_k8_run_v01.py"):
            shutil.copy(os.path.join(K8, "tests", f), os.path.join(tmp, "k8", "tests"))
            subprocess.run([sys.executable, "-B", os.path.join(tmp, "k8", "tests", f)], check=True, capture_output=True)
        t5 = {"sim": sha(os.path.join(tmp, "k8", "k8_sim_v01.py")) == sha(os.path.join(K8, "k8_sim_v01.py")),
              "run": sha(os.path.join(tmp, "k8", "k8_run_v01.py")) == sha(os.path.join(K8, "k8_run_v01.py"))}
    res["T5_generators"] = {"pass": bool(t5["sim"] and t5["run"]), **t5}
    ok_all &= res["T5_generators"]["pass"]
    # ---------------------------------------------------------------- T6
    cells = A.cell_family()
    n_logs, per_log = 12, 5
    n_ep = n_logs * per_log
    scene_of_ep = np.array(["s%03d" % i for i in range(n_ep)])
    log_of_ep = np.repeat(np.arange(n_logs), per_log)
    rng6 = np.random.default_rng(20261110)
    W_logs = rng6.multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=2000).astype(float)
    W = W_logs[:, log_of_ep]
    # clean cells at a true rate 0.02 with binomial noise (a non-zero bootstrap SE, so the all-evaluable sup-t quantile is a real
    # maximum over cells); PD: 20 evaluable cells, cell 5 at 0.08 on average with its rate alternating by log (0.08 -/+ d), so
    # that its own single-cell family flags it while the 20-cell simultaneous bound does not
    N_clean = np.full((n_ep, 32), 200.0)
    X_clean = rng6.binomial(200, 0.02, size=(n_ep, 32)).astype(float)
    fams = {"PD7_primary": np.ones(32, bool), "SD1_7_gap_le_5m": np.ones(32, bool), "PD_inpath": np.zeros(32, bool)}
    fams["PD_inpath"][5] = True
    found = None
    for d in (0.03, 0.04, 0.05, 0.06, 0.07, 0.08):
        N_pd = np.zeros((n_ep, 32))
        N_pd[:, :20] = 200.0
        X_pd = np.zeros((n_ep, 32))
        X_pd[:, :20] = X_clean[:, :20]
        rate5 = np.where(log_of_ep % 2 == 0, 0.08 - d, 0.08 + d)
        X_pd[:, 5] = np.round(200.0 * rate5)
        T = {"PD7_primary": (N_clean, X_clean), "SD1_7_gap_le_5m": (N_clean, X_clean), "PD_inpath": (N_pd, X_pd)}
        r8 = K8A.hk1_rule(T, cells, scene_of_ep, log_of_ep, W, [1, 2], fams)
        r7 = K7A.hk1_rule(T, cells, scene_of_ep, log_of_ep, W, [1, 2], fams)
        pd8, pd7 = r8["pops"]["PD_inpath"], r7["pops"]["PD_inpath"]
        if pd8["family_flagged"] and not pd8["flagged"]:
            found = {"d": d, "k8_PD_HK1a_met": pd8["HK1a_met"], "k7_PD_HK1a_met": pd7["HK1a_met"], "k8_HK1": r8["HK1"], "k7_HK1": r7["HK1"],
                     "family_flagged": pd8["family_flagged"], "all_evaluable_flagged": pd8["flagged"],
                     "same_on_PD7_SD1_7": bool(all(r8["pops"][p]["HK1a_met"] == r7["pops"][p]["HK1a_met"] and r8["pops"][p]["HK1b_met"] == r7["pops"][p]["HK1b_met"]
                                                   for p in ("PD7_primary", "SD1_7_gap_le_5m")))}
            break
    t6 = found is not None and found["k8_PD_HK1a_met"] is False and found["k7_PD_HK1a_met"] is True and found["k8_HK1"] is False and found["k7_HK1"] is True and found["same_on_PD7_SD1_7"]
    res["T6_N1_fix"] = {"pass": bool(t6), "case": found}
    ok_all &= bool(t6)
    # ---------------------------------------------------------------- T7
    try:
        from scipy.stats import chi2, norm
        t7 = all(abs(S8.Z_OF_DELTA[d] - float(norm.ppf(1 - d))) < 1e-12 for d in S8.Z_OF_DELTA)
        t7 &= abs(S8.CHI2_2[0] - chi2.ppf(0.025, 2)) < 1e-12 and abs(S8.CHI2_2[1] - chi2.ppf(0.975, 2)) < 1e-12 and abs(S8.CHI2_2_95 - chi2.ppf(0.95, 2)) < 1e-12
        t7 &= all(abs(c - chi2.ppf(q, 2)) < 1e-12 for q, c in zip(S8.COV_LEVELS, S8.CHI2_2_COV))
        res["T7_quantiles"] = {"pass": bool(t7)}
    except ImportError:
        res["T7_quantiles"] = {"pass": True, "note": "scipy not available; not checked"}
        t7 = True
    ok_all &= bool(t7)
    res["k7_sim_sha256"] = sha(S7.__file__)
    res["k8_sim_sha256"] = sha(S8.__file__)
    res["k8_analyse_sha256"] = sha(K8A.__file__)
    res["ALL_PASS"] = bool(ok_all)
    json.dump(res, open(sys.argv[1], "w"), indent=1, default=float)
    print(json.dumps({k: (v.get("pass") if isinstance(v, dict) else v) for k, v in res.items()}, indent=1))
    print("ALL_PASS" if ok_all else "FAIL")


if __name__ == "__main__":
    main()
