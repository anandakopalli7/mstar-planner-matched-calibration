#!/usr/bin/env python3
"""C1 predictor arms (Claude line, c1_predarm_v01, 2 Nov 2026): H9 (Trajectron++ int_ee, secondary, Choice 23) and Q1 (QCNet,
descriptive, Choice 20) on the C1 folds. C1 v04 sections 1.1, 1.2, 3, 4, 11.4.

Join and scoring are the tpp helper's (50_CODE/tpp/tpp_analyse_v01.py, imported unchanged): the K8 relied items at the 2 s step
(tpp_keys_v01 keys: scene, k, h, row, tid, inst, pair; geometry from the keys), the predictor's moment-matched V2 Gaussian (primary)
per record, D = a*.(g - mu) along the item's toward-ego normal, sd = sqrt(a*' S a* + 0.10^2), U = D / sd.
QCNet (descriptive) enters through qcnet_runs(): its rows (sample_token, instance_token; 2 s output v2_mu, v2_cov 2x2) are aligned
to the keys' records by (rec_sample_token, rec_instance_token), which the AV2 keys file carries, and scored the same way; the GT
source (qcnet_av2_v02, re-centred) and the deployed source (qcnet_av2_v03, matched AB3DMOT with T1's SF_thre, re-centred).
Calibration: DP-SCRC (M*'s rule: per-L0 CRC, fallback L0 -> L3, n_min = 19), cross-fitted on the C1 folds (each unit's thresholds
from the other folds), every CRC decision exact (c1_crc_exact_v01). Tables: per unit (log) and evaluation cell (m_lib_v04.make_cells,
kind E2, >= 39 units from >= 8 logs) the item and exceedance counts. Rule (c1_analyse_v01.h9_rule): no evaluable cell flagged, the
pooled cell not flagged, >= 6 power-qualified cells and none flagged. Seeds [20261110, i, 5] (bootstrap), [20261111, i, 5] (power).
Populations: PD (in-path relied items; the H9 population) and PD7 (all relied items; reported).
Usage: python -B c1_predarm_v01.py --keys <keys npz> --runs trk=<npz> [gt=<npz>] --folds <c1 folds json> --tracker-index 0|1
       --out <json> [--cache <dir>] [--synthetic] [--qcnet-deployed <npz> --qcnet-gt <npz>]
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "tpp"))
import c1_crc_exact_v01 as X  # noqa: E402
import c1_analyse_v01 as CA  # noqa: E402
import tpp_analyse_v01 as TA  # noqa: E402

M = X.M
SIGMA_A = M.SIGMA_A
J_PRED = 5


def qcnet_runs(qz, kz):
    """A tpp-run-like dict for the keys' records from a QCNet output file: rows aligned by (sample_token, instance_token)."""
    idx = {(str(s), str(i)): r for r, (s, i) in enumerate(zip(qz["sample_token"], qz["instance_token"]))}
    n = len(kz["rec_k"])
    st = np.full(n, 1, np.int8)
    mu, cov = np.zeros((n, 2)), np.ones((n, 3))
    for j, key in enumerate(zip(kz["rec_sample_token"], kz["rec_instance_token"])):
        r = idx.get((str(key[0]), str(key[1])))
        if r is not None and bool(qz["finite"][r]) and bool(qz["pd_v2"][r]):
            st[j] = TA.C.ST_OK
            mu[j] = qz["v2_mu"][r]
            c = qz["v2_cov"][r]
            cov[j] = (c[0, 0], c[0, 1], c[1, 1])
    return {"status": st, "v2_mu": mu, "v2_cov": cov, "v1_mu": mu, "v1_cov": cov, "rec_index": np.arange(n), "rec_pair": kz["rec_pair"],
            "rec_s": kz["rec_s"]}


def tables(it, kz, arm, pop, fold_of_unit):
    """Cross-fitted exceedance tables (units x cells) of one arm and population."""
    ok = it[arm + "_ok"].copy()
    if pop == "PD":
        ok &= it["inpath"]
    U = it[arm + "_D"][ok] / np.sqrt(it[arm + "_V"][ok] + SIGMA_A ** 2)
    s = it["s"][ok]
    mi, m, lv = TA.mlib_items(it, ok, kz)
    thr = np.full(len(U), np.nan)
    src = np.full(len(U), -1)
    folds = sorted(set(fold_of_unit[fold_of_unit >= 0].tolist()))
    for f in folds:
        cal, te = fold_of_unit[s] != f, fold_of_unit[s] == f
        t_m, t_src = X.fit_hier_exact(U[cal], s[cal], [x[cal] for x in lv], 0)
        assert not np.isnan(t_m[lv[0][te]]).any(), "a held-out stratum has no threshold at any level"
        thr[te], src[te] = t_m[lv[0][te]], t_src[lv[0][te]]
    exc = U > thr
    cells = M.make_cells(mi, m, "E2")
    l2c = np.full(M.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l2c[ids] = j
    cj = l2c[lv[0]]
    units = np.unique(s)
    ui = {u: i for i, u in enumerate(units)}
    N = np.zeros((len(units), len(cells)))
    Xc = np.zeros((len(units), len(cells)))
    keep = cj >= 0
    np.add.at(N, (np.array([ui[x] for x in s[keep]]), cj[keep]), 1.0)
    np.add.at(Xc, (np.array([ui[x] for x in s[keep]]), cj[keep]), exc[keep].astype(float))
    return N, Xc, cells, units, {"items": int(len(U)), "exceed_share": float(exc.mean()) if len(U) else None,
                                 "fallback_share": float(np.mean(src > 0)) if len(U) else None}


def arm_result(it, kz, arm, pop, fold_of_unit, i):
    N, Xc, cells, units, info = tables(it, kz, arm, pop, fold_of_unit)
    logs = np.array([str(kz["scene_logs"][u]) for u in units])
    ulog = sorted(set(logs.tolist()))
    log_of_ep = np.array([ulog.index(x) for x in logs])
    scene_of_ep = np.array([str(kz["scene_names"][u]) for u in units])
    rng = np.random.default_rng([CA.SEED_BOOT, i, J_PRED])
    W_logs = rng.multinomial(len(ulog), np.full(len(ulog), 1.0 / len(ulog)), size=CA.K.B_BOOT).astype(float)
    r = CA.h9_rule(N, Xc, cells, scene_of_ep, log_of_ep, W_logs[:, log_of_ep], [CA.SEED_POWER, i, J_PRED])
    r.update(info)
    r["units"], r["logs"], r["cells"] = int(len(units)), len(ulog), [c[0] for c in cells]
    return r


def main(argv=None):
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
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_predarm_v01", "c1_predarm_v04", {"keys": LEGACY.ds_keys(a.keys)})
    fj = json.load(open(a.folds))
    runs = dict(x.split("=", 1) for x in a.runs)
    if runs:
        kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)
    else:
        kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, {}, a.synthetic, a.cache)
    kz = dict(kz)
    names = [str(x) for x in kz["scene_names"]]
    fold_of_unit = np.array([int(fj["fold_of_log"].get(n, -1)) for n in names])
    assert (fold_of_unit >= 0).sum() > 0, "no unit of the keys is in the folds"
    out = {"label": {"TPP": "H9 secondary (Choice 23)", "TPPgt": "descriptive (ground-truth histories, upper bound)",
                     "Q1_deployed": "Q1 descriptive (Choice 20)", "Q1_gt": "Q1 descriptive, upper bound"},
           "folds_sha256": CA.sha(a.folds), "keys_sha256": CA.sha(a.keys), "arms": {}}
    if rz:
        it = TA.item_table(kz, rz, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        for arm in ("TPP", "TPPgt"):
            if arm + "_D" in it:
                out["arms"][arm] = {pop: arm_result(it, kz, arm, pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    for name, path in (("Q1_deployed", a.qcnet_deployed), ("Q1_gt", a.qcnet_gt)):
        if path:
            qr = qcnet_runs(np.load(path, allow_pickle=False), kz)
            it = TA.item_table(kz, {"trk": qr}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
            out["arms"][name] = {pop: arm_result(it, kz, "TPP", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    if "TPP" in out["arms"]:
        out["H9"] = out["arms"]["TPP"]["PD"]["H9"]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({k: {p: (v[p]["H9"], v[p]["family_size"], v[p]["flagged"]) for p in v} for k, v in out["arms"].items()}))
    print("C1 PREDARM DONE")


if __name__ == "__main__":
    main()
