#!/usr/bin/env python3
"""Apply a C1 transfer fit to a set of units (Claude line, c1_transfer_apply_v01, 2 Nov 2026). Choice 7.
The transfer fit (c1_fit_v01 --route transfer on the 850 nuScenes scenes) is computed from nuScenes only; which units it is applied
to (the 375 AV2 logs, known only after slot S20) does not change it. This copies the fit and sets fold_of_scene (every unit -> the
single transfer fold '0'), scenes, fold_scene_counts and folds_sha256 for the given folds file (c1_run_v01 checks folds_sha256), and
records the source fit's SHA-256. It asserts that the fit content (every 'fits' entry, 'joint', 'retuned_transfer_arm') is unchanged.
Usage: python -B c1_transfer_apply_v01.py --transfer-fit <json> --folds <AV2 c1 folds json> --out <json>
"""
import argparse
import copy
import hashlib
import json
import os


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--transfer-fit", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    src = json.load(open(a.transfer_fit))
    assert src.get("route") == "transfer" and list(src["fits"]) == ["0"], "not a C1 transfer fit"
    units = sorted(json.load(open(a.folds))["fold_of_log"])
    out = copy.deepcopy(src)
    out.update({"scenes": units, "fold_of_scene": {u: 0 for u in units}, "fold_scene_counts": [len(units)], "folds_sha256": sha(a.folds),
                "transfer_fit_source_sha256": sha(a.transfer_fit), "applied_by": "c1_transfer_apply_v01"})
    for k in ("fits", "joint", "retuned_transfer_arm", "transfer_source_units", "transfer_source_folds_sha256"):
        assert out.get(k) == src.get(k), "fit content changed: " + k
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({"out": os.path.abspath(a.out), "sha256": sha(a.out), "units": len(units)}))


if __name__ == "__main__":
    main()
