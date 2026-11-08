#!/usr/bin/env python3
"""X3 core report, round 2 (x3-core agent, x3_core_report_r2_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict
of record; not part of the registered test). Writes 70_TESTS/X3_INTEGRITY_v01/X3_CORE_REPORT_R2_v01.md and X3_CORE_FILES_R2_v01.txt
(every round-2 file of the x3-core agent with its sha256).
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import x3_common_v01 as C  # noqa: E402

CODE = ["x3_run_v02.py", "x3_fits_r2_v01.py", "x3_analysis_r2_v01.py", "x3_chain_r2_v01.py", "x3_core_report_r2_v01.py"]
CHOICES = """
1. **Runner v02** (`x3_run_v02.py`; `x3_run_v01.py` is unchanged): the covariance substitution follows x3-ref's interface (assert
   `sc.tr["k"] == z["tr_k"]`, copy, `[:, :, 2:5] = pred_cov`) and accepts `"self"` (the cache's own covariance) for the neutrality
   check; margin rule B7 (see 4). Everything else is v01 (variants, `_record` partition wrapper, shards, merge layout).
2. **Checks before any screen (all passed, T1 and T3, 375 logs, exact):** (d) `fits_x3ref_d0_*` drive arm Mstar to the run of record
   (decisions, counts, calibration tables, episode summaries; `x3_gates_v01.v0`); (e2) B0 on the cache's own covariance equals B0 of
   record; (e1) the runner's B7 margins equal the fit's item-level margins c exp(phi beta) sd on every item of three logs (max relative
   difference 1.3e-15 / 1.5e-15); (g) n = 300 reproduces `Mstar_ip` and `Mstar_ip_src` of record exactly.
3. **Comparison with M\* of record:** every arm judged like RETUNED-HK1 of record (labels outside K: flags at 0.95, power datasets 500),
   B = 4000, seeds [20261201, i, j] / [20261202, i, j] with j = 4 (d), 5 (e1, e2), 7 (g); power-key suffix [100 + code] (e1 arms
   codes 10-12, distinct from e2's 0-2); M* of record (the X3 core run, equal to the record by V0) screened with the same seeds as the
   reference row; infeasible rate with its 95 % log-bootstrap interval; M* - arm per-log paired, percentile 95 % interval; pooled
   relied-item exceedance per population.
4. **(e1) ports of m_lib_v04.fit_methods** (exact CRC as every CRC of record; per step and in-path part as M\*; delta 0.05, n_min 19):
   B5 = `fit_hier(start = 3)` (one CRC threshold per axis); B8 = `fit_hier(start = 0, stat = z_0.95 sqrt(mean U^2))` with its L1-L3
   fallback; B5 and B8 run through k8_sim_v04's own per-(L0, in-path) threshold x sd form (base arm Mstar, key `Mstar_ip`). B7: the
   calibration logs permuted by `default_rng([20261201, i, 5])` (m_lib_v04 re-creates one fixed-seed generator per fit; the same seed
   for every fold), first half -> least squares of log(max(|U|, 0.05)) on phi's 17 columns, second half -> CRC of U / exp(phi beta);
   per step and in-path part. **Inputs our items lack:** phi needs the track speed (`spd`) and the heading rate (`_om_used` = `omc`,
   course over ground); the items of record do not carry them. They are read from the stage-B cache at each item's track row (item ->
   record by (log, pair) -> `rec_row` -> `tr_spd`, `tr_omc`); the motion state re-derived from them equals every item's `m`. In the
   run, `k8_sim_v04.strata` / `margins` are wrapped in-process so the B7 variant's margin is c[h, ip] exp(phi beta[h, ip]) sd from the
   same quantities (the base arm is Mstar; its calibration-table covariance is the generic D S' D of margin / sd).
5. **(g):** subsample = first n of `default_rng([20261207, n, r, f]).permutation(sorted training logs)`; M\*'s fit rule
   (`split_fit_exact`, start 0). A subsample whose fit leaves a threshold undefined (no level with 19 logs; this happens in the in-path
   part) is not fittable and is not run: n = 25, T1 repeats 0 and 2, T3 all three. The fallback share = share of the 192 x 4
   thresholds whose source level is coarser than the own L0 stratum, mean over the five folds.
6. **(e2):** both arms of amendment A2 were run: plan grid (`subst_<t>`) and extended grid (`subst_ext_<t>`, q = 0 allowed), x3-ref's
   substitution files unchanged (manifests hash-recorded in the run records).
7. **Heavy lock:** the whole round ran under one lock (`x3_chain_r2_v01`, 13:33-14:03), integrity checked (full) at its start and end and
   (run log) after every run.
"""


def main():
    st = json.load(open(os.path.join(C.OUT, "runs", "logs", "chain_r2_status_v01.json")))
    integ = [json.loads(l) for l in open(os.path.join(C.INTEG, "x3_core_integrity_log_v01.jsonl"))]
    rr = {}
    for tag in ("d_t1", "d_t3", "e2_t1", "e2_t3", "e1_t1", "e1_t3", "g_t1", "g_t3"):
        r = json.load(open(os.path.join(C.OUT, "runs", "run_record_%s.json" % tag)))
        rr[tag] = (len(r["variants"]), r["episodes"], r["seconds"], r["scene_seconds_sum"])
    L = ["# X3 core report, round 2: analyses (d), (e2), (e1), (g)", "", "**%s**" % C.STAMP, "",
         "Plan sections 2(d), 2(e), 2(g) and amendment A2. Outputs: 60_RESULTS/x3_explore_v01/{d_ref_runs, e_alternatives, g_learning} "
         "(JSON and MD each); runs in 60_RESULTS/x3_explore_v01/runs (tags d_, e2_, e1_, g_<t>).", "",
         "Chain steps: %s." % json.dumps(st["steps"]), "", "## Choices and checks", CHOICES, "## Timings", "",
         "| run | variants | episodes | wall s | worker s |", "|---|---|---|---|---|"]
    for tag, (nv, ne, s, ws) in rr.items():
        L.append("| %s | %d | %d | %.0f | %.0f |" % (tag, nv, ne, s, ws))
    L += ["", "Whole round (one lock): %.0f s." % st["seconds"], "", "## Integrity (round 2)", "", "| time | event | run log | manifest |", "|---|---|---|---|"]
    for e in integ:
        if e["t"] >= "2026-11-07 13:30":
            L.append("| %s | %s | %s | %s |" % (e["t"], e["event"], e.get("run_log_ok"), e.get("manifest_ok", "(quick)")))
    files = [os.path.join(C.W, "50_CODE", "x3", f) for f in CODE]
    for d in ("d_ref_runs", "e_alternatives", "g_learning"):
        files += sorted(p for p in glob.glob(os.path.join(C.OUT, d, "**", "*"), recursive=True) if os.path.isfile(p))
    for tag in rr:
        files += sorted(glob.glob(os.path.join(C.OUT, "runs", "*_%s.*" % tag)))
        files += [os.path.join(C.OUT, "runs", "specs", "spec_%s_v01.json" % tag)]
    files += [os.path.join(C.OUT, "runs", "logs", "chain_r2_v01.log"), os.path.join(C.OUT, "runs", "logs", "chain_r2_status_v01.json")]
    lines = ["%s  %s" % (C.sha256(p), os.path.relpath(p, C.W).replace("\\", "/")) for p in files]
    C.wtext(os.path.join(C.INTEG, "X3_CORE_FILES_R2_v01.txt"), "# " + C.STAMP + " -- round-2 files of the x3-core agent (sha256, path)\n" + "\n".join(lines) + "\n")
    L += ["", "## Files", "", "Every round-2 file with its sha256: 70_TESTS/X3_INTEGRITY_v01/X3_CORE_FILES_R2_v01.txt (%d files; shards excluded)." % len(lines), ""]
    C.wtext(os.path.join(C.INTEG, "X3_CORE_REPORT_R2_v01.md"), "\n".join(L))
    print("round-2 report written; %d files" % len(lines))


if __name__ == "__main__":
    main()
