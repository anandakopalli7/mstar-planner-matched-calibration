#!/usr/bin/env python3
"""c1crit_mc_v01 (5 Nov 2026): question 2, Monte Carlo error of the power rule and of the sup-t flags, nuScenes K8 development
data only (T1, T3; 840 scenes, 68 logs; decision mode). Everything runs through k8_analyse_v03.hk1_rule (reused, unchanged).

Parts (each checkpointed as one JSON per tracker in mc_ckpt/):
  P200, P1000, P2000  the K8 seeds (bootstrap [20261106, i, 0], power [20261107, i, ...]) with POWER_REPS = 200 (the rule), 1000
                      and 2000. The power draws are nested: the first 200 datasets of the 2000-dataset run are the rule's.
  PS<s>, s = 1..5     alternative POWER seed bases 20261301 + s - 1 (bootstrap weights unchanged), POWER_REPS = 200.
  BS<s>, s = 1..5     alternative BOOTSTRAP seeds [20261106, i, 0, s] (power keys unchanged; the power rule's weights are the
                      first 500 of the new set). Two readings: 'full' (everything recomputed) and 'fixed_fams' (the power-qualified
                      families held at the K8 run's, so only the sup-t flags move).
For each: per arm and population the flags, the sup-t quantiles, the power of every evaluable cell, the family and its flags;
the C1 status (Valid, ShownAbove v07c / v07d, K8's form_valid) and Forms A, B, C (c1crit_common_v01.forms).
Also, at the K8 seeds: the MC standard error of each sup-t quantile (q is the 0.95 quantile of the B = 2000 max-|t| draws; its
SE from 1000 resamples of those draws, seed [20261207, i]) and every cell with |t - q| < 0.2, t = (E - delta) / SE.
Usage: python -B c1crit_mc_v01.py [--parts P200,P1000,P2000,PS,BS,QSE] [--tags t1,t3]
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A, K8 = C.A, C.K8
CKPT = os.path.join(C.OUT, "mc_ckpt")
POWER_ALT = [20261301 + s for s in range(5)]
BOOT_ALT = list(range(1, 6))
SEED_QSE = 20261207


def slim(vba):
    """hk1_rule outputs without bulky fields, with the power of every evaluable cell kept."""
    out = {}
    for a, v in vba.items():
        pops = {}
        for p in C.POPS:
            r = v["pops"][p]
            pw = next((r[k] for k in r if k.startswith("power_at_")), None)
            pops[C.LAB[p]] = {"evaluable": r["evaluable"], "flagged": r["flagged"], "q": r.get("q"), "family": r["family"],
                              "family_size": r["family_size"], "family_flagged": r["family_flagged"], "family_q": r.get("family_q"),
                              "pooled": r["pooled"], "power": pw, "floor_met": r.get("floor_met")}
        out[a] = {"HK1": v["HK1"], "pops": pops}
    return out


def evaluate(dev, W, vba):
    status = {a: C.status_from_hk1(vba[a]) for a in C.ARMS}
    fm = C.forms(dev, W, status)
    return {"verdicts": C.verdict_summary(status, fm), "forms": fm,
            "status": {a: {k: status[a][k] for k in ("valid", "shown_v07c", "shown_v07d", "valid_k8")} for a in C.ARMS}}


def fams_of(vba):
    """The power-qualified masks of a run, for hk1_rule(fams=...)."""
    out = {}
    for a, v in vba.items():
        out[a] = {}
        for p in C.POPS:
            m = np.zeros(len(C.CELLS), bool)
            for nm in v["pops"][p]["family"]:
                m[C.CELL_NAMES.index(nm)] = True
            out[a][p] = m
    return out


def q_se_and_near(dev, W, vba, rng):
    """MC SE of each sup-t quantile (cells family, power family) and the cells with |t - q| < 0.2, at the given weights."""
    one = np.ones((1, len(dev.scenes)))
    res = {}
    for a in C.ARMS:
        res[a] = {}
        for p in C.POPS:
            N, X = dev.T(a)[p]
            est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
            r = vba[a]["pops"][p]
            out = {}
            for name, fam_names, qstored in (("cells", None, r.get("q")), ("family", r["family"], r.get("family_q"))):
                ev = A.evaluable(N, dev.scenes, dev.log_idx)
                fam = np.flatnonzero(ev) if fam_names is None else np.array([C.CELL_NAMES.index(x) for x in fam_names], int)
                if not len(fam) or qstored is None:
                    out[name] = None
                    continue
                e, b = est[fam], boot[:, fam]
                se = np.nanstd(b, axis=0, ddof=1)
                ok = se > 0
                dev_ = np.where(ok, (b - e) / np.where(ok, se, 1.0), np.nan)
                T = np.nanmax(dev_, axis=1)
                q = float(np.nanquantile(T, 0.95))
                qs = [float(np.nanquantile(T[rng.integers(0, len(T), len(T))], 0.95)) for _ in range(1000)]
                t = np.where(ok, (e - C.DELTA) / np.where(ok, se, 1.0), np.nan)
                near = [{"cell": C.CELL_NAMES[j], "E": float(e[i]), "t": float(t[i]), "q": q} for i, j in enumerate(fam)
                        if np.isfinite(t[i]) and abs(t[i] - q) < 0.2]
                out[name] = {"q": q, "q_equals_stored": bool(abs(q - qstored) < 1e-9), "q_mc_se": float(np.std(qs, ddof=1)),
                             "near_cells": near, "size": int(len(fam))}
            res[a][C.LAB[p]] = out
    return res


def run_part(tag, part, base_vba=None):
    dev = C.Dev(tag)
    i = dev.i
    t0 = time.time()
    if part in ("P200", "P1000", "P2000"):
        reps = int(part[1:])
        W, _ = dev.weights()
        with C.power_settings(reps=reps):
            vba = C.validity_all(dev, W)
        res = {"seed_boot": [C.SEED_BOOT_K8, i, 0], "seed_power_base": C.SEED_POWER_K8, "reps": reps}
        res.update(evaluate(dev, W, vba))
        res["hk1"] = slim(vba)
        if part == "P200":
            res["q_mc"] = q_se_and_near(dev, W, vba, np.random.default_rng([SEED_QSE, i]))
        return res
    if part.startswith("PS"):
        s = int(part[2:])
        W, _ = dev.weights()
        vba = C.validity_all(dev, W, power_base=POWER_ALT[s - 1])
        res = {"seed_boot": [C.SEED_BOOT_K8, i, 0], "seed_power_base": POWER_ALT[s - 1], "reps": 200}
        res.update(evaluate(dev, W, vba))
        res["hk1"] = slim(vba)
        return res
    if part.startswith("BS"):
        s = int(part[2:])
        seed = [C.SEED_BOOT_K8, i, 0, s]
        W, _ = dev.weights(seed=seed)
        vba = C.validity_all(dev, W)
        res = {"seed_boot": seed, "seed_power_base": C.SEED_POWER_K8, "reps": 200, "full": evaluate(dev, W, vba)}
        res["full"]["hk1"] = slim(vba)
        vbf = C.validity_all(dev, W, fams=fams_of(base_vba))
        res["fixed_fams"] = evaluate(dev, W, vbf)
        res["fixed_fams"]["hk1"] = slim(vbf)
        res["q_mc"] = q_se_and_near(dev, W, vba, np.random.default_rng([SEED_QSE, i, s]))
        return res
    raise ValueError(part)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="P200,P2000,P1000,PS,BS")
    ap.add_argument("--tags", default="t1,t3")
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    parts = []
    for p in a.parts.split(","):
        parts += ["PS%d" % s for s in range(1, 6)] if p == "PS" else ["BS%d" % s for s in BOOT_ALT] if p == "BS" else [p]
    t0 = time.time()
    for tag in a.tags.split(","):
        base = None
        for part in parts:
            path = os.path.join(CKPT, "mc_%s_%s.json" % (tag, part))
            if os.path.exists(path):
                print("skip (checkpoint)", tag, part, flush=True)
                continue
            if part.startswith("BS") and base is None:
                W, _ = C.Dev(tag).weights()
                base = C.validity_all(C.Dev(tag), W)
            t1 = time.time()
            res = run_part(tag, part, base)
            res.update({"tracker": tag, "part": part, "seconds": time.time() - t1})
            C.jdump(path, res)
            v = res.get("verdicts") or res["full"]["verdicts"]
            print(tag, part, v, round(res["seconds"], 1), "s", flush=True)
    print("MC DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
