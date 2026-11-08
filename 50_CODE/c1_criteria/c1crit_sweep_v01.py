#!/usr/bin/env python3
"""c1crit_sweep_v01 (5 Nov 2026): question 4, the power-rule half of the verdict-stability sweep, nuScenes K8 development data
only. For every (rho, effect size P) on the grid, k8_analyse_v03.hk1_rule is rerun at the K8 seeds (bootstrap [20261106, i, 0];
power [20261107, i, ...]; 200 datasets, the rule's count) with k6_analyse_v02's POWER_RHO and POWER_P set in this process.

The cell flags and pooled bounds do not depend on rho or P; the power-qualified families, their flags and the floors do. The power
is recomputed for the arms whose verdict can depend on it, POWER_ARMS = M*, B0 and B3 (the comparators not shown above delta on
development data, plus M*). Every other comparator is shown above delta by flags in its all-evaluable cell family (independent of
the power rule); hk1_rule runs on it with its family held at the baseline (rho 0.5, P 0.15) family, and the summary asserts that
its ShownAbove comes from a cell flag. F_MIN, the HK1c margin and c are applied afterwards by c1crit_summary_v01 (no rerun).
One checkpoint JSON per (tracker, rho, P) in sweep_ckpt/.
Usage: python -B c1crit_sweep_v01.py [--rhos 0.3,0.5,0.7] [--ps 0.10,0.125,0.15,0.20] [--tags t1,t3]
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_mc_v01 as MC  # noqa: E402

CKPT = os.path.join(C.OUT, "sweep_ckpt")
POWER_ARMS = ("Mstar", "B0", "B3")


def key(rho, P):
    return "rho%.4f_p%.4f" % (rho, P)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--rhos", default="0.3,0.5,0.7")
    ap.add_argument("--ps", default="0.10,0.125,0.15,0.20")
    ap.add_argument("--tags", default="t1,t3")
    a = ap.parse_args(argv)
    os.makedirs(CKPT, exist_ok=True)
    t0 = time.time()
    rhos = [float(x) for x in a.rhos.split(",")]
    ps = [float(x) for x in a.ps.split(",")]
    for tag in a.tags.split(","):
        dev = C.Dev(tag)
        W, _ = dev.weights()
        bpath = os.path.join(CKPT, "sweep_%s_%s.json" % (tag, key(0.5, 0.15)))
        if not os.path.exists(bpath):
            t1 = time.time()
            vba = C.validity_all(dev, W)               # baseline: every arm's power at rho 0.5, P 0.15 (= the K8 run)
            res = {"tracker": tag, "rho": 0.5, "P": 0.15, "reps": C.A.POWER_REPS, "seed_boot": [C.SEED_BOOT_K8, dev.i, 0],
                   "seed_power_base": C.SEED_POWER_K8, "power_arms": list(C.ARMS), "hk1": MC.slim(vba)}
            res.update(MC.evaluate(dev, W, vba))
            res["seconds"] = time.time() - t1
            C.jdump(bpath, res)
            print(tag, "baseline", res["verdicts"], round(res["seconds"], 1), "s", flush=True)
        with open(bpath) as f:
            base = json.load(f)["hk1"]
        fams = {}
        for arm in C.ARMS:
            if arm in POWER_ARMS:
                continue
            fams[arm] = {}
            for p in C.POPS:
                m = C.np.zeros(len(C.CELLS), bool)
                for nm in base[arm]["pops"][C.LAB[p]]["family"]:
                    m[C.CELL_NAMES.index(nm)] = True
                fams[arm][p] = m
        for P in ps:
            for rho in rhos:
                path = os.path.join(CKPT, "sweep_%s_%s.json" % (tag, key(rho, P)))
                if os.path.exists(path):
                    print("skip (checkpoint)", tag, rho, P, flush=True)
                    continue
                t1 = time.time()
                with C.power_settings(P=P, rho=rho):
                    vba = C.validity_all(dev, W, fams=fams)
                res = {"tracker": tag, "rho": rho, "P": P, "reps": C.A.POWER_REPS, "seed_boot": [C.SEED_BOOT_K8, dev.i, 0],
                       "seed_power_base": C.SEED_POWER_K8, "power_arms": list(POWER_ARMS), "hk1": MC.slim(vba)}
                res.update(MC.evaluate(dev, W, vba))
                res["seconds"] = time.time() - t1
                C.jdump(path, res)
                print(tag, rho, P, res["verdicts"], round(res["seconds"], 1), "s", flush=True)
    print("SWEEP DONE", round(time.time() - t0, 1), "s")


if __name__ == "__main__":
    main()
