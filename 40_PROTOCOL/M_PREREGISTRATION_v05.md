# M pre-registration v05: the method stage (31 Oct 2026)

**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v05.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v05.txt`, which is not itself frozen. v01–v04 are kept unchanged; none of them was frozen.

**Why v05.**
1. v04 §9 fixed acceptance criteria for the OC study. On the T1 layout **A2 failed at ε = 0.02**: a valid M\* failed HM6 in 27 % of null datasets, all through HM6b, the equivalence bound on the pooled val exceedance.
2. The third check, R07c (`70_TESTS/R07C_M_PREFREEZE_CHECK_v01.md`), found two further problems:
   - choosing ε from those same simulated datasets would pass A2 by construction;
   - the pass rate of an equivalence bound depends on a between-log variance that the simulation sets arbitrarily.
3. v05 therefore:
   - makes **HM6b the pooled val cell's significance check** (it fails if the pooled cell is significantly above δ). Its false-failure rate is the test's size, not a simulated variance;
   - keeps the equivalence bound UB_bc ≤ δ + ε with ε = 0.03 (derived from OC v02) as a **reported, not decided** statement;
   - **confirms A2 on fresh seeds** (OC v03: 100 new null datasets per layout), with between-log SD 0.05 and 0.2 as sensitivities;
   - applies R07c's minor items (§13).
4. No real outcome had been computed. `M_PLAN_HASH_LOG.txt` lists the draft hashes. Its last v03 entry (`cec106ed…`) is the text that R07b reviewed.

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
| **K5** (validity) | DP-SCRC has a finite-sample guarantee on the toward-ego exceedance of tracked, still-observable objects. It holds for each stratum with its own threshold, under i.i.d. scenes (P02 PM1, marginal over calibration). Empirically, its exceedance is **consistent with δ = 0.05** in every evaluated cell on held-out logs (E1, a consistency check) and **after transfer to the log-disjoint val split** (E2), on three tracker settings. The pooled val cell is checked for significant exceedance (HM6b), and its bias-corrected 95 % upper bound is reported against δ + 0.03.
  - **Power at the real val layout (OC v03):** a planted val turning shift giving a turning-cell exceedance of about 0.20 is caught by HM6 in 0.80 of datasets on T1 and 0.85 on T3; one of about 0.12 in 0.23 and 0.23. | PM1; HM1 (E1); HM6 (E2) |
| K5a (practitioner corrections fail) | NEES-guided scaling (B1), pooled conformal (B4) and norm-ball conformal (B9) each leave at least one cell significantly under-covered **where DP-SCRC is not**, with a significant paired difference | HM2 |
| K5a′ (ablations) | Per-axis conformal (B5), learned-scale marginal conformal (B7), stratified variance matching (B8) and stratified empirical quantiles without the finite-sample term (B10): the same paired test | HM2b |
| K5b (motion state) | Without motion-state strata (B6), at least one car turning stratum is significantly under-covered where DP-SCRC is not, with a significant paired difference. **Confirmatory on T3 only.** On T1 it is foreknown (R06 found turning cars carry 68 % of exceedances, and the strata were designed from that), so T1 and T2 are reported but carry no weight. **Power (OC v02, the frozen refit rule):**

| B6 lateral-turning exceedance about | 0.10 | 0.125 | 0.17 |
|---|---|---|---|
| T1 | 0.10 | 0.65 | 1.00 |
| T3 | 0.15 | 0.60 | 0.95 |

HM3 therefore detects only a motion-state effect of about 0.14 or more. The refit-CV inference is used because it carries calibration randomness, not for power. | HM3 |
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
  - The turning share of moving cars is reported per setting and split from counts (`car_moving_turning_share`), and by speed band in each run (`turning_share_by_speed_band`).
  - **"Turning" is a course-change state, not a manoeuvre label at low speed (R07c X-m5).** Position noise in a short chord reads as a course change. R07c measured, on tracker output, that 41–45 % of moving cars at 1–3 m/s are "turning", against 8–11 % at ≥ 8 m/s, and 52–59 % of moving pedestrians. The method's validity does not depend on it: strata are only a partition. The paper uses the term "course-change state" and reports the speed bands. E5 adds a minimum-chord sensitivity (§10).
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
- **HM6 (transfer):** **(a)** M\* is significantly under-covered in no E2 cell; and **(b)** the pooled val cell ("all val items") is not significantly under-covered (its simultaneous LB ≤ δ; R07c X-M1).
  - Reported beside it: the bias-corrected UB (UB + max(bootstrap bias, 0); R07b N-m6) and whether UB_bc ≤ δ + 0.03 (`pooled_equivalence_at_eps`).
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
- **Probability of a false NO-GO.** Assume a valid method in all three settings, the OC null rates, and independence (T2 shares T1's layout). This is an upper bound, since T1 and T2 are positively correlated. HM6 alone then gives a false NO-GO with probability 1 − (1 − 0.03)²(1 − 0.01) = 0.07. HM1's null rate is 0 at these sizes (A1).
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

**Procedure.**
- The OC study rebuilds the real item layout of T1 and of T3: per scene and stratum counts, scenes in their real logs, and records per scene.
- It simulates scores correlated within each scene and stratum (ρ = 0.5 and 0.8), with between-log effects of SD 0.1, and 0.05 and 0.2 as sensitivities.
- It runs the actual rules (`run_e1`, `run_e2`, `hypotheses_e1`, `hypotheses_e2`), fitting only the methods each part needs.
- The `only=` path equals the full path for M\* and B6 (R07c S1).
- **Settings, disclosed (R07c X-m2):**
  - the E1 parts use 3 CV repetitions, fixed-rule B = 300 and refit-CV B = 60;
  - the E2 parts use B = 150;
  - the run uses 20, 2000, 200 and 1000.

**Two rounds.**
- **OC v02** (`tests/test_m_oc_v02.py`, shards in `70_TESTS/m_scratch/oc_v02/`) provides the E1 parts: e1null (A1), hm3power and component power.
- **OC v03** (`tests/test_m_oc_v03.py`, fresh seed labels "oc3", v04 rules, shards in `oc_v03/`) provides the E2 parts:
  - 100 null datasets at ρ 0.5 and log SD 0.1 (A2);
  - 20 at ρ 0.8;
  - 40 each at log SD 0.05 and 0.2;
  - 40 each with the val turning items scaled by 1.5 or 2.0.
- Merged by `merge_oc_v04.py`, which asserts the expected number of datasets per part, into `oc_v04_T1.json` and `oc_v04_T3.json`.

**Acceptance criteria.** All at ρ = 0.5, per layout.
- **A1:** M\* is flagged by HM1 in at most 10 % of null datasets, under the fixed rule and under the refit-CV rule.
- **A2:** HM6 fails in at most 10 % of the 100 fresh null datasets at log SD 0.1.
- When they were fixed (v04, 14:55), the OC v02 results had not been seen. OC v01, which used a different, fixed-rule E2 test, had shown a 15 % HM6 null failure rate (R07c X-m1).
- **History.** A2 failed in OC v02 under v04's equivalence-type HM6b (T1: 27 % at ε = 0.02). The tolerance rule in `tests/derive_eps_v01.py` gave ε = 0.03 (`eps_v01.json`), which is kept as the descriptive margin. HM6b was redefined (see "Why v05"), and A2 was then checked on fresh seeds.

**Results**

| Quantity | T1 (CANMOT layout) | T3 (Poly-MOT layout) |
|---|---|---|
| A1: M\* flagged by HM1, null (fixed / refit-CV) | 0.00 / 0.00 | 0.00 / 0.00 |
| **A2: HM6 fails, 100 fresh null datasets** | **0.03** (CI [0.0103, 0.0845]) | **0.01** (CI [0.0018, 0.0545]) |
| HM6 fails, null, ρ 0.8 | 0.00 | 0.05 |
| HM6 fails, null, log SD 0.05 / 0.2 | 0.00 / 0.05 | 0.00 / 0.00 |
| Equivalence bound UB_bc ≤ δ + 0.03 fails, null (descriptive) | 0.04 | 0.04 |
| HM6 fails, val turning ×1.5 (turning-cell E ≈ 0.12 / 0.13) | 0.23 | 0.23 |
| HM6 fails, val turning ×2.0 (turning-cell E ≈ 0.20 / 0.19) | 0.80 | 0.85 |
| HM3 holds, B6 lateral-turning E ≈ 0.10 / 0.125 / 0.17 | 0.10 / 0.65 / 1.00 | 0.15 / 0.60 / 0.95 |
| E1 component MDE80 per cell (range) | 0.10–0.30 | 0.10–0.30 |
| E2 component MDE80 per cell (range) | 0.15–0.30 | 0.15–0.30 |
| Acceptance A1 and A2 | True | True |

"Component" means the "significantly under-covered" component alone, under the fixed rule. Every validity statement in the paper is worded within these limits.

## 10. Sensitivities (E5; reported, not decisions)

1. Static threshold 0.5 and 2.0 m/s; turning threshold 0.05 and 0.20 rad/s.
2. Heading rate from the velocity direction for every group; from the yaw for every group (the default is course over ground); and course over ground counted as 0 when either chord is shorter than 1 m (`cog_min_chord_1m`; R07c X-m5).
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
  - **The v04 modules run the study:** m_lib_v04, m_data_v04, m_sizes_v04, m_run_v04, m_decide_v04, m_freeze_v05, and `run_m_main_v04.sh`.
    - They are generated by the recorded patch scripts `tests/make_m_lib_v03.py` then `make_m_lib_v04.py`, and `make_m_run_v03.py` then `make_m_run_v04.py`.
    - Each generator reproduces its module byte for byte (R07c X-m12).
  - **The real counts files** were made by m_sizes_v03. m_sizes_v04 differs from it only in its imports. The run re-derives every stratum count and cell with the v04 code and stops if any differs.
  - Also `50_CODE/x1/x1_lib_v03.py`, and the export and propagation code of T2 and T3.
  - The CANMOT files that define T3's predictions (motion model, filter, class constants, Poly-MOT configs).
  - v01 and v02 are kept as the pre-review record.
- **Run:**
  - `run_m_main_v04.sh` runs T1 and T2 in parallel and starts T3 once both have passed their loading peak, so the measured peaks (3.7, 3.3 and 4.4 GB) never overlap. No other job runs at the same time (R07c X-m8).
  - It then runs `m_decide_v04.py`, but only if every run exited cleanly, and checks the decision script's own exit code (R07c X-m9).
  - The 1 s and 4 s sections are fault-tolerant like E5.
  - Partial results are written after every section, and a failing sensitivity is recorded, not fatal (R07b N-m7).
  - Each run refuses to start unless the plan hash, the frozen files, the input binding and the numpy/scipy versions match.
- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v04.json` and `m_decision_v04.json`.
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
| M4 | Refit-CV bootstrap for E1 at 2 s. *Superseded by v04 (R07b N-M2):* baseline failures are judged on refit-CV alone. |
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

**Changes from v04 (R07c; all made before any real outcome was computed)**

| R07c finding | Change |
|---|---|
| X-C1 | A2 failed at ε = 0.02 (OC v02). Plan revised (this version). |
| X-M1 | HM6b is now the pooled significance check. ε = 0.03 is descriptive. A2 confirmed on 100 fresh null datasets per layout, with log-SD sensitivities and power. The K5 power sentence comes from OC v03. A false NO-GO bound is given (§8). |
| X-m1 | Qualifier on when the criteria were fixed (§9). |
| X-m2 | OC settings disclosed. Expected dataset counts asserted in the merge. |
| X-m3 | HM3 power in §1 and §9. Refit-only justified by calibration randomness. |
| X-m4 | `fixed_rule_alone` and `both_inferences` reported under their own names (m_lib_v04). |
| X-m5 | "Course-change state" wording, speed-band shares, and the E5 minimum-chord sensitivity. |
| X-m6 | Simulated dataset v03 docstring corrected; criterion 5 counts any car-turning cell; both tries disclosed in M_SYNTHETIC_TESTS v04. |
| X-m7 | §13 row M4 marked superseded. |
| X-m8 | Staggered T3 start (run_m_main_v04). |
| X-m9 | Fault-tolerant 1 s and 4 s sections; the decision's exit code is checked. |
| X-m10 | `tests/test_m_decide_checks_v01.py` (10 checks) frozen. |
| X-m11 | m_data_v04 asserts that the 10-dimensional state coincides with the CTRA classes for Poly-MOT. |
| X-m12 | v03 generators reproduce v03 byte for byte (the EPS edit was reverted). v04 changes are in new modules. |
| X-m13 | Stale texts corrected in the v04 files. |

FROZEN_HASHES_BEGIN
5ff55cc6765adc08e3ffab0f11f345646f6bd1e5d2e378b12ba6f7da3e62e513  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_data_v01.py
d56bb0ead84e2a211b5d18d99aef4e70c6a9a777d8548d6148ee16764cb9e924  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_data_v02.py
2b592de7d171e324f27edfbccce954d6882fc5ce73fa5ef460c11e758c303064  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_data_v03.py
67bf52a950e299d3775ee9f8b357dceb674a14ac2689d087a8ef1af189ec633f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_data_v04.py
b11c51bbda1dcb9956d9c912da8869d0c45dfe15c28cfb3340693e9d7f8d1a19  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_decide_v01.py
0432142799a042de2becc71444bba7e687335a3bac9261b7c9941593527d7d33  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_decide_v02.py
d634c01ae3abf7740dcb6483c746a4a4bde7693afbd69beb53b2cc22e39f3556  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_decide_v03.py
6bb362505eadd8caa0300f9f609a23ddb69e63b8973e5e01745ac47dfc24ac84  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_decide_v04.py
d8783e8e032db3015d6b1d170216fb10a02e4249e215749f6e06b875b353b26c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_freeze_v01.py
27c0e3c11c39af77de6189a4d5065e304c8ebc6e37f62c8826a593602a6b661d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_freeze_v02.py
9065e9b397187ec06ff80b731ecf6189d45eaec9fe6ae2daebad79cccfe39be2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_freeze_v03.py
0cafdd569aa886873b448ea11b2cdc4eff363717071fdf9fc1bcfe13a258b774  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_freeze_v04.py
c79897c8146d05d10438f6d9af4f6267aa685642eb845f1e88c835b5a75b70ef  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_freeze_v05.py
a07ec95fb9dfa11ba9da53dc847273f18ee35c4cb99f64ca77fce44c7e734da8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_lib_v01.py
1fdc76491d842526d60d04be6194d5be9c56dc9d2f5c59c06a00771683036631  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_lib_v02.py
7b0f35afe3acee130d950bbb3999d3b2692ea0c8c73c7c9614b1c7e600879ff2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_lib_v03.py
6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_lib_v04.py
c1a213c5ed480dc8d6c25af38241d3aa20d880fab53741f94c605852901dee1c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_run_v01.py
241df160669e6e631581f327592cd5e89fc5ac0dc4b7184c1c5a70b0081fc652  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_run_v02.py
71336bb3d97f74c5211583effdad763cf8036ea4f74f6efa8802146ec6f11826  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_run_v03.py
bfe6047b48902b195361a409f38cefeb7b0c451628918488e7186cfac5a20396  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_run_v04.py
3cee0f2bb3d6daef7e5c2f1a982783ea1c99b77ac283d92b4574ed9dad887acf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_sizes_v01.py
43411481f9d011fe13b9ef25f5633a0b925b4951cf105689124711effc9e389a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_sizes_v02.py
977036b0d6ddc0ced969da62fe84391a8f21cac555fafe4579408dc5c60b32e9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_sizes_v03.py
0bd9e4212af9d741d8dfbbbe635b71465bf09ac74eedc00b249149affbdc3a07  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\m_sizes_v04.py
c03665f8466545f60a2fbf663bf0c8ba3e690520c06df70e735e33711b0884d9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_main_v01.sh
652c28e11e28f1e804a3e1541daa5f627898c4c01d6e9ab364a6f253b51d8685  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_main_v02.sh
95295a860d7db5d4c6388b7527c1eefcd23fb469fd78c3f711148b17c61fe54b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_main_v03.sh
e24525ffad92e1a77b38a91a3fbae90f966c46ea79e3114f880be2d734dc0cee  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_main_v04.sh
4875d4ff303449b9e3d3d5b72d5f1ede58f0596bba2a6df2b58195c85c51e635  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_sizes_v01.sh
17615156c4443500c58f0ba98c902a1cabb35356b394bb548d3536e533f59b12  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_sizes_v02.sh
b25501bf9626ed0ed60e9ee3ef2b31a309cd498087fec7b3c2a905af431cc622  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\run_m_sizes_v03.sh
1712d81f33bcf6655949f2511e34f28d29155afe526b68bb992d3f1ea15a0781  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\check_sim_e2e_v02.py
a4aba1c749283df1bd4a75bb998c5c4e92821e212ebe458d6c8b4504dfeaec19  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\check_sim_e2e_v03.py
da48a28014cf58c2207ce707dbc8873969ad7f0774f4cd31fd9711379d5ee939  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\check_sim_e2e_v04.py
415b6057349331b5a31fc5985dcde06f4478f50436eae6012663bc8353ca7c23  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\derive_eps_v01.py
6d1cc7899814fd19618eb138ed1cc4f5b903138840fabb06fb47ebcecfec51c4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_freeze_v04.py
07e7be5c915b89b5a8da9d04a6a0e9b8a8ab3a4bf9692ee4073fc9dc39f6bd91  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_m_lib_v03.py
2e76896138d5ad582c5428108d4b52be66aa75f2fa10d297029ff1be361fac97  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_m_lib_v04.py
3afc1958375b429a53f4cc02032234c9da17a0f2afcad58e4d761ebf6ca9bbd9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_m_run_v03.py
4cb5fe33075aa5ad16f9bb0da7ea205853905e331e46774f5c13c9e193e14612  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_m_run_v04.py
ccfbf94e2bd18406e4682aec4f65a05937db0dcfc5ab94a6649a1d31dc83cac2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_sim_dataset_v01.py
ec44455491c4638ae53059fcf9ae384ce5312ee628075e4ebd7f02fb8a347f25  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_sim_dataset_v02.py
0ac85de4bea2c78c6228ab7085e47c72b651a2bd100360b0bbfcf47d8c6f4fbd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_sim_dataset_v03.py
ddcf12f0d9700f4903e3be0ddebdd4c495284427ea20f32f7b50825ec04072a8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\make_tests_v04.py
d53443890199d45a3ae48c09664f0e55013423fefc030fd380f1669e9ec749f0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\merge_oc_v02.py
36756cff17aeccc0c2d62645048fe6a427be6ce02abd3ab6ae2edb8128a5a9e6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\merge_oc_v03.py
709984191bbd2457a1fbbbc105c7ac969d7be80b28e64cb70041f4682b51f271  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\merge_oc_v04.py
86c75cba09a9e1df56a31417b3cf2e984fa8dd56f69bb307576fb8496da39bff  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\patch_refit_bootstrap_v01.py
4223ac3c36ee57f8462ac7f59e60ae1038da3199de24d0a8c778b9ef73cf3a2b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\run_m_oc_v02.sh
ef7af1a50d928194615c29aa17c0735c0aec6c0414ede73f4a6d80a9c000ccf6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\run_m_oc_v03.sh
fa157b0a5c84d9556d504543116e5d581cb6de2954f3d7d15260154c3f28ac82  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\run_m_sim_e2e_v01.sh
bb7df8f9570e1ad4db70b1fd65c537ad129abdd05043db2ef3cb9750def988bd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\run_m_sim_e2e_v02.sh
f45575108e46500f351847c6980adf8403ab4fcce9667dc6a9974bed2c4f78f5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\run_m_sim_e2e_v03.sh
7b9effa085d034b17ddd4afe7f3ceeac3c2679bb6529f52dec7e1f74d6e3ae6f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\run_m_sim_e2e_v04.sh
320a4f5ae53205837650bcb84a551cabfa8f646bf111d925373d70f1900d0646  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\summarise_tests_v01.py
abaa0b066fa111ca3e538aef8bee2c0b79462109aee6e8f23dd667cfa1eae8c4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\summarise_tests_v02.py
c47cff641e5aadb6acae9213e9a8409e26ea7c00e6d749705c1a88f35b3d93b7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\summarise_tests_v03.py
47538596bfeea0792e9a9b2eab3ddada0e18b5dc9159122e00cb45411931b63a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\summarise_tests_v04.py
49f9f5843b43cd7d50b45aec78e6dcb58eb169dbb25f479a11b60e8ebff912fb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\summarise_tests_v05.py
2f206526f9dbc4b8def536930f11c5c87fec7412b06873e443779cffcf4b7981  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_export_velocity_v01.py
a5af6a2eca2bf23c37dc22fe0c56b1696462545540a0713214ab516c84a3b42b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_export_velocity_v02.py
aec24773f655ed6b2593c9bab883b525f329404f5c2e7f88113c1d11147cecb5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_b8_v01.py
a0b3311730cd58dcd625c691f0e69f24583936c0c9f655565225fb2035c2a18e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_b8_v02.py
986a022432a0940ba48b548f0b0db980960754f291c39601907ce9c2bd06d413  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_b8_v03.py
7644afaa6f9d6ca0da18961114e1e4cf1931941944b28c0dbdecb47755e1c88d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_b8_v04.py
2ba1a07e7834d854440cff65ff02c7764c4ed12421dcc90c03d4c0d9bb8d0a08  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_decide_checks_v01.py
f16aab3303d8e0707e205212308186cca1b700c0f38be726abcbf6e6d348ead9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_freeze_check_v01.py
92fc64f17f470d66e88cbb0145d375f0cb149e1752a492e32f91fde3f9c6d416  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_freeze_check_v02.py
2c4b09de9e292684942c1c837e283bc8ec3538f9c6def069b0fa7bc1260a349a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_freeze_check_v03.py
c010bbc460714ac15a1596aa8914be5c243f6d55fd54bf0c343224c8c43e5528  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_oc_v01.py
9eb5b71750ac3c8a00eb7cb44ba0c11341235e695e863c48a240fd033fc4a642  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_oc_v02.py
433b8d01c0beb7d819990c5426a6e93bfc0ee059b7baf7a8ae5236ceeffa011a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_oc_v03.py
b8e1e852a839f4323d6e7120d5b1dca6e429dbfa0e8aa182a1aa505558ee57c2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_refit_v01.py
575c0cc3193e229907f04b5f58226317d3bb025401836eea925167912eed9f15  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_refit_v02.py
d48a3d10cc8b7cb7fbe58fbd338fdbe1a9df28a014085c73a25ba91122cf7c5a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_refit_v03.py
f4b215a8713a45b69ff2a1b94c46fc384beabd8ce9706be34a119229785b6ad2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_refit_v04.py
d0f56f78b2b23379198da732e9570eba01861ce12e88a7c32edf5c38c38fa227  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_units_v01.py
dbaba607415dee994f8dd925fcf03c49deac144771646f4bc8ea7244ea7415bf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_units_v02.py
4643ef015e5e054111535ccbdb2c70166f0682603ebee04b1c5c342383470c73  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_units_v03.py
205ea597d6fc7bc46335b08bfb8635f8d8891830bf0be5374d857f537f53400e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\m\tests\test_m_units_v04.py
f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_lib_v03.py
3dfb23045fa2f8c26ed616120068886b196aa8062e3f383f0a252c95b46ce76d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_export_v04.py
66d61a241f4922ea450d5bc0f1c22d8cb9a4c4e55cb1dc275ff08e5632be40e3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_export_v05.py
b55f767cc533f1f3b526535d96a8387838545eacef054a54b772066c60fdf675  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_export_v06.py
e3ef0767559be238e36c0fbd73e31caf05b0caef0e4da9af5bdeef3c7d646bfd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\tests_make_export_v06.py
d58ab11db1eeb163bc89202e8d3ec8a98cbd33956c84c5a9ec076845565268f4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\fast_convex_v01.py
b823756f19ca23d4d36b6d97249f647182eee20a570c2f92a6149aeb2908c3e6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_horizon_prep_v01.py
68a75062b081eb87b27e32ad9e9b0726d8b987399741d9231d235672790e6ff1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_horizon_prep_v02.py
927b36be2ab324d2f6f4b291e5eac13030e9d7b1ab05256caad92c9a477a9351  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_horizon_prep_v03.py
f38779326bb77649573c8bf287b66ff8955855a8b52ba3b81a67260ebec26115  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\run_m_sampletv_export_v01.sh
2ae08695e7cc86a00d63d5a90926a76b3c7b0eedf977b82eda2895dca5c318cb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\run_m_polymot_export_v01.sh
2188624b3327658f6f56a95ab2e725c432f69d1816eb931445ccb20b62199e79  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_gt_prep_v02.py
d0d3b91c30ee78c277639ecbd94b69397bf6bc4153752b3ebd070288e5894b89  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_gt_prep_v03.py
b19c4905d23cf94e6f3404d7ba950142afb9fd370805fa101ddebe88e133808c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_split_detections_stream_v03.py
ed219e9575f293c372dd3b5817d9be0f196e76448e122f4757035455b585fb71  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\src\canmot\motion_module\motion_model.py
c10777ece387eb03c4d8f1295d89298e1a5d44ecf882fefd7d3ca7d6d18a02c4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\src\canmot\motion_module\kalman_filter.py
84702b154e48227341cb116f1815fa31fea752e59d4808ff4bf725d797bdbc7d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\src\canmot\data\script\NUSC_CONSTANT.py
4791cb038dabef49de0c6be1190f147f87aa6a1231ce5f7edb9f2243a9ecdab3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\config\experiment\paper\baseline\poly_mot.yaml
96f6ff8b7df8f6ad779fa3c74a26b06fef912474c9f2f2dc73571bd95b0e882b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\config\poly_mot\nusc_config_poly_mot.yaml
f6387a601bac128334ed5a007189ab09e9b964d6e6738a71b1135c0d998db662  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\config\poly_mot\nusc_config_rotate_cov_cv.yaml
728065f00896d7952e3a393bd661a233cd28123b2334a522a0d9d36b753bb859  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\config\experiment\paper\local\canmot\sc.yaml
62bd68c909bb098348685897540a0c307c90a5243ef85f74d0fd8ab062e4a9e2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\config\experiment\paper\local\sample\trainval.yaml
0cb1e5189a09dac62003eeb3ffb5391fa01fa2a1722198fcc73da7e438f4eb17  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\third_party\CANMOT\src\canmot\pre_processing\nusc_data_conversion.py
173bca05c098ee6571a2a4a81ce08c0af8f9ac5f2bafc5ba82deac6e663b21bb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\M_PREREGISTRATION_v01.md
c4e8560456a1142b80055f29614f9fa009351001c88016eb8661e8089f6b178b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\M_PREREGISTRATION_v02.md
cec106eddd918aa5a0ae7f881a58905d41e4b1fa4e435a32b0a6e9f842fe9db4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\M_PREREGISTRATION_v03.md
060cfdcdad230fb78fbc585ba198ff06407f13057a5a6635dc27105255b16187  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\M_PREREGISTRATION_v04.md
0a8579e161974d6626a645ae2968ea715cb516e90f226724e3cb64b3b11b6ee8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\M_PLAN_HASH_LOG.txt
41bc5a936684dab6f6978c7d54e3d34c730afe7117ce62571b87bdb40aa447bc  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\X2_PREREGISTRATION_v02.md
f598a772d88d86e8abdd939ba4b02f63354868abdca22ef3a5d3b9ff740debdd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\make_plan_v04.py
8d0325b74f3bb701f1f0e99019c888880bddb64938b3799af90a86e03f67c719  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\make_plan_v05.py
666ec27d7c46ffde862a43316dea50ea58a1008fef0eff3b8a487b2262cdcf2e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\10_PROOFS\P02_METHOD_PROPOSITIONS_v03.md
ecd9ff5135579f5480063f82f6f10214e56616fa1d92da28862a8484896ae174  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\R07_M_PREFREEZE_REVIEW_v01.md
b391e39da55ad40011278fbc4acb10ccbc4f6e1cd509c2528f4f2219c80cb8c1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\R07B_M_PREFREEZE_REREVIEW_v01.md
0f70f02ad83706786109b8947e6c15cca2ac637d87897d5cae8c576443310744  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\R07C_M_PREFREEZE_CHECK_v01.md
d4385cd11734d039c5710a06491f1c1f89a83be801d4925a6b840f1bc3aa545d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\80_LOGS\pip_freeze_canmot310.txt
93b4ac8b234f87ac152ce71c26e70e8bdb9eeb656242a44aa68bd654d5bf3d58  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\x2_gt\x2_train_gt_v03.json
0c9e4b92bfea0340aaddd37cd756a4fbc99672a6905b0f2a17a82fcad14654e0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\x1_gt\x1_val_gt_v02.json
bdc3211bfbfda652d5e9dab73c45c7132925ca84f869bf45e8e14edeafb1d20b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\nuscenes\v1.0-trainval\scene.json
1d2652e8055e26aa97f1d79a5586bb10196687856b6d8a489e1e71c580bde732  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\det_subsets_train700\split_receipt.json
56bb3f19c8fbba072f1a94c7a437924624344371ed209e912e8408242f4ce008  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\det_subsets_val150\split_receipt.json
8da9170cc0a084198fc7aa2a6fc7aa09c9834e499da1babfaa269b8ff2df72c5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_horizon_v01.jsonl.gz
e3e5071ea83d4f3a658f05294e608c32e82a8acd3807e298c2600dce95053f70  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1\x1_horizon_v01.jsonl.gz
b000cce3cc86d3552c9b06a5fd95c2313d0d820b02129941a89be00104025359  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_fast_v04\EQUIVALENCE_vs_native_v02.json
8f28a1ffed3bc5a85029265f2712ec7d76c8e83a36890599d216be4196bc3ac6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\horizon_train_v02.jsonl.gz
5d3588d6b69d9c92e20b120fc8dfa0eb540305ea442a475fd8f314eb80cfe5db  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\horizon_val_v02.jsonl.gz
5a3a5785e55f8339d877b4bb7a6812ca9bf3b1d06b796b38be5a2f1a0a7d875e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\equiv\EQUIVALENCE_native_vs_fast.json
9502eb94cfee376266c43473101405c83ef9fd6b19b98fba6da8c13219e253c1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\horizon_train_v03.jsonl.gz
a0ab4a209cc42000a4ad98dedd7b2dd1e302b483d50f6d2968fc23306e4d7ba5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\horizon_val_v03.jsonl.gz
3e9761b7575e6bcc48bf974ecf3a7b0f9552e8d3e23500ed3894bd5a722ebd03  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\equiv\EQUIVALENCE_native_vs_fast.json
964ea1889ad5f40dc3491989b2d37739c824dc35e2706002021a832bd07adb7d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker0\x1_tracks.jsonl.gz
a47deef7245ad50fd3da2f7af17c1084edf4ac34ed67c0990df7398c2bb57aaf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker0\x1_export_record.json
4578355659dc7d5d019f9f44a6c38ba148653d7d5ade12c24484af717581f662  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker0\x1_per_frame.json
eb25f03fb7ed1928897b3790e6eff29d86417dc8e71775a4e8ee516e66d973bf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker1\x1_tracks.jsonl.gz
087136358a091882f58adb733ebb67c174008765de2c1fea8e7826c4754fa0eb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker1\x1_export_record.json
a0d5d4490176a68af9544f0a7501c76bb00e68828ef7206e976b2ffbdf0b60e3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker1\x1_per_frame.json
8ab657fc4b55e406e308dcf9c4c5bda14e2249ff5318fa93f3811bb548320eb2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker10\x1_tracks.jsonl.gz
17712c8a41832e22c0303b5e4269ef0e0bda76a0fa4d0323804c305d19ff67ec  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker10\x1_export_record.json
18068cdb08a73e56225ed428dee2c36cec436a1c143691d72f97478d4f112200  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker10\x1_per_frame.json
3846f0774e223b974b89db6892947b7f4cf72bbc2cb88097b6f6d596cab23c4b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker11\x1_tracks.jsonl.gz
c780fecdc7bc40195086b75542828d6300c75ab77f77eccd3a13558c46ff77dd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker11\x1_export_record.json
c1197e13ea84231154e0e9220d05ba1c078c91274b843544bbcc6190e53910e5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker11\x1_per_frame.json
cc3200e39ede625b6250355fcfd0c14d534c7caca782a71a1739779851eea8ab  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker2\x1_tracks.jsonl.gz
87488c81449303353e7ac5546bac7471c4821c2e5ad48d470d20032b27a38e4a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker2\x1_export_record.json
1412d3e19f3806a681c7c30055525f2a9f4657f0c09e82c8118a35b0602a7d85  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker2\x1_per_frame.json
684bed144db5c142855025bfd3f19934b7957549ba8dd5b6e51f27464b617073  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker3\x1_tracks.jsonl.gz
4e47d54b471c902c2db1df85813292fe1ae49f4e4277b89206f60c3c34bb05f5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker3\x1_export_record.json
c1f551e3c2379578095b8bfb23a8f87bb0a28d922a1ab56fbee32299dad5b4c7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker3\x1_per_frame.json
00a146675e7d58b586f96cc1f0563e7f461e45db4e0c00a88d3b590dde5d49f9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker4\x1_tracks.jsonl.gz
4e6ca9470f2cea2ff7f9648144afd46e1ad08da1edbb5c5bb8d04cb75d22b332  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker4\x1_export_record.json
1c36ee1c01be04f4259045571aa9c35cbf2d4f70e7453e4f8864e1cff2f66ae8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker4\x1_per_frame.json
9aa13e330e5d12cb267b83e9b88cc196299d7ff02bda096182582aca3fe829a7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker5\x1_tracks.jsonl.gz
9cf0e1f8e43671116a343321464e6502196df0f0376fa9eef9952162422e807b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker5\x1_export_record.json
98d96b5ea04e92b56401eafb250e615c4674a09fb5dd4989d0a7721675387a31  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker5\x1_per_frame.json
052fc67cf16eba81850f88b0cf3cef96d22fa6396ffad164811427fa16665fc2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker6\x1_tracks.jsonl.gz
f33ae2fc3296740b689bdfc99eb8c558b3e621c96ceaae8f8249d72f370ab362  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker6\x1_export_record.json
2b40513f68dcf9ea2ac60bba9044e31605253aadff94b3e4bf6aa44c677fde48  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker6\x1_per_frame.json
465efbd545734133e71a9e56db4f845f0ceec63417f274322069bb8a0cb6b521  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker7\x1_tracks.jsonl.gz
ecb6be3b3e78cea620a2274b2569ce1b646058e10eb4040f1de3dbc5972aad3d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker7\x1_export_record.json
c9827c4cf4fe1a3a2af46b0d84f3d39ea035071b376c4f97c53d5abce36264b5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker7\x1_per_frame.json
1f5c09af8fd0fa71c34c38c4d5ce43943121c4e7d0b0d0c75ac3fa4337608326  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker8\x1_tracks.jsonl.gz
4614de1dbbc7374c517b52715c6b5971099675314e4b41ac66810762ded9b8c7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker8\x1_export_record.json
ec59b0018fa31ca4ef0bb94e9532f0c9ba75abb9353a0962f675f74930f48b35  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker8\x1_per_frame.json
c00f26f4a2d464490176946b2215a5981f7b237a014888f185c9f3b524fc93f7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker9\x1_tracks.jsonl.gz
fbbfe86fb09a3ba35942f46cc2a4ed462d45389a4193dd444c7c28a204835a5b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker9\x1_export_record.json
4ec4cfb619647908b65303425d5fc1c42ff6fe5c077747d2d60fcc257b367819  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker9\x1_per_frame.json
5037c2c0bc7140eb72c603b5d16a6cbdf44584b131825debbf1b63e4c1f0df24  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker0\x1_tracks.jsonl.gz
adcd8475ed28bbd818b2bb282053496c65a7459a72b01773c68b25eb8bcc9b24  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker0\x1_export_record.json
2043c203db9c43ba21121c9c9c2c924c4cbffe0c7c161f1731533eee94f8d588  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker0\x1_per_frame.json
42f8433403ec9f0d441c67b2f79f72e8ec8f75a67114b024f9a3f31eaa33ae4f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker1\x1_tracks.jsonl.gz
49236a20107f094a27f9491fab0637a1bc775b15ea5f946d5b4465cb3b02b55b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker1\x1_export_record.json
52874ca85f0f798c2e904d87cd75d4c3d7ac27f29d381c38d9f65ee16e8af6d1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker1\x1_per_frame.json
31e82ce904edf1201b1d89fb8cfc05e43d5cd130a119ecce71dfb9b6b189027a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker2\x1_tracks.jsonl.gz
726bb8bec248583256aec09645abe8a26b7d8460e9c1b1352c819883ce4a33c4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker2\x1_export_record.json
8fbbca8c0b252e609eb96a9ee08dcfe0c6db7ab59e6f5fe41ce73f4d6e91526d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_v02\worker2\x1_per_frame.json
43bc1ce2c9308de4a2ebc6e87d9883cb839ae915468941fe927f9069fab34b06  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker0\x1_tracks.jsonl.gz
2689cc62242b6a2b041b36acf0dcf2c057677ca2eb8fbb0e927bf9622270a4c9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker0\x1_export_record.json
2fc41b1ea771e68919fab6d060ff6907b2780ff95fa2e7e9de7bb72df463c975  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker0\x1_per_frame.json
b47186f3ade0b6cda1aa395ec154823094dab941e885a188e57270ecb4f932c5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker1\x1_tracks.jsonl.gz
422b511591fc0b4845f1cee6a79fe8a1db3ad54abe8957f24e51d7b2e9669e8f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker1\x1_export_record.json
4371c73031e2a1585b5f6184f1ae62c64894a27db402061149ab0e16190314f9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker1\x1_per_frame.json
242fa05bb2847cb2f8328dd7425e914d922e39b2fba2189625668f524a690ef4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker10\x1_tracks.jsonl.gz
9a646786674f72f849ac331f477129603c7e7b5889f41bb03d27c6fad59f4f04  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker10\x1_export_record.json
93568a2653649a61102331bb4e3b96707b189bd927f2d044cfe3bd218039d053  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker10\x1_per_frame.json
794a952a82e34309ff4ce9b6c8e0d38308c31aee74e1845101c2f4cd5fe89ec1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker11\x1_tracks.jsonl.gz
9550e841caa2452d5ae126a761ab717561b62817e876653c8569a1e0e83c1bd2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker11\x1_export_record.json
e17bd242768374aa0338bcfde78a913b4c31b97e0c2bc4a58b69a0d2f10a79a4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker11\x1_per_frame.json
f87d77bcdd276a0f419afcd5854fda5f8c92d503c0057ccc620344d6b58efc2e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker2\x1_tracks.jsonl.gz
30731a37ba4be0160ae62895c4aef29cbac713321e8b5a1984f79a2e58a4aff5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker2\x1_export_record.json
eade0002e26963140c921a2c25f5b67ce95db8277b30f7ce95c02041aa3f6823  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker2\x1_per_frame.json
1bf0d200ad62b2d8cdd5884c0e27292888dbf78a752c9bee0c87299c70bfa0c1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker3\x1_tracks.jsonl.gz
965f1d7439652db2107ba940e0e5c68b962b666a53065e5e4940c8304f39f113  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker3\x1_export_record.json
4ac863209574a333ee40a21d382ed1ab02d3974234a38cf2469c9d9559f21f3e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker3\x1_per_frame.json
e86dcbe9128e9ea2febbebcebe341508f464cd9003fd592a38e3e1e9142d50a8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker4\x1_tracks.jsonl.gz
22afbac92c6df15e22e1aedc909afd39ff4f560e875ebed6e130b2383fefdf62  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker4\x1_export_record.json
e8af3fbdd992605c344647ffb200b19ffd3c405616e770c93437db94a7316c17  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker4\x1_per_frame.json
bc36bcabf2380cf56357b37e2114ee65855fca2aa9e745caf1b788693198fce7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker5\x1_tracks.jsonl.gz
27de980db76ebfd33715db25f2cb7bd9638c4d44bcf2fba4b69459c9105ec111  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker5\x1_export_record.json
e2d0732f37512d1e1c2bf0b7e10fb16c2085e5da01cf2770de31979f00d85b51  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker5\x1_per_frame.json
41e4bdd626188c701ba78eceae05b2cb95b49c422dc457658b34deeafd179516  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker6\x1_tracks.jsonl.gz
33777ae0609dd7e99fa94fbcbb7cc71de4173c9491110c28a38cc8b3861a4130  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker6\x1_export_record.json
2b75ffb0b9e1aedd2515c860eb450dc6f8d05fed1c8c57da49bde12b2d501ac4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker6\x1_per_frame.json
22e8198a9586b8318746e5e02a7ea125d0da615bb5e2508e9a9b255122220fc4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker7\x1_tracks.jsonl.gz
8800129deb3622f3f182869ef448ffaafc156606bc2401f42ccc90f3c3612780  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker7\x1_export_record.json
ffd16b348277a9c345da12e7b4b317502601fa57cb921afa17be17af8eb0de98  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker7\x1_per_frame.json
5b2decbb2e9f4364a7bc2ab79e12bb88126804ccc477553b56b5cfd875367081  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker8\x1_tracks.jsonl.gz
ad33ae6130ae62990e88ee65681768349e4e20cff256c613141e7263bd5aee67  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker8\x1_export_record.json
eb7358262b88dc48d86cd047de37b4f060b4785b2c14633b9635f91c623f37ae  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker8\x1_per_frame.json
0d91c3aa15969d3d909eef08396de7d2328278c6b6710fcddaf33a949c2f9605  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker9\x1_tracks.jsonl.gz
27705bd099f1dc977dce7047835629c41149ce84761a98ad57866de2749d3d4d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker9\x1_export_record.json
5ffec32d6cd4d92f0fe6224225dd967653788168c6db413d3a123eb4297c7535  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\train\worker9\x1_per_frame.json
0fbfadcb8a3c1c02b0562d4518534541c4890f6bc215e5f9be20b1a40c30b2dd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker0\x1_tracks.jsonl.gz
3a498c8112ddecce2a24e668d9095b2bb0b35f589c8072289e66015872829d4b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker0\x1_export_record.json
8669a3af6ed7e4052d4ffe1f977dfdecb35c51720d472b1b56d07ec50aafdb2d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker0\x1_per_frame.json
e6989fdbd02cd9b3d6aa1cc0018c0517cdd4b1eef874356c2b9b8a3561f4b1e9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker1\x1_tracks.jsonl.gz
852a469ffb1a93b7038bed6c06122d246fc82e17bba8dd03e7216880982fe440  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker1\x1_export_record.json
7144d9e44dcaafe2c9ab3ed1bda73b805b0e096ac38b3c5b69761bc6910651b3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker1\x1_per_frame.json
803565fbafc7ccc5b159339156d60e2f9e221c517d8159e5d18e0bebb894fa80  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker2\x1_tracks.jsonl.gz
c08b339668a072e221172e7fe95beac29b27013871af4b1bac4b882d886aaddf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker2\x1_export_record.json
025da612517fe7088d8b625dcebe5ece23e1fa69a8b04de6c656390fdb70ac73  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_sampletv_v01\val\worker2\x1_per_frame.json
0b22753970987b815ea85897b72caf4ee5f043c6c37d4d1a5886812b04e6275a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker0\x1_tracks.jsonl.gz
ec7a2d95e04a77e928712e65a2431d56b482763fe9f6642077a8665d5455ae1e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker0\x1_export_record.json
4e262573cd5e3985bb97105fbb35a048137de330396485dbd15d7370894f796f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker0\x1_per_frame.json
6ae2d48ed9c1cdba7372c8e5d3bda177fe0dbde58992a3e064bee95e09e7d0ab  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker1\x1_tracks.jsonl.gz
ecbe7170148fec5ad752e552214f42c1fabbbedd6194139c362b686a14613302  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker1\x1_export_record.json
4e3d988d1e2f9c1f3afd8981f19e9f3a9d769e9751accca27c7d907536233246  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker1\x1_per_frame.json
5bdef048b35c124c624ca40e90b34d0fd59c8b950da626c0ee471316dff57c8d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker10\x1_tracks.jsonl.gz
8f7a94968b9c62bd7bb0b9d30c72fac79a51b04d210fba6b17090c6cd20f7855  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker10\x1_export_record.json
53aba6005823817c203d502110679c3e05680b618c282552b4181134f47dc53b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker10\x1_per_frame.json
351c478ae2eb74d5f12133138533971e7c6bcdec6c4f28b3986aeb66c723ab7b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker11\x1_tracks.jsonl.gz
f444a59056d2bc25912c1c79e40ce53989da42c1ea1b87621714c43dbb709d00  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker11\x1_export_record.json
352c573bc70ee78a5b4951e76b4d894781b9046d27926888ef073edba1666f7a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker11\x1_per_frame.json
45e1f47adb35d427d77ac569467cc13b8fd34d11a9ffce77bfcebaf68fa6be7d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker2\x1_tracks.jsonl.gz
8e5389c9bc026cc4bf276fbccc82db14623839abee49c42291ca3695c74c7a33  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker2\x1_export_record.json
a776ba7a4dbf16030cd48c08df763bf86c1a7537a2941d8e43ef1c05b7d9c1bc  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker2\x1_per_frame.json
13ba9e1fd0dfa1e519338e33a4063e561420154f12ba5c7ce689a9a0ae28921e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker3\x1_tracks.jsonl.gz
923b8e7eeaa3a9fe9ad426a66b426b61af6fcabd8e436862020ffbc4cd8c6ca3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker3\x1_export_record.json
9986b41a5082609e6211915f78f99470fec1eaa5219c6b02a524e813ba775414  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker3\x1_per_frame.json
32c02500d00fe180028ad7ba5238681179021727fb7940e9e0ee7cc58f035f13  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker4\x1_tracks.jsonl.gz
4add48a25b7976a020581eb9abdc5abc7e4349ebb232027aca0693d055c0cec0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker4\x1_export_record.json
1683ef11827e6850ea6317c8e989daeb2960bbef5ec1656212c0178f3994b4c1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker4\x1_per_frame.json
611402565f70f787a08e4040230049f2f5fe927c8468478d32f24268db5107f7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker5\x1_tracks.jsonl.gz
303fb4cbd718be27d97ffc6735b7b75a915d037a542a97d98f58b83971b7f3a3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker5\x1_export_record.json
cd435f8293a89816652af182f95b3342440e58d31acd3681c982e261521b720f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker5\x1_per_frame.json
83ef6af7c68c5b198fd1229cde886e3d2f34a5ce9503d90d5e743852a45ff281  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker6\x1_tracks.jsonl.gz
26097711b75d1a3e7ca1690cc110bf02b21173c97d850cc8321e0edff9bcefa2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker6\x1_export_record.json
b12ed4b337c8024a9291ed9febbade2883ad486cfb79d1930cd164bf9f3d4d3c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker6\x1_per_frame.json
8f90bcf5749a8248a150eedf56aaabef537b01e9462ebced17756dc8a2a161fb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker7\x1_tracks.jsonl.gz
a026f4872f0b6357a2b18bfbd083655bdd114a7396785d89dc9922ed7959771d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker7\x1_export_record.json
ece92708d7148ac0bf4e57152139ef4d097d7b767eb11adb867e97cdd6dea16e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker7\x1_per_frame.json
3912c3269bb39dac758c44cc100bbee234b07e756e609ed93d67b370dc3d8d8b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker8\x1_tracks.jsonl.gz
d83205bcbec65c92f562b56ed7f4366af69c381e4fda1e1473c2436a450399ae  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker8\x1_export_record.json
0b7c08d4310d7c7034250cb25ece806bd8584b83d6dde4f96c33aa4be45cb836  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker8\x1_per_frame.json
9cfbb47a6d7dff0dec84cb4d024fc8499295415e1e85a666cc05daf793dc6ee0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker9\x1_tracks.jsonl.gz
f7031a6027a03357fa3f7d150a2c8845dc08de5bb50e7ee01184523006d01a89  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker9\x1_export_record.json
c636eb5c4666358bdf21952ae16861fe1bd599149b93c44a03f8f0cff580290a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\train\worker9\x1_per_frame.json
c25dd731a5d8db42b95711ed239807dc7449fec994262253fbd02d0ed025af77  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker0\x1_tracks.jsonl.gz
c5d1921e0b990e32c1658a2f2de001b1d6244579533f6521021a4ee770862d4e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker0\x1_export_record.json
5853c498f203b1e4f3b43a4bc8c57f1eada81837dee4367ef2bfc8f27a1dcb89  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker0\x1_per_frame.json
e41da65985ca38b7e72f391b6cebd94ba2cdc4a60c5fcd9a669dc47cea76ea06  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker1\x1_tracks.jsonl.gz
e5a7281046850099032f0b66a40b03c1d213aa8044e71197966abdb2d10782a8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker1\x1_export_record.json
1a0a899b8636921fdf07f2c162de22adfa60682a451c7c0acbba1fb7197cad5f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker1\x1_per_frame.json
d14194641f7dd9dc04c4116f510b0b1ff9696bc6d5c244295250133aac43cbb8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker2\x1_tracks.jsonl.gz
6035f04aebe00c78e06c0c6b009bfaf659d1f5b141326b4f2ede4f789fab2696  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker2\x1_export_record.json
172736362005902bdcbcc8f2f224eb156b1f3ab2d607dd973c0207aa77286ffd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m_export_polymot_v01\val\worker2\x1_per_frame.json
38aa4a4e11d502e025cd62ca94909993b99f6663afb5743bc7644751f4558a41  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m\m_sizes_canmot_sc_v03.json
9b2bc99f5ba9778050b565b857016aaaccc2b2bac363c569fdd7a685a752b6e4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m\m_sizes_sampletv_v03.json
0e949f76941dfa28c7455dce61a11833383ea616ea65be2ba7a3670bd86c0d31  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\m\m_sizes_polymot_v03.json
797569f6a33aa24a95e6c5887dfd023c7bcb1b3132d5c8d8bbfe5def3034ebb0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\units_v04_reps200.json
dac854e02b41b097362651b3ccdeb1f51a0f56dc8adc029f3a906cdee7e68322  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\refit_v04_reps30.json
47d35414fb15fba14d22eb67eea20e202766559d3ef104a5e211814b97e7ad4f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\b8_v04_reps20.json
38ab5b610b3a1e49269a064a7b58bffeb3fcf700d38f0d501c96a2071a40815c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\freeze_check_v03.json
927082fc046a7ff1fcfe75ce81bed34e3e1f91ffe62f44c837bbc5cf1b8cf363  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\decide_checks_v01.json
277d544c6e6059268d99df48e593b6aa20943bf2b236d15ede3995bb66321d5d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\export_velocity_v02.json
82afee318520d9feb420f9da39c8969ee00a26d9a2f7714791c98431f3736a37  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\sim_e2e_v04\check.json
0c1177533f5381b9188433cee02f21eb9dec3db2daecfbcc9d183b8b56e46a9f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v04_T1.json
fcb8d6f4a097331f755df8ae6ec52299d05dc8436d8faad69e1532ed38733cc8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v04_T3.json
dc94e0e71108df80ae48983bd821308d8376c66afc09371ac04f0d3241b9b799  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\sim_e2e_v04\result.json
eeb9035c6ca73e0f5c621679d9b6c8cb9dd3bf9ccb5cbd68e6d56adcf821e95c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\sim_e2e_v04\decision.json
cfe227a878dee86eef523477727b28b372cc40eecbf8a7ac51d73a834fd8ce98  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\sim_e2e_v04\sizes.json
79e681b0d78784eece024a35d60519fdbf194fe349e40821a100f01c8d171ee8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_comp_rho0.5_eff1.0_s0.json
d968f63a7331b61c476dde3a612427fa3f00681248c455610962b2f84affc15c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e1null_rho0.5_eff1.0_s0.json
37ca7e367d8e2506c4a6d40392121c056d5b68a038d2d8d9e633e3d2aee85ccf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e1null_rho0.5_eff1.0_s1.json
c3ff99be78a041356a87cd41ce8a087c7ab1964c037bbabdad3aaef636dea579  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e1null_rho0.8_eff1.0_s2.json
12178ef2b004a38ba79c0271aa8282a82e213bd856642f0e9ea321c52caed62c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e1null_rho0.8_eff1.0_s3.json
12088c984661adb2bbdd9d6470156af6c7071e1ca7d1669b23a6c5f52bf55492  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2null_rho0.5_eff1.0_s0.json
e5d7ec8cdff4626b0f9c75ddb44843d9f61d515f2541ebabd200279d0897dcc3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2null_rho0.5_eff1.0_s1.json
323b359011c8075b1d1eecae27d342a9fc74d79e8fa8f976a2adf1846f013067  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2null_rho0.5_eff1.0_s2.json
bc80a1fadf06729ce576e423caa7de587ca4492ab06595bead89ffee1c995ef8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2null_rho0.8_eff1.0_s3.json
b92ddbd1c46b154481675d21eb340f0cfcc000c93709249be5776799b613fb9f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2null_rho0.8_eff1.0_s4.json
c5b67b1ea9ff53808312d78e515403b0a42907ab493ed64a8486ef39c1c3199c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2power_rho0.5_eff1.5_s0.json
a0690cbf0669b13918e4cd92713baa948365ca9338c974006fa661179766c042  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2power_rho0.5_eff1.5_s1.json
790b29b107270d393ac386e7a8d2acd64c145646ae46efe18aab6d316c942f19  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2power_rho0.5_eff2.0_s2.json
97c898f5504e186da90dc6c468fd0b40eeea1813e6bf2b9971fadcf3747fde2c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_e2power_rho0.5_eff2.0_s3.json
5ab5a33312e442e79d7c1287ece4ff1ad9cecdb474b05a5e8a8f8828c01b0a4e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.5_eff1.6_s0.json
c300d22d942d7cd1e81b8bfad90e316b5ef04435f0b963fbf20a745b161b69ee  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.5_eff1.6_s1.json
2781383bd1885436f7630691031cf55a2b7a6501b4016cf981f9fc24713e9389  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.5_eff2.0_s2.json
5167161e11be6ab39e9d5cf0a339d34a9a1f0ea154b705b60496d128b5b1d1ac  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.5_eff2.0_s3.json
544ecba9b807fb9024add7e8f80edebd5ca1bac8e299aae67717be8744019b9b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.5_eff2.6_s4.json
a1dc48d16a0c11d2fd82b4328e8125f47f1c7f9f5761eab54c9886670d5a0b14  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.5_eff2.6_s5.json
d20c4542578dcdbc25084bbdc2f9f260f1ec95a16b2925bb252ad8725df02e02  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.8_eff2.0_s6.json
204af87320d546bd8b9b759c56071cc9ccbfe7474648fcb483a5674351f949bc  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T1_hm3power_rho0.8_eff2.0_s7.json
be1dbdc7e2d0d65a43d43f5c02e1b3078156eecfedf75469cca588ec0c0f4159  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_comp_rho0.5_eff1.0_s0.json
fce80f64ebe847a88a7813ba57036d10eee2039c89cd86c0d75d691d55045a8f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e1null_rho0.5_eff1.0_s0.json
2fb3e0237be3e35a6ce6c5bae5383e7f8bb52add1467c920ff78ac95bb767f5b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e1null_rho0.5_eff1.0_s1.json
70c60d8a206816282347b8e09042104fe3d1c3da552a565e89c436590aada19d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e1null_rho0.8_eff1.0_s2.json
07ee7073d44917ee2da90129a0fbe03cadf9c5ef8dbd6e6646502ae98930298d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e1null_rho0.8_eff1.0_s3.json
c43e7913020369cefd287af6004cb09370453c734bd38eaf2e39c55f10b13611  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2null_rho0.5_eff1.0_s0.json
acfe1af4238de1fbcb26a497c2022f1ceabb85525a73d4e8f592282da6b1e4ea  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2null_rho0.5_eff1.0_s1.json
30721aaf94a618752f0631148e3b354d0c82494085e37975e83f237d754b31b0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2null_rho0.5_eff1.0_s2.json
110733a39363c579e7e62c45af70c120d7ba10f58997910e6d5564a64df5123d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2null_rho0.8_eff1.0_s3.json
701bd7b083d94f9745b4a48529ff8dfc4e8c4ffcfd28c2a03ade91f93c5c2d53  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2null_rho0.8_eff1.0_s4.json
ac3607aa0fa58c211e1e4167d8e9fc8b4fbd85da1842763d2b2499ff4936c7c0  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2power_rho0.5_eff1.5_s0.json
a4819fb90fac6e201929ed3ac3aa3282f96cc3bec20048b25ac19a3e921e43e1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2power_rho0.5_eff1.5_s1.json
d29e8f44b5fe96a485f0df9cf7c656671d00bf713e859942bca31de6c9bf3ec6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2power_rho0.5_eff2.0_s2.json
5260d6bb6cca459f815888d92625d20c1225679d9dfc3ac68408dae074f78a2e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_e2power_rho0.5_eff2.0_s3.json
d800c56a4ed0ee2e8abe46aa4f8846f52fafe115a7a110b2cab1aa6c27c91014  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.5_eff1.6_s0.json
c192a443a81658c721d5422451eb84c49c6ab890a20715a8541d1fca40dd2e14  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.5_eff1.6_s1.json
604b30a12eeaacbc1a72262cc3390d0bff98b1694b81b13106862644740ccf2e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.5_eff2.0_s2.json
e4a7892cdc63aa48eaadcc9e61cbd23e3cc892bd568d3cfbed1516dfd6074834  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.5_eff2.0_s3.json
ea690d39b3d8b4cd1b13ef0dc436cdddae7692a85ba5b50ca373773804b6cc83  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.5_eff2.6_s4.json
455aaf68bfcea4c1f41250f8cc86f55c6b3999998ca9f849d7ad6af8a687e3d1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.5_eff2.6_s5.json
7e623fd101a4641fbc382e2fdc67690922809d379fc6dd6855a95be0658a28d7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.8_eff2.0_s6.json
4ea3c4bf44f03f7f5874aae6b7d57e224fdc8753ad8e217ea1d13d6dd1a4422e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v02\T3_hm3power_rho0.8_eff2.0_s7.json
7988652611aed7ac0410b063984ea8a39f71beb5b280c7862aa37976934e2a7b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.05_s5.json
405eb56795b54b12e7efe6a8979ef3cb51c2c9e096f86ea30ae85c4d3baae4b5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.05_s6.json
1e22d944fa9a8818b578be2c5a705079ab4d3ec79660f96d66cfd2ec2e4c6779  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.1_s0.json
f7d5053e15fb3c5d7e2df3ca563640388761e6d91e3dadbbcbd3e056bb4b4b70  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.1_s1.json
01bcb30b79bcb9f98c4bb0dff71552e26159c5baee97ebf8a019cb1a93b76476  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.1_s2.json
56e03bf343a5e064c45e204d55968fadc1fccf0132238ff4c3a7f77b51bf99f3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.1_s3.json
d7b7771fb897ca8a998682785d41a941085ec9062eb4ab4f71e3a9a46b0ff11a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.2_s7.json
8990a919d096a7b176228391757f51b110314bf1e02b1872b4edec4c70288ba8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.5_eff1.0_log0.2_s8.json
0efe4adbf20f5d7d7dd674a999e34a14f6cc85ebccb3cfebcf2f7a10a542ed49  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2null_rho0.8_eff1.0_log0.1_s4.json
58157fd622c048238bfb4accd15c090c1acd7bb2f6208627ec80c6869367b7a5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2power_rho0.5_eff1.5_log0.1_s10.json
fbbd957a370e8f78bc0357660576639b62d8bab257c2b8472b45b6028017f232  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2power_rho0.5_eff1.5_log0.1_s9.json
9f09b12e797cfe897ff943935ff269efec022448e541667d9d4d9507886ee90e  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2power_rho0.5_eff2.0_log0.1_s11.json
8c551445e9d8bcffee893a306c89b8bc2612858f48eb44dad3e5fe3a70cc0a51  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T1_e2power_rho0.5_eff2.0_log0.1_s12.json
f0868688e6ecd887b661e52531a2458f43bc4213e4738c7c68986f7cba1ea1dc  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.05_s5.json
de92ce204a5f36b50cee4cf3e6c0950b4af5fc5d788dd6bb41984501b8183b75  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.05_s6.json
f0ea28abdecc1821b58ec03166bdb0c82d02c91483955c170ea13aa75522b506  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.1_s0.json
4b435215cfa650f6ed4f991b4e295bddf82f8901e918889f1f1141fcea32a792  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.1_s1.json
c478b4f3b87b533576c1bd22d725bfafe61ad18e7b1e67466a9a9d08946adb96  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.1_s2.json
7376e5d406183a308d66f7e992c70073be2ffdcdce0a226c58269406c82b5bd5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.1_s3.json
9c19a6041d4eeafe10277c335b8fe7026955a1df8650a80e080ad64beec76a72  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.2_s7.json
974f1a8a0b40bae6b85ef10ff7a50b8d32a60bd703cbd97e58a13de0690754f5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.5_eff1.0_log0.2_s8.json
ce6f9f4d5d4fd5682322d4ceccf10d350b466af74f7b07992158f71a0e6e13ff  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2null_rho0.8_eff1.0_log0.1_s4.json
ac5600a0180e37d5f223727afa6d105d2ecc0777819f71021e56c4d8fa02e7aa  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2power_rho0.5_eff1.5_log0.1_s10.json
3fbc7d0eaae3fa7139c42cce85e44bad43baf074a60e3b3f37c0e7f5602a15d5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2power_rho0.5_eff1.5_log0.1_s9.json
97d2f632a301ae710726b4627915cda88315de581c2c4f7bf499054f9a11762b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2power_rho0.5_eff2.0_log0.1_s11.json
32da5b8e4ab21be6a4be1b39d4b5808008f5ae2c8b9a7db4260cd7e8a304e490  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\oc_v03\T3_e2power_rho0.5_eff2.0_log0.1_s12.json
c421cc0604d7465a8b8bbfc3d8474fc9d5f1c151c1d7ea4f032fe632471cbe71  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\m_scratch\eps_v01.json
d07a33242384cf69c02cdac513a34f7842812f8f14ff8c78e96777a4cc620c15  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\70_TESTS\M_SYNTHETIC_TESTS_v05.md
FROZEN_HASHES_END
