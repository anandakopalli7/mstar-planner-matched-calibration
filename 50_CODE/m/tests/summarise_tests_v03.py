#!/usr/bin/env python3
"""Compile the v03 simulated-data tests, the export velocity check and the OC v02 study into 70_TESTS/M_SYNTHETIC_TESTS_v03.md
(Claude line, v03, 31 Oct 2026).
Usage: python summarise_tests_v03.py --base <programme folder>
"""
import argparse
import hashlib
import json
import os


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def table(ok):
    return ["| Test | Result |", "|---|---|"] + ["| %s | %s |" % (k, "pass" if v else "**FAIL**") for k, v in ok.items()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    a = ap.parse_args()
    S = os.path.join(a.base, "70_TESTS", "m_scratch")
    J = lambda f: json.load(open(os.path.join(S, f)))
    u, r, b, fc, ev, chk = (J("units_v03_reps200.json"), J("refit_v03_reps30.json"), J("b8_v03_reps20.json"), J("freeze_check_v02.json"),
                            J("export_velocity_v01.json"), J(os.path.join("sim_e2e_v03", "check.json")))
    code = os.path.join(a.base, "50_CODE", "m")
    L = ["# M synthetic tests v03 (31 Oct 2026)", "",
         "Every outcome below is **simulated**, except section 5, which reads tracker output only and no ground truth. The OC "
         "layouts are the real ones (items per scene and stratum, scenes in their real logs, records per scene), with simulated scores.", "",
         "Code under test (sha256 prefixes): " + ", ".join("`%s` %s" % (f, sha(os.path.join(code, f))[:16]) for f in
                                                          ("m_lib_v03.py", "m_run_v03.py", "m_data_v03.py", "m_sizes_v03.py", "m_decide_v03.py")), "",
         "## 1. Unit and Monte Carlo tests (`test_m_units_v03.py`, 200 simulated datasets of 700 scenes in 50 logs)", ""] + table(u["ok"]) + [
         "", "- T1: worst cell mean held-out exceedance of M\\* %.4f (MC s.e. %.4f)." % (u["T1_max_mean_E"], u["T1_mcse"]),
         "- T2: size of the fixed-rule simultaneous test at an exact-5 %% oracle: %.3f. The test is conservative; plan v04 §1 says so." % u["T2_size_oracle"],
         "- T1b: M\\* flagged in %.3f of datasets. T3: the HM3 paired contrast detected the planted effect in %.2f." % (u["T1b_Mstar_flag_rate"], u["T3_power_HM3_paired"]),
         "- T11c: course-over-ground rates (straight, chord turn, short history) %s." % u["T11c_cog_rates"], "",
         "## 2. E2 refit bootstrap via `run_e2` (`test_m_refit_v03.py`)", ""] + table(r["ok"]) + [
         "", "- Null: HM6 held in %.2f of datasets. Val lateral-turning ×1.6: HM6 held in %.2f." % (r["T15_null_HM6_hold_rate"], r["T15b_shift1.6_HM6_hold_rate"]), "",
         "## 3. B8 (`test_m_b8_v03.py`)", "",
         "Gaussian: B8 mean exceedance %.4f. Mixture: B8 fails against M\\* in %.2f of datasets; M\\* not flagged in %.2f. %s." % (
             b["T16a_mean_Ebar_B8_gaussian"], b["T16b_rate_B8_fails_paired"], b["T16b_rate_Mstar_not_flagged"], "pass" if b["all_ok"] else "**FAIL**"), "",
         "## 4. Freeze dry run (`test_m_freeze_check_v02.py`)", ""] + table(fc["ok"]) + [
         "", "## 5. Export velocity check, tracker output only (`test_export_velocity_v01.py`; R07b N-C1)", ""] + table(ev["ok"]) + [""]
    for t in ("T1", "T2", "T3raw", "T3"):
        L.append("- %s: median |velocity − displacement/time| (m/s) by class: %s" % (t, {k: round(v, 2) for k, v in ev[t]["median_abs_error_mps_by_class"].items()}))
    L += ["", "## 6. End-to-end pipeline on a simulated dataset (`run_m_sim_e2e_v03.sh`, `check_sim_e2e_v03.py`)", ""] + table(chk["ok"]) + [
          "", "Decision label on the simulated triple: %s (no meaning for real data)." % chk["decision"],
          "", "**Disclosure (R07b N-m3).** The v02 end-to-end run failed HM6a at 2 s on its one fixed simulated dataset (one cell, LB 0.0503). "
          "The criterion was then relaxed to HM6a at 2 of 3 horizons with HM6b at all three. The reason: one fixed dataset cannot carry a "
          "statistical criterion, and the rates are measured by the OC study (section 7). Dataset v02 adds lateral cars, so HM3 now has a known "
          "answer (criterion HM3_known_answer).", "", "## 7. Operating characteristics at the real counts (OC v02; plan v04 §9)", ""]
    for t in ("T1", "T3"):
        p = os.path.join(S, "oc_v02_%s.json" % t)
        if not os.path.isfile(p):
            continue
        oc = json.load(open(p))
        L += ["### %s" % t, "", "Acceptance (plan v04 §9): %s" % json.dumps(oc["acceptance"]), ""]
        for k, v in oc["parts"].items():
            if k.startswith("comp"):
                for tag in ("E1", "E2"):
                    L.append("- %s, component power (fixed rule, 'significantly under-covered' alone), MDE80 per cell: %s" % (tag, v[tag]["MDE80_component"]))
            else:
                L.append("- %s: %s" % (k, json.dumps(v)))
        L.append("")
    open(os.path.join(a.base, "70_TESTS", "M_SYNTHETIC_TESTS_v03.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("written")


if __name__ == "__main__":
    main()
