#!/usr/bin/env python3
"""Method stage, pre-freeze counts v01 (Claude line, 31 Oct 2026): items and scenes per level-0 stratum for one tracker
setting, train and val, at 1, 2 and 4 s, with outcomes switched off (no residual is computed). Fixes the evaluated strata
(>= 39 scenes in the evaluation pool) as plan section 7 requires. Also writes the fold sizes and motion-state counts.
Usage: python m_sizes_v01.py --tracker T1 --train-workers ... --val-workers ... --train-gt ... --val-gt ... --meta ...
       --train-horizon ... --val-horizon ... --experiment ... --out sizes.json
"""
import argparse
import json
import sys

import numpy as np

import m_data_v01 as MD
import m_lib_v01 as M


def main():
    ap = argparse.ArgumentParser()
    for k in ("tracker", "train-gt", "val-gt", "meta", "train-horizon", "val-horizon", "experiment", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--train-workers", nargs="+", required=True)
    ap.add_argument("--val-workers", nargs="+", required=True)
    a = ap.parse_args()
    res = {"tracker": a.tracker, "experiment": a.experiment, "outcomes_computed": False, "rule": "evaluated = level-0 strata with >= %d scenes" % M.N_EVAL}
    for split, workers, gt, hz in (("train", a.train_workers, a.train_gt, a.train_horizon), ("val", a.val_workers, a.val_gt, a.val_horizon)):
        data, info, scene_names, scene_log = MD.load_split(workers, gt, a.meta, hz, a.experiment, outcomes=False)
        res[split] = {"info": info}
        if split == "train":
            folds, load = M.log_folds(scene_names, scene_log)
            res["folds"] = {"scenes_per_fold": load, "logs_per_fold": [int(len({scene_log[s] for s, f in zip(scene_names, folds) if f == i})) for i in range(M.K_FOLDS)]}
        for h, (items, recs) in data.items():
            assert np.all(np.isnan(items["D"])) and np.all(np.isnan(recs["dx"])), "outcomes leaked into the counts"
            m = M.motion_state(items)
            cnt = M.counts_by_l0(items, m)
            res[split][h] = {"n_items": int(len(items["D"])), "n_records": int(len(recs["s"])),
                             "motion_items": {M.MOTIONS[i]: int((m == i).sum()) for i in range(4)},
                             "strata": cnt, "evaluated": sorted([k for k, v in cnt.items() if v["scenes"] >= M.N_EVAL])}
        del data
    json.dump(res, open(a.out, "w"), indent=1)
    for split in ("train", "val"):
        print(split, {h: len(res[split][h]["evaluated"]) for h in M.HSTEPS}, res[split]["h2s"]["motion_items"])


if __name__ == "__main__":
    sys.exit(main())
