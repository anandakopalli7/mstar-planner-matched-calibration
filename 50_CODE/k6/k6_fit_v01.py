#!/usr/bin/env python3
"""K6 cross-fitted arm fits (Claude line, v01, 31 Oct 2026). For one tracker setting: the train and val items of every planner
step (k6_items_v01) are joined into one pool of 850 scenes; the scenes are split by log into 5 folds (m_lib_v04.log_folds,
seed K6_SEED); for every fold and step, every arm is fitted on the other four folds with m_lib_v04.prepare and
fit_methods, unchanged and with the frozen method defaults. The planner on a scene uses its own fold's fits.
Usage: python -B k6_fit_v01.py --items <dir> --tags <train tag> <val tag> --out <json>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m"))
import m_lib_v04 as M  # noqa: E402

K6_SEED = 20261101
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "omc", "chord", "V", "contested", "D")
REC_KEYS = ("s", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "contested")


def joined(items_dir, tags, step, names_by_tag, logs_by_tag, logs):
    lidx = {l: i for i, l in enumerate(logs)}
    it, rc, off = {k: [] for k in ITEM_KEYS}, {k: [] for k in REC_KEYS}, 0
    for tag in tags:
        z = np.load(os.path.join(items_dir, "items_%s_%s.npz" % (tag, step)))
        own_logs = sorted(set(logs_by_tag[tag].values()))
        remap = np.array([lidx[l] for l in own_logs], int)
        for k in ITEM_KEYS:
            v = z["item_" + k]
            if k == "s":
                v = v + off
            elif k == "lg":
                v = remap[v]
            it[k].append(v)
        for k in REC_KEYS:
            v = z["rec_" + k]
            rc[k].append(v + off if k == "s" else v)
        off += len(names_by_tag[tag])
    items = {k: np.concatenate(v) for k, v in it.items()}
    recs = {k: np.concatenate(v) for k, v in rc.items()}
    for d, ks in ((items, ("s", "lg", "g", "r", "a")), (recs, ("s", "g", "r"))):
        for k in ks:
            d[k] = d[k].astype(int)
    return items, recs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--tags", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    names_by_tag, logs_by_tag = {}, {}
    for tag in a.tags:
        sm = json.load(open(os.path.join(a.items, "items_%s_summary.json" % tag)))
        names_by_tag[tag] = sm["scene_names"]
        logs_by_tag[tag] = sm["scene_log"]
    names = [s for t in a.tags for s in names_by_tag[t]]
    assert len(set(names)) == len(names), "a scene appears in two splits"
    scene_log = {s: l for t in a.tags for s, l in logs_by_tag[t].items()}
    logs = sorted(set(scene_log.values()))
    folds, load = M.log_folds(names, scene_log, k=M.K_FOLDS, seed=K6_SEED)
    out = {"tags": a.tags, "seed": K6_SEED, "scenes": names, "fold_of_scene": {s: int(f) for s, f in zip(names, folds)},
           "fold_scene_counts": [int(x) for x in load], "fits": {str(f): {} for f in range(M.K_FOLDS)}, "items_per_step": {}}
    for step in STEPS:
        items, recs = joined(a.items, a.tags, step, names_by_tag, logs_by_tag, logs)
        items["scene_log_idx"] = np.array([logs.index(scene_log[s]) for s in names], int)
        items["n_scenes"], items["n_logs"] = len(names), len(logs)
        P = M.prepare(items, recs, {})
        out["items_per_step"][step] = int(len(items["D"]))
        for f in range(M.K_FOLDS):
            cal_scene = folds != f
            fit = M.fit_methods(items, recs, P, cal_scene, {})
            out["fits"][str(f)][step] = {"Mstar": fit["Mstar"].tolist(), "Mstar_src": fit["Mstar_src"].tolist(),
                                         "B6": fit["B6"].tolist(), "B4": float(fit["B4"]), "B3": float(fit["B3"]),
                                         "B9": float(fit["B9"]), "B1": fit["B1"].tolist(), "B1_k": fit["B1_k"]}
            assert np.all(np.isfinite(fit["Mstar"])) and np.all(np.isfinite(fit["B6"])), "non-finite threshold"
        print(step, "items", len(items["D"]), "%.0f s" % (time.time() - t0), flush=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("K6 FIT DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
