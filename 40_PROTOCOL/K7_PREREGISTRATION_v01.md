# K7 pre-registration v01: planner-matched calibration of DP-SCRC (1 Nov 2026)

**Status.** Draft until the hash block at the end is filled by `50_CODE/k7/k7_freeze_v01.py`. After the freeze, nothing in this file changes; deviations go to §12.

**Line.** Claude line, Programme A. Everything runs on the laptop; no spending.

## 0. Why K7

**K6 (frozen plan `K6_PREREGISTRATION_v02.md`, sha256 `6446d9f6…`) was a pre-registered NO-GO.** Its only failing condition was T3's power floor: 5 power-qualified cells against F_MIN = 6. No validity cell was flagged on either tracker. The audits R10, R11a and R11b confirmed this (`90_DECISIONS/D11_K6_CONFIDENCE_AND_K7_ROUTE_v01.md`).

**K6 also found a scope gap (R10 E4).**
- DP-SCRC was calibrated on the method's in-path population: objects whose constant-velocity footprint meets the logged ego's CTRV corridor.
- On constraints the planner relies on outside that population, M\* was significantly above δ: on T1 in car|long|straight (0.088) and car|long|turning (0.073), and on T3 in 6 cells.

**K7 changes one thing: the calibration population.** DP-SCRC and the calibrated baselines are calibrated on the constraints the planner itself evaluates, instead of the CTRV corridor population. Everything else is K6's, unchanged:
- the planner and harness;
- the cells, estimand, inference and power rule;
- F_MIN, the thresholds and the decision structure.

The calibration population now matches the test population, and that population is large enough to power the cells. Both problems that blocked K6 are therefore addressed by design, before any K7 outcome exists.

**One-shot commitment.** K7 is the last confirmatory stage on these 840 nuScenes scenes for the claim family "in-loop validity and operability of DP-SCRC". If K7 is a NO-GO:
- the next step is external data (a second dataset), not another redesign on these scenes;
- K6 and K7 are both reported in full, whatever the outcome.

## 1. Claims

| Claim | Statement | Hypothesis |
|---|---|---|
| **K7a** (validity) | In the decision mode, M7's exceedance is not significantly above δ = 0.05 in any evaluable cell, or in any pooled cell, of three populations: the planner's population PD7, its near-binding part SD1_7 (pair gap ≤ 5 m), and the method's in-path population PD. This holds on T1 and T3, in one simultaneous family. Non-exceedance is claimed for the power-qualified PD7 and SD1_7 cells only | HK1 |
| **K7b** (practitioner failure) | On T1, a recalibrated practitioner arm (B1 or B4) is significantly above δ in a PD7 cell where M7 is not | HK2 |
| **K7c** (dominance) | No comparator in {B0, B1, B4, B9} is shown to be both as valid as M7 and more operable: each is either less often feasible (higher infeasible-decision rate) or shown invalid where M7 is not | HK3 |

**Not claimed.**
- A closed-loop guarantee.
- A safety ranking from the closed-loop collisions, which are log-replay biased (R10 E3). They are descriptive.
- Validity in non-evaluable cells.

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

## 5. Hypotheses (decision mode, per tracker)

| Hypothesis | Condition |
|---|---|
| **HK1a** | (i) No cell is flagged in the **joint family**: one one-sided simultaneous sup-t at 0.95 over M7's evaluable cells of PD7, SD1_7 and PD, plus the three pooled cells. This is one family-wise 5 % for the whole validity claim, as K6's single family was for its claim. Evaluable: records in ≥ 39 scenes from ≥ 8 logs. Flag: simultaneous one-sided 95 % lower bound > δ, or zero SE with the estimate > δ. (ii) At least F_MIN = 6 power-qualified PD7 cells **and** at least F_MIN power-qualified SD1_7 cells, each family not flagged in its own sup-t. Power-qualified uses the K6 rule unchanged: power ≥ 0.80 to be flagged at a true rate of 0.15, beta-binomial with intra-scene correlation 0.5, 200 datasets, from M7's record counts of that population only. Power seeds are `[20261107, i, 0]` for PD7 and `[20261107, i, 1]` for SD1_7 |
| **HK1b** | The three pooled cells are evaluable, and none is flagged in the joint family |
| HK1 | HK1a and HK1b |
| **HK2** (T1) | B1 or B4 is flagged in a PD7 cell at level 1 − 0.05/2 (sup-t over its evaluable PD7 cells), M7 is not flagged there, and the paired difference arm − M7 is positive at 1 − 0.05/2. B0 is reported, not tested: it is fit-free and its K6 outcomes were seen |
| **HK3** (dominance) | For each of B0, B1, B4 and B9, at level 1 − 0.05/4: either (a) M7's infeasible-decision rate is lower (per-scene paired M7 − arm, one-sided log-bootstrap upper bound < 0), or (b) the arm is flagged in a PD7 cell (sup-t over its evaluable PD7 cells) where M7 is not flagged, with the paired difference arm − M7 positive. K6's form (route (a) for all four) is reported as `HK3_K6_form_all_lower` |

**Why HK3 changed form.** This is a disclosed design decision, made from calibration outputs only.
- On the planner's population, the pooled practitioner threshold B4 falls: at 0.5 s it is 1.03 on T1 against 1.51 in K6, because most items are easy objects away from the path.
- An arm with a small pooled threshold can be feasible more often than M7 while invalid in the hard strata.
- Being more operable than an invalid arm is not a merit, and R10 (§4b, item 9) noted that HK3 is meaningful only jointly with validity.
- The dominance form keeps K6's operability requirement against every comparator that is not shown invalid, and adds no other route.
- The K6 form is still computed and reported.

## 6. Decision rule (unchanged structure)

| Verdict | Conditions |
|---|---|
| **K7 GO-A** | HK1 and HK3 on T1 and T3, and HK2 on T1 |
| **K7 GO-B** | HK1 and HK3 on T1 and T3, without HK2 |
| **K7 NO-GO** | Otherwise. That includes a PD7 or SD1_7 family below F_MIN, any flagged M7 cell or pooled cell in the joint family, and a comparator that is shown neither invalid nor less operable |

**What the standard is, compared with K6.**

| Aspect | Same as K6 | Stricter than K6 | Changed |
|---|---|---|---|
| Statistics | δ, the scene-level estimand, the bootstrap, sup-t, evaluability, the power rule (0.15, 0.80, ρ = 0.5), F_MIN = 6, the HK2 structure and the GO-A/GO-B structure | — | — |
| Validity family | Family-wise level 5 % | It covers PD7, SD1_7 and PD, with their pooled cells | — |
| Power floor | — | Two floors (PD7 and SD1_7) instead of one | — |
| HK3 | — | — | The dominance form (§5) |
| PD floor | — | — | No power floor on PD. PD is a no-flag non-regression check; the claim's population is the planner's. K6 showed that PD's thinness on nuScenes is a data limit (T3: 5 qualified cells under 20 of 20 seeds, R10, R11a), and requiring it again would repeat a known data shortfall, not test the method |

A NO-GO is never reported as support.

## 7. Inference

As K6 §7, with the K6 functions imported unchanged from the frozen `k6_analyse_v02.py`:
- the log-cluster bootstrap, B = 2000, with weights shared by every arm;
- one-sided simultaneous sup-t bounds (`m_lib_v04._simul`).

The power simulation uses the first 500 bootstrap weights, as in K6 (R10 E6, now stated). **Seeds:** bootstrap `[20261106, i, 0 | 1]` (i = 0 for T1, 1 for T3); power `[20261107, i]`. They are fixed before any K7 outcome. The analysis is `k7_analyse_v01.py`.

## 8. Operating characteristics (`tests/k7_oc_v02.py`; `70_TESTS/k7_scratch/k7_oc_v02.json`)

**Layouts.** The observed K6 decision-mode record counts of M\* (n only; outcome-blind; the closest proxy for M7's layout). They are split four ways: near or far, in-path or not. K6's own OC failed by modelling the layout from development scenes (R10 E2); K7 uses the observed one.
- **Scales:** 1 and 0.5 (half the logs).
- **Correlation:** ρ ∈ {0.1, 0.3, 0.5}, with one scene effect per scene and cell shared by the four parts.
- **Datasets:** 250, with B = 500.

**What is reported:**
- A1, P(HK1 fails), with every cell at 0.05;
- A1b, with every cell at 0.04;
- P1, the thinnest PD7 family cell at 0.15;
- P2, the largest PD7 cell at 0.08;
- P3, the near-binding records only of the thinnest SD1_7 family cell at 0.15;
- P4, the in-path records only of the largest PD cell at 0.15.

**Acceptance:** A1 ≤ 0.10, and both floors ≥ F_MIN, in every layout.

**History.** v01 (two separate families, no SD1_7) was stopped after two layouts, A1 = 0.077 and 0.087 at ρ 0.1 (`k7_oc_v01_superseded_partial.log`). The design then gained SD1_7 and the joint family, and v01 no longer described it.

### 8a. Results

**Acceptance is met in every layout.** A1 max = 0.016, and both floors are ≥ 6.

| Layout | Evaluable PD7 / SD1_7 / PD | Floors PD7 / SD1_7 | A1 | A1b | P1 | P2 | P3 | P4 |
|---|---|---|---|---|---|---|---|---|
| T1, scale 1, ρ 0.1 | 32 / 25 / 18 | 27 / 18 | 0.004 | 0 | 1.00 | 1.00 | 0.94 | 1.00 |
| T1, scale 1, ρ 0.3 | 32 / 25 / 18 | 27 / 18 | 0.000 | 0 | 0.99 | 0.99 | 0.80 | 1.00 |
| T1, scale 1, ρ 0.5 | 32 / 25 / 18 | 27 / 18 | 0.000 | 0 | 0.92 | 0.83 | 0.79 | 1.00 |
| T1, scale 0.5, ρ 0.1 | 29 / 21 / 8 | 24 / 11 | 0.016 | 0 | 0.98 | 1.00 | 0.97 | 1.00 |
| T1, scale 0.5, ρ 0.3 | 29 / 21 / 8 | 24 / 11 | 0.008 | 0 | 0.88 | 0.59 | 0.85 | 0.97 |
| T1, scale 0.5, ρ 0.5 | 29 / 21 / 8 | 24 / 11 | 0.004 | 0 | 0.64 | 0.32 | 0.66 | 0.91 |
| T3, scale 1, ρ 0.1 | 32 / 26 / 17 | 27 / 18 | 0.008 | 0 | 1.00 | 1.00 | 0.84 | 1.00 |
| T3, scale 1, ρ 0.3 | 32 / 26 / 17 | 27 / 18 | 0.000 | 0 | 0.99 | 0.98 | 0.79 | 1.00 |
| T3, scale 1, ρ 0.5 | 32 / 26 / 17 | 27 / 18 | 0.000 | 0 | 0.95 | 0.78 | 0.76 | 1.00 |
| T3, scale 0.5, ρ 0.1 | 32 / 20 / 10 | 24 / 13 | 0.000 | 0 | 0.97 | 0.99 | 0.80 | 1.00 |
| T3, scale 0.5, ρ 0.3 | 32 / 20 / 10 | 24 / 13 | 0.000 | 0 | 0.85 | 0.63 | 0.63 | 0.96 |
| T3, scale 0.5, ρ 0.5 | 32 / 20 / 10 | 24 / 13 | 0.008 | 0 | 0.62 | 0.33 | 0.54 | 0.85 |

**Reading.**
- At the actual size (scale 1), a single invalid cell at 0.15 is caught with power 0.92–1.00 (P1). An excess confined to the near-binding records of the thinnest SD1_7 family cell is caught with power 0.76–0.94 (P3), and one confined to the in-path records with power 1.00 (P4). A mild excess of 0.08 in the largest cell is caught with power 0.78–1.00 (P2).
- The joint family is conservative at the boundary (A1 ≤ 0.016, against a nominal 0.05). The reason is not established; the skew of per-scene rates near 0.05 and the dependence across the 61–78 cells are candidates. A false NO-GO is therefore unlikely, and the price is lower power against small excesses. That limit is stated, not hidden: K7a claims non-exceedance only in the power-qualified cells, with the simultaneous upper bounds reported.

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
2. `k7_freeze_v01.py --plan K7_PREREGISTRATION_v01.md --oc 70_TESTS/k7_scratch/k7_oc_v02.json --dev 70_TESTS/k7_scratch/k7_dev_check_v01.json`.
3. `run_k7_main_v01.sh`, unattended. It runs T1 and T3 in decide and loop modes with the frozen fits, then the analysis and the decision.
4. An independent results review.

The runner refuses to start unless the plan sidecar, the frozen block and the run inputs match, and only with the fixed design.

## 12. Deviations

None so far. Any deviation is listed here after the freeze, with its reason, and the frozen analysis is reported beside it.

## 13. What had been seen before the freeze (full disclosure)

1. **All K6 outputs on the 840 scenes.** That covers every arm's in-loop exceedances in PD, SD1, SD2 and SD3, the HK2 and HK3 results and the closed loop. In particular:
   - K6's M\* exceeded δ in not-in-path cells. This motivated K7.
   - B0 and Z0 are fit-free, so their K7 outcomes are identical to K6's and were seen: B0's infeasible rate is 0.338 on T1 and 0.764 on T3.
2. **The K7 design counts** (`70_TESTS/k7_scratch/k7_design_counts_v01.json` and `_v02.json`). These are record counts only, from the K6 run; the exceedance array was never read. They sized the K7 design. The same script reproduces K6's PD families (7 and 5).
   - On PD7 with K6's M\* layout, T1 has 32 evaluable cells and a family of 27–28, and T3 has 32 evaluable cells and a family of 26–28.
   - SD1_7 and SD0_7 are given in the v02 file.
3. **The K7 calibration items and fits.** These are calibration outputs, not test outcomes. They include the drop of the pooled B4 threshold (§5). HK3's dominance form was decided from that drop and from the T1 development infeasibility (M7 0.159, B4 0.179), before the T3 development result (M7 0.190, B4 0.175) existed.
4. **The K7 development check** on the 10 development scenes (§9a). It prompted two design reviews:
   - **SD1_7.** Its addition followed the record counts by gap bin, not any outcome.
   - **The axis selection of the calibration items.** The development diagnostic `tests/k7_dev_axis_diag_v01.py` (`70_TESTS/k7_scratch/k7_dev_axis_diag_v01.json`) was run on the development scenes only. Under the all-axes calibration, M7's held-out exceedance is:

     | Items | T1 | T3 |
     |---|---|---|
     | Reference-relied axis | 0.044 | 0.050 |
     | Other axis | 0.059 | 0.058 |

     Calibrating on the relied axis alone (`k7_items_v02.py`) would therefore lower the margins. The method's all-separating-axes definition was kept, and the v02 items are not used for any fit.
   - **A watch item.** Pedestrian items run at about 0.064–0.069 on the 10 development scenes. That is noisy; nothing was changed for it.
5. **Not seen.** None of M7's outcomes, and none of the recalibrated B1, B4, B9, B6 or B3 outcomes, on the 840 confirmatory scenes. No held-out coverage of any K7 fit was computed.

## 14. Reviews

(Pre-freeze review R12 and responses are added here.)

## Frozen files

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END
