#!/usr/bin/env python3
"""K6 development check (Claude line, v01, 31 Oct 2026): summarises a --dev run on the 10 nuScenes-mini scenes (excluded from
K6) per arm and delay, and exercises the full analysis code path with the support rule relaxed to 2 scenes and 1 log (the
dev set is far below the frozen rule). Its numbers are harness diagnostics, not K6 evidence.
Usage: python -B k6_dev_check_v01.py --runs <dir> --tags <t1> <t3> --manifests <...> --out <json>
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import k6_analyse_v01 as A  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tags", nargs=2, required=True)
    ap.add_argument("--manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A.DEV_SCENES = ()
    A.MIN_SCENES, A.MIN_LOGS = 2, 1
    log_of_scene = {}
    for p in a.manifests:
        for s, info in json.load(open(p))["scenes"].items():
            log_of_scene[s] = info["log"]
    out = {}
    for i, tag in enumerate(a.tags):
        eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s.jsonl" % tag))]
        counts = dict(np.load(os.path.join(a.runs, "counts_%s.npz" % tag)))
        per = defaultdict(list)
        for o in eps:
            per[(o["arm"], o["delay_kf"])].append(o)
        table = {}
        for (arm, d), L in sorted(per.items()):
            ent = [o for o in L if o["entered"]]
            prog = [o["progress"] for o in ent if o["progress"] is not None]
            table["%s|d%d" % (arm, d)] = {"episodes": len(L), "entered": len(ent),
                                         "progress_mean": round(float(np.mean(prog)), 4) if prog else None,
                                         "progress_min": round(float(np.min(prog)), 4) if prog else None,
                                         "infeasible_share": round(sum(o["infeasible_frames"] for o in ent) / max(sum(o["frames"] for o in ent), 1), 4),
                                         "hard_brake_share": round(sum(o["hard_brake_frames"] for o in ent) / max(sum(o["frames"] for o in ent), 1), 4),
                                         "blocked_s_mean": round(float(np.mean([o["blocked_s"] for o in ent])), 2) if ent else None,
                                         "collisions": sum(o["n_collisions"] for o in ent), "at_fault": sum(o["n_at_fault"] for o in ent),
                                         "buffer_intrusions": sum(o["n_front_buffer_intrusions"] for o in ent)}
        res = A.analyse_tracker(eps, counts, log_of_scene, 200, np.random.default_rng([1, i]))
        pop = A.population_mask()
        rec = {}
        for arm in sorted({o["arm"] for o in eps}):
            ids = {o["episode"] for o in eps if o["arm"] == arm}
            m = np.isin(counts["episode"], list(ids)) & pop[counts["cell"]]
            rec[arm] = {"near_relied_records": int(counts["n"][m].sum()), "exceed": int(counts["exceed"][m].sum())}
        out[tag] = {"per_arm_delay": table, "records": rec, "analysis_path": {k: res[k] for k in ("hypotheses", "outcomes", "progress_vs_Mstar")},
                    "inloop_all": {arm: v.get("cells", {}).get("all") for arm, v in res["inloop_all"].items()}}
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    for tag in a.tags:
        print("==", tag)
        for k, v in out[tag]["per_arm_delay"].items():
            print(k, json.dumps(v))
        print(json.dumps(out[tag]["records"]))
        print(json.dumps(out[tag]["inloop_all"]))
    print("K6 DEV CHECK DONE")


if __name__ == "__main__":
    main()
