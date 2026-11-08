# Own CenterPoint on AV2: design addendum A (v01, 4 Nov 2026), the settings of the full run

**Status.** Written before the full training run. It adds to `OWN_DETECTOR_DESIGN_v01.md` (SHA-256 `cf09bb11…`). Sources:
- the lead's decision of 4 Nov 2026 (D18 v03, after the profiling);
- the profiling record `OWN_DETECTOR_PILOT_v02.md`.

Everything not listed here is as in the design, including the split `3771664f…`, every-5th-sweep frames, the shipped config and TTA at inference.

## A1. Training settings (final)

| Setting | Value |
|---|---|
| Batch | B = 4 |
| Learning rate | **5e-5** (1e-4 × B / B_ref, with B_ref = 8: the shipped `samples_per_gpu` 1 × 8 GPUs of the public log) |
| Sampler | LT3D's CBGS, unchanged. One epoch is 115,674 samples, 28,919 iterations at B = 4 |
| Length | **2 CBGS epochs = 57,838 iterations** (`IterBasedRunner`, `max_iters` 57,838) |
| Schedule | The shipped cyclic lr and momentum schedules (target ratios (10, 1e-4) and (0.85/0.95, 1), up-step ratio 0.4, one cycle) span the 57,838 iterations |
| Loader and threads | 11 loader workers; OMP/MKL/OpenBLAS threads 4 (profile P2). Model code unchanged; `get_targets` untouched |
| Expected wall time | about 16.5 h at 1.03 s/it, within the 18 h cap |

**Pace check.** The first 1,000 iterations re-measure the pace with CBGS batches. If the projection passes the 18 h cap or the $34 total since 2 Nov, the run continues only if the projected total stays below $34. Otherwise it stops at a checkpoint and is reported.

## A2. Real-time saving (researcher's rule of 4 Nov 2026)

**On the pod volume (`/workspace`).**
- Checkpoints every **1,000 iterations**, last 3 kept (`max_keep_ckpts = 3`), in the work directory with the mmcv text and json logs.
- Every training start resumes from the highest checkpoint present (`--resume-from`). A restart continues and never begins again.
- The prepared infos and GT database are archived on the volume once built, so a new container restores them instead of rebuilding.

**On the laptop.** A background loop runs every 2.5 h. It copies the latest checkpoint, the training log and a progress line (iteration, pace, ETA) to `30_DATA/av2_det_owncp_v01/train_progress/`, and appends a line to `80_LOGS/runpod/SPEND_LOG_OWNDET_v01.md`.

**Process control.** Every pod job is started with `setsid nohup`.

## A3. After training

Inference with the final checkpoint (iteration 57,838):
- on the 225 held-out train logs and the 150 val logs, every 5th sweep, config TTA;
- AP with the official evaluator (50 m, ROI) on both parts, against the public checkpoint's;
- copy-back with verified SHA256SUMS, termination, and `60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md`.

**Budget.** Stop and report before a projected total since 2 Nov of $34 (now about $11.91).
