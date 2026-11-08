#!/usr/bin/env python3
"""K8 analysis (Claude line, v02, 1 Nov 2026). Implements 90_DECISIONS/D14_K8_DESIGN_v04.md sections 2-6 on the runs of
k8_run_v02 / k8_sim_v02 and the items of k8_items_v02. Derived from k8_analyse_v01.py (kept); every K7-form computation is
unchanged in form. Nothing is gated on nuScenes (D14 v04 section 4): the K7-form hypotheses and the section 6 forms are REPORTED.

Changes from k8_analyse_v01 (mapped to 70_TESTS/R15_K8_CODE_AND_DEV_REVIEW_v01.md; file-by-file list in README_K8_v02.md):
  C1  three run modes, exactly one: --allow-dev (the 10 development scenes; relaxed evaluability, as v01), --exploratory (D14
      v04 section 5.1: the confirmatory statistics -- evaluable cell >= 39 scenes from >= 8 logs, finite sup-t quantiles, the
      development scenes excluded and asserted absent, B = 2000, both modes -- on runs whose run and launch records carry the
      hashes of the sim, runner, fits, manifests, k6_sim_v02, this analysis, k6_analyse_v02 and m_lib_v04, asserted equal to
      the current files), --prereg (a frozen K8 plan; v01's check_binding plus k6_sim_v02, m12). Every output (JSON and every
      CSV row) carries the stamp of its mode; the exploratory one is "EXPLORATORY: nuScenes development evidence, not a
      confirmation".
  M1  A5: the time to first violation (TTV) of the buffered footprint along the chosen plan over the enforced tracks, clipped at
      4 s, and the share of decisions with TTV < 2 s replace the TTC proxy in every table (kept as ttc_proxy_v01, secondary);
      the minimum gap is split by in-path / not in-path.
  M2  Form A: M* against K6's HK3 set B0, B1, B4, B9 at 1 - 0.05/4; the all-arm contrast is a separate descriptive row.
  M3  A2-A3: two-sided grids, one curve (a delta' arm sits at alpha_eq = (z_{1-delta'} / z_0.95)^2); the RETUNED arm is the least
      conservative point of the curve (smallest alpha_eq) whose pooled PD7, SD1_7 and PD scene-level exceedances are all <=
      delta (M*'s criterion), chosen cross-fitted over the 5 log folds of the fits (selected on 4 folds, applied to the 5th),
      with a boundary flag; RETUNED is analysed as a composite arm (each scene takes the episodes of its fold's selection).
  M4  A6 primary: on the arm-independent K7 PD7 items (k8_items_v02: the ref-relied record of every enforced pair with a
      ground-truth annotation; identical outcome set for every arm), per arm under the covariance documented in COV_DOC; the
      relied-pair table of v01 is kept as the secondary A6 (delta' rows dropped, m14).
  M5  A6 summaries: the scene-level bootstrap ANEES first, the chi-square interval labelled nominal (it assumes independent
      records, m11), the median NEES, the 1 %-trimmed ANEES, the share of the NEES sum in the top 1 %, p_v split below / above,
      the gross-error records (NEES above the chi-square(2) 1 - 1e-6 quantile under B0's raw covariance) listed.
  M6  A1: V2 read against its per-constraint reference 1 - (1 - delta)^n_tracks (per decision, n_tracks = tracks with a relied
      record); variants V2_viol (D > G), V2_near (pair gap <= 5 m), V2_binding (slack <= 0.5 m), V2_exec (executed margin
      lam * margin, m9), V2_dedup (A14); the one-step check kept; V2 is over the 4 annotated calibrated steps (m8).
  m1  cites D14 v04. m2: each population is tested at 0.95 with no Bonferroni split across populations (the stricter choice for
      a no-flag test). m3: Form B validity = HK1 and HK1c on PD7, SD1_7 and PD, identically for M* and every comparator. m4
      (A13): the fallback share per cell is record-weighted from each record's own fold, step, L0 and in-path flag (M*'s
      thresholds); a cell with share >= 0.5 is labelled "coarser bound only" (PM1). m7 (A14): duplicate tracks counted, V1 / V2
      / A6 de-duplicated sensitivities. m10: in decision mode the divergence share is labelled a hard-braking indicator. m12:
      --allow-dev asserts that every run record says DEV MODE and lists development scenes only.
Outputs: one JSON (--out) and CSV tables (--csv-dir): k8_<tag>_<mode>_<table>.csv.
Usage: python -B k8_analyse_v02.py --runs <dir> --tags t1 t3 --manifests <t1 train/val MANIFEST.json> --out <json> --csv-dir <dir>
       (--allow-dev | --exploratory | --prereg <plan.md>) --fits <t1.json> <t3.json> --items <t1 items npz> <t3 items npz>
       [--boot B --modes decide loop]
"""
import argparse
import csv
import json
import math
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
import k8_sim_v02 as S  # noqa: E402
import m_lib_v04 as M  # noqa: E402

DESIGN = "D14_K8_DESIGN_v04"
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
DEV_SCENES_K6 = A.DEV_SCENES
CC = A.STEPS_CC
RETUNED = "RETUNED"
ALL_ARMS = S.ARMS + (RETUNED,)
ARM_INDEX = {a: i for i, a in enumerate(ALL_ARMS)}
FORM_A_ARMS = HK3_ARMS                                   # R15 M2: K6's HK3 set B0, B1, B4, B9 (never Z0 or a sweep arm)
LEVEL_FORM_A = 1 - 0.05 / len(FORM_A_ARMS)
FORM_B_COMPARATORS = ("B0", "B1", "B3", "B4", "B6", "B9", RETUNED)   # every margin method; the sweep's single cross-fitted point
STAMPS = {"dev": "DEV MODE: the 10 development scenes (nuScenes-mini); diagnostics only, not evidence",
          "exploratory": "EXPLORATORY: nuScenes development evidence, not a confirmation",
          "confirmatory": "CONFIRMATORY: run under a frozen K8 plan"}
STAMP = STAMPS["dev"]
EXPLORATORY_RUN_STAMP = "EXPLORATORY: nuScenes development evidence, not a confirmation"   # k8_run_v02 / k8_items_v02
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
POP_LAB = {"PD7_primary": "PD7", "SD1_7_gap_le_5m": "SD1_7", "PD_inpath": "PD", "NIP_not_in_path": "NIP",
           "PL7_offset_le_15m": "PL7", "PL_offset_le_15m": "PL", "SL1_7_all_offsets": "SL1_7"}
# the 4-cell split of k8_sim_v02's per-decision counts: index = near (pair gap <= 5 m) * 2 + in-path
CELLS4 = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3), "NIP_not_in_path": (0, 2)}
NEAR_CELLS = (2, 3)
V2_DECIDE = {p: (CELLS4[p], (0,)) for p in REPORT_POPS}
V2_LOOP = {"PL7_offset_le_15m": ((0, 1, 2, 3), (0, 1)), "PL_offset_le_15m": ((1, 3), (0, 1)), "SL1_7_all_offsets": ((0, 1, 2, 3), (0, 1, 2))}
# V2 variants (D14 v04 A1): (record field, exceedance field, restrict to near cells, with the reference)
V2_VARIANTS = {"V2": ("n", "x", False, True), "V2_one_step": ("n_h0", "x_h0", False, False), "V2_viol": ("n", "v", False, False),
               "V2_near": ("n", "x", True, True), "V2_binding": ("nb", "xb", False, False), "V2_exec": ("ne", "xe", False, False),
               "V2_dedup": ("nd", "xd", False, False)}
SI = {f: i for i, f in enumerate(S.ST_FIELDS)}
NF = len(S.ST_FIELDS)
CI = {f: i for i, f in enumerate(S.CAL_FIELDS)}
PAIRED_ENDPOINTS = ("infeasible_rate", "progress_ratio", "mean_chosen_speed", "divergence_share", "estop_share", "mean_backoff_level",
                    "min_gap_mean", "min_gap_share_lt_1m", "min_gap_ip_mean", "ttv_mean", "ttv_share_lt_2s", "ttv_enf_share_lt_4s",
                    "V1_PD7_scene_rate", "V2_PD7_scene_rate", "V1_SD1_7_scene_rate", "V2_SD1_7_scene_rate",
                    "V2_viol_PD7_scene_rate", "V2_binding_PD7_scene_rate")
LOOP_PAIRED = PAIRED_ENDPOINTS[:12] + ("V2_PL7_scene_rate", "V2_viol_PL7_scene_rate")
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s"]
GROSS_NEES = 27.631021115871036          # chi-square(2) quantile at 1 - 1e-6: a "gross error" under B0's raw covariance (M5)
A6_ARMS = ("B0", "B1", "B3", "B4", "B6", "B9", "Mstar") + S.ALPHA_ARMS + (RETUNED,)   # delta' arms dropped (m14): their covariance is B0's
COV_DOC = {
    "Z0": "none (mean only)",
    "B0": "S_h + sigma_a^2 I (the raw tracker covariance with the annotation term)",
    "B0a<alpha>": "alpha (S_h + sigma_a^2 I) (sigma_a^2 scaled with the covariance: effective floor sqrt(alpha) 0.10 m)",
    "B1": "k(group, range) (S_h + sigma_a^2 I), the NEES-scaled covariance",
    "B3": "(c_B3 / z)^2 (S_h + sigma_a^2 I)",
    "B4": "(c_B4 / z)^2 (S_h + sigma_a^2 I)",
    "B6": "A (S_h + sigma_a^2 I) A, A = (c_long / z) a_l a_l' + (c_lat / z) a_t a_t', thresholds B6_ip(L0, in-path) (no motion strata)",
    "Mstar": "A (S_h + sigma_a^2 I) A as B6 with Mstar_ip(L0, in-path): m_lib_v04.deploy_covariance",
    "B9": "(r^2 / chi2_{2,0.95}) I, the isotropic Gaussian whose 95 % circle is the norm ball",
    "RETUNED": "alpha_sel(fold) (S_h + sigma_a^2 I), the cross-fitted point of the one curve",
    "B0d<delta'>": "B0's covariance (only the quantile changes): dropped from A6 (m14)",
}
SCOPE_NOTES = [
    "Transductive scope: the K7 fits are cross-fitted on 5 log folds of the same 850 nuScenes trainval scenes; the evaluation scenes "
    "are the 840 non-development scenes, held out of their own fold's fit but not of the design (K7 plan section 13).",
    "CANMOT-SC (T1) was tuned on nuScenes val by its authors; its detections and tracks on val are not independent of that tuning.",
    "The tracker does not run in the loop: the recorded tracker output is replayed from the logged ego (D14 v04 section 2).",
    "Each population is tested at 0.95 with no Bonferroni split across the three populations (R15 m2: the stricter choice for a "
    "no-flag test).",
    "Backed-off decisions are scored at the full margin in V1 / V2 (PD7's inherited selection); V2_exec scores the executed margin "
    "lam * margin (R15 m9).",
]
NONROW = ("st_fields", "trk_fields", "fields", "stamp")

STRICT_Q = True   # every sup-t quantile must be finite (K7 m3); --allow-dev relaxes it (few scenes: zero-SE cells only)


def sha(p):
    return A.sha(p)


def _q(q, where):
    if np.isfinite(q):
        return float(q)
    assert not STRICT_Q, "non-finite sup-t quantile in " + where
    return None


# ---------------------------------------------------------------- K7's rule with the N1 fix (unchanged from v01)

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


def form_valid(v):
    """D14 v04 section 6 (i), applied identically to M* and to every comparator (R15 m3): HK1 (HK1a and HK1b on PD7, SD1_7 and
    PD) and HK1c (pooled one-sided upper bound <= delta + 0.03) on all three."""
    return bool(v["HK1"] and all((v["pops"][p]["pooled"] or {}).get("HK1c_ub_le_delta_plus_0.03", False) for p in CONF_POPS))


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


def ratio_ci(num, den, W):
    """Record-weighted ratio sum(num) / sum(den) over keys with the log-cluster bootstrap 95 % interval (num, den per key)."""
    num, den = np.asarray(num, float), np.asarray(den, float)
    if den.sum() <= 0:
        return {"value": None, "ci95": None}
    with np.errstate(invalid="ignore", divide="ignore"):
        b = (W @ num) / (W @ den)
    return {"value": float(num.sum() / den.sum()), "ci95": [float(np.nanquantile(b, 0.025)), float(np.nanquantile(b, 0.975))]}


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


def _row_arrays(T, ep_key="episode"):
    n = len(T[ep_key])
    return [k for k, v in T.items() if k not in NONROW and isinstance(v, np.ndarray) and v.ndim >= 1 and len(v) == n]


def dec_rows(D, eps, kidx):
    """Per arm: the per-decision rows of the decisions table (dict of arrays) and the key index of each row."""
    ep_key = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps}
    ep_arm = {o["episode"]: o["arm"] for o in eps}
    e = D["episode"]
    arm_of_row = np.array([ep_arm.get(int(x), "") for x in e])
    key_of_row = np.array([ep_key.get(int(x), -1) for x in e])
    fields = [f for f in _row_arrays(D) if f != "episode"]
    out = {}
    for a in sorted(set(ep_arm.values())):
        sel = (arm_of_row == a) & (key_of_row >= 0)
        out[a] = ({f: D[f][sel] for f in fields}, key_of_row[sel])
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


# ---------------------------------------------------------------- A1: V2 and its variants

def n_tracks(trk, cells4):
    """Per decision: the tracks with a relied-on record in the cell set (TRK index 3 * in-path + {0 far only, 1 near only,
    2 both}; cell index = near * 2 + in-path). A track counts when its in-path flag matches and it has a record in a member
    cell."""
    c = set(cells4)
    trk = np.asarray(trk, float)
    tot = np.zeros(len(trk))
    for ip in (0, 1):
        far_in, near_in = ip in c, (2 + ip) in c
        if far_in and near_in:
            tot += trk[:, 3 * ip] + trk[:, 3 * ip + 1] + trk[:, 3 * ip + 2]
        elif far_in:
            tot += trk[:, 3 * ip] + trk[:, 3 * ip + 2]
        elif near_in:
            tot += trk[:, 3 * ip + 1] + trk[:, 3 * ip + 2]
    return tot


def v2_tables(rows, kix, n_keys, cells4, obs, nf="n", xf="x", ref=False):
    """A1: per key, N = decisions with >= 1 record (field nf) in the population (cells4 of the near x in-path split, sensor-
    offset bins obs), X = decisions with >= 1 exceedance (field xf) among them, and (ref) R = the sum over those decisions of
    the per-constraint reference 1 - (1 - delta)^n_tracks."""
    st = rows["stats"].reshape(len(kix), 4, NF).astype(float)
    sel_ob = np.isin(rows["ob"], list(obs))
    n = st[:, list(cells4), SI[nf]].sum(1)
    x = st[:, list(cells4), SI[xf]].sum(1)
    has = (n > 0) & sel_ob
    anyx = (x > 0) & has
    N = np.bincount(kix, weights=has.astype(float), minlength=n_keys)
    X = np.bincount(kix, weights=anyx.astype(float), minlength=n_keys)
    R = T = None
    if ref:
        nt = n_tracks(rows["trk"], cells4)
        R = np.bincount(kix, weights=np.where(has, 1.0 - (1.0 - DELTA) ** nt, 0.0), minlength=n_keys)
        T = np.bincount(kix, weights=np.where(has, nt, 0.0), minlength=n_keys)
    return N[:, None], X[:, None], R, T


def v2_summary(rows, kix, n_keys, W, cells4, obs, nf="n", xf="x", ref=False):
    """Scene-level V2 (K6's estimand: per scene the share of decisions with an exceedance, then the mean over scenes) with the
    log-cluster bootstrap interval; with ref, the reference 1 - (1 - delta)^n_tracks on the same estimand, the paired
    difference V2 - reference and the mean number of tracks per decision."""
    N, X, R, T = v2_tables(rows, kix, n_keys, cells4, obs, nf, xf, ref)
    one = np.ones((1, n_keys))
    if N.sum() == 0:
        return {"E": None, "ci95": None, "decisions_with_records": 0, "decisions_any_exceed": 0, "decision_level_rate": None}, np.full(n_keys, np.nan)
    est = float(A.rates(N, X, one)[0][0])
    boot = A.rates(N, X, W)[:, 0]
    per_key = np.where(N[:, 0] > 0, X[:, 0] / np.maximum(N[:, 0], 1), np.nan)
    out = {"E": est, "ci95": [float(np.nanquantile(boot, 0.025)), float(np.nanquantile(boot, 0.975))],
           "decisions_with_records": int(N.sum()), "decisions_any_exceed": int(X.sum()), "decision_level_rate": float(X.sum() / N.sum())}
    if ref:
        Rr = R[:, None]
        eref = float(A.rates(N, Rr, one)[0][0])
        bref = A.rates(N, Rr, W)[:, 0]
        bd = boot - bref
        out.update({"reference_E": eref, "reference_ci95": [float(np.nanquantile(bref, 0.025)), float(np.nanquantile(bref, 0.975))],
                    "reference_decision_level": float(R.sum() / N.sum()), "E_minus_reference": est - eref,
                    "E_minus_reference_ci95": [float(np.nanquantile(bd, 0.025)), float(np.nanquantile(bd, 0.975))],
                    "mean_tracks_per_decision": float(T.sum() / N.sum()),
                    "reference_note": "per decision 1 - (1 - delta)^n_tracks, delta = %.2f: the joint coverage a per-constraint "
                                      "calibration implies over n_tracks independent tracks; V2 is read against it, never against delta" % DELTA})
    return out, per_key


def v2_all(rows, kix, n_keys, W, cells4, obs):
    """Every V2 variant (V2_VARIANTS) for one population; returns ({variant: summary}, {variant: per-key rate})."""
    res, pk = {}, {}
    for var, (nf, xf, near_only, ref) in V2_VARIANTS.items():
        c4 = tuple(c for c in cells4 if c in NEAR_CELLS) if near_only else tuple(cells4)
        if not c4:
            res[var], pk[var] = {"E": None, "note": "no near cell in this population"}, np.full(n_keys, np.nan)
            continue
        res[var], pk[var] = v2_summary(rows, kix, n_keys, W, c4, obs, nf, xf, ref)
        res[var]["cells4"] = list(c4)
        res[var]["fields"] = [nf, xf]
    return res, pk


def pooled_from_decisions(rows, kix, n_keys, W, cells4, obs, nf="n", xf="x"):
    """The pooled scene-level V1 from the per-decision counts (equal to the K7 pooled cell for nf, xf = n, x: consistency
    check); with nd, xd it is the de-duplicated sensitivity (A14)."""
    st = rows["stats"].reshape(len(kix), 4, NF).astype(float)
    sel_ob = np.isin(rows["ob"], list(obs)).astype(float)
    n = st[:, list(cells4), SI[nf]].sum(1) * sel_ob
    x = st[:, list(cells4), SI[xf]].sum(1) * sel_ob
    N = np.bincount(kix, weights=n, minlength=n_keys)[:, None]
    X = np.bincount(kix, weights=x, minlength=n_keys)[:, None]
    if N.sum() == 0:
        return {"E": None, "records": 0, "exceed": 0}
    one = np.ones((1, n_keys))
    b = A.rates(N, X, W)[:, 0]
    return {"E": float(A.rates(N, X, one)[0][0]), "ci95": [float(np.nanquantile(b, 0.025)), float(np.nanquantile(b, 0.975))],
            "records": int(N.sum()), "exceed": int(X.sum())}


def cal_summary(v, n_scenes=None):
    """Secondary A6 (relied pairs, record-weighted) from summed CAL_FIELDS rows v (N_CAL,): ANEES with its NOMINAL chi-square
    interval (it assumes independent records: R15 m11), p_v (below / above), ellipse coverage, per-axis exceedance curve,
    mean NLL, mean energy score, mean margins."""
    n, nn = v[CI["n"]], v[CI["nees_n"]]
    out = {"records": int(n)}
    if n > 0:
        out["mean_margin_long"], out["mean_margin_lat"] = float(v[CI["mg_long_sum"]] / n), float(v[CI["mg_lat_sum"]] / n)
    if nn > 0:
        anees = float(v[CI["nees_sum"]] / nn)
        lo, hi = chi2.ppf(0.025, 2 * nn) / nn, chi2.ppf(0.975, 2 * nn) / nn
        out.update({"anees": anees, "anees_chi2_interval_nominal": [float(lo), float(hi)], "anees_in_nominal_interval": bool(lo <= anees <= hi),
                    "p_v": float(v[CI["nees_out"]] / nn), "p_v_above": float(v[CI["nees_hi"]] / nn),
                    "p_v_below": float((v[CI["nees_out"]] - v[CI["nees_hi"]]) / nn),
                    "ellipse_coverage": {("%.2f" % q): float(v[CI["cov%d" % int(round(q * 100))]] / nn) for q in S.COV_LEVELS},
                    "exceedance_curve": {("%g" % d): float(v[CI["x_d%g" % d]] / nn) for d in S.DELTA_CURVE},
                    "nll_mean": float(v[CI["nll_sum"]] / nn), "energy_score_mean": float(v[CI["es_sum"]] / nn), "nees_records": int(nn)})
    else:
        out.update({"anees": None, "p_v": None, "note": "no covariance (mean only)" if n > 0 else "no records"})
    return out


def fallback_shares_fits(fits):
    """v01's A13 (kept as a secondary reference): the share of M*'s (fold, step <= 2 s) threshold ENTRIES from a coarser level."""
    if fits is None:
        return None
    src = []
    for f in fits["fits"].values():
        for st in STEPS:
            if "Mstar_ip_src" in f[st]:
                src.append(np.asarray(f[st]["Mstar_ip_src"], int))
    if not src:
        return None
    src = np.stack(src)
    fb = (src > 0).mean(0)
    cells = A.cell_family()
    by_cell = {}
    for name, ids in cells:
        for pop, inps in (("PD7_primary", (0, 1)), ("SD1_7_gap_le_5m", (0, 1)), ("PD_inpath", (1,)), ("NIP_not_in_path", (0,))):
            idx = [l0 + S.N_L0 * ip for l0 in ids for ip in inps]
            by_cell.setdefault(pop, {})[name] = float(fb[idx].mean())
    return {"by_l0_inpath": fb.tolist(), "by_cell": by_cell, "entries": int(src.shape[0]),
            "note": "v01 form, secondary: share of M*'s (fold, step <= 2 s) threshold entries taken from a coarser level, not record-weighted"}


def src_table(fits):
    """(n_folds, 4 steps, 192) Mstar_ip_src of the fits."""
    nf = len(fits["fits"])
    src = np.zeros((nf, len(STEPS), 2 * S.N_L0), int)
    for f in range(nf):
        for hi, st in enumerate(STEPS):
            src[f, hi] = np.asarray(fits["fits"][str(f)][st]["Mstar_ip_src"], int)
    return src


_POPMASK = {}


def pop_mask(spec_name, spec):
    if spec_name not in _POPMASK:
        _POPMASK[spec_name] = A.mask(**spec)
    return _POPMASK[spec_name]


def decode_cells(cell):
    """Vectorised k8_sim_v02.decode_cell: (ob, inp, enf, sat, gb, rel, h, l0)."""
    cell = np.asarray(cell, np.int64)
    rest, l0 = np.divmod(cell, S.N_L0)
    rest, h = np.divmod(rest, S.N_STEP)
    rest, rel = np.divmod(rest, 2)
    rest, gb = np.divmod(rest, 3)
    rest, sat = np.divmod(rest, 2)
    rest, enf = np.divmod(rest, 2)
    ob, inp = np.divmod(rest, 2)
    return ob, inp, enf, sat, gb, rel, h, l0


def a13_record_weighted(counts, eps, fits, arm="Mstar"):
    """A13 (R15 m4): the share of the arm's records in each (population, cell) whose M* threshold came from a coarser level,
    from each record's own fold (its scene's), step, L0 stratum and in-path flag (Mstar_ip_src > 0); a cell with share >= 0.5
    is labelled 'coarser bound only' (PM1)."""
    if fits is None:
        return None
    ep_scene = {o["episode"]: o["scene"] for o in eps if o["arm"] == arm}
    if not ep_scene:
        return None
    src = src_table(fits)
    sel = np.isin(counts["episode"], list(ep_scene))
    ep, cell, n = counts["episode"][sel], counts["cell"][sel], counts["n"][sel].astype(float)
    ob, inp, enf, sat, gb, rel, h, l0 = decode_cells(cell)
    fold = np.array([fits["fold_of_scene"][ep_scene[int(e)]] for e in ep], int)
    fb = np.zeros(len(ep), bool)
    m = h < len(STEPS)
    fb[m] = src[fold[m], h[m], l0[m] + S.N_L0 * inp[m]] > 0
    cells = A.cell_family()
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    cj = l0_to_cell[l0]
    out = {"arm": arm, "by_population": {}, "threshold": 0.5,
           "note": "record-weighted from each record's fold, step, L0 and in-path flag; share >= 0.5 -> 'coarser bound only' (PM1)"}
    for p in REPORT_POPS:
        pm = pop_mask(p, POP_DECIDE[p])[cell]
        r = {"by_cell": {}}
        nn = float(n[pm].sum())
        r["pooled"] = {"records": int(nn), "fallback_records": int((n * fb)[pm].sum()), "share": float((n * fb)[pm].sum() / nn) if nn > 0 else None}
        for j, (name, _) in enumerate(cells):
            mm = pm & (cj == j)
            nj = float(n[mm].sum())
            if nj > 0:
                sh = float((n * fb)[mm].sum() / nj)
                r["by_cell"][name] = {"records": int(nj), "fallback_records": int((n * fb)[mm].sum()), "share": sh,
                                      "coarser_bound_only": bool(sh >= 0.5)}
        out["by_population"][p] = r
    return out


# ---------------------------------------------------------------- A2-A3: the one curve and the cross-fitted retuned arm

def pooled_rate(N, X, mask):
    """K6's pooled-cell estimand over the keys in mask: the mean over the keys with records of X / N (None without records)."""
    m = np.asarray(mask, bool) & (np.asarray(N) > 0)
    return float(np.mean(np.asarray(X)[m] / np.asarray(N)[m])) if m.any() else None


def crossfit_select(curve, fold_of_key, crit_pops=CONF_POPS, delta=DELTA, folds=None):
    """D14 v04 A3 (R15 M3). curve: list of (alpha, arm, {population: (N, X)}) with per-key pooled record and exceedance totals,
    in increasing alpha (least conservative first). For each fold f (folds, default those present in fold_of_key) the training
    keys are those of the other folds; a point qualifies when the pooled scene-level exceedance of every criterion population
    is <= delta on the training keys (a population without training records does not qualify). The selection is the first
    qualifying point (the least conservative). boundary: 'lower' (the first grid point), 'upper' (the last grid point
    qualifies and is the first that does), 'none_qualifies' (the last, most conservative point is used), else 'interior'."""
    curve = sorted(curve, key=lambda c: (c[0], c[1]))
    fold_of_key = np.asarray(fold_of_key)
    folds = sorted(set(fold_of_key.tolist())) if folds is None else folds
    out = {}
    for f in folds:
        train = fold_of_key != f
        grid = []
        for alpha, arm, tab in curve:
            E = {p: pooled_rate(tab[p][0], tab[p][1], train) for p in crit_pops}
            grid.append({"alpha": alpha, "arm": arm, "E_train": E, "qualifies": bool(all(E[p] is not None and E[p] <= delta for p in crit_pops))})
        qual = [i for i, g in enumerate(grid) if g["qualifies"]]
        if qual:
            i = qual[0]
            boundary = "lower" if i == 0 else ("upper" if i == len(grid) - 1 else "interior")
        else:
            i, boundary = len(grid) - 1, "none_qualifies"
        out[f] = {"alpha": grid[i]["alpha"], "arm": grid[i]["arm"], "index": i, "boundary": boundary, "boundary_flag": boundary != "interior",
                  "all_larger_qualify": bool(qual) and all(g["qualifies"] for g in grid[i:]), "train_keys": int(train.sum()),
                  "apply_keys": int((~train).sum()), "grid": grid}
    return out


def curve_tables(rows_by_arm, arms, n_keys, crit_pops=CONF_POPS):
    """Per sweep arm: per-key pooled (N, X) for the criterion populations, from the per-decision counts (offset bin 0)."""
    tabs = {}
    for a in arms:
        rows, kix = rows_by_arm[a]
        st = rows["stats"].reshape(len(kix), 4, NF).astype(float)
        ob0 = (rows["ob"] == 0).astype(float)
        tabs[a] = {}
        for p in crit_pops:
            c4 = list(CELLS4[p])
            tabs[a][p] = (np.bincount(kix, weights=st[:, c4, SI["n"]].sum(1) * ob0, minlength=n_keys),
                          np.bincount(kix, weights=st[:, c4, SI["x"]].sum(1) * ob0, minlength=n_keys))
    return tabs


def add_composite_arm(eps, counts, D, C, arm_of_scene, name=RETUNED):
    """Appends a composite arm: for every scene in arm_of_scene a copy of that arm's episodes (all delays), with its counts,
    per-decision rows and calibration rows copied under new episode ids."""
    base = max(o["episode"] for o in eps) + 1
    src_ids, new = [], []
    for o in eps:
        if arm_of_scene.get(o["scene"]) == o["arm"]:
            n = dict(o)
            n["arm"], n["episode"], n["composite_of"] = name, base + len(new), o["arm"]
            src_ids.append(o["episode"])
            new.append(n)
    remap = np.full(base + 1, -1, np.int64)
    remap[np.array(src_ids, np.int64)] = [n["episode"] for n in new]

    def ext(T):
        e = np.asarray(T["episode"], np.int64)
        m = np.isin(e, src_ids)
        out = dict(T)
        for k in _row_arrays(T):
            v = T[k]
            add = remap[e[m]].astype(v.dtype) if k == "episode" else v[m]
            out[k] = np.concatenate([v, add])
        return out
    return eps + new, ext(counts), ext(D), ext(C)


# ---------------------------------------------------------------- A4, A5, A10 endpoints

def arm_endpoints(rows, kix, n_keys, W, mode="decide"):
    """A4, A5, A10 per arm: scene-level means with intervals, and the per-key vectors for the paired contrasts."""
    inf = scene_mean(rows["infeasible"], kix, n_keys)
    pr = scene_ratio(rows["ds_plan"], rows["ds_log"], kix, n_keys)
    vc, vl = rows["v_chosen"], rows["v_log"]
    div = scene_mean((np.abs(vc - vl) > S.DIVERGENCE_MPS).astype(float), kix, n_keys)
    lam = rows["lam"]
    estop = scene_mean((lam == S.LAM_ESTOP).astype(float), kix, n_keys)
    lam0 = np.where(lam == S.LAM_ESTOP, 0.0, lam)
    mbl = scene_mean(lam0, kix, n_keys)
    ind = lambda v, f: np.where(np.isfinite(v), f(v).astype(float), np.nan)  # noqa: E731
    mg_, mgi, mgn = rows["min_gap"], rows["min_gap_ip"], rows["min_gap_nip"]
    tv, tvi, tp, te = rows["ttv"], rows["ttv_ip"], rows["ttc_proxy_v01"], rows["ttv_enf"]
    vecs = {"infeasible_rate": inf, "progress_ratio": pr, "mean_chosen_speed": scene_mean(vc, kix, n_keys),
            "mean_logged_speed": scene_mean(vl, kix, n_keys), "divergence_share": div, "estop_share": estop, "mean_backoff_level": mbl,
            "min_gap_mean": scene_mean(mg_, kix, n_keys), "min_gap_share_lt_1m": scene_mean(ind(mg_, lambda v: v < 1.0), kix, n_keys),
            "min_gap_ip_mean": scene_mean(mgi, kix, n_keys), "min_gap_ip_share_lt_1m": scene_mean(ind(mgi, lambda v: v < 1.0), kix, n_keys),
            "min_gap_nip_mean": scene_mean(mgn, kix, n_keys),
            "ttv_mean": scene_mean(tv, kix, n_keys), "ttv_share_lt_2s": scene_mean(ind(tv, lambda v: v < 2.0), kix, n_keys),
            "ttv_share_lt_2s_all_decisions": scene_mean(np.where(np.isfinite(tv), tv < 2.0, False).astype(float), kix, n_keys),
            "ttv_share_lt_4s": scene_mean(ind(tv, lambda v: v < S.TTV_CLIP), kix, n_keys),
            "ttv_ip_share_lt_2s": scene_mean(ind(tvi, lambda v: v < 2.0), kix, n_keys),
            "ttv_enf_mean": scene_mean(te, kix, n_keys), "ttv_enf_share_lt_2s": scene_mean(ind(te, lambda v: v < 2.0), kix, n_keys),
            "ttv_enf_share_lt_4s": scene_mean(ind(te, lambda v: v < S.TTV_CLIP), kix, n_keys),
            "ttc_proxy_v01_mean": scene_mean(tp, kix, n_keys), "ttc_proxy_v01_share_lt_2s": scene_mean(ind(tp, lambda v: v < 2.0), kix, n_keys)}
    res = {k: wmean_ci(v, W) for k, v in vecs.items()}
    nd = max(len(lam), 1)
    res["backoff_distribution"] = {("estop" if l_ == S.LAM_ESTOP else "%g" % l_): float((lam == l_).sum() / nd) for l_ in (1.0,) + S.BACKOFF + (S.LAM_ESTOP,)}
    res["decisions"] = int(len(lam))
    q10 = lambda v: float(np.nanquantile(v, 0.10)) if np.isfinite(v).any() else None  # noqa: E731
    res["min_gap_p10_decisions"], res["min_gap_ip_p10_decisions"] = q10(mg_), q10(mgi)
    res["ttv_p10_decisions"], res["ttc_proxy_v01_p10_decisions"] = q10(tv), q10(tp)
    res["decisions_with_enforced_pairs"] = int(np.isfinite(mg_).sum())
    res["decisions_with_enforced_inpath_pairs"] = int(np.isfinite(mgi).sum())
    res["notes"] = {"ttv": "time to first violation (pair gap < 0) of the buffered footprint along the chosen plan over the enforced tracks, "
                           "16 check times to 4 s, clipped at 4 s; shares over the decisions with an enforced track (D14 v04 A5)",
                    "ttv_enf": "the same over the enforced pairs only within 2 s (the exempt C8 pairs skipped there) and every check time "
                               "after 2 s: the part a speed choice could act on; ttv - ttv_enf isolates the exempt conflicts",
                    "ttc_proxy_v01": "v01's TTC proxy, secondary (R15 M1: not a time to collision)",
                    "divergence_share": ("decision mode: a hard-braking indicator (R15 m10); replay divergence is read from loop mode"
                                         if mode == "decide" else "loop mode: replay divergence |chosen - logged speed| > 2 m/s")}
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
    """A8: the calibration items per population and cell (ref_relied items: one per pair; development scenes excluded)."""
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


# ---------------------------------------------------------------- A6 primary: the arm-independent PD7 items

def load_items_k8(path, exclude):
    """The PD7 items of k8_items_v02 (one record per enforced pair with a ground-truth annotation whose relied-on axis at the
    reference pose separates: K7's ref_relied items), development scenes excluded, as per-record arrays."""
    z = np.load(path)
    names = np.array([str(x) for x in z["scene_names"]])
    assert "rec_yaw" in z.files, "items without yaw: use k8_items_v02 (R15 M4)"
    r = {k[4:]: z[k] for k in z.files if k.startswith("rec_")}
    g_rel = np.where(r["rel"] == 0, r["gap_long"], r["gap_lat"])
    keep = (g_rel > 0) & np.array([n not in exclude for n in names])[r["s"]]
    out = {k: v[keep] for k, v in r.items()}
    out["scene"] = names[out["s"]]
    out["gap_rel"] = g_rel[keep]
    out["D"] = np.where(out["rel"] == 0, out["D_long"], out["D_lat"])
    out["l0_rel"] = np.where(out["rel"] == 0, out["l0_long"], out["l0_lat"])
    out["n_ref_relied_items"] = int((z["item_ref_relied"] & np.array([n not in exclude for n in names])[z["item_s"]]).sum())
    out["file"] = os.path.abspath(path)
    out["file_sha256"] = sha(path)
    return out


def item_margins(arm, it, fits, alpha_of_fold=None):
    """(n, 2) margins along the object's long and lateral axes of every item under the arm's rule (the planner's margins at the
    item's step, with its fold's fit; k8_sim_v02.margins); B9 gives the radius on both axes."""
    sd2 = np.stack([it["sd_long"], it["sd_lat"]], -1)
    n = len(sd2)
    if arm == "B0":
        return S.Z * sd2
    if arm in S.ALPHA_OF_ARM:
        return math.sqrt(S.ALPHA_OF_ARM[arm]) * S.Z * sd2
    if "fold" not in it:
        it["fold"] = np.array([fits["fold_of_scene"][s] for s in it["scene"]], int)
    fold = it["fold"]
    h = it["h"]
    if arm == RETUNED:
        al = np.array([alpha_of_fold[int(f)] for f in range(int(fold.max()) + 1)])[fold]
        return np.sqrt(al)[:, None] * S.Z * sd2
    out = np.empty((n, 2))
    for f in np.unique(fold):
        for hh in np.unique(h):
            m = (fold == f) & (h == hh)
            if not m.any():
                continue
            F = fits["fits"][str(int(f))][STEPS[int(hh)]]
            if arm == "B1":
                k = np.asarray(F["B1"])[it["g"][m] * 3 + it["r"][m]]
                out[m] = S.Z * np.sqrt(k)[:, None] * sd2[m]
            elif arm in ("B3", "B4"):
                out[m] = F[arm] * sd2[m]
            elif arm == "B9":
                out[m] = F["B9"]
            elif arm in ("B6", "Mstar"):
                thr = np.asarray(F[arm + "_ip"])
                ip = it["inpath"][m].astype(int)
                out[m, 0] = thr[it["l0_long"][m] + S.N_L0 * ip] * sd2[m, 0]
                out[m, 1] = thr[it["l0_lat"][m] + S.N_L0 * ip] * sd2[m, 1]
            else:
                raise ValueError(arm)
    return out


def item_diagnostics(arm, it, fits, alpha_of_fold=None, chunk=40000):
    """Per item under the arm's covariance (k8_sim_v02._cal_pairs, chunked): NEES, the standardised error along the relied-on
    axis u, the Gaussian NLL and the energy score; and the margins (sharpness)."""
    mg2 = item_margins(arm, it, fits, alpha_of_fold)
    yaw = it["yaw"]
    axj = np.stack([np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1)], 1)
    pcov = np.stack([it["sxx"], it["sxy"], it["syy"]], -1)
    sd2 = np.stack([it["sd_long"], it["sd_lat"]], -1)
    e = np.stack([it["dx"], it["dy"]], -1)
    n = len(yaw)
    out = {k: np.empty(n) for k in ("nees", "u", "nll", "es")}
    for i0 in range(0, n, chunk):
        sl = slice(i0, min(n, i0 + chunk))
        cd = S._cal_pairs("B9" if arm == "B9" else arm, e[sl], axj[sl], pcov[sl], mg2[sl], sd2[sl], it["rel"][sl], it["D"][sl])
        for k in out:
            out[k][sl] = cd[k]
    out["mg2"] = mg2
    return out


def a6_summary(d, mask, key, n_keys, W):
    """A6 summaries of one arm on one population (M5): the scene-level bootstrap ANEES first, the record-weighted ANEES with its
    log-cluster bootstrap interval and its nominal chi-square interval, median NEES, 1 %-trimmed ANEES (the top floor(n/100),
    at least 1, NEES dropped), the share of the NEES sum in the top 1 %, max NEES, p_v (below / above), ellipse coverage, the
    per-axis exceedance curve along the relied-on axis, NLL, energy score, sharpness, and the count above GROSS_NEES."""
    m = np.asarray(mask, bool)
    n = int(m.sum())
    out = {"records": n}
    if n == 0:
        return out
    ne, u, nll, es, mg2 = d["nees"][m], d["u"][m], d["nll"][m], d["es"][m], d["mg2"][m]
    k = key[m]
    s_n = np.bincount(k, minlength=n_keys).astype(float)
    s_ne = np.bincount(k, weights=ne, minlength=n_keys)
    per_key = np.where(s_n > 0, s_ne / np.maximum(s_n, 1), np.nan)
    srt = np.sort(ne)[::-1]
    top = max(1, n // 100)
    lo, hi = chi2.ppf(0.025, 2 * n) / n, chi2.ppf(0.975, 2 * n) / n
    out.update({"scenes": int((s_n > 0).sum()),
                "anees_scene_level": wmean_ci(per_key, W),
                "anees_record_weighted": ratio_ci(s_ne, s_n, W),
                "anees": float(ne.mean()), "anees_chi2_interval_nominal": [float(lo), float(hi)],
                "anees_chi2_note": "nominal: assumes independent records (R15 m11); the scene-level bootstrap leads",
                "median_nees": float(np.median(ne)), "median_nees_reference_chi2_2": float(chi2.ppf(0.5, 2)),
                "anees_trimmed_1pct": float(srt[top:].mean()) if n > top else None,
                "share_nees_sum_top_1pct": float(srt[:top].sum() / max(ne.sum(), 1e-300)), "max_nees": float(srt[0]),
                "p_v": float(np.mean((ne < S.CHI2_2[0]) | (ne > S.CHI2_2[1]))), "p_v_below": float(np.mean(ne < S.CHI2_2[0])),
                "p_v_above": float(np.mean(ne > S.CHI2_2[1])),
                "ellipse_coverage": {("%.2f" % q): float(np.mean(ne <= c)) for q, c in zip(S.COV_LEVELS, S.CHI2_2_COV)},
                "exceedance_curve": {("%g" % dl): float(np.mean(u > S.Z_OF_DELTA[dl])) for dl in S.DELTA_CURVE},
                "nll_mean": float(nll.mean()), "energy_score_mean": float(es.mean()),
                "energy_score_scene_level": wmean_ci(np.where(s_n > 0, np.bincount(k, weights=es, minlength=n_keys) / np.maximum(s_n, 1), np.nan), W),
                "mean_margin_long": float(mg2[:, 0].mean()), "mean_margin_lat": float(mg2[:, 1].mean()),
                "records_above_gross_nees": int((ne > GROSS_NEES).sum())})
    return out


def flat_a6(c):
    out = {"records": c.get("records"), "scenes": c.get("scenes"),
           "anees_scene_level": (c.get("anees_scene_level") or {}).get("mean"),
           "anees_scene_level_ci95_lo": ((c.get("anees_scene_level") or {}).get("ci95") or [None, None])[0],
           "anees_scene_level_ci95_hi": ((c.get("anees_scene_level") or {}).get("ci95") or [None, None])[1],
           "anees_record_weighted": (c.get("anees_record_weighted") or {}).get("value"),
           "anees_chi2_nominal_lo": (c.get("anees_chi2_interval_nominal") or [None, None])[0],
           "anees_chi2_nominal_hi": (c.get("anees_chi2_interval_nominal") or [None, None])[1],
           "median_nees": c.get("median_nees"), "anees_trimmed_1pct": c.get("anees_trimmed_1pct"),
           "share_nees_sum_top_1pct": c.get("share_nees_sum_top_1pct"), "max_nees": c.get("max_nees"),
           "p_v": c.get("p_v"), "p_v_below": c.get("p_v_below"), "p_v_above": c.get("p_v_above")}
    for q in S.COV_LEVELS:
        out["cov%d" % int(round(q * 100))] = (c.get("ellipse_coverage") or {}).get("%.2f" % q)
    for dl in S.DELTA_CURVE:
        out["exc_d%g" % dl] = (c.get("exceedance_curve") or {}).get("%g" % dl)
    out["nll_mean"], out["energy_score_mean"] = c.get("nll_mean"), c.get("energy_score_mean")
    out["mean_margin_long"], out["mean_margin_lat"] = c.get("mean_margin_long"), c.get("mean_margin_lat")
    out["records_above_gross_nees"] = c.get("records_above_gross_nees")
    return out


def a6_items(it, fits, arms, kidx_scene, n_keys, W, alpha_of_fold=None):
    """A6 primary (D14 v04 A6; R15 M4, M5, m7, m14): calibration diagnostics per arm on the arm-independent PD7 items, per
    population, per stratum (K6 cell of the relied-on axis), with the de-duplicated sensitivity and the gross-error list."""
    assert all(s in kidx_scene for s in np.unique(it["scene"])), "items from scenes outside the analysis"
    key = np.array([kidx_scene[s] for s in it["scene"]], int)
    pops = {"PD7_primary": np.ones(len(key), bool), "SD1_7_gap_le_5m": it["gap_rel"] <= S.GAP_BINS[1], "PD_inpath": it["inpath"].astype(bool),
            "NIP_not_in_path": ~it["inpath"].astype(bool)}
    cells = A.cell_family()
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    cj = l0_to_cell[it["l0_rel"]]
    # A14: one record per (scene, decision, step, ground-truth instance), the first in record order kept
    seen, dd = set(), np.zeros(len(key), bool)
    for i, t_ in enumerate(zip(it["scene"].tolist(), it["k"].tolist(), it["h"].tolist(), it["inst"].tolist())):
        if t_ not in seen:
            seen.add(t_)
            dd[i] = True
    # A13 on the items: M*'s fallback per record (fold, step, L0 of the relied-on axis, in-path)
    fbr = None
    if fits is not None:
        src = src_table(fits)
        fold = np.array([fits["fold_of_scene"][s] for s in it["scene"]], int)
        fbr = src[fold, it["h"], it["l0_rel"] + S.N_L0 * it["inpath"].astype(int)] > 0
    res = {"file": it["file"], "file_sha256": it["file_sha256"], "records_PD7": int(len(key)), "ref_relied_items": it["n_ref_relied_items"],
           "records_equal_ref_relied_items": bool(len(key) == it["n_ref_relied_items"]), "duplicates_removed_PD7": int((~dd).sum()),
           "covariance_by_arm": COV_DOC, "gross_nees_threshold": GROSS_NEES,
           "gross_note": "gross errors: NEES under B0's raw covariance above the chi-square(2) 1 - 1e-6 quantile (suspected association errors)",
           "by_population": {p: {} for p in pops}, "dedup_PD7": {}, "fallback_record_weighted_Mstar": {}}
    rows_cells, keep_d = [], {}
    for arm in arms:
        if arm == RETUNED and alpha_of_fold is None:
            continue
        if arm not in A6_ARMS:
            continue
        d = item_diagnostics(arm, it, fits, alpha_of_fold)
        if arm in ("B0", "Mstar", "B4"):
            keep_d[arm] = d["nees"]
        for p, pm in pops.items():
            res["by_population"][p][arm] = a6_summary(d, pm, key, n_keys, W)
            for j, (name, _) in enumerate(cells):
                mm = pm & (cj == j)
                if not mm.any():
                    continue
                c = a6_summary(d, mm, key, n_keys, W)
                row = {"population": p, "arm": arm, "cell": name}
                row.update(flat_a6(c))
                if fbr is not None:
                    sh = float(fbr[mm].mean())
                    row["fallback_share_Mstar_record_weighted"], row["coarser_bound_only"] = sh, bool(sh >= 0.5)
                rows_cells.append(row)
        res["dedup_PD7"][arm] = a6_summary(d, dd, key, n_keys, W)
    if fbr is not None:
        for p, pm in pops.items():
            res["fallback_record_weighted_Mstar"][p] = {"share": float(fbr[pm].mean()) if pm.any() else None, "records": int(pm.sum())}
    # gross-error list (arm-independent definition: B0's NEES), with the NEES under M* and B4
    gross = []
    if "B0" in keep_d:
        idx = np.flatnonzero(keep_d["B0"] > GROSS_NEES)
        idx = idx[np.argsort(-keep_d["B0"][idx])]
        for i in idx.tolist():
            gross.append({"scene": str(it["scene"][i]), "k": int(it["k"][i]), "h": int(it["h"][i]), "inst": int(it["inst"][i]),
                          "group": int(it["g"][i]), "inpath": bool(it["inpath"][i]), "error_m": float(math.hypot(it["dx"][i], it["dy"][i])),
                          "gap_rel_m": float(it["gap_rel"][i]), "nees_B0": float(keep_d["B0"][i]),
                          "nees_Mstar": float(keep_d["Mstar"][i]) if "Mstar" in keep_d else None,
                          "nees_B4": float(keep_d["B4"][i]) if "B4" in keep_d else None, "duplicate": bool(not dd[i])})
    res["gross_errors"] = {"count": len(gross), "share": len(gross) / max(len(key), 1), "top": gross[:100]}
    res["_csv_cells"], res["_csv_gross"] = rows_cells, gross
    return res


# ---------------------------------------------------------------- D14 section 6 forms

def d14_forms(rate, Ws, valid, arms, form_b_comps=FORM_B_COMPARATORS):
    """D14 v04 section 6, reported. rate: {arm: per-scene infeasible rate}; Ws: (B, scenes) log weights; valid: {arm: bool} from
    form_valid (identical for M* and every comparator, R15 m3).
      A (K6's form; R15 M2): M* valid and strictly less infeasible than each of B0, B1, B4, B9 at 1 - 0.05/4 (one-sided log
        bootstrap upper bound of the paired difference below 0); the all-arm contrast is descriptive only.
      B (literature form): M* valid and less infeasible than every comparator in form_b_comps that is also valid, at
        1 - 0.05/|valid comparators|; every invalid comparator goes to the trade-off table.
      C: B plus M*'s infeasible rate <= B4's + 0.03 (point and one-sided 0.95 bound)."""
    def ub(b, level):
        d = rate["Mstar"] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        return float(d.mean()), float(np.quantile(bm, level))
    fa = [b for b in FORM_A_ARMS if b in arms]
    lower_a = {}
    for b in fa:
        md, u = ub(b, LEVEL_FORM_A)
        lower_a[b] = {"mean_diff": md, "ub_one_sided": u, "lower": bool(u < 0)}
    A_ = {"comparators": fa, "level": LEVEL_FORM_A, "validity_M": bool(valid.get("Mstar", False)), "lower_than": lower_a,
          "complete_comparator_set": len(fa) == len(FORM_A_ARMS)}
    A_["met"] = bool(A_["validity_M"] and A_["complete_comparator_set"] and all(v["lower"] for v in lower_a.values()))
    others = [b for b in arms if b != "Mstar"]
    level_all = 1 - 0.05 / max(len(others), 1)
    all_arm = {}
    for b in others:
        md, u = ub(b, level_all)
        all_arm[b] = {"mean_diff": md, "ub_one_sided": u, "lower": bool(u < 0)}
    comps = [b for b in form_b_comps if b in arms]
    passing = [b for b in comps if valid.get(b, False)]
    level_b = 1 - 0.05 / max(len(passing), 1)
    lower_b = {}
    for b in passing:
        md, u = ub(b, level_b)
        lower_b[b] = {"mean_diff": md, "ub_one_sided": u, "lower": bool(u < 0)}
    B_ = {"comparators": comps, "comparators_passing_validity": passing, "comparators_failing_validity": [b for b in comps if b not in passing],
          "level": level_b, "validity_M": bool(valid.get("Mstar", False)), "lower_than_every_passing_comparator": lower_b,
          "vacuous": not passing, "validity_rule": "HK1 and HK1c on PD7, SD1_7 and PD, identical for M* and every comparator (R15 m3)"}
    B_["met"] = bool(B_["validity_M"] and all(v["lower"] for v in lower_b.values()))
    C_ = {}
    if "B4" in arms:
        md, u95 = ub("B4", 0.95)
        C_ = {"Mstar_minus_B4_infeasible": md, "ub_one_sided_0.95": u95, "bound": 0.03, "point_within_bound": bool(md <= 0.03),
              "ub_within_bound": bool(u95 <= 0.03), "met_point": bool(B_["met"] and md <= 0.03)}
    return {"A_K6_form": A_, "B_literature_form": B_, "C_B_plus_price_bound": C_,
            "all_arm_contrast_descriptive": {"level": level_all, "by_arm": all_arm, "note": "descriptive only: Z0 and the sweep arms are never comparators"}}


# ---------------------------------------------------------------- decision mode

def analyse_decide(eps, counts, D, C, log_of_scene, B, rng, power_key, fits=None, items=None, items_k8=None):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES and o["arm"] != "LOG"]
    cells = A.cell_family()
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    n_keys = len(keys)
    kidx = {k: i for i, k in enumerate(keys)}
    one = np.ones((1, n_keys))
    res = {"stamp": STAMP, "scenes": len(keys), "logs": len(logs)}
    # ---- A3: the cross-fitted retuned arm on the one curve (before everything else, so that it is analysed as an arm)
    sweep_present = [a for a in S.SWEEP_ARMS if any(o["arm"] == a for o in eps)]
    retune = None
    if fits is not None and sweep_present:
        rows0 = dec_rows(D, eps, kidx)
        ctab = curve_tables(rows0, sweep_present, n_keys)
        fold_of_key = np.array([fits["fold_of_scene"][k[0]] for k in keys], int)
        all_folds = sorted(int(f) for f in fits["fits"])
        curve = [(S.CURVE_ALPHA_OF_ARM[a], a, ctab[a]) for a in sweep_present]
        sel = crossfit_select(curve, fold_of_key, folds=all_folds)
        sel_a = crossfit_select([c for c in curve if c[1] in S.ALPHA_ARMS], fold_of_key, folds=all_folds)
        sel_d = crossfit_select([c for c in curve if c[1] in S.DELTA_ARMS], fold_of_key, folds=all_folds)
        insample = crossfit_select(curve, np.zeros(n_keys, int), folds=[-1])[-1]    # every key trains: the in-sample choice (reported)
        arm_of_scene = {k[0]: sel[int(fits["fold_of_scene"][k[0]])]["arm"] for k in keys}
        eps, counts, D, C = add_composite_arm(eps, counts, D, C, arm_of_scene)
        retune = {"curve": "one curve: alpha arms at alpha, delta' arms at alpha_eq = (z_{1-delta'} / z_0.95)^2 (D14 v04 A2)",
                  "criterion": "pooled PD7, SD1_7 and PD scene-level exceedance <= delta on the 4 training folds (M*'s criterion)",
                  "rule": "least conservative qualifying point (smallest alpha_eq), selected on 4 folds and applied to the 5th",
                  "by_fold": {str(f): {k: v for k, v in s_.items()} for f, s_ in sel.items()},
                  "alpha_of_fold": {str(f): s_["alpha"] for f, s_ in sel.items()},
                  "arm_of_fold": {str(f): s_["arm"] for f, s_ in sel.items()},
                  "boundary_any": bool(any(s_["boundary_flag"] for f, s_ in sel.items() if s_["apply_keys"] > 0)),
                  "folds_applied": [str(f) for f, s_ in sel.items() if s_["apply_keys"] > 0],
                  "alpha_grid_only_by_fold": {str(f): {"alpha": s_["alpha"], "arm": s_["arm"], "boundary": s_["boundary"]} for f, s_ in sel_a.items()},
                  "delta_grid_only_by_fold": {str(f): {"alpha_eq": s_["alpha"], "arm": s_["arm"], "delta_prime": S.DELTA_OF_ARM[s_["arm"]],
                                                       "boundary": s_["boundary"]} for f, s_ in sel_d.items()},
                  "in_sample_choice_reported_only": {"alpha": insample["alpha"], "arm": insample["arm"], "boundary": insample["boundary"]},
                  "arm_of_scene": arm_of_scene}
    res["retune"] = retune
    arms = [a for a in ALL_ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    res["arms"] = arms
    # ---- V1 (K7 form) on the populations, plus the one-step check at step 0 (A1)
    pops, tabs = A.populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_DECIDE)
    res["populations"] = pops
    pops_h0, tabs_h0 = A.populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W,
                                     {p: dict(POP_DECIDE[p], steps=(0,)) for p in REPORT_POPS})
    res["V1_one_step"] = {p: {a: pops_h0[p]["pooled_by_arm"][a] for a in arms} for p in REPORT_POPS}
    # ---- K7's HK1 on M* and the validity tests on every arm (Form B needs them)
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
                                  "valid_form_B": form_valid(v),
                                  "pops": {p: {k: v["pops"][p].get(k) for k in ("evaluable", "flagged", "pooled", "family_size", "family_flagged", "HK1a_met", "HK1b_met")}
                                           for p in CONF_POPS}} for a, v in vba.items()}
    # ---- HK2 on SD1_7 (K7 form, reported)
    Ns, Xs, ests, boots, evs = tabs["SD1_7_gap_le_5m"]
    m7_flag_sd = set(pops["SD1_7_gap_le_5m"]["cells_by_arm"]["Mstar"]["sig_above_cells"])
    hk2 = {}
    for b in PRACTITIONER:
        if b not in arms:
            continue
        fb_ = np.flatnonzero(evs[b])
        sig_b = []
        if len(fb_):
            _, _, _, sb, _ = A.flag(ests[b], boots[b], fb_, LEVEL_HK2)
            sig_b = [cells[j][0] for i, j in enumerate(fb_) if sb[i]]
        pr = A.paired(ests, boots, evs, cells, b, "Mstar", LEVEL_HK2)
        hk2[b] = {"flagged_bonferroni_SD1_7": sig_b, "paired": pr,
                  "fails_where_Mstar_holds": [c for c in sig_b if c not in m7_flag_sd and pr.get(c, {}).get("positive", False)]}
    if "B0" in arms:
        fb_ = np.flatnonzero(evs["B0"])
        if len(fb_):
            _, _, _, sb, _ = A.flag(ests["B0"], boots["B0"], fb_, LEVEL_HK2)
            hk2["B0_descriptive"] = {"flagged_bonferroni_SD1_7": [cells[j][0] for i, j in enumerate(fb_) if sb[i]]}
    res["HK2"] = hk2
    # ---- HK3 (K6's form) and the dominance form (K7 code, unchanged)
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
    hk3 = {}
    for b in comps:
        d = rate["Mstar"] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        ub = float(np.quantile(bm, LEVEL_HK3))
        r = {"mean_diff": float(d.mean()), "ub_one_sided_bonferroni": ub, "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
             "lower": bool(ub < 0), "tested": b in HK3_ARMS}
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
                         "note": "K7-form hypotheses, reported only (D14 v04 section 4: nothing is gated on nuScenes)"}
    # ---- per-decision endpoints (A4, A5, A10), V2 and variants (A1), A14, calibration secondary (A6, A7)
    rows_by_arm = dec_rows(D, eps, kidx)
    cal_by_arm = cal_rows(C, eps, kidx)
    fb_fits = fallback_shares_fits(fits)
    a13 = a13_record_weighted(counts, eps, fits, "Mstar")
    res["fallback_strata_fits_entries"] = fb_fits
    res["A13_fallback_record_weighted"] = a13
    a13c = lambda p, name: ((((a13 or {}).get("by_population", {}).get(p) or {}).get("by_cell") or {}).get(name) or {})  # noqa: E731
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    endpoints, vecs, cal, cal_cells, cal_l0, consistency = {}, {}, {p: {} for p in REPORT_POPS}, [], [], {}
    v2 = {p: {} for p in REPORT_POPS}
    a14 = {p: {} for p in REPORT_POPS}
    for a in arms:
        rows, kix = rows_by_arm[a]
        endpoints[a], vecs[a] = arm_endpoints(rows, kix, n_keys, W, "decide")
        for p in REPORT_POPS:
            c4, obs = V2_DECIDE[p]
            v2[p][a], pk = v2_all(rows, kix, n_keys, W, c4, obs)
            lab = POP_LAB[p]
            if p in ("PD7_primary", "SD1_7_gap_le_5m"):
                vecs[a]["V2_%s_scene_rate" % lab] = pk["V2"]
                Nc, Xc = tabs[p][0][a], tabs[p][1][a]
                vecs[a]["V1_%s_scene_rate" % lab] = np.where(Nc.sum(1) > 0, Xc.sum(1) / np.maximum(Nc.sum(1), 1), np.nan)
            if p == "PD7_primary":
                vecs[a]["V2_viol_PD7_scene_rate"] = pk["V2_viol"]
                vecs[a]["V2_binding_PD7_scene_rate"] = pk["V2_binding"]
            v1 = pooled_from_decisions(rows, kix, n_keys, W, c4, obs)
            v1d = pooled_from_decisions(rows, kix, n_keys, W, c4, obs, "nd", "xd")
            k7E = (pops[p]["pooled_by_arm"].get(a) or {}).get("E")
            a14[p][a] = {"records": v1["records"], "records_dedup": v1d["records"], "duplicates": v1["records"] - v1d["records"],
                         "V1_pooled": v1.get("E"), "V1_pooled_dedup": v1d.get("E"), "V1_pooled_dedup_ci95": v1d.get("ci95"),
                         "V2": v2[p][a]["V2"]["E"], "V2_dedup": v2[p][a]["V2_dedup"]["E"],
                         "V1_pooled_equals_K7_pooled_cell": None if (v1.get("E") is None or k7E is None) else bool(abs(v1["E"] - k7E) < 1e-9)}
        st = rows["stats"].reshape(len(kix), 4, NF)
        consistency[a] = {"PD7_records_counts": int(tabs["PD7_primary"][0][a].sum()), "PD7_records_decisions": int(st[:, :, SI["n"]].sum()),
                          "PD7_exceed_counts": int(tabs["PD7_primary"][1][a].sum()), "PD7_exceed_decisions": int(st[:, :, SI["x"]].sum()),
                          "PD7_records_h0_counts": int(tabs_h0["PD7_primary"][0][a].sum()), "PD7_records_h0_decisions": int(st[:, :, SI["n_h0"]].sum())}
        consistency[a]["equal"] = bool(consistency[a]["PD7_records_counts"] == consistency[a]["PD7_records_decisions"]
                                       and consistency[a]["PD7_exceed_counts"] == consistency[a]["PD7_exceed_decisions"]
                                       and consistency[a]["PD7_records_h0_counts"] == consistency[a]["PD7_records_h0_decisions"])
        if a in S.DELTA_ARMS or a == RETUNED:   # m14: the delta' arms' in-loop covariance is B0's (and RETUNED copies them where a
            continue                            # fold selects a delta' point); no secondary A6 rows -- their A6 is the items table
        ckey, cval, ckix = cal_by_arm.get(a, (np.zeros(0, int), np.zeros((0, S.N_CAL)), np.zeros(0, int)))
        c4_of = ckey // S.N_L0
        l0_of = ckey % S.N_L0
        for p in REPORT_POPS:
            m_ = np.isin(c4_of, list(CELLS4[p]))
            cal[p][a] = cal_summary(cval[m_].sum(0))
            if cval[m_][:, CI["nees_n"]].sum() > 0:
                pk_ = scene_ratio(cval[m_][:, CI["nees_sum"]], cval[m_][:, CI["nees_n"]], ckix[m_], n_keys)
                cal[p][a]["anees_scene_level"] = wmean_ci(pk_, W)
            cj = l0_to_cell[l0_of]
            for j, (name, _) in enumerate(cells):
                mm = m_ & (cj == j)
                if not mm.any():
                    continue
                row = {"population": p, "arm": a, "cell": name}
                row.update(flat_cal(cal_summary(cval[mm].sum(0))))
                row["scenes"] = int(len(np.unique(ckix[mm])))
                row["fallback_share_Mstar_record_weighted"] = a13c(p, name).get("share")
                row["coarser_bound_only"] = a13c(p, name).get("coarser_bound_only")
                cal_cells.append(row)
        for l0 in range(S.N_L0):
            for ip in (0, 1):
                mm = (l0_of == l0) & ((c4_of % 2) == ip)
                if not mm.any():
                    continue
                row = {"population": "PD7_primary", "arm": a, "l0": l0, "l0_name": M.l0_name(l0), "inpath": ip}
                row.update(flat_cal(cal_summary(cval[mm].sum(0))))
                row["scenes"] = int(len(np.unique(ckix[mm])))
                row["fallback_share_fits_entries"] = fb_fits["by_l0_inpath"][l0 + S.N_L0 * ip] if fb_fits else None
                cal_l0.append(row)
    res["endpoints_by_arm"] = endpoints
    res["V2"] = v2
    res["A14_duplicates"] = a14
    res["calibration_relied_pairs_secondary"] = cal
    res["calibration_note"] = "secondary A6: each arm's own relied pairs (different outcome sets per arm); the primary A6 is calibration_items"
    res["consistency_decisions_vs_counts"] = consistency
    res["_csv_cal_cells"], res["_csv_cal_l0"] = cal_cells, cal_l0
    # ---- A6 primary on the arm-independent PD7 items
    res["calibration_items"] = None
    if items_k8 is not None:
        kidx_scene = {k[0]: i for i, k in enumerate(keys)}
        aof = {int(f): v for f, v in retune["alpha_of_fold"].items()} if retune else None
        ci_ = a6_items(items_k8, fits, arms, kidx_scene, n_keys, W, aof)
        res["_csv_a6_cells"], res["_csv_a6_gross"] = ci_.pop("_csv_cells"), ci_.pop("_csv_gross")
        res["calibration_items"] = ci_
    # ---- paired contrasts at identical decision states, every arm pair
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
    # ---- A2 / A3: the one curve
    a6p = ((res["calibration_items"] or {}).get("by_population") or {}).get("PD7_primary", {})

    def sweep_row(kind, val, a):
        pp = pops["PD7_primary"]["pooled_by_arm"].get(a) or {}
        r = {"kind": kind, "value": val, "alpha_eq": S.CURVE_ALPHA_OF_ARM.get(a), "arm": a,
             "V1_PD7_E": pp.get("E"), "V1_PD7_lb": pp.get("lb_sim"), "V1_PD7_ub": pp.get("ub_sim"), "V1_PD7_flagged": pp.get("sig_above")}
        for p in ("SD1_7_gap_le_5m", "PD_inpath", "NIP_not_in_path"):
            r["V1_%s_E" % POP_LAB[p]] = (pops[p]["pooled_by_arm"].get(a) or {}).get("E")
        r["meets_Mstar_criterion_in_sample"] = bool(all(r["V1_%s_E" % lab] is not None and r["V1_%s_E" % lab] <= DELTA for lab in ("PD7", "SD1_7", "PD")))
        for var in ("V2", "V2_near", "V2_viol", "V2_binding", "V2_exec"):
            r[var + "_PD7_E"] = v2["PD7_primary"][a][var].get("E")
        r["V2_PD7_reference_E"] = v2["PD7_primary"][a]["V2"].get("reference_E")
        r["V2_PD7_one_step_E"] = v2["PD7_primary"][a]["V2_one_step"].get("E")
        r["infeasible_rate"] = res["infeasible_rate"][a]["mean"]
        r["infeasible_ci95_lo"], r["infeasible_ci95_hi"] = res["infeasible_rate"][a]["ci95"]
        for k in ("progress_ratio", "mean_chosen_speed", "estop_share", "min_gap_mean", "min_gap_ip_mean", "ttv_share_lt_2s"):
            r[k] = endpoints[a][k]["mean"]
        c = a6p.get(a) or {}
        r["A6_items_anees_scene_level"] = (c.get("anees_scene_level") or {}).get("mean")
        r["A6_items_median_nees"], r["A6_items_nll"], r["A6_items_es"] = c.get("median_nees"), c.get("nll_mean"), c.get("energy_score_mean")
        r["mean_margin_long_PD7_items"], r["mean_margin_lat_PD7_items"] = c.get("mean_margin_long"), c.get("mean_margin_lat")
        r["HK1"] = res["validity_by_arm"][a]["HK1"]
        r["valid_form_B"] = res["validity_by_arm"][a]["valid_form_B"]
        return r
    sw_rows = [sweep_row("alpha", S.ALPHA_OF_ARM[a], a) for a in S.ALPHA_ARMS if a in arms]
    sw_rows += [sweep_row("delta_prime", S.DELTA_OF_ARM[a], a) for a in S.DELTA_ARMS if a in arms]
    sw_rows.sort(key=lambda r: (r["alpha_eq"], r["arm"]))
    sweep = {"one_curve": sw_rows, "reference": [sweep_row("reference", None, a) for a in ("Z0", "B0", "B4", "Mstar", RETUNED) if a in arms],
             "reading": "one curve: alpha arms at alpha, delta' arms at alpha_eq; RETUNED = the cross-fitted least conservative point "
                        "meeting M*'s criterion (retune); in-sample points are descriptive"}
    if RETUNED in arms and "Mstar" in arms:
        sweep["RETUNED_vs_Mstar"] = {ep_: res["paired_vs_Mstar"].get(ep_, {}).get(RETUNED) for ep_ in PAIRED_ENDPOINTS}
    res["sweep"] = sweep
    # ---- D14 section 6 forms A, B, C (reported)
    valid = {a: res["validity_by_arm"][a]["valid_form_B"] for a in arms}
    forms = d14_forms(rate, Ws, valid, arms)
    forms["trade_off_table"] = [{"arm": b, "valid_form_B": valid[b], "HK1": res["validity_by_arm"][b]["HK1"],
                                 "HK1c_all_pops": res["validity_by_arm"][b]["HK1c_all_pops"],
                                 "form_B_comparator": b in FORM_B_COMPARATORS, "form_A_comparator": b in FORM_A_ARMS,
                                 "pooled_PD7_E": (pops["PD7_primary"]["pooled_by_arm"].get(b) or {}).get("E"),
                                 "pooled_SD1_7_E": (pops["SD1_7_gap_le_5m"]["pooled_by_arm"].get(b) or {}).get("E"),
                                 "pooled_PD_E": (pops["PD_inpath"]["pooled_by_arm"].get(b) or {}).get("E"),
                                 "infeasible_rate": res["infeasible_rate"][b]["mean"], "progress_ratio": endpoints[b]["progress_ratio"]["mean"],
                                 "Mstar_minus_arm_infeasible": hk3[b]["mean_diff"]}
                                for b in comps]
    forms["note"] = "D14 v04 section 6: reported for the researcher's decision; nothing is gated on nuScenes"
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
                                                             "fallback_share_record_weighted": a13c(p, cells[j][0]).get("share"),
                                                             "coarser_bound_only": a13c(p, cells[j][0]).get("coarser_bound_only")}
                                               for j in range(len(cells))}
    if fits is not None:
        cnt["folds"] = {"k_folds": len(fits["fits"]), "seed": fits.get("seed"), "fold_scene_counts": fits.get("fold_scene_counts"),
                        "scenes_in_fits": len(fits.get("scenes", [])),
                        "analysed_scenes_by_fold": {str(f): int(sum(1 for k in keys if fits["fold_of_scene"][k[0]] == f)) for f in range(len(fits["fits"]))}}
    if items is not None:
        cnt["items"] = items
    res["counts"] = cnt
    return res


def flat_cal(c):
    out = {"records": c.get("records"), "nees_records": c.get("nees_records"), "anees": c.get("anees"),
           "anees_chi2_nominal_lo": (c.get("anees_chi2_interval_nominal") or [None, None])[0],
           "anees_chi2_nominal_hi": (c.get("anees_chi2_interval_nominal") or [None, None])[1],
           "anees_in_nominal_interval": c.get("anees_in_nominal_interval"), "p_v": c.get("p_v"), "p_v_below": c.get("p_v_below"),
           "p_v_above": c.get("p_v_above")}
    for q in S.COV_LEVELS:
        out["cov%d" % int(round(q * 100))] = (c.get("ellipse_coverage") or {}).get("%.2f" % q)
    for d in S.DELTA_CURVE:
        out["exc_d%g" % d] = (c.get("exceedance_curve") or {}).get("%g" % d)
    out["nll_mean"], out["energy_score_mean"] = c.get("nll_mean"), c.get("energy_score_mean")
    out["mean_margin_long"], out["mean_margin_lat"] = c.get("mean_margin_long"), c.get("mean_margin_lat")
    return out


# ---------------------------------------------------------------- closed loop

def analyse_loop(eps, counts, D, C, log_of_scene, B, rng, arm_of_scene=None):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES]
    if arm_of_scene:
        eps, counts, D, C = add_composite_arm(eps, counts, D, C, arm_of_scene)
    arms = [a for a in ALL_ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    eps_p = [o for o in eps if o["arm"] != "LOG"]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps_p, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    n_keys = len(keys)
    kidx = {k: i for i, k in enumerate(keys)}
    res = {"stamp": STAMP, "episode_keys": len(keys), "logs": len(logs), "arms": arms,
           "retuned_note": "RETUNED in loop mode takes, per scene, the decision-mode cross-fitted selection of its fold" if arm_of_scene else None}
    res["populations"], tabs = A.populations(eps_p, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_LOOP)
    res["progress_vs_Mstar"] = A.progress_contrasts(eps, arms, log_of_scene, logs, W_logs)
    res["outcomes"] = A.outcome_summary(eps)
    rows_by_arm = dec_rows(D, eps_p, kidx)
    endpoints, vecs, v2 = {}, {}, {p: {} for p in V2_LOOP}
    delays = sorted({o["delay_kf"] for o in eps_p})
    for a in arms:
        rows, kix = rows_by_arm[a]
        endpoints[a], vecs[a] = arm_endpoints(rows, kix, n_keys, W, "loop")
        endpoints[a]["by_delay"] = {}
        for d in delays:
            sel = np.array([keys[i][1] == d for i in range(n_keys)])
            endpoints[a]["by_delay"][str(d)] = {k: (float(np.nanmean(vecs[a][k][sel])) if np.isfinite(vecs[a][k][sel]).any() else None)
                                                for k in ("infeasible_rate", "progress_ratio", "mean_chosen_speed", "estop_share", "min_gap_mean",
                                                          "ttv_mean", "ttv_share_lt_2s", "divergence_share")}
        for p, (c4, obs) in V2_LOOP.items():
            v2[p][a], pk = v2_all(rows, kix, n_keys, W, c4, obs)
            if p == "PL7_offset_le_15m":
                vecs[a]["V2_PL7_scene_rate"] = pk["V2"]
                vecs[a]["V2_viol_PL7_scene_rate"] = pk["V2_viol"]
    res["endpoints_by_arm"] = endpoints
    res["V2"] = v2
    pairs = [("Mstar", b) for b in arms if b != "Mstar"]
    res["_csv_paired"] = paired_rows(vecs, arms, W, pairs, LOOP_PAIRED)
    res["paired_vs_Mstar"] = {}
    for r in res["_csv_paired"]:
        res["paired_vs_Mstar"].setdefault(r["endpoint"], {})[r["arm_b"]] = {"mean_diff_Mstar_minus_arm": r["mean_diff"], "ci95": [r["ci95_lo"], r["ci95_hi"]], "n_keys": r["n_scenes"]}
    return res


# ---------------------------------------------------------------- verdict-free summaries

def k7_form(d1, d3):
    """What K7's decision rule would have said (reported only; D14 v04 section 4 gates nothing on nuScenes)."""
    h1, h3 = d1["hypotheses"], d3["hypotheses"]
    if h1["HK1"] and h3["HK1"] and h1["HK3"] and h3["HK3"]:
        would = "GO-A" if h1["HK2"] else "GO-B"
    else:
        would = "NO-GO"
    failed = ["%s %s" % (t, k) for t, h in (("T1", h1), ("T3", h3)) for k in ("HK1a", "HK1b", "HK3") if not h[k]]
    return {"note": "K7-form rule evaluated and reported only: D14 v04 section 4 gates nothing on nuScenes", "k7_rule_would_say": would,
            "failed_conditions": failed, "T1": h1, "T3": h3}


# ---------------------------------------------------------------- CSV (every row stamped)

def write_csv(path, rows):
    if not rows:
        return
    rows = [dict([("stamp", STAMP)] + list(r.items())) for r in rows]
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
    a6 = (res.get("calibration_items") or {}).get("by_population") or {}
    rows = []
    for a in arms:
        e = res["endpoints_by_arm"][a]
        r = {"arm": a, "alpha": S.ALPHA_OF_ARM.get(a), "delta_prime": S.DELTA_OF_ARM.get(a), "alpha_eq": S.CURVE_ALPHA_OF_ARM.get(a),
             "decisions": e["decisions"]}
        r["infeasible_rate"] = res["infeasible_rate"][a]["mean"]
        r["infeasible_ci95_lo"], r["infeasible_ci95_hi"] = res["infeasible_rate"][a]["ci95"]
        for k in ("progress_ratio", "mean_chosen_speed", "mean_logged_speed", "divergence_share", "estop_share", "mean_backoff_level", "min_gap_mean",
                  "min_gap_share_lt_1m", "min_gap_ip_mean", "min_gap_ip_share_lt_1m", "min_gap_nip_mean", "ttv_mean", "ttv_share_lt_2s",
                  "ttv_share_lt_2s_all_decisions", "ttv_share_lt_4s", "ttv_ip_share_lt_2s", "ttv_enf_mean", "ttv_enf_share_lt_2s",
                  "ttv_enf_share_lt_4s", "ttc_proxy_v01_mean", "ttc_proxy_v01_share_lt_2s"):
            r[k] = e[k]["mean"]
            r[k + "_ci95_lo"], r[k + "_ci95_hi"] = (e[k]["ci95"] or [None, None])
        for lev, sh in e["backoff_distribution"].items():
            r["backoff_share_" + lev] = sh
        r["min_gap_p10_decisions"], r["ttv_p10_decisions"] = e["min_gap_p10_decisions"], e["ttv_p10_decisions"]
        for p in REPORT_POPS:
            lab = POP_LAB[p]
            pp = pops[p]["pooled_by_arm"].get(a) or {}
            r["V1_%s_E" % lab], r["V1_%s_lb" % lab], r["V1_%s_ub" % lab], r["V1_%s_flagged" % lab] = pp.get("E"), pp.get("lb_sim"), pp.get("ub_sim"), pp.get("sig_above")
            r["V1_%s_records" % lab] = pp.get("records")
            r["V1_%s_h0_E" % lab] = (res["V1_one_step"][p].get(a) or {}).get("E")
            v = res["V2"][p][a]
            r["V2_%s_E" % lab], r["V2_%s_lo" % lab], r["V2_%s_hi" % lab] = v["V2"]["E"], *(v["V2"].get("ci95") or [None, None])
            r["V2_%s_reference_E" % lab] = v["V2"].get("reference_E")
            r["V2_%s_tracks_per_decision" % lab] = v["V2"].get("mean_tracks_per_decision")
            for var in ("V2_one_step", "V2_viol", "V2_near", "V2_binding", "V2_exec", "V2_dedup"):
                r["%s_%s_E" % (var, lab)] = v[var].get("E")
            r["V2_near_%s_reference_E" % lab] = v["V2_near"].get("reference_E")
            r["V1_%s_dedup_E" % lab] = res["A14_duplicates"][p][a]["V1_pooled_dedup"]
            r["duplicates_%s" % lab] = res["A14_duplicates"][p][a]["duplicates"]
            r["cells_flagged_%s" % lab] = len(pops[p]["cells_by_arm"][a]["sig_above_cells"])
            r["cells_evaluable_%s" % lab] = len(pops[p]["cells_by_arm"][a]["family"])
            c = a6.get(p, {}).get(a) or {}
            r["A6_ANEES_scene_level_%s" % lab] = (c.get("anees_scene_level") or {}).get("mean")
            r["A6_median_NEES_%s" % lab], r["A6_ANEES_trimmed_%s" % lab] = c.get("median_nees"), c.get("anees_trimmed_1pct")
            r["A6_p_v_below_%s" % lab], r["A6_p_v_above_%s" % lab] = c.get("p_v_below"), c.get("p_v_above")
            r["A6_cov95_%s" % lab] = (c.get("ellipse_coverage") or {}).get("0.95")
            r["A6_NLL_%s" % lab], r["A6_ES_%s" % lab] = c.get("nll_mean"), c.get("energy_score_mean")
            r["margin_long_%s" % lab], r["margin_lat_%s" % lab] = c.get("mean_margin_long"), c.get("mean_margin_lat")
        v = res["validity_by_arm"][a]
        r["HK1a"], r["HK1b"], r["HK1"], r["HK1c_all_pops"], r["valid_form_B"] = v["HK1a"], v["HK1b"], v["HK1"], v["HK1c_all_pops"], v["valid_form_B"]
        if a != "Mstar":
            r["Mstar_minus_arm_infeasible"] = res["HK3"][a]["mean_diff"]
            r["Mstar_lower_bonferroni4"] = res["HK3"][a]["lower"]
        rows.append(r)
    write_csv(os.path.join(csv_dir, "k8_%s_decide_arms.csv" % tag), rows)
    a13 = res.get("A13_fallback_record_weighted") or {}
    rows = []
    for p in REPORT_POPS:
        a13p = ((a13.get("by_population") or {}).get(p) or {}).get("by_cell") or {}
        for a in arms:
            il = pops[p]["cells_by_arm"][a]
            for name, _ in cells:
                c = il["cells"].get(name)
                fb = a13p.get(name) or {}
                base = {"population": p, "arm": a, "cell": name, "fallback_share_Mstar_record_weighted": fb.get("share"),
                        "coarser_bound_only": fb.get("coarser_bound_only")}
                if c is not None:
                    rows.append(dict(base, evaluable=True, E=c["E"], lb_sim=c["lb_sim"], ub_sim=c["ub_sim"], se=c["se"], sig_above=c["sig_above"],
                                     records=c["records"], exceed=c["exceed"], E_rec=c["E_rec"], scenes=c["scenes"]))
                else:
                    d = il["descriptive"].get(name, {})
                    rows.append(dict(base, evaluable=False, E=d.get("E"), records=d.get("records"), scenes=d.get("scenes")))
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cells.csv" % tag), rows)
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            for var, v in res["V2"][p][a].items():
                rows.append({"population": p, "arm": a, "variant": var, "E": v.get("E"), "ci95_lo": (v.get("ci95") or [None, None])[0],
                             "ci95_hi": (v.get("ci95") or [None, None])[1], "reference_E": v.get("reference_E"),
                             "E_minus_reference": v.get("E_minus_reference"), "mean_tracks_per_decision": v.get("mean_tracks_per_decision"),
                             "decisions_with_records": v.get("decisions_with_records"), "decisions_any_exceed": v.get("decisions_any_exceed"),
                             "decision_level_rate": v.get("decision_level_rate")})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_v2.csv" % tag), rows)
    sw = res["sweep"]
    write_csv(os.path.join(csv_dir, "k8_%s_decide_sweep.csv" % tag), sw["one_curve"] + sw["reference"])
    if res.get("retune"):
        rows = []
        for f, s_ in res["retune"]["by_fold"].items():
            for g in s_["grid"]:
                rows.append({"fold": f, "selected_arm": s_["arm"], "selected_alpha_eq": s_["alpha"], "boundary": s_["boundary"],
                             "apply_keys": s_["apply_keys"], "train_keys": s_["train_keys"], "grid_arm": g["arm"], "grid_alpha_eq": g["alpha"],
                             "qualifies": g["qualifies"], **{"E_train_" + POP_LAB[p]: g["E_train"][p] for p in CONF_POPS}})
        write_csv(os.path.join(csv_dir, "k8_%s_decide_retune.csv" % tag), rows)
    write_csv(os.path.join(csv_dir, "k8_%s_decide_paired.csv" % tag), res["_csv_paired"])
    rows = []
    for a in arms:
        v = res["validity_by_arm"][a]
        for p in CONF_POPS:
            q = v["pops"][p]
            pl = q["pooled"] or {}
            rows.append({"arm": a, "population": p, "HK1a_met": q["HK1a_met"], "HK1b_met": q["HK1b_met"], "evaluable": q["evaluable"], "flagged": ";".join(q["flagged"]),
                         "pooled_E": pl.get("E"), "pooled_lb": pl.get("lb"), "pooled_ub": pl.get("ub"), "pooled_flagged": pl.get("flagged"),
                         "HK1c": pl.get("HK1c_ub_le_delta_plus_0.03"), "family_size": q["family_size"], "family_flagged": ";".join(q["family_flagged"]),
                         "valid_form_B": v["valid_form_B"]})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_validity.csv" % tag), rows)
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cal_relied_cells.csv" % tag), res["_csv_cal_cells"])
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cal_relied_l0_PD7.csv" % tag), res["_csv_cal_l0"])
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            if a in res["calibration_relied_pairs_secondary"][p]:
                c = res["calibration_relied_pairs_secondary"][p][a]
                rows.append({"population": p, "arm": a, **flat_cal(c), "anees_scene_level": (c.get("anees_scene_level") or {}).get("mean")})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_cal_relied.csv" % tag), rows)
    if res.get("calibration_items"):
        rows = []
        for p, by in res["calibration_items"]["by_population"].items():
            for a, c in by.items():
                rows.append({"population": p, "arm": a, **flat_a6(c)})
        for a, c in res["calibration_items"]["dedup_PD7"].items():
            rows.append({"population": "PD7_primary_dedup", "arm": a, **flat_a6(c)})
        write_csv(os.path.join(csv_dir, "k8_%s_decide_a6_items.csv" % tag), rows)
        write_csv(os.path.join(csv_dir, "k8_%s_decide_a6_items_cells.csv" % tag), res["_csv_a6_cells"])
        write_csv(os.path.join(csv_dir, "k8_%s_decide_a6_gross_errors.csv" % tag), res["_csv_a6_gross"])
    rows = []
    for p in REPORT_POPS:
        for a in arms:
            c = res["counts"]["records_by_population"][p][a]
            rows.append({"population": p, "arm": a, **c, "decisions": res["counts"]["decisions_by_arm"][a],
                         **{"a14_" + k: v for k, v in res["A14_duplicates"][p][a].items() if not isinstance(v, list)}})
    write_csv(os.path.join(csv_dir, "k8_%s_decide_counts.csv" % tag), rows)
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
                  "min_gap_mean", "min_gap_share_lt_1m", "min_gap_ip_mean", "ttv_mean", "ttv_share_lt_2s", "ttv_share_lt_4s", "ttv_enf_share_lt_2s",
                  "ttv_enf_share_lt_4s", "ttc_proxy_v01_mean"):
            r[k] = e[k]["mean"]
            r[k + "_ci95_lo"], r[k + "_ci95_hi"] = (e[k]["ci95"] or [None, None])
        for lev, sh in e["backoff_distribution"].items():
            r["backoff_share_" + lev] = sh
        for d, bd in e["by_delay"].items():
            for k, v in bd.items():
                r["%s_delay%s" % (k, d)] = v
        for p in V2_LOOP:
            lab = POP_LAB[p]
            pp = res["populations"][p]["pooled_by_arm"].get(a) or {}
            r["V1_%s_E" % lab], r["V1_%s_ub" % lab], r["V1_%s_flagged" % lab] = pp.get("E"), pp.get("ub_sim"), pp.get("sig_above")
            for var in ("V2", "V2_viol", "V2_near", "V2_binding", "V2_exec"):
                r["%s_%s_E" % (var, lab)] = res["V2"][p][a][var].get("E")
            r["V2_%s_reference_E" % lab] = res["V2"][p][a]["V2"].get("reference_E")
        if a != "Mstar" and ("Mstar-%s" % a) in res["progress_vs_Mstar"]:
            r["progress_Mstar_minus_arm"] = res["progress_vs_Mstar"]["Mstar-%s" % a]["mean_diff"]
        rows.append(r)
    write_csv(os.path.join(csv_dir, "k8_%s_loop_arms.csv" % tag), rows)
    write_csv(os.path.join(csv_dir, "k8_%s_loop_paired_vs_Mstar.csv" % tag), res["_csv_paired"])


def strip_csv_payload(res):
    return {k: v for k, v in res.items() if not k.startswith("_csv_")}


# ---------------------------------------------------------------- run governance: dev guard, exploratory binding, frozen plan

def current_code_hashes():
    """The code hashes k8_run_v02 logs before launch (run_record["hashes"]), recomputed from the current files."""
    import k8_run_v02 as R
    return {k + "_sha256": sha(p) for k, p in R.CODE_FILES.items()}


def check_dev_runs(runs, tags, modes, eps_by_run=None):
    """--allow-dev (R15 m12): every run record says DEV MODE, is not exploratory, and lists development scenes only; with
    eps_by_run, every episode's scene is a development scene."""
    for tag in tags:
        for mode in modes:
            rr = json.load(open(os.path.join(runs, "run_record_%s_%s.json" % (tag, mode))))
            assert str(rr.get("prereg", "")).startswith("DEV MODE"), "run %s_%s is not a DEV MODE run; --allow-dev refuses it" % (tag, mode)
            assert not rr.get("exploratory", False), "run %s_%s is exploratory; --allow-dev refuses it" % (tag, mode)
            assert set(rr["scene_names"]) <= set(DEV_SCENES_K6), "run %s_%s lists a non-development scene" % (tag, mode)
            if eps_by_run is not None:
                assert {o["scene"] for o in eps_by_run[(tag, mode)]} <= set(DEV_SCENES_K6), "run %s_%s holds a non-development episode" % (tag, mode)
    return True


def check_exploratory(runs, tags, modes, items_paths=None):
    """--exploratory (D14 v04 section 5.1; R15 C1): every run (both trackers, both modes) is an exploratory, non-dry run of the
    full design on every non-development scene; its run and launch records carry hashes equal to the current files (sim,
    runner, k6_sim_v02, this analysis, k6_analyse_v02, m_lib_v04), to its fits and manifests; its outputs equal their recorded
    hashes; no development scene is present. The items files (A6) must be exploratory items of the same scenes."""
    cur = current_code_hashes()
    assert cur["analysis_sha256"] == sha(os.path.abspath(__file__)), "the runner's CODE_FILES does not name this analysis"
    out = {"current_code_hashes": cur, "runs": {}}
    names_by_tag = {}
    for tag in tags:
        for mode in modes:
            rr = json.load(open(os.path.join(runs, "run_record_%s_%s.json" % (tag, mode))))
            assert rr.get("exploratory") is True and rr.get("dry_run") is False and rr.get("prereg") == EXPLORATORY_RUN_STAMP, \
                "run %s_%s is not an exploratory run" % (tag, mode)
            assert rr["tag"] == "%s_%s" % (tag, mode) and rr["mode"] == mode, "run record %s_%s carries another tag or mode" % (tag, mode)
            for k, v in cur.items():
                assert rr["hashes"].get(k) == v, "%s of run %s_%s differs from the current file" % (k, tag, mode)
            assert rr["hashes"]["fits_sha256"] == sha(rr["fits"]) == rr["fits_sha256"], "the fits of run %s_%s changed" % (tag, mode)
            assert rr["hashes"]["manifest_sha256"] == [sha(os.path.join(c, "MANIFEST.json")) for c in rr["caches"]], "a manifest of run %s_%s changed" % (tag, mode)
            lr = rr["launch_record"]
            assert sha(lr) == rr["launch_record_sha256"], "the launch record of run %s_%s changed" % (tag, mode)
            launch = json.load(open(lr))
            assert launch["hashes"] == rr["hashes"] and launch["dry_run"] is False and launch["exploratory"] is True, \
                "the launch record of run %s_%s differs from its run record" % (tag, mode)
            assert rr["arms"] == list(S.ARMS) and rr["delays_kf"] == DELAYS, "incomplete design in run %s_%s" % (tag, mode)
            nondev = sorted(s_ for c in rr["caches"] for s_ in json.load(open(os.path.join(c, "MANIFEST.json")))["scenes"] if s_ not in DEV_SCENES_K6)
            assert sorted(rr["scene_names"]) == nondev and len(nondev) == N_SCENES_CONF, "run %s_%s does not cover every non-development scene" % (tag, mode)
            assert not set(rr["scene_names"]) & set(DEV_SCENES_K6), "a development scene in run %s_%s" % (tag, mode)
            n_ep = N_SCENES_CONF * len(S.ARMS) * len(DELAYS) if mode == "loop" else N_SCENES_CONF * (len(S.ARMS) - 1)
            assert rr["episodes"] == n_ep, "incomplete run %s_%s: %d episodes, %d expected" % (tag, mode, rr["episodes"], n_ep)
            fits = json.load(open(rr["fits"]))
            exps = {json.load(open(os.path.join(c, "MANIFEST.json")))["experiment"] for c in rr["caches"]}
            assert fits.get("k7") is True and fits["tags"] == ["%s_train" % tag, "%s_val" % tag] and exps == {EXPERIMENT[tag]}, \
                "run %s_%s uses another tracker's fits or caches" % (tag, mode)
            for f, ext in (("episodes", "jsonl"), ("counts", "npz"), ("decisions", "npz"), ("cal", "npz")):
                assert sha(os.path.join(runs, "%s_%s_%s.%s" % (f, tag, mode, ext))) == rr["%s_sha256" % f], "%s of run %s_%s changed" % (f, tag, mode)
            names_by_tag.setdefault(tag, sorted(rr["scene_names"]))
            assert sorted(rr["scene_names"]) == names_by_tag[tag]
            out["runs"]["%s_%s" % (tag, mode)] = {"episodes": rr["episodes"], "scenes": rr["scenes"], "launched": launch.get("launched")}
    if items_paths:
        for tag, p in zip(tags, items_paths):
            summ = json.load(open(p.replace(".npz", "_summary.json")))
            assert summ.get("exploratory") is True and summ.get("stamp") == EXPLORATORY_RUN_STAMP, "items %s are not exploratory" % p
            assert summ["out_sha256"] == sha(p), "items %s changed" % p
            import k8_items_v02 as I
            assert summ["hashes"]["items_script_sha256"] == sha(I.__file__) and summ["hashes"]["k6_sim_v02_sha256"] == cur["k6_sim_v02_sha256"], \
                "items %s were made by other code" % p
            assert sorted(summ["scene_names"]) == names_by_tag[tag], "items %s cover other scenes than the runs" % p
    return out


def check_binding(prereg, runs, tags, manifests):
    """Confirmatory binding (as k7_analyse_v02.check_binding, for a future K8 freeze) plus k6_sim_v02 (R15 m12: its decode_cell
    and N_CELL define the populations through A.mask). Not used under --allow-dev or --exploratory."""
    import k8_run_v02 as R
    assert list(tags) == ["t1", "t3"], "the tags must be t1 t3, in this order"
    side, hashes = R.frozen_hashes(prereg)
    for p in manifests:
        assert sha(p) in hashes, "a manifest passed to the analysis is not frozen: " + p
    rec = open(os.path.join(os.path.dirname(prereg), "K8_FREEZE_RECORD_v02.txt"), encoding="utf-8").read()
    assert side in rec, "the plan sidecar differs from the freeze record"
    for p in (os.path.abspath(__file__), A.__file__, A.S.__file__, M.__file__, S.__file__):
        assert sha(p) in hashes, "analysis input not frozen: " + p
    for tag in tags:
        for mode in ("decide", "loop"):
            rr = json.load(open(os.path.join(runs, "run_record_%s_%s.json" % (tag, mode))))
            assert rr["prereg"] == side and rr["mode"] == mode, "run %s_%s was not made under the frozen K8 plan" % (tag, mode)
            for k in ("fits_sha256", "sim_sha256", "runner_sha256"):
                assert rr[k] in hashes, "%s of run %s_%s is not frozen" % (k, tag, mode)
            assert rr["sim_sha256"] == sha(S.__file__), "run %s_%s did not use k8_sim_v02" % (tag, mode)
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


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tags", nargs=2, required=True)
    ap.add_argument("--manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--csv-dir", default=None)
    ap.add_argument("--prereg", default=None)
    ap.add_argument("--allow-dev", action="store_true", help="development checks only: the 10 development scenes")
    ap.add_argument("--exploratory", action="store_true", help="D14 v04 section 5.1: the 840-scene exploratory run")
    ap.add_argument("--boot", type=int, default=B_BOOT)
    ap.add_argument("--modes", nargs="+", default=["decide", "loop"])
    ap.add_argument("--items", nargs=2, default=None, help="k8_items_v02 files (t1, t3): A6 primary and the A8 item counts")
    ap.add_argument("--fits", nargs=2, default=None, help="fits files (t1, t3): A3 folds, A6 and A13")
    a = ap.parse_args(argv)
    global DEV_SCENES, STRICT_Q, STAMP
    assert int(a.allow_dev) + int(a.exploratory) + int(a.prereg is not None) == 1, "exactly one of --allow-dev, --exploratory, --prereg"
    side, binding = None, None
    if a.allow_dev:
        DEV_SCENES = ()
        A.MIN_SCENES, A.MIN_LOGS = 2, 1
        STRICT_Q = False
        STAMP = STAMPS["dev"]
        check_dev_runs(a.runs, a.tags, a.modes)
    else:
        DEV_SCENES = DEV_SCENES_K6
        A.MIN_SCENES, A.MIN_LOGS = 39, 8
        STRICT_Q = True
        assert a.boot == B_BOOT and a.modes == ["decide", "loop"], "the confirmatory statistics are fixed: B = %d, both modes" % B_BOOT
        assert a.fits and a.items, "--fits and --items are required outside development checks"
        if a.exploratory:
            STAMP = STAMPS["exploratory"]
            binding = check_exploratory(a.runs, a.tags, a.modes, a.items)
        else:
            STAMP = STAMPS["confirmatory"]
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
    out = {"stamp": STAMP, "design": DESIGN, "delta": DELTA, "boot": a.boot, "prereg_sha256": side, "dev_mode": bool(a.allow_dev),
           "exploratory": bool(a.exploratory), "binding": binding, "evaluability": {"min_scenes": A.MIN_SCENES, "min_logs": A.MIN_LOGS},
           "strict_q": STRICT_Q, "dev_scenes_excluded": list(DEV_SCENES),
           "arms": list(ALL_ARMS), "alpha_of_arm": S.ALPHA_OF_ARM, "delta_of_arm": S.DELTA_OF_ARM, "curve_alpha_of_arm": S.CURVE_ALPHA_OF_ARM,
           "sim_sha256": sha(S.__file__), "analysis_sha256": sha(os.path.abspath(__file__)), "k6_analyse_sha256": sha(A.__file__),
           "k6_sim_v02_sha256": sha(A.S.__file__), "decide": {}, "loop": {}}
    for i, tag in enumerate(a.tags):
        fits = json.load(open(a.fits[i])) if a.fits else None
        items = items_counts(a.items[i], set(DEV_SCENES)) if a.items else None
        items_k8 = load_items_k8(a.items[i], set(DEV_SCENES)) if a.items else None
        arm_of_scene = None
        for mode in a.modes:
            eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s_%s.jsonl" % (tag, mode)))]
            if a.allow_dev:
                check_dev_runs(a.runs, [tag], [mode], {(tag, mode): eps})
            else:
                assert not ({o["scene"] for o in eps} & set(DEV_SCENES_K6)), "a development scene in run %s_%s" % (tag, mode)
            counts = dict(np.load(os.path.join(a.runs, "counts_%s_%s.npz" % (tag, mode))))
            D = dict(np.load(os.path.join(a.runs, "decisions_%s_%s.npz" % (tag, mode))))
            C = dict(np.load(os.path.join(a.runs, "cal_%s_%s.npz" % (tag, mode))))
            if mode == "decide":
                r = analyse_decide(eps, counts, D, C, log_of_scene, a.boot, np.random.default_rng([SEED, i, 0]), [POWER_SEED, i], fits, items, items_k8)
                arm_of_scene = (r.get("retune") or {}).get("arm_of_scene")
                csv_tables_decide(r, tag, csv_dir)
                out["decide"][tag] = strip_csv_payload(r)
            else:
                r = analyse_loop(eps, counts, D, C, log_of_scene, a.boot, np.random.default_rng([SEED, i, 1]), arm_of_scene)
                csv_tables_loop(r, tag, csv_dir)
                out["loop"][tag] = strip_csv_payload(r)
    if "decide" in a.modes and len(out["decide"]) == 2:
        out["k7_form_reported_only"] = k7_form(out["decide"][a.tags[0]], out["decide"][a.tags[1]])
        print(json.dumps(out["k7_form_reported_only"]["k7_rule_would_say"]))
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(STAMP)
    print("K8 ANALYSIS V02 DONE")


if __name__ == "__main__":
    main()
