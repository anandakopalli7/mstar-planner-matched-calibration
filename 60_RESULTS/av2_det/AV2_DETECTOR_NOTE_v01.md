# Argoverse 2 validation: detector stage of the external confirmation (v01, 1 Nov 2026)

**What this is.** The detector outputs for the independent confirmation planned in `90_DECISIONS/D15_EXTERNAL_DATA_PROPOSAL_v01.md`. Under D15 §4 (outcome-blind rule) the only quantities computed on Argoverse 2 before the confirmatory plan is frozen are detector AP, tracker HOTA/AMOTA and counts. **No exceedance, margin, infeasibility or ANEES number has been computed on Argoverse 2.**

## Data

- Argoverse 2 Sensor, validation split, 150 logs, downloaded from the public bucket without an account (fetcher `50_CODE/av2/av2_fetch_v04.py`; pod manifest SHA-256 56533144…, laptop copy without maps 47735085…).
- Frames used: **every 5th lidar sweep per log** (LT3D's `VAL_SAMPLE_RATE` rule), **4,806 frames**, the 2 Hz protocol of the nuScenes studies. Both detectors were run on exactly these frames. VoxelNeXt's OpenPCDet validation list (23,547 sweeps at 10 Hz) was restricted to the same rule (`argo2_infos_val.pkl` replaced by the subset; the full list kept as `argo2_infos_val_10hz.pkl`), so its AP is over the 2 Hz subset, not the model zoo's 10 Hz protocol.

## Detectors

| | LT3D CenterPoint (primary) | OpenPCDet VoxelNeXt (second detector) |
|---|---|---|
| Why | Same family as the nuScenes CenterPoint; 5 sweeps; **regresses velocity** (code size 9), which the CANMOT/Poly-MOT measurement model uses | Independent codebase and architecture; single sweep; **no velocity** |
| Checkpoint | LT3D "Pre-trained Detection Models" `av2_detectors.tar.gz` → `centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2/epoch_20.pth`, SHA-256 299cf3b7… | OpenPCDet model zoo "model-32M" (Drive id 1YP2UOz…), SHA-256 8641d838…; a bare state dict, wrapped unchanged as `{'model_state': sd}` for `test.py` (wrapped copy e513ef56…) |
| Code | LT3D commit e33189aa…; torch 1.10.1+cu111, mmcv-full 1.6.1, mmdet 2.25.2; av2 0.2.1 (no PyAV); nuscenes-devkit 1.1.11 (import only) | OpenPCDet commit 233f8498…; torch 2.1.0+cu118, spconv 2.3.8; av2 0.2.0 (no PyAV); kornia 0.6.12 (0.7 breaks OpenPCDet's argo2 TorchScript) |
| Range | ±54 m | ±200 m |
| Test-time augmentation | flips (config `…_tta_…`) | none |
| Detections | 4,806 frames, 150 logs (`30_DATA/av2_det_v01/lt3d_centerpoint/`) | 1,143,076 boxes, 4,806 frames, 150 logs (`30_DATA/av2_det_v01/voxelnext/`) |

## Detector AP (official av2 evaluator, ground truth restricted to the evaluated frames, ROI-filtered, all competition categories)

Columns: AP; average translation error (m); average scale error; average orientation error (rad); composite detection score.

**At 50 m (like for like):**

| Class | LT3D CenterPoint | VoxelNeXt |
|---|---|---|
| Regular vehicle | **0.875** · 0.259 · 0.140 · 0.091 · 0.787 | 0.891 · 0.316 · 0.158 · 0.341 · 0.765 |
| Pedestrian | **0.795** · 0.199 · 0.226 · 0.449 · 0.671 | 0.782 · 0.228 · 0.226 · 1.385 · 0.579 |
| Bicyclist | **0.543** · 0.247 · 0.330 · 0.117 · 0.454 | 0.638 · 0.216 · 0.242 · 1.118 · 0.488 |
| Average (26 classes) | 0.469 · 0.391 · 0.317 · 0.499 · 0.383 | 0.431 · 0.486 · 0.319 · 0.983 · 0.336 |

**VoxelNeXt at 200 m (OpenPCDet's evaluation range):** regular vehicle 0.721, pedestrian 0.633, bicyclist 0.351, average 0.306 (model zoo: 30.5 mAP at 10 Hz).

Readings, descriptive only: both detectors are strong on cars within 50 m, the range our strata cover; VoxelNeXt's orientation error is 3–10× LT3D's for pedestrians and bicyclists (it regresses no velocity and no heading history), which matters for the constant-turn-rate tracker; LT3D's lower bicyclist AP reflects its ±54 m training range and class hierarchy.

## Deviations and their reasons

1. 2 Hz frame subset for VoxelNeXt (stated above): matches LT3D and our tracker protocol; saves GPU time.
2. VoxelNeXt checkpoint wrapped (format only; weights unchanged; both hashes recorded).
3. Package versions differ from the repositories' pins where the pinned stack would not install or import on the pod image (av2 without PyAV; kornia 0.6.12; OpenCV 4.10 headless for NumPy < 2; LT3D's private nuScenes fork replaced by the public devkit, used only for an import).
4. VoxelNeXt AP computed by our export script (`50_CODE/av2/pod/pod_export_v03.py`) with OpenPCDet's own `format_results` and the official evaluator, because `test.py`'s evaluation failed on a relative-path join in av2 0.2.0's map loader.
5. Compute: two RunPod GPU pods, ≈ $2.56 in total (spend log `80_LOGS/runpod/SPEND_LOG_AV2_DET_v01.md`); the first pod's host failed and its work was lost.

## Next (D15 §3 steps 3–5)

Port the CANMOT/Poly-MOT loaders to Argoverse 2 (detections in the city frame via `city_SE3_egovehicle`, 2 Hz, class mapping car := REGULAR_VEHICLE, pedestrian := PEDESTRIAN, cyclist := BICYCLIST), run both trackers on LT3D CenterPoint (primary) and VoxelNeXt (second detector), report tracker HOTA/AMOTA and the item/stratum **counts** only, then write and freeze the confirmatory plan before any outcome is computed.
