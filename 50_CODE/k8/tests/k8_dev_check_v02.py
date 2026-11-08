#!/usr/bin/env python3
"""K8 development check (Claude line, v02, 1 Nov 2026; D14 v04 section 5 item 2). Development scenes only: k8_items_v02 --dev and
k8_run_v02 --dev (the 10 nuScenes-mini scenes, asserted) for both trackers and both modes with the K7 fits, then
k8_analyse_v02 --allow-dev (B = 2000; evaluability relaxed to >= 2 scenes from >= 1 log as in K7's development analysis) with the
development items (A6 primary, A8) and the fits (A3 folds, A13). Writes the headline JSON, the analysis JSON, the CSVs and the
timings used for the exploratory run-time estimate. Diagnostics, not evidence. Nothing is run on a non-development scene.
Usage: python -B k8_dev_check_v02.py --out <json> --runs <dir> --csv-dir <dir> [--workers n] [--boot B] [--skip-runs]
"""
import argparse
import json
import os
import subprocess
import sys
import time

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(K8))
HEAD_ARMS = ("Z0", "B0", "B3", "B4", "Mstar", "RETUNED")


def run(cmd):
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stdout[-4000:] + "\n" + p.stderr[-8000:] + "\n")
        raise SystemExit("command failed: " + " ".join(cmd[:4]))
    return p.stdout, time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", required=True)
    ap.add_argument("--csv-dir", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--boot", type=int, default=2000)
    ap.add_argument("--skip-runs", action="store_true", help="reuse the run and items outputs already in --runs")
    a = ap.parse_args()
    py = sys.executable
    os.makedirs(a.runs, exist_ok=True)
    timing = {}
    items = [os.path.join(a.runs, "items_k8_v02_dev_%s.npz" % t) for t in ("t1", "t3")]
    fits = [os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t) for t in ("t1", "t3")]
    if not a.skip_runs:
        for t, ip in zip(("t1", "t3"), items):
            caches = [os.path.join(W, "30_DATA", "k6", "cache_v02_%s_%s" % (t, sp)) for sp in ("train", "val")]
            _, dt = run([py, "-B", os.path.join(K8, "k8_items_v02.py"), "--caches", *caches, "--out", ip, "--dev", "--workers", str(a.workers)])
            timing["items_%s_s" % t] = round(dt, 1)
            for mode in ("decide", "loop"):
                _, dt = run([py, "-B", os.path.join(K8, "k8_run_v02.py"), "--caches", *caches, "--fits", fits[0 if t == "t1" else 1], "--tag", "%s_%s" % (t, mode),
                             "--mode", mode, "--out", a.runs, "--dev", "--workers", str(a.workers)])
                timing["run_%s_%s_s" % (t, mode)] = round(dt, 1)
                print("run %s_%s done (%.0f s)" % (t, mode, dt), flush=True)
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % sp, "MANIFEST.json") for sp in ("train", "val")]
    res_path = os.path.join(a.runs, "k8_dev_analysis_v02.json")
    cmd = [py, "-B", os.path.join(K8, "k8_analyse_v02.py"), "--runs", a.runs, "--tags", "t1", "t3", "--manifests", *man, "--out", res_path,
           "--csv-dir", a.csv_dir, "--allow-dev", "--boot", str(a.boot), "--fits", *fits, "--items", *items]
    _, dt = run(cmd)
    timing["analysis_s"] = round(dt, 1)
    rr = {}
    for t in ("t1", "t3"):
        for mode in ("decide", "loop"):
            r_ = json.load(open(os.path.join(a.runs, "run_record_%s_%s.json" % (t, mode))))
            rr["%s_%s" % (t, mode)] = {k: r_.get(k) for k in ("scenes", "episodes", "decisions", "seconds", "scene_seconds_median", "scene_seconds_sum", "prereg")}
        s_ = json.load(open(items[0 if t == "t1" else 1].replace(".npz", "_summary.json")))
        rr["items_%s" % t] = {k: s_.get(k) for k in ("scenes", "items", "records", "items_ref_relied", "seconds", "stamp")}
    r = json.load(open(res_path))
    out = {"note": "development scenes only (the 10 nuScenes-mini scenes); diagnostics, not evidence; nothing gated", "stamp": r["stamp"],
           "design": r["design"], "boot": r["boot"], "analysis_json": os.path.abspath(res_path), "csv_dir": os.path.abspath(a.csv_dir),
           "timing_wall_s": timing, "run_records": rr, "decide": {}, "loop": {}}
    for t in ("t1", "t3"):
        d = r["decide"][t]
        arms = [x for x in HEAD_ARMS if x in d["arms"]]
        pooled = lambda p: {k: (d["populations"][p]["pooled_by_arm"].get(k) or {}).get("E") for k in arms}  # noqa: E731
        v2 = lambda var, p="PD7_primary", f="E": {k: d["V2"][p][k][var].get(f) for k in arms}  # noqa: E731
        ep = lambda f: {k: d["endpoints_by_arm"][k][f]["mean"] for k in arms}  # noqa: E731
        a6 = (d.get("calibration_items") or {}).get("by_population", {}).get("PD7_primary", {})
        rt = d.get("retune") or {}
        out["decide"][t] = {
            "scenes": d["scenes"], "logs": d["logs"],
            "infeasible_rate": {k: d["infeasible_rate"][k]["mean"] for k in arms},
            "pooled_PD7": pooled("PD7_primary"), "pooled_SD1_7": pooled("SD1_7_gap_le_5m"), "pooled_PD": pooled("PD_inpath"), "pooled_NIP": pooled("NIP_not_in_path"),
            "V2_PD7": v2("V2"), "V2_PD7_reference": v2("V2", f="reference_E"), "V2_PD7_tracks_per_decision": v2("V2", f="mean_tracks_per_decision"),
            "V2_near_PD7": v2("V2_near"), "V2_near_PD7_reference": v2("V2_near", f="reference_E"), "V2_viol_PD7": v2("V2_viol"),
            "V2_binding_PD7": v2("V2_binding"), "V2_exec_PD7": v2("V2_exec"), "V2_dedup_PD7": v2("V2_dedup"), "V2_one_step_PD7": v2("V2_one_step"),
            "ttv_share_lt_2s": ep("ttv_share_lt_2s"), "ttv_share_lt_4s": ep("ttv_share_lt_4s"), "ttv_enf_share_lt_2s": ep("ttv_enf_share_lt_2s"),
            "ttv_enf_share_lt_4s": ep("ttv_enf_share_lt_4s"), "ttv_mean": ep("ttv_mean"), "ttc_proxy_v01_share_lt_2s": ep("ttc_proxy_v01_share_lt_2s"),
            "min_gap_mean": ep("min_gap_mean"), "min_gap_ip_mean": ep("min_gap_ip_mean"), "min_gap_nip_mean": ep("min_gap_nip_mean"),
            "progress_ratio": ep("progress_ratio"), "estop_share": ep("estop_share"),
            "A6_items_PD7": {k: {"anees_scene_level": (a6.get(k, {}).get("anees_scene_level") or {}).get("mean"),
                                 "anees_scene_level_ci95": (a6.get(k, {}).get("anees_scene_level") or {}).get("ci95"),
                                 "median_nees": a6.get(k, {}).get("median_nees"), "anees_trimmed_1pct": a6.get(k, {}).get("anees_trimmed_1pct"),
                                 "share_nees_sum_top_1pct": a6.get(k, {}).get("share_nees_sum_top_1pct"),
                                 "p_v_below": a6.get(k, {}).get("p_v_below"), "p_v_above": a6.get(k, {}).get("p_v_above"),
                                 "cov95": (a6.get(k, {}).get("ellipse_coverage") or {}).get("0.95"), "nll": a6.get(k, {}).get("nll_mean"),
                                 "energy_score": a6.get(k, {}).get("energy_score_mean"),
                                 "sharpness_long_lat": [a6.get(k, {}).get("mean_margin_long"), a6.get(k, {}).get("mean_margin_lat")]} for k in arms if k in a6},
            "A6_items_records": (d.get("calibration_items") or {}).get("records_PD7"),
            "A6_gross_errors": (d.get("calibration_items") or {}).get("gross_errors", {}).get("count"),
            "A14_duplicates_PD7": {k: d["A14_duplicates"]["PD7_primary"][k]["duplicates"] for k in arms},
            "A14_V1_PD7_dedup": {k: d["A14_duplicates"]["PD7_primary"][k]["V1_pooled_dedup"] for k in arms},
            "A13_record_weighted_PD7": ((d.get("A13_fallback_record_weighted") or {}).get("by_population", {}).get("PD7_primary") or {}).get("pooled"),
            "A13_cells_coarser_bound_only_PD7": sum(1 for c in (((d.get("A13_fallback_record_weighted") or {}).get("by_population", {}).get("PD7_primary") or {})
                                                                 .get("by_cell") or {}).values() if c.get("coarser_bound_only")),
            "retune": {"arm_of_fold": rt.get("arm_of_fold"), "alpha_of_fold": rt.get("alpha_of_fold"), "folds_applied": rt.get("folds_applied"),
                       "boundary_any": rt.get("boundary_any"), "boundary_by_fold": {f: s_["boundary"] for f, s_ in (rt.get("by_fold") or {}).items()},
                       "in_sample_choice_reported_only": rt.get("in_sample_choice_reported_only")},
            "one_curve": [(r_["arm"], round(r_["alpha_eq"], 4), r_["V1_PD7_E"], r_["infeasible_rate"]) for r_ in d["sweep"]["one_curve"]],
            "validity_form_B": {k: d["validity_by_arm"][k]["valid_form_B"] for k in d["arms"]},
            "Mstar_HK1": {k: d["HK1"][k] for k in ("HK1a", "HK1b", "HK1")},
            "d14_form_A": {k: d["d14_forms"]["A_K6_form"][k] for k in ("comparators", "level", "met", "validity_M")} | {"lower_than": {b: v["lower"] for b, v in d["d14_forms"]["A_K6_form"]["lower_than"].items()}},
            "d14_form_B": {k: d["d14_forms"]["B_literature_form"][k] for k in ("comparators", "comparators_passing_validity", "met", "vacuous")},
            "d14_form_C": d["d14_forms"]["C_B_plus_price_bound"],
            "consistency_all_equal": all(v["equal"] for v in d["consistency_decisions_vs_counts"].values()),
            "A6_items_equal_ref_relied": (d.get("calibration_items") or {}).get("records_equal_ref_relied_items"),
            "arms": d["arms"]}
        lo = r["loop"][t]
        out["loop"][t] = {k: {"progress_K6": v["progress_mean"], "at_fault_tracked": v["at_fault_tracked"], "infeasible_frames": v["infeasible_frame_share"],
                              "progress_ratio": (lo["endpoints_by_arm"].get(k) or {}).get("progress_ratio", {}).get("mean"),
                              "ttv_share_lt_2s": (lo["endpoints_by_arm"].get(k) or {}).get("ttv_share_lt_2s", {}).get("mean"),
                              "V2_PL7": ((lo["V2"]["PL7_offset_le_15m"].get(k) or {}).get("V2") or {}).get("E"),
                              "V2_PL7_reference": ((lo["V2"]["PL7_offset_le_15m"].get(k) or {}).get("V2") or {}).get("reference_E")}
                          for k, v in lo["outcomes"].items() if k in HEAD_ARMS + ("LOG",)}
    out["k7_form_reported_only"] = r.get("k7_form_reported_only", {}).get("k7_rule_would_say")
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))
    print("K8 DEV CHECK V02 DONE")


if __name__ == "__main__":
    main()
