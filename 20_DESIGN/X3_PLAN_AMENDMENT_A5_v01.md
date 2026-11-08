# X3 plan amendment A5: the neutral screen without the partitions related to M\*'s strata (7 Nov 2026, 18:21 EST)

**Status.** A5 amends `X3_POSTREG_EXPLORATORY_PLAN_v01.md` (38e2526d…) and follows A4 (ab19dd66…). It answers the referee read of v06c (`70_TESTS/V06C_REFEREE_REVIEW_v01.md`, new major concern N1, minor concern 22) and the number trace of v06c (`70_TESTS/V06C_NUMBER_TRACE_v02.md`).
- **When.** Written and hash-locked **before any cross-fitted quantity below was computed.**
- **What was already seen.** The referee re-read A4(1)'s *in-sample* curve table with P1 and P3 dropped. The sign of every M\* − comparator difference survived in sample; the T1 margin against B6 shrank from 0.23 to about 0.07. The lead read that report before writing A5. No cross-fitted value under A5 exists.
- **Label.** Every result is labelled "added after review (amendment A5)".

Common rules as in plan §0: imports only, new files only, the heavy lock, the integrity checks before and after, and seeds [20261201, i, 20 + k] / [20261202, i, 20 + k] for part k. No new decision-mode or loop-mode run is needed; A5 re-screens the runs with partition counts that A4(1) made (`runs/a4n_t1`, `runs/a4n_t3`, and the M\* refits at δ′).

## (1) The neutral screen without P1 and P3

**Why.** Two of the neutral screen's seven partitions are coarse functions of the variables that define M\*'s course-change state:
- **P1, track speed,** against M\*'s "static" state;
- **P3, track age,** against its "new" state.

**The reduced screen.** It is A4(1)'s screen restricted to P2 (track length), P4 (detection score), P5 (ego speed), P6 (annotation lidar points) and P7 (city):
- no flagged cell in P_rel, P_near or P_ip, at one-sided simultaneous 0.95 per partition and population;
- HK1c on each population.

The bins, evaluability (≥ 39 logs), flag rule and B = 4000 are A4(1)'s, and there is no power floor.

**Families and grid.** As A4(1):
- M\*, B4, B6 and B9 at δ′ ∈ {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005};
- the B0 curve's 21 points.

**Selection.** Exactly as A4(1): per held-out fold, the least conservative grid point that passes on the other four folds. A fold without one gives "no matched point", with the in-sample best reported and no substitute.

**Outputs, per family and tracker:**
- the per-fold choice;
- the composite's reduced-screen and registered-screen status;
- the infeasible rate, progress ratio, mean back-off level, V2, V2_exec and V2_viol;
- M\* (at its own reduced-screen matched point) minus the composite, paired, with a 95 % log-bootstrap interval, only when both have a matched point.

## (2) Which partitions set each matched level

For A4(1)'s screen and for A5(1)'s, in sample and per fold, list the flagged cells (partition, bin, axis, population) at the grid point just less conservative than each family's matched point: the flags that stop it there. This is a read-out of existing screens; nothing is refitted.

## (3) Exceedance measures of the matched points, for Fig. 4

For M\* at its matched point and for every family's composite, under A4(1) and under A5(1), compute by `k8_analyse_v04`'s definitions:
- V2 (P_rel, at full margin);
- V2_exec;
- V2_viol;
- the infeasible rate;
- the progress ratio;
- the share of decisions with a minimum enforced gap below 1 m.

These are read-outs of existing runs, with no new runs.

## Reading, fixed now

- **The sign holds:** if, under A5(1), every M\* − composite interval lies below 0 on both trackers, the paper states that the back-off advantage on the neutral screen survives removing P1 and P3. The abstract then gives the range over both screens.
- **The sign does not hold:** if any interval includes 0 or lies above 0, the paper states that the advantage is not robust to removing P1 and P3 for that family and tracker, and names them. The abstract's exploratory sentence is then reduced to the families for which it holds, or dropped.
- **In all cases:**
  - V-E(a) reports which partitions set each matched level, from (2);
  - the label "partitions that no method uses" becomes "partitions that no method stratifies on directly", with P1 and P3 named as coarse functions of M\*'s course-change variables.

## Unchanged

The plan's stamp, the integrity checks, the imports-only rule and the new-files-only rule.
