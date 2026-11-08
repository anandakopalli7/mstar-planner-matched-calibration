#!/usr/bin/env python3
"""C1 analysis (Claude line, c1_analyse_v01, 2 Nov 2026): the AV2 confirmation's hypotheses and labels, C1 v04 DRAFT (section 11
governs), D16 v08 Choices 6-23, D18 v02, ERRATA_K8 E8-E15.

Statistics: per route and tracker, k8_analyse_v04.analyse_decide (unchanged: K7's HK1 with R12b N1 and R15b N1, the power-qualified
families, log bootstrap B = 2000, the joint loss, RETUNED's cross-fitted selection, V2 variants, safety, A13, A14), seeded
[20261110, i, j] (bootstrap) and [20261111, i, j] (power), i = 0 T1 / 1 T3, j = route index (ROUTE_J). On top of it, as pure
functions of its outputs (each tested on planted cases in tests/test_c1_v01.py):
  arm_status    Valid(a,t) and ShownAbove(a,t) of C1 v04 section 5.4, per population (NoFlag, FamFlag, NoFlag_pool, Floor, HK1c).
                Wording: "not shown above delta (one-sided simultaneous test at 0.95)", never "at most delta" (E10).
  form_b        Form B with Choice 9 (E13): V_t = comparators of K = {B0, B1, B3, B4, B6, B9, RETUNED} NOT shown above delta, so a
                comparator failing only a floor stays in V_t, is logged (in_V_by_choice9) and counts in |V_t|; M* must be less often
                infeasible than each at 1 - 0.05/|V_t| (percentile log bootstrap of the per-log paired difference).
  form_a        descriptive (B0, B1, B4, B9 at 1 - 0.05/4).   form_c   UB^{0.95}(M* - B4) <= c_t, c read from the config (R16 m1).
  joint_b       H3: ValidJ (per population: pooled joint loss not flagged and its one-sided upper bound <= delta + 0.03) for M*Jx and
                every arm of K_J = {M*, B0, B1, B3, B4, B6, B9, RETUNED}; M*Jx less often infeasible than each valid one.
  h10_rule      M* against B6 (named ablation, E12): some PD7 cell flagged for B6, not for M*, with B6 - M* sup-t positive, AND
                UB^{0.95}(M* - B6) <= 0.03 (non-inferiority).
  h6/h7         method-stage rules on m_lib_v04 summaries (HM1, B4's HM2 failure, HM6), h8_rule (X2's FAILS rule on the 4 decision
                cells), h9_rule (no flag, pooled no flag, at least 6 power-qualified cells: Choice 23).
  holm          family S = {H2, H3, H4, H6b, H10}, tested by Holm at 0.05 only if H1 passes; otherwise every member is reported
                unadjusted as "supportive, not confirmatory (gate H1 not passed)". A claim's p-value is the maximum over trackers of
                its Bonferroni-adjusted rejection p-value; validity parts are pass/fail gates. Family P = {H8} at 0.05.
  descriptive   Form A; loop mode; RETUNED as E14 (fold choices, in-sample validity of every sweep point by Form B's rule, the
                cheapest valid point); source heterogeneity (M*'s pooled V1 on PD7, SD1_7, PD and its infeasible rate by source,
                with a log-bootstrap interval for the difference); seeds of every power family (R16 m5).
Routes and labels (ROUTE_LABEL): within_lt3d -> H1 (primary), H2, H3, H10; transfer_lt3d -> H4; voxelnext_val -> H5 (descriptive);
public_lt3d_val -> H1-P (descriptive); source_transfer -> descriptive.
Modes: --c1 (binds the frozen plan and the C1 run records), --standin (nuScenes stand-in records; never evidence), --reproduce
(any K8 decision-mode run directory: the K8 v03/v04 verdicts must be reproduced where the definitions coincide), --smoke (relaxed
evaluability, for the plumbing test only).
Usage: python -B c1_analyse_v01.py --config <json> --out <analysis json> --decision <decision json> --csv-dir <dir>
       (--c1 --plan <plan.md> | --standin | --reproduce | --smoke)
Config: {"routes": [{"name": "within_lt3d", "runs": dir, "tags": {"t1": "t1_within_lt3d", "t3": ...}, "fits": {"t1": f, "t3": f},
         "modes": ["decide", "loop"]}, ...], "units_are_logs": bool, "manifests": [...], "c": {"t1": 0.03, "t3": 0.03},
         "folds": path (source_of_log), "method_stage": {"t1": path, "t3": path} (optional), "h8": path, "h9": {...} (optional)}
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
import k8_analyse_v04 as K  # noqa: E402

A, M, S = K.A, K.M, K.S
DELTA = 0.05
POPS = K.CONF_POPS
FLOOR_POPS = K.FLOOR_POPS
F_MIN = 6
K_SET = ("B0", "B1", "B3", "B4", "B6", "B9", "RETUNED")
KJ_SET = ("Mstar",) + K_SET
FORM_A_SET = ("B0", "B1", "B4", "B9")
C_DEFAULT = {"t1": 0.03, "t3": 0.03}
NI_MARGIN = 0.03
SEED_BOOT, SEED_POWER = 20261110, 20261111
ROUTE_J = {"within_lt3d": 0, "transfer_lt3d": 1, "voxelnext_val": 2, "public_lt3d_val": 3, "source_transfer": 4}
ROUTE_LABEL = {"within_lt3d": "H1 primary; H2, H3, H10 secondary", "transfer_lt3d": "H4 secondary", "voxelnext_val": "H5 descriptive",
               "public_lt3d_val": "H1-P descriptive", "source_transfer": "descriptive (train -> validation source transfer)"}
TRACKERS = ("t1", "t3")
WORDING = "not shown above delta (one-sided simultaneous test at 0.95)"
STAMPS = {"c1": "C1 CONFIRMATORY: AV2 validation", "standin": "C1 STAND-IN: nuScenes development scenes treated as logs; not evidence",
          "reproduce": "C1 CODE ON K8 RUNS: reproduction check on nuScenes development evidence",
          "smoke": "C1 SMOKE: relaxed evaluability, plumbing only"}
GATE_NOTE = "supportive, not confirmatory (gate H1 not passed)"
K8_SEEDS = False   # --reproduce: K8 v03's own seeds (bootstrap [20261106, i, 0], power [20261107, i]), so its numbers are reproduced exactly


def seeds(i, j):
    if K8_SEEDS:
        return [K.SEED, i, 0], [K.POWER_SEED, i]
    return [SEED_BOOT, i, j], [SEED_POWER, i, j]


def sha(p):
    return K.sha(p)


# ---------------------------------------------------------------- C1 rules (pure functions)

def arm_status(v):
    """C1 v04 section 5.4 from one arm's k8 validity entry (validity_by_arm[a]): per population NoFlag, FamFlag, NoFlag_pool, Floor,
    HK1c; Valid = all five on every population; ShownAbove = a flagged cell, a flagged family cell, or the pooled cell (if
    evaluable) flagged or above HK1c; floor_only = not Valid and not ShownAbove (Choice 9's case)."""
    per, valid, shown = {}, True, False
    for p in POPS:
        r = v["pops"][p]
        pooled = r.get("pooled")
        nf, ff, pe = not r.get("flagged"), bool(r.get("family_flagged")), pooled is not None
        nfp = pe and not pooled["flagged"]
        hk1c = pe and bool(pooled["HK1c_ub_le_delta_plus_0.03"])
        floor = (int(r.get("family_size") or 0) >= F_MIN) if p in FLOOR_POPS else (int(r.get("evaluable") or 0) >= 1)
        ok = bool(nf and not ff and nfp and floor and hk1c)
        sa = bool((not nf) or ff or (pe and not nfp) or (pe and not hk1c))
        per[p] = {"NoFlag": nf, "FamFlag": ff, "pooled_evaluable": pe, "NoFlag_pool": nfp, "Floor": floor, "HK1c": hk1c, "valid": ok,
                  "shown_above": sa, "flagged_cells": list(r.get("flagged") or []), "family_flagged": list(r.get("family_flagged") or []),
                  "family_size": r.get("family_size"), "evaluable": r.get("evaluable")}
        valid, shown = valid and ok, shown or sa
    return {"valid": bool(valid), "shown_above": bool(shown), "floor_only": bool((not valid) and (not shown)), "pops": per,
            "wording": WORDING}


def paired(rate, Ws, a, b, level):
    """Per-log paired difference rate[a] - rate[b] (scene-level means), its one-sided bound at level, 95 % interval and the
    p-value of 'UB < 0' (the share of bootstrap means >= 0)."""
    d = np.asarray(rate[a], float) - np.asarray(rate[b], float)
    bm = (Ws @ d) / Ws.sum(1)
    return {"mean_diff": float(d.mean()), "ub": float(np.quantile(bm, level)), "level": float(level),
            "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])], "p_lt0": float(np.mean(bm >= 0)), "_bm": bm}


def form_b(status, rate, Ws, method="Mstar", comps=K_SET, alpha=0.05):
    present = [c for c in comps if c in status and c in rate]
    V = [c for c in present if not status[c]["shown_above"]]
    level = 1 - alpha / max(len(V), 1)
    per = {}
    for c in V:
        r = paired(rate, Ws, method, c, level)
        r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    met = bool(status[method]["valid"] and all(v["lower"] for v in per.values()))
    p = min(1.0, len(V) * max(v["p_lt0"] for v in per.values())) if V else 0.0
    return {"method": method, "valid_method": status[method]["valid"], "V": V, "in_V_by_choice9": [c for c in V if status[c]["floor_only"]],
            "removed_shown_above": [c for c in present if c not in V], "missing": [c for c in comps if c not in present],
            "n_V": len(V), "level": level, "vs": per, "met": met, "p_rejection_bonferroni": p,
            "rule": "C1 v04 5.4 FormB with Choice 9 (E13): V_t = K minus the comparators shown above delta"}


def form_a(status, rate, Ws, method="Mstar"):
    present = [c for c in FORM_A_SET if c in rate]
    per = {}
    for c in present:
        r = paired(rate, Ws, method, c, 1 - 0.05 / len(FORM_A_SET))
        r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    return {"label": "descriptive", "valid_method": status[method]["valid"], "vs": per, "complete": len(present) == len(FORM_A_SET),
            "met": bool(status[method]["valid"] and len(present) == len(FORM_A_SET) and all(v["lower"] for v in per.values()))}


def form_c(rate, Ws, c_t, alpha=0.05, method="Mstar", ref="B4"):
    r = paired(rate, Ws, method, ref, 1 - alpha)
    bm = r.pop("_bm")
    r.update({"c": float(c_t), "met": bool(r["ub"] <= c_t), "p": float(np.mean(bm > c_t)),
              "rule": "UB^{1-alpha}(M* - B4 infeasible rate) <= c_t; c_t read from the plan (R16 m1)"})
    return r


def joint_status(jv):
    """ValidJ from one arm's joint_loss.validity_by_arm entry: per population the pooled joint loss not flagged (A.flag: LB > delta,
    or zero SE and E > delta) and UB <= delta + 0.03. No floor exists on the joint loss (C1 v04 5.4)."""
    per, ok = {}, True
    for p in POPS:
        r = jv["pops"][p]
        has = r.get("E") is not None
        v = bool(has and not r.get("flagged") and r.get("ub_le_delta_plus_0.03"))
        per[p] = {"E": r.get("E"), "lb": r.get("lb_one_sided_0.95"), "ub": r.get("ub_one_sided_0.95"), "flagged": r.get("flagged"),
                  "evaluable": r.get("evaluable"), "validJ": v}
        ok = ok and v
    return {"validJ": bool(ok), "shown_aboveJ": bool(not ok), "pops": per}


def joint_b(jstat, rate, Ws, method="MstarJx", comps=KJ_SET, alpha=0.05):
    present = [c for c in comps if c in jstat and c in rate]
    V = [c for c in present if jstat[c]["validJ"]]
    level = 1 - alpha / max(len(V), 1)
    per = {}
    for c in V:
        r = paired(rate, Ws, method, c, level)
        r.pop("_bm")
        r["lower"] = bool(r["ub"] < 0)
        per[c] = r
    met = bool(jstat[method]["validJ"] and all(v["lower"] for v in per.values()))
    p = min(1.0, len(V) * max(v["p_lt0"] for v in per.values())) if V else 0.0
    return {"method": method, "validJ_method": jstat[method]["validJ"], "VJ": V, "missing": [c for c in comps if c not in present],
            "level": level, "vs": per, "met": met, "p_rejection_bonferroni": p}


def supt_lower_pvalues(est, boot, target):
    """For each cell of a family: the p-value of 'LB^{sup-t,1-alpha} > target' (the smallest alpha at which it holds), from the
    family's studentised sup statistic (M._simul's construction). Zero-SE cells: 0 if est > target else 1."""
    est, boot = np.asarray(est, float), np.asarray(boot, float)
    se = np.nanstd(boot, axis=0, ddof=1)
    ok = se > 0
    if not ok.any():
        return np.where(est > target, 0.0, 1.0)
    with np.errstate(invalid="ignore", divide="ignore"):
        T = np.nanmax(np.where(ok, (boot - est) / np.where(ok, se, 1.0), np.nan), axis=1)
        t = np.where(ok, (est - target) / np.where(ok, se, 1.0), np.nan)
    p = np.array([float(np.mean(T >= t[j])) if ok[j] else (0.0 if est[j] > target else 1.0) for j in range(len(est))])
    return p


def h10_rule(cells, est, boot, ev, sig_b6, sig_m, rate, Ws, alpha=0.05, margin=NI_MARGIN):
    """H10 for one tracker. est, boot, ev: PD7 cell estimates, bootstrap rows and evaluability per arm ('B6', 'Mstar');
    sig_b6, sig_m: the arms' flagged PD7 cells (all-evaluable family)."""
    pr = A.paired(est, boot, ev, cells, "B6", "Mstar", 0.95)
    both = np.flatnonzero(ev["B6"] & ev["Mstar"])
    fam_b6 = np.flatnonzero(ev["B6"])
    p_flag = dict(zip([cells[j][0] for j in fam_b6], supt_lower_pvalues(est["B6"][fam_b6], boot["B6"][:, fam_b6], DELTA))) if len(fam_b6) else {}
    d = est["B6"][both] - est["Mstar"][both]
    db = boot["B6"][:, both] - boot["Mstar"][:, both]
    p_pair = dict(zip([cells[j][0] for j in both], supt_lower_pvalues(d, db, 0.0))) if len(both) else {}
    qual = [cells[j][0] for j in both if cells[j][0] in set(sig_b6) and cells[j][0] not in set(sig_m) and pr.get(cells[j][0], {}).get("positive")]
    cand = [cells[j][0] for j in both if cells[j][0] not in set(sig_m)]
    p_cell = min([max(p_flag.get(c, 1.0), p_pair.get(c, 1.0)) for c in cand], default=1.0)
    ni = paired(rate, Ws, "Mstar", "B6", 1 - alpha)
    bm = ni.pop("_bm")
    ni.update({"margin": margin, "met": bool(ni["ub"] <= margin), "p": float(np.mean(bm > margin))})
    return {"cells_failing_B6": qual, "cell_part": bool(qual), "noninferiority": ni, "met": bool(qual and ni["met"]),
            "p": float(max(p_cell, ni["p"])), "rule": "C1 v04 5.4 H10 (M-PLAN 7 'a baseline fails' on PD7, and NI margin 0.03)"}


def h6_rules(ms):
    """H6a, H6b from the method stage's E1-AV2 summaries (m_lib_v04._summary dicts: ms['E1']['fixed'], ms['E1']['refit'])."""
    h = M.hypotheses_e1(ms["E1"]["fixed"], ms["E1"]["refit"])
    b4 = M.failures([ms["E1"]["refit"]], "B4", "B4-Mstar")
    return {"H6a": bool(h["HM1"]), "Mstar_flagged_cells": h["Mstar_flagged_cells"], "H6b": bool(b4), "B4_failing_cells": b4,
            "H6b_p": ms.get("H6b_p")}


def h7_rule(ms):
    h = M.hypotheses_e2(ms["E2"]["cells"], ms["E2"]["all"])
    return {"H7": bool(h["HM6"]), "flagged": h["HM6a_flagged"], "pooled_lb": h["pooled_lb"]}


def h8_rule(d, level=0.95):
    """X2's FAILS rule on the 4 decision cells: cell r FAILS if its sup-t lower bound under B0 exceeds max(delta, E0_r) and its
    truth-oriented sup-t lower bound exceeds delta. H8 holds if a lateral in-path car cell (< 20 m or 20-40 m) FAILS."""
    lb, _, _, _ = M._simul(np.asarray(d["est_B0"], float), np.asarray(d["boot_B0"], float), level, "lower")
    lbt, _, _, _ = M._simul(np.asarray(d["est_truth"], float), np.asarray(d["boot_truth"], float), level, "lower")
    fails = {c: bool(lb[i] > max(DELTA, d["E0"][i]) and lbt[i] > DELTA) for i, c in enumerate(d["cells"])}
    return {"fails": fails, "H8": bool(any(fails[c] for c in d["target_cells"])), "lb_B0": lb.tolist(), "lb_truth": lbt.tolist()}


def h9_rule(N, X, cells, scene_of_ep, log_of_ep, W, power_key, floor=F_MIN):
    """H9 (Choice 23): no evaluable cell flagged, the pooled cell not flagged, at least `floor` power-qualified cells, none flagged."""
    one = np.ones((1, N.shape[0]))
    ev = A.evaluable(N, scene_of_ep, log_of_ep)
    fam = np.flatnonzero(ev)
    est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
    flagged = []
    if len(fam):
        _, _, _, sig, _ = A.flag(est, boot, fam, 0.95)
        flagged = [cells[j][0] for i, j in enumerate(fam) if sig[i]]
    Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
    e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
    _, _, _, sigp, _ = A.flag(e1, b1, np.array([0]), 0.95)
    pw, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng(list(power_key)))
    qual = np.flatnonzero(ev & (pw >= A.POWER_MIN))
    fflag = []
    if len(qual):
        _, _, _, sigf, _ = A.flag(est, boot, qual, 0.95)
        fflag = [cells[j][0] for i, j in enumerate(qual) if sigf[i]]
    ok = bool(len(fam) and not flagged and not sigp[0] and len(qual) >= floor and not fflag)
    return {"H9": ok, "evaluable": int(len(fam)), "flagged": flagged, "pooled_flagged": bool(sigp[0]), "family_size": int(len(qual)),
            "family_flagged": fflag, "floor": floor, "power_seed": list(power_key)}


def holm(claims, alpha=0.05, gate=True):
    """claims: {name: {'p': float or None, 'gate_ok': bool}}. Holm step-down at alpha over the claims with a p-value and an open
    gate; a failed validity gate fails its claim. If the H1 gate is closed, nothing is tested: every claim is labelled GATE_NOTE."""
    out = {}
    if not gate:
        for c, v in claims.items():
            out[c] = {"p": v.get("p"), "gate_ok": v.get("gate_ok"), "rejected": None, "label": GATE_NOTE}
        return out
    tested = sorted([c for c, v in claims.items() if v.get("p") is not None and v.get("gate_ok", True)], key=lambda c: claims[c]["p"])
    m, stop = len(tested), False
    for i, c in enumerate(tested):
        lvl = alpha / (m - i)
        rej = (not stop) and claims[c]["p"] <= lvl
        stop = stop or not rej
        out[c] = {"p": claims[c]["p"], "holm_level": lvl, "rejected": bool(rej), "gate_ok": True,
                  "label": "confirmed (Holm, family S)" if rej else "not confirmed"}
    for c, v in claims.items():
        if c not in out:
            out[c] = {"p": v.get("p"), "gate_ok": v.get("gate_ok"), "rejected": False,
                      "label": "not confirmed (validity gate failed)" if v.get("gate_ok") is False else "not testable (no p-value)"}
    return out


def by_source(vals, keys_source, Ws, sources):
    """Descriptive source heterogeneity: per source the log-level mean with a 95 % interval, and the difference of the first two
    sources with its log-bootstrap interval."""
    v = np.asarray(vals, float)
    out = {}
    bms = {}
    for s in sources:
        m = (np.asarray(keys_source) == s) & np.isfinite(v)
        if not m.any():
            continue
        w = Ws[:, m]
        bms[s] = (w @ v[m]) / w.sum(1)
        out[s] = {"mean": float(v[m].mean()), "ci95": [float(x) for x in np.nanquantile(bms[s], [0.025, 0.975])], "logs": int(m.sum())}
    if len(bms) >= 2:
        a_, b_ = list(bms)[:2]
        dd = bms[a_] - bms[b_]
        out["difference"] = {"of": [a_, b_], "mean": out[a_]["mean"] - out[b_]["mean"], "ci95": [float(x) for x in np.nanquantile(dd, [0.025, 0.975])]}
    return out


# ---------------------------------------------------------------- one route x tracker (decision mode)

def configure(mode):
    if mode == "smoke":
        K.DEV_SCENES, K.STRICT_Q = (), False
        A.MIN_SCENES, A.MIN_LOGS = 2, 1
    else:
        K.DEV_SCENES, K.STRICT_Q = (), True
        A.MIN_SCENES, A.MIN_LOGS = 39, 8
    K.STAMP = STAMPS[mode]


def load_run(runs, tag, mode):
    tm = "%s_%s" % (tag, mode)
    rr_p = os.path.join(runs, "run_record_%s.json" % tm)
    rr = json.load(open(rr_p)) if os.path.exists(rr_p) else None
    if rr is not None:
        for f, ext in K.RUN_OUTPUTS:
            p = os.path.join(runs, "%s_%s.%s" % (f, tm, ext))
            assert sha(p) == rr["%s_sha256" % f], "output %s changed since its run record" % p
    eps = [json.loads(l) for l in open(os.path.join(runs, "episodes_%s.jsonl" % tm))]
    counts = dict(np.load(os.path.join(runs, "counts_%s.npz" % tm)))
    D = dict(np.load(os.path.join(runs, "decisions_%s.npz" % tm)))
    C = dict(np.load(os.path.join(runs, "cal_%s.npz" % tm)))
    return rr, eps, counts, D, C


def per_scene_rates(eps, arm_of_scene, scenes):
    inf = {(o["scene"], o["arm"]): (o["infeasible_frames"], o["frames"]) for o in eps if o.get("entered") and o["arm"] != "LOG"}
    arms = sorted({a for _, a in inf})
    rate = {a: np.array([inf[(sc, a)][0] / max(inf[(sc, a)][1], 1) for sc in scenes]) for a in arms if all((sc, a) in inf for sc in scenes)}
    if arm_of_scene:
        rate["RETUNED"] = np.array([inf[(sc, arm_of_scene[sc])][0] / max(inf[(sc, arm_of_scene[sc])][1], 1) for sc in scenes])
    return rate


def analyse_route_tracker(route, i, tag, runs, fits_path, log_of_scene, source_of_log, c_t, B=K.B_BOOT, transfer_retuned=None):
    j = ROUTE_J[route]
    rr, eps, counts, D, C = load_run(runs, tag, "decide")
    fits = json.load(open(fits_path)) if fits_path else None
    fits_for_k8 = fits
    if route in ("transfer_lt3d", "source_transfer"):     # one transfer fit: RETUNED is the recorded nuScenes point, applied everywhere
        arm = transfer_retuned or (fits or {}).get("retuned_transfer_arm")
        scen = sorted({o["scene"] for o in eps})
        if arm:
            eps, counts, D, C = K.add_composite_arm(eps, counts, D, C, {s_: arm for s_ in scen})
        fits_for_k8 = None
    sb, sp = seeds(i, j)
    res = K.analyse_decide(eps, counts, D, C, log_of_scene, B, np.random.default_rng(sb), sp, fits_for_k8, None, None)
    # the same keys and weights as analyse_decide (its first use of the rng), for the paired tests and H10
    eps_f = [o for o in eps if o["entered"] and o["scene"] not in K.DEV_SCENES and o["arm"] != "LOG"]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps_f, log_of_scene, B, np.random.default_rng(sb))
    W = W_logs[:, log_of_ep]
    scenes = sorted({o["scene"] for o in eps_f})
    lg = np.array([logs.index(log_of_scene[sc]) for sc in scenes])
    Ws = W_logs[:, lg]
    aos = (res.get("retune") or {}).get("arm_of_scene")
    rate = per_scene_rates(eps_f, aos if route not in ("transfer_lt3d", "source_transfer") else None, scenes)
    status = {a: arm_status(v) for a, v in res["validity_by_arm"].items()}
    out = {"route": route, "tracker": tag, "label": ROUTE_LABEL[route], "seeds": {"bootstrap": sb, "power": sp},
           "status": status, "form_b": form_b(status, rate, Ws), "form_a": form_a(status, rate, Ws),
           "form_c": form_c(rate, Ws, c_t) if "B4" in rate else None, "run_record_sha256": sha(os.path.join(runs, "run_record_%s_decide.json" % tag))
           if rr else None, "fits_sha256": sha(fits_path) if fits_path else None}
    # H3 on the joint loss
    jl = res.get("joint_loss") or {}
    if "MstarJx" in rate and jl.get("validity_by_arm"):
        jstat = {a: joint_status(v) for a, v in jl["validity_by_arm"].items()}
        out["joint_status"] = jstat
        out["H3"] = joint_b(jstat, rate, Ws, "MstarJx")
        if "MstarJ" in jstat:
            out["MstarJ_descriptive"] = joint_b(jstat, rate, Ws, "MstarJ")
    # H10 (M* vs B6) on PD7
    if "B6" in rate and "Mstar" in rate:
        cells = A.cell_family()
        _, tabs = A.populations(eps_f, counts, ["Mstar", "B6"], keys, scene_of_ep, log_of_ep, W, {"PD7_primary": K.POP_DECIDE["PD7_primary"]})
        Ns, Xs, ests, boots, evs = tabs["PD7_primary"]
        sig = {a: set(res["populations"]["PD7_primary"]["cells_by_arm"][a]["sig_above_cells"]) for a in ("Mstar", "B6")}
        out["H10"] = h10_rule(cells, ests, boots, evs, sig["B6"], sig["Mstar"], rate, Ws)
        # source heterogeneity (descriptive): M*'s pooled V1 per population and its infeasible rate, by source
        if source_of_log:
            ksrc = [source_of_log.get(log_of_scene[k[0]], "unknown") for k in keys]
            srcs = sorted(set(ksrc))
            het = {"infeasible_rate": by_source(rate["Mstar"], [source_of_log.get(log_of_scene[s_], "unknown") for s_ in scenes], Ws, srcs)}
            _, tabs3 = A.populations(eps_f, counts, ["Mstar"], keys, scene_of_ep, log_of_ep, W, {p: K.POP_DECIDE[p] for p in POPS})
            for p in POPS:
                Nm, Xm = tabs3[p][0]["Mstar"], tabs3[p][1]["Mstar"]
                v1 = np.where(Nm.sum(1) > 0, Xm.sum(1) / np.maximum(Nm.sum(1), 1), np.nan)
                het["V1_" + K.POP_LAB[p]] = by_source(v1, ksrc, W, srcs)
            out["source_heterogeneity"] = het
    # RETUNED as E14 (descriptive)
    sweep = [a for a in S.SWEEP_ARMS if a in status]
    valid_sweep = [a for a in sweep if status[a]["valid"]]
    out["RETUNED_E14"] = {"arm_of_fold": (res.get("retune") or {}).get("arm_of_fold"),
                          "single_arm_in_all_folds": len(set(((res.get("retune") or {}).get("arm_of_fold") or {}).values())) == 1,
                          "sweep_points_valid_in_sample_by_form_B_rule": valid_sweep,
                          "cheapest_valid_point": (min(valid_sweep, key=lambda a: float(rate[a].mean())) if valid_sweep else None),
                          "cheapest_valid_infeasible_rate": (float(min(rate[a].mean() for a in valid_sweep)) if valid_sweep else None),
                          "note": "RETUNED is selected by D14 A3's pooled rule and judged by Form B's cell rule (E14)"}
    out["power_family_seeds"] = {a: {"seed": (list(sp) if a == "Mstar" else list(sp) + [100 + K.ARM_INDEX[a]]),
                                     "per_population_suffix": list(range(len(POPS))),
                                     "family_size": {p: res["validity_by_arm"][a]["pops"][p].get("family_size") for p in POPS}}
                                 for a in res["validity_by_arm"]}
    out["infeasible_rate"] = {a: float(v.mean()) for a, v in rate.items()}
    res_small = {k: v for k, v in res.items() if not k.startswith("_")}
    return out, res_small, res


def decide(results, cfg, mode):
    """The decision file: H1 to H10, labels, failed conditions, the gate and Holm."""
    get = lambda route, t: results.get(route, {}).get(t)  # noqa: E731
    dec = {"stamp": STAMPS[mode], "delta": DELTA, "wording": WORDING, "hypotheses": {}, "failed_conditions": []}
    w = {t: get("within_lt3d", t) for t in TRACKERS}
    h1_ok = all(w[t] is not None for t in TRACKERS) and all(w[t]["form_b"]["met"] for t in TRACKERS)
    for t in TRACKERS:
        if w[t] is None:
            dec["failed_conditions"].append("%s: within-AV2 decision-mode run missing" % t)
            continue
        fb = w[t]["form_b"]
        if not fb["valid_method"]:
            st = w[t]["status"]["Mstar"]
            for p, r in st["pops"].items():
                for k_ in ("NoFlag", "NoFlag_pool", "Floor", "HK1c"):
                    if not r[k_]:
                        dec["failed_conditions"].append("%s %s: M* %s fails" % (t, p, k_))
                if r["FamFlag"]:
                    dec["failed_conditions"].append("%s %s: M* family cell flagged" % (t, p))
        for c, v in fb["vs"].items():
            if not v["lower"]:
                dec["failed_conditions"].append("%s: M* not less infeasible than %s%s" % (t, c, " (in V_t by Choice 9)" if c in fb["in_V_by_choice9"] else ""))
        if fb["missing"]:
            dec["failed_conditions"].append("%s: comparators missing from the run: %s" % (t, fb["missing"]))
    dec["hypotheses"]["H1"] = {"label": "primary", "holds": bool(h1_ok), "by_tracker": {t: (w[t] or {}).get("form_b") for t in TRACKERS}}
    dec["C1_verdict"] = "GO" if h1_ok else "NO-GO"
    if not h1_ok and all(w[t] is not None for t in TRACKERS):
        if all(w[t]["status"]["Mstar"]["valid"] for t in TRACKERS):
            dec["C1_verdict_wording"] = "not shown above delta, operability not shown"
        elif all(not w[t]["status"]["Mstar"]["shown_above"] for t in TRACKERS):
            dec["C1_verdict_wording"] = "floor not met"
    claims = {}
    if all(w[t] is not None for t in TRACKERS):
        fc = {t: w[t]["form_c"] for t in TRACKERS}
        dec["hypotheses"]["H2"] = {"label": "secondary", "holds": all(fc[t]["met"] for t in TRACKERS), "by_tracker": fc}
        claims["H2"] = {"p": max(fc[t]["p"] for t in TRACKERS), "gate_ok": True}
        if all("H3" in w[t] for t in TRACKERS):
            h3 = {t: w[t]["H3"] for t in TRACKERS}
            gate3 = all(h3[t]["validJ_method"] for t in TRACKERS)
            dec["hypotheses"]["H3"] = {"label": "secondary", "holds": all(h3[t]["met"] for t in TRACKERS), "validity_gate": gate3, "by_tracker": h3}
            claims["H3"] = {"p": max(h3[t]["p_rejection_bonferroni"] for t in TRACKERS), "gate_ok": gate3}
        h10 = {t: w[t].get("H10") for t in TRACKERS}
        if all(h10.values()):
            dec["hypotheses"]["H10"] = {"label": "secondary", "holds": all(h10[t]["met"] for t in TRACKERS), "by_tracker": h10}
            claims["H10"] = {"p": max(h10[t]["p"] for t in TRACKERS), "gate_ok": True}
        dec["hypotheses"]["FormA"] = {"label": "descriptive", "by_tracker": {t: w[t]["form_a"] for t in TRACKERS}}
    tr = {t: get("transfer_lt3d", t) for t in TRACKERS}
    if all(tr.values()):
        gate4 = all(tr[t]["form_b"]["valid_method"] for t in TRACKERS)
        dec["hypotheses"]["H4"] = {"label": "secondary", "holds": all(tr[t]["form_b"]["met"] for t in TRACKERS), "validity_gate": gate4,
                                   "by_tracker": {t: tr[t]["form_b"] for t in TRACKERS}}
        claims["H4"] = {"p": max(tr[t]["form_b"]["p_rejection_bonferroni"] for t in TRACKERS), "gate_ok": gate4}
    for route, hn in (("voxelnext_val", "H5"), ("public_lt3d_val", "H1-P"), ("source_transfer", "source_transfer")):
        rr_ = {t: get(route, t) for t in TRACKERS}
        if all(rr_.values()):
            dec["hypotheses"][hn] = {"label": "descriptive", "holds_as_formula": all(rr_[t]["form_b"]["met"] for t in TRACKERS),
                                     "by_tracker": {t: rr_[t]["form_b"] for t in TRACKERS}}
    ms = cfg.get("_method_stage")
    if ms:
        h6 = {t: h6_rules(ms[t]) for t in TRACKERS}
        h7 = {t: h7_rule(ms[t]) for t in TRACKERS}
        dec["hypotheses"]["H6a"] = {"label": "secondary (no-flag)", "holds": all(h6[t]["H6a"] for t in TRACKERS), "by_tracker": h6}
        dec["hypotheses"]["H6b"] = {"label": "secondary", "holds": all(h6[t]["H6b"] for t in TRACKERS)}
        pv = [h6[t]["H6b_p"] for t in TRACKERS]
        claims["H6b"] = {"p": max(pv) if all(p is not None for p in pv) else None, "gate_ok": True}
        dec["hypotheses"]["H7"] = {"label": "secondary (no-flag)", "holds": all(h7[t]["H7"] for t in TRACKERS), "by_tracker": h7}
    if cfg.get("_h8"):
        dec["hypotheses"]["H8"] = dict(h8_rule(cfg["_h8"]), label="secondary, family P at 0.05")
    if cfg.get("_h9"):
        dec["hypotheses"]["H9"] = {"label": "secondary (no-flag, floor 6)", "holds": all(v["H9"] for v in cfg["_h9"].values()), "by_tracker": cfg["_h9"]}
    dec["family_S"] = holm(claims, 0.05, gate=h1_ok)
    dec["gate_H1"] = bool(h1_ok)
    return dec


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--decision", required=True)
    ap.add_argument("--csv-dir", default=None)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--c1", action="store_true")
    g.add_argument("--standin", action="store_true")
    g.add_argument("--reproduce", action="store_true")
    g.add_argument("--smoke", action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--boot", type=int, default=K.B_BOOT)
    a = ap.parse_args(argv)
    mode = "c1" if a.c1 else "standin" if a.standin else "reproduce" if a.reproduce else "smoke"
    assert mode == "smoke" or a.boot == K.B_BOOT, "B = 2000 is fixed outside --smoke"
    configure(mode)
    global K8_SEEDS
    K8_SEEDS = mode == "reproduce"
    t0 = time.time()
    cfg = json.load(open(a.config))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_analyse_v01", "c1_analyse_v06", LEGACY.ds_config(cfg))
    binding = {"mode": mode, "config_sha256": sha(a.config), "analysis_sha256": sha(os.path.abspath(__file__)), "k8_analyse_v04_sha256": sha(K.__file__)}
    if mode == "c1":
        assert a.plan, "--c1 needs --plan (the frozen C1 plan)"
        side = open(a.plan.replace(".md", ".sha256")).read().split()[0]
        assert sha(a.plan) == side, "C1 plan hash mismatch"
        block = open(a.plan, encoding="utf-8").read().split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
        frozen = {ln.split("  ", 1)[0] for ln in block.strip().splitlines() if ln.strip() and not ln.startswith(("#", "("))}
        for p in [os.path.abspath(__file__), K.__file__, a.config] + [r["fits"][t] for r in cfg["routes"] for t in TRACKERS if r.get("fits")]:
            assert sha(p) in frozen, "not in the frozen plan: " + p
        binding["plan_sha256"] = side
    log_of_scene = {}
    for p in cfg.get("manifests", []):
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    source_of_log = json.load(open(cfg["folds"]))["source_of_log"] if cfg.get("folds") else {}
    if cfg.get("method_stage"):
        cfg["_method_stage"] = {t: json.load(open(p)) for t, p in cfg["method_stage"].items()}
    if cfg.get("h8"):
        cfg["_h8"] = json.load(open(cfg["h8"]))
    results, k8res = {}, {}
    csv_dir = a.csv_dir or os.path.dirname(os.path.abspath(a.out))
    os.makedirs(csv_dir, exist_ok=True)
    for r in cfg["routes"]:
        for i, t in enumerate(TRACKERS):
            if t not in r["tags"]:
                continue
            runs = r["runs"]
            l_of = log_of_scene
            if cfg.get("units_are_logs"):
                eps0 = [json.loads(l) for l in open(os.path.join(runs, "episodes_%s_decide.jsonl" % r["tags"][t]))]
                l_of = {o["scene"]: o["scene"] for o in eps0}
                del eps0
            if mode in ("c1", "standin"):
                rr = json.load(open(os.path.join(runs, "run_record_%s_decide.json" % r["tags"][t])))
                assert rr.get("c1") is True and bool(rr.get("standin")) == (mode == "standin"), "run %s is not a %s run" % (r["tags"][t], mode)
                if r.get("fits"):
                    assert rr["fits_sha256"] == sha(r["fits"][t]), "the fits are not the run's fits: " + r["tags"][t]
            c_t = float(cfg.get("c", C_DEFAULT)[t])
            out, res_small, res = analyse_route_tracker(r["name"], i, r["tags"][t], runs, (r.get("fits") or {}).get(t), l_of, source_of_log, c_t,
                                                        a.boot, r.get("retuned_arm"))
            K.csv_tables_decide(res, "%s_%s" % (r["name"], t), csv_dir)
            results.setdefault(r["name"], {})[t] = out
            k8res.setdefault(r["name"], {})[t] = K.strip_csv_payload(res_small)
            if "loop" in r.get("modes", []) and os.path.exists(os.path.join(runs, "episodes_%s_loop.jsonl" % r["tags"][t])):
                _, eps, counts, D, C = load_run(runs, r["tags"][t], "loop")
                rl = K.analyse_loop(eps, counts, D, C, l_of, a.boot, np.random.default_rng([SEED_BOOT, i, ROUTE_J[r["name"]], 1]),
                                    (res.get("retune") or {}).get("arm_of_scene"))
                k8res[r["name"]][t + "_loop"] = K.strip_csv_payload(rl)
            del res
            print("%s %s: done %.0f s" % (r["name"], t, time.time() - t0), flush=True)
    dec = decide(results, cfg, mode)
    dec["binding"] = binding
    for path, obj in ((a.out, {"stamp": STAMPS[mode], "binding": binding, "c1": results, "k8": k8res}), (a.decision, dec)):
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w") as f:
            json.dump(obj, f, indent=1, default=float)
    print(json.dumps({"C1_verdict": dec["C1_verdict"], "failed_conditions": dec["failed_conditions"][:10]}))
    print(STAMPS[mode])
    print("C1 ANALYSIS V01 DONE")


if __name__ == "__main__":
    main()
