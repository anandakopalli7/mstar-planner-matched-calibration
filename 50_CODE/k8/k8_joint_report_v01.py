#!/usr/bin/env python3
"""Tables of the joint arm M*J (Claude line, k8_joint_report_v01, 2 Nov 2026) from a k8_analyse_v04 decision-mode JSON and the
joint fits: the fitted lambdas per fold, M* vs M*J (and M*Jx) per tracker (per-constraint V1 and its Form B validity, the joint
V2 with its CRC target and the joint validity rule, V2_viol, V2_near, V2_binding, the infeasible rate, the price over M*), and
Form B on the joint loss. Reads only; writes a markdown file and a summary JSON.
Usage: python -B k8_joint_report_v01.py --analysis <json> --fits <t1 joint fits> <t3 joint fits> --out-md <md> --out-json <json>
"""
import argparse
import hashlib
import json
import os

POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")
LAB = {"PD7_primary": "PD7", "SD1_7_gap_le_5m": "SD1_7", "PD_inpath": "PD"}
ROWS = ("Mstar", "MstarJ", "MstarJx", "B4", "B0", "B1", "B3", "B6", "B9")
NAME = {"Mstar": "M*", "MstarJ": "M*J", "MstarJx": "M*Jx"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def f3(x):
    return "n/a" if x is None else "%.3f" % x


def ci(c):
    return "" if not c else " [%.3f, %.3f]" % (c[0], c[1])


def fit_rows(jf, tag):
    out = []
    for f, r in sorted(jf["joint"]["fit"]["folds"].items()):
        for arm in ("MstarJ", "MstarJx"):
            a = r[arm]
            bp = a["by_population"]
            oof = a.get("items_oof") or {}
            out.append({"tracker": tag, "fold": int(f), "arm": arm, "lambda": a["lambda"], "binding": ",".join(a["binding_populations"]),
                        "none_qualifies": a["none_qualifies_grid_max_used"],
                        "cal_scenes_PD7": bp["PD7_primary"]["n_scenes"], "cal_decisions_PD7": bp["PD7_primary"]["n_decisions"],
                        "lam_PD7": bp["PD7_primary"]["lam"], "lam_SD1_7": bp["SD1_7_gap_le_5m"]["lam"], "lam_PD": bp["PD_inpath"]["lam"],
                        "bound_at_lambda_PD7": bp["PD7_primary"].get("bound"), "loss_at_1_PD7": bp["PD7_primary"].get("loss_at_1"),
                        "items_oof_PD7_at_lambda": (oof.get("PD7_primary") or {}).get("E_at_lam"),
                        "items_oof_SD1_7_at_lambda": (oof.get("SD1_7_gap_le_5m") or {}).get("E_at_lam"),
                        "items_oof_PD_at_lambda": (oof.get("PD_inpath") or {}).get("E_at_lam"),
                        "items_oof_PD7_at_1": (oof.get("PD7_primary") or {}).get("E_at_1")})
    return out


def arm_row(r, a):
    v = r["validity_by_arm"][a]
    jl = r["joint_loss"]["validity_by_arm"][a]
    row = {"arm": a, "per_constraint_valid_form_B": v["valid_form_B"], "HK1": v["HK1"], "HK1c_all_pops": v["HK1c_all_pops"],
           "joint_valid": jl["valid"], "infeasible_rate": r["infeasible_rate"][a]["mean"], "infeasible_ci95": r["infeasible_rate"][a]["ci95"]}
    for p in POPS:
        pb = r["populations"][p]["pooled_by_arm"].get(a) or {}
        row["V1_%s" % LAB[p]] = pb.get("E")
        row["V1_%s_ub" % LAB[p]] = pb.get("ub_sim")
        jp = jl["pops"][p]
        row["V2_%s" % LAB[p]] = jp.get("E")
        row["V2_%s_ci95" % LAB[p]] = jp.get("ci95")
        row["V2_%s_ub" % LAB[p]] = jp.get("ub_one_sided_0.95")
        row["V2_%s_lb" % LAB[p]] = jp.get("lb_one_sided_0.95")
        row["V2_%s_flagged" % LAB[p]] = jp.get("flagged")
        row["V2_%s_valid" % LAB[p]] = jp.get("valid")
    v2 = r["V2"]["PD7_primary"][a]
    row["V2_PD7_reference"] = v2["V2"].get("reference_E")
    row["V2_PD7_tracks_per_decision"] = v2["V2"].get("mean_tracks_per_decision")
    for var in ("V2_viol", "V2_near", "V2_binding", "V2_exec", "V2_one_step"):
        row["%s_PD7" % var] = v2[var].get("E")
        row["%s_PD7_ci95" % var] = v2[var].get("ci95")
    row["V2_near_PD7_reference"] = v2["V2_near"].get("reference_E")
    e = r["endpoints_by_arm"][a]
    for k in ("progress_ratio", "mean_chosen_speed", "estop_share", "mean_backoff_level"):
        row[k] = (e.get(k) or {}).get("mean")
    pv = r["paired_vs_Mstar"]
    if a != "Mstar":
        for ep in ("infeasible_rate", "V2_PD7_scene_rate", "V2_viol_PD7_scene_rate", "V1_PD7_scene_rate", "progress_ratio"):
            d = (pv.get(ep) or {}).get(a)
            if d:
                row["arm_minus_Mstar_%s" % ep] = None if d["mean_diff_Mstar_minus_arm"] is None else -d["mean_diff_Mstar_minus_arm"]
                row["arm_minus_Mstar_%s_ci95" % ep] = None if not d["ci95"] else sorted([-d["ci95"][0], -d["ci95"][1]])
    return row


def md_tables(summary):
    L = []
    for tag, s in summary["trackers"].items():
        L.append("\n### %s (%s): M* vs M*J, decision mode, %d scenes, %d logs\n" % (tag.upper(), s["stamp"], s["scenes"], s["logs"]))
        L.append("| Arm | V1 PD7 | V1 SD1_7 | V1 PD | per-constraint Form B valid | V2_joint PD7 [95 % CI] (ub) | V2_joint SD1_7 (ub) | V2_joint PD (ub) | "
                 "joint valid | V2 reference | V2_viol PD7 | V2_near PD7 | V2_binding PD7 | infeasible rate | price vs M* [95 % CI] |")
        L.append("|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|")
        for r in s["arms"]:
            price = ""
            if r["arm"] != "Mstar" and r.get("arm_minus_Mstar_infeasible_rate") is not None:
                price = "%+.3f%s" % (r["arm_minus_Mstar_infeasible_rate"], ci(r.get("arm_minus_Mstar_infeasible_rate_ci95")))
            L.append("| %s | %s | %s | %s | %s | %s%s (%s) | %s (%s) | %s (%s) | %s | %s | %s | %s | %s | %s | %s |" % (
                NAME.get(r["arm"], r["arm"]), f3(r["V1_PD7"]), f3(r["V1_SD1_7"]), f3(r["V1_PD"]), "yes" if r["per_constraint_valid_form_B"] else "no",
                f3(r["V2_PD7"]), ci(r["V2_PD7_ci95"]), f3(r["V2_PD7_ub"]), f3(r["V2_SD1_7"]), f3(r["V2_SD1_7_ub"]), f3(r["V2_PD"]), f3(r["V2_PD_ub"]),
                "yes" if r["joint_valid"] else "no", f3(r["V2_PD7_reference"]), f3(r["V2_viol_PD7"]), f3(r["V2_near_PD7"]),
                f3(r["V2_binding_PD7"]), f3(r["infeasible_rate"]), price or "-"))
        L.append("\nForm B on the joint loss (CRC target delta = %.2f; joint validity: not flagged and one-sided upper bound <= delta + 0.03 on "
                 "PD7, SD1_7 and PD):\n" % summary["delta"])
        for m, fb in s["form_B_joint"].items():
            L.append("- **%s**: validity %s; comparators valid on the joint loss: %s; invalid: %s; less infeasible than every valid comparator: %s; "
                     "**Form B (joint) met: %s**%s" % (NAME.get(m, m), "PASS" if fb["validity_method"] else "FAIL",
                                                       ", ".join(fb["comparators_valid_on_joint_loss"]) or "none",
                                                       ", ".join(fb["comparators_invalid_on_joint_loss"]) or "none",
                                                       json.dumps({b: v["lower"] for b, v in fb["lower_than_every_valid_comparator"].items()}) or "{}",
                                                       "YES" if fb["met"] else "NO",
                                                       (" (missing comparators: %s)" % ", ".join(fb["missing_comparators"])) if fb["missing_comparators"] else ""))
        L.append("\nFitted lambda per fold (M*J: M*'s base, M*'s calibration scenes; M*Jx: 3-fold base, fold g = f + 1 for lambda):\n")
        L.append("| Arm | fold | lambda | binding population | cal. scenes (PD7) | cal. decisions (PD7) | lambda PD7 / SD1_7 / PD | CRC bound at lambda (PD7) | "
                 "items: joint loss at 1 (PD7, held-out fold) | items: joint loss at lambda, held-out fold (PD7 / SD1_7 / PD) |")
        L.append("|---|---|---|---|---|---|---|---|---|---|")
        for r in s["fit"]:
            L.append("| %s | %d | %.2f | %s | %d | %d | %s / %s / %s | %s | %s | %s / %s / %s |" % (
                NAME[r["arm"]], r["fold"], r["lambda"], r["binding"], r["cal_scenes_PD7"], r["cal_decisions_PD7"], r["lam_PD7"], r["lam_SD1_7"],
                r["lam_PD"], f3(r["bound_at_lambda_PD7"]), f3(r["items_oof_PD7_at_1"]), f3(r["items_oof_PD7_at_lambda"]),
                f3(r["items_oof_SD1_7_at_lambda"]), f3(r["items_oof_PD_at_lambda"])))
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True)
    ap.add_argument("--fits", nargs=2, required=True)
    ap.add_argument("--tags", nargs=2, default=["t1", "t3"])
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-json", required=True)
    a = ap.parse_args()
    an = json.load(open(a.analysis))
    summary = {"analysis": os.path.abspath(a.analysis), "analysis_sha256": sha(a.analysis), "stamp": an["stamp"], "delta": an["delta"],
               "fits": {t: {"path": os.path.abspath(p), "sha256": sha(p)} for t, p in zip(a.tags, a.fits)}, "trackers": {}}
    for t, fp in zip(a.tags, a.fits):
        r = an["decide"][t]
        jf = json.load(open(fp))
        arms = [x for x in ROWS if x in r["arms"]]
        summary["trackers"][t] = {"stamp": r["stamp"], "scenes": r["scenes"], "logs": r["logs"], "arms": [arm_row(r, x) for x in arms],
                                  "form_B_joint": r["joint_loss"]["form_B_joint"], "price_vs_Mstar": r["joint_loss"]["price_vs_Mstar"],
                                  "lambda_by_fold": r["joint_loss"]["lambda_by_fold"], "fit": fit_rows(jf, t),
                                  "per_constraint_form_B": {k: r["d14_forms"]["B_literature_form"].get(k) for k in
                                                            ("comparators_passing_validity", "validity_M", "met", "vacuous")}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out_json)), exist_ok=True)
    with open(a.out_json, "w") as f:
        json.dump(summary, f, indent=1, default=float)
    with open(a.out_md, "w", encoding="utf-8") as f:
        f.write("<!-- generated by k8_joint_report_v01.py from %s (sha256 %s) -->\n" % (os.path.basename(a.analysis), summary["analysis_sha256"]))
        f.write(md_tables(summary))
    print("K8 JOINT REPORT DONE", a.out_md)


if __name__ == "__main__":
    main()
