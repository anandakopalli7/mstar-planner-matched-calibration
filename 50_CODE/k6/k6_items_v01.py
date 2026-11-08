#!/usr/bin/env python3
"""K6 calibration items (Claude line, v01, 31 Oct 2026). The method stage's loader (m_data_v04.load_split) and item builder
(m_lib_v04.build_items) at all 8 planner steps (0.5 s to 4 s) instead of 1, 2 and 4 s, on the deployed tracker output:
only tracks with score >= SCORE_MIN (0.4) are paired and itemised, while the motion features use each track's full
exported history (the tracker keeps it whatever the output threshold). load_split_k6 below is load_split with exactly
those two changes; every other function is the method stage's, unchanged. Writes one npz per step.
Run in the CANMOT environment:
  python -B k6_items_v01.py --experiment <id> --workers <dirs...> --gt <gt json> --meta <v1.0-trainval> --horizon <horizon8 jsonl.gz>
         --out <dir> --tag <t1_train|...>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m"))
import m_lib_v04 as M  # noqa: E402
import m_data_v04 as MD  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from k6_sim_v01 import SCORE_MIN  # noqa: E402

HSTEPS8 = {"h0p5s": 1, "h1s": 2, "h1p5s": 3, "h2s": 4, "h2p5s": 5, "h3s": 6, "h3p5s": 7, "h4s": 8}
ITEM_KEYS = ("s", "lg", "g", "r", "a", "spd", "om", "omv", "omc", "chord", "V", "contested", "D")
REC_KEYS = ("s", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "contested")


def scores(path):
    import gzip
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return [json.loads(line)["tracking_score"] for line in f]


def load_split_k6(workers, gt, meta, horizon, experiment, outcomes=True):
    """m_data_v04.load_split with (1) the motion index from every record and (2) pairing and items from the records with
    tracking score >= SCORE_MIN only."""
    L = M.L
    tokens, recs, fixed = set(), [], 0
    for w in workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r["status_X1_gates"] == "PASS", "export worker failed its gates: " + w
        assert r["resolved_config"].get("experiment_id") == experiment, "wrong tracker setting in " + w
        pf = json.load(open(os.path.join(w, "x1_per_frame.json")))
        wt = [p["token"] for p in pf if not p.get("error")]
        assert not (set(wt) & tokens), "token exported twice"
        tokens |= set(wt)
        rw, fw = MD.load_export_v2(os.path.join(w, "x1_tracks.jsonl.gz"), experiment)
        sw = scores(os.path.join(w, "x1_tracks.jsonl.gz"))
        assert len(sw) == len(rw)
        for x, sc in zip(rw, sw):
            x["score"] = sc
        recs += rw
        fixed += fw
    samples, gtb, racks = L.load_gt(gt)
    assert tokens == set(samples), "exported tokens differ from the split's samples"
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    scene_names = sorted({s["scene"] for s in samples.values()})
    mi = M.motion_index(recs, samples)
    kept = [r for r in recs if r["score"] >= SCORE_MIN]
    info = {"tokens": len(tokens), "records": len(recs), "records_kept": len(kept), "score_min": SCORE_MIN,
            "ctra_velocity_corrected": fixed, "scenes": len(scene_names), "logs": len(set(scene_log[s] for s in scene_names))}
    del recs
    rows, pst = L.build_table(kept, samples, gtb, racks, scene_log=scene_log)
    info["pairing"] = pst
    rows = [r for r in rows if r["inpath"]]
    info["paired_inpath_rows"] = sum(1 for r in rows if r["paired"])
    pred = M.load_horizon_all(horizon, {(r["scene"], r["k"], r["tid"]) for r in rows})
    out, hst = {}, {}
    for h, steps in M.HSTEPS.items():
        hr, hst[h] = L.build_horizon_rows(rows, pred, samples, gtb, racks, key=h, steps=steps)
        out[h] = M.build_items(hr, mi, scene_names, scene_log, outcomes)
        del hr
    info["horizon_rows"] = hst
    info["peak_working_set_mb_after_load"] = MD.peak_mb()
    return out, info, scene_names, scene_log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--experiment", required=True)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tag", required=True)
    a = ap.parse_args()
    t0 = time.time()
    M.HSTEPS = dict(HSTEPS8)
    out, info, scene_names, scene_log = load_split_k6(a.workers, a.gt, a.meta, a.horizon, a.experiment)
    os.makedirs(a.out, exist_ok=True)
    summary = {"tag": a.tag, "experiment": a.experiment, "info": info, "scenes": len(scene_names), "steps": {}}
    for h, (items, recs) in out.items():
        arr = {"item_" + k: items[k] for k in ITEM_KEYS}
        arr.update({"rec_" + k: recs[k] for k in REC_KEYS})
        arr["scene_log_idx"] = items["scene_log_idx"]
        np.savez_compressed(os.path.join(a.out, "items_%s_%s.npz" % (a.tag, h)), **arr)
        summary["steps"][h] = {"items": int(len(items["D"])), "records": int(len(recs["dx"]))}
    summary["scene_names"] = scene_names
    summary["scene_log"] = {s: scene_log[s] for s in scene_names}
    summary["seconds"] = round(time.time() - t0, 1)
    json.dump(summary, open(os.path.join(a.out, "items_%s_summary.json" % a.tag), "w"), indent=1, default=str)
    print(json.dumps({k: summary[k] for k in ("tag", "scenes", "steps", "seconds")}))
    print("K6 ITEMS DONE")


if __name__ == "__main__":
    main()
