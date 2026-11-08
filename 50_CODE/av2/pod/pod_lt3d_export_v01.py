"""pod_lt3d_export_v01: LT3D CenterPoint predictions on AV2 val -> the standard AV2 detection table with velocity, pickle-free.

Runs on the pod in the LT3D venv, from the LT3D repository root. The boxes are converted by LT3D's own
AV2Dataset.format_results (the code the released model was evaluated with), so no box convention is re-implemented here.
Outputs in --out:
  av2val_lt3d_centerpoint_dets_v01.feather / .npz   predictions: tx_m ty_m tz_m length_m width_m height_m qw qx qy qz vx vy
                                                     score log_id timestamp_ns category (ego frame of each sweep)
  av2val_lt3d_centerpoint_gt_v01.feather             the ground truth table format_results built (for the AP check only)
  av2val_lt3d_centerpoint_ap_v01.csv / .json         detector AP from the official av2 evaluator (DetectionCfg, max range 50 m,
                                                     ROI-filtered): allowed before any freeze (D15 §4)
The npz loads with numpy.load(..., allow_pickle=False): strings are fixed-width unicode, so no pickle crosses machines.
"""
import argparse
import json
from pathlib import Path

import mmcv
import numpy as np
from mmcv import Config

from mmdet3d.datasets import build_dataset


def to_npz(df, path):
    arrays = {}
    for c in df.columns:
        v = df[c].to_numpy()
        if v.dtype == object:
            v = v.astype(str)
        arrays[c] = v
    np.savez_compressed(path, **arrays)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    cfg = Config.fromfile(a.cfg)
    cfg.data.test.test_mode = True
    ds = build_dataset(cfg.data.test)
    outputs = mmcv.load(a.pred)  # our own pod's output
    print("frames", len(outputs), "infos", len(ds.data_infos), flush=True)
    res = ds.format_results(outputs)
    dts, gts = (res if isinstance(res, tuple) else (res, None))
    dts = dts.reset_index(drop=True)
    dts.to_feather(out / "av2val_lt3d_centerpoint_dets_v01.feather")
    to_npz(dts, out / "av2val_lt3d_centerpoint_dets_v01.npz")
    summary = {"rows": int(len(dts)), "columns": list(dts.columns), "frames": len(outputs),
               "logs": int(dts["log_id"].nunique()), "per_category": {k: int(v) for k, v in dts["category"].value_counts().items()},
               "score_min": float(dts["score"].min()) if len(dts) else None}
    if gts is not None:
        gts = gts.reset_index(drop=True)
        gts.to_feather(out / "av2val_lt3d_centerpoint_gt_v01.feather")
        from av2.evaluation.detection.eval import evaluate
        from av2.evaluation.detection.utils import DetectionCfg
        dcfg = DetectionCfg(dataset_dir=Path(cfg.data.test.data_root) / "val", max_range_m=50.0, eval_only_roi_instances=True)
        _, _, metrics = evaluate(dts, gts, dcfg)
        metrics.to_csv(out / "av2val_lt3d_centerpoint_ap_v01.csv")
        summary["ap"] = {str(k): {str(c): float(v) for c, v in row.items()} for k, row in metrics.iterrows()}
        for k in ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST", "AVERAGE_METRICS"):
            if k in metrics.index:
                print(k, metrics.loc[k].to_dict(), flush=True)
    (out / "av2val_lt3d_centerpoint_dets_v01.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ("rows", "frames", "logs")}), flush=True)
    print("LT3D EXPORT DONE", flush=True)


if __name__ == "__main__":
    main()
