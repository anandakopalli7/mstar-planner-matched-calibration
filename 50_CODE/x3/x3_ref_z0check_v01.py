#!/usr/bin/env python3
"""x3_ref_z0check_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan section 2 (d1).

Secondary validation of reference d1: the arm-Z0 decisions that x3_ref_items_v01 computed with k8_sim_v04.plan_step (stored in
d_ref/items_x3ref_d1_<t>.npz, x3_z0_*) must equal the arm-Z0 decisions of the decision-mode run of record
(60_RESULTS/c1_av2_v01/runs/decisions_<t>_within_lt3d_decide.npz with episodes_<t>_within_lt3d_decide.jsonl), decision by decision:
infeasible, lam (back-off level; -1 = emergency stop), v_now, v_chosen, v_log and ds_plan (= the chosen candidate's leashed planned
arc length 0.5 s ahead minus s_k, i.e. the d1 reference at 0.5 s). Read-only on the record.
Usage: python -B x3_ref_z0check_v01.py --trk t1 t3
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402

FIELDS = ("infeasible", "lam", "v_now", "v_chosen", "v_log", "ds_plan")


def check(trk):
    runs = os.path.join(C.W, "60_RESULTS", "c1_av2_v01", "runs")
    dp = os.path.join(runs, "decisions_%s_within_lt3d_decide.npz" % trk)
    ep = os.path.join(runs, "episodes_%s_within_lt3d_decide.jsonl" % trk)
    eps = {}
    for ln in open(ep, encoding="utf-8"):
        r = json.loads(ln)
        if r["arm"] == "Z0":
            eps[int(r["episode"])] = r["scene"]
    zd = np.load(dp)
    epi = zd["episode"]
    msk = np.isin(epi, np.array(sorted(eps)))
    recd = {(eps[int(e)], int(k)): i for i, (e, k) in enumerate(zip(epi, zd["k"])) if msk[i]}
    rec = {f: zd[f] for f in FIELDS}
    zi = np.load(os.path.join(C.D_REF, "items_x3ref_d1_%s.npz" % trk))
    names = [str(x) for x in zi["scene_names"]]
    mine = {f: zi["x3_z0_" + f] for f in FIELDS}
    n, miss, res = len(zi["x3_z0_k"]), 0, {}
    idx = []
    for j in range(n):
        key = (names[int(zi["x3_z0_scene"][j])], int(zi["x3_z0_k"][j]))
        i = recd.get(key)
        if i is None:
            miss += 1
        idx.append(-1 if i is None else i)
    idx = np.array(idx)
    ok = idx >= 0
    for f in FIELDS:
        a, b = mine[f][ok].astype(float), rec[f][idx[ok]].astype(float)
        res[f] = {"equal": int(np.sum((a == b) | (np.isnan(a) & np.isnan(b)))), "of": int(ok.sum()),
                  "max_abs": float(np.nanmax(np.abs(a - b))) if ok.any() else None}
    allok = miss == 0 and len(recd) == n and all(v["equal"] == v["of"] for v in res.values())
    return {"stamp": C.STAMP, "tracker": trk, "decisions_mine": n, "decisions_record_z0": len(recd), "unmatched": miss,
            "fields": res, "pass": bool(allok), "record_decisions": dp, "record_decisions_sha256": C.sha256_path(dp),
            "record_episodes_sha256": C.sha256_path(ep), "d1_items_sha256": C.sha256_path(os.path.join(C.D_REF, "items_x3ref_d1_%s.npz" % trk)),
            "z0_infeasible_share": float(np.mean(mine["infeasible"])), "z0_estop_share": float(np.mean(mine["lam"] == -1.0))}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", nargs="+", required=True, choices=("t1", "t3"))
    a = ap.parse_args(argv)
    C.run_log_ok()
    for trk in a.trk:
        out = check(trk)
        out["code_sha256"] = C.code_record([os.path.abspath(__file__), C.__file__])
        C.save_json(os.path.join(C.D_REF, "VALIDATION_d1_z0_%s.json" % trk), out)
        print(trk, "PASS" if out["pass"] else "FAIL", json.dumps(out["fields"]), out["unmatched"])
    C.run_log_ok()


if __name__ == "__main__":
    main()
