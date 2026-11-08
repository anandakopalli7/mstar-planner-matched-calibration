#!/usr/bin/env python3
"""K7 freeze (Claude line, v01, 1 Nov 2026). Checks the pre-freeze conditions, writes the hash block into the K7 plan, then
the plan's .sha256 sidecar and the freeze record K7_FREEZE_RECORD_v01.txt (UTC times, R10 E5). Conditions:
  * no confirmatory K7 output exists yet (60_RESULTS/k7_main_v01 absent or empty);
  * the K7 harness tests pass (tests/test_k7_sim_v01.py is re-run here and must print ALL_PASS);
  * the generators reproduce k7_sim_v01.py and k7_run_v01.py from the frozen K6 files (in a temporary copy);
  * each K7 fit file names the sha256 of the K7 item file it was fitted on, and that file is frozen;
  * the K7 OC acceptance holds (A1 <= 0.10 and family >= F_MIN in every layout);
  * the development check exists.
Usage: python -B k7_freeze_v01.py --plan <K7_PREREGISTRATION_v02.md> --oc <k7_oc_v03.json> --dev <k7_dev_check_v01.json>
"""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K7 = os.path.join(W, "50_CODE", "k7")
K6 = os.path.join(W, "50_CODE", "k6")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frozen_files():
    j = lambda *a: os.path.join(W, *a)  # noqa: E731
    files = [os.path.join(K7, f) for f in ("k7_sim_v01.py", "k7_run_v01.py", "k7_analyse_v01.py", "k7_analyse_v02.py", "k7_items_v01.py",
                                           "k7_fit_v01.py", "k7_design_counts_v01.py", "k7_design_counts_v02.py", "k7_items_v02.py",
                                           "k7_freeze_v01.py", "run_k7_prep_v01.sh", "run_k7_main_v01.sh")]
    files += [os.path.join(K7, "tests", f) for f in ("make_k7_sim_v01.py", "make_k7_run_v01.py", "test_k7_sim_v01.py", "k7_oc_v01.py",
                                                     "k7_oc_v02.py", "k7_oc_v03.py", "k7_dev_check_v01.py", "k7_dev_axis_diag_v01.py")]
    files += [j("40_PROTOCOL", "K7_PREREGISTRATION_v01.md"), j("70_TESTS", "k7_scratch", "make_k7_plan_v02.py"),
              j("70_TESTS", "k7_scratch", "k7_oc_v03.json"), j("70_TESTS", "k7_scratch", "r12", "r12_items_vs_records_dev.json"),
              j("70_TESTS", "k7_scratch", "r12", "r12_rho_k6.json"), j("70_TESTS", "k7_scratch", "r12", "r12_oc_table.md")]
    files += [os.path.join(K6, f) for f in ("k6_sim_v02.py", "k6_run_v02.py", "k6_analyse_v02.py", "k6_fit_v01.py", "k6_items_v01.py",
                                            "k6_cache_v02.py")]
    files += [j("50_CODE", "x1", "x1_lib_v03.py"), j("50_CODE", "m", "m_lib_v04.py"), j("50_CODE", "m", "m_data_v04.py"),
              j("40_PROTOCOL", "K6_PREREGISTRATION_v02.md"), j("40_PROTOCOL", "K6_PREREGISTRATION_v02.sha256"),
              j("40_PROTOCOL", "K6_FREEZE_RECORD_v02.txt"), j("60_RESULTS", "k6_main_v02", "k6_result_v02.json"),
              j("40_PROTOCOL", "K7_PLAN_HASH_LOG.txt"),
              j("90_DECISIONS", "D10_K6_DECISION_REPORT_v01.md"), j("90_DECISIONS", "D11_K6_CONFIDENCE_AND_K7_ROUTE_v01.md"),
              j("70_TESTS", "R10_K6_RESULTS_REVIEW_v01.md"), j("70_TESTS", "R11A_K6_POWER_RULE_AUDIT_v01.md"),
              j("70_TESTS", "R11B_K6_RECORD_PIPELINE_AUDIT_v01.md"), j("70_TESTS", "R12_K7_PREFREEZE_REVIEW_v01.md"),
              j("70_TESTS", "k7_scratch", "k7_tests_v01.json"), j("70_TESTS", "k7_scratch", "k7_oc_v02.json"),
              j("70_TESTS", "k7_scratch", "k7_oc_v01_superseded_partial.log"),
              j("70_TESTS", "k7_scratch", "k7_dev_check_v01.json"), j("70_TESTS", "k7_scratch", "k7_dev_axis_diag_v01.json"),
              j("70_TESTS", "k7_scratch", "k7_design_counts_v01.json"), j("70_TESTS", "k7_scratch", "k7_design_counts_v02.json")]
    for t in ("t1", "t3"):
        files += [j("30_DATA", "k7", "k7_items_%s_v01.npz" % t), j("30_DATA", "k7", "k7_items_%s_v01_summary.json" % t),
                  j("60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t), j("60_RESULTS", "k6_items_v01", "k6_fits_%s_v01.json" % t)]
        for sp in ("train", "val"):
            files.append(j("30_DATA", "k6", "cache_v02_%s_%s" % (t, sp), "MANIFEST.json"))
    for extra in ("R12B_K7_PREFREEZE_REREVIEW_v01.md", "R12C_K7_PREFREEZE_CHECK_v01.md", "R12D_K7_PREFREEZE_CHECK_v01.md"):
        if os.path.exists(j("70_TESTS", extra)):
            files.append(j("70_TESTS", extra))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--oc", required=True)
    ap.add_argument("--dev", required=True)
    a = ap.parse_args()
    main_out = os.path.join(W, "60_RESULTS", "k7_main_v01")
    assert not (os.path.isdir(main_out) and os.listdir(main_out)), "confirmatory K7 output already exists"
    py = sys.executable
    r = subprocess.run([py, "-B", os.path.join(K7, "tests", "test_k7_sim_v01.py"), os.path.join(W, "70_TESTS", "k7_scratch", "k7_tests_v01.json")],
                       capture_output=True, text=True, cwd=os.path.join(K7, "tests"))
    assert "ALL_PASS" in r.stdout, "K7 harness tests fail:\n" + r.stdout[-2000:]
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "k7", "tests"))
        os.makedirs(os.path.join(tmp, "k6"))
        for f in ("k6_sim_v02.py", "k6_run_v02.py"):
            shutil.copy(os.path.join(K6, f), os.path.join(tmp, "k6"))
        for g in ("make_k7_sim_v01.py", "make_k7_run_v01.py"):
            shutil.copy(os.path.join(K7, "tests", g), os.path.join(tmp, "k7", "tests"))
            subprocess.run([py, "-B", os.path.join(tmp, "k7", "tests", g)], check=True, capture_output=True)
        for f in ("k7_sim_v01.py", "k7_run_v01.py"):
            assert sha(os.path.join(tmp, "k7", f)) == sha(os.path.join(K7, f)), "the generators do not reproduce " + f
    for t in ("t1", "t3"):
        fits = json.load(open(os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t)))
        assert fits["items_sha256"] == sha(os.path.join(W, "30_DATA", "k7", "k7_items_%s_v01.npz" % t)), "K7 fits %s not from the frozen items" % t
        assert fits["k6fits_sha256"] == sha(os.path.join(W, "60_RESULTS", "k6_items_v01", "k6_fits_%s_v01.json" % t)), "K7 fits %s: K6 folds differ" % t
    assert os.path.abspath(a.oc) == os.path.abspath(os.path.join(W, "70_TESTS", "k7_scratch", "k7_oc_v03.json")), "the OC must be the frozen file"
    oc = json.load(open(a.oc))
    assert oc["rule"] == "k7_analyse_v02.hk1_rule", "the OC must simulate the coded rule"
    assert oc["acceptance_all"], "K7 OC acceptance not met: %s" % oc["acceptance"]
    assert os.path.abspath(a.dev) == os.path.abspath(os.path.join(W, "70_TESTS", "k7_scratch", "k7_dev_check_v01.json")), "the development check must be the frozen file"
    assert os.path.abspath(a.plan) == os.path.abspath(os.path.join(W, "40_PROTOCOL", "K7_PREREGISTRATION_v02.md")), "the plan must be K7 plan v02"
    txt0 = open(a.plan, encoding="utf-8").read()
    for ph in ("PENDING", "(Filled", "(Pre-freeze review"):
        assert ph not in txt0.split("FROZEN_HASHES_BEGIN")[0], "placeholder left in the plan: " + ph
    log = os.path.join(W, "40_PROTOCOL", "K7_PLAN_HASH_LOG.txt")
    empty = txt0.split("FROZEN_HASHES_BEGIN")[0] + "FROZEN_HASHES_BEGIN\nFROZEN_HASHES_END" + txt0.split("FROZEN_HASHES_END")[1]
    with open(log, "a", encoding="utf-8") as f:
        f.write("%s  %s  K7_PREREGISTRATION_v02.md  final text before the freeze (empty hash block)\n"
                % (datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"), hashlib.sha256(empty.encode("utf-8")).hexdigest()))
    files = frozen_files()
    for p in files:
        assert os.path.exists(p), "missing " + p
    block = "\n".join("%s  %s" % (sha(p), p) for p in files)
    txt = open(a.plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN")
    _, tail = rest.split("FROZEN_HASHES_END")
    txt = head + "FROZEN_HASHES_BEGIN\n" + block + "\nFROZEN_HASHES_END" + tail
    open(a.plan, "w", encoding="utf-8", newline="\n").write(txt)
    h = sha(a.plan)
    open(a.plan.replace(".md", ".sha256"), "w").write("%s  %s\n" % (h, os.path.basename(a.plan)))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    rec = os.path.join(os.path.dirname(a.plan), "K7_FREEZE_RECORD_v01.txt")
    with open(rec, "w", encoding="utf-8") as f:
        f.write("K7 plan v01 frozen %s\nsha256 %s\nfiles %d\nK7 harness tests ALL_PASS\ngenerators reproduce k7_sim_v01 and k7_run_v01\n"
                "K7 fits bound to the frozen items and K6 folds\nOC A1 max %.3f\n" % (stamp, h, len(files), oc["acceptance"]["A1_max"]))
    print("FROZEN", h, len(files), "files")


if __name__ == "__main__":
    main()
