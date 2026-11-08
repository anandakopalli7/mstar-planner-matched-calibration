# Own CenterPoint on AV2: design addendum B (v01, 4 Nov 2026), budget-capped resume from iteration 1,000

**Status.** Written before the resume. It adds to `OWN_DETECTOR_DESIGN_v01.md` (`cf09bb11…`) and to `ADDENDUM_A_v01.md` (`41ba8fe3…`), both unchanged.

**Source.** The lead's decision of 4 Nov 2026, a budget rule with no AV2 outcome involved.

**State.** Training stopped at the iteration-1,000 checkpoint, after a pace check on an AMD EPYC 7443 host (1.41 s/it) projected a total of about $35.9. The saved files are in `30_DATA/av2_det_owncp_v01/train_progress/`:

| File | SHA-256 |
|---|---|
| `iter_1000.pth` | `edbc3dc8…` |
| config `cfg_train_i57838_b4.py` | `4e5fc6c8…` |
| infos and GT-database archive | `ada2146d…` |

Spend since 2 Nov before the resume: about **$13.17**.

## B1. Host selection

- Each new pod is checked at once: CPU model from `/proc/cpuinfo`, and CPU quota from cgroup `cpu.max` or `cfs_quota`.
- **Accepted:** a fast single-thread CPU with a quota of at least 8. That means a Ryzen 7950X/9950X-class part, or an EPYC 9xx4/9xx5 (Genoa/Turin) at high clock.
- **Rejected at once:** any other host, terminated immediately.
- Up to 8 creations, each logged in `SPEND_LOG_OWNDET_v01.md`. If none is accepted, the best host seen is taken under the same cap rule. "Best" means a fast CPU class first, then the higher quota.

## B2. Resume

- Training continues from `iter_1000.pth` (`--resume-from`, which restores optimizer state and iteration count). Every other setting is as in addendum A: B 4, lr 5e-5, CBGS, cyclic schedule over `max_iters`, 11 loader workers, OMP 4.
- The work directory is `/root/work/owndet/train_b4` on the pod volume. Checkpoints are written every 1,000 iterations and the last 3 kept; the highest checkpoint is always resumed.
- The infos and GT database are restored from the archive, not rebuilt (the archive's hash is checked). The 475 training logs are fetched again.

## B3. Cap rule (speed check over the first 200 iterations after resuming)

**Projection.** P(N) = spent since 2 Nov + pod cost so far + (N − 1,000) × (s/it) × price + 3.5 h × price. The 3.5 h cover the data swap, the held-out and val infos, inference, export, AP and copy-back.

**Rule.**
- If P(57,838) ≤ $34, all 2 epochs run.
- Otherwise max_iters = the largest N with P(N) ≤ $34, but at least **50,500** (1.75 epochs).

**Changing max_iters.** Training is stopped by PID, a new config is written with max_iters = N, and training resumes from the highest checkpoint. mmcv's cyclic schedule then spans N iterations; the change in learning rate at the resume point is negligible.

The chosen N, the measured s/it and the projection are added below before continuing.

## B4. Real-time saving

As addendum A2:
- the laptop loop (`owndet_progress_loop_v02.sh`, reading the pod connection, work directory and final iteration from `80_LOGS/runpod/owndet_pod_conn_v02.txt`) copies the latest checkpoint and log every 2.5 h, verifies them by SHA-256, and appends a line to the spend log;
- every pod job runs under `setsid nohup`.

## B5. After training

As addendum A3: inference with `iter_N.pth` on the 225 held-out and 150 val logs, AP on both parts, copy-back with verified SHA256SUMS, termination, and the note.

## B6. Recorded at the speed check (4 Nov 2026, 12:19 EST)

**Host.** Try 2 of the search: pod `8peoqsmqm9exjw`, AMD Ryzen 9 7950X, CPU quota 13.6, RTX 4090 at $0.89/h. Try 1 was a Xeon Gold 6342 with quota 7.65, rejected at once.

**Resume.** Training resumed from `iter_1000.pth` at 17:14:24 UTC (log: "resumed from epoch: 1, iter 999"; lr 5.207e-5, as at the stop).

**Pace.** Iterations 1,001–1,200 (log blocks ending at 1,050, 1,100, 1,150 and 1,200): 1.032, 1.068, 1.066 and 1.061 s/it, mean **1.057 s/it**, data time 0.010 s/it.

**Projection.** P(57,838) = $13.18 spent before this pod + $0.34 for this pod so far + 56,638 × 1.057 s × $0.89/h ($14.80, 16.6 h) + 3.5 h × $0.89 ($3.12) = **$31.44 ≤ $34**.

**Decision under B3:** run all **2 epochs, max_iters = 57,838**, unchanged.
