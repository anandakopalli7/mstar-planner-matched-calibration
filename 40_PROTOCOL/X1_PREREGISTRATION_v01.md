# X1 pre-registration: decision-projected calibration audit on real nuScenes val data (v01, 30 Oct 2026)

**Status.** This file is frozen read-only, with its SHA-256 recorded in `X1_PREREGISTRATION_v01.sha256`, before any U, NEES or exceedance value is computed. Only cell sizes are looked at before the freeze (§12).

**Purpose.** Decide GO criterion **G1**, "the problem exists on real data" (D03 §5), for the stack A-N3 would study.

## 1. Data and stack

| Item | Value |
|---|---|
| Detections | CenterPoint (flip), `infos_val_10sweeps_withvelo_filter_True.json`, SHA-256 `4186f748…903e`; matches the archive's 10 Oct record |
| Tracker | CANMOT at `515d0792…`, devkit `e4818ff9…`, experiment `paper/local/canmot/sc` (A-N3's approved raw stack). Q was tuned by Bayesian optimisation for **AMOTA on val** (`src/optimize.py`, objective = AMOTA). R is the trainval sample covariance. The stack is therefore tuned in-sample on val for tracking accuracy, not for calibration. |
| Export | `50_CODE/x1/x1_export_val_v01.py` → `60_RESULTS/x1_export_val150_v01/`. This line's own run, with the P/F/T/C criteria of the archived harness. |
| Ground truth | `50_CODE/x1/x1_gt_prep_v01.py` → `30_DATA/x1_gt/x1_val_gt_v01.json`: tracking classes, ego pose at the LIDAR_TOP keyframe |
| Scenes | the devkit's 150 val scenes |

**Known limits, stated in advance.**
- Val has been looked at before: the archive's A-M02 was an exploratory NEES study.
- The tracker's Q was tuned on val.
- X1 is therefore confirmatory **with respect to this plan**, not with respect to the data.
- The population is these 150 scenes and the same 18 drives (transductive).

## 2. Units

The unit is an exported track record r at keyframe k of scene s.

**Frame-0 exclusion.** Frame 0 of each scene is excluded from all analyses. It has no ego-motion history, and its tracks are initialisations.

## 3. Pairing (track ↔ ground-truth instance)

**Ground-truth set.** Annotations of the 7 tracking classes with lidar + radar points ≥ 1. No range filter is applied.

**Assignment.** Each scene is processed in time order. At frame k, separately for each class:
- Hungarian assignment (`scipy.optimize.linear_sum_assignment`) on BEV centre distance, with a gate of 2 m.
- The candidates are exported tracks not yet paired, and instances not currently paired to a live track.
- A live track is one exported at k.

**Persistence.**
- Once formed, the pair (track, instance) is kept for the track's whole life. No re-gating is applied, so large later residuals are kept, not truncated.
- At later frames, the residual uses that instance's annotation at the same sample.
- If the instance has no annotation there, or the annotation has 0 points, the record is **censored**. Censored records are counted.

**Reported counts.** Unpaired records (false or unmatched tracks); ID switches (an instance paired to more than one track over time); the censored share.

**Sensitivity.** The analysis is repeated with a 4 m gate.

## 4. Statistic

**Notation.**
- p_e: the ego BEV position at k.
- m̂: the track's BEV centre.
- Σ̂: `cov9[0:2, 0:2]`. CANMOT's P is in the global frame, and the measurement order is x, y, z, w, l, h, vx, vy, ry.
- ψ: the track's yaw, from its quaternion.

**Axes.** Longitudinal a_L = (cos ψ, sin ψ); lateral a_T = (−sin ψ, cos ψ).

**Orientation.** Each axis is oriented **toward the ego**: a* = a · sign(aᵀ(p_e − m̂)), with + if the product is zero. This uses estimates only.

**Projected standardised error.**

U = a*ᵀ(X − m̂) / √(a*ᵀΣ̂a* + σ_a²),

where X is the ground-truth BEV centre. U > 0 means the object was truly closer to the ego along that axis than the tracker reported.

**Annotation noise.** σ_a = 0.10 m is assumed. Adding it to the denominator makes "fails" verdicts conservative.

This U is P01 Theorem 1's projected statistic, with the planner-relevant (toward-ego) upper tail.

## 5. Cells

**Primary family (18 cells), defined from estimates only. Ground-truth class is never used.**
- Predicted class: **car**; **pedestrian**; **other vehicle** (truck, bus, trailer, motorcycle, bicycle).
- Estimated range ‖m̂ − p_e‖: **< 20 m**; **20–40 m**; **≥ 40 m**.
- Axis: longitudinal; lateral.

**Restriction.** Paired, uncensored records in the **in-path subset** (§6), frames k ≥ 1.

**Eligibility.** A cell gets a verdict only if ≥ 39 distinct scenes contribute at least one record (Prop. 6 floor for δ = 0.05). Other cells are "estimate only".

## 6. In-path subset (information-measurable)

**Ego motion.** Backward differences between keyframes k−1 and k give speed v and yaw rate ω, with the yaw difference wrapped to (−π, π].

**Ego corridor.** A CTRV extrapolation over 0–4 s in 0.5 s steps (9 poses). The ego footprint is 4.1 m × 1.8 m, inflated by 0.5 m on every side. The corridor is the union of the 9 footprints.

**Object.** The object's footprint (track w, l, yaw) is moved at constant velocity using the track's exported velocity, over the same 9 steps.

**Rule.** A record is in-path if any object footprint intersects the corridor. Polygons are computed with shapely.

**Secondary.** All paired records, with no in-path restriction.

## 7. Primary test: projected tail at δ = 0.05 (P01 Thm 1)

**Exceedance.** Per cell g, E_g is the instance-weighted share of records with U > z₀.₉₅ = 1.6449.

**Bounds.**
- Scene-cluster bootstrap: B = 2000 resamples of the scenes, seed 20261030.
- Simultaneous one-sided 95 % bounds across the eligible cells: max-|t| on bootstrap-studentised statistics.

**Verdicts.**
- **FAILS** if the simultaneous lower bound is > 0.05.
- **OVERCOVERS** if the simultaneous upper bound is < 0.05.
- **CONSISTENT** otherwise.

**Also reported, without verdicts.**
- The scene-weighted E_g (the mean over contributing scenes of the per-scene shares).
- E_g at δ ∈ {0.01, 0.005}. These are estimates only; certification is not possible on val.

## 8. NEES comparison (P01 Thm 2)

**Statistic.** Per cell (pooled over the two axes, so per class × range), 2-D BEV NEES:

ε = dᵀ(Σ̂ + σ_a² I)⁻¹d, with d = X − m̂.

**Verdict.** ANEES with a scene-bootstrap 95 % CI:
- **OVERCONFIDENT** if the lower bound is > 2;
- **UNDERCONFIDENT** if the upper bound is < 2;
- **CONSISTENT** otherwise.

**Disagreement.** In a projected cell g, the NEES verdict of its class × range is compared with g's verdict. The mapping is OVERCONFIDENT ↔ FAILS, CONSISTENT ↔ CONSISTENT, UNDERCONFIDENT ↔ OVERCOVERS. A cell disagrees when the mapped verdicts differ. **k** is the number of eligible cells that disagree.

## 9. Knob prices (P01 Thm 4, empirical)

**Per-cell quantities.**
- m̂_g: the empirical 0.95 quantile of U in cell g (instance-weighted).
- SD_g: the median over records of √(a*ᵀΣ̂a* + σ_a²), in metres.
- The extra margin cell g needs is Δ_g = (m̂_g − z₀.₉₅) · SD_g.

**(a) One global multiplier.**
- c* = max over eligible cells of m̂_g.
- The over-margin it imposes on cell g is (c* − m̂_g) · SD_g.

**(b) One global covariance inflation.**
- s_g is the smallest s with empirical P(U·√(σ̂² + σ_a²)/√(s σ̂² + σ_a²) > z₀.₉₅) ≤ 0.05, found by bisection.
- s* = max s_g.
- The over-margin is the median over cell-g records of z₀.₉₅ · [√(s* σ̂² + σ_a²) − √(s_g σ̂² + σ_a²)].

All prices are reported per cell, with scene-bootstrap 95 % percentile CIs (B = 500).

## 10. Q4 materiality of heterogeneity

**Statistic.**
- H = max_g m̂_g − min_g m̂_g over eligible cells, in SD units.
- H_m = H × median_g SD_g, in metres.
- Each m̂_g is computed on n* randomly subsampled scenes per cell, where n* is the minimum eligible scene count. The point estimate averages 50 subsamples.

**Bounds.** A 95 % percentile CI of H_m from B = 500 scene-bootstrap resamples. Inside each bootstrap replicate, m̂_g averages 10 subsamples.

**Verdicts.**
- **MATERIAL** if the lower bound is > h₀ = 0.10 m.
- **IMMATERIAL** if the upper bound is < h₀.
- **INCONCLUSIVE** otherwise.

**Operating characteristics.** These are checked before the freeze (§12), by simulation at the observed cell sizes. The targets are:
- false MATERIAL ≤ 0.10 when the true H = 0;
- false IMMATERIAL ≤ 0.10 when the true H_m = 2h₀.

If the targets are not met, Q4 is declared **underpowered** here, before the run, and reports estimates only.

## 11. Certification (P01 Thm 5, Prop 6), reported for every eligible cell

**Split.** A random 75/75 scene split, seed 20261030.

**Calibration half.** For each cell with n ≥ 39 calibration scenes:
- the loss is L_j(c), the share of the cell's records in scene j with U > c;
- ĉ_g is the smallest observed U value c with (n/(n+1)) · mean_j L_j(c) + 1/(n+1) ≤ 0.05.

**Test half.** Held-out exceedance at ĉ_g, both instance-weighted and scene-weighted.

**Leave-one-log-out.** For each of the 18 logs, calibrate on the other logs' scenes and test on the held-out log. The distribution is reported.

**Comparators**, each held out the same way:
- the uncalibrated z₀.₉₅;
- the global multiplier c*;
- the global inflation s*.

## 12. Before the freeze

Allowed:
- the export and its integrity record;
- pairing;
- record and scene counts per cell;
- the median exported projected SD per cell (no ground truth involved);
- the Q4 operating-characteristics simulation at those counts. It uses a synthetic scene-clustered model (intra-scene correlation 0.1), 200 replicates per scenario, B = 200 and 3 subsamples per replicate. This cheaper version of the §10 procedure is recorded as such.

Not allowed: any U, NEES, residual or exceedance value.

## 13. Sensitivities (descriptive, all reported)

- Gate of 4 m.
- σ_a ∈ {0, 0.05, 0.20} m.
- Per FAILS cell, the **tipping σ_a**: the smallest σ_a at which the cell's point exceedance is ≤ 0.05.
- All objects (no in-path restriction).
- Records from the active pool only.
- Scene-weighted estimand.

## 14. Integrity gates

- **Q0 provenance.** The export criteria P1–P6, F1–F4, T1–T2 and C1–C5 must all pass.
  - K1 must pass.
  - K2 is the archive's plausibility range, set for 4 smoke scenes. Its value is reported. It does not gate X1: exported track counts above detection counts are native CANMOT behaviour (tentative and coasted tracks). The two-scene code run gave 1.53.
- **Q1 pairing.** If fewer than 50 % of in-path records pair, this is flagged and reported. It does not stop the run.
- **Q2 sample size.** As in §5.

## 15. G1 decision rule (fixed now)

**G1 holds** if and only if both of these hold:
- **(a)** at least one eligible primary cell **FAILS**;
- **(b)** either k ≥ 1 (NEES disagrees in at least one eligible cell) or Q4 is **MATERIAL**.

**G1 is not shown otherwise.** In that case, the pre-declared next step before any GO or NO-GO is:
- a cross-fitted tracker arm: Q and R taken as sample covariances on a random half of the val logs and evaluated on the other half, then swapped;
- plus the all-objects analysis.

**Not in this stage:**
- predicted-horizon (t > 0) calibration;
- any closed-loop quantity;
- misses and false tracks as risks.
