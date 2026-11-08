#!/usr/bin/env python3
"""TPP arm join keys (Claude line, v01, 2 Nov 2026). Run in the CANMOT environment (canmot310, Python 3.10).

For every scene of one tracker's validation cache (W/30_DATA/k6/cache_v02_<t>_val, 150 scenes) this enumerates the K8
calibration records and items exactly as 50_CODE/k8/k8_items_v02.scene_items does (imported read-only, unchanged), and
adds what the Trajectron++ arm needs to predict them and to score them later along the same normal:
  * keys: scene name, k, h, row (track row in the cache), tid (track id), inst (paired ground-truth instance), pair (the
    per-scene record id that k8_items_v02 gives; the K8 items carry it), cache class, Trajectron++ node type;
  * histories: contiguous tracker history of tid ending at k (records with score >= 0.4, i.e. the deployed output), and
    contiguous ground-truth annotation history of inst ending at k, with the strata {2, 3-4, >=5};
  * geometry for the paired score: the object axes from the tracker yaw, the toward-ego sign of each axis at the
    reference ego pose (the logged pose at t_k + 0.5 (h + 1) s, as k8_items_v02), the reference ego centre, and the
    CTRV-predicted ego centre at the same time (manuscript III / IV-A definition), the ground-truth row at k + h + 1;
  * strata as in K8 (group, range, motion, l0 per axis, relied axis rel, in-path).
Consistency checks (asserted): every record's stored signed errors D_long / D_lat and gaps equal the ones rebuilt from the
stored sign, axes and reference pose; every item is a record axis with gap > 0 and ref_relied = (axis == rel).
The tracker-arm errors themselves (dx, dy, D, sd) are NOT written: the output carries keys and geometry only.
Usage: python -I tpp_keys_v01.py --cache <val cache dir> --out <keys npz> [--workers n] [--scenes s1 s2 ...]
"""
import argparse
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.join(W_ROOT, "50_CODE", "k8"))
import tpp_common_v01 as C  # noqa: E402
import k8_items_v02 as K8I  # noqa: E402

S = K8I.S   # k6_sim_v02, as imported by k8_items_v02

REC_OUT = ("k", "h", "g", "r", "row", "inst", "pair", "m", "l0_long", "l0_lat", "rel", "inpath", "yaw", "gap_long", "gap_lat")
ITEM_OUT = ("k", "h", "g", "r", "a", "m", "l0", "inpath", "pair", "ref_relied")


def _hist_index(keys_k, keys_id):
    """dict (id, k) -> contiguous run length ending at k."""
    out = {}
    order = np.lexsort((keys_k, keys_id))
    ids, ks = keys_id[order], keys_k[order]
    for u in np.unique(ids):
        sel = ids == u
        kk = ks[sel]
        for kv, n in zip(kk, C.contiguous_run_lengths(kk)):
            out[(int(u), int(kv))] = int(n)
    return out


def scene_keys(job):
    path, si, scene = job
    _, it, rc, st = K8I.scene_items((path, si))
    sc = S.Scene(path)
    tr, gt = sc.tr, sc.gt
    n = len(rc["k"])
    out = {k: np.asarray(rc[k]) for k in REC_OUT}
    ext = {key: np.zeros(n) for key in ("sign_long", "sign_lat", "cref_x", "cref_y", "cctrv_x", "cctrv_y")}
    ext.update({key: np.zeros(n, np.int64) for key in ("tid", "cls", "tpp_type", "hist_trk", "hist_gt", "gt_row", "gt_cls",
                                                         "gt_row_k")})
    chk = {"D_maxabs": 0.0, "gap_maxabs": 0.0}
    if n:
        htr = _hist_index(tr["k"].astype(int), tr["tid"].astype(int))
        hgt = _hist_index(gt["k"].astype(int), gt["inst"].astype(int))
        gt_k_inst = {(int(i), int(kv)): r_ for r_, (kv, i) in enumerate(zip(gt["k"], gt["inst"]))}
        ctrv_cache = {}
        for i in range(n):
            k, h, row, inst = int(rc["k"][i]), int(rc["h"][i]), int(rc["row"][i]), int(rc["inst"][i])
            assert int(tr["k"][row]) == k and int(tr["inst"][row]) == inst
            tk = float(sc.kf_t[k])
            t_h = 0.5 * (h + 1)
            s_ref = sc.s_log(tk + S.EVAL_T[2 * h + 1])
            assert abs(S.EVAL_T[2 * h + 1] - t_h) < 1e-12
            ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s_ref)))
            cx, cy = ex + S.R2C * math.cos(eyaw), ey + S.R2C * math.sin(eyaw)
            yaw = float(tr["yaw"][row])
            assert yaw == float(rc["yaw"][i])
            ax = np.array([[math.cos(yaw), math.sin(yaw)], [-math.sin(yaw), math.cos(yaw)]])
            m_pred = tr["pred"][row, h, :2]
            sp = ax @ (np.array([cx, cy]) - m_pred)
            sgn = np.sign(sp)
            e = np.array([rc["dx"][i], rc["dy"][i]])
            D_re = sgn * (ax @ e)
            chk["D_maxabs"] = max(chk["D_maxabs"], float(np.max(np.abs(D_re - np.array([rc["D_long"][i], rc["D_lat"][i]])))))
            ue, ve = np.array([math.cos(eyaw), math.sin(eyaw)]), np.array([-math.sin(eyaw), math.cos(eyaw)])
            he = (S.EGO_L / 2 + S.BUFFER) * np.abs(ax @ ue) + (S.EGO_W / 2 + S.BUFFER) * np.abs(ax @ ve)
            half = np.array([0.5 * tr["l"][row], 0.5 * tr["w"][row]])
            gap_re = np.abs(sp) - (half + he)
            chk["gap_maxabs"] = max(chk["gap_maxabs"], float(np.max(np.abs(gap_re - np.array([rc["gap_long"][i], rc["gap_lat"][i]])))))
            if k not in ctrv_cache:
                (px, py, pyaw0), v, w = S.sensor_ctrv(sc, k)
                ctrv_cache[k] = (px, py, pyaw0, v, w)
            px, py, pyaw0, v, w = ctrv_cache[k]
            if abs(w) < 1e-4:                           # the CTRV of k6_sim_v02.strata at th = 0.5 (h + 1)
                qx, qy, qyaw = px + v * t_h * math.cos(pyaw0), py + v * t_h * math.sin(pyaw0), pyaw0
            else:
                qyaw = pyaw0 + w * t_h
                qx = px + v / w * (math.sin(qyaw) - math.sin(pyaw0))
                qy = py - v / w * (math.cos(qyaw) - math.cos(pyaw0))
            ext["sign_long"][i], ext["sign_lat"][i] = sgn
            ext["cref_x"][i], ext["cref_y"][i] = cx, cy
            ext["cctrv_x"][i], ext["cctrv_y"][i] = qx + S.R2C * math.cos(qyaw), qy + S.R2C * math.sin(qyaw)
            tid = int(tr["tid"][row])
            ext["tid"][i] = tid
            ext["cls"][i] = int(tr["cls"][row])
            ext["tpp_type"][i] = int(C.TPP_TYPE_OF_CLS[int(tr["cls"][row])])
            ext["hist_trk"][i] = htr[(tid, k)]
            ext["hist_gt"][i] = hgt.get((inst, k), 0)
            ext["gt_row_k"][i] = gt_k_inst.get((inst, k), -1)
            gr = sc.gt_at[k + h + 1].get(inst)
            assert gr is not None and not (gt["inrack"][gr] if "inrack" in gt else False)
            ext["gt_row"][i] = gr
            ext["gt_cls"][i] = int(gt["cls"][gr])
    out.update(ext)
    items = {k: np.asarray(it[k]) for k in ITEM_OUT}
    return si, scene, out, items, st, chk


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True, help="one validation cache dir (cache_v02_<t>_val)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--scenes", nargs="*", default=None, help="subset (tests only)")
    a = ap.parse_args()
    t0 = time.time()
    mp = os.path.join(a.cache, "MANIFEST.json")
    man = json.load(open(mp))
    names = sorted(man["scenes"])
    if a.scenes:
        assert all(s in man["scenes"] for s in a.scenes)
        names = [s for s in names if s in a.scenes]
    jobs = []
    for si, scene in enumerate(names):
        p = os.path.join(a.cache, scene + ".npz")
        assert C.sha256_path(p) == man["scenes"][scene]["sha256"], "cache file differs from its manifest: " + p
        jobs.append((p, si, scene))
    if a.workers > 1:
        with Pool(a.workers) as pool:
            res = list(pool.imap_unordered(scene_keys, jobs, chunksize=1))
    else:
        res = [scene_keys(j) for j in jobs]
    res.sort(key=lambda x: x[0])
    rec_cols = list(REC_OUT) + ["sign_long", "sign_lat", "cref_x", "cref_y", "cctrv_x", "cctrv_y", "tid", "cls", "tpp_type",
                                "hist_trk", "hist_gt", "gt_row", "gt_cls", "gt_row_k"]
    R = {c: [] for c in rec_cols}
    I = {c: [] for c in ITEM_OUT}
    rec_s, item_s, item_rec = [], [], []
    stats, chk = {}, {"D_maxabs": 0.0, "gap_maxabs": 0.0}
    n_rec = 0
    for si, scene, out, items, st, ck in res:
        nr = len(out["k"])
        for c in rec_cols:
            R[c].append(np.asarray(out[c]))
        rec_s.append(np.full(nr, si, np.int32))
        # join items to records by (scene, pair); check the item is a record axis with gap > 0
        pid_to_rec = {int(p): j for j, p in enumerate(out["pair"])}
        assert len(pid_to_rec) == nr, "pair ids not unique within " + scene
        ni = len(items["k"])
        idx = np.array([pid_to_rec[int(p)] for p in items["pair"]], np.int64) if ni else np.zeros(0, np.int64)
        if ni:
            for c in ("k", "h", "g", "r", "inpath"):
                assert np.array_equal(np.asarray(items[c]).astype(np.int64), np.asarray(out[c])[idx].astype(np.int64)), c
            gapsel = np.where(items["a"] == 0, out["gap_long"][idx], out["gap_lat"][idx])
            assert np.all(gapsel > 0)
            assert np.array_equal(items["ref_relied"].astype(bool), items["a"] == out["rel"][idx])
            l0sel = np.where(items["a"] == 0, out["l0_long"][idx], out["l0_lat"][idx])
            assert np.array_equal(l0sel.astype(np.int64), items["l0"].astype(np.int64))
        n_axes = int(np.sum(out["gap_long"] > 0) + np.sum(out["gap_lat"] > 0)) if nr else 0
        assert n_axes == ni, "items != record axes with gap > 0 in " + scene
        for c in ITEM_OUT:
            I[c].append(np.asarray(items[c]))
        item_s.append(np.full(ni, si, np.int32))
        item_rec.append(idx + n_rec)
        n_rec += nr
        stats[scene] = dict(st, records=nr, items=ni)
        chk = {key: max(chk[key], ck[key]) for key in chk}
    assert chk["D_maxabs"] < 1e-6 and chk["gap_maxabs"] < 1e-6, chk
    o = {}
    for c in rec_cols:
        x = [v for v in R[c] if len(v)]
        o["rec_" + c] = np.concatenate(x) if x else np.zeros(0)
    for c in ITEM_OUT:
        x = [v for v in I[c] if len(v)]
        o["item_" + c] = np.concatenate(x) if x else np.zeros(0)
    o["rec_s"] = np.concatenate(rec_s) if rec_s else np.zeros(0, np.int32)
    o["item_s"] = np.concatenate(item_s) if item_s else np.zeros(0, np.int32)
    o["item_rec"] = np.concatenate(item_rec) if item_rec else np.zeros(0, np.int64)
    for c in ("k", "h", "g", "r", "row", "inst", "pair", "m", "l0_long", "l0_lat", "rel", "tid", "cls", "tpp_type", "hist_trk",
              "hist_gt", "gt_row", "gt_cls", "gt_row_k"):
        o["rec_" + c] = o["rec_" + c].astype(np.int32)
    o["rec_inpath"] = o["rec_inpath"].astype(bool)
    for c in ("k", "h", "g", "r", "a", "m", "l0", "pair"):
        o["item_" + c] = o["item_" + c].astype(np.int32)
    o["item_inpath"] = o["item_inpath"].astype(bool)
    o["item_ref_relied"] = o["item_ref_relied"].astype(bool)
    o["rec_hist_stratum_trk"] = C.hist_stratum(o["rec_hist_trk"])
    o["rec_hist_stratum_gt"] = C.hist_stratum(o["rec_hist_gt"])
    o["scene_names"] = np.array(names)
    o["scene_logs"] = np.array([man["scenes"][s]["log"] for s in names])
    o["scene_is_dev"] = np.array([s in K8I.DEV_SCENES for s in names])
    o["cache_dir"] = np.array(os.path.abspath(a.cache))
    hashes = {"tpp_keys_v01": C.sha256_path(os.path.abspath(__file__)), "tpp_common_v01": C.sha256_path(C.__file__),
              "k8_items_v02": C.sha256_path(K8I.__file__), "k6_sim_v02": C.sha256_path(S.__file__),
              "manifest": C.sha256_path(mp)}
    o["hashes_json"] = np.array(json.dumps(hashes))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    np.savez_compressed(a.out, **o)
    summ = {"cache": os.path.abspath(a.cache), "scenes": len(names), "records": int(len(o["rec_k"])), "items": int(len(o["item_k"])),
            "items_ref_relied": int(o["item_ref_relied"].sum()), "consistency": chk, "hashes": hashes,
            "out_sha256": C.sha256_path(a.out), "seconds": round(time.time() - t0, 1), "per_scene": stats}
    json.dump(summ, open(a.out.replace(".npz", "_summary.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "per_scene"}))
    print("TPP KEYS V01 DONE")


if __name__ == "__main__":
    main()
