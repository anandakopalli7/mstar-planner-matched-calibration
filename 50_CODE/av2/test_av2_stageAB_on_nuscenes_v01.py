#!/usr/bin/env python3
"""test_av2_stageAB_on_nuscenes_v01: compares a cache built by av2_cache_stageA_v01 (and completed by av2_cache_stageB_v01)
with the existing K6 cache on nuScenes ONLY (Claude line, 2 Nov 2026). Nothing here touches Argoverse 2.
  --mode A : every K6 field except gt_x, gt_y, gt_yaw, gt_w, gt_l is identical (dtype, shape, values; NaN = NaN), and those
             five are NaN everywhere in the stage-A file;
  --mode B : every K6 field is identical.
The manifests' per-scene fields other than sha256 must agree in both modes.
Usage: python -B test_av2_stageAB_on_nuscenes_v01.py --mode A|B --test <dir> --ref <30_DATA/k6/cache_v02_...> --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

GT_POS = ("gt_x", "gt_y", "gt_yaw", "gt_w", "gt_l")


def same(a, b):
    if a.dtype != b.dtype or a.shape != b.shape:
        return False
    if a.dtype.kind == "f":
        return bool(np.array_equal(a, b, equal_nan=True))
    return bool(np.array_equal(a, b))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=("A", "B"))
    ap.add_argument("--test", required=True)
    ap.add_argument("--ref", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    mt = json.load(open(os.path.join(a.test, "MANIFEST.json")))
    mr = json.load(open(os.path.join(a.ref, "MANIFEST.json")))
    rep = {"mode": a.mode, "test": os.path.abspath(a.test), "ref": os.path.abspath(a.ref), "scenes": len(mr["scenes"]),
           "manifest_scene_set_equal": sorted(mt["scenes"]) == sorted(mr["scenes"]), "manifest_fields_differ": [],
           "fields_compared": 0, "fields_different": [], "position_fields_not_nan": [], "extra_fields": None,
           "stats_equal": mt["stats"] == mr["stats"]}
    for sc in sorted(mr["scenes"]):
        it, ir = dict(mt["scenes"].get(sc, {})), dict(mr["scenes"][sc])
        it.pop("sha256", None)
        ir.pop("sha256", None)
        if it != ir:
            rep["manifest_fields_differ"].append(sc)
        zt, zr = np.load(os.path.join(a.test, sc + ".npz")), np.load(os.path.join(a.ref, sc + ".npz"))
        if rep["extra_fields"] is None:
            rep["extra_fields"] = sorted(set(zt.files) - set(zr.files))
        for k in zr.files:
            if k not in zt.files:
                rep["fields_different"].append((sc, k, "missing"))
                continue
            if a.mode == "A" and k in GT_POS:
                if not np.isnan(zt[k]).all() or zt[k].shape != zr[k].shape:
                    rep["position_fields_not_nan"].append((sc, k))
                continue
            rep["fields_compared"] += 1
            if not same(zt[k], zr[k]):
                rep["fields_different"].append((sc, k))
    rep["identical"] = (rep["manifest_scene_set_equal"] and not rep["manifest_fields_differ"] and not rep["fields_different"]
                        and not rep["position_fields_not_nan"] and rep["fields_compared"] > 0)
    json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps({k: (v if not isinstance(v, list) else v[:5]) for k, v in rep.items()}))


if __name__ == "__main__":
    sys.exit(main())
