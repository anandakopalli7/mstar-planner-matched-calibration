#!/usr/bin/env python3
"""c1crit_power2_v01 (5 Nov 2026): the lead's items 3 and 4 (C1_CRITERIA_EVIDENCE_REVIEW_v01 section 6) on the nuScenes K8
development counts only (T1, T3; 840 scenes; M*'s record counts per scene and cell). No AV2 file is read.

Item 3, M*'s power-qualified family under:
  W    (weights) 2000 datasets, all cells planted at 0.15, rho 0.5, with the first 500 K8 bootstrap weights (the rule) and with all
       2000. Power seed = the K8 rule's [20261107, i, k], so the 500-weight run must equal c1crit_mc_v01's P2000 for M* exactly
       (asserted when that checkpoint exists): this run calls k6_analyse_v02.power_family itself.
  G    (grid) planting in {all, target}, rho in --rhos, effect P in --ps, 1000 datasets, 500 weights. 'all' calls
       k6_analyse_v02.power_family. 'target' (individual power, Senn and Bretz 2007) is power_target below: per dataset, every
       cell is drawn at M*'s own development estimate (beta-binomial with the same rho; a cell with estimate 0 stays 0), then
       for each evaluable cell j in turn only cell j is redrawn at P, and the cell is counted if it is flagged in the
       all-evaluable one-sided sup-t at 0.95 (m_lib_v04._simul, the rule's flag). A self-check runs power_target with every
       base rate equal to P against power_family (they must agree within Monte Carlo error).
     Seeds: default_rng([20261209, i, k, s]), k the population index (PD7 0, SD1_7 1, PD 2) and
     s = 1000 round(1000 rho) + 10 round(1000 P) + (0 all, 1 target) (recorded in each checkpoint).
Item 4: per population, M*'s per-cell record counts, and the share of the population's records covered by each family; the
summary computes the share covered by the k most powerful cells, k = 5..20.
Checkpoint: one JSON per (tracker, part, setting) in power2_ckpt/.
Usage: python -B c1crit_power2_v01.py [--parts W,G,CHK] [--rhos 0.3,0.5,0.7] [--ps 0.10,0.12,0.15] [--pops PD7,SD1_7,PD]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A = C.A
M = A.M
CKPT = os.path.join(C.OUT, "power2_ckpt")
SEED = 20261209
K_OF = {"PD7": 0, "SD1_7": 1, "PD": 2}
INV = {v: k for k, v in C.LAB.items()}


def power_target(N, X, ev, W, rng, P, rho, reps):
    """Individual power: other cells at M*'s development estimates, the target cell at P (see the module docstring)."""
    fam = np.flatnonzero(ev)
    S, J = N.shape
    one = np.ones((1, S))
    base = A.rates(N, X, one)[0]
    base = np.where(np.isfinite(base), base, 0.0)
    th = (1 - rho) / rho
    hits = np.zeros(J)
    Ni = N.astype(int)
    pres = (N > 0).astype(float)
    den_one, den_W = one @ pres, W @ pres
    for _ in range(reps):
        Pb = np.zeros((S, J))
        pos = base > 0
        Pb[:, pos] = rng.beta(base[pos] * th, (1 - base[pos]) * th, size=(S, int(pos.sum())))
        Xb = rng.binomial(Ni, Pb).astype(float)
        pb = np.divide(Xb, N, out=np.zeros_like(Xb), where=N > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            est_b = ((one @ pb) / den_one)[0]
            boot_b = (W @ pb) / den_W
        Pt = rng.beta(P * th, (1 - P) * th, size=(S, len(fam)))
        Xt = rng.binomial(Ni[:, fam], Pt).astype(float)
        pt = np.divide(Xt, N[:, fam], out=np.zeros_like(Xt), where=N[:, fam] > 0)
        with np.errstate(invalid="ignore", divide="ignore"):
            est_t = ((one @ pt) / den_one[:, fam])[0]
            boot_t = (W @ pt) / den_W[:, fam]
        for i, j in enumerate(fam):
            e = est_b[fam].copy()
            b = boot_b[:, fam].copy()
            e[i], b[:, i] = est_t[i], boot_t[:, i]
            lb, se, q, ok = M._simul(e, b, 0.95, "lower")
            hits[j] += bool((ok[i] and lb[i] > C.DELTA) or ((not ok[i]) and e[i] > C.DELTA))
    return hits / reps


def fam_record(N, ev, pw):
    qual = ev & (pw >= A.POWER_MIN)
    rec = N.sum(0)
    return {"family": [C.CELL_NAMES[j] for j in np.flatnonzero(qual)], "family_size": int(qual.sum()),
            "record_share": float(rec[qual].sum() / rec.sum()), "power": {C.CELL_NAMES[j]: float(pw[j]) for j in np.flatnonzero(ev)}}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="CHK,W,G")
    ap.add_argument("--rhos", default="0.3,0.5,0.7")
    ap.add_argument("--ps", default="0.15,0.12,0.10")
    ap.add_argument("--pops", default="PD7,SD1_7,PD")
    ap.add_argument("--plantings", default="all,target")
    ap.add_argument("--tags", default="t1,t3")
    ap.add_argument("--reps-g", type=int, default=1000)
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    parts = a.parts.split(",")
    for tag in a.tags.split(","):
        dev = C.Dev(tag)
        W, _ = dev.weights()
        km = C.ARMS.index("Mstar")
        meta = {}
        for lab in ("PD7", "SD1_7", "PD"):
            p = INV[lab]
            N, X = dev.N[p][km], dev.X[p][km]
            ev = A.evaluable(N, dev.scenes, dev.log_idx)
            one = np.ones((1, N.shape[0]))
            est = A.rates(N, X, one)[0]
            meta[lab] = {"records_by_cell": {C.CELL_NAMES[j]: float(N[:, j].sum()) for j in range(N.shape[1])},
                         "scenes_by_cell": {C.CELL_NAMES[j]: int((N[:, j] > 0).sum()) for j in range(N.shape[1])},
                         "E_by_cell": {C.CELL_NAMES[j]: (float(est[j]) if np.isfinite(est[j]) else None) for j in range(N.shape[1])},
                         "evaluable": [C.CELL_NAMES[j] for j in np.flatnonzero(ev)], "records_total": float(N.sum())}
        mpath = os.path.join(CKPT, "meta_%s.json" % tag)
        if not os.path.exists(mpath):
            C.jdump(mpath, meta)
        pops = a.pops.split(",")
        jobs = []
        if "CHK" in parts:
            jobs.append(("CHK", "SD1_7", "check", 0.5, 0.15, 300, 500))
        if "W" in parts:
            for lab in pops:
                jobs.append(("W", lab, "all", 0.5, 0.15, 2000, 500))
                jobs.append(("W", lab, "all", 0.5, 0.15, 2000, 2000))
        if "G" in parts:
            for P in [float(x) for x in a.ps.split(",")]:
                for rho in [float(x) for x in a.rhos.split(",")]:
                    for pl in a.plantings.split(","):
                        for lab in pops:
                            jobs.append(("G", lab, pl, rho, P, a.reps_g, 500))
        for part, lab, pl, rho, P, reps, nw in jobs:
            name = "%s_%s_%s_%s_rho%.4f_p%.4f_r%d_w%d" % (part, tag, lab, pl, rho, P, reps, nw)
            path = os.path.join(CKPT, name + ".json")
            if os.path.exists(path):
                print("skip (checkpoint)", name, flush=True)
                continue
            p = INV[lab]
            N, X = dev.N[p][km], dev.X[p][km]
            ev = A.evaluable(N, dev.scenes, dev.log_idx)
            k = K_OF[lab]
            t1 = time.time()
            res = {"tracker": tag, "part": part, "pop": lab, "planting": pl, "rho": rho, "P": P, "reps": reps, "weights": nw}
            with C.power_settings(P=P, rho=rho, reps=reps):
                if part == "W":
                    seed = [C.SEED_POWER_K8, dev.i, k]
                    pw, _ = A.power_family(N, ev, dev.scenes, W[:nw], np.random.default_rng(seed))
                    res.update(fam_record(N, ev, pw))
                    mc = os.path.join(C.OUT, "mc_ckpt", "mc_%s_P2000.json" % tag)
                    if nw == 500 and os.path.exists(mc):
                        with open(mc) as f:
                            ref = json.load(f)["hk1"]["Mstar"]["pops"][lab]["power"]
                        res["equals_mc_P2000"] = bool(all(abs(ref[c] - res["power"][c]) < 1e-12 for c in ref))
                elif part == "CHK":
                    seed = [SEED, dev.i, k, 999]
                    Nb = N.copy()
                    Xb = np.round(N * P)      # every base cell at P (point estimate exactly P up to rounding)
                    pw_t = power_target(Nb, Xb, ev, W[:nw], np.random.default_rng(seed), P, rho, reps)
                    pw_a, _ = A.power_family(N, ev, dev.scenes, W[:nw], np.random.default_rng(seed + [1]))
                    res["target_with_all_base_at_P"] = {C.CELL_NAMES[j]: float(pw_t[j]) for j in np.flatnonzero(ev)}
                    res["power_family_all"] = {C.CELL_NAMES[j]: float(pw_a[j]) for j in np.flatnonzero(ev)}
                    d = pw_t[ev] - pw_a[ev]
                    res["max_abs_diff"] = float(np.max(np.abs(d)))
                    res["mean_diff"] = float(np.mean(d))
                    res["mc_se_diff_at_0.5"] = float(np.sqrt(2 * 0.25 / reps))
                else:
                    s = int(round(rho * 1000)) * 1000 + int(round(P * 1000)) * 10 + (0 if pl == "all" else 1)
                    seed = [SEED, dev.i, k, s]
                    if pl == "all":
                        pw, _ = A.power_family(N, ev, dev.scenes, W[:nw], np.random.default_rng(seed))
                    else:
                        pw = power_target(N, X, ev, W[:nw], np.random.default_rng(seed), P, rho, reps)
                    res.update(fam_record(N, ev, pw))
                    res["seed"] = seed
            res["seconds"] = time.time() - t1
            C.jdump(path, res)
            print(name, res.get("family_size"), res.get("record_share"), res.get("max_abs_diff"), res.get("equals_mc_P2000"),
                  round(res["seconds"], 1), "s", flush=True)
    print("POWER2 DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
