#!/usr/bin/env python3
"""K7 development diagnostic (Claude line, v01, 1 Nov 2026). Development scenes only (the 10 nuScenes-mini scenes, excluded
from every K7 analysis). Question: should the calibration items be all separating axes (the method's definition, used by
k7_items_v01) or only the axis the planner relies on at the reference pose (the largest gap at margin 0; k7_items_v02)?
For the development scenes' k7_items_v02 items, M7's held-out threshold (the scene's own fold's fit, from the other folds)
gives the exceedance rate of all items, of the reference-relied items and of the other items, overall and per group.
Usage: python -B k7_dev_axis_diag_v01.py --items-dir <dir with items_v02_dev_t1.npz, items_v02_dev_t3.npz> --out <json>
"""
import argparse
import json
import os

import numpy as np

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s"]
GROUPS = ["car", "pedestrian", "two_wheeler", "large"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = {"note": "development scenes only; diagnostics, not evidence"}
    for t in ("t1", "t3"):
        z = np.load(os.path.join(a.items_dir, "items_v02_dev_%s.npz" % t))
        F = json.load(open(os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t)))
        names = [str(x) for x in z["scene_names"]]
        fold = np.array([F["fold_of_scene"][n] for n in names])
        s, h, l0, ip = z["item_s"], z["item_h"], z["item_l0"], z["item_inpath"].astype(int)
        thr = np.array([F["fits"][str(fold[si])][STEPS[hh]]["Mstar_ip"][l + 96 * i] for si, hh, l, i in zip(s, h, l0, ip)])
        exc = z["item_D"] > thr * z["item_sd"]
        rr = z["item_ref_relied"]

        def rate(m):
            sc = [exc[m & (s == k)].mean() for k in range(len(names)) if (m & (s == k)).any()]
            return {"scene_level": float(np.mean(sc)) if sc else None, "item_level": float(exc[m].mean()) if m.any() else None, "items": int(m.sum())}
        r = {"all_axes": rate(np.ones(len(exc), bool)), "reference_relied": rate(rr), "other_axis": rate(~rr), "by_group": {}}
        for g, gn in enumerate(GROUPS):
            m = z["item_g"] == g
            r["by_group"][gn] = {"all_axes": rate(m), "reference_relied": rate(m & rr), "other_axis": rate(m & ~rr)}
        out[t] = r
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({t: {k: out[t][k] for k in ("all_axes", "reference_relied", "other_axis")} for t in ("t1", "t3")}, indent=1))


if __name__ == "__main__":
    main()
