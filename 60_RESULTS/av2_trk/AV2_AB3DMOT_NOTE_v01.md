# AB3DMOT on Argoverse 2 val: the descriptive third tracker (v01, 2 Nov 2026)

**What this is.** LT3D's AB3DMOT is the public AV2 baseline tracker named in D15 and the manuscript. It was added as a descriptive third tracker (D16 Choice 11). It is not part of H1. It ran on the LT3D CenterPoint detections at 2 Hz, on the same 4,806 frames as T1/T3. The table below gives its tracking metrics and its stage-A K8 item counts. **Outcome statement:** as for T1/T3 (`AV2_TRACKER_NOTE_v02.md`), no ground-truth position at a later frame was read, and no residual or other outcome quantity was computed.

## 1. What ran

| Item | Detail |
|---|---|
| Code | LT3D at commit e33189aa (the commit of the detector run), partial clone of `tracking/` and `data/` into `50_CODE/third_party_av2/LT3D/` (unchanged). Driver `50_CODE/av2/av2_ab3dmot_v04.py` repeats `tracking/test_tracker.py`'s loop line for line |
| Settings (LT3D's defaults) | score > 0.1, the top 500 boxes per frame over all 26 categories, one single-class AB3DMOT per category, `max_age` 3, IoU matching at 0.1 (Hungarian), track scores averaged over each track afterwards |
| Environment | `50_CODE/env/ab3dmot310`: numpy 1.23.5, scipy 1.10.1, numba 0.58.1 (the LT3D pod's versions), filterpy 1.4.5 |
| Frames | City frame via LT3D's `transform_to_global_reference` rule: centre R t + p, yaw + the ego's yaw, velocity rotated. One tracker reset per log. 150 logs in 6 log-workers (`--worker i --n-workers 6`); logs are independent |
| Classes passed to the tracker | After LT3D's score and top-500 filters (over all 26 categories), only the 12 categories of the tracker-input mapping (design §4.2). AB3DMOT's per-category trackers are independent, so these tracks equal a 26-category run's up to track-id labels |
| Shim L1 | `50_CODE/av2/shims_lt3d/data/utils.py` stands in for LT3D's `data/utils.py`: the two functions `ab3dmot.py` imports, copied verbatim. The original imports mmdet3d for a class list |
| Shim L2 (exact speed-up) | `associate_detections_to_tracks` is replaced in memory by a copy that skips `iou3d` for pairs whose bird's-eye-view circumscribed circles do not overlap. For those pairs LT3D's IoU is exactly 0.0. On one log the shimmed and unshimmed runs gave identical exports and horizon files (2,100 lines each; `60_RESULTS/av2_trk/AB3DMOT_FAST_SHIM_TEST_v01.json`) |
| Read-only capture | Each active track's Kalman state x (x y z yaw l w h + per-frame velocities), covariance P and the filter's F and Q |
| Exports (x1_export_v06 line format, mapped classes) | `30_DATA/av2_trk_v01/export_ab3dmot_v04w6/ab3dmot_det/` (box = the associated detection: LT3D's output) and `.../ab3dmot_kf/` (box = the filter's posterior: the original AB3DMOT output). Both carry velocity = state velocity / 0.5 s, cov = H P H′ (7 × 7), state, P. 625,596 records each, all 4,806 frames, every x, y covariance positive definite |
| 2 s propagation | The filter's own: x ← F x, P ← F P F′ + Q per 0.5 s step (AB3DMOT's step is one frame), aligned with the `ab3dmot_kf` export. Allowed by Choice 13 |
| Stage A | `30_DATA/av2_cache_stageA_v01/cache_stageA_ab3dmot_lt3d/` from the `ab3dmot_kf` export (187,443 deployed records with track score >= 0.4), then `k8_items_v04 --av2 --counts-only` |
| Stopped on purpose | v01: all 26 categories, one process, 250 s per log. v03: 650 s on a log. v02 never ran (a bounds bug fixed in v03). Queues 2–6 were stopped or interrupted; a power loss stopped queue 6 |

## 2. Results

Tracking metrics (official av2 evaluator for HOTA; nuScenes protocol for AMOTA, MOTA, IDS), next to T1 and T3 on the same detections:

| Tracker | Detector | Class | HOTA (av2, tuned) | HOTA (av2, mean of 10 thr.) | DetA | AssA | AMOTA | MOTA | IDS | MOTA (av2) | IDSW (av2) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 CANMOT sc | LT3D | car | 0.787 | 0.533 | 0.725 | 0.858 | 0.923 | 0.840 | 76 | 0.810 | 106 |
| T1 CANMOT sc | LT3D | pedestrian | 0.718 | 0.507 | 0.656 | 0.788 | 0.873 | 0.754 | 138 | 0.638 | 574 |
| T1 CANMOT sc | LT3D | cyclist | 0.518 | 0.365 | 0.382 | 0.703 | 0.572 | 0.449 | 0 | 0.209 | 3 |
| T3 Poly-MOT | LT3D | car | 0.792 | 0.535 | 0.731 | 0.861 | 0.923 | 0.840 | 82 | 0.812 | 121 |
| T3 Poly-MOT | LT3D | pedestrian | 0.715 | 0.505 | 0.658 | 0.778 | 0.870 | 0.751 | 165 | 0.634 | 709 |
| T3 Poly-MOT | LT3D | cyclist | 0.506 | 0.358 | 0.372 | 0.692 | 0.570 | 0.449 | 0 | 0.205 | 3 |
| AB3DMOT (LT3D), detection-box output | LT3D | car | 0.573 | 0.460 | 0.510 | 0.645 | 0.329 | 0.433 | 4716 | 0.395 | 6088 |
| AB3DMOT (LT3D), detection-box output | LT3D | pedestrian | 0.520 | 0.423 | 0.490 | 0.552 | 0.325 | 0.400 | 1889 | 0.305 | 3119 |
| AB3DMOT (LT3D), detection-box output | LT3D | cyclist | 0.264 | 0.179 | 0.325 | 0.215 | 0.000 | 0.000 | 182 | -0.340 | 174 |
| AB3DMOT (LT3D), filter-state output | LT3D | car | 0.571 | 0.460 | 0.507 | 0.648 | 0.328 | 0.433 | 4720 | 0.386 | 6189 |
| AB3DMOT (LT3D), filter-state output | LT3D | pedestrian | 0.522 | 0.424 | 0.490 | 0.556 | 0.326 | 0.400 | 1891 | 0.305 | 3122 |
| AB3DMOT (LT3D), filter-state output | LT3D | cyclist | 0.262 | 0.178 | 0.322 | 0.214 | 0.000 | 0.000 | 181 | -0.340 | 171 |

Stage-A K8 item counts (counts only; items / logs, evaluable cells of 32 in brackets):

| Run | decision states | pairs enforced at margin 0 | pairs with the paired object annotated at k + h | PD7 | SD1_7 | PD | NIP |
|---|---|---|---|---|---|---|---|
| t1_lt3d | 4506 | 213140 | 205283 | 205075 / 150 (20) | 23653 / 147 (11) | 8406 / 130 (6) | 196669 / 150 (19) |
| t3_lt3d | 4506 | 213385 | 205554 | 205395 / 150 (21) | 23582 / 147 (12) | 8116 / 128 (6) | 197279 / 150 (20) |
| ab3dmot_lt3d | 4506 | 231666 | 223771 | 223577 / 150 (20) | 28452 / 146 (11) | 8582 / 131 (5) | 214995 / 150 (20) |

Car PD7 cells (PD7 items / logs; in-path items / logs):

| Cell | ab3dmot_lt3d | t1_lt3d |
|---|---|---|
| car · long · static | 81882 / 150; in-path 2810 / 93 | 67520 / 149; in-path 1615 / 70 |
| car · long · straight | 13897 / 123; in-path 2665 / 73 | 19802 / 135; in-path 3612 / 87 |
| car · long · turning | 4033 / 123; in-path 534 / 58 | 3020 / 106; in-path 488 / 42 |
| car · long · new | 3918 / 138; in-path 428 / 63 | 4252 / 131; in-path 356 / 54 |
| car · lat · static | 40515 / 149; in-path 561 / 56 | 36013 / 146; in-path 432 / 41 |
| car · lat · straight | 3407 / 102; in-path 227 / 35 | 6045 / 122; in-path 369 / 50 |
| car · lat · turning | 1575 / 98; in-path 209 / 25 | 2055 / 93; in-path 310 / 28 |
| car · lat · new | 1526 / 122; in-path 70 / 25 | 1593 / 111; in-path 67 / 22 |

## 3. Readings (descriptive)

- **HOTA.** AB3DMOT reaches car 0.57, pedestrian 0.52 and cyclist 0.26, against T1/T3's 0.79, 0.72 and 0.51 on the same LT3D detections. Its detection-box and filter-state outputs are within 0.003 of each other.
- **Why lower.** At 2 Hz its constant-velocity filter steps one frame at a time with IoU matching at 0.1. The large inter-frame displacement makes it switch identities often: about 4,700 car IDS against about 80 for T1/T3. Its unit Q and R and its high initial velocity variance are tuned for 10 Hz KITTI-style use, not for this setting.
- **AMOTA.** On the nuScenes protocol its AMOTA is low (car 0.33, cyclist 0.00), because every detection above 0.1 becomes an output box. HOTA, with its tuned score threshold, is the fairer summary for it.
- **Stage A.** It gives PD7 counts of the same order as T1/T3 (223,577 PD7 items; 20 evaluable cells). Every count comes from its own filter state and its own propagation.
- **Role.** AB3DMOT stays descriptive (Choice 11). It is not part of H1.

## 4. Files

`50_CODE/av2/av2_ab3dmot_v04.py` (the run; v01–v03 kept), `shims_lt3d/data/utils.py`, `test_av2_ab3dmot_fast_v01.py`, `run_av2_queue7_v01.sh`; outputs `30_DATA/av2_trk_v01/export_ab3dmot_v04w6/`, `30_DATA/av2_cache_stageA_v01/cache_stageA_ab3dmot_lt3d/`, `items/items_k8_v04_av2_stageA_ab3dmot_lt3d.npz`; metrics `60_RESULTS/av2_trk/hota/AV2_HOTA_ab3dmot_{det,kf}.json`, `metrics/AV2_metrics_ab3dmot_{det,kf}.json`.
