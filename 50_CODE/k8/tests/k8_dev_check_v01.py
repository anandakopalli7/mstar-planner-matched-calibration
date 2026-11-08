#!/usr/bin/env python3
"""K8 development check (Claude line, v01, 1 Nov 2026). Development scenes only: exactly the selection of k7_dev_check_v01, i.e.
k8_run_v01 --dev with both caches of each tracker, which keeps the 10 nuScenes-mini scenes of k8_run_v01.DEV_SCENES (= K6's
DEV_SCENES; excluded from every confirmatory analysis) and asserts that all 10 are present. Runs both modes for both trackers
with the K7 fits (k7_fits_<t>_v01.json), then k8_analyse_v01 --allow-dev (B = 2000; evaluability relaxed to >= 2 scenes from >= 1
log as in K7's development analysis) with the development items files (A8) and the fits (A13), and writes a headline summary.
Diagnostics, not evidence. Nothing is run on a confirmatory scene.
Usage: python -B k8_dev_check_v01.py --out <json> --runs <scratch dir> [--csv-dir <dir>] [--workers n] [--boot B] [--skip-runs]
"""
import argparse
import json
import os
import subprocess
import sys

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(K8))


def run(cmd):
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stdout[-4000:] + "\n" + p.stderr[-8000:] + "\n")
        raise SystemExit("command failed: " + " ".join(cmd[:4]))
    return p.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--csv-dir", default=None)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--skip-runs", action="store_true", help="reuse the run outputs already in --runs")
    a = ap.parse_args()
    py = sys.executable
    os.makedirs(a.runs, exist_ok=True)
    csv_dir = a.csv_dir or os.path.join(a.runs, "csv")
    if not a.skip_runs:
        for t in ("t1", "t3"):
            for mode in ("decide", "loop"):
                caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, sp)) for sp in ("train", "val")]
                run([py, "-B", os.path.join(K8, "k8_run_v01.py"), "--caches", *caches, "--fits",
                     os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t), "--tag", "%s_%s" % (t, mode),
                     "--mode", mode, "--out", a.runs, "--dev", "--workers", str(a.workers)])
                print("run %s_%s done" % (t, mode), flush=True)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % sp, "MANIFEST.json") for sp in ("train", "val")]
    items = [os.path.join(W, "70_TESTS", "k7_scratch", "items_v02_dev_%s.npz" % t) for t in ("t1", "t3")]
    fits = [os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t) for t in ("t1", "t3")]
    res_path = os.path.join(a.runs, "k8_dev_analysis_v01.json")
    cmd = [py, "-B", os.path.join(K8, "k8_analyse_v01.py"), "--runs", a.runs, "--tags", "t1", "t3", "--manifests", *man, "--out", res_path,
           "--csv-dir", csv_dir, "--allow-dev", "--boot", str(a.boot), "--fits", *fits]
    if all(os.path.exists(p) for p in items):
        cmd += ["--items", *items]
    run(cmd)
    r = json.load(open(res_path))
    out = {"note": "development scenes only (the 10 nuScenes-mini scenes); diagnostics, not evidence; nothing gated", "design": r["design"],
           "boot": r["boot"], "analysis_json": os.path.abspath(res_path), "csv_dir": os.path.abspath(csv_dir), "decide": {}, "loop": {}}
    for t in ("t1", "t3"):
        d = r["decide"][t]
        arms = d["arms"]
        pooled = lambda p: {k: (v or {}).get("E") for k, v in d["populations"][p]["pooled_by_arm"].items()}  # noqa: E731
        out["decide"][t] = {
            "scenes": d["scenes"], "logs": d["logs"],
            "infeasible_rate": {k: v["mean"] for k, v in d["infeasible_rate"].items()},
            "pooled_PD7": pooled("PD7_primary"), "pooled_SD1_7": pooled("SD1_7_gap_le_5m"), "pooled_PD": pooled("PD_inpath"), "pooled_NIP": pooled("NIP_not_in_path"),
            "pooled_PD7_one_step": {k: (v or {}).get("E") for k, v in d["V1_one_step"]["PD7_primary"].items()},
            "V2_PD7": {k: v["E"] for k, v in d["V2"]["PD7_primary"].items()},
            "V2_PD7_one_step": {k: v["E"] for k, v in d["V2_one_step"]["PD7_primary"].items()},
            "V2_SD1_7": {k: v["E"] for k, v in d["V2"]["SD1_7_gap_le_5m"].items()},
            "progress_ratio": {k: v["progress_ratio"]["mean"] for k, v in d["endpoints_by_arm"].items()},
            "mean_chosen_speed": {k: v["mean_chosen_speed"]["mean"] for k, v in d["endpoints_by_arm"].items()},
            "divergence_share": {k: v["divergence_share"]["mean"] for k, v in d["endpoints_by_arm"].items()},
            "backoff_distribution": {k: v["backoff_distribution"] for k, v in d["endpoints_by_arm"].items()},
            "min_gap_mean": {k: v["min_gap_mean"]["mean"] for k, v in d["endpoints_by_arm"].items()},
            "ttc_mean": {k: v["ttc_mean"]["mean"] for k, v in d["endpoints_by_arm"].items()},
            "ttc_share_lt_2s": {k: v["ttc_share_lt_2s"]["mean"] for k, v in d["endpoints_by_arm"].items()},
            "ANEES_PD7": {k: v.get("anees") for k, v in d["calibration"]["PD7_primary"].items()},
            "p_v_PD7": {k: v.get("p_v") for k, v in d["calibration"]["PD7_primary"].items()},
            "cov95_PD7": {k: (v.get("ellipse_coverage") or {}).get("0.95") for k, v in d["calibration"]["PD7_primary"].items()},
            "NLL_PD7": {k: v.get("nll_mean") for k, v in d["calibration"]["PD7_primary"].items()},
            "ES_PD7": {k: v.get("energy_score_mean") for k, v in d["calibration"]["PD7_primary"].items()},
            "sharpness_PD7_long_lat": {k: [v.get("mean_margin_long"), v.get("mean_margin_lat")] for k, v in d["calibration"]["PD7_primary"].items()},
            "HK1_by_arm": {k: v["HK1"] for k, v in d["validity_by_arm"].items()},
            "Mstar_HK1": {k: d["HK1"][k] for k in ("HK1a", "HK1b", "HK1")},
            "Mstar_flagged_cells": d["hypotheses"]["flagged_cells"], "Mstar_family_flagged_cells": d["hypotheses"]["family_flagged_cells"],
            "HK3_Mstar_lower_than": {k: v["lower"] for k, v in d["HK3"].items() if v["tested"]},
            "sweep": {"retuned_nominal_delta": d["sweep"]["retuned_nominal_delta"], "retuned_nominal_arm": d["sweep"]["retuned_nominal_arm"],
                      "retuned_alpha": d["sweep"]["retuned_alpha"], "reading": d["sweep"]["reading"],
                      "alpha_curve": [(r_["value"], r_["V1_PD7_E"], r_["infeasible_rate"]) for r_ in d["sweep"]["alpha"]],
                      "delta_curve": [(r_["value"], r_["V1_PD7_E"], r_["infeasible_rate"]) for r_ in d["sweep"]["delta_prime"]]},
            "d14_forms": {k: d["d14_forms"][k].get("met") for k in ("A_K6_form", "B_literature_form")},
            "d14_form_B_passing_comparators": d["d14_forms"]["B_literature_form"]["comparators_passing_validity"],
            "d14_form_C": d["d14_forms"]["C_B_plus_price_bound"],
            "consistency_all_equal": all(v["equal"] for v in d["consistency_decisions_vs_counts"].values()),
            "records_PD7_Mstar": d["counts"]["records_by_population"]["PD7_primary"].get("Mstar", {}).get("records"),
            "items": {k: v for k, v in (d["counts"].get("items") or {}).items() if k != "by_population"},
            "fallback_entries": (d["fallback_strata"] or {}).get("entries"),
            "arms": arms}
        lo = r["loop"][t]
        out["loop"][t] = {k: {"progress_K6": v["progress_mean"], "at_fault_tracked": v["at_fault_tracked"], "infeasible_frames": v["infeasible_frame_share"],
                              "progress_ratio": (lo["endpoints_by_arm"].get(k) or {}).get("progress_ratio", {}).get("mean"),
                              "V2_PL7": (lo["V2"]["PL7_offset_le_15m"].get(k) or {}).get("E")}
                          for k, v in lo["outcomes"].items()}
    out["k7_form_reported_only"] = r.get("k7_form_reported_only", {}).get("k7_rule_would_say")
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
    print("K8 DEV CHECK DONE")


if __name__ == "__main__":
    main()
