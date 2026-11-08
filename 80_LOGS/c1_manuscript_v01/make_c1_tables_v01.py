#!/usr/bin/env python3
"""Results tables of the C1 confirmation for the manuscript, generated from the frozen analysis's decision file (the lead, 6 Nov 2026).
Every number is read from the decision JSON; nothing is typed by hand. Built and tested on the rehearsal's nuScenes stand-in decision
(70_TESTS/c1_v01/rehearsal150_v10/c1_decision_rehearsal_v09.json), never on an AV2 outcome before the run of record exists.
Tables: X (H1 per tracker: validity, V_t and removal reasons, Form B bounds), XI (every claim's status; family S with p, Holm and
confirmation; H8's cells), XIII (M*'s simultaneous upper bounds per population, descriptive). Refuses an existing output.
Usage: python -B make_c1_tables_v01.py --decision <c1_decision_r1.json> --out <tables.md> [--label "<text>"]
"""
import argparse
import hashlib
import json
import os
import sys

ROUTE = "within_lt3d"
POPS = (("PD7_primary", "PD7"), ("SD1_7_gap_le_5m", "SD1_7"), ("PD_inpath", "PD"))


def f(x, d=3):
    if x is None:
        return "–"
    if isinstance(x, bool):
        return "yes" if x else "no"
    if isinstance(x, float):
        return ("%." + str(d) + "f") % x
    return str(x)


def p_fmt(x):
    return "–" if x is None else ("%.2e" % x if x < 1e-3 else "%.4f" % x)


def table_h1(d):
    L = ["**Table X. H1 (primary) per tracker, within Argoverse 2 (own detector, 375 logs, decision mode).** Valid(M\\*) and the "
         "comparison set V_t (comparators not shown above δ at 1 − 0.0125/9); Form B's one-sided upper bound on the log-mean difference "
         "in infeasible-decision rate, M\\* minus comparator, at 1 − 0.0125/|V_t|; negative bounds favour M\\*.", ""]
    h1 = d["hypotheses"]["H1"]
    for t, bt in sorted(h1["by_tracker"].items()):
        L.append("*%s:* Valid(M\\*) %s; |V_t| = %s; Form B %s%s." % (t.upper(), f(bt.get("valid_method")), bt.get("n_V"), "met" if bt.get("met") else "not met",
                 " (vacuous)" if bt.get("vacuous") else ""))
    L += ["", "| Tracker | Comparator | In V_t | Why (removal condition, or why it stays) | M\\* − c, mean | Upper bound | Level |", "|---|---|---|---|---|---|---|"]
    for t, bt in sorted(h1["by_tracker"].items()):
        for c, r in sorted((bt.get("comparator_reasons") or {}).items()):
            vs = (bt.get("vs") or {}).get(c, {})
            why = r.get("stays_because") if r.get("in_V_t") else "; ".join(map(str, r.get("removed_by") or []))
            L.append("| %s | %s | %s | %s | %s | %s | %s |" % (t.upper(), c, f(r.get("in_V_t")), why, f(vs.get("mean_diff")), f(vs.get("ub")), f(vs.get("level"), 5)))
    L += ["", "C1 verdict: **%s**. Failed conditions: %s." % (d.get("C1_verdict"), "; ".join(d.get("failed_conditions") or []) or "none"),
          "Missing inputs: %s." % ("; ".join(d.get("missing_inputs") or []) or "none")]
    return L


def table_claims(d):
    fs = d.get("family_S") or {}
    L = ["**Table XI. Every claim's status.** Family S (H2, H3, H4, H6b, H10) by Holm at 0.025, opened only if H1 holds; p = (k + 1)/(B + 1). "
         "H8 is family P at 0.025; H6a and H7 are secondary validity statements; descriptive claims are never confirmed.", "",
         "| Claim | Label | Status | p | Confirmed (Holm) |", "|---|---|---|---|---|"]
    for k, v in d["hypotheses"].items():
        if k in ("FormA", "method_stage_provenance"):
            continue
        s = fs.get(k, {})
        L.append("| %s | %s | %s | %s | %s |" % (k, v.get("label", "")[:60], v.get("status"), p_fmt(s.get("p")), f(s.get("confirmed")) if s else "–"))
    h8 = d["hypotheses"].get("H8", {})
    if h8.get("cells"):
        L += ["", "**H8 cells (T1, B0, in-path cars, lateral, 2 s).** Record-weighted exceedance with the two-sided 95 % sup-t band over the 4 decision "
              "cells; FAILS if the lower end exceeds max(δ, E⁰).", "", "| Cell | Version | E | Items / logs | Threshold | Band | Verdict |", "|---|---|---|---|---|---|---|"]
        for c, v in h8["cells"].items():
            for ver in ("primary", "truth_oriented"):
                x = v.get(ver) or {}
                L.append("| %s | %s | %s | %s / %s | %s | [%s, %s] | %s |" % (c, ver.replace("_", "-"), f(x.get("E_rec")), x.get("n"), x.get("scenes"), f(x.get("threshold"), 4),
                                                                         f(x.get("lo")), f(x.get("hi")), x.get("verdict")))
    return L


def table_umax(d):
    u = ((d.get("Mstar_simultaneous_upper_bounds") or {}).get("by_route") or {}).get(ROUTE) or {}
    L = ["**Table XIII. M\\*'s simultaneous one-sided 95 %% upper bounds (descriptive, approximate; route %s).** Largest bound over the evaluable "
         "cells of each population, and the number of evaluable cells." % ROUTE, "", "| Tracker | Population | Evaluable cells | Largest upper bound |", "|---|---|---|---|"]
    for t, pops in sorted(u.items()):
        for key, name in POPS:
            x = pops.get(key) or {}
            cells = x.get("cells") or {}
            L.append("| %s | %s | %s | %s |" % (t.upper(), name, x.get("evaluable"), f(max(cells.values())) if cells else "–"))
    if not u:
        L.append("| – | – | – | route %s not in this decision file |" % ROUTE)
    return L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    a = ap.parse_args()
    assert not os.path.exists(a.out), "%s exists" % a.out
    raw = open(a.decision, "rb").read()
    d = json.loads(raw)
    L = ["<!-- generated by make_c1_tables_v01.py from %s (SHA-256 %s) %s -->" % (os.path.basename(a.decision), hashlib.sha256(raw).hexdigest(), a.label), ""]
    for part in (table_h1, table_claims, table_umax):
        L += part(d) + [""]
    with open(a.out, "w", encoding="utf-8", newline="\n") as fo:
        fo.write("\n".join(L))
    print("written", a.out)


if __name__ == "__main__":
    sys.exit(main())
