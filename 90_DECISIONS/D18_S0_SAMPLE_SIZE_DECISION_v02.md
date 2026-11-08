# D18: the Argoverse 2 sample-size problem (S0): options and DECISION (v02, 2 Nov 2026, 10:25 EST)

v02 = v01 plus the decision and the choices it forces, below. v01 is kept.

**For the researcher's decision.** Every number here comes from counts only. No Argoverse 2 outcome has been computed.

## The problem

- H1, the primary confirmatory test, checks M*'s validity on three populations: PD7, SD1_7 and PD.
- For each population, the plan requires at least **6 power-qualified cells**: cells with enough logs that a real excess over δ would be caught.
- The floor exists so that the test cannot pass merely because too little was tested. It is part of the standard carried over from K6 and K7 (D14 §7).
- On the 150 Argoverse 2 validation logs, SD1_7 (decisions with a gap of 5 m or less) has only **4 or 5** such cells, against 18 on nuScenes.
- So **P(H1) = 0 on counts alone**, whatever the method does. Source: `70_TESTS/c1_scratch/c1_power_counts_v02.json`.

## How many logs are needed

Source: `70_TESTS/c1_scratch/c1_power_scaling_v03.json`. LT3D detector, both trackers. Development effect sizes are taken as true.

| Logs | SD1_7 cells (median) | P(floor met) | P(H1) |
|---|---|---|---|
| 150 | 4 | 0.00 | 0.00 |
| 263 | 6 | ≥ 0.95 | — |
| 300 | 8 | 1.00 | 0.87 |
| 375 | 11 | 1.00 | 0.94 |
| 500 | 16 | 1.00 | 0.88 |

More logs also help the secondary claims:
- H3 (joint risk, M*Jx) fits its scalar λ on 30 logs at 150, and on about 75 at 375.
- The chance that B6 slips through validity on T3 falls from 0.45 to 0.02 in the stress case.

## Options

| | Option | Cost and time | Effect on the standard |
|---|---|---|---|
| **A (recommended)** | **Train our own detector on part of AV2's 700 training logs.** CenterPoint with LT3D's code and configuration, trained on about 475 training logs. Run it, and both trackers, on the other ~225 training logs plus the 150 validation logs: **about 375 logs, all unseen by the detector**. The public LT3D detections on the validation logs stay as a sensitivity check. | A rented GPU, ≈ $12–15: download, ~10 h of training, inference. About 1 to 1.5 days. Total spend since 2 Nov would reach about $21–24, **above the $20 approval**. | Every standard kept; every Argoverse 2 detection is out of sample. |
| B | Run the public detectors on the training logs. | ≈ $5 and a few hours. | The public detectors were **trained on those logs**, so their detections there are too good, and in-sample logs cannot be exchanged with validation logs in the calibration. Reviewers would object. **Not recommended.** |
| C | Keep 150 logs and test SD1_7 pooled only, without the cell floor. | Free, no delay. | **Lowers the standard** for the safety-critical near-miss population, against D14 §7. It needs your explicit consent. |

## What does not change

- Under every option, the plan is frozen before any Argoverse 2 outcome is computed.
- Detector AP on the held-out logs is reported.
- Every choice and its reason is recorded.

## Decision

The researcher answered in chat on 2 Nov 2026, to "May I raise the RunPod limit to $40 total for option A?": **"Yes, option A"**. The RunPod limit is now **$40 in total from 2 Nov 2026**. About $8.82 was spent before this decision.

## Choices forced by option A, fixed before any training-log data is examined

1. **Split of the 700 AV2 training logs.**
   - Sort the log ids, then permute them with NumPy `default_rng(20261102)`.
   - The **first 225 are held out** for the confirmation; the **other 475 train the detector**.
   - The city composition of both parts is reported.
   - The split file is hashed and recorded before any training.
2. **Detector.**
   - CenterPoint from LT3D's code (commit e33189aa…), with the configuration of the public checkpoint, `centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2`.
   - It is trained from scratch on the 475 logs.
   - Training frames are every 5th sweep (LT3D's sample rule), to fit the budget.
   - Adaptations to a single GPU (batch size and a linearly scaled learning rate) are stated in a design file before training.
   - The number of epochs is set from a measured pilot, so the job fits its budget. The value and reason are recorded before the full run.
3. **Confirmation set.**
   - The new detector runs on the **225 held-out training logs plus the 150 validation logs: 375 logs**, at every 5th sweep.
   - Every log is unseen by the detector.
   - Its AP is reported on both parts, next to the public checkpoint's AP on validation.
4. **Primary detector for H1.** The new detector on the 375 logs.
   - The public LT3D detections on the 150 validation logs become a sensitivity, H1-P, which is descriptive because the floor fails at 150 logs.
5. **Second detector (H5).**
   - VoxelNeXt's public checkpoint is trained on all 700 training logs, so it can be used only on the 150 validation logs, where the floor fails.
   - **H5 becomes descriptive.** Training a second detector is outside the budget.
6. **Predictor arms.** QCNet (descriptive) and Trajectron++ on AV2 (H9) stay on the 150 validation logs with the public detections, as already built.
   - H9's label is re-checked against its counts before the freeze.
7. **Budget for this job.**
   - About $25 for download, pilot, training and inference.
   - Stop and report before the total since 2 Nov passes a projected $36.
