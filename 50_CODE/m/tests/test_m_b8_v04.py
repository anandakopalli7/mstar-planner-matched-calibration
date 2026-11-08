#!/usr/bin/env python3
"""B8 (stratified variance matching) behaves as designed, with the v02 paired-contrast rule (Claude line, v04, 31 Oct 2026; ported to m_lib_v04).
Simulated data only. T16a: zero-mean Gaussian scores -> B8's mean held-out exceedance is near 0.05. T16b: in the lateral
turning strata the score is a mixture, 90 % N(0, 0.3^2) and 10 % N(2, 0.5^2), so the variance-matched multiplier 1.17
leaves 9.5 % exceedance -> B8 fails against M* (paired) in most datasets while M* is not flagged.
Usage: python test_m_b8_v04.py --reps 20 --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m_lib_v04 as M  # noqa: E402
from test_m_units_v04 import one_cv_fixed, sim_items  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=20)
    a = ap.parse_args()
    gauss, flag_b8, m_ok = [], 0, 0
    for rep in range(a.reps):
        it, rc, mot = sim_items(np.random.default_rng(4000 + rep))
        st = one_cv_fixed(it, rc, "g%d" % rep, B=200)[0]
        gauss.append(st["methods"]["B8"]["E_bar"])
        rng = np.random.default_rng(6000 + rep)
        it, rc, mot = sim_items(rng)
        k = (it["a"] == 1) & (mot == 2)
        sd = np.sqrt(it["V"] + M.SIGMA_A ** 2)
        mix = np.where(rng.random(len(sd)) < 0.1, 2.0 + 0.5 * rng.standard_normal(len(sd)), 0.3 * rng.standard_normal(len(sd)))
        it["D"] = np.where(k, mix * sd, it["D"])
        st = one_cv_fixed(it, rc, "h%d" % rep, B=200)[0]
        flag_b8 += int(bool(M.failures([st], "B8", "B8-Mstar")))
        m_ok += int(not st["methods"]["Mstar"]["any_sig_under"])
    out = {"T16a_mean_Ebar_B8_gaussian": float(np.mean(gauss)), "T16b_rate_B8_fails_paired": flag_b8 / a.reps,
           "T16b_rate_Mstar_not_flagged": m_ok / a.reps}
    ok = {"T16a": abs(out["T16a_mean_Ebar_B8_gaussian"] - 0.05) < 0.01, "T16b_B8_flagged": out["T16b_rate_B8_fails_paired"] >= 0.8,
          "T16b_Mstar_holds": out["T16b_rate_Mstar_not_flagged"] >= 0.85}
    out["ok"] = {k: bool(v) for k, v in ok.items()}
    out["all_ok"] = all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
