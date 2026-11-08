# Argoverse 2 validation: stage-A items, K8 counts and HOTA (v02, 2 Nov 2026)

**What this is.** The second AV2 tracker step: stage-A caches built under `90_DECISIONS/D16_DELEGATED_CHOICES_v03.md` Choice 13 for T1 (CANMOT sc) and T3 (Poly-MOT) on both detectors, plus AB3DMOT. It also covers the K8 decision-mode item counts (`AV2_TRACKER_COUNTS_v02.json`; v01 kept), the stage-B script tested on nuScenes only, HOTA from the official av2 evaluator (Choice 14) and AB3DMOT (Choice 11; `AV2_AB3DMOT_NOTE_v01.md`). The design is `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v02.md` §12, written before any stage-A file existed. The as-run record is `AV2_TRACKER_PORT_DESIGN_v03.md` §13. `AV2_TRACKER_NOTE_v01.md` (the first step) is unchanged.

**Outcome statement.** On AV2 this step computed only the following:
- the trackers' own 2 s propagation of mean and covariance;
- logged ego poses;
- estimate-only geometry: toward-ego normals, separating flags, predicted-range, group and motion strata, sd and L0;
- ground-truth association at time k;
- existence and point count of the paired `track_uuid` at later frames;
- the planner's arm-independent enforced pairs at margin 0;
- tracking metrics;
- counts.

**Not computed on AV2:** no annotation position, box or velocity at any frame entered a stage-A file or any count; `gt_x`, `gt_y`, `gt_yaw`, `gt_w` and `gt_l` are NaN. No residual, projected error, U, exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or coverage was computed. Stage B was not run on AV2: its guard refuses without the frozen-plan hash, and that refusal was tested.

## 1. Stage A (`30_DATA/av2_cache_stageA_v01/`)

| Item | Result |
|---|---|
| 2 s propagation (`horizon8_<run>.jsonl.gz`, `av2_horizon_prep_v01 --propagate-only --allow-av2-propagation`) | T1×LT3D 229,438; T3×LT3D 229,469; T1×VoxelNeXt 274,837; T3×VoxelNeXt 275,587 records; AB3DMOT from its own filter |
| Ego path (`av2_ego10hz_v01.json.gz`) | 150 logs at 10.06 Hz (median); at all 4,806 frames the pose equals the GT table's ego pose |
| Caches (`cache_stageA_<run>/`, `av2_cache_stageA_v01`) | 150 npz each, K6 layout plus `tr_g`, `tr_r8`, `tr_ax`, `tr_ctrv_c2s`, `tr_anorm2s_ctrv`, `tr_sep2s_ctrv`, `tr_anorm2s_log`, `tr_vis8`; GT existence and points only |
| Groups (design 12.1, written before any count) | car = `REGULAR_VEHICLE`; pedestrian = `PEDESTRIAN`; two-wheeler = `BICYCLIST` + `MOTORCYCLIST` (the counts give the split); large = the 8 truck, bus and trailer categories |

## 2. Tests on nuScenes only (`60_RESULTS/av2_trk/stageAB_nuscenes_test/`)

| Test | Result |
|---|---|
| Stage-A builder vs `30_DATA/k6/cache_v02_t1_val` (every non-position field) | **identical**: 4,650 field comparisons over 150 scenes; the five position fields NaN everywhere; manifests and stats equal |
| Stage B (`av2_cache_stageB_v01`) on that output vs the K6 cache (every field) | **identical**: 5,400 field comparisons |
| `k8_items_v04 --counts-only` vs `k8_items_v02` on the 10 development scenes | **identical** on every non-error field; every error field NaN |
| Stage-B guard on an AV2 stage-A cache | refused (no frozen-plan hash) |
| T3 nuScenes builder test | stopped on purpose (time); T1 exercises the same code |

## 3. Tracking metrics with HOTA (official av2 evaluator)

HOTA comes from `av2_hota_v03` in `50_CODE/env/av2eval310`: av2 0.3.6 and TrackEval at commit 12c8791b, labels within 50 m, centre-distance similarity with zero at 2 m, per-class score threshold tuned for HOTA. It differs from the official runner in three documented ways: the seven tracking classes are used, there is no ROI filter (no maps), and threshold tuning runs serially. "Tuned" is HOTA at the tuned threshold; "mean of 10 thr." is the number av2's runner prints. AMOTA, MOTA and IDS follow the nuScenes protocol (`av2_track_metrics_v03`).

| Tracker | Detector | Class | HOTA (av2, tuned) | HOTA (av2, mean of 10 thr.) | DetA | AssA | AMOTA | MOTA | IDS | MOTA (av2) | IDSW (av2) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 CANMOT sc | LT3D | car | 0.787 | 0.533 | 0.725 | 0.858 | 0.923 | 0.840 | 76 | 0.810 | 106 |
| T1 CANMOT sc | LT3D | pedestrian | 0.718 | 0.507 | 0.656 | 0.788 | 0.873 | 0.754 | 138 | 0.638 | 574 |
| T1 CANMOT sc | LT3D | cyclist | 0.518 | 0.365 | 0.382 | 0.703 | 0.572 | 0.449 | 0 | 0.209 | 3 |
| T3 Poly-MOT | LT3D | car | 0.792 | 0.535 | 0.731 | 0.861 | 0.923 | 0.840 | 82 | 0.812 | 121 |
| T3 Poly-MOT | LT3D | pedestrian | 0.715 | 0.505 | 0.658 | 0.778 | 0.870 | 0.751 | 165 | 0.634 | 709 |
| T3 Poly-MOT | LT3D | cyclist | 0.506 | 0.358 | 0.372 | 0.692 | 0.570 | 0.449 | 0 | 0.205 | 3 |
| T2 CANMOT sample/trainval | LT3D | car | 0.765 | 0.521 | 0.697 | 0.847 | 0.922 | 0.838 | 78 | 0.775 | 113 |
| T2 CANMOT sample/trainval | LT3D | pedestrian | 0.714 | 0.504 | 0.649 | 0.787 | 0.873 | 0.755 | 134 | 0.632 | 604 |
| T2 CANMOT sample/trainval | LT3D | cyclist | 0.486 | 0.344 | 0.350 | 0.678 | 0.564 | 0.447 | 0 | 0.199 | 2 |
| T1 CANMOT sc | VoxelNeXt | car | 0.755 | 0.526 | 0.705 | 0.812 | 0.899 | 0.801 | 815 | 0.783 | 1092 |
| T1 CANMOT sc | VoxelNeXt | pedestrian | 0.622 | 0.449 | 0.586 | 0.662 | 0.790 | 0.664 | 302 | 0.526 | 1523 |
| T1 CANMOT sc | VoxelNeXt | cyclist | 0.510 | 0.379 | 0.504 | 0.517 | 0.561 | 0.430 | 0 | 0.324 | 77 |
| T3 Poly-MOT | VoxelNeXt | car | 0.750 | 0.524 | 0.708 | 0.798 | 0.894 | 0.786 | 1222 | 0.779 | 1486 |
| T3 Poly-MOT | VoxelNeXt | pedestrian | 0.521 | 0.374 | 0.560 | 0.489 | 0.699 | 0.558 | 763 | 0.470 | 3095 |
| T3 Poly-MOT | VoxelNeXt | cyclist | 0.498 | 0.368 | 0.503 | 0.494 | 0.541 | 0.403 | 4 | 0.313 | 83 |
| AB3DMOT (LT3D), detection-box output | LT3D | car | 0.573 | 0.460 | 0.510 | 0.645 | 0.329 | 0.433 | 4716 | 0.395 | 6088 |
| AB3DMOT (LT3D), detection-box output | LT3D | pedestrian | 0.520 | 0.423 | 0.490 | 0.552 | 0.325 | 0.400 | 1889 | 0.305 | 3119 |
| AB3DMOT (LT3D), detection-box output | LT3D | cyclist | 0.264 | 0.179 | 0.325 | 0.215 | 0.000 | 0.000 | 182 | -0.340 | 174 |
| AB3DMOT (LT3D), filter-state output | LT3D | car | 0.571 | 0.460 | 0.507 | 0.648 | 0.328 | 0.433 | 4720 | 0.386 | 6189 |
| AB3DMOT (LT3D), filter-state output | LT3D | pedestrian | 0.522 | 0.424 | 0.490 | 0.556 | 0.326 | 0.400 | 1891 | 0.305 | 3122 |
| AB3DMOT (LT3D), filter-state output | LT3D | cyclist | 0.262 | 0.178 | 0.322 | 0.214 | 0.000 | 0.000 | 181 | -0.340 | 171 |

Descriptive readings: HOTA and AMOTA order the runs alike, up to near-ties. With LT3D, T1, T2 and T3 are within 0.035 HOTA of each other for every class (car 0.77–0.79, pedestrian 0.71–0.72, cyclist 0.49–0.52). Without detector velocity (VoxelNeXt), car HOTA drops by 0.03–0.04 and pedestrian HOTA by 0.10 (T1) and 0.19 (T3). AB3DMOT is well below both trackers (car 0.57); see its note. The av2 MOTA and IDSW differ from the nuScenes-protocol MOTA and IDS because the matching, the range filter and the score thresholds differ.

## 4. K8 decision-mode item counts (`AV2_TRACKER_COUNTS_v02.json`)

`k8_items_v04 --av2 --counts-only` enumerates the decision states (keyframes 1 to K − 2 of each log, the logged ego's state). For each state it finds the planner's enforced (track, check time) pairs at the arm-independent reference margin 0, keeps those whose paired `track_uuid` is annotated with points at k + h (h = 0.5 to 2 s), and takes the relied-on axis at the reference pose: these are the PD7 items. SD1_7 is PD7 with a gap of 5 m or less; PD is PD7 in the method's in-path set; NIP is the rest. Cells are group · axis · motion (K6's cell family, pooled over range). "Evaluable" means 39 or more logs (on AV2 a log is a scene). Error fields are NaN and are never read. Arm-dependent decision-mode records are **not** counted: the fitted arms need an AV2 fit, which is an outcome before the freeze, and every arm's plan choice carries the infeasibility indicator (Choice 13).

### K8 items (counts only): decision states, pairs and items per population, items / logs (evaluable cells of 32)

| Run | decision states | pairs enforced at margin 0 | pairs with the paired object annotated at k + h | PD7 | SD1_7 | PD | NIP |
|---|---|---|---|---|---|---|---|
| t1_lt3d | 4506 | 213140 | 205283 | 205075 / 150 (20) | 23653 / 147 (11) | 8406 / 130 (6) | 196669 / 150 (19) |
| t3_lt3d | 4506 | 213385 | 205554 | 205395 / 150 (21) | 23582 / 147 (12) | 8116 / 128 (6) | 197279 / 150 (20) |
| t1_voxelnext | 4506 | 208194 | 201262 | 200809 / 150 (23) | 24224 / 148 (16) | 9470 / 137 (7) | 191339 / 150 (22) |
| t3_voxelnext | 4506 | 208439 | 201473 | 201143 / 150 (21) | 24093 / 149 (13) | 9193 / 139 (7) | 191950 / 150 (20) |
| ab3dmot_lt3d | 4506 | 231666 | 223771 | 223577 / 150 (20) | 28452 / 146 (11) | 8582 / 131 (5) | 214995 / 150 (20) |

### PD7 items by group, items / logs (two-wheeler split: bicycle class / motorcycle class)

| Run | car | pedestrian | two-wheeler | (bicycle / motorcycle) | large |
|---|---|---|---|---|---|
| t1_lt3d | 140300 / 150 | 56599 / 136 | 1217 / 28 | (828 / 389) | 6959 / 106 |
| t3_lt3d | 140433 / 150 | 56739 / 136 | 1217 / 28 | (828 / 389) | 7006 / 106 |
| t1_voxelnext | 136637 / 150 | 54679 / 135 | 1307 / 28 | (923 / 384) | 8186 / 108 |
| t3_voxelnext | 136868 / 150 | 54779 / 135 | 1313 / 28 | (930 / 383) | 8183 / 108 |
| ab3dmot_lt3d | 150753 / 150 | 65060 / 133 | 1146 / 25 | (729 / 417) | 6618 / 91 |

### Car, PD7 cells (group | axis | motion, pooled over range): PD7 items / logs, of which in-path items / logs

| Cell | t1_lt3d | t3_lt3d | t1_voxelnext | t3_voxelnext | ab3dmot_lt3d |
|---|---|---|---|---|---|
| car · long · static | 67520 / 149; in-path 1615 / 70 | 68717 / 149; in-path 1557 / 72 | 61853 / 150; in-path 1893 / 77 | 67020 / 150; in-path 1931 / 84 | 81882 / 150; in-path 2810 / 93 |
| car · long · straight | 19802 / 135; in-path 3612 / 87 | 19552 / 134; in-path 3542 / 85 | 16827 / 134; in-path 3190 / 92 | 15298 / 134; in-path 3085 / 89 | 13897 / 123; in-path 2665 / 73 |
| car · long · turning | 3020 / 106; in-path 488 / 42 | 3921 / 112; in-path 599 / 47 | 5497 / 138; in-path 670 / 61 | 6403 / 140; in-path 829 / 71 | 4033 / 123; in-path 534 / 58 |
| car · long · new | 4252 / 131; in-path 356 / 54 | 4293 / 131; in-path 338 / 53 | 3445 / 139; in-path 280 / 53 | 3637 / 139; in-path 363 / 63 | 3918 / 138; in-path 428 / 63 |
| car · lat · static | 36013 / 146; in-path 432 / 41 | 35122 / 146; in-path 377 / 39 | 37430 / 150; in-path 716 / 52 | 34753 / 150; in-path 437 / 48 | 40515 / 149; in-path 561 / 56 |
| car · lat · straight | 6045 / 122; in-path 369 / 50 | 5738 / 119; in-path 318 / 50 | 5482 / 128; in-path 591 / 65 | 4431 / 127; in-path 396 / 62 | 3407 / 102; in-path 227 / 35 |
| car · lat · turning | 2055 / 93; in-path 310 / 28 | 1569 / 94; in-path 250 / 29 | 3886 / 134; in-path 420 / 43 | 3321 / 135; in-path 354 / 47 | 1575 / 98; in-path 209 / 25 |
| car · lat · new | 1593 / 111; in-path 67 / 22 | 1521 / 109; in-path 54 / 18 | 2217 / 134; in-path 112 / 34 | 2005 / 133; in-path 114 / 34 | 1526 / 122; in-path 70 / 25 |

### Evaluable PD7 / SD1_7 / PD cells (>= 39 logs) per run

- t1_lt3d PD7: 20 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · straight, pedestrian · long · turning, pedestrian · long · new, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning, pedestrian · lat · new, large · long · static, large · long · straight, large · long · new, large · lat · static
- t1_lt3d SD1_7: 11 cells: car · long · static, car · long · straight, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning
- t1_lt3d PD: 6 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight
- t3_lt3d PD7: 21 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · straight, pedestrian · long · turning, pedestrian · long · new, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning, pedestrian · lat · new, large · long · static, large · long · straight, large · long · new, large · lat · static, large · lat · straight
- t3_lt3d SD1_7: 12 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning
- t3_lt3d PD: 6 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight
- t1_voxelnext PD7: 23 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · straight, pedestrian · long · turning, pedestrian · long · new, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning, pedestrian · lat · new, large · long · static, large · long · straight, large · long · turning, large · long · new, large · lat · static, large · lat · straight, large · lat · turning
- t1_voxelnext SD1_7: 16 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · straight, pedestrian · long · turning, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning, large · long · static, large · lat · static
- t1_voxelnext PD: 7 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning
- t3_voxelnext PD7: 21 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · straight, pedestrian · long · turning, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning, pedestrian · lat · new, large · long · static, large · long · straight, large · long · turning, large · lat · static, large · lat · straight, large · lat · turning
- t3_voxelnext SD1_7: 13 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · turning, pedestrian · lat · static, pedestrian · lat · turning, large · lat · static
- t3_voxelnext PD: 7 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning
- ab3dmot_lt3d PD7: 20 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · long · straight, pedestrian · long · turning, pedestrian · long · new, pedestrian · lat · static, pedestrian · lat · straight, pedestrian · lat · turning, pedestrian · lat · new, large · long · static, large · long · straight, large · long · new, large · lat · static
- ab3dmot_lt3d SD1_7: 11 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static, car · lat · straight, car · lat · turning, car · lat · new, pedestrian · long · static, pedestrian · lat · static, pedestrian · lat · straight
- ab3dmot_lt3d PD: 5 cells: car · long · static, car · long · straight, car · long · turning, car · long · new, car · lat · static

## 5. Deviations and what is not done

1. **Counts are K8 items.** They are not the method-stage x1 items of `AV2_TRACKER_COUNTS_v01.json`, which counted the t = 0 geometry. Both files are kept. The predicted-range strata (2 s) are inside every K8 L0 stratum (`by_l0`).
2. **T2** is descriptive (Choice 14), so it has HOTA and AMOTA but no stage-A cache.
3. **HOTA** uses the seven tracking classes, has no ROI filter and tunes thresholds serially (§3). HOTA v02's result (about 0.02, frames of different logs paired) was discarded; v03 is the one reported.
4. **The nuScenes T3 builder test** was stopped on purpose (time).
5. **Stopped jobs.** Several queues were stopped on purpose and replaced, and one was interrupted by the power loss (about 07:05–08:51 EST). The full list is in design v03 §13. The only results these jobs left behind are partial outputs that nothing reads: `30_DATA/av2_trk_v01/export_ab3dmot/`, `export_ab3dmot_v03/`, `export_ab3dmot_v04/` (empty or partial) and `60_RESULTS/av2_trk/stageAB_nuscenes_test/t3_val_A/` (partial).
6. **Downloads.** av2 0.3.6 and its dependencies came from PyPI, and TrackEval and the LT3D `tracking/` and `data/` folders from GitHub, all into new folders. Global git and pip configuration was left unchanged.
