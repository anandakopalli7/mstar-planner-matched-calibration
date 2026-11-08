#!/usr/bin/env python3
"""x3_ref_qfit_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md section 2 (e2) (referee concern M8): a process noise re-fitted for
the 2 s horizon (Q-refit).

Decomposition (x3_ref_qzero_v01): S_h(q) = A_h + q (S_h - A_h), A_h the Q = 0 re-propagation (e2_qrefit/qzero_<t>/), S_h = the cache's
tr_pred[:, :, 2:5] (shown equal to the Q = 1 re-propagation and to the horizon of record).
Fit, per tracker, held-out fold f and class group g (k6_sim_v02.GROUP_OF_CLS: 0 car, 1 pedestrian, 2 motorcycle/bicycle,
3 truck/bus/trailer): on the relied items (item_ref_relied) of the items of record whose log is in another fold and whose track is in
group g, at the calibrated steps 0.5 ... 2 s pooled, q_{f,g} is the smallest q in GRID with
    share( D / sd(q) > z_0.95 ) <= 0.05,   sd(q) = sqrt(max(a' (A + q (S - A)) a + 0.10^2, 1e-6))
(a the item's object axis; the projection and floor are k6_sim_v02.strata's, so sd(1) is the item's sd of record). If no grid point
qualifies, q = 32 (the grid maximum) and the cell is flagged.
Substitution files for the runner (e2_qrefit/subst_<t>/<scene>.npz): pred_cov (n, 8, 3) float64 = A + q_{f(scene), g(row)} (S - A)
for every tr row and all 8 steps (rows with q = 1 take S itself, so they are bitwise the cache's covariance), tr_k for the alignment
check, q_row and g_row. The runner replaces tr_pred[:, :, 2:5] by pred_cov after loading the cache and runs arm B0 (margin z_0.95 sd).
Usage: python -B x3_ref_qfit_v01.py --trk t1 t3
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
sys.path.insert(0, os.path.join(C.W, "50_CODE", "k6"))
import k6_sim_v02 as S  # noqa: E402

GRID = (0.25, 0.5, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0)
Z95 = 1.6448536269514722
DELTA = 0.05
GROUPS = ("car", "pedestrian", "motorcycle_bicycle", "truck_bus_trailer")
assert Z95 == S.Z


def project(cov, yaw, a):
    """k6_sim_v02.strata's projection: var along object axis a (0 long, 1 lat) of (Pxx, Pxy, Pyy), then sd with sigma_a and the floor."""
    ax0 = np.where(a == 0, np.cos(yaw), -np.sin(yaw))
    ax1 = np.where(a == 0, np.sin(yaw), np.cos(yaw))
    var = ax0 ** 2 * cov[..., 0] + 2 * ax0 * ax1 * cov[..., 1] + ax1 ** 2 * cov[..., 2]
    return np.sqrt(np.maximum(var + S.SIGMA_A ** 2, 1e-6))


def subst_cov(A, Smat, q):
    """A + q (S - A); q = 1 returns S itself (bitwise)."""
    q = np.asarray(q, float)
    out = A + q[..., None] * (Smat - A) if q.ndim else A + float(q) * (Smat - A)
    if q.ndim:
        one = q == 1.0
        out[one] = Smat[one]
    elif float(q) == 1.0:
        out = Smat.copy()
    return out


def run_tracker(trk, folds):
    t0 = time.time()
    qdir = os.path.join(C.E2, "qzero_%s" % trk)
    qman = json.load(open(os.path.join(qdir, "MANIFEST.json")))
    assert qman["validation"]["pass"], "the Q = 0 re-propagation did not validate: (e2) not done"
    fold_of = {u: int(f) for u, f in folds["fold_of_log"].items()}
    z = np.load(C.ITEMS_REC[trk])
    names = [str(x) for x in z["scene_names"]]
    it = {k: z["item_" + k] for k in ("s", "h", "g", "a", "D", "sd", "pair", "ref_relied")}
    rc = {k: z["rec_" + k] for k in ("s", "h", "pair", "row", "yaw", "sxx", "sxy", "syy")}
    # item -> record (the pair id is the record's running index within its scene)
    key_rec = rc["s"].astype(np.int64) * 10_000_000 + rc["pair"]
    order = np.argsort(key_rec)
    key_it = it["s"].astype(np.int64) * 10_000_000 + it["pair"]
    pos = np.searchsorted(key_rec[order], key_it)
    ri = order[pos]
    assert np.array_equal(key_rec[ri], key_it) and np.array_equal(rc["h"][ri], it["h"]), "item-record linkage failed"
    # A at (row, h) of every record, from the Q = 0 files; S from the record (= the cache's tr_pred, checked in the substitution pass)
    A_rec = np.full((len(rc["s"]), 3), np.nan)
    for si, sc in enumerate(names):
        m = rc["s"] == si
        if not m.any():
            continue
        Aq = np.load(os.path.join(qdir, sc + ".npz"))["pred_cov"]
        A_rec[m] = Aq[rc["row"][m], rc["h"][m]]
    assert np.all(np.isfinite(A_rec)), "A missing for a record"
    S_rec = np.stack([rc["sxx"], rc["sxy"], rc["syy"]], -1)
    yaw_i, a_i = rc["yaw"][ri], it["a"]
    sd1 = project(S_rec[ri], yaw_i, a_i)
    sd_check = float(np.max(np.abs(sd1 - it["sd"])))
    assert sd_check <= 1e-12, "sd(1) differs from the item's sd of record: %g" % sd_check
    rel = it["ref_relied"]
    fold_i = np.array([fold_of[n] for n in names])[it["s"]]
    U = {}
    for q in GRID:
        sdq = sd1 if q == 1.0 else project(subst_cov(A_rec[ri], S_rec[ri], q), yaw_i, a_i)
        U[q] = it["D"] / sdq > Z95
    table, curve, flags = {}, {}, []
    for f in range(int(folds["k"])):
        table[str(f)], curve[str(f)] = {}, {}
        for g in range(4):
            m = rel & (fold_i != f) & (it["g"] == g)
            n = int(m.sum())
            shares = {str(q): (float(U[q][m].mean()) if n else None) for q in GRID}
            ok = [q for q in GRID if n and U[q][m].mean() <= DELTA]
            q_sel = ok[0] if ok else GRID[-1]
            if not ok:
                flags.append({"fold": f, "group": GROUPS[g], "reason": "no grid point qualifies" if n else "no training items", "items": n})
            table[str(f)][str(g)] = q_sel
            curve[str(f)][str(g)] = {"items": n, "logs": int(len(np.unique(it["s"][m]))), "exceedance_share_by_q": shares}
    # float32 question: the files are float64, so no rounding enters; the record of the exceedance check is kept for reference
    out = {"stamp": C.STAMP, "tracker": trk, "grid": GRID, "z": Z95, "delta": DELTA, "groups": GROUPS,
           "rule": "smallest q in the grid with share(D / sd(q) > z_0.95) <= 0.05 on the training folds' relied items of group g "
                   "(steps 0.5 ... 2 s pooled); none: q = 32, flagged",
           "q_table": table, "training_curve": curve, "flags": flags, "items": C.ITEMS_REC[trk],
           "items_sha256": C.sha256_path(C.ITEMS_REC[trk]), "folds_sha256": C.sha256_path(C.FOLDS),
           "qzero_manifest_sha256": C.sha256_path(os.path.join(qdir, "MANIFEST.json")),
           "checks": {"sd1_vs_item_sd_max_abs": sd_check, "relied_items": int(rel.sum())}}
    # substitution files
    sdir = os.path.join(C.E2, "subst_%s" % trk)
    os.makedirs(sdir, exist_ok=True)
    cman = json.load(open(os.path.join(C.CACHE[trk], "MANIFEST.json")))
    man = {"stamp": C.STAMP, "tracker": trk, "q_table": table, "fold_of_scene": fold_of, "folds_sha256": out["folds_sha256"],
           "cache": C.CACHE[trk], "cache_manifest_sha256": C.sha256_path(os.path.join(C.CACHE[trk], "MANIFEST.json")),
           "dtype": "float64", "scenes": {}}
    rec_vs_cache = 0.0
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
        cov = subst_cov(A, Smat, np.broadcast_to(q_row[:, None], (len(q_row), 8)).copy())
        si = names.index(sc)
        m = rc["s"] == si
        if m.any():
            rec_vs_cache = max(rec_vs_cache, float(np.max(np.abs(Smat[rc["row"][m], rc["h"][m]] - S_rec[m]))))
        if os.path.exists(p_out):                                  # resume: an existing file must hold exactly this content
            zo = np.load(p_out)
            assert np.array_equal(zo["pred_cov"], cov) and np.array_equal(zo["q_row"], q_row), "existing substitution file differs: " + sc
        else:
            C.save_npz(p_out, pred_cov=cov, tr_k=zc["tr_k"] if len(trp) else np.zeros(0, np.int64), q_row=q_row,
                       g_row=np.asarray(g_row, np.int32), fold=np.array(f), stamp=np.array(C.STAMP),
                       what=np.array("A + q (S - A) per tr row (q from the fold x class-group table); replaces tr_pred[:, :, 2:5]"))
        man["scenes"][sc] = {"rows": int(len(trp)), "fold": f, "sha256": C.sha256_path(p_out),
                             "rows_by_q": {str(q): int((q_row == q).sum()) for q in GRID if (q_row == q).any()}}
        if (i + 1) % 25 == 0:
            C.live("qfit substitution %s" % trk, i + 1, 375)
    assert rec_vs_cache == 0.0, "record covariance differs from the cache's tr_pred: %g" % rec_vs_cache
    out["checks"]["record_S_vs_cache_tr_pred_max_abs"] = rec_vs_cache
    man["code_sha256"] = C.code_record([os.path.abspath(__file__), C.__file__, S.__file__])
    out["code_sha256"] = man["code_sha256"]
    C.save_json(os.path.join(sdir, "MANIFEST.json"), man)
    out["subst_manifest"] = os.path.join(sdir, "MANIFEST.json")
    out["subst_manifest_sha256"] = C.sha256_path(out["subst_manifest"])
    out["seconds"] = round(time.time() - t0, 1)
    C.save_json(os.path.join(C.E2, "qfit_table_%s.json" % trk), out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", nargs="+", required=True, choices=("t1", "t3"))
    a = ap.parse_args(argv)
    C.run_log_ok()
    folds = json.load(open(C.FOLDS))
    from x3_heavylock_v01 import heavy_lock
    for trk in a.trk:
        with heavy_lock("x3-ref: Q-refit fit and substitution %s" % trk):
            out = run_tracker(trk, folds)
        print(trk, json.dumps(out["q_table"]), json.dumps(out["flags"]), json.dumps(out["checks"]))
    C.run_log_ok()
    print("X3 REF QFIT DONE")


if __name__ == "__main__":
    main()
