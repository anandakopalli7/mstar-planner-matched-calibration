#!/usr/bin/env python3
"""K7 cross-fitted arm fits (Claude line, v01, 1 Nov 2026): planner-matched calibration.

Input: the K7 items of one tracker (k7_items_v01: the planner's enforced pairs at the decision states of all 850 trainval
scenes) and the K6 fit file of the same tracker, whose 5 log folds (seed 20261101) are reused unchanged. For every fold f
and calibrated step h = 0.5, 1, 1.5, 2 s, every arm is fitted on the items of the other four folds:
  M7 ('Mstar', with 'Mstar_ip'): DP-SCRC (m_lib_v04.fit_hier: the CRC threshold of U = D/sd in the item's own L0 stratum
       when it has >= 19 calibration scenes, else the next coarser level L1, L2, L3), fitted SEPARATELY on the in-path and
       the not-in-path items; 'Mstar_ip'[L0 + 96 x in-path] holds the two fits. 'Mstar' (96) is the pooled fit, reported
       only (the K7 simulator uses '_ip' whenever present);
  B6 ('B6', 'B6_ip'): the same without motion strata (fit_hier from L1), also split by in-path (the motion ablation of M7);
  B4: one pooled CRC threshold over all items; B3: the largest M7 threshold (constant c);
  B1: NEES-guided k per group x range (>= 19 scenes, else the global k) on the records; B9: the norm-ball CRC radius on the
      records.
Steps 2.5-4 s are not enforced by the planner (constraints are enforced to 2 s) and keep the K6 fits unchanged.
The CRC, the hierarchy, n_min = 19, sigma_a = 0.10 and the strata are the method stage's, unchanged.
Usage: python -B k7_fit_v01.py --items <npz> --k6fits <json> --out <json>
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
import m_lib_v04 as M  # noqa: E402

L = M.L
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
N_MIN = M.N_CRC
N_L0 = M.N_L0


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def split_fit(U, s, lv, ip, start):
    """fit_hier separately on the not-in-path (ip = 0) and in-path (ip = 1) items; returns 192 thresholds and sources."""
    out, src = np.full(2 * N_L0, np.nan), np.full(2 * N_L0, -1)
    for part in (0, 1):
        sel = ip == part
        thr, so = M.fit_hier(U[sel], s[sel], [x[sel] for x in lv], start, N_MIN)
        out[part * N_L0:(part + 1) * N_L0], src[part * N_L0:(part + 1) * N_L0] = thr, so
    return out, src


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--k6fits", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    z = np.load(a.items)
    k6 = json.load(open(a.k6fits))
    names = [str(x) for x in z["scene_names"]]
    assert sorted(names) == sorted(k6["scenes"]), "the K7 items and the K6 folds cover different scenes"
    fold = np.array([k6["fold_of_scene"][n] for n in names], int)
    it = {k[5:]: z[k] for k in z.files if k.startswith("item_")}
    rc = {k[4:]: z[k] for k in z.files if k.startswith("rec_")}
    m = it["m"]
    lv = M.levels(it, m)
    assert np.array_equal(lv[0], it["l0"]), "L0 from the items differs from the simulator's L0"
    U = it["D"] / it["sd"]
    ip = it["inpath"].astype(int)
    sa = M.SIGMA_A
    S11, S12, S22 = rc["sxx"] + sa ** 2, rc["sxy"], rc["syy"] + sa ** 2
    nees = (S22 * rc["dx"] ** 2 - 2 * S12 * rc["dx"] * rc["dy"] + S11 * rc["dy"] ** 2) / (S11 * S22 - S12 ** 2)
    nrm = np.hypot(rc["dx"], rc["dy"])
    out = {"k7": True, "tags": k6["tags"], "seed": k6["seed"], "scenes": k6["scenes"], "fold_of_scene": k6["fold_of_scene"],
           "fold_scene_counts": k6["fold_scene_counts"], "items_sha256": sha256_path(a.items), "k6fits_sha256": sha256_path(a.k6fits),
           "fits": {str(f): {} for f in range(M.K_FOLDS)}, "items_per_step": {}, "src_share": {}}
    for f in range(M.K_FOLDS):
        for h, step in enumerate(STEPS):
            if h >= 4:
                out["fits"][str(f)][step] = k6["fits"][str(f)][step]
                continue
            sel = (it["h"] == h) & (fold[it["s"]] != f)
            Us, ss, lvs, ips = U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel]
            mip, mip_src = split_fit(Us, ss, lvs, ips, 0)
            b6ip, _ = split_fit(Us, ss, lvs, ips, 1)
            mpool, _ = M.fit_hier(Us, ss, lvs, 0, N_MIN)
            b6pool, _ = M.fit_hier(Us, ss, lvs, 1, N_MIN)
            for arr, nm in ((mip, "Mstar_ip"), (b6ip, "B6_ip"), (mpool, "Mstar"), (b6pool, "B6")):
                assert np.all(np.isfinite(arr)), "non-finite threshold: " + nm
            rsel = (rc["h"] == h) & (fold[rc["s"]] != f)
            ne, rs, rg, rr = nees[rsel], rc["s"][rsel], rc["g"][rsel], rc["r"][rsel]
            kg = float(np.mean(ne)) / 2.0
            b1k = {"global": kg}
            kk = np.full(12, kg)
            for g in range(4):
                for r in range(3):
                    gs = (rg == g) & (rr == r)
                    if gs.any() and len(np.unique(rs[gs])) >= N_MIN:
                        kk[g * 3 + r] = float(np.mean(ne[gs])) / 2.0
                        b1k["%s|%s" % (M.GROUPS[g], M.RANGES[r])] = kk[g * 3 + r]
            out["fits"][str(f)][step] = {"Mstar": mpool.tolist(), "Mstar_ip": mip.tolist(), "Mstar_ip_src": mip_src.tolist(),
                                         "B6": b6pool.tolist(), "B6_ip": b6ip.tolist(),
                                         "B4": float(L.crc_threshold(Us, ss)), "B3": float(np.nanmax(mip)),
                                         "B9": float(L.crc_threshold(nrm[rsel], rs)), "B1": kk.tolist(), "B1_k": b1k}
            if f == 0:
                out["items_per_step"][step] = int((it["h"] == h).sum())
            out["src_share"]["%d_%s" % (f, step)] = {str(lvl): float(np.mean(mip_src == lvl)) for lvl in range(4)}
        print("fold", f, "%.0f s" % (time.time() - t0), flush=True)
    json.dump(out, open(a.out, "w"), indent=1)
    print("K7 FIT DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
