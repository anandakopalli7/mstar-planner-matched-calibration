#!/usr/bin/env python3
"""Method-stage data loader v03 (Claude line, 31 Oct 2026). Loads one tracker setting on one split: integrity checks (Q0),
the X2 record table (persistent pairing, 2 m gate), motion index, and the item arrays at 1, 2 and 4 s.
Changes from v02 (review R07b):
- N-C1: Poly-MOT's CTRA model writes (speed, acceleration) into the exported velocity field. For that setting, every record
  with a 10-dimensional state (CTRA: x y z w l h v a theta omega) gets (vx, vy) = v (cos theta, sin theta) from its own state
  before anything uses the velocity: the in-path test, speed and heading rates. CA records (13-dimensional) and the CANMOT
  settings are unchanged.
- N-m10: the peak working set is read through K32GetProcessMemoryInfo with declared argument and return types.
In memory, the counts run also evaluates build_horizon_rows' 2 m drift flag; it is never stored."""
import gzip
import json
import math
import os

import m_lib_v03 as M

L = M.L
POLYMOT = "paper/baseline/poly_mot"


def peak_mb():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t), ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        k32 = ctypes.WinDLL("kernel32")
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        f = k32.K32GetProcessMemoryInfo
        f.argtypes = [wintypes.HANDLE, ctypes.POINTER(PMC), wintypes.DWORD]
        f.restype = wintypes.BOOL
        p = PMC()
        p.cb = ctypes.sizeof(PMC)
        return round(p.PeakWorkingSetSize / 2 ** 20) if f(k32.GetCurrentProcess(), ctypes.byref(p), p.cb) else None
    except Exception:
        return None


def load_export_v2(path, experiment):
    """x1_lib_v03.load_export, field for field, plus the Poly-MOT CTRA velocity correction. Returns (records, corrected)."""
    recs, fixed = [], 0
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            c = r["cov9"]
            vx, vy = r["velocity"][0], r["velocity"][1]
            st = r.get("state10")
            if experiment == POLYMOT and st is not None and len(st) == 10:
                vx, vy = st[6] * math.cos(st[8]), st[6] * math.sin(st[8])
                fixed += 1
            recs.append({"scene": r["scene"], "k": r["frame_id"], "tid": r["tracking_id"], "name": r["tracking_name"],
                         "x": r["translation"][0], "y": r["translation"][1], "w": r["size"][0], "l": r["size"][1],
                         "yaw": L.quat_yaw(r["rotation"]), "vx": vx, "vy": vy,
                         "S": (c[0][0], c[0][1], c[1][1]),
                         "c6": (abs(r["translation"][0] - st[0]) + abs(r["translation"][1] - st[1])) if st else None})
    return recs, fixed


def load_split(workers, gt, meta, horizon, experiment, outcomes=True):
    tokens, recs, fixed = set(), [], 0
    for w in workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r["status_X1_gates"] == "PASS", "export worker failed its gates: " + w
        assert r["resolved_config"].get("experiment_id") == experiment, "wrong tracker setting in " + w
        pf = json.load(open(os.path.join(w, "x1_per_frame.json")))
        wt = [p["token"] for p in pf if not p.get("error")]
        assert not (set(wt) & tokens), "token exported twice"
        tokens |= set(wt)
        rw, fw = load_export_v2(os.path.join(w, "x1_tracks.jsonl.gz"), experiment)
        recs += rw
        fixed += fw
    samples, gtb, racks = L.load_gt(gt)
    assert tokens == set(samples), "exported tokens differ from the split's samples"
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(meta, "scene.json")))}
    scene_names = sorted({s["scene"] for s in samples.values()})
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    c6 = [r["c6"] for r in rows if r["c6"] is not None and not r["first"]]
    info = {"tokens": len(tokens), "records": len(recs), "ctra_velocity_corrected": fixed, "scenes": len(scene_names),
            "logs": len(set(scene_log[s] for s in scene_names)), "pairing": pst,
            "C6_max_abs_m_non_birth": float(max(c6)) if c6 else None, "C6_pass": bool(c6) and max(c6) <= 1e-6}
    mi = M.motion_index(recs, samples)
    del recs
    rows = [r for r in rows if r["inpath"]]
    info["paired_inpath_rows"] = len(rows)
    pred = M.load_horizon_all(horizon, {(r["scene"], r["k"], r["tid"]) for r in rows})
    out, hst = {}, {}
    for h, steps in M.HSTEPS.items():
        hr, hst[h] = L.build_horizon_rows(rows, pred, samples, gtb, racks, key=h, steps=steps)
        out[h] = M.build_items(hr, mi, scene_names, scene_log, outcomes)
        del hr
    info["horizon_rows"] = hst
    info["peak_working_set_mb_after_load"] = peak_mb()
    return out, info, scene_names, scene_log
