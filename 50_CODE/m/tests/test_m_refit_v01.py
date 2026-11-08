#!/usr/bin/env python3
"""Tests of the log resampling and of the E2 two-sample refit bootstrap (Claude line, v01, 31 Oct 2026). Simulated data
only. T14: resample_logs with unit multiplicities reproduces the split; duplicated logs become distinct units and give
the same CRC threshold as explicit duplication. T15: with train and val drawn from the same simulated law, the E2
decision (HM1 rule with the 0.03 margin) holds in at least 90 % of datasets.
Usage: python test_m_refit_v01.py --reps 40 --out <json>
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m_lib_v01 as M  # noqa: E402
from test_m_units_v01 import sim_items  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--boot", type=int, default=200)
    a = ap.parse_args()
    out, ok = {}, {}
    items, recs, _ = sim_items(np.random.default_rng(7), n_logs=12, scenes_per_log=5)
    same, srec = M.resample_logs(items, recs, np.ones(12, int))
    ok["T14a_identity"] = all(np.array_equal(same[k], items[k], equal_nan=True) for k in ("s", "lg", "g", "r", "a", "D", "V")) \
        and np.array_equal(srec["s"], recs["s"]) and same["n_scenes"] == items["n_scenes"]
    mult = np.zeros(12, int)
    mult[3], mult[5] = 2, 1
    dup, _ = M.resample_logs(items, recs, mult)
    sel3, sel5 = items["lg"] == 3, items["lg"] == 5
    ok["T14b_counts"] = len(dup["D"]) == 2 * sel3.sum() + sel5.sum() and dup["n_scenes"] == 15 and dup["n_logs"] == 3 \
        and len(np.unique(dup["s"])) == 15 and len(np.unique(dup["lg"])) == 3
    U = dup["D"] / np.sqrt(dup["V"] + M.SIGMA_A ** 2)
    Ue = np.concatenate([items["D"][sel3], items["D"][sel3], items["D"][sel5]]) / np.sqrt(
        np.concatenate([items["V"][sel3], items["V"][sel3], items["V"][sel5]]) + M.SIGMA_A ** 2)
    se = np.concatenate([items["s"][sel3], items["s"][sel3] + 1000, items["s"][sel5]])
    ok["T14c_crc_equal"] = M.L.crc_threshold(U, dup["s"]) == M.L.crc_threshold(Ue, se)

    hits, holds = [], 0
    for rep in range(a.reps):
        rng = np.random.default_rng(300 + rep)
        tr, trr, _ = sim_items(rng, n_logs=30, scenes_per_log=10)
        va, var, _ = sim_items(rng, n_logs=10, scenes_per_log=8)
        Pt, Pv = M.prepare(tr, trr, {}), M.prepare(va, var, {})
        fit = M.fit_methods(tr, trr, Pt, np.ones(tr["n_scenes"], bool), {})
        cnt = M.counts_by_l0(va, Pv["m"])
        rev = {M.l0_name(i): i for i in range(M.N_L0)}
        ev = sorted(rev[k] for k, v in cnt.items() if v["scenes"] >= M.N_EVAL)
        allv = np.ones(len(va["D"]), bool)
        brng = np.random.default_rng(900 + rep)

        def replicates():
            for _ in range(a.boot):
                mt = brng.multinomial(tr["n_logs"], np.full(tr["n_logs"], 1.0 / tr["n_logs"]))
                mv = brng.multinomial(va["n_logs"], np.full(va["n_logs"], 1.0 / va["n_logs"]))
                tb, tbr = M.resample_logs(tr, trr, mt)
                fb = M.fit_methods(tb, tbr, M.prepare(tb, tbr, {}), np.ones(tb["n_scenes"], bool), {})
                yield {"Mstar": M.margins(va, Pv, fb, allv)["Mstar"]}, mv[va["scene_log_idx"]].astype(float)
        st = M.eval_stats_refit(va, Pv, {"Mstar": M.margins(va, Pv, fit, allv)["Mstar"]}, ev, replicates())
        m = st["methods"]["Mstar"]
        h = (not m["any_sig_under"]) and m["E_bar_ub95"] <= M.DELTA + 0.03
        holds += int(h)
        hits.append([m["E_bar"], m["E_bar_ub95"], len(ev)])
    out["T15_rate_HM6_holds"] = holds / a.reps
    out["T15_mean_Ebar_ub_nstrata"] = np.mean(hits, 0).round(4).tolist()
    ok["T15_refit_null_rate"] = out["T15_rate_HM6_holds"] >= 0.9
    ok = {k: bool(v) for k, v in ok.items()}
    out["ok"], out["all_ok"] = ok, all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out))


if __name__ == "__main__":
    sys.exit(main())
