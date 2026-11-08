#!/usr/bin/env python3
"""X3 amendment A4 part (4) (x3-a1 agent, 7 Nov 2026): heading error, stricter cuts and the annotation's own axes.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Added after review (amendment A4).

Amendment: 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md (sha256 ab19dd66...), section (4); extends A1 (a5cc3261...).
Reuses the A1 rebuild unchanged (60_RESULTS/x3_explore_v01/a1_heading/ckpt/a1_hr_v01.pkl, written by x3_a1_heading_v01.py);
the reproduction gate against the X2 result of record is re-checked on the reloaded rows before anything else.

  (4a) E and item counts on items with heading error <= 5 deg and <= 10 deg (heading error as A1: at keyframe k, folded).
  (4b) E along the annotation's own box axes, on the same items: for an item on the track's lateral (longitudinal) axis, the
       annotated box's lateral (longitudinal) axis b at keyframe k (the annotation A1 used, yaw psi_ann(k)); the error
       projected on b and oriented toward the ego as X2 orients (sign of b.(c - m) estimate-oriented, of b.(c - g)
       truth-oriented; c = predicted ego centre at 2 s, m = predicted mean, g = annotation centre at 2 s);
       sd = sqrt(b' S b + sigma_a^2) from the same predicted covariance S, sigma_a = 0.10 m; exceedance U_b > z_0.95.
       The item set is X2's (the separating filter is not re-evaluated on b).
  Intervals: pointwise scene-cluster bootstrap 95 % percentile intervals, B = 2000, seed [20261211, cell, k] with cell = 0..3 in
  X2's DEC order and k = 1 (<= 5 deg), 2 (<= 10 deg), 3 (annotation axes); same seed for both orientations of a cell.
"""
import gc
import json
import math
import os
import pickle
import sys
import time

import numpy as np

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
sys.path.insert(0, os.path.join(W, "50_CODE", "x3"))
import x3_a1_heading_v01 as A1  # noqa: E402  (imports the frozen X2 code read-only; no main runs on import)
from x3_heavylock_v01 import heavy_lock  # noqa: E402

L, X2, C = A1.L, A1.X2, A1.C
LABEL = "added after review (amendment A4)"
AMEND4 = os.path.join(W, "20_DESIGN", "X3_PLAN_AMENDMENT_A4_v01.md")
AMEND4_SHA = "ab19dd66b1838109534a4cb23f93835b5558af1e1cffd73d74416ef3bdf7832b"
HR_CK = os.path.join(A1.CK, "a1_hr_v01.pkl")
A1_JSON = A1.OUT_JSON
OUT_JSON = os.path.join(A1.OUTD, "x3_a4_heading_v01.json")
OUT_MD = os.path.join(A1.OUTD, "x3_a4_heading_v01.md")
SEED = 20261211
B = 2000
SIGMA = 0.10
CUTS = ((1, 5.0), (2, 10.0))
K_AXES = 3
T0 = time.time()


def live(step, done, total, note=""):
    line = "%s | x3-a1 | A4(4): %s | %s/%s%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), step, done, total, (" | " + note) if note else "")
    try:
        C.wtext(A1.LIVE, line)
    except Exception:
        pass
    print(line.strip(), flush=True)


def walk(hr, heading, scene_names, orient):
    """Frozen L.cell_items for the item set, U and scenes; a parallel walk in the same order for heading error and the
    annotation-axis quantities, checked item by item (D exactly equal; the annotation-axis code path run with the track's
    own yaw reproduces X2's U exactly)."""
    cells, sc_rows, _ = L.cell_items(hr, sigma_a=SIGMA, orient=orient)
    sidx = {s: i for i, s in enumerate(scene_names)}
    remap = np.array([sidx[s] for s in sc_rows])
    keys = ("he", "D", "keep", "Db", "varb", "Dt", "vart")
    acc = {c: {k: [] for k in keys} for c in L.CELLS}

    def along(r, yaw, name):
        cs, sn = math.cos(yaw), math.sin(yaw)
        b = (cs, sn) if name == "long" else (-sn, cs)
        sxx, sxy, syy = r["S"]
        var = b[0] * b[0] * sxx + 2 * b[0] * b[1] * sxy + b[1] * b[1] * syy
        proj = b[0] * (r["gx"] - r["mx"]) + b[1] * (r["gy"] - r["my"])
        if orient == "estimate":
            so = b[0] * (r["cx"] - r["mx"]) + b[1] * (r["cy"] - r["my"])
        else:
            so = b[0] * (r["cx"] - r["gx"]) + b[1] * (r["cy"] - r["gy"])
        return (1.0 if so >= 0 else -1.0) * proj, var

    for r in hr:
        if not r["paired"] or not r["inpath"]:
            continue
        psi_t, psi_a, he = heading[(r["scene"], r["k"], r["tid"])]
        assert psi_t == r["yaw"]
        for name, a, sep, hsum in L.axis_candidates(r):
            c = (r["group"], r["range"], name)
            proj = a[0] * (r["gx"] - r["mx"]) + a[1] * (r["gy"] - r["my"])
            sep_o = sep if orient == "estimate" else a[0] * (r["cx"] - r["gx"]) + a[1] * (r["cy"] - r["gy"])
            sign = 1.0 if sep_o >= 0 else -1.0
            Db, varb = along(r, psi_a, name)
            Dt, vart = along(r, psi_t, name)
            for k_, v in (("he", he), ("D", sign * proj), ("keep", abs(sep_o) > hsum), ("Db", Db), ("varb", varb), ("Dt", Dt), ("vart", vart)):
                acc[c][k_].append(v)
    out = {}
    for c in X2.DEC:
        d = cells[c]
        k = np.array(acc[c]["keep"], bool)
        arr = {k_: np.array(acc[c][k_])[k] for k_ in keys if k_ != "keep"}
        assert len(acc[c]["D"]) == len(d["all"]["var"]) and np.array_equal(arr["D"], d["D"]), "item alignment failed " + str(c)
        Ut = arr["Dt"] / np.sqrt(arr["vart"] + SIGMA ** 2)
        assert np.allclose(Ut, d["U"], rtol=0, atol=1e-9), "annotation-axis code path does not reproduce X2's U " + str(c)
        out[c] = {"U": d["U"], "s": remap[d["s"]], "n": d["n"], "n_scenes": d["n_scenes"], "he": arr["he"],
                  "Ub": arr["Db"] / np.sqrt(arr["varb"] + SIGMA ** 2),
                  "max_abs_Ut_minus_U": float(np.max(np.abs(Ut - d["U"]))) if d["n"] else 0.0}
    return out


def boot_e(exc, s, mask, n_sc, seed):
    es = L.sums_by(s[mask], exc[mask].astype(float), n_sc)
    ts = L.sums_by(s[mask], np.ones(int(mask.sum())), n_sc)
    E = float(es.sum() / ts.sum()) if ts.sum() > 0 else None
    rng = np.random.default_rng(seed)
    Wb = L.boot_weights(n_sc, B, rng)
    den = Wb @ ts
    bt = ((Wb @ es) / np.maximum(den, 1e-12))[den > 0]
    lo, hi = (float(np.quantile(bt, 0.025)), float(np.quantile(bt, 0.975))) if len(bt) else (None, None)
    return {"E": E, "ci95": [lo, hi], "n_items": int(mask.sum()), "n_scenes": int(len(np.unique(s[mask]))),
            "exceedances": int(exc[mask].sum()), "seed": list(seed), "replicates_used": int(len(bt))}


def fmt(x, nd=3):
    return "n/a" if x is None else "%.*f" % (nd, x)


def write_md(res):
    lab = {"car|<20|lat": "car, < 20 m, lat", "car|20-40|lat": "car, 20–40 m, lat", "car|<20|long": "car, < 20 m, long",
           "car|20-40|long": "car, 20–40 m, long"}
    out = ["# X3 amendment A4 (4): heading error, stricter cuts and annotation axes (v01)", "",
           "**%s**" % C.STAMP, "", "**%s.** Amendment `20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md` (sha256 %s...), section (4); "
           "extends A1 (`x3_a1_heading_v01.json`) on the same rebuilt X2 items (nuScenes train, 700 scenes, T1 = CANMOT, "
           "in-path cars, 2 s, sigma_a = 0.10 m)." % (LABEL, AMEND4_SHA[:8]), "",
           "Reuse check: the A1 rows reloaded from the checkpoint reproduce X2's n, scenes and E_rec exactly in the four decision "
           "cells, estimate- and truth-oriented: **%s**." % ("yes" if res["reuse_gate"]["passed"] else "NO"), ""]
    for orient, title in (("estimate", "Estimate-oriented (X2 primary)"), ("truth", "Truth-oriented (X2 a5 definition)")):
        out += ["## %s" % title, "",
                "| Cell | E, all items (record) | E, heading error <= 5 deg [95 % CI] | n (scenes) | E, heading error <= 10 deg [95 % CI] | n (scenes) | E, annotation axes [95 % CI] | n (scenes) | threshold of record |",
                "|---|---|---|---|---|---|---|---|---|"]
        for c in res["cells_order"]:
            v = res["results"][orient][c]
            a, b_, x = v["he_le5"], v["he_le10"], v["annotation_axes"]
            out.append("| %s | %s (%d) | %s [%s, %s] | %d (%d) | %s [%s, %s] | %d (%d) | %s [%s, %s] | %d (%d) | %s |" % (
                lab[c], fmt(v["E_all_record"]), v["n_all"], fmt(a["E"]), fmt(a["ci95"][0]), fmt(a["ci95"][1]), a["n_items"], a["n_scenes"],
                fmt(b_["E"]), fmt(b_["ci95"][0]), fmt(b_["ci95"][1]), b_["n_items"], b_["n_scenes"],
                fmt(x["E"]), fmt(x["ci95"][0]), fmt(x["ci95"][1]), x["n_items"], x["n_scenes"], fmt(v["threshold_of_record"], 4)))
        out.append("")
    out += ["## Method notes", ""] + ["- " + m for m in res["method_notes"]]
    out += ["", "Integrity: C1_RUN_LOG sha256 %s... before and after; c1_av2_v01 manifest identical before and after: %s." % (
        res["integrity"]["run_log_after"][:8], res["integrity"]["manifest_after_ok"]), ""]
    return "\n".join(out) + "\n"


def main():
    if os.path.exists(OUT_JSON) or os.path.exists(OUT_MD):
        raise SystemExit("output exists; not overwriting")
    live("integrity and hashes", 0, 4)
    rl0 = C.assert_run_log("before x3-a1 A4(4)")
    ok0, man0 = C.manifest_check()
    if not ok0:
        raise SystemExit("X3 STOP: c1_av2_v01 manifest differs before A4(4): %s" % json.dumps(man0)[:2000])
    assert C.sha256(AMEND4) == AMEND4_SHA, "amendment A4 changed"
    hashes = A1.check_hashes()
    a1 = json.load(open(A1_JSON))
    ck_sha = C.sha256(HR_CK)
    R = pickle.load(open(HR_CK, "rb"))
    rec = json.load(open(A1.RESULT))
    prim, truth_rec = rec["family_h2s"]["primary"], rec["truth_oriented_decision_band"]
    scene_names = R["scene_names"]
    n_sc = len(scene_names)
    assert n_sc == 700 and [tuple(c.split("|")) for c in rec["decision_cells"]] == X2.DEC
    live("items and reuse check", 1, 4)
    it = {o: walk(R["hr"], R["heading"], scene_names, o) for o in ("estimate", "truth")}
    gate = {"cells": {}}
    for o, refd in (("estimate", prim), ("truth", truth_rec)):
        for c in X2.DEC:
            key, d = "|".join(c), it[o][c]
            er = A1.e_rec(d, n_sc)[0]
            r_ = refd[key]
            gate["cells"]["%s %s" % (o, key)] = {"n": d["n"], "scenes": d["n_scenes"], "E_rec": er, "n_record": r_["n"],
                                                 "scenes_record": r_["scenes"], "E_rec_record": r_["E_rec"],
                                                 "equal": bool(d["n"] == r_["n"] and d["n_scenes"] == r_["scenes"] and er == r_["E_rec"]),
                                                 "max_abs_Ut_minus_U": d["max_abs_Ut_minus_U"]}
    gate["passed"] = all(v["equal"] for v in gate["cells"].values())
    if not gate["passed"]:
        raise SystemExit("A4(4) STOP: the reloaded A1 rows do not reproduce X2: %s" % json.dumps(gate)[:3000])
    live("bootstrap (B = 2000; 3 analyses x 4 cells x 2 orientations)", 2, 4)
    results = {"estimate": {}, "truth": {}}
    with heavy_lock("x3-a1: A4(4) bootstrap"):
        for o in ("estimate", "truth"):
            for ci, c in enumerate(X2.DEC):
                key, d = "|".join(c), it[o][c]
                exc = d["U"] > L.Z95
                v = {"n_all": d["n"], "E_all_record": (prim if o == "estimate" else truth_rec)[key]["E_rec"],
                     "threshold_of_record": (prim[key]["threshold"] if o == "estimate" else truth_rec[key]["threshold"])}
                for k, cut in CUTS:
                    v["he_le%d" % int(cut)] = boot_e(exc, d["s"], d["he"] <= cut, n_sc, [SEED, ci, k])
                v["annotation_axes"] = boot_e(d["Ub"] > L.Z95, d["s"], np.ones(d["n"], bool), n_sc, [SEED, ci, K_AXES])
                results[o][key] = v
    res = {"stamp": C.STAMP, "label": LABEL, "analysis": "X3 amendment A4 part (4): heading error, stricter cuts and annotation axes",
           "amendment_sha256": AMEND4_SHA, "extends": {"A1_amendment_sha256": A1.AMEND_SHA, "A1_result_sha256": C.sha256(A1_JSON),
                                                        "A1_rebuild_checkpoint": os.path.relpath(HR_CK, W).replace("\\", "/"),
                                                        "A1_rebuild_checkpoint_sha256": ck_sha},
           "x2_result_sha256": C.sha256(A1.RESULT), "hashes": hashes,
           "code": {"x3_a1_a4_heading_v01.py": C.sha256(os.path.abspath(__file__)), "x3_a1_heading_v01.py": C.sha256(A1.__file__)},
           "reuse_gate": gate, "cells_order": list(rec["decision_cells"]), "results": results}
    assert res["code"]["x3_a1_heading_v01.py"] == a1["code"]["x3_a1_heading_v01.py"], "A1 code changed since the A1 run"
    res["method_notes"] = [
        "Same items as A1 and X2 (L.cell_items on the A1 rebuild, reloaded unchanged; n, scenes and E_rec re-checked equal to the "
        "X2 result of record in all eight cell-orientation pairs).",
        "Heading error as A1: |wrap(psi_track - psi_annotation)| at the decision keyframe k, folded to [0, 90] deg; (4a) keeps items "
        "with heading error <= 5 deg or <= 10 deg; E record-weighted (exceedances / items), exceedance U > z_0.95 = %r." % L.Z95,
        "(4b) Annotation axes: for an item on the track's lateral (longitudinal) axis, the annotated box's lateral (longitudinal) "
        "axis b at keyframe k (the annotation paired at k, as in A1; A4 does not name the keyframe, and k keeps the analysis at "
        "decision time, swapping only the heading). Error (g - m) projected on b, signed toward the ego as X2 orients: sign of "
        "b.(c - m) estimate-oriented, of b.(c - g) truth-oriented (c = CTRV-predicted ego centre at 2 s, m = predicted mean, "
        "g = annotation centre at 2 s). sd = sqrt(b' S b + 0.10^2) from the same predicted covariance S. The item set is X2's: "
        "the separating filter is not re-evaluated along b.",
        "Code-path check: the (4b) computation run with the track's own yaw in place of the annotation's reproduces X2's U "
        "(max abs difference per cell in reuse_gate, tolerance 1e-9).",
        "Bootstrap: scene-cluster, B = 2000, numpy default_rng([20261211, cell, k]); cell = 0..3 in X2's DEC order (car <20 lat, "
        "car 20-40 lat, car <20 long, car 20-40 long); k = 1 (<= 5 deg), 2 (<= 10 deg), 3 (annotation axes); the same seed for the "
        "estimate- and truth-oriented versions. Weights L.boot_weights (multinomial over the 700 scenes, X2's convention); "
        "replicate = ratio of weighted sums; pointwise 95 % percentile interval.",
        "Thresholds listed for reference only (A4 (4) fixes no reading): estimate-oriented max(0.05, E0) of record; "
        "truth-oriented 0.05 of record.",
    ]
    live("integrity after", 3, 4)
    rl1 = C.assert_run_log("after x3-a1 A4(4)")
    ok1, man1 = C.manifest_check()
    res["integrity"] = {"run_log_before": rl0, "run_log_after": rl1, "manifest_before_ok": ok0, "manifest_after_ok": ok1,
                        "manifest_after": man1 if not ok1 else {"files": man1["files_now"]}}
    res["wall_s"] = round(time.time() - T0, 1)
    res["written"] = time.strftime("%Y-%m-%d %H:%M:%S")
    C.jdump(OUT_JSON, res, refuse_existing=True)
    C.wtext(OUT_MD, write_md(res), refuse_existing=True)
    live("done", 4, 4, "x3_a4_heading_v01.json/.md in 60_RESULTS/x3_explore_v01/a1_heading")
    if not ok1:
        raise SystemExit("X3 STOP: c1_av2_v01 manifest differs after A4(4)")


if __name__ == "__main__":
    main()
