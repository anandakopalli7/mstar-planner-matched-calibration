#!/usr/bin/env python3
"""C1 analysis v09 (Claude line, c1_analyse_v09, 5 Nov 2026) = c1_analyse_v08 (copied; v08 is kept unchanged and unbound as an entry
point) with D16 v26 Choice 47:
  (e) M2, the stricter direction. A COMPARATOR is shown above delta (and so leaves V_t) only through a flagged cell, a flagged family
      cell or a flagged pooled cell, in any of PD7, SD1_7 and PD. The term "pooled upper bound above delta + 0.03" (not HK1c) no longer
      removes a comparator: a comparator that fails only HK1c stays in V_t, so M* must still beat it on operability (a lack of precision
      is not evidence above delta; Choice 9's logic). M*'s own validity still requires HK1c (unchanged), and M*'s status, wording and
      every other rule are v08's. Form B (form_b, replaced in c1_analyse_v02's namespace as c1_analyse_v03 does) lists, per
      comparator, the conditions that removed it from V_t, or why it stays (valid; floor only, Choice 9; HK1c only, Choice 47e), and
      the decision carries them per route and tracker ("V_t_reasons").
  (f) M3, descriptive and never gated: for M*, per route, tracker and population (PD7, SD1_7, PD), the simultaneous one-sided 95 %
      upper bound of every evaluable cell (k6_analyse_v02.flag's upper bound, the sup-t family of the population's evaluable cells,
      the same bootstrap draws as the validity test) and their maximum ("Mstar_simultaneous_upper_bounds"). Read as: M*'s exceedance
      is at most U in every evaluable cell, simultaneously at 95 %. No rule reads it.
  (m13) A family in which M* has zero exceedance in every bootstrap draw (non-finite sup-t quantile) is judged as for the comparators:
      each zero-SE cell by E-hat > delta (k6_analyse_v02.flag), and the family is reported ("Mstar_zero_se_families"); it no longer
      raises (k8_analyse_v04.STRICT_Q is set False in every mode).
  (c) B3: the config must carry "h9_label" explicitly, "secondary" or "descriptive"; a missing key or another value is refused (no
      default). H9's status when its floor fails: the frozen predictor arm (c1_predarm_v06, h9_rule_v05) sets H9 = false for a tracker
      whose power-qualified E2 family has fewer than 6 cells (condition (a) of H9); this analysis then gives H9 the status
      "does not hold: floor not met" (claims_status["H9"] and hypotheses["H9"]["status"]), with the reason "floor not met
      (condition a: >= 6 power-qualified E2 cells): <tracker> family_size_E2 = n < 6", and the "H9_floor" block lists
      family_size_E2, floor and floor_met per tracker. A failure with the floor met on both trackers (a flag) stays "does not hold".
      H9 is "not tested" only if its table is missing, not provenance-valid or has no TPP arm.
  m-5 (D16 v27 Choice 48b): Q1 never appears among the missing inputs, in any exception path.
  49(c) (D16 v28): H3's comparator set V^J (joint_b, replaced in c1_analyse_v02's namespace) also keeps a comparator that fails only the
      pooled bound on the joint loss (ub > delta + 0.03, with the estimate present, evaluable and unflagged in every population), as
      47(e) does for V_t; its reasons are listed ("VJ_hk1c_only", "comparator_reasons"). M*Jx's own validity is unchanged.
CRITERIA (D16 v30 Choice 50, 90_DECISIONS/D16_DELEGATED_CHOICES_v30.md; register 90_DECISIONS/C1_CRITERIA_REGISTER_v02.md; ICH E9 5.5;
  every value in c1_rules_v01, one place):
  * evidence AGAINST M* at one-sided 0.05 (unchanged): M*'s cell, family and pooled flags (Valid in H1, H3, H4), H6a, H7, H9;
  * a bound SUPPORTING M* at one-sided 0.025: Form B's UB^{1 - 0.025/|V_t|} (H1, H4; H3 at 0.025/|V^J_t|); Form C (H2) and H10's NI
    part at UB^{0.975}; H6b's and H10's cell parts (the comparator's flag and the paired sup-t lower bound) at 0.975; Holm's family S
    at 0.025; Form A at 0.025/4;
  * a comparator leaves V_t only if one of its 9 removal conditions holds at one-sided 1 - 0.025/9 (H3's V^J_t: each of 3 at
    1 - 0.025/3); M*'s own validity stays at 0.95; the removal reasons state the level;
  * D16 v33 Choice 52: (c) H1's budget is split: removal at 1 - 0.0125/9 and Form B at UB^{1 - 0.0125/|V_t|}; H3's V^J removal at
    1 - 0.0025/3 and H3's p doubled (capped at 1) before Holm; (d) B = 20000 for every bootstrap of this analysis (the power rule keeps
    the first 500 weight rows, which do not depend on B); (b) h9_label must be "descriptive" in a C1 run, and the decision's H9_descriptive
    block reports H9's estimates, cell bounds, family size and floor status; (e) in family S the p-value governs (Holm), the status
    follows it, and the bound at the Holm-assigned level is reported beside it with any disagreement (S_decision_forms); for H1 the
    bound governs.
  * HK1c's (and ValidJ's) pooled upper bound at HK1C_LEVEL = 0.995 (D16 v30 Choice 50(c)), margin delta + 0.03 unchanged;
  * the power families by the target-only rule (P 0.15, rho 0.5, power >= 0.80, 2000 datasets, 500 weight rows, seeds unchanged);
  * descriptive, never gated: per power family the share of the population's records it covers and the floor at F_MIN 4, 6, 8;
    M*'s per-cell power at P 0.10, 0.12, 0.20 (500 datasets) and MDE80; every zero-SE case and whether it changed V_t; M*'s upper
    bounds labelled approximate;
  * a config that states any rule constant (or c) differently from c1_rules_v01 is refused (c1_rules_v01.config_check).
  The rules are installed by c1_rules_v01.apply_analysis (k8_analyse_v04.hk1_rule, analyse_decide and joint_section;
  c1_analyse_v02.form_a, form_c, h10_rule, h6_rules; c1_analyse_v05.holm_v05). This module's hk1_rule_v09 is replaced by
  c1_rules_v01.hk1_rule_criteria, which also carries 47(f)'s upper bounds.
Everything else is c1_analyse_v08's behaviour.
C1 analysis v08 (Claude line, c1_analyse_v08, 5 Nov 2026) = c1_analyse_v07 (kept, imported: e0_check, load_table, check_route_c1; and
through it c1_analyse_v06's decide_all, routes, claims and rules, all unchanged) on c1_guard_v05, with D16 v23 Choice 44 and v24 Choice 45c:
  * 44(d), 45(c) M-D: Q1 (QCNet) is not tested in C1. A config with a "q1" entry is refused. The decision reports Q1 as "not tested" with
    Choice 44(d)'s two reasons, in its own block, outside H1, H9 and family S. C1_verdict, gate_H1, H9 and family S are those of
    c1_analyse_v06.decide_all (Q1 is never read). Q1 is not listed among the missing inputs, because it was decided before any outcome.
  * 44(f) m1: on AV2 (--c1) the guard writes the run-log "start" line, and the analysis records the run log's hash. Every table it
    consumes must have a "done" line in the verified, chained run log whose output hash equals the file's SHA-256: the method-stage, H8,
    H9 and descriptive H9 tables, and every route's run record. A table without one is not provenance-valid (the claim it carries is
    then "not tested", Choice 33). A route's run record without one is a route problem. A broken chain refuses the analysis.
  * the rest as v07: the deposit record on AV2, tables with the current deposit_record_sha256, H8 on the folds units (h8_units), E0's
    recompute from the quarantine (on c1_guard_v05), an existing --out or --decision refused on AV2, the "done" line after the outputs.
Usage: as c1_analyse_v07 (the config holds no "q1" entry).
"""
import argparse
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v05 as G  # noqa: E402
import c1_analyse_v07 as A7  # noqa: E402
import c1_rules_v01 as R  # noqa: E402

A6 = A7.A6
A5, B, K = A6.A5, A6.B, A6.K
TRACKERS, DESCRIPTIVE_TRACKERS, FAMILY_S = A6.TRACKERS, A6.DESCRIPTIVE_TRACKERS, A6.FAMILY_S
ROLE = "entry:c1_analyse"
TABLE_ROLES, DESC_TABLES = A6.TABLE_ROLES, A6.DESC_TABLES
_exc = A6._exc


# ---------------------------------------------------------------------------------------------------------------- v09 (Choice 47)
import numpy as np  # noqa: E402

A_ = B.A
H9_LABELS = ("secondary", "descriptive")
_ARM_STATUS_V02 = B.arm_status
UB_KEY = R.UB_KEY
UB_LABEL = ("descriptive (Choice 47f; never gated): M*'s simultaneous one-sided 95 % upper bound of every evaluable cell of the "
            "population (sup-t over its evaluable cells, the validity test's bootstrap draws) and their maximum; " + R.UB_APPROX_LABEL)


def configure_v09(mode):
    """c1_analyse_v02.configure, then m13: no sup-t quantile raises, for M* as for every comparator."""
    B.configure(mode)
    K.STRICT_Q = False


def check_h9_label(cfg):
    """47(c): the label is explicit; no default."""
    assert "h9_label" in cfg, "the config has no h9_label: it must be stated explicitly (D16 v26 Choice 47c; no default)"
    assert cfg["h9_label"] in H9_LABELS, "h9_label must be one of %s, not %r (Choice 47c)" % (H9_LABELS, cfg["h9_label"])
    return cfg["h9_label"]


def arm_status_v09(v):
    """c1_analyse_v02.arm_status unchanged (M*'s validity and every arm's 'shown_above' as v08), plus what (f) and m13 report."""
    st = _ARM_STATUS_V02(v)
    if UB_KEY in v:
        st[UB_KEY] = v[UB_KEY]
    if v.get("zero_se_quantiles"):
        st["zero_se_quantiles"] = list(v["zero_se_quantiles"])
    pops = v.get("pops") or {}
    st["criteria"] = {"levels": v.get("levels"), "power_rule": v.get("power_rule"),
                      "zero_se": {p: {"cells": list(r.get("zero_se_flagged") or []), "family": list(r.get("zero_se_family_flagged") or []),
                                      "pooled": bool((r.get("pooled") or {}).get("zero_se_flagged"))} for p, r in pops.items()},
                      "families": {p: {"family_size": r.get("family_size"), "record_share": r.get("family_record_share"),
                                       "floor_at_F_MIN": r.get("floor_at_F_MIN")} for p, r in pops.items()}}
    if "descriptive_power" in v:
        st["descriptive_power"] = v["descriptive_power"]
    return st


def comparator_reasons(st):
    """47(e): why a comparator leaves V_t (flags only) or stays (valid; floor only; HK1c only; pooled not evaluable). The criteria
    decision: the flags are the comparator's removal conditions at one-sided 1 - 0.025/9; each reason states the level used."""
    removed, other = [], []
    lvl = ((st.get("criteria") or {}).get("levels") or {}).get("flags")
    at = (" at one-sided %.5f" % lvl) if lvl else ""
    for p, r in st["pops"].items():
        if not r["NoFlag"]:
            removed.append("%s: cell flagged%s (%s)" % (p, at, ", ".join(r.get("flagged_cells") or [])))
        if r["FamFlag"]:
            removed.append("%s: power-qualified family cell flagged%s (%s)" % (p, at, ", ".join(r.get("family_flagged") or [])))
        if r["pooled_evaluable"] and not r["NoFlag_pool"]:
            removed.append("%s: pooled cell flagged%s" % (p, at))
        if not r["Floor"]:
            other.append("%s: floor not met" % p)
        if r["pooled_evaluable"] and not r["HK1c"]:
            other.append("%s: HK1c fails (pooled upper bound above delta + 0.03)" % p)
        if not r["pooled_evaluable"]:
            other.append("%s: pooled cell not evaluable" % p)
    return removed, other


def shown_above_v09(st):
    return bool(comparator_reasons(st)[0])


def removal_split(st):
    """(removed, removed without the zero-SE flags): a removal that rests only on zero-SE cells (judged by E-hat > delta) changed
    V_t through the zero-SE rule (reported, criteria item 7)."""
    zs = (st.get("criteria") or {}).get("zero_se") or {}
    rem = rem_wo = False
    for p, r in st["pops"].items():
        z = zs.get(p) or {"cells": [], "family": [], "pooled": False}
        cf, ff = list(r.get("flagged_cells") or []), list(r.get("family_flagged") or [])
        pf = bool(r["pooled_evaluable"] and not r["NoFlag_pool"])
        rem = rem or bool(cf or ff or pf)
        rem_wo = rem_wo or bool([c for c in cf if c not in z["cells"]] or [c for c in ff if c not in z["family"]] or (pf and not z["pooled"]))
    return rem, rem_wo


def form_b(status, rate, Ws, method="Mstar", comps=B.K_SET, alpha=R.ALPHA_FORM_B):
    """c1_analyse_v03.form_b with V_t = the comparators NOT shown above delta by a flag (47e), and the reasons per comparator."""
    present = [c for c in comps if c in status and c in rate]
    missing = [c for c in comps if c not in present]
    reasons = {c: comparator_reasons(status[c]) for c in present}
    V = [c for c in present if not reasons[c][0]]
    level = 1 - alpha / max(len(V), 1)
    per, bms = {}, {}
    for c in V:
        r = B.paired(rate, Ws, method, c, level)
        bms[c] = r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    vac = not V
    valid_m = bool(method in status and status[method]["valid"])
    met = bool(valid_m and not missing and all(v["lower"] for v in per.values()))
    p = None if vac else min(1.0, len(V) * max(v["p_lt0"] for v in per.values()))
    holm = {}
    for a in R.HOLM_LEVELS:   # Choice 52(e): the bound form at every level Holm can assign (H4 is in family S)
        la = 1 - a / max(len(V), 1)
        ubs = {c: R.bm_quantile(bms[c], la) for c in V}
        holm["%.6f" % a] = {"level": la, "ub": ubs, "holds": bool(valid_m and not missing and all(u < 0 for u in ubs.values()))}
    why = {}
    for c in present:
        rem, oth = reasons[c]
        if rem:
            why[c] = {"in_V_t": False, "removed_by": rem, "also_failing": oth}
        else:
            stays = "valid" if status[c]["valid"] else ("HK1c only (stays in V_t: Choice 47e)" if any("HK1c" in x for x in oth) and
                                                         all(("HK1c" in x) for x in oth) else "not valid, not shown above delta")
            why[c] = {"in_V_t": True, "stays_because": stays, "failing": oth}
    return {"method": method, "valid_method": bool(method in status and status[method]["valid"]), "V": V,
            "in_V_by_choice9": [c for c in V if status[c]["floor_only"]],
            "in_V_hk1c_only": [c for c in V if not status[c]["valid"] and status[c]["shown_above"]],
            "removed_shown_above": [c for c in present if c not in V], "missing": missing, "n_V": len(V), "level": level, "vs": per,
            "met": met, "vacuous": vac, "p_rejection_bonferroni": p, "comparator_reasons": why,
            "alpha": alpha, "removal_level": R.LEVEL_REMOVAL_V, "holm_levels": holm, "p_threshold_H1": alpha,
            "rule": "C1 v04 5.4 FormB with Choice 9 (E13); a missing comparator fails it (D16 Choice 25); empty V_t is vacuous; "
                    "a comparator leaves V_t only through a flag (D16 v26 Choice 47e: not through HK1c) at one-sided 1 - 0.0125/9; "
                    "superiority at 1 - 0.0125/|V_t| (D16 v33 Choice 52c: H1's 0.025 split between removal and superiority)"}


def joint_hk1c_only(js):
    """49(c): a comparator whose joint status fails only the pooled bound (ub > delta + 0.03): in every population the joint estimate
    exists, is evaluable and is not flagged, and at least one population fails only that bound."""
    pops = js["pops"].values()
    return bool(not js["validJ"] and all(r.get("E") is not None and r.get("evaluable") and not r.get("flagged") for r in pops))


def joint_b(jstat, rate, Ws, method="MstarJx", comps=B.KJ_SET, alpha=R.ALPHA_FOR, mult=R.H3_P_MULTIPLIER):
    """c1_analyse_v03.joint_b, with D16 v28 Choice 49(c): H3's comparator set V^J also keeps a comparator that fails only the pooled
    bound (imprecision is not evidence above delta), as Form B's V_t does under Choice 47(e). M*Jx's own validity is unchanged."""
    present = [c for c in comps if c in jstat and c in rate]
    missing = [c for c in comps if c not in present]
    hk = [c for c in present if joint_hk1c_only(jstat[c])]
    V = [c for c in present if jstat[c]["validJ"] or c in hk]
    level = 1 - alpha / (mult * max(len(V), 1))   # Choice 52(c): the bound dual of the doubled p at the nominal alpha
    per, bms = {}, {}
    for c in V:
        r = B.paired(rate, Ws, method, c, level)
        bms[c] = r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    vac = not V
    valid_m = bool(method in jstat and jstat[method]["validJ"])
    met = bool(valid_m and not missing and all(v["lower"] for v in per.values()))
    p = None if vac else min(1.0, mult * len(V) * max(v["p_lt0"] for v in per.values()))   # Choice 52(c): doubled, capped at 1
    holm = {}
    for a in R.HOLM_LEVELS:
        la = 1 - a / (mult * max(len(V), 1))
        ubs = {c: R.bm_quantile(bms[c], la) for c in V}
        holm["%.6f" % a] = {"level": la, "ub": ubs, "holds": bool(valid_m and not missing and all(u < 0 for u in ubs.values()))}
    why = {c: ("valid" if jstat[c]["validJ"] else "pooled bound only (stays: Choice 49c)" if c in hk else
               "removed: " + "; ".join("%s %s" % (p_, ("flagged at one-sided %.5f" % R.LEVEL_REMOVAL_VJ) if r.get("flagged") else "not evaluable" if not r.get("evaluable")
                                                   else "no estimate" if r.get("E") is None else "bound")
                                       for p_, r in jstat[c]["pops"].items() if not r.get("validJ"))) for c in present}
    return {"method": method, "validJ_method": valid_m, "VJ": V, "VJ_hk1c_only": hk, "missing": missing, "level": level, "vs": per,
            "met": met, "vacuous": vac, "p_rejection_bonferroni": p, "comparator_reasons": why,
            "alpha": alpha, "removal_level": R.LEVEL_REMOVAL_VJ, "p_multiplier": mult, "holm_levels": holm,
            "rule": "V^J = comparators valid on the joint loss (flag at one-sided 1 - 0.0025/3), plus those failing only the pooled bound "
                    "(D16 v28 Choice 49c); p = min(1, 2 |V^J| max p) into Holm; nominal bound 1 - 0.025/(2 |V^J|) (D16 v33 Choice 52c)"}


for _n, _f in (("form_b", form_b), ("arm_status", arm_status_v09), ("joint_b", joint_b)):
    setattr(B, _n, _f)
R.apply_analysis(B, A6.A5)


def add_v09_blocks(dec, results_all):
    """47(e), (f), m13 and (c): reported beside the decision; no claim or status reads them. 48(b) m-5: Q1 is never a missing input,
    whatever path set it (Q1 stays "not tested" with Choice 44d's reasons)."""
    dec["missing_inputs"] = [x for x in dec.get("missing_inputs", []) if not str(x).startswith("Q1")]
    ub, why, zse, h9f, mpf, cpf, zeff = {}, {}, {}, {}, {}, {}, {}
    for route, by in sorted(results_all.items()):
        for t, out in sorted(by.items()):
            if not out:
                continue
            sm = (out.get("status") or {}).get("Mstar") or {}
            if UB_KEY in sm:
                ub.setdefault(route, {})[t] = sm[UB_KEY]["pops"]
            if sm.get("zero_se_quantiles"):
                zse.setdefault(route, {})[t] = {"families": sm["zero_se_quantiles"],
                                                "rule": "judged by E-hat > delta, as for comparators; reported (Choice 47m13)"}
            if "descriptive_power" in sm:
                mpf.setdefault(route, {})[t] = sm["descriptive_power"]["pops"]
            for c, s_ in sorted((out.get("status") or {}).items()):
                if c not in R.REMOVAL_ARMS:
                    continue
                crit = s_.get("criteria") or {}
                cpf.setdefault(route, {}).setdefault(t, {})[c] = crit.get("families")
                zs = crit.get("zero_se") or {}
                if s_.get("zero_se_quantiles") or any(z["cells"] or z["family"] or z["pooled"] for z in zs.values()):
                    rem, rem_wo = removal_split(s_)
                    zeff.setdefault(route, {}).setdefault(t, {})[c] = {"zero_se_quantiles": s_.get("zero_se_quantiles"), "zero_se_flags": zs,
                                                                       "removed": rem, "removed_without_zero_se_flags": rem_wo,
                                                                       "changed_V_t": bool(rem and not rem_wo)}
            fb = out.get("form_b") or {}
            if "comparator_reasons" in fb:
                why.setdefault(route, {})[t] = {"V_t": fb.get("V"), "reasons": fb["comparator_reasons"],
                                                "in_V_hk1c_only": fb.get("in_V_hk1c_only")}
    dec["Mstar_simultaneous_upper_bounds"] = {"label": UB_LABEL, "by_route": ub}
    dec["V_t_reasons"] = {"rule": "a comparator leaves V_t only through a flagged cell, family cell or pooled cell (Choice 47e)", "by_route": why}
    dec["Mstar_zero_se_families"] = zse
    dec["Mstar_power_families"] = {"label": "descriptive (never gated): M*'s per-cell power at P 0.10, 0.12, 0.15, 0.20, MDE80, each "
                                            "family's share of the population's records, the floor at F_MIN 4, 6, 8", "by_route": mpf}
    dec["comparator_power_families"] = {"label": "descriptive: each comparator's power family (size, record share, floor at F_MIN 4, 6, 8)",
                                        "by_route": cpf}
    dec["zero_se_effects"] = {"label": "every comparator with a zero-SE (non-finite quantile) case, and whether it changed V_t (criteria item 7)",
                              "by_route": zeff}
    dec["criteria"] = {"source": "D16 v30 Choice 50 (ICH E9 5.5); register 90_DECISIONS/C1_CRITERIA_REGISTER_v02.md; c1_rules_v01", "constants": R.CONSTANTS,
                       "levels": R.levels(), "hk1c_level_status": "final: 0.995 (D16 v30 Choice 50(c); Loh 1987 calibration rule)"}
    h9 = dec.get("hypotheses", {}).get("H9") or {}
    for t, r in (h9.get("by_tracker") or {}).items():
        if isinstance(r, dict):
            known = r.get("family_size_E2") is not None and r.get("floor") is not None
            h9f[t] = {"family_size_E2": r.get("family_size_E2"), "floor": r.get("floor"),
                      "floor_met": bool(r["family_size_E2"] >= r["floor"]) if known else None}
    descriptive = str(h9.get("status")) == "descriptive" or str(h9.get("label", "")).startswith("descriptive")
    dec["H9_floor"] = {"rule": ("condition (a) of H9: >= 6 power-qualified E2 cells; reported (H9 is descriptive: D16 v33 Choice 52b)" if descriptive else
                                "condition (a) of H9: >= 6 power-qualified E2 cells; if it fails on a tracker, the predictor arm sets H9 "
                                "false there and H9's status is 'does not hold: floor not met' (D16 v26 Choice 47c, v28 49l)"), "by_tracker": h9f}
    if descriptive:
        dec["H9_descriptive"] = {"label": H9_DESCRIPTIVE_WORDING,
                                 "by_tracker": {t: {k: r.get(k) for k in ("cells", "cell_estimates", "cell_lb_0.95", "cell_ub_0.95", "exceed_share",
                                                                          "evaluable", "evaluable_E2", "family_size", "family_size_E2", "floor",
                                                                          "flagged", "family_flagged", "pooled_flagged")} | {"floor_met": h9f.get(t, {}).get("floor_met")}
                                                for t, r in (h9.get("by_tracker") or {}).items() if isinstance(r, dict)}}
    s_decision_forms(dec, results_all)
    fails = sorted(t for t, v in h9f.items() if v["floor_met"] is False)
    if fails and dec.get("claims_status", {}).get("H9") == "does not hold":
        dec["claims_status"]["H9"] = "does not hold: floor not met"
        h9["status"] = "does not hold: floor not met"
        h9["reasons"] = list(h9.get("reasons") or []) + [
            "floor not met (condition a: >= 6 power-qualified E2 cells): %s" % "; ".join(
                "%s family_size_E2 = %s < %s" % (t, h9f[t]["family_size_E2"], h9f[t]["floor"]) for t in fails)]
    return dec


H9_DESCRIPTIVE_WORDING = ("H9 is descriptive (D16 v33 Choice 52b): the decision reports, per tracker, the Trajectron++ PD cells' estimates "
                          "and simultaneous one-sided 95 % bounds, the power-qualified E2 family size, the floor (6) and whether it is met; "
                          "no confirmatory claim is made about a learned predictor")
S_SOURCES = {"H2": ("within_lt3d", "form_c"), "H3": ("within_lt3d", "H3"), "H4": ("transfer_lt3d", "form_b"), "H10": ("within_lt3d", "H10")}


def s_decision_forms(dec, results_all):
    """D16 v33 Choice 52(e): in family S the p-value governs (Holm); the status follows it; the bound at the level Holm assigned is
    reported beside it, and any disagreement is listed. H6b's method-stage record holds p-values only."""
    fs = dec.get("family_S") or {}
    out, dis = {}, []
    for c, v in fs.items():
        rec = {"p": v.get("p"), "holm_level": v.get("holm_level"), "rejected": v.get("rejected"), "confirmed": v.get("confirmed"),
               "status": v.get("status"), "status_bound_nominal": v.get("status_bound_nominal")}
        if c in S_SOURCES and v.get("holm_level") is not None:
            route, key = S_SOURCES[c]
            per = {}
            for t, o in sorted((results_all.get(route) or {}).items()):
                if t in TRACKERS and isinstance((o or {}).get(key), dict):
                    per[t] = ((o[key].get("holm_levels") or {}).get("%.6f" % v["holm_level"]))
            rec["bound_at_holm_level"] = per
            if per and all(x is not None for x in per.values()):
                bh = all(x["holds"] for x in per.values())
                rec["bound_holds"] = bh
                rec["agree"] = bool(bh == bool(v.get("rejected")))
                if not rec["agree"]:
                    dis.append(c)
        elif c == "H6b":
            rec["bound_at_holm_level"] = "not available: the method stage records p-values only (H6b_detail); the p-value decides"
        out[c] = rec
        if v.get("status_bound_nominal") is not None and c in dec.get("claims_status", {}):
            dec["claims_status"][c] = v["status"]
            hyp = dec.get("hypotheses", {}).get(c)
            if isinstance(hyp, dict):
                hyp["status_bound_nominal"] = v["status_bound_nominal"]
                hyp["status"] = v["status"]
    dec["S_decision_forms"] = {"rule": "family S: the p-value (share of bootstrap replicates on the null side) decides through Holm at "
                                       "0.025 (m = 5, gated on H1); the bound at the Holm-assigned level is reported beside it (D16 v33 "
                                       "Choice 52e); H1: the bound decides", "by_claim": out, "disagreements": dis}


Q1_LABEL = "Q1 (QCNet on the 150 validation logs, descriptive): not tested in C1 (D16 v23 Choice 44d, v24 Choice 45c)"
Q1_REASONS = ["no C1 tracker index shares QCNet's history source: QCNet's deployed histories are the 10 Hz matched AB3DMOT tracks with "
              "the SF threshold (30_DATA/qcnet_av2_v03), while C1's AB3DMOT index is the 2 Hz run of Choice 11 (Choice 43a, 44d)",
              "QCNet predicted 95.7 % of T1's 2 Hz records (88,182 of 92,166), so the frozen condition not_predicted == 0 cannot hold (Choice 44d)"]


def add_q1_not_tested(dec):
    """44(d): Q1 in its own block, "not tested" with the decided reasons; nothing else in the decision is read or changed."""
    dec["hypotheses"].pop("Q1", None)
    dec["hypotheses"]["Q1"] = {"label": Q1_LABEL, "status": "not tested", "reasons": list(Q1_REASONS), "decided": "before any outcome (Choice 44d)"}
    dec["claims_status"]["Q1"] = "not tested"
    dec["not_tested"] = sorted(set(dec["not_tested"]) | {"Q1"})
    return dec


def decide_all(results_all, cfg, mode, aux):
    assert "q1" not in cfg, "the config holds a q1 entry: Q1 is not tested in C1 (D16 v23 Choice 44d)"
    check_h9_label(cfg)
    R.config_check(cfg)
    return add_v09_blocks(add_q1_not_tested(A6.decide_all(results_all, cfg, mode, aux)), results_all)


def e0_check(cfg, mode, frozen=None):
    """c1_analyse_v07.e0_check on c1_guard_v05 (its c1_gt_<pid>_* temporary folder is never swept while this run lives)."""
    import copy
    tmp = None
    try:
        e = cfg.get("e0")
        if e and int(e.get("seed", -1)) != A6.E0.SEED:
            return {"present": True, "ok": False, "reason": "E0's seed must be %d (R17c m2), not %s" % (A6.E0.SEED, e.get("seed"))}
        if e and frozen is not None and not os.path.exists(e["inputs"]["gt"]):
            k = G.rel(e["inputs"]["gt"])
            want = (e.get("inputs_sha256") or {}).get(k)
            member = G.member_for(want) if want else None
            assert member, "the E0 ground truth is neither on disk nor in the quarantine"
            tmp = G.materialise_quarantined(member, want)
            cfg = copy.deepcopy(cfg)
            cfg["e0"]["inputs"]["gt"] = tmp
            cfg["e0"]["inputs_sha256"] = {(G.rel(tmp) if kk == k else kk): v for kk, v in cfg["e0"]["inputs_sha256"].items()}
        return A5.e0_check(cfg, mode, frozen)
    except Exception as ex:
        return {"present": bool(cfg.get("e0")), "ok": False, "reason": "exception: " + _exc(ex)}
    finally:
        G.cleanup(tmp)


def logged_check(paths, logged):
    """m1: every consumed file's SHA-256 must be an output of a "done" line of the run log."""
    out, missing = {}, []
    for p in paths:
        h = G.sha(p)
        hits = logged.get(h) or []
        if not hits:
            missing.append(G.rel(p))
        else:
            out[G.rel(p)] = {"sha256": h, "done_lines": [{"output": q, "entry": e, "run_id": r} for q, e, r in hits]}
    return out, missing


def table_paths(cfg, key):
    ent = cfg.get(key)
    if not ent:
        return []
    if isinstance(ent, dict) and "path" not in ent:
        return [e if isinstance(e, str) else e["path"] for e in ent.values()]
    return [ent if isinstance(ent, str) else ent["path"]]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--csv-dir", default=None)
    g_ = ap.add_mutually_exclusive_group(required=True)
    for m_ in ("c1", "standin", "reproduce", "smoke"):
        g_.add_argument("--" + m_, action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None, help="a rehearsal's own log: nuScenes units only")
    ap.add_argument("--boot", type=int, default=R.B_BOOT)
    a = ap.parse_args(argv)
    mode = "c1" if a.c1 else "standin" if a.standin else "reproduce" if a.reproduce else "smoke"
    assert mode == "smoke" or a.boot == R.B_BOOT, "B = %d is fixed outside --smoke (D16 v33 Choice 52d)" % R.B_BOOT
    configure_v09(mode)
    B.K8_SEEDS = mode == "reproduce"
    t0 = time.time()
    cfg = json.load(open(a.config))
    assert "q1" not in cfg, "the config holds a q1 entry: Q1 is not tested in C1 (D16 v23 Choice 44d)"
    check_h9_label(cfg)
    R.config_check(cfg)
    R.check_h9_label_c1(cfg, mode)
    fj = json.load(open(cfg["folds"])) if cfg.get("folds") else None
    ds_units = G.folds_dataset(fj) if fj else "unknown"
    side = frozen = rt = None
    deposit = None
    if mode == "c1":
        assert a.plan, "--c1 needs --plan"
        G.refuse_existing([a.out, a.decision], ds_units)
        side, frozen, rt = G.guard(ds_units, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        deposit = rt["deposit_record_sha256"]
        G.require_bound(frozen, a.config, "config")
        folds_sha = G.require_bound(frozen, cfg["folds"], "folds")
        assert "c" in cfg, "--c1: c must be stated in the frozen config (R16 m1, R17 m9)"
    else:
        assert a.plan is None and a.hash_log is None, "--%s runs without a plan or a hash log" % mode
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha = G.sha(cfg["folds"]) if cfg.get("folds") else None
    av2_logged = mode == "c1" and ds_units not in G.EXEMPT_DS
    logged, run_log_rec = ({}, {"run_log": "not used (%s)" % ds_units})
    if av2_logged:
        logged, run_log_rec = G.logged_outputs()
    units = sorted(fj["fold_of_log"]) if fj else None
    h8_role = cfg.get("h8_units", "folds")
    h8_units = units
    if mode == "c1" and h8_role != "folds":
        hp, _ = G.role_hash(frozen, h8_role)
        h8_units = sorted(json.load(open(os.path.join(G.W, hp)))["fold_of_log"])
    binding = {"mode": mode, "config_sha256": G.sha(a.config), "plan_sha256": side, "entry_point": rt["entry_point"],
               "code_sha256": rt["code_sha256"], "folds_sha256": folds_sha, "versions": rt.get("versions"),
               "hash_log": G.rel(a.hash_log) if a.hash_log else "canonical", "hash_log_sha256": rt.get("hash_log_sha256"),
               "deposit_record_sha256": deposit, "h8_units_role": h8_role, "run_log_at_start": run_log_rec, "run_id": rt.get("run_id")}
    logged_tables = {}

    def gate_logged(key, tab):
        if not av2_logged or not tab or not tab.get("ok"):
            return tab
        ok_paths, missing = logged_check(table_paths(cfg, key), logged)
        logged_tables[key] = ok_paths
        if missing:
            return {"ok": False, "why": "%s: no 'done' line in the run log for %s (Choice 44f m1)" % (key, missing)}
        return tab
    tabs = {}
    for k, r in TABLE_ROLES.items():
        u = h8_units if k == "h8" else units
        tabs[k] = gate_logged(k, A7.load_table(k, r, cfg, mode, side, frozen, folds_sha, TRACKERS, u, ds_units, deposit))
    aux = {"route_problems": {}, "tables": tabs,
           "tables_descriptive": {k: gate_logged(k, A7.load_table(k, r, cfg, mode, side, frozen, folds_sha, DESCRIPTIVE_TRACKERS, units, ds_units, deposit))
                                  for k, r in DESC_TABLES.items() if cfg.get(k)}}
    aux["e0"] = e0_check(cfg, mode, frozen)
    print("E0 check:", json.dumps({k: v for k, v in aux["e0"].items() if k != "recomputed"}, default=float), flush=True)
    log_of_scene = {}
    for p in cfg.get("manifests", []):
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    source_of_log = fj["source_of_log"] if fj else {}
    results, k8res, route_checks = {}, {}, {}
    csv_dir = a.csv_dir or os.path.dirname(os.path.abspath(a.out))
    os.makedirs(csv_dir, exist_ok=True)
    for r in cfg["routes"]:
        for i, t in enumerate(TRACKERS + DESCRIPTIVE_TRACKERS):
            if t not in r["tags"]:
                continue
            try:
                runs, tag = r["runs"], r["tags"][t]
                rp = os.path.join(runs, "run_record_%s_decide.json" % tag)
                assert os.path.exists(rp), "no run record " + rp
                rr = json.load(open(rp))
                caches = rr.get("caches") or []
                dsets = [G.manifest_dataset(json.load(open(os.path.join(c, "MANIFEST.json")))) for c in caches]
                if mode == "c1":
                    if a.hash_log:
                        assert caches and all(d_ == "nuscenes" for d_ in dsets), "GUARD: a rehearsal hash log with caches that are not nuScenes"
                    route_checks.setdefault(r["name"], {})[t] = A7.check_route_c1(rr, r, t, side, frozen, ds_units, deposit)
                    if av2_logged:
                        okp, missing = logged_check([rp], logged)
                        assert not missing, "run record %s has no 'done' line in the run log (Choice 44f m1)" % missing
                        route_checks[r["name"]][t]["run_log"] = okp
                else:
                    assert not (rr.get("c1") and not rr.get("standin")), "GUARD: --%s refuses C1 confirmatory run records (R17 M2)" % mode
                    assert caches, "GUARD: --%s refuses a run record without caches (R17b A3)" % mode
                    assert all(d_ == "nuscenes" for d_ in dsets), "GUARD: --%s refuses runs on caches that are not nuScenes: %s" % (mode, dsets)
                    if mode == "standin":
                        assert rr.get("c1") is True and rr.get("standin") is True, "run %s is not a stand-in run" % tag
                l_of = log_of_scene
                if cfg.get("units_are_logs"):
                    l_of = {o["scene"]: o["scene"] for o in (json.loads(l) for l in open(os.path.join(runs, "episodes_%s_decide.jsonl" % tag)))}
                cc = cfg["c"] if mode == "c1" else cfg.get("c", B.C_DEFAULT)
                c_t = float(cc.get(t, cc[TRACKERS[0]]))
                out, res_small, res = B.analyse_route_tracker(r["name"], i, tag, runs, (r.get("fits") or {}).get(t), l_of, source_of_log, c_t,
                                                              a.boot, r.get("retuned_arm"))
                K.csv_tables_decide(res, "%s_%s" % (r["name"], t), csv_dir)
                results.setdefault(r["name"], {})[t] = out
                k8res.setdefault(r["name"], {})[t] = K.strip_csv_payload(res_small)
                del res
                print("%s %s: done %.0f s" % (r["name"], t, time.time() - t0), flush=True)
            except Exception as ex:
                if str(ex).startswith("GUARD:"):
                    raise
                aux["route_problems"].setdefault(r["name"], {})[t] = "not provenance-valid or failed: " + _exc(ex)
                print("%s %s: %s" % (r["name"], t, aux["route_problems"][r["name"]][t][:200]), flush=True)
    dec = decide_all(results, cfg, mode, aux)
    if mode == "c1":
        rt = G.verify_runtime_again(frozen, rt)
        binding["code_sha256"] = rt["code_sha256"]
    binding["tables_in_run_log"] = logged_tables if av2_logged else "not used (%s)" % ds_units
    dec["binding"] = binding
    dec["route_checks"] = route_checks
    dec["route_problems"] = aux["route_problems"]
    dec["tables"] = {k: ({"ok": v["ok"], "why": v.get("why"), "checks": v.get("checks")} if v else None) for k, v in aux["tables"].items()}
    for path, obj in ((a.out, {"stamp": B.STAMPS[mode], "binding": binding, "c1": results, "k8": k8res}), (a.decision, dec)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        tmp = path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(obj, f, indent=1, default=float)
        os.replace(tmp, path)
    if mode == "c1":
        G.run_log_append(ds_units, os.path.abspath(__file__), side, deposit, {"config": binding["config_sha256"]}, [a.out, a.decision])
    print(json.dumps({"C1_verdict": dec["C1_verdict"], "gate_H1": dec["gate_H1"], "nogo_reasons": dec["nogo_reasons"][:8],
                      "not_tested": dec["not_tested"], "claims": dec["claims_status"]}, default=str))
    print(B.STAMPS[mode])
    print("C1 ANALYSIS V09 DONE")


if __name__ == "__main__":
    main()
