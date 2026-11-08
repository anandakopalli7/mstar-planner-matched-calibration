#!/usr/bin/env python3
"""C1 stand-in preparation (Claude line, 2 Nov 2026): N nuScenes development scenes drawn at random (seed 20261114) from the 840
non-development scenes, each treated as one log (its source = the nuScenes split of its cache: train or val), cut into the C1 folds
by c1_folds_v01 (seed 20261112), plus the analysis configs: the stand-in, and the two reproduction configs (the K8 Linux replicate's
decision runs with K8's fits; the M*J Linux decision runs with the v02 joint fits).
Usage: python -B tests/c1_standin_prep_v01.py --n 375 --out-dir <dir>
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
import c1_folds_v01 as F  # noqa: E402

DEV = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077", "scene-1094", "scene-1100")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=375)
    ap.add_argument("--seed", type=int, default=20261114)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    src = {}
    for part in ("train", "val"):
        for sc in json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % part, "MANIFEST.json")))["scenes"]:
            if sc not in DEV:
                src[sc] = part
    names = sorted(src)
    assert len(names) == 840
    pick = sorted(np.random.default_rng(a.seed).choice(len(names), a.n, replace=False).tolist())
    lp = os.path.join(a.out_dir, "standin_units.txt")
    with open(lp, "w") as f:
        f.write("\n".join("%s %s" % (names[i], src[names[i]]) for i in pick) + "\n")
    F.main(["--logs", lp, "--out", os.path.join(a.out_dir, "folds.json"), "--label", "C1 STAND-IN: %d nuScenes scenes as logs" % a.n])
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % p, "MANIFEST.json") for p in ("train", "val")]
    cfg = {"routes": [{"name": "within_lt3d", "runs": os.path.join(a.out_dir, "runs"), "tags": {"t1": "t1_within_lt3d", "t3": "t3_within_lt3d"},
                       "fits": {t: os.path.join(a.out_dir, "fits_%s.json" % t) for t in ("t1", "t3")}, "modes": ["decide", "loop"]}],
           "units_are_logs": True, "manifests": man, "c": {"t1": 0.03, "t3": 0.03}, "folds": os.path.join(a.out_dir, "folds.json")}
    json.dump(cfg, open(os.path.join(a.out_dir, "config_standin.json"), "w"), indent=1)
    rk8 = {"routes": [{"name": "within_lt3d", "runs": os.path.join(W, "70_TESTS", "k8_expl_v02_linux"), "tags": {"t1": "t1", "t3": "t3"},
                       "fits": {t: os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t) for t in ("t1", "t3")}, "modes": ["decide"]}],
           "units_are_logs": False, "manifests": man, "c": {"t1": 0.03, "t3": 0.03}}
    json.dump(rk8, open(os.path.join(a.out_dir, "config_reproduce_k8.json"), "w"), indent=1)
    rj = {"routes": [{"name": "within_lt3d", "runs": os.path.join(W, "70_TESTS", "k8_joint_v01_linux", "full_v02fits", "runs"),
                      "tags": {"t1": "t1", "t3": "t3"},
                      "fits": {t: os.path.join(W, "60_RESULTS", "k8_joint_fits_v01", "k8_joint_fits_%s_v02.json" % t) for t in ("t1", "t3")},
                      "modes": ["decide"]}], "units_are_logs": False, "manifests": man, "c": {"t1": 0.03, "t3": 0.03}}
    json.dump(rj, open(os.path.join(a.out_dir, "config_reproduce_joint.json"), "w"), indent=1)
    print("STANDIN PREP DONE", a.n, a.out_dir)


if __name__ == "__main__":
    main()
