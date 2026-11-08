#!/usr/bin/env python3
"""X3 analysis (b): the screen on partitions no method used (x3-core agent, x3_analysis_b_v01, 7 Nov 2026).
X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test). Plan section 2(b).

Inputs: the X3 core runs (x3_run_v01 --parts, fits of record; V0 and V2 passed for them): M*, B0, B1, B3, B4, B6, B9 on T1 and T3,
M* on tab (descriptive). Cells = bin x relied-on axis (long, lat) of one partition, on each population P_rel (PD7_primary: every
near x in-path cell), P_near (SD1_7_gap_le_5m: pair gap <= 5 m) and P_ip (PD_inpath). Estimate per cell: the record's log-level mean
of per-log exceedance shares (k6_analyse_v02.rates); evaluable: >= 39 logs with records (k6_analyse_v02.evaluable: 39 units and
8 logs; units are logs); flag: the one-sided simultaneous sup-t lower bound at 0.95 over the evaluable cells of that partition and
population exceeds delta = 0.05 (k6_analyse_v02.flag, the record's flag rule, zero-SE cells by E > delta). Log-cluster bootstrap
B = 4000, seed [20261201, i, 2] (plan section 0; i = 0 T1, 1 T3, 2 tab).
Outputs per arm, partition and population: the flagged cells; the largest evaluable cell estimate with its simultaneous upper
bound; for M*, every cell whose estimate exceeds delta, with its interval and log count (non-evaluable cells: a marginal one-sided
95 % percentile interval, labelled). P0 (distance to the ego, the range stratum M*'s L0 uses) is reported for completeness.
Usage: python -B x3_analysis_b_v01.py --out-dir <dir>
"""
import argparse
import json
import os
import sys
import time

import numpy as np

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_screen_v01 as SC  # noqa: E402
import x3_run_v01 as RR  # noqa: E402
import x3_common_v01 as C  # noqa: E402
from x3_heavylock_v01 import heavy_lock  # noqa: E402

ARMS = {"t1": ("Mstar", "B0", "B1", "B3", "B4", "B6", "B9"), "t3": ("Mstar", "B0", "B1", "B3", "B4", "B6", "B9"), "tab": ("Mstar",)}
POP_C4 = {"PD7_primary": (0, 1, 2, 3), "SD1_7_gap_le_5m": (2, 3), "PD_inpath": (1, 3)}
POP_LAB = {"PD7_primary": "P_rel (PD7)", "SD1_7_gap_le_5m": "P_near (SD1_7)", "PD_inpath": "P_ip (PD)"}
RUN_DIR = os.path.join(C.OUT, "runs")


def acc_by_key(eps_f, parts, arm, keys):
    kidx = {k: i for i, k in enumerate(keys)}
    ep = {int(o["episode"]): kidx[(o["scene"], o["delay_kf"])] for o in eps_f if o["arm"] == arm}
    acc = np.zeros((len(keys), RR.N_PKEY, 2))
    hit = 0
    for row, e in enumerate(parts["episode"].tolist()):
        if e in ep:
            acc[ep[e]] = parts["acc"][row]
            hit += 1
    assert hit == len(ep) == len(keys), "partition rows missing for %s" % arm
    return acc.reshape(len(keys), 4, RR.NP_, RR.NB_, 2, 2)


def analyse_tracker(t):
    i = C.TRACKER_I[t]
    sb, _ = C.x3_seeds(t, "b")
    tag = "core_%s" % t
    eps = [json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_%s.jsonl" % tag))]
    eps_f = SC.entered(eps)
    parts = dict(np.load(os.path.join(RUN_DIR, "parts_%s.npz" % tag)))
    kw = SC.keys_W(eps_f, C.B_X3, sb)
    out = {"tracker": t, "seed_bootstrap": sb, "B": C.B_X3, "arms": {}, "missing_bin_records": {}, "score_below_0.4_records": {}}
    for arm in ARMS[t]:
        acc6 = acc_by_key(eps_f, parts, arm, kw["keys"])
        ra = {}
        for pi, pn in enumerate(RR.PARTS):
            labels = RR.BIN_LABELS[pn]
            nb = len(labels)
            miss = int(acc6[:, :, pi, RR.MISSING_BIN, :, 0].sum()) if nb <= RR.MISSING_BIN else 0
            out["missing_bin_records"].setdefault(arm, {})[pn] = miss
            if pn == "P4_detection_score":
                out["score_below_0.4_records"][arm] = int(acc6[:, :, pi, 4, :, 0].sum())
            names = ["%s|%s" % (labels[b], ax) for b in range(nb) for ax in ("long", "lat")]
            rp = {}
            for p, c4 in POP_C4.items():
                sub = acc6[:, list(c4), pi, :nb, :, :].sum(1)          # keys x bins x axes x (n, x)
                N = sub[..., 0].reshape(len(kw["keys"]), nb * 2)
                X = sub[..., 1].reshape(len(kw["keys"]), nb * 2)
                r = SC.partition_screen(N, X, kw, names)
                r["above_delta"] = {c: v for c, v in r["cells"].items() if v.get("E") is not None and v["E"] > C.DELTA}
                rp[p] = r
            ra[pn] = rp
        out["arms"][arm] = ra
        print("(b) %s %s done" % (t, arm), flush=True)
    return out


def md(res):
    L = ["# X3 analysis (b): the screen on partitions no method used", "", "**%s**" % C.STAMP, "",
         "Plan section 2(b). Cells = bin x relied-on axis; populations P_rel (PD7), P_near (SD1_7), P_ip (PD); evaluable with >= 39 logs; "
         "flag = one-sided simultaneous sup-t lower bound at 0.95 over the partition's evaluable cells above delta = 0.05; "
         "log bootstrap B = 4000, seed [20261201, i, 2]. Runs: x3_run_v01 core runs (fits of record; V0 and V2 passed). "
         "P0 (distance to the ego) is a partition M*'s strata use, reported for completeness; P1-P7 are used by no method.", ""]
    for t, r in res["by_tracker"].items():
        L += ["## %s%s" % (t.upper(), " (AB3DMOT, descriptive)" if t == "tab" else ""), "",
              "Flagged cells per arm and partition (P_rel / P_near / P_ip); '-' = none flagged; (n) = evaluable cells.", "",
              "| arm | " + " | ".join(p.split("_", 1)[0] for p in RR.PARTS) + " |", "|---|" + "---|" * len(RR.PARTS)]
        for arm, ra in r["arms"].items():
            row = []
            for pn in RR.PARTS:
                cell = []
                for p in POP_C4:
                    q = ra[pn][p]
                    cell.append(("%s (%d)" % (", ".join(q["flagged"]), len(q["evaluable"]))) if q["flagged"] else "- (%d)" % len(q["evaluable"]))
                row.append(" / ".join(cell))
            L.append("| %s | %s |" % (arm, " | ".join(row)))
        L += ["", "Largest evaluable cell estimate with its simultaneous upper bound (P_rel):", "",
              "| arm | " + " | ".join(p.split("_", 1)[0] for p in RR.PARTS) + " |", "|---|" + "---|" * len(RR.PARTS)]
        for arm, ra in r["arms"].items():
            row = []
            for pn in RR.PARTS:
                q = ra[pn]["PD7_primary"].get("largest")
                row.append("%s %.3f (UB %.3f)" % (q["cell"], q["E"], q["ub_sim"]) if q else "n/a")
            L.append("| %s | %s |" % (arm, " | ".join(row)))
        if "Mstar" in r["arms"]:
            L += ["", "M*: every cell with estimate above delta (all partitions and populations):", "",
                  "| partition | population | cell | E | simultaneous LB | simultaneous UB | logs | evaluable | flagged |", "|---|---|---|---|---|---|---|---|---|"]
            for pn in RR.PARTS:
                for p in POP_C4:
                    for c, v in sorted(r["arms"]["Mstar"][pn][p]["above_delta"].items()):
                        if v["evaluable"]:
                            L.append("| %s | %s | %s | %.4f | %.4f | %.4f | %d | yes | %s |" % (pn, POP_LAB[p], c, v["E"], v["lb_sim"], v["ub_sim"], v["logs"], "yes" if v["flagged"] else "no"))
                        else:
                            mi = v.get("marginal_95_one_sided") or [float("nan"), float("nan")]
                            L.append("| %s | %s | %s | %.4f | (marginal %.4f) | (marginal %.4f) | %d | no (< 39 logs) | n/a |" % (pn, POP_LAB[p], c, v["E"], mi[0], mi[1], v["logs"]))
        L.append("")
    L += ["Missing-bin records (non-finite partition value) and detection scores below 0.4 are listed in the JSON "
          "(missing_bin_records, score_below_0.4_records).", ""]
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--trackers", nargs="+", default=["t1", "t3", "tab"])
    a = ap.parse_args(argv)
    t0 = time.time()
    C.assert_run_log("(b) start")
    SC.setup()
    res = {"stamp": C.STAMP, "analysis": "(b) partitions", "plan": C.PLAN, "plan_sha256": C.sha256(C.PLAN), "by_tracker": {},
           "partitions": list(RR.PARTS), "bin_labels": RR.BIN_LABELS,
           "runs": {t: {"run_record_sha256": C.sha256(os.path.join(RUN_DIR, "run_record_core_%s.json" % t)),
                        "parts_sha256": C.sha256(os.path.join(RUN_DIR, "parts_core_%s.npz" % t))} for t in a.trackers}}
    with heavy_lock("x3-core: (b) partition screen B=4000"):
        for t in a.trackers:
            res["by_tracker"][t] = analyse_tracker(t)
            C.live("(b) partition screen", a.trackers.index(t) + 1, len(a.trackers))
    res["seconds"] = round(time.time() - t0, 1)
    C.assert_run_log("(b) end")
    C.jdump(os.path.join(a.out_dir, "x3_b_partitions_v01.json"), res)
    C.wtext(os.path.join(a.out_dir, "x3_b_partitions_v01.md"), md(res))
    print("X3 (b) DONE %.0f s" % res["seconds"])


if __name__ == "__main__":
    main()
