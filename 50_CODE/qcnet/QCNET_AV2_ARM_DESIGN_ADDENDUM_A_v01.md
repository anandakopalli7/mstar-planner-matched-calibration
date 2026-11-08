# QCNet AV2 arm: design addendum A (v01, 2 Nov 2026), D16 v04 Choices 15 and 17

**Status.** Written on 2 Nov 2026 at about 06:20 EST, before any pod or run for this rerun. It adds to `QCNET_AV2_ARM_DESIGN_v01.md` (SHA-256 `aa6e3ec0…ff06`, unchanged) and replaces it only where stated here. The outcome-blind boundary (design §0) is unchanged.

**What the rerun may use, and what it may not.**
- Allowed: the v01 run's counts, which D16 v04 Choice 15 cites (track fragmentation, history lengths, agents per scene), and its output-against-output numerics (Choice 17).
- Not used: no QCNet output was compared with any ground truth, and nothing below depends on such a comparison.

## A1. Primary deployed histories: "matched AB3DMOT" (Choice 15)

### Input
- The 10 Hz LT3D CenterPoint detections of the v01 run: `30_DATA/qcnet_av2_v01/av2val10_lt3d_centerpoint_dets_s010_v01.npz` (SHA-256 `0dbfe7cf…0840`). It holds all classes with score ≥ 0.1, in the AV2 table format.
- These rows are converted back to LT3D's tracker frame format:
  - translation = (tx, ty, tz − h/2): `format_results` added h/2 to the box's bottom centre;
  - size = (l, w, h);
  - yaw = wrap_pi(2·atan2(qz, qw)): the inverse of LT3D's `yaw_to_quaternion3d`;
  - velocity = (vx, vy) in ego axes;
  - name = category, label = its index in `AV2_CLASS_NAMES`.
- The rows are then moved to the city frame with LT3D's own `transform_to_global_reference`. Sweeps without detections are kept as empty frames; the sweep list comes from the v01 fetch manifest.
- **Path check:**
  - The released-default configuration, re-run from this input on the **first 10 logs** (sorted by log id; a full replay would double the tracker time), must reproduce those logs in `trk10_ab3dmot_lt3d_3cls_v01.npz` (v01's tracker output from LT3D's pickled predictions).
  - Report: row count, track ids, and the largest box difference.
  - Differences limited to float rounding are acceptable. Anything else stops A1, and the lead is told.
- Re-detection is not needed (lidar is not fetched).

### Rules (each fixed here, before any output)

| Rule | Value | Source |
|---|---|---|
| Score floor | **score ≥ 0.1**, over all classes, before tracking | The 2 Hz trackers' input floor: tracker-port design §4.4; `AV2_TRACKER_NOTE_v01.md` §2, "Removed: score < 0.1" |
| Top-k | top 500 boxes per sweep, kept from `test_tracker.py`; reported if it ever binds | LT3D `test_tracker.py` |
| Hit threshold | **min_hits = 3**, with AB3DMOT's own rule: a track is published in a sweep only if `hits ≥ min_hits or frame_count ≤ min_hits` | `eddyhkchiu/mahalanobis_3d_multi_object_tracking` @ `293388853c70`, `main.py`: line 491 (`min_hits=3` default), line 587 (output rule), line 264 (`hits = 1` at creation). LT3D's `tracking/ab3dmot.py` states it is adapted from this repository |
| Life (max_age) | **T1's track life in seconds, at 10 Hz** (derivation below) | CANMOT @ `515d0792` |

Details of the hit rule:
- frame_count = the 1-based sweep index within the log.
- As in LT3D's version, only tracks updated in that sweep (`active`) are published, with the matched detection's box.
- A track's rows before its third hit are not published, so they are not in any history: the predictor sees only published states.

Derivation of max_age:
- T1 is experiment `paper/local/canmot/sc`.
  - `config/experiment/paper/local/canmot/sc.yaml`, line 6: `override /poly_mot: nusc_config_rotate_cov_cv`.
  - `config/poly_mot/nusc_config_rotate_cov_cv.yaml`, line 45: `max_age: {1: 10, 0: 10, 2: 15, 3: 20, 4: 10, 5: 10, 6: 20}` (frames).
  - Same file, line 10: `LiDAR_interval: 0.5`.
- The T1 × LT3D export record `30_DATA/av2_trk_v01/export/t1_lt3d/worker0/x1_export_record.json` confirms both values (`resolved_config.life_cycle.max_age`, `resolved_config.basic.LiDAR_interval`).
- The rule is the same in both trackers:
  - CANMOT kills an active track when `time_since_update >= max_age` (`src/canmot/tracking/nusc_life_manage.py`, line 46).
  - LT3D's `SingleClassMOT` keeps tracks with `time_since_update < max_age`.
- Conversion, using the port's class labels (0 bicycle = cyclist, 2 car, 4 pedestrian):

  | Class | T1 frames × 0.5 s | Life | max_age at 10 Hz |
  |---|---|---|---|
  | car (REGULAR_VEHICLE) | 15 | 7.5 s | **75 sweeps** |
  | pedestrian | 10 | 5.0 s | **50 sweeps** |
  | cyclist (BICYCLIST) | 10 | 5.0 s | **50 sweeps** |

  Each class has its own `SingleClassMOT`, so each gets its own max_age.

### Unchanged from the released run
- 3-D IoU threshold 0.1;
- Hungarian matching;
- constant-velocity Kalman filter in frame units;
- one tracker per class;
- reset and id counter reset per log.

### Speed shim v02
- The v01 rule, vectorised: pairs whose BEV footprints cannot overlap get IoU exactly 0 without calling `iou3d`.
- Equivalence, native against shim, on the first 3 logs under the **matched** rules must be identical. Otherwise the native code is used.

### Items, matching and history construction
Unchanged: design §1, §2, §3 and §5. Only the track source changes.

### Descriptive run
The v01 released-default run (`max_age` 3, no hit rule, score > 0.1) stays as the descriptive deployed run. Its QCNet output stays in city coordinates (`30_DATA/qcnet_av2_v01/`).

## A2. Re-centring on the ego position at t₀ (Choice 17)

**Origin.** For each scene (log, origin t₀), o = (x, y) of `city_SE3_egovehicle` at t₀, in float64.

**Agents.** Positions minus o, in float64, **before** QCNet's `get_agent_features` casts them to float32. Headings and velocities are unchanged (a translation does not change them).

**Map.**
- Every (x, y) point of the log map JSON (lane boundaries, crosswalk edges, drivable areas) minus o, in float64.
- The result is parsed with av2's `ArgoverseStaticMap.from_json`, from a temporary file.
- Centerlines come from av2's `get_lane_segment_centerline` on the shifted map (unchanged rule; the Sensor maps carry no centerline).
- QCNet's `get_map_features` is computed per scene.

**Outputs back in the city frame.** μ_city = R(θ)·loc + p₀ + o in float64, where p₀ and θ are the re-centred position and the heading that QCNet saw at step 49. Σ is unchanged by the translation. V1 and V2 are as in design §6, and o is stored per row.

**Runs.**
- Primary: GT histories and matched-AB3DMOT histories, both re-centred.
- Sensitivity, kept: the v01 city-coordinate runs (GT and released default).
- Output-against-output comparison: city-coordinate GT run against re-centred GT run. It reports the distribution of |Δμ_V2|, |Δπ| and |ΔΣ_V2| per item, to show how large the float32 effect was. No ground truth is involved.

**Frame tests under re-centring** (frame test v04: output against output, with a negative control). The whole pipeline (tables, map JSON, re-centring) is applied to a transformed city scene:
- (a) translation by (123.4, −56.7) m;
- (b) rotation by 0.7 rad about the city origin;
- (c) rotation by exactly +90°.

Expected: (a) about 0; (b) and (c) within float32 rounding at local magnitudes. The wrong-sign conversion must miss (b) by more than 0.5 m. The maximum |Δμ|, |ΔΣ| and |Δπ| are reported, whatever they are.

## A3. Counts (allowed)

All v01 counts, for the new runs, plus:
- track-length distributions, matched against released default, per class;
- history-length (`n_hist`) distributions of items for matched, released and GT;
- agents per scene;
- items per class × history stratum;
- coverage of the 2 Hz audit keys (v01's `join2hz_t{1,3}_v01_keys.npz`) by each source;
- the A1 path-check agreement;
- finiteness and positive-definiteness.

## A4. Execution
- **Pod and storage.** Pod `claude-programmeA-qcnet2`, through `runpod_claude_v03.ps1` only, with `-VolumeGb 150` and `-MaxCostPerHr 1.0`. Data and venvs live on the container disk; outputs and logs on the volume.
- **Data on the pod.** AV2 val annotations, poses and maps only: no lidar, no calibration (`pod_av2_fetch_nolidar_v05.py`, derived from the helper's `av2_fetch_v04.py`). The 10 Hz detections npz, the v01 manifest, v01's tracker output and the join keys are uploaded from the laptop.
- **Environments.** LT3D environment by `pod_lt3d_setup_v04.sh`, `pod_lt3d_nuscenes_v01.sh` and `pod_lt3d_nntime_v01.sh`; QCNet environment by `pod_qcnet_setup_v03.sh`. The checkpoint SHA-256 must equal `b9f852ec…0f21`.
- **Spend.** Stop and report before the projected total of all Claude spend since 2 Nov reaches $10. Spend log: `80_LOGS/runpod/SPEND_LOG_QCNET_v02.md`.
- **Outputs.**
  - `30_DATA/qcnet_av2_v02/`, with SHA256SUMS verified on the laptop;
  - `60_RESULTS/qcnet_av2/QCNET_AV2_NOTE_v02.md`;
  - v01 is kept unchanged.
