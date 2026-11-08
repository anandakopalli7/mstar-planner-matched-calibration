#!/usr/bin/env python3
"""R21 timing probe (rehearsal stand-in only; B <= 2000): cost of one arm-population bootstrap and of one power dataset at
U = 150 (the rehearsal) and U = 375 (the rehearsal's units tiled 2.5 times; a stand-in for the AV2 size), for extrapolation
to B = 40000. Writes timing_probe_v01.json beside itself."""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import r21_lib_v01 as L  # noqa: E402
import numpy as np  # noqa: E402

R = r"C:/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911/70_TESTS/c1_v01/rehearsal150_v10"
d = L.RouteData(R + "/runs", "t1_within_lt3d", "t1", fits_path=R + "/fits_within_t1.json")
d.select_retuned()
out = {}
for U_target in (150, 375):
    N, X = d.table("Mstar", "PD7_primary")
    reps = int(np.ceil(U_target / N.shape[0]))
    N = np.vstack([N] * reps)[:U_target]
    X = np.vstack([X] * reps)[:U_target]
    rec = {}
    for B in (1000, 2000):
        W = L.Weights([L.SEED_BOOT, 0, 0], U_target, B)
        t0 = time.perf_counter()
        for _ in range(3):
            r = L.arm_population(N, X, W, L.LEVEL_M, family=[c for c in L.CELLNAMES[:8]], want_upper=True)
        rec["arm_population_B%d_s" % B] = (time.perf_counter() - t0) / 3
    ev = np.flatnonzero(L.evaluable(N))
    W = L.Weights([L.SEED_BOOT, 0, 0], U_target, 500)
    t0 = time.perf_counter()
    L.power_target(N, ev, W.rows(0, 500), np.random.default_rng(1), 100)
    rec["power_per_dataset_s"] = (time.perf_counter() - t0) / 100
    rec["evaluable_cells"] = int(len(ev))
    out["U%d" % U_target] = rec
    print(U_target, rec, flush=True)
out["memory"] = L.memory_mb()
with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "timing_probe_v01.json"), "w") as f:
    json.dump(out, f, indent=1)
print(out["memory"])
