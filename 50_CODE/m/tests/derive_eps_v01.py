#!/usr/bin/env python3
"""Derive the HM6b pooled tolerance eps (plan v05 section 9; Claude line, v01, 31 Oct 2026). The rule, fixed before T3's OC
result was seen: eps = the smallest candidate in {0.02, 0.025, 0.03, 0.035, 0.04} whose null HM6 failure rate at rho = 0.5
is at most 0.10 on T1 and on T3. Feasibility is monotone in eps, so this is the larger of the two per-layout minima.
Then each layout is re-merged with that eps (merge_oc_v03.py --eps), giving the final OC files.
Usage: python derive_eps_v01.py --dir <shard folder> --scratch <70_TESTS/m_scratch>
"""
import argparse
import json
import os
import subprocess
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--scratch", required=True)
    a = ap.parse_args()
    here = os.path.dirname(os.path.abspath(__file__))
    mins = {}
    for t in ("T1", "T3"):
        out = os.path.join(a.scratch, "oc_v03_%s_preliminary.json" % t)
        subprocess.check_call([sys.executable, "-B", os.path.join(here, "merge_oc_v03.py"), "--dir", a.dir, "--tracker", t, "--out", out])
        mins[t] = json.load(open(out))["eps_feasible_min"]
    assert all(v is not None for v in mins.values()), "no candidate eps meets A2 on some layout: %s" % mins
    eps = max(mins.values())
    for t in ("T1", "T3"):
        subprocess.check_call([sys.executable, "-B", os.path.join(here, "merge_oc_v03.py"), "--dir", a.dir, "--tracker", t, "--eps", str(eps),
                               "--out", os.path.join(a.scratch, "oc_v03_%s.json" % t)])
    res = {"rule": "smallest eps in {0.02, 0.025, 0.03, 0.035, 0.04} with null HM6 failure <= 0.10 at rho 0.5 on T1 and T3",
           "per_layout_minimum": mins, "eps": eps}
    json.dump(res, open(os.path.join(a.scratch, "eps_v01.json"), "w"), indent=1)
    print(json.dumps(res))


if __name__ == "__main__":
    sys.exit(main())
