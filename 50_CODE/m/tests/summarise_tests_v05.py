#!/usr/bin/env python3
"""Compile the final pre-freeze test record 70_TESTS/M_SYNTHETIC_TESTS_v05.md (Claude line, v05, 31 Oct 2026): v04 tests,
the export velocity check (tracker output), the decision checks, the end-to-end run and its disclosures, and the OC study
(oc_v04_*.json, merged from the v02 and v03 shards).
Usage: python summarise_tests_v05.py --base <programme folder>
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
    u, r, b, fc, dc, ev, chk, eps = (J("units_v04_reps200.json"), J("refit_v04_reps30.json"), J("b8_v04_reps20.json"), J("freeze_check_v03.json"),
                                     J("decide_checks_v01.json"), J("export_velocity_v02.json"), J(os.path.join("sim_e2e_v04", "check.json")), J("eps_v01.json"))
    code = os.path.join(a.base, "50_CODE", "m")
    L = ["# M synthetic tests v05 (31 Oct 2026): the record frozen with plan v05", "",
         "Every outcome below is **simulated**, except section 6, which reads tracker output only and no ground truth. The OC "
         "layouts are the real ones, with simulated scores.", "",
         "Code under test (sha256 prefixes): " + ", ".join("`%s` %s" % (f, sha(os.path.join(code, f))[:16]) for f in
                                                          ("m_lib_v04.py", "m_run_v04.py", "m_data_v04.py", "m_sizes_v04.py", "m_decide_v04.py")), "",
         "## 1. Unit and Monte Carlo tests (`test_m_units_v04.py`, 200 datasets of 700 scenes in 50 logs)", ""] + table(u["ok"]) + [
         "", "- T1: the worst cell's mean held-out exceedance for M\\* was %.4f (MC s.e. %.4f)." % (u["T1_max_mean_E"], u["T1_mcse"]),
         "- T2: at an exact-5 %% oracle, the fixed-rule simultaneous test's size was %.3f, so it is conservative." % u["T2_size_oracle"],
         "- T1b: M\\* was flagged in %.3f of datasets." % u["T1b_Mstar_flag_rate"],
         "- T3: the HM3 paired contrast found the planted effect in %.2f of datasets." % u["T3_power_HM3_paired"], "",
         "## 2. E2 refit bootstrap through `run_e2` (`test_m_refit_v04.py`; HM6b as the pooled significance check)", ""] + table(r["ok"]) + [
         "", "- Under the null, HM6 held in %.2f of datasets. With val lateral turning ×1.6, it held in %.2f." % (r["T15_null_HM6_hold_rate"], r["T15b_shift1.6_HM6_hold_rate"]), "",
         "## 3. B8 (`test_m_b8_v04.py`)", "",
         "- Gaussian scores: B8's mean exceedance was %.4f." % b["T16a_mean_Ebar_B8_gaussian"],
         "- Mixture: B8 failed against M\\* in %.2f of datasets, and M\\* was not flagged in %.2f." % (b["T16b_rate_B8_fails_paired"], b["T16b_rate_Mstar_not_flagged"]),
         "- Overall: %s." % ("pass" if b["all_ok"] else "**FAIL**"), "",
         "## 4. Freeze dry run (`test_m_freeze_check_v03.py`)", ""] + table(fc["ok"]) + [
         "", "## 5. Decision checks (`test_m_decide_checks_v01.py`; R07c X-m10)", ""] + table(dc["ok"]) + [
         "", "## 6. Export velocity check, tracker output only (`test_export_velocity_v02.py`, m_data_v04 loader with its X-m11 assertion)", ""] + table(ev["ok"]) + [""]
    for t in ("T1", "T2", "T3raw", "T3"):
        L.append("- %s: median |velocity − displacement/time| (m/s) by class: %s" % (t, {k: round(v, 2) for k, v in ev[t]["median_abs_error_mps_by_class"].items()}))
    L += ["", "## 7. End-to-end pipeline on a simulated dataset (`run_m_sim_e2e_v04.sh`, `check_sim_e2e_v04.py`)", ""] + table(chk["ok"]) + [
          "", "- Decision label on the simulated triple: %s (no meaning for real data)." % chk["decision"],
          "- HM3 cells found: %s." % chk.get("HM3_cells"), "",
          "**Disclosures (R07b N-m3, R07c X-m6).**",
          "1. The v02 end-to-end run failed HM6a at 2 s on its single fixed simulated dataset (one cell, LB 0.0503). The criterion was then "
          "relaxed to HM6a on 2 of 3 horizons, with the pooled check required at all three. One dataset cannot carry a rate; the OC study measures rates.",
          "2. Simulated dataset v02, first try (car E at 0.15 rad/s; `sim_e2e_v03_try1_omega0.15/`): B6 lateral-turning E was 0.088 with refit "
          "LB 0.045, so the known answer was not detected. This is consistent with OC power at that effect. The planted turn was raised to "
          "0.30 rad/s. Car E then circles, and B6 fails in a longitudinal car-turning cell. Criterion 5 counts any car-turning cell.", "",
          "## 8. Operating characteristics at the real counts (plan v05 §9)", "",
          "- Derived descriptive margin: %s." % json.dumps(eps),
          "- Settings: E1 parts use 3 CV repetitions, fixed B = 300 and refit-CV B = 60; E2 parts use B = 150.",
          "- E1 parts come from OC v02. E2 parts come from fresh OC v03 seeds.", ""]
    for t in ("T1", "T3"):
        oc = J("oc_v04_%s.json" % t)
        L += ["### %s" % t, "", "- Acceptance: %s." % json.dumps(oc["acceptance"]), ""]
        for k, v in oc["parts"].items():
            if k.startswith("comp"):
                for tag in ("E1", "E2"):
                    L.append("- %s: component power (fixed rule, 'significantly under-covered' alone), MDE80 per cell: %s" % (tag, v[tag]["MDE80_component"]))
            else:
                L.append("- %s: %s" % (k, json.dumps(v)))
        L.append("")
    open(os.path.join(a.base, "70_TESTS", "M_SYNTHETIC_TESTS_v05.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("written")


if __name__ == "__main__":
    main()
