"""pod_export_v01: OpenPCDet result.pkl on Argoverse 2 val -> the standard AV2 detection table, pickle-free.

Runs on the pod, inside OpenPCDet/tools, after test.py. It rebuilds the val dataset object from the same config so that
the boxes are converted by OpenPCDet's own Argo2Dataset.format_results (lidar_box_to_argo2), i.e. exactly the table the
official evaluation consumed. Outputs in --out:
  av2val_voxelnext_dets_v01.feather   the format_results DataFrame (AV2 columns: tx_m ty_m tz_m length_m width_m height_m
                                      qw qx qy qz score log_id timestamp_ns category), ego frame of each sweep
  av2val_voxelnext_dets_v01.npz       the same columns as plain arrays (strings as fixed-width unicode): loads with
                                      numpy.load(..., allow_pickle=False) on the laptop, so no pickle crosses machines
  av2val_voxelnext_dets_v01.json      counts per category and per log, and the column list
"""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np

from pcdet.config import cfg, cfg_from_yaml_file
from pcdet.datasets.argo2.argo2_dataset import Argo2Dataset
from pcdet.utils import common_utils


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--result", required=True)
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = Path(a.out)
    cfg_from_yaml_file(a.cfg, cfg)
    logger = common_utils.create_logger()
    ds = Argo2Dataset(dataset_cfg=cfg.DATA_CONFIG, class_names=cfg.CLASS_NAMES, training=False, root_path=None, logger=logger)
    with open(a.result, "rb") as f:  # our own pod's output
        det_annos = pickle.load(f)
    print("frames", len(det_annos), "infos", len(ds.argo2_infos), flush=True)
    feather = out / "av2val_voxelnext_dets_v01.feather"
    dts = ds.format_results(det_annos, cfg.CLASS_NAMES, pklfile_prefix=str(feather))
    cols = list(dts.columns)
    arrays = {}
    for c in cols:
        v = dts[c].to_numpy()
        if v.dtype == object:
            v = v.astype(str)
        arrays[c] = v
    np.savez_compressed(out / "av2val_voxelnext_dets_v01.npz", **arrays)
    summary = {"rows": int(len(dts)), "columns": cols, "frames": len(det_annos),
               "logs": int(dts["log_id"].nunique()) if "log_id" in dts else None,
               "per_category": {k: int(v) for k, v in dts["category"].value_counts().items()} if "category" in dts else None,
               "score_min": float(dts["score"].min()) if len(dts) else None}
    (out / "av2val_voxelnext_dets_v01.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps({k: summary[k] for k in ("rows", "frames", "logs")}), flush=True)
    print("EXPORT DONE", flush=True)


if __name__ == "__main__":
    main()
