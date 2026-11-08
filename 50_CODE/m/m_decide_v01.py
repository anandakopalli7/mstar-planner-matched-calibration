#!/usr/bin/env python3
"""Method-stage decision v01 (Claude line, 31 Oct 2026): applies plan section 7 to the two tracker results.
Method GO = HM1 in E1 (2 s) on T1 and T2, HM6 (E2 at 2 s) on T1 and T2, at least two of B0/B1/B4 significantly
under-covering on both trackers, and the 95 % CI of M*/B3 mean margin below 1 on both. Claims K5a-K5c need both trackers.
Usage: python m_decide_v01.py --t1 <result T1> --t2 <result T2> --out <decision json>
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--t1", required=True)
    ap.add_argument("--t2", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    R = {"T1": json.load(open(a.t1)), "T2": json.load(open(a.t2))}
    assert R["T1"]["prereg_sha256"] == R["T2"]["prereg_sha256"], "results come from different plans"
    e1 = {t: r["E1_h2s"] for t, r in R.items()}
    e2 = {t: r["E2_h2s"] for t, r in R.items()}
    both = lambda f: all(f(t) for t in R)
    d = {"prereg_sha256": R["T1"]["prereg_sha256"]}
    d["HM1_both"] = both(lambda t: e1[t]["hypotheses"]["HM1"])
    d["HM6_both"] = both(lambda t: e2[t]["hypotheses"]["HM1"])
    d["HM2_each_both"] = {b: both(lambda t: e1[t]["hypotheses"]["HM2"][b]) for b in ("B0", "B1", "B4")}
    d["HM2_ok"] = sum(d["HM2_each_both"].values()) >= 2
    d["ratio_Mstar_B3"] = {t: e1[t]["ratios"]["Mstar/B3"] for t in R}
    d["efficiency_ok"] = both(lambda t: e1[t]["ratios"]["Mstar/B3"]["ci"][1] < 1)
    d["METHOD_GO"] = bool(d["HM1_both"] and d["HM6_both"] and d["HM2_ok"] and d["efficiency_ok"])
    d["claims"] = {"K5": d["HM1_both"], "K5a": d["HM2_each_both"],
                   "K5a_B5": both(lambda t: e1[t]["hypotheses"]["HM2b"]),
                   "K5b": both(lambda t: e1[t]["hypotheses"]["HM3"]),
                   "K5c": both(lambda t: e1[t]["hypotheses"]["HM3b"]),
                   "K5a_B8": both(lambda t: e1[t]["hypotheses"]["HM2c"]),
                   "K5d": d["HM6_both"]}
    d["MLS_recommended"] = both(lambda t: e1[t]["hypotheses"]["MLS_HM1"] and e2[t]["hypotheses"]["MLS_HM1"]
                                and e1[t]["ratios"]["MLS/Mstar"]["ci"][1] < 1)
    d["HM1_fail_remedy_Mstar_log"] = None if d["HM1_both"] else both(lambda t: e1[t]["hypotheses"]["Mstar_log_HM1"])
    json.dump(d, open(a.out, "w"), indent=1)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    sys.exit(main())
