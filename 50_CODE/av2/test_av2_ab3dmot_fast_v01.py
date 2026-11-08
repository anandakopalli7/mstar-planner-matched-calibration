#!/usr/bin/env python3
"""test_av2_ab3dmot_fast_v01: av2_ab3dmot_v04 with and without the exact association shim L2 give identical outputs
(Claude line, 2 Nov 2026). Compares, line for line, both exports (ab3dmot_det, ab3dmot_kf) and the horizon8 file of two
runs on the same logs. Usage: python -B test_av2_ab3dmot_fast_v01.py --slow <out dir> --fast <out dir> --out <json>
"""
import argparse
import gzip
import json
import os
import sys


def lines(p):
    with gzip.open(p, "rt") as f:
        return f.read().splitlines()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slow", required=True)
    ap.add_argument("--fast", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rep = {"slow": a.slow, "fast": a.fast, "files": {}}
    for rel in ("ab3dmot_det/worker0/x1_tracks.jsonl.gz", "ab3dmot_kf/worker0/x1_tracks.jsonl.gz", "horizon8_ab3dmot_kf_worker0.jsonl.gz"):
        x, y = lines(os.path.join(a.slow, rel)), lines(os.path.join(a.fast, rel))
        d = sum(p != q for p, q in zip(x, y)) + abs(len(x) - len(y))
        rep["files"][rel] = {"lines_slow": len(x), "lines_fast": len(y), "different": d}
    rep["identical"] = all(v["different"] == 0 and v["lines_slow"] > 0 for v in rep["files"].values())
    json.dump(rep, open(a.out, "w"), indent=1)
    print(json.dumps(rep))


if __name__ == "__main__":
    sys.exit(main())
