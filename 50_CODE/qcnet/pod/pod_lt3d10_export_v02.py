"""pod_lt3d10_export_v02 (QCNet arm, 2 Nov 2026) = v01 with the log-id slice of the ap step fixed (v01 cut 13 characters off
"<log>_dts.feather", whose suffix has 12, so the ap step looked for a truncated log id and stopped). split and export ran with v01.
pod_lt3d10_export_v01: LT3D CenterPoint 10 Hz predictions -> per-log files, AV2 tables, AP, reproduction check.

Runs in the LT3D venv. Sub-commands:
  split   --pred P --infos I --out D      one pickle per log under D/per_log/<log>.pkl = {"outputs": [...], "infos": [...]}
                                           (our own pod outputs; consumed by 'export' and by the AB3DMOT runner)
  export  --out D --procs N               LT3D's own AV2Dataset.format_results per log (called on an object that carries only
                                           data_infos and CLASSES, which is all the method reads) -> D/tables/<log>_dts.feather and
                                           <log>_gts.feather; then the three analysis classes of all logs in one pickle-free npz
  ap      --out D --data <val dir> --procs N   official av2 evaluator (DetectionCfg: 50 m, ROI-filtered) on all sweeps for
                                           REGULAR_VEHICLE, PEDESTRIAN, BICYCLIST (per-category AP is independent of the others)
  repro   --out D --ref <2 Hz npz>        the 2 Hz subset of the 10 Hz detections against the detector stage's 2 Hz detections:
                                           per-frame row counts and max |difference| over rows matched in (category, score) order
Outcome-blind (design section 0): detector outputs, detector AP and output-against-output checks only.
"""
import argparse
import json
import os
import pickle
import sys
import time
import types
from multiprocessing import Pool

import numpy as np

CLASSES3 = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST")
A = None


def to_npz(df, path):
    arrays = {}
    for c in df.columns:
        v = df[c].to_numpy()
        if v.dtype == object:
            v = v.astype(str)
        arrays[c] = v
    np.savez_compressed(path, **arrays)


def cmd_split():
    import mmcv
    t0 = time.time()
    outputs = mmcv.load(A.pred)
    infos = pickle.load(open(A.infos, "rb"))
    print("frames", len(outputs), "infos", len(infos), "%.0fs" % (time.time() - t0), flush=True)
    assert len(outputs) == len(infos)
    by_log = {}
    for o, i in zip(outputs, infos):
        d = by_log.setdefault(i["log_id"], {"outputs": [], "infos": []})
        d["outputs"].append(o)
        d["infos"].append(i)
    os.makedirs(os.path.join(A.out, "per_log"), exist_ok=True)
    for log, d in by_log.items():
        ts = [i["timestamp"] for i in d["infos"]]
        assert ts == sorted(ts), log
        p = os.path.join(A.out, "per_log", log + ".pkl")
        with open(p + ".part", "wb") as f:
            pickle.dump(d, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(p + ".part", p)
    print("logs", len(by_log), "SPLIT DONE", flush=True)


def export_one(log):
    from mmdet3d.datasets import AV2Dataset
    d = pickle.load(open(os.path.join(A.out, "per_log", log + ".pkl"), "rb"))
    fake = types.SimpleNamespace(data_infos=d["infos"], CLASSES=AV2Dataset.CLASSES)
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        dts, gts = AV2Dataset.format_results(fake, d["outputs"])
    dts.to_feather(os.path.join(A.out, "tables", log + "_dts.feather"))
    gts.reset_index(drop=True).to_feather(os.path.join(A.out, "tables", log + "_gts.feather"))
    return log, len(d["infos"]), len(dts), len(gts)


def cmd_export():
    import pandas as pd
    logs = sorted(f[:-4] for f in os.listdir(os.path.join(A.out, "per_log")) if f.endswith(".pkl"))
    os.makedirs(os.path.join(A.out, "tables"), exist_ok=True)
    with Pool(A.procs) as pool:
        res = pool.map(export_one, logs, chunksize=1)
    summ = {"logs": len(res), "frames": sum(r[1] for r in res), "dts_rows": sum(r[2] for r in res), "gts_rows": sum(r[3] for r in res)}
    print(json.dumps(summ), flush=True)
    parts = []
    for log in logs:
        df = pd.read_feather(os.path.join(A.out, "tables", log + "_dts.feather"))
        parts.append(df[df["category"].isin(CLASSES3)])
    d3 = pd.concat(parts, ignore_index=True)
    to_npz(d3, os.path.join(A.out, "av2val10_lt3d_centerpoint_dets3_v01.npz"))
    summ["dts3_rows"] = int(len(d3))
    summ["dts3_per_category"] = {k: int(v) for k, v in d3["category"].value_counts().items()}
    with open(os.path.join(A.out, "av2val10_lt3d_centerpoint_export_v01.json"), "w") as f:
        json.dump(summ, f, indent=1)
    print(json.dumps(summ), flush=True)
    print("EXPORT DONE", flush=True)


def cmd_ap():
    import pandas as pd
    from pathlib import Path
    from av2.evaluation.detection.eval import evaluate
    from av2.evaluation.detection.utils import DetectionCfg
    logs = sorted(f[: -len("_dts.feather")] for f in os.listdir(os.path.join(A.out, "tables")) if f.endswith("_dts.feather"))
    assert len(logs) == 150, len(logs)
    dts = pd.concat([pd.read_feather(os.path.join(A.out, "tables", l + "_dts.feather")) for l in logs], ignore_index=True)
    gts = pd.concat([pd.read_feather(os.path.join(A.out, "tables", l + "_gts.feather")) for l in logs], ignore_index=True)
    dts = dts[dts["category"].isin(CLASSES3)].reset_index(drop=True)
    gts = gts[gts["category"].isin(CLASSES3)].reset_index(drop=True)
    print("dts", len(dts), "gts", len(gts), "frames", dts.groupby(["log_id", "timestamp_ns"]).ngroups, flush=True)
    t0 = time.time()
    try:
        cfg = DetectionCfg(dataset_dir=Path(A.data), max_range_m=50.0, eval_only_roi_instances=True, categories=CLASSES3)
    except TypeError:
        cfg = DetectionCfg(dataset_dir=Path(A.data), max_range_m=50.0, eval_only_roi_instances=True)
    _, _, metrics = evaluate(dts, gts, cfg, n_jobs=A.procs)
    metrics.to_csv(os.path.join(A.out, "av2val10_lt3d_centerpoint_ap3_v01.csv"))
    out = {k: metrics.loc[k].to_dict() for k in CLASSES3 if k in metrics.index}
    with open(os.path.join(A.out, "av2val10_lt3d_centerpoint_ap3_v01.json"), "w") as f:
        json.dump({"frames": int(dts.groupby(["log_id", "timestamp_ns"]).ngroups), "max_range_m": 50.0, "roi": True,
                   "ap": out, "seconds": time.time() - t0}, f, indent=1)
    for k, v in out.items():
        print(k, v, flush=True)
    print("AP10 DONE", flush=True)


def cmd_repro():
    import pandas as pd
    ref = np.load(A.ref, allow_pickle=False)
    cols = ["tx_m", "ty_m", "tz_m", "length_m", "width_m", "height_m", "qw", "qx", "qy", "qz", "vx", "vy", "score"]
    r = pd.DataFrame({c: ref[c] for c in cols + ["log_id", "timestamp_ns", "category"]})
    frames_ref = r.groupby(["log_id", "timestamp_ns"]).size()
    logs = sorted(r["log_id"].unique())
    n_same_count = n_frames = n_cat_match = 0
    maxdiff = {c: 0.0 for c in cols}
    missing = []
    for log in logs:
        p = os.path.join(A.out, "tables", log + "_dts.feather")
        if not os.path.exists(p):
            missing.append(log)
            continue
        d = pd.read_feather(p)
        d = d[d["timestamp_ns"].isin(r.loc[r["log_id"] == log, "timestamp_ns"].unique())]
        rl = r[r["log_id"] == log]
        for ts, rg in rl.groupby("timestamp_ns"):
            n_frames += 1
            dg = d[d["timestamp_ns"] == ts]
            if len(dg) == len(rg):
                n_same_count += 1
                a = rg.sort_values(["category", "score", "tx_m"], kind="mergesort")[cols].to_numpy(np.float64)
                b = dg.sort_values(["category", "score", "tx_m"], kind="mergesort")[cols].to_numpy(np.float64)
                if (rg.sort_values(["category", "score", "tx_m"], kind="mergesort")["category"].to_numpy() ==
                        dg.sort_values(["category", "score", "tx_m"], kind="mergesort")["category"].to_numpy()).all():
                    n_cat_match += 1
                    dd = np.abs(a - b).max(axis=0) if len(a) else np.zeros(len(cols))
                    for c, v in zip(cols, dd):
                        maxdiff[c] = max(maxdiff[c], float(v))
    rec = {"ref_frames": int(len(frames_ref)), "frames_compared": n_frames, "frames_same_row_count": n_same_count, "frames_same_categories_in_order": n_cat_match,
           "max_abs_diff_on_same_count_frames": maxdiff, "logs_missing": missing}
    with open(os.path.join(A.out, "av2val10_lt3d_repro_2hz_v01.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec), flush=True)
    print("REPRO DONE", flush=True)


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "export", "ap", "repro"])
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--pred")
    ap.add_argument("--infos")
    ap.add_argument("--out", required=True)
    ap.add_argument("--data")
    ap.add_argument("--ref")
    ap.add_argument("--procs", type=int, default=8)
    A = ap.parse_args()
    sys.path.insert(0, A.lt3d)
    os.chdir(A.lt3d)
    {"split": cmd_split, "export": cmd_export, "ap": cmd_ap, "repro": cmd_repro}[A.cmd]()


if __name__ == "__main__":
    main()
