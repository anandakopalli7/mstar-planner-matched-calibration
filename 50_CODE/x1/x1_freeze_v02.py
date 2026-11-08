#!/usr/bin/env python3
"""Freeze X1 pre-registration v02 (Claude line, 30 Oct 2026). Inserts the SHA-256 of the code and inputs into the
section 0 block, records the band chosen by the FWER simulation, writes the .sha256 sidecar and makes the file read-only.
Usage: python x1_freeze_v02.py --base <programme folder> --fwer <fwer json>
"""
import argparse
import hashlib
import json
import os
import stat


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    ap.add_argument("--fwer", required=True)
    a = ap.parse_args()
    B = a.base
    files = [os.path.join(B, "50_CODE", "x1", f) for f in ("x1_lib_v02.py", "x1_prefreeze_v02.py", "x1_full_v02.py", "x1_export_val_v02.py",
                                                           "x1_split_detections_v01.py", "x1_gt_prep_v02.py", "x1_freeze_v02.py", "x1_horizon_prep_v01.py")]
    for w in range(3):
        d = os.path.join(B, "60_RESULTS", "x1_export_val150_v02", "worker%d" % w)
        files += [os.path.join(d, f) for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
    files += [os.path.join(B, "30_DATA", "x1_gt", "x1_val_gt_v02.json"), os.path.join(B, "30_DATA", "nuscenes", "v1.0-trainval", "scene.json"),
              os.path.join(B, "30_DATA", "det_subsets_val150", "split_receipt.json"),
              os.path.join(B, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"), os.path.join(B, "60_RESULTS", "x1", "x1_sizes_v02.json"), os.path.join(B, "60_RESULTS", "x1", "x1_fwer_v02.json"),
              os.path.join(B, "60_RESULTS", "x1", "x1_oc_q4_v02.json"), os.path.join(B, "60_RESULTS", "x1", "x1_selftest_v02.json")]
    fw = json.load(open(a.fwer))
    band = "linear" if fw["primary_linear_band"]["ok"] else "logit"
    lines = ["setting  band=%s" % band] + ["%s  %s" % (sha(p), p) for p in files]
    pre = os.path.join(B, "40_PROTOCOL", "X1_PREREGISTRATION_v02.md")
    txt = open(pre, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN")
    _, tail = rest.split("FROZEN_HASHES_END")
    txt = head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail
    open(pre, "w", encoding="utf-8").write(txt)
    h = sha(pre)
    open(pre.replace(".md", ".sha256"), "w").write(h + "  X1_PREREGISTRATION_v02.md\n")
    os.chmod(pre, stat.S_IREAD)
    print("frozen", h, "band", band, "files", len(files))


if __name__ == "__main__":
    main()
