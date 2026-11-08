# X1 pre-registration v02: decision-projected calibration audit on real nuScenes val data (30 Oct 2026)

**Supersedes v01** (kept, never frozen). Every change answers review R03 (`70_TESTS/R03_PREFREEZE_REVIEW_v01.md`): 2 critical, 9 major and 25 minor findings. The fix log is in §17.

**Freeze.**
- This file is hashed together with the code and inputs listed in §0, after the export has passed Q0.
- The text governs. Any code change after the freeze is a logged deviation.
- The file's hash is also recorded outside this folder: in the session hand-over note and in memory.

**Purpose.** Decide GO criterion **G1**, "the problem exists on real data" (D03 §5), for the stack A-N3 would study.

**Two pre-registered families,** both fixed before any outcome is seen:
- **t0:** the tracker's output covariance at the current keyframe.
- **h2s:** that output propagated 2 s ahead (4 keyframes). This is what a planner consumes. Propagation uses CANMOT's own constant-velocity model and process noise Q, with no measurement update (`x1_horizon_prep_v01.py`, the same algebra as `ExtendedKalmanFilterRotate.predict`). Its truth is the paired instance's annotation at k + 4. Its ego is the **CTRV-predicted** ego pose at k + 4, computed from keyframes k − 1 and k. This is the planner's nominal own-motion and is I_k-measurable. The logged future pose is not used, because a human driver chose it knowing the true object positions (R04 m10).

**Multiplicity.** Bonferroni across the two families: every simultaneous band is at **97.5 %**, and the material-margin lower bound in §15 (a2) is one-sided at **98.75 %**. G1 holds if **either** family meets §15. The chance of G1 holding by error is therefore controlled at the same overall level as a single family at 95 %.

**Family h2s in detail.**
- Records are the t0 records (k ≥ 1, in-path at k, rack exclusion) whose scene has a keyframe k + 4.
- A pair is censored at the horizon when the instance has no annotation with ≥ 1 point at k + 4, or when it is in a rack.
- Cells, axes, filters, nulls, NEES, prices, certification and sensitivities are the same as for t0, applied to the predicted mean and covariance. The range bin is the predicted range to the ego centre at k + 4.
- 1 s and 4 s predictions are exported for description only.

## 0. Frozen code and inputs

The SHA-256 values are inserted by `50_CODE/x1/x1_freeze_v02.py` immediately before the freeze, in the block below. The full analysis refuses to run if any listed file's hash differs.

```
FROZEN_HASHES_BEGIN
setting  band=linear
9728e9f518e284e39e522c7252353f1342e7b9ffd682a742cd1eba9b646f8571  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_lib_v02.py
a2d613f047ae09e37fb03291ef635ce6ac3055d67e49346a7fac88333a128538  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_prefreeze_v02.py
b59dd08a407b8907d93386e7b136af973a5889444c3a0c84053d3e8a4a42bf64  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_full_v02.py
0e1d65e9db9e9bdd2eba4fac1cbf415bd82b2e3b3feece70d77d522d15a4f9d8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_export_val_v02.py
a92c62074a8d93f0a6773b28da872f9e3cb7b5e75e6f0cdce52cb5917897bc4f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_split_detections_v01.py
2188624b3327658f6f56a95ab2e725c432f69d1816eb931445ccb20b62199e79  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_gt_prep_v02.py
68e970664d7b18389119b7865dfe00dbf25a4dc7761c7e39b409007f5025032b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_freeze_v02.py
b823756f19ca23d4d36b6d97249f647182eee20a570c2f92a6149aeb2908c3e6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_horizon_prep_v01.py
5037c2c0bc7140eb72c603b5d16a6cbdf44584b131825debbf1b63e4c1f0df24  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker0\x1_tracks.jsonl.gz
adcd8475ed28bbd818b2bb282053496c65a7459a72b01773c68b25eb8bcc9b24  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker0\x1_export_record.json
2043c203db9c43ba21121c9c9c2c924c4cbffe0c7c161f1731533eee94f8d588  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker0\x1_per_frame.json
42f8433403ec9f0d441c67b2f79f72e8ec8f75a67114b024f9a3f31eaa33ae4f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker1\x1_tracks.jsonl.gz
49236a20107f094a27f9491fab0637a1bc775b15ea5f946d5b4465cb3b02b55b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker1\x1_export_record.json
52874ca85f0f798c2e904d87cd75d4c3d7ac27f29d381c38d9f65ee16e8af6d1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker1\x1_per_frame.json
31e82ce904edf1201b1d89fb8cfc05e43d5cd130a119ecce71dfb9b6b189027a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker2\x1_tracks.jsonl.gz
726bb8bec248583256aec09645abe8a26b7d8460e9c1b1352c819883ce4a33c4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker2\x1_export_record.json
8fbbca8c0b252e609eb96a9ee08dcfe0c6db7ab59e6f5fe41ce73f4d6e91526d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker2\x1_per_frame.json
0c9e4b92bfea0340aaddd37cd756a4fbc99672a6905b0f2a17a82fcad14654e0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\x1_gt\x1_val_gt_v02.json
bdc3211bfbfda652d5e9dab73c45c7132925ca84f869bf45e8e14edeafb1d20b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\nuscenes\v1.0-trainval\scene.json
56bb3f19c8fbba072f1a94c7a437924624344371ed209e912e8408242f4ce008  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\det_subsets_val150\split_receipt.json
e3e5071ea83d4f3a658f05294e608c32e82a8acd3807e298c2600dce95053f70  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1\x1_horizon_v01.jsonl.gz
6c7fa5ade0eef78d974535ad5dd68b0ee79b6bcd4d682d4d8487dbf62da48a73  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1\x1_sizes_v02.json
b26a31dea09d1224d092d8df7a3eeffdca985be43b329c6d86cb45d327c89077  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1\x1_fwer_v02.json
23b47aceacf91ef3e07b04e3665fad82e7730b485f04a932baf10147262aa991  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1\x1_oc_q4_v02.json
4387f15910bd25d606bd1d8eaf02395072aae79f40073718c1fb8c58472796d4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1\x1_selftest_v02.json
FROZEN_HASHES_END
```

## 1. Data and stack

| Item | Value |
|---|---|
| Detections | CenterPoint (flip) val `infos_val_10sweeps_withvelo_filter_True.json`, SHA-256 `4186f748…903e`. This is the researcher's archive in Downloads, and it matches the archive's 10 Oct record. |
| Tracker | CANMOT at `515d0792…`, devkit `e4818ff9…`, experiment `paper/local/canmot/sc` (A-N3's approved raw stack). Q was tuned by Bayesian optimisation for **AMOTA on val** (`src/optimize.py`); R is the trainval sample covariance. So the stack is tuned in-sample on val for accuracy, not for calibration. |
| Export | `x1_export_val_v02.py` in 3 scene-subset workers. The split keeps each scene whole (`x1_split_detections_v01.py`, partition exact). On 2 scenes the output is identical to the single-process run: 4,318 records, all fields except the file-order `seq_id`. |
| Ground truth | `x1_gt_prep_v02.py` → `x1_val_gt_v02.json`: the 7 tracking classes, 274 bicycle-rack boxes, and the ego pose at the LIDAR_TOP keyframe |
| Scenes | the devkit's 150 val scenes from 18 drives (logs) |

**Population.** The analysis is transductive: these 150 scenes and these 18 drives. Val was looked at before (the archive's A-M02, exploratory NEES), and the tracker was tuned on it. X1 is therefore confirmatory with respect to this plan, not with respect to the data.

## 2. Estimand

The estimand is P01 Theorem 1's **I_k-conditional (posterior) calibration** of the projected error along a separating axis. That means calibration given everything the tracker knows at step k, on the toward-ego side.

Fixed-truth calibration (the NEES sense) does not imply it, and it does not imply fixed-truth calibration.

**Two separate safeguards (R03 C1, R04 M1).**
- Under I_k-conditional calibration, the FAILS threshold 0.05 is exact for any I_k-measurable selection (R04 §6).
- The orientation null E⁰ (§6) is a plug-in estimate (truth := m̂) of the fixed-truth exceedance at the estimated geometry. Its candidates are all (record, axis) pairs taken *before* the separating filter. Using max(0.05, E⁰) only adds conservatism; it does **not** bound the fixed-truth orientation artefact (R04 counterexample: 0.315 against E⁰ = 0.175).
- The fixed-truth artefact is therefore excluded by a separate condition, **(a5) in §15**. The failing cell must also FAIL in the **truth-oriented** analysis, where orientation and filter are computed from the ground-truth centre. Under fixed-truth calibration this analysis has exceedance exactly 0.05, so a FAILS there cannot come from orientation.

**Measurability.** Every ego quantity is computed from current and past ego poses (R04 m10):
- the ego centre and the corridor (backward differences);
- for h2s, the CTRV prediction of the ego pose from keyframes k − 1 and k. The logged future pose is not used.

## 3. Records, pairing and selection

**Units.**
- Exported track records at keyframes k ≥ 1. Frame 0 lacks ego-motion history.
- Two-wheeler records whose centre lies in a bicycle-rack box are excluded. So are ground-truth two-wheelers in racks (the devkit's bike-rack filter).

**Ground-truth candidates.** Annotations of the 7 tracking classes with at least 1 lidar + radar point.

**Pairing (primary: persistent).** Scenes are processed in time order.
- At frame k, separately for each class, Hungarian assignment on BEV centre distance with a 2 m gate.
- The candidates are tracks not yet paired, and instances not currently paired to a live track.
- A pair persists for the track's life, with no re-gating.
- A record is **censored** when its instance has no qualifying annotation at k.
- Pairing requires predicted class = ground-truth class. A misclassified track is therefore unpaired, so the analysis covers matched true positives only.

**Flags**, computed per record:
- **contested**: another same-class candidate instance is closer to m̂ than the paired one, or the paired instance is the pair of ≥ 2 live tracks at k;
- **first**: the track's first exported record (its birth);
- **duplicate**: another live track of the same class lies within 1 m;
- **residual > gate**: the pair has drifted beyond 2 m.

**Selection effects, disclosed.**
- First association truncates the residual at 2 m. This is conservative for FAILS and anti-conservative for OVERCOVERS and certification.
- Censoring depends on the outcome: 0-point and coasting periods drop out.
- In-path selection uses estimates only (I_k-measurable), but it conditions the estimand.
- The censored share is reported per cell.

## 4. Statistic and separating axes

**Ego.** The ego centre c_e is the rear-axle pose moved 1.39 m forward along the ego yaw. Footprint 4.1 × 1.8 m, inflated by 0.5 m on every side.

**Track.** m̂ is the track's BEV centre and Σ̂ = `cov9[0:2, 0:2]`. CANMOT's P is in the global frame; the measurement order is x, y, z, w, l, h, vx, vy, ry. ψ is the track's yaw.

**Object axes.** a_L = (cos ψ, sin ψ) with half-extent l/2; a_T = (−sin ψ, cos ψ) with half-extent w/2.

**Separating-axis filter** (estimates only). An axis is kept for a record only if

|aᵀ(c_e − m̂)| > h_obj(a) + h_ego(a),

where h_ego(a) is the support of the inflated ego footprint along a. A record contributes 0, 1 or 2 items.

**Orientation.** a* = a · sign(aᵀ(c_e − m̂)).

**Statistic.** U = a*ᵀ(X − m̂) / √(a*ᵀΣ̂a* + σ_a²), with X the ground-truth BEV centre. U > 0 means the object is closer to the ego than reported.

**Annotation noise σ_a.** No published centre-annotation precision for nuScenes is available to this study, so σ_a is treated as unknown. The primary value is σ_a = 0.10 m. G1 also requires the verdict at σ_a = 0.20 m (§15).

## 5. Cells

**24 cells**, all defined on estimates:
- class group: **car**; **pedestrian**; **two-wheeler** (motorcycle, bicycle); **large vehicle** (truck, bus, trailer);
- estimated range ‖m̂ − c_e‖: **< 20 m**; **20–40 m**; **≥ 40 m**;
- axis: longitudinal; lateral.

**Primary restriction.** Paired, uncensored, in-path (§7) items that pass the separating filter.

**Eligibility.**
- **Verdict-eligible:** ≥ 39 distinct scenes, which is Prop. 6(ii)'s *practical* size; the floor is 19.
- **Certification-eligible** (§11): ≥ 39 calibration scenes after the split. This is a subset of the verdict-eligible cells.
- Eligibility is recomputed for every sensitivity.

## 6. Orientation null (computed before the freeze; no ground truth)

**Construction.**
- For each candidate (record, axis) in a cell, the estimate is taken as a plug-in truth.
- 20 draws are made per item: e ~ N(0, Σ̂ + σ_a² I) gives a pseudo-estimate m̂ + e.
- The separating filter and the orientation are re-evaluated on the pseudo-estimate.
- U⁰ = sign · aᵀ(−e) / √(aᵀΣ̂a + σ_a²).

**Outputs.**
- E⁰_g = P(U⁰ > z₀.₉₅ | kept): the exceedance a perfectly (fixed-truth) calibrated tracker would show at this geometry.
- m⁰_g: the 0.95 quantile of U⁰.

Both are computed at σ_a = 0.10 and 0.20 m.

## 7. In-path subset (estimates only)

**Ego motion.** Backward keyframe differences give the speed, signed by the heading projection, and the yaw rate (wrapped).

**Ego corridor.** A CTRV extrapolation of the rear-axle pose over 0–4 s in 0.5 s steps, with the footprints centred at the ego centre.

**Object.** Footprints moved at constant velocity using the track's velocity.

**Rule.** In-path means any intersection. In-path is computed for every record at k ≥ 1. The paired share among in-path records is reported (Q1).

## 8. Primary test: projected tail at δ = 0.05

**Exceedance.** E_g is the **record-weighted** share of items with U > z₀.₉₅.

**Band.** A **two-sided simultaneous 97.5 % sup-t band** (Bonferroni across the two families) over a family's eligible cells, built from a scene-cluster bootstrap with B = 2000, seed 20261030, and bootstrap SE.
- Its family-wise false-FAILS rate was simulated before the freeze at the observed per-scene counts of each family (§12). The requirement is ≤ 0.025 + 2 MC SE.
- If that requirement failed, the pre-declared logit-scale band is used instead. §0 records which band applies.

**Verdicts.**
- **FAILS** if the lower bound is > max(0.05, E⁰_g).
- **OVERCOVERS** if the upper bound is < 0.05.
- **CONSISTENT** otherwise.
- Cells with zero bootstrap SE are judged on the point value and flagged.

**Also reported:**
- the scene-weighted E_g;
- E_g at δ ∈ {0.01, 0.005}, as estimates only;
- the log-cluster bootstrap verdicts, as a sensitivity.

## 9. NEES (P01 Thm 2)

**Statistic.** Per class group × range, 2-D BEV NEES ε = dᵀ(Σ̂ + σ_a² I)⁻¹d, with d = X − m̂, over the same in-path paired uncensored records. No axis filter is applied.

**Verdict.** ANEES with a marginal scene-bootstrap 95 % CI (B = 2000):
- **OVERCONFIDENT** if the lower bound is > 2;
- **UNDERCONFIDENT** if the upper bound is < 2;
- **CONSISTENT** otherwise.

**Disagreement types**, reported only and not part of G1:
- **type I**: the projected cell FAILS and NEES is not OVERCONFIDENT;
- **type II**: the projected cell OVERCOVERS and NEES is OVERCONFIDENT;
- **power-only**: one side is CONSISTENT.

## 10. Prices (P01 Thm 4) and heterogeneity (K3)

**Per eligible cell.**
- m̂_g: the 0.95 quantile of U.
- SD_g: the median of √(a*ᵀΣ̂a* + σ_a²).
- The **extra margin** Δ_g = (m̂_g − max(z₀.₉₅, m⁰_g)) · SD_g, in metres.
- A scene-bootstrap 95 % percentile CI, with B = 500. Dropped replicates are counted.

**Global knobs, fitted on all scenes** (descriptive, for K3):
- c* = max m̂_g, with its over-margin (c* − m̂_g)·SD_g;
- s* = max s_g, with its over-margin. Inflation searches that hit their cap are flagged.

These maxima suffer a winner's curse. Held-out comparisons are made in §11.

**Q4 (heterogeneity, for K3 only).**
- H_m = (max_g m̂_g − min_g m̂_g) × the median SD_g, computed at n* subsampled scenes per cell.
- The point estimate averages 50 subsamples. The CI uses B = 500 replicates with 10 subsamples each.
- **MATERIAL** if the lower bound is > h₀ = 0.10 m; **IMMATERIAL** if the upper bound is < h₀; **INCONCLUSIVE** otherwise.
- **UNDERPOWERED** if the operating-characteristics targets in §12 were not met.

## 11. Certification and held-out comparison (P01 Thm 5, Prop. 6; K5)

**Split.** A random 75/75 scene split, seed 20261030.

**Calibration half.** Every method below is fitted on these scenes only:
- **(i) stratum CRC:** ĉ_g is the smallest observed U with (n/(n+1)) · mean_j L_j(c) + 1/(n+1) ≤ 0.05, where L_j(c) is the share of the cell's items in scene j with U > c;
- **(ii) global multiplier** c*_cal = max_g q₀.₉₅(U_g);
- **(iii) global inflation** s*_cal = max_g s_g;
- **(iv) pooled single-threshold conformal**, a CGKF-style global conformal correction: one CRC threshold over all eligible cells' items pooled;
- **(v) uncalibrated** z₀.₉₅.

**Test half.** Per cell and method:
- held-out exceedance, both record-weighted and scene-weighted;
- the **margin in metres**: the median of threshold × √(a*ᵀΣ̂a* + σ_a²) for (i), (ii), (iv) and (v), and of z₀.₉₅·√(s*V + σ_a²) for (iii).

**Leave-one-log-out.** Each of the 18 logs is held out in turn; all methods are refitted on the rest. Reported per log: n, held-out exceedance (both weightings) and margins.

**Scope.** Theorem 5's guarantee is transductive within val. It holds in expectation over the split, scene-weighted, for matched uncensored records at logged states.

**K5 is judged only on these numbers**, after review R04 (M2, M3, m9, m11).

**Comparators.** A sixth comparator is added: **(vi) the certified global multiplier**, the maximum over cells of ĉ_g.

**K5 is supported** if and only if both of these hold:
- **(a)** The mean over certification-eligible cells of stratum-CRC held-out scene-weighted exceedance is ≤ 0.05 + 0.01. This is an implementation check: Theorem 5 predicts about 0.024–0.03.
- **(c)** In at least one cell, (iv) pooled conformal or (v) uncalibrated is **significantly** under-covered on the test half: the scene-bootstrap one-sided 95 % lower bound of its record-weighted exceedance is > 0.05.

**Reported, not claimed.** (b) is reported as a **magnitude**: the total margin of (i) against (vi), and against (ii) and (iii), which are uncertified and labelled as such.

**Sensitivity to σ_a.** At t0, σ_a² plays the role of q (R04 M2). The prices, certification and K5 are therefore computed at σ_a = 0.10 **and** σ_a = 0. K5 is claimed only if it is supported at both. K3's heterogeneity is claimed only if the cell ordering of m̂_g agrees at both σ_a values.

## 12. Before the freeze (allowed outputs only)

**Allowed:**
- the export and its integrity record;
- pairing at the 2 m gate;
- per-cell item and scene counts and per-scene counts;
- the median exported SD;
- the orientation null (§6);
- the FWER simulation for §8: scene random effects on the logit scale with τ = 0.5 (robustness τ = 1.0), E = 0.05, B = 2000, 500 replicates;
- the Q4 operating-characteristics simulation at the observed per-scene counts: Gaussian U with intra-scene correlation 0.1, 200 replicates, B = 200, 3 subsamples. This is cheaper than §10, and that is recorded as a limitation.

**Not computed before the freeze:**
- any U, residual, NEES or exceedance;
- contested-pair counts;
- 4 m pairing counts.

The viewed sizes file is hashed in §0.

## 13. Sensitivities (all reported)

- σ_a ∈ {0, 0.05, 0.20} m, and a range- and size-dependent σ_a = 0.10 × (1 + r/40) × (1.5 for large vehicles) m.
- The **point-tipping** σ_a (point exceedance ≤ max(0.05, E⁰)) and the **verdict-tipping** σ_a (first value on the grid {0.10, 0.15, 0.20, 0.30, 0.50, 0.75, 1.00} m at which a FAILS cell is no longer FAILS). "None" means > 1.00 m.
- Gate 4 m.
- **Per-frame re-matching**: Hungarian each frame, 2 m gate, no persistence.
- Contested records excluded.
- First records excluded.
- All objects: no in-path restriction.
- Log-cluster bootstrap.
- **Truth-oriented secondary**: orientation and separating filter on the ground-truth centre. This is labelled not information-measurable.
- The class mix within each cell.
- The share of exceedances that come from records with residual > gate.

## 14. Integrity gates

**Q0.** Every export worker must have `status_X1_gates` = PASS. That covers P1–P6, F1–F4, T1–T2, C1–C5 and K1.
- K2, a plausibility range from the archive, is reported and does not gate. The excess tracks are coasted active tracks.
- After merging, the union must cover all 6,019 val tokens exactly once.
- **C6** (exported centre = filter-state centre, birth records excluded) is computed from the export and reported.

**Q1.** The paired share among in-path records. Below 50 % is flagged, and the run continues.

**Q2.** Eligibility as in §5.

## 15. G1 decision rule (mirrors D03 G1)

**G1 holds** if and only if, in at least one of the two families (t0, h2s), at least one eligible cell g satisfies **all** of (a) and (b). Each family is evaluated separately, with its own nulls, NEES and sensitivities.

**(a) A material, robust failure.**
- **(a1)** g FAILS against max(0.05, E⁰_g) at σ_a = 0.10 m.
- **(a2)** The bootstrap one-sided 98.75 % lower bound of Δ_g (Bonferroni) is > h₀ = 0.10 m.
  - Why 0.10 m: it equals the assumed annotation noise. An extra margin smaller than the measurement's own reference uncertainty cannot be attributed to the tracker.
- **(a3)** g still FAILS at σ_a = 0.20 m, with its own E⁰.
- **(a4)** g still FAILS with contested records excluded.
- **(a5)** g also FAILS in the truth-oriented analysis (threshold 0.05, same band level). This excludes the fixed-truth orientation artefact (R04 M1, §2).

**(b) NEES does not flag it correctly.** For the same g, either:
- **(b1)** the NEES verdict of g's class group × range is CONSISTENT or UNDERCONFIDENT; or
- **(b2)** NEES ranks it wrongly. Another class group × range h with ≥ 39 scenes has **no FAILS cell**, yet NEES rates h as significantly worse: the lower 95 % CI bound of h's ANEES exceeds the upper 95 % CI bound of g's group ANEES. NEES would then direct the fix to h, while the decision-relevant failure is in g.
  - This replaces v02-draft's median rule. A synthetic test with planted over-confidence (`50_CODE/x1/tests`) showed that rule passing by construction: with two eligible groups, one is always at or below the median.

**Not part of G1:** Q4, k and the type counts. They feed K3 and K4.

**If G1 is not shown**, two analyses run before any GO or NO-GO:
1. the all-objects analysis;
2. a **cross-fitted tracker arm**. A random half of the val logs serves as the fitting half; R and Q are re-estimated with CANMOT's own sample-covariance script (`src/canmot/data/script/compute_sample_covariance_nusc.py`) on that half only, and the arm is evaluated on the other half, then swapped. CANMOT's R recipe, sample covariance of detection residuals, is applied to the fitting-half logs. Q is taken as the sample covariance of ground-truth constant-velocity one-step residuals per class on the same logs.

## 16. Not in this stage

- Predicted horizons other than 2 s (1 s and 4 s are descriptive only).
- Any closed-loop quantity.
- Misses and false tracks as risks.
- New-scene (superpopulation) guarantees.

## 17. Changes from v01 (R03)

| Finding | Change |
|---|---|
| C1 | §2 estimand; §4 separating-axis filter; §6 orientation null; truth-oriented secondary (§13); self-tests C1 (artefact reproduced at 0.100; filter gives 0.050; small-offset case matches brute force) |
| C2 | §15 rewritten to mirror D03 G1; Q4 and k removed from G1 |
| M1 | contested, duplicate and drift flags; contested-excluded sensitivity, which (a4) requires; per-frame re-matching sensitivity |
| M2 | §9 type I / II / power-only |
| M3 | §8 FWER simulation with the logit fallback; self-test coverage 0.951 over 1000 replicates (B = 2000) |
| M4 | §11: every comparator is fitted on the calibration half, including leave-one-log-out |
| M5 | §11 margins and the pooled conformal comparator; K5 rule |
| M6 | §0 hashes of code and inputs; the text governs; external record of the hash |
| M7 | σ_a treated as unknown; (a3) at 0.20 m; size- and range-dependent sensitivity; verdict-tipping value |
| M8 | 4 class groups (24 cells); devkit bike-rack filter |
| M9 | P5 v02 rewording |
| post-review, pre-freeze | (b2) rule replaced by a significance-based inversion test after the synthetic over-confidence test showed the median rule passing by construction (`70_TESTS/X1_E2E_SYNTHETIC_TESTS_v01.md`). Second family h2s added with a Bonferroni split (97.5 % bands, 98.75 % margin bound). Both changes were made before any real-data residual was computed. |
| R04 (third proof review: 0 critical, 3 major, 11 minor) | M1: E⁰ reworded as conservative only; (a5) truth-oriented FAILS added to G1. M2: K3 and K5 at σ_a ∈ {0, 0.10}. M3: K5 (c) significance-based; certified global comparator (vi); (b) reported as a magnitude (m9); (a) labelled an implementation check (m11). m10: h2s ego is the CTRV prediction, not the logged future. P01 and P5 wording items (m1–m8) are carried to P01 addendum v04 and P5 v03; they do not affect X1. All changes were made before any real-data residual was computed. |
| m1–m25 | m1 relabelled; m2 two-sided; m3 record-weighted; m4 §3; m5 the "active pool" sensitivity dropped (all records are active) and §14 corrected; m6 in-path for all records; m7 first-record sensitivity; m8 selection paragraph; m9 transductive target plus log-cluster bootstrap; m10 §12 list; m11 ego centre offset and signed speed; m12 zero-SE handling; m13 counts and flags; m14 eligibility recomputed; m15 verdict-tipping value and "> 1.00"; m16 leave-one-log-out scene-weighted with comparators; m17 observed per-scene counts in the OC simulation; m18 `status_X1_gates`, asserted in the full analysis; m19 C6; m20 ground-truth assertions; m21 cross-fit estimator defined; m22–m25 in P5 v02 |
