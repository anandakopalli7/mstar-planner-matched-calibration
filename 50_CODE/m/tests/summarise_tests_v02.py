#!/usr/bin/env python3
"""Compile the v02 simulated-data test outputs, including the operating characteristics at the real counts, into
70_TESTS/M_SYNTHETIC_TESTS_v02.md (Claude line, v02, 31 Oct 2026).
Usage: python summarise_tests_v02.py --base <programme folder>
"""
import argparse
import hashlib
import json
import os


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", required=True)
    a = ap.parse_args()
    S = os.path.join(a.base, "70_TESTS", "m_scratch")
    J = lambda f: json.load(open(os.path.join(S, f)))
    u, r, b, fc = J("units_v02_reps200.json"), J("refit_v02_reps30.json"), J("b8_v02_reps20.json"), J("freeze_check_v01.json")
    chk = J(os.path.join("sim_e2e_v02", "check.json"))
    ocs = {t: J("oc_v01_%s.json" % t) for t in ("T1", "T3") if os.path.isfile(os.path.join(S, "oc_v01_%s.json" % t))}
    code = os.path.join(a.base, "50_CODE", "m")
    L = ["# M synthetic tests v02 (31 Oct 2026)", "",
         "Every outcome below is **simulated**. The item layouts in the operating-characteristic (OC) section are the real ones "
         "(counts of items per scene and stratum, scenes in their real logs), but their scores are simulated. No real "
         "residual was computed by any test.", "",
         "Code under test (sha256 prefixes): " + ", ".join("`%s` %s" % (f, sha(os.path.join(code, f))[:16]) for f in
                                                          ("m_lib_v02.py", "m_run_v02.py", "m_data_v02.py", "m_sizes_v02.py", "m_decide_v02.py")), "",
         "## 1. Unit and Monte Carlo tests (`tests/test_m_units_v02.py`, 200 simulated datasets of 700 scenes in 50 logs)", "",
         "| Test | Result |", "|---|---|"]
    for k, v in u["ok"].items():
        L.append("| %s | %s |" % (k, "pass" if v else "**FAIL**"))
    L += ["", "Numbers:",
          "- T1: M\\* mean held-out exceedance per cell, maximum over cells, %.4f (MC s.e. %.4f)." % (u["T1_max_mean_E"], u["T1_mcse"]),
          "- T2: size of the fixed-rule simultaneous test at an exact-5 %% oracle, %.3f (conservative)." % u["T2_size_oracle"],
          "- T1b: M\\* flagged in %.3f of datasets." % u["T1b_Mstar_flag_rate"],
          "- T3: HM3 paired contrast (B6 against M\\*, car turning cells) detected in %.2f of datasets." % u["T3_power_HM3_paired"],
          "- T21: B10 (no finite-sample term) mean exceedance %.4f; M\\* %.4f (single split)." % (u["T21_B10_mean_E"], u["T21_Mstar_mean_E"]),
          "- Other checks: B9 in-sample exceedance %.4f; NEES factor %.3f (planted 4); scale ratio %.3f (planted 2.17)." % (
              u["T20_B9_in_sample_exceedance"], u["T4_k"], u["T5_scale_ratio_turn_vs_straight_lat"]), "",
          "## 2. Log resampling and the E2 refit bootstrap (`tests/test_m_refit_v02.py`, via `m_run_v02.run_e2`)", "",
          "| Test | Result |", "|---|---|"]
    for k, v in r["ok"].items():
        L.append("| %s | %s |" % (k, "pass" if v else "**FAIL**"))
    L += ["", "- Null (train 50 logs, val 18 logs, same law): HM6 held in %.2f of datasets; mean pooled E, UB, cells %s." % (
              r["T15_null_HM6_hold_rate"], r["T15_null_mean_pooledE_ub_ncells"]),
          "- Val lateral-turning scale x 1.6: HM6 held in %.2f of datasets, so it was detected in %.2f; mean pooled E, UB, cells %s." % (
              r["T15b_shift1.6_HM6_hold_rate"], 1 - r["T15b_shift1.6_HM6_hold_rate"], r["T15b_shift1.6_mean_pooledE_ub_ncells"]), "",
          "## 3. B8 behaviour (`tests/test_m_b8_v02.py`, 20 datasets)", "",
          "- Gaussian scores: B8 mean exceedance %.4f." % b["T16a_mean_Ebar_B8_gaussian"],
          "- Mixture in the lateral turning strata: B8 fails against M\\* (paired) in %.2f of datasets; M\\* is not flagged in %.2f." % (
              b["T16b_rate_B8_fails_paired"], b["T16b_rate_Mstar_not_flagged"]),
          "- All B8 checks: %s." % ("pass" if b["all_ok"] else "**FAIL**"), "",
          "## 4. Freeze dry run (`tests/test_m_freeze_check_v01.py`)", "",
          "%s: %s." % ("pass" if fc["all_ok"] else "**FAIL**", ", ".join("%s %s" % (k, v) for k, v in fc["ok"].items())), "",
          "## 5. End-to-end pipeline on a simulated dataset (`tests/run_m_sim_e2e_v02.sh`, checked by `check_sim_e2e_v02.py`)", "",
          "%s: %s. Decision label on the simulated triple: %s (no meaning for real data)." % (
              "pass" if chk["all_ok"] else "**FAIL**", ", ".join("%s %s" % (k, v) for k, v in chk["ok"].items()), chk["decision"]), "",
          "## 6. Operating characteristics at the real counts (`tests/test_m_oc_v01.py`)", ""]
    for t, oc in ocs.items():
        L += ["### %s (%s)" % (t, "CANMOT" if t == "T1" else "Poly-MOT"), "",
              "Within-scene correlation rho = %s; log effects of SD %s." % (oc["rho"], oc["log_sd"]), "",
              "- (a) E1 null: M\\* flagged in %.3f of datasets (fixed rule) and %.3f (refit-CV)." % (oc["a_E1_fixed_Mstar_flag_rate"], oc["a_E1_refit_Mstar_flag_rate"]),
              "- (b) E2 null: HM6 failed in %.3f of datasets (HM6a alone %.3f); mean pooled E and UB %s." % (
                  oc["b_E2_HM6_fail_rate"], oc["b_E2_HM6a_fail_rate"], oc["b_E2_mean_pooled_E_and_ub"]),
              "- (d) HM3 paired contrast at these counts: power %.2f (fixed rule), %.2f (both inferences)." % (
                  oc["d_HM3_power_fixed"], oc["d_HM3_power_both_inferences"]), ""]
        for tag in ("E1", "E2"):
            c = oc["c_%s_power" % tag]
            L += ["(c) %s: power of the fixed-rule test against a planted true exceedance, and the minimum detectable exceedance (80 %%):" % tag, "",
                  "| Cell | p = 0.10 | 0.15 | 0.20 | 0.30 | MDE |", "|---|---|---|---|---|---|"]
            pw = c["power_by_true_exceedance"]
            for j, name in enumerate(c["cells"]):
                L.append("| %s | %s | %s | %s | %s | %s |" % (name, pw["0.1"][j], pw["0.15"][j], pw["0.2"][j], pw["0.3"][j], c["MDE_80"][j]))
            L.append("")
    open(os.path.join(a.base, "70_TESTS", "M_SYNTHETIC_TESTS_v02.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("written")


if __name__ == "__main__":
    main()
