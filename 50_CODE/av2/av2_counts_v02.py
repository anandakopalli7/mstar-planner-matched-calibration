#!/usr/bin/env python3
"""av2_counts_v02: K8 decision-mode item counts on the AV2 stage-A caches (Claude line, 2 Nov 2026). Design:
AV2_TRACKER_PORT_DESIGN_v02.md section 12.4; D16 Choice 13 (K8 decision-mode item counts are allowed before the freeze).

Input: per tracker x detector, the k8_items_v04 --av2 --counts-only output (its error fields are NaN and never read here)
and its summary. Output (AV2_TRACKER_COUNTS_v02.json), per run:
  * decision states, pairs considered / enforced at the reference margin 0 / with the paired instance annotated at k + h
    (the visibility condition, existence only);
  * K8 items (ref_relied: one per enforced visible pair, the axis the planner relies on at the reference pose) per
    population PD7 (all), SD1_7 (gap at the reference pose <= 5 m), PD (in-path), NIP (not in-path), per group, per L0
    stratum (group x predicted range x axis x motion) and per K6 evaluation cell (group | axis | motion, pooled over range;
    k6_analyse_v02.cell_family), each with items, logs (= scenes on AV2) and the evaluability flag of the K8 exploratory
    analysis (>= 39 scenes and >= 8 logs, which on AV2 is >= 39 logs);
  * the two-wheeler group split by tracking class (bicycle = BICYCLIST, motorcycle = MOTORCYCLIST; design 12.1);
  * the car in-path table per PD7 cell.
Arm-dependent decision-mode records are not counted (design 12.4).
Usage: python -I -B av2_counts_v02.py --runs <tag>=<items npz> ... --caches <tag>=<stage-A dir> ... --out <json>
"""
import argparse
import datetime as dt
import json
import os
import sys
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
GROUPS = ["car", "pedestrian", "two_wheeler", "large"]
RANGES = ["<20", "20-40", ">=40"]
AXES = ["long", "lat"]
MOTIONS = ["static", "straight", "turning", "new"]
MIN_SCENES, MIN_LOGS = 39, 8
GAP_NEAR = 5.0
CLASSES = ["car", "truck", "bus", "trailer", "pedestrian", "motorcycle", "bicycle"]


def decode_l0(l0):
    m = l0 % 4
    a = (l0 // 4) % 2
    gr = l0 // 8
    return gr // 3, gr % 3, a, m


def cell_family():
    return [("%s|%s|%s" % (GROUPS[g], AXES[a], MOTIONS[m]), [((g * 3 + r) * 2 + a) * 4 + m for r in range(3)])
            for g in range(4) for a in range(2) for m in range(4)]


def one_run(items_path, cache_dir):
    z = np.load(items_path)
    names = [str(x) for x in z["scene_names"]]
    logs = [str(x) for x in z["scene_logs"]]
    it = {k[5:]: z[k] for k in z.files if k.startswith("item_")}
    rc = {k[4:]: z[k] for k in z.files if k.startswith("rec_")}
    assert np.isnan(it["D"]).all() and np.isnan(rc["dx"]).all(), "items carry an error value: not a counts-only file"
    summ = json.load(open(items_path.replace(".npz", "_summary.json")))
    rel = it["ref_relied"].astype(bool)
    pops = {"PD7": rel, "SD1_7": rel & (it["gap"] <= GAP_NEAR), "PD": rel & it["inpath"].astype(bool), "NIP": rel & ~it["inpath"].astype(bool)}
    log_of = np.array(logs)[it["s"]]
    # tracking class of each item's track (the two-wheeler split): rec row -> cache tr_cls, via the pair id
    cls_of_scene = {}
    for si, sc in enumerate(names):
        cls_of_scene[si] = np.load(os.path.join(cache_dir, sc + ".npz"))["tr_cls"]
    pair_cls = {}
    for s_, p_, row in zip(rc["s"], rc["pair"], rc["row"]):
        pair_cls[(int(s_), int(p_))] = int(cls_of_scene[int(s_)][int(row)])
    it_cls = np.array([pair_cls[(int(s_), int(p_))] for s_, p_ in zip(it["s"], it["pair"])], int) if len(it["s"]) else np.zeros(0, int)
    cells = cell_family()
    l0_to_cell = np.full(96, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    out = {"items_file": os.path.abspath(items_path), "items_sha256": summ.get("out_sha256"), "stamp": str(z["stamp"]),
           "logs": len(names), "decision_states_and_pairs": summ["totals"], "items_all_axes": int(len(it["s"])),
           "items_ref_relied": int(rel.sum()), "by_population": {}}
    for p, m_ in pops.items():
        d = {"items": int(m_.sum()), "logs": int(len(np.unique(log_of[m_]))), "by_group": {}, "by_cell": {}, "by_l0": {}}
        g_of = it["g"][m_]
        for gi, gname in enumerate(GROUPS):
            sel = g_of == gi
            d["by_group"][gname] = {"items": int(sel.sum()), "logs": int(len(np.unique(log_of[m_][sel])))}
        tw = m_ & (it["g"] == 2)
        d["two_wheeler_by_class"] = {c: {"items": int((tw & (it_cls == CLASSES.index(c))).sum()),
                                         "logs": int(len(np.unique(log_of[tw & (it_cls == CLASSES.index(c))])))} for c in ("bicycle", "motorcycle")}
        cj = l0_to_cell[it["l0"][m_]]
        lg = log_of[m_]
        for j, (cname, _) in enumerate(cells):
            sel = cj == j
            n, nl = int(sel.sum()), int(len(np.unique(lg[sel])))
            if n:
                d["by_cell"][cname] = {"items": n, "logs": nl, "evaluable_39_logs": nl >= MIN_SCENES and nl >= MIN_LOGS}
        l0s = it["l0"][m_]
        for l0 in np.unique(l0s):
            g_, r_, a_, mo = decode_l0(int(l0))
            sel = l0s == l0
            d["by_l0"]["%s|%s|%s|%s" % (GROUPS[g_], RANGES[r_], AXES[a_], MOTIONS[mo])] = {"items": int(sel.sum()), "logs": int(len(np.unique(lg[sel])))}
        d["evaluable_cells"] = sum(1 for v in d["by_cell"].values() if v["evaluable_39_logs"])
        out["by_population"][p] = d
    # car: in-path items per PD7 cell (every PD7 cell of the car group, with its in-path part)
    car = {}
    for j, (cname, _) in enumerate(cells):
        if not cname.startswith("car|"):
            continue
        sel7 = pops["PD7"] & (l0_to_cell[it["l0"]] == j)
        selp = pops["PD"] & (l0_to_cell[it["l0"]] == j)
        car[cname] = {"PD7_items": int(sel7.sum()), "PD7_logs": int(len(np.unique(log_of[sel7]))),
                      "inpath_items": int(selp.sum()), "inpath_logs": int(len(np.unique(log_of[selp])))}
    out["car_PD7_cells_with_inpath"] = car
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", nargs="+", required=True)
    ap.add_argument("--caches", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    caches = dict(x.split("=", 1) for x in a.caches)
    res = {"created_utc": dt.datetime.now(dt.timezone.utc).isoformat(), "script": "av2_counts_v02",
           "design": "50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v02.md section 12", "decision": "90_DECISIONS/D16_DELEGATED_CHOICES_v03.md Choice 13",
           "outcome_statement": ("counts only: the items' error fields are NaN (k8_items_v04 --counts-only) and are never read; no residual, "
                                 "projected error, U, exceedance, margin, infeasibility, V2, TTV, NEES or coverage computed"),
           "populations": {"PD7": "ref_relied items (one per enforced pair whose paired instance is annotated at k + h)",
                           "SD1_7": "PD7 with the relied axis' gap at the reference pose <= 5 m", "PD": "PD7 in the method's in-path set",
                           "NIP": "PD7 not in-path"},
           "runs": {}}
    for x in a.runs:
        tag, path = x.split("=", 1)
        res["runs"][tag] = one_run(path, caches[tag])
    json.dump(res, open(a.out, "w"), indent=1)
    for tag, r in res["runs"].items():
        print(tag, {p: (v["items"], v["logs"], v["evaluable_cells"]) for p, v in r["by_population"].items()})


if __name__ == "__main__":
    sys.exit(main())
