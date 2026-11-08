#!/usr/bin/env python3
"""Tests for the TPP arm join keys (v01, 2 Nov 2026). Run in canmot310 with `python -I` on a keys file built for a few
validation scenes (tiny input). Checks only keys and geometry; no Trajectron++ output is read.
  K1 join coverage: the keys file's records and items equal, field by field and in order, what
     k8_items_v02.scene_items returns for the same cache files (called afresh here), so (scene name, pair) and
     (scene name, pair, axis) join 1:1 to the K8 records and items; items map to records and every record axis with
     gap > 0 is an item.
  K2 histories: tracker and ground-truth contiguous history lengths equal a brute-force recount from the cache.
  K3 geometry: the stored toward-ego sign reproduces the K8 record's signed errors (rebuilt here from the cache, not
     stored in the keys file) and gaps; the reference ego centre lies R2C ahead of the logged rear axle.
  K4 the keys npz loads with allow_pickle=False and carries no tracker-arm error field (dx, dy, D, sd).
Usage: python -I test_tpp_keys_v01.py --keys <keys npz> --out <json>
"""
import argparse
import json
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tpp_keys_v01 as TK  # noqa: E402

K8I, S, C = TK.K8I, TK.S, TK.C
RES = {}


def check(name, cond, info=None):
    RES[name] = {"pass": bool(cond), "info": info}
    print(("PASS " if cond else "FAIL ") + name + ("  " + json.dumps(info, default=float) if info is not None else ""), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    kz = np.load(a.keys, allow_pickle=False)
    names = [str(s) for s in kz["scene_names"]]
    cache = str(kz["cache_dir"])
    good1, good2, good3 = True, True, True
    info1, d_err, g_err, c_err = {}, 0.0, 0.0, 0.0
    for si, scene in enumerate(names):
        p = os.path.join(cache, scene + ".npz")
        _, it, rc, st = K8I.scene_items((p, si))
        sel = np.nonzero(kz["rec_s"] == si)[0]
        isel = np.nonzero(kz["item_s"] == si)[0]
        g = len(sel) == len(rc["k"]) and len(isel) == len(it["k"])
        for f in ("k", "h", "g", "r", "row", "inst", "pair", "m", "l0_long", "l0_lat", "rel", "inpath", "yaw", "gap_long", "gap_lat"):
            g &= np.array_equal(np.asarray(kz["rec_" + f][sel]).astype(float), np.asarray(rc[f]).astype(float))
        for f in ("k", "h", "g", "r", "a", "m", "l0", "inpath", "pair", "ref_relied"):
            g &= np.array_equal(np.asarray(kz["item_" + f][isel]).astype(float), np.asarray(it[f]).astype(float))
        g &= np.array_equal(kz["rec_pair"][kz["item_rec"][isel]], kz["item_pair"][isel]) and np.all(kz["rec_s"][kz["item_rec"][isel]] == si)
        nax = int(np.sum(kz["rec_gap_long"][sel] > 0) + np.sum(kz["rec_gap_lat"][sel] > 0))
        g &= nax == len(isel)
        good1 &= bool(g)
        info1[scene] = {"records": int(len(sel)), "items": int(len(isel)), "match": bool(g)}
        # K2 brute force histories
        sc = S.Scene(p)
        tr, gt = sc.tr, sc.gt
        trk_present = {(int(t), int(k_)) for t, k_ in zip(tr["tid"], tr["k"])}
        gt_present = {(int(i), int(k_)) for i, k_ in zip(gt["inst"], gt["k"])}
        for j in sel:
            k, tid, inst = int(kz["rec_k"][j]), int(kz["rec_tid"][j]), int(kz["rec_inst"][j])
            n = 0
            while (tid, k - n) in trk_present:
                n += 1
            m = 0
            while (inst, k - m) in gt_present:
                m += 1
            good2 &= n == kz["rec_hist_trk"][j] and m == kz["rec_hist_gt"][j]
        # K3 geometry against the K8 record fields recomputed here
        for jj, j in enumerate(sel):
            row, h = int(kz["rec_row"][j]), int(kz["rec_h"][j])
            yaw = float(kz["rec_yaw"][j])
            ax = np.array([[math.cos(yaw), math.sin(yaw)], [-math.sin(yaw), math.cos(yaw)]])
            e = np.array([rc["dx"][jj], rc["dy"][jj]])
            D = np.array([kz["rec_sign_long"][j], kz["rec_sign_lat"][j]]) * (ax @ e)
            d_err = max(d_err, float(np.max(np.abs(D - np.array([rc["D_long"][jj], rc["D_lat"][jj]])))))
            gr = int(kz["rec_gt_row"][j])
            e2 = np.array([gt["x"][gr], gt["y"][gr]]) - tr["pred"][row, h, :2]
            g_err = max(g_err, float(np.max(np.abs(e2 - e))))
            tk = float(sc.kf_t[int(kz["rec_k"][j])])
            ex, ey, eyaw = (float(q) for q in sc.pose(np.array(sc.s_log(tk + 0.5 * (h + 1)))))
            c_err = max(c_err, abs(kz["rec_cref_x"][j] - ex - S.R2C * math.cos(eyaw)), abs(kz["rec_cref_y"][j] - ey - S.R2C * math.sin(eyaw)))
    check("K1_join_coverage_vs_k8_items_v02", good1, info1)
    check("K2_history_lengths", bool(good2), {"records": int(len(kz["rec_k"]))})
    good3 = d_err < 1e-9 and g_err < 1e-9 and c_err < 1e-9
    check("K3_sign_gt_row_reference_pose", good3, {"D_err": d_err, "gt_row_err": g_err, "cref_err": c_err})
    banned = [f for f in kz.files if any(f == "rec_" + b or f == "item_" + b for b in ("dx", "dy", "D", "D_long", "D_lat", "sd", "sd_long", "sd_lat"))]
    check("K4_npz_no_pickle_no_errors", len(banned) == 0, {"fields": len(kz.files), "banned_present": banned})
    out = {"tests": RES, "all_pass": all(v["pass"] for v in RES.values()), "keys": os.path.abspath(a.keys),
           "scripts": {"tpp_keys_v01": C.sha256_path(TK.__file__), "test_tpp_keys_v01": C.sha256_path(os.path.abspath(__file__)),
                       "k8_items_v02": C.sha256_path(K8I.__file__)}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print("ALL_PASS" if out["all_pass"] else "SOME_FAIL")


if __name__ == "__main__":
    main()
