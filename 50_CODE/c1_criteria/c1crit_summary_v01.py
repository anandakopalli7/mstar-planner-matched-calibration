#!/usr/bin/env python3
"""c1crit_summary_v01 (5 Nov 2026): reads the checkpoints of c1crit_rho_v01, c1crit_mc_v01, c1crit_cover_v01 and c1crit_sweep_v01
(nuScenes K8 development data only), applies the post-hoc parameters (F_MIN, the HK1c margin, c), adds question 5 (effect sizes
of the comparators shown above delta) and the H3 comparator-set check of D16 v28 Choice 49(c), and writes
60_RESULTS/c1_criteria_sensitivity_v01/c1crit_summary_v01.json. It computes no new random draw: Forms reuse the K8 weights.
Usage: python -B c1crit_summary_v01.py [--rho-extra lo,est,hi]
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A = C.A
INV = {v: k for k, v in C.LAB.items()}
JOINT = os.path.join(C.W_ROOT, "70_TESTS", "k8_joint_v01_linux", "full_v02fits", "k8_joint_analysis_v04.json")
SE80 = float(np.sqrt(0.8 * 0.2 / 200))


def load(path):
    with open(path) as f:
        return json.load(f)


def v_from_slim(s):
    """hk1_rule-like dict (population names as keys) from MC.slim's entry."""
    return {"pops": {INV[lab]: {"flagged": r["flagged"], "family_flagged": r["family_flagged"], "pooled": r["pooled"],
                                "family_size": r["family_size"], "evaluable": r["evaluable"]} for lab, r in s["pops"].items()}}


def verdict(dev, W, hk1, f_min=6, hk1c=0.03, c=0.03):
    st = {a: C.status_from_hk1(v_from_slim(hk1[a]), f_min, hk1c) for a in C.ARMS}
    fm = C.forms(dev, W, st, c)
    v = C.verdict_summary(st, fm)
    v["Mstar_failing"] = {C.LAB[p]: [k for k in ("NoFlag", "NoFlag_pool", "Floor", "HK1c") if not st["Mstar"]["pops"][p][k]]
                          + (["FamFlag"] if st["Mstar"]["pops"][p]["FamFlag"] else []) for p in C.POPS}
    v["formB_v07d_ub"] = fm["B_v07d_flags_only"]["ub"]
    v["formC_ub"] = fm["C"]["ub"]
    return v


def key_verdict(v):
    return (v["valid_Mstar"], tuple(v["not_shown_v07d"]), v["formA"], v["formB_v07d"], v["formC"])


# ------------------------------------------------------------------ Q1
def q1():
    out = {"by_tracker_arm_pop": {}, "bands": {}}
    rows = []
    for path in sorted(glob.glob(os.path.join(C.OUT, "rho_ckpt", "rho_*.json"))):
        r = load(path)
        for lab, p in r["pops"].items():
            out["by_tracker_arm_pop"]["%s|%s|%s" % (r["tracker"], r["arm"], lab)] = {
                k: p[k] for k in ("cells_used", "anova_pooled", "anova_pooled_ci95", "bb_pooled", "bb_pooled_ci95", "bb_boot_B",
                                  "anova_cell_median", "anova_cell_iqr", "bb_cell_median", "implied_cell_median", "implied_cell_iqr",
                                  "implied_cell_max")}
            for nm, c in p["cells"].items():
                if c["used_for_pooling"]:
                    rows.append((r["tracker"], r["arm"], lab, nm, c["E"], c["anova_rho"], c["bb_rho"], c["implied_rho"]))
    for lo, hi in ((0.0, 0.03), (0.03, 0.08), (0.08, 0.30), (0.30, 1.01), (0.10, 0.20)):
        sel = [x for x in rows if x[4] is not None and lo <= x[4] < hi]
        f = lambda i: [y[i] for y in sel if y[i] is not None]  # noqa: E731
        out["bands"]["E in [%.2f, %.2f)" % (lo, hi)] = {
            "cells": len(sel), "anova_median": float(np.median(f(5))) if f(5) else None, "anova_q90": float(np.quantile(f(5), 0.9)) if f(5) else None,
            "bb_median": float(np.median(f(6))) if f(6) else None, "bb_q90": float(np.quantile(f(6), 0.9)) if f(6) else None,
            "implied_median": float(np.median(f(7))) if f(7) else None, "implied_q90": float(np.quantile(f(7), 0.9)) if f(7) else None,
            "implied_max": float(np.max(f(7))) if f(7) else None}
    out["n_cells"] = len(rows)
    return out


def q1_moment(devs):
    """The unweighted moment estimator of the beta-binomial rho, the quantity the power rule's estimate depends on: under the
    model, sum_s E(r_s - mu)^2 = mu (1 - mu) (rho S + (1 - rho) H), H = sum_s 1 / n_s, so
    rho = (sum_s (r_s - rbar)^2 * S / (S - 1) / (rbar (1 - rbar)) - H) / (S - H), scenes treated as independent (AV2: a log is a
    scene). Pooled over the used cells as a ratio of sums. CI: log-cluster bootstrap with c1crit_rho_v01's weights
    ([20261205, i, 1], B = 1000). Also the log design effect: the K8 log-bootstrap variance of each cell estimate over the
    scene-i.i.d. variance (sample variance / S), median over the used cells."""
    out = {}
    for tag in C.TAGS:
        dev = devs[tag]
        rng = np.random.default_rng([20261205, dev.i, 1])
        Wl = rng.multinomial(dev.n_logs, np.full(dev.n_logs, 1.0 / dev.n_logs), size=1000).astype(float)
        Wb = np.vstack([np.ones((1, len(dev.scenes))), Wl[:, dev.log_idx]])
        Wk8 = dev.weights()[0]
        for a in C.ARMS:
            for p in C.POPS:
                N, X = dev.T(a)[p]
                ev = A.evaluable(N, dev.scenes, dev.log_idx)
                use = ev & (X.sum(0) > 0) & (X.sum(0) < N.sum(0))
                pres = (N > 0).astype(float)
                r = np.divide(X, N, out=np.zeros_like(X), where=N > 0)
                invn = np.divide(pres, N, out=np.zeros_like(X), where=N > 0)
                S = Wb @ pres
                with np.errstate(invalid="ignore", divide="ignore"):
                    m = (Wb @ r) / S
                    ss = (Wb @ (r * r)) - S * m * m
                    num = ss * S / (S - 1) / (m * (1 - m)) - (Wb @ invn)
                    den = S - (Wb @ invn)
                    rho_c = num / den
                cols = np.flatnonzero(use)
                pooled = num[:, cols].sum(1) / den[:, cols].sum(1) if len(cols) else np.full(len(Wb), np.nan)
                one = np.ones((1, len(dev.scenes)))
                boot = A.rates(N, X, Wk8)
                vlog = np.nanvar(boot, axis=0, ddof=1)
                with np.errstate(invalid="ignore", divide="ignore"):
                    viid = (ss[0] / (S[0] - 1)) / S[0]
                    deff = vlog / viid
                cells = {C.CELL_NAMES[j]: {"E": float(m[0, j]), "moment_rho": float(rho_c[0, j]),
                                           "moment_rho_ci95": [float(x) for x in np.nanquantile(rho_c[1:, j], [0.025, 0.975])],
                                           "log_design_effect": float(deff[j])} for j in cols}
                out["%s|%s|%s" % (tag, a, C.LAB[p])] = {
                    "cells_used": int(len(cols)),
                    "moment_pooled": float(pooled[0]) if len(cols) else None,
                    "moment_pooled_ci95": [float(x) for x in np.nanquantile(pooled[1:], [0.025, 0.975])] if len(cols) else None,
                    "moment_cell_median": float(np.median(rho_c[0, cols])) if len(cols) else None,
                    "moment_cell_q90": float(np.quantile(rho_c[0, cols], 0.9)) if len(cols) else None,
                    "moment_cell_max": float(np.max(rho_c[0, cols])) if len(cols) else None,
                    "log_design_effect_median": float(np.median(deff[cols])) if len(cols) else None,
                    "cells": cells}
    rows = [(v["E"], v["moment_rho"]) for k, d in out.items() for v in d["cells"].values()]
    bands = {}
    for lo, hi in ((0.0, 0.03), (0.03, 0.08), (0.08, 0.30), (0.30, 1.01), (0.10, 0.20)):
        vv = [x[1] for x in rows if lo <= x[0] < hi and np.isfinite(x[1])]
        bands["E in [%.2f, %.2f)" % (lo, hi)] = {"cells": len(vv), "median": float(np.median(vv)) if vv else None,
                                                  "q75": float(np.quantile(vv, 0.75)) if vv else None,
                                                  "q90": float(np.quantile(vv, 0.9)) if vv else None, "max": float(np.max(vv)) if vv else None}
    return {"by_tracker_arm_pop": out, "bands": bands}


# ------------------------------------------------------------------ Q2
def q2(devs, Ws):
    out = {"mc_se_at_0.80_200": SE80, "band_2se": [0.8 - 2 * SE80, 0.8 + 2 * SE80], "trackers": {}}
    for tag in C.TAGS:
        base = os.path.join(C.OUT, "mc_ckpt", "mc_%s_%%s.json" % tag)
        if not os.path.exists(base % "P200"):
            continue
        P = {k: load(base % k) for k in ("P200", "P1000", "P2000") if os.path.exists(base % k)}
        t = {"near_080_at_200": {}, "status_changes": {}, "family_sizes": {}, "floors": {}, "verdicts": {}}
        p200 = P["P200"]["hk1"]
        for a in C.ARMS:
            for lab in ("PD7", "SD1_7", "PD"):
                pw = p200[a]["pops"][lab]["power"] or {}
                near = {c: v for c, v in pw.items() if abs(v - 0.8) <= 2 * SE80}
                if near:
                    t["near_080_at_200"]["%s|%s" % (a, lab)] = near
                t["family_sizes"]["%s|%s" % (a, lab)] = {k: P[k]["hk1"][a]["pops"][lab]["family_size"] for k in P}
                for k in P:
                    if k == "P200":
                        continue
                    pk = P[k]["hk1"][a]["pops"][lab]["power"] or {}
                    ch = [c for c in pw if (pw[c] >= 0.8) != (pk.get(c, 0) >= 0.8)]
                    if ch:
                        t["status_changes"].setdefault(k, {})["%s|%s" % (a, lab)] = {c: [pw[c], pk.get(c)] for c in ch}
        t["n_near_080_at_200"] = sum(len(v) for v in t["near_080_at_200"].values())
        t["n_near_080_at_200_Mstar"] = sum(len(v) for k, v in t["near_080_at_200"].items() if k.startswith("Mstar|"))
        t["n_status_changes"] = {k: sum(len(v) for v in d.values()) for k, d in t["status_changes"].items()}
        for k in P:
            t["verdicts"][k] = verdict(devs[tag], Ws[tag], P[k]["hk1"])
        # alternative power seeds
        ps = {}
        for s in range(1, 6):
            f = base % ("PS%d" % s)
            if os.path.exists(f):
                r = load(f)
                ps["PS%d" % s] = {"verdict": verdict(devs[tag], Ws[tag], r["hk1"]),
                                  "family_sizes": {"%s|%s" % (a, lab): r["hk1"][a]["pops"][lab]["family_size"]
                                                   for a in C.ARMS for lab in ("PD7", "SD1_7", "PD")}}
        t["power_seed_sets"] = ps
        if ps:
            fam_range = {}
            for kk in ps["PS1"]["family_sizes"]:
                vals = [P["P200"]["hk1"][kk.split("|")[0]]["pops"][kk.split("|")[1]]["family_size"]] + [ps[s]["family_sizes"][kk] for s in ps]
                fam_range[kk] = [min(vals), max(vals)]
            t["power_seed_family_range"] = fam_range
            t["power_seed_verdict_changes"] = [s for s in ps if key_verdict(ps[s]["verdict"]) != key_verdict(t["verdicts"]["P200"])]
        # bootstrap seed sets
        bs = {}
        q0 = P["P200"].get("q_mc", {})
        for s in range(1, 6):
            f = base % ("BS%d" % s)
            if not os.path.exists(f):
                continue
            r = load(f)
            item = {}
            for reading in ("full", "fixed_fams"):
                hk = r[reading]["hk1"]
                ch, fch = [], []
                for a in C.ARMS:
                    for lab in ("PD7", "SD1_7", "PD"):
                        b0, b1 = set(p200[a]["pops"][lab]["flagged"]), set(hk[a]["pops"][lab]["flagged"])
                        if b0 != b1:
                            ch.append({"arm": a, "pop": lab, "only_base": sorted(b0 - b1), "only_alt": sorted(b1 - b0)})
                        f0, f1 = set(p200[a]["pops"][lab]["family_flagged"]), set(hk[a]["pops"][lab]["family_flagged"])
                        if f0 != f1 or p200[a]["pops"][lab]["family_size"] != hk[a]["pops"][lab]["family_size"]:
                            fch.append({"arm": a, "pop": lab, "family_size": [p200[a]["pops"][lab]["family_size"], hk[a]["pops"][lab]["family_size"]],
                                        "fam_flag_only_base": sorted(f0 - f1), "fam_flag_only_alt": sorted(f1 - f0)})
                vv = verdict(devs[tag], Ws[tag], hk)
                item[reading] = {"cell_flag_changes": ch, "n_cell_flag_changes": sum(len(x["only_base"]) + len(x["only_alt"]) for x in ch),
                                 "family_changes": fch, "verdict": vv,
                                 "verdict_changed": key_verdict(vv) != key_verdict(t["verdicts"]["P200"])}
            item["q"] = {a: {lab: (r["q_mc"][a][lab]["cells"] or {}).get("q") for lab in ("PD7", "SD1_7", "PD")} for a in C.ARMS}
            bs["BS%d" % s] = item
        t["boot_seed_sets"] = bs
        if bs:
            qsd = {}
            for a in C.ARMS:
                for lab in ("PD7", "SD1_7", "PD"):
                    vals = [(q0[a][lab]["cells"] or {}).get("q")] + [bs[s]["q"][a][lab] for s in bs]
                    vals = [x for x in vals if x is not None]
                    if len(vals) > 1:
                        qsd["%s|%s" % (a, lab)] = {"q_base": vals[0], "sd_over_seed_sets": float(np.std(vals, ddof=1)),
                                                   "range": [min(vals), max(vals)],
                                                   "q_mc_se_resampling": (q0[a][lab]["cells"] or {}).get("q_mc_se")}
            t["q_spread"] = qsd
        t["near_q_cells_base"] = {"%s|%s" % (a, lab): [x for x in ((q0[a][lab].get("cells") or {}).get("near_cells") or [])]
                                  + [dict(x, family=True) for x in ((q0[a][lab].get("family") or {}).get("near_cells") or [])]
                                  for a in C.ARMS for lab in ("PD7", "SD1_7", "PD") if q0}
        t["near_q_cells_base"] = {k: v for k, v in t["near_q_cells_base"].items() if v}
        out["trackers"][tag] = t
    return out


# ------------------------------------------------------------------ Q3
def q3():
    out = {"trackers": {}}
    allrows = []
    for path in sorted(glob.glob(os.path.join(C.OUT, "cover_ckpt", "cover_*.json"))):
        r = load(path)
        for i, m in enumerate(r["cells"]):
            allrows.append(dict(m, tracker=r["tracker"], n=r["n"], **{k: r["coverage"][k][i] for k in r["coverage"]},
                                zero_se=r["zero_se_share"][i]))
    if not allrows:
        return out
    ns = sorted({x["n"] for x in allrows})
    summ = {}
    for n in ns:
        sel = [x for x in allrows if x["n"] == n]
        d = {"cells": len(sel)}
        for k in ("lb_pct", "ub_pct", "lb_coded", "ub_coded"):
            v = np.array([x[k] for x in sel])
            d[k] = {"mean": float(v.mean()), "p10": float(np.quantile(v, 0.1)), "min": float(v.min()),
                    "share_below_0.93": float(np.mean(v < 0.93)), "share_below_0.94": float(np.mean(v < 0.94))}
            for lo, hi in ((0.0, 0.03), (0.03, 0.08), (0.08, 1.01)):
                vv = np.array([x[k] for x in sel if lo <= x["truth"] < hi])
                if len(vv):
                    d[k]["mean_truth_%.2f_%.2f" % (lo, hi)] = float(vv.mean())
            vv = np.array([x[k] for x in sel if 0.02 <= x["truth"] < 0.10])
            if len(vv):
                d[k]["mean_truth_0.02_0.10_near_delta"] = float(vv.mean())
        d["zero_se_mean"] = float(np.mean([x["zero_se"] for x in sel]))
        summ[n] = d
    out["by_n"] = summ
    first = {}
    for k in ("lb_pct", "ub_pct", "lb_coded", "ub_coded"):
        for thr in (0.93, 0.94):
            ok = [n for n in ns if summ[n][k]["mean"] >= thr]
            first["%s_mean_ge_%.2f" % (k, thr)] = min(ok) if ok else None
            ok = [n for n in ns if summ[n][k].get("mean_truth_0.02_0.10_near_delta", 0) >= thr]
            first["%s_near_delta_mean_ge_%.2f" % (k, thr)] = min(ok) if ok else None
            ok = [n for n in ns if summ[n][k]["p10"] >= thr]
            first["%s_p10_ge_%.2f" % (k, thr)] = min(ok) if ok else None
    out["smallest_n"] = first
    out["n_cells_per_n"] = {n: summ[n]["cells"] for n in ns}
    return out


def q3b():
    """c1crit_cover2_v01: pooled cells and the per-cell coverage of bounds at the Sidak level of 32 cells."""
    out = {}
    for path in sorted(glob.glob(os.path.join(C.OUT, "cover2_ckpt", "cover2_*.json"))):
        r = load(path)
        t = np.array([c["truth"] for c in r["cells"]])
        d = {"cells": len(t), "level": r["level"]}
        for k in ("lb_pct", "ub_pct", "lb_coded", "ub_coded"):
            v = np.array(r["coverage"][k])
            d[k] = {"mean": float(v.mean()), "min": float(v.min()), "p10": float(np.quantile(v, 0.1))}
            m = (t >= 0.02) & (t < 0.10)
            if m.any():
                d[k]["mean_truth_0.02_0.10_near_delta"] = float(v[m].mean())
                d[k]["min_truth_0.02_0.10_near_delta"] = float(v[m].min())
        out["%s|%s|n%d" % (r["part"], r["tracker"], r["n"])] = d
    return out


# ------------------------------------------------------------------ Q4
def q4(devs, Ws, rho_extra):
    out = {"trackers": {}}
    for tag in C.TAGS:
        files = sorted(glob.glob(os.path.join(C.OUT, "sweep_ckpt", "sweep_%s_*.json" % tag)))
        if not files:
            continue
        S = {}
        held = set()
        for f in files:
            r = load(f)
            S[(round(r["rho"], 4), round(r["P"], 4))] = r["hk1"]
            held |= {a for a in C.ARMS if a not in r.get("power_arms", C.ARMS)}
        # c1crit_sweep_v01 holds the family of the arms outside POWER_ARMS at the baseline: their ShownAbove must come from a
        # cell flag in the all-evaluable family (independent of rho and P), on every setting
        held_ok = all(any(hk[a]["pops"][lab]["flagged"] for lab in ("PD7", "SD1_7", "PD")) for hk in S.values() for a in held)
        base = verdict(devs[tag], Ws[tag], S[(0.5, 0.15)])
        t = {"baseline": base, "oat": {}, "grid": {}, "flips": [], "arms_with_family_held_at_baseline": sorted(held),
             "held_arms_shown_by_cell_flag_everywhere": bool(held_ok)}

        def rec(label, v):
            t["oat"][label] = v
            if key_verdict(v) != key_verdict(base):
                t["flips"].append(label)
        for (rho, P) in sorted(S):
            if P == 0.15:
                rec("rho=%.4f" % rho, verdict(devs[tag], Ws[tag], S[(rho, P)]))
            if rho == 0.5:
                rec("P=%.3f" % P, verdict(devs[tag], Ws[tag], S[(rho, P)]))
        for fm in (4, 5, 6, 7, 8):
            rec("F_MIN=%d" % fm, verdict(devs[tag], Ws[tag], S[(0.5, 0.15)], f_min=fm))
        for m in (0.02, 0.03, 0.05):
            rec("HK1c=%.2f" % m, verdict(devs[tag], Ws[tag], S[(0.5, 0.15)], hk1c=m))
        for c in (0.02, 0.03, 0.05):
            rec("c=%.2f" % c, verdict(devs[tag], Ws[tag], S[(0.5, 0.15)], c=c))
        for (rho, P) in sorted(S):
            for fm in (4, 5, 6, 7, 8):
                v = verdict(devs[tag], Ws[tag], S[(rho, P)], f_min=fm)
                t["grid"]["rho=%.4f|P=%.3f|F_MIN=%d" % (rho, P, fm)] = {
                    "valid_Mstar": v["valid_Mstar"], "not_shown_v07d": v["not_shown_v07d"], "formA": v["formA"], "formB_v07d": v["formB_v07d"],
                    "formC": v["formC"], "Mstar_family_sizes": v["family_sizes_Mstar"], "Mstar_failing": v["Mstar_failing"],
                    "flip": key_verdict(v) != key_verdict(base)}
        t["grid_flips"] = [k for k, v in t["grid"].items() if v["flip"]]
        # comparator rules: does v07d (flags only) differ from v07c (flags or HK1c) or from K8's valid-only, anywhere?
        diffs = []
        for lab, v in list(t["oat"].items()) + [("baseline", base)]:
            if v["not_shown_v07d"] != v["not_shown_v07c"] or v["formB_v07d"] != v["formB_v07c"]:
                diffs.append({"setting": lab, "v07d": v["not_shown_v07d"], "v07c": v["not_shown_v07c"],
                              "formB_v07d": v["formB_v07d"], "formB_v07c": v["formB_v07c"]})
        t["rule_v07d_vs_v07c_differences"] = diffs
        t["rule_v07d_vs_k8_differences"] = [
            {"setting": lab, "v07d": v["not_shown_v07d"], "k8": v["valid_k8"], "formB_v07d": v["formB_v07d"], "formB_k8": v["formB_k8"]}
            for lab, v in list(t["oat"].items()) + [("baseline", base)]
            if v["not_shown_v07d"] != v["valid_k8"] or v["formB_v07d"] != v["formB_k8"]]
        out["trackers"][tag] = t
    out["rho_extra_given"] = rho_extra
    return out


def h3_49c():
    """D16 v28 Choice 49(c) on the development joint loss: which comparators fail only the pooled bound (ub > delta + 0.03) while
    not flagged and evaluable in every population, and whether V^J changes."""
    if not os.path.exists(JOINT):
        return None
    J = load(JOINT)
    out = {"source": JOINT, "sha256": C.sha(JOINT), "trackers": {}}
    for tag in C.TAGS:
        vb = J["decide"][tag]["joint_loss"]["validity_by_arm"]
        st = {a: C.CA2.joint_status(v) for a, v in vb.items()}
        hk_only = [a for a, s in st.items() if not s["validJ"] and all(r.get("E") is not None and r.get("evaluable") and not r.get("flagged")
                                                                         for r in s["pops"].values())]
        comps = [c for c in C.CA2.KJ_SET if c in st]
        out["trackers"][tag] = {"VJ_old_validJ": [c for c in comps if st[c]["validJ"]],
                                "VJ_new_49c": [c for c in comps if st[c]["validJ"] or c in hk_only],
                                "hk1c_only_comparators": [c for c in hk_only if c in comps],
                                "per_arm_pops": {a: {p: {k: r.get(k) for k in ("E", "lb", "ub", "flagged", "validJ")} for p, r in s["pops"].items()}
                                                 for a, s in st.items()}}
    return out


# ------------------------------------------------------------------ Q5
def q5(devs, J):
    out = {"trackers": {}}
    for tag in C.TAGS:
        dev = devs[tag]
        d = J["decide"][tag]["validity_by_arm"]
        one = np.ones((1, len(dev.scenes)))
        t = {}
        for a in C.ARMS:
            for p in C.POPS:
                N, X = dev.T(a)[p]
                est = A.rates(N, X, one)[0]
                ev = A.evaluable(N, dev.scenes, dev.log_idx)
                fl = d[a]["pops"][p]["flagged"]
                e_ev = est[ev]
                e_fl = np.array([est[C.CELL_NAMES.index(c)] for c in fl])
                t["%s|%s" % (a, C.LAB[p])] = {
                    "evaluable": int(ev.sum()), "flagged": len(fl),
                    "E_evaluable_median": float(np.median(e_ev)) if len(e_ev) else None,
                    "E_evaluable_quartiles": [float(x) for x in np.quantile(e_ev, [0.25, 0.75])] if len(e_ev) else None,
                    "E_evaluable_max": float(e_ev.max()) if len(e_ev) else None,
                    "share_evaluable_above_delta": float(np.mean(e_ev > C.DELTA)) if len(e_ev) else None,
                    "E_above_delta_median": float(np.median(e_ev[e_ev > C.DELTA])) if np.any(e_ev > C.DELTA) else None,
                    "E_flagged_median": float(np.median(e_fl)) if len(e_fl) else None,
                    "E_flagged_quartiles": [float(x) for x in np.quantile(e_fl, [0.25, 0.75])] if len(e_fl) else None,
                    "E_flagged_min": float(e_fl.min()) if len(e_fl) else None, "E_flagged_max": float(e_fl.max()) if len(e_fl) else None,
                    "E_flagged": {c: float(est[C.CELL_NAMES.index(c)]) for c in fl},
                    "pooled_E": (d[a]["pops"][p]["pooled"] or {}).get("E")}
        out["trackers"][tag] = t
    # pooled over trackers and populations for B4 and B6 (cells counted once per tracker x population)
    for grp, arms in (("B4_B6", ("B4", "B6")), ("all_shown_above", ("B0", "B1", "B4", "B6", "B9", "RETUNED"))):
        vals, vals_ev = [], []
        for tag in C.TAGS:
            for a in arms:
                for lab in ("PD7", "SD1_7", "PD"):
                    r = out["trackers"][tag].get("%s|%s" % (a, lab))
                    if r is None:
                        continue
                    vals += list(r["E_flagged"].values())
        out[grp] = {"flagged_cells": len(vals), "E_flagged_median": float(np.median(vals)) if vals else None,
                    "E_flagged_quartiles": [float(x) for x in np.quantile(vals, [0.1, 0.25, 0.75, 0.9])] if vals else None}
        pd7 = [v for tag in C.TAGS for a in arms for v in out["trackers"][tag]["%s|PD7" % a]["E_flagged"].values()]
        out[grp]["PD7_only_flagged_cells"] = len(pd7)
        out[grp]["PD7_only_E_flagged_median"] = float(np.median(pd7)) if pd7 else None
    return out


# ------------------------------------------------------------------ the lead's items (C1_CRITERIA_EVIDENCE_REVIEW_v01 section 6)
MOVING_CAR = [c for c in C.CELL_NAMES if c.startswith("car|") and not c.endswith("|static")]


def item1_bbcheck():
    path = os.path.join(C.OUT, "bbcheck_v01.json")
    if not os.path.exists(path):
        return None
    b = load(path)
    return {t: {k: {kk: v[kk] for kk in v if kk != "cells"} for k, v in d.items()} for t, d in b["trackers"].items()}


def item34_power2():
    ck = os.path.join(C.OUT, "power2_ckpt")
    out = {"check": {}, "weights": {}, "grid": {}, "coverage_topk": {}, "family_contents": {}}
    for path in sorted(glob.glob(os.path.join(ck, "*.json"))):
        name = os.path.basename(path)[:-5]
        if name.startswith("meta_"):
            continue
        r = load(path)
        key = "%s|%s|%s|rho%.2f|P%.3f|reps%d|w%d" % (r["tracker"], r["pop"], r["planting"], r["rho"], r["P"], r["reps"], r["weights"])
        if r["part"] == "CHK":
            out["check"][key] = {k: r[k] for k in ("max_abs_diff", "mean_diff", "mc_se_diff_at_0.5")}
        elif r["part"] == "W":
            out["weights"][key] = {"family_size": r["family_size"], "record_share": r["record_share"],
                                   "equals_mc_P2000": r.get("equals_mc_P2000")}
        else:
            out["grid"][key] = {"family_size": r["family_size"], "record_share": r["record_share"],
                                "floor_6_met": (r["family_size"] >= 6) if r["pop"] in ("PD7", "SD1_7") else None,
                                "moving_car_cells_in_family": [c for c in MOVING_CAR if c in r["family"]]}
    # item 4: the k most powerful cells' record share, k = 5..20, at the rule's settings (W, 2000 datasets, 500 weights)
    for tag in C.TAGS:
        mpath = os.path.join(ck, "meta_%s.json" % tag)
        if not os.path.exists(mpath):
            continue
        meta = load(mpath)
        for lab in ("PD7", "SD1_7", "PD"):
            f = os.path.join(ck, "W_%s_%s_all_rho0.5000_p0.1500_r2000_w500.json" % (tag, lab))
            if not os.path.exists(f):
                continue
            r = load(f)
            rec = meta[lab]["records_by_cell"]
            tot = meta[lab]["records_total"]
            order = sorted(r["power"], key=lambda c: (-r["power"][c], -rec[c]))
            byrec = sorted(meta[lab]["evaluable"], key=lambda c: -rec[c])
            out["coverage_topk"]["%s|%s" % (tag, lab)] = {
                "k_most_powerful": {k: float(sum(rec[c] for c in order[:k]) / tot) for k in range(5, 21)},
                "k_most_records": {k: float(sum(rec[c] for c in byrec[:k]) / tot) for k in range(5, 21)},
                "actual_family_size": r["family_size"], "actual_family_share": r["record_share"],
                "moving_car_record_share": float(sum(rec[c] for c in MOVING_CAR) / tot),
                "moving_car_in_family": [c for c in MOVING_CAR if c in r["family"]],
                "moving_car_power": {c: r["power"].get(c) for c in MOVING_CAR},
                "scenes_power": {c: [meta[lab]["scenes_by_cell"][c], r["power"][c]] for c in r["power"]},
                "min_scenes_power_qualified": min([meta[lab]["scenes_by_cell"][c] for c in r["family"]], default=None),
                "max_scenes_not_qualified": max([meta[lab]["scenes_by_cell"][c] for c in r["power"] if c not in r["family"]], default=None)}
    return out


def item5_size():
    out = {}
    for path in sorted(glob.glob(os.path.join(C.OUT, "size_ckpt", "size_*.json"))):
        r = load(path)
        key = "%s%s" % (r["variant"], "" if r["rho"] is None else "_rho%.2f" % r["rho"])
        out.setdefault(key, {})[r["G"]] = {"familywise": r["familywise_size"], "per_cell": r["per_cell_flag_rate"]}
    smallest = {}
    for key, d in out.items():
        for K in ("1", "32"):
            ok = [G for G in sorted(d) if 0.025 <= float(d[G]["familywise"].get(K, d[G]["familywise"].get(int(K), -1))) <= 0.075]
            smallest["%s|K=%s" % (key, K)] = min(ok) if ok else None
    return {"by_variant": out, "smallest_G_in_bradley_band": smallest}


def item6_removal():
    out = {}
    for path in sorted(glob.glob(os.path.join(C.OUT, "removal_ckpt", "removal_*.json"))):
        r = load(path)
        out["%s|%s|rho%.2f" % (r["tracker"], r["arm"], r["rho"])] = {
            "P_removed_rule": r["rule_0.95_each"]["P_removed"], "P_removed_familywise9": r["familywise_bonferroni_9"]["P_removed"],
            "by_condition_rule": r["rule_0.95_each"]["P_by_condition"], "family_sizes": r["family_sizes"], "evaluable": r["evaluable"],
            "reps": r["reps"]}
    return out


def item7_oc375():
    out = {}
    for path in sorted(glob.glob(os.path.join(C.OUT, "oc375_ckpt", "oc375_*.json"))):
        r = load(path)
        out[r["variant"]] = {"P_H1": r["P_H1"], "P_H1_fails": r["P_H1_fails"], "P_H1_without_floors": r["P_H1_without_floors_diagnostic"],
                             "reps": r["reps"], "rule": r["rule"], "rho_analytic": r["power_rho_analytic"], "caps": r.get("caps"),
                             "trackers": {t: {k: r[t][k] for k in ("P_formB", "P_Mstar_failure_reason", "Mstar_family_size_median",
                                                                   "Mstar_family_size_p10", "P_in_V_choice9", "P_shown_invalid",
                                                                   "P_formB_fails_only_on_B6", "P_formC")} for t in C.TAGS}}
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rho-extra", default="")
    a = ap.parse_args(argv)
    J = C.load_analysis()
    devs = {t: C.Dev(t) for t in C.TAGS}
    Ws = {t: devs[t].weights()[0] for t in C.TAGS}
    res = {"stamp": "c1crit_summary_v01: nuScenes development data only (K8 Linux replicate)",
           "Q1_rho": q1(), "Q1_rho_moment": q1_moment(devs), "Q2_mc": q2(devs, Ws), "Q3_coverage": q3(), "Q3b_coverage_pooled_and_simultaneous": q3b(),"Q4_sweep": q4(devs, Ws, a.rho_extra),
           "Q4_h3_choice49c": h3_49c(), "Q5_effect": q5(devs, J),
           "lead_item1_bbcheck": item1_bbcheck(), "lead_items3_4_power": item34_power2(), "lead_item5_size": item5_size(),
           "lead_item6_removal": item6_removal(), "lead_item7_oc375": item7_oc375()}
    C.jdump(os.path.join(C.OUT, "c1crit_summary_v01.json"), res)
    print("SUMMARY WRITTEN")


if __name__ == "__main__":
    main()
