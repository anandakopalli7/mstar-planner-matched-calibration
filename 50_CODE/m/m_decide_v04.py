#!/usr/bin/env python3
"""Method-stage decision v04 (Claude line, 31 Oct 2026): plan v05 section 8 applied to the three tracker results
(v03 with the m_lib_v04 key names: fixed_rule_alone and both_inferences; HM6b is the pooled significance check).
T1 = CANMOT (main), T2 = CANMOT with a data-estimated Q (same residual family), T3 = Poly-MOT (different motion models).
  METHOD GO-A: HM1 and HM6 on T1, T2 and T3; the same practitioner baseline (B1, B4 or B9) failing on T1 and on T3 (HM2);
               and the motion-state contrast HM3 on T3 (confirmatory; on T1 it is foreknown and reported only).
  METHOD GO-B: as GO-A without HM3 on T3; "GO-B (HM3 untestable)" if T3 has no car-turning cell.
  NO-GO:       anything else.
Changes from v02 (R07b): the same baseline is required on T1 and T3 (N-m1); HM3 is confirmatory on T3 only (N-M1);
HM3 testability is recorded (N-m2); the inputs are verified: the plan hash equals the frozen sidecar, no result comes from
test mode, and each result carries its own tracker label (N-m8).
Usage: python m_decide_v04.py --prereg <plan .md> --t1 <json> --t2 <json> --t3 <json> --out <json> [--test-mode]
"""
import argparse
import json
import sys


def main():
    ap = argparse.ArgumentParser()
    for k in ("prereg", "t1", "t2", "t3", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--test-mode", action="store_true")
    a = ap.parse_args()
    R = {"T1": json.load(open(a.t1)), "T2": json.load(open(a.t2)), "T3": json.load(open(a.t3))}
    shas = {r["prereg_sha256"] for r in R.values()}
    assert len(shas) == 1, "results come from different plans"
    sha = shas.pop()
    if a.test_mode:
        assert sha == "TEST MODE"
    else:
        side = open(a.prereg.replace(".md", ".sha256")).read().split()[0]
        assert sha == side, "results do not come from the frozen plan"
        assert all(R[t]["tracker"] == t for t in R), "a result file carries another tracker label"
        assert all(R[t].get("completed_through") == "all" for t in R), "a run did not complete"
    h1 = {t: r["E1_h2s"]["hypotheses"] for t, r in R.items()}
    h2 = {t: r["E2_h2s"]["hypotheses"] for t, r in R.items()}
    core = ("T1", "T3")
    d = {"prereg_sha256": sha, "per_tracker": {t: {"HM1": h1[t]["HM1"], "HM6": h2[t]["HM6"], "HM6a": h2[t]["HM6a"], "HM6b": h2[t]["HM6b"],
                                                    "HM2": h1[t]["HM2"], "HM2b": h1[t]["HM2b"], "HM3_testable": h1[t]["HM3_testable"],
                                                    "HM3_cells": h1[t]["HM3"], "fixed_rule_alone": h1[t]["fixed_rule_alone"],
                                                    "both_inferences": h1[t]["both_inferences"],
                                                    "pooled_val": {k: h2[t][k] for k in ("pooled_E", "pooled_lb", "pooled_ub_bias_corrected",
                                                                                         "pooled_equivalence_at_eps")}} for t in R}}
    valid_all = all(h1[t]["HM1"] and h2[t]["HM6"] for t in R)
    common = [b for b in h1["T1"]["HM2"] if all(bool(h1[t]["HM2"][b]) for t in core)]
    need_core = bool(common)
    if valid_all and need_core and h1["T3"]["HM3_holds"]:
        lab = "GO-A"
    elif valid_all and need_core:
        lab = "GO-B" if h1["T3"]["HM3_testable"] else "GO-B (HM3 untestable)"
    else:
        lab = "NO-GO"
    d["METHOD_DECISION"] = lab
    d["claims"] = {"K5_validity_consistency_and_transfer": valid_all,
                   "K5a_practitioner_on_T1_and_T3": common,
                   "K5a_ablations_on_T1_and_T3": [b for b in h1["T1"]["HM2b"] if all(bool(h1[t]["HM2b"][b]) for t in core)],
                   "K5b_motion_state_confirmatory_T3": h1["T3"]["HM3_holds"],
                   "K5b_T1_foreknown_reported": h1["T1"]["HM3_holds"], "K5b_T2_reported": h1["T2"]["HM3_holds"]}
    d["MLS_recommended"] = bool(all(h1[t]["MLS_consistent"] and h2[t]["MLS_HM6"] for t in R)
                                and all(R[t]["E1_h2s"]["fixed"]["ratios"]["MLS/Mstar"]["ci"][1] < 1 for t in core))
    d["efficiency_descriptive"] = {t: {k: R[t]["E1_h2s"]["fixed"]["ratios"][k] for k in ("Mstar/B3", "Mstar/B6c", "Mstar/B9", "MLS/Mstar")}
                                   for t in R}
    d["if_HM1_failed_Mstar_log_consistent"] = {t: h1[t]["Mstar_log_consistent"] for t in R if not h1[t]["HM1"]}
    json.dump(d, open(a.out, "w"), indent=1)
    print(json.dumps(d, indent=1))


if __name__ == "__main__":
    sys.exit(main())
