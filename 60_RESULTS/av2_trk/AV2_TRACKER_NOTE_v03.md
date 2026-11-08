# Argoverse 2: T1, T3 and AB3DMOT on the 375 C1 confirmation logs, own detector (v03, 5 Nov 2026)

**What this is.** This step ran the trackers on the C1 confirmation set with our own CenterPoint:
- **Trackers:** T1 (CANMOT `paper/local/canmot/sc`), T3 (Poly-MOT `paper/baseline/poly_mot`) and AB3DMOT (tracker label `tab`, Choice 38c).
- **Confirmation set:** 225 held-out train logs + 150 validation logs = 375 logs.

It also prepared what stage A needs:
- the tracker exports;
- the 2 s propagation;
- the ego path;
- the one prepared ground-truth file;
- the list of ground-truth files for the quarantine.

**It stops before stage A.** On the lead's instruction of 5 Nov (received about 09:28), the Rule 0 tracker metrics on the 375 logs were **not** computed (§5).

The design is `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v04.md` (SHA-256 c97ba992…), written before any fetch or run of this step. Notes v01 and v02 are unchanged.

**Outcome statement.** On the 375 logs this step computed only:
- tracker outputs;
- the trackers' own 2 s propagation of mean and covariance;
- logged ego poses;
- the prepared ground-truth table (Rule 0);
- integrity counts.

It computed no tracking metric, residual, projected error, exceedance, coverage, margin, NEES/ANEES, quantile, multiplier, minADE/minFDE or risk number. It ran no stage A, no stage B, no `k8_items` and no `c1_*` entry point. No ground-truth file was opened by hand; ground truth was read only by the tools (`av2_gt_prep_v02`, `av2_ego_prep_v02`, which reads only the samples' ego poses, and the 150-log metric equivalence tests).

## 1. What ran

| Step | Tool | Output | Result |
|---|---|---|---|
| Train-log metadata | `av2_fetch_v05` (public bucket, prefix `datasets/av2/sensor/train/<log>/`) | `30_DATA/av2_train225/` | 225 logs, 900 files fetched (annotations, poses, 2 calibration files each; 179.0 MB), every file's MD5 equal to its ETag; 35,412 lidar keys listed, **not** fetched (35.6 GB); 0 failures |
| 375-log list | `av2_c1_logs_v01` | `30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` (49c363fd…) | `held_out_225` of `AV2_TRAIN_SPLIT_v01.json` (3771664f…, checked disjoint from `train_475`) + the 150 `av2_val` folders, sorted |
| Frame check | `av2_c1_frame_check_v01` | `60_RESULTS/av2_trk/c1_375/C1_FRAME_CHECK_v01.json` | §3 |
| Velocity probe P-c | `av2_c1_velocity_probe_v01` | `…/C1_VELOCITY_PROBE_v01.json` | §3 |
| Tracker input | `av2_tracker_input_v02 --detector owncp --workers 8` | `30_DATA/av2_trk_v02/input/owncp/` | §4 |
| Prepared ground truth | `av2_gt_prep_v02 --logs-file C1_LOGS_375_v01.json` | `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json` (e5c390aa…) | 375 logs, 12,038 samples, 717,382 mapped annotations (tool summary) |
| Ego path | `av2_ego_prep_v02` | `30_DATA/av2_trk_v02/ego/av2_c1_ego10hz_v01.json.gz` (3e4acb4a…) | 375 logs; all 12,038 frames' poses equal the GT table's; median 10.06 Hz |
| T1, T3 | `av2_track_v02 --detector owncp --fast-convex`, 8 subsets each, nuScenes parameters, nothing re-tuned | `30_DATA/av2_trk_v02/export/{t1,t3}_owncp/worker0…7/` | §4 |
| AB3DMOT (`tab`) | `av2_ab3dmot_v05 --detector owncp --fast --n-workers 6` (LT3D defaults) | `30_DATA/av2_trk_v02/export_tab_owncp/ab3dmot_{det,kf}/worker0…5/` | §4 |
| 2 s propagation | `av2_horizon_prep_v02 --propagate-only --allow-av2-propagation` (Choice 13) for T1, T3; AB3DMOT's own, its worker files merged in worker order | `30_DATA/av2_trk_v02/horizon/horizon8_{t1,t3,tab}_owncp.jsonl.gz` | §4 |
| GT list for the quarantine | `av2_c1_gt_list_v01` | `30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt` | §6 |

**Environments.** All tools ran with `python -I -B` from `C:\Users\anand`:
- canmot310 for the tracker input, GT, ego, T1/T3 and propagation;
- ab3dmot310 for AB3DMOT;
- av2eval310 for the HOTA equivalence test only.

Single-threaded BLAS and numba throughout.

**Drivers.**
- `run_av2_c1_equiv_gt_v01.sh` and `run_av2_c1_equiv_trk_v01.sh` ran the tests.
- `run_av2_c1_queue_v01.sh` ran the production queue. It is resumable, starts each job only after its tool's equivalence test has passed, and stops if C: falls below 8 GB.
- At most 3 of these processes ran at a time (`nproc` 8; the CPU was shared and often at 100 %).

**Checkpoints.** The trackers checkpoint per log. No resume was needed in production (0 logs reused). The resume path was tested in §2.

## 2. Equivalence tests (150 validation logs, public LT3D detections)

Test outputs were written under the scratchpad and deleted after the comparison; ground-truth test outputs were deleted at once. Results are in `60_RESULTS/av2_trk/c1_375/equiv/`.

| Tool | Test | Result |
|---|---|---|
| `av2_common_v02` | `log_dir`, `sweep_timestamps`, `frame_timestamps` for all 150 logs; v01 constants and detector paths | **identical** |
| `av2_gt_prep_v02` | no log list, and `--logs-file` = the 150 logs | **byte-identical**: both outputs have SHA-256 9642db5b… = `30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json` (hashed, never opened); each copy deleted at once (06:56:26 and 06:57:24) |
| `av2_ego_prep_v02` | `--gt` the v01 GT file | **identical** decompressed content to `av2_cache_stageA_v01/av2_ego10hz_v01.json.gz` (gzip headers carry a time stamp); copy deleted 06:58:00 |
| `av2_tracker_input_v02` | `--detector lt3d --workers 4` | `first_tokens.json` **byte-identical**. Each `dets_worker*.json` is **byte-identical after one documented substitution**: its meta names the adapter `av2_tracker_input_v02` (exactly one occurrence per file). Receipt equal on every non-path, non-time key |
| `av2_track_v02` | T1 worker 3, stopped on purpose after 5 logs (`--test-stop-after 5`) and resumed (5 logs reused from checkpoints); T3 worker 1 straight | decompressed `x1_tracks` (57,042 and 57,094 lines) and `x1_per_frame.json` **byte-identical** to v01's; record stats, criteria and fields equal |
| `av2_ab3dmot_v05` | `--detector lt3d --fast`, worker 1 of 6, stopped on purpose after 3 logs and resumed (3 reused) | det and kf exports (75,265 lines each), horizon file and per-frame file **identical** to `export_ab3dmot_v04w6` worker 1 |
| `av2_horizon_prep_v02` | v01 T1 and T3 LT3D worker 0 | output = the first 58,939 / 58,943 lines of `horizon8_{t1,t3}_lt3d.jsonl.gz`, **identical**; without `--allow-av2-propagation` it refuses and writes nothing |
| `av2_track_metrics_v04` | `--logs-file` = the 150 logs, v01 T3 VoxelNeXt exports and the v01 GT file | every per-class value and the counts **equal** to `metrics/AV2_metrics_t3_voxelnext.json` |
| `av2_hota_v04` | the same inputs | **not bit for bit; equal within relative tolerance 1e-12** (below) |

**HOTA.** Two values differ from v03's stored output in the last binary digit:
- bicycle `HOTA_mean_over_10_thresholds`: 0.36836255402675544 against 0.3683625540267555;
- truck AssA: 0.6338765065023598 against 0.6338765065023599.

A control rerun of **v03 itself** on the same inputs also differs from v03's stored output in the last digit (car and truck AssA). So the evaluator is not bit-reproducible from run to run, most likely because floating-point summation order follows Python's randomised string hashing under `-I`. The verdict is therefore made at relative tolerance 1e-12, with the exact comparison and the control kept:
- `EQUIV_hota_v04_t3_voxelnext_exact.json`;
- `EQUIV_hota_v04_t3_voxelnext_rtol.json`;
- the gate copy `metrics_gate_held/EQUIV_hota_v04_t3_voxelnext.json`.

`av2_fetch_v05` has no earlier output to reproduce. It was checked by sizes and MD5s, and its listings against the pod's own manifest (§3).

## 3. Frame-timestamp check and velocity probe

- **Held-out 225 logs.** For every log, `sweeps[::5]` from the recorded bucket listing equals the own detector's frame timestamps (held-225 npz). That gives 225 of 225 logs equal and 7,232 frames, with 32–40 frames per log. **No mismatch.**
- **Validation 150 logs.** Checked against the local lidar folders: 150 of 150 logs equal, 4,806 frames, 31–40 frames per log.
- **Log sets.** The npz log sets equal the list's two parts.
- **Listing against the pod's fetch.** Every one of the 35,412 listed lidar keys (key, size, ETag) equals the pod's own fetch manifest `env/MANIFEST_train_confirm_v06_maps.csv`, for all 225 logs.
- **Velocity convention (P-c; detector against detector, no ground truth).** On the 150 validation logs, 117,138 own/LT3D detection pairs were matched (same frame and category, both scores > 0.5, mutually nearest within 1 m).
  - median |v_own − v_lt3d| = 0.019 m/s;
  - median cosine of the two velocities = 0.99986 over the 35,936 pairs where both speeds exceed 1 m/s (mirrored: −0.99986; axes swapped: 0.004);
  - median speeds 0.010 and 0.017 m/s.

  The own detector's (vx, vy) therefore follows LT3D's convention, and the adapter's rotation-only conversion (design v03 §3) applies unchanged.

## 4. Counts

**Detections (adapter receipt).** Rows: 31,191,145 (validation 12,376,531; held-out 18,814,614). Mapped to the seven tracking classes: 9,205,983. After the 54 m square, the 0.1 floor and CANMOT's `SF_thre`, 1,617,812 boxes were kept:

| Part | Kept |
|---|---|
| validation | 624,093 |
| held-out | 993,719 |

| Class | Kept |
|---|---|
| car | 898,127 |
| pedestrian | 445,989 |
| truck | 136,780 |
| trailer | 39,679 |
| bicycle | 39,028 |
| bus | 36,629 |
| motorcycle | 21,580 |

All 12,038 frames carry detections. The 8 subsets hold 46–47 whole logs and about 202,000 boxes each. Receipt SHA-256 6bfb5002…; first tokens baedd61d….

**Tracker outputs.** Every worker record is PASS, with no failed criteria. Each of the three runs covers all 375 logs and 12,038 frames, with dataset tag `av2_sensor_val_train`.

| Run | Part | Logs | Frames | Detections to the tracker | Exported track records |
|---|---|---|---|---|---|
| T1 CANMOT sc | held-out 225 | 225 | 7,232 | 410,515 | 526,947 |
| T1 CANMOT sc | validation 150 | 150 | 4,806 | 257,986 | 331,301 |
| T1 CANMOT sc | pooled | 375 | 12,038 | 668,501 | 858,248 |
| T3 Poly-MOT | held-out 225 | 225 | 7,232 | 410,515 | 526,898 |
| T3 Poly-MOT | validation 150 | 150 | 4,806 | 257,986 | 331,306 |
| T3 Poly-MOT | pooled | 375 | 12,038 | 668,501 | 858,204 |
| AB3DMOT (`tab`), kf and det exports | held-out 225 | 225 | 7,232 | 1,335,870 | 1,335,870 |
| AB3DMOT (`tab`), kf and det exports | validation 150 | 150 | 4,806 | 838,290 | 838,290 |
| AB3DMOT (`tab`), kf and det exports | pooled | 375 | 12,038 | 2,174,160 | 2,174,160 |

What the counts mean:
- "Detections to the tracker" is CANMOT's `det_num` after its own filters for T1/T3. For AB3DMOT it is the mapped detections after LT3D's score > 0.1 and top-500 rules.
- AB3DMOT outputs one record per associated detection, as on the 150 logs (note v02).
- T1/T3 median tracks per detection are 1.26–1.30 (K2 band 0.2–1.5).
- AB3DMOT has 0 non-positive-definite xy covariances.

**2 s propagation.** The propagation files cover exactly the export records.

| Tracker | Records | Note |
|---|---|---|
| T1 | 858,248 | `ExtendedKalmanFilterRotate`; Q SHA-256 59c0aea8…, as on the 150 logs |
| T3 | 858,204 | `ExtendKalmanFilter`, `LinearKalmanFilter`; Q 0a3a48d5…, as on the 150 logs |
| AB3DMOT | 2,174,160 | its own F and Q; lines aligned with the `ab3dmot_kf` export (equal line count) |

## 5. Rule 0 tracker metrics: held, not computed (deliberate stop)

**What the lead said.** At about 09:28 on 5 Nov the lead said not to compute the 375-log tracker metrics (HOTA, AMOTA, MOTA, IDS) yet. Every confirmation-set quantity is to be computed only after the plan's text lock, which precedes stage A.

**What was done.**
- No metric job had started (the queue's metric jobs were waiting for the tracker outputs).
- At 09:28:22 the two files that gate them in the queue (`EQUIV_track_metrics_v04_t3_voxelnext.json`, `EQUIV_hota_v04_t3_voxelnext.json`) were moved to `60_RESULTS/av2_trk/c1_375/equiv/metrics_gate_held/`. The queue therefore never started a metric job.
- `60_RESULTS/av2_trk/c1_375/metrics/` and `hota/` are empty. There are no partial outputs.
- After the propagation finished, the queue process, which was then only waiting on the held metric jobs, was stopped on purpose: 11:00:21, bash PIDs 20840, 30424 and 35568, all mine; no python job was running.

**Ready for later.** The jobs are defined in `run_av2_c1_queue_v01.sh`:
- `av2_track_metrics_v04 --classes car pedestrian bicycle` and `av2_hota_v04`;
- per part with `--logs-file C1_LOGS_375_v01.json --logs-key held_out_225 | val_150`, and pooled with `--logs-key logs`;
- for T1, T3 and both AB3DMOT exports.

Moving the two files back and restarting the queue runs exactly those jobs, which the tracker jobs would skip as done. `av2_c1_tables_v01.py` then writes the table beside the 150-log public-LT3D table of note v02 §3.

## 6. Ground-truth files for the quarantine

`30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt` (SHA-256 874d4cbd…) lists, as `<sha256>  <path>`, the files to pass to `--extra`:

| File | SHA-256 |
|---|---|
| `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json` (the one prepared file; plan §8.4) | e5c390aad971502aec3546d4e2093a3282d3774ed93dc004fb141599d8adb2c2 |
| `30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_gt_v01.feather` | a9d85a547f536d97fb1c756643272b5f53fdc1bc55385ec7c7554e54aa1a362e |
| `30_DATA/av2_det_owncp_v01/held225/av2held225_owncp_centerpoint_gt_v01.feather` | 8cb86154f41c59187ff62ab82159ec3093c094897da94d440106e9b3862ec5ef |

- **Already handled by the plan:** `30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json` (9642db5b…) and `30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_gt_v01.feather` (a9d85a54…). The second is the **same bytes** as the own detector's val-150 feather, so the quarantine's hash scan treats both copies.
- **Kept out of the workspace:** no ground-truth test output was kept; each was deleted at once (§2).
- **Not quarantined:** the public `annotations.feather` files of `30_DATA/av2_val` and the new `30_DATA/av2_train225` stay outside, as plan §8.4 concedes.

## 7. Files and hashes

### Code (`50_CODE/av2/`)

| File | Role | SHA-256 |
|---|---|---|
| `AV2_TRACKER_PORT_DESIGN_v04.md` | design (written before any run of this step) | c97ba99267a83fe5c258ce74eaff9ddd7af232e0dc80fa5dcb3474577eb3917f |
| `av2_common_v02.py` | v01 + data roots, sweep-list rule, own detector | cfee915dce66c30915bc657a6147998ee67b995064ddab391f411566af3db686 |
| `av2_fetch_v05.py` | train metadata + lidar key listing | 7d6baf5b90df399d3e5bd9176cafd337b8fa6596acdf229148444f2de70ab564 |
| `av2_c1_logs_v01.py` | the 375-log list | efda01cbc02942bc96f4ba03608c931b21790fab3d774314cf7d72e0baa7069a |
| `av2_gt_prep_v02.py` | prepared ground truth (v01's computation) | 5cba8fb9d190ed39b45f1376192cf5eeea24205efac3bc8ff30bc7f4eef8ba77 |
| `av2_ego_prep_v02.py` | ego path | 037015f21dae83729725e097271ddf037cbea7ab054e62a596e48ea8b384089a |
| `av2_tracker_input_v02.py` | adapter, several sources | b236804f30864c9bceac8a72cd999b240045009bc3f7c7f96c4439091e5813af |
| `av2_track_v02.py` | T1/T3 runner, per-log checkpoints (corrected 07:07:05) | 0a9a0eb300de4cd58ddcddf661547953688a8cf639e81bf45eafa74ceee25eed |
| `av2_ab3dmot_v05.py` | AB3DMOT driver, per-log checkpoints (corrected 07:07:05) | e4ea995048402403c7a553bd49e2ffe3a2f26e44238e83825972349a4aa59d54 |
| `av2_horizon_prep_v02.py` | 2 s propagation, guard by tag prefix | 76cc6a9aa7f7ad0992ab3f449298755feb1eef413e7e83f8c8979ba9bc02e540 |
| `av2_track_metrics_v04.py` | AMOTA/MOTA/IDS with a log restriction (equivalence test only; not run on the 375 logs) | 981db2a602ad28749235958b28a46153906ac47978ec5d8b63d6adf2566e0206 |
| `av2_hota_v04.py` | HOTA with a log restriction (equivalence test only; not run on the 375 logs) | 26944dc245419335963d4ab4d1b3d6a9cda9220ff58ae5003f2dde42b664bbb9 |
| `av2_c1_frame_check_v01.py` | frame-timestamp and listing check | 10fc4964ac04eaf2a7e2585e38f7900af6f1166dbc584165a52c0dc38013a961 |
| `av2_c1_velocity_probe_v01.py` | probe P-c | 1286d35861072884216e3fb7d4030fd8c5fb286838ec637cbe97fce53159e068 |
| `av2_c1_gt_list_v01.py` | GT list for the quarantine | 75bac8577bf51b5d06f2a15391952765334f5c064309944fb2565c9286bef7a9 |
| `av2_c1_tables_v01.py` | note tables (counts used here; its metric part waits for the metrics) | 481fdc209684d45b1077080b69a3f9beff32737c8187baf25d40a900be3d2112 |
| `test_av2_port_v04_equiv_v01.py` | equivalence comparisons | 6ad5652800828855cdeac725841d3b5575396092187f3c4f05d411932a949c82 |
| `run_av2_c1_equiv_gt_v01.sh` | GT/ego equivalence driver | dcb13120d067f57f4c5be46bc9f7f0b8ef4b5bfe9597a326cbfd62d64f1c9ce5 |
| `run_av2_c1_equiv_trk_v01.sh` | tracker-side equivalence driver | f03b0130570278486df8b5cb9418da83fc4145139472846b38e033682cb945eb |
| `run_av2_c1_queue_v01.sh` | production queue | e7cff37d159e5c811ab12c7f28323007072963cb87ec28f81625e8ab3d26d327 |

Used unchanged: `av2_feather_v01.py`, `x1/x1_export_v06.py`, `x1/fast_convex_v01.py`, `shims_lt3d/data/utils.py`, the CANMOT and LT3D trees.

### Data (`30_DATA/av2_trk_v02/` unless named)

`30_DATA/av2_trk_v02/SHA256SUMS_v01.txt` (SHA-256 b8c732f76f22618b1b205ff0bbf12479dbf260ed779c21d00c20f4d88d8f8995) hashes all 108 output files of this folder (logs and the numba cache excluded). The main ones:

| File | SHA-256 |
|---|---|
| `C1_LOGS_375_v01.json` | 49c363fd3e1e41a71bbc39d73fba7f0732730d8a6b47045e206bfd081e157f88 |
| `gt/av2_c1_gt375_v01.json` | e5c390aad971502aec3546d4e2093a3282d3774ed93dc004fb141599d8adb2c2 |
| `ego/av2_c1_ego10hz_v01.json.gz` | 3e4acb4a946f8a07aa55dd73e7f100fa298e91b0b7012f7df4cb5e2729c50033 |
| `input/owncp/receipt.json` | 6bfb5002decea498a05c48dc778e85891903f27d895f7e076fc5757d6d559871 |
| `horizon/horizon8_t1_owncp.jsonl.gz` | 168f0ad9eb55d8ff9ed14cb75677c853d9e2b1356bea471e1daa1963321651f2 |
| `horizon/horizon8_t3_owncp.jsonl.gz` | b10ea0715040817c6cd41a32062d7957c2ac0e655e0632d50ebe263629141181 |
| `horizon/horizon8_tab_owncp.jsonl.gz` | 578a813a830285246ca92e657a756e72a6fe80ebd9882ea97e25bdb1861b8835 |
| `GT_FILES_FOR_QUARANTINE_v01.txt` | 874d4cbdd6d2c77e2bd2d619c772caf2e5786d51e433e31fcec895cf8b549304 |
| `30_DATA/av2_train225/MANIFEST_av2_train225_meta_v05.csv` | d3ad784097d9fc6a37f820551db625166cc262d6cbf638beff772ac30cfaf005 |
| `30_DATA/av2_train225/FETCH_SUMMARY_av2_train225_meta_v05.json` | 29ef573920af9ac02ddb56b7d880216ed5f6ba37cb1372726c735c771766c604 |
| `60_RESULTS/av2_trk/c1_375/C1_FRAME_CHECK_v01.json` | c315b27b593751056803ddaaac7fff953092aaa967db69a1bb72cdf836279dae |
| `60_RESULTS/av2_trk/c1_375/C1_VELOCITY_PROBE_v01.json` | 350e3aff4782c025c68479d0d468d55a6d7b476b555d47dc33c04b5fbb4ef1fc |

The export gzip files carry a time stamp in their header. Each worker record also gives the SHA-256 of the decompressed tracks (`output_sha256`). Logs are in `30_DATA/av2_trk_v02/logs/` (queue: `run_queue_v01.log`, one `q_<job>.log` per job).

## 8. Deviations, corrections and stops

1. **Two tools corrected in place at 07:07:05, before any production output was kept.** `av2_track_v02` and `av2_ab3dmot_v05` hashed each checkpoint part's lines without the newline translation that the text-mode gzip writer applies on Windows (`\n` → `\r\n`, the same as v01/v04's writers). The outputs were correct, but every resume would have recomputed instead of reusing.
   - **The fix.** Hash the written bytes, and change the harness and checkpoint key strings so that older checkpoints are never reused.
   - **Found by** the first T1 resume test, whose second process reused 0 of 5 logs.
   - **Stopped on purpose** (my own PIDs), because they used the pre-fix files:
     - the production `t1_w0` job, started 07:06:01 (PIDs 37892, 38068). Its partial checkpoints are invalid under the new key; it reran from 07:30 and passed;
     - the AB3DMOT resume test (PIDs 39864, 37904 and its bash).
   - **Tests rerun on the fixed files** (07:07–07:14): T1 and T3, and AB3DMOT. The first results are kept in `equiv/superseded_checkpoint_hash_bug/`.
2. **Other edits after a file's first version** (none changes any production computation):
   - `test_av2_port_v04_equiv_v01.py`:
     - 07:07, `--expect-reused`, so a resume test must reuse;
     - about 07:20, top-level `identical` kept as the last key;
     - 07:26, `--rtol` / `--control` mode for the HOTA comparison.
   - `run_av2_c1_equiv_trk_v01.sh`: 07:07:39, passes `--expect-reused`.
   - `run_av2_c1_queue_v01.sh`: 06:57, gates and the `QUEUE_LIMIT` file, before its first launch.
   - `av2_c1_tables_v01.py`: 07:31, removed a no-op loop, before any run.
   - `av2_tracker_input_v02.py`, `av2_ab3dmot_v05.py`, `av2_horizon_prep_v02.py`, `av2_gt_prep_v02.py`, `av2_ego_prep_v02.py`, `av2_track_metrics_v04.py`, `av2_hota_v04.py` were each created as a copy of their v01 (v04, v03) and patched within minutes, before any run.
3. **Result files rewritten without changing their content.**
   - About 07:20: the two `EQUIV_track_v02_*` files were re-serialised so that `identical` is the last key, which the queue's gate reads.
   - 07:28: the exact HOTA comparison was renamed `_exact` and the tolerance verdict copied as the gate file.
   - 09:28: the two metric gate files were moved to `metrics_gate_held/` (§5).
4. **The HOTA equivalence passed at rtol 1e-12, not bit for bit** (§2). AMOTA/MOTA/IDS (`av2_track_metrics_v04`) matched exactly.
5. **The tracker input's `dets_worker*.json` carry the adapter name `av2_tracker_input_v02`** in their meta. They are byte-identical to v01's only after that one substitution (§2).
6. **Dataset tag `av2_sensor_val_train`** on the 375-log exports (design v04 §9). The C1 guard normalises it to `av2`; `av2_horizon_prep_v02` treats it as AV2. **`av2_horizon_prep_v01` must not be used on these exports**, because its guard only knows `av2_sensor_val`.
7. **8 tracker subsets instead of v01's 4.** This was for memory and resume granularity; the worker count is a parameter, not a constant.
8. **The plan text (§1.1, §8.4, §8.5 step 1) names `av2_gt_prep_v01 --logs`.** v01 cannot read the 225 train logs (its data root is `av2_val` only), so the file was made with `av2_gt_prep_v02`. That tool reproduces v01 byte for byte on the 150 logs. The plan text should name v02.
9. **Deliberate stops:**
   - the simulated crashes in the resume tests (`--test-stop-after`);
   - the processes in item 1;
   - the metric gate (§5);
   - the final queue stop (§5).

   Nothing was interrupted by accident.
10. **Disk.** C: had 28 GB free at the start; the minimum seen was 20 GB, and 38 GB free at the end. The step added 4.4 GB (`30_DATA/av2_trk_v02`) + 0.18 GB (`30_DATA/av2_train225`) (all under `30_DATA/av2_trk_v02/` and `30_DATA/av2_train225/`). No lidar was downloaded for the 225 train logs.

## 9. For stage A (not run here)

The stage-A builder needs the following inputs. Every stage-A manifest must name the one GT file (e5c390aa…).

| Input | T1 | T3 | AB3DMOT |
|---|---|---|---|
| `--workers` | `30_DATA/av2_trk_v02/export/t1_owncp/worker0…7` | `30_DATA/av2_trk_v02/export/t3_owncp/worker0…7` | `30_DATA/av2_trk_v02/export_tab_owncp/ab3dmot_kf/worker0…5` |
| `--horizon` | `horizon/horizon8_t1_owncp.jsonl.gz` | `horizon/horizon8_t3_owncp.jsonl.gz` | `horizon/horizon8_tab_owncp.jsonl.gz` |
| `--experiment` | `paper/local/canmot/sc` | `paper/baseline/poly_mot` | `lt3d/ab3dmot`, as for the 150-log cache |

All three use `--gt 30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json` and `--ego 30_DATA/av2_trk_v02/ego/av2_c1_ego10hz_v01.json.gz`. The builder version and the `--meta` / scene-map details are the lead's.
