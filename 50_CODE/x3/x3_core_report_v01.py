#!/usr/bin/env python3
"""X3 core report (x3-core agent, x3_core_report_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record;
not part of the registered test). Writes 70_TESTS/X3_INTEGRITY_v01/X3_CORE_REPORT_v01.md and X3_CORE_FILES_v01.txt (every file the
x3-core agent wrote, with its sha256) from the outputs; the choices section is the text below (CHOICES).
Usage: python -B x3_core_report_v01.py
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_common_v01 as C  # noqa: E402

MINE_CODE = ["x3_common_v01.py", "x3_run_v01.py", "x3_gates_v01.py", "x3_fits_v01.py", "x3_screen_v01.py", "x3_analysis_a_v01.py",
             "x3_analysis_b_v01.py", "x3_gates_report_v01.py", "x3_integrity_v01.py", "x3_core_report_v01.py", "x3_chain_v01.py"]
CHOICES = """
1. **Screen as coded and installed for the record.** `c1_rules_v02.apply_analysis` (as `c1_analyse_v10` does at import) installs
   `hk1_rule_criteria` as `k8_analyse_v04.hk1_rule`; `c1_analyse_v02.configure("c1")` and `configure_v09` set 39 units / 8 logs and
   `STRICT_Q = False`; status = `c1_analyse_v02.arm_status`. The flag level follows the arm label as of record: the comparators of K
   (B0, B1, B3, B4, B6, B9, RETUNED) at 1 - 0.0125/9, every other label (M*, sweep points, RETUNED-HK1, joint arms, Z0) at 0.95.
   X3 grid points and composites carry labels outside K, so they are judged like RETUNED-HK1 and the sweep points of record (0.95,
   power datasets 500): "matched validity" = M*'s own standard. `c1_analyse_v10` itself is not imported (it imports the guard
   modules); the same three installs are made in-process.
2. **V1 seeds and B.** The record's seeds (`c1_analyse_v02.seeds(i, 0)`: [20261110, i, 0], [20261111, i, 0]; i = 0 T1, 1 T3, 2 tab)
   and the record's power-key suffixes ([100 + ARM_INDEX], [300] for RETUNED-HK1, [200 + ARM_INDEX, f] in its selection). With
   B = 4000 the weights are the first 4000 rows of the record's 40000 (numpy's multinomial draws rows in order), so the power
   families (first 500 rows) are the record's and only the flag and bound quantiles carry Monte Carlo error. RETUNED (A3) is rebuilt
   from the record's `arm_of_scene` (`k8_analyse_v04.add_composite_arm`); RETUNED-HK1 from the record's per-fold choice, and its
   selection is re-run at B = 4000 as a check of the X3 selection code. V1 covers T1, T3 and tab (tab descriptive).
3. **V1 yardstick.** A disagreement is acceptable if every differing component's decisive statistic is within 3 MC SE of its
   threshold; MC SE at B = 4000 = max(R21 step 3's empirical MC SE at B = 40000 x sqrt(10), where R21 measured the quantity; X3's own
   order-statistic MC SE of the bound). Evaluable counts, family sizes and floors are deterministic here and never acceptable.
4. **Runner.** Variants run per scene through `k8_sim_v04.run_decisions` with the variant's fits (`fits[fold][step]`, the record's
   layout); arm relabelled; `c1_run_v02._scene_job`'s record layout and merge order reproduced in `x3_run_v01` (c1_run_v02 is not
   imported: its scene job reads a module-global fits dict and cannot relabel). Fold from `C1_FOLDS_375_v01` (asserted equal to every
   fits file's `fold_of_scene`). Cache files checked against their manifest hashes. 3 workers, per-scene atomic shards, `--resume`.
5. **Partition wrapper.** `k8_sim_v04._record` is replaced in the worker processes by a wrapper that calls the frozen function
   unchanged and then recomputes its locals for the relied records; at every call the recomputed per-cell (near x in-path) record and
   exceedance counts are asserted equal to `_record`'s own `st` (78,484 calls on T1 alone; no failure).
6. **Partition definitions where the plan is silent.** Track age = k - (first keyframe of the tr_tid in the log) + 1. Ego speed =
   `max(v_log(t_k), 0)`, `run_decisions`' own value (= the DEC field v_now). Lidar points = `gt_pts` of the matched annotation row at
   k + h. Distance to the ego = the range stratum r of the record's L0 (< 20, 20-40, >= 40 m, the CTRV ego centre distance M*'s strata
   use). A detection score below 0.4 gets its own bin and a non-finite value a "missing" bin (both reported; see the (b) JSON).
   **City (P7) is available**: from the AV2 map file names `log_map_archive_<log>____<CITY>_city_*.json` listed in the local map
   manifests (30_DATA/av2_det_owncp_v01/env, .../pilot/env, 30_DATA/av2_det_v01/voxelnext); 850 logs, all 375 C1 logs covered
   (MIA, PIT, WDC, DTW, ATX, PAO).
7. **(a) refits.** `split_fit_exact` and `fit_hier_exact` take no delta, so `x3_fits_v01` calls `m_lib_v04.fit_hier` with
   `stat = crc_threshold_exact(., ., delta=delta')` in `split_fit_exact`'s two-part loop; `n_min = ceil(1/delta') - 1` in exact
   rational arithmetic (19, 24, 33, 49, 66, 99, 199, 399, 999). delta' = 0.05 reproduces the fits of record exactly (B4, B6, B6_ip,
   B9; 5 folds x 8 steps, both trackers). **delta' = 0.0025 and 0.001 are not fittable** by the frozen rule: each training split
   has 300 logs, and `crc_threshold_exact` returns no threshold when 1/(n + 1) > delta' (n >= 399 and 999 needed); `fit_hier` leaves
   every stratum undefined. They are reported as not fittable and not run; the most conservative fittable point is delta' = 0.005.
8. **(a) runs and keys.** delta' = 0.05 is taken from the X3 core run (V0: equal to the record). Power-key suffixes: in-sample
   [100 + code], selection [200 + code, f], composite [300 + family index], code = 10 x family index (B4 0, B6 1, B9 2) + grid index.
   M*'s rates from the core run (equal to the record's by V0). The B0 family is reported from the record (RETUNED-HK1).
9. **(b).** Flags at 0.95 for every arm (the plan's rule), `k6_analyse_v02.flag` over the evaluable cells of each partition and
   population, evaluability by `k6_analyse_v02.evaluable` (>= 39 logs; units are logs). Non-evaluable cells with an estimate above
   delta carry a marginal one-sided 95 % percentile interval, labelled as such.
10. **Heavy lock.** Every decision-mode run, refit and B >= 2000 screen ran inside `x3_heavylock_v01.heavy_lock` (shared with the
    other X3 agents; waits recorded in 60_RESULTS/x3_explore_v01/HEAVY_LOCK_HISTORY.jsonl).
"""


def files_written():
    out = []
    for f in MINE_CODE:
        p = os.path.join(C.W, "50_CODE", "x3", f)
        if os.path.exists(p):
            out.append(p)
    for sub in ("gates", "a_matched", "b_partitions", "runs", "smoke"):
        for p in sorted(glob.glob(os.path.join(C.OUT, sub, "**", "*"), recursive=True)):
            if os.path.isfile(p) and "shards_" not in p:
                out.append(p)
    for p in (os.path.join(C.INTEG, "x3_core_integrity_log_v01.jsonl"), os.path.join(C.INTEG, "X3_CORE_REPORT_v01.md")):
        if os.path.exists(p):
            out.append(p)
    return out


def shard_counts():
    return {os.path.basename(d): len(glob.glob(os.path.join(d, "*.npz"))) for d in sorted(glob.glob(os.path.join(C.OUT, "*", "shards_*")))}


def main():
    g = json.load(open(os.path.join(C.OUT, "gates", "x3_gates_v01.json")))
    a = json.load(open(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json"))) if os.path.exists(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json")) else None
    b = json.load(open(os.path.join(C.OUT, "b_partitions", "x3_b_partitions_v01.json"))) if os.path.exists(os.path.join(C.OUT, "b_partitions", "x3_b_partitions_v01.json")) else None
    integ = [json.loads(l) for l in open(os.path.join(C.INTEG, "x3_core_integrity_log_v01.jsonl"))]
    rr = {}
    for p in sorted(glob.glob(os.path.join(C.OUT, "runs", "run_record_*.json"))):
        r = json.load(open(p))
        rr[r["tag"]] = {"seconds": r["seconds"], "scene_seconds_sum": r["scene_seconds_sum"], "variants": len(r["variants"]), "episodes": r["episodes"],
                        "partition_checks": r.get("partition_checks")}
    L = ["# X3 core report (x3-core agent)", "", "**%s**" % C.STAMP, "",
         "Plan: 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md (sha256 %s), sections 0, 1, 2(a), 2(b). Code: 50_CODE/x3/; outputs: "
         "60_RESULTS/x3_explore_v01/{gates, a_matched, b_partitions, runs}." % C.PLAN_SHA, "",
         "## Gates", "", "- V0 (runner reproduces the record exactly; M*, B0, B4, B6, B9 on T1 and T3; B1, B3 and tab M* also compared): **%s**" % g["V0_ok"],
         "- V2 (partition sums = counts of record per arm, population, log): **%s**" % g["V2_ok"],
         "- V1 (screen at B = 4000 vs statuses of record): **%s** (details in gates/x3_gates_v01.md)" % g["V1_ok"],
         "- Overall: **%s**" % ("PASSED" if g["passed"] else "FAILED"), "",
         "V1 detail: status (Valid, shown above, removal) agrees for %s arms of record. The one status disagreement is T1's sweep point "
         "B0a4 (X3 not Valid: PD_inpath car|lat|turning flagged, LB - delta = +0.0012, 0.92 MC SE; record Valid), within the rule. "
         "Component-only differences (statuses unchanged) are listed in gates/x3_gates_v01.md; two exceed 3 MC SE on the R21-scaled "
         "yardstick (T1 B9 PD7 large|long|new z 3.09; T3 B4 SD1_7 large|long|straight z 9.18) but are 1.15 and 0.56 MC SE on X3's own "
         "MC SE of that exact cell (R21 measured each comparator's largest removal statistic, a different cell); they change no status "
         "and do not gate. RETUNED-HK1's composite status agrees on all three trackers; its selection, re-run at B = 4000 on T1 (105 "
         "training screens), reproduces the record's choice (B0a8, none qualifies, every fold). Infeasible rates recomputed from the "
         "outputs of record equal the record's." % ", ".join("%s %d/%d" % (t, sum(1 for v in per.values() if v.get("status_agree")), len(per))
                                                             for t, per in g["V1_judged"].items()), "",
         "## Choices (where the plan is silent or the code needed a decision)", CHOICES, "## Timings", "",
         "| run | variants | episodes | wall s | worker s | partition checks |", "|---|---|---|---|---|---|"]
    for t, r in rr.items():
        L.append("| %s | %s | %s | %s | %.0f | %s |" % (t, r["variants"], r["episodes"], r["seconds"], r["scene_seconds_sum"] or 0, r["partition_checks"]))
    L += ["", "One hk1_rule call at B = 4000 on 375 logs: %s s; selection B: %s." % (g["timing"], g["B_selection"])]
    if a:
        L.append("Analysis (a) screen: %s s; (b) screen: %s s." % (a.get("seconds"), (b or {}).get("seconds")))
    L += ["", "Shards (per-scene, resumable): %s" % json.dumps(shard_counts()), "", "## Integrity checks", "",
          "| time | event | run log | manifest of 60_RESULTS/c1_av2_v01 |", "|---|---|---|---|"]
    for e in integ:
        L.append("| %s | %s | %s | %s |" % (e["t"], e["event"], e.get("run_log_ok"), e.get("manifest_ok", e.get("ok")) if "manifest" in e or "details" in e else "(quick)"))
    L += ["", "Every X3 script also asserts the run log's sha256 at its start and end (x3_common_v01.assert_run_log).", ""]
    files = files_written()
    lines = ["%s  %s" % (C.sha256(p), os.path.relpath(p, C.W).replace("\\", "/")) for p in files if not p.endswith("X3_CORE_REPORT_v01.md")]
    C.wtext(os.path.join(C.INTEG, "X3_CORE_FILES_v01.txt"),
            "# " + C.STAMP + " -- files written by the x3-core agent (sha256, path relative to W)\n" + "\n".join(lines) + "\n")
    L += ["## Files written", "", "Every file with its sha256: 70_TESTS/X3_INTEGRITY_v01/X3_CORE_FILES_v01.txt (%d files; shards excluded)." % len(lines), ""]
    C.wtext(os.path.join(C.INTEG, "X3_CORE_REPORT_v01.md"), "\n".join(L))
    print("report written; %d files listed" % len(lines))


if __name__ == "__main__":
    main()
