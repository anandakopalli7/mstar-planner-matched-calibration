#!/usr/bin/env python3
"""C1 folds v03 (Claude line, c1_folds_v03, 4 Nov 2026) = c1_folds_v02 (kept, imported, unchanged) plus D16 v17 Choice 38d (R17c §7.1a):
  --restrict-from <the 375-log folds> --source val|held_out_train  writes a CHILD folds file: the parent's fold labels restricted to the
  units whose source is --source, the parent's seed, k and dataset, parent_sha256 and the restriction; no new randomness (no
  permutation is drawn). Bound before the freeze in the roles folds_val150 and folds_train225; c1_guard_v03.check_child_folds verifies
  it against the bound parent.
Without --restrict-from it is c1_folds_v02 (same arguments, same output).
Usage: python -B c1_folds_v03.py --restrict-from <folds.json> --source val|held_out_train --out <json>
       python -B c1_folds_v03.py <c1_folds_v02 arguments>
"""
import argparse
import hashlib
import json
import os
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_folds_v02 as F2  # noqa: E402

RULE = "restriction of the parent folds to the units of one source; labels, seed and k unchanged; no new randomness (Choice 38d)"


def restrict(parent, source):
    fol = {u: f for u, f in parent["fold_of_log"].items() if parent["source_of_log"].get(u) == source}
    assert fol, "no unit of the parent folds has the source %r" % source
    by = {}
    for f in sorted(set(fol.values())):
        by[str(f)] = {"logs": sum(1 for v in fol.values() if v == f)}
    return {"rule": RULE, "seed": parent["seed"], "k": parent["k"], "n_logs": len(fol), "logs_sorted": sorted(fol), "fold_of_log": fol,
            "source_of_log": {u: source for u in fol}, "by_fold": by, "dataset": parent.get("dataset"), "label": parent.get("label", "") + " / " + source,
            "restriction": {"source": source}}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--restrict-from" not in argv:
        return F2.main(argv)
    ap = argparse.ArgumentParser()
    ap.add_argument("--restrict-from", required=True)
    ap.add_argument("--source", required=True, choices=["val", "held_out_train"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    parent = json.load(open(a.restrict_from))
    out = restrict(parent, a.source)
    out.update({"parent_file": os.path.basename(a.restrict_from), "parent_sha256": F2.sha256_path(a.restrict_from),
                "code_sha256": {"c1_folds_v03": F2.sha256_path(os.path.abspath(__file__))}})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    h = F2.sha256_path(a.out)
    with open(a.out + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.out)))
    print(json.dumps({"out": os.path.basename(a.out), "sha256": h, "units": out["n_logs"], "by_fold": out["by_fold"]}))


if __name__ == "__main__":
    main()
