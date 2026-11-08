#!/usr/bin/env python3
"""Operating characteristics at the frozen counts (Claude line, v01, 31 Oct 2026; R07 C1, M4, M5, M11). Simulated outcomes only.
The item layout is the real one from a sizes file: per scene and level-0 stratum, the item count; scenes in their real
logs; records per scene. The real E1 and E2 cells are used. Scores are simulated:
  U = tau(stratum) * (sqrt(rho) * eta[scene, stratum] + sqrt(1 - rho) * eps) + log effect
with rho = 0.5 (items of one scene and stratum are correlated, like one track over keyframes) and log effects of SD 0.1.
The code under test is m_run_v02.run_e1 and run_e2 themselves, with reduced repetitions and replicates.
Reports:
 (a) E1 null: how often M* is flagged (HM1 fails) under the fixed-rule and the refit-CV inference;
 (b) E2 null: how often HM6 fails;
 (c) power of the fixed-rule E1 and E2 tests, per cell, for a planted rule with true exceedance 0.10, 0.15, 0.20 or 0.30,
     and the minimum detectable exceedance (80 % power);
 (d) power of the HM3 paired contrast (B6 against M*) at the real counts, with lateral turning tau 2.6 against straight 1.2.
Usage: python test_m_oc_v01.py --sizes <m_sizes_*_v02.json> --out <json> [--datasets 20]
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
import m_lib_v02 as M  # noqa: E402
import m_run_v02 as R  # noqa: E402

RHO, LOG_SD = 0.5, 0.1


def tau_of(l0, shift=1.0):
    g, r, a, m = M.decode(l0)
    t = (2.6 if m == 2 else (0.6 if m == 0 else 1.2)) if a == 1 else (0.5 if m == 0 else 0.9)
    return t * (shift if (g == 0 and a == 1 and m == 2) else 1.0)


def simulate(layout, rng, shift=1.0):
    sl = np.asarray(layout["scene_l0_count"], int)
    sli = np.asarray(layout["scene_log_idx"], int)
    S, nl = len(sli), layout["n_logs"]
    s = np.repeat(sl[:, 0], sl[:, 2])
    l0 = np.repeat(sl[:, 1], sl[:, 2])
    grp = np.repeat(np.arange(len(sl)), sl[:, 2])
    dec = np.array([M.decode(x) for x in l0]) if len(l0) else np.zeros((0, 4), int)
    g, r, a, mo = dec[:, 0], dec[:, 1], dec[:, 2], dec[:, 3]
    n = len(s)
    spd = np.where(mo == 0, 0.5, 5.0)
    om = np.where(mo == 2, 0.2, np.where(mo == 3, np.nan, 0.02))
    tau = np.array([tau_of(x, shift) for x in range(M.N_L0)])[l0]
    leff = rng.normal(0, LOG_SD, nl)
    eta = rng.standard_normal(len(sl))[grp]
    U = tau * (math.sqrt(RHO) * eta + math.sqrt(1 - RHO) * rng.standard_normal(n)) + leff[sli[s]]
    V = rng.uniform(0.3, 0.8, n) ** 2
    sd = np.sqrt(V + M.SIGMA_A ** 2)
    items = {"s": s, "lg": sli[s], "g": g, "r": r, "a": a, "spd": spd, "om": om, "omv": om.copy(), "V": V, "contested": np.zeros(n, bool),
             "D": U * sd, "scene_log_idx": sli, "n_scenes": S, "n_logs": nl}
    rps = np.asarray(layout["records_per_scene"], int)
    rs = np.repeat(np.arange(S), rps)
    nr = len(rs)
    sxx, syy = rng.uniform(0.1, 0.5, nr), rng.uniform(0.1, 0.5, nr)
    recs = {"s": rs, "g": np.zeros(nr, int), "r": rng.integers(0, 2, nr), "sxx": sxx, "sxy": np.zeros(nr), "syy": syy,
            "dx": 2 * np.sqrt(sxx + M.SIGMA_A ** 2) * rng.standard_normal(nr), "dy": 2 * np.sqrt(syy + M.SIGMA_A ** 2) * rng.standard_normal(nr),
            "contested": np.zeros(nr, bool)}
    return items, recs, tau


def planted_margins(items, tau, p):
    """Margin whose true marginal exceedance is p for every item (U is normal with SD tau * sqrt(1 + LOG_SD^2 / tau^2))."""
    sd = np.sqrt(items["V"] + M.SIGMA_A ** 2)
    tot = np.sqrt(tau ** 2 + LOG_SD ** 2)
    return float(norm.ppf(1 - p)) * tot * sd


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--sizes", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--datasets", type=int, default=20)
    ap.add_argument("--e1-reps", type=int, default=5)
    ap.add_argument("--e1-refit-datasets", type=int, default=6)
    ap.add_argument("--e1-refit-B", type=int, default=40)
    ap.add_argument("--e2-B", type=int, default=150)
    ap.add_argument("--power-datasets", type=int, default=40)
    a = ap.parse_args()
    sz = json.load(open(a.sizes))
    lay_tr, lay_va = sz["train"]["h2s"]["layout"], sz["val"]["h2s"]["layout"]
    c1 = [(n, list(ids)) for n, ids in sz["train"]["h2s"]["cells"]]
    c2 = [(n, list(ids)) for n, ids in sz["val"]["h2s"]["cells"]]
    out = {"tracker": sz["tracker"], "rho": RHO, "log_sd": LOG_SD, "E1_cells": [c[0] for c in c1], "E2_cells": [c[0] for c in c2]}
    t0 = time.time()
    rng = np.random.default_rng([M.SEED, zlib.crc32(("oc|" + sz["tracker"]).encode())])

    def names_logs(items):
        names = ["sc%04d" % i for i in range(items["n_scenes"])]
        return names, {nm: "log%03d" % items["scene_log_idx"][i] for i, nm in enumerate(names)}

    # (a) E1 null, fixed-rule (and HM3 paired power on the same data); refit-CV on the first few datasets
    e1_flag, e1r_flag, hm3_fixed, hm3_both = 0, 0, 0, 0
    for d in range(a.datasets):
        it, rc, _ = simulate(lay_tr, rng)
        names, slog = names_logs(it)
        refit = a.e1_refit_B if d < a.e1_refit_datasets else 0
        e = R.run_e1(it, rc, {}, names, slog, c1, "oc|E1|%d" % d, B=300, reps=a.e1_reps, refit_B=refit)
        e1_flag += int(e["fixed"]["methods"]["Mstar"]["any_sig_under"])
        hm3_fixed += int(bool(M.failures([e["fixed"]], "B6", "B6-Mstar|car turning")))
        if refit:
            e1r_flag += int(e["refit"]["methods"]["Mstar"]["any_sig_under"])
            hm3_both += int(e["hypotheses"]["HM3_holds"])
        print("E1 dataset", d, "%.0f s" % (time.time() - t0), flush=True)
    out["a_E1_fixed_Mstar_flag_rate"] = e1_flag / a.datasets
    out["a_E1_refit_Mstar_flag_rate"] = e1r_flag / max(a.e1_refit_datasets, 1)
    out["d_HM3_power_fixed"] = hm3_fixed / a.datasets
    out["d_HM3_power_both_inferences"] = hm3_both / max(a.e1_refit_datasets, 1)

    # (b) E2 null
    e2_fail, e2a_fail, pooled = 0, 0, []
    for d in range(a.datasets):
        tr, trr, _ = simulate(lay_tr, rng)
        va, var, _ = simulate(lay_va, rng)
        e = R.run_e2(tr, trr, va, var, {}, c2, "oc|E2|%d" % d, B=a.e2_B)
        e2_fail += int(not e["hypotheses"]["HM6"])
        e2a_fail += int(not e["hypotheses"]["HM6a"])
        pooled.append([e["hypotheses"]["pooled_E"], e["hypotheses"]["pooled_ub"]])
        print("E2 dataset", d, "%.0f s" % (time.time() - t0), flush=True)
    out["b_E2_HM6_fail_rate"] = e2_fail / a.datasets
    out["b_E2_HM6a_fail_rate"] = e2a_fail / a.datasets
    out["b_E2_mean_pooled_E_and_ub"] = np.mean(pooled, 0).round(4).tolist()

    # (c) power per cell of the fixed-rule test for a planted rule with true exceedance p
    ps = (0.10, 0.15, 0.20, 0.30)
    for tag, lay, cells in (("E1", lay_tr, c1), ("E2", lay_va, c2)):
        det = {p: np.zeros(len(cells)) for p in ps}
        for d in range(a.power_datasets):
            it, rc, tau = simulate(lay, rng)
            P = M.prepare(it, rc, {})
            W = M.boot_scene_weights(it, 300, rng)
            st = M.eval_stats(it, P, {"p%.2f" % p: planted_margins(it, tau, p) for p in ps}, cells, W)
            for p in ps:
                det[p] += np.array([st["methods"]["p%.2f" % p]["cells"][n]["sig_under"] for n, _ in cells], float)
        pw = {p: (det[p] / a.power_datasets).round(3).tolist() for p in ps}
        mde = []
        for j in range(len(cells)):
            hit = [p for p in ps if pw[p][j] >= 0.8]
            mde.append(min(hit) if hit else ">0.30")
        out["c_%s_power" % tag] = {"cells": [c[0] for c in cells], "power_by_true_exceedance": {str(p): pw[p] for p in ps}, "MDE_80": mde}
    out["wall_s"] = round(time.time() - t0, 1)
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({k: v for k, v in out.items() if not k.startswith("c_")}))
    print("OC DONE")


if __name__ == "__main__":
    sys.exit(main())
