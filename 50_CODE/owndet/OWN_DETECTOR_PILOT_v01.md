# Own CenterPoint on AV2: pilot and epoch rule (v01, 2 Nov 2026, 13:15 EST)

**Rule.** Design `OWN_DETECTOR_DESIGN_v01.md` §4 (SHA-256 `cf09bb11…`):
- E = min(20, floor(18 h × 3600 / (s/it × iters_per_epoch)));
- stop and report if E < 2 or if the projected total passes $36.

## Pilot, measured on pod `1nh5mu31ztk945`

Setup: RTX 4090 at $0.89/h, 13.6-CPU quota, 116 GB memory limit. 300 iterations, with records in `30_DATA/av2_det_owncp_v01/pilot/` (25 files, SHA256SUMS verified).

| Quantity | Value |
|---|---|
| Batch B | 4. The shipped config has `samples_per_gpu` = 1, and the public log shows 8 × A100-40GB, so B_ref = 8 |
| Learning rate | 1e-4 × 4/8 = 5e-5, cyclic as shipped |
| Mean time, iterations 101–300 | **1.649 s/it** (2.43 samples/s) |
| Data time | 0.021 s/it |
| Peak memory | 10.6 GB |
| Train infos | 15,245 frames (475 logs, every 5th sweep) |
| CBGS epoch | **115,674 samples = 28,919 iterations at B = 4** |
| Hours per epoch | **13.25** (≈ $11.79) |
| Epoch rule | floor(18 / 13.25) = **E = 1** |

Reading:
- The loss falls as expected in the pilot (2.19 at iteration 210).
- Data time is small and the GPU was 12 % busy in a snapshot, so the step is bound by the main process's CPU work, not by data loading or the GPU.
- For scale, the public model trained 20 epochs of 85,312 CBGS samples (1.71 M samples; log `20230216_171208.log`, 8 × A100, 0.61 s/it at batch 1 per GPU). One epoch here is 115,674 samples, 6.8 % of that.

## Decision under the rule: **stop and report** (E = 1 < 2)

The pod was terminated while blocked, per the standing rule. Spend so far: about $10.86 of the $36 stop line.

**Options for the lead.** Projections assume a fresh pod at $0.89/h: about 1.5 h to re-fetch and rebuild the infos and GT database (≈ $1.35), then training, inference (≈ 2 h) and export, AP and copy-back (≈ 0.6 h).

| Option | Training | Added cost | Projected total since 2 Nov |
|---|---|---|---|
| E = 1 (rule value, below the design's floor of 2) | 13.25 h | ≈ $15.5 | ≈ **$26.3** |
| Iteration cap at the 18 h training budget (≈ 39,300 iterations, 1.36 epochs; cyclic schedule over those iterations) | 18 h | ≈ $19.7 | ≈ **$30.6** |
| E = 2 | 26.5 h | ≈ $27.2 | ≈ **$38.1**: above the $36 stop line, below the $40 limit |

No full training has started.
