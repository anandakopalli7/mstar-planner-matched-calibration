#!/usr/bin/env python3
"""Log resampling and the E2 refit bootstrap through m_run_v02.run_e2 (Claude line, v02, 31 Oct 2026). Simulated data only.
T14: resample_logs with unit multiplicities reproduces the split; duplicated logs become distinct units with their
original ids kept; CRC on the copy equals CRC on explicit duplication.
T15: train (50 logs) and val (18 logs) from the same law; HM6 must hold in >= 90 % of datasets.
T15b: val lateral turning scale x 1.6 (true exceedance about 0.2 in that cell); the rate at which HM6 fails is reported.
Usage: python test_m_refit_v02.py --reps 30 --boot 150 --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m_lib_v02 as M  # noqa: E402
import m_run_v02 as R  # noqa: E402
from test_m_units_v02 import TAU, sim_items  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=30)
    ap.add_argument("--boot", type=int, default=150)
    a = ap.parse_args()
    out, ok = {}, {}
    items, recs, _ = sim_items(np.random.default_rng(7), n_logs=12, scenes_per_log=5)
    same, srec = M.resample_logs(items, recs, np.ones(12, int))
    ok["T14a_identity"] = all(np.array_equal(same[k], items[k], equal_nan=True) for k in ("s", "lg", "g", "r", "a", "D", "V")) \
        and np.array_equal(srec["s"], recs["s"]) and same["n_scenes"] == items["n_scenes"] \
        and np.array_equal(same["orig_scene"], np.arange(items["n_scenes"])) and np.array_equal(same["orig_log"], np.arange(12))
    mult = np.zeros(12, int)
    mult[3], mult[5] = 2, 1
    dup, _ = M.resample_logs(items, recs, mult)
    sel3, sel5 = items["lg"] == 3, items["lg"] == 5
    ok["T14b_counts"] = len(dup["D"]) == 2 * sel3.sum() + sel5.sum() and dup["n_scenes"] == 15 and dup["n_logs"] == 3 \
        and len(np.unique(dup["s"])) == 15 and len(np.unique(dup["lg"])) == 3 and sorted(dup["orig_log"].tolist()) == [3, 3, 5]
    U = dup["D"] / np.sqrt(dup["V"] + M.SIGMA_A ** 2)
    Ue = np.concatenate([items["D"][sel3], items["D"][sel3], items["D"][sel5]]) / np.sqrt(
        np.concatenate([items["V"][sel3], items["V"][sel3], items["V"][sel5]]) + M.SIGMA_A ** 2)
    se = np.concatenate([items["s"][sel3], items["s"][sel3] + 1000, items["s"][sel5]])
    ok["T14c_crc_equal"] = M.L.crc_threshold(U, dup["s"]) == M.L.crc_threshold(Ue, se)

    for tag, shift in (("T15_null", 1.0), ("T15b_shift1.6", 1.6)):
        holds, rows = 0, []
        for rep in range(a.reps):
            rng = np.random.default_rng([M.SEED, 300 + rep, int(shift * 10)])
            tr, trr, _ = sim_items(rng, n_logs=50, scenes_per_log=6, items_per_scene=30)
            tv = lambda g_, a_, m_: TAU(g_, a_, m_) * np.where((g_ == 0) & (a_ == 1) & (m_ == 2), shift, 1.0)
            va, var, _ = sim_items(rng, n_logs=18, scenes_per_log=8, items_per_scene=30, tau=tv)
            cells = M.make_cells(va, M.motion_state(va), "E2")
            e = R.run_e2(tr, trr, va, var, {}, cells, "refit-test|%s|%d" % (tag, rep), B=a.boot)
            holds += int(e["hypotheses"]["HM6"])
            rows.append([e["hypotheses"]["pooled_E"], e["hypotheses"]["pooled_ub"], len(cells)])
        out[tag + "_HM6_hold_rate"] = holds / a.reps
        out[tag + "_mean_pooledE_ub_ncells"] = np.mean(rows, 0).round(4).tolist()
    ok["T15_null_rate"] = out["T15_null_HM6_hold_rate"] >= 0.9
    ok = {k: bool(v) for k, v in ok.items()}
    out["ok"], out["all_ok"] = ok, all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
