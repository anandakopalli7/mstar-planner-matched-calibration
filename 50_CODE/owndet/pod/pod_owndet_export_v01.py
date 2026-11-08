"""pod_owndet_export_v01 (own-detector job, 2 Nov 2026): own CenterPoint predictions of one part (held225 or val150) -> the AV2 table
in the format of 30_DATA/av2_det_v01/lt3d_centerpoint/ (npz pickle-free + feather + json summary), and detector AP with the official
av2 evaluator (DetectionCfg: 50 m, ROI-filtered, all competition categories). Design: OWN_DETECTOR_DESIGN_v01.md section 5.
Boxes are converted by LT3D's own AV2Dataset.format_results, per log (called on an object carrying only data_infos and CLASSES).
Outcome-blind: detector outputs, AP, counts and integrity checks only.
Usage (LT3D venv): python pod_owndet_export_v01.py --lt3d <root> --pred <merged pkl> --infos <infos pkl> --part held225|val150
       --dataset-dir <.../Sensor/train or val> --out <dir> --procs N
"""
import argparse
import contextlib
import io
import json
import os
import pickle
import sys
import time
import types
from multiprocessing import Pool
from pathlib import Path

import numpy as np

A = None


def to_npz(df, path):
    arrays = {}
    for c in df.columns:
        v = df[c].to_numpy()
        if v.dtype == object:
            v = v.astype(str)
        arrays[c] = v
    np.savez_compressed(path, **arrays)


def export_one(log):
    from mmdet3d.datasets import AV2Dataset
    d = pickle.load(open(os.path.join(A.out, "per_log", log + ".pkl"), "rb"))
    fake = types.SimpleNamespace(data_infos=d["infos"], CLASSES=AV2Dataset.CLASSES)
    with contextlib.redirect_stdout(io.StringIO()):
        dts, gts = AV2Dataset.format_results(fake, d["outputs"])
    dts.reset_index(drop=True).to_feather(os.path.join(A.out, "tables", log + "_dts.feather"))
    gts.reset_index(drop=True).to_feather(os.path.join(A.out, "tables", log + "_gts.feather"))
    n_nonfinite = int((~np.isfinite(dts[["tx_m", "ty_m", "tz_m", "length_m", "width_m", "height_m", "qw", "qz", "vx", "vy", "score"]].to_numpy(np.float64))).sum())
    return log, len(d["infos"]), len(dts), len(gts), n_nonfinite


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--pred", required=True)
    ap.add_argument("--infos", required=True)
    ap.add_argument("--part", required=True)
    ap.add_argument("--dataset-dir", dest="dataset_dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=8)
    A = ap.parse_args()
    sys.path.insert(0, A.lt3d)
    os.chdir(A.lt3d)
    import mmcv
    import pandas as pd
    t0 = time.time()
    outputs = mmcv.load(A.pred)
    infos = pickle.load(open(A.infos, "rb"))
    assert len(outputs) == len(infos), (len(outputs), len(infos))
    by_log = {}
    for o, i in zip(outputs, infos):
        d = by_log.setdefault(i["log_id"], {"outputs": [], "infos": []})
        d["outputs"].append(o)
        d["infos"].append(i)
    os.makedirs(os.path.join(A.out, "per_log"), exist_ok=True)
    os.makedirs(os.path.join(A.out, "tables"), exist_ok=True)
    for log, d in by_log.items():
        pickle.dump(d, open(os.path.join(A.out, "per_log", log + ".pkl"), "wb"), protocol=pickle.HIGHEST_PROTOCOL)
    del outputs
    logs = sorted(by_log)
    with Pool(A.procs) as pool:
        res = pool.map(export_one, logs, chunksize=1)
    dts = pd.concat([pd.read_feather(os.path.join(A.out, "tables", l + "_dts.feather")) for l in logs], ignore_index=True)
    gts = pd.concat([pd.read_feather(os.path.join(A.out, "tables", l + "_gts.feather")) for l in logs], ignore_index=True)
    stem = "av2%s_owncp_centerpoint" % A.part
    dts.to_feather(os.path.join(A.out, stem + "_dets_v01.feather"))
    to_npz(dts, os.path.join(A.out, stem + "_dets_v01.npz"))
    gts.to_feather(os.path.join(A.out, stem + "_gt_v01.feather"))
    summary = {"part": A.part, "rows": int(len(dts)), "frames": int(sum(r[1] for r in res)), "logs": len(logs),
               "frames_with_predictions": int(dts.groupby(["log_id", "timestamp_ns"]).ngroups), "nonfinite_values": int(sum(r[4] for r in res)),
               "per_category": {k: int(v) for k, v in dts["category"].value_counts().items()}, "score_min": float(dts["score"].min()) if len(dts) else None,
               "gt_rows": int(len(gts))}
    from av2.evaluation.detection.eval import evaluate
    from av2.evaluation.detection.utils import DetectionCfg
    cfg = DetectionCfg(dataset_dir=Path(A.dataset_dir), max_range_m=50.0, eval_only_roi_instances=True)
    _, _, metrics = evaluate(dts, gts, cfg, n_jobs=A.procs)
    metrics.to_csv(os.path.join(A.out, stem + "_ap_v01.csv"))
    summary["ap"] = {str(k): {str(c): float(v) for c, v in row.items()} for k, row in metrics.iterrows()}
    summary["seconds"] = time.time() - t0
    json.dump(summary, open(os.path.join(A.out, stem + "_dets_v01.json"), "w"), indent=1)
    for k in ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST", "AVERAGE_METRICS"):
        if k in metrics.index:
            print(k, metrics.loc[k].to_dict(), flush=True)
    print(json.dumps({k: summary[k] for k in ("part", "rows", "frames", "logs", "frames_with_predictions", "nonfinite_values")}), flush=True)
    print("OWN EXPORT DONE", A.part, flush=True)


if __name__ == "__main__":
    main()
