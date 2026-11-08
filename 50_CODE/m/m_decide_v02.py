#!/usr/bin/env python3
"""Method-stage decision v02 (Claude line, 31 Oct 2026): plan v03 section 8 applied to the three tracker results.
T1 = CANMOT (main), T2 = CANMOT with a sample-covariance Q (same residual family), T3 = Poly-MOT (different motion models).
  METHOD GO-A: on T1 and T3, HM1 (E1, 2 s), HM6 (E2, 2 s), at least one practitioner baseline failing (HM2) and the
               motion-state contrast (HM3); on T2, HM1 and HM6.
  METHOD GO-B: as GO-A without HM3 (motion state not shown to matter on T1 or T3).
  NO-GO:       anything else.
Claims need T1 and T3; T2 is reported beside them. Efficiency ratios are descriptive.
Usage: python m_decide_v02.py --t1 <json> --t2 <json> --t3 <json> --out <json>
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    for k in ("t1", "t2", "t3", "out"):
        ap.add_argument("--" + k, required=True)
    a = ap.parse_args()
    R = {"T1": json.load(open(a.t1)), "T2": json.load(open(a.t2)), "T3": json.load(open(a.t3))}
    shas = {r["prereg_sha256"] for r in R.values()}
    assert len(shas) == 1, "results come from different plans"
    h1 = {t: r["E1_h2s"]["hypotheses"] for t, r in R.items()}
    h2 = {t: r["E2_h2s"]["hypotheses"] for t, r in R.items()}
    core = ("T1", "T3")
    d = {"prereg_sha256": shas.pop(), "per_tracker": {t: {"HM1": h1[t]["HM1"], "HM6": h2[t]["HM6"], "HM2_any": h1[t]["HM2_any"],
                                                            "HM3": h1[t]["HM3_holds"], "HM2": h1[t]["HM2"], "HM2b": h1[t]["HM2b"],
                                                            "HM3_cells": h1[t]["HM3"]} for t in R}}
    valid_all = all(h1[t]["HM1"] and h2[t]["HM6"] for t in R)
    need_core = all(h1[t]["HM2_any"] for t in core)
    motion_core = all(h1[t]["HM3_holds"] for t in core)
    d["METHOD_DECISION"] = "GO-A" if (valid_all and need_core and motion_core) else ("GO-B" if (valid_all and need_core) else "NO-GO")
    d["claims"] = {"K5_validity_consistency_and_transfer": valid_all,
                   "K5a_practitioner": {b: all(bool(h1[t]["HM2"][b]) for t in core) for b in h1["T1"]["HM2"]},
                   "K5a_ablations": {b: all(bool(h1[t]["HM2b"][b]) for t in core) for b in h1["T1"]["HM2b"]},
                   "K5b_motion_state": motion_core, "K5b_on_T2": h1["T2"]["HM3_holds"]}
    d["MLS_recommended"] = bool(all(h1[t]["MLS_consistent"] and h2[t]["MLS_HM6"] for t in R)
                                and all(R[t]["E1_h2s"]["fixed"]["ratios"]["MLS/Mstar"]["ci"][1] < 1 for t in core))
    d["efficiency_descriptive"] = {t: {k: R[t]["E1_h2s"]["fixed"]["ratios"][k] for k in ("Mstar/B3", "Mstar/B6c", "Mstar/B9", "MLS/Mstar")}
                                   for t in R}
    d["if_HM1_failed_Mstar_log_consistent"] = {t: h1[t]["Mstar_log_consistent"] for t in R if not h1[t]["HM1"]}
    json.dump(d, open(a.out, "w"), indent=1)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    sys.exit(main())
