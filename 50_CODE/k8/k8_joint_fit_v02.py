#!/usr/bin/env python3
"""K8 joint arm M*J (Claude line, k8_joint_fit_v02, 2 Nov 2026) = k8_joint_fit_v01 with two changes after the T3 full fit stopped
on v01's own guard ("the refit of M* from these items differs from the fits (fold 4, h2s)"; diagnosis
70_TESTS/k8_joint_v01/diag/k8_joint_t3_refit_diag_v01.json, tests/k8_joint_t3_refit_diag_v01.py):
  * the cause: an exact tie at delta in x1_lib_v03.crc_threshold. For T3 fold 4, h2s, L0 74 (large|<20|long|turning, not in
    path; 108 scenes), the CRC bound at U = 0.38665 is exactly 1/20 = delta; in floating point it evaluates to
    0.049999999999999996 (accepted) when the scenes are summed in sorted-name order and to 0.05000000000000001 (rejected) in
    K7 v01's scene order, so M*'s fit took the next value 0.39570 (exact bound 89/2180). The items are identical to M*'s
    (every field, every scene). M*'s fit is consistent with its own items in its own order; it is order-dependent only at exact ties;
  * v02 refits M* (the guard, unchanged: exact equality with k7_fits) and M*Jx's base in M*'s own scene order, the order of
    M*'s K7 v01 items (--k7-items, now required outside --dev): the scene index of every item is relabelled to that order;
  * v02 decides the joint CRC bound for lambda in exact rational arithmetic (per-scene counts as fractions; delta = 1/20), so
    lambda does not depend on the scene order; the floating-point decision is recorded beside it (float_exact_agree).
v01 (unchanged, kept):
K8 joint arm M*J (Claude line, k8_joint_fit_v01, 2 Nov 2026): scene-level conformal risk control on the JOINT (union) loss.
Implements 90_DECISIONS/D16_DELEGATED_CHOICES_v01.md Choice 2 (b) and D14 v05 section 9 route (b).

What M*J is. M* (k7_fit_v01 'Mstar_ip') gives, per log fold f, calibrated step h (0.5, 1, 1.5, 2 s), L0 stratum and in-path flag,
a threshold c > 0 on U = D / sd (DP-SCRC per constraint, n_min = 19 scenes, fallback L0 -> L3). M*J keeps that per-stratum
shape and multiplies it by ONE scalar lambda_f per tracker and fold, shared by every stratum, both in-path parts and the 4
calibrated steps:  c_J(f, h, l0, ip) = lambda_f * c_M*(f, h, l0, ip). Steps 2.5-4 s (not enforced by the planner) keep M*'s
K6 thresholds unchanged. lambda_f is the smallest value on the grid GRID (1.00, 1.01, ..., 100.00) whose CRC bound on the joint
scene loss is <= delta = 0.05:
  * a decision = one planner query at a logged state (scene, keyframe k) of the calibration items (k8_items_v02 / k7_items_v02:
    the planner's enforced (track, check time) pairs at the decision states, ground truth at k + h);
  * its constraints = the ref_relied items (one per enforced pair: the axis the planner relies on at the reference pose), i.e.
    the arm-independent PD7 items, over every track and the 4 calibrated steps;
  * the decision's joint loss at lambda = 1{ some constraint i of the decision has U_i > lambda c_i } = 1{ R_d > lambda } with
    R_d = max_i U_i / c_i (c_i > 0 is asserted for every base threshold, so U_i > lambda c_i <=> U_i / c_i > lambda);
  * a scene's loss L_s(lambda) = the fraction of its decisions (with >= 1 constraint in the population) with a joint loss, in
    [0, 1] and non-increasing in lambda (a union of non-increasing indicators, then a mean);
  * CRC: lambda_P = min{ lambda in GRID : n / (n + 1) mean_s L_s(lambda) + 1 / (n + 1) <= delta } over the n calibration scenes
    of population P (x1_lib_v03.crc_threshold's rule with the scene as the unit, on the grid);
  * the populations are PD7 (every relied constraint), SD1_7 (pair gap <= 5 m at the reference pose) and PD (in-path): the three
    on which D14 v05 section 6 tests validity. lambda_f = max_P lambda_P certifies all three: by monotonicity the loss of every
    population at the max is pointwise <= its loss at its own lambda_P, so each population keeps its own CRC guarantee (no
    union bound across populations is needed or claimed).
Two variants are written (the arms the k8_sim_v04 harness reads as '<arm>_ip'):
  MstarJ  (primary, as specified) calibration scenes = M*'s own for fold f (the scenes of the other 4 folds), base = M*'s
          fold-f thresholds. The base was fitted on the same scenes, so the CRC bound holds exactly only conditional on a base
          that does not depend on them; the in-sample optimism is measured by 'items_oof' (the joint loss of fold f's own items
          at lambda_f, out of fold) and by the sim's V2 on the held-out folds.
  MstarJx (exact split, sensitivity) for test fold f, g = (f + 1) mod 5: the base is refitted with M*'s own rule
          (k7_fit_v01.split_fit, the same strata, n_min and fallback) on the 3 folds other than f and g, and lambda is fitted by
          CRC on fold g's scenes only. Base, lambda and test scenes are disjoint, so the CRC guarantee holds exactly under scene
          exchangeability (it uses the same calibration scenes as M*, split into a shape part and an inflation part).
Checks written into the output: the refit of M*'s fold-f thresholds from the items equals k7_fits exactly (split_fit on the
4 folds); the items equal M*'s own K7 v01 items scene by scene (--k7-items); every base threshold is > 0.
--dev (plumbing only, never evidence): the 10 development scenes; every fold calibrates in-sample on all of them; --delta may
then be relaxed (10 scenes cannot certify delta = 0.05: 1 / (n + 1) > delta); MstarJx then keeps M*'s base (crc_threshold needs
>= 19 scenes, so M*'s rule cannot be refitted on 10).
Usage: python -B k8_joint_fit_v01.py --fits <k7_fits_<t>_v01.json> --items <k8_items_v02 npz> [<npz> ...] --out <json>
       [--k7-items <k7_items_<t>_v01.npz>] [--dev [--delta d]]
"""
import argparse
import copy
from fractions import Fraction
import hashlib
import json
import os
import sys
import time

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k7"))
import m_lib_v04 as M  # noqa: E402
import k7_fit_v01 as K7F  # noqa: E402  (split_fit: M*'s fit, unchanged)

L = M.L                                  # x1_lib_v03 (crc_threshold)
STEPS = K7F.STEPS                        # the 8 planner steps of the fits
CC_STEPS = 4                             # calibrated, enforced steps 0.5 ... 2 s (k8_sim_v02.CC_STEPS)
N_L0 = M.N_L0
DELTA = 0.05
N_MIN = M.N_CRC                          # 19 scenes
GAP_NEAR = 5.0                           # k8_sim_v02.GAP_BINS[1]: SD1_7 = pair gap <= 5 m
GRID = np.round(np.arange(1.0, 100.0 + 1e-9, 0.01), 2)
JOINT_ARMS = ("MstarJ", "MstarJx")
POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")
ITEM_FIELDS = ("s", "k", "h", "g", "r", "a", "m", "inpath", "sd", "D", "l0", "gap", "pair", "ref_relied")
K7_V01_FIELDS = ("k", "h", "g", "r", "a", "m", "inpath", "sd", "D", "l0")
STAMPS = {"exploratory": "EXPLORATORY: nuScenes development evidence, not a confirmation (K8 joint arm M*J)",
          "dev": "DEV MODE: the 10 development scenes; plumbing only, not evidence (K8 joint arm M*J)"}
DEC_BASE = 1000000                       # decision id = scene index * DEC_BASE + keyframe
DEV_SCENES = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077",
              "scene-1094", "scene-1100")    # k8_run_v02.DEV_SCENES
STRATIFICATION = ("one scalar lambda per tracker and fold, shared by all 96 L0 strata x 2 in-path parts and the 4 calibrated "
                  "steps, multiplying M*'s per-stratum thresholds (MstarJ) or the same rule's 3-fold refit (MstarJx); "
                  "steps 2.5-4 s unchanged")


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ---------------------------------------------------------------- the joint loss and its CRC

def decision_max_ratio(dec_id, ratio):
    """Per decision: R_d = max of the constraint ratios U_i / c_i. Returns (decision ids, R) sorted by id."""
    u, inv = np.unique(dec_id, return_inverse=True)
    R = np.full(len(u), -np.inf)
    np.maximum.at(R, inv, ratio)
    return u, R


def scene_losses(scene_of_dec, R, lam):
    """L_s(lam): per scene, the fraction of its decisions with a joint loss (R_d > lam). Returns (scenes, losses)."""
    scenes, sidx = np.unique(scene_of_dec, return_inverse=True)
    tot = np.bincount(sidx, minlength=len(scenes)).astype(float)
    return scenes, np.bincount(sidx, weights=(R > lam).astype(float), minlength=len(scenes)) / tot


def crc_bound(scene_of_dec, R, lam):
    """The CRC bound n / (n + 1) mean_s L_s(lam) + 1 / (n + 1) and the in-sample mean loss."""
    _, Ls = scene_losses(scene_of_dec, R, lam)
    n = len(Ls)
    return n / (n + 1.0) * float(Ls.mean()) + 1.0 / (n + 1.0), float(Ls.mean())


def crc_grid(scene_of_dec, R, delta=DELTA, grid=GRID):
    """The smallest lam in grid with crc_bound(lam) <= delta (binary search; the bound is non-increasing in lam).
    Returns a dict; lam is None (none_qualifies) when even the last grid point fails or n is too small (1 / (n + 1) > delta)."""
    scenes, sidx = np.unique(scene_of_dec, return_inverse=True)
    n = len(scenes)
    out = {"n_scenes": int(n), "n_decisions": int(len(R)), "delta": float(delta), "lam": None, "none_qualifies": True}
    if n == 0 or 1.0 / (n + 1.0) > delta:
        out["reason"] = "1 / (n + 1) > delta: n = %d scenes cannot certify delta = %g" % (n, delta)
        return out
    tot = np.bincount(sidx, minlength=n).astype(float)
    tot_i = np.bincount(sidx, minlength=n)
    d_exact = Fraction(repr(float(delta)))                   # 0.05 -> 1/20 exactly

    def bnd(lam):
        Ls = np.bincount(sidx, weights=(R > lam).astype(float), minlength=n) / tot
        return n / (n + 1.0) * float(Ls.mean()) + 1.0 / (n + 1.0), float(Ls.mean())

    def ok(lam):
        """v02: the CRC decision in exact rational arithmetic (sum over scenes of x_s / t_s, grouped by t_s)."""
        x = np.bincount(sidx, weights=(R > lam).astype(float), minlength=n).astype(np.int64)
        ssum = sum((Fraction(int(x[tot_i == t].sum()), int(t)) for t in np.unique(tot_i)), Fraction(0))
        return Fraction(n, n + 1) * ssum / n + Fraction(1, n + 1) <= d_exact
    out["loss_at_1"] = bnd(1.0)[1]
    b_last = bnd(grid[-1])
    if not ok(grid[-1]):
        out["reason"] = "the bound at the last grid point %.2f is %.4f > delta" % (grid[-1], b_last[0])
        out["bound_at_grid_max"] = b_last[0]
        return out
    lo, hi = 0, len(grid) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(grid[mid]):
            hi = mid
        else:
            lo = mid + 1
    b, l_in = bnd(grid[lo])
    out.update({"lam": float(grid[lo]), "grid_index": int(lo), "none_qualifies": False, "bound": b, "loss_in_sample": l_in,
                "bound_at_previous_grid_point": (bnd(grid[lo - 1])[0] if lo > 0 else None),
                "at_grid_min": bool(lo == 0), "decision": "exact rational (v02)",
                "float_exact_agree": bool((b <= delta) == ok(grid[lo]) and (lo == 0 or (bnd(grid[lo - 1])[0] <= delta) == ok(grid[lo - 1])))})
    return out


def crc_continuous(scene_of_dec, R, delta=DELTA):
    """The same CRC with x1_lib_v03.crc_threshold (the method stage's function) on the per-decision R_d (cross-check)."""
    return L.crc_threshold(np.asarray(R, float), np.asarray(scene_of_dec), delta)


# ---------------------------------------------------------------- items

def load_items(paths):
    """Concatenates k8_items_v02 / k7_items_v02 item arrays from one or more files over the union of their scenes. Returns
    (items dict with a global scene index 's', scene names (sorted), per-file info). A scene may appear in one file only."""
    names_all, parts, info = [], [], []
    for p in paths:
        z = np.load(p)
        names = [str(x) for x in z["scene_names"]]
        assert "item_ref_relied" in z.files, "items without ref_relied: use k8_items_v02 or k7_items_v02 (" + p + ")"
        parts.append((names, {f: z["item_" + f] for f in ITEM_FIELDS}))
        names_all += names
        info.append({"file": os.path.abspath(p), "sha256": sha256_path(p), "scenes": len(names), "items": int(len(z["item_D"])),
                     "stamp": str(z["stamp"]) if "stamp" in z.files else None})
    assert len(set(names_all)) == len(names_all), "a scene appears in two item files"
    order = sorted(names_all)
    gidx = {n: i for i, n in enumerate(order)}
    it = {f: [] for f in ITEM_FIELDS}
    for names, d in parts:
        remap = np.array([gidx[n] for n in names], np.int64)
        for f in ITEM_FIELDS:
            it[f].append(remap[d["s"]] if f == "s" else d[f])
    it = {f: np.concatenate(v) for f, v in it.items()}
    it["inpath"] = it["inpath"].astype(bool)
    it["ref_relied"] = it["ref_relied"].astype(bool)
    return it, np.array(order), info


def k7_scene_names(k7_items_path):
    """v02: the scene order of M*'s own K7 v01 items (the index order k7_fit_v01 used)."""
    return [str(x) for x in np.load(k7_items_path)["scene_names"]]


def relabel_to_order(it, names, order):
    """v02: relabels the items' scene index to the given scene order (M*'s); returns the new names array."""
    rank = {n: i for i, n in enumerate(order)}
    assert sorted(order) == sorted(names), "the scene orders cover different scenes"
    it["s"] = np.array([rank[n] for n in names], np.int64)[it["s"]]
    return np.array(order)


def check_against_k7_items(it, names, k7_items_path, fits):
    """The items equal M*'s own input (k7_items_v01, the file whose hash the fits carry) scene by scene, field by field."""
    sha = sha256_path(k7_items_path)
    assert sha == fits["items_sha256"], "the K7 items file is not the one M* was fitted on"
    z = np.load(k7_items_path)
    n1 = [str(x) for x in z["scene_names"]]
    assert sorted(n1) == list(names), "the items cover other scenes than M*'s K7 items"
    rank = {n: i for i, n in enumerate(names)}
    s1 = np.array([rank[n] for n in n1], np.int64)[z["item_s"]]
    o1 = np.argsort(s1, kind="stable")
    o2 = np.argsort(it["s"], kind="stable")
    assert np.array_equal(s1[o1], it["s"][o2]), "items per scene differ in number"
    out = {"k7_items_sha256": sha, "items": int(len(o1))}
    for f in K7_V01_FIELDS:
        a, b = z["item_" + f][o1], it[f][o2]
        if f == "inpath":
            a = a.astype(bool)
        assert np.array_equal(a, b), "item field %s differs from M*'s K7 items" % f
        out[f] = "equal"
    return out


def base_of_items(base_f, it, sel):
    """c_i for the selected items under ONE deployed base: base_f[h, l0 + 96 * inpath] (base_f: (4, 192), the thresholds of the
    test fold, applied to every calibration and test item alike)."""
    return base_f[it["h"][sel], it["l0"][sel] + N_L0 * it["inpath"][sel].astype(int)]


def pop_mask(it, p):
    rel = it["ref_relied"]
    if p == "PD7_primary":
        return rel.copy()
    if p == "SD1_7_gap_le_5m":
        return rel & (it["gap"] <= GAP_NEAR)
    if p == "PD_inpath":
        return rel & it["inpath"]
    raise ValueError(p)


def joint_R(it, sel, c):
    """Per decision of the selected items: (scene index, R_d)."""
    U = it["D"][sel] / it["sd"][sel]
    dec = it["s"][sel].astype(np.int64) * DEC_BASE + it["k"][sel].astype(np.int64)
    d, R = decision_max_ratio(dec, U / c)
    return d // DEC_BASE, R


def fit_lambda(it, cal_scene_mask, base_f, delta, grid):
    """lambda = max over the three populations of the grid CRC on the calibration scenes' joint losses."""
    by_pop = {}
    for p in POPS:
        sel = pop_mask(it, p) & cal_scene_mask[it["s"]]
        c = base_of_items(base_f, it, sel)
        sc, R = joint_R(it, sel, c)
        r = crc_grid(sc, R, delta, grid)
        lc = crc_continuous(sc, R, delta) if r["n_scenes"] and 1.0 / (r["n_scenes"] + 1.0) <= delta else None
        r["lam_continuous_crc_threshold"] = None if lc is None else float(lc)
        if lc is not None and r["lam"] is not None:          # the grid answer is the first grid point at or above the continuous one
            exp = float(grid[0]) if lc <= grid[0] else float(grid[min(np.searchsorted(grid, lc - 1e-12, "left"), len(grid) - 1)])
            r["grid_equals_ceil_of_continuous"] = bool(abs(exp - r["lam"]) < 1e-9)
        r["empty"] = r["n_scenes"] == 0
        by_pop[p] = r
    used = [p for p in POPS if not by_pop[p]["empty"]]           # a population without calibration scenes constrains nothing
    assert used, "no calibration decision in any population"
    if any(by_pop[p]["lam"] is None for p in used):
        return None, by_pop, [p for p in used if by_pop[p]["lam"] is None]
    lam = max(by_pop[p]["lam"] for p in used)
    return lam, by_pop, [p for p in used if by_pop[p]["lam"] == lam]


def joint_loss_at(it, scene_mask, base_f, lam):
    """Items-level joint loss (reference pose) of the scenes in scene_mask at lam: per population the scene-level mean."""
    out = {}
    for p in POPS:
        sel = pop_mask(it, p) & scene_mask[it["s"]]
        if not sel.any():
            out[p] = None
            continue
        c = base_of_items(base_f, it, sel)
        sc, R = joint_R(it, sel, c)
        _, Ls = scene_losses(sc, R, lam)
        _, L1 = scene_losses(sc, R, 1.0)
        out[p] = {"scenes": int(len(Ls)), "decisions": int(len(R)), "E_at_lam": float(Ls.mean()), "E_at_1": float(L1.mean()),
                  "decision_level_at_lam": float(np.mean(R > lam))}
    return out


# ---------------------------------------------------------------- the fit

def base_array(fits, key="Mstar_ip", folds=5):
    return np.array([[fits["fits"][str(f)][STEPS[h]][key] for h in range(CC_STEPS)] for f in range(folds)], float)


def refit_split(it, lv, U, scene_sel, n_min):
    """M*'s fit rule (k7_fit_v01.split_fit: fit_hier separately on the not-in-path and in-path items, from L0) on the items of
    the selected scenes, per calibrated step. Returns ((4, 192) thresholds, (4, 192) sources)."""
    thr, src = np.full((CC_STEPS, 2 * N_L0), np.nan), np.full((CC_STEPS, 2 * N_L0), -1)
    ip = it["inpath"].astype(int)
    for h in range(CC_STEPS):
        sel = (it["h"] == h) & scene_sel[it["s"]]
        old = K7F.N_MIN
        K7F.N_MIN = n_min
        try:
            t_, s_ = K7F.split_fit(U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel], 0)
        finally:
            K7F.N_MIN = old
        thr[h], src[h] = t_, s_
    return thr, src


def fit(fits, it, names, delta=DELTA, grid=GRID, dev=False, n_min=N_MIN, check_refit=True, log=print):
    nf = len(fits["fits"])
    assert nf == 5, "5 log folds expected"
    fold_of_scene = np.array([fits["fold_of_scene"][n] for n in names], int)
    base = base_array(fits, "Mstar_ip", nf)
    assert np.all(np.isfinite(base)) and np.all(base > 0), "every M* threshold must be finite and > 0 (monotonicity in lambda)"
    m = it["m"]
    lv = M.levels(it, m)
    assert np.array_equal(lv[0], it["l0"]), "L0 from the items differs from the simulator's L0"
    U = it["D"] / it["sd"]
    ns = len(names)
    res = {"folds": {}, "refit_reproduces_Mstar": None}
    jfits = {str(f): {} for f in range(nf)}
    if check_refit and not dev:
        rep = {}
        for f in range(nf):
            thr, src = refit_split(it, lv, U, fold_of_scene != f, N_MIN)
            for h in range(CC_STEPS):
                F = fits["fits"][str(f)][STEPS[h]]
                ok = np.array_equal(thr[h], np.asarray(F["Mstar_ip"], float)) and np.array_equal(src[h], np.asarray(F["Mstar_ip_src"], int))
                rep["%d_%s" % (f, STEPS[h])] = bool(ok)
                assert ok, "the refit of M* from these items differs from the fits (fold %d, %s)" % (f, STEPS[h])
            log("refit of M* fold %d reproduces k7_fits exactly" % f)
        res["refit_reproduces_Mstar"] = rep
    for f in range(nf):
        t0 = time.time()
        test = fold_of_scene == f
        cal = np.ones(ns, bool) if dev else ~test
        # ---- MstarJ: M*'s base and M*'s calibration scenes
        lam, by_pop, binding = fit_lambda(it, cal, base[f], delta, grid)
        none_q = lam is None
        if none_q:                                    # CRC's answer is then lambda = infinity; the grid maximum is deployed, flagged
            lam = float(grid[-1])
        r = {"MstarJ": {"lambda": lam, "none_qualifies_grid_max_used": none_q, "binding_populations": binding, "by_population": by_pop,
                        "calibration_scenes": int(cal.sum()), "base": "M*'s fold-%d thresholds (k7_fits Mstar_ip)" % f,
                        "calibration": "in-sample on all development scenes (DEV)" if dev else "the scenes of the 4 other folds (M*'s own)"}}
        r["MstarJ"]["items_in_sample"] = joint_loss_at(it, cal, base[f], lam)
        r["MstarJ"]["items_oof"] = None if dev else joint_loss_at(it, test, base[f], lam)
        # ---- MstarJx: exact split (base on 3 folds, lambda on fold g, test fold f)
        g = (f + 1) % nf
        if dev:       # 10 scenes cannot refit M*'s rule (crc_threshold needs >= 19 scenes): M*'s base, in-sample lambda (plumbing)
            base_scenes, lam_scenes = np.ones(ns, bool), np.ones(ns, bool)
            thr_x = base[f].copy()
            src_x = np.array([fits["fits"][str(f)][STEPS[h]]["Mstar_ip_src"] for h in range(CC_STEPS)], int)
        else:
            base_scenes = (fold_of_scene != f) & (fold_of_scene != g)
            lam_scenes = fold_of_scene == g
            thr_x, src_x = refit_split(it, lv, U, base_scenes, n_min)
        assert np.all(np.isfinite(thr_x)) and np.all(thr_x > 0), "MstarJx base: every threshold must be finite and > 0"
        lam_x, by_pop_x, binding_x = fit_lambda(it, lam_scenes, thr_x, delta, grid)
        none_qx = lam_x is None
        if none_qx:
            lam_x = float(grid[-1])
        r["MstarJx"] = {"lambda": lam_x, "none_qualifies_grid_max_used": none_qx, "binding_populations": binding_x,
                        "by_population": by_pop_x, "lambda_fold": None if dev else g,
                        "base_folds": "DEV: M*'s base (no refit possible on 10 scenes)" if dev else [x for x in range(nf) if x not in (f, g)],
                        "base_scenes": int(base_scenes.sum()), "lambda_scenes": int(lam_scenes.sum()), "n_min": int(n_min),
                        "base_src_share": {str(lv_): float(np.mean(src_x == lv_)) for lv_ in range(4)},
                        "base_ratio_to_Mstar_median": float(np.median(thr_x / base[f]))}
        r["MstarJx"]["items_lambda_fold"] = joint_loss_at(it, lam_scenes, thr_x, lam_x)
        r["MstarJx"]["items_oof"] = None if dev else joint_loss_at(it, test, thr_x, lam_x)
        res["folds"][str(f)] = r
        for h, st in enumerate(STEPS):
            F = fits["fits"][str(f)][st]
            if h < CC_STEPS:
                jfits[str(f)][st] = {
                    "MstarJ_ip": (lam * np.asarray(F["Mstar_ip"], float)).tolist(),
                    "MstarJ_ip_src": list(F["Mstar_ip_src"]), "MstarJ_lambda": lam,
                    "MstarJx_ip": (lam_x * thr_x[h]).tolist(),
                    "MstarJx_ip_src": src_x[h].astype(int).tolist(), "MstarJx_lambda": lam_x}
            else:                                       # steps 2.5-4 s: not enforced, M*'s K6 thresholds unchanged
                jfits[str(f)][st] = {"MstarJ": list(F["Mstar"]), "MstarJx": list(F["Mstar"]), "MstarJ_lambda": None, "MstarJx_lambda": None}
        log("fold %d: lambda MstarJ %s (binding %s), MstarJx %s (binding %s)  %.0f s"
            % (f, lam, ",".join(binding), lam_x, ",".join(binding_x), time.time() - t0))
    return jfits, res


def write_joint_fits(fits, jfits, meta):
    """A copy of M*'s fits file (every key unchanged, so k8_run_v0x and k8_analyse_v0x read it as before) with the joint arms'
    entries added to every fold and step, and the metadata under 'joint'."""
    out = copy.deepcopy(fits)
    for f, d in jfits.items():
        for st, e in d.items():
            for k, v in e.items():
                assert k not in out["fits"][f][st], "would overwrite " + k
                out["fits"][f][st][k] = v
    out["joint"] = meta
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--fits", required=True, help="M*'s fits (k7_fits_<t>_v01.json)")
    ap.add_argument("--items", nargs="+", required=True, help="k8_items_v02 / k7_items_v02 files covering M*'s scenes")
    ap.add_argument("--out", required=True)
    ap.add_argument("--k7-items", default=None, help="M*'s own K7 v01 items: checked equal to --items scene by scene")
    ap.add_argument("--dev", action="store_true", help="the 10 development scenes; plumbing only")
    ap.add_argument("--delta", type=float, default=DELTA)
    ap.add_argument("--no-refit-check", action="store_true")
    a = ap.parse_args(argv)
    t0 = time.time()
    if not a.dev:
        assert a.delta == DELTA, "outside --dev, delta = 0.05 is fixed"
        assert a.k7_items, "outside --dev, --k7-items is required (v02: M*'s refit runs in M*'s own scene order)"
    fits = json.load(open(a.fits))
    it, names, info = load_items(a.items)
    if a.dev:
        assert set(names) <= set(DEV_SCENES), "--dev takes the development scenes only"
    else:
        assert not (set(names) - set(fits["scenes"])), "items of scenes outside the fits"
        assert list(names) == sorted(fits["scenes"]), "the items must cover exactly M*'s scenes (%d found, %d in the fits)" % (len(names), len(fits["scenes"]))
    k7chk = check_against_k7_items(it, names, a.k7_items, fits) if a.k7_items else None
    scene_order = "sorted scene names (development items)"
    if a.k7_items:                                        # v02: M*'s own scene order (the tie at delta is order-dependent)
        names = relabel_to_order(it, names, k7_scene_names(a.k7_items))
        scene_order = "M*'s K7 v01 items (k7_fit_v01's index order)"
    jfits, res = fit(fits, it, names, a.delta, GRID, a.dev, N_MIN, check_refit=not (a.dev or a.no_refit_check))
    meta = {"stamp": STAMPS["dev" if a.dev else "exploratory"], "method": "M*J: scene-level CRC on the joint (union) loss",
            "arms": list(JOINT_ARMS), "primary": "MstarJ", "sensitivity": "MstarJx (exact split)",
            "stratification": STRATIFICATION, "populations": list(POPS), "lambda_rule": "max over the populations of the grid CRC",
            "delta": a.delta, "grid": {"min": float(GRID[0]), "max": float(GRID[-1]), "step": 0.01, "points": int(len(GRID))},
            "n_min": N_MIN, "dev": bool(a.dev), "gap_near_m": GAP_NEAR, "decision_unit": "(scene, keyframe) of the items",
            "constraint_unit": "ref_relied items (one per enforced pair with ground truth, 4 calibrated steps, every track)",
            "base_fits": os.path.abspath(a.fits), "base_fits_sha256": sha256_path(a.fits), "items": info,
            "k7_items_check": k7chk, "code_sha256": sha256_path(os.path.abspath(__file__)),
            "m_lib_v04_sha256": sha256_path(M.__file__), "k7_fit_v01_sha256": sha256_path(K7F.__file__),
            "scenes": int(len(names)), "fit": res, "seconds": None, "version": "k8_joint_fit_v02",
            "scene_order": scene_order, "joint_crc_decision": "exact rational arithmetic (v02)"}
    meta["seconds"] = round(time.time() - t0, 1)
    out = write_joint_fits(fits, jfits, meta)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, a.out)
    print(json.dumps({"out": os.path.abspath(a.out), "sha256": sha256_path(a.out), "seconds": meta["seconds"],
                      "lambda": {f: {k: res["folds"][f][k]["lambda"] for k in JOINT_ARMS} for f in res["folds"]}}))
    print("K8 JOINT FIT DONE")


if __name__ == "__main__":
    main()
