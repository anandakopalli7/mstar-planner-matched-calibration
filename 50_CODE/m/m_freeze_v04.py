#!/usr/bin/env python3
"""Freeze the method-stage pre-registration v05 (Claude line, v04, 31 Oct 2026). It writes the SHA-256 of these files into
the plan's FROZEN_HASHES block:
- code, run scripts and tests;
- the T2/T3 export and propagation code, and the CANMOT files that define T3's predictions;
- the plans v01-v04 and their makers, their hash log, P02 v03, and reviews R07, R07b and R07c;
- the environment listing;
- every run input of the three tracker settings, the split receipts and the equivalence checks;
- the pre-freeze counts and the test outputs.
Every test JSON must report all_ok (R07b N-m9), and the OC merges must report acceptance.all at the derived eps, which must
equal m_lib_v03.EPS_POOLED (plan v05 section 9).
It writes the .sha256 sidecar and makes the plan read-only. The freeze hash goes into M_FREEZE_RECORD_v05.txt, which is not
itself frozen.
Usage: python m_freeze_v04.py --base <programme folder>
"""
import argparse
import datetime as dt
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
    a = ap.parse_args()
    B = a.base
    j = lambda *p: os.path.join(B, *p)
    files = sorted(glob.glob(j("50_CODE", "m", "*.py")) + glob.glob(j("50_CODE", "m", "*.sh"))
                   + glob.glob(j("50_CODE", "m", "tests", "*.py")) + glob.glob(j("50_CODE", "m", "tests", "*.sh")))
    files += [j("50_CODE", "x1", f) for f in ("x1_lib_v03.py", "x1_export_v04.py", "x1_export_v05.py", "x1_export_v06.py", "tests_make_export_v06.py",
                                              "fast_convex_v01.py", "x1_horizon_prep_v01.py", "x1_horizon_prep_v02.py", "x1_horizon_prep_v03.py",
                                              "run_m_sampletv_export_v01.sh", "run_m_polymot_export_v01.sh", "x1_gt_prep_v02.py", "x1_gt_prep_v03.py",
                                              "x1_split_detections_stream_v03.py")]
    C = j("50_CODE", "third_party", "CANMOT")
    files += [os.path.join(C, *p) for p in (("src", "canmot", "motion_module", "motion_model.py"), ("src", "canmot", "motion_module", "kalman_filter.py"),
                                            ("src", "canmot", "data", "script", "NUSC_CONSTANT.py"), ("config", "experiment", "paper", "baseline", "poly_mot.yaml"),
                                            ("config", "poly_mot", "nusc_config_poly_mot.yaml"), ("config", "poly_mot", "nusc_config_rotate_cov_cv.yaml"),
                                            ("config", "experiment", "paper", "local", "canmot", "sc.yaml"),
                                            ("config", "experiment", "paper", "local", "sample", "trainval.yaml"),
                                            ("src", "canmot", "pre_processing", "nusc_data_conversion.py"))]
    files += [j("40_PROTOCOL", f) for f in ("M_PREREGISTRATION_v01.md", "M_PREREGISTRATION_v02.md", "M_PREREGISTRATION_v03.md", "M_PREREGISTRATION_v04.md",
                                            "M_PLAN_HASH_LOG.txt", "X2_PREREGISTRATION_v02.md", "make_plan_v04.py", "make_plan_v05.py")]
    files += sorted(glob.glob(j("40_PROTOCOL", "make_plan_v05_r07c_edits.json")))
    files += [j("10_PROOFS", "P02_METHOD_PROPOSITIONS_v03.md"), j("70_TESTS", "R07_M_PREFREEZE_REVIEW_v01.md"),
              j("70_TESTS", "R07B_M_PREFREEZE_REREVIEW_v01.md"), j("70_TESTS", "R07C_M_PREFREEZE_CHECK_v01.md"), j("80_LOGS", "pip_freeze_canmot310.txt")]
    data = [j("30_DATA", "x2_gt", "x2_train_gt_v03.json"), j("30_DATA", "x1_gt", "x1_val_gt_v02.json"), j("30_DATA", "nuscenes", "v1.0-trainval", "scene.json"),
            j("30_DATA", "det_subsets_train700", "split_receipt.json"), j("30_DATA", "det_subsets_val150", "split_receipt.json"),
            j("60_RESULTS", "x2", "x2_horizon_v01.jsonl.gz"), j("60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"),
            j("60_RESULTS", "x1_export_val150_fast_v04", "EQUIVALENCE_vs_native_v02.json")]
    T2, T3 = j("60_RESULTS", "m_export_sampletv_v01"), j("60_RESULTS", "m_export_polymot_v01")
    data += [os.path.join(T2, "horizon_train_v02.jsonl.gz"), os.path.join(T2, "horizon_val_v02.jsonl.gz"), os.path.join(T2, "equiv", "EQUIVALENCE_native_vs_fast.json"),
             os.path.join(T3, "horizon_train_v03.jsonl.gz"), os.path.join(T3, "horizon_val_v03.jsonl.gz"), os.path.join(T3, "equiv", "EQUIVALENCE_native_vs_fast.json")]
    for d in (sorted(glob.glob(j("60_RESULTS", "x2_export_train700_fast_v02", "worker*"))) + sorted(glob.glob(j("60_RESULTS", "x1_export_val150_v02", "worker*")))
              + sorted(glob.glob(os.path.join(T2, "train", "worker*"))) + sorted(glob.glob(os.path.join(T2, "val", "worker*")))
              + sorted(glob.glob(os.path.join(T3, "train", "worker*"))) + sorted(glob.glob(os.path.join(T3, "val", "worker*")))):
        data += [os.path.join(d, f) for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
    S = j("70_TESTS", "m_scratch")
    pre = [j("60_RESULTS", "m", "m_sizes_%s_v03.json" % t) for t in ("canmot_sc", "sampletv", "polymot")]
    tests = [os.path.join(S, f) for f in ("units_v03_reps200.json", "refit_v03_reps30.json", "b8_v03_reps20.json", "freeze_check_v02.json",
                                          "export_velocity_v01.json", os.path.join("sim_e2e_v03", "check.json"))]
    ocs = [os.path.join(S, "oc_v03_T1.json"), os.path.join(S, "oc_v03_T3.json")]
    pre += tests + ocs + [os.path.join(S, "sim_e2e_v03", f) for f in ("result.json", "decision.json", "sizes.json")]
    pre += sorted(glob.glob(os.path.join(S, "oc_v02", "*.json"))) + [os.path.join(S, "eps_v01.json"), j("70_TESTS", "M_SYNTHETIC_TESTS_v04.md")]
    allf = files + data + pre
    missing = [p for p in allf if not os.path.isfile(p)]
    assert not missing, "missing files: %s" % missing
    for p in tests:
        assert json.load(open(p)).get("all_ok") is True, "test output not all_ok: " + p
    eps = json.load(open(os.path.join(S, "eps_v01.json")))["eps"]
    import sys
    sys.path.insert(0, os.path.join(B, "50_CODE", "m"))
    import m_lib_v03
    assert abs(m_lib_v03.EPS_POOLED - eps) < 1e-12, "m_lib_v03.EPS_POOLED differs from the derived eps"
    for p in ocs:
        oc = json.load(open(p))
        assert oc["acceptance"]["all"] is True and oc["eps_used"] == eps, "OC acceptance criteria not met at the derived eps: " + p
    n_workers = sum(1 for p in data if p.endswith("x1_tracks.jsonl.gz"))
    assert n_workers == 45, "expected 45 export workers (3 settings x 15), found %d" % n_workers
    lines = ["%s  %s" % (sha(p), p) for p in allf]
    plan = j("40_PROTOCOL", "M_PREREGISTRATION_v05.md")
    txt = open(plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN")
    _, tail = rest.split("FROZEN_HASHES_END")
    open(plan, "w", encoding="utf-8", newline="\n").write(head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail)
    h = sha(plan)
    open(plan.replace(".md", ".sha256"), "w").write(h + "  " + os.path.basename(plan) + "\n")
    os.chmod(plan, stat.S_IREAD)
    open(j("40_PROTOCOL", "M_FREEZE_RECORD_v05.txt"), "a").write("%s  %s  M_PREREGISTRATION_v05.md frozen, %d files\n" % (
        dt.datetime.now().astimezone().isoformat(timespec="seconds"), h, len(allf)))
    print("frozen", h, "files", len(allf))


if __name__ == "__main__":
    main()
