#!/usr/bin/env python3
"""X3 analysis (c1), interval sensitivity (x3-stats, v01, 7 Nov 2026). Plan 2(c1); referee concern M4.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

For T1 and T3 on the within_lt3d route, every quantity that decided H1 is recomputed by three interval methods:
  (i)   the record's log-cluster bootstrap bound: sup-t on the bootstrap SE (k6_analyse_v02.flag / m_lib_v04._simul, as re-derived
        by R21); for one cell this is the basic (reverse-percentile) bootstrap bound 2E - Q_{1-L}(E*). Computed (a) on the record's
        own weights (seed [20261110, i, 0], B = 40000) as the reproduction check, and (b) on X3's weights ([20261201, i, 3], B = 4000);
  (ii)  the studentised log bootstrap: pivots (E* - E) / SE*, SE the cluster delta-method SE of the estimator floored at
        sqrt(delta (1 - delta) / N_eff), recomputed on every replicate; simultaneous by sup-t over the same cell sets as the record.
        Primary on X3's weights (B = 4000); also on the record's weights (B = 40000) as a Monte Carlo sensitivity;
  (iii) the design-effect Wilson interval: n_eff = N / deff, deff = 1 + (m_bar - 1) rho_hat, rho_hat the ANOVA ICC across logs;
        Bonferroni over the cells where the record uses sup-t. Centre = the record's estimate (mean of per-log rates); the variant
        centred on the record-pooled proportion x / n is reported alongside.
Families (power-qualified cells) and evaluable sets are the record's (validity_by_arm), never recomputed. The status rules are the
code of record's (c1_analyse_v02.arm_status: ShownAbove = cell flag, family flag, pooled flag or HK1c failure; Valid = NoFlag,
no FamFlag, NoFlag_pool, Floor, HK1c on every population). Where V_t changes, Form B is recomputed by the record's paired percentile
bootstrap on the record's weights.
Run (heavy: B = 40000 on 375 logs, inside the X3 heavy lock):
  python -B x3_stats_c1_v01.py --out-dir <60_RESULTS/x3_explore_v01/c_intervals>
"""
import argparse
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_stats_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

L = C.L
METHODS = ("i_rec", "i_x3", "ii_x3", "ii_rec", "iii", "iii_pooledcentre")
METHOD_LABEL = {
    "i_rec": "(i) record's bootstrap bound, record weights B=40000 (reproduction)",
    "i_x3": "(i) record's bootstrap bound, X3 weights B=4000",
    "ii_x3": "(ii) studentised log bootstrap with SE floor, X3 weights B=4000 (primary (ii))",
    "ii_rec": "(ii) studentised log bootstrap with SE floor, record weights B=40000 (MC sensitivity)",
    "iii": "(iii) design-effect Wilson, Bonferroni, centre = record's estimate (primary (iii))",
    "iii_pooledcentre": "(iii') design-effect Wilson, Bonferroni, centre = record-pooled x/n (variant)"}
PRIMARY = ("i_rec", "ii_x3", "iii")


def lst(a):
    return [C.fnum(x) for x in np.asarray(a, float).tolist()]


def method_pop(method, N, X, ev, fam, level, is_m, W, stud_cache):
    """One arm and population under one method: cell LBs over the evaluable set, family LBs, pooled LB at level, pooled UB at
    0.995 (HK1c), and for M* the simultaneous 0.95 UBs over the evaluable set."""
    Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
    est = L.point_rates(N, X)
    pe = L.point_rates(Np, Xp)
    out = {"E": {CELLNAMES[j]: C.fnum(est[j]) for j in ev}, "pooled_E": C.fnum(pe[0])}
    if method.startswith("i_"):
        boot = W.rates(N, X) if len(ev) else None
        pb = W.rates(Np, Xp)
        if len(ev):
            r = L.flag_cells(est, boot, ev, level)
            out["cell_lb"] = dict(zip([CELLNAMES[j] for j in ev], lst(r["bound"])))
            out["cell_lb_mcse"] = dict(zip([CELLNAMES[j] for j in ev], lst(r["bound_mcse"])))
            out["cell_flag"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(r["flag"])]
            out["q_cells"] = C.fnum(r["q"])
        if len(fam):
            rf = L.flag_cells(est, boot, fam, level)
            out["fam_lb"] = dict(zip([CELLNAMES[j] for j in fam], lst(rf["bound"])))
            out["fam_lb_mcse"] = dict(zip([CELLNAMES[j] for j in fam], lst(rf["bound_mcse"])))
            out["fam_flag"] = [CELLNAMES[fam[i]] for i in np.flatnonzero(rf["flag"])]
            out["q_family"] = C.fnum(rf["q"])
        lo = L.flag_cells(pe, pb, [0], level)
        up = L.supt(pe, pb, [0], C.L_HK1C, "upper")
        out.update({"pooled_lb": C.fnum(lo["bound"][0]), "pooled_lb_mcse": C.fnum(lo["bound_mcse"][0]),
                    "pooled_flag": bool(lo["flag"][0]), "pooled_q": C.fnum(lo["q"]),
                    "hk1c_ub": C.fnum(up["bound"][0]), "hk1c_ub_mcse": C.fnum(up["bound_mcse"][0]),
                    "hk1c_ub_pure_percentile": C.fnum(np.nanquantile(pb[:, 0], C.L_HK1C))})
        if is_m and len(ev):
            u = L.supt(est, boot, ev, C.LEVEL_M, "upper")
            out["sim_ub"] = dict(zip([CELLNAMES[j] for j in ev], lst(u["bound"])))
            out["sim_ub_mcse"] = dict(zip([CELLNAMES[j] for j in ev], lst(u["bound_mcse"])))
        return out
    if method.startswith("ii_"):
        S, Sp = C.Stud(N, X, W), C.Stud(Np, Xp, W)
        out["se_floor_binds"] = {CELLNAMES[j]: bool(S.floor[j] > S.se_d[j]) for j in ev}
        out["cell_se_delta"] = {CELLNAMES[j]: C.fnum(S.se_d[j]) for j in ev}
        out["cell_se_floor"] = {CELLNAMES[j]: C.fnum(S.floor[j]) for j in ev}
        if len(ev):
            b, q, m = S.bounds(ev, level, "lower")
            out["cell_lb"] = dict(zip([CELLNAMES[j] for j in ev], lst(b)))
            out["cell_lb_mcse"] = dict(zip([CELLNAMES[j] for j in ev], lst(m)))
            out["cell_flag"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(b > C.DELTA)]
            out["q_cells"] = C.fnum(q)
        if len(fam):
            b, q, m = S.bounds(fam, level, "lower")
            out["fam_lb"] = dict(zip([CELLNAMES[j] for j in fam], lst(b)))
            out["fam_lb_mcse"] = dict(zip([CELLNAMES[j] for j in fam], lst(m)))
            out["fam_flag"] = [CELLNAMES[fam[i]] for i in np.flatnonzero(b > C.DELTA)]
            out["q_family"] = C.fnum(q)
        b, q, m = Sp.bounds([0], level, "lower")
        bu, qu, mu = Sp.bounds([0], C.L_HK1C, "upper")
        out.update({"pooled_lb": C.fnum(b[0]), "pooled_lb_mcse": C.fnum(m[0]), "pooled_flag": bool(b[0] > C.DELTA),
                    "pooled_q": C.fnum(q), "hk1c_ub": C.fnum(bu[0]), "hk1c_ub_mcse": C.fnum(mu[0]),
                    "pooled_se_delta": C.fnum(Sp.se_d[0]), "pooled_se_floor": C.fnum(Sp.floor[0])})
        if is_m and len(ev):
            b, q, m = S.bounds(ev, C.LEVEL_M, "upper")
            out["sim_ub"] = dict(zip([CELLNAMES[j] for j in ev], lst(b)))
            out["sim_ub_mcse"] = dict(zip([CELLNAMES[j] for j in ev], lst(m)))
        return out
    # (iii)
    dt = C.deff_table(N, X)
    dtp = C.deff_table(Np, Xp)
    centre = None
    centre_p = None
    if method == "iii_pooledcentre":
        with np.errstate(invalid="ignore", divide="ignore"):
            centre = np.where(dt["n"] > 0, dt["x"] / dt["n"], np.nan)
            centre_p = np.where(dtp["n"] > 0, dtp["x"] / dtp["n"], np.nan)
    out["deff"] = {CELLNAMES[j]: {"rho": C.fnum(dt["rho"][j]), "m_bar": C.fnum(dt["mbar"][j]), "deff": C.fnum(dt["deff"][j]),
                                  "n_eff": C.fnum(dt["neff"][j]), "N": C.fnum(dt["n"][j]), "logs": int(dt["k"][j])} for j in ev}
    out["pooled_deff"] = {"rho": C.fnum(dtp["rho"][0]), "m_bar": C.fnum(dtp["mbar"][0]), "deff": C.fnum(dtp["deff"][0]),
                          "n_eff": C.fnum(dtp["neff"][0]), "N": C.fnum(dtp["n"][0]), "logs": int(dtp["k"][0])}
    if len(ev):
        b, z = C.wilson_family(est, dt, ev, level, "lower", centre)
        out["cell_lb"] = dict(zip([CELLNAMES[j] for j in ev], lst(b)))
        out["cell_flag"] = [CELLNAMES[ev[i]] for i in np.flatnonzero(b > C.DELTA)]
        out["z_cells"] = z
    if len(fam):
        b, z = C.wilson_family(est, dt, fam, level, "lower", centre)
        out["fam_lb"] = dict(zip([CELLNAMES[j] for j in fam], lst(b)))
        out["fam_flag"] = [CELLNAMES[fam[i]] for i in np.flatnonzero(b > C.DELTA)]
        out["z_family"] = z
    b, z = C.wilson_family(pe, dtp, [0], level, "lower", centre_p)
    bu, zu = C.wilson_family(pe, dtp, [0], C.L_HK1C, "upper", centre_p)
    out.update({"pooled_lb": C.fnum(b[0]), "pooled_flag": bool(b[0] > C.DELTA), "hk1c_ub": C.fnum(bu[0]), "z_pooled": z,
                "z_hk1c": zu})
    if is_m and len(ev):
        b, z = C.wilson_family(est, dt, ev, C.LEVEL_M, "upper", centre)
        out["sim_ub"] = dict(zip([CELLNAMES[j] for j in ev], lst(b)))
        out["z_sim_ub"] = z
    return out


CELLNAMES = C.CELLNAMES


def pop_status(r, pop, family_size, n_ev):
    """c1_analyse_v02.arm_status's per-population terms from one method's bounds."""
    nf = not r.get("cell_flag")
    ff = bool(r.get("fam_flag"))
    nfp = not r["pooled_flag"]
    hk = r["hk1c_ub"] is not None and r["hk1c_ub"] <= C.DELTA + C.HK1C_MARGIN
    floor = (family_size >= L.F_MIN) if pop != "PD_inpath" else (n_ev >= L.PD_MIN_EVALUABLE)
    return {"NoFlag": nf, "FamFlag": ff, "NoFlag_pool": nfp, "HK1c": bool(hk), "Floor": bool(floor),
            "valid": bool(nf and not ff and nfp and floor and hk),
            "shown_above_code_of_record": bool((not nf) or ff or (not nfp) or (not hk)),
            "shown_above_9_conditions": bool((not nf) or ff or (not nfp))}


def arm_status(per):
    valid = all(v["valid"] for v in per.values())
    sa = any(v["shown_above_code_of_record"] for v in per.values())
    s9 = any(v["shown_above_9_conditions"] for v in per.values())
    return {"valid": valid, "shown_above": sa, "shown_above_9_conditions": s9, "floor_only": bool((not valid) and (not sa))}


def run_tracker(t, ext, log):
    i = C.TRACKER_I[t]
    rec = ext["trackers"][t]
    t0 = time.time()
    data = C.load_data(t)
    log("loaded %s: U %d arms %d (%.0f s)" % (t, data.U, len(data.arms), time.time() - t0))
    out = {"units": data.U, "input_sha256": data.input_sha256, "run_table_hash_checks": data.hash_checks}
    # RETUNED composite: R21's selection against the record's
    aos = rec["retune_arm_of_scene"] or {}
    mism = [u for k, u in enumerate(data.units) if aos.get(u) != data.retuned["arm_of_unit"][k]]
    out["check_retuned_arm_of_unit_equals_record"] = {"mismatches": len(mism), "examples": mism[:5],
                                                       "arm_of_fold_r21": data.retuned["arm_of_fold"],
                                                       "arm_of_fold_record": rec["retune_arm_of_fold"]}
    Wrec = L.Weights([C.SEED_REC_BOOT, i, 0], data.U, C.B_REC)
    Wx = L.Weights([C.SEED_X3_BOOT, i, C.J_C], data.U, C.B_X3)
    log("weights ready %s" % t)
    Ws = {"i_rec": Wrec, "i_x3": Wx, "ii_x3": Wx, "ii_rec": Wrec, "iii": None, "iii_pooledcentre": None}
    arms_out = {}
    status = {m: {} for m in METHODS}
    checks = []
    for arm in ["Mstar"] + list(C.COMPS):
        is_m = arm == "Mstar"
        level = C.LEVEL_M if is_m else C.LEVEL_RM
        arms_out[arm] = {}
        per = {m: {} for m in METHODS}
        stud_cache = {}
        for pop in C.POPS:
            N, X = data.table(arm, pop)
            ev = np.flatnonzero(L.evaluable(N))
            fam_names = rec["families"][arm][pop]
            fam = C.cells_idx(fam_names)
            res = {"evaluable": [CELLNAMES[j] for j in ev], "family": fam_names, "records": float(N.sum()),
                   "logs_with_records": int((N.sum(1) > 0).sum())}
            for m in METHODS:
                res[m] = method_pop(m, N, X, ev, fam, level, is_m, Ws[m], stud_cache)
                per[m][pop] = pop_status(res[m], pop, len(fam), len(ev))
                res[m]["status"] = per[m][pop]
            # reproduction check of (i) on the record's weights against the record's validity entry
            v = rec["validity"][arm]["pops"][pop]
            r0 = res["i_rec"]
            pooled = v.get("pooled") or {}
            pairs = [("q_cells", r0.get("q_cells"), v.get("q")), ("q_family", r0.get("q_family"), v.get("family_q")),
                     ("pooled_lb", r0["pooled_lb"], pooled.get("lb")), ("hk1c_ub", r0["hk1c_ub"], pooled.get("ub")),
                     ("pooled_E", r0["pooled_E"], pooled.get("E")),
                     ("max_cell_lb", max(r0.get("cell_lb", {}).values()) if r0.get("cell_lb") else None, v.get("max_lb"))]
            if is_m and rec.get("Mstar_desc_ub"):
                du = (rec["Mstar_desc_ub"].get(pop) or {}).get("cells") or {}
                for c, val in du.items():
                    pairs.append(("sim_ub " + c, (r0.get("sim_ub") or {}).get(c), val))
            for name, a, b in pairs:
                if a is None and b is None:
                    continue
                d = None if (a is None or b is None) else abs(float(a) - float(b))
                checks.append({"arm": arm, "pop": pop, "quantity": name, "x3": a, "record": b, "abs_diff": d})
            checks.append({"arm": arm, "pop": pop, "quantity": "flagged cells (list)", "x3": sorted(r0.get("cell_flag", [])),
                           "record": sorted(v.get("flagged") or []),
                           "abs_diff": 0.0 if sorted(r0.get("cell_flag", [])) == sorted(v.get("flagged") or []) else 1.0})
            checks.append({"arm": arm, "pop": pop, "quantity": "family flagged (list)", "x3": sorted(r0.get("fam_flag", [])),
                           "record": sorted(v.get("family_flagged") or []),
                           "abs_diff": 0.0 if sorted(r0.get("fam_flag", [])) == sorted(v.get("family_flagged") or []) else 1.0})
            arms_out[arm][pop] = res
        for m in METHODS:
            status[m][arm] = dict(arm_status(per[m]), pops=per[m])
        rs = rec["status"][arm]
        checks.append({"arm": arm, "pop": "all", "quantity": "valid / shown_above (record status)",
                       "x3": [status["i_rec"][arm]["valid"], status["i_rec"][arm]["shown_above"]],
                       "record": [rs["valid"], rs["shown_above"]],
                       "abs_diff": 0.0 if [status["i_rec"][arm]["valid"], status["i_rec"][arm]["shown_above"]] == [rs["valid"], rs["shown_above"]] else 1.0})
        log("%s %s done (%.0f s)" % (t, arm, time.time() - t0))
        C.live("(c1) intervals %s, arm %s" % (t, arm), (["Mstar"] + list(C.COMPS)).index(arm) + 1, 8, "tracker %s of t1,t3" % t)
    # V_t, H1 per method
    rate_m = data.inf("Mstar")
    h1 = {}
    for m in METHODS:
        V = [c for c in C.COMPS if not status[m][c]["shown_above"]]
        V9 = [c for c in C.COMPS if not status[m][c]["shown_above_9_conditions"]]
        rates = {c: data.inf(c) for c in set(V) | set(V9)}
        fb = L.form_b(Wrec, rate_m, rates, V)
        fb9 = L.form_b(Wrec, rate_m, rates, V9)
        h1[m] = {"valid_Mstar": status[m]["Mstar"]["valid"], "V_t": V, "form_b": fb,
                 "H1": bool(status[m]["Mstar"]["valid"] and fb["all_lower"]),
                 "V_t_9_conditions": V9, "form_b_9_conditions": fb9,
                 "H1_9_conditions": bool(status[m]["Mstar"]["valid"] and fb9["all_lower"])}
    rec_fb = rec["form_b"]
    out.update({"arms": arms_out, "status": status, "H1": h1, "record_V_t": rec_fb["V"],
                "record_removed": rec_fb["removed_shown_above"], "record_comparator_reasons": rec_fb["comparator_reasons"],
                "reproduction_checks": checks,
                "reproduction_max_abs_diff_numeric": max([c["abs_diff"] for c in checks if c["abs_diff"] is not None
                                                          and c["quantity"] not in ("flagged cells (list)", "family flagged (list)",
                                                                                    "valid / shown_above (record status)")] or [0.0]),
                "reproduction_list_mismatches": sum(1 for c in checks if c["quantity"] in (
                    "flagged cells (list)", "family flagged (list)", "valid / shown_above (record status)") and c["abs_diff"] != 0.0),
                "seconds": time.time() - t0})
    del Wrec, Wx, data
    return out


def summarise(res):
    """The headline tables: M*'s HK1c UBs, M*'s largest simultaneous UBs, every r1 removal condition's LB, status changes."""
    S = {"hk1c": [], "max_sim_ub": [], "removal_conditions": [], "status_changes": [], "Mstar_cell_flags": []}
    for t, r in res.items():
        for pop in C.POPS:
            m = r["arms"]["Mstar"][pop]
            row = {"tracker": t, "pop": pop}
            for meth in METHODS:
                row[meth] = m[meth]["hk1c_ub"]
                row[meth + "_pass"] = m[meth]["status"]["HK1c"]
            S["hk1c"].append(row)
            row = {"tracker": t, "pop": pop}
            for meth in METHODS:
                su = m[meth].get("sim_ub") or {}
                if su:
                    c = max(su, key=lambda k: su[k])
                    row[meth] = su[c]
                    row[meth + "_cell"] = c
            S["max_sim_ub"].append(row)
            for meth in METHODS:
                for c in (m[meth].get("cell_flag") or []) + ["family:" + c for c in (m[meth].get("fam_flag") or [])] + (
                        ["pooled"] if m[meth]["pooled_flag"] else []):
                    S["Mstar_cell_flags"].append({"tracker": t, "pop": pop, "method": meth, "flag": c})
        # every r1 removal condition: the cells / family cells / pooled flagged under (i) on the record's weights
        for arm in C.COMPS:
            for pop in C.POPS:
                a = r["arms"][arm][pop]
                conds = [("cell", c) for c in a["i_rec"].get("cell_flag", [])] + [("family", c) for c in a["i_rec"].get("fam_flag", [])]
                if a["i_rec"]["pooled_flag"]:
                    conds.append(("pooled", "pooled"))
                if not a["i_rec"]["status"]["HK1c"]:
                    conds.append(("hk1c", "pooled UB"))
                for kind, c in conds:
                    row = {"tracker": t, "arm": arm, "pop": pop, "set": kind, "cell": c}
                    for meth in METHODS:
                        mm = a[meth]
                        if kind == "cell":
                            v = (mm.get("cell_lb") or {}).get(c)
                            fl = c in (mm.get("cell_flag") or [])
                        elif kind == "family":
                            v = (mm.get("fam_lb") or {}).get(c)
                            fl = c in (mm.get("fam_flag") or [])
                        elif kind == "pooled":
                            v, fl = mm["pooled_lb"], mm["pooled_flag"]
                        else:
                            v, fl = mm["hk1c_ub"], not mm["status"]["HK1c"]
                        row[meth] = v
                        row[meth + "_flag"] = bool(fl)
                    S["removal_conditions"].append(row)
        # status changes against (i) on the record's weights
        for meth in METHODS:
            if meth == "i_rec":
                continue
            for arm in ["Mstar"] + list(C.COMPS):
                a0, a1 = r["status"]["i_rec"][arm], r["status"][meth][arm]
                for key in ("valid", "shown_above", "shown_above_9_conditions"):
                    if a0[key] != a1[key]:
                        S["status_changes"].append({"tracker": t, "method": meth, "arm": arm, "what": key, "record": a0[key],
                                                    "method_value": a1[key]})
                for pop in C.POPS:
                    p0, p1 = a0["pops"][pop], a1["pops"][pop]
                    for key in ("NoFlag", "FamFlag", "NoFlag_pool", "HK1c"):
                        if p0[key] != p1[key]:
                            S["status_changes"].append({"tracker": t, "method": meth, "arm": arm, "pop": pop, "what": key,
                                                        "record": p0[key], "method_value": p1[key]})
                    # new or lost flagged cells
                    c0 = set(r["arms"][arm][pop]["i_rec"].get("cell_flag", []))
                    c1 = set(r["arms"][arm][pop][meth].get("cell_flag", []))
                    f0 = set(r["arms"][arm][pop]["i_rec"].get("fam_flag", []))
                    f1 = set(r["arms"][arm][pop][meth].get("fam_flag", []))
                    if c0 != c1 or f0 != f1:
                        S["status_changes"].append({"tracker": t, "method": meth, "arm": arm, "pop": pop, "what": "flagged cell set",
                                                    "lost_cells": sorted(c0 - c1), "new_cells": sorted(c1 - c0),
                                                    "lost_family": sorted(f0 - f1), "new_family": sorted(f1 - f0)})
            h0, h1 = r["H1"]["i_rec"], r["H1"][meth]
            if h0["V_t"] != h1["V_t"] or h0["H1"] != h1["H1"]:
                S["status_changes"].append({"tracker": t, "method": meth, "arm": "-", "what": "V_t / H1", "record": [h0["V_t"], h0["H1"]],
                                            "method_value": [h1["V_t"], h1["H1"]],
                                            "form_b_ub": {c: v["ub"] for c, v in h1["form_b"]["vs"].items()}})
    return S


def write_md(path, out):
    S = out["summary"]
    f6 = lambda v: "-" if v is None else ("%.4f" % v)  # noqa: E731
    lines = ["# X3 (c1): interval sensitivity of the quantities that decided H1 (v01)", "", "**%s**" % C.STAMP, "",
             "Plan `20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md` section 2(c1) (sha256 %s...); referee concern M4. Route within_lt3d, "
             "decision mode, T1 and T3. JSON: `%s`." % (C.PLAN_SHA[:8], os.path.basename(out["json_name"])), "",
             "## Methods", ""]
    for m in METHODS:
        lines.append("- **%s**: %s" % (m, METHOD_LABEL[m]))
    lines += ["", "Families and evaluable sets are the record's. Thresholds: a flag is LB > 0.05; HK1c passes at UB <= 0.08. M* is judged "
              "at one-sided 0.95; a comparator's removal conditions at 1 - 0.0125/9 = 0.998611. The record's (i) is the sup-t bound on "
              "the bootstrap SE (for one cell, the basic bootstrap bound); the pure percentile UB of HK1c is in the JSON "
              "(`hk1c_ub_pure_percentile`).", "",
              "## Reproduction of the record by (i) on the record's weights", ""]
    for t, r in out["trackers"].items():
        lines.append("- %s: largest absolute difference over %d numeric checks = %.2e; list / status mismatches = %d; RETUNED composite "
                     "mismatches against the record = %d." % (t, sum(1 for c in r["reproduction_checks"] if c["quantity"] not in (
                         "flagged cells (list)", "family flagged (list)", "valid / shown_above (record status)")),
                         r["reproduction_max_abs_diff_numeric"], r["reproduction_list_mismatches"],
                         r["check_retuned_arm_of_unit_equals_record"]["mismatches"]))
    lines += ["", "## M*'s pooled HK1c upper bound at 0.995 (passes at <= 0.08)", "",
              "| Tracker | Population | " + " | ".join(METHODS) + " |", "|---|---|" + "---|" * len(METHODS)]
    for row in S["hk1c"]:
        lines.append("| %s | %s | %s |" % (row["tracker"], row["pop"], " | ".join(
            "%s%s" % (f6(row[m]), "" if row[m + "_pass"] else " FAIL") for m in METHODS)))
    lines += ["", "## M*'s largest simultaneous 0.95 upper bound per population (descriptive, never gated)", "",
              "| Tracker | Population | " + " | ".join(METHODS) + " |", "|---|---|" + "---|" * len(METHODS)]
    for row in S["max_sim_ub"]:
        lines.append("| %s | %s | %s |" % (row["tracker"], row["pop"], " | ".join(
            "%s (%s)" % (f6(row.get(m)), row.get(m + "_cell", "-")) for m in METHODS)))
    lines += ["", "## M*'s flags under each method (any entry here is a status change for M*)", ""]
    if S["Mstar_cell_flags"]:
        lines += ["| Tracker | Population | Method | Flag |", "|---|---|---|---|"]
        for row in S["Mstar_cell_flags"]:
            lines.append("| %s | %s | %s | %s |" % (row["tracker"], row["pop"], row["method"], row["flag"]))
    else:
        lines.append("None: no cell, family cell or pooled cell of M* is flagged under any method.")
    lines += ["", "## Every r1 removal condition of a comparator: its bound under each method", "",
              "Lower bounds at 0.998611 (flag when > 0.05; '*' marks a flag); for an HK1c row the pooled upper bound (fails when > 0.08).", "",
              "| Tracker | Arm | Population | Set | Cell | " + " | ".join(METHODS) + " |", "|---|---|---|---|---|" + "---|" * len(METHODS)]
    for row in S["removal_conditions"]:
        lines.append("| %s | %s | %s | %s | %s | %s |" % (row["tracker"], row["arm"], row["pop"], row["set"], row["cell"], " | ".join(
            "%s%s" % (f6(row[m]), "*" if row[m + "_flag"] else "") for m in METHODS)))
    lines += ["", "## Status, V_t and H1 per method", "", "| Tracker | Method | Valid(M*) | V_t | removed | H1 |", "|---|---|---|---|---|---|"]
    for t, r in out["trackers"].items():
        for m in METHODS:
            h = r["H1"][m]
            rem = [c for c in C.COMPS if c not in h["V_t"]]
            lines.append("| %s | %s | %s | %s | %s | %s |" % (t, m, h["valid_Mstar"], ", ".join(h["V_t"]) or "-", ", ".join(rem), h["H1"]))
    lines += ["", "## Status changes against the record ((i), record weights)", ""]
    if S["status_changes"]:
        lines += ["| Tracker | Method | Arm | Population | What | Record | Method | Detail |", "|---|---|---|---|---|---|---|---|"]
        for row in S["status_changes"]:
            det = ""
            if row["what"] == "flagged cell set":
                det = "lost %s; new %s; lost family %s; new family %s" % (row["lost_cells"], row["new_cells"], row["lost_family"], row["new_family"])
            elif row["what"] == "V_t / H1":
                det = "Form B UB %s" % {k: round(v, 4) for k, v in row["form_b_ub"].items()}
            lines.append("| %s | %s | %s | %s | %s | %s | %s | %s |" % (row["tracker"], row["method"], row["arm"], row.get("pop", "-"),
                                                                    row["what"], row.get("record", "-"), row.get("method_value", "-"), det))
    else:
        lines.append("None.")
    lines += ["", "## Choices where the plan is silent", ""] + ["- " + c for c in out["choices"]]
    lines += ["", "Code: `50_CODE/x3/x3_stats_c1_v01.py`, `x3_stats_common_v01.py` (sha256 in the JSON). Nothing here changes the verdict "
              "of record, a claim status or a table of record.", ""]
    C.text_new(path, "\n".join(lines))


CHOICES = [
    "(i) is computed exactly as the code of record (sup-t on the bootstrap SE, k6_analyse_v02.flag via R21's re-derivation); "
    "'percentile' in the plan is read as 'the record's bootstrap bound'. For one cell it equals the basic bootstrap bound "
    "2E - Q_{1-L}(E*); the pure percentile UB of HK1c is also reported.",
    "(ii) the estimator is the record's (mean over logs with records of the per-log rate; in the bootstrap a ratio of two log totals), "
    "so its cluster delta-method SE is the ratio's: U/(U-1) sum_u 1[N_u>0](p_u - R)^2 / m^2 over all U = 375 logs.",
    "(ii) the floor sqrt(delta(1-delta)/N_eff) uses N_eff = N/deff of (iii) (records N, deff from the ANOVA ICC), recomputed on each "
    "replicate with the replicate's multiplicities, so the pivot uses the same SE formula in sample and replicate.",
    "(ii) simultaneity: sup-t over the same cell sets as the record (all evaluable cells; the power family; the pooled cell alone).",
    "(ii) primary on X3's weights [20261201, i, 3], B = 4000 (plan section 0); also on the record's weights (B = 40000), because the "
    "removal level 0.998611 leaves only about 5.6 replicates beyond the quantile at B = 4000.",
    "(iii) ANOVA ICC for unbalanced clusters (MSB, MSW, n0) over the logs with records in the cell, truncated to [0, 1]; m_bar = N / "
    "(logs with records); centre = the record's estimate; the variant centred on x/n is reported as iii_pooledcentre.",
    "(iii) one-sided Wilson bound with z = Phi^-1(1 - (1 - L)/J), J = the number of cells in the record's sup-t set (Bonferroni); "
    "J = 1 for the pooled cell (pooled LB at the arm's level, HK1c UB at 0.995).",
    "Status rules are the code of record's (c1_analyse_v02.arm_status): a comparator is 'shown above' on a cell, family or pooled "
    "flag or an HK1c failure; the 9-condition reading of plan 6.2 (no HK1c term) is reported alongside.",
    "Families (power rule) and evaluable sets are fixed at the record's; the power rule is not an interval and is not recomputed.",
    "Where V_t changes, Form B is recomputed with the record's paired percentile bootstrap on the record's weights (B = 40000) at "
    "1 - 0.0125/|V_t|.",
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--trackers", default="t1,t3")
    a = ap.parse_args(argv)
    jpath = os.path.join(a.out_dir, "x3_c1_intervals_v01.json")
    mpath = os.path.join(a.out_dir, "x3_c1_intervals_v01.md")
    for p in (jpath, mpath):
        if os.path.exists(p):
            sys.exit("refusing to overwrite " + p)

    def log(*x):
        print(time.strftime("%H:%M:%S"), *x, flush=True)

    assert C.sha256(C.PLAN) == C.PLAN_SHA, "plan hash differs"
    log("reading the record extract")
    ext = C.load_record_extract(tuple(a.trackers.split(",")))
    out = {"stamp": C.STAMP, "analysis": "X3 (c1) interval sensitivity, plan 2(c1); referee M4", "json_name": jpath,
           "plan": {"path": "20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md", "sha256": C.PLAN_SHA},
           "inputs": {"analysis_sha256": ext["analysis_sha256"], "decision_sha256": C.sha256(C.DECISION)},
           "code_sha256": {os.path.basename(p): C.sha256(p) for p in (os.path.abspath(__file__), C.__file__, L.__file__)},
           "versions": C.versions(), "methods": METHOD_LABEL, "primary_methods": PRIMARY, "choices": CHOICES,
           "seeds": {"record_weights": "[20261110, i, 0], B = 40000", "x3_weights": "[20261201, i, 3], B = 4000"},
           "levels": {"Mstar": C.LEVEL_M, "removal": C.LEVEL_RM, "hk1c": C.L_HK1C, "hk1c_threshold": C.DELTA + C.HK1C_MARGIN},
           "trackers": {}}
    with heavy_lock("x3-stats: (c1) interval sensitivity, B = 40000 and 4000 on 375 logs"):
        for t in a.trackers.split(","):
            out["trackers"][t] = run_tracker(t, ext, log)
    out["summary"] = summarise(out["trackers"])
    C.jdump_new(jpath, out)
    write_md(mpath, out)
    log("wrote", jpath, mpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
