#!/usr/bin/env python3
"""B8 (stratified variance matching) behaves as designed (Claude line, v01, 31 Oct 2026). Simulated data only.
T16a: zero-mean Gaussian scores in every stratum -> B8's mean held-out exceedance is near 0.05 (it is the Gaussian
rule). T16b: in the lateral turning strata the score is a mixture, 90 % N(0, 0.3^2) and 10 % N(2, 0.5^2) (most cars on track, a
minority far off), so the variance-matched multiplier 1.17 leaves 9.5 % exceedance -> B8 is flagged
(HM2c) in most datasets while M* is not (HM1).
Usage: python test_m_b8_v01.py --reps 20 --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m_lib_v01 as M  # noqa: E402
from test_m_units_v01 import fold_eval, sim_items  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=20)
    a = ap.parse_args()
    gauss, flag_b8, hold_m = [], 0, 0
    for rep in range(a.reps):
        it, rc, mot = sim_items(np.random.default_rng(4000 + rep))
        st, _, _ = fold_eval(it, rc, {}, "g%d" % rep, B=200)
        gauss.append(st["methods"]["B8"]["E_bar"])
        rng = np.random.default_rng(6000 + rep)
        it, rc, mot = sim_items(rng)
        k = (it["a"] == 1) & (mot == 2)
        sd = np.sqrt(it["V"] + M.SIGMA_A ** 2)
        mix = np.where(rng.random(len(sd)) < 0.1, 2.0 + 0.5 * rng.standard_normal(len(sd)), 0.3 * rng.standard_normal(len(sd)))
        it["D"] = np.where(k, mix * sd, it["D"])
        st, _, _ = fold_eval(it, rc, {}, "h%d" % rep, B=200)
        flag_b8 += int(st["hypotheses"]["HM2c"])
        hold_m += int(st["hypotheses"]["HM1"])
    out = {"T16a_mean_Ebar_B8_gaussian": float(np.mean(gauss)), "T16b_rate_HM2c": flag_b8 / a.reps, "T16b_rate_HM1_Mstar": hold_m / a.reps}
    ok = {"T16a": abs(out["T16a_mean_Ebar_B8_gaussian"] - 0.05) < 0.01, "T16b_B8_flagged": out["T16b_rate_HM2c"] >= 0.8,
          "T16b_Mstar_holds": out["T16b_rate_HM1_Mstar"] >= 0.85}
    out["ok"] = {k: bool(v) for k, v in ok.items()}
    out["all_ok"] = all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
