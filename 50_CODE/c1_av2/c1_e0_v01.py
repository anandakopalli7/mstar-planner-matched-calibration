#!/usr/bin/env python3
"""C1 E0 for H8 (Claude line, c1_e0_v01, 4 Nov 2026). D16 v11 Choice 31 and its addendum; X1_PREREGISTRATION_v02 section 6.
E0_g is X1's orientation null, unchanged (x1_lib_v03.orientation_null): the plug-in, fixed-truth exceedance at the estimated
geometry, over all in-path paired (record, axis) candidates BEFORE the separating filter; 20 draws per item, e ~ N(0, Sigma_hat +
sigma_a^2 I); U0 = sign . a'(-e) / sqrt(a' Sigma_hat a + sigma_a^2); E0 = P(U0 > z_0.95 | kept). sigma_a = 0.10 m is H8's (X1's
primary); 0.20 m is reported. H8 uses the 2 s family (h2s) and the two lateral in-path car cells (< 20 m, 20-40 m).
Outcome-free (Choice 13): rows at k come from x1_lib_v03.build_table (pairing at k with the annotation at k); the 2 s rows come
from horizon_rows_stageA, a copy of x1_lib_v03.build_horizon_rows that reads NO ground-truth position after k: at the target sweep
only the paired instance's existence and num_pts (the visibility condition) are read; gx, gy are NaN; the bicycle-rack test at the
horizon (which needs the future position; it only concerns bicycles and motorcycles) is not applied. E0 never uses D.
Draws (addendum): mode "c1" gives every (cell, sigma) its own generator default_rng([seed, cell index in x1_lib_v03.CELLS, sigma
index]) with seed 20261114, so the value of a cell depends only on its own items, in their input order, and the post-freeze
recompute is bit-exact. Mode "x1" reproduces X1's sizes file (x1_prefreeze_v02.sizes): one generator default_rng(x1_lib_v03.SEED),
consumed for t0 (sigma 0.10, 0.20) then h2s (0.10, 0.20), cells in CELLS order.
Usage: python -B c1_e0_v01.py --workers <x1 export dirs> --gt <gt json> --meta <dir with scene.json> --horizon <jsonl.gz> --out <json>
       [--mode c1|x1] [--seed 20261114]
"""
import argparse
import hashlib
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "x1"))
import x1_lib_v03 as L  # noqa: E402

SEED = 20261114
SIGMAS = (0.10, 0.20)
PRIMARY_SIGMA = 0.10
DECISION_CELLS = ("car|<20|lat", "car|20-40|lat")


def visibility(gtb):
    """{sample token: {instance token: num_pts}}: the only target-sweep fields used (no position)."""
    return {tok: {a["instance_token"]: a["num_pts"] for a in anns} for tok, anns in gtb.items()}


def horizon_rows_stageA(rows, pred, samples, vis, key="h2s", steps=4):
    """x1_lib_v03.build_horizon_rows without any ground-truth position at k + steps (see the module docstring)."""
    scene_tokens = defaultdict(dict)
    for s in samples.values():
        scene_tokens[s["scene"]][s["index"]] = s
    out, st = [], defaultdict(int)
    for r in rows:
        h = dict(r)
        p = pred.get((r["scene"], r["k"], r["tid"]))
        fut = scene_tokens[r["scene"]].get(r["k"] + steps)
        if p is None or fut is None:
            st["no_future_frame"] += 1
            continue
        x, y, sxx, sxy, syy = p[key]
        now, prev = scene_tokens[r["scene"]][r["k"]], scene_tokens[r["scene"]][r["k"] - 1]
        dt = 1e-6 * (now["timestamp"] - prev["timestamp"])
        ex, ey, eyaw = now["ego_xyz"][0], now["ego_xyz"][1], now["ego_yaw"]
        v = ((ex - prev["ego_xyz"][0]) * math.cos(eyaw) + (ey - prev["ego_xyz"][1]) * math.sin(eyaw)) / dt
        w = L.wrap(eyaw - prev["ego_yaw"]) / dt
        th = steps * 0.5
        if abs(w) < 1e-4:
            px, py, pyaw = ex + v * th * math.cos(eyaw), ey + v * th * math.sin(eyaw), eyaw
        else:
            pyaw = eyaw + w * th
            px, py = ex + v / w * (math.sin(pyaw) - math.sin(eyaw)), ey - v / w * (math.cos(pyaw) - math.cos(eyaw))
        cx, cy = L.ego_centre(px, py, pyaw)
        h.update({"mx": x, "my": y, "S": (sxx, sxy, syy), "cx": cx, "cy": cy, "eyaw": pyaw,
                  "range": L.range_bin(math.hypot(x - cx, y - cy)), "c6": None})
        if r["paired"]:
            n_pts = vis.get(fut["token"], {}).get(r["inst"])
            if n_pts is None or n_pts < 1:
                h["paired"] = False
                st["censored_at_horizon"] += 1
            else:
                h["gx"], h["gy"], h["resid_gt_gate"] = float("nan"), float("nan"), False
        out.append(h)
    return out, dict(st)


def load_rows(workers, gt, meta, horizon):
    recs = []
    for w in workers:
        recs += L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
    samples, gtb, racks = L.load_gt(gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    rows, st = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    vis = visibility(gtb)
    del recs, gtb
    hr, hst = horizon_rows_stageA(rows, L.load_horizon(horizon, {(r["scene"], r["k"], r["tid"]) for r in rows}), samples, vis)
    return rows, hr, {"pairing": st, "horizon": hst}


def e0_table(fams, mode="c1", seed=SEED):
    out = {}
    shared = np.random.default_rng(L.SEED) if mode == "x1" else None
    for fam, frows in fams.items():
        out[fam] = {}
        for si, sa in enumerate(SIGMAS):
            cells, _, _ = L.cell_items(frows, sigma_a=sa)
            if mode == "x1":
                null = L.orientation_null(cells, shared)
            else:
                null = {c: L.orientation_null({c: cells[c]}, np.random.default_rng([seed, ci, si]))[c] for ci, c in enumerate(L.CELLS)}
            out[fam]["%.2f" % sa] = {"|".join(c): {"E0": null[c][0], "m0": null[c][1], "items_before_filter": int(len(cells[c]["all"]["var"])) if cells[c]["all"] else 0}
                                     for c in L.CELLS}
    return out


def compute(workers, gt, meta, horizon, mode="c1", seed=SEED):
    rows, hr, info = load_rows(workers, gt, meta, horizon)
    fams = {"t0": rows, "h2s": hr} if mode == "x1" else {"h2s": hr}
    tab = e0_table(fams, mode, seed)
    return {"rule": "X1 v02 section 6 orientation null (x1_lib_v03.orientation_null), stage-A rows (no GT position after k)",
            "mode": mode, "seed": seed if mode == "c1" else L.SEED, "n_draw": L.N_NULL, "sigmas": list(SIGMAS), "primary_sigma": PRIMARY_SIGMA,
            "decision_cells": list(DECISION_CELLS), "E0": tab,
            "H8_E0_primary": {c: tab["h2s"]["%.2f" % PRIMARY_SIGMA][c]["E0"] for c in DECISION_CELLS}, "info": info}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["c1", "x1"], default="c1")
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_e0_v01", "c1_e0_v03", {"exports": LEGACY.ds_exports(a.workers)})
    out = compute(a.workers, a.gt, a.meta, a.horizon, a.mode, a.seed)
    out["inputs_sha256"] = {"export": [L.sha256_path(os.path.join(w, "x1_tracks.jsonl.gz")) for w in a.workers], "gt": L.sha256_path(a.gt),
                            "horizon": L.sha256_path(a.horizon)}
    out["code_sha256"] = hashlib.sha256(open(os.path.abspath(__file__), "rb").read()).hexdigest()
    with open(a.out, "w") as f:
        json.dump(out, f, indent=1, default=float)
    print(json.dumps({"H8_E0_primary": out["H8_E0_primary"], "seed": out["seed"]}))
    print("C1 E0 DONE")


if __name__ == "__main__":
    main()
