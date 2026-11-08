#!/usr/bin/env python3
"""av2_c1_logs_v01 (Claude line, 5 Nov 2026): the 375-log C1 confirmation list (AV2_TRACKER_PORT_DESIGN_v04.md section 1).

held_out_225 = the split file's `held_out_225` (the first 225 of the seeded permutation; checked: 225 distinct, disjoint from
`train_475`); val_150 = the log folders of 30_DATA/av2_val (directories only). Writes {"logs": sorted 375, "held_out_225":
sorted, "val_150": sorted, split file path and SHA-256, rule} and a .sha256 file beside it. Reads no data file.
Usage: python -I -B av2_c1_logs_v01.py --split <AV2_TRAIN_SPLIT_v01.json> --out <C1_LOGS_375_v01.json>
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import av2_common_v02 as C  # noqa: E402

SPLIT_SHA256 = "3771664f8aca73d4829e9867147af2c84e8d87fd95d5472e3b1c1bc443700f72"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit("refused: %s exists" % a.out)
    sh = C.sha256_path(a.split)
    assert sh == SPLIT_SHA256, sh
    sp = json.load(open(a.split))
    held = [str(x) for x in sp["held_out_225"]]
    assert len(held) == 225 and len(set(held)) == 225
    assert not set(held) & set(sp["train_475"]) and len(set(held) | set(sp["train_475"])) == 700
    val = C.val_logs()
    assert len(val) == 150
    assert not set(held) & set(val)
    logs = sorted(held + val)
    assert len(logs) == 375 and len(set(logs)) == 375
    out = {"note": "C1 confirmation set (plan v07b section 1.1): 225 held-out AV2 Sensor train logs (own detector never saw them) "
                   "+ 150 AV2 Sensor val logs; sorted (av2_c1_logs_v01)",
           "rule": {"held_out_225": "AV2_TRAIN_SPLIT_v01.json key held_out_225 (first 225 of sorted(700) permuted with "
                                    "numpy default_rng(20261102)), sorted",
                    "val_150": "log folders of 30_DATA/av2_val, sorted"},
           "split_file": os.path.relpath(os.path.abspath(a.split), C.W_ROOT).replace(os.sep, "/"), "split_sha256": sh,
           "n_logs": 375, "logs": logs, "held_out_225": sorted(held), "val_150": val}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1)
    h = hashlib.sha256(open(a.out, "rb").read()).hexdigest()
    with open(a.out[:-5] + ".sha256" if a.out.endswith(".json") else a.out + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.out)))
    print("wrote", a.out, h, "logs", len(logs), "held", len(held), "val", len(val))


if __name__ == "__main__":
    sys.exit(main())
