#!/usr/bin/env python3
"""r21_mcse_v01 (7 Nov 2026): R21's Monte Carlo error and seed-set stability of C1's decisive quantities (plan section 6.1,
Choice 53e; descriptive, the verdict is always the primary seed's).

For each route and tracker (one at a time) and each seed set s = 0..S (s = 0: the registered bootstrap seed [20261110, i, j]
under the criteria library's generator scheme, as R21's reference; s = 1..S: R21's own seeds [20261121, i, j, s], disjoint from
every registered seed), the same R21 statistics as r21_rederive_v01: every H1 flag, family flag, pooled LB and flag, floor and
HK1c bound; each comparator's removal statistic (max over its 9 conditions of LB - delta) and V_t; the Form B bounds (at the set's
own level and at the reference set's |V_t|); H4 (transfer route) and H3 (within route) p-values and V^J; cells with |t - q| < 0.2.
Families: --power fixed holds every family at the reference (the analysis's M* per-cell power and the comparators' families
recovered from the analysis's size and record share, else R21's own), so floors cannot move and only the flags move;
--power recompute redraws R21's power rule per set (power seed [20261122, i, j, s, arm, pop], first 500 rows of that set's
weights), so family sizes can change and every change is listed.
The summary gives, per decisive quantity, the empirical MC SE over sets 1..S, the Andrews-Buchinsky MC SE at the reference
set, and the share of sets under which each status equals the reference's (and the analysis's, if given).

Resumable: one checkpoint JSON per (route, tracker, set) in --ckpt-dir; an existing checkpoint is never recomputed.
Memory: --lowmem keeps the weights as int16 only (no float64 cache) and uses 2000-row chunks.

Usage: python -B r21_mcse_v01.py --config <cfg> [--analysis <c1_analysis.json>] --ckpt-dir <dir> --out <json> --md <md>
         [--sets 20] [--B 40000] [--power fixed|recompute] [--power-datasets 2000] [--routes within_lt3d,transfer_lt3d]
         [--trackers t1,t3] [--only within_lt3d/t1] [--lowmem] [--max-mem-mb 0] [--summary-only]
"""
import argparse
import glob
import json
import math
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r21_lib_v01 as L  # noqa: E402
import r21_rederive_v01 as RD  # noqa: E402
import numpy as np  # noqa: E402


def families_reference(data, W, route, an_rt, power_n, mem):
    """The reference families: analysis-based where possible (as r21_rederive_v01), else R21's own (power_n datasets)."""
    an_power = RD.analysis_mstar_power(an_rt) if an_rt else None
    notes = {}

    def family_fn(arm, pop, N, ev_names, own_power):
        if an_rt is None:
            return None
        if arm == "Mstar" and an_power is not None:
            notes["%s/%s" % (arm, pop)] = "analysis per-cell power"
            return an_power[pop]["family"]
        fam = RD.g(an_rt, "status", arm, "criteria", "families", pop)
        if not fam:
            return None
        f, note = RD.recover_family(N, ev_names, own_power, fam.get("family_size"), RD.fl(fam.get("record_share")))
        notes["%s/%s" % (arm, pop)] = note
        return f
    res = L.h1_route_tracker(data, W, route, family_fn=family_fn, power_n=power_n, mem=mem)
    fams = {arm: {p: res["arms"][arm][p].get("family", []) for p in L.POPS} for arm in res["arms"] if res["arms"][arm]}
    return fams, notes, res


def one_set(data, W, route, fams, power_mode, power_n, power_seed, mem):
    if power_mode == "fixed":
        res = L.h1_route_tracker(data, W, route, fixed_families=fams, want_power=False, mem=mem)
    else:
        res = L.h1_route_tracker(data, W, route, power_n=power_n, power_seed=power_seed, mem=mem)
    asm = L.assemble_h1(data, W, res, route)
    out = {"arms": {}, "V": asm["V"], "valid_Mstar": asm["valid_Mstar"], "met": asm["met"], "vacuous": asm["vacuous"],
           "removal_stat": asm["removal_stat_max_lb_minus_delta"], "removal_stat_mcse": asm["removal_stat_mcse"],
           "without_zero_se": {"V": asm["without_zero_se_removals"]["V"], "met": asm["without_zero_se_removals"]["met"]},
           "form_b": {c: {"ub": v["ub"], "ub_mcse": v["ub_mcse"], "p": v["p"], "level": v["level"]} for c, v in asm["form_b"]["vs"].items()},
           "form_b_p": asm["form_b"]["p"]}
    for arm, pops in res["arms"].items():
        if pops is None:
            continue
        out["arms"][arm] = {}
        for p in L.POPS:
            r = pops[p]
            s = r["status"]
            out["arms"][arm][p] = {
                "flagged": r["flagged"], "family_flagged": r.get("family_flagged", []), "family_size": s["family_size"],
                "family": r.get("family", []), "NoFlag": s["NoFlag"], "FamFlag": s["FamFlag"], "NoFlag_pool": s["NoFlag_pool"],
                "Floor": s["Floor"], "HK1c": s["HK1c"], "valid": s["valid"], "shown_above": s["shown_above"],
                "pooled_lb": r["pooled"].get("lb"), "pooled_lb_mcse": r["pooled"].get("lb_mcse"),
                "pooled_ub": r["pooled"].get("ub"), "pooled_ub_mcse": r["pooled"].get("ub_mcse"),
                "max_lb_minus_delta": r.get("max_lb_minus_delta"), "family_max_lb_minus_delta": r.get("family_max_lb_minus_delta"),
                "near_t_minus_q": r.get("near_t_minus_q", []), "family_near_t_minus_q": r.get("family_near_t_minus_q", [])}
    if route == "within_lt3d":
        h3 = L.h3_route_tracker(data, W)
        if h3.get("available", True):
            out["H3"] = {"VJ": h3["VJ"], "validJ": h3["validJ_method"], "p": h3["p"], "met_bound_form": h3["met_bound_form"],
                         "ub": {c: v["ub"] for c, v in h3["form"]["vs"].items()},
                         "ub_mcse": {c: v["ub_mcse"] for c, v in h3["form"]["vs"].items()}}
        out["H2"] = L.form_c(W, data)
    return out, asm


def fixed_level_bounds(data, W, route, V_ref):
    """Form B UBs at the reference set's |V_t| for every comparator of the reference V_t (the same quantity in every set)."""
    if not V_ref:
        return {}
    alpha = L.ALPHA_FOR / 2 if route == L.H4_ROUTE else L.ALPHA_FORM_B
    lev = 1 - alpha / len(V_ref)
    rm = data.inf("Mstar")
    out = {}
    for c in V_ref:
        r = L.paired(W, rm - data.inf(c), lev)
        out[c] = {"ub": r["ub"], "ub_mcse": r["ub_mcse"], "p": r["p"], "level": lev}
    return out


def run(a):
    mem = L.MemGuard(a.max_mem_mb)
    with open(a.config, encoding="utf-8") as f:
        cfg = json.load(f)
    routes_cfg = {r["name"]: r for r in cfg["routes"]}
    an = None
    if a.analysis:
        with open(a.analysis, encoding="utf-8") as f:
            an = json.load(f)
    os.makedirs(a.ckpt_dir, exist_ok=True)
    only = set(a.only.split(",")) if a.only else None
    for route in [r for r in a.routes.split(",") if r]:
        rc = routes_cfg[route]
        for t in [x for x in a.trackers.split(",") if x]:
            if only and "%s/%s" % (route, t) not in only:
                continue
            paths = {s: os.path.join(a.ckpt_dir, "mc_%s_%s_s%02d.json" % (route, t, s)) for s in range(a.sets + 1)}
            if all(os.path.exists(p) for p in paths.values()):
                L.log("all sets done (checkpoints)", route, t)
                continue
            L.log("load", route, t)
            data = L.RouteData(rc["runs"], rc["tags"][t], t, fits_path=rc["fits"].get(t), mem=mem)
            data.select_retuned()
            i, j = L.TRACKER_INDEX[t], L.ROUTE_INDEX[route]
            an_rt = RD.g(an, "c1", route, t) if an else None
            cache = 0 if a.lowmem else 160
            chunk = 2000 if a.lowmem else 4000
            # reference set 0: the registered seed (also fixes the families and V_ref)
            ref_path = paths[0]
            if os.path.exists(ref_path):
                with open(ref_path, encoding="utf-8") as f:
                    ref = json.load(f)
            else:
                t0 = time.time()
                W0 = L.Weights([L.SEED_BOOT, i, j], data.U, a.B, chunk=chunk, cache_mb=cache)
                fams, notes, _ = families_reference(data, W0, route, an_rt, a.ref_power_datasets, mem)
                ref, _ = one_set(data, W0, route, fams, "fixed", a.power_datasets, None, mem)
                ref["fixed_level_form_b"] = fixed_level_bounds(data, W0, route, ref["V"])
                ref.update({"set": 0, "seed": W0.seed, "B": a.B, "power_mode": "fixed (reference)", "families": fams,
                            "family_notes": notes, "seconds": time.time() - t0, "memory": L.memory_mb()})
                L.jdump(ref_path, ref)
                L.log(route, t, "set 0 (registered seed)", round(ref["seconds"], 1), "s")
                del W0
            for s in range(1, a.sets + 1):
                if os.path.exists(paths[s]):
                    continue
                t0 = time.time()
                W = L.Weights([L.R21_SEED_MC, i, j, s], data.U, a.B, chunk=chunk, cache_mb=cache)
                r, _ = one_set(data, W, route, ref["families"], a.power, a.power_datasets, [L.R21_SEED_POWER, i, j, s], mem)
                r["fixed_level_form_b"] = fixed_level_bounds(data, W, route, ref["V"])
                r.update({"set": s, "seed": W.seed, "B": a.B, "power_mode": a.power, "seconds": time.time() - t0,
                          "memory": L.memory_mb()})
                L.jdump(paths[s], r)
                L.log(route, t, "set", s, round(r["seconds"], 1), "s", {k: round(v) for k, v in r["memory"].items() if v})
                del W
            del data


# ------------------------------------------------------------------ summary
def summarise(a):
    an = None
    if a.analysis:
        with open(a.analysis, encoding="utf-8") as f:
            an = json.load(f)
    out = {"label": "R21 Monte Carlo error and seed-set stability (descriptive; plan section 6.1; the verdict is the primary seed's)",
           "B": a.B, "power_mode": a.power, "routes": {}}
    h1_sets = {}
    for route in [r for r in a.routes.split(",") if r]:
        for t in [x for x in a.trackers.split(",") if x]:
            files = sorted(glob.glob(os.path.join(a.ckpt_dir, "mc_%s_%s_s*.json" % (route, t))))
            if not files:
                continue
            sets = {}
            for fp in files:
                with open(fp, encoding="utf-8") as f:
                    o = json.load(f)
                sets[o["set"]] = o
            ref = sets.get(0)
            alt = [sets[k] for k in sorted(sets) if k >= 1]
            if ref is None:
                continue
            S = len(alt)
            res = {"n_sets": S, "reference_seed": ref["seed"], "alt_seeds": [o["seed"] for o in alt]}
            an_rt = RD.g(an, "c1", route, t) if an else None

            def stats(vals, ab=None):
                v = np.array([x for x in vals if x is not None], float)
                d = {"n": int(len(v))}
                if len(v):
                    d.update({"mean": float(v.mean()), "min": float(v.min()), "max": float(v.max())})
                if len(v) > 1:
                    d["mc_se_empirical"] = float(v.std(ddof=1))
                if ab is not None:
                    d["mc_se_andrews_buchinsky_ref"] = ab
                return d
            dq = {}
            # removal statistics
            for c in L.COMPS:
                dq["removal_stat %s" % c] = dict(stats([o["removal_stat"].get(c) for o in alt], ref["removal_stat_mcse"].get(c)),
                                                 reference=ref["removal_stat"].get(c))
            # Form B at the reference level
            for c, v in ref.get("fixed_level_form_b", {}).items():
                dq["Form B UB M* - %s (level %.6f)" % (c, v["level"])] = dict(
                    stats([o["fixed_level_form_b"].get(c, {}).get("ub") for o in alt], v["ub_mcse"]), reference=v["ub"])
                p = v["p"]
                dq["p_c M* - %s" % c] = dict(stats([o["fixed_level_form_b"].get(c, {}).get("p") for o in alt],
                                                   math.sqrt(max(p * (1 - p), 0) / a.B)), reference=p)
            # HK1c bounds (M*)
            for p in L.POPS:
                m = ref["arms"]["Mstar"][p]
                dq["HK1c UB M* %s" % p] = dict(stats([o["arms"]["Mstar"][p]["pooled_ub"] for o in alt], m.get("pooled_ub_mcse")),
                                               reference=m["pooled_ub"])
                dq["pooled LB M* %s" % p] = dict(stats([o["arms"]["Mstar"][p]["pooled_lb"] for o in alt], m.get("pooled_lb_mcse")),
                                                 reference=m["pooled_lb"])
            if route == L.H4_ROUTE:
                dq["H4 p (this tracker; doubled)"] = dict(stats([o["form_b_p"] for o in alt],
                                                                None), reference=ref["form_b_p"])
            if "H3" in ref:
                dq["H3 p (this tracker; doubled)"] = dict(stats([(o.get("H3") or {}).get("p") for o in alt]), reference=ref["H3"]["p"])
                for c, v in ref["H3"]["ub"].items():
                    dq["H3 UB M*Jx - %s (own level)" % c] = dict(stats([(o.get("H3") or {}).get("ub", {}).get(c) for o in alt],
                                                                        ref["H3"]["ub_mcse"].get(c)), reference=v)
            res["decisive_quantities"] = dq
            # status stability
            st = {}
            for arm in ["Mstar"] + L.COMPS:
                if arm not in ref["arms"]:
                    continue
                for p in L.POPS:
                    rr = ref["arms"][arm][p]
                    keys = ("NoFlag", "FamFlag", "NoFlag_pool", "Floor", "HK1c", "valid") if arm == "Mstar" else ("NoFlag", "FamFlag", "NoFlag_pool", "shown_above")
                    for k in keys:
                        same = sum(1 for o in alt if o["arms"].get(arm, {}).get(p, {}).get(k) == rr[k])
                        st["%s/%s %s" % (arm, p, k)] = {"reference": rr[k], "share_same": same / S if S else None,
                                                        "analysis": RD.g(an_rt, "status", arm, "pops", p, k) if an_rt else None}
                    sizes = sorted({o["arms"].get(arm, {}).get(p, {}).get("family_size") for o in alt} - {None})
                    if sizes != [rr["family_size"]]:
                        st["%s/%s family size" % (arm, p)] = {"reference": rr["family_size"], "values": sizes,
                                                              "by_set": [o["arms"].get(arm, {}).get(p, {}).get("family_size") for o in alt]}
            same_v = sum(1 for o in alt if sorted(o["V"]) == sorted(ref["V"]))
            st["V_t membership identical"] = {"reference": ref["V"], "share_same": same_v / S if S else None,
                                              "analysis": RD.g(an_rt, "form_b", "V") if an_rt else None,
                                              "differing_sets": {o["set"]: o["V"] for o in alt if sorted(o["V"]) != sorted(ref["V"])}}
            st["Form B met"] = {"reference": ref["met"], "share_same": sum(1 for o in alt if o["met"] == ref["met"]) / S if S else None}
            for c, v in ref.get("fixed_level_form_b", {}).items():
                st["Form B UB < 0 M* - %s" % c] = {"reference": v["ub"] < 0,
                                                   "share_same": sum(1 for o in alt if (o["fixed_level_form_b"].get(c, {}).get("ub", 1) < 0) == (v["ub"] < 0)) / S if S else None}
            if "H3" in ref:
                st["V^J membership identical"] = {"reference": ref["H3"]["VJ"],
                                                  "share_same": sum(1 for o in alt if sorted((o.get("H3") or {}).get("VJ", [])) == sorted(ref["H3"]["VJ"])) / S if S else None}
            res["stability"] = st
            # cells near the flag threshold
            near = {}
            for o in [ref] + alt:
                for arm, pops in o["arms"].items():
                    for p, rr in pops.items():
                        for kind in ("near_t_minus_q", "family_near_t_minus_q"):
                            for x in rr.get(kind) or []:
                                key = "%s/%s/%s %s" % (arm, p, x["cell"], "family" if kind.startswith("family") else "cells")
                                near.setdefault(key, []).append({"set": o["set"], "t": x["t"], "q": x["q"]})
            res["cells_t_minus_q_below_0.2"] = near
            res["seconds_per_set"] = stats([o.get("seconds") for o in alt])
            out["routes"]["%s/%s" % (route, t)] = res
            if route == "within_lt3d":
                h1_sets[t] = {o["set"]: o["met"] for o in [ref] + alt}
    if set(h1_sets) >= {"t1", "t3"}:
        common = sorted(set(h1_sets["t1"]) & set(h1_sets["t3"]))
        h1 = {s: bool(h1_sets["t1"][s] and h1_sets["t3"][s]) for s in common}
        alt = [s for s in common if s >= 1]
        out["H1_by_set"] = {"reference": h1.get(0), "share_same": (sum(1 for s in alt if h1[s] == h1.get(0)) / len(alt)) if alt else None,
                            "by_set": h1}
    return out


def write_md(path, out):
    lines = ["# R21 Monte Carlo error and seed stability", "",
             "Descriptive (plan section 6.1); the verdict is always the primary seed's. B = %s; power mode %s." % (out["B"], out["power_mode"]), ""]
    if out.get("H1_by_set"):
        lines.append("- H1 (bound form) at the reference set: %s; share of alternative sets with the same: %s" % (
            out["H1_by_set"]["reference"], out["H1_by_set"]["share_same"]))
    for rt, r in out["routes"].items():
        lines += ["", "## %s (%d sets)" % (rt, r["n_sets"]), ""]
        for k, v in r["decisive_quantities"].items():
            lines.append("- %s: reference %s; empirical MC SE %s; A-B MC SE %s; range [%s, %s]" % (
                k, _f(v.get("reference")), _f(v.get("mc_se_empirical")), _f(v.get("mc_se_andrews_buchinsky_ref")), _f(v.get("min")), _f(v.get("max"))))
        unstable = {k: v for k, v in r["stability"].items() if v.get("share_same") is not None and v["share_same"] < 1}
        lines.append("- statuses not identical in every set: %d; %s" % (len(unstable), json.dumps(unstable, default=str)[:3000]))
        sz = {k: v for k, v in r["stability"].items() if k.endswith("family size")}
        lines.append("- power-family size changes: %s" % (json.dumps(sz)[:2000] if sz else "none"))
        lines.append("- cells with |t - q| < 0.2: %s" % (", ".join("%s (%d sets)" % (k, len(v)) for k, v in r["cells_t_minus_q_below_0.2"].items()) or "none"))
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def _f(x):
    return "None" if x is None else ("%.6g" % x if isinstance(x, (int, float)) else str(x))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--analysis")
    ap.add_argument("--ckpt-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--md", required=True)
    ap.add_argument("--sets", type=int, default=20)
    ap.add_argument("--B", type=int, default=L.B_REGISTERED)
    ap.add_argument("--power", choices=("fixed", "recompute"), default="fixed")
    ap.add_argument("--power-datasets", type=int, default=2000, help="per set, in --power recompute")
    ap.add_argument("--ref-power-datasets", type=int, default=500, help="R21's own power at the reference set (family recovery)")
    ap.add_argument("--routes", default="within_lt3d,transfer_lt3d")
    ap.add_argument("--trackers", default="t1,t3")
    ap.add_argument("--only", default="", help="comma list of route/tracker to process in this call")
    ap.add_argument("--lowmem", action="store_true")
    ap.add_argument("--max-mem-mb", type=float, default=0.0)
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args(argv)
    for _p in (a.out, a.md):
        os.makedirs(os.path.dirname(os.path.abspath(_p)), exist_ok=True)
    t0 = time.time()
    if not a.summary_only:
        run(a)
    out = summarise(a)
    out["seconds_this_call"] = time.time() - t0
    out["memory"] = L.memory_mb()
    out["code_sha256"] = {os.path.basename(p): L.sha256(p) for p in (os.path.abspath(__file__), L.__file__, RD.__file__)}
    L.jdump(a.out, out)
    write_md(a.md, out)
    L.log("summary written", a.out, round(out["seconds_this_call"], 1), "s")


if __name__ == "__main__":
    main()
