"""pod_owndet_profile_v01 (own-detector job, D18 v03 "Training budget after the pilot" 1, 2 Nov 2026): profile the training step.

Builds the model, CBGS train dataset and loader from a dumped training config (pod_owndet_cfg_v02.py), runs the same step as mmcv's
EpochBasedRunner + OptimizerHook (model.train_step -> zero_grad -> backward -> grad clip 35 -> AdamW step), and reports:
  - wall time per iteration (CUDA-synchronised) and the share spent waiting for data;
  - section times (CUDA-synchronised wrappers): voxelisation + backbone/neck (extract_pts_feat), head forward, head loss, of which
    get_targets (target generation), and backward + optimizer step;
  - a torch.profiler table (CPU and CUDA) over iterations 6-15, sorted by self CPU time and by CUDA time, and a stack-grouped table;
  - whether mmcv's compiled ops are CUDA builds (compiling CUDA version) and the device of the voxeliser's input.
Nothing is saved from the model. Usage (LT3D venv, LT3D root):
  python pod_owndet_profile_v01.py --lt3d <root> --cfg <cfg.py> --iters 40 --workers W --out <dir>
"""
import argparse
import json
import os
import sys
import time


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--iters", type=int, default=40)
    ap.add_argument("--workers", type=int, default=None)
    ap.add_argument("--out", required=True)
    ap.add_argument("--profile", action="store_true")
    a = ap.parse_args()
    sys.path.insert(0, a.lt3d)
    os.chdir(a.lt3d)
    os.makedirs(a.out, exist_ok=True)
    import numpy as np
    import torch
    from mmcv import Config
    from mmcv.parallel import MMDataParallel
    from mmcv.runner import build_optimizer
    from mmdet3d.datasets import build_dataloader, build_dataset
    from mmdet3d.models import build_model
    rec = {"cfg": a.cfg, "torch": torch.__version__, "cuda": torch.version.cuda, "omp_threads_env": os.environ.get("OMP_NUM_THREADS"),
           "torch_num_threads": torch.get_num_threads()}
    try:
        from mmcv.ops import get_compiler_version, get_compiling_cuda_version
        rec["mmcv_ops_compiling_cuda"] = get_compiling_cuda_version()
        rec["mmcv_ops_compiler"] = get_compiler_version()
    except Exception as e:  # noqa: BLE001
        rec["mmcv_ops_error"] = repr(e)
    cfg = Config.fromfile(a.cfg)
    B = int(cfg.data.samples_per_gpu)
    W = a.workers if a.workers is not None else int(cfg.data.workers_per_gpu)
    rec.update(batch=B, workers=W)
    torch.manual_seed(0)
    np.random.seed(0)
    ds = build_dataset(cfg.data.train)
    loader = build_dataloader(ds, B, W, num_gpus=1, dist=False, seed=0, shuffle=True)
    model = build_model(cfg.model, train_cfg=cfg.get("train_cfg"), test_cfg=cfg.get("test_cfg"))
    model.init_weights()
    model = MMDataParallel(model.cuda(), device_ids=[0])
    model.train()
    opt = build_optimizer(model, cfg.optimizer)
    m = model.module
    head = m.pts_bbox_head
    times = {"extract_pts_feat": [], "head_forward": [], "head_loss": [], "get_targets": [], "voxelize": []}

    def timed(name, fn):
        def wrap(*args, **kw):
            torch.cuda.synchronize()
            t = time.perf_counter()
            r = fn(*args, **kw)
            torch.cuda.synchronize()
            times[name].append(time.perf_counter() - t)
            return r
        return wrap
    vox_dev = []
    orig_vox = m.voxelize

    def vox(points):
        vox_dev.append(str(points[0].device))
        return orig_vox(points)
    m.voxelize = timed("voxelize", vox)
    m.extract_pts_feat = timed("extract_pts_feat", m.extract_pts_feat)
    head.forward = timed("head_forward", head.forward)
    head.loss = timed("head_loss", head.loss)
    head.get_targets = timed("get_targets", head.get_targets)
    it_times, data_waits, bwd_times = [], [], []
    prof = None
    if a.profile:
        prof = torch.profiler.profile(activities=[torch.profiler.ProfilerActivity.CPU, torch.profiler.ProfilerActivity.CUDA],
                                      schedule=torch.profiler.schedule(wait=5, warmup=1, active=10, repeat=1), with_stack=True)
        prof.__enter__()
    t_end = time.perf_counter()
    for i, data in enumerate(loader):
        t_data = time.perf_counter()
        data_waits.append(t_data - t_end)
        out = model.train_step(data, None)
        torch.cuda.synchronize()
        t_b = time.perf_counter()
        opt.zero_grad()
        out["loss"].backward()
        torch.nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], max_norm=35, norm_type=2)
        opt.step()
        torch.cuda.synchronize()
        t_end = time.perf_counter()
        bwd_times.append(t_end - t_b)
        it_times.append(t_end - t_data + data_waits[-1])
        if prof is not None:
            prof.step()
        if i + 1 >= a.iters:
            break
    if prof is not None:
        prof.__exit__(None, None, None)
        ka = prof.key_averages()
        open(os.path.join(a.out, "profile_self_cpu.txt"), "w").write(ka.table(sort_by="self_cpu_time_total", row_limit=40))
        open(os.path.join(a.out, "profile_cuda.txt"), "w").write(ka.table(sort_by="cuda_time_total", row_limit=30))
        open(os.path.join(a.out, "profile_stack.txt"), "w").write(prof.key_averages(group_by_stack_n=6).table(sort_by="self_cpu_time_total", row_limit=25))
        rec["profiled_iterations"] = "6-15"
        rec["cuda_time_total_s"] = sum(e.self_cuda_time_total for e in ka) / 1e6
        rec["cpu_time_total_s"] = sum(e.self_cpu_time_total for e in ka) / 1e6
    skip = 5
    mean = lambda v: float(np.mean(v[skip:])) if len(v) > skip else float(np.mean(v))  # noqa: E731
    rec.update(iters=len(it_times), s_per_it=mean(it_times), data_wait_s=mean(data_waits), backward_step_s=mean(bwd_times),
               samples_per_s=B / mean(it_times), voxelizer_input_device=sorted(set(vox_dev)),
               sections_s={k: mean(v) for k, v in times.items() if v}, peak_memory_gb=torch.cuda.max_memory_allocated() / 1e9,
               train_dataset_len=len(ds))
    json.dump(rec, open(os.path.join(a.out, "profile_summary.json"), "w"), indent=1)
    print(json.dumps(rec), flush=True)
    print("PROFILE DONE", flush=True)


if __name__ == "__main__":
    main()
