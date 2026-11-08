#!/usr/bin/env python3
"""X3 amendment A1 (x3-a1 agent, 7 Nov 2026): the heading error behind the "lateral" diagnosis.
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).

Amendment: 20_DESIGN/X3_PLAN_AMENDMENT_A1_v01.md (sha256 a5cc3261...), under the parent plan
20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md section 0 (38e2526d...).

What it does
  1. Rebuilds the X2 h2s items (nuScenes train, 700 scenes, T1 = CANMOT, in-path, 2 s, sigma_a = 0.10 m) by importing the
     frozen X2 code read-only (x2_full_v02 -> x1_lib_v03 / x1_full_v02). Only library functions are called: load_export,
     build_table, load_horizon, build_horizon_rows, cell_items, sums_by, boot_weights. No main(), no check_freeze(), no
     bind_inputs() (guards are not called; input hashes are checked here against the X2 frozen block, read as text).
     Memory: the laptop has about 2 GB free, so (a) the ground truth is read by a lean streaming loader that keeps, per
     annotation, exactly the keys the frozen functions read (instance_token, tracking_name, translation, num_pts) plus yaw,
     in file order per sample (as load_gt); (b) build_table runs per export worker (scenes are disjoint across workers,
     asserted; pairing state is per scene), and only paired, in-path rows at k are kept (the only rows cell_items uses).
  2. Reproduction gate: per decision cell, n, scenes and record-weighted E must equal x2_full_v02_result.json exactly.
  3. Per item: heading error |wrap(psi_track - psi_annotation)| at the decision keyframe k, psi_track = the record's box yaw
     at k (the yaw that defines the axes of the horizon item), psi_annotation = the yaw of the paired instance's annotation
     at k (the one build_table paired; its centre is checked equal to the row's gx, gy), folded to [0, 90] deg.
  4. Per cell, estimate- and truth-oriented: shares <= 10, (10, 20], > 20 deg; share of exceedances (U > z_0.95) from
     items > 20 deg; E on items <= 20 deg with a scene-cluster bootstrap 95 % percentile interval (B = 2000, seed
     [20261211, cell], cell = index in X2's DEC order; X2's scene-weight convention: multinomial over the 700 scenes,
     ratio of weighted sums), against X2's threshold of record.
Checkpoints: 60_RESULTS/x3_explore_v01/a1_heading/ckpt (per worker, then the horizon rows). Resume, never restart.
"""
import gc
import json
import math
import os
import pickle
import sys
import time
from collections import defaultdict

import numpy as np

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
X1 = os.path.join(W, "50_CODE", "x1")
X3 = os.path.join(W, "50_CODE", "x3")
sys.path.insert(0, X3)
sys.path.insert(0, X1)
import x2_full_v02 as X2  # noqa: E402  frozen; module level = imports + F.analyse_cells rebinding; no guard, no I/O
import x3_common_v01 as C  # noqa: E402  lead's X3 helpers (hashing, integrity, atomic writes)
from x3_heavylock_v01 import heavy_lock  # noqa: E402

L, F = X2.L, X2.F
assert L.__name__ == "x1_lib_v03" and F.L is L

STAMP = C.STAMP
AMEND = os.path.join(W, "20_DESIGN", "X3_PLAN_AMENDMENT_A1_v01.md")
AMEND_SHA = "a5cc32611fd31da1ad847a12cc177286c6f6f9349b86bd65f7f45c20d699837a"
PREREG = os.path.join(W, "40_PROTOCOL", "X2_PREREGISTRATION_v02.md")
PREREG_SHA = "41bc5a936684dab6f6978c7d54e3d34c730afe7117ce62571b87bdb40aa447bc"
RESULT = os.path.join(W, "60_RESULTS", "x2", "x2_full_v02_result.json")
EXP = os.path.join(W, "60_RESULTS", "x2_export_train700_fast_v02")
GT = os.path.join(W, "30_DATA", "x2_gt", "x2_train_gt_v03.json")
META = os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval", "scene.json")
HOR = os.path.join(W, "60_RESULTS", "x2", "x2_horizon_v01.jsonl.gz")
WORKERS = [os.path.join(EXP, "worker%d" % i) for i in range(12)]  # the order of the X2 run (seq 0 11)
FROZEN_CODE = {os.path.join(X1, f): h for f, h in (
    ("x2_full_v02.py", "7025ea878bff9b1b2ae8c8a0a2765e197b1d7869dd16e468b28a2f00dfe53c00"),
    ("x1_full_v02.py", "b59dd08a407b8907d93386e7b136af973a5889444c3a0c84053d3e8a4a42bf64"),
    ("x1_lib_v03.py", "f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd"),
    ("x1_lib_v02.py", "9728e9f518e284e39e522c7252353f1342e7b9ffd682a742cd1eba9b646f8571"),
    ("x1_prefreeze_v02.py", "a2d613f047ae09e37fb03291ef635ce6ac3055d67e49346a7fac88333a128538"))}
OUTD = os.path.join(W, "60_RESULTS", "x3_explore_v01", "a1_heading")
CK = os.path.join(OUTD, "ckpt")
OUT_JSON = os.path.join(OUTD, "x3_a1_heading_v01.json")
OUT_MD = os.path.join(OUTD, "x3_a1_heading_v01.md")
LIVE = os.path.join(W, "00_PROGRESS", "live", "x3_a1.txt")
SEED_A1 = 20261211
B_A1 = 2000
SIGMA = 0.10
BINS_DEG = (10.0, 20.0)
T0 = time.time()


def live(step, done, total, note=""):
    line = "%s | x3-a1 | %s | %s/%s%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), step, done, total, (" | " + note) if note else "")
    try:
        C.wtext(LIVE, line)
    except Exception:
        pass
    print(line.strip(), flush=True)


def frozen_block():
    txt = open(PREREG, encoding="utf-8").read()
    block = txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
    out = {}
    for ln in block.strip().splitlines():
        if not ln.strip() or ln.startswith(("setting", "(", "#")):
            continue
        h, p = ln.split("  ", 1)
        out[os.path.normcase(p.strip())] = h
    return out


def check_hashes():
    """Frozen code and every run input of the rebuild, against the X2 frozen block (read as text; no guard is called)."""
    fb = frozen_block()
    rep = {"prereg": C.sha256(PREREG), "amendment": C.sha256(AMEND), "code": {}, "inputs": {}}
    assert rep["prereg"] == PREREG_SHA, "X2 prereg changed"
    assert rep["amendment"] == AMEND_SHA, "amendment A1 changed"
    for p, h in FROZEN_CODE.items():
        got = C.sha256(p)
        assert got == h and fb.get(os.path.normcase(p)) == h, "frozen code differs: " + p
        rep["code"][os.path.basename(p)] = got
    for p in [GT, META, HOR] + [os.path.join(w, "x1_tracks.jsonl.gz") for w in WORKERS]:
        got = C.sha256(p)
        assert fb.get(os.path.normcase(p)) == got, "input not in the X2 frozen block: " + p
        rep["inputs"][os.path.relpath(p, W).replace("\\", "/")] = got
    return rep


def _ws(t, i):
    while t[i] in " \t\r\n":
        i += 1
    return i


def load_gt_lean(path):
    """Same samples / by_sample / racks as L.load_gt (same open() call, same order within each sample), but each annotation
    keeps only the keys the frozen functions read plus yaw. Streams the annotations array element by element."""
    t = open(path).read()
    dec = json.JSONDecoder()
    top, by_sample, n_ann = {}, defaultdict(list), 0
    i = _ws(t, 0)
    assert t[i] == "{"
    i = _ws(t, i + 1)
    while t[i] != "}":
        key, i = dec.raw_decode(t, i)
        i = _ws(t, i)
        assert t[i] == ":"
        i = _ws(t, i + 1)
        if key == "annotations":
            assert t[i] == "["
            i = _ws(t, i + 1)
            if t[i] == "]":
                i += 1
            else:
                while True:
                    a, i = dec.raw_decode(t, i)
                    by_sample[sys.intern(a["sample_token"])].append(
                        {"instance_token": sys.intern(a["instance_token"]), "tracking_name": sys.intern(a["tracking_name"]),
                         "translation": a["translation"], "num_pts": a["num_pts"], "yaw": a["yaw"]})
                    n_ann += 1
                    i = _ws(t, i)
                    if t[i] == ",":
                        i = _ws(t, i + 1)
                        continue
                    assert t[i] == "]"
                    i += 1
                    break
        else:
            top[key], i = dec.raw_decode(t, i)
        i = _ws(t, i)
        if t[i] == ",":
            i = _ws(t, i + 1)
    del t
    samples = {s["token"]: s for s in top["samples"]}
    racks = defaultdict(list)
    for r in top.get("bicycle_racks", []):
        racks[r["sample_token"]].append(r)
    return samples, by_sample, racks, {"samples": len(samples), "annotations": n_ann,
                                       "racks": len(top.get("bicycle_racks", [])), "note": top.get("note")}


def scene_index(samples):
    st = defaultdict(dict)
    for s in samples.values():
        st[s["scene"]][s["index"]] = s
    return st


def paired_annotation(r, scene_tokens, gtb, racks):
    """The annotation build_table paired with row r at keyframe k (same gts filter, same ann_by_inst construction)."""
    smp = scene_tokens[r["scene"]][r["k"]]
    rk = racks.get(smp["token"], [])

    def rack_hit(px, py):
        return any(L.in_rect(px, py, q["translation"][0], q["translation"][1], q["yaw"], q["size"][1], q["size"][0]) for q in rk)
    gts = [a for a in gtb.get(smp["token"], []) if a["num_pts"] >= 1
           and not (a["tracking_name"] in ("bicycle", "motorcycle") and rack_hit(a["translation"][0], a["translation"][1]))]
    a = {x["instance_token"]: x for x in gts}[r["inst"]]
    assert a["translation"][0] == r["gx"] and a["translation"][1] == r["gy"], "pairing mismatch at k"
    return a


def fold_deg(psi_t, psi_a):
    d = abs(L.wrap(psi_t - psi_a))
    return math.degrees(min(d, math.pi - d))


def rebuild():
    """Heavy: per-worker build_table (checkpointed), then the horizon rows (checkpointed)."""
    os.makedirs(CK, exist_ok=True)
    hr_ck = os.path.join(CK, "a1_hr_v01.pkl")
    if os.path.exists(hr_ck):
        live("rebuild: horizon checkpoint found, resuming", 14, 14)
        return pickle.load(open(hr_ck, "rb"))
    live("rebuild: loading ground truth (lean streaming loader)", 0, 14)
    samples, gtb, racks, gtinfo = load_gt_lean(GT)
    gc.collect()
    live("rebuild: ground truth loaded", 1, 14, "%d samples, %d annotations, peak %s MB" % (gtinfo["samples"], gtinfo["annotations"], X2.peak_mb()))
    scene_log = {s["name"]: s["log_token"] for s in json.load(open(META))}
    scene_tokens = scene_index(samples)
    rows_all, st_all, heading, seen_scenes, per_worker = [], defaultdict(int), {}, set(), []
    for i, w in enumerate(WORKERS):
        ck = os.path.join(CK, "a1_worker%02d_v01.pkl" % i)
        if os.path.exists(ck):
            d = pickle.load(open(ck, "rb"))
        else:
            t1 = time.time()
            recs = L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
            n_recs = len(recs)
            scenes = sorted({r["scene"] for r in recs})
            rows, st = L.build_table(recs, samples, gtb, racks, scene_log=scene_log)
            del recs
            keep = [r for r in rows if r["paired"] and r["inpath"]]
            n_rows = len(rows)
            del rows
            gc.collect()
            head = {}
            for r in keep:
                key = (r["scene"], r["k"], r["tid"])
                assert key not in head, "duplicate (scene, k, tid)"
                a = paired_annotation(r, scene_tokens, gtb, racks)
                head[key] = (r["yaw"], a["yaw"], fold_deg(r["yaw"], a["yaw"]))
            d = {"worker": i, "rows": keep, "st": dict(st), "head": head, "scenes": scenes, "n_recs": n_recs,
                 "n_paired_rows": n_rows, "wall_s": round(time.time() - t1, 1)}
            with open(ck + ".tmp", "wb") as f:
                pickle.dump(d, f, protocol=4)
            os.replace(ck + ".tmp", ck)
        assert not (set(d["scenes"]) & seen_scenes), "a scene is split across workers"
        seen_scenes |= set(d["scenes"])
        rows_all += d["rows"]
        for k_, v in d["st"].items():
            st_all[k_] += v
        heading.update(d["head"])
        per_worker.append({"worker": i, "records": d["n_recs"], "scenes": len(d["scenes"]), "paired_rows": d["n_paired_rows"],
                           "paired_inpath_rows": len(d["rows"]), "wall_s": d["wall_s"]})
        live("rebuild: worker %d done" % i, i + 2, 14, "%d records, %d paired in-path rows, peak %s MB" % (d["n_recs"], len(d["rows"]), X2.peak_mb()))
        del d
        gc.collect()
    keys = {(r["scene"], r["k"], r["tid"]) for r in rows_all}
    pred = L.load_horizon(HOR, keys)
    hr, hst = L.build_horizon_rows(rows_all, pred, samples, gtb, racks)
    del pred
    scene_names = sorted({s["scene"] for s in samples.values()})
    out = {"hr": hr, "heading": heading, "scene_names": scene_names, "pairing": dict(st_all), "horizon_rows_inpath": hst,
           "gtinfo": gtinfo, "per_worker": per_worker, "n_rows_k": len(rows_all), "scenes_in_exports": len(seen_scenes)}
    with open(hr_ck + ".tmp", "wb") as f:
        pickle.dump(out, f, protocol=4)
    os.replace(hr_ck + ".tmp", hr_ck)
    live("rebuild: horizon rows built", 14, 14, "%d rows, peak %s MB" % (len(hr), X2.peak_mb()))
    return out


def items(hr, heading, scene_names, orient):
    """L.cell_items (frozen) for U, s, n, n_scenes; a parallel walk in the same order for the per-item heading error, checked
    item by item against the frozen arrays (D exactly equal)."""
    cells, sc_rows, _ = L.cell_items(hr, sigma_a=SIGMA, orient=orient)
    sidx = {s: i for i, s in enumerate(scene_names)}
    remap = np.array([sidx[s] for s in sc_rows])
    acc = {c: {"he": [], "D": [], "keep": []} for c in L.CELLS}
    for r in hr:
        if not r["paired"] or not r["inpath"]:
            continue
        he = heading[(r["scene"], r["k"], r["tid"])][2]
        for name, a, sep, hsum in L.axis_candidates(r):
            c = (r["group"], r["range"], name)
            proj = a[0] * (r["gx"] - r["mx"]) + a[1] * (r["gy"] - r["my"])
            sep_o = sep if orient == "estimate" else a[0] * (r["cx"] - r["gx"]) + a[1] * (r["cy"] - r["gy"])
            sign = 1.0 if sep_o >= 0 else -1.0
            acc[c]["he"].append(he)
            acc[c]["D"].append(sign * proj)
            acc[c]["keep"].append(abs(sep_o) > hsum)
    out = {}
    for c in L.CELLS:
        d = cells[c]
        if d["n"] == 0:
            out[c] = None
            continue
        k = np.array(acc[c]["keep"], bool)
        D = np.array(acc[c]["D"])[k]
        assert len(acc[c]["D"]) == len(d["all"]["var"]) and np.array_equal(D, d["D"]), "item alignment failed " + str(c)
        out[c] = {"U": d["U"], "s": remap[d["s"]], "n": d["n"], "n_scenes": d["n_scenes"], "he": np.array(acc[c]["he"])[k]}
    return out


def e_rec(it, n_sc):
    """Exactly F.band_verdicts' E_rec and E_scene."""
    e = L.sums_by(it["s"], (it["U"] > L.Z95).astype(float), n_sc)
    t = L.sums_by(it["s"], np.ones(it["n"]), n_sc)
    m = t > 0
    return float(e.sum() / t.sum()), float(np.mean(e[m] / t[m]))


def a1_cell(it, n_sc, ci, thr):
    he, exc = it["he"], it["U"] > L.Z95
    b1, b2 = he <= BINS_DEG[0], (he > BINS_DEG[0]) & (he <= BINS_DEG[1])
    b3 = he > BINS_DEG[1]
    n = it["n"]
    sub = he <= BINS_DEG[1]
    es = L.sums_by(it["s"][sub], exc[sub].astype(float), n_sc)
    ts = L.sums_by(it["s"][sub], np.ones(int(sub.sum())), n_sc)
    E20 = float(es.sum() / ts.sum()) if ts.sum() > 0 else None
    rng = np.random.default_rng([SEED_A1, ci])
    Wb = L.boot_weights(n_sc, B_A1, rng)
    den = Wb @ ts
    boot = (Wb @ es) / np.maximum(den, 1e-12)
    boot = boot[den > 0]
    lo, hi = (float(np.quantile(boot, 0.025)), float(np.quantile(boot, 0.975))) if len(boot) else (None, None)
    n_exc = int(exc.sum())
    return {"n_items": n, "n_scenes": it["n_scenes"],
            "counts": {"le10": int(b1.sum()), "10_20": int(b2.sum()), "gt20": int(b3.sum())},
            "shares": {"le10": float(b1.mean()), "10_20": float(b2.mean()), "gt20": float(b3.mean())},
            "exceedances": {"total": n_exc, "from_gt20": int((exc & b3).sum()), "from_le20": int((exc & sub).sum())},
            "share_of_exceedances_from_gt20": (float((exc & b3).sum() / n_exc) if n_exc else None),
            "E_le20": E20, "E_le20_n_items": int(sub.sum()), "E_le20_n_scenes": int(len(np.unique(it["s"][sub]))),
            "E_le20_ci95": [lo, hi], "bootstrap": {"B": B_A1, "seed": [SEED_A1, ci], "replicates_used": int(len(boot)),
                                                  "type": "scene-cluster, multinomial weights over the %d scenes (X2 convention); percentile" % n_sc},
            "threshold_of_record": thr,
            "E_le20_above_threshold": (E20 is not None and E20 > thr),
            "ci_lower_above_threshold": (lo is not None and lo > thr),
            "ci_upper_below_threshold": (hi is not None and hi < thr)}


def fmt(x, nd=3):
    return "n/a" if x is None else ("%.*f" % (nd, x))


def write_md(res):
    g = res["reproduction_gate"]
    L_ = ["# X3 amendment A1: heading error behind the lateral diagnosis (v01)", "", "**%s**" % STAMP, "",
          "Amendment `20_DESIGN/X3_PLAN_AMENDMENT_A1_v01.md` (sha256 %s...). Data: X2 (nuScenes train, 700 scenes, T1 = CANMOT, "
          "in-path cars, 2 s, sigma_a = 0.10 m). Items rebuilt by importing the frozen X2 code read-only (no main, no guard)." % AMEND_SHA[:8], "",
          "## Reproduction gate", "", "| Cell | n (rebuilt / record) | scenes | E_rec (rebuilt / record) | equal |", "|---|---|---|---|---|"]
    for c, v in g["cells"].items():
        L_.append("| %s | %d / %d | %d / %d | %r / %r | %s |" % (c, v["n"], v["n_record"], v["scenes"], v["scenes_record"], v["E_rec"], v["E_rec_record"], "yes" if v["equal"] else "NO"))
    L_ += ["", "Gate: **%s**. Additional checks: truth-oriented decision cells %s; all other h2s cells %s; pairing counts %s." % (
        "PASSED" if g["passed"] else "FAILED", "equal" if g["truth_oriented_equal"] else "DIFFER",
        "equal" if g["all_h2s_cells_equal"] else "DIFFER", "equal" if g["pairing_equal"] else "DIFFER"), ""]
    if not g["passed"]:
        L_ += ["A1 is not done: the rebuild does not reproduce the X2 result of record (see the JSON for the differences).", ""]
        return "\n".join(L_) + "\n"
    for orient, lab in (("estimate", "Estimate-oriented (X2 primary)"), ("truth", "Truth-oriented (X2 a5 definition)")):
        L_ += ["## %s" % lab, "",
               "| Cell | n | <= 10 deg | (10, 20] deg | > 20 deg | exceedances from > 20 deg | E (<= 20 deg) [95 %% CI] | n (<= 20 deg) | threshold of record | E (all, record) |",
               "|---|---|---|---|---|---|---|---|---|---|"]
        for c in res["cells_order"]:
            v = res["results"][orient][c]
            L_.append("| %s | %d | %s | %s | %s | %s (%d of %d) | %s [%s, %s] | %d | %s | %s |" % (
                c, v["n_items"], fmt(v["shares"]["le10"]), fmt(v["shares"]["10_20"]), fmt(v["shares"]["gt20"]),
                fmt(v["share_of_exceedances_from_gt20"]), v["exceedances"]["from_gt20"], v["exceedances"]["total"],
                fmt(v["E_le20"]), fmt(v["E_le20_ci95"][0]), fmt(v["E_le20_ci95"][1]), v["E_le20_n_items"],
                fmt(v["threshold_of_record"], 4), fmt(v["E_all_record"])))
        L_.append("")
    L_ += ["## Reading (fixed in A1 section ii)", ""]
    for line in res["reading"]:
        L_.append("- " + line)
    L_ += ["", "## Method notes", ""]
    for line in res["method_notes"]:
        L_.append("- " + line)
    L_ += ["", "Integrity: C1_RUN_LOG sha256 %s... before and after; c1_av2_v01 manifest identical before and after: %s." % (
        res["integrity"]["run_log_after"][:8], res["integrity"]["manifest_after_ok"]), ""]
    return "\n".join(L_) + "\n"


def main():
    if os.path.exists(OUT_JSON):
        raise SystemExit("output exists; not overwriting: " + OUT_JSON)
    live("integrity and hashes", 0, 5)
    rl0 = C.assert_run_log("before x3-a1")
    ok0, man0 = C.manifest_check()
    if not ok0:
        raise SystemExit("X3 STOP: c1_av2_v01 manifest differs before x3-a1: %s" % json.dumps(man0)[:2000])
    hashes = check_hashes()
    live("integrity and hashes done", 1, 5)
    with heavy_lock("x3-a1: item rebuild (X2 train700 h2s)"):
        R = rebuild()
    gc.collect()
    rec = json.load(open(RESULT))
    prim, truth_rec = rec["family_h2s"]["primary"], rec["truth_oriented_decision_band"]
    thr_rec = {c: prim[c]["threshold"] for c in rec["decision_cells"]}
    scene_names = R["scene_names"]
    n_sc = len(scene_names)
    assert n_sc == 700
    live("items and reproduction gate", 2, 5)
    it_e = items(R["hr"], R["heading"], scene_names, "estimate")
    it_t = items(R["hr"], R["heading"], scene_names, "truth")
    dec = [tuple(c.split("|")) for c in rec["decision_cells"]]
    assert dec == X2.DEC
    gate = {"cells": {}}
    for c in dec:
        key = "|".join(c)
        it = it_e[c]
        er, es_ = e_rec(it, n_sc)
        p = prim[key]
        gate["cells"][key] = {"n": it["n"], "n_record": p["n"], "scenes": it["n_scenes"], "scenes_record": p["scenes"],
                              "E_rec": er, "E_rec_record": p["E_rec"], "E_scene": es_, "E_scene_record": p["E_scene"],
                              "equal": bool(it["n"] == p["n"] and it["n_scenes"] == p["scenes"] and er == p["E_rec"])}
    gate["passed"] = all(v["equal"] for v in gate["cells"].values())
    tdiff, adiff = {}, {}
    for c in dec:
        key, it = "|".join(c), it_t[c]
        er, _ = e_rec(it, n_sc)
        t_ = truth_rec[key]
        if not (it["n"] == t_["n"] and it["n_scenes"] == t_["scenes"] and er == t_["E_rec"]):
            tdiff[key] = {"n": it["n"], "scenes": it["n_scenes"], "E_rec": er, "record": t_}
    for c in L.CELLS:
        key = "|".join(c)
        it = it_e[c]
        if key not in prim and it is None:
            continue
        p = prim.get(key)
        if it is None or p is None or not (it["n"] == p["n"] and it["n_scenes"] == p["scenes"] and e_rec(it, n_sc)[0] == p["E_rec"]):
            adiff[key] = {"rebuilt": None if it is None else {"n": it["n"], "scenes": it["n_scenes"], "E_rec": e_rec(it, n_sc)[0]}, "record": p}
    pdiff = {k: [R["pairing"].get(k), v] for k, v in rec["pairing"].items() if R["pairing"].get(k) != v}
    gate.update({"truth_oriented_equal": not tdiff, "truth_oriented_differences": tdiff, "all_h2s_cells_equal": not adiff,
                 "all_h2s_cells_differences": adiff, "pairing_equal": not pdiff, "pairing_differences": pdiff,
                 "E_scene_equal": all(v["E_scene"] == v["E_scene_record"] for v in gate["cells"].values())})
    res = {"stamp": STAMP, "analysis": "X3 amendment A1: heading error behind the lateral diagnosis", "amendment_sha256": AMEND_SHA,
           "parent_plan_sha256": C.PLAN_SHA, "x2_result_sha256": C.sha256(RESULT), "hashes": hashes,
           "code": {"x3_a1_heading_v01.py": C.sha256(os.path.abspath(__file__))}, "reproduction_gate": gate,
           "rebuild": {k: R[k] for k in ("gtinfo", "per_worker", "n_rows_k", "scenes_in_exports", "horizon_rows_inpath")},
           "cells_order": list(rec["decision_cells"])}
    if gate["passed"]:
        live("bootstrap (B = 2000 per cell and orientation)", 3, 5)
        with heavy_lock("x3-a1: bootstrap"):
            out = {"estimate": {}, "truth": {}}
            for ci, c in enumerate(dec):
                key = "|".join(c)
                out["estimate"][key] = a1_cell(it_e[c], n_sc, ci, thr_rec[key])
                out["estimate"][key]["E_all_record"] = prim[key]["E_rec"]
                out["estimate"][key]["threshold_source"] = "family_h2s.primary[cell].threshold = max(0.05, E0) of record"
                out["truth"][key] = a1_cell(it_t[c], n_sc, ci, truth_rec[key]["threshold"])
                out["truth"][key]["E_all_record"] = truth_rec[key]["E_rec"]
                out["truth"][key]["threshold_source"] = "truth_oriented_decision_band[cell].threshold of record (X2 ran it with thr = {} -> 0.05)"
                out["truth"][key]["estimate_oriented_threshold_for_reference"] = thr_rec[key]
        res["results"] = out
        reading = []
        for c in ("car|<20|lat", "car|20-40|lat"):
            for orient in ("estimate", "truth"):
                v = out[orient][c]
                if v["E_le20_above_threshold"]:
                    s = ("%s, %s-oriented: E on items with heading error <= 20 deg is %s [%s, %s] against the threshold %s; it still "
                         "exceeds the threshold, so by A1 (ii) the lateral under-coverage there is not explained by heading error"
                         % (c, orient, fmt(v["E_le20"]), fmt(v["E_le20_ci95"][0]), fmt(v["E_le20_ci95"][1]), fmt(v["threshold_of_record"], 4)))
                    s += " (the 95 % interval lies entirely above the threshold)." if v["ci_lower_above_threshold"] else \
                        " (point estimate only: the 95 % interval reaches below the threshold)."
                else:
                    s = ("%s, %s-oriented: E on items with heading error <= 20 deg is %s [%s, %s] against the threshold %s; it falls "
                         "below the threshold, so by A1 (ii) the cell's lateral failure is largely a heading-error effect"
                         % (c, orient, fmt(v["E_le20"]), fmt(v["E_le20_ci95"][0]), fmt(v["E_le20_ci95"][1]), fmt(v["threshold_of_record"], 4)))
                    s += " (the 95 % interval lies entirely below the threshold)." if v["ci_upper_below_threshold"] else \
                        " (point estimate only: the 95 % interval reaches above the threshold)."
                reading.append(s)
        reading.append("Longitudinal cells are reported for completeness; A1 (ii) states its reading for the lateral cells.")
        res["reading"] = reading
    else:
        res["results"] = None
        res["reading"] = ["Reproduction gate failed: A1 is not done."]
    res["method_notes"] = [
        "Heading error = |wrap(psi_track - psi_annotation)| at the decision keyframe k, folded to [0, 90] deg (min(d, 180 - d)). "
        "psi_track is the record's box yaw at k (quat_yaw of the exported rotation), which defines the item's axes at 2 s; "
        "psi_annotation is the yaw of the annotation build_table paired at k (its centre equals the row's gx, gy exactly). "
        "Both are global-frame yaws from the same quat_yaw formula.",
        "Exceedance: U > z_0.95 = %r (L.Z95, the value X2 used; the amendment writes 1.645)." % L.Z95,
        "E is record-weighted as X2's E_rec: exceedances / items, items pooled over scenes.",
        "Bootstrap: scene-cluster, B = 2000, numpy default_rng([20261211, cell]) with cell = 0..3 in X2's DEC order "
        "(car <20 lat, car 20-40 lat, car <20 long, car 20-40 long); the same seed (hence the same scene weights) is used for the "
        "estimate- and truth-oriented versions of a cell. Weights: L.boot_weights (multinomial over the 700 scenes, X2's convention); "
        "replicate = ratio of weighted sums; pointwise 95 % percentile interval (not X2's simultaneous sup-t band).",
        "Thresholds: estimate-oriented = max(0.05, E0) of record (family_h2s.primary); truth-oriented = the threshold of record in "
        "truth_oriented_decision_band (0.05, as X2 ran a5 with thr = {}). The estimate-oriented E0 threshold is listed for reference.",
        "Truth orientation is X2's (cell_items orient='truth'): the same track axes; the separating filter and sign use the "
        "annotation's centre at 2 s in place of the estimate. The heading error of an item is the same in both orientations "
        "(it belongs to the record at k).",
        "Memory-lean rebuild (about 2 GB free): lean streaming ground-truth loader (same samples, same per-sample annotation order, "
        "only the keys the frozen functions read, plus yaw); build_table per export worker (scenes disjoint across workers, "
        "asserted); only paired, in-path rows at k kept for the horizon step (the only rows cell_items uses). The reproduction "
        "gate checks the result end to end.",
    ]
    gc.collect()
    live("integrity after", 4, 5)
    rl1 = C.assert_run_log("after x3-a1")
    ok1, man1 = C.manifest_check()
    res["integrity"] = {"run_log_before": rl0, "run_log_after": rl1, "manifest_before_ok": ok0, "manifest_after_ok": ok1,
                        "manifest_after": man1 if not ok1 else {"files": man1["files_now"]}}
    res["peak_working_set_mb"] = X2.peak_mb()
    res["wall_s"] = round(time.time() - T0, 1)
    res["written"] = time.strftime("%Y-%m-%d %H:%M:%S")
    C.jdump(OUT_JSON, res, refuse_existing=True)
    C.wtext(OUT_MD, write_md(res), refuse_existing=True)
    live("done: gate %s" % ("PASSED" if gate["passed"] else "FAILED"), 5, 5, "outputs in 60_RESULTS/x3_explore_v01/a1_heading")
    if not ok1:
        raise SystemExit("X3 STOP: c1_av2_v01 manifest differs after x3-a1")


if __name__ == "__main__":
    main()
