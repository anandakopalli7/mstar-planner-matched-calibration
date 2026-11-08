#!/usr/bin/env python3
"""Freeze X2 pre-registration v01 (Claude line, 30 Oct 2026): insert SHA-256 of code and inputs, record the band setting,
write the .sha256 sidecar, make the file read-only.
Usage: python x2_freeze_v01.py --base <programme folder> --fwer <x2 fwer json>
"""
import argparse
import glob
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
    code = ["x1_lib_v02.py", "x1_full_v02.py", "x1_prefreeze_v02.py", "x2_full_v01.py", "x2_prefreeze_v01.py", "x2_freeze_v01.py",
            "x1_export_v04.py", "fast_convex_v01.py", "x1_split_detections_stream_v03.py", "x1_gt_prep_v03.py", "x1_horizon_prep_v01.py"]
    files = [os.path.join(B, "50_CODE", "x1", f) for f in code]
    E = os.path.join(B, "60_RESULTS", "x2_export_train700_fast_v02")
    for d in sorted(glob.glob(os.path.join(E, "worker*"))):
        files += [os.path.join(d, f) for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
    R = os.path.join(B, "60_RESULTS", "x2")
    files += [os.path.join(B, "30_DATA", "x2_gt", "x2_train_gt_v03.json"), os.path.join(B, "30_DATA", "nuscenes", "v1.0-trainval", "scene.json"),
              os.path.join(B, "30_DATA", "det_subsets_train700", "split_receipt.json"),
              os.path.join(B, "60_RESULTS", "x1_export_val150_fast_v04", "EQUIVALENCE_vs_native_v02.json"),
              os.path.join(R, "x2_horizon_v01.jsonl.gz"), os.path.join(R, "x2_sizes_v01.json"), os.path.join(R, "x2_fwer_v01.json"),
              os.path.join(R, "x2_oc_q4_v01.json")]
    fw = json.load(open(a.fwer))
    band = "linear" if fw["primary_linear_band"]["ok"] else "logit"
    lines = ["setting  band=%s" % band] + ["%s  %s" % (sha(p), p) for p in files]
    pre = os.path.join(B, "40_PROTOCOL", "X2_PREREGISTRATION_v01.md")
    txt = open(pre, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN")
    _, tail = rest.split("FROZEN_HASHES_END")
    open(pre, "w", encoding="utf-8").write(head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail)
    h = sha(pre)
    open(pre.replace(".md", ".sha256"), "w").write(h + "  X2_PREREGISTRATION_v01.md\n")
    os.chmod(pre, stat.S_IREAD)
    print("frozen", h, "band", band, "files", len(files))


if __name__ == "__main__":
    main()
