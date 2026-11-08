#!/usr/bin/env python3
"""Tests of the K8 v02 code (Claude line, 1 Nov 2026; D14 v04 section 5 item 2). Development scenes only (the 10 nuScenes-mini
scenes); nothing here reads or simulates a non-development scene (the exploratory paths are exercised by dry runs and by
binding checks on synthetic records that carry scene NAMES only).
  T1   decision-mode equality with k7_sim_v01 for every shared arm (Z0, B0, B1, B3, B4, B9, B6, Mstar) on the 10 development
       scenes, both trackers (160 comparisons); T1b the closed loop (Mstar, B6; delays 0 and 2 s; 3 scenes), trace hash included;
       T1c k8_sim_v02 equals k8_sim_v01 on every arm both have (21 arms x 10 scenes x 2 trackers): every v01 per-decision field
       (ttc -> ttc_proxy_v01), the first 4 relied-on fields per cell, the calibration table, the counts and the summaries.
  T2   V2 on a hand-built episode with the v02 layout: rates, the reference 1 - (1 - delta)^n_tracks, n_tracks per cell set,
       the variants (viol, near, binding, exec, dedup) and the one-step check.
  T3   synthetic Gaussian draws: k8_sim_v02._cal_pairs under the covariance rules (ANEES ~ 2, p_v ~ 0.05, coverage, curve, NLL,
       energy score) and the A6 item summaries (a6_summary on synthetic items: ANEES, median NEES ~ chi2_2 median, trimmed
       ANEES, p_v below/above, coverage, gross count).
  T4   on the development scenes, both trackers: along the one curve (12 alpha + 9 delta' points ordered by alpha_eq) the
       pooled PD7 exceedance is non-increasing and the infeasible rate non-decreasing; B0a1 = B0d0.05 = B0; B0d0.5 decides as
       Z0 (zero margin).
  T5   the generators reproduce k8_sim_v02.py, k8_run_v02.py, k8_items_v02.py; the v01 files are unchanged (R15's hashes).
  T6   N1 fix (as v01) in k8_analyse_v02.hk1_rule.
  T7   the hard-coded quantiles (normal, chi-square, alpha_eq, GROSS_NEES) equal scipy's.
  T8   V2 variants against R15's hand re-derivation (70_TESTS/k8_scratch/r15/scripts/v2_hand.py, plain loops): every
       per-decision v02 count (n, x, n_h0, x_h0, v, nb, xb, nd, xd, track counts) of the stored dev run equals the counts
       rebuilt from R15's relied pairs, and the decision-level totals equal r15_v2_variants.json exactly; the executed-margin
       counts (ne, xe) equal a plain-loop re-derivation (relied-on axis at lam * margin, any satisfaction), incl. B3.
  T9   TTV on a hand-built episode (a straight logged path at 10 m/s and a static in-path car): ttv, ttv_ip, ttv_enf, min_gap and
       min_gap_ip equal the hand values for every decision where the leash-following plan is feasible; ttv_from_pair_gaps on
       hand arrays (first violation, clip, empty).
  T10  cross-fitted retuning on a synthetic monotone curve: the selection per fold equals the hand answer (a bad fold moves the
       others' choice), boundary flags (lower, upper, none_qualifies); add_composite_arm copies the right rows.
  T11  Form A uses exactly B0, B1, B4, B9 at 1 - 0.05/4 (Z0 and the sweep arms never), the all-arm contrast is descriptive;
       Form B applies one validity rule to M* and every comparator (an invalid M* fails B even when it is lower).
  T12  exploratory dry runs of k8_run_v02 (decide and loop) and k8_items_v02 (in process, with open / np.load / Pool / Scene
       instrumented): no cache file other than the manifests is opened, nothing is simulated, the listed scenes are the 840
       non-development scenes, the launch record carries the current hashes; the analysis' exploratory binding accepts a
       well-formed synthetic record set and refuses a changed hash, a development scene, a dry run and an incomplete design.
  T13  --allow-dev guard: the analysis accepts the DEV MODE dev runs and refuses an exploratory record, a record or an episode
       with a non-development scene; the runner refuses --dev with a non-development scene name before reading any cache.
  T14  per-scene shards: k8_run_v02 --dev on 2 scenes x 3 arms (decide) and 1 scene (loop) equals in-process k8_sim_v02 output
       array for array; --resume reuses the shards and reproduces the files byte for byte.
  T15  k8_items_v02 --dev reproduces every K7 item and record field of k7_items_v02 (dev items) and its PD7 records are K7's
       ref_relied items; T16 the A6 item NEES / NLL under B0, B4, M*, B9 equal an independent numpy.linalg.solve computation with
       m_lib_v04.deploy_covariance (R15 cal_check's construction).
Usage: python -B test_k8_v02.py <out json> [--workers n]
"""
import builtins
import contextlib
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from multiprocessing import Pool

import numpy as np

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K8))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k7"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, K8)
import k7_sim_v01 as S7  # noqa: E402
import k8_sim_v01 as S1  # noqa: E402
import k8_sim_v02 as S2  # noqa: E402
import k8_analyse_v02 as K8A  # noqa: E402
import k7_analyse_v02 as K7A  # noqa: E402
import k6_analyse_v02 as A  # noqa: E402

DEV = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077", "scene-1094", "scene-1100")
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
K7_DECIDE_KEYS = ("arm", "mode", "keyframes", "entered", "frames", "infeasible_frames", "emergency_stop_frames", "uncontrollable_pairs",
                  "brought_to_ego_pairs", "mean_first_accel")
V01_DEC = ("k", "ob", "infeasible", "lam", "v_now", "v_chosen", "v_log", "ds_plan", "ds_log", "min_gap", "n_enf_tracks")
R15_HASHES = {"k8_sim_v01.py": "c19a8421", "k8_analyse_v01.py": "a7a3e70d", "k8_run_v01.py": "2c4bab2d"}
SCRATCH = os.path.join(W_ROOT, "70_TESTS", "k8_scratch")
DEV_RUNS = os.path.join(SCRATCH, "v02", "dev_v02")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def scene_path(tag, scene):
    assert scene in DEV, "tests read development scenes only"
    for sp in ("train", "val"):
        p = os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_%s_%s" % (tag, sp), scene + ".npz")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(scene)


def caches(tag):
    return [os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_%s_%s" % (tag, sp)) for sp in ("train", "val")]


def fits_file(tag):
    return os.path.join(W_ROOT, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % tag)


def fits_for(F, scene):
    return [F["fits"][str(F["fold_of_scene"][scene])][h] for h in STEPS]


def same(a, b):
    return json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)


def arr_eq(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    return a.shape == b.shape and np.array_equal(a, b, equal_nan=True)


def pd7_pooled(c):
    n = x = 0
    for cell, (n_, x_) in c.items():
        ob, inp, enf, sat, gb, rel, h, l0 = S2.decode_cell(cell)
        if ob == 0 and enf == 1 and sat == 1 and rel == 1 and h < S2.CC_STEPS:
            n += n_
            x += x_
    return n, x


# ---------------------------------------------------------------- T1 / T1c / T4 worker (one tracker x scene)

def _scene_compare(job):
    tag, scene = job
    F = json.load(open(fits_file(tag)))
    p = scene_path(tag, scene)
    sc7, sc1, sc2 = S7.Scene(p), S1.Scene(p), S2.Scene(p)
    fits = fits_for(F, scene)
    out = {"t1_bad": [], "t1_n": 0, "t1c_bad": [], "t1c_n": 0, "acc": {}, "twins": True, "z0_twin": True}
    v2 = {}
    for arm in [x for x in S2.ARMS if x != "LOG"]:
        v2[arm] = S2.run_decisions(sc2, arm, fits if arm not in S2.FITFREE else None)
    for arm in [x for x in S7.ARMS if x != "LOG"]:
        o7, c7 = S7.run_decisions(sc7, arm, fits if arm not in ("Z0", "B0") else None)
        o8, c8 = v2[arm]
        out["t1_n"] += 1
        if not (all(k in o8 and same(o7[k], o8[k]) for k in o7) and same(c7, c8) and set(o7) == set(K7_DECIDE_KEYS)):
            out["t1_bad"].append((tag, scene, arm))
    for arm in [x for x in S1.ARMS if x != "LOG" and x in S2.ARMS]:
        o1, c1 = S1.run_decisions(sc1, arm, fits if arm not in S1.FITFREE else None)
        o2, c2 = v2[arm]
        d1, d2 = o1["decisions"], o2["decisions"]
        ok = all(arr_eq(d1[f], d2[f]) for f in V01_DEC) and arr_eq(d1["ttc"], d2["ttc_proxy_v01"])
        st1 = np.array(d1["stats"], float).reshape(-1, 4, 4)
        st2 = np.array(d2["stats"], float).reshape(-1, 4, len(S2.ST_FIELDS))
        ok &= arr_eq(st1, st2[:, :, :4]) and same(c1, c2) and same(o1["cal"], o2["cal"])
        ok &= all(same(o1[k], o2[k]) for k in o1 if k not in ("decisions", "cal", "ttc_mean", "share_ttc_lt_2s"))
        ok &= (o1.get("ttc_mean") is None and o2.get("ttc_proxy_v01_mean") is None) or abs(o1["ttc_mean"] - o2["ttc_proxy_v01_mean"]) < 1e-12
        out["t1c_n"] += 1
        if not ok:
            out["t1c_bad"].append((tag, scene, arm))
    for arm in ("B0",) + S2.SWEEP_ARMS:
        o, c = v2[arm]
        n_, x_ = pd7_pooled(c)
        out["acc"][arm] = [o["frames"], o["infeasible_frames"], n_, x_]
    for twin in ("B0a1", "B0d0.05"):
        o, c = v2[twin]
        ob, cb = v2["B0"]
        out["twins"] &= same({k: v for k, v in o.items() if k != "arm"}, {k: v for k, v in ob.items() if k != "arm"}) and same(c, cb)
    o, c = v2["B0d0.5"]
    oz, cz = v2["Z0"]
    dz, dd = oz["decisions"], o["decisions"]
    out["z0_twin"] = bool(same(c, cz) and all(arr_eq(dz[f], dd[f]) for f in S2.DEC_FIELDS) and arr_eq(dz["stats"], dd["stats"]))
    return out


def _loop_compare(job):
    scene, arm, d = job
    F = json.load(open(fits_file("t1")))
    p = scene_path("t1", scene)
    o7, c7 = S7.run_episode(S7.Scene(p), arm, fits_for(F, scene), d)
    o8, c8 = S2.run_episode(S2.Scene(p), arm, fits_for(F, scene), d)
    return bool(all(k in o8 and same(o7[k], o8[k]) for k in o7) and same(c7, c8)), (scene, arm, d)


# ---------------------------------------------------------------- T8 helpers: executed-margin plain-loop re-derivation

def exec_pairs(S, sc, arm, fits, k):
    """Plain-loop re-derivation of the executed-margin records of one decision (R15 m9): the chosen plan and lam from plan_step,
    then per (calibrated step, paired track with ground truth) the relied-on axis at lam * margin (argmax of G - lam * mg),
    G > 0 on it, enforced (C8 at reference margin 0), any satisfaction; exceedance D > lam * mg."""
    tk = float(sc.kf_t[k])
    s, v = float(sc.s_log(tk)), max(sc.v_log(tk), 0.0)
    vmax = sc.v_log_max + 2.0
    ps = S.plan_step(sc, arm, fits, k, s, v, vmax, sc.s_log, {}, 0, None, None)
    lam = 0.0 if ps["lam"] is None else float(ps["lam"])
    rows = sc.tr_by_k[k]
    if not len(rows):
        return ps, []
    ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
    cxe, cye = ex + S.R2C * math.cos(eyaw), ey + S.R2C * math.sin(eyaw)
    tr = sc.tr
    dx, dy = tr["x"][rows] - cxe, tr["y"][rows] - cye
    sel = rows[(np.hypot(dx, dy) < S.R_CONSIDER) & (dx * math.cos(eyaw) + dy * math.sin(eyaw) >= -S.EGO_L / 2)]
    if not len(sel):
        return ps, []
    g, r, m, sd, l0, ax = S.strata(sc, sel, k, *S.sensor_ctrv(sc, k))
    mg = S.margins(arm, fits, g, r, sd, l0, tr["inpath"][sel])
    pred_xy = tr["pred"][sel][:, :, :2]
    splan = np.minimum(S.plan_positions(s, v, vmax), sc.s_log(tk + S.EVAL_T)[None, :])
    cur = np.stack([tr["x"][sel], tr["y"][sel]], -1)[:, None, :]
    prev = np.concatenate([cur, pred_xy[:, :-1]], 1)
    xy16 = np.empty((len(sel), S.N_EVAL, 2))
    xy16[:, 1::2] = pred_xy
    xy16[:, 0::2] = 0.5 * (prev + pred_xy)
    half = np.stack([0.5 * tr["l"][sel], 0.5 * tr["w"][sel]], -1)
    gap, sep = S.gaps(sc, splan, xy16, ax, half)
    ghold, _ = S.gaps(sc, np.full((1, S.N_EVAL), s), xy16, ax, half)
    c = ps["choice"]
    out = []
    for h in range(4):
        kk = k + h + 1
        if kk >= sc.K:
            break
        ie = 2 * h + 1
        for j in range(len(sel)):
            inst = int(tr["inst"][sel[j]])
            if inst < 0:
                continue
            grow = sc.gt_at[kk].get(inst)
            if grow is None or (("inrack" in sc.gt) and sc.gt["inrack"][grow]):
                continue
            ctrl = any(max(gap[cc, ie, j, 0], gap[cc, ie, j, 1]) >= 0.0 for cc in range(S.N_C))
            hold = max(ghold[0, ie, j, 0], ghold[0, ie, j, 1]) >= 0.0
            if not (ctrl and hold):
                continue
            G = gap[c, ie, j]
            sl = [G[0] - lam * mg[j, h, 0], G[1] - lam * mg[j, h, 1]]
            rel = int(np.argmax(sl))
            if not G[rel] > 0:
                continue
            e = np.array([sc.gt["x"][grow] - pred_xy[j, h, 0], sc.gt["y"][grow] - pred_xy[j, h, 1]])
            D = float(np.sign(sep[c, ie, j, rel]) * (ax[j, rel] @ e))
            pg = float(max(G[0], G[1]))
            out.append({"cell": int(pg <= 5.0) * 2 + int(tr["inpath"][sel[j]]), "exceed": bool(D > lam * mg[j, h, rel])})
    return ps, out


def _t8_job(job):
    tag, scene, arm = job
    sys.argv = [sys.argv[0], W_ROOT, os.devnull]          # v2_hand reads W and OUT from argv at import
    sys.path.insert(0, os.path.join(SCRATCH, "r15", "scripts"))
    import v2_hand as VH
    F = json.load(open(fits_file(tag)))
    sc = S1.Scene(scene_path(tag, scene))
    fits = None if arm in S1.FITFREE else fits_for(F, scene)
    eps = [json.loads(l) for l in open(os.path.join(DEV_RUNS, "episodes_%s_decide.jsonl" % tag))]
    Dz = np.load(os.path.join(DEV_RUNS, "decisions_%s_decide.npz" % tag))
    ep = [o for o in eps if o["scene"] == scene and o["arm"] == arm][0]["episode"]
    rows = np.flatnonzero(Dz["episode"] == ep)
    nf = len(S2.ST_FIELDS)
    fi = {f: i for i, f in enumerate(S2.ST_FIELDS)}
    agg = {"V2_margin": 0, "V2_violation": 0, "V2_near_margin": 0, "V2_binding_margin": 0, "dec_with_near": 0, "dec_with_binding": 0,
           "pairs": 0, "pairs_violation": 0, "pairs_binding": 0, "pairs_binding_exceed": 0, "decisions_with_records": 0}
    bad, bad_exec, n_dec = [], [], 0
    for row in rows:
        k = int(Dz["k"][row])
        ps, pairs, _ = VH.relied_pairs(sc, arm, fits, k)
        st = np.zeros((4, nf))
        trk = np.zeros(6)
        seen = set()
        tracks = {}
        for p_ in pairs:
            c4 = p_["near"] * 2 + p_["inpath"]
            ex = float(p_["exceed"])
            st[c4, fi["n"]] += 1
            st[c4, fi["x"]] += ex
            if p_["h"] == 0:
                st[c4, fi["n_h0"]] += 1
                st[c4, fi["x_h0"]] += ex
            st[c4, fi["v"]] += float(p_["D"] > p_["G_rel"])
            if p_["G_rel"] - p_["margin"] <= 0.5:
                st[c4, fi["nb"]] += 1
                st[c4, fi["xb"]] += ex
            if (p_["h"], p_["inst"]) not in seen:
                seen.add((p_["h"], p_["inst"]))
                st[c4, fi["nd"]] += 1
                st[c4, fi["xd"]] += ex
            tracks.setdefault(p_["j"], [p_["inpath"], set()])[1].add(p_["near"])
        for j, (ip, ns) in tracks.items():
            trk[3 * ip + (2 if ns == {0, 1} else (1 if ns == {1} else 0))] += 1
        stored = Dz["stats"][row].astype(float).reshape(4, nf)
        cols = [fi[f] for f in ("n", "x", "n_h0", "x_h0", "v", "nb", "xb", "nd", "xd")]
        if not (np.array_equal(stored[:, cols], st[:, cols]) and np.array_equal(Dz["trk"][row].astype(float), trk)):
            bad.append((scene, arm, k))
        n_dec += 1
        if pairs:
            agg["decisions_with_records"] += 1
            agg["pairs"] += len(pairs)
            agg["V2_margin"] += any(p["exceed"] for p in pairs)
            agg["V2_violation"] += any(p["D"] > p["G_rel"] for p in pairs)
            agg["pairs_violation"] += sum(p["D"] > p["G_rel"] for p in pairs)
            near = [p for p in pairs if p["near"]]
            bind = [p for p in pairs if p["G_rel"] - p["margin"] <= 0.5]
            agg["pairs_binding"] += len(bind)
            agg["pairs_binding_exceed"] += sum(p["exceed"] for p in bind)
            agg["dec_with_near"] += bool(near)
            agg["dec_with_binding"] += bool(bind)
            agg["V2_near_margin"] += any(p["exceed"] for p in near)
            agg["V2_binding_margin"] += any(p["exceed"] for p in bind)
        # the executed margin, plain loops (with k8_sim_v02 geometry: the same functions)
        ps2, ep_ = exec_pairs(S2, sc2_cache(tag, scene), arm, fits, k)
        ste = np.zeros((4, 2))
        for p_ in ep_:
            ste[p_["cell"], 0] += 1
            ste[p_["cell"], 1] += p_["exceed"]
        if not np.array_equal(stored[:, [fi["ne"], fi["xe"]]], ste):
            bad_exec.append((scene, arm, k))
    return {"job": job, "decisions": n_dec, "bad": bad, "bad_exec": bad_exec, "agg": agg}


_SC2 = {}


def sc2_cache(tag, scene):
    if (tag, scene) not in _SC2:
        _SC2[(tag, scene)] = S2.Scene(scene_path(tag, scene))
    return _SC2[(tag, scene)]


# ---------------------------------------------------------------- T9: a hand-built scene

def make_synthetic_scene(path, X0=100.37, v=5.0, T=20.0):
    """A straight logged path along x at v m/s (20 Hz poses), keyframes every 0.5 s, one static in-path car (4 x 2 m) at x = X0,
    unpaired (no ground truth): only the planner and the safety proxies act."""
    t = np.arange(0.0, T + 1e-9, 0.05)
    kf_t = np.arange(0.0, T + 1e-9, 0.5)
    K = len(kf_t)
    z = {"ego_t": t, "ego_x": v * t, "ego_y": np.zeros_like(t), "ego_yaw": np.zeros_like(t), "kf_t": kf_t,
         "kf_ego": np.stack([v * kf_t, np.zeros(K), np.zeros(K)], -1)}
    pred = np.zeros((K, 8, 5))
    pred[:, :, 0], pred[:, :, 2], pred[:, :, 4] = X0, 0.01, 0.01
    tr = {"k": np.arange(K), "x": np.full(K, X0), "y": np.zeros(K), "yaw": np.zeros(K), "l": np.full(K, 4.0), "w": np.full(K, 2.0),
          "pred": pred, "cls": np.zeros(K, int), "spd": np.zeros(K), "omc": np.zeros(K), "inst": np.full(K, -1), "inpath": np.ones(K, bool)}
    for k_, v_ in tr.items():
        z["tr_" + k_] = v_
    for k_, dt in (("k", int), ("inst", int), ("cls", int), ("pts", int), ("x", float), ("y", float), ("yaw", float), ("l", float),
                   ("w", float), ("inrack", bool)):
        z["gt_" + k_] = np.zeros(0, dt)
    np.savez(path, **z)
    return X0, v


# ---------------------------------------------------------------- the instrumented dry run (T12)

class Spy:
    def __init__(self, cache_dirs):
        self.cache_dirs = [os.path.abspath(c) for c in cache_dirs]
        self.opened = []
        self.calls = {"Pool": 0, "Scene": 0, "scene_job": 0, "np_load": 0}

    def in_cache(self, p):
        p = os.path.abspath(str(p))
        return any(p.startswith(c) for c in self.cache_dirs) and not p.endswith("MANIFEST.json")


@contextlib.contextmanager
def instrumented(spy, module):
    o_open, o_load = builtins.open, np.load

    def open_(p, *a, **k):
        if spy.in_cache(p):
            spy.opened.append(str(p))
        return o_open(p, *a, **k)

    def load_(p, *a, **k):
        spy.calls["np_load"] += 1
        if spy.in_cache(p):
            spy.opened.append(str(p))
        return o_load(p, *a, **k)

    def pool_(*a, **k):
        spy.calls["Pool"] += 1
        raise RuntimeError("Pool must not be created in a dry run")

    saved = {}
    builtins.open, np.load = open_, load_
    for name, fn in (("Pool", pool_),):
        saved[name] = getattr(module, name)
        setattr(module, name, fn)
    if hasattr(module, "_scene_job"):
        saved["_scene_job"] = module._scene_job

        def job_(*a, **k):
            spy.calls["scene_job"] += 1
            raise RuntimeError("no scene may be simulated in a dry run")
        module._scene_job = job_
    if hasattr(module, "S") and hasattr(module.S, "Scene"):
        saved["Scene"] = module.S.Scene

        def scene_(*a, **k):
            spy.calls["Scene"] += 1
            raise RuntimeError("no scene may be loaded in a dry run")
        module.S.Scene = scene_
    try:
        yield
    finally:
        builtins.open, np.load = o_open, o_load
        for name, fn in saved.items():
            if name == "Scene":
                module.S.Scene = fn
            else:
                setattr(module, name, fn)


def run_main(module, argv):
    old = sys.argv
    sys.argv = [module.__file__] + list(argv)
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            module.main()
        err = None
    except BaseException as e:   # noqa: BLE001 (assertions and SystemExit are results here)
        err = e
    finally:
        sys.argv = old
    return buf.getvalue(), err


def fake_exploratory_runs(d, nondev_by_tag, mutate=None):
    """Synthetic exploratory run records (scene NAMES only, no data) for the analysis' binding check."""
    import k8_run_v02 as R
    cur = {k + "_sha256": sha(p) for k, p in R.CODE_FILES.items()}
    for tag in ("t1", "t3"):
        for mode in ("decide", "loop"):
            hashes = dict(cur, fits_sha256=sha(fits_file(tag)), manifest_sha256=[sha(os.path.join(c, "MANIFEST.json")) for c in caches(tag)])
            names = list(nondev_by_tag[tag])
            n_ep = len(names) * len(S2.ARMS) * 3 if mode == "loop" else len(names) * (len(S2.ARMS) - 1)
            rec = {"tag": "%s_%s" % (tag, mode), "mode": mode, "prereg": R.EXPLORATORY_STAMP, "exploratory": True, "dry_run": False,
                   "arms": list(S2.ARMS), "delays_kf": [0, 2, 4], "scenes": len(names), "episodes": n_ep, "fits": fits_file(tag),
                   "fits_sha256": hashes["fits_sha256"], "caches": [os.path.abspath(c) for c in caches(tag)], "hashes": hashes, "scene_names": names}
            if mutate:
                mutate(tag, mode, rec)
            launch = {"hashes": rec["hashes"], "dry_run": rec["dry_run"], "exploratory": rec["exploratory"], "launched": "synthetic"}
            lp = os.path.join(d, "launch_record_%s_%s.json" % (tag, mode))
            json.dump(launch, open(lp, "w"))
            rec["launch_record"], rec["launch_record_sha256"] = lp, sha(lp)
            for f, ext in (("episodes", "jsonl"), ("counts", "npz"), ("decisions", "npz"), ("cal", "npz")):
                fp = os.path.join(d, "%s_%s_%s.%s" % (f, tag, mode, ext))
                open(fp, "w").write("synthetic %s %s %s\n" % (f, tag, mode))
                rec["%s_sha256" % f] = sha(fp)
            json.dump(rec, open(os.path.join(d, "run_record_%s_%s.json" % (tag, mode)), "w"))


_RES = {}


def main():
    out_json = sys.argv[1]
    workers = int(sys.argv[sys.argv.index("--workers") + 1]) if "--workers" in sys.argv else 6
    res = _RES
    ok_all = True
    pool = Pool(workers)
    # ---------------------------------------------------------------- T1, T1c, T4 (parallel over tracker x scene)
    outs = pool.map(_scene_compare, [(t, s) for t in ("t1", "t3") for s in DEV], chunksize=1)
    for tag in ("t1", "t3"):
        o_t = [o for (t, s), o in zip([(t, s) for t in ("t1", "t3") for s in DEV], outs) if t == tag]
        bad1 = [b for o in o_t for b in o["t1_bad"]]
        badc = [b for o in o_t for b in o["t1c_bad"]]
        res["T1_decide_%s" % tag] = {"pass": not bad1, "compared": sum(o["t1_n"] for o in o_t), "mismatch": bad1}
        res["T1c_v02_equals_v01_%s" % tag] = {"pass": not badc, "compared": sum(o["t1c_n"] for o in o_t), "mismatch": badc}
        ok_all &= (not bad1) and (not badc)
        acc = {}
        for o in o_t:
            for a_, v_ in o["acc"].items():
                acc.setdefault(a_, np.zeros(4))
                acc[a_] += np.array(v_, float)
        curve = sorted(S2.SWEEP_ARMS, key=lambda a_: (S2.CURVE_ALPHA_OF_ARM[a_], a_))
        inf = [acc[a_][1] / max(acc[a_][0], 1) for a_ in curve]
        exc = [acc[a_][3] / max(acc[a_][2], 1) for a_ in curve]
        mono = lambda v, up, tol=1e-15: all((b >= a - tol) if up else (b <= a + tol) for a, b in zip(v, v[1:]))  # noqa: E731
        sep = {}
        for grid in (S2.ALPHA_ARMS, S2.DELTA_ARMS):     # each grid on its own (v01's T4 form): strict
            g_ = sorted(grid, key=lambda a_: S2.CURVE_ALPHA_OF_ARM[a_])
            sep[grid[0][:3]] = mono([acc[a_][3] / max(acc[a_][2], 1) for a_ in g_], False)
        t4 = {"curve": [(a_, S2.CURVE_ALPHA_OF_ARM[a_], round(i_, 5), round(e_, 6)) for a_, i_, e_ in zip(curve, inf, exc)],
              "max_upward_step_exceedance": float(max([0.0] + [b - a for a, b in zip(exc, exc[1:])])),
              "infeasible_nondecreasing_along_curve": mono(inf, True),
              "exceedance_nonincreasing_per_grid_strict": bool(all(sep.values())),
              "exceedance_nonincreasing_along_curve_strict": mono(exc, False),
              "exceedance_nonincreasing_along_curve_within_1e-4": mono(exc, False, 1e-4),
              "note": "the pooled exceedance is record-weighted over the relied set, which the margin itself selects, so it is not "
                      "monotone by construction; the infeasible rate is. Interleaving the two grids exposes upward steps of 1e-6-2e-5",
              "B0a1_and_B0d0.05_identical_to_B0": bool(all(o["twins"] for o in o_t)), "B0d0.5_decides_as_Z0": bool(all(o["z0_twin"] for o in o_t))}
        t4["pass"] = bool(all(t4[k] for k in ("infeasible_nondecreasing_along_curve", "exceedance_nonincreasing_per_grid_strict",
                                              "exceedance_nonincreasing_along_curve_within_1e-4",
                                              "B0a1_and_B0d0.05_identical_to_B0", "B0d0.5_decides_as_Z0")))
        res["T4_one_curve_monotone_%s" % tag] = t4
        ok_all &= t4["pass"]
    lo = pool.map(_loop_compare, [(s, a_, d) for s in DEV[:3] for a_ in ("Mstar", "B6") for d in (0, 4)], chunksize=1)
    res["T1b_loop"] = {"pass": all(x for x, _ in lo), "mismatch": [j for x, j in lo if not x]}
    ok_all &= res["T1b_loop"]["pass"]
    # ---------------------------------------------------------------- T2
    nf = len(K8A.S.ST_FIELDS)
    fi = K8A.SI

    def st_row(cells):   # {cell4: {field: value}}
        r = np.zeros((4, nf))
        for c, d_ in cells.items():
            for f, v in d_.items():
                r[c, fi[f]] = v
        return r.ravel()
    # scene A: d1 3 far NIP records, 0 exceed (step 0: 1 record), 2 far NIP tracks; d2 2 near IP records, 1 exceed, violated 1,
    # binding 1 (exceeded), executed 2 / 1, one duplicate (dedup 1 / 0); 1 IP track near only. scene B: d3 none; d4 1 far NIP
    # record exceeded (not step 0), executed at lam 0: 2 records 2 exceed; 1 NIP track far only.
    full = lambda n, x, **kw: dict(n=n, x=x, ne=kw.get("ne", n), xe=kw.get("xe", x), nd=kw.get("nd", n), xd=kw.get("xd", x), **{k: v for k, v in kw.items() if k not in ("ne", "xe", "nd", "xd")})  # noqa: E731
    stats = np.stack([st_row({0: full(3, 0, n_h0=1)}), st_row({3: full(2, 1, n_h0=1, x_h0=1, v=1, nb=1, xb=1, nd=1, xd=0)}),
                      st_row({}), st_row({0: full(1, 1, ne=2, xe=2)})])
    trk = np.zeros((4, 6))
    trk[0, 0], trk[1, 4], trk[3, 0] = 2, 1, 1
    rows = {"stats": stats, "ob": np.zeros(4, int), "trk": trk}
    kix = np.array([0, 0, 1, 1])
    W = np.ones((5, 2))
    v_all, pk = K8A.v2_all(rows, kix, 2, W, (0, 1, 2, 3), (0,))
    v_sd, _ = K8A.v2_all(rows, kix, 2, W, (2, 3), (0,))
    v_ob, _ = K8A.v2_all(rows, kix, 2, W, (0, 1, 2, 3), (1,))
    ref1, ref2 = 1 - 0.95 ** 2, 1 - 0.95 ** 1        # d1: 2 tracks; d2: 1 track; d4: 1 track
    e_ref = 0.5 * ((ref1 + ref2) / 2 + ref2)
    nt = K8A.n_tracks(np.array([[1, 2, 3, 4, 5, 6]], float), (0, 1, 2, 3))[0] == 21 and K8A.n_tracks(np.array([[1, 2, 3, 4, 5, 6]], float), (2, 3))[0] == 2 + 3 + 5 + 6 \
        and K8A.n_tracks(np.array([[1, 2, 3, 4, 5, 6]], float), (1,))[0] == 4 + 6 and K8A.n_tracks(np.array([[1, 2, 3, 4, 5, 6]], float), (0, 2))[0] == 6
    t2 = (abs(v_all["V2"]["E"] - 0.75) < 1e-12 and v_all["V2"]["decisions_with_records"] == 3 and v_all["V2"]["decisions_any_exceed"] == 2
          and np.allclose(pk["V2"], [0.5, 1.0]) and abs(v_all["V2"]["reference_E"] - e_ref) < 1e-12
          and abs(v_all["V2"]["mean_tracks_per_decision"] - 4 / 3) < 1e-12
          and abs(v_all["V2_one_step"]["E"] - 0.5) < 1e-12 and v_all["V2_one_step"]["decisions_with_records"] == 2
          and abs(v_all["V2_viol"]["E"] - 0.25) < 1e-12 and abs(v_all["V2_near"]["E"] - 1.0) < 1e-12 and v_all["V2_near"]["decisions_with_records"] == 1
          and abs(v_all["V2_near"]["reference_E"] - ref2) < 1e-12 and abs(v_all["V2_binding"]["E"] - 1.0) < 1e-12
          and v_all["V2_binding"]["decisions_with_records"] == 1 and abs(v_all["V2_exec"]["E"] - 0.75) < 1e-12
          and abs(v_all["V2_dedup"]["E"] - 0.5) < 1e-12 and v_sd["V2"]["decisions_with_records"] == 1 and abs(v_sd["V2"]["E"] - 1.0) < 1e-12
          and v_ob["V2"]["decisions_with_records"] == 0 and v_ob["V2"]["E"] is None and nt)
    pf = K8A.pooled_from_decisions(rows, kix, 2, W, (0, 1, 2, 3), (0,))
    pfd = K8A.pooled_from_decisions(rows, kix, 2, W, (0, 1, 2, 3), (0,), "nd", "xd")
    t2 = t2 and abs(pf["E"] - 0.5 * (1 / 5 + 1.0)) < 1e-12 and abs(pfd["E"] - 0.5 * (0 / 4 + 1.0)) < 1e-12
    res["T2_V2_hand_built"] = {"pass": bool(t2), "V2": v_all, "pooled": pf, "pooled_dedup": pfd}
    ok_all &= bool(t2)
    # ---------------------------------------------------------------- T3
    rng = np.random.default_rng(20261109)
    n = 40000
    yaw = rng.uniform(-math.pi, math.pi, n)
    axj = np.stack([np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1)], 1)
    s1, s2_, rho = rng.uniform(0.2, 1.5, n), rng.uniform(0.2, 1.5, n), rng.uniform(-0.8, 0.8, n)
    Sw = np.empty((n, 2, 2))
    Sw[:, 0, 0], Sw[:, 1, 1], Sw[:, 0, 1] = s1 ** 2, s2_ ** 2, rho * s1 * s2_
    Sw[:, 1, 0] = Sw[:, 0, 1]
    pcov = np.stack([Sw[:, 0, 0] - S2.SIGMA_A ** 2, Sw[:, 0, 1], Sw[:, 1, 1] - S2.SIGMA_A ** 2], -1)
    Sp = np.einsum("nax,nxy,nby->nab", axj, Sw, axj)
    sd2 = np.sqrt(np.stack([Sp[:, 0, 0], Sp[:, 1, 1]], -1))
    a_rel = rng.integers(0, 2, n)

    def draw(cov):
        L = np.linalg.cholesky(cov)
        return np.einsum("nab,nb->na", L, rng.standard_normal((n, 2)))
    t3 = {}
    cases = {"B0": (S2.Z * sd2, Sp), "Mstar": (np.array([1.8, 0.7])[None, :] * sd2, None), "B0a0.03125": (math.sqrt(1 / 32) * S2.Z * sd2, None),
             "B9": (np.full((n, 2), 0.9), None)}
    for arm, (mg2, cov_true) in cases.items():
        if cov_true is None and arm != "B9":
            d = np.maximum(mg2 / sd2, 1e-3) / S2.Z
            cov_true = Sp * d[:, :, None] * d[:, None, :]
        if arm == "B9":
            cov_true = np.zeros((n, 2, 2))
            cov_true[:, 0, 0] = cov_true[:, 1, 1] = 0.9 ** 2 / S2.CHI2_2_95
        eo = draw(cov_true)
        e = np.einsum("nax,na->nx", axj, eo)
        D = np.take_along_axis(eo, a_rel[:, None], 1)[:, 0]
        cd = S2._cal_pairs(arm, e, axj, pcov, mg2, sd2, a_rel, D)
        ne = cd["nees"]
        cov = {q: float(np.mean(ne <= c)) for q, c in zip(S2.COV_LEVELS, S2.CHI2_2_COV)}
        curve = {dl: float(np.mean(cd["u"] > S2.Z_OF_DELTA[dl])) for dl in S2.DELTA_CURVE}
        logdet = np.log(cov_true[:, 0, 0] * cov_true[:, 1, 1] - cov_true[:, 0, 1] ** 2)
        nll_ref = 0.5 * (ne + logdet) + math.log(2 * math.pi)
        m = 2000
        L = np.linalg.cholesky(cov_true[:m])
        X = np.einsum("nab,nmb->nma", L, rng.standard_normal((m, 400, 2)))
        X2 = np.einsum("nab,nmb->nma", L, rng.standard_normal((m, 400, 2)))
        es_ref = np.mean(np.linalg.norm(X - eo[:m, None, :], axis=-1), 1) - 0.5 * np.mean(np.linalg.norm(X - X2, axis=-1), 1)
        # the A6 item summary on the same draws (one scene key per 400 records)
        key = np.arange(n) // 400
        nk = int(key.max()) + 1
        Wk = rng.multinomial(nk, np.full(nk, 1.0 / nk), size=200).astype(float)
        summ = K8A.a6_summary({"nees": ne, "u": cd["u"], "nll": cd["nll"], "es": cd["es"], "mg2": mg2}, np.ones(n, bool), key, nk, Wk)
        r = {"anees": float(ne.mean()), "p_v": float(np.mean((ne < S2.CHI2_2[0]) | (ne > S2.CHI2_2[1]))), "coverage": cov, "curve": curve,
             "nll_max_abs_diff": float(np.max(np.abs(cd["nll"] - nll_ref))), "es_mean": float(cd["es"][:m].mean()), "es_ref_mean": float(es_ref.mean()),
             "a6_anees_scene_level": summ["anees_scene_level"]["mean"], "a6_median": summ["median_nees"], "a6_trimmed": summ["anees_trimmed_1pct"],
             "a6_p_v_below": summ["p_v_below"], "a6_p_v_above": summ["p_v_above"]}
        r["pass"] = bool(abs(r["anees"] - 2) < 0.04 and abs(r["p_v"] - 0.05) < 0.005
                         and all(abs(cov[q] - q) < 0.008 for q in S2.COV_LEVELS)
                         and all(abs(curve[dl] - dl) < max(0.004, 0.3 * dl) for dl in S2.DELTA_CURVE)
                         and r["nll_max_abs_diff"] < 1e-9 and abs(r["es_mean"] - r["es_ref_mean"]) < 0.01
                         and abs(r["a6_anees_scene_level"] - 2) < 0.05 and abs(r["a6_median"] - 2 * math.log(2)) < 0.04
                         and r["a6_trimmed"] < r["anees"] and abs(r["a6_p_v_below"] - 0.025) < 0.004 and abs(r["a6_p_v_above"] - 0.025) < 0.004
                         and summ["records_above_gross_nees"] <= 3)
        t3[arm] = r
    res["T3_calibration_synthetic"] = {"pass": bool(all(v["pass"] for v in t3.values())), "cases": t3, "n": n}
    ok_all &= res["T3_calibration_synthetic"]["pass"]
    # ---------------------------------------------------------------- T5
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        os.makedirs(os.path.join(tmp, "k8", "tests"))
        os.makedirs(os.path.join(tmp, "k7"))
        for f in ("k8_sim_v01.py", "k8_run_v01.py"):
            shutil.copy(os.path.join(K8, f), os.path.join(tmp, "k8"))
        shutil.copy(os.path.join(W_ROOT, "50_CODE", "k7", "k7_items_v02.py"), os.path.join(tmp, "k7"))
        for f in ("make_k8_sim_v02.py", "make_k8_run_v02.py", "make_k8_items_v02.py"):
            shutil.copy(os.path.join(K8, "tests", f), os.path.join(tmp, "k8", "tests"))
            subprocess.run([sys.executable, "-B", os.path.join(tmp, "k8", "tests", f)], check=True, capture_output=True)
        t5 = {f: sha(os.path.join(tmp, "k8", f)) == sha(os.path.join(K8, f)) for f in ("k8_sim_v02.py", "k8_run_v02.py", "k8_items_v02.py")}
    t5.update({"v01_unchanged_" + f: sha(os.path.join(K8, f)).startswith(h) for f, h in R15_HASHES.items()})
    res["T5_generators"] = {"pass": bool(all(t5.values())), **t5}
    ok_all &= res["T5_generators"]["pass"]
    # ---------------------------------------------------------------- T6
    cells = A.cell_family()
    n_logs, per_log = 12, 5
    n_ep = n_logs * per_log
    scene_of_ep = np.array(["s%03d" % i for i in range(n_ep)])
    log_of_ep = np.repeat(np.arange(n_logs), per_log)
    rng6 = np.random.default_rng(20261110)
    W_logs = rng6.multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=2000).astype(float)
    W6 = W_logs[:, log_of_ep]
    N_clean = np.full((n_ep, 32), 200.0)
    X_clean = rng6.binomial(200, 0.02, size=(n_ep, 32)).astype(float)
    fams = {"PD7_primary": np.ones(32, bool), "SD1_7_gap_le_5m": np.ones(32, bool), "PD_inpath": np.zeros(32, bool)}
    fams["PD_inpath"][5] = True
    found = None
    save = (A.MIN_SCENES, A.MIN_LOGS)
    A.MIN_SCENES, A.MIN_LOGS = 39, 8
    for d in (0.03, 0.04, 0.05, 0.06, 0.07, 0.08):
        N_pd = np.zeros((n_ep, 32))
        N_pd[:, :20] = 200.0
        X_pd = np.zeros((n_ep, 32))
        X_pd[:, :20] = X_clean[:, :20]
        rate5 = np.where(log_of_ep % 2 == 0, 0.08 - d, 0.08 + d)
        X_pd[:, 5] = np.round(200.0 * rate5)
        T = {"PD7_primary": (N_clean, X_clean), "SD1_7_gap_le_5m": (N_clean, X_clean), "PD_inpath": (N_pd, X_pd)}
        r8 = K8A.hk1_rule(T, cells, scene_of_ep, log_of_ep, W6, [1, 2], fams)
        r7 = K7A.hk1_rule(T, cells, scene_of_ep, log_of_ep, W6, [1, 2], fams)
        pd8, pd7 = r8["pops"]["PD_inpath"], r7["pops"]["PD_inpath"]
        if pd8["family_flagged"] and not pd8["flagged"]:
            found = {"d": d, "k8_PD_HK1a_met": pd8["HK1a_met"], "k7_PD_HK1a_met": pd7["HK1a_met"], "k8_HK1": r8["HK1"], "k7_HK1": r7["HK1"],
                     "same_on_PD7_SD1_7": bool(all(r8["pops"][p]["HK1a_met"] == r7["pops"][p]["HK1a_met"] and r8["pops"][p]["HK1b_met"] == r7["pops"][p]["HK1b_met"]
                                                   for p in ("PD7_primary", "SD1_7_gap_le_5m")))}
            break
    A.MIN_SCENES, A.MIN_LOGS = save
    t6 = found is not None and found["k8_PD_HK1a_met"] is False and found["k7_PD_HK1a_met"] is True and found["k8_HK1"] is False and found["k7_HK1"] is True and found["same_on_PD7_SD1_7"]
    res["T6_N1_fix"] = {"pass": bool(t6), "case": found}
    ok_all &= bool(t6)
    # ---------------------------------------------------------------- T7
    from scipy.stats import chi2, norm
    t7 = all(abs(S2.Z_OF_DELTA[d] - float(norm.ppf(1 - d))) < 1e-12 for d in S2.Z_OF_DELTA)
    t7 &= abs(S2.CHI2_2[0] - chi2.ppf(0.025, 2)) < 1e-12 and abs(S2.CHI2_2[1] - chi2.ppf(0.975, 2)) < 1e-12 and abs(S2.CHI2_2_95 - chi2.ppf(0.95, 2)) < 1e-12
    t7 &= all(abs(c - chi2.ppf(q, 2)) < 1e-12 for q, c in zip(S2.COV_LEVELS, S2.CHI2_2_COV))
    t7 &= all(abs(S2.ALPHA_EQ_OF_DELTA[d] - (norm.ppf(1 - d) / norm.ppf(0.95)) ** 2) < 1e-12 for d in S2.DELTAS_PRIME)
    t7 &= abs(K8A.GROSS_NEES - chi2.ppf(1 - 1e-6, 2)) < 1e-9
    res["T7_quantiles"] = {"pass": bool(t7)}
    ok_all &= bool(t7)
    # ---------------------------------------------------------------- T8 (R15's hand re-derivation)
    r15 = json.load(open(os.path.join(SCRATCH, "r15", "r15_v2_variants.json")))
    jobs = [(tag, s, a_) for tag, scs in (("t1", ("scene-0061", "scene-0553", "scene-0916", "scene-1077")), ("t3", ("scene-0103", "scene-0655", "scene-0757")))
            for s in scs for a_ in ("Mstar", "B4", "B0", "Z0")]
    jobs += [(t, s, "B3") for t, s in (("t1", "scene-0553"), ("t3", "scene-0103"))]
    t8o = pool.map(_t8_job, jobs, chunksize=1)
    t8 = {"per_decision_mismatch": [b for o in t8o for b in o["bad"]], "executed_margin_mismatch": [b for o in t8o for b in o["bad_exec"]],
          "decisions": sum(o["decisions"] for o in t8o), "vs_r15_json": {}}
    for tag in ("t1", "t3"):
        for a_ in ("Mstar", "B4", "B0", "Z0"):
            agg = {}
            for o in t8o:
                if o["job"][0] == tag and o["job"][2] == a_:
                    for k_, v_ in o["agg"].items():
                        agg[k_] = agg.get(k_, 0) + int(v_)
            ref = r15["%s_%s" % (tag, a_)]
            keys_ = ("V2_margin", "V2_violation", "V2_near_margin", "V2_binding_margin", "dec_with_near", "dec_with_binding", "pairs",
                     "pairs_violation", "pairs_binding", "pairs_binding_exceed", "decisions_with_records")
            t8["vs_r15_json"]["%s_%s" % (tag, a_)] = {"equal": all(agg[k_] == ref[k_] for k_ in keys_), "ours": {k_: agg[k_] for k_ in keys_}}
    t8["pass"] = bool(not t8["per_decision_mismatch"] and not t8["executed_margin_mismatch"] and all(v["equal"] for v in t8["vs_r15_json"].values()))
    res["T8_V2_variants_vs_R15"] = t8
    ok_all &= t8["pass"]
    # ---------------------------------------------------------------- T9 (TTV on a hand-built episode)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        p = os.path.join(tmp, "synthetic_scene.npz")
        X0, vv = make_synthetic_scene(p)
        sc = S2.Scene(p)
        o, _ = S2.run_decisions(sc, "Z0", None)
        dd = o["decisions"]
        checked, bad = 0, []
        for i, k in enumerate(dd["k"]):
            xc = vv * float(sc.kf_t[k]) + S2.R2C
            Dk = X0 - xc - (2.0 + S2.EGO_L / 2 + S2.BUFFER)        # long-axis buffered gap of an ego held at its position
            if not (Dk >= 2.0 * vv + 1e-6 and X0 - xc < S2.R_CONSIDER - 1e-6):
                continue
            first = [t for t in S2.EVAL_T if Dk - vv * t < 0.0]
            ttv = float(first[0]) if first else S2.TTV_CLIP
            ok = (abs(dd["ttv"][i] - ttv) < 1e-9 and abs(dd["ttv_ip"][i] - ttv) < 1e-9 and abs(dd["ttv_enf"][i] - ttv) < 1e-9
                  and math.isnan(dd["ttv_nip"][i]) and abs(dd["min_gap"][i] - (Dk - 2.0 * vv)) < 1e-6 and abs(dd["min_gap_ip"][i] - (Dk - 2.0 * vv)) < 1e-6
                  and math.isnan(dd["min_gap_nip"][i]) and dd["infeasible"][i] == 0 and dd["n_enf_tracks"][i] == 1)
            checked += 1
            if not ok:
                bad.append((int(k), ttv, dd["ttv"][i], Dk))
        pg = np.full((16, 3), 5.0)
        pg[9, 1] = -0.1
        pg[3, 2] = -1.0
        hand = (S2.ttv_from_pair_gaps(pg, [0, 1]) == S2.EVAL_T[9] and S2.ttv_from_pair_gaps(pg, [1, 2]) == S2.EVAL_T[3]
                and S2.ttv_from_pair_gaps(pg, [0]) == S2.TTV_CLIP and S2.ttv_from_pair_gaps(pg, []) is None)
        lt2 = [dd["ttv"][i] for i in range(len(dd["k"])) if np.isfinite(dd["ttv"][i])]
    clip_seen = any(abs(x - S2.TTV_CLIP) < 1e-12 for x in lt2)
    res["T9_TTV_hand_built"] = {"pass": bool(checked >= 10 and not bad and hand and clip_seen), "decisions_checked": checked, "mismatch": bad,
                                "hand_arrays": bool(hand), "ttv_values": sorted(set(round(x, 2) for x in lt2))}
    ok_all &= res["T9_TTV_hand_built"]["pass"]
    # ---------------------------------------------------------------- T10 (cross-fitted retuning)
    alphas = (0.1, 0.25, 0.5, 1.0, 2.0, 4.0)
    nk = 50
    fold = np.repeat(np.arange(5), 10)
    Nk = np.full(nk, 100.0)

    def curve_of(rate_fn):
        cv = []
        for al in alphas:
            tab = {p: (Nk, Nk * rate_fn(al, p)) for p in K8A.CONF_POPS}
            cv.append((al, "a%g" % al, tab))
        return cv
    bad_fold = np.where(fold == 0, 3.0, 1.0)
    s1_ = K8A.crossfit_select(curve_of(lambda al, p: 0.1 * math.exp(-al) * bad_fold), fold)
    s_lower = K8A.crossfit_select(curve_of(lambda al, p: np.full(nk, 0.001)), fold)
    s_none = K8A.crossfit_select(curve_of(lambda al, p: np.full(nk, 0.2)), fold)
    s_upper = K8A.crossfit_select(curve_of(lambda al, p: np.full(nk, 0.04 if al >= 4 else 0.06)), fold)
    s_sd = K8A.crossfit_select(curve_of(lambda al, p: np.full(nk, (0.07 if al < 2 else 0.01) if p == "SD1_7_gap_le_5m" else 0.01)), fold)
    t10 = {"fold0_alpha": s1_[0]["alpha"], "other_folds_alpha": [s1_[f]["alpha"] for f in (1, 2, 3, 4)],
           "selection_ok": bool(s1_[0]["alpha"] == 1.0 and all(s1_[f]["alpha"] == 2.0 for f in (1, 2, 3, 4)) and all(s1_[f]["boundary"] == "interior" for f in range(5))),
           "lower_flag": bool(all(s_lower[f]["boundary"] == "lower" and s_lower[f]["alpha"] == 0.1 and s_lower[f]["boundary_flag"] for f in range(5))),
           "none_flag": bool(all(s_none[f]["boundary"] == "none_qualifies" and s_none[f]["alpha"] == 4.0 for f in range(5))),
           "upper_flag": bool(all(s_upper[f]["boundary"] == "upper" and s_upper[f]["alpha"] == 4.0 for f in range(5))),
           "criterion_uses_SD1_7": bool(all(s_sd[f]["alpha"] == 2.0 for f in range(5)))}
    eps_t = [{"episode": 0, "scene": "a", "arm": "X", "delay_kf": 0}, {"episode": 1, "scene": "a", "arm": "Y", "delay_kf": 0},
             {"episode": 2, "scene": "b", "arm": "X", "delay_kf": 0}, {"episode": 3, "scene": "b", "arm": "Y", "delay_kf": 0}]
    cnt_t = {"episode": np.array([0, 1, 1, 2, 3], np.int32), "cell": np.array([5, 6, 7, 8, 9], np.int32), "n": np.array([1, 2, 3, 4, 5], np.int32),
             "exceed": np.array([0, 1, 1, 0, 2], np.int32)}
    D_t = {"episode": np.array([0, 1, 2, 3, 3], np.int32), "k": np.array([1, 1, 1, 1, 2], np.int32), "stats": np.arange(10, dtype=np.float32).reshape(5, 2),
           "st_fields": np.array(["a", "b"])}
    C_t = {"episode": np.array([1, 2], np.int32), "key": np.array([3, 4], np.int32), "values": np.ones((2, 3)), "fields": np.array(["x", "y", "z"])}
    e2, c2, d2, cc2 = K8A.add_composite_arm(eps_t, cnt_t, D_t, C_t, {"a": "Y", "b": "X"})
    new = [o for o in e2 if o["arm"] == K8A.RETUNED]
    t10["composite_ok"] = bool(len(new) == 2 and [o["composite_of"] for o in new] == ["Y", "X"] and [o["episode"] for o in new] == [4, 5]
                               and c2["episode"][-3:].tolist() == [4, 4, 5] and c2["cell"][-3:].tolist() == [6, 7, 8]
                               and d2["episode"][-2:].tolist() == [4, 5] and d2["stats"][-2:].tolist() == [[2, 3], [4, 5]] and d2["st_fields"].tolist() == ["a", "b"]
                               and cc2["episode"][-2:].tolist() == [4, 5] and cc2["fields"].tolist() == ["x", "y", "z"])
    t10["pass"] = bool(all(v for k_, v in t10.items() if k_.endswith(("_ok", "_flag", "SD1_7"))))
    res["T10_crossfit_retuning"] = t10
    ok_all &= t10["pass"]
    # ---------------------------------------------------------------- T11 (Form A comparator set, Form B symmetric)
    arms11 = ["Z0", "B0", "B1", "B3", "B4", "B9", "B6", "Mstar", "B0a0.25", "B0d0.1", K8A.RETUNED]
    rng11 = np.random.default_rng(5)
    Ws11 = rng11.multinomial(20, np.full(20, 0.05), size=500).astype(float)
    rate11 = {a_: np.full(20, 0.5) for a_ in arms11}
    rate11["Mstar"] = np.full(20, 0.2)
    rate11["Z0"], rate11["B0a0.25"] = np.full(20, 0.01), np.full(20, 0.05)
    valid11 = {a_: False for a_ in arms11}
    valid11.update({"Mstar": True, "B3": True, "B0a0.25": True})
    f11 = K8A.d14_forms(rate11, Ws11, valid11, arms11)
    valid11b = dict(valid11, Mstar=False)
    f11b = K8A.d14_forms(rate11, Ws11, valid11b, arms11)
    t11 = {"A_comparators": f11["A_K6_form"]["comparators"], "A_level": f11["A_K6_form"]["level"],
           "A_set_ok": f11["A_K6_form"]["comparators"] == ["B0", "B1", "B4", "B9"] and abs(f11["A_K6_form"]["level"] - (1 - 0.05 / 4)) < 1e-15,
           "A_met_despite_Z0_and_sweep_lower": bool(f11["A_K6_form"]["met"]),
           "all_arm_descriptive_has_Z0_not_lower": bool(f11["all_arm_contrast_descriptive"]["by_arm"]["Z0"]["lower"] is False),
           "B_passing": f11["B_literature_form"]["comparators_passing_validity"],
           "B_ok": f11["B_literature_form"]["comparators_passing_validity"] == ["B3"] and f11["B_literature_form"]["met"] is True
           and "B0a0.25" not in f11["B_literature_form"]["comparators"] and K8A.RETUNED in f11["B_literature_form"]["comparators"],
           "B_symmetric_invalid_M_fails": f11b["B_literature_form"]["met"] is False and f11b["A_K6_form"]["met"] is False}
    dev_json = os.path.join(SCRATCH, "v02", "dev_v02", "k8_dev_analysis_v02.json")
    if os.path.exists(dev_json):
        dj = json.load(open(dev_json))
        t11["dev_output_A_comparators"] = {t: dj["decide"][t]["d14_forms"]["A_K6_form"]["comparators"] for t in dj["decide"]}
        t11["dev_output_ok"] = all(v == ["B0", "B1", "B4", "B9"] for v in t11["dev_output_A_comparators"].values())
    t11["pass"] = bool(t11["A_set_ok"] and t11["A_met_despite_Z0_and_sweep_lower"] and t11["all_arm_descriptive_has_Z0_not_lower"] and t11["B_ok"]
                       and t11["B_symmetric_invalid_M_fails"] and t11.get("dev_output_ok", True))
    res["T11_forms"] = t11
    ok_all &= t11["pass"]
    # ---------------------------------------------------------------- T12 (exploratory dry runs; binding on synthetic records)
    import k8_run_v02 as R
    import k8_items_v02 as I
    t12 = {}
    nondev = {}
    for tag in ("t1", "t3"):
        nondev[tag] = sorted(s_ for c in caches(tag) for s_ in json.load(open(os.path.join(c, "MANIFEST.json")))["scenes"] if s_ not in DEV)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for tag, mode in (("t1", "decide"), ("t3", "loop")):
            spy = Spy(caches(tag))
            with instrumented(spy, R):
                txt, err = run_main(R, ["--caches", *caches(tag), "--fits", fits_file(tag), "--tag", "%s_%s" % (tag, mode), "--mode", mode,
                                        "--out", tmp, "--exploratory", "--dry-run", "--workers", "6"])
            lr = json.load(open(os.path.join(tmp, "launch_record_%s_%s_DRYRUN.json" % (tag, mode))))
            listed = txt.split("scenes: ", 1)[1].split("\n", 1)[0].split()
            cur = {k + "_sha256": sha(p_) for k, p_ in R.CODE_FILES.items()}
            t12["run_%s_%s" % (tag, mode)] = {
                "error": None if err is None else repr(err), "cache_files_opened": len(spy.opened), "calls": spy.calls,
                "scenes_listed": len(listed), "dev_listed": sorted(set(listed) & set(DEV)), "listed_are_nondev": listed == nondev[tag],
                "launch_dry_run": lr["dry_run"], "launch_hashes_current": all(lr["hashes"][k] == v for k, v in cur.items())
                and lr["hashes"]["fits_sha256"] == sha(fits_file(tag)),
                "no_outputs": not any(f.startswith(("episodes_", "decisions_", "counts_", "cal_", "run_record_", "shards_")) for f in os.listdir(tmp))}
            r_ = t12["run_%s_%s" % (tag, mode)]
            r_["pass"] = bool(err is None and not spy.opened and spy.calls["Pool"] == 0 and spy.calls["scene_job"] == 0 and spy.calls["Scene"] == 0
                              and len(listed) == 840 and not r_["dev_listed"] and r_["listed_are_nondev"] and r_["launch_dry_run"] is True
                              and r_["launch_hashes_current"] and r_["no_outputs"] and "DRY RUN" in txt)
        spy = Spy(caches("t1"))
        with instrumented(spy, I):
            txt, err = run_main(I, ["--caches", *caches("t1"), "--out", os.path.join(tmp, "items_expl_t1.npz"), "--exploratory", "--dry-run"])
        t12["items_t1"] = {"error": None if err is None else repr(err), "cache_files_opened": len(spy.opened), "calls": spy.calls,
                           "no_items_file": not os.path.exists(os.path.join(tmp, "items_expl_t1.npz")), "dry_run_printed": "DRY RUN" in txt,
                           "scenes_840": "840 scenes" in txt}
        t12["items_t1"]["pass"] = bool(err is None and not spy.opened and spy.calls["Pool"] == 0 and t12["items_t1"]["no_items_file"]
                                       and t12["items_t1"]["dry_run_printed"] and t12["items_t1"]["scenes_840"])
    # the analysis' exploratory binding on synthetic records (names only)
    cases12 = {"well_formed": (None, True),
               "sim_hash_changed": (lambda t, m, r: r["hashes"].__setitem__("sim_sha256", "0" * 64) if (t, m) == ("t3", "loop") else None, False),
               "analysis_hash_changed": (lambda t, m, r: r["hashes"].__setitem__("analysis_sha256", "0" * 64) if t == "t1" else None, False),
               "dev_scene_present": (lambda t, m, r: r["scene_names"].__setitem__(0, "scene-0061") if (t, m) == ("t1", "decide") else None, False),
               "dry_run": (lambda t, m, r: r.__setitem__("dry_run", True) if (t, m) == ("t1", "loop") else None, False),
               "incomplete_design": (lambda t, m, r: r.__setitem__("arms", r["arms"][:-1]) if (t, m) == ("t3", "decide") else None, False),
               "dev_record": (lambda t, m, r: r.__setitem__("prereg", R.DEV_STAMP) if (t, m) == ("t1", "decide") else None, False)}
    t12["binding"] = {}
    for name, (mut, expect) in cases12.items():
        with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
            fake_exploratory_runs(tmp, nondev, mut)
            try:
                K8A.check_exploratory(tmp, ["t1", "t3"], ["decide", "loop"])
                got = True
            except AssertionError:
                got = False
        t12["binding"][name] = {"accepted": got, "expected": expect, "ok": got == expect}
    t12["pass"] = bool(all(v["pass"] for k_, v in t12.items() if k_ != "binding") and all(v["ok"] for v in t12["binding"].values()))
    res["T12_exploratory_dry_run_and_binding"] = t12
    ok_all &= t12["pass"]
    # ---------------------------------------------------------------- T13 (--allow-dev guard)
    t13 = {}
    try:
        t13["dev_runs_accepted"] = K8A.check_dev_runs(DEV_RUNS, ["t1", "t3"], ["decide", "loop"])
    except AssertionError as e:
        t13["dev_runs_accepted"] = "refused: %s" % e
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for name, mut in (("exploratory_record", lambda r: r.update(prereg=R.EXPLORATORY_STAMP, exploratory=True)),
                          ("nondev_scene_listed", lambda r: r["scene_names"].append(nondev["t1"][0])),
                          ("not_dev_mode", lambda r: r.update(prereg="0" * 64))):
            for tag in ("t1", "t3"):
                for mode in ("decide", "loop"):
                    r = json.load(open(os.path.join(DEV_RUNS, "run_record_%s_%s.json" % (tag, mode))))
                    if (tag, mode) == ("t3", "loop"):
                        mut(r)
                    json.dump(r, open(os.path.join(tmp, "run_record_%s_%s.json" % (tag, mode)), "w"))
            try:
                K8A.check_dev_runs(tmp, ["t1", "t3"], ["decide", "loop"])
                t13[name + "_refused"] = False
            except AssertionError:
                t13[name + "_refused"] = True
        try:
            K8A.check_dev_runs(DEV_RUNS, ["t1"], ["decide"], {("t1", "decide"): [{"scene": nondev["t1"][0]}]})
            t13["nondev_episode_refused"] = False
        except AssertionError:
            t13["nondev_episode_refused"] = True
        spy = Spy(caches("t1"))
        with instrumented(spy, R):
            txt, err = run_main(R, ["--caches", *caches("t1"), "--tag", "x", "--mode", "decide", "--out", tmp, "--dev", "--scenes", nondev["t1"][0]])
        t13["runner_dev_nondev_scene_refused"] = bool(isinstance(err, AssertionError) and not spy.opened and spy.calls["Pool"] == 0)
    t13["pass"] = bool(t13["dev_runs_accepted"] is True and all(v for k_, v in t13.items() if k_.endswith("refused")))
    res["T13_allow_dev_guard"] = t13
    ok_all &= t13["pass"]
    # ---------------------------------------------------------------- T14 (shards, merge, resume)
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        sc_ = ["scene-0103", "scene-0757"]
        arms_ = ["Z0", "Mstar", "B0a0.25"]
        cmd = [sys.executable, "-B", os.path.join(K8, "k8_run_v02.py"), "--caches", *caches("t1"), "--fits", fits_file("t1"), "--tag", "t1_decide",
               "--mode", "decide", "--out", tmp, "--dev", "--workers", "2", "--scenes", *sc_, "--arms", *arms_]
        subprocess.run(cmd, check=True, capture_output=True)
        F = json.load(open(fits_file("t1")))
        Dm = dict(np.load(os.path.join(tmp, "decisions_t1_decide.npz")))
        Cm = dict(np.load(os.path.join(tmp, "counts_t1_decide.npz")))
        Km = dict(np.load(os.path.join(tmp, "cal_t1_decide.npz")))
        eps_ = [json.loads(l) for l in open(os.path.join(tmp, "episodes_t1_decide.jsonl"))]
        ok14 = [o["episode"] for o in eps_] == list(range(len(eps_))) and [(o["scene"], o["arm"]) for o in eps_] == [(s_, a_) for s_ in sorted(sc_) for a_ in arms_]
        for o in eps_:
            sc = S2.Scene(scene_path("t1", o["scene"]))
            oo, cc = S2.run_decisions(sc, o["arm"], None if o["arm"] in S2.FITFREE else fits_for(F, o["scene"]))
            m = Dm["episode"] == o["episode"]
            ok14 &= all(arr_eq(Dm[f][m], oo["decisions"][f]) for f in S2.DEC_FIELDS) and arr_eq(Dm["stats"][m], oo["decisions"]["stats"]) \
                and arr_eq(Dm["trk"][m], oo["decisions"]["trk"])
            mc = Cm["episode"] == o["episode"]
            ok14 &= Cm["cell"][mc].tolist() == sorted(cc) and Cm["n"][mc].tolist() == [cc[c][0] for c in sorted(cc)] and Cm["exceed"][mc].tolist() == [cc[c][1] for c in sorted(cc)]
            mk = Km["episode"] == o["episode"]
            ok14 &= Km["key"][mk].tolist() == sorted(oo["cal"]) and arr_eq(Km["values"][mk], np.array([oo["cal"][k] for k in sorted(oo["cal"])]).reshape(-1, S2.N_CAL))
            ok14 &= all(same(o[k], oo[k]) for k in oo if k not in ("decisions", "cal"))
        h1 = {f: sha(os.path.join(tmp, f)) for f in ("episodes_t1_decide.jsonl", "decisions_t1_decide.npz", "counts_t1_decide.npz", "cal_t1_decide.npz")}
        subprocess.run(cmd + ["--resume"], check=True, capture_output=True)
        rr = json.load(open(os.path.join(tmp, "run_record_t1_decide.json")))
        h2 = {f: sha(os.path.join(tmp, f)) for f in h1}
        resume_ok = rr["shards_reused"] == 2 and h1 == h2
        cmdl = [sys.executable, "-B", os.path.join(K8, "k8_run_v02.py"), "--caches", *caches("t3"), "--fits", fits_file("t3"), "--tag", "t3_loop",
                "--mode", "loop", "--out", tmp, "--dev", "--workers", "1", "--scenes", "scene-0655", "--arms", "B4", "--delays-kf", "0", "2"]
        subprocess.run(cmdl, check=True, capture_output=True)
        F3 = json.load(open(fits_file("t3")))
        Dl = dict(np.load(os.path.join(tmp, "decisions_t3_loop.npz")))
        el = [json.loads(l) for l in open(os.path.join(tmp, "episodes_t3_loop.jsonl"))]
        loop_ok = len(el) == 2
        for o in el:
            oo, cc = S2.run_episode(S2.Scene(scene_path("t3", "scene-0655")), "B4", fits_for(F3, "scene-0655"), o["delay_kf"])
            m = Dl["episode"] == o["episode"]
            loop_ok &= all(arr_eq(Dl[f][m], oo["decisions"][f]) for f in S2.DEC_FIELDS) and arr_eq(Dl["stats"][m], oo["decisions"]["stats"]) \
                and o["trace_sha256"] == oo["trace_sha256"]
    res["T14_shards"] = {"pass": bool(ok14 and resume_ok and loop_ok), "decide_equal": bool(ok14), "resume_byte_identical": bool(resume_ok), "loop_equal": bool(loop_ok)}
    ok_all &= res["T14_shards"]["pass"]
    # ---------------------------------------------------------------- T15 (items reproduce K7) and T16 (A6 items re-derived)
    t15, t16 = {}, {}
    import m_lib_v04 as Mlib
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for tag in ("t1", "t3"):
            ip = os.path.join(tmp, "items_%s.npz" % tag)
            subprocess.run([sys.executable, "-B", os.path.join(K8, "k8_items_v02.py"), "--caches", *caches(tag), "--out", ip, "--dev", "--workers", str(workers)],
                           check=True, capture_output=True)
            a7 = np.load(os.path.join(SCRATCH, "..", "k7_scratch", "items_v02_dev_%s.npz" % tag))
            b8 = np.load(ip)
            na, nb = list(a7["scene_names"]), list(b8["scene_names"])
            eq = sorted(na) == sorted(nb) == sorted(DEV)
            for name in na:
                sa, sb = na.index(name), nb.index(name)
                for pre in ("item_", "rec_"):
                    ma, mb = a7[pre + "s"] == sa, b8[pre + "s"] == sb
                    for k in [f for f in a7.files if f.startswith(pre) and f != pre + "s"]:
                        eq &= np.array_equal(a7[k][ma], b8[k][mb])
            it = K8A.load_items_k8(ip, set())
            t15[tag] = {"k7_fields_equal": bool(eq), "pd7_records": len(it["k"]), "ref_relied_items": it["n_ref_relied_items"],
                        "pass": bool(eq and len(it["k"]) == it["n_ref_relied_items"])}
            F = json.load(open(fits_file(tag)))
            sub = np.random.default_rng(3).choice(len(it["k"]), size=min(400, len(it["k"])), replace=False)
            worst = {}
            for arm in ("B0", "B4", "Mstar", "B9"):
                d = K8A.item_diagnostics(arm, it, F)
                mx = 0.0
                for i in sub.tolist():
                    Sw_ = np.array([[it["sxx"][i], it["sxy"][i]], [it["sxy"][i], it["syy"][i]]])
                    h = int(it["h"][i])
                    f_ = F["fits"][str(F["fold_of_scene"][str(it["scene"][i])])][STEPS[h]]
                    if arm == "B0":
                        Sig = Sw_ + S2.SIGMA_A ** 2 * np.eye(2)
                    elif arm == "B4":
                        Sig = (f_["B4"] / S2.Z) ** 2 * (Sw_ + S2.SIGMA_A ** 2 * np.eye(2))
                    elif arm == "Mstar":
                        thr = np.asarray(f_["Mstar_ip"])
                        ipf = int(it["inpath"][i])
                        Sig = Mlib.deploy_covariance(Sw_, float(it["yaw"][i]), thr[it["l0_long"][i] + 96 * ipf], thr[it["l0_lat"][i] + 96 * ipf])
                    else:
                        Sig = (f_["B9"] ** 2 / chi2.ppf(0.95, 2)) * np.eye(2)
                    e = np.array([it["dx"][i], it["dy"][i]])
                    nees = float(e @ np.linalg.solve(Sig, e))
                    nll = 0.5 * nees + 0.5 * math.log(np.linalg.det(Sig)) + math.log(2 * math.pi)
                    mx = max(mx, abs(nees - d["nees"][i]) / max(1.0, abs(nees)), abs(nll - d["nll"][i]) / max(1.0, abs(nll)))
                worst[arm] = mx
            t16[tag] = {"max_rel_diff": worst, "pass": bool(all(v < 1e-9 for v in worst.values()))}
    res["T15_items_reproduce_K7"] = {"pass": bool(all(v["pass"] for v in t15.values())), **t15}
    res["T16_A6_items_rederived"] = {"pass": bool(all(v["pass"] for v in t16.values())), **t16}
    ok_all &= res["T15_items_reproduce_K7"]["pass"] and res["T16_A6_items_rederived"]["pass"]
    pool.close()
    res["hashes"] = {f: sha(os.path.join(K8, f)) for f in ("k8_sim_v02.py", "k8_run_v02.py", "k8_items_v02.py", "k8_analyse_v02.py")}
    res["ALL_PASS"] = bool(ok_all)
    json.dump(res, open(out_json, "w"), indent=1, default=float)
    print(json.dumps({k: (v.get("pass") if isinstance(v, dict) else v) for k, v in res.items()}, indent=1))
    print("ALL_PASS" if ok_all else "FAIL")


if __name__ == "__main__":
    try:
        main()
    except BaseException:
        import traceback
        _RES["CRASHED"] = traceback.format_exc()
        _RES["ALL_PASS"] = False
        json.dump(_RES, open(sys.argv[1], "w"), indent=1, default=float)
        raise
