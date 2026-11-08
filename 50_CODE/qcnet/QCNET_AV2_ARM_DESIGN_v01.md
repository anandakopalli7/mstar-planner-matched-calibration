# QCNet on Argoverse 2 Sensor val: the second deployed-predictor arm (design v01, 2 Nov 2026)

**Status.** Written on 2 Nov 2026 (≈ 00:40 EST) **before** any pod was created for this arm, before any 10 Hz detection, tracking or QCNet output existed, and before any Argoverse 2 (AV2) ground-truth content beyond what the detector stage and the tracker-port design already used. Every choice below is fixed by a rule that refers only to the literature, the code of the public models, the data format, or the AV2 facts already recorded in `60_RESULTS/av2_det/AV2_DETECTOR_NOTE_v01.md` and `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v01.md` §2–§4. **No choice may be revisited after QCNet outputs exist**, except to fix a crash or a format error; any such fix is logged in the note as a deviation, with its reason.

**Governing documents.** `90_DECISIONS/D16_DELEGATED_CHOICES_v01.md` (Choice 3 for the Trajectron++ analogue, Choice 4 for QCNet), `30_PRIOR_ART/P7_L5_DEPLOYED_PREDICTOR_ARM_v01.md` §B.5, §C.2, §C.3, §D, §E; the lead's brief of 2 Nov 2026 (pre-approved RunPod spend ≤ $20 from 2 Nov, stop at a projected $18).

## 0. Outcome-blind boundary (D15 §4; D16 Rule 0)

**Computed on AV2 by this arm, and nothing else:** detector AP (official av2 evaluator); tracker HOTA/AMOTA if computed; counts (frames, sweeps, tracks, items per class × history-length stratum, join coverage, failures); finiteness and positive-definiteness of every QCNet output and derived covariance; equality checks between two runs of the same detector or of two equivalent code paths (output against output, never against GT at a later time).

**Never computed on any QCNet, tracker or AV2 output:** an exceedance, coverage, residual against σ, NEES/ANEES, projected-error quantile, margin, infeasibility, calibration multiplier, or QCNet's own minADE/minFDE/MR/Brier against GT. The output files hold **no GT position at the target time**; the target sweep is identified by its timestamp only, and the GT object's presence there by existence and `num_interior_pts ≥ 1` only (the tracker port's "horizon availability by existence", design §9). QCNet's `validation_step`, its metrics modules and `TargetBuilder` are never run.

## 1. Items and origins

- **Origin grid.** The 2 Hz audit frames of the tracker arm: every 5th lidar sweep of each log from sweep 0 (LT3D `VAL_SAMPLE_RATE`), 4,806 frames in 150 logs (tracker-port design §2).
- **Item key.** `sample_token = "<log_id>_<timestamp_ns>"` of the origin sweep and `instance_token` = the AV2 GT `track_uuid`, exactly the tracker port's keys (design §2, §7). Each output row is one (sample_token, instance_token); each key occurs at most once per source, so every file joins 1:1 with the tracker arm's audit items.
- **Pairing on the intersection.** This arm writes a superset: every eligible GT object (GT source) and every GT object matched by a 10 Hz track (deployed source) at every origin. The confirmatory analysis joins on the key and keeps the intersection of the tracker arm's audit items, the GT-history rows and the deployed rows. Join coverage is reported as counts.
- **Classes.** Dynamic analysis classes only: `REGULAR_VEHICLE` (car), `PEDESTRIAN`, `BICYCLIST` (cyclist; the rider cuboid, as in RB-1 of the port design §4.3). These are also the only agent classes fed to QCNet besides the ego vehicle (§4).
- **Visibility at the origin.** GT objects with `num_interior_pts ≥ 1` at the origin sweep (the port design's GT visibility rule, §5).
- **Visible at the target** (stored as a flag, not a filter): the same uuid is annotated at the target sweep with `num_interior_pts ≥ 1`. Existence only.

## 2. Target and timing

- **Target.** The sweep of the same log nearest to t₀ + 2.0 s, accepted if within 20 ms. Origins without such a sweep (log end, dropped sweeps) produce no rows; they are counted.
- **Jitter** = t_target − (t₀ + 2.0 s) in ms, stored per row and summarised (min, percentiles, max).
- **QCNet step.** QCNet predicts 60 future steps on a nominal 0.1 s grid; the 2.0 s output is future step index **19** (0-based; step j is t₀ + 0.1 (j + 1) s). The nominal step is used whatever the jitter (the predictor has no other output time).
- **History grid.** Step i ∈ {0, …, 49} has nominal time t₀ − 0.1 (49 − i) s, and step 49 is the origin. Each step takes the sweep of the log nearest to its nominal time if within 20 ms, else the step is missing. Partial histories are allowed (QCNet was trained on AV2 Motion Forecasting tracks, which have them).

## 3. History sources

| | **Primary: deployed** | **Upper bound: GT** |
|---|---|---|
| Positions | 10 Hz tracker output boxes (city frame x, y) | AV2 annotation cuboid centres (city frame x, y) |
| Heading | box yaw (city frame) | cuboid yaw (city frame) |
| Velocity | the detector's regressed (vx, vy), rotated to the city frame (LT3D's own `transform_to_global_reference`) | backward difference of the uuid's centres to its previous annotated sweep, if that sweep is ≤ 0.25 s earlier; else 0 (track birth) |
| Field of view | the detector's (LT3D ±54 m) | annotations inside the ego-frame BEV square \|x\|, \|y\| ≤ 54 m of their own sweep (the detector's range, the tracker port's input square, design §5) |
| Item at an origin | a 10 Hz track active at the origin sweep, matched to a visible GT object of the same class (§5) | the visible GT object itself |

Reasons:
- Each source supplies the kinematics its pipeline has. A deployed stack has the detector's velocity, not a finite difference of noisy centres; the GT source has no velocity field, and a backward difference is the causal choice (a central difference would read the sweep 0.1 s after the origin).
- The same field of view in both sources makes the upper bound isolate input quality (noise, misses, ID switches), not the extra context of far-away annotated agents.
- **Ego vehicle (`AV`)**, required by QCNet's data format: `city_SE3_egovehicle` at every history sweep (translation x, y; yaw of the rotation; velocity by the GT backward-difference rule). Identical in both sources.

## 4. QCNet input conversion

- **Code and weights.** `ZikangZhou/QCNet` at commit `55cacb418cbbce3753119c1f157360e66993d0d0` (P7 §B.5); checkpoint `QCNet_AV2` from Drive id `1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv`. No published hash exists, so the SHA-256 (and MD5, size) of the downloaded file are recorded and are the identity of the weights. "Verified" means: the file loads with `torch.load(weights_only=True)` (no pickled code runs), the model is built from the checkpoint's own `hyper_parameters`, and `load_state_dict(strict=True)` succeeds; the hash is computed twice on the pod (after download and after the runs).
- **Scene per origin.** One QCNet scene per (log, origin, source): agents = `AV` + every agent of the three classes with at least one step in the 50-step window (QCNet's own `predict_unseen_agents=False` rule), split `test` (50 historical steps, no future rows).
- **Agent features.** QCNet's own `ArgoverseV2Dataset.get_agent_features` on a DataFrame in the AV2 MF parquet schema (`track_id`, `object_type`, `object_category`, `timestep`, `position_x`, `position_y`, `heading`, `velocity_x`, `velocity_y`, `scenario_id`, `city`, …). Types: `REGULAR_VEHICLE`, `AV` → `vehicle`; `PEDESTRIAN` → `pedestrian`; `BICYCLIST` → `cyclist`. `object_category` = 2 (`SCORED_TRACK`) for all; QCNet's encoder and decoder do not read it (it only sets `predict_mask`, which we do not use).
- **Map features.** The log's `map/log_map_archive_*.json` (fetched with `av2_fetch_v04.py --maps`) in the city frame, through QCNet's own `get_map_features(map_api, centerlines)`. Centerlines are read from the JSON's `centerline` field as QCNet does; **if the Sensor map JSON has no `centerline` field**, they are computed with av2's own `ArgoverseStaticMap.get_lane_segment_centerline` (the av2 API's definition). Which case applied is a property of the file format and is reported. Map features are computed once per log and shared by its origins (they do not depend on the origin).
- **Inference.** `eval()`, `torch.no_grad()`, fp32, no test-time augmentation; PyG `Batch` of B scenes. A bs = 1 vs bs = B comparison on the first log (output against output) checks that batching does not change outputs beyond float tolerance.
- **Agent frame.** QCNet's outputs are in each agent's frame at step 49 (origin p₀ = position at step 49, θ = **the heading QCNet used**, `heading[:, 49]`); `test_step` maps them to the world frame by `world = R(θ) local + p₀`, with R(θ) = [[cos θ, −sin θ], [sin θ, cos θ]]. The same rotation is used below.

## 5. Matching deployed tracks to items (time t₀ only)

Per class, Hungarian assignment on the BEV centre distance between the 10 Hz tracks active at the origin sweep and the visible GT objects of that class at the same sweep, with a **2.0 m gate** (the tracker port's pairing gate, design §7). Unmatched tracks (false positives) and unmatched visible GT objects (misses) are counted. This is a same-time association, as in the port's `build_table`; no distance is reported. (The port's pairing is persistent across frames; this arm pairs at each origin independently, because its items are origin-wise. The difference is stated in the note.)

## 6. Outputs per row (both sources)

- Per mode k = 1…6 at future step 19: location μ_k (world frame), Laplace scales (b_x,k, b_y,k) (agent frame), mixture weight π_k (softmax of QCNet's `pi`).
- **Covariance per mode:** Σ_k = R(θ) diag(2 b_x,k², 2 b_y,k²) R(θ)ᵀ (variance of a Laplace law = 2b²; QCNet's two axes are independent in the agent frame).
- **V1 (most likely mode):** k* = argmax π_k; μ_V1 = μ_k*, Σ_V1 = Σ_k*.
- **V2 (moment-matched over the 6 modes), primary**, as for Trajectron++ (D16 Choice 3): μ_V2 = Σ π_k μ_k, Σ_V2 = Σ π_k (Σ_k + d_k d_kᵀ), d_k = μ_k − μ_V2.
- Also: key, log, origin and target timestamps, jitter, class, number of valid raw history steps `n_hist` (0–50, step 49 always valid), QCNet's vector validity at step 49 (steps 48 and 49 both present), visible-at-target flag, `num_interior_pts` at the origin, θ, p₀; deployed only: the tracker's track id.
- **Checks (allowed):** all values finite; Σ_V1, Σ_V2 and every Σ_k symmetric with both eigenvalues > 0.
- **History-length strata** (counts only): n_hist ∈ {1}, {2–5}, {6–15}, {16–49}, {50}, i.e. ≤ 0.1 s, ≤ 0.5 s, ≤ 1.5 s, < 5 s and the full 4.9 s window.
- Files: pickle-free `.npz` (`numpy.load(..., allow_pickle=False)`; strings as fixed-width unicode), one per source, plus `SHA256SUMS`.

## 7. The 10 Hz detector

- **LT3D CenterPoint, the primary detector**, unchanged: LT3D commit `e33189aa09f282cf555b64dba1654eb0c14464a6` (checked out explicitly), config `centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2`, `epoch_20.pth` (SHA-256 must equal `299cf3b7…e50c`, the detector stage's), the same environment recipe (`pod_lt3d_setup_v03.sh` → `_v04`, which only pins the commit and adds `filterpy` for the tracker).
- **Frames: all lidar sweeps of the 150 val logs** (23,547 sweeps, tracker-port probe P-a), infos by LT3D's own `generate_info(..., 5 sweeps)` with sample rate 1 instead of 5.
- **Reproduction check (allowed, output against output):** on the 4,806 sweeps of the 2 Hz subset the 10 Hz run is compared with `30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_dets_v01.npz`: per-frame row counts, and the largest absolute difference of box values over rows matched in score order. Exact equality is expected on the same GPU type; small differences are possible across GPU types (sparse-convolution and DCN kernels use atomic adds) and are reported as they are. A gross mismatch (a frame shifted, a log missing) stops the arm.
- **AP sanity check at 10 Hz:** official av2 evaluator, as in the detector stage (`DetectionCfg`, 50 m, ROI-filtered), on all sweeps, for the three analysis classes (an AP of one category depends only on that category's detections and labels, so restricting the categories does not change the three values). Compared descriptively with the 2 Hz values.

## 8. The 10 Hz tracker: LT3D's AB3DMOT

**Rule from the brief:** prefer T1 (CANMOT) and T3 (Poly-MOT) at 10 Hz if their motion and noise models are parameterised by dt; otherwise LT3D's AB3DMOT.

**Finding (code at the pinned CANMOT commit `515d0792…`):**
- The transition F uses the configured scalar `LiDAR_interval` (0.5 s), so F alone could be re-parameterised.
- **The process noise is not a function of dt.** T1's Q (`centerpoint/local/val/canmot_q`) is a per-step sample covariance fitted on nuScenes at 0.5 s steps. T3's Q is a fixed per-step constant (`CTRA.getProcessNoiseQ` = I; `CA_INIT_EKFQ`).
- The life cycle is counted in frames (`max_age` 10–20, score `decay_rate` per frame).
- Running T1/T3 at 10 Hz would therefore require re-scaling Q, `max_age` and the decay, i.e. re-tuning. The port forbids that ("No parameter is re-tuned on AV2", design §4.4), and nothing in the literature fixes how to do it.

**Choice: AB3DMOT as released in LT3D** (`tracking/ab3dmot.py`, `tracking/test_tracker.py` at `e33189aa`), the public AV2 tracking baseline:
- Its settings are the released defaults of `test_tracker.py`: score > 0.1, top 500 boxes per frame over all classes, `max_track_age` 3, 3-D IoU threshold 0.1, Hungarian matching, one constant-velocity Kalman filter per track in frame units. These are generic AB3DMOT values, not fitted at either rate; AB3DMOT was introduced on KITTI at 10 Hz.
- Detections are converted with LT3D's own `unpack_predictions` and `transform_to_global_reference`.
- The tracker is reset per log.
- Output: the boxes of active tracks (tracks updated in that sweep), as `test_tracker.py` stores them. LT3D's AB3DMOT returns the matched detection with the track id, so the history is the detector's boxes linked by identity.
- `average_scores_across_track` (an offline, non-causal score smoothing) is not used for the histories.

Execution details (no effect on results):
- The score and top-k filter run over all classes first. Only the three analysis classes are then tracked, because LT3D's AB3DMOT runs one independent `SingleClassMOT` per class.
- **Speed shim:** the 3-D IoU of a detection–track pair whose BEV footprints cannot overlap (centre distance > half the sum of their BEV diagonals + 1 cm) is exactly 0 in LT3D's `iou3d`. The shim fills those entries with 0 without calling `iou3d`, so the IoU matrix, and hence the Hungarian solution, are identical.
- **Equivalence is shown on the first 3 logs:** native and shimmed runs give identical outputs. The full run proceeds only if they are identical.
- The tracker runs on the pod's CPUs, one process per log, with the worker count chosen from the pod's cgroup memory limit.

**Ordering.** The tracker part starts only after `60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v01.md` exists (lead's brief). The helper's code in `50_CODE/av2/` is used read-only, as copies on the pod, and only for join-coverage counts against the 2 Hz audit items. AB3DMOT itself does not depend on it.

## 9. Execution and logging

- **Pod.** Only through `50_CODE/env/runpod/runpod_claude_v03.ps1` (list, create-gpu, get, terminate). The pod is named `claude-programmeA-qcnet*`, with `-VolumeGb 150` (`/workspace`) and `-MaxCostPerHr 1.0`; all work lives on the volume (`/workspace/work`, reached as `/root/work`) behind resumable done-markers. If the pod loses its IP it is terminated, and the work resumes on a new pod.
- **Order:**
  1. [fetch with maps | LT3D env | QCNet env + checkpoint], in parallel;
  2. LT3D 10 Hz infos (parallel), inference, export, AP;
  3. QCNet on GT histories (parallel with step 2 where GPU memory allows);
  4. after the tracker note: AB3DMOT 10 Hz → matching → QCNet on deployed histories;
  5. copy back, verify hashes on the laptop, terminate, confirm with list.
- **Spend.** `80_LOGS/runpod/SPEND_LOG_QCNET_v01.md` records every create, terminate, price and wall time. Before each step, the projected total of all Claude RunPod spend since 2 Nov (all `SPEND_LOG_*.md`) is checked against $18; the work stops and is reported if a step would cross it.
- **Code.** New files only, in `50_CODE/qcnet/` (pod scripts derived from `50_CODE/av2/pod/` carry `_v04`). Downloaded code (LT3D, QCNet) lives in its own directories on the pod. Our scripts live in `/root/work/code_qcnet`, and Python runs with `-I` where the import layout allows.
- **Outputs.** In `30_DATA/qcnet_av2_v01/`; note in `60_RESULTS/qcnet_av2/QCNET_AV2_NOTE_v01.md`.

## 10. Known limitations, stated in advance

- QCNet's AV2 weights were trained on AV2 Motion Forecasting tracks, which come from a tracker and are smoothed (P7 §C.3); our GT is human annotation. The GT source is therefore an *input* upper bound, not the training distribution.
- Only the three analysis classes plus the ego vehicle are fed. Other road users (buses, trucks, motorcyclists) are absent from QCNet's scene in both sources alike.
- Sensor log maps cover the whole log, whereas the MF archives are cropped to each scenario. Only polygons within QCNet's radii (50 m pl2a, 150 m pl2m) reach an agent.
- Laplace → Gaussian by variance matching is nearly exact at one-sided δ = 0.05 and short at δ = 0.01 (P7 §C.3). DP-SCRC is distribution-free on the score.
