#!/usr/bin/env python3
"""Freeze the method-stage pre-registration (Claude line, v01, 31 Oct 2026): SHA-256 of the code, run scripts, test
outputs, environment listings, every run input of both tracker settings and the pre-freeze counts, written into the
plan's FROZEN_HASHES block; .sha256 sidecar; plan made read-only.
Usage: python m_freeze_v01.py --base <programme folder> --plan 40_PROTOCOL/M_PREREGISTRATION_v02.md
"""
import argparse
import glob
import hashlib
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
    ap.add_argument("--plan", required=True)
    a = ap.parse_args()
    B = a.base
    j = lambda *p: os.path.join(B, *p)
    files = sorted(glob.glob(j("50_CODE", "m", "*.py")) + glob.glob(j("50_CODE", "m", "*.sh"))
                   + glob.glob(j("50_CODE", "m", "tests", "*.py")) + glob.glob(j("50_CODE", "m", "tests", "*.sh")))
    files += [j("50_CODE", "x1", f) for f in ("x1_lib_v03.py", "x1_export_v04.py", "x1_export_v05.py", "fast_convex_v01.py",
                                              "x1_horizon_prep_v01.py", "x1_horizon_prep_v02.py", "run_m_sampletv_export_v01.sh",
                                              "x1_gt_prep_v02.py", "x1_gt_prep_v03.py")]
    files += [j("40_PROTOCOL", "M_PREREGISTRATION_v01.md"), j("40_PROTOCOL", "M_PLAN_HASH_LOG.txt"),
              j("40_PROTOCOL", "X2_PREREGISTRATION_v02.md"), j("10_PROOFS", "P02_METHOD_PROPOSITIONS_v01.md"),
              j("80_LOGS", "pip_freeze_canmot310.txt")]
    data = [j("30_DATA", "x2_gt", "x2_train_gt_v03.json"), j("30_DATA", "x1_gt", "x1_val_gt_v02.json"),
            j("30_DATA", "nuscenes", "v1.0-trainval", "scene.json"),
            j("60_RESULTS", "x2", "x2_horizon_v01.jsonl.gz"), j("60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz")]
    T2 = j("60_RESULTS", "m_export_sampletv_v01")
    data += [os.path.join(T2, "horizon_train_v02.jsonl.gz"), os.path.join(T2, "horizon_val_v02.jsonl.gz"),
             os.path.join(T2, "equiv", "EQUIVALENCE_native_vs_fast.json")]
    for d in (sorted(glob.glob(j("60_RESULTS", "x2_export_train700_fast_v02", "worker*"))) + sorted(glob.glob(j("60_RESULTS", "x1_export_val150_v02", "worker*")))
              + sorted(glob.glob(os.path.join(T2, "train", "worker*"))) + sorted(glob.glob(os.path.join(T2, "val", "worker*")))):
        data += [os.path.join(d, f) for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
    pre = [j("60_RESULTS", "m", "m_sizes_canmot_sc_v01.json"), j("60_RESULTS", "m", "m_sizes_sampletv_v01.json"),
           j("70_TESTS", "m_scratch", "units_v01_reps200.json"), j("70_TESTS", "m_scratch", "refit_v01_reps40.json"),
           j("70_TESTS", "m_scratch", "sim_e2e_v01", "result.json"), j("70_TESTS", "M_SYNTHETIC_TESTS_v01.md"),
           j("70_TESTS", "R07_M_PREFREEZE_REVIEW_v01.md")]
    allf = files + data + pre
    missing = [p for p in allf if not os.path.isfile(p)]
    assert not missing, "missing files: %s" % missing
    n_workers = sum(1 for p in data if p.endswith("x1_tracks.jsonl.gz"))
    assert n_workers == 12 + 3 + 12 + 3, "expected 30 export workers, found %d" % n_workers
    lines = ["%s  %s" % (sha(p), p) for p in allf]
    plan = j(a.plan)
    txt = open(plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN")
    _, tail = rest.split("FROZEN_HASHES_END")
    open(plan, "w", encoding="utf-8", newline="\n").write(head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail)
    h = sha(plan)
    open(plan.replace(".md", ".sha256"), "w").write(h + "  " + os.path.basename(plan) + "\n")
    os.chmod(plan, stat.S_IREAD)
    print("frozen", h, "files", len(allf))


if __name__ == "__main__":
    main()
