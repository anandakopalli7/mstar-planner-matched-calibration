# QCNet AV2 arm: design addendum A, as run (v01, 2 Nov 2026, 09:10 EST)

This file records how addendum A (`QCNET_AV2_ARM_DESIGN_ADDENDUM_A_v01.md`, SHA-256 `8b249c56…e768`, unchanged) was executed. It was written after the run, from the recovered pod outputs (`30_DATA/qcnet_av2_v02/`, 38/38 SHA-256 OK on the laptop). Every rule of A1–A3 ran as written. The departures, all in execution and none in method, are listed below.

## Execution as it happened (EST)

| Time | Event |
|---|---|
| 06:15–06:18 | Four create attempts found no instance. Pod `lq459c84r42q2k` (`claude-programmeA-qcnet2`) was created: RTX 4090, $0.89/h, SECURE. |
| 06:24–06:27 | `pod_qcnet2_master_v01.sh` stage 1: 750 files fetched without lidar, LT3D and QCNet environments built, checkpoint SHA-256 = `b9f852ec…` as in v01. |
| ≈ 06:30 | Path check (released rules, first 10 logs): **identical** to v01 in rows, track ids, names and every value (183,837 rows, max difference 0.0). |
| — | Master v01's QCNet GT step failed on its first log (see 2 below). |
| ≈ 06:31 | GT step started by hand: `run_qgt_manual_v01.sh` with `qcnet_av2_infer_v03.py` and `qcnet_frame_test_v05.py`. |
| 06:32 | GT run and frame test done. |
| ≈ 06:37 | Matched-rule equivalence: native = shim on 3 logs (**identical**). |
| ≈ 06:37–07:06 | Matched AB3DMOT run on 150 logs (shim; 15,451 CPU-s). |
| 07:06:59 | Master v01 stopped by its own rule (`Q2_MASTER_STOP`): its GT branch had failed. |
| 07:07:13 | `pod_qcnet2_master_v02.sh` started. It skipped every finished step (each step log held its DONE line), ran QCNet on the matched histories (436 s), packed the outputs and wrote SHA256SUMS. It ended at **07:15:23** (`Q2_MASTER_DONE`). The command that launched master v02 is not in the session record: the laptop lost power at about 07:05. |
| 07:05–08:51 | The laptop was without power; the pod sat idle. |
| 08:57–08:58 | The lead copied `/workspace/work/deliver2` to `30_DATA/qcnet_av2_v02/`, verified 38 sums and terminated the pod. |
| 09:00 | The sums were re-verified locally (38/38 OK). The 40 code files hashed on the pod at the end equal the copies in `50_CODE/qcnet/pod/`. That includes `run_qgt_manual_v01.sh`, which was written on the pod and restored locally with the same SHA-256 (`1764b5fd…`). |

## Departures, each in execution only

1. **Pod volume 40 GB, not 150 GB.** No 150 GB instance was available (spend log v02). The rerun needed under 5 GB on the volume.
2. **QCNet scene transport.** `qcnet_av2_infer_v02.py` built scenes in worker processes and sent torch tensors back. Torch shares tensors through file descriptors, and the first log failed with "Too many open files" (limit 1024).
   - `qcnet_av2_infer_v03.py` sends NumPy dictionaries and rebuilds the HeteroData in the parent. Nothing else changed.
   - `qcnet_frame_test_v05.py` (= v04 on infer v03) and `pod_qcnet2_master_v02.sh` (= v01 with those two scripts) followed from this.
3. **`pod_lt3d_setup_v05.sh`** = v04 with `MAX_JOBS=8`, because the pod has 41 GB of memory and 17 CPUs.
4. **Top-500 cap.** It binds in 256 sweeps of the matched run. It was kept as the addendum states; the sweeps are counted.
5. **Score floor ≥ 0.1 versus the released > 0.1.** The two rules give the same 2,785,808 three-class inputs, because no score equals 0.1 exactly.

No job was stopped on purpose in this rerun.
