#!/usr/bin/env python3
"""K6 development check v02 (Claude line, 1 Nov 2026): summarises a --dev run of k6_run_v02 on the 10 nuScenes-mini scenes
(excluded from K6) per arm, and exercises the v02 analysis path with the support rule relaxed (2 scenes, 1 log). Also
writes the per-cell ratio of M*'s primary in-loop records to the open-loop calibration items of the same scenes, which
the OC v02 layout uses. Harness diagnostics, not K6 evidence.
Usage: python -B k6_dev_check_v02.py --runs <dir> --tags <t1> <t3> --items <k6_items dir> --manifests <...> --out <json>
"""
import argparse
import json
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "m"))
import k6_analyse_v02 as A  # noqa: E402
import k6_sim_v02 as S  # noqa: E402
import m_lib_v04 as M  # noqa: E402

STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]


def open_loop_items(items_dir, tag_pair, scenes):
    """Open-loop calibration items per scene and cell (summed over the 8 steps) for the given scenes."""
    cells = A.cell_family()
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    out = {s: np.zeros(len(cells)) for s in scenes}
    for tag in tag_pair:
        names = json.load(open(os.path.join(items_dir, "items_%s_summary.json" % tag)))["scene_names"]
        for h in STEPS:
            z = np.load(os.path.join(items_dir, "items_%s_%s.npz" % (tag, h)))
            it = {k: z["item_" + k] for k in ("g", "r", "a", "spd", "omc", "chord")}
            m = M.motion_state(it)
            l0 = ((it["g"] * 3 + it["r"]) * 2 + it["a"]) * 4 + m
            for si, c in zip(z["item_s"], l0_to_cell[l0]):
                nm = names[si]
                if nm in out:
                    out[nm][c] += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tags", nargs=2, required=True)
    ap.add_argument("--items", required=True)
    ap.add_argument("--manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    A.DEV_SCENES, A.MIN_SCENES, A.MIN_LOGS = (), 2, 1
    log_of_scene = {}
    for p in a.manifests:
        for s, info in json.load(open(p))["scenes"].items():
            log_of_scene[s] = info["log"]
    cells = A.cell_family()
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, idl) in enumerate(cells):
        l0_to_cell[idl] = j
    out = {}
    for i, tag in enumerate(a.tags):
        out[tag] = {}
        for mode in ("decide", "loop"):
            eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s_%s.jsonl" % (tag, mode)))]
            counts = dict(np.load(os.path.join(a.runs, "counts_%s_%s.npz" % (tag, mode))))
            per = defaultdict(lambda: defaultdict(float))
            for o in eps:
                if not o["entered"] or o["arm"] == "LOG":
                    continue
                x = per[o["arm"]]
                x["n"] += 1
                x["frames"] += o["frames"]
                x["inf"] += o["infeasible_frames"]
                if mode == "loop":
                    if o["progress"] is not None:
                        x["prog"] += o["progress"]
                        x["np"] += 1
                    x["hard"] += o["hard_brake_frames"]
                    x["blocked"] += o["blocked_s"]
                    x["off_med"] += o["sensor_offset_median"] or 0.0
                    x["off_gt15"] += o["sensor_offset_share_gt15"] or 0.0
                    for c in o["collisions"]:
                        x["af_tr" if (c["at_fault"] and c["tracked"]) else ("af_un" if c["at_fault"] else "nf")] += 1
            table = {}
            for arm, x in per.items():
                row = {"episodes": int(x["n"]), "infeasible_share": round(x["inf"] / max(x["frames"], 1), 4)}
                if mode == "loop":
                    row.update({"progress_mean": round(x["prog"] / max(x["np"], 1), 4), "hard_brake_share": round(x["hard"] / x["frames"], 4),
                                "blocked_s_mean": round(x["blocked"] / x["n"], 2), "sensor_offset_median_mean": round(x["off_med"] / x["n"], 1),
                                "share_frames_offset_gt15": round(x["off_gt15"] / x["n"], 3), "at_fault_tracked": int(x["af_tr"]),
                                "at_fault_untracked": int(x["af_un"]), "not_at_fault": int(x["nf"])})
                table[arm] = row
            if mode == "decide":
                res = A.analyse_decide(eps, counts, log_of_scene, 200, np.random.default_rng([1, i]), np.random.default_rng([2, i]))
                dev = sorted({o["scene"] for o in eps})
                ol = open_loop_items(a.items, ["%s_train" % tag, "%s_val" % tag], set(dev))
                pop = A.mask(**A.POP_DECIDE["PD_primary"])
                ids = {o["episode"] for o in eps if o["arm"] == "Mstar" and o["entered"]}
                sel = np.isin(counts["episode"], list(ids)) & pop[counts["cell"]]
                rec = np.zeros(len(cells))
                np.add.at(rec, l0_to_cell[counts["cell"][sel] % S.N_L0], counts["n"][sel])
                olt = np.sum([ol[s] for s in dev], axis=0)
                ratio = {cells[j][0]: {"inloop_records_per_episode": float(rec[j] / len(ids)), "open_loop_items_per_scene": float(olt[j] / len(dev)),
                                       "ratio": float(rec[j] / len(ids) / (olt[j] / len(dev))) if olt[j] > 0 else None} for j in range(len(cells))}
                # per-scene infeasible rates (HK3 effect sizes)
                inf = defaultdict(dict)
                for o in eps:
                    if o["arm"] != "LOG":
                        inf[o["arm"]][o["scene"]] = o["infeasible_frames"] / max(o["frames"], 1)
                d = {b: [inf["Mstar"][s_] - inf[b][s_] for s_ in dev] for b in inf if b != "Mstar"}
                out[tag][mode] = {"per_arm": table, "layout_ratio_Mstar": ratio, "dev_scenes": dev,
                                  "PD_pooled_by_arm": res["populations"]["PD_primary"]["pooled_by_arm"], "HK3": res["HK3"],
                                  "HK3_scene_diff_mean_sd": {b: [float(np.mean(v)), float(np.std(v, ddof=1))] for b, v in d.items()},
                                  "hypotheses_relaxed_support": res["hypotheses"]}
            else:
                res = A.analyse_loop(eps, counts, log_of_scene, 200, np.random.default_rng([3, i]))
                out[tag][mode] = {"per_arm": table, "progress_vs_Mstar": res["progress_vs_Mstar"],
                                  "PL_pooled_by_arm": res["populations"]["PL_offset_le_15m"]["pooled_by_arm"]}
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    for tag in a.tags:
        for mode in ("decide", "loop"):
            print("==", tag, mode)
            for arm in S.ARMS:
                if arm in out[tag][mode]["per_arm"]:
                    print(arm, json.dumps(out[tag][mode]["per_arm"][arm]))
            key = "PD_pooled_by_arm" if mode == "decide" else "PL_pooled_by_arm"
            print("pooled in-loop:", {k: (None if v is None else (round(v["E"], 4), v["records"])) for k, v in out[tag][mode][key].items()})
    print("K6 DEV CHECK V02 DONE")


if __name__ == "__main__":
    main()
