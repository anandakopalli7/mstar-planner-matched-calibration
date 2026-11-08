# M pre-registration v03: the method stage (31 Oct 2026)

**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v02.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v03.txt`. v01 (`173bca05…`) and v02 are kept unchanged. v02 was never frozen.

**Why v03.** The pre-freeze review R07 (`70_TESTS/R07_M_PREFREEZE_REVIEW_v01.md`; 3 critical, 11 major, 19 minor) found that v02 would have allowed claims its tests could not support:
- validity was claimed from tests with almost no power;
- the transfer test never reached the motion strata;
- the efficiency criterion could not fail;
- the second tracker setting shared its residuals with the first.

v03 changes the claims, the inference and the decision rule, and adds a third tracker setting with different motion models. The change list against v02 is in §13. No real outcome had been computed when any of these changes was made.

## 1. Claims and how far the tests can carry them

| Claim | Statement | Evidence |
|---|---|---|
| **K5** (validity) | DP-SCRC has a per-stratum finite-sample guarantee on the toward-ego exceedance of tracked, still-observable objects (P02 PM1, marginal over calibration). Empirically, its exceedance is **consistent with δ = 0.05** in every evaluated cell on held-out logs (E1, a consistency check) and **after transfer to the log-disjoint val split** (E2), on three tracker settings. | PM1; HM1 (E1); HM6 (E2) |
| K5a (practitioner corrections fail) | NEES-guided scaling (B1), pooled conformal (B4) and norm-ball conformal (B9) each leave at least one cell significantly under-covered **where DP-SCRC is not**, with a significant paired difference | HM2 |
| K5a′ (ablations) | Per-axis conformal (B5), learned-scale marginal conformal (B7), stratified variance matching (B8) and stratified empirical quantiles without the finite-sample term (B10): the same paired test | HM2b |
| K5b (motion state) | Without motion-state strata (B6), at least one car turning stratum is significantly under-covered where DP-SCRC is not, with a significant paired difference | HM3 |
| K5e (price) | Margin ratios against the certified single multiplier (B3), the certified coarse rule (B6c) and the norm ball (B9) | Descriptive, 95 % CIs |
| K5f (generality) | The above on CANMOT (T1), on CANMOT with a data-estimated Q (T2) and on Poly-MOT (T3) | §8 |

**What the tests cannot show, stated in advance.**
- **E1 is pinned for conformal methods.** On held-out logs, a conformal method's pooled held-out exceedance stays near δ by construction. R07's simulation S3 found its across-dataset SD to be about 0.11 of the bootstrap SE. HM1 is therefore a consistency check and not evidence of validity under shift. Validity rests on PM1, on the transfer test E2, and on the replication across settings.
- **Power is limited.** The smallest exceedance each cell can detect with 80 % power is measured by the operating-characteristic simulation at the real counts (§9) and reported with every claim. "Not significantly above δ" is never written as "at most δ".
- **The tests are conservative.** At an exact-5 % oracle the simultaneous rule almost never fires (unit test T2). The baseline-failure claims are therefore conservative. The validity checks are weak and are worded as such.

## 2. Data and settings

| Setting | Tracker configuration | What differs from T1 |
|---|---|---|
| **T1** | CANMOT `paper/local/canmot/sc` (IROS 2026): EKF with rotated process noise and a constant-velocity model for every class. Q tuned by Bayesian optimisation for AMOTA on **val**; R a trainval sample covariance. | – |
| **T2** | CANMOT `paper/local/sample/trainval`: same filter and R. Q is the trainval sample covariance of the CV model's one-step residuals. | **Only Q.** The errors D differ from T1's only through the Kalman gain, so T2 is a *covariance-model variant on almost the same residuals* (R07 M1). It shows that the conclusions do not hinge on the BO-tuned Q. |
| **T3** | Poly-MOT (Li et al., IROS 2023), CANMOT's `paper/baseline/poly_mot`: an EKF with a constant-turn-rate-and-acceleration model (CTRA) for cars, buses, pedestrians and trucks, and a linear KF with constant acceleration (CA) for bicycles, motorcycles and trailers. Poly-MOT's own Q and R (the CTRA Q is the identity). | **Different motion models, filter, Q and R, so the residuals differ.** T3 is the independent setting. |

**Shared by all three settings.** The CenterPoint detections, the scenes, logs and ground truth, the pairing code, and the item definition.

**Tuning and training dependencies (R07 M2).**
- **Detector.** CenterPoint was trained on train, so train detections are in-sample and val detections are out-of-sample.
- **T1's Q** was tuned on val. **R** (T1, T2) and **T2's Q** use trainval ground truth, which includes val.
- **T3's** Q and R are fixed defaults.
- **Consequences for E2.** It is a transfer test under three confounded shifts: a new set of logs, the detector moving from in-sample to out-of-sample, and (for T1 and T2) tracker parameters fitted partly on val. A failure of HM6 would not be attributed to log shift alone, and M\*-log does not address detector shift.

**Splits.** Train has 700 scenes in 50 logs; val has 150 scenes in 18 logs; no log is in both.

**Exports.**
- T1: train `60_RESULTS/x2_export_train700_fast_v02`, val `60_RESULTS/x1_export_val150_v02`; horizons `60_RESULTS/x2/x2_horizon_v01.jsonl.gz` and `60_RESULTS/x1/x1_horizon_v01.jsonl.gz`.
- T2: `60_RESULTS/m_export_sampletv_v01`, made with export v05; horizon files v02.
- T3: `60_RESULTS/m_export_polymot_v01`, made with export v06; horizon files v03.
- Export v06 checks C3 and C4 on the native xy block and on P (the CTRA 9×9 output covariance is singular at zero speed by construction). Propagation v03 repeats each class's own filter prediction; on a CV/EKF-rotate setting it is byte-identical to v02.
- Every setting has a 2-scene native-versus-fast equivalence check.

**Data reuse.**
- T1 train and val outcomes were analysed at coarse-cell level in X1, X2 and K5. R06 examined the share of exceedances from turning cars on T1 train.
- **T1's results for B0, B1 and B4 are largely foreknown** (X2 H1, H3 and K5; R07 m18).
- T2 and T3 outcomes have never been computed.

## 3. Items and population

Items are as in X2. At horizon h (2 s for decisions; 1 s and 4 s descriptive), an item is a (record, axis) pair with these properties:
- the record is at k ≥ 1, in the ego's 4 s CTRV corridor, and not a bicycle or motorcycle in a bike rack;
- it is persistently paired with a ground-truth object (2 m gate) and is uncensored at k + h (annotation with ≥ 1 lidar point, not in a rack);
- the axis (object long or lat, from the estimated yaw) separates the estimate from the CTRV-predicted ego footprint;
- the orientation is toward the ego, from the estimate.

For each item:
- D = toward-ego projected error;
- V = a′Σ̂a, the projected horizon variance;
- sd = √(V + σ_a²), with σ_a = 0.10 m;
- U = D/sd.

A margin m is **exceeded** when D > m.

**Population (R07 M7).** Selecting items needs ground truth: pairing at k and observability at k + h. Guarantees and evaluations therefore cover tracked real objects that remain observable. The share of in-path paired items censored at the horizon is reported per stratum from counts. In memory, the counts run also evaluates X2's 2 m drift flag for each row; it is never stored (R07 m8).

## 4. Features and strata (I_k-measurable)

- **Group** (car, pedestrian, two-wheeler, large), from the tracker's class.
- **Range** of the predicted object from the predicted ego at k + h: < 20, 20–40, ≥ 40 m.
- **Axis**: long, lat.
- **Motion state**, from the track's own exported estimates at k, k−1 and k−2:
  - speed ŝ = ‖v̂_k‖;
  - heading rate ω̂ = Δθ / Δt over j = 2 keyframes if the track has a record at k − 2, else over j = 1.
    - **θ is the velocity direction for pedestrians** (their detector yaw is mostly noise; R07 m13) **and the yaw for every other group**.
    - Yaw differences are wrapped to [−π/2, π/2), so a 180° flip does not read as a turn. Velocity-direction differences are wrapped to [−π, π).
  - **static** if ŝ < 1.0 m/s; otherwise **new** if there is no record at k − 1 or k − 2; otherwise **turning** if |ω̂| ≥ 0.10 rad/s; otherwise **straight**.
- **Strata.** Level 0 = group × range × axis × motion (96). Coarser levels: L1 = group × range × axis; L2 = group × axis; L3 = axis.

## 5. Methods

z = Φ⁻¹(0.95). All methods are fitted on calibration scenes only.

**CRC threshold.** For a cell with n ≥ 19 calibration scenes, ĉ is the smallest observed U with n/(n+1)·mean_i L_i(c) + 1/(n+1) ≤ δ, where L_i(c) is scene i's share of items with U > c (Angelopoulos et al., ICLR 2024).

**The method and its variants**

- **M\* (DP-SCRC).**
  - Each level-0 stratum with ≥ 19 calibration scenes gets its own CRC threshold. Otherwise it takes the threshold of the first coarser cell (L1, L2, L3) with ≥ 19 scenes.
  - The margin is m = ĉ·sd.
  - Deployable covariance (P02 PM2): Σ̃ = A(Σ̂ + σ_a²I)A, with A = (max(ĉ_long, 10⁻³)/z) a_l a_l′ + (max(ĉ_lat, 10⁻³)/z) a_t a_t′.
  - The share of fits in which each evaluated cell used its own threshold is reported (R07 M6, m11).
- **M-LS (secondary method arm).**
  - The calibration scenes are split 50/50 by original scene id (seed 20261031).
  - A scale model is fitted on the first half by OLS: log max(|U|, 0.05) on the 17 features φ(x) of v02.
  - M\*'s stratification is then applied to U/s(x) on the second half.
- **M\*-log (sensitivity arm).** As M\*, with the log as the unit and ≥ 19 calibration logs for a stratum's own threshold.
  - With about 40 calibration logs, most level-0 strata fall back, so in practice it is a log-unit CRC at L1–L3 (R07 m10).
  - If a stratum has no level with 19 logs, the arm uses M\*'s maximum threshold there and records that it did.

**Baselines**

- **B0 uncalibrated:** m = z·sd.
- **B1 NEES-guided:**
  - k = ANEES/2 per group × range, from the 2-D NEES on calibration records, with the global value as fallback.
  - m = z·√k·sd. This is X2 H3's correction.
- **B2 variance inflation:** the largest s needed by any L1 cell, fitted empirically and uncertified. m = z·√(sV + σ_a²).
- **B4 pooled conformal:** one CRC threshold over all items. This is the single-inflation correction used in conformalised Kalman filtering (e.g. Weisman et al., 2026).
- **B5 per-axis conformal:** one CRC threshold per axis.
- **B6 coarse stratified:** CRC per L1 cell, with fallback. This is X2's K5 method, without motion state.
- **B7 learned-scale marginal conformal:** M-LS's scale model with one pooled threshold.
- **B8 stratified variance matching:** M\*'s strata, with multiplier z·√(mean U²).
- **B9 norm-ball conformal** (Lindemann et al., RA-L 2023):
  - one CRC radius r̂ on the 2-D error norm ‖truth − mean‖ of calibration records, with the scene as unit;
  - m = r̂ on every axis.
- **B10 stratified empirical quantile:** M\*'s strata, with the item-level empirical 95 % quantile of U and no finite-sample term.

**Pricing references (not competitors)**

- **B3:** the maximum of M\*'s thresholds. It is valid in every stratum that has its own threshold (P02 PM3, scoped).
- **B6c:** per L1 cell, the maximum of M\*'s motion-stratum thresholds.

## 6. Evaluations

- **E1, held-out logs on train.** 20 repetitions of a 5-fold split by log. Folds use seed 20261031 + r, with logs permuted and assigned greedily by scene load. Each item's exceedance indicator and margin are averaged over the repetitions. Inference uses both of the following:
  - **fixed-rule:** a log-cluster bootstrap of the averaged values, B = 2000;
  - **refit-CV** (2 s only; R07 M4): B = 200 replicates. Each replicate resamples the 50 logs, assigns every copy of a log to the same fold, re-runs one 5-fold CV of every method, and recomputes the cell estimates. The replicates are centred at the fixed-rule point estimate.
- **E2, transfer to val.**
  - Point estimate: every method fitted on all 700 train scenes (the deployable rule) and evaluated on val.
  - Inference: a two-sample refit log bootstrap that resamples train logs and val logs and refits on the resampled train. B = 1000 at 2 s and 300 at 1 s and 4 s.
  - **Estimand:** the marginal risk of the procedure (P02, v02 section).
- **E4:** E1 (fixed-rule) and E2 at 1 s and 4 s. Descriptive.
- **E5:** sensitivities (§10), E1 fixed-rule. Descriptive.
- **Tracker settings:** E1, E2 and E4 run on T1, T2 and T3 with identical code.

## 7. Cells, statistics and hypotheses

**Evaluation cells** (fixed from counts before the freeze; `60_RESULTS/m/m_sizes_*_v02.json`). Every cell needs **≥ 39 scenes and ≥ 8 logs** in its evaluation pool (R07 m4).
- **E1 (train):**
  1. each level-0 stratum that qualifies;
  2. then, per group × axis, the union of the remaining strata;
  3. then, per axis, the union of what remains (R07 M6).
- **E2 (val):**
  1. group × axis × motion, pooled over range (R07 C2);
  2. then each motion state pooled over groups, axes and ranges for the strata still unused (on T1 val this yields an "all turning items" cell; car lateral turning alone has only 25 val scenes);
  3. then the remainders, as in E1;
  4. and one pooled cell, "all val items", for HM6b.

**Statistics.**
- Ê_c = mean over scenes with items in c of the scene's exceeded share. This is primary; the record share is secondary.
- One-sided simultaneous 95 % bounds within each method, by sup-t with the bootstrap SE:
  - the lower bound LB for under-coverage;
  - the upper bound UB, reported.
- A cell is **significantly under-covered** if LB > δ. If its SE is 0, it is under-covered when Ê > δ (R07 m3).
- Per cell, the NaN share of replicates and the bootstrap bias are reported. Ē is the mean over cells that are present in every replicate (R07 m2, m17).
- **Paired contrast b − M\*:**
  - the difference of cell estimates, with a sup-t lower bound over a pre-specified family, using the same replicates for both methods;
  - "significantly positive" if LB > 0.

**A baseline b fails in cell c** when, in E1 at 2 s and under **both** the fixed-rule and the refit-CV inference, all three hold:
- b is significantly under-covered in c;
- M\* is not;
- the paired difference b − M\* is significantly positive.

**Hypotheses, per tracker setting (decision horizon 2 s).**
- **HM1 (consistency):** M\* is significantly under-covered in no E1 cell, under either inference.
- **HM6 (transfer):** **(a)** M\* is significantly under-covered in no E2 cell; and **(b)** the pooled val exceedance of M\* has UB ≤ δ + 0.02.
- **HM2:** for each of B1, B4 and B9: the baseline fails in at least one E1 cell (paired family = all E1 cells).
- **HM2b:** the same for B5, B7, B8 and B10.
- **HM3:** B6 fails in at least one cell of the pre-specified family, the single-stratum E1 cells of cars with motion state *turning*.

## 8. Decision on the method stage (written into D07; script `m_decide_v02.py`)

- **METHOD GO-A:**
  - on T1 and on T3: HM1, HM6, HM2 for at least one of B1, B4, B9, and HM3;
  - on T2: HM1 and HM6.
- **METHOD GO-B:** as GO-A except HM3. The paper then presents motion strata as an option and makes no claim that they are needed.
- **NO-GO:** anything else.
  - If HM1 fails, the M\*-log consistency is reported as the pre-registered remedy, labelled post hoc.
  - If HM6 fails, the diagnosis distinguishes log shift from detector shift (§2).

**Claims.**
- Each of K5a, K5a′ and K5b is claimed for a baseline only if it holds on T1 and on T3. T2 is reported beside them.
- **M-LS is recommended** only if all three hold:
  - it is consistent in E1 on all three settings;
  - it passes the HM6 rule on all three settings;
  - its mean-margin ratio M-LS/M\* has a 95 % CI below 1 on T1 and on T3.
- **Efficiency is descriptive** (R07 C3): M\*/B3, M\*/B6c, M\*/B9 and M-LS/M\*, with CIs.

## 9. Operating characteristics at the real counts (computed before the freeze)

`50_CODE/m/tests/test_m_oc_v01.py` rebuilds the real item layout of T1 and of T3 (per scene and stratum counts, scenes in their real logs) with simulated, within-scene-correlated scores (ρ = 0.5, log effects of SD 0.1). It then runs `run_e1` and `run_e2` themselves and reports:
- (a) how often HM1 fails for a valid M\* (fixed-rule and refit-CV);
- (b) how often HM6 fails for a valid M\*;
- (c) per E1 and E2 cell, the power of the fixed-rule test against true exceedances of 0.10, 0.15, 0.20 and 0.30, and the minimum detectable exceedance at 80 % power;
- (d) the power of HM3's paired contrast.

The results are frozen with this plan (`70_TESTS/m_scratch/oc_v01_T1.json`, `oc_v01_T3.json`) and summarised in `70_TESTS/M_SYNTHETIC_TESTS_v02.md`. The paper quotes the minimum detectable exceedance beside every validity statement.

## 10. Sensitivities (E5; reported, not decisions)

1. Static threshold 0.5 and 2.0 m/s; turning threshold 0.05 and 0.20 rad/s.
2. Heading rate from the velocity direction for every group; from the yaw for every group.
3. σ_a = 0 and 0.20 m.
4. Own-threshold minimum n ≥ 39 instead of 19. This applies to every minimum in `fit_methods` (M\*, B1, B2, B5, B6, B8, B10, M-LS) except M\*-log (R07 m5).
5. Contested pairs excluded.
6. Scene bootstrap instead of log bootstrap.

In every sensitivity the cells are rebuilt by the §7 rule from that sensitivity's own strata.

## 11. Before the freeze: what may be computed

- Simulated-data tests only. No real annotation enters a test.
- Counts per stratum and cell for every setting, split and horizon, with outcomes switched off.
- Export integrity (Q0) and the native-versus-fast equivalence checks (tracker outputs only).
- Nothing else touches D, U or any residual on real data.
- An independent re-review of v03 and the v02 code (R07b) is done before the freeze.

## 12. Code, inputs, outputs, run

- **Code:** `50_CODE/m/` (m_lib_v02, m_data_v02, m_sizes_v02, m_run_v02, m_decide_v02, m_freeze_v02, run scripts) and its `tests/`. Also `50_CODE/x1/x1_lib_v03.py`, the export and propagation code of T2 and T3, and the v01 files, which are kept as the pre-review record.
- **Run:** `run_m_main_v02.sh` runs T1, T2 and T3 in parallel (memory per run is about 2–3 GB after the in-path filter of m_data_v02), then `m_decide_v02.py`. It runs unattended and has no branch on any result.
  - Each run refuses to start unless the plan hash, the frozen files, the input binding and the numpy/scipy versions match.
- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v02.json` and `m_decision_v02.json`.
- **Deviations:** `90_DECISIONS/D08_M_DEVIATION_LOG_v01.md`.

## 13. Changes from v02 (all made before any real outcome was computed)

| R07 finding | Change |
|---|---|
| C1 | Claims reworded (§1). Minimum detectable exceedances from an OC simulation at the real counts (§9). E1 named a consistency check. |
| C2 | E2 cells are pooled over range and keep the motion state, and leftover strata are pooled per motion state (so turning is tested on val). Remainder cells added. A pooled val cell is used for HM6b. |
| C3 | The efficiency criterion is removed from the decision. GO-A requires HM3 and a practitioner baseline failing, on T1 and T3. GO-B is defined. |
| M1 | T3 = Poly-MOT added (different motion models). T2 relabelled. |
| M2 | Tuning and training dependencies listed, with their effect on E2. |
| M3 | HM3 is a paired contrast within a pre-specified car turning family. |
| M4 | Refit-CV bootstrap for E1 at 2 s; a baseline fails only if both inferences agree. |
| M5 | Size and power reported (unit tests, OC simulation). |
| M6 | Remainder cells; own-threshold shares reported. |
| M7 | Population stated; censoring counts reported. |
| M8 | B9 (norm ball) and B10 (no finite-sample term) added; related work in P02 v02. |
| M9 | Estimand stated (P02 v02). |
| M10 | Empty-cell guard; in-path filter before the horizon step; a log arm without a threshold no longer crashes. |
| M11 | crc32 seeds; refit and OC tests run the run-script functions; end-to-end pass criteria; freeze dry run. |
| m1–m19 | Applied as listed in the code headers (m_lib_v02, m_run_v02, m_freeze_v02) and above. m12, the orientation null: not needed, because every method is evaluated on the same estimate-oriented population on which M\* is calibrated, so the orientation effect is part of what each method must cover. |

FROZEN_HASHES_BEGIN
(filled at the freeze)
FROZEN_HASHES_END
