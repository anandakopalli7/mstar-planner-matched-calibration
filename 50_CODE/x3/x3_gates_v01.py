#!/usr/bin/env python3
"""X3 validation gates V0 and V2 (x3-core agent, x3_gates_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan section 1.

V0 (the runner): for the given arms, the X3 run's decision arrays (every DEC field, including infeasible and lam, plus stats and
trk), counts (cell, n, exceed) and calibration tables (key, values), and the episode summaries, equal the run of record's exactly,
after re-indexing episodes by (scene, arm). Any mismatch fails the gate.
V2 (the partitions): for every arm, population (PD7_primary, SD1_7_gap_le_5m, PD_inpath, NIP_not_in_path) and log, each
partition's tagged counts summed over its bins and the relied axes equal the counts of record (k6_analyse_v02.mask with
k8_analyse_v04.POP_DECIDE, the record's population filter, summed over all cells), for n and for the exceedances.
Usage: python -B x3_gates_v01.py v0|v2 --tracker t1 --run-dir <dir> --tag <tag> --arms Mstar B0 ... --out <json>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(X3))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k8"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
import k8_sim_v04 as S  # noqa: E402
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402

POPS4 = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath", "NIP_not_in_path")
CELLS4 = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3), "NIP_not_in_path": (0, 2)}


def load_outputs(run_dir, tag, need=("episodes", "counts", "decisions", "cal")):
    o = {}
    if "episodes" in need:
        o["eps"] = [json.loads(l) for l in open(os.path.join(run_dir, "episodes_%s.jsonl" % tag))]
    if "counts" in need:
        o["counts"] = dict(np.load(os.path.join(run_dir, "counts_%s.npz" % tag)))
    if "decisions" in need:
        o["dec"] = dict(np.load(os.path.join(run_dir, "decisions_%s.npz" % tag)))
    if "cal" in need:
        o["cal"] = dict(np.load(os.path.join(run_dir, "cal_%s.npz" % tag)))
    return o


def _ordered(ep_arr, ep_scene_rank, extra=None):
    """Indices of the rows whose episode is in ep_scene_rank (dict episode -> scene rank), ordered by (scene rank, extra, row)."""
    sel = np.flatnonzero(np.isin(ep_arr, np.fromiter(ep_scene_rank.keys(), np.int64)))
    sr = np.array([ep_scene_rank[int(e)] for e in ep_arr[sel]], np.int64)
    keys = (sel, extra[sel], sr) if extra is not None else (sel, sr)
    return sel[np.lexsort(keys)]


def _eq(a, b):
    a, b = np.asarray(a), np.asarray(b)
    if a.shape != b.shape:
        return False
    if a.dtype.kind == "f" or b.dtype.kind == "f":
        return bool(np.array_equal(a.astype(float), b.astype(float), equal_nan=True))
    return bool(np.array_equal(a, b))


def v0(rec, mine, arms, scenes=None):
    """Exact comparison of the X3 run (mine) with the run of record (rec) for each arm."""
    out = {}
    skip = {"episode", "stamp", "base_arm", "_local"}
    for arm in arms:
        er = {o["scene"]: o for o in rec["eps"] if o["arm"] == arm}
        em = {o["scene"]: o for o in mine["eps"] if o["arm"] == arm}
        sc = sorted(em) if scenes is None else sorted(scenes)
        r = {"scenes": len(sc), "episode_summaries_equal": True, "summary_mismatches": []}
        assert set(sc) <= set(er) and set(sc) <= set(em), "scenes missing for " + arm
        for s in sc:
            a_, b_ = {k: v for k, v in er[s].items() if k not in skip}, {k: v for k, v in em[s].items() if k not in skip}
            if json.dumps(a_, sort_keys=True) != json.dumps(b_, sort_keys=True):
                r["episode_summaries_equal"] = False
                r["summary_mismatches"].append(s)
        rank = {s: i for i, s in enumerate(sc)}
        rr = {int(er[s]["episode"]): rank[s] for s in sc}
        mr = {int(em[s]["episode"]): rank[s] for s in sc}
        # decisions
        ir = _ordered(rec["dec"]["episode"], rr, rec["dec"]["k"])
        im = _ordered(mine["dec"]["episode"], mr, mine["dec"]["k"])
        r["decision_rows"] = [int(len(ir)), int(len(im))]
        dec_eq = {}
        for f in list(S.DEC_FIELDS) + ["stats", "trk"]:
            dec_eq[f] = len(ir) == len(im) and _eq(rec["dec"][f][ir], mine["dec"][f][im])
        r["decisions_equal_by_field"] = dec_eq
        r["decisions_equal"] = bool(all(dec_eq.values()))
        # counts
        ir = _ordered(rec["counts"]["episode"], rr, rec["counts"]["cell"])
        im = _ordered(mine["counts"]["episode"], mr, mine["counts"]["cell"])
        r["count_rows"] = [int(len(ir)), int(len(im))]
        r["counts_equal"] = bool(len(ir) == len(im) and all(_eq(rec["counts"][f][ir], mine["counts"][f][im]) for f in ("cell", "n", "exceed"))
                                 and _eq(np.array([rr[int(e)] for e in rec["counts"]["episode"][ir]]), np.array([mr[int(e)] for e in mine["counts"]["episode"][im]])))
        # calibration tables
        ir = _ordered(rec["cal"]["episode"], rr, rec["cal"]["key"])
        im = _ordered(mine["cal"]["episode"], mr, mine["cal"]["key"])
        r["cal_rows"] = [int(len(ir)), int(len(im))]
        r["cal_equal"] = bool(len(ir) == len(im) and _eq(rec["cal"]["key"][ir], mine["cal"]["key"][im]) and _eq(rec["cal"]["values"][ir], mine["cal"]["values"][im]))
        r["equal"] = bool(r["decisions_equal"] and r["counts_equal"] and r["cal_equal"] and r["episode_summaries_equal"])
        out[arm] = r
    return out


def pop_masks():
    import k6_analyse_v02 as A
    import k8_analyse_v04 as K
    return {p: A.mask(**K.POP_DECIDE[p]) for p in POPS4}


def record_pop_totals(rec, arm, masks, only=None):
    """Per scene and population: (n, exceed) of the counts of record, summed over every cell of the population."""
    ep = {int(o["episode"]): o["scene"] for o in rec["eps"] if o["arm"] == arm and (only is None or o["scene"] in only)}
    c = rec["counts"]
    sel = np.isin(c["episode"], np.fromiter(ep.keys(), np.int64))
    e_, cell, n, x = c["episode"][sel], c["cell"][sel], c["n"][sel].astype(np.int64), c["exceed"][sel].astype(np.int64)
    scenes = sorted(set(ep.values()))
    srank = {s: i for i, s in enumerate(scenes)}
    row = np.array([srank[ep[int(q)]] for q in e_], np.int64)
    out = {}
    for p, m in masks.items():
        k = m[cell]
        out[p] = (np.bincount(row[k], weights=n[k], minlength=len(scenes)).astype(np.int64),
                  np.bincount(row[k], weights=x[k], minlength=len(scenes)).astype(np.int64))
    return scenes, out


def parts_pop_totals(mine_eps, parts, arm, scenes):
    """Per partition, scene and population: (n, exceed) from the partition arrays, summed over bins and axes."""
    import x3_run_v01 as R
    ep = {int(o["episode"]): o["scene"] for o in mine_eps if o["arm"] == arm}
    srank = {s: i for i, s in enumerate(scenes)}
    acc = np.zeros((len(scenes), R.N_PKEY, 2), np.int64)
    for i, e in enumerate(parts["episode"].tolist()):
        if e in ep:
            acc[srank[ep[e]]] = parts["acc"][i]
    keys = np.arange(R.N_PKEY)
    dec = np.array([R.decode_pkey(k) for k in keys])           # c4, part, bin, axis
    out = {}
    for pi, pn in enumerate(R.PARTS):
        out[pn] = {}
        for p in POPS4:
            m = (dec[:, 1] == pi) & np.isin(dec[:, 0], CELLS4[p])
            out[pn][p] = (acc[:, m, 0].sum(1), acc[:, m, 1].sum(1))
    bins_used = {pn: sorted(set(int(b) for b in dec[(dec[:, 1] == pi) & (acc[:, :, 0].sum(0) > 0), 2])) for pi, pn in enumerate(R.PARTS)}
    return out, bins_used


def v2(rec, mine_eps, parts, arms, masks):
    res = {}
    for arm in arms:
        scenes, rt = record_pop_totals(rec, arm, masks, {o["scene"] for o in mine_eps if o["arm"] == arm})
        pt, bins_used = parts_pop_totals(mine_eps, parts, arm, scenes)
        r = {"scenes": len(scenes), "bins_used": bins_used, "by_partition": {}}
        ok_all = True
        for pn, byp in pt.items():
            rp = {}
            for p in POPS4:
                eq_n = bool(np.array_equal(byp[p][0], rt[p][0]))
                eq_x = bool(np.array_equal(byp[p][1], rt[p][1]))
                rp[p] = {"n_equal": eq_n, "exceed_equal": eq_x, "records": int(rt[p][0].sum()), "exceed": int(rt[p][1].sum()),
                         "logs_differing": int(np.sum((byp[p][0] != rt[p][0]) | (byp[p][1] != rt[p][1])))}
                ok_all = ok_all and eq_n and eq_x
            r["by_partition"][pn] = rp
        r["equal"] = ok_all
        res[arm] = r
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("gate", choices=["v0", "v2"])
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--arms", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    t0 = time.time()
    C.assert_run_log("gate %s start" % a.gate)
    rec_tag = "%s_decide" % C.TAG_REC[a.tracker]
    if a.gate == "v0":
        rec = load_outputs(C.REC_RUNS, rec_tag)
        mine = load_outputs(a.run_dir, a.tag)
        partial = len({o["scene"] for o in mine["eps"]}) < 375
        res = v0(rec, mine, a.arms)
        ok = all(v["equal"] for v in res.values())
        out = {"stamp": C.STAMP, "gate": "V0", "tracker": a.tracker, "record": os.path.join(C.REC_RUNS, rec_tag), "x3_run": os.path.join(a.run_dir, a.tag),
               "partial": partial, "arms": a.arms, "by_arm": res, "passed": bool(ok and not partial), "seconds": round(time.time() - t0, 1)}
    else:
        rec = load_outputs(C.REC_RUNS, rec_tag, ("episodes", "counts"))
        mine_eps = [json.loads(l) for l in open(os.path.join(a.run_dir, "episodes_%s.jsonl" % a.tag))]
        parts = dict(np.load(os.path.join(a.run_dir, "parts_%s.npz" % a.tag)))
        rr = json.load(open(os.path.join(a.run_dir, "run_record_%s.json" % a.tag)))
        res = v2(rec, mine_eps, parts, a.arms, pop_masks())
        ok = all(v["equal"] for v in res.values())
        out = {"stamp": C.STAMP, "gate": "V2", "tracker": a.tracker, "x3_run": os.path.join(a.run_dir, a.tag), "arms": a.arms,
               "partial": bool(rr.get("partial")), "partition_checks_in_run": rr.get("partition_checks"), "by_arm": res,
               "passed": bool(ok and not rr.get("partial")), "seconds": round(time.time() - t0, 1)}
    C.assert_run_log("gate %s end" % a.gate)
    C.jdump(a.out, out)
    print(json.dumps({"gate": out["gate"], "tracker": a.tracker, "passed": out["passed"], "partial": out["partial"],
                      "by_arm": {k: v["equal"] for k, v in res.items()}, "seconds": out["seconds"]}))


if __name__ == "__main__":
    main()
