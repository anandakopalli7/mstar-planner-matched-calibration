#!/usr/bin/env python3
"""r21_rederive_v01 (7 Nov 2026): R21's independent re-derivation of H1 (with and without zero-SE removals), H2, H3, H4 and
the K8 arm tables from the run tables, compared with the frozen analysis's decision, analysis JSON and CSV tables.

Standalone (imports only r21_lib_v01 and numpy); runs nothing from 50_CODE; reads only the files named on the command line or in
the config's routes. Rules: R21_DESIGN_v01.md. Output: one JSON (every re-derived value beside the analysis's value, with an
agree / MC-borderline / disagree class) and a short markdown summary. The frozen verdict stands whatever this prints (plan s.9).

Usage (canmot310 or any python with numpy):
  python -B r21_rederive_v01.py --config <cfg.json> --analysis <c1_analysis.json> --decision <c1_decision.json>
      --csv-dir <analysis csv dir> --out <r21.json> --md <r21.md> [--B 40000] [--power-datasets 500]
      [--routes within_lt3d,transfer_lt3d] [--k8-routes within_lt3d] [--k8-trackers t1,t3] [--max-mem-mb 0]
"""
import argparse
import csv
import itertools
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r21_lib_v01 as L  # noqa: E402
import numpy as np  # noqa: E402


# ------------------------------------------------------------------ comparison bookkeeping
class Cmp:
    def __init__(self, B_r21, B_an, power_n):
        self.rows, self.B, self.B_an, self.power_n = [], B_r21, B_an, power_n
        self.tb = L.tol_bound(B_r21, B_an)
        self.exact_weights = None

    def tol(self, mcse=None, level=None):
        """max(fixed tol(B), 4 x the combined Andrews-Buchinsky MC SE of R21 at B and the analysis at B_an). A bound at a level
        with fewer than 10 replicates beyond it at R21's B (B (1 - level) < 10: not estimable, plan 6.1's own rule) gets 0.05."""
        t = self.tb
        if mcse is not None and math.isfinite(mcse):
            t = max(t, 4.0 * mcse * math.sqrt(1.0 + float(self.B) / self.B_an))
        if level is not None and self.B * (1.0 - level) < 10:
            t = max(t, 0.05)
        return t

    def add(self, key, r21, an, rule, tol=None, borderline=False, note=None):
        if an is None and rule != "info":
            self.rows.append({"key": key, "r21": r21, "analysis": None, "rule": rule, "class": "not in analysis output", "note": note})
            return
        agree = None
        if rule == "exact":
            agree = _norm(r21) == _norm(an)
        elif rule in ("abs", "1e-9"):
            t = 1e-9 if rule == "1e-9" else tol
            agree = (r21 is not None and an is not None and abs(float(r21) - float(an)) <= t) or (r21 is None and an is None)
        elif rule == "info":
            agree = None
        cls = "info" if agree is None else ("agree" if agree else ("MC-borderline" if borderline and not self.exact_weights else "disagree"))
        row = {"key": key, "r21": r21, "analysis": an, "rule": rule if rule != "abs" else "abs<=%.3g" % tol, "class": cls}
        if rule == "abs":
            row["diff"] = None if (r21 is None or an is None) else float(r21) - float(an)
        if note:
            row["note"] = note
        self.rows.append(row)

    def summary(self):
        out = {}
        for r in self.rows:
            out[r["class"]] = out.get(r["class"], 0) + 1
        return out


def _norm(v):
    if isinstance(v, (list, tuple, set)):
        return sorted(_norm(x) for x in v)
    if isinstance(v, (np.bool_,)):
        return bool(v)
    if isinstance(v, float) and v.is_integer():
        return int(v)
    return v


def g(d, *path, default=None):
    for p in path:
        if isinstance(d, dict) and p in d:
            d = d[p]
        else:
            return default
    return d


def fl(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def read_csv(path):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


# ------------------------------------------------------------------ analysis inputs
def analysis_mstar_power(an_rt):
    """The analysis's per-cell power at 0.15 for M* (status.Mstar.descriptive_power), its family and the size check."""
    out = {}
    for pop in L.POPS:
        pc = g(an_rt, "status", "Mstar", "descriptive_power", "pops", pop, "per_cell")
        if pc is None:
            return None
        pw = {c: fl(v.get("0.15")) for c, v in pc.items()}
        fam = [c for c, v in pw.items() if v is not None and v >= L.POWER_MIN]
        out[pop] = {"power": pw, "family": fam, "family_size_status": g(an_rt, "status", "Mstar", "pops", pop, "family_size")}
    return out


def recover_family(N, ev_names, power, k, share, max_combos=300000):
    """The analysis's power family identified from its published size and record share: the unique subset of evaluable cells
    of that size whose share of the population's records equals the published share (to 1e-12), searched among the cells that
    R21's own power ranks near 0.80. Returns (family or None, note)."""
    if k is None or share is None:
        return None, "size or share not published"
    tot = float(N.sum())
    if k == 0:
        return [], "empty family"
    if tot <= 0:
        return None, "no records"
    recs = {c: float(N[:, L.CELLNAMES.index(c)].sum()) for c in ev_names}
    pw = {c: (power or {}).get(c) for c in ev_names}
    for width in (0.1, 0.2, 0.35, 1.01):
        if power:
            forced = [c for c in ev_names if pw[c] is not None and pw[c] >= L.POWER_MIN + width]
            cand = [c for c in ev_names if c not in forced and (pw[c] is None or pw[c] >= L.POWER_MIN - width)]
        else:
            forced, cand = [], list(ev_names)
        need = k - len(forced)
        if need < 0 or need > len(cand) or math.comb(len(cand), need) > max_combos:
            continue
        base = sum(recs[c] for c in forced)
        hits = [combo for combo in itertools.combinations(cand, need) if abs((base + sum(recs[c] for c in combo)) / tot - share) <= 1e-12]
        if len(hits) == 1:
            return sorted(forced + list(hits[0]), key=L.CELLNAMES.index), "recovered (unique; window %.2f)" % width
        if len(hits) > 1:
            best = max(hits, key=lambda h: sum((pw.get(c) or 0.0) for c in h))
            return sorted(forced + list(best), key=L.CELLNAMES.index), "ambiguous: %d subsets match; chose the largest R21 power sum" % len(hits)
    return None, "no subset matches"


# ------------------------------------------------------------------ comparisons
def borderline_sets(r, cmp, level=None):
    """R21's borderline components of one arm and population (bounds within tolerance of their threshold; powers near 0.80
    only when the family came from R21's own power rule)."""
    flags = [c for c, v in r["cells"].items() if v["lb"] is not None and abs(v["lb"] - L.DELTA) <= cmp.tol(v.get("lb_mcse"), level)]
    fam = [c for c, v in (r.get("family_lb") or {}).items()
           if v is not None and abs(v - L.DELTA) <= cmp.tol((r.get("family_lb_mcse") or {}).get(c), level)]
    tp = L.tol_power(cmp.power_n)
    pw = []
    if str(r.get("family_source", "")).startswith("R21"):
        pw = [c for c, v in (r.get("power") or {}).items() if v is not None and abs(v - L.POWER_MIN) <= tp]
    pooled = r["pooled"]
    pl = pooled.get("lb") is not None and abs(pooled["lb"] - L.DELTA) <= cmp.tol(pooled.get("lb_mcse"), level)
    hk = pooled.get("ub") is not None and abs(pooled["ub"] - (L.DELTA + L.HK1C_MARGIN)) <= cmp.tol(pooled.get("ub_mcse"))
    return {"flags": flags, "family": fam + pw, "pooled": pl, "hk1c": hk}


def compare_h1_arms(cmp, route, t, res, an_rt, an_power):
    pre = "%s/%s" % (route, t)
    for arm in ["Mstar"] + L.COMPS:
        pops = res["arms"].get(arm)
        if pops is None:
            cmp.add("%s/%s: arm present" % (pre, arm), False, True, "exact")
            continue
        for pop in L.POPS:
            r = pops[pop]
            s = r["status"]
            a = g(an_rt, "status", arm, "pops", pop)
            if a is None:
                cmp.add("%s/%s/%s status" % (pre, arm, pop), True, None, "exact")
                continue
            bl = borderline_sets(r, cmp, res["levels"]["Mstar"] if arm == "Mstar" else res["levels"]["comparators"])
            k = "%s/%s/%s" % (pre, arm, pop)
            cmp.add(k + " evaluable cells", s["n_evaluable"], a.get("evaluable"), "exact")
            cmp.add(k + " flagged cells", r["flagged"], a.get("flagged_cells"), "exact", borderline=bool(bl["flags"]),
                    note="borderline cells %s" % bl["flags"] if bl["flags"] else None)
            cmp.add(k + " NoFlag", s["NoFlag"], a.get("NoFlag"), "exact", borderline=bool(bl["flags"]))
            fam_bl = bool(bl["family"])
            cmp.add(k + " family size", s["family_size"], a.get("family_size"), "exact", borderline=fam_bl,
                    note="family source: %s" % r.get("family_source"))
            fsh = g(an_rt, "status", arm, "criteria", "families", pop, "record_share")
            if fsh is not None and r.get("family_record_share") is not None:
                cmp.add(k + " family record share", r["family_record_share"], fl(fsh), "abs", 1e-9, borderline=fam_bl,
                        note="family source: %s" % r.get("family_source"))
            cmp.add(k + " family flagged", r.get("family_flagged", []), a.get("family_flagged"), "exact", borderline=fam_bl)
            cmp.add(k + " FamFlag", s["FamFlag"], a.get("FamFlag"), "exact", borderline=fam_bl)
            cmp.add(k + " pooled evaluable", s["pooled_evaluable"], a.get("pooled_evaluable"), "exact")
            cmp.add(k + " NoFlag_pool", s["NoFlag_pool"], a.get("NoFlag_pool"), "exact", borderline=bl["pooled"])
            cmp.add(k + " Floor", s["Floor"], a.get("Floor"), "exact", borderline=fam_bl)
            cmp.add(k + " HK1c", s["HK1c"], a.get("HK1c"), "exact", borderline=bl["hk1c"])
            anyb = bool(bl["flags"] or fam_bl or bl["pooled"] or bl["hk1c"])
            cmp.add(k + " valid", s["valid"], a.get("valid"), "exact", borderline=anyb)
            cmp.add(k + " shown_above", s["shown_above"], a.get("shown_above"), "exact", borderline=anyb)
            z = g(an_rt, "status", arm, "criteria", "zero_se", pop)
            if z is not None:
                cmp.add(k + " zero-SE flagged cells", r.get("zero_se_flagged", []), z.get("cells"), "exact")
                cmp.add(k + " zero-SE flagged family cells", r.get("family_zero_se_flagged", []), z.get("family"), "exact")
                cmp.add(k + " zero-SE pooled flag", bool(r["pooled"].get("zero_se_flag", False)), z.get("pooled"), "exact")
        if arm == "Mstar":
            for pop in L.POPS:
                r = pops[pop]
                du = g(an_rt, "status", "Mstar", "descriptive_simultaneous_ub_0.95", "pops", pop)
                if du is not None and r.get("U_cells_0.95") is not None:
                    um = [r["U_mcse_0.95"].get(c) for c in r["U_cells_0.95"]] if r.get("U_mcse_0.95") else []
                    um = max([x for x in um if x is not None], default=None)
                    cmp.add("%s/Mstar/%s U_max (0.95, descriptive)" % (pre, pop), r.get("U_max_0.95"), fl(du.get("max_ub")), "abs", cmp.tol(um))
                    for c, v in r["U_cells_0.95"].items():
                        cmp.add("%s/Mstar/%s U cell %s" % (pre, pop, c), v, fl(g(du, "cells", c)), "abs",
                                cmp.tol((r.get("U_mcse_0.95") or {}).get(c)))
                if an_power is not None and r.get("power"):
                    ap = an_power[pop]
                    cmp.add("%s/Mstar/%s analysis family size = count(power >= 0.80) (internal consistency)" % (pre, pop),
                            len(ap["family"]), ap["family_size_status"], "exact")
                    tp = L.tol_power(cmp.power_n)
                    for c, v in r["power"].items():
                        cmp.add("%s/Mstar/%s power(0.15) %s" % (pre, pop, c), v, ap["power"].get(c), "abs", tp)
                    own = [c for c, v in r["power"].items() if v is not None and v >= L.POWER_MIN]
                    bl = [c for c in set(own) ^ set(ap["family"]) if r["power"].get(c) is not None and abs(r["power"][c] - L.POWER_MIN) <= tp]
                    cmp.add("%s/Mstar/%s R21-own family (check)" % (pre, pop), own, ap["family"], "exact",
                            borderline=bool(bl) or not (set(own) ^ set(ap["family"])))


def compare_form_b(cmp, pre, asm, an_fb, data, W, route, p_mult=1):
    fb = asm["form_b"]
    an_fb = an_fb or {}
    an_V = list(an_fb.get("V") or [])
    diff = [c for c in L.COMPS if (c in an_V) != (c in asm["V"])]
    rs = asm["removal_stat_max_lb_minus_delta"]
    bl = [c for c in diff if (rs.get(c) is not None and abs(rs[c]) <= cmp.tol(asm.get("removal_stat_mcse", {}).get(c)))
          or asm["power_near_0.80"].get(c)]
    v_border = bool(diff) and len(bl) == len(diff)
    cmp.add(pre + " V_t", asm["V"], an_fb.get("V"), "exact", borderline=v_border,
            note=("differing %s; R21 removal statistic (max LB - delta) %s" % (diff, {c: rs.get(c) for c in diff})) if diff else None)
    cmp.add(pre + " removed (shown above)", asm["removed_shown_above"], an_fb.get("removed_shown_above"), "exact", borderline=v_border)
    cmp.add(pre + " |V_t|", fb["n_V"], an_fb.get("n_V"), "exact", borderline=v_border)
    if fb["level"] is not None:
        cmp.add(pre + " Form B level", fb["level"], an_fb.get("level"), "1e-9", borderline=v_border)
    # like-for-like bounds: R21's code on the analysis's V_t when the sets differ
    if diff and an_V:
        rate_m = data.inf("Mstar")
        fb_cmp = L.form_b(W, rate_m, {c: data.inf(c) for c in an_V}, an_V,
                          level_alpha=(L.ALPHA_FOR / 2 if route == L.H4_ROUTE else L.ALPHA_FORM_B), p_multiplier=p_mult)
        asm["form_b_on_analysis_V"] = fb_cmp
        tag = " (R21 on the analysis's V_t)"
    else:
        fb_cmp, tag = fb, ""
    for c, v in fb_cmp["vs"].items():
        av = (an_fb.get("vs") or {}).get(c)
        if av is None:
            cmp.add(pre + " Form B vs %s%s" % (c, tag), v["ub"], None, "abs", cmp.tol(v.get("ub_mcse")))
            continue
        cmp.add(pre + " mean diff M* - %s" % c, v["mean_diff"], fl(av.get("mean_diff")), "1e-9")
        t_ = cmp.tol(v.get("ub_mcse"), v.get("level"))
        cmp.add(pre + " Form B UB M* - %s%s" % (c, tag), v["ub"], fl(av.get("ub")), "abs", t_)
        cmp.add(pre + " p_c M* - %s" % c, v["p"], fl(av.get("p_lt0")), "abs", L.tol_p(v["p"], cmp.B, cmp.B_an))
        cmp.add(pre + " UB < 0 M* - %s%s" % (c, tag), v["ub"] < 0, (fl(av.get("ub")) or 0) < 0, "exact",
                borderline=abs(v["ub"]) <= t_)
    near0 = any(abs(v["ub"]) <= cmp.tol(v.get("ub_mcse")) for v in fb["vs"].values())
    cmp.add(pre + " Form B met", asm["met"], an_fb.get("met"), "exact", borderline=near0 or v_border)
    cmp.add(pre + " vacuous", asm["vacuous"], an_fb.get("vacuous"), "exact", borderline=v_border)
    if not fb_cmp["vacuous"]:
        pb = an_fb.get("p_rejection_bonferroni")
        cmp.add(pre + " Form B p (|V| x max p_c x %d)%s" % (p_mult, tag), fb_cmp["p"], fl(pb), "abs",
                p_mult * fb_cmp["n_V"] * L.tol_p(min(1.0, fb_cmp["p"] / max(1, p_mult * fb_cmp["n_V"])), cmp.B, cmp.B_an))
    cmp.add(pre + " Valid(M*)", asm["valid_Mstar"], an_fb.get("valid_method"), "exact")


def compare_k8(cmp, route, t, k8, csv_dir):
    pre = "%s/%s K8" % (route, t)
    base = os.path.join(csv_dir, "k8_%s_%s_decide_" % (route, t)) if csv_dir else None
    if not base:
        return
    counts = read_csv(base + "counts.csv")
    val = read_csv(base + "validity.csv")
    cells = read_csv(base + "cells.csv")
    trade = read_csv(base + "tradeoff.csv")
    arms_c = read_csv(base + "arms.csv")
    cal = read_csv(base + "cal_relied.csv")
    v2 = read_csv(base + "v2.csv")
    saf = read_csv(base + "safety.csv")
    for row in counts or []:
        a, p = row["arm"], row["population"]
        r = g(k8, a, "pops", p)
        if r is None:
            continue
        cmp.add("%s counts %s/%s records" % (pre, a, p), r["records"], fl(row.get("records")), "exact")
        cmp.add("%s counts %s/%s exceed" % (pre, a, p), r["exceed"], fl(row.get("exceed")), "exact")
        cmp.add("%s counts %s/%s units" % (pre, a, p), r["units"], fl(row.get("scenes")), "exact")
    for row in val or []:
        a, p = row["arm"], row["population"]
        r = g(k8, a, "pops", p)
        if r is None:
            continue
        lev = k8[a].get("level_C1")
        k = "%s validity(C1 level %.5f) %s/%s" % (pre, lev, a, p)
        cmp.add(k + " evaluable", r["n_evaluable"], fl(row.get("evaluable")), "exact")
        flagged = [x for x in (row.get("flagged") or "").split(";") if x]
        bl = [c for c, v in (r.get("flag_lb_C1") or {}).items()
              if v is not None and abs(v - L.DELTA) <= cmp.tol((r.get("flag_lb_C1_mcse") or {}).get(c), lev)]
        cmp.add(k + " flagged", r["flagged"], flagged, "exact", borderline=bool(bl))
        if row.get("pooled_E") not in (None, ""):
            cmp.add(k + " pooled E", r["pooled_E"], fl(row.get("pooled_E")), "1e-9")
            cmp.add(k + " pooled LB", r.get("pooled_lb"), fl(row.get("pooled_lb")), "abs", cmp.tol(r.get("pooled_lb_mcse"), lev))
            cmp.add(k + " pooled UB(0.995)", r.get("pooled_ub"), fl(row.get("pooled_ub")), "abs", cmp.tol(r.get("pooled_ub_mcse")),
                    note="R21 studentised; percentile %.6f" % r["pooled_ub_percentile"] if r.get("pooled_ub_percentile") is not None else None)
        else:
            cmp.add(k + " pooled E (analysis empty)", r["pooled_E"], None, "info")
        cmp.add(k + " pooled flagged", r.get("pooled_flagged"), row.get("pooled_flagged") == "True", "exact",
                borderline=r.get("pooled_lb") is not None and abs(r["pooled_lb"] - L.DELTA) <= cmp.tol(r.get("pooled_lb_mcse"), lev))
        cmp.add(k + " HK1c", r.get("HK1c"), row.get("HK1c") == "True", "exact",
                borderline=r.get("pooled_ub") is not None and abs(r["pooled_ub"] - 0.08) <= cmp.tol(r.get("pooled_ub_mcse")))
    for row in cells or []:
        a, p, c = row["arm"], row["population"], row["cell"]
        r = g(k8, a, "pops", p, "cells", c)
        if r is None:
            continue
        k = "%s cell(0.95) %s/%s/%s" % (pre, a, p, c)
        cmp.add(k + " E", r["E"], fl(row.get("E")), "1e-9")
        cmp.add(k + " records", r["records"], fl(row.get("records")), "exact")
        cmp.add(k + " units", r["units"], fl(row.get("scenes")), "exact")
        cmp.add(k + " SE", r["se"], fl(row.get("se")), "abs", cmp.tol(r.get("lb_mcse")))
        cmp.add(k + " LB", r["lb"], fl(row.get("lb_sim")), "abs", cmp.tol(r.get("lb_mcse")))
        cmp.add(k + " UB", r["ub"], fl(row.get("ub_sim")), "abs", cmp.tol(r.get("ub_mcse")))
        if row.get("sig_above") in ("True", "False"):
            cmp.add(k + " flag", r["flag"], row["sig_above"] == "True", "exact",
                    borderline=r["lb"] is not None and abs(r["lb"] - L.DELTA) <= cmp.tol(r.get("lb_mcse")))
    for row in trade or []:
        a = row["arm"]
        r = k8.get(a)
        if r is None:
            continue
        cmp.add("%s tradeoff %s infeasible" % (pre, a), r.get("infeasible_rate"), fl(row.get("infeasible_rate")), "1e-9")
        cmp.add("%s tradeoff %s M*-arm infeasible" % (pre, a), r.get("Mstar_minus_arm_infeasible"), fl(row.get("Mstar_minus_arm_infeasible")), "1e-9")
        for p, col in (("PD7_primary", "pooled_PD7_E"), ("SD1_7_gap_le_5m", "pooled_SD1_7_E"), ("PD_inpath", "pooled_PD_E")):
            if row.get(col) in (None, ""):
                cmp.add("%s tradeoff %s %s (analysis empty)" % (pre, a, col), g(r, "pops", p, "pooled_E"), None, "info")
            else:
                cmp.add("%s tradeoff %s %s" % (pre, a, col), g(r, "pops", p, "pooled_E"), fl(row.get(col)), "1e-9")
    for row in arms_c or []:
        a = row["arm"]
        r = k8.get(a)
        if r is None:
            continue
        ms = r.get("infeasible_ci95_mcse") or [None, None]
        cmp.add("%s arms %s decisions" % (pre, a), r.get("decisions"), fl(row.get("decisions")), "exact")
        cmp.add("%s arms %s infeasible ci95 lo" % (pre, a), (r.get("infeasible_ci95") or [None])[0], fl(row.get("infeasible_ci95_lo")), "abs", cmp.tol(ms[0]))
        cmp.add("%s arms %s infeasible ci95 hi" % (pre, a), (r.get("infeasible_ci95") or [None, None])[1], fl(row.get("infeasible_ci95_hi")), "abs", cmp.tol(ms[1]))
    for row in cal or []:
        a, p = row["arm"], row["population"]
        r = g(k8, a, "pops", p)
        if r is None or r.get("cal_records") is None:
            continue
        cmp.add("%s margins %s/%s records" % (pre, a, p), r["cal_records"], fl(row.get("records")), "exact")
        if row.get("mean_margin_long") in (None, ""):
            cmp.add("%s margins %s/%s (analysis empty)" % (pre, a, p), r["mean_margin_long"], None, "info")
            continue
        cmp.add("%s margins %s/%s mean long" % (pre, a, p), r["mean_margin_long"], fl(row.get("mean_margin_long")), "1e-9")
        cmp.add("%s margins %s/%s mean lat" % (pre, a, p), r["mean_margin_lat"], fl(row.get("mean_margin_lat")), "1e-9")
    for row in v2 or []:
        a, p, var = row["arm"], row["population"], row["variant"]
        r = g(k8, a, "pops", p, var)
        if r is None:
            continue
        k = "%s %s %s/%s" % (pre, var, a, p)
        if row.get("E") in (None, ""):
            cmp.add(k + " E (analysis empty)", r["E"], None, "info")
            continue
        cmp.add(k + " E", r["E"], fl(row.get("E")), "1e-9")
        cmp.add(k + " decisions with records", r["decisions_with_records"], fl(row.get("decisions_with_records")), "exact")
        cmp.add(k + " decisions any", r["decisions_any"], fl(row.get("decisions_any_exceed")), "exact")
        if r.get("ci95"):
            ms = r.get("ci95_mcse") or [None, None]
            cmp.add(k + " ci95 lo", r["ci95"][0], fl(row.get("ci95_lo")), "abs", cmp.tol(ms[0]))
            cmp.add(k + " ci95 hi", r["ci95"][1], fl(row.get("ci95_hi")), "abs", cmp.tol(ms[1]))
        if var == "V2":
            cmp.add(k + " reference E", r.get("reference_E"), fl(row.get("reference_E")), "1e-9")
            cmp.add(k + " mean tracks", r.get("mean_tracks_per_decision"), fl(row.get("mean_tracks_per_decision")), "1e-9")
    for row in saf or []:
        a = row["arm"]
        for p in L.POPS4:
            r = g(k8, a, "pops", p, "V2_viol")
            if r is None:
                continue
            lab = L.LAB[p]
            if row.get("V2_viol_%s_E" % lab) in (None, ""):
                cmp.add("%s V2_viol %s/%s E (analysis empty)" % (pre, a, lab), r["E"], None, "info")
                continue
            cmp.add("%s V2_viol %s/%s E" % (pre, a, lab), r["E"], fl(row.get("V2_viol_%s_E" % lab)), "1e-9")
            cmp.add("%s V2_viol %s/%s decisions any" % (pre, a, lab), r["decisions_any"], fl(row.get("V2_viol_%s_decisions_any_violation" % lab)), "exact")


# ------------------------------------------------------------------ main
def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--analysis")
    ap.add_argument("--decision")
    ap.add_argument("--csv-dir")
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--B", type=int, default=L.B_REGISTERED)
    ap.add_argument("--B-analysis", type=int, default=L.B_REGISTERED)
    ap.add_argument("--power-datasets", type=int, default=500)
    ap.add_argument("--routes", default="within_lt3d,transfer_lt3d")
    ap.add_argument("--trackers", default="t1,t3")
    ap.add_argument("--k8-routes", default="within_lt3d")
    ap.add_argument("--k8-trackers", default="t1,t3")
    ap.add_argument("--no-k8", action="store_true")
    ap.add_argument("--max-mem-mb", type=float, default=0.0, help="abort if the working set exceeds this (0: off)")
    a = ap.parse_args(argv)
    for _p in (a.out, a.md):
        os.makedirs(os.path.dirname(os.path.abspath(_p)), exist_ok=True)
    t_start = time.time()
    mem = L.MemGuard(a.max_mem_mb)
    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    routes_cfg = {r["name"]: r for r in cfg["routes"]}
    an = dec = None
    if a.analysis:
        with open(a.analysis, encoding="utf-8") as f:
            an = json.load(f)
    if a.decision:
        with open(a.decision, encoding="utf-8") as f:
            dec = json.load(f)
    cmp = Cmp(a.B, a.B_analysis, a.power_datasets)
    out = {"label": "R21 independent re-derivation (descriptive review; the frozen verdict stands, plan section 9)",
           "design": "R21_DESIGN_v01.md", "versions": L.versions(), "B": a.B, "B_analysis": a.B_analysis,
           "power_datasets": a.power_datasets, "tolerance_bound": cmp.tb,
           "inputs": {"config": a.config, "config_sha256": L.sha256(a.config),
                      "analysis": a.analysis, "analysis_sha256": L.sha256(a.analysis) if a.analysis else None,
                      "decision": a.decision, "decision_sha256": L.sha256(a.decision) if a.decision else None,
                      "csv_dir": a.csv_dir},
           "code_sha256": {os.path.basename(p): L.sha256(p) for p in (os.path.abspath(__file__), L.__file__)},
           "routes": {}, "H1": {}, "comparisons": None}
    exact_probe = []
    h1_parts = {}
    for route in [r for r in a.routes.split(",") if r]:
        rc = routes_cfg.get(route)
        if rc is None:
            out["routes"][route] = {"missing": "route not in config"}
            continue
        out["routes"][route] = {}
        for t in [x for x in a.trackers.split(",") if x]:
            if t not in rc["tags"]:
                continue
            t0 = time.time()
            log("load", route, t)
            data = L.RouteData(rc["runs"], rc["tags"][t], t, fits_path=rc["fits"].get(t), mem=mem)
            ret = data.select_retuned()
            i, j = L.TRACKER_INDEX[t], L.ROUTE_INDEX[route]
            W = L.Weights([L.SEED_BOOT, i, j], data.U, a.B)
            an_rt = g(an, "c1", route, t) if an else None
            an_power = analysis_mstar_power(an_rt) if an_rt else None
            mfam = {p: an_power[p]["family"] for p in L.POPS} if an_power else None
            recovered = {}

            def family_fn(arm, pop, N, ev_names, own_power, an_rt=an_rt, an_power=an_power, recovered=recovered):
                """M*: the analysis's per-cell power (exact); comparators: the analysis's family recovered from its size and
                record share; None (R21's own power rule) when neither is available."""
                if an_rt is None:
                    return None
                if arm == "Mstar" and an_power is not None:
                    recovered[(arm, pop)] = "analysis per-cell power at 0.15"
                    return an_power[pop]["family"]
                fam = g(an_rt, "status", arm, "criteria", "families", pop)
                if not fam:
                    recovered[(arm, pop)] = "not published"
                    return None
                f, note = recover_family(N, ev_names, own_power, fam.get("family_size"), fl(fam.get("record_share")))
                recovered[(arm, pop)] = note
                return f

            log("H1 machinery", route, t, "U", data.U, "B", a.B)
            res = L.h1_route_tracker(data, W, route, family_fn=family_fn, power_n=a.power_datasets, mem=mem)
            for (arm_, pop_), note_ in recovered.items():
                if "ambiguous" in note_ and res["arms"].get(arm_):
                    res["arms"][arm_][pop_]["family_source"] = "R21-like (analysis family ambiguous)"
            asm = L.assemble_h1(data, W, res, route)
            # fully independent variant: every family from R21's own power rule (same weights, same power draws)
            own_fams = {arm: {p: L.family_from_power(res["power"][arm][p]["per_cell"]) for p in L.POPS}
                        for arm in res["power"]}
            res_own = L.h1_route_tracker(data, W, route, fixed_families=own_fams, want_power=False, mem=mem)
            asm_own = L.assemble_h1(data, W, res_own, route)
            rt = {"units": data.U, "arms_in_run": data.arms, "input_sha256": data.input_sha256,
                  "run_table_hash_checks": data.hash_checks, "decisions_vs_episodes_mismatch": data.decisions_vs_episodes_mismatch,
                  "not_entered": data.not_entered[:20], "missing_arm_unit": data.missing_arm_unit[:20],
                  "duplicate_episodes": data.duplicate_episodes, "weights_seed": W.seed,
                  "retuned": {k: v for k, v in ret.items() if k != "arm_of_unit"},
                  "Mstar_family_source": "analysis per-cell power at 0.15" if mfam else "R21 own power rule",
                  "family_sources": {"%s/%s" % k_: v_ for k_, v_ in recovered.items()},
                  "assembled": asm, "arms": res["arms"], "power": res["power"],
                  "assembled_with_R21_own_families": {k_: asm_own[k_] for k_ in ("valid_Mstar", "V", "met", "vacuous", "removed_shown_above",
                                                                                  "without_zero_se_removals")},
                  "R21_own_families": {arm: {p: len(v) for p, v in d.items()} for arm, d in own_fams.items()},
                  "infeasible_rate": {x: L.fnum(np.mean(data.inf(x))) for x in data.arms + ["RETUNED"] if data.inf(x) is not None}}
            rt["assembled_with_R21_own_families"]["form_b_ub"] = {c: v["ub"] for c, v in asm_own["form_b"]["vs"].items()}
            if route == "within_lt3d":
                rt["H2_form_c"] = L.form_c(W, data)
                rt["H3"] = L.h3_route_tracker(data, W)
            # ---- comparisons
            pre = "%s/%s" % (route, t)
            if an_rt is not None:
                cmp.add(pre + " run record sha256", data.input_sha256["run_record"], an_rt.get("run_record_sha256"), "exact")
                if "fits" in data.input_sha256:
                    cmp.add(pre + " fits sha256", data.input_sha256["fits"], an_rt.get("fits_sha256"), "exact")
                cmp.add(pre + " bootstrap seed", W.seed, g(an_rt, "seeds", "bootstrap"), "exact")
                for k_, v_ in data.hash_checks.items():
                    cmp.add(pre + " %s sha256 = run record" % k_, v_["now"], v_["recorded"], "exact")
                if ret.get("arm_of_fold") and g(an_rt, "RETUNED_E14", "arm_of_fold"):
                    cmp.add(pre + " RETUNED arm of fold", ret["arm_of_fold"], g(an_rt, "RETUNED_E14", "arm_of_fold"), "exact")
                for x, v in rt["infeasible_rate"].items():
                    if g(an_rt, "infeasible_rate", x) is not None:
                        cmp.add(pre + " infeasible rate %s" % x, v, fl(an_rt["infeasible_rate"][x]), "1e-9")
                compare_h1_arms(cmp, route, t, res, an_rt, an_power)
                compare_form_b(cmp, pre + (" H4" if route == L.H4_ROUTE else " H1"), asm, an_rt.get("form_b"), data, W, route,
                               p_mult=2 if route == L.H4_ROUTE else 1)
                cmp.add(pre + " Form B met with R21's own families (fully independent check)", asm_own["met"],
                        g(an_rt, "form_b", "met"), "exact", borderline=True,
                        note="families from R21's power rule at %d datasets; differences are MC of the power rule" % a.power_datasets)
                if route == "within_lt3d":
                    fc, afc = rt["H2_form_c"], an_rt.get("form_c") or {}
                    cmp.add(pre + " H2 Form C mean diff", fc["mean_diff"], fl(afc.get("mean_diff")), "1e-9")
                    cmp.add(pre + " H2 Form C UB(0.975)", fc["ub"], fl(afc.get("ub")), "abs", cmp.tol(fc.get("ub_mcse")))
                    cmp.add(pre + " H2 Form C met", fc["met"], afc.get("met"), "exact", borderline=abs(fc["ub"] - 0.03) <= cmp.tol(fc.get("ub_mcse")))
                    cmp.add(pre + " H2 p", fc["p"], fl(afc.get("p")), "abs", L.tol_p(fc["p"], a.B, a.B_analysis))
                    h3, ah3 = rt["H3"], an_rt.get("H3") or {}
                    if h3.get("available", True):
                        cmp.add(pre + " H3 ValidJ(M*Jx)", h3["validJ_method"], ah3.get("validJ_method"), "exact",
                                borderline=any(abs((v["lb"] or 0) - L.DELTA) <= cmp.tol(v.get("lb_mcse")) or abs((v["ub"] or 0) - 0.08) <= cmp.tol(v.get("ub_mcse"))
                                               for v in h3["pops"].values()))
                        vj_bl = any(c_["removed_by"] and any(abs(x["lb"] - L.DELTA) <= cmp.tol(x.get("lb_mcse")) for x in c_["removed_by"])
                                    for c_ in h3["comparators"].values() if c_["removed_by"])
                        cmp.add(pre + " H3 V^J", h3["VJ"], ah3.get("VJ"), "exact", borderline=vj_bl)
                        for c, v in h3["form"]["vs"].items():
                            av = g(ah3, "vs", c) or {}
                            cmp.add(pre + " H3 UB M*Jx - %s" % c, v["ub"], fl(av.get("ub")), "abs", cmp.tol(v.get("ub_mcse")))
                        if h3["form"]["level"] is not None:
                            cmp.add(pre + " H3 level", h3["form"]["level"], fl(ah3.get("level")), "1e-9")
                        cmp.add(pre + " H3 met (bound form)", h3["met_bound_form"], ah3.get("met"), "exact")
                        if not h3["form"]["vacuous"]:
                            cmp.add(pre + " H3 p (doubled)", h3["p"], fl(ah3.get("p_rejection_bonferroni")), "abs",
                                    2 * h3["form"]["n_V"] * L.tol_p(h3["p"] / (2 * h3["form"]["n_V"]), a.B, a.B_analysis))
                ze = g(dec, "zero_se_effects", "by_route", route, t) if dec else None
                if ze is not None:
                    an_changed = sorted(c for c, v in ze.items() if v.get("changed_V_t"))
                    cmp.add(pre + " comparators whose V_t membership is changed by zero-SE flags",
                            asm["without_zero_se_removals"]["zero_se_removed"], an_changed, "exact")
            h1_parts[(route, t)] = asm
            out["routes"][route][t] = rt
            rt["seconds"] = time.time() - t0
            rt["memory"] = L.memory_mb()
            log("done", route, t, round(rt["seconds"], 1), "s", rt["memory"])
            # K8 table on the same weights
            if not a.no_k8 and route in a.k8_routes.split(","):
                k8 = L.k8_table(data, W, route, mem=mem)
                rt["K8_table"] = k8
                compare_k8(cmp, route, t, k8, a.csv_dir)
            del data, W
        # descriptive trackers' K8 tables (tab) if asked
        for t in [x for x in a.k8_trackers.split(",") if x and x not in a.trackers.split(",")]:
            if route not in a.k8_routes.split(",") or t not in rc["tags"]:
                continue
            data = L.RouteData(rc["runs"], rc["tags"][t], t, fits_path=rc["fits"].get(t), mem=mem)
            data.select_retuned()
            W = L.Weights([L.SEED_BOOT, L.TRACKER_INDEX[t], L.ROUTE_INDEX[route]], data.U, a.B)
            k8 = L.k8_table(data, W, route, mem=mem)
            out["routes"][route][t] = {"K8_table": k8, "units": data.U, "input_sha256": data.input_sha256}
            compare_k8(cmp, route, t, k8, a.csv_dir)
            del data, W
    # ---- H1 and its zero-SE variant
    if ("within_lt3d", "t1") in h1_parts and ("within_lt3d", "t3") in h1_parts:
        p1, p3 = h1_parts[("within_lt3d", "t1")], h1_parts[("within_lt3d", "t3")]
        h1 = bool(p1["met"] and p3["met"])
        h1nz = bool(p1["without_zero_se_removals"]["met"] and p3["without_zero_se_removals"]["met"])
        out["H1"] = {"holds": h1, "by_tracker": {"t1": p1["met"], "t3": p3["met"]},
                     "without_zero_se_removals": {"holds": h1nz, "V_t1": p1["without_zero_se_removals"]["V"],
                                                  "V_t3": p3["without_zero_se_removals"]["V"],
                                                  "zero_se_removed_t1": p1["without_zero_se_removals"]["zero_se_removed"],
                                                  "zero_se_removed_t3": p3["without_zero_se_removals"]["zero_se_removed"]}}
        if dec is not None:
            anyb = any(r["class"] == "MC-borderline" for r in cmp.rows if r["key"].startswith("within_lt3d/"))
            cmp.add("H1 holds", h1, g(dec, "hypotheses", "H1", "holds"), "exact", borderline=anyb)
            cmp.add("C1 verdict", "GO" if h1 else "NO-GO", dec.get("C1_verdict"), "exact", borderline=anyb,
                    note="R21 checks H1's statistics only, not input provenance")
    if ("transfer_lt3d", "t1") in h1_parts and ("transfer_lt3d", "t3") in h1_parts:
        q1, q3 = h1_parts[("transfer_lt3d", "t1")], h1_parts[("transfer_lt3d", "t3")]
        pf = [(q["form_b"]["p"] if not q["form_b"]["vacuous"] else 1.0, 2 * max(1, q["form_b"]["n_V"])) for q in (q1, q3)]
        valid4 = bool(q1["valid_Mstar"] and q3["valid_Mstar"])
        out["H4"] = {"bound_form_holds": bool(q1["met"] and q3["met"]), "valid_Mstar_both": valid4,
                     "p_form_b": max(x[0] for x in pf), "multiplier": max(pf)[1],
                     "p": max(x[0] for x in pf) if valid4 else 1.0,
                     "p_rule": "p = max_t min(1, 2|V_t| max p_c) (plan 6.1); 1 when Valid(M*) fails on a tracker (H1's formula includes Valid)"}
    if "within_lt3d" in out["routes"] and all(t in out["routes"]["within_lt3d"] for t in ("t1", "t3")):
        r1, r3 = out["routes"]["within_lt3d"]["t1"], out["routes"]["within_lt3d"]["t3"]
        if "H3" in r1 and "H3" in r3 and r1["H3"].get("available", True) and r3["H3"].get("available", True):
            vj = bool(r1["H3"]["validJ_method"] and r3["H3"]["validJ_method"])
            pf = [(x["H3"]["p"], 2 * max(1, x["H3"]["form"]["n_V"])) for x in (r1, r3)]
            out["H3"] = {"bound_form_holds": bool(r1["H3"]["met_bound_form"] and r3["H3"]["met_bound_form"]), "validJ_both": vj,
                         "p_form": max(x[0] for x in pf), "multiplier": max(pf)[1], "p": max(x[0] for x in pf) if vj else 1.0,
                         "p_rule": "p = max_t min(1, 2|V^J| max p_c) (plan 6.1); 1 when ValidJ(M*Jx) fails on a tracker"}
        out["H2"] = {"bound_form_holds": bool(r1["H2_form_c"]["met"] and r3["H2_form_c"]["met"]),
                     "p": max(r1["H2_form_c"]["p"], r3["H2_form_c"]["p"]), "multiplier": 1}
        if dec is not None:
            for h in ("H2", "H3", "H4"):
                fs = g(dec, "family_S", h)
                if fs and h in out and fs.get("p") is not None:
                    m = out[h]["multiplier"]
                    p0 = min(1.0, out[h]["p"] / m)
                    t_ = m * (4 * math.sqrt(max(p0 * (1 - p0), 1e-12) * (1.0 / a.B + 1.0 / a.B_analysis)) + 1.0 / (a.B + 1) + 1.0 / (a.B_analysis + 1))
                    cmp.add("%s p (family S)" % h, out[h]["p"], fl(fs.get("p")), "abs", t_,
                            note="tolerance m (4 sqrt(p(1-p)(1/B + 1/B_an)) + 1/(B+1) + 1/(B_an+1)), m = %d" % m)
    # exact-reproduction probe: every compared Form B UB within 1e-9?
    probe = [abs(r["diff"]) for r in cmp.rows if ("Form B UB" in r["key"] or "pooled LB" in r["key"]) and r.get("diff") is not None]
    out["exact_weight_reproduction"] = {"n_bounds": len(probe), "max_abs_diff": max(probe) if probe else None,
                                        "exact": bool(probe) and max(probe) <= 1e-9}
    out["comparisons"] = cmp.rows
    out["comparison_summary"] = cmp.summary()
    out["disagreements"] = [r for r in cmp.rows if r["class"] == "disagree"]
    out["borderline"] = [r for r in cmp.rows if r["class"] == "MC-borderline"]
    out["seconds"] = time.time() - t_start
    out["memory"] = L.memory_mb()
    L.jdump(a.out, out)
    write_md(a.md, out)
    log("written", a.out, out["comparison_summary"], round(out["seconds"], 1), "s", out["memory"])


def log(*x):
    L.log(*x)


def write_md(path, out):
    s = out["comparison_summary"]
    lines = ["# R21 re-derivation summary", "",
             "Descriptive review; the frozen verdict stands whatever this shows (plan section 9). Rules: R21_DESIGN_v01.md.", "",
             "- B = %d (analysis %d); power check %d datasets; bound tolerance %.4f" % (out["B"], out["B_analysis"], out["power_datasets"], out["tolerance_bound"]),
             "- exact weight reproduction: %s" % json.dumps(out.get("exact_weight_reproduction")),
             "- comparisons: %s" % json.dumps(s),
             "- runtime %.0f s; memory %s" % (out["seconds"], json.dumps({k: round(v) for k, v in (out.get("memory") or {}).items() if v})), ""]
    if out.get("H1"):
        lines += ["## H1", "", "- R21: holds = %s (T1 %s, T3 %s)" % (out["H1"]["holds"], out["H1"]["by_tracker"]["t1"], out["H1"]["by_tracker"]["t3"]),
                  "- without zero-SE removals: %s" % json.dumps(out["H1"]["without_zero_se_removals"]), ""]
    for route, d in out["routes"].items():
        for t, rt in d.items():
            if not isinstance(rt, dict) or "assembled" not in rt:
                continue
            asm = rt["assembled"]
            lines.append("- %s/%s: Valid(M*) %s; V_t %s; Form B met %s; UB %s; RETUNED %s" % (
                route, t, asm["valid_Mstar"], asm["V"], asm["met"],
                {c: round(v["ub"], 4) for c, v in asm["form_b"]["vs"].items()}, rt["retuned"].get("arm_of_fold")))
    for h in ("H2", "H3", "H4"):
        if out.get(h):
            lines.append("- %s: %s" % (h, json.dumps(out[h])))
    lines += ["", "## Disagreements (%d)" % len(out["disagreements"]), ""]
    for r in out["disagreements"][:200]:
        lines.append("- %s: R21 %s, analysis %s (%s)" % (r["key"], _short(r["r21"]), _short(r["analysis"]), r["rule"]))
    lines += ["", "## MC-borderline (%d)" % len(out["borderline"]), ""]
    for r in out["borderline"][:200]:
        lines.append("- %s: R21 %s, analysis %s" % (r["key"], _short(r["r21"]), _short(r["analysis"])))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _short(v):
    s = json.dumps(v, default=str)
    return s if len(s) < 160 else s[:157] + "..."


if __name__ == "__main__":
    main()
