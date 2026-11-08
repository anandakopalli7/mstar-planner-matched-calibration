#!/usr/bin/env python3
"""C1 H8: the lateral-tail diagnosis on T1 (Claude line, c1_h8_v01, 2 Nov 2026). C1 v04 section 5.4:
  H8 := T1: exists r in {<20, 20-40}: the lateral in-path car cell r has LB > max(delta, E0_r) under B0, and its truth-oriented
        exceedance has LB > delta  (X2's FAILS rule; 95 % sup-t over the 4 decision cells).
It reuses X2's code unchanged (50_CODE/x1/x2_full_v02.py and x1_full_v02.py, x1_lib_v03): the in-path paired horizon rows
(L.build_table, L.load_horizon, L.build_horizon_rows), the decision band over the 4 cells car x {<20, 20-40} x {lat, long} with each
cell's threshold max(delta, E0) from the orientation null (x2_full_v02.analyse_decision), and the truth-oriented band
(L.cell_items(orient="truth"), x1_full_v02.band_verdicts). Unlike X2's H1 it does not require X2's sensitivities (a2-a4): C1's H8 is
the two-part rule above. Unit: the scene (= the log on AV2); bootstrap B = x1_full_v02.B_EXC with seed [20261113, 8]; band linear.
Output: per cell verdicts (primary and truth-oriented), H8 and its parts. Family P at 0.05 (C1 v04 section 5.5).
Usage: python -B c1_h8_v01.py --workers <x1 export dirs> --gt <gt json> --meta <dir with scene.json> --horizon <jsonl.gz> --out <json>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "x1"))
import x2_full_v02 as X2  # noqa: E402

L, F = X2.L, X2.F
SEED = [20261113, 8]
BINS = X2.BINS


def compute(workers, gt, meta, horizon, band="linear", seed=SEED):
    t0 = time.time()
    tokens, recs = set(), []
    for w in workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r["status_X1_gates"] == "PASS", "export worker failed its gates: " + w
        pf = json.load(open(os.path.join(w, "x1_per_frame.json")))
        wt = [p["token"] for p in pf if not p.get("error")]
        assert not (set(wt) & tokens), "token exported twice"
        tokens |= set(wt)
        recs += L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
    samples, gtb, racks = L.load_gt(gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    del recs
    scene_names = sorted({s["scene"] for s in samples.values()})
    rng = np.random.default_rng(seed)
    W = L.boot_weights(len(scene_names), F.B_EXC, rng)
    pred = L.load_horizon(horizon, {(r["scene"], r["k"], r["tid"]) for r in rows})
    hr, hst = L.build_horizon_rows(rows, pred, samples, gtb, racks)
    del pred
    logit = band == "logit"
    cells, null, thr, elig, prim = X2.analyse_decision(hr, 0.10, rng, len(scene_names), scene_names, logit, W)
    ct, sct, _ = L.cell_items(hr, sigma_a=0.10, orient="truth")
    sidx = {s: i for i, s in enumerate(scene_names)}
    for c in L.CELLS:
        if ct[c]["n"]:
            ct[c]["s"] = np.array([sidx[sct[i]] for i in ct[c]["s"]])
    elig_t = [c for c in X2.DEC if ct[c]["n_scenes"] >= L.MIN_SCENES]
    truth = F.band_verdicts(ct, elig_t, len(scene_names), {}, W, logit)
    out = {"cells": {}, "bins": {}, "band": band, "seed": seed, "B": F.B_EXC, "scenes": len(scene_names), "pairing": pst,
           "horizon_rows": hst, "E0": {"|".join(c): (null[c][0] if null.get(c) else None) for c in X2.DEC}}
    for c in X2.DEC:
        k = "|".join(c)
        out["cells"][k] = {"primary": {kk: v for kk, v in prim.get(k, {}).items()}, "truth_oriented": {kk: v for kk, v in truth.get(k, {}).items()},
                           "eligible": c in elig, "threshold_max_delta_E0": thr.get(c)}
    for rb in BINS:
        k = "car|%s|lat" % rb
        p, t = prim.get(k, {}), truth.get(k, {})
        fails = bool(p.get("verdict") == "FAILS" and not p.get("zero_se") and t.get("verdict") == "FAILS")
        out["bins"][rb] = {"cell": k, "primary_FAILS": p.get("verdict") == "FAILS", "zero_se": bool(p.get("zero_se")),
                           "truth_FAILS": t.get("verdict") == "FAILS", "FAILS": fails}
    out["H8"] = bool(any(v["FAILS"] for v in out["bins"].values()))
    out["seconds"] = round(time.time() - t0, 1)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--label", default="C1 H8 (T1)")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_h8_v01", "c1_h8_v04", {"exports": LEGACY.ds_exports(a.workers)})
    out = compute(a.workers, a.gt, a.meta, a.horizon)
    out["label"] = a.label
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"H8": out["H8"], "bins": out["bins"], "seconds": out["seconds"]}))
    print("C1 H8 DONE")


if __name__ == "__main__":
    main()
