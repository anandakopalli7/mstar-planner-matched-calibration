#!/usr/bin/env python3
"""c1crit_rstar2_summary_v03 (5 Nov 2026): combines the checkpoints of c1crit_rstar2_v03 (C3, E3, A3, D3) into
60_RESULTS/c1_criteria_sensitivity_v03/rstar2_summary_v03.json. No new random draws; nuScenes development data only.
Usage: python -B c1crit_rstar2_summary_v03.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_rstar2_v03 as R3  # noqa: E402
import numpy as np  # noqa: E402

POPL = R3.POPL


def load(p):
    with open(p) as f:
        return json.load(f)


def e3(c3):
    out = {}
    for tag in C.TAGS:
        files = sorted(glob.glob(os.path.join(R3.OUT3, "E3_ckpt", "E3_%s_s*.json" % tag)))
        if not files:
            continue
        rs = [load(f) for f in files]
        prim = c3["trackers"][tag]
        Vp, VJp = prim["V_t"], prim["H3"]["V_J"]
        o = {"sets": len(rs), "V_t_primary": Vp, "V_J_primary": VJp,
             "share_V_t_differs": float(np.mean([r["V_t"] != Vp for r in rs])),
             "share_V_J_differs": float(np.mean([r["V_J"] != VJp for r in rs])),
             "share_valid_Mstar": float(np.mean([r["valid"] for r in rs])),
             "share_formB_met": float(np.mean([r["formB_met"] for r in rs])),
             "share_H10": float(np.mean([r["H10"] for r in rs])),
             "share_in_V_t": {c: float(np.mean([c in r["V_t"] for r in rs])) for c in C.COMPS},
             "share_in_V_J": {c: float(np.mean([c in r["V_J"] for r in rs])) for c in set(sum([r["V_J"] for r in rs], [])) | set(VJp)},
             "mc_se": {}, "margins": {}}
        se = o["mc_se"]
        for c in Vp:
            v = [r["formB_ub"].get(c) for r in rs if c in r["formB_ub"]]
            se["formB_ub|" + c] = {"primary": prim["formB"]["ub"][c], "sd": float(np.std(v, ddof=1)), "mean": float(np.mean(v)), "n": len(v)}
        for l in POPL:
            v = [r["hk1c_ub"][l] for r in rs]
            se["hk1c_ub|" + l] = {"primary": prim["arms"]["Mstar"]["pops"][l]["pooled_ub_at_L"], "sd": float(np.std(v, ddof=1)),
                                  "max": float(np.max(v)), "share_above_0.08": float(np.mean(np.array(v) > 0.08))}
        for k, pk in (("formC_ub", prim["formC"]["ub_0.975"]), ("H10_ni_ub", prim["H10"]["ni_ub_0.975"])):
            v = [r[k] for r in rs]
            se[k] = {"primary": pk, "sd": float(np.std(v, ddof=1)), "max": float(np.max(v))}
        v = [r["p_H3"] for r in rs]
        se["p_H3"] = {"primary": prim["H3"]["p_H3_doubled"], "sd": float(np.std(v, ddof=1)), "max": float(np.max(v)),
                      "share_pass": {al: float(np.mean([r["H3_passes"][al] for r in rs])) for al in rs[0]["H3_passes"]}}
        for c in VJp:
            v = [r["H3_ub_0.0125"][c] for r in rs if r.get("H3_ub_0.0125") and c in r["H3_ub_0.0125"]]
            if v:
                se["H3_ub_at_0.0125|" + c] = {"primary": prim["H3"]["ub_at_holm_level"]["%.5f" % 0.0125][c], "sd": float(np.std(v, ddof=1)), "n": len(v)}
        # margins of the comparators' removal (max over cells of t - q at the removal level; > 0 is a flag)
        for c in C.COMPS:
            for l in POPL:
                v = [r["max_t_minus_q"][c][l] for r in rs if r["max_t_minus_q"][c][l] is not None]
                if v:
                    o["margins"]["%s|%s" % (c, l)] = {"primary": prim["arms"][c]["pops"][l].get("max_t_minus_q"), "min": float(np.min(v)),
                                                      "median": float(np.median(v)), "share_flag": float(np.mean(np.array(v) > 0))}
        jl = {}
        for c in set(sum([list(r["J_lb_removal"]) for r in rs], [])):
            for l in POPL:
                v = [r["J_lb_removal"][c][l] for r in rs]
                jl["%s|%s" % (c, l)] = {"primary": prim["H3"]["joint"][c][l]["lb_removal"], "min": float(np.min(v)), "max": float(np.max(v))}
        o["joint_removal_lb"] = jl
        out[tag] = o
    return out


def d3():
    out = {}
    for var in ("plugin", "capped"):
        files = sorted(glob.glob(os.path.join(R3.OUT3, "D3_ckpt", "D3_%s_c*.json" % var)))
        if not files:
            continue
        rs = [load(f) for f in files]
        n = sum(r["reps"] for r in rs)
        w = lambda key: float(sum(r[key] * r["reps"] for r in rs) / n)  # noqa: E731
        o = {"chunks": len(rs), "sets": n, "boot": rs[0]["boot"], "P_H1": w("P_H1"), "P_H1_fails": 1 - w("P_H1"),
             "P_H1_without_floors": w("P_H1_without_floors_diagnostic"), "P_H2": w("P_H2"), "P_H10": w("P_H10"), "trackers": {}}
        for t in C.TAGS:
            g = {}
            for k in ("P_formB", "P_formA", "P_formC"):
                g[k] = float(sum(r[t][k] * r["reps"] for r in rs) / n)
            g["P_Mstar_failure_reason"] = {k: float(sum(r[t]["P_Mstar_failure_reason"][k] * r["reps"] for r in rs) / n)
                                           for k in rs[0][t]["P_Mstar_failure_reason"]}
            inV, beats = {}, {}
            for c in rs[0][t]["P_in_V_choice9"]:
                cnt = sum(r[t]["P_in_V_choice9"][c] * r["reps"] for r in rs)
                b = sum((r[t]["P_beats_given_in_V"][c] or 0) * r[t]["P_in_V_choice9"][c] * r["reps"] for r in rs)
                inV[c] = float(cnt / n)
                beats[c] = None if cnt == 0 else float(b / cnt)
            g["P_in_V"] = inV
            g["P_beats_given_in_V"] = beats
            fam = {}
            for l in POPL:
                vals = sum([r["Mstar_family_record"][t][l] for r in rs], [])
                sz = np.array([v[0] for v in vals], float)
                sh = np.array([np.nan if v[1] is None else v[1] for v in vals], float)
                fam[l] = {"median": float(np.median(sz)), "p10": float(np.quantile(sz, 0.1)), "P_ge_6": float(np.mean(sz >= 6)),
                          "share_median": float(np.nanmedian(sh)), "share_p10": float(np.nanquantile(sh, 0.1))}
            g["Mstar_family"] = fam
            o["trackers"][t] = g
        out[var] = o
    return out


def main():
    c3 = load(os.path.join(R3.OUT3, "C3_verdict_rstar2_v03.json"))
    a3 = {t: load(p) for t in C.TAGS for p in [os.path.join(R3.OUT3, "A3_ckpt", "A3_%s.json" % t)] if os.path.exists(p)}
    res = {"stamp": "c1crit_rstar2_summary_v03: nuScenes development data only", "E3": e3(c3), "D3": d3(),
           "A3": {t: v["cells"] for t, v in a3.items()}}
    C.jdump(os.path.join(R3.OUT3, "rstar2_summary_v03.json"), res)
    print("SUMMARY V03 WRITTEN")


if __name__ == "__main__":
    main()
