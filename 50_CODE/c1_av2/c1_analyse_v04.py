#!/usr/bin/env python3
"""C1 analysis v04 (Claude line, c1_analyse_v04, 4 Nov 2026) = c1_analyse_v03 (kept, imported, unchanged) plus D16 v11 Choice 31:
H8's E0 is the plan's. Before v03's analysis runs, the config's "e0" entry {"plan_values": {cell: E0}, "seed": 20261114, "sigma_a":
0.10, "inputs": {"workers", "gt", "meta", "horizon"}} is RECOMPUTED with c1_e0_v01 (mode c1, the same seed and inputs) and compared
with the plan's values for H8's two decision cells, exactly (bit for bit). v03's decide() is wrapped: a mismatch, a missing "e0"
entry under --c1, or an H8 table whose E0_plan differs from the plan's values makes the decision NO-GO with the reason stated.
Usage: as c1_analyse_v03.
"""
import json
import os
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_analyse_v03 as B3  # noqa: E402
import c1_e0_v01 as E0  # noqa: E402

E0_CHECK = {"done": False}
_decide_v03 = B3.decide


def e0_check(cfg):
    e = cfg.get("e0")
    if not e:
        return {"done": True, "present": False, "match": False, "reason": "no e0 entry in the config"}
    i = e["inputs"]
    assert float(e.get("sigma_a", E0.PRIMARY_SIGMA)) == E0.PRIMARY_SIGMA, "H8 uses sigma_a = 0.10 m"
    rec = E0.compute(i["workers"], i["gt"], i["meta"], i["horizon"], "c1", int(e["seed"]))["H8_E0_primary"]
    plan = {c: e["plan_values"].get(c) for c in E0.DECISION_CELLS}
    match = all(plan[c] is not None and rec[c] == plan[c] for c in E0.DECISION_CELLS)
    return {"done": True, "present": True, "match": bool(match), "recomputed": rec, "plan": plan, "seed": int(e["seed"])}


def decide(results, cfg, mode):
    dec = _decide_v03(results, cfg, mode)
    chk = E0_CHECK if E0_CHECK.get("done") else e0_check(cfg)
    dec["E0_check"] = chk
    bad = None
    if not chk.get("present"):
        if mode == "c1":
            bad = "H8: the plan's E0 is missing from the config (D16 Choice 31)"
    elif not chk["match"]:
        bad = "H8: the recomputed E0 %s differs from the plan's %s (D16 Choice 31)" % (chk.get("recomputed"), chk.get("plan"))
    h8 = cfg.get("_h8")
    if h8 and chk.get("present") and h8.get("E0_plan") is not None:
        if any(h8["E0_plan"].get(c) != chk["plan"][c] for c in E0.DECISION_CELLS):
            bad = (bad + "; " if bad else "") + "H8: its table used E0 values other than the plan's"
    if bad:
        dec["failed_conditions"].append(bad)
        dec["C1_verdict"] = "NO-GO"
    return dec


B3.decide = decide


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser(add_help=False)
    ap.add_argument("--config")
    a, _ = ap.parse_known_args(argv)
    if a.config:
        E0_CHECK.clear()
        E0_CHECK.update(e0_check(json.load(open(a.config))))
        print("E0 check:", json.dumps(E0_CHECK, default=float), flush=True)
    B3.main(argv)
    print("C1 ANALYSIS V04 DONE")


if __name__ == "__main__":
    main()
