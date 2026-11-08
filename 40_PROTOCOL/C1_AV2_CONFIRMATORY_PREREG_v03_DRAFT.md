# C1 pre-registration v03 (DRAFT): the external confirmation on Argoverse 2 (2 Nov 2026)

**Status.** Draft. Not reviewed, not frozen. The hash block at the end is empty. Open items are marked `[SLOT: ...]` and listed in section 9. A freeze script must refuse this file while any slot is left. v01 and v02 (`C1_AV2_CONFIRMATORY_PREREG_v0{1,2}_DRAFT.md`) are kept unchanged.

**What v03 changes** (`90_DECISIONS/D16_DELEGATED_CHOICES_v07.md`, Choices 18 to 21):
- H9 (Trajectron++ on AV2) is secondary, cross-fitted within AV2; the nuScenes-fitted transfer is H9-T, descriptive (Choice 19).
- QCNet is descriptive (Choice 20); its primary deployed histories are matched AB3DMOT publishing only tracks at or above T1's class `SF_thre` (Choice 18).
- H3 is carried by **M\*Jx**, a pre-registered secondary with exact scene-level CRC; M\*J is descriptive (Choice 21). H3's formulas, its comparators on the joint loss, its power and its caveats are added (sections 1, 5.4, 6.6).
- Section 6.7 adds the scaling scenario for slot S0 (`50_CODE/c1_av2/c1_power_counts_v03.py`, `70_TESTS/c1_scratch/c1_power_scaling_v03.json`).

**What v02 changed.**
- Applies `90_DECISIONS/D16_DELEGATED_CHOICES_v04.md` Choices 6 to 17: within-AV2 cross-fitting primary, transfer secondary (6); a new all-850-scene transfer fit (7); four groups (8); a comparator that fails only a floor stays in Form B(ii) (9); the price is the decision-mode infeasible-rate difference (10); AB3DMOT as a descriptive third tracker (11); the B6 rule (12); the outcome-blind boundary for building AV2 items, stages A and B (13); HOTA with the official evaluator, T2 descriptive (14); matched AB3DMOT histories for QCNet (15); 2 Hz detections kept (16); QCNet re-centred (17). The multiplicity scheme of v01 section 5.5 is accepted subject to the pre-freeze review (D16 v04 "Multiplicity").
- Fills c = 0.03 for both trackers from the 840-scene K8 development analysis. This is the floor of the c rule; the measured decision-mode price is negative on both trackers (E11).
- Applies the K8 results review R16 (`70_TESTS/R16_K8_RESULTS_REVIEW_v01.md`) and its errata E8 to E14 (`90_DECISIONS/ERRATA_K8_v01.md`): M\* against B6 becomes the named motion-strata ablation H10; validity is worded "not shown above δ" (E10); loop mode stays descriptive with no ordering claim (E8); V2 is reported at its development level of about 0.35 (E9); RETUNED is reported as in E14; Choice 9 becomes a code requirement with a test (E13); CRC decisions are made in exact arithmetic (E15, `ERRATA_K8_v02.md`).
- Uses the AV2 stage-A decision counts `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v02.json` (counts only).
- Replaces v01's pooled-proxy power check, which used 10-scene development numbers, with a resampling check on the 840-scene development data and a direct floor check on the AV2 counts (section 6; `50_CODE/c1_av2/c1_power_counts_v02.py`). **The direct check predicts that H1 fails on M\*'s SD1_7 floor whatever the outcomes (section 6.1).**
- Recommended labels for H9 (Trajectron++) and the QCNet arm; decided in D16 v06 Choices 19 and 20 (applied in v03).

**Development numbers and their status.** Every nuScenes development number here comes from the complete Linux replicate of the K8 exploratory run, `70_TESTS/k8_expl_v02_linux/`, and its v03 analysis, `70_TESTS/k8_expl_v02_linux_analysis_v03/k8_exploratory_analysis_v03.json`. R16 recomputed them independently from the hashed raw arrays and confirmed every headline number. The Windows run of record agrees exactly on every decision-mode integer and boolean endpoint (`70_TESTS/k8_expl_v02_linux/PLATFORM_CHECK_v01.md`); loop-mode numbers are re-checked on the run of record (PLATFORM_CHECK_v02, R16 m7) before any is quoted.

**Outcome-blind attestation for this draft.** About AV2, the author read: `AV2_DETECTOR_NOTE_v01.md` (detector AP), `AV2_TRACKER_PORT_DESIGN_v01.md`, the counts files `AV2_TRACKER_COUNTS_v01.json` and `_v02.json`, `30_DATA/qcnet_av2_v02/qcnet_av2_counts_v02.json` (counts and integrity checks), and `50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md` sections 0 to 6 (design). No AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error was computed, opened or requested. The only code run on AV2-derived input reads the counts files.

---

## 0. Why C1, and what kind of evidence it is

**Role.** D13 Phase 4: one frozen plan for the method stage and the closed loop on external data. D14 section 1: the external run is "the same study" as K8. D16 fixes the GO form, the labels and the calibration route.

**The nuScenes evidence is development evidence.** K6 was a pre-registered NO-GO (power floor on T3). K7 was never frozen. K8 on the 840 nuScenes scenes is exploratory (D14 section 1). On those scenes, decision mode (confirmed by R16):
- infeasible-decision rate: T1 M\* 0.114, B4 0.198, B6 0.176; T3 M\* 0.161, B4 0.208, B6 0.167;
- comparators not shown above δ: B3 on T1; B0 and B3 on T3. B4 and B6 are shown above δ on both trackers (B6: 12 flagged PD7 cells on each tracker);
- Forms A, B and C are met on both trackers;
- M\* − B4: −0.084 (T1), −0.047 (T3).

**What "valid" means (E10).** "Not shown above δ" by the one-sided simultaneous test at 0.95, never "at most δ". M\*'s point estimate exceeds δ in 9 of 32 PD7 cells, 5 of 25 SD1_7 and 7 of 18 PD on T1, and in 11, 4 and 3 on T3; the largest are 0.085 (T1 SD1_7 pedestrian|long|new) and 0.068 (T1 PD car|lat|new); none is near a flag (largest t 1.3). T1's pooled PD estimate is 0.0495, one-sided upper bound 0.058 (R16 M3).

**Form B on T3 turns on B6 (E12).** M\* − B6 on T3 is −0.005 [−0.017, +0.005], a tie; if B6 were not shown above δ, Form B on T3 would fail. On nuScenes B6's failure is robust: 11 to 12 flagged PD7 cells with t up to 10.7 against q ≈ 3.18, structural because B6 is M\* without the motion strata (R16 M2).

**What C1 is.** The first look at AV2 for every outcome named here. AV2 differs from nuScenes in cities, sensors, annotation rate, detector checkpoint and score calibration (D15 section 2; `AV2_DETECTOR_NOTE_v01.md`). The trackers keep their nuScenes parameters (port design section 4.4).

**What the primary test adds (D16 v04 Choice 6, stated plainly).** With within-AV2 cross-fitting, M\*'s pooled cells are close to guaranteed not to be shown above δ by the theorem (P02 PM1): calibration and test logs are exchangeable. The primary test therefore adds:
1. no stratum shown above δ in small strata through the hierarchical fallback, cell by cell, under the planner's relied-on selection;
2. the operability price on new data;
3. the ranking against every comparator that is not shown above δ;
4. the premise's replication (H8).

**What a choice may use (D16 Rule 0).** The literature; nuScenes development results; AV2 detector AP, tracker HOTA/AMOTA and counts. Nothing else about AV2.

**One-shot commitment.** The AV2 validation split is used once for the claim family "validity and operability of DP-SCRC in the planner". A NO-GO leads to diagnosis and new work on new data, never to a re-run of C1 (section 8).

**Reporting constraints.** A C1 GO supports section 1's claims on AV2 validation with the named detector, trackers and calibration route only. nuScenes K8 numbers are quoted as development evidence beside K6 (NO-GO) and K7 (not frozen). No label changes after the freeze (D16 Rule 0, "No swaps").

---

## 1. Claims under test

### 1.1 Hypotheses

**Manuscript claims** (`20_DESIGN/MANUSCRIPT_DRAFT_v02.md`, section I Contributions): MC2 the mis-shaped 2 s covariance and NEES misdirection (V-B); MC3/MC4 DP-SCRC validity on held-out logs and after transfer, and B4's failure (IV, V-C); MC5 the planner study (V-D, VI-G); R14 O1 a deployed learned predictor (V-D "Planned").

δ = 0.05 throughout. The formulas are in section 5.4.

| ID | Label | Maps to | Statement (LT3D detector, decision mode, unless stated) |
|---|---|---|---|
| **H1** | **Primary** | MC5 | **Form B** holds on T1 **and** T3 with within-AV2 cross-fitting (Choice 6): no cell or pooled cell of M\* is shown above δ on PD7, SD1_7 or PD, with the floors and HK1c met, and M\* is less often infeasible than every comparator not shown above δ (Choice 9). On T3 this is expected to turn on B6 (E12) |
| H2 | Secondary | MC5 | **Form C ceiling**: the decision-mode price, M\* − B4 infeasible rate, is ≤ c_t on T1 and T3, with c_T1 = c_T3 = **0.03**, the floor of the c rule (E11) |
| H3 | Secondary (Choice 21) | MC5 | **Trajectory-level certificate, M\*Jx**: on T1 and T3, M\*Jx's joint loss (per decision, any relied constraint over the 4 calibrated steps and all tracks exceeded) is not shown above δ on PD7, SD1_7 and PD, **and** Form B holds on the joint loss: M\*Jx is less often infeasible than every comparator not shown above δ on the joint loss |
| H4 | Secondary | MC5; S02 R10 | **Transfer in the loop**: Form B on T1 and T3 with every fitted arm from the all-850-scene nuScenes fit (Choices 6, 7) |
| H5 | Secondary | MC5 | **Second detector**: Form B on T1 and T3 on VoxelNeXt tracks, within-AV2 cross-fitting |
| H6a | Secondary | MC3/MC4 | **Method stage within AV2 (E1-AV2)**: M\* shown above δ in no E1-AV2 cell, fixed-rule and refit-CV, T1 and T3 (HM1 analogue) |
| H6b | Secondary | MC4 | **Practitioner failure**: B4 fails (flagged, M\* not, paired difference positive; refit-CV) in at least one E1-AV2 cell on T1 and on T3 (HM2 analogue) |
| H7 | Secondary | MC3/MC4 | **Method stage, transfer (E2-AV2)**: the M-stage M\* fitted on the 700 nuScenes train scenes is shown above δ in no AV2 cell and not in the pooled AV2 cell, T1 and T3 (HM6 analogue) |
| H8 | Secondary | MC2 | **Diagnosis replicates (T1)**: an in-path car lateral 2 s cell (< 20 m or 20 to 40 m) FAILS under B0, and its truth-oriented exceedance also FAILS |
| H9 | Secondary (Choice 19) | R14 O1 | **Trajectron++ `int_ee` on AV2 histories**: DP-SCRC cross-fitted within AV2 on its V2 (moment-matched) items is shown above δ in no evaluable cell and not in its pooled cell, on T1 and T3 histories. The nuScenes-fitted transfer is reported as H9-T, descriptive |
| **H10** | Secondary (named, R16 M2; E12) | MC4, MC5 | **Motion-strata ablation, M\* against B6** (B6 = M\* without the motion strata): on T1 and T3, B6 fails in at least one PD7 cell (shown above δ there, M\* not, paired difference B6 − M\* significantly positive) **and** M\*'s infeasible rate is not more than 0.03 above B6's (non-inferiority): validity gained at no operability cost |
| Q1 | Descriptive (Choice 20) | R14 O1 | **QCNet (AV2 checkpoint), re-centred** (Choice 17): the statement of H9, reported for ground-truth histories (upper bound) and for matched AB3DMOT histories publishing only tracks at or above T1's class `SF_thre` (Choice 18; the unthresholded run is a sensitivity, the released defaults a record) |

**Descriptive (reported in full, never a claim).** Form A; loop mode (collisions, front-buffer intrusions, V2_viol on PL7), with no ordering claim (section 5.8); V2 and its variants for every arm (section 5.8); RETUNED's selection and its reading (section 5.8); TTV < 4 s and `ttv_enf`, with TTV < 2 s labelled "arm-invariant by construction (R15b N3)"; A6 diagnostics and A7 sharpness; the α-sweep curve and δ′ arms with both boundary flags; A13 fallback shares; A14 duplicates; NIP; margin ratios; the B6 motion ablation in the method stage; **AB3DMOT** as a third tracker on LT3D at 2 Hz with the same items (Choice 11); T2 on LT3D (Choice 14); HOTA, AMOTA, MOTA and IDS (Choice 14); M\*J (Choice 21); H9-T, the Trajectron++ transferred calibration (Choice 19); the QCNet arm Q1 with its unthresholded and released-default AB3DMOT histories (Choices 15, 18, 20) and its city-coordinate runs kept as a record (Choices 17, 18); the AV2 Ford Fusion footprint sensitivity (section 2.5).

**Not claimed.** A closed-loop guarantee; a safety ranking from loop-mode collisions; validity in non-evaluable cells; validity along an object's true axes; anything outside the four groups; anything about AV2 train or test splits.

### 1.2 Labels of the predictor arms (decided: D16 v07 Choices 19, 20)

**H9, Trajectron++ `int_ee`: secondary, cross-fitted within AV2 (Choice 19).** Choice 6 overrides Choice 4's frozen transfer for this arm too, so one calibration rule holds for every arm on AV2; the transfer is H9-T, descriptive. H9 is a no-flag test and spends no α (section 5.5). It answers R14 O1 on data outside the predictor's training set, with deployed (tracker) histories. Conditions kept: the nuScenes predictor-arm plan (Choice 3) is frozen and run before this freeze, and the Trajectron++ AV2 item counts exist `[SLOT]`; if either is missing at the freeze, H9 is descriptive.

**QCNet: descriptive (Choice 20).** No development run exists for it; its deployed-history protocol was revised by Choices 15 and 18 (on counts only); whether QCNet's AV2 Motion Forecasting training scenarios overlap the Sensor validation logs is unchecked (stated as a limitation); its items are a different population from the K8 items. Ground-truth histories (upper bound) and the Choice 18 deployed histories are both reported.

### 1.3 H3: the trajectory-level certificate, M\*Jx (Choice 21; `60_RESULTS/k8_joint_v01/K8_JOINT_NOTE_v01.md`)

**The arm.** M\*'s per-stratum thresholds c_M\*(f, h, l0, ip) at the 4 calibrated steps, multiplied by one scalar λ_f ≥ 1 per tracker and log fold, shared by all strata and steps (steps 2.5 to 4 s keep M\*'s thresholds). The joint loss of a decision is ℓ_d(λ) = 1{max_i U_i / c_i > λ} over its relied constraints in the population; the scene loss L_s(λ) is the share of the scene's decisions with ℓ_d = 1. λ_P is the smallest grid value in {1.00, 1.01, …, 100.00} with n_P/(n_P + 1)·mean_s L_s(λ) + 1/(n_P + 1) ≤ δ, and λ_f = max over P ∈ {PD7, SD1_7, PD}. **M\*Jx** fits the base by M\*'s own rule on 3 folds and λ on the 4th (fold g = f + 1), then applies both to fold f, so the scene-level CRC theorem holds exactly (note sections 2, 3). The λ decision is made in exact rational arithmetic (E15). On AV2 the folds are the 5 folds of 30 logs of section 3.

**What it certifies.** The expected share of a new log's decisions in which some relied constraint over every track and the 4 steps is exceeded at margin λ·c·sd, **at the reference (logged) pose and the full margin**, per population, marginally.

**Development result** (nuScenes, 840 scenes, decision mode; `K8_JOINT_TABLES_v01.md`): M\*Jx's joint loss on PD7 is 0.044 [0.033, 0.056] (upper bound 0.052) on T1 and 0.046 [0.036, 0.058] (0.055) on T3; SD1_7 0.008 / 0.008; PD 0.002 / 0.004. On the joint loss only B3 (T1) and B0 and B3 (T3) are not shown above δ; M\*, B1, B4, B6 and B9 are. Form B on the joint loss is met on both trackers. Its price is large: infeasible rate 0.453 (T1) and 0.577 (T3) against M\*'s 0.114 and 0.161 (+0.339 [0.307, 0.370] and +0.415 [0.387, 0.446]).

**Caveats stated in advance (Choice 21).**
1. The point estimates sit just under δ; validity rests on the +0.03 pooled tolerance (HK1c).
2. Certification is at the reference pose and the full margin. The planner backs off on 42 to 55 % of the joint arm's decisions; the executed-margin joint exceedance (0.21 to 0.28 on development) is not certified.
3. Decision mode only; M\*J and M\*Jx were not run in loop mode.
4. The held-out joint loss varied by fold from 0.030 to 0.075 on development: the guarantee holds in expectation, not per fold.
5. The paper states the trade-off: the per-constraint certificate (M\*) keeps the planner operable, but about one decision in three breaks some margin; the trajectory-level certificate (M\*Jx) holds the joint rate near δ at roughly three times the infeasible rate.

**M\*J** (base reusing M\*'s calibration scenes; approximate guarantee) is descriptive.

---

## 2. Data

### 2.1 Logs, frames, decisions

| Item | Value | Source |
|---|---|---|
| Split | AV2 Sensor validation, 150 logs | D15 section 1; counts v01 and v02 |
| Frames | every 5th lidar sweep from sweep 0 (2 Hz), 4,806 frames; 31 to 40 per log | `AV2_DETECTOR_NOTE_v01.md`; port design section 2 |
| Decision states | 4,506 per tracker × detector run (30.04 per log) | counts v02 `runs.*.decision_states_and_pairs.decisions` |
| Scene and log | one log = one scene | port design section 2 |
| Licence | CC BY-NC-SA 4.0; derived statistics and code released, data not | D15 sections 1, 2 |

### 2.2 Detectors (Choice 5; Choice 16)

LT3D CenterPoint is primary (checkpoint 299cf3b7…; AP at 50 m: vehicle 0.875, pedestrian 0.795, bicyclist 0.543). VoxelNeXt is the second detector (8641d838…; 0.891, 0.782, 0.638; no velocity). Source: `AV2_DETECTOR_NOTE_v01.md`. The tracker arms keep the 2 Hz-stage detections; the 10 Hz QCNet run differs from them at the 2 Hz frames by a median of about 3 mm in matched boxes and AP within 0.02. Arms are paired by ground-truth identity and time; the non-determinism is a stated limitation (Choice 16).

### 2.3 Trackers

- **T1** CANMOT `paper/local/canmot/sc` and **T3** Poly-MOT `paper/baseline/poly_mot`, parameters transferred unchanged (port design section 4.4). Both run on both detectors.
- **AB3DMOT** (LT3D's), descriptive third tracker on LT3D at 2 Hz, the same items, not part of H1 (Choice 11).
- **T2** on LT3D is kept as descriptive; it is not run on VoxelNeXt (Choice 14).
- Tracking metrics: HOTA with the official av2 evaluator, beside AMOTA, MOTA and IDS (Choice 14).
- 2 Hz is the protocol. The 10 Hz sensitivity of D15 is not run `[SLOT: run or drop]`.

### 2.4 Classes and the four groups (Choice 8)

The strata and the planner use the four nuScenes groups. The mapping from AV2 categories is the written rule of the port design section 4.2, fixed before any outcome:
- car := `REGULAR_VEHICLE`;
- pedestrian := `PEDESTRIAN`;
- two-wheeler := `BICYCLIST` (with the ridden-two-wheeler rule RB-1, port design section 4.3) and `MOTORCYCLIST`;
- large := `BUS`, `ARTICULATED_BUS`, `SCHOOL_BUS`, `TRUCK`, `BOX_TRUCK`, `TRUCK_CAB`, `LARGE_VEHICLE`, `VEHICULAR_TRAILER`.

D15's three classes (car, pedestrian, cyclist) remain the headline reporting classes.

### 2.5 Items, strata, populations

- **Method-stage items** (H6 to H8): M-PLAN section 3. In-path, persistently paired (2 m gate), uncensored at k + h, separating axis, toward the ego; h = 2 s (1 s and 4 s descriptive); U = D/sd, σ_a = 0.10 m.
- **K8 items** (H1 to H5): K7 section 2 and the K8 item builder (the AV2 stage-A items were built by `k8_items_v04 --counts-only`; counts v02 `outcome_statement`).
- **Strata**: M-PLAN section 4 (group × range from the predicted ego at k + h × axis × motion state); L1 to L3.
- **Populations** (D14 section 4): PD7, SD1_7 (pair gap ≤ 5 m), PD (in-path), NIP (reported).
- **Cells**: group × axis × motion pooled over range (32) plus the pooled cell. **Evaluable**: ≥ 39 scenes from ≥ 8 logs; on AV2, ≥ 39 logs.
- **Ego footprint**: the nuScenes constants are the protocol; the Fusion footprint (about 4.9 × 1.9 m, port design section 5) is a descriptive sensitivity `[SLOT: rear-axle offset source, or drop it]`.

### 2.6 Outcome-blind boundary for building AV2 items (Choice 13)

**Allowed before the freeze:** the tracker's 2 s propagation of mean and covariance; the ego's logged poses at k and k + 4; the toward-ego normal; predicted-range strata; planner decision construction; K8 decision-mode item counts; the existence of the ground-truth `track_uuid` at the target sweep.

**Forbidden until the freeze:** any ground-truth position, velocity or box at a sweep later than k; any residual, projected error, U, exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or coverage.

**Two stages.** Stage A caches carry no later ground-truth position and serve the counts and the freeze. Stage B adds those fields by a script that is hash-bound in the frozen plan and runs only after the freeze `[SLOT: stage-B script written, tested on nuScenes, hashed]`.

### 2.7 Counts (outcome-free)

**K8 decision counts, stage A** (`60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v02.json`, created 2026-11-02 10:44 UTC by `av2_counts_v02`; item error fields NaN and never read):

| Run | Decisions | PD7 items (logs) | SD1_7 items (logs) | PD items (logs) | Evaluable cells PD7 / SD1_7 / PD |
|---|---|---|---|---|---|
| T1, LT3D | 4,506 | 205,075 (150) | 23,653 (147) | 8,406 (130) | 20 / 11 / 6 |
| T3, LT3D | 4,506 | 205,395 (150) | 23,582 (147) | 8,116 (128) | 21 / 12 / 6 |
| T1, VoxelNeXt | 4,506 | 200,809 (150) | 24,224 (148) | 9,470 (137) | 23 / 16 / 7 |
| T3, VoxelNeXt | 4,506 | 201,143 (150) | 24,093 (149) | 9,193 (139) | 21 / 13 / 7 |

PD7 by group, T1 LT3D: car 140,300 items (150 logs), pedestrian 56,599 (136), two-wheeler 1,217 (28: bicycle 828 in 18 logs, motorcycle 389 in 14), large 6,959 (106).

For comparison, nuScenes had 32 evaluable PD7 cells, 25 SD1_7 and 18 PD for M\* on T1 over 840 scenes (analysis `decide.t1.evaluable_cells`), and M\*'s power-qualified families were 28, 18 and 5 (`decide.t1.hypotheses`).

**Method-stage counts** (T1, LT3D, `AV2_TRACKER_COUNTS_v01.json`): in-path paired car items at k: < 20 m 2,928 (123 logs), 20 to 40 m 2,193 (122), ≥ 40 m 306 (59); 83.1 % of in-path records paired. Range at k, not from the predicted ego.

**QCNet items** (`30_DATA/qcnet_av2_v02/qcnet_av2_counts_v02.json`): ground-truth histories 107,756 items in 150 logs (vehicle 76,542; pedestrian 30,720; bicyclist 494); matched-AB3DMOT histories 104,010 items (74,472; 29,126; 412), of which 1,738 carry the full 50-step history against 46,829 with ground-truth histories. Every output passed the finiteness, mixture-weight and symmetry checks.

`[SLOT: remaining counts. Method-stage h = 2 s predicted-range counts for T1 and T3 on both detectors; Trajectron++ AV2 items; AB3DMOT items]`

---

## 3. The method stage on AV2: what is calibrated where (Choices 6 and 7)

**Primary: within-AV2 cross-fitting.** 5 log folds of 30 logs (seed 20261112); each log's thresholds come from the fit on the other 4 folds. This is how K8 fits M\* and its comparators on nuScenes.

**Secondary: transfer of a frozen nuScenes fit.** A new all-850-scene nuScenes fit of every arm, made before the freeze by a new versioned script with its hash recorded; `k7_fits_t*_v01.json` holds per-fold fits only and cannot serve (Choice 7) `[SLOT: transfer fit]`.

**Why** (Choice 6; S02 v03 D4, D5; P02 PM1). DP-SCRC's certificate assumes exchangeable calibration and test scenes. AV2 changes the detector, cities and sensors, so a transferred fit falls outside the theorem, and a deployed user recalibrates on their own domain. Transfer is still reported: how far a fit travels is useful evidence and reviewers will ask.

| Arm | Within AV2 (H1, H5, H6; H9 if Choice 6 governs it) | Transfer (H4, H7) |
|---|---|---|
| Method-stage M\*, B1, B2, B4 to B10, M-LS; references B3, B6c | E1-AV2: 20 repetitions of a 5-fold split of the 150 logs (seed 20261113 + r), fixed-rule (B = 2000) and refit-CV (B = 200) inference (M-PLAN section 6) | The 700-scene nuScenes train fits in `60_RESULTS/m/m_result_{canmot_sc,polymot}_v04.json` (`E2_h2s.fit_on_all_train`); two-sample refit log bootstrap, B = 1000 (M-PLAN E2) |
| K8 M\* (`Mstar_ip`), B1, B3, B4, B6, B9 | 5 log folds on the AV2 K8 items; log bootstrap B = 2000 | The all-850-scene fit (Choice 7); AV2 log bootstrap with the fit held fixed, B = 2000 (a deployed-rule estimand, stated as different from the within-AV2 one) |
| RETUNED | Cross-fitted selection on the merged α/δ′ curve over the AV2 folds, by D14 A3's pooled rule (reported as in section 5.8) | The merged-curve point chosen by the same pooled rule on all 840 nuScenes scenes `[SLOT: computed with the transfer fit]` |
| M\*Jx (H3) | Base refitted by M\*'s rule on 3 AV2 folds, λ fitted on the 4th (g = f + 1), applied to fold f; exact CRC (Choice 21) | Descriptive |
| M\*J | M\*'s base, λ on M\*'s 4 calibration folds (descriptive) | Descriptive |
| B0, Z0, α-sweep, δ′ arms, LOG | Fit-free | Fit-free |
| Trajectron++ `int_ee` | Cross-fitted on the AV2 folds (H9, Choice 19) | nuScenes val all-150 fit (H9-T, descriptive) |
| QCNet | Cross-fitted on the AV2 folds (Q1, descriptive) | None (no nuScenes counterpart) |

**Ordering.** Every transfer fit is computed and hashed before the freeze from nuScenes data only. Every within-AV2 fit is computed after the freeze by frozen code from stage-B items.

---

## 4. Comparators and arms

| Arm | Label in C1 | Source |
|---|---|---|
| **M\*** (`Mstar_ip`), per-constraint DP-SCRC | **Primary certificate** | D16 Choice 2a; K7 section 2 |
| B0, B1, B3, B4, B6, B9, RETUNED | Form B comparators; the set is never changed (Choice 12) | D14 section 6; README_K8_v02 |
| B4 | Also the Form C reference | Choice 1 |
| Z0, α-sweep, δ′ arms | Descriptive; never comparators | D14 A2, A3 |
| LOG | Loop-mode reference | D14 section 2 |
| **M\*Jx** | Secondary (H3): the trajectory-level certificate | Choices 2b, 21 |
| M\*J | Descriptive | Choice 21 |
| Joint-loss comparators for H3 | K_J = {M\*, B0, B1, B3, B4, B6, B9, RETUNED}: every per-constraint arm, judged on the joint loss by the same rule; M\*J is reported, not a comparator | K8 joint note section 7 |
| Transfer versions of every fitted arm | Secondary (H4, H7) | Choices 6, 7 |
| **Trajectron++ `int_ee`**, ECCV 2020 branch, commit ef0165a9…, 2 Hz, tracker histories (T1, T3), covariance V2 primary, V1 secondary, Σ + Σ_track sensitivity, ground-truth histories as an upper bound | Secondary (H9), within AV2; transfer H9-T descriptive | Choices 3, 4, 19 |
| Trajectron++ `int_ee_me` | Not run on AV2 (no nuScenes-format map); on nuScenes primary only if the map expansion arrives `[SLOT]` | Choice 3 |
| **QCNet** (AV2 checkpoint, code commit 55cacb41…, weights hash recorded on the pod), deployed histories from matched AB3DMOT (score floor 0.1, min_hits 3, max_age from T1's track life) publishing only tracks at or above T1's class `SF_thre`, re-centred at the ego position at t₀, V2 primary, ground-truth histories as an upper bound | Descriptive (Q1) | Choices 4, 15, 17, 18, 20; QCNet design sections 1 to 6 |
| AB3DMOT (2 Hz, LT3D) | Descriptive third tracker | Choice 11 |

---

## 5. Endpoints, modes, tests, multiplicity and GO conditions

### 5.1 Modes (D14 section 2, unchanged)

- **Decision mode** carries H1 to H5: one decision per keyframe from the logged ego's state, identical states for every arm, leash to the log, v_max = log maximum + 2 m/s, 32 accelerate-then-brake candidates and the emergency stop, object-axis half-spaces with a 0.5 m buffer every 0.25 s to 2 s, exemption rule C8, back-off ladder λ ∈ {0.75, 0.5, 0.25, 0}, recorded tracks at score ≥ 0.4, deployable covariance with σ_a = 0.10 m.
- **Loop mode**: non-reactive closed-loop replay, delays 0, 1, 2 s, references Z0 and LOG. Descriptive.

### 5.2 Endpoints (D14 section 4)

V1 per-constraint exceedance; O1 infeasible-decision rate, O2 progress ratio and mean speed, O3 back-off distribution; S1 V2_viol (decision mode), collisions and front-buffer intrusions (loop mode); S2 TTV < 4 s and `ttv_enf`; V2 and its variants against the reference 1 − (1 − δ)^{n_tracks}; C1 to C4 calibration and sharpness; the joint loss J_P for M\*Jx, M\*J and every K_J arm; method-stage cell exceedance, margins and ratios.

### 5.3 Statistics

- Unit: the log. Estimand: the log-level mean of each log's rate.
- Log bootstrap, weights shared by all arms. Seeds `[20261110, i, j]` for the K8 bootstrap (i = 0 T1, 1 T3; j = 0 LT3D within AV2, 1 LT3D transfer, 2 VoxelNeXt), `[20261111, i, j]` for the power rule, 20261112 for the K8 folds, 20261113 + r for the method-stage repetitions. Fixed now.
- Cell flag: one-sided simultaneous sup-t at 0.95 over the arm's evaluable cells; zero SE with Ê > δ flags. M\*'s sup-t quantiles must be finite (R15b N1); a comparator's non-finite quantile is recorded as q = None and its cells are judged by Ê > δ.
- Power rule and floor, unchanged: power ≥ 0.80 to flag a true 0.15 in the population's all-evaluable sup-t, beta-binomial with correlation 0.5, 200 datasets, the arm's record counts, the first 500 bootstrap weights; F_MIN = 6 on PD7 and SD1_7; on PD at least one evaluable cell and no flag in its own power-qualified family (R12b N1).
- Paired operability: per-log differences at identical decision states; percentile log-bootstrap bounds, as `k8_analyse_v03.d14_forms`.
- p-values for Holm: the smallest α at which a bound criterion holds, from the same bootstrap replicates (for "UB < x", the share of bootstrap means ≥ x).

### 5.4 Definitions and GO conditions

Per tracker t. P ∈ {PD7, SD1_7, PD}. K = {B0, B1, B3, B4, B6, B9, RETUNED}. f_{a,l} = arm a's infeasible-decision rate in log l.

```
Flag_cell(a,P,c)   := LB^{sup-t,0.95}_{a,P}(c) > δ,  or  SE = 0 and Ê_{a,P}(c) > δ
NoFlag(a,P)        := no evaluable cell of P flagged (all-evaluable family)
FamFlag(a,P)       := some cell of a's power-qualified family flagged in that family's own sup-t
NoFlag_pool(a,P)   := pooled cell of P evaluable and LB^{0.95}(pooled) ≤ δ
Floor(a,P)         := F_{a,P} ≥ 6 for P ∈ {PD7, SD1_7};  ≥ 1 evaluable cell for P = PD
HK1c(a,P)          := UB^{0.95}(pooled) ≤ δ + 0.03

Valid(a,t)         := AND over P of [ NoFlag ∧ ¬FamFlag ∧ NoFlag_pool ∧ Floor ∧ HK1c ]
                      read: "a is not shown above δ, with the floors met" (E10); never "a is at most δ"
ShownAbove(a,t)    := OR over P of [ ¬NoFlag ∨ FamFlag ∨ (pooled evaluable ∧ ¬NoFlag_pool) ∨ (pooled evaluable ∧ ¬HK1c) ]

V_t                := { c ∈ K : ¬ShownAbove(c,t) }            (Choice 9: a floor-only failure stays in)
Δ_t(c)             := mean over logs of ( f_{M*,l} − f_{c,l} )
FormB(t)           := Valid(M*,t) ∧ ∀ c ∈ V_t : UB^{1 − 0.05/|V_t|}(Δ_t(c)) < 0
FormA(t)           := Valid(M*,t) ∧ ∀ c ∈ {B0,B1,B4,B9} : UB^{1 − 0.05/4}(Δ_t(c)) < 0          (descriptive)
FormC(t)           := UB^{1 − α_C}(Δ_t(B4)) ≤ c_t ;  c_t = max(0.03, ceil(100·π_t)/100 + 0.01)
                      π_T1 = −0.084, π_T3 = −0.047  →  ceil: −0.08, −0.04; + 0.01: −0.07, −0.03  →  c_T1 = c_T3 = 0.03
                      (π = the decision-mode price, M* minus B4 infeasible rate on all decisions, K8 v03, Choice 10, E11;
                       0.03 is the rule's floor, not a measured price)

H1 (primary) := FormB(T1) ∧ FormB(T3)                LT3D, within AV2, decision mode
C1 GO        :⇔ H1.   C1 NO-GO otherwise, every failed condition named.

H2  := FormC(T1) ∧ FormC(T3)
J_P(a)        := log-level mean of the share of a's decisions with some relied constraint of population P exceeded
                  over the 4 calibrated steps and all tracks, at the reference pose and full margin (the joint loss, V2_P)
ValidJ(a,t)   := AND over P ∈ {PD7,SD1_7,PD} of [ LB^{0.95}(J_P(a)) ≤ δ  ∧  UB^{0.95}(J_P(a)) ≤ δ + 0.03 ]
                  (pooled only: a decision's union spans strata, so HK1a's per-stratum family has no analogue)
ShownAboveJ(a,t) := ¬ValidJ(a,t)               (no floor exists on the joint loss, so Choice 9 has nothing to keep)
V^J_t         := { c ∈ K_J : ¬ShownAboveJ(c,t) },   K_J = {M*, B0, B1, B3, B4, B6, B9, RETUNED}
Δ^J_t(c)      := mean over logs of ( f_{M*Jx,l} − f_{c,l} )
H3  := ∀ t ∈ {T1,T3}: ValidJ(M*Jx,t)  ∧  ∀ c ∈ V^J_t : UB^{1 − α/|V^J_t|}(Δ^J_t(c)) < 0
       (development: V^J = {B3} on T1, {B0, B3} on T3; Δ^J = −0.41 vs B3 on T1; −0.19 vs B0 and −0.29 vs B3 on T3)
H4  := H1's formula with every fitted arm from the transfer fit
H5  := H1's formula on VoxelNeXt tracks
H6a := ∀ t: M* flagged in no E1-AV2 cell, fixed-rule and refit-CV
H6b := ∀ t: ∃ E1-AV2 cell c: B4 flagged (refit-CV) ∧ M* not flagged ∧ LB^{sup-t}(Ê_B4(c) − Ê_M*(c)) > 0
H7  := ∀ t: M-stage M*_NS flagged in no E2-AV2 cell ∧ pooled E2-AV2 cell LB^{sup-t} ≤ δ
H8  := T1: ∃ r ∈ {<20, 20-40}: lateral in-path car cell r has LB > max(δ, E⁰_r) under B0
       ∧ its truth-oriented exceedance has LB > δ       (X2's FAILS rule; 95 % sup-t over the 4 decision cells)
H9  := ∀ t: Trajectron++ int_ee DP-SCRC (within AV2) shown above δ in no evaluable cell ∧ not in its pooled cell
H10 := ∀ t: [ ∃ PD7 cell c evaluable for both: Flag_cell(B6,PD7,c) ∧ ¬Flag_cell(M*,PD7,c)
                ∧ LB^{sup-t,0.95}(Ê_B6(c) − Ê_M*(c)) > 0 ]                 (M-PLAN section 7 "a baseline fails")
            ∧ UB^{1 − α_H}(Δ_t(B6)) ≤ 0.03                                   (non-inferiority; margin = Form C's floor)
Q1  := the statement of H9 for QCNet (descriptive)
```

### 5.5 Multiplicity (accepted subject to review; D16 v04)

- **H1** is an intersection-union test over trackers and conditions; inside it, Bonferroni across V_t (1 − 0.05/|V_t|).
- **No-flag validity tests are never corrected** (a correction would make them easier to pass): H6a, H7, H9, Q1 and the validity parts of H1, H3 (ValidJ), H4, H5; each population at 0.95.
- **Family S** (secondary claims that need a rejection): H2, H3 (its Form B part on the joint loss), H4, H5, H6b, H10; the worst Holm level is 0.05/6. Tested only if H1 passes; then Holm at family-wise 0.05. If H1 fails, they are reported unadjusted and labelled "supportive, not confirmatory (gate H1 not passed)". A claim's p-value is the maximum over trackers of its Bonferroni-adjusted rejection p-value (Form B parts: |V_t| times the largest per-comparator p-value, capped at 1). Its validity parts are pass/fail gates at 0.95.
- **Family P**: H8 alone at 0.05, not gated on H1.
- **Consequence of the gate.** While slot S0 stands (section 6.1), H1 is a foreknown failure on the floor, and every family-S claim, H3's Form B part included, could only be reported as supportive. Choice 21's condition "the paper headlines (b) only if (b)'s pre-registered secondary test passes" is then unreachable. The lead decides S0 with this in view.

### 5.6 The B6 rule (Choice 12) applied to the development data

Step 2 of the rule asks for a diagnosis if B6 is not shown above δ **and** more operable than M\* on T3 in the 840-scene development data. Neither holds (R16 M2): B6 is shown above δ on T3 (12 flagged PD7 cells and 2 flagged SD1_7 cells; t up to 10.7 against q ≈ 3.18), and its operability advantage is not resolved (M\* − B6 = −0.005 [−0.017, +0.005]; one-sided bound at 1 − 0.05/3 is +0.006). On T1, M\* − B6 = −0.062 [−0.081, −0.042]. No revision of M\* follows; the plan proceeds as designed and the comparator set is unchanged.

**Stated in advance (R16 M2 recommendation):** Form B on T3 is expected to turn on whether B6 is shown above δ on AV2. The mechanism is that static records dominate every group, so B6's motion-free thresholds are set by static tracks and moving classes are under-covered at 2 to 3 × δ. B6 could pass on AV2 only if motion-dependent error largely vanished there. Section 6 estimates that chance and H10 tests the ablation directly.

### 5.7 Always reported

Every arm, form, population, detector, tracker, route and mode: the K8 table (validity, operability, safety, calibration, sharpness), the trade-off table for every comparator outside V_t with its exceedance on the binding population, Form A, the method-stage tables, the predictor arms. Every validity sentence uses "not shown above δ (one-sided simultaneous test at 0.95)" and states how many cells have point estimates above δ (E10). The 12 overclaim sentences of R16 section 5 bind the write-up.

### 5.8 Reading rules for loop mode, V2 and RETUNED (E8, E9, E14)

**Loop mode (E8; R16 C1).** Descriptive only. No ordering of arms is claimed from collisions or intrusions, and T1 is never quoted without T3. On nuScenes development data, at-fault collisions with tracked agents per 1000 episodes were M\* 24.9 and 31.6 (T1, T3), B4 28.3 and 27.8, B6 24.0 and 27.4, Z0 22.4 and 20.2; no paired M\* − arm difference was resolved on either tracker. **LOG's zero holds by construction:** the artefact filter removes every collision LOG has at the same scene and delay (271 artefacts), so LOG is never reported as a reference. `at_fault` is geometric (ego moving at ≥ 0.1 m/s with a front-half overlap) and agents are non-reactive. Allowed sentence: "In closed-loop log replay with non-reactive agents, no difference in at-fault collisions between M\* and any comparator was resolved on either tracker."

**V2 (E9; R16 M1).** V2 is reported at its development level, with the dependence between constraints stated. On nuScenes, M\*'s V2 (any relied constraint over the 4 calibrated steps and all tracks exceeded) is 0.358 [0.325, 0.392] on T1 and 0.351 [0.320, 0.386] on T3; 0.40 to 0.42 with executed margins; against the track reference 1 − 0.95^{8.35} = 0.308. A decision holds on average 8.35 tracks but 30 relied records, so constraints within a decision are strongly dependent. M\*'s V2_viol is 0.0080 (T1) and 0.0087 (T3). D14 section 9's "about 0.5 with 14 tracks" is stale. The certificate is per constraint, and about one decision in three breaks some margin; that is a stated limitation, and M\*J (H3) is its pre-registered remedy.

**RETUNED (E14; R16 M4).** RETUNED is selected by D14 A3's pooled rule (pooled PD7, SD1_7 and PD ≤ δ on the training folds) but judged by Form B's cell rule, so "RETUNED is shown above δ" says little on its own. It is reported as: the arm chosen in each fold; on T1 the development selection was B0a1 in all folds, so RETUNED equalled B0 and is listed once with that note; whether any point of the B0 α/δ′ sweep passes Form B's validity rule in sample (on nuScenes T1 none did, even at α = 8; on T3 the cheapest that did was B0a0.25, infeasible rate 0.581 against M\*'s 0.161). D14 A3's phrase "M\*'s validity criterion" for the pooled rule is not used. `[SLOT: lead decides whether to add R16's RETUNED-HK1, cross-fitted on Form B's validity rule, as a descriptive arm]`

---

## 6. Power and operating characteristics

**Script and output.** `50_CODE/c1_av2/c1_power_counts_v02.py` (SHA-256 8f783935…), output `70_TESTS/c1_scratch/c1_power_counts_v02.json` (2b9a462e…), seed 20261103, 400 synthetic datasets per scheme, 812 s on one process. AV2 input: the stage-A counts v02 only (3ce8da26…). Development input: the K8 Linux replicate's decision-mode count arrays and per-decision infeasibility flags, and its v03 analysis (confirmed by R16). v01's pooled-proxy check (`c1_power_counts_v01.json`) used 10-scene numbers and is superseded for H1 and H2; its counts-only method-stage and diagnosis powers (v01 sections 6.3, 6.7) still stand.

**Method.** One synthetic AV2 dataset is 150 units, each a nuScenes development scene drawn with replacement with all its arms' per-cell counts and per-decision infeasibility flags, so arms and cells keep their real correlation. Decisions are thinned to AV2's 30.04 per log (θ = 0.787 of nuScenes' 38.17 per scene). In the layout-matched schemes, each population's cells are thinned to AV2's share of logs holding them and AV2's items per log (counts v02), capped at 1. On each dataset the coded K8 rule is applied (`k6_analyse_v02.rates` and `flag`, the HK1/HK1c logic of `k8_analyse_v03`, B = 200 log-bootstrap weights) to M\* and every Form B comparator, with Choice 9's V_t. The power-qualified family uses a normal approximation of `power_family`.
- **Validation on the full development data** (840 scenes, 68 logs, B = 500): the reimplementation reproduces the analysis's verdict for all 8 arms on both trackers, the flagged-cell counts within one cell, the family sizes within two, every infeasible rate exactly, and Forms A, B and C.
- **The approximate floor against the coded `power_family`** (200 simulated datasets) on six synthetic AV2 datasets: PD7 families 12/13, 13/11, 9/9, 10/10, 13/12, 11/11 (coded/approximate); SD1_7 2/2, 2/1 and 2/2 in the other four.

### 6.1 The SD1_7 floor fails on the AV2 counts alone

The power-qualified family depends only on record counts, so it can be computed now. From counts v02, with each cell's items spread equally over its logs (M\*'s relied records equal the arm-independent items to 99.7 % on nuScenes, K7 section 3):

| Run | PD7: evaluable, family | SD1_7: evaluable, family | PD: evaluable, family |
|---|---|---|---|
| T1, LT3D | 20, 15 | 11, **4** | 6, 2 |
| T3, LT3D | 21, 15 | 12, **4** | 6, 2 |
| T1, VoxelNeXt | 23, 15 | 16, **4** | 7, 2 |
| T3, VoxelNeXt | 21, 13 | 13, **5** | 7, 2 |

F_MIN = 6 on SD1_7, so **Valid(M\*, t) cannot hold on AV2 validation for any tracker or detector, and H1, H4 and H5 fail on the floor whatever the outcomes.** Only the four car static and straight cells (88 to 127 logs) reach power 0.80, plus pedestrian lat static on T3 VoxelNeXt (85 logs, 0.82); every other evaluable SD1_7 cell has 39 to 80 logs and power 0.29 to 0.79. A power-qualified cell needs about 82 logs or more at these family sizes. On nuScenes the same family had 18 cells over 840 scenes. The resampling agrees: M\*'s SD1_7 family has median 2 (10th percentile 1) in every scheme, and the floor fails in 100 % of datasets.

This is K6's failure mode, known before the data. Lowering F_MIN is excluded (D14 section 7). Options for the lead and the researcher, before the freeze `[SLOT S0]`:
1. Freeze as designed. H1 is then a foreknown NO-GO on the floor; the rest of the plan still runs and is reported. This spends the AV2 look on a predetermined verdict.
2. **Add AV2 Sensor train logs** (700 annotated logs exist). The next cells (pedestrian static, car lat new: 58 to 67 logs) need about 1.3 to 1.4 times their logs, so roughly 50 to 100 additional logs at the same density might bring two more cells over the bar; a stage-A counts pass on the added logs decides. Cost: a download and detector inference on RunPod (the 150 validation logs cost about $2.56 in total for two detectors). Caveat: LT3D and VoxelNeXt were trained on AV2 train, so those detections are in-sample, as nuScenes train detections were for CenterPoint; it is disclosed and analysed as a stratum.
3. Revisit the SD1_7 floor as a self-set gate (S02 D16b): a researcher decision, against D14 section 7.

### 6.2 H1 and its components (layout-matched scene draw; 400 datasets)

| Quantity | T1 | T3 |
|---|---|---|
| P(Form B), as coded with floors | 0.000 | 0.000 |
| P(Form B) without the floors (diagnostic only) | 0.82 | 0.95 |
| M\* fails HK1c (pooled upper bound > δ + 0.03, mostly PD) | 0.18 | 0.02 |
| M\* has a flagged cell or family cell | 0.00 | 0.005 |
| Comparators in V_t (not shown above δ) | B3 always; B1 22 %, B9 18 %, B0 and RETUNED 4 % | B0 and B3 always; B9 18 % |
| P(M\* beats every comparator in V_t), given V_t | 1.00 | 1.00 |
| **B6 shown above δ** | **1.00** | **1.00** |
| M\* − B4 infeasible rate (mean, SD over datasets) | −0.084, 0.017 | −0.047, 0.011 |
| M\* − B6 infeasible rate | −0.062, 0.019 | −0.005, 0.009 |

**P(H1) = 0.000** in every scheme (floors). Without the floors, P(H1) would be 0.79 (layout-matched), 0.75 (nuScenes layout at 150 units) and 0.62 (log-block draw, which keeps nuScenes' within-log correlation and is pessimistic). The T1 loss without floors comes from HK1c on PD; PD is under-represented in the layout-matched synthetic data (median 2 evaluable PD cells against AV2's 6), so this figure is pessimistic.

### 6.3 The B6 risk on T3

On the development effect sizes, B6 is shown above δ in 100 % of synthetic AV2 datasets on both trackers, because its flagged PD7 cells carry t up to 10.7 on nuScenes (R16 M2). The risk named in E12 arises only if AV2's motion-dependent error is smaller. A stress test scales B6's per-cell excess over M\* by κ:

| κ (B6 excess kept) | P(B6 not shown above δ), T3 | P(M\* beats B6 \| B6 in V_t), T3 | P(Form B on T3), no floors | P(H1), no floors |
|---|---|---|---|---|
| 1 (development) | 0.00 | none | 0.95 | 0.79 |
| 0.5 | 0.45 | 0.05 | 0.50 | 0.41 |
| 0.25 | 0.90 | 0.05 | 0.10 | 0.07 |

So P(Form B fails on T3) tracks P(B6 not shown above δ) almost one for one, as R16 predicted: once B6 is in V_t, M\* beats it in only 5 % of datasets (M\* − B6 = −0.005, SD 0.009). On T1 the margin is large (M\* beats B6 in 95 % of those datasets).

### 6.4 Secondary claims

- **H2 (Form C, c = 0.03):** shown in 100 % of datasets on both trackers, at 0.05 and at the worst Holm level 0.01.
- **H10 (motion-strata ablation):** 0.998 (layout-matched), 1.00 (nuScenes layout), 0.96 (log-block); 0.98 at the worst Holm level. Under the stress it falls to 0.16 (κ = 0.5) and 0.00 (κ = 0.25): H10 and the T3 part of H1 rise and fall together.
- **H6 to H9:** v01 sections 6.3 and 6.7 (counts-only component power) still apply; the method-stage h = 2 s counts are a slot.

### 6.5 Limits of this check

The development errors are nuScenes': the check cannot know AV2's error structure, only its layout. Cells richer on AV2 than on nuScenes are capped (q or r above 1 in 10 to 19 of 32 cells per population), which understates AV2's cells and is pessimistic for evaluability and the floors in the resampling (6.1 is computed from AV2's own counts). Paired thinning of records ignores the nesting of SD1_7 and PD in PD7. The floor uses an approximation, checked against the coded rule above.

### 6.6 H3 (M\*Jx) from the development numbers

- **Joint validity.** On nuScenes, M\*Jx's PD7 joint loss is 0.044 (T1) and 0.046 (T3), upper bounds 0.052 and 0.055, against the HK1c tolerance δ + 0.03 = 0.08; SD1_7 and PD are near 0.01. With 150 AV2 logs of 30 decisions, the pooled joint rate has a two-sided 95 % half-width of 0.010 to 0.020 (v01 section 6.5, intra-log correlation 0.05 to 0.30). At a true rate of 0.05 the pooled test is passed in 0.96, 0.97 and 0.86 of datasets; at 0.08 it fails in 1.00, 0.97 and 0.92 (`c1_power_counts_v01.json`, `mstarj_precision`).
- **Fold size changes M\*Jx on AV2.** Its λ is fitted on one fold. On nuScenes that fold held 160 to 179 scenes, so the CRC condition allowed a calibration-fold joint loss up to about (0.05 − 1/166)·166/165 ≈ 0.044. On AV2 a fold holds 30 logs: 1/31 = 0.032 is spent on the finite-sample term, and the calibration-fold loss must be at most (0.05 − 1/31)·31/30 ≈ 0.018. λ will therefore be larger than on nuScenes (3.06 to 4.62), the true joint rate well below δ, and the joint validity test easier to pass.
- **Form B on the joint loss.** The price rises with λ. On nuScenes M\*Jx beat its joint-valid comparators by wide margins (−0.41 against B3 on T1; −0.19 against B0 and −0.29 against B3 on T3). On T3, B0's infeasible rate (0.764) is the binding comparison; a larger λ on AV2 narrows it. The size of that effect needs the per-decision ratios R_d = max_i U_i / c_i of the development items, which this counts-only check does not read `[SLOT S2: OC of M\*Jx's λ and price at 30-log folds, from the nuScenes items, before the freeze]`.
- **Gate.** H3's Form B part is in family S and gated on H1; see section 5.5's consequence of the gate.

### 6.7 Scaling scenario for slot S0 (`c1_power_counts_v03.py`, SHA-256 38fdb281…; `70_TESTS/c1_scratch/c1_power_scaling_v03.json`, ad5f9bd9…)

**Question.** If the external set held k × 150 logs with AV2 validation's per-log composition, would the floors hold, and what would P(H1) be?

**Method.** Part A (counts only): k × 150 logs resampled with replacement from AV2 validation; the logs holding each cell are Binomial(k·150, L_c/150) with items per log unchanged, one draw shared by T1 and T3; the floor rule as in 6.1; 4,000 replicates. Part B (development effect sizes): v02's resampling at k × 150 units, 100 datasets per variant: plug-in (as v02); M\* capped (M\*'s exceedances thinned to δ in its cells whose 840-scene estimate exceeds δ: 9, 11 and 10 cells of PD7, SD1_7 and PD on T1; 11, 7 and 10 on T3); and B6's excess halved (κ = 0.5). P(H1) is reported as P(floors met, Part A) × P(H1 without floors, Part B); Part B's own floor is pessimistic (6.5).

| k (logs) | SD1_7 family, median T1/T3 (P ≥ 6) | PD7 family | PD family | P(H1) plug-in [M\* capped] | P(B6 passes on T3): κ = 1 / κ = 0.5 | H2 / H10 |
|---|---|---|---|---|---|---|
| 1 (150) | 4 / 4 (0.00) | 15 | 2 | 0.00 | 0.00 / 0.45 | 1.00 / 1.00 |
| 2 (300) | 8 / 8 (1.00) | 19 | 6 | 0.87 [0.92] | 0.00 / 0.10 | 1.00 / 1.00 |
| 2.5 (375) | 11 / 11 (1.00) | 20 | 6 | 0.94 [0.99] | 0.00 / 0.02 | 1.00 / 1.00 |
| 3 (450) | 15 / 14 (1.00) | 22 | 7 | 0.90 [0.99] | 0.00 / 0.00 | 1.00 / 1.00 |
| 3.33 (500) | 16 / 16 (1.00) | 22 | 7 | 0.88 [0.97] | 0.00 / 0.00 | 1.00 / 1.00 |
| 4.67 (700) | 16 / 16 (1.00) | 23 | 7 | 0.71 [0.95] | 0.00 / 0.00 | 1.00 / 1.00 |

(k = 1 is v02's result. Families are LT3D; PD7 and PD medians are equal on T1 and T3.)

**Reading.**
- The smallest k at which P(SD1_7 family ≥ 6) ≥ 0.95 on both LT3D trackers is **1.75 (about 263 logs, 113 more than validation)**; 1.5 on VoxelNeXt. At k = 1.5 the LT3D probability is 0.49 (T1) and 0.93 (T3).
- With the floors met, P(H1) is 0.87 to 0.94 for k = 2 to 3.33 at the development effect sizes.
- P(H1) falls at k = 4.67 (0.71) because M\*'s own cells start to be flagged on T3 (cell 0.18, family 0.23 of datasets): the plug-in treats M\*'s nuScenes point estimates above δ as true rates, and 700 independent logs resolve them. With those cells capped at δ, P(H1) stays 0.95. So a larger set is a sharper test of M\*, not only a way past the floor.
- B6 is shown above δ on T3 in every dataset at the development excess; with its excess halved it passes in 10 % of datasets at k = 2 and in none from k = 3.
- Limits: the added logs are assumed to resemble validation; AV2 train detections would be in-sample for both detectors (6.1 option 2). Part B used 100 datasets per cell of the table (Monte Carlo SE up to 0.05).

---

## 7. Analysis code, hash binding and outputs

**Existing, bound by SHA-256 at the freeze:**
- AV2 pipeline: `50_CODE/av2/` (feather reader, common, tracker input, ground-truth prep, tracker runner, counts v01 and v02 scripts, horizon prep, the nuScenes horizon test); the AV2 port design v02 (section 12, stage A); the stage-A caches `30_DATA/av2_cache_stageA_v01/` and items `items_k8_v04_av2_stageA_{t1,t3}_{lt3d,voxelnext}.npz` (hashes d9ebaa80…, bfe05c43…, 64962cad…, b65fb9c7…, from counts v02); the HOTA evaluator installation (Choice 14).
- Method stage: `50_CODE/m/m_lib_v04.py`, `m_data_v04.py`, `50_CODE/x1/x1_lib_v03.py`, the T1/T3 propagation code, CANMOT and Poly-MOT at 515d0792….
- K8: `k8_sim_v02.py`, the item builder used for stage A (`k8_items_v04`), `k8_analyse_v03.py`, `k6_sim_v02.py`, `k6_analyse_v02.py`, `k7_fit_v01.py`.
- Predictors: Trajectron++ at ef0165a9… with its weights; QCNet at 55cacb41… with the weights hash recorded on the pod; `30_DATA/qcnet_av2_v02/` outputs and `SHA256SUMS.txt`.
- Inputs: detector checkpoints, detection dumps, data manifests, tracker exports, counts v01 and v02, the M-stage nuScenes results, the transfer fit, the K8 v03 analysis of the run of record.
- The power checks: `50_CODE/c1_av2/c1_power_counts_v01.py`, `c1_power_counts_v02.py` and their outputs.
- Environment: `50_CODE/env/canmot310` (Python 3.10, NumPy 1.26.4, SciPy 1.15.3).

**New, to be written and tested on nuScenes development scenes and synthetic data before the freeze** `[SLOT]`: the stage-B builder (Choice 13); the within-AV2 fitter and the transfer fitter (Choice 7); the AV2 K8 runner with a `--prereg` path and the end-of-run hash guard; the method-stage E1-AV2/E2-AV2 runner; the M\*J module; the Trajectron++ and QCNet audit-item joins; `c1_analyse_v01.py` (k8_analyse_v03 plus the AV2 binding, Choice 9's V_t, H1 to H10, gatekeeping and Holm, the decision file); the OC of the coded rule on the final code; `c1_freeze_v01.py` (refuses any `[SLOT`, writes the hash block, the `.sha256` sidecar and a new `40_PROTOCOL/C1_PLAN_HASH_LOG.txt`); `run_c1_main_v01.sh`.

**Code requirements for `c1_analyse_v01.py`, each with a test, filled before the freeze** `[SLOT: implemented and tested]`:
1. **Choice 9 (E13; R16 M5).** `k8_analyse_v03.d14_forms` drops every comparator for which `form_valid` is false, floors included, and lowers the Bonferroni count. The AV2 analysis must keep a comparator that fails only a floor in V_t, log which comparators are in V_t only by Choice 9, and count them in |V_t|. Test: a synthetic comparator that fails only the SD1_7 floor stays in V_t, raises |V_t| and must be beaten; one with a flagged cell is removed. (On nuScenes no comparator fails only a floor, but B3's T3 SD1_7 family sits exactly at 6.)
1b. **Exact CRC decisions (E15, `90_DECISIONS/ERRATA_K8_v02.md`).** At an exact tie, where the CRC bound n/(n+1)·mean L + 1/(n+1) equals δ in rational arithmetic, a floating-point sum is decided by the scene order (nuScenes T3, fold 4, h2s, one L0 cell: one grid step more conservative in K7's order than in sorted order). Every CRC accept/reject decision in the AV2 fits (within AV2 and transfer), the method stage and the analysis is decided in exact rational arithmetic (each scene loss as an exact fraction of item counts; Python `fractions.Fraction`), as `k8_joint_fit_v02.py` does for λ. If a module cannot, it fixes and states the scene order (logs sorted by log id) and reports every cell whose decision is within one float ulp of δ. Test: a constructed cell whose bound equals 1/20 exactly gives the same threshold under every permutation of its scenes, and equals the exact-arithmetic answer; the nuScenes T3 fold 4 h2s cell reproduces the exact-arithmetic threshold.
2. **c as a parameter (R16 m1).** Form C's bound is read from this plan (c_T1, c_T3), not hard-coded. Test: c = 0.04 changes the verdict on a synthetic case.
3. **H10.** The ablation rule of section 5.4, with its test on a synthetic B6 flagged in one cell where M\* is not.
4. **Power-family seeds reported (R16 m5).** The power rule is seed-sensitive near 6; every family size is reported with its seed. `[SLOT: lead decides whether the confirmatory run uses more than 200 power replications; more replications reduce Monte Carlo noise and do not change the rule]`

**Binding rules.** Each runner refuses to start unless the plan hash, every bound file, the inputs and the environment match; each run record re-hashes at the end; the analysis refuses records whose hashes differ.

**Outputs.** `60_RESULTS/c1_av2/`: run records and shards per tracker × detector × route × mode; method-stage results; predictor results; `c1_analysis_v01.json` and CSVs stamped "C1 CONFIRMATORY: AV2 validation"; `c1_decision_v01.json` (H1 to H9 and Q1, the C1 verdict, `failed_conditions`, the Holm table, the gate status). Deviations: `90_DECISIONS/D17_C1_DEVIATION_LOG_v01.md` (new, after the freeze).

---

## 8. Deviation policy and failure

**After the freeze nothing in this file changes.** Deviations go to the D17 log with their reason; the frozen analysis is reported beside any deviating one.

**Allowed without a new plan:** a technical fix that changes no statistic, threshold, population, arm, seed, fold, detector, tracker or data selection. It is logged, reviewed and shown to reproduce the frozen code's outputs where both run.

**Never allowed:** re-running with other seeds, folds, thresholds, floors, populations, comparator sets, detectors, frame rates or logs; promoting a secondary or descriptive result; demoting a failed primary; adding AV2 data after any outcome is seen.

**If H1 fails (C1 NO-GO).**
1. Reported as NO-GO with every failed condition, never as support.
2. A pre-specified diagnosis: which condition failed (M\* shown above δ in a cell, a family or a pooled cell; a floor; HK1c; or a comparator in V_t not beaten), per tracker; within AV2 against transfer; LT3D against VoxelNeXt; A13 fallback shares; A6 diagnostics; margins by stratum; whether the failing comparator was in V_t only by Choice 9.
3. No re-run for a better answer. A method change suggested by the diagnosis is new work, developed openly and confirmed on new data under a new plan.
4. "Not shown above δ, operability not shown" if Valid(M\*, t) holds on both trackers and part (ii) fails; "floor not met" if M\* is shown above δ nowhere but a floor fails (K6's wording).

**After the run:** an independent results review re-derives H1 and the K8 tables with separate code.

---

## 9. Open slots

| # | Slot | Needed from | Blocks |
|---|---|---|---|
| S0 | **M\*'s SD1_7 floor cannot be met on AV2 validation (section 6.1).** The scaling scenario (6.7) puts the threshold at about 263 logs (k = 1.75); P(H1) is 0.87 to 0.94 for 300 to 500 logs. The researcher chooses before the freeze; lowering F_MIN is excluded by D14 section 7 | Lead, researcher | H1 |
| S1 | The decision-mode numbers on the Windows run of record (PLATFORM_CHECK_v02); loop numbers re-checked before any is quoted (R16 m7) | Run of record | Sections 0, 5.8 |
| S1b | Choice 9 (E13), exact-arithmetic CRC decisions (E15), c as a parameter, H10 and seed reporting implemented in the AV2 fits and analysis with tests (section 7) | Me | H1, H2, H10, every fit |
| S1c | RETUNED-HK1 as a descriptive arm (R16 M4); the number of power replications (R16 m5) | Lead | Descriptive; floors |
| S2 | M\*Jx at AV2 fold sizes: its λ is fitted on one fold of 30 logs, so the finite-sample term 1/31 = 0.032 uses most of δ (section 6.6). The lead decides whether Choice 21's 3 + 1 split stands on AV2; an OC of M\*Jx's price at these sizes is run before the freeze | Lead; me | H3 |
| S3 | Remaining counts: method-stage h = 2 s predicted-range counts; Trajectron++ AV2 items; AB3DMOT items | Port and predictor runs | H6 to H9 OC |
| S4 | The all-850-scene transfer fit and RETUNED's transfer point (Choice 7) | Me, nuScenes only | H4 |
| S5 | `int_ee_me`: the nuScenes map expansion v1.3 | Researcher | H9 model |
| S6 | Trajectron++: the nuScenes predictor-arm plan frozen and run, and its AV2 item counts (H9's conditions, section 1.2) | Me | H9 |
| S7 | QCNet: the training-overlap check, or the stated limitation | Me | Q1 |
| S8 | Stage-B builder (Choice 13) and the new code of section 7 | Me | Freeze |
| S9 | OC of the coded rule on the final code and final counts | Me | Freeze |
| S10 | Pre-freeze adversarial review, including the multiplicity scheme | Reviewer | Freeze |
| S11 | 10 Hz sensitivity: run or drop | Lead | Descriptive |
| S12 | Fusion rear-axle offset source, or drop the footprint sensitivity | Me | Descriptive |
| S13 | The predicted H1 risks of section 6 (the floor of S0; HK1c on PD for T1; B6 on T3 under attenuation) | Lead | H1 |

---

## 10. What was seen before the freeze (to be completed at the freeze)

1. **nuScenes:** every K6 output; the K7 and K8 development checks; the full K8 840-scene exploratory analysis (Linux replicate; the run of record when it ends) and its independent review R16 with errata E8 to E15. Development evidence by design.
2. **AV2:** detector AP; the port design and its probes; counts v01 and v02 (stage A); QCNet counts and integrity checks; the QCNet design. Tracker HOTA/AMOTA exist under `60_RESULTS/av2_trk/`; they were not read for this draft.
3. **Not seen by anyone, to the author's knowledge:** any AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error. The attestation is completed and timestamped at the freeze.

---

## Frozen files

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END
