#!/usr/bin/env python3
"""x3_ref_qfit_ext_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan amendment 20_DESIGN/X3_PLAN_AMENDMENT_A2_v01.md (sha256 b50779e0...), analysis (e2-ext).

x3_ref_qfit_v01's q-fit repeated exactly, with the grid extended downward to {0, 1/64, 1/32, 1/16, 1/8, 0.25, 0.5, 1, 2, 4, 8, 16, 32}
and the same rule: per tracker, held-out fold f and class group g, the smallest q whose share(D / sd(q) > z_0.95) on the training
folds' relied items of group g (steps 0.5 ... 2 s pooled) is <= 0.05; none: q = 32, flagged. q = 0 means pred_cov = A_h (the Q = 0
propagation of e2_qrefit/qzero_<t>/, taken as is); q = 1 means S (the cache's covariance, bitwise). The projection, the item-record
linkage and the substitution are x3_ref_qfit_v01's own functions (imported; that file is not changed).
Checks: at the grid points shared with the plan grid, the training shares equal qfit_table_<t>.json's exactly, and wherever the
extended choice is >= 0.25 it equals the plan-grid choice.
Outputs (new files only): e2_qrefit/qfit_table_ext_<t>.json, e2_qrefit/subst_ext_<t>/<log>.npz (float64) + MANIFEST.json.
Usage: python -B x3_ref_qfit_ext_v01.py --trk t1 t3
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402
import x3_ref_qfit_v01 as QF  # noqa: E402

S = QF.S
GRID = (0.0, 1.0 / 64, 1.0 / 32, 1.0 / 16, 1.0 / 8, 0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
Z95, DELTA, GROUPS = QF.Z95, QF.DELTA, QF.GROUPS
AMEND = os.path.join(C.W, "20_DESIGN", "X3_PLAN_AMENDMENT_A2_v01.md")
AMEND_SHA = "b50779e08ce73ba00d3a148b59eec0b3a94095c7c4521ab85f461f649d3c3443"


def cov_at(A, Smat, q):
    """q = 0: A itself; q = 1: S itself; else A + q (S - A) (x3_ref_qfit_v01.subst_cov). q: scalar or per-row array (broadcast)."""
    q = np.asarray(q, float)
    if q.ndim == 0:
        return A.copy() if float(q) == 0.0 else QF.subst_cov(A, Smat, q)
    out = QF.subst_cov(A, Smat, q)
    zero = q == 0.0
    out[zero] = A[zero]
    return out


def run_tracker(trk, folds):
    t0 = time.time()
    qdir = os.path.join(C.E2, "qzero_%s" % trk)
    qman = json.load(open(os.path.join(qdir, "MANIFEST.json")))
    assert qman["validation"]["pass"], "the Q = 0 re-propagation did not validate"
    plan_tab = json.load(open(os.path.join(C.E2, "qfit_table_%s.json" % trk)))
    fold_of = {u: int(f) for u, f in folds["fold_of_log"].items()}
    z = np.load(C.ITEMS_REC[trk])
    names = [str(x) for x in z["scene_names"]]
    it = {k: z["item_" + k] for k in ("s", "h", "g", "a", "D", "sd", "pair", "ref_relied")}
    rc = {k: z["rec_" + k] for k in ("s", "h", "pair", "row", "yaw", "sxx", "sxy", "syy")}
    key_rec = rc["s"].astype(np.int64) * 10_000_000 + rc["pair"]
    order = np.argsort(key_rec)
    key_it = it["s"].astype(np.int64) * 10_000_000 + it["pair"]
    ri = order[np.searchsorted(key_rec[order], key_it)]
    assert np.array_equal(key_rec[ri], key_it) and np.array_equal(rc["h"][ri], it["h"]), "item-record linkage failed"
    A_rec = np.full((len(rc["s"]), 3), np.nan)
    for si, sc in enumerate(names):
        m = rc["s"] == si
        if m.any():
            A_rec[m] = np.load(os.path.join(qdir, sc + ".npz"))["pred_cov"][rc["row"][m], rc["h"][m]]
    assert np.all(np.isfinite(A_rec)), "A missing for a record"
    S_rec = np.stack([rc["sxx"], rc["sxy"], rc["syy"]], -1)
    yaw_i, a_i = rc["yaw"][ri], it["a"]
    sd1 = QF.project(S_rec[ri], yaw_i, a_i)
    sd_check = float(np.max(np.abs(sd1 - it["sd"])))
    assert sd_check <= 1e-12, "sd(1) differs from the item's sd of record: %g" % sd_check
    rel = it["ref_relied"]
    fold_i = np.array([fold_of[n] for n in names])[it["s"]]
    U = {}
    for q in GRID:
        sdq = sd1 if q == 1.0 else QF.project(cov_at(A_rec[ri], S_rec[ri], q), yaw_i, a_i)
        U[q] = it["D"] / sdq > Z95
    table, curve, flags, mism = {}, {}, [], []
    for f in range(int(folds["k"])):
        table[str(f)], curve[str(f)] = {}, {}
        for g in range(4):
            m = rel & (fold_i != f) & (it["g"] == g)
            n = int(m.sum())
            shares = {repr(q): (float(U[q][m].mean()) if n else None) for q in GRID}
            ok = [q for q in GRID if n and U[q][m].mean() <= DELTA]
            q_sel = ok[0] if ok else GRID[-1]
            if not ok:
                flags.append({"fold": f, "group": GROUPS[g], "reason": "no grid point qualifies" if n else "no training items", "items": n})
            table[str(f)][str(g)] = q_sel
            curve[str(f)][str(g)] = {"items": n, "logs": int(len(np.unique(it["s"][m]))), "exceedance_share_by_q": shares}
            pc = plan_tab["training_curve"][str(f)][str(g)]
            for q in QF.GRID:                                      # shared grid points: identical shares
                if pc["exceedance_share_by_q"][str(q)] != shares[repr(q)]:
                    mism.append(("share", f, g, q))
            if q_sel >= 0.25 and q_sel != plan_tab["q_table"][str(f)][str(g)]:
                mism.append(("choice", f, g, q_sel))
    assert not mism, "extended fit disagrees with the plan-grid fit at shared points: %s" % mism[:5]
    out = {"stamp": C.STAMP, "amendment": "X3_PLAN_AMENDMENT_A2_v01.md", "amendment_sha256": C.sha256_path(AMEND), "tracker": trk,
           "grid": GRID, "grid_keys": [repr(q) for q in GRID], "z": Z95, "delta": DELTA, "groups": GROUPS,
           "rule": "smallest q in the extended grid with share(D / sd(q) > z_0.95) <= 0.05 on the training folds' relied items of group g "
                   "(steps 0.5 ... 2 s pooled); none: q = 32, flagged; q = 0: pred_cov = A_h (no process noise over the horizon)",
           "q_table": table, "training_curve": curve, "flags": flags,
           "cells_q0": [[int(f), GROUPS[int(g)]] for f, gs in table.items() for g, q in gs.items() if q == 0.0],
           "items": C.ITEMS_REC[trk], "items_sha256": C.sha256_path(C.ITEMS_REC[trk]), "folds_sha256": C.sha256_path(C.FOLDS),
           "qzero_manifest_sha256": C.sha256_path(os.path.join(qdir, "MANIFEST.json")),
           "plan_grid_table": os.path.join(C.E2, "qfit_table_%s.json" % trk),
           "plan_grid_table_sha256": C.sha256_path(os.path.join(C.E2, "qfit_table_%s.json" % trk)),
           "checks": {"sd1_vs_item_sd_max_abs": sd_check, "relied_items": int(rel.sum()),
                      "shares_at_plan_grid_points_equal_plan_table": True, "choices_ge_0.25_equal_plan_table": True}}
    sdir = os.path.join(C.E2, "subst_ext_%s" % trk)
    os.makedirs(sdir, exist_ok=True)
    cman = json.load(open(os.path.join(C.CACHE[trk], "MANIFEST.json")))
    man = {"stamp": C.STAMP, "amendment_sha256": out["amendment_sha256"], "tracker": trk, "q_table": table, "fold_of_scene": fold_of,
           "folds_sha256": out["folds_sha256"], "cache": C.CACHE[trk],
           "cache_manifest_sha256": C.sha256_path(os.path.join(C.CACHE[trk], "MANIFEST.json")), "dtype": "float64", "scenes": {}}
    rec_vs_cache, rows_tot = 0.0, {}
    for i, sc in enumerate(sorted(cman["scenes"])):
        p_out = os.path.join(sdir, sc + ".npz")
        cp = os.path.join(C.CACHE[trk], sc + ".npz")
        assert C.sha256_path(cp) == cman["scenes"][sc]["sha256"], "cache differs from its manifest: " + sc
        zc = np.load(cp)
        trp = zc["tr_pred"] if "tr_pred" in zc.files else np.zeros((0, 8, 5))
        Aq = np.load(os.path.join(qdir, sc + ".npz"))
        A = Aq["pred_cov"]
        assert A.shape == (len(trp), 8, 3) and np.array_equal(Aq["tr_k"], zc["tr_k"] if len(trp) else np.zeros(0, np.int64)), "alignment: " + sc
        Smat = trp[:, :, 2:5]
        f = fold_of[sc]
        g_row = S.GROUP_OF_CLS[zc["tr_cls"]] if len(trp) else np.zeros(0, int)
        q_row = np.array([table[str(f)][str(int(g))] for g in g_row], float)
        cov = cov_at(A, Smat, np.broadcast_to(q_row[:, None], (len(q_row), 8)).copy())
        si = names.index(sc)
        m = rc["s"] == si
        if m.any():
            rec_vs_cache = max(rec_vs_cache, float(np.max(np.abs(Smat[rc["row"][m], rc["h"][m]] - S_rec[m]))))
        if os.path.exists(p_out):                                  # resume: an existing file must hold exactly this content
            zo = np.load(p_out)
            assert np.array_equal(zo["pred_cov"], cov) and np.array_equal(zo["q_row"], q_row), "existing file differs: " + sc
        else:
            C.save_npz(p_out, pred_cov=cov, tr_k=zc["tr_k"] if len(trp) else np.zeros(0, np.int64), q_row=q_row,
                       g_row=np.asarray(g_row, np.int32), fold=np.array(f), stamp=np.array(C.STAMP),
                       what=np.array("(e2-ext, amendment A2) A + q (S - A) per tr row; q = 0 -> A_h; replaces tr_pred[:, :, 2:5]"))
        rb = {repr(q): int((q_row == q).sum()) for q in GRID if (q_row == q).any()}
        for k_, v_ in rb.items():
            rows_tot[k_] = rows_tot.get(k_, 0) + v_
        man["scenes"][sc] = {"rows": int(len(trp)), "fold": f, "sha256": C.sha256_path(p_out), "rows_by_q": rb}
        if (i + 1) % 25 == 0:
            C.live("e2-ext substitution %s" % trk, i + 1, 375)
    assert rec_vs_cache == 0.0, "record covariance differs from the cache's tr_pred: %g" % rec_vs_cache
    man["rows_by_q_total"] = rows_tot
    man["code_sha256"] = C.code_record([os.path.abspath(__file__), QF.__file__, C.__file__, S.__file__])
    C.save_json(os.path.join(sdir, "MANIFEST.json"), man)
    out["checks"]["record_S_vs_cache_tr_pred_max_abs"] = rec_vs_cache
    out["rows_by_q_total"] = rows_tot
    out["code_sha256"] = man["code_sha256"]
    out["subst_manifest"] = os.path.join(sdir, "MANIFEST.json")
    out["subst_manifest_sha256"] = C.sha256_path(out["subst_manifest"])
    out["seconds"] = round(time.time() - t0, 1)
    C.save_json(os.path.join(C.E2, "qfit_table_ext_%s.json" % trk), out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", nargs="+", required=True, choices=("t1", "t3"))
    a = ap.parse_args(argv)
    C.run_log_ok()
    assert C.sha256_path(AMEND) == AMEND_SHA, "amendment A2 differs from the locked file"
    for trk in a.trk:
        for p in (os.path.join(C.E2, "qfit_table_ext_%s.json" % trk), os.path.join(C.E2, "subst_ext_%s" % trk, "MANIFEST.json")):
            assert not os.path.exists(p), "exists (new files only): " + p
    folds = json.load(open(C.FOLDS))
    from x3_heavylock_v01 import heavy_lock
    with heavy_lock("x3-ref: e2-ext qfit"):
        for trk in a.trk:
            out = run_tracker(trk, folds)
            print(trk, json.dumps(out["q_table"]), "q0 cells", out["cells_q0"], json.dumps(out["flags"]), json.dumps(out["rows_by_q_total"]), flush=True)
    C.run_log_ok()
    print("X3 REF QFIT EXT DONE")


if __name__ == "__main__":
    main()
