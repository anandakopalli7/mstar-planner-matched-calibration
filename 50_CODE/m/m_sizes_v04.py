#!/usr/bin/env python3
"""Method stage, pre-freeze counts v04 (Claude line, 31 Oct 2026; v03 with the v04 imports, used by the simulated
end-to-end test; the real counts files were made by m_sizes_v03 and the run re-derives and checks them with v04 code; v02 + the m_data_v03 loader with the Poly-MOT velocity
correction, peak memory, and the turning share of moving cars per split). For one tracker setting, train and val, at 1, 2 and 4 s,
with outcomes switched off (no residual is computed), it writes:
- items, scenes and logs per level-0 stratum;
- the evaluation cells: E1 on train (strata, then remainders) and E2 on val (pooled over range, then remainders), each
  needing >= 39 scenes and >= 8 logs (plan v03 section 7);
- in-path items censored at the horizon, per stratum;
- the item layout (scene, stratum, count) at 2 s, for the operating-characteristic simulation;
- fold sizes.
It refuses to finish if any evaluation-cell list is empty.
Usage: python m_sizes_v04.py --tracker T1 --train-workers ... --val-workers ... --train-gt ... --val-gt ... --meta ...
       --train-horizon ... --val-horizon ... --experiment ... --out sizes.json
"""
import argparse
import json
import sys

import numpy as np

import m_data_v04 as MD
import m_lib_v04 as M


def main():
    ap = argparse.ArgumentParser()
    for k in ("tracker", "train-gt", "val-gt", "meta", "train-horizon", "val-horizon", "experiment", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--train-workers", nargs="+", required=True)
    ap.add_argument("--val-workers", nargs="+", required=True)
    a = ap.parse_args()
    res = {"tracker": a.tracker, "experiment": a.experiment, "outcomes_computed": False,
           "rule": "cells need >= %d scenes and >= %d logs" % (M.MIN_CELL_SCENES, M.MIN_CELL_LOGS)}
    for split, workers, gt, hz in (("train", a.train_workers, a.train_gt, a.train_horizon), ("val", a.val_workers, a.val_gt, a.val_horizon)):
        data, info, scene_names, scene_log = MD.load_split(workers, gt, a.meta, hz, a.experiment, outcomes=False)
        res[split] = {"info": info}
        if split == "train":
            folds, load = M.log_folds(scene_names, scene_log)
            res["folds"] = {"scenes_per_fold": load, "logs_per_fold": [int(len({scene_log[s] for s, f in zip(scene_names, folds) if f == i})) for i in range(M.K_FOLDS)]}
        for h, (items, recs) in data.items():
            assert np.all(np.isnan(items["D"])) and np.all(np.isnan(recs["dx"])), "outcomes leaked into the counts"
            m = M.motion_state(items)
            cells = M.make_cells(items, m, "E1" if split == "train" else "E2")
            assert cells, "no evaluation cell for %s %s" % (split, h)
            l0 = M.levels(items, m)[0]
            res[split][h] = {"n_items": int(len(items["D"])), "n_records": int(len(recs["s"])),
                             "motion_items": {M.MOTIONS[i]: int((m == i).sum()) for i in range(4)},
                             "strata": M.counts_by_l0(items, m), "cells": [[n, [int(x) for x in ids]] for n, ids in cells],
                             "items_in_cells": int(np.isin(l0, [x for _, ids in cells for x in ids]).sum()),
                             "censored_by_l0": {M.l0_name(i): int(v) for i, v in enumerate(items["censored_by_l0"]) if v}}
            mv = (items["g"] == 0) & (m != 0)
            res[split][h]["car_moving_turning_share"] = float(np.mean(m[mv] == 2)) if mv.any() else None
            if h == "h2s":
                key, cnt = np.unique(np.stack([items["s"], l0]), axis=1, return_counts=True)
                res[split][h]["layout"] = {"scene_l0_count": np.vstack([key, cnt]).T.tolist(),
                                           "scene_log_idx": items["scene_log_idx"].tolist(), "n_logs": int(items["n_logs"]),
                                           "records_per_scene": np.bincount(recs["s"], minlength=items["n_scenes"]).tolist()}
        del data
    res["peak_working_set_mb"] = MD.peak_mb()
    json.dump(res, open(a.out, "w"))
    for split in ("train", "val"):
        print(split, {h: len(res[split][h]["cells"]) for h in M.HSTEPS}, res[split]["h2s"]["motion_items"],
              "items in cells %d of %d" % (res[split]["h2s"]["items_in_cells"], res[split]["h2s"]["n_items"]))
    print("M SIZES V04 DONE", a.tracker)


if __name__ == "__main__":
    sys.exit(main())
