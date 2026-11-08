#!/usr/bin/env python3
"""Per-arm development table for Section V-D (Table VIII) from the K8 run of record (the lead, 6 Nov 2026).
Reads only 70_TESTS/k8_expl_v02_analysis_v03/k8_exploratory_analysis_v03.json (nuScenes development evidence).
Writes <out>.json and <out>.md; refuses existing outputs.
Usage: python -B make_k8_arm_table_v01.py <out_stem>
"""
import hashlib
import json
import os
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
SRC = os.path.join(W, r"70_TESTS\k8_expl_v02_analysis_v03\k8_exploratory_analysis_v03.json")
ARMS = ["Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED", "Z0"]
POPS = [("PD7", "PD7_primary"), ("SD1_7", "SD1_7_gap_le_5m"), ("PD", "PD_inpath")]


def main():
    stem = sys.argv[1]
    for ext in (".json", ".md"):
        assert not os.path.exists(stem + ext), stem + ext
    raw = open(SRC, "rb").read()
    d = json.loads(raw)
    out = {"source": SRC, "source_sha256": hashlib.sha256(raw).hexdigest(), "stamp": d["stamp"], "rows": {}}
    for t in ("t1", "t3"):
        dt = d["decide"][t]
        trade = {r["arm"]: r for r in dt["d14_forms"]["trade_off_table"]}
        rows = []
        for a in ARMS:
            v = dt["validity_by_arm"][a]
            r = {"arm": a, "valid_form_B": v.get("valid_form_B")}
            for short, key in POPS:
                p = v["pops"][key]
                r[short + "_pooled_E"] = p["pooled"]["E"]
                r[short + "_pooled_ub95"] = p["pooled"]["ub"]
                r[short + "_cells_flagged"] = len(p["flagged"])
                r[short + "_cells_evaluable"] = p["evaluable"]
            r["infeasible_rate"] = dt["infeasible_rate"][a]["mean"] if isinstance(dt["infeasible_rate"][a], dict) else dt["infeasible_rate"][a]
            r["infeasible_rate_trade_table"] = trade.get(a, {}).get("infeasible_rate")
            v2 = dt["V2"]["PD7_primary"].get(a)
            r["V2_PD7"] = v2["V2"]["E"] if v2 else None
            r["V2_viol_PD7"] = v2["V2_viol"]["E"] if v2 else None
            ci = dt["calibration_items"]["by_population"]["PD7_primary"].get(a)
            r["mean_margin_lat_m"] = ci["mean_margin_lat"] if ci else None
            r["mean_margin_long_m"] = ci["mean_margin_long"] if ci else None
            rows.append(r)
        out["rows"][t] = rows
    json.dump(out, open(stem + ".json", "w", encoding="utf-8"), indent=1)
    f3 = lambda x: "—" if x is None else ("%.3f" % x)  # noqa: E731
    f2 = lambda x: "—" if x is None else ("%.2f" % x)  # noqa: E731
    lines = ["Source: %s (SHA-256 %s…); %s" % (os.path.relpath(SRC, W), out["source_sha256"][:16], d["stamp"]), ""]
    for t in ("t1", "t3"):
        lines += ["**%s**" % t.upper(), "",
                  "| Arm | Not shown above δ (Valid) | PD7 pooled exc. | SD1_7 pooled | PD pooled | PD7 cells flagged / evaluable | Infeasible | V2 (PD7) | V2_viol (PD7) | Mean margin lat / long (m) |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in out["rows"][t]:
            lines.append("| %s | %s | %s | %s | %s | %d / %d | %s | %s | %s | %s / %s |" % (
                r["arm"].replace("Mstar", "M\*"), {True: "yes", False: "no", None: "—"}[r["valid_form_B"]],
                f3(r["PD7_pooled_E"]), f3(r["SD1_7_pooled_E"]), f3(r["PD_pooled_E"]),
                r["PD7_cells_flagged"], r["PD7_cells_evaluable"], f3(r["infeasible_rate"]), f3(r["V2_PD7"]),
                f3(r["V2_viol_PD7"]), f2(r["mean_margin_lat_m"]), f2(r["mean_margin_long_m"])))
        lines.append("")
    open(stem + ".md", "w", encoding="utf-8", newline="\n").write("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
