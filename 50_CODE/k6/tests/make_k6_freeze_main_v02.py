#!/usr/bin/env python3
"""Writes k6_freeze_v02.py (from k6_freeze_v01.py) and run_k6_main_v02.sh for K6 plan v02 (Claude line, 1 Nov 2026)."""
import os

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(K, "k6_freeze_v01.py"), encoding="utf-8").read()
NL = "\\n"
rep = [
    (s[s.index('"""K6 freeze'):s.index('"""', s.index('"""K6 freeze') + 3) + 3],
     '"""K6 freeze (Claude line, v02, 1 Nov 2026). Checks the pre-freeze conditions, writes the hash block into the K6 plan v02,\n'
     'then the plan\'s .sha256 sidecar and the freeze record K6_FREEZE_RECORD_v02.txt. Conditions:\n'
     '  * the harness tests pass (tests/test_k6_sim_v02.py is re-run here and must print ALL_PASS);\n'
     '  * the generators reproduce k6_sim_v02.py (make_k6_sim_v02.py, then _step2 and _step3, in a temporary copy);\n'
     '  * the 8-step horizon identity check passed;\n'
     '  * the OC v02 acceptance holds (A1 <= 0.10 and family >= F_MIN at scale 1 in every layout);\n'
     '  * the development check v02 exists;\n'
     '  * no confirmatory run output exists yet (60_RESULTS/k6_main_v02 is absent or empty).\n'
     'v02 also freezes the item npz files and the horizon files the fits came from (R09 m6).\n'
     'Usage: python -B k6_freeze_v02.py --plan <K6_PREREGISTRATION_v02.md> --oc <json> --dev <json>\n'
     '"""'),
    ('    files = [os.path.join(K, f) for f in ("k6_sim_v01.py", "k6_run_v01.py", "k6_analyse_v01.py", "k6_fit_v01.py", "k6_items_v01.py",\n'
     '                                          "k6_cache_v01.py", "k6_ego_prep_v01.py", "check_horizon8_v01.py", "run_k6_horizon_v01.sh",\n'
     '                                          "run_k6_prep_v01.sh", "run_k6_main_v01.sh", "k6_freeze_v01.py")]\n'
     '    files += [os.path.join(K, "tests", f) for f in ("test_k6_sim_v01.py", "k6_oc_v01.py", "k6_dev_check_v01.py")]',
     '    files = [os.path.join(K, f) for f in ("k6_sim_v02.py", "k6_run_v02.py", "k6_analyse_v02.py", "k6_fit_v01.py", "k6_items_v01.py",\n'
     '                                          "k6_cache_v02.py", "k6_ego_prep_v01.py", "check_horizon8_v01.py", "run_k6_horizon_v01.sh",\n'
     '                                          "run_k6_prep_v01.sh", "run_k6_cache_v02.sh", "run_k6_main_v02.sh", "k6_freeze_v02.py",\n'
     '                                          "k6_sim_v01.py", "k6_cache_v01.py")]\n'
     '    files += [os.path.join(K, "tests", f) for f in ("test_k6_sim_v02.py", "k6_oc_v02.py", "k6_dev_check_v02.py", "make_k6_sim_v02.py",\n'
     '                                                    "make_k6_sim_v02_step2.py", "make_k6_sim_v02_step3.py", "make_k6_analyse_v02.py",\n'
     '                                                    "make_k6_freeze_main_v02.py", "patch_k6_analyse_v02_r09b.py", "patch_k6_run_v02_r09b.py",\n'
     '                                                    "patch_test_k6_sim_v02_r09b.py", "patch_test_t10_t12.py", "patch_oc_analyse_r09b.py",\n'
     '                                                    "patch_r09c.py", "patch_plan_v02_r09b.py", "patch_plan_v02_r09b_part2.py")]'),
    ('              j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v03.md"), j("70_TESTS", "k6_scratch", "debug_frames_v01.py"),',
     '              j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v03.md"), j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v04.md"),\n'
     '              j("70_TESTS", "R09_K6_PREFREEZE_REVIEW_v01.md"), j("70_TESTS", "R09B_K6_PREFREEZE_REREVIEW_v01.md"),\n'
     '              j("70_TESTS", "R09C_K6_PREFREEZE_CHECK_v01.md"), j("90_DECISIONS", "D09_K6_HARNESS_DESIGN_v05.md"),\n'
     '              j("70_TESTS", "k6_scratch", "debug_frames_v01.py"),'),
    ('              j("70_TESTS", "k6_scratch", "k6_tests_v01.json"), j("70_TESTS", "k6_scratch", "k6_oc_v01.json"),\n'
     '              j("70_TESTS", "k6_scratch", "k6_dev_check_v01.json")]',
     '              j("70_TESTS", "k6_scratch", "k6_tests_v02.json"), j("70_TESTS", "k6_scratch", "k6_oc_v02.json"),\n'
     '              j("70_TESTS", "k6_scratch", "k6_dev_check_v02.json")]'),
    ('            files.append(j("30_DATA", "k6", "cache_%s_%s" % (t, sp), "MANIFEST.json"))\n'
     '            files.append(j("60_RESULTS", "k6_items_v01", "items_%s_%s_summary.json" % (t, sp)))',
     '            files.append(j("30_DATA", "k6", "cache_v02_%s_%s" % (t, sp), "MANIFEST.json"))\n'
     '            files.append(j("60_RESULTS", "k6_items_v01", "items_%s_%s_summary.json" % (t, sp)))\n'
     '            files.append(j("60_RESULTS", "k6_horizon_v01", "horizon8_%s_%s.jsonl.gz" % (t, sp)))\n'
     '            files += sorted(glob.glob(j("60_RESULTS", "k6_items_v01", "items_%s_%s_h*.npz" % (t, sp))))'),
    ('    main_out = os.path.join(W, "60_RESULTS", "k6_main_v01")', '    main_out = os.path.join(W, "60_RESULTS", "k6_main_v02")'),
    ('    r = subprocess.run([py, "-B", os.path.join(K, "tests", "test_k6_sim_v01.py"), os.path.join(W, "70_TESTS", "k6_scratch", "k6_tests_v01.json")],',
     '    r = subprocess.run([py, "-B", os.path.join(K, "tests", "test_k6_sim_v02.py"), os.path.join(W, "70_TESTS", "k6_scratch", "k6_tests_v02.json")],'),
    ('    assert "ALL_PASS" in r.stdout, "harness tests fail:' + NL + '" + r.stdout[-2000:]',
     '    assert "ALL_PASS" in r.stdout, "harness tests fail:' + NL + '" + r.stdout[-2000:]\n'
     '    import shutil\n'
     '    import tempfile\n'
     '    with tempfile.TemporaryDirectory() as tmp:\n'
     '        os.makedirs(os.path.join(tmp, "tests"))\n'
     '        shutil.copy(os.path.join(K, "k6_sim_v01.py"), tmp)\n'
     '        for g in ("make_k6_sim_v02.py", "make_k6_sim_v02_step2.py", "make_k6_sim_v02_step3.py"):\n'
     '            shutil.copy(os.path.join(K, "tests", g), os.path.join(tmp, "tests"))\n'
     '            subprocess.run([py, "-B", os.path.join(tmp, "tests", g)], check=True, capture_output=True)\n'
     '        assert sha(os.path.join(tmp, "k6_sim_v02.py")) == sha(os.path.join(K, "k6_sim_v02.py")), "the generators do not reproduce k6_sim_v02.py"'),
    ('    a1 = {k: v["A1_null_any_cell_flag_rate"] for k, v in oc["layouts"].items()}\n'
     '    assert all(x <= 0.10 for x in a1.values()), "OC A1 not met: %s" % a1',
     '    assert os.path.abspath(a.oc) == os.path.abspath(os.path.join(W, "70_TESTS", "k6_scratch", "k6_oc_v02.json")), "the OC must be the frozen file"\n'
     '    assert oc["acceptance_all"], "OC v02 acceptance not met: %s" % oc["acceptance"]\n'
     '    a1 = {k: v["A1_P_HK1_fails_valid_Mstar"] for k, v in oc["layouts"].items()}'),
    ('    rec = os.path.join(os.path.dirname(a.plan), "K6_FREEZE_RECORD_v01.txt")',
     '    rec = os.path.join(os.path.dirname(a.plan), "K6_FREEZE_RECORD_v02.txt")'),
    ('        f.write("K6 plan frozen %s' + NL + 'sha256 %s' + NL + 'files %d' + NL + 'harness tests ALL_PASS' + NL + 'horizon identity PASS' + NL + 'OC A1 %s' + NL + '" % (stamp, h, len(files), json.dumps(a1)))',
     '        f.write("K6 plan v02 frozen %s' + NL + 'sha256 %s' + NL + 'files %d' + NL + 'harness tests ALL_PASS' + NL + 'generators reproduce k6_sim_v02' + NL
     + 'horizon identity PASS' + NL + 'OC v02 A1 %s' + NL + '" % (stamp, h, len(files), json.dumps(a1)))'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b, 1)
open(os.path.join(K, "k6_freeze_v02.py"), "w", encoding="utf-8", newline="\n").write(s)

MAIN = r'''#!/usr/bin/env bash
# K6 confirmatory run v02 (Claude line, 1 Nov 2026): for T1 and then T3, the decision mode and the closed loop on the 840
# confirmatory scenes (k6_run_v02, which refuses to start unless the frozen K6 plan v02, its file block and the run inputs
# match, and only with the fixed design), then the K6 analysis and decision (k6_analyse_v02, which checks the freeze record,
# the frozen block, the run records and the design completeness). Unattended; no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
K="$W/50_CODE/k6"; CA="$W/30_DATA/k6"; IT="$W/60_RESULTS/k6_items_v01"; O="$W/60_RESULTS/k6_main_v02"; LG="$W/80_LOGS"
PLAN="$(w "$W/40_PROTOCOL/K6_PREREGISTRATION_v02.md")"
mkdir -p "$O"
cd "$K"
echo "start $(date +%H:%M:%S)"
for T in t1 t3; do
  for MODE in decide loop; do
    "$PY" -B k6_run_v02.py --caches "$(w "$CA/cache_v02_${T}_train")" "$(w "$CA/cache_v02_${T}_val")" --fits "$(w "$IT/k6_fits_${T}_v01.json")" \
      --tag ${T}_$MODE --mode $MODE --out "$(w "$O")" --prereg "$PLAN" --workers 6 > "$LG/K6_main_v02_${T}_$MODE.log" 2>&1 || { echo "RUN ${T}_$MODE FAILED"; exit 1; }
    echo "${T}_$MODE done $(date +%H:%M:%S)"
  done
done
"$PY" -B k6_analyse_v02.py --runs "$(w "$O")" --tags t1 t3 --prereg "$PLAN" \
  --manifests "$(w "$CA/cache_v02_t1_train/MANIFEST.json")" "$(w "$CA/cache_v02_t1_val/MANIFEST.json")" \
  --out "$(w "$O/k6_result_v02.json")" > "$LG/K6_main_v02_analysis.log" 2>&1 || { echo "ANALYSIS FAILED"; exit 1; }
tail -n 40 "$LG/K6_main_v02_analysis.log"
echo "K6 MAIN V02 DONE $(date +%H:%M:%S)"
'''
open(os.path.join(K, "run_k6_main_v02.sh"), "w", encoding="utf-8", newline="\n").write(MAIN)
print("k6_freeze_v02.py and run_k6_main_v02.sh written")
