"""pod_owndet_cfg_v02 (own-detector job, 2 Nov 2026) = v01 + the val and test info files pointed at our av2_infos_val150.pkl (v01 left
the shipped path, which does not exist on the pod, and tools/train.py builds the val dataset). No training setting changes.
pod_owndet_cfg_v01: the training config = the public checkpoint's shipped config with the overrides
of 50_CODE/owndet/OWN_DETECTOR_DESIGN_v01.md section 2-3, dumped with mmcv (resolved values) and summarised.

Overrides: data paths; train infos (475 logs); GT-database infos (from the 475 logs); samples_per_gpu = B; workers_per_gpu;
lr = lr_cfg * B / B_ref with B_ref = samples_per_gpu(shipped) * 8; max_epochs (or an iteration-based runner for the pilot);
evaluation interval beyond the run; checkpoint every epoch; work_dir. Everything else is the shipped file.
Usage (LT3D venv, LT3D root): python pod_owndet_cfg_v01.py --lt3d <root> --public-cfg <shipped .py> --infos-dir <abs> --out-rel <rel>
        --data-root <.../Sensor/> --batch B --workers W --epochs E | --pilot-iters N --work-dir <dir> --out <cfg.py>
"""
import argparse
import json
import os
import sys


def set_db(obj, info_path, data_root):
    """Point every db_sampler in a (nested) pipeline config at our GT database."""
    if isinstance(obj, dict):
        if obj.get("type") == "ObjectSample" and "db_sampler" in obj:
            obj["db_sampler"]["info_path"] = info_path
            obj["db_sampler"]["data_root"] = data_root
        for v in obj.values():
            set_db(v, info_path, data_root)
    elif isinstance(obj, list):
        for v in obj:
            set_db(v, info_path, data_root)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--public-cfg", dest="public_cfg", required=True)
    ap.add_argument("--infos-dir", dest="infos_dir", required=True)
    ap.add_argument("--data-root", dest="data_root", required=True)
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--workers", type=int, required=True)
    ap.add_argument("--epochs", type=int, default=0)
    ap.add_argument("--pilot-iters", dest="pilot_iters", type=int, default=0)
    ap.add_argument("--work-dir", dest="work_dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset-len", dest="dataset_len", action="store_true", help="also build the train dataset and report its length")
    a = ap.parse_args()
    sys.path.insert(0, a.lt3d)
    os.chdir(a.lt3d)
    from mmcv import Config
    cfg = Config.fromfile(a.public_cfg)
    b_cfg = int(cfg.data.samples_per_gpu)
    b_ref = b_cfg * 8
    lr_cfg = float(cfg.optimizer.lr)
    train_infos = os.path.join(a.infos_dir, "av2_infos_train475.pkl")
    db_infos = os.path.join(a.infos_dir, "av2_dbinfos_train.pkl")
    tr = cfg.data.train
    if tr.get("type") == "CBGSDataset":
        tr.dataset.ann_file = train_infos
        tr.dataset.data_root = a.data_root
    if "ann_file" in tr:
        tr.ann_file = train_infos
    if "data_root" in tr:
        tr.data_root = a.data_root
    set_db(cfg._cfg_dict, db_infos, a.data_root)
    if "db_sampler" in cfg:
        cfg.db_sampler.info_path = db_infos
        cfg.db_sampler.data_root = a.data_root
    cfg.data_root = a.data_root
    for k in ("val", "test"):  # v02
        cfg.data[k].ann_file = os.path.join(a.infos_dir, "av2_infos_val150.pkl")
        cfg.data[k].data_root = a.data_root
    cfg.data.samples_per_gpu = a.batch
    cfg.data.workers_per_gpu = a.workers
    cfg.optimizer.lr = lr_cfg * a.batch / b_ref
    if a.pilot_iters:
        cfg.runner = dict(type="IterBasedRunner", max_iters=a.pilot_iters)
        cfg.workflow = [("train", 1)]
        cfg.checkpoint_config = dict(interval=10 ** 9, by_epoch=False)
        cfg.evaluation = dict(interval=10 ** 9, by_epoch=False)
        cfg.log_config.interval = 10
    else:
        cfg.runner = dict(type="EpochBasedRunner", max_epochs=a.epochs)
        cfg.checkpoint_config = dict(interval=1)
        cfg.evaluation.interval = a.epochs + 100
    cfg.work_dir = a.work_dir
    cfg.load_from = None
    cfg.resume_from = None
    cfg.dump(a.out)
    rec = {"public_cfg": a.public_cfg, "samples_per_gpu_shipped": b_cfg, "B_ref": b_ref, "lr_shipped": lr_cfg, "batch": a.batch,
           "lr": cfg.optimizer.lr, "workers": a.workers, "epochs": a.epochs, "pilot_iters": a.pilot_iters, "train_infos": train_infos,
           "db_infos": db_infos, "train_type": tr.get("type"), "lr_config": dict(cfg.lr_config), "optimizer": dict(cfg.optimizer),
           "fp16": "fp16" in cfg, "out": a.out}
    if a.dataset_len:
        from mmdet3d.datasets import build_dataset
        ds = build_dataset(cfg.data.train)
        rec["train_dataset_len"] = len(ds)
        rec["iters_per_epoch"] = -(-len(ds) // a.batch)
    json.dump(rec, open(a.out.replace(".py", "_summary.json"), "w"), indent=1, default=str)
    print(json.dumps(rec, default=str), flush=True)
    print("CFG DONE", flush=True)


if __name__ == "__main__":
    main()
