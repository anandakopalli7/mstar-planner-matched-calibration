#!/usr/bin/env python3
"""Tests of k8_analyse_v03 (Claude line, 1 Nov 2026; 70_TESTS/R15B_K8V02_CHECK_v01.md N1-N3, n2-n8). Development outputs and
synthetic records only: nothing here reads a non-development scene cache (only the cache MANIFEST.json files, for scene NAMES and
logs), imports or runs k8_run_v02 / k8_items_v02, or touches 70_TESTS/k8_expl_v02 or 70_TESTS/k8_expl_v02_records_archive.
Every output goes to 70_TESTS/k8_scratch/v03/.
  (a) v03 --allow-dev on the stored development runs (70_TESTS/k8_scratch/v02/dev_v02, B = 2000, the dev check's arguments):
      every number of k8_analyse_v02 rerun on the same runs in the same environment (single-threaded BLAS; --allow-dev does not
      import the runner) is reproduced EXACTLY, JSON and CSVs; against the stored v02 outputs every number agrees to a relative
      1e-12 (last-digit BLAS summation-order differences, which the v02 rerun shows too) and the development check's headline
      (k8_dev_check_v02.json) exactly; the by-design changes are listed (BY_DESIGN: two strings, no number); everything else v03
      writes is an addition (listed).
  (b) a synthetic exploratory run directory (the 10 development scenes' stored outputs copied onto the 840 non-development scene
      NAMES, thinned to about 1/10 except M*'s count rows, which are copied in full so that M*'s strict quantiles stay defined as
      on the development data, with B1's exceedances set to zero; run, launch and items records as k8_run_v02 / k8_items_v02 write them,
      with the current hashes): k8_analyse_v02.analyse_decide with the exploratory statistics raises "non-finite sup-t quantile"
      (shown, with the arm and the set), while v03 --exploratory completes, records q = None with ZERO_SE_NOTE for B1 and for the
      arm v02 died on, keeps M*'s quantiles finite, and archives every record it read (originals unchanged).
  (c) M*'s strictness is kept: hk1_rule raises on a zero-SE M* family and records None for a comparator; a constant-rate
      comparator (est 1 > delta, zero SE) is flagged in every cell by A.flag's est > delta rule; --allow-dev stays relaxed.
  (d) the v02 binding (check_exploratory) on synthetic name-only records: accepts matching v02 records (the fits stored as the
      relative path run_k8_expl_v02.sh passes, resolved against the run cwd from another process cwd: n6) and refuses a
      mismatched sim hash, a run naming v03 as its analysis, launch code files other than V02_CODE_FILES, items with other
      manifest hashes (n7), a wrong run cwd (n6), the other tracker's --fits, a development scene and a dry run; the records are
      archived before any check, by reading only.
  (e) checkpoint recovery: an abort injected in the second loop analysis (t3_loop) leaves t1_decide, t1_loop, t3_decide on
      disk; --resume reuses them (t3_loop takes RETUNED from the t3_decide checkpoint) and the final JSON and the CSVs equal (a)'s;
      a checkpoint with another key or a changed CSV is not reused.
  (f) R15b n2: T4 as counts on the development curve (stored decision-mode runs): along the merged alpha / delta' curve the
      pooled PD7 exceedance count X is non-increasing and the infeasible-decision count non-decreasing, with no tolerance.
Usage: python -B test_k8_analyse_v03.py <out json> [--parts abcdef] [--reuse]
"""
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from collections import Counter

import numpy as np

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K8))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, K8)
import k6_analyse_v02 as A  # noqa: E402
import k8_sim_v02 as S  # noqa: E402
import k8_analyse_v02 as V2  # noqa: E402
import k8_analyse_v03 as V3  # noqa: E402

V3_PATH = os.path.join(K8, "k8_analyse_v03.py")
SCR = os.path.join(W_ROOT, "70_TESTS", "k8_scratch", "v03")
DEV_RUNS = os.path.join(W_ROOT, "70_TESTS", "k8_scratch", "v02", "dev_v02")
DEV_CSV_V02 = os.path.join(W_ROOT, "70_TESTS", "k8_scratch", "v02", "dev_csv_v02")
DEV_JSON_V02 = os.path.join(DEV_RUNS, "k8_dev_analysis_v02.json")
DEV_CHECK_V02 = os.path.join(W_ROOT, "70_TESTS", "k8_scratch", "v02", "k8_dev_check_v02.json")
A_JSON = os.path.join(SCR, "dev_v03", "k8_dev_analysis_v03.json")
A_CSV = os.path.join(SCR, "dev_csv_v03")
FORBIDDEN = (os.path.join(W_ROOT, "70_TESTS", "k8_expl_v02"), V3.ARCHIVE_DEFAULT)
DEV = A.DEV_SCENES
FITS = {t: os.path.join(W_ROOT, "60_RESULTS", "k7_fits_v01", "k7_fits_%s_v01.json" % t) for t in ("t1", "t3")}
FITS_REL = {t: "../../60_RESULTS/k7_fits_v01/k7_fits_%s_v01.json" % t for t in ("t1", "t3")}    # as run_k8_expl_v02.sh passes them
CACHES = {t: [os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_%s_%s" % (t, sp)) for sp in ("train", "val")] for t in ("t1", "t3")}
T1_MANIFESTS = [os.path.join(c, "MANIFEST.json") for c in CACHES["t1"]]
DEV_ITEMS = [os.path.join(DEV_RUNS, "items_k8_v02_dev_%s.npz" % t) for t in ("t1", "t3")]
PROTECTED = [V3.V02_CODE_FILES[k] for k in ("analysis", "sim", "runner", "k6_sim_v02", "k6_analyse_v02", "m_lib_v04")] + \
            [V3.V02_ITEMS_SCRIPT, FITS["t1"], FITS["t3"]] + [os.path.join(c, "MANIFEST.json") for t in ("t1", "t3") for c in CACHES[t]]
BY_DESIGN = {"/analysis_sha256": "the analysis file is k8_analyse_v03.py (its own hash)",
             "/design": "D14_K8_DESIGN_v05 (v03 implements D14 v05)"}
ENV = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1")
EXPL_STAMP = V3.EXPLORATORY_RUN_STAMP


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def safe_out(p):
    ap = os.path.normcase(os.path.abspath(p))
    assert ap.startswith(os.path.normcase(SCR)) and not any(ap.startswith(os.path.normcase(f)) for f in FORBIDDEN), "test output outside v03 scratch: " + p
    return p


def run_v03(argv, log, cwd=K8):
    t0 = time.time()
    p = subprocess.run([sys.executable, "-B", V3_PATH] + list(argv), cwd=cwd, capture_output=True, text=True, env=ENV)
    with open(safe_out(log), "w", encoding="utf-8") as f:
        f.write(p.stdout + "\n--- stderr ---\n" + p.stderr)
    return p, round(time.time() - t0, 1)


def dev_argv(out_json, csv_dir):
    return ["--runs", DEV_RUNS, "--tags", "t1", "t3", "--manifests", *T1_MANIFESTS, "--out", out_json, "--csv-dir", csv_dir, "--allow-dev",
            "--boot", "2000", "--fits", FITS["t1"], FITS["t3"], "--items", *DEV_ITEMS]


def nondev_names(tag):
    return sorted(s_ for c in CACHES[tag] for s_ in json.load(open(os.path.join(c, "MANIFEST.json")))["scenes"] if s_ not in DEV)


# ---------------------------------------------------------------- JSON / CSV comparison

def _num(x):
    return isinstance(x, (int, float)) and not isinstance(x, bool)


def walk(a, b, path, acc):
    """Every leaf of a (v02) against b (v03): numbers exactly (NaN = NaN; 5 = 5.0), booleans, None and strings; dict keys only in
    b are additions."""
    if isinstance(a, dict):
        if not isinstance(b, dict):
            acc["type"].append(path)
            return
        for k in a:
            if k not in b:
                acc["removed"].append(path + "/" + k)
            else:
                walk(a[k], b[k], path + "/" + k, acc)
        for k in b:
            if k not in a:
                acc["added"].append(path + "/" + k)
    elif isinstance(a, list):
        if not isinstance(b, list) or len(a) != len(b):
            acc["list_len"].append(path)
            return
        for i, (x, y) in enumerate(zip(a, b)):
            walk(x, y, "%s[%d]" % (path, i), acc)
    elif _num(a):
        acc["numbers"] += 1
        if not (_num(b) and (a == b or (isinstance(a, float) and isinstance(b, float) and math.isnan(a) and math.isnan(b)))):
            acc["numeric_mismatch"].append((path, a, b))
    elif isinstance(a, str):
        acc["strings"] += 1
        if a != b:
            acc["string_changes"].append((path, a[:80], str(b)[:80]))
    else:
        acc["other"] += 1
        if a != b:
            acc["value_mismatch"].append((path, a, b))


def new_acc():
    return {"numbers": 0, "strings": 0, "other": 0, "numeric_mismatch": [], "string_changes": [], "value_mismatch": [], "added": [],
            "removed": [], "list_len": [], "type": []}


def pattern(path):
    """An added field's path with list indices, tags, arms, populations and folds replaced by placeholders (for the report)."""
    import re
    arms, pops = set(V3.ALL_ARMS) | {"LOG"}, set(V3.POP_DECIDE) | set(V3.POP_LOOP)
    seg = []
    for s_ in re.sub(r"\[\d+\]", "[]", path).split("/"):
        seg.append("<tag>" if s_ in ("t1", "t3") else "<arm>" if s_ in arms else "<pop>" if s_ in pops else "<n>" if s_.isdigit() else s_)
    return "/".join(seg)


def _cell(s, sig):
    if sig is None or s in ("", None):
        return s
    try:
        return "%.*g" % (sig, float(s))
    except ValueError:
        return s


def compare_csv_dirs(d2, d3, sig=None):
    """Every row of every v02 CSV must appear in the v03 CSV of the same name, projected on v02's columns (a multiset); v03 may
    add columns, rows (new variants) and files. sig: compare numbers at that many significant digits (None: exactly)."""
    out = {"files": {}, "missing_files": [], "new_files": sorted(set(os.listdir(d3)) - set(os.listdir(d2))), "rows_missing_total": 0,
           "significant_digits": sig or "exact"}
    for fn in sorted(os.listdir(d2)):
        if not fn.endswith(".csv"):
            continue
        p3 = os.path.join(d3, fn)
        if not os.path.exists(p3):
            out["missing_files"].append(fn)
            continue
        with open(os.path.join(d2, fn), newline="", encoding="utf-8") as f:
            r2 = list(csv.DictReader(f))
        with open(p3, newline="", encoding="utf-8") as f:
            rd = csv.DictReader(f)
            cols3 = rd.fieldnames
            r3 = list(rd)
        cols2 = list(r2[0].keys()) if r2 else []
        miss_cols = [c for c in cols2 if c not in cols3]
        c2 = Counter(tuple(_cell(r[c], sig) for c in cols2) for r in r2)
        c3 = Counter(tuple(_cell(r.get(c), sig) for c in cols2) for r in r3)
        missing = c2 - c3
        extra = c3 - c2
        out["files"][fn] = {"rows_v02": len(r2), "rows_v03": len(r3), "v02_rows_missing_in_v03": sum(missing.values()),
                            "rows_added_in_v03": sum(extra.values()), "columns_missing": miss_cols, "columns_added": [c for c in cols3 if c not in cols2]}
        if "variant" in cols3 and extra:
            out["files"][fn]["added_row_variants"] = sorted({r["variant"] for r in r3 if tuple(_cell(r.get(c), sig) for c in cols2) in extra})
        out["rows_missing_total"] += sum(missing.values()) + (len(r2) if miss_cols else 0)
    out["pass"] = bool(not out["missing_files"] and out["rows_missing_total"] == 0)
    return out


def headline(r):
    """k8_dev_check_v02's headline extraction (tests/k8_dev_check_v02.py, lines 71-124), applied to an analysis JSON."""
    HEAD_ARMS = ("Z0", "B0", "B3", "B4", "Mstar", "RETUNED")
    out = {"decide": {}, "loop": {}}
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
                       "in_sample_choice_reported_only": {k: v for k, v in (rt.get("in_sample_choice_reported_only") or {}).items() if k in ("alpha", "arm", "boundary")}},
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
    return json.loads(json.dumps(out, default=float))


# ---------------------------------------------------------------- (a)

V2_RERUN_DIR = os.path.join(SCR, "dev_v02_rerun_same_env")
V2_RERUN_JSON = os.path.join(V2_RERUN_DIR, "k8_dev_analysis_v02_rerun.json")
V2_RERUN_CSV = os.path.join(V2_RERUN_DIR, "csv")
ULP_REL = 1e-12


def json_compare(j2, j3):
    acc = new_acc()
    walk(j2, j3, "", acc)
    changed = [c[0] for c in acc["string_changes"]]
    rel = [abs(a - b) / max(abs(a), abs(b), 1e-300) for _, a, b in acc["numeric_mismatch"] if _num(a) and _num(b)]
    out = {"numbers_compared": acc["numbers"], "strings_compared": acc["strings"], "other_compared": acc["other"],
           "n_numeric_mismatch": len(acc["numeric_mismatch"]), "numeric_mismatch_examples": acc["numeric_mismatch"][:30],
           "max_relative_difference": max(rel) if rel else 0.0, "all_mismatches_ulp_level": bool(len(rel) == len(acc["numeric_mismatch"]) and all(r_ <= ULP_REL for r_ in rel)),
           "value_mismatch": acc["value_mismatch"][:50], "removed": acc["removed"][:50], "list_len_changed": acc["list_len"][:50],
           "type_changed": acc["type"][:50], "string_changes": acc["string_changes"],
           "string_changes_by_design": {p_: BY_DESIGN[p_] for p_ in changed if p_ in BY_DESIGN},
           "string_changes_not_by_design": [p_ for p_ in changed if p_ not in BY_DESIGN],
           "added_fields": len(acc["added"]), "added_field_patterns": sorted({pattern(p_) for p_ in acc["added"]})}
    out["structure_ok"] = bool(not acc["value_mismatch"] and not acc["removed"] and not acc["list_len"] and not acc["type"]
                               and not out["string_changes_not_by_design"])
    return out


def part_a(reuse):
    """(a) v03 reproduces v02 on the development outputs. Exactly against a v02 rerun in the same environment (single-threaded
    BLAS, as every v03 run here); against the stored v02 outputs (made with multi-threaded BLAS by k8_dev_check_v02) every number
    agrees to a relative 1e-12 (the last-digit differences come from the BLAS summation order, and v02 itself shows the same ones
    against its stored outputs), the CSVs at 12 significant digits, and the development check's headline exactly."""
    os.makedirs(safe_out(os.path.dirname(A_JSON)), exist_ok=True)
    res = {}
    if not (reuse and os.path.exists(A_JSON) and json.load(open(A_JSON)).get("analysis_sha256") == sha(V3_PATH)):
        p, dt = run_v03(dev_argv(A_JSON, A_CSV), os.path.join(SCR, "dev_v03", "run_a.log"))
        res["run_v03"] = {"returncode": p.returncode, "seconds": dt, "done": "K8 ANALYSIS V03 DONE" in p.stdout}
        if p.returncode != 0:
            res["pass"] = False
            res["stderr_tail"] = p.stderr[-3000:]
            return res
    else:
        res["run_v03"] = "reused (the JSON carries the current v03 hash)"
    v02_path = V3.V02_CODE_FILES["analysis"]
    if not (reuse and os.path.exists(V2_RERUN_JSON) and json.load(open(V2_RERUN_JSON)).get("analysis_sha256") == sha(v02_path)):
        os.makedirs(safe_out(V2_RERUN_DIR), exist_ok=True)
        t0 = time.time()
        argv = dev_argv(V2_RERUN_JSON, V2_RERUN_CSV)
        p = subprocess.run([sys.executable, "-B", v02_path] + argv, cwd=K8, capture_output=True, text=True, env=ENV)   # --allow-dev: no runner import
        open(os.path.join(V2_RERUN_DIR, "run_v02.log"), "w", encoding="utf-8").write(p.stdout + "\n--- stderr ---\n" + p.stderr)
        res["run_v02_same_env"] = {"returncode": p.returncode, "seconds": round(time.time() - t0, 1)}
        if p.returncode != 0:
            res["pass"] = False
            res["stderr_tail_v02"] = p.stderr[-3000:]
            return res
    else:
        res["run_v02_same_env"] = "reused (the JSON carries the current k8_analyse_v02 hash)"
    j2s, j2r, j3 = json.load(open(DEV_JSON_V02)), json.load(open(V2_RERUN_JSON)), json.load(open(A_JSON))
    res["exact_vs_v02_same_env"] = {"json": json_compare(j2r, j3), "csv": compare_csv_dirs(V2_RERUN_CSV, A_CSV)}
    ex = res["exact_vs_v02_same_env"]
    ex["pass"] = bool(ex["json"]["n_numeric_mismatch"] == 0 and ex["json"]["structure_ok"] and ex["csv"]["pass"])
    res["vs_stored_v02"] = {"json": json_compare(j2s, j3), "csv_12_significant_digits": compare_csv_dirs(DEV_CSV_V02, A_CSV, 12),
                            "csv_exact_rows_missing": compare_csv_dirs(DEV_CSV_V02, A_CSV)["rows_missing_total"]}
    acc_env = json_compare(j2s, j2r)
    res["vs_stored_v02"]["v02_rerun_vs_stored_same_differences"] = {
        "n_numeric_mismatch": acc_env["n_numeric_mismatch"], "max_relative_difference": acc_env["max_relative_difference"],
        "note": "k8_analyse_v02 itself, rerun with single-threaded BLAS, differs from its stored outputs in the last digit at the same "
                "kind of places: the stored outputs used multi-threaded BLAS (another summation order)"}
    st_ = res["vs_stored_v02"]
    st_["pass"] = bool(st_["json"]["all_mismatches_ulp_level"] and st_["json"]["structure_ok"] and st_["csv_12_significant_digits"]["pass"])
    st_["json"].pop("added_field_patterns", None)          # the same list as in exact_vs_v02_same_env
    res["added_by_v03"] = {"fields": ex["json"]["added_fields"], "field_patterns": ex["json"]["added_field_patterns"],
                           "csv_files": ex["csv"]["new_files"],
                           "csv_columns": {fn: v["columns_added"] for fn, v in ex["csv"]["files"].items() if v["columns_added"]},
                           "csv_rows": {fn: v.get("added_row_variants", v["rows_added_in_v03"]) for fn, v in ex["csv"]["files"].items() if v["rows_added_in_v03"]}}
    j2 = j2s
    h2, h3 = headline(j2), headline(j3)
    stored = json.load(open(DEV_CHECK_V02))
    st = json.loads(json.dumps({k: stored[k] for k in ("decide", "loop", "k7_form_reported_only")}, default=float))
    acc_h = new_acc()
    walk(h2, h3, "", acc_h)
    acc_s = new_acc()
    walk(st, h3, "", acc_s)
    res["dev_check_headline"] = {"numbers_compared": acc_h["numbers"], "v03_equals_v02_analysis": bool(json.dumps(h2, sort_keys=True) == json.dumps(h3, sort_keys=True)),
                                 "v03_equals_stored_k8_dev_check_v02_json": bool(not acc_s["numeric_mismatch"] and not acc_s["value_mismatch"]
                                                                                and not acc_s["string_changes"] and not acc_s["removed"] and not acc_s["list_len"]),
                                 "stored_numbers_compared": acc_s["numbers"], "mismatch_vs_stored": (acc_s["numeric_mismatch"] + acc_s["value_mismatch"])[:20]}
    res["by_design_changes"] = {"numbers": "none: no fix changes a v02 number on the development outputs (under --allow-dev the strict "
                                           "quantile, the only N1 behaviour change, is not applied, as in v02)",
                                "strings": BY_DESIGN,
                                "additions": "every other difference is an added field, row, column or file (N1 quantiles and notes, N3 "
                                             "safety_reading and its CSVs, n3 boundary flags, n4 note, n5 V2_exec split, checkpoints)"}
    res["pass"] = bool(ex["pass"] and st_["pass"] and res["dev_check_headline"]["v03_equals_v02_analysis"]
                       and res["dev_check_headline"]["v03_equals_stored_k8_dev_check_v02_json"])
    return res


# ---------------------------------------------------------------- (b) synthetic exploratory run directory

def _group(ep):
    order = np.argsort(ep, kind="stable")
    s = ep[order]
    uniq, start = np.unique(s, return_index=True)
    end = np.r_[start[1:], len(s)]
    return {int(u): order[a:b] for u, a, b in zip(uniq, start, end)}


ZERO_ARM = "B1"
FULL_ARM = "Mstar"
X_FIELDS = ("x", "x_h0", "v", "xb", "xe", "xd")
SUB = {"decide": {"counts": 10, "dec": 10, "cal": 12}, "loop": {"counts": 25, "dec": 12, "cal": 15}}


def build_mode(tag, mode, names, fold_of_scene, d):
    eps_t = [json.loads(l) for l in open(os.path.join(DEV_RUNS, "episodes_%s_%s.jsonl" % (tag, mode)))]
    cnt = dict(np.load(os.path.join(DEV_RUNS, "counts_%s_%s.npz" % (tag, mode))))
    dec = dict(np.load(os.path.join(DEV_RUNS, "decisions_%s_%s.npz" % (tag, mode))))
    cal = dict(np.load(os.path.join(DEV_RUNS, "cal_%s_%s.npz" % (tag, mode))))
    pops = V3.POP_DECIDE if mode == "decide" else V3.POP_LOOP
    rel = np.zeros(A.S.N_CELL, bool)
    for spec in pops.values():
        rel |= A.mask(**spec)
    keep_c = rel[cnt["cell"]]
    g_cnt = _group(np.where(keep_c, cnt["episode"], -1))
    g_dec, g_cal = _group(dec["episode"]), _group(cal["episode"])
    by_scene = {}
    for o in eps_t:
        by_scene.setdefault(o["scene"], []).append(o)
    tmpl = sorted(by_scene)
    sub = SUB[mode]
    xi = [list(S.ST_FIELDS).index(f) for f in X_FIELDS]
    eps, ci, di, ki, c_ep, d_ep, k_ep, zero_c, zero_d = [], [], [], [], [], [], [], [], []
    for i, name in enumerate(names):
        phase = i // len(tmpl)                 # varies across the 84 copies of a template, so each copy keeps other rows
        for o in by_scene[tmpl[i % len(tmpl)]]:
            n = dict(o)
            n["scene"], n["episode"], n["stamp"], n["synthetic"] = name, len(eps), EXPL_STAMP, True
            n["fold"] = fold_of_scene[name]
            eps.append(n)
            for g, sel_l, ep_l, r_ in ((g_cnt, ci, c_ep, sub["counts"]), (g_dec, di, d_ep, sub["dec"]), (g_cal, ki, k_ep, sub["cal"])):
                rows = g.get(o["episode"], np.zeros(0, int))
                if not (g is g_cnt and n["arm"] == FULL_ARM):     # M*'s count rows are copied in full (its quantiles must stay finite)
                    rows = rows[(np.arange(len(rows)) + phase) % r_ == 0]
                sel_l.append(rows)
                ep_l.append(np.full(len(rows), n["episode"], np.int64))
                if g is g_cnt:
                    zero_c.append(np.full(len(rows), n["arm"] == ZERO_ARM))
                elif g is g_dec:
                    zero_d.append(np.full(len(rows), n["arm"] == ZERO_ARM))
    ci, di, ki = np.concatenate(ci), np.concatenate(di), np.concatenate(ki)
    zc, zd = np.concatenate(zero_c), np.concatenate(zero_d)
    out = {}
    p = os.path.join(d, "episodes_%s_%s.jsonl" % (tag, mode))
    with open(p, "w") as f:
        for o in eps:
            f.write(json.dumps(o) + "\n")
    out["episodes"] = p
    exc = cnt["exceed"][ci].copy()
    exc[zc] = 0
    p = os.path.join(d, "counts_%s_%s.npz" % (tag, mode))
    np.savez_compressed(p, episode=np.concatenate(c_ep).astype(np.int32), cell=cnt["cell"][ci], n=cnt["n"][ci], exceed=exc, stamp=np.array(EXPL_STAMP))
    out["counts"] = p
    darr = {k: v[di] for k, v in dec.items() if k not in V3.NONROW and k != "episode"}
    st = darr["stats"].reshape(len(di), 4, len(S.ST_FIELDS)).copy()
    st[np.ix_(np.flatnonzero(zd), range(4), xi)] = 0
    darr["stats"] = st.reshape(len(di), -1).astype(np.float32)
    p = os.path.join(d, "decisions_%s_%s.npz" % (tag, mode))
    np.savez_compressed(p, st_fields=dec["st_fields"], trk_fields=dec["trk_fields"], stamp=np.array(EXPL_STAMP),
                        episode=np.concatenate(d_ep).astype(np.int32), **darr)
    out["decisions"] = p
    p = os.path.join(d, "cal_%s_%s.npz" % (tag, mode))
    np.savez_compressed(p, episode=np.concatenate(k_ep).astype(np.int32), key=cal["key"][ki], values=cal["values"][ki], fields=cal["fields"], stamp=np.array(EXPL_STAMP))
    out["cal"] = p
    return out, len(eps), {"count_rows": int(len(ci)), "decision_rows": int(len(di)), "cal_rows": int(len(ki))}


def build_items(tag, names, d, every=60):
    z = dict(np.load(DEV_ITEMS[0 if tag == "t1" else 1]))
    dev_names = [str(x) for x in z["scene_names"]]
    rec = {k: v for k, v in z.items() if k.startswith("rec_")}
    itm = {k: v for k, v in z.items() if k.startswith("item_")}
    gr, gi = _group(rec["rec_s"]), _group(itm["item_s"])
    tmpl = sorted(dev_names)
    rsel, rs, isel, is_ = [], [], [], []
    for i, name in enumerate(names):
        t = dev_names.index(tmpl[i % len(tmpl)])
        phase = i // len(tmpl)
        for g, sel_l, s_l in ((gr, rsel, rs), (gi, isel, is_)):
            rows = g.get(t, np.zeros(0, int))
            rows = rows[(np.arange(len(rows)) + phase) % every == 0]
            sel_l.append(rows)
            s_l.append(np.full(len(rows), i, rec["rec_s"].dtype))
    rsel, isel = np.concatenate(rsel), np.concatenate(isel)
    new = {k: v[rsel] for k, v in rec.items()}
    new["rec_s"] = np.concatenate(rs)
    new.update({k: v[isel] for k, v in itm.items()})
    new["item_s"] = np.concatenate(is_).astype(itm["item_s"].dtype)
    logs = {}
    for c in CACHES[tag]:
        for s_, info in json.load(open(os.path.join(c, "MANIFEST.json")))["scenes"].items():
            logs[s_] = info["log"]
    p = os.path.join(d, "items_k8_v02_expl_%s.npz" % tag)
    np.savez_compressed(p, scene_names=np.array(names), scene_logs=np.array([logs[n] for n in names]), stamp=np.array(EXPL_STAMP), **new)
    man = [sha(os.path.join(c, "MANIFEST.json")) for c in CACHES[tag]]
    hashes = {"items_script_sha256": sha(V3.V02_ITEMS_SCRIPT), "k6_sim_v02_sha256": sha(V3.V02_CODE_FILES["k6_sim_v02"]), "manifest_sha256": man}
    lp = p.replace(".npz", "_launch.json")
    json.dump({"out": os.path.abspath(p), "stamp": EXPL_STAMP, "exploratory": True, "dry_run": False, "scenes": len(names), "hashes": hashes,
               "launched": "synthetic (test_k8_analyse_v03)", "synthetic": True}, open(lp, "w"), indent=1)
    summ = {"stamp": EXPL_STAMP, "exploratory": True, "caches": [os.path.abspath(c) for c in CACHES[tag]], "manifest_sha256": man,
            "scenes": len(names), "scene_names": names, "records": int(len(rsel)), "items": int(len(isel)), "sim_sha256": hashes["k6_sim_v02_sha256"],
            "items_script_sha256": hashes["items_script_sha256"], "hashes": hashes, "launch_record": os.path.abspath(lp), "out_sha256": sha(p),
            "synthetic": True}
    json.dump(summ, open(p.replace(".npz", "_summary.json"), "w"), indent=1)
    return p


def write_records(d, tag, mode, names, n_ep, outs=None, mutate=None, fits_rec=None):
    """Run and launch records as k8_run_v02 writes them (exploratory, current hashes, the runner's code_files); outs: the output
    files (else dummy files are written)."""
    cur = V3.v02_code_hashes()
    hashes = dict(cur, fits_sha256=sha(FITS[tag]), manifest_sha256=[sha(os.path.join(c, "MANIFEST.json")) for c in CACHES[tag]])
    fits_rec = FITS_REL[tag] if fits_rec is None else fits_rec
    tm = "%s_%s" % (tag, mode)
    launch = {"tag": tm, "mode": mode, "prereg": EXPL_STAMP, "exploratory": True, "dry_run": False, "stamp": EXPL_STAMP, "arms": list(S.ARMS),
              "delays_kf": [0, 2, 4], "scenes": len(names), "scene_names": list(names), "dev_scenes_present": [], "fits": fits_rec,
              "caches": [os.path.abspath(c) for c in CACHES[tag]], "hashes": hashes, "code_files": dict(V3.V02_CODE_FILES), "workers": 6,
              "numpy": np.__version__, "launched": "synthetic (test_k8_analyse_v03)", "synthetic": True}
    rec = {"tag": tm, "mode": mode, "prereg": EXPL_STAMP, "exploratory": True, "dry_run": False, "stamp": EXPL_STAMP, "arms": list(S.ARMS),
           "delays_kf": [0, 2, 4], "scenes": len(names), "episodes": n_ep, "fits": fits_rec, "fits_sha256": hashes["fits_sha256"],
           "sim_sha256": hashes["sim_sha256"], "runner_sha256": hashes["runner_sha256"], "manifest_sha256": hashes["manifest_sha256"],
           "hashes": hashes, "hashes_equal_at_end": True, "caches": launch["caches"], "scene_names": list(names), "synthetic": True}
    if mutate:
        mutate(tag, mode, rec, launch)
    lp = os.path.join(d, "launch_record_%s.json" % tm)
    json.dump(launch, open(lp, "w"), indent=1)
    rec["launch_record"], rec["launch_record_sha256"] = os.path.abspath(lp), sha(lp)
    for f, ext in V3.RUN_OUTPUTS:
        fp = os.path.join(d, "%s_%s.%s" % (f, tm, ext))
        if outs is None:
            open(fp, "w").write("synthetic %s %s\n" % (f, tm))
        rec["%s_sha256" % f] = sha(fp)
    json.dump(rec, open(os.path.join(d, "run_record_%s.json" % tm), "w"), indent=1)


def build_synthetic(d):
    os.makedirs(safe_out(d), exist_ok=True)
    with open(os.path.join(d, "README_SYNTHETIC.txt"), "w") as f:
        f.write("SYNTHETIC TEST DATA (test_k8_analyse_v03 part b). The stored outputs of the 10 development scenes "
                "(70_TESTS/k8_scratch/v02/dev_v02), copied onto the 840 non-development scene NAMES (scene i takes development scene "
                "i mod 10) and thinned (every arm but M*, whose count rows are copied in full; the rows kept vary across the copies), with B1's exceedances "
                "set to zero. No non-development scene cache was read. The EXPLORATORY stamps are there only because the binding "
                "requires them: nothing here is nuScenes evidence.\n")
    info = {}
    for tag in ("t1", "t3"):
        names = nondev_names(tag)
        fos = json.load(open(FITS[tag]))["fold_of_scene"]
        for mode in ("decide", "loop"):
            outs, n_ep, sz = build_mode(tag, mode, names, fos, d)
            write_records(d, tag, mode, names, n_ep, outs)
            info["%s_%s" % (tag, mode)] = dict(sz, episodes=n_ep)
        build_items(tag, names, d)
    return info


def v02_raises(d):
    """k8_analyse_v02.analyse_decide on the synthetic T1 decision-mode run with the exploratory statistics (STRICT_Q, 39 scenes / 8
    logs, the development scenes excluded, B = 2000): returns the exception and the arm whose hk1_rule raised."""
    saved = (V2.DEV_SCENES, V2.STRICT_Q, V2.STAMP, A.MIN_SCENES, A.MIN_LOGS, V2.hk1_rule)
    seen = []
    orig = V2.hk1_rule

    def spy(T, cells, scene_of_ep, log_of_ep, W, power_key, fams=None):
        pk = list(power_key)
        seen.append("Mstar" if len(pk) == 2 else V2.ALL_ARMS[pk[-1] - 100])
        return orig(T, cells, scene_of_ep, log_of_ep, W, power_key, fams)
    V2.DEV_SCENES, V2.STRICT_Q, V2.STAMP = V2.DEV_SCENES_K6, True, V2.STAMPS["exploratory"]
    A.MIN_SCENES, A.MIN_LOGS = 39, 8
    V2.hk1_rule = spy
    t0 = time.time()
    try:
        log_of_scene = {}
        for p in T1_MANIFESTS:
            for s_, info in json.load(open(p))["scenes"].items():
                log_of_scene[s_] = info["log"]
        eps = [json.loads(l) for l in open(os.path.join(d, "episodes_t1_decide.jsonl"))]
        counts = dict(np.load(os.path.join(d, "counts_t1_decide.npz")))
        D = dict(np.load(os.path.join(d, "decisions_t1_decide.npz")))
        C = dict(np.load(os.path.join(d, "cal_t1_decide.npz")))
        fits = json.load(open(FITS["t1"]))
        ip = os.path.join(d, "items_k8_v02_expl_t1.npz")
        items, items_k8 = V2.items_counts(ip, set(V2.DEV_SCENES)), V2.load_items_k8(ip, set(V2.DEV_SCENES))
        try:
            V2.analyse_decide(eps, counts, D, C, log_of_scene, V2.B_BOOT, np.random.default_rng([V2.SEED, 0, 0]), [V2.POWER_SEED, 0], fits, items, items_k8)
            err = None
        except AssertionError as e:
            err = str(e)
    finally:
        V2.DEV_SCENES, V2.STRICT_Q, V2.STAMP, A.MIN_SCENES, A.MIN_LOGS, V2.hk1_rule = saved
    return {"raised": err is not None, "message": err, "arm": seen[-1] if seen else None, "arms_tested_before": seen[:-1],
            "seconds": round(time.time() - t0, 1),
            "nothing_written": "v02 writes CSVs only after analyse_decide returns and its JSON once at the end (k8_analyse_v02.main), so "
                               "this abort in the first tracker's decision mode leaves no output"}


def part_b(reuse):
    d = os.path.join(SCR, "synthetic_expl_runs")
    od = os.path.join(SCR, "synthetic_expl_analysis_v03")
    arch = os.path.join(SCR, "synthetic_expl_records_archive")
    res = {}
    t0 = time.time()
    if reuse and os.path.exists(os.path.join(d, "run_record_t3_loop.json")) and os.path.exists(os.path.join(d, "items_k8_v02_expl_t3_summary.json")):
        res["build"] = "reused"
    else:
        for x in (d, od, arch):
            if os.path.exists(x):
                shutil.rmtree(safe_out(x))
        res["build"] = build_synthetic(d)
    res["build_seconds"] = round(time.time() - t0, 1)
    res["v02"] = v02_raises(d)
    recs = sorted(os.path.join(d, f) for f in os.listdir(d) if f.startswith(("run_record_", "launch_record_")) or f.endswith(("_summary.json", "_launch.json")))
    before = {p: (sha(p), os.path.getmtime(p)) for p in recs}
    out_json = os.path.join(od, "k8_SYNTHETIC_exploratory_analysis_v03.json")
    os.makedirs(safe_out(od), exist_ok=True)
    argv = ["--runs", d, "--tags", "t1", "t3", "--manifests", *T1_MANIFESTS, "--out", out_json, "--csv-dir", os.path.join(od, "csv"),
            "--exploratory", "--fits", FITS["t1"], FITS["t3"], "--items", os.path.join(d, "items_k8_v02_expl_t1.npz"),
            os.path.join(d, "items_k8_v02_expl_t3.npz"), "--archive-dir", arch]
    if not (reuse and os.path.exists(out_json) and json.load(open(out_json)).get("analysis_sha256") == sha(V3_PATH)):
        p, dt = run_v03(argv, os.path.join(od, "run_b.log"), cwd=SCR)       # another process cwd: the runs' relative fits resolve against --run-cwd
        res["v03_run"] = {"returncode": p.returncode, "seconds": dt, "done": "K8 ANALYSIS V03 DONE" in p.stdout, "stdout_tail": p.stdout[-1500:]}
        if p.returncode != 0:
            res["v03_run"]["stderr_tail"] = p.stderr[-3000:]
            res["pass"] = False
            return res
    else:
        res["v03_run"] = "reused"
    after = {p: (sha(p), os.path.getmtime(p)) for p in recs}
    j = json.load(open(out_json))
    res["stamp"], res["exploratory"] = j["stamp"], j["exploratory"]
    res["relation"] = j["binding"]["analysis_relation"]
    q = {}
    for t in ("t1", "t3"):
        vb = j["decide"][t]["validity_by_arm"]
        q[t] = {"zero_arm_" + ZERO_ARM: {p_: {"cells_q": vb[ZERO_ARM]["pops"][p_]["q"], "pooled_q": (vb[ZERO_ARM]["pops"][p_]["pooled"] or {}).get("q"),
                                              "family_q": vb[ZERO_ARM]["pops"][p_]["family_q"],
                                              "note": (vb[ZERO_ARM]["pops"][p_]["pooled"] or {}).get("q_note", "")[:len(V3.ZERO_SE_NOTE)]} for p_ in V3.CONF_POPS},
                "Mstar": {p_: {"cells_q": vb["Mstar"]["pops"][p_]["q"], "evaluable_cells": vb["Mstar"]["pops"][p_]["evaluable"],
                               "pooled_q": (vb["Mstar"]["pops"][p_]["pooled"] or {}).get("q"),
                               "family_q": vb["Mstar"]["pops"][p_]["family_q"], "family_size": vb["Mstar"]["pops"][p_]["family_size"]} for p_ in V3.CONF_POPS},
                "zero_se_by_arm": j["decide"][t]["zero_se_quantiles"]["by_arm"],
                "Mstar_strict": vb["Mstar"]["strict_q"]}
    res["quantiles"] = q
    v02arm = res["v02"]["arm"]
    where = (res["v02"]["message"] or "").replace("non-finite sup-t quantile in ", "")
    kind = "pooled" if where.startswith("pooled ") else "family" if where.startswith("family ") else "cells"
    pop = where.split()[-1] if where else None
    res["v02_abort_cell_in_v03"] = {"arm": v02arm, "population": pop, "set": kind,
                                    "v03_records_none": bool(v02arm and pop and ("%s:%s" % (pop, kind)) in q["t1"]["zero_se_by_arm"].get(v02arm, []))}
    zero_ok = all(q[t]["zero_arm_" + ZERO_ARM][p_]["pooled_q"] is None and q[t]["zero_arm_" + ZERO_ARM][p_]["note"] == V3.ZERO_SE_NOTE
                  for t in ("t1", "t3") for p_ in V3.CONF_POPS)
    mstar_ok = all(q[t]["Mstar"][p_]["pooled_q"] is not None and (q[t]["Mstar"][p_]["evaluable_cells"] == 0 or q[t]["Mstar"][p_]["cells_q"] is not None)
                   and q[t]["Mstar_strict"] is True
                   and (q[t]["Mstar"][p_]["family_size"] == 0 or q[t]["Mstar"][p_]["family_q"] is not None) for t in ("t1", "t3") for p_ in V3.CONF_POPS)
    arch_files = j["binding"]["archive"]["files"]
    res["archive"] = {"dir": j["binding"]["archive"]["dir"], "files": len(arch_files),
                      "all_records_archived": sorted(os.path.normcase(e["source"]) for e in arch_files) == sorted(os.path.normcase(os.path.abspath(p_)) for p_ in recs),
                      "copies_equal_originals": all(sha(e["archived"]) == e["sha256"] == sha(e["source"]) for e in arch_files),
                      "originals_unchanged": before == after}
    res["checkpoints"] = {k: v["reused"] for k, v in j["checkpoints"].items()}
    res["safety_headline_present"] = all(k in j["decide"][t]["safety_reading"] for t in ("t1", "t3") for k in ("headline_V2_viol", "secondary", "labelled")) \
        and all(k in j["loop"][t]["safety_reading"] for t in ("t1", "t3") for k in ("headline_collisions", "headline_front_buffer_intrusions"))
    res["pass"] = bool(res["v02"]["raised"] and "non-finite sup-t quantile" in res["v02"]["message"] and j["exploratory"] is True
                       and res["relation"]["relation"] == V3.RELATION and res["relation"]["analysis_named_by_the_runs_sha256"] == sha(V3.V02_CODE_FILES["analysis"])
                       and zero_ok and mstar_ok and res["v02_abort_cell_in_v03"]["v03_records_none"] and all(res["archive"][k] for k in
                       ("all_records_archived", "copies_equal_originals", "originals_unchanged")) and res["safety_headline_present"])
    return res


# ---------------------------------------------------------------- (c) strictness kept for M*

def part_c():
    rng = np.random.default_rng(11)
    nk, nl = 60, 10
    scene_of_ep = np.array(["s%02d" % i for i in range(nk)])
    log_of_ep = np.arange(nk) % nl
    W = rng.multinomial(nl, np.full(nl, 1.0 / nl), size=2000).astype(float)[:, log_of_ep]
    cells = A.cell_family()
    N = np.full((nk, len(cells)), 6.0)
    zero = {p: (N, np.zeros_like(N)) for p in V3.CONF_POPS}
    const = {p: (N, N.copy()) for p in V3.CONF_POPS}
    rnd = {p: (N, rng.binomial(6, 0.03, size=N.shape).astype(float)) for p in V3.CONF_POPS}
    saved = (V3.STRICT_Q, A.MIN_SCENES, A.MIN_LOGS)
    out = {}
    try:
        A.MIN_SCENES, A.MIN_LOGS = 39, 8
        V3.STRICT_Q = True
        try:
            V3.hk1_rule(zero, cells, scene_of_ep, log_of_ep, W, [5, 0], arm="Mstar")
            out["Mstar_zero_se_raises"] = False
        except AssertionError as e:
            out["Mstar_zero_se_raises"] = "non-finite sup-t quantile" in str(e)
            out["Mstar_message"] = str(e)
        rz = V3.hk1_rule(zero, cells, scene_of_ep, log_of_ep, W, [5, 1], arm=ZERO_ARM)
        out["comparator_zero_se"] = {p: {"q": rz["pops"][p]["q"], "pooled_q": rz["pops"][p]["pooled"]["q"], "family_q": rz["pops"][p]["family_q"],
                                         "family_size": rz["pops"][p]["family_size"], "flagged": rz["pops"][p]["flagged"],
                                         "note_ok": rz["pops"][p]["q_note"].startswith(V3.ZERO_SE_NOTE)} for p in V3.CONF_POPS}
        out["comparator_zero_se_list"] = rz["zero_se_quantiles"]
        allc = {p: np.ones(len(cells), bool) for p in V3.CONF_POPS}       # a non-empty power-qualified family (precomputed masks)
        rf = V3.hk1_rule(zero, cells, scene_of_ep, log_of_ep, W, [5, 5], fams=allc, arm=ZERO_ARM)
        out["comparator_zero_se_family"] = {p: {"family_size": rf["pops"][p]["family_size"], "family_q": rf["pops"][p]["family_q"],
                                                "note_ok": (rf["pops"][p].get("family_q_note") or "").startswith(V3.ZERO_SE_NOTE)} for p in V3.CONF_POPS}
        Xm = rng.binomial(6, 0.03, size=N.shape).astype(float)          # cells 0-15 with exceedances, 16-31 none
        Xm[:, 16:] = 0.0
        mixed = {p: (N, Xm) for p in V3.CONF_POPS}
        fz = {p: np.arange(len(cells)) >= 16 for p in V3.CONF_POPS}      # a family of zero-SE cells only
        try:
            V3.hk1_rule(mixed, cells, scene_of_ep, log_of_ep, W, [5, 6], fams=fz, arm="Mstar")
            out["Mstar_zero_se_family_raises"] = False
        except AssertionError as e:
            out["Mstar_zero_se_family_raises"] = "non-finite sup-t quantile in Mstar family" in str(e)
            out["Mstar_family_message"] = str(e)
        rc = V3.hk1_rule(const, cells, scene_of_ep, log_of_ep, W, [5, 2], arm="B4")
        out["comparator_constant_rate_1"] = {p: {"q": rc["pops"][p]["q"], "flagged_cells": len(rc["pops"][p]["flagged"]),
                                                 "pooled_flagged": rc["pops"][p]["pooled"]["flagged"]} for p in V3.CONF_POPS}
        rm = V3.hk1_rule(rnd, cells, scene_of_ep, log_of_ep, W, [5, 3], arm="Mstar")
        out["Mstar_positive_se_ok"] = all(rm["pops"][p]["q"] is not None and rm["pops"][p]["pooled"]["q"] is not None for p in V3.CONF_POPS)
        V3.STRICT_Q = False
        rd = V3.hk1_rule(zero, cells, scene_of_ep, log_of_ep, W, [5, 4], arm="Mstar")
        out["allow_dev_relaxed_for_Mstar"] = all(rd["pops"][p]["q"] is None for p in V3.CONF_POPS) and rd["strict_q"] is False
        V3.STRICT_Q = True
        try:
            V2.STRICT_Q = True
            V2._q(float("nan"), "demo")
            out["v02_q_raises_for_any_arm"] = False
        except AssertionError:
            out["v02_q_raises_for_any_arm"] = True
    finally:
        V3.STRICT_Q, A.MIN_SCENES, A.MIN_LOGS = saved
    cz = out["comparator_zero_se"]
    out["pass"] = bool(out["Mstar_zero_se_raises"] is True
                       and all(v["q"] is None and v["pooled_q"] is None and v["note_ok"] and not v["flagged"] and (v["family_size"] == 0 or v["family_q"] is None) for v in cz.values())
                       and all(v["q"] is None and v["flagged_cells"] == len(cells) and v["pooled_flagged"] for v in out["comparator_constant_rate_1"].values())
                       and all(v["family_size"] == len(cells) and v["family_q"] is None and v["note_ok"] for v in out["comparator_zero_se_family"].values())
                       and out["Mstar_zero_se_family_raises"] is True
                       and out["Mstar_positive_se_ok"] and out["allow_dev_relaxed_for_Mstar"] and out["v02_q_raises_for_any_arm"])
    return out


# ---------------------------------------------------------------- (d) the v02 binding

def part_d():
    base = os.path.join(SCR, "binding")
    if os.path.exists(base):
        shutil.rmtree(safe_out(base))
    os.makedirs(base)
    names = {t: nondev_names(t) for t in ("t1", "t3")}
    v03sha = sha(V3_PATH)

    def make(case, mutate=None, items_mut=None):
        d = os.path.join(base, case)
        os.makedirs(d)
        for tag in ("t1", "t3"):
            for mode in ("decide", "loop"):
                n_ep = len(names[tag]) * (len(S.ARMS) * 3 if mode == "loop" else len(S.ARMS) - 1)
                write_records(d, tag, mode, names[tag], n_ep, None, mutate)
            p = os.path.join(d, "items_k8_v02_expl_%s.npz" % tag)
            open(p, "wb").write(b"synthetic items " + tag.encode())
            man = [sha(os.path.join(c, "MANIFEST.json")) for c in CACHES[tag]]
            hashes = {"items_script_sha256": sha(V3.V02_ITEMS_SCRIPT), "k6_sim_v02_sha256": sha(V3.V02_CODE_FILES["k6_sim_v02"]), "manifest_sha256": man}
            lp = p.replace(".npz", "_launch.json")
            launch = {"out": p, "stamp": EXPL_STAMP, "exploratory": True, "dry_run": False, "hashes": hashes, "launched": "synthetic"}
            summ = {"stamp": EXPL_STAMP, "exploratory": True, "manifest_sha256": list(man), "scene_names": names[tag], "hashes": dict(hashes),
                    "launch_record": os.path.abspath(lp), "out_sha256": sha(p)}
            if items_mut:
                items_mut(tag, summ, launch)
            json.dump(launch, open(lp, "w"))
            json.dump(summ, open(p.replace(".npz", "_summary.json"), "w"))
        return d

    def setk(path_keys, val, when):
        def m(tag, mode, rec, launch):
            if (tag, mode) in when:
                obj = rec if path_keys[0] == "rec" else launch
                for k in path_keys[1:-1]:
                    obj = obj[k]
                obj[path_keys[-1]] = val
        return m
    cases = {
        "well_formed": (None, None, {}, True),
        "sim_hash_mismatch": (setk(("rec", "hashes", "sim_sha256"), "0" * 64, {("t3", "loop")}), None, {}, False),
        "runs_name_v03_as_analysis": (setk(("rec", "hashes", "analysis_sha256"), v03sha, {("t1", "decide")}), None, {}, False),
        "launch_code_files_not_v02": (setk(("launch", "code_files", "analysis"), V3_PATH, {("t3", "decide")}), None, {}, False),
        "items_other_manifests_n7": (None, lambda t, s, l: s.__setitem__("manifest_sha256", ["0" * 64, "1" * 64]) if t == "t3" else None, {}, False),
        "wrong_run_cwd_n6": (None, None, {"run_cwd": SCR}, False),
        "fits_of_other_tracker": (None, None, {"fits_paths": [FITS["t3"], FITS["t1"]]}, False),
        "dev_scene_present": (lambda t, m, r, l: r["scene_names"].__setitem__(0, "scene-0061") if (t, m) == ("t1", "decide") else None, None, {}, False),
        "dry_run": (setk(("rec", "dry_run"), True, {("t1", "loop")}), None, {}, False),
    }
    res = {}
    old_cwd = os.getcwd()
    try:
        os.chdir(SCR)                       # n6: the relative fits paths in the records must resolve against --run-cwd, not the process cwd
        for case, (mut, imut, kw, expect) in cases.items():
            d = make(case, mut, imut)
            items = [os.path.join(d, "items_k8_v02_expl_%s.npz" % t) for t in ("t1", "t3")]
            recs = sorted(os.path.join(d, f) for f in os.listdir(d) if f.endswith(".json"))
            before = {p: (sha(p), os.path.getmtime(p)) for p in recs}
            arch = d + "_archive"
            try:
                b = V3.check_exploratory(d, ["t1", "t3"], ["decide", "loop"], items, kw.get("fits_paths", [FITS["t1"], FITS["t3"]]), T1_MANIFESTS,
                                         arch, kw.get("run_cwd", K8))
                got, msg = True, None
            except AssertionError as e:
                got, msg, b = False, str(e), None
            after = {p: (sha(p), os.path.getmtime(p)) for p in recs}
            arch_ok = os.path.isdir(arch) and all(os.path.exists(os.path.join(arch, os.path.basename(p))) and sha(os.path.join(arch, os.path.basename(p))) == before[p][0]
                                                  for p in recs if os.path.basename(p).startswith(("run_record_", "launch_record_")) or p.endswith(("_summary.json", "_launch.json")))
            r = {"accepted": got, "expected": expect, "ok": got == expect, "message": msg, "archived_before_checks": arch_ok, "originals_unchanged": before == after}
            if b is not None:
                r["relation"] = b["analysis_relation"]["relation"]
                r["fits_resolved"] = b["runs"]["t1_decide"]["fits_resolved"]
                r["fits_recorded"] = b["runs"]["t1_decide"]["fits_recorded"]
                r["archived_files"] = len(b["archive"]["files"])
            res[case] = r
        # archive behaviour: a second read archives nothing new; a changed record (a re-merge) is kept beside the first copy
        d = os.path.join(base, "well_formed")
        arch = d + "_archive"
        a2 = V3.archive_records(V3.records_to_archive(d, ["t1", "t3"], ["decide", "loop"]), arch)
        rp = os.path.join(d, "run_record_t1_decide.json")
        txt = open(rp).read()
        open(rp, "w").write(txt.replace('"synthetic": true', '"synthetic": true, "re_merged": true'))
        a3 = V3.archive_records([rp], arch)
        res["archive_second_read"] = {"all_identical": all(e["status"].startswith("already archived") for e in a2["files"]),
                                      "changed_record_kept_beside": a3["files"][0]["status"].startswith("copied beside")
                                      and os.path.exists(os.path.join(arch, "run_record_t1_decide.json")) and os.path.exists(a3["files"][0]["archived"]),
                                      "log_lines": sum(1 for _ in open(os.path.join(arch, "ARCHIVE_LOG.jsonl")))}
        # --archive-only on a run directory whose t3_loop run did not finish: the records that exist are archived, nothing is checked
        d = make("archive_only_failed_run")
        os.remove(os.path.join(d, "run_record_t3_loop.json"))
        arch = d + "_archive"
        items = [os.path.join(d, "items_k8_v02_expl_%s.npz" % t) for t in ("t1", "t3")]
        saved = (V3.DEV_SCENES, V3.STRICT_Q, V3.STAMP, A.MIN_SCENES, A.MIN_LOGS)
        try:
            V3.main(["--runs", d, "--tags", "t1", "t3", "--manifests", *T1_MANIFESTS, "--out", os.path.join(d, "unused.json"), "--exploratory",
                     "--fits", FITS["t1"], FITS["t3"], "--items", *items, "--archive-dir", arch, "--archive-only"])
            err = None
        except BaseException as e:   # noqa: BLE001
            err = repr(e)
        finally:
            V3.DEV_SCENES, V3.STRICT_Q, V3.STAMP, A.MIN_SCENES, A.MIN_LOGS = saved
        expect = sorted(f for f in os.listdir(d) if f.endswith(".json"))
        res["archive_only_failed_run"] = {"error": err, "archived": sorted(f for f in os.listdir(arch) if f.endswith(".json")) == expect,
                                          "files": len(expect), "no_output": not os.path.exists(os.path.join(d, "unused.json"))}
    finally:
        os.chdir(old_cwd)
    wf = res["well_formed"]
    res["pass"] = bool(all(v["ok"] and v["archived_before_checks"] and v["originals_unchanged"] for k, v in res.items() if isinstance(v, dict) and "ok" in v)
                       and wf.get("relation") == V3.RELATION and os.path.normcase(wf.get("fits_resolved", "")) == os.path.normcase(os.path.normpath(FITS["t1"]))
                       and wf.get("fits_recorded") == FITS_REL["t1"] and all(res["archive_second_read"][k] for k in ("all_identical", "changed_record_kept_beside"))
                       and res["archive_second_read"]["log_lines"] == 3
                       and res["archive_only_failed_run"]["error"] is None and res["archive_only_failed_run"]["archived"]
                       and res["archive_only_failed_run"]["files"] == 11 and res["archive_only_failed_run"]["no_output"])
    return res


# ---------------------------------------------------------------- (e) checkpoint recovery

def child_inject_abort(argv):
    """Child process: v03's main with an abort injected at the second analyse_loop call (t3_loop)."""
    calls = {"n": 0}
    orig = V3.analyse_loop

    def bad(*a, **k):
        calls["n"] += 1
        if calls["n"] == 2:
            raise RuntimeError("INJECTED ABORT in the second loop analysis (t3_loop), test (e)")
        return orig(*a, **k)
    V3.analyse_loop = bad
    try:
        V3.main(argv)
    except RuntimeError as e:
        print("INJECTED ABORT: %s" % e, flush=True)
        sys.exit(3)
    sys.exit(0)


def part_e():
    d = os.path.join(SCR, "e_checkpoints")
    if os.path.exists(d):
        shutil.rmtree(safe_out(d))
    os.makedirs(d)
    out_json, csv_dir = os.path.join(d, "k8_dev_analysis_v03_e.json"), os.path.join(d, "csv")
    ck = os.path.join(d, "k8_dev_analysis_v03_e_checkpoints")
    argv = dev_argv(out_json, csv_dir)
    t0 = time.time()
    p = subprocess.run([sys.executable, "-B", os.path.abspath(__file__), "--child-inject-abort", json.dumps(argv)], cwd=K8, capture_output=True, text=True, env=ENV)
    open(os.path.join(d, "run_e1_abort.log"), "w", encoding="utf-8").write(p.stdout + "\n--- stderr ---\n" + p.stderr)
    res = {"abort_run": {"returncode": p.returncode, "seconds": round(time.time() - t0, 1), "injected": "INJECTED ABORT" in p.stdout}}
    on_disk = {tm: os.path.exists(os.path.join(ck, tm + ".json")) for tm in ("t1_decide", "t1_loop", "t3_decide", "t3_loop")}
    complete = {tm: json.load(open(os.path.join(ck, tm + ".json"))).get("complete") is True for tm, x in on_disk.items() if x}
    res["after_abort"] = {"checkpoints_on_disk": on_disk, "complete": complete, "final_json_absent": not os.path.exists(out_json)}
    # a checkpoint with another key, or whose CSV changed, is not reused
    ckp = os.path.join(ck, "t1_decide.json")
    meta = json.load(open(ckp))
    res["refuse_other_key"] = V3.load_checkpoint(ckp, "0" * 64) is None
    alt = os.path.join(d, "t1_decide_csv_changed.json")
    m2 = dict(meta)
    first = sorted(m2["csv_sha256"])[0]
    m2["csv_sha256"] = dict(m2["csv_sha256"], **{first: "0" * 64})
    json.dump(m2, open(alt, "w"))
    res["refuse_changed_csv"] = V3.load_checkpoint(alt, meta["key_sha256"]) is None
    res["accept_own_key"] = V3.load_checkpoint(ckp, meta["key_sha256"]) is not None
    os.remove(alt)
    p2, dt = run_v03(argv + ["--resume"], os.path.join(d, "run_e2_resume.log"))
    res["resume_run"] = {"returncode": p2.returncode, "seconds": dt, "done": "K8 ANALYSIS V03 DONE" in p2.stdout}
    if p2.returncode != 0:
        res["resume_run"]["stderr_tail"] = p2.stderr[-3000:]
        res["pass"] = False
        return res
    je = json.load(open(out_json))
    res["reused"] = {k: v["reused"] for k, v in je["checkpoints"].items()}
    ja = json.load(open(A_JSON))
    acc = new_acc()
    walk({k: v for k, v in ja.items() if k != "checkpoints"}, {k: v for k, v in je.items() if k != "checkpoints"}, "", acc)
    res["final_json_equals_a"] = {"numbers_compared": acc["numbers"], "differences": len(acc["numeric_mismatch"]) + len(acc["value_mismatch"]) + len(acc["string_changes"])
                                  + len(acc["added"]) + len(acc["removed"]) + len(acc["list_len"]) + len(acc["type"]),
                                  "examples": (acc["numeric_mismatch"] + acc["string_changes"] + acc["added"] + acc["removed"])[:10]}
    same_csv = {fn: sha(os.path.join(csv_dir, fn)) == sha(os.path.join(A_CSV, fn)) for fn in sorted(os.listdir(A_CSV))}
    res["csv_equal_a"] = {"files": len(same_csv), "all_equal": all(same_csv.values()) and sorted(os.listdir(csv_dir)) == sorted(os.listdir(A_CSV)),
                          "differ": [k for k, v in same_csv.items() if not v]}
    res["pass"] = bool(p.returncode == 3 and res["abort_run"]["injected"] and on_disk == {"t1_decide": True, "t1_loop": True, "t3_decide": True, "t3_loop": False}
                       and all(complete.values()) and res["after_abort"]["final_json_absent"] and res["refuse_other_key"] and res["refuse_changed_csv"]
                       and res["accept_own_key"] and res["reused"] == {"t1_decide": True, "t1_loop": True, "t3_decide": True, "t3_loop": False}
                       and res["final_json_equals_a"]["differences"] == 0 and res["csv_equal_a"]["all_equal"])
    return res


# ---------------------------------------------------------------- (f) T4 as counts (R15b n2)

def part_f():
    pd7 = A.mask(**V3.POP_DECIDE["PD7_primary"])
    res = {}
    for tag in ("t1", "t3"):
        eps = [json.loads(l) for l in open(os.path.join(DEV_RUNS, "episodes_%s_decide.jsonl" % tag))]
        cnt = np.load(os.path.join(DEV_RUNS, "counts_%s_decide.npz" % tag))
        dec = np.load(os.path.join(DEV_RUNS, "decisions_%s_decide.npz" % tag))
        arm_of = {o["episode"]: o["arm"] for o in eps if o["entered"]}
        ea_c = np.array([arm_of.get(int(e), "") for e in cnt["episode"]])
        ea_d = np.array([arm_of.get(int(e), "") for e in dec["episode"]])
        m = pd7[cnt["cell"]]
        curve = sorted(S.SWEEP_ARMS, key=lambda a_: (S.CURVE_ALPHA_OF_ARM[a_], a_))
        rows = []
        for a_ in curve:
            sel = m & (ea_c == a_)
            inf_ep = sum(o["infeasible_frames"] for o in eps if o["entered"] and o["arm"] == a_)
            inf_dec = int(dec["infeasible"][ea_d == a_].sum())
            rows.append({"arm": a_, "alpha_eq": S.CURVE_ALPHA_OF_ARM[a_], "X": int(cnt["exceed"][sel].sum()), "N": int(cnt["n"][sel].sum()),
                         "infeasible_decisions": inf_ep, "infeasible_decisions_from_rows": inf_dec,
                         "decisions": sum(o["frames"] for o in eps if o["entered"] and o["arm"] == a_)})
        X = [r["X"] for r in rows]
        I = [r["infeasible_decisions"] for r in rows]
        rate = [r["X"] / max(r["N"], 1) for r in rows]
        res[tag] = {"curve": rows,
                    "X_nonincreasing_no_tolerance": all(b <= a for a, b in zip(X, X[1:])),
                    "infeasible_nondecreasing_no_tolerance": all(b >= a for a, b in zip(I, I[1:])),
                    "infeasible_rows_equal_episode_counts": all(r["infeasible_decisions"] == r["infeasible_decisions_from_rows"] for r in rows),
                    "decisions_equal_across_arms": len({r["decisions"] for r in rows}) == 1,
                    "rate_upward_steps_v02_form": [(rows[i]["arm"], rows[i + 1]["arm"], rate[i + 1] - rate[i]) for i in range(len(rows) - 1) if rate[i + 1] > rate[i]],
                    "note": "counts, not rates: the decisions are the same for every arm (decision mode), so the infeasible count is the rate's "
                            "numerator over a common denominator; X is the PD7 exceedance count, whose rate's denominator N the margin "
                            "itself selects (R15b section 3 (5))"}
        res[tag]["pass"] = bool(res[tag]["X_nonincreasing_no_tolerance"] and res[tag]["infeasible_nondecreasing_no_tolerance"]
                                and res[tag]["infeasible_rows_equal_episode_counts"] and res[tag]["decisions_equal_across_arms"])
    res["pass"] = bool(res["t1"]["pass"] and res["t3"]["pass"])
    return res


def main():
    if "--child-inject-abort" in sys.argv:
        child_inject_abort(json.loads(sys.argv[sys.argv.index("--child-inject-abort") + 1]))
        return
    out_json = sys.argv[1]
    parts = sys.argv[sys.argv.index("--parts") + 1] if "--parts" in sys.argv else "abcdef"
    reuse = "--reuse" in sys.argv
    os.makedirs(SCR, exist_ok=True)
    safe_out(out_json)
    arch_existed = os.path.exists(V3.ARCHIVE_DEFAULT)
    prot0 = {p: sha(p) for p in PROTECTED}
    res = {"note": "development outputs and synthetic records only; see the module docstring", "v03_sha256": sha(V3_PATH),
           "v02_analysis_sha256": sha(V3.V02_CODE_FILES["analysis"]), "started": time.strftime("%Y-%m-%d %H:%M:%S"), "parts": parts}
    t_all = time.time()
    for k, fn in (("f", part_f), ("c", part_c), ("d", part_d), ("a", lambda: part_a(reuse)), ("e", part_e), ("b", lambda: part_b(reuse))):
        if k not in parts:
            continue
        t0 = time.time()
        print("part %s ..." % k, flush=True)
        try:
            res[k] = fn()
        except Exception as e:  # noqa: BLE001 (a crash is a test result)
            import traceback
            res[k] = {"pass": False, "crash": repr(e), "traceback": traceback.format_exc()[-4000:]}
        res[k]["seconds"] = round(time.time() - t0, 1)
        print("part %s: %s (%.0f s)" % (k, "PASS" if res[k].get("pass") else "FAIL", res[k]["seconds"]), flush=True)
        json.dump(res, open(out_json, "w"), indent=1, default=str)
    prot1 = {p: sha(p) for p in PROTECTED}
    res["protected_files_unchanged"] = prot0 == prot1
    res["protected_files"] = {os.path.relpath(p, W_ROOT): h[:12] for p, h in prot1.items()}
    res["real_archive_untouched"] = os.path.exists(V3.ARCHIVE_DEFAULT) == arch_existed
    res["seconds"] = round(time.time() - t_all, 1)
    res["verdict"] = "ALL_PASS" if all(res[k].get("pass") for k in parts) and res["protected_files_unchanged"] and res["real_archive_untouched"] \
        else "FAIL: " + ", ".join(k for k in parts if not res[k].get("pass"))
    json.dump(res, open(out_json, "w"), indent=1, default=str)
    print(res["verdict"])


if __name__ == "__main__":
    main()
