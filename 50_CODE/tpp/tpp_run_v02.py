#!/usr/bin/env python3
"""Trajectron++ forward passes v02 (Claude line, tpp_run_v02, 4 Nov 2026) = tpp_run_v01 (kept, imported and run unchanged; D17 v04 binds
it) with R17c M4 / D16 v18 Choice 39d for C1: when the keys' units are not nuScenes scenes (read from the keys' scene names) the
`--scenes` subset is REFUSED, so every record is predicted. After tpp_run_v01 has written the run, this writes <out>.wrapper.json:
this file's hash (entry point), the run's and the keys' hashes, the seed, the dataset and scenes = null. c1_predarm_v04 requires that
record for AV2 runs and checks the seed against the run's summary. Self-contained (Python 3.8, the tpp38 environment; no C1 import).
Usage: as tpp_run_v01.
"""
import hashlib
import json
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
NUSC = re.compile(r"^scene-\d{4}$")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace("\\", "/")


def arg(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    keys, out = arg(argv, "--keys"), arg(argv, "--out")
    names = [str(x) for x in np.load(keys, allow_pickle=False)["scene_names"]]
    ds = "nuscenes" if names and all(NUSC.match(n) for n in names) else "av2" if names and not any(NUSC.match(n) for n in names) else "unknown"
    if ds != "nuscenes":
        assert "--scenes" not in argv, "refused: --scenes is refused under C1 (every record is predicted; R17c M4)"
    import tpp_run_v01 as R1
    sys.argv = [R1.__file__] + argv
    R1.main()
    summ = json.load(open(out.replace(".npz", "_summary.json")))
    rec = {"entry_point": {rel(__file__): sha(os.path.abspath(__file__))}, "module": {rel(R1.__file__): sha(R1.__file__)},
           "out_sha256": sha(out), "keys_sha256": sha(keys), "seed": summ.get("seed"), "dataset": ds,
           "scenes": None if "--scenes" not in argv else "subset (nuScenes only)"}
    json.dump(rec, open(out + ".wrapper.json", "w"), indent=1)
    print("TPP RUN V02 DONE")


if __name__ == "__main__":
    main()
