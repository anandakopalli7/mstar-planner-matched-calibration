# Own CenterPoint on AV2: design (v01, 2 Nov 2026, about 11:40 EST), D18 v02 option A

**Status.** Written before any pod for this job exists, before any AV2 training-log content (lidar, annotations, poses) has been read, and before any training. The split was written and hashed first:
- `50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json`, SHA-256 `3771664f8aca73d4829e9867147af2c84e8d87fd95d5472e3b1c1bc443700f72`;
- script `owndet_split_v01.py`, `0ed1a401…`;
- city composition `AV2_TRAIN_SPLIT_v01_CITIES.json`, `04e878b4…`, taken from map file names in a bucket listing.

**Approval.** The researcher's approval and the $40 RunPod limit are as quoted by the lead (chat, 2 Nov 2026).

**Outcome-blind boundary** (D15 §4, D16 Choice 13). On AV2 this job computes only:
- detector AP (and the AV2 evaluator's ATE/ASE/AOE/CDS);
- counts;
- integrity checks: hashes, frame and log coverage, finiteness.

No tracker is run, and nothing is compared with ground truth at a later time.

## 1. Split (D18 v02, 1)

- **Rule.** The 700 AV2 sensor train log ids, sorted, then permuted by `numpy.random.default_rng(20261102).permutation` (NumPy 1.26.4). The first **225 are held out** for the confirmation; the other **475 train** the detector.
- **Ids.** The sorted id list has SHA-256 `sorted_log_ids_sha256` (in the file). It came from the public bucket's listing.
- **City composition** (logs):

  | Part | ATX | DTW | MIA | PAO | PIT | WDC |
  |---|---|---|---|---|---|---|
  | Held-out 225 | 5 | 23 | 90 | 3 | 76 | 28 |
  | Train 475 | 20 | 52 | 164 | 9 | 171 | 59 |

- **Confirmation set:** 225 held-out + 150 val = 375 logs, all unseen by the new detector.

## 2. Detector and configuration (D18 v02, 2)

**Code.** LT3D at commit `e33189aa09f282cf555b64dba1654eb0c14464a6`. Environment: `50_CODE/qcnet/pod/pod_lt3d_setup_v05.sh` + `pod_lt3d_nuscenes_v01.sh` + `pod_lt3d_nntime_v01.sh`, the detector stage's package set.

**Configuration.**
- The public checkpoint's own config file: `centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py` from LT3D's `av2_detectors.tar.gz` (SHA-256 `607534ae…`), as shipped next to `epoch_20.pth`.
- Unchanged: model, voxel size 0.075 m, range ±54 m, 5 sweeps, class hierarchy and "wide" head, CBGS resampling, GT-database object sampling, augmentations, AdamW (weight decay 0.01, gradient clip 35), cyclic learning-rate and momentum schedules, and test-time augmentation (flips) for inference.
- Overrides, applied with mmcv's `Config` and written to a dumped config file whose hash is recorded:
  - the data paths;
  - the train info file (our 475 logs);
  - the GT-database info file (built from our 475 logs only);
  - `samples_per_gpu`, `workers_per_gpu`, `lr`, `max_epochs`;
  - `work_dir`;
  - `evaluation.interval` > `max_epochs`, so no evaluation runs during training.

**From scratch.** No `load_from`; random initialisation by the config's own init.

**Training frames: every 5th sweep of each training log**, as the lead specified and D18 states ("LT3D's sample rule").
- Disclosed discrepancy: LT3D's released converter uses `TRAIN_SAMPLE_RATE = 10` for training and `VAL_SAMPLE_RATE = 5` for evaluation (`tools/data_converter/av2_converter.py`, lines 35–36). The public checkpoint was therefore probably trained at every 10th sweep.
- Every 5th is kept: the epoch count is set by compute (§4), so the number of iterations is the same either way, and every 5th gives twice as many distinct frames.

**Infos.** LT3D's own `generate_info(..., 5 sweeps)` per log, as in `pod_lt3d10_prep_v01.py`, with the log lists from the split file and sample rate 5. The same rule is used for the 225 held-out logs and the 150 val logs (the 2 Hz protocol).

**GT database.** LT3D/mmdet3d `create_groundtruth_database('AV2Dataset', …)` on the 475-log train infos only.

## 3. Single-GPU adaptations

**Reference batch.**
- The config file sets `samples_per_gpu = 1`. Its name says 8 GPUs ("4x8": mmdet3d's `<samples>x<gpus>`).
- The file is what ran, so the reference total batch is **B_ref = samples_per_gpu(config) × 8**: 8 if the shipped file says 1.
- If the shipped file sets another `samples_per_gpu`, that value is used and recorded.

**Our batch.**
- B = the largest of {4, 2, 1} that runs the pilot without CUDA OOM, with ≥ 15 % GPU memory headroom.
- **Learning rate scaled linearly:** lr = 1e-4 × B / B_ref. The cyclic schedule keeps its target ratios (10, 1e-4), its up-step ratio of 0.4 and one cycle over the full run.

**Data loading.**
- `workers_per_gpu` = min(CPU quota − 2, 12).
- `mp_start_method = fork`, as in the config.
- Data and environment on the container disk; work directory, checkpoints and logs on the pod volume.

**Run settings.**
- Precision: fp32, as in the config.
- Seed: 0. `deterministic = False`, as in the config: the sparse kernels are not deterministic anyway.

## 4. Pilot, then epochs (fixed rule, recorded before the full run)

**Pilot.**
- `tools/train.py` with the final config, but `max_epochs` large, run for **300 iterations** (or 20 min, whichever comes first) at B = 4 (then 2, then 1 on OOM).
- Measured from the log, iterations 101–300:
  - mean iteration time (s/it) and data time;
  - peak GPU memory;
  - `iters_per_epoch` = len(CBGS train dataset) / B.
- The pilot weights are discarded. The full run starts from scratch, so its cyclic schedule is clean.

**Epoch rule.**
- **E = min(20, floor(H_train × 3600 / (s/it × iters_per_epoch)))**.
- **H_train = 18 h of training wall time.** That is about $16 at the 4090's $0.89/h, chosen so that the whole job (about 5 h of download, preparation, pilot, inference and copy-back plus training) stays near the $25 job budget.
- The value of E, the pilot numbers and the projected job and overall cost are written to `OWN_DETECTOR_PILOT_v01.md` **before** the full run starts.

**Stop rules.**
- If the projected total of all Claude spend since 2 Nov passes **$36**, or if E < 2, the job stops after the pilot and is reported to the lead with the pilot numbers.
- During training: if the measured pace projects past $36, the job stops and is reported.

**Checkpoints.** Every epoch on the volume. A container restart resumes from the last one (`--resume-from`).

## 5. Inference and AP (D18 v02, 3)

**Inference.**
- The final epoch's checkpoint, with the config's test pipeline (TTA flips).
- On the 225 held-out logs and the 150 val logs, every 5th sweep.
- Sharded `tools/test.py` processes on one GPU, merged in order (`pod_lt3d10_shard_v01.py`), as in the QCNet arm.

**Export.**
- LT3D's own `AV2Dataset.format_results` per log (`pod_lt3d10_export_v02.py` logic), giving the AV2 table.
- Same format as `30_DATA/av2_det_v01/lt3d_centerpoint/`: npz (pickle-free) + feather + json summary, per part (held-out, val), plus SHA256SUMS.

**AP.**
- Official av2 evaluator, `DetectionCfg(max_range_m = 50, eval_only_roi_instances = True)`, all competition categories.
- Computed on (a) the 225 held-out logs and (b) the 150 val logs, with the logs' own maps.
- (b) is set next to the public checkpoint's AP at 50 m from `AV2_DETECTOR_NOTE_v01.md`.

**Integrity checks.**
- Frames per log equal to the infos.
- 375 logs present.
- All values finite.
- Checkpoint SHA-256 recorded.

## 6. Pod, spend and outputs

**Pod.**
- Name `claude-programmeA-owndet`, via `runpod_claude_v03.ps1` only. GPU: RTX 4090 first (A6000 or A40 if no 4090), `-MaxCostPerHr 1.0`.
- Container disk large enough for about 135 GB of lidar (700 train + 150 val logs) plus environments; a pod volume for outputs.
- Every long job is launched with `setsid nohup` and stopped only by PID. Uploads run in the background.
- **Fetch:** AV2 sensor train (all 700 logs) and val: lidar, poses, calibration, annotations and maps. Unsigned public bucket, using the v04 fetcher's logic with the split prefix as a parameter.

**Spend.**
- `80_LOGS/runpod/SPEND_LOG_OWNDET_v01.md`.
- Job budget about $25. Stop before a projected $36 total since 2 Nov (all `SPEND_LOG_*.md`; $8.82 before this job).

**Outputs.**
- `30_DATA/av2_det_owncp_v01/`, with SHA256SUMS verified on the laptop;
- `60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md`;
- the public-vs-own AP comparison added in a new version of the detector note (`AV2_DETECTOR_NOTE_v02.md`; v01 kept).
