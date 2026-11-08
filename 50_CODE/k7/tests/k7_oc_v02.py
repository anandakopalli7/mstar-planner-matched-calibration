#!/usr/bin/env python3
"""K7 operating characteristics v02 (Claude line, 1 Nov 2026), for the final K7 design (joint validity family over PD7,
SD1_7 and PD with their pooled cells; power floors on PD7 and SD1_7). Supersedes k7_oc_v01 (two separate families; stopped
after two layouts: A1 0.077 and 0.087 at rho 0.1, kept in 70_TESTS/k7_scratch/k7_oc_v01.log).

OUTCOME-BLIND: the layouts are K6's decision-mode record counts n of M* (the closest proxy for M7's layout) per (scene,
cell), split four ways: near (pair gap <= 5 m) or far, in-path or not. The 'exceed' array is never read. K6's own OC failed
by modelling the layout from development scenes (R10 E2); this uses the observed layout.
For each tracker, scale (1: all 840 scenes; 0.5: a random half of the logs) and intra-scene correlation rho in {0.1, 0.3,
0.5}, REPS datasets are simulated: per scene and cell one rate P ~ Beta(mean p, correlation rho), shared by the four parts of
that cell (records of a scene and cell share their scene effect), and X ~ Binomial(n, P) per part. Each dataset is analysed
with the frozen K6 functions and K7's HK1 rule: one sup-t (0.95, bootstrap B = 500) over the evaluable PD7, SD1_7 and PD
cells and the three pooled cells; the floors (count-only, computed once per layout with the frozen K6 power rule) must have
>= F_MIN cells each.
Reported:
  A1   P(HK1 fails | every cell at p = 0.05)            (acceptance: <= 0.10 in every layout)
  A1b  P(HK1 fails | every cell at p = 0.04)
  P1   P(HK1 fails | the thinnest PD7 family cell at 0.15, the rest at 0.05)
  P2   P(HK1 fails | the largest PD7 cell at 0.08, the rest at 0.05)
  P3   P(HK1 fails | the near-binding records of the thinnest SD1_7 family cell at 0.15, everything else at 0.05)
  P4   P(HK1 fails | the in-path records of the largest PD cell at 0.15, everything else at 0.05)
Usage: python -B k7_oc_v02.py --out <json> [--reps 250]
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
SEED = 20261109
PARTS = {"near_ip": dict(inpath=(1,), gap=(0, 1)), "near_nip": dict(inpath=(0,), gap=(0, 1)),
         "far_ip": dict(inpath=(1,), gap=(2,)), "far_nip": dict(inpath=(0,), gap=(2,))}


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


def pops_of(P):
    """PD7, SD1_7, PD tables from the four parts."""
    return {"PD7": P["near_ip"] + P["near_nip"] + P["far_ip"] + P["far_nip"], "SD1_7": P["near_ip"] + P["near_nip"],
            "PD": P["near_ip"] + P["far_ip"]}


def joint_flag(NP, XP, evs, W, one):
    ests, boots = [], []
    for k in ("PD7", "SD1_7", "PD"):
        N, X, ev = NP[k], XP[k], evs[k]
        if ev.any():
            ests.append(A.rates(N, X, one)[0][ev])
            boots.append(A.rates(N, X, W)[:, ev])
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        ests.append(A.rates(Np, Xp, one)[0])
        boots.append(A.rates(Np, Xp, W))
    est, boot = np.concatenate(ests), np.hstack(boots)
    _, _, _, sig, _ = A.flag(est, boot, np.arange(len(est)), 0.95)
    return bool(sig.any())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=250)
    a = ap.parse_args()
    t0 = time.time()
    log_of_scene = {}
    for p in MANIFESTS:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    cells = A.cell_family()
    masks = {k: A.mask(offset=(0,), steps=A.STEPS_CC, **v) for k, v in PARTS.items()}
    out = {"note": "outcome-blind: only record counts n were read", "reps": a.reps, "layout_arm": "Mstar (K6)", "layouts": {}}
    for i, tag in enumerate(("t1", "t3")):
        eps = [json.loads(l) for l in open(os.path.join(RUNS, "episodes_%s_decide.jsonl" % tag))]
        eps = [o for o in eps if o["entered"] and o["scene"] not in A.DEV_SCENES and o["arm"] == "Mstar"]
        with np.load(os.path.join(RUNS, "counts_%s_decide.npz" % tag)) as z:
            counts = {k: z[k] for k in ("episode", "cell", "n")}
        keys = sorted({(o["scene"], o["delay_kf"]) for o in eps})
        kidx = {k: j for j, k in enumerate(keys)}
        scene_all = np.array([k[0] for k in keys])
        epi = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps}
        parts_all = {k: n_table(counts, epi, len(keys), cells, m) for k, m in masks.items()}
        for scale in (1.0, 0.5):
            rng = np.random.default_rng([SEED, i, int(scale * 10)])
            logs_all = sorted(set(log_of_scene[s] for s in scene_all))
            if scale < 1:
                keep_logs = set(rng.choice(logs_all, size=len(logs_all) // 2, replace=False).tolist())
                keep = np.array([log_of_scene[s] in keep_logs for s in scene_all])
            else:
                keep = np.ones(len(scene_all), bool)
            NPt = {k: v[keep] for k, v in parts_all.items()}
            scene_of_ep = scene_all[keep]
            logs = sorted(set(log_of_scene[s] for s in scene_of_ep))
            log_of_ep = np.array([logs.index(log_of_scene[s]) for s in scene_of_ep])
            W = rng.multinomial(len(logs), np.full(len(logs), 1.0 / len(logs)), size=500).astype(float)[:, log_of_ep]
            one = np.ones((1, len(scene_of_ep)))
            NP = pops_of(NPt)
            evs = {k: A.evaluable(v, scene_of_ep, log_of_ep) for k, v in NP.items()}
            fams = {}
            for k_, k in enumerate(("PD7", "SD1_7")):
                pw, _ = A.power_family(NP[k], evs[k], scene_of_ep, W, np.random.default_rng([A.POWER_SEED, i, k_]))
                fams[k] = np.flatnonzero(evs[k] & (pw >= A.POWER_MIN))
            floors_met = all(len(v) >= A.F_MIN for v in fams.values())
            rec7, recs, recp = NP["PD7"].sum(0), NP["SD1_7"].sum(0), NP["PD"].sum(0)
            thin7 = int(fams["PD7"][np.argmin(rec7[fams["PD7"]])]) if len(fams["PD7"]) else None
            big7 = int(np.flatnonzero(evs["PD7"])[np.argmax(rec7[evs["PD7"]])])
            thins = int(fams["SD1_7"][np.argmin(recs[fams["SD1_7"]])]) if len(fams["SD1_7"]) else None
            bigp = int(np.flatnonzero(evs["PD"])[np.argmax(recp[evs["PD"]])]) if evs["PD"].any() else None
            for rho in (0.1, 0.3, 0.5):
                res = {}
                scen = {"A1_p05": {}, "A1b_p04": {"all": 0.04}, "P1_thin_PD7_at_015": {"cell_all": thin7},
                        "P2_big_PD7_at_008": {"cell_all_008": big7}, "P3_thin_SD1_7_near_at_015": {"cell_near": thins},
                        "P4_big_PD_inpath_at_015": {"cell_ip": bigp}}
                for name, spec in scen.items():
                    base = spec.get("all", 0.05)
                    fails = 0
                    for _ in range(a.reps):
                        pc = np.full((len(scene_of_ep), len(cells)), base)
                        aa = pc * (1 - rho) / rho
                        bb = (1 - pc) * (1 - rho) / rho
                        P05 = rng.beta(aa, bb)
                        Pp = {k: P05 for k in PARTS}
                        alt = None
                        if spec.get("cell_all") is not None:
                            alt, parts_hit, p_alt = spec["cell_all"], tuple(PARTS), 0.15
                        elif spec.get("cell_all_008") is not None:
                            alt, parts_hit, p_alt = spec["cell_all_008"], tuple(PARTS), 0.08
                        elif spec.get("cell_near") is not None:
                            alt, parts_hit, p_alt = spec["cell_near"], ("near_ip", "near_nip"), 0.15
                        elif spec.get("cell_ip") is not None:
                            alt, parts_hit, p_alt = spec["cell_ip"], ("near_ip", "far_ip"), 0.15
                        if alt is not None:
                            Palt = P05.copy()
                            Palt[:, alt] = rng.beta(p_alt * (1 - rho) / rho, (1 - p_alt) * (1 - rho) / rho, size=len(scene_of_ep))
                            Pp = {k: (Palt if k in parts_hit else P05) for k in PARTS}
                        XPt = {k: rng.binomial(NPt[k].astype(int), Pp[k]).astype(float) for k in PARTS}
                        XP = pops_of(XPt)
                        fails += (not floors_met) or joint_flag(NP, XP, evs, W, one)
                    res[name] = fails / a.reps
                key = "%s|scale%.1f|rho%.1f" % (tag, scale, rho)
                res.update({"evaluable": {k: int(v.sum()) for k, v in evs.items()}, "floors": {k: int(len(v)) for k, v in fams.items()},
                            "joint_family_cells": int(sum(v.sum() for v in evs.values()) + 3),
                            "thin_PD7": cells[thin7][0] if thin7 is not None else None, "big_PD7": cells[big7][0],
                            "thin_SD1_7": cells[thins][0] if thins is not None else None, "big_PD": cells[bigp][0] if bigp is not None else None,
                            "scenes": int(len(scene_of_ep))})
                out["layouts"][key] = res
                print(key, json.dumps(res), "%.0f s" % (time.time() - t0), flush=True)
    a1 = [v["A1_p05"] for v in out["layouts"].values()]
    out["acceptance"] = {"A1_max": max(a1), "A1_le_0.10_all": bool(max(a1) <= 0.10),
                         "floors_ge_F_MIN_all": bool(all(min(v["floors"].values()) >= A.F_MIN for v in out["layouts"].values()))}
    out["acceptance_all"] = bool(out["acceptance"]["A1_le_0.10_all"] and out["acceptance"]["floors_ge_F_MIN_all"])
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["acceptance"]))
    print("K7 OC V02 DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
