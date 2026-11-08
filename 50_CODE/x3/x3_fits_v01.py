#!/usr/bin/env python3
"""X3 analysis (a) refits (x3-core agent, x3_fits_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan section 2(a).

Refits B4 (one pooled CRC threshold per step), B6 (hierarchical CRC from L1, no motion strata, split by in-path: 'B6_ip', and the
pooled 'B6' reported) and B9 (the norm-ball CRC radius on the records) at the nominal levels
delta' in {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005, 0.0025, 0.001}, per fold of C1_FOLDS_375_v01 (calibration = the other four
folds' logs), on the items of record, through the frozen fit functions:
  * c1_crc_exact_v01.crc_threshold_exact(U, s, delta=delta') for B4 and B9 (exact CRC decisions);
  * m_lib_v04.fit_hier(U, unit, lv, start=1, n_min, stat=crc_threshold_exact(., ., delta=delta')) for B6, separately on the
    not-in-path and in-path items for B6_ip (c1_crc_exact_v01.split_fit_exact's loop; split_fit_exact and fit_hier_exact take no
    delta argument, so the loop is written here with the same two calls), n_min = ceil(1/delta') - 1 (exact rational arithmetic);
  * the items, records, levels and unit masks exactly as c1_fit_v02.main / fit_arms (J.load_items, c1_fit_v02.load_records,
    M.levels, U = D / sd, norm = hypot(dx, dy)); the 2.5 to 4 s step dicts are copies of the 2 s dict, as of record.
Check: delta' = 0.05 must reproduce fits_within_<t>.json of record exactly for B4, B6, B6_ip and B9 (all folds and steps).
A grid point is not fittable when the frozen rule returns no threshold (crc_threshold_exact returns None when the calibration
units n satisfy 1/(n + 1) > delta', i.e. n < ceil(1/delta') - 1; fit_hier leaves NaN where no level has n_min units); that point is
reported as not fittable with the reason, as plan section 0 requires, and is not run.
Usage: python -B x3_fits_v01.py --tracker t1 --out-dir <dir>
"""
import argparse
import json
import math
import os
import sys
import time
from fractions import Fraction
from functools import partial

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(X3))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "c1_av2"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
sys.path.insert(0, X3)
import c1_crc_exact_v01 as X  # noqa: E402
import c1_fit_v02 as F  # noqa: E402
import k8_joint_fit_v02 as J  # noqa: E402
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

M = X.M
STEPS = J.STEPS
CC = J.CC_STEPS
N_L0 = M.N_L0
GRID = (0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005, 0.0025, 0.001)
ARMS = ("B4", "B6", "B6_ip", "B9")


def n_min_of(d):
    return int(math.ceil(Fraction(1) / Fraction(repr(float(d))))) - 1


def split_fit_delta(U, s, lv, ip, start, n_min, stat):
    out, src = np.full(2 * N_L0, np.nan), np.full(2 * N_L0, -1)
    for part in (0, 1):
        sel = ip == part
        thr, so = M.fit_hier(U[sel], s[sel], [x[sel] for x in lv], start, n_min, stat=stat)
        out[part * N_L0:(part + 1) * N_L0], src[part * N_L0:(part + 1) * N_L0] = thr, so
    return out, src


def fit_fold(it, lv, U, rc, nrm, mask, d):
    nm = n_min_of(d)
    stat = partial(X.crc_threshold_exact, delta=d)
    ip = it["inpath"].astype(int)
    out, notes = {}, []
    for h in range(CC):
        sel = (it["h"] == h) & mask[it["s"]]
        Us, ss, lvs, ips = U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel]
        b6ip, b6src = split_fit_delta(Us, ss, lvs, ips, 1, nm, stat)
        b6pool, _ = M.fit_hier(Us, ss, lvs, 1, nm, stat=stat)
        b4 = X.crc_threshold_exact(Us, ss, delta=d)
        rsel = (rc["h"] == h) & mask[rc["s"]]
        b9 = X.crc_threshold_exact(nrm[rsel], rc["s"][rsel], delta=d)
        units = {"items": int(len(np.unique(ss))), "items_inpath": int(len(np.unique(ss[ips == 1]))),
                 "items_not_inpath": int(len(np.unique(ss[ips == 0]))), "records": int(len(np.unique(rc["s"][rsel])))}
        e = {"B4": None if b4 is None else float(b4), "B9": None if b9 is None else float(b9),
             "B6": None if not np.all(np.isfinite(b6pool)) else b6pool.tolist(),
             "B6_ip": None if not np.all(np.isfinite(b6ip)) else b6ip.tolist(),
             "B6_ip_src": b6src.astype(int).tolist(), "units": units, "n_min": nm}
        if b4 is None:
            notes.append("h%d B4: %d calibration units < n_min %d (1/(n+1) > delta')" % (h, units["items"], nm))
        if b9 is None:
            notes.append("h%d B9: %d calibration units < n_min %d" % (h, units["records"], nm))
        if e["B6_ip"] is None:
            notes.append("h%d B6_ip: %d of 192 thresholds undefined (no level with n_min = %d units; in-path units %d, not-in-path %d)"
                         % (h, int(np.sum(~np.isfinite(b6ip))), nm, units["items_inpath"], units["items_not_inpath"]))
        out[STEPS[h]] = e
    for h in range(CC, len(STEPS)):
        out[STEPS[h]] = dict(out[STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
    return out, notes


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True, choices=["t1", "t3", "tab"])
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--grid", nargs="*", type=float, default=list(GRID))
    a = ap.parse_args(argv)
    t0 = time.time()
    C.assert_run_log("x3_fits start %s" % a.tracker)
    rec = json.load(open(C.FITS_REC[a.tracker]))
    items = [x["file"] for x in rec["items"]]
    for x in rec["items"]:
        assert C.sha256(x["file"]) == x["sha256"], "items of record changed: " + x["file"]
    fj = json.load(open(C.FOLDS))
    assert C.sha256(C.FOLDS) == rec["folds_sha256"]
    fold_of = {u: int(f) for u, f in fj["fold_of_log"].items()}
    k = int(fj["k"])
    with heavy_lock("x3-core: (a) refits %s" % a.tracker):
        it, names, info = J.load_items(items)
        assert set(names) == set(fold_of), "the items' units differ from the folds' units"
        rc = F.load_records(items, list(names))
        fold_unit = np.array([fold_of.get(n, -1) for n in names], int)
        lv = M.levels(it, it["m"])
        assert np.array_equal(lv[0], it["l0"])
        U = it["D"] / it["sd"]
        nrm = np.hypot(rc["dx"], rc["dy"])
        summary = {}
        for d in a.grid:
            t1 = time.time()
            out = {"stamp": C.STAMP, "tracker": a.tracker, "delta_prime": d, "n_min": n_min_of(d), "folds": C.FOLDS,
                   "folds_sha256": C.sha256(C.FOLDS), "items": info, "fits_of_record": C.FITS_REC[a.tracker],
                   "fold_of_scene": fold_of, "fits": {}, "not_fittable_notes": {}, "rule": __doc__.split("Check:")[0].strip()}
            fittable = {x: True for x in ARMS}
            for f in range(k):
                mask = (fold_unit != f) & (fold_unit >= 0)
                fd, notes = fit_fold(it, lv, U, rc, nrm, mask, d)
                out["fits"][str(f)] = fd
                if notes:
                    out["not_fittable_notes"][str(f)] = notes
                for x in ARMS:
                    if any(fd[s][x] is None for s in STEPS):
                        fittable[x] = False
            out["fittable"] = fittable
            # descriptive: B6_ip's source levels (0 = L0 own stratum is never used: start = 1; 1 = L1, 2 = L2, 3 = L3)
            src = np.array([fd_[s]["B6_ip_src"] for fd_ in out["fits"].values() for s in STEPS[:CC]])
            out["B6_ip_source_level_shares"] = {str(lvl): float(np.mean(src == lvl)) for lvl in (-1, 1, 2, 3)}
            check = None
            if abs(d - 0.05) < 1e-12:
                check = {}
                for f in range(k):
                    for s in STEPS:
                        r_, m_ = rec["fits"][str(f)][s], out["fits"][str(f)][s]
                        for x in ARMS:
                            eq = (r_[x] == m_[x]) if not isinstance(r_[x], list) else (list(map(float, r_[x])) == list(map(float, m_[x])))
                            check["%d/%s/%s" % (f, s, x)] = bool(eq)
                out["check_vs_record"] = {"all_equal": bool(all(check.values())), "compared": len(check),
                                          "mismatches": [q for q, v in check.items() if not v]}
            name = "fits_x3a_%s_d%s.json" % (a.tracker, repr(d))
            C.jdump(os.path.join(a.out_dir, name), out)
            summary[repr(d)] = {"file": name, "sha256": C.sha256(os.path.join(a.out_dir, name)), "fittable": fittable, "n_min": n_min_of(d),
                                "check_vs_record": out.get("check_vs_record"), "notes_first": sum(out["not_fittable_notes"].values(), [])[:6],
                                "B6_ip_source_level_shares": out["B6_ip_source_level_shares"], "seconds": round(time.time() - t1, 1)}
            print("delta' %s: fittable %s  %.0f s%s" % (d, fittable, time.time() - t1,
                                                        ("  check %s" % out["check_vs_record"]["all_equal"]) if check is not None else ""), flush=True)
            C.live("(a) refits %s" % a.tracker, list(a.grid).index(d) + 1, len(a.grid))
    C.assert_run_log("x3_fits end %s" % a.tracker)
    C.jdump(os.path.join(a.out_dir, "fits_x3a_%s_summary.json" % a.tracker),
            {"stamp": C.STAMP, "tracker": a.tracker, "grid": list(a.grid), "by_delta_prime": summary, "seconds": round(time.time() - t0, 1),
             "code_sha256": C.code_hashes([os.path.abspath(__file__), X.__file__, M.__file__, F.__file__, J.__file__])})
    print("X3 FITS V01 DONE")


if __name__ == "__main__":
    main()
