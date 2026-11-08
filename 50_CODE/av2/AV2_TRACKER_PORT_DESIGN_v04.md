# AV2 tracker port: design v04, the 375 confirmation logs with the own detector (5 Nov 2026)

v01 to v03 are kept unchanged. v04 is a new design for one step: run T1 (CANMOT `paper/local/canmot/sc`), T3 (Poly-MOT `paper/baseline/poly_mot`) and AB3DMOT (label `tab`) on the 375 C1 confirmation logs of Argoverse 2 (AV2), with our own CenterPoint's detections. It prepares what stage A needs and computes the Rule 0 tracker metrics. It stops before stage A.

**Status.** Written before any fetch, tool or run of this step. The only facts used come from file listings, file sizes, hashes and these documents:
- `AV2_TRACKER_PORT_DESIGN_v03.md` (sections 1–13);
- `60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v02.md` and `AV2_AB3DMOT_NOTE_v01.md`;
- `60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md`;
- `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07b_DRAFT.md` §1.1, §1.2, §8.4, §8.5;
- the owndet summaries (`30_DATA/av2_det_owncp_v01/*/…_dets_v01.json`, `env/av2_infos_*_summary.json`, `env/MANIFEST_train_confirm_v06_maps.csv`);
- the split file `50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json`.

No ground-truth content was opened.

**Outcome boundary.** This is v03 §9 unchanged, with D16 Choice 13 and plan §1.5. This step computes only the following on AV2:
- tracker outputs;
- the trackers' own 2 s propagation of mean and covariance;
- logged ego poses;
- the prepared ground-truth table (Rule 0: ground truth at the same sweep);
- tracking metrics (HOTA, AMOTA, MOTA, IDS) from the tools.

It computes no residual, projected error, exceedance, coverage, margin, NEES/ANEES, quantile, multiplier, minADE/minFDE or risk number. It runs no stage A, no stage B, no `k8_items` and no `c1_*` entry point.

## 1. The 375-log set

- **Held-out train part (225).** `AV2_TRAIN_SPLIT_v01.json` (SHA-256 3771664f…) records the rule: "sorted(700) → `default_rng(20261102).permutation`; first 225 held out". Its key `held_out_225` holds those 225 ids in permutation order. The tool takes them as given, checks that there are 225 distinct ids, none of them among `train_475`, and sorts them.
- **Validation part (150).** The 150 log folders of `30_DATA/av2_val` (directories only; the manifest CSV beside them is ignored).
- **List file.** `30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` is written by `av2_c1_logs_v01.py`:
  - `logs` (375, sorted);
  - `held_out_225` (sorted) and `val_150` (sorted);
  - the split file's path and SHA-256;
  - the rule.

  The tool checks that the two parts are disjoint and contain 375 ids in all. The file's SHA-256 is written to `C1_LOGS_375_v01.sha256` and to the note.
- **Part of a log.** `val150` if the log resolves to `30_DATA/av2_val`, `held225` if it resolves to `30_DATA/av2_train225` (§2).

## 2. Data-root rule (`av2_common_v02.log_dir`)

`log_dir(log)` returns `30_DATA/av2_val/<log>` or `30_DATA/av2_train225/<log>`. Exactly one of the two must be an existing directory; if none or both exist, it raises. Every v02 tool reads per-log files only through `log_dir`:
- `annotations.feather`;
- `city_SE3_egovehicle.feather`;
- the sweep list.

## 3. Sweep-list rule (`av2_common_v02.sweep_timestamps`)

- If `<log_dir>/sensors/lidar/` exists and holds `.feather` files, the sweep list is v01's: the sorted integer stems of those files. This applies to the 150 validation logs, whose lidar is on disk.
- Otherwise the list comes from `<log_dir>/lidar_keys_v01.csv`, a recorded bucket listing (`key,size,etag`, one row per lidar object, sorted by key) written by `av2_fetch_v05`. Each key must:
  - start with `datasets/av2/sensor/`;
  - contain `/<log>/sensors/lidar/`;
  - end with `.feather`, with an all-digit stem;
  - have a size > 0.

  Stems must be unique, and the list must be non-empty. Any violation raises.
- If there is neither a lidar folder with `.feather` files nor a listing, it raises.
- `frame_timestamps(log) = sweep_timestamps(log)[::5]`, as in v01.

No lidar point cloud is downloaded for the 225 train logs (disk: about 28 GB free; the 225 logs' lidar is 35.6 GB per the pod manifest).

## 4. Fetch (`av2_fetch_v05.py`)

- **Source.** Only the public bucket `https://argoverse.s3.amazonaws.com`, prefix `datasets/av2/sensor/train/<log>/`. Unsigned ListObjectsV2 calls and plain HTTPS GETs, with the standard library only.
- **Logs.** An explicit log list, `--logs-file`: the `held_out_225` key of `C1_LOGS_375_v01.json`.
- **Downloaded per log:**
  - `annotations.feather`;
  - `city_SE3_egovehicle.feather`;
  - `calibration/*` (2 files).
- **Listed per log, not downloaded:** `sensors/lidar/` (key, size, ETag), written as `lidar_keys_v01.csv` in the log folder. Cameras, maps and lidar contents are never fetched.
- **Integrity.**
  - Every fetched file's size must equal the listing's.
  - Where the ETag is a plain MD5 (32 hex characters, no `-`), the file's MD5 must equal it.
  - A failed check deletes the partial file and reports the failure.
  - The run is resumable: a file of the right size and MD5 is kept.
- **Manifest.** `30_DATA/av2_train225/MANIFEST_av2_train225_meta_v05.csv` (key, size, etag, md5_ok, status) plus a summary JSON (counts, bytes, the hash of the manifest).
- **Untrusted data.** Downloads go only into `30_DATA/av2_train225/<log>/`. Nothing there is executed or imported. Every Python that reads them runs with `-I -B` from a working directory outside the data folders. Keys containing `..` or a backslash are refused.

## 5. Own-detector inputs

- `DET_PATHS["owncp"]` is the two npz files, in this order:
  - `30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_dets_v01.npz` (SHA-256 3ce5e372…);
  - `30_DATA/av2_det_owncp_v01/held225/av2held225_owncp_centerpoint_dets_v01.npz` (SHA-256 3b06178f…).

  The expected hashes are taken from `SHA256SUMS.txt` (e8dad0a8…), stored as `DET_SHA256` and checked by the adapter before use.
- `DET_HAS_VELO["owncp"] = True`: the npz has `vx` and `vy`, the same columns as LT3D's.
- `det_sources(name)` returns the tuple of source files (one for `lt3d` and `voxelnext`).
- **Velocity convention, probe P-c (outcome-free; detector against detector, no ground truth).** On the 150 validation logs, take own and LT3D detections of the same frame and AV2 category, both with score > 0.5, and mutually nearest within 1 m in the ego frame. The probe reports:
  - the median of |v_own − v_lt3d|;
  - the median cosine of the two velocity vectors where both speeds exceed 1 m/s.

  If the own export used another frame or sign, the cosine would be far from 1. If it is not near 1, the step stops and reports. This probe is a check, not a gate on any outcome.

## 6. Tools (new versioned files only; nothing existing is edited)

Every constant and every computation is v01's (v04's for AB3DMOT, v03's for the metrics). Only the following change.

| New file | From | What changes |
|---|---|---|
| `av2_common_v02.py` | `av2_common_v01` | + `AV2_TRAIN225`, `log_dir`, `log_part`, the sweep-list rule (§3), `listing_timestamps`, `DET_PATHS["owncp"]`, `DET_SHA256`, `DET_HAS_VELO["owncp"]`, `det_sources`, `read_logs_file`, `val_logs`. Everything of v01 is kept verbatim |
| `av2_fetch_v05.py` | `av2_fetch_v04` | §4: train split, explicit list, metadata and lidar listing only, MD5 check |
| `av2_c1_logs_v01.py` | new | §1 |
| `av2_gt_prep_v02.py` | `av2_gt_prep_v01` | reads through `log_dir` / `sweep_timestamps` v02; `--logs` or `--logs-file`. Without a list it is v01 (all validation logs; asserts 150 and 4,806). The note string is v01's when every log is a validation log, otherwise a v02 note naming both roots. Nothing else in the output differs |
| `av2_ego_prep_v02.py` | `av2_ego_prep_v01` | `log_dir`, `sweep_timestamps` v02; the check `checked == 4806` becomes `checked ==` the number of samples in `--gt` (v01's 4,806 when that is the 150-log table) |
| `av2_tracker_input_v02.py` | `av2_tracker_input_v01` | several source npz files (each streamed and masked exactly as v01; kept rows concatenated, then v01's sort); the log list from `--logs-file` (default: v01's 150); poses through `log_dir`; frames from `frame_timestamps` v02; per-source stats beside v01's (summed); `meta.adapter` is `av2_tracker_input_v02`; `--workers 8` for the run (v01 ran 4) |
| `av2_track_v02.py` | `av2_track_v01` | `--detector owncp`; dataset tag (§9); **per-log checkpoints** (§7). The tracking loop, record criteria and export lines are v01's |
| `av2_ab3dmot_v05.py` | `av2_ab3dmot_v04` | `--detector {lt3d, owncp}`; the log list from `--logs-file` (default: the 150 validation logs); poses through `log_dir`; loads only its worker's logs (memory; the per-log rows and their order are unchanged); per-log checkpoints, including `KalmanBoxTracker.count` (§7); dataset tag (§9) |
| `av2_horizon_prep_v02.py` | `av2_horizon_prep_v01` | an export counts as AV2 when its dataset tag starts with `av2` (v01: equals `av2_sensor_val`), so both guards keep holding for the v02 tag. The propagation is v01's |
| `av2_track_metrics_v04.py` | `av2_track_metrics_v03` | `--logs-file` / `--logs` restricts the GT samples and the exported records to those logs (per-part metrics from one GT file). Without them it is v03 |
| `av2_hota_v04.py` | `av2_hota_v03` | the same log restriction; label text names the GT file. Without it it is v03 |
| `av2_c1_frame_check_v01.py` | new | §11 |
| `test_av2_port_v04_equiv_v01.py` | new | §10 comparisons |
| `run_av2_c1_*.sh` | new | drivers (§12) |

`av2_feather_v01.py`, `x1_export_v06.py`, `fast_convex_v01.py`, the CANMOT and LT3D trees and the shims are used unchanged.

## 7. Per-log checkpoints (resume, never restart)

- **`av2_track_v02`.** CANMOT's `Tracker.reset()` runs at every log's first frame and clears all trajectories and `id_seed`. A log's export lines therefore do not depend on earlier logs; its `seq_id` and `index` come from the fixed subset file. After each log the runner writes into `<out>/parts/`:
  - `<log>.jsonl.gz`, that log's export lines;
  - `<log>.state.json`, written atomically last: per-frame records, visited frames, K1 violations, counts, minimum eigenvalues, class counts, tokens, line count, and the SHA-256 of the uncompressed lines.

  On a restart, a log whose state file matches (harness version, subset SHA-256, experiment, detector, `has_velo`, fast-convex flag) and whose part decompresses to the recorded SHA-256 is reused; the others run again. At the end the runner assembles `x1_tracks.jsonl.gz` (the parts' lines in selection order), `x1_per_frame.json` and `x1_export_record.json` from the states, with v01's code, then removes `parts/`. The record lists the reused logs.
- **`av2_ab3dmot_v05`.** `AB3DMOT.reset()` runs per log. The only cross-log state is the class counter `KalmanBoxTracker.count`, which numbers the tracks. After each log the driver writes:
  - the log's det, kf and horizon lines;
  - its per-frame records and stat deltas;
  - the counter after the log.

  On a restart, the longest prefix of the worker's logs with valid checkpoints is reused, and the counter is restored from the last of them. The outputs are then assembled as v04 writes them.
- **Other steps** (adapter about 5 min, GT prep about 10 min, ego, propagation, metrics) are units of a queue. A unit whose output exists and verifies is skipped; a broken unit is rerun.

## 8. Runs (outputs under `30_DATA/av2_trk_v02/`; no existing file is touched)

| Step | Tool, env | Output |
|---|---|---|
| fetch | `av2_fetch_v05`, canmot310 `-I` | `30_DATA/av2_train225/` |
| list | `av2_c1_logs_v01` | `C1_LOGS_375_v01.json` |
| tracker input | `av2_tracker_input_v02 --detector owncp --logs-file … --workers 8` | `input/owncp/` |
| GT | `av2_gt_prep_v02 --logs-file C1_LOGS_375_v01.json` | `gt/av2_c1_gt375_v01.json` (the one prepared file, plan §8.4) |
| T1 | `av2_track_v02 --experiment paper/local/canmot/sc --detector owncp --fast-convex`, 8 subsets | `export/t1_owncp/worker0…7/` |
| T3 | the same with `paper/baseline/poly_mot` | `export/t3_owncp/worker0…7/` |
| AB3DMOT (`tab`) | `av2_ab3dmot_v05 --detector owncp --fast --n-workers 6`, ab3dmot310 | `export_tab_owncp/ab3dmot_{det,kf}/worker0…5/`, `horizon8_ab3dmot_kf_worker*.jsonl.gz` |
| ego | `av2_ego_prep_v02 --gt gt/av2_c1_gt375_v01.json` | `ego/av2_c1_ego10hz_v01.json.gz` |
| 2 s propagation | `av2_horizon_prep_v02 --propagate-only --allow-av2-propagation` (Choice 13), T1 and T3; AB3DMOT's own (its worker files merged in worker order, as queue 7 did) | `horizon/horizon8_{t1,t3,tab}_owncp.jsonl.gz` |
| Rule 0 metrics | `av2_track_metrics_v04` (car, pedestrian, bicycle), `av2_hota_v04` (seven classes) | `60_RESULTS/av2_trk/c1_375/{metrics,hota}/` |

- No tracker parameter is re-tuned. The trackers keep their nuScenes parameters, and AB3DMOT keeps LT3D's defaults.
- **Concurrency.** At most 3 of these processes at a time (`nproc` = 8; the lead and code v08's author share the CPU). Single-threaded BLAS and numba. Memory-heavy steps (GT load, metrics, HOTA) run at most 2 at a time.
- **Process handling.** Long jobs run detached (`nohup`, background) with per-log checkpoints. Only processes started here are killed, by PID.
- **Disk.** `df -h /c` is checked before each phase. Below 8 GB free, everything stops and is reported.

## 9. Dataset tag

The export record's `dataset` is:
- `av2_sensor_val` when every log of the receipt (T1/T3) or of the log list (AB3DMOT) is a validation log, as in v01, so the equivalence tests compare like with like;
- `av2_sensor_val_train` otherwise.

The C1 guard normalises any tag starting with `av2` to `av2`. `av2_horizon_prep_v02` treats both tags as AV2 (§6). Do not run `av2_horizon_prep_v01` on the v02 exports, because its guard only knows `av2_sensor_val`.

## 10. Equivalence tests (150 validation logs, public LT3D detections)

Each new tool must reproduce its v01 (v04, v03) output. Test outputs go under the scratchpad S, never into the workspace, and are deleted after the comparison. Ground-truth test outputs are deleted immediately, and each deletion is recorded.

| Test | Pass criterion |
|---|---|
| `av2_common_v02` | for all 150 validation logs: `log_dir` = `av2_val/<log>`, `sweep_timestamps` and `frame_timestamps` equal v01's; `DET_PATHS` lt3d/voxelnext equal v01's |
| `av2_gt_prep_v02` (no list, and `--logs` = the 150) | SHA-256 of each output = 9642db5b… (the existing `av2_val_gt_v01.json`, hashed, never opened); then delete |
| `av2_ego_prep_v02` (`--gt` the v01 GT file) | SHA-256 of the decompressed output = that of `av2_cache_stageA_v01/av2_ego10hz_v01.json.gz` decompressed (gzip headers carry a time stamp) |
| `av2_tracker_input_v02 --detector lt3d --workers 4` | `first_tokens.json` byte-identical; each `dets_worker*.json` byte-identical after the single documented substitution `"adapter": "av2_tracker_input_v02"` → `…_v01` in its meta; receipt equal on every non-path, non-time key |
| `av2_track_v02` T1 worker 3 and T3 worker 1 (v01 receipt, `--fast-convex`), T1 interrupted on purpose and resumed | decompressed `x1_tracks.jsonl.gz` SHA-256 and `x1_per_frame.json` bytes equal v01's; record criteria and stats equal (except times, paths, memory) |
| `av2_ab3dmot_v05 --detector lt3d --fast --worker 1 --n-workers 6`, interrupted and resumed | decompressed det, kf and horizon files and `x1_per_frame.json` equal `export_ab3dmot_v04w6` worker 1's |
| `av2_horizon_prep_v02` on the v01 T1 and T3 LT3D worker 0 | decompressed output = the first n lines of `horizon8_{t1,t3}_lt3d.jsonl.gz` (n = worker 0's record count; v01 wrote the workers in order), and no further line |
| `av2_track_metrics_v04` and `av2_hota_v04` with `--logs` = the 150, on the v01 T3 VoxelNeXt exports and the v01 GT | every per-class value equal to `60_RESULTS/av2_trk/metrics/AV2_metrics_t3_voxelnext.json` / `hota/AV2_HOTA_t3_voxelnext.json` |

`av2_fetch_v05` has no v01 output to reproduce. It is checked by sizes and MD5s, and its lidar listings are checked against the pod's fetch manifest (§11).

## 11. Frame-timestamp check (`av2_c1_frame_check_v01`)

For each of the 225 train logs, `frame_timestamps(log)` (= `sweeps[::5]` from the listing) must equal the sorted unique `timestamp_ns` of the own detector's held-225 npz for that log. The pod's infos used `sample_rate` 5 and gave 32–40 frames per log and 7,232 frames. The same is checked for the 150 validation logs against the val-150 npz (4,806 frames).

The listing's lidar keys (key, size, ETag) must also equal those of `env/MANIFEST_train_confirm_v06_maps.csv`, the pod's own fetch. Any mismatch is reported per log, not repaired.

## 12. Ground-truth files and the quarantine list

`30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt` lists, as path and SHA-256, every prepared ground-truth file this step writes or uses for the Rule 0 metrics:
- `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json`;
- `30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_gt_v01.feather` (a9d85a54…);
- `30_DATA/av2_det_owncp_v01/held225/av2held225_owncp_centerpoint_gt_v01.feather` (8cb86154…).

It also names, for the lead, the files the plan already handles: `av2_trk_v01/gt/av2_val_gt_v01.json`, named by the 150-log manifests, and the LT3D detection-evaluation GT feather, already on the extra list. The public `annotations.feather` files of `av2_val` and `av2_train225` stay outside the quarantine, as plan §8.4 concedes. Test GT outputs are never kept.

## 13. Stop

After the runs, the metrics, the list and the note, this step stops. It runs no `av2_cache_stageA_*` and no counts. The lead supplies the builder version and the `--meta` / scene-map details once code v08 is verified.
