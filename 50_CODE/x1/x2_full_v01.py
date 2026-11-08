#!/usr/bin/env python3
"""X2 confirmatory replication on nuScenes train (Claude line, v01, 30 Oct 2026). Implements 40_PROTOCOL/X2_PREREGISTRATION_v01.md.
Reuses the X1 v02 machinery (x1_lib_v02, x1_full_v02 functions) at band level 0.95 (single primary family h2s) and adds the
H1/H2 decision and the H3 report. Refuses to run unless the X2 pre-registration and every file in its section 0 match.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_lib_v02 as L  # noqa: E402
import x1_full_v02 as F  # noqa: E402

F.LEVEL = 0.95
F.DELTA_LO_Q = 0.025
H1_CELLS = ["car|<20|lat", "car|20-40|lat"]


def h3_report(rows, ne, cells):
    out = {}
    for key in H1_CELLS:
        g = "|".join(key.split("|")[:2])
        nv = ne.get(g)
        if not nv:
            continue
        k = nv["ANEES"] / 2.0
        lat, lon = tuple(key.split("|")), (key.split("|")[0], key.split("|")[1], "long")
        rep = {"ANEES": nv["ANEES"], "k": k}
        d = cells.get(lat)
        if d is not None and d["n"]:
            rep["lat_exc_after_nees_scaling"] = float(np.mean(d["D"] > L.Z95 * np.sqrt(k * d["V"] + d["SA"] ** 2)))
        d = cells.get(lon)
        if d is not None and d["n"]:
            rep["long_extra_margin_median_m"] = float(np.median(L.Z95 * (np.sqrt(k * d["V"] + d["SA"] ** 2) - np.sqrt(d["V"] + d["SA"] ** 2))))
        out[key] = rep
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--oc", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--expected-tokens", type=int, default=28130)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    pre_sha, settings = F.check_freeze(a.prereg)
    logit = settings.get("band", "linear") == "logit"
    t0 = time.time()
    rng = np.random.default_rng(L.SEED)
    res = {"prereg_sha256": pre_sha, "band": "logit" if logit else "linear", "band_level": F.LEVEL}
    tokens, recs = set(), []
    for w in a.workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r["status_X1_gates"] == "PASS", "export worker failed Q0: " + w
        pf = json.load(open(os.path.join(w, "x1_per_frame.json")))
        wt = [p["token"] for p in pf if not p.get("error")]
        assert not (set(wt) & tokens), "token exported twice"
        tokens |= set(wt)
        recs += L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
    assert len(tokens) == a.expected_tokens, "union does not cover the expected tokens"
    samples, gtb, racks = L.load_gt(a.gt)
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(os.path.join(a.meta, "scene.json")))}
    rows, pst = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
    rows4, _ = L.build_table(recs, samples, gtb, racks, gate=4.0, scene_log=scene_log)
    rowsr, _ = L.build_table(recs, samples, gtb, racks, persistent=False, scene_log=scene_log)
    res["pairing"] = pst
    c6 = [r["c6"] for r in rows if r["c6"] is not None and not r["first"]]
    res["Q0"] = {"tokens": len(tokens), "records": len(recs), "C6_max_abs_m_non_birth": float(max(c6)) if c6 else None}
    res["Q1_paired_share_of_inpath"] = pst.get("paired_inpath", 0) / max(pst.get("inpath_records", 1), 1)
    scene_names = sorted({r["scene"] for r in rows})
    logs = sorted(set(scene_log[s] for s in scene_names))
    W = L.boot_weights(len(scene_names), F.B_EXC, rng)
    WL = L.log_cluster_weights(np.array([logs.index(scene_log[s]) for s in scene_names]), len(logs), F.B_EXC, rng)
    oc = json.load(open(a.oc))
    pred = L.load_horizon(a.horizon)
    hr, hst = L.build_horizon_rows(rows, pred, samples, gtb, racks)
    hr4, _ = L.build_horizon_rows(rows4, pred, samples, gtb, racks)
    hrr, _ = L.build_horizon_rows(rowsr, pred, samples, gtb, racks)
    res["horizon_rows"] = hst
    fam = F.family("h2s", hr, hr4, hrr, scene_names, scene_log, logit, W, WL, rng, oc.get("h2s", oc))
    res["family_h2s"] = fam
    print("h2s %.0f s" % (time.time() - t0), flush=True)
    # H1 / H2 decision
    prim, sens, pr = fam["primary"], fam["sensitivities"], fam["prices"]["cells"]
    dec = []
    for key in H1_CELLS:
        rb = key.split("|")[1]
        lon = "car|%s|long" % rb
        v = prim.get(key, {})
        h1 = {"cell": key, "eligible": key in fam["eligible"], "a1_fails": v.get("verdict") == "FAILS",
              "a2_material": key in pr and pr[key]["Delta_m"]["lo_bonf"] > L.H0,
              "a3_sigma_0.20": sens["sigma_a=0.20"].get(key, {}).get("verdict") == "FAILS",
              "a4_contested_excluded": sens["contested_excluded"].get(key, {}).get("verdict") == "FAILS",
              "a5_truth_oriented": sens["truth_oriented_not_measurable"].get(key, {}).get("verdict") == "FAILS"}
        h1["H1"] = bool(h1["eligible"] and h1["a1_fails"] and h1["a2_material"] and h1["a3_sigma_0.20"] and h1["a4_contested_excluded"] and h1["a5_truth_oriented"])
        h2 = {"long_cell": lon, "long_overcovers": prim.get(lon, {}).get("verdict") == "OVERCOVERS",
              "s_lat_lo": pr.get(key, {}).get("s_needed", {}).get("ci", [None])[0],
              "s_long_hi": pr.get(lon, {}).get("s_needed", {}).get("ci", [None, None])[1]}
        h2["opposite_directions"] = bool(h2["s_lat_lo"] is not None and h2["s_long_hi"] is not None and h2["s_lat_lo"] > 1 and h2["s_long_hi"] < 1)
        h2["H2"] = bool(h2["long_overcovers"] and h2["opposite_directions"])
        dec.append({"H1": h1, "H2": h2, "holds": bool(h1["H1"] and h2["H2"])})
    res["G1_X2"] = {"by_range": dec, "holds": any(d["holds"] for d in dec)}
    cells, _, _ = L.cell_items(hr, sigma_a=0.10)
    res["H3_nees_scaling"] = h3_report(hr, fam["nees"], {c: cells[c] for c in L.CELLS})
    res["family_t0_descriptive"] = F.family("t0", rows, rows4, rowsr, scene_names, scene_log, logit, W, WL, rng, oc.get("t0", oc))
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res["G1_X2"], default=float)[:1500], flush=True)


if __name__ == "__main__":
    sys.exit(main())
