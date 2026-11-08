#!/usr/bin/env python3
"""av2_note_tables_v02: Markdown tables for AV2_TRACKER_NOTE_v02.md and AV2_AB3DMOT_NOTE_v01.md from the stored JSONs
(Claude line, 2 Nov 2026): tracking metrics with HOTA next to AMOTA, MOTA and IDS; K8 item counts (AV2_TRACKER_COUNTS_v02.json).
Reads only outputs of this port. Usage: python -I -B av2_note_tables_v02.py > tables.md
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
R = os.path.join(W, "60_RESULTS", "av2_trk")
RUNS = [("t1_lt3d", "T1 CANMOT sc", "LT3D"), ("t3_lt3d", "T3 Poly-MOT", "LT3D"), ("t2_lt3d", "T2 CANMOT sample/trainval", "LT3D"),
        ("t1_voxelnext", "T1 CANMOT sc", "VoxelNeXt"), ("t3_voxelnext", "T3 Poly-MOT", "VoxelNeXt"),
        ("ab3dmot_det", "AB3DMOT (LT3D), detection-box output", "LT3D"), ("ab3dmot_kf", "AB3DMOT (LT3D), filter-state output", "LT3D")]
CLS = [("car", "car"), ("pedestrian", "pedestrian"), ("bicycle", "cyclist")]


def load(p):
    return json.load(open(p)) if os.path.exists(p) else None


def f3(x):
    return "–" if x is None else "%.3f" % x


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("| Tracker | Detector | Class | HOTA (av2, tuned) | HOTA (av2, mean of 10 thr.) | DetA | AssA | AMOTA | MOTA | IDS | MOTA (av2) | IDSW (av2) |")
    print("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for tag, trk, det in RUNS:
        h = load(os.path.join(R, "hota", "AV2_HOTA_%s.json" % tag))
        m = load(os.path.join(R, "metrics", "AV2_metrics_%s.json" % tag))
        if h is None and m is None:
            continue
        for c, lab in CLS:
            hc = (h or {}).get("per_class", {}).get(c, {})
            mc = ((m or {}).get("per_class", {}) or {}).get(c) or {}
            print("| %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
                trk, det, lab, f3(hc.get("HOTA")), f3(hc.get("HOTA_mean_over_10_thresholds")), f3(hc.get("DetA")), f3(hc.get("AssA")),
                f3(mc.get("amota")), f3(mc.get("mota")), "–" if mc.get("ids") is None else "%d" % mc["ids"],
                f3(hc.get("MOTA_av2")), "–" if hc.get("IDSW_av2") is None else "%d" % hc["IDSW_av2"]))
    c = load(os.path.join(R, "AV2_TRACKER_COUNTS_v02.json"))
    if c is None:
        return
    print("\n### K8 items (counts only): decision states, pairs and items per population, items / logs (evaluable cells of 32)\n")
    print("| Run | decision states | pairs enforced at margin 0 | pairs with the paired object annotated at k + h | PD7 | SD1_7 | PD | NIP |")
    print("|---|---|---|---|---|---|---|---|")
    for tag, r in c["runs"].items():
        t = r["decision_states_and_pairs"]
        bp = r["by_population"]
        print("| %s | %d | %d | %d | %s |" % (tag, t["decisions"], t["pairs_enforced"], t["pairs_with_gt"],
              " | ".join("%d / %d (%d)" % (bp[p]["items"], bp[p]["logs"], bp[p]["evaluable_cells"]) for p in ("PD7", "SD1_7", "PD", "NIP"))))
    print("\n### PD7 items by group, items / logs (two-wheeler split: bicycle class / motorcycle class)\n")
    print("| Run | car | pedestrian | two-wheeler | (bicycle / motorcycle) | large |")
    print("|---|---|---|---|---|---|")
    for tag, r in c["runs"].items():
        g = r["by_population"]["PD7"]["by_group"]
        tw = r["by_population"]["PD7"]["two_wheeler_by_class"]
        print("| %s | %s | (%d / %d) | %s |" % (tag, " | ".join("%d / %d" % (g[x]["items"], g[x]["logs"]) for x in ("car", "pedestrian", "two_wheeler")),
              tw["bicycle"]["items"], tw["motorcycle"]["items"], "%d / %d" % (g["large"]["items"], g["large"]["logs"])))
    print("\n### Car, PD7 cells (group | axis | motion, pooled over range): PD7 items / logs, of which in-path items / logs\n")
    tags = list(c["runs"])
    print("| Cell | " + " | ".join(tags) + " |")
    print("|---|" + "---|" * len(tags))
    cells = list(next(iter(c["runs"].values()))["car_PD7_cells_with_inpath"])
    for cell in cells:
        row = []
        for tag in tags:
            v = c["runs"][tag]["car_PD7_cells_with_inpath"][cell]
            row.append("%d / %d; in-path %d / %d" % (v["PD7_items"], v["PD7_logs"], v["inpath_items"], v["inpath_logs"]))
        print("| %s | %s |" % (cell, " | ".join(row)))
    print("\n### Evaluable PD7 / SD1_7 / PD cells (>= 39 logs) per run\n")
    for tag, r in c["runs"].items():
        for p in ("PD7", "SD1_7", "PD"):
            ev = [k for k, v in r["by_population"][p]["by_cell"].items() if v["evaluable_39_logs"]]
            print("- %s %s: %d cells: %s" % (tag, p, len(ev), ", ".join(ev)))


if __name__ == "__main__":
    main()
