# C1 pre-registration v05 (DRAFT): the external confirmation on Argoverse 2 (4 Nov 2026)

**Status.** Draft. Not reviewed, not frozen. v01 to v04 are kept unchanged. This version consolidates v04 (whose section 11 overrode earlier sections) into one text and applies `90_DECISIONS/D16_DELEGATED_CHOICES_v16.md` (Choices 1 to 37), `90_DECISIONS/D18_S0_SAMPLE_SIZE_DECISION_v03.md` and `50_CODE/c1_av2/README_C1_CODE_v05.md` (SHA-256 cbeb96b4…). The numbers that need the own detector are left as marked slots. `c1_freeze_v03` refuses this file while any slot is open (its slot test is the regex of `c1_guard_v02.SLOT`).

## Open slots (every one blocks the freeze)

| # | Slot | Filled from | When | Where used |
|---|---|---|---|---|
| S20a | Stage-A counts of the 375 logs, own detector, T1 and T3: K8 decision counts (PD7, SD1_7, PD per cell and log), method-stage in-path counts, and H9's PD × history-length counts | `av2_counts` on the stage-A caches of the 375 logs (outcome-free, Choice 13) | after the detector run (about 05:00 EST, 5 Nov) | sections 3.6, 7 |
| S20b | Detector AP of the own CenterPoint on the 225 held-out train logs and on the 150 validation logs, beside the public checkpoint's validation AP; the final training iteration count | official av2 evaluator; training log | after the detector run | section 3.2 |
| S20c | H9's label by the Choice 23 rule (secondary if its power-qualified family has at least 6 cells on the S20a counts, else descriptive) | S20a | after S20a | sections 2, 6.4 |
| S21 | E⁰ for the two H8 cells (`H8_E0_primary`) and the hashes of its inputs (`inputs_sha256`, copied into the analysis config as `e0.inputs_sha256`) | `c1_e0_v02 --mode c1 --seed 20261114 --stageA-manifests …` on the stage-A fields of the 375 logs, T1 | after the stage-A caches exist, before the freeze | section 6.3 (H8) |
| S22 | Power and operating characteristics on the real counts: the floors, P(H1), P(B6 passes on T3), H9's floor, and M\*Jx's λ and price at 75-log folds | the power tools on S20a, with the development effect sizes | after S20a | section 7 |

The slot markers in the text are:
- `[SLOT: S20a stage-A counts of the 375 logs, T1 and T3, own detector]`
- `[SLOT: S20b detector AP on the 225 held-out and 150 validation logs, and the final iteration count]`
- `[SLOT: S20c H9 label by the Choice 23 rule]`
- `[SLOT: S21 H8_E0_primary for car|<20|lat and car|20-40|lat, and e0 inputs_sha256]`
- `[SLOT: S22 power on the real counts]`

**Process items before the freeze (not plan text):** the independent code check R17c (running); the pre-freeze adversarial review of this plan; the analysis config (c, levels, seeds, replications, the `e0` entry) and the folds, split, transfer-fit and stage-A manifest files, all bound by `c1_freeze_v03`.

---

## 0. What C1 is, and what kind of evidence

**Role.** One frozen plan for the method stage and the closed loop on external data (D13 Phase 4); the external run is "the same study" as K8 (D14 section 1).

**Development evidence.** K6 was a pre-registered NO-GO (power floor on T3). K7 was never frozen. K8 on the 840 nuScenes scenes is exploratory; its numbers below are from the Linux replicate and its v03 analysis, confirmed by the independent review R16 (`70_TESTS/R16_K8_RESULTS_REVIEW_v01.md`; errata E8 to E16). Decision mode: infeasible-decision rate T1 M\* 0.114, B4 0.198, B6 0.176; T3 M\* 0.161, B4 0.208, B6 0.167. Comparators not shown above δ: B3 on T1; B0 and B3 on T3. B4 and B6 are shown above δ on both trackers. Forms A, B and C are met on both trackers. On T3, Form B turns on B6: M\* − B6 = −0.005 [−0.017, +0.005] (E12).

**What "valid" means (E10).** "Not shown above δ" by a one-sided simultaneous test at 0.95, never "at most δ". M\*'s point estimate exceeds δ in 9 of 32 PD7 cells on T1 and 11 on T3 on development data, none near a flag.

**What the primary test adds (Choice 6).** With within-AV2 cross-fitting, M\*'s pooled cells are close to guaranteed not to be shown above δ. The test adds: no stratum shown above δ in small strata through the fallback, under the planner's relied-on selection; the operability price on new data; the ranking against every comparator not shown above δ; and the premise's replication (H8).

**What a design choice may use (D16 Rule 0).** The literature; nuScenes development results; AV2 detector AP, tracker metrics and counts. No AV2 outcome.

**One-shot commitment.** The 375-log AV2 set is used once for the claim family "validity and operability of DP-SCRC in the planner". A NO-GO leads to diagnosis and new work on new data, never to a re-run (section 9).

**Outcome-blind attestation for this draft.** No code was run on AV2 data for v05, and no AV2 file was opened. The AV2 facts used are those already in v01 to v04 (detector AP of the public checkpoints; counts v01 and v02 of the 150 validation logs; QCNet counts) and the decision files above.

---

## 1. Data and sets

### 1.1 The confirmation set (D18 v02 and v03, option A)

- **Split.** The 700 AV2 Sensor train log ids, sorted, permuted with NumPy `default_rng(20261102)`; the first 225 are held out, the other 475 train the detector. Split file `50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json` (3771664f…), city composition in `AV2_TRAIN_SPLIT_v01_CITIES.json`; bound at the freeze as role `split`.
- **Detector.** Our own CenterPoint from LT3D's code (commit e33189aa…) with the public checkpoint's configuration (`centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2`), trained from scratch on the 475 logs at every 5th sweep, batch 4, learning rate 5e-5, CBGS sampler, cyclic schedule over the iterations that fit the cap (`50_CODE/owndet/OWN_DETECTOR_DESIGN_ADDENDUM_A_v01.md`, `_B_v01.md`: 2 CBGS epochs if the projected total stays within $34, otherwise the largest count of at least 50,500 iterations). **No checkpoint or setting is selected on any of the 375 confirmation logs.**
- **Confirmation set.** The own detector on the 225 held-out train logs plus the 150 validation logs, every 5th sweep: **375 logs, all unseen by the detector**. T1 (CANMOT `paper/local/canmot/sc`) and T3 (Poly-MOT `paper/baseline/poly_mot`) run on its detections with their nuScenes parameters, re-tuned on nothing.
- **Training data are not confirmation data.** The 475 training logs' annotations train the detector only.

### 1.2 Detector AP (reported, never gated)

`[SLOT: S20b detector AP on the 225 held-out and 150 validation logs, and the final iteration count]`

Reported per part (held-out train, validation) with the official av2 evaluator (50 m, ROI-filtered, mapped classes and the 26-class average), beside the public checkpoint's validation AP: regular vehicle 0.875, pedestrian 0.795, bicyclist 0.543, average 0.469 (`60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md`). A weaker detector is disclosed, not hidden: the study tests calibration given a deployed detector (D18 v03).

### 1.3 Descriptive data on the 150 validation logs

- **H1-P**: the public LT3D checkpoint (299cf3b7…) on the 150 validation logs. Descriptive: its SD1_7 floor fails at 150 logs (power-qualified family 4, counts v02).
- **H5**: the public VoxelNeXt checkpoint (8641d838…) on the same logs. Descriptive: its checkpoint saw all 700 train logs, so it can only run on validation, where the floor fails.
- **Q1 (QCNet)**: on the 150 validation logs with the public detections, descriptive (Choice 20).

### 1.4 Classes, groups, items, populations

- **Four groups** (Choice 8): car := `REGULAR_VEHICLE`; pedestrian := `PEDESTRIAN`; two-wheeler := `BICYCLIST` (ridden-two-wheeler rule RB-1) and `MOTORCYCLIST`; large := bus, truck and trailer categories (port design section 4.2).
- **K8 items** (H1 to H4, H10): enforced (track, check time) pairs at decision states, considered tracks within 60 m and not behind, every separating axis at the reference pose (the logged pose at t_k + h, the decision mode's leash), split by the in-path flag (`k8_items_v05 --av2-stageB`).
- **Method-stage items** (H6a, H6b, H7, H8): M-PLAN section 3 (in-path, persistently paired, uncensored at k + h, separating axis, toward the ego), h = 2 s.
- **Strata**: group × range (from the sensor's CTRV-predicted ego) × axis × motion state; L1 to L3; n_min = 19 units.
- **Populations** (D14 section 4): PD7, SD1_7 (gap ≤ 5 m), PD (in-path), NIP (reported).
- **Cells**: group × axis × motion pooled over range (32) plus the pooled cell; **evaluable** at ≥ 39 logs (on AV2 a log is a scene).

### 1.5 The outcome-blind boundary (Choices 13 and 34)

- **Allowed before the freeze:** the tracker's propagation of its mean and covariance; the ego's logged poses; the toward-ego normal; predicted-range strata; planner decision construction; K8 decision-mode item counts; existence of the ground-truth `track_uuid` at the target sweep; E⁰ from stage-A fields only (Choice 31).
- **Forbidden until the freeze:** any ground-truth position, velocity or box at a sweep later than k; any residual, projected error, U, exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or coverage.
- **Two stages.** Stage-A caches carry no later ground-truth position; they serve the counts, E⁰ and the freeze. Stage B (`av2_cache_stageB_v03`, entry `stageB`) adds those fields after the freeze, only for a plan whose hash is in `40_PROTOCOL/C1_PLAN_HASH_LOG.txt`.
- **Enforced by code** (`c1_guard_v02`): one hard-coded hash log per plan, no command-line override on AV2; every module that can read AV2 data is guarded; a dataset tag must agree with the unit names; run-time hash checks of the entry point and every loaded project module.

### 1.6 Counts

`[SLOT: S20a stage-A counts of the 375 logs, T1 and T3, own detector]`

To be reported: decisions, items per population, per cell and per log; evaluable cells; power-qualified families; method-stage in-path cells; H9's PD × history-length cells; per-fold source and city composition. The counts of the 150 validation logs under the public detectors (counts v01, v02) stay as reported in v02 to v04; they are not the H1 layout.

---

## 2. Claims under test

δ = 0.05 throughout. Formulas in section 6.3. "Secondary" claims are pre-registered; "descriptive" ones are reported in full and never claimed.

| ID | Label | Data | Statement |
|---|---|---|---|
| **H1** | **Primary** | 375 logs, own detector, T1 and T3 | **Form B**: no cell, family cell or pooled cell of M\* is shown above δ on PD7, SD1_7 or PD, the floors and HK1c hold, and M\* is less often infeasible than every comparator not shown above δ (Choice 9). Expected to turn on B6 on T3 (E12) |
| H2 | Secondary | as H1 | **Form C**: the decision-mode price, M\* − B4 infeasible rate, is ≤ c_t on T1 and T3; c_T1 = c_T3 = 0.03, the floor of the c rule (development prices −0.084 and −0.047; E11) |
| H3 | Secondary | as H1 | **M\*Jx**, the trajectory-level certificate (Choice 21): its joint loss is not shown above δ on PD7, SD1_7 and PD, and Form B holds on the joint loss |
| H4 | Secondary | as H1, transfer fits | **Transfer in the loop**: H1's formula with every fitted arm from the all-850-scene nuScenes fit (Choices 6, 7) |
| H6a | Secondary | 375 logs | **Method stage within AV2 (E1-AV2)**: M\* shown above δ in no E1-AV2 cell, fixed-rule and refit-CV, T1 and T3 |
| H6b | Secondary | 375 logs | **Practitioner failure**: B4 fails (flagged, M\* not, paired difference positive; refit-CV) in at least one E1-AV2 cell on T1 and on T3 |
| H7 | Secondary | 375 logs | **Method stage, transfer (E2-AV2)**: the M-stage M\* fitted on the 700 nuScenes train scenes is shown above δ in no AV2 cell and not in the pooled cell, T1 and T3 |
| H8 | Secondary (family P) | 375 logs, T1 | **Diagnosis replicates**: an in-path car lateral 2 s cell (< 20 m or 20 to 40 m) FAILS under B0, and its truth-oriented exceedance also FAILS |
| H9 | Secondary, label by rule `[SLOT: S20c H9 label by the Choice 23 rule]` | 375 logs, own-detector T1 and T3 histories | **Trajectron++ `int_ee`** (Choices 23, 35, 37): DP-SCRC with history-length strata, cross-fitted on the C1 folds, is shown above δ in no cell of its validity family (the E2 cells plus the three pooled history-length cells) and not in its pooled cell, with at least 6 power-qualified cells, none shown above δ |
| H10 | Secondary | as H1 | **Motion-strata ablation, M\* against B6**: B6 fails in at least one PD7 cell where M\* does not, and M\*'s infeasible rate is at most 0.03 above B6's |

**Descriptive.** Form A; H1-P and H5 (section 1.3); the source heterogeneity check and the train-to-validation source-transfer reading (Choice 22); loop mode (section 6.6); V2 and its variants for every arm (section 6.6); RETUNED and RETUNED-HK1 (section 6.6); M\*J (Choice 21); H9-noHL (Choice 37); H9-T, the nuScenes-fitted Trajectron++ transfer (Choices 19, 23); TPPgt, Trajectron++ with ground-truth histories (upper bound); Q1, QCNet with ground-truth and deployed histories (Choices 18, 20); A6 calibration diagnostics; A7 sharpness; the α-sweep and δ′ arms; A13; A14; NIP; margin ratios; HOTA, AMOTA, MOTA and IDS.

**Not run in this plan** (outside the bound path of README v05): AB3DMOT as a third tracker on the 375 logs (Choice 11); the 10 Hz protocol; the Ford Fusion footprint sensitivity; T2 on the 375 logs.

**Not claimed.** A closed-loop guarantee; a safety ranking from loop-mode collisions; validity in non-evaluable cells; validity along an object's true axes; anything outside the four groups; anything about the AV2 test split.

---

## 3. Calibration: what is calibrated where

### 3.1 Folds (Choice 22)

- **375 logs: 5 folds of 75**, from `c1_folds_v02` (entry `c1_folds`): the 375 log ids sorted, permuted by NumPy `default_rng(20261112)`, cut into 5 consecutive blocks (`np.array_split`). The tool checks that the ids are exactly the split's 225 held-out logs plus the 150 validation logs, and records the NumPy version and a permutation probe. Not stratified by source; source is reported.
- **Why.** A uniformly random partition keeps every test log exchangeable with every calibration log, which is the certificate's assumption (P02 PM1; S02 v03 D4, D5; the transductive guarantee of P01 Thm 5 on the pooled set). Stratifying by source would add an assumption for little balance (validation share per fold 0.40 ± 0.05). Source as a stratum would split the logs again and bring back the floor problem.
- **150-log descriptive routes (H1-P, H5).** The 375-log folds restricted to the 150 validation logs (folds of about 30; the same permutation, seed 20261112).
- **Source reported** (descriptive, pre-specified): per-fold source and city composition; M\*'s pooled V1 on PD7, SD1_7 and PD and its infeasible rate by source, with a log-bootstrap interval for the difference; the source-transfer reading (fit on the 225 held-out train logs, evaluated on the 150 validation logs; route index 4).

### 3.2 Routes

| Arm | Within AV2 (primary; H1, H2, H3, H6, H8 to H10) | Transfer (H4, H7) |
|---|---|---|
| K8 M\* (`Mstar_ip`), B1, B3, B4, B6, B9 | each log's thresholds from the fit on the other 4 folds (`c1_fit_v03`, entry `c1_fit`), exact CRC | the all-850-scene nuScenes fit, `60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_{t1,t3}_v01.json` (97f4b78c…, ac4cbda2…), applied by `c1_transfer_apply_v01` |
| RETUNED | cross-fitted selection on the merged α/δ′ curve over the AV2 folds (D14 A3's pooled rule) | the nuScenes point chosen by the same rule: B0a1 (T1), B0d0.3 (T3) (`retuned_transfer_{t1,t3}.txt`); required for H4 (Choice 25) |
| M\*Jx (H3) | base refitted by M\*'s rule on 3 folds (225 logs), λ fitted on the 4th (75 logs), applied to the 5th; exact λ decision | descriptive |
| M\*J | M\*'s base, λ on its 4 calibration folds; descriptive | descriptive |
| Method-stage M\* and baselines | E1-AV2: 20 repetitions of a 5-fold split of the 375 logs (seeds 20261113 + r), exact CRC in every fit and refit | the 700-scene nuScenes train fits (M-PLAN E2), two-sample refit log bootstrap |
| Trajectron++ (H9) | DP-SCRC with history-length strata on the C1 folds (section 6.4) | H9-T: the nuScenes val fit, descriptive |
| QCNet (Q1) | DP-SCRC without history-length strata on the 150-log folds; descriptive | none |
| B0, Z0, α-sweep, δ′ arms, LOG | fit-free | fit-free |

**Exact arithmetic (E15).** Every CRC accept/reject decision (every fit, refit and λ) is decided in exact rational arithmetic (`c1_crc_exact_v01.crc_threshold_exact`).

**Ordering.** The transfer fits, the split and the folds exist and are hashed before the freeze; every within-AV2 fit is made after it, by frozen code, from stage-B items, and is checked by provenance (Choice 24).

---

## 4. Comparators and arms

| Arm | Label |
|---|---|
| **M\*** (`Mstar_ip`), per-constraint DP-SCRC | primary certificate |
| K = {B0, B1, B3, B4, B6, B9, RETUNED} | Form B comparators; never changed (Choice 12) |
| B4 | also the Form C reference |
| K_J = {M\*, B0, B1, B3, B4, B6, B9, RETUNED} | joint-loss comparators for H3 |
| M\*Jx | secondary (H3) |
| M\*J, RETUNED-HK1, Z0, α-sweep, δ′ arms, LOG | descriptive; never comparators |
| Trajectron++ `int_ee` (ECCV 2020 branch, commit ef0165a9…; tracker histories; covariance V2 primary; forward-pass seed 20261102, torch seed fixed per scene, k and node, Choice 27) | H9 (label by rule) |
| Trajectron++ noHL; H9-T; TPPgt | descriptive |
| QCNet (AV2 checkpoint, commit 55cacb41…; re-centred; deployed histories from matched AB3DMOT publishing only tracks at or above T1's `SF_thre`, ground-truth histories as an upper bound) | descriptive (Q1); no history-length stratum, because QCNet's own input history is not in the keys |

---

## 5. Modes and endpoints (D14 sections 2 and 4, unchanged)

- **Decision mode** carries H1 to H4 and H10: one decision per keyframe from the logged ego's state, identical states for every arm, leash to the log, v_max = log maximum + 2 m/s, 32 accelerate-then-brake candidates and the emergency stop, object-axis half-spaces with a 0.5 m buffer every 0.25 s to 2 s, exemption rule C8, back-off ladder λ ∈ {0.75, 0.5, 0.25, 0}, recorded tracks at score ≥ 0.4, deployable covariance with σ_a = 0.10 m.
- **Loop mode**: non-reactive closed-loop replay, delays 0, 1, 2 s; descriptive (section 6.6).
- **Endpoints**: V1 per-constraint exceedance; O1 infeasible-decision rate (O2 progress and speed, O3 back-off, descriptive); S1 V2_viol, collisions, front-buffer intrusions; S2 TTV < 4 s and `ttv_enf`, with TTV < 2 s labelled "arm-invariant by construction"; the joint loss J_P; C1 to C4 calibration and sharpness; method-stage cell exceedance and margins.

---

## 6. Statistics, GO condition and multiplicity

### 6.1 Units, bootstrap, seeds (every seed the code uses; R17 m8)

- Unit: the log. Estimand: the log-level mean of each log's rate. Log bootstrap B = 2000, weights shared by every arm (fixed outside the smoke mode of `c1_analyse_v05`).

| Use | Seed |
|---|---|
| Folds, 375 logs (and their restriction to the 150 validation logs) | 20261112 |
| K8 log bootstrap, decision mode | [20261110, i, j], i = 0 T1, 1 T3 |
| K8 power rule (floors) | [20261111, i, j] |
| Loop mode | [20261110, i, j, 1] |
| Route index j | 0 within AV2 (H1, H2, H3, H10); 1 transfer (H4); 2 VoxelNeXt on validation (H5); 3 public LT3D on validation (H1-P); 4 source transfer; 5 predictor arm (H9, H9-noHL) |
| Method stage (H6, H7) | 20261113: E1 folds 20261113 + r (r = 0 to 19), refit-CV 20261113 + 1000 + b, bootstrap generators [20261113, crc32(label)] |
| H8 bootstrap | [20261113, 8], B = 2000 |
| E⁰ (H8) | 20261114 |
| Trajectron++ forward pass | 20261102 |
| Detector split | 20261102 |

- **Cell flag**: one-sided simultaneous sup-t at 0.95 over the arm's evaluable cells; zero SE with Ê > δ flags. M\*'s sup-t quantiles must be finite; a comparator's non-finite quantile is recorded as q = None and its cells are judged by Ê > δ.
- **Power rule and floor** (unchanged): power ≥ 0.80 to flag a true 0.15 in the population's all-evaluable sup-t, beta-binomial with correlation 0.5, 200 datasets, the arm's record counts, the first 500 bootstrap weights; F_MIN = 6 on PD7 and SD1_7; on PD at least one evaluable cell and no flag in its own power-qualified family.
- **Paired operability**: per-log differences at identical decision states; percentile log-bootstrap bounds.
- **p-values for Holm**: from the same bootstrap replicates. A Form B part: |V_t| times the largest per-comparator p (the share of bootstrap means ≥ 0), capped at 1. Form C: the share of bootstrap Δ(B4) > c. H6b: per tracker, the minimum over E1-AV2 cells where M\* is not flagged of max(sup-t p of B4's flag, sup-t p of the paired difference). H10: per tracker, max(the same cell-part p for B6 on PD7, the share of bootstrap Δ(B6) > 0.03). A claim's p is the maximum over trackers.

### 6.2 Definitions

Per tracker t; P ∈ {PD7, SD1_7, PD}; f_{a,l} is arm a's infeasible-decision rate in log l.

```
Flag_cell(a,P,c)  := LB^{sup-t,0.95}_{a,P}(c) > δ,  or  SE = 0 and Ê_{a,P}(c) > δ
NoFlag(a,P)       := no evaluable cell of P flagged (all-evaluable family)
FamFlag(a,P)      := some cell of a's power-qualified family flagged in that family's own sup-t
NoFlag_pool(a,P)  := pooled cell of P evaluable and LB^{0.95}(pooled) ≤ δ
Floor(a,P)        := F_{a,P} ≥ 6 for P ∈ {PD7, SD1_7};  ≥ 1 evaluable cell for P = PD
HK1c(a,P)         := UB^{0.95}(pooled) ≤ δ + 0.03

Valid(a,t)        := AND over P of [ NoFlag ∧ ¬FamFlag ∧ NoFlag_pool ∧ Floor ∧ HK1c ]      read "not shown above δ, floors met"
ShownAbove(a,t)   := OR over P of [ ¬NoFlag ∨ FamFlag ∨ (pooled evaluable ∧ ¬NoFlag_pool) ∨ (pooled evaluable ∧ ¬HK1c) ]
V_t               := { c ∈ K : ¬ShownAbove(c,t) }               (Choice 9: a floor-only failure stays in)
Δ_t(c)            := mean over logs of ( f_{M*,l} − f_{c,l} )

FormB(t)          := Valid(M*,t) ∧ ∀ c ∈ V_t : UB^{1 − 0.05/|V_t|}(Δ_t(c)) < 0          (V_t empty: part (ii) vacuous)
FormA(t)          := Valid(M*,t) ∧ ∀ c ∈ {B0,B1,B4,B9} : UB^{1 − 0.05/4}(Δ_t(c)) < 0     (descriptive)
FormC(t)          := UB^{0.95}(Δ_t(B4)) ≤ c_t,   c_T1 = c_T3 = 0.03

J_P(a)            := log-level mean share of a's decisions with some relied constraint of P exceeded over the 4
                     calibrated steps and all tracks, at the reference pose and full margin
ValidJ(a,t)       := AND over P of [ pooled joint population evaluable (≥ 39 logs) ∧ LB^{0.95}(J_P(a)) ≤ δ ∧ UB^{0.95}(J_P(a)) ≤ δ + 0.03 ]
V^J_t             := { c ∈ K_J : ValidJ(c,t) }
```

### 6.3 Hypotheses and the GO condition (Choice 33)

```
H1 (primary) := FormB(T1) ∧ FormB(T3)        within AV2, own detector, 375 logs, decision mode
C1 GO        :⇔ H1 holds, with every input H1 needs present and provenance-valid: both trackers' within-AV2 runs,
                their fits, the folds, the split, the stage-A to stage-B chain, every comparator and every arm.
                Otherwise NO-GO, with H1's failed or missing conditions named (and nothing else).

H2  := FormC(T1) ∧ FormC(T3)
H3  := ∀ t: ValidJ(M*Jx,t) ∧ ∀ c ∈ V^J_t : UB^{1 − 0.05/|V^J_t|}(f_{M*Jx} − f_c) < 0 ; a fold whose λ does not qualify fails H3 for that tracker
H4  := H1's formula with every fitted arm from the transfer fits; RETUNED's transfer point required
H6a := ∀ t: M* flagged in no E1-AV2 cell, fixed-rule and refit-CV
H6b := ∀ t: ∃ E1-AV2 cell c: B4 flagged (refit-CV) ∧ M* not flagged ∧ LB^{sup-t}(Ê_B4(c) − Ê_M*(c)) > 0
H7  := ∀ t: M-stage M*_NS flagged in no E2-AV2 cell ∧ pooled E2-AV2 cell LB^{sup-t} ≤ δ
H8  := T1: ∃ r ∈ {<20, 20-40}: lateral in-path car cell r has LB > max(δ, E⁰_r) under B0
       ∧ its truth-oriented exceedance has LB > δ          (X2's FAILS rule; 95 % sup-t over the 4 decision cells)
H9  := ∀ t: Trajectron++ DP-SCRC (history-length strata) shown above δ in no evaluable cell of its family
       (E2 cells + the three pooled history-length cells) ∧ pooled cell not flagged ∧ ≥ 6 power-qualified cells, none flagged
H10 := ∀ t: [ ∃ PD7 cell c evaluable for both: Flag_cell(B6,PD7,c) ∧ ¬Flag_cell(M*,PD7,c) ∧ LB^{sup-t,0.95}(Ê_B6(c) − Ê_M*(c)) > 0 ]
            ∧ UB^{0.95}(Δ_t(B6)) ≤ 0.03
```

**E⁰ for H8** (Choice 31, X1's frozen definition): E⁰_r = P(U⁰ > z₀.₉₅ | kept), a plug-in with truth := m̂ over all (record, axis) candidates before the separating filter, 20 perturbation draws, σ_a = 0.10 m, computed from stage-A fields of the 375 logs (own detector, T1) before the freeze:

`[SLOT: S21 H8_E0_primary for car|<20|lat and car|20-40|lat, and e0 inputs_sha256]`

The analysis re-hashes the E⁰ inputs, recomputes E⁰ with the same code and seed, and compares bit for bit.

**What a missing or unverifiable input does (Choice 33; replaces Choice 31's rule).**
- An input H1 needs, missing or not provenance-valid: **NO-GO**, with the reason.
- An input a secondary claim needs (H2 to H10), missing or not provenance-valid: that claim is **"not tested"**, with the reason recorded in `missing_inputs`; it enters family S with p = 1 (if it is a family-S member), is never confirmed, and **never changes GO**.
- **E⁰ problems make H8 "not tested"**: a missing `e0` entry, missing input hashes, changed or unbound inputs, a recomputed value that differs, or an H8 table without the plan's `E0_plan`. None changes the verdict.
- Every claim gets one status: holds, does not hold, not tested (or descriptive). `gate_H1` equals (verdict = GO), and no claim is confirmed unless the gate holds and the claim holds.

### 6.4 H9 (Choices 23, 35, 37)

- **Population (Choice 35; corrects v04 section 11.4).** PD: the K8 relied in-path items at 2 s, **scored on the K8 tracker-planner's constraints** (the relied axis, the gap and the toward-ego normal and sign taken from the K8 items, which evaluate them at the reference pose, the logged pose at t_k + h), not recomputed from Trajectron++'s own mean. The claim is worded "along the K8 tracker-planner's constraints". The items are paired with the tracker arm item for item, joined by (log, track, k).
- **Errors.** A unit of the keys outside the folds is an error, before anything is computed; a non-finite D or variance in a used item is an error.
- **History length (Choice 37).** Each item's history length is its predictor's own input history at decision time k, read from the Trajectron++ keys (`rec_hist_stratum_trk`: contiguous tracker states up to k, written by `tpp_keys_v01`); strata {2, 3–4, ≥ 5 states}. Nothing after k is read. A used item below 2 states, or keys without the field, is an error.
- **Fit.** DP-SCRC on L0 × HL, L1 × HL, L2 × HL, L3 × HL, then L3 as the last fallback, so every item has a threshold; a cell gets its own exact-CRC threshold with at least 19 calibration units, otherwise its items fall back; cross-fitted on the C1 folds.
- **Validity family.** The E2 cells plus the three pooled history-length cells; rule as in 6.3; seeds [20261110, i, 5] and [20261111, i, 5].
- **Label by rule (Choice 23).** Secondary if its power-qualified family has at least 6 cells on the S20a counts; otherwise descriptive, before the freeze.
- **Why history length.** On the frozen nuScenes D17 run, items with only two tracker states stayed above δ after M\* (0.079, lower bound 0.062, on T1; 0.072 [0.063] on T3), offset by items with five or more (Choice 37, from R19). History length is observable at decision time, so stratifying on it is the method's own principle. It was found on development data and fixed before the freeze.
- **Descriptive companions.** H9-noHL (D17-style strata, E2 cells only); the diagnostic `noHL_on_HL_cells`; H9-T; TPPgt. **Q1 (QCNet)** has no history-length stratum, because QCNet's own input history is not in the keys.

### 6.5 Multiplicity (Choices 26 and 33)

- **H1** is an intersection-union test over trackers and conditions; inside it, Bonferroni across V_t.
- **No-flag validity tests are never corrected** (a correction would make them easier to pass): H6a, H7, H9 and the validity parts of H1, H3 and H4; each population at 0.95.
- **Family S = {H2, H3, H4, H6b, H10}, m = 5 fixed.** Tested only if H1 holds; then Holm at family-wise 0.05. A member that cannot be tested (gate failed, route absent, input missing, no p-value) enters with p = 1. A vacuous Form B part gives no p-value and enters with p = 1. A member is confirmed only if its bound-based verdict holds **and** Holm rejects at its level. If H1 fails, the members are reported unadjusted as "supportive, not confirmatory (gate H1 not passed)".
- **Family P = {H8}** at 0.05, not gated on H1.

### 6.6 Reading rules (E8, E9, E14; R16)

- **Loop mode (E8).** Descriptive only; no ordering of arms; T1 is never quoted without T3. LOG's zero holds by construction (the artefact filter removes every collision LOG has at the same scene and delay) and LOG is never a reference. Allowed sentence: "In closed-loop log replay with non-reactive agents, no difference in at-fault collisions between M\* and any comparator was resolved on either tracker."
- **V2 (E9).** Reported at its development level with the dependence stated: M\*'s V2 is 0.358 [0.325, 0.392] (T1) and 0.351 [0.320, 0.386] (T3), against the track reference 0.308; a decision holds about 8.35 tracks but 30 relied records. The per-constraint certificate leaves about one decision in three with some margin broken; M\*Jx (H3) is the pre-registered remedy.
- **RETUNED (E14).** Selected by the pooled rule, judged by the cell rule; reported with the arm chosen per fold and whether any α/δ′ point passes Form B's rule in sample. RETUNED-HK1, cross-fitted on Form B's rule, is descriptive and never in K.
- **The 12 overclaim sentences of R16 section 5 bind the write-up.**

### 6.7 H3's caveats (Choice 21)

Point estimates just under δ, validity resting on the +0.03 tolerance; certification at the reference pose and full margin, the executed-margin joint exceedance not certified; decision mode only; the held-out joint loss varied by fold (0.030 to 0.075 on development), so the guarantee holds in expectation. With λ fitted on 75 logs the CRC allows a calibration-fold joint loss of at most 0.037 (0.044 on nuScenes folds), so λ and the price will sit somewhat above development's (+0.34 on T1, +0.42 on T3).

---

## 7. Power and operating characteristics

`[SLOT: S22 power on the real counts]`

**Provisional values (scaling model; replaced by S22).** From `70_TESTS/c1_scratch/c1_power_375_v04.json` (375 logs with AV2 validation's per-log composition under the public LT3D detector; development effect sizes): SD1_7 power-qualified family 11 on both trackers, P(≥ 6) = 1.00; PD7 family 20; P(H1) 0.91 (0.97 if M\*'s development cells above δ are noise); P(B6 passes on T3) 0.000, 0.007 with B6's motion effect halved; H2 and H10 1.00; the in-path population reaches a family of 6 to 7 cells. These assume the own detector's layout matches the public detector's, which S20a checks.

The power tools `c1_power_counts_v01` to `v04` are pre-freeze tools, not part of the confirmatory path, and are not bound (README v05); their outputs are cited by hash.

---

## 8. Code, binding and run order (README_C1_CODE_v05)

### 8.1 Entry points (the roles the freeze writes into the FROZEN_ROLES block)

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v05.py` |
| `entry:c1_fit` | `c1_av2/c1_fit_v03.py` |
| `entry:c1_run` | `c1_av2/c1_run_v03.py` |
| `entry:c1_mstage` | `c1_av2/c1_mstage_v03.py` |
| `entry:c1_h8` | `c1_av2/c1_h8_v03.py` |
| `entry:c1_e0` | `c1_av2/c1_e0_v02.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v03.py` |
| `entry:c1_transfer_apply` | `c1_av2/c1_transfer_apply_v01.py` |
| `entry:c1_folds` | `c1_av2/c1_folds_v02.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v03.py` |
| `entry:stageB` | `av2/av2_cache_stageB_v03.py` |
| `entry:k8_items` | `k8/k8_items_v05.py` |
| `entry:tpp_keys` | `tpp/tpp_keys_v01.py` |
| `entry:tpp_run` | `tpp/tpp_run_v01.py` |

The other 70 bound files (modules, generators, sources, builders, tests) and the 7 superseded files are listed in README v05 with their hashes and roles. The data roles are `folds`, `split`, `transfer_fits`, `stageA_manifest`, `config` and `data:<name>`. The freeze tool is **`c1_freeze_v03`**: it fills both blocks at the end of this file, writes the `.sha256` sidecar and appends one line to `40_PROTOCOL/C1_PLAN_HASH_LOG.txt`. Both blocks must be empty in the draft.

### 8.2 Order of operations (AV2; `../env/canmot310/Scripts/python.exe -B` from `50_CODE/c1_av2`)

**Before the freeze:**
1. E⁰: `c1_e0_v02.py --mode c1 --seed 20261114 --workers <AV2 T1 x1 exports> --gt <AV2 GT> --meta <dir> --horizon <AV2 T1 h2s horizon> --stageA-manifests <the stage-A MANIFEST.json files> --out <json>`. Its `H8_E0_primary` fills S21; its `inputs_sha256` goes into the config as `e0.inputs_sha256`.
2. Freeze: `c1_freeze_v03.py --plan <C1 plan> --readme README_C1_CODE_v05.md --results-dir <60_RESULTS/c1_av2> --folds --split --transfer-fits <t1> <t3> --stageA-manifests ... --config <json> --data e0_plan=<json> <name>=<AV2 input files used by mstage/h8/e0> ... --test "<python> -B tests/test_c1_v06.py <out>" "<python> -B tests/test_c1_v07.py <out>"`.

**After the freeze, in this order:**
1. `av2_cache_stageB_v03 --frozen-plan`
2. `k8_items_v05 --av2-stageB --plan`
3. `c1_fit_v03 --plan`
4. `c1_transfer_apply_v01`
5. `c1_run_v03 --c1-plan`
6. `c1_mstage_v03 --plan --folds`
7. `c1_h8_v03 --plan --folds --e0-plan`
8. `tpp_keys_v01` and `tpp_run_v01` (pod)
9. `c1_predarm_v03 --plan`
10. `c1_analyse_v05 --c1 --plan`

None takes `--hash-log` on AV2.

### 8.3 How later artefacts are checked (Choices 24, 34, 36)

Everything made after the freeze is checked by provenance, not listed: each within-AV2 fit records its code, folds and plan hashes; each run record carries the plan and folds hashes; the H6 to H9 tables carry their entry point, every loaded module's hash, the plan, the folds and their inputs; caches must be stage B under this plan, built by `entry:stageB` from a bound stage-A manifest; items must chain to such caches through `entry:k8_items`. The analysis refuses anything whose provenance does not match. Superseded entry points refuse real input (Choice 36) and fail the role checks. The whole path was rehearsed end to end on a mock frozen plan with nuScenes stand-in data (`70_TESTS/c1_v01/rehearsal150_v05b/`); the rehearsal's verdicts are not evidence.

### 8.4 Limits of the binding (for the methods section)

- **Provenance records can be forged by hand.** They are JSON files written by bound entry points. A hand-made table with correct fields would pass the provenance check. The guard prevents accidental and command-line bypasses, not deliberate forgery; the independent results review, which re-derives the headline results from the raw arrays, is the safeguard against it.
- **The AV2 export and port builders are bound at their current hashes**, but nothing in the code verifies that these are the versions that produced the AV2 stage-A data. The stage-A manifests record a `builder_sha256`, which is compared with the bound builders at the freeze.
- **The scene-to-log map** (`scene.json`) is hashed and recorded, but it is not required to be a stage-A input.
- **One generator is not re-run at the freeze** (`av2/gen/make_k8_items_v04_v01.py` writes its target on import); `k8_items_v04` is bound as a builder and as the source of `make_k8_items_v05`.

---

## 9. Deviation policy and failure

- **After the freeze nothing in this file changes.** Deviations go to `90_DECISIONS/D19_C1_DEVIATION_LOG_v01.md` (new, after the freeze), with their reason; the frozen analysis is reported beside any deviating one.
- **Allowed without a new plan:** a technical fix that changes no statistic, threshold, population, arm, seed, fold, detector, tracker or data selection, logged, reviewed and shown to reproduce the frozen code's outputs where both run. Any code change is a new versioned file; bound files are never edited.
- **Never allowed:** re-running with other seeds, folds, thresholds, floors, populations, comparator sets, detectors or logs; selecting a detector checkpoint on the confirmation logs; promoting a secondary or descriptive result; demoting a failed primary; adding AV2 data after any outcome is seen.
- **If H1 fails (NO-GO):** reported as NO-GO with H1's failed or missing conditions; a pre-specified diagnosis (M\* shown above δ in a cell, family or pooled cell; a floor; HK1c; a comparator in V_t not beaten; per tracker; within against transfer; by source; A13 fallback shares; A6 diagnostics; margins by stratum); no re-run; any method change is new work on new data. Wording: "not shown above δ, operability not shown" when Valid(M\*, t) holds on both trackers and part (ii) fails; "floor not met" when M\* is shown above δ nowhere but a floor fails.
- **After the run:** an independent results review re-derives H1 and the K8 tables with separate code.

---

## 10. What was seen before the freeze (completed at the freeze)

1. **nuScenes:** every K6 output; the K7 and K8 development checks; the K8 840-scene exploratory analysis and its review R16; the M\*J and M\*Jx development runs; the frozen D17 Trajectron++ run and its review R19 (development evidence).
2. **AV2:** public-detector AP on the 150 validation logs; counts v01 and v02 of the 150 validation logs; QCNet counts and integrity checks; the own detector's training logs and pilot; S20a, S20b and S21 when filled. No stage-B data.
3. **Not seen by anyone, to the author's knowledge:** any AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error. Attested and timestamped at the freeze.

---

## 11. Changes from v04

- **Consolidated:** v04's section 11 is folded into sections 1 to 8; nothing in this file is overridden by a later section.
- **Choice 33** replaces the GO text and Choice 31's E⁰ rule (section 6.3).
- **Choice 35** corrects v04 section 11.4: H9's population is PD on the K8 tracker-planner's constraints (section 6.4).
- **Choice 37** adds history-length strata to H9, the three history-length cells to its family, H9-noHL as descriptive, and Q1's noHL reason (sections 4, 6.4).
- **Choices 22 to 27, 34 and 36** are stated where they act (sections 1.5, 3, 6.1, 6.5, 8.3).
- **R17 m8, stale text removed or corrected:** v04 section 1.3's "folds of 30 logs" for M\*Jx (now 3 + 1 folds of 75, section 3.2); v04 section 3's E1-AV2 "of the 150 AV2 logs" (now 375, section 3.2); the seeds for route indices 3 (public LT3D) and 4 (source transfer), the loop seeds and the seed of the 150-log descriptive folds, now in section 6.1. Also removed: v04 section 6.1 to 6.7's 150-log power and scaling tables as the plan's power (kept in v04 and in the cited JSON files), the 150-log fold rule for the primary routes, H5 as secondary, and the claim that the power tools are bound.
- **R17 m5:** ValidJ requires an evaluable pooled joint population, as the code does (section 6.2).
- **README v05 items:** the FROZEN_ROLES entry points, the order of operations, the limits (section 8).

---

## Frozen files

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END

FROZEN_ROLES_BEGIN
FROZEN_ROLES_END
