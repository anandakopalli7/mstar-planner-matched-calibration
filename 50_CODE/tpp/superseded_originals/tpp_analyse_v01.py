#!/usr/bin/env python3
"""TPP arm analysis (Claude line, v01, 2 Nov 2026) PROPOSED for 90_DECISIONS/D17_TPP_ARM_PREREG_v01.md (draft, not frozen).
Run in canmot310. Written and tested on SYNTHETIC data only. On real data it refuses to run unless it is given a freeze
record whose analysis hash equals this file's SHA-256 and whose plan hash equals the plan file's SHA-256 (the lead
writes that record at the freeze); `--synthetic` accepts only inputs stamped synthetic.

What it computes (per tracker; primary horizon h = 3, i.e. 2.0 s; the K8 item populations PD7 = relied items,
SD1_7 = relied items with pair gap <= 5 m, PD = relied in-path items):
  * per item, for each arm, the projected error along the item's own toward-ego normal a* (object axis from the tracker
    yaw, sign at the reference ego pose, both from the keys file): D = a*.(g - mu), sd = sqrt(a*' S a* + sigma_a^2),
    U = D / sd, g the annotated centre at k + h + 1. Arms: TPP (Trajectron++ on tracker histories; V2 primary, V1
    secondary), TPPgt (ground-truth histories, upper bound), TRK (the tracker's own propagated prediction, as K8);
  * methods per arm: B0 (raw, z_0.95 sd), B4 (one pooled scene-level CRC threshold), B3 (certified single multiplier,
    the max of M*'s thresholds) and M* (DP-SCRC: per-L0 scene-level CRC with the count-based fallback chain, n_min = 19),
    each FITTED ON 4 FOLDS AND APPLIED TO THE 5TH: 5 folds of 30 validation scenes from a seeded permutation (Choice 3);
  * the tracker arm's statistics, imported unchanged from 50_CODE/m/m_lib_v04.py: evaluation cells (`make_cells`, kind
    E2: >= 39 scenes and >= 8 logs), scene-level exceedance, log-cluster bootstrap (B = 2000), one-sided simultaneous
    sup-t flags at 0.95, the pooled cell pointwise, the pooled upper bound (HK1c: <= delta + 0.03), margins in metres,
    paired contrasts (`eval_stats` with per-method exceedance indicators);
  * A6-type diagnostics on the relied records (2-D position block): scene-level ANEES, median NEES, coverage of the
    chi-square ellipses at 50/90/95/99 %; the weight summary by history stratum.
Hypotheses and decision rules: D17 sections 2 and 6.
Usage (synthetic): python -I tpp_analyse_v01.py --synthetic --keys <syn keys> --runs trk=<npz> gt=<npz> --out <json>
       (real, after the freeze): ... --keys <keys> --runs trk=<npz> gt=<npz> --plan <D17 file> --freeze-record <json> --out <json>
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(W_ROOT, "50_CODE", "m"))
import tpp_common_v01 as C  # noqa: E402
import m_lib_v04 as M  # noqa: E402

L = M.L
DELTA, Z, SIGMA_A, N_MIN = M.DELTA, M.Z, M.SIGMA_A, M.N_CRC
FOLD_SEED = 20261102
N_FOLDS, FOLD_SIZE = 5, 30
B_BOOT = 2000
BOOT_SEED = 20261103
H_PRIMARY = 3
HK1C_EPS = 0.03
CHI2_2 = {0.5: 1.3862943611198906, 0.9: 4.605170185988091, 0.95: 5.991464547107979, 0.99: 9.210340371976182}   # -2 ln(1-p)
SYN_STAMP = "SYNTHETIC: generated test data, not nuScenes"


def sha(p):
    return C.sha256_path(p)


def scene_folds(scene_names, seed=FOLD_SEED, k=N_FOLDS, size=FOLD_SIZE):
    """Fold index per scene: a seeded permutation of the sorted scene names cut into k blocks of `size`."""
    names = sorted(scene_names)
    assert len(names) == k * size, "Choice 3 folds need %d scenes, got %d" % (k * size, len(names))
    perm = np.random.default_rng(seed).permutation(len(names))
    fold_of_name = {names[p]: i // size for i, p in enumerate(perm)}
    return np.array([fold_of_name[s] for s in scene_names], np.int32)


def load_inputs(keys_path, run_paths, synthetic, cache_dir=None):
    """cache_dir: the val cache on this machine when the keys were built elsewhere (pod); its MANIFEST.json must have
    the SHA-256 recorded in the keys file."""
    kz = np.load(keys_path, allow_pickle=False)
    is_syn = "stamp" in kz.files and str(kz["stamp"]) == SYN_STAMP
    assert is_syn == synthetic, "synthetic mode needs synthetic inputs and real mode real inputs"
    runs = {}
    for src, p in run_paths.items():
        z = np.load(p, allow_pickle=False)
        assert np.array_equal(z["rec_index"], np.arange(len(kz["rec_k"]))), "run %s does not cover the keys records 1:1" % src
        assert np.array_equal(z["rec_pair"], kz["rec_pair"]) and np.array_equal(z["rec_s"], kz["rec_s"])
        if synthetic:
            assert str(z["stamp"]) == SYN_STAMP
        runs[src] = z
    n = len(kz["rec_k"])
    if synthetic:
        gt_xy, trk_mu, trk_cov = kz["syn_gt_xy"], kz["syn_trk_mu"], kz["syn_trk_cov"]
    else:   # read the annotated centre and the tracker's propagated prediction from the cache the keys were built on
        gt_xy, trk_mu, trk_cov = np.zeros((n, 2)), np.zeros((n, 2)), np.zeros((n, 3))
        cache = cache_dir or str(kz["cache_dir"])
        assert sha(os.path.join(cache, "MANIFEST.json")) == json.loads(str(kz["hashes_json"]))["manifest"], "cache manifest differs from the keys'"
        for si, s in enumerate(kz["scene_names"]):
            sel = np.nonzero(kz["rec_s"] == si)[0]
            if not len(sel):
                continue
            z = np.load(os.path.join(cache, str(s) + ".npz"), allow_pickle=False)
            gr, row, h = kz["rec_gt_row"][sel], kz["rec_row"][sel], kz["rec_h"][sel]
            gt_xy[sel] = np.stack([z["gt_x"][gr], z["gt_y"][gr]], -1)
            p = z["tr_pred"][row, h]
            trk_mu[sel], trk_cov[sel] = p[:, :2], p[:, 2:5]
    return kz, runs, gt_xy, trk_mu, trk_cov


def item_table(kz, runs, gt_xy, trk_mu, trk_cov, h_sel=H_PRIMARY, variant="v2"):
    """Relied items at step h_sel with the per-arm errors; returns a dict of arrays (one entry per item)."""
    rec = kz["item_rec"]
    sel = kz["item_ref_relied"] & (kz["item_h"] == h_sel)
    it = {"rec": rec[sel], "a": kz["item_a"][sel].astype(int), "s": kz["item_s"][sel].astype(int), "g": kz["item_g"][sel].astype(int),
          "r": kz["item_r"][sel].astype(int), "m": kz["item_m"][sel].astype(int), "l0": kz["item_l0"][sel].astype(int),
          "inpath": kz["item_inpath"][sel].astype(bool)}
    j = it["rec"]
    yaw = kz["rec_yaw"][j]
    sgn = np.where(it["a"] == 0, kz["rec_sign_long"][j], kz["rec_sign_lat"][j])
    ax = np.where(it["a"][:, None] == 0, np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1))
    astar = sgn[:, None] * ax
    it["gap"] = np.where(it["a"] == 0, kz["rec_gap_long"][j], kz["rec_gap_lat"][j])
    it["hist_stratum"] = kz["rec_hist_stratum_trk"][j]
    g = gt_xy[j]

    def proj(mu, c3):
        D = np.sum(astar * (g - mu), -1)
        V = astar[:, 0] ** 2 * c3[:, 0] + 2 * astar[:, 0] * astar[:, 1] * c3[:, 1] + astar[:, 1] ** 2 * c3[:, 2]
        return D, V

    it["TRK_D"], it["TRK_V"] = proj(trk_mu[j], trk_cov[j])
    it["TRK_ok"] = np.ones(len(j), bool)
    for src, z in runs.items():
        name = "TPP" if src == "trk" else "TPPgt"
        mu, c3 = z[variant + "_mu"][j], z[variant + "_cov"][j]
        ok = z["status"][j] == C.ST_OK
        D, V = proj(np.where(ok[:, None], mu, 0.0), np.where(ok[:, None], c3, 1.0))
        it[name + "_D"], it[name + "_V"], it[name + "_ok"] = D, V, ok
    return it


def mlib_items(it, sel, kz):
    """The m_lib_v04 item layout for the selected items (scene index, axis, strata, logs)."""
    logs = list(kz["scene_logs"])
    ulog = sorted(set(logs))
    out = {"s": it["s"][sel], "a": it["a"][sel], "g": it["g"][sel], "r": it["r"][sel], "D": np.zeros(int(sel.sum())),
           "scene_log_idx": np.array([ulog.index(x) for x in logs]), "n_scenes": len(logs), "n_logs": len(ulog)}
    m = it["m"][sel]
    lv = M.levels(out, m)
    assert np.array_equal(lv[0], it["l0"][sel]), "l0 of the keys differs from m_lib_v04.levels"
    return out, m, lv


def crossfit(U, s, lv, folds_scene):
    """Held-out thresholds per item for M* (DP-SCRC with fallback), B4 (pooled CRC) and B3 (max of M*)."""
    n = len(U)
    thr = {k: np.full(n, np.nan) for k in ("Mstar", "B4", "B3")}
    src = np.full(n, -1)
    fits = []
    for f in range(N_FOLDS):
        cal = folds_scene[s] != f
        te = ~cal
        t_m, t_src = M.fit_hier(U[cal], s[cal], [x[cal] for x in lv], 0, N_MIN)
        b4 = L.crc_threshold(U[cal], s[cal])
        b3 = float(np.nanmax(t_m))
        assert not np.isnan(t_m[lv[0][te]]).any(), "a held-out stratum has no threshold at any level"
        thr["Mstar"][te] = t_m[lv[0][te]]
        thr["B4"][te] = b4
        thr["B3"][te] = b3
        src[te] = t_src[lv[0][te]]
        fits.append({"fold": f, "cal_scenes": int(len(np.unique(s[cal]))), "B4": b4, "B3": b3,
                     "own_threshold_share": float(np.mean(t_src[lv[0][te]] == 0)) if te.any() else None})
    return thr, src, fits


def a6(D2, S3, s, n_scenes):
    """2-D NEES diagnostics with sigma_a added: scene-level ANEES, median, ellipse coverage."""
    d = D2
    S11, S12, S22 = S3[:, 0] + SIGMA_A ** 2, S3[:, 1], S3[:, 2] + SIGMA_A ** 2
    det = S11 * S22 - S12 ** 2
    nees = (S22 * d[:, 0] ** 2 - 2 * S12 * d[:, 0] * d[:, 1] + S11 * d[:, 1] ** 2) / det
    per = np.bincount(s, weights=nees, minlength=n_scenes) / np.maximum(np.bincount(s, minlength=n_scenes), 1)
    pres = np.bincount(s, minlength=n_scenes) > 0
    return {"records": int(len(nees)), "ANEES_scene": float(np.mean(per[pres])), "ANEES_record": float(np.mean(nees)),
            "median_NEES": float(np.median(nees)), "chi2_2_median": CHI2_2[0.5],
            "coverage": {str(p): float(np.mean(nees <= q)) for p, q in CHI2_2.items()}}


def analyse(kz, runs, gt_xy, trk_mu, trk_cov, variant="v2", h_sel=H_PRIMARY, B=B_BOOT):
    it = item_table(kz, runs, gt_xy, trk_mu, trk_cov, h_sel, variant)
    names = [str(x) for x in kz["scene_names"]]
    folds = scene_folds(names)
    arms = ["TRK"] + [a for a in ("TPP", "TPPgt") if a + "_ok" in it]
    res = {"variant": variant, "h": h_sel, "folds": {str(f): sorted(np.array(names)[folds == f].tolist()) for f in range(N_FOLDS)},
           "counts": {}, "populations": {}}
    common = np.ones(len(it["s"]), bool)
    for a in arms:
        common &= it[a + "_ok"]
    res["counts"] = {"relied_items_h": int(len(common)), "common_ok": int(common.sum()),
                     **{a + "_ok": int(it[a + "_ok"].sum()) for a in arms}}
    pops = {"PD7": common, "SD1_7": common & (it["gap"] <= 5.0), "PD": common & it["inpath"]}
    # every method is fitted ONCE, cross-fitted on the PD7 items (the calibration population, as K7 / K8), and its
    # held-out margins are then evaluated on PD7 and on its sub-populations SD1_7 and PD
    items7, m7, lv7 = mlib_items(it, pops["PD7"], kz)
    EXC, MARG, fitinfo = {}, {}, {}
    for a in arms:
        D, V = it[a + "_D"][pops["PD7"]], it[a + "_V"][pops["PD7"]]
        sd = np.sqrt(np.maximum(V + SIGMA_A ** 2, 1e-6))
        thr, src, fits = crossfit(D / sd, items7["s"], lv7, folds)
        for meth, mg in (("B0", Z * sd), ("B4", thr["B4"] * sd), ("B3", thr["B3"] * sd), ("Mstar", thr["Mstar"] * sd)):
            EXC[a + "_" + meth] = (D > mg).astype(float)
            MARG[a + "_" + meth] = mg
        fitinfo[a] = {"folds": fits, "Mstar_own_threshold_share": float(np.mean(src == 0))}
    idx7 = np.nonzero(pops["PD7"])[0]
    for pname, sel in pops.items():
        items, m, lv = mlib_items(it, sel, kz)
        s = items["s"]
        sub = np.isin(idx7, np.nonzero(sel)[0])
        exc = {k: v[sub] for k, v in EXC.items()}
        marg = {k: v[sub] for k, v in MARG.items()}
        rng = np.random.default_rng(BOOT_SEED)
        W = M.boot_scene_weights(items, B, rng, "log")
        cells = M.make_cells(items, m, "E2")
        pairs = []
        if "TPP" in arms:
            pairs.append(("TPP_B0", "TRK_B0", list(range(len(cells))), "TPP_B0 - TRK_B0"))
            if "TPPgt" in arms:
                pairs.append(("TPP_B0", "TPPgt_B0", list(range(len(cells))), "TPP_B0 - TPPgt_B0 (input-noise share)"))
        st = M.eval_stats(items, {"lv": lv}, marg, cells, W, exc_frac=exc, pairs=pairs) if cells else None
        pooled = M.eval_stats(items, {"lv": lv}, marg, [("pooled", list(range(M.N_L0)))], W, exc_frac=exc,
                              pairs=[(p[0], p[1], [0], p[3]) for p in pairs])
        hk = {}
        for meth in marg:
            pc = pooled["methods"][meth]["cells"]["pooled"]
            hk[meth] = {"no_flagged_cell": (not st["methods"][meth]["any_sig_under"]) if st else None,
                        "flagged_cells": st["methods"][meth]["sig_under_cells"] if st else [],
                        "pooled_E": pc["E_scene"], "pooled_lb": pc["lb_sim"], "pooled_ub": pc["ub_sim"],
                        "pooled_not_flagged": not pc["sig_under"], "HK1c_pooled_ub_le_delta_plus_0.03": pc["ub_sim"] <= DELTA + HK1C_EPS,
                        "mean_margin_m": pc["mean_margin_m"]}
            hk[meth]["HK1"] = bool(hk[meth]["no_flagged_cell"] is not False and hk[meth]["pooled_not_flagged"] and cells)
        res["populations"][pname] = {"items": int(sel.sum()), "scenes": int(len(np.unique(s))), "cells": [c[0] for c in cells],
                                     "validity": hk, "cells_stats": st, "pooled_stats": pooled, "fits": fitinfo}
    # A6-type diagnostics on the relied records at h (2-D), common set
    recs = np.unique(it["rec"][pops["PD7"]])
    s_rec = kz["rec_s"][recs].astype(int)
    a6res = {"TRK": a6(gt_xy[recs] - trk_mu[recs], trk_cov[recs], s_rec, len(names))}
    for src, z in runs.items():
        name = "TPP" if src == "trk" else "TPPgt"
        a6res[name] = a6(gt_xy[recs] - z[variant + "_mu"][recs], z[variant + "_cov"][recs], s_rec, len(names))
    res["A6"] = a6res
    # hypotheses H1-H3 (D17 section 2), per tracker, on PD7
    v = res["populations"]["PD7"]["validity"]
    cs = res["populations"]["PD7"]["pooled_stats"]["paired"]
    res["hypotheses"] = {
        "H1_raw_TPP_overconfident": bool(v["TPP_B0"]["pooled_lb"] > DELTA) if "TPP_B0" in v else None,
        "H2_Mstar_TPP_valid_HK1": bool(v["TPP_Mstar"]["HK1"]) if "TPP_Mstar" in v else None,
        "H2_Mstar_TPP_HK1c": bool(v["TPP_Mstar"]["HK1c_pooled_ub_le_delta_plus_0.03"]) if "TPP_Mstar" in v else None,
        "H3_gt_history_less_exceedance": (bool(cs["TPP_B0 - TPPgt_B0 (input-noise share)"]["cells"]["pooled"]["positive"])
                                          if "TPP_B0 - TPPgt_B0 (input-noise share)" in cs else None)}
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--runs", nargs="+", required=True, help="source=path, sources trk (primary) and gt")
    ap.add_argument("--out", required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--freeze-record", default=None)
    ap.add_argument("--variants", nargs="+", default=["v2", "v1"])
    ap.add_argument("--boot", type=int, default=B_BOOT)
    ap.add_argument("--cache-dir", default=None, help="this machine's val cache when the keys were built on the pod")
    a = ap.parse_args()
    t0 = time.time()
    me = sha(os.path.abspath(__file__))
    if not a.synthetic:
        assert a.plan and a.freeze_record, "real data: the frozen plan and its freeze record are required (D17 is a draft)"
        fr = json.load(open(a.freeze_record))
        assert fr.get("analysis_sha256") == me, "this analysis file is not the frozen one"
        assert fr.get("plan_sha256") == sha(a.plan), "the plan file is not the frozen one"
    run_paths = dict(x.split("=", 1) for x in a.runs)
    kz, runs, gt_xy, trk_mu, trk_cov = load_inputs(a.keys, run_paths, a.synthetic, a.cache_dir)
    out = {"stamp": SYN_STAMP if a.synthetic else "TPP arm analysis on the frozen D17 plan", "analysis_sha256": me,
           "keys_sha256": sha(a.keys), "runs_sha256": {k: sha(v) for k, v in run_paths.items()},
           "results": {v: analyse(kz, runs, gt_xy, trk_mu, trk_cov, v, H_PRIMARY, a.boot) for v in a.variants}}
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({v: out["results"][v]["hypotheses"] for v in a.variants}))
    print("TPP ANALYSE V01 DONE")


if __name__ == "__main__":
    main()
