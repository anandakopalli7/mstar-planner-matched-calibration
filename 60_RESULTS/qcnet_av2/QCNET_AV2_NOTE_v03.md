# QCNet on AV2 Sensor val: primary deployed histories with T1's published-track threshold (note v03, 2 Nov 2026)

**What this is.** D16 v05 Choice 18 makes the **primary deployed histories** "matched AB3DMOT + SF": the v02 matched AB3DMOT, publishing only rows whose score is at or above T1's class `SF_thre`. QCNet ran re-centred, unchanged.

The labels are now:

| Label | History source | Run |
|---|---|---|
| Primary deployed | Matched + SF | v03 |
| Secondary | Matched, no threshold | v02 |
| Descriptive | Released defaults | v01 |
| Upper bound | GT histories | v02, re-centred |

Notes v01 and v02 are kept.

| Item | Location |
|---|---|
| Design | `50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_ADDENDUM_B_v01.md` (SHA-256 `1a501933…`), written before the filter or any pod |
| Data | `30_DATA/qcnet_av2_v03/` (21 files; `SHA256SUMS.txt` `d744cf7d…`, 21/21 OK on the laptop) |
| Spend | `80_LOGS/runpod/SPEND_LOG_QCNET_v03.md` |

**Outcome statement.** Only counts, distributions, join coverage, and finiteness and positive-definiteness checks were computed. There was no minADE/minFDE, exceedance, residual, NEES, coverage, quantile, margin or multiplier, and no GT position after an origin was read.

## 1. The threshold (addendum B)

**Values.** `SF_thre` comes from CANMOT `config/poly_mot/preprocessing/centerpoint_nusc.yaml`, line 1, which T1 loads through `nusc_config_rotate_cov_cv.yaml`, line 4. The T1 × LT3D export record confirms them.
- car (REGULAR_VEHICLE): **0.16**
- pedestrian: **0.16**
- cyclist (BICYCLIST): **0.14**

**Score.** The score of a published (updated) AB3DMOT row is the score of the detection that updated it. That is the quantity T1 thresholds (`nusc_loader.py`, line 72) and the score T1 gives an updated track (`nusc_score_manage.py`, line 80).
- No row sits exactly at a threshold, so the decision's "≥" and T1's ">" give the same result.

**Application.** A post-filter on `trk10_ab3dmot_matched_3cls_v02.npz`, run on the laptop as one light process (`50_CODE/qcnet/qcnet_trk_sf_filter_v01.py`).
- 2,399,166 rows → **1,766,350 kept** (632,816 removed):
  - vehicles 1,229,818 / 1,680,971;
  - pedestrians 521,966 / 693,564;
  - bicyclists 14,566 / 24,631.
- **Difference from T1:** sub-threshold detections still feed the tracker's state, hits and life, as in v02. They are only not published.

## 2. Histories and clutter, four sources

**Item histories.**

| Source | Items | n_hist median | 50/50 share | Agents per scene, median (p90) |
|---|---|---|---|---|
| GT (upper bound) | 107,756 | 41 | 43.5 % | 43 (82) |
| **Matched + SF (primary)** | **101,935** | **19** | **1.5 %** | **356 (669)** |
| Matched (secondary, v02) | 104,010 | 22 | 1.7 % | 446 (764) |
| Released (descriptive, v01) | 105,517 | 16 | 2.1 % | 938 (1,475) |

**Matched + SF by class.**

| Class | Items | n_hist = 1 | 2–5 | 6–15 | 16–49 | 50 | Visible at target |
|---|---|---|---|---|---|---|---|
| Regular vehicle | 73,026 | 4,163 | 7,026 | 18,032 | 42,534 | 1,271 | 66,146 |
| Pedestrian | 28,520 | 2,071 | 4,358 | 7,864 | 13,937 | 290 | 25,135 |
| Bicyclist | 389 | 20 | 62 | 127 | 172 | 8 | 345 |

Items with steps 48 and 49 both present: 83,048. Matched-track candidates at origins: 314,947.

**Track lengths (published rows per track).**

| Class | Matched + SF: tracks, median, p90 | Matched (v02) | Released (v01) |
|---|---|---|---|
| Vehicle | 58,294; 9; 60 | 75,374; 8; 66 | 198,619; 3; 26 |
| Pedestrian | 42,816; 4; 35 | 57,185; 4; 35 | 146,500; 2; 14 |
| Bicyclist | 3,884; 1; 8 | 6,521; 1; 8 | 41,140; 1; 3 |

**Reading (descriptive).**
- The threshold cuts the scene clutter by another 20 %: a median of 446 → 356 agents, against 938 for released and 43 for GT.
- Item histories get slightly shorter (median 22 → 19 steps). Sub-threshold sweeps inside a track become missing steps.
- Deployed scenes still hold about 8 times more agents than GT, and full 4.9 s histories stay rare.
- That reflects LT3D's box density at score ≥ 0.16 (≈ 75 published boxes per sweep for the three classes) together with AB3DMOT's 10 Hz track fragmentation (a median vehicle track of 9 sweeps). A threshold alone does not remove it.

## 3. Checks and coverage

**Checks.** All 101,935 rows are finite. Every Σ (modes, V1, V2) is positive definite, π sums to 1, and V2 is symmetric. Target jitter is within ±4.6 ms, as before.
- 2 CUDA-OOM fall-backs to a smaller batch occurred. Batch size does not change outputs (v01: ≤ 2e-5 m).

**Join between sources.**
- Matched + SF ⊂ matched: every key is in v02.
- GT ∩ matched + SF = **101,377**.

**Against the 2 Hz audit records** (paired, k + 4 available).

| Audit set | Records | Matched + SF | GT ∩ matched + SF |
|---|---|---|---|
| T1 × LT3D, all | 92,166 | 88,566 (96.1 %) | **88,182 (95.7 %)** |
| T1, car in-path | 3,887 | 3,856 | 3,855 (99.2 %) |
| T1, pedestrian | 25,581 | 24,618 | 24,575 |
| T1, cyclist | 372 | 328 | 326 |
| T3 × LT3D, all | 92,124 | 88,553 | 88,170 (95.7 %) |
| T3, car in-path | 3,795 | 3,763 | 3,762 (99.1 %) |

## 4. Runtime, cost and pods

**Pod.** `twtoo6fyhfzxo8` (`claude-programmeA-qcnet3`, RTX 4090 at $0.89/h, 40 GB volume, SECURE). Jobs were started with `setsid nohup`; inputs were uploaded in the background and checked against their SHA-256 sums on the pod.
- Wall time 09:09:32 → 09:21:14 EST. Fetch and environment took 3 min; QCNet took 366 s (1,274 CPU-s building scenes, 335 s of inference).
- Pod cost: 0.195 h ≈ **$0.17**.
- The 42 code files hashed on the pod equal `50_CODE/qcnet/pod/`.

**Totals.**
- QCNet arm: $2.62 + $2.37 + $0.17 = **$5.16**.
- All Claude spend since 2 Nov: ≈ $8.6 (lead's figure before this step) + $0.17 + the lead's K8 CPU pod time since then.

**Pods.** The pod was terminated at 09:21:14 EST, and `list` then showed no claude-programmeA pod.

**Laptop.** The only laptop job was the one light post-filter process. No job was stopped on purpose.

## 5. Quantities computed on AV2 in this step (complete)

1. Counts and distributions:
   - rows kept and removed by the threshold;
   - tracks and track lengths;
   - items per class × history stratum;
   - `n_hist`;
   - agents per scene;
   - visible-at-target by existence;
   - join coverage.
2. Target jitter.
3. Finiteness, positive-definiteness, symmetry and Σπ = 1 checks.

Nothing else was computed.
