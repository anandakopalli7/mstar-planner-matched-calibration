#!/usr/bin/env python3
"""m_decide_v04 on crafted results (Claude line, v01, 31 Oct 2026; R07c X-m10). No data of any kind.
Checks the labels and the input refusals of plan v05 section 8:
  GO-A; NO-GO when no common practitioner baseline fails on T1 and T3; GO-B when HM3 fails on T3; GO-B (HM3 untestable);
  NO-GO when HM6 fails on T2; refusal for a wrong plan hash, a test-mode result, a swapped tracker label and an incomplete run.
Usage: python test_m_decide_checks_v01.py --out <json>
"""
import argparse
import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RATIO = {"point": 0.5, "ci": [0.4, 0.6]}


def result(tracker, sha, hm2=None, hm3=True, testable=True, hm6=True):
    hm2 = hm2 if hm2 is not None else {"B1": [], "B4": ["car|<20|lat|turning"], "B9": []}
    h1 = {"HM1": True, "HM2": hm2, "HM2_any": any(hm2.values()), "HM2b": {"B5": [], "B7": [], "B8": [], "B10": []},
          "HM3_testable": testable, "HM3": ["car|<20|lat|turning"] if hm3 else [], "HM3_holds": hm3,
          "fixed_rule_alone": {}, "both_inferences": {}, "MLS_consistent": True, "Mstar_log_consistent": True}
    h2 = {"HM6": hm6, "HM6a": hm6, "HM6b": True, "MLS_HM6": True, "pooled_E": 0.05, "pooled_lb": 0.04, "pooled_ub_bias_corrected": 0.06,
          "pooled_equivalence_at_eps": True}
    return {"prereg_sha256": sha, "tracker": tracker, "completed_through": "all",
            "E1_h2s": {"hypotheses": h1, "fixed": {"ratios": {"Mstar/B3": RATIO, "Mstar/B6c": RATIO, "Mstar/B9": RATIO, "MLS/Mstar": {"point": 1.1, "ci": [1.0, 1.2]}}}},
            "E2_h2s": {"hypotheses": h2}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    d = tempfile.mkdtemp()
    ok = {}
    try:
        plan = os.path.join(d, "PLAN.md")
        open(plan, "w").write("plan\n")
        open(os.path.join(d, "PLAN.sha256"), "w").write("abc123  PLAN.md\n")

        def run(res, test_mode=False):
            paths = []
            for t in ("T1", "T2", "T3"):
                p = os.path.join(d, "%s.json" % t)
                json.dump(res[t], open(p, "w"))
                paths.append(p)
            cmd = [sys.executable, "-B", os.path.join(HERE, "m_decide_v04.py"), "--prereg", plan, "--t1", paths[0], "--t2", paths[1],
                   "--t3", paths[2], "--out", os.path.join(d, "dec.json")] + (["--test-mode"] if test_mode else [])
            pr = subprocess.run(cmd, capture_output=True, text=True)
            return pr.returncode, (json.load(open(os.path.join(d, "dec.json")))["METHOD_DECISION"] if pr.returncode == 0 else None)
        base = {t: result(t, "abc123") for t in ("T1", "T2", "T3")}
        ok["GO_A"] = run(base) == (0, "GO-A")
        r = copy.deepcopy(base)
        r["T1"] = result("T1", "abc123", hm2={"B1": ["x"], "B4": [], "B9": []})
        r["T3"] = result("T3", "abc123", hm2={"B1": [], "B4": ["x"], "B9": []})
        ok["NO_GO_no_common_baseline"] = run(r) == (0, "NO-GO")
        r = copy.deepcopy(base)
        r["T3"] = result("T3", "abc123", hm3=False)
        ok["GO_B_HM3_fails_on_T3"] = run(r) == (0, "GO-B")
        r["T3"] = result("T3", "abc123", hm3=False, testable=False)
        ok["GO_B_untestable"] = run(r) == (0, "GO-B (HM3 untestable)")
        r = copy.deepcopy(base)
        r["T1"] = result("T1", "abc123", hm3=False)
        ok["T1_HM3_does_not_decide"] = run(r) == (0, "GO-A")
        r = copy.deepcopy(base)
        r["T2"] = result("T2", "abc123", hm6=False)
        ok["NO_GO_HM6_fails_on_T2"] = run(r) == (0, "NO-GO")
        r = {t: result(t, "wrong") for t in ("T1", "T2", "T3")}
        ok["refuses_wrong_hash"] = run(r)[0] != 0
        r = {t: result(t, "TEST MODE") for t in ("T1", "T2", "T3")}
        ok["refuses_test_mode_result"] = run(r)[0] != 0
        r = copy.deepcopy(base)
        r["T1"], r["T2"] = result("T2", "abc123"), result("T1", "abc123")
        ok["refuses_swapped_label"] = run(r)[0] != 0
        r = copy.deepcopy(base)
        r["T3"]["completed_through"] = "h2s"
        ok["refuses_incomplete_run"] = run(r)[0] != 0
    finally:
        shutil.rmtree(d, ignore_errors=True)
    ok = {k: bool(v) for k, v in ok.items()}
    out = {"ok": ok, "all_ok": all(ok.values())}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
