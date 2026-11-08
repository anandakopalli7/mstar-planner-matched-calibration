#!/usr/bin/env python3
"""Operating characteristics at the frozen counts, v03 (Claude line, 31 Oct 2026; R07c X-M1): v02 with fresh seeds (labels "oc3"),
the v04 rules (HM6b = pooled significance check), a --log-sd option for the between-log spread, and the pooled LB stored.
v02 header follows (R07 C1/M4/M5/M11, R07b N-M3, N-m14).
Simulated outcomes only. The item layout is the real one from a sizes file (per scene and level-0 stratum, the item count;
scenes in their real logs; records per scene); the real E1 and E2 cells are used. Scores:
  U = tau(stratum) * (sqrt(rho) * eta[scene, stratum] + sqrt(1 - rho) * eps) + log effect (SD 0.1)
The rules under test are m_run_v03.run_e1 and run_e2 themselves, fitting only the methods each part needs (M*, B6).
Parts (each writes one JSON; merge_oc_v02.py combines shards and applies the acceptance criteria of plan v04 section 9):
  e1null   E1 at the real layout, M* valid: how often HM1 fails, under the fixed rule and under the refit-CV rule.
  e2null   E2 (two-sample refit, B = 150), M* valid: how often HM6, HM6a and HM6b fail.
  e2power  E2 with every turning item on val scaled by `effect`: realised M* exceedance of the val turning cell and the
           rates at which HM6a flags it and HM6 fails.
  hm3power E1 with car lateral turning tau = `effect` (straight 1.2): realised B6 exceedance in the car turning cells and
           the rate at which HM3 holds under the frozen rule (refit-CV, paired, M* not flagged).
  comp     Power of the component "significantly under-covered" alone (fixed rule) for a planted rule with true
           exceedance 0.10, 0.15, 0.20 or 0.30, per E1 and E2 cell. It is not the power of HM2, HM3 or HM6.
Usage: python test_m_oc_v03.py --sizes <m_sizes_*_v03.json> --part e1null --rho 0.5 --datasets 10 --shard 0 --out <json>
"""
import argparse
import json
import math
import os
import sys
import time
import zlib

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)
import m_lib_v04 as M  # noqa: E402
import m_run_v04 as R  # noqa: E402

LOG_SD = 0.1  # default; --log-sd overrides it


def tau_table(car_lat_turn=1.2, turn_scale=1.0):
    t = np.zeros(M.N_L0)
    for l0 in range(M.N_L0):
        g, r, a, m = M.decode(l0)
        base = (0.6 if m == 0 else 1.2) if a == 1 else (0.5 if m == 0 else 0.9)
        if g == 0 and a == 1 and m == 2:
            base = car_lat_turn
        t[l0] = base * (turn_scale if m == 2 else 1.0)
    return t


def simulate(layout, rng, rho, tau, log_sd=None):
    log_sd = LOG_SD if log_sd is None else log_sd
    sl = np.asarray(layout["scene_l0_count"], int)
    sli = np.asarray(layout["scene_log_idx"], int)
    S, nl = len(sli), layout["n_logs"]
    s, l0 = np.repeat(sl[:, 0], sl[:, 2]), np.repeat(sl[:, 1], sl[:, 2])
    grp = np.repeat(np.arange(len(sl)), sl[:, 2])
    dec = np.array([M.decode(x) for x in l0])
    g, r, a, mo = dec[:, 0], dec[:, 1], dec[:, 2], dec[:, 3]
    n = len(s)
    spd = np.where(mo == 0, 0.5, 5.0)
    om = np.where(mo == 2, 0.2, np.where(mo == 3, np.nan, 0.02))
    tt = tau[l0]
    U = tt * (math.sqrt(rho) * rng.standard_normal(len(sl))[grp] + math.sqrt(1 - rho) * rng.standard_normal(n)) + rng.normal(0, log_sd, nl)[sli[s]]
    V = rng.uniform(0.3, 0.8, n) ** 2
    sd = np.sqrt(V + M.SIGMA_A ** 2)
    items = {"s": s, "lg": sli[s], "g": g, "r": r, "a": a, "spd": spd, "om": om, "omv": om.copy(), "omc": om.copy(), "chord": np.full(n, 5.0), "V": V,
             "contested": np.zeros(n, bool), "D": U * sd, "scene_log_idx": sli, "n_scenes": S, "n_logs": nl}
    rps = np.asarray(layout["records_per_scene"], int)
    rs = np.repeat(np.arange(S), rps)
    nr = len(rs)
    sxx, syy = rng.uniform(0.1, 0.5, nr), rng.uniform(0.1, 0.5, nr)
    recs = {"s": rs, "g": np.zeros(nr, int), "r": rng.integers(0, 2, nr), "sxx": sxx, "sxy": np.zeros(nr), "syy": syy,
            "dx": 2 * np.sqrt(sxx + M.SIGMA_A ** 2) * rng.standard_normal(nr), "dy": 2 * np.sqrt(syy + M.SIGMA_A ** 2) * rng.standard_normal(nr),
            "contested": np.zeros(nr, bool)}
    return items, recs, tt


def names_logs(items):
    names = ["sc%04d" % i for i in range(items["n_scenes"])]
    return names, {nm: "log%03d" % items["scene_log_idx"][i] for i, nm in enumerate(names)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", required=True)
    ap.add_argument("--part", required=True, choices=["e1null", "e2null", "e2power", "hm3power", "comp"])
    ap.add_argument("--rho", type=float, default=0.5)
    ap.add_argument("--effect", type=float, default=1.0)
    ap.add_argument("--datasets", type=int, default=10)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--e1-reps", type=int, default=3)
    ap.add_argument("--refit-B", type=int, default=40)
    ap.add_argument("--e2-B", type=int, default=150)
    ap.add_argument("--log-sd", type=float, default=LOG_SD)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    sz = json.load(open(a.sizes))
    lay_tr, lay_va = sz["train"]["h2s"]["layout"], sz["val"]["h2s"]["layout"]
    c1 = [(n, list(ids)) for n, ids in sz["train"]["h2s"]["cells"]]
    c2 = [(n, list(ids)) for n, ids in sz["val"]["h2s"]["cells"]]
    rng = np.random.default_rng([M.SEED, zlib.crc32(("oc3|%s|%s|%s|%s|%s|%d" % (sz["tracker"], a.part, a.rho, a.effect, a.log_sd, a.shard)).encode())])
    out = {"tracker": sz["tracker"], "part": a.part, "rho": a.rho, "effect": a.effect, "log_sd": a.log_sd, "shard": a.shard, "datasets": a.datasets,
           "e2_B": a.e2_B, "e1_reps": a.e1_reps, "refit_B": a.refit_B, "rows": []}
    t0 = time.time()
    turn_val_cell = [j for j, (n, ids) in enumerate(c2) if all(M.decode(x)[3] == 2 for x in ids)]
    for d in range(a.datasets):
        row = {}
        if a.part == "e1null":
            it, rc, _ = simulate(lay_tr, rng, a.rho, tau_table())
            names, slog = names_logs(it)
            e = R.run_e1(it, rc, {}, names, slog, c1, "oc2|e1|%d|%d" % (a.shard, d), B=300, reps=a.e1_reps, refit_B=a.refit_B, only=("Mstar",))
            row = {"fixed_flag": e["fixed"]["methods"]["Mstar"]["any_sig_under"], "refit_flag": e["refit"]["methods"]["Mstar"]["any_sig_under"]}
        elif a.part == "hm3power":
            it, rc, _ = simulate(lay_tr, rng, a.rho, tau_table(car_lat_turn=a.effect))
            names, slog = names_logs(it)
            e = R.run_e1(it, rc, {}, names, slog, c1, "oc2|hm3|%d|%d" % (a.shard, d), B=300, reps=a.e1_reps, refit_B=a.refit_B, only=("Mstar", "B6"))
            fam = [c1[j][0] for j in M.turning_family(c1)]
            row = {"HM3": e["hypotheses"]["HM3_holds"], "HM3_testable": e["hypotheses"]["HM3_testable"],
                   "HM3_fixed_rule": bool(M.failures([e["fixed"]], "B6", "B6-Mstar|car turning")),
                   "B6_E_turning_cells": {c: e["fixed"]["methods"]["B6"]["cells"][c]["E_scene"] for c in fam},
                   "Mstar_E_turning_cells": {c: e["fixed"]["methods"]["Mstar"]["cells"][c]["E_scene"] for c in fam}}
        elif a.part in ("e2null", "e2power"):
            tr, trr, _ = simulate(lay_tr, rng, a.rho, tau_table(), a.log_sd)
            va, var, _ = simulate(lay_va, rng, a.rho, tau_table(turn_scale=a.effect if a.part == "e2power" else 1.0), a.log_sd)
            e = R.run_e2(tr, trr, va, var, {}, c2, "oc2|e2|%d|%d" % (a.shard, d), B=a.e2_B, only=("Mstar",))
            h = e["hypotheses"]
            row = {"HM6": h["HM6"], "HM6a": h["HM6a"], "HM6b": h["HM6b"], "pooled_E": h["pooled_E"], "pooled_lb": h["pooled_lb"],
                   "pooled_ub_bc": h["pooled_ub_bias_corrected"], "pooled_equivalence_at_eps": h["pooled_equivalence_at_eps"]}
            if turn_val_cell:
                cn = c2[turn_val_cell[0]][0]
                cm = e["cells"]["methods"]["Mstar"]["cells"][cn]
                row.update({"turn_cell": cn, "turn_cell_E": cm["E_scene"], "turn_cell_flagged": cm["sig_under"]})
        elif a.part == "comp":
            ps = (0.10, 0.15, 0.20, 0.30)
            for tag, lay, cells in (("E1", lay_tr, c1), ("E2", lay_va, c2)):
                it, rc, tt = simulate(lay, rng, a.rho, tau_table())
                P = M.prepare(it, rc, {})
                sd = np.sqrt(it["V"] + M.SIGMA_A ** 2)
                tot = np.sqrt(tt ** 2 + LOG_SD ** 2)
                marg = {"p%.2f" % p: float(norm.ppf(1 - p)) * tot * sd for p in ps}
                st = M.eval_stats(it, P, marg, cells, M.boot_scene_weights(it, 300, rng))
                row[tag] = {"p%.2f" % p: [st["methods"]["p%.2f" % p]["cells"][n]["sig_under"] for n, _ in cells] for p in ps}
        out["rows"].append(row)
        print(a.part, a.rho, a.effect, "dataset", d, "%.0f s" % (time.time() - t0), flush=True)
    out["wall_s"] = round(time.time() - t0, 1)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print("OC PART DONE")


if __name__ == "__main__":
    sys.exit(main())
