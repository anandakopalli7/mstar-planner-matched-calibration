#!/usr/bin/env python3
"""test_k8_items_v04_v01: k8_items_v04 --counts-only reproduces k8_items_v02 on every non-error field (nuScenes development
scenes only; Claude line, 2 Nov 2026). The error fields of v04 must be NaN everywhere.
Usage: python -B test_k8_items_v04_v01.py --v02 <npz> --v04 <npz> --out <json>
"""
import argparse
import json
import sys

import numpy as np

ERR = {"item_D", "rec_dx", "rec_dy", "rec_D_long", "rec_D_lat"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v02", required=True)
    ap.add_argument("--v04", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    z2, z4 = np.load(a.v02), np.load(a.v04)
    rep = {"v02": a.v02, "v04": a.v04, "keys_equal": sorted(z2.files) == sorted(z4.files), "compared": [], "different": [], "error_fields_all_nan": {}}
    for k in sorted(z2.files):
        if k == "stamp":
            continue
        if k in ERR:
            rep["error_fields_all_nan"][k] = bool(np.isnan(z4[k]).all()) and z4[k].shape == z2[k].shape
            continue
        rep["compared"].append(k)
        x, y = z2[k], z4[k]
        ok = x.shape == y.shape and x.dtype == y.dtype and (np.array_equal(x, y, equal_nan=True) if x.dtype.kind == "f" else np.array_equal(x, y))
        if not ok:
            rep["different"].append(k)
    rep["items"] = int(len(z2["item_s"]))
    rep["records"] = int(len(z2["rec_s"]))
    rep["identical"] = rep["keys_equal"] and not rep["different"] and all(rep["error_fields_all_nan"].values()) and rep["items"] > 0
    json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps(rep))


if __name__ == "__main__":
    sys.exit(main())
