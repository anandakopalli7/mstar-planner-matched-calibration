#!/usr/bin/env python3
"""X3 amendment A4 (1): M* refitted at delta' (x3-core agent, x3_fits_a4_v01, 7 Nov 2026). Added after review (amendment A4).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).

M*'s fit rule of record (c1_fit_v02.fit_arms: 'Mstar_ip' = split_fit_exact(U, s, lv, ip, start 0), 'Mstar' = fit_hier_exact(start 0),
'Mstar_ip_src'; the 2.5 to 4 s step dicts copies of the 2 s dict) with every CRC decision at delta = delta' (crc_threshold_exact's
delta argument, through m_lib_v04.fit_hier's stat, as x3_fits_v01 does for B4 / B6 / B9) and n_min = ceil(1/delta') - 1, per fold
of C1_FOLDS_375_v01 on the items of record. delta' in {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005}. Check: delta' = 0.05 reproduces
Mstar_ip, Mstar_ip_src and Mstar of fits_within_<t>.json exactly (all folds, all 8 steps). A threshold <= 0 is recorded (the record's
fit asserts > 0 only for the joint arms).
Usage: python -B x3_fits_a4_v01.py --tracker t1
"""
import argparse
import json
import os
import sys
import time
from functools import partial

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_fits_v01 as FV  # noqa: E402
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

X, M, F, J = FV.X, FV.M, FV.F, FV.J
STEPS, CC = FV.STEPS, FV.CC
GRID = (0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005)
LABEL = "added after review (amendment A4)"
OUT = os.path.join(C.OUT, "a4_review", "fits")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True, choices=["t1", "t3"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.assert_run_log("x3_fits_a4 start")
    rec = json.load(open(C.FITS_REC[a.tracker]))
    items = [x["file"] for x in rec["items"]]
    for x in rec["items"]:
        assert C.sha256(x["file"]) == x["sha256"]
    fold_of = {u: int(f) for u, f in json.load(open(C.FOLDS))["fold_of_log"].items()}
    summary = {"stamp": C.STAMP, "label": LABEL, "tracker": a.tracker, "by_delta_prime": {}}
    with heavy_lock("x3-core: A4 (1) M* refits %s" % a.tracker):
        it, names, info = J.load_items(items)
        fold_unit = np.array([fold_of[n] for n in names], int)
        lv = M.levels(it, it["m"])
        U = it["D"] / it["sd"]
        ip = it["inpath"].astype(int)
        for d in GRID:
            nm = FV.n_min_of(d)
            stat = partial(X.crc_threshold_exact, delta=d)
            out = {"stamp": C.STAMP, "label": LABEL, "tracker": a.tracker, "delta_prime": d, "n_min": nm, "folds_sha256": C.sha256(C.FOLDS),
                   "items": info, "fold_of_scene": fold_of, "fits": {}, "rule": __doc__.split("Usage:")[0].strip()}
            ok, nonpos = True, 0
            for f in range(5):
                mask = fold_unit != f
                fd = {}
                for h in range(CC):
                    sel = (it["h"] == h) & mask[it["s"]]
                    Us, ss, lvs, ips = U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel]
                    mip, src = FV.split_fit_delta(Us, ss, lvs, ips, 0, nm, stat)
                    mpool, _ = M.fit_hier(Us, ss, lvs, 0, nm, stat=stat)
                    if not (np.all(np.isfinite(mip))):
                        ok = False
                    nonpos += int(np.sum(np.isfinite(mip) & (mip <= 0)))
                    fd[STEPS[h]] = {"Mstar": [None if not np.isfinite(v) else float(v) for v in mpool],
                                    "Mstar_ip": [None if not np.isfinite(v) else float(v) for v in mip], "Mstar_ip_src": src.astype(int).tolist()}
                for h in range(CC, len(STEPS)):
                    fd[STEPS[h]] = dict(fd[STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
                out["fits"][str(f)] = fd
            out["fittable"], out["nonpositive_thresholds"] = ok, nonpos
            src_all = np.array([out["fits"][f_][s_]["Mstar_ip_src"] for f_ in out["fits"] for s_ in STEPS[:CC]])
            out["fallback_share"] = float(np.mean(src_all > 0))
            chk = None
            if d == 0.05:
                chk = all(out["fits"][str(f)][s_][k_] == rec["fits"][str(f)][s_][k_] for f in range(5) for s_ in STEPS
                          for k_ in ("Mstar_ip", "Mstar_ip_src", "Mstar"))
                out["check_vs_record"] = bool(chk)
            p = os.path.join(OUT, "fits_x3a4_Mstar_%s_d%s.json" % (a.tracker, repr(d)))
            C.jdump(p, out)
            summary["by_delta_prime"][repr(d)] = {"file": p, "sha256": C.sha256(p), "fittable": ok, "n_min": nm, "nonpositive": nonpos,
                                                  "fallback_share": out["fallback_share"], "check_vs_record": chk}
            print("M* delta' %s fittable %s fallback %.3f%s" % (d, ok, out["fallback_share"], ("  check %s" % chk) if chk is not None else ""), flush=True)
    summary["seconds"] = round(time.time() - t0, 1)
    C.assert_run_log("x3_fits_a4 end")
    C.jdump(os.path.join(OUT, "fits_x3a4_Mstar_%s_summary.json" % a.tracker), summary)
    assert summary["by_delta_prime"]["0.05"]["check_vs_record"], "X3 STOP (A4 1): delta' = 0.05 does not reproduce M* of record"


if __name__ == "__main__":
    main()
