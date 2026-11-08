"""pod_join2hz_v01 (QCNet arm, 2 Nov 2026): join coverage of the QCNet rows against the 2 Hz tracker arm's paired records.

The 2 Hz paired records are rebuilt with the tracker helper's own code, used read-only from a copy of the work tree on the
pod (50_CODE/av2/av2_counts_v01.py's run_one steps: m_data_v04.load_export_v2 -> x1_lib_v03.load_gt -> x1_lib_v03.build_table
with keep_unpaired=True -> av2_counts_v01.horizon_availability, existence only). Only keys and labels are kept:
(sample token at k, GT instance token, analysis group, in-path flag, k, horizon status). build_table's association flags
(resid_gt_gate, contested) are not read. Then counts of these keys found in each QCNet file (GT and tracker histories).
Outcome-blind: association at time k and existence at k + 4 only; no position after k is read; no error is computed.
Usage: python pod_join2hz_v01.py --wroot <copy of W> --tracker t1|t3 --exports <worker dirs...> --gt <gt json>
       --qcnet-gt <npz> --qcnet-trk <npz> --out <json>
"""
import argparse
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--wroot", required=True)
    ap.add_argument("--tracker", required=True, choices=["t1", "t3"])
    ap.add_argument("--exports", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--qcnet-gt", dest="qgt", required=True)
    ap.add_argument("--qcnet-trk", dest="qtrk", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    sys.path.insert(0, os.path.join(a.wroot, "50_CODE", "av2"))
    import av2_counts_v01 as AC  # the helper's module (read-only copy); imports av2_common_v01, m_data_v04, m_lib_v04, x1_lib_v03
    C, MD, L = AC.C, AC.MD, AC.L
    exp = AC.EXPERIMENTS[a.tracker]
    recs = []
    for w in a.exports:
        er = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert er["status_X1_gates"] == "PASS" and er["resolved_config"]["experiment_id"] == exp and er["detector"] == "lt3d", w
        rw, _ = MD.load_export_v2(os.path.join(w, "x1_tracks.jsonl.gz"), exp)
        recs += rw
    samples, gtb, racks = L.load_gt(a.gt)
    logs = sorted({s["scene"] for s in samples.values()})
    frames_per_log = defaultdict(lambda: {"n": 0, "tokens": {}})
    for s in samples.values():
        frames_per_log[s["scene"]]["tokens"][s["index"]] = s["token"]
    for lg in frames_per_log:
        frames_per_log[lg]["n"] = len(frames_per_log[lg]["tokens"])
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log={lg: lg for lg in logs}, keep_unpaired=True)
    del recs
    ann_keys = {(tok, x["instance_token"]) for tok, anns in gtb.items() for x in anns if x["num_pts"] >= 1}
    paired = [r for r in rows if r["paired"]]
    hav = AC.horizon_availability([(r["scene"], r["k"], r["inst"]) for r in paired], frames_per_log, ann_keys)
    keys = []
    for r in paired:
        g = C.ANALYSIS_GROUP[r["name"]]
        if g not in ("car", "pedestrian", "cyclist"):
            continue
        keys.append((frames_per_log[r["scene"]]["tokens"][r["k"]], r["inst"], g, bool(r["inpath"]), int(r["k"]), hav[(r["scene"], r["k"], r["inst"])]))
    del rows
    qg = np.load(a.qgt, allow_pickle=False)
    qt = np.load(a.qtrk, allow_pickle=False)
    kg = set(zip(qg["sample_token"].tolist(), qg["instance_token"].tolist()))
    kt = set(zip(qt["sample_token"].tolist(), qt["instance_token"].tolist()))
    tab = defaultdict(lambda: {"audit": 0, "in_gt_source": 0, "in_trk_source": 0, "in_both": 0})
    for tok, inst, g, inp, k, hz in keys:
        for lab in ("%s|all|%s" % (g, hz), "%s|%s|%s" % (g, "inpath" if inp else "not_inpath", hz), "ALL|all|%s" % hz):
            d = tab[lab]
            d["audit"] += 1
            ig, it = (tok, inst) in kg, (tok, inst) in kt
            d["in_gt_source"] += ig
            d["in_trk_source"] += it
            d["in_both"] += ig and it
    rec = {"tracker": a.tracker, "detector": "lt3d", "experiment": exp, "paired_records_3_groups": len(keys),
           "association_counts": {k: v for k, v in pst.items()}, "coverage": {k: dict(v) for k, v in sorted(tab.items())},
           "note": "audit = paired records (2 Hz, build_table, 2 m gate) of car/pedestrian/cyclist; label group|population|horizon status; "
                   "in_*_source = the (sample token, instance token) key has a QCNet row from that history source",
           "seconds": time.time() - t0}
    json.dump(rec, open(a.out, "w"), indent=1)
    np.savez_compressed(a.out.replace(".json", "_keys.npz"), sample_token=np.array([k[0] for k in keys]), instance_token=np.array([k[1] for k in keys]),
                        group=np.array([k[2] for k in keys]), inpath=np.array([k[3] for k in keys]), k=np.array([k[4] for k in keys]),
                        horizon=np.array([k[5] for k in keys]))
    print(json.dumps({x: rec["coverage"].get(x) for x in ("ALL|all|available", "car|inpath|available", "pedestrian|all|available", "cyclist|all|available")}), flush=True)
    print("JOIN2HZ DONE", flush=True)


if __name__ == "__main__":
    main()
