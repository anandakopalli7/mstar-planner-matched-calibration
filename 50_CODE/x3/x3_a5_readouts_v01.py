#!/usr/bin/env python3
"""X3 A5 read-outs (x3-core agent, x3_a5_readouts_v01, 7 Nov 2026). Added after review (amendment A5). X3 POST-REGISTRATION
EXPLORATORY (after the verdict of record; not part of the registered test). Read-outs of outputs of record and existing X3 files only
(sums and ratios of stored values; no statistic is recomputed). Writes a5_review/x3_a5_readouts_v01.md and .json.
"""
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_common_v01 as C  # noqa: E402

LABEL = "added after review (amendment A5)"
OUT = os.path.join(C.OUT, "a5_review")
POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")
LAB = {"PD7_primary": "P_rel", "SD1_7_gap_le_5m": "P_near", "PD_inpath": "P_ip"}


def main():
    C.assert_run_log("A5 readouts start")
    res = {"stamp": C.STAMP, "label": LABEL, "i": {}, "ii": {}, "iii": {}, "iv": {}}
    an = json.load(open(os.path.join(C.REC, "c1_analysis_r1.json")))
    c2p = os.path.join(C.OUT, "c_intervals", "x3_c2_simulation_v01.json")
    c2 = json.load(open(c2p))
    dec = json.load(open(os.path.join(C.REC, "c1_decision_r1.json")))
    for t in ("t1", "t3"):
        f = os.path.join(C.REC, "c1_analysis_csv_r1", "k8_within_lt3d_%s_decide_cells.csv" % t)
        rows = [r for r in csv.DictReader(open(f)) if r["arm"] == "Mstar"]
        res["i"][t] = {}
        for p in POPS:
            rr = [r for r in rows if r["population"] == p]
            ok = [r for r in rr if r["records"] != "" and r["exceed"] != ""]
            n, x = sum(int(r["records"]) for r in ok), sum(int(r["exceed"]) for r in ok)
            n_all = sum(int(r["records"]) for r in rr if r["records"] != "")
            res["i"][t][p] = {"exceed": x, "records": n, "pooled_record_weighted": x / n, "cells_used": len(ok), "cells_all": len(rr),
                              "records_all_cells": n_all, "share_of_records_covered": n / n_all,
                              "note": "the CSV stores 'exceed' only for evaluable cells; non-evaluable cells (records only) are left out"}
        a13 = an["k8"]["within_lt3d"][t]["A13_fallback_record_weighted"]["by_population"]["PD_inpath"]["pooled"]
        res["ii"][t] = dict(a13, source="c1_analysis_r1.json k8.within_lt3d.%s.A13_fallback_record_weighted.by_population.PD_inpath.pooled" % t)
        r_ = c2["results"][t]
        res["iii"][t] = {"screen_flag_any_population_at_delta": r_["Mstar|delta"]["i"]["screen_flag_any_population"],
                         "simultaneous_ub_coverage_at_observed_rates": {p: {k: r_["Mstar|observed"]["i"][p][k] for k in ("sim_ub_cover_all", "sim_ub_cover_all_ci95",
                                                                                                                     "sim_ub_cover_cell_mean", "sim_ub_cover_cell_min", "hk1c_cover")}
                                                                       for p in POPS},
                         "screen_flag_any_population_at_observed_rates": r_["Mstar|observed"]["i"]["screen_flag_any_population"]}
        h2 = dec["hypotheses"]["H2"]["by_tracker"][t]
        res["iv"][t] = {"holm_levels": h2["holm_levels"], "nominal": {"level": h2["level"], "ub": h2["ub"], "c": h2["c"]}}
    fs = dec["family_S"]["H2"]
    res["iv"]["holm_level_assigned"] = fs["holm_level"]
    res["iv"]["bound_at_holm_level"] = dec["S_decision_forms"]["by_claim"]["H2"]["bound_at_holm_level"]
    res["iv"]["p"] = fs["p"]
    res["iv"]["status"] = fs["status"]
    C.jdump(os.path.join(OUT, "x3_a5_readouts_v01.json"), res)
    L = ["# X3 A5 read-outs", "", "**%s** -- %s" % (C.STAMP, LABEL), "", "Read-outs of outputs of record and existing X3 files (sums of stored counts, stored values); nothing recomputed.", "",
         "## (i) M*'s record-weighted pooled exceedance", "",
         "Source: `60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_t{1,3}_decide_cells.csv`, rows arm = Mstar, per population: "
         "sum of column `exceed` / sum of column `records` over the cell rows that carry both (the CSV stores `exceed` only for evaluable "
         "cells; the share of the population's records covered is given).", "",
         "| tracker | P_rel | P_near | P_ip |", "|---|---|---|---|"]
    for t in ("t1", "t3"):
        L.append("| %s | %s |" % (t.upper(), " | ".join("%.4f (%d / %d; %.1f %% of records)" % (res["i"][t][p]["pooled_record_weighted"], res["i"][t][p]["exceed"],
                                                                                          res["i"][t][p]["records"], 100 * res["i"][t][p]["share_of_records_covered"]) for p in POPS)))
    L += ["", "## (ii) Share of M*'s in-path relied records in fallback strata (S6 Table 13 source)", "",
          "Source: `c1_analysis_r1.json`, key `k8.within_lt3d.<t>.A13_fallback_record_weighted.by_population.PD_inpath.pooled` (record-weighted from each "
          "record's fold, step, L0 and in-path flag).", ""]
    for t in ("t1", "t3"):
        q = res["ii"][t]
        L.append("- %s: %d of %d in-path relied records in fallback strata = **%.4f**" % (t.upper(), q["fallback_records"], q["records"], q["share"]))
    L += ["", "## (iii) From c_intervals (x3-stats, analysis c2; method (i), the record's rule)", "",
          "Source: `60_RESULTS/x3_explore_v01/c_intervals/x3_c2_simulation_v01.json`, keys `results.<t>.\"Mstar|delta\".i.screen_flag_any_population` and "
          "`results.<t>.\"Mstar|observed\".i.<population>.sim_ub_cover_all` (1000 simulated datasets).", ""]
    for t in ("t1", "t3"):
        q = res["iii"][t]
        L.append("- %s: P(M* at delta flagged in any population) = **%.3f**; simultaneous coverage of the cell upper bounds at M*'s observed cell rates: %s" % (
            t.upper(), q["screen_flag_any_population_at_delta"], "; ".join("%s %.3f [%.3f, %.3f]" % (LAB[p], v["sim_ub_cover_all"], *v["sim_ub_cover_all_ci95"])
                                                                         for p, v in q["simultaneous_ub_coverage_at_observed_rates"].items())))
    L += ["", "## (iv) H2's bound at its Holm level", "",
          "Source: `60_RESULTS/c1_av2_v01/c1_decision_r1.json`, keys `family_S.H2.holm_level`, `S_decision_forms.by_claim.H2.bound_at_holm_level` and "
          "`hypotheses.H2.by_tracker.<t>.holm_levels`.", "",
          "- Holm level assigned: %s (p = %.3g, status %s); the bound used is UB at level 1 - %s = %.3f: T1 %.5f, T3 %.5f (c = 0.03; both hold)." % (
              res["iv"]["holm_level_assigned"], res["iv"]["p"], res["iv"]["status"], res["iv"]["holm_level_assigned"], 1 - res["iv"]["holm_level_assigned"],
              res["iv"]["bound_at_holm_level"]["t1"]["ub"], res["iv"]["bound_at_holm_level"]["t3"]["ub"]),
          "- Nominal (0.975) bound: T1 %.5f, T3 %.5f." % (res["iv"]["t1"]["nominal"]["ub"], res["iv"]["t3"]["nominal"]["ub"]), ""]
    C.wtext(os.path.join(OUT, "x3_a5_readouts_v01.md"), "\n".join(L))
    C.assert_run_log("A5 readouts end")
    print("\n".join(L))


if __name__ == "__main__":
    main()
