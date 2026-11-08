#!/usr/bin/env python3
"""Freeze the method-stage pre-registration v03 (Claude line, v02, 31 Oct 2026). It writes the SHA-256 of these files into
the plan's FROZEN_HASHES block:
- code, run scripts and tests;
- T1, T2 and T3 export and propagation code;
- the plans v01 and v02, their hash log, P02, and reviews R07 and R07b;
- the environment listing;
- every run input of the three tracker settings;
- the pre-freeze counts and the test outputs.
It also writes the .sha256 sidecar and makes the plan read-only. The freeze hash goes into M_FREEZE_RECORD_v03.txt, which is
not itself frozen, so that recording it later cannot break the check (R07 m14).
Usage: python m_freeze_v02.py --base <programme folder>
"""
import argparse
import datetime as dt
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
    a = ap.parse_args()
    B = a.base
    j = lambda *p: os.path.join(B, *p)
    files = sorted(glob.glob(j("50_CODE", "m", "*.py")) + glob.glob(j("50_CODE", "m", "*.sh"))
                   + glob.glob(j("50_CODE", "m", "tests", "*.py")) + glob.glob(j("50_CODE", "m", "tests", "*.sh")))
    files += [j("50_CODE", "x1", f) for f in ("x1_lib_v03.py", "x1_export_v04.py", "x1_export_v05.py", "x1_export_v06.py", "tests_make_export_v06.py",
                                              "fast_convex_v01.py", "x1_horizon_prep_v01.py", "x1_horizon_prep_v02.py", "x1_horizon_prep_v03.py",
                                              "run_m_sampletv_export_v01.sh", "run_m_polymot_export_v01.sh", "x1_gt_prep_v02.py", "x1_gt_prep_v03.py")]
    files += [j("40_PROTOCOL", "M_PREREGISTRATION_v01.md"), j("40_PROTOCOL", "M_PREREGISTRATION_v02.md"), j("40_PROTOCOL", "M_PLAN_HASH_LOG.txt"),
              j("40_PROTOCOL", "X2_PREREGISTRATION_v02.md"), j("10_PROOFS", "P02_METHOD_PROPOSITIONS_v02.md"),
              j("70_TESTS", "R07_M_PREFREEZE_REVIEW_v01.md"), j("70_TESTS", "R07B_M_PREFREEZE_REREVIEW_v01.md"), j("80_LOGS", "pip_freeze_canmot310.txt")]
    data = [j("30_DATA", "x2_gt", "x2_train_gt_v03.json"), j("30_DATA", "x1_gt", "x1_val_gt_v02.json"), j("30_DATA", "nuscenes", "v1.0-trainval", "scene.json"),
            j("60_RESULTS", "x2", "x2_horizon_v01.jsonl.gz"), j("60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz")]
    T2, T3 = j("60_RESULTS", "m_export_sampletv_v01"), j("60_RESULTS", "m_export_polymot_v01")
    data += [os.path.join(T2, "horizon_train_v02.jsonl.gz"), os.path.join(T2, "horizon_val_v02.jsonl.gz"), os.path.join(T2, "equiv", "EQUIVALENCE_native_vs_fast.json"),
             os.path.join(T3, "horizon_train_v03.jsonl.gz"), os.path.join(T3, "horizon_val_v03.jsonl.gz"), os.path.join(T3, "equiv", "EQUIVALENCE_native_vs_fast.json")]
    for d in (sorted(glob.glob(j("60_RESULTS", "x2_export_train700_fast_v02", "worker*"))) + sorted(glob.glob(j("60_RESULTS", "x1_export_val150_v02", "worker*")))
              + sorted(glob.glob(os.path.join(T2, "train", "worker*"))) + sorted(glob.glob(os.path.join(T2, "val", "worker*")))
              + sorted(glob.glob(os.path.join(T3, "train", "worker*"))) + sorted(glob.glob(os.path.join(T3, "val", "worker*")))):
        data += [os.path.join(d, f) for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
    S = j("70_TESTS", "m_scratch")
    pre = [j("60_RESULTS", "m", "m_sizes_%s_v02.json" % t) for t in ("canmot_sc", "sampletv", "polymot")]
    pre += [os.path.join(S, f) for f in ("units_v02_reps200.json", "refit_v02_reps30.json", "b8_v02_reps20.json", "oc_v01_T1.json", "oc_v01_T3.json",
                                         "freeze_check_v01.json")]
    pre += [os.path.join(S, "sim_e2e_v02", f) for f in ("result.json", "decision.json", "sizes.json", "check.json")]
    pre += [j("70_TESTS", "M_SYNTHETIC_TESTS_v02.md")]
    allf = files + data + pre
    missing = [p for p in allf if not os.path.isfile(p)]
    assert not missing, "missing files: %s" % missing
    n_workers = sum(1 for p in data if p.endswith("x1_tracks.jsonl.gz"))
    assert n_workers == 45, "expected 45 export workers (3 settings x 15), found %d" % n_workers
    lines = ["%s  %s" % (sha(p), p) for p in allf]
    plan = j("40_PROTOCOL", "M_PREREGISTRATION_v03.md")
    txt = open(plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN")
    _, tail = rest.split("FROZEN_HASHES_END")
    open(plan, "w", encoding="utf-8", newline="\n").write(head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail)
    h = sha(plan)
    open(plan.replace(".md", ".sha256"), "w").write(h + "  " + os.path.basename(plan) + "\n")
    os.chmod(plan, stat.S_IREAD)
    open(j("40_PROTOCOL", "M_FREEZE_RECORD_v03.txt"), "a").write("%s  %s  M_PREREGISTRATION_v03.md frozen, %d files\n" % (
        dt.datetime.now().astimezone().isoformat(timespec="seconds"), h, len(allf)))
    print("frozen", h, "files", len(allf))


if __name__ == "__main__":
    main()
