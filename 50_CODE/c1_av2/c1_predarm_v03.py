#!/usr/bin/env python3
"""C1 predictor arms v03 (Claude line, c1_predarm_v03, 4 Nov 2026) = c1_predarm_v02 (kept, imported: guard, chains, Choice 35's
checks, the join and scoring unchanged) plus D16 v16 Choice 37: history length is a calibration stratum of the predictor arm.
  * History length (HL) of an item = its predictor's own input history at decision time k, from the Trajectron++ keys (tpp_keys_v01:
    the contiguous states up to k): rec_hist_stratum_trk for TPP (tracker histories, the H9 arm), rec_hist_stratum_gt for TPPgt
    (ground-truth histories, descriptive). Strata {2, 3-4, >=5 states} (tpp_common_v01.hist_stratum). Nothing after k is read.
    A used item with a stratum below 2 states is an error (the predictor does not run on it).
  * H9 (primary for the arm, Choice 37): DP-SCRC with HL as a stratum dimension: levels L0 x HL, L1 x HL, L2 x HL, L3 x HL, then L3
    (the axis) as the last fallback so that every item has a threshold; at each level a cell is fitted by exact CRC
    (c1_crc_exact_v01.crc_threshold_exact) when it has >= 19 calibration units (n_min, as M*), else the item falls back to the next
    level. Cross-fitted on the C1 folds exactly as v01. Validity family: the E2 evaluation cells (m_lib_v04.make_cells, as v01) PLUS
    the three pooled HL cells {2, 3-4, >=5}; H9's rule (c1_analyse_v01.h9_rule: no evaluable cell flagged, the pooled cell not flagged,
    >= 6 power-qualified cells, none flagged) is applied to that family. Same bootstrap and power seeds as v01 ([20261110, i, 5],
    [20261111, i, 5]).
  * H9-noHL (descriptive, Choice 37): v02's arm unchanged (D17-style stratification, E2 cells only); its "H9" value is reported as H9_noHL.
  * Diagnostic: the noHL thresholds evaluated on the E2 + HL family ("noHL_on_HL_cells"), so a short-history excess of the noHL
    method is visible.
  * Q1 (QCNet, descriptive): QCNet's own input history is not in the keys, so Q1 stays noHL (v02's rule) and says so.
Usage: as c1_predarm_v02.
"""
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v02 as G  # noqa: E402
import c1_predarm_v02 as P2  # noqa: E402

P1, TA = P2.P1, P2.TA
X, CA, M = P1.X, P1.CA, P1.M
ROLE = "entry:c1_predarm"
HL_KEY = {"TPP": "rec_hist_stratum_trk", "TPPgt": "rec_hist_stratum_gt"}
HL_NAMES = ("hist=2", "hist=3-4", "hist>=5")
N_MIN = M.N_CRC
POPULATION = P2.POPULATION + "; H9 strata and family include history length {2, 3-4, >=5} (D16 v16 Choice 37)"


def fit_levels(U, unit, lvs, n_min=N_MIN):
    """Exact-CRC threshold per (level, cell) with >= n_min units."""
    tabs = []
    for ids in lvs:
        t = {}
        for c in np.unique(ids):
            sel = ids == c
            if len(np.unique(unit[sel])) >= n_min:
                t[int(c)] = X.crc_threshold_exact(U[sel], unit[sel])
        tabs.append(t)
    return tabs


def apply_levels(tabs, lvs):
    n = len(lvs[0])
    thr, src = np.full(n, np.nan), np.full(n, -1)
    for lev, (t, ids) in enumerate(zip(tabs, lvs)):
        todo = np.isnan(thr)
        for c, v in t.items():
            sel = todo & (ids == c)
            thr[sel], src[sel] = v, lev
    return thr, src


def hl_levels(lv, hl):
    return [lv[0] * 3 + hl, lv[1] * 3 + hl, lv[2] * 3 + hl, lv[3] * 3 + hl, lv[3]]


def tables_hl(it, kz, arm, pop, fold_of_unit, hl_fit, hl_key):
    """Cross-fitted exceedance tables over the E2 cells plus the 3 HL cells; thresholds with (hl_fit) or without HL strata."""
    ok = it[arm + "_ok"].copy()
    if pop == "PD":
        ok &= it["inpath"]
    D, V = it[arm + "_D"][ok], it[arm + "_V"][ok]
    assert np.all(np.isfinite(D)) and np.all(np.isfinite(V)) and np.all(V >= 0), "%s %s: non-finite D or variance (Choice 35)" % (arm, pop)
    s = it["s"][ok]
    assert np.all(fold_of_unit[s] >= 0), "%s %s: a unit outside the folds (Choice 35)" % (arm, pop)
    hl = np.asarray(kz[hl_key])[it["rec"][ok]].astype(int)
    assert np.all(hl >= 0), "%s %s: a used item with fewer than 2 history states" % (arm, pop)
    U = D / np.sqrt(V + P1.SIGMA_A ** 2)
    mi, m, lv = TA.mlib_items(it, ok, kz)
    lvs = hl_levels(lv, hl) if hl_fit else list(lv)
    thr, src = np.full(len(U), np.nan), np.full(len(U), -1)
    for f in sorted(set(fold_of_unit[fold_of_unit >= 0].tolist())):
        cal, te = fold_of_unit[s] != f, fold_of_unit[s] == f
        tabs = fit_levels(U[cal], s[cal], [x[cal] for x in lvs])
        thr[te], src[te] = apply_levels(tabs, [x[te] for x in lvs])
    assert np.all(np.isfinite(thr)), "%s %s: an item without a threshold at any level" % (arm, pop)
    exc = U > thr
    cells = M.make_cells(mi, m, "E2")
    l2c = np.full(M.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l2c[ids] = j
    cj = l2c[lv[0]]
    units = np.unique(s)
    ui = np.searchsorted(units, s)
    nc = len(cells) + 3
    N, Xc = np.zeros((len(units), nc)), np.zeros((len(units), nc))
    keep = cj >= 0
    np.add.at(N, (ui[keep], cj[keep]), 1.0)
    np.add.at(Xc, (ui[keep], cj[keep]), exc[keep].astype(float))
    np.add.at(N, (ui, len(cells) + hl), 1.0)
    np.add.at(Xc, (ui, len(cells) + hl), exc.astype(float))
    names = list(cells) + [(n, []) for n in HL_NAMES]
    info = {"items": int(len(U)), "exceed_share": float(exc.mean()) if len(U) else None,
            "items_by_hl": {HL_NAMES[h]: int((hl == h).sum()) for h in range(3)},
            "exceed_share_by_hl": {HL_NAMES[h]: (float(exc[hl == h].mean()) if (hl == h).any() else None) for h in range(3)},
            "fallback_share_by_level": {str(l): float(np.mean(src == l)) for l in range(len(lvs))}, "hl_fit": bool(hl_fit)}
    return N, Xc, names, units, info


def rule(N, Xc, cells, units, kz, i, cols=None):
    cols = list(range(N.shape[1])) if cols is None else cols
    logs = np.array([str(kz["scene_logs"][u]) for u in units])
    ulog = sorted(set(logs.tolist()))
    log_of_ep = np.array([ulog.index(x) for x in logs])
    scene_of_ep = np.array([str(kz["scene_names"][u]) for u in units])
    rng = np.random.default_rng([CA.SEED_BOOT, i, P1.J_PRED])
    W_logs = rng.multinomial(len(ulog), np.full(len(ulog), 1.0 / len(ulog)), size=CA.K.B_BOOT).astype(float)
    r = CA.h9_rule(N[:, cols], Xc[:, cols], [cells[j] for j in cols], scene_of_ep, log_of_ep, W_logs[:, log_of_ep], [CA.SEED_POWER, i, P1.J_PRED])
    r["cells"], r["units"], r["logs"] = [cells[j][0] for j in cols], int(len(units)), len(ulog)
    return r


def arm_results(it, kz, arm, pop, fold_of_unit, i):
    hk = HL_KEY[arm]
    N, Xc, cells, units, info = tables_hl(it, kz, arm, pop, fold_of_unit, True, hk)
    hl_r = dict(rule(N, Xc, cells, units, kz, i), **info)
    N0, X0, c0, u0, info0 = tables_hl(it, kz, arm, pop, fold_of_unit, False, hk)
    diag = dict(rule(N0, X0, c0, u0, kz, i), **info0)
    nohl = P1.arm_result(it, kz, arm, pop, fold_of_unit, i)
    return {"HL": hl_r, "noHL": nohl, "noHL_on_HL_cells": diag}


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--folds", required=True)
    ap.add_argument("--tracker-index", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--qcnet-deployed", default=None)
    ap.add_argument("--qcnet-gt", default=None)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None)
    a = ap.parse_args(argv)
    kz0 = np.load(a.keys, allow_pickle=False)
    names = [str(x) for x in kz0["scene_names"]]
    if a.synthetic:
        assert str(kz0["stamp"]) == TA.SYN_STAMP and a.plan is None, "--synthetic: synthetic keys, no plan"
        ds = "synthetic"
    else:
        ds = G.dataset_checked(None, names)
        mp = os.path.join(a.cache or str(kz0["cache_dir"]), "MANIFEST.json")
        assert G.manifest_dataset(json.load(open(mp))) == ds, "the keys' units and their cache disagree on the dataset"
    fj = json.load(open(a.folds))
    outside = sorted(n for n in names if n not in fj["fold_of_log"])
    assert not outside, "units of the keys outside the folds: an error, never a non-exceedance (D16 Choice 35): %s" % outside[:5]
    runs = dict(x.split("=", 1) for x in a.runs)
    files = [a.keys] + list(runs.values()) + [p for p in (a.qcnet_deployed, a.qcnet_gt) if p]
    side = frozen = None
    chains = {}
    if ds == "synthetic":
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha, checked = G.sha(a.folds), False
    else:
        g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        if g:
            side, frozen, rt = g
            folds_sha = G.require_bound(frozen, a.folds, "folds")
            chains["keys"] = P2.chain_keys(kz0, a.keys, a.cache, side, frozen)
            chains["runs"] = {src: P2.chain_run(p, G.sha(a.keys), frozen) for src, p in runs.items()}
            q = [p for p in (a.qcnet_deployed, a.qcnet_gt) if p]
            if q:
                chains["qcnet"] = G.check_inputs(frozen, q)
            checked = True
        else:
            rt = G.code_record(os.path.abspath(__file__))
            folds_sha, checked = G.sha(a.folds), False
    kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)
    kz = dict(kz)
    for src in runs:
        k = HL_KEY["TPP" if src == "trk" else "TPPgt"]
        assert k in kz, "the keys carry no %s (history length, Choice 37)" % k
    fold_of_unit = np.array([int(fj["fold_of_log"][n]) for n in names])
    out = {"label": {"TPP": "H9 secondary (Choice 23), HL-stratified (Choice 37); H9_noHL descriptive",
                     "TPPgt": "descriptive (ground-truth histories, upper bound)", "Q1_deployed": "Q1 descriptive (Choice 20), noHL",
                     "Q1_gt": "Q1 descriptive, upper bound, noHL"},
           "population": POPULATION, "history_length": {"TPP": HL_KEY["TPP"], "TPPgt": HL_KEY["TPPgt"], "strata": list(HL_NAMES),
                                                         "source": "the predictor's own input history at k (tpp keys); nothing after k"},
           "folds_sha256": folds_sha, "keys_sha256": G.sha(a.keys), "arms": {}, "units": len(names),
           "fold_units_without_keys": sorted(set(fj["fold_of_log"]) - set(names))}
    if rz:
        it = TA.item_table(kz, rz, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        for arm in ("TPP", "TPPgt"):
            if arm + "_D" in it:
                out["arms"][arm] = {pop: arm_results(it, kz, arm, pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    for name, path in (("Q1_deployed", a.qcnet_deployed), ("Q1_gt", a.qcnet_gt)):
        if path:
            qr = P1.qcnet_runs(np.load(path, allow_pickle=False), kz)
            it = TA.item_table(kz, {"trk": qr}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
            out["arms"][name] = {pop: {"noHL": P1.arm_result(it, kz, "TPP", pop, fold_of_unit, a.tracker_index),
                                       "note": "QCNet's own input history is not in the keys: no HL stratum"} for pop in ("PD", "PD7")}
    if "TPP" in out["arms"]:
        out["H9"] = out["arms"]["TPP"]["PD"]["HL"]["H9"]
        out["H9_noHL"] = out["arms"]["TPP"]["PD"]["noHL"]["H9"]
    if frozen is not None:
        rt = G.verify_runtime_again(frozen, rt)
    out["provenance"] = {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                         "inputs_sha256": {G.rel(f): G.sha(f) for f in files}, "inputs_checked": checked, "chains": chains, "dataset": ds}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    print(json.dumps({"H9": out.get("H9"), "H9_noHL": out.get("H9_noHL"),
                      "exceed_by_hl": {k: v["PD"]["HL"]["exceed_share_by_hl"] for k, v in out["arms"].items() if "HL" in v["PD"]}}))
    print("C1 PREDARM V03 DONE")


if __name__ == "__main__":
    main()
