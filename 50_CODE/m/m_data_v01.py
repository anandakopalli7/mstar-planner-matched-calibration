#!/usr/bin/env python3
"""Method-stage data loader v01 (Claude line, 31 Oct 2026). Loads one tracker setting on one split: integrity checks (Q0),
the X2 record table (persistent pairing, 2 m gate), motion index, and the item arrays at 1, 2 and 4 s.
With outcomes=False no residual is computed (pre-freeze counts)."""
import json
import os

import m_lib_v01 as M

L = M.L


def load_split(workers, gt, meta, horizon, experiment, outcomes=True):
    tokens, recs = set(), []
    for w in workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r["status_X1_gates"] == "PASS", "export worker failed its gates: " + w
        assert r["resolved_config"].get("experiment_id") == experiment, "wrong tracker setting in " + w
        pf = json.load(open(os.path.join(w, "x1_per_frame.json")))
        wt = [p["token"] for p in pf if not p.get("error")]
        assert not (set(wt) & tokens), "token exported twice"
        tokens |= set(wt)
        recs += L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
    samples, gtb, racks = L.load_gt(gt)
    assert tokens == set(samples), "exported tokens differ from the split's samples"
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    scene_names = sorted({s["scene"] for s in samples.values()})
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    c6 = [r["c6"] for r in rows if r["c6"] is not None and not r["first"]]
    info = {"tokens": len(tokens), "records": len(recs), "scenes": len(scene_names),
            "logs": len(set(scene_log[s] for s in scene_names)), "pairing": pst,
            "C6_max_abs_m_non_birth": float(max(c6)) if c6 else None, "C6_pass": bool(c6) and max(c6) <= 1e-6}
    mi = M.motion_index(recs, samples)
    del recs
    pred = M.load_horizon_all(horizon, {(r["scene"], r["k"], r["tid"]) for r in rows})
    out, hst = {}, {}
    for h, steps in M.HSTEPS.items():
        hr, hst[h] = L.build_horizon_rows(rows, pred, samples, gtb, racks, key=h, steps=steps)
        out[h] = M.build_items(hr, mi, scene_names, scene_log, outcomes)
        del hr
    info["horizon_rows"] = hst
    return out, info, scene_names, scene_log
