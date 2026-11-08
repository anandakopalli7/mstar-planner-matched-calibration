#!/usr/bin/env python3
"""Compile the simulated-data test outputs into 70_TESTS/M_SYNTHETIC_TESTS_v01.md (Claude line, v01, 31 Oct 2026).
Usage: python summarise_tests_v01.py --base <programme folder>
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
    u = json.load(open(os.path.join(S, "units_v01_reps200.json")))
    r = json.load(open(os.path.join(S, "refit_v01_reps40.json")))
    b = json.load(open(os.path.join(S, "b8_v01_reps20.json")))
    e = json.load(open(os.path.join(S, "sim_e2e_v01", "result.json")))
    d = json.load(open(os.path.join(S, "sim_e2e_v01", "decision.json")))
    code = os.path.join(a.base, "50_CODE", "m")
    L = ["# M synthetic tests v01 (31 Oct 2026)", "",
         "All data below are **simulated**: simulated scenes, logs, motion, errors and covariances. No real annotation, export or "
         "residual was read by any test. The tests check the code, not the method's real-data performance.", "",
         "Code under test: `m_lib_v01.py` sha256 `%s`; `m_run_v01.py` `%s`." % (sha(os.path.join(code, "m_lib_v01.py"))[:16],
                                                                              sha(os.path.join(code, "m_run_v01.py"))[:16]), "",
         "## Unit and Monte Carlo tests (`tests/test_m_units_v01.py`, 200 simulated datasets of 700 scenes in 50 logs)", "",
         "| Test | What it checks | Result |", "|---|---|---|"]
    desc = {"T11_motion_state": "motion-state rule (static priority, NaN history -> new)",
            "T12_wrap_half": "half-angle wrap: a 180 degree heading flip is not a turn",
            "T6_PM2": "PM2: deployable covariance reproduces stratum margins (max error %.1e m)" % u["T6_max_abs_error_m"],
            "T7_folds": "log folds disjoint, every scene once, balanced (loads %s)" % u["T7_fold_loads"],
            "T8_fallback": "strata with < 19 calibration scenes fall back; others use their own threshold",
            "T9_B3_B6c_dominate": "B3 and B6c thresholds >= M* in every stratum (PM3)",
            "T4_nees_k": "NEES baseline recovers a planted variance factor 4 (got %.3f)" % u["T4_k"],
            "T5_scale_ratio": "learned scale recovers planted lateral turning/straight ratio 2.17 (got %.3f)" % u["T5_scale_ratio_turn_vs_straight_lat"],
            "T10_eval_stats": "exceedance statistics equal a direct computation",
            "T1_validity": "M* held-out exceedance <= 0.05 per stratum on average (max mean %.4f, MC s.e. %.4f)" % (u["T1_max_mean"], u["T1_mcse"]),
            "T2_fwer": "oracle with exact 5 %% exceedance is flagged in %.3f of datasets (limit 0.05 + MC)" % u["T2_fwer_oracle"],
            "T3_power": "B6 flagged on a planted motion-state failure in %.2f of datasets" % u["T3_power_HM3"],
            "T1b_HM1_rate": "HM1 holds for M* in %.2f of datasets" % u["T1b_HM1_rate"]}
    for k, v in u["ok"].items():
        L.append("| %s | %s | %s |" % (k, desc.get(k, ""), "pass" if v else "**FAIL**"))
    L += ["", "Informational T13 (log random effect sd 0.3): mean E-bar of M* and M*-log = %s." % u["T13_log_effect_mean_Ebar_Mstar_Mstarlog"], "",
          "## Log resampling and E2 refit bootstrap (`tests/test_m_refit_v01.py`)", "", "| Test | Result |", "|---|---|"]
    for k, v in r["ok"].items():
        L.append("| %s | %s |" % (k, "pass" if v else "**FAIL**"))
    L += ["", "T15: with train (30 logs) and val (10 logs) drawn from the same law, HM6 held in %.2f of %s datasets "
          "(mean E-bar, mean upper bound, strata: %s)." % (r["T15_rate_HM6_holds"], "40", r["T15_mean_Ebar_ub_nstrata"]), "",
          "## B8 behaviour (`tests/test_m_b8_v01.py`, 20 datasets)", "",
          "- Gaussian scores: B8 mean exceedance %.4f (it is the Gaussian rule)." % b["T16a_mean_Ebar_B8_gaussian"],
          "- Mixture in lateral turning strata (90 %% N(0, 0.3^2), 10 %% N(2, 0.5^2)): B8 flagged in %.2f of datasets; M* held HM1 in %.2f."
          % (b["T16b_rate_HM2c"], b["T16b_rate_HM1_Mstar"]),
          "- All B8 checks: %s." % ("pass" if b["all_ok"] else "**FAIL**"), "",
          "## End-to-end pipeline on a simulated dataset (`tests/run_m_sim_e2e_v01.sh`)", "",
          "Simulated train 200 scenes in 25 logs and val 48 scenes in 8 logs, in the export, ground-truth and horizon formats; "
          "m_sizes (outcomes off), m_run in test mode (B = 300 for E1, 200 for E2), m_decide. Planted: turning car with "
          "0.15 rad/s, CV prediction; longitudinal covariance too wide.", "", "| Evaluation | HM1 | HM2 (B0, B1, B4) | HM2b | HM2c | HM3 | HM3b |", "|---|---|---|---|---|---|---|"]
    for h in ("h1s", "h2s", "h4s"):
        for ev in ("E1", "E2"):
            x = e["%s_%s" % (ev, h)]["hypotheses"]
            L.append("| %s %s | %s | %s | %s | %s | %s | %s |" % (ev, h, x["HM1"], [x["HM2"][k] for k in ("B0", "B1", "B4")],
                                                                x["HM2b"], x.get("HM2c"), x["HM3"], x["HM3b"]))
    L += ["", "Sensitivities ran without error: %s." % ", ".join(e["E5_h2s"].keys()),
          "Decision script output on the simulated pair: METHOD_GO = %s (simulation-specific; no meaning for real data)." % d["METHOD_GO"], ""]
    open(os.path.join(a.base, "70_TESTS", "M_SYNTHETIC_TESTS_v01.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("written")


if __name__ == "__main__":
    main()
