#!/usr/bin/env python3
"""c1crit_repro_v01 (5 Nov 2026): build the development caches (K8 Linux replicate, nuScenes only) and reproduce the stored
K8 v03 development verdicts with the reused code at the K8 seeds. Output: 60_RESULTS/c1_criteria_sensitivity_v01/repro_v01.json.
Usage: python -B c1crit_repro_v01.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402


def cmp_arm(v, ref):
    """Compare hk1_rule output with the stored validity_by_arm entry."""
    diffs = []
    for p in C.POPS:
        r, s = v["pops"][p], ref["pops"][p]
        for k in ("evaluable", "flagged", "family_size", "family_flagged"):
            if (r.get(k) if k != "family_size" else r.get("family_size")) != s.get(k):
                diffs.append("%s %s: %s vs %s" % (p, k, r.get(k), s.get(k)))
        for k in ("q", "family_q"):
            a, b = r.get(k), s.get(k)
            if (a is None) != (b is None) or (a is not None and abs(a - b) > 1e-9):
                diffs.append("%s %s: %s vs %s" % (p, k, a, b))
        pa, pb = r.get("pooled"), s.get("pooled")
        if (pa is None) != (pb is None):
            diffs.append("%s pooled presence" % p)
        elif pa is not None:
            for k in ("E", "lb", "ub"):
                if abs(pa[k] - pb[k]) > 1e-9:
                    diffs.append("%s pooled %s: %r vs %r" % (p, k, pa[k], pb[k]))
            for k in ("flagged", "HK1c_ub_le_delta_plus_0.03"):
                if pa[k] != pb[k]:
                    diffs.append("%s pooled %s" % (p, k))
    return diffs


def main():
    t0 = time.time()
    J = C.load_analysis()
    out = {"stamp": "c1crit_repro_v01: nuScenes development data only (K8 Linux replicate, v03 analysis)",
           "analysis_json": C.ANALYSIS, "analysis_sha256": C.sha(C.ANALYSIS), "seeds": {"boot": "[20261106, i, 0]",
           "power": "[20261107, i] (+ [100 + ARM_INDEX[a]] for comparators) + [k]"}, "trackers": {}}
    for tag in C.TAGS:
        if not os.path.exists(C.cache_path(tag)):
            C.build_cache(tag, J)
        dev = C.Dev(tag)
        d = J["decide"][tag]
        W, Wl = dev.weights()
        vba = C.validity_all(dev, W, strict_mstar=True)
        rep = {"cache": C.cache_path(tag), "cache_sha256": C.sha(C.cache_path(tag)), "scenes": int(len(dev.scenes)),
               "logs": dev.n_logs, "arms": {}}
        for a in C.ARMS:
            ref = d["validity_by_arm"][a]
            rep["arms"][a] = {"diffs": cmp_arm(vba[a], ref), "HK1": vba[a]["HK1"], "HK1_stored": ref["HK1"]}
        # M*'s stored power values
        pw_diff = []
        for p in C.POPS:
            a_ = vba["Mstar"]["pops"][p].get("power_at_0.15", {})
            b_ = d["HK1"]["pops"][p].get("power_at_0.15", {})
            if a_ != b_:
                pw_diff.append(p)
        rep["Mstar_power_values_equal"] = not pw_diff
        rep["status_equivalence_failures"] = C.check_status_equivalence(vba)
        # infeasible rates
        rep["infeasible_rate_max_abs_diff"] = max(abs(float(dev.rate[a].mean()) - d["infeasible_rate"][a]["mean"]) for a in C.ARMS)
        status = {a: C.status_from_hk1(vba[a]) for a in C.ARMS}
        fm = C.forms(dev, W, status)
        f8 = d["d14_forms"]
        rep["forms_here"] = fm
        rep["verdicts_here"] = C.verdict_summary(status, fm)
        rep["forms_stored"] = {"A_met": f8["A_K6_form"]["met"], "B_met": f8["B_literature_form"]["met"],
                               "B_passing": f8["B_literature_form"]["comparators_passing_validity"],
                               "C_ub": f8["C_B_plus_price_bound"]["ub_one_sided_0.95"],
                               "C_point_within": f8["C_B_plus_price_bound"]["point_within_bound"],
                               "A_ub": {k: v["ub_one_sided"] for k, v in f8["A_K6_form"]["lower_than"].items()},
                               "B_ub": {k: v["ub_one_sided"] for k, v in f8["B_literature_form"]["lower_than_every_passing_comparator"].items()}}
        st = rep["forms_stored"]
        checks = {
            "all_arm_validity_tables_equal": all(not rep["arms"][a]["diffs"] for a in C.ARMS),
            "Mstar_power_values_equal": rep["Mstar_power_values_equal"],
            "status_equivalence": not rep["status_equivalence_failures"],
            "infeasible_rates_equal": rep["infeasible_rate_max_abs_diff"] < 1e-12,
            "formA_equal": fm["A"]["met"] == st["A_met"] and all(abs(fm["A"]["ub"][k] - st["A_ub"][k]) < 1e-9 for k in st["A_ub"]),
            "formB_k8_equal": fm["B_k8_valid_only"]["met"] == st["B_met"] and fm["B_k8_valid_only"]["V"] == st["B_passing"]
                              and all(abs(fm["B_k8_valid_only"]["ub"][k] - st["B_ub"][k]) < 1e-9 for k in st["B_ub"]),
            "formC_ub_equal": abs(fm["C"]["ub"] - st["C_ub"]) < 1e-9,
        }
        rep["checks"] = checks
        rep["all_checks_pass"] = all(checks.values())
        out["trackers"][tag] = rep
        print(tag, "checks", checks, "verdicts", rep["verdicts_here"], flush=True)
    out["all_checks_pass"] = all(out["trackers"][t]["all_checks_pass"] for t in C.TAGS)
    out["seconds"] = time.time() - t0
    C.jdump(os.path.join(C.OUT, "repro_v01.json"), out)
    print("REPRO", "PASS" if out["all_checks_pass"] else "FAIL", round(out["seconds"], 1), "s")


if __name__ == "__main__":
    main()
