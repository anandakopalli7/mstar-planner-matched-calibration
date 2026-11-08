#!/usr/bin/env python3
"""X3 analysis (a): matched-validity operability (x3-core agent, x3_analysis_a_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan sections 0 and 2(a).

Families B4, B6, B9: each refitted by the frozen fit rule at delta' in GRID (x3_fits_v01; delta' = 0.05 is the arm of record and is
taken from the X3 core run, which V0 showed equal to the run of record), run in decision mode by x3_run_v01 (variant label
'<family>@<delta'>'), on T1 and T3. Per family and tracker:
  * the whole curve: each fittable grid point's in-sample status (the screen on all 375 logs, B = 4000) and infeasible rate;
  * the cross-fitted matched-validity selection: grid ordered from least to most conservative (GRID order, delta' decreasing); for
    each held-out fold f the first point Valid on the other four folds' logs (c1_analyse_v02.retuned_hk1's rule with this explicit
    order), applied to fold f; if none, the most conservative fittable point, flagged;
  * the composite's status (B = 4000) and infeasible rate on all 375 logs, exactly as RETUNED-HK1 of record; M* minus the
    composite: per-log paired difference, percentile log bootstrap 95 % interval (B = 4000).
Every grid point and composite is judged as RETUNED-HK1 and the sweep points of record are (labels outside K: flags at 0.95, M*'s
level, and the descriptive power-dataset count 500). Seeds: bootstrap [20261201, i, 1], power [20261202, i, 1]; power-key suffixes
[100 + code] in-sample, [200 + code, f] in the selection, [300 + family index] for the composite; code = 10 x family index (B4 0,
B6 1, B9 2) + the grid index of delta'. The B0 family is reported from the record (RETUNED-HK1), not re-run.
Commands: specs (write the run specs from the fits summaries), screen (after the runs).
"""
import argparse
import json
import os
import sys
import time

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_screen_v01 as SC  # noqa: E402
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

GRID = (0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005, 0.0025, 0.001)
FAMILIES = ("B4", "B6", "B9")
FIT_KEY = {"B4": "B4", "B6": "B6_ip", "B9": "B9"}
ADIR = os.path.join(C.OUT, "a_matched")
FITS_DIR = os.path.join(ADIR, "fits")
RUN_DIR = os.path.join(C.OUT, "runs")


def label(fam, d):
    return "%s@%s" % (fam, repr(d))


def code(fam, d):
    return 10 * FAMILIES.index(fam) + GRID.index(d)


def fittable(t):
    s = json.load(open(os.path.join(FITS_DIR, "fits_x3a_%s_summary.json" % t)))
    return {fam: [d for d in GRID if s["by_delta_prime"][repr(d)]["fittable"][FIT_KEY[fam]]] for fam in FAMILIES}, s


def write_specs(trackers):
    out = {}
    for t in trackers:
        fit, s = fittable(t)
        assert s["by_delta_prime"]["0.05"]["check_vs_record"]["all_equal"], "delta' = 0.05 does not reproduce the fits of record"
        vs = []
        for fam in FAMILIES:
            for d in fit[fam]:
                if d == 0.05:
                    continue
                vs.append({"label": label(fam, d), "base": fam, "fits": os.path.join(FITS_DIR, "fits_x3a_%s_d%s.json" % (t, repr(d))), "cov_dir": None})
        p = os.path.join(RUN_DIR, "specs", "spec_a_%s_v01.json" % t)
        C.jdump(p, {"stamp": C.STAMP, "purpose": "analysis (a): B4, B6, B9 refitted at delta' (fittable points other than 0.05)", "variants": vs})
        out[t] = {"spec": p, "variants": len(vs), "fittable": {f: [repr(d) for d in v] for f, v in fit.items()}}
    print(json.dumps(out, indent=1))


def analyse_tracker(t, B_sel):
    masks = SC.setup("within_lt3d")
    sb, sp = C.x3_seeds(t, "a")
    fit, _ = fittable(t)
    eps_c, counts_c = SC.load_eps_counts(RUN_DIR, "core_%s" % t)
    eps_a, counts_a = SC.load_eps_counts(RUN_DIR, "a_%s" % t)
    ef_c, ef_a = SC.entered(eps_c), SC.entered(eps_a)
    kw = SC.keys_W(ef_c, C.B_X3, sb)
    assert sorted({(o["scene"], o["delay_kf"]) for o in ef_a}) == kw["keys"], "the (a) run's keys differ from the core run's"
    tabs = SC.arm_tables(ef_c, counts_c, list(FAMILIES), kw["keys"], masks)
    tabs = {p: {label(f, 0.05): tabs[p][f] for f in FAMILIES} for p in tabs}
    la = sorted({o["arm"] for o in ef_a})
    ta = SC.arm_tables(ef_a, counts_a, la, kw["keys"], masks)
    for p in tabs:
        tabs[p].update(ta[p])
    del counts_c, counts_a, ta
    rc = SC.infeasible_rates(ef_c, kw["scenes"])
    ra = SC.infeasible_rates(ef_a, kw["scenes"])
    rate = {"Mstar": rc["Mstar"]}
    rate.update({label(f, 0.05): rc[f] for f in FAMILIES})
    rate.update(ra)
    folds = json.load(open(C.FOLDS))["fold_of_log"]
    fold_of_key = np.array([int(folds[k[0]]) for k in kw["keys"]])
    Ws = kw["Ws"]
    out = {"tracker": t, "seeds": {"bootstrap": sb, "power": sp}, "B": C.B_X3, "B_selection": B_sel or C.B_X3,
           "Mstar_infeasible_rate": float(rate["Mstar"].mean()), "families": {}}
    for fi, fam in enumerate(FAMILIES):
        pts = [label(fam, d) for d in fit[fam]]
        not_fit = [repr(d) for d in GRID if d not in fit[fam]]
        cur = []
        for d in fit[fam]:
            a = label(fam, d)
            t1 = time.time()
            v, st = SC.screen(SC.T_of(tabs, a), kw, list(sp) + [100 + code(fam, d)], a)
            bm = (Ws @ rate[a]) / Ws.sum(1)
            cur.append({"point": a, "delta_prime": d, "in_sample": SC.status_summary(st), "pooled": SC.pooled_numbers(v),
                        "infeasible_rate": float(rate[a].mean()), "infeasible_ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
                        "Mstar_minus_point": SC.paired(rate, Ws, "Mstar", a), "seconds": round(time.time() - t1, 1)})
            print("(a) %s %s in-sample valid %s shown %s infeasible %.3f  %.0f s" % (t, a, st["valid"], st["shown_above"], rate[a].mean(), time.time() - t1), flush=True)
        t1 = time.time()
        choice, arm_of_key, Tc, trace = SC.crossfit(tabs, pts, fold_of_key, kw, sp, {a: code(fam, float(a.split("@")[1])) for a in pts}, B_sel=B_sel)
        comp = "X3A_%s_composite" % fam
        v, st = SC.screen(Tc, kw, list(sp) + [300 + fi], comp)
        rate[comp] = np.array([rate[a][ii] for ii, a in enumerate(arm_of_key)])
        out["families"][fam] = {
            "grid_fittable": [repr(d) for d in fit[fam]], "grid_not_fittable": not_fit, "order": pts, "curve": cur,
            "choice_by_fold": choice, "selection_trace": trace, "selection_seconds": round(time.time() - t1, 1),
            "composite": {"label": comp, "status": SC.status_summary(st), "pooled": SC.pooled_numbers(v),
                          "infeasible_rate": float(rate[comp].mean()), "Mstar_minus_composite": SC.paired(rate, Ws, "Mstar", comp)}}
        print("(a) %s %s composite %s valid %s infeasible %.3f  selection %.0f s" % (t, fam, {f: c["point"] for f, c in choice.items()}, st["valid"],
                                                                              rate[comp].mean(), time.time() - t1), flush=True)
        C.live("(a) screen %s" % t, fi + 1, len(FAMILIES))
    return out


def b0_from_record():
    an = json.load(open(os.path.join(C.REC, "c1_analysis_r1.json")))
    out = {}
    for t in ("t1", "t3"):
        r = an["c1"]["within_lt3d"][t]["RETUNED_HK1"]
        out[t] = {"choice_by_fold": r["choice_by_fold"], "valid": r["status"]["valid"], "shown_above": r["status"]["shown_above"],
                  "infeasible_rate": r["infeasible_rate"], "Mstar_minus_RETUNED_HK1": {k: r["Mstar_minus_RETUNED_HK1"].get(k) for k in ("mean_diff", "ci95", "ub", "level")},
                  "source": "60_RESULTS/c1_av2_v01/c1_analysis_r1.json c1.within_lt3d.%s.RETUNED_HK1 (B = 40000; reported, not re-run)" % t}
    return out


def md(res):
    L = ["# X3 analysis (a): matched-validity operability", "", "**%s**" % C.STAMP, "",
         "Plan section 2(a). B4, B6 (B6_ip) and B9 refitted by the frozen fit rule at delta' (x3_fits_v01; n_min = ceil(1/delta') - 1), "
         "cross-fitted on the C1 folds, run in decision mode (x3_run_v01). Screen: the registered screen as coded (hk1_rule_criteria, "
         "arm_status), grid points and composites judged as RETUNED-HK1 of record (flags at 0.95, power datasets 500); B = 4000; seeds "
         "[20261201, i, 1] / [20261202, i, 1]. Selection: per held-out fold, the least conservative point Valid on the other four folds "
         "(B = %s in the selection); else the most conservative fittable point, flagged." % res["B_selection"], ""]
    for t, r in res["by_tracker"].items():
        L += ["## %s" % t.upper(), "", "M* infeasible rate %.4f." % r["Mstar_infeasible_rate"], "",
              "| family | per-fold choice (0..4) | none qualifies | composite Valid | composite shown above | composite infeasible | M* - composite (95 % CI) |",
              "|---|---|---|---|---|---|---|"]
        for fam, f in r["families"].items():
            ch = f["choice_by_fold"]
            c = f["composite"]
            pr = c["Mstar_minus_composite"]
            L.append("| %s | %s | %s | %s | %s | %.4f | %.4f [%.4f, %.4f] |" % (
                fam, ", ".join(ch[k]["point"].split("@")[1] for k in sorted(ch, key=int)), ", ".join(str(k) for k in sorted(ch, key=int) if ch[k]["none_qualifies"]) or "-",
                c["status"]["valid"], c["status"]["shown_above"], c["infeasible_rate"], pr["mean_diff"], pr["ci95"][0], pr["ci95"][1]))
        b0 = res["B0_family_from_record"][t] if t in res["B0_family_from_record"] else None
        if b0:
            L.append("| B0 (RETUNED-HK1 of record) | %s | %s | %s | %s | %.4f | %.4f [%.4f, %.4f] |" % (
                ", ".join(b0["choice_by_fold"][k]["arm"] for k in sorted(b0["choice_by_fold"], key=int)),
                ", ".join(k for k in sorted(b0["choice_by_fold"], key=int) if b0["choice_by_fold"][k]["none_qualifies"]) or "-",
                b0["valid"], b0["shown_above"], b0["infeasible_rate"], b0["Mstar_minus_RETUNED_HK1"]["mean_diff"],
                b0["Mstar_minus_RETUNED_HK1"]["ci95"][0], b0["Mstar_minus_RETUNED_HK1"]["ci95"][1]))
        L += ["", "Whole curve (in-sample, all 375 logs):", "", "| point | Valid | shown above | failing (per population) | infeasible (95 % CI) | M* - point |", "|---|---|---|---|---|---|"]
        for fam, f in r["families"].items():
            for c in f["curve"]:
                fails = "; ".join("%s: %s" % (p.split("_")[0], ",".join(k for k in ("NoFlag", "NoFlag_pool", "Floor", "HK1c") if not q[k]) + (",FamFlag" if q["FamFlag"] else ""))
                                  for p, q in c["in_sample"]["pops"].items() if not q["valid"]) or "-"
                L.append("| %s | %s | %s | %s | %.4f [%.4f, %.4f] | %.4f |" % (c["point"], c["in_sample"]["valid"], c["in_sample"]["shown_above"], fails,
                                                                           c["infeasible_rate"], c["infeasible_ci95"][0], c["infeasible_ci95"][1], c["Mstar_minus_point"]["mean_diff"]))
            if f["grid_not_fittable"]:
                L.append("| %s at delta' %s | not fittable (see JSON: not_fittable) | | | | |" % (fam, ", ".join(f["grid_not_fittable"])))
        L.append("")
    L += ["Not fittable: the frozen CRC rule gives no threshold when the calibration logs n satisfy 1/(n + 1) > delta' (300 logs per "
          "training split: delta' = 0.0025 needs n >= 399 and 0.001 needs n >= 999); details per fold and step in the fits summaries.", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["specs", "screen"])
    ap.add_argument("--trackers", nargs="+", default=["t1", "t3"])
    ap.add_argument("--b-selection", type=int, default=0, help="0: B = 4000 in the selection; else that B (plan: 2000 if one call > 60 s)")
    ap.add_argument("--out-dir", default=ADIR)
    a = ap.parse_args(argv)
    if a.cmd == "specs":
        write_specs(a.trackers)
        return
    t0 = time.time()
    C.assert_run_log("(a) start")
    res = {"stamp": C.STAMP, "analysis": "(a) matched validity", "plan_sha256": C.sha256(C.PLAN), "B_selection": a.b_selection or C.B_X3,
           "by_tracker": {}, "B0_family_from_record": b0_from_record(),
           "fits_summaries": {t: C.sha256(os.path.join(FITS_DIR, "fits_x3a_%s_summary.json" % t)) for t in a.trackers},
           "runs": {t: {"core": C.sha256(os.path.join(RUN_DIR, "run_record_core_%s.json" % t)), "a": C.sha256(os.path.join(RUN_DIR, "run_record_a_%s.json" % t))}
                    for t in a.trackers}}
    with heavy_lock("x3-core: (a) screen B=4000 and cross-fitted selection"):
        for t in a.trackers:
            res["by_tracker"][t] = analyse_tracker(t, a.b_selection or None)
            C.jdump(os.path.join(a.out_dir, "x3_a_matched_v01.partial.json"), res)
    res["seconds"] = round(time.time() - t0, 1)
    C.assert_run_log("(a) end")
    C.jdump(os.path.join(a.out_dir, "x3_a_matched_v01.json"), res)
    C.wtext(os.path.join(a.out_dir, "x3_a_matched_v01.md"), md(res))
    try:
        os.remove(os.path.join(a.out_dir, "x3_a_matched_v01.partial.json"))
    except FileNotFoundError:
        pass
    print("X3 (a) DONE %.0f s" % res["seconds"])


if __name__ == "__main__":
    main()
