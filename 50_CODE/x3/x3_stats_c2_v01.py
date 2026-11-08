#!/usr/bin/env python3
"""X3 analysis (c2), simulated false removal and coverage at Argoverse 2's cell sizes (x3-stats, v01, 7 Nov 2026). Plan 2(c2); M4.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)

Model (plan 2(c2)). Each dataset keeps the observed per-log record counts per cell; every cell's true rate is r_c (delta = 0.05, or
M*'s observed cell rate); per-log rates are drawn per cell from Beta with mean r_c and intraclass correlation rho_c (the ANOVA ICC of
the observed data in that cell, as (c1)(iii)), and exceedances are binomial given the per-log rate (beta-binomial).
  * False removal (every comparator removed from V_t in r1): truth delta in every cell. The three populations share records (P_near
    and P_ip are parts of P_rel), so each dataset is drawn on the four disjoint record blocks (far/near x not-in-path/in-path), with one
    rate per log and cell shared by the blocks, and the populations are their sums; rho_c from the comparator's P_rel cell.
    The record's comparator rule is applied at 1 - 0.0125/9 by sup-t with an inner log bootstrap of 1000 (fresh multinomial weights
    per dataset): cell flags over the evaluable cells, family flags over the record's power family, the pooled flag, per population.
    False removal = a flag in >= 1 of these 9 conditions (plan 6.2); the code of record also removes on an HK1c failure (pooled UB at
    0.995 above 0.08), reported alongside.
  * Coverage (M*): per population (coverage is a per-population property, so each population is drawn on its own layout), truth delta
    in every cell, or M*'s observed cell rates in that population; rho_c from M*'s cell in that population. Simultaneous coverage of
    M*'s one-sided 0.95 upper bounds over the evaluable cells (all cells covered), per-cell coverage, and coverage of the HK1c pooled
    upper bound at 0.995 (pooled truth = mean over logs of sum_c N_uc r_c / sum_c N_uc, the expectation of the estimator).
Methods: (i) the record's rule (pre-specified). Added beyond the plan and labelled so (not pre-specified): the same quantities under
(ii) the studentised bootstrap with the SE floor and (iii) the design-effect Wilson interval of (c1), and M*'s own flag rate (cell,
family or pooled LB at 0.95 above delta) when every cell is at delta, i.e. the size of the screen against M*.
Seeds: [20261201, i, 3] extended per scenario s and dataset d: numpy default_rng([20261201, i, 3, s, d]) draws the dataset and then
its 1000 inner bootstrap rows, so a resumed run reproduces a stopped one exactly. Scenario index s: 0 M* at delta, 1 M* at observed
rates, 2 + k for comparator k of (B0, B1, B3, B4, B6, B9, RETUNED).
Checkpoints: one new JSON per chunk of 50 datasets in <out-dir>/c2_ckpt_v01/; existing chunks are skipped on restart.
Run (heavy, inside the X3 heavy lock, one tracker at a time): python -B x3_stats_c2_v01.py --out-dir <c_intervals>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_stats_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

L = C.L
N_DATASETS = 1000
INNER_B = 1000
CHUNK = 50
SCEN_M_DELTA, SCEN_M_OBS = 0, 1
REMOVED_R1 = {"t1": ["B0", "B1", "B4", "B6", "B9", "RETUNED"], "t3": ["B1", "B4", "B6", "B9", "RETUNED"]}
METHODS = ("i", "ii", "iii")


class WArr:
    """Weights wrapper for C.Stud (rows as float64)."""

    def __init__(self, Wf):
        self.Wf = Wf
        self.B = Wf.shape[0]
        self.chunk = self.B

    def rows(self, s, e):
        return self.Wf[s:e]

    def rates(self, N, X):
        p = np.divide(X, N, out=np.zeros_like(X, dtype=np.float64), where=N > 0)
        pres = (N > 0).astype(np.float64)
        with np.errstate(invalid="ignore", divide="ignore"):
            return (self.Wf @ p) / (self.Wf @ pres)


def beta_rates(rng, r, rho, shape):
    """Per-log rates (U, J): Beta with mean r_c and ICC rho_c per column; rho = 0 gives r_c exactly."""
    r = np.asarray(r, np.float64)
    rho = np.clip(np.asarray(rho, np.float64), 0.0, 0.999)
    out = np.broadcast_to(r, shape).copy()
    m = (rho > 1e-9) & (r > 0) & (r < 1)
    if m.any():
        s = (1.0 - rho[m]) / rho[m]
        out[:, m] = rng.beta(r[m] * s, (1.0 - r[m]) * s, size=(shape[0], int(m.sum())))
    return out


def pooled_cols(N, X):
    return N.sum(1, keepdims=True), X.sum(1, keepdims=True)


# ------------------------------------------------------------------ the rules on one simulated table
def comparator_rules(N, X, ev, fam, Wa, level):
    """(i), (ii), (iii): cell flags over ev, family flags over fam, pooled flag at level, HK1c failure; returns per method a dict."""
    out = {}
    Np, Xp = pooled_cols(N, X)
    est, pe = L.point_rates(N, X), L.point_rates(Np, Xp)
    # (i)
    boot = Wa.rates(N, X)
    pb = Wa.rates(Np, Xp)
    rc = L.flag_cells(est, boot, ev, level)
    rf = L.flag_cells(est, boot, fam, level) if len(fam) else {"flag": np.zeros(0, bool)}
    rp = L.flag_cells(pe, pb, [0], level)
    up = L.supt(pe, pb, [0], C.L_HK1C, "upper")
    out["i"] = {"cell": [int(ev[k]) for k in np.flatnonzero(rc["flag"])], "family": [int(fam[k]) for k in np.flatnonzero(rf["flag"])],
                "pooled": bool(rp["flag"][0]), "hk1c_fail": bool(up["bound"][0] > C.DELTA + C.HK1C_MARGIN)}
    # (ii)
    S, Sp = C.Stud(N, X, Wa), C.Stud(Np, Xp, Wa)
    bc = S.bounds(ev, level, "lower")[0]
    bf = S.bounds(fam, level, "lower")[0] if len(fam) else np.zeros(0)
    bp = Sp.bounds([0], level, "lower")[0]
    bu = Sp.bounds([0], C.L_HK1C, "upper")[0]
    out["ii"] = {"cell": [int(ev[k]) for k in np.flatnonzero(bc > C.DELTA)], "family": [int(fam[k]) for k in np.flatnonzero(bf > C.DELTA)],
                 "pooled": bool(bp[0] > C.DELTA), "hk1c_fail": bool(bu[0] > C.DELTA + C.HK1C_MARGIN)}
    # (iii)
    dt, dtp = C.deff_table(N, X), C.deff_table(Np, Xp)
    bc = C.wilson_family(est, dt, ev, level, "lower")[0]
    bf = C.wilson_family(est, dt, fam, level, "lower")[0] if len(fam) else np.zeros(0)
    bp = C.wilson_family(pe, dtp, [0], level, "lower")[0]
    bu = C.wilson_family(pe, dtp, [0], C.L_HK1C, "upper")[0]
    out["iii"] = {"cell": [int(ev[k]) for k in np.flatnonzero(bc > C.DELTA)], "family": [int(fam[k]) for k in np.flatnonzero(bf > C.DELTA)],
                  "pooled": bool(bp[0] > C.DELTA), "hk1c_fail": bool(bu[0] > C.DELTA + C.HK1C_MARGIN)}
    return out


def mstar_rules(N, X, ev, fam, Wa, truth_cells, truth_pooled):
    """Coverage of the simultaneous 0.95 UBs over ev and of the HK1c UB; M*'s flags at 0.95 (cells, family, pooled)."""
    out = {}
    Np, Xp = pooled_cols(N, X)
    est, pe = L.point_rates(N, X), L.point_rates(Np, Xp)
    boot = Wa.rates(N, X)
    pb = Wa.rates(Np, Xp)
    S, Sp = C.Stud(N, X, Wa), C.Stud(Np, Xp, Wa)
    dt, dtp = C.deff_table(N, X), C.deff_table(Np, Xp)
    tc = truth_cells[ev]
    for m in METHODS:
        if m == "i":
            ub = L.supt(est, boot, ev, C.LEVEL_M, "upper")["bound"]
            hk = L.supt(pe, pb, [0], C.L_HK1C, "upper")["bound"][0]
            fc = L.flag_cells(est, boot, ev, C.LEVEL_M)["flag"]
            ff = L.flag_cells(est, boot, fam, C.LEVEL_M)["flag"] if len(fam) else np.zeros(0, bool)
            fp = bool(L.flag_cells(pe, pb, [0], C.LEVEL_M)["flag"][0])
        elif m == "ii":
            ub = S.bounds(ev, C.LEVEL_M, "upper")[0]
            hk = Sp.bounds([0], C.L_HK1C, "upper")[0][0]
            fc = S.bounds(ev, C.LEVEL_M, "lower")[0] > C.DELTA
            ff = (S.bounds(fam, C.LEVEL_M, "lower")[0] > C.DELTA) if len(fam) else np.zeros(0, bool)
            fp = bool(Sp.bounds([0], C.LEVEL_M, "lower")[0][0] > C.DELTA)
        else:
            ub = C.wilson_family(est, dt, ev, C.LEVEL_M, "upper")[0]
            hk = C.wilson_family(pe, dtp, [0], C.L_HK1C, "upper")[0][0]
            fc = C.wilson_family(est, dt, ev, C.LEVEL_M, "lower")[0] > C.DELTA
            ff = (C.wilson_family(est, dt, fam, C.LEVEL_M, "lower")[0] > C.DELTA) if len(fam) else np.zeros(0, bool)
            fp = bool(C.wilson_family(pe, dtp, [0], C.LEVEL_M, "lower")[0][0] > C.DELTA)
        cov = ub >= tc
        out[m] = {"cover_cells": [bool(x) for x in cov], "cover_all": bool(cov.all()), "max_ub": float(np.max(ub)),
                  "hk1c_ub": float(hk), "hk1c_cover": bool(hk >= truth_pooled), "hk1c_pass": bool(hk <= C.DELTA + C.HK1C_MARGIN),
                  "flag_cell": bool(fc.any()), "flag_family": bool(ff.any()), "flag_pooled": fp,
                  "flag_any": bool(fc.any() or ff.any() or fp)}
    return out


# ------------------------------------------------------------------ scenarios
def scenario_specs(t, data, ext, blocks):
    rec = ext["trackers"][t]
    specs = []
    # M*: per population, truth delta and observed
    mp = {}
    for pop in C.POPS:
        N, X = data.table("Mstar", pop)
        ev = np.flatnonzero(L.evaluable(N))
        fam = C.cells_idx(rec["families"]["Mstar"][pop])
        dt = C.deff_table(N, X)
        est = L.point_rates(N, X)
        obs = np.where(np.isfinite(est), est, 0.0)
        mp[pop] = {"N": N, "ev": ev, "fam": fam, "rho": dt["rho"], "obs": obs}
    specs.append({"s": SCEN_M_DELTA, "kind": "mstar", "arm": "Mstar", "truth": "delta", "pops": mp})
    specs.append({"s": SCEN_M_OBS, "kind": "mstar", "arm": "Mstar", "truth": "observed", "pops": mp})
    for c in REMOVED_R1[t]:
        Nb, Xb = blocks[c]
        Nrel, Xrel = C.pop_from_blocks(Nb, "PD7_primary"), C.pop_from_blocks(Xb, "PD7_primary")
        dt = C.deff_table(Nrel, Xrel)
        pops = {}
        for pop in C.POPS:
            N = C.pop_from_blocks(Nb, pop)
            pops[pop] = {"ev": np.flatnonzero(L.evaluable(N)), "fam": C.cells_idx(rec["families"][c][pop])}
        specs.append({"s": 2 + C.COMPS.index(c), "kind": "comparator", "arm": c, "truth": "delta", "Nb": Nb, "rho": dt["rho"],
                      "pops": pops})
    return specs


def run_dataset(t, spec, d, U):
    rng = np.random.default_rng([C.SEED_X3_BOOT, C.TRACKER_I[t], C.J_C, spec["s"], d])
    if spec["kind"] == "comparator":
        Nb = spec["Nb"]
        p = beta_rates(rng, np.full(32, C.DELTA), spec["rho"], (U, 32))
        Xb = rng.binomial(Nb.astype(np.int64), p[:, :, None]).astype(np.float64)
        Wa = WArr(rng.multinomial(U, np.full(U, 1.0 / U), size=INNER_B).astype(np.float64))
        res = {}
        for pop in C.POPS:
            N, X = C.pop_from_blocks(Nb, pop), C.pop_from_blocks(Xb, pop)
            res[pop] = comparator_rules(N, X, spec["pops"][pop]["ev"], spec["pops"][pop]["fam"], Wa, C.LEVEL_RM)
        out = {"d": d}
        for m in METHODS:
            n9 = any(res[p][m]["cell"] or res[p][m]["family"] or res[p][m]["pooled"] for p in C.POPS)
            hk = any(res[p][m]["hk1c_fail"] for p in C.POPS)
            out[m] = {"removed_9": bool(n9), "removed_code_of_record": bool(n9 or hk), "hk1c_fail_any": bool(hk),
                      "by_pop": {p: {"cell": [C.CELLNAMES[j] for j in res[p][m]["cell"]],
                                     "family": [C.CELLNAMES[j] for j in res[p][m]["family"]],
                                     "pooled": res[p][m]["pooled"], "hk1c_fail": res[p][m]["hk1c_fail"]} for p in C.POPS}}
        return out
    # M*: three independent population layouts, drawn in order from the same generator
    Wa = None
    out = {"d": d}
    draws = {}
    for pop in C.POPS:
        sp = spec["pops"][pop]
        r = np.full(32, C.DELTA) if spec["truth"] == "delta" else sp["obs"]
        p = beta_rates(rng, r, sp["rho"], (U, 32))
        X = rng.binomial(sp["N"].astype(np.int64), p).astype(np.float64)
        draws[pop] = (X, r)
    Wa = WArr(rng.multinomial(U, np.full(U, 1.0 / U), size=INNER_B).astype(np.float64))
    for pop in C.POPS:
        sp = spec["pops"][pop]
        X, r = draws[pop]
        N = sp["N"]
        tot = N.sum(1)
        has = tot > 0
        truth_pooled = float(np.mean((N[has] @ r) / tot[has]))
        out[pop] = mstar_rules(N, X, sp["ev"], sp["fam"], Wa, r, truth_pooled)
        out[pop]["truth_pooled"] = truth_pooled
    return out


def ckpt_path(ck_dir, t, s, c0):
    return os.path.join(ck_dir, "%s_s%02d_d%04d.json" % (t, s, c0))


def run_tracker(t, ext, ck_dir, log, total_done, total_all):
    with heavy_lock("x3-stats: (c2) simulation %s, 1000 datasets x inner B 1000 per scenario" % t):
        t0 = time.time()
        data = C.load_data(t)
        blocks = C.block_tables(data, ["Mstar"] + list(C.COMPS))
        # check: block sums equal the populations of R21's tables (which reproduced the record)
        bcheck = {}
        for a in ["Mstar"] + list(C.COMPS):
            for pop in C.POPS:
                N, X = data.table(a, pop)
                bcheck["%s/%s" % (a, pop)] = float(max(np.abs(C.pop_from_blocks(blocks[a][0], pop) - N).max(),
                                                       np.abs(C.pop_from_blocks(blocks[a][1], pop) - X).max()))
        assert max(bcheck.values()) == 0.0, "block sums differ from the population tables"
        specs = scenario_specs(t, data, ext, blocks)
        meta = {"units": data.U, "block_check_max_abs_diff": max(bcheck.values()),
                "scenarios": [{"s": sp["s"], "arm": sp["arm"], "kind": sp["kind"], "truth": sp["truth"]} for sp in specs],
                "rho_used": {}}
        for sp in specs:
            if sp["kind"] == "comparator":
                meta["rho_used"][sp["arm"]] = {C.CELLNAMES[j]: float(sp["rho"][j]) for j in range(32) if sp["Nb"][:, j].sum() > 0}
            elif sp["s"] == SCEN_M_DELTA:
                meta["rho_used"]["Mstar"] = {pop: {C.CELLNAMES[j]: float(sp["pops"][pop]["rho"][j]) for j in range(32)
                                                   if sp["pops"][pop]["N"][:, j].sum() > 0} for pop in C.POPS}
                meta["observed_rates_Mstar"] = {pop: {C.CELLNAMES[j]: float(sp["pops"][pop]["obs"][j]) for j in range(32)
                                                      if sp["pops"][pop]["N"][:, j].sum() > 0} for pop in C.POPS}
        log("%s: data and blocks ready (%.0f s); %d scenarios" % (t, time.time() - t0, len(specs)))
        for sp in specs:
            for c0 in range(0, N_DATASETS, CHUNK):
                p = ckpt_path(ck_dir, t, sp["s"], c0)
                if os.path.exists(p):
                    total_done[0] += CHUNK
                    continue
                t1 = time.time()
                rows = [run_dataset(t, sp, d, data.U) for d in range(c0, min(N_DATASETS, c0 + CHUNK))]
                C.jdump_new(p, {"stamp": C.STAMP, "tracker": t, "s": sp["s"], "arm": sp["arm"], "truth": sp["truth"],
                                "d0": c0, "rows": rows, "seconds": time.time() - t1, "written": C.now()})
                total_done[0] += len(rows)
                C.live("(c2) simulation %s %s (%s)" % (t, sp["arm"], sp["truth"]), total_done[0], total_all,
                       "datasets; chunk %d-%d took %.0f s" % (c0, c0 + len(rows) - 1, time.time() - t1))
            log("%s scenario %s/%s done (%.0f s so far)" % (t, sp["arm"], sp["truth"], time.time() - t0))
        del data, blocks, specs
    return meta


# ------------------------------------------------------------------ aggregation
def wilson95(k, n):
    lo, hi = C.wilson(k / n, n, 1.959963984540054)
    return [float(lo), float(hi)]


def aggregate(ck_dir, trackers, metas):
    res = {}
    for t in trackers:
        res[t] = {}
        for sc in metas[t]["scenarios"]:
            rows = []
            for c0 in range(0, N_DATASETS, CHUNK):
                with open(ckpt_path(ck_dir, t, sc["s"], c0), encoding="utf-8") as f:
                    rows += json.load(f)["rows"]
            assert [r["d"] for r in rows] == list(range(N_DATASETS)), "missing datasets"
            n = len(rows)
            key = "%s|%s" % (sc["arm"], sc["truth"])
            if sc["kind"] == "comparator":
                o = {"datasets": n}
                for m in METHODS:
                    k9 = sum(r[m]["removed_9"] for r in rows)
                    kc = sum(r[m]["removed_code_of_record"] for r in rows)
                    kcell = sum(any(r[m]["by_pop"][p]["cell"] for p in C.POPS) for r in rows)
                    cond = {}
                    for p in C.POPS:
                        cond[p] = {"cell": sum(bool(r[m]["by_pop"][p]["cell"]) for r in rows) / n,
                                   "family": sum(bool(r[m]["by_pop"][p]["family"]) for r in rows) / n,
                                   "pooled": sum(r[m]["by_pop"][p]["pooled"] for r in rows) / n,
                                   "hk1c_fail": sum(r[m]["by_pop"][p]["hk1c_fail"] for r in rows) / n}
                    cells = {}
                    for r in rows:
                        for p in C.POPS:
                            for c in r[m]["by_pop"][p]["cell"]:
                                cells["%s:%s" % (p, c)] = cells.get("%s:%s" % (p, c), 0) + 1
                    o[m] = {"false_removal_9_conditions": k9 / n, "ci95": wilson95(k9, n),
                            "false_removal_code_of_record": kc / n, "ci95_code_of_record": wilson95(kc, n),
                            "any_cell_flag": kcell / n, "by_condition": cond,
                            "most_flagged_cells": sorted(cells.items(), key=lambda x: -x[1])[:8]}
                res[t][key] = o
            else:
                o = {"datasets": n}
                for m in METHODS:
                    o[m] = {}
                    for p in C.POPS:
                        rr = [r[p][m] for r in rows]
                        cc = np.array([x["cover_cells"] for x in rr], float)
                        ka = sum(x["cover_all"] for x in rr)
                        kh = sum(x["hk1c_cover"] for x in rr)
                        kf = sum(x["flag_any"] for x in rr)
                        o[m][p] = {"sim_ub_cover_all": ka / n, "sim_ub_cover_all_ci95": wilson95(ka, n),
                                   "sim_ub_cover_cell_mean": float(cc.mean()), "sim_ub_cover_cell_min": float(cc.mean(0).min()),
                                   "hk1c_cover": kh / n, "hk1c_cover_ci95": wilson95(kh, n),
                                   "hk1c_pass_share": sum(x["hk1c_pass"] for x in rr) / n,
                                   "flag_any_share": kf / n, "flag_any_ci95": wilson95(kf, n),
                                   "flag_cell_share": sum(x["flag_cell"] for x in rr) / n,
                                   "flag_family_share": sum(x["flag_family"] for x in rr) / n,
                                   "flag_pooled_share": sum(x["flag_pooled"] for x in rr) / n,
                                   "median_max_ub": float(np.median([x["max_ub"] for x in rr])),
                                   "truth_pooled": rows[0][p]["truth_pooled"]}
                    o[m]["screen_flag_any_population"] = sum(any(r[p][m]["flag_any"] for p in C.POPS) for r in rows) / n
                res[t][key] = o
    return res


def write_md(path, out):
    A = out["results"]
    f3 = lambda v: "-" if v is None else "%.3f" % v  # noqa: E731
    lines = ["# X3 (c2): simulated false removal and coverage at Argoverse 2's cell sizes (v01)", "", "**%s**" % C.STAMP, "",
             "Plan 2(c2) (sha256 %s...); referee concern M4. %d datasets per scenario, inner log bootstrap of %d, seeds [20261201, i, 3, s, d]. "
             "Method (i) is the record's rule (pre-specified); (ii) and (iii) are the (c1) alternatives, added and not pre-specified. "
             "JSON: `x3_c2_simulation_v01.json`." % (C.PLAN_SHA[:8], N_DATASETS, INNER_B), "",
             "## False removal of each comparator removed in r1 (truth 0.05 in every cell, its own layout)", "",
             "Removal level 1 - 0.0125/9. '9 conditions' = a cell, family or pooled flag in P_rel, P_near or P_ip (plan 6.2); 'code' adds "
             "the HK1c failure that c1_analyse_v02.arm_status also counts. 95 % Wilson intervals over datasets in brackets.", "",
             "| Tracker | Comparator | (i) 9 conditions | (i) code | (ii) 9 conditions | (iii) 9 conditions |", "|---|---|---|---|---|---|"]
    for t, rt in A.items():
        for key, o in rt.items():
            if not key.endswith("|delta") or key.startswith("Mstar"):
                continue
            arm = key.split("|")[0]
            lines.append("| %s | %s | %s [%s, %s] | %s | %s [%s, %s] | %s [%s, %s] |" % (
                t, arm, f3(o["i"]["false_removal_9_conditions"]), f3(o["i"]["ci95"][0]), f3(o["i"]["ci95"][1]),
                f3(o["i"]["false_removal_code_of_record"]),
                f3(o["ii"]["false_removal_9_conditions"]), f3(o["ii"]["ci95"][0]), f3(o["ii"]["ci95"][1]),
                f3(o["iii"]["false_removal_9_conditions"]), f3(o["iii"]["ci95"][0]), f3(o["iii"]["ci95"][1])))
    for truth in ("delta", "observed"):
        lines += ["", "## M*: coverage at true rates = %s" % ("0.05 in every cell" if truth == "delta" else "M*'s observed cell rates"), "",
                  "Simultaneous coverage of the one-sided '95 %' upper bounds over the evaluable cells (mean and worst per-cell coverage in "
                  "brackets) and coverage of the HK1c '99.5 %' pooled upper bound.", "",
                  "| Tracker | Population | (i) simultaneous | (i) HK1c | (ii) simultaneous | (ii) HK1c | (iii) simultaneous | (iii) HK1c |",
                  "|---|---|---|---|---|---|---|---|"]
        for t, rt in A.items():
            o = rt.get("Mstar|%s" % truth)
            if not o:
                continue
            for p in C.POPS:
                cells = []
                for m in METHODS:
                    x = o[m][p]
                    cells.append("%s (%s; %s)" % (f3(x["sim_ub_cover_all"]), f3(x["sim_ub_cover_cell_mean"]), f3(x["sim_ub_cover_cell_min"])))
                    cells.append(f3(x["hk1c_cover"]))
                lines.append("| %s | %s | %s |" % (t, p, " | ".join(cells)))
    lines += ["", "## M*'s own flag rate when every cell is at 0.05 (size of the screen against M*; added, not pre-specified)", "",
              "| Tracker | Population | (i) | (ii) | (iii) |", "|---|---|---|---|---|"]
    for t, rt in A.items():
        o = rt.get("Mstar|delta")
        if not o:
            continue
        for p in C.POPS:
            lines.append("| %s | %s | %s |" % (t, p, " | ".join(f3(o[m][p]["flag_any_share"]) for m in METHODS)))
        lines.append("| %s | any population | %s |" % (t, " | ".join(f3(o[m]["screen_flag_any_population"]) for m in METHODS)))
    lines += ["", "## Notes", ""] + ["- " + n for n in out["notes"]] + ["", "Code: `50_CODE/x3/x3_stats_c2_v01.py` (sha256 in the JSON).", ""]
    C.text_new(path, "\n".join(lines))


NOTES = [
    "rho_c is the ANOVA ICC of the observed cell (truncated to [0, 1]; 0 where undefined, which gives binomial data); its values are "
    "in the JSON (meta.rho_used).",
    "With an inner bootstrap of 1000 the removal quantile 0.998611 sits between the 2nd and 3rd largest max-t replicates; the record "
    "used 40000. The simulated false-removal rate therefore carries this extra Monte Carlo noise in the quantile (it is part of what is "
    "simulated, as the plan specifies 1000).",
    "Evaluable sets and power families are fixed at the record's (they depend only on the record counts, which the simulation keeps).",
    "The comparator scenarios share one per-log rate per cell across the four record blocks, so the 9 conditions are correlated as in "
    "the data; the M* coverage scenarios draw each population on its own layout (coverage is a per-population property).",
    "Pooled truth = mean over logs with records of sum_c N_uc r_c / sum_c N_uc (the expectation of the record's pooled estimator given "
    "the layout); cell truth = r_c.",
]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--trackers", default="t1,t3")
    a = ap.parse_args(argv)
    jpath = os.path.join(a.out_dir, "x3_c2_simulation_v01.json")
    mpath = os.path.join(a.out_dir, "x3_c2_simulation_v01.md")
    for p in (jpath, mpath):
        if os.path.exists(p):
            sys.exit("refusing to overwrite " + p)
    ck_dir = os.path.join(a.out_dir, "c2_ckpt_v01")
    os.makedirs(ck_dir, exist_ok=True)

    def log(*x):
        print(time.strftime("%H:%M:%S"), *x, flush=True)

    assert C.sha256(C.PLAN) == C.PLAN_SHA, "plan hash differs"
    trackers = a.trackers.split(",")
    ext = C.load_record_extract(tuple(trackers))
    n_scen = sum(2 + len(REMOVED_R1[t]) for t in trackers)
    total_all = n_scen * N_DATASETS
    done = [0]
    metas = {}
    t0 = time.time()
    for t in trackers:
        metas[t] = run_tracker(t, ext, ck_dir, log, done, total_all)
    res = aggregate(ck_dir, trackers, metas)
    out = {"stamp": C.STAMP, "analysis": "X3 (c2) simulated false removal and coverage, plan 2(c2); referee M4",
           "plan": {"path": "20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md", "sha256": C.PLAN_SHA},
           "inputs": {"analysis_sha256": ext["analysis_sha256"]},
           "code_sha256": {os.path.basename(p): C.sha256(p) for p in (os.path.abspath(__file__), C.__file__, L.__file__)},
           "versions": C.versions(), "datasets": N_DATASETS, "inner_bootstrap": INNER_B, "chunk": CHUNK,
           "seeds": "numpy default_rng([20261201, i, 3, s, d]); i tracker index, s scenario index, d dataset index",
           "levels": {"removal": C.LEVEL_RM, "Mstar": C.LEVEL_M, "hk1c": C.L_HK1C},
           "removed_in_r1": {t: REMOVED_R1[t] for t in trackers}, "meta": metas, "results": res, "notes": NOTES,
           "pre_specified": "method (i): false removal for every comparator removed in r1; coverage of M*'s simultaneous 0.95 UBs and "
                            "HK1c 0.995 UB at truth delta and at M*'s observed rates",
           "added_not_pre_specified": "methods (ii) and (iii) for the same quantities; M*'s own flag rate at truth delta",
           "seconds": time.time() - t0}
    C.jdump_new(jpath, out)
    write_md(mpath, out)
    C.live("(c2) simulation done", done[0], total_all, "outputs written")
    log("wrote", jpath, mpath)
    return 0


if __name__ == "__main__":
    sys.exit(main())
