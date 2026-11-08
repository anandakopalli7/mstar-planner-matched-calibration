# AV2 tracker port: design (v02, 2 Nov 2026; v01 kept unchanged; v02 = v01 sections 1-11 verbatim plus section 12, the stage-A and stage-B design written before any stage-A cache was built)

**Status.** Written before any tracker was run on Argoverse 2 (AV2) and before any AV2 ground-truth (GT) overlap, pairing or count was computed. The only AV2 facts used here are detector-side or pose-side and were checked with two outcome-free probes (scratch scripts, no GT content beyond timestamps): (P-a) the 2 Hz frame rule and its timing; (P-b) the velocity convention of the LT3D detections against ego speed. Both are reported in §2 and §3.

**Governing documents.** `90_DECISIONS/D15_EXTERNAL_DATA_PROPOSAL_v01.md` §3–§4 (protocol, outcome-blind rule), `30_PRIOR_ART/P7_L3_EXTERNAL_DATA_FEASIBILITY_v01.md` §D (risks), `20_DESIGN/E01_EVIDENCE_DOSSIER_v02.md` §2 (the nuScenes pipeline being ported), `60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md` (detections).

**Outcome-blind rule (D15 §4), restated as an engineering boundary.** On AV2 this port computes only tracker outputs (states, covariances), tracking metrics, GT association and counts. It never computes a prediction error, residual, projected error aᵀe, score U, exceedance, margin, NEES/ANEES, coverage, or anything derived from comparing a predicted state or covariance with a GT position at a later time. §9 lists every function on either side of the boundary.

---

## 1. Files

| File | Role | Runs on AV2? |
|---|---|---|
| `av2_feather_v01.py` | Pure-Python Arrow IPC (Feather v2) reader. Needed because the CANMOT environment has no `pyarrow` and installing one would mean downloading packages. Parses bytes only; supports the column types AV2 uses; fails loudly on anything else. | yes (reads `annotations.feather`, `city_SE3_egovehicle.feather`) |
| `av2_common_v01.py` | Constants and helpers shared by the port: class mappings (§4), ridden-two-wheeler rule (§4.3), pose interpolation-free lookup, quaternion algebra, token format, range filter. | yes |
| `av2_tracker_input_v01.py` | Adapter: AV2 detection tables (both detectors) → CANMOT/Poly-MOT detection JSON (nuScenes result format, city frame) + first-token table + per-worker subsets + receipt. | yes |
| `av2_gt_prep_v01.py` | AV2 GT → the nuScenes-format GT JSON that `x1_lib_v03` reads (samples with ego pose; annotations with mapped class, centre, size, yaw, central-difference velocity, `num_pts` = `num_interior_pts`). Reads GT; computes no residual. | yes |
| `av2_track_v01.py` | Runner: T1 / T2 / T3 on one detector subset; per-frame export identical in format to `x1_export_v06.py` (it imports that file's verbatim `run.py` copies). | yes |
| `av2_track_metrics_v01.py` | Tracking metrics (AMOTA, MOTA, IDS, recall, …) by the nuScenes protocol, re-implemented on the devkit's own `MOTAccumulatorCustom` and `create_motmetrics`, **without** the NEES and TP-error side computations of CANMOT's modified devkit (§9). | yes |
| `av2_counts_v01.py` | Counts: frames, tracks, records, matched records, items per stratum × population. Estimates and association only. | yes |
| `av2_horizon_prep_v01.py` | The horizon step ported: `propagate()` (= `x1_horizon_prep_v04`), `horizon_rows()` (= `x1_lib_v03.build_horizon_rows`, the first code that reads a GT position at k + h). Refuses AV2 input unless given the SHA-256 of a frozen plan. | **no** (tested on nuScenes only) |
| `test_av2_horizon_on_nuscenes_v01.py` | Shows `av2_horizon_prep_v01` reproduces `x1_horizon_prep_v04` (and `build_horizon_rows`) exactly on nuScenes exports. | nuScenes only |

Outputs: `30_DATA/av2_trk_v01/` (adapter JSON, GT JSON, tracker exports), `60_RESULTS/av2_trk/` (metrics, counts, note). No existing file is modified; nothing in `third_party/` is edited.

## 2. Frames, sample tokens, timing

- **Frames.** The 2 Hz protocol of the nuScenes studies: every 5th lidar sweep of each log, starting at sweep 0 (LT3D's `VAL_SAMPLE_RATE`; both detectors were run on exactly these frames). Probe P-a: 150 logs, 23,547 sweeps, **4,806 frames**, first frame = sweep 0 in every log, index step 5 everywhere, 31–40 frames per log (median 32); every frame has annotations at its exact timestamp.
- **Sample token.** `"<log_id>_<timestamp_ns>"`. **Scene** = the log (AV2 has one continuous drive per log; there is no scene/log distinction, so log-cluster resampling and scene-level counts coincide).
- **Order.** Logs sorted by log id; frames in time order within a log; one tracker reset per log (CANMOT's first-token mechanism, `is_first_frame`).
- **Timing.** Δt between consecutive 2 Hz frames (P-a): min 0.4958 s, 1st percentile 0.4996, median 0.5003, 99th percentile 0.5004, max 0.5999 s (a dropped sweep). The trackers use their configured constant `LiDAR_interval = 0.5 s` exactly as on nuScenes (whose keyframes are also only nominally 0.5 s apart). The actual Δt is recorded per frame in the export's per-frame file; the in-path rule and the motion state use the actual timestamps, as on nuScenes.

## 3. Ego pose and the ego → city conversion

- **Pose.** `city_SE3_egovehicle.feather` holds the 6-DOF pose of the ego-vehicle frame (origin at the rear-axle centre, x forward, y left, z up — the same convention as nuScenes' `ego_pose`) in the city frame, at every sensor timestamp. Every 2 Hz frame timestamp is present exactly in the pose table; the port looks the pose up by exact timestamp and stops if it is missing (no interpolation).
- **Detections** are AV2 detection tables in the ego frame of their sweep. For a detection with ego-frame centre t, rotation q and velocity (vx, vy) and pose (R, p):
  - centre: `t_city = R t + p` (3-D);
  - rotation: `q_city = q_pose ⊗ q` (Hamilton product, w-first), then CANMOT's own sign normalisation (`NuscBox.abs_orientation_axisZ`);
  - size: AV2 (length, width, height) → nuScenes `wlh` order (width, length, height);
  - velocity: `v_city = R [vx, vy, 0]ᵀ`, keeping x, y. **Rotation only, no ego-velocity term**: probe P-b showed that LT3D's (vx, vy) is the object's ground velocity expressed in ego axes (median detected speed of REGULAR_VEHICLE detections with score > 0.5 is 0.01 m/s whether the ego is still or moving at 6–10 m/s; 63–68 % of them are below 0.5 m/s in every ego-speed band, i.e. parked cars read as still). This is also the nuScenes CenterPoint convention.
- **VoxelNeXt** regresses no velocity (§5).

## 4. Classes

### 4.1 Analysis classes (D15 §3.5, fixed before download)

car := `REGULAR_VEHICLE`; pedestrian := `PEDESTRIAN`; cyclist := `BICYCLIST` (with §4.3). These three are the analysis groups; the range strata are the nuScenes bins (< 20, 20–40, ≥ 40 m), and the motion strata are the method stage's (static / straight / turning / new; `m_lib_v04.motion_state`, unchanged).

### 4.2 Tracker-input mapping (AV2 category → the nuScenes tracking class whose parameters are used)

On nuScenes the trackers received all seven tracking classes, and the score filter, the cross-class ("blend") NMS and the class-specific parameters acted on all of them. To keep the trackers' operating conditions, AV2 detections are mapped onto the same seven classes; the analysis then keeps only §4.1.

| nuScenes tracking class (CANMOT label) | AV2 categories fed | Analysis group |
|---|---|---|
| car (2) | `REGULAR_VEHICLE` | car |
| pedestrian (4) | `PEDESTRIAN` | pedestrian |
| bicycle (0) | `BICYCLIST` | cyclist |
| motorcycle (3) | `MOTORCYCLIST` | (two-wheeler, descriptive only) |
| bus (1) | `BUS`, `ARTICULATED_BUS`, `SCHOOL_BUS` | (large, descriptive only) |
| truck (6) | `TRUCK`, `BOX_TRUCK`, `TRUCK_CAB`, `LARGE_VEHICLE` | (large, descriptive only) |
| trailer (5) | `VEHICULAR_TRAILER` | (large, descriptive only) |

Not fed (no nuScenes tracking counterpart, or the vehicle part of a ridden two-wheeler, §4.3): `BICYCLE`, `MOTORCYCLE`, `WHEELED_DEVICE`, `WHEELED_RIDER`, `STROLLER`, `WHEELCHAIR`, `DOG`, `OFFICIAL_SIGNALER`, `RAILED_VEHICLE`, `MESSAGE_BOARD_TRAILER`, static objects and signs. The same mapping is applied to the GT (for pairing and the tracking metrics). Known taxonomy difference, stated in P7 §D.3: nuScenes counts pick-ups as trucks, AV2 as `REGULAR_VEHICLE`.

### 4.3 Ridden two-wheelers (rule RB-1, written before any GT overlap was looked at)

AV2 annotates a person riding a bicycle as `BICYCLIST` and may annotate the bicycle under them as a separate `BICYCLE` cuboid (likewise `MOTORCYCLIST` / `MOTORCYCLE`). nuScenes has one box per ridden bicycle.

- **RB-1 (GT).** At each annotated sweep, a `BICYCLE` cuboid is *ridden* if its bird's-eye-view (BEV) rectangle has IoU ≥ 0.10 with a `BICYCLIST` cuboid of the same sweep (greedy one-to-one, highest IoU first). The **cyclist object is the `BICYCLIST` cuboid** (its centre, size, yaw and `track_uuid` are used unchanged); a ridden `BICYCLE` cuboid is attached to it (its uuid recorded) and dropped as a separate object. Unridden `BICYCLE` cuboids belong to no analysis class (they are parked or pushed bicycles; the nuScenes analogue is the bicycle-rack exclusion). The same rule with `MOTORCYCLIST` / `MOTORCYCLE` applies to the descriptive motorcycle class.
- Why the rider's cuboid and not the union: both detectors were trained on AV2's `BICYCLIST` cuboids, so the tracker estimates the rider's cuboid; pairing a track with a union box would add a systematic centre offset that the detector never had.
- **RB-1 (detections).** Detected `BICYCLE` / `MOTORCYCLE` boxes are not fed (§4.2), so a ridden two-wheeler enters the tracker once, as its rider class.
- The counts report how many `BICYCLE` cuboids RB-1 attached and how many were left unridden.

### 4.4 Class-specific tracker parameters (transferred unchanged)

Per CANMOT label (0 bicycle, 1 bus, 2 car, 3 motorcycle, 4 pedestrian, 5 trailer, 6 truck), from `config/poly_mot/*.yaml` and `config/poly_mot/preprocessing/centerpoint_nusc.yaml` at the pinned commit `515d0792…`:

- detector-side score floor **0.1** before the tracker's own filter. The nuScenes input had this floor implicitly (CenterPoint's test-time `score_threshold`; measured minimum 0.1000001 over all 701,327 boxes of `infos_val_10sweeps_withvelo_filter_True.json`), so CANMOT's `SF_thre` of 0 for bus and truck meant 0.1 in practice. VoxelNeXt's output is floored at 0.1 already (OpenPCDet `SCORE_THRESH`; minimum 0.1000001); LT3D's goes down to 0.018 and is floored here (added after the first draft of this design, when the adapter's counts showed 539k sub-0.1 bus/truck boxes from LT3D; decided from the nuScenes input file and the detector outputs only);
- score filter `SF_thre` {0: 0.14, 1: 0, 2: 0.16, 3: 0.16, 4: 0.16, 5: 0.10, 6: 0}; NMS `blend_nms`, `iou_bev`, threshold 0.08 (across all fed classes);
- association: first-stage metric `giou_3d` (bus `giou_bev`), thresholds {0: 1.55, 1: 1.34, 2: 1.31, 3: 1.44, 4: 1.69, 5: 1.25, 6: 1.21}; two-stage with `giou_bev`, threshold 1.0; Hungarian;
- life cycle: `max_age` {0: 10, 1: 10, 2: 15, 3: 20, 4: 10, 5: 10, 6: 20}, `min_hit` 1, score decay {0: 0.05, 1: 0.3, 2: 0.2, 3: 0.1, 4: 0.15, 5: 0.15, 6: 0.25}; output `punish_num` 1, no post-NMS;
- motion models and noise: **T1** `paper/local/canmot/sc` (CV, EKF-rotate, Q = `centerpoint/local/val/canmot_q`, R = `centerpoint/local/trainval/sample_cov`); **T2** `paper/local/sample/trainval` (same, Q = `centerpoint/local/trainval/CV_sample_cov`); **T3** `paper/baseline/poly_mot` (CTRA EKF for car, bus, pedestrian, truck; CA linear KF for bicycle, motorcycle, trailer; Poly-MOT's own Q, R, initial P).

**No parameter is re-tuned on AV2.** The score thresholds were set for nuScenes CenterPoint scores; LT3D's and VoxelNeXt's scores are calibrated differently, and this is part of what the transfer tests.

## 5. What differs from nuScenes, and how each difference is handled

| Difference | Handling |
|---|---|
| 10 Hz sweeps, 2 Hz protocol | Every 5th sweep (§2). 10 Hz is not run here (D15 lists it as a sensitivity). |
| No velocity from VoxelNeXt | `has_velo = False` for that detector. **T3's CTRA classes** support this natively (Poly-MOT's CTRA has a dedicated initial covariance for the no-velocity case); **T3's CA classes and T1/T2** need shim S3 (§8): the 7 × 7 measurement noise is the (x, y, z, w, l, h, yaw) block of CANMOT's own 9 × 9 R (the marginal of the same Gaussian), and the unobserved (vx, vy) receive initial variance 10, CANMOT's own rule for its unobserved vz (`P[8, 8] = 10.0`). The exported covariance is then 7 × 7 (its x, y block is in the same place). |
| Detector range: LT3D ±54 m, VoxelNeXt ±200 m | Tracker input from both detectors is restricted to the ego-frame BEV square \|x\|, \|y\| ≤ 54 m (LT3D's range; nuScenes CenterPoint's is ±51.2 m). The VoxelNeXt boxes removed are counted. Analysis strata stay the nuScenes bins (P7 §D.7). |
| Detector score calibration | Unchanged thresholds (§4.4). |
| No camera, no radar | Lidar-only detectors on both datasets for the trackers; GT visibility is `num_interior_pts ≥ 1` (nuScenes: lidar + radar points ≥ 1). |
| No velocity in AV2 GT | Central differences of the 10 Hz city-frame centres of the same `track_uuid` at the neighbouring sweeps (±1 sweep, gap ≤ 0.15 s each side); one-sided if only one neighbour exists; NaN if none (D15 §3.5; P7 §D.4). GT velocity is not used by any count. |
| No bicycle racks | No rack exclusion; unridden bicycles are outside every analysis class (§4.3). |
| Logs ≈ 15.5–20 s (31–40 frames) vs 20 s (≈ 40 keyframes) | Nothing to do; fewer k + 4 futures per log; reported in the counts. |
| Ego vehicle (Ford Fusion, ≈ 4.9 × 1.9 m) vs nuScenes Renault Zoe (4.1 × 1.8 m, rear axle 1.39 m behind centre) | **Unchanged** `x1_lib_v03` constants (footprint 4.1 × 1.8 m + 0.5 m, rear axle → centre 1.39 m) for the in-path rule in these counts. Flagged for the confirmatory plan: keep the nuScenes corridor (protocol unchanged) or use AV2's footprint. |
| One log = one scene | Scene counts = log counts. |

## 6. Export format

Identical to `x1_export_v06.py`: `x1_tracks.jsonl.gz` (one line per kept track per frame: `scene` (= log id), `seq_id`, `frame_id`, `sample_token`, `tracking_id`, `tracking_name`, `tracking_score`, `translation`, `size` (wlh), `rotation`, `velocity`, `cov9` (native measurement-space covariance HPHᵀ; 9 × 9, or 7 × 7 when `has_velo` is false), `state10` (the filter state: 10 for CV/CTRA, 13 for CA), `P10` (its covariance), `pool`), `x1_per_frame.json`, `x1_export_record.json` with the same integrity criteria (T1–T2, F1–F4, C1–C5, K1–K2) and AV2-specific provenance (P1–P4 unchanged; P5 = the adapter's subset file hash equals its receipt; P6 = experiment and `has_velo` as requested). The runner imports `x1_export_v06`'s verbatim copies of `run.py`'s loop body (`filter_classes`, `export_frame`, `postprocess_token`) and its state capture (`state_export`, `mat_check`), so the record content is produced by the same code.

## 7. GT table and pairing

`av2_gt_prep_v01.py` writes the GT in the format of `x1_gt_prep_v03.py`: `samples` (token, scene, index, timestamp in µs, `ego_xyz`, `ego_yaw` at the sweep) and `annotations` (sample token, `instance_token` = `track_uuid`, `tracking_name` by §4.2 and RB-1, translation and yaw in the city frame, size wlh, velocity by central differences, `num_pts` = `num_interior_pts`), plus `bicycle_racks: []`. With this, `x1_lib_v03.build_table` (persistent per-class Hungarian pairing, 2 m gate, in-path rule) runs unchanged on AV2 — see §9 for the two association-level flags it also computes.

## 8. Shims (no third-party file is edited)

| Id | What | Why |
|---|---|---|
| S1 | AV2 → nuScenes-format detection JSON (§3, §4.2) and a first-token table | CANMOT's `NuScenesloader` reads exactly this format; no devkit object is needed for tracking. |
| S2 | Runner bypasses `run.py`'s `validate_config` dataset/detector checks (nuScenes paths and hashes) but runs its Python-version and locked-dependency checks | The nuScenes checks do not apply; the environment checks do. |
| S3 | `has_velo = False` (VoxelNeXt): `CV.getMeaNoiseR` (T1/T2) and `CA.getMeaNoiseR` (T3's bicycle, motorcycle, trailer) return the (x, y, z, w, l, h, yaw) 7 × 7 block of their 9 × 9 R, and `ExtendedKalmanFilterRotate.initialize` (T1/T2) additionally sets the initial variance of vx and vy to 10. Patched in memory at run time by `av2_track_v01.install_no_velocity_shim` and recorded in the run record; T3's CTRA classes need nothing (Poly-MOT's own no-velocity branch). | CANMOT never ran without velocity: its CV R and Poly-MOT's CA R are 9 × 9 whatever `has_velo` is (the CA case would crash), and CANMOT's initial P would have zero velocity variance. |
| S4 | `fast_convex_v01` (the numba hull area) installed as on nuScenes (`--fast-convex`) | Speed; its equivalence to Qhull was shown record for record on nuScenes val (381,553 records, 0 differences). A 2-log native-vs-fast comparison is repeated on AV2. |
| S5 | `av2_feather_v01` instead of pyarrow | No pyarrow in the environment; no downloads. |
| S6 | Tracking metrics re-implemented on the devkit's `MOTAccumulatorCustom` + `create_motmetrics` without NEES/TP errors (§9) | CANMOT's modified devkit computes NEES and Mahalanobis coverage inside `TrackingEvaluation.accumulate_threshold`; the av2 evaluator is not installed. |

## 9. The outcome-blind boundary

**Never run on AV2:**

| Code | Why it is outcome |
|---|---|
| `av2_horizon_prep_v01.horizon_rows` (= `x1_lib_v03.build_horizon_rows`) | **The first function that reads a GT position at a later time (k + h)**; it sets `gx, gy` at the horizon and the 2 m drift flag `resid_gt_gate` from \|prediction − GT\|. |
| `av2_horizon_prep_v01.propagate` / `x1_horizon_prep_v04` | Pure tracker output (no GT), hence allowed by D15 §4, but **not run on AV2 in this step** by instruction; it has a `--propagate-only` mode so that the h = 2 s strata (predicted range) can be counted later if the researcher allows it. |
| `x1_lib_v03.cell_items`, `orientation_null`, `crc_threshold`, `inflation_needed`, `m_lib_v04.build_items` with `outcomes=True`, everything in `m_lib_v04` after `counts_by_l0` | Compute D, U, exceedance, thresholds or margins. |
| `m_data_v04.load_split` | Calls `build_horizon_rows` (computes the drift flag from the future GT position even when `outcomes=False`). **Split:** the counts use `m_data_v04.load_export_v2` (export reader + Poly-MOT velocity fix) and `m_lib_v04.motion_index / motion_features / motion_state` only. |
| CANMOT's devkit `TrackingEvaluation` / `TrackingEval` / `run.py` `evaluate()` | Computes NEES, Mahalanobis inside/outside shares and a χ² test on every matched TP. Replaced by S6. |

**Run on AV2 (allowed: tracker outputs, association, metrics, counts):** the adapter, the GT prep (reads GT at each frame; computes GT velocity; no comparison with any estimate), the runner, `x1_lib_v03.build_table` (association at time k: persistent Hungarian pairing with the 2 m gate, in-path from estimates and ego poses), `av2_track_metrics_v01` (CLEAR/AMOTA counts of matches, misses, false positives and switches; MOTP/AMOTP and the TP-error means are not computed), `av2_counts_v01`.

**Two association-level flags.** `build_table` also stores, per paired record at time k, `resid_gt_gate` (paired distance > 2 m) and `contested` (another same-class GT is closer). Both are same-time association diagnostics, not predictions; the counts never aggregate `resid_gt_gate` and report no distance.

**Horizon availability (existence only).** For sizing, the counts also report how many paired records have a k + 4 frame in their log and whether the paired `track_uuid` is annotated there with `num_interior_pts ≥ 1` (the nuScenes "censored at the horizon" count). This reads the existence and point count of the future annotation, **never its position**, and is computed by `av2_counts_v01.horizon_availability`, which receives only the set of (frame, uuid, num_pts ≥ 1) keys.

## 10. Run order

1. `av2_gt_prep_v01.py` → `30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json`.
2. `av2_tracker_input_v01.py` → `30_DATA/av2_trk_v01/input/<detector>/` (full file, first tokens, 4 subsets, receipt).
3. `av2_track_v01.py` per tracker × detector × subset (≤ 4 processes at a time) → `30_DATA/av2_trk_v01/export/<tracker>_<detector>/worker<i>/`.
4. `av2_track_metrics_v01.py` → `60_RESULTS/av2_trk/metrics/`.
5. `av2_counts_v01.py` → `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json`.
6. `test_av2_horizon_on_nuscenes_v01.py` (nuScenes only).

## 11. As run (addendum, 2 Nov 2026; sections 1–10 above are the design as written before the runs, plus the two marked additions in §4.4 and §8 S3)

- **Tracking metrics code**: `av2_track_metrics_v03.py` (v01 → v02 → v03 are successive exact speed-ups of the same protocol; v03 counts the CLEAR events with a line-for-line copy of `motmetrics.MOTAccumulator.update` and uses motmetrics itself once, at the best-MOTA threshold, for MT/ML/FRAG/TID/LGD and as a cross-check). Validated on nuScenes val T1 against CANMOT's reference evaluation (`reproducibility/reference/local_canmot_sc.json`): AMOTA, MOTA, recall, IDS, TP, FP, FN and GT equal to the last digit for bicycle, bus, car and pedestrian. Only car, pedestrian and bicycle (= cyclist) are evaluated on AV2 (time).
- **Drivers**: `run_av2_track_v01.sh` (stopped on purpose after its first four jobs, which kept running) → `run_av2_track_v02.sh` (≤ 3 tracker processes, single-threaded BLAS; stopped on purpose after dispatching T1/T3 on both detectors and T2 LT3D workers 0–1) → `run_av2_track_v03.sh` (T2 LT3D workers 2–3; **T2 on VoxelNeXt dropped for time**). Analysis: `run_av2_analysis_v01.sh` → `_v02` → `_v03` → `_v04` (each stopped on purpose and replaced; see the note) → `run_av2_analysis_lane_v01.sh` (parallel lanes).
- **Counts**: `av2_counts_v01.py` exactly as designed (t = 0 geometry; horizon availability by existence only).

## 12. Stage-A items, HOTA and AB3DMOT (design, 2 Nov 2026, written before any stage-A cache, K8 item, HOTA or AB3DMOT number existed)

Governing text: `90_DECISIONS/D16_DELEGATED_CHOICES_v03.md` Choices 8, 11, 13, 14.

### 12.1 Groups (D16 Choice 8; rule fixed here, before any outcome)

Four groups, the nuScenes ones (`k8_sim_v04.GROUP_OF_CLS`: car; pedestrian; two-wheeler = bicycle + motorcycle; large = truck + bus + trailer), reached through the tracker-input mapping of §4.2, which is unchanged:

| Group | nuScenes tracking classes | AV2 categories |
|---|---|---|
| car | car | `REGULAR_VEHICLE` |
| pedestrian | pedestrian | `PEDESTRIAN` |
| two-wheeler | bicycle, motorcycle | `BICYCLIST`, `MOTORCYCLIST` (riders; their `BICYCLE` / `MOTORCYCLE` cuboids attached and dropped by RB-1) |
| large | truck, bus, trailer | `TRUCK`, `BOX_TRUCK`, `TRUCK_CAB`, `LARGE_VEHICLE`, `BUS`, `ARTICULATED_BUS`, `SCHOOL_BUS`, `VEHICULAR_TRAILER` |

D15's cyclist := `BICYCLIST` is the two-wheeler group's bicycle class; `MOTORCYCLIST` joins it because the nuScenes two-wheeler group contains motorcycles. The counts also give the two-wheeler group split by class, so the D15-strict reading (bicycle class only) can be read off. No other AV2 category enters any group.

### 12.2 Stage-A cache (D16 Choice 13)

One npz per log and tracker × detector, in the layout of `k6_cache_v02` (which `k6_sim_v02`, `k8_sim_v0*` and `k8_items_v02` read), built by `av2_cache_stageA_v01.py` with `k6_cache_v02`'s own functions and order (deployed tracks score >= 0.4; `m_data_v04.load_export_v2`; `m_lib_v04.motion_features` from the full exported history; `x1_lib_v03.build_table` pairing among deployed tracks):
- `tr_*`: every K6 track field, including `tr_pred` = the tracker's own propagation of its mean and xy covariance at 0.5 ... 4 s (`av2_horizon_prep_v01.propagate`, run on AV2 under Choice 13 with `--allow-av2-propagation`), `tr_inst` (GT pairing at k), `tr_contested`, `tr_inpath`;
- added fields (extra `tr_` keys, ignored by the K8 readers): `tr_g` (group, 12.1), `tr_r8` (predicted-range bin per step from the sensor's CTRV, `k8_sim` `strata`), `tr_ax` (object axes), `tr_anorm2s` (the toward-ego normal a* at 2 s for both axes: sign(a.(c_e - m_2s)) a, with c_e the CTRV-predicted ego centre at k + 4, the method-stage convention), `tr_sep2s` (separating-axis flags at 2 s), `tr_vis8` (the paired `track_uuid` annotated with >= 1 interior point at k + h, h = 1 ... 8; existence only);
- `kf_t`, `kf_ego` (logged ego at every 2 Hz frame), `ego_t/x/y/yaw` (logged ego at every 10 Hz sweep between the first and the last 2 Hz frame: the analogue of K6's LIDAR_TOP sample_data poses), `kf_ego_k4` is implicit (`kf_ego[k + 4]`);
- `gt_k`, `gt_inst`, `gt_cls`, `gt_pts`, `gt_inrack` (all False on AV2): existence and visibility only;
- `gt_x`, `gt_y`, `gt_yaw`, `gt_w`, `gt_l`: **present and NaN-filled**. No ground-truth position, velocity or box of any annotation enters a stage-A file (every annotation is at a sweep later than some decision time k, so none is written). GT velocity is not written at all.
- `MANIFEST.json` as K6's plus `stage: "A"` and the hashes of the inputs.

The logged ego trajectory (not an annotation) is kept in full, because the K8 decision construction leashes the plan to it up to 4 s ahead (Choice 13 allows planner decision construction and the logged poses at k and k + 4).

### 12.3 Stage-B script (hash-bound in the frozen plan; NOT run on AV2)

`av2_cache_stageB_v01.py` copies a stage-A cache and fills `gt_x, gt_y, gt_yaw, gt_w, gt_l` from the GT table (`av2_gt_prep_v01` format), row for row (rows are matched by sample token order, instance and keyframe, asserted), and writes `stage: "B"`. It refuses to run on an AV2 stage-A cache unless given `--frozen-plan` and its `--frozen-plan-sha256`. Tested on nuScenes only: (i) the stage-A builder on nuScenes inputs reproduces every non-GT-position field of `30_DATA/k6/cache_v02_t*_val` exactly; (ii) stage B on that stage-A output reproduces every field of the K6 cache exactly.

### 12.4 Counts (K8 decision-mode items)

`k8_items_v04.py` = `k8_items_v02` plus a `--counts-only` mode (and an `--av2` scene set) in which the error fields `dx, dy, D, D_long, D_lat` are written as NaN without any arithmetic on a ground-truth position; the enumeration (decision states, enforced pairs at the reference margin 0, the paired instance annotated at k + h, relied axis, gaps, strata, sd, L0) is unchanged. `av2_counts_v02.py` turns the items into `AV2_TRACKER_COUNTS_v02.json`: per tracker × detector, group, L0 stratum (group × predicted range × axis × motion), PD7 / SD1_7 / PD / NIP and the K6 evaluation cell family, items and logs per cell, and the decision states. Arm-dependent decision-mode records are **not** computed: the fitted arms need an AV2 fit (an outcome before the freeze) and every arm's plan choice embeds the infeasibility indicator, which Choice 13 forbids.

### 12.5 HOTA (Choice 14)

The official av2 tracking evaluator in a new virtual environment (`50_CODE/env/av2eval310`, from PyPI); tracks converted from the exports to the evaluator's input format; HOTA reported next to AMOTA, MOTA, IDS for every run, on the mapped classes car, pedestrian, cyclist (and the other classes descriptively). Any deviation of the evaluator's protocol from the nuScenes one (matching, ranges, ROI without maps) is written down where it applies.

### 12.6 AB3DMOT (Choice 11)

LT3D's AB3DMOT (the repository at the commit used for the detector, `e33189aa…`), run at 2 Hz on the LT3D detections of the same 4,806 frames, as a descriptive third tracker. Its tracking metrics are computed as for T1/T3. Stage-A counts need its own state, covariance and 2 s propagation; if its code exposes them, they are captured read-only by a wrapper (no third-party edit); otherwise its counts are reported as not computable and the reason is written down.
