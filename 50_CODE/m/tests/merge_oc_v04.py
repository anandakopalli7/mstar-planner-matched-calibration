#!/usr/bin/env python3
"""Merge the OC study for one tracker layout under plan v05 section 9 (Claude line, v04, 31 Oct 2026; R07c X-M1, X-m2, X-m3).
- E1 parts come from the OC v02 shards (E1 rules unchanged in code v04): e1null, hm3power, comp.
- E2 parts come from the fresh OC v03 shards (seed labels "oc3", v04 rules where HM6b is the pooled significance check):
  e2null at log SD 0.05, 0.1 and 0.2 and rho 0.5 and 0.8; e2power.
- Acceptance:
  A1: at rho 0.5, M* is flagged by HM1 in at most 10 % of null datasets, fixed rule and refit-CV.
  A2: at rho 0.5 and log SD 0.1, HM6 fails in at most 10 % of the 100 fresh null datasets.
- The expected number of datasets per part is asserted, so a missing shard stops the merge.
Usage: python merge_oc_v04.py --v02 <oc_v02 dir> --v03 <oc_v03 dir> --tracker T1 --out <json>
"""
import argparse
import glob
import json
import math
import os
from collections import defaultdict

import numpy as np

EXPECTED = {("e1null", 0.5, 1.0, 0.1): 20, ("e1null", 0.8, 1.0, 0.1): 10, ("hm3power", 0.5, 1.6, 0.1): 20, ("hm3power", 0.5, 2.0, 0.1): 20,
            ("hm3power", 0.5, 2.6, 0.1): 20, ("hm3power", 0.8, 2.0, 0.1): 10, ("comp", 0.5, 1.0, 0.1): 40,
            ("e2null", 0.5, 1.0, 0.1): 100, ("e2null", 0.8, 1.0, 0.1): 20, ("e2null", 0.5, 1.0, 0.05): 40, ("e2null", 0.5, 1.0, 0.2): 40,
            ("e2power", 0.5, 1.5, 0.1): 40, ("e2power", 0.5, 2.0, 0.1): 40}


def wilson(k, n):
    p, z = k / n, 1.96
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def rate(rows, f):
    k = sum(1 for r in rows if f(r))
    return {"rate": round(k / len(rows), 4), "k": k, "n": len(rows), "ci95": wilson(k, len(rows))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v02", required=True)
    ap.add_argument("--v03", required=True)
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    groups = defaultdict(list)
    settings = defaultdict(set)
    for d, parts in ((a.v02, ("e1null", "hm3power", "comp")), (a.v03, ("e2null", "e2power"))):
        for f in sorted(glob.glob(os.path.join(d, "%s_*.json" % a.tracker))):
            r = json.load(open(f))
            if r["part"] not in parts:
                continue
            key = (r["part"], r["rho"], r["effect"], r.get("log_sd", 0.1))
            groups[key] += r["rows"]
            settings[key].add((r.get("e1_reps", 3), r.get("refit_B", 60), r.get("e2_B", 150)))
    for key, n in EXPECTED.items():
        assert len(groups.get(key, [])) == n, "part %s has %d datasets, expected %d" % (key, len(groups.get(key, [])), n)
    out = {"tracker": a.tracker, "settings_note": "E1 parts: 3 CV repetitions, fixed-rule B = 300, refit-CV B = 60; E2 parts: B = 150 "
                                                  "(the run uses 20 repetitions and B = 2000 / 200 / 1000)", "parts": {}}
    for key, rows in sorted(groups.items()):
        part, rho, eff, lsd = key
        name = "%s|rho%.1f|effect%.2f|logsd%.2f" % key
        if part == "e1null":
            out["parts"][name] = {"Mstar_flag_fixed": rate(rows, lambda r: r["fixed_flag"]), "Mstar_flag_refit": rate(rows, lambda r: r["refit_flag"])}
        elif part in ("e2null", "e2power"):
            d = {"HM6_fail": rate(rows, lambda r: not r["HM6"]), "HM6a_fail": rate(rows, lambda r: not r["HM6a"]),
                 "HM6b_fail": rate(rows, lambda r: not r["HM6b"]), "pooled_equivalence_at_eps_fails": rate(rows, lambda r: not r["pooled_equivalence_at_eps"]),
                 "mean_pooled_E": round(float(np.mean([r["pooled_E"] for r in rows])), 4),
                 "sd_pooled_E": round(float(np.std([r["pooled_E"] for r in rows])), 4)}
            if "turn_cell" in rows[0]:
                d.update({"turn_cell": rows[0]["turn_cell"], "mean_turn_cell_E": round(float(np.mean([r["turn_cell_E"] for r in rows])), 4),
                          "turn_cell_flag": rate(rows, lambda r: r["turn_cell_flagged"])})
            out["parts"][name] = d
        elif part == "hm3power":
            cells = rows[0]["B6_E_turning_cells"].keys()
            out["parts"][name] = {"HM3_holds": rate(rows, lambda r: r["HM3"]), "HM3_fixed_rule_alone": rate(rows, lambda r: r["HM3_fixed_rule"]),
                                  "mean_B6_E": {c: round(float(np.mean([r["B6_E_turning_cells"][c] for r in rows])), 4) for c in cells},
                                  "mean_Mstar_E": {c: round(float(np.mean([r["Mstar_E_turning_cells"][c] for r in rows])), 4) for c in cells}}
        elif part == "comp":
            d = {}
            for tag in ("E1", "E2"):
                ps = sorted(rows[0][tag].keys())
                pw = {p: np.mean([r[tag][p] for r in rows], axis=0).round(3).tolist() for p in ps}
                d[tag] = {"power_component": pw, "MDE80_component": [next((p[1:] for p in ps if pw[p][j] >= 0.8), ">0.30") for j in range(len(pw[ps[0]]))]}
            out["parts"][name] = d
    p = out["parts"]
    e1 = p["e1null|rho0.5|effect1.00|logsd0.10"]
    e2 = p["e2null|rho0.5|effect1.00|logsd0.10"]
    out["acceptance"] = {"A1_fixed": e1["Mstar_flag_fixed"]["rate"] <= 0.10, "A1_refit": e1["Mstar_flag_refit"]["rate"] <= 0.10,
                         "A2": e2["HM6_fail"]["rate"] <= 0.10}
    out["acceptance"]["all"] = all(out["acceptance"].values())
    out["null_HM6_failure_rate_for_this_layout"] = e2["HM6_fail"]["rate"]
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["acceptance"]), "HM6 null fail", e2["HM6_fail"])


if __name__ == "__main__":
    main()
