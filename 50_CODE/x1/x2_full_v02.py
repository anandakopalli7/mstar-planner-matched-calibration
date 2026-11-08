#!/usr/bin/env python3
"""X2 confirmatory replication on nuScenes train, v02 (Claude line, 30 Oct 2026). Implements X2_PREREGISTRATION_v01.md
as amended by review R05 (before the freeze):
  * decision cells only: car <20 m and 20-40 m, lateral and longitudinal (h2s); the 95 % sup-t band spans these 4 cells;
  * fixed test sequence at alpha 0.05: H1 (lateral failure with a2-a5) -> H2 (price of a single lateral-fixing scalar on the
    longitudinal axis, 97.5 % lower bound > h0) -> H3 (NEES-guided correction misdirects); G1(X2) = H1 and H2; H3 gated;
  * decision bounds from B = 2000 scene-bootstrap replicates; zero-SE decision cells count as not shown;
  * every run input is bound to the frozen hash list; peak memory recorded.
Uses x1_lib_v03 (memory-lean, analysis logic identical to v02) through the x1_full_v02 functions.
"""
import argparse
import json
import math
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_lib_v03 as L  # noqa: E402
import x1_full_v02 as F  # noqa: E402

F.L = L
F.LEVEL = 0.95
F.DELTA_LO_Q = 0.025
F.B_PRICE = 2000
DEC = [("car", "<20", "lat"), ("car", "20-40", "lat"), ("car", "<20", "long"), ("car", "20-40", "long")]
BINS = ["<20", "20-40"]
B_DEC = 2000

_orig_analyse = F.analyse_cells


def analyse_decision(rows, sigma_a, rng, n_scenes, scene_names, logit, W, sigma_fn=None, **kw):
    cells, null, thr, elig, _ = _orig_analyse(rows, sigma_a, rng, n_scenes, scene_names, logit, W, sigma_fn=sigma_fn, **kw)
    elig = [c for c in elig if c in DEC]
    return cells, null, thr, elig, F.band_verdicts(cells, elig, n_scenes, thr, W, logit)


F.analyse_cells = analyse_decision


def peak_mb():
    try:
        import ctypes
        from ctypes import wintypes

        class PMC(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD), ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t), ("a", ctypes.c_size_t), ("b", ctypes.c_size_t), ("c", ctypes.c_size_t),
                        ("d", ctypes.c_size_t), ("e", ctypes.c_size_t), ("f", ctypes.c_size_t)]
        k = ctypes.windll.kernel32
        k.GetCurrentProcess.restype = wintypes.HANDLE
        p = PMC()
        p.cb = ctypes.sizeof(PMC)
        k.K32GetProcessMemoryInfo(k.GetCurrentProcess(), ctypes.byref(p), p.cb)
        return round(p.PeakWorkingSetSize / 2 ** 20)
    except Exception:
        return None


def bind_inputs(prereg, paths):
    txt = open(prereg, encoding="utf-8").read()
    block = txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
    hashes = {ln.split("  ", 1)[0] for ln in block.strip().splitlines() if ln.strip() and not ln.startswith(("setting", "(", "#"))}
    assert len(hashes) > 10, "frozen block is empty"
    for p in paths:
        assert L.sha256_path(p) in hashes, "run input not frozen: " + p


def h2_price(cells, key_lat, key_long, rng, n_scenes):
    """Longitudinal over-margin of the single scalar that fixes the lateral cell: median over longitudinal records of
    z (sqrt(s_lat V + sa^2) - sqrt(s_long V + sa^2)); bootstrap over scenes (B_DEC) for its 2.5 % lower bound."""
    def price(cl, cg):
        s_lat = L.inflation_needed(cl["D"], cl["V"], cl["SA"])[0]
        s_long = L.inflation_needed(cg["D"], cg["V"], cg["SA"])[0]
        return float(np.median(L.Z95 * (np.sqrt(s_lat * cg["V"] + cg["SA"] ** 2) - np.sqrt(s_long * cg["V"] + cg["SA"] ** 2)))), s_lat, s_long
    cl, cg = cells[key_lat], cells[key_long]
    p0, sl, sg = price(cl, cg)
    boots = []
    for _ in range(B_DEC):
        cnt = np.bincount(rng.integers(0, n_scenes, n_scenes), minlength=n_scenes)
        bl, bg = L.expand(cl, cnt), L.expand(cg, cnt)
        if bl["n"] == 0 or bg["n"] == 0:
            continue
        boots.append(price(bl, bg)[0])
    return {"price_m": p0, "s_lat": sl, "s_long": sg, "lo_2.5": float(np.quantile(boots, 0.025)), "replicates": len(boots)}


def h3_nees(cells, ne, key_lat, key_long, rng, n_scenes):
    g = "|".join(key_lat[:2])
    nv = ne.get(g)
    if not nv:
        return {"available": False}
    k = nv["ANEES"] / 2.0
    cl, cg = cells[key_lat], cells[key_long]

    def stats(cl_, cg_):
        exc = float(np.mean(cl_["D"] > L.Z95 * np.sqrt(k * (cl_["V"] + cl_["SA"] ** 2))))
        extra = float(np.median(L.Z95 * (np.sqrt(k * (cg_["V"] + cg_["SA"] ** 2)) - np.sqrt(cg_["V"] + cg_["SA"] ** 2))))
        return exc, extra
    e0, x0 = stats(cl, cg)
    be, bx = [], []
    for _ in range(B_DEC):
        cnt = np.bincount(rng.integers(0, n_scenes, n_scenes), minlength=n_scenes)
        bl, bg = L.expand(cl, cnt), L.expand(cg, cnt)
        if bl["n"] == 0 or bg["n"] == 0:
            continue
        e, x = stats(bl, bg)
        be.append(e); bx.append(x)
    r = {"available": True, "ANEES": nv["ANEES"], "k": k, "lat_exc_after": e0, "lat_exc_after_lo_2.5": float(np.quantile(be, 0.025)),
         "long_extra_margin_m": x0, "long_extra_margin_lo_2.5": float(np.quantile(bx, 0.025))}
    r["H3"] = bool(r["lat_exc_after_lo_2.5"] > L.DELTA or r["long_extra_margin_lo_2.5"] > L.H0)
    return r


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
    ap.add_argument("--skip-bind", action="store_true", help="synthetic tests only")
    a = ap.parse_args()
    pre_sha, settings = F.check_freeze(a.prereg)
    inputs = [a.gt, a.oc, a.horizon] + [os.path.join(w, f) for w in a.workers for f in ("x1_tracks.jsonl.gz", "x1_export_record.json", "x1_per_frame.json")]
    if not a.skip_bind:
        bind_inputs(a.prereg, inputs)
    logit = settings.get("band", "linear") == "logit"
    t0 = time.time()
    rng = np.random.default_rng(L.SEED)
    res = {"prereg_sha256": pre_sha, "band": "logit" if logit else "linear", "band_level": F.LEVEL, "decision_cells": ["|".join(c) for c in DEC]}
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
    c6 = [r["c6"] for r in rows if r["c6"] is not None and not r["first"]]
    res["Q0"] = {"tokens": len(tokens), "records": len(recs), "C6_max_abs_m_non_birth": float(max(c6)) if c6 else None,
                 "C6_pass": bool(c6) and max(c6) <= 1e-6}
    del recs
    res["pairing"] = pst
    res["Q1_paired_share_of_inpath"] = pst.get("paired_inpath", 0) / max(pst.get("inpath_records", 1), 1)
    scene_names = sorted({s["scene"] for s in samples.values()})
    logs = sorted(set(scene_log[s] for s in scene_names))
    W = L.boot_weights(len(scene_names), F.B_EXC, rng)
    WL = L.log_cluster_weights(np.array([logs.index(scene_log[s]) for s in scene_names]), len(logs), F.B_EXC, rng)
    oc = json.load(open(a.oc))
    keys = {(r["scene"], r["k"], r["tid"]) for rr in (rows, rows4, rowsr) for r in rr}
    pred = L.load_horizon(a.horizon, keys)
    hr, hst = L.build_horizon_rows(rows, pred, samples, gtb, racks)
    hr4, _ = L.build_horizon_rows(rows4, pred, samples, gtb, racks)
    hrr, _ = L.build_horizon_rows(rowsr, pred, samples, gtb, racks)
    del pred, rows4, rowsr
    res["horizon_rows"] = hst
    fam = F.family("h2s", hr, hr4, hrr, scene_names, scene_log, logit, W, WL, rng, oc.get("h2s", oc))
    fam["G1_family_NOTE"] = "X1 rule recomputed at X2 levels for reference only; NOT the X2 decision (see G1_X2)"
    res["family_h2s"] = fam
    print("h2s %.0f s, peak %s MB" % (time.time() - t0, peak_mb()), flush=True)
    prim, sens, pr = fam["primary"], fam["sensitivities"], fam["prices"]["cells"]
    cells, _, _ = L.cell_items(hr, sigma_a=0.10)
    sidx = {s: i for i, s in enumerate(scene_names)}
    sc_rows = sorted({r["scene"] for r in hr})
    for c in DEC:
        if cells[c]["n"]:
            cells[c]["s"] = np.array([sidx[sc_rows[i]] for i in cells[c]["s"]])
    ct, sct, _ = L.cell_items(hr, sigma_a=0.10, orient="truth")
    for c in L.CELLS:
        if ct[c]["n"]:
            ct[c]["s"] = np.array([sidx[sct[i]] for i in ct[c]["s"]])
    elig_t = [c for c in DEC if ct[c]["n_scenes"] >= L.MIN_SCENES]
    truth_dec = F.band_verdicts(ct, elig_t, len(scene_names), {}, W, logit)
    res["truth_oriented_decision_band"] = {k: v for k, v in truth_dec.items() if not k.startswith("_")}
    steps = []
    for rb in BINS:
        kl, kg = "car|%s|lat" % rb, "car|%s|long" % rb
        v = prim.get(kl, {})
        h1 = {"cell": kl, "eligible": kl in fam["eligible"], "zero_se": bool(v.get("zero_se")), "a1_fails": v.get("verdict") == "FAILS",
              "a2_material": kl in pr and pr[kl]["Delta_m"]["lo_bonf"] > L.H0,
              "a3_sigma_0.20": sens["sigma_a=0.20"].get(kl, {}).get("verdict") == "FAILS",
              "a4_contested_excluded": sens["contested_excluded"].get(kl, {}).get("verdict") == "FAILS",
              "a5_truth_oriented": truth_dec.get(kl, {}).get("verdict") == "FAILS"}
        h1["H1"] = bool(h1["eligible"] and not h1["zero_se"] and h1["a1_fails"] and h1["a2_material"] and h1["a3_sigma_0.20"]
                        and h1["a4_contested_excluded"] and h1["a5_truth_oriented"])
        step = {"bin": rb, "H1": h1}
        if h1["H1"] and cells[("car", rb, "long")]["n"]:
            h2 = h2_price(cells, ("car", rb, "lat"), ("car", rb, "long"), rng, len(scene_names))
            h2["H2"] = h2["lo_2.5"] > L.H0
            step["H2"] = h2
            if h2["H2"]:
                step["H3"] = h3_nees(cells, fam["nees"], ("car", rb, "lat"), ("car", rb, "long"), rng, len(scene_names))
        steps.append(step)
    g1 = any(s["H1"]["H1"] and s.get("H2", {}).get("H2") for s in steps)
    res["G1_X2"] = {"steps": steps, "G1_holds": bool(g1),
                    "H3_holds": bool(g1 and any(s.get("H3", {}).get("H3") for s in steps)),
                    "sequence": "H1 -> H2 -> H3 at alpha 0.05; G1 = H1 and H2 in at least one range bin"}
    res["family_t0_descriptive"] = F.family("t0", rows, rows, rows, scene_names, scene_log, logit, W, WL, rng, oc.get("t0", oc))
    res["family_t0_descriptive"]["NOTE"] = "descriptive; gate-4 m and re-matching sensitivities not recomputed for t0 in X2"
    res["peak_working_set_mb"] = peak_mb()
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps(res["G1_X2"], default=float)[:2000], flush=True)


if __name__ == "__main__":
    sys.exit(main())
