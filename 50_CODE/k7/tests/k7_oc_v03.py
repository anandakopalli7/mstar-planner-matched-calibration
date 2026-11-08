#!/usr/bin/env python3
"""K7 operating characteristics v03 (Claude line, 1 Nov 2026), after review R12 (M2): the OC calls the analysis' own HK1
function (k7_analyse_v02.hk1_rule), so it simulates exactly the coded rule: K6's tests on each of PD7, SD1_7 and PD (no
flag in the all-evaluable sup-t, pooled cell not flagged pointwise), the PD7 and SD1_7 power floors with their own-family
sup-t, and >= 1 evaluable PD cell. Supersedes k7_oc_v01 and v02 (which simulated earlier rules).

OUTCOME-BLIND: the layout is K6's decision-mode record counts n of M* per (scene, cell), split four ways (near = pair gap
<= 5 m or far; in-path or not). The 'exceed' array is never read. The power-qualified families depend on n only and are
computed once per layout with the frozen K6 rule (the confirmatory power seeds).
Simulation: per scene and cell, the parts whose rate is the same share ONE draw P ~ Beta(mean p, intra-scene correlation rho)
(records of a scene and cell share their scene effect); parts whose rate an alternative changes share one draw of their own,
independent of the unchanged parts' draw (a slight weakening of the within-cell correlation across parts, stated here);
X ~ Binomial(n, P). (A first version drew comonotone Beta quantiles with scipy and was stopped before any output: too slow.)
Bootstrap B = 500 log-cluster weights per layout. 200 datasets per alternative.
Alternatives (the rest at 0.05): A1 every cell 0.05; A1b every cell 0.04; U057 / U060 every record 0.057 / 0.060; IP07 every
in-path record 0.07; NIP12 every near-binding in-path record 0.12; MED07 the median PD7 family cell 0.07; PED07 the largest
pedestrian PD7 cell 0.07; IPMED15 the in-path records of the median evaluable PD cell 0.15; IPCLT15 the in-path records of
car|lat|turning 0.15; THIN15 the thinnest PD7 family cell 0.15; SDTHIN15 the near-binding records of the thinnest SD1_7
family cell 0.15.
Acceptance (declared before this file was run):
  size         A1 <= 0.15 and A1b <= 0.05 in every layout (K6's tests on three populations raise the false-NO-GO rate at the
               exact boundary above K6's 0.10; R12 C2 / its table: 0.08-0.14. This only makes a GO harder.)
  informative  at scale 1 and rho 0.3, on both trackers: P(HK1 fails) >= 0.80 under U060, IP07 and NIP12
  floors       both floors >= F_MIN in every layout
HK3: a normal approximation from the development per-scene paired differences (10 scenes, k7_dev_check runs), with
design effects 1, 2 and 3.5 on the 840-scene standard error, at level 1 - 0.05/4 (reported, not an acceptance criterion).
Usage: python -B k7_oc_v03.py --out <json> [--reps 200]
"""
import argparse
import collections
import json
import os
import sys
import time

import numpy as np
from scipy.stats import norm

K7 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K7))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, K7)
import k6_analyse_v02 as A  # noqa: E402
import k7_analyse_v02 as K  # noqa: E402

RUNS = os.path.join(W_ROOT, "60_RESULTS", "k6_main_v02")
DEVRUNS = os.path.join(W_ROOT, "70_TESTS", "k7_scratch", "dev_v01")
MANIFESTS = [os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_t1_%s" % s, "MANIFEST.json") for s in ("train", "val")]
SEED = 20261110
PARTS = {"near_ip": dict(inpath=(1,), gap=(0, 1)), "near_nip": dict(inpath=(0,), gap=(0, 1)),
         "far_ip": dict(inpath=(1,), gap=(2,)), "far_nip": dict(inpath=(0,), gap=(2,))}
IP_PARTS, NEAR_PARTS = ("near_ip", "far_ip"), ("near_ip", "near_nip")


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
    return {"PD7_primary": P["near_ip"] + P["near_nip"] + P["far_ip"] + P["far_nip"], "SD1_7_gap_le_5m": P["near_ip"] + P["near_nip"],
            "PD_inpath": P["near_ip"] + P["far_ip"]}


def hk3_power():
    out = {}
    z = norm.ppf(1 - 0.05 / 4)
    for t in ("t1", "t3"):
        r = collections.defaultdict(dict)
        for l in open(os.path.join(DEVRUNS, "episodes_%s_decide.jsonl" % t)):
            o = json.loads(l)
            r[o["arm"]][o["scene"]] = o["infeasible_frames"] / max(o["frames"], 1)
        sc = sorted(r["Mstar"])
        for b in ("B0", "B1", "B4", "B9"):
            d = np.array([r["Mstar"][s] - r[b][s] for s in sc])
            row = {"dev_mean_diff": float(d.mean()), "dev_sd": float(d.std(ddof=1)), "dev_scenes_M7_worse": int((d > 0).sum())}
            for deff in (1.0, 2.0, 3.5):
                se = d.std(ddof=1) / np.sqrt(840) * deff
                row["power_deff_%.1f" % deff] = float(norm.cdf((-d.mean() - z * se) / se))
            out["%s|%s" % (t, b)] = row
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=200)
    a = ap.parse_args()
    t0 = time.time()
    log_of_scene = {}
    for p in MANIFESTS:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    cells = A.cell_family()
    cname = [c[0] for c in cells]
    masks = {k: A.mask(offset=(0,), steps=A.STEPS_CC, **v) for k, v in PARTS.items()}
    out = {"note": "outcome-blind: only record counts n were read", "reps": a.reps, "rule": "k7_analyse_v02.hk1_rule", "layouts": {}}
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
            NP = pops_of(NPt)
            evs = {k: A.evaluable(v, scene_of_ep, log_of_ep) for k, v in NP.items()}
            fams = {}
            for k_, p in enumerate(K.CONF_POPS):
                pw, _ = A.power_family(NP[p], evs[p], scene_of_ep, W, np.random.default_rng([K.POWER_SEED, i, k_]))
                fams[p] = evs[p] & (pw >= A.POWER_MIN)
            rec7, recs, recp = NP["PD7_primary"].sum(0), NP["SD1_7_gap_le_5m"].sum(0), NP["PD_inpath"].sum(0)
            f7, fs = np.flatnonzero(fams["PD7_primary"]), np.flatnonzero(fams["SD1_7_gap_le_5m"])
            evp = np.flatnonzero(evs["PD_inpath"])
            thin7 = int(f7[np.argmin(rec7[f7])])
            med7 = int(f7[np.argsort(rec7[f7])[len(f7) // 2]])
            thins = int(fs[np.argmin(recs[fs])])
            ped = [j for j in np.flatnonzero(evs["PD7_primary"]) if cname[j].startswith("pedestrian")]
            ped7 = int(ped[np.argmax(rec7[ped])])
            medp = int(evp[np.argsort(recp[evp])[len(evp) // 2]]) if len(evp) else None
            clt = cname.index("car|lat|turning")
            alts = {"A1": [], "A1b": [("all", None, 0.04)], "U057": [("all", None, 0.057)], "U060": [("all", None, 0.060)],
                    "IP07": [(IP_PARTS, None, 0.07)], "NIP12": [(("near_ip",), None, 0.12)], "MED07": [("all", med7, 0.07)],
                    "PED07": [("all", ped7, 0.07)], "IPMED15": [(IP_PARTS, medp, 0.15)] if medp is not None else None,
                    "IPCLT15": [(IP_PARTS, clt, 0.15)], "THIN15": [("all", thin7, 0.15)], "SDTHIN15": [(NEAR_PARTS, thins, 0.15)]}
            for rho in (0.1, 0.3, 0.5):
                res = {}
                for name, spec in alts.items():
                    if spec is None:
                        res[name] = None
                        continue
                    means = {k: np.full(len(cells), 0.05) for k in PARTS}
                    for parts, cell, p_ in spec:
                        for k in (tuple(PARTS) if parts == "all" else parts):
                            if cell is None:
                                means[k][:] = p_
                            else:
                                means[k][cell] = p_
                    groups = {}
                    for k in PARTS:
                        groups.setdefault(tuple(np.round(means[k], 6)), []).append(k)
                    fails = 0
                    for _ in range(a.reps):
                        Pk = {}
                        for mvec, ks in groups.items():
                            m = np.broadcast_to(np.array(mvec)[None, :], (len(scene_of_ep), len(cells)))
                            Pg = rng.beta(m * (1 - rho) / rho, (1 - m) * (1 - rho) / rho)
                            for k in ks:
                                Pk[k] = Pg
                        XPt = {k: rng.binomial(NPt[k].astype(int), Pk[k]).astype(float) for k in PARTS}
                        XP = pops_of(XPt)
                        T = {p: (NP[p], XP[p]) for p in K.CONF_POPS}
                        fails += not K.hk1_rule(T, cells, scene_of_ep, log_of_ep, W, None, fams=fams)["HK1"]
                    res[name] = fails / a.reps
                key = "%s|scale%.1f|rho%.1f" % (tag, scale, rho)
                res.update({"evaluable": {p: int(v.sum()) for p, v in evs.items()}, "families": {p: int(v.sum()) for p, v in fams.items()},
                            "cells": {"thin_PD7": cname[thin7], "median_PD7_family": cname[med7], "thin_SD1_7": cname[thins],
                                      "largest_pedestrian_PD7": cname[ped7], "median_PD": cname[medp] if medp is not None else None},
                            "scenes": int(len(scene_of_ep))})
                out["layouts"][key] = res
                print(key, json.dumps(res), "%.0f s" % (time.time() - t0), flush=True)
    L = out["layouts"]
    size_ok = all(v["A1"] <= 0.15 and v["A1b"] <= 0.05 for v in L.values())
    inf_ok = all(L["%s|scale1.0|rho0.3" % t][k] >= 0.80 for t in ("t1", "t3") for k in ("U060", "IP07", "NIP12"))
    floors_ok = all(v["families"]["PD7_primary"] >= A.F_MIN and v["families"]["SD1_7_gap_le_5m"] >= A.F_MIN for v in L.values())
    out["acceptance"] = {"A1_max": max(v["A1"] for v in L.values()), "A1b_max": max(v["A1b"] for v in L.values()),
                         "size_ok": size_ok, "informative_ok": inf_ok, "floors_ok": floors_ok}
    out["acceptance_all"] = bool(size_ok and inf_ok and floors_ok)
    out["HK3_power_normal_approx_from_development"] = hk3_power()
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["acceptance"]))
    print(json.dumps(out["HK3_power_normal_approx_from_development"], indent=1))
    print("K7 OC V03 DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
