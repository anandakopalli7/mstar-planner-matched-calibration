# Own CenterPoint on AV2: profiling and the configuration chosen (pilot v02, 4 Nov 2026)

**Context.** D18 v03, "Training budget after the pilot", step 1: profile the CPU-bound step and fix what can be fixed without changing LT3D's model or CBGS sampler.

**Run.** Pod `xbiqlg7n9x0iiy`, 2 Nov 2026 18:18–18:37 UTC (13:18–13:37 EST): RTX 4090, AMD Ryzen 9 7950X, a 32-CPU quota and a 61 GB memory limit.

**Data.**
- Profiling subset: the first 40 logs of `train_475` (`pod_owndet_prep_v02.py`, part `prof40`), with its own GT database.
- LT3D's `CBGSDataset` divides by zero when a class is absent, and it was in this subset. So the profiles use the wrapper's inner AV2Dataset, with the same pipeline, model and step (`pod_owndet_profile_v02.py --no-cbgs`).
- The full train fetch ran at the same time.
- Each run: 40 iterations; means are over iterations 6–40. Times are CUDA-synchronised.

## Throughput per configuration

| Run | B | Loader workers | OMP/MKL threads | s/it | Samples/s | Data wait (s/it) | get_targets (s/it) | Forward: features / head (s) | Backward + step (s) | Peak memory |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 (torch profiler on; iterations 6–15 profiled) | 4 | 11 | 1 | 6.29 | 0.64 | 4.30 | 1.37 | 0.146 / 0.097 | 0.370 | 10.9 GB |
| **P2** | **4** | **11** | **4** | **1.029** | **3.89** | 0.008 | 0.504 | 0.050 / 0.097 | 0.363 | 10.9 GB |
| P3 (lr × 2) | 8 | 11 | 4 | 2.187 | 3.66 | 0.020 | 1.036 | 0.103 / 0.186 | 0.830 | 21.2 GB |
| P4 | 4 | 6 | 4 | 1.033 | 3.87 | 0.008 | 0.505 | 0.050 / 0.097 | 0.366 | 10.9 GB |

For comparison, the pilot v01 (other host, 13.6-CPU quota, OMP 1, CBGS, B = 4) ran at 1.649 s/it.

## Findings

**mmcv's ops are CUDA builds and run on CUDA.**
- `get_compiling_cuda_version` = 11.1 (GCC 7.3).
- The voxeliser's input is on `cuda:0`.
- Voxelisation takes 0.004 s/it; the backbone, neck and head forward take 0.15 s together.
- No CPU fallback was found.

**The CPU-bound part is `CenterHead.get_targets`.** It takes about 0.50 s of the 1.03 s step at B = 4, about half. It is a Python per-object loop.
- In 10 profiled steps: 684,676 `cudaLaunchKernel` calls, 405,742 `aten::select` and 176,596 `aten::item` host syncs.
- CUDA time was 11.4 s against 36.8 s of CPU time (profiler overhead included).
- Its cost grows with the number of objects, so batch 8 gives no gain: 3.66 against 3.89 samples/s.

**Loader workers and threads.** 6 or 11 workers make no difference. The CPU quota and the faster single-thread CPU of this host, with the profiler off, explain the gain over the pilot (1.65 → 1.03 s/it); the thread setting is not separated from those.

## Chosen

**P2: B = 4, 11 loader workers, OMP/MKL threads 4, lr = 1e-4 × 4/8 = 5e-5**, cyclic as shipped.
- The CBGS sampler is kept. No code change to `get_targets`.
- Expected pace about 1.03 s/it. Batches drawn by CBGS may hold more objects, so the actual pace is checked in the first 1,000 iterations of the full run.
- Settings and epochs: `OWN_DETECTOR_DESIGN_ADDENDUM_A_v01.md`.
