# X3 plan amendment A4: further analyses requested by the independent referee read of v06b (7 Nov 2026, 15:11 EST)

**Status.** It amends `X3_POSTREG_EXPLORATORY_PLAN_v01.md` (38e2526d…) and follows A3 (009a0aad…). It answers `70_TESTS/V06_REFEREE_REVIEW_v01.md` (59956973…): MC4, MC6, minor concerns 1 and 10, and questions 2 and 5.
- **When.** Written and hash-locked **before any quantity below was computed.**
- **Label.** Every result is labelled "added after review (amendment A4)".

Common rules as in plan §0: imports only, new files only, the heavy lock, the integrity checks, seeds [20261201, i, 10 + k] for part k.

## (1) Matched validity on a neutral screen (MC4, question 2)

**The neutral screen.** An arm passes on a tracker when both hold:
- **(a) no flag on the partitions no method uses.** No cell of P1–P7 of analysis (b) is flagged in P_rel, P_near or P_ip, at one-sided simultaneous 0.95 per partition and population. This is (b)'s rule: same bins, evaluability ≥ 39 logs, B = 4000.
- **(b) HK1c.** HK1c holds on each population: the pooled upper bound at 0.995 is ≤ 0.08. The pooled cell uses no partition.

There is no power floor. Each arm's count of evaluable partition cells is reported beside its status, so that an arm judged on few records is visible.

**The families:**
- M\*, refitted at δ′;
- B4, B6 and B9 at δ′, reusing analysis (a)'s refits;
- the B0 scale (the merged α/δ′ curve, re-run with partition counts).

**The grid:** δ′ ∈ {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005}, and the B0 curve's 21 points.

**Selection.** Cross-fitted as in (a): per held-out fold, the least conservative grid point that passes the neutral screen on the other four folds. If no point qualifies, the family is reported as "no matched point", with its in-sample best point. The most conservative point is not substituted.

**Outputs, per family and tracker:**
- the per-fold choice;
- the composite's neutral-screen status;
- the composite's registered-screen status;
- the infeasible rate, progress ratio, mean back-off level and V2_exec;
- M\* (at its own neutral-matched point) minus the composite, paired, 95 % interval, given only when both pass.

**Supplement contents.** The registered-screen version of (a) is redone with this reporting: separating "flagged" from "fails a floor only", and giving no contrast for non-passing composites.

## (2) Loop-mode replay on Argoverse 2, descriptive (MC6, question 5)

The closed-loop non-reactive replay of `k8_sim_v04.run_episode` is run through the X3 runner, not the frozen tool, writing only under `60_RESULTS/x3_explore_v01/`:
- **Episodes.** Delays of 0, 2 and 4 keyframes. Every log of the 375.
- **Arms.** M\*, B0, B4, B6, B8, and the (a) B6 composite on T1 and T3.

The loop endpoints are those of the analysis of record (`k8_analyse_v04`'s loop functions):
- collisions at fault with tracked and untracked agents, per episode;
- progress;
- infeasible frames;
- hard braking;
- the log-replay divergence share.

Each endpoint is reported per arm with a log-bootstrap 95 % interval, and paired against M\*. **No ranking or claim:** non-reactive agents make loop-mode collisions an optimistic and confounded measure (record's LOOP_CONFOUND_NOTE).

## (3) Ego footprint (MC6)

- **The change.** The decision-mode runs are repeated with the ego footprint enlarged from 4.1 × 1.8 m to 4.9 × 1.9 m, with the same 0.5 m buffer.
- **Arms.** M\* (fits of record), B0, B4 and B6 on T1 and T3.
- **Reported:** the registered-screen status, the infeasible rate and V2_exec.

The footprint is overridden in-process in the X3 runner. The frozen file is not edited.

## (4) Heading error, stricter (minor concern 1, question 4)

Extending A1 on the same rebuilt X2 items, per lateral and longitudinal cell, estimate- and truth-oriented, with pointwise scene-bootstrap 95 % intervals (seed [20261211, cell, k]):
- **(4a)** E on items with heading error ≤ 5° and ≤ 10°, with the item counts;
- **(4b)** E along the **annotation's** axes: the projected error along the annotated box's lateral and longitudinal axes, oriented toward the ego. The relevant standard deviation is recomputed along that axis from the same covariance.

## (5) False-positive tracks on AB3DMOT (minor concern 10)

- **The run.** M\* on AB3DMOT (fits of record) is re-run in decision mode with every track that has no annotation match removed from the planner's input. Matched tracks are left as they are.
- **Reported:** the infeasible rate, the progress ratio and the registered-screen status. These are compared with M\* on all tracks (0.891), and with Z0 under the same removal.
- **Reading, fixed now.** If the infeasible rate falls by more than half, false-positive tracks are a main driver. Otherwise the text drops that explanation.
