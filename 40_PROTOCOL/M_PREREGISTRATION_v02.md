# M pre-registration v02: the method stage (31 Oct 2026)

**Status.** Draft v02, for the independent pre-freeze review (R07). It becomes binding when its hash block is filled and its `.sha256` sidecar is written. v01 (hash `173bca05…`, recorded in `40_PROTOCOL/M_PLAN_HASH_LOG.txt` before any pre-freeze computation) is kept unchanged.

**Changes from v01.** All of them came from simulated-data tests. No real outcome was computed before any of them.
1. **E1 is repeated 20 times** with different log-fold seeds (SEED + r, r = 0..19; r = 0 is v01's split). Each item's exceedance and margin are averaged over the repetitions before the log-cluster bootstrap. Why: one split conditions every conclusion on one calibration draw. The conformal guarantee holds on average over calibration draws, which is what repeated splitting estimates.
2. **E2 inference uses a two-sample refit bootstrap** (B = 1000): each replicate resamples train logs and val logs, refits every rule on the resampled train and evaluates it on the resampled val. The point estimate is the rule fitted on all train scenes (the deployable rule). Why: in the simulated end-to-end test, a valid method fitted on a train set whose tail was 2.5 SE light was flagged on exchangeable val data when the fitted rule was held fixed. The fixed-rule test ignores calibration randomness, and averaging over train subsamples cannot remove a train-level deviation; refitting on resampled train logs does.
3. **M\*-log always uses the CRC minimum of 19 calibration logs.** The n ≥ 39 sensitivity concerns scene units only. With n ≥ 39 the log arm could have no threshold at any level.
4. **The rule for recommending M-LS is made precise** (§7).
5. **Integrity of T2 exports.** The export harness's track-to-detection sanity ratio K2 is informational and not one of its gates, as it already was for T1. T2 keeps more tracks alive: 1.53 tracks per detection on the 2-scene check against the soft limit of 1.5. Unpaired tracks never become items.
6. **Notes** on the deployable covariance when a threshold is ≤ 0 (P02, PM2 remark), and on fallback strata (P02, PM1).
7. **A ninth baseline, B8** (stratified variance matching), with hypothesis HM2c. It answers the question "is it the stratification or the conformal quantile that matters?". It was added before review and before any real outcome.

**Scope.** The method stage turns claim K5 (secondary in X2) into the paper's method claim. It evaluates a decision-projected, stratified conformal recalibration (named **DP-SCRC** below) against nine baselines on held-out logs, on a log-disjoint transfer split, and on a second tracker setting whose data have never been analysed.

## 1. Claims this stage can support

| Claim | Statement | Decided by |
|---|---|---|
| K5 (method validity) | DP-SCRC keeps the toward-ego exceedance at or below δ = 0.05 in every evaluated stratum on held-out logs | HM1 |
| K5a (baselines fail) | Uncalibrated, NEES-guided, pooled conformal, per-axis conformal and stratified variance-matching corrections each leave at least one evaluated stratum significantly under-covered | HM2, HM2b, HM2c |
| K5b (motion state matters) | A stratification without motion state leaves at least one motion stratum significantly under-covered | HM3 |
| K5c (adaptive marginal method is not enough) | A learned-scale conformal method with a marginal guarantee leaves at least one evaluated stratum significantly under-covered | HM3b |
| K5d (transfer) | DP-SCRC fitted on train stays valid on the log-disjoint val split | HM6 |
| K5e (efficiency) | DP-SCRC needs less margin than the certified single multiplier, and the price of ignoring motion state is measured | descriptive with CIs |
| K5f (second tracker setting) | All of the above replicate on CANMOT's sample-covariance setting | E3 |

No safety claim is made here (K6).

## 2. Data

**Tracker settings.**
- **T1 (main):** CANMOT `paper/local/canmot/sc` (Q tuned by Bayesian optimisation for AMOTA on val; R = trainval sample covariance). Exports: train `60_RESULTS/x2_export_train700_fast_v02` (12 workers), val `60_RESULTS/x1_export_val150_v02` (3 workers). Horizon files: `60_RESULTS/x2/x2_horizon_v01.jsonl.gz`, `60_RESULTS/x1/x1_horizon_v01.jsonl.gz`.
- **T2 (fresh):** CANMOT `paper/local/sample/trainval` (Q = trainval sample covariance of the CV model's residuals; same R, same detections, same code commit). Exports: `60_RESULTS/m_export_sampletv_v01/{train,val}` (export v05, fast mode, 2-scene native equivalence check). Horizon files: `60_RESULTS/m_export_sampletv_v01/horizon_{train,val}_v02.jsonl.gz` (propagation identical to T1's, with T2's Q).
- Detections: CenterPoint (flip), val sha `4186f748…`, train sha `547fdb7d…`. Ground truth: `30_DATA/x2_gt/x2_train_gt_v03.json`, `30_DATA/x1_gt/x1_val_gt_v02.json`.

**Splits.** Train 700 scenes in 50 logs; val 150 scenes in 18 logs; no log is in both.

**Data reuse, stated plainly.**
- T1 train and val outcomes were analysed at coarse-cell level (class group × range × axis) in X1, X2 and K5. Review R06 looked at the share of exceedances from turning cars on T1 train using ground-truth future heading.
- The motion-state strata below were therefore motivated by outcomes on T1 train. E1 on T1 is a held-out evaluation, but it is not a fresh test of whether motion strata help.
- **T2 outcomes have never been computed at any level.** E3 on T2 is the fresh replication. Every rule below is fixed before any T2 outcome is computed.

## 3. Items (unchanged from X2)

At horizon h (primary 2 s; secondary 1 s and 4 s), an item is a (record, axis) pair:
- record at keyframe k ≥ 1, in the ego's 4 s CTRV corridor at k, not a bicycle or motorcycle in a bike rack;
- persistently paired with a ground-truth instance (2 m gate) and uncensored at k + h (annotation present, ≥ 1 lidar point, not in a rack);
- axis a ∈ {object long, object lat} from the estimated yaw, kept only if it separates the estimated object from the CTRV-predicted ego footprint (|sep| > h_obj + h_ego);
- toward-ego orientation from the estimate.

For each item: D = signed toward-ego projection of (truth − predicted mean) on a; V = a′Σ̂a with Σ̂ the predicted xy covariance at k + h; sd = √(V + σ_a²) with σ_a = 0.10 m; U = D / sd. A margin m is **exceeded** when D > m.

## 4. Features and strata (all I_k-measurable; no ground truth)

- **group**: car, pedestrian, two-wheeler, large (as X2).
- **range**: distance from the predicted ego centre to the predicted object centre at k + h: < 20, 20–40, ≥ 40 m.
- **axis**: long, lat.
- **motion state** from the track's own exported estimates:
  - speed ŝ = ‖(v̂x, v̂y)‖ at k;
  - heading rate ω̂ = wrap½(ψ̂_k − ψ̂_{k−j}) / (t_k − t_{k−j}), using j = 2 if the same track has a record at k − 2, else j = 1 if it has one at k − 1; wrap½ maps to (−π/2, π/2] so a 180° heading flip does not read as a turn;
  - **static** if ŝ < 1.0 m/s; otherwise **new** if neither k − 1 nor k − 2 has a record of the track; otherwise **turning** if |ω̂| ≥ 0.10 rad/s; otherwise **straight**.
- **Level-0 stratum** = group × range × axis × motion (96 strata). Coarser levels: L1 = group × range × axis; L2 = group × axis; L3 = axis.

The thresholds 1.0 m/s and 0.10 rad/s are fixed here. They are not tuned. Sensitivities are in §8.

## 5. Methods

All thresholds are fitted on calibration scenes only. z = Φ⁻¹(0.95) = 1.645.

**CRC threshold.** For a cell with calibration scenes i = 1..n that have items in it, L_i(c) = share of scene i's items with U > c. The threshold ĉ is the smallest observed U with n/(n+1)·mean_i L_i(c) + 1/(n+1) ≤ δ (Angelopoulos et al., ICLR 2024; loss bound 1). It exists when n ≥ 19 (since 1/(n+1) ≤ δ). This is `crc_threshold` in `x1_lib_v03.py`.

**M\* (DP-SCRC, the method).**
- For each level-0 stratum with n ≥ 19 calibration scenes: its own CRC threshold ĉ_g.
- Otherwise the threshold of the finest coarser level (L1, then L2, then L3) whose cell has n ≥ 19, fitted on all calibration items of that cell. Every use of a fallback is recorded.
- Margin m = ĉ_g · sd.
- **Deployable output.** For an object with estimated yaw ψ, axes a_l = (cos ψ, sin ψ), a_t = (−sin ψ, cos ψ), and α_l = ĉ_(…,long,m)/z, α_t = ĉ_(…,lat,m)/z: A = α_l a_l a_l′ + α_t a_t a_t′ and Σ̃ = A (Σ̂ + σ_a² I) A. Then a′Σ̃a = α²(a′Σ̂a + σ_a²) on both object axes, so a planner using z·√(a′Σ̃a) applies exactly the stratum margin (proposition PM2, §10). Σ̃ is positive semi-definite. Directions other than the object axes carry no guarantee (condition M of addendum v04).

**Variant M-LS (secondary method arm): stratified CRC on learned-scale scores.**
- The calibration scenes are split 50/50 by a seeded permutation (seed 20261031) into a fit half and a conformal half.
- On the fit half: ordinary least squares of y = log(max(|U|, 0.05)) on φ(x) = [1, lat, static, turning, new, lat·static, lat·turning, lat·new, pedestrian, two-wheeler, large, range 20–40, range ≥ 40, log sd, min(ŝ, 20), min(|ω̂|, 0.5)·(1 − lat), min(|ω̂|, 0.5)·lat] (ω̂ := 0 when undefined or static). Scale s(x) = exp(φ′β̂).
- On the conformal half: M\*'s stratification and fallback applied to U′ = U / s(x). Margin m = ĉ′_g · s(x) · sd.

**Baselines.**
- **B0 uncalibrated:** m = z · sd.
- **B1 NEES-guided:** k = ANEES/2 per group × range (2-D NEES of the xy residual with Σ̂ + σ_a² I on calibration in-path paired records at the horizon); a global k if the group × range has fewer than 19 calibration scenes. m = z · √k · sd. (As X2 H3.)
- **B2 global variance inflation (uncertified):** s\* = the largest, over L1 cells with ≥ 19 calibration scenes, of the smallest s that brings that cell's calibration record exceedance of z√(sV + σ_a²) to ≤ δ. m = z · √(s\*V + σ_a²). (As X2.)
- **B3 certified global multiplier:** c = max over level-0 strata of M\*'s thresholds (including fallbacks). Valid in every stratum. m = c · sd.
- **B4 pooled conformal (one threshold, CGKF-style):** one CRC threshold over all calibration items. m = ĉ · sd.
- **B5 per-axis conformal:** one CRC threshold per axis (L3).
- **B6 coarse stratified (X2's K5 method):** CRC per L1 cell with fallback to L2, L3. No motion state.
- **B6c certified coarse:** per L1 cell, the maximum of M\*'s thresholds over its motion strata. It is valid wherever M\* is, and is used only to price the omission of motion state (K5e). It is not a competitor.
- **B7 learned-scale conformal (marginal):** M-LS's scale model, with one pooled CRC threshold on U′ over the conformal half. m = ĉ′ · s(x) · sd.
- **B8 stratified variance matching (added in v02):** M\*'s strata and fallback, but each cell's multiplier is z·√(mean U²) over its calibration items (a projected 1-D NEES rescaling per stratum, Gaussian assumption, no certificate). m = that multiplier · sd. It isolates the role of the conformal quantile from that of the stratification.

**Sensitivity arm M\*-log:** as M\*, with the log as the exchangeable unit (L_i over logs, n = number of calibration logs with items, n ≥ 19 for a stratum's own threshold in every configuration). It is the pre-registered remedy if HM1 fails because logs differ.

## 6. Evaluations

- **E1 (T1, train, held-out logs):**
  - The 50 train logs are permuted with seed 20261031 + r and assigned greedily, in that order, to the fold with the fewest scenes so far (5 folds).
  - For each fold, every method is fitted on the other four folds and evaluated on it, so each item is held out once per repetition.
  - This is repeated for r = 0..19. Each item's exceedance indicator and margin are averaged over the 20 repetitions.
  - Inference: log-cluster bootstrap (B = 2000) over the averaged per-item values, rules held fixed.
- **E2 (T1, transfer):**
  - **Point estimate:** every method fitted on all 700 train scenes (the deployable rule) and evaluated on the 150 val scenes.
  - **Inference:** a two-sample log bootstrap (B = 1000). Each replicate draws the 50 train logs and the 18 val logs with replacement, refits every method on the resampled train (each copy of a scene or log is its own calibration unit), and evaluates it on the resampled val.
- **E3 (T2):** E1 and E2 repeated on T2 with identical code and settings.
- **E4 (secondary horizons):** E1 and E2 at 1 s and 4 s on T1 and T2. Descriptive only.
- **E5 (sensitivities, T1 and T2, E1 design):** §8.

## 7. Endpoints, statistics and hypotheses

**Evaluated strata.** Level-0 strata with ≥ 39 distinct scenes in the evaluation pool (E1: the 700 train scenes; E2: the 150 val scenes). They are fixed from counts before any outcome is computed (§9).

**Exceedance.** For method m and stratum g, Ê_g = mean over scenes with items in g of the scene's share of exceeded items (the CRC target; primary). The pooled record share is secondary.

**Uncertainty.**
- **E1:** log-cluster bootstrap over the 50 train logs (all scenes of a drawn log enter with its multiplicity), B = 2000, with the repetition-averaged values held fixed.
- **E2:** the two-sample refit bootstrap of §6, B = 1000.
- **Seeds:** each evaluation has its own generator, seeded by (20261031, crc32 of the evaluation label), so results do not depend on the order of evaluations.
- **Sensitivity:** a scene bootstrap is reported for E1.

**Significant under-coverage.** For each method separately:
- se_g = bootstrap SD of Ê_g;
- T = max over its evaluated strata with se_g > 0 of (Ê\*_g − Ê_g)/se_g, and q = the 95 % quantile of T;
- LB_g = Ê_g − q·se_g.

Stratum g is **significantly under-covered** if LB_g > δ. Strata with se_g = 0 cannot be declared under-covered.

**Hypotheses (each tested at α = 0.05 within each evaluation).**
- **HM1 (validity of M\*):** (a) no evaluated stratum is significantly under-covered by M\*; and (b) Ē, the mean of Ê_g over evaluated strata, has a one-sided 95 % bootstrap upper bound ≤ δ + 0.02.
- **HM2:** each of B0, B1 and B4 significantly under-covers at least one evaluated stratum. Each baseline is reported separately; K5a is claimed only for those that do.
- **HM2b:** B5 significantly under-covers at least one evaluated stratum.
- **HM2c (added in v02):** B8 significantly under-covers at least one evaluated stratum. Claim K5a_B8: stratification with a Gaussian variance match is not enough; the conformal quantile is needed.
- **HM3:** B6 significantly under-covers at least one evaluated stratum whose motion state is static, straight, turning or new.
- **HM3b:** B7 significantly under-covers at least one evaluated stratum.
- **HM6 (transfer, E2):** M\* fitted on train leaves no evaluated val stratum significantly under-covered, and Ē on val has a one-sided 95 % upper bound ≤ δ + 0.03.

**Efficiency (K5e; descriptive, 95 % log-bootstrap CIs).** Mean margin per item, over all items of the evaluated strata, by axis and in total, for every method; the ratios M\*/B3, M\*/B6c, M-LS/M\* and M\*/B7; and per-stratum mean margins. Efficiency is only compared between methods that pass HM1(a) in that evaluation, and B3 and B6c.

**Decision on the method stage (written into D07).**
- **Method GO** if HM1 holds in E1 on T1 and on T2, HM6 holds on T1 and on T2, HM2 holds for at least two of B0, B1, B4 on both trackers, and M\*'s mean margin is below B3's with the 95 % CI of the ratio below 1 on both trackers.
- Each of K5a–K5c is claimed only if it holds on **both** trackers (intersection over the two settings).
- No family-wise error control across different claims is claimed; each claim needs its own test to hold on both trackers.
- The paper recommends M-LS, and reports M\* as the simpler arm, only if all of these hold on both trackers:
  - M-LS passes the HM1 rule in E1 and the HM6 rule in E2;
  - the 95 % CI of the mean-margin ratio M-LS/M\* in E1 lies below 1.

  The choice is made by this rule alone.

**If HM1 fails.** Report it. Check M\*-log (§5). If M\*-log passes HM1 on both trackers, a v03 amendment adopts it, and its claims are labelled post hoc until a fresh check.

## 8. Sensitivities (E5; reported, not decisions)

1. Static threshold 0.5 and 2.0 m/s; turning threshold 0.05 and 0.20 rad/s.
2. ω̂ from the change in velocity direction instead of yaw.
3. σ_a = 0 and 0.20 m.
4. Own-threshold minimum n ≥ 39 instead of 19.
5. Contested pairs excluded.
6. Scene bootstrap instead of log bootstrap.
7. M\*-log.

## 9. Before the freeze: what may be computed

- Synthetic tests on **simulated** data only: simulated scenes, logs, motion and errors. No real annotation enters a synthetic test.
- Counts per level-0 stratum (items and scenes) for T1 and T2, train and val, at 1, 2 and 4 s. The builder runs with outcomes switched off: D and U are not computed. The counts fix the evaluated strata.
- T2's integrity criteria (Q0) and the native-versus-fast equivalence check (tracker outputs only).
- Nothing else touches D, U or any residual on real data.

## 10. Proof obligations (method)

- **PM1 (per-stratum validity).** If scenes are i.i.d., the calibration scenes that have items in stratum g and a test scene that has items in g are i.i.d. from the conditional law; applying CRC to them gives E[L_test,g(ĉ_g)] ≤ δ. Fallback thresholds give the same bound marginally over their coarser cell only. Under log-level dependence the guarantee holds with the log as the unit (M\*-log).
- **PM2 (deployable covariance).** Σ̃ = A(Σ̂ + σ_a²I)A is positive semi-definite and a′Σ̃a = α²(a′Σ̂a + σ_a²) for a ∈ {a_l, a_t}, because A a_l = α_l a_l and A a_t = α_t a_t.
- **PM3 (certified single multiplier).** max_g ĉ_g is valid in every stratum, because each L_i,g(c) is non-increasing in c. Its excess margin over M\* is Σ_items (max ĉ − ĉ_g)·sd (Thm 4 form).
These are written out in `10_PROOFS/P02_METHOD_PROPOSITIONS_v01.md` before the freeze.

## 11. Code, inputs and outputs

- **Code** (frozen by hash):
  - `50_CODE/m/`: `m_lib_v01.py` (items, features, methods, statistics), `m_data_v01.py` (loading and integrity), `m_sizes_v01.py` (counts, outcomes off), `m_run_v01.py` (E1, E2, E4, E5; freeze and input binding), `m_decide_v01.py` (§7 decision), `m_freeze_v01.py`;
  - `50_CODE/m/tests/` (simulated-data tests and their runner, and the pre-freeze patch record);
  - the X1/X2 library it imports (`50_CODE/x1/x1_lib_v03.py`);
  - T2's export and propagation code (`x1_export_v05.py`, `x1_horizon_prep_v02.py`, `run_m_sampletv_export_v01.sh`).
- **Run order:** T1 then T2 (they may run in parallel), then `m_decide_v01.py`.
- **Outputs:** `60_RESULTS/m/m_result_canmot_sc_v01.json`, `60_RESULTS/m/m_result_sampletv_v01.json`, `60_RESULTS/m/m_decision_v01.json`, plus logs.
- Deviations are logged in `90_DECISIONS/D08_M_DEVIATION_LOG_v01.md`.

FROZEN_HASHES_BEGIN
(filled at the freeze, in v02)
FROZEN_HASHES_END
