#!/usr/bin/env python3
"""Table VIII (Section V-E) from the frozen Trajectron++ analysis (D17 run of record), the lead, 6 Nov 2026.
Reads only 60_RESULTS/tpp_v01/tpp_analysis_v04.json (nuScenes development evidence, primary seed, V2 covariance, P_rel = PD7).
Writes <stem>.md and <stem>.json; refuses existing outputs. Usage: python -B make_tpp_table_v01.py <out_stem>
"""
import hashlib
import json
import os
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
SRC = os.path.join(W, r"60_RESULTS\tpp_v01\tpp_analysis_v04.json")
ARMS = [("TPP_B0", "Trajectron++, raw"), ("TPPgt_B0", "Trajectron++ with ground-truth histories, raw"), ("TPP_Mstar", "Trajectron++ + DP-SCRC"),
        ("TPP_B4", "Trajectron++ + one pooled multiplier (B4)"), ("TPP_B3", "Trajectron++ + certified single multiplier (B3)"),
        ("TRK_B0", "tracker extrapolation, raw"), ("TRK_Mstar", "tracker extrapolation + DP-SCRC")]


def main():
    stem = sys.argv[1]
    for e in (".md", ".json"):
        assert not os.path.exists(stem + e), stem + e
    raw = open(SRC, "rb").read()
    d = json.loads(raw)
    out = {"source": SRC, "source_sha256": hashlib.sha256(raw).hexdigest(), "rows": {}}
    L = ["Source: %s (SHA-256 %s…), primary seed, P_rel (PD7), 2 s." % (os.path.relpath(SRC, W), out["source_sha256"][:16]), "",
         "| Arm | T1 pooled exc. [LB, UB] | T1 flagged / evaluable | T1 mean margin (m) | T3 pooled exc. [LB, UB] | T3 flagged / evaluable | T3 mean margin (m) |",
         "|---|---|---|---|---|---|---|"]
    for key, name in ARMS:
        cells = []
        for t in ("t1", "t3"):
            v = d["trackers"][t]["primary_v2"]["populations"]["PD7"]["validity"][key]
            r = {"E": v["pooled_E"], "lb": v["pooled_lb"], "ub": v["pooled_ub"], "flagged": len(v.get("flagged_cells") or []),
                 "evaluable": v["evaluable_cells"], "margin": v["mean_margin_m"]}
            out["rows"].setdefault(key, {})[t] = r
            cells += ["%.3f [%.3f, %.3f]" % (r["E"], r["lb"], r["ub"]), "%d / %d" % (r["flagged"], r["evaluable"]), "%.2f" % r["margin"]]
        L.append("| %s | %s |" % (name, " | ".join(cells)))
    json.dump(out, open(stem + ".json", "w", encoding="utf-8"), indent=1)
    open(stem + ".md", "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    sys.exit(main())
