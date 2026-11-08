#!/usr/bin/env python3
"""K8 analysis (Claude line, v01, 1 Nov 2026). Implements 90_DECISIONS/D14_K8_DESIGN_v02.md sections 2-5 on the runs of
k8_run_v01 / k8_sim_v01. Derived from k7_analyse_v02.py; everything K7 computed is computed in the same form, and the
following is added. Nothing is gated on nuScenes (D14 v02 section 4): the K7-form hypotheses are computed and REPORTED.

Changes from k7_analyse_v02 (file-by-file list in README_K8_v01.md):
  N1  (R12b) hk1_rule: PD's own power-qualified family must not be flagged in its own sup-t (a_ok &= not family_flagged); the
      count floor stays reported only on PD. R12b n1: this docstring names the design it implements (D14 v02, not plan v01).
  A1  V2 trajectory-level exceedance: per decision, the indicator that any relied constraint over the steps and objects is
      exceeded at the reference pose (from the per-decision counts of k8_sim_v01); scene-level rate per population with the
      log-cluster bootstrap interval. Plus the one-step check: V1 and V2 at the first check time (step 0, 0.5 s) only.
  A2  alpha-sweep arms B0a<alpha> (margin sqrt(alpha) z sd): curve of (pooled PD7 / SD1_7 / PD exceedance, V2, infeasible rate).
  A3  delta'-retuning arms B0d<delta'> (margin z_{1-delta'} sd): the same curve; the "retuned nominal" is the LARGEST delta'
      (the least conservative, i.e. the smallest retuning) whose pooled PD7 scene-level exceedance is <= delta. D14 says
      "the smallest delta'"; read literally that is degenerate under monotonicity (every smaller delta' also qualifies), so
      the least-inflated qualifying arm is taken and the reading is stated here and in the README. The analogous "retuned
      alpha" (the smallest alpha with pooled PD7 exceedance <= delta) is reported too.
  A4  O1 infeasible-decision rate (K6/K7 form, unchanged), O2 progress ratio (sum of the leashed planned 0.5 s increments over
      the sum of the logged ego's 0.5 s increments, per scene) and mean chosen speed, O3 back-off distribution (share of
      decisions at lambda = 1, 0.75, 0.5, 0.25, 0 and emergency stop; mean back-off level with the stop counted as 0).
  A5  S1 minimum pair gap and TTC at decision states (k8_sim_v01._safety_extras): mean, share of decisions with gap < 1 m,
      share with TTC < 2 s; collisions (loop) are reported as in K6 and never rank arms.
  A6  C1 ANEES with its chi-square interval ([chi2_{2n}(0.025), chi2_{2n}(0.975)] / n) and p_v (share of NEES outside the 95 %
      chi-square(2) interval, split into below and above), ellipse coverage at 50/90/95/99 %; C2 per-axis exceedance curves at
      delta in {0.1, 0.05, 0.01, 0.001} per stratum (standardised error along the relied-on axis under the arm's covariance);
      C3 Gaussian NLL and energy score (200 fixed standard-normal draws, seed 20261108) per stratum; all on the PD7 pairs
      (and SD1_7, PD, NIP), per arm, under the covariance k8_sim_v01._arm_cov documents per arm (Z0 has none).
  A7  C4 sharpness: mean margin along the object's long and lateral axes over the relied-on pairs, per arm, beside every
      calibration figure.
  A8  counts: scenes, logs, decisions, records (per population, per arm; per cell for M*), items (--items, the K7 items file,
      development scenes excluded), the 5 log folds (--fits), the development scenes excluded, the scope notes.
  A9  NIP (not-in-path relied constraints) with its exceedance per arm (cells, pooled, V2, calibration).
  A10 replay divergence: share of decisions with |chosen speed - logged speed| > 2 m/s.
  A13 fallback strata: for every per-stratum table the share of M*'s (fold, step <= 2 s, L0, in-path) thresholds in the
      stratum that came from a coarser level (Mstar_ip_src > 0 in the fits) and the flag share > 0.
  Validity per arm: hk1_rule (K6's tests, N1 restored) is evaluated for EVERY arm on its own tables (power families from the
      arm's own counts; seeds [20261107, i] + [k] for M* as in K7, [20261107, i, 100 + arm index] + [k] for the others), so
      D14 section 6 form B ("comparators that pass validity") can be reported; forms A, B and C are reported per tracker.
  Statistics: paired differences at identical decision states for every arm pair on O1-O3, S1, A10, V1 and V2 (per-scene
      means; the decision states are identical across arms in the decision mode), log-cluster bootstrap B = 2000 (seeds
      [20261106, i, 0 | 1] as K7), sup-t and Bonferroni unchanged.
Outputs: one JSON (--out) and CSV tables (--csv-dir, default: the JSON's directory): k8_<tag>_<mode>_<table>.csv.
Usage: python -B k8_analyse_v01.py --runs <dir> --tags t1 t3 --manifests <...> --out <json> [--csv-dir <dir>] [--prereg <plan.md>]
       [--allow-dev --boot B --modes decide loop --items <t1.npz> <t3.npz> --fits <t1.json> <t3.json>]
"""
import argparse
import csv
import json
import os
import sys

import numpy as np
from scipy.stats import chi2

K8 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(K8))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, K8)
import k6_analyse_v02 as A  # noqa: E402
import k8_sim_v01 as S  # noqa: E402
import m_lib_v04 as M  # noqa: E402

DELTA, B_BOOT, SEED, POWER_SEED = A.DELTA, A.B_BOOT, 20261106, 20261107
F_MIN = A.F_MIN
POWER_MIN = A.POWER_MIN
PRACTITIONER = ("B1", "B4")
LEVEL_HK2 = 1 - 0.05 / len(PRACTITIONER)
HK3_ARMS = A.HK3_ARMS
LEVEL_HK3 = 1 - 0.05 / len(HK3_ARMS)
N_SCENES_CONF, DELAYS = A.N_SCENES_CONF, A.DELAYS
EXPERIMENT = A.EXPERIMENT
DEV_SCENES = A.DEV_SCENES
CC = A.STEPS_CC
POP_DECIDE = {
    "PD7_primary": dict(offset=(0,), inpath=(0, 1), gap=(0, 1, 2), steps=CC),
    "PD_inpath": dict(offset=(0,), inpath=(1,), gap=(0, 1, 2), steps=CC),
    "SD1_7_gap_le_5m": dict(offset=(0,), inpath=(0, 1), gap=(0, 1), steps=CC),
    "NIP_not_in_path": dict(offset=(0,), inpath=(0,), gap=(0, 1, 2), steps=CC),
    "SD3_7_all_relied_any_enforcement": dict(offset=(0,), inpath=(0, 1), enforced=(0, 1), satisfied=(0, 1), gap=(0, 1, 2), steps=CC),
}
POP_LOOP = {
    "PL7_offset_le_15m": dict(offset=(0, 1), inpath=(0, 1), gap=(0, 1, 2), steps=CC),
    "PL_offset_le_15m": dict(offset=(0, 1), gap=(0, 1, 2), steps=CC),
    "SL1_7_all_offsets": dict(offset=(0, 1, 2), inpath=(0, 1), gap=(0, 1, 2), steps=CC),
}
CONF_POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")
FLOOR_POPS = ("PD7_primary", "SD1_7_gap_le_5m")
REPORT_POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath", "NIP_not_in_path")
# the 4-cell split of k8_sim_v01's per-decision counts and calibration table: index = near (pair gap <= 5 m) * 2 + in-path
CELLS4 = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3), "NIP_not_in_path": (0, 2)}
V2_DECIDE = {p: (CELLS4[p], (0,)) for p in REPORT_POPS}
V2_LOOP = {"PL7_offset_le_15m": ((0, 1, 2, 3), (0, 1)), "PL_offset_le_15m": ((1, 3), (0, 1)), "SL1_7_all_offsets": ((0, 1, 2, 3), (0, 1, 2))}
CI = {f: i for i, f in enumerate(S.CAL_FIELDS)}
ARM_INDEX = {a: i for i, a in enumerate(S.ARMS)}
PAIRED_ENDPOINTS = ("infeasible_rate", "progress_ratio", "mean_chosen_speed", "divergence_share", "estop_share", "mean_backoff_level",
                    "min_gap_mean", "min_gap_share_lt_1m", "ttc_mean", "ttc_share_lt_2s", "V1_PD7_scene_rate", "V2_PD7_scene_rate",
                    "V1_SD1_7_scene_rate", "V2_SD1_7_scene_rate")
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s"]
SCOPE_NOTES = [
    "Transductive scope: the K7 fits are cross-fitted on 5 log folds of the same 850 nuScenes trainval scenes; the evaluation scenes "
    "are the 840 non-development scenes, held out of their own fold's fit but not of the design (K7 plan section 13).",
    "CANMOT-SC (T1) was tuned on nuScenes val by its authors; its detections and tracks on val are not independent of that tuning.",
    "The tracker does not run in the loop: the recorded tracker output is replayed from the logged ego (D14 v02 section 2).",
]


STRICT_Q = True   # confirmatory: every sup-t quantile must be finite (K7 m3); --allow-dev relaxes it (few scenes: zero-SE cells only)


def sha(p):
    return A.sha(p)


def _q(q, where):
    if np.isfinite(q):
        return float(q)
    assert not STRICT_Q, "non-finite sup-t quantile in " + where
    return None


# ---------------------------------------------------------------- K7's rule with the N1 fix

def hk1_rule(T, cells, scene_of_ep, log_of_ep, W, power_key, fams=None):
    """K6's validity tests on each confirmatory population (k7_analyse_v02.hk1_rule with the R12b N1 fix). T: {population:
    (N, X)} of the arm under test (episode x cell tables). fams: optional precomputed power-qualified masks {population: bool
    array}. Returns the per-population results and HK1a, HK1b, HK1. On PD (no count floor, the narrowed claim) the
    power-qualified family's own sup-t must still not flag any cell (N1): that is K6's HK1a (ii) without the count."""
    one = np.ones((1, len(scene_of_ep)))
    out = {"pops": {}}
    hk1a = hk1b = True
    for k, p in enumerate(CONF_POPS):
        N, X = T[p]
        ev = A.evaluable(N, scene_of_ep, log_of_ep)
        fam = np.flatnonzero(ev)
        est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
        r = {"evaluable": int(len(fam)), "flagged": []}
        if len(fam):
            lb, ub, se, sig, q = A.flag(est, boot, fam, 0.95)
            r["q"] = _q(q, p)
            r["flagged"] = [cells[j][0] for i, j in enumerate(fam) if sig[i]]
            r["max_lb"] = float(np.nanmax(lb))
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        r["pooled"] = None
        if A.evaluable(Np, scene_of_ep, log_of_ep)[0]:
            e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
            lbp, ubp, sep, sigp, qp = A.flag(e1, b1, np.array([0]), 0.95)
            _q(qp, "pooled " + p)
            r["pooled"] = {"E": float(e1[0]), "lb": float(lbp[0]), "ub": float(ubp[0]), "flagged": bool(sigp[0]),
                           "HK1c_ub_le_delta_plus_0.03": bool(ubp[0] <= DELTA + 0.03)}
        a_ok = (not r["flagged"]) and len(fam) >= 1
        b_ok = r["pooled"] is not None and not r["pooled"]["flagged"]
        if fams is not None and p in fams:
            qual = fams[p]
        else:
            pw, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng(list(power_key) + [k]))
            qual = ev & (pw >= POWER_MIN)
            r["power_at_%.2f" % A.POWER_P] = {cells[j][0]: float(pw[j]) for j in fam}
        fq = np.flatnonzero(qual)
        r["family"] = [cells[j][0] for j in fq]
        r["family_size"] = int(len(fq))
        r["family_flagged"] = []
        if len(fq):
            _, _, _, sigf, qf = A.flag(est, boot, fq, 0.95)
            _q(qf, "family " + p)
            r["family_flagged"] = [cells[j][0] for i, j in enumerate(fq) if sigf[i]]
        if p in FLOOR_POPS:
            r["floor_met"] = bool(len(fq) >= F_MIN and not r["family_flagged"])
            a_ok = a_ok and r["floor_met"]
        else:
            a_ok = a_ok and not r["family_flagged"]   # N1 (R12b): K6's own-family no-flag test on PD; only the count floor is dropped
            r["floor_note"] = "reported only: no count floor on PD (in-path non-exceedance is not power-qualified); the own-family no-flag test applies (N1)"
        r["HK1a_met"], r["HK1b_met"] = bool(a_ok), bool(b_ok)
        hk1a &= a_ok
        hk1b &= b_ok
        out["pops"][p] = r
    out["HK1a"], out["HK1b"], out["HK1"] = bool(hk1a), bool(hk1b), bool(hk1a and hk1b)
    return out


# ---------------------------------------------------------------- helpers

def wmean_ci(v, W, one_sided=None):
    """Scene-level mean of a per-key quantity (K6's estimand: the unweighted mean over the keys with a value) with the
    log-cluster bootstrap 95 % interval (weights W, B x keys); one_sided: also the one-sided upper and lower bounds at it."""
    v = np.asarray(v, float)
    ok = np.isfinite(v)
    if not ok.any():
        return {"mean": None, "ci95": None, "n": 0}
    Wk = W[:, ok]
    with np.errstate(invalid="ignore", divide="ignore"):
        bm = (Wk @ v[ok]) / Wk.sum(1)
    out = {"mean": float(v[ok].mean()), "ci95": [float(np.nanquantile(bm, 0.025)), float(np.nanquantile(bm, 0.975))], "n": int(ok.sum())}
    if one_sided is not None:
        out["ub_one_sided"] = float(np.nanquantile(bm, one_sided))
        out["lb_one_sided"] = float(np.nanquantile(bm, 1 - one_sided))
    return out


def scene_mean(vals, kix, n_keys):
    """Per-key mean of a per-decision quantity (NaN where the key has no finite value)."""
    vals = np.asarray(vals, float)
    out = np.full(n_keys, np.nan)
    ok = np.isfinite(vals)
    if ok.any():
        s_ = np.bincount(kix[ok], weights=vals[ok], minlength=n_keys)
        n_ = np.bincount(kix[ok], minlength=n_keys)
        out[n_ > 0] = s_[n_ > 0] / n_[n_ > 0]
    return out


def scene_ratio(num, den, kix, n_keys, eps=1e-9):
    s_n = np.bincount(kix, weights=np.asarray(num, float), minlength=n_keys)
    s_d = np.bincount(kix, weights=np.asarray(den, float), minlength=n_keys)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(s_d > eps, s_n / np.where(s_d > eps, s_d, 1.0), np.nan)


def dec_rows(D, eps, kidx):
    """Per arm: the per-decision rows of the decisions table (dict of arrays) and the key index of each row."""
    ep_key = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps}
    ep_arm = {o["episode"]: o["arm"] for o in eps}
    e = D["episode"]
    arm_of_row = np.array([ep_arm.get(int(x), "") for x in e])
    key_of_row = np.array([ep_key.get(int(x), -1) for x in e])
    out = {}
    for a in sorted(set(ep_arm.values())):
        sel = (arm_of_row == a) & (key_of_row >= 0)
        out[a] = ({f: D[f][sel] for f in D if f != "episode"}, key_of_row[sel])
    return out


def cal_rows(C, eps, kidx):
    """Per arm: the calibration-table rows (key = cell4 * N_L0 + L0, values (n, N_CAL)) and their key index."""
    ep_key = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps}
    ep_arm = {o["episode"]: o["arm"] for o in eps}
    e = C["episode"]
    arm_of_row = np.array([ep_arm.get(int(x), "") for x in e])
    key_of_row = np.array([ep_key.get(int(x), -1) for x in e])
    out = {}
    for a in sorted(set(ep_arm.values())):
        sel = (arm_of_row == a) & (key_of_row >= 0)
        out[a] = (C["key"][sel], C["values"][sel], key_of_row[sel])
    return out


def v2_tables(rows, kix, n_keys, cells4, obs, first_step=False):
    """A1: per key, N = decisions with >= 1 relied-on record in the population (cells4 of the near x in-path split, sensor-offset
    bins obs), X = decisions with >= 1 exceedance among them; first_step: at the first check time (step 0) only."""
    st = rows["stats"].reshape(len(kix), 4, len(S.ST_FIELDS))
    fn, fx = (2, 3) if first_step else (0, 1)
    sel_ob = np.isin(rows["ob"], list(obs))
    n = st[:, list(cells4), fn].sum(1)
    x = st[:, list(cells4), fx].sum(1)
    has = ((n > 0) & sel_ob).astype(float)
    anyx = ((x > 0) & sel_ob).astype(float)
    N = np.bincount(kix, weights=has, minlength=n_keys)
    X = np.bincount(kix, weights=anyx, minlength=n_keys)
    return N[:, None], X[:, None]


def v2_summary(rows, kix, n_keys, W, cells4, obs, first_step=False):
    N, X = v2_tables(rows, kix, n_keys, cells4, obs, first_step)
    one = np.ones((1, n_keys))
    if N.sum() == 0:
        return {"E": None, "ci95": None, "decisions_with_records": 0, "decisions_any_exceed": 0, "decision_level_rate": None}, np.full(n_keys, np.nan)
    est = float(A.rates(N, X, one)[0][0])
    boot = A.rates(N, X, W)[:, 0]
    per_key = np.where(N[:, 0] > 0, X[:, 0] / np.maximum(N[:, 0], 1), np.nan)
    return {"E": est, "ci95": [float(np.nanquantile(boot, 0.025)), float(np.nanquantile(boot, 0.975))],
            "decisions_with_records": int(N.sum()), "decisions_any_exceed": int(X.sum()),
            "decision_level_rate": float(X.sum() / N.sum())}, per_key


def cal_summary(v, n_scenes=None):
    """A6/A7 summaries from summed CAL_FIELDS rows v (N_CAL,): ANEES with its chi-square interval, p_v (below / above), ellipse
    coverage, per-axis exceedance curve, mean NLL, mean energy score, mean margins. Record-weighted."""
    n, nn = v[CI["n"]], v[CI["nees_n"]]
    out = {"records": int(n)}
    if n > 0:
        out["mean_margin_long"], out["mean_margin_lat"] = float(v[CI["mg_long_sum"]] / n), float(v[CI["mg_lat_sum"]] / n)
    if nn > 0:
        anees = float(v[CI["nees_sum"]] / nn)
        lo, hi = chi2.ppf(0.025, 2 * nn) / nn, chi2.ppf(0.975, 2 * nn) / nn
        out.update({"anees": anees, "anees_chi2_interval": [float(lo), float(hi)], "anees_in_interval": bool(lo <= anees <= hi),
                    "p_v": float(v[CI["nees_out"]] / nn), "p_v_above": float(v[CI["nees_hi"]] / nn),
                    "p_v_below": float((v[CI["nees_out"]] - v[CI["nees_hi"]]) / nn),
                    "ellipse_coverage": {("%.2f" % q): float(v[CI["cov%d" % int(round(q * 100))]] / nn) for q in S.COV_LEVELS},
                    "exceedance_curve": {("%g" % d): float(v[CI["x_d%g" % d]] / nn) for d in S.DELTA_CURVE},
                    "nll_mean": float(v[CI["nll_sum"]] / nn), "energy_score_mean": float(v[CI["es_sum"]] / nn), "nees_records": int(nn)})
    else:
        out.update({"anees": None, "p_v": None, "note": "no covariance (mean only)" if n > 0 else "no records"})
    return out


def fallback_shares(fits):
    """A13: from the fits' Mstar_ip_src (per fold and step <= 2 s, 192 = L0 + 96 x in-path), the share of entries that came from
    a coarser level (src > 0) per (L0, in-path) and per cell x in-path set."""
    if fits is None:
        return None
    src = []
    for f in fits["fits"].values():
        for st in STEPS:
            if "Mstar_ip_src" in f[st]:
                src.append(np.asarray(f[st]["Mstar_ip_src"], int))
    if not src:
        return None
    src = np.stack(src)                                              # (folds x steps, 192)
    fb = (src > 0).mean(0)                                           # per (L0 + 96 inpath)
    cells = A.cell_family()
    by_cell = {}
    for name, ids in cells:
        for pop, inps in (("PD7_primary", (0, 1)), ("SD1_7_gap_le_5m", (0, 1)), ("PD_inpath", (1,)), ("NIP_not_in_path", (0,))):
            idx = [l0 + S.N_L0 * ip for l0 in ids for ip in inps]
            by_cell.setdefault(pop, {})[name] = float(fb[idx].mean())
    return {"by_l0_inpath": fb.tolist(), "by_cell": by_cell, "entries": int(src.shape[0]),
            "note": "share of M*'s (fold, step <= 2 s) thresholds in the stratum taken from a coarser level (Mstar_ip_src > 0)"}


def arm_endpoints(rows, kix, n_keys, W):
    """A4, A5, A10 per arm: scene-level means with intervals, and the per-key vectors for the paired contrasts."""
    inf = scene_mean(rows["infeasible"], kix, n_keys)
    pr = scene_ratio(rows["ds_plan"], rows["ds_log"], kix, n_keys)
    vc, vl = rows["v_chosen"], rows["v_log"]
    div = scene_mean((np.abs(vc - vl) > S.DIVERGENCE_MPS).astype(float), kix, n_keys)
    lam = rows["lam"]
    estop = scene_mean((lam == S.LAM_ESTOP).astype(float), kix, n_keys)
    lam0 = np.where(lam == S.LAM_ESTOP, 0.0, lam)
    mbl = scene_mean(lam0, kix, n_keys)
    mg_, tt = rows["min_gap"], rows["ttc"]
    mg_lt1 = np.where(np.isfinite(mg_), (mg_ < 1.0).astype(float), np.nan)
    tt_lt2 = np.where(np.isfinite(tt), (tt < 2.0).astype(float), np.nan)
    vecs = {"infeasible_rate": inf, "progress_ratio": pr, "mean_chosen_speed": scene_mean(vc, kix, n_keys),
            "mean_logged_speed": scene_mean(vl, kix, n_keys), "divergence_share": div, "estop_share": estop, "mean_backoff_level": mbl,
            "min_gap_mean": scene_mean(mg_, kix, n_keys), "min_gap_share_lt_1m": scene_mean(mg_lt1, kix, n_keys),
            "ttc_mean": scene_mean(tt, kix, n_keys), "ttc_share_lt_2s": scene_mean(tt_lt2, kix, n_keys)}
    res = {k: wmean_ci(v, W) for k, v in vecs.items()}
    nd = max(len(lam), 1)
    res["backoff_distribution"] = {("estop" if l_ == S.LAM_ESTOP else "%g" % l_): float((lam == l_).sum() / nd) for l_ in (1.0,) + S.BACKOFF + (S.LAM_ESTOP,)}
    res["decisions"] = int(len(lam))
    res["min_gap_p10_decisions"] = float(np.nanquantile(mg_, 0.10)) if np.isfinite(mg_).any() else None
    res["ttc_p10_decisions"] = float(np.nanquantile(tt, 0.10)) if np.isfinite(tt).any() else None
    res["decisions_with_enforced_pairs"] = int(np.isfinite(mg_).sum())
    return res, vecs


def paired_rows(vecs, arms, W, pairs, endpoints, level=0.95):
    """Paired differences a - b over the keys where both arms have a value (identical decision states in the decision mode)."""
    rows = []
    for a, b in pairs:
        for ep_ in endpoints:
            if ep_ not in vecs.get(a, {}) or ep_ not in vecs.get(b, {}):
                continue
            d = vecs[a][ep_] - vecs[b][ep_]
            r = wmean_ci(d, W, one_sided=level)
            rows.append({"endpoint": ep_, "arm_a": a, "arm_b": b, "mean_diff": r["mean"], "ci95_lo": r["ci95"][0] if r["ci95"] else None,
                         "ci95_hi": r["ci95"][1] if r["ci95"] else None, "ub_one_sided_%.2f" % level: r.get("ub_one_sided"),
                         "lb_one_sided_%.2f" % level: r.get("lb_one_sided"), "n_scenes": r["n"]})
    return rows


def items_counts(path, exclude):
    """A8: the K7 calibration items per population and cell (ref_relied items: one per pair; development scenes excluded)."""
    z = np.load(path)
    names = [str(x) for x in z["scene_names"]]
    keep_s = np.array([n not in exclude for n in names])
    it = {k[5:]: z[k] for k in z.files if k.startswith("item_")}
    sel = keep_s[it["s"]]
    rel = it["ref_relied"] & sel
    pops = {"PD7_primary": rel, "SD1_7_gap_le_5m": rel & (it["gap"] <= S.GAP_BINS[1]), "PD_inpath": rel & it["inpath"],
            "NIP_not_in_path": rel & ~it["inpath"]}
    cells = A.cell_family()
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    out = {"file": os.path.abspath(path), "scenes": int(keep_s.sum()), "scenes_excluded": int((~keep_s).sum()), "items_all_axes": int(sel.sum()),
           "items_ref_relied": int(rel.sum()), "records": int(keep_s[z["rec_s"]].sum()), "by_population": {}}
    for p, m_ in pops.items():
        cj = l0_to_cell[it["l0"][m_]]
        out["by_population"][p] = {"items": int(m_.sum()), "scenes": int(len(np.unique(it["s"][m_]))),
                                   "by_cell": {cells[j][0]: int((cj == j).sum()) for j in range(len(cells))}}
    return out


# ---------------------------------------------------------------- decision mode

def analyse_decide(eps, counts, D, C, log_of_scene, B, rng, power_key, fits=None, items=None):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES and o["arm"] != "LOG"]
    cells = A.cell_family()
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    n_keys = len(keys)
    kidx = {k: i for i, k in enumerate(keys)}
    one = np.ones((1, n_keys))
    res = {"scenes": len(keys), "logs": len(logs), "arms": arms}
    # ---- V1 (K7 form) on the populations, plus the one-step check at step 0 (A1)
    pops, tabs = A.populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_DECIDE)
    res["populations"] = pops
    pops_h0, tabs_h0 = A.populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W,
                                     {p: dict(POP_DECIDE[p], steps=(0,)) for p in REPORT_POPS})
    res["V1_one_step"] = {p: {a: pops_h0[p]["pooled_by_arm"][a] for a in arms} for p in REPORT_POPS}
    # ---- K7's HK1 on M* and the validity tests on every arm (reported; D14 section 6 form B needs them)
    T = {p: (tabs[p][0]["Mstar"], tabs[p][1]["Mstar"]) for p in CONF_POPS}
    res["HK1"] = hk1_rule(T, cells, scene_of_ep, log_of_ep, W, power_key)
    res["evaluable_cells"] = {p: res["HK1"]["pops"][p]["evaluable"] for p in CONF_POPS}
    vba = {"Mstar": res["HK1"]}
    for a in arms:
        if a == "Mstar":
            continue
        Ta = {p: (tabs[p][0][a], tabs[p][1][a]) for p in CONF_POPS}
        vba[a] = hk1_rule(Ta, cells, scene_of_ep, log_of_ep, W, list(power_key) + [100 + ARM_INDEX[a]])
    res["validity_by_arm"] = {a: {"HK1a": v["HK1a"], "HK1b": v["HK1b"], "HK1": v["HK1"],
                                  "HK1c_all_pops": bool(all((v["pops"][p]["pooled"] or {}).get("HK1c_ub_le_delta_plus_0.03", False) for p in CONF_POPS)),
                                  "pops": {p: {k: v["pops"][p].get(k) for k in ("evaluable", "flagged", "pooled", "family_size", "family_flagged", "HK1a_met", "HK1b_met")}
                                           for p in CONF_POPS}} for a, v in vba.items()}
    # ---- HK2 on SD1_7 (K7 form, reported)
    Ns, Xs, ests, boots, evs = tabs["SD1_7_gap_le_5m"]
    m7_flag_sd = set(pops["SD1_7_gap_le_5m"]["cells_by_arm"]["Mstar"]["sig_above_cells"])
    hk2 = {}
    for b in PRACTITIONER:
        if b not in arms:
            continue
        fb = np.flatnonzero(evs[b])
        sig_b = []
        if len(fb):
            _, _, _, sb, _ = A.flag(ests[b], boots[b], fb, LEVEL_HK2)
            sig_b = [cells[j][0] for i, j in enumerate(fb) if sb[i]]
        pr = A.paired(ests, boots, evs, cells, b, "Mstar", LEVEL_HK2)
        hk2[b] = {"flagged_bonferroni_SD1_7": sig_b, "paired": pr,
                  "fails_where_Mstar_holds": [c for c in sig_b if c not in m7_flag_sd and pr.get(c, {}).get("positive", False)]}
    if "B0" in arms:
        fb = np.flatnonzero(evs["B0"])
        if len(fb):
            _, _, _, sb, _ = A.flag(ests["B0"], boots["B0"], fb, LEVEL_HK2)
            hk2["B0_descriptive"] = {"flagged_bonferroni_SD1_7": [cells[j][0] for i, j in enumerate(fb) if sb[i]]}
    res["HK2"] = hk2
    # ---- HK3 (K6's form) and the dominance form (K7 code, unchanged), plus every comparator at the all-comparator level
    inf = {(o["scene"], o["arm"]): (o["infeasible_frames"], o["frames"]) for o in eps}
    scenes = sorted({o["scene"] for o in eps})
    lg = np.array([logs.index(log_of_scene[sc]) for sc in scenes])
    Ws = W_logs[:, lg]
    rate = {a: np.array([inf[(sc, a)][0] / max(inf[(sc, a)][1], 1) for sc in scenes]) for a in arms}
    res["infeasible_rate"] = {a: {"mean": float(rate[a].mean()),
                                  "ci95": [float(x) for x in np.quantile((Ws @ rate[a]) / Ws.sum(1), [0.025, 0.975])]} for a in arms}
    pooled_sd = {}
    for a_ in arms:
        Np, Xp = Ns[a_].sum(1, keepdims=True), Xs[a_].sum(1, keepdims=True)
        pooled_sd[a_] = (A.rates(Np, Xp, one)[0][0], A.rates(Np, Xp, W)[:, 0])
    comps = [x for x in arms if x != "Mstar"]
    level_all = 1 - 0.05 / max(len(comps), 1)
    hk3 = {}
    for b in comps:
        d = rate["Mstar"] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        ub = float(np.quantile(bm, LEVEL_HK3))
        r = {"mean_diff": float(d.mean()), "ub_one_sided_bonferroni": ub, "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
             "lower": bool(ub < 0), "tested": b in HK3_ARMS, "ub_one_sided_all_comparators": float(np.quantile(bm, level_all)),
             "lower_all_comparators": bool(np.quantile(bm, level_all) < 0)}
        if b in HK3_ARMS:
            eb, bb = pooled_sd[b]
            lbb, _, _, sgb, _ = A.flag(np.array([eb]), bb[:, None], np.array([0]), LEVEL_HK3)
            em, bmm = pooled_sd["Mstar"]
            lbd, _, _, sgd, _ = A.flag(np.array([eb - em]) + DELTA, (bb - bmm)[:, None] + DELTA, np.array([0]), LEVEL_HK3)
            r["dominance_reported_only"] = {"pooled_SD1_7_E": float(eb), "pooled_SD1_7_lb": float(lbb[0]), "pooled_SD1_7_flagged": bool(sgb[0]),
                                            "paired_pooled_diff": float(eb - em), "paired_pooled_positive": bool(sgd[0]),
                                            "dominated": bool(r["lower"] or (sgb[0] and sgd[0]))}
        hk3[b] = r
    res["HK3"] = hk3
    h = res["HK1"]
    res["hypotheses"] = {"HK1a": h["HK1a"], "HK1b": h["HK1b"], "HK1": h["HK1"],
                         "family_size_PD7": h["pops"]["PD7_primary"]["family_size"], "family_size_SD1_7": h["pops"]["SD1_7_gap_le_5m"]["family_size"],
                         "family_size_PD_reported": h["pops"]["PD_inpath"]["family_size"], "family_floor": F_MIN,
                         "flagged_cells": {p: h["pops"][p]["flagged"] for p in CONF_POPS},
                         "family_flagged_cells": {p: h["pops"][p]["family_flagged"] for p in CONF_POPS},
                         "pooled_flagged": {p: (h["pops"][p]["pooled"] or {}).get("flagged") for p in CONF_POPS},
                         "HK2": bool(any(v.get("fails_where_Mstar_holds") for k, v in hk2.items() if k in PRACTITIONER)),
                         "HK3": bool(all(hk3.get(b, {}).get("lower", False) for b in HK3_ARMS)),
                         "HK3_not_lower_against": [b for b in HK3_ARMS if not hk3.get(b, {}).get("lower", False)],
                         "HK3_dominance_reported_only": bool(all(hk3.get(b, {}).get("dominance_reported_only", {}).get("dominated", False) for b in HK3_ARMS)),
                         "note": "K7-form hypotheses, reported only (D14 v02 section 4: nothing is gated on nuScenes)"}
    # ---- per-decision endpoints (A4, A5, A10), V2 (A1), calibration (A6, A7)
    rows_by_arm = dec_rows(D, eps, kidx)
    cal_by_arm = cal_rows(C, eps, kidx)
    fb = fallback_shares(fits)
    res["fallback_strata"] = fb
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    endpoints, vecs, v2, v2_h0, cal, cal_cells, cal_l0, consistency = {}, {}, {p: {} for p in REPORT_POPS}, {p: {} for p in REPORT_POPS}, {p: {} for p in REPORT_POPS}, [], [], {}
    for a in arms:
        rows, kix = rows_by_arm[a]
        endpoints[a], vecs[a] = arm_endpoints(rows, kix, n_keys, W)
        for p in REPORT_POPS:
            c4, obs = V2_DECIDE[p]
            v2[p][a], per_key = v2_summary(rows, kix, n_keys, W, c4, obs)
            v2_h0[p][a], _ = v2_summary(rows, kix, n_keys, W, c4, obs, first_step=True)
            if p in ("PD7_primary", "SD1_7_gap_le_5m"):
                vecs[a]["V2_%s_scene_rate" % ("PD7" if p == "PD7_primary" else "SD1_7")] = per_key
                Nc, Xc = tabs[p][0][a], tabs[p][1][a]
                vecs[a]["V1_%s_scene_rate" % ("PD7" if p == "PD7_primary" else "SD1_7")] = np.where(Nc.sum(1) > 0, Xc.sum(1) / np.maximum(Nc.sum(1), 1), np.nan)
        # consistency: the per-decision relied-on counts equal the PD7 records of the counts table
        st = rows["stats"].reshape(len(kix), 4, len(S.ST_FIELDS))
        consistency[a] = {"PD7_records_counts": int(tabs["PD7_primary"][0][a].sum()), "PD7_records_decisions": int(st[:, :, 0].sum()),
                          "PD7_exceed_counts": int(tabs["PD7_primary"][1][a].sum()), "PD7_exceed_decisions": int(st[:, :, 1].sum()),
                          "PD7_records_h0_counts": int(tabs_h0["PD7_primary"][0][a].sum()), "PD7_records_h0_decisions": int(st[:, :, 2].sum())}
        consistency[a]["equal"] = bool(consistency[a]["PD7_records_counts"] == consistency[a]["PD7_records_decisions"]
                                       and consistency[a]["PD7_exceed_counts"] == consistency[a]["PD7_exceed_decisions"]
                                       and consistency[a]["PD7_records_h0_counts"] == consistency[a]["PD7_records_h0_decisions"])
        ckey, cval, ckix = cal_by_arm.get(a, (np.zeros(0, int), np.zeros((0, S.N_CAL)), np.zeros(0, int)))
        c4_of = ckey // S.N_L0
        l0_of = ckey % S.N_L0
        for p in REPORT_POPS:
            m_ = np.isin(c4_of, list(CELLS4[p]))
            cal[p][a] = cal_summary(cval[m_].sum(0))
            # scene-level ANEES (per-key ANEES, then the K6 mean with the log bootstrap)
            if cval[m_][:, CI["nees_n"]].sum() > 0:
                pk = scene_ratio(cval[m_][:, CI["nees_sum"]], cval[m_][:, CI["nees_n"]], ckix[m_], n_keys)
                cal[p][a]["anees_scene_level"] = wmean_ci(pk, W)
            cj = l0_to_cell[l0_of]
            for j, (name, _) in enumerate(cells):
                mm = m_ & (cj == j)
                if not mm.any():
                    continue
                row = {"population": p, "arm": a, "cell": name}
                row.update(flat_cal(cal_summary(cval[mm].sum(0))))
                row["scenes"] = int(len(np.unique(ckix[mm])))
                row["fallback_share"] = fb["by_cell"][p][name] if fb else None
                row["fallback_any"] = (fb["by_cell"][p][name] > 0) if fb else None
                cal_cells.append(row)
        m_ = np.ones(len(ckey), bool)
        for l0 in range(S.N_L0):
            for ip in (0, 1):
                mm = (l0_of == l0) & ((c4_of % 2) == ip)
                if not mm.any():
                    continue
                row = {"population": "PD7_primary", "arm": a, "l0": l0, "l0_name": M.l0_name(l0), "inpath": ip}
                row.update(flat_cal(cal_summary(cval[mm].sum(0))))
                row["scenes"] = int(len(np.unique(ckix[mm])))
                row["fallback_share"] = fb["by_l0_inpath"][l0 + S.N_L0 * ip] if fb else None
                row["fallback_any"] = (fb["by_l0_inpath"][l0 + S.N_L0 * ip] > 0) if fb else None
                cal_l0.append(row)
    res["endpoints_by_arm"] = endpoints
    res["V2"] = v2
    res["V2_one_step"] = v2_h0
    res["calibration"] = cal
    res["consistency_decisions_vs_counts"] = consistency
    res["_csv_cal_cells"], res["_csv_cal_l0"] = cal_cells, cal_l0
    # ---- paired contrasts at identical decision states, every arm pair (A4/A5 statistics)
    pairs = [(a, b) for i, a in enumerate(arms) for b in arms[i + 1:]]
    res["_csv_paired"] = paired_rows(vecs, arms, W, pairs, PAIRED_ENDPOINTS)
    res["paired_vs_Mstar"] = {}
    for r in res["_csv_paired"]:
        if "Mstar" in (r["arm_a"], r["arm_b"]):
            other = r["arm_b"] if r["arm_a"] == "Mstar" else r["arm_a"]
            sgn = 1.0 if r["arm_a"] == "Mstar" else -1.0
            res["paired_vs_Mstar"].setdefault(r["endpoint"], {})[other] = {
                "mean_diff_Mstar_minus_arm": None if r["mean_diff"] is None else sgn * r["mean_diff"],
                "ci95": None if r["ci95_lo"] is None else sorted([sgn * r["ci95_lo"], sgn * r["ci95_hi"]]), "n_scenes": r["n_scenes"]}
    # ---- A2 / A3 sweeps and the retuned nominal
    def sweep_row(kind, val, a):
        pp = pops["PD7_primary"]["pooled_by_arm"].get(a) or {}
        r = {"kind": kind, "value": val, "arm": a, "V1_PD7_E": pp.get("E"), "V1_PD7_lb": pp.get("lb_sim"), "V1_PD7_ub": pp.get("ub_sim"),
             "V1_PD7_flagged": pp.get("sig_above"), "V1_PD7_meets_delta": (pp.get("E") is not None and pp["E"] <= DELTA)}
        for p, lab in (("SD1_7_gap_le_5m", "SD1_7"), ("PD_inpath", "PD"), ("NIP_not_in_path", "NIP")):
            q = pops[p]["pooled_by_arm"].get(a) or {}
            r["V1_%s_E" % lab] = q.get("E")
        r["V2_PD7_E"] = v2["PD7_primary"][a]["E"]
        r["V2_PD7_h0_E"] = v2_h0["PD7_primary"][a]["E"]
        r["infeasible_rate"] = res["infeasible_rate"][a]["mean"]
        r["infeasible_ci95_lo"], r["infeasible_ci95_hi"] = res["infeasible_rate"][a]["ci95"]
        r["progress_ratio"] = endpoints[a]["progress_ratio"]["mean"]
        r["mean_chosen_speed"] = endpoints[a]["mean_chosen_speed"]["mean"]
        r["estop_share"] = endpoints[a]["estop_share"]["mean"]
        r["min_gap_mean"] = endpoints[a]["min_gap_mean"]["mean"]
        r["ttc_mean"] = endpoints[a]["ttc_mean"]["mean"]
        c = cal["PD7_primary"][a]
        r["anees_PD7"], r["p_v_PD7"] = c.get("anees"), c.get("p_v")
        r["mean_margin_long_PD7"], r["mean_margin_lat_PD7"] = c.get("mean_margin_long"), c.get("mean_margin_lat")
        r["HK1_all_pops"] = res["validity_by_arm"][a]["HK1"]
        return r
    sweep = {"alpha": [sweep_row("alpha", S.ALPHA_OF_ARM[a], a) for a in S.ALPHA_ARMS if a in arms],
             "delta_prime": [sweep_row("delta_prime", S.DELTA_OF_ARM[a], a) for a in S.DELTA_ARMS if a in arms],
             "reference": [sweep_row("reference", None, a) for a in ("B0", "B4", "Mstar") if a in arms]}
    qual_d = [(S.DELTA_OF_ARM[r["arm"]], r["arm"]) for r in sweep["delta_prime"] if r["V1_PD7_meets_delta"]]
    qual_a = [(S.ALPHA_OF_ARM[r["arm"]], r["arm"]) for r in sweep["alpha"] if r["V1_PD7_meets_delta"]]
    sweep["retuned_nominal_delta"] = max(qual_d)[0] if qual_d else None
    sweep["retuned_nominal_arm"] = max(qual_d)[1] if qual_d else None
    sweep["retuned_alpha"] = min(qual_a)[0] if qual_a else None
    sweep["retuned_alpha_arm"] = min(qual_a)[1] if qual_a else None
    sweep["reading"] = ("retuned nominal = the LARGEST delta' (the least conservative) whose pooled PD7 scene-level exceedance is <= delta; "
                        "retuned alpha = the smallest alpha with the same property (D14 A3; see the module docstring)")
    for lab, arm_r in (("retuned_nominal", sweep["retuned_nominal_arm"]), ("retuned_alpha", sweep["retuned_alpha_arm"])):
        if arm_r is not None and "Mstar" in arms:
            sweep[lab + "_vs_Mstar"] = {ep_: res["paired_vs_Mstar"].get(ep_, {}).get(arm_r) for ep_ in ("infeasible_rate", "progress_ratio", "mean_chosen_speed",
                                                                                                      "V1_PD7_scene_rate", "V2_PD7_scene_rate", "min_gap_mean", "ttc_mean")}
    res["sweep"] = sweep
    # ---- D14 section 6 forms A, B, C (reported)
    hk1c_m = res["validity_by_arm"]["Mstar"]["HK1c_all_pops"] if "Mstar" in arms else False
    passing = [b for b in comps if res["validity_by_arm"][b]["HK1"]]
    level_pass = 1 - 0.05 / max(len(passing), 1)
    lower_pass = {}
    for b in passing:
        bm = (Ws @ (rate["Mstar"] - rate[b])) / Ws.sum(1)
        lower_pass[b] = bool(np.quantile(bm, level_pass) < 0)
    forms = {"A_K6_form": {"validity_M": bool(h["HK1"] and hk1c_m), "lower_than_every_comparator": bool(all(hk3[b]["lower_all_comparators"] for b in comps)),
                           "level": level_all},
             "B_literature_form": {"validity_M": bool(h["HK1"] and hk1c_m), "comparators_passing_validity": passing,
                                   "lower_than_every_passing_comparator": lower_pass, "level": level_pass,
                                   "vacuous": not passing},
             "C_B_plus_price_bound": {}}
    forms["A_K6_form"]["met"] = bool(forms["A_K6_form"]["validity_M"] and forms["A_K6_form"]["lower_than_every_comparator"])
    forms["B_literature_form"]["met"] = bool(forms["B_literature_form"]["validity_M"] and all(lower_pass.values()))
    if "B4" in arms and "Mstar" in arms:
        d = rate["Mstar"] - rate["B4"]
        bm = (Ws @ d) / Ws.sum(1)
        forms["C_B_plus_price_bound"] = {"Mstar_minus_B4_infeasible": float(d.mean()), "ub_one_sided_0.95": float(np.quantile(bm, 0.95)),
                                         "bound": 0.03, "point_within_bound": bool(d.mean() <= 0.03), "ub_within_bound": bool(np.quantile(bm, 0.95) <= 0.03)}
        forms["C_B_plus_price_bound"]["met_point"] = bool(forms["B_literature_form"]["met"] and d.mean() <= 0.03)
    forms["trade_off_table"] = [{"arm": b, "passes_validity_HK1": res["validity_by_arm"][b]["HK1"],
                                 "HK1c_all_pops": res["validity_by_arm"][b]["HK1c_all_pops"],
                                 "pooled_PD7_E": (pops["PD7_primary"]["pooled_by_arm"].get(b) or {}).get("E"),
                                 "pooled_SD1_7_E": (pops["SD1_7_gap_le_5m"]["pooled_by_arm"].get(b) or {}).get("E"),
                                 "pooled_PD_E": (pops["PD_inpath"]["pooled_by_arm"].get(b) or {}).get("E"),
                                 "infeasible_rate": res["infeasible_rate"][b]["mean"], "progress_ratio": endpoints[b]["progress_ratio"]["mean"],
                                 "Mstar_minus_arm_infeasible": hk3[b]["mean_diff"], "Mstar_lower_at_all_comparator_level": hk3[b]["lower_all_comparators"]}
                                for b in comps]
    forms["note"] = "D14 v02 section 6: reported for the researcher's decision; nothing is gated on nuScenes"
    res["d14_forms"] = forms
    # ---- A8 counts
    cnt = {"scenes": len(keys), "logs": len(logs), "decisions_by_arm": {a: endpoints[a]["decisions"] for a in arms},
           "dev_scenes_excluded": list(DEV_SCENES) if DEV_SCENES else "development run: the development scenes ARE the data (none excluded)",
           "records_by_population": {}, "records_by_cell_Mstar": {}, "notes": SCOPE_NOTES}
    for p in REPORT_POPS:
        Nc, Xc = tabs[p][0], tabs[p][1]
        cnt["records_by_population"][p] = {a: {"records": int(Nc[a].sum()), "exceed": int(Xc[a].sum()),
                                               "scenes": int(len(set(scene_of_ep[Nc[a].sum(1) > 0]))),
                                               "logs": int(len(set(log_of_ep[Nc[a].sum(1) > 0])))} for a in arms}
        if "Mstar" in arms:
            Nm = Nc["Mstar"]
            cnt["records_by_cell_Mstar"][p] = {cells[j][0]: {"records": int(Nm[:, j].sum()), "scenes": int(len(set(scene_of_ep[Nm[:, j] > 0]))),
                                                             "logs": int(len(set(log_of_ep[Nm[:, j] > 0]))),
                                                             "fallback_share": fb["by_cell"][p][cells[j][0]] if fb else None} for j in range(len(cells))}
    if fits is not None:
        cnt["folds"] = {"k_folds": len(fits["fits"]), "seed": fits.get("seed"), "fold_scene_counts": fits.get("fold_scene_counts"),
                        "scenes_in_fits": len(fits.get("scenes", []))}
    if items is not None:
        cnt["items"] = items
    res["counts"] = cnt
    return res


def flat_cal(c):
    out = {"records": c.get("records"), "nees_records": c.get("nees_records"), "anees": c.get("anees"),
           "anees_chi2_lo": (c.get("anees_chi2_interval") or [None, None])[0], "anees_chi2_hi": (c.get("anees_chi2_interval") or [None, None])[1],
           "anees_in_interval": c.get("anees_in_interval"), "p_v": c.get("p_v"), "p_v_below": c.get("p_v_below"), "p_v_above": c.get("p_v_above")}
    for q in S.COV_LEVELS:
        out["cov%d" % int(round(q * 100))] = (c.get("ellipse_coverage") or {}).get("%.2f" % q)
    for d in S.DELTA_CURVE:
        out["exc_d%g" % d] = (c.get("exceedance_curve") or {}).get("%g" % d)
    out["nll_mean"], out["energy_score_mean"] = c.get("nll_mean"), c.get("energy_score_mean")
    out["mean_margin_long"], out["mean_margin_lat"] = c.get("mean_margin_long"), c.get("mean_margin_lat")
    return out


# ---------------------------------------------------------------- closed loop

def analyse_loop(eps, counts, D, C, log_of_scene, B, rng):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES]
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    eps_p = [o for o in eps if o["arm"] != "LOG"]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps_p, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    n_keys = len(keys)
    kidx = {k: i for i, k in enumerate(keys)}
    res = {"episode_keys": len(keys), "logs": len(logs), "arms": arms}
    res["populations"], tabs = A.populations(eps_p, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_LOOP)
    res["progress_vs_Mstar"] = A.progress_contrasts(eps, arms, log_of_scene, logs, W_logs)
    res["outcomes"] = A.outcome_summary(eps)
    rows_by_arm = dec_rows(D, eps_p, kidx)
    endpoints, vecs, v2 = {}, {}, {p: {} for p in V2_LOOP}
    delays = sorted({o["delay_kf"] for o in eps_p})
    for a in arms:
        rows, kix = rows_by_arm[a]
        endpoints[a], vecs[a] = arm_endpoints(rows, kix, n_keys, W)
        endpoints[a]["by_delay"] = {}
        for d in delays:
            sel = np.array([keys[i][1] == d for i in range(n_keys)])
            endpoints[a]["by_delay"][str(d)] = {k: (float(np.nanmean(vecs[a][k][sel])) if np.isfinite(vecs[a][k][sel]).any() else None)
                                                for k in ("infeasible_rate", "progress_ratio", "mean_chosen_speed", "estop_share", "min_gap_mean", "ttc_mean", "divergence_share")}
        for p, (c4, obs) in V2_LOOP.items():
            v2[p][a], per_key = v2_summary(rows, kix, n_keys, W, c4, obs)
            if p == "PL7_offset_le_15m":
                vecs[a]["V2_PL7_scene_rate"] = per_key
    res["endpoints_by_arm"] = endpoints
    res["V2"] = v2
    pairs = [("Mstar", b) for b in arms if b != "Mstar"]
    res["_csv_paired"] = paired_rows(vecs, arms, W, pairs, PAIRED_ENDPOINTS[:10] + ("V2_PL7_scene_rate",))
    res["paired_vs_Mstar"] = {}
    for r in res["_csv_paired"]:
        res["paired_vs_Mstar"].setdefault(r["endpoint"], {})[r["arm_b"]] = {"mean_diff_Mstar_minus_arm": r["mean_diff"], "ci95": [r["ci95_lo"], r["ci95_hi"]], "n_keys": r["n_scenes"]}
    return res


# ---------------------------------------------------------------- verdict-free summaries

def k7_form(d1, d3):
    """What K7's decision rule would have said (reported only; D14 v02 section 4 gates nothing on nuScenes)."""
    h1, h3 = d1["hypotheses"], d3["hypotheses"]
    if h1["HK1"] and h3["HK1"] and h1["HK3"] and h3["HK3"]:
        would = "GO-A" if h1["HK2"] else "GO-B"
    else:
        would = "NO-GO"
    failed = ["%s %s" % (t, k) for t, h in (("T1", h1), ("T3", h3)) for k in ("HK1a", "HK1b", "HK3") if not h[k]]
    return {"note": "K7-form rule evaluated and reported only: D14 v02 section 4 gates nothing on nuScenes", "k7_rule_would_say": would,
            "failed_conditions": failed, "T1": h1, "T3": h3}


# ---------------------------------------------------------------- CSV

def write_csv(path, rows):
    if not rows:
        return
    fields = []
    for r in rows:
        for k in r:
            if k not in fields:
                fields.append(k)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: ("" if v is None else v) for k, v in r.items()})


def csv_tables_decide(res, tag, csv_dir):
    arms = res["arms"]
    cells = A.cell_family()
    pops = res["populations"]
    rows = []
    for a in arms:
        e = res["endpoints_by_arm"][a]
        r = {"arm": a, "alpha": S.ALPHA_OF_ARM.get(a), "delta_prime": S.DELTA_OF_ARM.get(a), "decisions": e["decisions"]}
        r["infeasible_rate"] = res["infeasible_rate"][a]["mean"]
        r["infeasible_ci95_lo"], r["infeasible_ci95_hi"] = res["infeasible_rate"][a]["ci95"]
        for k in ("progress_ratio", "mean_chosen_speed", "mean_logged_speed", "divergence_share", "estop_share", "mean_backoff_level", "min_gap_mean",
                  "min_gap_share_lt_1m", "ttc_mean", "ttc_share_lt_2s"):
            r[k] = e[k]["mean"]
            r[k + "_ci95_lo"], r[k + "_ci95_hi"] = (e[k]["ci95"] or [None, None])
        for lev, sh in e["backoff_distribution"].items():
            r["backoff_share_" + lev] = sh
        r["min_gap_p10_decisions"], r["ttc_p10_decisions"] = e["min_gap_p10_decisions"], e["ttc_p10_decisions"]
        for p, lab in (("PD7_primary", "PD7"), ("SD1_7_gap_le_5m", "SD1_7"), ("PD_inpath", "PD"), ("NIP_not_in_path", "NIP")):
            pp = pops[p]["pooled_by_arm"].get(a) or {}
            r["V1_%s_E" % lab], r["V1_%s_lb" % lab], r["V1_%s_ub" % lab], r["V1_%s_flagged" % lab] = pp.get("E"), pp.get("lb_sim"), pp.get("ub_sim"), pp.get("sig_above")
            r["V1_%s_records" % lab] = pp.get("records")
            r["V1_%s_h0_E" % lab] = (res["V1_one_step"][p].get(a) or {}).get("E")
            r["V2_%s_E" % lab], r["V2_%s_lo" % lab], r["V2_%s_hi" % lab] = res["V2"][p][a]["E"], *(res["V2"][p][a]["ci95"] or [None, None])
            r["V2_%s_h0_E" % lab] = res["V2_one_step"][p][a]["E"]
            r["cells_flagged_%s" % lab] = len(pops[p]["cells_by_arm"][a]["sig_above_cells"])
            r["cells_evaluable_%s" % lab] = len(pops[p]["cells_by_arm"][a]["family"])
            c = res["calibration"][p][a]
            r["ANEES_%s" % lab], r["p_v_%s" % lab] = c.get("anees"), c.get("p_v")
            r["cov95_%s" % lab] = (c.get("ellipse_coverage") or {}).get("0.95")
            r["NLL_%s" % lab], r["ES_%s" % lab] = c.get("nll_mean"), c.get("energy_score_mean")
            r["margin_long_%s" % lab], r["margin_lat_%s" % lab] = c.get("mean_margin_long"), c.get("mean_margin_lat")
        v = res["validity_by_arm"][a]
        r["HK1a"], r["HK1b"], r["HK1"], r["HK1c_all_pops"] = v["HK1a"], v["HK1b"], v["HK1"], v["HK1c_all_pops"]
        if a != "Mstar":
            r["Mstar_minus_arm_infeasible"] = res["HK3"][a]["mean_diff"]
            r["Mstar_lower_bonferroni4"] = res["HK3"][a]["lower"]
        rows.append(r)
    write_csv(os.path.join(csv_dir, "k8_%s_decide_arms.csv" % tag), rows)
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            il = pops[p]["cells_by_arm"][a]
            for name, _ in cells:
                c = il["cells"].get(name)
                fb = ((res["fallback_strata"] or {}).get("by_cell", {}).get(p, {}) or {}).get(name)
                if c is not None:
                    rows.append({"population": p, "arm": a, "cell": name, "evaluable": True, "E": c["E"], "lb_sim": c["lb_sim"], "ub_sim": c["ub_sim"], "se": c["se"],
                                 "sig_above": c["sig_above"], "records": c["records"], "exceed": c["exceed"], "E_rec": c["E_rec"], "scenes": c["scenes"],
                                 "fallback_share": fb, "fallback_any": None if fb is None else fb > 0})
                else:
                    d = il["descriptive"].get(name, {})
                    rows.append({"population": p, "arm": a, "cell": name, "evaluable": False, "E": d.get("E"), "records": d.get("records"), "scenes": d.get("scenes"),
                                 "fallback_share": fb, "fallback_any": None if fb is None else fb > 0})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cells.csv" % tag), rows)
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            for lab, src in (("all_steps", res["V2"]), ("step0", res["V2_one_step"])):
                v = src[p][a]
                rows.append({"population": p, "arm": a, "steps": lab, "E": v["E"], "ci95_lo": (v["ci95"] or [None, None])[0], "ci95_hi": (v["ci95"] or [None, None])[1],
                             "decisions_with_records": v["decisions_with_records"], "decisions_any_exceed": v["decisions_any_exceed"],
                             "decision_level_rate": v["decision_level_rate"]})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_v2.csv" % tag), rows)
    sw = res["sweep"]
    write_csv(os.path.join(csv_dir, "k8_%s_decide_sweep.csv" % tag), sw["alpha"] + sw["delta_prime"] + sw["reference"])
    write_csv(os.path.join(csv_dir, "k8_%s_decide_paired.csv" % tag), res["_csv_paired"])
    rows = []
    for a in arms:
        v = res["validity_by_arm"][a]
        for p in CONF_POPS:
            q = v["pops"][p]
            pl = q["pooled"] or {}
            rows.append({"arm": a, "population": p, "HK1a_met": q["HK1a_met"], "HK1b_met": q["HK1b_met"], "evaluable": q["evaluable"], "flagged": ";".join(q["flagged"]),
                         "pooled_E": pl.get("E"), "pooled_lb": pl.get("lb"), "pooled_ub": pl.get("ub"), "pooled_flagged": pl.get("flagged"),
                         "HK1c": pl.get("HK1c_ub_le_delta_plus_0.03"), "family_size": q["family_size"], "family_flagged": ";".join(q["family_flagged"])})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_validity.csv" % tag), rows)
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cal_cells.csv" % tag), res["_csv_cal_cells"])
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cal_l0_PD7.csv" % tag), res["_csv_cal_l0"])
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            c = res["counts"]["records_by_population"][p][a]
            rows.append({"population": p, "arm": a, **c, "decisions": res["counts"]["decisions_by_arm"][a]})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_counts.csv" % tag), rows)
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            rows.append({"population": p, "arm": a, **flat_cal(res["calibration"][p][a]),
                         "anees_scene_level": (res["calibration"][p][a].get("anees_scene_level") or {}).get("mean")})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_calibration.csv" % tag), rows)
    write_csv(os.path.join(csv_dir, "k8_%s_decide_tradeoff.csv" % tag), res["d14_forms"]["trade_off_table"])


def csv_tables_loop(res, tag, csv_dir):
    rows = []
    for a in res["arms"]:
        e = res["endpoints_by_arm"][a]
        o = res["outcomes"].get(a, {})
        r = {"arm": a, "episodes": o.get("episodes"), "progress_mean_K6": o.get("progress_mean"), "at_fault_tracked": o.get("at_fault_tracked"),
             "at_fault_tracked_fallback_related": o.get("at_fault_tracked_fallback_related"), "at_fault_untracked": o.get("at_fault_untracked"),
             "infeasible_frame_share_K6": o.get("infeasible_frame_share"), "emergency_stop_frame_share": o.get("emergency_stop_frame_share"),
             "hard_brake_frame_share": o.get("hard_brake_frame_share"), "blocked_s_mean": o.get("blocked_s_mean"),
             "front_buffer_intrusions_per_episode": o.get("front_buffer_intrusions_per_episode")}
        for k in ("infeasible_rate", "progress_ratio", "mean_chosen_speed", "mean_logged_speed", "divergence_share", "estop_share", "mean_backoff_level",
                  "min_gap_mean", "min_gap_share_lt_1m", "ttc_mean", "ttc_share_lt_2s"):
            r[k] = e[k]["mean"]
            r[k + "_ci95_lo"], r[k + "_ci95_hi"] = (e[k]["ci95"] or [None, None])
        for lev, sh in e["backoff_distribution"].items():
            r["backoff_share_" + lev] = sh
        for d, bd in e["by_delay"].items():
            for k, v in bd.items():
                r["%s_delay%s" % (k, d)] = v
        for p, lab in (("PL7_offset_le_15m", "PL7"), ("PL_offset_le_15m", "PL"), ("SL1_7_all_offsets", "SL1_7")):
            pp = res["populations"][p]["pooled_by_arm"].get(a) or {}
            r["V1_%s_E" % lab], r["V1_%s_ub" % lab], r["V1_%s_flagged" % lab] = pp.get("E"), pp.get("ub_sim"), pp.get("sig_above")
            r["V2_%s_E" % lab] = res["V2"][p][a]["E"]
        if a != "Mstar" and ("Mstar-%s" % a) in res["progress_vs_Mstar"]:
            r["progress_Mstar_minus_arm"] = res["progress_vs_Mstar"]["Mstar-%s" % a]["mean_diff"]
        rows.append(r)
    write_csv(os.path.join(csv_dir, "k8_%s_loop_arms.csv" % tag), rows)
    write_csv(os.path.join(csv_dir, "k8_%s_loop_paired_vs_Mstar.csv" % tag), res["_csv_paired"])


def strip_csv_payload(res):
    return {k: v for k, v in res.items() if not k.startswith("_csv_")}


# ---------------------------------------------------------------- binding and main

def check_binding(prereg, runs, tags, manifests):
    """Confirmatory binding (as k7_analyse_v02.check_binding, for a future K8 freeze). Not used under --allow-dev."""
    import k8_run_v01 as R
    assert list(tags) == ["t1", "t3"], "the tags must be t1 t3, in this order"
    side, hashes = R.frozen_hashes(prereg)
    for p in manifests:
        assert sha(p) in hashes, "a manifest passed to the analysis is not frozen: " + p
    rec = open(os.path.join(os.path.dirname(prereg), "K8_FREEZE_RECORD_v01.txt"), encoding="utf-8").read()
    assert side in rec, "the plan sidecar differs from the freeze record"
    for p in (os.path.abspath(__file__), A.__file__, M.__file__, S.__file__):
        assert sha(p) in hashes, "analysis input not frozen: " + p
    for tag in tags:
        for mode in ("decide", "loop"):
            rr = json.load(open(os.path.join(runs, "run_record_%s_%s.json" % (tag, mode))))
            assert rr["prereg"] == side and rr["mode"] == mode, "run %s_%s was not made under the frozen K8 plan" % (tag, mode)
            for k in ("fits_sha256", "sim_sha256", "runner_sha256"):
                assert rr[k] in hashes, "%s of run %s_%s is not frozen" % (k, tag, mode)
            assert rr["sim_sha256"] == sha(S.__file__), "run %s_%s did not use k8_sim_v01" % (tag, mode)
            assert all(h in hashes for h in rr["manifest_sha256"]), "a cache manifest of run %s_%s is not frozen" % (tag, mode)
            assert rr["arms"] == list(S.ARMS) and rr["delays_kf"] == DELAYS and rr["scenes"] == N_SCENES_CONF, "incomplete design " + tag
            n_ep = N_SCENES_CONF * len(S.ARMS) * len(DELAYS) if mode == "loop" else N_SCENES_CONF * (len(S.ARMS) - 1)
            assert rr["episodes"] == n_ep, "incomplete run %s_%s" % (tag, mode)
            assert rr["tag"] == "%s_%s" % (tag, mode), "run record %s_%s carries another tag" % (tag, mode)
            assert sha(rr["fits"]) == rr["fits_sha256"], "the fits file of run %s_%s differs from its run record" % (tag, mode)
            fits = json.load(open(rr["fits"]))
            assert fits.get("k7") is True, "run %s_%s did not use the K7 fits" % (tag, mode)
            exps = {json.load(open(os.path.join(c, "MANIFEST.json")))["experiment"] for c in rr["caches"]}
            same_tracker = (fits["tags"] == ["%s_train" % tag, "%s_val" % tag] and exps == {EXPERIMENT[tag]}
                            and all(("cache_v02_%s_" % tag) in c for c in rr["caches"]))
            assert same_tracker, "run %s_%s uses another tracker's fits or caches" % (tag, mode)
            for f, ext in (("episodes", "jsonl"), ("counts", "npz"), ("decisions", "npz"), ("cal", "npz")):
                assert sha(os.path.join(runs, "%s_%s_%s.%s" % (f, tag, mode, ext))) == rr["%s_sha256" % f], "%s of run %s_%s changed" % (f, tag, mode)
    return side


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tags", nargs=2, required=True)
    ap.add_argument("--manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv-dir", default=None)
    ap.add_argument("--prereg", default=None)
    ap.add_argument("--allow-dev", action="store_true", help="development checks only: mini scenes, no plan check")
    ap.add_argument("--boot", type=int, default=B_BOOT)
    ap.add_argument("--modes", nargs="+", default=["decide", "loop"])
    ap.add_argument("--items", nargs=2, default=None, help="K7 items files (t1, t3) for the A8 item counts")
    ap.add_argument("--fits", nargs=2, default=None, help="fits files (t1, t3) for the A13 fallback flags and the A8 fold counts")
    a = ap.parse_args()
    global DEV_SCENES, STRICT_Q
    if a.allow_dev:
        DEV_SCENES = ()
        A.MIN_SCENES, A.MIN_LOGS = 2, 1
        STRICT_Q = False
        side = None
    else:
        assert a.boot == B_BOOT and a.modes == ["decide", "loop"], "the confirmatory analysis is fixed: B = %d, both modes" % B_BOOT
        assert a.prereg, "the confirmatory analysis needs --prereg"
        side = check_binding(a.prereg, a.runs, a.tags, a.manifests)
    csv_dir = a.csv_dir or os.path.dirname(os.path.abspath(a.out))
    os.makedirs(csv_dir, exist_ok=True)
    log_of_scene = {}
    for p in a.manifests:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    if not a.allow_dev:
        for tag in a.tags:
            for c in json.load(open(os.path.join(a.runs, "run_record_%s_decide.json" % tag)))["caches"]:
                for s_, info in json.load(open(os.path.join(c, "MANIFEST.json")))["scenes"].items():
                    assert log_of_scene.get(s_) == info["log"], "scene -> log map of %s differs for %s" % (tag, s_)
    out = {"design": "D14_K8_DESIGN_v02", "delta": DELTA, "boot": a.boot, "prereg_sha256": side, "dev_mode": bool(a.allow_dev),
           "arms": list(S.ARMS), "alpha_of_arm": S.ALPHA_OF_ARM, "delta_of_arm": S.DELTA_OF_ARM,
           "sim_sha256": sha(S.__file__), "analysis_sha256": sha(os.path.abspath(__file__)), "k6_analyse_sha256": sha(A.__file__),
           "decide": {}, "loop": {}}
    for i, tag in enumerate(a.tags):
        fits = json.load(open(a.fits[i])) if a.fits else None
        items = items_counts(a.items[i], set(DEV_SCENES)) if a.items else None
        for mode in a.modes:
            eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s_%s.jsonl" % (tag, mode)))]
            counts = dict(np.load(os.path.join(a.runs, "counts_%s_%s.npz" % (tag, mode))))
            D = dict(np.load(os.path.join(a.runs, "decisions_%s_%s.npz" % (tag, mode))))
            C = dict(np.load(os.path.join(a.runs, "cal_%s_%s.npz" % (tag, mode))))
            if mode == "decide":
                r = analyse_decide(eps, counts, D, C, log_of_scene, a.boot, np.random.default_rng([SEED, i, 0]), [POWER_SEED, i], fits, items)
                csv_tables_decide(r, tag, csv_dir)
                out["decide"][tag] = strip_csv_payload(r)
            else:
                r = analyse_loop(eps, counts, D, C, log_of_scene, a.boot, np.random.default_rng([SEED, i, 1]))
                csv_tables_loop(r, tag, csv_dir)
                out["loop"][tag] = strip_csv_payload(r)
    if "decide" in a.modes and len(out["decide"]) == 2:
        out["k7_form_reported_only"] = k7_form(out["decide"][a.tags[0]], out["decide"][a.tags[1]])
        print(json.dumps(out["k7_form_reported_only"]["k7_rule_would_say"]))
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print("K8 ANALYSIS V01 DONE")


if __name__ == "__main__":
    main()
