#!/usr/bin/env python3
"""C1 decision rules v02 (Claude line, c1_rules_v02, 5 Nov 2026) = c1_rules_v01 (kept unchanged; it stays the module of c1_predarm_v07
and c1_power_counts_v05, which read only constants whose values are equal here) with D16 v34 Choice 53
(90_DECISIONS/D16_DELEGATED_CHOICES_v34.md). A bound module of README v10: c1_analyse_v10 imports it; test_c1_v13 (group CRIT) pins
every constant and checks that each constant shared with c1_rules_v01 has the same value (B_BOOT excepted: the two modules that keep
c1_rules_v01 do not read it).
  (b) H4 is treated as H3. On H4's route (H4_ROUTE = "transfer_lt3d") each of a comparator's 9 removal conditions is tested at
      LEVEL_REMOVAL_H4 = 1 - ALPHA_REMOVAL_H4 / 9 = 1 - 0.0025/9, and H4's Form B p-value is multiplied by H4_P_MULTIPLIER = 2 (capped
      at 1) before Holm (c1_analyse_v10.form_b). H1's own V_t (within_lt3d) and the descriptive routes keep LEVEL_REMOVAL_V =
      1 - 0.0125/9. The route is known through analyse_route_tracker_routed, installed in c1_analyse_v02's namespace, which records the
      route being analysed (removal_level(), flag_level()).
  (c) B_BOOT = 40000 (was 20000): at least 10 replicates beyond every decision quantile (H4's removal quantile 0.0025/9 needs
      B >= 36000). The power rule keeps 2000 datasets and 500 weight rows, the descriptive arms 500 datasets.
  (d) Every Monte Carlo p-value is (k + MC_P_ADD) / (B + MC_P_ADD) = (k + 1)/(B + 1), k the replicates on the null side, never k/B
      (Davison and Hinkley 1997, ch. 4; Phipson and Smyth 2010): mc_p(). paired_mc replaces c1_analyse_v02.paired (its p_lt0, read
      by Form B's, H3's and H4's p-values); supt_lower_pvalues_mc replaces c1_analyse_v02.supt_lower_pvalues (H10's cell part: B6's
      flag p and the paired p; a zero-SE cell gets 1/(B + 1) if its estimate exceeds the target, else 1); form_c_criteria (H2) and
      h10_rule_criteria's NI part count k themselves; h6_rules_criteria converts the method stage's per-cell p = k/refit_B (the
      table records refit_B, so c1_mstage_v06 is not reopened) to (k + 1)/(refit_B + 1), and refuses a table without refit_B or with a
      p that is not a multiple of 1/refit_B. No p-value is 0.

c1_rules_v01's docstring (kept):
C1 decision rules after the criteria audit (Claude line, c1_rules_v01, 5 Nov 2026). D16 v30 Choice 50
(90_DECISIONS/D16_DELEGATED_CHOICES_v30.md; criteria register 90_DECISIONS/C1_CRITERIA_REGISTER_v02.md), with D16 v33 Choice 52
(90_DECISIONS/D16_DELEGATED_CHOICES_v33.md: H1's budget split, H3's removal level and doubled p, B = 20000, H9 descriptive, one decision
form per hypothesis): the lead's decision on the researcher's evidence audit of every pass/fail threshold, under ICH E9 section 5.5: evidence AGAINST M* is judged at one-sided 0.05
(the strict direction for M*), and every bound or flag whose passing SUPPORTS a claim in M*'s favour at one-sided 0.025 (two-sided
95 %). A bound module of README v09 (role module): c1_analyse_v09, c1_predarm_v07 and c1_power_counts_v05 import it; every threshold
below is defined ONCE, here, with its source, and test_c1_v12 (group CRIT) pins each value.

What it provides (k6_analyse_v02, k8_analyse_v04, m_lib_v04 and c1_analyse_v02 are imported and never edited):
  * the constants, the levels derived from them (levels()), and config_check(cfg): a config that states a rule constant (top-level
    or under "criteria", any case) with another value than the code's, or a Form C "c" other than C_FORM_C, is refused;
  * power_target(...): the power rule. TARGET-ONLY planting: for each evaluable cell j, cell j is drawn at P_PLANT and every other
    evaluable cell at exactly DELTA (beta-binomial with intra-scene correlation RHO, one rate per scene and cell, the arm's real
    record counts); the dataset counts for j if j is flagged in the all-evaluable one-sided sup-t at POWER_FLAG_LEVEL
    (m_lib_v04._simul's rule, with A.flag's zero-SE rule est > DELTA). N_DATASETS datasets (N_DATASETS_DESCRIPTIVE_ARMS for an arm whose validity is descriptive only), each judged with the first N_WEIGHTS
    bootstrap weight rows; datasets are drawn one after another from one generator, so a run with fewer datasets is a prefix of a
    run with more (nested). Outcome-free: only record counts enter. power_target_reference is the same rule written as a plain loop
    over the targets with m_lib_v04._simul (the test checks that both agree);
  * HK1C_LEVEL is the lead's final value 0.995 (D16 v30 Choice 50(c)): Valid's HK1c term and ValidJ's upper bound in H3.
  * hk1_rule_criteria: k8_analyse_v04.hk1_rule's validity tests with these levels: M* (and every arm that is judged for validity,
    not removal) at LEVEL_AGAINST; a comparator of K (B0, B1, B3, B4, B6, B9, RETUNED) at LEVEL_REMOVAL_V for its cell flags, family
    flags and pooled flag (its 9 removal conditions); HK1c's pooled upper bound at HK1C_LEVEL; the families from power_target. For
    M* it adds the descriptive outputs (never gated): the simultaneous one-sided 95 % upper bounds (labelled approximate), each
    family's share of the population's relied records, the floor at F_MIN 4, 6 and 8, and per-cell power at DESC_P;
  * joint_validity_criteria / joint_section_criteria: k8_analyse_v04's joint-loss validity with the joint methods (M*J, M*Jx) at
    LEVEL_AGAINST and H3's comparators at LEVEL_REMOVAL_VJ, the upper bound at HK1C_LEVEL;
  * form_a_criteria (1 - ALPHA_FOR / 4), form_c_criteria (1 - ALPHA_FOR), h10_rule_criteria (B6's flag and the paired sup-t lower
    bound at LEVEL_FOR, the NI bound at LEVEL_FOR), h6_rules_criteria (H6b from the method stage's per-cell p-values at ALPHA_FOR),
    holm_v05_criteria (family S at ALPHA_FOR), and apply_analysis(B, K, A5), which installs them;
  * analyse_decide_criteria: k8_analyse_v04.analyse_decide, then the per-arm extras of hk1_rule_criteria (levels, zero-SE detail,
    descriptive outputs) copied into validity_by_arm (k8_analyse_v04 keeps only a fixed list of keys there).
"""
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(C1))
for _d in ("k6", "k8", "m"):
    sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", _d))
sys.path.insert(0, C1)
import k6_analyse_v02 as A  # noqa: E402
import k8_analyse_v04 as K  # noqa: E402
import m_lib_v04 as M  # noqa: E402

# ------------------------------------------------------------------------------------------------- the constants (one place)
ALPHA_AGAINST = 0.05      # D16 v30 Choice 50; ICH E9 5.5: evidence AGAINST M* at one-sided 0.05: M*'s flags, family flags, pooled LB; H6a, H7, H9
ALPHA_FOR = 0.025         # D16 v30 Choice 50; ICH E9 5.5: a bound whose passing SUPPORTS a claim for M*: Forms A, B, C, H3, H4, H6b, H10, Holm family S
ALPHA_REMOVAL = 0.0125    # D16 v33 Choice 52(c): H1's removal half of 0.025: each of V_t's 9 removal conditions at 1 - 0.0125/9 (was 0.025)
ALPHA_FORM_B = 0.0125     # D16 v33 Choice 52(c): H1's superiority half of 0.025: Form B UB^{1 - 0.0125/|V_t|} < 0 (was 0.025)
ALPHA_REMOVAL_VJ = 0.0025  # D16 v33 Choice 52(c): H3's V^J removal, each of 3 conditions at 1 - 0.0025/3 (half of the smallest Holm level)
H3_P_MULTIPLIER = 2       # D16 v33 Choice 52(c): H3's p-value is doubled (capped at 1) before Holm
ALPHA_REMOVAL_H4 = 0.0025  # D16 v34 Choice 53(b): H4's V_t removal, each of its 9 removal conditions at 1 - 0.0025/9 (as H3)
H4_P_MULTIPLIER = 2       # D16 v34 Choice 53(b): H4's Form B p-value is doubled (capped at 1) before Holm
H4_ROUTE = "transfer_lt3d"   # D16 v34 Choice 53(b): the route whose Form B is H4 (c1_analyse_v02.ROUTE_LABEL); other routes keep ALPHA_REMOVAL
MC_P_ADD = 1              # D16 v34 Choice 53(d): every Monte Carlo p-value is (k + 1)/(B + 1), never k/B (Davison & Hinkley 1997; Phipson & Smyth 2010)
N_REMOVAL_V = 9           # V_t's removal conditions: cell flag, family flag, pooled flag x PD7, SD1_7, PD
N_REMOVAL_VJ = 3          # H3's V^J_t: the pooled joint-loss flag x PD7, SD1_7, PD
HK1C_LEVEL = 0.995        # D16 v30 Choice 50(c); Loh 1987 calibration rule; development coverage at 375 units, 60_RESULTS/c1_criteria_sensitivity_v02 (note 2e69fae6…), A_hk1c_level_v02.json
HK1C_MARGIN = 0.03        # unchanged: HK1c and ValidJ need that upper bound <= DELTA + 0.03
DELTA = 0.05              # the claim's exceedance threshold (C1 plan; k6_analyse_v02.DELTA)
P_PLANT = 0.15            # D16 v30 Choice 50: the target cell's planted exceedance rate (value unchanged)
RHO = 0.5                 # D16 v30 Choice 50: beta-binomial intra-scene correlation (value unchanged)
POWER_MIN = 0.80          # D16 v30 Choice 50: power-qualified at power >= 0.80 (unchanged)
N_DATASETS = 2000         # D16 v30 Choice 50: power datasets (was 200), for M* and every comparator of K
N_DATASETS_DESCRIPTIVE_ARMS = 500   # Claude's cost choice (reported, not D16): power datasets for arms whose validity is descriptive only
N_WEIGHTS = 500           # D16 v30 Choice 50: the first 500 bootstrap weight rows judge each dataset (unchanged)
POWER_FLAG_LEVEL = 0.95   # D16 v30 Choice 50: the target counts if flagged in the all-evaluable one-sided sup-t at 0.95
F_MIN = 6                 # unchanged: >= 6 power-qualified cells on PD7 and SD1_7 (and H9's E2 cells)
PD_MIN_EVALUABLE = 1      # unchanged: PD needs >= 1 evaluable cell (no count floor)
MIN_UNITS = 39            # unchanged: an evaluable cell has >= 39 units (scenes; on AV2 a unit is a log) ...
MIN_LOGS = 8              # ... from >= 8 logs (unchanged)
B_BOOT = 40000            # D16 v34 Choice 53(c): log-cluster bootstrap draws of every bootstrap of the analysis (was 20000): >= 10 beyond H4's removal quantile; power keeps N_WEIGHTS
H9_LABEL_C1 = "descriptive"   # D16 v33 Choice 52(b): H9 is descriptive in C1; c1_analyse_v10 --c1 refuses another h9_label
C_FORM_C = 0.03           # unchanged: Form C's c; the frozen config's "c" must equal it
NI_MARGIN = 0.03          # unchanged: H10's non-inferiority margin
FORM_A_K = 4              # Form A's comparators B0, B1, B4, B9 (Bonferroni over 4)
HOLM_M = 5                # family S: H2, H3, H4, H6b, H10 (gate H1 unchanged)
DESC_F_MIN = (4, 8)       # D16 v30 Choice 50 (descriptive): the floor also read at these F_MIN
DESC_P = (0.10, 0.12, 0.20)   # D16 v30 Choice 50 (descriptive): per-cell power at these planted rates (MDE80 read-off)
DESC_N_DATASETS = 500     # D16 v30 Choice 50 (descriptive): power datasets at DESC_P
UB_APPROX_LABEL = "approximate (development coverage 0.78 at 39 units, 0.87 at 150, near δ)"

CONSTANTS = {k: v for k, v in dict(globals()).items() if k.isupper() and k not in ("C1", "W_ROOT", "UB_APPROX_LABEL", "CONSTANTS")
             and isinstance(v, (int, float, tuple, str))}

LEVEL_AGAINST = 1 - ALPHA_AGAINST                      # 0.95
LEVEL_FOR = 1 - ALPHA_FOR                              # 0.975
LEVEL_REMOVAL_V = 1 - ALPHA_REMOVAL / N_REMOVAL_V      # 1 - 0.0125/9 = 0.998611...
LEVEL_REMOVAL_VJ = 1 - ALPHA_REMOVAL_VJ / N_REMOVAL_VJ  # 1 - 0.0025/3 = 0.999166...
LEVEL_REMOVAL_H4 = 1 - ALPHA_REMOVAL_H4 / N_REMOVAL_V  # 1 - 0.0025/9 = 0.999722... (H4's route)
HOLM_LEVELS = tuple(ALPHA_FOR / (HOLM_M - i) for i in range(HOLM_M))   # the levels Holm can assign: 0.005, 0.00625, 0.00833, 0.0125, 0.025
LEVEL_FORM_A = 1 - ALPHA_FOR / FORM_A_K                # 0.99375
REMOVAL_ARMS = ("B0", "B1", "B3", "B4", "B6", "B9", "RETUNED")   # the comparators of K (c1_analyse_v02.K_SET)
DECISION_ARMS = ("Mstar",) + REMOVAL_ARMS                        # arms whose power family enters a C1 decision
JOINT_METHOD_ARMS = tuple(K.JOINT_METHODS)                       # M*J, M*Jx: judged for validity, not removal
UB_KEY = "descriptive_simultaneous_ub_0.95"
_LAST = {}
_CTX = {"route": None}   # the route analyse_route_tracker_routed is analysing (D16 v34 Choice 53b)

# the modules this rule builds on carry the same values (they are not edited; this asserts that nothing diverges)
assert (A.DELTA, A.F_MIN, A.POWER_MIN, A.POWER_P, A.POWER_RHO) == (DELTA, F_MIN, POWER_MIN, P_PLANT, RHO), \
    "k6_analyse_v02's constants differ from c1_rules_v02's"
assert (K.DELTA, K.F_MIN, K.POWER_MIN) == (DELTA, F_MIN, POWER_MIN)


def levels():
    return {"against": LEVEL_AGAINST, "for": LEVEL_FOR, "removal_V_t": LEVEL_REMOVAL_V, "removal_VJ_t": LEVEL_REMOVAL_VJ,
            "removal_V_t_H4": LEVEL_REMOVAL_H4, "h4_route": H4_ROUTE,
            "hk1c_ub": HK1C_LEVEL, "form_a": LEVEL_FORM_A, "power_flag": POWER_FLAG_LEVEL,
            "form_b": "1 - %s / |V_t| (H1 and the descriptive routes; H4's nominal bound, 1 - %s / (%d |V_t|), is the same number)" % (
                ALPHA_FORM_B, ALPHA_FOR, H4_P_MULTIPLIER),
            "h3": "p = min(1, %d |V^J| max p); nominal bound 1 - %s / (%d |V^J|)" % (H3_P_MULTIPLIER, ALPHA_FOR, H3_P_MULTIPLIER),
            "h4": "on %s: removal at 1 - %s / %d; p = min(1, %d |V_t| max p); nominal bound 1 - %s / (%d |V_t|)" % (
                H4_ROUTE, ALPHA_REMOVAL_H4, N_REMOVAL_V, H4_P_MULTIPLIER, ALPHA_FOR, H4_P_MULTIPLIER),
            "p_value": "(k + %d) / (B + %d), k = the replicates on the null side (D16 v34 Choice 53d)" % (MC_P_ADD, MC_P_ADD),
            "holm_family_S": ALPHA_FOR, "holm_levels": list(HOLM_LEVELS), "bootstrap_B": B_BOOT, "power_weights": N_WEIGHTS,
            "decision_form": "H1: the bound; family S (H2, H3, H4, H6b, H10): the p-value, the bound at the Holm-assigned level reported (Choice 52e)"}


def _eq(a, b):
    if isinstance(b, str):
        return a == b
    if isinstance(b, tuple):
        return isinstance(a, (list, tuple)) and len(a) == len(b) and all(_eq(x, y) for x, y in zip(a, b))
    try:
        return abs(float(a) - float(b)) < 1e-12
    except (TypeError, ValueError):
        return False


def check_h9_label_c1(cfg, mode):
    """D16 v33 Choice 52(b): in a C1 run (--c1) the config's h9_label must be H9_LABEL_C1 ("descriptive")."""
    if mode == "c1":
        assert cfg.get("h9_label") == H9_LABEL_C1, "the C1 config must set h9_label = %r (D16 v33 Choice 52b), not %r" % (H9_LABEL_C1, cfg.get("h9_label"))
    return cfg.get("h9_label")


def bm_quantile(bm, level):
    return float(np.quantile(bm, level))


def config_check(cfg):
    """D16 v30 Choice 50: a config that sets a rule constant differently from the code is refused (no config default, no
    override). Checks the top-level keys and the "criteria" block, in any case, and Form C's "c" per tracker."""
    bad = []
    seen = {}
    crit = cfg.get("criteria") or {}
    assert isinstance(crit, dict), "the config's criteria block must be an object"
    for k, v in list(crit.items()) + [(k, v) for k, v in cfg.items() if str(k).upper() in CONSTANTS]:
        name = str(k).upper()
        if name not in CONSTANTS:
            bad.append("%s (not a rule constant of c1_rules_v02)" % k)
        elif not _eq(v, CONSTANTS[name]):
            bad.append("%s = %r (the code's %s = %r)" % (k, v, name, CONSTANTS[name]))
        else:
            seen[name] = CONSTANTS[name]
    for t, v in (cfg.get("c") or {}).items():
        if not _eq(v, C_FORM_C):
            bad.append("c[%s] = %r (C_FORM_C = %r)" % (t, v, C_FORM_C))
    assert not bad, "the config sets rule constants differently from the code (c1_rules_v02; D16 v30 Choice 50, v34 Choice 53): %s" % bad
    return {"stated_and_equal": seen, "c": dict(cfg.get("c") or {})}


# ------------------------------------------------------------------------------------------------- p-values and the route (Choice 53)
def mc_p(k, n):
    """D16 v34 Choice 53(d): the Monte Carlo p-value of k of n replicates on the null side, (k + 1)/(n + 1); never 0."""
    k, n = int(k), int(n)
    assert n > 0 and 0 <= k <= n, (k, n)
    return (k + MC_P_ADD) / (n + MC_P_ADD)


def removal_level(route=None):
    """D16 v34 Choice 53(b): the comparators' removal level on a route: LEVEL_REMOVAL_H4 on H4's route, LEVEL_REMOVAL_V elsewhere
    (H1's within_lt3d and the descriptive routes). Without a route argument, the route being analysed (_CTX)."""
    r = _CTX["route"] if route is None else route
    return LEVEL_REMOVAL_H4 if r == H4_ROUTE else LEVEL_REMOVAL_V


def removal_alpha(route=None):
    r = _CTX["route"] if route is None else route
    return ALPHA_REMOVAL_H4 if r == H4_ROUTE else ALPHA_REMOVAL


def paired_mc(rate, Ws, a, b, level):
    """c1_analyse_v02.paired (the same arithmetic) with D16 v34 Choice 53(d): p_lt0 = (k + 1)/(B + 1), k = the bootstrap means >= 0;
    k and B are recorded."""
    d = np.asarray(rate[a], float) - np.asarray(rate[b], float)
    bm = (Ws @ d) / Ws.sum(1)
    k = int(np.sum(bm >= 0))
    return {"mean_diff": float(d.mean()), "ub": float(np.quantile(bm, level)), "level": float(level),
            "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])], "p_lt0": mc_p(k, len(bm)), "p_k": k, "p_B": int(len(bm)), "_bm": bm}


def supt_lower_pvalues_mc(est, boot, target):
    """c1_analyse_v02.supt_lower_pvalues (the same statistic) with D16 v34 Choice 53(d): per cell (k + 1)/(B + 1), k = the replicates
    whose studentised sup statistic is >= the cell's; a zero-SE cell: 1/(B + 1) if its estimate exceeds the target (k = 0), else 1."""
    est, boot = np.asarray(est, float), np.asarray(boot, float)
    n = int(boot.shape[0])
    se = np.nanstd(boot, axis=0, ddof=1)
    ok = se > 0
    if not ok.any():
        return np.where(est > target, mc_p(0, n), 1.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        T = np.nanmax(np.where(ok, (boot - est) / np.where(ok, se, 1.0), np.nan), axis=1)
        t = np.where(ok, (est - target) / np.where(ok, se, 1.0), np.nan)
    return np.array([mc_p(int(np.sum(T >= t[j])), n) if ok[j] else (mc_p(0, n) if est[j] > target else 1.0) for j in range(len(est))])


def mstage_p(p, n):
    """D16 v34 Choice 53(d) for H6b: the method stage records p = k / n (n = its refit_B replicates); returns (k + 1)/(n + 1).
    Refuses a p that is not a multiple of 1/n (the table would not be the method stage's k/n)."""
    n = int(n)
    k = float(p) * n
    assert n > 0 and abs(k - round(k)) < 1e-6 and 0 <= round(k) <= n, "the method stage's p %r is not k/%d" % (p, n)
    return mc_p(int(round(k)), n)


def _routed(f):
    def analyse_route_tracker_routed(route, *a, **k):
        """c1_analyse_v02.analyse_route_tracker, with the route recorded for removal_level() (D16 v34 Choice 53b)."""
        prev = _CTX["route"]
        _CTX["route"] = route
        try:
            return f(route, *a, **k)
        finally:
            _CTX["route"] = prev
    analyse_route_tracker_routed.wrapped = f
    return analyse_route_tracker_routed


# ------------------------------------------------------------------------------------------------- the power rule
def _sidx(scene_of_ep):
    scenes = sorted(set(scene_of_ep))
    pos = {s: i for i, s in enumerate(scenes)}
    return np.array([pos[s] for s in scene_of_ep]), len(scenes)


BATCH = 25                # power: datasets are drawn and judged in batches of 25 (a run's datasets are a prefix of a longer run's)


class _Layout:
    """Where records exist: rates are drawn per (scene, cell) pair with records, counts per (unit, cell) entry with records."""

    def __init__(self, Nf, sidx, S):
        Ni = Nf.astype(int)
        F = Ni.shape[1]
        has = np.zeros((S, F), bool)
        np.logical_or.at(has, sidx, Ni > 0)
        self.pairs = np.flatnonzero(has.ravel())
        self.S, self.F, self.sidx = S, F, sidx
        self.nz = np.nonzero(Ni > 0)
        self.n_nz = Ni[self.nz]
        self.Nf = Nf
        self.pres = (Nf > 0).astype(float)


def _draw_batch(rng, lay, th, rate, nb):
    """nb datasets: (nb, units, cells) counts. One beta rate per (scene, cell) pair, binomial counts per (unit, cell) entry."""
    P = np.zeros((nb, lay.S * lay.F))
    P[:, lay.pairs] = rng.beta(rate * th, (1 - rate) * th, size=(nb, len(lay.pairs)))
    P = P.reshape(nb, lay.S, lay.F)[:, lay.sidx, :]
    X = np.zeros((nb,) + lay.Nf.shape)
    X[:, lay.nz[0], lay.nz[1]] = rng.binomial(lay.n_nz[None, :], P[:, lay.nz[0], lay.nz[1]])
    return X


def _rates_batch(lay, X, W):
    """A.rates for a batch: est (nb, cells) and boot (nb, rows of W, cells)."""
    p = np.divide(X, lay.Nf[None], out=np.zeros_like(X), where=lay.Nf[None] > 0)
    with np.errstate(invalid="ignore", divide="ignore"):
        est = p.sum(axis=1) / lay.pres.sum(axis=0)[None, :]
        boot = np.matmul(W[None], p) / (W @ lay.pres)[None]
    return est, boot


def target_flags(est_b, boot_b, est_t, boot_t, level=POWER_FLAG_LEVEL, delta=DELTA):
    """For a batch (leading axis) and each target i: is cell i flagged in the all-evaluable one-sided sup-t (m_lib_v04._simul, side
    lower) when column i of the base family (est_b, boot_b) is replaced by the target column (est_t[:, i], boot_t[:, :, i])?
    est_*: (nb, cells); boot_*: (nb, rows, cells). Returns (nb, cells) booleans."""
    se_b = np.nanstd(boot_b, axis=1, ddof=1)
    se_t = np.nanstd(boot_t, axis=1, ddof=1)
    ok_b, ok_t = se_b > 0, se_t > 0
    with np.errstate(invalid="ignore", divide="ignore"):
        dev_b = np.where(ok_b[:, None, :], (boot_b - est_b[:, None, :]) / np.where(ok_b, se_b, 1.0)[:, None, :], np.nan)
        dev_t = np.where(ok_t[:, None, :], (boot_t - est_t[:, None, :]) / np.where(ok_t, se_t, 1.0)[:, None, :], np.nan)
    nb, R, F = dev_b.shape
    db = np.where(np.isnan(dev_b), -np.inf, dev_b)
    if F > 1:
        a1 = db.argmax(axis=2)
        m1 = np.take_along_axis(db, a1[:, :, None], axis=2)[:, :, 0]
        d2 = db.copy()
        np.put_along_axis(d2, a1[:, :, None], -np.inf, axis=2)
        m2 = d2.max(axis=2)
        excl = np.where(a1[:, :, None] == np.arange(F)[None, None, :], m2[:, :, None], m1[:, :, None])
    else:
        excl = np.full_like(db, -np.inf)
    T = np.maximum(excl, np.where(np.isnan(dev_t), -np.inf, dev_t))
    T = np.where(np.isneginf(T), np.nan, T)
    q = np.full((nb, F), np.nan)
    fin = np.isfinite(T)
    if fin.all():
        q = np.quantile(T, level, axis=1)
    else:
        for b, i in zip(*np.nonzero(fin.any(axis=1))):
            q[b, i] = np.nanquantile(T[b, :, i], level)
    with np.errstate(invalid="ignore"):
        lb = np.where(ok_t, est_t - q * se_t, est_t)
        return (ok_t & (lb > delta)) | (~ok_t & (est_t > delta))


def _setup(N, ev, scene_of_ep, rho):
    fam = np.flatnonzero(ev)
    scenes = sorted(set(scene_of_ep))
    pos = {s: i for i, s in enumerate(scenes)}
    sidx = np.array([pos[s] for s in scene_of_ep])
    return fam, _Layout(N[:, fam].astype(float), sidx, len(scenes)), (1 - rho) / rho


def power_target(N, ev, scene_of_ep, W, rng, p_plant=P_PLANT, rho=RHO, reps=N_DATASETS, base_rate=DELTA, level=POWER_FLAG_LEVEL):
    """The power rule (see the module docstring). N: units x cells record counts; ev: evaluable mask; W: the weight rows (the caller
    passes the first N_WEIGHTS); rng: numpy Generator (the caller's seed). Datasets come in batches of BATCH (base counts at
    base_rate, then target counts at p_plant). Returns (power per cell, 0 where not evaluable; fam)."""
    pw = np.zeros(N.shape[1])
    fam, lay, th = _setup(N, ev, scene_of_ep, rho)
    if not len(fam):
        return pw, fam
    hits = np.zeros(len(fam))
    for start in range(0, int(reps), BATCH):
        nb = min(BATCH, int(reps) - start)
        est_b, boot_b = _rates_batch(lay, _draw_batch(rng, lay, th, base_rate, nb), W)
        est_t, boot_t = _rates_batch(lay, _draw_batch(rng, lay, th, p_plant, nb), W)
        hits += target_flags(est_b, boot_b, est_t, boot_t, level, DELTA).sum(axis=0)
    pw[fam] = hits / int(reps)
    return pw, fam


def power_target_reference(N, ev, scene_of_ep, W, rng, p_plant=P_PLANT, rho=RHO, reps=N_DATASETS, base_rate=DELTA, level=POWER_FLAG_LEVEL):
    """The same rule and the same draws as power_target, judged by a plain loop over datasets and targets with m_lib_v04._simul
    (for the test only: slow)."""
    pw = np.zeros(N.shape[1])
    fam, lay, th = _setup(N, ev, scene_of_ep, rho)
    if not len(fam):
        return pw, fam
    hits = np.zeros(len(fam))
    for start in range(0, int(reps), BATCH):
        nb = min(BATCH, int(reps) - start)
        est_b, boot_b = _rates_batch(lay, _draw_batch(rng, lay, th, base_rate, nb), W)
        est_t, boot_t = _rates_batch(lay, _draw_batch(rng, lay, th, p_plant, nb), W)
        for b in range(nb):
            for i in range(len(fam)):
                e, bb = est_b[b].copy(), boot_b[b].copy()
                e[i], bb[:, i] = est_t[b, i], boot_t[b, :, i]
                lb, se, q, ok = M._simul(e, bb, level, "lower")
                hits[i] += bool((ok[i] and lb[i] > DELTA) or ((not ok[i]) and e[i] > DELTA))
    pw[fam] = hits / int(reps)
    return pw, fam


def mde80(power_by_p):
    """The smallest planted rate whose power is >= POWER_MIN, from {P: power}; None if none reaches it."""
    ok = sorted(p for p, v in power_by_p.items() if v >= POWER_MIN)
    return ok[0] if ok else None


# ------------------------------------------------------------------------------------------------- validity (HK1, HK1c, families)
def flag_level(arm):
    return removal_level() if arm in REMOVAL_ARMS else LEVEL_AGAINST


def power_datasets(arm):
    return N_DATASETS if arm in DECISION_ARMS else N_DATASETS_DESCRIPTIVE_ARMS


def hk1_rule_criteria(T, cells, scene_of_ep, log_of_ep, W, power_key, fams=None, arm="Mstar"):
    """k8_analyse_v04.hk1_rule (same tests, same output keys) at the audit's levels and with the target-only power rule."""
    one = np.ones((1, len(scene_of_ep)))
    strict = bool(K.STRICT_Q and arm == "Mstar")
    lvl = flag_level(arm)
    out = {"pops": {}, "arm": arm, "strict_q": strict, "zero_se_quantiles": [],
           "levels": {"flags": lvl, "hk1c_ub": HK1C_LEVEL, "power_flag": POWER_FLAG_LEVEL,
                      "route": _CTX["route"],
                      "role": "comparator: removal conditions at 1 - %s / %d" % (removal_alpha(), N_REMOVAL_V) if arm in REMOVAL_ARMS
                      else "judged for validity at 1 - %s" % ALPHA_AGAINST},
           "power_rule": {"planting": "target-only (others at DELTA)", "P": P_PLANT, "rho": RHO, "datasets": power_datasets(arm),
                          "weights": N_WEIGHTS, "power_min": POWER_MIN, "batch": BATCH,
                          "arm_class": "decision" if arm in DECISION_ARMS else "descriptive only"}}
    note_full = K.ZERO_SE_NOTE + " (" + K.ZERO_SE_DETAIL + ")"
    hk1a = hk1b = True
    desc = {}
    for k, p in enumerate(K.CONF_POPS):
        N, X = T[p]
        ev = A.evaluable(N, scene_of_ep, log_of_ep)
        fam = np.flatnonzero(ev)
        est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
        r = {"evaluable": int(len(fam)), "flagged": [], "zero_se_flagged": []}
        if len(fam):
            lb, ub, se, sig, q = A.flag(est, boot, fam, lvl)
            r["q"], qn = K._q(q, "%s cells %s" % (arm, p), strict)
            if qn:
                r["q_note"] = note_full
                out["zero_se_quantiles"].append(p + ":cells")
            r["flagged"] = [cells[j][0] for i, j in enumerate(fam) if sig[i]]
            r["zero_se_flagged"] = [cells[j][0] for i, j in enumerate(fam) if sig[i] and not se[i] > 0]
            r["max_lb"] = float(np.nanmax(lb))
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        r["pooled"] = None
        if A.evaluable(Np, scene_of_ep, log_of_ep)[0]:
            e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
            lbp, _, sep, sigp, qp = A.flag(e1, b1, np.array([0]), lvl)
            _, ubh, _, _, _ = A.flag(e1, b1, np.array([0]), HK1C_LEVEL)
            qpv, qpn = K._q(qp, "%s pooled %s" % (arm, p), strict)
            r["pooled"] = {"E": float(e1[0]), "lb": float(lbp[0]), "ub": float(ubh[0]), "flagged": bool(sigp[0]),
                           "HK1c_ub_le_delta_plus_0.03": bool(ubh[0] <= DELTA + HK1C_MARGIN), "q": qpv,
                           "zero_se_flagged": bool(sigp[0] and not sep[0] > 0), "levels": {"lb_flag": lvl, "ub_hk1c": HK1C_LEVEL}}
            if qpn:
                r["pooled"]["q_note"] = note_full
                out["zero_se_quantiles"].append(p + ":pooled")
        a_ok = (not r["flagged"]) and len(fam) >= PD_MIN_EVALUABLE
        b_ok = r["pooled"] is not None and not r["pooled"]["flagged"]
        if fams is not None and p in fams:
            qual = fams[p]
            pw = None
        else:
            pw, _ = power_target(N, ev, scene_of_ep, W[:N_WEIGHTS], np.random.default_rng(list(power_key) + [k]), reps=power_datasets(arm))
            qual = ev & (pw >= POWER_MIN)
            r["power_at_%.2f" % P_PLANT] = {cells[j][0]: float(pw[j]) for j in fam}
        fq = np.flatnonzero(qual)
        r["family"] = [cells[j][0] for j in fq]
        r["family_size"] = int(len(fq))
        r["family_flagged"] = []
        r["family_q"] = None
        r["family_record_share"] = float(N[:, fq].sum() / N.sum()) if N.sum() > 0 else None
        r["floor_at_F_MIN"] = {str(f): bool(len(fq) >= f) for f in sorted(set(DESC_F_MIN) | {F_MIN})}
        if len(fq):
            _, _, sef, sigf, qf = A.flag(est, boot, fq, lvl)
            r["family_q"], qfn = K._q(qf, "%s family %s" % (arm, p), strict)
            if qfn:
                r["family_q_note"] = note_full
                out["zero_se_quantiles"].append(p + ":family")
            r["family_flagged"] = [cells[j][0] for i, j in enumerate(fq) if sigf[i]]
            r["zero_se_family_flagged"] = [cells[j][0] for i, j in enumerate(fq) if sigf[i] and not sef[i] > 0]
        if p in K.FLOOR_POPS:
            r["floor_met"] = bool(len(fq) >= F_MIN and not r["family_flagged"])
            a_ok = a_ok and r["floor_met"]
        else:
            a_ok = a_ok and not r["family_flagged"]
            r["floor_note"] = "reported only: no count floor on PD (in-path non-exceedance is not power-qualified); the own-family no-flag test applies (N1)"
        r["HK1a_met"], r["HK1b_met"] = bool(a_ok), bool(b_ok)
        hk1a &= a_ok
        hk1b &= b_ok
        out["pops"][p] = r
        if arm == "Mstar":
            d = {"evaluable": int(len(fam)), "cells": {}, "max_ub": None, "max_cell": None, "label": UB_APPROX_LABEL}
            if len(fam):
                _, ub95, _, _, _ = A.flag(est, boot, fam, 0.95)
                d["cells"] = {cells[j][0]: float(ub95[i]) for i, j in enumerate(fam)}
                kk = int(np.nanargmax(ub95))
                d["max_ub"], d["max_cell"] = float(ub95[kk]), cells[fam[kk]][0]
            desc.setdefault("ub", {})[p] = d
            if pw is not None and len(fam):
                byp = {}
                for P in DESC_P:
                    pwp, _ = power_target(N, ev, scene_of_ep, W[:N_WEIGHTS], np.random.default_rng(list(power_key) + [k, 1000 + int(round(P * 1000))]),
                                          p_plant=P, reps=DESC_N_DATASETS)
                    byp[P] = pwp
                byp[P_PLANT] = pw
                desc.setdefault("power", {})[p] = {
                    "per_cell": {cells[j][0]: {("%.2f" % P): float(v[j]) for P, v in sorted(byp.items())} for j in fam},
                    "mde80": {cells[j][0]: mde80({P: float(v[j]) for P, v in byp.items()}) for j in fam},
                    "datasets": {("%.2f" % P): (N_DATASETS if P == P_PLANT else DESC_N_DATASETS) for P in byp},
                    "family_record_share": r["family_record_share"], "family_size": r["family_size"], "floor_at_F_MIN": r["floor_at_F_MIN"]}
    out["HK1a"], out["HK1b"], out["HK1"] = bool(hk1a), bool(hk1b), bool(hk1a and hk1b)
    if arm == "Mstar":
        out[UB_KEY] = {"label": "descriptive (Choice 47f; never gated): M*'s simultaneous one-sided 95 % upper bounds; " + UB_APPROX_LABEL,
                       "pops": desc.get("ub", {})}
        out["descriptive_power"] = {"label": "descriptive (never gated): per-cell power at the planted rates, MDE80, record shares, "
                                             "floors at F_MIN 4, 6, 8", "pops": desc.get("power", {})}
    _LAST[arm] = out
    return out


EXTRA_KEYS = ("levels", "power_rule", UB_KEY, "descriptive_power")
POP_EXTRA_KEYS = ("zero_se_flagged", "zero_se_family_flagged", "family_record_share", "floor_at_F_MIN", "family")


def analyse_decide_criteria(*a, **k):
    """k8_analyse_v04.analyse_decide, then the extras of hk1_rule_criteria copied into validity_by_arm."""
    _LAST.clear()
    res = _ANALYSE_DECIDE_V04(*a, **k)
    for arm, out in list(_LAST.items()):
        v = (res.get("validity_by_arm") or {}).get(arm)
        if v is None:
            continue
        for key in EXTRA_KEYS:
            if key in out:
                v[key] = out[key]
        for p in K.CONF_POPS:
            v["pops"][p].update({kk: out["pops"][p].get(kk) for kk in POP_EXTRA_KEYS})
    return res


# ------------------------------------------------------------------------------------------------- the joint loss (H3)
def joint_validity_criteria(rows, kix, n_keys, W, scene_of_ep, log_of_ep, arm):
    """k8_analyse_v04.joint_validity with the joint methods (M*J, M*Jx) flagged at LEVEL_AGAINST and every other arm (H3's
    comparators) at LEVEL_REMOVAL_VJ; the upper bound of ValidJ at HK1C_LEVEL. The keys *_0.95 keep their 0.95 meaning."""
    lvl = LEVEL_AGAINST if arm in JOINT_METHOD_ARMS else LEVEL_REMOVAL_VJ
    one = np.ones((1, n_keys))
    out = {"pops": {}, "levels": {"flag": lvl, "ub": HK1C_LEVEL}}
    ok_all = True
    for p in K.CONF_POPS:
        c4, obs = K.V2_DECIDE[p]
        N, X, _, _ = K.v2_tables(rows, kix, n_keys, c4, obs)
        r = {"evaluable": bool(A.evaluable(N, scene_of_ep, log_of_ep)[0]), "valid": False}
        if N.sum() > 0:
            est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
            lb95, ub95, _, _, _ = A.flag(est, boot, np.array([0]), 0.95)
            lbf, _, se, sig, q = A.flag(est, boot, np.array([0]), lvl)
            _, ubh, _, _, _ = A.flag(est, boot, np.array([0]), HK1C_LEVEL)
            r.update({"E": float(est[0]), "lb_one_sided_0.95": float(lb95[0]), "ub_one_sided_0.95": float(ub95[0]), "flagged": bool(sig[0]),
                      "lb_flag_level": float(lbf[0]), "ub_hk1c_level": float(ubh[0]), "q": float(q) if np.isfinite(q) else None,
                      "ub_le_delta_plus_0.03": bool(ubh[0] <= DELTA + HK1C_MARGIN), "point_le_delta": bool(est[0] <= DELTA),
                      "decisions_with_records": int(N.sum()), "decisions_any_exceed": int(X.sum()), "scenes": int((N[:, 0] > 0).sum()),
                      "zero_se_flagged": bool(sig[0] and not se[0] > 0),
                      "ci95": [float(np.nanquantile(boot[:, 0], 0.025)), float(np.nanquantile(boot[:, 0], 0.975))]})
            r["valid"] = bool(r["evaluable"] and not r["flagged"] and r["ub_le_delta_plus_0.03"])
        ok_all = ok_all and r["valid"]
        out["pops"][p] = r
    out["valid"] = bool(ok_all)
    return out


def joint_section_criteria(rows_by_arm, arms, n_keys, W, scene_of_ep, log_of_ep, rate, Ws, fits):
    """k8_analyse_v04.joint_section with joint_validity_criteria (the arm's role decides its level): the validity of every arm is
    computed here, and k8_analyse_v04.joint_section, which asks for it once per arm in the order of arms, receives it."""
    jv = {a: joint_validity_criteria(rows_by_arm[a][0], rows_by_arm[a][1], n_keys, W, scene_of_ep, log_of_ep, a) for a in arms}
    order = iter(list(arms))
    saved = K.joint_validity
    K.joint_validity = lambda *args: jv[next(order)]
    try:
        out = _JOINT_SECTION_V04(rows_by_arm, arms, n_keys, W, scene_of_ep, log_of_ep, rate, Ws, fits)
    finally:
        K.joint_validity = saved
    assert all(out["validity_by_arm"][a] is jv[a] for a in arms)
    return out


# ------------------------------------------------------------------------------------------------- forms, H6b, H10, Holm
def form_a_criteria(status, rate, Ws, method="Mstar", B=None):
    B = B or _B["B"]
    assert len(B.FORM_A_SET) == FORM_A_K
    present = [c for c in B.FORM_A_SET if c in rate]
    per = {}
    for c in present:
        r = B.paired(rate, Ws, method, c, LEVEL_FORM_A)
        r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    return {"label": "descriptive", "valid_method": status[method]["valid"], "vs": per, "complete": len(present) == len(B.FORM_A_SET),
            "level": LEVEL_FORM_A, "met": bool(status[method]["valid"] and len(present) == len(B.FORM_A_SET) and all(v["lower"] for v in per.values()))}


def form_c_criteria(rate, Ws, c_t, alpha=ALPHA_FOR, method="Mstar", ref="B4"):
    """c1_analyse_v02.form_c at 1 - alpha (nominal), plus the bound at every level Holm can assign (Choice 52e: the p-value governs in
    family S; the bound at the Holm-assigned level is reported beside it)."""
    r = _B["form_c"](rate, Ws, c_t, alpha, method, ref)
    r["level"] = 1 - alpha
    d = np.asarray(rate[method], float) - np.asarray(rate[ref], float)
    bm = (Ws @ d) / Ws.sum(1)
    r["holm_levels"] = {"%.6f" % a: {"level": 1 - a, "ub": bm_quantile(bm, 1 - a), "holds": bool(bm_quantile(bm, 1 - a) <= c_t)} for a in HOLM_LEVELS}
    k = int(np.sum(bm > c_t))
    r["p"], r["p_k"], r["p_B"] = mc_p(k, len(bm)), k, int(len(bm))
    r["p_definition"] = "(k + 1)/(B + 1), k = the bootstrap replicates on the null side (Delta > c) (D16 v34 Choice 53d)"
    return r


def h10_rule_criteria(cells, est, boot, ev, sig_b6, sig_m, rate, Ws, alpha=ALPHA_FOR, margin=NI_MARGIN):
    """c1_analyse_v02.h10_rule with B6's flag and the paired sup-t lower bound at LEVEL_FOR (supporting M*) and the NI bound at
    1 - alpha; M*'s own flags stay at LEVEL_AGAINST (sig_m, from k8_analyse_v04's populations)."""
    B = _B["B"]
    fam_b6 = np.flatnonzero(ev["B6"])
    sig_b6_for = set()
    if len(fam_b6):
        _, _, _, sg, _ = A.flag(est["B6"], boot["B6"], fam_b6, LEVEL_FOR)
        sig_b6_for = {cells[j][0] for i, j in enumerate(fam_b6) if sg[i]}
    pr = A.paired(est, boot, ev, cells, "B6", "Mstar", LEVEL_FOR)
    both = np.flatnonzero(ev["B6"] & ev["Mstar"])
    p_flag = dict(zip([cells[j][0] for j in fam_b6], B.supt_lower_pvalues(est["B6"][fam_b6], boot["B6"][:, fam_b6], DELTA))) if len(fam_b6) else {}
    d = est["B6"][both] - est["Mstar"][both]
    db = boot["B6"][:, both] - boot["Mstar"][:, both]
    p_pair = dict(zip([cells[j][0] for j in both], B.supt_lower_pvalues(d, db, 0.0))) if len(both) else {}
    qual = [cells[j][0] for j in both if cells[j][0] in sig_b6_for and cells[j][0] not in set(sig_m) and pr.get(cells[j][0], {}).get("positive")]
    cand = [cells[j][0] for j in both if cells[j][0] not in set(sig_m)]
    p_cell = min([max(p_flag.get(c, 1.0), p_pair.get(c, 1.0)) for c in cand], default=1.0)
    ni = B.paired(rate, Ws, "Mstar", "B6", 1 - alpha)
    bm = ni.pop("_bm")
    k_ni = int(np.sum(bm > margin))
    ni.update({"margin": margin, "met": bool(ni["ub"] <= margin), "p": mc_p(k_ni, len(bm)), "p_k": k_ni, "p_B": int(len(bm))})
    holm = {}
    for a in HOLM_LEVELS:   # Choice 52(e): the bound form at every level Holm can assign
        sg_a = set()
        if len(fam_b6):
            _, _, _, sga, _ = A.flag(est["B6"], boot["B6"], fam_b6, 1 - a)
            sg_a = {cells[j][0] for i, j in enumerate(fam_b6) if sga[i]}
        pr_a = A.paired(est, boot, ev, cells, "B6", "Mstar", 1 - a)
        q_a = [cells[j][0] for j in both if cells[j][0] in sg_a and cells[j][0] not in set(sig_m) and pr_a.get(cells[j][0], {}).get("positive")]
        ub_a = bm_quantile(bm, 1 - a)
        holm["%.6f" % a] = {"level": 1 - a, "cells_failing_B6": q_a, "ni_ub": ub_a, "holds": bool(q_a and ub_a <= margin)}
    return {"cells_failing_B6": qual, "cell_part": bool(qual), "noninferiority": ni, "met": bool(qual and ni["met"]), "holm_levels": holm,
            "p": float(max(p_cell, ni["p"])), "p_definition": "max(cell part, NI part), each (k + 1)/(B + 1) (D16 v34 Choice 53d)",
            "levels": {"B6_flag": LEVEL_FOR, "paired_lb": LEVEL_FOR, "ni_ub": 1 - alpha, "Mstar_flags": LEVEL_AGAINST},
            "B6_flagged_at_0.95": sorted(sig_b6),
            "rule": "C1 v04 5.4 H10 at the audit's levels (B6's flag and the paired bound at %s; NI at %s; margin %s)" % (LEVEL_FOR, 1 - alpha, margin)}


def h6_rules_criteria(ms):
    """H6a as c1_analyse_v02.h6_rules (M*'s flags at LEVEL_AGAINST). H6b at ALPHA_FOR: a cell where M* is not flagged and both B4's
    sup-t p-value and the paired (B4 - M*) sup-t p-value are <= ALPHA_FOR (the method stage's H6b_detail: per cell the larger of
    the two; the p-value form of 'B4 flagged and LB^{sup-t}(B4 - M*) > 0 at one-sided 0.975')."""
    B = _B["B"]
    h = B.M.hypotheses_e1(ms["E1"]["fixed"], ms["E1"]["refit"])
    raw = ms.get("H6b_detail")
    assert isinstance(raw, dict), "the method-stage table has no H6b_detail: H6b cannot be judged at ALPHA_FOR"
    n = (ms.get("sizes") or {}).get("refit_B")
    assert n, "the method-stage table records no refit_B: H6b's p cannot be converted to (k + 1)/(B + 1) (D16 v34 Choice 53d)"
    det = {c: mstage_p(p, n) for c, p in raw.items()}   # D16 v34 Choice 53(d): (k + 1)/(refit_B + 1)
    cells = sorted(c for c, p in det.items() if p <= ALPHA_FOR)
    return {"H6a": bool(h["HM1"]), "Mstar_flagged_cells": h["Mstar_flagged_cells"], "H6b": bool(cells), "B4_failing_cells": cells,
            "H6b_p": min(det.values()) if det else 1.0, "H6b_detail": det, "H6b_method_stage_k_over_refit_B": ms.get("H6b_p"),
            "H6b_refit_B": int(n), "H6b_p_definition": "per cell (k + 1)/(refit_B + 1) from the method stage's k/refit_B; the smallest (D16 v34 Choice 53d)",
            "H6b_level": ALPHA_FOR,
            "B4_failing_cells_at_0.95_flags": B.M.failures([ms["E1"]["refit"]], "B4", "B4-Mstar")}


def holm_v05_criteria(claims, statuses, gate):
    """c1_analyse_v05.holm_v05 with family S at ALPHA_FOR, and D16 v33 Choice 52(e): the p-value governs. A claim of S is confirmed
    when Holm rejects it (gate H1 open); the bound-form status at the nominal level is kept beside it as 'holds_bound_nominal', and
    c1_analyse_v10 (as v09) reports the bound at the Holm-assigned level and any disagreement."""
    A5 = _B["A5"]
    full = A5.B3.holm({c: v for c, v in claims.items() if statuses.get(c) != "not tested"}, ALPHA_FOR, gate=gate)
    for c, v in full.items():
        v["holds_bound_nominal"] = v.get("holds")
        if gate and v.get("rejected") is not None:
            v["confirmed"] = bool(v["rejected"])
            v["decision_form"] = "p-value (D16 v33 Choice 52e): confirmed iff Holm rejects"
    for c in A5.FAMILY_S:
        st = statuses.get(c, "not tested")
        if st == "not tested":
            full[c] = dict(full[c], p=1.0, holds=False, rejected=False if gate else None, confirmed=False, status=st,
                           label="not tested (%s)" % "; ".join(statuses.get("_why_" + c, ["input missing"])))
        else:
            full[c]["status_bound_nominal"] = st
            if gate and full[c].get("rejected") is not None:   # Choice 52(e): the p-value governs the status inside S
                full[c]["status"] = "holds" if full[c]["rejected"] else "does not hold"
            else:
                full[c]["status"] = st
            full[c].setdefault("confirmed", False)
        full[c]["alpha_family"] = ALPHA_FOR
        assert not full[c].get("confirmed") or gate, "a claim confirmed without the gate"
    assert len(A5.FAMILY_S) == HOLM_M
    return full


_B = {}
_ANALYSE_DECIDE_V04 = K.analyse_decide
_JOINT_SECTION_V04 = K.joint_section


def apply_analysis(B, A5):
    """Installs the audit's rules in the analysis chain (c1_analyse_v02's and k8_analyse_v04's namespaces, as c1_analyse_v03 and
    v09 do). Idempotent."""
    if _B.get("applied"):
        return
    _B.update({"B": B, "A5": A5, "form_c": B.form_c, "paired_v02": B.paired, "supt_v02": B.supt_lower_pvalues,
               "analyse_route_tracker_v02": B.analyse_route_tracker, "applied": True})
    B.paired = paired_mc
    B.supt_lower_pvalues = supt_lower_pvalues_mc
    B.analyse_route_tracker = _routed(_B["analyse_route_tracker_v02"])
    K.hk1_rule = hk1_rule_criteria
    K.analyse_decide = analyse_decide_criteria
    K.joint_section = joint_section_criteria
    B.form_a = form_a_criteria
    B.form_c = form_c_criteria
    B.h10_rule = h10_rule_criteria
    B.h6_rules = h6_rules_criteria
    A5.holm_v05 = holm_v05_criteria
