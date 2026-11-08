#!/usr/bin/env python3
"""Diagnosis of the T3 refit mismatch of k8_joint_fit_v01 (fold 4, h2s) (Claude line, 2 Nov 2026). Read-only, one process.
For the merged items (K8 v02 expl + dev, as the full fit loads them) and for M*'s own K7 v01 items: refit M*'s fold-4 h2s thresholds
with k7_fit_v01.split_fit, list the entries that differ from k7_fits_t3_v01.json, and for each differing CRC cell evaluate the CRC
bound n/(n+1) mean_s L_s + 1/(n+1) at the two candidate thresholds in EXACT rational arithmetic and in floating point under the two
scene orders (K7 v01's scene index order and the merged items' sorted-name order).
Usage: python -B tests/k8_joint_t3_refit_diag_v01.py --out <json>
"""
import argparse
import json
import os
import sys
from fractions import Fraction

import numpy as np

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(K8))
sys.path.insert(0, K8)
import k8_joint_fit_v01 as J  # noqa: E402
import k7_fit_v01 as K7F  # noqa: E402

M = J.M
FOLD, H = 4, 3


def cell_members(it, lv, sel, level, cid, part):
    m = sel & (lv[level] == cid) & (it["inpath"].astype(int) == part)
    return m


def bound_float(U, s, c, delta=0.05):
    scenes = np.unique(s)
    n = len(scenes)
    idx = {sc: i for i, sc in enumerate(scenes)}
    si = np.array([idx[x] for x in s])
    tot = np.bincount(si, minlength=n).astype(float)
    L = np.bincount(si, weights=(U > c).astype(float), minlength=n) / tot
    b = n / (n + 1) * L.mean() + 1 / (n + 1)
    return float(b), bool(b <= delta), float(L.mean())


def bound_exact(U, s, c):
    scenes, si = np.unique(s, return_inverse=True)
    n = len(scenes)
    tot = np.bincount(si, minlength=n)
    x = np.bincount(si, weights=(U > c).astype(float), minlength=n).astype(int)
    mean = sum(Fraction(int(a), int(b)) for a, b in zip(x, tot)) / n
    b = Fraction(n, n + 1) * mean + Fraction(1, n + 1)
    return b, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    fits = json.load(open(os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_t3_v01.json")))
    F = fits["fits"][str(FOLD)][J.STEPS[H]]
    thr_k7, src_k7 = np.asarray(F["Mstar_ip"], float), np.asarray(F["Mstar_ip_src"], int)
    out = {"fold": FOLD, "step": J.STEPS[H]}
    # (1) the merged items, exactly as the full fit loads them
    it, names, info = J.load_items([os.path.join(W, "70_TESTS", "k8_expl_v02", "items_k8_v02_expl_t3.npz"),
                                    os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_t3.npz")])
    out["k7_items_check"] = J.check_against_k7_items(it, names, os.path.join(W, "30_DATA", "k7", "k7_items_t3_v01.npz"), fits)
    fold_of_scene = np.array([fits["fold_of_scene"][n] for n in names], int)
    lv = M.levels(it, it["m"])
    U = it["D"] / it["sd"]
    thr_m, src_m = J.refit_split(it, lv, U, fold_of_scene != FOLD, J.N_MIN)
    thr_m, src_m = thr_m[H], src_m[H]
    diff = np.flatnonzero((thr_m != thr_k7) | (src_m != src_k7))
    # (2) M*'s own K7 v01 items, in their own scene index order (exactly k7_fit_v01's input)
    z = np.load(os.path.join(W, "30_DATA", "k7", "k7_items_t3_v01.npz"))
    n1 = [str(x) for x in z["scene_names"]]
    it1 = {k[5:]: z[k] for k in z.files if k.startswith("item_")}
    fold1 = np.array([fits["fold_of_scene"][n] for n in n1], int)
    lv1 = M.levels(it1, it1["m"])
    U1 = it1["D"] / it1["sd"]
    sel1 = (it1["h"] == H) & (fold1[it1["s"]] != FOLD)
    t1_, s1_ = K7F.split_fit(U1[sel1], it1["s"][sel1], [x[sel1] for x in lv1], it1["inpath"][sel1].astype(int), 0)
    out["k7_v01_items_own_order_reproduces_k7_fits"] = bool(np.array_equal(t1_, thr_k7) and np.array_equal(s1_, src_k7))
    # the same K7 v01 items with the scene labels renumbered in sorted-name order (the merged items' order)
    rank = {n: i for i, n in enumerate(sorted(n1))}
    relab = np.array([rank[n] for n in n1])[it1["s"]]
    t2_, s2_ = K7F.split_fit(U1[sel1], relab[sel1], [x[sel1] for x in lv1], it1["inpath"][sel1].astype(int), 0)
    out["k7_v01_items_sorted_name_order_equals_merged_refit"] = bool(np.array_equal(t2_, thr_m) and np.array_equal(s2_, src_m))
    out["k7_v01_items_sorted_name_order_reproduces_k7_fits"] = bool(np.array_equal(t2_, thr_k7) and np.array_equal(s2_, src_k7))
    rows = []
    sel_m = (it["h"] == H) & (fold_of_scene[it["s"]] != FOLD)
    for e in diff.tolist():
        part, l0 = divmod(e, J.N_L0)
        level = int(src_k7[e])
        keys = (l0,) + M.parents(l0)
        cid = keys[level]
        r = {"entry": e, "l0": l0, "l0_name": M.l0_name(l0), "inpath": part, "src_k7": int(src_k7[e]), "src_refit": int(src_m[e]),
             "thr_k7": float(thr_k7[e]), "thr_refit": float(thr_m[e]), "level": level, "cell_id": int(cid)}
        if src_k7[e] == src_m[e]:
            mm = cell_members(it, lv, sel_m, level, cid, part)
            Uc, sc = U[mm], it["s"][mm]
            m1 = sel1 & (lv1[level] == cid) & (it1["inpath"].astype(int) == part)
            Uc1, sc1 = U1[m1], it1["s"][m1]
            r["cell_items"], r["cell_scenes"] = int(mm.sum()), int(len(np.unique(sc)))
            for tag, c in (("at_thr_k7", thr_k7[e]), ("at_thr_refit", thr_m[e])):
                be, n = bound_exact(Uc, sc, c)
                bm, okm, _ = bound_float(Uc, sc, c)
                bk, okk, _ = bound_float(Uc1, sc1, c)
                r[tag] = {"bound_exact": "%d/%d" % (be.numerator, be.denominator), "bound_exact_minus_delta": float(be - Fraction(1, 20)),
                          "exact_le_delta": bool(be <= Fraction(1, 20)), "n_scenes": n,
                          "float_bound_merged_order": repr(bm), "float_ok_merged_order": okm,
                          "float_bound_k7_order": repr(bk), "float_ok_k7_order": okk}
            r["unique_U_between"] = int(np.sum((np.unique(Uc) > min(thr_k7[e], thr_m[e])) & (np.unique(Uc) < max(thr_k7[e], thr_m[e]))))
        rows.append(r)
    out["differing_entries"] = rows
    out["n_differing"] = len(rows)
    json.dump(out, open(a.out, "w"), indent=1, default=str)
    print(json.dumps(out, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
