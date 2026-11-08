#!/usr/bin/env python3
"""X3 gates summary (x3-core agent, x3_gates_report_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of
record; not part of the registered test). Plan section 1.

Reads the V0 and V2 gate JSONs (x3_gates_v01) and the V1 JSON (x3_screen_v01 v1); applies V1's rule: agreement with the statuses
of record is reported arm by arm; a disagreement is acceptable only for a decisive quantity within about 3 MC SE of its threshold
(R21 step 3's MC SE as the yardstick). The MC SE at B = 4000: R21 step 3's empirical MC SE at B = 40000 scaled by sqrt(10)
where R21 measured that quantity class (a comparator's removal statistic, M*'s pooled LB and HK1c UB); otherwise X3's own
order-statistic MC SE of that exact bound at B = 4000 (x3_screen_v01.simul_detail); both z-values are reported. A status
disagreement (Valid, shown above, removal) gates; a component-only difference (same statuses) is reported, not gating. A difference
in a deterministic part (evaluable count, power-family size, hence the floor) is never acceptable. Writes gates/x3_gates_v01.json and .md.
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_common_v01 as C  # noqa: E402

GD = os.path.join(C.OUT, "gates")
R21 = os.path.join(C.W, "70_TESTS", "R21_c1_v01", "real", "r21_mcse_fixed_r1.json")
K_SET = ("B0", "B1", "B3", "B4", "B6", "B9", "RETUNED")
POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")
STAT_OF = {"NoFlag": "cells_max", "FamFlag": "family_max", "NoFlag_pool": "pooled_flag", "HK1c": "hk1c"}


def r21_mcse():
    d = json.load(open(R21))
    out = {}
    for rt, v in d["routes"].items():
        if not rt.startswith("within_lt3d/"):
            continue
        t = rt.split("/")[1]
        out[t] = {k: q.get("mc_se_empirical") for k, q in v["decisive_quantities"].items()}
    return out


def yardstick(r21, t, arm, pop, kind, own):
    """(MC SE used, z-basis, both values). Primary: R21 step 3's empirical MC SE (B = 40000) x sqrt(10) where R21 measured that
    quantity class (a comparator of K: its removal statistic; M*: pooled LB and HK1c UB); otherwise X3's own order-statistic MC SE of
    that exact bound at B = 4000."""
    q, name = None, None
    if arm in K_SET and kind in ("cells_max", "family_max", "pooled_flag"):
        q, name = (r21.get(t) or {}).get("removal_stat %s" % arm), "R21 removal_stat %s" % arm
    elif arm == "Mstar" and kind == "hk1c":
        q, name = (r21.get(t) or {}).get("HK1c UB M* %s" % pop), "R21 HK1c UB M* %s" % pop
    elif arm == "Mstar" and kind == "pooled_flag":
        q, name = (r21.get(t) or {}).get("pooled LB M* %s" % pop), "R21 pooled LB M* %s" % pop
    r21v = q * math.sqrt(10) if q is not None else None
    ownv = own if own is not None and math.isfinite(own) and own > 0 else None
    if r21v is not None:
        return r21v, "%s x sqrt(10) (B 40000 -> 4000)" % name, {"r21_x_sqrt10": r21v, "x3_own": ownv}
    return ownv, "x3 order-statistic MC SE at B = 4000", {"r21_x_sqrt10": None, "x3_own": ownv}


def _z(stat, se):
    return (abs(stat) / se) if se else None


def judge_v1(v1):
    """Status disagreements (Valid, shown above, removal) gate: every differing component behind them must have its decisive
    statistic within 3 MC SE of the threshold (primary yardstick). Component-only differences (same statuses) are reported with
    their z-values and do not gate. A deterministic difference (evaluable count, family size, floor) always fails."""
    r21 = r21_mcse()
    out, ok_all = {}, True
    for t, r in v1["by_tracker"].items():
        per = {}
        for arm, e in r["by_arm"].items():
            if arm == "RETUNED_HK1":
                a = e["agree"]
                good = a["valid"] and a["shown_above"] and a["all_components"]
                per[arm] = {"agree": good, "status_agree": a["valid"] and a["shown_above"], "acceptable": good, "detail": a,
                            "selection_rerun": e.get("selection_rerun")}
                ok_all = ok_all and good
                continue
            a = e["agree"]
            status_agree = bool(a["valid"] and a["shown_above"] and e["removal_agree"])
            if status_agree and a["all_components"]:
                per[arm] = {"agree": True, "status_agree": True, "acceptable": True}
                continue
            diffs, acceptable = [], True
            dec = e.get("decisive") or {}
            for comp, same in a["components"].items():
                if same:
                    continue
                pop, k_ = comp.split("/")
                d = {"component": comp, "x3": e["x3"]["pops"][pop].get(k_), "record": e["record_pops"][pop].get(k_)}
                if k_ in ("family_size", "evaluable", "Floor"):
                    d.update({"deterministic": True, "within_3": False})
                    acceptable = False
                else:
                    kind = STAT_OF.get(k_, "cells_max" if k_ == "flagged_cells" else "family_max")
                    q = (dec.get(pop) or {}).get(kind)
                    if q is None:
                        d.update({"within_3": False, "why": "no decisive statistic"})
                        acceptable = acceptable and status_agree
                    elif k_ in ("flagged_cells", "family_flagged"):
                        mine, rec_cells = set(e["x3"]["pops"][pop][k_]), set(e["record_cells"][pop][k_])
                        d["record"] = sorted(rec_cells)
                        cells = q.get("all") or {}
                        d["cells"] = {}
                        w_all = True
                        for c in sorted(c for c in cells if (c in mine) != (c in rec_cells)) or [q["cell"]]:
                            s_, mc_ = cells.get(c, [q["stat"], q["mcse"]])
                            ys, basis, both = yardstick(r21, t, arm, pop, kind, mc_)
                            within = ys is not None and abs(s_) <= 3 * ys
                            d["cells"][c] = {"stat": s_, "mcse_used": ys, "basis": basis, "z": _z(s_, ys), "z_r21_x_sqrt10": _z(s_, both["r21_x_sqrt10"]),
                                             "z_x3_own": _z(s_, both["x3_own"]), "within_3": within}
                            w_all = w_all and within
                        d["within_3"] = w_all
                    else:
                        ys, basis, both = yardstick(r21, t, arm, pop, kind, q["mcse"])
                        within = ys is not None and abs(q["stat"]) <= 3 * ys
                        d.update({"statistic": kind, "cell": q.get("cell"), "stat": q["stat"], "mcse_used": ys, "basis": basis, "z": _z(q["stat"], ys),
                                  "z_r21_x_sqrt10": _z(q["stat"], both["r21_x_sqrt10"]), "z_x3_own": _z(q["stat"], both["x3_own"]), "within_3": within})
                    if not status_agree and not d.get("within_3"):
                        acceptable = False
                d["gating"] = not status_agree
                diffs.append(d)
            if not e["removal_agree"]:
                diffs.append({"component": "removal (flags only)", "x3": e["removal_x3"], "record": e["removal_record"],
                              "note": "judged through the flag components above", "gating": True})
            per[arm] = {"agree": False, "status_agree": status_agree, "acceptable": bool(acceptable),
                        "valid": [e["x3"]["valid"], e["record"]["valid"]], "shown_above": [e["x3"]["shown_above"], e["record"]["shown_above"]],
                        "differences": diffs}
            ok_all = ok_all and acceptable
        out[t] = per
    return out, ok_all


def md(summary):
    L = ["# X3 validation gates V0, V1, V2", "", "**%s**" % C.STAMP, "", "Plan section 1. Overall: **%s**." % ("PASSED" if summary["passed"] else "FAILED"), ""]
    L += ["## V0: the runner reproduces the runs of record", "", "| tracker | arm | decisions | counts | cal | episode summaries | equal |", "|---|---|---|---|---|---|---|"]
    for t, g in summary["V0"].items():
        for arm, r in g["by_arm"].items():
            L.append("| %s | %s | %s (%d rows) | %s (%d rows) | %s | %s | %s |" % (t, arm, r["decisions_equal"], r["decision_rows"][0], r["counts_equal"], r["count_rows"][0],
                                                                       r["cal_equal"], r["episode_summaries_equal"], r["equal"]))
    L += ["", "V0 gate arms: M*, B0, B4, B6, B9 on T1 and T3; B1, B3 (T1, T3) and M* (tab) are compared the same way (reported).", ""]
    L += ["## V2: partition sums equal the counts of record", "", "| tracker | arm | partitions x populations x logs equal | records (PD7) |", "|---|---|---|---|"]
    for t, g in summary["V2"].items():
        for arm, r in g["by_arm"].items():
            L.append("| %s | %s | %s | %d |" % (t, arm, r["equal"], r["by_partition"]["P1_track_speed"]["PD7_primary"]["records"]))
    L += ["", "## V1: the X3 screen (B = 4000) against the statuses of record (B = 40000)", ""]
    for t, per in summary["V1_judged"].items():
        n = len(per)
        ag = sum(1 for v in per.values() if v["agree"])
        sa = sum(1 for v in per.values() if v.get("status_agree"))
        L += ["### %s: status (Valid, shown above, removal) agrees for %d of %d arms; every component for %d" % (t.upper(), sa, n, ag), ""]
        dis = {a_: v for a_, v in per.items() if not v["agree"] and "differences" in v}
        if dis:
            L += ["| arm | Valid (X3 / record) | shown above (X3 / record) | status disagreement (gating) | differing component | statistic (LB - delta, or UB - 0.08) | z (primary) | z (R21 x sqrt 10) | z (X3 own) | within 3 |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
            fz = lambda x: ("%.2f" % x) if x is not None else "n/a"  # noqa: E731
            for a_, v in dis.items():
                gate = "yes" if not v["status_agree"] else "no"
                for d in v.get("differences", []):
                    if "cells" in d:
                        for c, q in d["cells"].items():
                            L.append("| %s | %s | %s | %s | %s %s | %.5f | %s | %s | %s | %s |" % (a_, v["valid"], v["shown_above"], gate, d["component"], c, q["stat"],
                                                                                   fz(q["z"]), fz(q["z_r21_x_sqrt10"]), fz(q["z_x3_own"]), q["within_3"]))
                    elif "stat" in d:
                        L.append("| %s | %s | %s | %s | %s (%s) | %.5f | %s | %s | %s | %s |" % (a_, v["valid"], v["shown_above"], gate, d["component"], d.get("cell") or "pooled",
                                                                                  d["stat"], fz(d["z"]), fz(d["z_r21_x_sqrt10"]), fz(d["z_x3_own"]), d["within_3"]))
                    else:
                        L.append("| %s | %s | %s | %s | %s: X3 %s, record %s | | | | | %s |" % (a_, v["valid"], v["shown_above"], gate, d["component"], d.get("x3"), d.get("record"),
                                                                                d.get("within_3", "see above")))
            L.append("")
        hk = per.get("RETUNED_HK1")
        if hk and hk.get("selection_rerun"):
            sr = hk["selection_rerun"]
            L += ["RETUNED-HK1: composite status agrees: %s; selection re-run at B = 4000 reproduces the record's per-fold choice: %s (%s)." % (
                hk["agree"], sr["agree"], ", ".join("%s: %s" % (f, c["point"]) for f, c in sorted(sr["choice_by_fold"].items(), key=lambda x: int(x[0])))), ""]
    L += ["Infeasible rates recomputed from the outputs of record equal the record's (every arm): %s." % summary.get("V1_rates_equal"), ""]
    L += ["## Timing", "", "One hk1_rule call on the 375 logs at B = 4000: %s s (B = 2000 inside the selection only if > 60 s: %s)." % (
        summary.get("timing"), summary.get("B_selection")), ""]
    return "\n".join(L)


def main():
    v0 = {t: json.load(open(os.path.join(GD, "x3_v0_%s_v01.json" % t))) for t in ("t1", "t3", "tab") if os.path.exists(os.path.join(GD, "x3_v0_%s_v01.json" % t))}
    v2 = {t: json.load(open(os.path.join(GD, "x3_v2_%s_v01.json" % t))) for t in ("t1", "t3", "tab") if os.path.exists(os.path.join(GD, "x3_v2_%s_v01.json" % t))}
    v1 = json.load(open(os.path.join(GD, "x3_v1_v01.json")))
    tm = json.load(open(os.path.join(GD, "x3_hk1_timing_v01.json")))
    judged, v1_ok = judge_v1(v1)
    v0_ok = all(v0[t]["passed"] for t in ("t1", "t3")) and all(v0[t]["by_arm"][a]["equal"] for t in ("t1", "t3") for a in ("Mstar", "B0", "B4", "B6", "B9"))
    v2_ok = all(g["passed"] for g in v2.values())
    rates_eq = all(all(r["infeasible_rate_equal_record"].values()) for r in v1["by_tracker"].values())
    mx = max(tm["seconds_per_hk1_rule_call"].values())
    summary = {"stamp": C.STAMP, "V0": v0, "V2": v2, "V1_judged": judged, "V1_ok": v1_ok, "V0_ok": v0_ok, "V2_ok": v2_ok,
               "V1_rates_equal": rates_eq, "timing": tm["seconds_per_hk1_rule_call"], "B_selection": 2000 if mx > 60 else 4000,
               "passed": bool(v0_ok and v1_ok and v2_ok)}
    C.jdump(os.path.join(GD, "x3_gates_v01.json"), summary)
    C.wtext(os.path.join(GD, "x3_gates_v01.md"), md(summary))
    print(json.dumps({"V0": v0_ok, "V1": v1_ok, "V2": v2_ok, "passed": summary["passed"], "B_selection": summary["B_selection"]}))


if __name__ == "__main__":
    main()
