"""pod_export_v02: OpenPCDet VoxelNeXt result.pkl on AV2 val (2 Hz subset) -> AV2 detection table + detector AP, pickle-free.

v01 relied on test.py's own evaluation, which failed: av2 0.2.0's map loader joins a relative dataset_dir twice
(".../val/<log>/map/../data/argo2/sensor/val/<log>/map/..."). v02 sets DATA_PATH to an absolute path, converts the boxes
with OpenPCDet's own Argo2Dataset.format_results, and computes AP with the official evaluator exactly as
Argo2Dataset.evaluation does (ground truth restricted to the predicted frames, all competition categories,
eval_only_roi_instances=True), at OpenPCDet's evaluate range (200 m) and at LT3D's (50 m) for a like-for-like comparison.
Runs on the pod, from OpenPCDet/tools. Outputs in --out:
  av2val_voxelnext_dets_v01.feather / .npz / .json   (npz loads with allow_pickle=False)
  av2val_voxelnext_ap_200m_v02.csv, av2val_voxelnext_ap_50m_v02.csv, av2val_voxelnext_ap_v02.json
Outcome-blind rule (D15 §4): detector AP and counts only.
"""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets.argo2.argo2_dataset import Argo2Dataset
from pcdet.utils import common_utils


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
    ap.add_argument("--result", required=True)
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--data-path", default="/root/work/OpenPCDet/data/argo2")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    cfg_from_yaml_file(a.cfg, cfg)
    cfg.DATA_CONFIG.DATA_PATH = a.data_path
    logger = common_utils.create_logger()
    ds = Argo2Dataset(dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, training=False, root_path=None, logger=logger)
    with open(a.result, "rb") as f:  # our own pod's output
        det_annos = pickle.load(f)
    print("frames", len(det_annos), "infos", len(ds.argo2_infos), flush=True)
    dts = ds.format_results(det_annos, cfg.CLASS_NAMES, pklfile_prefix=str(out / "av2val_voxelnext_dets_v01.feather"))
    dts = dts.reset_index(drop=True)
    to_npz(dts, out / "av2val_voxelnext_dets_v01.npz")
    summary = {"rows": int(len(dts)), "columns": list(dts.columns), "frames": len(det_annos), "logs": int(dts["log_id"].nunique()),
               "per_category": {k: int(v) for k, v in dts["category"].value_counts().items()}, "score_min": float(dts["score"].min()),
               "frame_rule": "every 5th sweep per log (LT3D VAL_SAMPLE_RATE); 4,806 frames"}
    (out / "av2val_voxelnext_dets_v01.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ("rows", "frames", "logs")}), flush=True)

    from av2.evaluation.detection.constants import CompetitionCategories
    from av2.evaluation.detection.eval import evaluate
    from av2.evaluation.detection.utils import DetectionCfg
    from av2.utils.io import read_feather
    gts = read_feather(Path(a.data_path) / "val_anno.feather")
    gts = gts.set_index(["log_id", "timestamp_ns"]).sort_values("category")
    keep = sorted(set(zip(dts["log_id"], dts["timestamp_ns"])) & set(gts.index.unique()))
    gts = gts.loc[keep].sort_index().reset_index()
    gts["category"] = gts["category"].str.upper()
    print("gt rows on predicted frames", len(gts), "frames", len(keep), flush=True)
    res = {}
    for rng in (200.0, 50.0):
        dcfg = DetectionCfg(dataset_dir=Path(a.data_path) / "sensor" / "val", categories=tuple(x.value for x in CompetitionCategories),
                            max_range_m=rng, eval_only_roi_instances=True)
        _, _, metrics = evaluate(dts.copy(), gts.copy(), dcfg)
        tag = "%dm" % int(rng)
        metrics.to_csv(out / ("av2val_voxelnext_ap_%s_v02.csv" % tag))
        res[tag] = {str(k): {str(c): float(v) for c, v in row.items()} for k, row in metrics.iterrows()}
        for k in ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST", "AVERAGE_METRICS"):
            if k in metrics.index:
                print(tag, k, {c: round(float(v), 3) for c, v in metrics.loc[k].items()}, flush=True)
    (out / "av2val_voxelnext_ap_v02.json").write_text(json.dumps(res, indent=1))
    print("EXPORT DONE", flush=True)


if __name__ == "__main__":
    main()
