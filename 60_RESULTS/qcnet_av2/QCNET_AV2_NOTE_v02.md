# QCNet on AV2 Sensor val: the rerun under D16 v04 Choices 15–17 (note v02, 2 Nov 2026)

**What this is.** QCNet (checkpoint SHA-256 `b9f852ec…`, the same as in v01) rerun with every scene re-centred on the ego position at t₀. It was run on two history sources:
- **GT histories;**
- **"matched AB3DMOT" histories:** score ≥ 0.1, min_hits 3, and max_age equal to T1's track life converted to 10 Hz.

`QCNET_AV2_NOTE_v01.md` is kept. Its city-coordinate runs (GT, and released-default AB3DMOT) stay as the numerical sensitivity and the descriptive deployed run.

| Item | Location |
|---|---|
| Design | `50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md` + `QCNET_AV2_ARM_DESIGN_ADDENDUM_A_v01.md` (written before the run; cites T1's configuration by file and line) + `QCNET_AV2_ARM_DESIGN_ADDENDUM_A_ASRUN_v01.md` |
| Data | `30_DATA/qcnet_av2_v02/` (38 files; SHA256SUMS verified on the laptop) |
| Spend | `80_LOGS/runpod/SPEND_LOG_QCNET_v02.md` |

**Outcome statement.** On AV2 the rerun computed:
- counts and distributions;
- join coverage;
- finiteness and positive-definiteness;
- output-against-output checks: path replay, native vs shim, frame tests, city vs re-centred.

It computed no minADE/minFDE, exceedance, residual, NEES, coverage, quantile, margin or multiplier. No GT position after an origin was read.

## 1. Rules as fixed (addendum A1, A2)

**Matched AB3DMOT**
- Input: v01's 10 Hz LT3D detections (`dets_s010`, `0dbfe7cf…`), converted back to LT3D's tracker format.
- Score floor: ≥ 0.1, the 2 Hz trackers' floor.
- Top 500 boxes per sweep.
- **min_hits 3**, with AB3DMOT's own rule (Chiu `main.py` l. 491 and 587).
- **max_age = T1's life × 10 Hz.** T1's life comes from CANMOT `config/poly_mot/nusc_config_rotate_cov_cv.yaml`: l. 45 (`max_age`) and l. 10 (`LiDAR_interval: 0.5`), selected by `config/experiment/paper/local/canmot/sc.yaml` l. 6. That gives car 15 × 0.5 s = 7.5 s → **75 sweeps**, pedestrian and cyclist 5 s → **50 sweeps**.

**Re-centring.** o = ego (x, y) at t₀ is subtracted in float64 from agents and from every map point before QCNet's float32 cast. It is added back after the conversion, which is otherwise unchanged.

## 2. Checks (output against output)

| Check | Result |
|---|---|
| Path replay (released rules from the npz input, first 10 logs) | **Identical** to v01's tracker output: 183,837 rows, same track ids, max value difference 0.0 |
| Native vs shim (matched rules, 3 logs) | **Identical**: 43,857 rows |
| QCNet outputs, both runs | All rows finite, every Σ (modes, V1, V2) positive definite, π sums to 1 |

**Frame tests under re-centring (v05; log 0, 39 items; the whole pipeline applied to a transformed city scene).**

| Transform | max \|Δμ\| | max \|ΔΣ\| | max \|Δπ\| | Before re-centring (v01 tests) |
|---|---|---|---|---|
| Translation (123.4, −56.7) m | **1.2e-6 m** | 1.4e-6 | 1.1e-5 | 0.13 m |
| Rotation 0.7 rad | **0.72 mm** | 6.5e-4 | 5.1e-3 | 0.16 m |
| Rotation 90° | **0.37 mm** | 4.3e-4 | 4.3e-3 | 0.26 mm (exact transforms only) |

Wrong-sign control: misses by 2.92 m and 4.53 m. Passed.

**City-coordinate vs re-centred GT run** (107,756 items, same keys). This shows how large the float32 effect was in v01:
- |Δμ_V2|: median 3.8 mm, p90 2.3 cm, p99 10.3 cm, max **2.50 m**;
- max |Δπ| per item: median 0.009, p99 0.38, max 1.00;
- the most likely mode (V1) changes in **5.1 %** of items;
- max |ΔΣ_V2|: median 7.8e-4, p99 0.15, max 19.7 m².

The tail is larger than the v01 frame tests suggested. The re-centred runs are the ones to use.

## 3. Matched against released-default histories (counts)

**Tracks** (10 Hz, three classes). Matched publishes 2,399,166 rows, with 386,642 tentative rows held back by min_hits. Released published 2,785,808 rows.

| Class | Tracks (matched / released) | Length median (matched / released) | Length p90 (matched / released) | Tracks > 50 sweeps (matched / released) |
|---|---|---|---|---|
| Regular vehicle | 75,374 / 198,619 | 8 / 3 | 66 / 26 | 11,718 / 7,157 |
| Pedestrian | 57,185 / 146,500 | 4 / 2 | 35 / 14 | 3,276 / 1,736 |
| Bicyclist | 6,521 / 41,140 | 1 / 1 | 8 / 3 | 37 / 15 |

**Item histories** (`n_hist` = valid steps of the 50).

| Source | Items | n_hist median | 1 | 2–5 | 6–15 | 16–49 | 50 (share) | Agents per scene (median / p90) |
|---|---|---|---|---|---|---|---|---|
| GT, re-centred | 107,756 | 41 | 4,238 | 3,188 | 13,819 | 39,682 | 46,829 (43.5 %) | 43 / 82 |
| **Matched, re-centred** | 104,010 | **22** | 6,019 | 9,865 | 23,275 | 63,113 | 1,738 (1.7 %) | **446 / 764** |
| Released, city (v01) | 105,517 | 16 | 6,967 | 15,966 | 29,343 | 51,016 | 2,225 (2.1 %) | 938 / 1,475 |

Per class, matched: vehicle 74,472 items (median 24), pedestrian 29,126 (median 17), bicyclist 412 (median 16).

Reading (descriptive):
- The matched rules halve the clutter and lengthen histories (median 16 → 22 steps).
- A full 4.9 s history needs a published box in all 50 sweeps. Any missed detection breaks it, so full histories stay rare (1.7 %).
- Scenes still hold about 10 times more agents than GT. Persistent low-score detections pass min_hits 3.
- A published-track score threshold, such as T1's `SF_thre` of 0.14–0.16, would be a further pre-registered variant. It was not run.

**Other counts**
- Matched items visible at the target (existence): 93,220.
- Items with both steps 48 and 49 present: 87,478.
- Target jitter: within ±4.6 ms, as in v01.

## 4. Join coverage

GT ∩ matched = 103,203 keys.

**Against the 2 Hz audit records** (paired, k + 4 available).

| Audit set | Records | GT | Matched | Released | GT ∩ matched |
|---|---|---|---|---|---|
| T1 × LT3D, all | 92,166 | 90,252 | 89,479 (97.1 %) | 90,446 | **88,976 (96.5 %)** |
| T1, car in-path | 3,887 | 3,881 | 3,868 | 3,881 | 3,867 (99.5 %) |
| T1, pedestrian | 25,581 | 25,293 | 24,884 | 25,163 | 24,830 |
| T1, cyclist | 372 | 366 | 340 | 356 | 338 |
| T3 × LT3D, all | 92,124 | 90,226 | 89,467 | 90,438 | 88,965 (96.6 %) |
| T3, car in-path | 3,795 | 3,787 | 3,775 | 3,786 | 3,774 |

## 5. Runtime and cost

| Step | Time |
|---|---|
| Stage 1 (fetch without lidar, environments) | 3 min |
| QCNet GT, re-centred | 510 CPU-s to build scenes, 105 s of inference |
| Matched AB3DMOT | 15,451 CPU-s, about 30 min wall |
| QCNet on matched histories | 436 s |
| Packing | about 1 min |

Work ended at 07:15 EST. The laptop's power loss (07:05–08:51) stopped the copy-back, so the pod idled until the lead copied the outputs and terminated it at 08:58.

**Pod.** `lq459c84r42q2k` (RTX 4090, $0.89/h, 40 GB volume), 2.66 h ≈ **$2.37**, of which about $1.5 was idle time. QCNet total: $2.62 + $2.37 = **$4.99**.

**All Claude spend since 2 Nov.** `SPEND_LOG_K8CPU_v01.md` estimates ≈ $8.05 with a second K8 CPU pod still running at $1.12/h, so the $10 line now depends on that pod.

**Pods.** No QCNet pod remains.

**Deviations** (all in execution; see the as-run addendum):
- 40 GB volume;
- `qcnet_av2_infer_v03` replaced v02 to fix the pool transport (file-descriptor limit);
- LT3D build with `MAX_JOBS=8`;
- the top-500 cap binds in 256 sweeps;
- the GT branch was run by hand with the same commands.

No job was stopped on purpose.

## 6. Quantities computed on AV2 in this rerun (complete)

1. Counts and distributions:
   - tracks;
   - track lengths;
   - items per class × history stratum;
   - `n_hist` histograms;
   - agents per scene;
   - visible-at-target by existence;
   - join coverage.
2. Target jitter.
3. Finiteness, positive-definiteness, symmetry and Σπ = 1 checks.
4. Output-against-output checks:
   - path replay;
   - native vs shim;
   - frame tests under re-centring;
   - city vs re-centred GT outputs.

Nothing else was computed.
