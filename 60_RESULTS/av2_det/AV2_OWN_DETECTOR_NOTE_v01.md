# Argoverse 2: our own CenterPoint, trained without the confirmation logs (v01, 5 Nov 2026)

**What this is.** The public LT3D CenterPoint checkpoint was trained on all 700 AV2 train logs. That includes 225 logs we want for the confirmation. So we trained the same model, from scratch, on the other 475 train logs only (D18 v02 option A). The confirmation set is now 375 logs that this detector never saw: 225 held-out train logs plus the 150 val logs.

**Outcome-blind boundary** (D15 §4, D16 Choice 13). This job computed only:
- detector AP, with the AV2 evaluator's ATE/ASE/AOE/CDS;
- counts;
- integrity checks.

No tracker was run. **No exceedance, coverage, residual, NEES, quantile, margin, multiplier or minADE/minFDE number has been computed on Argoverse 2.**

## Design records (written before the run they govern)

| File (`50_CODE/owndet/`) | SHA-256 | Role |
|---|---|---|
| `AV2_TRAIN_SPLIT_v01.json` | 3771664f… | 700 sorted train ids, permuted with `default_rng(20261102)`: first 225 held out, 475 train |
| `OWN_DETECTOR_DESIGN_v01.md` | cf09bb11… | detector, config, overrides, inference, AP |
| `OWN_DETECTOR_PILOT_v01.md`, `…_PILOT_v02.md` | 55ad2ed1…, 9083c9ec… | pilot (E < 2 stop), then profiling: the step is bound by CenterHead `get_targets`, a single-thread CPU loop |
| `OWN_DETECTOR_DESIGN_ADDENDUM_A_v01.md` | 41ba8fe3… | B = 4, 2 CBGS epochs = 57,838 iterations, checkpoints every 1,000 |
| `OWN_DETECTOR_DESIGN_ADDENDUM_B_v01.md` | b824f3ea… (after §B6 was filled at the speed check) | fast-host search, resume rule, $34 cap rule, saving |

## Training as run

**Model and config.** LT3D commit e33189aa, with the public checkpoint's own config, `centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2`, unchanged except:
- the data paths;
- the train and GT-database infos (475 logs only: 15,245 frames at every 5th sweep; 971,237 GT-database objects);
- batch B = 4, with lr scaled linearly to 5e-5 (1e-4 × 4/8);
- an iteration-based runner with `max_iters` 57,838 and a checkpoint every 1,000;
- no evaluation during training.

The dumped config is `env/cfg_train_i57838_b4.py`, SHA-256 277f0969…. It differs from the stopped segment's copy (4e5fc6c8…) only in `work_dir`.

**Run.**
- From scratch, seed 0, fp32.
- CBGS gives 115,674 samples per epoch, so 2 epochs = 57,838 iterations.
- One cyclic learning-rate cycle over the whole run (peak 5e-4 at 40 %).

**Two segments.**
- Iterations 1–1,000 ran on pod 78zv5c7fe7xrnx (EPYC 7443). That host's pace (1.41 s/it) projected past the $34 line, so the run was stopped on purpose at the 1,000 checkpoint.
- Iterations 1,001–57,838 ran on pod 8peoqsmqm9exjw (Ryzen 9 7950X, RTX 4090), resumed from `iter_1000.pth`. The resume restored the optimiser and schedule (log: "resumed from epoch: 1, iter 999"; lr 5.207e-5, as at the stop).
- Speed check: 1.057 s/it over iterations 1,001–1,200, projecting $31.44 ≤ $34, so all 2 epochs ran (addendum B §B6).
- Iterations 1,001–57,838 took 16.70 h (1.058 s/it).

**Loss.** Total loss 2.02 at iteration 1,000 and 0.80 at iteration 57,800. There were no error lines in the run log.

**Compared with the public run.**
- Public: 20 epochs on 700 logs, batch 8 on 8 GPUs, probably every 10th sweep (LT3D's `TRAIN_SAMPLE_RATE`).
- Ours: 2 epochs on 475 logs, batch 4 on one GPU, every 5th sweep (design §2).
- Ours is a much shorter schedule on about two thirds of the data.

## Inference and AP

**Inference.** `iter_57838.pth` (SHA-256 68369a71…, the same on the pod, in the deliverable and in `train_progress/`). It used the config's test pipeline with TTA flips, every 5th sweep, on 6 `tools/test.py` shards merged in order.

**Export and AP.**
- Export uses LT3D's `format_results` per log.
- AP uses the official av2 0.2.1 evaluator with `DetectionCfg(max_range_m = 50, eval_only_roi_instances = True)`, all 26 competition categories, ground truth restricted to the evaluated frames.

**AP at 50 m** (AP · ATE m · ASE · AOE rad · CDS):

| Class | Val, 150 logs (4,806 frames) | Held-out train, 225 logs (7,232 frames) |
|---|---|---|
| Regular vehicle | **0.857** · 0.266 · 0.145 · 0.105 · 0.768 | **0.854** · 0.265 · 0.143 · 0.097 · 0.767 |
| Pedestrian | **0.777** · 0.205 · 0.226 · 0.501 · 0.650 | **0.800** · 0.201 · 0.239 · 0.466 · 0.670 |
| Bicyclist | **0.403** · 0.255 · 0.352 · 0.120 · 0.334 | **0.495** · 0.253 · 0.354 · 0.183 · 0.406 |
| Average (26 classes) | 0.425 · 0.392 · 0.327 · 0.538 · 0.343 | 0.415 · 0.354 · 0.311 · 0.465 · 0.336 |

All 26 classes are in `val150/…_ap_v01.csv` and `held225/…_ap_v01.csv`. The comparison with the public checkpoint is in `AV2_DETECTOR_NOTE_v02.md`.

**Integrity.**

| | Val | Held-out |
|---|---|---|
| Logs | 150 | 225 |
| Frames | 4,806 | 7,232 |
| Frames with predictions | 4,806 | 7,232 |
| Non-finite values | 0 | 0 |
| Detection rows | 12,376,531 | 18,814,614 |
| GT rows | 288,960 | 448,436 |

The val ground-truth file is byte-identical to the public checkpoint's (SHA-256 a9d85a54… for both), so the two val APs use the same frames and labels.

## Files (`30_DATA/av2_det_owncp_v01/`)

- `val150/`, `held225/`: detections (npz without pickle, feather, json summary), ground truth (feather) and the AP csv.
- `env/`:
  - the checkpoint;
  - the config and its summary;
  - fetch manifests;
  - infos summaries;
  - code hashes;
  - the pip freeze.
- `logs/`: the training log json, inference and export logs.
- `SHA256SUMS.txt`: SHA-256 e8dad0a8…. All 33 files OK on the laptop (`sha256_check_laptop_v01.txt`).
- `logs_extra_v01/`: the full mmdet text log of the resumed segment, the pipeline log and the shard logs; 23 files, SHA-256 OK.
- `train_progress/`: the real-time copies, including the stopped segment's logs, `iter_51000.pth` and `iter_57838.pth`.
- `pilot/`: the pilot records.

**Pod code** (`50_CODE/owndet/pod/`):

| File | SHA-256 |
|---|---|
| `pod_owndet_full_v03.sh` | 26757c64… |
| `pod_owndet_cfg_v03.py` | 36757830… |
| `pod_owndet_infer_v02.sh` | 024d7f20… |
| `pod_owndet_export_v01.py` | 1caa6c7e… |

## Deviations and disclosures

1. **Training ran in two segments on two hosts,** joined by an exact resume at iteration 1,000 (optimiser, lr and momentum state from the checkpoint). Data order after the resume is not the order an unbroken run would have drawn.
2. **GPU architecture warning.** The sparse-convolution library's prebuilt kernels list no sm_89 (RTX 4090) build and print a warning on every call. Both segments ran on RTX 4090s with the same warning. The run never raised an "invalid device function" error, losses fell smoothly across the join, and the AP is close to the public checkpoint's. The fp32 kernels therefore ran correctly, presumably through PTX JIT.
3. **Training frames** were every 5th sweep, against probably every 10th sweep for the public checkpoint (design §2).
4. The **epoch count was set by compute,** 2 against the public 20 (addendum A).

## Spend

Pod 8peoqsmqm9exjw: 18.44 h × $0.89 ≈ $16.41. The pod was terminated at 06:22:38 EST on 5 Nov, and `list` was empty afterwards.

All Claude RunPod spend since 2 Nov is about **$29.59**, below the $34 stop line. Details are in `80_LOGS/runpod/SPEND_LOG_OWNDET_v01.md`.
