# K6 pre-registration v02: closed-loop evaluation of DP-SCRC (1 Nov 2026)

**Status.** This is the version to be frozen. It becomes binding when `50_CODE/k6/k6_freeze_v02.py` fills its hash block and writes its `.sha256` sidecar; the freeze is recorded in `K6_FREEZE_RECORD_v02.txt`, which is not itself frozen. v01 (draft `e757fbe6…`, `K6_PLAN_HASH_LOG.txt`) was reviewed by R09, never frozen, and is kept unchanged. The v02 draft `75eb7101…` was re-reviewed by R09b (`70_TESTS/R09B_K6_PREFREEZE_REREVIEW_v01.md`; 0 critical, 3 major, 11 minor; "freeze after fixes"). §13 answers every R09 finding and §13b every R09b finding.

**What had been seen when this plan was written.**
1. **No confirmatory episode.** No closed-loop episode or planner decision had been run on any of the 840 confirmatory scenes.
2. **Computed on those scenes:**
   - inputs (horizons, ego paths, caches, cross-fitted fits);
   - the open-loop calibration items, a new 8-step build on the deployed output (score ≥ 0.4) that includes steps D07 did not have (0.5, 1.5, 2.5, 3 and 3.5 s). Their residuals were computed and used only for the cross-fitted fits; at the steps D07 had, they are the method stage's residuals on a subset (R09b m8);
   - the record layout of the OC (stratum fields only).
3. **The score threshold 0.4** (D09 v02 C3) was chosen from the GT pairing rates of 59 confirmatory train scenes (worker 0).
4. **Development scenes.** Closed-loop and decision outcomes had been seen on the 10 nuScenes-mini scenes only, and every K6 analysis excludes those scenes. Nine recorded development iterations fixed the planner rules:
   - dev v01–v05 (D09 v03 §0);
   - dev v05b (the scratch run `try_twolevel`), v06 and v07 (D09 v04 §0–§1);
   - dev v08 (D09 v05);
   - in addition, the scratch runs `try_h2s` and `dev_v02_t1only`.
5. **Earlier OC runs** (`k6_oc_t1_v01.json`, `k6_oc_v01.json`, R09's `r09_oc_realistic.json`) preceded the OC v02 used here.
6. **HK3 was chosen after seeing development outcomes (R09b MJ2).** HK3's endpoint, the infeasible-decision rate, and its comparator set were chosen *after* dev v07:
   - **Infeasibility.** In dev v07, M\*'s infeasible-decision rate was 0.19 against 0.40–0.63 for B0, B1, B4 and B9 on T1, and 0.28 against 0.33–0.95 on T3.
   - **Progress.** The closed-loop progress differences were small, for example T1 M\* 0.67 against B4 0.65.
   - **v01's HK3** was progress against B3 and B9. B3 is dominated by construction.
   - **B6 is not an HK3 comparator.** B6 is DP-SCRC without the motion strata, a variant of the method rather than an alternative. D07 had already found the motion strata cost margin on Poly-MOT (M\*/B6 = 1.056), and in development B6 was more often feasible than M\* on T3 (0.24 against 0.28). M\* against B6 is reported as the motion-state option, and no operability claim is made against it.

## 1. Question, claims, and what is already known

**Question.** A chance-constrained (CC) speed planner takes its covariance from one of several calibration arms. Two things are asked:
1. Does the certificate of DP-SCRC (M\*) carry over to the constraints the planner relies on?
2. Does calibration make the planner operable, that is, less often left without a feasible plan, compared with the practitioner corrections (B0, B1, B4) and the norm-ball certified alternative (B9)?

| Claim | Statement | Test |
|---|---|---|
| **K6a** (validity on relied-on constraints) | In the decision mode, on the calibrated population, M\*'s exceedance is not significantly above δ = 0.05 in any evaluable cell, nor in the pooled cell, on T1 and T3. The claim of non-exceedance is made for the power-qualified cells only: those where an exceedance of 0.15 would be detected with power ≥ 0.80 under the stated model | HK1 |
| **K6b** (operational benefit) | At identical logged states, M\* leaves the planner without a feasible plan less often than B0, B1, B4 and B9, on T1 and T3 | HK3 |
| K6c (practitioner failure in the loop) | B0, B1 or B4 significantly above δ where M\* is not (Bonferroni over the three) | HK2: supportive, separates GO-A from GO-B |
| — (closed-loop operation) | Progress, infeasible frames, stops, collisions, buffer intrusions and sensor offset per arm | Estimates with intervals, not tests |

**What is already known, and how far K6 adds to it.**
- **K6a is a selection-shift test.** It tests whether the method stage's open-loop calibration survives the planner's selection of constraints (axis, sign, relied-on, satisfied). The residuals are the same tracker predictions against the same annotations that the method stage analysed (R09 M5).
- **HK2 on T1 is expected from D07** (B4 and B1 fail car lateral turning open-loop). The development scenes suggest it may *not* appear on the relied-on constraints of this planner (D09 v04 §1). Either outcome is reported.
- **HK3 is new.** No earlier stage measured planner feasibility.
- **Dominance.** B3's multiplier is the maximum of M\*'s thresholds, so M\*'s margins are never larger, and its feasibility at a given state is at least B3's by construction. M\* − B3 is reported, not tested (R09 M4).
- **HK3 against B0 on T3 is near-implied (R09b m1).** Poly-MOT's covariance over-covers (D07). M\*'s multiplier exceeds z in at most 0.7 % of T3's confirmatory items at 0.5–2 s, and in development M\* was never infeasible where B0 was feasible (0 of 384 T3 decisions). The test is kept, but it adds little on T3.

**Not claimed.**
- A closed-loop guarantee.
- Reactive-agent behaviour: agents are logged and do not react.
- Perception from the simulated ego's viewpoint: perception is replayed from the logged ego.
- Lateral or path planning.
- Anything about the 10 development scenes.
- Operability against B6: that comparison is the motion-state option, reported only.
- Closed-loop safety differences between arms as calibration effects. An arm that is infeasible more often runs more often at a backed-off margin (C14). In development every tracked at-fault collision was fallback-related, but that is weak evidence: the 2 s fallback window covered 39–95 % of the margin arms' driving time (R09c N3).
- That K6's M\* is the method stage's frozen rule. **K6's M\* is a new cross-fit:** the deployed output with score ≥ 0.4, 8 steps, 5 log folds over 850 scenes, built with the method stage's `fit_methods` (R09 m14).

## 2. Harness

The harness is `90_DECISIONS/D09_K6_HARNESS_DESIGN_v05.md` and v04 (with v01–v03 for unchanged sections), implemented in `50_CODE/k6/k6_sim_v02.py` and tested by `tests/test_k6_sim_v02.py` (13/13 pass). The simulator is generated from `k6_sim_v01.py` by `make_k6_sim_v02.py`, `_step2` and `_step3`.

**World and perception.**
- The world is the nuScenes trainval logs, with non-reactive annotated agents.
- Perception is the recorded CenterPoint → T1 (CANMOT `sc`) or T3 (Poly-MOT) output, restricted to tracks with score ≥ 0.4.
- Means and covariances at the 8 steps come from each class's own filter.

**Planner.**
- **Path and replanning.** It plans speed along the logged 20 Hz path and replans at every keyframe.
- **Candidates.** 32 accelerate-then-brake candidates plus an emergency stop, scored by the mean planned position over 4 s.
- **Constraints.** Object-axis half-spaces with a 0.5 m buffer, checked every 0.25 s and **enforced up to 2 s** (C10). A pair is safe if one object axis has gap ≥ margin.
- **Exemptions (C8).** They are decided at the arm-independent reference margin 0. A (track, check time) pair is exempt if no candidate keeps the buffered mean footprints apart, or if an ego held at its current position would not. Every other pair is enforced at the arm's margin.
- **Choice.** The feasible candidate with the largest planned progress.
- **Fallback (C14).** If no candidate is feasible at the arm's margin (an *infeasible decision*), the margin is backed off on the same enforced set, λ ∈ {0.75, 0.5, 0.25, 0}. The planner takes the best candidate at the largest feasible λ, and the emergency stop only if λ = 0 is infeasible.
- **Decision-mode replay devices, shared by every arm (R09b m10).**
  - The planner's speed is the logged speed over a centred 0.5 s window, so it reads 0.25 s of the future log: a median difference of 0.06 m/s from the CTRV speed, 95th percentile 0.30 m/s.
  - v_max is the scene's maximum logged speed + 2 m/s.
  - Candidates are capped at the future logged positions (the leash).
- **Strata.** Computed from the sensor, that is, the logged ego's CTRV (C9).

**Margins by arm** (margin along axis a, with sd = √(aᵀS_h a + 0.10²)).

| Arm | Margin |
|---|---|
| B0 | z·sd |
| B1 | z·√k(group, range)·sd |
| B3 | max ĉ·sd |
| B4 | ĉ_pooled·sd |
| B9 | r |
| B6 | ĉ_L1·sd |
| M\* | ĉ_L0·sd |
| References | Z0 (margin 0) and LOG (the delayed logged profile, closed loop only) |

**Fits.** Cross-fitted over 5 log folds (seed 20261101) at each of the 8 steps (`60_RESULTS/k6_items_v01/k6_fits_t{1,3}_v01.json`).

**Two modes (C11).**
- **decide.** At every keyframe 1 ≤ k ≤ K − 2, the planner decides once from the logged ego's position and speed, with the leash set to the log. The sensor offset is 0, and every arm is paired at identical states. This mode carries the confirmatory tests.
- **loop.** The closed loop with delays d ∈ {0, 1, 2} s and a leash s(t) ≤ s_log(t − d). It carries the operational estimates.

**Collisions (loop).**
- Exact rectangle overlap at every 0.1 s substep.
- At fault: the ego is moving and the agent overlaps its front half.
- Tracked: a deployed track was paired to the agent in one of the previous two keyframes.
- Artefact: an agent that LOG at the same delay overlaps.

## 3. Population and runs

- **Scenes.** The 840 trainval scenes other than the 10 mini scenes.
- **Trackers.** T1 is primary; T3 is the replication.
- **decide.** 8 arms (Z0, B0, B1, B3, B4, B9, B6, M\*) × 840 scenes; each scene contributes K − 2 decisions.
- **loop.** 9 arms (with LOG) × 3 delays × 840 scenes = 22,680 episodes per tracker.
- **Exclusions.** An episode is excluded if its entry pose overlaps an agent (at any delay, including d = 0), or if it has fewer than delay + 2 keyframes. Exclusions do not depend on the arm.
- **Progress** is defined when the logged travel is ≥ 10 m.

## 4. Endpoints

### 4.1 In-loop exceedance (HK1, HK2): decision mode

**Records.** For the chosen plan at keyframe k, the records are taken over every deployed track paired to an annotated object at k. That object must also be annotated at k + h, for h = 1 … 4 (0.5–2 s), with at least 1 point and not in a bicycle rack.

For each object axis that separates the pair at the planned ego pose:
- D = sign(sep)·a·(g − m);
- the record exceeds if D > margin.

Each record carries the in-path, enforced, satisfied, gap, relied-on, step and stratum bits (C12).

**Primary population PD.** The method's in-path flag ∩ relied-on axis (the largest gap − margin) ∩ enforced ∩ satisfied (the chosen plan kept the relied-on gap ≥ margin), with any gap, at steps 0.5–2 s.

**Cells.** 32 cells (group × axis × motion state, pooled over range) and the pooled cell.

**Estimand.** The scene-level rate: the mean, over scenes with records in the cell, of the scene's exceedance fraction.

### 4.2 Infeasible-decision rate (HK3): decision mode

- **Definition.** For each scene and arm, the share of its decisions in which no candidate satisfied the enforced constraints at the arm's full margin. In those decisions the planner backs off (C14), and the emergency stop is taken only if even λ = 0 is infeasible (R09c N1).
- **Contrast.** Paired per scene: M\* − arm.

### 4.3 Closed-loop estimates

| Quantity | How it is reported |
|---|---|
| Progress ratio s(end) / s_log(end − d) | Mean per arm; contrasts M\* − arm per (scene, delay) with log-bootstrap 95 % intervals |
| Infeasible frames, back-off use and emergency stops, hard braking, blocked time, mean \|a\| | Per arm |
| At-fault collisions with tracked agents, split into fallback-related (within 2 s of an infeasible decision) and not | Per 1000 episodes, exact Poisson 95 % interval. Contrasts between arms are descriptive and are not interpreted as calibration effects (C14) |
| At-fault collisions with untracked agents | Per 1000 episodes, exact Poisson 95 % interval |
| Not-at-fault collisions and artefacts | Counts |
| Front buffer intrusions | Per episode |
| Sensor offset | Median, and share of frames > 15 m |
| In-loop exceedance with sensor offset ≤ 15 m (population PL) | Secondary consistency check |

## 5. Hypotheses (decision mode, per tracker)

| | Statement | Holds when |
|---|---|---|
| **HK1a** | M\* valid in every evaluable cell, with at least F_MIN power-qualified cells | Two conditions (C15, R09b MJ3). (i) **No flag:** no cell is flagged in M\*'s sup-t over *all* its evaluable cells (records in ≥ 39 scenes from ≥ 8 logs), where a flag means a simultaneous one-sided 95 % lower bound > δ, or zero SE with estimate > δ. (ii) **Enough qualified cells:** at least F_MIN = 6 power-qualified cells, also not flagged in their own sup-t. A power-qualified cell is an evaluable cell whose simulated power to be flagged at a true rate of 0.15 is ≥ 0.80. That power is computed from M\*'s record counts only, under a beta-binomial with intra-scene correlation 0.5 (200 datasets, seed 20261104). The claim of non-exceedance is made for those cells only. The power is ≥ 0.80 under this model, and R09b showed it falls under stronger clustering (R09b m2). |
| **HK1b** | M\* pooled not above δ | The pooled PD cell is not flagged. |
| HK1 | | HK1a and HK1b. |
| **HK2** | A practitioner arm fails where M\* holds | For some b ∈ {B0, B1, B4}, three conditions hold in the same cell: it is flagged at level 1 − 0.05/3 (sup-t over b's evaluable cells); M\* is not flagged there in M\*'s own sup-t over all its evaluable cells at level 0.95 (R09b m9); and the paired difference b − M\* is positive at level 1 − 0.05/3 (sup-t over the cells evaluable for both). |
| **HK3** | M\* is feasible more often | For each b ∈ {B0, B1, B4, B9}, the one-sided log-bootstrap upper bound of the mean per-scene difference (M\* − b), at level 1 − 0.05/4, is < 0. |

HK1c (descriptive) is the pooled simultaneous upper bound against δ + 0.03.

## 6. Decision rule

| Verdict | Condition |
|---|---|
| **K6 GO-A** | HK1 and HK3 on both T1 and T3, and HK2 on T1 |
| **K6 GO-B** | HK1 and HK3 on both T1 and T3, and HK2 not on T1 |
| **K6 NO-GO** | otherwise, including an HK1a family below the floor |

`k6_analyse_v02.decide` implements the table. A NO-GO is diagnosed and a pivot proposed; it is never reported as support.

## 7. Inference

- **Bootstrap.** Log-cluster bootstrap with B = 2000. The seed is [20261102, tracker index, 0] for decide and [20261102, tracker index, 1] for loop. A log's weight applies to all its scenes, arms and episodes, so the paired contrasts share the weights.
- **Simultaneous bounds.** Taken with `m_lib_v04._simul` (sup-t) over the family concerned.
- **Progress and infeasibility contrasts.** Bootstrap means of the per-scene (or per-episode) differences.
- **Multiplicity.**
  - HK1 must hold on both trackers.
  - HK2 is Bonferroni-corrected over the three practitioner arms.
  - HK3 is Bonferroni-corrected over its four arms and must hold on both trackers.

## 8. Operating characteristics (`tests/k6_oc_v02.py`; `70_TESTS/k6_scratch/k6_oc_v02.json`)

**Layout.**
- For each confirmatory scene, the open-loop items per cell are multiplied by that cell's development ratio of M\*'s PD records to open-loop items. A missing ratio takes the mean of the motion class, or failing that the pooled ratio.
- **Zero development ratios are floored at 0.02**, not treated as structural zeros (R09b m4).
- The layout is scaled by 0.5, 1 and 2, with ρ ∈ {0.1, 0.3}, 300 datasets and B = 500.
- The planted practitioner arm uses M\*'s layout. Arms are simulated independently, which is conservative for the paired test, since in reality they share residuals (R09 m12).
- A1 counts HK1 as failing when *any* evaluable cell is flagged (C15).

**Acceptance (checked by the freeze script, which reads only the frozen OC file).** At scale 1, in every layout:
- A1 = P(HK1 fails | M\* valid) ≤ 0.10;
- the HK1a family has at least F_MIN = 6 cells;
- on T1, the family contains car|lat|straight and car|lat|turning, the cells of the method-stage failures. This is the informative criterion (R09b m3).

| Layout | Evaluable cells | HK1a family | A1: P(HK1 fails \| M\* valid) | P(flag \| M\* at 0.15 in the thinnest family cell) | Practitioner power in car\|lat\|turning at 0.10 / 0.15 / 0.20 |
|---|---|---|---|---|---|
| T1, scale 0.5, ρ 0.1 | 17 | 7 | 0.050 | 1.00 (car|lat|turning) | 0.10 / 0.67 / 0.96 |
| T1, scale 0.5, ρ 0.3 | 17 | 8 | 0.037 | 0.92 (pedestrian|long|turning) | 0.06 / 0.65 / 0.99 |
| T1, scale 1.0, ρ 0.1 | 18 | 11 | 0.053 | 1.00 (large|long|static) | 0.17 / 0.92 / 1.00 |
| T1, scale 1.0, ρ 0.3 | 18 | 11 | 0.070 | 0.96 (large|long|static) | 0.17 / 0.90 / 1.00 |
| T1, scale 2.0, ρ 0.1 | 20 | 11 | 0.043 | 1.00 (large|long|static) | 0.46 / 0.99 / 1.00 |
| T1, scale 2.0, ρ 0.3 | 20 | 11 | 0.053 | 0.99 (large|long|static) | 0.35 / 0.97 / 1.00 |
| T3, scale 0.5, ρ 0.1 | 15 | 6 | 0.063 | 1.00 (car|lat|static) | not evaluable |
| T3, scale 0.5, ρ 0.3 | 15 | 6 | 0.070 | 1.00 (car|lat|static) | not evaluable |
| T3, scale 1.0, ρ 0.1 | 17 | 8 | 0.030 | 1.00 (pedestrian|lat|turning) | 0.00 / 0.08 / 0.27 |
| T3, scale 1.0, ρ 0.3 | 17 | 9 | 0.043 | 0.97 (large|long|static) | 0.01 / 0.04 / 0.26 |
| T3, scale 2.0, ρ 0.1 | 19 | 12 | 0.043 | 1.00 (large|long|static) | 0.04 / 0.46 / 0.89 |
| T3, scale 2.0, ρ 0.3 | 19 | 11 | 0.063 | 1.00 (large|long|static) | 0.04 / 0.45 / 0.86 |

**Reading the table.**
- **Acceptance.** It holds in every layout. At scale 1, A1 is 0.030–0.070 and the family has 8–11 cells.
- **What acceptance shows.** A1 ≤ 0.10 is a sanity check: a conservative sup-t passes it easily. The informative criterion is that T1's family includes the moving-car lateral cells.
- **Practitioner arms.** On T1, a practitioner arm at 0.15 in car|lat|turning is detected with power 0.65–0.99. At 0.10 the power is only 0.06–0.46, so HK2 cannot see small failures.
- **T3.** car|lat|turning is barely populated on T3, because the development ratio was 0, floored at 0.02, and HK2 there has little power. HK2 is decided on T1 only.
- **False NO-GO.** The probability that a valid M\* fails HK1 on at least one tracker is about 1 − (1 − 0.070)² ≈ 0.14.

**HK3 power.** A normal approximation from the development per-scene paired differences, with a log-cluster design effect of 1, 2 or 3.5 on the standard error, at the development effect and at half of it.

| Tracker | Arm | Development mean (SD) of M\* − arm, per scene | Power at the development effect, design effect 1 / 2 / 3.5 | Power at half the effect, design effect 1 / 2 / 3.5 |
|---|---|---|---|---|
| T1 | B0 | -0.210 (0.379) | 1.00 / 1.00 / 0.99 | 1.00 / 0.96 / 0.52 |
| T1 | B1 | -0.376 (0.314) | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| T1 | B4 | -0.205 (0.376) | 1.00 / 1.00 / 0.99 | 1.00 / 0.96 / 0.51 |
| T1 | B9 | -0.442 (0.325) | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| T3 | B0 | -0.669 (0.183) | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 1.00 |
| T3 | B1 | -0.049 (0.078) | 1.00 / 1.00 / 1.00 | 1.00 / 0.99 / 0.64 |
| T3 | B4 | -0.096 (0.148) | 1.00 / 1.00 / 1.00 | 1.00 / 0.99 / 0.66 |
| T3 | B9 | -0.322 (0.386) | 1.00 / 1.00 / 1.00 | 1.00 / 1.00 / 0.89 |

**Joint power.** HK3 needs all 8 one-sided tests (4 arms × 2 trackers). As a product (treating the tests as independent), the joint power is:
- at the development effect: 1.00 with design effect 2, and 0.98 with design effect 3.5;
- at half the effect: 0.90 with design effect 2, and 0.10 with design effect 3.5.

The weakest single contrasts are T1 against B4 (0.51) and T1 against B0 (0.52), both at half the effect with design effect 3.5 (R09b m7). The development effects come from 10 scenes.

## 9. Development scenes (diagnostics, not evidence)

**Where the results are.** D09 v04 §1 and D09 v05 §1, with data in `70_TESTS/k6_scratch/k6_dev_check_v02.json` (final rules, dev v08).

**How they were used (R09b MJ2).**
- **To fix the planner rules.** Each change listed in D09 v03–v05 states its reason.
- **To choose HK3's endpoint and comparator set.** This was done after dev v07; see "What had been seen" item 6.
- **The HK1 and HK2 populations** (PD) were set in response to R09, before their development values were inspected for any choice.

**Not evidence.** Ten scenes from 8 logs support no statement about the arms.

## 10. Sensitivities (descriptive)

**Decision mode.**
- SD1: pair gap ≤ 5 m.
- SD2: the records that are not in-path.
- SD3: every relied-on record, whatever its enforcement or satisfaction.
- S6: the record-pooled rate (E_rec) of each cell.

**Closed loop.**
- PL: in-loop exceedance with sensor offset ≤ 15 m.
- SL1: all offsets.

**Arm comparisons.**
- B6 against M\* (the motion-state option).
- M\* against B0, B1 and B4 in progress (the price of validity against arms that under-cover).
- T3 against T1.

## 11. Run procedure

1. **The run.** `50_CODE/k6/run_k6_main_v02.sh` runs `k6_run_v02.py`, for T1 then T3, in decide mode and then in loop mode, with 6 workers on this laptop. Each run refuses to start unless:
   - the sidecar and frozen block match;
   - the fits, simulator, runner and manifests are frozen;
   - every cache file matches its manifest;
   - the design is the fixed one.
2. **The analysis.** `k6_analyse_v02.py` then:
   - checks the freeze record, the frozen block (itself, `m_lib_v04`, the simulator), the run-record hashes, design completeness and B = 2000;
   - applies §5–§7.
3. **Unattended.** The chain has no branch on any result.

**Compute.** About 20 minutes per tracker for loop mode and 5 for decide mode on the laptop. RunPod is not needed, and nothing is spent.

## 12. Deviations

Any change after the freeze is logged with its reason and its timing relative to the outcomes. A change made after seeing outcomes is labelled exploratory, and the frozen analysis is reported as well.

## 13. Response to R09

| R09 | Resolution |
|---|---|
| C1 | C8: exemptions at reference margin 0, the same for every arm. The "matches the fault rule" text is withdrawn. *Superseded in part by §13b MJ1:* the emergency-stop fallback is replaced by the margin back-off (C14), and T11 is now R09b's 576-case grid. |
| C2 | C9: strata computed from the sensor's CTRV. C11: the decision mode carries the confirmatory tests with offset 0. Closed-loop records carry the offset bin; PL (≤ 15 m) is the secondary check, and the offset is reported per arm. |
| M1, M2 | C12: in-path, enforced and satisfied bits. PD = in-path ∩ relied-on ∩ enforced ∩ satisfied. |
| M3 | OC v02 on a development-informed per-cell layout. The HK1a family is power-qualified (≥ 0.80 at 0.15) by a mechanical, count-only rule with a floor F_MIN, and the power acceptance is in §8. |
| M4 | HK3 is no longer progress against B3. M\* − B3 is reported as implied. Feasibility against B0, B1, B4 and B9 is not implied. |
| M5 | §1 states the selection-shift nature of K6a and that HK2 is expected from D07; HK2 is Bonferroni-corrected. |
| M6 | C13: the run is locked to the fixed design; the analysis checks the frozen block, the run records, completeness and B, and compares the sidecar with the freeze record. |
| m1 | The F_MIN floor: an empty or small family fails HK1a. |
| m2 | §3 now says the entry exclusion applies at every delay. |
| m3 | Collision checks run at 5 substeps per keyframe interval (0.1 s). |
| m4 | SD1–SD3, PL, SL1 and E_rec are all coded in `k6_analyse_v02`. |
| m5 | Noted: `check_horizon8_v01` can undercount `extra_new` by one; the cache asserts the line count, so the result is unaffected. |
| m6 | The item npz files and horizon files are frozen. |
| m7 | Rack censoring is applied in `_record`. |
| m8 | "What had been seen" now lists the score threshold and the earlier OC runs. |
| m9 | Entered episodes are counted, not assumed. |
| m10 | The artefact rule applies per delay. |
| m11 | T13 (decision mode) and T12 (bits) were added. T7 stays a no-selection check. |
| m12 | The correlation assumption and the independence of arms are stated in §8. |
| m13 | The wording is fixed in §4. |
| m14 | §1 states that K6's M\* is a new cross-fit. |

## 13b. Response to R09b

| R09b | Resolution |
|---|---|
| MJ1 | C14 (D09 v05): the margin back-off before the emergency stop, with the infeasibility indicator unchanged. On R09b's widened grid (576 cases × 9 doses), no case free of collisions at dose 0 collides at a larger dose, against 16 such cases before. T11 is now that grid, and 170 of its cases collide at some dose. Fallback-related collisions are flagged, and closed-loop safety contrasts are declared descriptive, not calibration effects (§1, §4.3). |
| MJ2 | "What had been seen" item 6 gives the history of HK3's endpoint and arms, with the development values. B6 is excluded from HK3 with the reason and the foreknowledge stated; "operability against B6" is not claimed. §9 and the iteration count are corrected. |
| MJ3 | C15: HK1a fails on a flag in any evaluable cell. Bounds for all evaluable cells are reported (`HK1a_Mstar_all_evaluable`). The OC's A1 counts the union. |
| m1 | §1: HK3 against B0 on T3 is near-implied. |
| m2 | The power rule uses ρ = 0.5; §5 says "under this model". |
| m3 | The informative acceptance criterion (T1 family contains the moving-car lateral cells); §8 calls A1 a sanity check. |
| m4 | F_MIN = 6; zero ratios are floored at 0.02 in the OC. |
| m5 | T12 produces and asserts every value of the in-path, enforced and satisfied bits. A mutant with the bits hard-coded to 1 now fails it. |
| m6 | Done: the manifests given to the analysis must be frozen; run records hash their outputs, and the analysis checks them; the tracker pairing is checked; the tag order is checked; the freeze reads only the frozen OC. |
| m7 | §8: the weakest contrasts are corrected, and the joint power of HK3 is reported. |
| m8 | "What had been seen" item 2 describes the new 8-step build. |
| m9 | §5 (HK2) states which M\* family is meant. |
| m10 | §2 discloses the decision-mode replay devices. |
| m11 | Usage lines and the T10 name are fixed. E_rec (S6) is reported beside E_scene. |

## 13c. Response to R09c (`70_TESTS/R09C_K6_PREFREEZE_CHECK_v01.md`; verdict "fix first: N1, N2, then freeze")

R09c verified all 14 R09b findings as fixed and found no new critical or major problem.

| R09c | Resolution |
|---|---|
| N1 | §4.2 now defines an infeasible decision at the arm's full margin, with the back-off described. The §13 C1 row is marked superseded in part. |
| N2 | `outcome_summary` reports `backoff_frame_share` and `emergency_stop_frame_share` per arm. The analysis was re-run on the development runs (`--allow-dev`) without error. |
| N3 | §1 "Not claimed" states the exposure of the fallback window (39–95 % of the margin arms' driving time). |
| N4 | Not changed. T12 asserts that both values of each bit occur, not that each record carries the right value. The per-record correctness of the bits rests on the code review (R09b and R09c checked the encoding) and on T8 and T13. |
| N5 | The tracker pairing is now checked by content: the fits file's `tags`, and the `experiment` in every cache manifest. |
| N6 | The test header for T11 is updated; "What had been seen" is renumbered; `try_twolevel` is counted once (as dev v05b). |
| N7 | Two hand edits are not reproduced by a patch script: the split of the tracker-pairing assertion in `k6_analyse_v02.py` into `same_tracker`, and the renaming of the T10 result key with `sed`. Both are recorded in D09 v05 §3. The frozen files are what bind the run. |
| N8 | Noted: `k6_cache_v02.py` changed after the caches were built, but only in its usage line; restoring that line reproduces the old hash exactly. |

FROZEN_HASHES_BEGIN
257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_sim_v02.py
2821511f35e51520fc7b724dd5dc9b9ab7d02c50ac9acd38c98d79b64a982cf3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_run_v02.py
9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_analyse_v02.py
19ec27bfa6786132947b4d0c81f0f73a755877233212c10e5996b7e9d2a7e788  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_fit_v01.py
d1c45eb558a6e7472270933cf91bd21ea02de180849dada8e7e28d8077b4599b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_items_v01.py
a4f7bd977486df13fac977b0be6dcbc5c5f3f47275d6958d1f57095602686c3f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_cache_v02.py
0349a788f9f3bcecead0c806d1b45ba9bbe36ea366c59b00f3f768880c735ff5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_ego_prep_v01.py
d43f9cdac2a9b7389410e2450137bdbde896e687dfa2982f5608bdba355d159c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\check_horizon8_v01.py
a5c7cf8608927317fd1ea168ff0d653af314daaa03241c2e1102638ee9945d49  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\run_k6_horizon_v01.sh
201ea1fa0de834f60661e12aceebd1c6688791d64e465f0cef1361e8b5ed7849  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\run_k6_prep_v01.sh
d53ac74fadbb7a17c092e8d1df8cfc173307762ee8e6395fb05f05429dc4d2ac  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\run_k6_cache_v02.sh
0958a020754b0578dbcaa102994ff9e065dcce0126850962c1b6a2d8bd90b6ba  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\run_k6_main_v02.sh
acec42512d03278f8a2805c95b21b9cdc74bbd1657ac450d334635e9e12e7219  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_freeze_v02.py
07957ffe115f1980b8c88f1bb37336f7638c37733cec9f8c9e95b600f73125f3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_sim_v01.py
287151ab41c9b0f8e056e46d6f07d6d98c6c17da8c0f3f7acfa17074d166f5b4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\k6_cache_v01.py
619af3ae094ae285870843134ed1d0da9c93c1055c9a73a658b4379b5dcefb03  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\test_k6_sim_v02.py
4405a0d380bc660b8c13125690eeaf261af7abbd003b733d3737e406e011c009  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\k6_oc_v02.py
10a9ca95bb7da7be3e03f76fff3e5ba37f28420820f3eca684572ea2272a5a83  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\k6_dev_check_v02.py
5c3cae576de1d17491a7100ddb68aefd4cc24198a744e7eac42bc15f2a9049c2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\make_k6_sim_v02.py
d64af0e6eb46959eaed02bbd6adc57cadfe7e6bb7bd7df2fa8189569d6cdcb52  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\make_k6_sim_v02_step2.py
26042312781bd63ec16131ced40c8277c1cf0d534fd0ce519f22a0cab8306986  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\make_k6_sim_v02_step3.py
6e94e700b7f4c056a303586a3e54018d7d9ccf7ba7218b4adc5fa85209423c21  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\make_k6_analyse_v02.py
0e44d2c1379983d1ef24d36af50fbfd5222fa71c7f4643c51a49b5f23c3db080  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\make_k6_freeze_main_v02.py
0b28c4d953203b9a2a64737df8aba3c40798bef1ee28aa9a45f13b7d44641fd6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_k6_analyse_v02_r09b.py
bc869d9623c46f120bc17b3cfd52012eb33bc9e8544f9e003e5fd328b5fb17d7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_k6_run_v02_r09b.py
2ddd942529485621d2502c78d4f7f639138dce844984d804b3a4e6799372313b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_test_k6_sim_v02_r09b.py
da02cd0221ea3fb2529d00fabd2d231e743700120f36bfc2fe171d02a2dcd7a5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_test_t10_t12.py
c8ff1350e9cf284da2c368445c32ce60eb126d09a195461dc3b342ca5cdcd9b7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_oc_analyse_r09b.py
7fac00db74c047c6d65e72916de7e5d0328f67621a30da9fc8efebf397d9435d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_r09c.py
c769d40b264cccc2d58628d656601fa1e8cbaa8664b5a240e79b5c7a68f5c1e3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_plan_v02_r09b.py
03f7620285e7b2f8672db738331b5380d0661a5c7bf89c21a41960bbb0b2cd89  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\k6\tests\patch_plan_v02_r09b_part2.py
5db8b11681a28dfc081aeb610ffb1a280efb828c564dc6d8c29f79bc04d60792  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_horizon_prep_v04.py
f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_lib_v03.py
d0d3b91c30ee78c277639ecbd94b69397bf6bc4153752b3ebd070288e5894b89  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_gt_prep_v03.py
6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_lib_v04.py
67bf52a950e299d3775ee9f8b357dceb674a14ac2689d087a8ef1af189ec633f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_data_v04.py
af3cb24a53a153e31e7a2fe421622e3eaeac801732dc5069c9ef7adb5e83f2b6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\90_DECISIONS\D09_K6_HARNESS_DESIGN_v01.md
01819272c3d17ed0b86d92789bc736307b7084e754ad93e2abd8281e07c17ea2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\90_DECISIONS\D09_K6_HARNESS_DESIGN_v02.md
c7d8c5b019f699f2b31a9a012d7057bc8f49a23505cafc2181051d51d84995de  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\90_DECISIONS\D09_K6_HARNESS_DESIGN_v03.md
70d995943ad1b01b9a6f3aaaa07d7f3cd75c48afc30275521087379750e5407a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\90_DECISIONS\D09_K6_HARNESS_DESIGN_v04.md
f9c07183710482c2fd465fc2c402d97cf25f8af0ffde620cd111f5dd4f63a559  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\R09_K6_PREFREEZE_REVIEW_v01.md
1064d57668b42f21f4660a4fd9cf676dde1098ac542b9ce57465630a24c0ccc1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\R09B_K6_PREFREEZE_REREVIEW_v01.md
43317a97deb6daef02bf91e5dc89415a529bb4ccddffdd8600725e492de148f9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\R09C_K6_PREFREEZE_CHECK_v01.md
73123b86336f3f4186c81b159b88b7fe1161b9974e6bee9f8ac076cf02bf3608  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\90_DECISIONS\D09_K6_HARNESS_DESIGN_v05.md
c67e9ba7689d2ee229e1fd738cbdbd47daff214172a97200ad6cb5f3cb379ae7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\k6_scratch\debug_frames_v01.py
160d8d00d200d0231c9236f90125f283082c79851b2bbc93a58277d7548e2687  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\k6_scratch\debug_frames_v02.py
9fecb6ae4c5061df22e505ef5bc589a58fae29b36efd5a792c0e7311fb413624  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_horizon_v01\HORIZON8_IDENTITY_v01.json
165d8a29535f82479ebf03dff422145ff97faf42a975209a9b953009dd3790c2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\k6\k6_ego20hz_v01.json.gz
41ed255f91cfe2bc14d77feca725a7b136c76c8f426946e8ade4b47aad789923  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\k6_scratch\k6_tests_v02.json
8e52748ec54fa7c87090f2240d31adf9ca7eb070ea939007aea549c922cb41a6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\k6_scratch\k6_oc_v02.json
a299f942689dfbbfd66c26cd01b7d021d62a4c1c07111f8ad46e9626ac19777d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\k6_scratch\k6_dev_check_v02.json
df2beb2630017b41ab9b9d29181fb8fcdf13076e33bccfc68416c5165dd4bd4c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\k6_fits_t1_v01.json
02e69efe047e5bad9f9811102ab4f838bc64dc96cd10ec7a146e1a41502ce2c9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\k6\cache_v02_t1_train\MANIFEST.json
e5e838b8f75e9535951048eddb98ab8440d00af29c38f1d60a95aad95e4a3e8b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_summary.json
adae29128a3236c78bc19708376b9b3068de4dca88994f6349af39b564644439  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_horizon_v01\horizon8_t1_train.jsonl.gz
2f6295d91dd43935dfa4fd63717406e9eb70bf7955aa3acbe1fd54aae46e2394  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h0p5s.npz
fc233d786e20de31994b77fef4dc05404abe72d4ad00bf2c2201e121be88ec74  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h1p5s.npz
7512117f61d8729c9a4d276f3af642d1a4a210441e292ef84a068341bfb89a72  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h1s.npz
6aa2ee8fc2251b21d0889c1bc398a1386c87c4063591014917bb0256a6e6d106  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h2p5s.npz
f49b3f2c3e4cfbf8e3bd0dbf6a721fe00516225d813ff2bf8e189c4cbac4339d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h2s.npz
9bd88abb6a03f75fa2db7100e638b4d34996783323ee4cc686745cce64dbac5d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h3p5s.npz
f053303ec06cb1a08b27d216f6908b1c0b5d359a93e8fe300700a8536579da5a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h3s.npz
e9823f2e89b180ab4cf17afa1c44238fc30635bd3475ac151bca1c9d0383eff5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_train_h4s.npz
3fce4b25729a666b7b5e645369dc434fc44b97233b57c0c19df5b23e24259cc7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\k6\cache_v02_t1_val\MANIFEST.json
2d383ef4c02483dd21b420f8334fca30ac55199568b36edc0bcdbf440e0db10a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_summary.json
e6b6ca7d6e7da0908bf64e9b5c2b82408d9079563a4fb156c099a7fbd8bc3a36  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_horizon_v01\horizon8_t1_val.jsonl.gz
99c099f42890ea7ddf97fa04a12f4b264c6f22c79761198f5b10fefae2d5c42b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h0p5s.npz
f6d46cd8969e7fac60d5c893437f9138bef94a25e6221c83784b9cd1dcffe24e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h1p5s.npz
fd8375c479412df6fbbc3f63cd8e26e3beff9e5df695da62544f455c4dfbd482  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h1s.npz
d3a0012746a3fc41f3946fec15d07a3aa11d13fb59bb7985c3f15c309c919924  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h2p5s.npz
17d29a6fbea5e65a14313abbc06801353fcb650f7250e4d495c9c7fe9ef3f90d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h2s.npz
0fac3bbbf75a6575f79ebc160341894fd505b3aa947b288d5e3f8a3df79a1563  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h3p5s.npz
8f8ac15d33ba7a397bf851e96f90d8a0542b4c53e26b29c2324fa36fddbdd100  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h3s.npz
5cfe7329857cfaf89f526f61df18ff25c72343b1afc9f8914fa031b689e9aac5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t1_val_h4s.npz
c771b0b5483280d1bf8766f03809a8e629749acbd188ee7dbe0c994d414c127b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\k6_fits_t3_v01.json
0988453cc5885b6e1e91b6920200fe6fbb6282aa5f0295d6bf8d9f242a969635  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\k6\cache_v02_t3_train\MANIFEST.json
b65207f399e59cd560eb04453c246fc2f7096c2d73f1fa9f0e63b7d059da2e42  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_summary.json
fa747788204b1b058bb7c4f95f6c23dfc800856f399d845d41de2e47006ffcbb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_horizon_v01\horizon8_t3_train.jsonl.gz
d82da392f9dacd0057cd796123336506d4295b4272dd73412616e7e9873f6351  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h0p5s.npz
9a50f30664831f69f185f00bb9d483f1b686b70a0a80f849484a758edf10526a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h1p5s.npz
1e1f402f2c49b683f20e0ffe7f5778ab75e9b8bddbca2d3334e512356c183df5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h1s.npz
eac8461af24472b2dbfbd9334df2ec0081f730de0477911947bfd966ceb0a03c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h2p5s.npz
908cd35033ca2ad75ce8f2517e349ef0f3400cda5954793451704f66687c5919  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h2s.npz
1dfd70068467d2f858a6d81221dde7f583f0a7f6a9cc21b1b8c27cb1ecc48092  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h3p5s.npz
337f192b1bd8d87ea2bde38d40020713ea9967df0ed5f5045c3e7f396a7b243f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h3s.npz
70835658319a21fb301b304a7cd92c127a09e9363e199a11998a460d4c492082  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_train_h4s.npz
f0be2a92bea3edd35bd9af82624e9aea1c2f996930f90a8165e3e8d298db2a8b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\k6\cache_v02_t3_val\MANIFEST.json
976538ca365550ae0fa808c692a179f344b4a3d215ba770e479be0e1ff405105  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_summary.json
7e7a064d9f477b62f445d8eea4018361ac7050e04206e69384d09540135087e7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_horizon_v01\horizon8_t3_val.jsonl.gz
a9b78eec06d37ab21ed98a411b3f30d8d7dc88b0932d88a56d788a917875d331  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h0p5s.npz
ac2113f523a40ff390a2a0a9852dd8a269a42bd70db62e36fa3f2da73a07136f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h1p5s.npz
e1b77313bea52d06666134286404e426025adacabf755751ad8a17250d22aa60  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h1s.npz
ccd82b5ec23500b5741474beb285ab9fe4b33b1d64000620360b70e898c8ec44  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h2p5s.npz
e659e89b7cf439c91d88fbaf868983cb07fcaee8a63e53bb8a7224d4e9bf8c1e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h2s.npz
98c9f5282e45e8ecab4b4613e0f386e8c8c0efccf459ff735678e9b826cabf91  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h3p5s.npz
0cf6d9d49a6a7b5190ee781e2ab5b60d637f4b45962ba05ef01be684312c5b82  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h3s.npz
acc2b86e9b26163174395526deeaab1e6809b3152399ea25786c2fa423d73b37  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\k6_items_v01\items_t3_val_h4s.npz
FROZEN_HASHES_END
