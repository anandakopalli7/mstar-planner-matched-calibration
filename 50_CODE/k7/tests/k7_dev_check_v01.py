#!/usr/bin/env python3
"""K7 development check (Claude line, v01, 1 Nov 2026). Development scenes only (the 10 nuScenes-mini scenes, excluded
from every K7 analysis): runs k7_run_v01 --dev in both modes for both trackers with the K7 fits, then k7_analyse_v01
--allow-dev (B = 200), and writes a summary: per arm the infeasible-decision rate, the pooled PD7 and PD exceedance
(scene level), and the closed-loop progress and collision counts. Diagnostics, not evidence.
Usage: python -B k7_dev_check_v01.py --out <json> --runs <scratch dir>
"""
import argparse
import json
import os
import subprocess
import sys

K7 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(K7))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", required=True)
    a = ap.parse_args()
    py = sys.executable
    os.makedirs(a.runs, exist_ok=True)
    for t in ("t1", "t3"):
        for mode in ("decide", "loop"):
            caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, sp)) for sp in ("train", "val")]
            subprocess.run([py, "-B", os.path.join(K7, "k7_run_v01.py"), "--caches", *caches, "--fits",
                            os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t), "--tag", "%s_%s" % (t, mode),
                            "--mode", mode, "--out", a.runs, "--dev", "--workers", "6"], check=True, capture_output=True)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % sp, "MANIFEST.json") for sp in ("train", "val")]
    res_path = os.path.join(a.runs, "dev_analysis.json")
    subprocess.run([py, "-B", os.path.join(K7, "k7_analyse_v01.py"), "--runs", a.runs, "--tags", "t1", "t3", "--manifests", *man,
                    "--out", res_path, "--allow-dev", "--boot", "200"], check=True, capture_output=True)
    r = json.load(open(res_path))
    out = {"note": "development scenes only; diagnostics, not evidence", "decide": {}, "loop": {}}
    for t in ("t1", "t3"):
        d = r["decide"][t]
        out["decide"][t] = {"infeasible_rate": {k: v["mean"] for k, v in d["infeasible_rate"].items()},
                            "pooled_PD7": {k: (v or {}).get("E") for k, v in d["populations"]["PD7_primary"]["pooled_by_arm"].items()},
                            "pooled_PD": {k: (v or {}).get("E") for k, v in d["populations"]["PD_inpath"]["pooled_by_arm"].items()},
                            "records_PD7_Mstar": (d["populations"]["PD7_primary"]["pooled_by_arm"]["Mstar"] or {}).get("records")}
        lo = r["loop"][t]["outcomes"]
        out["loop"][t] = {k: {"progress": v["progress_mean"], "at_fault_tracked": v["at_fault_tracked"], "infeasible_frames": v["infeasible_frame_share"]}
                          for k, v in lo.items()}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
    print("K7 DEV CHECK DONE")


if __name__ == "__main__":
    main()
