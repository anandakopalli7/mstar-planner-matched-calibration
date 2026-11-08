# K7 pre-registration v02: planner-matched calibration of DP-SCRC (1 Nov 2026)

**Status.** Draft until the hash block at the end is filled by `50_CODE/k7/k7_freeze_v01.py`. After the freeze, nothing in this file changes; deviations go to §12.

**Version.** v02 applies the pre-freeze review R12 (`70_TESTS/R12_K7_PREFREEZE_REVIEW_v01.md`, verdict "fix first"); §14 maps every finding to its change. The reviewed draft is `K7_PREREGISTRATION_v01.md`, kept unchanged; every recorded state of the plan text is in `K7_PLAN_HASH_LOG.txt`.

**Line.** Claude line, Programme A. Everything runs on the laptop; no spending.

## 0. Why K7, and what kind of evidence it is

**K6 was a pre-registered NO-GO.** The frozen plan is `K6_PREREGISTRATION_v02.md` (sha256 `6446d9f6…`).
- **The cause.** T3's power floor: 5 power-qualified cells against F_MIN = 6. No validity cell was flagged on either tracker.
- **The confirmation.** R10, R11a and R11b (`90_DECISIONS/D11_K6_CONFIDENCE_AND_K7_ROUTE_v01.md`). Computed precisely, T1's family would also be 5 (R11a F2). Under one reading that the plan does not state, the own-family sup-t, T3 would have passed (R11a F3).
- **K6's NO-GO stands for K6's claim.** No K7 outcome reverses it.

**K6 also found a scope gap (R10 E4).** DP-SCRC was calibrated on the method's in-path population. On constraints the planner relies on outside it, M\* was significantly above δ.

**K7 changes the calibration population.** DP-SCRC and the calibrated baselines are calibrated on the constraints the planner itself evaluates. Everything else is K6's, unchanged: the planner, harness, cells, estimand, inference, power rule, F_MIN, the validity tests (applied to each population, §5) and HK3.

**What kind of evidence K7 is (R12 M4, M5).**

*A second pre-registered look at the same 840 scenes.* Its p-values are conditional on K6 having been seen.

*Not independent of its own calibration.* The calibration items are the planner's enforced pairs at the decision states. On the development scenes, 99.7 % of M7's PD7 records have a calibration item with the identical residual D (R12 Q3). Cross-fitting by log fold keeps each fit away from the scene it is evaluated on, but the design choices were made after seeing all-scene calibration outputs (§13).

*An easier test than K6a.* K7a tests the held-out validity of a planner-matched, cross-fitted calibration, including the planner's relied-on and satisfied selection, log-fold heterogeneity and the hierarchy's fallbacks. K6a was a harder selection-shift test (open-loop calibration, planner records). K7 is not presented as a harder version of K6.

**Reporting constraints, binding on any write-up:**
- A K7 GO supports the planner-population claim only.
- Any statement of in-loop validity "on nuScenes" names both stages, K6 (NO-GO) and K7.
- The abstract states K7a without qualification only after an external-data replication.

**One-shot commitment.** K7 is the last confirmatory stage on these 840 scenes for the claim family "in-loop validity and operability of DP-SCRC". If K7 is a NO-GO, the next step is external data, or nuScenes used openly as development data for a new method stage confirmed on external data. It is never another redesign confirmed on these scenes.

## 1. Claims

| Claim | Statement | Hypothesis |
|---|---|---|
| **K7a** (validity) | In the decision mode, on T1 and T3, M7's exceedance is not significantly above δ = 0.05 in any evaluable cell or in the pooled cell of each of three populations. Each population is tested with K6's own tests (§5). The populations are the planner's PD7, its near-binding part SD1_7 (pair gap ≤ 5 m) and the method's in-path population PD. Non-exceedance is claimed for the power-qualified PD7 and SD1_7 cells only. In-path non-exceedance is not power-qualified, in K6 or in K7 | HK1 |
| **K7b** (practitioner failure) | On T1, a recalibrated practitioner arm (B1 or B4) is significantly above δ in a near-binding (SD1_7) cell where M7 is not | HK2 |
| **K7c** (operability, K6's standard) | At identical states, M7 is significantly less often infeasible than each of B0, B1, B4 and B9, on both trackers | HK3 |

**Not claimed.**
- A closed-loop guarantee.
- A safety ranking from the closed-loop collisions, which are log-replay biased (R10 E3).
- Validity in non-evaluable cells.
- Validity along an object's *true* axes. The axes are the tracked box's: on T1, CANMOT's heading errors put many cars' "lateral" records along a mis-oriented box axis (R11b O1).

## 2. Method M7 and the arms

**Calibration population.** Built by `50_CODE/k7/k7_items_v01.py`.
- **Decision states.** Every decision state of the K6 decision mode: keyframe 1 ≤ k ≤ K − 2, at the logged ego's position and speed.
- **Steps.** Each calibrated step h = 0.5, 1, 1.5, 2 s. The planner enforces constraints only to 2 s.
- **Pairs.** The planner's enforced (track, check time) pairs, decided exactly as in `k6_sim_v02.plan_step`. A pair is enforced at the arm-independent reference margin 0 when some candidate keeps the buffered mean footprints apart and an ego held at its position would too. Only the considered tracks count: within 60 m and not behind the ego.
- **Ground truth.** The pair needs an annotation at k + h with ≥ 1 point, not in a bicycle rack.
- **Items.** Each object axis that separates the pair at the reference ego pose gives one item. The reference pose is the logged pose at t_k + h, which is the decision mode's leash.
  - The item is U = D/sd, with D = sign(sep)·a·(g − m) and sd = √(aᵀS_h a + 0.10²).
  - Its strata are K6's L0 (group, range from the sensor's CTRV, axis, motion) and the method's in-path flag.
- **Records.** Each such pair also gives one record (dx, dy, S_h), used by the NEES and norm-ball baselines.
- **Arm-independence.** Nothing in the population depends on an arm, a margin or a plan choice.
- **Size.** From 850 scenes and 32,449 decision states:
  - T1: 1,606,994 items and 938,461 records; 2.6 % of the items are in-path.
  - T3: 1,613,073 items and 938,718 records; 2.4 % in-path.
  - Of the considered pairs, 99.7–99.8 % are enforced.

**Arms** (fitted by `k7_fit_v01.py`, cross-fitted on K6's 5 log folds, seed 20261101; calibration uses all 850 scenes, evaluation the 840 non-development scenes):

| Arm (run label) | Margin | Fitted on |
|---|---|---|
| **M7** (`Mstar`, `Mstar_ip`) | ĉ(L0, in-path)·sd: DP-SCRC (`m_lib_v04.fit_hier`: own L0 stratum with ≥ 19 calibration scenes, else L1, L2, L3), fitted **separately** on the in-path and not-in-path items | K7 items |
| B6 (`B6_ip`) | The same without motion strata (fit_hier from L1), split by in-path: the motion ablation | K7 items |
| B4 | One pooled CRC ĉ·sd | K7 items |
| B3 | max ĉ of M7, times sd | K7 items |
| B1 | z·√k(group, range)·sd, NEES-guided k | K7 records |
| B9 | Norm-ball CRC radius r | K7 records |
| B0 | z·sd (raw covariance) | fit-free, identical to K6 |
| Z0 | 0 (mean only) | reference, identical to K6 |
| LOG | the delayed logged profile | closed-loop reference |

**Steps 2.5–4 s.** These keep the K6 fits without `_ip` keys. This is harmless: only check times ≤ 2 s are enforced, and they map to steps 0.5–2 s (`MARGIN_OF_EVAL`; R12 m9).

**Why split by in-path.**
- Only 2.6 % of the planner's items are in-path.
- A pooled fit would be driven by objects outside the path and could under-cover in-path objects, where K6 established validity.
- Splitting keeps both parts calibrated on their own data. Each part uses the method's unchanged hierarchy, CRC, n_min = 19 and σ_a = 0.10.

## 3. Harness

`50_CODE/k7/k7_sim_v01.py` is written from the frozen `k6_sim_v02.py` by `tests/make_k7_sim_v01.py`. Its only functional change: an arm whose fit carries `<arm>_ip` takes its threshold from the track's (L0, in-path) instead of L0 alone.

**Tests** (`tests/test_k7_sim_v01.py`, `70_TESTS/k7_scratch/k7_tests_v01.json`, all pass):

| Test | What it checks |
|---|---|
| T-K7-1 | With the K6 fits, decision mode reproduces k6_sim_v02 exactly for every arm on the 10 development scenes, for both trackers (160 comparisons) |
| T-K7-2 | Duplicated `_ip` thresholds reproduce K6 |
| T-K7-3 | The in-path index is selected correctly |
| T-K7-4 | The closed loop reproduces K6 |
| T-K7-5 | The generator reproduces the file |
| T-K7-6 | Distinct `_ip` thresholds take effect in `plan_step`: raising either half changes the decisions, and with in-path margins at 100·sd no in-path exceedance remains (R12 m6) |

**Item–record equivalence (R12 Q3).** R12 checked the items against the planner on the 10 development scenes (`70_TESTS/k7_scratch/r12/r12_items_vs_records_dev.json`). It found 0 mismatches in the considered tracks, the enforced set, the L0 strata and the margins `Mstar_ip[L0 + 96·inpath]·sd`. On 99.7 % of PD7 records the item has the same axis and the same D.

The simulator asserts that every cache carries the in-path flag (R12 m5); R11b verified that all 1,700 caches carry both the in-path and the bicycle-rack fields.

`k7_run_v01.py` is `k6_run_v02.py` running k7_sim_v01, generated by `tests/make_k7_run_v01.py`, with the same design lock.

Planner, candidates, exemptions, back-off, replay devices, collisions and the closed loop: K6 §2, unchanged.

## 4. Populations and endpoints (decision mode; K6 §4 unless stated)

**Records.** As in K6 §4.1 (the K6 code, unchanged). Each record carries the in-path, enforced, satisfied, gap, relied-on, step and stratum bits.

| Population | Definition |
|---|---|
| **PD7 (primary)** | Relied-on axis ∩ enforced ∩ satisfied, any gap, steps 0.5–2 s, offset 0, in-path or not: every constraint the planner relies on |
| **SD1_7 (near-binding)** | PD7 with pair gap ≤ 5 m. About 86 % of PD7's records are far constraints (gap > 5 m) that cannot bind soon; SD1_7 is the part where a margin error matters. With K6's M\* layout (counts only) it has about 122,000 records per tracker |
| **PD** | PD7 ∩ the method's in-path flag (K6's primary population): the non-regression check of K6's population |

- **Cells.** 32 (group × axis × motion, pooled over range) and the pooled cell.
- **Estimand.** The scene-level rate.
- **Infeasible-decision rate, closed-loop quantities.** As K6 §4.2 and §4.3.

## 5. Hypotheses (decision mode, per tracker; `k7_analyse_v02.py`)

**HK1 (`hk1_rule`): K6's validity tests, applied to each of PD7, SD1_7 and PD (R12 C2).** For each population:

| Condition | What is required |
|---|---|
| (i) | No cell is flagged in M7's one-sided simultaneous sup-t at 0.95 over all its evaluable cells. Evaluable: records in ≥ 39 scenes from ≥ 8 logs. Flag: lower bound > δ, or zero SE with the estimate > δ. This is K6's HK1a (i) |
| (ii) | The pooled cell is evaluable and not flagged pointwise at 0.95. This is K6's HK1b |
| (iii) | **PD7 and SD1_7 only:** at least F_MIN = 6 power-qualified cells, not flagged in their own sup-t. The rule is K6's, unchanged: power ≥ 0.80 to be flagged at a true rate of 0.15 in the population's all-evaluable sup-t, beta-binomial with intra-scene correlation 0.5, 200 datasets, M7's record counts only, the first 500 bootstrap weights. Power seeds are `[20261107, i, 0]` for PD7 and `[…, 1]` for SD1_7 |
| (iv) | **PD:** at least 1 evaluable cell. PD's power family is computed with the same rule (seed `[…, 2]`) and **reported**, not required (§6) |

- HK1a = (i), (iii) and (iv) for every population; HK1b = (ii) for every population; HK1 = HK1a and HK1b.
- Every sup-t quantile must be finite (asserted).
- HK1c (pooled upper bound ≤ δ + 0.03) is reported.

**HK2 (T1, near-binding; R12 M5).** All three of the following, with sup-t taken over the evaluable SD1_7 cells:
- B1 or B4 is flagged in an SD1_7 cell at level 1 − 0.05/2, over that arm's evaluable SD1_7 cells;
- M7 is not flagged there in its own all-evaluable SD1_7 sup-t;
- the paired difference arm − M7 is positive at 1 − 0.05/2, over the cells evaluable for both.

B0 is reported, not tested: it is fit-free and its K6 outcomes were seen.

**HK3 (K6's form, unchanged; R12 C1).** M7's infeasible-decision rate is lower than that of each of B0, B1, B4 and B9:
- per-scene paired differences M7 − arm;
- one-sided log-bootstrap upper bound at 1 − 0.05/4, below 0 for all four;
- on both trackers.

**Reported only.** The dominance form of HK3: each comparator is either less operable, or its pooled SD1_7 cell is flagged pointwise at 1 − 0.05/4 with a positive paired pooled difference. It is never a GO condition.

## 6. Decision rule

| Verdict | Conditions |
|---|---|
| **K7 GO-A** | HK1 and HK3 on T1 and T3, and HK2 on T1 |
| **K7 GO-B** | HK1 and HK3 on T1 and T3, without HK2 |
| **K7 NO-GO** | Otherwise. The failed conditions are named (`failed_conditions`) |

- A NO-GO is never reported as support.
- A NO-GO with HK1 on both trackers is reported as "validity shown, operability not shown", never as a GO.

**The standard, compared with K6 (corrected after R12).**

| Aspect | Status | Detail |
|---|---|---|
| Statistics, HK3 and the GO-A/GO-B structure | **Same as K6** | δ; the scene-level estimand; the log bootstrap; sup-t; evaluability; the power rule (0.15, 0.80, ρ = 0.5, 200 datasets); F_MIN = 6; per-population validity tests (all-evaluable sup-t plus a pointwise pooled cell); HK3 |
| More populations tested at K6's standard | **Stricter** | PD7, SD1_7 and PD instead of PD alone. This raises the false-NO-GO rate at the exact validity boundary to 0.08–0.14 (§8; it only makes a GO harder) |
| PD floor | **Changed: a narrower claim** | K6 required ≥ 6 power-qualified PD cells, and T3 had 5 under every seed (R10, R11a). K7 claims power-qualified non-exceedance on the planner's populations, PD7 and SD1_7, not on PD. PD keeps K6's validity tests, but its non-exceedance is not power-qualified. This is a change of claim, not a stricter test. The new floors are far above 6 and are not expected to bind (§8, R12 M1) |
| HK2 | **Changed** | B1 and B4 (recalibrated) on SD1_7 at 1 − 0.05/2, instead of B0, B1, B4 on PD at 1 − 0.05/3. B0's outcomes were seen; PD7 would make HK2 near-automatic (R12 M5, m2) |
| Data | **Changed: lower independence** | The same 840 scenes as K6 (§0) |

## 7. Inference

As K6 §7, with the K6 functions imported unchanged from the frozen `k6_analyse_v02.py`:
- the log-cluster bootstrap, B = 2000, with weights shared by every arm;
- one-sided simultaneous sup-t bounds (`m_lib_v04._simul`).

The power simulation uses the first 500 bootstrap weights, as in K6 (R10 E6, now stated). **Seeds:** bootstrap `[20261106, i, 0 | 1]` (i = 0 for T1, 1 for T3); power `[20261107, i]`. They are fixed before any K7 outcome. The analysis is `k7_analyse_v02.py`.

## 8. Operating characteristics (`tests/k7_oc_v03.py`; `70_TESTS/k7_scratch/k7_oc_v03.json`)

**The coded rule is simulated (R12 M2).** The OC calls `k7_analyse_v02.hk1_rule` itself.
- **Layout.** K6's decision-mode record counts of M\* (n only; outcome-blind), split four ways: near or far, in-path or not.
- **Scene effect.** Per scene and cell, parts with the same rate share one Beta draw. Parts whose rate an alternative changes share one draw of their own, independent of the unchanged parts' draw. This slightly weakens the within-cell correlation across parts. A first version drew comonotone quantiles and was stopped before any output, because it was too slow.
- **Rates.** Intra-scene correlation ρ ∈ {0.1, 0.3, 0.5}. The observed intra-scene correlation of K6 M\*'s exceedances is a median 0.13–0.15 in PD7 cells, 0.21–0.26 in SD1_7 and 0.31–0.32 in PD (R12, `r12_rho_k6.json`).
- **Size.** Scales 1 and 0.5 (half the logs), 200 datasets, B = 500.
- **The families** are computed once per layout, from counts only.

**Alternatives** (the rest at 0.05):

| Label | Alternative |
|---|---|
| A1 | Every cell at 0.05 |
| A1b | Every cell at 0.04 |
| U057, U060 | Every record at 0.057 / 0.060 |
| IP07 | Every in-path record at 0.07 |
| NIP12 | Every near-binding in-path record at 0.12 |
| MED07 | The median PD7 family cell at 0.07 |
| PED07 | The largest pedestrian PD7 cell at 0.07 |
| IPMED15 | The in-path records of the median PD cell at 0.15 |
| IPCLT15 | The in-path car\|lat\|turning records at 0.15 |
| THIN15 | The thinnest PD7 family cell at 0.15 |
| SDTHIN15 | The near-binding records of the thinnest SD1_7 family cell at 0.15 |

**Acceptance**, declared in the OC file before it ran:

| Criterion | Requirement | Note |
|---|---|---|
| Size | A1 ≤ 0.15 and A1b ≤ 0.05 in every layout | K6's limit was 0.10. Testing three populations at K6's standard raises the boundary false-NO-GO rate; the relaxation only makes a GO harder, not easier |
| Informative | At scale 1 and ρ 0.3, on both trackers, power ≥ 0.80 against U060, IP07 and NIP12 | — |
| Floors | Both floors ≥ 6 in every layout | — |

**HK3** is given a normal approximation from the development per-scene paired differences, with design effects 1, 2 and 3.5 (reported).

**History.** v01 simulated two separate families and was stopped. Its log holds 12 layouts, three of which exceeded 0.10: T1 M\* scale 0.5 at ρ 0.1, 0.127; at ρ 0.3, 0.107; and B6 scale 1 at ρ 0.3, 0.103 (R12 M3). v02 simulated the joint family that R12 rejected (C2). Neither describes the coded rule.

### 8a. Results

OC_V03_RESULTS_PENDING

## 9. Development scenes (diagnostics, not evidence)

`tests/k7_dev_check_v01.py` on the 10 nuScenes-mini scenes (`70_TESTS/k7_scratch/k7_dev_check_v01.json`). The results are in §9a.

### 9a. Results

Ten scenes, K7 fits; diagnostics only. Scene-level pooled exceedance is computed with B = 200.

| | Z0 | B0 | B1 | B3 | B4 | B9 | B6 | **M7** |
|---|---|---|---|---|---|---|---|---|
| Infeasible-decision rate, T1 | 0.008 | 0.401 | 0.483 | 0.951 | 0.179 | 0.520 | 0.248 | **0.159** |
| Infeasible-decision rate, T3 | 0.000 | 0.945 | 0.415 | 0.968 | 0.175 | 0.502 | 0.169 | **0.190** |
| Pooled PD7 exceedance, T1 | 0.493 | 0.033 | 0.015 | 0.003 | 0.070 | 0.021 | 0.056 | **0.043** |
| Pooled PD7 exceedance, T3 | 0.520 | 0.005 | 0.040 | 0.004 | 0.087 | 0.028 | 0.063 | **0.051** |
| Pooled PD exceedance, T1 | 0.417 | 0.000 | 0.000 | 0.000 | 0.003 | 0.032 | 0.029 | **0.017** |
| Pooled PD exceedance, T3 | 0.338 | 0.000 | 0.021 | 0.000 | 0.075 | 0.015 | 0.031 | **0.028** |

**Closed loop, M7.** Progress is 0.818 (T1) and 0.810 (T3), with no tracked at-fault collision on these 10 scenes.

**Reading.**
- On T3, B4 and B6 are more often feasible than M7, but B4's pooled exceedance is above δ. This is the case the dominance form of HK3 (§5) is written for.
- M7's development pooled rates (0.043 and 0.051) are close to δ, as expected of a CRC calibrated at δ.
- With about 900,000 PD7 records, the pooled and large cells detect small excesses (OC P2: an excess of 0.08 in the largest cell is found with power 1.0). The test is demanding, and a K7 GO is not assured.

## 10. Sensitivities (descriptive)

**Decision mode:**
- SD1_7: PD7 with gap ≤ 5 m;
- NIP: PD7 not in-path;
- SD3_7: relied-on records with any enforcement or satisfaction;
- every arm's PD7 and PD cells;
- K6's M\* on PD7, from the K6 run (seen);
- the pooled-M7 thresholds (in the fits; not run).

**Closed loop:** as K6, with PL7 (any in-path, offset ≤ 15 m) beside PL and SL1_7.

## 11. Run procedure

1. `run_k7_prep_v01.sh` (already run before the freeze: items and fits).
2. `k7_freeze_v01.py --plan K7_PREREGISTRATION_v02.md --oc 70_TESTS/k7_scratch/k7_oc_v03.json --dev 70_TESTS/k7_scratch/k7_dev_check_v01.json`. It checks the tests, the generators, the fits' binding, the OC acceptance, the development-check path and that no placeholder is left. It appends a pre-freeze line to `K7_PLAN_HASH_LOG.txt`.
3. `run_k7_main_v01.sh`, unattended. It runs T1 and T3 in decide and loop modes with the frozen fits, then `k7_analyse_v02.py` and the decision.
4. An independent results review.

## 12. Deviations

None so far. Any deviation is listed here after the freeze, with its reason, and the frozen analysis is reported beside it.

## 13. What had been seen before the freeze (full disclosure)

1. **All K6 outputs on the 840 scenes.** That covers every arm's in-loop exceedances in PD, SD1, SD2 and SD3, HK2, HK3 and the closed loop. Two consequences:
   - K6's M\* exceeded δ in not-in-path cells, which motivated K7.
   - B0 and Z0 are fit-free, so their K7 outcomes equal K6's and were seen: B0's infeasible rate is 0.338 on T1 and 0.764 on T3.

   R12 also computed the intra-scene correlation of K6 M\*'s exceedances by cell (`r12_rho_k6.json`), used only to read the OC's ρ grid.
2. **The K7 design counts** (`k7_design_counts_v01.json`, `_v02.json`). These are record counts only from the K6 run; the exceedance array was never read. The same script reproduces K6's PD families (7 and 5).
3. **The K7 calibration items and fits.** These are calibration outputs, but they are functions of the very residuals the test uses (R12 M4).
   - The pooled B4 threshold fell from 1.5 to 1.0 on T1 at 0.5 s. That led the draft v01 to a dominance form of HK3, which R12 judged lower than K6's standard (C1). It is now reported only.
   - The draft's claim that the dominance form was decided before the T3 development result existed cannot be verified from file timestamps (R12 M3). It is withdrawn.
4. **The development scenes (10 nuScenes-mini scenes):**
   - the development check (§9a; summaries computed with `k7_analyse_v01`, whose summary quantities do not depend on the hypothesis rules);
   - three development analyses: `dev_v01/dev_analysis_t1.json`, `dev_analysis_v2.json` (after the draft's joint-family change; R12 M3) and `dev_analysis_v3_analyse_v02.json` (after the R12 fixes; HK3 not lower against B4 on either tracker, with 10 scenes);
   - the axis-selection diagnostic (`k7_dev_axis_diag_v01.json`): M7's held-out exceedance on development is 0.044 (T1) and 0.050 (T3) on the reference-relied axis, against 0.059 and 0.058 on the other axis, so all-axes items were kept;
   - the per-scene paired infeasibility differences: M7 − B4 is +0.016 on T3, with M7 worse in 8 of 10 scenes, and −0.020 on T1. **This predicts a real risk that HK3 fails on T3 against B4.** HK3 was nevertheless restored to K6's form (R12 C1);
   - R12's instrumented development re-run (item–record equivalence).
5. **Design sequence (R12 M3).**
   - The draft's joint family was adopted shortly after OC v01 had exceeded its acceptance in 3 of 12 layouts; the joint family is now withdrawn (C2).
   - SD1_7 was added after the record counts by gap bin (counts only).
6. **Not seen.** None of M7's outcomes, and none of the recalibrated B1, B4, B9, B6 or B3 outcomes, on the 840 confirmatory scenes. No held-out exceedance or coverage of any K7 fit on a confirmatory scene was computed. The attestation is timestamped in `K7_PLAN_HASH_LOG.txt` (17:28:41 UTC).

## 14. Reviews

**R12** (`70_TESTS/R12_K7_PREFREEZE_REVIEW_v01.md`): fix first. The changes in v02:

| Finding | Change |
|---|---|
| C1 | HK3 restored to K6's form as the GO condition; dominance reported only (§5) |
| C2 | K6's per-population tests (all-evaluable sup-t, pointwise pooled cell) on PD7, SD1_7 and PD; the joint family withdrawn (§5, `hk1_rule`) |
| M1 | PD power family computed and reported; claim narrowed explicitly (§1, §6); "both problems addressed by design" deleted |
| M2 | OC v03 simulates the coded rule, with R12's alternatives, an informative acceptance and the HK3 approximation (§8) |
| M3 | v01 OC history corrected; all development analyses listed; HK3 timing claim withdrawn; D11 and R11a exist; plan-hash log started (§8, §13) |
| M4 | Evidence type and reporting constraints stated (§0); attestation logged |
| M5 | K7a described as held-out validity of a planner-matched calibration (§0); HK2 on SD1_7 (§5) |
| m1 | K7c reworded to the test |
| m2 | HK2 change listed (§6) |
| m3 | Finite-q assertion; PD needs ≥ 1 evaluable cell; HK1c reported |
| m4 | Fits path bound to the run record's hash; scene→log map asserted per tracker |
| m5 | The simulator asserts the in-path flag (regenerated, tests re-run). The item builder's caches all carry it (R11b); the item file itself is unchanged to keep the frozen items' provenance |
| m6 | T-K7-6 added; item–record equivalence from R12 Q3 |
| m7 | Freeze checks the development path, rejects placeholders and logs a pre-freeze hash |
| m8 | Heading-error caveat (§1) |
| m9 | Steps 2.5–4 s sentence (§2) |

**R12b** (re-review of v02): REVIEW_R12B_PENDING

## Frozen files

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END
