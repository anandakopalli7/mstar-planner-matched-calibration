# M pre-registration v04: the method stage (31 Oct 2026)

**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v03.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v04.txt`, which is not itself frozen. v01, v02 and v03 are kept unchanged; none of them was frozen. `M_PLAN_HASH_LOG.txt` lists the draft hashes. Its last v03 entry (`cec106ed…`) is the text that R07b reviewed.

**Why v04.** A second pre-freeze review, R07b (`70_TESTS/R07B_M_PREFREEZE_REREVIEW_v01.md`), checked v03 against R07 and found new problems: 1 critical, 3 major and 15 minor.
- **The critical one (N-C1).** Poly-MOT's CTRA model writes (speed, acceleration) into the exported velocity field. T3's in-path selection and motion states would have been built on it.
- **The majors.**
  - The motion-state claim had no clean confirmatory test (N-M1).
  - The E1 refit-CV bootstrap is still far too wide for M\* (N-M2).
  - The OC study measured the wrong E2 test and had no acceptance criteria (N-M3).

v04 fixes all of them. The table is in §13. No real outcome had been computed when any change was made.

**Why v03.** The pre-freeze review R07 (`70_TESTS/R07_M_PREFREEZE_REVIEW_v01.md`; 3 critical, 11 major, 19 minor) found that v02 would have allowed claims its tests could not support:
- validity was claimed from tests with almost no power;
- the transfer test never reached the motion strata;
- the efficiency criterion could not fail;
- the second tracker setting shared its residuals with the first.

v03 changes the claims, the inference and the decision rule, and adds a third tracker setting with different motion models. The change list against v02 is in §13. No real outcome had been computed when any of these changes was made.

## 1. Claims and how far the tests can carry them

| Claim | Statement | Evidence |
|---|---|---|
| **K5** (validity) | DP-SCRC has a finite-sample guarantee on the toward-ego exceedance of tracked, still-observable objects. It holds for each stratum with its own threshold, under i.i.d. scenes (P02 PM1, marginal over calibration). Empirically, its exceedance is **consistent with δ = 0.05** in every evaluated cell on held-out logs (E1, a consistency check) and **after transfer to the log-disjoint val split** (E2), on three tracker settings. The best-powered check is HM6b, the pooled val exceedance, which detects a pooled exceedance of about 0.06 or more (§9). | PM1; HM1 (E1); HM6 (E2) |
| K5a (practitioner corrections fail) | NEES-guided scaling (B1), pooled conformal (B4) and norm-ball conformal (B9) each leave at least one cell significantly under-covered **where DP-SCRC is not**, with a significant paired difference | HM2 |
| K5a′ (ablations) | Per-axis conformal (B5), learned-scale marginal conformal (B7), stratified variance matching (B8) and stratified empirical quantiles without the finite-sample term (B10): the same paired test | HM2b |
| K5b (motion state) | Without motion-state strata (B6), at least one car turning stratum is significantly under-covered where DP-SCRC is not, with a significant paired difference. **Confirmatory on T3 only.** On T1 it is foreknown (R06 found turning cars carry 68 % of exceedances, and the strata were designed from that), so T1 and T2 are reported but carry no weight. | HM3 |
| K5e (price) | Margin ratios against the certified single multiplier (B3), the certified coarse rule (B6c) and the norm ball (B9) | Descriptive, 95 % CIs |
| K5f (generality) | The above on CANMOT (T1), on CANMOT with a data-estimated Q (T2) and on Poly-MOT (T3) | §8 |

**What the tests cannot show, stated in advance.**
- **E1 is pinned for conformal methods.** On held-out logs, a conformal method's pooled held-out exceedance stays near δ by construction.
  - R07 S3 found the fixed-rule bootstrap SE for M\* to be about 9 times its true SD.
  - R07b S1 found the refit-CV SE still 4.6–7.7 times too wide, with replicates biased upwards.
  - HM1 is therefore a consistency check under both inferences, not evidence of validity under shift.
  - Validity rests on PM1, the transfer test E2 (HM6b best of all) and the replication across settings.
- **Power is limited.** §9 measures:
  - the per-cell power of the "significantly under-covered" component;
  - the power of the actual E2 rule against planted val shifts;
  - the power of the actual HM3 rule.

  These are reported with every claim. "Not significantly above δ" is never written as "at most δ".
- **The tests are conservative.** At an exact-5 % oracle the simultaneous rule almost never fires (unit test T2). The baseline-failure claims are therefore conservative. The validity checks are weak and are worded as such.

## 2. Data and settings

| Setting | Tracker configuration | What differs from T1 |
|---|---|---|
| **T1** | CANMOT `paper/local/canmot/sc` (IROS 2026): EKF with rotated process noise and a constant-velocity model for every class. Q tuned by Bayesian optimisation for AMOTA on **val**; R a trainval sample covariance. | – |
| **T2** | CANMOT `paper/local/sample/trainval`: same filter and R. Q is the trainval sample covariance of the CV model's one-step residuals. | **Only Q.** The errors D differ from T1's only through the Kalman gain, so T2 is a *covariance-model variant on almost the same residuals* (R07 M1). It shows that the conclusions do not hinge on the BO-tuned Q. |
| **T3** | Poly-MOT (Li et al., IROS 2023), CANMOT's `paper/baseline/poly_mot`: an EKF with a constant-turn-rate-and-acceleration model (CTRA) for cars, buses, pedestrians and trucks, and a linear KF with constant acceleration (CA) for bicycles, motorcycles and trailers. Poly-MOT's own Q and R (the CTRA Q is the identity). | **A different motion-model family, filter, Q and R, on the same detections, association and life cycle** (R07b N-m4). Its residuals differ, so it is the most independent of the three settings, though not fully independent. |

**Shared by all three settings.** These are the same in T1, T2 and T3:
- the CenterPoint detections;
- the preprocessing (score filter, NMS);
- the association metrics, thresholds and life cycle (Poly-MOT's published values; `nusc_config_poly_mot.yaml` differs from `nusc_config_rotate_cov_cv.yaml` only in filter and motion model);
- the scenes, logs and ground truth;
- the pairing code and the item definition.

**T3's velocity (R07b N-C1).** Poly-MOT's CTRA `getOutputInfo` writes state slots 6–7, which are (speed, acceleration), into the exported velocity field.
- **Correction.** The loader `m_data_v03` sets (vx, vy) = v·(cos θ, sin θ) from each CTRA record's own state (v = state[6], θ = state[8]), births included, before anything uses velocity: the in-path test, speed and heading rates. CA records and T1/T2 are unchanged.
- **Check, on tracker output only** (`tests/test_export_velocity_v01.py`; `70_TESTS/m_scratch/export_velocity_v01.json`). For moving cars, the median |velocity − displacement/time| is 7.22 m/s uncorrected and 0.74 m/s corrected, against 0.71 m/s on T1. Every CTRA class is within 0.5 m/s of T1. On T1 and T2 the loader is identical, field for field, to the X2 loader.

**Tuning and training dependencies (R07 M2).**
- **Detector.** CenterPoint was trained on train, so train detections are in-sample and val detections are out-of-sample.
- **T1's Q** was tuned on val. **R** (T1, T2) and **T2's Q** use trainval ground truth, which includes val.
- **T3's** Q and R are fixed defaults.
- **Shared by all three:** the association, life-cycle, score-filter and NMS thresholds are Poly-MOT's published values, selected on nuScenes val (R07b N-m4).
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
- **T1's results for B0, B1 and B4 are largely foreknown** (X2 H1, H3 and K5; R07 m18). **So is HM3 on T1** (R06; R07b N-M1). HM3 is confirmatory on T3 only.
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
  - **heading rate ω̂: the course-over-ground turn rate, for every group** (R07b N-M1).
    - It is the change in the direction of the track's own displacement between [k−4, k−2] and [k−2, k], divided by the time between the midpoints of the two intervals (about 1 s).
    - Without the record at k−4, it uses [k−2, k−1] and [k−1, k].
    - The exported positions are the tracker's estimates, so ω̂ is I_k-measurable. It does not depend on each tracker's yaw noise. On the same two scenes, the yaw rule labelled 49 % of Poly-MOT's moving cars "turning", against 4 % on CANMOT.
    - Directions are wrapped to [−π, π).
    - The yaw rate (yaw at k against k−2, else k−1, wrapped to [−π/2, π/2)) and the velocity-direction rate are kept as sensitivities (§10).
  - **static** if ŝ < 1.0 m/s; otherwise **new** if ω̂ is undefined (no history for either interval pair); otherwise **turning** if |ω̂| ≥ 0.10 rad/s; otherwise **straight**.
  - The turning share of moving cars is reported per setting and split from counts (`car_moving_turning_share` in the counts files).
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
  - **refit-CV** (2 s only): B = 200 replicates. Each replicate resamples the 50 logs, assigns every copy of a log to the same fold, re-runs one 5-fold CV of every method, and recomputes the cell estimates. The replicates are centred at the 20-repetition point estimate.
  - **Character of the refit-CV.** It carries calibration randomness. It is conservative:
    - about 5× for M\* (R07b S1);
    - about 1.4× for B6 under the null (R07b S2).

    Its replicate means run high, because duplicated logs act as distinct calibration units, and that also makes it conservative for flags. **Baseline failures are judged on the refit-CV inference** (§7); the fixed rule is reported beside it.
- **E2, transfer to val.**
  - Point estimate: every method fitted on all 700 train scenes (the deployable rule) and evaluated on val.
  - Inference: a two-sample refit log bootstrap that resamples train logs and val logs and refits on the resampled train. B = 1000 at 2 s and 300 at 1 s and 4 s.
  - **Estimand:** the marginal risk of the procedure (P02, v02 section).
- **E4:** E1 (fixed-rule) and E2 at 1 s and 4 s. Descriptive.
- **E5:** sensitivities (§10), E1 fixed-rule. Descriptive.
- **Tracker settings:** E1, E2 and E4 run on T1, T2 and T3 with identical code.

## 7. Cells, statistics and hypotheses

**Evaluation cells** (fixed from counts before the freeze; `60_RESULTS/m/m_sizes_*_v03.json`). Every cell needs **≥ 39 scenes and ≥ 8 logs** in its evaluation pool (R07 m4).
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
- **Pooled cells (R07b N-m5).** A range-pooled, motion-pooled or remainder cell, or the pooled val cell, averages strata within each scene by item counts. Its null value is only approximately δ, even when every stratum meets PM1, and remainders include fallback strata. A flag in a pooled cell is evidence against the method, read with that caveat.
- **Paired contrast b − M\*:**
  - the difference of cell estimates, with a sup-t lower bound over a pre-specified family, using the same replicates for both methods;
  - "significantly positive" if LB > 0.

**A baseline b fails in cell c** when, in E1 at 2 s and on the **refit-CV inference** (R07b N-M2), all three hold:
- b is significantly under-covered in c;
- M\* is not;
- the paired difference b − M\* is significantly positive.

**Hypotheses, per tracker setting (decision horizon 2 s).**
- **HM1 (consistency):** M\* is significantly under-covered in no E1 cell, under either inference.
- **HM6 (transfer):** **(a)** M\* is significantly under-covered in no E2 cell; and **(b)** the pooled val exceedance of M\* has a **bias-corrected** UB ≤ δ + 0.02 (UB + max(bootstrap bias, 0); R07b N-m6).
- **HM2:** for each of B1, B4 and B9: the baseline fails in at least one E1 cell (paired family = all E1 cells).
- **HM2b:** the same for B5, B7, B8 and B10.
- **HM3:** B6 fails in at least one cell of the pre-specified family, the single-stratum E1 cells of cars with motion state *turning*.
  - If the family is empty, HM3 is recorded as untestable, not as false (R07b N-m2).
  - Confirmatory on T3 only (§1).

## 8. Decision on the method stage (written into D07; script `m_decide_v03.py`)

- **METHOD GO-A:** all of these hold:
  - HM1 and HM6 on T1, T2 and T3;
  - **the same** practitioner baseline (B1, B4 or B9) fails (HM2) on T1 and on T3 (R07b N-m1);
  - HM3 on T3.
- **METHOD GO-B:** as GO-A without HM3 on T3. The paper then presents motion strata as an option and does not claim they are needed. If T3 has no car-turning cell, the label is "GO-B (HM3 untestable)".
- **NO-GO:** anything else.
  - If HM1 fails, the M\*-log consistency is reported as a pre-registered *diagnostic*. Adopting M\*-log would need a new plan version, and any such claim is labelled exploratory (R07b N-m11).
  - If HM6 fails, the diagnosis distinguishes log shift from detector shift (§2).
- **Inputs are verified.** m_decide_v03 decides only if the results carry the frozen plan's hash, none is from test mode, each carries its own tracker label, and all three runs completed. `run_m_main_v03.sh` decides only if all three runs exit cleanly (R07b N-m8).

**Claims.**
- K5a and K5a′ are claimed for a baseline only if it holds on T1 and on T3.
- K5b is claimed only if HM3 holds on T3.
- T2, and T1 for K5b, are reported beside them.
- **M-LS is recommended** only if all three hold:
  - it is consistent in E1 on all three settings;
  - it passes the HM6 rule on all three settings;
  - its mean-margin ratio M-LS/M\* has a 95 % CI below 1 on T1 and on T3.
- **Efficiency is descriptive** (R07 C3): M\*/B3, M\*/B6c, M\*/B9 and M-LS/M\*, with CIs.

## 9. Operating characteristics at the real counts (computed before the freeze)

**Procedure.** `tests/test_m_oc_v02.py`, run by `run_m_oc_v02.sh` and merged by `merge_oc_v02.py`.
- It rebuilds the real item layout of T1 and of T3 (per scene and stratum counts, scenes in their real logs, records per scene) with simulated scores, correlated within each scene and stratum (ρ = 0.5 and 0.8), and log effects of SD 0.1.
- It runs the actual rules (`run_e1`, `run_e2`, `hypotheses_e1`, `hypotheses_e2`), fitting only the methods each part needs (R07b N-M3).
- The parts:
  - **e1null:** the HM1 failure rate for a valid M\*, fixed rule and refit-CV;
  - **e2null:** the HM6 failure rate for a valid M\*;
  - **e2power:** every val turning item's scale × 1.5 or × 2.0; the HM6a flag rate in the val turning cell and the HM6 failure rate;
  - **hm3power:** car lateral turning τ = 1.6, 2.0 or 2.6 against straight 1.2; the HM3 rate under the frozen rule, with the realised B6 exceedance;
  - **comp:** the per-cell power of the "significantly under-covered" component alone, against planted exceedances of 0.10–0.30 (labelled as component power; R07b N-m14).
- The E2 parts use B = 150, against 1000 in the run, and the refit-CV parts use B = 60, against 200.

**Acceptance criteria, fixed before the OC results were seen.** All at ρ = 0.5, per tracker layout.
- **A1:** M\* is flagged by HM1 in at most 10 % of null datasets, under the fixed rule and under the refit-CV rule.
- **A2:** HM6 fails in at most 10 % of null datasets.

If A1 or A2 fails for T1 or T3, the plan is revised before the freeze: ε, the cell-size rule or the bound is changed, and the OC study is re-run. That revision and its reason go into v05. The OC results (`70_TESTS/m_scratch/oc_v02_T1.json`, `oc_v02_T3.json`) are frozen with this plan and summarised in `70_TESTS/M_SYNTHETIC_TESTS_v03.md`. Every validity statement in the paper quotes the relevant power.

## 10. Sensitivities (E5; reported, not decisions)

1. Static threshold 0.5 and 2.0 m/s; turning threshold 0.05 and 0.20 rad/s.
2. Heading rate from the velocity direction for every group; from the yaw for every group (the default is course over ground).
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

- **Code:** `50_CODE/m/` and its `tests/`.
  - The v03 modules: m_lib_v03, m_data_v03, m_sizes_v03, m_run_v03, m_decide_v03, m_freeze_v03, run scripts.
  - They are generated from v02 by the recorded patch scripts `tests/make_m_lib_v03.py` and `tests/make_m_run_v03.py`.
  - Also `50_CODE/x1/x1_lib_v03.py`, and the export and propagation code of T2 and T3.
  - The CANMOT files that define T3's predictions (motion model, filter, class constants, Poly-MOT configs).
  - v01 and v02 are kept as the pre-review record.
- **Run:**
  - `run_m_main_v03.sh` runs T1, T2 and T3 in parallel. The peak working set of each loading step is logged in the counts files; with 15.7 GB of RAM, three parallel runs fit if each stays below about 4.5 GB, and otherwise they are run in turn.
  - It then runs `m_decide_v03.py`, but only if every run exited cleanly.
  - Partial results are written after every section, and a failing sensitivity is recorded, not fatal (R07b N-m7).
  - Each run refuses to start unless the plan hash, the frozen files, the input binding and the numpy/scipy versions match.
- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v03.json` and `m_decision_v03.json`.
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

**Changes from v03 (R07b; all made before any real outcome was computed)**

| R07b finding | Change |
|---|---|
| N-C1 | T3 velocity rebuilt from the CTRA state in `m_data_v03`. Export-level velocity check on tracker output. T3 counts and OC built only after the fix. |
| N-M1 | Course-over-ground turn rate for every group. HM3 confirmatory on T3 only; T1 foreknown. Turning shares reported. |
| N-M2 | Refit-CV described as conservative (about 5× for M\*). Baseline failures judged on refit-CV alone; the fixed rule reported. |
| N-M3 | OC v02 runs the actual E2 and HM3 rules, at ρ = 0.5 and 0.8, with acceptance criteria A1 and A2 (§9). |
| N-m1 | The same practitioner baseline must fail on T1 and T3. |
| N-m2 | HM3 untestable is recorded and labelled. |
| N-m3 | The simulated dataset v02 has lateral cars, so HM3 has a known answer (end-to-end criterion 5). The v02 relaxation of criterion 3 is disclosed. |
| N-m4 | T3 wording; shared association, life-cycle and preprocessing values added to the tuning list. |
| N-m5 | Pooled-cell caveat (§7). |
| N-m6 | Bias-corrected UB for HM6b. |
| N-m7 | Partial saves; fault-tolerant sensitivities; sd floor. |
| N-m8 | m_decide_v03 verifies its inputs; the main script checks exit codes. |
| N-m9 | m_freeze_v03 asserts all_ok for every test output and freezes the CANMOT T3 files, the split receipts and T1's equivalence file. |
| N-m10 | Peak memory logged; parallel run conditional on it. |
| N-m11 | Wording of K5, the remedy and §13. |
| N-m12 | The hash log is not appended after the freeze; the freeze record is a separate file. |
| N-m13 | The B2 cap flag is reported. |
| N-m14 | OC component power labelled as such. |
| N-m15 | HM6b named the best-powered validity check (§1). |

FROZEN_HASHES_BEGIN
(filled at the freeze)
FROZEN_HASHES_END
