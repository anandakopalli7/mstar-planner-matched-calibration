# K6 pre-registration v01: closed-loop evaluation of DP-SCRC (31 Oct 2026)

**Status.** This is the version to be frozen. It becomes binding when `50_CODE/k6/k6_freeze_v01.py` fills its hash block and writes its `.sha256` sidecar; the freeze is recorded in `K6_FREEZE_RECORD_v01.txt`, which is not itself frozen.

**What had been seen when this plan was written.**
- No closed-loop episode had been run on any of the 840 confirmatory scenes.
- On those scenes only inputs and counts had been computed: horizons, ego paths, calibration items, caches, fits, and the record layout used by the OC study (§8). The calibration items involve open-loop residuals that the method stage had already analysed.
- Closed-loop outcomes had been seen only on the 10 nuScenes-mini development scenes (§9), which every K6 analysis excludes.

## 1. Question and claims

**Question.** A chance-constrained planner is fed covariances from one of several calibration arms. Three things are asked.
1. Does the open-loop certificate of DP-SCRC (M\*) carry over to the constraints the planner actually relies on in closed loop, where selection can bias it?
2. Where do the practitioner corrections fail in the loop?
3. What does certification cost in progress compared with the certified alternatives?

| Claim | Statement | Test |
|---|---|---|
| K6a (in-loop validity) | On the relied-on near constraints of the executed plans, M\*'s exceedance is not significantly above δ = 0.05 in any evaluable cell, nor in the pooled cell, on T1 and T3 | HK1 |
| K6b (practitioner failure in the loop) | At least one of B0, B1 and B4 is significantly above δ in a cell where M\* is not, with a significant paired difference | HK2 (supportive; it separates GO-A from GO-B) |
| K6c (price of certification) | M\*'s mean progress exceeds that of the certified single multiplier (B3) and of norm-ball conformal (B9), on T1 and T3 | HK3 |
| — (safety outcomes) | At-fault collisions, front buffer intrusions, infeasible frames, hard braking and blocked time per arm | Descriptive only: collisions are too rare for a confirmatory test (§8) |

**Not claimed.**
- A closed-loop guarantee: K6 is empirical.
- Reactive-agent or perception-in-the-loop behaviour: agents are logged and do not react, and perception is replayed from the logged ego (D09 §1).
- Lateral or path planning, since the planner chooses speed only.
- Any statement about the 10 development scenes.

## 2. Harness

The harness is `90_DECISIONS/D09_K6_HARNESS_DESIGN_v03.md`, together with v02 and v01 for the sections they leave unchanged. It is implemented in `50_CODE/k6/k6_sim_v01.py` and tested by `tests/test_k6_sim_v01.py` (10/10 pass).

**World and perception.** nuScenes trainval logs with non-reactive annotated agents. The perception is the real CenterPoint → T1 (CANMOT `sc`) or T3 (Poly-MOT) output at each keyframe, restricted to the deployed output: tracking score ≥ 0.4.

**Planner.** A chance-constrained speed planner along the logged 20 Hz path.
- It replans every keyframe over 4 s, with constraints checked every 0.25 s.
- Candidates: 32 accelerate-then-brake profiles plus an emergency stop.
- A leash keeps it behind the logged ego delayed by d.
- Constraints are object-axis half-spaces with the 0.5 m buffer. A pair is safe if one object axis has gap ≥ margin.
- **Enforced constraints (D09 v03 C6).** A (track, check time) constraint is enforced only if some candidate satisfies it and an ego held at its current position would satisfy it. A conflict the other agent brings to the ego is not the ego's to resolve; this matches the fault rule. The other constraints are counted, not enforced.
- **Choice.** The planner takes the candidate that satisfies every enforced constraint and has the largest mean planned position over the 16 check times. If no candidate satisfies them all, it takes the emergency stop (C7).

**Margins (by arm).**

| Arm | Margin |
|---|---|
| B0 | z·sd |
| B1 | z·√k(group, range)·sd |
| B3 | max ĉ·sd |
| B4 | ĉ_pooled·sd |
| B9 | r |
| B6 | ĉ_L1·sd |
| M\* | ĉ_L0·sd |

Here sd = √(aᵀS_h a + 0.10²).
- The fits are cross-fitted: 5 log folds over the 850 trainval scenes (seed 20261101). Each fold's fit comes from the other four folds, using the method stage's `fit_methods` on the deployed output's items at each of the 8 planner steps.
- There are two references: **Z0**, the mean only (margin 0), and **LOG**, the delayed logged profile without a planner.

**Outcomes.**
- Exact rectangle overlap at every substep.
- At fault: the ego is moving (≥ 0.1 m/s) and the agent overlaps the ego's front half.
- An agent that the LOG reference at delay 0 overlaps is a geometry artefact and is left out of the at-fault counts.
- Front buffer intrusions are agents entering the ego's front half inflated by the 0.5 m buffer while the ego moves.

## 3. Population and episodes

- **Scenes.** The 840 trainval scenes other than the 10 mini scenes.
- **Trackers.** T1 is primary; T3 is the replication.
- **Delays.** d ∈ {0, 1, 2} s, entered at keyframes 0, 2 and 4.
- **Arms.** LOG, Z0, B0, B1, B3, B4, B9, B6 and M\*.
- **Size.** 840 × 3 × 9 = 22,680 episodes per tracker.
- **Exclusions.** An episode is excluded if its entry pose overlaps an agent (d > 0), or if the scene has fewer than delay + 2 keyframes. Exclusions are reported per arm and delay; they do not depend on the arm.
- **Progress** is defined only when the logged travel up to the episode's end is ≥ 10 m.

## 4. Endpoints

### 4.1 In-loop exceedance (HK1, HK2)

**Records.** At each keyframe, for the executed plan, the records are taken over every deployed track that is:
- paired to an annotated object at that keyframe (the method's persistent 2 m pairing);
- annotated with at least 1 lidar or radar point at k + h, for steps h = 1 … 8.

For each object axis that separates the pair at the planned ego pose, the record is D = sign(sep)·a·(g − m), and it exceeds if D > margin.

**Primary population.** The relied-on axis of the (track, step) pair: the axis with the largest gap − margin, among pairs whose footprint gap to the planned ego is at most 5 m (gap bins 0 and 1). All 8 steps are pooled.

**Cells.** Group × axis × motion state, pooled over range: 32 candidate cells, plus the pooled cell over all strata. A cell is evaluable for an arm if that arm's records in it come from at least 39 scenes and 8 logs. Other cells are reported descriptively.

**Estimand.** The episode-level rate: the mean, over episodes with records in the cell, of the episode's exceedance fraction. This is the method stage's scene-level estimand, with episodes in place of scenes.

### 4.2 Progress (HK3)

- The progress ratio of an episode is s(end) / s_log(end − d).
- For each pair of arms, the per-episode differences are averaged over the (scene, delay) keys where both are defined.

### 4.3 Descriptive outcomes

- At-fault collisions per 1000 episodes, with exact Poisson 95 % intervals:
  - with tracked agents (a deployed track paired to the agent in one of the previous two keyframes), the count the covariance arm can affect;
  - with untracked agents, a limit of log-replay perception for a lagging ego.
- Not-at-fault collisions, mostly non-reactive followers running into a slower ego.
- Artefact collisions.
- Constraints not enforced (uncontrollable, or brought to the ego).
- Front buffer intrusions per episode.
- The shares of infeasible and hard-braking frames.
- Mean blocked time and mean |acceleration|.

## 5. Hypotheses

| | Statement | Holds when |
|---|---|---|
| HK1a | M\* is valid in every evaluable cell | no evaluable M\* cell is flagged: simultaneous one-sided 95 % lower bound > δ, or zero bootstrap SE with estimate > δ |
| HK1b | M\*'s pooled exceedance is not above δ | the pooled cell is not flagged |
| HK1 | | HK1a and HK1b |
| HK2 | A practitioner arm fails where M\* holds | for some b ∈ {B0, B1, B4}, a cell flagged for b and not for M\*, with the paired difference b − M\* positive (simultaneous one-sided 95 % lower bound > 0 over the cells evaluable for both arms) |
| HK3 | Certification without strata costs progress | mean progress of M\* − B3 and M\* − B9 each have a one-sided 95 % log-bootstrap lower bound > 0 |

## 6. Decision rule

| Verdict | Condition |
|---|---|
| **K6 GO-A** | HK1 and HK3 hold on both T1 and T3, and HK2 holds on T1 |
| **K6 GO-B** | HK1 and HK3 hold on both T1 and T3, and HK2 does not hold on T1 |
| **K6 NO-GO** | otherwise |

`k6_analyse_v01.decide` implements this table. A NO-GO is diagnosed and a pivot proposed; it is never reported as support for K6.

## 7. Inference

- **Bootstrap.** Log-cluster bootstrap, B = 2000, seed [20261102, tracker index]. A log's weight applies to every episode of every scene in that log, so all delays and arms share it, and the paired contrasts use the same weights.
- **Bounds.** Simultaneous bounds use the sup-t construction of the method stage (`m_lib_v04._simul`), taken over the cells evaluable for the arm or the pair.
- **Progress.** The one-sided 95 % lower bound of the bootstrap mean difference; the two-sided 95 % interval is reported beside it.
- **Multiplicity.** None beyond the simultaneous bounds. HK1 must hold on both trackers, which is conservative for a GO.

## 8. Operating characteristics (`50_CODE/k6/tests/k6_oc_v01.py`; `70_TESTS/k6_scratch/k6_oc_v01.json`)

**Layout.** Each confirmatory scene's open-loop calibration items per L0 stratum, summed over the 8 steps (the deployed output). They are scaled by 0.25 or 1, because the relied-on near records are a subset.

**Simulation.**
- Exceedance probabilities are drawn per scene and cell from a beta distribution with mean p and intra-scene correlation ρ ∈ {0.1, 0.3}.
- Binomial records are drawn once per scene and copied to its 3 delays, the conservative extreme.
- There are 300 datasets per layout, with B = 500.

**Acceptance (checked by the freeze script).** A1: the null flag rate of HK1a is ≤ 0.10 in every layout.

| Layout | Scale | ρ | A1: M\* any-cell false flag | M\* pooled false flag | Power at 0.10 | Power at 0.15 | Power at 0.20 |
|---|---|---|---|---|---|---|---|
| T1 | 0.25 | 0.1 | 0.003 | 0.030 | 0.77 | 1.00 | 1.00 |
| T1 | 0.25 | 0.3 | 0.000 | 0.043 | 0.61 | 1.00 | 1.00 |
| T1 | 1.00 | 0.1 | 0.003 | 0.023 | 0.99 | 1.00 | 1.00 |
| T1 | 1.00 | 0.3 | 0.003 | 0.030 | 0.85 | 1.00 | 1.00 |
| T3 | 0.25 | 0.1 | 0.003 | 0.037 | 0.77 | 1.00 | 1.00 |
| T3 | 0.25 | 0.3 | 0.003 | 0.040 | 0.63 | 1.00 | 1.00 |
| T3 | 1.00 | 0.1 | 0.003 | 0.033 | 0.99 | 1.00 | 1.00 |
| T3 | 1.00 | 0.3 | 0.007 | 0.043 | 0.85 | 1.00 | 1.00 |

**Reading the table.**
- **Acceptance.** A1 holds in every layout; the largest false-flag rate is 0.007.
- **Pooled cell.** It is flagged at about its nominal size (0.02–0.04).
- **False NO-GO probability.** The chance that a valid M\* fails HK1 on at least one of the two trackers is about 1 − (1 − 0.05)² ≈ 0.10, dominated by the pooled checks.
- **Power.** A practitioner cell in the loop at 0.15 or above is found with power 1.00. At 0.10 the power is 0.61–0.99, depending on how many records the loop yields and how strongly they correlate within a scene.
- **Planted cell.** car|lat|turning has records in 300 (T1) and 338 (T3) scenes.

**Safety outcomes.** Collision power is not claimed. On the development scenes no arm had an at-fault collision with a tracked agent in 30 episodes (§9), so even 2,520 episodes per arm can bound only rates of about 1–2 per 1000.

## 9. Development scenes (harness diagnostics, not evidence)

The development record is `90_DECISIONS/D09_K6_HARNESS_DESIGN_v03.md` §0–§1, with data in `70_TESTS/k6_scratch/k6_dev_check_v01.json`. These are the 10 mini scenes × 3 delays, under the final rules.

| Arm | T1 progress | T1 infeasible frames | T3 progress | Tracked at-fault (T1 / T3) | M\*-type in-loop rate, T1 / T3 (episode level, near relied-on) |
|---|---|---|---|---|---|
| Z0 | 0.912 | 0.007 | 0.962 | 0 / 0 | 0.43 / 0.44 |
| B0 | 0.568 | 0.038 | 0.370 | 0 / 0 | 0.067 / 0.000 |
| B1 | 0.506 | 0.046 | 0.546 | 0 / 0 | 0.026 / 0.040 |
| B3 | 0.384 | 0.016 | 0.350 | 0 / 0 | 0.000 / 0.000 |
| B4 | 0.560 | 0.034 | 0.534 | 0 / 0 | 0.051 / 0.022 |
| B9 | 0.442 | 0.028 | 0.426 | 0 / 0 | 0.000 / 0.000 |
| B6 | 0.571 | 0.036 | 0.505 | 0 / 0 | 0.020 / 0.017 |
| M\* | 0.603 | 0.029 | 0.517 | 0 / 0 | 0.021 / 0.017 |

**How these were used.** They were used only to fix the planner rules, as D09 v03 §0 records. Nothing in §4–§7 was chosen from these values. Ten scenes from 8 logs cannot support any statement about the arms.

## 10. Sensitivities (descriptive; they do not enter the decision)

- In-loop exceedance:
  - with the pair gap ≤ 2 m;
  - on every relied-on record whatever its gap;
  - per planner step;
  - at delay 0 only;
  - as the record-pooled rate Σ exceed / Σ n.
- B6 against M\*: the motion-state option, in progress and in-loop exceedance.
- M\* against B0, B1 and B4 in progress: the price of validity against arms that under-cover.
- T3 against T1, for every endpoint.

## 11. Run procedure

1. `50_CODE/k6/run_k6_main_v01.sh` runs `k6_run_v01.py` for T1, then T3, with 6 workers on this laptop. Each run refuses to start unless:
   - the plan's sidecar hash matches;
   - every file in the block is unchanged;
   - the fits, simulator, runner and cache manifests are among the frozen files.

   Every cache file must also match its manifest hash.
2. `k6_analyse_v01.py` then applies §5–§7 and §6's table, and refuses runs whose record does not carry the frozen hash.
3. The chain runs unattended and has no branch on any result.

**Compute.** About 20 minutes per tracker on the laptop (§9). RunPod is not needed, and nothing is spent.

## 12. Deviations

Any change after the freeze is logged in a deviation file with its reason and its timing relative to the outcomes. A change made after seeing outcomes is labelled exploratory, and the frozen analysis is reported as well.

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END
