#!/usr/bin/env python3
"""X3 round 2: analyses (d), (e2), (e1), (g) (x3-core agent, x3_analysis_r2_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan sections 2(d), 2(e), 2(g) and
amendment A2 (20_DESIGN/X3_PLAN_AMENDMENT_A2_v01.md).

Every arm is compared with M* of record in the same way: the registered screen as coded (x3_screen_v01: hk1_rule_criteria and
arm_status), each X3 arm judged like RETUNED-HK1 of record (labels outside K: flags at 0.95, power datasets 500), B = 4000; the
infeasible rate (per-log share, mean over logs) with its 95 % log-bootstrap interval; M* minus the arm (per-log paired difference,
percentile log bootstrap 95 % interval); the pooled relied-item exceedance per population (P_rel PD7, P_near SD1_7, P_ip PD).
M* of record is screened with the same seeds (label Mstar, power key = the analysis's power seed) as the reference row; its runs are
the X3 core runs, equal to the record by gate V0. Seeds (plan section 0): bootstrap [20261201, i, j], power [20261202, i, j],
j = 4 (d), 5 (e1 and e2), 7 (g); power-key suffix [100 + code] per arm.
Checks before any screen: (d) the d0 fits (x3-ref) drive arm Mstar to the run of record exactly (all 375 logs; decisions, counts,
calibration tables, episode summaries: x3_gates_v01.v0); (e2) substituting the cache's own covariance drives B0 to the run of record
exactly. A failed check stops that analysis, which is then reported as not done.
Commands: specs | b7test | check | screen
"""
import argparse
import json
import os
import sys
import time

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402

RUN_DIR = os.path.join(C.OUT, "runs")
DREF = os.path.join(C.OUT, "d_ref")
E2Q = os.path.join(C.OUT, "e2_qrefit")
OUTD = {"d": os.path.join(C.OUT, "d_ref_runs"), "e": os.path.join(C.OUT, "e_alternatives"), "g": os.path.join(C.OUT, "g_learning")}
G_N = (25, 50, 100, 200)
ARMS = {
    "d": [("X3D_Mstar_d0", "d0: logged arc length (= record; check)"), ("X3D_Mstar_d1", "d1: the planner's margin-0 plan (Z0)"),
          ("X3D_Mstar_d2", "d2: constant current speed")],
    "e2": [("X3E2_B0_cache_cov", "B0 on the cache's own covariance (check)"), ("X3E2_B0_qrefit", "Q-refit, plan grid"),
           ("X3E2_B0_qrefit_ext", "Q-refit, extended grid (amendment A2)")],
    "e1": [("X3E1_B5", "B5: per-axis CRC scalars"), ("X3E1_B8", "B8: stratified variance matching"), ("X3E1_B7", "B7: learned scale")],
}


def g_labels(t):
    out = []
    for n in G_N:
        for r in range(3):
            p = os.path.join(C.OUT, "g_learning", "fits", "fits_x3g_%s_n%d_r%d.json" % (t, n, r))
            out.append(("X3G_n%d_r%d" % (n, r), p, json.load(open(p))["fittable"]))
    return out


def write_specs(trackers):
    for t in trackers:
        sd = os.path.join(RUN_DIR, "specs")
        d = [{"label": "X3D_Mstar_%s" % r, "base": "Mstar", "fits": os.path.join(DREF, "fits_x3ref_%s_%s.json" % (r, t)), "cov_dir": None}
             for r in ("d0", "d1", "d2")]
        C.jdump(os.path.join(sd, "spec_d_%s_v01.json" % t), {"stamp": C.STAMP, "purpose": "(d) M* at references d0 (check), d1, d2", "variants": d})
        e2 = [{"label": "X3E2_B0_cache_cov", "base": "B0", "fits": None, "cov_dir": "self"},
              {"label": "X3E2_B0_qrefit", "base": "B0", "fits": None, "cov_dir": os.path.join(E2Q, "subst_%s" % t)},
              {"label": "X3E2_B0_qrefit_ext", "base": "B0", "fits": None, "cov_dir": os.path.join(E2Q, "subst_ext_%s" % t)}]
        C.jdump(os.path.join(sd, "spec_e2_%s_v01.json" % t), {"stamp": C.STAMP, "purpose": "(e2) B0's margin rule on substituted covariances", "variants": e2})
        fe = os.path.join(C.OUT, "e_alternatives", "fits")
        e1 = [{"label": "X3E1_B5", "base": "Mstar", "fits": os.path.join(fe, "fits_x3e1_B5_%s.json" % t), "cov_dir": None},
              {"label": "X3E1_B8", "base": "Mstar", "fits": os.path.join(fe, "fits_x3e1_B8_%s.json" % t), "cov_dir": None},
              {"label": "X3E1_B7", "base": "Mstar", "fits": os.path.join(fe, "fits_x3e1_B7_%s.json" % t), "cov_dir": None, "margin_rule": "B7"}]
        C.jdump(os.path.join(sd, "spec_e1_%s_v01.json" % t), {"stamp": C.STAMP, "purpose": "(e1) B5, B8 (per-L0 thresholds through Mstar's "
                                                                "margin form) and B7 (learned scale, margin rule B7)", "variants": e1})
        g = [{"label": lab, "base": "Mstar", "fits": p, "cov_dir": None} for lab, p, ok in g_labels(t) if ok]
        C.jdump(os.path.join(sd, "spec_g_%s_v01.json" % t), {"stamp": C.STAMP, "purpose": "(g) M* refitted on n training logs per fold",
                                                              "variants": g, "not_fittable": [lab for lab, p, ok in g_labels(t) if not ok]})
        print(t, "specs written; g variants", len(g))


def b7test(t):
    """The B7 margins of the runner (x3_run_v02's margins wrapper on k8_sim_v04.strata's outputs) equal the fit's own item-level
    margins c * exp(phi . beta) * sd for every item of three logs (the features are the same quantities in both places)."""
    import x3_run_v02 as RUN
    import x3_fits_r2_v01 as FR
    S = RUN.S
    RUN.install_wrapper()
    fits = json.load(open(os.path.join(C.OUT, "e_alternatives", "fits", "fits_x3e1_B7_%s.json" % t)))
    z = np.load(C.ITEMS_REC[t])
    names = [str(x) for x in z["scene_names"]]
    out, worst = {}, 0.0
    for scene in names[:3]:
        si = names.index(scene)
        fold = int(fits["fold_of_scene"][scene])
        fl = [fits["fits"][str(fold)][h] for h in RUN.STEPS]
        sc = S.Scene(os.path.join(C.CACHES[t], scene + ".npz"))
        rec = {k: z["rec_" + k][z["rec_s"] == si] for k in ("pair", "row")}
        row_of_pair = dict(zip(rec["pair"].tolist(), rec["row"].tolist()))
        it = {k: z["item_" + k][z["item_s"] == si] for k in ("k", "h", "a", "m", "g", "r", "sd", "pair", "inpath")}
        n_cmp = 0
        for k in sorted(set(it["k"].tolist())):
            rows = sc.tr_by_k[k]
            sp_, v_, w_ = S.sensor_ctrv(sc, k)
            g, r, m, sd, l0, ax = S.strata(sc, rows, k, sp_, v_, w_)
            RUN._CTX["b7"] = True
            mg = S.margins("Mstar", fl, g, r, sd, l0, sc.tr["inpath"][rows])
            RUN._CTX["b7"] = False
            pos = {int(rw): i for i, rw in enumerate(rows.tolist())}
            sel = np.flatnonzero(it["k"] == k)
            for q in sel:
                j = pos[row_of_pair[int(it["pair"][q])]]
                h, a_ = int(it["h"][q]), int(it["a"][q])
                assert abs(sd[j, h, a_] - it["sd"][q]) < 1e-12, "sd differs"
                beta, c = np.asarray(fl[h]["B7_beta_ip"]), np.asarray(fl[h]["B7_c_ip"])
                X = FR._lat_cols(RUN.b7_phi(0, it["m"][[q]], it["g"][[q]], it["r"][[q]], it["sd"][[q]], np.array([sc.tr["spd"][rows[j]]]),
                                            np.array([sc.tr["omc"][rows[j]]])), np.array([float(a_)]), it["m"][[q]], np.array([sc.tr["omc"][rows[j]]]))
                ip = int(it["inpath"][q])
                ref = c[ip] * np.exp(X[0] @ beta[ip]) * it["sd"][q]
                worst = max(worst, abs(ref - mg[j, h, a_]) / ref)
                n_cmp += 1
        out[scene] = n_cmp
    res = {"stamp": C.STAMP, "tracker": t, "items_compared": out, "max_relative_difference": worst, "passed": bool(worst < 1e-9)}
    C.jdump(os.path.join(C.OUT, "e_alternatives", "x3_e1_b7_margin_check_%s_v01.json" % t), res)
    print("B7 margin check", t, res["items_compared"], worst, res["passed"])
    return res


def check(analysis, t):
    """(d): X3D_Mstar_d0 == Mstar of record; (e2): X3E2_B0_cache_cov == B0 of record (x3_gates_v01.v0, exact)."""
    import x3_gates_v01 as GV
    lab, rec_arm, tag = {"d": ("X3D_Mstar_d0", "Mstar", "d_%s" % t), "e2": ("X3E2_B0_cache_cov", "B0", "e2_%s" % t)}[analysis]
    rec = GV.load_outputs(C.REC_RUNS, "%s_decide" % C.TAG_REC[t])
    mine = GV.load_outputs(RUN_DIR, tag)
    mine["eps"] = [dict(o, arm=rec_arm) if o["arm"] == lab else dict(o, arm="__" + o["arm"]) for o in mine["eps"]]
    for o in mine["eps"]:
        o.pop("cov_dir", None)
        o.pop("margin_rule", None)
    r = GV.v0(rec, mine, [rec_arm])[rec_arm]
    res = {"stamp": C.STAMP, "analysis": analysis, "tracker": t, "x3_arm": lab, "record_arm": rec_arm, "scenes": r["scenes"], "detail": r,
           "passed": bool(r["equal"] and r["scenes"] == 375)}
    C.jdump(os.path.join(OUTD["d" if analysis == "d" else "e"], "x3_check_%s_%s_v01.json" % (analysis, t)), res)
    print("check", analysis, t, res["passed"])
    return res


def screen_tracker(t, analysis, labels, code0=0):
    import x3_screen_v01 as SC
    masks = SC.setup("within_lt3d")
    jkey = {"d": "d", "e2": "e", "e1": "e", "g": "g"}[analysis]
    sb, sp = C.x3_seeds(t, jkey)
    eps_c, counts_c = SC.load_eps_counts(RUN_DIR, "core_%s" % t)
    ef_c = SC.entered(eps_c)
    kw = SC.keys_W(ef_c, C.B_X3, sb)
    tabs = SC.arm_tables(ef_c, counts_c, ["Mstar"], kw["keys"], masks)
    rate = {"Mstar": SC.infeasible_rates(ef_c, kw["scenes"])["Mstar"]}
    del counts_c
    tag = "%s_%s" % (analysis, t)
    eps_a, counts_a = SC.load_eps_counts(RUN_DIR, tag)
    ef_a = SC.entered(eps_a)
    assert sorted({(o["scene"], o["delay_kf"]) for o in ef_a}) == kw["keys"]
    ta = SC.arm_tables(ef_a, counts_a, [l for l, _ in labels], kw["keys"], masks)
    for p in tabs:
        tabs[p].update(ta[p])
    ra = SC.infeasible_rates(ef_a, kw["scenes"])
    del counts_a, ta
    Ws = kw["Ws"]

    def one(label, pk, code_):
        t1 = time.time()
        v, st = SC.screen(SC.T_of(tabs, label), kw, pk, label)
        bm = (Ws @ rate[label]) / Ws.sum(1)
        r = {"label": label, "power_key": pk, "status": SC.status_summary(st), "pooled": SC.pooled_numbers(v),
             "infeasible_rate": float(rate[label].mean()), "infeasible_ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
             "seconds": round(time.time() - t1, 1)}
        if label != "Mstar":
            r["Mstar_minus_arm"] = SC.paired(rate, Ws, "Mstar", label)
        print("(%s) %s %s valid %s shown %s infeasible %.4f" % (analysis, t, label, st["valid"], st["shown_above"], r["infeasible_rate"]), flush=True)
        return r
    out = {"tracker": t, "seeds": {"bootstrap": sb, "power": sp}, "B": C.B_X3, "run": tag,
           "run_record_sha256": C.sha256(os.path.join(RUN_DIR, "run_record_%s.json" % tag)), "arms": {}}
    out["arms"]["Mstar"] = one("Mstar", list(sp), None)
    for ci, (label, desc) in enumerate(labels):
        rate[label] = ra[label]
        out["arms"][label] = dict(one(label, list(sp) + [100 + code0 + ci], code0 + ci), description=desc)
    return out


def fmt_pool(pooled):
    return " / ".join("%.4f" % (pooled[p]["E"] if pooled[p]["E"] is not None else float("nan")) for p in ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath"))


def failing(st):
    return "; ".join("%s: %s" % (p.split("_")[0], ",".join(k for k in ("NoFlag", "NoFlag_pool", "Floor", "HK1c") if not q[k]) + (",FamFlag" if q["FamFlag"] else ""))
                     for p, q in st["pops"].items() if not q["valid"]) or "-"


def md_table(res_t):
    L = ["| arm | Valid | shown above | failing | infeasible (95 % CI) | M* - arm (95 % CI) | pooled exceedance P_rel / P_near / P_ip |",
         "|---|---|---|---|---|---|---|"]
    for lab, r in res_t["arms"].items():
        pr = r.get("Mstar_minus_arm")
        L.append("| %s | %s | %s | %s | %.4f [%.4f, %.4f] | %s | %s |" % (
            lab + ((" (" + r["description"] + ")") if r.get("description") else " (M* of record)"), r["status"]["valid"], r["status"]["shown_above"],
            failing(r["status"]), r["infeasible_rate"], r["infeasible_ci95"][0], r["infeasible_ci95"][1],
            ("%.4f [%.4f, %.4f]" % (pr["mean_diff"], pr["ci95"][0], pr["ci95"][1])) if pr else "-", fmt_pool(r["pooled"])))
    return L


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["specs", "b7test", "check", "screen"])
    ap.add_argument("--analysis", choices=["d", "e2", "e1", "g", "e"])
    ap.add_argument("--trackers", nargs="+", default=["t1", "t3"])
    a = ap.parse_args(argv)
    C.assert_run_log("r2 %s start" % a.cmd)
    if a.cmd == "specs":
        write_specs(a.trackers)
    elif a.cmd == "b7test":
        for t in a.trackers:
            assert b7test(t)["passed"], "X3 STOP (e1 B7): runner margins differ from the fit's"
    elif a.cmd == "check":
        ok = all(check(a.analysis, t)["passed"] for t in a.trackers)
        if not ok:
            raise SystemExit("X3 STOP (%s): check failed" % a.analysis)
    else:
        t0 = time.time()
        if a.analysis in ("d", "g"):
            res = {"stamp": C.STAMP, "analysis": a.analysis, "plan_sha256": C.sha256(C.PLAN), "by_tracker": {}}
            for t in a.trackers:
                labels = ARMS["d"] if a.analysis == "d" else [(l_, "n = %s training logs per fold, repeat %s" % (l_.split("_")[1][1:], l_.split("_")[2][1:]))
                                                              for l_, p, ok in g_labels(t) if ok]
                res["by_tracker"][t] = screen_tracker(t, a.analysis, labels)
                if a.analysis == "d":
                    res["by_tracker"][t]["check_d0"] = json.load(open(os.path.join(OUTD["d"], "x3_check_d_%s_v01.json" % t)))["passed"]
                else:
                    res["by_tracker"][t]["not_fittable"] = [l_ for l_, p, ok in g_labels(t) if not ok]
                    res["by_tracker"][t]["fallback"] = {l_: json.load(open(p))["fallback"] for l_, p, ok in g_labels(t)}
                    f300 = json.load(open(os.path.join(C.OUT, "g_learning", "fits", "fits_x3g_%s_n300_r0.json" % t)))
                    res["by_tracker"][t]["n300"] = {"equals_record_fit": f300.get("check_vs_record"), "fallback": f300["fallback"],
                                                    "note": "n = 300 is M* of record (fit identical), screened as the reference row"}
        else:
            res = {"stamp": C.STAMP, "analysis": "e (e2 then e1)", "plan_sha256": C.sha256(C.PLAN),
                   "amendment_A2_sha256": C.sha256(os.path.join(C.W, "20_DESIGN", "X3_PLAN_AMENDMENT_A2_v01.md")), "by_tracker": {}}
            for t in a.trackers:
                r2 = screen_tracker(t, "e2", ARMS["e2"])
                r1 = screen_tracker(t, "e1", ARMS["e1"], code0=10)
                r1["arms"].pop("Mstar")
                r2["arms"].update(r1["arms"])
                r2["runs"] = [r2.pop("run"), r1["run"]]
                r2["check_e2"] = json.load(open(os.path.join(OUTD["e"], "x3_check_e2_%s_v01.json" % t)))["passed"]
                r2["q_tables"] = {k: json.load(open(os.path.join(E2Q, "subst%s_%s" % (s_, t), "MANIFEST.json")))["q_table"] for k, s_ in (("plan", ""), ("ext", "_ext"))}
                r2["b7_margin_check"] = json.load(open(os.path.join(OUTD["e"], "x3_e1_b7_margin_check_%s_v01.json" % t)))["passed"]
                res["by_tracker"][t] = r2
        res["seconds"] = round(time.time() - t0, 1)
        name = {"d": "x3_d_ref_runs_v01", "g": "x3_g_learning_v01", "e": "x3_e_alternatives_v01"}[a.analysis]
        od = OUTD[a.analysis]
        C.jdump(os.path.join(od, name + ".json"), res)
        C.wtext(os.path.join(od, name + ".md"), md(a.analysis, res))
    C.assert_run_log("r2 %s end" % a.cmd)


def md(analysis, res):
    title = {"d": "X3 analysis (d): M* at an I_k-measurable reference", "e": "X3 analysis (e): the obvious alternatives (e2 Q-refit, e1 B5 / B8 / B7)",
             "g": "X3 analysis (g): the learning curve of M*"}[analysis]
    L = ["# " + title, "", "**%s**" % C.STAMP, "",
         "Screen: the registered screen as coded, each arm judged like RETUNED-HK1 of record (flags at 0.95, power datasets 500); "
         "B = 4000; M* of record screened with the same seeds as the reference row. Infeasible rate: mean over logs of the per-log share; "
         "M* - arm: per-log paired difference, percentile log bootstrap. Pooled exceedance: the relied-item exceedance per population.", ""]
    if analysis == "d":
        L += ["References (x3-ref, 70_TESTS/X3_INTEGRITY_v01/X3_REF_REPORT_v01.md): d0 = logged arc length (as of record); d1 = arm Z0's "
              "chosen plan, leashed by the log (equal to d0 in 95.7 % / 96.4 % of decisions at 2 s); d2 = constant current speed. M* refitted on "
              "each reference's items by the frozen rule; decisions, leash and relied constraints as of record (the arm's own plan).", ""]
    if analysis == "e":
        L += ["e2: B0's margin rule (z_0.95 sd) on the substituted covariances A + q (S - A) of x3-ref (plan grid; amendment A2's extended "
              "grid with q = 0). e1: B5, B8, B7 fitted by m_lib_v04's rules (exact CRC; per step and in-path part as M*); B5 and B8 run "
              "through k8_sim_v04's per-(L0, in-path) threshold x sd form, B7 through x3_run_v02's margin rule B7.", ""]
    for t, r in res["by_tracker"].items():
        L += ["## %s" % t.upper(), ""]
        if analysis == "d":
            L += ["Check: d0 fits reproduce M* of record exactly (375 logs): **%s**." % r["check_d0"], ""]
        if analysis == "e":
            L += ["Check: B0 on the cache's own covariance reproduces B0 of record exactly (375 logs): **%s**. B7 runner margins equal the "
                  "fit's item-level margins: **%s**." % (r["check_e2"], r["b7_margin_check"]), "",
                  "q (fold x group car / pedestrian / two-wheeler / large), plan grid: %s; extended grid: %s." % (
                      json.dumps(r["q_tables"]["plan"]), json.dumps(r["q_tables"]["ext"])), ""]
        L += md_table(r)
        if analysis == "g":
            L += ["", "Fallback (share of the 192 x 4 thresholds per fold whose source is coarser than the own L0 stratum, mean over folds; "
                  "n = 300 = the fit of record, identical: %s, share %.3f):" % (r["n300"]["equals_record_fit"], r["n300"]["fallback"]["share_coarser_than_L0"]), "",
                  "| composite | fallback share | undefined share |", "|---|---|---|"]
            for l_, fb in r["fallback"].items():
                L.append("| %s | %.3f | %.3f |" % (l_, fb["share_coarser_than_L0"], fb["share_undefined"]))
            if r["not_fittable"]:
                L.append("")
                L.append("Not fittable (a threshold with no level of 19 logs), not run: %s." % ", ".join(r["not_fittable"]))
        L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    main()
