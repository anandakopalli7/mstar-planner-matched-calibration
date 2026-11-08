#!/usr/bin/env python3
"""X3 screen (x3-core agent, x3_screen_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan sections 0, 1 (V1), 2(a), 2(b).

The screen is the registered screen as coded and as installed for the analysis of record: c1_rules_v02.apply_analysis puts
hk1_rule_criteria in k8_analyse_v04's namespace (K.hk1_rule), and c1_analyse_v02.configure("c1") then c1_analyse_v10.configure_v09
set the evaluability floor (39 units, 8 logs) and STRICT_Q = False. Status = c1_analyse_v02.arm_status(K.hk1_rule(...)), the frozen
constants: delta 0.05, the power-qualified families (target-only rule, first 500 weight rows) and floors, HK1c's upper bound at
0.995 with margin 0.03. As of record, the flag level follows the arm's role in hk1_rule_criteria: a comparator of K (B0, B1, B3, B4,
B6, B9, RETUNED) is flagged at 1 - 0.0125/9 (its removal conditions), every other arm (M*, the sweep points, RETUNED-HK1, the joint
arms, Z0, and every X3 grid point or composite, whose labels are not in K) at 0.95, i.e. judged for validity like M*.
Bootstrap: the log-cluster bootstrap of k6_analyse_v02.keys_and_weights with B = 4000 (X3) from the given seed; the power rule
reads the first 500 rows, which do not depend on B.
Functions: tables per arm and population (k6_analyse_v02.episode_cell_table, the record's population masks), status per arm,
decisive quantities with Monte Carlo SE (for V1's distance to threshold), per-log infeasible rates (c1_analyse_v02.per_scene_rates),
paired differences (c1_analyse_v02.paired as installed: percentile log bootstrap), the cross-fitted matched-validity selection
(c1_analyse_v02.retuned_hk1's rule with an explicit grid order), and the partition screen of analysis (b).
Commands: v1 (gate V1 on the outputs of record), a (analysis a), b (analysis b). See main().
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import argparse  # noqa: E402
import json  # noqa: E402
import math  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402

import numpy as np  # noqa: E402

X3 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(X3))
for _d in ("c1_av2", "k8", "k6", "m"):
    sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", _d))
sys.path.insert(0, X3)
import k6_analyse_v02 as A  # noqa: E402
import k8_analyse_v04 as K  # noqa: E402
import k8_sim_v04 as S  # noqa: E402
import c1_analyse_v02 as B  # noqa: E402
import c1_rules_v02 as R  # noqa: E402
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

POPS = tuple(K.CONF_POPS)
CELLS = A.cell_family()
_SETUP = {}


def setup(route="within_lt3d"):
    """The rules as installed for the analysis of record (c1_analyse_v10 at import and in main), in this process only."""
    if not _SETUP:
        R.apply_analysis(B, types.SimpleNamespace())
        B.configure("c1")
        K.STRICT_Q = False
        _SETUP["masks"] = {p: A.mask(**K.POP_DECIDE[p]) for p in K.POP_DECIDE}
    R._CTX["route"] = route
    assert K.hk1_rule is R.hk1_rule_criteria and A.MIN_SCENES == 39 and A.MIN_LOGS == 8 and K.STRICT_Q is False
    return _SETUP["masks"]


def load_eps_counts(run_dir, tag):
    eps = [json.loads(l) for l in open(os.path.join(run_dir, "episodes_%s.jsonl" % tag))]
    counts = dict(np.load(os.path.join(run_dir, "counts_%s.npz" % tag)))
    return eps, counts


def entered(eps):
    return [o for o in eps if o["entered"] and o["scene"] not in K.DEV_SCENES and o["arm"] != "LOG"]


def keys_W(eps_f, B_, seed):
    """k6_analyse_v02.keys_and_weights (units are logs: log_of_scene is the identity), the generator's first use."""
    los = {o["scene"]: o["scene"] for o in eps_f}
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps_f, los, B_, np.random.default_rng(seed))
    W = W_logs[:, log_of_ep]
    scenes = sorted({o["scene"] for o in eps_f})
    lg = np.array([logs.index(sc) for sc in scenes])
    return {"keys": keys, "scene_of_ep": scene_of_ep, "logs": logs, "log_of_ep": log_of_ep, "W_logs": W_logs, "W": W,
            "Ws": W_logs[:, lg], "scenes": scenes}


def arm_tables(eps, counts, arms, keys, masks, pops=POPS):
    """{pop: {arm: (N, X)}} exactly as k6_analyse_v02.populations builds them (episode_cell_table), counts pre-split by arm."""
    kidx = {k: i for i, k in enumerate(keys)}
    out = {p: {} for p in pops}
    ep_all = counts["episode"]
    for arm in arms:
        epi = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps if o["arm"] == arm}
        sel = np.isin(ep_all, np.fromiter(epi.keys(), np.int64))
        sub = {k: v[sel] for k, v in counts.items() if isinstance(v, np.ndarray) and v.ndim == 1 and len(v) == len(ep_all)}
        for p in pops:
            out[p][arm] = A.episode_cell_table(sub, epi, len(keys), CELLS, masks[p])
    return out


def T_of(tabs, arm, rows=None):
    if rows is None:
        return {p: (tabs[p][arm][0], tabs[p][arm][1]) for p in POPS}
    return {p: (tabs[p][arm][0][rows], tabs[p][arm][1][rows]) for p in POPS}


def screen(T, kw, power_key, arm, rows=None, B_=None):
    """K.hk1_rule (hk1_rule_criteria) and c1_analyse_v02.arm_status; rows restricts the keys (training folds), B_ the weight rows."""
    W = kw["W"] if B_ is None else kw["W"][:B_]
    sc, lg = kw["scene_of_ep"], kw["log_of_ep"]
    if rows is not None:
        W, sc, lg = W[:, rows], sc[rows], lg[rows]
    v = K.hk1_rule(T, CELLS, sc, lg, W, list(power_key), arm=arm)
    return v, B.arm_status(v)


def removal_reasons(st):
    """c1_analyse_v10.comparator_reasons' first part: a comparator leaves V_t only through a flag (Choice 47e)."""
    rem = []
    for p, r in st["pops"].items():
        if not r["NoFlag"]:
            rem.append("%s cells" % p)
        if r["FamFlag"]:
            rem.append("%s family" % p)
        if r["pooled_evaluable"] and not r["NoFlag_pool"]:
            rem.append("%s pooled" % p)
    return rem


def _q_mcse(T, level):
    """Monte Carlo SE of the level-quantile of the sup-t draws T (order-statistic interval, Andrews-Buchinsky style)."""
    T = np.sort(T[np.isfinite(T)])
    n = len(T)
    if n < 10:
        return float("nan")
    s = 1.96 * math.sqrt(n * level * (1 - level))
    lo, hi = max(int(math.floor(n * level - s)), 0), min(int(math.ceil(n * level + s)), n - 1)
    return float((T[hi] - T[lo]) / (2 * 1.96))


def simul_detail(est, boot, fam, level, side):
    """m_lib_v04._simul's bound with its Monte Carlo SE: se (q-quantile MC error) and q (bootstrap-SE MC error) in quadrature."""
    e, b = est[fam], boot[:, fam]
    se = np.nanstd(b, axis=0, ddof=1)
    ok = se > 0
    sgn = 1.0 if side == "lower" else -1.0
    with np.errstate(invalid="ignore", divide="ignore"):
        dev = np.where(ok, sgn * (b - e) / np.where(ok, se, 1.0), np.nan)
        Tm = np.nanmax(dev, axis=1) if ok.any() else np.full(len(b), np.nan)
    q = float(np.nanquantile(Tm, level)) if np.isfinite(Tm).any() else float("nan")
    bound = np.where(ok, e - sgn * q * se, e)
    qse = _q_mcse(Tm, level)
    mcse = np.where(ok, np.sqrt((se * qse) ** 2 + (q * se / math.sqrt(2 * len(b))) ** 2), 0.0)
    return bound, se, q, ok, mcse


def decisive(T, kw, arm, v, rows=None, B_=None):
    """The decisive quantities of an arm's status (distance to threshold; positive = the condition fails), per population: the
    largest cell flag statistic (LB - delta at the arm's flag level), the largest family flag statistic, the pooled flag statistic,
    HK1c (UB at 0.995 - (delta + 0.03)), the floor (6 - family size, PD7 and SD1_7) and evaluability; each LB/UB with its MC SE."""
    W = kw["W"] if B_ is None else kw["W"][:B_]
    sc, lg = kw["scene_of_ep"], kw["log_of_ep"]
    if rows is not None:
        W, sc, lg = W[:, rows], sc[rows], lg[rows]
    lvl = R.flag_level(arm)
    one = np.ones((1, W.shape[1]))
    out = {"flag_level": lvl}
    for p in POPS:
        N, X = T[p]
        ev = A.evaluable(N, sc, lg)
        fam = np.flatnonzero(ev)
        est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
        r = {"evaluable": int(len(fam))}
        if len(fam):
            lb, se, q, ok, mc = simul_detail(est, boot, fam, lvl, "lower")
            stat = np.where(ok, lb - C.DELTA, est[fam] - C.DELTA)
            i = int(np.nanargmax(stat))
            r["cells_max"] = {"cell": CELLS[fam[i]][0], "stat": float(stat[i]), "mcse": float(mc[i]), "zero_se": bool(not ok[i]),
                              "all": {CELLS[j][0]: [float(stat[ii]), float(mc[ii])] for ii, j in enumerate(fam)}}
        fq = [CELLS.index(next(c for c in CELLS if c[0] == nm)) for nm in (v["pops"][p].get("family") or [])]
        if fq:
            fq = np.array(fq)
            lb, se, q, ok, mc = simul_detail(est, boot, fq, lvl, "lower")
            stat = np.where(ok, lb - C.DELTA, est[fq] - C.DELTA)
            i = int(np.nanargmax(stat))
            r["family_max"] = {"cell": CELLS[fq[i]][0], "stat": float(stat[i]), "mcse": float(mc[i]),
                               "all": {CELLS[j][0]: [float(stat[ii]), float(mc[ii])] for ii, j in enumerate(fq)}}
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        if A.evaluable(Np, sc, lg)[0]:
            e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
            lb, se, q, ok, mc = simul_detail(e1, b1, np.array([0]), lvl, "lower")
            ub, seu, qu, oku, mcu = simul_detail(e1, b1, np.array([0]), R.HK1C_LEVEL, "upper")
            r["pooled_flag"] = {"stat": float(lb[0] - C.DELTA) if ok[0] else float(e1[0] - C.DELTA), "mcse": float(mc[0])}
            r["hk1c"] = {"stat": float(ub[0] - (C.DELTA + R.HK1C_MARGIN)), "mcse": float(mcu[0])}
        r["family_size"] = v["pops"][p].get("family_size")
        out[p] = r
    return out


def infeasible_rates(eps_f, scenes, arm_of_scene=None):
    return B.per_scene_rates(eps_f, arm_of_scene, scenes)


def paired(rate, Ws, a, b):
    r = B.paired(rate, Ws, a, b, 0.95)
    r.pop("_bm", None)
    return {"mean_diff": r["mean_diff"], "ci95": r["ci95"], "ub_0.95": r["ub"], "p_lt0": r.get("p_lt0")}


def crossfit(tabs, order, fold_of_key, kw, power_key, code_of, B_sel=None):
    """c1_analyse_v02.retuned_hk1's rule with an explicit grid order (least to most conservative): for each held-out fold f, the
    first grid point Valid (arm_status) on the other folds' keys (weights restricted to them); else the most conservative point,
    flagged. Power keys: power_key + [200 + code(point), f] (the record's pattern). Returns the choice per fold, the composite's
    per-key tables and the training statuses."""
    choice, trace = {}, {}
    for f in sorted(set(fold_of_key.tolist())):
        tr = fold_of_key != f
        pick, tried, tr_st = None, 0, []
        for a in order:
            v, st = screen(T_of(tabs, a, tr), kw, list(power_key) + [200 + code_of[a], int(f)], a, rows=tr, B_=B_sel)
            tried += 1
            tr_st.append({"point": a, "valid": st["valid"], "shown_above": st["shown_above"],
                          "failing": {p: [k_ for k_ in ("NoFlag", "NoFlag_pool", "Floor", "HK1c") if not r_[k_]] + (["FamFlag"] if r_["FamFlag"] else [])
                                      for p, r_ in st["pops"].items()}})
            if st["valid"]:
                pick = a
                break
        choice[int(f)] = {"point": pick or order[-1], "none_qualifies": pick is None, "points_tried": tried}
        trace[int(f)] = tr_st
    arm_of_key = [choice[int(f)]["point"] for f in fold_of_key]
    Tc = {}
    for p in POPS:
        Tc[p] = (np.stack([tabs[p][a][0][i] for i, a in enumerate(arm_of_key)]), np.stack([tabs[p][a][1][i] for i, a in enumerate(arm_of_key)]))
    return choice, arm_of_key, Tc, trace


def status_summary(st):
    return {"valid": st["valid"], "shown_above": st["shown_above"], "floor_only": st["floor_only"],
            "pops": {p: {k: r[k] for k in ("NoFlag", "FamFlag", "pooled_evaluable", "NoFlag_pool", "Floor", "HK1c", "valid", "shown_above",
                                          "flagged_cells", "family_flagged", "family_size", "evaluable")} for p, r in st["pops"].items()}}


def pooled_numbers(v):
    return {p: {k: (v["pops"][p].get("pooled") or {}).get(k) for k in ("E", "lb", "ub", "flagged")} for p in POPS}


# ================================================================================================ V1
def gate_v1(tracker, B_=C.B_X3, recheck_retuned_hk1=True):
    masks = setup("within_lt3d")
    i = C.TRACKER_I[tracker]
    sb, sp = B.seeds(i, B.ROUTE_J["within_lt3d"])
    an = json.load(open(os.path.join(C.REC, "c1_analysis_r1.json")))
    rec_out = an["c1"]["within_lt3d"][tracker]
    rec_k8 = an["k8"]["within_lt3d"][tracker]
    del an
    assert rec_out["seeds"] == {"bootstrap": sb, "power": sp}, "the record's seeds differ from c1_analyse_v02.seeds"
    eps, counts = load_eps_counts(C.REC_RUNS, "%s_decide" % C.TAG_REC[tracker])
    eps_f = entered(eps)
    kw = keys_W(eps_f, B_, sb)
    aos = rec_k8["retune"]["arm_of_scene"]
    D0 = {"episode": np.zeros(0, np.int64)}
    eps_c, counts_c, _, _ = K.add_composite_arm(eps_f, counts, dict(D0), dict(D0), aos)
    arms = [a for a in K.ALL_ARMS if a != "LOG" and any(o["arm"] == a for o in eps_c)]
    t0 = time.time()
    tabs = arm_tables(eps_c, counts_c, arms, kw["keys"], masks)
    t_tab = time.time() - t0
    res, timings = {}, {}
    for a in arms:
        t1 = time.time()
        pk = list(sp) if a == "Mstar" else list(sp) + [100 + K.ARM_INDEX[a]]
        v, st = screen(T_of(tabs, a), kw, pk, a)
        timings[a] = round(time.time() - t1, 2)
        rs = rec_out["status"][a]
        mine = status_summary(st)
        agree = {"valid": mine["valid"] == rs["valid"], "shown_above": mine["shown_above"] == rs["shown_above"]}
        per = {}
        for p in POPS:
            for k_ in ("NoFlag", "FamFlag", "NoFlag_pool", "Floor", "HK1c", "family_size", "evaluable"):
                per["%s/%s" % (p, k_)] = mine["pops"][p][k_] == rs["pops"][p][k_]
            per["%s/flagged_cells" % p] = sorted(mine["pops"][p]["flagged_cells"]) == sorted(rs["pops"][p]["flagged_cells"])
            per["%s/family_flagged" % p] = sorted(mine["pops"][p]["family_flagged"]) == sorted(rs["pops"][p]["family_flagged"])
        agree["components"] = per
        agree["all_components"] = bool(all(per.values()))
        rem_mine = removal_reasons(st)
        rem_rec = removal_reasons(rs)
        entry = {"x3": mine, "x3_pooled": pooled_numbers(v), "record_pooled": {p: {k: ((rec_k8["validity_by_arm"][a]["pops"][p].get("pooled") or {}).get(k))
                                                                                  for k in ("E", "lb", "ub", "flagged")} for p in POPS},
                 "record": {"valid": rs["valid"], "shown_above": rs["shown_above"]}, "agree": agree,
                 "removal_x3": rem_mine, "removal_record": rem_rec, "removal_agree": bool(rem_mine) == bool(rem_rec),
                 "record_cells": {p: {"flagged_cells": list(rs["pops"][p]["flagged_cells"]), "family_flagged": list(rs["pops"][p]["family_flagged"])} for p in POPS},
                 "record_pops": {p: {k_: rs["pops"][p][k_] for k_ in ("NoFlag", "FamFlag", "NoFlag_pool", "Floor", "HK1c", "family_size", "evaluable")} for p in POPS},
                 "flag_level": R.flag_level(a), "power_key": pk}
        if not (agree["valid"] and agree["shown_above"] and agree["all_components"] and entry["removal_agree"]):
            entry["decisive"] = decisive(T_of(tabs, a), kw, a, v)
        res[a] = entry
        print("V1 %s %-12s valid %s/%s shown %s/%s comps %s  %.1f s" % (tracker, a, mine["valid"], rs["valid"], mine["shown_above"], rs["shown_above"],
                                                                     agree["all_components"], timings[a]), flush=True)
    # RETUNED-HK1 of record: the composite of the record's per-fold choice, screened at B = 4000; and the selection re-run
    sweep = [a for a in S.SWEEP_ARMS if a in arms]
    fits = json.load(open(C.FITS_REC[tracker]))
    fold_of_key = np.array([int(fits["fold_of_scene"][k[0]]) for k in kw["keys"]])
    del fits
    ch_rec = rec_out["RETUNED_HK1"]["choice_by_fold"]
    arm_of_key = [ch_rec[str(f)]["arm"] for f in fold_of_key]
    Tc = {p: (np.stack([tabs[p][a][0][ii] for ii, a in enumerate(arm_of_key)]), np.stack([tabs[p][a][1][ii] for ii, a in enumerate(arm_of_key)])) for p in POPS}
    v, st = screen(Tc, kw, list(sp) + [300], "RETUNED_HK1")
    rs = rec_out["RETUNED_HK1"]["status"]
    mine = status_summary(st)
    hk = {"x3": mine, "record": {"valid": rs["valid"], "shown_above": rs["shown_above"]},
          "agree": {"valid": mine["valid"] == rs["valid"], "shown_above": mine["shown_above"] == rs["shown_above"],
                    "all_components": all(mine["pops"][p][k_] == rs["pops"][p][k_] for p in POPS
                                          for k_ in ("NoFlag", "FamFlag", "NoFlag_pool", "Floor", "HK1c", "family_size", "evaluable"))}}
    if recheck_retuned_hk1:
        t1 = time.time()
        order = sorted(sweep, key=lambda a: (S.CURVE_ALPHA_OF_ARM[a], a))
        ch, _, _, trace = crossfit(tabs, order, fold_of_key, kw, sp, {a: K.ARM_INDEX[a] for a in order})
        hk["selection_rerun"] = {"choice_by_fold": ch, "record_choice_by_fold": {f: {"arm": c["arm"], "none_qualifies": c["none_qualifies"]} for f, c in ch_rec.items()},
                                 "agree": all(ch[int(f)]["point"] == c["arm"] for f, c in ch_rec.items()), "seconds": round(time.time() - t1, 1)}
    res["RETUNED_HK1"] = hk
    # infeasible rates: deterministic, must equal the record's
    rate = infeasible_rates(eps_f, kw["scenes"], aos)
    rate_eq = {a: abs(float(rate[a].mean()) - rec_out["infeasible_rate"][a]) < 1e-12 for a in rate if a in rec_out["infeasible_rate"]}
    return {"tracker": tracker, "B": B_, "seeds": {"bootstrap": sb, "power": sp}, "by_arm": res, "timings_s": timings, "tables_s": round(t_tab, 1),
            "infeasible_rate_equal_record": rate_eq}


# ================================================================================================ (b)
def partition_tables(eps_f, parts, arm, keys, pop_c4, part_index, nbins):
    """N, X (keys x cells) for one arm, population and partition; cell = bin * 2 + axis."""
    import x3_run_v01 as RR
    kidx = {k: i for i, k in enumerate(keys)}
    ep = {int(o["episode"]): kidx[(o["scene"], o["delay_kf"])] for o in eps_f if o["arm"] == arm}
    N = np.zeros((len(keys), nbins * 2))
    X = np.zeros((len(keys), nbins * 2))
    for row, e in enumerate(parts["episode"].tolist()):
        if e not in ep:
            continue
        acc = parts["acc"][row]
        for c4 in pop_c4:
            for b in range(nbins):
                for ax in (0, 1):
                    k_ = int(RR.pkey(c4, part_index, b, ax))
                    N[ep[e], b * 2 + ax] += acc[k_, 0]
                    X[ep[e], b * 2 + ax] += acc[k_, 1]
    return N, X


def partition_screen(N, X, kw, cell_names, level=0.95):
    one = np.ones((1, N.shape[0]))
    ev = A.evaluable(N, kw["scene_of_ep"], kw["log_of_ep"])
    fam = np.flatnonzero(ev)
    est, boot = A.rates(N, X, one)[0], A.rates(N, X, kw["W"])
    logs = (N > 0).sum(0)
    out = {"cells": {}, "evaluable": [cell_names[j] for j in fam], "flagged": [], "q": None}
    if len(fam):
        lb, ub, se, sig, q = A.flag(est, boot, fam, level)
        out["q"] = float(q) if np.isfinite(q) else None
        out["flagged"] = [cell_names[j] for i, j in enumerate(fam) if sig[i]]
        for i, j in enumerate(fam):
            out["cells"][cell_names[j]] = {"E": float(est[j]), "lb_sim": float(lb[i]), "ub_sim": float(ub[i]), "se": float(se[i]),
                                           "flagged": bool(sig[i]), "logs": int(logs[j]), "records": int(N[:, j].sum()),
                                           "exceed": int(X[:, j].sum()), "evaluable": True}
        k = int(np.nanargmax(est[fam]))
        out["largest"] = {"cell": cell_names[fam[k]], "E": float(est[fam[k]]), "ub_sim": float(ub[k]), "lb_sim": float(lb[k]),
                          "logs": int(logs[fam[k]])}
    for j in range(N.shape[1]):
        if j in set(fam.tolist()) or logs[j] == 0:
            continue
        b = boot[:, j]
        b = b[np.isfinite(b)]
        out["cells"][cell_names[j]] = {"E": float(est[j]) if np.isfinite(est[j]) else None, "logs": int(logs[j]), "records": int(N[:, j].sum()),
                                       "exceed": int(X[:, j].sum()), "evaluable": False,
                                       "marginal_95_one_sided": [float(np.quantile(b, 0.05)), float(np.quantile(b, 0.95))] if len(b) > 10 else None}
    return out


def _time_test():
    """Plan section 0: one hk1_rule call on the 375 logs at B = 4000 (B4 as a comparator, M*, a sweep point)."""
    masks = setup()
    sb, sp = B.seeds(0, 0)
    eps, counts = load_eps_counts(C.REC_RUNS, "t1_within_lt3d_decide")
    eps_f = entered(eps)
    kw = keys_W(eps_f, C.B_X3, sb)
    t0 = time.time()
    tabs = arm_tables(eps_f, counts, ["B4", "Mstar", "B0a8"], kw["keys"], masks)
    print("tables %.1f s" % (time.time() - t0))
    out = {}
    for arm, pk in (("B4", list(sp) + [100 + K.ARM_INDEX["B4"]]), ("Mstar", list(sp)), ("B0a8", list(sp) + [100 + K.ARM_INDEX["B0a8"]])):
        t0 = time.time()
        v, st = screen(T_of(tabs, arm), kw, pk, arm)
        out[arm] = round(time.time() - t0, 1)
        print(arm, st["valid"], st["shown_above"], "%.1f s" % out[arm], flush=True)
    C.jdump(os.path.join(C.OUT, "gates", "x3_hk1_timing_v01.json"), {"stamp": C.STAMP, "B": C.B_X3, "seconds_per_hk1_rule_call": out,
                                                                     "rule": "plan section 0: B = 2000 inside the selection only if one call takes > 60 s"})


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["v1", "time"])
    ap.add_argument("--trackers", nargs="+", default=["t1", "t3"])
    ap.add_argument("--out", required=False)
    ap.add_argument("--no-recheck", action="store_true")
    ap.add_argument("--recheck-trackers", nargs="*", default=["t1"],
                    help="trackers on which RETUNED-HK1's selection is re-run (105 training screens each: none qualifies in the record)")
    a = ap.parse_args(argv)
    if a.cmd == "time":
        with heavy_lock("x3-core: timing one hk1_rule call at B=4000"):
            _time_test()
        return
    C.assert_run_log("v1 start")
    t0 = time.time()
    out = {"stamp": C.STAMP, "gate": "V1", "rule": "plan section 1: agreement arm by arm; a disagreement is acceptable only for a decisive "
           "quantity within about 3 MC SE of its threshold", "by_tracker": {}, "recheck_trackers": a.recheck_trackers,
           "code_sha256": C.code_hashes([os.path.abspath(__file__), os.path.abspath(C.__file__), os.path.abspath(R.__file__),
                                         os.path.abspath(K.__file__), os.path.abspath(A.__file__), os.path.abspath(B.__file__)])}
    with heavy_lock("x3-core: V1 screen B=4000 on the outputs of record"):
        for t in a.trackers:
            out["by_tracker"][t] = gate_v1(t, recheck_retuned_hk1=(not a.no_recheck) and t in a.recheck_trackers)
            C.live("V1 screen", a.trackers.index(t) + 1, len(a.trackers))
            C.jdump(a.out + ".partial.json", out)
    out["seconds"] = round(time.time() - t0, 1)
    C.assert_run_log("v1 end")
    C.jdump(a.out, out)
    try:
        os.remove(a.out + ".partial.json")
    except FileNotFoundError:
        pass
    print("X3 V1 DONE")


if __name__ == "__main__":
    main()
