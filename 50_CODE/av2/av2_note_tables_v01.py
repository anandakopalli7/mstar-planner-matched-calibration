#!/usr/bin/env python3
"""av2_note_tables_v01: prints the Markdown tables of AV2_TRACKER_NOTE_v01.md from the stored metric and count JSONs
(Claude line, 1 Nov 2026), so that no number in the note is transcribed by hand. Reads only outputs of this port.
Usage: python -I -B av2_note_tables_v01.py > tables.md
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import av2_common_v01 as C  # noqa: E402

R = os.path.join(C.W_ROOT, "60_RESULTS", "av2_trk")
T = os.path.join(C.W_ROOT, "30_DATA", "av2_trk_v01")
COMBOS = ["t1_lt3d", "t3_lt3d", "t2_lt3d", "t1_voxelnext", "t3_voxelnext", "t2_voxelnext"]
NAMES = {"t1": "T1 CANMOT sc", "t2": "T2 CANMOT sample/trainval", "t3": "T3 Poly-MOT", "lt3d": "LT3D CenterPoint", "voxelnext": "VoxelNeXt"}


def f(x, d=3):
    return "–" if x is None else ("%.*f" % (d, x) if isinstance(x, float) and x == x else str(x))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print("### Tracking metrics (nuScenes protocol; AMOTA over 40 recall thresholds, the rest at the best-MOTA threshold)\n")
    print("| Tracker × detector | Class | AMOTA | MOTA | Recall | TP | FP | FN | IDS | FRAG | GT boxes |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for cb in COMBOS:
        p = os.path.join(R, "metrics", "AV2_metrics_%s.json" % cb)
        if not os.path.exists(p):
            continue
        m = json.load(open(p))
        t, d = cb.split("_")
        for cls in ("car", "pedestrian", "bicycle", "truck", "bus", "trailer", "motorcycle"):
            r = m["per_class"].get(cls)
            if not r:
                continue
            print("| %s × %s | %s | %s | %s | %s | %d | %d | %d | %d | %d | %d |" % (
                NAMES[t], NAMES[d], cls if cls != "bicycle" else "cyclist (bicycle class)", f(r.get("amota")), f(r.get("mota")),
                f(r.get("recall")), r.get("tp", 0), r.get("fp", 0), r.get("fn", 0), r.get("ids", 0), r.get("frag", 0), r["gt_boxes"]))
    for lab in ("T1 v01", "T1 v03"):
        p = os.path.join(R, "metrics", "NUSC_VAL_%s_metric_validation_%s.json" % tuple(lab.split()))
        if os.path.exists(p):
            m = json.load(open(p))
            rc = m.get("reference_check", m)
            neq = [(c, k) for c, v in rc.get("per_class", {}).items() for k, x in v.items() if not x["equal"]]
            print("\nnuScenes %s validation of the metric code: classes %s, all equal = %s; unequal entries: %s" % (
                lab, sorted(rc.get("per_class", {})), rc.get("all_equal"), neq[:20]))
    p = os.path.join(R, "AV2_TRACKER_COUNTS_v01.json")
    if not os.path.exists(p):
        return
    c = json.load(open(p))
    print("\n### Headline: car, in-path, paired items at the current-estimate geometry (t = 0 family), items / logs\n")
    print("| Tracker × detector | < 20 m | 20–40 m | ≥ 40 m |")
    print("|---|---|---|---|")
    for cb in COMBOS:
        h = c["headline_car_inpath_paired_items_t0_by_range"].get(cb)
        if h:
            t, d = cb.split("_")
            print("| %s × %s | %s |" % (NAMES[t], NAMES[d], " | ".join("%d / %d" % (h[r]["items"], h[r]["logs"]) for r in ("<20", "20-40", ">=40"))))
    print("\n### Frames, tracks, records, association (counts)\n")
    print("| Tracker × detector | frames | tracks | export records | records k ≥ 1 | in-path records | paired in-path | unpaired | censored at k | id switches | paired records: k+4 available / censored / no k+4 frame |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for cb in COMBOS:
        r = c["runs"].get(cb)
        if not r:
            continue
        a = r["association"]
        hz = r["records_by_horizon_status"]
        t, d = cb.split("_")
        print("| %s × %s | %d | %d | %d | %d | %d | %d | %d | %d | %d | %d / %d / %d |" % (
            NAMES[t], NAMES[d], r["frames"], r["tracks"], r["export_records"], a.get("records_k_ge_1", 0), a.get("inpath_records", 0),
            a.get("paired_inpath", 0), a.get("unpaired", 0), a.get("censored", 0), a.get("id_switches", 0),
            hz.get("available", 0), hz.get("censored_at_horizon", 0), hz.get("no_future_frame", 0)))
    print("\n### Paired items by group × range × axis × population (t = 0 geometry), items / logs\n")
    for cb in COMBOS:
        r = c["runs"].get(cb)
        if not r:
            continue
        s = r["summaries"]["paired_items_by_group_range_axis_population"]
        sa = r["summaries"].get("paired_horizon_available_items_by_group_range_axis_population", {})
        t, d = cb.split("_")
        print("\n%s × %s (in brackets: of which the paired object is annotated with points at k + 4)\n" % (NAMES[t], NAMES[d]))
        print("| Group | Axis | Population | < 20 m | 20–40 m | ≥ 40 m |")
        print("|---|---|---|---|---|---|")
        for g in ("car", "pedestrian", "cyclist"):
            for ax in ("long", "lat"):
                for pop in ("inpath", "not_inpath"):
                    cells = []
                    for rg in ("<20", "20-40", ">=40"):
                        k = "|".join((g, rg, ax, pop))
                        x, y = s.get(k, {"items": 0, "logs": 0}), sa.get(k, {"items": 0})
                        cells.append("%d / %d (%d)" % (x["items"], x["logs"], y["items"]))
                    print("| %s | %s | %s | %s |" % (g, ax, pop, " | ".join(cells)))
    print("\n### Car in-path paired items by axis × motion state (t = 0 geometry, pooled over range), items / logs\n")
    print("| Tracker × detector | axis | static | straight | turning | new |")
    print("|---|---|---|---|---|---|")
    for cb in COMBOS:
        r = c["runs"].get(cb)
        if not r:
            continue
        s = r["summaries"]["paired_items_by_group_axis_motion_population"]
        t, d = cb.split("_")
        for ax in ("long", "lat"):
            cells = []
            for mo in ("static", "straight", "turning", "new"):
                x = s.get("|".join(("car", ax, mo, "inpath")), {"items": 0, "logs": 0})
                cells.append("%d / %d" % (x["items"], x["logs"]))
            print("| %s × %s | %s | %s |" % (NAMES[t], NAMES[d], ax, " | ".join(cells)))


if __name__ == "__main__":
    main()
