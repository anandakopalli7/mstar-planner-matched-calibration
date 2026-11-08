#!/usr/bin/env python3
"""Tests of the joint arm M*J (Claude line, test_k8_joint_fit_v02, 2 Nov 2026): k8_joint_fit_v02.py and the v04 copies written
by tests/make_k8_joint_v04.py. Single process, tiny inputs (synthetic data, the 10 development scenes' items, one development
scene's cache); nothing reads a non-development scene.
  J1 CRC bound property on synthetic exchangeable scenes: the fitted lambda meets the bound and is the smallest grid point that
     does; it is the grid ceiling of x1_lib_v03.crc_threshold on the per-decision max ratio; Monte Carlo over 2000 draws of
     n + 1 = 41 scenes: the held-out scene's mean joint loss is <= delta (and not far below: delta - 2 / (n + 1)).
  J2 Monotonicity: the decision, scene and bound are non-increasing in lambda (synthetic and the development items under M*'s
     base); every M* threshold of both trackers is > 0 (all folds, all 8 steps); k8_sim_v04's MstarJ margins are lambda x M*'s
     at the calibrated steps and M*'s after them; on a development scene the planner's infeasible count is non-decreasing in
     lambda (1, 2, 4).
  J3 Schema compatibility: the joint fits keep every key and value of M*'s fits; every fold and step carries the joint keys;
     k8_sim_v02 decides identically with the joint fits and the original fits (B1, B4, Mstar) and raises ValueError for MstarJ
     (why the v04 copies exist); k8_sim_v04 equals k8_sim_v02 on every shared arm (B0, B1, B3, B4, B6, B9, Mstar); with
     lambda = 1 MstarJ decides exactly as Mstar; k8_run_v04's scene job runs Mstar, MstarJ, MstarJx in-process and writes a
     shard; the generator reproduces the three v04 files byte for byte; k8_analyse_v04 lists the joint arms.
  J4 Planted-miscalibration recovery: items whose true scale is kappa x the base (kappa = 1 and 2.5, and kappa = 3 in one of
     three strata only): the fitted lambda recovers the analytic lambda* within 2-3 %, scales with kappa, and out of sample the
     joint loss at lambda is ~delta while at lambda = 1 (M*) it is far above.
  J5 The development fit end to end (--dev, delta 0.2): MstarJ_ip = lambda x Mstar_ip exactly, the bound holds, the grid answer
     equals the ceiling of the continuous CRC for every population, and the output is a superset of M*'s fits.
  J6 k8_analyse_v04.joint_validity and joint_form_b on hand-built decision tables.
  J7 The protected files (v02 / v03 code, the K6 / M libraries, M*'s fits) have the hashes the K8 runs logged, before and after.
  J8 The full fit's inputs on tiny data: two item files merge exactly; the check against M*'s K7 v01 items accepts a reordered
     copy and refuses a changed value; refit_split equals k7_fit_v01.split_fit.
  J9 (v02) The exact CRC is invariant to the scene labelling at an exact tie at delta; relabel_to_order keeps every scene's items;
     the T3 diagnosis (the tie in M*'s fold-4 h2s fit) is as recorded.
Usage (from 50_CODE/k8): python -B tests/test_k8_joint_fit_v02.py <out.json>
"""
import copy
import hashlib
import json
import math
import os
import sys
import time
import traceback

import numpy as np

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K8))
sys.path.insert(0, K8)
sys.path.insert(0, os.path.join(K8, "tests"))
import k8_joint_fit_v02 as J  # noqa: E402
import k8_sim_v02 as S2  # noqa: E402
import k8_sim_v04 as S4  # noqa: E402

DELTA = 0.05
FITS = {t: os.path.join(W_ROOT, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t) for t in ("t1", "t3")}
DEV_ITEMS = {t: os.path.join(W_ROOT, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_%s.npz" % t) for t in ("t1", "t3")}
CACHE = {t: os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_%s_train" % t) for t in ("t1", "t3")}
SCENE = "scene-0757"                       # the smallest development scene
OUT_DIR = os.path.join(W_ROOT, "70_TESTS", "k8_joint_v01", "tests")
# hashes logged by the K8 v02 runs (80_LOGS/k8_expl_v02_*.log, run_record_t3_decide) and the K7 fits
PROTECTED = {os.path.join(K8, "k8_sim_v02.py"): "d646f4205298781b49f78dad4b71a900604076e76fca7fc97b36a858c4ccf2d5",
             os.path.join(K8, "k8_run_v02.py"): "e5e1e03779427da30f4be190779252c8353e0854bcad82593d8c281b4fdc1183",
             os.path.join(K8, "k8_analyse_v02.py"): "333210a2836492abe76c0825ef2b83409f1d4d44096eb23826ff1b9054be5ce5",
             os.path.join(K8, "k8_analyse_v03.py"): "868e4ff028e2e04072b2508dad57c0c3b29b4c030b34f9acff350ce7083c810a",
             os.path.join(W_ROOT, "50_CODE", "k6", "k6_sim_v02.py"): "257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4",
             os.path.join(W_ROOT, "50_CODE", "k6", "k6_analyse_v02.py"): "9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61",
             os.path.join(W_ROOT, "50_CODE", "m", "m_lib_v04.py"): "6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5",
             FITS["t1"]: "02409ec6df29b371c08092ed8977dc7a293933ad0eeb3135e73a5cee319c48f3",
             FITS["t3"]: "8f455eddb700a3ccdc7d999653e735720c068c0753b493b6b9bdb97229a59d5d"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- synthetic data

def gen_R(rng, n_scenes, kappa=1.0):
    """Exchangeable scenes: 1 + Poisson(15) decisions, each the max ratio of 1 + Poisson(10) items with a scene-level spread;
    returns (scene of decision, R)."""
    nd = 1 + rng.poisson(15, n_scenes)
    sig = rng.uniform(0.3, 0.8, n_scenes)
    sc = np.repeat(np.arange(n_scenes), nd)
    m = 1 + rng.poisson(10, len(sc))
    zmax = _norm_ppf(rng.uniform(size=len(sc)) ** (1.0 / m))      # the max of m standard normals
    return sc, kappa * np.exp(sig[sc] * zmax)


def _norm_ppf(u):
    from scipy.stats import norm
    return norm.ppf(np.clip(u, 1e-15, 1 - 1e-15))


def synth_items(rng, n_scenes, n_dec, m, kappa_of_stratum, base_of_stratum):
    """Synthetic items in the k8_items_v02 layout: n_dec decisions per scene, m items per decision, each in one of the strata
    (L0 = stratum id, step 0, not in path unless drawn), base c = base_of_stratum, true U = kappa x c x W with W ~ Exp(1)."""
    ns = len(base_of_stratum)
    N = n_scenes * n_dec * m
    s = np.repeat(np.arange(n_scenes), n_dec * m)
    k = np.tile(np.repeat(np.arange(n_dec), m), n_scenes)
    l0 = rng.integers(0, ns, N)
    W = rng.exponential(1.0, N)
    sd = rng.uniform(0.2, 2.0, N)
    U = np.asarray(kappa_of_stratum)[l0] * np.asarray(base_of_stratum)[l0] * W
    it = {"s": s, "k": k, "h": np.zeros(N, int), "l0": l0, "inpath": rng.uniform(size=N) < 0.1, "sd": sd, "D": U * sd,
          "gap": rng.uniform(0, 20, N), "ref_relied": np.ones(N, bool)}
    base_f = np.ones((J.CC_STEPS, 2 * J.N_L0))
    for c_ in range(ns):
        base_f[:, c_] = base_of_stratum[c_]
        base_f[:, c_ + J.N_L0] = base_of_stratum[c_]
    return it, base_f


def lam_star_exp(kappas, weights, m, delta_eff):
    """Analytic lambda*: P(max of m items' ratio > lam) = delta_eff with a ratio kappa_s x Exp(1) in stratum s (prob weights)."""
    lo, hi = 1e-6, 1e4
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        p_le = sum(w * (1 - math.exp(-mid / k)) for k, w in zip(kappas, weights))
        if 1 - p_le ** m > delta_eff:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


# ---------------------------------------------------------------- tests

def t_j1():
    rng = np.random.default_rng(20261102)
    out = {}
    sc, R = gen_R(rng, 300)
    r = J.crc_grid(sc, R, DELTA)
    b, _ = J.crc_bound(sc, R, r["lam"])
    lc = J.crc_continuous(sc, R, DELTA)
    exp = J.GRID[np.searchsorted(J.GRID, lc - 1e-12)]
    out["fit_n300"] = {"lam": r["lam"], "bound": b, "bound_prev": r["bound_at_previous_grid_point"], "continuous": lc}
    assert b <= DELTA and r["bound_at_previous_grid_point"] > DELTA, "lambda is not the smallest grid point meeting the bound"
    assert abs(exp - r["lam"]) < 1e-9, "grid answer is not the ceiling of crc_threshold"
    # Monte Carlo: n = 40 calibration scenes + 1 held out, exchangeable
    n, reps = 40, 2000
    test_loss, lams = np.empty(reps), np.empty(reps)
    for i in range(reps):
        sc, R = gen_R(rng, n + 1)
        cal = sc < n
        rr = J.crc_grid(sc[cal], R[cal], DELTA)
        lams[i] = rr["lam"]
        test_loss[i] = np.mean(R[~cal] > rr["lam"])
    m_, se = float(test_loss.mean()), float(test_loss.std(ddof=1) / math.sqrt(reps))
    out["monte_carlo"] = {"n": n, "reps": reps, "mean_test_loss": m_, "se": se, "lam_mean": float(lams.mean()),
                          "upper_check": "mean <= delta + 3 se", "lower_check": "mean >= delta - 2 / (n + 1) - 3 se"}
    assert m_ <= DELTA + 3 * se, "held-out joint loss above delta"
    assert m_ >= DELTA - 2.0 / (n + 1) - 3 * se, "held-out joint loss implausibly far below delta"
    return out


def t_j2():
    rng = np.random.default_rng(7)
    out = {}
    sc, R = gen_R(rng, 200)
    grid = J.GRID[::25]
    prev_L, prev_b = None, None
    for lam in grid:
        _, Ls = J.scene_losses(sc, R, lam)
        b, _ = J.crc_bound(sc, R, lam)
        if prev_L is not None:
            assert np.all(Ls <= prev_L + 1e-15) and b <= prev_b + 1e-15, "not monotone at %g" % lam
        prev_L, prev_b = Ls, b
    out["synthetic_grid_points"] = int(len(grid))
    # every M* threshold of both trackers is > 0 (monotonicity of U > lambda c in lambda)
    mins = {}
    for t, p in FITS.items():
        f = json.load(open(p))
        vals = []
        for fo in f["fits"].values():
            for st in J.STEPS:
                vals.append(np.asarray(fo[st]["Mstar_ip"] if "Mstar_ip" in fo[st] else fo[st]["Mstar"], float))
        mins[t] = float(np.min(np.concatenate(vals)))
        assert mins[t] > 0, "a non-positive M* threshold in " + t
    out["min_Mstar_threshold"] = mins
    # the development items under M*'s fold-0 base
    fits = json.load(open(FITS["t1"]))
    it, names, _ = J.load_items([DEV_ITEMS["t1"]])
    base = J.base_array(fits)[0]
    for p in J.POPS:
        sel = J.pop_mask(it, p)
        s_, Rr = J.joint_R(it, sel, J.base_of_items(base, it, sel))
        prev = None
        for lam in J.GRID[::50]:
            _, Ls = J.scene_losses(s_, Rr, lam)
            if prev is not None:
                assert np.all(Ls <= prev + 1e-15), "dev items: not monotone in " + p
            prev = Ls
    out["dev_items_monotone"] = True
    # k8_sim_v04 margins: MstarJ = lambda x Mstar at the calibrated steps, Mstar after them
    jf = json.load(open(os.path.join(OUT_DIR, "j5v2_dev_fits_t1.json")))
    ratios = {}
    for fo in range(5):
        steps = [jf["fits"][str(fo)][st] for st in J.STEPS]
        lam = jf["fits"][str(fo)]["h0p5s"]["MstarJ_lambda"]
        nJ = 50
        g, r = rng.integers(0, 4, nJ), rng.integers(0, 3, (nJ, 8))
        sd = rng.uniform(0.1, 3.0, (nJ, 8, 2))
        l0 = rng.integers(0, 96, (nJ, 8, 2))
        inp = rng.uniform(size=nJ) < 0.3
        mM = S4.margins("Mstar", steps, g, r, sd, l0, inp)
        mJ = S4.margins("MstarJ", steps, g, r, sd, l0, inp)
        assert np.allclose(mJ[:, :4], lam * mM[:, :4], rtol=1e-12, atol=0) and np.array_equal(mJ[:, 4:], mM[:, 4:]), "MstarJ margins"
        ratios[str(fo)] = lam
    out["sim_v04_margins_lambda_by_fold"] = ratios
    # planner: infeasible count non-decreasing in lambda on one development scene
    sc4 = S4.Scene(os.path.join(CACHE["t1"], SCENE + ".npz"))
    fits_f = [fits["fits"][str(fits["fold_of_scene"][SCENE])][st] for st in J.STEPS]
    inf = {}
    for lam in (1.0, 2.0, 4.0):
        ff = copy.deepcopy(fits_f)
        for h in range(J.CC_STEPS):
            ff[h]["MstarJ_ip"] = (lam * np.asarray(ff[h]["Mstar_ip"])).tolist()
        for h in range(J.CC_STEPS, 8):
            ff[h]["MstarJ"] = ff[h]["Mstar"]
        o, _ = S4.run_decisions(sc4, "MstarJ", ff)
        inf[lam] = o["infeasible_frames"]
    assert inf[1.0] <= inf[2.0] <= inf[4.0], "infeasible count not monotone in lambda: %s" % inf
    out["planner_infeasible_by_lambda_" + SCENE] = {str(k): v for k, v in inf.items()}
    return out


def _canon(o, c):
    """A comparable form of run_decisions' (summary, counts)."""
    o = dict(o)
    decs = o.pop("decisions", None)
    cal = o.pop("cal", None)
    o.pop("arm", None)
    d = None if decs is None else {k: np.asarray(v).tolist() for k, v in decs.items()}
    return json.dumps([o, d, {str(k): v for k, v in sorted((cal or {}).items())}, {str(k): v for k, v in sorted(c.items())}],
                      sort_keys=True, default=float)


def _deep_subset(a, b, path=""):
    """Every key of a is in b with an equal value (b may have more keys)."""
    if isinstance(a, dict):
        assert isinstance(b, dict), path
        for k, v in a.items():
            assert k in b, "missing key " + path + "/" + k
            _deep_subset(v, b[k], path + "/" + k)
    else:
        assert a == b, "value differs at " + path


def t_j3():
    out = {}
    fits = json.load(open(FITS["t1"]))
    jf = json.load(open(os.path.join(OUT_DIR, "j5v2_dev_fits_t1.json")))
    _deep_subset(fits, jf)
    out["joint_fits_superset_of_Mstar_fits"] = True
    for fo in range(5):
        for h, st in enumerate(J.STEPS):
            e = jf["fits"][str(fo)][st]
            if h < J.CC_STEPS:
                assert len(e["MstarJ_ip"]) == 192 and len(e["MstarJx_ip"]) == 192 and all(x > 0 for x in e["MstarJ_ip"] + e["MstarJx_ip"])
            else:
                assert len(e["MstarJ"]) == 96 and len(e["MstarJx"]) == 96
    out["joint_keys_every_fold_and_step"] = True
    fold = fits["fold_of_scene"][SCENE]
    steps = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]        # k8_run_v02._scene_job's reading
    f_orig = [fits["fits"][str(fold)][h] for h in steps]
    f_joint = [jf["fits"][str(jf["fold_of_scene"][SCENE])][h] for h in steps]
    sc2 = S2.Scene(os.path.join(CACHE["t1"], SCENE + ".npz"))
    sc4 = S4.Scene(os.path.join(CACHE["t1"], SCENE + ".npz"))
    same = {}
    for arm in ("B1", "B4", "Mstar"):
        a_ = _canon(*S2.run_decisions(sc2, arm, f_orig))
        b_ = _canon(*S2.run_decisions(sc2, arm, f_joint))
        same["v02_orig_vs_joint_fits_" + arm] = a_ == b_
        assert a_ == b_, "k8_sim_v02 decides differently with the joint fits: " + arm
    try:
        S2.run_decisions(sc2, "MstarJ", f_joint)
        raised = False
    except ValueError:
        raised = True
    assert raised, "k8_sim_v02 accepted MstarJ"
    out["v02_raises_for_MstarJ"] = True
    for arm in ("B0", "B1", "B3", "B4", "B6", "B9", "Mstar"):
        fa = None if arm in S2.FITFREE else f_orig
        a_ = _canon(*S2.run_decisions(sc2, arm, fa))
        b_ = _canon(*S4.run_decisions(sc4, arm, f_joint if fa is not None else None))
        same["v04_equals_v02_" + arm] = a_ == b_
        assert a_ == b_, "k8_sim_v04 differs from k8_sim_v02 on " + arm
    f_one = copy.deepcopy(f_orig)
    for h in range(J.CC_STEPS):
        f_one[h]["MstarJ_ip"] = list(f_one[h]["Mstar_ip"])
    for h in range(J.CC_STEPS, 8):
        f_one[h]["MstarJ"] = list(f_one[h]["Mstar"])
    a_ = _canon(*S4.run_decisions(sc4, "Mstar", f_one))
    b_ = _canon(*S4.run_decisions(sc4, "MstarJ", f_one))
    assert a_ == b_, "MstarJ at lambda = 1 differs from Mstar"
    same["MstarJ_lambda1_equals_Mstar"] = True
    out["identical"] = same
    # k8_run_v04's scene job, in-process (no pool)
    import k8_run_v04 as R4
    shard_dir = os.path.join(OUT_DIR, "j3_shards")
    os.makedirs(shard_dir, exist_ok=True)
    R4._init(os.path.join(OUT_DIR, "j5v2_dev_fits_t1.json"))
    scene, sp, n_ep, dt = R4._scene_job((os.path.join(CACHE["t1"], SCENE + ".npz"), SCENE, ["Mstar", "MstarJ", "MstarJx"], [0, 2, 4],
                                         "decide", shard_dir, {"tag": "j3"}))
    z = np.load(sp)
    eps = json.loads(str(z["episodes"]))
    assert [o["arm"] for o in eps] == ["Mstar", "MstarJ", "MstarJx"] and n_ep == 3
    out["run_v04_scene_job"] = {"episodes": n_ep, "decisions": int(len(z["dec_k"])),
                                "infeasible_frames": {o["arm"]: o["infeasible_frames"] for o in eps}, "seconds": round(dt, 1)}
    # the generator reproduces the v04 files
    import make_k8_joint_v04 as MK
    for src, dst, fn in (("k8_sim_v02.py", "k8_sim_v04.py", MK.make_sim), ("k8_run_v02.py", "k8_run_v04.py", MK.make_run),
                         ("k8_analyse_v03.py", "k8_analyse_v04.py", MK.make_analysis)):
        with open(os.path.join(K8, src), encoding="utf-8", newline="") as f:
            gen = fn(f.read())
        with open(os.path.join(K8, dst), encoding="utf-8", newline="") as f:
            assert f.read() == gen, "the generator does not reproduce " + dst
    out["generator_reproduces_v04"] = True
    import k8_analyse_v04 as A4
    assert all(a in A4.ALL_ARMS for a in S4.JOINT_ARMS) and A4.S is S4
    out["analyse_v04_arms_include_joint"] = True
    return out


def t_j4():
    rng = np.random.default_rng(11)
    out = {}
    n, nd, m = 3000, 10, 10
    d_eff = (DELTA * (n + 1) - 1) / n                       # the in-sample level the CRC bound allows
    lam = {}
    for kappa in (1.0, 2.5):
        it, base_f = synth_items(rng, n, nd, m, [kappa] * 3, [0.5, 1.0, 2.0])
        sel = J.pop_mask(it, "PD7_primary")
        s_, R = J.joint_R(it, sel, J.base_of_items(base_f, it, sel))
        r = J.crc_grid(s_, R, DELTA)
        ls = lam_star_exp([kappa], [1.0], m, d_eff)
        lam[kappa] = r["lam"]
        out["kappa_%g" % kappa] = {"lam_hat": r["lam"], "lam_star": ls, "rel_err": abs(r["lam"] - ls) / ls}
        assert abs(r["lam"] - ls) / ls < 0.02, "lambda does not recover the planted scale %g" % kappa
    out["ratio_2.5_over_1"] = lam[2.5] / lam[1.0]
    assert abs(lam[2.5] / lam[1.0] - 2.5) < 0.06, "lambda does not scale with the planted miscalibration"
    # miscalibration planted in one stratum of three; the full fit_lambda over the three populations
    kap = [3.0, 1.0, 1.0]
    it, base_f = synth_items(rng, n, nd, m, kap, [0.5, 1.0, 2.0])
    lam_f, by_pop, binding = J.fit_lambda(it, np.ones(n, bool), base_f, DELTA, J.GRID)
    ls = lam_star_exp(kap, [1 / 3.0] * 3, m, d_eff)
    out["one_stratum_kappa3"] = {"lam_hat": lam_f, "lam_star_PD7": ls, "binding": binding,
                                 "lam_by_pop": {p: by_pop[p]["lam"] for p in J.POPS}}
    assert abs(by_pop["PD7_primary"]["lam"] - ls) / ls < 0.03, "one-stratum miscalibration not recovered"
    it2, _ = synth_items(rng, n, nd, m, kap, [0.5, 1.0, 2.0])
    sel = J.pop_mask(it2, "PD7_primary")
    s_, R = J.joint_R(it2, sel, J.base_of_items(base_f, it2, sel))
    _, L_hat = J.scene_losses(s_, R, lam_f)
    _, L_one = J.scene_losses(s_, R, 1.0)
    out["one_stratum_kappa3"]["oos_joint_loss_at_lam"] = float(L_hat.mean())
    out["one_stratum_kappa3"]["oos_joint_loss_at_1_Mstar"] = float(L_one.mean())
    assert abs(L_hat.mean() - DELTA) < 0.01 and L_one.mean() > 0.5, "out-of-sample joint loss"
    return out


def t_j5():
    out = {}
    os.makedirs(OUT_DIR, exist_ok=True)
    for t in ("t1", "t3"):
        p = os.path.join(OUT_DIR, "j5v2_dev_fits_%s.json" % t)
        J.main(["--fits", FITS[t], "--items", DEV_ITEMS[t], "--out", p, "--dev", "--delta", "0.2"])
        jf = json.load(open(p))
        fits = json.load(open(FITS[t]))
        _deep_subset(fits, jf)
        meta = jf["joint"]
        assert meta["dev"] and meta["stamp"].startswith("DEV MODE")
        lam_by = {}
        for fo, r in meta["fit"]["folds"].items():
            for arm in J.JOINT_ARMS:
                lam = r[arm]["lambda"]
                assert lam >= 1.0 and not r[arm]["none_qualifies_grid_max_used"]
                for p_, v in r[arm]["by_population"].items():
                    if v["empty"]:
                        continue
                    assert v["bound"] <= 0.2 + 1e-12 and v["grid_equals_ceil_of_continuous"], (t, fo, arm, p_)
                lam_by["%s_%s" % (fo, arm)] = lam
            for h in range(J.CC_STEPS):
                F, E = fits["fits"][fo][J.STEPS[h]], jf["fits"][fo][J.STEPS[h]]
                assert E["MstarJ_ip"] == (r["MstarJ"]["lambda"] * np.asarray(F["Mstar_ip"], float)).tolist()
        out[t] = {"sha256": sha(p), "lambda": lam_by}
    return out


def t_j6():
    import k8_analyse_v04 as A4
    A = A4.A
    rng = np.random.default_rng(5)
    old = (A.MIN_SCENES, A.MIN_LOGS)
    A.MIN_SCENES, A.MIN_LOGS = 39, 8
    try:
        n_keys, n_dec, n_logs = 80, 12, 16
        kix = np.repeat(np.arange(n_keys), n_dec)
        log_of_ep = np.arange(n_keys) % n_logs
        scene_of_ep = np.array(["s%03d" % i for i in range(n_keys)])
        W_logs = rng.multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=2000).astype(float)
        W = W_logs[:, log_of_ep]
        out = {}
        jv = {}
        for name, p in (("good", 0.02), ("bad", 0.30)):
            st = np.zeros((len(kix), 4, A4.NF), np.float32)
            st[:, 3, A4.SI["n"]] = 1.0                         # one near in-path record per decision: PD7, SD1_7 and PD alike
            st[:, 3, A4.SI["x"]] = (rng.uniform(size=len(kix)) < p).astype(np.float32)
            rows = {"stats": st.reshape(len(kix), -1), "ob": np.zeros(len(kix), np.int8)}
            v = A4.joint_validity(rows, kix, n_keys, W, scene_of_ep, log_of_ep)
            jv[name] = v
            out[name] = {q: {k: v["pops"][q].get(k) for k in ("E", "lb_one_sided_0.95", "ub_one_sided_0.95", "flagged", "valid")}
                         for q in A4.CONF_POPS}
        assert jv["good"]["valid"] and not jv["bad"]["valid"] and jv["bad"]["pops"]["PD7_primary"]["flagged"]
        rate = {"MstarJ": np.full(n_keys, 0.5), "Mstar": np.full(n_keys, 0.2), "B4": np.full(n_keys, 0.6)}
        Ws = W_logs[:, log_of_ep]
        fb = A4.joint_form_b(rate, Ws, {"MstarJ": jv["good"], "Mstar": jv["bad"], "B4": jv["good"]}, ["MstarJ", "Mstar", "B4"], "MstarJ")
        assert fb["comparators_valid_on_joint_loss"] == ["B4"] and fb["met"] and fb["lower_than_every_valid_comparator"]["B4"]["lower"]
        fb2 = A4.joint_form_b(rate, Ws, {"MstarJ": jv["good"], "Mstar": jv["good"], "B4": jv["bad"]}, ["MstarJ", "Mstar", "B4"], "MstarJ")
        assert not fb2["met"], "MstarJ is more infeasible than a valid M*: Form B must fail"
        out["form_B_joint"] = {"met_when_only_B4_valid": fb["met"], "met_when_Mstar_valid_and_less_infeasible": fb2["met"]}
        return out
    finally:
        A.MIN_SCENES, A.MIN_LOGS = old


def t_j8():
    """The full fit's input path on tiny data: the development items split into two files merge back exactly (load_items, as the
    full fit merges the 840-scene and the 10-scene files); check_against_k7_items accepts a K7-v01-layout copy (another scene order,
    the fits carrying its hash) and refuses one changed value; refit_split equals k7_fit_v01.split_fit on synthetic items."""
    import k7_fit_v01 as K7F
    out = {}
    z = np.load(DEV_ITEMS["t1"])
    names = np.array([str(x) for x in z["scene_names"]])
    it_all, nm_all, _ = J.load_items([DEV_ITEMS["t1"]])
    parts = []
    for half, sc_ids in (("a", np.arange(0, 5)), ("b", np.arange(5, 10))):
        keep = np.isin(z["item_s"], sc_ids)
        remap = np.full(len(names), -1)
        remap[sc_ids] = np.arange(len(sc_ids))
        d = {("item_" + f): z["item_" + f][keep] for f in J.ITEM_FIELDS}
        d["item_s"] = remap[z["item_s"][keep]].astype(np.int32)
        p = os.path.join(OUT_DIR, "j8_items_%s.npz" % half)
        np.savez(p, scene_names=names[sc_ids], stamp=np.array("test"), **d)
        parts.append(p)
    it2, nm2, _ = J.load_items(parts[::-1])
    assert list(nm2) == list(nm_all)
    o1, o2 = np.argsort(it_all["s"], kind="stable"), np.argsort(it2["s"], kind="stable")
    for f in J.ITEM_FIELDS:
        assert np.array_equal(it_all[f][o1], it2[f][o2]), "merge differs in " + f
    out["merge_two_files_equal"] = True
    perm = np.random.default_rng(3).permutation(len(names))       # the K7 v01 layout in another scene order
    inv = np.empty_like(perm)
    inv[perm] = np.arange(len(perm))
    order = np.argsort(inv[z["item_s"]], kind="stable")
    v01 = {("item_" + f): z["item_" + f][order] for f in J.K7_V01_FIELDS}
    v01["item_s"] = inv[z["item_s"][order]].astype(np.int32)
    p1 = os.path.join(OUT_DIR, "j8_k7_v01_layout.npz")
    np.savez(p1, scene_names=names[perm], **v01)
    fake_fits = {"items_sha256": sha(p1)}
    chk = J.check_against_k7_items(it_all, nm_all, p1, fake_fits)
    assert all(chk[f] == "equal" for f in J.K7_V01_FIELDS)
    v01["item_D"] = v01["item_D"].copy()
    v01["item_D"][17] += 1e-9
    p2 = os.path.join(OUT_DIR, "j8_k7_v01_layout_changed.npz")
    np.savez(p2, scene_names=names[perm], **v01)
    try:
        J.check_against_k7_items(it_all, nm_all, p2, {"items_sha256": sha(p2)})
        refused = False
    except AssertionError:
        refused = True
    assert refused, "a changed item value was accepted"
    out["k7_items_check_accepts_and_refuses"] = True
    rng = np.random.default_rng(9)
    n = 60000
    it = {"s": rng.integers(0, 45, n), "h": rng.integers(0, 4, n), "g": rng.integers(0, 4, n), "r": rng.integers(0, 3, n),
          "a": rng.integers(0, 2, n), "m": rng.integers(0, 4, n), "inpath": rng.uniform(size=n) < 0.2}
    lv = J.M.levels(it, it["m"])
    U = rng.standard_normal(n) * (1 + it["g"])
    allsc = np.ones(45, bool)
    thr, src = J.refit_split(it, lv, U, allsc, J.N_MIN)
    for h in range(4):
        sel = it["h"] == h
        t_, s_ = K7F.split_fit(U[sel], it["s"][sel], [x[sel] for x in lv], it["inpath"][sel].astype(int), 0)
        assert np.array_equal(t_, thr[h]) and np.array_equal(s_, src[h])
    out["refit_split_equals_k7_split_fit"] = True
    out["refit_fallback_share"] = {str(k): float(np.mean(src == k)) for k in range(4)}
    return out


def t_j9():
    """v02: (a) an exact tie at delta: n = 39 scenes, one scene with joint loss 1 for lam < 5 and the rest 0, so the CRC bound
    is exactly 39/40 x 1/39 + 1/40 = 1/20 on [1, 5); the exact decision accepts lam = 1.00 under every scene labelling (100
    random relabellings); (b) relabel_to_order keeps every scene's items; (c) the T3 diagnosis: the tie found in M*'s fit."""
    out = {}
    n = 39
    sc = np.repeat(np.arange(n), 3)
    R = np.full(len(sc), 0.5)
    R[sc == 0] = 5.0
    lams = set()
    rng = np.random.default_rng(1)
    for _ in range(100):
        perm = rng.permutation(n)
        r = J.crc_grid(perm[sc], R, DELTA)
        lams.add(r["lam"])
    assert lams == {1.0}, "the exact CRC is not invariant to the scene labelling at a tie: %s" % lams
    out["tie_lambda_all_labellings"] = sorted(lams)
    it, names, _ = J.load_items([DEV_ITEMS["t1"]])
    before = {n_: np.sort(it["D"][it["s"] == i]) for i, n_ in enumerate(names)}
    order = list(names[::-1])
    names2 = J.relabel_to_order(it, list(names), order)
    for i, n_ in enumerate(names2):
        assert np.array_equal(np.sort(it["D"][it["s"] == i]), before[n_])
    out["relabel_keeps_scene_items"] = True
    dp = os.path.join(W_ROOT, "70_TESTS", "k8_joint_v01", "diag", "k8_joint_t3_refit_diag_v01.json")
    d = json.load(open(dp))
    e = d["differing_entries"][0]
    assert (d["n_differing"] == 1 and d["k7_v01_items_own_order_reproduces_k7_fits"] and d["k7_v01_items_sorted_name_order_equals_merged_refit"]
            and e["at_thr_refit"]["bound_exact"] == "1/20" and e["at_thr_refit"]["float_ok_merged_order"] and not e["at_thr_refit"]["float_ok_k7_order"])
    out["t3_diag"] = {"entry": e["l0_name"], "inpath": e["inpath"], "thr_k7": e["thr_k7"], "thr_sorted_order": e["thr_refit"],
                      "bound_exact_at_thr_sorted": e["at_thr_refit"]["bound_exact"], "sha256": sha(dp)}
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT_DIR, "k8_joint_tests_v02.json")
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()
    before = {p: sha(p) for p in PROTECTED}
    res = {"protected_before_equal_logged": {os.path.basename(p): before[p] == h for p, h in PROTECTED.items()}}
    ok = all(res["protected_before_equal_logged"].values())
    for name, fn in (("J5_dev_fit", t_j5), ("J1_crc_bound", t_j1), ("J2_monotonicity", t_j2), ("J3_schema", t_j3),
                     ("J4_planted_recovery", t_j4), ("J6_joint_validity", t_j6), ("J8_full_fit_inputs", t_j8),
                     ("J9_tie_and_order", t_j9)):
        t1 = time.time()
        try:
            r = fn()
            res[name] = {"pass": True, "result": r, "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"], flush=True)
    after = {p: sha(p) for p in PROTECTED}
    res["J7_protected_unchanged"] = {"pass": before == after and all(before[p] == h for p, h in PROTECTED.items()),
                                     "files": {os.path.basename(p): after[p] for p in PROTECTED}}
    ok = ok and res["J7_protected_unchanged"]["pass"]
    print("J7_protected_unchanged", "PASS" if res["J7_protected_unchanged"]["pass"] else "FAIL", flush=True)
    res["code_sha256"] = {os.path.basename(p): sha(p) for p in (J.__file__, S4.__file__, os.path.join(K8, "k8_run_v04.py"),
                                                               os.path.join(K8, "k8_analyse_v04.py"), os.path.abspath(__file__),
                                                               os.path.join(K8, "tests", "make_k8_joint_v04.py"))}
    res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t0, 1)
    with open(out_path, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
