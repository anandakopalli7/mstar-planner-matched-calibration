#!/usr/bin/env python3
"""R21 rehearsal re-check of the two H1-relevant MC-borderline items (rehearsal stand-in only; B = 2000): the family flag of
B6 (T1) and of RETUNED (T3) at the removal level 1 - 0.0125/9, with the analysis's families (recovered from size and record
share), under the registered seed and 5 R21 seeds. A flag that changes across seeds is MC at this B, not a code difference.
Writes borderline_recheck_v01.json beside itself."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import r21_lib_v01 as L  # noqa: E402
import numpy as np  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
R = r"C:/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911/70_TESTS/c1_v01/rehearsal150_v10"
res = json.load(open(os.path.join(HERE, "r21_rederive_rehearsal_B2000.json"), encoding="utf-8"))
out = {}
for t, arm in (("t1", "B6"), ("t3", "RETUNED")):
    rt = res["routes"]["within_lt3d"][t]
    fam = rt["arms"][arm]["PD7_primary"]["family"]
    d = L.RouteData(R + "/runs", "%s_within_lt3d" % t, t, fits_path=R + "/fits_within_%s.json" % t)
    d.select_retuned()
    N, X = d.table(arm, "PD7_primary")
    est = L.point_rates(N, X)
    famidx = [L.CELLNAMES.index(c) for c in fam]
    rows = []
    for seed in [[L.SEED_BOOT, L.TRACKER_INDEX[t], 0]] + [[L.R21_SEED_MC, L.TRACKER_INDEX[t], 0, 900 + s] for s in range(5)]:
        W = L.Weights(seed, d.U, 2000)
        r = L.flag_cells(est, W.rates(N, X), famidx, L.LEVEL_RM)
        k = int(np.argmax(r["bound"]))
        rows.append({"seed": seed, "max_lb_minus_delta": float(r["bound"][k] - L.DELTA), "cell": fam[k], "flagged": bool(r["flag"].any()),
                     "q": r["q"], "q_mcse_AB": r["q_mcse"]})
    out["%s %s PD7 family" % (t, arm)] = {"family": fam, "by_seed": rows,
                                         "share_flagged": float(np.mean([x["flagged"] for x in rows]))}
    print(t, arm, [(round(x["max_lb_minus_delta"], 4), x["flagged"]) for x in rows], flush=True)
with open(os.path.join(HERE, "borderline_recheck_v01.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, indent=1)
