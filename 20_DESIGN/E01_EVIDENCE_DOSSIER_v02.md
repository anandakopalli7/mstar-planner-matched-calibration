# E01: Evidence dossier for the Programme A article (v02, 1 Nov 2026)

**v02 supersedes v01** (`E01_EVIDENCE_DOSSIER_v01.md`, kept unchanged, sha256 `64a53113…`). v02 applies the adversarial review R13b (`70_TESTS/R13B_E01_REVIEW_v01.md`: 0 critical, 7 major, 18 minor). Every finding is mapped to its fix in Appendix B. No number in v01 was changed by recomputation; the corrections are to one false sentence inherited from D07 (five Poly-MOT multipliers exceed 1), one definition that disagreed with its count, one over-claim in §7, the §1 summary wording, the description of what K7 would test, an unstated denominator, and the minor citation, wording and readability items R13b lists.

**Purpose.** This document answers two questions in plain language: *what data were the experiments run on*, and *what criteria were defined and what metrics were measured*. Every number is traced to a frozen file in this folder. Nothing here is a new result: the dossier only reads, cross-checks and re-states what the frozen files contain. Where a decision report and the result file it cites disagree, both values are given and the disagreement is flagged (§5 and Appendix A).

**How to read the citations.** A tag in square brackets, for example `[X2R]`, names a file in the file index (§8), where its full path and SHA-256 are listed. A path after the tag, for example `[X2R] family_h2s.primary.<cell>.threshold`, is the JSON key path inside that file. The SHA-256 values in §8 were recomputed on 1 Nov 2026 for this dossier; where a value also appears in a frozen hash block or a review report, the two agree. Where the dossier refers to the hash recorded inside a frozen plan's own block (for example the 353-file block of the method-stage plan), it says so.

**Who ran what.** All computation was done on one laptop (CPU only). Nothing was spent on cloud compute. Every stage was planned in a document whose hash was fixed ("frozen") before the stage's real outcomes were computed, and every stage's results were then re-derived by an independent reviewer with separate code (§6).

---

## 1. The question in one paragraph

A chance-constrained motion planner is a planner that asks, for each nearby object, "with probability at least 1 − δ, will this object stay out of the space I am about to use?" (here **δ = 0.05**, so a 5 % allowed risk per constraint) and answers it with a safety margin computed from the object's predicted position **and its predicted uncertainty** (a covariance matrix). In a typical autonomous-driving stack, that covariance comes from a multi-object tracker: a Kalman filter that fuses detections over time and that can extrapolate its state and covariance into the future with its own motion model. The question of this programme is whether that extrapolated covariance is **calibrated for the planner's constraints** — whether the margin the planner computes along the direction *toward the ego vehicle* is **exceeded** (the true object is closer than the margin allows; §3.2) only 5 % of the time — and, if it is not, whether the covariance can be **recalibrated with a finite-sample guarantee** and whether doing so helps the planner. The programme's answers, in order: the extrapolated covariance of a 2026 covariance-aware tracker is mis-shaped for in-path cars (too narrow sideways, far too wide along the direction of travel, concentrated in turning cars); the standard filter-consistency statistic (**NEES**, the normalised estimation error squared; §3.3) does not point to the right fix, and no single scalar can fix the shape without paying several metres of unnecessary longitudinal margin; a stratified conformal recalibration (**DP-SCRC**, decision-projected stratified conformal risk control; §4) is **not significantly above δ** on held-out logs and on log-disjoint validation scenes on three tracker settings, where the pooled single-threshold conformal correction is; in a closed-loop study **no DP-SCRC cell was flagged on the population it was calibrated for**, and the planner was left without a feasible plan less often than with the four tested practitioner and certified alternatives (B0, B1, B4, B9), but the pre-registered rule returned NO-GO because one tracker had too few well-powered cells, and on constraints outside the calibrated population DP-SCRC exceeded δ in several cells.

---

## 2. Data

### 2.1 The dataset

| Item | Value | Source |
|---|---|---|
| Dataset | nuScenes, version **v1.0-trainval** (metadata files dated 22 Mar 2019 in the local copy; licence file present). The trainval release has 850 driving scenes of about 20 s each, with human-annotated 3-D boxes at **keyframes every 0.5 s (2 Hz)**. A "log" is one continuous drive; a scene is a 20 s cut from a log. | `30_DATA/nuscenes/v1.0-trainval/` [SCENE], [NUSC-META] |
| Official splits used | **train: 700 scenes from 50 logs. val: 150 scenes from 18 logs.** No log is in both splits (verified by R06 and R08). | [M-PLAN] §2; [R06] §1; [SCENE] |
| Development subset | The 10 scenes of the **v1.0-mini** split (a subset of trainval). They were used only to develop the closed-loop harness and were excluded from every confirmatory K6 analysis (840 = 850 − 10). | [K6-PLAN] §3; [MINI-META]; [R10] §1 |
| Ground truth used | The 7 nuScenes tracking classes (car, truck, bus, trailer, pedestrian, motorcycle, bicycle), each box with ≥ 1 lidar + radar point; bicycle-rack boxes used to exclude parked two-wheelers; ego pose at the LIDAR_TOP keyframe. Train: **28,130 keyframes, 725,431 annotations, 2,439 rack boxes**. Val: **6,019 keyframes**. | [X2-PLAN] §3; [X1-PLAN] §1; [GT-TRAIN], [GT-VAL] |
| Ego motion for the closed loop | The logged ego path resampled at **20 Hz**. | [K6-PLAN] §2; [EGO20] |

**Class groups.** The seven classes are grouped into four: **car**; **pedestrian**; **two-wheeler** (motorcycle, bicycle); **large vehicle** (truck, bus, trailer). [X1-PLAN] §5; [XLIB] lines 26–27 (`GROUP`).

**Range bands.** The distance from the object's estimate to the ego centre: **< 20 m, 20–40 m, ≥ 40 m**. For the 2 s family it is the *predicted* range at the horizon. [X1-PLAN] §5.

### 2.2 The detections

All three tracker settings consume the **same** detections: the **CenterPoint** lidar detector (the "flip" test-time-augmentation variant), 10 lidar sweeps, with velocity, from the researcher's archive. The detector was **trained on the nuScenes train split**, so train detections are **in-sample** for the detector and val detections are out-of-sample.

| File | SHA-256 | Size |
|---|---|---|
| `infos_val_10sweeps_withvelo_filter_True.json` | `4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e` | 312 MB |
| `infos_train_10sweeps_withvelo_filter_True.json` | `547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145` (equals CANMOT's own `PAPER_INPUT_HASHES['train']`) | 1.48 GB |

Sources: [DET-RECEIPT], recomputed in §8; [X1-PLAN] §1; [X2-PLAN] §3. The detections were split into per-scene subsets for parallel tracking (3 workers for val, 12 for train) with each scene kept whole; the split receipts record the source hash and every subset's hash and scene list [SPLIT-VAL], [SPLIT-TRAIN].

### 2.3 The trackers (three "settings")

| Setting | Tracker and configuration | What is tuned on what | Source |
|---|---|---|---|
| **T1** | **CANMOT** (Osterburg et al., arXiv 2026, "IROS 2026" in the decision reports), experiment `paper/local/canmot/sc`, commit `515d0792…`, devkit `e4818ff9…`. An extended Kalman filter with a **constant-velocity (CV) motion model** for every class and a process-noise matrix Q rotated into the box frame. | **Q was tuned by Bayesian optimisation for tracking accuracy (AMOTA) on val**; the measurement noise R is the trainval sample covariance. So T1 is tuned in-sample on val, and Q is out-of-sample on train. | [X1-PLAN] §1; [X2-PLAN] §3; [M-PLAN] §2 |
| **T2** | CANMOT, experiment `paper/local/sample/trainval`: same filter and R, but **Q is the trainval sample covariance of the CV model's one-step residuals** (a data-estimated Q). | Same detections and association as T1; only Q differs, so T2's errors differ from T1's only through the Kalman gain. It checks that conclusions do not hinge on the BO-tuned Q. | [M-PLAN] §2 |
| **T3** | **Poly-MOT** (Li et al., IROS 2023), run through CANMOT's `paper/baseline/poly_mot`: an EKF with a **constant-turn-rate-and-acceleration (CTRA) model** for cars, buses, pedestrians and trucks and a linear constant-acceleration (CA) filter for bicycles, motorcycles and trailers, with Poly-MOT's own Q and R (CTRA Q is the identity). | A different motion-model family, filter, Q and R on the same detections, association and life cycle. Its exported "velocity" field held (speed, acceleration); the loader rebuilds (vx, vy) from the CTRA state (median error for moving cars 7.22 m/s before, 0.74 m/s after; T1's is 0.71 m/s). | [M-PLAN] §2; [D07] §1; [D08] |

Shared by all three: the CenterPoint detections, the score filter and NMS, the association metrics and life cycle (Poly-MOT's published values, selected on nuScenes val), the scenes, logs and ground truth, and the pairing code. The decision reports therefore forbid the phrase "three independent trackers" [D07] §4.

### 2.4 What a "record", a "pair" and an "item" are

- **Record.** One exported track at one keyframe: position, size, yaw, velocity and the 2-D position covariance. Two counts exist and both are used below, so both are defined here:
  - **Export totals (all keyframes, frame 0 included).** Val: **381,553 records over 6,019 keyframes**; train: **1,839,331 records over 28,130 keyframes** (T1). These are the integrity-gate counts `Q0.records` and the figures the export, horizon-identity and K6-cache files use. [X1R] `Q0`; [X2R] `Q0`; [H8-ID]; [K6-ITEMS-T1-TRAIN].
  - **Analysis records (k ≥ 1).** Frame 0 has no ego-motion history, so every analysis population starts at keyframe 1: val **373,702** (= 381,553 − 7,851 frame-0 records); train **1,800,482** (= 1,839,331 − 38,849). **All cell tables in §5 are built from these.** [X1R] `pairing.records_k_ge_1`, `pairing.frame0_records`; [X2R] same.
- **Pairing to truth.** Scenes are processed in time order. At each keyframe, for each class separately, tracks are matched to annotated objects of the same class by Hungarian assignment on bird's-eye-view centre distance with a **2 m gate**; a pair then persists for the track's life. A record is **censored** when its object has no qualifying annotation. Misclassified tracks stay unpaired, so every analysis covers **matched true positives only**. Flags record whether a pair is *contested*, a track's *first* record, a *duplicate* (another same-class track within 1 m), or drifted beyond the gate. [X1-PLAN] §3.
- **Item.** One (record, axis) pair that passes the separating-axis filter (§3.1). A record contributes 0, 1 or 2 items.
- **In-path share paired (Q1).** On val 63.9 % of in-path records were paired; on train 67.4 %. [X1R] `Q1_paired_share_of_inpath`; [X2R] same.

### 2.5 The ego corridor and "in-path"

The planner cares about objects it might meet. "In-path" was therefore defined, **from estimates only** (nothing about the true future is used), as follows ([X1-PLAN] §7; code in [XLIB] `ego_corridor`, `object_in_path`, lines 75–97):

1. **Ego motion** is estimated from the current and previous keyframe poses: speed (signed by the heading) and yaw rate.
2. **Ego corridor.** The ego's rear-axle pose is extrapolated for 0–4 s in 0.5 s steps with a constant-turn-rate-and-velocity (CTRV) model. At each step the ego footprint (4.1 m × 1.8 m, centred 1.39 m ahead of the rear axle, **inflated by 0.5 m on every side**) is placed; the union of these nine rectangles is the corridor.
3. **Object sweep.** The tracked object's box is moved at its estimated constant velocity over the same nine steps.
4. **Rule.** The object is **in-path** if any of its swept boxes intersects the corridor. A cheap distance test skips objects that cannot reach the corridor.

In-path is computed for every record. The analysis population of X1, X2 and the method stage is the in-path, paired, uncensored items. R11b later observed that 61–63 % of in-path paired tracks at planner decision times are *behind* the ego (following traffic), a property of this definition [R11B] O2.

### 2.6 The 2 s extrapolation ("h2s")

The planner consumes a prediction, not the current estimate. The study therefore builds, for every record at keyframe k, the tracker's own **prediction 4 keyframes (2 s) ahead**: the state and covariance are propagated with that tracker's own motion model and process noise, **with no measurement updates** (the same algebra as the filter's `predict`). The truth for that prediction is the paired object's annotation at k + 4; a pair is censored at the horizon if that annotation is missing, has no points, or lies in a bicycle rack. The ego pose at k + 4 is the **CTRV prediction from keyframes k − 1 and k**, not the logged future pose (a human driver chose that pose knowing the true object positions). [X1-PLAN] preamble and §2. R06 re-propagated 180 records by its own code and matched the horizon file **exactly** (maximum relative difference 0.0) [R06] §1. Predictions at 1 s and 4 s were exported for description only; the closed-loop stage later exported 8 steps (0.5–4 s) and verified they reproduce the 2 s files record for record (`mismatch 0` on all four files, 1,839,331 and 381,553 export records) [H8-ID].

R06 M3 adds a qualifier the article must carry: this 2 s covariance is a **constructed open-loop extrapolation**. CANMOT does not output it, and its Q was tuned for one-step association; Q alone supplies about 63 % of the lateral and 75 % of the longitudinal 2 s variance [R06] §5.

### 2.7 Motion state (added at the method stage)

Each item is also labelled with a **course-change state** computed from the track's own estimates: **static** if speed < 1.0 m/s; otherwise **new** if the course-over-ground turn rate is undefined (no history); otherwise **turning** if |turn rate| ≥ 0.10 rad/s; otherwise **straight**. The turn rate is the change in the direction of the track's own displacement between two consecutive intervals, divided by the time between their midpoints. The code uses the records at **k − 4, k − 2 and k** when the k − 4 record exists (midpoints 1 s apart) and otherwise **k − 2, k − 1 and k** (midpoints 0.5 s apart); k − 1 is used only in the fallback. It depends on positions, not on the tracker's yaw. [M-PLAN] §4; [MLIB] `motion_features` (the `for j in (2, 1)` loop), `motion_state`. The plan warns that at low speed position noise reads as a course change: in the run, 18–20 % of cars at 1–3 m/s and 3–7 % at ≥ 8 m/s are "turning" on train, and 45–57 % of pedestrians [MR-T1]…[MR-T3] `turning_share_by_speed_band`; [D07] §5.

### 2.8 Which data were used in which stage, and what was in-sample

| Stage | Scenes used | Role | What was seen before | In-sample caveats | Sources |
|---|---|---|---|---|---|
| **X1** (discovery) | **150 val scenes, 18 logs**, T1 only | A pre-registered audit of calibration at t0 and at 2 s | The archive had looked at val before (an exploratory NEES study), and T1's Q was tuned on val. X1 is confirmatory with respect to its plan, not with respect to the data (its own words). | Detector out-of-sample; tracker Q in-sample on val | [X1-PLAN] §1; [X1R] |
| **X2** (confirmation) | **700 train scenes, 50 logs**, T1 only | A new hypothesis from X1's descriptive 2 s result, tested on data sharing no scene or log with val | Nothing of CANMOT's calibration on train had been examined before the plan. One pre-freeze synthetic test used real train motion and previewed the same decision; the decision rule and the freeze-and-run script were fixed before it (D06). | Detector **in-sample** on train; Q out-of-sample; R in-sample (trainval) | [X2-PLAN] §1, §3; [D06]; [X2R] |
| **Method stage (M)** | **E1:** 700 train scenes, 20 repeated 5-fold splits by log (each fold's thresholds fitted on the other 4 folds). **E2:** fitted on all 700 train scenes, evaluated on the 150 val scenes. T1, T2, T3. | Validity on held-out logs, transfer to log-disjoint val, baselines, efficiency | T1's train and val outcomes were analysed coarsely in X1/X2, so T1's B0, B1, B4 and turning results are "largely foreknown". T2 and T3 outcomes had never been computed. | E2 is a transfer under three confounded shifts: new logs; detector in-sample → out-of-sample; and T1/T2 parameters fitted partly on val | [M-PLAN] §2, §6; [MR-T1]…[MR-T3] |
| **K6** (closed loop) | **840 trainval scenes (850 − 10 mini), 68 logs**; T1 and T3. Calibration thresholds cross-fitted over 5 log folds on all 850 scenes (seed 20261101) at each of 8 steps; each scene is evaluated with thresholds fitted on the other folds. **K6's M\* is therefore a new cross-fit (deployed output with score ≥ 0.4, 8 steps), not the method stage's frozen rule; its thresholds differ from D07's.** | In-loop validity, practitioner failure, planner infeasibility; closed-loop estimates | The 10 mini scenes carried 9 development iterations; HK3's endpoint was chosen after development. No confirmatory episode had been run. | All 850 scenes contribute to calibration (cross-fitted); the score threshold 0.4 was chosen from the ground-truth pairing rates of worker 0's 59 train scenes (pairing rates only) | [K6-PLAN] §0, §1, §3; [K6R]; [K6-FITS-T1], [K6-FITS-T3] |
| **K7** (built, not run) | The same 840 scenes; calibration items from 850 scenes (T1: 1,606,994 items, T3: 1,613,073; 2.6 % and 2.4 % **of the calibration items** are in-path) | Planner-matched calibration | All K6 outcomes on the 840 scenes were seen. **B0 and Z0 are fit-free, so their K7 outcomes equal K6's and were seen** (B0 infeasible rate 0.338 on T1, 0.764 on T3). On the development scenes **99.7 % of M7's PD7 records have a calibration item with the identical residual** (R12 Q3), so K7 is "not independent of its own calibration". No K7 outcome on any confirmatory scene has been computed (attested). | A second look at seen data | [K7-PLAN] §0, §2, §13; [K7-LOG]; [K7-IT-T1], [K7-IT-T3] |

**Population sizes actually analysed.**

| Quantity | Value | Source |
|---|---|---|
| X1 (val) in-path paired records | 3,892 of 6,092 in-path records | [X1R] `pairing` |
| X2 (train) in-path paired records | 18,599 of 27,613; 83,239 censored at the 2 s horizon, 50,809 with no future frame | [X2R] `pairing`, `horizon_rows` |
| X2 decision cells at 2 s (items / scenes) | car < 20 m lateral 3,396 / 442; car 20–40 m lateral 1,229 / 219; car < 20 m longitudinal 8,038 / 529; car 20–40 m longitudinal 3,522 / 345 | [X2R] `family_h2s.primary` |
| Method stage E2 (val) items evaluated | T1 4,262; T2 4,044; T3 4,045 | [MR-T1]…[MR-T3] `E2_h2s.all.n_items_eval` |
| K6 deployed tracks (score ≥ 0.4) | 512,367 of 1,839,331 train export records kept (T1) | [K6-ITEMS-T1-TRAIN] |
| K6 primary population PD records (M\*) | T1 28,140 records in 637 scenes; T3 25,953 in 637 scenes | [K6R] `decide.*.populations.PD_primary.pooled_by_arm.Mstar` |
| K6 closed-loop episodes entered / with progress defined | 2,371 per arm per tracker (of 2,520; 149 excluded by entry conflict) / **2,100** (logged travel ≥ 10 m) | [K6R] `loop.*.outcomes.*.episodes`, `progress_episodes`; [R10] §1, §2e |

---

## 3. Criteria and metrics

Every term below is defined the first time it is used, with the file that fixes the definition.

### 3.1 The projected error and the toward-ego projection

- **Ego centre** c_e: the rear-axle pose moved 1.39 m forward. Footprint 4.1 × 1.8 m, inflated by 0.5 m. [X1-PLAN] §4.
- **Object axes.** From the tracked box's yaw ψ: the **longitudinal axis** a_L = (cos ψ, sin ψ) with half-extent l/2 and the **lateral axis** a_T = (−sin ψ, cos ψ) with half-extent w/2. These are the planner's separating directions for a box-shaped obstacle. Note (R11b O1): they are the *tracked* box's axes, so on T1 a mis-oriented box gives a mis-oriented "lateral" axis [R11B].
- **Separating-axis filter.** An axis is kept for a record only if |aᵀ(c_e − m̂)| > h_obj(a) + h_ego(a): along that axis the estimated object and the inflated ego footprint do not overlap. This uses estimates only.
- **Toward-ego orientation.** a\* = a · sign(aᵀ(c_e − m̂)), so that positive error means the object is closer to the ego than the tracker says.
- **Statistic.** **U = a\*ᵀ(X − m̂) / √(a\*ᵀ Σ̂ a\* + σ_a²)**, where X is the ground-truth centre, m̂ the estimate (or 2 s prediction), Σ̂ its 2-D covariance and **σ_a = 0.10 m** an assumed annotation noise (0.20 m and 0 are sensitivities). Under a calibrated Gaussian, U > z₀.₉₅ = 1.645 happens 5 % of the time. [X1-PLAN] §4.
- **D** = a\*ᵀ(X − m̂) is the toward-ego **projected error** in metres; **sd** = √(V + σ_a²) with V = a\*ᵀΣ̂a\*. A planner margin m is **exceeded** when D > m. [M-PLAN] §3.

### 3.2 The exceedance rate E at δ = 0.05

- **E (record-weighted):** the share of items in a cell with U > 1.645 (equivalently D > 1.645·sd for the raw covariance, or D > margin for a recalibrated one). **Target: 0.05.** This is the statistic on which the X1 and X2 verdicts are taken. [X1-PLAN] §8.
- **E (scene-weighted / scene-level rate):** first the exceeded share within each scene, then the mean over scenes that have items in the cell. This is the **primary estimand from the method stage onward**, because scenes are the sampling unit and the conformal guarantee is scene-weighted. [M-PLAN] §7; [K6-PLAN] §4.1.
- **The "price" quantities** (P01 Theorem 4): for a cell, m̂ is the 0.95 quantile of U; the **extra margin** Δ = (m̂ − max(1.645, m⁰))·SD in metres, where m⁰ is the 0.95 quantile of U under the orientation null (§3.4) and SD the median sd in the cell; the **needed variance factor** s is the smallest multiplier of Σ̂ that brings E to ≤ 0.05. [X1-PLAN] §10.

### 3.3 NEES

The **normalised estimation error squared**, ε = dᵀ(Σ̂ + σ_a²I)⁻¹d with d = X − m̂, is the standard filter-consistency statistic. For a calibrated 2-D Gaussian its mean (**ANEES**) is 2. Verdict per class group × range, with a scene-bootstrap 95 % CI (B = 2000): **OVERCONFIDENT** if the lower bound > 2, **UNDERCONFIDENT** if the upper bound < 2, else **CONSISTENT**. A NEES-guided correction multiplies **Σ̂ + σ_a²I** (the same matrix the NEES is computed on) by **k = ANEES/2**. [X1-PLAN] §9; [X2-PLAN] §2 step 3.

### 3.4 Bands, bootstraps and verdicts

- **Scene-cluster bootstrap.** Scenes are resampled with replacement (B = 2000, seed 20261030 in X1/X2) and every statistic is recomputed; the standard error is the bootstrap SD. [X1-PLAN] §8.
- **Log-cluster bootstrap.** Logs are resampled instead of scenes, so that scenes from the same drive move together. It was a sensitivity in X1/X2 and the **primary inference in the method stage and K6** (B = 2000). [M-PLAN] §6; [K6-PLAN] §7.
- **Simultaneous sup-t band.** For a family of cells, one quantile q of the maximum standardised deviation across the family is taken from the bootstrap; every cell's bound is estimate ± q·SE. This controls the chance that *any* cell in the family is wrongly flagged. The q values actually used, so that a reader can recompute a bound from a table's SE: X1 two-sided 97.5 % bands (Bonferroni over its two families), q = 2.76 (t0) and 2.85 (h2s) [X1R] `family_*.primary._q`; X2 two-sided 95 % over 4 cells, q = 2.48 [X2R] `family_h2s.primary._q`; method stage one-sided 95 %: fixed-rule M\* family q = 3.40–3.46, refit-CV M\* family q = 4.50–4.83 (R08 m7: "4.5–4.8 against 3.4"), refit-CV paired families q = 2.19–4.57, E2 M\* cells q = 3.31–3.74 [MR-T1]…[MR-T3] `E1_h2s.fixed.methods.Mstar.q_lower`, `E1_h2s.refit.methods.Mstar.q_lower`, `E1_h2s.refit.paired.*.q`, `E2_h2s.cells.methods.Mstar.q_lower`; K6 one-sided 95 %: all-evaluable 3.23 (T1) and 3.20 (T3), power-qualified 2.72 and 2.52, SD1 3.00 and 3.14, SD2 3.26 and 3.21 [K6R] `decide.*.HK1a_Mstar_all_evaluable.q`, `HK1a_Mstar_power_qualified.q`, `populations.*.cells_by_arm.Mstar.q`.
- **Verdicts (X1/X2), on the record-weighted E.** A cell **FAILS** if its lower bound exceeds max(0.05, E⁰); **OVERCOVERS** if its upper bound is below 0.05; otherwise **CONSISTENT**. A cell with zero bootstrap SE is judged on its point value and flagged.
- **Orientation null E⁰.** A perfectly calibrated tracker would still show more than 5 % toward-ego exceedances, because orienting the axis *toward the ego on the estimate* selects a biased sign. E⁰ is this artefact's size at the cell's own geometry, computed before any truth is read by perturbing the estimates with their own covariance (20 draws per item); m⁰ is the matching 0.95 quantile of U. The FAILS threshold is therefore max(0.05, E⁰): about 0.078–0.082 for the X2 lateral cells. A separate **truth-oriented** analysis (orientation and filter computed from the true centre, threshold 0.05) must also FAIL, which excludes the artefact entirely. [X1-PLAN] §2, §6; [X2R] `family_h2s.orientation_null.<cell>.E0`, `.m0`, and `family_h2s.primary.<cell>.threshold`.
- **Flag (method stage, K6).** A cell is **significantly under-covered / flagged** when its one-sided simultaneous 95 % lower bound exceeds δ = 0.05 (or SE = 0 with estimate > δ). [M-PLAN] §7; [K6-PLAN] §5.
- **FWER check.** Before each freeze the family-wise false-FAILS rate of the band was simulated at the observed per-scene counts with scene random effects; the pass limit is the nominal level plus 2 Monte Carlo SE. X1: 0.002 against a limit of 0.0390 (nominal 0.025) [X1-FWER]; X2: P(any FAILS) = 0.024 (τ = 0.5), 0.004 (τ = 1.0) against a limit of 0.0695 (nominal 0.05) [X2-FWER].

### 3.5 Evaluable cells and the n_min = 19 floor

- **Verdict-eligible cell (X1/X2):** ≥ 39 distinct scenes (Proposition 6's "practical size"). [X1-PLAN] §5.
- **Evaluable cell (method stage, K6, K7):** records in ≥ 39 scenes **from ≥ 8 logs**. [M-PLAN] §7; [K6-PLAN] §5.
- **Own-threshold floor n_min = 19.** A conformal risk-control threshold at δ = 0.05 exists only if the cell has ≥ 19 calibration scenes (1/(n+1) ≤ 0.05). Below that the stratum takes the threshold of the first coarser level that has 19. [M-PLAN] §5; [MLIB] `N_CRC = 19`, `fit_hier`; [P01] Prop. 6.

### 3.6 The conformal risk-control (CRC) threshold

For a cell with n calibration scenes, ĉ is the **smallest observed U** such that n/(n+1) · (mean over calibration scenes of that scene's share of items with U > ĉ) + 1/(n+1) ≤ 0.05. The deployed margin is ĉ·sd. Under exchangeable (i.i.d.) scenes the expected scene-level exceedance on a new scene is ≤ 0.05 (Angelopoulos et al. 2024, applied in P01 Thm 5 and P02 PM1). The guarantee is **marginal over calibration** and holds **per stratum with its own threshold**; fallback strata inherit only the coarser cell's guarantee. [M-PLAN] §5; [P02] PM1; [XLIB] `crc_threshold`.

### 3.7 The pre-registered decision rules

**X1, G1 (D03 criterion "the problem exists on real data").** G1 holds if in at least one family (t0 or h2s) some eligible cell satisfies **all** of: (a1) FAILS against max(0.05, E⁰) at σ_a = 0.10 m; (a2) the one-sided 98.75 % lower bound of the extra margin Δ exceeds h₀ = 0.10 m; (a3) still FAILS at σ_a = 0.20 m; (a4) still FAILS with contested records excluded; (a5) FAILS in the truth-oriented analysis; **and** (b) NEES does not flag it correctly (b1: the group's NEES is CONSISTENT or UNDERCONFIDENT; or b2: NEES ranks another, non-failing group as significantly worse). [X1-PLAN] §15.

**X2, fixed sequence at α = 0.05** ([X2-PLAN] §2). Four decision cells: in-path cars, < 20 m and 20–40 m, lateral and longitudinal, at 2 s. One 95 % sup-t band over these 4 cells.
- **H1 (lateral under-coverage):** for at least one range bin the lateral cell meets (a1)–(a5) above, with (a2) at the one-sided 97.5 % level.
- **H2 (price of one scalar):** let s_lat and s_long be the smallest variance factors bringing the lateral and longitudinal cells to ≤ 0.05; the **price** is the median over longitudinal records of 1.645·[√(s_lat·V + σ_a²) − √(s_long·V + σ_a²)], the unnecessary longitudinal margin any single scalar that fixes the lateral tail imposes. H2 holds if its one-sided 97.5 % lower bound > 0.10 m.
- **G1 (X2) holds iff H1 and H2 both hold in at least one bin.**
- **H3 (NEES misdirection), tested only if G1 holds:** apply k = ANEES/2 to Σ̂ + σ_a²I; H3 holds if the lateral exceedance after scaling has a lower bound > 0.05, **or** the longitudinal margin it adds has a lower bound > 0.10 m.

**D05 GO criteria (programme level).** G1 the problem exists on real data; G2 it is not already solved; G3 a definite proof path; G4 a feasible evidence path. [D05].

**Method stage, per tracker setting, at 2 s** ([M-PLAN] §7–§8).
- **HM1 (consistency):** M\* is flagged in no E1 cell, under the fixed-rule and the refit-CV inference.
- **HM6 (transfer):** (a) M\* flagged in no E2 cell; (b) the pooled val cell ("all val items") not flagged. The bias-corrected upper bound against δ + 0.03 is reported, not decided.
- **A baseline fails in a cell** when, on the **refit-CV inference** (a bootstrap that re-runs the whole cross-validated fit on resampled logs, so it carries calibration randomness), all three hold: the baseline is flagged there; M\* is not; the paired difference (baseline − M\*) is significantly positive.
- **HM2:** each of B1, B4, B9 fails in ≥ 1 E1 cell. **HM2b:** the same for B5, B7, B8, B10. **HM3:** B6 fails in ≥ 1 single-stratum car *turning* cell (confirmatory on T3 only; foreknown on T1).
- **METHOD GO-A:** HM1 and HM6 on T1, T2, T3; the **same** practitioner baseline fails on T1 and T3; HM3 on T3. **GO-B:** as GO-A without HM3 on T3. **NO-GO:** anything else. Probability of a false NO-GO from HM6 alone: 1 − (1 − 0.03)²(1 − 0.01) = 0.07.

**K6, per tracker, decision mode** ([K6-PLAN] §5–§6). Code labels used below: **PD** (primary decision population: in-path, relied-on, enforced, satisfied records); **F_MIN** (the minimum number of power-qualified cells, 6); **SD1** (PD records with pair gap ≤ 5 m, "near-binding"); **SD2** (relied-on records that are **not** in-path); **SD3** (all relied-on records whatever their enforcement); **PL** (closed-loop records with sensor offset ≤ 15 m).
- **HK1a:** (i) no M\* cell flagged in M\*'s one-sided sup-t over **all** its evaluable cells; (ii) at least **F_MIN = 6 power-qualified cells**, also unflagged in their own sup-t. A **power-qualified cell** is an evaluable cell whose simulated power to be flagged at a true exceedance of **0.15** is **≥ 0.80**, computed from M\*'s record counts only under a beta-binomial with intra-scene correlation 0.5 (200 simulated datasets, seed 20261104). Non-exceedance is claimed only for those cells.
- **HK1b:** M\*'s pooled PD cell not flagged. **HK1 = HK1a and HK1b.**
- **HK2:** some practitioner arm b ∈ {B0, B1, B4} is flagged in a cell at level 1 − 0.05/3, M\* is not flagged there, and the paired difference b − M\* is positive at 1 − 0.05/3.
- **HK3:** for each b ∈ {B0, B1, B4, B9}, the one-sided log-bootstrap upper bound (level 1 − 0.05/4) of the mean per-scene difference in **infeasible-decision rate** (M\* − b) is < 0. B6 and B3 are not HK3 comparators (B6 is the motion-state option, reported only; B3 is dominated by construction).
- **K6 GO-A:** HK1 and HK3 on both T1 and T3, and HK2 on T1. **GO-B:** HK1 and HK3 on both, HK2 not on T1. **NO-GO:** otherwise, *including an HK1a family below the floor*.
- **Infeasible decision:** a keyframe at which no speed candidate satisfied all enforced constraints at the arm's full margin (the planner then backs the margin off, λ ∈ {0.75, 0.5, 0.25, 0}, and takes the emergency stop only if even λ = 0 is infeasible). [K6-PLAN] §4.2; [K6SIM] `plan_step`.
- **Primary population PD:** records at steps 0.5–2 s that are in-path (method's flag) ∩ relied-on axis (the axis with the largest gap − margin) ∩ enforced ∩ satisfied by the chosen plan. 32 cells: group × axis × motion state, pooled over range; plus the pooled cell. [K6-PLAN] §4.1.

**K7 (plan v02, not frozen).** K7 keeps K6's statistics (δ, scene-level estimand, log bootstrap, sup-t, evaluability, the power rule with 0.15 / 0.80 / ρ = 0.5 / 200 datasets, F_MIN = 6, HK3's form) but **changes what is tested and claimed** ([K7-PLAN] §5–§6, its own table "The standard, compared with K6"):
- the validity tests are applied to three populations — **PD7** (every constraint the planner relies on, in-path or not), **SD1_7** (PD7 with gap ≤ 5 m, near-binding) and **PD** (K6's in-path population) — with calibration redone on the planner's own enforced pairs, split by the in-path flag;
- **the F_MIN = 6 power floor applies to PD7 and SD1_7 only. On PD — the population on which K6 failed — condition (iv) requires only "at least 1 evaluable cell", and PD's power family is "computed … and reported, not required".** The plan labels this "**Changed: a narrower claim**": a K7 GO would claim power-qualified non-exceedance on the planner's populations, not on PD, and K6's PD floor would not be re-tested. A K7 GO therefore supports the planner-population claim only, and any statement of in-loop validity "on nuScenes" must name both K6 (NO-GO) and K7 ([K7-PLAN] §0 "Reporting constraints");
- **HK2 is changed**: B1 or B4 (recalibrated) on SD1_7 at level 1 − 0.05/2, instead of B0, B1, B4 on PD at 1 − 0.05/3; B0 is reported only, because its outcomes were seen.

### 3.8 Operating-characteristic (OC) simulations

Before each freeze, the frozen rule was run on simulated outcomes laid out on the **real record counts** (counts only; no outcome read), to measure its false-NO-GO rate and its power. These are reported alongside every verdict: X1/X2 FWER and power ([X1-FWER], [X2-FWER], [X2-POWER]); method stage OC v02–v04 ([M-PLAN] §9; [M-OC-T1], [M-OC-T3]); K6 OC v02 ([K6-PLAN] §8; [K6-OC]); K7 OC v03 ([K7-OC]).

---

## 4. Methods compared

All are rules for the **margin along an object axis**; most are written as a multiplier of sd = √(aᵀΣ̂a + σ_a²). Every calibrated method is fitted on calibration scenes only (held-out folds in E1 and K6; train in E2). Definitions: [M-PLAN] §5; margins as the planner uses them: [K6-PLAN] §2 and [K6SIM] `margins`.

| Arm | Margin | What it represents |
|---|---|---|
| **B0, raw covariance ("uncalibrated")** | 1.645·sd | The tracker's covariance taken at face value. The default in any stack that passes the Kalman covariance straight to a chance-constrained planner. |
| **B1, NEES-scaled** | 1.645·√k·sd with k = ANEES/2 per class group × range | The textbook consistency fix: inflate the covariance until the filter's NEES averages its nominal value (Bar-Shalom-style consistency tuning). It is X2's H3 correction. |
| B2, variance inflation | 1.645·√(sV + σ_a²) with the largest s needed by any L1 cell | An empirically tuned global inflation, uncertified. Pricing reference only. |
| **B3, certified single multiplier** | (max over strata of M\*'s thresholds)·sd | The one-knob certified correction: a single conformal multiplier large enough for the worst stratum. Valid in every own-threshold stratum (P02 PM3). It is a pricing reference, not a competitor: it is **dominated by M\* by construction**. |
| **B4, pooled conformal** | one CRC threshold over all items, ĉ_pooled·sd | The single global conformal correction used in **conformalised Kalman filtering** (Weisman et al. 2026, CGKF). It certifies the pooled exceedance only. |
| B5, per-axis conformal | one CRC threshold per axis (long, lat) | Ablation: strata on axis only. |
| **B6, no-motion strata** | CRC per group × range × axis (L1), with fallback | DP-SCRC **without** the motion-state layer; X2's original K5 method. The motion-state ablation. **B6c** is its certified coarse version (per L1 cell, the max of M\*'s motion thresholds). |
| B7, learned-scale conformal | M-LS's regression scale with one pooled threshold | Ablation: a learned heteroscedastic scale instead of strata. |
| B8, stratified variance matching | M\*'s strata with multiplier 1.645·√(mean U²) | Ablation: moment matching per stratum, no finite-sample term. |
| **B9, norm-ball conformal** | a fixed radius r (metres) on every axis, from one CRC on the 2-D error norm | The trajectory/error-norm conformal region of **Lindemann et al. (RA-L 2023)** fed to a planner. It certifies the stronger event "the 2-D error is inside the ball", so it is expected to over-cover any single projection. |
| B10, stratified empirical quantile | M\*'s strata, item-level 95 % quantile of U, no finite-sample term | Ablation. |
| **M\* (DP-SCRC)** | ĉ(stratum)·sd | **Decision-projected, stratified conformal risk control.** Strata (L0, 96 cells): group × range × axis × motion state. Each L0 stratum with ≥ 19 calibration scenes gets its own CRC threshold; otherwise it takes the first coarser level with ≥ 19 (L1 group × range × axis → L2 group × axis → L3 axis) — the **hierarchy** in [MLIB] `fit_hier`/`parents`. The **deployable covariance** (P02 PM2) is Σ̃ = A(Σ̂ + σ_a²I)A with A = (max(ĉ_long, 10⁻³)/1.645)·a_l a_lᵀ + (max(ĉ_lat, 10⁻³)/1.645)·a_t a_tᵀ (the 10⁻³ floor keeps A invertible when a fitted ĉ ≤ 0 and only enlarges the margin): a symmetric positive-definite matrix such that a planner using 1.645·√(aᵀΣ̃a) applies exactly max(ĉ, 10⁻³)·sd on each object axis. It is a post-processor between tracker and planner. Literature: CRC (Angelopoulos et al. 2024) + group-conditional/Mondrian conformal (Vovk 2012) + hierarchical fallback + scene-level units; what is added is the decision projection, the strata and the deployable covariance. [MLIB] `deploy_covariance`. |
| M-LS | M\* on scaled scores | A secondary arm; not recommended (M-LS/M\* ≈ 1.03, 1.07, 1.00). |
| Z0 | 0 (mean only) | Closed-loop reference: no uncertainty margin at all. |
| LOG | the delayed logged ego profile | Closed-loop reference: no planner. |

---

## 5. Results, stage by stage

### 5.1 X1 — discovery on val (150 scenes), frozen plan `ab9b8e05…`

**Verdict text** ([X1-REP]): "**Verdict on G1: NOT SHOWN, in either family.** No eligible cell FAILS against its threshold under the 97.5 % simultaneous band, so conditions (a2)–(a5) and (b) are never reached."

Integrity: Q0 passes (6,019 keyframes, 381,553 export records, C6 = 0); Q1 = 0.639. Eligible cells: 4 per family, all cars. [X1R] `Q0`, `Q1_paired_share_of_inpath`.

**Family t0 (the tracker's current output); E record-weighted**

| Cell | E (record-weighted) | Threshold max(0.05, E⁰) | 97.5 % band | Verdict |
|---|---|---|---|---|
| car < 20 m, longitudinal | 0.005 | 0.050 | [0.000, 0.010] | OVERCOVERS |
| car < 20 m, lateral | 0.042 | 0.061 | [0.001, 0.083] | CONSISTENT |
| car 20–40 m, longitudinal | 0.033 | 0.052 | [0.015, 0.050] | OVERCOVERS |
| car 20–40 m, lateral | 0.046 | 0.061 | [−0.002, 0.094] | CONSISTENT |

Source: [X1R] `family_t0.primary`. So at t0 the covariance is consistent or conservative; nothing is claimed about t0 miscalibration.

**Family h2s (2 s extrapolation); E record-weighted; s = the multiplier of Σ̂ that brings E to 0.05**

| Cell | E | Threshold | Band | Verdict | Predicted SD (m) | Needed variance factor s [95 % CI] |
|---|---|---|---|---|---|---|
| car < 20 m, longitudinal | 0.004 | 0.062 | [−0.002, 0.010] | OVERCOVERS | 3.34 | 0.25 [0.18, 0.32] |
| car < 20 m, lateral | **0.135** | 0.084 | [0.040, 0.229] | CONSISTENT | 0.67 | **5.3 [2.2, 7.4]** |
| car 20–40 m, longitudinal | 0.009 | 0.050 | [−0.002, 0.019] | OVERCOVERS | 3.34 | 0.30 [0.25, 0.48] |
| car 20–40 m, lateral | **0.175** | 0.093 | [0.078, 0.271] | CONSISTENT | 0.67 | **2.6 [1.5, 10.7]** |

Source: [X1R] `family_h2s.primary`, `family_h2s.prices.cells`. Other X1 facts: ANEES for cars at 2 s is 3.18 (< 20 m) and 3.52 (20–40 m), both OVERCONFIDENT, giving a **type II disagreement** in both longitudinal cells (NEES asks for more variance where the tail is already over-covered) [X1R] `family_h2s.nees`, `family_h2s.nees_disagreement`. The pre-registered method check K5 was supported at 2 s: stratum CRC held-out mean scene exceedance 0.004 (criterion ≤ 0.06); on the test half the uncalibrated threshold under-covered car 20–40 m lateral (0.151, one-sided 95 % lower bound 0.072) and so did the certified global multiplier (0.175, lower bound 0.098); the total margin (the sum over test records of the margin, in metres) was 4,490 for stratum CRC against 11,559 for the global multiplier and 11,674 for global inflation [X1R] `family_h2s.certification`. Heterogeneity H_m = 5.5 m [3.5, 8.4] but UNDERPOWERED by its own OC [X1R] `family_h2s.Q4`.

**Why G1 was not shown.** The 97.5 % band (Bonferroni over two families; simulated false-FAILS rate 0.002 against the file's limit of 0.0390, which is the nominal 0.025 plus 2 Monte Carlo SE [X1-FWER]), the raised orientation-null thresholds (0.084–0.093) and only 52–83 scenes per lateral cell. The lateral point values sit above their thresholds; the lower band edges do not. [X1-REP].

### 5.2 X2 — confirmation on train (700 scenes), frozen plan `41bc5a93…`

**Verdict text** ([X2R] `G1_X2`): `"G1_holds": true, "H3_holds": true, "sequence": "H1 -> H2 -> H3 at alpha 0.05; G1 = H1 and H2 in at least one range bin"`. D05's verdict: "**VERDICT: GO**. All four criteria in D03 §5 are met." [D05].

**Decision cells (h2s, in-path cars, σ_a = 0.10 m; one 95 % sup-t band over 4 cells, q = 2.48; E record-weighted is the decision statistic, E scene-weighted shown beside it)**

| Cell | E (record) | E (scene) | n items / scenes | Threshold max(0.05, E⁰) | Band | Verdict |
|---|---|---|---|---|---|---|
| car < 20 m, lateral | **0.194** | 0.141 | 3,396 / 442 | 0.0775 | [0.152, 0.236] | **FAILS** |
| car 20–40 m, lateral | **0.272** | 0.245 | 1,229 / 219 | 0.0816 | [0.205, 0.338] | **FAILS** |
| car < 20 m, longitudinal | 0.004 | 0.008 | 8,038 / 529 | 0.0646 | [0.002, 0.007] | OVERCOVERS |
| car 20–40 m, longitudinal | 0.011 | 0.019 | 3,522 / 345 | 0.050 | [0.004, 0.017] | OVERCOVERS |

Source: [X2R] `family_h2s.primary.<cell>` (fields `E_rec`, `E_scene`, `n`, `scenes`, `threshold`, `lo`, `hi`, `verdict`).

**The three steps, per bin** ([X2R] `G1_X2.steps`):

| Quantity | < 20 m | 20–40 m |
|---|---|---|
| H1 (a1)–(a5) | all true | all true |
| Extra lateral margin Δ (m), point [95 % CI] | 1.58 [1.18, 1.93] | 1.51 [1.08, 2.03] |
| Truth-oriented lateral E (threshold 0.05) | 0.154, band [0.116, 0.193], FAILS | 0.228, band [0.162, 0.293], FAILS |
| Lateral E at σ_a = 0.20 m | 0.188 FAILS | 0.260 FAILS |
| Lateral E, contested excluded | 0.195 FAILS | 0.271 FAILS |
| s_lat / s_long (needed variance factors) | 6.75 / 0.235 | 6.56 / 0.460 |
| **H2 price (m)**, one-sided 97.5 % lower bound | **11.61**, 9.81 | **10.34**, 8.24 |
| ANEES (car group), k = ANEES/2 | 4.46, 2.23 | 3.89, 1.95 |
| **H3:** lateral E after NEES scaling (lower bound) | **0.130** (0.104) | **0.172** (0.130) |
| **H3:** longitudinal margin added by NEES scaling (m) | **2.72** | **2.17** |

Sources: [X2R] `G1_X2.steps[*]`, `family_h2s.prices.cells`, `truth_oriented_decision_band`, `family_h2s.sensitivities.sigma_a=0.20`, `family_h2s.sensitivities.contested_excluded`.

**Supporting facts quoted in D05 and D13, traced:**
- "**68 % of exceedances from turning cars**": R06's own breakdown on the in-path lateral items, by ground-truth heading change over the 2 s: < 5° (3,143 items, E = 0.100); 5–15° (964, E = 0.405); 15–45° (492, E = 0.555) — cars turning ≥ 5° carry 68 % of the exceedances. Moving, non-turning, well-headed cars give 0.035 at < 20 m. **This number is from the review [R06] §3, not from the frozen result file.**
- "**An unstratified all-object average E ≈ 0.04 hides it**": the all-objects sensitivity gives lateral E = 0.0387 (< 20 m) and 0.0383 (20–40 m), both OVERCOVERS [X2R] `family_h2s.sensitivities.all_objects`. R06 M2 shows this is composition: 80 % of all-object lateral items are parked cars with E ≈ 0.002, while moving cars in the all-objects set already fail (0.157, 0.171) [R06] §3.
- Robustness: verdict-tipping annotation noise is **0.75 m** for both lateral cells (point-tipping 0.90–0.95 m) [X2R] `family_h2s.sensitivities.tipping`; gate 4 m, per-frame re-matching, contested excluded, log-cluster bootstrap, truth orientation, velocity-defined axes and the logged ego pose all keep the FAILS [X2R] `family_h2s.sensitivities.*`; [R06] §3.
- Pre-freeze simulations: FWER of the band 0.024 / 0.004 against the limit 0.0695 [X2-FWER]; power of (a1) at 0.6–1.0 × the X1 effect = 1.00 [X2-POWER].

**Deviations (D06 v02).** (1) A pre-freeze synthetic scale test built its tracks from real train ground truth and so previewed the decision (synthetic price 9.35 m against 11.61 m real). The freeze-and-run script was written 16 minutes before that leak, has no branch on the result, and ran unattended; byte identity of the plan before the leak cannot be proven from artefacts. The article must disclose this. (2) The peak-memory guard was vacuous. [D06]; [R06] m1.

### 5.3 Method stage — DP-SCRC on three tracker settings, frozen plan `6366020a…` (353 files)

**Verdict text** ([D07]): "**Verdict: METHOD GO-B.** By the pre-registered rule of plan v05 (§8; sha256 6366020a…, frozen 17:05, 353 files, no deviations), confirmed by the independent results review R08." Decision file: `"METHOD_DECISION": "GO-B"`, `K5_validity_consistency_and_transfer: true`, `K5a_practitioner_on_T1_and_T3: ["B4"]`, `K5b_motion_state_confirmatory_T3: false` [MDEC].

**Hypotheses per tracker** ([MDEC]; [MR-T1]…[MR-T3] `E1_h2s.hypotheses`, `E2_h2s.hypotheses`). "LB" and "UB" are the simultaneous one-sided 95 % lower and upper bounds of §3.4:

| | T1 CANMOT | T2 CANMOT data-Q | T3 Poly-MOT |
|---|---|---|---|
| HM1 (M\* flagged in no E1 cell; cells evaluated) | true (33 cells) | true (32) | true (34) |
| M\* mean E1 cell exceedance (scene-level) | 0.042 | 0.042 | 0.042 |
| HM6a (M\* flagged in no E2 cell) | true, **0 of 10** | true, **0 of 9** | true, **0 of 10** |
| HM6b pooled val exceedance; simultaneous LB; bias-corrected UB | **0.043**; 0.013; 0.063 | **0.044**; 0.019; 0.062 | **0.038**; 0.018; 0.051 |
| HM2 (refit-CV): cells where B4 fails | 4 car lateral cells | 3 cells | **1: car 20–40 m long straight** (E 0.104, LB 0.054) |
| HM2: B1 fails | car lat turning, both ranges | 2 cells | none |
| HM2: B9 fails | none | 1 cell | none |
| HM2b: B5 / B7 / B8 / B10 fail | 2 / 0 / 0 / 0 | 2 / 0 / 0 / 0 | 0 / 0 / 0 / 0 |
| HM3 (B6 fails in a car-turning cell) | true (car < 20 lat turning; foreknown) | true (not confirmatory) | **false** |

**E1 car cells at 2 s, scene-mean exceedance, fixed-rule point estimates** (target 0.05; [MR-T1]…[MR-T3] `E1_h2s.fixed.methods.<arm>.cells.<cell>.E_scene`):

| Cell | Setting | B0 | B1 | B4 | B6 | B9 | **M\*** |
|---|---|---|---|---|---|---|---|
| car < 20 lat turning | T1 | 0.287 | 0.224 | 0.273 | 0.142 | 0.024 | **0.046** |
| car 20–40 lat turning | T1 | 0.409 | 0.359 | 0.391 | 0.084 | 0.017 | **0.042** |
| car < 20 lat straight | T1 | 0.132 | 0.076 | 0.115 | 0.022 | 0.000 | **0.047** |
| car < 20 long straight | T1 | 0.003 | 0.000 | 0.001 | 0.036 | 0.003 | **0.049** |
| car < 20 lat turning | T2 | 0.439 | 0.225 | 0.263 | 0.156 | 0.010 | **0.047** |
| car < 20 lat turning | T3 | 0.000 | 0.017 | 0.019 | 0.110 | 0.043 | **0.044** |
| car 20–40 long straight | T3 | 0.000 | 0.070 | 0.104 | 0.058 | 0.007 | **0.046** |

All seven rows in D07's table reproduce from the files to three decimals.

**E2 (val) M\* cells that D07 singles out as unresolved:** T1 car lateral turning E = 0.087 (UB 0.155; 44 scenes, 16 logs); T3 car longitudinal turning 0.088 (UB 0.151); T2 car longitudinal static 0.077 (UB 0.184). None is flagged, and the OC says the val test catches a turning-cell exceedance of about 0.20 in 80–85 % of datasets and one of 0.12 in only 23 % [MR-T1]…[MR-T3] `E2_h2s.cells.methods.Mstar.cells`; [M-PLAN] §9.

**HM3 on T3 (the motion-state question).** B6 is at 0.110 and 0.133 in the two lateral-turning car cells against M\* 0.044 and 0.036; the paired difference is significantly positive (LB 0.022 and 0.023), but B6's own simultaneous bound (0.026 and −0.004) does not exceed δ, so HM3 is **not met**; the OC put the power at 0.15–0.60; 4 of 12 sensitivities show the failure under the fixed rule. Inconclusive, not negative. [D07] §2; [MR-T3].

**Efficiency (descriptive).** Two sets of intervals exist and both are in the frozen files:

| Ratio of mean margins | T1 E2 (val, includes calibration randomness) | T1 E1 (train, fixed rule) | T2 E2 | T3 E2 |
|---|---|---|---|---|
| M\*/B3 | 0.161 [0.121, 0.177] | 0.165 [0.160, 0.171] | 0.317 [0.197, 0.358] | 0.361 [0.127, 0.388] |
| M\*/B6c | 0.530 [0.475, 0.635] | 0.554 [0.540, 0.572] | 0.656 [0.576, 0.715] | 0.684 [0.518, 0.751] |
| M\*/B9 | 0.584 [0.513, 0.666] | 0.590 [0.568, 0.617] | 0.554 [0.495, 0.618] | 0.701 [0.595, 0.837] |
| M\*/B6 | 0.889 | 0.924 | 0.907 | 1.056 (E1: 1.110) |
| M\*/B7 | 0.975 | 1.015 | 0.979 | 1.244 |
| M-LS/M\* | 1.032 | 1.034 | 1.072 | 1.003 |

D07's table uses the E2 values ([MR-T1]…[MR-T3] `E2_h2s.all.ratios`); the decision file `efficiency_descriptive` holds the E1 fixed-rule values ([MDEC]), which R08 M4 criticised for leaving out calibration randomness. The two are different estimates from different files, not a conflict.

**The deployable recalibration is a shape correction.** T1, car < 20 m, multipliers on the projected SD (nominal 1.645): lateral turning **6.97**, lateral straight **3.06**, lateral static **0.69**, longitudinal static **0.38** [MR-T1] `E2_h2s.fit_on_all_train.Mstar`. On Poly-MOT **91 of the 96 strata have a multiplier below 1**, including **all 16 car strata under 40 m** (largest 0.87; car < 20 m lateral turning 0.31, longitudinal static 0.42), so the method shrinks an over-wide covariance there. **The five exceptions** are `car|≥40|long|straight` = **1.118** (its own L0 fit), `car|≥40|long|static`, `|turning` and `|new` = 1.118 (inherited from that L1 cell), and `two_wheeler|<20|long|straight` = **1.108** (own fit) [MR-T3] `E2_h2s.fit_on_all_train.Mstar` (value, level). D07 §2's sentence "Poly-MOT. Every multiplier is below 1" is therefore wrong in those five strata (Appendix A row 8). Poly-MOT's raw-covariance mean margin: **16.9 m (lateral 32.1 m) on E1 train**, 16.0 m (lateral 30.3 m) on E2 val, against **4.3 m (E1) / 4.4 m (E2)** for CANMOT ([MR-T3], [MR-T1] `E1_h2s.fixed.methods.B0.mean_margin_m`, `E2_h2s.all.methods.B0.mean_margin_m`; D07 quotes the E1 values without saying so).

**Pre-freeze operating characteristics** ([M-PLAN] §9; [M-OC-T1], [M-OC-T3]): a valid M\* fails HM1 in 0 % of null datasets; fails HM6 in 3 % (T1) and 1 % (T3) of 100 fresh null datasets; the probability of a false NO-GO is ≤ 0.07; the smallest per-cell exceedance detected with 80 % power (MDE80) is 0.10–0.30 in E1 and 0.15–0.30 in E2.

**Deviations after the freeze: none** [D08]. Errata in the frozen text (no effect on the run): §8 names v03 scripts (v04 ran); a stale "25 val scenes" count; per-record turning shares [D07] §5.

### 5.4 K6 — closed-loop stage, frozen plan `6446d9f6…` (97 files)

**Verdict text** ([D10]): "**Verdict: K6 NO-GO** (frozen plan v02, sha256 6446d9f6…). This is the verdict of the pre-registered §6 rule. … **The only cause.** T3's power-qualified HK1a family has **5 cells against the floor of 6**. With 6 the verdict would have been GO-A. **What did not fail.** No validity hypothesis was violated: no M\* cell was flagged in any evaluable cell (18 on T1, 17 on T3), in the power-qualified families, or in the pooled cell, on either tracker. **What this verdict is not.** It must not be reported as 'passed', as 'GO on the primary tracker', or as a failure 'only on a technicality'." Decision block: `"verdict": "K6 NO-GO"`; T1: family 7 ≥ 6, HK1a/HK1b/HK1/HK2/HK3 all true; T3: family **5** < 6, HK1a false, HK1b true, HK1 false, HK2 false, HK3 true [K6R] `decision`.

**The harness in words** ([K6-PLAN] §2; [D09]; [K6SIM]). The world is the nuScenes log with non-reactive annotated agents. Perception is the recorded CenterPoint → T1 or T3 output restricted to tracks with score ≥ 0.4, with means and covariances at 8 steps (0.5–4 s) from each class's own filter. The ego follows the logged 20 Hz path; a **speed planner** replans at every keyframe among **32 accelerate-then-brake candidates** (accelerations −4, −2, −1, 0, 0.5, 1, 1.5, 2 m/s² held for 0.5, 1, 2 or 4 s, then braking to a stop) **plus an emergency stop**. Constraints: for every considered track (centre within 60 m of the ego centre and not more than 2.05 m — half the ego length — behind it, i.e. not behind the rear bumper; `plan_step`: `dx·cos ψ + dy·sin ψ ≥ −EGO_L/2`) and every check time (every 0.25 s, **enforced up to 2 s**), the pair is safe if one object axis has gap ≥ margin, where the gap is the separation of the mean footprints minus a **0.5 m buffer**. Exemptions are decided at an arm-independent reference margin of 0 (pairs no speed choice can act on, or that an ego held at its position would already violate). The planner takes the feasible candidate with the largest mean planned position over 4 s; if none is feasible at the arm's margin, that is an **infeasible decision**, and the margin is backed off. Two modes: **decide** (one decision per keyframe from the logged state, identical across arms; carries the confirmatory tests) and **loop** (closed loop with delays 0, 1, 2 s; carries the operational estimates).

**Confirmatory results (decide mode; 840 scenes, 68 logs per tracker; all values reproduced by R10)**

| Hypothesis | T1 (CANMOT) | T3 (Poly-MOT) |
|---|---|---|
| Evaluable M\* cells / flagged | 18 / **0** | 17 / **0** |
| Power-qualified family (≥ 0.80 at 0.15) | **7**: car long static/straight/turning/new, car lat static, car lat straight (0.845), pedestrian long turning (0.81) | **5**: car long static/straight/turning/new, car lat static (0.95). Next: pedestrian long turning 0.665, car lat straight 0.58 (329 records, 91 scenes), car lat turning 0.40 |
| HK1a | **holds** | **fails** (5 < 6) |
| HK1b: pooled PD exceedance (simultaneous UB) | **0.049** (0.057); 28,140 records, 637 scenes | **0.049** (0.057); 25,953 records, 637 scenes |
| HK2 | **holds**: B0, B1, B4 flagged in car\|lat\|turning (E 0.289, 0.265, 0.297; 95 % sup-t LB 0.178, 0.149, 0.181) against M\* 0.041 (UB 0.083; 732 records, 72 scenes); paired excess +0.248, +0.224, +0.256 (LB 0.134, 0.113, 0.143) | does not hold (no practitioner arm flagged in PD); only required on T1. **Borderline:** B1 in car\|long\|turning has E 0.110 with a Bonferroni lower bound of **0.0496** against 0.05 (D10 §1; R10 §2 reports that another bootstrap seed gives 0.0501, which would flag it) |
| HK3: infeasible-decision rate, M\* vs the four tested arms | **holds**: M\* **0.159** vs B0 0.338, B4 0.330, B1 0.457, B9 0.512; one-sided Bonferroni UB of M\* − arm: −0.155, −0.146, −0.268, −0.318 | **holds**: M\* **0.222** vs B1 0.327, B4 0.359, B9 0.504, B0 0.764; UBs −0.081, −0.111, −0.243, −0.510 |
| Reference arms (not HK3 comparators, not tested) | B6 0.344, B3 0.841, Z0 0.008 | **B6 0.215 (lower than M\*'s 0.222, as foreknown from development)**, B3 0.742, Z0 0.003 |

Sources: [K6R] `decide.t1`, `decide.t3` (`HK1a_family`, `HK1a_family_power_at_0.15`, `HK1a_Mstar_all_evaluable`, `HK2`, `infeasible_rate`, `HK3`, `populations.PD_primary.pooled_by_arm`); [D10] §1; [R10] §2.

**Scope finding (descriptive populations).** On relied-on records that are **not** in-path (SD2), M\* is significantly above δ: T1 car\|long\|straight **0.088** (LB 0.069) and car\|long\|turning **0.073** (LB 0.052); T3 six cells: car\|long\|straight 0.090, car\|long\|turning 0.075, car\|long\|new 0.098, pedestrian\|long\|static 0.079, large\|long\|straight 0.101, large\|long\|new 0.097. The pooled SD2 rate is 0.036 (T1) and 0.044 (T3). [K6R] `populations.SD2_not_in_path`; [R10] E4. DP-SCRC was calibrated on in-path objects; the planner relies on many others.

**In-loop check at sensor offset ≤ 15 m (PL: closed-loop records taken while the logged ego, whose perception is replayed, leads the simulated ego by at most 15 m).** M\* pooled 0.042 (T1) and 0.047 (T3) [K6R] `loop.*.populations.PL_offset_le_15m.pooled_by_arm.Mstar`.

**Closed-loop estimates (descriptive by design).** Definitions: **progress** = s(end)/s_log(end − d), the simulated ego's travel as a share of the delayed logged travel, defined only when the logged travel is ≥ 10 m ([K6-PLAN] §3, §4.3); **infeasible-frame share** = share of planning frames with an infeasible decision; **sensor offset** = distance by which the logged ego (whose perception is replayed) leads the simulated ego. **Denominators:** the collision rates, infeasible-frame shares and offsets are over the **2,371** entered episodes per arm and tracker; **the progress means are over the 2,100 episodes with progress defined** (`progress_episodes` = 2,100 for every arm). [K6R] `loop.*.outcomes`, `progress_vs_Mstar`:

| | Z0 | **M\*** | B6 | B4 | B0 | B1 | B9 | B3 |
|---|---|---|---|---|---|---|---|---|
| Progress, T1 (over 2,100 episodes) | 0.947 | **0.845** | 0.780 | 0.758 | 0.753 | 0.720 | 0.708 | 0.672 |
| Progress, T3 (over 2,100 episodes) | 0.972 | **0.860** | 0.848 | 0.817 | 0.746 | 0.827 | 0.730 | 0.760 |
| Infeasible-frame share, T1 / T3 (2,371 episodes) | 0.003 / 0.003 | 0.214 / 0.248 | 0.346 / 0.242 | 0.307 / 0.358 | 0.315 / 0.709 | 0.389 / 0.344 | 0.453 / 0.451 | 0.780 / 0.686 |
| Tracked at-fault collisions per 1,000 episodes, T1 / T3 (2,371 episodes) | 22.4 / 20.2 | 30.8 / 29.5 | 29.9 / 24.9 | 35.0 / 26.6 | 29.5 / 27.8 | 29.1 / 24.9 | 35.8 / 31.6 | 29.9 / 30.8 |
| Median sensor offset (m), T1 / T3 | 3.7 / 2.9 | 5.8 / 5.7 | 8.0 / 5.8 | 9.2 / 7.1 | 9.4 / 9.7 | 12.5 / 6.5 | 11.4 / 10.5 | 14.6 / 9.0 |

Progress: M\* is highest of every margin arm on both trackers, every M\* − arm 95 % interval excludes 0; against B6 on T3 the difference is +0.011 [0.006, 0.017]. Collisions: Z0 (no margin) has the fewest; 94–100 % of the margin arms' at-fault collisions are within 2 s of an infeasible decision; not-at-fault collisions grow with lag from 285 (Z0) to 1,093 (B3); the delayed logged profile itself collides at fault 10 times at 1 s and 45 at 2 s [R10] §5 and E3. **No safety ranking may be drawn** [D10] §2; [K6-PLAN] §1.

**Diagnosis in D10 §3, traced.** (1) Data sufficiency, not invalidity. (2) The OC over-predicted power: it assumed 260 scenes for T1 car\|lat\|turning, the run had 72, so the predicted families of 8–11 became 7 and 5 [K6-PLAN] §8; [K6R]; [R10] E2. (3) The scope gap above. Three confidence facts from D11 ([D11]; [R11A]; [R11B]): computed precisely (2,000 datasets), T1's family is also 5; one unstated reading (power inside the qualified family's own sup-t) would give T3 7 cells and GO-A, but is circular and was rejected before the freeze; T1's lateral car cells rest substantially on mis-oriented CANMOT boxes (median heading error 40° on T1-only records; Poly-MOT about 1°). Overall confidence that the NO-GO is genuine: about 95 % [D11].

### 5.5 K7 — built and reviewed, not frozen, no confirmatory outcome

**Status text** ([D12] §4): "**Not frozen:** K7. No K7 outcome has been computed on any of the 840 confirmatory scenes (attestation in `K7_PLAN_HASH_LOG.txt`)." The hash log records the reviewed draft v01 (`51512ffe…`) and the attestation [K7-LOG]; plan v02 (`0773143c…`, the state R12b reviewed) still contains the placeholders `OC_V03_RESULTS_PENDING` and `REVIEW_R12B_PENDING` and an empty hash block [K7-PLAN].

**What exists.** Calibration items from 850 scenes and 32,449 decision states (T1: 1,606,994 items, 938,461 records, 2.6 % of items in-path; T3: 1,613,073, 938,718, 2.4 %; 99.7–99.8 % of considered pairs enforced) [K7-IT-T1], [K7-IT-T3]; cross-fitted fits [K7-FITS-T1], [K7-FITS-T3]; a one-change simulator that reproduces the frozen K6 simulator exactly on the development scenes (T-K7-1 to T-K7-6, all pass) [K7-TESTS]; the analysis `k7_analyse_v02.py` whose `hk1_rule` equals K6's code path in 300/300 synthetic datasets [R12B].

**Operating characteristics of the coded rule (counts only; `k7_oc_v03.json`)** [K7-OC]. Legend: **ρ** = assumed intra-scene correlation of exceedances; **scale 1** = the real record layout of the 840 scenes (scale 0.5 = half the logs); **A1** = false NO-GO rate when every cell is exactly at δ; **A1b** = the same at a true rate of 0.04; **U057 / U060** = power when every record is at 0.057 / 0.060; **IP07** = power when in-path records are at 0.07; **NIP12** = power when near-binding in-path records are at 0.12; **IPCLT15** = power when the in-path car\|lat\|turning records are at 0.15; **PD7 / SD1_7 / PD** as in §3.7.

| Quantity (scale 1 = 840 scenes) | T1, ρ 0.1 / 0.3 / 0.5 | T3, ρ 0.1 / 0.3 / 0.5 |
|---|---|---|
| False NO-GO rate A1, every cell exactly at δ | **0.16** / 0.13 / 0.13 | 0.11 / **0.15** / 0.06 |
| False NO-GO at true rate 0.04 (A1b) | 0.00 | 0.00 (0.005 at scale 0.5) |
| Power: every record at 0.057 / 0.060 | 0.905–1.00 / 0.985–1.00 | 0.905–1.00 / 1.00 |
| Power: in-path records at 0.07 (IP07) | 0.99–1.00 | 0.985–1.00 |
| Power: near-binding in-path at 0.12 (NIP12) | 0.985–1.00 | 0.98–1.00 |
| Power: in-path car\|lat\|turning at 0.15 (IPCLT15) | 0.90 / 0.705 / 0.50 | 0.84 / 0.61 / 0.405 |
| Evaluable cells PD7 / SD1_7 / PD | 32 / 25 / 18 | 32 / 26 / 17 |
| Power-qualified family PD7 / SD1_7 / PD | 28 / 18 / 5 | 27 / 18 / 5 |
| Acceptance | `size_ok: false` (A1 max 0.16 > 0.15), `informative_ok: true`, `floors_ok: true`, **`acceptance_all: false`** | |

Note on the family row: under K7 plan v02 §5 (iv) the PD family of 5 is **reported, not required**, so it would **not** block a K7 GO; the F_MIN = 6 floor binds only on PD7 and SD1_7, where the families are 27–28 and 18 (§3.7).

**HK3 power from the 10 development scenes (normal approximation; design effect 1 / 2 / 3.5)** [K7-OC] `HK3_power_normal_approx_from_development`: against B0, B1, B9 it is **≥ 0.998** on both trackers (every value is 0.999–1.000 except T1 vs B0 at design effect 3.5, 0.9986); **T1 against B4: 0.81 / 0.25 / 0.09** (M7 − B4 = −0.020, M7 worse in 3 of 10); **T3 against B4: 0.000** at every design effect (M7 − B4 = **+0.016**, M7 worse in **8 of 10**).

**Development check (10 mini scenes; diagnostics only)** [K7-DEV]:

| | Z0 | B0 | B1 | B3 | B4 | B9 | B6 | **M7** |
|---|---|---|---|---|---|---|---|---|
| Infeasible-decision rate, T1 | 0.008 | 0.401 | 0.483 | 0.951 | 0.179 | 0.520 | 0.248 | **0.159** |
| Infeasible-decision rate, T3 | 0.000 | 0.945 | 0.415 | 0.968 | 0.175 | 0.502 | 0.169 | **0.190** |
| Pooled PD7 exceedance, T1 | 0.493 | 0.033 | 0.015 | 0.003 | 0.070 | 0.021 | 0.056 | **0.043** |
| Pooled PD7 exceedance, T3 | 0.520 | 0.005 | 0.040 | 0.004 | **0.087** | 0.028 | 0.063 | **0.051** |
| Pooled PD exceedance, T1 / T3 | 0.417 / 0.338 | 0.000 / 0.000 | 0.000 / 0.021 | 0.000 / 0.000 | 0.003 / 0.075 | 0.032 / 0.015 | 0.029 / 0.031 | **0.017 / 0.028** |

M7's closed-loop progress on these scenes: 0.818 (T1), 0.810 (T3), no tracked at-fault collision. Reading: on T3 the recalibrated pooled B4 is more often feasible than M7 but is itself above δ on the planner's population (0.087). The decision put to the researcher (D12) was to run K7 at K6's standard (expected NO-GO on HK3 against B4 on T3) or move the confirmation to external data (recommended). D13 then set the forward plan: literature first, K8 redesign, external data, confirmation, manuscript [D12]; [D13].

---

## 6. Independent verification

Every stage was reviewed before its freeze (adversarially, by an independent subagent) and its results were re-derived afterwards with separate code. One line each; the file holds the detail. The finding counts in this table were read from each review's own summary (file and line given), not from the decision reports that cite them.

| Review | Stage | What it did | What it found (counts from the review's own summary) |
|---|---|---|---|
| R01 [R01] | Theory P01 v01, design S01 | Hostile referee of the proofs and study design | **3 critical, 16 major, 16 minor** (R01 lines 28–30); fixed in P01 v02 (fix log in `70_TESTS/R01_FIX_LOG_v01.md`) |
| R02 [R02] | P01 v02 | Second pass: a verdict on each of R01's 35 findings; re-ran the check script (exact reproduction, ALL_PASS 16 flags) | **0 new critical** (R02 line 33); residual items closed in addendum v03 |
| R03 [R03] | X1 plan v01 | Pre-freeze review of plan, code, prior art, claims; synthetic Monte Carlo of the orientation rule | **2 critical, 9 major, 25 minor** (R03 line 47); all applied in X1 v02 |
| R04 [R04] | P01 v02 + addendum, X1 §2/§4/§6/§11 | Third proof review; closed forms and Monte Carlo | **0 critical, 3 major, 11 minor** (R04 §1 table); truth-oriented condition (a5) added |
| R05 [R05] | X2 plan v01 | Pre-freeze review; executed the decision block on X1's real output | **0 critical, 5 major, 10 minor** (R05 line 42); H2 redefined as a price; band over 4 cells only |
| **R06** [R06] | **X2 results** | Re-implemented pairing, in-path, filter, orientation and bootstrap with no pipeline import; re-derived the 2 s covariance from CANMOT's config (exact); verified all 65 frozen hashes | **"G1 holds" stands**: lateral cells 0.1927 / 0.2724 against 0.1941 / 0.2718; price 11.62 / 10.32 m; **0 critical, 3 major** (claim scope: manoeuvre effect, composition, constructed extrapolation), **11 minor** |
| R07, R07b, R07c [R07], [R07B], [R07C] | Method-stage plan v02 → v05 | Three pre-freeze passes; found the Poly-MOT velocity-field defect (R07b critical), low power of validity tests, an OC acceptance that failed (27 % false HM6 failures at ε = 0.02, R07c critical) | R07 **3 critical, 11 major, 19 minor** (line 29); R07b **1 critical, 3 major, 15 minor** new (line 67); R07c **1 critical, 1 major, 13 minor** new (line 51; D07 abbreviates R07c to "1 major"); all fixed before the freeze |
| **R08** [R08] | **Method-stage results** | Rebuilt items, strata, cells, thresholds, fallback, margins and exceedances from the raw exports with its own code; re-drew the decisive bootstrap 8 times | **GO-B stands**; every deployable threshold and E2 point estimate on T1 and T3 reproduced to 10⁻¹⁷; T3 B4 lower bound 0.0547 ± 0.0013 over 8 re-draws (all flag); **0 critical, 7 major** (claim scope), **10 minor** |
| R09, R09b, R09c [R09], [R09B], [R09C] | K6 plan v01 → v02 | Pre-freeze: found an anti-monotone enforcement rule and a sensor-offset flaw (R09 critical), replaced the emergency stop with a margin back-off (R09b), checked all fixes | R09 **2 critical, 6 major, 14 minor** (its summary table); R09b **0 critical, 3 major, 11 minor** (its header); R09c **no new critical or major** (line 133), "fix first, N1–N2, then freeze" |
| **R10** [R10] | **K6 results** | Recomputed every reported number with its own code and with the frozen bootstrap weights; integrity, hashes, timeline (UTC) | **"K6 NO-GO" confirmed**, every value reproduces exactly; **4 major** claim findings (E1–E4): T1's family is seed-sensitive (13 of 20 seeds reach 6), the OC over-predicted power, collisions are replay-biased, M\* exceeds δ outside the in-path population; 5 minor |
| **R11a** [R11A] | K6 power rule | Blind re-implementation from the plan text, then audit of the frozen code; 300 alternative seeds; 13 alternative readings | Code matches text; T3 family is 5 in 300/300 seeds, 6th cell at power 0.69–0.71; T1 computed precisely is also 5; one circular reading would pass; overall confidence about 95 % |
| **R11b** [R11B] | K6 record pipeline | Re-ran all 840 scenes × 8 arms with the frozen code (6,720/6,720 summaries equal, 1.79 M and 1.74 M count rows equal); re-derived 76,065 records bit by bit with code importing no project module | No defect; T3's thinness is tracker behaviour (CANMOT heading errors manufacture T1 lateral records; both trackers carry the identical 597,310 detections) |
| R12, R12b [R12], [R12B] | K7 plan v01, v02 | Pre-freeze: found two places where the draft was weaker than K6's standard (dominance HK3; a single joint family), verified the reversal element by element (300/300), found a dropped K6 condition (N1) and an OC size gate that fails (N2) | Both "fix first"; R12 2 critical, 5 major; K7 not frozen |
| R13b [R13B] | This dossier (v01) | Traced 212 numbers, recomputed 54 hashes, checked definitions against code and plans | 0 critical, 7 major, 18 minor; all applied in this v02 (Appendix B) |
| Synthetic tests [X1-E2E], [M-SYN] | X1, M | Known-answer tests of the analysis code; the X1 test found and fixed a rule that passed by construction before the freeze | All pass; recorded with the freezes |

---

## 7. What the evidence does and does not establish

This list is the complete list of what the programme has established, theory included.

**Established (each with its qualifier):**

0. **The theory.** P01 Theorem 1 (a chance-constrained planner's premise is calibration of the toward-ego projected error along its constraint directions, conditional on the tracker's information), Theorem 2 (NEES is neither necessary nor sufficient for that premise), Theorem 4 (the price of a single multiplier or inflation knob), Theorem 5 and Proposition 6 (CRC certification from driving logs; n ≥ 19 at δ = 0.05); P02 PM1 (per-stratum validity of the CRC threshold under i.i.d. scenes), PM2 (the deployable covariance), PM3 (the certified single multiplier). Reviewed three times (R01, R02, R04) and checked constructively (ALL_PASS). Qualifier (P01's own table "what is new"): the theorems are a formalisation layer whose own contributions are modest; the article's contribution rests on the measurements. [P01]; [P02]; [R01]; [R02]; [R04].
1. **The problem exists on this stack and dataset.** On nuScenes train (700 scenes), the 2 s extrapolation of CANMOT's state and covariance with its own CV model and process noise is mis-shaped for in-path cars: toward-ego lateral exceedance 0.194 and 0.272 against 0.05 (truth-oriented 0.154 and 0.228), longitudinal 0.004–0.011. Pre-registered, frozen, replicated from a val discovery, reproduced independently to within 0.002. Qualifiers: one dataset, one detector (in-sample on train), a constructed extrapolation; the failure is concentrated in manoeuvring cars.
2. **A single scalar cannot fix the shape without a large price, and NEES misdirects.** The price is 10–12 m of longitudinal margin (lower bounds 8.2–9.8 m); the NEES-guided scalar leaves the lateral tail at 0.13–0.17 and adds 2.2–2.7 m longitudinally. Qualifier: NEES *does* flag the covariance as over-confident; it misdirects the fix, it does not miss the problem.
3. **DP-SCRC is not significantly above δ, and transfers, in open loop on three tracker settings.** Pooled held-out val exceedance 0.043 / 0.044 / 0.038 with 0 of 10 / 9 / 10 cells flagged; mean held-out-log cell exceedance 0.042; reproduced to 10⁻¹⁷. Qualifiers: "not significantly above δ", never "at most δ"; power is limited — the OC catches a 0.12 turning-cell excess 23 % of the time, and the smallest per-cell excess detected with 80 % power is 0.10–0.30 in E1 and 0.15–0.30 in E2 (M plan §9); the population is tracked, paired, still-observable in-path objects; fallback strata carry only the coarser guarantee.
4. **The pooled single-threshold conformal correction (B4) fails where DP-SCRC holds, on CANMOT and on Poly-MOT.** On Poly-MOT in one longitudinal cell (E 0.104, LB 0.054, robust over 8 re-draws, 12 sensitivities and 3 horizons); on CANMOT in four car lateral cells (foreknown). This is evidence for stratified, decision-projected CRC as such.
5. **In the closed-loop study, at identical logged states, DP-SCRC left the planner without a feasible plan less often than each of the four arms HK3 tested — B0 (raw), B1 (NEES-scaled), B4 (pooled conformal) and B9 (norm ball) — on both trackers** (0.159 vs 0.330–0.512 on T1; 0.222 vs 0.327–0.764 on T3; all eight Bonferroni upper bounds below 0), **and no DP-SCRC cell was flagged on the calibrated population** (pooled 0.049 on both; the power-qualified cells bound the exceedance below about 0.09–0.10, not below 0.05). Qualifiers: HK3's endpoint was chosen after development; T3 against B0 is near-implied and B3 is implied by construction; **B6, the certified no-motion-strata rule, was not an HK3 comparator and was slightly *more* operable than DP-SCRC on T3 (0.215 vs 0.222)**, so the statement is about the four tested arms, not about every certified alternative; the verdict of the pre-registered rule is nevertheless NO-GO.

**Not established (each stated plainly):**

1. **A confirmed closed-loop validity claim.** K6 is a pre-registered NO-GO: T3 has 5 power-qualified cells against the floor of 6 (robust over 300 seeds), and computed precisely T1 also has 5. It may not be reported as "passed", "GO on the primary tracker" or "a technicality". No post-hoc rescue (a lower floor, another seed, the own-family reading, pooled cells) may be presented as confirmatory.
2. **Validity outside the calibrated population.** On relied-on constraints that are not in-path, DP-SCRC exceeds δ in 2 cells on T1 (0.088, 0.073) and 6 on T3 (0.075–0.101). The certificate does not cover every constraint the planner relies on. K7, the fix, is built but not run; it would not re-test K6's PD floor (§3.7), and its own development data predict a NO-GO on operability against a recalibrated pooled comparator on T3.
3. **Any safety consequence.** Closed-loop collision counts are dominated by log-replay bias (non-reactive agents; the delayed logged profile itself collides at fault 45 times at 2 s); the mean-only arm has the fewest collisions. No safety ranking or calibration effect may be drawn from them.
4. **That motion-state strata are necessary.** HM3 was not met on Poly-MOT (power 0.15–0.60); the strata save 9–11 % margin on CANMOT (M\*/B6 0.889, 0.907) and cost margin on Poly-MOT (E2 6 %, E1 11 %: M\*/B6 1.056 and 1.110). They are an option with a trade-off, not a confirmed component. Nor is DP-SCRC the tightest method evaluated (M\*/B7 = 1.24 on Poly-MOT).
5. **Generalisation and purity.** Nothing transfers to other datasets, detectors, cities or deployment; the three settings share detections and association ("three independent trackers" is forbidden); the detector is in-sample on train and T1's Q on val; a pre-freeze synthetic check previewed X2's decision (D06); "lateral" means along the tracked box's axis, which on CANMOT is often mis-oriented. The literature base (arXiv only) and the closed-loop design (own, unbenchmarked) are the gaps D13 names.

---

## 8. File index

Every file cited above, with its SHA-256 recomputed on 1 Nov 2026 (`sha256sum`, this folder as root `W`). Where the value is also the one in a frozen block, sidecar or review, they agree. R13b independently recomputed 54 of these and found 54/54 matches.

| Tag | Path (under `W\`) | SHA-256 |
|---|---|---|
| [START] | `00_START_HERE.md` | `84e7c176d651e1a3ec191a7fee195937393eafb6a023233e128c39a577656432` |
| [D04] | `90_DECISIONS\D04_IEEE_ACCESS_PATH_v01.md` | `71b22c130e20632e581ff87de7a457fbe7766501a5a79e85bcebe536a1613fc8` |
| [D05] | `90_DECISIONS\D05_GO_NOGO_REPORT_v03.md` | `97d9d6de9e5d8f1d25d82d8a4edc40afaa1d2823fd97a6236a3265e577504830` |
| [D06] | `90_DECISIONS\D06_X2_DEVIATION_LOG_v02.md` | `ca9dfa50ef13d1c9d397a28626ccbe140ff50b8c2d7195b2a91774451e2c11c5` |
| [D07] | `90_DECISIONS\D07_METHOD_STAGE_REPORT_v01.md` | `213b1ec5151644e83900826ee12dee218e27cbc5771f30b25303491fa83cfa2b` |
| [D08] | `90_DECISIONS\D08_M_DEVIATION_LOG_v03.md` | `8dfe8d2e19cbbdaea546530ef188e17c478a3fa0a9809bbb626ced00bd645026` |
| [D09] | `90_DECISIONS\D09_K6_HARNESS_DESIGN_v05.md` | `73123b86336f3f4186c81b159b88b7fe1161b9974e6bee9f8ac076cf02bf3608` |
| [D10] | `90_DECISIONS\D10_K6_DECISION_REPORT_v01.md` | `a2972a20b15bec7d7e882bf39b173a160c335a0918b636363b128d45e62669a9` |
| [D11] | `90_DECISIONS\D11_K6_CONFIDENCE_AND_K7_ROUTE_v01.md` | `409788c48bf800ccf9bda4b4dbb3e6afd9f37878e3cc6126cba194c79146a8a5` |
| [D12] | `90_DECISIONS\D12_K7_PREFREEZE_DECISION_v01.md` | `b14479d3ebd45db18dc4526f70f67ad407fd92f6a1fea5a0a7620f6d766ad5da` |
| [D13] | `90_DECISIONS\D13_FORWARD_PLAN_TO_GO_v01.md` | `a2d7f8fa9a9b20d50953d23d955a05f5c6f8932c7338e8898b2f9ef7feb2141f` |
| [X1-PLAN] | `40_PROTOCOL\X1_PREREGISTRATION_v02.md` (frozen) | `ab9b8e05d1210950d06481da4cc4b202227cc859bf5b9df4a114b2d17e709485` |
| | `40_PROTOCOL\X1_PREREGISTRATION_v02.sha256` | `a3e1f936218c10d75b4e1dd2104cdca7c1b982e1704f01904898fa199e38a6ea` |
| [X2-PLAN] | `40_PROTOCOL\X2_PREREGISTRATION_v02.md` (frozen) | `41bc5a936684dab6f6978c7d54e3d34c730afe7117ce62571b87bdb40aa447bc` |
| | `40_PROTOCOL\X2_PREREGISTRATION_v02.sha256` | `db1c86c7e1457b3823f88ea36fc5ea84a0473c8d22aad9d19281c994ea70dabf` |
| [M-PLAN] | `40_PROTOCOL\M_PREREGISTRATION_v05.md` (frozen, 353 files) | `6366020a4cb8f52af0865a6bd29fd6ff5e970405eb39efb339f434fe7621d42d` |
| | `40_PROTOCOL\M_PREREGISTRATION_v05.sha256` | `3b9c5b4407b9467b090a9670ee99708f8e07f3d269bb2322d0e41e00a07fa1e9` |
| | `40_PROTOCOL\M_FREEZE_RECORD_v05.txt` | `93826a8e28d96cedade13a2fb895ec654a317925a8dfd8c692520d6214537957` |
| | `40_PROTOCOL\M_PLAN_HASH_LOG.txt` | `0a8579e161974d6626a645ae2968ea715cb516e90f226724e3cb64b3b11b6ee8` |
| [K6-PLAN] | `40_PROTOCOL\K6_PREREGISTRATION_v02.md` (frozen, 97 files) | `6446d9f6ed28ad3ea1c14ea380a53861c18811cf2017f1975d2124453d7e3e40` |
| | `40_PROTOCOL\K6_PREREGISTRATION_v02.sha256` | `4245624bba0a539780c4467e4151de9ec27f0a6cc785a1a6629f1068a8249992` |
| | `40_PROTOCOL\K6_FREEZE_RECORD_v02.txt` | `f2f58a205cb4330b18b1ae5591195f02a0c7238b4a263d6c9c1fa98a6d5a4c0a` |
| | `40_PROTOCOL\K6_PLAN_HASH_LOG.txt` | `5460b34c310c8707f25f2b74ed3efe80e97b6ad56ba5fe4c871ac3a56c6bc097` |
| [K7-PLAN-v01] | `40_PROTOCOL\K7_PREREGISTRATION_v01.md` (draft reviewed by R12) | `51512ffe07a8371b751cb799d6da4514495bd29b1ad48a36fa4779b5a5e63d4c` |
| [K7-PLAN] | `40_PROTOCOL\K7_PREREGISTRATION_v02.md` (draft, **not frozen**, placeholders present) | `0773143ca96ba9a62fc9827702221ec07ff684a54736e14a2e2d5102828a3168` |
| [K7-LOG] | `40_PROTOCOL\K7_PLAN_HASH_LOG.txt` | `9aac2b0ddaf7cf97092ffd057768b30ecae8d11efa1c0532765d9441ecc96925` |
| [X1-REP] | `60_RESULTS\x1\X1_RESULTS_REPORT_v01.md` | `c251501335efd71a424a955ec22f151de48ac0c2b09d94bad077977f8eb13e86` |
| [X1R] | `60_RESULTS\x1\x1_full_v02_result.json` | `c0e4eb0673aca4ddc2de7310ac166ab1cc1eddc33dc12379eb3e3ad70c2b2a98` |
| [X1-FWER] | `60_RESULTS\x1\x1_fwer_v02.json` | `b26a31dea09d1224d092d8df7a3eeffdca985be43b329c6d86cb45d327c89077` |
| | `60_RESULTS\x1\x1_oc_q4_v02.json` | `364527260da39c6ba99ba74fe42266ab2be96102e0f1489e92b06d1408cd0409` |
| | `60_RESULTS\x1\x1_horizon_v01.jsonl.gz` (2 s predictions, val) | `e3e5071ea83d4f3a658f05294e608c32e82a8acd3807e298c2600dce95053f70` |
| [X2R] | `60_RESULTS\x2\x2_full_v02_result.json` | `3a6a9c58f7eb4012c03588497d9005bd5f8fab0a58f595f617aa64de592e88cd` |
| [X2-FWER] | `60_RESULTS\x2\x2_fwer_v02.json` | `26d9485e7f69b56529ff14aa8d6a2ac9edb337fd7161007ea221a8ee374aa871` |
| [X2-POWER] | `60_RESULTS\x2\x2_power_v02.json` | `690af66a729330c1cbbfc925de217aea7698d9df15e9da41904a03986850b1f8` |
| | `60_RESULTS\x2\x2_horizon_v01.jsonl.gz` (2 s predictions, train) | `8da9170cc0a084198fc7aa2a6fc7aa09c9834e499da1babfaa269b8ff2df72c5` |
| [MR-T1] | `60_RESULTS\m\m_result_canmot_sc_v04.json` | `6cf1778d73be03ed32e3796765fa9d3a0d0fa795f9ecf194f5f924111b7b7201` |
| [MR-T2] | `60_RESULTS\m\m_result_sampletv_v04.json` | `8888791262d719accf85040c7881f59c82dc8d9df41f023e1207a6bc57ebcaa5` |
| [MR-T3] | `60_RESULTS\m\m_result_polymot_v04.json` | `5ea926434c493a2e5cbaa9ac2dacfda5601c00e80603825cd5868c15812331d4` |
| [MDEC] | `60_RESULTS\m\m_decision_v04.json` | `b1b67e65f7a732f1444afee389fe390eedcbe15490b5751eefc19676523133e2` |
| [K6R] | `60_RESULTS\k6_main_v02\k6_result_v02.json` | `9defb80035d853efa8f148c9081e53aa0a01e6529f0572dc38d4fbf377dc1da8` |
| | `60_RESULTS\k6_main_v02\run_record_t1_decide.json` | `d566cdef39720515bc7df887686fca36a22f35a1ab3c98852aee8850a801f22a` |
| | `60_RESULTS\k6_main_v02\run_record_t3_decide.json` | `3e3fdcc17f4e55acc564fdebde0fcb4d93d02ddf02f39a2a1dd1f57c67200ed5` |
| | `60_RESULTS\k6_main_v02\run_record_t1_loop.json` | `fbc46935fc3551e6f103ac42101796022949fa6568d9e2401c63b3fa049dec41` |
| | `60_RESULTS\k6_main_v02\run_record_t3_loop.json` | `0b61392fd6fb76bb3535f103a6f0cad66166a483a1750a698b578626f0eb887c` |
| | `60_RESULTS\k6_main_v02\counts_t1_decide.npz` | `34f0664fcc718cd7b8937a2514412ee183994fca61e9b52ef33ad610654c7dc9` |
| | `60_RESULTS\k6_main_v02\counts_t3_decide.npz` | `49b643be3129f1a1e3d398291321362eb391815b13444045d1124e29eab4b2d5` |
| | `60_RESULTS\k6_main_v02\episodes_t1_decide.jsonl` | `7ed17187163d24c8a85cb6157b5eacce61621cd3be2d09b88fb6be6181cd19ce` |
| | `60_RESULTS\k6_main_v02\episodes_t3_decide.jsonl` | `6481e5dca6fd4da99695706370ee81366cd4563f259b0661ec9440ea95f1ed3d` |
| | `60_RESULTS\k6_main_v02\episodes_t1_loop.jsonl` | `fc9d9b7e311edfdb30f8314cc2f6c16a1319bb089bc97c17190b62d3ec917759` |
| | `60_RESULTS\k6_main_v02\episodes_t3_loop.jsonl` | `f7fca06e8d68b8e184106ff6fb38f84db0062c6ce3f78b9f9b43dcd10d2b5a31` |
| [K6-FITS-T1] | `60_RESULTS\k6_items_v01\k6_fits_t1_v01.json` | `df2beb2630017b41ab9b9d29181fb8fcdf13076e33bccfc68416c5165dd4bd4c` |
| [K6-FITS-T3] | `60_RESULTS\k6_items_v01\k6_fits_t3_v01.json` | `c771b0b5483280d1bf8766f03809a8e629749acbd188ee7dbe0c994d414c127b` |
| [K6-ITEMS-T1-TRAIN] | `60_RESULTS\k6_items_v01\items_t1_train_summary.json` | `e5e838b8f75e9535951048eddb98ab8440d00af29c38f1d60a95aad95e4a3e8b` |
| | `60_RESULTS\k6_items_v01\items_t3_train_summary.json` | `b65207f399e59cd560eb04453c246fc2f7096c2d73f1fa9f0e63b7d059da2e42` |
| | `60_RESULTS\k6_items_v01\items_t1_val_summary.json` | `2d383ef4c02483dd21b420f8334fca30ac55199568b36edc0bcdbf440e0db10a` |
| | `60_RESULTS\k6_items_v01\items_t3_val_summary.json` | `976538ca365550ae0fa808c692a179f344b4a3d215ba770e479be0e1ff405105` |
| [H8-ID] | `60_RESULTS\k6_horizon_v01\HORIZON8_IDENTITY_v01.json` | `9fecb6ae4c5061df22e505ef5bc589a58fae29b36efd5a792c0e7311fb413624` |
| [K7-FITS-T1] | `60_RESULTS\k7_fits_v01\k7_fits_t1_v01.json` | `02409ec6df29b371c08092ed8977dc7a293933ad0eeb3135e73a5cee319c48f3` |
| [K7-FITS-T3] | `60_RESULTS\k7_fits_v01\k7_fits_t3_v01.json` | `8f455eddb700a3ccdc7d999653e735720c068c0753b493b6b9bdb97229a59d5d` |
| | `60_RESULTS\x1_export_val150_fast_v04\EQUIVALENCE_vs_native_v02.json` | `b000cce3cc86d3552c9b06a5fd95c2313d0d820b02129941a89be00104025359` |
| | `60_RESULTS\x2_export_train700_fast_v02\EQUIVALENCE_train_partial_vs_native.json` | `d912b85d292bbedc9a96b555198a06d3da99665db80b373275be0bd434b7183f` |
| [DET-RECEIPT] | `30_DATA\detectors\RECEIPT_val_copy.sha256` | `7602f93cb9d4f365b5b0b7f2daab1023598613cef908f2dba97bfc79e561efc0` |
| [DET-VAL] | `30_DATA\detectors\centerpoint_flip\infos_val_10sweeps_withvelo_filter_True.json` | `4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e` |
| [DET-TRAIN] | `30_DATA\detectors\centerpoint_flip\infos_train_10sweeps_withvelo_filter_True.json` | `547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145` |
| [SPLIT-VAL] | `30_DATA\det_subsets_val150\split_receipt.json` | `56bb3f19c8fbba072f1a94c7a437924624344371ed209e912e8408242f4ce008` |
| [SPLIT-TRAIN] | `30_DATA\det_subsets_train700\split_receipt.json` | `1d2652e8055e26aa97f1d79a5586bb10196687856b6d8a489e1e71c580bde732` |
| [SCENE] | `30_DATA\nuscenes\v1.0-trainval\scene.json` | `bdc3211bfbfda652d5e9dab73c45c7132925ca84f869bf45e8e14edeafb1d20b` |
| [NUSC-META] | `30_DATA\nuscenes\.v1.0-trainval_meta.txt` | `8aa6ea653821fadeef5c6da495c01997451436696ea17b972dca54ca4959c775` |
| [MINI-META] | `30_DATA\nuscenes_mini_meta\.v1.0-mini.txt` | `7e33af34b107e22b5fd3c49c0a7e824818107b493a7a4fd8cce01259942ccc29` |
| [GT-VAL] | `30_DATA\x1_gt\x1_val_gt_v02.json` | `0c9e4b92bfea0340aaddd37cd756a4fbc99672a6905b0f2a17a82fcad14654e0` |
| [GT-TRAIN] | `30_DATA\x2_gt\x2_train_gt_v03.json` | `93b4ac8b234f87ac152ce71c26e70e8bdb9eeb656242a44aa68bd654d5bf3d58` |
| | `30_DATA\k6\cache_v02_t1_train\MANIFEST.json` | `02e69efe047e5bad9f9811102ab4f838bc64dc96cd10ec7a146e1a41502ce2c9` |
| | `30_DATA\k6\cache_v02_t1_val\MANIFEST.json` | `3fce4b25729a666b7b5e645369dc434fc44b97233b57c0c19df5b23e24259cc7` |
| | `30_DATA\k6\cache_v02_t3_train\MANIFEST.json` | `0988453cc5885b6e1e91b6920200fe6fbb6282aa5f0295d6bf8d9f242a969635` |
| | `30_DATA\k6\cache_v02_t3_val\MANIFEST.json` | `f0be2a92bea3edd35bd9af82624e9aea1c2f996930f90a8165e3e8d298db2a8b` |
| [EGO20] | `30_DATA\k6\k6_ego20hz_v01.json.gz` | `165d8a29535f82479ebf03dff422145ff97faf42a975209a9b953009dd3790c2` |
| [K7-IT-T1] | `30_DATA\k7\k7_items_t1_v01_summary.json` | `b264ab1f1f40c0979f941247467dbfdac179c3a00e1339195e6dfc51e3c6df58` |
| [K7-IT-T3] | `30_DATA\k7\k7_items_t3_v01_summary.json` | `1455a7564213c2e6f0a203136a5bdb5daf00160a8f394aa89af380f2d690d768` |
| | `30_DATA\k7\k7_items_t1_v01.npz` | `5571bbb649a78b371341b865e1456c111b51f5f8b27a2841f4cf91de6b2f2e03` |
| | `30_DATA\k7\k7_items_t3_v01.npz` | `81d265fc43d02df2480fb3ef853a586e42945c9b6d511e8e62a1dc10cf2aa6a2` |
| [XLIB] | `50_CODE\x1\x1_lib_v03.py` | `f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd` |
| | `50_CODE\x1\x1_full_v02.py` | `b59dd08a407b8907d93386e7b136af973a5889444c3a0c84053d3e8a4a42bf64` |
| | `50_CODE\x1\x2_full_v02.py` | `7025ea878bff9b1b2ae8c8a0a2765e197b1d7869dd16e468b28a2f00dfe53c00` |
| | `50_CODE\x1\x1_horizon_prep_v01.py` | `b823756f19ca23d4d36b6d97249f647182eee20a570c2f92a6149aeb2908c3e6` |
| | `50_CODE\x1\x1_export_v04.py` | `3dfb23045fa2f8c26ed616120068886b196aa8062e3f383f0a252c95b46ce76d` |
| | `50_CODE\x1\x1_gt_prep_v03.py` | `d0d3b91c30ee78c277639ecbd94b69397bf6bc4153752b3ebd070288e5894b89` |
| [MLIB] | `50_CODE\m\m_lib_v04.py` | `6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5` |
| | `50_CODE\m\m_run_v04.py` | `bfe6047b48902b195361a409f38cefeb7b0c451628918488e7186cfac5a20396` |
| | `50_CODE\m\m_decide_v04.py` | `6bb362505eadd8caa0300f9f609a23ddb69e63b8973e5e01745ac47dfc24ac84` |
| | `50_CODE\m\m_data_v04.py` | `67bf52a950e299d3775ee9f8b357dceb674a14ac2689d087a8ef1af189ec633f` |
| [K6SIM] | `50_CODE\k6\k6_sim_v02.py` | `257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4` |
| | `50_CODE\k6\k6_analyse_v02.py` | `9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61` |
| | `50_CODE\k6\k6_run_v02.py` | `2821511f35e51520fc7b724dd5dc9b9ab7d02c50ac9acd38c98d79b64a982cf3` |
| | `50_CODE\k6\k6_fit_v01.py` | `19ec27bfa6786132947b4d0c81f0f73a755877233212c10e5996b7e9d2a7e788` |
| | `50_CODE\k6\k6_items_v01.py` | `d1c45eb558a6e7472270933cf91bd21ea02de180849dada8e7e28d8077b4599b` |
| | `50_CODE\k7\k7_analyse_v02.py` | `ec33f1465542b75c400f33dd06525a8ca23c1ab960a499448e7ff2629140c248` |
| | `50_CODE\k7\k7_sim_v01.py` | `1556568dced53280b49324ffa4841b478f83d9577f8e1f0d8aa185cf073e5db2` |
| | `50_CODE\k7\k7_items_v01.py` | `8ebc9d45f3563b2e439a793013cca7e9cc793b1656e13d3495b73492f6802977` |
| | `50_CODE\k7\k7_fit_v01.py` | `05b835a020b809265fa75a7d1d7a2f8995fa7b04f48b9075677114c14ec2857d` |
| [R01] | `70_TESTS\R01_ADVERSARIAL_REVIEW_P01_S01_v01.md` | `228438949f524548e45034db28d9a87ec1a841fe6d2f129ebf9ba9e08a5ba4bb` |
| [R02] | `70_TESTS\R02_SECOND_PASS_v01.md` | `32a6790de9268d083fd9263e8de438777665352d4aff8fedab5fce57af0151b5` |
| [R03] | `70_TESTS\R03_PREFREEZE_REVIEW_v01.md` | `9484c02f88e13520b144e7218c67c4b21d4bbb31218513546171e2364a3f02a7` |
| [R04] | `70_TESTS\R04_THIRD_PROOF_REVIEW_v01.md` | `8da0bb7ca080d2975768a06f787d0aece9bdea00b11d0c3d7b4be6abec0c66a7` |
| [R05] | `70_TESTS\R05_X2_PREFREEZE_REVIEW_v01.md` | `08798fad46cb08863831facfe7e178069137283996eae215a4b6dc25c45ecebe` |
| [R06] | `70_TESTS\R06_X2_RESULTS_REVIEW_v01.md` | `a29a3104eb8686cbd30562c61808de89d3f37465826da4f6fefc5529a671527e` |
| [R07] | `70_TESTS\R07_M_PREFREEZE_REVIEW_v01.md` | `ecd9ff5135579f5480063f82f6f10214e56616fa1d92da28862a8484896ae174` |
| [R07B] | `70_TESTS\R07B_M_PREFREEZE_REREVIEW_v01.md` | `b391e39da55ad40011278fbc4acb10ccbc4f6e1cd509c2528f4f2219c80cb8c1` |
| [R07C] | `70_TESTS\R07C_M_PREFREEZE_CHECK_v01.md` | `0f70f02ad83706786109b8947e6c15cca2ac637d87897d5cae8c576443310744` |
| [R08] | `70_TESTS\R08_M_RESULTS_REVIEW_v01.md` | `9ba67e5b7d649753a735b2aa1afe9f2956b19c2648c428023b1f1acebb807f5f` |
| [R09] | `70_TESTS\R09_K6_PREFREEZE_REVIEW_v01.md` | `f9c07183710482c2fd465fc2c402d97cf25f8af0ffde620cd111f5dd4f63a559` |
| [R09B] | `70_TESTS\R09B_K6_PREFREEZE_REREVIEW_v01.md` | `1064d57668b42f21f4660a4fd9cf676dde1098ac542b9ce57465630a24c0ccc1` |
| [R09C] | `70_TESTS\R09C_K6_PREFREEZE_CHECK_v01.md` | `43317a97deb6daef02bf91e5dc89415a529bb4ccddffdd8600725e492de148f9` |
| [R10] | `70_TESTS\R10_K6_RESULTS_REVIEW_v01.md` | `2d8655272a93105842edc415707ba34258e5cd5731aa0074efb9a96471c1bd20` |
| [R11A] | `70_TESTS\R11A_K6_POWER_RULE_AUDIT_v01.md` | `f1239fa4af4045c8125f03252741ebca1519d0cf0fa6dcdf8ab955395616c25b` |
| [R11B] | `70_TESTS\R11B_K6_RECORD_PIPELINE_AUDIT_v01.md` | `40661e1b5d8d9cb0c17772a9528afddae00753a88e3beb6ff626182c6298dcaf` |
| [R12] | `70_TESTS\R12_K7_PREFREEZE_REVIEW_v01.md` | `610fb819bff43cf84ab4fca9139acaa51eea474d03a77702398ba3136cc64ce1` |
| [R12B] | `70_TESTS\R12B_K7_PREFREEZE_REREVIEW_v01.md` | `00d371af5444b31863c4b8a3cfd2505b12e58d3b54d444a6687cd6089a261097` |
| [R13B] | `70_TESTS\R13B_E01_REVIEW_v01.md` (the review applied in v02) | `df7b47828e6e22110492365aced61eaa35bcee6ba5670866fe5c003d2c90168b` |
| [M-SYN] | `70_TESTS\M_SYNTHETIC_TESTS_v05.md` | `d07a33242384cf69c02cdac513a34f7842812f8f14ff8c78e96777a4cc620c15` |
| [X1-E2E] | `70_TESTS\X1_E2E_SYNTHETIC_TESTS_v01.md` | `d2a4d9142d10574348130aecc440b2f7d18276224ed37f4481a469efb12dd145` |
| [K7-OC] | `70_TESTS\k7_scratch\k7_oc_v03.json` | `8b91aa300425b622eb6ed9168002a354b2482a74c253aad3fc3fdd65e3f61b2a` |
| [K7-DEV] | `70_TESTS\k7_scratch\k7_dev_check_v01.json` | `397541625427fe95a11c0b032fc119d9b48aff22fb52d6a6a47b9d55c8b9f9dc` |
| [K7-TESTS] | `70_TESTS\k7_scratch\k7_tests_v01.json` | `aa739816514d5bb271e8c022ecd9d8f70575a1c47cd0a8f617b80c0c5914ff7b` |
| | `70_TESTS\k7_scratch\k7_design_counts_v02.log` | `67ed5976a2de6cbde7c1382a62b5a51780bd9a58cf6f432ce469ab9c05fafaec` |
| | `70_TESTS\k7_scratch\k7_dev_axis_diag_v01.json` | `7fb31f859ff80f7a42b35c5bb5b059bfe09f9d05ff1cd5363776eb137e7bd3f9` |
| [K6-OC] | `70_TESTS\k6_scratch\k6_oc_v02.json` | `8e52748ec54fa7c87090f2240d31adf9ca7eb070ea939007aea549c922cb41a6` |
| | `70_TESTS\k6_scratch\k6_dev_check_v02.json` | `a299f942689dfbbfd66c26cd01b7d021d62a4c1c07111f8ad46e9626ac19777d` |
| | `70_TESTS\k6_scratch\k6_tests_v02.json` | `41ed255f91cfe2bc14d77feca725a7b136c76c8f426946e8ade4b47aad789923` |
| [M-OC-T1] | `70_TESTS\m_scratch\oc_v04_T1.json` | `0c1177533f5381b9188433cee02f21eb9dec3db2daecfbcc9d183b8b56e46a9f` |
| [M-OC-T3] | `70_TESTS\m_scratch\oc_v04_T3.json` | `fcb8d6f4a097331f755df8ae6ec52299d05dc8436d8faad69e1532ed38733cc8` |
| [P01] | `10_PROOFS\P01_THEORY_PROOFS_v02.md` | `3c4d176e524adf79f93737d81c25fe969fa1cdabe0903d75c77d3ffc5fad8c74` |
| | `10_PROOFS\P01_ADDENDUM_v03.md` | `04fc13f9997168658b8f716b8708e5a90dd8c1ba3bbeaa57d807b2d18fbf3602` |
| | `10_PROOFS\P01_ADDENDUM_v04.md` | `5557b6b190b0953a45a3a2cca9d649acc97aa5138805e1c0d47f198039fbb738` |
| [P02] | `10_PROOFS\P02_METHOD_PROPOSITIONS_v03.md` | `666ec27d7c46ffde862a43316dea50ea58a1008fef0eff3b8a487b2262cdcf2e` |
| [P5] | `20_DESIGN\P5_CLAIMS_AND_PROOF_OBLIGATIONS_v04.md` | `ce5c5d56fe932793d99649d2eda6ed06b7e090aa0d3412dca5a2fcad9a268ed8` |
| [P4] | `30_PRIOR_ART\P4_OCCUPANCY_REPORT_v01.md` | `23be659c22a6484bb9dd5f01e9dfe4ee89ec9f4c5df8ee37e93f69613e164c1c` |
| | `80_LOGS\K6_main_v02_analysis.log` | `c409a96f6f95357d7391b6978d1094fae30cbbccc1db8272ea7c06d6eba8e699` |
| | `80_LOGS\K6_freeze_and_main_v02.log` | `9be6ebc9be4717d5f8886c867758e37d5837a6d20daf73b59af22eae828a9d3d` |
| [E01-v01] | `20_DESIGN\E01_EVIDENCE_DOSSIER_v01.md` (superseded, kept) | `64a53113d358b88421758cf8bd221bce7f68445505b0be49e05dbed2024aa37d` |

The large per-worker export files, the 8-step horizon files and the K6 caches are not re-hashed here; their hashes are inside the frozen blocks of [X2-PLAN] §0, [M-PLAN] (353 files) and [K6-PLAN] (97 files), which R06, R08 and R10 each verified file by file.

---

## Appendix A. Cross-checks: where a report and its file differ, or a number could not be traced to a stored field

| # | Statement in a report | What the frozen file says | Reading |
|---|---|---|---|
| 1 | D05 (and **D13 §0**, which repeats it verbatim): NEES scaling "leaves the lateral tail at **13–20 %** while adding **1.6–2.7 m** of longitudinal margin" | [X2R] `G1_X2.steps[*].H3`: lateral exceedance after scaling **0.130** and **0.172** (lower bounds 0.104, 0.130); longitudinal margin added **2.72 m** and **2.17 m**. R06 m3, re-estimating k in each bootstrap replicate, gives lower bounds **1.57 m** and 0.95 m. | "20 %" and "1.6 m" are not in the result file; the 1.6 m appears to be R06's re-estimated lower bound for the < 20 m bin. The frozen point values are 0.130–0.172 and 2.17–2.72 m. Flagged as loose rounding in D05 and D13, not a contradiction. |
| 2 | D07 efficiency table: M\*/B3 on T1 **0.161 [0.121, 0.177]** | [MR-T1] `E2_h2s.all.ratios`: 0.161 [0.121, 0.177] (E2, val). [MDEC] `efficiency_descriptive`: 0.165 [0.160, 0.171] (E1 fixed rule, train). | Both exist in frozen files; D07 uses the E2 intervals and says so. The decision file's narrower intervals are the ones R08 M4 warned against. Not a conflict; §5.3 shows both. |
| 3 | D07: Poly-MOT's covariance "mean margin **16.9 m**; lateral **32 m**" | [MR-T3] `E1_h2s.fixed.methods.B0`: 16.90 m, lateral 32.13 m (train, held-out logs). `E2_h2s.all.methods.B0`: 16.01 m, lateral 30.27 m (val). | D07 quotes the E1 values without naming the split. Both given in §5.3, together with CANMOT's 4.3 m (E1) / 4.4 m (E2). |
| 4 | D10 HK2 on T1: "Bonferroni lower bounds **0.13–0.16**" | [K6R] `decide.t1.HK2.*` stores only `flagged_bonferroni` (lists) and the paired contrasts; the stored cell bounds are the arms' 95 % sup-t lower bounds (0.178, 0.149, 0.181) and the paired-difference lower bounds (0.134, 0.113, 0.143). | The exact "0.13–0.16" interval is not a stored field (the 1 − 0.05/3-level cell bounds are computed inside the analysis but not written). The flags themselves and the paired bounds are stored and reproduce. Minor traceability gap. |
| 5 | D05/D13: "turning cars carry **68 %** of exceedances" | Not in [X2R]. From [R06] §3 and M1: ground-truth heading change ≥ 5° over 2 s carries 68 % of in-path lateral exceedances (5–15°: E 0.405; 15–45°: 0.555). | A reviewer's descriptive breakdown, not a pre-registered statistic. The article should cite it as such. |
| 6 | D10: "the delayed logged profile itself collides at fault (10 times at 1 s, 45 at 2 s)" | [K6R] `loop.*.outcomes.LOG` reports 0 at-fault collisions in aggregate (LOG is excluded from fault accounting in the summary); the per-delay counts are in [R10] **§5** ("Anomalies and observations", line 378: 63 collisions at 1 s with 10 at fault, 202 at 2 s with 45 at fault). | Traced to R10 §5, not to the result JSON. |
| 7 | D11: R11b re-derived "76,065 records" | [R11B]: 38,225 (T3) + 37,840 (T1) = 76,065. | Consistent. |
| **8** | **D07 §2: "Poly-MOT. Every multiplier is below 1: the method shrinks its over-wide covariance."** (repeated in E01 v01 §5.3) | [MR-T3] `E2_h2s.fit_on_all_train.Mstar`: **91 of 96** L0 thresholds are below 1; **5 are above 1**: `car|>=40|long|straight` 1.1177 (own L0 fit), `car|>=40|long|static`, `|turning`, `|new` 1.1177 (inherited from L1), `two_wheeler|<20|long|straight` 1.1081 (own fit). All 16 car strata under 40 m are ≤ 0.87. | **D07 is wrong in five strata; the file is right.** The scientific reading (Poly-MOT's covariance is over-wide and is shrunk, including in every car stratum under 40 m) survives; the sentence "every multiplier" does not. v02 §5.3 gives the exact count and names; found by R13b 1.1. |

Nothing in this dossier required a new computation on real data; every value above was read from a frozen file or a review that cites one.

---

## Appendix B. R13b findings and where v02 fixes them

| R13b | Severity | Finding (short) | v02 location of the fix |
|---|---|---|---|
| 1.1 | Major | "Every Poly-MOT multiplier below 1" is false (5 of 96 above 1) | §5.3 "shape correction" paragraph (exact count, names, values, levels); Appendix A row 8 names D07 §2 as the source |
| 1.2 | Major | Record defined at k ≥ 1 but counted with frame 0 | §2.4 "Record": both counts with definitions (381,553 / 1,839,331 export totals incl. frame 0; 373,702 / 1,800,482 at k ≥ 1) and which the tables use; §5.1 and §2.8 now say "export records" |
| 1.3 | Major | Progress means over 2,100, header says 2,371 | §5.4 closed-loop paragraph "Denominators" and the row labels; §2.8 population table last row |
| 1.4 | Minor | sup-t q range wrong for the method stage | §3.4 "Simultaneous sup-t band": per-stage q values with key paths (X1 2.76/2.85; X2 2.48; M fixed 3.40–3.46, refit M\* 4.50–4.83, refit paired 2.19–4.57, E2 3.31–3.74; K6 3.23/3.20, 2.72/2.52, SD1 3.00/3.14, SD2 3.26/3.21) |
| 1.5 | Minor | X1 FWER "against 2.5 % allowed"; the file's limit is 0.0390 | §3.4 FWER bullet and §5.1 "Why G1 was not shown": 0.002 against the limit 0.0390 (nominal 0.025 + 2 MC SE), same convention as X2 |
| 1.6 | Minor | "≥ 0.999" overstated (T1 vs B0 at deff 3.5 is 0.9986) | §5.5 HK3 power paragraph: "≥ 0.998 … except T1 vs B0 at design effect 3.5, 0.9986" |
| 1.7 | Minor | "4.3 m for CANMOT" mixes E1/E2 without naming | §5.3: "4.3 m (E1) / 4.4 m (E2)" |
| 1.8 | Minor | Citation paths that do not exist as written | §3.4: `[X2R] family_h2s.primary.<cell>.threshold`, `family_h2s.orientation_null.<cell>.E0/.m0`; §5.2: `family_h2s.sensitivities.*`; §2.1: `[XLIB] lines 26–27`; §5.4 and Appendix A row 6: `[R10] §5` |
| 1.9 | Minor | Counts for R01–R05, R07–R07c, R09–R09c unverified | §6: every count now read from the review's own summary with its line number; R07c corrected to its own "1 critical, 1 major, 13 minor" (D07 abbreviates); R02 limited to what its header states |
| 2.1 | Major | K7 description hides the dropped PD floor | §3.7 K7 paragraph (PD floor dropped, "narrower claim", HK2 changed, reporting constraints); §5.5 note under the OC table (PD family of 5 reported, not required); §7 Not-established 2 |
| 2.2 | Minor | Motion-state history "k, k−1, k−2 (and k−4)" | §2.7: k−4, k−2, k when k−4 exists, else k−2, k−1, k |
| 2.3 | Minor | "not behind the ego" imprecise | §5.4 harness: "not more than 2.05 m (half the ego length) behind the ego centre, i.e. not behind the rear bumper", with the code test |
| 2.4 | Minor | A omits the max(ĉ, 10⁻³) floor | §4 M\* row: A written with max(ĉ, 10⁻³)/1.645 and its purpose |
| 2.5 | Minor | X1/X2 verdicts not labelled record-weighted | §3.2 first bullet and §3.4 "Verdicts (X1/X2), on the record-weighted E"; §5.1 and §5.2 table captions |
| 2.6 | Minor | §3.3 omits that k is applied to Σ̂ + σ_a²I | §3.3 last sentence |
| 3.1 | Major | §1 "does fix it" / "certificate held" harder than D07/D10 allow | §1: "is not significantly above δ on held-out logs and on log-disjoint validation scenes", "no DP-SCRC cell was flagged on the population it was calibrated for" |
| 3.2 | Minor | T3 HK2 borderline (B1 bound 0.0496) omitted | §5.4 confirmatory table, HK2 row, T3 column |
| 3.3 / 5.1 | Major | §7 Established 5 "every practitioner and certified alternative" contradicted by B6 on T3 | §7 Established 5: names B0, B1, B4, B9 as the tested arms; states B6 0.215 vs M\* 0.222 on T3 and that B6 was not an HK3 comparator; §3.7 HK3 bullet says B6/B3 are not comparators; §5.4 reference-arm row highlights B6 < M\* on T3 |
| 4.1 | Minor | K7 row omits B0/Z0 fit-free and the 99.7 % identical-residual fact | §2.8 K7 row |
| 4.2 | Minor | K6 row does not say K6's M\* is a new cross-fit | §2.8 K6 row |
| 5.2 | Minor | Established 3 lacks the MDE80 figures | §7 Established 3 (0.10–0.30 E1, 0.15–0.30 E2); §5.3 OC paragraph |
| 5.3 | Minor | Theory absent from §7 | §7 first line and new bullet 0 (P01 Thm 1, 2, 4, 5, Prop. 6; P02 PM1–PM3; R01, R02, R04) |
| 5.4 | Minor | Poly-MOT motion-strata cost mixes E1/E2 | §7 Not-established 4: "(E2 6 %, E1 11 %: M\*/B6 1.056 and 1.110)" |
| A-1 | Minor | D13 §0 repeats the D05 rounding | Appendix A row 1 now names D13 §0 |
| A-6 | Minor | R10 section number for LOG collisions | Appendix A row 6 and §5.4: R10 §5, line 378 |
| A-new | Major (with 1.1) | Missing Appendix A row for D07's multiplier sentence | Appendix A row 8 |
| 7.1 | Readability | §1 uses δ, "exceeded", NEES, DP-SCRC before definition | §1: each defined or cross-referenced at first use |
| 7.2 | Readability | Record count vs definition | §2.4 (= 1.2) |
| 7.3 | Readability | m⁰ used before definition | §3.2 price bullet: "the 0.95 quantile of U under the orientation null (§3.4)" |
| 7.4 | Readability | s and "m-records" undefined in §5.1 | §5.1 h2s table caption defines s; "the sum over test records of the margin, in metres" |
| 7.5 | Readability | LB/UB unexpanded in §5.3 | §5.3 first table lead-in |
| 7.6 | Readability | Progress, infeasible-frame share, sensor offset undefined; 2,100 | §5.4 closed-loop paragraph "Definitions" and "Denominators" |
| 7.7 | Readability | SD2, PL, PD, PD7, SD1_7, F_MIN are code labels | §3.7 K6 paragraph "Code labels used below"; §3.7 K7 paragraph defines PD7 and SD1_7; §5.4 glosses SD2 and PL at use |
| 7.8 | Readability | K7 OC table legend | §5.5 legend above the OC table |
| 7.9 | Readability | "2.6 % in-path" denominator; "59 train scenes" | §2.8 K7 row ("of the calibration items") and K6 row ("worker 0's 59 train scenes, pairing rates only") |
| 7.10 | Readability | q range | §3.4 (= 1.4) |

R13b's file is cited as [R13B] and hashed in §8 as it stood when v02 was written. Every number changed or added in v02 was re-read from its file after the edit (37 field checks, all passing after one rounding correction to the T3 SD1 q value; script `e01_v02_verify.py` in the session scratchpad, which imports no project module and writes nothing under `W`).
