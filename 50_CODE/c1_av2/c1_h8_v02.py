#!/usr/bin/env python3
"""C1 H8 v02 (Claude line, c1_h8_v02, 4 Nov 2026) = c1_h8_v01 (kept) with D16 v11 Choice 31: the decision band's thresholds are
max(delta, E0_g) with E0_g THE PLAN'S VALUES (computed before the freeze from stage-A fields by c1_e0_v01, sigma_a = 0.10 m), not
the data-based null of X2's code. Everything else is v01's: X2's band over the 4 decision cells (sup-t at 0.95, log/scene bootstrap
B = x1_full_v02.B_EXC, seed [20261113, 8]), the truth-oriented band, and H8 = some lateral in-path car cell (< 20 m, 20-40 m) FAILS
in both. Only the lateral cells' thresholds matter to H8; the long cells take delta (their verdicts are reported, not used).
The data-based null is still computed and reported beside the plan's values.
Usage: python -B c1_h8_v02.py --workers ... --gt ... --meta ... --horizon ... --e0-plan <json {cell: E0}> --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_h8_v01 as H1  # noqa: E402

X2, L, F = H1.X2, H1.L, H1.F


def compute(workers, gt, meta, horizon, e0_plan, band="linear", seed=H1.SEED):
    tokens, recs = set(), []
    for w in workers:
        recs += L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
    samples, gtb, racks = L.load_gt(gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    del recs
    scene_names = sorted({s["scene"] for s in samples.values()})
    rng = np.random.default_rng(seed)
    W = L.boot_weights(len(scene_names), F.B_EXC, rng)
    hr, hst = L.build_horizon_rows(rows, L.load_horizon(horizon, {(r["scene"], r["k"], r["tid"]) for r in rows}), samples, gtb, racks)
    logit = band == "logit"
    cells, null, thr_data, elig, _ = X2.analyse_decision(hr, 0.10, rng, len(scene_names), scene_names, logit, W)
    thr = {c: max(L.DELTA, float(e0_plan["|".join(c)])) if "|".join(c) in e0_plan else L.DELTA for c in X2.DEC}
    prim = F.band_verdicts(cells, elig, len(scene_names), thr, W, logit)
    ct, sct, _ = L.cell_items(hr, sigma_a=0.10, orient="truth")
    sidx = {s: i for i, s in enumerate(scene_names)}
    for c in L.CELLS:
        if ct[c]["n"]:
            ct[c]["s"] = np.array([sidx[sct[i]] for i in ct[c]["s"]])
    truth = F.band_verdicts(ct, [c for c in X2.DEC if ct[c]["n_scenes"] >= L.MIN_SCENES], len(scene_names), {}, W, logit)
    out = {"E0_plan": dict(e0_plan), "E0_data_based_reported": {"|".join(c): (null[c][0] if null.get(c) else None) for c in X2.DEC},
           "thresholds": {"|".join(c): v for c, v in thr.items()}, "cells": {}, "bins": {}, "seed": seed, "B": F.B_EXC, "scenes": len(scene_names)}
    for c in X2.DEC:
        k = "|".join(c)
        out["cells"][k] = {"primary": dict(prim.get(k, {})), "truth_oriented": dict(truth.get(k, {})), "eligible": c in elig}
    for rb in X2.BINS:
        k = "car|%s|lat" % rb
        p, t = prim.get(k, {}), truth.get(k, {})
        out["bins"][rb] = {"cell": k, "primary_FAILS": p.get("verdict") == "FAILS", "zero_se": bool(p.get("zero_se")),
                           "truth_FAILS": t.get("verdict") == "FAILS",
                           "FAILS": bool(p.get("verdict") == "FAILS" and not p.get("zero_se") and t.get("verdict") == "FAILS")}
    out["H8"] = bool(any(v["FAILS"] for v in out["bins"].values()))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--e0-plan", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_h8_v02", "c1_h8_v04", {"exports": LEGACY.ds_exports(a.workers)})
    out = compute(a.workers, a.gt, a.meta, a.horizon, json.load(open(a.e0_plan)))
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"H8": out["H8"], "bins": out["bins"]}))
    print("C1 H8 V02 DONE")


if __name__ == "__main__":
    main()
