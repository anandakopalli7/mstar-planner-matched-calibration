#!/usr/bin/env python3
"""K6 freeze (Claude line, v01, 31 Oct 2026). Checks the pre-freeze conditions, writes the hash block into the K6 plan,
then the plan's .sha256 sidecar and a freeze record. Conditions:
  * the harness tests pass (tests/test_k6_sim_v01.py is re-run here and must print ALL_PASS);
  * the 8-step horizon identity check passed;
  * the OC acceptance in the plan holds in the OC result (A1 <= 0.10 in every layout);
  * the development check exists;
  * no confirmatory run output exists yet (60_RESULTS/k6_main_v01 is absent or empty).
Usage: python -B k6_freeze_v01.py --plan <K6_PREREGISTRATION_v01.md> --oc <json> --dev <json>
"""
import argparse
import datetime
import glob
import hashlib
import json
import os
import subprocess
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
K = os.path.join(W, "50_CODE", "k6")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frozen_files():
    j = lambda *a: os.path.join(W, *a)  # noqa: E731
    files = [os.path.join(K, f) for f in ("k6_sim_v01.py", "k6_run_v01.py", "k6_analyse_v01.py", "k6_fit_v01.py", "k6_items_v01.py",
                                          "k6_cache_v01.py", "k6_ego_prep_v01.py", "check_horizon8_v01.py", "run_k6_horizon_v01.sh",
                                          "run_k6_prep_v01.sh", "run_k6_main_v01.sh", "k6_freeze_v01.py")]
    files += [os.path.join(K, "tests", f) for f in ("test_k6_sim_v01.py", "k6_oc_v01.py", "k6_dev_check_v01.py")]
    files += [j("50_CODE", "x1", "x1_horizon_prep_v04.py"), j("50_CODE", "x1", "x1_lib_v03.py"), j("50_CODE", "x1", "x1_gt_prep_v03.py"),
              j("50_CODE", "m", "m_lib_v04.py"), j("50_CODE", "m", "m_data_v04.py"),
              j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v01.md"), j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v02.md"),
              j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v03.md"), j("70_TESTS", "k6_scratch", "debug_frames_v01.py"),
              j("70_TESTS", "k6_scratch", "debug_frames_v02.py"),
              j("60_RESULTS", "k6_horizon_v01", "HORIZON8_IDENTITY_v01.json"), j("30_DATA", "k6", "k6_ego20hz_v01.json.gz"),
              j("70_TESTS", "k6_scratch", "k6_tests_v01.json"), j("70_TESTS", "k6_scratch", "k6_oc_v01.json"),
              j("70_TESTS", "k6_scratch", "k6_dev_check_v01.json")]
    for t in ("t1", "t3"):
        files.append(j("60_RESULTS", "k6_items_v01", "k6_fits_%s_v01.json" % t))
        for sp in ("train", "val"):
            files.append(j("30_DATA", "k6", "cache_%s_%s" % (t, sp), "MANIFEST.json"))
            files.append(j("60_RESULTS", "k6_items_v01", "items_%s_%s_summary.json" % (t, sp)))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--oc", required=True)
    ap.add_argument("--dev", required=True)
    a = ap.parse_args()
    main_out = os.path.join(W, "60_RESULTS", "k6_main_v01")
    assert not (os.path.isdir(main_out) and os.listdir(main_out)), "confirmatory output already exists"
    py = sys.executable
    r = subprocess.run([py, "-B", os.path.join(K, "tests", "test_k6_sim_v01.py"), os.path.join(W, "70_TESTS", "k6_scratch", "k6_tests_v01.json")],
                       capture_output=True, text=True, cwd=os.path.join(K, "tests"))
    assert "ALL_PASS" in r.stdout, "harness tests fail:\n" + r.stdout[-2000:]
    idj = json.load(open(os.path.join(W, "60_RESULTS", "k6_horizon_v01", "HORIZON8_IDENTITY_v01.json")))
    assert idj["all_ok"], "horizon identity failed"
    oc = json.load(open(a.oc))
    a1 = {k: v["A1_null_any_cell_flag_rate"] for k, v in oc["layouts"].items()}
    assert all(x <= 0.10 for x in a1.values()), "OC A1 not met: %s" % a1
    assert os.path.exists(a.dev)
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
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rec = os.path.join(os.path.dirname(a.plan), "K6_FREEZE_RECORD_v01.txt")
    with open(rec, "w", encoding="utf-8") as f:
        f.write("K6 plan frozen %s\nsha256 %s\nfiles %d\nharness tests ALL_PASS\nhorizon identity PASS\nOC A1 %s\n" % (stamp, h, len(files), json.dumps(a1)))
    print("FROZEN", h, len(files), "files")


if __name__ == "__main__":
    main()
