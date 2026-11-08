#!/usr/bin/env python3
"""K7 operating characteristics (Claude line, v01, 1 Nov 2026). OUTCOME-BLIND: the layouts are the K6 decision-mode record
counts n per (scene, cell) of an arm, split into in-path (PD) and not-in-path (NIP) records; the 'exceed' array is never
read. K6's OC failed because its layout was modelled from development scenes; K7's is the observed layout (R10 E2).

For each tracker, layout arm (Mstar: K6's M*, the closest proxy for M7's layout; B6 as a second proxy), correlation
rho in {0.1, 0.3, 0.5} and scale (1: all 840 scenes; 0.5: a random half of the logs), 300 datasets are simulated: per scene
and cell a rate P ~ Beta with mean p and intra-scene correlation rho, shared by the scene's in-path and not-in-path records
of that cell, and X ~ Binomial(n, P). Each dataset is analysed with the frozen K6 functions and K7's HK1 rule:
  flags in the sup-t over the evaluable PD7 cells and over the evaluable PD cells (0.95 each), the pooled PD7 and pooled
  PD cells (0.95 each), and the power-qualified family size (count-only, computed once per layout with the frozen rule).
Reported:
  A1  P(HK1 fails | every cell at p = 0.05)         -- the false NO-GO rate at the validity boundary (acceptance <= 0.10)
  A1' P(HK1 fails | every cell at p = 0.04)
  P1  P(HK1 fails | the smallest family cell at 0.15, the rest at 0.05)   -- power against one invalid cell
  P2  P(HK1 fails | the largest PD7 cell at 0.08, the rest at 0.05)       -- power against a mild excess in a big cell
Bootstrap B = 500 per dataset (the confirmatory analysis uses 2000).
Usage: python -B k7_oc_v01.py --out <json> [--reps 300]
"""
import argparse
import json
import os
import sys
import time

import numpy as np

K7 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K7))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
import k6_analyse_v02 as A  # noqa: E402

RUNS = os.path.join(W_ROOT, "60_RESULTS", "k6_main_v02")
MANIFESTS = [os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_t1_%s" % s, "MANIFEST.json") for s in ("train", "val")]
SEED = 20261108


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


def flagged(N, X, fam, W):
    if not len(fam):
        return False
    est = A.rates(N, X, np.ones((1, N.shape[0])))[0]
    boot = A.rates(N, X, W)
    _, _, _, sig, _ = A.flag(est, boot, fam, 0.95)
    return bool(sig.any())


def hk1_fails(Np, Nn, Xp, Xn, ev7, evp, W):
    N7, X7 = Np + Nn, Xp + Xn
    return (flagged(N7, X7, np.flatnonzero(ev7), W) or flagged(Np, Xp, np.flatnonzero(evp), W)
            or flagged(N7.sum(1, keepdims=True), X7.sum(1, keepdims=True), np.array([0]), W)
            or flagged(Np.sum(1, keepdims=True), Xp.sum(1, keepdims=True), np.array([0]), W))


def simulate(Np, Nn, p_cell, rho, rng):
    a = p_cell * (1 - rho) / rho
    b = (1 - p_cell) * (1 - rho) / rho
    P = rng.beta(np.broadcast_to(a, Np.shape), np.broadcast_to(b, Np.shape))
    return rng.binomial(Np.astype(int), P).astype(float), rng.binomial(Nn.astype(int), P).astype(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=300)
    a = ap.parse_args()
    t0 = time.time()
    log_of_scene = {}
    for p in MANIFESTS:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    cells = A.cell_family()
    pop_p = A.mask(offset=(0,), inpath=(1,), gap=(0, 1, 2), steps=A.STEPS_CC)
    pop_n = A.mask(offset=(0,), inpath=(0,), gap=(0, 1, 2), steps=A.STEPS_CC)
    out = {"note": "outcome-blind: only record counts n were read", "reps": a.reps, "layouts": {}}
    for i, tag in enumerate(("t1", "t3")):
        eps = [json.loads(l) for l in open(os.path.join(RUNS, "episodes_%s_decide.jsonl" % tag))]
        eps = [o for o in eps if o["entered"] and o["scene"] not in A.DEV_SCENES and o["arm"] != "LOG"]
        with np.load(os.path.join(RUNS, "counts_%s_decide.npz" % tag)) as z:
            counts = {k: z[k] for k in ("episode", "cell", "n")}
        keys = sorted({(o["scene"], o["delay_kf"]) for o in eps})
        kidx = {k: j for j, k in enumerate(keys)}
        scene_all = np.array([k[0] for k in keys])
        for arm in ("Mstar", "B6"):
            epi = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps if o["arm"] == arm}
            Np_all = n_table(counts, epi, len(keys), cells, pop_p)
            Nn_all = n_table(counts, epi, len(keys), cells, pop_n)
            for scale in (1.0, 0.5):
                rng = np.random.default_rng([SEED, i, int(scale * 10), 0 if arm == "Mstar" else 1])
                logs_all = sorted(set(log_of_scene[s] for s in scene_all))
                if scale < 1:
                    keep_logs = set(rng.choice(logs_all, size=len(logs_all) // 2, replace=False).tolist())
                    keep = np.array([log_of_scene[s] in keep_logs for s in scene_all])
                else:
                    keep = np.ones(len(scene_all), bool)
                Np, Nn, scene_of_ep = Np_all[keep], Nn_all[keep], scene_all[keep]
                logs = sorted(set(log_of_scene[s] for s in scene_of_ep))
                log_of_ep = np.array([logs.index(log_of_scene[s]) for s in scene_of_ep])
                W_logs = rng.multinomial(len(logs), np.full(len(logs), 1.0 / len(logs)), size=500).astype(float)
                W = W_logs[:, log_of_ep]
                ev7 = A.evaluable(Np + Nn, scene_of_ep, log_of_ep)
                evp = A.evaluable(Np, scene_of_ep, log_of_ep)
                pw, _ = A.power_family(Np + Nn, ev7, scene_of_ep, W, np.random.default_rng([A.POWER_SEED, i]))
                fam = np.flatnonzero(ev7 & (pw >= A.POWER_MIN))
                rec7 = (Np + Nn).sum(0)
                thin = int(fam[np.argmin(rec7[fam])]) if len(fam) else None
                big = int(np.flatnonzero(ev7)[np.argmax(rec7[ev7])]) if ev7.any() else None
                for rho in (0.1, 0.3, 0.5):
                    res = {}
                    for name, pc in (("A1_p05", None), ("A1_p04", 0.04), ("P1_thin_at_015", thin), ("P2_big_at_008", big)):
                        p_cell = np.full(len(cells), 0.05)
                        if name == "A1_p04":
                            p_cell[:] = 0.04
                        elif name == "P1_thin_at_015" and thin is not None:
                            p_cell[thin] = 0.15
                        elif name == "P2_big_at_008" and big is not None:
                            p_cell[big] = 0.08
                        fails = 0
                        for _ in range(a.reps):
                            Xp, Xn = simulate(Np, Nn, p_cell[None, :], rho, rng)
                            fails += hk1_fails(Np, Nn, Xp, Xn, ev7, evp, W)
                        res[name] = fails / a.reps
                    key = "%s|%s|scale%.1f|rho%.1f" % (tag, arm, scale, rho)
                    res.update({"evaluable_PD7": int(ev7.sum()), "evaluable_PD": int(evp.sum()), "family": int(len(fam)),
                                "thin_cell": cells[thin][0] if thin is not None else None, "big_cell": cells[big][0] if big is not None else None,
                                "scenes": int(len(scene_of_ep))})
                    out["layouts"][key] = res
                    print(key, json.dumps(res), "%.0f s" % (time.time() - t0), flush=True)
    a1 = [v["A1_p05"] for v in out["layouts"].values()]
    out["acceptance"] = {"A1_max": max(a1), "A1_le_0.10_all": bool(max(a1) <= 0.10),
                         "family_ge_F_MIN_all": bool(all(v["family"] >= A.F_MIN for v in out["layouts"].values()))}
    out["acceptance_all"] = bool(out["acceptance"]["A1_le_0.10_all"] and out["acceptance"]["family_ge_F_MIN_all"])
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["acceptance"]))
    print("K7 OC DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
