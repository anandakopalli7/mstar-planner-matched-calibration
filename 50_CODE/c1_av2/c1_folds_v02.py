#!/usr/bin/env python3
"""C1 cross-fitting folds v02 (Claude line, c1_folds_v02, 2 Nov 2026) = c1_folds_v01 (kept) with R17 m7:
  * a duplicate id in the input is an error (v01 merged duplicates of a text input silently);
  * the NumPy version is recorded, and the rule is checked against NumPy's permutation on a fixed probe;
  * no absolute path is written (input file name and SHA-256 only), so the output's hash does not depend on the machine;
  * --split <owndet AV2_TRAIN_SPLIT_v01.json> with --val <file of the 150 validation log ids, or a stage-A val MANIFEST.json>: the
    ids must be exactly the split's held_out_225 plus the 150 validation logs; sources are then set from them
    (held_out_train / val), whatever the input says;
  * --dataset is recorded (av2 for the confirmation; nuscenes for stand-ins).
Rule unchanged: sorted ids, default_rng(seed).permutation(n), k consecutive blocks (np.array_split); seed 20261112.
Usage: python -B c1_folds_v02.py --logs <file> --out <json> --dataset av2|nuscenes [--split <json> --val <file>] [--seed --k]
"""
import argparse
import json
import os

import numpy as np

import c1_folds_v01 as F1

SEED, K, RULE = F1.SEED, F1.K, F1.RULE
sha256_path = F1.sha256_path


def read_logs_strict(path):
    txt = open(path, encoding="utf-8").read()
    try:
        d = json.loads(txt)
        items = list(d["logs"].items()) if isinstance(d.get("logs"), dict) else [(x, "unknown") for x in d["logs"]]
    except ValueError:
        items = [(ln.split()[0], ln.split()[1] if len(ln.split()) > 1 else "unknown") for ln in txt.splitlines() if ln.strip()]
    ids = [str(i) for i, _ in items]
    dup = sorted({i for i in ids if ids.count(i) > 1})
    assert not dup, "duplicate log ids in the input: %s" % dup[:5]
    return {str(i): str(s) for i, s in items}


def read_val(path):
    if path.endswith(".json"):
        d = json.load(open(path))
        return sorted(d["scenes"]) if "scenes" in d else sorted(d["logs"])
    return sorted(ln.split()[0] for ln in open(path).read().splitlines() if ln.strip())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dataset", required=True, choices=["av2", "nuscenes"])
    ap.add_argument("--split", default=None)
    ap.add_argument("--val", default=None)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--k", type=int, default=K)
    ap.add_argument("--label", default="C1 AV2 375-log confirmation set")
    a = ap.parse_args(argv)
    src = read_logs_strict(a.logs)
    if a.dataset == "av2":
        assert a.split and a.val, "--dataset av2 needs --split (the owndet split) and --val (the 150 validation logs)"
    split_info = None
    if a.split:
        sp = json.load(open(a.split))
        held, val = sorted(sp["held_out_225"]), read_val(a.val)
        assert len(held) == 225 and len(val) == 150 and not (set(held) & set(val)), "the split must give 225 held-out and 150 validation logs"
        assert set(src) == set(held) | set(val), "the ids are not the 225 held-out train logs plus the 150 validation logs"
        src = {i: ("held_out_train" if i in set(held) else "val") for i in src}
        split_info = {"split_file": os.path.basename(a.split), "split_sha256": sha256_path(a.split), "val_file": os.path.basename(a.val),
                      "val_sha256": sha256_path(a.val)}
    probe = np.random.default_rng(20261112).permutation(10).tolist()
    out = F1.make_folds(src, a.seed, a.k)
    out.update({"label": a.label, "dataset": a.dataset, "input_file": os.path.basename(a.logs), "input_sha256": sha256_path(a.logs),
                "numpy_version": np.__version__, "permutation_probe_seed20261112_n10": probe, "split_check": split_info,
                "code_sha256": {"c1_folds_v02": sha256_path(os.path.abspath(__file__)), "c1_folds_v01": sha256_path(F1.__file__)}})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    h = sha256_path(a.out)
    with open(a.out + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.out)))
    print(json.dumps({"out": os.path.basename(a.out), "sha256": h, "by_fold": out["by_fold"]}))


if __name__ == "__main__":
    main()
