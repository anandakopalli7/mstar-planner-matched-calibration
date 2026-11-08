#!/usr/bin/env python3
"""X2 pre-freeze steps (Claude line, v01, 30 Oct 2026): sizes for t0 and h2s on the train export, FWER of the 95 % band
(single primary family, alpha 0.05), Q4 operating characteristics. Reuses x1_prefreeze_v02 without modifying it.
No ground-truth residual is computed or written here.
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x1_prefreeze_v02 as PF  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["sizes", "fwer", "oc"])
    ap.add_argument("--export", nargs="+")
    ap.add_argument("--gt")
    ap.add_argument("--meta")
    ap.add_argument("--horizon")
    ap.add_argument("--sizes")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    if a.mode == "sizes":
        res = PF.sizes(a.export, a.gt, a.meta, a.horizon)
    else:
        allsz = json.load(open(a.sizes))
        res = {}
        for fam, sz in allsz["families"].items():
            if a.mode == "fwer":
                r1 = PF.fwer(sz, level=0.95, alpha=0.05)
                fr = {"primary_linear_band": r1}
                if not r1["ok"]:
                    fr["fallback_logit_band"] = PF.fwer(sz, logit=True, level=0.95, alpha=0.05)
                fr["robustness_tau_1.0"] = PF.fwer(sz, tau=1.0, logit=not r1["ok"], level=0.95, alpha=0.05)
                res[fam] = fr
            else:
                res[fam] = PF.oc_q4(sz)
        if a.mode == "fwer":
            res["primary_linear_band"] = {"ok": res["h2s"]["primary_linear_band"]["ok"]}
        else:
            res["targets_met"] = all(res[f].get("targets_met", False) for f in allsz["families"])
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "families"}, default=float)[:2000])


if __name__ == "__main__":
    sys.exit(main())
