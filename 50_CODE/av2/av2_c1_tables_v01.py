#!/usr/bin/env python3
"""av2_c1_tables_v01 (Claude line, 5 Nov 2026): tables for AV2_TRACKER_NOTE_v03 from the 375-log step's own outputs
(tracker records and per-frame files, the adapter receipt, the metric and HOTA JSONs, the 150-log v01/v02 metric files).
Reads no ground truth; prints markdown and writes a JSON summary. Tracking metrics only.
Usage: python -I -B av2_c1_tables_v01.py --out-json <json> --out-md <md>
"""
import argparse
import json
import os
import sys
from collections import defaultdict

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
T = os.path.join(W, "30_DATA", "av2_trk_v02")
R = os.path.join(W, "60_RESULTS", "av2_trk", "c1_375")
R1 = os.path.join(W, "60_RESULTS", "av2_trk")
PARTS = ("held225", "val150", "pooled")
RUNS = {"t1": ("T1 CANMOT sc", [os.path.join(T, "export", "t1_owncp", "worker%d" % i) for i in range(8)]),
        "t3": ("T3 Poly-MOT", [os.path.join(T, "export", "t3_owncp", "worker%d" % i) for i in range(8)]),
        "tab_kf": ("AB3DMOT (tab), filter-state output", [os.path.join(T, "export_tab_owncp", "ab3dmot_kf", "worker%d" % i) for i in range(6)]),
        "tab_det": ("AB3DMOT (tab), detection-box output", [os.path.join(T, "export_tab_owncp", "ab3dmot_det", "worker%d" % i) for i in range(6)])}
OLD = {"t1": "t1_lt3d", "t3": "t3_lt3d", "tab_kf": "ab3dmot_kf", "tab_det": "ab3dmot_det"}
CLS = (("car", "car"), ("pedestrian", "pedestrian"), ("bicycle", "cyclist"))


def f3(x):
    return "n/a" if x is None else ("%.3f" % x)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-json", required=True)
    ap.add_argument("--out-md", required=True)
    a = ap.parse_args()
    L = json.load(open(os.path.join(T, "C1_LOGS_375_v01.json")))
    part_of = {lg: "held225" for lg in L["held_out_225"]}
    part_of.update({lg: "val150" for lg in L["val_150"]})
    out = {"counts": {}, "metrics": {}}
    md = []
    # counts: logs, frames, records per run and part (from the per-frame files)
    rc = json.load(open(os.path.join(T, "input", "owncp", "receipt.json")))
    out["counts"]["adapter"] = {"stats": rc["stats"], "stats_per_source": [{k: v for k, v in s.items() if k != "per_category_in"} for s in rc["stats_per_source"]]}
    for run, (name, dirs) in RUNS.items():
        c = {p: defaultdict(int) for p in PARTS}
        for d in dirs:
            pf = json.load(open(os.path.join(d, "x1_per_frame.json")))
            for p in pf:
                if p.get("error"):
                    continue
                for q in (part_of[p["scene"]], "pooled"):
                    c[q]["frames"] += 1
                    c[q]["records"] += p.get("tracks", p.get("tracks_active", 0))
                    c[q]["dets_to_tracker"] += p.get("dets_post_filter", p.get("dets_tracker", 0))
        for q in PARTS:
            c[q]["logs"] = sum(1 for lg, pp in part_of.items() if pp == q or q == "pooled")
        out["counts"][run] = {q: dict(c[q]) for q in PARTS}
    md.append("| Run | Part | Logs | Frames | Detections to the tracker | Exported track records |")
    md.append("|---|---|---|---|---|---|")
    for run, (name, _) in RUNS.items():
        for q in PARTS:
            x = out["counts"][run][q]
            md.append("| %s | %s | %d | %d | %d | %d |" % (name, q, x["logs"], x["frames"], x["dets_to_tracker"], x["records"]))
    md.append("")
    # metrics: HOTA (av2) + AMOTA/MOTA/IDS (nuScenes protocol), per part and pooled, beside the 150-log public-LT3D values
    md.append("| Tracker | Part | Class | HOTA (tuned) | HOTA (mean of 10 thr.) | DetA | AssA | AMOTA | MOTA | IDS | MOTA (av2) | IDSW (av2) |")
    md.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for run, (name, _) in RUNS.items():
        for q in PARTS + ("val150_public_lt3d",):
            if q == "val150_public_lt3d":
                hp = os.path.join(R1, "hota", "AV2_HOTA_%s.json" % OLD[run])
                mp = os.path.join(R1, "metrics", "AV2_metrics_%s.json" % OLD[run])
            else:
                hp = os.path.join(R, "hota", "AV2_C1_HOTA_%s_%s.json" % (run, q))
                mp = os.path.join(R, "metrics", "AV2_C1_metrics_%s_%s.json" % (run, q))
            H = json.load(open(hp))["per_class"] if os.path.exists(hp) else {}
            M = json.load(open(mp))["per_class"] if os.path.exists(mp) else {}
            for c, lab in CLS:
                h, m = H.get(c) or {}, M.get(c) or {}
                row = {"HOTA": h.get("HOTA"), "HOTA_mean10": h.get("HOTA_mean_over_10_thresholds"), "DetA": h.get("DetA"),
                       "AssA": h.get("AssA"), "AMOTA": m.get("amota"), "MOTA": m.get("mota"), "IDS": m.get("ids"),
                       "MOTA_av2": h.get("MOTA_av2"), "IDSW_av2": h.get("IDSW_av2")}
                out["metrics"]["%s|%s|%s" % (run, q, lab)] = row
                md.append("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                    name, "val150, public LT3D (note v02)" if q == "val150_public_lt3d" else q, lab, f3(row["HOTA"]), f3(row["HOTA_mean10"]),
                    f3(row["DetA"]), f3(row["AssA"]), f3(row["AMOTA"]), f3(row["MOTA"]),
                    "n/a" if row["IDS"] is None else "%d" % row["IDS"], f3(row["MOTA_av2"]),
                    "n/a" if row["IDSW_av2"] is None else "%d" % row["IDSW_av2"]))
    json.dump(out, open(a.out_json, "w"), indent=1)
    open(a.out_md, "w").write("\n".join(md) + "\n")
    print("\n".join(md))


if __name__ == "__main__":
    sys.exit(main())
