#!/usr/bin/env python3
"""Merge the OC v02 shards of one tracker layout and apply the acceptance criteria of plan v04 section 9
(Claude line, v01, 31 Oct 2026).
  A1: at rho = 0.5, M* is flagged by HM1 in at most 10 % of datasets under the fixed rule and under the refit-CV rule.
  A2: at rho = 0.5, HM6 fails for a valid M* in at most 10 % of datasets.
Rates are given with Wilson 95 % intervals. Power tables: E2 (planted val turning shift), HM3 (car lateral turning effect),
and the per-cell component power with its minimum detectable exceedance (80 %).
Usage: python merge_oc_v02.py --dir <shard folder> --tracker T1 --out <json>
"""
import argparse
import glob
import json
import math
import os
from collections import defaultdict

import numpy as np


def wilson(k, n):
    if n == 0:
        return [None, None]
    p, z = k / n, 1.96
    c = (p + z * z / (2 * n)) / (1 + z * z / n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return [round(max(0, c - h), 4), round(min(1, c + h), 4)]


def rate(rows, key, want=True):
    k = sum(1 for r in rows if bool(r[key]) == want)
    return {"rate": round(k / len(rows), 4) if rows else None, "n": len(rows), "ci95": wilson(k, len(rows))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    groups = defaultdict(list)
    for f in sorted(glob.glob(os.path.join(a.dir, "%s_*.json" % a.tracker))):
        r = json.load(open(f))
        groups[(r["part"], r["rho"], r["effect"])] += r["rows"]
    out = {"tracker": a.tracker, "parts": {}}
    for (part, rho, eff), rows in sorted(groups.items()):
        key = "%s|rho%.1f|effect%.2f" % (part, rho, eff)
        if part == "e1null":
            out["parts"][key] = {"Mstar_flag_fixed": rate(rows, "fixed_flag"), "Mstar_flag_refit": rate(rows, "refit_flag")}
        elif part in ("e2null", "e2power"):
            d = {"HM6_fail": rate(rows, "HM6", False), "HM6a_fail": rate(rows, "HM6a", False), "HM6b_fail": rate(rows, "HM6b", False),
                 "mean_pooled_E": round(float(np.mean([r["pooled_E"] for r in rows])), 4)}
            if rows and "turn_cell" in rows[0]:
                d.update({"turn_cell": rows[0]["turn_cell"], "mean_turn_cell_E": round(float(np.mean([r["turn_cell_E"] for r in rows])), 4),
                          "turn_cell_flag": rate(rows, "turn_cell_flagged")})
            out["parts"][key] = d
        elif part == "hm3power":
            cells = rows[0]["B6_E_turning_cells"].keys() if rows else []
            out["parts"][key] = {"HM3_holds": rate(rows, "HM3"), "HM3_fixed_rule_only": rate(rows, "HM3_fixed_rule"),
                                 "mean_B6_E": {c: round(float(np.mean([r["B6_E_turning_cells"][c] for r in rows])), 4) for c in cells},
                                 "mean_Mstar_E": {c: round(float(np.mean([r["Mstar_E_turning_cells"][c] for r in rows])), 4) for c in cells}}
        elif part == "comp":
            sz = None
            d = {}
            for tag in ("E1", "E2"):
                ps = sorted(rows[0][tag].keys())
                pw = {p: np.mean([r[tag][p] for r in rows], axis=0).round(3).tolist() for p in ps}
                mde = [next((p[1:] for p in ps if pw[p][j] >= 0.8), ">0.30") for j in range(len(pw[ps[0]]))]
                d[tag] = {"power_component": pw, "MDE80_component": mde, "n": len(rows)}
            out["parts"][key] = d
    p = out["parts"]
    e1 = p.get("e1null|rho0.5|effect1.00")
    e2 = p.get("e2null|rho0.5|effect1.00")
    out["acceptance"] = {"A1_fixed": bool(e1 and e1["Mstar_flag_fixed"]["rate"] <= 0.10),
                         "A1_refit": bool(e1 and e1["Mstar_flag_refit"]["rate"] <= 0.10),
                         "A2": bool(e2 and e2["HM6_fail"]["rate"] <= 0.10)}
    out["acceptance"]["all"] = all(out["acceptance"].values())
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out["acceptance"]), "parts:", len(p))


if __name__ == "__main__":
    main()
