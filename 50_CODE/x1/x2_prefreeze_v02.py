#!/usr/bin/env python3
"""X2 pre-freeze steps v02 (Claude line, 30 Oct 2026), after review R05. Uses the memory-lean library v03.
  sizes : per-cell counts, per-scene counts, median SD, orientation null (no ground-truth residual)
  fwer  : P(any decision cell FAILS) under E = 0.05 for the 95 % band over the 4 decision cells (h2s); <= 0.05 + 2 MC SE
  power : P(at least one lateral decision cell FAILS) when the true lateral exceedance is 0.05 + f (E_X1 - 0.05),
          f in {0.6, 0.8, 1.0}, longitudinal cells at their X1 values; thresholds max(0.05, E0) from the train sizes
  oc    : Q4 operating characteristics (as X1)
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np
from scipy.optimize import brentq
from scipy.special import expit

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_lib_v03 as L3  # noqa: E402
import x1_prefreeze_v02 as PF  # noqa: E402

PF.L = L3
DEC = ["car|<20|lat", "car|20-40|lat", "car|<20|long", "car|20-40|long"]
X1_E = {"car|<20|lat": 0.135, "car|20-40|lat": 0.175, "car|<20|long": 0.004, "car|20-40|long": 0.009}


def sim(sz, E_true, thr, reps=500, B=2000, tau=0.5, seed=1):
    rng = np.random.default_rng(L3.SEED + seed)
    cells = [c for c in DEC if sz["cells"].get(c, {}).get("eligible")]
    counts = np.array([sz["cells"][c]["per_scene_counts"] for c in cells], dtype=float).T
    S, G = counts.shape
    a0 = {c: brentq(lambda a_: np.mean(expit(a_ + rng.normal(0, tau, 100000))) - E_true[c], -15, 5) for c in cells}
    hits_any = hits_lat = 0
    for _ in range(reps):
        b = math.sqrt(tau ** 2 / 2) * (rng.normal(0, 1, (S, 1)) + rng.normal(0, 1, (S, G)))
        p = expit(np.array([a0[c] for c in cells])[None, :] + b)
        exc = rng.binomial(counts.astype(int), p).astype(float)
        est = exc.sum(0) / np.maximum(counts.sum(0), 1)
        W = L3.boot_weights(S, B, rng)
        boot = (W @ exc) / np.maximum(W @ counts, 1e-12)
        lo, hi, _, zero = L3.sup_t_band(est, boot, level=0.95)
        v = L3.verdicts(est, lo, hi, zero, np.array([thr[c] for c in cells]))
        fails = [c for c, x in zip(cells, v) if x == "FAILS"]
        hits_any += int(bool(fails))
        hits_lat += int(any(c.endswith("lat") for c in fails))
    return {"cells": cells, "reps": reps, "P_any_FAILS": hits_any / reps, "P_lateral_FAILS": hits_lat / reps}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["sizes", "fwer", "power", "oc"])
    ap.add_argument("--export", nargs="+")
    ap.add_argument("--gt")
    ap.add_argument("--meta")
    ap.add_argument("--horizon")
    ap.add_argument("--sizes")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    if a.mode == "sizes":
        res = PF.sizes(a.export, a.gt, a.meta, a.horizon)
    else:
        allsz = json.load(open(a.sizes))
        sz = allsz["families"]["h2s"]
        if a.mode == "fwer":
            null = {c: 0.05 for c in DEC}
            r = sim(sz, null, {c: 0.05 for c in DEC})
            r_tau1 = sim(sz, null, {c: 0.05 for c in DEC}, tau=1.0, seed=2)
            lim = 0.05 + 2 * math.sqrt(0.05 * 0.95 / r["reps"])
            res = {"h2s": {"tau0.5": r, "tau1.0": r_tau1, "limit": lim}, "primary_linear_band": {"ok": r["P_any_FAILS"] <= lim and r_tau1["P_any_FAILS"] <= lim}}
        elif a.mode == "power":
            thr = {c: max(0.05, sz["cells"][c].get("E0_sigma_0.10") or 0.05) for c in DEC if c in sz["cells"]}
            res = {"thresholds_from_train_E0": thr}
            for f in (0.6, 0.8, 1.0):
                E = {c: (0.05 + f * (X1_E[c] - 0.05)) if c.endswith("lat") else X1_E[c] for c in DEC}
                res["f=%.1f" % f] = sim(sz, E, thr, reps=300, seed=int(10 * f))
            res["note"] = "power of condition (a1) only; a2-a5 and H2 are not simulated"
        else:
            res = {"h2s": PF.oc_q4(sz)}
            res["targets_met"] = res["h2s"].get("targets_met", False)
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "families"}, default=float)[:2500])


if __name__ == "__main__":
    sys.exit(main())
