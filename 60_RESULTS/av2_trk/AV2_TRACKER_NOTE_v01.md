# Argoverse 2 validation: tracker stage of the external confirmation (v01, 1–2 Nov 2026)

**What this is.** The tracker port for the independent confirmation planned in `90_DECISIONS/D15_EXTERNAL_DATA_PROPOSAL_v01.md` §3 steps 3–5: CANMOT (T1, T2) and Poly-MOT (T3) run on Argoverse 2 (AV2) val with both detectors of `60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md`, their exports, tracking metrics and the item/stratum **counts**. Design (written first): `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md`.

**Outcome statement (D15 §4).** On AV2 nothing was computed beyond tracker outputs (states, covariances), ground-truth association, tracking metrics and counts. **No prediction error, residual, projected error aᵀe, score U, exceedance, margin, NEES/ANEES, coverage, or any quantity comparing a predicted state or covariance with a ground-truth position at a later time was computed on AV2.** The 2 s propagation and the residual step (`av2_horizon_prep_v01.py`) were run on nuScenes only; the script refuses AV2 input without a frozen-plan hash. The tracking metrics are a re-implementation that leaves out the NEES/Mahalanobis side computations of CANMOT's modified devkit, and report no MOTP/AMOTP. The only GT read at a later frame is the *existence* (with ≥ 1 interior point) of the paired `track_uuid` at k + 4, never its position.

## 1. What ran

| Step | Script (all in `50_CODE/av2/`) | Output | Result |
|---|---|---|---|
| Arrow reader (no pyarrow, no download) | `av2_feather_v01.py` | — | reads `annotations.feather`, `city_SE3_egovehicle.feather` (uncompressed Arrow IPC) |
| GT preparation | `av2_gt_prep_v01.py` | `30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json` (sha256 9642db5b…) | 150 logs, 4,806 frames, 278,242 mapped annotations (car 196,582; pedestrian 61,986; cyclist 1,321; truck 11,494; bus 3,900; trailer 2,392; motorcycle 567). RB-1: 1,243 `BICYCLE` cuboids attached to a `BICYCLIST` (3,660 unridden); 528 `MOTORCYCLE` attached (1,106 unridden). GT velocity: 266,096 central, 12,089 one-sided, 57 NaN (not used by any count) |
| Tracker input | `av2_tracker_input_v01.py` | `30_DATA/av2_trk_v01/input/{lt3d,voxelnext}/` (4 whole-log subsets + receipt each) | see §2 |
| Trackers | `av2_track_v01.py` via `run_av2_track_v01.sh` → `run_av2_track_v02.sh` | `30_DATA/av2_trk_v01/export/<tracker>_<detector>/worker0-3/` (x1_export_v06 format) | see §3 |
| Native-vs-fast hull equivalence | same, `--logs` 2 logs, LT3D | `30_DATA/av2_trk_v01/equiv/` | see §3 |
| Horizon port test (nuScenes only) | `test_av2_horizon_on_nuscenes_v01.py` | `60_RESULTS/av2_trk/horizon_nuscenes_test/HORIZON_PORT_TEST_NUSCENES_v01.json` | **all identical** (§4) |
| Tracking-metric code validation (nuScenes only) | `av2_track_metrics_v01/v03.py` | `60_RESULTS/av2_trk/metrics/NUSC_VAL_T1_metric_validation_v0{1,3}.json` | see §5 |
| AV2 tracking metrics | `av2_track_metrics_v03.py` via `run_av2_analysis_v04.sh` | `60_RESULTS/av2_trk/metrics/AV2_metrics_<combo>.json` | §6 |
| Counts | `av2_counts_v01.py` | `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json` (+ `counts_parts/`) | §7 |
| Note tables | `av2_note_tables_v01.py` | the tables of §6–§7 are printed from the JSONs, not typed | |

## 2. Tracker input (adapter receipts `30_DATA/av2_trk_v01/input/<detector>/receipt.json`)

| | LT3D CenterPoint (primary) | VoxelNeXt |
|---|---|---|
| Detector rows (npz sha256) | 11,570,785 (c96ebcee…) | 1,143,076 (da9ca2c8…) |
| In the tracker-input mapping (§4.2 of the design) | 3,209,888 | 807,585 |
| Removed: outside the ±54 m ego-frame square | 0 | 514,742 |
| Removed: score < 0.1 (floor of the nuScenes input) | 2,579,489 | 0 |
| Removed: CANMOT's own class score filter `SF_thre` | 191,204 | 50,515 |
| **Boxes fed to the trackers** | **439,195** (car 264,630; pedestrian 120,475; cyclist 6,787; truck 30,031; bus 7,562; trailer 5,350; motorcycle 4,360) | **242,328** (car 126,345; pedestrian 97,823; cyclist 710; truck 10,731; bus 3,216; trailer 2,996; motorcycle 507) |
| Velocity | yes (ground velocity in ego axes, rotated to the city frame) | none (`has_velo = False`, shim S3) |
| Frames / logs / subsets | 4,806 / 150 / 4 whole-log subsets (≈ 110k boxes each) | same frames; 4 subsets |

The trackers' own score filter and NMS run again inside CANMOT's loader, unchanged.

## 3. Tracker runs and integrity

Five tracker × detector runs, each over the 4 subsets: **T1 × LT3D, T3 × LT3D, T2 × LT3D, T1 × VoxelNeXt, T3 × VoxelNeXt** (T2 × VoxelNeXt not run, §8). **All 20 worker exports PASS** every criterion of the x1_export_v06 record (P1–P6, T1–T2, F1–F4, C1–C5, K1, K2): pinned CANMOT commit 515d0792… and devkit e4818ff9…, clean tree, every frame exported once in order, every covariance of the configured dimension, finite, symmetric and positive definite in its x, y block, HPHᵀ recomputed from the owning filter equal to the native covariance (1e-9 relative), track counts bounded by detections. Exported records: T1 × LT3D 229,438; T3 × LT3D 229,469; T2 × LT3D 229,441; T1 × VoxelNeXt 274,837; T3 × VoxelNeXt 275,587. Native Qhull vs the numba hull (`--fast-convex`) on 2 LT3D logs: **identical** for T1 (2,615 records) and T3 (2,616 records). Actual 2 Hz Δt per worker: median 0.5003 s, range 0.4958–0.5999 s. Wall time 940–2,850 s per worker (CPU shared with the K8 run).

## 4. Horizon port, tested on nuScenes only

`test_av2_horizon_on_nuscenes_v01.py` on the first 3 val scenes of each setting's worker-0 export (T1 8,792 records, T2 8,787, T3 8,777): `av2_horizon_prep_v01 --propagate-only` vs `x1_horizon_prep_v04` (run from the CANMOT root as originally): **0 differing lines** over all 8 steps for T1, T2 and T3; h1s/h2s/h4s equal to the stored study files (`x1_horizon_v01`, `horizon_val_v02`, `horizon_val_v03`); `horizon_rows` (the outcome-boundary function) vs `x1_lib_v03.build_horizon_rows` on those scenes' rows with `x1_val_gt_v02`: **0 differing rows**. Result file: `60_RESULTS/av2_trk/horizon_nuscenes_test/HORIZON_PORT_TEST_NUSCENES_v01.json` (`all_identical: true`). The script was never run on AV2; its AV2 guard refuses propagation without `--allow-av2-propagation` and the residual step without a frozen-plan hash.

## 5. Tracking-metric code, validated on nuScenes only

`av2_track_metrics_v03.py` on the nuScenes val T1 export (`x1_export_val150_fast_v04`, the record-identical twin of the paper run) with `x1_val_gt_v02.json`, against CANMOT's reference devkit evaluation (`reproducibility/reference/local_canmot_sc.json`): AMOTA, MOTA, recall, IDS, TP, FP, FN and GT **equal to the last digit for bicycle, bus, car and pedestrian** (e.g. car AMOTA 0.8648777514719983, IDS 72, TP 49,025, FP 5,959, FN 9,220; pedestrian AMOTA 0.8340153133784283). v01 of the same code matched bicycle and bus before it was stopped. Files: `60_RESULTS/av2_trk/metrics/NUSC_VAL_T1_metric_validation_v01.json`, `_v03.json`.

## 6. Tracking metrics on AV2 (allowed by D15 §4)

Tracking metrics (nuScenes protocol; AMOTA over 40 recall thresholds, the rest at the best-MOTA threshold)

| Tracker × detector | Class | AMOTA | MOTA | Recall | TP | FP | FN | IDS | FRAG | GT boxes |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 CANMOT sc × LT3D CenterPoint | car | 0.923 | 0.840 | 0.910 | 72629 | 5543 | 7201 | 76 | 172 | 79906 |
| T1 CANMOT sc × LT3D CenterPoint | pedestrian | 0.873 | 0.754 | 0.866 | 23684 | 2938 | 3679 | 138 | 55 | 27501 |
| T1 CANMOT sc × LT3D CenterPoint | cyclist (bicycle class) | 0.572 | 0.449 | 0.650 | 268 | 83 | 144 | 0 | 1 | 412 |
| T3 Poly-MOT × LT3D CenterPoint | car | 0.923 | 0.840 | 0.910 | 72620 | 5516 | 7204 | 82 | 174 | 79906 |
| T3 Poly-MOT × LT3D CenterPoint | pedestrian | 0.870 | 0.751 | 0.849 | 23188 | 2541 | 4148 | 165 | 67 | 27501 |
| T3 Poly-MOT × LT3D CenterPoint | cyclist (bicycle class) | 0.570 | 0.449 | 0.650 | 268 | 83 | 144 | 0 | 1 | 412 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | car | 0.922 | 0.838 | 0.910 | 72620 | 5667 | 7208 | 78 | 179 | 79906 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | pedestrian | 0.873 | 0.755 | 0.866 | 23693 | 2921 | 3674 | 134 | 59 | 27501 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | cyclist (bicycle class) | 0.564 | 0.447 | 0.665 | 274 | 90 | 138 | 0 | 2 | 412 |
| T1 CANMOT sc × VoxelNeXt | car | 0.899 | 0.801 | 0.898 | 70923 | 6913 | 8168 | 815 | 315 | 79906 |
| T1 CANMOT sc × VoxelNeXt | pedestrian | 0.790 | 0.664 | 0.796 | 21588 | 3331 | 5611 | 302 | 122 | 27501 |
| T1 CANMOT sc × VoxelNeXt | cyclist (bicycle class) | 0.561 | 0.430 | 0.483 | 199 | 22 | 213 | 0 | 1 | 412 |
| T3 Poly-MOT × VoxelNeXt | car | 0.894 | 0.786 | 0.903 | 70901 | 8073 | 7783 | 1222 | 315 | 79906 |
| T3 Poly-MOT × VoxelNeXt | pedestrian | 0.699 | 0.558 | 0.737 | 19507 | 4159 | 7231 | 763 | 205 | 27501 |
| T3 Poly-MOT × VoxelNeXt | cyclist (bicycle class) | 0.541 | 0.403 | 0.471 | 190 | 24 | 218 | 4 | 4 | 412 |

nuScenes T1 v01 validation of the metric code: classes ['bicycle', 'bus'], all equal = True; unequal entries: []

nuScenes T1 v03 validation of the metric code: classes ['bicycle', 'bus', 'car', 'pedestrian'], all equal = True; unequal entries: []

Descriptive readings (no outcome involved): with the primary detector all three settings track cars at AMOTA 0.92 (nuScenes val, T1: 0.865) and pedestrians at 0.87; cyclists (412 GT boxes within 40 m) at 0.56–0.57. Without detector velocity (VoxelNeXt) the trackers lose 0.02–0.03 AMOTA on cars and switch identities 10–15 times more often (T1 815, T3 1,222 car IDS vs 76–82 with LT3D); Poly-MOT's CTRA pedestrians suffer most (AMOTA 0.70). GT boxes after the nuScenes filters (class range, ≥ 1 point): 110,042 of 278,242. Per-class cross-check: at every class's best-MOTA threshold the counting accumulator equals motmetrics' own event table (`crosscheck_equal` true in all 15 cells). HOTA: not computed (§8.8).

## 7. Counts on AV2 (`60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json`)

Definitions. *Record*: one exported track at one frame. *Paired*: `x1_lib_v03.build_table` persistent per-class Hungarian pairing with the 2 m gate, uncensored at k (the paired uuid annotated with ≥ 1 interior point). *In-path*: the nuScenes rule from estimates and ego poses (ego corridor from the frames k − 1, k; nuScenes ego footprint, §8.10). *Item*: a (record, axis) pair passing the separating-axis filter, here **at the current-estimate geometry** (range bin of the estimate, axes of the tracked box, ego pose at k). *Motion*: `m_lib_v04.motion_state` on the track's own positions. *k + 4 available*: the paired uuid is annotated with points at k + 4 (existence only). All per-stratum tables (group × range × axis × motion × population × pairing × horizon status, with logs per cell) are in the JSON (`items_table`, `records_table`, `summaries`).

### Headline: car, in-path, paired items at the current-estimate geometry (t = 0 family), items / logs

| Tracker × detector | < 20 m | 20–40 m | ≥ 40 m |
|---|---|---|---|
| T1 CANMOT sc × LT3D CenterPoint | 2928 / 123 | 2193 / 122 | 306 / 59 |
| T3 Poly-MOT × LT3D CenterPoint | 2694 / 122 | 2073 / 120 | 287 / 57 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | 2866 / 122 | 2188 / 123 | 338 / 60 |
| T1 CANMOT sc × VoxelNeXt | 3169 / 128 | 2532 / 126 | 354 / 62 |
| T3 Poly-MOT × VoxelNeXt | 2888 / 128 | 2141 / 129 | 292 / 62 |

### Frames, tracks, records, association (counts)

| Tracker × detector | frames | tracks | export records | records k ≥ 1 | in-path records | paired in-path | unpaired | censored at k | id switches | paired records: k+4 available / censored / no k+4 frame |
|---|---|---|---|---|---|---|---|---|---|---|
| T1 CANMOT sc × LT3D CenterPoint | 4806 | 33362 | 229438 | 222366 | 5894 | 4899 | 89486 | 7642 | 611 | 97555 / 11271 / 16412 |
| T3 Poly-MOT × LT3D CenterPoint | 4806 | 33451 | 229469 | 222397 | 5706 | 4731 | 89530 | 7640 | 684 | 97532 / 11262 / 16433 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | 4806 | 33381 | 229441 | 222369 | 6032 | 5000 | 89567 | 7703 | 623 | 97417 / 11277 / 16405 |
| T1 CANMOT sc × VoxelNeXt | 4806 | 42514 | 274837 | 268482 | 6477 | 5313 | 138766 | 5952 | 1919 | 96504 / 10872 / 16388 |
| T3 Poly-MOT × VoxelNeXt | 4806 | 42758 | 275587 | 269232 | 6176 | 5074 | 138876 | 5996 | 2918 | 96853 / 10936 / 16571 |

### Paired items by group × range × axis × population (t = 0 geometry), items / logs


T1 CANMOT sc × LT3D CenterPoint (in brackets: of which the paired object is annotated with points at k + 4)

| Group | Axis | Population | < 20 m | 20–40 m | ≥ 40 m |
|---|---|---|---|---|---|
| car | long | inpath | 2237 / 121 (1961) | 1704 / 120 (1559) | 217 / 59 (211) |
| car | long | not_inpath | 15024 / 149 (12541) | 32438 / 150 (25492) | 26770 / 150 (19486) |
| car | lat | inpath | 691 / 90 (590) | 489 / 87 (443) | 89 / 39 (87) |
| car | lat | not_inpath | 17112 / 148 (14339) | 30006 / 150 (23586) | 24404 / 150 (17712) |
| pedestrian | long | inpath | 89 / 25 (69) | 43 / 16 (32) | 4 / 4 (4) |
| pedestrian | long | not_inpath | 8909 / 121 (7071) | 13727 / 136 (10447) | 8846 / 133 (6239) |
| pedestrian | lat | inpath | 72 / 24 (61) | 49 / 17 (39) | 4 / 4 (4) |
| pedestrian | lat | not_inpath | 9161 / 121 (7294) | 13474 / 136 (10310) | 8620 / 133 (6082) |
| cyclist | long | inpath | 0 / 0 (0) | 7 / 2 (6) | 2 / 1 (2) |
| cyclist | long | not_inpath | 129 / 13 (89) | 177 / 20 (137) | 137 / 22 (103) |
| cyclist | lat | inpath | 1 / 1 (1) | 13 / 2 (12) | 4 / 1 (4) |
| cyclist | lat | not_inpath | 145 / 13 (96) | 180 / 20 (141) | 132 / 22 (99) |

T3 Poly-MOT × LT3D CenterPoint (in brackets: of which the paired object is annotated with points at k + 4)

| Group | Axis | Population | < 20 m | 20–40 m | ≥ 40 m |
|---|---|---|---|---|---|
| car | long | inpath | 2198 / 120 (1939) | 1678 / 120 (1542) | 211 / 57 (203) |
| car | long | not_inpath | 15173 / 149 (12651) | 32659 / 150 (25647) | 26824 / 150 (19502) |
| car | lat | inpath | 496 / 90 (449) | 395 / 84 (367) | 76 / 36 (73) |
| car | lat | not_inpath | 17306 / 149 (14507) | 30243 / 150 (23746) | 24379 / 150 (17698) |
| pedestrian | long | inpath | 78 / 25 (66) | 37 / 12 (28) | 3 / 3 (3) |
| pedestrian | long | not_inpath | 9032 / 122 (7139) | 13683 / 136 (10416) | 8818 / 133 (6220) |
| pedestrian | lat | inpath | 63 / 20 (55) | 41 / 14 (32) | 3 / 3 (3) |
| pedestrian | lat | not_inpath | 9189 / 121 (7298) | 13451 / 136 (10265) | 8599 / 133 (6059) |
| cyclist | long | inpath | 0 / 0 (0) | 9 / 2 (8) | 2 / 1 (2) |
| cyclist | long | not_inpath | 129 / 13 (89) | 176 / 20 (135) | 134 / 22 (101) |
| cyclist | lat | inpath | 1 / 1 (1) | 13 / 2 (12) | 4 / 1 (4) |
| cyclist | lat | not_inpath | 146 / 13 (97) | 180 / 20 (140) | 130 / 22 (98) |

T2 CANMOT sample/trainval × LT3D CenterPoint (in brackets: of which the paired object is annotated with points at k + 4)

| Group | Axis | Population | < 20 m | 20–40 m | ≥ 40 m |
|---|---|---|---|---|---|
| car | long | inpath | 2284 / 120 (1997) | 1745 / 121 (1589) | 248 / 60 (235) |
| car | long | not_inpath | 15057 / 149 (12564) | 32376 / 150 (25426) | 26717 / 150 (19444) |
| car | lat | inpath | 582 / 88 (511) | 443 / 88 (399) | 90 / 39 (87) |
| car | lat | not_inpath | 17140 / 148 (14354) | 29926 / 150 (23545) | 24316 / 150 (17648) |
| pedestrian | long | inpath | 84 / 24 (67) | 37 / 15 (27) | 2 / 2 (2) |
| pedestrian | long | not_inpath | 8844 / 121 (6959) | 13729 / 136 (10439) | 8845 / 133 (6238) |
| pedestrian | lat | inpath | 69 / 23 (59) | 46 / 15 (37) | 2 / 2 (2) |
| pedestrian | lat | not_inpath | 9118 / 121 (7233) | 13481 / 136 (10320) | 8572 / 132 (6042) |
| cyclist | long | inpath | 1 / 1 (1) | 8 / 2 (7) | 2 / 1 (2) |
| cyclist | long | not_inpath | 111 / 13 (80) | 179 / 20 (138) | 132 / 21 (100) |
| cyclist | lat | inpath | 2 / 1 (2) | 15 / 2 (14) | 4 / 1 (4) |
| cyclist | lat | not_inpath | 144 / 13 (95) | 169 / 20 (130) | 134 / 22 (100) |

T1 CANMOT sc × VoxelNeXt (in brackets: of which the paired object is annotated with points at k + 4)

| Group | Axis | Population | < 20 m | 20–40 m | ≥ 40 m |
|---|---|---|---|---|---|
| car | long | inpath | 2306 / 124 (2015) | 1760 / 125 (1591) | 194 / 60 (185) |
| car | long | not_inpath | 14698 / 149 (12258) | 31864 / 150 (25039) | 26025 / 150 (18967) |
| car | lat | inpath | 863 / 98 (744) | 772 / 111 (694) | 160 / 55 (151) |
| car | lat | not_inpath | 16258 / 149 (13682) | 29379 / 150 (22994) | 24221 / 150 (17560) |
| pedestrian | long | inpath | 89 / 30 (74) | 64 / 27 (51) | 5 / 5 (5) |
| pedestrian | long | not_inpath | 8770 / 121 (6967) | 12958 / 135 (9927) | 8389 / 132 (5939) |
| pedestrian | lat | inpath | 109 / 32 (92) | 59 / 27 (46) | 4 / 4 (4) |
| pedestrian | lat | not_inpath | 8644 / 121 (6889) | 13103 / 136 (10037) | 8445 / 132 (5987) |
| cyclist | long | inpath | 2 / 1 (2) | 11 / 1 (11) | 1 / 1 (1) |
| cyclist | long | not_inpath | 125 / 13 (85) | 161 / 17 (133) | 95 / 16 (78) |
| cyclist | lat | inpath | 2 / 1 (2) | 12 / 1 (12) | 1 / 1 (1) |
| cyclist | lat | not_inpath | 132 / 13 (91) | 146 / 17 (121) | 81 / 16 (68) |

T3 Poly-MOT × VoxelNeXt (in brackets: of which the paired object is annotated with points at k + 4)

| Group | Axis | Population | < 20 m | 20–40 m | ≥ 40 m |
|---|---|---|---|---|---|
| car | long | inpath | 2236 / 126 (1980) | 1634 / 129 (1481) | 191 / 62 (185) |
| car | long | not_inpath | 15010 / 149 (12501) | 32417 / 150 (25409) | 26195 / 150 (19109) |
| car | lat | inpath | 652 / 106 (575) | 507 / 104 (459) | 101 / 44 (99) |
| car | lat | not_inpath | 16800 / 148 (14041) | 29391 / 150 (22945) | 23854 / 150 (17290) |
| pedestrian | long | inpath | 182 / 48 (154) | 56 / 28 (47) | 4 / 4 (4) |
| pedestrian | long | not_inpath | 8824 / 121 (6987) | 13384 / 136 (10223) | 8488 / 132 (6015) |
| pedestrian | lat | inpath | 160 / 47 (140) | 54 / 28 (45) | 4 / 4 (4) |
| pedestrian | lat | not_inpath | 8883 / 121 (7018) | 13199 / 136 (10085) | 8361 / 132 (5912) |
| cyclist | long | inpath | 3 / 2 (3) | 16 / 1 (16) | 1 / 1 (1) |
| cyclist | long | not_inpath | 128 / 13 (86) | 158 / 17 (129) | 94 / 15 (79) |
| cyclist | lat | inpath | 4 / 2 (4) | 13 / 1 (13) | 1 / 1 (1) |
| cyclist | lat | not_inpath | 131 / 13 (85) | 146 / 17 (120) | 79 / 15 (68) |

### Car in-path paired items by axis × motion state (t = 0 geometry, pooled over range), items / logs

| Tracker × detector | axis | static | straight | turning | new |
|---|---|---|---|---|---|
| T1 CANMOT sc × LT3D CenterPoint | long | 564 / 78 | 3146 / 122 | 258 / 52 | 190 / 100 |
| T1 CANMOT sc × LT3D CenterPoint | lat | 331 / 56 | 647 / 83 | 224 / 42 | 67 / 40 |
| T3 Poly-MOT × LT3D CenterPoint | long | 517 / 78 | 3086 / 124 | 292 / 63 | 192 / 99 |
| T3 Poly-MOT × LT3D CenterPoint | lat | 317 / 62 | 433 / 74 | 153 / 42 | 64 / 37 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | long | 569 / 81 | 3265 / 123 | 232 / 46 | 211 / 107 |
| T2 CANMOT sample/trainval × LT3D CenterPoint | lat | 333 / 57 | 536 / 83 | 177 / 39 | 69 / 38 |
| T1 CANMOT sc × VoxelNeXt | long | 709 / 90 | 3069 / 126 | 324 / 74 | 158 / 90 |
| T1 CANMOT sc × VoxelNeXt | lat | 465 / 76 | 959 / 108 | 279 / 66 | 92 / 63 |
| T3 Poly-MOT × VoxelNeXt | long | 633 / 94 | 2769 / 124 | 440 / 105 | 219 / 107 |
| T3 Poly-MOT × VoxelNeXt | lat | 414 / 83 | 490 / 90 | 261 / 79 | 95 / 64 |

Readings, descriptive only. Car in-path paired items per tracker × detector: 5,050–6,060 (< 20 m 2,690–3,170; 20–40 m 2,070–2,530; ≥ 40 m 290–350), from 120–129 logs in the two near bins and 57–62 logs at ≥ 40 m; 89–91 % of them (86–98 % per cell) have the paired car annotated at k + 4. The lateral axis has 2.4–4.2× fewer in-path car items than the longitudinal one (nuScenes X2, car < 20 m at 2 s: 2.4×). In-path pedestrians give at most ~180 items per range × axis cell and in-path cyclists at most 16, from 1–2 logs: below any evaluable size; their not-in-path populations are large (pedestrians ≈ 8–14 k items per cell over 121–136 logs; cyclists 80–180 items over 13–22 logs). These are t = 0 counts; the 2 s family re-bins items by the predicted range and predicted ego pose (§8.11).

## 8. Deviations from the nuScenes pipeline and from D15, each with its reason

1. **Tracker-input classes.** AV2 categories mapped onto all seven nuScenes tracking classes (design §4.2) so that the score filter, cross-class NMS and class parameters act as on nuScenes; the analysis keeps only the D15 classes car := `REGULAR_VEHICLE`, pedestrian := `PEDESTRIAN`, cyclist := `BICYCLIST`. Truck/bus/trailer/motorcycle are tracked and counted but are descriptive only.
2. **Ridden two-wheelers (RB-1, written in the design before any GT overlap was examined).** A `BICYCLE` cuboid with BEV IoU ≥ 0.10 to a `BICYCLIST` cuboid is the ridden bicycle and is dropped; the cyclist is the rider's cuboid. Unridden bicycles are in no class (the nuScenes analogue is the rack exclusion; nuScenes' bicycle class also contains parked bicycles outside racks, AV2's cyclist group does not). Detected `BICYCLE`/`MOTORCYCLE` boxes are not fed to the trackers.
3. **Detector score floor 0.1 for LT3D** (added to the design after the first draft, from the nuScenes input file: its minimum score is 0.1000001 over 701,327 boxes, so CANMOT's `SF_thre` = 0 for bus/truck meant 0.1 on nuScenes). 2,579,489 mapped LT3D boxes below 0.1 removed; VoxelNeXt already had this floor.
4. **Range.** Tracker input restricted to the ego-frame BEV square |x|, |y| ≤ 54 m (LT3D's range; nuScenes CenterPoint ±51.2 m); 514,742 mapped VoxelNeXt boxes outside removed. Range strata are the nuScenes bins; the long-range remainder is not tracked.
5. **VoxelNeXt has no velocity.** `has_velo = False`; shim S3 (7 × 7 block of CANMOT's/Poly-MOT-CA's 9 × 9 R; vx, vy initial variance 10 = CANMOT's own unobserved-vz rule). The VoxelNeXt exports' native covariance is 7 × 7 (x, y block unchanged in place).
6. **Timing.** Trackers keep `LiDAR_interval = 0.5 s`; actual 2 Hz Δt 0.4958–0.5999 s (median 0.5003 s; one dropped sweep gives 0.5999), recorded per frame.
7. **No pyarrow** in the environment and no downloads: `av2_feather_v01.py` parses the Arrow IPC files (all AV2 tables used were uncompressed).
8. **Tracking metrics.** nuScenes protocol re-implemented without NEES/TP errors/MOTP (CANMOT's devkit computes NEES on every matched TP); validated equal to CANMOT's reference on nuScenes val (4 classes × 8 fields). **HOTA not computed** (the av2 evaluator is not installed and installing it means downloading packages). AV2 metrics for car, pedestrian, cyclist only.
9. **T2 on VoxelNeXt not run** (time; T2 is the optional Q-sensitivity arm, run on the primary detector).
10. **Ego footprint.** The in-path rule keeps the nuScenes constants (4.1 × 1.8 m + 0.5 m, rear axle 1.39 m behind the centre); the AV2 ego (Ford Fusion) is ≈ 4.9 × 1.9 m. To be decided in the confirmatory plan.
11. **Counts at the current-estimate geometry (t = 0).** The method-stage strata use the 2 s predicted geometry (predicted range and axes, predicted ego pose). That needs `av2_horizon_prep_v01.propagate` (tracker output only, allowed by D15 §4) which was **not run on AV2** by instruction; the h = 2 s counts will differ in range assignment. Horizon availability is counted by existence only.
12. **Scene = log.** AV2 logs are single drives of 15.5–20 s (31–40 frames), so scene and log counts coincide; the nuScenes "≥ 39 scenes and ≥ 8 logs" evaluability rule collapses to one condition.
13. **Velocity convention checked, not assumed.** LT3D's (vx, vy) is the ground velocity in ego axes (parked cars ≈ 0 m/s at every ego speed), so the conversion is a rotation only.
14. **Stopped and replaced jobs (all on purpose).** Tracker driver `run_av2_track_v01.sh` → replaced by `run_av2_track_v02.sh` (single-threaded BLAS, ≤ 3 tracker processes; the four jobs v01 had started kept running and were used) → `run_av2_track_v03.sh` (T2 LT3D workers 2–3; T2 VoxelNeXt dropped). Analysis queue `run_av2_analysis_v01.sh` → `_v02.sh` → `_v03.sh` → `_v04.sh` → `run_av2_analysis_lane_v01.sh` (four lanes). Metric code `av2_track_metrics_v01.py` → `_v02.py` → `_v03.py` (exact speed-ups); the v01 nuScenes validation run was stopped by hand after 2 classes and the v01 AV2 T1 × LT3D metrics run (> 25 min on cars) was stopped and redone with v03; the v03 nuScenes validation crashed in its comparison block after computing all four classes (key error, fixed) and its values were compared with the reference from the run log (`NUSC_VAL_T1_metric_validation_v03.json`). No result was computed twice with different outcomes.

## 9. What was not ported or not done

- HOTA (§8.8); the av2 tracking evaluator.
- The 10 Hz sensitivity run and LT3D's AB3DMOT public baseline tracker (D15 §3 step 3) — not part of this step.
- The 2 s propagation on AV2 and every count at the predicted geometry (§8.11) — a decision for the researcher; `av2_horizon_prep_v01.py --propagate-only --allow-av2-propagation` does it without touching ground truth.
- T2 × VoxelNeXt (§8.9); tracking metrics for truck, bus, trailer and motorcycle.

## 10. Outcome-blindness, restated

The functions run on AV2 were: `av2_feather_v01`, `av2_gt_prep_v01` (GT per frame; GT velocity by central differences, unused), `av2_tracker_input_v01`, `av2_track_v01` (the trackers), `av2_track_metrics_v03` (CLEAR/AMOTA event counts; no NEES, no TP errors, no MOTP/AMOTP), `av2_counts_v01` (`x1_lib_v03.build_table` association at time k, the separating-axis filter on estimates, `m_lib_v04` motion state on estimates, existence of the paired uuid at k + 4). `x1_lib_v03.build_table` also sets two per-record association flags (`resid_gt_gate`, `contested`); they were never aggregated or written. Not run on AV2: `av2_horizon_prep_v01` (both parts), `x1_horizon_prep_v04`, `x1_lib_v03.build_horizon_rows / cell_items / orientation_null / crc_threshold / inflation_needed`, `m_data_v04.load_split`, `m_lib_v04.build_items`, CANMOT's `evaluate()` and devkit `TrackingEvaluation`. **No prediction error, residual, projected error, U, exceedance, margin, NEES/ANEES or coverage was computed on Argoverse 2.**
