#!/usr/bin/env python3
"""C1 fits (Claude line, c1_fit_v01, 2 Nov 2026): every fitted K8 arm on K8-layout items, per C1 fold (within) or once (transfer).
C1 v04 sections 3, 4 and 11.3; D16 v08 Choices 6, 7, 21, 22; ERRATA_K8_v02 E15.

Arms (k7_fit_v01's definitions, unchanged except that every CRC accept/reject is exact, c1_crc_exact_v01):
  M* ('Mstar_ip', 192 = L0 + 96 x in-path; 'Mstar' pooled 96, reported): DP-SCRC per L0 stratum with >= 19 calibration units, else
     L1, L2, L3; fitted separately on not-in-path and in-path items;  B6 ('B6_ip', 'B6'): the same from L1 (no motion strata);
  B4: one pooled CRC threshold;  B3: the largest M* threshold;  B9: the norm-ball CRC radius on the records;  B1: NEES-guided k per
     group x range (>= 19 units, else the global k), on the records;
  M*Jx (H3, Choice 21): for test fold f and g = (f + 1) mod k, the base by M*'s rule on the folds other than f and g, lambda by the
     exact joint CRC on fold g (k8_joint_fit_v02.fit_lambda: max over PD7, SD1_7, PD; grid 1.00..100.00), applied to fold f;
  M*J (descriptive): M*'s fold-f base, lambda on M*'s calibration folds.
Steps: the 4 calibrated steps (0.5 to 2 s) are fitted. The planner enforces constraints to 2 s only; the 2.5 to 4 s step dicts are
copies of the 2 s dict (key '_copied_from'), which no decision or endpoint reads (test C3 checks it on a development scene).
Units: one unit = one scene of the items (= one log on AV2). Calibration for fold f = the units of the other folds.
Routes:
  within    (primary, Choice 6): per fold of --folds (c1_folds_v01 JSON); the output maps every unit to its fold;
  transfer  (Choice 7): one fit on all units of the items (the 850 nuScenes scenes), written as fold '0'; every unit of --apply-folds
            maps to it. M*Jx's base uses the folds of --folds other than 0 and 1 and its lambda fold 1; M*J uses all units
            (both descriptive in the transfer route). --retuned-arm records RETUNED's transfer point (chosen on nuScenes).
Usage: python -B c1_fit_v01.py --items <npz> [<npz> ...] --folds <folds json> --out <fits json> [--route within|transfer
       --apply-folds <AV2 folds json> --retuned-arm <arm>] [--units-subset]   (--units-subset: items may cover more units than the folds)
"""
import argparse
import hashlib
import json
import os
import sys
import time

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
import c1_crc_exact_v01 as X  # noqa: E402
import k8_joint_fit_v02 as J  # noqa: E402

M = X.M
STEPS = J.STEPS
CC = J.CC_STEPS
N_L0 = M.N_L0
DELTA = 0.05
N_MIN = M.N_CRC
REC = ("s", "h", "g", "r", "dx", "dy", "sxx", "sxy", "syy")
STAMP = "C1: fits for the AV2 confirmation (within-AV2 cross-fitting or nuScenes transfer); exact CRC decisions (E15)"


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def load_records(paths, names):
    """rec_* arrays of the item files, with the scene index remapped to names (the order of J.load_items)."""
    gidx = {n: i for i, n in enumerate(names)}
    parts = {f: [] for f in REC}
    for p in paths:
        z = np.load(p)
        remap = np.array([gidx[str(x)] for x in z["scene_names"]], np.int64)
        for f in REC:
            parts[f].append(remap[z["rec_s"]] if f == "s" else z["rec_" + f])
    return {f: np.concatenate(v) for f, v in parts.items()}


def fit_arms(it, lv, U, rc, nees, nrm, unit_mask):
    """Every per-constraint arm on the units in unit_mask, for the 4 calibrated steps (k7_fit_v01's rules, exact CRC)."""
    out = {}
    ip = it["inpath"].astype(int)
    for h in range(CC):
        sel = (it["h"] == h) & unit_mask[it["s"]]
        Us, ss, lvs, ips = U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel]
        mip, mip_src = X.split_fit_exact(Us, ss, lvs, ips, 0)
        b6ip, _ = X.split_fit_exact(Us, ss, lvs, ips, 1)
        mpool, _ = X.fit_hier_exact(Us, ss, lvs, 0)
        b6pool, _ = X.fit_hier_exact(Us, ss, lvs, 1)
        for arr, nm in ((mip, "Mstar_ip"), (b6ip, "B6_ip"), (mpool, "Mstar"), (b6pool, "B6")):
            assert np.all(np.isfinite(arr)), "non-finite threshold: " + nm
        assert np.all(mip > 0), "an M* threshold <= 0: the joint arms' monotonicity needs c > 0"
        rsel = (rc["h"] == h) & unit_mask[rc["s"]]
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
        out[STEPS[h]] = {"Mstar": mpool.tolist(), "Mstar_ip": mip.tolist(), "Mstar_ip_src": mip_src.astype(int).tolist(),
                         "B6": b6pool.tolist(), "B6_ip": b6ip.tolist(), "B4": float(X.crc_threshold_exact(Us, ss)),
                         "B3": float(np.nanmax(mip)), "B9": float(X.crc_threshold_exact(nrm[rsel], rs)), "B1": kk.tolist(), "B1_k": b1k}
    return out


def base_of(fd):
    return np.array([fd[STEPS[h]]["Mstar_ip"] for h in range(CC)], float)


def joint_entries(fd, lam, thr_x, lam_x, src_x):
    for h in range(CC):
        fd[STEPS[h]]["MstarJ_ip"] = (lam * np.asarray(fd[STEPS[h]]["Mstar_ip"], float)).tolist()
        fd[STEPS[h]]["MstarJ_lambda"] = lam
        fd[STEPS[h]]["MstarJx_ip"] = (lam_x * thr_x[h]).tolist()
        fd[STEPS[h]]["MstarJx_ip_src"] = src_x[h].astype(int).tolist()
        fd[STEPS[h]]["MstarJx_lambda"] = lam_x


def lam_or_max(it, mask, base, grid):
    lam, by_pop, binding = J.fit_lambda(it, mask, base, DELTA, grid)
    none_q = lam is None
    return (float(grid[-1]) if none_q else lam), {"lambda": float(grid[-1]) if none_q else lam, "none_qualifies_grid_max_used": none_q,
                                                   "binding_populations": binding, "by_population": by_pop}


def refit_base(it, lv, U, mask):
    thr, src = np.full((CC, 2 * N_L0), np.nan), np.full((CC, 2 * N_L0), -1)
    ip = it["inpath"].astype(int)
    for h in range(CC):
        sel = (it["h"] == h) & mask[it["s"]]
        thr[h], src[h] = X.split_fit_exact(U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel], 0)
    assert np.all(np.isfinite(thr)) and np.all(thr > 0), "M*Jx base: every threshold finite and > 0"
    return thr, src


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", nargs="+", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--route", choices=["within", "transfer"], default="within")
    ap.add_argument("--apply-folds", default=None, help="transfer: the AV2 folds JSON whose units the transfer fit is applied to")
    ap.add_argument("--retuned-arm", default=None, help="transfer: RETUNED's point chosen on nuScenes (recorded)")
    ap.add_argument("--units-subset", action="store_true", help="the items may cover more units than the folds (stand-in)")
    a = ap.parse_args(argv)
    t0 = time.time()
    fj = json.load(open(a.folds))
    fold_of = {u: int(f) for u, f in fj["fold_of_log"].items()}
    k = int(fj["k"])
    it, names, info = J.load_items(a.items)
    if a.units_subset:
        keep_names = [n for n in names if n in fold_of]
        assert set(keep_names) == set(fold_of), "the items do not cover every unit of the folds"
        keep = np.isin(names, keep_names)
        sel = keep[it["s"]]
        it = {f: v[sel] for f, v in it.items()}            # scene indices still refer to names; units outside the folds are dropped
        unit_ok = keep
    else:
        assert set(names) == set(fold_of), "the items' units differ from the folds' units"
        unit_ok = np.ones(len(names), bool)
    rc = load_records(a.items, list(names))
    rc = {f: v[unit_ok[rc["s"]]] for f, v in rc.items()}
    fold_unit = np.array([fold_of.get(n, -1) for n in names], int)
    lv = M.levels(it, it["m"])
    assert np.array_equal(lv[0], it["l0"]), "L0 from the items differs from the simulator's L0"
    U = it["D"] / it["sd"]
    sa = M.SIGMA_A
    S11, S12, S22 = rc["sxx"] + sa ** 2, rc["sxy"], rc["syy"] + sa ** 2
    nees = (S22 * rc["dx"] ** 2 - 2 * S12 * rc["dx"] * rc["dy"] + S11 * rc["dy"] ** 2) / (S11 * S22 - S12 ** 2)
    nrm = np.hypot(rc["dx"], rc["dy"])
    grid = J.GRID
    out = {"c1": True, "stamp": STAMP, "route": a.route, "folds": os.path.abspath(a.folds), "folds_sha256": sha256_path(a.folds),
           "k": k, "seed": fj.get("seed"), "items": info, "exact_crc": "c1_crc_exact_v01 (E15)", "fits": {}, "joint": {"fit": {"folds": {}}},
           "code_sha256": {"c1_fit_v01": sha256_path(os.path.abspath(__file__)), "c1_crc_exact_v01": sha256_path(X.__file__),
                           "k8_joint_fit_v02": sha256_path(J.__file__), "m_lib_v04": sha256_path(M.__file__)}}
    if a.route == "within":
        out["scenes"] = sorted(fold_of)
        out["fold_of_scene"] = fold_of
        out["fold_scene_counts"] = [int((fold_unit == f).sum()) for f in range(k)]
        for f in range(k):
            t1 = time.time()
            cal = unit_ok & (fold_unit != f) & (fold_unit >= 0)
            fd = fit_arms(it, lv, U, rc, nees, nrm, cal)
            lam, mj = lam_or_max(it, cal, base_of(fd), grid)
            g = (f + 1) % k
            thr_x, src_x = refit_base(it, lv, U, unit_ok & (fold_unit != f) & (fold_unit != g) & (fold_unit >= 0))
            lam_x, mjx = lam_or_max(it, unit_ok & (fold_unit == g), thr_x, grid)
            mjx.update({"lambda_fold": g, "base_folds": [x for x in range(k) if x not in (f, g)],
                        "items_oof": J.joint_loss_at(it, unit_ok & (fold_unit == f), thr_x, lam_x)})
            mj["items_oof"] = J.joint_loss_at(it, unit_ok & (fold_unit == f), base_of(fd), lam)
            joint_entries(fd, lam, thr_x, lam_x, src_x)
            for h in range(CC, len(STEPS)):
                fd[STEPS[h]] = dict(fd[STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
            out["fits"][str(f)] = fd
            out["joint"]["fit"]["folds"][str(f)] = {"MstarJ": mj, "MstarJx": mjx}
            print("fold %d: MstarJ %.2f MstarJx %.2f  %.0f s" % (f, lam, lam_x, time.time() - t1), flush=True)
    else:
        assert a.apply_folds, "--route transfer needs --apply-folds (the AV2 folds the fit is applied to)"
        af = json.load(open(a.apply_folds))
        out["folds_sha256"] = sha256_path(a.apply_folds)
        out["transfer_source_folds_sha256"] = sha256_path(a.folds)
        out["transfer_source_units"] = sorted(fold_of)
        out["scenes"] = sorted(af["fold_of_log"])
        out["fold_of_scene"] = {u: 0 for u in af["fold_of_log"]}
        out["fold_scene_counts"] = [len(af["fold_of_log"])]
        allu = unit_ok & (fold_unit >= 0)
        fd = fit_arms(it, lv, U, rc, nees, nrm, allu)
        lam, mj = lam_or_max(it, allu, base_of(fd), grid)
        thr_x, src_x = refit_base(it, lv, U, allu & (fold_unit != 0) & (fold_unit != 1))
        lam_x, mjx = lam_or_max(it, allu & (fold_unit == 1), thr_x, grid)
        joint_entries(fd, lam, thr_x, lam_x, src_x)
        for h in range(CC, len(STEPS)):
            fd[STEPS[h]] = dict(fd[STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
        out["fits"]["0"] = fd
        out["joint"]["fit"]["folds"]["0"] = {"MstarJ": mj, "MstarJx": mjx}
        out["retuned_transfer_arm"] = a.retuned_arm
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1)
    os.replace(tmp, a.out)
    print(json.dumps({"out": os.path.abspath(a.out), "sha256": sha256_path(a.out), "seconds": out["seconds"]}))
    print("C1 FIT DONE")


if __name__ == "__main__":
    main()
