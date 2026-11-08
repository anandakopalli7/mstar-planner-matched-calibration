#!/usr/bin/env python3
"""X3 amendment A5 (x3-core agent, x3_a5_v01, 7 Nov 2026). Added after review (amendment A5).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).
Amendment: 20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md (sha256 25f3bb65...). No new decision-mode or loop-mode run: A5 re-screens the runs
with partition counts of A4(1) (runs/a4n_<t>, runs/core_<t>; the M* refits at delta').

(1) The reduced neutral screen: A4(1)'s screen (x3_a4_v01.neutral: (b)'s flag rule at one-sided simultaneous 0.95 per partition and
    population over the evaluable cells, >= 39 logs, B = 4000; HK1c per population at 0.995 <= 0.08; no power floor) restricted to P2,
    P4, P5, P6, P7 (P1 track speed and P3 track age dropped). Families and grid as A4(1); cross-fitted selection; "no matched point"
    without substitute. Per family and tracker: per-fold choice, the composite's reduced and registered (x3_screen_v01, flags at 0.95
    as RETUNED-HK1) statuses, infeasible rate, progress ratio, mean back-off, V2, V2_exec, V2_viol, and M* (its own reduced-screen
    composite) minus the composite, infeasible rate, per-log paired, log-bootstrap 95 % interval. Seeds [20261201, i, 21] /
    [20261202, i, 21].
(2) For A4(1)'s screen (its own seeds [20261201, i, 11], reproduced here: the A4 selection is recomputed and checked equal to the
    A4 output) and for A5(1)'s, in sample and per fold: the flagged cells and HK1c failures at the grid point just less conservative
    than the matched point.
(3) For M*'s matched composite and every family's composite under A4(1) and A5(1), and for every in-sample grid point: V2, V2_exec,
    V2_viol (P_rel), infeasible rate, progress ratio, share of decisions with a minimum enforced gap < 1 m (k8_analyse_v04's definitions,
    x3_a3_v01.endpoints); intervals with seed [20261201, i, 23].
Usage: python -B x3_a5_v01.py
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import csv  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
import x3_screen_v01 as SC  # noqa: E402
import x3_a3_v01 as A3  # noqa: E402
import x3_a4_v01 as A4  # noqa: E402
import x3_run_v01 as RR  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

K, A, R = SC.K, SC.A, SC.R
LABEL = "added after review (amendment A5)"
OUT = os.path.join(C.OUT, "a5_review")
AMEND = os.path.join(C.W, "20_DESIGN", "X3_PLAN_AMENDMENT_A5_v01.md")
AMEND_SHA = "25f3bb65903cd250416d31cde6b898733cbb2e44169b882b36f3a0e64c906960"
PARTS_A4 = tuple(p for p in RR.PARTS if p != "P0_distance_range")
PARTS_A5 = ("P2_track_length", "P4_detection_score", "P5_ego_speed", "P6_gt_lidar_points", "P7_city")
SIX = ("V2", "V2_exec", "V2_viol", "infeasible_rate", "progress_ratio", "min_gap_share_lt_1m")
FAMS = A4.FAMS


def seeds(t, j):
    i = C.TRACKER_I[t]
    return [C.SEED_BOOT_X3, i, j], [C.SEED_POWER_X3, i, j]


def screen(acc6, kw, parts, rows=None):
    """A4(1)'s neutral screen (x3_a4_v01.neutral's arithmetic) on the given partitions; returns the pass flag, the flagged cells as
    (partition, cell, population), the HK1c per population and the evaluable partition cells."""
    W, sc, lg = kw["W"], kw["scene_of_ep"], kw["log_of_ep"]
    if rows is not None:
        W, sc, lg, acc6 = W[:, rows], sc[rows], lg[rows], acc6[rows]
    kwr = {"W": W, "scene_of_ep": sc, "log_of_ep": lg}
    nk = acc6.shape[0]
    flagged, n_eval = [], 0
    for pi, pn in enumerate(RR.PARTS):
        if pn not in parts:
            continue
        labels = RR.BIN_LABELS[pn]
        nb = len(labels)
        names = ["%s|%s" % (labels[b], ax) for b in range(nb) for ax in ("long", "lat")]
        for p, c4 in A4.POP_C4.items():
            sub = acc6[:, list(c4), pi, :nb, :, :].sum(1)
            r = SC.partition_screen(sub[..., 0].reshape(nk, nb * 2), sub[..., 1].reshape(nk, nb * 2), kwr, names)
            n_eval += len(r["evaluable"])
            flagged += [[pn, c, p] for c in r["flagged"]]
    one = np.ones((1, nk))
    hk = {}
    for p, c4 in A4.POP_C4.items():
        Np = acc6[:, :, 0, :, :, 0][:, list(c4)].sum((1, 2, 3))[:, None]
        Xp = acc6[:, :, 0, :, :, 1][:, list(c4)].sum((1, 2, 3))[:, None]
        if not A.evaluable(Np, sc, lg)[0]:
            hk[p] = {"evaluable": False, "ub": None, "holds": False}
            continue
        e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
        _, ub, _, _, _ = A.flag(e1, b1, np.array([0]), R.HK1C_LEVEL)
        hk[p] = {"evaluable": True, "E": float(e1[0]), "ub": float(ub[0]), "holds": bool(ub[0] <= C.DELTA + R.HK1C_MARGIN)}
    return {"passes": bool(not flagged and all(v["holds"] for v in hk.values())), "flagged": flagged, "hk1c": hk,
            "hk1c_failing": [p for p, v in hk.items() if not v["holds"]], "evaluable_partition_cells": n_eval}


def load_tracker(t):
    ec = SC.entered([json.loads(l) for l in open(os.path.join(A4.RUN_DIR, "episodes_core_%s.jsonl" % t))])
    en = SC.entered([json.loads(l) for l in open(os.path.join(A4.RUN_DIR, "episodes_a4n_%s.jsonl" % t))])
    keys = sorted({(o["scene"], o["delay_kf"]) for o in ec})
    assert sorted({(o["scene"], o["delay_kf"]) for o in en}) == keys
    acc = A4.acc_tables(ec, dict(np.load(os.path.join(A4.RUN_DIR, "parts_core_%s.npz" % t))), ["Mstar", "B4", "B6", "B9"], keys)
    acc = {"%s@0.05" % k: v for k, v in acc.items()}
    acc.update(A4.acc_tables(en, dict(np.load(os.path.join(A4.RUN_DIR, "parts_a4n_%s.npz" % t))), sorted({o["arm"] for o in en}), keys))
    kidx = {k: i for i, k in enumerate(keys)}
    rows = {}
    for tag, sel in (("core_%s" % t, ("Mstar", "B4", "B6", "B9")), ("a4n_%s" % t, None)):
        e_, D_ = A3.load_dec(A4.RUN_DIR, tag)
        for a, v in K.dec_rows(D_, e_, kidx).items():
            if sel is None:
                rows[a] = v
            elif a in sel:
                rows["%s@0.05" % a] = v
        del D_
    folds = json.load(open(C.FOLDS))["fold_of_log"]
    return ec, keys, acc, rows, np.array([int(folds[k[0]]) for k in keys])


def kw_seed(ec, sb):
    return SC.keys_W(ec, C.B_X3, sb)


def select(acc, pts, kw, parts, fold_of_key):
    curve = {p: screen(acc[p], kw, parts) for p in pts}
    choice, prev_flags = {}, {}
    for f in range(5):
        tr = fold_of_key != f
        pick, last = None, None
        for p in pts:
            s_ = screen(acc[p], kw, parts, rows=tr)
            if s_["passes"]:
                pick = p
                break
            last = (p, s_)
        choice[str(f)] = pick
        prev_flags[str(f)] = ({"point": last[0], "flagged": last[1]["flagged"], "hk1c_failing": last[1]["hk1c_failing"]} if (pick and last) else
                              {"point": None, "note": "matched at the least conservative grid point" if pick else "no matched point"})
    best = next((p for p in pts if curve[p]["passes"]), None)
    i_b = pts.index(best) if best else None
    prev_in = ({"point": pts[i_b - 1], "flagged": curve[pts[i_b - 1]]["flagged"], "hk1c_failing": curve[pts[i_b - 1]]["hk1c_failing"]}
               if (best and i_b > 0) else {"point": None, "note": "matched at the least conservative grid point" if best else "no point passes in sample"})
    return curve, choice, best, prev_flags, prev_in


def tracker(t):
    masks = SC.setup()
    ec, keys, acc, rows, fold_of_key = load_tracker(t)
    n = len(keys)
    kw4 = kw_seed(ec, seeds(t, 11)[0])
    kw5 = kw_seed(ec, seeds(t, 21)[0])
    sp5 = seeds(t, 21)[1]
    kw3 = kw_seed(ec, seeds(t, 23)[0])
    a4 = json.load(open(os.path.join(A4.OUT, "x3_a4_1_neutral_v01.json")))["by_tracker"][t]["families"]
    out = {"tracker": t, "families": {}, "points": {}, "check_A4_reproduced": {}}
    vec5 = {}
    # every grid point's six measures (point estimates: no dependence on the bootstrap)
    for fam in FAMS:
        for p in A4.family_points(fam):
            ep, _ = A3.endpoints(*rows[p], n, kw3["W"])
            out["points"][p] = {"family": fam, **{k: ep[k] for k in SIX}, "ci95": {k: ep["ci95"].get(k) for k in SIX}}
    for fi, fam in enumerate(FAMS):
        pts = A4.family_points(fam)
        res = {}
        for scr, parts, kw in (("A4", PARTS_A4, kw4), ("A5", PARTS_A5, kw5)):
            curve, choice, best, prev_flags, prev_in = select(acc, pts, kw, parts, fold_of_key)
            r = {"choice_by_fold": choice, "in_sample_best_point": best, "in_sample_pass": {p: curve[p]["passes"] for p in pts},
                 "flags_just_less_conservative": {"in_sample": prev_in, "by_fold": prev_flags}}
            for p in pts:
                out["points"][p]["%s_in_sample_pass" % scr] = curve[p]["passes"]
            if scr == "A4":
                out["check_A4_reproduced"][fam] = bool(choice == a4[fam]["choice_by_fold"] and best == a4[fam]["in_sample_best_point"])
            if all(choice.values()):
                crow = A3.compose(rows, choice, fold_of_key)
                ep3, _ = A3.endpoints(*crow, n, kw3["W"])
                r["composite_six"] = {k: ep3[k] for k in SIX}
                r["composite_six_ci95"] = {k: ep3["ci95"].get(k) for k in SIX}
                r["composite_mean_backoff"] = ep3["mean_backoff_level"]
                if scr == "A5":
                    comp = np.zeros_like(acc[pts[0]])
                    for f, p in choice.items():
                        comp[fold_of_key == int(f)] = acc[p][fold_of_key == int(f)]
                    r["composite_reduced_screen"] = screen(comp, kw5, PARTS_A5)
                    T = A4.registered_tables(t, keys, masks, choice, fold_of_key)
                    v, st = SC.screen(T, kw5, list(sp5) + [300 + fi], "X3A5_%s_reduced_composite" % fam)
                    r["composite_registered"] = SC.status_summary(st)
                    r["composite_registered_class"] = A4.reg_class(st)
                    vec5[fam] = K.scene_mean(crow[0]["infeasible"], crow[1], n)
                r["result"] = "matched"
            else:
                r["result"] = "no matched point (folds %s)" % [f for f, p in choice.items() if p is None]
            res[scr] = r
        out["families"][fam] = res
        print("(A5) %s %s A4 %s | A5 %s" % (t, fam, res["A4"]["choice_by_fold"], res["A5"]["choice_by_fold"]), flush=True)
        C.live("A5 %s %s" % (t, fam), fi + 1, len(FAMS))
    if "Mstar" in vec5:
        for fam in FAMS[1:]:
            if fam in vec5:
                r = K.wmean_ci(vec5["Mstar"] - vec5[fam], kw5["W"])
                out["families"][fam]["A5"]["Mstar_minus_composite_infeasible"] = {"mean_diff": r["mean"], "ci95": r["ci95"], "below_0": bool(r["ci95"][1] < 0)}
    return out


def md(r):
    L = ["# X3 A5: the neutral screen without P1 and P3", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "Reduced screen = A4(1)'s neutral screen on P2, P4, P5, P6, P7 (P1 track speed, P3 track age dropped) + HK1c per population; "
         "seeds [20261201, i, 21] / [20261202, i, 21]; B = 4000. Runs: runs/a4n_<t> and core_<t> (no new run). A4(1)'s selection is "
         "recomputed with its own seeds and checked equal to the A4 output: %s." % json.dumps({t: x["check_A4_reproduced"] for t, x in r["by_tracker"].items()}), "",
         "## (1) Matched validity on the reduced screen", "",
         "| tracker | family | per-fold choice | composite reduced | composite registered | infeasible | progress | mean back-off | V2 | V2_exec | V2_viol | M* - composite infeasible (95 % CI) |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for t, x in r["by_tracker"].items():
        for fam, f in x["families"].items():
            a5 = f["A5"]
            six = a5.get("composite_six") or {}
            mm = a5.get("Mstar_minus_composite_infeasible")
            L.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                t.upper(), fam, ", ".join(str(a5["choice_by_fold"][k]) for k in sorted(a5["choice_by_fold"], key=int)),
                (a5.get("composite_reduced_screen") or {}).get("passes", a5["result"]), a5.get("composite_registered_class", "-"),
                *(("%.4f" % six[k]) if six else "-" for k in ("infeasible_rate", "progress_ratio")),
                ("%.4f" % a5["composite_mean_backoff"]) if "composite_mean_backoff" in a5 else "-",
                *(("%.4f" % six[k]) if six else "-" for k in ("V2", "V2_exec", "V2_viol")),
                ("%.4f [%.4f, %.4f]" % (mm["mean_diff"], mm["ci95"][0], mm["ci95"][1])) if mm else "-"))
    L += ["", "Reading fixed by A5: %s" % r["reading"], "", "## (2) The flags that stop each family one grid point before its matched point", ""]
    for t, x in r["by_tracker"].items():
        for fam, f in x["families"].items():
            for scr in ("A4", "A5"):
                q = f[scr]["flags_just_less_conservative"]
                ins = q["in_sample"]
                fl = lambda d_: "; ".join("%s %s %s" % (a_.split("_")[0], b_, c_.split("_")[0]) for a_, b_, c_ in d_.get("flagged", [])) + (  # noqa: E731
                    (" | HK1c fails: %s" % ", ".join(d_["hk1c_failing"])) if d_.get("hk1c_failing") else "")
                L.append("- %s %s %s: matched in sample at %s; at %s: %s" % (t.upper(), fam, scr, f[scr]["in_sample_best_point"], ins.get("point"),
                                                                         fl(ins) if ins.get("point") else ins.get("note")))
                for fo, d_ in sorted(q["by_fold"].items(), key=lambda kv: int(kv[0])):
                    L.append("  - fold %s (matched %s): at %s: %s" % (fo, f[scr]["choice_by_fold"][fo], d_.get("point"), fl(d_) if d_.get("point") else d_.get("note")))
    L += ["", "## (3) Six exceedance and operability measures of the matched composites (k8_analyse_v04's definitions)", "",
          "| tracker | family | screen | V2 | V2_exec | V2_viol | infeasible | progress | min gap < 1 m |", "|---|---|---|---|---|---|---|---|---|"]
    for t, x in r["by_tracker"].items():
        for fam, f in x["families"].items():
            for scr in ("A4", "A5"):
                six = f[scr].get("composite_six")
                if six:
                    L.append("| %s | %s | %s | %s |" % (t.upper(), fam, scr, " | ".join("%.4f" % six[k] for k in SIX)))
    L += ["", "Every in-sample grid point: x3_a5_points_v01.csv (the same six measures, and the in-sample pass under each screen).", ""]
    return "\n".join(L)


def main():
    t0 = time.time()
    assert C.sha256(AMEND) == AMEND_SHA, "A5 amendment hash differs"
    C.assert_run_log("A5 start")
    os.makedirs(OUT, exist_ok=True)
    r = {"stamp": C.STAMP, "label": LABEL, "amendment_sha256": AMEND_SHA, "parts_A4": PARTS_A4, "parts_A5": PARTS_A5, "by_tracker": {}}
    with heavy_lock("x3-core: A5 reduced neutral screen (no runs)"):
        for t in ("t1", "t3"):
            r["by_tracker"][t] = tracker(t)
    below = {t: {fam: (x["families"][fam]["A5"].get("Mstar_minus_composite_infeasible") or {}).get("below_0") for fam in FAMS[1:]} for t, x in r["by_tracker"].items()}
    r["every_A5_interval_below_0"] = bool(all(v is True for d_ in below.values() for v in d_.values()))
    r["below_0_by_family"] = below
    r["reading"] = ("every M* - composite interval lies below 0 on both trackers: the back-off advantage on the neutral screen survives removing P1 and P3"
                    if r["every_A5_interval_below_0"] else
                    "not every interval lies below 0: the advantage is not robust to removing P1 and P3 for %s" % [
                        "%s %s" % (t, fam) for t, d_ in below.items() for fam, v in d_.items() if v is not True])
    r["seconds"] = round(time.time() - t0, 1)
    C.jdump(os.path.join(OUT, "x3_a5_reduced_screen_v01.json"), r)
    C.wtext(os.path.join(OUT, "x3_a5_reduced_screen_v01.md"), md(r))
    rows_ = []
    for t, x in r["by_tracker"].items():
        for p, v in x["points"].items():
            rows_.append({"stamp": C.STAMP, "label": LABEL, "tracker": t, "family": v["family"], "point": p, "A4_in_sample_pass": v.get("A4_in_sample_pass"),
                          "A5_in_sample_pass": v.get("A5_in_sample_pass"), **{k: v[k] for k in SIX}})
    p_csv = os.path.join(OUT, "x3_a5_points_v01.csv")
    with open(p_csv + ".tmp", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows_[0].keys()))
        w.writeheader()
        w.writerows(rows_)
    os.replace(p_csv + ".tmp", p_csv)
    C.assert_run_log("A5 end")
    print("A5 DONE %.0f s; every interval below 0: %s" % (r["seconds"], r["every_A5_interval_below_0"]))


if __name__ == "__main__":
    main()
