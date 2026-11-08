# X3 plan amendment A3: additions after the independent referee read of v06b (7 Nov 2026, 15:09 EST)

**Status.** It amends `X3_POSTREG_EXPLORATORY_PLAN_v01.md` (38e2526d…).
- **When and why.** It was written after the independent referee read `70_TESTS/V06_REFEREE_REVIEW_v01.md` (59956973…), to answer its concerns 3, 4, 5 and 7, and hash-locked **before any of the quantities below was computed for an X3 arm.**
- **What was already known.** For the arms of record, progress and V2_exec already exist in the analysis of record (`c1_analysis_csv_r1/k8_within_lt3d_t*_decide_{arms,v2}.csv`). The lead read them before writing A3; they are outputs of record and are reported as such.
- **Label.** Everything here is labelled **"added after review"** in the paper, not pre-specified.

## (i) What an infeasible decision costs in this planner

**For every arm:**
- of record: M\*, B0, B1, B3, B4, B6, B9, RETUNED, the B0 sweep and Z0;
- X3: the matched-validity composites of (a), B5, B7, B8, both Q-refit arms, d1, d2, and the learning-curve composites at n = 50, 100 and 200.

**On T1 and T3, from the decision-mode runs, by the analysis of record's own definitions (`k8_analyse_v04`):**
- the infeasible-decision rate;
- the progress ratio;
- the mean executed back-off level;
- V2 (relied constraints at full margin);
- **V2_exec** (relied constraints at the executed margin);
- V2_viol;
- the share of decisions with a minimum enforced gap < 1 m.

**Paired against M\*,** with log-bootstrap 95 % intervals (B = 4000, seed [20261201, i, 9]): the progress ratio and V2_exec.

**Reading, fixed now:**
- If the progress ratio differs by less than 0.02 between M\* and an arm, infeasibility has no progress cost in this leashed replay, and the paper says so.
- In every case the paper states that an infeasible decision is one at which the planner cannot keep its per-constraint risk statement (Proposition 1 covers feasible decisions only). It also reports V2_exec without ranking arms on it.

## (ii) Matched validity, re-read on the partitions no method used

The screen of analysis (b) is applied to:
- the matched-validity composites of (a): B6 on T1 and T3, and RETUNED-HK1 on T1;
- the passing in-sample grid points of (a);
- B8.

The same partitions, bins, flag rule and seeds as (b) are used. Each arm's flagged cells are reported next to M\*'s.

## (iii) The quantity the certificate is about

- **What is computed.** M\*'s cross-fitted exceedance on its **own calibration items**: every separating axis at the reference pose, not the relied records. It is computed per own-threshold stratum (Proposition 6's quantity: log-weighted, held out by fold), with one-sided simultaneous sup-t flags at 0.95 over the evaluable strata, and the share of items in fallback strata, on T1 and T3.
- **Reading.** This is a consistency check of the theory on the data. It is not a test of the planner-facing claim.

## (iv) Multiplicity across partitions

As a sensitivity for (b), M\*'s and every arm's partition flags are recomputed with the simultaneous level corrected across the 7 partitions (one-sided 1 − 0.05/7 per partition).

## Unchanged

The plan's stamp, integrity checks, imports-only rule and new-files-only rule.
