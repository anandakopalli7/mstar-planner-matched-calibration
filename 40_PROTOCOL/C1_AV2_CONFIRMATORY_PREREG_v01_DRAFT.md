# C1 pre-registration v01 (DRAFT): the external confirmation on Argoverse 2 (2 Nov 2026)

**Status.** Draft. Not reviewed, not frozen. The hash block at the end is empty. Every open item is marked `[SLOT: ...]` and listed in section 9. A freeze script must refuse this file while any slot is open.

**Line.** Claude line, Programme A. Laptop CPU for everything after detection. No spending is planned by this document. QCNet would need GPU spend and is a slot.

**Governing files (read in this order).** `90_DECISIONS/D16_DELEGATED_CHOICES_v01.md` (binding choices), `90_DECISIONS/D15_EXTERNAL_DATA_PROPOSAL_v01.md` (protocol; outcome-blind rule in its section 4), `90_DECISIONS/D14_K8_DESIGN_v05.md` (K8 endpoints, GO forms in its section 6, R15b mapping in its section 10), `90_DECISIONS/D13_FORWARD_PLAN_TO_GO_v01.md` (Phase 4). Templates: `40_PROTOCOL/K7_PREREGISTRATION_v02.md`, `40_PROTOCOL/M_PREREGISTRATION_v05.md`. Code notes: `50_CODE/k8/README_K8_v02.md`, `50_CODE/k8/README_K8_v03_ANALYSIS.md`. Claims: `20_DESIGN/MANUSCRIPT_DRAFT_v02.md` sections III to V.

**Outcome-blind attestation for this draft.** About Argoverse 2 (AV2), the author of this draft read only `60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md` (detector AP), `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md` and `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json` (counts). No AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error was computed, opened or requested. The only code run on AV2-derived input is `50_CODE/c1_av2/c1_power_counts_v01.py`, which reads the counts file and nothing else (section 6).

---

## 0. Why C1, and what kind of evidence it is

**Role.** D13 Phase 4 asks for one frozen plan that covers the method stage and the closed loop on external data. D14 section 1 says the external run is "the same study" as K8, frozen before the data are seen. D16 fixes the GO form and the labels of the arms.

**What the nuScenes evidence is.** Development evidence. K6 was a pre-registered NO-GO (power floor on T3). K7 was never frozen. K8 on the 840 nuScenes scenes is labelled exploratory (D14 section 1). Its v03 analysis (`50_CODE/k8/k8_analyse_v03.py`) is the analysis of record for those runs and supplies two inputs to this plan: the Form C ceiling c and the development effect sizes.

**What C1 is.** The first look at AV2 for every outcome named here. AV2 differs from nuScenes in cities, sensors, annotation rate (10 Hz cuboids), detector checkpoint and detector family operating point (D15 section 2; `AV2_DETECTOR_NOTE_v01.md`). The trackers keep their nuScenes parameters; none is re-tuned on AV2 (`AV2_TRACKER_PORT_DESIGN_v01.md` section 4.4).

**What a choice in this plan may use (D16 Rule 0).** The literature (`20_DESIGN/S02_LITERATURE_SYNTHESIS_v03.md`), nuScenes development results, AV2 detector AP, AV2 tracker HOTA/AMOTA and AV2 counts. Nothing else about AV2.

**One-shot commitment.** The AV2 validation split is used once for the claim family "validity and operability of DP-SCRC in the planner". If C1 is a NO-GO, the next step is diagnosis and a new study on new data. It is never a re-run of C1 for a better answer (section 8).

**Reporting constraints, binding on any write-up.**
- A C1 GO supports the claims of section 1 on AV2 validation, with the named detector, trackers and calibration route only.
- nuScenes K8 numbers are quoted as development evidence, beside K6 (NO-GO) and K7 (not frozen).
- A secondary or descriptive result keeps its label whatever it shows (D16 Rule 0, "No swaps").

---

## 1. Claims under test

**Manuscript claims** (`MANUSCRIPT_DRAFT_v02.md`, Contributions in section I):
- MC2: the 2 s extrapolated tracker covariance of in-path cars is mis-shaped; NEES scaling misdirects the fix (sections I, V-B).
- MC3/MC4: DP-SCRC is not significantly above δ on held-out logs and after transfer; the pooled single-threshold conformal correction (B4) fails where DP-SCRC holds, on both tracker families (sections IV, V-C).
- MC5: in a chance-constrained planner, DP-SCRC's relied-on constraints are valid and the planner is more operable than with any other valid calibration (sections V-D, VI-G; to be written from K8 and C1).
- R14 O1 (section V-D "Planned"; D16 Choice 3 and 4): a deployed learned predictor's covariance, recalibrated.

**Hypotheses.** δ = 0.05 throughout. "Valid", "flag" and the forms are defined as formulas in section 5.4.

| ID | Label | Maps to | Statement (per tracker unless stated; detector LT3D unless stated) |
|---|---|---|---|
| **H1** | **Primary** | MC5 | **Form B** (D16 Choice 1) holds on T1 **and** T3, decision mode, calibration route W (section 3): M\* is valid on PD7, SD1_7 and PD, and its infeasible-decision rate is lower than that of every comparator that is also valid |
| H2 | Secondary (pre-registered) | MC5 | **Form C ceiling** (D16 Choice 1): M\*'s infeasible-decision rate is at most B4's plus c_t, on T1 and on T3, with c_t from the nuScenes K8 v03 analysis `[SLOT: c_T1, c_T3]` |
| H3 | Secondary, or exploratory `[SLOT: M*J development verdict]` | MC5 | **M\*J** (D16 Choice 2b): the joint loss (per-decision union indicator) of M\*J passes Form B's validity test on T1 and T3 |
| H4 | Secondary | MC5, R10 of S02 | **Transfer in the loop**: Form B holds on T1 and T3 when every fitted arm uses the frozen nuScenes fit (route T) |
| H5 | Secondary | MC5 | **Second detector**: Form B holds on T1 and T3 on VoxelNeXt tracks (route W) |
| H6a | Secondary | MC3/MC4 | **Method stage, within AV2 (E1-AV2)**: M\* is flagged in no E1-AV2 cell, under the fixed-rule and the refit-CV inference, on T1 and T3 (the AV2 analogue of HM1) |
| H6b | Secondary | MC4 | **Practitioner failure**: B4 fails (flagged, M\* not flagged, paired difference significantly positive; refit-CV) in at least one E1-AV2 cell on T1 **and** on T3 (the AV2 analogue of HM2 for B4) |
| H7 | Secondary | MC3/MC4 | **Method stage, transfer (E2-AV2)**: the M-stage M\* fitted on the 700 nuScenes train scenes is flagged in no AV2 cell, and the pooled AV2 cell is not flagged, on T1 and T3 (the AV2 analogue of HM6) |
| H8 | Secondary | MC2 | **Diagnosis replicates (T1)**: at least one in-path car lateral 2 s cell (< 20 m or 20 to 40 m) FAILS under B0 (the raw covariance), and its truth-oriented exceedance also FAILS |
| H9 | `[SLOT: secondary if the nuScenes predictor-arm plan is frozen and run before this freeze; else descriptive]` | R14 O1 | **Predictor transfer arm**: Trajectron++ `int_ee`, recalibrated by DP-SCRC on nuScenes and transferred unchanged (D16 Choice 4), is flagged in no evaluable AV2 cell and its pooled cell is not flagged, on T1 and T3 histories |

**Descriptive (reported in full, never a claim):** Form A (D16 Choice 1); loop mode (collisions, front-buffer intrusions, V2_viol on PL7; D14 section 4 S1); V2 and its variants for every arm (D16 Choice 2 last bullet; D14 A1); TTV < 4 s and `ttv_enf` (S2), with TTV < 2 s labelled "arm-invariant by construction (R15b N3)"; A6 calibration diagnostics and A7 sharpness; the α-sweep curve and the δ′ arms (A2, A3, both boundary flags); A13 fallback shares; A14 duplicates; NIP (A9); margin ratios (M-PLAN section 8, K5e); the motion-stratum ablation B6 versus M\* in the method stage (HM3 analogue; nuScenes HM3 was inconclusive, `MANUSCRIPT_DRAFT_v02.md` V-C); T2 if run; the raw predictor covariance's exceedance direction (PSU-TF expectation, D16 Choice 3).

**Not claimed.** A closed-loop guarantee; any safety ranking from loop-mode collisions (log replay with non-reactive agents, D10 section 2); validity in non-evaluable cells; validity along an object's true axes (K7 section 1); anything about objects outside the four analysis groups; transfer to AV2 test or train splits.

---

## 2. Data

### 2.1 Logs and frames

| Item | Value | Source |
|---|---|---|
| Split | AV2 Sensor, validation, 150 logs | D15 section 1; counts file `runs.t1_lt3d.logs` = 150 |
| Frames | Every 5th lidar sweep from sweep 0 (2 Hz), 4,806 frames; 31 to 40 per log, median 32 | `AV2_DETECTOR_NOTE_v01.md` "Data"; port design section 2 (probe P-a); counts file `frames` = 4,806 |
| Frame interval | median 0.5003 s, max 0.5999 s (a dropped sweep) | port design section 2 |
| Scene and log | One log = one scene; log-cluster and scene-level resampling coincide | port design section 2 |
| Decision states | keyframes 1 ≤ k ≤ K − 2 per log (K7 section 2 rule): about 4,806 − 2 × 150 = 4,506, about 30 per log | counts file; derived |
| Licence | CC BY-NC-SA 4.0; derived statistics and code released, data not | D15 sections 1, 2 |
| Data manifests | pod 56533144…, laptop copy without maps 47735085… (full hashes bound at freeze) | `AV2_DETECTOR_NOTE_v01.md` "Data" |

### 2.2 Detectors (D16 Choice 5; D15 section 3 step 2)

| | LT3D CenterPoint (**primary**) | OpenPCDet VoxelNeXt (**second detector**, H5) |
|---|---|---|
| Checkpoint SHA-256 | 299cf3b7… | 8641d838… (wrapped copy e513ef56…) |
| Velocity | regressed | none (tracker shim S3, port design section 8) |
| AP at 50 m: regular vehicle, pedestrian, bicyclist | 0.875, 0.795, 0.543 | 0.891, 0.782, 0.638 |
| Frames | the 4,806 frames | the same frames |

Source: `AV2_DETECTOR_NOTE_v01.md`. The AP values are descriptive; nothing in this plan is gated on them.

### 2.3 Trackers (D16 Choice 5)

- **T1**: CANMOT `paper/local/canmot/sc`. **T3**: Poly-MOT `paper/baseline/poly_mot`. Parameters transferred unchanged from nuScenes, including the 0.1 detector score floor and every class threshold (port design section 4.4).
- T2 (`paper/local/sample/trainval`) is descriptive only, if run.
- Tracker input restricted to the ego-frame square |x|, |y| ≤ 54 m for both detectors (port design section 5).
- 2 Hz is the primary protocol. 10 Hz is a D15 sensitivity that the port has not run; it stays descriptive `[SLOT: run the 10 Hz sensitivity or drop it]`.

### 2.4 Classes and groups

- **Analysis classes (D15 section 3.5, fixed before download):** car := `REGULAR_VEHICLE`; pedestrian := `PEDESTRIAN`; cyclist := `BICYCLIST` with the ridden-two-wheeler rule RB-1 (port design section 4.3).
- **Tracker input mapping:** the seven nuScenes tracking classes (port design section 4.2).
- **Strata and planner groups.** DP-SCRC's strata use four groups (car, pedestrian, two-wheeler, large; M-PLAN section 4). The planner constrains every tracked object it considers. So every fed class needs a group: two-wheeler := bicycle (`BICYCLIST`) and motorcycle (`MOTORCYCLIST`); large := bus, truck and trailer classes as in port design section 4.2. The validity cells are the nuScenes cells over all four groups. D15's three classes are the headline reporting classes. `[SLOT: lead confirms the four-group reading; D15 section 3.5 names only three classes, and the port design section 4.2 calls motorcycles and large vehicles "descriptive only"]`

### 2.5 Items, strata and populations

- **Method-stage items** (H6 to H9): M-PLAN section 3 unchanged. A (record, axis) pair at k ≥ 1, in the ego's 4 s CTRV corridor, persistently paired (2 m gate), uncensored at k + h, on a separating axis, oriented toward the ego from the estimate. h = 2 s (4 frames) for decisions; 1 s and 4 s descriptive. Score U = D/sd, sd = √(aᵀΣ̂a + σ_a²), σ_a = 0.10 m.
- **K8 items and records** (H1 to H5): K7 section 2 and `k8_items_v02.py`: enforced (track, check time) pairs at decision states, considered tracks within 60 m and not behind, every separating axis at the logged reference pose, split by the in-path flag.
- **Strata:** M-PLAN section 4: group × range (< 20, 20 to 40, ≥ 40 m, from the predicted ego at k + h) × axis × motion state (static, new, straight, turning; course-over-ground turn rate). L1, L2, L3 as before.
- **Populations** (D14 section 4): PD7 (all relied constraints at decision states), SD1_7 (PD7 with pair gap ≤ 5 m), PD (PD7 in-path), NIP (PD7 not in-path, reported).
- **Cells:** K8 validity cells are group × axis × motion pooled over range (32) plus the pooled cell (K7 section 4). Method-stage cells follow M-PLAN section 7 (E1 and E2 rules).
- **Evaluable cell:** ≥ 39 scenes from ≥ 8 logs (K6, K7). On AV2 a scene is a log, so this is ≥ 39 logs.
- **Ego footprint.** The port kept the nuScenes constants (4.1 × 1.8 m, +0.5 m, rear axle 1.39 m behind centre) and flagged the choice (port design section 5). **Recommendation:** keep the nuScenes constants as the protocol (the strata, the in-path rule and the transferred fits depend on them); run AV2's Ford Fusion footprint (about 4.9 × 1.9 m, port design section 5) as a descriptive sensitivity `[SLOT: source for the Fusion's rear-axle-to-centre offset, or drop the sensitivity]`.

### 2.6 Counts (outcome-free)

All from `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json` (created 2026-11-02 03:23 UTC by `av2_counts_v01`). **Only T1 on LT3D exists.**

| Quantity (T1, LT3D) | Value | Field |
|---|---|---|
| Frames, logs | 4,806, 150 | `runs.t1_lt3d.frames`, `.logs` |
| Export records; tracks | 229,438; 33,362 | `.export_records`, `.tracks` |
| Records at frame 0; at k ≥ 1 | 7,072; 222,366 | `.association.frame0_records`, `.records_k_ge_1` |
| In-path records; paired; unpaired | 5,894; 4,899 (83.1 %); 981 | `.association.inpath_records`, `.paired_inpath`, `.unpaired_inpath` |
| Records by horizon status (k ≥ 1) | available 97,555; not paired 97,128; censored at horizon 11,271; no future frame 16,412 | `.records_by_horizon_status` |
| Duplicate records within 1 m; ID switches | 24,807; 611 | `.association` |
| In-path paired car items at k, by range (t0) | < 20 m: 2,928 (123 logs); 20 to 40 m: 2,193 (122); ≥ 40 m: 306 (59) | `headline_car_inpath_paired_items_t0_by_range` |
| In-path paired car items with the horizon available | < 20 m lat 590 (86 logs), long 1,961 (118); 20 to 40 m lat 443 (86), long 1,559 (119); ≥ 40 m lat 87 (37), long 211 (56) | `summaries.paired_horizon_available_items_by_group_range_axis_population` |
| In-path paired pedestrian items, horizon available | < 20 m lat 61 (20 logs); 20 to 40 m lat 39 (15) | same |
| In-path paired cyclist items, horizon available | at most 12 items in 1 log per range × axis cell | same |

**Caveats.** (1) Range here is at time k (`t0`), not from the predicted ego at k + h; the h = 2 s strata need `av2_horizon_prep_v01.py --propagate-only`, which is tracker output only and allowed by D15 section 4, but not run yet. (2) These are method-stage counts. The K8 decision-mode counts (PD7, SD1_7, PD records per cell and per log) do not exist on AV2. (3) For comparison, nuScenes had 63.9 % (val) and 67.4 % (train) of in-path records paired (`MANUSCRIPT_DRAFT_v02.md` V-A); AV2 T1 LT3D has 83.1 %.

`[SLOT: final counts. T3 on LT3D; T1 and T3 on VoxelNeXt; the h = 2 s predicted-range strata; the K8 decision-mode record counts per population, cell and log for each tracker × detector, from an outcome-blind counts pass like K7's k7_design_counts]`

---

## 3. The method stage on AV2: what is calibrated where

### 3.1 What D15 says, and where it is ambiguous

D15 section 3 step 4 lists "the nuScenes-fitted recalibration **frozen before any AV2 run**". The manuscript repeats this (`MANUSCRIPT_DRAFT_v02.md` V-D "Planned"), and D16 Choice 4 applies it to the predictor arm. That part is explicit, and this plan keeps it to the letter (route T below).

D15 is ambiguous on three points:
1. **Role.** It does not say whether the transferred fit is the primary calibration for the GO, or whether a within-AV2 calibration is also run.
2. **Which fit.** There are two nuScenes fits. The method-stage fit is on the 700 train scenes, in-path items (`60_RESULTS/m/m_result_*_v04.json`, `E2_h2s.fit_on_all_train`). The K8 fits are planner-matched and exist only per fold: `60_RESULTS/k7_fits_v01/k7_fits_t1_v01.json` holds folds 0 to 4 (fold sizes 176, 179, 163, 168, 164 scenes) and no all-scene fit.
3. **"The same study."** D14 section 1 says the external run is the same study as K8. On nuScenes, K8 calibrates by 5-fold log cross-fitting inside the dataset (D14 A3; K7 section 2).

### 3.2 Options

| | Route | What it tests | Theory covering it |
|---|---|---|---|
| **T** | Transfer only: every fitted arm uses a frozen nuScenes fit | Deployment of the nuScenes thresholds on a new dataset, detector checkpoint and tracker noise regime, without recalibration | None. CRC and Mondrian validity need exchangeable calibration and test scenes |
| **W** | Within AV2 only: every fitted arm is cross-fitted on AV2 log folds | The procedure of Algorithm 1 (calibrate on logs of the deployed stack) replicated on a second dataset and detector | P02 PM1 / Proposition 6 under i.i.d. logs |
| **TW** | Both, each with its own label, fixed now | Both questions, without choosing after the data | As above, per route |

### 3.3 Recommendation: TW, with W primary for H1 and H6, and T secondary (H4, H7)

Reasons, from `S02_LITERATURE_SYNTHESIS_v03.md`:
1. **The certificate is exchangeable-scene.** CRC's guarantee (Angelopoulos et al. 2024, Thm 1; S02 D5) and Mondrian per-stratum validity (Vovk 2012; S02 D3) need calibration and test units drawn from one distribution. S02 D4 states that the scene-level certificate assumes i.i.d. scenes and that a new-scene reading needs every ingredient of the score fitted outside the evaluation scenes. nuScenes to AV2 changes the detector checkpoint (10-sweep nuScenes CenterPoint against 5-sweep LT3D CenterPoint), cities, sensors and annotation rate, while the tracker noise stays nuScenes-tuned. No source in S02 gives a guarantee across that shift.
2. **The published conformal corrections of a filter or predictor covariance calibrate on the system they deploy on.** Weisman et al.'s CGKF and LUCCa's per-partition factor (S02 D8), and Lindemann et al.'s trajectory units (S02 D4). Algorithm 1 (`MANUSCRIPT_DRAFT_v02.md` IV-I) is "fitted offline on logs with ground truth" from the deployed stack.
3. **K8 is within-dataset.** D14 section 1 calls the external run "the same study". K8's M\*, B1, B3, B4, B6, B9 and RETUNED are cross-fitted on log folds (D14 A3, K7 section 2).
4. **Form B stays symmetric.** Under W, every fitted comparator is refitted on the same AV2 folds as M\* (D14 section 6 B(i)).
5. **D15's transfer is kept, pre-registered, with its own criterion** (H4, H7). The M-PLAN already reads a transfer failure as a confounded-shift result (M-PLAN section 2, "Consequences for E2"); C1 adds dataset and detector to those shifts.

**Cost of W, stated plainly.** For a conformal method, held-out validity within one distribution is close to pinned in pooled cells (M-PLAN section 1, "E1 is pinned"). The parts of H1 that are not pinned are the planner's relied-on selection, per-cell validity under the hierarchy, the floors, comparator validity and operability (K7 section 0). The transfer claims H4 and H7 carry the harder test and are reported beside H1 whatever they show.

`[SLOT: the lead confirms route TW with W primary, or chooses T as primary (D15's literal reading). If T is chosen, H1 and H4 swap labels before the freeze; nothing else changes]`

### 3.4 What is calibrated where

| Arm | Route W (within AV2; primary for H1, H5, H6) | Route T (transfer; H4, H7) |
|---|---|---|
| Method-stage M\* and baselines B1, B2, B4, B5, B6, B7, B8, B9, B10, M-LS; pricing references B3, B6c | E1-AV2: 20 repetitions of a 5-fold split of the 150 AV2 logs (seed 20261113 + r, logs permuted and assigned greedily by item load; M-PLAN section 6 assigns by scene load, and on AV2 each log is one scene) | Fits on all 700 nuScenes train scenes, read from `60_RESULTS/m/m_result_{canmot_sc,polymot}_v04.json` (`E2_h2s.fit_on_all_train`), unchanged |
| K8 planner-matched M\* (`Mstar_ip`), B1, B3, B4, B6, B9 | `k7_fit_v01.py` logic on AV2 K8 items, 5 log folds of 30 logs (seed 20261112), each log's thresholds from the fit on the other 4 folds | One new all-850-scene nuScenes fit of the same arms, made by a new script before the freeze from nuScenes items only `[SLOT: write and hash the all-scene K7-form fit; the existing file holds per-fold fits only]` |
| RETUNED | Cross-fitted selection on the merged α/δ′ curve over the AV2 folds (D14 A3) | The merged-curve point chosen on all 840 nuScenes scenes by M\*'s criterion, read from the K8 v03 analysis `[SLOT]` |
| M\*J (joint loss) | Cross-fitted on the AV2 folds, one shared inflation per stratum family (D16 Choice 2b) | nuScenes all-scene fit, descriptive |
| B0, Z0, the α-sweep, the δ′ arms, LOG | Fit-free | Fit-free |
| Trajectron++ `int_ee` DP-SCRC (H9) | Within-AV2 refit: descriptive | **Primary for this arm** (D16 Choice 4): the DP-SCRC fit on all 150 nuScenes val scenes of that predictor's items (D16 Choice 3 calibrates by 5-fold cross-fitting inside val; the deployable all-150 fit is its transfer form) |

**Inference per route.** W, K8: log-cluster bootstrap, B = 2000, weights shared by every arm (K7 section 7). W, method stage: fixed-rule log bootstrap (B = 2000) and refit-CV (B = 200), as M-PLAN section 6 E1. T, method stage: two-sample refit log bootstrap that resamples nuScenes train logs (refitting) and AV2 logs, B = 1000 at 2 s, as M-PLAN section 6 E2. T, K8: one-sample AV2 log bootstrap with the nuScenes fit held fixed (a deployed-rule estimand), B = 2000; this is stated as a different estimand from W's.

**Ordering rule.** Every fit used by route T is computed and hashed before the freeze, from nuScenes data only. Every route W fit is computed after the freeze by frozen code.

---

## 4. Comparators and arms

| Arm | What it is | Label in C1 | Source |
|---|---|---|---|
| **M\*** (`Mstar_ip`) | DP-SCRC, planner-matched, split by in-path; per-constraint certificate | **Primary certificate** (D16 Choice 2a) | K7 section 2; D14 section 4 |
| B0 | Raw covariance z·sd | Form B comparator | D14 section 4 |
| B1 | NEES-scaled | Form B comparator | K7 section 2 |
| B3 | Certified single multiplier | Form B comparator (pricing reference) | README_K8_v02 "Form B comparators" |
| B4 | Pooled conformal (planner-matched) | Form B comparator; Form C reference | D14 section 6 |
| B6 | No motion strata | Form B comparator | README_K8_v02 |
| B9 | Norm-ball conformal | Form B comparator | K7 section 2 |
| RETUNED | Least conservative merged-curve point meeting M\*'s criterion, cross-fitted | Form B comparator | D14 A3 |
| Z0 | Mean only | Descriptive reference; never a comparator | D14 section 6 |
| α-sweep (12 points), δ′ arms (9 points) | One curve | Descriptive; single points are never comparators | D14 A2, A3; README_K8_v02 |
| LOG | Delayed logged profile | Loop-mode reference | D14 section 2 |
| **M\*J** | Scene-level CRC on the joint loss, one shared inflation per stratum family | Secondary (H3), or exploratory if it fails validity on nuScenes development data | D16 Choice 2b `[SLOT]` |
| **M\*\_NS** and the route-T comparators | The same arms with frozen nuScenes fits | Secondary (H4, H7) | Section 3 |
| **Trajectron++ `int_ee` transfer arm** | ECCV 2020 branch, commit ef0165a9…, no map, 2 Hz, tracker histories (T1, T3) on AV2; covariance V2 (moment-matched, primary), V1 (most likely mode, secondary), Σ + Σ_track (sensitivity); ground-truth histories as an upper bound; DP-SCRC transferred from nuScenes | `[SLOT: secondary or descriptive]` (H9) | D16 Choices 3, 4 |
| Trajectron++ `int_ee_me` | Map model | Not run on AV2 (no nuScenes-format map on AV2); on nuScenes it is primary only if the map expansion arrives `[SLOT]` | D16 Choice 3 |
| QCNet (AV2 checkpoint) | Learned predictor native to AV2 | Descriptive, only if the researcher approves GPU spend `[SLOT]` | D16 Choice 4 |

Form B's comparator set is exactly {B0, B1, B3, B4, B6, B9, RETUNED}, as implemented in `k8_analyse_v03.py` (`d14_forms`) and listed in README_K8_v02. Form A's set is {B0, B1, B4, B9} (D14 section 6).

---

## 5. Endpoints, modes, tests, multiplicity and GO conditions

### 5.1 Modes (D14 section 2, unchanged)

- **Decision mode** carries every confirmatory test of H1 to H5: one decision per keyframe from the logged ego's state, identical decision states for every arm, leash to the log, v_max = log maximum + 2 m/s, 32 accelerate-then-brake candidates plus the emergency stop, object-axis half-spaces with a 0.5 m buffer every 0.25 s to 2 s, exemption rule C8, back-off ladder λ ∈ {0.75, 0.5, 0.25, 0}, recorded tracks at score ≥ 0.4 (unchanged from nuScenes, although LT3D's scores are calibrated differently; port design section 4.4), deployable covariance with σ_a = 0.10 m.
- **Loop mode**: closed-loop replay with non-reactive agents, delays d ∈ {0, 1, 2} s, references Z0 and LOG. Descriptive only.

### 5.2 Endpoints (D14 section 4)

- **V1**: per-constraint exceedance, scene-level (here log-level) rate per population, per cell and pooled.
- **O1**: infeasible-decision rate (K6 section 4.2 definition); **O2**: progress ratio and mean speed; **O3**: back-off distribution.
- **S1**: V2_viol (decision mode), collisions and front-buffer intrusions (loop mode). **S2**: TTV < 4 s and `ttv_enf`; TTV < 2 s labelled "arm-invariant by construction (R15b N3)".
- **V2** and variants (V2_near, V2_binding, V2_exec split by the emergency stop, V2_dedup, one-step check), read against the reference 1 − (1 − δ)^{n_tracks}.
- **C1 to C4** calibration diagnostics and sharpness (A6, A7).
- **Joint loss** for M\*J: the per-decision union indicator over the 4 annotated calibrated steps and all relied tracks, per population.
- **Method stage**: scene-level exceedance per cell (M-PLAN section 7); margins and ratios.

### 5.3 Statistics (shared)

- Unit: the log (= scene). Estimand: log-level mean of each log's rate.
- Bootstrap: log-cluster, weights shared by all arms. Seeds `[20261110, i, j]` for K8 bootstrap (i = 0 for T1, 1 for T3; j = 0 LT3D route W, 1 LT3D route T, 2 VoxelNeXt), `[20261111, i, j]` for the power rule, 20261112 for the K8 folds, 20261113 + r for the method-stage repetitions. Fixed now; never re-drawn.
- Cell flag: one-sided simultaneous sup-t at 0.95 over the arm's evaluable cells (K7 HK1(i)); zero SE with Ê > δ flags. M\*'s sup-t quantiles must be finite (R15b N1); a comparator's non-finite quantile is q = None and its cells are judged by Ê > δ (README_K8_v03 N1).
- Power rule and floor: power ≥ 0.80 to flag a true rate of 0.15 in the population's all-evaluable sup-t, beta-binomial with intra-scene correlation 0.5, 200 datasets, the arm's record counts, the first 500 bootstrap weights; F_MIN = 6 (K7 HK1(iii)). Unchanged (D14 section 7: the standard does not change).
- Paired operability: per-log differences at identical decision states; one-sided log-bootstrap bounds.
- p-values for multiplicity (5.5): one-sided, studentised, from the same bootstrap replicates as the bounds; for a bound criterion "UB < x" the p-value is the smallest α at which it holds.

### 5.4 Definitions and GO conditions as formulas

Per tracker t, detector and route as stated in the hypothesis. P ∈ {PD7, SD1_7, PD}. K = {B0, B1, B3, B4, B6, B9, RETUNED}. f_{a,l} is arm a's infeasible-decision rate in log l; L is the set of logs.

```
Flag_cell(a,P,c)   := LB^{sup-t, 0.95}_{a,P}(c) > δ,  or  SE_{a,P}(c) = 0 and Ê_{a,P}(c) > δ
NoFlag(a,P)        := no evaluable cell c of P has Flag_cell(a,P,c)
NoFlag_pool(a,P)   := pooled cell of P evaluable and LB^{0.95}_{a,P}(pooled) ≤ δ
Floor(a,P)         := F_{a,P} ≥ 6 for P ∈ {PD7, SD1_7};  at least 1 evaluable cell for P = PD
HK1c(a,P)          := UB^{0.95}_{a,P}(pooled) ≤ δ + 0.03
Valid(a,t)         := AND over P of [ NoFlag(a,P) ∧ NoFlag_pool(a,P) ∧ Floor(a,P) ∧ HK1c(a,P) ]

V_t                := { c ∈ K : Valid(c,t) }
Δ_t(c)             := (1/|L|) Σ_{l ∈ L} ( f_{M*,l} − f_{c,l} )
FormB(t)           := Valid(M*,t) ∧ for every c ∈ V_t: UB^{1 − 0.05/|V_t|}(Δ_t(c)) < 0
                      (if V_t is empty, the second part holds and this is reported)
FormA(t)           := Valid(M*,t) ∧ for every c ∈ {B0,B1,B4,B9}: UB^{1 − 0.05/4}(Δ_t(c)) < 0
FormC(t)           := UB^{1 − α_C}(Δ_t(B4)) ≤ c_t,
                      c_t = max(0.03, ceil(100·π_t)/100 + 0.01),
                      π_t = nuScenes K8 v03 exploratory decision-mode f_{M*} − f_{B4}   [SLOT]

H1 (primary)  := FormB(T1) ∧ FormB(T3)          LT3D, route W, decision mode
C1 GO         :⇔ H1.     C1 NO-GO otherwise, with every failed condition named.

H2  := FormC(T1) ∧ FormC(T3)                     LT3D, route W
H3  := for t ∈ {T1,T3} and P ∈ {PD7,SD1_7,PD}:
         LB^{0.95}(V2_P of M*J) ≤ δ  ∧  UB^{0.95}(V2_P of M*J) ≤ δ + 0.03
         [+ NoFlag over stratum-family cells if the development implementation defines them; SLOT]
H4  := FormB(T1) ∧ FormB(T3) with every fitted arm from route T
H5  := FormB(T1) ∧ FormB(T3) on VoxelNeXt tracks, route W
H6a := for t ∈ {T1,T3}: M* flagged in no E1-AV2 cell, fixed-rule and refit-CV (M-PLAN HM1)
H6b := for t ∈ {T1,T3}: ∃ E1-AV2 cell c with B4 flagged (refit-CV), M* not flagged,
         and LB^{sup-t}(Ê_{B4}(c) − Ê_{M*}(c)) > 0   (M-PLAN section 7, "a baseline fails")
H7  := for t ∈ {T1,T3}: M*_NS flagged in no E2-AV2 cell ∧ pooled AV2 cell LB^{sup-t} ≤ δ (M-PLAN HM6)
H8  := T1: ∃ r ∈ {<20, 20-40}: lateral in-path car cell r has LB > max(δ, E⁰_r) under B0
         ∧ the truth-oriented exceedance of cell r has LB > δ    (X2's FAILS rule, 95 % sup-t band over the 4 cells)
H9  := for t ∈ {T1,T3}: Trajectron++ int_ee DP-SCRC (route T) flagged in no evaluable AV2 cell
         ∧ pooled cell not flagged
```

Reading of D16's "price on PD7": the infeasible-decision rate is a decision-level quantity. "On PD7" is read as the decision-mode run whose validity is measured on PD7. `[SLOT: lead confirms this reading]`

**Comparator classification.** The literal reading of D14 section 6 B(i), implemented in `form_valid`, removes a comparator from (ii) when it fails any validity condition, including the floor. A comparator that fails only the floor has not been shown invalid. **Recommendation (stricter for M\*):** keep a floor-only failure in V_t for part (ii) and report it as "validity not shown (floor)". `[SLOT: lead chooses the literal or the stricter reading]`

### 5.5 Multiplicity

- **H1** is an intersection-union test over trackers and conditions. Each condition is tested at its own level; no further correction is needed (every condition must hold). Inside it, Bonferroni across valid comparators (1 − 0.05/|V_t|) as D14 section 6 states.
- **Validity conditions are "no flag" tests.** A multiplicity correction would make them easier to pass, so none is applied across populations, trackers or claims; each population is tested at 0.95 (D14 section 4, R15b n1). This covers H3, H6a, H7, H9 and the Valid(·) parts of H1, H4, H5.
- **Family S (solution claims that need a rejection): H2, H4, H5, H6b.** Serial gatekeeping on H1, then Holm at family-wise 0.05. If H1 fails, these four are reported with their unadjusted results and labelled "supportive, not confirmatory (gate H1 not passed)". A claim's p-value is the maximum over its trackers of its Bonferroni-adjusted rejection p-value (for Form B parts: |V_t| times the largest per-comparator p-value, capped at 1). Its validity parts are pass/fail gates at 0.95.
- **Family P (the problem claim): H8** alone, at 0.05. It answers a different question from family S and is not gated on H1.
- This gatekeeping and Holm design is a choice made in this draft, not in D14 or D16. It is listed for review in section 9.

### 5.6 What is reported whatever the outcome

Every arm, form, population, detector, route and mode: the full K8 table (validity, operability, safety, calibration, sharpness), the trade-off table for every comparator that fails Form B(i) with its exceedance on the binding population (D16 Choice 1), Form A, and the method-stage tables.

---

## 6. Power and precision from the counts only

**Script and output.** `50_CODE/c1_av2/c1_power_counts_v01.py` (SHA-256 22c7c509…dd3), output `70_TESTS/c1_scratch/c1_power_counts_v01.json` (27c36df1…f6d), seed 20261102, 822 s on one process. It read the counts file (eb81a056…456) and nothing else about AV2. Every number in this section is from that JSON. The effect sizes are nuScenes development numbers copied into the script with their sources: infeasible-decision rates and pooled PD7 exceedances on the 10 development scenes (`README_K8_v02.md` "Development check" for M\*, B0, B4, RETUNED; `K7_PREREGISTRATION_v02.md` section 9a for B1, B3, B6, B9); X2's in-path car scene-level exceedances and thresholds (`MANUSCRIPT_DRAFT_v02.md` Table II).

**What this is not.** It is not the operating characteristic of the coded rule. The K8 decision-mode counts do not exist on AV2 (slot S3), so cell flags, SD1_7, PD and the floors are not simulated for H1. Every probability for H1 below is therefore an **upper bound** that uses the pooled PD7 cell only. The OC of the coded rule on the real counts is slot S12.

### 6.1 Layout assumptions (from the counts)

- 150 logs; 30.04 decision states per log ((4,806 − 300)/150).
- PD7 records per log: 627.5, assumed as 30.04 × (900,000 / 32,449 nuScenes PD7 records per decision; K7 sections 2 and 9a) × 0.753 (AV2 T1 LT3D export records per frame, 47.7, over nuScenes T1 val, 63.4).
- Intra-log correlation of exceedances ρ_e ∈ {0.05, 0.15, 0.30} (K6 M\*: median 0.13 to 0.15 in PD7 cells; K7 section 8). Log-level correlation of infeasibility ρ_log ∈ {0.1, 0.3} (assumed; no source).
- Coupling of two arms' infeasibility at the same decision: comonotone (fewest discordant decisions, highest power) and independent (most, lowest power). The truth lies between.

### 6.2 Which cells can be evaluated (≥ 39 logs)

- **Method stage, in-path (T1, LT3D, 2 s horizon available):** only car cells. Evaluable for certain: car long new, static, straight, turning and car lat straight. Uncertain (log union between bounds): car lat new (19 to 40 logs), lat static (38 to 56), lat turning (31 to 42). Every pedestrian, two-wheeler and large in-path cell has at most 25 logs; they enter only through the remainder and pooled cells (M-PLAN section 7 E2 rule).
- **Planner population, upper bounds** (logs with any paired item at k, in-path or not, per group × axis × motion): car 130 to 150 logs in all 8 cells; pedestrian 113 to 150 in all 8; large 57 to 125; two-wheeler at most 32 (never evaluable). PD7 cells are subsets of these.

### 6.3 Floors (F_MIN = 6 power-qualified cells)

Minimum logs for one cell to have power ≥ 0.80 against a true rate of 0.15 under the power rule (ρ = 0.5), with Bonferroni critical values (conservative against the coded sup-t):

| Family size k | q | 5 records per log | 20 | 100 |
|---|---|---|---|---|
| 1 (lower bound) | 1.645 | 45 | 35 | 35 |
| 10 | 2.576 | 80 | 70 | 65 |
| 20 | 2.807 | 90 | 80 | 75 |
| 32 | 2.955 | 100 | 85 | 85 |

**Reading.** A power-qualified cell needs roughly 65 to 100 logs. For PD7, the car and pedestrian cells have upper bounds of 113 to 150 logs, so 6 power-qualified PD7 cells are plausible. For SD1_7 (gap ≤ 5 m) no count exists; it is a much smaller subset, and the floor is a real risk there. K6 failed on exactly this kind of floor. The OC on the real counts must settle it before the freeze (slot S12, acceptance (c)).

### 6.4 H1 and Form A (pooled PD7 proxy, decision mode, route W)

At the central setting ρ_e = 0.15:

| | T1 | T3 |
|---|---|---|
| P(M\* pooled PD7 valid) | 0.997 to 0.999 | 0.946 to 0.961 |
| P(B4 valid) | 0.16 to 0.18 | 0.00 |
| P(B6 valid) | 0.82 to 0.84 | 0.47 to 0.50 |
| P(M\* beats B6 at the Bonferroni level, given B6 valid) | 1.00 | **0.00** |
| P(Form B), pooled proxy | 0.93 to 1.00 | **0.48 to 0.50** |
| P(Form A), pooled proxy | 0.66 to 1.00 | 0.00 |

Across all settings (ρ_e 0.05 to 0.30, both couplings): P(Form B) is 0.86 to 1.00 on T1 and 0.42 to 0.87 on T3. P(H1) as a product of the two is about 0.36 to 0.87, about 0.47 at ρ_e = 0.15. These are upper bounds.

**The dominant predicted failure is T3 against B6.** On the development scenes B6 is more operable than M\* on T3 (0.169 against 0.191) while its pooled PD7 exceedance (0.063) sits close enough to δ that it is classified valid in about half of the simulated datasets. Two other development facts point the same way: K6's B6 was at 0.215 against M\*'s 0.222 on T3 over 840 scenes (`MANUSCRIPT_DRAFT_v02.md` V-D), and the method stage found that the motion strata cost 6 to 11 % of margin on T3 (DP-SCRC/B6 = 1.056, E1 1.110; Table VI). Form A fails on T3 for the reason D12 gave (B4 more operable); Form B removes that failure but exposes B6. B6 stays in the comparator set: removing it would weaken the test. The 840-scene K8 v03 numbers replace these 10-scene effect sizes before the freeze (slot S12); if they confirm the B6 pattern, the lead should know the predicted H1 risk before freezing.

### 6.5 Precision

- **Pooled PD7 exceedance of M\*** (true 0.05): SE 0.0040, 0.0069, 0.0096 at ρ_e 0.05, 0.15, 0.30; two-sided 95 % half-widths 0.008, 0.013, 0.019.
- **Paired infeasibility difference M\* − B4**: SE 0.0019 to 0.0024 (comonotone) and 0.0066 to 0.0079 (independent).
- **M\*J joint loss** (H3; 30 decisions per log): at a true joint rate of 0.05, P(valid) 0.96, 0.97, 0.86 at ρ 0.05, 0.15, 0.30; at 0.08 it is flagged with probability 1.00, 0.97, 0.81; two-sided 95 % half-widths at a true rate of 0.05 are 0.010 to 0.020.

### 6.6 H2 (Form C ceiling)

At the development prices the rule gives c = 0.03 on both trackers (T1: −0.020 → 0.03; T3: +0.016 → 0.02 + 0.01 = 0.03). With the true AV2 price equal to the development price:
- T1: P(ceiling shown) 1.00 under both couplings.
- T3: 1.00 (comonotone) but **0.57 to 0.65 (independent) at level 0.05**, and 0.31 to 0.39 at 0.01 (the worst Holm step with 4 claims is 0.0125).
- If the true price is 0.02: 0.99 (comonotone), 0.34 to 0.44 (independent). At 0.03 the claim is false and is shown in 0.05 to 0.07 of datasets (the size).

**Reading.** D16's rule sets c only 0.01 to 0.02 above the development price. H2 then has adequate power only if the two arms' decisions are highly concordant. This is a property of D16's rule, reported here, not changed.

### 6.7 Method stage and diagnosis

- **Component power** (one car cell flagged, fixed calibration, 10-cell family, ρ 0.3 / 0.5): MDE80 0.12 / 0.15 for car long straight (2,797 items, 122 logs), 0.15 to 0.20 for car lat straight and long static, 0.20 for long new and long turning, 0.20 to 0.25 for lat static and lat turning, 0.30 for lat new. nuScenes E2 had 0.15 to 0.30 (M-PLAN section 9). The refit-CV inference of H6 is more conservative than this (M-PLAN section 6).
- **H8** (T1): at X2's scene-level effect the 20 to 40 m lateral cell FAILS with power 0.99 (0.245 against threshold 0.0816; 443 items, 86 logs) and the < 20 m cell with 0.27 to 0.36 (0.141 against 0.0775). At half of X2's excess the powers are 0.27 to 0.35 and 0.01. The truth-oriented condition is not simulated. Ranges are at time k in the counts, not from the predicted ego (section 2.6).

### 6.8 Not simulated

H4 (no development transfer effect exists), H5 (no VoxelNeXt counts), H6b and H7 at their real cell layout (only the component power of 6.7), H9 (no predictor counts), loop mode (descriptive).

---

## 7. Analysis code, hash binding and outputs

### 7.1 Files bound at the freeze

**Existing, bound by SHA-256 at the freeze:**
- AV2 pipeline: `50_CODE/av2/av2_feather_v01.py`, `av2_common_v01.py`, `av2_tracker_input_v01.py`, `av2_gt_prep_v01.py`, `av2_track_v01.py`, `av2_counts_v01.py`, `av2_horizon_prep_v01.py` (it refuses AV2 input without the SHA-256 of a frozen plan; port design section 1), `test_av2_horizon_on_nuscenes_v01.py`; the AV2 track-metrics script of record `[SLOT: which of av2_track_metrics_v01 to v03]`.
- Method stage: `50_CODE/m/m_lib_v04.py`, `m_data_v04.py`, `50_CODE/x1/x1_lib_v03.py`; the T1 and T3 propagation code and CANMOT/Poly-MOT files at commit 515d0792… (M-PLAN section 12).
- K8: `50_CODE/k8/k8_sim_v02.py`, `k8_items_v02.py`, `k8_analyse_v03.py`, `50_CODE/k6/k6_sim_v02.py`, `k6_analyse_v02.py`, `50_CODE/k7/k7_fit_v01.py`.
- Inputs: detector checkpoints (299cf3b7…, 8641d838…), detection dumps under `30_DATA/av2_det_v01/`, the data manifests (56533144…, 47735085…), adapter receipts, tracker exports and their records under `30_DATA/av2_trk_v01/`, the counts file, the nuScenes M-stage results `m_result_{canmot_sc,polymot}_v04.json`, the nuScenes all-scene K7-form fit (route T), the K8 v03 exploratory analysis JSON (source of c_t and RETUNED's route-T point).
- Environment: Python, numpy and scipy versions (`50_CODE/env/canmot310`: Python 3.10, numpy 1.26.4, scipy 1.15.3 per README_K8_v02).

**New, to be written and tested before the freeze** `[SLOT: written, tested on nuScenes development scenes and synthetic data only, reviewed]`:

| File (proposed) | Role |
|---|---|
| `50_CODE/c1_av2/c1_cache_av2_v01.py` | AV2 tracker exports and propagated horizons into the K6 cache format |
| `50_CODE/c1_av2/c1_items_av2_v01.py` | K8 items on AV2, generated from `k8_items_v02.py` by asserted text replacements |
| `50_CODE/c1_av2/c1_fit_v01.py` | Route W cross-fits on AV2 folds; the route-T all-850-scene nuScenes fit |
| `50_CODE/c1_av2/c1_run_v01.py` | K8 runner with an AV2 `--prereg` path and the end-of-run hash guard |
| `50_CODE/c1_av2/c1_method_stage_v01.py` | E1-AV2 (route W) and E2-AV2 (route T) on `m_lib_v04` |
| `50_CODE/c1_av2/c1_mstarj_v01.py` | M\*J fit and joint-loss validity, from its nuScenes development implementation |
| `50_CODE/c1_av2/c1_predictor_av2_v01.py` | Trajectron++ `int_ee` on AV2 histories at 2 Hz; items; transferred DP-SCRC |
| `50_CODE/c1_av2/c1_analyse_v01.py` | `k8_analyse_v03.py` plus the AV2 binding, H1 to H9 rules, gatekeeping and Holm; writes the decision |
| `50_CODE/c1_av2/c1_oc_v01.py` | Operating characteristics of the coded rule on the real AV2 K8 counts (as K7 OC v03) |
| `50_CODE/c1_av2/c1_freeze_v01.py` | Checks tests, generators, slots (refuses any `[SLOT`), writes the hash block, the `.sha256` sidecar and a **new** `40_PROTOCOL/C1_PLAN_HASH_LOG.txt` |
| `50_CODE/c1_av2/run_c1_main_v01.sh` | One unattended run after the freeze |
| `50_CODE/c1_av2/tests/test_c1_*.py` | Tests on nuScenes development scenes and synthetic data |

`50_CODE/c1_av2/c1_power_counts_v01.py` (section 6) already exists and is bound too.

**Binding rules.** Each runner refuses to start unless the plan hash, every bound file, the inputs and the environment match. Each run record re-hashes at the end and refuses to write if anything changed (README_K8_v02 C1 guard). The analysis refuses run records whose hashes differ (README_K8_v03 N2 logic).

### 7.2 Outputs

- `60_RESULTS/c1_av2/c1_k8_{lt3d,voxelnext}_{t1,t3}_{W,T}_{decide,loop}/` run records and shards.
- `60_RESULTS/c1_av2/c1_method_stage_{t1,t3}_v01.json` (E1-AV2, E2-AV2).
- `60_RESULTS/c1_av2/c1_predictor_{t1,t3}_v01.json`.
- `60_RESULTS/c1_av2/c1_analysis_v01.json` and `csv/`, every row stamped "C1 CONFIRMATORY: AV2 validation".
- `60_RESULTS/c1_av2/c1_decision_v01.json`: H1 to H9 with their conditions, the C1 verdict, `failed_conditions`, the Holm table and the gate status.
- Deviations: `90_DECISIONS/D17_C1_DEVIATION_LOG_v01.md` (new file, after the freeze).

---

## 8. Deviation policy and failure

**After the freeze nothing in this file changes.** Every deviation is written to `D17_C1_DEVIATION_LOG_v01.md` with its reason, and the frozen analysis is reported beside any deviating one.

**Allowed without a new plan:** a technical fix that changes no statistic, threshold, population, arm, seed, fold, detector, tracker or data selection (for example a crash or a path). It is logged, reviewed and shown to reproduce the frozen code's outputs where both run.

**Never allowed:** re-running with other seeds, folds, thresholds, floors, populations, comparator sets, detectors, frame rates or logs; promoting a secondary or descriptive result; demoting a failed primary; adding AV2 data after any outcome is seen.

**If H1 fails (C1 NO-GO).**
1. The verdict is reported as NO-GO with every failed condition (`failed_conditions`), never as support.
2. A pre-specified diagnosis is reported: which condition failed (M\*'s cell flags, pooled cell, HK1c, a floor, a comparator's operability); per tracker; route W against route T; LT3D against VoxelNeXt; the A13 fallback shares; the A6 diagnostics; the margins by stratum.
3. No re-run for a better answer. A method change suggested by the diagnosis is new work: it is developed openly and confirmed on new data under a new plan.
4. "Validity shown, operability not shown" is the wording if Valid(M\*, t) holds on both trackers and part (ii) fails (K7 section 6).

**If H1 holds**, the secondary claims are tested under section 5.5 and reported whatever they show.

**After the run:** an independent results review re-derives H1 and the K8 tables with separate code (as R06, R08).

---

## 9. Open slots and decisions for the lead

| # | Slot | Needed from | Blocks |
|---|---|---|---|
| S1 | c_T1, c_T3 by D16's rule from the K8 v03 exploratory analysis (`70_TESTS/k8_expl_v02_analysis_v03/` does not exist yet) | K8 v03 analysis | H2, section 6 |
| S2 | M\*J's nuScenes development verdict (sets H3's label); its stratum-family cell definition | M\*J development run | H3, `c1_mstarj_v01.py` |
| S3 | Final counts: T3 on LT3D; T1 and T3 on VoxelNeXt; h = 2 s predicted-range strata; K8 decision-mode counts per population, cell and log | Port runs and a K8 counts pass on AV2 | Section 6 OC, floors |
| S4 | Inclusion of `int_ee_me` (nuScenes map expansion) and QCNet (GPU spend) | Researcher | H9 model, QCNet arm |
| S5 | H9's label: secondary only if the nuScenes predictor-arm plan is frozen and run before this freeze | Predictor-arm pre-registration | H9 |
| S6 | Calibration route: TW with W primary (recommended) or T primary (D15 literal) | Lead | H1, H4, H6, H7 |
| S7 | Four groups for strata and planner (recommended) against D15's three classes | Lead | Section 2.4 |
| S8 | Comparator classification: literal D14 (floor failure excludes) or stricter (floor-only stays) | Lead | Form B(ii) |
| S9 | "Price on PD7" read as the decision-mode infeasible-rate difference | Lead | H2 |
| S10 | Route-T all-850-scene nuScenes K7-form fit (new script) and RETUNED's route-T point | Me, nuScenes data only | H4 |
| S11 | New code of section 7.1 written, tested and reviewed | Me | Freeze |
| S12 | OC of the coded rule on the real AV2 K8 counts (`c1_oc_v01.py`), with the acceptance below | Me, after S3 | Freeze |
| S13 | Gatekeeping plus Holm (section 5.5) accepted by the pre-freeze review | Review | H2, H4, H5, H6b |
| S14 | 10 Hz sensitivity: run or drop | Lead | Descriptive |
| S15 | Fusion rear-axle offset source for the footprint sensitivity, or drop it | Me | Descriptive |
| S16 | Track-metrics script of record | Me | Section 7.1 |
| S17 | Adversarial pre-freeze review of this plan (D15 section 4) and its fixes | Reviewer | Freeze |
| S18 | LT3D's AB3DMOT: D15 section 3 step 3 names it as the public baseline tracker and the manuscript (V-D "Planned") cites a public KF tracker, while D16 Choice 5 runs T1 and T3 only. This plan follows D16; AB3DMOT is absent unless the lead adds it as descriptive | Lead | Manuscript V-D wording |
| S19 | Predicted H1 risk on T3 against B6 (section 6.4; P(Form B on T3) about 0.42 to 0.87 on the pooled proxy). The lead decides before the freeze: proceed as designed, or first develop a method change openly on nuScenes (D13 section 4). B6 is never removed from the comparator set | Lead, after the K8 v03 numbers | H1 |

**OC acceptance, declared now (for S12).** On the real AV2 K8 counts, per tracker, at ρ = 0.3: (a) every cell at 0.04 gives a false NO-GO on H1's validity part of at most 0.05; (b) power at least 0.80 against every record at 0.060 and every in-path record at 0.07 (K7's U060 and IP07); (c) the expected number of power-qualified cells is at least 6 in PD7 and in SD1_7 for M\*. The false NO-GO rate with every cell exactly at δ is reported, not gated (D12, R12b). If (c) fails, the lead chooses before the freeze between running with the stated floor risk, or adding AV2 train logs (download, GPU spend for detection, detections in-sample for LT3D and VoxelNeXt). Lowering F_MIN is not an option (D14 section 7).

---

## 10. What was seen before the freeze (full disclosure, to be completed at the freeze)

1. **nuScenes:** every K6 output; the K7 and K8 development checks on the 10 mini scenes; the K8 840-scene exploratory analysis once it exists (it is development evidence by design).
2. **AV2, by the author of this draft:** detector AP (`AV2_DETECTOR_NOTE_v01.md`), the port design and its probes P-a (timing) and P-b (LT3D velocity convention), and the T1/LT3D counts file. Tracker HOTA/AMOTA files exist under `60_RESULTS/av2_trk/metrics/`; they were not read for this draft.
3. **Not seen by anyone, to the author's knowledge:** any AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error. The attestation is completed and timestamped at the freeze in `C1_PLAN_HASH_LOG.txt`.

---

## Frozen files

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END
