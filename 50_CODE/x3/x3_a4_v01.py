#!/usr/bin/env python3
"""X3 amendment A4 parts (1), (3), (5) and (2) (x3-core agent, x3_a4_v01, 7 Nov 2026). Added after review (amendment A4).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).
Amendment: 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md (sha256 ab19dd66...). Seeds [20261201, i, 10 + k] (bootstrap) and
[20261202, i, 10 + k] (power) for part k.

(1) Matched validity on the neutral screen. An arm passes when (a) no cell of P1-P7 of analysis (b) is flagged in P_rel, P_near or
    P_ip (one-sided simultaneous 0.95 per partition and population over its evaluable cells, >= 39 logs; (b)'s bins and rule) and (b)
    HK1c holds on each population (pooled upper bound at 0.995 <= 0.08; the pooled cell is every record of the population, from the
    partition counts' P0 sums, which equal the counts of record by gate V2; not evaluable = fails). No power floor; the evaluable
    partition cells are counted beside the status. Families: M* at delta' (x3_fits_a4_v01), B4 / B6 / B9 at delta' ((a)'s refits),
    the B0 merged alpha/delta' curve (21 points, ordered by alpha_eq). Grid order least to most conservative. Selection per held-out
    fold: the first point passing on the other four folds' logs (weights restricted to them); no point -> "no matched point" for the
    family (no conservative substitute), with its in-sample best (the least conservative point passing on all 375 logs). Per point and
    composite: infeasible rate, progress ratio, mean back-off level, V2_exec (k8_analyse_v04's definitions, x3_a3_v01.endpoints); the
    composite's neutral and registered (x3_screen_v01, flags at 0.95 as RETUNED-HK1) statuses; M* (at its own neutral-matched
    composite) minus the composite, paired, 95 % interval, only when both pass. Also (a)'s registered-screen table re-read with
    "flagged" separated from "fails HK1c only" and "fails a floor only", contrasts only for passing composites.
(3) Ego footprint 4.9 x 1.9 m (x3_run_v03 variant "ego"; the default 4.1 x 1.8 m through the same code path is checked equal to the
    record first): M* (fits of record), B0, B4, B6; registered-screen status with the record's roles (the arm's own name: comparators of
    K flagged at 1 - 0.0125/9, M* at 0.95), infeasible rate, V2_exec.
(5) AB3DMOT without unmatched tracks (x3_run_v03 "drop_unmatched"): M* and Z0; infeasible rate, progress ratio, registered-screen status,
    compared with M* and Z0 on all tracks (record). Reading fixed by A4: a fall of the infeasible rate by more than half = false-positive
    tracks are a main driver.
Commands: spec | check | neutral | ego | tab
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
import x3_screen_v01 as SC  # noqa: E402
import x3_a3_v01 as A3  # noqa: E402

K, A, S, R = SC.K, SC.A, SC.S, SC.R
LABEL = "added after review (amendment A4)"
OUT = os.path.join(C.OUT, "a4_review")
RUN_DIR = os.path.join(C.OUT, "runs")
AMEND = os.path.join(C.W, "20_DESIGN", "X3_PLAN_AMENDMENT_A4_v01.md")
GRID = (0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005)
FAMS = ("Mstar", "B4", "B6", "B9", "B0")
POP_C4 = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3)}
EGO_BIG = [4.9, 1.9]


def seeds(t, k):
    i = C.TRACKER_I[t]
    return [C.SEED_BOOT_X3, i, 10 + k], [C.SEED_POWER_X3, i, 10 + k]


def stamp():
    return {"stamp": C.STAMP, "label": LABEL, "amendment_sha256": C.sha256(AMEND)}


def sweep_order():
    return sorted(S.SWEEP_ARMS, key=lambda a: (S.CURVE_ALPHA_OF_ARM[a], a))


def family_points(fam):
    if fam == "B0":
        return sweep_order()
    return ["%s@%s" % (fam, repr(d)) for d in GRID]


def write_spec():
    for t in ("t1", "t3"):
        vs = []
        for d in GRID[1:]:
            vs.append({"label": "Mstar@%s" % repr(d), "base": "Mstar", "fits": os.path.join(OUT, "fits", "fits_x3a4_Mstar_%s_d%s.json" % (t, repr(d))), "cov_dir": None})
        for fam in ("B4", "B6", "B9"):
            for d in GRID[1:]:
                vs.append({"label": "%s@%s" % (fam, repr(d)), "base": fam, "fits": os.path.join(C.OUT, "a_matched", "fits", "fits_x3a_%s_d%s.json" % (t, repr(d))), "cov_dir": None})
        for a in sweep_order():
            vs.append({"label": a, "base": a, "fits": None, "cov_dir": None})
        C.jdump(os.path.join(RUN_DIR, "specs", "spec_a4n_%s_v01.json" % t), dict(stamp(), purpose="A4 (1): M*, B4, B6, B9 at delta' and the B0 curve, with partition counts", variants=vs))
        ego = []
        for arm in ("Mstar", "B0", "B4", "B6"):
            for lab, sz in (("default", [4.1, 1.8]), ("4.9x1.9", EGO_BIG)):
                ego.append({"label": "%s_ego_%s" % (arm, lab), "base": arm, "fits": None if arm == "B0" else C.FITS_REC[t], "cov_dir": None, "ego": sz})
        C.jdump(os.path.join(RUN_DIR, "specs", "spec_a4ego_%s_v01.json" % t), dict(stamp(), purpose="A4 (3): ego footprint (default through the same path = check)", variants=ego))
    C.jdump(os.path.join(RUN_DIR, "specs", "spec_a4tab_v01.json"), dict(stamp(), purpose="A4 (5): AB3DMOT without unmatched tracks", variants=[
        {"label": "Mstar_matched_only", "base": "Mstar", "fits": C.FITS_REC["tab"], "cov_dir": None, "drop_unmatched": True},
        {"label": "Z0_matched_only", "base": "Z0", "fits": None, "cov_dir": None, "drop_unmatched": True}]))
    print("specs written")


def check():
    """(1) the a4n re-runs of B4 / B6 / B9 equal (a)'s runs and the B0 curve equals the record; (3) the default footprint through the
    ego code path equals the record (M*, B0, B4, B6), all exact (x3_gates_v01.v0)."""
    import x3_gates_v01 as GV
    res, ok = {}, True
    for t in ("t1", "t3"):
        rec = GV.load_outputs(C.REC_RUNS, "%s_decide" % C.TAG_REC[t])
        mine = GV.load_outputs(RUN_DIR, "a4ego_%s" % t)
        for arm in ("Mstar", "B0", "B4", "B6"):
            m2 = dict(mine, eps=[dict(o, arm=arm) if o["arm"] == "%s_ego_default" % arm else dict(o, arm="__" + o["arm"]) for o in mine["eps"]])
            for o in m2["eps"]:
                o.pop("ego", None)
            r = GV.v0(rec, m2, [arm])[arm]
            res["%s ego default %s" % (t, arm)] = r["equal"] and r["scenes"] == 375
        mine = GV.load_outputs(RUN_DIR, "a4n_%s" % t)
        for a in sweep_order():
            r = GV.v0(rec, mine, [a])[a]
            res["%s a4n %s vs record" % (t, a)] = r["equal"] and r["scenes"] == 375
        del rec
        prev = GV.load_outputs(RUN_DIR, "a_%s" % t)
        labs = [l_ for l_ in {o["arm"] for o in prev["eps"]}]
        r_all = GV.v0(prev, mine, labs)
        for l_, r in r_all.items():
            res["%s a4n %s vs (a) run" % (t, l_)] = r["equal"] and r["scenes"] == 375
    ok = all(res.values())
    C.jdump(os.path.join(OUT, "x3_a4_checks_v01.json"), dict(stamp(), checks=res, passed=ok))
    print("A4 checks", ok, [k for k, v in res.items() if not v])
    if not ok:
        raise SystemExit("X3 STOP (A4): a check failed")


# ---------------------------------------------------------------- (1) the neutral screen
def acc_tables(eps_f, parts, labels, keys):
    import x3_analysis_b_v01 as AB
    return {lab: AB.acc_by_key(eps_f, parts, lab, keys) for lab in labels}


def neutral(acc6, kw, rows=None):
    import x3_run_v01 as RR
    W, sc, lg = kw["W"], kw["scene_of_ep"], kw["log_of_ep"]
    if rows is not None:
        W, sc, lg, acc6 = W[:, rows], sc[rows], lg[rows], acc6[rows]
    kwr = {"W": W, "scene_of_ep": sc, "log_of_ep": lg}
    nk = acc6.shape[0]
    flagged, n_eval = {}, 0
    for pi, pn in enumerate(RR.PARTS):
        if pn == "P0_distance_range":
            continue
        labels = RR.BIN_LABELS[pn]
        nb = len(labels)
        names = ["%s|%s" % (labels[b], ax) for b in range(nb) for ax in ("long", "lat")]
        for p, c4 in POP_C4.items():
            sub = acc6[:, list(c4), pi, :nb, :, :].sum(1)
            r = SC.partition_screen(sub[..., 0].reshape(nk, nb * 2), sub[..., 1].reshape(nk, nb * 2), kwr, names)
            n_eval += len(r["evaluable"])
            if r["flagged"]:
                flagged["%s/%s" % (pn, p)] = r["flagged"]
    one = np.ones((1, nk))
    hk = {}
    for p, c4 in POP_C4.items():
        Np = acc6[:, :, 0, :, :, 0][:, list(c4)].sum((1, 2, 3))[:, None]     # P0's bins cover every record (gate V2)
        Xp = acc6[:, :, 0, :, :, 1][:, list(c4)].sum((1, 2, 3))[:, None]
        if not A.evaluable(Np, sc, lg)[0]:
            hk[p] = {"evaluable": False, "ub": None, "holds": False}
            continue
        e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
        _, ub, _, _, _ = A.flag(e1, b1, np.array([0]), R.HK1C_LEVEL)
        hk[p] = {"evaluable": True, "E": float(e1[0]), "ub": float(ub[0]), "holds": bool(ub[0] <= C.DELTA + R.HK1C_MARGIN)}
    passes = bool(not flagged and all(v["holds"] for v in hk.values()))
    return {"passes": passes, "flagged": flagged, "n_flagged": sum(len(v) for v in flagged.values()), "hk1c": hk, "evaluable_partition_cells": n_eval}


def reg_class(st):
    """Registered-screen status split: Valid / flagged / fails HK1c only / fails a floor only."""
    if st["valid"]:
        return "Valid"
    pops = st["pops"].values()
    if any((not q["NoFlag"]) or q["FamFlag"] or (q["pooled_evaluable"] and not q["NoFlag_pool"]) for q in pops):
        return "flagged"
    if any(q["pooled_evaluable"] and not q["HK1c"] for q in pops) or any(not q["pooled_evaluable"] for q in pops):
        return "fails HK1c only" if all(q["Floor"] for q in pops) else "fails HK1c and a floor"
    return "fails a floor only"


def neutral_tracker(t):
    masks = SC.setup()
    sb, sp = seeds(t, 1)
    ec = SC.entered([json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_core_%s.jsonl" % t))])
    en = SC.entered([json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_a4n_%s.jsonl" % t))])
    kw = SC.keys_W(ec, C.B_X3, sb)
    keys = kw["keys"]
    assert sorted({(o["scene"], o["delay_kf"]) for o in en}) == keys
    acc = acc_tables(ec, dict(np.load(os.path.join(RUN_DIR, "parts_core_%s.npz" % t))), ["Mstar", "B4", "B6", "B9"], keys)
    acc = {("%s@0.05" % k if k != "Mstar" else "Mstar@0.05"): v for k, v in acc.items()}
    acc.update(acc_tables(en, dict(np.load(os.path.join(RUN_DIR, "parts_a4n_%s.npz" % t))), sorted({o["arm"] for o in en}), keys))
    folds = json.load(open(C.FOLDS))["fold_of_log"]
    fold_of_key = np.array([int(folds[k[0]]) for k in keys])
    # decisions for the endpoints
    kidx = {k: i for i, k in enumerate(keys)}
    rows = {}
    for tag, sel in (("core_%s" % t, ("Mstar", "B4", "B6", "B9")), ("a4n_%s" % t, None)):
        e_, D_ = A3.load_dec(RUN_DIR, tag)
        for a, v in K.dec_rows(D_, e_, kidx).items():
            if sel is None:
                rows[a] = v
            elif a in sel:
                rows["%s@0.05" % a] = v
        del D_
    n = len(keys)
    W = kw["W"]
    out = {"tracker": t, "seeds": {"bootstrap": sb, "power": sp}, "B": C.B_X3, "families": {}}
    vec_cache = {}
    for fi, fam in enumerate(FAMS):
        pts = family_points(fam)
        curve = []
        for p in pts:
            ns = neutral(acc[p], kw)
            ep, pk = A3.endpoints(*rows[p], n, W)
            vec_cache[p] = pk
            curve.append({"point": p, "neutral_in_sample": ns, "endpoints": {k: ep[k] for k in ("infeasible_rate", "progress_ratio", "mean_backoff_level", "V2_exec")}})
        choice, none_folds = {}, []
        for f in range(5):
            tr = fold_of_key != f
            pick = None
            for p in pts:
                if neutral(acc[p], kw, rows=tr)["passes"]:
                    pick = p
                    break
            choice[str(f)] = pick
            if pick is None:
                none_folds.append(f)
        best = next((c["point"] for c in curve if c["neutral_in_sample"]["passes"]), None)
        fr = {"grid_order": pts, "curve": curve, "choice_by_fold": choice, "in_sample_best_point": best}
        if none_folds:
            fr["result"] = "no matched point (no point passes on the training folds of fold(s) %s)" % none_folds
        else:
            comp_acc = np.zeros_like(acc[pts[0]])
            for f, p in choice.items():
                comp_acc[fold_of_key == int(f)] = acc[p][fold_of_key == int(f)]
            ns = neutral(comp_acc, kw)
            crow = A3.compose(rows, choice, fold_of_key)
            ep, pk = A3.endpoints(*crow, n, W)
            # registered screen of the composite (tables from the runs' counts, per fold's chosen point)
            T = registered_tables(t, keys, masks, choice, fold_of_key)
            v, st = SC.screen(T, kw, list(sp) + [300 + fi], "X3A4_%s_neutral_composite" % fam)
            fr.update({"result": "matched", "composite_neutral": ns, "composite_registered": SC.status_summary(st),
                       "composite_registered_class": reg_class(st),
                       "composite_endpoints": {k: ep[k] for k in ("infeasible_rate", "progress_ratio", "mean_backoff_level", "V2_exec")}})
            vec_cache["COMP_" + fam] = pk
            vec_cache["COMP_" + fam]["infeasible_rate"] = K.scene_mean(crow[0]["infeasible"], crow[1], n)
        out["families"][fam] = fr
        print("(A4 1) %s %s choice %s best %s %s" % (t, fam, choice, best, fr["result"]), flush=True)
        C.live("A4 (1) neutral %s %s" % (t, fam), fi + 1, len(FAMS))
    # M* (its own neutral-matched composite) minus each passing composite
    mres = out["families"]["Mstar"]
    if mres["result"] == "matched" and mres["composite_neutral"]["passes"]:
        for fam in FAMS[1:]:
            fr = out["families"][fam]
            if fr["result"] == "matched" and fr["composite_neutral"]["passes"]:
                fr["Mstar_minus_composite"] = {}
                for e in ("infeasible_rate", "progress_ratio", "V2_exec"):
                    r = K.wmean_ci(vec_cache["COMP_Mstar"][e] - vec_cache["COMP_" + fam][e], W)
                    fr["Mstar_minus_composite"][e] = {"mean_diff": r["mean"], "ci95": r["ci95"]}
    return out


def registered_tables(t, keys, masks, choice, fold_of_key):
    tabs = {}
    for tag, lab_map in (("core_%s" % t, {"Mstar": "Mstar@0.05", "B4": "B4@0.05", "B6": "B6@0.05", "B9": "B9@0.05"}), ("a4n_%s" % t, None)):
        eps, counts = SC.load_eps_counts(RUN_DIR, tag)
        ef = SC.entered(eps)
        need = sorted({p for p in choice.values()})
        labs = [a for a in need if (lab_map is None and a in {o["arm"] for o in ef})] if lab_map is None else [k for k, v in lab_map.items() if v in need]
        if labs:
            tt = SC.arm_tables(ef, counts, labs, keys, masks)
            for p in tt:
                for a, v in tt[p].items():
                    tabs.setdefault(p, {})[lab_map[a] if lab_map else a] = v
    T = {}
    for p in SC.POPS:
        N = np.zeros_like(next(iter(tabs[p].values()))[0])
        X = np.zeros_like(N)
        for f, a in choice.items():
            m = fold_of_key == int(f)
            N[m], X[m] = tabs[p][a][0][m], tabs[p][a][1][m]
        T[p] = (N, X)
    return T


def a_redo():
    am = json.load(open(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json")))
    out = {}
    for t, r in am["by_tracker"].items():
        out[t] = {}
        for fam, f in r["families"].items():
            cs = f["composite"]["status"]
            out[t][fam] = {"curve": [{"point": c["point"], "class": reg_class(c["in_sample"]), "infeasible_rate": c["infeasible_rate"]} for c in f["curve"]],
                           "composite_choice": {k: v["point"] for k, v in f["choice_by_fold"].items()}, "composite_class": reg_class(cs),
                           "composite_infeasible": f["composite"]["infeasible_rate"],
                           "Mstar_minus_composite": f["composite"]["Mstar_minus_composite"] if cs["valid"] else "no contrast: the composite does not pass"}
    return out


def md_neutral(r):
    L = ["# X3 A4 (1): matched validity on the neutral screen", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "Neutral screen: no flagged cell of P1-P7 in P_rel, P_near or P_ip (one-sided simultaneous 0.95 per partition and population, "
         ">= 39 logs) and HK1c (pooled upper bound at 0.995 <= 0.08) on each population; no power floor (evaluable partition cells "
         "counted). Selection per held-out fold on the other four folds; no point -> 'no matched point' (no conservative substitute). "
         "Seeds [20261201, i, 11] / [20261202, i, 11]; B = 4000.", ""]
    for t, x in r["by_tracker"].items():
        L += ["## %s" % t.upper(), "", "| family | per-fold choice | result | in-sample best | composite neutral | composite registered | infeasible | progress | mean back-off | V2_exec | M* - composite infeasible (95 % CI) |",
              "|---|---|---|---|---|---|---|---|---|---|---|"]
        for fam, f in x["families"].items():
            ce = f.get("composite_endpoints") or {}
            mm = (f.get("Mstar_minus_composite") or {}).get("infeasible_rate")
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                fam, ", ".join(str(f["choice_by_fold"][k]) for k in sorted(f["choice_by_fold"], key=int)), f["result"], f["in_sample_best_point"],
                (f.get("composite_neutral") or {}).get("passes", "-"), f.get("composite_registered_class", "-"),
                *(("%.4f" % ce[k]) if ce else "-" for k in ("infeasible_rate", "progress_ratio", "mean_backoff_level", "V2_exec")),
                ("%.4f [%.4f, %.4f]" % (mm["mean_diff"], mm["ci95"][0], mm["ci95"][1])) if mm else "-"))
        L += ["", "Every point (in-sample, all 375 logs): neutral pass / flagged cells / HK1c by population / evaluable partition cells; endpoints.", "",
              "| point | neutral pass | flagged cells | HK1c P_rel / P_near / P_ip (UB) | evaluable cells | infeasible | progress | mean back-off | V2_exec |",
              "|---|---|---|---|---|---|---|---|---|"]
        for fam, f in x["families"].items():
            for c in f["curve"]:
                ns, e = c["neutral_in_sample"], c["endpoints"]
                hk = " / ".join(("%s (%.3f)" % (v["holds"], v["ub"])) if v["ub"] is not None else "n.e." for v in ns["hk1c"].values())
                L.append("| %s | %s | %d | %s | %d | %.4f | %.4f | %.4f | %.4f |" % (c["point"], ns["passes"], ns["n_flagged"], hk, ns["evaluable_partition_cells"],
                                                                         e["infeasible_rate"], e["progress_ratio"], e["mean_backoff_level"], e["V2_exec"]))
        L.append("")
    L += ["## (a) re-read on the registered screen (classes: Valid / flagged / fails HK1c only / fails a floor only; contrasts only for passing composites)", ""]
    for t, x in r["a_redo"].items():
        for fam, f in x.items():
            L.append("- %s %s: composite %s -> %s (infeasible %.4f); %s; curve: %s" % (
                t.upper(), fam, f["composite_choice"], f["composite_class"], f["composite_infeasible"],
                ("M* - composite %.4f [%.4f, %.4f]" % (f["Mstar_minus_composite"]["mean_diff"], *f["Mstar_minus_composite"]["ci95"])) if isinstance(f["Mstar_minus_composite"], dict) else f["Mstar_minus_composite"],
                ", ".join("%s %s" % (c["point"].split("@")[1], c["class"]) for c in f["curve"])))
    return "\n".join(L) + "\n"


# ---------------------------------------------------------------- (3) and (5)
def simple_arms(t, tag, items, k, rec_compare):
    """items: [(label, screen_label, power suffix)]; registered-screen status, infeasible, progress, V2_exec."""
    masks = SC.setup()
    sb, sp = seeds(t, k)
    eps, counts = SC.load_eps_counts(RUN_DIR, tag)
    ef = SC.entered(eps)
    kw = SC.keys_W(ef, C.B_X3, sb)
    tabs = SC.arm_tables(ef, counts, [l_ for l_, _, _ in items], kw["keys"], masks)
    kidx = {kk: i for i, kk in enumerate(kw["keys"])}
    e_, D_ = A3.load_dec(RUN_DIR, tag)
    rows = K.dec_rows(D_, e_, kidx)
    del D_
    out = {}
    for lab, slab, suf in items:
        v, st = SC.screen(SC.T_of(tabs, lab), kw, list(sp) + suf, slab)
        ep, _ = A3.endpoints(*rows[lab], len(kw["keys"]), kw["W"])
        out[lab] = {"screen_label": slab, "registered": SC.status_summary(st), "registered_class": reg_class(st), "pooled": SC.pooled_numbers(v),
                    "endpoints": {kk: ep[kk] for kk in ("infeasible_rate", "progress_ratio", "mean_backoff_level", "V2_exec")},
                    "endpoints_ci95": {kk: ep["ci95"][kk] for kk in ("infeasible_rate", "progress_ratio", "V2_exec")}}
        print("(A4) %s %s %s infeasible %.4f" % (t, lab, out[lab]["registered_class"], ep["infeasible_rate"]), flush=True)
    return {"tracker": t, "seeds": {"bootstrap": sb, "power": sp}, "run": tag, "arms": out, "record": rec_compare}


def record_row(t, arm):
    import csv
    rows = {r["arm"]: r for r in csv.DictReader(open(os.path.join(A3.CSV_DIR, "k8_within_lt3d_%s_decide_arms.csv" % t)))}
    v2 = {(r["population"], r["arm"], r["variant"]): r for r in csv.DictReader(open(os.path.join(A3.CSV_DIR, "k8_within_lt3d_%s_decide_v2.csv" % t)))}
    an = json.load(open(os.path.join(C.REC, "c1_decision_r1.json")))
    del an
    return {"infeasible_rate": float(rows[arm]["infeasible_rate"]), "progress_ratio": float(rows[arm]["progress_ratio"]),
            "V2_exec": float(v2[("PD7_primary", arm, "V2_exec")]["E"]), "source": "c1_analysis_csv_r1 (record)"}


def ego():
    r = dict(stamp(), part="(3) ego footprint 4.9 x 1.9 m", by_tracker={})
    an = json.load(open(os.path.join(C.REC, "c1_analysis_r1.json")))
    for t in ("t1", "t3"):
        items = []
        for arm in ("Mstar", "B0", "B4", "B6"):
            suf = [] if arm == "Mstar" else [100 + K.ARM_INDEX[arm]]
            items.append(("%s_ego_4.9x1.9" % arm, arm, suf))
        rec = {arm: dict(record_row(t, arm), registered_valid=an["c1"]["within_lt3d"][t]["status"][arm]["valid"],
                         registered_shown_above=an["c1"]["within_lt3d"][t]["status"][arm]["shown_above"]) for arm in ("Mstar", "B0", "B4", "B6")}
        r["by_tracker"][t] = simple_arms(t, "a4ego_%s" % t, items, 3, rec)
    C.jdump(os.path.join(OUT, "x3_a4_3_ego_footprint_v01.json"), r)
    L = ["# X3 A4 (3): ego footprint 4.9 x 1.9 m", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "Decision mode, buffer 0.5 m unchanged; the default footprint through the same code path reproduces the record exactly (checks). "
         "Registered screen with the record's roles; seeds [20261201, i, 13] / [20261202, i, 13]; B = 4000.", ""]
    for t, x in r["by_tracker"].items():
        L += ["## %s" % t.upper(), "", "| arm | registered (4.9 x 1.9) | record status | infeasible 4.9 x 1.9 (record 4.1 x 1.8) | progress | V2_exec (record) |", "|---|---|---|---|---|---|"]
        for lab, v in x["arms"].items():
            arm = v["screen_label"]
            rc = x["record"][arm]
            L.append("| %s | %s | %s | %.4f (%.4f) | %.4f (%.4f) | %.4f (%.4f) |" % (arm, v["registered_class"], "Valid" if rc["registered_valid"] else ("shown above" if rc["registered_shown_above"] else "not valid"),
                                                                           v["endpoints"]["infeasible_rate"], rc["infeasible_rate"], v["endpoints"]["progress_ratio"], rc["progress_ratio"],
                                                                           v["endpoints"]["V2_exec"], rc["V2_exec"]))
        L.append("")
    C.wtext(os.path.join(OUT, "x3_a4_3_ego_footprint_v01.md"), "\n".join(L))


def tab():
    an = json.load(open(os.path.join(C.REC, "c1_analysis_r1.json")))
    rec = {arm: dict(record_row("tab", arm), registered_valid=an["c1"]["within_lt3d"]["tab"]["status"][arm]["valid"]) for arm in ("Mstar", "Z0")}
    del an
    x = simple_arms("tab", "a4tab", [("Mstar_matched_only", "Mstar", []), ("Z0_matched_only", "Z0", [100 + K.ARM_INDEX["Z0"]])], 5, rec)
    eps = [json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_a4tab.jsonl"))]
    x["dropped_unmatched_track_rows"] = int(sum(o.get("dropped_unmatched_track_rows", 0) for o in eps if o["arm"] == "Mstar_matched_only"))
    m_new, m_old = x["arms"]["Mstar_matched_only"]["endpoints"]["infeasible_rate"], rec["Mstar"]["infeasible_rate"]
    x["reading"] = ("the infeasible rate falls by more than half (%.4f -> %.4f): false-positive tracks are a main driver" % (m_old, m_new)
                    if m_new < 0.5 * m_old else "the infeasible rate does not fall by more than half (%.4f -> %.4f): the text drops the false-positive explanation" % (m_old, m_new))
    r = dict(stamp(), part="(5) AB3DMOT without unmatched tracks", by_tracker={"tab": x})
    C.jdump(os.path.join(OUT, "x3_a4_5_ab3dmot_matched_only_v01.json"), r)
    L = ["# X3 A4 (5): AB3DMOT without unmatched tracks", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "Every track row with tr_inst = -1 (no annotation match) removed from the planner's input after loading (%d track rows over 375 logs); "
         "matched tracks unchanged; decision mode; registered screen with the record's roles; seeds [20261201, 2, 15] / [20261202, 2, 15]." % x["dropped_unmatched_track_rows"], "",
         "| arm | infeasible (all tracks, record) | progress (record) | registered (record Valid) |", "|---|---|---|---|"]
    for lab, v in x["arms"].items():
        rc = rec[v["screen_label"]]
        L.append("| %s | %.4f (%.4f) | %.4f (%.4f) | %s (%s) |" % (lab, v["endpoints"]["infeasible_rate"], rc["infeasible_rate"], v["endpoints"]["progress_ratio"],
                                                              rc["progress_ratio"], v["registered_class"], rc["registered_valid"]))
    L += ["", "Reading (fixed by A4): " + x["reading"] + ".", ""]
    C.wtext(os.path.join(OUT, "x3_a4_5_ab3dmot_matched_only_v01.md"), "\n".join(L))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["spec", "check", "neutral", "ego", "tab"])
    a = ap.parse_args(argv)
    C.assert_run_log("A4 %s start" % a.cmd)
    SC.setup()
    t0 = time.time()
    if a.cmd == "spec":
        write_spec()
    elif a.cmd == "check":
        check()
    elif a.cmd == "neutral":
        r = dict(stamp(), part="(1) matched validity on the neutral screen", by_tracker={})
        for t in ("t1", "t3"):
            r["by_tracker"][t] = neutral_tracker(t)
            C.jdump(os.path.join(OUT, "x3_a4_1_neutral_v01.partial.json"), r)
        r["a_redo"] = a_redo()
        r["seconds"] = round(time.time() - t0, 1)
        C.jdump(os.path.join(OUT, "x3_a4_1_neutral_v01.json"), r)
        C.wtext(os.path.join(OUT, "x3_a4_1_neutral_v01.md"), md_neutral(r))
        try:
            os.remove(os.path.join(OUT, "x3_a4_1_neutral_v01.partial.json"))
        except FileNotFoundError:
            pass
    elif a.cmd == "ego":
        ego()
    elif a.cmd == "tab":
        tab()
    C.assert_run_log("A4 %s end" % a.cmd)


if __name__ == "__main__":
    main()
