#!/usr/bin/env python3
"""Reproduction check (Claude line, 2 Nov 2026): c1_analyse_v01 --reproduce against the K8 development verdicts where the
definitions coincide. (a) the K8 Linux replicate's decision runs: every arm's validity (HK1, valid_form_B) equals K8 v03's checkpoint
exactly (same code path, K8's seeds), arm_status.valid equals valid_form_B, C1's Form B (Choice 9) equals v03's Form B when no
comparator fails only a floor (V_t = v03's passing set), Forms A and C agree, infeasible rates are equal, RETUNED's fold choices are
equal. (b) the M*J Linux runs: C1's H3 (M*Jx) and joint validity per arm equal the k8_analyse_v04 joint section.
Usage: python -B tests/c1_reproduce_check_v01.py --c1-k8 <c1 analysis json of the K8 runs> --c1-joint <c1 analysis json of the joint runs>
       --out <json>
"""
import argparse
import json
import os

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
V03 = os.path.join(W, "70_TESTS", "k8_expl_v02_linux_analysis_v03", "k8_exploratory_analysis_v03_checkpoints", "%s_decide.json")
JOINT = os.path.join(W, "70_TESTS", "k8_joint_v01_linux", "full_v02fits", "k8_joint_analysis_v04.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c1-k8", default=None)
    ap.add_argument("--c1-joint", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res, ok = {}, True
    if a.c1_k8:
        c1 = json.load(open(a.c1_k8))
        for t in ("t1", "t3"):
            v3 = json.load(open(V03 % t))["result"]
            k8 = c1["k8"]["within_lt3d"][t]
            cc = c1["c1"]["within_lt3d"][t]
            chk = {}
            chk["validity_by_arm_equal"] = {a_: k8["validity_by_arm"][a_]["valid_form_B"] == v3["validity_by_arm"][a_]["valid_form_B"]
                                            and k8["validity_by_arm"][a_]["HK1"] == v3["validity_by_arm"][a_]["HK1"] for a_ in v3["validity_by_arm"]}
            chk["arm_status_equals_valid_form_B"] = {a_: cc["status"][a_]["valid"] == v3["validity_by_arm"][a_]["valid_form_B"] for a_ in v3["validity_by_arm"]}
            chk["infeasible_equal"] = all(abs(k8["infeasible_rate"][a_]["mean"] - v3["infeasible_rate"][a_]["mean"]) < 1e-12 for a_ in v3["infeasible_rate"])
            B = v3["d14_forms"]["B_literature_form"]
            fl = cc["form_b"]["in_V_by_choice9"]
            chk["formB"] = {"c1_met": cc["form_b"]["met"], "v03_met": B["met"], "c1_V": cc["form_b"]["V"], "v03_passing": B["comparators_passing_validity"],
                            "floor_only_in_V": fl, "equal": (cc["form_b"]["met"] == B["met"] and (fl or sorted(cc["form_b"]["V"]) == sorted(B["comparators_passing_validity"])))}
            chk["formA_equal"] = cc["form_a"]["met"] == v3["d14_forms"]["A_K6_form"]["met"]
            chk["formC"] = {"c1_met": cc["form_c"]["met"], "v03_met_point": v3["d14_forms"]["C_B_plus_price_bound"]["met_point"],
                            "c1_ub": cc["form_c"]["ub"], "v03_ub": v3["d14_forms"]["C_B_plus_price_bound"]["ub_one_sided_0.95"]}
            chk["formC"]["equal_ub"] = abs(chk["formC"]["c1_ub"] - chk["formC"]["v03_ub"]) < 1e-12
            chk["retune_equal"] = (k8.get("retune") or {}).get("arm_of_fold") == (v3.get("retune") or {}).get("arm_of_fold")
            chk["H10"] = {k_: cc["H10"][k_] for k_ in ("met", "cells_failing_B6", "p")}
            chk["pass"] = bool(all(chk["validity_by_arm_equal"].values()) and all(chk["arm_status_equals_valid_form_B"].values()) and chk["infeasible_equal"]
                               and chk["formB"]["equal"] and chk["formA_equal"] and chk["formC"]["equal_ub"] and chk["retune_equal"])
            ok = ok and chk["pass"]
            res["k8_" + t] = chk
    if a.c1_joint:
        c1 = json.load(open(a.c1_joint))
        jj = json.load(open(JOINT))
        for t in ("t1", "t3"):
            cc = c1["c1"]["within_lt3d"][t]
            ref = jj["decide"][t]["joint_loss"]
            fb = ref["form_B_joint"]["MstarJx"]
            chk = {"c1_H3_met": cc["H3"]["met"], "v04_met": fb["met"], "c1_VJ": cc["H3"]["VJ"], "v04_valid": fb["comparators_valid_on_joint_loss"],
                   "validJ_equal": {a_: cc["joint_status"][a_]["validJ"] == ref["validity_by_arm"][a_]["valid"] for a_ in ref["validity_by_arm"]},
                   "H3_missing": cc["H3"]["missing"]}
            chk["pass"] = bool(chk["c1_H3_met"] == chk["v04_met"] and sorted(chk["c1_VJ"]) == sorted(["Mstar"] * 0 + [c for c in chk["v04_valid"]])
                               and all(chk["validJ_equal"].values()))
            ok = ok and chk["pass"]
            res["joint_" + t] = chk
    res["verdict"] = "REPRODUCED" if ok else "DIFFERENT"
    json.dump(res, open(a.out, "w"), indent=1)
    print(json.dumps(res, indent=1)[:3000])
    print(res["verdict"])


if __name__ == "__main__":
    main()
