#!/usr/bin/env python3
"""Cross-check of the joint runs against the K8 v02 exploratory runs (Claude line, 2 Nov 2026): for every arm both decision-mode
runs hold (B0, B1, B3, B4, B6, B9, Mstar), every per-decision field (DEC_FIELDS, stats, trk) and every episode summary of the
k8_run_v04 --joint run equals the k8_run_v02 run scene by scene. Reads the v02 run directory only (never writes there).
Usage: python -B tests/k8_joint_crosscheck_v01.py --joint-runs <dir> --v02-runs <dir> --tags t1 t3 --out <json>
"""
import argparse
import json
import os
import sys

import numpy as np

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, K8)
import k8_sim_v04 as S  # noqa: E402

SKIP_SUMMARY = ("episode", "stamp", "fold")


def load(run_dir, tm):
    eps = [json.loads(l) for l in open(os.path.join(run_dir, "episodes_%s.jsonl" % tm))]
    D = np.load(os.path.join(run_dir, "decisions_%s.npz" % tm))
    fields = [f for f in ("k",) + tuple(S.DEC_FIELDS) + ("stats", "trk")]
    e = D["episode"]
    order = np.argsort(e, kind="stable")
    starts = np.searchsorted(e[order], np.arange(len(eps)))
    ends = np.searchsorted(e[order], np.arange(len(eps)), side="right")
    arr = {f: D[f][order] for f in dict.fromkeys(fields)}
    return eps, arr, starts, ends


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--joint-runs", required=True)
    ap.add_argument("--v02-runs", required=True)
    ap.add_argument("--tags", nargs="+", default=["t1", "t3"])
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = {"tags": {}}
    ok_all = True
    for tag in a.tags:
        tm = "%s_decide" % tag
        ej, aj, sj, nj = load(a.joint_runs, tm)
        ev, av, sv, nv = load(a.v02_runs, tm)
        iv = {(o["scene"], o["arm"]): i for i, o in enumerate(ev)}
        shared = sorted({o["arm"] for o in ej} & {o["arm"] for o in ev})
        bad, n_eps, n_dec = [], 0, 0
        for i, o in enumerate(ej):
            if o["arm"] not in shared:
                continue
            k = iv[(o["scene"], o["arm"])]
            ov = ev[k]
            if {x: y for x, y in o.items() if x not in SKIP_SUMMARY} != {x: y for x, y in ov.items() if x not in SKIP_SUMMARY}:
                bad.append(["summary", o["scene"], o["arm"]])
            for f in aj:
                x, y = aj[f][sj[i]:nj[i]], av[f][sv[k]:nv[k]]
                if not np.array_equal(x, y, equal_nan=(x.dtype.kind == "f")):
                    bad.append([f, o["scene"], o["arm"]])
            n_eps += 1
            n_dec += int(nj[i] - sj[i])
        res["tags"][tag] = {"shared_arms": shared, "episodes_compared": n_eps, "decisions_compared": n_dec, "mismatches": bad[:50],
                            "n_mismatches": len(bad), "equal": not bad}
        ok_all = ok_all and not bad
        print(tag, "shared arms", shared, "episodes", n_eps, "decisions", n_dec, "mismatches", len(bad), flush=True)
    res["verdict"] = "EQUAL" if ok_all else "DIFFERENT"
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1)
    print(res["verdict"])


if __name__ == "__main__":
    main()
