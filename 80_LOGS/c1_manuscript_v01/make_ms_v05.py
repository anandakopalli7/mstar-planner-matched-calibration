#!/usr/bin/env python3
"""Produces 20_DESIGN/MANUSCRIPT_DRAFT_v05.md from 20_DESIGN/MANUSCRIPT_DRAFT_v05a.md (SHA-256 5e887907...; never edited).
The full v05a texts of Sections IV-K (detail), V-C to V-E and V-F1 to V-F6 move verbatim to Appendices A, B and E, with short
summaries left in the body; four descriptive or development tables move to the appendices (X1 -> B1, K8 -> B2, Trajectron++ -> B3,
tracker scores -> F5) and the body tables are renumbered I-IX by first citation.

v05 = v05a after the length cut (body I-VII from about 17,000 to about 12,000 words, mostly by moving detail into Appendices A-F
and by removing text that repeats a table or another section) and the open fixes of 20_DESIGN/V05_TODO_FROM_LATEX_v01.md
(items 1, 2, 3, 5, 8-11; table renumbering). No number, table value or claim changes; the texts fixed before the outcome
(abstract, the introduction's registered-test paragraph, contribution 6, the V-F7 verdict sentence and the sentence after it,
Section VI-E, the conclusion) are asserted byte-identical. Every change is an explicit replacement or a move of an exact block
of v05a, each asserted to occur once. Change log: 20_DESIGN/V05_CHANGE_LOG_v01.md.

Usage: python make_ms_v05.py [output path]   (default 20_DESIGN/MANUSCRIPT_DRAFT_v05.md; refuses an existing output)
The self-checks at the end (fixed texts, number tokens, labels, citation keys, wording counts, float citation order, word
counts) run on every build and abort on a failure.
"""
import collections
import hashlib
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
SRC = os.path.join(D, "MANUSCRIPT_DRAFT_v05a.md")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(D, "MANUSCRIPT_DRAFT_v05.md")
assert not os.path.exists(OUT), "refusing to overwrite " + OUT
raw = open(SRC, "rb").read()
assert hashlib.sha256(raw).hexdigest() == "5e887907e2d7990821175fd002005bdbdcabdf6ed8c99b58c9a4634ce5a03674", "v05a hash"
A = raw.decode("utf-8")
s = A
LOG = []  # (section, kind, what)


def note(sec, kind, what):
    LOG.append((sec, kind, what))


def one(t, a):
    n = t.count(a)
    assert n == 1, (n, a[:140])
    return t.index(a)


def blk(start, end, t=None):
    """The exact block of v05a (or of t) from start to the first end after it, both inclusive; start asserted unique."""
    t = A if t is None else t
    i = one(t, start)
    j = t.index(end, i)
    return t[i:j + len(end)]


def rp(a, b):
    global s
    one(s, a)
    s = s.replace(a, b)


def region(start, end, new):
    """Replace s[start:end) (start and end markers asserted unique) by new."""
    global s
    i = one(s, start)
    j = one(s, end)
    assert i < j
    s = s[:i] + new + s[j:]


def put_before(anchor, text):
    rp(anchor, text + anchor)


# ---------------------------------------------------------------------------------------------------------------------
# Blocks of v05a used verbatim (extracted before any change, so every moved text is byte-identical to v05a)
# ---------------------------------------------------------------------------------------------------------------------
TITLE = blk("# Decision-Projected Calibration of Tracker Covariances", "a Registered Test on Argoverse 2\n")
STALE = blk("`[ABSTRACT AND CONCLUSION TO BE REWRITTEN", "THE ABSTRACT BELOW IS v02's]`\n")
ABSTRACT = blk("Chance-constrained planners with linearised half-space constraints need", "supported in neither secondary test.")
REG = open(os.path.join(D, "ms_v05_parts_lead", "01_intro_result.md"), encoding="utf-8").read().strip("\n")
C6 = open(os.path.join(D, "ms_v05_parts_lead", "02_contribution6.md"), encoding="utf-8").read().strip("\n")
VERDICT = blk("> In a registered, one-shot test on 375 Argoverse 2 logs", "is tested separately, by H4 and H7 (below).")
VIE = blk("**E. The registered test** (the frozen plan's limits, stated before any outcome)", "not that no other analysis was run.")
CONCL = blk("## VII. Conclusion", "`[placeholder for the repository reference]`.")
for fx in (REG, C6):
    one(A, fx)

II_B = blk("**B. Where the covariance comes from.**", "none certifies the extrapolated covariance a planner consumes.")

IVK_MID = blk("Midpoint checks use interpolated", "the next calibrated step's margin.")
IVK_CONF = blk("A conflict the other agent brings", "is not the planner's to resolve.")
IVK_161 = blk("On nuScenes, T1's fits used 1.61 million items", "the scored set has 0.92 million.")
IVK_STEPS = blk("Steps beyond 2 s are not enforced:", "unused copies of the 2 s fit.")
ALG1P = blk("```\nAlgorithm 1-P (M*)", "# fit on all items; score validity on relied items\n```")
THEORY = blk("**What the theory covers.**\n- **Within a dataset.**", "A population at the planner's predicted pose was not run (Section VI-B).")

GT = blk("Ground truth: the seven tracking classes", "val 6,019 keyframes `[E01 §2.1 / GT-TRAIN, GT-VAL]`.")

X1_OLD = blk("**X1 (discovery; 150 val scenes; plan `ab9b8e05…`).**", "which were already over-covered `[E01 §5.1 / X1R: family_h2s]`.")
X1_G1 = blk("Criterion G1 required a FAILS cell", "(nominal 0.025 plus 2 Monte Carlo SE) `[E01 §5.1, §3.4 / X1-REP; X1-FWER]`.")
X2_OC = blk("Pre-freeze false-FAILS rates were 0.024", "× the X1 effect `[E01 §3.7, §5.2 / X2-FWER; X2-POWER]`.")
READ_OLD = blk("**Reading.** (1) *Shape, not scale*", "because 80 % of those items are parked cars.")

VC_HEAD = blk("### C. Method evaluation: DP-SCRC on three tracker settings", "no deviations)")
VC_DESIGN = blk("Decisions at 2 s; 1 s and 4 s descriptive (E4)", "Operating characteristics are in Appendix B.")
TAB4 = blk("**Table IV. Pre-specified hypotheses per tracker setting at 2 s.**", "| true (not confirmatory) | **false** |")
VC_E1 = blk("**E1 (Table V).** On T1 the diagnosis replicates", "under any of the 12 sensitivities `[E01 §5.3; D07 §2]`.")
TAB5 = blk("**Table V. E1 held-out-log scene-mean exceedance", "| 0.000 | 0.070 | 0.104 | 0.058 | 0.007 | **0.046** |")
VC_B4_TAIL = blk("The directions differ, a lateral tail on T1", "are above DP-SCRC's `[D07 §4]`.")
VC_R08 = blk("A separate results review rebuilt the pipeline from the raw exports", "to 10⁻¹⁷ `[E01 §6 / R08]`.")
VC_E2BIAS = blk("These per-cell bounds are not bias-corrected, and refit replicates", "by up to that amount `[R08 m8]`.")
VC_T1MULT = blk("On T1, car < 20 m, the multipliers on the projected SD", "`[E01 §5.3 / MR-T1: E2_h2s.fit_on_all_train.Mstar]`.")
VC_T3MULT = blk("On T3, 91 of the 96 multipliers are below 1, including", "(own fit) `[E01 §5.3, App. A row 8 / MR-T3: E2_h2s.fit_on_all_train.Mstar]`.")
VC_FORM = blk("The diagnosis generalises in form, not in direction", "`[D07 §3 item 5]`.")
VC_COMPARE = blk("B3 and B6c are maxima of DP-SCRC's own thresholds", "their ratios price certification with less structure.")
TAB6 = blk("**Table VI. Ratio of mean margins at 2 s on val", "| M-LS / DP-SCRC | 1.032 | 1.072 | 1.003 | M-LS is not recommended |")
VC_HM3 = blk("**The course-change layer (HM3, confirmatory on T3).**", "`[E01 §5.3 / MR-T3; D07 §2]`.")

K8TAG = blk("`[K8 = 70_TESTS/", "K8_JOINT_NOTE_v01.md]`")
VD_FIT = blk("Fits are cross-fitted over 5 log folds, with a log-cluster bootstrap (B = 2000).", "≥ 39 scenes from ≥ 8 logs.")
VD_POWER = blk("K8's rule is its own:", "26 / 18 / 5 (T3).")
VD_VALDET = blk("Point estimates exceed δ in 9 of 32 P_rel cells", "None is near a flag.")
VD_FAM = blk("The power-qualified families under K8's rule are", "27 / 18 / 5 (T3).")
VD_B0CELLS = blk("(car lateral turning and new; car longitudinal new;", "pedestrian longitudinal static)")
VD_C1 = blk("These are B3 on T1, and B0 and B3 on T3.", "(paired −0.75; −0.60 and −0.71).")
VD_C2 = blk("These comparisons carry little evidence. B3, whose margin is at least M\\*'s on every item by construction",
            "and T3's B0 in 0.76.")
VD_B6 = blk("The informative comparison on T3 is with B6", "(in 12 P_rel cells on each tracker).")
VD_B6T1 = blk("On T1 the strata pay:", "`[K8: paired_vs_Mstar.infeasible_rate.B6; ERR E12]`")
VD_RET = blk("**RETUNED** equals B0 on T1,", "`[K8: retune; ERR E14; R16 §5 item 11]`.")
VD_INDEP = blk("A decision also holds about 30 relied records", "`[K8: V2.PD7_primary.Mstar; ERR E9; R16 M1]`.")
TAB7_ROWS = blk("| Tracker | Arm | Valid | P_rel | P_near | P_ip |", "| 32 / 32 | 0.003 | 0.953 | 0.030 | — / — |")

D17TAG = blk("`[D17 = 90_DECISIONS/", "R19_TPP_RESULTS_REVIEW_v01.md]`")
VE_RUN = blk("It runs online through our adaptation of the authors' code", "with the moment-matched covariance primary.")
VE_CORR = blk("DP-SCRC is cross-fitted on 5 scene folds, which split logs", "with a log-cluster bootstrap (B = 2000).")
TAB8 = blk("**Table VIII. Trajectron++ on nuScenes validation", "| 0 / 20 | 1.50 | 0.030 [0.023, 0.037] | 0 / 20 | 2.40 |")

VFTAG = blk("`[C1-PLAN = 40_PROTOCOL/", "C1_FREEZE_TIME_RECORD_v01.md]`")
VF_CBGS = blk("(2 CBGS epochs [Zhu2019cbgs]).", "could not be used.")
VF_PUB = blk("B6 and M\\* use fixed partitions where [Marques2024]", "learn theirs.")
VF_NOTK = blk("- **Not in K:**\n", "  - the published filters' own implementations.")
VF_DESCR = blk("- **Descriptive results:**\n", "QCNet [Zhou2023qcnet] is not tested.")
VF_STATS = blk("- **Units.** The log is the unit of the estimand", "  - leaves one of its two outputs without the other.")
VF_DETECT = blk("- **Power is a pre-data property.**", "gives 0.88–0.97 `[C1-PLAN §7; S22]`.")
VF_GO = blk("- **What a GO would show, per tracker:**", "  - superiority over methods outside K.")
VF_R7TAG = blk("**7. Results.** `[C1D = 60_RESULTS/", "full item-by-item results with every source key: Appendix F]`")
VF_VERDICT_BLOCK = blk("**The verdict of record is GO.**", "is tested separately, by H4 and H7 (below).")
TABX = blk("**Table X. The registered screen for M\\* on Argoverse 2**",
           "`[C1A: c1.within_lt3d.t*.status.Mstar.pops; C1D: Mstar_power_families; CSV: k8_within_lt3d_t*_decide_validity.csv]`")
FIG9 = blk("**Fig. 9.** M\\*'s per-cell exceedance on Argoverse 2", "manifest figs_v01_manifest.json]`")
TAB12_ROWS = blk("| Tracker | Arm | Screen | P_rel |", "| 2 / 25 | 0.611 | 0.316 (0.438) | 0.028 | – |")
TAB12_SRC = blk("`[CSV: k8_within_lt3d_t*_decide_{validity,arms,v2,safety,cal_relied}.csv; equal to the tool output",
                "C1_RESULTS_MATERIAL_r1_v01.md]`")
FIG10 = blk("**Fig. 10.** Infeasible-decision rate per arm on Argoverse 2", "`[FIG: 95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf]`")
TAB13_ROWS = blk("| Claim | What it tests | p (Holm level) | Status |", "| H8 | the diagnosis of Section V-B replicates (T1, B0, in-path cars, lateral, 2 s) | – | holds |")
TAB9 = blk("**Table IX. Tracker scores on the 375 logs**", "`[TRK: 60_RESULTS/av2_trk/c1_375/{hota,metrics}/*_pooled.json]`")
VF_SCREEN_TAGS = "`[C1D: Mstar_power_families.*.per_cell; Mstar_simultaneous_upper_bounds; CSV: k8_within_lt3d_t*_decide_cells.csv]`"
one(A, VF_SCREEN_TAGS)
VF_FORMB_TAG = "`[C1D: hypotheses.H1.by_tracker.*.V, vs, comparator_reasons; zero_se_effects]`"
one(A, VF_FORMB_TAG)
VF_H8 = blk("- **H8 holds: the diagnosis replicated.**", "which the nuScenes diagnosis did not show.")
VF_R21PEND = "With the power rule also redrawn in every set: `[R21 step 4: pending]`."
one(A, VF_R21PEND)
VIA = blk("**A. Wording.**", "δ = 0.05 is a calibration level per constraint, not a safety target.")

# ---------------------------------------------------------------------------------------------------------------------
# 0. Header: the draft's own header notes (v05a and v04 blocks) and the stale abstract bracket are removed; one line kept
# ---------------------------------------------------------------------------------------------------------------------
i = one(s, "## Abstract")
head = s[:i]
assert head.startswith("# MANUSCRIPT_DRAFT_v05a") and "# (v04 header, kept for the record)" in head and TITLE in head and STALE in head
s = ("MANUSCRIPT_DRAFT_v05 — v05a (5e887907…) after the length cut and the v05 fixes, 7 Nov 2026 "
     "(header notes in V05_CHANGE_LOG_v01.md)\n\n" + TITLE + "\n" + s[i:])
note("Header", "removed", "v05a header, the v04 header kept for the record, and the stale abstract bracket; copied to the change log")

# ---------------------------------------------------------------------------------------------------------------------
# I. Introduction (the registered-test paragraph and contribution 6 untouched)
# ---------------------------------------------------------------------------------------------------------------------
region("**What trackers check instead.**", "**The measurement on nuScenes.**", r"""**What trackers check instead.** The covariance comes from a tracker whose noise model was set for another purpose, and its consistency is checked, if at all, with the whole-vector normalised estimation error squared (NEES) or its average (ANEES) [BarShalom2001; Osterburg2026]; in the corpus we searched, no tracking paper measures the one-sided tail of the error projected onto a constraint normal at a planning horizon `[S02 §1.3]`. Explicit constructions show that NEES acceptance neither implies nor is implied by this property, and that a multiplier and an inflation factor are not equivalent corrections, each paying a computable price when directions need different corrections (Theorems 1–2, Proposition 5). These statements are elementary, with ingredients in print [Gneiting2007; Ziegel2014; Forsling2025]; what is new is to state them at the tracker–planner interface and to measure the consequence on real stacks.

""")
note("I", "tightened", "'What trackers check instead': two bullets joined into the paragraph; wording kept")
region("**The measurement on nuScenes.**", "**The correction and its first test.**", r"""**The measurement on nuScenes.** We measured it first on the tracker's own state and covariance extrapolated 2 s. A pre-specified study on the 700 nuScenes training scenes, frozen with its code before its outcomes were computed (one pre-freeze check previewed the decision; Section VI-D), found for in-path cars that the toward-ego lateral margin is exceeded in 19.4 % and 27.2 % of items and the longitudinal one in 0.4 % and 1.1 %; that the NEES-guided scalar leaves the lateral tail at 13.0 % and 17.2 %; and that any single variance factor that fixes the lateral tail adds 10–12 m of unneeded longitudinal margin (Section V-B) `[E01 §5.2 / X2R]`.

""")
note("I", "tightened", "'The measurement on nuScenes': three result bullets into one sentence; every number kept; tag kept with it")
region("**The correction and its first test.**", "**The planner study and its variant.**", r"""**The correction and its first test.** Decision-projected stratified conformal risk control (DP-SCRC) scores the error in the planner's constraint coordinates, fits one conformal-risk-control threshold per stratum of planner-observable features with a count-based fallback, and returns a covariance the planner consumes unchanged, under a scene-level, stratum-marginal, transductive certificate on the audited population (Section IV-C). On three tracker settings it was not significantly above δ in any cell on held-out logs or on transfer, while the pooled single-threshold conformal correction was significantly under-covered on both tracker families `[E01 §5.3]`.

""")
note("I", "tightened", "'The correction and its first test': three bullets into one sentence; claims unchanged")
region("**The planner study and its variant.**", "**A learned predictor.** In a pre-specified study on the nuScenes validation split", r"""**The planner study and its variant.** A pre-specified planner study (NO-GO on a power floor) showed that the certificate did not reach every constraint the planner relied on `[E01 §5.4]`, so we built a planner-matched variant, M\* (Section IV-K). In exploratory development evidence on 840 nuScenes scenes (Section V-D) it was shown above δ in no cell and was less often infeasible than the pooled correction and than the raw covariance, the latter largely by narrowing margins that are mostly too wide on the planner's relied constraints (the in-path lateral cars above are 0.4 % of them).

""")
note("I", "tightened", "'The planner study and its variant': two bullets into the paragraph; wording kept")
rp("3. *DP-SCRC* and its planner-matched variant M\\*. The certificate is scene-level, stratum-marginal and transductive. It is not a per-object, per-constraint or per-decision guarantee (Section IV).",
   "3. *DP-SCRC* and its planner-matched variant M\\*, with a scene-level, stratum-marginal and transductive certificate, not a per-object, per-constraint or per-decision guarantee (Section IV).")
rp("5. *Planner evidence (exploratory) and learned-predictor evidence (pre-specified) on nuScenes* (Sections V-D, V-E). It shows that a per-constraint certificate is not a per-decision one, and that the raw covariance can be too wide as well as too narrow on the planner's population.",
   "5. *Planner evidence (exploratory) and learned-predictor evidence (pre-specified) on nuScenes* (Sections V-D, V-E), showing that a per-constraint certificate is not a per-decision one and that the raw covariance can be too wide as well as too narrow on the planner's population.")
rp("1. *A criterion separated from NEES* for covariances consumed through linearised half-space chance constraints, its transfer to estimate-chosen axes, and the price and non-equivalence of single-knob corrections (Section III).",
   "1. *A criterion separated from NEES* for linearised half-space chance constraints, its transfer to estimate-chosen axes, and the price and non-equivalence of single-knob corrections (Section III).")
rp("2. *A pre-specified measurement on one real stack:* lateral under-coverage and longitudinal over-coverage of the 2 s extrapolated covariance; the NEES-guided scalar misdirects the fix (Section V-B).",
   "2. *A pre-specified measurement on one real stack:* the 2 s extrapolated covariance is laterally under- and longitudinally over-covering, and the NEES-guided scalar misdirects the fix (Section V-B).")
note("I", "tightened", "contributions 1, 2, 3 and 5 shortened (contribution 6 untouched)")

# ---------------------------------------------------------------------------------------------------------------------
# II. Related Work (every citation kept; Mei2024 renamed DixitMei2024)
# ---------------------------------------------------------------------------------------------------------------------
II_NEW = r"""**A. Chance-constrained planning with uncertain obstacles.** Chance-constrained control replaces the probability of violating a linear constraint under Gaussian uncertainty by a margin along the constraint normal, allocating risk across constraints or fixing it per constraint [Blackmore2011; Ono2008], and extends to moving obstacles tracked by a Kalman filter, with the collision region linearised to a half-space [Zhu2019]; the obstacle-covariance form for road vehicles is treated in [DuToit2011; Hardy2013]. Driving-scale planners keep the half-space form with multimodal predictions [Nair2025; Ren2025] and in scenario or risk-allocating MPC [deGroot2025; Mustafa2023]; conformal-region planners tighten the same half-spaces by a non-parametric radius [Lindemann2023]; a second family enforces a Mahalanobis keep-out on the whole covariance [Shah2026; Mohamed2025; Pouria2026]. Other planners consume perception uncertainty [Li2024; Guo2025; Shi2026; Liao2026], and 2026 IEEE journals evaluate uncertainty-aware planners in closed loop without a perception-covariance chance constraint [Zhao2026; Jang2026; HUP2026]. Whether V̂ supports the consumed quantile is assumed, not tested.

""" + II_B + r"""

**C. Assessing covariance consistency.** The NEES/ANEES and NIS χ² tests [BarShalom2001] penalise optimism and pessimism asymmetrically and depend on Gaussianity [Li2002; Li2006], hold only for tuned filters [Chen2024], fail for mixture filters [Ahmed2024] and do not separate bias from scale [Yan2026]; for Σ = [[8, 1], [1, 2]] and P = diag(8, 2) the NEES has the right mean and χ² histogram while the whitened covariance has eigenvalues 0.75 and 1.25, so scalar measures "fail to evaluate matrix-valued conditions" [Forsling2025]. Forecast verification distinguishes calibration notions that do not imply one another [Gneiting2007], proposes directional checks [Ziegel2014], shows that no single pre-rank detects every misspecification [Allen2024] and makes calibration functional-specific [GneitingResin2023].

**D. Conformal prediction and risk control for filters and planners.** Conformal prediction gives finite-sample marginal coverage under exchangeability, per category in its Mondrian form [Vovk2012; Bostrom2020] and with conditional guarantees over richer covariate classes [Gibbs2023], while object-conditional validity is impossible in general [Vovk2012; Lei2014; Barber2021]. Conformal risk control extends it to bounded monotone losses [Angelopoulos2024; Bates2021], including detection losses [Andeol2023]; scarce classes are pooled by clustering [Ding2023], hierarchical data take one score per group [LeeBarberWillett; Dunn2023], and thresholds can be updated online [GibbsCandes2021], which could be layered on our strata `[P02 Relation to known results]`. Training-conditional and high-probability variants [Bates2021; Angelopoulos2025LTT], and training-conditional guarantees where they hold [BianBarber2023], bound the risk of one fitted rule, which the registered test checks empirically; under distribution shift, coverage needs reweighting or degrades [Tibshirani2019; Barber2023]; and items chosen after seeing the data need selection-aware methods [JinCandes2023] and coverage guarantees after selection [Bao2024], which our relied-axis scoring does not have. Conformal regions surround physics-constrained trajectory predictions [Tumu2023]; in robotics, conformal prediction gives sample-efficient safety assurances [Luo2022], its regions around predicted trajectories drive MPC [Lindemann2023; Dixit2023; Cleaveland2024; Lindemann2025], conformal perception error feeds controllers [Yang2023; Zhang2025; DixitMei2024], conformal decision theory controls a decision loss online [Lekeufack2024], and conformal sets tighten chance constraints [DSilva2026; Natraj2026; Vlahakis2024]. Closest to our mechanism, [Weisman2026] inflate Kalman-filter confidence regions by one conformal scalar per horizon (CGKF, the analogue of our pooled baseline B4) and calibrate directional quantiles along fixed random directions with a two-sided maximum-violation score (CQKF); [Marques2024; Marques2026] apply per-partition conformal factors, with learned partitions, to a Gaussian dynamics covariance consumed by a sampling-based planner and show that one global factor fails; [Suganda2026] use Mondrian conformal prediction with group-specific risk in a safety filter; [Su2024] conformalise detection noise inside a tracker. Nearer in form, [Chen2026] learn polyhedral conformal sets, intersections of data-driven half-spaces whose orientations are optimised to the decision loss, with the full-conformal robust-optimisation method F-CROMS [Bao2025] among their baselines; [DSilva2026] tighten each polytopic constraint row with a conformal set; [Cuonzo] calibrate one-sided standardised residuals. In the corpus searched, none calibrates a one-sided tail per constraint normal of a driving tracker's exported Gaussian, with the normal fixed by the planner and the stratum by what it observes, or replays a real tracker's recorded covariance into a planner on real logs `[S02 §5]`.

**E. Decision-aware calibration.** Decision calibration asks that predictions be calibrated for the decisions made from them [Zhao2021; Sahoo2021; Kiyani2025; Tang2026; Noarov2025]; threshold calibration is implied by distribution calibration and implies average calibration, not conversely [Sahoo2021]; action-conditional conformal guarantees condition the tail on the chosen action [Zhu2026]. Our criterion specialises this idea to a Gaussian covariance consumed through half-space chance constraints, with the normal fixed by the planner rather than learned as in [Chen2026]. Planner-centric and planning-aware metrics [Philion2020; IvanovicPavone2022] and control-aware training objectives [McAllister2022] weigh detection, forecasting or a predictor's training by their effect on a downstream planner; calibrated regression [Kuleshov2018], propagated perceptual uncertainty [Ivanovic2022] and its effect on motion plans on real driving data [IvanovicA2024] concern the predictor's own uncertainty; and NEES-based auto-tuning of Kalman filters [Chen2018nees] optimises the whole-vector statistic that Theorem 1 separates from what the planner uses. We instead test the covariance a planner consumes against the quantity it uses.

**F. Closed-loop evaluation of uncertainty-aware planning.** nuPlan [Karnchanachari2024] defines closed-loop non-reactive and reactive scores; [Shah2026] evaluate calibrated predictors in a CC MPC on nuPlan with ground-truth perception and a covariance-scaling sweep, finding that global scaling cannot rescue a miscalibrated covariance; [Jang2026] report both replay modes; robotics studies report violation against ε, freezing and infeasibility [Zhu2019; Mustafa2023; deGroot2025; Serfling2026]; and [Pouria2026] show that calibration of Gaussian predictors, not displacement error, drives MPC success on pedestrian replay, with an MPC consuming confidence ellipses, for which their χ²-type check (ESV) is the matched diagnostic (Proposition 4). Every nuPlan study we found uses ground-truth or noise-injected perception; we replay a real tracker's recorded covariance. Open-loop scores at logged states, such as our decision mode, can disagree with closed-loop behaviour [Dauner2023; Li2024Ego], and demonstrating safety statistically needs far more driving than any study here [KalraPaddock2016].
"""
region("**A. Chance-constrained planning with uncertain obstacles.**", "\n---\n\n## III. Formalisation", II_NEW)
note("II", "tightened", "A, C-F tightened sentence by sentence (B verbatim); every citation and claim kept; Mei2024 -> DixitMei2024 (TODO item 10)")

# ---------------------------------------------------------------------------------------------------------------------
# IV. Method: Fig. 1 pointer, Algorithm 1 sentence (TODO item 1), IV-K cut (detail to Appendix B)
# ---------------------------------------------------------------------------------------------------------------------
rp("DP-SCRC is a post-processor between tracker and planner, fitted offline", "DP-SCRC is a post-processor between tracker and planner (Fig. 1), fitted offline")
note("IV", "pointer", "Fig. 1 cited at first use (TODO item 2)")
rp(" Case (b) is a passing whole-vector test hiding a direction-specific failure; (d) shows that second-moment agreement says nothing about a 1 % tail.", "")
note("III-D", "duplicate removed", "the sentence restating Theorem 1(b) and (d) after the theorem ('a passing whole-vector test hiding a direction-specific failure'; '1 % tail' as in (d))")
rp("Lines 1–9 follow `[E01 §2.4–§2.7, §3.1; HPREP; XLIB axis_candidates]`; lines 10–13 are `fit_hier` and `crc_threshold` `[MLIB; E01 §3.5–§3.6]`; lines 14–17 are Proposition 8.",
   "Lines 1–9 follow the item construction of Section IV-A `[E01 §2.4–§2.7, §3.1; HPREP; XLIB axis_candidates]`; lines 10–13 are the per-stratum fit with fallback of Sections IV-C to IV-E `[MLIB fit_hier, crc_threshold; E01 §3.5–§3.6]`; lines 14–17 are Proposition 8.")
REM4 = blk("**Remark 4 (tuning on the evaluation scenes).**", "(Section VI-A).")
rp(REM4, "A new-scene reading needs every ingredient of the score, the tracker's Q and R included, fitted outside the evaluation scenes (Remark 4, Appendix A).")
CLE0 = blk("If a fitted ĉ ≤ 0, α = max(ĉ, ε)/z with ε = 10⁻³;", "`[P02 PM2 Remark]`.")
rp(CLE0 + " A planner normal", "A non-positive fitted ĉ is floored (Appendix A). A planner normal")
FORS = blk("for Σ = [[8, 1], [1, 2]] and P = diag(8, 2)", "\"fail to evaluate matrix-valued conditions\" [Forsling2025]")
rp(FORS + ".", "a scalar test can pass while the whitened covariance is wrong [Forsling2025] (example in Appendix A).")
note("IV-C, IV-F, II-C", "moved", "Remark 4 (tuning on the evaluation scenes), the remark on a fitted ĉ ≤ 0 (ε = 10⁻³) and the [Forsling2025] example (Σ = [[8, 1], [1, 2]], eigenvalues 0.75, 1.25) moved verbatim to Appendix A beside Remarks 2-3 and Theorem 1(b); one-sentence pointers left")
note("IV-I", "fixed", "TODO item 1: 'Lines 1–9 follow' names its object; code names fit_hier/crc_threshold moved into the tag")

IVK_CONS = blk("**The planner's constraints.** The planner is the chance-constrained speed planner of Section V-D.\n- **Gap.**",
               "- **Tracks considered.** Score ≥ 0.4, within 60 m and not behind the ego.")
IVK_NEW = r"""### K. The planner-matched variant M\*

M\* is DP-SCRC's calibration and deployment (Sections IV-B to IV-F; Algorithm 1, lines 10–17) applied to the constraints a planner enforces instead of the audit population of Section IV-A `[D14 §2; k6_sim_v02; k7_items_v02; k7_fit_v01; c1_fit_v02; ERR E16]`.

**Constraints, items and populations.** For a track and an object axis a, the *gap* is the clearance between the buffered footprints along a, and the chance-constrained speed planner of Section V-D needs gap ≥ margin on some axis. A (track, check time) pair is *enforced* if, at an arm-independent reference margin of 0, some candidate plan satisfies it and an ego held at its position would also satisfy it (definitions in Appendix B). At every decision state (every keyframe of a log except the first and the last, at the logged ego's position and speed) and every calibrated check time (0.5, 1, 1.5 and 2 s), each enforced pair with an annotation at that time gives items: every object axis that separates the pair at the **reference pose**, the logged ego pose at the check time, gives one calibration item U = D/sd, as in Section IV-A, oriented to the side on which it separates. The scored populations keep one item per enforced pair, the **relied axis**: the separating axis with the largest gap at the reference pose. They are P_rel, all relied items; P_near, those with gap ≤ 5 m; P_ip, those of in-path tracks; and P_nip, those of tracks that are not in-path, reported for scope only `[code and plan names: PD7, SD1_7, PD, NIP]`. P_ip is not the in-path audit population of Sections V-B and V-C. Fits are made separately for in-path and not-in-path tracks and for each calibrated check time, and thresholds are cross-fitted over 5 log folds (Algorithm 1-P in Appendix B).

**What the theory covers.** Within a dataset, cross-fitted M\* has the marginal per-stratum bound of Propositions 6–7 for its own-threshold strata, on its calibration items: logs are exchangeable, and the item rule, which may use the logged future pose, is the same in calibration and test. Not covered are the scored relied-axis subset, which is selected by the gap, and Propositions 1 and 3, whose condition (M) fails because the reference pose is the logged future pose; the link from these items to a deployed planner's own relied constraints is not proved (Appendix B).
"""
region("### K. The planner-matched variant M\\*", "\n---\n\n## V. Experiments", IVK_NEW)
note("IV-K", "cut + moved", "the constraint bullets (gap, check times, enforced pairs, tracks considered), the 1.61/0.92 million sentence, the beyond-2 s sentence, Algorithm 1-P and the full 'What the theory covers' moved verbatim to Appendix B; items and populations kept; code population names into a tag")

# ---------------------------------------------------------------------------------------------------------------------
# V-A
# ---------------------------------------------------------------------------------------------------------------------
rp(" " + GT, " The ground-truth filters and counts are in Appendix B.")
note("V-A", "moved", "ground-truth sentence (classes, 28,130 / 725,431 / 2,439 / 6,019) moved verbatim to Appendix B")
rp("**Trackers.** `[E01 §2.3; M-PLAN §2]`\n\n| Setting |",
   "**Trackers.** The three settings are in Table @TRK@ `[E01 §2.3; M-PLAN §2]`.\n\n**Table @TRK@. The three nuScenes tracker settings: tracker, configuration and what was tuned on which data.**\n\n| Setting |")
note("V-A", "fixed", "TODO item 3: the Trackers table gets a caption and the number Table I (all later body tables renumbered)")
rp("so every analysis covers matched true positives only: 63.9 % (val) and 67.4 % (train) of in-path records were paired (counts in Appendix B).",
   "so every analysis covers matched true positives only (pairing rates and counts in Appendix B).")
note("V-A", "duplicate removed", "pairing rates 63.9 % / 67.4 % (stated in Appendix B, 'Records, pairing and items')")
VA_INPATH = blk("**In-path rule and the planner's population.**", "This is the mechanism of the scope gap (Section IV-J).")
rp(VA_INPATH, r"""**In-path rule and the planner's population.** From estimates only, the ego rear-axle pose is extrapolated 0–4 s in 0.5 s steps with a CTRV model from the current and previous keyframe poses; the union of the nine inflated footprints is the corridor, and an object is *in-path* if its box, swept at its estimated constant velocity, intersects it `[E01 §2.5 / XLIB ego_corridor, object_in_path]`. The analysis population (in-path, paired, uncensored items) differs by construction from what a planner considers: 61–63 % of in-path paired tracks at planner decision times are behind the ego and never become the planner's constraints, while the planner relies on tracks within 60 m that are not in-path. This is the mechanism of the scope gap (Section IV-J; Appendix B) `[E01 §2.5 / R11B O2; R11B M1]`.""")
note("V-A", "cut + moved", "in-path paragraph shortened; the full paragraph (K6 planner's 60 m / rear-bumper rule, approximate counting) moved verbatim to Appendix B; 'the K6 planner' no longer in the body")
PRESPEC = blk("**Pre-specification.** Each nuScenes stage was planned in a document whose SHA-256 was fixed", "Operating characteristics, reviews and re-derivations are in Appendix B.")
rp(PRESPEC, "**Pre-specification.** Each nuScenes stage was planned and its plan hashed, with code, inputs and environment listings, before its outcomes were computed; the hashes are self-recorded, so we call the stages *pre-specified*, and only the Argoverse 2 test *registered* (Section V-F1). Operating characteristics, reviews and re-derivations are in Appendix B.")
note("V-A", "tightened", "pre-specification paragraph shortened; its full statement is Appendix B's 'Pre-specification and checks' (SHA-256 named there)")
rp("and one pre-freeze check previewed X2's decision (D06). Details are in Appendix B.", "and one pre-freeze check previewed X2's decision `[D06]`. Details are in Appendix B.")
note("V-A", "internal IDs", "'(D06)' into a tag")

# ---------------------------------------------------------------------------------------------------------------------
# V-B
# ---------------------------------------------------------------------------------------------------------------------
TAB1 = blk("**Table I. X1, 2 s family, in-path cars on val", "| CONSISTENT | 0.67 | 2.6 [1.5, 10.7] |")
rp("\n\n" + TAB1 + "\n", "\n")
note("V-B", "moved", "Table I of v05a (X1's descriptive 2 s cells on val) moved verbatim to Appendix B as Table B1, next to X1's criterion")
rp(X1_OLD, r"""**X1 (discovery; 150 val scenes; plan `ab9b8e05…`).** Its criterion G1 (Appendix B) gave the verdict "NOT SHOWN, in either family" under a 97.5 % band `[E01 §5.1, §3.4 / X1-REP; X1-FWER]`. At the tracker's current output all four eligible car cells were CONSISTENT or OVERCOVERS `[E01 §5.1]`. At 2 s the pattern of Table @B1@ (Appendix B) appeared descriptively: lateral point values above their thresholds, lower band edges not; the car ANEES was 3.18 and 3.52, both OVERCONFIDENT, so NEES asked for more variance in both longitudinal cells, which were already over-covered `[E01 §5.1 / X1R: family_h2s]`.""")
note("V-B", "moved", "X1's G1 definition, Bonferroni band and false-FAILS rate (0.002 vs 0.0390), and '52–83 scenes per lateral cell' moved to Appendix B")
rp(" " + X2_OC + " **Result:** `G1_holds: true, H3_holds: true` `[E01 §5.2 / X2R: G1_X2]` (Tables II, III).",
   " Its operating characteristics are in Appendix B. **Result:** G1 and X2-H3 hold (Tables II, III; Fig. 2) `[E01 §5.2 / X2R: G1_X2: G1_holds true, H3_holds true]`.")
note("V-B", "moved + internal IDs", "X2 pre-freeze false-FAILS rates and power moved verbatim to Appendix B; the file key G1_holds/H3_holds into the tag; Fig. 2 cited")
rp(READ_OLD, r"""**Reading.** (1) *Shape, not scale*: the needed variance factors run in opposite directions (Table III). (2) *Price of one knob* (Proposition 5(b); Fig. 3): 11.61 m and 10.34 m of unneeded longitudinal margin; one scalar over-pays, which does not mean that no scalar can fix the lateral tail `[P5 K3]`. (3) *NEES misdirection* (Theorem 1(c)): the ANEES correctly reports over-confidence, but its scalar leaves the lateral tail at 0.130 and 0.172 while adding 2.72 m and 2.17 m longitudinally `[P5 K4b]`. Items (4)–(7) are in Appendix B. In short, the failure concentrates in moving cars that turn (68 % of the exceedances come from cars turning ≥ 5° over the 2 s), and the all-objects lateral exceedance is below δ (0.039) because 80 % of those items are parked cars.""")
note("V-B", "duplicate removed", "Reading (1)-(3): the variance factors 6.75/0.235/6.56/0.460, the lower bounds 9.81/8.24 m and the ANEES 4.46/3.89 'against 2' repeat Table III (X2 gated steps; number unchanged) and are dropped from the prose; Fig. 3 cited")

# ---------------------------------------------------------------------------------------------------------------------
# V-C: a summary in the body; the result paragraphs of v05a verbatim in Appendix B
# ---------------------------------------------------------------------------------------------------------------------
VC_B4_FULL = blk("**The pooled conformal correction fails on both tracker families.**", "are above DP-SCRC's `[D07 §4]`.")
VC_E2_FULL = blk("**E2: transfer to val.** Pooled val exceedance", "by up to that amount `[R08 m8]`.")
VC_SHAPE_FULL = blk("**The deployable recalibration is a shape correction.**", "`[D07 §3 item 5]`.")
VC_PROPS = blk("*Properties of the inference* (Appendix B):", "(margin ratios below) `[D07 §4]`.")
VC_PROPS_APP = VC_PROPS.replace("*Properties of the inference* (Appendix B):", "*Properties of the inference* (see 'Method-stage inference'):").replace(
    "(margin ratios below)", "(Table VI)")
assert VC_PROPS_APP.count("Appendix B") == 0
VC_NEW = VC_HEAD + r"""

**Design** (Appendix B). *E1* repeats a 5-fold split of train by log 20 times; *E2* fits every method on train and evaluates it on val. A cell (≥ 39 scenes from ≥ 8 logs) is *flagged* if its one-sided simultaneous 95 % lower bound exceeds δ; *a baseline fails* in a cell when, on refit-CV, it is flagged, DP-SCRC is not, and the paired difference is significantly positive, a test whose "DP-SCRC not flagged" leg is easy to meet. The hypotheses are the rows of Table IV `[M-PLAN §6–§10; E01 §3.7]`.

**Outcome (pre-specified decision label GO-B).** DP-SCRC is not significantly above δ and transfers on all three settings, the same practitioner correction (B4) fails where DP-SCRC holds on both tracker families, and the course-change layer is inconclusive on the confirmatory tracker `[D07 preamble; E01 §5.3 / MDEC: METHOD_DECISION "GO-B"; K5a_practitioner_on_T1_and_T3 ["B4"]]`. A separate results review reproduced the pipeline with its own code (Appendix B).

""" + TAB4 + r"""

**Results** (full text in Appendix B). On held-out logs (E1; Table V; Fig. 4), DP-SCRC sits at 0.042–0.049 in every car row and is flagged in no E1 cell on any setting, under either inference, at any horizon, or under any of the 12 sensitivities `[E01 §5.3; D07 §2]`. B4 fails on both tracker families, in opposite directions: on T1 in four car lateral cells (foreknown from X2), and on T3, where it shrinks a far too wide raw covariance by one factor, in car 20–40 m longitudinal straight (E 0.104, refit-CV lower bound 0.054); one global threshold cannot follow a shape that differs by axis and condition `[E01 §5.3, §6, §7 item 4 / MDEC: per_tracker.*.HM2.B4; R08]`. The deployable recalibration is a shape correction (Fig. 5): on T1, car < 20 m, the multipliers on the projected SD (nominal 1.645) are 6.97 lateral turning, 3.06 lateral straight, 0.69 lateral static and 0.38 longitudinal static, while on T3 91 of the 96 multipliers are below 1 `[E01 §5.3 / MR-T1, MR-T3: E2_h2s.fit_on_all_train.Mstar]`. On val (E2; Fig. 6), none of the 10, 9 and 10 cells is flagged and the pooled exceedance is 0.043, 0.044 and 0.038 `[E01 §5.3 / MDEC: per_tracker.*.pooled_val]`; no val or pooled cell is flagged at 1, 2 or 4 s (E4; Fig. 7). B3 and B6c are dominated by construction and B9 certifies a stronger event; the non-dominated comparisons, B6 and B7, go against DP-SCRC on T3 (Table VI) `[D07 §4]`.

""" + TAB5 + "\n\n" + TAB6 + "\n\n"
region(VC_HEAD, "### D. Planner study on nuScenes (exploratory development evidence)", VC_NEW)
note("V-C", "cut + moved", "design, outcome and results summarised in three paragraphs; the full design paragraph, the E1, B4, E2, shape, 'what the comparisons can show' and HM3 paragraphs and the R08 reproduction sentence moved verbatim to Appendix B ('Method-stage results in full'); decision-file keys into the tag")
note("V-C", "pointers", "Figs. 4-7 and Table VI (margin ratios; number unchanged; TODO item 2) cited in order of appearance")

# ---------------------------------------------------------------------------------------------------------------------
# V-D: a summary in the body; the v05a text verbatim in Appendix B
# ---------------------------------------------------------------------------------------------------------------------
VD_FULL = blk("**Harness.** A real tracker's recorded covariance (T1 or T3) is replayed", "Section V-F6 states what the confirmation can and cannot detect.")
assert VD_FULL.count("(Appendix B)") == 2
VD_FULL_APP = VD_FULL.replace("(Appendix B)", "(below)").replace("**Results (Table VII).**", "**Results (Table @B2@).**")
VD_CAP = r"""**Table VII. K8 (nuScenes development, decision mode), per arm and tracker.** Valid: not shown above δ on every population; pooled exceedance on P_rel / P_near / P_ip; flagged P_rel cells; infeasible-decision rate; V2 and V2_viol on P_rel; mean lateral / longitudinal margin (m) on the arm-independent calibration items; Z0 is margin 0. `[K8T]`"""
VD_NEW = "### D. Planner study on nuScenes (exploratory development evidence)\n\n" + K8TAG + r"""

**Design** (full text in Appendix B). A real tracker's recorded covariance (T1 or T3) is replayed from the logged ego's state into the chance-constrained speed planner of Section IV-K (32 accelerate-then-brake candidates and an emergency stop). Every comparison is made in *decision mode*: open loop, one decision per keyframe from the logged state, identical across arms and not executed; loop mode (non-reactive replay [Karnchanachari2024]) is descriptive `[D14 §2; ERR E16]`. A first, pre-specified study, K6, fitted DP-SCRC on the audit population, ended NO-GO on a power floor and exposed the scope gap of Section IV-J `[E01 §5.4, §7; K6R: populations.SD2_not_in_path]`. The second, K8, fits M\* (Section IV-K) on 840 scenes (68 logs; 32,065 decisions per arm) and is exploratory: nothing is gated on nuScenes `[K8: stamp; D14; K8: decide.*.scenes, logs, counts]`. The comparators are B0, B1, B3, B4, B6 and B9 (Section IV-H) and RETUNED [Shah2026; Mustafa2023], the least conservative point of a 21-point curve of B0 whose pooled exceedance is ≤ δ.

**Results (Table @B2@ in Appendix B; Fig. 8).** M\* is shown above δ in no cell, family cell or pooled cell of P_rel, P_near or P_ip, on either tracker (one-sided simultaneous 0.95) `[K8: decide.*.hypotheses, validity_by_arm.Mstar]`. The raw covariance is mostly too wide on this population (the in-path lateral cars of Section V-B are 0.4 % of relied items `[R19 §3]`), so M\* mostly narrows margins: it is less often infeasible than B4 (paired −0.084 and −0.047) and than B0, at a cost in ground-truth violations on T3 (V2_viol) `[K8T; R16 M1]`. The comparators not shown above δ (B3 on T1; B0 and B3 on T3) are infeasible in most decisions. Against B6 the course-change strata buy nothing on T3 (M\* − B6 = −0.005 [−0.016, +0.005]; Form B of Section V-F5 holds there only because B6 is shown above δ) and pay on T1 (−0.062) `[K8: paired_vs_Mstar.infeasible_rate.B6; ERR E12]`. V2, the share of decisions with an exceeded relied constraint at any of the four check times, is 0.358 and 0.351 for M\*, about 0.05 above the per-track reference 1 − 0.95^{n_tracks} = 0.308 at 8.35 tracks; the trajectory-level variant M\*J brings it to 0.048 and 0.049, at +0.307 and +0.393 in infeasible-decision rate `[K8: V2.PD7_primary.Mstar; JN]`.

**Reading.** K8 is transductive development evidence (fits on all 850 scenes, on which M\* was developed; T1's Q tuned on nuScenes validation; our own gates), reproduced by a Linux replicate and a separate-code review (Appendix B). Section V-F's rules were set on it; Section V-F6 states what the confirmation can and cannot detect.


"""
TAB7_APP = VD_CAP.replace("**Table VII. K8", "**Table @B2@. K8") + "\n\n" + TAB7_ROWS
region("### D. Planner study on nuScenes (exploratory development evidence)", "### E. A learned predictor: Trajectron++ on nuScenes", VD_NEW)
note("V-D", "cut + moved", "harness, K6, data, rules, arms, results bullets, per-decision bullets and reading summarised in three paragraphs; the whole v05a text of V-D (except its table) moved verbatim to Appendix B ('The planner study K8 in full'), with its two '(Appendix B)' pointers read '(below)'")
note("V-D", "pointer + caption + moved", "Fig. 8 cited (TODO item 2); Table VII of v05a (K8 per arm and tracker) moved verbatim to Appendix B as Table B2, after the full K8 text; its column bullets into one caption sentence (TODO item 4); K8 defined as 'the second' planner study")

# ---------------------------------------------------------------------------------------------------------------------
# V-E: a summary in the body; the v05a text verbatim in Appendix B
# ---------------------------------------------------------------------------------------------------------------------
VE_A = blk("**Design.** A deployed stack would use a learned trajectory predictor", "+0.032 (0.027) `[J: pooled_stats.paired]`.")
VE_B = blk("**Review and scope.** A results review with its own code", "- **Scope.** This is development-side evidence on 18 log clusters, with no planner outcome.")
assert "**Table VIII." not in VE_A and "**Table VIII." not in VE_B
VE_FULL = VE_A.replace("**Results (Table VIII; all three hypotheses", "**Results (Table @B3@; all three hypotheses") + "\n\n" + VE_B
assert "@B3@" in VE_FULL
VE_NEW = "### E. A learned predictor: Trajectron++ on nuScenes (pre-specified, frozen, reviewed)\n\n" + D17TAG + r"""

**Design** (full text in Appendix B). In a plan frozen on 4 Nov 2026 with 26 bound files, before its analysis ran, Trajectron++ [Salzmann2020] (the authors' `int_ee` checkpoint, trained on the 700 nuScenes training scenes, without a map) predicts on the validation split (150 scenes, 18 logs) from T1's and T3's histories, and each prediction is scored at 2 s along K8's relied constraints (Section IV-K), which are those of the tracker-fed planner; DP-SCRC is cross-fitted on scene folds and compared with B4 and B3 `[D17 l. 72–278; J: trackers.*.primary_v2.populations]`.

**Results (Table @B3@ in Appendix B; all three hypotheses held under all six tracker–seed runs).** The raw covariance is over-confident in scale (pooled P_rel exceedance 0.135 and 0.125), and NEES sees it directly (record-level ANEES 16.6 and 10.2 against 2): this is not a case where NEES misleads `[J: validity.TPP_B0; A6.TPP]`. DP-SCRC leaves no evaluated P_rel cell flagged, but only 3 cells are power-qualified, so the result reads "not shown above δ in the evaluated cells"; one pooled multiplier (B4) nearly suffices `[J: validity.TPP_Mstar; R19 l. 47, 113, §5]`. Ground-truth histories remove about half the excess `[J: pooled_stats.paired]`. A results review with its own code reproduced every point estimate and found that records with only two tracker states stay above δ after correction, so the Argoverse 2 study stratifies the predictor's calibration by history length (H9, descriptive) `[R19]`. This is development-side evidence on 18 log clusters, with no planner outcome.

"""
region("### E. A learned predictor: Trajectron++ on nuScenes", "### F. External confirmation on Argoverse 2", VE_NEW)
note("V-E", "cut + moved", "design and results summarised in two paragraphs; the whole v05a text of V-E (except its table) moved verbatim to Appendix B ('Trajectron++ in full')")

# ---------------------------------------------------------------------------------------------------------------------
# V-F: V-F1 to V-F6 summarised (their v05a text verbatim in Appendix E); V-F7 tightened (Appendix F has every item);
# Table IX moved to V-F2
# ---------------------------------------------------------------------------------------------------------------------
VF_FULL = blk("**1. Purpose and registration.** Sections V-B to V-E used one dataset", "  - superiority over methods outside K.")
assert VF_FULL.count("Details are in Appendix E") == 1 and VF_FULL.count("which the freeze binds (Appendix E)") == 1
assert VF_FULL.count("are in Table IX.") == 1
VF_FULL_APP = VF_FULL.replace("Details are in Appendix E", "Details are below").replace("which the freeze binds (Appendix E)", "which the freeze binds (below)").replace(
    "are in Table IX.", "are in Table @F5@ (Appendix F).").replace("the power projection S22.", "the power projection `[S22]`.")
assert "`[S22]`" in VF_FULL_APP
assert VF_FULL_APP.count(VF_GO) == 1 and VF_FULL_APP.endswith(VF_GO)
VF_FULL_APP = VF_FULL_APP.replace(VF_GO, "- **What a GO would and would not show:** as listed in Section V-F6 (kept there verbatim).")
RUN_OLD = blk("- **The run.** The frozen analysis ran once (7 Nov 2026, B = 40,000).", "Its run-log lines and output hashes are in Appendix F.")
VF7_GO = VF_VERDICT_BLOCK.replace("- **The outcome.** No condition failed and no input was missing on either tracker.",
                                  "- **The outcome.** No condition failed and no input was missing on either tracker (Table X).").replace(
    RUN_OLD, "- **The run.** The frozen analysis ran once (7 Nov 2026, B = 40,000) and passed the completion check of plan §9 (Appendix F(a)).")
assert RUN_OLD not in VF7_GO
assert VF7_GO != VF_VERDICT_BLOCK and VERDICT in VF7_GO
VF_NEW = "### F. External confirmation on Argoverse 2 (registered, run once)\n\n" + VFTAG + r"""

**1. Purpose and registration.** Sections V-B to V-E used one dataset, and V-D is exploratory. This study tests M\* once, on 375 Argoverse 2 logs, under a plan frozen on 6 Nov 2026 at 20:08:13 UTC and registered on OSF under embargo at 20:31 UTC (https://osf.io/v8qfk/), before any outcome existed; the plan binds 354 files by hash, ground-truth reads after the decision time need a deposit record naming the registration, and every guarded run is logged in a hash chain `[C1-PLAN §8.2–§8.6, §11.3; D16 Choices 61, 66]`. Appendix E gives the protocol and Sections V-F1 to V-F6 in full. M\* is re-fitted within Argoverse 2, so the test checks what theory (Section IV-K) does not cover: the scored relied-axis subset, pooled and fallback cells, the risk of the fitted rule, the power floors and operability on new data. Whether nuScenes thresholds transfer is tested by H4 and H7, and whether the diagnosis of Section V-B replicates by H8.

**2. Data, detector and trackers.** The logs are 225 training logs of the Argoverse 2 Sensor dataset [Argoverse2], held out from the detector by a seeded permutation, and the 150 validation logs; a log is one segment of about 15 s, comparable to a nuScenes scene. The detector, CenterPoint [Yin2021] in the LT3D code base [Peri2022], was trained by us on the other 475 training logs, and nothing was selected on the 375; its 26-class AP at 50 m is 0.425 (validation) and 0.415 (held-out), against 0.469 for the public checkpoint, and its bicyclist AP is 0.403, against 0.543 `[C1-PLAN §1.1, §1.2]`. T1 and T3 keep their nuScenes parameters and run at 2 Hz; AB3DMOT [Weng2020] is a descriptive third tracker (scores in Appendix F, Table @F5@).

**3. Outcome-blind preparation** [KleinRoodman2005; MacCoun2015; Nosek2018]. Everything not needing an annotation position after the decision time (stage A: states, items, counts, folds and H8's null E⁰) was built before the freeze; the scoring (stage B) ran only after the registration; and the 8 derived ground-truth files were quarantined before the freeze. What was seen before the freeze is listed in a freeze-time record that the freeze binds (Appendix E).

**4. Design.** The populations, decision mode and M\* are those of Sections IV-K and V-D, cross-fitted on 5 folds of 75 logs. The comparators K = {B0, B1, B3, B4, B6, B9, RETUNED} were fixed on development; B4 is the analogue of a per-horizon conformal inflation (CGKF [Weisman2026]) and of a single global factor [Marques2024]. Because B3's margin is at least M\*'s on every item (Proposition 9), Form B adds little to the screen if the comparators not shown above δ are those of development ({B3} on T1; {B0, B3} on T3) `[C1-PLAN §2, §4]`. The secondary claims, H2 to H4, H6a, H6b, H7, H8 and H10, are defined in Appendix E and listed with what each tests in Section V-F7.

**5. Statistics and the GO rule** `[C1-PLAN §6.1–§6.5, §9]`. The log is the unit of the estimand and of the bootstrap (B = 40,000). A cell is evaluable with ≥ 39 logs and power-qualified if a planted exceedance of 0.15 in it alone would be flagged with probability ≥ 0.80. M\* passes the screen on a tracker if, in each of P_rel, P_near and P_ip, no cell, power-family cell or pooled cell is flagged, the floors hold (≥ 6 power-qualified cells on P_rel and P_near, ≥ 1 evaluable P_ip cell) and HK1c holds (the pooled upper bound at 0.995 is ≤ δ + 0.03). A comparator leaves the comparison set V_t only on familywise evidence above δ; Form B holds if the screen holds and M\* is less often infeasible than every member of V_t. H1, Form B on T1 and T3, is an intersection-union test [Berger1982] at one-sided 0.025 nominal, and **GO** means that H1 holds with every input present and of verified provenance. Family S = {H2, H3, H4, H6b, H10} is tested by Holm at 0.025 only if H1 holds [Holm1979; DmitrienkoTamhane2007]; H8 has its own 0.025. The verdict of record is the first completed run.

**6. What the design can detect, and what a GO would mean** `[C1-PLAN §0, §6.6, §6.9, §7]`. Power is a pre-data property and licenses no "at most" statement: a cell at 0.10 can pass with probability near one minus its power at 0.10. The post-data bounds, HK1c's and M\*'s simultaneous cell bounds U_max, are approximate (Appendix E).
""" + VF_GO + "\n\n" + VF_R7TAG + "\n\n" + VF7_GO + "\n\n" + TABX + r"""

**What the screen can and cannot show** (Fig. 9). Median per-cell power at a planted exceedance of 0.10 is 0.61 and 0.58 on P_rel, 0.12 on P_near and about 0.22 on P_ip, so a cell at 0.10 would usually pass, and the largest approximate simultaneous upper bound is 0.157 (T3, P_ip): exceedances of that size cannot be excluded in individual cells """ + VF_SCREEN_TAGS + r""".

**The comparison set and Form B.** Every comparator except B3 on T1 and B0 and B3 on T3 was shown above δ at one-sided 0.99861 (Appendix F), and M\* was less often infeasible than each remaining one (M\* − B3 = −0.783 on T1; M\* − B0 = −0.611 and M\* − B3 = −0.694 on T3). These comparisons carry little evidence of operability, because B3's margin is at least M\*'s on every item and B3 and T3's B0 are infeasible in most decisions (Table XII); this is the qualifier in the verdict sentence, anticipated in Section V-F4 """ + VF_FORMB_TAG + r""".

**The informative comparison, B6** (M\* without the course-change strata), was shown above δ in five P_rel cells on each tracker and left V_t, yet M\* was *more* often infeasible than B6, by +0.018 [0.009, 0.027] on T3 and +0.021 [0.003, 0.039] on T1 (two-sided 95 %; Fig. 10; −0.005 on T3 on development): the strata bought the cells in which B6 was shown above δ and M\* was not, not operability `[CSV: k8_within_lt3d_t*_decide_paired.csv]`.

""" + r"""

**Table XII. Per arm and tracker on Argoverse 2** (decision mode): the screen of Table X; pooled exceedance per population; flagged P_rel cells; infeasible-decision rate; V2 with its per-track reference; V2_viol; mean margins on each arm's own relied pairs (item sets differ by arm).

""" + TAB12_ROWS + "\n\n" + TAB12_SRC + r"""

**Reading Table XII** (descriptive). Every comparator infeasible in fewer than half of decisions was shown above δ, and the raw covariance is again mostly too wide. About one decision in two has some relied constraint exceeded (V2 0.491 and 0.496 for M\*), because decisions hold 13.07 tracks against 8.35 on development; the excess over the per-track reference (0.441, against 0.308) is about 0.05 on both data sets `[C1A: k8.within_lt3d.t*.V2.PD7_primary.Mstar]`.

""" + r"""

**The secondary claims** (Table XIII). H2 is confirmed (M\* − B4 = −0.016, UB^0.975 0.005, on T1; −0.069, UB −0.054, on T3), which bounds a price, not superiority. Holm then stops, because H6b's p (0.0199, from 200 refit replicates) exceeds its level of 0.00625, so H10, H3 and H4 are not confirmed whatever their p-values. The nuScenes-fitted thresholds were not supported: with them M\* was shown above δ on both trackers (H4), as was the method stage's M\* (H7); the procedure re-fitted on new data passed (H1, H6a), the thresholds did not carry over. H8 holds: on T1 under the raw covariance the in-path car lateral 20–40 m cell fails both versions (0.214 [0.122, 0.306] against E⁰ = 0.090; truth-oriented 0.144 [0.068, 0.220]) and the < 20 m cell the primary one (0.147); outside H8's definition the 20–40 m longitudinal cell also fails (0.158), which the nuScenes diagnosis did not show.

**Table XIII. Claim statuses** (family S by Holm at 0.025, gated on H1, p = (k + 1)/(B + 1); H6a and H7 no-flag statements; H8 family P, at its own 0.025).

""" + TAB13_ROWS + r"""

`[C1D: family_S; claims_status; hypotheses.*]`

**Descriptive results** (Appendix F; none is a claim). On AB3DMOT the screen is not met (pooled P_rel E 0.061, lower bound 0.057; infeasible in 0.891 of decisions); the three 150-log routes fail the P_near floor (1 to 3 power-qualified cells against 6); Form A is not met on T1; Trajectron++ (H9) misses its floor (2 cells against 6); loop mode was not run; and Q1 (QCNet) was not tested.

**The independent results review** (Appendix F(g)) found the run log intact (96 of 96 checks) and reproduced the analysis with separate code (108,059 of 108,109 comparisons agree, none disagrees); H1 held with the same V_t in all 20 alternative seed sets. """ + VF_R21PEND + r""" It does not re-derive H6a, H6b, H7, H8, H9, H10 or Form A.

**8. Deviations.** After the freeze, three events were logged before the affected step was repeated: the launcher's shell altered the commands' Windows paths, so 14 processes stopped before any guard or input; deviation D-1 wrote one argument token, an interpreter path, with backslashes in two environment checks; and an outcome-free tool's missing output folder was created and the tool rerun. Two transfer runs were also started by hand with their frozen commands. No rule, input, seed or analysis changed (Appendix E) `[DEV-LOG; D16 Choices 67–69]`.
"""
region("### F. External confirmation on Argoverse 2 (registered, run once)", "\n---\n\n## VI. Limitations", VF_NEW)
note("V-F1 to V-F6", "cut + moved", "summarised (registration, data and detector numbers, preparation, comparators and secondary claims, statistics and GO rule, what a GO would and would not show verbatim); the whole v05a text of V-F1 to V-F6 moved verbatim to Appendix E, with 'Details are in Appendix E' and '(Appendix E)' read 'below'; 'the power projection S22' only in Appendix E")
note("V-F4", "duplicate removed", "the one-line definitions of the secondary claims (H2: price against B4 at most 0.03; H3; H4; H6a, H6b, H7; H8; H10) repeat the 'What it tests' column of Table IX and the full V-F4 text in Appendix E; a pointer is left")
note("V-F2", "moved", "Table IX of v05a (tracker scores on the 375 logs) moved verbatim from the end of V-F7 to Appendix F(h) as Table F5, beside its discussion; V-F2 points to it")
H_OLD = blk("**(h) The trackers (Table IX).**", "HOTA, with its tuned score threshold, is the fairer summary for it.")
rp(H_OLD, H_OLD.replace("**(h) The trackers (Table IX).**", "**(h) The trackers (Table @F5@).**").replace(
    "The tracker scores are Table IX (Section V-F7).", "The tracker scores are in Table @F5@.") + "\n\n" + TAB9.replace(
    "**Table IX. Tracker scores on the 375 logs**", "**Table @F5@. Tracker scores on the 375 logs**"))
note("V-F7", "tightened", "verdict block, verdict sentence and the sentence after it verbatim; screen limits, Form B, B6, the reading of Table VIII (old XII), secondary claims, descriptive results and the review as short paragraphs; every number dropped here is in Appendix F or in Tables VII-IX; Table IX (old XIII) placed after the claims it lists")
note("V-F7", "internal IDs", "'(R21)' -> 'The independent results review' (Appendix F(g)); V^J left to Appendix F")
note("V-F8", "tightened", "deviation bullets into one paragraph; 14, D-1 and the hand-started runs kept")

# ---------------------------------------------------------------------------------------------------------------------
# VI. Limitations (VI-A and VI-E verbatim; B-D, F, G tightened)
# ---------------------------------------------------------------------------------------------------------------------
VI_NEW = r"""## VI. Limitations

This section collects the caveats that the method and results sections state only in part.

""" + VIA + r"""

**B. What the certificates cover.** Neither certificate is per object, per decision, closed loop or in fallback strata (Sections IV-C to IV-K); on nuScenes about one decision in three keeps an exceeded relied constraint (V2 0.35–0.36), and the trajectory-level variant is costly. The audit certificate holds on matched true positives still observable at the horizon, along the separating object axes, and its "new scene" reading (Remark 4) fails for T1 and T2, whose noise was fitted on val or trainval, with all settings' association selected on val. M\*'s is built at the logged ego pose, outside Propositions 1 and 3, fitted on all separating axes and scored on the relied one, on a proxy population shared by all arms; a population at the planner's predicted pose was not run.

**C. Data, detectors, trackers and predictors.** Two datasets, with one detector architecture trained separately for each (in-sample on nuScenes train, where T1's Q was tuned on val); three nuScenes settings that share detections and association, hence not independent trackers; "lateral" as the tracked box's axis (median heading error of T1-only records about 40°, against about 1° on T3 `[E01 §5.4; R11B O1]`); Argoverse 2 trackers at their nuScenes parameters at 2 Hz, with thin two-wheeler cells; a constructed open-loop extrapolation as the audited predictor; and Trajectron++ from the authors' checkpoint without a map, through our online adaptation, with log-splitting scene folds, on the tracker-fed planner's items and with 3 power-qualified cells. Other detectors, cities or a deployed stack are not shown.

**D. Evaluation design.** Decision mode is open loop at logged states, and open-loop scores can disagree with closed-loop behaviour [Dauner2023; Li2024Ego]; loop mode replays non-reactive agents [Karnchanachari2024] and ranks no arm. The method-stage tests make "DP-SCRC not flagged" easy, catch an exceedance of about 0.12 in a val turning cell 23 % of the time and rest B4's failure on T3 on one cell; DP-SCRC is not the tightest method (B6 and B7 use less margin on T3). K6 is a pre-specified NO-GO; K8 is exploratory and set Section V-F's rules. The nuScenes hashes are self-recorded, one pre-freeze check previewed X2's decision `[D06]`, and reviews were within the project; only the K6 power-rule audit is an independent re-implementation.

""" + VIE + r"""

**F. Not claimed.** For the nuScenes tracker study: miscalibration of the tracker's current-time output, a uniform lateral failure, that only the decision projection reveals the problem, or that no scalar can fix it. For DP-SCRC: that course-change strata are needed or unneeded, that methods that did not fail are adequate, that DP-SCRC is the tightest method, or margin "savings" without naming the dominated references `[D07 §4]`. For the planner studies: any safety consequence or closed-loop guarantee, a per-decision guarantee, validity at the planner's own predicted pose, or a ranking from loop mode. For Trajectron++: that it is calibrated or certified. For Argoverse 2: validity in non-evaluable cells, along the objects' true axes or outside the four groups; anything about the test split; that no early look at the annotations was technically possible; anything beyond Section V-F6.

**G. Found after the registered run** (Section V-F7). The strata bought no operability against B6 (+0.018 and +0.021), itself shown above δ; the nuScenes-fitted thresholds did not carry over (H4, H7), mostly in longitudinal cells, so M\* has to be re-fitted for each deployment; the GO covers the two registered trackers only (AB3DMOT's pooled relied-constraint cell is shown above δ, 0.061, and the three 150-log routes fail the P_near floor); loop mode was not run; H9's frozen "seed-robust" label is stricter than the plan's wording; and the independent results review does not re-derive H6a, H6b, H7, H8, H9, H10 or Form A.
"""
region("## VI. Limitations", "\n---\n\n## VII. Conclusion", VI_NEW)
note("VI", "tightened", "VI-B, C, D, F, G: bullets into prose, every caveat kept (VI-B also names fallback strata via Section IV-E); VI-A and VI-E verbatim; '(D06)' into a tag; 'R21' -> 'the independent results review'")

# ---------------------------------------------------------------------------------------------------------------------
# Appendix A: provenance IDs in running text into tags (TODO item 5)
# ---------------------------------------------------------------------------------------------------------------------
LMAP = blk("Label map (v01 label → v02 label; source):", "PM3 → Proposition 9 (P02).")
rp(LMAP + " Outlines, to be expanded from the sources:", "`[" + LMAP + "]` Outlines, to be expanded from the sources:")
rp("with I_{k(i)}-measurable weights (P01-A4 m1); non-sufficiency by the fair-label example (check T1ii).",
   "with I_{k(i)}-measurable weights `[P01-A4 m1]`; non-sufficiency by the fair-label example `[check T1ii]`.")
rp("*Proposition 2.* dr/dρ̂ = (1 − κ)/(κρ̂ + 1)² (check P1).", "*Proposition 2.* dr/dρ̂ = (1 − κ)/(κρ̂ + 1)² `[check P1]`.")
rp("*Proposition 3.* R04 §4–§6 as carried into P01-A4; Monte Carlo 0.0503.",
   "*Proposition 3.* As in the full statement below; Monte Carlo 0.0503 `[R04 §4–§6 as carried into P01-A4]`.")
rp("*Remark 2.* R04 counter-example (0.315 against 0.175).", "*Remark 2.* A fixed-truth counter-example (0.315 against 0.175) `[R04]`.")
rp("heavier tails than the Gaussian at δ ≤ 0.01; checks T2a, T2b2, T2d (`10_PROOFS/checks/p01_verify_v03_results.json`, ALL_PASS).",
   "heavier tails than the Gaussian at δ ≤ 0.01 `[checks T2a, T2b2, T2d: 10_PROOFS/checks/p01_verify_v03_results.json, ALL_PASS]`.")
rp("(c) by contradiction on the weighted sum (P01-A3 §A).", "(c) by contradiction on the weighted sum `[P01-A3 §A]`.")
rp("*Theorem 2.* Direct evaluation (check T4c).", "*Theorem 2.* Direct evaluation `[check T4c]`.")
rp("hence exchangeable with the test scene (P01 Lemma 4; the conditioning of [Vovk2012, Prop. 3]);",
   "hence exchangeable with the test scene by the conditioning of [Vovk2012, Prop. 3] `[P01 Lemma 4]`;")
rp("the infimum is attained at an observed score (P02 PM1 steps 1–4; check T5).", "the infimum is attained at an observed score `[P02 PM1 steps 1–4; check T5]`.")
rp("*Remark 4.* P01-A4 Prop. B (B1)–(B3).", "*Remark 4.* As in its source `[P01-A4 Prop. B (B1)–(B3)]`.")
rp("which is δ/(2 − δ) at n + 1 = 2/δ (P01-A3 §A).", "which is δ/(2 − δ) at n + 1 = 2/δ `[P01-A3 §A]`.")
put_before("*Proposition 3, full statement (Section III-C).*", REM4 + "\n\n*The deployable covariance when ĉ ≤ 0 (Section IV-F).* " + CLE0 + "\n\n")
rp("(d) e = (T₁, T₂)/√3 with independent T_i ~ t₃:", "A published example of (b)'s kind: " + FORS + ".\n(d) e = (T₁, T₂)/√3 with independent T_i ~ t₃:")
note("App. A", "internal IDs", "label map (v01 -> v02 with P01/P02 sources) and every source/check reference of the outlines put into backtick tags; text otherwise unchanged")

# ---------------------------------------------------------------------------------------------------------------------
# Appendix B: material moved from IV-K and V-A to V-E; internal IDs
# ---------------------------------------------------------------------------------------------------------------------
rp("the pre-freeze OC, and the deviation logs D06 and D08.", "the pre-freeze OC, and the two deviation logs `[D06; D08]`.")
rp("**Disclosure (D06):** one pre-freeze synthetic test", "**Disclosure:** one pre-freeze synthetic test")
rp("found the reading sound after errata E8–E14; later checks added E15 and E16 `[R16; ERR]`.",
   "found the reading sound after seven errata; later checks added two more `[R16; ERR E8–E14, E15, E16]`.")
rp("The 12 sensitivities are listed in Appendix B.", "The 12 sensitivities are listed above.")
note("App. B", "internal IDs", "D06/D08 and the errata numbers E8-E16 into tags; the self-pointer 'listed in Appendix B' inside Appendix B reads 'listed above'")

X1_G1_APP = X1_G1.replace("a NEES condition (Appendix B);", "a NEES condition (above);")
assert X1_G1_APP != X1_G1
VC_DESIGN_APP = VC_DESIGN.replace("Operating characteristics are in Appendix B.", "Operating characteristics follow.").replace(
    "and the decision rule is in Appendix B", "and the decision rule is given above")
assert VC_DESIGN_APP.count("Appendix B") == 0, VC_DESIGN_APP
put_before("**Records, pairing and items.**", "**Ground truth (Section V-A).** " + GT + "\n\n" + VA_INPATH.replace(
    "**In-path rule and the planner's population.**", "**In-path rule and the planner's population, in full (Section V-A).**") + "\n\n")
put_before("**Reading of X2, continued (Section V-B).**",
           "**X1 and X2: criteria and operating characteristics (Section V-B).** *X1:* " + X1_G1_APP +
           " Its 2 s lateral cells had 52–83 scenes each `[E01 §5.1 / X1R: family_h2s]`. *X2:* " + X2_OC + "\n\n"
           + TAB1.replace("**Table I. X1, 2 s family", "**Table @B1@. X1, 2 s family") + "\n\n")
put_before("**Method-stage operating characteristics (Section V-C).**",
           "**Method-stage design (Section V-C).** " + VC_DESIGN_APP + "\n\n")
put_before("**E4, E5 and deviations.**",
           "**Method-stage results in full (Section V-C).**\n\n" + VC_E1 + "\n\n" + VC_B4_FULL + "\n\n" + VC_E2_FULL + "\n\n" + VC_SHAPE_FULL
           + "\n\n" + VC_PROPS_APP + "\n\n" + VC_HM3 + "\n\n" + VC_R08 + "\n\n")
IVK_APP = ("*From Section IV-K.*\n\n**M\\*: the planner's constraints, fits and Algorithm 1-P (Section IV-K).**\n\n" + IVK_CONS + "\n\n" + IVK_161 + " "
           + IVK_STEPS + "\n\n" + ALG1P + "\n\n" + THEORY.replace("**What the theory covers.**", "**What the theory covers, in full (Section IV-K).**") + "\n\n")
put_before("*From Section V-D.*", IVK_APP)
rp("*From Section V-D.*\n", "*From Section V-D.*\n\n**The planner study K8 in full (Section V-D).**\n\n" + VD_FULL_APP + "\n\n" + TAB7_APP + "\n\n")
put_before("**C. Full per-stratum tables.**", "*From Section V-E.*\n\n**Trajectron++ in full (Section V-E).**\n\n" + VE_FULL + "\n\n"
           + TAB8.replace("**Table VIII. Trajectron++", "**Table @B3@. Trajectron++") + "\n\n")
note("V-E", "moved", "Table VIII of v05a (Trajectron++ results) moved verbatim to Appendix B as Table B3, after the full Trajectron++ text")
note("App. B", "moved in", "ground truth and the full in-path paragraph (V-A); X1 G1/band and X2 OC (V-B); method-stage design and results in full (V-C); the planner's constraints, fits, Algorithm 1-P and the full theory scope (IV-K); K8 in full (V-D); Trajectron++ in full (V-E)")

# ---------------------------------------------------------------------------------------------------------------------
# Appendix C
# ---------------------------------------------------------------------------------------------------------------------
rp("(scene-level E; simultaneous one-sided bounds, not bias-corrected, R08 m8)", "(scene-level E; simultaneous one-sided bounds, not bias-corrected `[R08 m8]`)")
note("App. C", "internal IDs", "'R08 m8' into a tag")

# ---------------------------------------------------------------------------------------------------------------------
# Appendix E: Sections V-F1 to V-F6 of v05a in full
# ---------------------------------------------------------------------------------------------------------------------
put_before("**F. Argoverse 2: full results of the registered test**",
           "*Sections V-F1 to V-F6 in full (the text of v05a; the body gives a summary).*\n\n" + VF_FULL_APP + "\n\n")
note("App. E", "moved in", "the v05a text of Sections V-F1 to V-F6 verbatim (two self-pointers to Appendix E read 'below'; 'S22' put into a tag; the pointer to Table IX reads Table F5)")

# ---------------------------------------------------------------------------------------------------------------------
# Appendix F: internal IDs (TODO item 5)
# ---------------------------------------------------------------------------------------------------------------------
rp("Populations: P_rel = PD7, P_near = SD1_7, P_ip = PD (Section IV-K).", "Populations: P_rel, P_near and P_ip (Section IV-K) `[code names: P_rel = PD7, P_near = SD1_7, P_ip = PD]`.")
rp("- **Branch and qualifiers (frames v02 §1).** The branch is GO, with no flag (E, A, B, C or D) on either tracker `[C1D: nogo_reasons = []; MAT: verdict line]`.",
   "- **Branch and qualifiers.** The branch is GO, with no flag (E, A, B, C or D) on either tracker `[FR2 §1; C1D: nogo_reasons = []; MAT: verdict line]`.")
rp("**The verdict sentence** (frames v02 §3, with its qualifier).", "**The verdict sentence** (with its qualifier) `[FR2 §3]`.")
rp("- **Scope** (always added, frames v02 §2).", "- **Scope** (always added) `[FR2 §2]`.")
rp("- **The main-text items in brief** (frames v02 §3; details in (b)–(e)).", "- **The main-text items in brief** (details in (b)–(e)) `[FR2 §3]`.")
rp("**What the verdict establishes** (frames v02 §2–§3).", "**What the verdict establishes** `[FR2 §2–§3]`.")
rp("- **The plan's sentence for the screen** (C1-PLAN §6.6, filled from the decision).", "- **The plan's sentence for the screen** (plan §6.6, filled from the decision).")
rp("The plan expected GO on T3 to turn on B6 (C1-PLAN §2; E12).", "The plan expected GO on T3 to turn on B6 (plan §2) `[ERR E12]`.")
rp("their development coverage near δ is 0.78 at 39 units and 0.87 at 150 (C1-PLAN §0).", "their development coverage near δ is 0.78 at 39 units and 0.87 at 150 (plan §0).")
rp("- **H8** is family P, at its own 0.025.\n\n| Claim | Label |",
   "- **H8** is family P, at its own 0.025.\n- **E1-AV2 and E2-AV2** are the method stage's E1 and E2 designs (Section V-C) run on Argoverse 2.\n\n| Claim | Label |")
rp("because it fails only the pooled upper bound (Choice 49c).", "because it fails only the pooled upper bound `[D16 Choice 49c]`.")
rp("(\"the same descriptive pattern under all three seeds\", Choice 54c)", "(\"the same descriptive pattern under all three seeds\") `[D16 Choice 54c]`")
rp("**(g) The independent results review R21.**", "**(g) The independent results review.**")
rp("and 9 in R21's check (500 datasets).", "and 9 in the review's check (500 datasets).")
rp("- **What R21 does not re-derive.** It does not re-derive", "- **What the review does not re-derive.** It does not re-derive")
note("App. F", "internal IDs", "frames v02 / C1-PLAN / E12 / Choice 49c / 54c references into tags or 'plan §'; R21 -> 'the independent results review'; E1-AV2 and E2-AV2 defined once; population code names into a tag")

# ---------------------------------------------------------------------------------------------------------------------
# Table renumbering (TODO item 4): body tables numbered by first citation, Trackers table = I, old I-X -> II-XI
# ---------------------------------------------------------------------------------------------------------------------
ROM = {"II": "II", "III": "III", "IV": "IV", "V": "V", "VI": "VI", "X": "VII", "XII": "VIII", "XIII": "IX"}
r0 = one(s, "## I. Introduction")
r1 = one(s, "## Figures and tables (list with captions)")
seen = collections.Counter()


def _renum(m):
    def sub(r):
        seen[r.group(0)] += 1
        return ROM[r.group(0)]
    return m.group(1) + " " + re.sub(r"\b[IVX]+\b", sub, m.group(2))


s = s[:r0] + re.sub(r"\b(Tables?) ((?:[IVX]+)(?:(?:, | and |–)[IVX]+)*)\b(?![\w(])", _renum, s[r0:r1]) + s[r1:]
s = s.replace("Table @TRK@", "Table I").replace("Table @B1@", "Table B1").replace("Table @F5@", "Table F5").replace(
    "Table @B2@", "Table B2").replace("Table @B3@", "Table B3")
for ph in ("@TRK@", "@B1@", "@F5@", "@B2@", "@B3@"):
    assert ph not in s, ph
note("Tables", "renumbered", "Trackers = I; old I -> Appendix B Table B1; old II-VI keep their numbers; old VII -> Appendix B Table B2; old VIII -> Appendix B Table B3; old IX -> Appendix F Table F5; old X -> VII; old XI was already Appendix F's Table F3; old XII -> VIII; old XIII -> IX; every reference updated, including Appendix F and the figures list")

# Figures and tables list
TL_OLD = blk("**Tables** (numbered by first citation). I X1 2 s cells (val).", "Appendix: A1 full E1/E2 per-stratum tables; A2 frozen hashes and OC.")
FIG9_OLD = "**Fig. 9. Argoverse 2: M\\*'s per-cell exceedances with simultaneous one-sided 95 % bands, per population and tracker** (`95_SUBMISSION/figs_v01/fig09_mstar_cells.pdf`)."
FIG10_OLD = "**Fig. 10. Argoverse 2: infeasible-decision rate per arm, and the paired difference M\\* − arm, per tracker** (`95_SUBMISSION/figs_v01/fig10_infeasible_arms.pdf`)."
rp(FIG9_OLD, FIG9)
FIG10_FLAT = FIG10.replace(":\n- **(a)** the rate", ": **(a)** the rate").replace(";\n- **(b)** the paired", "; **(b)** the paired").replace(
    "interval.\n\nFilled markers", "interval. Filled markers").replace("Form B's bounds for them are in Table X's text.", "Form B's bounds for them are in Section V-F7.")
assert "\n" not in FIG10_FLAT, FIG10_FLAT
rp(FIG10_OLD, FIG10_FLAT)
note("V-F7 / figures list", "moved", "the in-body captions of Figs. 9 and 10 replace their short entries in the figures list, where Figs. 1-8 have theirs; Fig. 10's caption flattened to one paragraph and its pointer 'Table X's text' read 'Section V-F7'")
rp(TL_OLD, "**Tables** (numbered by first citation). I The three nuScenes tracker settings (V-A). II X2 decision cells (train). III X2 gated steps. "
   "IV Method-stage hypotheses. V E1 car cells. VI Margin ratios. VII Argoverse 2 H1 per tracker. VIII Argoverse 2 per arm and tracker. "
   "IX Every claim's status (family S, H6a, H7, H8). Appendix B: B1 X1 2 s cells (val; formerly Table I); B2 K8 per arm and tracker "
   "(formerly Table VII); B3 Trajectron++ results (formerly Table VIII). Appendix F: F1 the registered screen in full; F2 V_t and Form B; "
   "F3 M\\*'s simultaneous upper bounds on Argoverse 2 (descriptive; formerly Table XI); F4 every claim's status in full; "
   "F5 tracker scores on the 375 Argoverse 2 logs (formerly Table IX). Appendix: A1 full E1/E2 per-stratum tables; A2 frozen hashes and OC.")
note("Figures and tables", "updated", "table list renumbered; Appendix F tables listed")

# ---------------------------------------------------------------------------------------------------------------------
# References (TODO items 8-11)
# ---------------------------------------------------------------------------------------------------------------------
rp("Mehra1970, SageHusa1969, Sarkka2009, Huang2018, Zhang2020 [A];",
   "Mehra1970, Sarkka2009, Huang2018, Zhang2020 [A]; **SageHusa1969** — A. P. Sage, G. W. Husa, Algorithms for sequential adaptive "
   "estimation of prior statistics, Proc. 8th IEEE Symp. Adaptive Processes (SAP), 1969, p. 61, doi 10.1109/SAP.1969.269927 (Crossref; "
   "the JACC 1969 citation is not used) [A];")
rp("Li2002 [F];", "**Li2002** — X. R. Li, Z. Zhao, V. P. Jilkov, Estimator's credibility and its measures, Proc. 15th IFAC World Congress, "
   "Barcelona, Jul. 2002 (session T-Fr-M01; proceedings paper 02779, "
   "https://skoge.folk.ntnu.no/prost/proceedings/ifac2002/data/content/02779/abstract.htm; no DOI found; its §3 supports the sentence) [F];")
rp("Gibbs2023 (Gibbs, Cherian, Candès; cited in P02);",
   "Gibbs2023 (Gibbs, Cherian, Candès; cited in P02; the JRSS-B record, 2025, is cited; the key year is the arXiv year only);")
rp("Mei2024 [A];", "**DixitMei2024** (was Mei2024) — A. Dixit, Z. Mei, et al., CoRL 2024, PMLR 270:2517–2541, 2024 (the IJRR version is not used) [A];")
note("References", "updated", "Li2002 (IFAC 2002 record), SageHusa1969 (IEEE SAP 1969, doi 10.1109/SAP.1969.269927), Mei2024 -> DixitMei2024 (CoRL 2024, PMLR 270:2517–2541), Gibbs2023 key kept with year 2025")

rp("*End of draft v05a.*", "*End of draft v05.*")
while "\n\n\n" in s:
    s = s.replace("\n\n\n", "\n\n")

# =====================================================================================================================
# Self-checks
# =====================================================================================================================
# (1) fixed texts byte-identical
for name, fx in (("abstract", ABSTRACT), ("registered-test paragraph", REG), ("contribution 6", C6), ("verdict sentence + next", VERDICT),
                 ("Section VI-E", VIE), ("conclusion", CONCL)):
    assert s.count(fx) == 1, name
    print("fixed text identical:", name, hashlib.sha256(fx.encode("utf-8")).hexdigest()[:12])


def part_of(t, a, b):
    return t[one(t, a):one(t, b)]


CHECK_A = part_of(A, "## Abstract", "## Reference keys")
CHECK_S = part_of(s, "## Abstract", "## Reference keys")
LABEL = re.compile(r"\b(?:Figs?\.|Tables?|Propositions?|Theorems?|Remarks?|Definition|Lemma|Corollary|Algorithm|Sections?|[Ll]ines?|Choices?|items?)\s+"
                   r"\d+(?:\s*[–-]\s*\d+)?(?:(?:\s*,\s*|\s+and\s+)\d+)*")
NUM = re.compile(r"(?<![A-Za-z_\d.\\])(?:\d{1,3}(?:,\d{3})+(?!\d)|\d+)(?:\.\d+)?(?:[⁰¹²³⁴⁵⁶⁷⁸⁹⁻]+)?(?:\s?%)?")


def numbers(t):
    t = LABEL.sub(" ", t)
    return collections.Counter(m.group(0).replace(" ", "") for m in NUM.finditer(t))


def labels(t):
    return set(re.sub(r"\s+", " ", m.group(0)) for m in LABEL.finditer(t) if not m.group(0).startswith(("Table", "Fig")))


na, ns = numbers(CHECK_A), numbers(CHECK_S)
missing = sorted(k for k in na if ns[k] == 0)
new = sorted(k for k in ns if na[k] == 0)
dropped = sorted((k for k in na if 0 < ns[k] < na[k]), key=lambda k: (float(re.sub(r"[^\d.]", "", k.split("⁻")[0]) or 0), k))
print("number tokens v05a / v05:", sum(na.values()), sum(ns.values()), "distinct", len(na), len(ns))
print("MISSING (must be empty):", missing)
print("NEW (must be empty):", new)
print("COUNT DROPS (duplicates):", len(dropped))
for k in dropped:
    print("  drop", k, na[k], "->", ns[k])
assert not missing and not new
la, ls = labels(CHECK_A), labels(CHECK_S)
print("labels lost:", sorted(la - ls), "labels new:", sorted(ls - la))

# (2) citation keys
cite = re.compile(r"\[([A-Z][A-Za-z]+\d{4}[a-z]*(?:LTT|Ego|cbgs|voxelnext|qcnet|nees)?|LeeBarberWillett|Cuonzo|Argoverse2)")


def keys(t):
    out = set()
    for m in re.finditer(r"\[([^\[\]`]*)\]", t):
        for part in re.split(r";\s*", m.group(1)):
            part = part.split(",")[0].strip()
            if re.fullmatch(r"[A-Za-z]+\d{4}[A-Za-z]*|LeeBarberWillett|Cuonzo|Argoverse2|[A-Z][A-Za-z]+\d{4}[a-z]+", part):
                out.add(part)
    return out


ka, ks = keys(CHECK_A), keys(CHECK_S)
print("citation keys lost:", sorted(ka - ks), "new:", sorted(ks - ka))
assert ka - ks == {"Mei2024"} and ks - ka == {"DixitMei2024"}

# (3) wording counts in prose (backtick spans, i.e. provenance tags and code names, excluded; must not rise)
PROSE_A = re.sub(r"`[^`]*`", " ", CHECK_A)
PROSE_S = re.sub(r"`[^`]*`", " ", CHECK_S)
for w in (r"\bvalid\b", r"\bvalidity\b", r"\bcalibrated\b", r"\bcertified\b", r"\bsafe\b", r"\bsafer\b", r"\bguarantee", r"at most δ", r"\btransfers\b"):
    ca, cs = len(re.findall(w, PROSE_A, flags=re.I)), len(re.findall(w, PROSE_S, flags=re.I))
    print(f"wording {w}: {ca} -> {cs}")
    assert cs <= ca, w

# (4) every body float cited, and in order of first citation
body = part_of(s, "## I. Introduction", "## Tools and author responsibility")
caps = {m.group(1): m.start() for m in re.finditer(r"^\*\*Table ([IVX]+)\.", body, flags=re.M)}
order = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX"]
assert list(caps) == order, list(caps)
first = {}
for m in re.finditer(r"\bTables? ((?:[IVX]+)(?:(?:, | and |–)[IVX]+)*)\b", body):
    line_start = body.rfind("\n", 0, m.start()) + 1
    if body.startswith("**Table ", line_start) and m.start() == line_start + 2:
        continue
    for r in re.findall(r"[IVX]+", m.group(1)):
        first.setdefault(r, m.start())
for r in order:
    assert r in first, "table not cited: " + r
    print(f"Table {r}: first cited {'before' if first[r] < caps[r] else 'AFTER'} its caption")
assert [r for r in sorted(first, key=first.get)] == order, sorted(first, key=first.get)
ff = {}
for m in re.finditer(r"\bFigs?\. (\d+)", body):
    line_start = body.rfind("\n", 0, m.start()) + 1
    if body.startswith("**Fig. ", line_start) and m.start() == line_start + 2:
        continue
    ff.setdefault(int(m.group(1)), m.start())
print("figures cited in order:", sorted(ff, key=ff.get))
assert sorted(ff, key=ff.get) == list(range(1, 11))


# (5) word counts
def wc(t, tags=False):
    if not tags:
        t = re.sub(r"`\[[^`]*\]`", " ", t)
    t = re.sub(r"^\|[-| :]+\|\s*$", " ", t, flags=re.M)
    t = re.sub(r"^---\s*$", " ", t, flags=re.M)
    return len(t.replace("|", " ").split())


for nm, t in (("v05a", A), ("v05", s)):
    b = part_of(t, "## I. Introduction", "## Tools and author responsibility")
    ap = part_of(t, "## Appendices", "## Figures and tables (list with captions)")
    print(f"{nm}: body {wc(b)} words without tags ({wc(b, True)} with tags); appendices {wc(ap)} ({wc(ap, True)})")

open(OUT, "w", encoding="utf-8", newline="\n").write(s)
print("written", OUT, hashlib.sha256(open(OUT, "rb").read()).hexdigest())
print("operations logged:", len(LOG))
for sec, kind, what in LOG:
    print(f"  [{sec}] {kind}: {what}")
