#!/usr/bin/env python3
"""av2_c1_gt_list_v01 (Claude line, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md section 12): writes
30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt, the prepared ground-truth files of the 375-log step for the quarantine's
--extra list: one line "<sha256>  <workspace-relative path>" per file (sha256sum format; '#' lines are comments). Hashes the
files' bytes only; opens no content. Refuses to overwrite.
Usage: python -I -B av2_c1_gt_list_v01.py --out <txt>
"""
import argparse
import hashlib
import os
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FILES = [  # (path relative to the workspace, expected SHA-256 or None)
    ("30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json", None),
    ("30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_gt_v01.feather",
     "a9d85a547f536d97fb1c756643272b5f53fdc1bc55385ec7c7554e54aa1a362e"),
    ("30_DATA/av2_det_owncp_v01/held225/av2held225_owncp_centerpoint_gt_v01.feather",
     "8cb86154f41c59187ff62ab82159ec3093c094897da94d440106e9b3862ec5ef"),
]
ALREADY = [  # already handled by the plan (named by the 150-log stage-A manifests / already on the extra list)
    "30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json",
    "30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_gt_v01.feather",
]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        raise SystemExit("refused: %s exists" % a.out)
    lines = ["# Prepared AV2 ground-truth files of the 375-log C1 tracker step (av2_c1_gt_list_v01, design v04 section 12).",
             "# Format: <sha256>  <path relative to the workspace>. Pass every path to c1_quarantine_v02 --extra.",
             "# The note also names files the plan already handles (not repeated here as entries):"]
    for r in ALREADY:
        p = os.path.join(W, *r.split("/"))
        lines.append("#   already handled: %s  %s" % (sha(p) if os.path.exists(p) else "(absent)", r))
    lines.append("# Public annotations.feather files of 30_DATA/av2_val and 30_DATA/av2_train225 stay outside (plan section 8.4).")
    for r, exp in FILES:
        h = sha(os.path.join(W, *r.split("/")))
        if exp is not None and h != exp:
            raise SystemExit("hash differs from the recorded one: %s %s" % (r, h))
        lines.append("%s  %s" % (h, r))
    with open(a.out, "w", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
