#!/usr/bin/env python3
"""Results material v02 (the lead, 6 Nov 2026) = v01 (kept) with the branch rule of 20_DESIGN/C1_REPORTING_FRAMES_v02.md §1:
per-tracker flags E, A, B, C, D from the verbatim reason strings (wording_by_tracker is not used), and the GO qualifiers
Q-empty, Q-zse and Q-construct.
v01: Results material of the C1 confirmation for Section V-F7, generated from the decision and analysis files (the lead, 6 Nov 2026).
Complements make_c1_tables_v01.py (its tables X, XI and XIII are included, renumbered X, XIII and XI as in manuscript v04) with:
  * the outcome branch of 20_DESIGN/C1_REPORTING_FRAMES_v01.md §1 (GO, NG-E, NG-A, NG-B, NG-C, NG-D), applied mechanically from
    hypotheses.H1.wording_by_tracker, failed_conditions and missing_inputs;
  * the plan's validity sentence (C1-PLAN §6.6) per tracker: k power-qualified cells and their record shares per population;
  * per-cell power at 0.10 / 0.12 / 0.15 / 0.20 and MDE80, summarised per population (min, median, max);
  * V_t with each comparator's removal condition or the reason it stayed; zero-SE effects;
  * Table XII: per arm and tracker on the within-AV2 route (shown above delta or not; pooled exceedance per population; flagged cells;
    infeasible-decision rate; V2 against its reference; V2_viol; mean margins on each arm's own relied pairs, secondary A6).
Every number is read from the files; nothing is typed by hand. Built and tested on the rehearsal's nuScenes stand-in
(70_TESTS/c1_v01/rehearsal150_v10/), never on an AV2 outcome before the run of record exists. Refuses an existing output.
Usage: python -B make_c1_results_v01.py --decision <decision.json> --analysis <analysis.json> --out <results.md> [--label "<text>"]
"""
import argparse
import hashlib
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import make_c1_tables_v01 as T  # noqa: E402

ROUTE = "within_lt3d"
POPS = T.POPS
ARMS = ("Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED")
ORDER = ("NG-E", "NG-A", "NG-B", "NG-C", "NG-D")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def _flags(d, t):
    """Frames v02 §1: flags for tracker t from nogo_reasons / failed_conditions and missing_inputs (verbatim strings)."""
    reasons = [c for c in (list(d.get("nogo_reasons") or []) + list(d.get("failed_conditions") or []))
               if c.startswith(t + " ") or c.startswith(t + ":")]
    miss = [m for m in (d.get("missing_inputs") or []) if m.startswith("H1 %s" % t)]
    f = set()
    if miss or any("arms missing from the run" in c or "comparators missing" in c for c in reasons):
        f.add("E")
    if any("M* NoFlag fails" in c or "pooled cell is shown above delta" in c or "M* family cell flagged" in c for c in reasons):
        f.add("A")
    if any("M* Floor fails" in c or "pooled cell is not evaluable" in c for c in reasons):
        f.add("B")
    if any("M* HK1c fails" in c for c in reasons):
        f.add("C")
    if any("M* not less infeasible than" in c for c in reasons):
        f.add("D")
    return [x for x in "EABCD" if x in f], reasons


def qualifiers(d, an=None):
    """Frames v02 §1 GO qualifiers per tracker: Q-empty, Q-zse, Q-construct."""
    out = {}
    z = (d.get("zero_se_effects") or {}).get("by_route", {}).get(ROUTE, {})
    for t, bt in sorted(d["hypotheses"]["H1"]["by_tracker"].items()):
        q = []
        V = list(bt.get("V") or [])
        if not V:
            q.append("Q-empty")
        if any(r.get("changed_V_t") for r in (z.get(t) or {}).values()):
            q.append("Q-zse")
        if V and an is not None:
            ir = an["k8"][ROUTE][t]["infeasible_rate"]
            rate = lambda c: (ir[c]["mean"] if isinstance(ir.get(c), dict) else ir.get(c))  # noqa: E731
            if all(c == "B3" or (rate(c) is not None and rate(c) > 0.5) for c in V):
                q.append("Q-construct")
        out[t] = q
    return out


def branch(d):
    """C1_REPORTING_FRAMES_v02 §1, applied mechanically. Returns (label, {tracker: [flags]})."""
    per = {t: _flags(d, t)[0] for t in sorted(d["hypotheses"]["H1"]["by_tracker"])}
    if d.get("C1_verdict") == "GO":
        assert all(not v for v in per.values()), ("GO with a flagged tracker", per)
        return "GO", per
    parts = ["NG-%s (%s)" % (x, ", ".join(t.upper() for t in sorted(per) if x in per[t])) for x in "EABCD"
             if any(x in v for v in per.values())]
    return (" + ".join(parts) if parts else "NO-GO (unflagged: see failed_conditions)"), per


def validity_sentence(d):
    L = ["**The plan's validity sentence (C1-PLAN §6.6), per tracker** (power-qualified family size k and its record share per "
         "population; 'floor at F_MIN 4 / 6 / 8' from the criteria audit).", ""]
    mp = d["Mstar_power_families"]["by_route"].get(ROUTE, {})
    for t in sorted(mp):
        parts = []
        for key, short in POPS:
            r = mp[t].get(key) or {}
            fl = r.get("floor_at_F_MIN", {})
            parts.append("%s: k = %s, share %s (floor at 4/6/8: %s/%s/%s)" % (
                short, r.get("family_size"), T.f(r.get("family_record_share")), T.f(fl.get("4")), T.f(fl.get("6")), T.f(fl.get("8"))))
        L.append("- *%s:* %s." % (t.upper(), "; ".join(parts)))
    return L + [""]


def power_summary(d):
    L = ["**Per-cell power of M\\*'s cells at planted exceedances 0.10, 0.12, 0.15 and 0.20, and MDE80** (min / median / max over the "
         "population's evaluable cells; descriptive, decides nothing).", "",
         "| Tracker | Population | cells | power 0.10 | power 0.12 | power 0.15 | power 0.20 | MDE80 |", "|---|---|---|---|---|---|---|---|"]
    mp = d["Mstar_power_families"]["by_route"].get(ROUTE, {})

    def mmm(xs):
        xs = [x for x in xs if isinstance(x, (int, float))]
        return "–" if not xs else "%.2f / %.2f / %.2f" % (min(xs), statistics.median(xs), max(xs))
    for t in sorted(mp):
        for key, short in POPS:
            r = mp[t].get(key) or {}
            pc, mde = r.get("per_cell", {}) or {}, r.get("mde80", {}) or {}
            cols = [mmm([v.get(lv) for v in pc.values()]) for lv in ("0.10", "0.12", "0.15", "0.20")]
            n_out = sum(1 for v in mde.values() if not isinstance(v, (int, float)))
            L.append("| %s | %s | %d | %s | %s; %d cells not reached by 0.20 |" % (t.upper(), short, len(pc), " | ".join(cols),
                                                                                  mmm(list(mde.values())), n_out))
    return L + [""]


def vt_reasons(d):
    L = ["**V_t per tracker, with each comparator's removal condition or the reason it stayed (removal at 1 − 0.0125/9).**", ""]
    for t, bt in sorted(d["hypotheses"]["H1"]["by_tracker"].items()):
        L.append("*%s:* V_t = {%s}." % (t.upper(), ", ".join(bt.get("V") or [])))
        for c, r in sorted((bt.get("comparator_reasons") or {}).items()):
            if r.get("in_V_t"):
                L.append("- %s stays: %s%s." % (c, r.get("stays_because"), (" (" + "; ".join(r.get("failing") or []) + ")") if r.get("failing") else ""))
            else:
                L.append("- %s removed: %s." % (c, "; ".join(r.get("removed_by") or [])))
    return L + [""]


def zero_se(d):
    L = ["**Zero-SE effects** (C1-PLAN §6.2; a comparator removed on a zero-SE point estimate, outside the removal budget).", ""]
    z = d["zero_se_effects"]["by_route"].get(ROUTE, {})
    any_ = False
    for t in sorted(z):
        for c, r in sorted(z[t].items()):
            if r.get("removed") or r.get("changed_V_t"):
                any_ = True
                L.append("- %s %s: removed %s; removed without zero-SE flags %s; V_t changed %s." % (
                    t.upper(), c, T.f(r.get("removed")), T.f(r.get("removed_without_zero_se_flags")), T.f(r.get("changed_V_t"))))
    if not any_:
        L.append("- None changed V_t on the within-AV2 route.")
    return L + [""]


def table_arms(a):
    L = ["**Table XII. Argoverse 2 (within route, decision mode), per arm and tracker:** shown above δ (no) or not; pooled exceedance on "
         "P_rel / P_near / P_ip; flagged P_rel cells of the evaluable ones; infeasible-decision rate; V2 on P_rel against its per-track "
         "reference; V2_viol on P_rel; mean lateral / longitudinal margin on each arm's own relied pairs (secondary A6; different outcome "
         "sets per arm).", "",
         "| Tracker | Arm | Valid | P_rel | P_near | P_ip | P_rel flagged | Infeasible | V2 (ref.) | V2_viol | Margin lat / long (m) |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    k8 = a["k8"][ROUTE]
    for t in ("t1", "t3"):
        if t not in k8 or k8[t] is None:
            L.append("| %s | – | route missing | | | | | | | | |" % t.upper())
            continue
        dt = k8[t]
        sec = (dt.get("calibration_relied_pairs_secondary") or {}).get("PD7_primary", {})
        for arm in ARMS:
            v = dt["validity_by_arm"].get(arm)
            if v is None:
                L.append("| %s | %s | missing | | | | | | | | |" % (t.upper(), arm))
                continue
            pe = [v["pops"][k]["pooled"]["E"] if v["pops"].get(k) else None for k, _ in POPS]
            fl = v["pops"]["PD7_primary"]
            ir = dt["infeasible_rate"].get(arm)
            ir = ir["mean"] if isinstance(ir, dict) else ir
            v2 = (dt["V2"]["PD7_primary"] or {}).get(arm) or {}
            m = sec.get(arm) or {}
            L.append("| %s | %s | %s | %s | %s | %s | %d / %d | %s | %s (%s) | %s | %s / %s |" % (
                t.upper(), arm.replace("Mstar", "M\\*"), T.f(v.get("valid_form_B")), T.f(pe[0]), T.f(pe[1]), T.f(pe[2]),
                len(fl.get("flagged", [])), fl.get("evaluable", 0), T.f(ir), T.f((v2.get("V2") or {}).get("E")),
                T.f((v2.get("V2") or {}).get("reference_E")), T.f((v2.get("V2_viol") or {}).get("E")),
                T.f(m.get("mean_margin_lat"), 2), T.f(m.get("mean_margin_long"), 2)))
    return L + [""]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--decision", required=True)
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="")
    a_ = ap.parse_args()
    assert not os.path.exists(a_.out), "%s exists" % a_.out
    d = json.load(open(a_.decision, encoding="utf-8"))
    an = json.load(open(a_.analysis, encoding="utf-8"))
    overall, per = branch(d)
    L = ["# C1 results material for Section V-F7 %s" % a_.label, "",
         "Decision: `%s` (SHA-256 %s). Analysis: `%s` (SHA-256 %s). Stamp: %s." % (a_.decision, sha(a_.decision), a_.analysis,
                                                                               sha(a_.analysis), d.get("stamp")), "",
         "**Verdict:** %s. **Reporting-frames branch (C1_REPORTING_FRAMES_v02 §1):** %s; flags per tracker: %s. **GO qualifiers:** %s." % (
             d.get("C1_verdict"), overall, "; ".join("%s %s" % (t.upper(), ", ".join(b) or "none") for t, b in sorted(per.items())),
             "; ".join("%s %s" % (t.upper(), ", ".join(q) or "none") for t, q in sorted(qualifiers(d, an).items()))),
         "", "**H1 wording per tracker (the code's label; not used for the branch):** %s." % "; ".join(
             "%s: %s" % (t.upper(), w) for t, w in sorted(d["hypotheses"]["H1"].get("wording_by_tracker", {}).items())), "",
         "**Failed or missing conditions (verbatim):**", ""]
    L += ["- %s" % c for c in (d.get("failed_conditions") or [])] or ["- none"]
    L += ["", "**Missing inputs (verbatim):**", ""] + (["- %s" % m for m in (d.get("missing_inputs") or [])] or ["- none"]) + [""]
    L += T.table_h1(d) + [""] + validity_sentence(d) + power_summary(d) + vt_reasons(d) + zero_se(d)
    L += [x.replace("**Table XIII.", "**Table XI.") for x in T.table_umax(d)] + [""]
    L += table_arms(an)
    L += [x.replace("**Table XI.", "**Table XIII.") for x in T.table_claims(d)] + [""]
    with open(a_.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(L) + "\n")
    print("written", a_.out, "| verdict", d.get("C1_verdict"), "| branch", overall)


if __name__ == "__main__":
    sys.exit(main())
