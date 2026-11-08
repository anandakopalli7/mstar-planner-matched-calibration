"""pod_owndet_pilot_v01 (own-detector job, 2 Nov 2026): read a pilot run's mmcv json log and apply the epoch rule of
OWN_DETECTOR_DESIGN_v01.md section 4: E = min(20, floor(H_train * 3600 / (s_per_it * iters_per_epoch))).
Usage: python pod_owndet_pilot_v01.py --work-dir <pilot work dir> --cfg-summary <cfg _summary.json> --h-train 18 --price 0.89 --out <json>
"""
import argparse
import glob
import json
import math

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--work-dir", dest="work_dir", required=True)
    ap.add_argument("--cfg-summary", dest="cfg_summary", required=True)
    ap.add_argument("--h-train", dest="h_train", type=float, default=18.0)
    ap.add_argument("--price", type=float, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    logs = sorted(glob.glob(a.work_dir + "/*.log.json"))
    rows = []
    for line in open(logs[-1]):
        try:
            d = json.loads(line)
        except Exception:  # noqa: BLE001
            continue
        if d.get("mode") == "train" and "time" in d:
            rows.append(d)
    late = [r for r in rows if r["iter"] > 100] or rows
    s_it = float(np.mean([r["time"] for r in late]))
    data_t = float(np.mean([r["data_time"] for r in late]))
    mem = max(r.get("memory", 0) for r in rows)
    cs = json.load(open(a.cfg_summary))
    ipe = cs["iters_per_epoch"]
    hours_per_epoch = s_it * ipe / 3600
    e_rule = min(20, math.floor(a.h_train * 3600 / (s_it * ipe)))
    rec = {"log": logs[-1], "iters_logged": len(rows), "last_iter": rows[-1]["iter"] if rows else None, "s_per_it_after_100": s_it,
           "data_time_s_per_it": data_t, "peak_memory_mb": mem, "batch": cs["batch"], "lr": cs["lr"], "train_dataset_len": cs["train_dataset_len"],
           "iters_per_epoch": ipe, "hours_per_epoch": hours_per_epoch, "epochs_rule": e_rule, "h_train": a.h_train,
           "train_hours_at_rule": e_rule * hours_per_epoch, "train_cost_at_rule": e_rule * hours_per_epoch * a.price, "price_per_h": a.price}
    json.dump(rec, open(a.out, "w"), indent=1)
    print(json.dumps(rec), flush=True)
    print("PILOT SUMMARY DONE", flush=True)


if __name__ == "__main__":
    main()
