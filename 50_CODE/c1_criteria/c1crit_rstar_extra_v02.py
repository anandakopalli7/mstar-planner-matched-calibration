#!/usr/bin/env python3
"""c1crit_rstar_extra_v02 (5 Nov 2026): how well the OC's analytic power family (c1_power_counts_v02.power_family_analytic, used by
part D of c1crit_rstar_v02) stands for R*'s simulated family (target-only planting with the other cells at delta, 2000 datasets, 500
weights; part CP), on the 840 nuScenes development scenes: per tracker, arm and population, the two family sizes and the cells on
which they disagree. Development data only; deterministic (reads the CP checkpoints). Output:
60_RESULTS/c1_criteria_sensitivity_v02/D_analytic_vs_simulated_v02.json. Usage: python -B c1crit_rstar_extra_v02.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import c1crit_rstar_v02 as R  # noqa: E402
import numpy as np  # noqa: E402

A, PC2 = C.A, C.PC2


def main():
    out = {}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        for arm in C.ARMS:
            for lab in ("PD7", "SD1_7", "PD"):
                cp = R.cp_family(tag, arm, lab)
                if cp is None:
                    continue
                N = dev.N[R.INV[lab]][C.ARMS.index(arm)]
                ev = A.evaluable(N, dev.scenes, dev.log_idx)
                qa = PC2.power_family_analytic(N, ev)
                fa = [C.CELL_NAMES[j] for j in np.flatnonzero(qa)]
                fs = cp["family"]
                out["%s|%s|%s" % (tag, arm, lab)] = {"analytic": len(fa), "simulated_rstar": len(fs),
                                                     "only_analytic": sorted(set(fa) - set(fs)), "only_simulated": sorted(set(fs) - set(fa)),
                                                     "simulated_power_of_disagreeing": {c: cp["power"].get(c) for c in set(fa) ^ set(fs)}}
                print(tag, arm, lab, len(fa), len(fs), flush=True)
    C.jdump(os.path.join(R.OUT2, "D_analytic_vs_simulated_v02.json"), out)
    print("EXTRA DONE")


if __name__ == "__main__":
    main()
