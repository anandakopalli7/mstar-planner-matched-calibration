#!/usr/bin/env python3
"""K7 design counts (Claude line, v01, 1 Nov 2026). OUTCOME-BLIND sizing of the K7 cell family from the K6 decision-mode
record counts. Only the record counts n are read: the 'exceed' array of the counts files is never loaded.

For each tracker, arm and population it reports, per cell (group x axis x motion, pooled over range): records, scenes, logs,
evaluability (>= 39 scenes, >= 8 logs), and, for the margin arms, the frozen K6 power rule (k6_analyse_v02.power_family:
power to be flagged at a true scene-level rate of 0.15, beta-binomial with intra-scene correlation 0.5, 200 datasets) on the
arm's own counts. Populations:
  PD      the K6 primary population (the method's in-path flag)
  PD7     the same without the in-path restriction (every relied-on, enforced, satisfied record at offset 0, steps 0.5-2 s)
  NIP     PD7 minus PD (not in the method's in-path population)
The K6 power seeds reproduce K6's family sizes on PD (a check); 10 more seeds show the Monte Carlo spread.
Usage: python -B k7_design_counts_v01.py --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
import k6_analyse_v02 as A  # noqa: E402

RUNS = os.path.join(W_ROOT, "60_RESULTS", "k6_main_v02")
MANIFESTS = [os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_t1_%s" % s, "MANIFEST.json") for s in ("train", "val")]
POPS = {"PD": dict(offset=(0,), gap=(0, 1, 2), steps=A.STEPS_CC),
        "PD7": dict(offset=(0,), inpath=(0, 1), gap=(0, 1, 2), steps=A.STEPS_CC),
        "NIP": dict(offset=(0,), inpath=(0,), gap=(0, 1, 2), steps=A.STEPS_CC)}
ARMS = ("Mstar", "B6", "B0", "B1", "B4", "B9")


def n_table(counts, ep_index, n_ep, cells, pop):
    l0_to_cell = np.full(A.S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    ep, cell, n = counts["episode"], counts["cell"], counts["n"]
    sel = pop[cell] & np.isin(ep, list(ep_index))
    ep, cell, n = ep[sel], cell[sel], n[sel]
    col = l0_to_cell[cell % A.S.N_L0]
    ok = col >= 0
    row = np.array([ep_index[e] for e in ep[ok]], int)
    N = np.zeros((n_ep, len(cells)))
    np.add.at(N, (row, col[ok]), n[ok])
    return N


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    log_of_scene = {}
    for p in MANIFESTS:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    cells = A.cell_family()
    out = {"note": "outcome-blind: only record counts n were read", "trackers": {}}
    for i, tag in enumerate(("t1", "t3")):
        eps = [json.loads(l) for l in open(os.path.join(RUNS, "episodes_%s_decide.jsonl" % tag))]
        eps = [o for o in eps if o["entered"] and o["scene"] not in A.DEV_SCENES and o["arm"] != "LOG"]
        with np.load(os.path.join(RUNS, "counts_%s_decide.npz" % tag)) as z:
            counts = {k: z[k] for k in ("episode", "cell", "n")}
        keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps, log_of_scene, A.B_BOOT, np.random.default_rng([A.SEED, i, 0]))
        W = W_logs[:, log_of_ep]
        kidx = {k: j for j, k in enumerate(keys)}
        res = {}
        for pname, spec in POPS.items():
            pop = A.mask(**spec)
            res[pname] = {}
            for arm in ARMS:
                epi = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps if o["arm"] == arm}
                N = n_table(counts, epi, len(keys), cells, pop)
                ev = A.evaluable(N, scene_of_ep, log_of_ep)
                r = {"cells": {}}
                for j, (name, _) in enumerate(cells):
                    pres = N[:, j] > 0
                    r["cells"][name] = {"records": int(N[:, j].sum()), "scenes": int(len(set(scene_of_ep[pres]))),
                                        "logs": int(len(set(log_of_ep[pres]))), "evaluable": bool(ev[j])}
                r["pooled"] = {"records": int(N.sum()), "scenes": int((N.sum(1) > 0).sum())}
                if arm in ("Mstar", "B6"):
                    pw, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng([A.POWER_SEED, i]))
                    for j, (name, _) in enumerate(cells):
                        if ev[j]:
                            r["cells"][name]["power"] = float(pw[j])
                    r["family_frozen_seed"] = [cells[j][0] for j in np.flatnonzero(ev & (pw >= A.POWER_MIN))]
                    sizes = []
                    for s in range(10):
                        pw2, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng([A.POWER_SEED + 1000 + s, i]))
                        sizes.append(int((ev & (pw2 >= A.POWER_MIN)).sum()))
                    r["family_sizes_10_other_seeds"] = sizes
                r["evaluable_cells"] = int(ev.sum())
                res[pname][arm] = r
                print(tag, pname, arm, "evaluable", int(ev.sum()), "family", len(r.get("family_frozen_seed", [])),
                      r.get("family_sizes_10_other_seeds", ""), flush=True)
        out["trackers"][tag] = res
    json.dump(out, open(a.out, "w"), indent=1)
    print("K7 DESIGN COUNTS DONE")


if __name__ == "__main__":
    main()
