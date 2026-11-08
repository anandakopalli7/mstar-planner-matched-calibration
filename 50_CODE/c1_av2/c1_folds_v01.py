#!/usr/bin/env python3
"""C1 cross-fitting folds (Claude line, c1_folds_v01, 2 Nov 2026). C1 v04 sections 3 and 11.3; D16 v08 Choice 22.

Rule (fixed before any outcome): the log ids are sorted; NumPy default_rng(seed).permutation(n) orders them; the permuted list is
cut into k consecutive blocks (np.array_split; 5 x 75 for the 375 logs); block j is fold j. Not stratified by source; the source of
each log (held-out train / validation) is recorded and reported only. Seed 20261112 (C1 v04 section 5.3).
Input: a JSON or text file of log ids, one source per id: {"logs": {"<id>": "<source>", ...}} or lines "<id> <source>".
Output: a JSON with the rule, seed, sorted ids, permutation, fold_of_log, source_of_log, per-fold counts and source shares, and the
input's SHA-256; the output's SHA-256 is printed and written to <out>.sha256.
Usage: python -B c1_folds_v01.py --logs <file> --out <json> [--seed 20261112 --k 5]
"""
import argparse
import hashlib
import json
import os

import numpy as np

SEED = 20261112
K = 5
RULE = ("sorted log ids permuted by numpy default_rng(seed).permutation(n), cut into k consecutive blocks (np.array_split); "
        "block j = fold j; not stratified by source (C1 v04 section 11.3; D16 Choice 22)")


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_logs(path):
    txt = open(path, encoding="utf-8").read()
    try:
        d = json.loads(txt)
        return {str(k): str(v) for k, v in d["logs"].items()}
    except ValueError:
        out = {}
        for ln in txt.splitlines():
            if ln.strip():
                p = ln.split()
                out[p[0]] = p[1] if len(p) > 1 else "unknown"
        return out


def make_folds(source_of_log, seed=SEED, k=K):
    logs = sorted(source_of_log)
    assert len(set(logs)) == len(logs), "a log id appears twice"
    perm = np.random.default_rng(seed).permutation(len(logs))
    blocks = np.array_split(perm, k)
    fold_of_log = {}
    for j, b in enumerate(blocks):
        for i in b.tolist():
            fold_of_log[logs[i]] = j
    by_fold = {str(j): {"logs": int(len(b)), "sources": {s: int(sum(1 for i in b.tolist() if source_of_log[logs[i]] == s))
                                                          for s in sorted(set(source_of_log.values()))}} for j, b in enumerate(blocks)}
    return {"rule": RULE, "seed": int(seed), "k": int(k), "n_logs": len(logs), "logs_sorted": logs, "permutation": perm.tolist(),
            "fold_of_log": fold_of_log, "source_of_log": dict(source_of_log), "by_fold": by_fold}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--logs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--k", type=int, default=K)
    ap.add_argument("--label", default="C1 AV2 375-log confirmation set")
    a = ap.parse_args(argv)
    out = make_folds(read_logs(a.logs), a.seed, a.k)
    out.update({"label": a.label, "input": os.path.abspath(a.logs), "input_sha256": sha256_path(a.logs),
                "code_sha256": sha256_path(os.path.abspath(__file__))})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
    h = sha256_path(a.out)
    with open(a.out + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.out)))
    print(json.dumps({"out": os.path.abspath(a.out), "sha256": h, "by_fold": out["by_fold"]}))


if __name__ == "__main__":
    main()
