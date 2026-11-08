# Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Open-Loop Log-Replay Test on Argoverse 2

**Supplementary material** (assembled 7 Nov 2026). It holds the full method-stage, development and registered-test results, the protocol of the registered test, the post-registration exploratory analyses (X3), the proofs, the planner and perception stack, and the record of what was computed before the freeze. Section, table, figure, appendix, proposition and remark numbers without an "S" prefix refer to the main text. S8 keeps its own labels; cited from outside S8, they carry the prefix "S8-" (for example, S8-Proposition 9). The supplement's bracketed source tags point to released files, by path or by a short key; most keys are expanded in the opening tag of their section or in the glossary below, and "the authors' decision record" is one released file that records the authors' design and reporting decisions. Paths are relative to the root of the released project files; inside S6, a path without a top-level folder is relative to `60_RESULTS/x3_explore_v01/`.

**Sources.** Source tags name the records behind the statements they follow. The X3 result files are in `60_RESULTS/x3_explore_v01/` and the X3 integrity reports in `70_TESTS/X3_INTEGRITY_v01/`.

## Codes used in this supplement

Terms of the main text keep their main-text meaning (Section IV and Appendix C of the main text). The codes below name studies, analyses and records; they are labels, not results.

| Code | Meaning | Where |
|---|---|---|
| T1, T2, T3 | The nuScenes tracker settings: CANMOT with process noise tuned on val (T1) or set to a sample covariance (T2), and Poly-MOT (T3). T1 and T3 are the trackers of the registered test; AB3DMOT is its descriptive third tracker. | S1.2; S9.15.2 |
| X1, X2 | The two pre-specified nuScenes diagnosis studies behind main-text Section V-B (X1 on val, X2 on train). | S1.8 |
| Method stage; HM1–HM6; E1, E2 | The pre-specified nuScenes study of DP-SCRC, M\*'s parent, on the audit population; its hypotheses; its cross-validated evaluation on train (E1) and its train-to-val transfer (E2). | S1 |
| K6 | The first planner study on nuScenes (pre-specified; NO-GO). | S2.1 |
| K8 | The exploratory planner study on nuScenes on which M\* and the registered rules were developed (main-text Section V-C). | S2.2 |
| D17 | The pre-specified Trajectron++ study on nuScenes, named after its plan file. | S3 |
| C1; H1–H10, Q1 | The registered test on Argoverse 2 (main-text Section V-D) and its claims; Q1, the QCNet claim, was dropped before the freeze and not tested. "The C1 plan" is its frozen plan (v07m). | S4, S5, S7 |
| X3; A1–A5 | The post-registration exploratory analyses of main-text Section V-E, and the five amendments to their plan (A5 is S6.22). | S6 |
| P0–P7 (in S6) | The partitions of X3's analysis (b). | S6.3 |
| P1–P18 (in S5 and S10) | The computations made before the freeze, in time order. | S10.3 |
| V0–V2 (in S6.1) | X3's validation gates. Elsewhere V2 is the main text's share of decisions with an exceeded relied constraint. | S6.1 |
| G0–G3, W (in S10) | What a computation before the freeze read of the annotations. | S10.1 |
| R06–R21 | The project's internal reviews, checks and re-derivations, filed in `70_TESTS/` under these codes, for example R08 (method-stage results), R16 (K8 results), R17–R17g and R20 (code and plan of the registered test), R19 (Trajectron++ results) and R21 (the separate re-derivation of the registered results). | source tags; S4(g); S10.6 |
| D06–D10, D14, D17, D18; E01 | Design, decision and report files in `90_DECISIONS/`, for example D07 (the method-stage report) and D14 (the K8 design); E01 is the evidence dossier of the nuScenes stages, `20_DESIGN/E01_EVIDENCE_DOSSIER_v02.md`. | source tags |
| The authors' decision record (DR in S10) | One released file that records the authors' design and reporting decisions. | source tags |
| AV2 | Argoverse 2. | — |

## Contents

- S1. DP-SCRC on the audit population (the nuScenes method stage)
- S2. The planner studies on nuScenes: K6, and K8 in full
- S3. A learned predictor: Trajectron++ on nuScenes
- S4. Full results of the registered test on Argoverse 2 (S4.1: the secondary claims in full)
- S5. The Argoverse 2 protocol: registration, blinding, events and mechanics
- S6. Post-registration exploratory analyses (X3): full results (S6.12–S6.22: amendments A3, A4 and A5, added after review)
- S7. The registered plan
- S8. Proofs and supporting results in full
- S9. The planner and the perception stack in full
- S10. What was computed on the 375 test logs before the freeze, in full

---

## S1. DP-SCRC on the audit population (the nuScenes method stage)

`[M-PLAN = the method-stage plan 6366020a…, 353 files; E01; MDEC; MR-T1…MR-T3; D07; R08]`

**Status.** Pre-specified development evidence on nuScenes. The plan was hashed with its code, inputs and environment listings before the outcomes were computed, and there was no deviation after the freeze. DP-SCRC is M\*'s parent (Section IV): the same per-stratum conformal risk control, fitted on a fixed in-path *audit* population instead of the constraints the planner relies on. The planner study K6 (S2.1) found that the two populations differ, which is why the main text uses M\*.

**HM1 and HM6 are consistency checks.** E1 is pinned by construction for conformal methods, and the refit-CV test that judges it is conservative (S1.4), so "DP-SCRC not flagged" was close to guaranteed. HM1 (E1) and HM6 (the same no-flag statement on val, E2) are therefore reported as consistency checks, not as evidence of validity under shift `[V05_REFEREE_REVIEW_v01 M4(e)]`. E2 is a transfer under the confounded shifts listed in S1.4, judged with per-cell bounds that are not bias-corrected (S1.5). The informative results of the method stage are the failures of the pooled correction B4 and the shape of the deployable recalibration (S1.5).

### S1.1 The audit population and what its certificate covers

**Items in constraint coordinates** `[E01 §3.1]`. Every quantity is computed from the tracker's estimate and the ego's own predicted state; nothing about the true future enters the selection or the direction.
- *Horizon prediction.* For a record at keyframe k the class's own filter prediction is repeated h = 4 times at the 0.5 s keyframe interval (2 s) with no measurement update; m̂ and Σ̂ are the predicted position and its 2 × 2 covariance `[HPREP; E01 §2.6]`.
- *Ego at the horizon.* The constant-turn-rate-and-velocity (CTRV) prediction from keyframes k − 1 and k, not the logged future pose. Its center c_e is the rear-axle pose moved 1.39 m forward; its footprint, 4.1 m × 1.8 m inflated by 0.5 m on every side, has axes u_e, v_e from the predicted ego yaw `[E01 §2.6, §3.1]`.
- *Object axes* from the tracked box's yaw ψ: a_L = (cos ψ, sin ψ), half-extent l/2; a_T = (−sin ψ, cos ψ), half-extent w/2.
- *Separating-axis filter.* Axis a is kept only if |aᵀ(c_e − m̂)| > h_obj(a) + h_ego(a), with h_obj and h_ego the support functions of the estimated box and the inflated ego rectangle along a `[XLIB axis_candidates]`.
- *Toward-ego orientation.* a* = a·sign(aᵀ(c_e − m̂)): a positive error means the object is closer to the ego than predicted.
- *Score.* U = a*ᵀ(X − m̂)/√(a*ᵀΣ̂a* + σ_a²), with X the annotated center at k + h and σ_a = 0.10 m an assumed annotation noise (0 and 0.20 m as sensitivities). D = a*ᵀ(X − m̂) is the projected error in meters, and a margin m is *exceeded* when D > m. Under a calibrated Gaussian, U > 1.645 in 5 % of items.
- *Item.* One (record, axis) pair passing the filter; a record gives 0, 1 or 2 items. The audit population is the in-path, paired, uncensored items (S1.8).

Strata, the per-stratum CRC rule, the floor of 19 calibration units and the count-based fallback are those of Sections IV-B to IV-D, without M\*'s in-path split and with the 20 s **scene** as the exchangeable unit instead of the log. Every evaluated car level-0 cell used its own threshold in all fits on all three settings `[MR-T1…MR-T3: E1_h2s.Mstar_own_threshold_share]`.

**What the certificate covers** `[P02 Estimand; P01-A4 Props. A, B]`.
- *Scene-level and stratum-marginal.* The loss is a scene's share of stratum items, and the bound is per own-threshold stratum, marginal over the draw of calibration and test scenes. It is not item-level, not the per-constraint premise, and not a bound for one deployed rule given its calibration set. A scene-weighted rate can exceed δ even under exact conditional calibration: an exact example gives 1.25δ = 0.0625 (S8.2).
- *Transductive.* Given the data and a uniformly random split of a set of scenes, the bound holds for a test unit drawn uniformly from the held-out part, and so for the held-out part's average. It does not hold for a fixed test scene (S8-Remark 4). A new-scene reading needs every ingredient of the score, the tracker's Q and R included, fitted outside the evaluation scenes. It therefore fails for T1 and T2, whose noise was fitted on val or trainval, and all settings' association was selected on val.
- *The scene as the unit.* Scenes cut from one drive are dependent, so Proposition 3 holds for nuScenes scenes only to the extent that they are exchangeable (S8-Remark A.5).
- *The audit's axes.* S8-Proposition 3 transfers the premise to the audit's estimate-chosen, toward-ego separating axes under condition (M). The record-weighted pooled exceedance over any selection satisfying (M) is then at most δ, and exactly 0.05 under a Gaussian posterior with known annotation noise σ_a. Fixed-truth calibration, outcome-dependent selection, scene weights, a misspecified σ_a and proxy normals are not covered `[P01-A4 Prop. A, N1–N6]`.
- *The population.* The certificate holds on matched true positives still observable at the horizon, along the separating object axes. It is not the planner's population (S2.1).

### S1.2 The three nuScenes tracker settings

`[E01 §2.3; M-PLAN §2; D07 §4; V06_REFERENCES_CHECK_v01 Li2023 (b)]`
- **T1.** CANMOT [Osterburg2026], experiment `paper/local/canmot/sc`: an extended Kalman filter with a CV model for every class and Q rotated into the box frame. Q was tuned by Bayesian optimization for AMOTA on **val**; R is the trainval sample covariance.
- **T2.** The same tracker, experiment `paper/local/sample/trainval`: Q is the trainval sample covariance of the CV model's one-step residuals. Only Q differs from T1.
- **T3.** Poly-MOT [Li2023], as configured in CANMOT's `paper/baseline/poly_mot` experiment (`config/poly_mot/nusc_config_poly_mot.yaml`, lines 41–42): a CTRA extended filter for cars, buses, pedestrians and trucks, and a linear CA filter for bicycles, motorcycles and trailers, with its own hand-set Q and R (CTRA Q the identity). The Poly-MOT paper uses a bicycle model for bicycles and motorcycles [Li2023, §IV-B]. Its exported velocity field held (speed, acceleration); the loader rebuilds (v_x, v_y) from the state (median error for moving cars 7.22 m/s before, 0.74 m/s after; T1's is 0.71 m/s).
- **Shared by all three:** detections, score filter and non-maximum suppression, association metrics and life cycle (Poly-MOT's published values, selected on nuScenes val), scenes, ground truth and pairing code. They are three tracker settings, not three independent trackers.

### S1.3 The arms

All arms are margins along an object axis `[E01 §4; M-PLAN §5; P02 PM3]`.
- **B0**, raw: 1.645·sd.
- **B1**, NEES-scaled: 1.645·√k·sd, k = ANEES/2 per class group × range [BarShalom2001; Osterburg2026].
- **B3**, the certified single multiplier: c̄·sd (S8-Proposition 9), with c̄ the maximum of all 96 deployed thresholds, fallbacks included. It is at least every own threshold and carries no guarantee in fallback strata. **B6c**, the maximum over the course-change strata within an L1 cell. B3 and B6c are pricing references, dominated by DP-SCRC by construction.
- **B4**, pooled conformal: one CRC threshold over all items, the analogue of the per-time-step conformal inflation of [Weisman2026] and of the single global factor tested as a baseline in [Marques2026b].
- **B6**, no course-change strata: CRC per L1 cell with fallback.
- **B9**, norm-ball conformal: one radius on every axis from CRC on the 2-D error norm [Lindemann2023; Dixit2023], certifying the stronger event that the 2-D error is inside the ball.
- **Ablations, reported and not claimed:** B2 (empirical global inflation), B5 (per-axis conformal), B7 (learned heteroscedastic scale, one pooled threshold), B8 (stratified variance matching), B10 (stratified empirical quantile without the finite-sample term) and M-LS (DP-SCRC on regression-scaled scores).

### S1.4 Design, statistics and operating characteristics

**Design.** Decisions at 2 s; 1 s and 4 s descriptive (E4); 12 sensitivities (E5). *E1*: 20 repetitions of a 5-fold split of train by log, thresholds fitted on the other folds, each item's indicator and margin averaged over repetitions; inference by a fixed-rule log-cluster bootstrap (B = 2000) and a refit-CV bootstrap (B = 200) that resamples logs and re-runs the whole cross-validated fit. *E2*: every method fitted on train and evaluated on val, with a two-sample refit log bootstrap (B = 1000). Evaluated cells need ≥ 39 scenes from ≥ 8 logs; a cell is *flagged* if its one-sided simultaneous 95 % lower bound exceeds δ; *a baseline fails* in a cell when, on refit-CV, it is flagged, DP-SCRC is not, and the paired difference is significantly positive. The hypotheses are the rows of S1-Table 1, and the decision rule is given below `[M-PLAN §6–§10; E01 §3.7]`.

**Statistics and decision rule** `[E01 §3.7; M-PLAN §6–§10]`. Ê_c is the mean over scenes with items in c of the scene's exceeded share. Bounds are one-sided simultaneous 95 % by sup-t within each method (a cell is flagged also if SE = 0 and Ê > δ).
- **HM1** (consistency check): DP-SCRC flagged in no E1 cell under either inference.
- **HM6** (consistency checks): (a) flagged in no E2 cell and (b) the pooled val cell not flagged.
- **HM2:** each of B1, B4, B9 fails in ≥ 1 E1 cell; **HM2b:** the same for B5, B7, B8, B10.
- **HM3:** B6 fails in ≥ 1 single-stratum car turning cell, confirmatory on T3 only (foreknown on T1).
- **METHOD GO-A:** HM1 and HM6 on T1, T2 and T3, the same practitioner baseline failing on T1 and on T3, and HM3 on T3. **GO-B:** GO-A without HM3. **NO-GO** otherwise.

**Cells.** E1: each qualifying level-0 stratum, then per group × axis the union of the remaining strata, then per axis the remainder. E2: group × axis × course-change state pooled over range, then each course-change state pooled over the rest, then remainders, and the pooled cell "all val items". The bias-corrected upper bound of the pooled cell against δ + 0.03 is reported, not decided. E2 uses B = 300 at 1 s and 4 s.

**E5 sensitivities** `[M-PLAN §10]`: static threshold 0.5 and 2.0 m/s; turning threshold 0.05 and 0.20 rad/s; turn rate from the velocity direction, from the yaw, and course over ground with a 1 m minimum chord; σ_a = 0 and 0.20 m; own-threshold floor 39 instead of 19; contested pairs excluded; scene instead of log bootstrap.

**Seeds**: E1 folds 20261031 + r; bootstraps 20261030.

**Operating characteristics (OC).** A valid DP-SCRC fails HM1 in 0 % and HM6 in 3 % (T1) and 1 % (T3) of null datasets, a false NO-GO has probability ≤ 0.07, a val turning-cell exceedance of about 0.20 is caught in 80 % (T1) and 85 % (T3) of datasets and one of about 0.12 in 23 %, and the smallest per-cell excess detected with 80 % power is 0.10 to more than 0.30 in E1 (one T1 component is above 0.30) and 0.15–0.30 in E2 `[E01 §5.3, §7 item 3 / M-OC-T1, M-OC-T3; 70_TESTS/m_scratch/oc_v04_T1.json]`.

**Properties of the inference.** E1 is pinned by construction for conformal methods: a consistency check, not evidence of validity under shift. The refit-CV is conservative: in pre-freeze simulations its standard error was 4.6–7.7 times the true sampling SD of DP-SCRC's point estimate and 1.36 times for B6 under the null `[M-PLAN §6; R07B S1, S2]`; its simultaneous critical value for DP-SCRC is 4.5–4.8 against 3.4 under the fixed rule, and its replicates run high (bias up to +0.032 in E1 cells) `[R08 m7, m8]`.

**Pre-specification, reviews and re-derivations** `[E01 §3.8, §6, §8]`. The method-stage plan `6366020a…` (353 files) was hashed with its code, inputs and environment listings before its real outcomes were computed. The hash is self-recorded, with no third-party timestamp, so the stage is *pre-specified*, not registered. Before the freeze the rule was run on simulated outcomes laid out on the real record counts (the OC above). The stage was reviewed adversarially before its freeze and re-derived afterwards with separate code, within the project rather than by an outside group. The re-derivation used code importing no pipeline module, by reviewers who could read the pipeline's code `[E01 §6 / R06, R08]`; it is therefore not *independent* in our sense, which requires code written without access to the first implementation.

**What was foreknown, and what is in-sample** `[E01 §2.8; M-PLAN §2]`. T1's B0, B1, B4 and turning results were largely foreknown from X1 and X2 (S1.8), while T2 and T3 outcomes had never been computed. E2 is a transfer under the three confounded shifts named in the method-stage plan: new logs; the detector in-sample on train and out-of-sample on val; T1/T2 noise parameters fitted partly on val. A fourth confound, association and life cycle selected on val for all settings, is noted in `[E01 §2.3]`.

**Errata in the frozen method-stage text** (no effect on the run): a script version name; a stale val scene count for the turning cell (44 scenes and 16 logs under the course-over-ground rule); per-record turning shares replaced by the run's item-level shares `[D07 §5]`.

### S1.5 Results

**Outcome (pre-specified decision label GO-B).** On all three settings DP-SCRC was flagged in no E1 or E2 cell (HM1 and HM6, consistency checks); the same practitioner correction, B4, failed where DP-SCRC held on both tracker families; and the course-change layer was inconclusive on the confirmatory tracker `[D07 preamble; E01 §5.3 / MDEC: METHOD_DECISION "GO-B"; K5a_practitioner_on_T1_and_T3 ["B4"]]`. A separate results review reproduced the pipeline with its own code (below).

**S1-Table 1. Pre-specified hypotheses per tracker setting at 2 s; HM1 and HM6 are consistency checks.** `[E01 §5.3 / MDEC; MR-T1…MR-T3: E1_h2s.hypotheses, E2_h2s.hypotheses]`

| | T1 (CV, tuned Q) | T2 (CV, data Q) | T3 (CTRA/CA) |
|---|---|---|---|
| HM1 (consistency check): DP-SCRC flagged in no E1 cell (cells evaluated) | true (33) | true (32) | true (34) |
| DP-SCRC mean E1 cell exceedance (scene-level) | 0.042 | 0.042 | 0.042 |
| HM6a (consistency check): flagged in no E2 cell | true, 0 of 10 | true, 0 of 9 | true, 0 of 10 |
| HM6b (consistency check): pooled val exceedance; simultaneous LB; bias-corrected UB | **0.043**; 0.013; 0.063 | **0.044**; 0.019; 0.062 | **0.038**; 0.018; 0.051 |
| HM2 (refit-CV): cells where B4 fails | 4 (car lateral: < 20 and 20–40 m, straight and turning) | 3 | **1: car 20–40 m longitudinal straight** (E 0.104, LB 0.054) |
| HM2: B1 fails | 2 (car lateral turning, both ranges) | 2 | none |
| HM2: B9 fails | none | 1 | none |
| HM2b: B5 / B7 / B8 / B10 fail | 2 / 0 / 0 / 0 | 2 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| HM3: B6 fails in a car-turning cell | true (car < 20 m lateral turning; foreknown) | true (not confirmatory) | **false** |

**E1 (S1-Table 2).** On T1 the diagnosis replicates stratum by stratum: the raw covariance is laterally too narrow for course-changing cars (0.287, 0.409) and longitudinally too wide (0.003); NEES scaling and pooled conformal leave the lateral cells at 0.076–0.391; the norm ball over-covers (0.000–0.024). On T3 the raw covariance is far too wide (mean margin 16.9 m, lateral 32.1 m, on E1 train, against 4.3 m for T1; on E2 val 16.0 m and 30.3 m against 4.4 m), and the pooled correction, which shrinks it by one factor, under-covers the longitudinal straight cell (0.104) `[E01 §5.3 / MR-T1, MR-T3: E1_h2s.fixed.methods.B0, E2_h2s.all.methods.B0]`. DP-SCRC sits at 0.042–0.049 in every row and is flagged in no E1 cell on any setting (33, 32, 34 cells), under either inference, at any horizon, or under any of the 12 sensitivities `[E01 §5.3; D07 §2]`.

**S1-Table 2. E1 held-out-log scene-mean exceedance at 2 s, car cells (target 0.05; fixed-rule point estimates).** `[E01 §5.3 / MR-T1…MR-T3: E1_h2s.fixed.methods.*.cells.*.E_scene]`

| Cell | Setting | B0 raw | B1 NEES | B4 pooled | B6 no course-change | B9 norm ball | **DP-SCRC** |
|---|---|---|---|---|---|---|---|
| car < 20 m lateral turning | T1 | 0.287 | 0.224 | 0.273 | 0.142 | 0.024 | **0.046** |
| car 20–40 m lateral turning | T1 | 0.409 | 0.359 | 0.391 | 0.084 | 0.017 | **0.042** |
| car < 20 m lateral straight | T1 | 0.132 | 0.076 | 0.115 | 0.022 | 0.000 | **0.047** |
| car < 20 m longitudinal straight | T1 | 0.003 | 0.000 | 0.001 | 0.036 | 0.003 | **0.049** |
| car < 20 m lateral turning | T2 | 0.439 | 0.225 | 0.263 | 0.156 | 0.010 | **0.047** |
| car < 20 m lateral turning | T3 | 0.000 | 0.017 | 0.019 | 0.110 | 0.043 | **0.044** |
| car 20–40 m longitudinal straight | T3 | 0.000 | 0.070 | 0.104 | 0.058 | 0.007 | **0.046** |

**The pooled conformal correction fails on both tracker families.** B4 fails on T1 in four car lateral cells (foreknown from X2) and on T3 in car 20–40 m longitudinal straight (E 0.104, refit-CV lower bound 0.054; 0.0547 ± 0.0013 over 8 re-draws of the decisive bootstrap, all flagging; also under 12 sensitivities and 3 horizons) `[E01 §5.3, §6, §7 item 4 / MDEC: per_tracker.*.HM2.B4; R08]`. The directions differ, a lateral tail on T1 and a longitudinal one on T3: one global threshold cannot follow a shape that differs by axis and condition. B1 fails on T1 and T2 only, B9 on T2 only; B7, B8 and B10 did not fail, under low power, and their mean cell exceedances are above DP-SCRC's `[D07 §4]`.

**E2: transfer to val.** Pooled val exceedance 0.043 (T1), 0.044 (T2) and 0.038 (T3), with simultaneous lower bounds 0.013, 0.019 and 0.018 and bias-corrected upper bounds 0.063, 0.062 and 0.051; none of the 10, 9 and 10 val cells is flagged `[E01 §5.3 / MDEC: per_tracker.*.pooled_val]`. Of these 29 cells, 8 have point estimates above δ at three decimals (S1.6) and a ninth is at 0.0503; the largest are T3 car longitudinal turning 0.088 (UB 0.151), T1 car lateral turning 0.087 (UB 0.155; 44 scenes, 16 logs) and T3 car longitudinal static 0.079 (UB 0.171) `[MR-T1…MR-T3: E2_h2s.cells.methods.Mstar.cells]`. These per-cell bounds are not bias-corrected, and refit replicates run high by up to +0.013 in E2 cells, so they are anti-conservative by up to that amount `[R08 m8]`.

**The deployable recalibration is a shape correction.** On T1, car < 20 m, the multipliers on the projected SD (nominal 1.645) are 6.97 lateral turning, 3.06 lateral straight, 0.69 lateral static and 0.38 longitudinal static `[E01 §5.3 / MR-T1: E2_h2s.fit_on_all_train.Mstar]`. On T3, 91 of the 96 multipliers are below 1, including all 16 car strata under 40 m (largest 0.87; car < 20 m lateral turning 0.31, longitudinal static 0.42); the five exceptions are car ≥ 40 m longitudinal straight at 1.118 (own level-0 fit), the static, turning and new strata of that L1 cell at 1.118 (inherited by fallback), and two-wheeler < 20 m longitudinal straight at 1.108 (own fit) `[E01 §5.3, App. A row 8 / MR-T3: E2_h2s.fit_on_all_train.Mstar]`. The diagnosis generalizes in form, not in direction: one factor fixes neither shape `[D07 §3 item 5]`.

*Properties of the inference* (S1.4): E1 is pinned by construction for conformal methods, and the refit-CV is conservative. This makes "DP-SCRC not flagged", one leg of each baseline-failure test, easy to meet. *What the comparisons can show.* B3 and B6c are maxima of DP-SCRC's own thresholds, dominated by construction; B9 certifies a stronger event; their ratios price certification with less structure. The non-dominated comparisons, B6 and B7, go against DP-SCRC on T3 (S1-Table 3) `[D07 §4]`.

**S1-Table 3. Ratio of mean margins at 2 s on val (E2; intervals include calibration randomness), DP-SCRC against references (descriptive).** `[E01 §5.3 / MR-T1…MR-T3: E2_h2s.all.ratios; the T3 entry "(E1: 1.110)" from MR-T3: E1_h2s.fixed.ratios]`

| Ratio | T1 | T2 | T3 | Reading |
|---|---|---|---|---|
| DP-SCRC / B3 (certified single multiplier) | 0.161 [0.121, 0.177] | 0.317 [0.197, 0.358] | 0.361 [0.127, 0.388] | Dominated by construction |
| DP-SCRC / B6c (certified coarse rule) | 0.530 [0.475, 0.635] | 0.656 [0.576, 0.715] | 0.684 [0.518, 0.751] | Dominated by construction |
| DP-SCRC / B9 (norm-ball conformal) | 0.584 [0.513, 0.666] | 0.554 [0.495, 0.618] | 0.701 [0.595, 0.837] | B9 certifies the stronger 2-D norm event |
| DP-SCRC / B6 (coarse CRC) | 0.889 | 0.907 | 1.056 (E1: 1.110) | Course-change strata save 9–11 % on T1/T2 and cost 6–11 % on T3 |
| DP-SCRC / B7 (learned scale) | 0.975 | 0.979 | 1.244 | DP-SCRC is not the tightest method on T3 |
| M-LS / DP-SCRC | 1.032 | 1.072 | 1.003 | M-LS is not recommended |

**The course-change layer (HM3, confirmatory on T3).** B6 is at 0.110 and 0.133 in the two lateral-turning car cells against DP-SCRC's 0.044 and 0.036; the paired difference is significantly positive (lower bounds 0.022, 0.023), but B6's own simultaneous bound (0.026, −0.004) does not exceed δ, so HM3 is not met; the pre-freeze power at this effect was 0.15–0.60, and 4 of 12 sensitivities show the failure under the fixed rule. The result is inconclusive, not negative: the strata are an option with a trade-off, not a confirmed component `[E01 §5.3 / MR-T3; D07 §2]`.

A separate results review rebuilt the pipeline from the raw exports with its own code and reproduced every deployable threshold and E2 point estimate on T1 and T3 to 10⁻¹⁷ `[E01 §6 / R08]`.

**E4, E5 and deviations.** The pooled val exceedance at 1 / 2 / 4 s is 0.051 / 0.043 / 0.033 on T1, 0.043 / 0.044 / 0.052 on T2 and 0.038 / 0.038 / 0.053 on T3, with no val cell and no pooled cell flagged at any horizon `[MR-T1…MR-T3: E2_h1s, E2_h2s, E2_h4s.hypotheses]`; the mean DP-SCRC margin on T1 val is 1.40, 3.13 and 9.95 m, against 1.97, 4.43 and 11.57 m for the raw covariance `[MR-T1: E2_h1s/E2_h2s/E2_h4s.all.methods.Mstar, B0.mean_margin_m]`. The 12 sensitivities are listed in S1.4. There was no deviation after the freeze; three errata in the frozen text had no effect on the run `[E01 §5.3 / D07 §5; D08]`.

### S1.6 Per-stratum notes

The full E1 and E2 per-stratum tables (every method and setting, with own-threshold and censoring shares, and record-weighted rates where the files hold them) are not typeset here; they are in the method-stage result files `[MR-T1…MR-T3]`. The E2 DP-SCRC val cells with point estimates above δ (scene-level E; simultaneous one-sided bounds, not bias-corrected `[R08 m8]`): T1 car lateral turning 0.087 (UB 0.155; 44 scenes, 16 logs); T1 all groups turning 0.066 (UB 0.134); T2 car longitudinal static 0.077 (UB 0.184); T2 car longitudinal straight 0.052 (LB 0.004, UB 0.083); T2 all groups turning 0.076 (UB 0.152); T2 all groups new 0.056 (UB 0.113); T3 car longitudinal static 0.079 (UB 0.171); T3 car longitudinal turning 0.088 (UB 0.151); and, at 0.0503, T1 car longitudinal turning (UB 0.113) `[MR-T1…MR-T3: E2_h2s.cells.methods.Mstar.cells.*.E_scene, lb_sim, ub_sim]`.

### S1.7 The course-change state

**The turn rate.** ω̂ is the change in direction of the track's displacement between two consecutive intervals divided by the time between their midpoints, from the records at (k − 4, k − 2, k) when the k − 4 record exists (midpoints 1 s apart) and otherwise (k − 2, k − 1, k) (0.5 s apart); it uses positions, not the tracker's yaw `[E01 §2.7; MLIB motion_features]`.

**Course-change shares.** Position noise reads as a course change at low speed: 18–20 % of car items at 1–3 m/s and 3–7 % at ≥ 8 m/s are "turning" on train, and 45–57 % of pedestrians `[E01 §2.7 / MR-T1…MR-T3: turning_share_by_speed_band]`; "turning" is a state, not a manoeuvre label, and validity does not depend on its meaning.

### S1.8 Supporting detail for the diagnosis (Section V-B): data, pairing, X1 and X2

X1 (plan `ab9b8e05…`) and X2 (plan `41bc5a93…`) are pre-specified in the same sense as the method stage `[E01 §8]`.

**Ground truth.** The seven tracking classes, boxes with at least one lidar-plus-radar point, bicycle-rack boxes excluding parked two-wheelers; train has 28,130 keyframes, 725,431 annotations and 2,439 rack boxes, val 6,019 keyframes `[E01 §2.1 / GT-TRAIN, GT-VAL]`.

**In-path rule and the planner's population.** From estimates only, the ego rear-axle pose is extrapolated 0–4 s in 0.5 s steps with a CTRV model from the current and previous keyframe poses; the union of the nine inflated footprints is the corridor, and an object is *in-path* if its box, swept at its estimated constant velocity, intersects it `[E01 §2.5 / XLIB ego_corridor, object_in_path]`. The analysis population is the in-path, paired, uncensored items, and it differs by construction from what a planner considers: 61–63 % of in-path paired tracks at planner decision times are behind the ego (following traffic) `[E01 §2.5 / R11B O2]`, whereas the K6 planner considers only tracks within 60 m whose center is not behind its rear bumper `[E01 §5.4 / K6SIM plan_step]`, so those tracks (counted approximately from the keyframe ego pose) never become its constraints `[R11B M1]`, while it relies on tracks within that range that are not in-path. This is the mechanism of the scope gap (S2.1).

**Records, pairing and items.** A *record* is one exported track at one keyframe (position, size, yaw, velocity, 2-D position covariance). *Export totals*, over all keyframes with frame 0 included: 381,553 records over 6,019 val keyframes and 1,839,331 over 28,130 train keyframes (T1). *Analysis records*, at k ≥ 1 because frame 0 has no ego-motion history: 373,702 (val) and 1,800,482 (train), after removing 7,851 and 38,849 frame-0 records; every cell table uses these `[E01 §2.4 / X1R, X2R: Q0, pairing.records_k_ge_1, pairing.frame0_records]`. Tracks are matched to same-class annotations by Hungarian assignment on bird's-eye-view center distance with a 2 m gate, and a pair persists for the track's life; misclassified tracks stay unpaired, so every analysis covers matched true positives only. On val 63.9 % and on train 67.4 % of in-path records were paired `[E01 §2.4]`.

**Criteria** `[E01 §3.7]`. *X1 G1*: some eligible cell (a1) FAILS against max(0.05, E⁰) at σ_a = 0.10 m, (a2) has a one-sided 98.75 % extra-margin lower bound above 0.10 m, (a3) FAILS at σ_a = 0.20 m, (a4) FAILS with contested records excluded, (a5) FAILS truth-oriented, and (b) NEES does not flag it correctly. *X2 H1* uses (a1)–(a5), with (a2) at the one-sided 97.5 % level.

**X1 and X2: criteria and operating characteristics.** *X1:* Criterion G1 required a FAILS cell meeting four robustness conditions and a NEES condition (above); the verdict was "NOT SHOWN, in either family" under a 97.5 % band (Bonferroni over the current-time and 2 s families), whose simulated false-FAILS rate was 0.002 against the file's limit of 0.0390 (nominal 0.025 plus 2 Monte Carlo SE) `[E01 §5.1, §3.4 / X1-REP; X1-FWER]`. Its 2 s lateral cells had 52–83 scenes each `[E01 §5.1 / X1R: family_h2s]`. *X2:* Pre-freeze false-FAILS rates were 0.024 (τ = 0.5) and 0.004 (τ = 1.0) against a limit of 0.0695; power was 1.00 at 0.6–1.0 × the X1 effect `[E01 §3.7, §5.2 / X2-FWER; X2-POWER]`.

**S1-Table 4. X1, 2 s family, in-path cars on val (record-weighted E; 97.5 % simultaneous band).** `[E01 §5.1 / X1R: family_h2s.primary, family_h2s.prices]`

| Cell | E | Threshold max(0.05, E⁰) | Band | Verdict | Predicted SD (m) | Needed variance factor s [95 % CI] |
|---|---|---|---|---|---|---|
| car < 20 m, longitudinal | 0.004 | 0.062 | [−0.002, 0.010] | OVERCOVERS | 3.34 | 0.25 [0.18, 0.32] |
| car < 20 m, lateral | 0.135 | 0.084 | [0.040, 0.229] | CONSISTENT | 0.67 | 5.3 [2.2, 7.4] |
| car 20–40 m, longitudinal | 0.009 | 0.050 | [−0.002, 0.019] | OVERCOVERS | 3.34 | 0.30 [0.25, 0.48] |
| car 20–40 m, lateral | 0.175 | 0.093 | [0.078, 0.271] | CONSISTENT | 0.67 | 2.6 [1.5, 10.7] |

**Reading of X2, continued from Section V-B.** (4) *Both lateral tails*: the away-from-ego tail is also exceeded (0.120 and 0.126, against toward-ego 0.193 and 0.272 in the same re-computation), so the lateral covariance is too narrow on both sides; estimate-based orientation adds about 0.04 to the toward-ego value `[R06 §3, m7]`. (5) *Concentration* (review statistics, not pre-specified): by ground-truth heading change over the 2 s, E = 0.100 below 5° (3,143 items), 0.405 at 5–15° (964) and 0.555 at 15–45° (492), so cars turning ≥ 5° carry 68 % of the exceedances, and moving, non-turning, well-headed cars give 0.035 at < 20 m; by scene, 68 % of the 654 exceedances at < 20 m come from the top 10 % of scenes, yet dropping the 20 scenes with most exceedances leaves 0.127 and one item per object gives 0.112, both above the 0.0775 threshold `[E01 §5.2, App. A row 5 / R06 §2, §3, m5]`. (6) *Composition*: the all-objects lateral exceedance is 0.0387 and 0.0383 (OVERCOVERS) because 80 % of those items are parked cars with E ≈ 0.002, while moving cars fail (0.157, 0.171) `[E01 §5.2 / X2R: sensitivities.all_objects; R06 M2]`. (7) *Robustness and reproduction*: the verdict-tipping annotation noise is 0.75 m (point-tipping 0.90–0.95 m); a 4 m gate and per-frame re-matching keep the FAILS `[E01 §5.2 / X2R: sensitivities]`, and so does a log-cluster bootstrap `[X2R: family_h2s.log_cluster_band]`; velocity-defined axes and the logged ego pose were checked with point estimates only, without a verdict `[R06 §2]`; separate code gave lateral E 0.1927 / 0.2724 against 0.1941 / 0.2718 and prices 11.62 / 10.32 m, and verified all 65 frozen hashes `[E01 §6 / R06]`.

**What was seen before X1 and X2** `[E01 §2.8]`. X1 ran on val with T1; val had been examined before and T1's Q was tuned on it, so X1 is confirmatory with respect to its plan, not to the data. X2 tested a new hypothesis from X1's descriptive 2 s result on train, which shares no scene or log with val; the detector and R are in-sample there. **Disclosure:** one pre-freeze synthetic test built its tracks from real train ground truth and so previewed the decision (synthetic price 9.35 m against 11.61 m real). The freeze-and-run script was written 16 minutes before that leak, has no branch on the result and ran unattended, but byte identity of the plan before the leak cannot be proven `[E01 §5.2 / D06]`.

---

## S2. The planner studies on nuScenes: K6, and K8 in full

### S2.1 K6, the first planner study (pre-specified; NO-GO)

`[K6-PLAN = the K6 plan 6446d9f6…, 97 files; K6R; K6SIM; E01 §5.4, §7, §8; R11A; R11B]`

This subsection collects every statement about K6.
- **Design.** The first planner study was pre-specified (plan `6446d9f6…`, 97 files) `[E01 §8]`. It replayed a real tracker's recorded covariance (T1 or T3) into the chance-constrained speed planner in decision mode, with DP-SCRC calibrated on the audit population of S1 `[E01 §5.4, §7]`. The 10 v1.0-mini scenes served only to develop its closed-loop harness `[E01 §2.1; K6-PLAN §3]`. Its cross-fit seed was 20261101.
- **The planner's population.** The K6 planner considers only tracks within 60 m whose center is not behind its rear bumper `[E01 §5.4 / K6SIM plan_step]`. Of the in-path paired tracks at planner decision times, 61–63 % are behind the ego (following traffic) `[E01 §2.5 / R11B O2]`, so those tracks (counted approximately from the keyframe ego pose) never become its constraints `[R11B M1]`, while it relies on tracks within that range that are not in-path.
- **Verdict: NO-GO on a power floor.** T3 had 5 power-qualified cells against the floor of 6; T1 had 7 in the run of record and 5 when computed precisely `[E01 §5.4, §7; K6R]`.
- **The scope gap.** On relied constraints from tracks that are not in-path, DP-SCRC was significantly above δ in 2 cells on T1 and 6 on T3 (0.073–0.101), while no cell of the audited population was flagged `[E01 §5.4 / K6R: populations.SD2_not_in_path, decide.*]`.
- **The response.** A calibration population matched to the planner's relied constraints: M\* (Section IV), developed in K8 (S2.2) and tested on new data in Section V-D.
- **The one independent audit.** The audit of the K6 power rule, written from the plan text before the frozen code was read, is the only nuScenes re-derivation that meets our definition of independent `[E01 §6 / R11A]`.

### S2.2 K8 in full (exploratory development evidence; Section V-C)

`[K8 = 70_TESTS/k8_expl_v02_analysis_v03/k8_exploratory_analysis_v03.json; K8T = 80_LOGS/c1_manuscript_v01/k8_arm_table_v01.json; D14 = 90_DECISIONS/D14_K8_DESIGN_v05.md; R16 = 70_TESTS/R16_K8_RESULTS_REVIEW_v01.md; ERR = 90_DECISIONS/ERRATA_K8_v03.md; JN = 60_RESULTS/k8_joint_v01/K8_JOINT_NOTE_v01.md]`

**Harness.** A real tracker's recorded covariance (T1 or T3) is replayed from the logged ego's state into the chance-constrained speed planner of Appendix B, specified in full in S9.
- **The planner.** It chooses among 32 accelerate-then-brake candidates and an emergency stop, and backs the margin off (λ ∈ {0.75, 0.5, 0.25, 0}) when nothing is feasible.
- **Decision mode** carries every comparison. It is open loop: one decision per keyframe from the logged state, identical across arms, scored on the records each arm relied on under its own chosen, leashed plan (Section IV-A; S9.10–S9.11), and not executed.
- **Loop mode** (non-reactive replay [Karnchanachari2024]) is descriptive (below).

`[D14 §2; ERR E16]`

**K8 data and rules.**
- **The data.** 840 scenes (68 logs; 10 development scenes excluded), 32,065 decisions per arm, and 919,396 (T1) and 920,618 (T3) relied items at the reference pose `[K8: decide.*.calibration_items.ref_relied_items]`. Each arm is scored on the P_rel records it relied on under its own plan, so the scored sets differ by arm (on T1, 914,867 for M\* and 686,705 for B3) `[K8: decide.t1.counts.records_by_population.PD7_primary]`.
- **Fitting and inference.** Fits are cross-fitted over 5 log folds, with a log-cluster bootstrap (B = 2000). Cells (group × axis × course-change state) are evaluable with ≥ 39 scenes from ≥ 8 logs.
- **The power rule.** K8's rule is its own: power ≥ 0.80 to flag an exceedance of 0.15 with every family cell planted together (scene units, ρ = 0.5, 200 datasets), and a floor of 6 power-qualified cells. The registered rule (Section V-D3) plants one cell at a time; under it the development families are 27 / 18 / 5 (T1) and 26 / 18 / 5 (T3).

`[K8: decide.*.scenes, logs, counts; D14 §3–§4; C1-PLAN §6.1]`

**Arms.** M\* is compared with:
- B0 (raw);
- B1 (NEES-scaled);
- B3 (the largest of M\*'s thresholds, hence at least M\*'s margin on every item);
- B4 (one pooled conformal threshold);
- B6 (M\* without course-change strata);
- B9 (norm ball);
- RETUNED [Shah2026; Mustafa2023]. RETUNED is the least conservative point of a 21-point curve of B0, scaled by a factor up to 8 or set to a nominal risk δ′, whose pooled exceedance is ≤ δ on P_rel, P_near and P_ip (the *pooled rule*). It is selected cross-fitted and judged, like every arm, by the cell rule.

**Results (S2-Table 1).**
- **Validity.** M\* is shown above δ in no cell, family cell or pooled cell of P_rel, P_near or P_ip, on either tracker (one-sided simultaneous 0.95).
  - Its pooled P_rel exceedance is 0.042 (T1; upper bound 0.045) and 0.040 (T3; 0.043).
  - Point estimates exceed δ in 9 of 32 P_rel cells on T1 and 11 on T3; the largest are 0.058 and 0.065, and 0.085 in one T1 P_near cell. None is near a flag.
  - The power-qualified families under K8's rule are 28 / 18 / 5 (T1) and 27 / 18 / 5 (T3).

  `[K8: decide.*.hypotheses, validity_by_arm.Mstar; K8 csv; ERR E10]`
- **The raw covariance on this population is mostly too wide.** B0's pooled P_rel exceedance is 0.026 (T1) and 0.002 (T3). It is flagged in 4 T1 cells (car lateral turning and new; car longitudinal new; pedestrian longitudinal static) and none on T3 `[K8T]`.
  - The in-path lateral cars that carry Section V-B's diagnosis are rare among relied items: 0.4 % at 2 s, computed on the validation split (T1; 115 of the 27,044 P_rel items of the Trajectron++ study, S3), not on K8's 840 scenes `[R19 §3; V05_NUMBER_TRACE_v01 U1]`.
  - M\* therefore mostly narrows margins. Its mean lateral / longitudinal margin is 0.61 / 0.95 m against B0's 1.80 / 2.29 m on T1, and 0.76 / 1.68 m against 6.64 / 7.59 m on T3.
- **Back-off of the designed margin.** At identical states M\* is infeasible, that is, backs off its designed margin, in 0.114 (T1) and 0.161 (T3) of decisions. B4 is infeasible in 0.198 and 0.208 (paired −0.084 and −0.047; one-sided 0.9875 bounds −0.064 and −0.031), and B0 in 0.338 and 0.764 `[K8: decide.*.infeasible_rate; d14_forms]`.
- **Ground-truth violations at the chosen plan** (V2_viol: some relied constraint whose projected error exceeds its gap, over the 4 calibrated steps). M\* has 0.008 against B0's 0.012 on T1, and 0.009 against 0.005 on T3. On T3 the narrower margins cost real violations `[K8T; R16 M1]`.
- **Comparators not shown above δ.** These are B3 on T1, and B0 and B3 on T3. M\* is less often infeasible than each (paired −0.75; −0.60 and −0.71).
  - These comparisons carry little evidence. B3, whose margin is at least M\*'s on every item by construction, is infeasible in 0.87 of decisions, and T3's B0 in 0.76.
  - The informative comparison on T3 is with B6, where the course-change strata buy nothing: M\* − B6 = −0.005 [−0.016, +0.005] (−0.016 on the Linux replicate). Form B holds on T3 only because B6 itself is shown above δ (in 12 P_rel cells on each tracker).
  - On T1 the strata pay: −0.062 [−0.081, −0.043] `[K8: paired_vs_Mstar.infeasible_rate.B6; ERR E12]`.
- **RETUNED** equals B0 on T1, where, in sample and within the factor-8 grid, no sweep point passes the cell rule. On T3 the cheapest sweep point not shown above δ is infeasible in 0.581 of decisions `[K8: retune; ERR E14; R16 §5 item 11]`.

**Per constraint is not per decision.** V2 is the share of decisions with some relied constraint exceeded over the 4 calibrated steps and all tracks. It counts only decisions with at least one scored record and is the mean over scenes of each scene's share (over logs on Argoverse 2). For M\* it is 0.358 (T1) and 0.351 (T3).
- **Against a per-track reference.** A decision holds 8.35 (T1) and 8.34 (T3) tracks, and 1 − 0.95^{n_tracks} gives 0.308. V2 is 0.050 [0.035, 0.067] and 0.043 [0.028, 0.058] above that reference.
- **Against independence.** A decision also holds about 30 relied records, for which independence would give 0.65. The records are strongly dependent `[K8: V2.PD7_primary.Mstar; ERR E9; R16 M1]`.
- **A trajectory-level variant.** M\*J calibrates one scalar on the union loss. It brings V2 to 0.048 and 0.049, at +0.307 and +0.393 in infeasible-decision rate `[JN]`.
- **What δ is.** δ = 0.05 is a calibration level, not a safety target. Certifying δ = 0.01 needs ≥ 99 calibration units per own-threshold stratum (Section IV-C; S8-Remark 5), and was not studied.

**Reading.**
- **What K8 is.** Transductive development evidence: the fits use all 850 scenes, M\* was developed on them, T1's Q was tuned on nuScenes validation, and the gates are ours. A Linux replicate and a separate-code review reproduced it (below).
- **What the confirmation took from it.** The registered test's rules (Section V-D) were set on these data. A design set on development looks favourable there; Section V-D5 and S5.7(6) state what the confirmation can and cannot detect.

**S2-Table 1. K8 (nuScenes development, decision mode), per arm and tracker.** Valid: not shown above δ on every population; pooled exceedance on P_rel / P_near / P_ip; flagged P_rel cells; infeasible-decision rate; V2 and V2_viol on P_rel; mean lateral / longitudinal margin (m) on the arm-independent calibration items; Z0 is margin 0. `[K8T]`

| Tracker | Arm | Valid | P_rel | P_near | P_ip | P_rel flagged | Infeasible | V2 | V2_viol | Margin lat / long (m) |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | M\* | yes | 0.042 | 0.032 | 0.049 | 0 / 32 | 0.114 | 0.358 | 0.008 | 0.61 / 0.95 |
| T1 | B0 | no | 0.026 | 0.025 | 0.044 | 4 / 32 | 0.338 | 0.216 | 0.012 | 1.80 / 2.29 |
| T1 | B1 | no | 0.017 | 0.018 | 0.040 | 5 / 32 | 0.390 | 0.151 | 0.013 | 3.09 / 2.85 |
| T1 | B3 | yes | 0.002 | 0.001 | 0.001 | 0 / 32 | 0.866 | 0.030 | 0.004 | 8.77 / 11.21 |
| T1 | B4 | no | 0.052 | 0.044 | 0.077 | 12 / 32 | 0.198 | 0.370 | 0.014 | 1.09 / 1.40 |
| T1 | B6 | no | 0.043 | 0.036 | 0.048 | 12 / 32 | 0.176 | 0.328 | 0.012 | 0.70 / 1.44 |
| T1 | B9 | no | 0.013 | 0.007 | 0.028 | 2 / 32 | 0.447 | 0.126 | 0.006 | 2.45 / 2.45 |
| T1 | RETUNED | no | 0.026 | 0.025 | 0.044 | 4 / 32 | 0.338 | 0.216 | 0.012 | 1.80 / 2.29 |
| T1 | Z0 | no | 0.502 | 0.493 | 0.457 | 32 / 32 | 0.008 | 0.947 | 0.034 | — / — |
| T3 | M\* | yes | 0.040 | 0.031 | 0.042 | 0 / 32 | 0.161 | 0.351 | 0.009 | 0.76 / 1.68 |
| T3 | B0 | yes | 0.002 | 0.000 | 0.002 | 0 / 32 | 0.764 | 0.026 | 0.005 | 6.64 / 7.59 |
| T3 | B1 | no | 0.022 | 0.016 | 0.043 | 9 / 32 | 0.379 | 0.194 | 0.012 | 2.16 / 2.58 |
| T3 | B3 | yes | 0.002 | 0.001 | 0.003 | 0 / 32 | 0.870 | 0.021 | 0.004 | 9.91 / 11.31 |
| T3 | B4 | no | 0.057 | 0.039 | 0.106 | 11 / 32 | 0.208 | 0.403 | 0.018 | 1.06 / 1.22 |
| T3 | B6 | no | 0.045 | 0.035 | 0.049 | 12 / 32 | 0.167 | 0.363 | 0.011 | 0.72 / 1.96 |
| T3 | B9 | no | 0.014 | 0.007 | 0.033 | 1 / 32 | 0.434 | 0.141 | 0.008 | 2.33 / 2.33 |
| T3 | RETUNED | no | 0.023 | 0.013 | 0.040 | 5 / 32 | 0.431 | 0.210 | 0.010 | 2.12 / 2.42 |
| T3 | Z0 | no | 0.514 | 0.496 | 0.484 | 32 / 32 | 0.003 | 0.953 | 0.030 | — / — |

**Loop mode, reproduction and M\*J.**
- **Loop mode.** In closed-loop log replay with non-reactive agents, no difference in at-fault collisions between M\* and any comparator was resolved on either tracker. At-fault collisions with tracked agents per 1,000 episodes are 24.9 (T1) and 31.6 (T3) for M\*, 28.3 and 27.8 for B4, and 22.4 and 20.2 for Z0 (margin 0) `[K8: loop.*.safety_reading; ERR E8; R16]`.
- **Reproduction.** A replicate on Linux reproduced every decision-mode verdict and comparator set, and the infeasible-decision rates of M\*, B4, B6, B0 and B3 to six decimals `[PC2 = 70_TESTS/k8_expl_v02_linux/PLATFORM_CHECK_v02.md, l. 10–25]`.
- **The results review.** It used code separate from the analysis and found the reading sound after seven errata; later checks added two more `[R16; ERR E8–E14, E15, E16]`.
- **M\*J.** It calibrates one scalar on the union loss over a decision's relied constraints. Its V2 upper bounds are 0.058 and 0.059, and 42 % and 55 % of its decisions run at a reduced margin `[JN l. 139–217]`.

---

## S3. A learned predictor: Trajectron++ on nuScenes (pre-specified, frozen, reviewed)

`[D17 = 90_DECISIONS/D17_TPP_ARM_PREREG_v04.md, SHA-256 e9d98d92…; J = 60_RESULTS/tpp_v01/tpp_analysis_v04.json; R19 = 70_TESTS/R19_TPP_RESULTS_REVIEW_v01.md]`

**Design.** A deployed stack would use a learned trajectory predictor, so we asked how its covariance fares along the planner's constraints.
- **The plan.** It was frozen on 4 Nov 2026 with 26 bound files, before its analysis ran.
- **The model.** Trajectron++ [Salzmann2020]: the authors' `int_ee` checkpoint, trained on the 700 nuScenes training scenes, without a map. It runs online through our adaptation of the authors' code, one decoder draw per pass, with the moment-matched covariance primary.
- **The data.** It predicts on the validation split (150 scenes, 18 logs) from T1's and T3's histories. Each prediction is scored at 2 s along K8's relied constraints (Section IV-A; S2.2): 27,044 (T1) and 27,119 (T3) P_rel items from 144 scenes. These are the constraints of the tracker-fed planner; a planner fed by Trajectron++ would form its own.
- **The correction.** DP-SCRC is cross-fitted on 5 scene folds, which split logs and are anti-conservative relative to the log unit used elsewhere. Its comparators are B4 and B3. Each hypothesis is tested under 3 decoder seeds with a log-cluster bootstrap (B = 2000).

`[D17 l. 72–278; J: trackers.*.primary_v2.populations]`

**Results (S3-Table 1; all three hypotheses held under all six tracker–seed runs).**
- **TPP-H1: over-confidence in scale.**
  - The raw pooled P_rel exceedance is 0.135 (T1; lower bound 0.117) and 0.125 (T3; 0.108), stable across seeds.
  - NEES sees it directly: record-level ANEES 16.6 and 10.2 against 2, and 95 % ellipse coverage 0.68 and 0.69. This is not a case where NEES misleads `[J: validity.TPP_B0; A6.TPP]`.
- **TPP-H2: DP-SCRC on the relied items (the M\* fit of Section IV, one check time).**
  - No evaluated P_rel cell is flagged (0 of 20 per tracker), and the pooled exceedance is 0.034 and 0.033.
  - The mean margin rises from 0.98 to 2.17 m (T1) and from 1.04 to 2.14 m (T3). The tracker's own M\*-calibrated extrapolation uses 1.5 m and 2.4 m on the same items.
  - **The single multiplier nearly suffices.** One pooled multiplier (B4) reaches 0.042 on both trackers with one cell flagged on each, at a slightly smaller mean margin (2.07 and 2.12 m).
  - Only 3 P_rel cells are power-qualified, below the floor of 6 used elsewhere, so the result reads "not shown above δ in the evaluated cells" `[J: validity.TPP_Mstar; R19 l. 47, 113, §5]`.
- **TPP-H3: tracker histories cost coverage.** With ground-truth histories the raw exceedance is 0.094 and 0.093, so about half the excess remains. The paired history effect is +0.042 (lower bound 0.036) and +0.032 (0.027) `[J: pooled_stats.paired]`.

**Review and scope.** A results review with its own code reproduced every point estimate to 10⁻¹² `[R19]`.
- **Short histories.** It found that records with only two tracker states (14 % of items) stay above δ after correction (0.079, 0.072). For this reason the Argoverse 2 study stratifies the predictor's calibration by history length (H9, descriptive; S4(f)).
- **Scope.** This is development-side evidence on 18 log clusters, with no planner outcome.

**S3-Table 1. Trajectron++ on nuScenes validation (P_rel, 2 s, primary seed): pooled exceedance with its one-sided 95 % lower and upper bounds, flagged cells of the 20 evaluable ones (one-sided simultaneous 0.95), and mean margin.** `[80_LOGS/c1_manuscript_v01/tpp_table_v01.json from J]`

| Arm | T1 pooled exc. [LB, UB] | T1 flagged / evaluable | T1 mean margin (m) | T3 pooled exc. [LB, UB] | T3 flagged / evaluable | T3 mean margin (m) |
|---|---|---|---|---|---|---|
| Trajectron++, raw | 0.135 [0.117, 0.152] | 15 / 20 | 0.98 | 0.125 [0.108, 0.141] | 15 / 20 | 1.04 |
| Trajectron++ with ground-truth histories, raw | 0.094 [0.078, 0.108] | 13 / 20 | 0.80 | 0.093 [0.077, 0.107] | 12 / 20 | 0.80 |
| Trajectron++ + DP-SCRC | 0.034 [0.029, 0.039] | 0 / 20 | 2.17 | 0.033 [0.029, 0.038] | 0 / 20 | 2.14 |
| Trajectron++ + one pooled multiplier (B4) | 0.042 [0.034, 0.049] | 1 / 20 | 2.07 | 0.042 [0.033, 0.049] | 1 / 20 | 2.12 |
| Trajectron++ + certified single multiplier (B3) | 0.001 [0.000, 0.001] | 0 / 20 | 8.38 | 0.002 [0.001, 0.004] | 0 / 20 | 6.29 |
| tracker extrapolation, raw | 0.016 [0.012, 0.020] | 0 / 20 | 3.62 | 0.001 [-0.000, 0.002] | 0 / 20 | 10.55 |
| tracker extrapolation + DP-SCRC | 0.032 [0.024, 0.038] | 0 / 20 | 1.50 | 0.030 [0.023, 0.037] | 0 / 20 | 2.40 |

---

## S4. Full results of the registered test on Argoverse 2

Section V-D gives the main results; every item of the registered output list is here, with its source key. `[C1D = 60_RESULTS/c1_av2_v01/c1_decision_r1.json, SHA-256 ff976904…; C1A = 60_RESULTS/c1_av2_v01/c1_analysis_r1.json, 1100bbf7…; CSV = 60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/; MST = 60_RESULTS/c1_av2_v01/mstage/; H9T = 60_RESULTS/c1_av2_v01/h9/; RL = 40_PROTOCOL/C1_RUN_LOG.txt, 8bc6235d…; R21 = 70_TESTS/R21_c1_v01/real/; TRK = 60_RESULTS/av2_trk/c1_375/; MAT = 80_LOGS/c1_manuscript_v01/C1_RESULTS_MATERIAL_r1_v01.md; FIG = 95_SUBMISSION/figs_v01/figs_v01_manifest.json; FR2 = 20_DESIGN/C1_REPORTING_FRAMES_v02.md; FR3 = 20_DESIGN/C1_REPORTING_FRAMES_v03.md]`

Populations: P_rel, P_near and P_ip (Section IV-A) `[code names: P_rel = PD7, P_near = SD1_7, P_ip = PD]`. Comparator cells are flagged at the removal level 1 − 0.0125/9 = 0.99861; M\*'s cells at 0.95. Point estimates and bounds are rounded to three decimals.

### S4.0 The pre-fixed abstract

**What it was.** Before the verdict existed, the reporting frames (`20_DESIGN/C1_REPORTING_FRAMES_v03.md` §6) fixed the abstract's text, with slots to be filled mechanically from the run of record, to prevent outcome-driven wording. It was filled from r1 `[20_DESIGN/ABSTRACT_FILLED_r1_v01.md, SHA-256 18ee398f…]`: branch GO; qualifier Q-construct on T1 (CANMOT) and T3 (Poly-MOT); {H8} = "replicated"; {u} = 0.055, the largest M\* pooled HK1c bound at 0.995 (T1, P_ip, 0.05460) rounded up; {X} = "in neither secondary test"; 248 words. Its text, verbatim:

> Chance-constrained planners with linearized half-space constraints need tracker covariances covering the one-sided error tail along each constraint normal (decision-projected calibration); passing the normalized estimation error squared (NEES) test is neither necessary nor sufficient. In a pre-specified nuScenes study, a tracker's 2 s extrapolation exceeds the toward-ego lateral margin of in-path cars in 19.4–27.2% of items (nominal 5%); the NEES-guided scalar leaves this tail at 13.0–17.2%, and lateral-fixing scalars add 10–12 m of longitudinal margin; on Argoverse 2 the diagnosis replicated. We propose DP-SCRC, stratified conformal risk control in constraint coordinates delivered as a recalibrated covariance, with a scene-level, stratum-marginal certificate on audited objects; on three nuScenes tracker settings no validation cell was shown above 5%. In an exploratory planner study, the planner-matched variant M\*, which mostly narrows over-wide raw covariances, was shown above 5% in no cell; the result is per constraint, not per decision: about one decision in three has an exceeded constraint. In a registered test on 375 held-out Argoverse 2 logs, with M\* re-fitted there, no evaluable M\* cell was shown above 5% on either tracker (simultaneous 95% bounds; power at least 0.8 against 15% in power-qualified cells), its approximate pooled 99.5% upper bounds were at most 0.055, and it was less often infeasible than every comparator not shown above 5%; on CANMOT and Poly-MOT those comparators were conservative by construction or mostly infeasible. Here 5% is a calibration level, not a safety target; transfer of the nuScenes-fitted rule was supported in neither secondary test.

**Why the manuscript's abstract replaces it** `[the authors' decision record; 20_DESIGN/V06_STRUCTURE_PLAN_v01.md §3; 70_TESTS/V05_REFEREE_REVIEW_v01.md, M2, M4(e), M6, M7, M9]`. An internal review found that the pre-fixed text invited a wrong reading of the operability clause and left out negatives. The same review asked that its nuScenes validity sentence move to the body with the qualifier of S1. The manuscript's abstract is therefore a documented departure from the frames, recorded, and kept with the claim it states, in the authors' decision record. It follows these rules:
- it removes no registered result and adds negatives and qualifiers;
- it says early that the raw covariance is mostly too wide on relied constraints;
- it names the proxy population;
- it reports X3 as post-registration exploratory;
- every number in it is traced.

The pre-fixed text stays in the record and is quoted here.

### S4(a) The verdict of record

- **Verdict.** GO `[C1D: C1_verdict]`. H1 holds, no condition failed and no input was missing `[C1D: gate_H1; failed_conditions = []; nogo_reasons = []; missing_inputs = []]`. Q1 is the only claim not tested (item (f)) `[C1D: not_tested]`.
- **The run.** The frozen analysis (`c1_analyse_v10`, B = 40,000) ran once `[C1A: binding.entry_point; C1D: criteria.constants.B_BOOT]`. Its start and done lines are lines 81 and 82 of the run log (7 Nov 2026, 10:33:58 and 12:22:43 UTC; run id ed69b9e4…) `[RL: lines 81–82; C1D: binding.run_id]`. The done line records both outputs with their SHA-256 `[RL: line 82, outputs_sha256]`.
- **Completion check (plan §9).** None of the seven resource-error strings occurs in the decision, no route problem is recorded, and both outputs exist. The run is therefore a completed run, not an environment stop `[C1D: full text, 0 matches for each string; route_problems = {}]`. The reruns `_r2` to `_r4` were not needed (the completion rules are in S5.8). The run-log check found no start line without its done line `[R21: r21_runlog_check_r1.md]`.
- **Branch and qualifiers.** The branch is GO, with no flag (E, A, B, C or D) on either tracker `[FR2 §1; C1D: nogo_reasons = []; MAT: verdict line]`.
  - **Q-construct holds on both trackers.** V_t is {B3} on T1 and {B0, B3} on T3 `[C1D: hypotheses.H1.by_tracker.t1.V; .t3.V]`. B3's margin is at least M\*'s on every item, and T3's B0 is infeasible in 0.858 of decisions `[CSV: k8_within_lt3d_t3_decide_arms.csv, B0 infeasible_rate]`.
  - **Q-empty and Q-zse do not apply.** V_t is non-empty on both trackers, and no zero-SE case changed V_t `[C1D: zero_se_effects.by_route.within_lt3d]`.

**The verdict sentence** (with its qualifier, as one sentence) `[FR2 §3]`. In a registered, one-shot test on 375 Argoverse 2 logs not used to train the detector, with M\* re-fitted within Argoverse 2, no evaluable cell of M\* was shown above δ = 0.05 on either tracker (one-sided simultaneous 0.95; power ≥ 0.8 against a per-cell exceedance of 0.15 in the power-qualified cells), its pooled 99.5 % upper bounds (nominal, approximate) were at most 0.055, and it was less often infeasible than every comparator not shown above δ, which on CANMOT and Poly-MOT were only comparators at least as conservative by construction or infeasible in most decisions. `[C1D: C1_verdict; 0.055 = the largest of the six HK1c bounds, 0.0546 (T1, P_ip), rounded up as in FR3 §6: CSV: k8_within_lt3d_t1_decide_validity.csv, Mstar PD_inpath pooled_ub; qualifier: C1D: hypotheses.H1.by_tracker.*.V]`

- **Beside the verdict: power at 0.10 and U_max.**
  - **Power at a per-cell exceedance of 0.10.** M\*'s cells had median power 0.606 (T1) and 0.582 (T3) on P_rel, 0.115 and 0.122 on P_near, and 0.213 and 0.235 on P_ip. Only 7, 1 and 0 cells (T1) and 8, 2 and 0 cells (T3) reached 0.80 `[C1D: Mstar_power_families.by_route.within_lt3d.t1/t3.<population>.per_cell."0.10"]`. A cell whose true exceedance is 0.10 passes with probability near one minus its power at 0.10, which for most cells is substantial.
  - **U_max (approximate).** M\*'s largest simultaneous 95 % cell upper bounds are 0.127, 0.118 and 0.129 (T1) and 0.122, 0.110 and 0.157 (T3) on P_rel, P_near and P_ip `[C1D: Mstar_simultaneous_upper_bounds.by_route.within_lt3d.t1/t3.<population>.max_ub]`. Exceedances as large as 0.157 therefore cannot be excluded in individual cells. These bounds understate: in the X3 simulation at Argoverse 2's cell sizes they covered 0.376–0.547 as a simultaneous set at δ, against the nominal 0.95, and studentized bounds, which cover near nominal, give 0.1556–0.1894 (S6.4).
- **Scope** (always added) `[FR2 §2]`.
  - The result is per relied constraint, not per decision.
  - δ = 0.05 is a calibration level, not a safety target.
  - The primary test re-fits M\* within Argoverse 2. Transfer of the nuScenes-fitted rule is tested by H4 and H7 (item (e)).
- **The main-text items in brief** (details in (b)–(e)) `[FR2 §3]`.
  - **V_t.** {B3} (T1) and {B0, B3} (T3) `[C1D: hypotheses.H1.by_tracker.*.V]`.
  - **The informative comparison.** On T3, B6 was shown above δ and left V_t. M\* was 0.018 more often infeasible than B6 there `[CSV: k8_within_lt3d_t3_decide_paired.csv, infeasible_rate B6 Mstar]`.
  - **Family S.** H2 is confirmed. H3, H4, H6b and H10 are not confirmed `[C1D: family_S.*.confirmed]`.
  - **H7 and H8.** H7 does not hold; H8 holds `[C1D: claims_status.H7; .H8]`.
  - **Per decision.** V2 is 0.491 and 0.496, against a per-track reference of 0.441. The excess, about 0.05, is the same as on development (item (d)) `[CSV: k8_within_lt3d_t1/t3_decide_v2.csv, PD7_primary Mstar V2]`.

### S4(b) H1: the registered screen and V_t (S4-Table 1, S4-Table 2)

**S4-Table 1. The registered screen for M\*, per tracker and population** (within Argoverse 2: own detector, 375 logs, decision mode).

Each condition is shown with its value and its threshold:
- **cells flagged:** the number of flagged cells, with the largest simultaneous 0.95 lower bound in brackets (a cell is flagged if that bound is above 0.05);
- **power family:** the number of power-qualified cells, with their record share, and how many of them are flagged;
- **pooled:** the estimate, with its pointwise 0.95 lower bound in brackets (the pooled cell is flagged if that bound is above 0.05);
- **floor:** at least 6 power-qualified cells on P_rel and P_near, and at least 1 evaluable cell on P_ip;
- **HK1c:** the pooled upper bound at 0.995 must be at most 0.08.

| Tracker | Population | Evaluable cells | Cells flagged (largest LB) | Power family (share); flagged | Pooled E [LB] | Floor | HK1c UB^0.995 | Met |
|---|---|---|---|---|---|---|---|---|
| T1 | P_rel | 27 | 0 (0.042) | 19 (0.987); 0 | 0.044 [0.041] | 19 ≥ 6 | 0.048 | yes |
| T1 | P_near | 16 | 0 (0.019) | 9 (0.907); 0 | 0.038 [0.030] | 9 ≥ 6 | 0.047 | yes |
| T1 | P_ip | 8 | 0 (0.016) | 5 (0.786); 0 | 0.040 [0.030] | 8 ≥ 1 | 0.055 | yes |
| T3 | P_rel | 27 | 0 (0.041) | 19 (0.988); 0 | 0.043 [0.040] | 19 ≥ 6 | 0.047 | yes |
| T3 | P_near | 16 | 0 (0.018) | 8 (0.883); 0 | 0.032 [0.026] | 8 ≥ 6 | 0.041 | yes |
| T3 | P_ip | 8 | 0 (0.023) | 5 (0.797); 0 | 0.040 [0.032] | 8 ≥ 1 | 0.052 | yes |

Sources:
- conditions: `[C1A: c1.within_lt3d.t1/t3.status.Mstar.pops.<population>]`;
- largest lower bound: `[C1A: k8.within_lt3d.t*.HK1.pops.<population>.max_lb = CSV: k8_within_lt3d_t*_decide_cells.csv, Mstar, max lb_sim]`;
- family and share: `[C1D: Mstar_power_families.by_route.within_lt3d.t*.<population>.family_size, family_record_share]`;
- pooled columns: `[CSV: k8_within_lt3d_t*_decide_validity.csv, Mstar, pooled_E, pooled_lb, pooled_ub]`.

**S4-Table 2. V_t and Form B, per tracker.** A comparator leaves V_t only through a flag at one-sided 0.99861 (cell, family cell or pooled cell, on any population). Form B's one-sided upper bound on the log-mean difference in infeasible-decision rate, M\* minus comparator, is at 1 − 0.0125/|V_t|. A negative bound favors M\*.

| Tracker | Comparator | In V_t | Why: the removal condition, or why it stays | M\* − c | Form B UB (level) |
|---|---|---|---|---|---|
| T1 | B0 | no | P_rel cells car long new, car lat turning and pedestrian long static flagged (cells and family cells) | – | – |
| T1 | B1 | no | P_rel cell large long new flagged | – | – |
| T1 | B3 | yes | not shown above δ (fails only the P_near floor) | −0.783 | −0.760 (0.9875) |
| T1 | B4 | no | 9 P_rel cells and 9 family cells; P_near family cell car lat turning; P_ip cell and family cell car long new | – | – |
| T1 | B6 | no | 5 P_rel cells and family cells (car long turning and new; car lat straight, turning and new); P_near family cell car lat turning | – | – |
| T1 | B9 | no | P_rel cell car long new (cell and family cell) | – | – |
| T1 | RETUNED | no | P_rel cells car long new and car lat turning (cells and family cells) | – | – |
| T3 | B0 | yes | not shown above δ (fails only the P_near floor) | −0.611 | −0.582 (0.99375) |
| T3 | B1 | no | P_rel family cell car long new | – | – |
| T3 | B3 | yes | not shown above δ (fails only the P_near floor) | −0.694 | −0.666 (0.99375) |
| T3 | B4 | no | P_rel: 6 cells, 4 family cells and the pooled cell; P_near: 3 cells and 2 family cells; P_ip: 3 cells, 3 family cells and the pooled cell | – | – |
| T3 | B6 | no | 5 P_rel cells and family cells (car long straight, turning and new; car lat turning and new) | – | – |
| T3 | B9 | no | P_rel cell car long new (cell and family cell) | – | – |
| T3 | RETUNED | no | P_rel cells car long turning and new; family cells car long straight, turning and new | – | – |

Sources:
- membership and reasons: `[C1D: hypotheses.H1.by_tracker.t1/t3.comparator_reasons]`;
- differences and bounds: `[C1D: hypotheses.H1.by_tracker.t1/t3.vs.<c>.mean_diff, ub, level]`.

- **The plan's sentence for the screen** (plan §6.6, filled from the decision).
  - **T1.** "No cell was shown above δ. Each of the 33 power-qualified cells (covering 98.7 % of P_rel, 90.7 % of P_near and 78.6 % of P_ip records) had power ≥ 0.8 to be flagged at a per-cell exceedance of 0.15. The other evaluable cells were tested without a power claim." The 33 cells are 19, 9 and 5 per population `[C1D: Mstar_power_families.by_route.within_lt3d.t1.<population>.family_size, family_record_share]`.
  - **T3.** The same sentence, with 32 cells (19, 8 and 5) covering 98.8 %, 88.3 % and 79.7 % `[C1D: Mstar_power_families.by_route.within_lt3d.t3]`.
- **Per-cell power and MDE80** (descriptive; they decide nothing).
  - **Medians across cells.** At planted exceedances of 0.10, 0.12, 0.15 and 0.20, M\*'s P_rel cells have median power 0.606, 0.952, 1.000 and 1.000 (T1) and 0.582, 0.940, 1.000 and 1.000 (T3). The P_near medians are 0.115, 0.400, 0.851 and 0.997 (T1) and 0.122, 0.373, 0.799 and 0.998 (T3). The P_ip medians are 0.213, 0.553, 0.907 and 0.999 (T1) and 0.235, 0.584, 0.923 and 0.998 (T3) `[C1D: Mstar_power_families.by_route.within_lt3d.t*.<population>.per_cell]`.
  - **MDE80.** Its median is 0.12 on P_rel and 0.15 on P_near and P_ip on both trackers `[C1D: ….mde80]`.
  - **Cells without 0.80 power even at 0.20.** On each tracker there are 5 such cells on P_rel (the three two-wheeler cells and two large-vehicle lateral cells), 2 on P_near and 1 on P_ip `[C1D: ….mde80 = null]`.
- **Zero-SE cases** (the rule is in S5.8). On the primary route, only T1's B3 had a zero-SE case: its P_ip family quantile `[C1D: zero_se_effects.by_route.within_lt3d.t1.B3]`.
  - It raised no flag, did not remove B3 and left V_t unchanged.
  - T3 and M\* had none `[C1D: zero_se_effects.by_route.within_lt3d; Mstar_zero_se_families = {}]`.
  - H1 is the same with and without zero-SE removals: it holds, with V_t {B3} and {B0, B3} `[R21: r21_rederive_r1.md, "without zero-SE removals"]`.
- **Form B is met on both trackers, and not vacuously** (S4-Table 2) `[C1D: hypotheses.H1.by_tracker.t1/t3.met, vacuous]`. These comparisons carry little evidence that M\* backs off its designed margin less often than an informative comparator.
  - **B3.** Its margin is at least M\*'s on every item (S8-Proposition 9), and it is infeasible in 0.969 (T1) and 0.941 (T3) of decisions.
  - **B0 on T3.** It is infeasible in 0.858 of decisions `[CSV: k8_within_lt3d_t*_decide_arms.csv, infeasible_rate]`.
- **The informative comparison: B6 on T3.** The plan expected GO on T3 to turn on B6 (plan §2) `[ERR E12]`.
  - **What happened.** B6, M\* without the course-change strata, was shown above δ on T3 in five P_rel cells and their family cells: car longitudinal straight, turning and new, and car lateral turning and new. So it left V_t, and Form B did not compare M\* with it `[C1D: hypotheses.H1.by_tracker.t3.comparator_reasons.B6]`.
  - **The paired comparison.** M\* was more often infeasible than B6: +0.018 [0.009, 0.027] on T3 and +0.021 [0.003, 0.039] on T1 (two-sided 95 %) `[CSV: k8_within_lt3d_t3/t1_decide_paired.csv, infeasible_rate, B6 vs Mstar, sign reversed]`. On development, T3's difference was −0.005 [−0.016, +0.005] (S2.2).
  - **Reading.** On Argoverse 2 the strata did not let M\* back off its designed margin less often than B6. B6, however, was shown above δ in cells where M\* was not (H10's cell part, item (e)).

### S4(c) M\*'s simultaneous cell bounds (S4-Table 3; main-text Fig. 2)

**S4-Table 3. M\*'s per-cell exceedances and their simultaneous one-sided 95 % bounds, within Argoverse 2.**
- The lower bounds decide M\*'s flags.
- The upper bounds are descriptive and approximate, and they understate: their development coverage near δ is 0.78 at 39 units and 0.87 at 150 (plan §0), and in the X3 simulation at Argoverse 2's cell sizes their simultaneous coverage at δ was 0.376–0.547 (S6.4).
- U_max is the largest upper bound in a population.

| Tracker | Population | Evaluable cells | Estimates above δ | Largest estimate (cell) | Largest LB | U_max (cell) |
|---|---|---|---|---|---|---|
| T1 | P_rel | 27 | 9 | 0.071 (large long turning) | 0.042 | 0.127 (large long turning) |
| T1 | P_near | 16 | 3 | 0.072 (pedestrian lat straight) | 0.019 | 0.118 (pedestrian lat straight) |
| T1 | P_ip | 8 | 1 | 0.073 (car lat straight) | 0.016 | 0.129 (car lat straight) |
| T3 | P_rel | 27 | 10 | 0.063 (car lat straight) | 0.041 | 0.122 (large long turning) |
| T3 | P_near | 16 | 2 | 0.063 (pedestrian lat turning) | 0.018 | 0.110 (large lat straight) |
| T3 | P_ip | 8 | 3 | 0.099 (car lat straight) | 0.023 | 0.157 (car lat straight) |

Sources:
- estimates and lower bounds: `[CSV: k8_within_lt3d_t1/t3_decide_cells.csv, arm Mstar, evaluable True: E, lb_sim]`;
- U_max: `[C1D: Mstar_simultaneous_upper_bounds.by_route.within_lt3d.t*.<population>.max_ub, max_cell]`;
- check: `ub_sim` equals the decision's cell upper bounds to 10⁻¹² `[the assertion at make_c1_figs_v01.py l. 142; recomputed by V05_NUMBER_TRACE_v01 U3: 102 cells, largest difference 0]`.

- **Point estimates above δ.** They occur in 9 of 27, 3 of 16 and 1 of 8 cells (T1) and in 10 of 27, 2 of 16 and 3 of 8 cells (T3), and none is flagged `[CSV: k8_within_lt3d_t*_decide_cells.csv]`.
- **The largest point estimate.** It is 0.099, in T3's in-path car lateral straight cell. Its simultaneous band is [0.023, 0.157] `[CSV: k8_within_lt3d_t3_decide_cells.csv, PD_inpath, car|lat|straight]`.
- **What the bounds allow.** Per-cell exceedances up to the U_max values cannot be excluded, and studentized bounds raise the largest to 0.1556–0.1621 (T1) and 0.1622–0.1894 (T3) (S6.4). No equivalence bound is claimed for any cell.

Main-text Fig. 2 shows these cells.

### S4(d) Per arm (main-text Table 4 and Fig. 3) and the per-decision reading

The per-arm table is main-text Table 4 (Section V-D6); its sources are `CSV: k8_within_lt3d_t*_decide_{validity,arms,v2,safety,cal_relied}.csv`.

- **Pooled exceedances.** Among the arms of record, every comparator infeasible in fewer than half of decisions was shown above δ on both trackers: B0, B4, B6 and RETUNED on T1, and B4 and B6 on T3 `[CSV: arms.csv; C1D: hypotheses.H1.by_tracker.*.removed_shown_above]`. This holds for the arms of record only: the exploratory B8 (stratified variance matching, S6.6) passes the screen at infeasible rates of 0.282 (T1) and 0.507 (T3).
- **The raw covariance (B0) is wider than M\* on both trackers.** Its pooled P_rel exceedance is 0.034 (T1) and 0.004 (T3), and its mean margins are 1.47 / 2.32 m and 5.44 / 6.66 m, against M\*'s 0.57 / 1.22 m and 0.65 / 1.93 m (descriptive; each arm is scored on its own relied records, so the record sets differ by arm) `[CSV: validity.csv; cal_relied.csv]`.
- **V2_viol** is reported in the table; no ordering of arms is drawn from it.
- **Per decision is not per constraint** (descriptive).
  - **V2 on Argoverse 2.** V2 counts only decisions with at least one scored P_rel record and is the mean over logs of each log's share of such decisions with some relied constraint exceeded. For M\*, V2 is 0.491 [0.466, 0.515] (T1) and 0.496 [0.472, 0.521] (T3) `[CSV: k8_within_lt3d_t*_decide_v2.csv, PD7_primary, Mstar, V2: E, ci95_lo, ci95_hi]`.
  - **Its reference.** A decision holds 13.07 tracks on average, and the per-track reference 1 − 0.95^{n_tracks} is 0.441 on both trackers. V2 is therefore 0.049 [0.031, 0.068] (T1) and 0.055 [0.037, 0.073] (T3) above it `[C1A: k8.within_lt3d.t*.V2.PD7_primary.Mstar.V2: mean_tracks_per_decision, reference_E, E_minus_reference, E_minus_reference_ci95]`.
  - **On development** (S2.2), V2 was 0.358 and 0.351 against a reference of 0.308 at 8.35 (T1) and 8.34 (T3) tracks per decision, an excess of 0.050 and 0.043.
  - **The reading.** V2 rose because decisions hold more tracks, and with them the reference. The excess over the reference is about 0.05 on both data sets.
  - **What it means.** About one decision in two keeps some relied constraint exceeded over V2's four steps.

Main-text Fig. 3 shows the infeasible-decision rates.

### S4(e) Every claim's status (S4-Table 4, S4-Table 5)

**S4-Table 4. Claim statuses.**
- **Family S** = {H2, H3, H4, H6b, H10} is tested by Holm at 0.025, gated on H1. Each p-value is (k + 1)/(B + 1), and the p-value decides. The bound at the Holm-assigned level is reported beside it.
- **H6a and H7** are secondary no-flag statements.
- **H8** is family P, at its own 0.025.
- **E1-AV2 and E2-AV2** are the method stage's E1 and E2 designs (S1.4) run on Argoverse 2.

| Claim | Label | p | Holm level | Status | Bound at the Holm level (or what decides) |
|---|---|---|---|---|---|
| H1 | primary | – | – | holds | the bounds (S4-Table 1) |
| H2 | family S | 2.5 × 10⁻⁵ | 0.005 | confirmed | UB^0.995(M\* − B4): 0.011 (T1), −0.049 (T3); margin 0.03 |
| H6b | family S | 0.0199 | 0.00625 | not confirmed | not available (the method stage records p-values only) |
| H10 | family S | 0.172 | 0.00833 | not confirmed | NI UB^0.99167(M\* − B6): 0.043 (T1), 0.029 (T3); margin 0.03 |
| H3 | family S | 1.000 | 0.0125 | not confirmed | T1: UB(M\*Jx − B3) −0.090 at 0.99375; T3: UB(M\*Jx − B0) +0.057, UB(M\*Jx − B3) −0.027 at 0.996875 |
| H4 | family S | 1.000 | 0.025 | not confirmed (the decision's "validity gate failed") | T1: −0.722 (B3); T3: −0.583 (B0), −0.609 (B3); M\*'s screen fails on both trackers |
| H6a | secondary (no flag) | – | – | holds | the method-stage rule flagged in no E1-AV2 cell |
| H7 | secondary (no flag) | – | – | does not hold | a cell and the pooled E2-AV2 cell shown above δ |
| H8 | family P (0.025) | – | – | holds | the 20–40 m lateral cell fails both versions |

Sources:
- p, Holm level and status: `[C1D: family_S.<claim>.p, holm_level, confirmed, label]`;
- bounds: `[C1D: S_decision_forms.by_claim.<claim>.bound_at_holm_level]`;
- H6a, H7 and H8: `[C1D: hypotheses.H6a, .H7, .H8]`.

- **Holm's sequence.** Holm confirms H2 at 0.005. It stops at its second step: H6b's p of 0.0199 is above 0.00625. H10, H3 and H4 are therefore not confirmed, whatever their p-values, and each also fails its own level (p 0.172, 1.000 and 1.000 against 0.00833, 0.0125 and 0.025) `[C1D: family_S]`.
- **H2: the price against B4, at most 0.03 (Form C).**
  - **T1.** M\* − B4 = −0.016, with UB^0.975 = 0.005 `[C1D: hypotheses.H2.by_tracker.t1.mean_diff, ub]`.
  - **T3.** −0.069, with UB −0.054 `[C1D: hypotheses.H2.by_tracker.t3]`.
  - **What it bounds.** H2 bounds a price, not superiority. On T1, M\* was not shown less often infeasible than B4: the 95 % interval is [−0.036, +0.005] `[CSV: k8_within_lt3d_t1_decide_paired.csv, infeasible_rate B4 vs Mstar]`.
- **H6b: a practitioner failure of B4 in the method stage.** The test asks for an E1-AV2 cell where the method-stage rule on the in-path audit items is not flagged, B4 is flagged and the paired difference, B4 minus that rule, is positive.
  - **The cells.** Such a cell exists on both trackers: car, < 20 m, lateral, turning (T1), and car, 20–40 m, longitudinal, straight (T3). Each has p = 0.0199 `[C1D: hypotheses.H6a.by_tracker.t1/t3.B4_failing_cells, H6b_p]`.
  - **The resolution.** That p is k + 1 = 4 over 201 refit replicates. At its Holm level of 0.00625, only k = 0 could have passed (plan §6.6) `[C1D: hypotheses.H6a.by_tracker.*.H6b_method_stage_k_over_refit_B = 0.015, H6b_refit_B = 200]`.
- **H10: the course-change strata, M\* against B6.**
  - **The cell part held on both trackers.** B6 was flagged at 0.975 in cells where M\* was not flagged, with a positive paired lower bound: 7 cells (T1) and 6 cells (T3) `[C1D: hypotheses.H10.by_tracker.t1/t3.cell_part, cells_failing_B6]`.
  - **The non-inferiority part failed on T1.** M\* − B6 = +0.021, with UB^0.975 = 0.039 > 0.03 `[C1D: hypotheses.H10.by_tracker.t1.noninferiority]`.
  - **It held on T3.** +0.018, with UB 0.027 `[C1D: hypotheses.H10.by_tracker.t3.noninferiority]`.
  - **p = 0.172** (from T1's non-inferiority part) `[C1D: family_S.H10.p]`.
- **H3: the trajectory-level M\*Jx.**
  - **Its joint loss was not shown above δ on either tracker** `[C1D: hypotheses.H3.by_tracker.t1/t3.validJ_method]`.
  - **On T1** it was less often infeasible than B3: UB −0.092 at 0.9875.
  - **On T3** B0 stays in V^J, because it fails only the pooled upper bound `[the authors' decision record]`. M\*Jx was more often infeasible than B0: +0.040, with UB +0.055 at 0.99375. So p = 1 `[C1D: hypotheses.H3.by_tracker.t3.vs.B0, comparator_reasons.B0; .t1.vs.B3]`.
- **H4: transfer in the loop.** H4 is H1's formula with every fitted arm (M\* and every fitted comparator) taken from the all-850-scene nuScenes fit. With nuScenes thresholds, M\* was shown above δ on both trackers.
  - **T1.** The P_rel cells car longitudinal new and large longitudinal static (cells and family cells) and the P_near cell large longitudinal static were flagged. The P_ip pooled cell was flagged too (E 0.070, LB 0.057) and fails HK1c (UB 0.089 > 0.08).
  - **T3.** The P_rel cells car longitudinal new and large longitudinal static, straight and new were flagged, with three of them in the family. The P_ip family cell car longitudinal new and the P_ip pooled cell were flagged (E 0.070, LB 0.057; HK1c UB 0.089).
  - **The result.** p = 1, although its Form B bounds are negative `[C1A: c1.transfer_lt3d.t1/t3.status.Mstar.pops; k8.transfer_lt3d.t*.validity_by_arm.Mstar.pops.PD_inpath.pooled; C1D: hypotheses.H4]`.
- **H6a holds.** The method-stage rule on the in-path audit items, fitted within Argoverse 2, is flagged in no E1-AV2 cell on either tracker `[C1D: hypotheses.H6a.by_tracker.t1/t3.Mstar_flagged_cells = []]`.
- **H7 does not hold.** The method-stage rule on the in-path audit items, fitted on the 700 nuScenes training scenes, is shown above δ on Argoverse 2 on both trackers.
  - **The flagged cell.** Car, all ranges, longitudinal, straight: E 0.174 (LB 0.106) on T1 and 0.159 (LB 0.101) on T3 `[MST: mstage_t1/t3.json, E2.cells.methods.Mstar.cells."car|all ranges|long|straight".E_scene, lb_sim]`.
  - **The pooled E2-AV2 cell.** E 0.123 (LB 0.098) and 0.116 (LB 0.095) `[MST: mstage_t*.json, E2.hypotheses.pooled_E, pooled_lb; C1D: hypotheses.H7.by_tracker.*.pooled_lb]`.
- **Transfer.** The nuScenes-fitted rule was supported in neither secondary test: H4 is not confirmed and H7 does not hold `[C1D: claims_status.H4, .H7]`.
- **H8 holds: the diagnosis of Section V-B replicated on Argoverse 2** (T1, B0, in-path cars, 2 s).
  - **The 20–40 m lateral cell fails both versions.** The primary exceedance is 0.214 [0.122, 0.306] against E⁰ = 0.090. The truth-oriented exceedance is 0.144 [0.068, 0.220] against δ.
  - **The < 20 m lateral cell** fails the primary version (0.147 [0.093, 0.201] against E⁰ = 0.082) but is consistent in the truth-oriented one (0.088 [0.046, 0.130]) `[C1D: hypotheses.H8.cells; E0_check.recomputed]`.
  - **Cells outside H8's definition** (H8 is defined on the lateral cells; descriptive). The longitudinal cells give 0.037 [0.022, 0.052] (< 20 m) and 0.158 [0.106, 0.210] (20–40 m, failing both versions) `[C1D: hypotheses.H8.cells."car|<20|long", ."car|20-40|long"]`.

**S4-Table 5. H8's cells: T1, raw covariance (B0), in-path cars, 2 s.**

| H8 cell (T1, B0, 2 s) | Primary: E [band] vs threshold | Truth-oriented: E [band] vs δ | Items / logs (primary) |
|---|---|---|---|
| car < 20 m lateral | 0.147 [0.093, 0.201] vs 0.082: FAILS | 0.088 [0.046, 0.130]: consistent | 1,694 / 263 |
| car 20–40 m lateral | 0.214 [0.122, 0.306] vs 0.090: FAILS | 0.144 [0.068, 0.220]: FAILS | 588 / 143 |
| car < 20 m longitudinal (descriptive) | 0.037 [0.022, 0.052] vs 0.05: consistent | 0.024 [0.013, 0.036]: over-covers | 4,681 / 328 |
| car 20–40 m longitudinal (descriptive) | 0.158 [0.106, 0.210] vs 0.05: FAILS | 0.154 [0.103, 0.206]: FAILS | 2,813 / 247 |

The bands are two-sided 95 % sup-t over the 4 decision cells `[C1D: hypotheses.H8.cells.*.primary/truth_oriented: E_rec, lo, hi, threshold, n, scenes]`.

### S4(f) Descriptive results

Every item below is descriptive. None is a claim, and none is support for M\*.
- **AB3DMOT** (third tracker, same 375 logs).
  - **The screen is not met.** M\*'s pooled P_rel cell is shown above δ: E 0.061, with pointwise lower bound 0.057 `[CSV: k8_within_lt3d_tab_decide_validity.csv, Mstar PD7_primary pooled_E, pooled_lb]`.
  - **Form B is not met.** M\* is infeasible in 0.891 of decisions `[C1D: descriptive_trackers.routes.within_lt3d.tab.Mstar_valid = false, form_b.met = false; CSV: k8_within_lt3d_tab_decide_arms.csv]`. The exploratory diagnosis is in S6.9 and S6.21.
- **H9: Trajectron++ `int_ee` with DP-SCRC in history-length strata, on the in-path relied items at 2 s.**
  - **The cells.** No cell and no pooled cell is flagged on either tracker. The pooled exceedance is 0.039 (T1; 4,810 items, 324 logs) and 0.036 (T3; 4,621 items, 321 logs) `[C1D: hypotheses.H9.by_tracker.t1/t3: flagged, pooled_flagged, exceed_share, items, logs]`.
  - **The floor is not met**, as the registered projection predicted: 2 power-qualified E2 cells against 6 on both trackers `[C1D: H9_floor.by_tracker]`. No confirmatory claim is made about a learned predictor.
  - **The seed-robustness label.** The decision records "not seed-robust" `[C1D: hypotheses.H9_seed_robustness.label_value]`. Under each of the three forward-pass seeds, H9's formula is false: no cell is flagged and the E2 family has 2 cells. By the plan's wording ("the same descriptive pattern under all three seeds") `[the authors' decision record]` this pattern is seed-robust; the frozen code's label requires H9 to hold under all three seeds. The label decides nothing `[H9T: h9_t1/t3.json, arms.TPP*, PD.HL]`.
  - **H9-noHL** (no history-length strata). No flag; family 2; pooled exceedance 0.038 (T1) and 0.035 (T3) `[H9T: h9_t*.json, arms.TPP.PD.noHL]`.
  - **TPPgt** (ground-truth histories). No flag; E2 family 2; pooled exceedance 0.038 (T1) and 0.031 (T3) `[H9T: h9_t*.json, arms.TPPgt.PD.HL]`.
  - **H9-T** (the nuScenes-fitted Trajectron++ transfer) is not in the decision of record.
- **H1-P** (public LT3D detector, 150 validation logs).
  - **No M\* cell is shown above δ, but the screen is not met.** The P_near floor fails, with 3 power-qualified cells against 6 on both trackers.
  - **Form B is not met** `[C1A: c1.public_lt3d_val.t1/t3.status.Mstar.pops.SD1_7_gap_le_5m.family_size, Floor; C1D: hypotheses.H1-P]`.
- **H5** (public VoxelNeXt detector, 150 validation logs).
  - **The same pattern.** No M\* cell is shown above δ, but the P_near floor fails: 1 cell (T1) and 2 cells (T3) against 6.
  - **Form B is not met** `[C1A: c1.voxelnext_val.t*.status.Mstar; C1D: hypotheses.H5]`.
- **Source transfer** (fit on the 225 held-out training logs, applied to the 150 validation logs).
  - **The same pattern.** No M\* cell is shown above δ, but the P_near floor fails: 3 cells against 6 on both trackers.
  - **Form B is not met** `[C1A: c1.source_transfer.t*.status.Mstar; C1D: hypotheses.source_transfer]`.
  - **By source, within the primary route,** M\*'s infeasible rate is 0.196 (held-out) against 0.172 (validation) on T1, a difference of +0.023 [−0.014, +0.061]. On T3 it is 0.255 against 0.235, +0.020 [−0.024, +0.063].
  - **Its pooled P_rel exceedance** differs by +0.005 [−0.002, +0.011] on both trackers `[C1A: c1.within_lt3d.t1/t3.source_heterogeneity]`.
- **Form A** (M\* against B0, B1, B4 and B9 at 0.99375).
  - **Not met on T1.** Against B4 the upper bound is +0.010 `[C1D: hypotheses.FormA.by_tracker.t1.vs.B4.ub]`.
  - **Met on T3** `[C1D: hypotheses.FormA.by_tracker.t3.met]`.
- **M\*J** (one scalar fitted on the joint loss).
  - **Its joint loss is not shown above δ.** Its P_rel joint exceedance (V2) is 0.047 on both trackers `[C1A: c1.within_lt3d.t*.joint_status.MstarJ.pops.PD7_primary.E]`.
  - **The price.** It is infeasible in 0.823 (T1) and 0.862 (T3) of decisions, against M\*'s 0.186 and 0.247 `[C1A: c1.within_lt3d.t*.infeasible_rate]`.
- **RETUNED-HK1 and the curve.**
  - **RETUNED-HK1** (cross-fitted on Form B's rule) found no qualifying point among the 21 in any fold, on T1 as on T3: its qualifying scale is "(none)" on both trackers. As the plan specified, the curve's end, a factor of 8 on B0, was substituted in every fold on both trackers.
  - **RETUNED-HK1's results.** On T1 it is not shown above δ and meets the screen, at an infeasible rate of 0.781. On T3 it is not shown above δ but does not meet the screen, at 0.977 `[C1A: c1.within_lt3d.t*.RETUNED_HK1.choice_by_fold, status; .infeasible_rate.RETUNED_HK1]`.
  - **RETUNED itself** (the pooled rule) took B0a1 and B0d0.02 by fold on T1, and B0a0.125, B0a0.25 and B0d0.3 on T3.
  - **The in-sample points meeting Form B's cell rule.** They are B0a4, B0a5 and B0a8 on T1, the cheapest infeasible in 0.660 of decisions, and B0a0.5 on T3, infeasible in 0.781 `[C1A: c1.within_lt3d.t*.RETUNED_E14]`.
- **Fallback shares.** The share of M\*'s records in fallback strata is 0.007, 0.008 and 0.075 on P_rel, P_near and P_ip for T1, and 0.006, 0.009 and 0.076 for T3 `[C1A: k8.within_lt3d.t*.A13_fallback_record_weighted.by_population.*.pooled.share]`.
- **Families at F_MIN 4 and 8.** M\*'s P_rel and P_near families meet the floor at F_MIN 4, 6 and 8 on both trackers. P_ip's 5 cells meet 4 but not 6 or 8; P_ip's registered floor is one evaluable cell `[C1D: Mstar_power_families.by_route.within_lt3d.t*.<population>.floor_at_F_MIN]`.
- **The AV2 pairing rate by score bin, how often v_max binds, and the share of relied constraints at 50–60 m.** None is in the decision of record.
- **Loop mode.** Not in the decision of record. The frozen configuration runs decision mode only (`"modes": ["decide"]` on every route), and the analysis has no loop-mode output `[40_PROTOCOL/C1_ANALYSIS_CONFIG_AV2_v01.json; C1A]`. No loop-mode result is reported. The plan lists loop mode among its descriptive outputs (§6.6, §7), but its frozen command list runs decision mode only (§8.5 requires `--mode decide`, because a loop run writes files of the same names), so no loop-mode output of record exists and none is reported here. A descriptive loop-mode replay added after review is in S6.18 (amendment A4).
- **Q1 (QCNet) was not tested,** for two reasons fixed before any outcome `[C1D: hypotheses.Q1.reasons, decided]`.
  - No C1 tracker index shares QCNet's history source.
  - The frozen coverage condition cannot hold: QCNet predicted 95.7 % of T1's records (88,182 of 92,166).

### S4(g) The separate re-derivation of the results

The re-derivation is a re-implementation within the project, written from the registered plan, the frozen configuration and a shared criteria library, which never opened the statistical functions of the analysis code. By the definition of S1.4 it is not independent `[R21]`.

- **The run-log check.** The log has 82 lines, and its hash chain is intact. Of 96 checks, none found a problem. The decision is the first completed analysis run, and its tables of record still hash as recorded `[R21: r21_runlog_check_r1.md]`.
- **No stop occurred,** so there was nothing to classify.
- **The re-derivation with separate code** (B = 40,000) `[R21: r21_rederive_r1.md]`.
  - **Exact reproduction.** It reproduced the analysis's bootstrap weights exactly: 480 bounds, largest difference 4.4 × 10⁻¹⁶ `[R21: r21_rederive_r1.json, exact_weight_reproduction.n_bounds]`.
  - **The comparisons.** Of the 108,109 comparisons, 108,059 agree, 0 disagree, 2 are Monte Carlo borderline and 48 are informational, where the analysis field is empty.
  - **H1.** It holds on both trackers with the same V_t, with and without zero-SE removals. H2, H3 and H4 have the decision's p-values.
- **The two borderline rows change no status** `[R21: r21_rederive_r1.json, borderline]`.
  - **T3, M\*'s P_near power family.** It has 8 cells in the analysis (2,000 datasets) and 9 in the review's check (500 datasets). The extra cell, pedestrian lateral turning, has power 0.783 in the analysis, just below 0.80 `[C1D: Mstar_power_families.by_route.within_lt3d.t3.SD1_7_gap_le_5m.per_cell]`. The floor of 6 holds either way, and no family cell is flagged.
  - **Transfer route, T1, B6, P_ip "shown above".** Neither computation has a cell or family flag, and both find that HK1c fails (UB 0.089) `[C1A: k8.transfer_lt3d.t1.validity_by_arm.B6.pops.PD_inpath]`. The difference is one of definition: the analysis's flag counts the HK1c failure, while plan §6.2's removal condition has no HK1c term. B6 leaves H4's comparison set through its P_rel flags in either reading, and H4 fails on M\*'s screen.
- **What the review does not re-derive.** It does not re-derive H6a, H6b, H7, H8, H9, H10 or Form A `[R21: r21_rederive_r1.json, top-level keys H1–H4]`.
- **Monte Carlo error and seed stability** (20 alternative seed sets, power fixed) `[R21: r21_mcse_fixed_r1.md/.json]`.
  - **Stability.** H1 holds in each of the 20 sets. V_t and V^J membership are identical in all 20, and so is every status of M\* on both trackers.
  - **Monte Carlo SE.** The empirical Monte Carlo SE across the 20 seed sets is at most 0.00032 for the Form B upper bounds and 0.00013 for HK1c's upper bounds; the A-B estimates are at most 0.0004 and 0.00017 `[R21: r21_mcse_fixed_r1.md; V05_NUMBER_TRACE_v01 §5]`.
- **The power rule redrawn in each of the 20 seed sets** `[R21: r21_mcse_recompute_r1.md; 90_DECISIONS/D19_GO_DECISION_v03.md §4]`.
  - H1 holds in 20 of 20 sets; V_t, V^J and every status of M\* are unchanged, and no power-family size of M\* changes.
  - Only some comparators' family sizes move, by ±1 cell (for example B0's P_near family on T1: 9 or 10), with no effect on V_t.

### S4(h) The trackers (S4-Table 6)

The tracker scores are in S4-Table 6. They were computed after the text lock and before the quarantine `[C1-PLAN §1.5]`; sources `[TRK: hota/AV2_C1_HOTA_{t1,t3,tab_kf}_pooled.json; metrics/AV2_C1_metrics_{t1,t3,tab_kf}_pooled.json]`. AB3DMOT outputs every detection above score 0.1 as a box, which lowers its AMOTA and MOTA; HOTA, with its tuned score threshold, is the fairer summary for it.

**S4-Table 6. Tracker scores on the 375 logs** (own detector, 2 Hz): HOTA [Luiten2021] at 50 m with the official Argoverse 2 evaluator, and AMOTA and MOTA under the nuScenes protocol.

| Tracker | Car HOTA / AMOTA / MOTA | Pedestrian | Bicycle |
|---|---|---|---|
| T1 (CANMOT) | 0.770 / 0.924 / 0.819 | 0.704 / 0.854 / 0.736 | 0.492 / 0.558 / 0.484 |
| T3 (Poly-MOT) | 0.775 / 0.924 / 0.819 | 0.702 / 0.851 / 0.731 | 0.490 / 0.570 / 0.500 |
| AB3DMOT | 0.554 / 0.295 / 0.390 | 0.502 / 0.299 / 0.364 | 0.286 / 0.000 / 0.000 |

AB3DMOT outputs every detection above score 0.1, which lowers its AMOTA and MOTA. `[TRK: 60_RESULTS/av2_trk/c1_375/{hota,metrics}/*_pooled.json]`

### S4(i)

Item (i) of the registered output list does not apply (GO).

### S4.1 Secondary claims in full

Section V-D reports H1, H2, H4, H8 and AB3DMOT in prose and lists every claim in main-text Table 5. This subsection gives the prose on the other claims; their statistics, sources and decision forms are in S4(e) and S4(f).

- **Holm's sequence.** Family S is tested by Holm at 0.025 after H1 holds. H2 is confirmed at 0.005. The sequence stops at its second step, H6b, whose p of 0.0199 is above its level of 0.00625. H10, H3 and H4 are therefore not confirmed whatever their p-values, and each also fails its own level (p 0.172, 1.000 and 1.000 against 0.00833, 0.0125 and 0.025).
- **H6b: a practitioner failure of B4 in the method stage.** It asks for a cell of the method-stage design run on Argoverse 2 (E1-AV2) in which B4 is flagged, the method-stage rule is not, and the paired difference is positive. Such a cell exists on both trackers, but the p-value comes from 200 refit replicates and has resolution 1/201, so it could pass its Holm level only with no exceedance at all, which was foreseeable at design time (Section VI-E).
- **H6a and H7: the method-stage rule on the in-path audit items.** These claims are not about M\*. They concern the method stage's rule (S1): the same per-stratum conformal risk control, fitted on the fixed in-path audit items rather than on the constraints the planner relies on.
  - **H6a holds.** Fitted within Argoverse 2, the rule is flagged in no E1-AV2 cell on either tracker.
  - **H7 does not hold.** Fitted on the 700 nuScenes training scenes, the rule is shown above δ on Argoverse 2 on both trackers: 0.174 (lower bound 0.106) on T1 and 0.159 (0.101) on T3 in the cell car, all ranges, longitudinal, straight, and 0.123 (0.098) and 0.116 (0.095) pooled. These are demonstrated under-coverages, about 2.5 times δ. The rule re-fitted on Argoverse 2 passed (H6a), but its nuScenes thresholds did not carry over, mostly in longitudinal cells. M\*'s own transfer test is H4 (Section V-D).
- **H10: the course-change strata, M\* against B6.** The cell part held on both trackers: B6 was flagged where M\* was not, with a positive paired lower bound, in 7 cells (T1) and 6 cells (T3). The non-inferiority part failed on T1: M\* − B6 = +0.021, with an upper bound of 0.039, above the 0.03 margin. It held on T3 (+0.018, upper bound 0.027). The p-value is 0.172.
- **H3: the trajectory-level M\*Jx.** Its joint loss was not shown above δ on either tracker. On T3, however, M\*Jx was more often infeasible than B0, which stays in the joint comparison set (+0.040, upper bound +0.055), so p = 1 and H3 is not confirmed. On development, a trajectory-level calibration cost 0.31–0.39 in infeasible-decision rate (Section V-C).
- **H9: a learned predictor (descriptive).** Trajectron++ (`int_ee`), calibrated by DP-SCRC in history-length strata on the in-path relied items at 2 s, is flagged in no cell and no pooled cell on either tracker, but its floor is not met (2 power-qualified cells against 6), as the registered projection predicted. No claim is made about a learned predictor.
- **Form A (descriptive).** M\* against B0, B1, B4 and B9: not met on T1, where the upper bound against B4 is +0.010; met on T3.
- **Not re-derived.** The separate re-derivation of the results (S4(g)), a re-implementation within the project, did not re-derive H6a, H6b, H7, H8, H9, H10 or Form A.

### What the verdict establishes

- **Per constraint.** The result is per relied constraint, not per decision: about one decision in two keeps some relied constraint exceeded (item (d)).
- **What δ is.** δ = 0.05 is a calibration level, not a safety target.
- **What the primary test re-fits.** It re-fits M\* within Argoverse 2. Transfer of the nuScenes-fitted rule is tested by H4 and H7. H4 is not confirmed (its screen failed), and H7 does not hold (item (e)).
- **Nothing beyond that.** Nothing is claimed per decision or about safety, and nothing for cells, methods or populations outside the registered screen.

---

## S5. The Argoverse 2 protocol: registration, blinding, events and mechanics

`[C1-PLAN = 40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md, SHA-256 0817e600…, §0, §1.1, §1.5, §8.2–§8.6, §9, §10, §11.3; FREEZE-RECORD = 40_PROTOCOL/C1_FREEZE_TIME_RECORD_v01.md; DEV-LOG = 40_PROTOCOL/C1_DEVIATION_LOG_v01.md; RL = 40_PROTOCOL/C1_RUN_LOG.txt, 8bc6235d…; the authors' decision record; E_prefreeze_v01 = 20_DESIGN/ms_v06_parts/E_prefreeze_v01.md, §E.7]`

S10, built from the same records, lists every computation made on the 375 test logs before the freeze (S10.3), groups them by what they read of the annotations (S10.4) and states who saw what (S10.5); Section VI-D of the main text summarizes it.

### S5.0 Terms used here

- **Plan §n:** section n of the frozen plan (S7).
- **Text lock:** the upload of the plan's text to a private OSF project, before the confirmation set's stage A.
- **Freeze:** the binding of the plan's files by hash, with the plan's own SHA-256 in a sidecar and a hash log.
- **Registration:** the frozen plan's registration on OSF under embargo.
- **Guarded entry point:** a C1 program that refuses to compute any Argoverse 2 outcome before the freeze, and any outcome after the decision time before the registration is recorded. Every guarded run appends a line to the hash-chained run log.
- **Deposit record:** the record, written after the registration and naming it, without which the entry points that read ground truth after the decision time refuse to run.
- **Stage A:** everything built before the freeze without any annotation position after a decision time (S5.3).
- **Stage B:** the scoring, which joins annotation positions after the decision time; it ran only after the registration.
- **D-1:** the one logged deviation (S5.6).
- **The analyst:** the role that ran the registered test (S10.5).

### S5.1 The registered file and the order of events

*The registered file.* The frozen plan keeps its drafting title line ("v07m (DRAFT)"); its frozen status is given by the hash log, the sidecar and the registration, not by that line.

*Order of events.* The list begins on 1 Nov, when processing of the 150 validation logs began `[E_prefreeze_v01 §E.3, E-Δ5]`.
- **From 1 Nov 2026, the 150 validation logs:** public-detector inference and AP, the first tracker ports with their tracking metrics, the counts that set the sample size, and the QCNet inputs (S10.3, P1–P5).
- **2–5 Nov, the 225 held-out logs:** they entered with the inference of our detector, trained on the other 475 training logs (S10.3, P6).
- **5 Nov.** The Argoverse 2 port ran its outcome-free 375-log builds: tracking, ego preparation, the prepared ground-truth file and the 2 s propagation (S10.3, P9).
- **6 Nov, the text lock (15:08:58 UTC).** The plan's text was locked and uploaded to a private OSF project (https://osf.io/eumj8/) before the confirmation set's stage A.
- **The freeze (20:08:13 UTC).** 354 bound files were hashed into the plan, the plan's own SHA-256 (0817e600…) went into a sidecar and hash log, and the bound test suite passed.
- **The registration (20:31 UTC)** under embargo (https://osf.io/v8qfk/). A deposit record naming the registration then unlocked the entry points that read ground truth after the decision time.

### S5.2 Port checks

`[TRK3 = 60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v03.md §2; EQ = 60_RESULTS/av2_trk/c1_375/equiv/; E_prefreeze_v01 E-Δ3]`

Before any 375-log output was kept, every data-preparation tool of the port was checked against its earlier output on the validation logs (S10.3, P7). The tracker input matched byte for byte after one documented substitution, the ego file after decompression (its gzip time stamps differ), and the HOTA tool within a relative 1e-12. Two tools were corrected in place on 5 Nov before that point, and one production worker started on the earlier version was stopped and its output discarded.

### S5.3 Stage A, stage B and the quarantine

`[PORT1 §7, §9; PORT3 §12.2; E0; FREEZE-RECORD §4; E_prefreeze_v01 E-Δ2, E-Δ4]`
- **Stage A** was built before the freeze without any annotation position after a decision time. It used tracker estimates, ego poses, annotation positions **at the decision time** (to pair tracks with objects within the 2 m gate), and the existence and lidar point count of later annotations. It kept the logged ego path after the decision time, and its counts evaluate the relied axis at the logged future ego pose (S10.3, P12–P13).
- **Stage B** joins ground-truth positions, after the registration only, reading the ground truth from the quarantine with a verified hash.
- **The quarantine.** An inventory tool with a content rule found 8 workspace files holding annotation geometry (3.57 GB). They went into 7 members, because two of them are byte-identical feathers, and all 8 plain copies were removed. The 8 include the detector-evaluation ground truth, the QCNet ground-truth history files and the detector's training-info archive, not only files derived for C1.
- **Checks.** Three scans found no copy outside the workspace. A provenance check re-made the stage-A inputs (ego, prepared ground truth, horizons) with the bound builders and matched their hashes; tracker exports were checked by producer hash.

### S5.4 What was seen before the freeze

`[C1-PLAN §10 items 2 and 10; FREEZE-RECORD §1, §5; E_prefreeze_v01 §E.2, §E.5, E-Δ1]`

The freeze-time record, which the freeze binds, lists what was seen. Seen before the freeze were:
- **On the 150 validation logs, from 1 Nov, with the public detectors:** detector AP; HOTA, AMOTA, MOTA and IDS of T1, T2, T3 and AB3DMOT, with HOTA's per-class score thresholds tuned on the validation annotations; the counts v01 and v02, which set the sample size; and the QCNet counts, integrity checks and coverage.
- **Before the text lock, on the 375 logs:** our detector's AP on the validation and held-out parts, the port's 375-log counts and the H9 power projection.
- **After the text lock:** the last lines of one job log, which print T1's per-class HOTA on the 150 validation logs with our detector; of the 24 Rule-0 metric files otherwise only their log counts and run times; the stage-A (S20a) counts, the S22 power file, the folds' composition, the scene map, the E⁰ values, the provenance record, the inventory and the quarantine manifest.

The job log read after the text lock was therefore not the first look at tracker scores on those logs. According to the records, no computation before the freeze used an annotation position after a decision time, and no Argoverse 2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error was computed or seen (S10.2). Whether the author saw any pre-freeze metric is not recorded (S10.5).

Before the freeze, on counts only, H9 was made descriptive and Q1 (QCNet) dropped.

### S5.5 The blinding claim, in the plan's words: procedural, not technical

The C1 entry points refuse to compute any Argoverse 2 outcome before the freeze, and any outcome after the decision time before the registration is recorded. Not technically barred were:
- the programs of the earlier nuScenes studies;
- the public annotation files of all 375 logs, which were on the analysis computer;
- the Argoverse 2 data tools, which can rebuild a prepared ground-truth file;
- copies outside the workspace.

The run log records only guarded runs. Tools outside the guarded entry points, such as the copy of the nuScenes thresholds, write no line. Re-running the frozen analysis reproduces every table, which shows that the tables are the frozen analysis's, not that no other analysis was run.

### S5.6 After the freeze: the logged events and deviation D-1

- **(1) The launcher.** Our launcher passed the command lines through a shell, which removed the backslashes of their Windows paths.
  - 12 processes stopped at their first path; two environment checks failed for the reason of (2).
  - No guard was reached, no input read and no output or run-log line written. Two empty temporary folders were removed.
  - The same commands then ran without a shell, with only the interpreter path made absolute (the same file). This is a launcher fix, not a change of any argument.
- **(2) Deviation D-1.** Two environment checks hand an interpreter path, given as an argument, to Windows' process start, which cannot resolve the printed forward-slash form. That one token was written with backslashes. It has no effect on any outcome.
- **(3) A missing output folder.** The tool that copies the nuScenes-fitted thresholds failed because its output folder did not exist. The folder was created and the tool rerun.
- **(4) Two transfer runs started by hand.** They used the same frozen commands, after (3), while the launcher finished its other lines.

No rule, input, seed or analysis changed.

### S5.7 The registered design in full

Main-text Section V-D gives the summary.

**1. Purpose and registration.** The nuScenes studies (Sections V-B and V-C; S1–S3) used one dataset, and K8 is exploratory. This study tests M\* once, on 375 Argoverse 2 logs, under a plan frozen on 6 Nov 2026 at 20:08:13 UTC and registered on OSF under embargo at 20:31 UTC (https://osf.io/v8qfk/), before any outcome existed.
- **Binding.** The plan binds 354 files by hash.
- **The guard.** Every entry point that reads ground truth after the decision time refuses to run without a deposit record naming the registration.
- **The run log.** Every guarded run is appended to a hash-chained log, published with the results.

Details are below `[C1-PLAN §8.2–§8.6, §11.3; the authors' decision record]`.

**What the primary test is.** M\* is re-fitted within Argoverse 2 by 5-fold cross-fitting, so for its own-threshold strata the marginal bound of Propositions 3–4 holds by theory (Section IV-G). The test checks what theory does not cover:
- the scored relied-axis subset;
- pooled and fallback cells;
- the risk averaged over the five cross-fitted fold rules;
- the power floors;
- how often the planner backs off its designed margin (the infeasible-decision rate) on new data.

**What H1 can fail on, and what lies outside it.**
- H1 can fail on a flag of M\* (powered at exceedances of about 0.15), a floor, HK1c, or a comparator not beaten.
- On development data its failures came mostly from HK1c on T1's P_ip cell. On T3 a GO also needs B6 to be shown above δ.
- Whether nuScenes thresholds transfer is tested by H4 and H7. Whether the diagnosis of Section V-B replicates is tested by H8.

**2. Data, detector and trackers.**
- **The logs.** 375 logs of the Argoverse 2 Sensor dataset [Argoverse2]: 225 training logs held out from the detector by a seeded permutation, and the 150 validation logs. An Argoverse 2 log is one segment of about 15 s, comparable to a nuScenes scene, so log-level exchangeability here is scene-level.
- **The detector.** CenterPoint [Yin2021] in the LT3D code base [Peri2022], trained by us on the other 475 training logs (2 CBGS epochs [Zhu2019cbgs]). The public checkpoint, trained on all 700, could not be used. Nothing was selected on the 375 logs.
  - Its 26-class AP at 50 m is 0.425 (validation) and 0.415 (held-out), against 0.469 for the public checkpoint.
  - Its bicyclist AP is 0.403, against 0.543.

  `[C1-PLAN §1.1, §1.2]`
- **The trackers.** T1 and T3 keep their nuScenes parameters and run at 2 Hz. AB3DMOT [Weng2020] is a descriptive third tracker. Their scores (HOTA [Luiten2021], AMOTA, MOTA), computed after the text lock, are in S4-Table 6.

**3. Procedurally blinded preparation** (Section VI-D) [KleinRoodman2005; MacCoun2015; Nosek2018].
- **Stage A.** Everything not needing an annotation position after the decision time was built before the freeze: states, items, counts, folds and H8's null E⁰. What stage A did use is in S5.3.
- **Stage B.** Scoring ran only after the registration.
- **The quarantine.** The 8 inventory files holding annotation geometry were quarantined, as 7 members, before the freeze (S5.3).
- **What was seen before the freeze:** S5.4 and S10. It is listed in a freeze-time record, which the freeze binds.

**4. Design.** The populations, decision mode and M\* are those of Section IV and S2.2, cross-fitted on 5 folds of 75 logs with exact rational CRC thresholds.
- **The comparators.** K = {B0, B1, B3, B4, B6, B9, RETUNED} was fixed on development and never changed. RETUNED is selected by the pooled rule.
- **Published methods.** B4 is the analogue of a per-time-step conformal inflation (CGKF [Weisman2026]) and of the single global factor that [Marques2026a] argue against and [Marques2026b] test as a baseline. B6 and M\* use fixed partitions where [Marques2026a] learn theirs.
- **Not in K:**
  - B5 and B7 (method-stage ablations);
  - a re-fitted process noise;
  - the published filters' own implementations.
- **What the comparisons can show.**
  - B3's margin is at least M\*'s on every item (S8-Proposition 9), so backing off its designed margin less often than B3 is no evidence of an advantage for M\*.
  - If the comparators not shown above δ are those of development ({B3} on T1; {B0, B3} on T3), Form B adds little to the screen `[C1-PLAN §2, §4]`.
- **Secondary claims:**
  - H2: the price against B4 is at most 0.03;
  - H3: the trajectory-level M\*Jx;
  - H4: the nuScenes-fitted rule in the loop;
  - H10: M\* against B6;
  - H6a, H6b and H7: the method stage's DP-SCRC on the audit population, within Argoverse 2 and with the nuScenes rule;
  - H8: the diagnosis on T1.
- **Descriptive results:**
  - AB3DMOT;
  - the public LT3D and VoxelNeXt [Chen2023voxelnext] detectors, on the validation logs;
  - a train-to-validation source transfer;
  - Trajectron++ with the nuScenes checkpoint, stratified by history length (H9).

  QCNet [Zhou2023qcnet] is not tested.

**5. Statistics and the GO rule** `[C1-PLAN §6.1–§6.5, §9]`.
- **Units.** The log is the unit of the estimand and the bootstrap (B = 40,000; p = (k + 1)/(B + 1)).
- **Evaluable and power-qualified cells.** A cell is evaluable with ≥ 39 logs. It is power-qualified if a planted exceedance of 0.15 (0.10 above δ) in that cell alone would be flagged with probability ≥ 0.80 (ρ = 0.5, 2,000 datasets [SennBretz2007]).
- **The registered screen.** M\* passes it on a tracker if, in each of P_rel, P_near and P_ip:
  - **no flag:** no cell or power-family cell is flagged by a one-sided simultaneous 0.95 sup-t bound [MontielOlea2019], and the pooled cell is evaluable and not flagged by its pointwise 0.95 lower bound;
  - **the floors hold:** ≥ 6 power-qualified cells on P_rel and P_near, and ≥ 1 evaluable P_ip cell;
  - **HK1c holds:** the pooled upper bound at 0.995 is ≤ δ + 0.03.
    - The margin is our own value: the 98.4th percentile of the Beta(15, 286) law of split-conformal risk [Vovk2012; Angelopoulos2021].
    - The level was calibrated on development coverage by a rule fixed beforehand. The rule was ambiguous between the mean and the minimum over cells. The mean was applied; the minimum reading reaches the same 0.995 through the rule's fallback.
- **Removal from V_t.** A comparator leaves V_t only on familywise evidence above δ: any of 9 conditions, each at 1 − 0.0125/9, a plain Bonferroni split of 0.0125 over the nine conditions. A zero-SE cell above δ removes it outside this budget, and H1 is reported with and without such removals (S5.8).
- **Form B.** It holds if the screen holds and M\* is less often infeasible than every member of V_t: paired log-level upper bounds at 1 − 0.0125/|V_t| below 0. It is vacuous if V_t is empty.
- **H1 and GO.** H1 is Form B on T1 and T3, an intersection-union test [Berger1982] at one-sided 0.025 nominal.
  - HK1c enters by the maximum. Where its null holds, H1's actual error follows HK1c's: 0.012–0.033 on development population means, and about 0.05 in the worst cell. In the X3 simulation at Argoverse 2's cell sizes, HK1c's "99.5 %" bound covered 0.973–0.991 at δ under the record's rule (S6.4).
  - **GO** means that H1 holds with every input present and provenance-valid. Otherwise the outcome is NO-GO, with H1's failed conditions named.
- **Family S** = {H2, H3, H4, H6b, H10}, tested by Holm at 0.025 only if H1 holds [Holm1979; DmitrienkoTamhane2007]. Otherwise its members are reported as supportive, not confirmatory. H8 has its own 0.025. All confirmatory statements together are at most 0.05 nominal.
- **The verdict of record** is the first completed run of the frozen analysis. A run is not completed if it:
  - ends in power loss or a killed process;
  - records one of seven named memory or disk errors;
  - leaves one of its two outputs without the other.

**6. What the design can detect, and what a GO would mean.**
- **Power is a pre-data property.**
  - It licenses no "at most" statement. A cell at 0.10 can pass with probability near one minus its power at 0.10, which the decision reports per cell (power at 0.10, 0.12, 0.15 and 0.20, and MDE80).
  - At 0.12 the P_near floor fails on development data.
  - The post-data bounds are HK1c's (nominal 99.5 %, approximate) and M\*'s simultaneous cell bounds U_max. U_max is approximate and understates: its development coverage near δ is 0.78 at 39 units and 0.87 at 150, and in the X3 simulation at Argoverse 2's cell sizes its simultaneous coverage at δ was 0.376–0.547; studentized bounds give 0.1556–0.1894 (S6.4) `[C1-PLAN §0, §6.6, §6.9, §7]`.
- **Counts (pre-data).** The stage-A counts, made before any outcome, gave T1 537,924 relied items at the reference pose, with 27 P_rel cells, 18 P_near cells and 9 P_ip cells evaluable on those counts; T3 had 537,754 relied items, with 27, 18 and 9 `[S20a]`. Two-wheeler cells are mostly not evaluable. In the analysis, evaluability and the scored records are arm-specific: M\*'s evaluable cells were 27, 16 and 8 (S4-Table 1), and each arm is scored on the records it relied on under its own plan (on T1, 534,846 P_rel records for M\* and 356,260 for B3; S6-Table 1).
- **Planned chance of GO.** If M\* behaves as on nuScenes, H1 holds with probability 0.870 at 375 resampled development units (0.933 with M\*'s rates capped at δ). A projection from the public LT3D detector's counts on the 150 validation logs gives 0.88–0.97 `[C1-PLAN §7; S22]`.
- **What a GO would show, per tracker:**
  - no evaluable cell, family or pooled cell of M\* shown above δ, at the stated power;
  - the floors and HK1c met;
  - M\* less often infeasible than every comparator in K not shown above δ.
- **What a GO would not show:**
  - that every cell is at most δ;
  - transfer;
  - anything per decision;
  - safety;
  - superiority over methods outside K.

### S5.8 Protocol mechanics: removal budget, zero-SE cases, completion and the run log

These mechanics decide no claim by themselves; the main text reports only their outcome.

**The removal budget** `[C1-PLAN §6.2, §6.3; C1D: hypotheses.H1.by_tracker.*]`.
- A comparator of K leaves V_t only through a flag at one-sided 1 − 0.0125/9 = 0.99861 in any of 9 conditions: a cell, power-family cell or pooled-cell flag, in P_rel, P_near or P_ip. This is a plain Bonferroni split of 0.0125 over the nine conditions.
- Form B then compares M\* with each member of V_t at 1 − 0.0125/|V_t|: 0.9875 on T1, where V_t = {B3}, and 0.99375 on T3, where V_t = {B0, B3} (S4-Table 2).
- The analysis code's status also counts an HK1c failure as "shown above", while plan §6.2's nine conditions have no HK1c term. The two readings differ in one transfer-route row and decide nothing (S4(g)).
- In the X3 simulation at Argoverse 2's cell sizes, a comparator truly at δ in every cell was falsely removed in 0.000–0.003 of data sets under the record's rule, against the 0.0125 budget (S6.4).

**Zero-SE cases** `[C1D: zero_se_effects.by_route.within_lt3d; R21: r21_rederive_r1.md]`.
- *Rule.* A comparator cell above δ with a zero bootstrap SE removes the comparator outside the removal budget, and H1 is reported with and without such removals.
- *In r1.* On the primary route only T1's B3 had a zero-SE case, its P_ip family quantile. It raised no flag, did not remove B3 and left V_t unchanged; T3 and M\* had none. H1 is the same with and without zero-SE removals (S4(b)).

**Completion criteria** `[C1-PLAN §9; C1D; R21: r21_runlog_check_r1.md]`.
- *Rule.* The verdict of record is the first completed run of the frozen analysis. A run is not completed if it ends in power loss or a killed process, records one of seven named memory or disk errors, or leaves one of its two outputs without the other.
- *In r1.* None of the seven resource-error strings occurs in the decision, no route problem is recorded, and both outputs exist, so r1 is a completed run, not an environment stop. The reruns `_r2` to `_r4` were not needed (S4(a)).

**The run log** `[RL: lines 81–82; R21: r21_runlog_check_r1.md; X3_STATS_REPORT_v01 §1]`.
- Every guarded run appends a line to a hash-chained log, published with the results. The log has 82 lines, and its hash chain is intact.
- The frozen analysis (`c1_analyse_v10`, B = 40,000) has its start and done lines at lines 81 and 82 (7 Nov 2026, 10:33:58 and 12:22:43 UTC; run id ed69b9e4…). The done line records both outputs with their SHA-256.
- The run-log check of the separate re-derivation (S4(g)) made 96 checks and found no problem, and no start line without its done line.
- The run log kept its SHA-256 (8bc6235d…) at every X3 integrity check (S6.0).

---

## S6. Post-registration exploratory analyses (X3): full results

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).**

`[X3 plan = 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md, SHA-256 38e2526d…; A1 = 20_DESIGN/X3_PLAN_AMENDMENT_A1_v01.md, a5cc3261…; A2 = 20_DESIGN/X3_PLAN_AMENDMENT_A2_v01.md, b50779e0…; A3 = 20_DESIGN/X3_PLAN_AMENDMENT_A3_v01.md, 009a0aad…; A4 = 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md, ab19dd66…; A5 = 20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md, 25f3bb65…; outputs 60_RESULTS/x3_explore_v01/; reports 70_TESTS/X3_INTEGRITY_v01/: X3_CORE_REPORT_v01 (7b09316b…), X3_CORE_REPORT_R2_v01 (396ec44d…), X3_REF_REPORT_v01 (c63df848…), X3_STATS_REPORT_v01 (8237cc93…)]`

Section V-E gives the main results. Here each analysis has a short paragraph with its plan reference and its main table, copied from its result file; the remaining pre-specified outputs are in the named result files, which are released with the code.

**Status.** Everything in S6 is post-registration and exploratory. The X3 plan and its five amendments A1–A5 were hash-locked by the project itself, in SHA-256 sidecars with no third-party timestamp, after the verdict of record and after the registered outputs had been read; each was locked before its own outputs were computed. These self-recorded locks are not a registration. No family-wise error control is applied across the analyses of S6, nor across the 21 partition families per tracker within (b). Nothing in S6 changes the verdict of record, a claim status or a table of record. The results of amendments A3, A4 and A5 (S6.12–S6.22) carry the label "added after review (amendment A3)", "(amendment A4)" or "(amendment A5)"; a quantity that neither the plan nor an amendment specifies is marked *added*.

### S6.0 What X3 is, and its integrity

- **The plan.** It was written and hash-locked after the verdict of record and before any X3 output existed (as recorded in the authors' decision record). Each analysis answers a concern raised in an internal review of an earlier version of the manuscript. Amendment A1 (11:18 EST) and amendment A2 (12:51 EST) were each hash-locked before any of their own outputs. A2 was written after seeing only the training-fold q table, before any run, screen or infeasibility of a Q-refit arm. Amendments A3 (15:09 EST) and A4 (15:11 EST), written after a second internal review, are described in S6.12, and amendment A5 (18:21 EST), written after a third internal review, in S6.22.
- **Common rules** (plan §0). The 375 logs, with the frozen stage-B caches, folds, items and fits of record; the route of H1 (`within_lt3d`); decision mode only; frozen modules imported read-only and never run as entry points. The bootstrap is a log-cluster bootstrap with B = 4000 (40,000 of record). Seeds are [20261201, i, j] (bootstrap) and [20261202, i, j] (power), with i = 0, 1, 2 for T1, T3 and AB3DMOT and j the analysis index. "Passes the screen" means Valid by the registered screen as coded. Arms outside K are judged like RETUNED-HK1 of record: flags at 0.95, 500 power datasets.
- **Integrity.** The run log `40_PROTOCOL/C1_RUN_LOG.txt` kept its SHA-256 (8bc6235d…) at every check, and every file of `60_RESULTS/c1_av2_v01/` re-hashed identical to the baseline manifest before and after every X3 step. No guarded entry point was run. Nothing in X3 changes the verdict of record, a claim status or a table of record.
- **Process notes.** One helper of the process that built the reference inputs, the progress-line function of `x3_ref_common_v01`, was edited while a run was in progress (progress line only), so the d0 T3 summary records a later code hash than the code it ran; no computation changed. Two of the X3 processes were stopped by hand while they were waiting for the shared compute lock, before they had written anything.
- **Reading the tables.** Failing conditions use the code's names: NoFlag (some cell is flagged), FamFlag (a power-family cell is flagged), NoFlag_pool (the pooled cell is flagged), HK1c (the pooled upper bound is above 0.08) and Floor (too few power-qualified or evaluable cells). Status words: "valid" passes the screen, "shown above" is flagged, "floor only" fails only a floor. Numbers are copied from the result files at their printed precision, with the minus sign as printed there.

### S6.1 The validation gates V0–V2 (plan §1)

`[gates/x3_gates_v01.md; X3_CORE_REPORT_v01]`

- **V0, the runner.** The X3 runner, run on the fits of record, reproduced the runs of record exactly for M\*, B0, B4, B6 and B9 on T1 and T3 (decisions, counts, calibration tables and episode summaries); B1, B3 and AB3DMOT's M\* were compared the same way and are equal too.
- **V2, the partitions.** The partition-tagged counts of analysis (b), summed over the bins, equal the counts of record per arm, population and log; inside the runs, 78,484 per-call checks on each of T1 and T3 and 11,180 on AB3DMOT found no failure. The last column of S6-Table 1 is the number of scored P_rel records per arm: each arm is scored on the records it relied on under its own plan, so the scored sets differ by arm (Section IV-A).
- **V1, the screen.** At B = 4000 the X3 screen gives the status of record (B = 40,000) for 98 of 99 arm statuses: 32 of 33 on T1, 33 of 33 on T3 and 33 of 33 on AB3DMOT. The exception is T1's sweep point B0a4, whose in-path car lateral turning cell X3 flags (LB − δ = 0.00116, 0.92 Monte Carlo SE) and the record does not. RETUNED-HK1's selection, re-run at B = 4000, reproduces the record's per-fold choice (B0a8 in every fold), and the infeasible rates recomputed from the outputs of record equal the record's.

**S6-Table 1. Gates V0 and V2, per tracker and arm.**

| Tracker | Arm | V0: decisions | V0: counts | V0: cal | V0: episode summaries | V0: equal | V2: partitions × populations × logs equal | V2: scored P_rel records |
|---|---|---|---|---|---|---|---|---|
| T1 | M\* | True (11288 rows) | True (106587 rows) | True | True | True | True | 534846 |
| T1 | B0 | True (11288 rows) | True (106537 rows) | True | True | True | True | 527372 |
| T1 | B4 | True (11288 rows) | True (106068 rows) | True | True | True | True | 533554 |
| T1 | B6 | True (11288 rows) | True (105904 rows) | True | True | True | True | 534861 |
| T1 | B9 | True (11288 rows) | True (109952 rows) | True | True | True | True | 497127 |
| T1 | B1 | True (11288 rows) | True (108970 rows) | True | True | True | True | 512072 |
| T1 | B3 | True (11288 rows) | True (109948 rows) | True | True | True | True | 356260 |
| T3 | M\* | True (11288 rows) | True (108294 rows) | True | True | True | True | 533331 |
| T3 | B0 | True (11288 rows) | True (119567 rows) | True | True | True | True | 472380 |
| T3 | B4 | True (11288 rows) | True (107763 rows) | True | True | True | True | 531363 |
| T3 | B6 | True (11288 rows) | True (106973 rows) | True | True | True | True | 534025 |
| T3 | B9 | True (11288 rows) | True (108465 rows) | True | True | True | True | 501968 |
| T3 | B1 | True (11288 rows) | True (113007 rows) | True | True | True | True | 503289 |
| T3 | B3 | True (11288 rows) | True (123985 rows) | True | True | True | True | 413292 |
| AB3DMOT | M\* | True (11288 rows) | True (118840 rows) | True | True | True | True | 524152 |

### S6.2 (a) Back-off at matched validity (plan §2(a))

`[a_matched/x3_a_matched_v01.md]`

B4, B6 (split by in-path, as of record) and B9 were refitted by the frozen fit rule at each δ′ in {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005, 0.0025, 0.001}, cross-fitted on the folds of record. Each held-out fold uses the least conservative level that passes the screen on the other four folds; if none does, the most conservative fittable level is used and flagged. The levels 0.0025 and 0.001 are not fittable: a training split has 300 logs, and they need 399 and 999. The B0 family is RETUNED-HK1 of record, reported from the record: it found no qualifying scale in any fold on either tracker ("(none)" on T1 as on T3), and ×8, the curve's end, was substituted in every fold as the plan specified. Of the refitted families only B6's composite passes, infeasible in 0.6226 (T1) and 0.4862 (T3) of decisions against M\*'s 0.1864 and 0.2466; the B0 family's substituted composite passes on T1 at 0.7810 and not on T3, at 0.9770. Over all 375 logs (in sample), B4 passes at δ′ = 0.01 on T1 (infeasible 0.6951) and at no level on T3; B6 at 0.01 on T1 (0.6784) and at 0.015 and 0.01 on T3 (0.4862 and 0.6246); B9 at 0.02 (0.8216 and 0.8174). The whole curves are in the result file.

**S6-Table 2. Matched-validity composites** (cross-fitted; status by the registered screen; infeasible-decision rate; M\* − composite, paired, 95 % percentile log-bootstrap interval).

| Tracker | Family | Per-fold choice (folds 0–4) | Folds where none qualifies | Composite Valid | Composite shown above | Composite infeasible | M\* − composite (95 % CI) |
|---|---|---|---|---|---|---|---|
| T1 | M\* (of record) | – | – | True | False | 0.1864 | – |
| T1 | B4 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.9106 | -0.7243 [-0.7446, -0.7032] |
| T1 | B6 | 0.015, 0.005, 0.015, 0.015, 0.015 | 1 | True | False | 0.6226 | -0.4362 [-0.4634, -0.4098] |
| T1 | B9 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.9724 | -0.7860 [-0.8047, -0.7670] |
| T1 | B0 (RETUNED-HK1 of record) | B0a8, B0a8, B0a8, B0a8, B0a8 | 0, 1, 2, 3, 4 | True | False | 0.7810 | -0.5946 [-0.6187, -0.5704] |
| T3 | M\* (of record) | – | – | True | False | 0.2466 | – |
| T3 | B4 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.8647 | -0.6181 [-0.6408, -0.5954] |
| T3 | B6 | 0.015, 0.015, 0.015, 0.015, 0.015 | none | True | False | 0.4862 | -0.2396 [-0.2559, -0.2237] |
| T3 | B9 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.9715 | -0.7249 [-0.7461, -0.7037] |
| T3 | B0 (RETUNED-HK1 of record) | B0a8, B0a8, B0a8, B0a8, B0a8 | 0, 1, 2, 3, 4 | False | False | 0.9770 | -0.7303 [-0.7513, -0.7091] |

**Reading S6-Table 2 with amendment A4's reporting** (S6.17). A4 asks that the registered-screen version of (a) separate "flagged" from "fails a floor only" and give no contrast for a composite that does not pass. The composites of B4 and B9 (both trackers) and of B0 on T3 do not pass: B4 and B0 fail a floor only and B9 fails HK1c and a floor, so their M\* − composite intervals above are not comparisons at matched validity. The B0 composite on T1 passes only through the ×8 substituted in every fold, so main-text Section V-E(a) states that B0 has no matched point on either tracker; its in-sample registered-screen best points are ×4 on T1 (infeasible 0.660) and ×0.5 on T3 (0.781). On T1, B6 used the most conservative level (0.005) in fold 1, the one fold where no level qualified.

### S6.3 (b) The screen on partitions no method stratifies on directly (plan §2(b))

`[b_partitions/x3_b_partitions_v01.md]`

Seven partitions with bins fixed in the plan: P1 track speed, P2 track length, P3 track age, P4 detection score, P5 ego speed, P6 annotation lidar points at k + h, and P7 city (available for all 375 logs: MIA, PIT, WDC, DTW, ATX, PAO). P0, distance to the ego, is a partition M\*'s strata use and is reported for completeness. No method stratifies on P1–P7 directly, but track speed (P1) and track age (P3) are coarse functions of the variables that define M\*'s "static" and "new" course-change states (S6.22). Cells are bin × relied axis on P_rel, P_near and P_ip; a cell is evaluable with ≥ 39 logs and flagged when its one-sided simultaneous 0.95 sup-t lower bound over the partition's evaluable cells exceeds δ (B = 4000). M\* is flagged in 5 P_rel cells on each tracker over P1–P7, all in low-quality tracks (detection score 0.4–0.5 on both axes, track age 1–2, 1–10 annotation lidar points, on T3 also 11–50, and on T1 one slow-track cell), and in no P_near or P_ip cell. On T3 it is also flagged in two P0 distance cells. B4 is flagged in 22 (T1) and 24 (T3) and B6 in 13 and 14 P_rel cells over P1–P7. The result file also gives every arm's flagged cells per population, the largest cell estimate with its simultaneous upper bound, every M\* cell with an estimate above δ, and M\* on AB3DMOT (descriptive). The partition screens of the matched arms of (a) and of B8, and the flags with the level corrected across the seven partitions, are in S6.14 (amendment A3); no family-wise control is applied across the 21 partition families per tracker.

**S6-Table 3. M\*'s flagged cells on the partitions** (T1 and T3; every flagged cell is in P_rel).

| Tracker | Partition | Population | Cell (bin, axis) | E | Simultaneous LB | Simultaneous UB | Logs |
|---|---|---|---|---|---|---|---|
| T1 | P1 track speed | P_rel | [0.5,3) long | 0.0818 | 0.0639 | 0.0974 | 365 |
| T1 | P3 track age | P_rel | 1-2 lat | 0.0655 | 0.0540 | 0.0752 | 374 |
| T1 | P4 detection score | P_rel | [0.4,0.5) lat | 0.0926 | 0.0736 | 0.1090 | 363 |
| T1 | P4 detection score | P_rel | [0.4,0.5) long | 0.0868 | 0.0723 | 0.0995 | 374 |
| T1 | P6 annotation lidar points | P_rel | 1-10 lat | 0.0715 | 0.0537 | 0.0870 | 343 |
| T3 | P0 distance | P_rel | 20-40 m lat | 0.0613 | 0.0510 | 0.0707 | 372 |
| T3 | P0 distance | P_rel | >=40 m lat | 0.0683 | 0.0500 | 0.0847 | 359 |
| T3 | P3 track age | P_rel | 1-2 lat | 0.0667 | 0.0574 | 0.0748 | 374 |
| T3 | P4 detection score | P_rel | [0.4,0.5) lat | 0.0878 | 0.0722 | 0.1012 | 362 |
| T3 | P4 detection score | P_rel | [0.4,0.5) long | 0.0780 | 0.0650 | 0.0892 | 374 |
| T3 | P6 annotation lidar points | P_rel | 1-10 lat | 0.0759 | 0.0538 | 0.0948 | 343 |
| T3 | P6 annotation lidar points | P_rel | 11-50 lat | 0.0695 | 0.0505 | 0.0858 | 369 |

**S6-Table 4. Flagged P_rel cells per arm and partition** (counted from the result file's per-arm lists of flagged cells).

| Tracker | Arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 | Sum P1–P7 |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | M\* | 0 | 1 | 0 | 1 | 2 | 0 | 1 | 0 | 5 |
| T1 | B0 | 0 | 4 | 1 | 1 | 1 | 0 | 0 | 0 | 7 |
| T1 | B1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| T1 | B3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T1 | B4 | 2 | 5 | 3 | 2 | 2 | 4 | 4 | 2 | 22 |
| T1 | B6 | 0 | 6 | 0 | 2 | 4 | 1 | 0 | 0 | 13 |
| T1 | B9 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T3 | M\* | 2 | 0 | 0 | 1 | 2 | 0 | 2 | 0 | 5 |
| T3 | B0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T3 | B1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 |
| T3 | B3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| T3 | B4 | 3 | 3 | 3 | 4 | 3 | 4 | 3 | 4 | 24 |
| T3 | B6 | 2 | 5 | 0 | 2 | 4 | 1 | 2 | 0 | 14 |
| T3 | B9 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 |

### S6.4 (c) Interval sensitivity, false removal and coverage (plan §2(c))

`[c_intervals/x3_c1_intervals_v01.md; x3_c2_simulation_v01.md; x3_c2_modelcheck_v01.md; X3_STATS_REPORT_v01]`

**(c1) Alternative intervals for the quantities that decided H1.** Method (i) is the record's bound (sup-t on the bootstrap SE); on the record's weights it reproduces the record to 3.11e-15 over 194 numeric checks on T1 and 5.33e-15 over 195 on T3. Method (ii) is a studentized log bootstrap with the SE floored at √(δ(1 − δ)/N_eff); method (iii) is a design-effect Wilson interval with the ANOVA intraclass correlation, Bonferroni over the record's sup-t sets. The variants are (i) and (ii) on X3's or the record's weights (i_x3, ii_x3 at B = 4000; i_rec, ii_rec at B = 40,000), and (iii) centered on the pooled x/n, a different estimand (iii_pooledcentre). Under (ii) no status changes: M\* stays valid, V_t is unchanged and H1 holds. M\*'s largest simultaneous upper bounds rise to 0.1556–0.1621 on T1 and 0.1622–0.1894 on T3 (ii_x3), and its largest HK1c bound to 0.0606 (T1, P_ip). Under (iii) M\* is flagged in T1 P_rel car lateral static (LB 0.0522) and T3 P_ip car lateral straight (LB 0.0521), so H1 would not be met; that method's size at δ is 0.180–0.333 per population (c2). No r1 removal is reversed by any method.

**S6-Table 5. (c1) M\*'s status, V_t and H1, with M\*'s HK1c bounds and largest cell bounds, per method.**

| Tracker | Method | Valid(M\*) | V_t | H1 | M\*'s HK1c UB at 0.995, P_rel / P_near / P_ip | M\*'s largest simultaneous 0.95 UB (cell), P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|
| T1 | i_rec | True | B3 | True | 0.0482 / 0.0473 / 0.0546 | 0.1268 (large long turning) / 0.1184 (pedestrian lat straight) / 0.1285 (car lat straight) |
| T1 | i_x3 | True | B3 | True | 0.0481 / 0.0468 / 0.0550 | 0.1269 (large long turning) / 0.1183 (pedestrian lat straight) / 0.1277 (car lat straight) |
| T1 | ii_x3 | True | B3 | True | 0.0485 / 0.0521 / 0.0606 | 0.1621 (large lat new) / 0.1578 (pedestrian lat straight) / 0.1556 (car lat straight) |
| T1 | ii_rec | True | B3 | True | 0.0487 / 0.0526 / 0.0598 | 0.1633 (large lat new) / 0.1570 (pedestrian lat straight) / 0.1553 (car lat straight) |
| T1 | iii | False | B3 | False | 0.0482 / 0.0449 / 0.0551 | 0.1970 (large lat new) / 0.1434 (car long turning) / 0.1626 (car lat straight) |
| T1 | iii_pooledcentre | False | B3 | False | 0.0496 / 0.0385 / 0.0493 | 0.2177 (large lat new) / 0.1595 (pedestrian long turning) / 0.1561 (large long straight) |
| T3 | i_rec | True | B0, B3 | True | 0.0471 / 0.0412 / 0.0521 | 0.1219 (large long turning) / 0.1096 (large lat straight) / 0.1569 (car lat straight) |
| T3 | i_x3 | True | B0, B3 | True | 0.0473 / 0.0409 / 0.0514 | 0.1224 (large long turning) / 0.1097 (large lat straight) / 0.1555 (car lat straight) |
| T3 | ii_x3 | True | B0, B3 | True | 0.0475 / 0.0447 / 0.0527 | 0.1622 (large long turning) / 0.1653 (large lat straight) / 0.1894 (car lat straight) |
| T3 | ii_rec | True | B0, B3 | True | 0.0474 / 0.0450 / 0.0536 | 0.1606 (large long turning) / 0.1660 (large lat straight) / 0.1884 (car lat straight) |
| T3 | iii | False | B0, B3 | False | 0.0471 / 0.0396 / 0.0535 | 0.1458 (large long turning) / 0.1289 (large lat static) / 0.1817 (car lat straight) |
| T3 | iii_pooledcentre | False | B0, B3 | False | 0.0487 / 0.0369 / 0.0480 | 0.1333 (large lat turning) / 0.1628 (large long static) / 0.1801 (car lat straight) |

**(c2) Simulated false removal and coverage at Argoverse 2's cell sizes.** 1000 data sets per tracker keep the observed per-log record counts per cell, set every cell's true rate to δ = 0.05 and draw per-log rates from a beta-binomial with the cell's ANOVA intraclass correlation. The record's comparator rule is applied at the removal level with an inner log bootstrap of 1000, so the removal quantile sits between the 2nd and 3rd largest replicate. Method (i) is the record's rule (pre-specified); methods (ii) and (iii) and M\*'s own flag rate are added, not pre-specified. Under (i), a comparator truly at δ is falsely removed in 0.000–0.003 of data sets, against the 0.0125 budget. M\*'s simultaneous "95 %" cell bounds cover only 0.376–0.547 at δ and 0.256–0.520 at M\*'s observed cell rates, while the HK1c "99.5 %" bound covers 0.973–0.991 at δ and 0.969–0.994 at observed rates. M\*'s own flag rate at δ is 0.029–0.056 per population and 0.113–0.127 for any population. Method (ii) covers 0.913–0.953 simultaneously, with false removal 0.006–0.014 and a flag rate of 0.091–0.114; method (iii) covers 0.713–0.834, with false removal 0.129–0.240 and a flag rate of 0.180–0.333. A model check puts the model's SE at a median 0.85–1.04 of the record's bootstrap SE (range 0.33–2.89), so power-like numbers at observed rates are overstated by the simulation.

**S6-Table 6. (c2) False removal of each comparator removed in r1** (truth 0.05 in every cell, on its own layout; "9 conditions" is plan §6.2's rule, "code" adds the HK1c failure; 95 % Wilson intervals over data sets in brackets).

| Tracker | Comparator | (i) 9 conditions | (i) code | (ii) 9 conditions | (iii) 9 conditions |
|---|---|---|---|---|---|
| T1 | B0 | 0.003 [0.001, 0.009] | 0.003 | 0.014 [0.008, 0.023] | 0.166 [0.144, 0.190] |
| T1 | B1 | 0.001 [0.000, 0.006] | 0.001 | 0.012 [0.007, 0.021] | 0.212 [0.188, 0.238] |
| T1 | B4 | 0.003 [0.001, 0.009] | 0.003 | 0.011 [0.006, 0.020] | 0.159 [0.138, 0.183] |
| T1 | B6 | 0.002 [0.001, 0.007] | 0.002 | 0.014 [0.008, 0.023] | 0.129 [0.110, 0.151] |
| T1 | B9 | 0.001 [0.000, 0.006] | 0.001 | 0.009 [0.005, 0.017] | 0.225 [0.200, 0.252] |
| T1 | RETUNED | 0.002 [0.001, 0.007] | 0.003 | 0.014 [0.008, 0.023] | 0.209 [0.185, 0.235] |
| T3 | B1 | 0.000 [0.000, 0.004] | 0.000 | 0.006 [0.003, 0.013] | 0.240 [0.215, 0.267] |
| T3 | B4 | 0.001 [0.000, 0.006] | 0.001 | 0.011 [0.006, 0.020] | 0.204 [0.180, 0.230] |
| T3 | B6 | 0.000 [0.000, 0.004] | 0.000 | 0.011 [0.006, 0.020] | 0.179 [0.156, 0.204] |
| T3 | B9 | 0.001 [0.000, 0.006] | 0.001 | 0.010 [0.005, 0.018] | 0.239 [0.214, 0.266] |
| T3 | RETUNED | 0.000 [0.000, 0.004] | 0.000 | 0.009 [0.005, 0.017] | 0.235 [0.210, 0.262] |

**S6-Table 7. (c2) M\*: coverage at true rates 0.05 in every cell, and M\*'s own flag rate** (simultaneous coverage of the one-sided "95 %" cell bounds over the evaluable cells, with mean and worst per-cell coverage; coverage of the HK1c "99.5 %" pooled bound; flag rate added, not pre-specified).

| Tracker | Population | (i) simultaneous (mean; worst cell) | (i) HK1c | (ii) simultaneous (mean; worst cell) | (ii) HK1c | (iii) simultaneous (mean; worst cell) | (iii) HK1c | M\*'s flag rate (i) | (ii) | (iii) |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 | P_rel | 0.395 (0.966; 0.899) | 0.991 | 0.942 (0.998; 0.990) | 0.993 | 0.732 (0.988; 0.957) | 0.992 | 0.053 | 0.101 | 0.267 |
| T1 | P_near | 0.414 (0.944; 0.899) | 0.986 | 0.937 (0.996; 0.991) | 0.995 | 0.729 (0.980; 0.968) | 0.990 | 0.037 | 0.099 | 0.304 |
| T1 | P_ip | 0.524 (0.924; 0.876) | 0.973 | 0.913 (0.989; 0.952) | 0.988 | 0.795 (0.973; 0.934) | 0.985 | 0.029 | 0.092 | 0.183 |
| T3 | P_rel | 0.433 (0.969; 0.921) | 0.991 | 0.953 (0.998; 0.990) | 0.994 | 0.733 (0.989; 0.967) | 0.994 | 0.056 | 0.107 | 0.308 |
| T3 | P_near | 0.376 (0.943; 0.880) | 0.980 | 0.941 (0.996; 0.991) | 0.987 | 0.713 (0.980; 0.956) | 0.982 | 0.040 | 0.114 | 0.333 |
| T3 | P_ip | 0.547 (0.928; 0.903) | 0.976 | 0.942 (0.992; 0.978) | 0.988 | 0.834 (0.977; 0.957) | 0.987 | 0.035 | 0.091 | 0.180 |
| T1 | any population | – | – | – | – | – | – | 0.113 | 0.267 | 0.589 |
| T3 | any population | – | – | – | – | – | – | 0.127 | 0.281 | 0.629 |

### S6.5 (d) M\* at a reference that uses nothing after the decision time (plan §2(d))

`[d_ref_runs/x3_d_ref_runs_v01.md; X3_REF_REPORT_v01 §2]`

M\*'s items were rebuilt with the frozen items rule, changing only the reference ego progression (three changed lines of code). The references are d0, the logged arc length (of record); d1, the plan arm Z0 chooses at margin 0, leashed by the log; and d2, constant current speed along the route, capped at its end. M\* was refitted on each set of items by the frozen rule and folds and run in decision mode; d0 reproduces the record exactly. **The leash.** d1 equals d0 at 2 s in 95.7 % (T1) and 96.4 % (T3) of decisions, because decision mode caps the planner's positions at the logged arc length, so d1 does not leave the logged speed profile. d2 does: it equals the logged arc length in 17.8 % of decisions, with a 10th–90th percentile range of −1.7 to +1.9 m. d2's speed is the logged speed over a 0.5 s window centered on the decision time, a 0.25 s look-ahead shared with the items of record. The scored plans of every arm are leashed to the log as well, so the hindsight enters both the items and the evaluation, through the leash, for all arms alike. **The population** barely moves: 98.74–99.80 % of the relied items of record keep their axis and side, and M\*'s thresholds change by a median ratio of 1.000 (10th–90th percentiles within 0.93–1.07). Validity and the infeasible rate are unchanged (differences at most 0.0006).

**S6-Table 8. (d) M\* refitted at three references.**

| Tracker | Arm | Valid | Shown above | Failing | Infeasible (95 % CI) | M\* − arm (95 % CI) | Pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|---|
| T1 | M\* of record | True | False | - | 0.1864 [0.1680, 0.2048] | - | 0.0440 / 0.0376 / 0.0404 |
| T1 | d0: logged arc length (= record; check) | True | False | - | 0.1864 [0.1680, 0.2048] | 0.0000 [0.0000, 0.0000] | 0.0440 / 0.0376 / 0.0404 |
| T1 | d1: the planner's margin-0 plan (Z0) | True | False | - | 0.1861 [0.1679, 0.2045] | 0.0003 [-0.0008, 0.0014] | 0.0440 / 0.0378 / 0.0406 |
| T1 | d2: constant current speed | True | False | - | 0.1863 [0.1681, 0.2046] | 0.0001 [-0.0013, 0.0015] | 0.0441 / 0.0383 / 0.0407 |
| T3 | M\* of record | True | False | - | 0.2466 [0.2258, 0.2677] | - | 0.0430 / 0.0324 / 0.0405 |
| T3 | d0: logged arc length (= record; check) | True | False | - | 0.2466 [0.2258, 0.2677] | 0.0000 [0.0000, 0.0000] | 0.0430 / 0.0324 / 0.0405 |
| T3 | d1: the planner's margin-0 plan (Z0) | True | False | - | 0.2461 [0.2253, 0.2673] | 0.0005 [0.0001, 0.0010] | 0.0430 / 0.0326 / 0.0396 |
| T3 | d2: constant current speed | True | False | - | 0.2460 [0.2254, 0.2668] | 0.0006 [-0.0007, 0.0021] | 0.0430 / 0.0327 / 0.0395 |

### S6.6 (e) The obvious alternatives (plan §2(e)), with amendment A2

`[e_alternatives/x3_e_alternatives_v01.md; X3_CORE_REPORT_R2_v01; X3_REF_REPORT_v01 §3–§4]`

(e1) B5, per-axis CRC scalars; B8, stratified variance matching, z_0.95·√(mean U²) per L0 stratum with its fallback; B7, a learned scale on a seeded half of the calibration logs with CRC on the other half. B7 needs the track speed and course over ground, which the items of record do not carry; they were read from the stage-B cache at each item's track row, and the motion state re-derived from them equals every item's. (e2) The Q-refit uses S_h(q) = A_h + q(S_h − A_h), with A_h the propagated covariance at Q = 0; the frozen propagation at Q = 1 matches the horizon of record with largest absolute difference 0, and the linearity in Q holds to 1.7e-13 (T1) and 1.2e-10 (T3). q per fold and class group is the smallest grid value whose B0-type margin has a pooled training exceedance ≤ 0.05, and the arm runs B0's margin rule on the substituted covariances; both grids of amendment A2 were run (S6.11). Checks: B0 on the cache's own covariance reproduces B0 of record exactly, and B7's runner margins equal the fit's item-level margins. B5 and B7 are shown above δ; B8 passes but is infeasible in 0.2822 (T1) and 0.5074 (T3) of decisions; neither Q-refit arm passes.

**S6-Table 9. (e) The alternatives** (screen; infeasible-decision rate; M\* − arm, paired, 95 % interval; pooled relied-record exceedance per population).

| Tracker | Arm | Valid | Shown above | Failing | Infeasible (95 % CI) | M\* − arm (95 % CI) | Pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|---|
| T1 | M\* of record | True | False | - | 0.1864 [0.1678, 0.2050] | - | 0.0440 / 0.0376 / 0.0404 |
| T1 | B0 on the cache's own covariance (check) | False | True | P_rel: NoFlag,FamFlag; P_near: NoFlag,FamFlag; P_ip: NoFlag,FamFlag | 0.3711 [0.3435, 0.3990] | -0.1847 [-0.2097, -0.1594] | 0.0337 / 0.0258 / 0.0502 |
| T1 | Q-refit, plan grid | False | True | P_rel: NoFlag,FamFlag; P_near: NoFlag,FamFlag; P_ip: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.2709 [0.2459, 0.2952] | -0.0846 [-0.1085, -0.0596] | 0.0431 / 0.0318 / 0.0696 |
| T1 | Q-refit, extended grid (amendment A2) | False | True | P_rel: NoFlag,FamFlag; P_near: NoFlag,FamFlag; P_ip: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.2299 [0.2072, 0.2530] | -0.0436 [-0.0668, -0.0199] | 0.0488 / 0.0367 / 0.0803 |
| T1 | B5: per-axis CRC scalars | False | True | P_rel: NoFlag,FamFlag; P_near: NoFlag,FamFlag; P_ip: NoFlag,FamFlag | 0.1668 [0.1493, 0.1840] | 0.0196 [0.0009, 0.0384] | 0.0471 / 0.0473 / 0.0534 |
| T1 | B8: stratified variance matching | True | False | - | 0.2822 [0.2587, 0.3064] | -0.0959 [-0.1091, -0.0836] | 0.0157 / 0.0177 / 0.0291 |
| T1 | B7: learned scale | False | True | P_rel: NoFlag,FamFlag | 0.1538 [0.1367, 0.1712] | 0.0325 [0.0180, 0.0471] | 0.0463 / 0.0314 / 0.0485 |
| T3 | M\* of record | True | False | - | 0.2466 [0.2263, 0.2681] | - | 0.0430 / 0.0324 / 0.0405 |
| T3 | B0 on the cache's own covariance (check) | False | False | P_near: Floor | 0.8575 [0.8397, 0.8748] | -0.6109 [-0.6341, -0.5888] | 0.0041 / 0.0031 / 0.0030 |
| T3 | Q-refit, plan grid | False | False | P_near: Floor | 0.8136 [0.7933, 0.8335] | -0.5669 [-0.5902, -0.5443] | 0.0064 / 0.0046 / 0.0065 |
| T3 | Q-refit, extended grid (amendment A2) | False | False | P_near: Floor | 0.7835 [0.7626, 0.8042] | -0.5369 [-0.5601, -0.5145] | 0.0078 / 0.0060 / 0.0080 |
| T3 | B5: per-axis CRC scalars | False | True | P_rel: NoFlag,FamFlag; P_near: NoFlag,FamFlag; P_ip: NoFlag | 0.2395 [0.2188, 0.2607] | 0.0071 [-0.0023, 0.0166] | 0.0507 / 0.0346 / 0.0534 |
| T3 | B8: stratified variance matching | True | False | - | 0.5074 [0.4818, 0.5339] | -0.2607 [-0.2817, -0.2404] | 0.0148 / 0.0144 / 0.0298 |
| T3 | B7: learned scale | False | True | P_rel: NoFlag,FamFlag | 0.2634 [0.2422, 0.2859] | -0.0168 [-0.0296, -0.0040] | 0.0485 / 0.0276 / 0.0532 |

### S6.7 (f) The infeasibility–violation trade-off (plan §2(f))

`[f_tradeoff/x3_f_tradeoff_v01.md; figures x3_f_infeasible_vs_V2_v01.pdf and x3_f_infeasible_vs_V2viol_v01.pdf (main-text Fig. 4)]`

From the outputs of record only. V2 and V2_viol are on P_rel (V2_viol: some relied constraint violated, D > G), and the status is the record's: comparators of K at their removal level, every other arm at 0.95. The checks against the record (449 per tracker) agree to 3.33e-16 (T1), 1.11e-16 (T3) and 2.22e-16 (AB3DMOT). A decision is infeasible exactly when its executed back-off level is below 1, with no exception in 349,928 decision rows per tracker. No arm of any status is at or below M\* on both the infeasible rate and V2_viol, on any tracker, and every valid arm of record other than M\* (the B0 sweep points included) is infeasible in at least 0.660 of decisions. This holds for the arms of record only: the exploratory B8 of (e) passes at 0.282 (T1) and 0.507 (T3) (S6.6). The emergency-stop share is the same for every arm: 0.004252 (T1), 0.002392 (T3) and 0.006378 (AB3DMOT). Of M\*'s infeasible decisions on T1, 0.323 / 0.302 / 0.212 / 0.140 / 0.023 back off to λ = 0.75 / 0.5 / 0.25 / 0 / the emergency stop; on AB3DMOT 0.739 go to λ = 0. The 21 B0 sweep points per tracker are in the result file; RETUNED-HK1 chose B0a8 in every fold, so its point coincides with B0a8's. *(added)* By linear interpolation of the sweep at M\*'s V2, scaling the raw covariance is infeasible in 0.2755 (T1) and 0.4403 (T3) of decisions, against M\*'s 0.1864 and 0.2466 (S6.16).

**S6-Table 10. (f) Every arm of record except the B0 sweep points** (status of record; infeasible-decision rate; V2; V2_viol).

| Tracker | Arm | Status of record | Infeasible | V2 | V2_viol |
|---|---|---|---|---|---|
| T1 | Z0 | shown above | 0.004 | 0.976 | 0.057 |
| T1 | B6 | shown above | 0.165 | 0.501 | 0.023 |
| T1 | M\* | valid | 0.186 | 0.491 | 0.016 |
| T1 | B4 | shown above | 0.202 | 0.520 | 0.026 |
| T1 | B0 | shown above | 0.371 | 0.395 | 0.022 |
| T1 | RETUNED | shown above | 0.407 | 0.361 | 0.022 |
| T1 | B1 | shown above | 0.513 | 0.188 | 0.019 |
| T1 | B9 | shown above | 0.693 | 0.158 | 0.014 |
| T1 | RETUNED-HK1 (= B0a8) | valid | 0.781 | 0.095 | 0.014 |
| T1 | M\*J | valid | 0.823 | 0.047 | 0.006 |
| T1 | M\*Jx | floor only | 0.858 | 0.038 | 0.006 |
| T1 | B3 | floor only | 0.969 | 0.033 | 0.007 |
| T3 | Z0 | shown above | 0.002 | 0.978 | 0.053 |
| T3 | B6 | shown above | 0.229 | 0.529 | 0.023 |
| T3 | M\* | valid | 0.247 | 0.496 | 0.018 |
| T3 | B4 | shown above | 0.315 | 0.572 | 0.049 |
| T3 | RETUNED | shown above | 0.611 | 0.316 | 0.028 |
| T3 | B9 | shown above | 0.663 | 0.177 | 0.018 |
| T3 | B1 | shown above | 0.666 | 0.228 | 0.024 |
| T3 | B0 | floor only | 0.858 | 0.072 | 0.013 |
| T3 | M\*J | valid | 0.862 | 0.047 | 0.009 |
| T3 | M\*Jx | floor only | 0.897 | 0.038 | 0.009 |
| T3 | B3 | floor only | 0.941 | 0.030 | 0.009 |
| T3 | RETUNED-HK1 (= B0a8) | floor only | 0.977 | 0.015 | 0.005 |
| AB3DMOT | Z0 | shown above | 0.006 | 0.977 | 0.183 |
| AB3DMOT | B6 | shown above | 0.891 | 0.493 | 0.052 |
| AB3DMOT | M\* | shown above | 0.891 | 0.520 | 0.038 |
| AB3DMOT | B4 | shown above | 0.896 | 0.517 | 0.059 |
| AB3DMOT | RETUNED | valid | 0.934 | 0.180 | 0.040 |
| AB3DMOT | B1 | floor only | 0.935 | 0.233 | 0.041 |
| AB3DMOT | B0 | floor only | 0.950 | 0.117 | 0.034 |
| AB3DMOT | M\*J | floor only | 0.963 | 0.045 | 0.015 |
| AB3DMOT | B9 | floor only | 0.968 | 0.111 | 0.043 |
| AB3DMOT | M\*Jx | floor only | 0.969 | 0.036 | 0.013 |
| AB3DMOT | RETUNED-HK1 (= B0a8) | floor only | 0.982 | 0.024 | 0.017 |
| AB3DMOT | B3 | floor only | 0.988 | 0.009 | 0.007 |

**S6-Table 11. (f) Back-off levels executed** (share of decisions pooled over decisions, log mean in brackets; λ = −1 is the emergency stop; the last column divides by the arm's infeasible decisions).

| Tracker | Arm | Infeasible | λ 1 | 0.75 | 0.5 | 0.25 | 0 | e-stop (−1) | Among infeasible: 0.75 / 0.5 / 0.25 / 0 / e-stop |
|---|---|---|---|---|---|---|---|---|---|
| T1 | M\* | 0.186 | 0.814 (0.814) | 0.060 (0.060) | 0.056 (0.056) | 0.040 (0.040) | 0.026 (0.026) | 0.004 (0.004) | 0.323 / 0.302 / 0.212 / 0.140 / 0.023 |
| T1 | B0 | 0.371 | 0.629 (0.629) | 0.116 (0.115) | 0.120 (0.120) | 0.078 (0.078) | 0.054 (0.054) | 0.004 (0.004) | 0.311 / 0.323 / 0.209 / 0.145 / 0.011 |
| T1 | B1 | 0.513 | 0.486 (0.487) | 0.125 (0.124) | 0.165 (0.164) | 0.151 (0.151) | 0.069 (0.069) | 0.004 (0.004) | 0.242 / 0.321 / 0.294 / 0.134 / 0.008 |
| T1 | B3 | 0.969 | 0.031 (0.031) | 0.028 (0.028) | 0.062 (0.062) | 0.180 (0.180) | 0.695 (0.695) | 0.004 (0.004) | 0.029 / 0.064 / 0.185 / 0.718 / 0.004 |
| T1 | B4 | 0.202 | 0.798 (0.798) | 0.071 (0.071) | 0.053 (0.053) | 0.044 (0.044) | 0.030 (0.030) | 0.004 (0.004) | 0.349 / 0.263 / 0.216 / 0.151 / 0.021 |
| T1 | B6 | 0.165 | 0.835 (0.835) | 0.063 (0.063) | 0.043 (0.043) | 0.033 (0.034) | 0.022 (0.022) | 0.004 (0.004) | 0.379 / 0.259 / 0.202 / 0.135 / 0.026 |
| T1 | B9 | 0.693 | 0.307 (0.307) | 0.105 (0.105) | 0.154 (0.155) | 0.166 (0.166) | 0.263 (0.263) | 0.004 (0.004) | 0.151 / 0.223 / 0.240 / 0.380 / 0.006 |
| T1 | RETUNED | 0.407 | 0.593 (0.593) | 0.116 (0.115) | 0.134 (0.134) | 0.095 (0.094) | 0.058 (0.058) | 0.004 (0.004) | 0.284 / 0.329 / 0.232 / 0.144 / 0.010 |
| T3 | M\* | 0.247 | 0.753 (0.753) | 0.069 (0.069) | 0.074 (0.074) | 0.066 (0.066) | 0.036 (0.036) | 0.002 (0.002) | 0.281 / 0.299 / 0.266 / 0.145 / 0.010 |
| T3 | B0 | 0.858 | 0.142 (0.142) | 0.064 (0.064) | 0.099 (0.099) | 0.246 (0.246) | 0.446 (0.445) | 0.002 (0.002) | 0.075 / 0.116 / 0.287 / 0.520 / 0.003 |
| T3 | B1 | 0.666 | 0.334 (0.334) | 0.080 (0.080) | 0.104 (0.104) | 0.197 (0.196) | 0.283 (0.283) | 0.002 (0.002) | 0.120 / 0.156 / 0.295 / 0.425 / 0.004 |
| T3 | B3 | 0.941 | 0.059 (0.059) | 0.040 (0.040) | 0.089 (0.089) | 0.190 (0.191) | 0.619 (0.618) | 0.002 (0.002) | 0.043 / 0.095 / 0.202 / 0.658 / 0.003 |
| T3 | B4 | 0.315 | 0.685 (0.685) | 0.077 (0.077) | 0.078 (0.078) | 0.081 (0.081) | 0.077 (0.077) | 0.002 (0.002) | 0.245 / 0.247 / 0.255 / 0.245 / 0.008 |
| T3 | B6 | 0.229 | 0.771 (0.771) | 0.062 (0.062) | 0.068 (0.068) | 0.057 (0.057) | 0.040 (0.040) | 0.002 (0.002) | 0.269 / 0.297 / 0.249 / 0.174 / 0.010 |
| T3 | B9 | 0.663 | 0.337 (0.337) | 0.115 (0.116) | 0.136 (0.136) | 0.168 (0.168) | 0.241 (0.241) | 0.002 (0.002) | 0.174 / 0.205 / 0.253 / 0.364 / 0.004 |
| T3 | RETUNED | 0.611 | 0.389 (0.389) | 0.102 (0.102) | 0.139 (0.139) | 0.179 (0.179) | 0.189 (0.189) | 0.002 (0.002) | 0.167 / 0.227 / 0.293 / 0.309 / 0.004 |
| AB3DMOT | M\* | 0.891 | 0.109 (0.109) | 0.014 (0.014) | 0.035 (0.035) | 0.177 (0.178) | 0.658 (0.658) | 0.006 (0.006) | 0.016 / 0.039 / 0.199 / 0.739 / 0.007 |
| AB3DMOT | B0 | 0.950 | 0.050 (0.050) | 0.014 (0.014) | 0.015 (0.015) | 0.021 (0.021) | 0.894 (0.894) | 0.006 (0.006) | 0.015 / 0.016 / 0.022 / 0.941 / 0.007 |
| AB3DMOT | B1 | 0.935 | 0.065 (0.065) | 0.012 (0.012) | 0.013 (0.013) | 0.030 (0.030) | 0.874 (0.874) | 0.006 (0.006) | 0.013 / 0.013 / 0.032 / 0.935 / 0.007 |
| AB3DMOT | B3 | 0.988 | 0.012 (0.012) | 0.003 (0.003) | 0.008 (0.008) | 0.024 (0.024) | 0.947 (0.947) | 0.006 (0.006) | 0.003 / 0.008 / 0.024 / 0.958 / 0.006 |
| AB3DMOT | B4 | 0.896 | 0.104 (0.104) | 0.007 (0.007) | 0.009 (0.009) | 0.084 (0.084) | 0.789 (0.789) | 0.006 (0.006) | 0.008 / 0.010 / 0.094 / 0.881 / 0.007 |
| AB3DMOT | B6 | 0.891 | 0.109 (0.109) | 0.010 (0.010) | 0.025 (0.025) | 0.070 (0.070) | 0.779 (0.779) | 0.006 (0.006) | 0.012 / 0.028 / 0.079 / 0.874 / 0.007 |
| AB3DMOT | B9 | 0.968 | 0.032 (0.032) | 0.021 (0.021) | 0.064 (0.063) | 0.194 (0.194) | 0.683 (0.683) | 0.006 (0.006) | 0.022 / 0.066 / 0.200 / 0.706 / 0.007 |
| AB3DMOT | RETUNED | 0.934 | 0.066 (0.066) | 0.011 (0.011) | 0.013 (0.013) | 0.018 (0.018) | 0.885 (0.885) | 0.006 (0.006) | 0.012 / 0.014 / 0.019 / 0.948 / 0.007 |

### S6.8 (g) The learning curve (plan §2(g))

`[g_learning/x3_g_learning_v01.md; X3_CORE_REPORT_R2_v01]`

M\* was refitted on n ∈ {25, 50, 100, 200} training logs per held-out fold, as seeded subsamples of the 300 training logs with 3 repeats each; n = 300 is the fit of record. A subsample whose fit leaves a threshold undefined (no level with 19 logs, in the in-path part) is not fittable and was not run: n = 25 on T1 repeats 0 and 2, and on T3 all three. From n = 200 every repeat passes on both trackers, at an infeasible rate of 0.1911–0.1980 (T1) and 0.2538–0.2641 (T3), against 0.1864 and 0.2466 of record. At n = 50 and 100, four of the six T1 repeats are shown above δ, through the P_rel no-flag condition (and on one repeat also P_ip). The share of M\*'s thresholds that fall back to a coarser level than their own L0 stratum (mean over folds) is 0.907, 0.913 and 0.802 (T1) and 0.847, 0.859 and 0.797 (T3) at n = 25; 0.752–0.760 and 0.748–0.758 at n = 50; 0.645–0.653 and 0.643–0.653 at n = 100; 0.560–0.567 and 0.555–0.562 at n = 200; and 0.484 and 0.483 at n = 300.

**S6-Table 12. (g) M\* refitted on n training logs per fold.**

| Tracker | Arm | Valid | Shown above | Failing | Infeasible (95 % CI) | M\* − arm (95 % CI) | Pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|---|
| T1 | M\* of record | True | False | - | 0.1864 [0.1682, 0.2053] | - | 0.0440 / 0.0376 / 0.0404 |
| T1 | n = 25 training logs per fold, repeat 1 | False | True | P_rel: NoFlag,FamFlag; P_near: NoFlag,FamFlag | 0.4316 [0.4034, 0.4603] | -0.2452 [-0.2672, -0.2239] | 0.0158 / 0.0160 / 0.0292 |
| T1 | n = 50 training logs per fold, repeat 0 | False | True | P_rel: NoFlag; P_ip: NoFlag | 0.3018 [0.2779, 0.3260] | -0.1154 [-0.1298, -0.1013] | 0.0313 / 0.0288 / 0.0418 |
| T1 | n = 50 training logs per fold, repeat 1 | False | True | P_rel: NoFlag | 0.2690 [0.2467, 0.2917] | -0.0826 [-0.0957, -0.0695] | 0.0298 / 0.0250 / 0.0348 |
| T1 | n = 50 training logs per fold, repeat 2 | True | False | - | 0.2797 [0.2562, 0.3030] | -0.0933 [-0.1074, -0.0796] | 0.0298 / 0.0255 / 0.0304 |
| T1 | n = 100 training logs per fold, repeat 0 | False | True | P_rel: NoFlag | 0.2323 [0.2113, 0.2541] | -0.0459 [-0.0556, -0.0365] | 0.0376 / 0.0313 / 0.0436 |
| T1 | n = 100 training logs per fold, repeat 1 | False | True | P_rel: NoFlag | 0.2028 [0.1844, 0.2221] | -0.0165 [-0.0232, -0.0097] | 0.0393 / 0.0355 / 0.0380 |
| T1 | n = 100 training logs per fold, repeat 2 | True | False | - | 0.2214 [0.2022, 0.2413] | -0.0350 [-0.0428, -0.0277] | 0.0383 / 0.0307 / 0.0410 |
| T1 | n = 200 training logs per fold, repeat 0 | True | False | - | 0.1955 [0.1770, 0.2151] | -0.0092 [-0.0144, -0.0038] | 0.0417 / 0.0358 / 0.0396 |
| T1 | n = 200 training logs per fold, repeat 1 | True | False | - | 0.1911 [0.1728, 0.2106] | -0.0047 [-0.0098, 0.0002] | 0.0428 / 0.0342 / 0.0373 |
| T1 | n = 200 training logs per fold, repeat 2 | True | False | - | 0.1980 [0.1792, 0.2178] | -0.0116 [-0.0165, -0.0068] | 0.0425 / 0.0363 / 0.0346 |
| T3 | M\* of record | True | False | - | 0.2466 [0.2255, 0.2680] | - | 0.0430 / 0.0324 / 0.0405 |
| T3 | n = 50 training logs per fold, repeat 0 | True | False | - | 0.3651 [0.3411, 0.3897] | -0.1185 [-0.1305, -0.1069] | 0.0315 / 0.0263 / 0.0300 |
| T3 | n = 50 training logs per fold, repeat 1 | True | False | - | 0.3762 [0.3523, 0.4001] | -0.1296 [-0.1426, -0.1172] | 0.0304 / 0.0221 / 0.0279 |
| T3 | n = 50 training logs per fold, repeat 2 | True | False | - | 0.3764 [0.3517, 0.4015] | -0.1298 [-0.1420, -0.1170] | 0.0285 / 0.0232 / 0.0235 |
| T3 | n = 100 training logs per fold, repeat 0 | False | True | P_rel: NoFlag | 0.3010 [0.2788, 0.3238] | -0.0543 [-0.0618, -0.0471] | 0.0370 / 0.0275 / 0.0370 |
| T3 | n = 100 training logs per fold, repeat 1 | True | False | - | 0.2919 [0.2696, 0.3144] | -0.0453 [-0.0533, -0.0377] | 0.0389 / 0.0306 / 0.0372 |
| T3 | n = 100 training logs per fold, repeat 2 | True | False | - | 0.3025 [0.2799, 0.3250] | -0.0558 [-0.0624, -0.0491] | 0.0376 / 0.0273 / 0.0376 |
| T3 | n = 200 training logs per fold, repeat 0 | True | False | - | 0.2641 [0.2429, 0.2857] | -0.0175 [-0.0223, -0.0128] | 0.0411 / 0.0315 / 0.0389 |
| T3 | n = 200 training logs per fold, repeat 1 | True | False | - | 0.2538 [0.2325, 0.2755] | -0.0072 [-0.0113, -0.0033] | 0.0425 / 0.0307 / 0.0394 |
| T3 | n = 200 training logs per fold, repeat 2 | True | False | - | 0.2608 [0.2396, 0.2822] | -0.0141 [-0.0191, -0.0091] | 0.0424 / 0.0336 / 0.0400 |

### S6.9 (h) The AB3DMOT diagnosis (plan §2(h))

`[h_ab3dmot/x3_h_ab3dmot_v01.md; X3_STATS_REPORT_v01 §2, §4–§5]`

From the outputs of record; AB3DMOT is descriptive in the registered test, and T1 and T3 are shown for comparison. M\*'s screen on AB3DMOT fails only through the pooled P_rel cell (E 0.0609, LB 0.0570); no cell or family cell is flagged. Its 16 P_rel cells with E > 0.05 hold 0.800 of P_rel records, among them car longitudinal static (0.0573; 187,026 records) and the pedestrian static cells (0.0590 and 0.0596); the two-wheeler cells with E 0.2007–0.3067 are not evaluable and take a coarser level's threshold. The false-positive share was counted directly with the items' own enumeration over every track, because the items summaries count ground-truth-matched tracks only; on the matched tracks the count reproduces the summaries exactly. AB3DMOT's score scale may differ from the LT3D detector's; the score bins are the plan's fixed bins. Whether false-positive tracks drive AB3DMOT's high infeasible rate was tested afterwards (amendment A4(5); S6.21): removing every unmatched track from the planner's input lowers M\*'s infeasible rate only from 0.891 to 0.757, less than the halving fixed in advance, and M\* is still flagged. False-positive tracks are therefore not the main driver, and that explanation is dropped.

**S6-Table 13. (h) M\*'s pooled P_rel screen (h1), the fallback shares of M\*'s fits (h2), relied records by track score (h3) and enforced pairs whose track has no ground-truth match (h4).**

| Tracker | M\* Valid (P_rel) | M\* pooled P_rel E [LB 0.95] | Pooled flag | HK1c UB 0.995 | Thresholds from a coarser level | Record-weighted P_rel / P_near / P_ip | Relied records | Score below 0.5 | Score below 0.7 | Enforced pairs (all tracks) | Without GT match | Share | Per decision | Decisions with ≥ 1 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | True | 0.0440 [0.0411] | False | 0.0482 | 0.484 | 0.0066 / 0.0077 / 0.0746 | 537924 | 0.080 | 0.446 | 637896 | 77490 | 0.1215 | 6.865 | 0.643 |
| T3 | True | 0.0430 [0.0402] | False | 0.0471 | 0.483 | 0.0065 / 0.0092 / 0.0758 | 537754 | 0.080 | 0.446 | 638036 | 77839 | 0.1220 | 6.896 | 0.647 |
| AB3DMOT | False | 0.0609 [0.0570] | True | 0.0666 | 0.520 | 0.0042 / 0.0054 / 0.0676 | 587133 | 0.413 | 0.915 | 1013537 | 403577 | 0.3982 | 35.753 | 0.926 |

### S6.10 Amendment A1: the heading error behind the "lateral" diagnosis

`[a1_heading/x3_a1_heading_v01.md; A1 §(i)–(ii)]`

Data: X2's four decision cells (nuScenes train, 700 scenes, T1, in-path cars, 2 s, σ_a = 0.10 m). The items were rebuilt by importing the frozen X2 code read-only, and the rebuild reproduces X2's item counts, scenes and record-weighted E in all four cells exactly (car < 20 m lateral: 3396 items, 442 scenes, E 0.19405182567726736), as well as the truth-oriented cells. The heading error is |wrap(ψ_track − ψ_annotation)| at the decision keyframe, folded to [0°, 90°]. The reading fixed in A1 (ii): in both lateral cells and both orientations, E on items with heading error ≤ 20° still exceeds the threshold, with its 95 % interval entirely above it, so the lateral under-coverage is not explained by heading error. In the lateral cells 0.348–0.387 of items have a heading error above 20°, and they carry 0.411–0.493 of the exceedances. The intervals are pointwise percentile intervals from a scene-cluster bootstrap (B = 2000), not X2's simultaneous band. Stricter cuts (≤ 5° and ≤ 10°) and the annotation's own axes (amendment A4(4); S6.20) show that heading error explains part of the lateral excess; in the < 20 m cell the excess remains under every cut.

**S6-Table 14. (A1) Heading error in X2's decision cells.**

| Orientation | Cell | n | ≤ 10° | (10°, 20°] | > 20° | Exceedances from > 20° | E (≤ 20°) [95 % CI] | n (≤ 20°) | Threshold of record | E (all, record) |
|---|---|---|---|---|---|---|---|---|---|---|
| estimate | car, < 20 m, lat | 3396 | 0.458 | 0.155 | 0.387 | 0.411 (271 of 659) | 0.186 [0.154, 0.223] | 2081 | 0.0775 | 0.194 |
| estimate | car, 20–40 m, lat | 1229 | 0.418 | 0.229 | 0.352 | 0.419 (140 of 334) | 0.244 [0.185, 0.306] | 796 | 0.0816 | 0.272 |
| estimate | car, < 20 m, long | 8038 | 0.781 | 0.092 | 0.128 | 0.057 (2 of 35) | 0.005 [0.003, 0.007] | 7013 | 0.0646 | 0.004 |
| estimate | car, 20–40 m, long | 3522 | 0.793 | 0.089 | 0.119 | 0.000 (0 of 38) | 0.012 [0.007, 0.018] | 3104 | 0.0500 | 0.011 |
| truth | car, < 20 m, lat | 3554 | 0.460 | 0.157 | 0.383 | 0.444 (244 of 549) | 0.139 [0.111, 0.170] | 2193 | 0.0500 | 0.154 |
| truth | car, 20–40 m, lat | 1248 | 0.418 | 0.234 | 0.348 | 0.493 (140 of 284) | 0.177 [0.122, 0.237] | 814 | 0.0500 | 0.228 |
| truth | car, < 20 m, long | 8233 | 0.777 | 0.090 | 0.132 | 0.100 (1 of 10) | 0.001 [0.001, 0.002] | 7143 | 0.0500 | 0.001 |
| truth | car, 20–40 m, long | 3522 | 0.793 | 0.089 | 0.119 | 0.000 (0 of 37) | 0.012 [0.007, 0.018] | 3104 | 0.0500 | 0.011 |

### S6.11 Amendment A2: the Q-refit grid extended to no process noise

`[A2; e2_qrefit/qfit_table_ext_t1.json (3af4e893…), qfit_table_ext_t3.json (398859b3…); e_alternatives/x3_e_alternatives_v01.md; X3_REF_REPORT_v01 §4]`

The plan's grid {0.25, 0.5, 1, 2, 4, 8, 16, 32} hit its floor: q = 0.25 was chosen in 17 of 20 (fold, class group) cells on T1 and in 20 of 20 on T3, where the training exceedance at q = 0.25 was already 0.000–0.0095. A2 repeats §2(e2) with the grid extended down to {0, 1/64, 1/32, 1/16, 1/8}, under the same selection rule, and both arms were run (S6-Table 9). On the extended grid, T3 takes q = 0 in all 20 cells, with a training exceedance of at most 0.012 even with no process noise; T1 takes q = 0 for cars in every fold (training exceedance 0.038–0.040), 1–4 for pedestrians (as on the plan grid), 1/16–1/8 for two-wheelers and 1/16–1/4 for large vehicles. Re-tuning the process noise for the 2 s horizon on the relied population therefore removes most of it, and neither Q-refit arm passes the screen (S6.6).

**S6-Table 15. (A2) q per fold and class group: plan grid → extended grid.**

| Tracker | Fold | Car | Pedestrian | Two-wheeler | Large vehicle |
|---|---|---|---|---|---|
| T1 | 0 | 0.25 → 0 | 2 → 2 | 0.25 → 0.125 | 0.25 → 0.25 |
| T1 | 1 | 0.25 → 0 | 1 → 1 | 0.25 → 0.0625 | 0.25 → 0.25 |
| T1 | 2 | 0.25 → 0 | 2 → 2 | 0.25 → 0.125 | 0.25 → 0.0625 |
| T1 | 3 | 0.25 → 0 | 2 → 2 | 0.25 → 0.125 | 0.25 → 0.25 |
| T1 | 4 | 0.25 → 0 | 4 → 4 | 0.25 → 0.125 | 0.25 → 0.25 |
| T3 | 0 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 |
| T3 | 1 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 |
| T3 | 2 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 |
| T3 | 3 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 |
| T3 | 4 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 | 0.25 → 0 |

### S6.12 Amendments A3 and A4: what they add, and their status

`[A3 = 20_DESIGN/X3_PLAN_AMENDMENT_A3_v01.md, SHA-256 009a0aad…; A4 = 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md, SHA-256 ab19dd66…; outputs 60_RESULTS/x3_explore_v01/a3_review/, a4_review/ and a1_heading/x3_a4_heading_v01.md; the authors' decision record]`

- **Why they were written.** A second internal review of an earlier version of the manuscript `[70_TESTS/V06_REFEREE_REVIEW_v01.md, 59956973…]` asked what an infeasible decision costs in this planner, whether the matched-validity comparison of (a) holds on a screen that no method's strata define, how the partition flags of (b) behave under multiplicity, and for checks of the harness, of the heading diagnosis and of the AB3DMOT diagnosis.
- **What they add.** A3: (i) what an infeasible decision costs, for every arm (S6.13); (ii) the partition screen of (b) applied to the matched arms of (a) and to B8, and (iv) the partition flags with the level corrected across partitions (S6.14); (iii) M\*'s exceedance on its own calibration items, the quantity its certificate is about (S6.15). A4: (1) matched validity on a neutral screen, with M\*'s own level tuned (S6.17); (2) loop-mode replay on Argoverse 2 (S6.18); (3) a larger ego footprint (S6.19); (4) stricter heading-error cuts and the annotation's own axes (S6.20); (5) AB3DMOT without unmatched tracks (S6.21). S6.16 adds one derived quantity, the B0 sweep at M\*'s V2, which neither amendment specifies.
- **Hash locks.** Each amendment was hash-locked by the project before any of its own outputs was computed, in a self-recorded SHA-256 sidecar with no third-party timestamp: A3 at 15:09 EST (SHA-256 prefix 009a0aad) and A4 at 15:11 EST (prefix ab19dd66), on 7 Nov 2026. By file time, the earliest A4 output was written at 15:13 EST and the earliest A3 output at 15:16 EST. Both amendments were written after the verdict of record, after the registered outputs had been read, and after the results of S6.1–S6.11 existed. They are not a registration.
- **What was known when A3 was written.** For the arms of record, progress and V2_exec already exist in the analysis of record (`60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_t*_decide_{arms,v2}.csv`) and were read before A3 was written. They are outputs of record and are reported as such.
- **Labels.** Every result in S6.13–S6.21 carries the label "added after review (amendment A3)" or "added after review (amendment A4)", as in its result file. None is pre-specified by the X3 plan, and none is registered. There is no family-wise error control across these analyses.
- **Rules and integrity.** The common rules of S6.0 apply (frozen modules imported read-only; new files only), except that A4(2) runs loop mode and A4(4) uses the nuScenes items of A1. The run log kept its SHA-256 (8bc6235d…), and the files of `60_RESULTS/c1_av2_v01/` were identical to the baseline manifest at every check `[the authors' decision record]`. One code error in A4(1), an index into the pooled cell, stopped that analysis step; it was fixed and the step re-run, and the failed step stays in its status file `[a4_review/x3_a4_chain_part1_status_v01.json]`.
- **Seeds.** A3 (i) and (iii): [20261201, i, 9]; A3 (ii) and (iv): [20261201, i, 2]; A4 part k: [20261201, i, 10 + k] for the bootstrap and, where power families are computed, [20261202, i, 10 + k], with i = 0, 1, 2 for T1, T3 and AB3DMOT; A4 (4): [20261211, cell, k] (S6.20).

### S6.13 A3 (i): what an infeasible decision costs

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A3)

`[a3_review/x3_a3_i_infeasible_cost_v01.md; A3 §(i)]`

The tables cover every arm of record (M\*, B0, B1, B3, B4, B6, B9, RETUNED, the 21-point B0 sweep, RETUNED-HK1 and Z0) and every X3 arm (the composites of (a), B5, B7, B8, both Q-refit arms, d1, d2 and the fittable learning-curve repeats), on T1 and T3. They are computed from the decision-mode runs by the analysis of record's own definitions (`k8_analyse_v04`: `arm_endpoints`, and `v2_summary` on P_rel = PD7). Every endpoint is a log mean:
- the infeasible-decision rate;
- the progress ratio;
- the mean executed back-off level λ (λ = 1 for a feasible decision);
- V2, relied constraints exceeded at full margin;
- V2_exec, relied constraints exceeded at the executed margin;
- V2_viol;
- the share of decisions with a minimum enforced gap below 1 m.

M\* − arm is paired per log, with a log-bootstrap 95 % interval (B = 4000, seed [20261201, i, 9]), for the progress ratio and for V2_exec. For the arms of record the values were checked against the record's CSVs: 210 values per tracker, largest absolute difference 0.

**Reading, fixed by A3.** A progress-ratio difference below 0.02 means that infeasibility has no progress cost in this leashed replay. An infeasible decision is one at which the planner cannot keep its per-constraint risk statement: Proposition 1 covers feasible decisions only. V2_exec is reported, and arms are not ranked on it.

**Row names** are the result file's. `Mstar` is M\*. `B0a{s}` is B0 with its margin scaled by s, and `B0d{δ′}` is B0 at nominal risk δ′ (the B0 curve of S2.2 and S4(f)). `RETUNED_HK1` is RETUNED-HK1 (B0a8 in every fold). `A_B4_composite`, `A_B6_composite` and `A_B9_composite` are the composites of (a) (S6.2). `X3E1_B5`, `X3E1_B7` and `X3E1_B8` are the alternatives of (e1), and `X3E2_B0_qrefit` and `X3E2_B0_qrefit_ext` the Q-refit arms on the plan grid and on the extended grid (S6.6, S6.11). `X3D_Mstar_d1` and `X3D_Mstar_d2` are M\* at the references d1 and d2 (S6.5). `X3G_n{n}_r{r}` is M\* refitted on n training logs per fold, repeat r (S6.8).

**S6-Table 16. (A3 i) T1: what an infeasible decision costs.**

| arm | infeasible | progress ratio | mean back-off | V2 | V2_exec | V2_viol | min gap < 1 m | M* - arm progress (95 % CI) | M* - arm V2_exec (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|
| Mstar | 0.1864 | 0.9723 | 0.8967 | 0.4909 | 0.5509 | 0.0161 | 0.2959 | - | - |
| B0 | 0.3711 | 0.9609 | 0.7949 | 0.3947 | 0.5153 | 0.0224 | 0.2704 | 0.0115 [0.0085, 0.0145] | 0.0356 [0.0175, 0.0547] |
| B1 | 0.5133 | 0.9568 | 0.7000 | 0.1879 | 0.3752 | 0.0190 | 0.2717 | 0.0156 [0.0124, 0.0187] | 0.1756 [0.1551, 0.1960] |
| B3 | 0.9689 | 0.9744 | 0.1280 | 0.0331 | 0.7455 | 0.0072 | 0.3207 | -0.0021 [-0.0058, 0.0014] | -0.1946 [-0.2217, -0.1668] |
| B4 | 0.2019 | 0.9725 | 0.8885 | 0.5197 | 0.5783 | 0.0260 | 0.2883 | -0.0002 [-0.0030, 0.0026] | -0.0274 [-0.0462, -0.0085] |
| B6 | 0.1653 | 0.9711 | 0.9114 | 0.5013 | 0.5484 | 0.0226 | 0.2874 | 0.0013 [-0.0013, 0.0039] | 0.0025 [-0.0151, 0.0196] |
| B9 | 0.6928 | 0.9552 | 0.5048 | 0.1582 | 0.5266 | 0.0143 | 0.2676 | 0.0171 [0.0141, 0.0200] | 0.0243 [0.0013, 0.0483] |
| RETUNED | 0.4066 | 0.9597 | 0.7706 | 0.3612 | 0.5010 | 0.0218 | 0.2697 | 0.0126 [0.0095, 0.0158] | 0.0499 [0.0312, 0.0687] |
| Z0 | 0.0042 | 0.9941 | 0.9958 | 0.9756 | 0.9756 | 0.0567 | 0.3283 | -0.0218 [-0.0247, -0.0191] | -0.4247 [-0.4457, -0.4030] |
| B0a0.03125 | 0.0373 | 0.9885 | 0.9776 | 0.8937 | 0.8956 | 0.0423 | 0.3122 | -0.0161 [-0.0190, -0.0137] | -0.3447 [-0.3622, -0.3263] |
| B0a0.0625 | 0.0581 | 0.9860 | 0.9658 | 0.8447 | 0.8501 | 0.0392 | 0.3053 | -0.0137 [-0.0164, -0.0112] | -0.2992 [-0.3168, -0.2803] |
| B0a0.125 | 0.0846 | 0.9822 | 0.9501 | 0.7681 | 0.7815 | 0.0350 | 0.3002 | -0.0099 [-0.0126, -0.0074] | -0.2306 [-0.2482, -0.2126] |
| B0a0.25 | 0.1358 | 0.9766 | 0.9230 | 0.6669 | 0.6955 | 0.0303 | 0.2935 | -0.0043 [-0.0070, -0.0017] | -0.1447 [-0.1625, -0.1266] |
| B0a0.333 | 0.1695 | 0.9732 | 0.9059 | 0.6160 | 0.6550 | 0.0283 | 0.2898 | -0.0009 [-0.0034, 0.0015] | -0.1041 [-0.1226, -0.0855] |
| B0a0.5 | 0.2323 | 0.9695 | 0.8743 | 0.5371 | 0.6000 | 0.0265 | 0.2846 | 0.0028 [0.0001, 0.0056] | -0.0491 [-0.0672, -0.0307] |
| B0a1 | 0.3711 | 0.9609 | 0.7949 | 0.3947 | 0.5153 | 0.0224 | 0.2704 | 0.0115 [0.0085, 0.0145] | 0.0356 [0.0175, 0.0547] |
| B0a2 | 0.5250 | 0.9544 | 0.6900 | 0.2538 | 0.4609 | 0.0193 | 0.2755 | 0.0179 [0.0147, 0.0210] | 0.0900 [0.0701, 0.1098] |
| B0a3 | 0.6061 | 0.9519 | 0.6219 | 0.1895 | 0.4458 | 0.0181 | 0.2774 | 0.0204 [0.0174, 0.0234] | 0.1051 [0.0836, 0.1262] |
| B0a4 | 0.6603 | 0.9507 | 0.5701 | 0.1553 | 0.4490 | 0.0170 | 0.2777 | 0.0217 [0.0184, 0.0249] | 0.1018 [0.0798, 0.1227] |
| B0a5 | 0.7010 | 0.9495 | 0.5307 | 0.1322 | 0.4529 | 0.0156 | 0.2835 | 0.0228 [0.0195, 0.0260] | 0.0980 [0.0763, 0.1194] |
| B0a8 | 0.7810 | 0.9495 | 0.4445 | 0.0945 | 0.4686 | 0.0143 | 0.2905 | 0.0228 [0.0191, 0.0263] | 0.0823 [0.0587, 0.1054] |
| B0d0.5 | 0.0042 | 0.9941 | 0.9958 | 0.9756 | 0.9756 | 0.0567 | 0.3283 | -0.0218 [-0.0247, -0.0191] | -0.4247 [-0.4457, -0.4030] |
| B0d0.3 | 0.0765 | 0.9835 | 0.9553 | 0.7959 | 0.8057 | 0.0358 | 0.3022 | -0.0111 [-0.0138, -0.0087] | -0.2548 [-0.2721, -0.2367] |
| B0d0.2 | 0.1404 | 0.9762 | 0.9207 | 0.6595 | 0.6898 | 0.0302 | 0.2927 | -0.0039 [-0.0065, -0.0013] | -0.1389 [-0.1570, -0.1206] |
| B0d0.1 | 0.2714 | 0.9665 | 0.8544 | 0.4950 | 0.5726 | 0.0256 | 0.2809 | 0.0059 [0.0030, 0.0087] | -0.0217 [-0.0395, -0.0035] |
| B0d0.05 | 0.3711 | 0.9609 | 0.7949 | 0.3947 | 0.5153 | 0.0224 | 0.2704 | 0.0115 [0.0085, 0.0145] | 0.0356 [0.0175, 0.0547] |
| B0d0.02 | 0.4682 | 0.9572 | 0.7313 | 0.3027 | 0.4761 | 0.0202 | 0.2683 | 0.0151 [0.0121, 0.0181] | 0.0748 [0.0555, 0.0942] |
| B0d0.01 | 0.5250 | 0.9544 | 0.6900 | 0.2538 | 0.4608 | 0.0193 | 0.2755 | 0.0179 [0.0147, 0.0211] | 0.0901 [0.0702, 0.1099] |
| B0d0.005 | 0.5701 | 0.9519 | 0.6552 | 0.2197 | 0.4484 | 0.0187 | 0.2780 | 0.0205 [0.0172, 0.0238] | 0.1025 [0.0813, 0.1230] |
| B0d0.001 | 0.6375 | 0.9515 | 0.5936 | 0.1676 | 0.4429 | 0.0177 | 0.2724 | 0.0209 [0.0179, 0.0240] | 0.1080 [0.0865, 0.1292] |
| RETUNED_HK1 | 0.7810 | 0.9495 | 0.4445 | 0.0945 | 0.4686 | 0.0143 | 0.2905 | 0.0228 [0.0191, 0.0263] | 0.0823 [0.0587, 0.1054] |
| A_B4_composite | 0.9106 | 0.9567 | 0.2802 | 0.0469 | 0.5472 | 0.0097 | 0.3022 | 0.0157 [0.0118, 0.0194] | 0.0037 [-0.0218, 0.0286] |
| A_B6_composite | 0.6226 | 0.9532 | 0.5610 | 0.1531 | 0.4752 | 0.0108 | 0.2763 | 0.0191 [0.0161, 0.0221] | 0.0757 [0.0519, 0.0987] |
| A_B9_composite | 0.9724 | 0.9747 | 0.1248 | 0.0021 | 0.7121 | 0.0009 | 0.3188 | -0.0023 [-0.0063, 0.0012] | -0.1612 [-0.1883, -0.1331] |
| X3E1_B5 | 0.1668 | 0.9714 | 0.9054 | 0.4914 | 0.5423 | 0.0244 | 0.2899 | 0.0010 [-0.0019, 0.0037] | 0.0086 [-0.0091, 0.0256] |
| X3E1_B8 | 0.2822 | 0.9669 | 0.8369 | 0.2328 | 0.3536 | 0.0130 | 0.2853 | 0.0055 [0.0034, 0.0075] | 0.1972 [0.1823, 0.2124] |
| X3E1_B7 | 0.1538 | 0.9761 | 0.9117 | 0.4830 | 0.5375 | 0.0202 | 0.2957 | -0.0037 [-0.0061, -0.0016] | 0.0134 [0.0023, 0.0251] |
| X3E2_B0_qrefit | 0.2709 | 0.9661 | 0.8541 | 0.4582 | 0.5374 | 0.0284 | 0.2824 | 0.0063 [0.0033, 0.0092] | 0.0135 [-0.0048, 0.0321] |
| X3E2_B0_qrefit_ext | 0.2299 | 0.9685 | 0.8760 | 0.4971 | 0.5591 | 0.0302 | 0.2855 | 0.0039 [0.0008, 0.0069] | -0.0082 [-0.0264, 0.0106] |
| X3D_Mstar_d1 | 0.1861 | 0.9724 | 0.8970 | 0.4908 | 0.5512 | 0.0161 | 0.2960 | -0.0000 [-0.0003, 0.0002] | -0.0004 [-0.0012, 0.0004] |
| X3D_Mstar_d2 | 0.1863 | 0.9721 | 0.8970 | 0.4908 | 0.5511 | 0.0161 | 0.2961 | 0.0002 [-0.0002, 0.0006] | -0.0002 [-0.0012, 0.0008] |
| X3G_n100_r0 | 0.2323 | 0.9687 | 0.8649 | 0.4466 | 0.5319 | 0.0161 | 0.2922 | 0.0036 [0.0021, 0.0053] | 0.0190 [0.0123, 0.0259] |
| X3G_n100_r1 | 0.2028 | 0.9702 | 0.8858 | 0.4587 | 0.5292 | 0.0171 | 0.2924 | 0.0022 [0.0005, 0.0038] | 0.0217 [0.0153, 0.0282] |
| X3G_n100_r2 | 0.2214 | 0.9691 | 0.8735 | 0.4581 | 0.5361 | 0.0154 | 0.2905 | 0.0032 [0.0014, 0.0049] | 0.0148 [0.0085, 0.0211] |
| X3G_n200_r0 | 0.1955 | 0.9720 | 0.8916 | 0.4772 | 0.5424 | 0.0156 | 0.2952 | 0.0003 [-0.0008, 0.0014] | 0.0085 [0.0036, 0.0132] |
| X3G_n200_r1 | 0.1911 | 0.9722 | 0.8949 | 0.4805 | 0.5451 | 0.0157 | 0.2937 | 0.0001 [-0.0012, 0.0012] | 0.0057 [0.0013, 0.0104] |
| X3G_n200_r2 | 0.1980 | 0.9714 | 0.8902 | 0.4802 | 0.5452 | 0.0163 | 0.2951 | 0.0010 [-0.0004, 0.0023] | 0.0057 [0.0013, 0.0104] |
| X3G_n25_r1 | 0.4316 | 0.9589 | 0.7323 | 0.2458 | 0.4425 | 0.0174 | 0.2805 | 0.0134 [0.0106, 0.0163] | 0.1084 [0.0902, 0.1262] |
| X3G_n50_r0 | 0.3018 | 0.9646 | 0.8146 | 0.3977 | 0.5185 | 0.0177 | 0.2855 | 0.0077 [0.0057, 0.0100] | 0.0324 [0.0213, 0.0435] |
| X3G_n50_r1 | 0.2690 | 0.9641 | 0.8412 | 0.3850 | 0.4909 | 0.0171 | 0.2832 | 0.0082 [0.0057, 0.0108] | 0.0599 [0.0492, 0.0705] |
| X3G_n50_r2 | 0.2797 | 0.9637 | 0.8344 | 0.3821 | 0.4946 | 0.0163 | 0.2858 | 0.0086 [0.0065, 0.0109] | 0.0563 [0.0456, 0.0668] |

**S6-Table 17. (A3 i) T3: the same.**

| arm | infeasible | progress ratio | mean back-off | V2 | V2_exec | V2_viol | min gap < 1 m | M* - arm progress (95 % CI) | M* - arm V2_exec (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|
| Mstar | 0.2466 | 0.9731 | 0.8585 | 0.4963 | 0.5805 | 0.0176 | 0.2967 | - | - |
| B0 | 0.8575 | 0.9652 | 0.3020 | 0.0718 | 0.6042 | 0.0131 | 0.2923 | 0.0079 [0.0048, 0.0113] | -0.0237 [-0.0455, -0.0010] |
| B1 | 0.6658 | 0.9679 | 0.4953 | 0.2282 | 0.5754 | 0.0238 | 0.2840 | 0.0052 [0.0024, 0.0084] | 0.0051 [-0.0160, 0.0268] |
| B3 | 0.9406 | 0.9725 | 0.1819 | 0.0296 | 0.6783 | 0.0087 | 0.3083 | 0.0006 [-0.0027, 0.0040] | -0.0978 [-0.1213, -0.0741] |
| B4 | 0.3152 | 0.9694 | 0.8018 | 0.5725 | 0.6425 | 0.0491 | 0.2878 | 0.0037 [0.0015, 0.0060] | -0.0620 [-0.0791, -0.0440] |
| B6 | 0.2286 | 0.9734 | 0.8657 | 0.5286 | 0.5969 | 0.0228 | 0.2950 | -0.0003 [-0.0017, 0.0012] | -0.0164 [-0.0286, -0.0044] |
| B9 | 0.6629 | 0.9587 | 0.5338 | 0.1774 | 0.5230 | 0.0180 | 0.2693 | 0.0144 [0.0118, 0.0172] | 0.0575 [0.0338, 0.0811] |
| RETUNED | 0.6108 | 0.9600 | 0.5800 | 0.3160 | 0.5677 | 0.0282 | 0.2778 | 0.0131 [0.0104, 0.0161] | 0.0128 [-0.0070, 0.0326] |
| Z0 | 0.0024 | 0.9956 | 0.9976 | 0.9785 | 0.9785 | 0.0531 | 0.3307 | -0.0225 [-0.0251, -0.0200] | -0.3980 [-0.4197, -0.3760] |
| B0a0.03125 | 0.3287 | 0.9666 | 0.7943 | 0.6154 | 0.6797 | 0.0459 | 0.2848 | 0.0065 [0.0043, 0.0088] | -0.0992 [-0.1149, -0.0830] |
| B0a0.0625 | 0.4476 | 0.9632 | 0.7128 | 0.4885 | 0.6157 | 0.0382 | 0.2781 | 0.0099 [0.0075, 0.0124] | -0.0352 [-0.0528, -0.0170] |
| B0a0.125 | 0.5647 | 0.9601 | 0.6184 | 0.3605 | 0.5717 | 0.0309 | 0.2765 | 0.0130 [0.0103, 0.0159] | 0.0088 [-0.0102, 0.0274] |
| B0a0.25 | 0.6936 | 0.9592 | 0.5099 | 0.2349 | 0.5578 | 0.0220 | 0.2795 | 0.0139 [0.0110, 0.0170] | 0.0227 [0.0026, 0.0433] |
| B0a0.333 | 0.7324 | 0.9596 | 0.4656 | 0.1915 | 0.5566 | 0.0200 | 0.2792 | 0.0136 [0.0105, 0.0168] | 0.0239 [0.0032, 0.0449] |
| B0a0.5 | 0.7806 | 0.9613 | 0.4040 | 0.1356 | 0.5630 | 0.0167 | 0.2874 | 0.0118 [0.0087, 0.0152] | 0.0175 [-0.0034, 0.0386] |
| B0a1 | 0.8575 | 0.9652 | 0.3020 | 0.0718 | 0.6042 | 0.0131 | 0.2923 | 0.0079 [0.0048, 0.0113] | -0.0237 [-0.0455, -0.0010] |
| B0a2 | 0.9217 | 0.9703 | 0.2151 | 0.0391 | 0.6548 | 0.0106 | 0.3026 | 0.0029 [-0.0003, 0.0062] | -0.0743 [-0.0972, -0.0507] |
| B0a3 | 0.9469 | 0.9731 | 0.1688 | 0.0297 | 0.6975 | 0.0086 | 0.3105 | 0.0000 [-0.0033, 0.0033] | -0.1170 [-0.1400, -0.0936] |
| B0a4 | 0.9567 | 0.9765 | 0.1404 | 0.0260 | 0.7295 | 0.0077 | 0.3162 | -0.0034 [-0.0067, -0.0000] | -0.1490 [-0.1713, -0.1258] |
| B0a5 | 0.9657 | 0.9786 | 0.1203 | 0.0229 | 0.7498 | 0.0065 | 0.3187 | -0.0055 [-0.0087, -0.0022] | -0.1693 [-0.1919, -0.1468] |
| B0a8 | 0.9770 | 0.9825 | 0.0897 | 0.0145 | 0.7903 | 0.0050 | 0.3238 | -0.0094 [-0.0126, -0.0063] | -0.2098 [-0.2317, -0.1881] |
| B0d0.5 | 0.0024 | 0.9956 | 0.9976 | 0.9785 | 0.9785 | 0.0531 | 0.3307 | -0.0225 [-0.0251, -0.0200] | -0.3980 [-0.4197, -0.3760] |
| B0d0.3 | 0.5275 | 0.9602 | 0.6477 | 0.3977 | 0.5835 | 0.0332 | 0.2747 | 0.0129 [0.0102, 0.0160] | -0.0030 [-0.0221, 0.0155] |
| B0d0.2 | 0.7004 | 0.9590 | 0.5028 | 0.2281 | 0.5577 | 0.0216 | 0.2801 | 0.0141 [0.0112, 0.0171] | 0.0228 [0.0023, 0.0436] |
| B0d0.1 | 0.8012 | 0.9606 | 0.3745 | 0.1143 | 0.5753 | 0.0154 | 0.2893 | 0.0125 [0.0092, 0.0158] | 0.0052 [-0.0162, 0.0267] |
| B0d0.05 | 0.8575 | 0.9652 | 0.3020 | 0.0718 | 0.6042 | 0.0131 | 0.2923 | 0.0079 [0.0048, 0.0113] | -0.0237 [-0.0455, -0.0010] |
| B0d0.02 | 0.9041 | 0.9678 | 0.2449 | 0.0475 | 0.6351 | 0.0114 | 0.2950 | 0.0054 [0.0020, 0.0088] | -0.0546 [-0.0776, -0.0310] |
| B0d0.01 | 0.9217 | 0.9703 | 0.2151 | 0.0391 | 0.6548 | 0.0106 | 0.3026 | 0.0029 [-0.0003, 0.0062] | -0.0743 [-0.0972, -0.0507] |
| B0d0.005 | 0.9363 | 0.9710 | 0.1909 | 0.0339 | 0.6779 | 0.0097 | 0.3067 | 0.0021 [-0.0012, 0.0054] | -0.0974 [-0.1201, -0.0740] |
| B0d0.001 | 0.9530 | 0.9751 | 0.1528 | 0.0272 | 0.7159 | 0.0079 | 0.3131 | -0.0019 [-0.0052, 0.0014] | -0.1354 [-0.1581, -0.1124] |
| RETUNED_HK1 | 0.9770 | 0.9825 | 0.0897 | 0.0145 | 0.7903 | 0.0050 | 0.3238 | -0.0094 [-0.0126, -0.0063] | -0.2098 [-0.2317, -0.1881] |
| A_B4_composite | 0.8647 | 0.9684 | 0.2909 | 0.0407 | 0.5892 | 0.0115 | 0.2902 | 0.0047 [0.0016, 0.0078] | -0.0087 [-0.0328, 0.0162] |
| A_B6_composite | 0.4862 | 0.9591 | 0.7027 | 0.2079 | 0.4307 | 0.0148 | 0.2886 | 0.0140 [0.0117, 0.0165] | 0.1498 [0.1330, 0.1662] |
| A_B9_composite | 0.9715 | 0.9771 | 0.1277 | 0.0056 | 0.7094 | 0.0031 | 0.3196 | -0.0040 [-0.0072, -0.0007] | -0.1290 [-0.1540, -0.1035] |
| X3E1_B5 | 0.2395 | 0.9721 | 0.8540 | 0.5293 | 0.5973 | 0.0292 | 0.2922 | 0.0010 [-0.0008, 0.0029] | -0.0168 [-0.0310, -0.0025] |
| X3E1_B8 | 0.5074 | 0.9641 | 0.6835 | 0.2240 | 0.4383 | 0.0147 | 0.2786 | 0.0090 [0.0069, 0.0112] | 0.1422 [0.1250, 0.1595] |
| X3E1_B7 | 0.2634 | 0.9740 | 0.8371 | 0.5005 | 0.5924 | 0.0249 | 0.2920 | -0.0009 [-0.0025, 0.0008] | -0.0119 [-0.0237, 0.0003] |
| X3E2_B0_qrefit | 0.8136 | 0.9623 | 0.3633 | 0.1073 | 0.5724 | 0.0141 | 0.2924 | 0.0108 [0.0076, 0.0143] | 0.0081 [-0.0130, 0.0298] |
| X3E2_B0_qrefit_ext | 0.7835 | 0.9616 | 0.4007 | 0.1315 | 0.5593 | 0.0146 | 0.2927 | 0.0116 [0.0084, 0.0149] | 0.0211 [0.0000, 0.0420] |
| X3D_Mstar_d1 | 0.2461 | 0.9730 | 0.8586 | 0.4968 | 0.5808 | 0.0177 | 0.2966 | 0.0001 [-0.0001, 0.0003] | -0.0004 [-0.0009, 0.0001] |
| X3D_Mstar_d2 | 0.2460 | 0.9731 | 0.8587 | 0.4974 | 0.5805 | 0.0176 | 0.2967 | 0.0000 [-0.0005, 0.0006] | -0.0000 [-0.0013, 0.0013] |
| X3G_n100_r0 | 0.3010 | 0.9696 | 0.8196 | 0.4526 | 0.5664 | 0.0181 | 0.2961 | 0.0035 [0.0019, 0.0052] | 0.0141 [0.0079, 0.0205] |
| X3G_n100_r1 | 0.2919 | 0.9706 | 0.8278 | 0.4702 | 0.5740 | 0.0179 | 0.2951 | 0.0026 [0.0009, 0.0043] | 0.0065 [-0.0000, 0.0131] |
| X3G_n100_r2 | 0.3025 | 0.9691 | 0.8198 | 0.4645 | 0.5742 | 0.0166 | 0.2960 | 0.0040 [0.0023, 0.0058] | 0.0063 [0.0005, 0.0121] |
| X3G_n200_r0 | 0.2641 | 0.9712 | 0.8453 | 0.4824 | 0.5766 | 0.0177 | 0.2958 | 0.0020 [0.0008, 0.0031] | 0.0039 [-0.0005, 0.0083] |
| X3G_n200_r1 | 0.2538 | 0.9723 | 0.8529 | 0.4920 | 0.5816 | 0.0182 | 0.2962 | 0.0008 [-0.0001, 0.0018] | -0.0011 [-0.0053, 0.0032] |
| X3G_n200_r2 | 0.2608 | 0.9719 | 0.8477 | 0.4899 | 0.5799 | 0.0184 | 0.2959 | 0.0012 [-0.0000, 0.0025] | 0.0006 [-0.0035, 0.0047] |
| X3G_n50_r0 | 0.3651 | 0.9658 | 0.7735 | 0.4060 | 0.5524 | 0.0174 | 0.2929 | 0.0073 [0.0052, 0.0096] | 0.0280 [0.0181, 0.0376] |
| X3G_n50_r1 | 0.3762 | 0.9669 | 0.7637 | 0.3992 | 0.5572 | 0.0165 | 0.2924 | 0.0062 [0.0043, 0.0083] | 0.0233 [0.0120, 0.0343] |
| X3G_n50_r2 | 0.3764 | 0.9653 | 0.7657 | 0.3845 | 0.5435 | 0.0165 | 0.2910 | 0.0078 [0.0055, 0.0103] | 0.0370 [0.0260, 0.0479] |

**Result.** Against M\*, the progress ratio differs by less than 0.02 for every arm except two groups. Z0 (and B0d0.5, which equals it) makes more progress than M\*, by 0.0218 (T1) and 0.0225 (T3). On T1 only, the conservative B0 sweep points B0a3, B0a4, B0a5, B0a8 (= RETUNED_HK1), B0d0.005 and B0d0.001 make less progress than M\*, by 0.0204–0.0228. No difference exceeds 0.023 in absolute value, so by A3's reading infeasibility costs almost no progress in this leashed replay. M\* keeps its designed margin (λ = 1) in 0.814 (T1) and 0.753 (T3) of decisions (S6-Table 11).

### S6.14 A3 (ii) and (iv): the partition screen of the matched arms, and multiplicity across partitions

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A3)

`[a3_review/x3_a3_ii_iv_partitions_v01.md; a3_review/x3_a3_ii_check_t1_v01.json; a3_review/x3_a3_ii_check_t3_v01.json; A3 §(ii), §(iv)]`

**(ii)** The screen of (b), with its bins, populations and flag rule (one-sided simultaneous 0.95 over each partition's evaluable cells; seeds [20261201, i, 2]; B = 4000), applied to re-runs with partition counts of the matched arms of (a) (B6 on T1 and T3, RETUNED-HK1 on T1), the grid points of (a) that make up those composites or pass the registered screen in sample, and B8. Each re-run was checked equal to its earlier run, and its partition sums equal to its counts. RETUNED-HK1 on T1 is B0a8 in every fold, rebuilt with the X3 runner, because no partition counts of record exist for it. **(iv)** The same flags at the per-partition one-sided level 1 − 0.05/7 = 0.992857, for every arm.

In the (ii) tables each entry lists the flagged cells of one partition as bin|axis, for P_rel / P_near / P_ip ('-': none); a bar inside an entry is escaped for typesetting. In the (iv) tables each entry is the number of flagged cells summed over P1–P7, with P0 in brackets. `M* (b)` is M\*'s row of (b) (S6-Table 3); `B4@δ′`, `B6@δ′` and `B9@δ′` are the refits of (a) at level δ′; `X3E1_B8` is B8; `A_B6_composite` is the B6 composite of (a); `B0a8` is the B0 sweep point ×8 of record, and `RETUNED_HK1` the same rule rebuilt with the X3 runner as RETUNED-HK1.

**S6-Table 18. (A3 ii) T1: flagged partition cells, P_rel / P_near / P_ip.**

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| M* (b) | - / - / - | [0.5,3)\|long / - / - | - / - / - | 1-2\|lat / - / - | [0.4,0.5)\|long, [0.4,0.5)\|lat / - / - | - / - / - | 1-10\|lat / - / - | - / - / - |
| B0a8 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B4@0.01 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B6@0.005 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B6@0.01 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B6@0.015 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B9@0.02 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| X3E1_B8 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| A_B6_composite | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| RETUNED_HK1 (B0a8 in every fold) | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |

**S6-Table 19. (A3 iv) T1: flagged-cell counts, P1–P7 total (P0) per population, at 0.95 and at 1 − 0.05/7.**

| arm | P_rel 0.95 | P_rel corr. | P_near 0.95 | P_near corr. | P_ip 0.95 | P_ip corr. |
|---|---|---|---|---|---|---|
| Mstar | 5 (0) | 4 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B0 | 7 (0) | 4 (0) | 0 (0) | 0 (0) | 4 (1) | 0 (0) |
| B1 | 1 (0) | 1 (0) | 0 (0) | 0 (0) | 1 (0) | 0 (0) |
| B3 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B4 | 22 (2) | 14 (2) | 7 (0) | 5 (0) | 11 (2) | 3 (1) |
| B6 | 13 (0) | 13 (0) | 2 (0) | 2 (0) | 0 (0) | 0 (0) |
| B9 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B0a8 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B4@0.01 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B6@0.005 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B6@0.01 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B6@0.015 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B9@0.02 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| X3E1_B8 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| A_B6_composite | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| RETUNED_HK1 (B0a8 in every fold) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**S6-Table 20. (A3 ii) T3: flagged partition cells, P_rel / P_near / P_ip.**

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| M* (b) | 20-40 m\|lat, >=40 m\|lat / - / - | - / - / - | - / - / - | 1-2\|lat / - / - | [0.4,0.5)\|long, [0.4,0.5)\|lat / - / - | - / - / - | 1-10\|lat, 11-50\|lat / - / - | - / - / - |
| B6@0.01 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B6@0.015 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| B9@0.02 | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| X3E1_B8 | - / - / - | - / - / - | >=8\|long / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |
| A_B6_composite | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - | - / - / - |

**S6-Table 21. (A3 iv) T3: flagged-cell counts, P1–P7 total (P0) per population, at 0.95 and at 1 − 0.05/7.**

| arm | P_rel 0.95 | P_rel corr. | P_near 0.95 | P_near corr. | P_ip 0.95 | P_ip corr. |
|---|---|---|---|---|---|---|
| Mstar | 5 (2) | 3 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B0 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B1 | 1 (0) | 1 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B3 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B4 | 24 (3) | 20 (3) | 18 (1) | 14 (1) | 20 (2) | 18 (2) |
| B6 | 14 (2) | 12 (2) | 1 (0) | 0 (0) | 1 (0) | 0 (0) |
| B9 | 1 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B6@0.01 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B6@0.015 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| B9@0.02 | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| X3E1_B8 | 1 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |
| A_B6_composite | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) | 0 (0) |

**S6-Table 22. (A3 ii) AB3DMOT (descriptive), M\*: flagged partition cells, P_rel / P_near / P_ip.**

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| M* (b) | <20 m\|lat, 20-40 m\|long / <20 m\|long / - | [0.5,3)\|long, [0.5,3)\|lat / [0.5,3)\|long / - | [5.5,8)\|long / - / - | 6-10\|long, 6-10\|lat, >10\|long, >10\|lat / - / - | [0.4,0.5)\|long, [0.4,0.5)\|lat / [0.4,0.5)\|long, [0.4,0.5)\|lat / - | <1\|long, [1,5)\|long, [1,5)\|lat / <1\|long / - | 1-10\|long, >200\|long / - / - | MIA\|long, MIA\|lat / - / - |

**S6-Table 23. (A3 iv) AB3DMOT (descriptive), M\*: flagged-cell counts, P1–P7 total (P0) per population, at 0.95 and at 1 − 0.05/7.**

| arm | P_rel 0.95 | P_rel corr. | P_near 0.95 | P_near corr. | P_ip 0.95 | P_ip corr. |
|---|---|---|---|---|---|---|
| Mstar | 16 (2) | 11 (2) | 4 (1) | 1 (0) | 0 (0) | 0 (0) |

**Result.** No matched arm of (a), no grid point of (a) and no B8 run is flagged on any partition, on either tracker, except B8 on T3 in one P_rel cell (track length ≥ 8, longitudinal). With the level corrected across the seven partitions, M\* keeps 4 of its 5 P_rel flags on T1 and 3 of 5 on T3, with none left in P0 on T3; on AB3DMOT it keeps 11 of 16 on P_rel and 1 of 4 on P_near.

### S6.15 A3 (iii): M\*'s exceedance on its own calibration items

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A3)

`[a3_review/x3_a3_iii_own_items_v01.md; A3 §(iii)]`

This is the quantity the certificate of Propositions 3–4 is about. The items are those of record: every separating axis at the reference pose, not the relied records. Each held-out fold's thresholds (the fits of record within Argoverse 2) are applied to that fold's items, and an item exceeds when U = D/sd > c. The strata are the own-threshold L0 strata (an item's threshold is its stratum's own fit) by in-path part, with the check times pooled. The rate is log-weighted, with one-sided simultaneous sup-t flags at 0.95 over the evaluable strata (≥ 39 logs); B = 4000, seed [20261201, i, 9]. **Reading, fixed by A3:** a consistency check of the theory on the data, not a test of the planner-facing claim.

Verbatim from the result file, with its bootstrap intervals in brackets:

**T1**

- items 947306; evaluable own-threshold strata 93; flagged 0: none
- pooled own-threshold items: 0.0429 [0.0402, 0.0459] (940940 items); fallback items: share 0.007, pooled 0.0396 [0.0255, 0.0567]
- fallback by level (share of items): {"0": 0.993, "1": 0.005, "2": 0.001, "3": 0.0}; pooled rate by level: {"1": 0.0379, "2": 0.0504, "3": 0.0}
- largest stratum estimate: large|<20|long|turning|not_inpath 0.0714 (UB 0.1679)

**T3**

- items 947746; evaluable own-threshold strata 92; flagged 0: none
- pooled own-threshold items: 0.0418 [0.0392, 0.0445] (941556 items); fallback items: share 0.007, pooled 0.0429 [0.0280, 0.0599]
- fallback by level (share of items): {"0": 0.993, "1": 0.005, "2": 0.001, "3": 0.0}; pooled rate by level: {"1": 0.0444, "2": 0.0285, "3": 0.0887}
- largest stratum estimate: car|<20|long|turning|inpath 0.0567 (UB 0.1031)

**Result.** No own-threshold stratum is flagged: 0 of 93 on T1 and 0 of 92 on T3. The pooled exceedance on own-threshold items is 0.0429 (T1) and 0.0418 (T3), and 0.7 % of the items are in fallback strata.

### S6.16 The B0 sweep at M\*'s V2 (added, with A3's outputs)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A3)

`[a3_review/x3_a3_sweep_at_Mstar_V2_v01.md]`

This computation is not one of A3's specified analyses, so it is marked *added*. It reads main-text Fig. 4 from the record's CSV values (P_rel V2 and infeasible rate per sweep point), sorted by V2, by linear interpolation at M\*'s V2. Verbatim from the result file:

- T1: M* V2 0.4909, M* infeasible 0.1864; sweep infeasible at that V2 = **0.2755** (between B0d0.05 V2 0.3947 / 0.3711 and B0d0.1 V2 0.4950 / 0.2714)
- T3: M* V2 0.4963, M* infeasible 0.2466; sweep infeasible at that V2 = **0.4403** (between B0a0.0625 V2 0.4885 / 0.4476 and B0a0.03125 V2 0.6154 / 0.3287)

At M\*'s V2, scaling the raw covariance is therefore infeasible in about 0.28 (T1) and 0.44 (T3) of decisions, against M\*'s 0.186 and 0.247.

### S6.17 A4 (1): matched validity on a neutral screen

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

`[a4_review/x3_a4_1_neutral_v01.md; a4_review/x3_a4_checks_v01.json; A4 §(1)]`

- **The neutral screen.** An arm passes on a tracker when no cell of P1–P7 of (b) is flagged in P_rel, P_near or P_ip (one-sided simultaneous 0.95 per partition and population; cells evaluable with ≥ 39 logs) and HK1c holds on each population (pooled upper bound at 0.995 ≤ 0.08; the pooled cell uses no partition). There is no power floor; each point's number of evaluable partition cells is reported beside its status.
- **Families.** M\* refitted at δ′; B4, B6 and B9 at δ′, reusing (a)'s refits; and the B0 curve, re-run with partition counts.
- **Grid.** δ′ ∈ {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005}, and the B0 curve's 21 points.
- **Selection.** Cross-fitted as in (a): per held-out fold, the least conservative point that passes on the other four folds. If no point qualifies, the family has "no matched point" and is reported with its in-sample best point; no conservative point is substituted.
- **Contrast.** M\* − composite in infeasible-decision rate, paired per log, with a 95 % interval, given only when both composites pass.
- **Seeds and checks.** Seeds [20261201, i, 11] / [20261202, i, 11]; B = 4000. Every re-run with partition counts was checked against the corresponding run of record or of (a), and every check passed. "n.e." marks a population that is not evaluable.

**S6-Table 24. (A4 1) T1: matched validity on the neutral screen, per family** (per-fold choice; composite status on the neutral and on the registered screen; endpoints of the composite; M\* − composite).

| family | per-fold choice | result | in-sample best | composite neutral | composite registered | infeasible | progress | mean back-off | V2_exec | M* - composite infeasible (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | matched | Mstar@0.03 | True | Valid | 0.2603 | 0.9657 | 0.8480 | 0.4480 | - |
| B4 | B4@0.015, B4@0.02, B4@0.02, B4@0.015, B4@0.015 | matched | B4@0.015 | True | flagged | 0.5327 | 0.9537 | 0.6836 | 0.4295 | -0.2723 [-0.2992, -0.2457] |
| B6 | B6@0.02, B6@0.02, B6@0.02, B6@0.02, B6@0.02 | matched | B6@0.02 | True | flagged | 0.4926 | 0.9554 | 0.6974 | 0.4607 | -0.2323 [-0.2579, -0.2075] |
| B9 | B9@0.05, B9@0.05, B9@0.05, B9@0.04, B9@0.05 | matched | B9@0.05 | True | flagged | 0.6998 | 0.9555 | 0.4987 | 0.5256 | -0.4395 [-0.4649, -0.4146] |
| B0 | B0d0.005, B0a2, B0a2, B0d0.005, B0a3 | matched | B0d0.005 | True | flagged | 0.5624 | 0.9522 | 0.6615 | 0.4538 | -0.3021 [-0.3296, -0.2753] |

**S6-Table 25. (A4 1) T1: every grid point** (in sample, all 375 logs: neutral pass, flagged cells, HK1c by population with its upper bound, evaluable partition cells; endpoints).

| point | neutral pass | flagged cells | HK1c P_rel / P_near / P_ip (UB) | evaluable cells | infeasible | progress | mean back-off | V2_exec |
|---|---|---|---|---|---|---|---|---|
| Mstar@0.05 | False | 5 | True (0.048) / True (0.047) / True (0.054) | 154 | 0.1864 | 0.9723 | 0.8967 | 0.5509 |
| Mstar@0.04 | False | 3 | True (0.038) / True (0.036) / True (0.041) | 154 | 0.2181 | 0.9687 | 0.8762 | 0.5024 |
| Mstar@0.03 | True | 0 | True (0.029) / True (0.027) / True (0.033) | 154 | 0.2603 | 0.9657 | 0.8480 | 0.4480 |
| Mstar@0.02 | True | 0 | True (0.018) / True (0.016) / True (0.020) | 153 | 0.3429 | 0.9599 | 0.7902 | 0.4088 |
| Mstar@0.015 | True | 0 | True (0.013) / True (0.012) / True (0.018) | 153 | 0.3809 | 0.9570 | 0.7639 | 0.3760 |
| Mstar@0.01 | True | 0 | True (0.008) / True (0.010) / True (0.010) | 152 | 0.5059 | 0.9547 | 0.6811 | 0.3733 |
| Mstar@0.005 | True | 0 | True (0.003) / True (0.006) / True (0.002) | 145 | 0.8330 | 0.9551 | 0.3676 | 0.4980 |
| B4@0.05 | False | 39 | True (0.059) / True (0.046) / False (0.098) | 154 | 0.2019 | 0.9725 | 0.8885 | 0.5783 |
| B4@0.04 | False | 16 | True (0.047) / True (0.038) / False (0.080) | 154 | 0.2645 | 0.9669 | 0.8562 | 0.5312 |
| B4@0.03 | False | 8 | True (0.034) / True (0.032) / True (0.060) | 153 | 0.3523 | 0.9630 | 0.8048 | 0.4836 |
| B4@0.02 | False | 1 | True (0.022) / True (0.024) / True (0.041) | 153 | 0.4750 | 0.9574 | 0.7250 | 0.4393 |
| B4@0.015 | True | 0 | True (0.016) / True (0.018) / True (0.031) | 152 | 0.5677 | 0.9526 | 0.6576 | 0.4251 |
| B4@0.01 | True | 0 | True (0.010) / True (0.015) / True (0.017) | 148 | 0.6951 | 0.9495 | 0.5367 | 0.4457 |
| B4@0.005 | True | 0 | True (0.003) / True (0.009) / True (0.005) | 137 | 0.9106 | 0.9567 | 0.2802 | 0.5472 |
| B6@0.05 | False | 15 | True (0.053) / True (0.052) / True (0.062) | 153 | 0.1653 | 0.9711 | 0.9114 | 0.5484 |
| B6@0.04 | False | 8 | True (0.042) / True (0.042) / True (0.050) | 153 | 0.2337 | 0.9660 | 0.8790 | 0.4984 |
| B6@0.03 | False | 2 | True (0.031) / True (0.032) / True (0.040) | 153 | 0.3327 | 0.9615 | 0.8236 | 0.4528 |
| B6@0.02 | True | 0 | True (0.020) / True (0.018) / True (0.024) | 153 | 0.4926 | 0.9554 | 0.6974 | 0.4607 |
| B6@0.015 | True | 0 | True (0.014) / True (0.014) / True (0.021) | 152 | 0.5572 | 0.9543 | 0.6205 | 0.4589 |
| B6@0.01 | True | 0 | True (0.009) / True (0.010) / True (0.011) | 150 | 0.6784 | 0.9539 | 0.5271 | 0.4763 |
| B6@0.005 | True | 0 | True (0.003) / True (0.008) / True (0.002) | 139 | 0.8631 | 0.9567 | 0.3368 | 0.5082 |
| B9@0.05 | True | 0 | True (0.014) / True (0.008) / True (0.030) | 153 | 0.6928 | 0.9552 | 0.5048 | 0.5266 |
| B9@0.04 | True | 0 | True (0.011) / True (0.007) / True (0.020) | 152 | 0.7261 | 0.9538 | 0.4725 | 0.5226 |
| B9@0.03 | True | 0 | True (0.008) / True (0.005) / True (0.015) | 152 | 0.7659 | 0.9538 | 0.4328 | 0.5284 |
| B9@0.02 | True | 0 | True (0.005) / True (0.004) / True (0.008) | 150 | 0.8216 | 0.9571 | 0.3762 | 0.5435 |
| B9@0.015 | True | 0 | True (0.004) / True (0.004) / True (0.004) | 148 | 0.8546 | 0.9575 | 0.3389 | 0.5511 |
| B9@0.01 | True | 0 | True (0.002) / True (0.004) / True (0.002) | 141 | 0.8956 | 0.9604 | 0.2853 | 0.5650 |
| B9@0.005 | False | 0 | True (0.000) / n.e. / True (0.000) | 84 | 0.9724 | 0.9747 | 0.1248 | 0.7121 |
| B0d0.5 | False | 155 | False (0.505) / False (0.505) / False (0.496) | 155 | 0.0042 | 0.9941 | 0.9958 | 0.9756 |
| B0a0.03125 | False | 146 | False (0.196) / False (0.181) / False (0.276) | 155 | 0.0373 | 0.9885 | 0.9776 | 0.8956 |
| B0a0.0625 | False | 137 | False (0.157) / False (0.137) / False (0.234) | 155 | 0.0581 | 0.9860 | 0.9658 | 0.8501 |
| B0d0.3 | False | 122 | False (0.130) / False (0.107) / False (0.200) | 155 | 0.0765 | 0.9835 | 0.9553 | 0.8057 |
| B0a0.125 | False | 111 | False (0.120) / False (0.097) / False (0.187) | 155 | 0.0846 | 0.9822 | 0.9501 | 0.7815 |
| B0a0.25 | False | 80 | False (0.088) / True (0.070) / False (0.143) | 155 | 0.1358 | 0.9766 | 0.9230 | 0.6955 |
| B0d0.2 | False | 77 | False (0.086) / True (0.068) / False (0.139) | 155 | 0.1404 | 0.9762 | 0.9207 | 0.6898 |
| B0a0.333 | False | 70 | True (0.076) / True (0.060) / False (0.122) | 155 | 0.1695 | 0.9732 | 0.9059 | 0.6550 |
| B0a0.5 | False | 43 | True (0.061) / True (0.049) / False (0.103) | 154 | 0.2323 | 0.9695 | 0.8743 | 0.6000 |
| B0d0.1 | False | 30 | True (0.054) / True (0.042) / False (0.093) | 154 | 0.2714 | 0.9665 | 0.8544 | 0.5726 |
| B0a1 | False | 11 | True (0.038) / True (0.033) / True (0.067) | 153 | 0.3711 | 0.9609 | 0.7949 | 0.5153 |
| B0d0.05 | False | 11 | True (0.038) / True (0.033) / True (0.067) | 153 | 0.3711 | 0.9609 | 0.7949 | 0.5153 |
| B0d0.02 | False | 1 | True (0.026) / True (0.026) / True (0.049) | 153 | 0.4682 | 0.9572 | 0.7313 | 0.4761 |
| B0a2 | False | 1 | True (0.021) / True (0.021) / True (0.041) | 153 | 0.5250 | 0.9544 | 0.6900 | 0.4609 |
| B0d0.01 | False | 1 | True (0.021) / True (0.021) / True (0.041) | 153 | 0.5250 | 0.9544 | 0.6900 | 0.4608 |
| B0d0.005 | True | 0 | True (0.018) / True (0.019) / True (0.035) | 153 | 0.5701 | 0.9519 | 0.6552 | 0.4484 |
| B0a3 | True | 0 | True (0.015) / True (0.017) / True (0.031) | 152 | 0.6061 | 0.9519 | 0.6219 | 0.4458 |
| B0d0.001 | True | 0 | True (0.013) / True (0.019) / True (0.026) | 151 | 0.6375 | 0.9515 | 0.5936 | 0.4429 |
| B0a4 | True | 0 | True (0.012) / True (0.017) / True (0.024) | 150 | 0.6603 | 0.9507 | 0.5701 | 0.4490 |
| B0a5 | True | 0 | True (0.010) / True (0.015) / True (0.020) | 149 | 0.7010 | 0.9495 | 0.5307 | 0.4529 |
| B0a8 | True | 0 | True (0.007) / True (0.012) / True (0.015) | 146 | 0.7810 | 0.9495 | 0.4445 | 0.4686 |

**S6-Table 26. (A4 1) T3: matched validity on the neutral screen, per family.**

| family | per-fold choice | result | in-sample best | composite neutral | composite registered | infeasible | progress | mean back-off | V2_exec | M* - composite infeasible (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | matched | Mstar@0.03 | True | Valid | 0.3505 | 0.9663 | 0.7843 | 0.5044 | - |
| B4 | B4@0.01, B4@0.01, B4@0.015, B4@0.01, B4@0.01 | matched | B4@0.01 | True | flagged | 0.7010 | 0.9618 | 0.4878 | 0.5172 | -0.3505 [-0.3739, -0.3284] |
| B6 | B6@0.02, B6@0.02, B6@0.02, B6@0.02, B6@0.02 | matched | B6@0.02 | True | flagged | 0.4296 | 0.9615 | 0.7430 | 0.4499 | -0.0790 [-0.0921, -0.0669] |
| B9 | B9@0.05, B9@0.04, B9@0.05, B9@0.04, B9@0.04 | matched | B9@0.04 | True | flagged | 0.6919 | 0.9578 | 0.5093 | 0.5257 | -0.3414 [-0.3713, -0.3132] |
| B0 | B0a0.333, B0a0.333, B0a0.333, B0a0.333, B0a0.333 | matched | B0a0.333 | True | flagged | 0.7324 | 0.9596 | 0.4656 | 0.5566 | -0.3818 [-0.4056, -0.3595] |

**S6-Table 27. (A4 1) T3: every grid point** (in sample, all 375 logs).

| point | neutral pass | flagged cells | HK1c P_rel / P_near / P_ip (UB) | evaluable cells | infeasible | progress | mean back-off | V2_exec |
|---|---|---|---|---|---|---|---|---|
| Mstar@0.05 | False | 5 | True (0.047) / True (0.041) / True (0.052) | 153 | 0.2466 | 0.9731 | 0.8585 | 0.5805 |
| Mstar@0.04 | False | 2 | True (0.038) / True (0.033) / True (0.040) | 153 | 0.2948 | 0.9708 | 0.8256 | 0.5429 |
| Mstar@0.03 | True | 0 | True (0.028) / True (0.024) / True (0.032) | 153 | 0.3505 | 0.9663 | 0.7843 | 0.5044 |
| Mstar@0.02 | True | 0 | True (0.018) / True (0.014) / True (0.019) | 153 | 0.4429 | 0.9631 | 0.7208 | 0.4665 |
| Mstar@0.015 | True | 0 | True (0.014) / True (0.011) / True (0.016) | 152 | 0.5188 | 0.9601 | 0.6730 | 0.4538 |
| Mstar@0.01 | True | 0 | True (0.008) / True (0.006) / True (0.007) | 150 | 0.6148 | 0.9582 | 0.5802 | 0.4611 |
| Mstar@0.005 | True | 0 | True (0.003) / True (0.003) / True (0.001) | 136 | 0.8813 | 0.9674 | 0.2902 | 0.5826 |
| B4@0.05 | False | 62 | True (0.067) / True (0.052) / False (0.135) | 154 | 0.3152 | 0.9694 | 0.8018 | 0.6425 |
| B4@0.04 | False | 40 | True (0.055) / True (0.036) / False (0.099) | 153 | 0.3824 | 0.9660 | 0.7566 | 0.5995 |
| B4@0.03 | False | 21 | True (0.042) / True (0.029) / True (0.075) | 154 | 0.4679 | 0.9642 | 0.6950 | 0.5627 |
| B4@0.02 | False | 4 | True (0.027) / True (0.019) / True (0.047) | 152 | 0.5659 | 0.9614 | 0.6107 | 0.5252 |
| B4@0.015 | False | 1 | True (0.019) / True (0.015) / True (0.031) | 152 | 0.6331 | 0.9608 | 0.5536 | 0.5164 |
| B4@0.01 | True | 0 | True (0.011) / True (0.007) / True (0.017) | 150 | 0.7206 | 0.9615 | 0.4711 | 0.5152 |
| B4@0.005 | True | 0 | True (0.003) / True (0.004) / True (0.002) | 141 | 0.8647 | 0.9684 | 0.2909 | 0.5892 |
| B6@0.05 | False | 16 | True (0.053) / True (0.046) / True (0.056) | 153 | 0.2286 | 0.9734 | 0.8657 | 0.5969 |
| B6@0.04 | False | 6 | True (0.042) / True (0.038) / True (0.043) | 153 | 0.2627 | 0.9688 | 0.8419 | 0.5488 |
| B6@0.03 | False | 2 | True (0.032) / True (0.029) / True (0.033) | 153 | 0.3215 | 0.9657 | 0.8058 | 0.4984 |
| B6@0.02 | True | 0 | True (0.020) / True (0.021) / True (0.019) | 152 | 0.4296 | 0.9615 | 0.7430 | 0.4499 |
| B6@0.015 | True | 0 | True (0.015) / True (0.016) / True (0.015) | 151 | 0.4862 | 0.9591 | 0.7027 | 0.4307 |
| B6@0.01 | True | 0 | True (0.009) / True (0.008) / True (0.007) | 150 | 0.6246 | 0.9556 | 0.5966 | 0.4406 |
| B6@0.005 | True | 0 | True (0.003) / True (0.003) / True (0.001) | 134 | 0.8759 | 0.9640 | 0.3110 | 0.5472 |
| B9@0.05 | False | 1 | True (0.016) / True (0.007) / True (0.022) | 153 | 0.6629 | 0.9587 | 0.5338 | 0.5230 |
| B9@0.04 | True | 0 | True (0.013) / True (0.006) / True (0.018) | 150 | 0.7073 | 0.9579 | 0.4929 | 0.5242 |
| B9@0.03 | True | 0 | True (0.009) / True (0.004) / True (0.013) | 148 | 0.7531 | 0.9576 | 0.4447 | 0.5295 |
| B9@0.02 | True | 0 | True (0.006) / True (0.004) / True (0.007) | 148 | 0.8174 | 0.9602 | 0.3792 | 0.5429 |
| B9@0.015 | True | 0 | True (0.005) / True (0.003) / True (0.006) | 146 | 0.8573 | 0.9605 | 0.3348 | 0.5536 |
| B9@0.01 | True | 0 | True (0.003) / True (0.002) / True (0.002) | 138 | 0.9069 | 0.9662 | 0.2707 | 0.5749 |
| B9@0.005 | False | 0 | True (0.001) / n.e. / True (0.000) | 85 | 0.9715 | 0.9771 | 0.1277 | 0.7094 |
| B0d0.5 | False | 155 | False (0.509) / False (0.492) / False (0.506) | 155 | 0.0024 | 0.9956 | 0.9976 | 0.9785 |
| B0a0.03125 | False | 64 | True (0.073) / True (0.051) / False (0.145) | 154 | 0.3287 | 0.9666 | 0.7943 | 0.6797 |
| B0a0.0625 | False | 35 | True (0.052) / True (0.034) / False (0.098) | 154 | 0.4476 | 0.9632 | 0.7128 | 0.6157 |
| B0d0.3 | False | 16 | True (0.039) / True (0.025) / True (0.073) | 152 | 0.5275 | 0.9602 | 0.6477 | 0.5835 |
| B0a0.125 | False | 10 | True (0.034) / True (0.021) / True (0.063) | 152 | 0.5647 | 0.9601 | 0.6184 | 0.5717 |
| B0a0.25 | False | 2 | True (0.020) / True (0.013) / True (0.032) | 152 | 0.6936 | 0.9592 | 0.5099 | 0.5578 |
| B0d0.2 | False | 2 | True (0.020) / True (0.013) / True (0.032) | 152 | 0.7004 | 0.9590 | 0.5028 | 0.5577 |
| B0a0.333 | True | 0 | True (0.016) / True (0.011) / True (0.025) | 151 | 0.7324 | 0.9596 | 0.4656 | 0.5566 |
| B0a0.5 | True | 0 | True (0.011) / True (0.010) / True (0.015) | 150 | 0.7806 | 0.9613 | 0.4040 | 0.5630 |
| B0d0.1 | True | 0 | True (0.009) / True (0.008) / True (0.012) | 150 | 0.8012 | 0.9606 | 0.3745 | 0.5753 |
| B0a1 | True | 0 | True (0.005) / True (0.006) / True (0.005) | 147 | 0.8575 | 0.9652 | 0.3020 | 0.6042 |
| B0d0.05 | True | 0 | True (0.005) / True (0.006) / True (0.005) | 147 | 0.8575 | 0.9652 | 0.3020 | 0.6042 |
| B0d0.02 | True | 0 | True (0.003) / True (0.006) / True (0.003) | 146 | 0.9041 | 0.9678 | 0.2449 | 0.6351 |
| B0a2 | True | 0 | True (0.003) / True (0.006) / True (0.003) | 145 | 0.9217 | 0.9703 | 0.2151 | 0.6548 |
| B0d0.01 | True | 0 | True (0.003) / True (0.006) / True (0.003) | 145 | 0.9217 | 0.9703 | 0.2151 | 0.6548 |
| B0d0.005 | True | 0 | True (0.002) / True (0.004) / True (0.001) | 142 | 0.9363 | 0.9710 | 0.1909 | 0.6779 |
| B0a3 | True | 0 | True (0.002) / True (0.004) / True (0.001) | 139 | 0.9469 | 0.9731 | 0.1688 | 0.6975 |
| B0d0.001 | True | 0 | True (0.002) / True (0.002) / True (0.001) | 135 | 0.9530 | 0.9751 | 0.1528 | 0.7159 |
| B0a4 | True | 0 | True (0.002) / True (0.003) / True (0.000) | 128 | 0.9567 | 0.9765 | 0.1404 | 0.7295 |
| B0a5 | True | 0 | True (0.001) / True (0.020) / True (0.000) | 106 | 0.9657 | 0.9786 | 0.1203 | 0.7498 |
| B0a8 | False | 0 | True (0.001) / n.e. / True (0.000) | 93 | 0.9770 | 0.9825 | 0.0897 | 0.7903 |

**The registered-screen version of (a), re-read with A4's reporting** (classes Valid / flagged / fails HK1c only / fails a floor only; contrasts only for composites that pass). Verbatim from the result file:

- T1 B4: composite {'0': 'B4@0.005', '1': 'B4@0.005', '2': 'B4@0.005', '3': 'B4@0.005', '4': 'B4@0.005'} -> fails a floor only (infeasible 0.9106); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 flagged, 0.01 Valid, 0.005 fails a floor only
- T1 B6: composite {'0': 'B6@0.015', '1': 'B6@0.005', '2': 'B6@0.015', '3': 'B6@0.015', '4': 'B6@0.015'} -> Valid (infeasible 0.6226); M* - composite -0.4362 [-0.4634, -0.4098]; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 flagged, 0.01 Valid, 0.005 fails a floor only
- T1 B9: composite {'0': 'B9@0.005', '1': 'B9@0.005', '2': 'B9@0.005', '3': 'B9@0.005', '4': 'B9@0.005'} -> fails HK1c and a floor (infeasible 0.9724); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 Valid, 0.015 fails a floor only, 0.01 fails a floor only, 0.005 fails HK1c and a floor
- T3 B4: composite {'0': 'B4@0.005', '1': 'B4@0.005', '2': 'B4@0.005', '3': 'B4@0.005', '4': 'B4@0.005'} -> fails a floor only (infeasible 0.8647); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 flagged, 0.01 flagged, 0.005 fails a floor only
- T3 B6: composite {'0': 'B6@0.015', '1': 'B6@0.015', '2': 'B6@0.015', '3': 'B6@0.015', '4': 'B6@0.015'} -> Valid (infeasible 0.4862); M* - composite -0.2396 [-0.2559, -0.2237]; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 Valid, 0.01 Valid, 0.005 fails a floor only
- T3 B9: composite {'0': 'B9@0.005', '1': 'B9@0.005', '2': 'B9@0.005', '3': 'B9@0.005', '4': 'B9@0.005'} -> fails HK1c and a floor (infeasible 0.9715); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 Valid, 0.015 fails a floor only, 0.01 fails a floor only, 0.005 fails HK1c and a floor

**Result.** At its registered level, δ′ = 0.05, M\* fails the neutral screen on both trackers, with 5 flagged partition cells. From δ′ = 0.03 it passes in every fold, at infeasible rates of 0.2603 (T1) and 0.3505 (T3), and it is valid on the registered screen there. Every comparator family has a neutral-matched composite, and each of these composites is flagged on the registered screen. M\* at its matched point is less often infeasible than each of them: M\* − composite is −0.2323 to −0.4395 on T1 and −0.0790 to −0.3818 on T3, and every interval excludes 0. B9, however, passes at its least conservative grid point (δ′ = 0.05) in four (T1) and two (T3) of the five folds, so its composite is censored by the grid and its contrast (−0.4395 on T1, −0.3414 on T3) is not at matched validity; over B0, B4 and B6 the range is −0.2323 to −0.3021 (T1) and −0.0790 to −0.3818 (T3). On the registered screen only B6 on T3 has a matched point under the no-substitute rule; the composites of B4 and B9 fail a floor only or HK1c and a floor, and are given no contrast (B0: S6.2).

### S6.18 A4 (2): loop-mode replay on Argoverse 2 (descriptive)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

`[a4_review/x3_a4_2_loop_v01.md; A4 §(2)]`

The closed-loop, non-reactive replay `k8_sim_v04.run_episode` (S9.10) was run through the X3 runner, not the frozen tool, with delays of 0, 2 and 4 keyframes on all 375 logs: 1,054 episodes per arm and tracker. The endpoints are those of the record's loop functions: at-fault collisions with tracked and with untracked agents per episode, progress, the share of infeasible frames, the share of hard-braking frames and the log-replay divergence share. Keys are (log, delay); log bootstrap B = 4000, seed [20261201, i, 12]. The arms are M\*, B0, B4, B6, B8 (X3E1_B8) and the B6 composite of (a) (A_B6_composite). **No ranking or claim:** this is log replay with non-reactive agents (nuPlan's CL-NR), and an arm that is infeasible more often runs more often at a backed-off margin (K6 R09b MJ1), so collision contrasts are not read as calibration effects (D10 section 2).

**S6-Table 28. (A4 2) T1: loop mode per arm** (episodes; at-fault collisions with tracked agents, count with rate per 1,000 episodes and 95 % interval; with untracked agents; progress; infeasible frames; hard braking; divergence share).

| arm | episodes | at fault, tracked (per 1000; 95 % CI) | at fault, untracked (per 1000) | progress | infeasible frames | hard braking | divergence share |
|---|---|---|---|---|---|---|---|
| Mstar | 1054 | 31 (29.41; 19.98-41.75) | 0 (0.00) | 0.8821 | 0.1834 | 0.0634 | 0.2087 |
| B0 | 1054 | 49 (46.49; 34.39-61.46) | 2 (1.90) | 0.7605 | 0.3305 | 0.1014 | 0.3357 |
| B4 | 1054 | 41 (38.90; 27.91-52.77) | 1 (0.95) | 0.8304 | 0.1849 | 0.0762 | 0.2496 |
| B6 | 1054 | 34 (32.26; 22.34-45.08) | 1 (0.95) | 0.8554 | 0.1467 | 0.0671 | 0.2206 |
| X3E1_B8 | 1054 | 23 (21.82; 13.83-32.74) | 2 (1.90) | 0.8455 | 0.2977 | 0.0779 | 0.2510 |
| A_B6_composite | 1054 | 51 (48.39; 36.03-63.62) | 5 (4.74) | 0.7223 | 0.5103 | 0.1186 | 0.4012 |

**S6-Table 29. (A4 2) T1: M\* minus arm** (key level, 95 % interval).

| arm | endpoint | M* - arm | 95 % CI |
|---|---|---|---|
| B0 | collisions_at_fault_tracked_per_episode | -0.0171 | [-0.0332, -0.0019] |
| B0 | collisions_at_fault_untracked_per_episode | -0.0019 | [-0.0048, 0.0000] |
| B0 | progress | 0.1216 | [0.1023, 0.1411] |
| B0 | infeasible_frame_share | -0.1469 | [-0.1706, -0.1243] |
| B0 | hard_brake_frame_share | -0.0380 | [-0.0438, -0.0319] |
| B0 | divergence_share | -0.1271 | [-0.1484, -0.1059] |
| B0 | progress_ratio | 0.1204 | [0.1008, 0.1391] |
| B4 | collisions_at_fault_tracked_per_episode | -0.0095 | [-0.0238, 0.0047] |
| B4 | collisions_at_fault_untracked_per_episode | -0.0009 | [-0.0029, 0.0000] |
| B4 | progress | 0.0518 | [0.0358, 0.0680] |
| B4 | infeasible_frame_share | -0.0016 | [-0.0202, 0.0165] |
| B4 | hard_brake_frame_share | -0.0128 | [-0.0182, -0.0073] |
| B4 | divergence_share | -0.0409 | [-0.0597, -0.0215] |
| B4 | progress_ratio | 0.0507 | [0.0351, 0.0665] |
| B6 | collisions_at_fault_tracked_per_episode | -0.0028 | [-0.0142, 0.0085] |
| B6 | collisions_at_fault_untracked_per_episode | -0.0009 | [-0.0029, 0.0000] |
| B6 | progress | 0.0267 | [0.0133, 0.0403] |
| B6 | infeasible_frame_share | 0.0365 | [0.0210, 0.0517] |
| B6 | hard_brake_frame_share | -0.0036 | [-0.0084, 0.0011] |
| B6 | divergence_share | -0.0119 | [-0.0278, 0.0042] |
| B6 | progress_ratio | 0.0276 | [0.0141, 0.0414] |
| X3E1_B8 | collisions_at_fault_tracked_per_episode | 0.0076 | [-0.0029, 0.0199] |
| X3E1_B8 | collisions_at_fault_untracked_per_episode | -0.0019 | [-0.0058, 0.0000] |
| X3E1_B8 | progress | 0.0367 | [0.0248, 0.0488] |
| X3E1_B8 | infeasible_frame_share | -0.1147 | [-0.1284, -0.1020] |
| X3E1_B8 | hard_brake_frame_share | -0.0145 | [-0.0181, -0.0105] |
| X3E1_B8 | divergence_share | -0.0424 | [-0.0549, -0.0302] |
| X3E1_B8 | progress_ratio | 0.0358 | [0.0242, 0.0476] |
| A_B6_composite | collisions_at_fault_tracked_per_episode | -0.0190 | [-0.0347, -0.0058] |
| A_B6_composite | collisions_at_fault_untracked_per_episode | -0.0047 | [-0.0115, 0.0000] |
| A_B6_composite | progress | 0.1598 | [0.1390, 0.1803] |
| A_B6_composite | infeasible_frame_share | -0.3268 | [-0.3535, -0.3008] |
| A_B6_composite | hard_brake_frame_share | -0.0551 | [-0.0614, -0.0486] |
| A_B6_composite | divergence_share | -0.1925 | [-0.2160, -0.1694] |
| A_B6_composite | progress_ratio | 0.1558 | [0.1357, 0.1761] |

**S6-Table 30. (A4 2) T3: loop mode per arm.**

| arm | episodes | at fault, tracked (per 1000; 95 % CI) | at fault, untracked (per 1000) | progress | infeasible frames | hard braking | divergence share |
|---|---|---|---|---|---|---|---|
| Mstar | 1054 | 26 (24.67; 16.11-36.14) | 5 (4.74) | 0.8888 | 0.2499 | 0.0683 | 0.2128 |
| B0 | 1054 | 40 (37.95; 27.11-51.68) | 3 (2.85) | 0.7810 | 0.8057 | 0.1118 | 0.3709 |
| B4 | 1054 | 34 (32.26; 22.34-45.08) | 4 (3.80) | 0.8571 | 0.2966 | 0.0845 | 0.2759 |
| B6 | 1054 | 28 (26.57; 17.65-38.39) | 3 (2.85) | 0.8824 | 0.2307 | 0.0717 | 0.2268 |
| X3E1_B8 | 1054 | 32 (30.36; 20.77-42.86) | 3 (2.85) | 0.7977 | 0.4625 | 0.1006 | 0.3263 |
| A_B6_composite | 1054 | 41 (38.90; 27.91-52.77) | 2 (1.90) | 0.8166 | 0.4674 | 0.1031 | 0.3159 |

**S6-Table 31. (A4 2) T3: M\* minus arm** (key level, 95 % interval).

| arm | endpoint | M* - arm | 95 % CI |
|---|---|---|---|
| B0 | collisions_at_fault_tracked_per_episode | -0.0133 | [-0.0274, -0.0019] |
| B0 | collisions_at_fault_untracked_per_episode | 0.0019 | [-0.0038, 0.0077] |
| B0 | progress | 0.1079 | [0.0874, 0.1284] |
| B0 | infeasible_frame_share | -0.5549 | [-0.5777, -0.5327] |
| B0 | hard_brake_frame_share | -0.0436 | [-0.0501, -0.0367] |
| B0 | divergence_share | -0.1580 | [-0.1814, -0.1344] |
| B0 | progress_ratio | 0.1048 | [0.0850, 0.1250] |
| B4 | collisions_at_fault_tracked_per_episode | -0.0076 | [-0.0199, 0.0028] |
| B4 | collisions_at_fault_untracked_per_episode | 0.0009 | [0.0000, 0.0029] |
| B4 | progress | 0.0317 | [0.0193, 0.0446] |
| B4 | infeasible_frame_share | -0.0467 | [-0.0615, -0.0321] |
| B4 | hard_brake_frame_share | -0.0162 | [-0.0210, -0.0116] |
| B4 | divergence_share | -0.0631 | [-0.0794, -0.0470] |
| B4 | progress_ratio | 0.0317 | [0.0195, 0.0444] |
| B6 | collisions_at_fault_tracked_per_episode | -0.0019 | [-0.0096, 0.0048] |
| B6 | collisions_at_fault_untracked_per_episode | 0.0019 | [0.0000, 0.0048] |
| B6 | progress | 0.0064 | [-0.0026, 0.0155] |
| B6 | infeasible_frame_share | 0.0187 | [0.0098, 0.0278] |
| B6 | hard_brake_frame_share | -0.0034 | [-0.0067, -0.0000] |
| B6 | divergence_share | -0.0140 | [-0.0243, -0.0037] |
| B6 | progress_ratio | 0.0059 | [-0.0028, 0.0147] |
| X3E1_B8 | collisions_at_fault_tracked_per_episode | -0.0057 | [-0.0133, 0.0010] |
| X3E1_B8 | collisions_at_fault_untracked_per_episode | 0.0019 | [-0.0019, 0.0057] |
| X3E1_B8 | progress | 0.0911 | [0.0744, 0.1082] |
| X3E1_B8 | infeasible_frame_share | -0.2119 | [-0.2302, -0.1947] |
| X3E1_B8 | hard_brake_frame_share | -0.0323 | [-0.0373, -0.0274] |
| X3E1_B8 | divergence_share | -0.1135 | [-0.1319, -0.0956] |
| X3E1_B8 | progress_ratio | 0.0886 | [0.0721, 0.1053] |
| A_B6_composite | collisions_at_fault_tracked_per_episode | -0.0142 | [-0.0254, -0.0047] |
| A_B6_composite | collisions_at_fault_untracked_per_episode | 0.0028 | [-0.0010, 0.0075] |
| A_B6_composite | progress | 0.0722 | [0.0585, 0.0862] |
| A_B6_composite | infeasible_frame_share | -0.2172 | [-0.2319, -0.2028] |
| A_B6_composite | hard_brake_frame_share | -0.0348 | [-0.0398, -0.0301] |
| A_B6_composite | divergence_share | -0.1030 | [-0.1187, -0.0871] |
| A_B6_composite | progress_ratio | 0.0702 | [0.0567, 0.0841] |

**Result** (descriptive). At-fault collisions with tracked agents per 1,000 episodes were 29.41 (T1) and 24.67 (T3) for M\*, against 21.82–48.39 and 26.57–38.90 for the other arms. Against the B6 composite, M\* − arm was −0.0190 [−0.0347, −0.0058] per episode on T1 and −0.0142 [−0.0254, −0.0047] on T3. Episode progress was 0.8821 (T1) and 0.8888 (T3) for M\*, against 0.7223 and 0.8166 for the B6 composite.

### S6.19 A4 (3): a larger ego footprint

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

`[a4_review/x3_a4_3_ego_footprint_v01.md; a4_review/x3_a4_checks_v01.json; A4 §(3)]`

The decision-mode runs were repeated with the ego footprint 4.9 × 1.9 m instead of the nuScenes 4.1 × 1.8 m of record (S9.5), with the 0.5 m buffer unchanged. The footprint is overridden in-process in the X3 runner; the frozen file is not edited, and the default footprint run through the same code path reproduces the record exactly. Registered screen with the record's roles; seeds [20261201, i, 13] / [20261202, i, 13]; B = 4000.

**S6-Table 32. (A4 3) T1: ego footprint 4.9 × 1.9 m** (in brackets: the record, 4.1 × 1.8 m).

| arm | registered (4.9 x 1.9) | record status | infeasible 4.9 x 1.9 (record 4.1 x 1.8) | progress | V2_exec (record) |
|---|---|---|---|---|---|
| Mstar | Valid | Valid | 0.2083 (0.1864) | 0.9678 (0.9723) | 0.5600 (0.5509) |
| B0 | flagged | shown above | 0.4067 (0.3711) | 0.9593 (0.9609) | 0.5329 (0.5153) |
| B4 | flagged | shown above | 0.2336 (0.2019) | 0.9679 (0.9725) | 0.5876 (0.5783) |
| B6 | flagged | shown above | 0.1970 (0.1653) | 0.9673 (0.9711) | 0.5619 (0.5484) |

**S6-Table 33. (A4 3) T3: ego footprint 4.9 × 1.9 m.**

| arm | registered (4.9 x 1.9) | record status | infeasible 4.9 x 1.9 (record 4.1 x 1.8) | progress | V2_exec (record) |
|---|---|---|---|---|---|
| Mstar | Valid | Valid | 0.2700 (0.2466) | 0.9685 (0.9731) | 0.5921 (0.5805) |
| B0 | fails a floor only | not valid | 0.8671 (0.8575) | 0.9635 (0.9652) | 0.6224 (0.6042) |
| B4 | flagged | shown above | 0.3479 (0.3152) | 0.9666 (0.9694) | 0.6533 (0.6425) |
| B6 | flagged | shown above | 0.2500 (0.2286) | 0.9695 (0.9734) | 0.6063 (0.5969) |

**Result.** M\* stays valid on both trackers. Its infeasible rate rises from 0.1864 to 0.2083 (T1) and from 0.2466 to 0.2700 (T3), and its V2_exec by about 0.01. B0, B4 and B6 are flagged, or on T3 B0 fails a floor only, as of record.

### S6.20 A4 (4): heading error, stricter cuts and the annotation's axes

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

**added after review (amendment A4).** Amendment `20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md` (sha256 ab19dd66...), section (4); extends A1 (`x3_a1_heading_v01.json`) on the same rebuilt X2 items (nuScenes train, 700 scenes, T1 = CANMOT, in-path cars, 2 s, sigma_a = 0.10 m).

`[a1_heading/x3_a4_heading_v01.md; A4 §(4)]`

Reuse check: the A1 rows reloaded from the checkpoint reproduce X2's n, scenes and E_rec exactly in the four decision cells, estimate- and truth-oriented: **yes**.

**Method notes**, verbatim from the result file:

- Same items as A1 and X2 (L.cell_items on the A1 rebuild, reloaded unchanged; n, scenes and E_rec re-checked equal to the X2 result of record in all eight cell-orientation pairs).
- Heading error as A1: |wrap(psi_track - psi_annotation)| at the decision keyframe k, folded to [0, 90] deg; (4a) keeps items with heading error <= 5 deg or <= 10 deg; E record-weighted (exceedances / items), exceedance U > z_0.95 = 1.6448536269514722.
- (4b) Annotation axes: for an item on the track's lateral (longitudinal) axis, the annotated box's lateral (longitudinal) axis b at keyframe k (the annotation paired at k, as in A1; A4 does not name the keyframe, and k keeps the analysis at decision time, swapping only the heading). Error (g - m) projected on b, signed toward the ego as X2 orients: sign of b.(c - m) estimate-oriented, of b.(c - g) truth-oriented (c = CTRV-predicted ego center at 2 s, m = predicted mean, g = annotation center at 2 s). sd = sqrt(b' S b + 0.10^2) from the same predicted covariance S. The item set is X2's: the separating filter is not re-evaluated along b.
- Code-path check: the (4b) computation run with the track's own yaw in place of the annotation's reproduces X2's U (max abs difference per cell in reuse_gate, tolerance 1e-9).
- Bootstrap: scene-cluster, B = 2000, numpy default_rng([20261211, cell, k]); cell = 0..3 in X2's DEC order (car <20 lat, car 20-40 lat, car <20 long, car 20-40 long); k = 1 (<= 5 deg), 2 (<= 10 deg), 3 (annotation axes); the same seed for the estimate- and truth-oriented versions. Weights L.boot_weights (multinomial over the 700 scenes, X2's convention); replicate = ratio of weighted sums; pointwise 95 % percentile interval.
- Thresholds listed for reference only (A4 (4) fixes no reading): estimate-oriented max(0.05, E0) of record; truth-oriented 0.05 of record.

**S6-Table 34. (A4 4) Estimate-oriented (X2 primary)** (E record-weighted; n with scenes in brackets; pointwise scene-bootstrap 95 % percentile intervals; thresholds of record for reference only).

| Cell | E, all items (record) | E, heading error <= 5 deg [95 % CI] | n (scenes) | E, heading error <= 10 deg [95 % CI] | n (scenes) | E, annotation axes [95 % CI] | n (scenes) | threshold of record |
|---|---|---|---|---|---|---|---|---|
| car, < 20 m, lat | 0.194 (3396) | 0.139 [0.110, 0.171] | 1163 (322) | 0.162 [0.131, 0.194] | 1556 (352) | 0.124 [0.102, 0.146] | 3396 (442) | 0.0775 |
| car, 20–40 m, lat | 0.272 (1229) | 0.232 [0.158, 0.314] | 276 (107) | 0.233 [0.176, 0.297] | 514 (144) | 0.108 [0.074, 0.143] | 1229 (219) | 0.0816 |
| car, < 20 m, long | 0.004 (8038) | 0.004 [0.002, 0.006] | 5313 (455) | 0.004 [0.002, 0.006] | 6275 (474) | 0.007 [0.005, 0.010] | 8038 (529) | 0.0646 |
| car, 20–40 m, long | 0.011 (3522) | 0.013 [0.006, 0.021] | 2418 (255) | 0.014 [0.008, 0.020] | 2792 (287) | 0.020 [0.013, 0.028] | 3522 (345) | 0.0500 |

**S6-Table 35. (A4 4) Truth-oriented (X2 a5 definition).**

| Cell | E, all items (record) | E, heading error <= 5 deg [95 % CI] | n (scenes) | E, heading error <= 10 deg [95 % CI] | n (scenes) | E, annotation axes [95 % CI] | n (scenes) | threshold of record |
|---|---|---|---|---|---|---|---|---|
| car, < 20 m, lat | 0.154 (3554) | 0.101 [0.078, 0.126] | 1193 (339) | 0.122 [0.095, 0.150] | 1634 (376) | 0.089 [0.070, 0.108] | 3554 (454) | 0.0500 |
| car, 20–40 m, lat | 0.228 (1248) | 0.123 [0.069, 0.182] | 285 (112) | 0.144 [0.094, 0.203] | 522 (149) | 0.064 [0.040, 0.093] | 1248 (224) | 0.0500 |
| car, < 20 m, long | 0.001 (8233) | 0.001 [0.000, 0.001] | 5417 (457) | 0.001 [0.000, 0.001] | 6398 (474) | 0.002 [0.001, 0.004] | 8233 (530) | 0.0500 |
| car, 20–40 m, long | 0.011 (3522) | 0.012 [0.006, 0.020] | 2418 (255) | 0.013 [0.007, 0.020] | 2792 (287) | 0.019 [0.012, 0.028] | 3522 (345) | 0.0500 |

Integrity: C1_RUN_LOG sha256 8bc6235d... before and after; c1_av2_v01 manifest identical before and after: True.

**Result** (A4 (4) fixes no reading; descriptive). Estimate-oriented, the lateral exceedance on items with heading error ≤ 5° is 0.139 [0.110, 0.171] (< 20 m) and 0.232 [0.158, 0.314] (20–40 m), against 0.194 and 0.272 on all items and thresholds of 0.0775 and 0.0816; along the annotation's axes it is 0.124 [0.102, 0.146] and 0.108 [0.074, 0.143]. Truth-oriented, the same cells give 0.101 [0.078, 0.126] and 0.123 [0.069, 0.182] at ≤ 5°, and 0.089 [0.070, 0.108] and 0.064 [0.040, 0.093] along the annotation's axes, against 0.05. Heading error therefore explains part of the lateral excess. In the < 20 m cell the excess remains under every cut and along the annotation's axes, with every interval above the threshold; in the 20–40 m cell along the annotation's axes, the interval reaches below the threshold in both orientations. The longitudinal cells stay below their thresholds throughout.

### S6.21 A4 (5): AB3DMOT without unmatched tracks

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

`[a4_review/x3_a4_5_ab3dmot_matched_only_v01.md; A4 §(5)]`

M\* on AB3DMOT (fits of record) was re-run in decision mode with every track that has no annotation match (`tr_inst = -1`; 203,733 track rows over the 375 logs) removed from the planner's input after loading; matched tracks are unchanged. Z0 was run under the same removal. Registered screen with the record's roles; seeds [20261201, 2, 15] / [20261202, 2, 15].

**S6-Table 36. (A4 5) AB3DMOT with unmatched tracks removed** (in brackets: all tracks, of record).

| arm | infeasible (all tracks, record) | progress (record) | registered (record Valid) |
|---|---|---|---|
| Mstar_matched_only | 0.7570 (0.8907) | 0.9765 (0.9812) | flagged (False) |
| Z0_matched_only | 0.0044 (0.0063) | 0.9949 (0.9929) | flagged (False) |

Reading (fixed by A4): the infeasible rate does not fall by more than half (0.8907 -> 0.7570): the text drops the false-positive explanation.

**Result.** A4 fixed in advance that false-positive tracks would count as a main driver of AB3DMOT's infeasibility only if removing them more than halved M\*'s infeasible rate. The rate falls only from 0.8907 to 0.7570, and M\* is still flagged on the registered screen, so false-positive tracks are not the main driver, and that explanation is dropped (S6.9).

---

### S6.22 A5: the neutral screen without track speed and track age; what sets the matched levels; read-outs

Amendment A5 (`20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md`, SHA-256 25f3bb65…, self-recorded hash lock at 18:21:54 EST on 7 Nov 2026) was written after a third internal review of an earlier version of the manuscript and before any cross-fitted quantity below was computed. The reviewer had re-read A4(1)'s in-sample curve table without P1 and P3, and the analyst had read that report. A5 re-screens the runs of A4(1); no run was added. Everything below is labeled *added after review (amendment A5)*.

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A5)

Reduced screen = A4(1)'s neutral screen on P2, P4, P5, P6, P7 (P1 track speed, P3 track age dropped) + HK1c per population; seeds [20261201, i, 21] / [20261202, i, 21]; B = 4000. Runs: `a4n_<t>` and `core_<t>` in `runs/` (no new run). A4(1)'s selection is recomputed with its own seeds and checked equal to the A4 output: {"t1": {"Mstar": true, "B4": true, "B6": true, "B9": true, "B0": true}, "t3": {"Mstar": true, "B4": true, "B6": true, "B9": true, "B0": true}}.

#### (1) Matched validity on the reduced screen

| tracker | family | per-fold choice | composite reduced | composite registered | infeasible | progress | mean back-off | V2 | V2_exec | V2_viol | M* - composite infeasible (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | True | Valid | 0.2603 | 0.9657 | 0.8480 | 0.3412 | 0.4480 | 0.0128 | - |
| T1 | B4 | B4@0.02, B4@0.02, B4@0.03, B4@0.02, B4@0.02 | True | flagged | 0.4472 | 0.9583 | 0.7424 | 0.2804 | 0.4478 | 0.0212 | -0.1869 [-0.2144, -0.1595] |
| T1 | B6 | B6@0.03, B6@0.03, B6@0.03, B6@0.04, B6@0.04 | True | flagged | 0.2982 | 0.9635 | 0.8446 | 0.3767 | 0.4747 | 0.0183 | -0.0379 [-0.0634, -0.0118] |
| T1 | B9 | B9@0.05, B9@0.05, B9@0.05, B9@0.05, B9@0.05 | True | flagged | 0.6928 | 0.9552 | 0.5048 | 0.1582 | 0.5266 | 0.0143 | -0.4325 [-0.4580, -0.4055] |
| T1 | B0 | B0d0.02, B0d0.02, B0d0.02, B0d0.02, B0d0.02 | True | flagged | 0.4682 | 0.9572 | 0.7313 | 0.3027 | 0.4761 | 0.0202 | -0.2079 [-0.2341, -0.1805] |
| T3 | Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | True | Valid | 0.3505 | 0.9663 | 0.7843 | 0.3480 | 0.5044 | 0.0149 | - |
| T3 | B4 | B4@0.015, B4@0.015, B4@0.015, B4@0.015, B4@0.015 | True | flagged | 0.6331 | 0.9608 | 0.5536 | 0.2209 | 0.5164 | 0.0271 | -0.2826 [-0.3033, -0.2622] |
| T3 | B6 | B6@0.03, B6@0.02, B6@0.02, B6@0.03, B6@0.02 | True | flagged | 0.3832 | 0.9635 | 0.7692 | 0.3046 | 0.4651 | 0.0160 | -0.0327 [-0.0453, -0.0206] |
| T3 | B9 | B9@0.05, B9@0.05, B9@0.05, B9@0.05, B9@0.05 | True | flagged | 0.6629 | 0.9587 | 0.5338 | 0.1774 | 0.5230 | 0.0180 | -0.3124 [-0.3409, -0.2840] |
| T3 | B0 | B0a0.25, B0a0.333, B0a0.25, B0a0.25, B0a0.333 | True | flagged | 0.7076 | 0.9587 | 0.4930 | 0.2179 | 0.5587 | 0.0214 | -0.3571 [-0.3799, -0.3344] |

Reading fixed by A5: every M* - composite interval lies below 0 on both trackers: the back-off advantage on the neutral screen survives removing P1 and P3

#### (2) The flags that stop each family one grid point before its matched point

- T1 Mstar A4: matched in sample at Mstar@0.03; at Mstar@0.04: P1 [0.5,3)|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P1 [0.5,3)|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T1 Mstar A5: matched in sample at Mstar@0.03; at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T1 B4 A4: matched in sample at B4@0.015; at B4@0.02: P1 [3,8)|lat PD
  - fold 0 (matched B4@0.015): at B4@0.02: P1 [3,8)|lat PD
  - fold 1 (matched B4@0.02): at B4@0.03: P1 [0.5,3)|long PD7; P1 [3,8)|long PD7; P1 [3,8)|lat PD; P3 1-2|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 2 (matched B4@0.02): at B4@0.03: P1 [0.5,3)|long PD7; P1 [3,8)|long PD7; P1 [3,8)|lat PD7; P1 [3,8)|lat PD; P3 1-2|long PD7; P4 [0.4,0.5)|long PD7
  - fold 3 (matched B4@0.015): at B4@0.02: P1 [3,8)|lat PD
  - fold 4 (matched B4@0.015): at B4@0.02: P1 [3,8)|lat PD
- T1 B4 A5: matched in sample at B4@0.02; at B4@0.03: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 0 (matched B4@0.02): at B4@0.03: P2 [2,5.5)|lat PD; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 1 (matched B4@0.02): at B4@0.03: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 2 (matched B4@0.03): at B4@0.04: P2 <2|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|long PD7; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 3 (matched B4@0.02): at B4@0.03: P4 [0.4,0.5)|long PD7
  - fold 4 (matched B4@0.02): at B4@0.03: P4 [0.4,0.5)|long PD7
- T1 B6 A4: matched in sample at B6@0.02; at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 0 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 1 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 2 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 3 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 4 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
- T1 B6 A5: matched in sample at B6@0.03; at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 0 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 1 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 2 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 3 (matched B6@0.04): at B6@0.05: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7; P4 [0.5,0.7)|long PD7; P4 [0.5,0.7)|lat PD7; P5 <1|lat PD7
  - fold 4 (matched B6@0.04): at B6@0.05: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7; P4 [0.5,0.7)|long PD7; P4 [0.5,0.7)|lat PD7
- T1 B9 A4: matched in sample at B9@0.05; at None: matched at the least conservative grid point
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
  - fold 4 (matched B9@0.05): at None: matched at the least conservative grid point
- T1 B9 A5: matched in sample at B9@0.05; at None: matched at the least conservative grid point
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 4 (matched B9@0.05): at None: matched at the least conservative grid point
- T1 B0 A4: matched in sample at B0d0.005; at B0d0.01: P1 [3,8)|lat PD
  - fold 0 (matched B0d0.005): at B0d0.01: P1 [3,8)|lat PD
  - fold 1 (matched B0a2): at B0d0.02: P1 [3,8)|lat PD
  - fold 2 (matched B0a2): at B0d0.02: P1 [3,8)|lat PD
  - fold 3 (matched B0d0.005): at B0d0.01: P1 [3,8)|lat PD
  - fold 4 (matched B0a3): at B0d0.005: P1 [3,8)|lat PD
- T1 B0 A5: matched in sample at B0d0.02; at B0d0.05: P2 <2|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 0 (matched B0d0.02): at B0d0.05: P2 <2|long PD7; P2 [2,5.5)|lat PD; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 1 (matched B0d0.02): at B0d0.05: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 2 (matched B0d0.02): at B0d0.05: P2 <2|long PD7; P4 [0.4,0.5)|long PD7
  - fold 3 (matched B0d0.02): at B0d0.05: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD
  - fold 4 (matched B0d0.02): at B0d0.05: P2 <2|long PD7; P4 [0.4,0.5)|long PD7
- T3 Mstar A4: matched in sample at Mstar@0.03; at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T3 Mstar A5: matched in sample at Mstar@0.03; at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T3 B4 A4: matched in sample at B4@0.01; at B4@0.015: P1 [3,8)|long PD7
  - fold 0 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
  - fold 1 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
  - fold 2 (matched B4@0.015): at B4@0.02: P1 [3,8)|long PD7; P1 >=8|long PD7; P2 >=8|long PD7
  - fold 3 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
  - fold 4 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
- T3 B4 A5: matched in sample at B4@0.015; at B4@0.02: P2 >=8|long PD7
  - fold 0 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 1 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 2 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 3 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 4 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
- T3 B6 A4: matched in sample at B6@0.02; at B6@0.03: P1 [3,8)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7
  - fold 1 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 3 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7
  - fold 4 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
- T3 B6 A5: matched in sample at B6@0.02; at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 0 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 1 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 2 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 3 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 4 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
- T3 B9 A4: matched in sample at B9@0.04; at B9@0.05: P1 [3,8)|long PD7
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
  - fold 4 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
- T3 B9 A5: matched in sample at B9@0.05; at None: matched at the least conservative grid point
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 4 (matched B9@0.05): at None: matched at the least conservative grid point
- T3 B0 A4: matched in sample at B0a0.333; at B0d0.2: P1 [3,8)|long PD7; P2 >=8|long PD7
  - fold 0 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7
  - fold 1 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7; P2 >=8|long PD7
  - fold 2 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7
  - fold 3 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7
  - fold 4 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7; P2 >=8|long PD7
- T3 B0 A5: matched in sample at B0d0.2; at B0a0.25: P2 >=8|long PD7
  - fold 0 (matched B0a0.25): at B0a0.125: P2 [5.5,8)|long PD7; P2 >=8|long PD7; P2 >=8|long SD1; P6 >200|long PD7
  - fold 1 (matched B0a0.333): at B0d0.2: P2 >=8|long PD7
  - fold 2 (matched B0a0.25): at B0a0.125: P2 >=8|long PD7
  - fold 3 (matched B0a0.25): at B0a0.125: P2 [5.5,8)|long PD7; P2 >=8|long PD7; P2 >=8|long SD1
  - fold 4 (matched B0a0.333): at B0d0.2: P2 >=8|long PD7

#### (3) Six exceedance and operability measures of the matched composites (k8_analyse_v04's definitions)

| tracker | family | screen | V2 | V2_exec | V2_viol | infeasible | progress | min gap < 1 m |
|---|---|---|---|---|---|---|---|---|
| T1 | Mstar | A4 | 0.3412 | 0.4480 | 0.0128 | 0.2603 | 0.9657 | 0.2865 |
| T1 | Mstar | A5 | 0.3412 | 0.4480 | 0.0128 | 0.2603 | 0.9657 | 0.2865 |
| T1 | B4 | A4 | 0.2207 | 0.4295 | 0.0187 | 0.5327 | 0.9537 | 0.2725 |
| T1 | B4 | A5 | 0.2804 | 0.4478 | 0.0212 | 0.4472 | 0.9583 | 0.2682 |
| T1 | B6 | A4 | 0.2440 | 0.4607 | 0.0141 | 0.4926 | 0.9554 | 0.2689 |
| T1 | B6 | A5 | 0.3767 | 0.4747 | 0.0183 | 0.2982 | 0.9635 | 0.2739 |
| T1 | B9 | A4 | 0.1530 | 0.5256 | 0.0137 | 0.6998 | 0.9555 | 0.2685 |
| T1 | B9 | A5 | 0.1582 | 0.5266 | 0.0143 | 0.6928 | 0.9552 | 0.2676 |
| T1 | B0 | A4 | 0.2251 | 0.4538 | 0.0189 | 0.5624 | 0.9522 | 0.2771 |
| T1 | B0 | A5 | 0.3027 | 0.4761 | 0.0202 | 0.4682 | 0.9572 | 0.2683 |
| T3 | Mstar | A4 | 0.3480 | 0.5044 | 0.0149 | 0.3505 | 0.9663 | 0.2913 |
| T3 | Mstar | A5 | 0.3480 | 0.5044 | 0.0149 | 0.3505 | 0.9663 | 0.2913 |
| T3 | B4 | A4 | 0.1566 | 0.5172 | 0.0215 | 0.7010 | 0.9618 | 0.2777 |
| T3 | B4 | A5 | 0.2209 | 0.5164 | 0.0271 | 0.6331 | 0.9608 | 0.2772 |
| T3 | B6 | A4 | 0.2673 | 0.4499 | 0.0158 | 0.4296 | 0.9615 | 0.2894 |
| T3 | B6 | A5 | 0.3046 | 0.4651 | 0.0160 | 0.3832 | 0.9635 | 0.2896 |
| T3 | B9 | A4 | 0.1569 | 0.5257 | 0.0167 | 0.6919 | 0.9578 | 0.2716 |
| T3 | B9 | A5 | 0.1774 | 0.5230 | 0.0180 | 0.6629 | 0.9587 | 0.2693 |
| T3 | B0 | A4 | 0.1915 | 0.5566 | 0.0200 | 0.7324 | 0.9596 | 0.2792 |
| T3 | B0 | A5 | 0.2179 | 0.5587 | 0.0214 | 0.7076 | 0.9587 | 0.2795 |

Every in-sample grid point: `a5_review/x3_a5_points_v01.csv` (the same six measures, and the in-sample pass under each screen).

#### Read-outs of outputs of record and of earlier X3 files (A5)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A5)

Read-outs of outputs of record and existing X3 files (sums of stored counts, stored values); nothing recomputed.

#### (i) M*'s record-weighted pooled exceedance

Source: `60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_t{1,3}_decide_cells.csv`, rows arm = Mstar, per population: sum of column `exceed` / sum of column `records` over the cell rows that carry both (the CSV stores `exceed` only for evaluable cells; the share of the population's records covered is given).

| tracker | P_rel | P_near | P_ip |
|---|---|---|---|
| T1 | 0.0454 (24186 / 533293; 99.7 % of records) | 0.0316 (1780 / 56403; 98.5 % of records) | 0.0355 (653 / 18385; 88.9 % of records) |
| T3 | 0.0445 (23663 / 531815; 99.7 % of records) | 0.0297 (1680 / 56523; 98.4 % of records) | 0.0349 (613 / 17562; 88.9 % of records) |

#### (ii) Share of M*'s in-path relied records in fallback strata (S6 Table 13 source)

Source: `c1_analysis_r1.json`, key `k8.within_lt3d.<t>.A13_fallback_record_weighted.by_population.PD_inpath.pooled` (record-weighted from each record's fold, step, L0 and in-path flag).

- T1: 1543 of 20692 in-path relied records in fallback strata = **0.0746**
- T3: 1497 of 19754 in-path relied records in fallback strata = **0.0758**

#### (iii) From c_intervals (x3-stats, analysis c2; method (i), the record's rule)

Source: `60_RESULTS/x3_explore_v01/c_intervals/x3_c2_simulation_v01.json`, keys `results.<t>."Mstar|delta".i.screen_flag_any_population` and `results.<t>."Mstar|observed".i.<population>.sim_ub_cover_all` (1000 simulated datasets).

- T1: P(M* at delta flagged in any population) = **0.113**; simultaneous coverage of the cell upper bounds at M*'s observed cell rates: P_rel 0.346 [0.317, 0.376]; P_near 0.370 [0.341, 0.400]; P_ip 0.406 [0.376, 0.437]
- T3: P(M* at delta flagged in any population) = **0.127**; simultaneous coverage of the cell upper bounds at M*'s observed cell rates: P_rel 0.271 [0.244, 0.299]; P_near 0.256 [0.230, 0.284]; P_ip 0.520 [0.489, 0.551]

#### (iv) H2's bound at its Holm level

Source: `60_RESULTS/c1_av2_v01/c1_decision_r1.json`, keys `family_S.H2.holm_level`, `S_decision_forms.by_claim.H2.bound_at_holm_level` and `hypotheses.H2.by_tracker.<t>.holm_levels`.

- Holm level assigned: 0.005 (p = 2.5e-05, status holds); the bound used is UB at level 1 - 0.005 = 0.995: T1 0.01064, T3 -0.04939 (c = 0.03; both hold).
- Nominal (0.975) bound: T1 0.00452, T3 -0.05415.

---

## S7. The registered plan

The frozen plan is `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md`, SHA-256 0817e60097c2288b730044b8a38eb77de5f4e57a4b80067af6fd7c83a074e31c, registered on OSF under embargo at https://osf.io/v8qfk/ (reviewers receive a view-only link). It is not reproduced here. **Its structure:** the slots left open at the text lock and filled before the freeze; §0, what C1 is and what kind of evidence it gives; §1, the data and sets (the confirmation set, detector AP, the descriptive data on the 150 validation logs, classes, items and populations, the outcome-blind boundary and its scope, and the counts); §2, the claims under test; §3, what is calibrated where (folds and routes); §4, comparators and arms; §5, modes and endpoints; §6, statistics, the GO condition and multiplicity (units, bootstrap, p-values, seeds and the power rule; definitions and levels; hypotheses, decision forms and the GO condition; H9; multiplicity; reading rules; H3's caveats; the sources of the design choices; and the limits as the paper states them); §7, power and operating characteristics; §8, code, binding, freeze, deposit and run order (entry points, data roles and frozen blocks; the stage-B log; the external deposit before every outcome; ground truth, the Rule-0 metrics, the inventory and the quarantine; the order of operations; the run log and the tables of record; how later artifacts are checked; and the limits of the binding); §9, the deviation policy and failure; §10, what was seen before the text lock and the freeze; §11, the changes from earlier drafts, the outcome-blindness claim and the deposit order, and token exceptions; and finally the list of the 354 frozen files with their SHA-256, written by the freeze tool.

---

## S8. Proofs and supporting results in full

This section gives the proofs and supporting results in full, under its own labels, which differ from the main text's numbering. The main text keeps Remark 1, Propositions 1–5 and Theorem 1; Appendix A of the main text proves Theorem 1(b) and Propositions 3 and 4. A statement that the main text keeps carries its main-text label in brackets. Cited from outside this section, a label of this section carries the prefix "S8-" (for example, S8-Proposition 5). A tag [C: id] points to the numeric check of a statement in the released file `A_proofs_checks_v01.json`. Each check is exact (closed form or rational arithmetic), a one-dimensional quadrature, or a seeded Monte Carlo run with the stated tolerance.

**Label map.**

| Label in S8 | Main text | Subsection |
|---|---|---|
| Remark 1 | Remark 1 (Section III-B) | S8.2 |
| Proposition 1 | Proposition 1 (Section III-B) | S8.2 |
| Proposition 2 (dilution) | – | S8.2 |
| Proposition 3 (transfer to estimate-chosen separating axes) | – | S8.2 |
| Remark 2 (orientation null) | – (E⁰ of Table II) | S8.2 |
| Proposition 4 (plan-uniform criterion) | Proposition 2 (Section III-C) | S8.3 |
| Remark 3 (Schur) | – | S8.3 |
| Theorem 1 | Theorem 1 (Section III-C: (a), (c); (b) proved in Appendix A) | S8.3 |
| Proposition 5 and Theorem 2 (single knobs) | cited in Section III-D | S8.4 |
| Lemmas A.1 and A.2 | Appendix A, same labels | S8.5 |
| Lemma A.3 and Corollary A.4 | stated in Appendix A | S8.5 |
| Proposition 6 | Proposition 3 (Section IV-C; proof in Appendix A) | S8.5 |
| Remark 4 (transductive reading) | – | S8.5 |
| Remark A.5 (the scene as the unit) | cited in Section IV-C | S8.5 |
| Remark 5 (sample floor) | cited in Section IV-C | S8.5 |
| Proposition 7 | Proposition 4 (Section IV-D; proof in Appendix A) | S8.6 |
| Proposition 8 | Proposition 5 (Section IV-E) | S8.6 |
| Proposition 9 (certified single multiplier) | – | S8.6 |

### S8.1 Setting and notation

Throughout, (Ω, 𝓕, P) is a probability space; Φ and φ are the standard normal distribution and density functions, Φ̄ = 1 − Φ, and z_{1−δ} = Φ̄⁻¹(δ). We take δ ∈ (0, ½), so z_{1−δ} > 0.

**(M1) Information.** At decision step k the planner's information is a σ-field I_k ⊂ 𝓕. It contains the tracker's means μ̂_i and position–velocity covariances Σ̂_i ≻ 0 with class, size and yaw, and the ego state. A predictor gives m̂_i(t) and V̂_i(t), both I_k-measurable; for constant velocity, m̂_i(t) = F_tμ̂_i and V̂_i(t) = F_tΣ̂_iF_tᵀ + Q(t), with F_t = [I₂, tI₂].

**(M2) Constraints.** For each evaluated tuple j = (candidate plan, object, horizon) the planner forms a unit normal a_j, an offset b_j and a multiplier c_j, and checks

  (TC)  a_jᵀm̂_j + c_j√v̂_j ≤ b_j,  v̂_j = a_jᵀV̂_ja_j > 0.

Along a_j the predicted variance splits as v̂_j = p̂_j + q_j, where p̂_j = a_jᵀF_tΣ̂F_tᵀa_j is the exported (tracker) share and q_j = a_jᵀQ(t)a_j the process-noise share; ρ̂_j = p̂_j/q_j (∞ if q_j = 0). Under a stated truth whose tracker share is p_j, κ_j = p_j/p̂_j.

**(M3) Scores.** With X_j the realized position:
- U_j = a_jᵀ(X_j − m̂_j)/√v̂_j, the projected standardized error;
- N_j = (X_j − m̂_j)ᵀV̂_j⁻¹(X_j − m̂_j), the NEES;
- τ_j = (b_j − a_jᵀm̂_j)/√v̂_j, the realized threshold. (TC) is τ_j ≥ c_j.

Two standing assumptions are named once and used in S8.2–S8.4:
- **(M0) Measurability.** a_j, b_j, c_j, δ_j, m̂_j and V̂_j are I_k-measurable.
- **(P0) The executed plan is chosen from I_k.** The planner's choice is I_k-measurable: deterministic given I_k, or randomized independently of the X_j given I_k. The executed tuples' a_j, b_j and τ_j are then I_k-measurable.

The *risk along a* is P(U > z_{1−δ} | I_k) for the normal a. The *premise* at j is P(U_j > c_j | I_k) ≤ δ_j almost surely.

### S8.2 The premise

**Remark 1 (Gaussian half-space reduction) [main text: Remark 1].** If Y ~ N(m, V), V ≻ 0 and a ≠ 0, then P(aᵀY > b) = Φ̄((b − aᵀm)/√(aᵀVa)), and P(aᵀY > b) ≤ δ iff aᵀm + z_{1−δ}√(aᵀVa) ≤ b.

*Proof.* aᵀY is Gaussian with mean aᵀm and variance aᵀVa, which is positive because V ≻ 0 and a ≠ 0. Standardising gives the identity. Φ̄ is continuous and strictly decreasing, so Φ̄(x) ≤ δ iff x ≥ z_{1−δ}, that is, iff b − aᵀm ≥ z_{1−δ}√(aᵀVa). ∎ [C: R1_halfspace]

**Proposition 1 (premise, slack-aware) [main text: Proposition 1].** Assume (M0) and (P0).
- **(i)** For every executed tuple j that satisfies (TC), P(a_jᵀX_j > b_j | I_k) = P(U_j > τ_j | I_k) almost surely. Hence the premise P(U_j > c_j | I_k) ≤ δ_j is sufficient for the per-constraint guarantee P(a_jᵀX_j > b_j | I_k) ≤ δ_j. On the active set {τ_j = c_j} the guarantee and the premise coincide; off it the premise is not necessary. Tuples that violate (TC), such as fallback steps, are outside the statement.
- **(ii)** Let 𝕀 be a countable set of potential instances. Instance i has information I_{k(i)}, a threshold c_i, a level δ_i, a selection indicator 1_G(i) and a weight w_i ≥ 0, where c_i, δ_i and w_i1_G(i) are I_{k(i)}-measurable, and 0 < E[Σ_i w_i1_G(i)] < ∞. Define the pooled exceedance and the pooled level

  P_w(U > c_J | G) = E[Σ_i w_i1_G(i)1{U_i > c_i}] / E[Σ_i w_i1_G(i)],  E_w[δ_J | G] = E[Σ_i w_i1_G(i)δ_i] / E[Σ_i w_i1_G(i)].

  If the premise P(U_i > c_i | I_{k(i)}) ≤ δ_i holds almost surely on {i ∈ G} for every i, then P_w(U > c_J | G) ≤ E_w[δ_J | G]. With δ_i ≡ δ and c_i = z_{1−δ}, P_w(U > z_{1−δ} | G) ≤ δ. The stratum inequality is therefore necessary for the premise. It is not sufficient in general. It is sufficient when P(U_i > z_{1−δ} | I_{k(i)}) is constant on G, for example when membership of G is all the information.

*Proof of (i).* By (M0) and (P0), m̂_j, b_j and v̂_j > 0 are I_k-measurable, and, dividing by √v̂_j > 0,

  {a_jᵀX_j > b_j} = {a_jᵀ(X_j − m̂_j) > b_j − a_jᵀm̂_j} = {U_j > τ_j}.

Equal events have almost surely equal conditional probabilities. Under (TC), τ_j ≥ c_j, so {U_j > τ_j} ⊂ {U_j > c_j} and P(U_j > τ_j | I_k) ≤ P(U_j > c_j | I_k) ≤ δ_j almost surely. On the I_k-measurable event {τ_j = c_j} the two conditional probabilities coincide. Off it the premise is not necessary: if U_j | I_k puts mass 2δ_j on (c_j, τ_j] and none above τ_j, the guarantee holds and the premise fails. The event identity itself is pointwise. (M0) and (P0) are what make the premise a property of the tracker's conditional law given I_k: a normal or offset chosen with knowledge of X_j can make the premise fail for the executed tuple even when the tracker is calibrated along every I_k-measurable direction. ∎ [C: P1i_event_identity]

*Proof of (ii).* For each i, w_i1_G(i) ≥ 0 is I_{k(i)}-measurable, so by the tower property

  E[w_i1_G(i)1{U_i > c_i}] = E[w_i1_G(i)·P(U_i > c_i | I_{k(i)})] ≤ E[w_i1_G(i)δ_i].

Summing over i (Tonelli's theorem; every term is non-negative) and dividing by E[Σ_i w_i1_G(i)] ∈ (0, ∞) gives the bound. If P(U_i > z | I_{k(i)}) = π on G for every i, the pooled exceedance equals π, so the stratum inequality and the premise coincide. ∎

*Non-sufficiency, computed exactly.* Let a fair label L ∈ {1, 2} be part of the information, with U | L = 1 ~ |N(0, 1)| and U | L = 2 ~ −|N(0, 1)|. The density of U is ½·2φ(u)1{u > 0} + ½·2φ(u)1{u < 0} = φ(u), so U ~ N(0, 1). The stratum of all instances (w ≡ 1) has P(U > z_{0.99}) = Φ̄(z_{0.99}) = 0.0100, exactly at δ = 0.01. Yet P(U > z_{0.99} | L = 1) = P(|Z| > z_{0.99}) = 2Φ̄(z_{0.99}) = 0.0200, and P(U > z_{0.99} | L = 2) = 0: the premise fails on {L = 1}. [C: P1ii_fair_label]

*Weights that are not instance-measurable.* Part (ii) needs w_i1_G(i) to be measurable at the instance's own information. Log (or scene) weights w_i = 1/n_g(Z), where n_g(Z) is the number of the log's instances in the stratum, are not, because n_g(Z) depends on instances that occur later. The bound can then fail even under exact conditional calibration. Exact example:
- a log has instance 1 with U₁ | I₁ ~ N(0, 1);
- I₂ contains U₁, and instance 2 is selected iff U₁ ≤ 0, with U₂ | I₂ ~ N(0, 1).

Both instances are exactly calibrated and the selection is I₂-measurable. The record-weighted rate is (δ + ½δ)/(1 + ½) = δ. The log-weighted rate, the expected share of a log's selected instances above z_{1−δ}, is P(U₁ > z_{1−δ}) + P(U₁ ≤ 0)·δ/2 = 1.25δ, which is 0.0625 at δ = 0.05. Selecting instance 2 iff U₁ > 0 instead gives 0.75δ. [C: P1ii_logweighted_toy]

*Remark on object-conditional coverage.* Exact object-conditional coverage cannot be certified distribution-free at non-atoms [Vovk2012, Prop. 4]. An open-loop audit also selects matched true positives and censors at the horizon, so it estimates (ii) only up to these selection effects.

**Proposition 2 (dilution).** Assume that along a_j the projection of X_j − m̂_j given I_k is N(0, p_j + q_j), with q_j > 0 (process noise correct) and p_j = κ_jp̂_j. Then

  P(U_j > c | I_k) = Φ̄(c√r_j),  r_j = (ρ̂_j + 1)/(κ_jρ̂_j + 1).

- For κ_j > 1, r_j decreases from 1 to 1/κ_j as ρ̂_j runs from 0 to ∞; for κ_j < 1 it increases from 1 to 1/κ_j; for κ_j = 1 it equals 1. If q_j = 0, r_j = 1/κ_j.
- Multiplying Σ̂ by s > 0 (so p̂_j ↦ sp̂_j, with q_j unchanged) multiplies the margin c√v̂_j by √((sρ̂_j + 1)/(ρ̂_j + 1)). For s ≠ 1 this factor is the same for all evaluated tuples **iff ρ̂_j is the same for all of them**, in particular when q_j ≡ 0 (factor √s).

*Proof.* U_j | I_k ~ N(0, (p_j + q_j)/(p̂_j + q_j)), so P(U_j > c | I_k) = Φ̄(c√((p̂_j + q_j)/(κ_jp̂_j + q_j))). Dividing numerator and denominator by q_j > 0 gives r_j. By the quotient rule, dr/dρ̂ = (1 − κ)/(κρ̂ + 1)², whose sign is that of 1 − κ; r(0) = 1 and r → 1/κ as ρ̂ → ∞. With q_j = 0, r_j = p̂_j/p_j = 1/κ_j. For the dose, √(sp̂_j + q_j) = √v̂_j·√((sρ̂_j + 1)/(ρ̂_j + 1)). The map g(ρ̂) = (sρ̂ + 1)/(ρ̂ + 1) has g′(ρ̂) = (s − 1)/(ρ̂ + 1)² ≠ 0 for s ≠ 1, so it is injective on [0, ∞], with g(∞) = s. The factor is therefore common to all tuples iff the ρ̂_j are. ∎ [C: P2_dilution; P2_global_dose_constancy: two tuples with q > 0 and ρ̂ = 1 share the factor √2.5 at s = 4]

**Proposition 3 (transfer to estimate-chosen separating axes).** *Notation.* An audit item i is a (record, axis) pair at step k(i), with:
- axis a_i ∈ {a_L(ψ̂), a_T(ψ̂)} from the estimated yaw, and toward-ego orientation a*_i = a_i·sign(a_iᵀ(c_e − m̂));
- v_i = a*_iᵀΣ̂a*_i > 0;
- an estimate-only selection S_i (separating filter, in-path filter, cell);
- the annotated position X^gt = X + η, with η independent of (X, I_k);
- U_i = a*_iᵀ(X^gt − m̂)/√(v_i + σ_a²).

**Condition (M):** a*_i, v_i, 1_{S_i} and the weight w_i are I_{k(i)}-measurable. Under (M):
- **(A1)** For any I_k-measurable b, P(a*ᵀX > b | I_k) = P(U^true > τ | I_k), with U^true = a*ᵀ(X − m̂)/√v and τ = (b − a*ᵀm̂)/√v. Take b = a*ᵀc_e − h_obj(a) − h_ego(a), and suppose the true yaw and extents equal the estimates. Then footprint overlap implies a*ᵀX ≥ b, so a premise at τ bounds the overlap probability. The separating filter makes τ > 0.
- **(A2)** If P(U_i > z | I_{k(i)}) ≤ δ on S_i for every i, the record-weighted exceedance E[Σ_i w_i1_{S_i}1{U_i > z}]/E[Σ_i w_i1_{S_i}] is at most δ. If X − m̂ | I_k ~ N(0, Σ̂) and η ~ N(0, σ_a²I) independently, it equals Φ̄(z) exactly.
- **(A3)** Theorem 1 transfers axis by axis.
- **(A4)** The single-multiplier price transfers in a distribution-free, cell-level form. Let E_g(c) be the pooled exceedance of cell g at multiplier c and m_g = inf{c : E_g(c) ≤ δ}. A global multiplier that meets every cell has c ≥ max_g m_g and pays (c − m_g)·sd on each item of cell g. It pays nothing iff all m_g are equal and c equals them. Theorem 2 transfers only under the mapping q ↦ σ_a².

*Proof.*
- (A1) This is Proposition 1(i) with normal a*. Its proof uses only the measurability of (a*, b, m̂, v), which (M) supplies. For the inclusion: the projections of the two footprints on a* are [a*ᵀX − h_obj, a*ᵀX + h_obj] and [a*ᵀc_e − h_ego, a*ᵀc_e + h_ego]. If the footprints overlap, so do their projections; hence a*ᵀX + h_obj ≥ a*ᵀc_e − h_ego, that is, a*ᵀX ≥ b. The filter |a*ᵀ(c_e − m̂)| > h_obj + h_ego, with the toward-ego sign, gives b − a*ᵀm̂ > 0.
- (A2) This is Proposition 1(ii) with weights w_i1_{S_i}. Under the Gaussian posterior, a*_i is fixed given I_k, so a*_iᵀ(X − m̂) + a*_iᵀη | I_k ~ N(0, v_i + σ_a²) and P(U_i > z | I_k) = Φ̄(z) on S_i; substitute in the ratio.
- (A3) Each case of Theorem 1 is a statement about the law of e = X − m̂ given I_k along fixed directions. Rotating a construction so that its axis is the I_k-measurable a*_i gives the same non-implications. Case (b) survives annotation noise: given e, |e + η|²/σ_a² is non-central χ²₂ with non-centrality |e|²/σ_a². This depends on e only through |e| = R, whose law does not depend on the angle. So the law of |e + η|² is the one under a uniform angle, where e + η ~ N(0, (1 + σ_a²)I₂), and |e + η|²/(1 + σ_a²) ~ χ²₂ for every angle law.
- (A4) E_g(c) ≤ δ implies c ≥ m_g by the definition of the infimum. The margin is c·sd, so the excess over m_g·sd is (c − m_g)·sd ≥ 0, which is zero in every cell iff c = m_g for all g. ∎

[C: P3_A2_posterior_exact: 0.04999 on 3.0 × 10⁶ selected items of a Gaussian-posterior toy with the separating filter and toward-ego orientation, Monte Carlo SE 0.00013. A fixed-truth-calibrated tracker on the same geometry gives 0.059. C: P3_A3_annotation_noise]

*Not covered:*
- fixed-truth calibration, which does not give (A2) (0.059 against 0.050 above);
- selection that depends on outcomes: matched true positives, the 2 m first association, censoring and contested-pair exclusion;
- weights not measurable at I_{k(i)}, such as scene or log weights;
- a misspecified σ_a, under which U | I_k ~ N(0, (v + σ_true²)/(v + σ_a²));
- sufficiency: only cell-level necessity holds;
- proxy normals in place of the planner's.

**Remark 2 (orientation null).** The orientation null E⁰ of a cell is computed without ground truth:
- each candidate's estimate is taken as the truth;
- a pseudo-estimate m̂ + e′, e′ ~ N(0, Σ̂ + σ_a²I), is drawn;
- the separating filter and the orientation are re-evaluated on the pseudo-estimate;
- E⁰ = P(U⁰ > z_{0.95} | kept), pooled over candidates and draws, with the candidates taken before the real filter.

*(i) What holds.* Under I_k-conditional calibration and (M), a cell's record-weighted exceedance is at most δ (Proposition 3(A2)). Since max(δ, E⁰) ≥ δ pointwise, judging a cell against max(δ, E⁰) cannot raise the false-flag probability; E⁰ adds conservatism only.

*(ii) What fails.* E⁰ does not bound the exceedance of a fixed-truth-calibrated tracker. Take one dimension along the axis, in units of the exported SD, with σ_a = 0, separating half-width h = 6, true offset d = h + x, and m̂ = X + e, e ~ N(0, 1). An item is kept iff |d − e| > h, and U = sign(d − e)·(−e). Then

  E^FT = [Φ(min(d − h, −z)) + Φ̄(max(d + h, z))] / [Φ(d − h) + Φ̄(d + h)].

At x = −1 (the truth one SD inside the boundary) this is Φ(−z_{0.95})/Φ(−1) up to a term below 10⁻²⁷, that is 0.05/0.15866 = 0.3151. The null on the same geometry is

  E⁰ = [∫_{−∞}^{−z} φ(e′)Φ(d − h − e′)de′ + ∫_z^∞ φ(e′)Φ̄(d + h − e′)de′] / [Φ((d − h)/√2) + Φ̄((d + h)/√2)] = 0.1754,

and 0.0734 if only candidates that pass the real filter are used. For truths outside the boundary E⁰ is conservative (x = +1: E^FT = 0.0594, E⁰ = 0.0657). [C: R2_orientation_null] Section V-B therefore also requires a truth-oriented failure.

### S8.3 NEES versus the premise

**Proposition 4 (plan-uniform criterion) [main text: Proposition 2].** For V̂ ≻ 0, e ≠ 0 and a ≠ 0, (aᵀe)²/(aᵀV̂a) ≤ eᵀV̂⁻¹e, with equality iff a ∝ V̂⁻¹e. Hence, for c ≥ 0, P(N > c² | I_k) ≤ δ implies P(U > c | I_k) ≤ δ for every I_k-measurable a. Under Gaussian truth in two dimensions, certifying through N costs the margin ratio √(χ²_{2;1−δ})/z_{1−δ} = √(−2 ln δ)/z_{1−δ}, which is 1.30 at δ = 0.01.

*Proof.* Write x = V̂^{1/2}a and y = V̂^{−1/2}e. Then aᵀe = xᵀy, aᵀV̂a = |x|² and eᵀV̂⁻¹e = |y|². The Cauchy–Schwarz inequality gives (xᵀy)² ≤ |x|²|y|², with equality iff x ∝ y, that is, iff a ∝ V̂⁻¹e. With e = X − m̂ this says U² ≤ N pointwise (trivially if e = 0). For c ≥ 0, {U > c} ⊂ {U² > c²} ⊂ {N > c²}, so P(U > c | I_k) ≤ P(N > c² | I_k), simultaneously for every I_k-measurable a.

For the ratio, let X − m̂ | I_k ~ N(0, V̂). Along a fixed a, U ~ N(0, 1), so the smallest valid c is z_{1−δ}. N ~ χ²₂ with P(N > x) = e^{−x/2}, so the smallest c with P(N > c²) ≤ δ is √(−2 ln δ). At δ = 0.01 this is 3.0349 against z_{0.99} = 2.3263, a ratio of 1.3046 (at δ = 0.05, 2.4477/1.6449 = 1.488). ∎ [C: P4_cauchy_schwarz, P4_margin_ratio]

A planner with a Mahalanobis keep-out consumes P(N > c²) itself, so for it N is the matched criterion.

**Remark 3 (Schur).** Partition V̂ ≻ 0 with V̂₁₁ the position block, and e = (e₁, e₂) accordingly. Then e₁ᵀV̂₁₁⁻¹e₁ ≤ eᵀV̂⁻¹e. A population pass of the nine-dimensional 95 % NEES test, P(N₉ > χ²_{9;0.95}) ≤ 0.05, therefore bounds only P(U > √χ²_{9;0.95}) ≤ 0.05 along position directions, with √χ²_{9;0.95} = √16.919 = 4.113.

*Proof.* With the Schur complement S = V̂₂₂ − V̂₂₁V̂₁₁⁻¹V̂₁₂ ≻ 0,

  eᵀV̂⁻¹e = e₁ᵀV̂₁₁⁻¹e₁ + (e₂ − V̂₂₁V̂₁₁⁻¹e₁)ᵀS⁻¹(e₂ − V̂₂₁V̂₁₁⁻¹e₁) ≥ e₁ᵀV̂₁₁⁻¹e₁.

Proposition 4 on the position block gives U² ≤ e₁ᵀV̂₁₁⁻¹e₁ ≤ N₉ for every position direction; conclude as in Proposition 4. ∎ [C: R3_schur_radius]

**Theorem 1 (NEES and the premise do not imply each other, in two dimensions) [main text: Theorem 1; (b) also in Appendix A].** In each case e = X − m̂ has the stated law given I_k, the export is V̂, and the risk along a is P(aᵀe/√(aᵀV̂a) > z_{1−δ}). The level is δ = 0.01 unless stated.

**(a)** Truth N(0, I₂), export V̂ = diag(2, 2/3): E[N] = 2, exactly consistent in mean, yet the risk along the second axis is 0.0288.

*Proof.* E[N] = E[eᵀV̂⁻¹e] = tr(V̂⁻¹Cov(e)) = ½ + 3/2 = 2. Along e₂, U = e₂/√(2/3) ~ N(0, 3/2), so the risk is Φ̄(z_{0.99}√(2/3)) = Φ̄(1.8994) = 0.02875. Moreover N = e₁²/2 + 3e₂²/2 has mean 2 and variance 2(¼ + 9/4) = 5, against 4 for χ²₂. A two-sided 95 % ANEES test over M independent samples therefore accepts with probability tending to 2Φ(1.96·2/√5) − 1 = 0.920 as M grows: the mean test does not reject this export in the limit. ∎ [C: T1a]

**(b)** A whole-vector χ² test can be passed exactly while the risk along some direction exceeds δ. Let R² ~ χ²₂ and let θ be an angle with any law, independent of R; set e = R(cos θ, sin θ) and export V̂ = I₂.

*Proof.*
1. **N is exactly χ²₂.** N = eᵀe = R², whose law does not involve θ. Every test that uses only the law of N, such as the χ² test with any acceptance region, the ANEES test or the p_v statistic, behaves exactly as under a calibrated Gaussian. For example, P(N > χ²_{2;0.95}) = e^{−χ²_{2;0.95}/2} = 0.0500 exactly.
2. **The risk along a direction.** Let a_φ = (cos φ, sin φ). With V̂ = I₂, U_φ = a_φᵀe = R cos(θ − φ). Since P(R > r) = P(R² > r²) = e^{−r²/2} for r ≥ 0 and z = z_{1−δ} > 0,

  P(U_φ > z | θ) = h(θ − φ),  h(ψ) = exp(−z²/(2cos²ψ))·1{cos ψ > 0},

  so the risk along a_φ is risk(φ) = E[h(θ − φ)].
3. **The direction average is exactly δ.** By Fubini's theorem and periodicity,

  (1/2π)∫₀^{2π} risk(φ)dφ = E[(1/2π)∫₀^{2π} h(θ − φ)dφ] = (1/2π)∫₀^{2π} h(ψ)dψ.

  The right-hand side is the risk when θ is uniform. Then e ~ N(0, I₂) and U_φ ~ N(0, 1), so it equals Φ̄(z) = δ. Since risk(φ) is continuous in φ (dominated convergence), max_φ risk(φ) ≥ δ, with equality iff risk(φ) = δ for every φ. So for **every** angle law whose directional risk is not constant, some direction has risk above δ, while every N-based test is passed exactly.
4. **The example.** Let θ = θ₀ + πB, with θ₀ ~ N(0, s²) and B a fair bit independent of θ₀. The symmetry θ ↦ θ + π gives E[e] = 0. For cos ψ ≠ 0 exactly one of h(ψ) and h(ψ + π) is non-zero, and h(ψ) + h(ψ + π) = exp(−z²/(2cos²ψ)); hence, along a₀ = (1, 0),

  risk(0) = ½·E[exp(−z²/(2cos²θ₀))].

  One-dimensional quadrature at z = z_{0.99} gives 0.02682, 0.01808 and 0.01214 for s = 0.3, 0.6 and 1.0. As s → 0 the risk tends to ½e^{−z²/2} = 0.0334, and as s → ∞ it tends to 0.01.
5. **What the joint test misses.** Var(e₁) = E[R²]E[cos²θ₀] = 1 + e^{−2s²}, which is 1.835 at s = 0.3: the covariance is wrong along a₀. The one-dimensional NEES along a₀, whose mean is Var(e₁), detects it; the two-dimensional test cannot. ∎ [C: T1b; the Monte Carlo check also confirms p_v95 = 0.050 and the three risks to within 5 × 10⁻⁴]

*A published example of this kind* [Forsling2025]: for Σ = [[8, 1], [1, 2]] and P = diag(8, 2), E[N] = tr(P⁻¹Σ) = 2, while the whitened covariance P^{−1/2}ΣP^{−1/2} = [[1, ¼], [¼, 1]] has eigenvalues 0.75 and 1.25. [C: T1b_forsling]

**(c)** Truth diag(1, 4), export I₂, binding direction e₁: the binding direction is calibrated, yet E[N] = 5. Matching the average NEES globally (×2.5) gives a risk of 0.00012 along it, where 0.01 was required.

*Proof.* E[N] = tr(I₂⁻¹diag(1, 4)) = 5. Along e₁, U = e₁ ~ N(0, 1), so the risk is exactly δ: the premise holds on the binding direction (it fails along e₂, with risk Φ̄(z_{0.99}/2) = 0.122). The NEES-guided correction multiplies the export by k = E[N]/2 = 2.5, giving U′ = e₁/√2.5 and risk Φ̄(z_{0.99}√2.5) = Φ̄(3.678) = 1.17 × 10⁻⁴. ∎ [C: T1c]

**(d)** Second moments do not determine a 1 % tail. Let e = (T₁, T₂)/√3 with T₁, T₂ independent t₃ variables and export I₂.

*Proof.* Var(T_i) = ν/(ν − 2) = 3, so Cov(e) = I₂ and E[N] = 2: the export matches the error covariance exactly. The risk along e₁ is P(T₁ > √3z). The t₃ distribution has the closed form P(T > t) = ½ − (1/π)[arctan(t/√3) + (t/√3)/(1 + t²/3)], so with t = √3z,

  risk = ½ − (arctan z + z/(1 + z²))/π.

This is 0.01374 at δ = 0.01 and 0.00638 at δ = 0.001, both above δ; at δ = 0.05 it is 0.03258, conservative. ∎ [C: T1d] Case (d) defeats checks based on first and second moments, such as ANEES. A full goodness-of-fit test of N against χ²₂ would detect it with enough data, since N is not χ²₂ here.

### S8.4 The price of one knob

**Proposition 5 (single knobs and their prices).** Assume Proposition 2's truth with tuple-specific (κ_j, ρ̂_j), p̂_j > 0, and a target level δ.
- **(a)** A multiplier c meets the premise for every j iff c ≥ max_j m_j, where m_j = z_{1−δ}√((κ_jρ̂_j + 1)/(ρ̂_j + 1)). The excess margin at j is (c − m_j)√v̂_j.
- **(b)** An inflation s of Σ̂ meets it for every j iff s ≥ max_j κ_j. The excess at j is z_{1−δ}[√(s·p̂_j + q_j) − √(κ_j·p̂_j + q_j)].
- **(c)** Let w_j > 0 with Σ_j w_j = 1, and choose c so that the weighted average risk equals δ. Then max_j risk_j ≥ δ, with equality iff all m_j are equal.

*Proof.*
- (a) By Proposition 2, risk_j(c) = Φ̄(c√r_j). Since Φ̄ is strictly decreasing, risk_j(c) ≤ δ iff c√r_j ≥ z_{1−δ}, that is, iff c ≥ z_{1−δ}/√r_j = m_j. Requiring this for all j gives c ≥ max_j m_j. The margin is c√v̂_j, and the excess over m_j√v̂_j is (c − m_j)√v̂_j.
- (b) With inflation s the margin is z_{1−δ}√(sp̂_j + q_j) and the true SD √(κ_jp̂_j + q_j), so risk_j = Φ̄(z_{1−δ}√((sp̂_j + q_j)/(κ_jp̂_j + q_j))) ≤ δ iff sp̂_j ≥ κ_jp̂_j, that is, iff s ≥ κ_j. The excess is the difference of the two margins.
- (c) F(c) = Σ_j w_j·risk_j(c) is continuous and strictly decreasing, from F(0) = ½ to 0 as c → ∞, so a unique c_agg with F(c_agg) = δ exists. If every risk_j(c_agg) were ≤ δ and one were < δ, then F(c_agg) < δ, a contradiction; hence max_j risk_j(c_agg) ≥ δ. If the maximum equals δ, the weighted average δ forces every risk_j(c_agg) = δ, that is, c_agg = m_j for every j; conversely, equal m_j give risk_j(c_agg) = δ for all j. ∎ [C: P5c_aggregate: on Theorem 2's first pair with equal weights, c_agg = 2.893 and the risks are 0.0037 and 0.0163]

**Theorem 2 (the two knobs are not equivalent when q ≢ 0).** At δ = 0.01, with excesses in units of the exported SD √v̂_j:
- for (κ, ρ̂) ∈ {(2, 0.2), (2, 5)}, inflation is exact for both tuples, while the multiplier knob costs 0.637;
- for (κ, ρ̂) ∈ {(2, 1), (3, 1/3)}, the multiplier knob is exact for both (2.849 each), while inflation costs 0.441.

Neither knob dominates.

*Proof.* By Proposition 5, with z_{0.99} = 2.32635:
- First pair: m = z√(1.4/1.2) = 2.5127 and z√(11/6) = 3.1499. Inflation needs s ≥ max κ = 2 = κ_j for both tuples, so s = 2 is exact for both. The multiplier must be ≥ 3.1499, an excess of 3.1499 − 2.5127 = 0.6371 at the first tuple.
- Second pair: m = z√(3/2) = 2.8492 and z√(2/(4/3)) = 2.8492, so the multiplier 2.8492 is exact for both. Inflation needs s ≥ 3. At (2, 1), where p̂ = q and v̂ = 2q, its excess is z[√(3p̂ + q) − √(2p̂ + q)]/√v̂ = z(√2 − √1.5) = 0.4408. ∎ [C: T2_knobs]

### S8.5 Certification with the log as the unit

This section restates Proposition 6 with the unit the registered test used: the log. It proves it from first principles, with the conformal-risk-control step written out.

**Setting.**
- **Logs and items.** A log Z is a random element of a measurable space. A fixed *item map* turns Z into a finite, possibly empty, multiset of items (x, U), with features x and score U ∈ ℝ. In the registered Argoverse 2 test a log is one drive segment of about 15 s. Its items are M\*'s calibration items (Section IV-A): every enforced pair at every decision state and calibrated check time, one item per object axis that separates the pair at the reference pose. The features include the check time and the in-path flag, because M\* is fitted separately for each (check time, in-path flag). A *stratum* g is therefore a (check time, in-path flag, level-0 stratum) triple, and a *cell* C a (check time, in-path flag, coarser cell) triple. Items within a log may be arbitrarily dependent: they share tracks, consecutive decision states and the ego trajectory.
- **Membership and loss.** n_g(Z) is the number of Z's items in g, and A_g(Z) = 1{n_g(Z) ≥ 1}. For A_g(Z) = 1 the *log loss* is

  L_g(Z; c) = (1/n_g(Z))·Σ_{items of Z in g} 1{U > c},  c ∈ ℝ ∪ {+∞}.

- **Calibration and threshold.** Calibration logs Z₁, …, Z_m; I_g = {i : A_g(Z_i) = 1}; N_g = |I_g|; R̂_g(c) = (1/N_g)Σ_{i∈I_g} L_g(Z_i; c);

  ĉ_g = inf{c ∈ ℝ : (N_g/(N_g + 1))·R̂_g(c) + 1/(N_g + 1) ≤ δ},  with inf ∅ = +∞.

**Assumptions.**
- **(L1) I.i.d. logs.** Z₁, …, Z_m and Z_test are independent and identically distributed. This is the modeling assumption of the test. It treats logs recorded in the same city or on the same day as independent draws from the population of logs. It is not testable from the data.
- **(L2) A fixed item map.** The item map, the stratum map and every ingredient of U are fixed without using Z₁, …, Z_m or Z_test. The ingredients include the detector, the tracker's Q and R, σ_a, the cut-points and the planner that defines enforced pairs. In the registered test the detector was not trained on the 375 logs and both trackers keep their nuScenes parameters (Section V-D). The item map may use anything inside the log, including the logged future ego pose; this matters for S8.7, not here. If an ingredient was fitted on the evaluation logs, Remark 4 applies instead.
- **(L3) Positive membership.** P(A_g(Z) = 1) > 0.

**Properties of the log loss.** For each log with A_g(Z) = 1, c ↦ L_g(Z; c):
- (F1) is non-increasing, because each 1{U > c} is;
- (F2) is right-continuous, because 1{U > c} → 1{U > c₀} as c ↓ c₀ (for U > c₀ eventually c < U; for U ≤ c₀ the indicator is always 0), and a finite average preserves this;
- (F3) takes values in [0, 1], so it is bounded by B = 1;
- (F4) satisfies L_g(Z; +∞) = 0, and L_g(Z; c) = 0 for c ≥ the log's largest g-score;
- (F5) satisfies L_g(Z; c) = 1 for c below the log's smallest g-score.

**Lemma A.1 (conformal risk control, in the form used).** [Angelopoulos2024, Thm 1] states: if L₁, …, L_{n+1} are exchangeable random functions of λ that are non-increasing and right-continuous, with L_i(λ_max) ≤ α and sup_λ L_i(λ) ≤ B < ∞ almost surely, then λ̂ = inf{λ : (n/(n + 1))R̂_n(λ) + B/(n + 1) ≤ α}, with λ̂ = λ_max if the set is empty, satisfies E[L_{n+1}(λ̂)] ≤ α. We use it with λ = c, λ_max = +∞, B = 1 and α = δ. For completeness, here is the proof in this setting.

Let α ∈ (0, 1). Let ℓ₁, …, ℓ_{n+1} be random functions on ℝ ∪ {+∞} with values in [0, 1] such that:
- (C1) (ℓ₁, …, ℓ_{n+1}) is exchangeable;
- (C2) each ℓ_i is non-increasing;
- (C3) each ℓ_i is right-continuous;
- (C4) each ℓ_i is bounded by B = 1;
- (C5) ℓ_i(+∞) ≤ α;
- (C6) ℓ_i(c) = 1 for all c below some finite random point.

Let R̂_n = (1/n)Σ_{i≤n}ℓ_i and λ̂ = inf{c : (n/(n + 1))R̂_n(c) + 1/(n + 1) ≤ α}, with λ̂ = +∞ if the set is empty. Then E[ℓ_{n+1}(λ̂)] ≤ α.

*Proof.* Let R̂_{n+1}(c) = (1/(n + 1))Σ_{i=1}^{n+1}ℓ_i(c) and λ̂′ = inf{c : R̂_{n+1}(c) ≤ α}.
1. **The oracle is attained.** By (C5) the set {c : R̂_{n+1}(c) ≤ α} contains +∞. By (C6) and α < 1 it contains no c below the smallest of the n + 1 finite points, so λ̂′ is finite or +∞. By (C2)–(C3), R̂_{n+1} is non-increasing and right-continuous, so the set is an interval [λ̂′, +∞] that contains its left end: if c_r ↓ λ̂′ with R̂_{n+1}(c_r) ≤ α, then R̂_{n+1}(λ̂′) = lim_r R̂_{n+1}(c_r) ≤ α.
2. **The oracle is below the rule.** For every c in the set that defines λ̂, (C4) gives R̂_{n+1}(c) = (n/(n + 1))R̂_n(c) + ℓ_{n+1}(c)/(n + 1) ≤ (n/(n + 1))R̂_n(c) + 1/(n + 1) ≤ α. So that set lies in [λ̂′, +∞], and λ̂ ≥ λ̂′; this also holds when the set is empty and λ̂ = +∞. This is the role of the "+ 1/(n + 1)" term: it bounds the unseen test loss by B = 1.
3. **Monotonicity.** By (C2), ℓ_{n+1}(λ̂) ≤ ℓ_{n+1}(λ̂′).
4. **Symmetry.** λ̂′ is a symmetric function of (ℓ₁, …, ℓ_{n+1}). By (C1), the pair (ℓ_i, λ̂′) has the same law for every i. Hence E[ℓ_{n+1}(λ̂′)] = (1/(n + 1))Σ_i E[ℓ_i(λ̂′)] = E[R̂_{n+1}(λ̂′)] ≤ α by step 1.

Combining steps 3 and 4, E[ℓ_{n+1}(λ̂)] ≤ α. (Measurability holds because each ℓ_i is a step function determined by finitely many scores.) ∎

If n + 1 < 1/α, the set defining λ̂ is empty, because R̂_n ≥ 0 and 1/(n + 1) > α. Then λ̂ = +∞ and the bound is trivial. For the log losses below, which vanish at and above a log's largest score (property F4), the set contains every c at or above the largest calibration score when n ≥ 1/α − 1, so λ̂ is finite. At α = 0.05 this is n ≥ 19.

**Lemma A.2 (conditioning on membership).** Assume (L1) and (L3). Conditionally on the membership vector (A_g(Z₁), …, A_g(Z_m)) = a ∈ {0, 1}^m and on A_g(Z_test) = 1, the logs {Z_i : a_i = 1} and Z_test are i.i.d. with law Q_g = Law(Z | A_g(Z) = 1). Hence the N_g + 1 loss functions L_g(Z_i; ·), i ∈ I_g, and L_g(Z_test; ·) are exchangeable.

*Proof.* Let B_i = {A_g = a_i}, B_test = {A_g = 1}, and let P_Z be the law of a log. By (L1) the joint law is the product P_Z^{⊗(m+1)}, and the conditioning event ∩_i{Z_i ∈ B_i} ∩ {Z_test ∈ B_test} has probability Π_i P_Z(B_i)·P_Z(B_test) > 0 by (L3), restricting a to vectors of positive probability. For measurable sets E_i,

  P(∩_i{Z_i ∈ E_i} | ∩_i{Z_i ∈ B_i}) = Π_i P_Z(E_i ∩ B_i)/Π_i P_Z(B_i) = Π_i P_Z(E_i | B_i),

including the test log. So, given the memberships, the logs are independent, and those with A_g = 1, the test log among them, all have law P_Z(· | A_g = 1) = Q_g. An i.i.d. sequence is exchangeable, and the loss functions are one fixed map (by (L2)) applied to each log, so they are exchangeable. ∎

If the logs are only exchangeable, not i.i.d., the same conclusion holds conditionally on the membership pattern. A permutation of the logs that maps the member set J onto itself leaves the event {members = J} unchanged, so it preserves the conditional law given that event; the member logs, the test log among them, are therefore exchangeable given the pattern.

**Lemma A.3 (the threshold is an observed score, and the code computes it).** Let N_g = n ≥ 1, and let 𝒰 be the set of distinct scores of the calibration g-items.
- R̂_g is a right-continuous step function whose jumps lie in 𝒰, with R̂_g(c) = 1 below min 𝒰 and R̂_g(c) = 0 at and above max 𝒰.
- Hence the set {c : (n/(n + 1))R̂_g(c) + 1/(n + 1) ≤ δ} is empty if n < 1/δ − 1. Otherwise it equals [u*, +∞), where u* is the smallest u ∈ 𝒰 that satisfies the inequality. In particular ĉ_g = u* ∈ 𝒰 is attained.
- The code (`crc_threshold_exact`, c1_crc_exact_v01; with `fit_hier`, m_lib_v04) returns `None` when 1/(n + 1) > δ, the case handled by fallback.
- Otherwise it bisects over the sorted 𝒰 with the predicate Σ_{i∈I_g} x_i/t_i ≤ δ(n + 1) − 1, evaluated in rational arithmetic with δ = 1/20. Here x_i is log i's number of g-items above c and t_i its number of g-items. This is the defining inequality multiplied by n + 1.
- The predicate is monotone in c, so the bisection returns u*. The fall-through branch "largest score + 10⁻⁹" is unreachable: at c = max 𝒰 the left side is 0 ≤ δ(n + 1) − 1 whenever n ≥ 19.
- At n = 19 the right side is 0, so u* = max 𝒰.

[C: P6a_threshold_is_infimum: 300 data sets with ties, every rule output equal to the infimum, the floor case equal to the largest score, and the floating-point rule used in the simulations equal to the exact rule]

**Proposition 6 (per-stratum validity, the log as the unit) [main text: Proposition 3; proof also in Appendix A].** Assume (L1)–(L3) and δ = 0.05. Let ĉ_g be fitted on the g-items of the calibration logs in I_g. Then, for every membership vector a with Σ_i a_i = n ≥ 19,

  E[L_g(Z_test; ĉ_g) | (A_g(Z_i))_{i≤m} = a, A_g(Z_test) = 1] ≤ δ.

Consequently E[L_g(Z_test; ĉ_g) | N_g = n, A_g(Z_test) = 1] ≤ δ for every n ≥ 19, and E[L_g(Z_test; ĉ_g) | N_g ≥ 19, A_g(Z_test) = 1] ≤ δ. Equivalently, if J is drawn uniformly from the test log's g-items, independently of everything else given the logs, then P(U_J > ĉ_g | N_g = n, A_g(Z_test) = 1) ≤ δ. For N_g < 19, ĉ_g = +∞ and the loss is 0; the deployed rule then uses a fallback (Proposition 7).

*Proof.*
1. **Exchangeability.** Fix a with Σ_i a_i = n ≥ 19. By Lemma A.2, under P(· | A = a, A_g(Z_test) = 1) the n calibration loss functions L_g(Z_i; ·), i ∈ I_g, and L_g(Z_test; ·) are exchangeable.
2. **The conditions of Lemma A.1.** By (F1)–(F5) they satisfy (C2)–(C6) with B = 1 and α = δ < 1. ĉ_g is the λ̂ of Lemma A.1 computed from the n calibration losses.
3. **The bound.** Lemma A.1 gives the bound conditionally on (A = a, A_g(Z_test) = 1). Average over the vectors a with Σ_i a_i = n, by the law of total expectation, for the statement given N_g = n; then over n ≥ 19 for the last statement.
4. **The item form.** For every fixed c, E[1{U_J > c} | logs] = L_g(Z_test; c). ĉ_g is a function of the calibration logs, so E[1{U_J > ĉ_g} | logs] = L_g(Z_test; ĉ_g); take expectations. ∎

[C: P6b_validity_log_unit: i.i.d. logs with a log random effect, 300 calibration logs, membership 0.6, exact conditional risk given ĉ: mean 0.0453 (SE 0.0001) with a Gaussian log effect, 0.0452 with a t₄ log effect. C: P6c_validity_near_floor: N_g ~ Bin(300, 0.065); mean 0.0102 given N_g ≥ 19, 0.0035 at N_g = 19, where ĉ is the largest calibration score]

*What is, and is not, conditioned on.*
- The bound holds conditionally on the stratum's membership vector, and requires the test log to contain g. It is marginal over everything else: the calibration logs' scores, their item counts, the test log's item count, and the other strata's thresholds.
- It is **not** conditional on the calibration logs. The risk of the one rule fitted on a given calibration set exceeds δ with substantial probability, because conformal risk control is nearly tight: in the check above, 24 % of calibration draws gave a conditional risk above δ (26 % with the t₄ log effect).
- It holds for one stratum at a time. No simultaneous bound over the 192 strata of a check time is asserted.
- It weights logs, not items: each test log counts once, and its stratum items share its weight.

**Corollary A.4 (cross-fitting on Argoverse 2).** Let the 375 logs satisfy (L1)–(L3). The folds F₁, …, F₅ of 75 logs are fixed independently of the logs' contents; the registered test sorts the log identifiers, permutes them with a fixed seed and cuts the result into five blocks. For fold f, ĉ_g^{(f)} is fitted on the logs outside F_f (300 logs), and N_g^{(−f)} is their number of members of g.
- **(i)** For every t ∈ F_f and every membership vector a of the 375 logs with a_t = 1 and N_g^{(−f)}(a) ≥ 19, E[L_g(Z_t; ĉ_g^{(f)}) | A = a] ≤ δ.
- **(ii)** The cross-fitted, log-weighted estimate Ê_g = (1/|T_g|)Σ_{t∈T_g} L_g(Z_t; ĉ_g^{(f(t))}), with T_g = {t : a_t = 1}, satisfies E[Ê_g | A = a] ≤ δ whenever N_g^{(−f)}(a) ≥ 19 for all five folds, that is, when g has its own threshold in every fold.

*Proof.* (i) Given A = a, Lemma A.2, applied to all 375 logs, makes the logs independent and the members i.i.d. Q_g. For t ∈ F_f, the members outside F_f and Z_t are therefore i.i.d. Q_g, hence exchangeable, and ĉ_g^{(f)} is the λ̂ of Lemma A.1 computed from the former. Lemma A.1 applies. (ii) Ê_g is an average with weights fixed by a, so linearity gives the bound. The 75 test logs of a fold share one calibration set, which makes the summands dependent; this does not affect the expectation. ∎ [C: P6d_crossfit: mean 0.0453, SE 0.0001, 2000 draws]

If g has its own threshold in some folds and falls back in others, Ê_g mixes Proposition 6 terms with Proposition 7(ii) terms and has no bound. The bootstrap bounds of Section V estimate E[Ê_g]; they are not part of the corollary.

**Remark 4 (tuning on the evaluation logs: the transductive reading).** Assume condition (P): the tracker runs per log with no state carried across logs, and no score ingredient is fitted on the calibration part only or the test part only.
- **(B1)** Condition on the data D: the set of logs and every ingredient θ̂ = T(D) fitted on it. Let the split be uniformly random and independent of D, and let n and m be the numbers of g-logs in the calibration and test parts. Then E[L_g(T; ĉ_g) | D, n, m] ≤ δ for a test log T drawn uniformly from the test part's g-logs. The same bound therefore holds for the test-part average.

  *Proof.* Given D, every loss function is fixed. A uniformly random split assigns the g-logs to the two parts by a uniformly random partition of sizes n and m. With T uniform in the test part, calibration ∪ {T} is a uniformly random (n + 1)-subset and T is uniform within it. The n + 1 losses are therefore exchangeable, and Lemma A.1 applies. ∎ The same argument covers the registered test's cross-fitting if the fold partition is treated as uniformly random.

  *Not for a fixed test log.* The bound does not hold for a fixed test log: if one log has all scores far above the others, its loss is 1 whenever it falls in the test part. [C: R4_fixed_test_log: 40 logs split 20 + 20; test-part average 0.047, the fixed extreme log's loss 1.000]
- **(B2)** If D is exchangeable and T is a symmetric function of the logs, the exchangeable form of Lemma A.2 applies to the pairs (L_g(Z_j; T(D)), A_g(Z_j)).
- **(B3)** There is no new-log guarantee in this case. A new log is not exchangeable with the evaluation logs when T used them. A new-log reading needs (L2): every ingredient of the score fitted outside the evaluation logs.

**Remark A.5 (the scene as the unit on nuScenes).** The nuScenes development fits used the 20 s scene as the unit, and scenes are cut from longer logs. Under (L1) for logs, scenes from one log are dependent, Lemma A.2 does not apply to scenes, and Proposition 6 with the scene as the unit can fail for a scene from an unseen log.

*Exact example.* n′ logs each contribute K scenes whose single items are identical (perfect within-log dependence); scores are continuous and i.i.d. across logs; δ = 1/20.
- With the scene as the unit (n = n′K units), the rule needs (number of scenes above c + 1)/(n + 1) ≤ δ. The number of scenes above c is K times the number of logs above c, so ĉ is the (n′ − j)-th smallest log score, with j = ⌊(δ(n′K + 1) − 1)/K⌋.
- A new log's score exceeds ĉ with probability (j + 1)/(n′ + 1), because its rank among the n′ + 1 log scores is uniform.
- For n′ = 30 and K = 5, j = 1 and the risk is 2/31 = 0.0645 > δ.
- With the log as the unit, j = ⌊δ(n′ + 1) − 1⌋ = 0 and the risk is 1/31 = 0.032.

[C: P6e_scene_unit_counterexample; Monte Carlo 0.0641] The nuScenes evidence is therefore covered by Proposition 6 only to the extent that scenes are exchangeable. The Argoverse 2 fits, and the method stage's log-unit arm, use the log.

**Remark 5 (the sample floor).** With n calibration units:
- (i) a finite ĉ needs n ≥ 1/δ − 1: 19 at δ = 0.05, 99 at δ = 0.01;
- (ii) at n = 2/δ − 1 (39 at δ = 0.05, 199 at δ = 0.01) the allowance for the empirical term is δ/(2 − δ): 0.02564 and 0.005025;
- (iii) at the floor ĉ is the largest calibration score: valid and maximally conservative;
- (iv) levels below 1/(n + 1) cannot be certified by this construction. This is not an impossibility result for every method.

*Proof.*
- (i) R̂ ≥ 0, so the defining inequality needs 1/(n + 1) ≤ δ.
- (ii) The inequality is R̂(c) ≤ ((n + 1)δ − 1)/n =: a(n). With n + 1 = 2/δ, a(n) = (2 − 1)/(2/δ − 1) = δ/(2 − δ).
- (iii) At n + 1 = 1/δ, a(n) = 0, and ĉ = inf{c : R̂(c) = 0} is the largest calibration score (Lemma A.3).
- (iv) This is (i) read as a condition on δ. ∎ [C: R5_floor]

### S8.6 Fallback, deployable covariance and single multiplier

**The fallback rule.** For a stratum g, let C₀(g) = g ⊂ C₁(g) ⊂ C₂(g) ⊂ C₃(g) be its chain of level-1, level-2 and level-3 cells, within the same check time and in-path flag. For each cell C:
- N_C is the number of calibration logs with at least one item in C;
- ĉ_C is the CRC threshold fitted on **all** of C's items in those logs, defined when N_C ≥ n_min = 19;
- L_C(Z; c) is the share of all of log Z's C-items with U > c.

The level used is ℓ*(g) = min{ℓ : N_{C_ℓ(g)} ≥ 19}, and the deployed threshold is ĉ(g) = ĉ_{C_{ℓ*(g)}(g)}. This is `fit_hier` of m_lib_v04: a cell's count is its number of distinct units, and a coarser cell is fitted on all of its items, whether or not its sub-strata have their own thresholds. [C: P7_code_fit_hier, run through the imported library]

**Proposition 7 (count-based hierarchical fallback) [main text: Proposition 4; proof also in Appendix A].** Assume (L1)–(L3) for every cell on the chain.
- **(i) Own threshold.** O_g = {N_g ≥ 19} is a function of the calibration logs' membership vector for g. For every vector a ∈ O_g, E[L_g(Z_test; ĉ(g)) | A_g = a, A_g(Z_test) = 1] ≤ δ. Hence E[L_g(Z_test; ĉ(g)) | O_g, A_g(Z_test) = 1] ≤ δ: Proposition 6 holds conditionally on the stratum being assigned its own threshold.
- **(ii) A coarser cell.** For a cell C and every membership vector a_C of C with N_C ≥ 19, E[L_C(Z_test; ĉ_C) | A_C = a_C, A_C(Z_test) = 1] ≤ δ. The proposition asserts nothing beyond this:
  - **(a)** No bound conditional on g's fallback event F_g = {N_g < 19, …, N_{C_{ℓ*−1}(g)} < 19}. F_g depends on the membership vectors of g and of the intermediate cells, which are not functions of A_C. F_g restricts how many calibration logs of C contain g and places no restriction on the test log, so conditionally on F_g the calibration logs of C are no longer exchangeable with the test log; Lemma A.2 does not apply.
  - **(b)** No bound for g's own loss L_g at ĉ_C, even unconditionally.
  - **(c)** No bound for the deployed loss over C: sub-strata of C with their own thresholds use those, not ĉ_C.
  - **(d)** No bound conditional on the test log containing g.
- **(iii) A fixed map.** Given the calibration logs, the deployed map x ↦ ĉ(g(x)) is fixed: it depends on no test log. The level ℓ*(g) depends on the calibration logs only through the membership counts N_{C_ℓ(g)}, not on any score. At deployment the map needs only the stratum features: group, range from the ego's CTRV-predicted center, axis, course-change state, check time and in-path flag. All of these are computed from the tracker's estimates and the ego state.

*Proof.*
- (i) On O_g, ĉ(g) = ĉ_g. O_g is determined by the membership vector, so conditioning on A_g = a ∈ O_g fixes the assignment without disturbing Lemma A.2. Proposition 6 gives the bound for each such a; average over a ∈ O_g. An event that involved calibration scores or item counts, not only membership, would not have this property. `fit_hier` uses unit counts only.
- (ii) This is Proposition 6 with C in place of g; its loss is L_C, over all of C's items at the single threshold ĉ_C. The counterexample below shows that (a) and (b) can fail.
- (iii) By construction: own versus fallback is decided by counts of distinct calibration units per cell, and every threshold is computed from calibration items only. ∎

*Counterexample to conditioning on fallback* [C: P7_fallback_conditioning]. Let C = g ∪ h, with 300 calibration logs:
- every log has 1–3 items of h with U ~ N(0, 1);
- with probability 0.06 a log also has 5–10 items of g with U ~ N(3, 1).

The conditional risk given ĉ_C is computed exactly, over 20 000 calibration draws. Then:
- unconditionally, E[L_C(ĉ_C)] = 0.0481 (SE 0.0001) ≤ δ, as (ii) states;
- given the fallback event N_g < 19 (probability 0.57), E[L_C(ĉ_C)] = 0.0536 (SE 0.0001) > δ, and 0.0595 given N_g ≤ 14;
- in the fallback case, a test log's g-loss at ĉ_C averages 0.80;
- when N_g ≥ 19, g's own threshold gives a g-loss of 0.0099 ≤ δ.

Fallback strata are therefore reported separately and carry no certificate.

**Proposition 8 (deployable covariance) [main text: Proposition 5].** For estimated yaw ψ let a_l = (cos ψ, sin ψ) and a_t = (−sin ψ, cos ψ), α_l, α_t > 0, A = α_la_la_lᵀ + α_ta_ta_tᵀ, M = Σ̂ + σ_a²I with Σ̂ ⪰ 0 and σ_a > 0 (or Σ̂ ≻ 0), and Σ̃ = AMA.
- Σ̃ is symmetric positive definite.
- aᵀΣ̃a = α²(aᵀΣ̂a + σ_a²) for (a, α) ∈ {(±a_l, α_l), (±a_t, α_t)}.
- With α = max(ĉ, ε)/z_{1−δ} and ε = 10⁻³, a planner applying z_{1−δ}√(aᵀΣ̃a) applies exactly max(ĉ, ε)·sd on each object axis, in either orientation.

*Proof.*
- a_l and a_t are orthonormal (a_lᵀa_t = −cos ψ sin ψ + sin ψ cos ψ = 0). So A is symmetric with eigenpairs (α_l, a_l) and (α_t, a_t), and it is positive definite, hence invertible.
- Σ̃ᵀ = AᵀMᵀAᵀ = AMA. For x ≠ 0, xᵀΣ̃x = (Ax)ᵀM(Ax) > 0, since Ax ≠ 0 and M ≻ 0.
- Aa_l = α_la_l, so a_lᵀΣ̃a_l = α_l²a_lᵀMa_l = α_l²(a_lᵀΣ̂a_l + σ_a²), using a_lᵀa_l = 1; the same holds for a_t. The sign of a cancels in a quadratic form, so the toward-ego normal a* = ±a receives the same value.
- Then z_{1−δ}√(aᵀΣ̃a) = z_{1−δ}·α·sd = max(ĉ, ε)·sd. ∎

[C: P8_congruence: exact in rational arithmetic on 2000 random cases; m_lib_v04.deploy_covariance agrees to floating-point accuracy on 20 000]

*The floor and other normals.*
- If a fitted ĉ ≤ 0, the deployed margin ε·sd exceeds the fitted ĉ·sd. Since L is non-increasing, validity is kept. The registered fit asserts that every M\* threshold is positive, so the floor was never active there.
- A planner normal that is not an object axis, a = cos φ·a_l + sin φ·a_t, receives aᵀΣ̃a = α_l²cos²φ·M_ll + α_t²sin²φ·M_tt + 2α_lα_t sin φ cos φ·M_lt, with M_ll = a_lᵀMa_l and so on. This mixes the two corrected axes and their cross term, and no certificate covers it.

**Proposition 9 (certified single multiplier).** Let c̄ ≥ ĉ(g′) for every stratum g′ of the fit. In the registered test, B3 is the largest of the 192 thresholds of a check time, fallbacks included.
- For every stratum g with its own threshold, E[L_g(Z_test; c̄) | O_g, A_g(Z_test) = 1] ≤ δ.
- The extra margin over the stratified rule is Σ_items(c̄ − ĉ(g(item)))·sd_item ≥ 0, and it is zero iff ĉ(g(item)) = c̄ for every item.
- The same holds for B6c, the maximum over the course-change strata within a level-1 cell. Nothing is asserted for fallback strata.

*Proof.* c̄ ≥ ĉ_g and (F1) give L_g(Z; c̄) ≤ L_g(Z; ĉ_g) for every log Z, whatever the dependence of c̄ on the other strata's data. Take conditional expectations and apply Proposition 7(i). Every term of the margin sum is non-negative because c̄ is at least every deployed threshold and sd_item > 0, so the sum vanishes iff every term does. ∎ [C: P9_domination] B3 and B6c are pricing references, dominated by M\* by construction.

### S8.7 What the propositions do not cover

Propositions 6–9 bound one quantity: the expected share of a test log's calibration items in an own-threshold stratum whose score exceeds that stratum's threshold. The share is marginal over i.i.d. logs and conditional only on membership. The evaluation and the claims of the paper reach beyond it in five places, which the propositions do not cover.

- **(1) The relied-axis selection by gap.** The propositions bound the share over all of a log's calibration items: every separating axis of every enforced pair. The scored populations keep one item per pair, the separating axis with the largest gap. This subset is selected by the gap, which is tied to the score through the geometry, so its exceedance share is a different loss from the calibrated one. When the gap is taken under each arm's own chosen plan (decision mode, Section IV-A), the subset also depends on that arm's fitted thresholds, and hence on the calibration logs, so it is neither the calibration rule nor a fixed function of the test log. A subset of a log's items can have any exceedance share while the full share is at most δ. Items chosen after seeing the data need selection-aware methods [JinCandes2023; Bao2024]. Validity on the relied records is measured (Section V), not proved.
- **(2) The logged-pose reference.** The item rule uses the logged ego pose at t_k + h, which the driver chose knowing where the objects were. It is not I_k-measurable, so condition (M) fails. Propositions 1 and 3 do not apply to the calibration items: these are not constraints a planner forms at decision time, and no per-constraint premise follows for any planner. Exchangeability is unaffected, because the logged pose is part of the log and the same rule is applied in calibration and test. Proposition 6 therefore holds for this proxy population, and only for it.
- **(3) The scored decision-mode population.** In decision mode each arm's planner chooses its own plan from the logged state, and its relied constraints follow from that plan. The population an arm is scored on thus depends on the arm and on its calibration logs. None of the propositions bounds exceedance on it, nor infeasibility, nor any per-decision quantity. With several relied constraints per decision, the share of decisions with some exceeded constraint can far exceed δ; it was about one in two on Argoverse 2.
- **(4) Cross-fitting averages five fold rules.** The registered estimate averages test-log losses under five different fold rules, each fitted on 300 logs. Corollary A.4 bounds its expectation for strata that have their own threshold in all five folds. It is not a statement about a single deployed rule:
  - not about one fold rule given its calibration logs, whose conditional risk exceeds δ with substantial probability (about one draw in four in [C: P6b]);
  - not about the rule a deployment would fit on all 375 logs. That rule's marginal bound is Proposition 6 with its own calibration count, and it was not what was evaluated.

  A training-conditional guarantee would need risk-controlling prediction sets or Learn-then-Test [Bates2021; Angelopoulos2025LTT].
- **(5) The log-weighted estimand against the premise.** Proposition 6 bounds a log-weighted rate: each test log counts once, and its stratum items share its weight. The weights 1/n_g(Z) are not measurable at an item's information, so Proposition 1(ii) does not apply, and the log-weighted rate neither implies nor is implied by the per-instance premise.
  - One direction: with both instances exactly calibrated, the rate is 1.25δ = 0.0625 (S8.2).
  - The other: the fair-label example has a rate exactly at δ with a premise failure at 2δ.

  The registered screen's cells pool level-0 strata over range. Pooled cells weight strata by their item counts within each log, so no proposition bounds them and their null value is only approximately δ. Fallback strata are covered only as in Proposition 7(ii), and nuScenes scene-unit fits only as in Remark A.5.

The population is also limited: items exist only for tracked real objects annotated at k + h, under an assumed annotation noise σ_a. False-positive tracks and objects that become occluded are outside it.

---

## S9. The planner and the perception stack in full

Appendix B of the main text summarizes the planner (Table X and Algorithm 2). This section specifies it in full, from the code of record: the path, the longitudinal model, the candidate set, the cost and choice rule, and how the λ back-off relates to "infeasible" (S9.1–S9.14). It then records the detectors, trackers and learned predictor (S9.15). Every planner statement ends with a code reference in brackets, `[file:line]`, to the files as hashed below; a bare line number means `k8_sim_v04.py`. Only code and records were read to write it.

**Code of record.** One file holds the planner for both data sets. The nuScenes study K8 ran `k8_sim_v02`, and the Argoverse 2 runs ran `k8_sim_v04`, which adds two joint arms and changes no decision of any other arm [k8_sim_v04.py:2–8; c1_run_v02.py:56].

| File | SHA-256 | Bound in the frozen C1 plan (v07m line) | Role |
|---|---|---|---|
| `50_CODE/k8/k8_sim_v04.py` | 03881acdbf28e53afbe6c5f4de8aeb352e14ddd43ad9f2feff6c67217a528e01 | 1587 | planner; decision mode; loop mode; scored records |
| `50_CODE/k6/k6_sim_v02.py` | 257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4 | 1583 | the functions the calibration items import; same constants and geometry [k6_sim_v02.py:54–96, 304–305] |
| `50_CODE/k8/k8_items_v08.py` | dfc7b8cface55b2234e6173a96eb68ecf2b906b6cba808d74c482faa551a65e3 | 1540 | calibration items at the reference pose |
| `50_CODE/k8/k8_analyse_v04.py` | edd721dac4612b023e3e77b102bd1844cd74a700be6056de68072c0ea86fad94 | 1585 | populations, V2, infeasible rate |
| `50_CODE/k6/k6_analyse_v02.py` | 9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61 | 1581 | population masks, cells, rates |

**Lineage** (each step states that it changes no decision): `k6_sim_v02` (the K6 harness after review R09: exemptions at margin 0, strata from the sensor, constraints enforced to 2 s, decision mode, back-off ladder) → `k7_sim_v01` (in-path-split thresholds) → `k8_sim_v01` (records and fit-free arms) → `k8_sim_v02` (more records) → `k8_sim_v04` (joint arms) [k8_sim_v04.py:2–74; D09_K6_HARNESS_DESIGN_v04.md §0].

---

### S9.1 What the planner receives at a decision

- The tracker does not run in the loop. The recorded tracker output, produced at the logged ego, is replayed [27].
- Each track carries its current center, yaw, length and width, class, speed, course-change rate and the method's in-path flag, plus the tracker's own propagated mean and 2-D position covariance at 0.5, 1, …, 4 s [318–335, 618–622, 628].
- Only tracks with a tracking score ≥ 0.4 are in the cache. The filter is applied when the cache is built, not in the planner [116; k6_cache_v02.py:84; av2_cache_stageA_v02.py:159].
- The in-path flag is read from the cache, never defaulted [618–619].

### S9.2 The path and the leash

- **The path is the logged ego path.** The ego moves along the logged rear-axle poses, at a speed the planner chooses; the planner controls speed only [80–81, 383–399]. The poses are 20 Hz on nuScenes [80] and 10 Hz on Argoverse 2 (median 10.06 Hz; `60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v03.md` §1).
- **Decimation.** A logged pose is kept only if it lies at least 5 cm from the last kept pose [119, 233–237]. Arc length s is the cumulative chord length of the kept poses [239]; yaw is unwrapped [240].
- **Pose at arc length s.** x, y and yaw are interpolated linearly in s, with s clipped to [0, s_end] [258–261]. The ego center is the rear-axle point moved R2C = 1.39 m forward along the heading [103, 410].
- **Logged progress and speed.** s_log(t) interpolates arc length in time, clipped at both ends [252–253]. The logged speed is the arc length covered over a 0.5 s window on a 0.1 s grid, assigned to the window's midpoint, so v_log(t) uses logged positions from t − 0.25 s to t + 0.25 s [244–250, 255–256].
- **Speed cap.** v_max is the log's largest logged speed plus 2 m/s [249, 674, 708].
- **The leash.** At each check time, a candidate's planned arc length is capped at the leash [601–602]:
  - in decision mode the leash is the logged arc length at the same time, s_log(t_k + t) [680];
  - in loop mode it is s_log(t − d) for a delay d of 0, 1 or 2 s, and the executed position and speed are capped the same way [706–707, 758–762].

  In decision mode no candidate's planned position is ever ahead of the logged ego's.

### S9.3 The longitudinal model and the candidates

- **Model.** A point mass on the path, with piecewise-constant acceleration, speed clipped to [0, v_max] [391–394].
- **Integration.** 80 steps of DT_FINE = 0.05 s over 4 s. The acceleration of step i is read at the step's midpoint τ_i = (i + ½)·0.05 s. Then v_{i+1} = clip(v_i + a·0.05, 0, v_max) and s_{i+1} = s_i + ½(v_i + v_{i+1})·0.05 [108, 182–183, 391–394].
- **Candidates.** A candidate (a₁, T₁) holds a₁ while τ < T₁ and then brakes at A_BRAKE = −4 m/s² [111, 183].
  - a₁ ∈ {−4, −2, −1, 0, 0.5, 1, 1.5, 2} m/s² and T₁ ∈ {0.5, 1, 2, 4} s: 32 candidates [109–110, 176].
  - **The emergency stop** is a 33rd candidate: −6 m/s² for the full 4 s, so the speed falls to 0 and stays there [111, 177, 183, 392].
  - With T₁ = 4 s, a₁ is held for the whole scoring horizon (a₁ = 0 is constant speed) [110, 182–183].
  - The four candidates with a₁ = −4 m/s² are identical, because −4 m/s² is also the braking value. There are therefore 29 distinct non-emergency profiles, and 30 with the emergency stop [109, 111, 183].
- **Candidate order** (used for ties): smaller |a₁| first, then positive before negative, then longer T₁; the emergency stop last [174–177]. The order is a₁ = 0, 0.5, 1, −1, 1.5, 2, −2, −4, each with T₁ = 4, 2, 1, 0.5 s.
- **Start state.** In decision mode s = s_log(t_k) and v = max(v_log(t_k), 0) [680]; in loop mode, the simulated ego's s and v [731].
- **SUB.** In loop mode only, the chosen candidate is executed until the next keyframe in SUB = 5 equal substeps, with the acceleration read from the candidate's table at the substep's midpoint [107, 749–755]. Decision mode executes nothing [666–693].

### S9.4 Check times and horizons

- **Check times.** 16, every 0.25 s from 0.25 s to 4 s [184–186].
- **Enforced constraint horizon: 2 s.** Constraints are enforced at the first 8 check times only [188, 630, 635, 637].
- **Scoring horizon: 4 s.** The choice objective uses all 16 check times [603].
- **Track means.** At the 0.5 s steps, the tracker's propagated mean. At the midpoints (0.25, 0.75, … s), the average of the two neighbouring means; at 0.25 s, of the current center and the 0.5 s mean [621–626].
- **Margins at midpoints.** A midpoint uses the margin of the next 0.5 s step [187, 627].
- **Calibrated steps.** Records and items are taken at 0.5, 1, 1.5 and 2 s [189, 658–659; k8_items_v08.py:128–132].
- Check times after 2 s enter only the safety proxies [449–477].

### S9.5 Footprints, gap and margin per axis

- **Object axes.** a_long = (cos ψ, sin ψ) and a_lat = (−sin ψ, cos ψ), from the track's yaw ψ at the decision time. The same axes are used at every check time; no predicted yaw is used [333–334, 621].
- **Object footprint.** Half extents l/2 along a_long and w/2 along a_lat. The object's footprint is **not** buffered [628].
- **Ego footprint.** A 4.1 m × 1.8 m rectangle inflated by BUFFER = 0.5 m on every side, centered 1.39 m ahead of the rear axle at the planned arc length, with the path's yaw there [103, 409–410, 415]. These are the nuScenes constants. They are also used on Argoverse 2, whose ego (a Ford Fusion, about 4.9 m × 1.9 m) is larger (`50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md` §5; the Ford Fusion footprint sensitivity is "not run", plan v07m §2; a sensitivity added after review is in S6.19).
- **Gap along axis a.** With sep_a = aᵀ(c_ego − m̂):
  gap_a = |sep_a| − [h_obj,a + (L/2 + 0.5)|u_eᵀa| + (W/2 + 0.5)|v_eᵀa|],
  where u_e and v_e are the ego's axes [414–416]. Only the object's two axes are tested, not the ego's [407–416].
- **Margin along axis a.** It comes from the arm and depends on the track, step and axis [343–378]:
  - Z0: 0 [349–350];
  - B0: z₀.₉₅·sd, with sd = √(aᵀS_h a + σ_a²) and σ_a = 0.10 m [104–105, 335–338, 351–352];
  - M\*: c[L0 + 96·in-path]·sd, the threshold of the track's L0 stratum and in-path flag at that step [370–371].
- **A pair constraint at one check time** is satisfied when max over the two axes of (gap_a − margin_a) is ≥ 0, a disjunction over the object's axes [630].
- **The buffer's contribution.** The buffer inflates the ego rectangle and is projected with it, so it adds 0.5(|u_eᵀa| + |v_eᵀa|), between 0.5 m and 0.71 m, to the ego's projected half extent along a; the object is not buffered [415].

### S9.6 The tracks considered

- The tracks of the current keyframe [599], within 60 m of the ego center [113, 613], and whose center lies no more than L/2 = 2.05 m behind the ego center along the ego heading, that is, not behind the rear bumper [613].
- Distances use the tracks' current centers and the ego's position at the decision [610–613].
- If no track is considered, every candidate is feasible [608–615].

### S9.7 The enforced-pair rule (reference margin 0)

A (track j, check time t) pair with t ≤ 2 s is **enforced** when both conditions hold [638]:
1. **Controllable:** at margin 0, some candidate of the 33, the emergency stop included, has max_a gap_a ≥ 0 at t on its leashed plan [602, 629, 635];
2. **Not brought to the ego:** an ego held at its current arc length s for all 16 check times also has max_a gap_a ≥ 0 at t [636–637].

- The rule uses no margin, so the enforced set is the same for every arm [631–638].
- It is decided per (track, check time). A track can be enforced at some check times and exempt at others [638].
- Pairs that fail condition 1 are counted as "uncontrollable", and pairs that pass 1 and fail 2 as "brought to the ego" [639–640].
- The rule replaced an earlier one that tested exemption at each arm's own margin. Under that rule a larger margin exempted more pairs (D09 v04 §0, C8).

### S9.8 The cost and the choice rule

- **Objective.** Each candidate is scored by prog_c, the mean over the 16 check times of its **leashed** planned arc length [602–603]. There is no other cost term: no comfort, jerk or risk term.
- **Feasibility.** A candidate is feasible at the arm's margin when it violates no enforced pair: the sum over enforced pairs within 2 s of max(0, −slack)² is zero [641–643]. W_PEN (1000) scales that sum for the record only [112, 642, 655].
- **Choice.** If some candidate is feasible, the planner chooses the feasible candidate with the largest prog_c, the emergency stop included [644–645].
- **Ties** go to the earliest candidate in the order of S9.3, because `argmax` returns the first maximum [174–177, 645]. Ties are common in decision mode: every candidate that reaches the leash at all 16 check times has the same prog_c. The tie then goes to the smallest |a₁|, positive before negative, then the longest hold [176, 602–603].
- **No track considered:** the candidate with the largest prog_c over all 33 [604, 608–615].

### S9.9 "Infeasible", the λ back-off and the emergency stop

1. **Infeasible.** A decision is *infeasible* when no candidate, the emergency stop included, satisfies every enforced constraint at the arm's full margin [643, 646–647].
2. **Back-off.** The margin is then scaled by λ ∈ (0.75, 0.5, 0.25, 0), in that order, on the **same** enforced set. At the first λ at which some candidate satisfies max_a(gap_a − λ·margin_a) ≥ 0 for every enforced pair, the planner chooses the candidate with the largest prog_c among those, and records λ [190, 649–654].
3. **Emergency stop.** If even λ = 0 (the buffered mean footprints) fails, the emergency stop is taken and λ is recorded as −1 [648, 153, 551].
   - λ = 0 can fail even though every enforced pair passed condition 1 of S9.7. Condition 1 asks for some candidate per pair; the back-off needs one candidate for all pairs at once [635, 651].
4. **Feasible decisions** record λ = 1 [604].
5. **Choosing the emergency stop at full margin.** If the emergency stop is the only candidate feasible at the full margin, it is chosen as an ordinary candidate. That decision is neither infeasible nor counted as an emergency stop [645, 684].

**What the infeasible rate counts.**
- **Per decision:** the indicator of point 1 [647, 683]. It includes decisions resolved by any back-off level and decisions that end in the emergency stop. It excludes decisions in which some candidate, the emergency stop included, met the full margin.
- **The rate.** For each log, the share of its decisions that are infeasible; then the unweighted mean over logs [k8_analyse_v04.py:1376–1377]. Paired contrasts use the same per-log shares [k8_analyse_v04.py:734].
- **The emergency-stop share** is reported separately [684; k8_analyse_v04.py:739].

### S9.10 Decision mode and loop mode

**Decision mode** [666–693] carries every comparison of the paper.
- Decisions are made at every keyframe k = 1, …, K − 2 of a log [678]. On Argoverse 2 this gives 11,288 decisions on 375 logs (plan v07m §1.6).
- Each decision starts from the logged state, (s_log(t_k), max(v_log(t_k), 0)), with the leash set to the log and sensor-offset bin 0 [680].
- Each decision is made once and not executed. Every arm faces identical states [678–687].
- **What it uses after t_k.** The logged ego's arc length up to t_k + 4 s, through the leash, and its positions up to t_k + 0.25 s, through the centered speed window [244–250, 601–602, 680]. These are logged ego poses, not annotations.

**Loop mode** [696–807] is descriptive on nuScenes and was not run on Argoverse 2 in the registered test; a descriptive replay added after review is in S6.18.
- **Entry.** The ego enters at keyframe d ∈ {0, 2, 4}, a delay of 0, 1 or 2 s, at s = 0 with the logged initial speed. An episode is not entered if the ego overlaps an annotated agent at entry [697–715].
- **Each keyframe.** The planner decides from the simulated s and v, with the leash s_log(t − delay) [727–731]. The choice is executed for one interval in 5 substeps, with the leash cap applied [749–767].
- **Agents** are the annotated boxes, interpolated linearly between keyframes, bridging gaps of up to 3 keyframes. They do not react [118, 263–292, 771].
- **Perception** is still the recorded tracker output produced at the logged ego [27–28].
- **Collisions** are exact rectangle overlaps at every substep, at fault when the ego moves and the agent overlaps the ego's front half [771–792].

### S9.11 The relied axis and the relied populations, as coded

The code builds two different sets from the same enforced pairs.

**(a) Calibration items: the M\* fit** [k8_items_v08.py:99–169].
- **Where.** The same decision states, considered tracks and enforced rule as decision mode [k8_items_v08.py:99–128].
- **Which pairs.** Every enforced (track, step) at the steps 0.5, 1, 1.5 and 2 s whose paired object is annotated at that step's keyframe (k + 1 to k + 4), with ≥ 1 lidar point and not in a bicycle rack [k8_items_v08.py:132–145].
- **The reference pose.** Gap and separation are evaluated at the **logged ego pose at t_k + h**, the leash [k8_items_v08.py:129–130].
- **Items.** Every axis with gap > 0 gives one item U = D/sd, with D = sign(sep_a)·aᵀ(g − m̂) [k8_items_v08.py:162–169].
- **ref_relied** marks the axis with the **largest gap** at the reference pose [k8_items_v08.py:161, 168].
- **Use.** M\* is fitted on all items, both axes [k7_fit_v01.py:88–93; c1_fit_v02.py:84–87, 185]. The items also give the outcome-free counts of plan v07m §1.6 and the A6 calibration diagnostics.

**(b) Scored records: the validity screen V1, and V2** [810–938].
- **Where.** Records are taken at **each arm's chosen candidate**, at its leashed planned pose: G is the gap and S the separation along the chosen plan [660, 827–828].
- **The relied axis** is the axis with the **largest slack**, the gap minus the arm's own margin [829–830]. "Satisfied" means that slack is ≥ 0 [831].
- **Which records.** Paired tracks annotated at the step's keyframe (k + 1 to k + 4), with ≥ 1 point and not in a rack [834–846]. One record per axis with G_a > 0 [854–856].
- **Exceedance.** D = sign(S_a)·aᵀ(g − m̂), and an exceedance is D > margin_a [860–861].
- **Keys.** Each record is keyed by sensor-offset bin, in-path flag, enforced, satisfied, pair-gap bin (max_a G_a: ≤ 2, (2, 5] or > 5 m), relied, step and L0 stratum [120, 832, 852–853, 862, 941–950].

**The populations of the screen** are masks over (b) [k8_analyse_v04.py:137–143; k6_analyse_v02.py:84–89]. Each is a decision-mode record (offset bin 0) on the relied axis, enforced, satisfied at the arm's full margin, at steps 0.5–2 s:
- **P_rel** (code PD7): every in-path flag and every gap bin;
- **P_near** (SD1_7): pair gap at the chosen plan ≤ 5 m;
- **P_ip** (PD): in-path tracks only;
- **P_nip** (NIP): not-in-path tracks only.

How they are scored:
- **Backed-off decisions** are scored at the full margin, so their unsatisfied pairs drop out of the populations [k8_analyse_v04.py:196].
- **Cells** are group × axis × motion state pooled over range, 32 in all [k6_analyse_v02.py:75–81]. The group comes from the class [122, 318], and the motion state is static below 1 m/s, otherwise new, turning (|ω̂| ≥ 0.10 rad/s) or straight [114, 319–320].
- A cell's rate is the mean over logs of each log's exceeded share [k6_analyse_v02.py:122–126].

**Evidence that the screen's population is (b), not (a).**

| Development or test set | Arm-independent relied items | Records the screen used, per arm |
|---|---|---|
| nuScenes K8, T1 | 919,396 [`70_TESTS/k8_expl_v02_analysis_v03/csv/k8_t1_decide_a6_items.csv`] | M\* 914,867; B0 889,061; B3 686,705; Z0 920,802 [`…/csv/k8_t1_decide_counts.csv`] |
| Argoverse 2, T1 | 537,924 (plan v07m §1.6) | M\* 534,846; B0 527,372; B3 356,260; Z0 538,329 [`60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_t1_decide_counts.csv`] |

- **Evaluable cells on Argoverse 2.** On the items, 27, 18 and 9 for P_rel, P_near and P_ip (plan v07m §1.6). On the scored records, M\*'s registered screen has 27, 16 and 8 (main-text Table 3).
- **The reported rates come from (b).** M\*'s pooled P_rel 0.044 and B0's 0.034 on T1 are the record-based values of the counts file above (0.04397 and 0.03371).
- **Fit and scoring use different selections:** a different pose (the reference pose for the items, the chosen, leashed plan for the records), a different relied-axis rule (largest gap for the items, largest slack for the records) and the satisfied filter. Item counts, such as the 919,396 (T1) and 920,618 (T3) arm-independent relied items of nuScenes K8 and the 537,924 of Argoverse 2 T1, are therefore not the sizes of the scored sets.
- **The scored pose is not a decision-time pose either.** The chosen plan is capped by the logged future progress (S9.2), so scoring at it is not I_k-measurable.

### S9.12 V2 and V2_viol

- **Per decision** [k8_analyse_v04.py:446–466]:
  - the decisions counted are those with at least one scored record of (b) in the population, in decision mode;
  - V2's indicator is at least one exceedance (D > margin) among them, over the four calibrated steps and all tracks.
- **The estimate.** For each log, the share of its counted decisions with an exceedance; then the mean over logs [k8_analyse_v04.py:468–477; k6_analyse_v02.py:122–126].
- **The reference.** Per decision, 1 − (1 − δ)^{n_tracks}, where n_tracks counts the tracks with a scored record in the population; it is averaged the same way [869–903; k8_analyse_v04.py:428–443, 461–464, 481–492].
- **V2_viol.** The same, with the indicator "the projected error along the relied axis exceeds the planned gap", D > G_rel [883–885; k8_analyse_v04.py:160].
- **Margins.** V2 and V2_viol use the arm's full margin at the chosen plan. **V2_exec** instead re-selects the relied axis and scores at the executed margin λ·margin, with the emergency stop at λ = 0 [926–937; k8_analyse_v04.py:160–164].

### S9.13 Algorithm 2 (main-text Appendix B; one decision; every line checked against `k8_sim_v04.py`)

```
Algorithm 2  plan_step(arm, k, s, v): one decision                               [590–663]
input : keyframe k at time t_k; arc length s and speed v (decision mode: s_log(t_k),
        max(v_log(t_k), 0)); leash lead(t); v_max = max logged speed + 2 m/s     [597, 680, 674]
 1  S_plan[c, i] <- integrate candidate c over 80 steps of 0.05 s from (s, v),
                   clip v to [0, v_max]; keep s at check times t_i = 0.25 i      [600, 383-399]
 2  S_plan[c, i] <- min(S_plan[c, i], lead(t_k + t_i))           # the leash     [601-602]
 3  prog[c] <- mean_i S_plan[c, i]           # 16 check times, scoring to 4 s     [603]
 4  J <- tracks at k with |c_track - c_ego| < 60 m and
        (c_track - c_ego) . u_ego >= -2.05 m                                      [610-613]
 5  if J is empty: return argmax_c prog[c], feasible, lambda = 1                  [604, 614-615]
 6  for j in J, step h = 1..8 (0.5 s): sd, L0 stratum, margin m[j, h, a]         [616-620, 314-378]
 7  mean at check time i: tracker mean at the 0.5 s steps, average of the two
    neighbours at midpoints; margin at i = margin of the next 0.5 s step          [621-627, 187]
 8  gap[c, i, j, a] <- |a.(c_ego(c, i) - mu[j, i])| - (h_obj[j, a] + h_ego(c, i, a))
                   (ego 4.1 x 1.8 m + 0.5 m per side; object not buffered)        [629, 407-416]
 9  for check times i = 1..8 (to 2 s):
10     ctrl[i, j] <- exists c in all 33 candidates: max_a gap[c, i, j, a] >= 0   [635]
11     hold[i, j] <- max_a gap_held(s)[i, j, a] >= 0     # ego held at s          [636-637]
12     enf[i, j]  <- ctrl[i, j] and hold[i, j]     # arm-independent (margin 0)    [638]
13  slack[c, i, j] <- max_a (gap[c, i, j, a] - m[j, i, a])                        [630]
14  F <- {c : slack[c, i, j] >= 0 for every enforced (i, j)}                      [641-643]
15  if F is not empty: return argmax_{c in F} prog[c] (first in candidate order),
                      infeasible = false, lambda = 1                              [644-645, 176]
16  infeasible <- true                                                            [646-647]
17  for lambda in (0.75, 0.5, 0.25, 0):                                           [649]
18     F_l <- {c : max_a (gap[c, i, j, a] - lambda m[j, i, a]) >= 0 for every
              enforced (i, j)}                    # the same enforced set         [650-651]
19     if F_l is not empty: return argmax_{c in F_l} prog[c], infeasible, lambda [652-654]
20  return the emergency stop (-6 m/s^2), infeasible, lambda = -1 (recorded)     [648, 551]
21  records (decision mode): at the chosen c, steps 0.5-2 s, relied axis
    a* = argmax_a (G_a - m_a), satisfied = G_a* - m_a* >= 0; one record per axis
    with G_a > 0; exceedance D > m                                                [657-662, 826-862]
```

### S9.14 Parameter table

| Quantity | Value | Code | Basis of the value (`90_DECISIONS/C1_CRITERIA_REGISTER_v05.md`) |
|---|---|---|---|
| Path | logged rear-axle path, decimated to poses ≥ 0.05 m apart | 119, 233–240 | — |
| Ego footprint | 4.1 × 1.8 m, center 1.39 m ahead of the rear axle (nuScenes constants, also on Argoverse 2) | 103 | port design v01 §5 |
| Buffer | 0.5 m on every side of the ego only | 103, 415 | C15c (own value) |
| Consideration range | 60 m from the ego center; center not more than 2.05 m behind it | 113, 613 | C15d |
| Score threshold | 0.4 (applied in the cache) | 116; k6_cache_v02.py:84 | C15h |
| First-phase accelerations a₁ | −4, −2, −1, 0, 0.5, 1, 1.5, 2 m/s² | 109 | C15e |
| Hold times T₁ | 0.5, 1, 2, 4 s | 110 | C15e |
| Braking after the hold | −4 m/s² to standstill | 111, 183 | — |
| Emergency stop | −6 m/s² throughout | 111, 177, 183 | — |
| Candidates | 33 listed (32 + emergency stop); 30 distinct profiles | 173–181 | C15e |
| Integration | DT_FINE = 0.05 s, 80 steps, midpoint acceleration, trapezoidal position | 108, 182–183, 391–394 | — |
| Speed bounds | [0, v_max], v_max = log maximum + 2 m/s | 249, 392, 674 | C15f |
| Logged speed | 0.5 s centered window on a 0.1 s grid | 244–250 | — |
| Check times | every 0.25 s, 16 in all (0.25–4 s) | 184–186 | C15b |
| Enforced horizon | 2 s (8 check times) | 188 | C15a |
| Scoring horizon | 4 s (16 check times) | 603 | — |
| Calibrated steps | 0.5, 1, 1.5, 2 s | 189 | — |
| Track motion | tracker's propagated mean; object yaw fixed at its current value | 333–334, 621–626 | — |
| Margin per axis | arm's margin; B0 z₀.₉₅·sd with σ_a = 0.10 m | 104–105, 338, 343–378 | C12c (σ_a) |
| Enforced-pair rule | margin 0: some candidate clear and held ego clear | 635–638 | (D09 v04 C8) |
| Choice | max mean leashed planned arc length over 16 check times; ties by candidate order | 603, 645, 174–177 | — |
| Back-off ladder | λ = 0.75, 0.5, 0.25, 0, then emergency stop | 190, 646–654 | C15g |
| Decision states | keyframes 1 … K − 2 | 678 | — |
| Loop-mode delays and substeps | 0, 2, 4 keyframes; SUB = 5 | 107, 697, 750 | — |
| Near / far split | pair gap ≤ 5 m at the chosen plan (bins ≤ 2, (2, 5], > 5 m) | 120, 832, 852 | — |
| Motion strata | static < 1.0 m/s; turning \|ω̂\| ≥ 0.10 rad/s; "new" without ω̂ | 114, 319–320 | — |
| Range strata | < 20, 20–40, ≥ 40 m from the sensor's CTRV-predicted center | 321–332 | — |

**Between nuScenes and Argoverse 2**, the planner differs only in its inputs:
- the ego path (20 Hz against 10 Hz) [80; AV2_TRACKER_NOTE_v03.md §1];
- the keyframe spacing, nominally 0.5 s; on Argoverse 2 it ranges from 0.4958 to 0.5999 s, and t_k is the actual time stamp [597; AV2_TRACKER_PORT_DESIGN_v01.md §2].

Every constant above is the same.

---

### S9.15 Detectors, trackers and the learned predictor, as recorded

This part states only what the records state. Each statement carries its source in brackets; paths are relative to the project root. Where a record gives only a hash prefix, the prefix is quoted. A value read from third-party source code rather than from a project record is marked **(source code)**. "Not recorded" means that none of the records read states it.

#### S9.15.1 Detectors

##### S9.15.1.1 nuScenes (development studies X1, X2, the method stage, K6, K8, D17)

- **Model.** CenterPoint [Yin2021], the "flip" test-time-augmentation variant, 10 lidar sweeps, with velocity, from the author's archive [`20_DESIGN/E01_EVIDENCE_DOSSIER_v02.md` §2.2].
- **Training data.** The nuScenes train split, so train detections are in-sample for the detector and val detections are out-of-sample [E01 §2.2].
- **The inputs consumed, as hashed** (receipt `30_DATA/detectors/RECEIPT_val_copy.sha256`, 7602f93c…) [E01 §2.2, §8 source table]:
  - `30_DATA/detectors/centerpoint_flip/infos_val_10sweeps_withvelo_filter_True.json`: 4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e (312 MB);
  - `…/infos_train_10sweeps_withvelo_filter_True.json`: 547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145 (1.48 GB), equal to CANMOT's own `PAPER_INPUT_HASHES['train']`.
- **Not recorded:** the checkpoint file, its hash, the training configuration and the epoch count of these detections.
- **Score floor.** The smallest score over all 701,327 val boxes is 0.1000001, so CenterPoint's test-time score threshold of 0.1 acted on the nuScenes input [`50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md` §4.4].

##### S9.15.1.2 Argoverse 2, the detector of the registered test (own CenterPoint)

**Code and architecture.**
- LT3D [Peri2022] at commit e33189aa09f282cf555b64dba1654eb0c14464a6. The configuration is the public checkpoint's own, `centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py`, from LT3D's `av2_detectors.tar.gz` (607534ae…) [`50_CODE/owndet/OWN_DETECTOR_DESIGN_v01.md` §2].
- **Kept unchanged** [OWN_DETECTOR_DESIGN_v01 §2]: the model; voxel size 0.075 m; range ±54 m; 5 sweeps; the class hierarchy and "wide" head; CBGS resampling; ground-truth-database object sampling; the augmentations; AdamW (weight decay 0.01, gradient clip 35); the cyclic learning-rate and momentum schedules; and flip test-time augmentation at inference.
- **The architecture in the name** (SECOND backbone, SECFPN neck, deformable-convolution head) is read from the configuration's name. The records do not describe the layers further.

**Training data** [`60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md`; `50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json`, 3771664f8aca73d4829e9867147af2c84e8d87fd95d5472e3b1c1bc443700f72; C1 plan v07m §1.1]:
- the 700 Argoverse 2 Sensor train log ids, sorted and permuted with `numpy.random.default_rng(20261102)`; the first 225 are held out for the confirmation, and the other **475 train** the detector;
- 15,245 frames at every 5th sweep;
- a ground-truth database of 971,237 objects, built from the 475 logs only.

**Overrides and schedule** [OWN_DETECTOR_NOTE_v01, "Training as run"; OWN_DETECTOR_DESIGN_ADDENDUM_A_v01.md, 41ba8fe3…; ADDENDUM_B_v01.md, b824f3ea…]:
- data paths and info files;
- batch 4 on one GPU, with the learning rate scaled linearly to 5e-5 (1e-4 × 4/8);
- an iteration-based runner, `max_iters` 57,838, with a checkpoint every 1,000 and no evaluation during training;
- from scratch, seed 0, fp32;
- CBGS gives 115,674 samples per epoch, so **2 CBGS epochs = 57,838 iterations**, in one cyclic cycle (peak 5e-4 at 40 %);
- the epoch count was set by the compute cap ($34): the speed check projected $31.44, so both epochs ran.

**Hosts** [OWN_DETECTOR_NOTE_v01]:
- iterations 1–1,000 on the first of two cloud machines;
- iterations 1,001–57,838 on the second (RTX 4090), resumed exactly from `iter_1000.pth` (optimiser and schedule restored), 16.70 h;
- the data order after the resume is not that of an unbroken run;
- the sparse-convolution kernels printed an architecture warning (no sm_89 build) on every call, with no error.

**Weights and configuration, as hashed** [`30_DATA/av2_det_owncp_v01/SHA256SUMS.txt`, e8dad0a8…; OWN_DETECTOR_NOTE_v01]:
- the checkpoint `env/own_centerpoint_iter_57838.pth`: 68369a713ed1acd725f4abdb9edcbdc3473f7fdc5ca5b9b0f515ade1083105ee;
- the dumped training configuration `env/cfg_train_i57838_b4.py`: 277f0969e34d7e6145253e1010e5a1d0f371aee7097709f3d61a859a3eddb2c9. It differs from the stopped segment's copy only in `work_dir`;
- the package list `env/lt3d_pip_freeze_v04c.txt`: c85990c1…;
- the cloud-machine scripts `50_CODE/owndet/pod/`: `pod_owndet_full_v03.sh` 26757c64…, `pod_owndet_cfg_v03.py` 36757830…, `pod_owndet_infer_v02.sh` 024d7f20…, `pod_owndet_export_v01.py` 1caa6c7e…;
- no checkpoint or setting was selected on any of the 375 confirmation logs; AP was computed only on the final checkpoint, after training [C1 plan v07m §1.2].

**Inference** [OWN_DETECTOR_NOTE_v01; SHA256SUMS above]:
- the configuration's test pipeline with flip TTA, every 5th sweep (the 2 Hz protocol), in six `tools/test.py` shards merged in order;
- outputs, the detection inputs of the trackers:
  - `val150/av2val150_owncp_centerpoint_dets_v01.npz`: 3ce5e3724da3998fbdbf8057f29bccb3fa15043eafab1e2899a8a78516e48073 (150 validation logs, 4,806 frames, 12,376,531 rows);
  - `held225/av2held225_owncp_centerpoint_dets_v01.npz`: 3b06178f44d08af8cbc8a63af2d1c1c641c0b998c24d43d8240602f71cbbfa80 (225 held-out logs, 7,232 frames, 18,814,614 rows);
- every frame has predictions, and none is non-finite.

**AP at 50 m** (official av2 0.2.1 evaluator, ROI-filtered, 26 categories) [OWN_DETECTOR_NOTE_v01; C1 plan v07m §1.2]:

| | Vehicle | Pedestrian | Bicyclist | 26-class mean |
|---|---|---|---|---|
| validation | 0.857 | 0.777 | 0.403 | 0.425 |
| held-out | 0.854 | 0.800 | 0.495 | 0.415 |
| public checkpoint (validation) | 0.875 | 0.795 | 0.543 | 0.469 |

##### S9.15.1.3 Argoverse 2, the public detectors (descriptive routes and pre-freeze counts)

- **LT3D CenterPoint**, the public checkpoint `epoch_20.pth`, 299cf3b7… [`60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md`; OWN_DETECTOR_NOTE_v01, "Compared with the public run"]:
  - trained on all 700 train logs: 20 epochs, batch 8 on 8 GPUs, probably every 10th sweep;
  - run on the 150 validation logs only (H1-P).
- **VoxelNeXt**, the OpenPCDet "model-32M" checkpoint, 8641d838…, wrapped unchanged (e513ef56…). It regresses no velocity and is run on the 150 validation logs only (H5) [AV2_DETECTOR_NOTE_v01].

---

#### S9.15.2 Trackers on Argoverse 2 at 2 Hz

##### S9.15.2.1 What was ported, and what is common to T1 and T3

- **Code.**
  - The CANMOT tree at the pinned commit 515d0792…, with devkit e4818ff9…, clean [`60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v01.md` §3].
  - The runner `50_CODE/av2/av2_track_v02.py` (0a9a0eb3…) imports `x1_export_v06`'s verbatim copies of CANMOT's `run.py` loop body and state capture, so the export is produced by the same code as on nuScenes [AV2_TRACKER_PORT_DESIGN_v01 §6; AV2_TRACKER_NOTE_v03 §7].
  - The tracker is reset at each log's first frame [AV2_TRACKER_PORT_DESIGN_v04 §7].
- **Shims; no third-party file was edited** [AV2_TRACKER_PORT_DESIGN_v01 §8]:
  - S1, AV2 detections written as nuScenes-format detection JSON;
  - S2, the runner skips `run.py`'s nuScenes dataset checks but keeps its environment checks;
  - S4, the numba hull (`--fast-convex`), equal record for record to Qhull on nuScenes val and on 2 AV2 logs;
  - S5, a pure-Python Feather reader.

  S3, the no-velocity shim, applies only to VoxelNeXt; the own detector has velocity [AV2_TRACKER_PORT_DESIGN_v04 §5].
- **Frames.** Every 5th lidar sweep from sweep 0 [AV2_TRACKER_PORT_DESIGN_v01 §2]. The trackers use their configured constant `LiDAR_interval` of 0.5 s, while the actual spacing on Argoverse 2 runs from 0.4958 to 0.5999 s (median 0.5003 s).
- **Coordinate frames** [AV2_TRACKER_PORT_DESIGN_v01 §3]:
  - detections go from the ego frame to the city frame with `city_SE3_egovehicle`, looked up by exact time stamp;
  - velocity is rotated only, with no ego-velocity term, because LT3D's velocity is ground velocity in ego axes (probe P-b);
  - the own detector follows the same convention: median cosine against LT3D's velocities 0.99986 (probe P-c) [AV2_TRACKER_NOTE_v03 §3].
- **Classes** [AV2_TRACKER_PORT_DESIGN_v01 §4.2–4.3; v03 §12.1]:
  - AV2 categories are mapped onto the seven nuScenes tracking classes, whose class-specific parameters are then used;
  - car ← `REGULAR_VEHICLE`; pedestrian ← `PEDESTRIAN`; bicycle ← `BICYCLIST`; motorcycle ← `MOTORCYCLIST`; bus ← three bus categories; truck ← `TRUCK`, `BOX_TRUCK`, `TRUCK_CAB`, `LARGE_VEHICLE`; trailer ← `VEHICULAR_TRAILER`;
  - a ridden `BICYCLE` or `MOTORCYCLE` cuboid is attached to its rider (rule RB-1), and detected bicycles and motorcycles are not fed;
  - the analysis groups are car, pedestrian, two-wheeler (bicycle and motorcycle classes) and large.
- **Changes on the input side for AV2** [AV2_TRACKER_PORT_DESIGN_v01 §4.4, §5]:
  - a detector score floor of 0.1 before the tracker's own filter. The nuScenes input had this floor implicitly; it was added for AV2 after the adapter's counts showed sub-0.1 LT3D boxes;
  - a ±54 m bird's-eye-view square in the ego frame.

  On the 375 logs, 1,617,812 boxes were kept from 31,191,145 rows [AV2_TRACKER_NOTE_v03 §4].
- **Parameters shared by T1 and T3, transferred unchanged from nuScenes** [AV2_TRACKER_PORT_DESIGN_v01 §4.4; CANMOT `config/poly_mot/*.yaml` at 515d0792…]. Labels: 0 bicycle, 1 bus, 2 car, 3 motorcycle, 4 pedestrian, 5 trailer, 6 truck.
  - class score filter `SF_thre`: {0: 0.14, 1: 0, 2: 0.16, 3: 0.16, 4: 0.16, 5: 0.10, 6: 0};
  - non-maximum suppression: `blend_nms` on `iou_bev`, threshold 0.08, across all fed classes;
  - first-stage association: `giou_3d` (bus `giou_bev`), thresholds {1.55, 1.34, 1.31, 1.44, 1.69, 1.25, 1.21}; second stage `giou_bev` at 1.0; Hungarian;
  - life cycle: `max_age` {10, 10, 15, 20, 10, 10, 20} frames, `min_hit` 1, score decay {0.05, 0.3, 0.2, 0.1, 0.15, 0.15, 0.25}; output `punish_num` 1; no post-NMS.
- **No tracker parameter was re-tuned on AV2** [AV2_TRACKER_PORT_DESIGN_v01 §4.4; v04 §8; C1 plan v07m §1.1].
- **Outputs used by the planner** [AV2_TRACKER_PORT_DESIGN_v02 §12.2; AV2_TRACKER_NOTE_v03 §4]:
  - the exported track records, with the 2-D position covariance taken from HPHᵀ;
  - the tracker's own propagation of mean and xy covariance in 0.5 s steps to 4 s, made by `av2_horizon_prep_v02 --propagate-only` (= `x1_horizon_prep_v04`'s `propagate`);
  - only tracks with a tracking score ≥ 0.4 enter the stage-A caches;
  - T3's exported velocity field is converted back to (v_x, v_y) by the loader's Poly-MOT velocity fix (`m_data_v04.load_export_v2`) [AV2_TRACKER_PORT_DESIGN_v01 §9; `50_CODE/av2/av2_cache_stageA_v02.py` docstring; E01 §2.3].
- **Pairing to annotations** happens at the decision time only: persistent per-class Hungarian on center distance with a 2 m gate, against annotations with ≥ 1 interior lidar point [AV2_TRACKER_PORT_DESIGN_v01 §7].

##### S9.15.2.2 T1, CANMOT `paper/local/canmot/sc`

- **Filter.** Extended Kalman filter with a constant-velocity model for every class, Q rotated into the box frame (EKF-rotate) [E01 §2.3; AV2_TRACKER_PORT_DESIGN_v01 §4.4].
- **Configuration.** The experiment file sets [`50_CODE/third_party/CANMOT/config/experiment/paper/local/canmot/sc.yaml`, lines 4–6]:
  - Q: `model_cfg/matrix_q: centerpoint/local/val/canmot_q`;
  - R: `model_cfg/matrix_r: centerpoint/local/trainval/sample_cov`;
  - the tracker configuration `poly_mot: nusc_config_rotate_cov_cv`.
- **Q** was tuned by Bayesian optimization for AMOTA on nuScenes **val** by CANMOT's authors [E01 §2.3]. The Q used on AV2 has SHA-256 59c0aea8…, "as on the 150 logs" [AV2_TRACKER_NOTE_v03 §4].
- **R** is the nuScenes trainval sample covariance [E01 §2.3].
- The numerical Q and R matrices are not reproduced in the records read.

##### S9.15.2.3 T3, Poly-MOT `paper/baseline/poly_mot`

- **Filters.** A CTRA extended Kalman filter for car, bus, pedestrian and truck, and a linear CA Kalman filter for bicycle, motorcycle and trailer [E01 §2.3; AV2_TRACKER_PORT_DESIGN_v01 §4.4].
- **Configuration.** `matrix_q: null` and `matrix_r: null`, so Poly-MOT's own Q, R and initial P apply, with `poly_mot: nusc_config_poly_mot` [`50_CODE/third_party/CANMOT/config/experiment/paper/baseline/poly_mot.yaml`, lines 4–6, 13–15]. The CTRA Q is the identity [E01 §2.3].
- **The Q used on AV2** has SHA-256 0a3a48d5…, "as on the 150 logs" [AV2_TRACKER_NOTE_v03 §4].

##### S9.15.2.4 AB3DMOT (descriptive third tracker, label `tab`)

- **Code.** LT3D's AB3DMOT at commit e33189aa (partial clone of `tracking/` and `data/` into `50_CODE/third_party_av2/LT3D/`, unchanged). The driver `50_CODE/av2/av2_ab3dmot_v05.py` (e4ea9950…) repeats LT3D's `tracking/test_tracker.py` loop line for line, and runs in `50_CODE/env/ab3dmot310` (numpy 1.23.5, scipy 1.10.1, numba 0.58.1, filterpy 1.4.5) [`60_RESULTS/av2_trk/AV2_AB3DMOT_NOTE_v01.md` §1; AV2_TRACKER_NOTE_v03 §7].
- **Settings: LT3D's defaults, not re-tuned** [AV2_AB3DMOT_NOTE_v01 §1; `…/LT3D/tracking/test_tracker.py`, lines 32–34 (source code)]:
  - score > 0.1, and the top 500 boxes per frame over all 26 categories;
  - one single-class AB3DMOT per category, of which only the 12 mapped categories are passed on;
  - `max_age` 3 frames; IoU matching at 0.1 (Hungarian);
  - track scores averaged over each track afterwards.
- **Filter** [`…/LT3D/tracking/ab3dmot.py`, lines 196–229 (source code)]:
  - a constant-velocity Kalman filter on (x, y, z, yaw, l, w, h, v_x, v_y, v_z), with F adding one frame's velocity per step;
  - initial P: 10·I on the box block and 10⁴ on the three velocities (P[7:, 7:] × 1000, then P × 10);
  - Q: the identity, with 0.01 on the velocities;
  - R is not set in `ab3dmot.py`, so filterpy's default applies: the identity. This is an inference from the source, not a record.

  The project note describes the setting as "unit Q and R and … high initial velocity variance … tuned for 10 Hz KITTI-style use" [AV2_AB3DMOT_NOTE_v01 §3].
- **At 2 Hz** one filter step is one frame, 0.5 s [AV2_AB3DMOT_NOTE_v01 §1]:
  - exported velocity = state velocity / 0.5 s, and covariance = HPHᵀ (7 × 7);
  - the 2 s propagation is the filter's own, x ← Fx and P ← FPFᵀ + Q per 0.5 s step;
  - the planner uses the filter-state ("kf") export, with experiment tag `lt3d/ab3dmot` [AV2_TRACKER_NOTE_v03 §9].
- **Shims** [AV2_AB3DMOT_NOTE_v01 §1; AV2_TRACKER_PORT_DESIGN_v04 §6–§7]:
  - L1, two functions of LT3D's `data/utils.py` copied verbatim;
  - L2, an exact association speed-up, identical on a test log;
  - v05 adds the own detector, per-log checkpoints that include `KalmanBoxTracker.count`, and the dataset tag.

##### S9.15.2.5 Equivalence of the port

Each port tool reproduced its v01 output on the 150 validation logs with the public LT3D detections before any 375-log output was kept [AV2_TRACKER_NOTE_v03 §2; `60_RESULTS/av2_trk/c1_375/equiv/`]:
- **byte-identical:** the ground-truth preparation (hashed, never opened; deleted) and the decompressed T1 and T3 track exports;
- **identical after decompression:** the ego file;
- **byte-identical after one documented substitution** (the adapter's name): the tracker input;
- **identical:** the AB3DMOT exports and the propagation;
- **the metric tools:** AMOTA/MOTA/IDS equal, HOTA within a relative 1e-12 (the evaluator is not bit-reproducible run to run).

Two tools were corrected in place at 07:07 EST on 5 Nov, before any production output was kept. The production T1 worker started on the earlier file at 07:06:01 was stopped and rerun [AV2_TRACKER_NOTE_v03 §8; C1 plan v07m §1.1].

---

#### S9.15.3 Trajectron++ and its online adaptation

##### S9.15.3.1 Model and code

- **Code.** Trajectron++, ECCV 2020 branch, commit ef0165a93ee5ba8cdc14f9b999b3e00070cd8588, sparse checkout [`50_CODE/tpp/TPP_PROVENANCE_v01.txt`].
- **Model.** `int_ee`, `model_registrar-12.pt`, 3fcc65cd8f48b70fce4965813e503e03c664e027f1f83f8a27d317773a138028, with `config.json` 3538638e… on disk. The authors' checkpoint was trained on the 700 nuScenes train scenes [`90_DECISIONS/D17_TPP_ARM_PREREG_v04.md` §3, §4].
- **Map.** It runs without a map, because the map expansion was absent. `int_ee_me` is not used in C1 [D17 §4, §9 item 1; C1 plan v07m §2].
- **Safety check.** A pickle scan found no disallowed global before any `torch.load` [TPP_PROVENANCE_v01].

##### S9.15.3.2 The online adaptation

As stated in `50_CODE/tpp/tpp_run_v01.py` (docstring, lines 2–31) and D17 §4 and §9 items 3–6:
- **Streaming.** One `OnlineTrajectron` per scene (on AV2, per log), streamed over every keyframe with `incremental_forward`, the eccv2020 online API as in `trajectron/test_online.py`. Hyper-parameters are the model's `config.json` with `test_online.py`'s argument defaults; the defaults equal the config values for `int_ee`, which was checked and recorded.
- **Nodes.** Every deployed track (score ≥ 0.4) of a mapped class is a node: car, truck, bus and trailer as VEHICLE, pedestrian as PEDESTRIAN; motorcycle and bicycle are **not fed**. The logged ego is added as the node `ego`, a robot VEHICLE as in `process_data.py`.
  - On AV2 the cache classes are the mapped nuScenes classes of S9.15.2.1. No AV2-specific Trajectron++ class map is recorded.
- **State at k.**
  - position: the box center minus the scene offset of `process_data.py`;
  - velocity and acceleration: Trajectron++'s own `derivative_of`, on the node's contiguous history up to k (causal);
  - heading: the tracker's yaw; heading rate by `derivative_of`.

  Training used central differences over the whole track, and at track birth the velocity is 0 (D17 §9 item 5).
- **Prediction.** At each keyframe the encoders are advanced for every node. For each record whose node has ≥ 2 contiguous states, the decoder runs as `sample_model` does: `_run_decoder`, `num_samples` 1, `z_mode` False, `gmm_mode` False, `full_dist` True, horizon 6.
  - A torch seed is fixed per (scene, k, node) from SHA-256 of `scene|k|node|<base>`.
  - The decoder conditions on sampled controls, so one forward pass is one random draw.
- **Covariance.** V2 (primary) is the moment-matched mean and covariance, μ = Σπₖμₖ and Σ = Σπₖ(Σₖ + dₖdₖᵀ). V1 is the largest-weight component. Output at step h + 1, with h = 3 the 2 s step.
- **Known departures from training** (D17 §9 items 4–6):
  - the history LSTM carries state for a track's whole life, while training used 8 steps;
  - the ego pose is the cache's keyframe pose, not the CAM_FRONT sample pose;
  - parked vehicles cannot be identified and are fed.

##### S9.15.3.3 Platform, seeds and scoring

- **Platform.** The laptop only, in `50_CODE/env/tpp38`: Python 3.8.20, torch 1.4.0+cpu, numpy 1.18.5. On AV2 these versions are checked against FROZEN_ENV_TPP; the keys builder `tpp_keys_v03` runs under canmot310 and is checked against FROZEN_ENV [D17 §4; C1 plan v07m §6.4 and lines 2274–2285].
- **Seeds.** Base seed 20261102 (primary); 20261104 and 20261105 for the descriptive seed-robustness label [D17 §4; C1 plan v07m §4, §6.4].
- **Items** [D17 §3; C1 plan v07m §6.4]:
  - the K8 items of the tracker-planner (the arm-independent relied items of `k8_items` at the reference pose, S9.11(a)), taken from those items and not recomputed;
  - on AV2, the relied in-path (PD) items at the 2 s step.
- **Calibration on AV2 (H9, descriptive).** DP-SCRC with history-length strata ({2, 3–4, ≥ 5} contiguous tracker states up to k, read from the keys), cross-fitted on the C1 folds. H9-T uses the nuScenes-fitted calibration [C1 plan v07m §6.4; the authors' decision record].
- **Wrappers on AV2.** `tpp_run_v03` and `tpp_keys_v03` run v01's code unchanged. They add a wrapper record (entry-point, run and keys hashes, seed, environment versions) and refuse subsets of the units [`50_CODE/tpp/tpp_run_v02.py`, `tpp_run_v03.py`, `tpp_keys_v02.py`, `tpp_keys_v03.py` docstrings].

---

#### S9.15.4 What the records do not state

- the nuScenes CenterPoint checkpoint, its configuration and its training schedule (S9.15.1.1);
- the numerical Q and R matrices of T1 and T3 (identified by configuration name and by the hash of Q only);
- AB3DMOT's R (inferred from the source code, S9.15.2.4);
- an AV2-specific Trajectron++ class map (S9.15.3.2);
- the layers of the own CenterPoint beyond the configuration's name (S9.15.1.2).

---

## S10. What was computed on the 375 test logs before the freeze, in full

Section VI-D of the main text summarizes this section. It covers all 375 test logs, the 150 validation logs and the 225 held-out training logs, up to the freeze at **2026-11-06 20:08:13 UTC**; the text lock was at 15:08:58 UTC the same day, and the registration at 20:31 UTC. It was built from the records only, each cited in brackets; nothing was run, and no ground-truth file was opened, to write it. Times are UTC unless marked EST (UTC − 5).

**Sources** (paths relative to the project root):

| Key | Record |
|---|---|
| PLAN | `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md` (frozen, 0817e600…), §0, §1.1–§1.6, §6.4, §7, §10, §11.3 |
| FTR | `40_PROTOCOL/C1_FREEZE_TIME_RECORD_v01.md` (bound by the freeze as `data:freeze_record`) |
| DEV | `40_PROTOCOL/C1_DEVIATION_LOG_v01.md` (post-freeze events only) |
| DR | The authors' decision record (one released file) |
| D18 | `90_DECISIONS/D18_S0_SAMPLE_SIZE_DECISION_v02.md`, `_v03.md` |
| DET1 | `60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md` (public detectors, 1 Nov) |
| DETO | `60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md` (own detector, 5 Nov) |
| TRK1, TRK2, TRK3 | `60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v01.md` (1–2 Nov), `_v02.md` (2 Nov), `_v03.md` (5 Nov) |
| AB | `60_RESULTS/av2_trk/AV2_AB3DMOT_NOTE_v01.md` (2 Nov) |
| QC1–QC3 | `60_RESULTS/qcnet_av2/QCNET_AV2_NOTE_v01.md`, `_v02.md`, `_v03.md` (2 Nov) |
| PORT1, PORT3, PORT4 | `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md`, `_v03.md`, `_v04.md` |
| EQ | `60_RESULTS/av2_trk/c1_375/equiv/` (the port's equivalence records, bound as `data:port_equiv`) |
| E0 | `50_CODE/c1_av2/c1_e0_v01.py` and `c1_e0_v05.py` (docstrings) |
| PROV | `50_CODE/c1_av2/c1_av2_provenance_v01.py` (docstring) |

### S10.1 How ground truth could enter a computation

Each computation below is classed by the most it read of the annotations:
- **G0:** no annotation. Detections, tracker outputs, logged ego poses, time stamps, file names, sizes and hashes only.
- **G1:** annotation positions **at the same sweep** as the quantity computed. This covers detector AP, tracking metrics, and pairing tracks with objects at the decision time k (PLAN §1.5, "Rule 0").
- **G2:** whether an annotation **exists at a later sweep**, with its lidar point count, but never its position (DR).
- **G3:** an annotation **position after the decision time**.
- **W:** the tool wrote or re-made a file that holds annotation positions at every sweep, without comparing any of them with an estimate or a prediction. Such files are listed so that a reader can see where later positions existed.
- **Ego after k** is marked separately. It means the logged ego trajectory after k was used: the planner's leash and reference pose, or a centered speed window. These are logged ego poses, not annotations.

### S10.2 The answer in brief

- **G3.** According to the records, **no computation made before the freeze used an annotation position after a decision time**.
  - The C1 steps that do (stage B, the method stage, H8 and the E⁰ recompute) first ran after the deposit record (PLAN §1.5, §11.3; FTR §5; DEV entries 1–3).
  - No AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error was computed or seen (PLAN §10 item 10; FTR §5).
- **Annotation files did exist and were read by tools.**
  - Files holding annotation positions were written or re-made by tools in P1, P2, P5, P6, P7, P9 and P16 (class W).
  - Detector AP and tracking metrics used positions at the same sweep (G1).
  - Stage A and the counts used later-sweep existence only (G2).
- **The limit of this answer.** The public annotation files of all 375 logs were on the analysis computer. Tools outside the guarded entry points write no run-log line. The records therefore show what was run and recorded, not that nothing else was run (PLAN §1.5 "Scope", §11.3).

### S10.3 Every computation before the freeze, in time order

| # | When | Logs | What was computed | Ground truth | Ego after k | Source |
|---|---|---|---|---|---|---|
| P1 | 1 Nov | val 150 | Public LT3D CenterPoint and VoxelNeXt inference on 4,806 frames (on a cloud machine); AP at 50 m with the official av2 evaluator | G1 (labels of the evaluated frames); W: the evaluation ground-truth feather `av2val_lt3d_centerpoint_gt_v01.feather` (a9d85a54…) | no | DET1; PLAN §10 items 2–3 |
| P2 | 1 Nov | val 150 | Prepared ground truth `av2_val_gt_v01.json` (9642db5b…): annotations mapped to nuScenes classes, ridden-bicycle rule, ground-truth velocity by central differences; printed counts only | W (positions at every frame; velocities from neighbouring sweeps); no comparison with an estimate | no | TRK1 §1; PORT1 §7, §9 |
| P3 | 1–2 Nov | val 150 | Tracker port v01: detections to tracker input; T1, T2, T3 on LT3D and T1, T3 on VoxelNeXt; native-against-fast hull check; AMOTA, MOTA, IDS and other CLEAR metrics; counts v01 (method-stage geometry at k; future availability) | G0 (tracking); G1 (metrics; pairing at k); G2 (whether the paired object is annotated at k + 4, by existence and point count) | no | TRK1 §1–§7; PORT1 §9, §11 |
| P4 | 2 Nov | val 150 | Stage A v01 (T1, T3 × LT3D, VoxelNeXt; AB3DMOT × LT3D): the trackers' own 2 s propagation; the 10 Hz ego path; caches with every annotation position NaN; K8 counts-only items (`k8_items_v04 --av2 --counts-only`), giving counts v02 (PD7, SD1_7, PD, NIP per cell); HOTA with `av2_hota_v03`, per-class score thresholds tuned on the validation ground truth; AB3DMOT at 2 Hz with its metrics | G0 (propagation, ego); G1 (HOTA, AMOTA; pairing at k); G2 (`tr_vis8`; items need the paired object annotated at k + h) | **yes**: items take enforced pairs and the relied axis at the logged ego pose at t_k + h, with the leash to 4 s; the field `tr_anorm2s_log` uses the logged ego at k + 4 | TRK2 §1–§5; AB; PORT3 §12–§13; DR |
| P5 | 2 Nov | val 150 | QCNet arm (three cloud machines): LT3D CenterPoint at 10 Hz on 23,547 sweeps with an AP sanity check; LT3D AB3DMOT at 10 Hz; QCNet forward passes from ground-truth histories and from deployed histories (three history rules); counts, finiteness and positive-definiteness checks, frame tests, join coverage against the 2 Hz tracker records | G1 (AP); ground-truth **histories**: positions at and before each origin t₀, "no GT position after an origin was read"; G2 (visibility at the 2 s target, by time stamp and point count); W: `qcnet_av2_gt_v01.npz` (993019f6…) and `qcnet_av2_gt_recentred_v02.npz` (6380a729…), history files | no | QC1 (outcome statement, §5–§6); QC2; QC3; PLAN §1.3, §10 items 2–3; DR |
| P6 | 2–5 Nov | train 475 (training); held-out 225 and val 150 (inference) | Own CenterPoint trained on the 475 training logs only; infos built; inference on the 375 logs; AP on validation and held-out after training, on the final checkpoint only | G1 (AP); W: `av2val150_owncp_centerpoint_gt_v01.feather` (a9d85a54…, the same bytes as P1's), `av2held225_owncp_centerpoint_gt_v01.feather` (8cb86154…), `infos_archive_v01b.tar` (ada2146d…; ground truth by member names) | no | DETO; PLAN §1.2, §10 item 3 |
| P7 | 5 Nov, about 06:56–07:30 EST | val 150 (public LT3D detections) | Port v04 equivalence tests against the v01 outputs: ground-truth preparation (the output only hashed, then deleted); ego file; tracker input; T1 and T3 exports (with an interrupt-and-resume test); AB3DMOT; propagation; AMOTA/MOTA/IDS and HOTA recomputed on the v01 T3 × VoxelNeXt exports and checked for equality with P3/P4's stored values | W (the re-made prepared file, hashed and deleted at once, never opened); G1 (the metric tools; values equal to P3/P4's) | no | TRK3 §2, §8; EQ; PLAN §1.1 |
| P8 | 5 Nov | val 150; held-out 225 | Velocity probe P-c, own detections against LT3D detections (no ground truth); frame-time check of the 225 logs against their bucket listing and of the 150 against their lidar folders | G0 | no | TRK3 §3 |
| P9 | 5 Nov | all 375 | Production: tracker input from the own detections; prepared ground truth `av2_c1_gt375_v01.json` (e5c390aa…); ego path (reads only the samples' ego poses); T1, T3 and AB3DMOT tracking; 2 s propagation; the port's ground-truth list. The Rule-0 metrics were **held** (gate files moved; nothing computed) | W (the prepared file); G0 (the rest) | no | TRK3 §1, §4–§6 |
| P10 | 5 Nov, 14:56 EST | val 150 counts, resampled to 375 | H9 projection: `c1_power_counts_v05` part H9 on the 150-log public-LT3D counts-only items (2 cells in every draw). Earlier power projections (D18 v03; plan drafts v07d, v07e) also used the 150-log counts | G2, through the items | yes, through the items | PLAN §6.4, §7, §10 item 2; D18 |
| — | **6 Nov 15:08:58** | | **Text lock** (the author's OSF upload of v07m DRAFT, 3e303eee…) | | | DR |
| P11 | 6 Nov 15:12–17:15 | all 375 (per part and pooled) | Step 9, Rule-0 metrics: 12 HOTA files (`av2_hota_v04`) and 12 AMOTA/MOTA/IDS files (`av2_track_metrics_v04`) for T1, T3 and AB3DMOT's two exports, on the validation part, the held-out part and all 375 logs | G1 (`av2_hota_v04` is v03 with a log restriction, so the thresholds are tuned on the ground truth as in P4) | no | FTR §1; DR; PORT4 §6 |
| P12 | 17:15–17:38 | all 375 | Step 10, stage-A caches (T1, T3, AB3DMOT) with `av2_cache_stageA_v02` | G1 (pairing at k); G2 (existence at k + h); every annotation position, box, size and yaw NaN at every frame | yes (the logged ego path is kept in full for decision construction) | DR; PLAN §1.5; PORT3 §12.2 |
| P13 | 17:38–17:47 | all 375 | Step 11: S20a counts (`k8_items_v04 --av2 --counts-only`, then `av2_counts_v02`; error fields NaN and never read) and S22 power (parts A and B projected from the 150-log counts v02, part H9 on the 375-log items, part J analytic) | G2 | yes (items at the logged pose) | PLAN §1.6, §7; DR |
| P14 | 17:48–17:49 | all 375 | Step 12, folds (log ids, seeded permutation); step 13, scene map (names); the validation logs' city codes, from bucket file names | G0 | no | DR |
| P15 | 17:49–17:57 | all 375, T1 | Step 14, E⁰ for H8 (`c1_e0_v05`, seed 20261114): pairing at k from the annotation at k; at the 2 s target only the paired object's existence and point count; 20 draws per item from the tracker's covariance; "E0 never uses D". Values 0.0824 and 0.0897 | G1 (at k); G2 (target) | no | E0 (docstring); PLAN §6.3 (S21); DR |
| P16 | 17:58–19:11 | all 375 | Step 15, provenance: the T1 and T3 horizons re-made from tracker output; the ego file re-made; the prepared ground truth re-made by `av2_gt_prep_v02` into a temporary file outside the workspace, hashed and deleted at once, never opened; all hashes equal | W (the re-made prepared file); G0 (the rest) | no | PROV; DR; FTR §6.4 |
| P17 | 19:12–19:40 | files | Steps 16–19b: inventory v03 (8 files by a content rule); three off-workspace hash scans; quarantine into 7 gzip members (19:15–19:18); dry run; hand checks (member hashes only, nothing decompressed); config shape and value checks; the 62-command list; the input-binding check | G0 (file level) | no | FTR §2–§6 |
| P18 | 19:42:13–20:08:14 | — | Step 20, the freeze, with the bound test suite `test_c1_v13`. The suite tests the AV2 paths in a copy tree on R17d's AV2-tagged stand-in, not on AV2 data | G0 for AV2 | no | DR; PLAN §0 ("Stand-ins are not evidence") |

**Not on any AV2 log.** Every rehearsal of the confirmatory path used nuScenes validation scenes as stand-in "AV2" units. The AV2 code paths were tested on R17d's AV2-tagged stand-in. The criteria audit and the development replays used nuScenes development data (PLAN §0, §10 items 1 and 5).

### S10.4 The same computations, grouped by what they used

- **G3, annotation positions after the decision time:** none recorded (S10.2).
- **W, files with positions at every sweep, written or re-made without any comparison:**
  - P2, P9: the two prepared files;
  - P1, P6: the detector-evaluation ground truth and the training-info archive;
  - P5: the QCNet ground-truth history files, which hold positions up to the origin only;
  - P7, P16: re-made prepared files, hashed and deleted at once.

  All files that remained were moved into the verified quarantine before the freeze: 8 files, 7 members, because two are byte-identical; every plain copy was removed (FTR §4; PLAN §10 item 3).
- **G1, annotations at the same sweep:**
  - detector AP: P1, P5, P6;
  - tracking metrics: P3, P4, P7, P11;
  - pairing at the decision time: P3, P4, P12, P15.
- **G2, existence and point count at a later sweep:**
  - future availability: P3;
  - stage-A visibility fields and K8 items: P4, P12, P13;
  - QCNet target visibility: P5;
  - projections from the counts: P10, P13;
  - E⁰'s visibility condition: P15.
- **Tracker outputs, detections, poses or file metadata only (G0):**
  - tracking and the 2 s propagation: P3, P4, P9;
  - ego paths: P4, P9, P16;
  - the velocity probe and frame checks: P8;
  - folds, scene map and city codes: P14;
  - inventory, scans, quarantine and checks: P17;
  - the provenance re-makes of horizons and ego: P16.
- **Logged ego trajectory after k:** the K8 items and counts in P4, P10 and P13. Their enforced pairs and relied axis are evaluated at the logged ego pose at t_k + h, and the leash reaches t_k + 4 s. Stage A also keeps the logged ego path (P12).

### S10.5 Who saw what

| Who | What they saw | Source |
|---|---|---|
| **The analyst** (who ran the registered test) | **Before the text lock:** public-detector AP and the own detector's AP (P1, P6); the 150-log tracker metrics with the public detectors, HOTA included (P3, P4); counts v01 and v02 (P3, P4), "which set the sample size"; the port's 375-log counts (P9); the H9 projection (P10); QCNet counts, integrity checks and coverage (P5); the own detector's training logs. **After the lock:** at about 15:19, the last lines of the job log `30_DATA/av2_trk_v02/logs/q_h_t1_val150.log`, which print T1's per-class HOTA on the 150 validation logs with the own detector; of the 24 Rule-0 files, otherwise only `n_logs` and `wall_seconds`; the S20a counts, the S22 file, the folds' composition, the scene map, the E⁰ values, the provenance record, the inventory and the quarantine manifest | PLAN §10 item 2; FTR §1, §5; DR |
| The analysis run that ported the trackers (author of TRK3) | The step's counts and integrity results. "No ground-truth file was opened by hand"; ground truth was read only by the tools | TRK3, outcome statement; DR |
| The analysis runs of the detector, tracker-v01/v02 and QCNet steps | The values in DET1, TRK1, TRK2, AB and QC1–QC3, which these runs wrote; the notes do not name the runs | those notes |
| The plan's author | "Ran no code on AV2 data for v05 to v07m and opened no AV2 file"; read decision, review, code and results-note text, and file-level facts | PLAN §0, outcome-blind attestation |
| A separate read-only check run before the freeze (19:23–19:36) | Hashed the 24 Rule-0 files and read only their log counts and run times, never a metric value | FTR §6.1 |
| A read-only code-review run | Source code only | FTR §1; DR |
| **The author** | "Has not been sent any value" of the Rule-0 metrics. D18 (counts only) was written for the author's decision, and the author chose option A on 2 Nov. Whether the author saw the 150-log metrics, AP or counts: **not recorded** | FTR §1; D18 v02 lines 5, 47 |
| Anyone | Any AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error before the freeze: not seen, "to the author's knowledge" | PLAN §10 item 10 |

### S10.6 What the records leave open

- **Tools outside the entry points.** Whether any tool outside the guarded C1 entry points read the public annotation files of the 375 logs before the freeze is **not recorded**. The run log records guarded runs only (PLAN §11.3).
- **Reviewers.** Whether the code and plan reviewers (R17 to R17g, R20) saw any AV2 metric value is **not recorded**. They reviewed code, plan text and stand-in rehearsals (PLAN §10 item 5).
- **Two cloud machines.** Whether two cloud machines used before the freeze received any AV2 data is **unverified**. Cloud storage, other project folders and other machines were not scanned (PLAN §10 item 4).
- **The official test split.** No record names the official Argoverse 2 Sensor test split as an input to any step.
