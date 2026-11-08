#!/usr/bin/env python3
"""K6 freeze (Claude line, v02, 1 Nov 2026). Checks the pre-freeze conditions, writes the hash block into the K6 plan v02,
then the plan's .sha256 sidecar and the freeze record K6_FREEZE_RECORD_v02.txt. Conditions:
  * the harness tests pass (tests/test_k6_sim_v02.py is re-run here and must print ALL_PASS);
  * the generators reproduce k6_sim_v02.py (make_k6_sim_v02.py, then _step2 and _step3, in a temporary copy);
  * the 8-step horizon identity check passed;
  * the OC v02 acceptance holds (A1 <= 0.10 and family >= F_MIN at scale 1 in every layout);
  * the development check v02 exists;
  * no confirmatory run output exists yet (60_RESULTS/k6_main_v02 is absent or empty).
v02 also freezes the item npz files and the horizon files the fits came from (R09 m6).
Usage: python -B k6_freeze_v02.py --plan <K6_PREREGISTRATION_v02.md> --oc <json> --dev <json>
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
    files = [os.path.join(K, f) for f in ("k6_sim_v02.py", "k6_run_v02.py", "k6_analyse_v02.py", "k6_fit_v01.py", "k6_items_v01.py",
                                          "k6_cache_v02.py", "k6_ego_prep_v01.py", "check_horizon8_v01.py", "run_k6_horizon_v01.sh",
                                          "run_k6_prep_v01.sh", "run_k6_cache_v02.sh", "run_k6_main_v02.sh", "k6_freeze_v02.py",
                                          "k6_sim_v01.py", "k6_cache_v01.py")]
    files += [os.path.join(K, "tests", f) for f in ("test_k6_sim_v02.py", "k6_oc_v02.py", "k6_dev_check_v02.py", "make_k6_sim_v02.py",
                                                    "make_k6_sim_v02_step2.py", "make_k6_sim_v02_step3.py", "make_k6_analyse_v02.py",
                                                    "make_k6_freeze_main_v02.py", "patch_k6_analyse_v02_r09b.py", "patch_k6_run_v02_r09b.py",
                                                    "patch_test_k6_sim_v02_r09b.py", "patch_test_t10_t12.py", "patch_oc_analyse_r09b.py",
                                                    "patch_r09c.py", "patch_plan_v02_r09b.py", "patch_plan_v02_r09b_part2.py")]
    files += [j("50_CODE", "x1", "x1_horizon_prep_v04.py"), j("50_CODE", "x1", "x1_lib_v03.py"), j("50_CODE", "x1", "x1_gt_prep_v03.py"),
              j("50_CODE", "m", "m_lib_v04.py"), j("50_CODE", "m", "m_data_v04.py"),
              j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v01.md"), j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v02.md"),
              j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v03.md"), j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v04.md"),
              j("70_TESTS", "R09_K6_PREFREEZE_REVIEW_v01.md"), j("70_TESTS", "R09B_K6_PREFREEZE_REREVIEW_v01.md"),
              j("70_TESTS", "R09C_K6_PREFREEZE_CHECK_v01.md"), j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v05.md"),
              j("70_TESTS", "k6_scratch", "debug_frames_v01.py"),
              j("70_TESTS", "k6_scratch", "debug_frames_v02.py"),
              j("60_RESULTS", "k6_horizon_v01", "HORIZON8_IDENTITY_v01.json"), j("30_DATA", "k6", "k6_ego20hz_v01.json.gz"),
              j("70_TESTS", "k6_scratch", "k6_tests_v02.json"), j("70_TESTS", "k6_scratch", "k6_oc_v02.json"),
              j("70_TESTS", "k6_scratch", "k6_dev_check_v02.json")]
    for t in ("t1", "t3"):
        files.append(j("60_RESULTS", "k6_items_v01", "k6_fits_%s_v01.json" % t))
        for sp in ("train", "val"):
            files.append(j("30_DATA", "k6", "cache_v02_%s_%s" % (t, sp), "MANIFEST.json"))
            files.append(j("60_RESULTS", "k6_items_v01", "items_%s_%s_summary.json" % (t, sp)))
            files.append(j("60_RESULTS", "k6_horizon_v01", "horizon8_%s_%s.jsonl.gz" % (t, sp)))
            files += sorted(glob.glob(j("60_RESULTS", "k6_items_v01", "items_%s_%s_h*.npz" % (t, sp))))
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--oc", required=True)
    ap.add_argument("--dev", required=True)
    a = ap.parse_args()
    main_out = os.path.join(W, "60_RESULTS", "k6_main_v02")
    assert not (os.path.isdir(main_out) and os.listdir(main_out)), "confirmatory output already exists"
    py = sys.executable
    r = subprocess.run([py, "-B", os.path.join(K, "tests", "test_k6_sim_v02.py"), os.path.join(W, "70_TESTS", "k6_scratch", "k6_tests_v02.json")],
                       capture_output=True, text=True, cwd=os.path.join(K, "tests"))
    assert "ALL_PASS" in r.stdout, "harness tests fail:\n" + r.stdout[-2000:]
    import shutil
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "tests"))
        shutil.copy(os.path.join(K, "k6_sim_v01.py"), tmp)
        for g in ("make_k6_sim_v02.py", "make_k6_sim_v02_step2.py", "make_k6_sim_v02_step3.py"):
            shutil.copy(os.path.join(K, "tests", g), os.path.join(tmp, "tests"))
            subprocess.run([py, "-B", os.path.join(tmp, "tests", g)], check=True, capture_output=True)
        assert sha(os.path.join(tmp, "k6_sim_v02.py")) == sha(os.path.join(K, "k6_sim_v02.py")), "the generators do not reproduce k6_sim_v02.py"
    idj = json.load(open(os.path.join(W, "60_RESULTS", "k6_horizon_v01", "HORIZON8_IDENTITY_v01.json")))
    assert idj["all_ok"], "horizon identity failed"
    oc = json.load(open(a.oc))
    assert os.path.abspath(a.oc) == os.path.abspath(os.path.join(W, "70_TESTS", "k6_scratch", "k6_oc_v02.json")), "the OC must be the frozen file"
    assert oc["acceptance_all"], "OC v02 acceptance not met: %s" % oc["acceptance"]
    a1 = {k: v["A1_P_HK1_fails_valid_Mstar"] for k, v in oc["layouts"].items()}
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
    rec = os.path.join(os.path.dirname(a.plan), "K6_FREEZE_RECORD_v02.txt")
    with open(rec, "w", encoding="utf-8") as f:
        f.write("K6 plan v02 frozen %s\nsha256 %s\nfiles %d\nharness tests ALL_PASS\ngenerators reproduce k6_sim_v02\nhorizon identity PASS\nOC v02 A1 %s\n" % (stamp, h, len(files), json.dumps(a1)))
    print("FROZEN", h, len(files), "files")


if __name__ == "__main__":
    main()
