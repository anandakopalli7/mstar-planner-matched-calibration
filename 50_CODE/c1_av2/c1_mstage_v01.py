#!/usr/bin/env python3
"""C1 method stage on AV2: E1-AV2 and E2-AV2 (Claude line, c1_mstage_v01, 2 Nov 2026). C1 v04 sections 1.1 (H6a, H6b, H7), 3, 5.3.

It runs m_run_v04's run_e1 and run_e2 (M-PLAN v05 sections 6 and 7; m_run_v04 and m_lib_v04 are imported unchanged) with three
process-local substitutions, nothing else:
  1. seeds: m_lib_v04.SEED := 20261113, so the E1 repetitions use log folds seeded 20261113 + r (r = 0..19), the refit-CV
     replicates 20261113 + 1000 + b, and every bootstrap generator [20261113, crc32(label)] (C1 v04 section 5.3);
  2. exact CRC (E15): x1_lib_v03.crc_threshold := c1_crc_exact_v01.crc_threshold_exact, so every CRC accept/reject of every
     method-stage fit (M*, B4, B9, the fallback chain, ...) is decided in exact rational arithmetic (B2's variance inflation is
     not a CRC rule and is unchanged);
  3. the refit bootstrap arrays are kept (m_lib_v04.eval_stats_replicates is wrapped, its arithmetic unchanged), so H6b gets its
     p-value: min over cells where M* is not flagged of max(p of "B4's sup-t LB > delta", p of "B4 - M* sup-t LB > 0").
Data: AV2 in-path items through m_data_v04.load_split (the x1 export layout the AV2 port writes) as the E1-AV2 set and the E2-AV2
evaluation set; the 700 nuScenes train scenes as E2-AV2's training set. Cells from counts only: E1-AV2 kind "E1", E2-AV2 kind "E2".
Inference sizes (C1 v04 section 3): E1 fixed-rule B = 2000 over 20 repetitions, refit-CV B = 200 (decision horizon 2 s);
E2 two-sample refit log bootstrap B = 1000. --test allows smaller sizes for tests only.
Output (consumed by c1_analyse_v02): {"E1": {"fixed", "refit", "hypotheses", ...}, "E2": {"cells", "all", "hypotheses"}, "H6b_p",
"H6b_detail", "seeds", "exact_crc"}.
Usage: python -B c1_mstage_v01.py --tracker T1 --experiment <id> --av2-workers <dirs> --av2-gt <json> --av2-meta <dir>
       --av2-horizon <jsonl.gz> --train-workers <dirs> --train-gt <json> --train-meta <dir> --train-horizon <jsonl.gz> --out <json>
       [--test --reps r --boot B --refit-boot B --e2-boot B] [--float-crc --m-seeds]   (the last two: reproduction of m_run_v04)
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
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
import c1_crc_exact_v01 as X  # noqa: E402
import m_run_v04 as R  # noqa: E402

M = R.M
MD = R.MD
SEED_C1 = 20261113
_ORIG = {"seed": M.SEED, "crc": M.L.crc_threshold, "esr": M.eval_stats_replicates}
CAPTURE = {}


def eval_stats_replicates_capture(items, P, marg_point, families, replicates, delta=M.DELTA, level=0.95, exc_point=None, pairs=None):
    """m_lib_v04.eval_stats_replicates, unchanged arithmetic, plus: the per-family bootstrap estimate arrays are kept in CAPTURE."""
    pairs = pairs or {}
    lays = {f: M._layout(items, P, cells, None) for f, cells in families.items()}
    tabs = {f: {} for f in families}
    for f, lay in lays.items():
        for m, mg in marg_point.items():
            exc = (lay["D"] > mg).astype(float) if exc_point is None else exc_point[m]
            tabs[f][m] = M._tables(lay, mg, exc)
    acc = {f: {m: ([], [], [], []) for m in marg_point} for f in families}
    for it_b, P_b, exc_b, marg_b, w_b in replicates:
        w = np.ones(it_b["n_scenes"]) if w_b is None else w_b
        for f, cells in families.items():
            lay_b = M._layout(it_b, P_b, cells, None)
            for m in marg_point:
                est, mb, ax = M._boot_rows(lay_b, M._tables(lay_b, marg_b[m], exc_b[m].astype(float)), w[None, :])
                acc[f][m][0].append(est[0])
                acc[f][m][1].append(mb[0])
                acc[f][m][2].append(ax[0][0])
                acc[f][m][3].append(ax[1][0])
    out = {}
    for f in families:
        boots = {m: (np.array(v[0]), np.array(v[1]), [np.array(v[2]), np.array(v[3])]) for m, v in acc[f].items()}
        out[f] = M._summary(lays[f], tabs[f], boots, delta, level, pairs.get(f, ()))
        CAPTURE[f] = {m: boots[m][0] for m in boots}
    return out


def configure(exact=True, c1_seeds=True):
    M.SEED = SEED_C1 if c1_seeds else _ORIG["seed"]
    M.L.crc_threshold = X.crc_threshold_exact if exact else _ORIG["crc"]
    M.eval_stats_replicates = eval_stats_replicates_capture


def supt_p(est, boot, target):
    """p-value of 'sup-t lower bound > target' per cell (M._simul's statistic over the whole family)."""
    est, boot = np.asarray(est, float), np.asarray(boot, float)
    se = np.nanstd(boot, axis=0, ddof=1)
    ok = se > 0
    with np.errstate(invalid="ignore", divide="ignore"):
        T = np.nanmax(np.where(ok, (boot - est) / np.where(ok, se, 1.0), np.nan), axis=1) if ok.any() else np.full(len(boot), np.nan)
        t = np.where(ok, (est - target) / np.where(ok, se, 1.0), np.nan)
    return np.array([float(np.mean(T >= t[j])) if ok[j] else (0.0 if est[j] > target else 1.0) for j in range(len(est))])


def h6b_pvalue(refit, boots, delta=M.DELTA):
    """H6b's p-value from the refit-CV bootstrap arrays of the 'cells' family (B x cells for B4 and M*)."""
    cells = refit["cells"]
    eB = np.array([refit["methods"]["B4"]["cells"][c]["E_scene"] for c in cells])
    eM = np.array([refit["methods"]["Mstar"]["cells"][c]["E_scene"] for c in cells])
    pB = supt_p(eB, boots["B4"], delta)
    pd = supt_p(eB - eM, boots["B4"] - boots["Mstar"], 0.0)
    cand = [j for j, c in enumerate(cells) if not refit["methods"]["Mstar"]["cells"][c]["sig_under"]]
    per = {cells[j]: max(float(pB[j]), float(pd[j])) for j in cand}
    return (min(per.values()) if per else 1.0), per


def run(av2, train, tracker, reps, B, BR, B2, h="h2s"):
    ai, arc = av2[h]
    ti, trc = train[h]
    m_a = M.motion_state(ai)
    c1 = M.make_cells(ai, m_a, "E1")
    c2 = M.make_cells(ai, m_a, "E2")
    names, slog = av2["_names"], av2["_slog"]
    CAPTURE.clear()
    e1 = R.run_e1(ai, arc, {}, names, slog, c1, "%s|E1-AV2|%s" % (tracker, h), B=B, reps=reps, refit_B=BR)
    boots = {m: CAPTURE["cells"][m] for m in ("B4", "Mstar")}
    p, per = h6b_pvalue(e1["refit"], boots)
    e2 = R.run_e2(ti, trc, ai, arc, {}, c2, "%s|E2-AV2|%s" % (tracker, h), B=B2)
    return {"E1": e1, "E2": e2, "H6b_p": p, "H6b_detail": per, "cells_E1": [n for n, _ in c1], "cells_E2": [n for n, _ in c2]}


def load(workers, gt, meta, horizon, experiment):
    data, info, names, slog = MD.load_split(workers, gt, meta, horizon, experiment)
    data["_names"], data["_slog"], data["_info"] = names, slog, info
    return data


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--experiment", required=True)
    for p in ("av2", "train"):
        ap.add_argument("--%s-workers" % p, nargs="+", required=True)
        ap.add_argument("--%s-gt" % p, required=True)
        ap.add_argument("--%s-meta" % p, required=True)
        ap.add_argument("--%s-horizon" % p, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--reps", type=int, default=M.R_CV)
    ap.add_argument("--boot", type=int, default=M.B_BOOT)
    ap.add_argument("--refit-boot", type=int, default=M.B_E1R)
    ap.add_argument("--e2-boot", type=int, default=M.B_REFIT)
    ap.add_argument("--float-crc", action="store_true", help="reproduction of m_run_v04 only")
    ap.add_argument("--m-seeds", action="store_true", help="reproduction of m_run_v04 only")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_mstage_v01", "c1_mstage_v04", {"AV2-set exports": LEGACY.ds_exports(a.av2_workers),
                                                  "training exports": LEGACY.ds_exports(a.train_workers)})
    if not a.test:
        assert (a.reps, a.boot, a.refit_boot, a.e2_boot) == (M.R_CV, M.B_BOOT, M.B_E1R, M.B_REFIT) and not (a.float_crc or a.m_seeds), \
            "the confirmatory sizes and seeds are fixed (20 repetitions, B = 2000 / 200 / 1000, C1 seeds, exact CRC)"
    configure(exact=not a.float_crc, c1_seeds=not a.m_seeds)
    t0 = time.time()
    av2 = load(a.av2_workers, a.av2_gt, a.av2_meta, a.av2_horizon, a.experiment)
    train = load(a.train_workers, a.train_gt, a.train_meta, a.train_horizon, a.experiment)
    print("loaded %.0f s" % (time.time() - t0), flush=True)
    res = run(av2, train, a.tracker, a.reps, a.boot, a.refit_boot, a.e2_boot)
    res.update({"tracker": a.tracker, "seeds": {"base": M.SEED, "e1_folds": "base + r", "refit": "base + 1000 + b"},
                "exact_crc": not a.float_crc, "sizes": {"reps": a.reps, "B": a.boot, "refit_B": a.refit_boot, "e2_B": a.e2_boot},
                "test_mode": bool(a.test), "av2_info": av2["_info"], "train_info": train["_info"],
                "code_sha256": {"c1_mstage_v01": hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()},
                "seconds": round(time.time() - t0, 1)})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps({"H6a": res["E1"]["hypotheses"]["HM1"], "H6b_any": res["E1"]["hypotheses"]["HM2"].get("B4"), "H6b_p": res["H6b_p"],
                      "H7": res["E2"]["hypotheses"]["HM6"]}))
    print("C1 MSTAGE DONE")


if __name__ == "__main__":
    main()
