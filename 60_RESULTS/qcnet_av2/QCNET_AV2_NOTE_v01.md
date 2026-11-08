# QCNet on Argoverse 2 Sensor val: the second deployed-predictor arm (note v01, 2 Nov 2026)

**What this is.** QCNet's public AV2 checkpoint, run on the 2 Hz audit origins of the 150 AV2 Sensor val logs, with two history sources:
- **deployed (primary):** LT3D CenterPoint on every 10 Hz sweep, then LT3D's AB3DMOT at 10 Hz;
- **upper bound:** ground-truth (GT) annotation histories.

The design was written before anything ran and has not been changed since the first pod was created: `50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md`, SHA-256 `aa6e3ec0f3de95f3eb428845c0e471470e8c3d0d5e49688f0722faf1f7b5ff06`.

| Item | Location |
|---|---|
| Data | `30_DATA/qcnet_av2_v01/` (`SHA256SUMS.txt` and `SHA256SUMS_addendum.txt`, all 77 files verified on the laptop) |
| Code | `50_CODE/qcnet/pod/` |
| Spend | `80_LOGS/runpod/SPEND_LOG_QCNET_v01.md` |

**Outcome statement.** On AV2 this arm computed only:
- detector AP;
- counts;
- timing jitter;
- finiteness and positive-definiteness checks;
- output-against-output equality checks (10 Hz vs 2 Hz detections, batch size, native vs shimmed tracker, frame equivariance).

It did **not** compute any of the following on any QCNet, tracker or AV2 output:
- exceedance, coverage, residual against σ, NEES/ANEES;
- projected-error quantile, margin, infeasibility, calibration multiplier;
- QCNet minADE/minFDE/MR/Brier.

How the boundary was kept:
- No GT position after an origin was read. The files hold no GT position at the target.
- The target sweep is found by timestamp.
- "Visible at target" is existence with `num_interior_pts` ≥ 1.

## 1. Choices (design §1–§8, fixed before any output)

| Choice | Fixed as |
|---|---|
| Origins and items | Every 5th sweep from sweep 0 (the 4,806 2 Hz frames). Key `(sample_token = <log>_<ts>, instance_token = GT track_uuid)`, unique per source. Items are paired with the tracker arm's audit items on the intersection. |
| Target | The sweep nearest t₀ + 2.0 s within 20 ms; QCNet future step 19. History is 50 steps on a nominal 0.1 s grid, each step taking the nearest sweep within 20 ms. |
| History, deployed | AB3DMOT active boxes in the city frame. Heading = box yaw; velocity = LT3D's regressed velocity rotated to the city frame. |
| History, GT | Annotation centres in the city frame, inside the ±54 m ego-frame square of each sweep. Heading = cuboid yaw; velocity = backward difference (≤ 0.25 s), else 0. |
| Ego (`AV`) | `city_SE3_egovehicle`, identical in both sources. |
| 10 Hz tracker | **LT3D AB3DMOT**, not T1/T3. T1/T3 process noise is a per-step constant (T1's Q fitted at 0.5 s) and their life cycle is counted in frames, so running them at 10 Hz would mean re-tuning. AB3DMOT used the released `test_tracker.py` defaults: score > 0.1, top 500, `max_age` 3, IoU 0.1, Hungarian. |
| Matching deployed tracks to items at t₀ | Per-class Hungarian on BEV centre distance, 2 m gate, against GT with ≥ 1 point. |
| Covariance per mode | Σ_k = R(θ) diag(2b_x², 2b_y²) R(θ)ᵀ, with θ = QCNet's heading input at step 49. |
| V1 and V2 | V1 = most likely mode. **V2 = moment-matched over 6 modes (primary).** |
| Classes | `REGULAR_VEHICLE`, `PEDESTRIAN`, `BICYCLIST`; only these plus `AV` are fed to QCNet. |
| Map | The log's `log_map_archive_*.json`. No Sensor map has a `centerline` field (0/150), so av2's `get_lane_segment_centerline` is used (design §4 rule). |

## 2. Versions and hashes

**QCNet**
- Code: `ZikangZhou/QCNet` at `55cacb418cbbce3753119c1f157360e66993d0d0`.
- Checkpoint `QCNet_AV2.ckpt` (Drive id `1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv`): 93,083,579 B; SHA-256 `b9f852ec888d6fb966a38e3e307af231145b8e1e69cf7b0b9dddd1ae33120f21`; MD5 `5db9ee8b1847cf5703d8e9cdaf91c59d`.
- Load check: loaded with `torch.load(weights_only=True)` (no pickled code), so the restricted unpickler was not needed. Built from its own hyper-parameters; `load_state_dict(strict=True)`: all keys matched.
- Model: 7,660,673 parameters, epoch 63, step 399,872; state-dict digest `7a12434d…`.
- Hyper-parameters: argoverse_v2, input/output dim 2, no output head, 50 → 60 steps, 6 modes, radii pl2pl 150 / pl2a 50 / a2a 50 / pl2m 150 / a2m 150.
- Environment: torch 2.1.0+cu118, torch-geometric 2.3.1, torch-cluster 1.6.3, torch-scatter 2.1.2, pytorch-lightning 2.0.4, av2 0.2.1 (`env/qcnet_pip_freeze_v03.txt`).

**LT3D**
- Commit `e33189aa09f282cf555b64dba1654eb0c14464a6` (checked out explicitly).
- `av2_detectors.tar.gz` `607534ae…7827d` and `epoch_20.pth` `299cf3b7…e50c`, both equal to the detector stage's.
- Packages equal to the detector stage's freeze, plus filterpy 1.4.5, nuscenes-devkit 1.1.11 and nntime 0.1.1 (§7).

**Data**
- AV2 val with maps: 24,597 files, 0 failed. Manifest SHA-256 `56533144…72c`, identical to the detector stage's pod manifest.

**Helper code (read-only)**
- The tracker helper's code and 2 Hz exports were copied read-only to the pod for the join (§6). 44 of 45 laptop hashes were checked OK on the pod. The 45th, `av2_ego_prep_v01.py`, appeared on the laptop after the copy and was not used.

## 3. 10 Hz detector (LT3D CenterPoint, all sweeps)

**Run.** 23,547 sweeps, 150 logs, 56,969,946 boxes (2,419 per sweep; the 2 Hz stage had 2,407). GT rows: 1,419,817.

**AP sanity check** (official av2 evaluator, 50 m, ROI-filtered). Columns are AP · ATE · ASE · AOE · CDS.

| Class | 10 Hz (23,547 sweeps) | 2 Hz detector note (4,806 frames) |
|---|---|---|
| Regular vehicle | 0.875 · 0.258 · 0.140 · 0.091 · 0.788 | 0.875 · 0.259 · 0.140 · 0.091 · 0.787 |
| Pedestrian | 0.798 · 0.199 · 0.226 · 0.437 · 0.675 | 0.795 · 0.199 · 0.226 · 0.449 · 0.671 |
| Bicyclist | 0.561 · 0.240 · 0.329 · 0.117 · 0.470 | 0.543 · 0.247 · 0.330 · 0.117 · 0.454 |

**Reproduction of the 2 Hz subset** (output against output; `av2val10_lt3d_repro_2hz_v01.json`, `_v02.json`):
- The run is **not bit-identical** to the detector stage. This pod had an RTX 3090; the detector stage ran on an RTX 4090, and LT3D's spconv/DCN kernels are nondeterministic.
- Rows at the 4,806 frames: 11,615,159 now vs 11,570,785 before (+0.4 %). Only 104 frames have equal row counts; the per-frame |Δrows| median is 17 (p99 164).
- Boxes with score ≥ 0.1, matched one-to-one within 0.5 m:

  | Class | Matched | Median centre difference | p90 centre difference | Median score difference |
  |---|---|---|---|---|
  | Vehicles | 86 % | 3.6 mm | 3 cm | 0.003 |
  | Pedestrians | 93 % | 2.4 mm | 1.9 cm | 0.002 |
  | Bicyclists | 88 % | 2.2 mm | 2.5 cm | 0.002 |

- No frame or log was shifted or missing.
- **Consequence:** at the 2 Hz frames, the deployed QCNet histories and the 2 Hz T1/T3 tracks come from slightly different detection sets.

## 4. 10 Hz tracker (AB3DMOT)

**Equivalence.** On 3 logs, native LT3D association and the exact-zero-IoU shim gave **identical** outputs (9,389 + 4,886 + 37,460 rows).

**Output.** 150 logs, 2,785,808 rows for the three classes. Every input box above 0.1 becomes an active-track row: LT3D's AB3DMOT has no minimum-hit rule.

| Class | Tracks | Track length, sweeps (p10 / median / p90 / max) | Tracks of 1 sweep | Tracks > 50 sweeps |
|---|---|---|---|---|
| Regular vehicle | 198,619 | 1 / 3 / 26 / 157 | 53,464 | 7,157 |
| Pedestrian | 146,500 | 1 / 2 / 14 / 157 | 50,618 | 1,736 |
| Bicyclist | 41,140 | 1 / 1 / 3 / 117 | 28,578 | 15 |

Reading (descriptive). With the released `max_age` of 3 frames (0.3 s at 10 Hz) and no hit threshold, the public baseline fragments tracks heavily and outputs low-score fragments as tracks. Two consequences follow in §5: short deployed histories, and cluttered deployed scenes.

## 5. QCNet runs: counts and checks

**Totals.**

| | GT histories | Deployed (AB3DMOT) |
|---|---|---|
| Origins | 4,806 (600 without a target sweep within 20 ms) | same |
| Origins with ≥ 1 item | 4,196 | 4,196 |
| Items | 107,756 (visible GT inside ±54 m) | 105,517 (497,861 tracks at origins; 105,517 matched to visible GT) |
| Items with steps 48 and 49 both present | 103,497 | 90,501 |
| Items visible at target | 96,046 | 94,514 |
| Agents per scene (median / max) | 43 / 207 | **938 / 3,265** |
| Wall time | 252 s | 2,257 s (71 CUDA-OOM fall-backs to a smaller batch) |

**Items per class.** Each cell is the item count, with the visible-at-target count in brackets.

| Source | Class | n_hist = 1 | 2–5 | 6–15 | 16–49 | 50 | All |
|---|---|---|---|---|---|---|---|
| GT | Regular vehicle | 3,120 (2,794) | 2,305 (2,065) | 10,088 (9,052) | 28,760 (25,717) | 32,269 (29,194) | 76,542 (68,822) |
| GT | Pedestrian | 1,103 (994) | 863 (734) | 3,661 (3,200) | 10,709 (9,290) | 14,384 (12,571) | 30,720 (26,789) |
| GT | Bicyclist | 15 (13) | 20 (19) | 70 (64) | 213 (187) | 176 (152) | 494 (435) |
| Deployed | Regular vehicle | 4,752 (4,194) | 9,854 (8,626) | 20,053 (17,995) | 39,069 (35,632) | 1,764 (1,700) | 75,492 (68,147) |
| Deployed | Pedestrian | 2,181 (1,885) | 6,012 (5,143) | 9,161 (7,988) | 11,788 (10,535) | 447 (427) | 29,589 (25,978) |
| Deployed | Bicyclist | 34 (31) | 100 (90) | 129 (109) | 159 (145) | 14 (14) | 436 (389) |

`n_hist` = valid raw steps of the 50. Full 4.9 s histories make up 43 % of GT items but **2 %** of deployed items.

**Checks** (allowed), on every row of both files:
- finite;
- Σ positive definite for every mode, V1 and V2;
- mixture weights sum to 1;
- V2 covariance symmetric.

**Target jitter.** Median −0.07 ms, p1 −0.75 ms, p99 0.63 ms, range −4.57 to +3.98 ms. No accepted target is near the 20 ms limit.

**Batching.** bs 1 vs bs 4 on log 0 (244 items): max |Δμ| 2.2e-5 m, |Δb| 5.2e-5, |Δπ| 1.3e-4.

**Frame-convention unit test** (`qcnet_frame_test_v01–v03.json`; output against output):
- Exact transforms (v03):
  - Translation by (512, 128) m gives **zero** difference.
  - A +90° rotation reproduces μ' = Rμ to **0.26 mm** and Σ' = RΣRᵀ to 4.4e-4 m².
  - The negative control (wrong rotation sign) misses by 4.4 m.
  - The script's own pass flag is false only because the mixture weights changed by 2.9e-3, above the 1e-3 written in the script. π is not touched by the conversion; heading rounding of about 1e-7 rad moves it.
- Generic transforms (v01, v02; 0.7 rad and a non-binary shift):
  - μ moved by up to 0.16 m (median ≈ 0.03 m) and π by up to 0.62. A pure translation alone moved μ by 0.13 m and π by 0.65; repeating the same scene gave 0.
  - Cause: QCNet rounds its agent inputs to float32 at city coordinates (≈ 6,700 m, 0.5 mm grid). The angle of near-zero motion vectors is one of its input features.
  - This is a property of QCNet on city-frame inputs, the same as on its own MF data, not of the conversion.

## 6. Join coverage

**GT vs deployed.** 104,400 keys are in both sources (by class: vehicle 74,526; pedestrian 29,441; bicyclist 433). 3,356 keys are GT-only and 1,117 deployed-only.

**Against the 2 Hz tracker arm's paired records.** These are the helper's own `build_table` pairing (2 m gate) for the three groups, at k with k + 4 available (existence only).

| Tracker × LT3D | Audit records | In GT source | In deployed source | In both |
|---|---|---|---|---|
| T1 CANMOT, all | 92,166 | 90,252 (97.9 %) | 90,446 (98.1 %) | 89,778 (97.4 %) |
| T1, car in-path | 3,887 | 3,881 | 3,881 | 3,877 (99.7 %) |
| T1, pedestrian | 25,581 | 25,293 | 25,163 | 25,090 |
| T1, cyclist | 372 | 366 | 356 | 354 |
| T3 Poly-MOT, all | 92,124 | 90,226 | 90,438 | 89,771 (97.4 %) |
| T3, car in-path | 3,795 | 3,787 | 3,786 | 3,782 (99.7 %) |

Key lists for the downstream join: `join2hz_t{1,3}_v01_keys.npz`.

## 7. Failures, deviations and stopped jobs

1. **GPU.** RTX 3090 at $0.50/h. An L40S at $1.09/h was refused by the price cap; A40, A6000, A5000 and 4090 were unavailable.
2. **Storage.** The pod volume is a network file system (about 35 ms per file create). AV2 data and the venvs lived on the container disk; all outputs and logs were on the volume.
3. **QCNet environment.** Setup v01's `uv` installed torch 2.14.1 into the venv, which broke torch-cluster. v02 rebuilt it with pip and a `torch==2.1.0` constraint; v03 added torch-scatter, which QCNet's losses import. `pod_master_v04` → `v06` changed only to point at those setup versions.
4. **LT3D environment.** mmdet3d's imports also need nuscenes-devkit 1.1.11 (as in the detector stage) and nntime (LT3D's own `setup.sh`). Both were installed with `--no-deps`.
5. **Stopped on purpose (by PID).**
   - The single-process 10 Hz test (`pod_lt3d_run_v04.sh`): 0.9 sweeps/s, ETA 7.3 h.
   - The 20-worker retry (`_v05`): unchanged speed. The bottleneck is a per-box `.item()` loop in LT3D's `CenterHead`.
   - `_v06` then ran 6 test processes on contiguous shards (2.4 sweeps/s) and merged them in order. Inference is per sweep with batch size 1, so the output is unchanged.
   - Also stopped: a hung local ssh client that had launched the first master (the master kept running).
   - One LT3D test start failed with CUDA OOM while the QCNet GT run held the GPU. It was restarted after that run ended.
6. **AP step.** `export_v01` failed on a log-id slice bug, fixed in `export_v02` / `run_v07`. Split and export had already completed with v01.
7. **First 2 Hz reproduction check.** It compared only frames with equal row counts. `repro_v02` added the matched comparison (§3).
8. **Join.** Pairing was per origin (Hungarian, 2 m), not persistent across frames as in the port (design §5).
9. **Not computed.** Tracker HOTA/AMOTA: av2 0.2.1 has no tracking evaluator.

## 8. Runtime and cost

**Pod.** `j48im9254i0na5` (`claude-programmeA-qcnet`, RTX 3090, 150 GB volume), 00:39:31 → 05:53:33 EST: **5.23 h ≈ $2.62**. **All Claude RunPod spend since 2 Nov is ≈ $2.62.**

**Step times.**

| Step | Time |
|---|---|
| Fetch | 10 min |
| Environments | < 15 min |
| 10 Hz infos | 10 min |
| 10 Hz test | 2.68 h |
| Split / export / AP / repro | ≈ 15 min |
| AB3DMOT | ≈ 41 min after a 4 min equivalence test (55,000 CPU-s) |
| QCNet, GT histories | 4 min |
| QCNet, deployed histories | 38 min |
| Joins and packing | ≈ 10 min |

**Laptop.** No heavy job ran on the laptop; the K8 processes were not touched.

**Pod status.** The pod was terminated and `list` confirmed that no claude-programmeA pod remains.

## 9. Quantities computed on AV2 (complete list)

1. Detector AP / ATE / ASE / AOE / CDS: official av2 evaluator, 10 Hz, three classes.
2. Counts:
   - sweeps, boxes and tracks;
   - track lengths;
   - items per class × history stratum;
   - visible-at-target counts (existence);
   - join coverage;
   - agents per scene;
   - origins without a target.
3. Target-timestamp jitter.
4. Finiteness, positive-definiteness, symmetry and Σπ = 1 checks on QCNet outputs.
5. Output-against-output checks:
   - 10 Hz vs 2 Hz detections;
   - native vs shim AB3DMOT;
   - batch size 1 vs 4;
   - QCNet frame equivariance.

Nothing else was computed. In particular there is no exceedance, coverage, residual, NEES/ANEES, quantile, margin, infeasibility, multiplier, or minADE/minFDE.

## 10. For the lead (decisions, not taken here)

- **Deployed histories are short and the scenes are cluttered.** Only 2 % of deployed items have full histories, and deployed scenes have a median of 938 agents against 43 for GT. This is AB3DMOT-as-released at 10 Hz (`max_age` 3 frames, no hit threshold).
  - A sensitivity with `max_age` 15 (1.5 s, the 2 Hz time constant), or an output score/hit filter, would be a new, pre-registered variant. It was not run.
- **The 10 Hz detections are near-identical but not bit-identical to the 2 Hz stage's** (§3). Decide whether the 2 Hz tracker arm should be re-run on the 10 Hz run's 2 Hz subset for exact input pairing.
- **QCNet's float32 sensitivity** (≈ 3 cm median, up to 0.2 m in μ under arbitrary re-origination) is a floor on how exactly its outputs can be reproduced.
