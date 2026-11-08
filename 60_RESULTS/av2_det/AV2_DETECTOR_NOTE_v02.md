# Argoverse 2 validation: detector stage of the external confirmation (v02, 5 Nov 2026)

**What changed from v01.** v01 (`AV2_DETECTOR_NOTE_v01.md`, unchanged) reports the public LT3D CenterPoint and VoxelNeXt checkpoints on the 150 val logs. v02 adds our own CenterPoint, trained only on 475 of the 700 train logs (`AV2_OWN_DETECTOR_NOTE_v01.md`), and sets its val AP next to the public checkpoint's. Everything else in v01 stands.

**Outcome-blind boundary** (D15 §4). The only quantities here are detector AP, the evaluator's error terms and counts. **No exceedance, margin, infeasibility or ANEES number has been computed on Argoverse 2.**

## Like-for-like conditions

Both detectors are compared under the same conditions:

| Condition | Both detectors |
|---|---|
| Model and config | LT3D CenterPoint at commit e33189aa, the same config `…_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2` |
| Test-time augmentation | Flips |
| Frames | The same 4,806 val frames: 150 logs, every 5th sweep |
| Ground truth | The same file, SHA-256 a9d85a54… for both |
| Evaluator | Official av2 0.2.1 evaluator, `DetectionCfg(max_range_m = 50, eval_only_roi_instances = True)`, all 26 competition categories |

The two differ only in how they were trained:

| | Public checkpoint | Our own |
|---|---|---|
| Training logs | all 700 train logs | 475 train logs (225 held out for the confirmation) |
| Schedule | 20 epochs, batch 8 on 8 GPUs | 2 CBGS epochs = 57,838 iterations, batch 4 on 1 GPU, lr scaled to 5e-5 |
| Training frames | probably every 10th sweep | every 5th sweep |
| Checkpoint | `epoch_20.pth`, 299cf3b7… | `iter_57838.pth`, 68369a71… |

## Val AP at 50 m, public vs own

Entries are AP · ATE (m) · ASE · AOE (rad) · CDS.

| Class | Public LT3D CenterPoint (v01) | Own CenterPoint | Own − public (AP) |
|---|---|---|---|
| Regular vehicle | 0.875 · 0.259 · 0.140 · 0.091 · 0.787 | 0.857 · 0.266 · 0.145 · 0.105 · 0.768 | −0.018 |
| Pedestrian | 0.795 · 0.199 · 0.226 · 0.449 · 0.671 | 0.777 · 0.205 · 0.226 · 0.501 · 0.650 | −0.018 |
| Bicyclist | 0.543 · 0.247 · 0.330 · 0.117 · 0.454 | 0.403 · 0.255 · 0.352 · 0.120 · 0.334 | −0.140 |
| Average (26 classes) | 0.469 · 0.391 · 0.317 · 0.499 · 0.383 | 0.425 · 0.392 · 0.327 · 0.538 · 0.343 | −0.044 |

**Own detector on the 225 held-out train logs** (7,232 frames, not seen in its training), AP at 50 m:

| Class | AP |
|---|---|
| Regular vehicle | 0.854 |
| Pedestrian | 0.800 |
| Bicyclist | 0.495 |
| Average | 0.415 |

The public checkpoint is not scored on these logs, because it was trained on them.

**Sources.**
- Public: `30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_ap_v01.csv`.
- Own: `30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_ap_v01.csv` and `…/held225/av2held225_owncp_centerpoint_ap_v01.csv`.
- All 26 classes are in the csv files.

## Readings (descriptive only)

**Cars and pedestrians.** Our detector is within 0.02 AP of the public checkpoint for regular vehicles and pedestrians, the two largest tracker classes. Its translation and scale errors are within 0.01 of the public checkpoint's.

**Bicyclists.** It is weaker on bicyclists by 0.14 AP on val. This is the rarer class, and it gains most from the public run's longer schedule and larger training set.

**Average.** The 26-class average is 0.044 lower.

**Held-out logs.** On the 225 held-out logs the own detector's vehicle and pedestrian AP (0.854, 0.800) are within 0.03 of its val AP (0.857, 0.777). Its bicyclist AP is higher there (0.495).

**Choice.** The choice of detector for the confirmation arm is the lead's. This note only states the numbers.
