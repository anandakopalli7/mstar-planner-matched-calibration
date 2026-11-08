# R21 test on the rehearsal stand-in v01 (7 Nov 2026, 05:51–06:25 local)

**What was tested.** R21's code on the nuScenes rehearsal stand-in `70_TESTS/c1_v01/rehearsal150_v10/` (150 nuScenes validation scenes as "AV2" units, produced by code v10; its decision `c1_decision_rehearsal_v09.json` and analysis `c1_analysis_rehearsal_v09.json`, B = 40000), and the run-log checker on the AV2-tagged stand-in run log of `70_TESTS/c1_v01/tests_v13/tree/`. **No AV2 file was opened, listed or hashed; no tool of `50_CODE/c1_av2` or any driver was run.** Stand-in verdicts are not evidence. Everything ran single-threaded under `50_CODE/env/canmot310` (Python 3.10.22, NumPy 1.26.4, the analysis's versions), with B ≤ 2000, ≤ 500 power datasets, a 600 MB memory guard, each step under 2 minutes. **Outputs of record: `rehearsal_test/final/`** (06:27–06:30, the final code of `RUN_REAL_v01.txt`; every count below is from these and equals the earlier runs kept in `rehearsal_test/`, made before the output-folder change).

## 1. Commands (from `70_TESTS/R21_c1_v01`, `PY=../../50_CODE/env/canmot310/Scripts/python.exe`, `R=../c1_v01/rehearsal150_v10`)

```
$PY -B r21_rederive_v01.py --config $R/config.json --analysis $R/c1_analysis_rehearsal_v09.json --decision $R/c1_decision_rehearsal_v09.json
    --csv-dir $R/csv --out rehearsal_test/r21_rederive_rehearsal_B2000.json --md rehearsal_test/r21_rederive_rehearsal_B2000.md
    --B 2000 --power-datasets 500 --routes within_lt3d,transfer_lt3d --k8-routes within_lt3d,transfer_lt3d --k8-trackers t1,t3,tab --max-mem-mb 600
$PY -B r21_mcse_v01.py --config $R/config.json --analysis $R/c1_analysis_rehearsal_v09.json --ckpt-dir rehearsal_test/mc_fixed_ckpt
    --out rehearsal_test/r21_mcse_rehearsal_fixed.json --md rehearsal_test/r21_mcse_rehearsal_fixed.md --sets 2 --B 500 --power fixed --ref-power-datasets 200 --max-mem-mb 600
$PY -B r21_mcse_v01.py ... --ckpt-dir rehearsal_test/mc_recompute_ckpt --sets 2 --B 500 --power recompute --power-datasets 100 --ref-power-datasets 100 --routes within_lt3d --lowmem --max-mem-mb 600
    (run twice: the second call found every checkpoint and recomputed nothing: the resume test)
python -B r21_runlog_check_v01.py --run-log <tree>/40_PROTOCOL/C1_RUN_LOG.txt --decision <tree>/70_TESTS/dec1.json --analysis <tree>/70_TESTS/an1.json
    --config <tree>/30_DATA/fx_config.json --root <tree> --plan <tree>/70_TESTS/PLAN_2.md --out rehearsal_test/runlog_standin_dec1.json --md ...
    (also dec2/an2; and two damaged copies of the log written in rehearsal_test/: one byte changed in line 3, the last 40 bytes cut)
$PY -B rehearsal_test/r21_timing_probe_v01.py         $PY -B rehearsal_test/r21_borderline_recheck_v01.py
```

## 2. Runtime and peak memory

| Step | Runtime | Peak private / working set |
|---|---|---|
| `r21_rederive_v01` (4 route-trackers H1/H4, H2, H3; K8 tables for 7 route-trackers incl. `tab`), B = 2000 | 86 s wall (68 s compute) | 258 / 239 MB |
| `r21_mcse_v01` fixed, 2 sets + reference, 4 route-trackers, B = 500 | 42 s | 206 / 186 MB |
| `r21_mcse_v01` recompute (100 datasets), 2 sets, within route, `--lowmem` | 37 s | 204 / 185 MB |
| `r21_runlog_check_v01` (each run) | < 2 s | small |
| timing probe (U = 150 and U = 375 by tiling, B ≤ 2000) | 5 s | 104 MB |

## 3. Re-derivation against the rehearsal decision and analysis (B = 2000 against the analysis's 40000)

**94,533 comparisons: 94,455 agree, 58 MC-borderline, 20 info, 0 disagreements.** Non-K8 (H1 to H4 pieces): 2,184 (2,153 agree, 31 borderline). K8 tables (counts, validity, cells, trade-off, arms, margins, V2 and variants, V2_viol, for within and transfer, T1, T3 and AB3DMOT): 92,349 (92,302 agree, 27 borderline, 20 info).

- **Exact** on every count, membership and point estimate: records, exceedances, units and evaluable cells of every arm, population and cell; every Ê (max difference 2e-16); infeasible rates of all 32 arms; Δ means; V2 and its variants, the reference and the mean tracks; margins; RETUNED's arm of every fold (T1 B0a0.5, T3 B0d0.3, as the analysis); run-table hashes against the run records; seeds.
- **H1**: R21 NO-GO = decision NO-GO. M\*'s statuses equal the analysis's in all 6 tracker-populations (both trackers fail only the SD1_7 floor; HK1c UBs 0.043/0.042/0.050 on T1, 0.047/0.043/0.041 on T3); the exact floor comparison (analysis per-cell power ≥ 0.80) agrees in every population, and every analysis M\* family size equals its count of cells with power ≥ 0.80 (internal consistency, 12 of 12). H1 without zero-SE removals: no zero-SE removal on the stand-in (as the decision's `zero_se_effects`), so unchanged.
- **H2, H3, H4**: bound forms and p-values agree (H2 p 0.0005 at B = 2000 against 2.5e-5, the 1/(B + 1) floor; H3 V^J {B3} on T1, {B0, B3} on T3, p 0.042 against 0.048; H4 p = 1 because Valid(M\*) fails on the transfer route, p of the Form B part 0.49).
- **Family recovery** (design §7 item 2): 66 comparator families recovered uniquely from size and record share, 17 empty, 1 ambiguous (B1, T1, PD7: two subsets with the same record share), 12 M\* families from the per-cell power.

**The 58 MC-borderline rows, diagnosed:**
1. **V_t on within T1 (B6) and T3 (RETUNED)**, 8 rows with their consequences (removed list, \|V_t\|, Form B level): R21 removes each through one power-family cell flagged at 1 − 0.0125/9 with LB − δ = +0.0011 (B6) and +0.0035 (RETUNED). **Re-check (second way)**: the same flag under the registered seed and 5 other R21 seeds at B = 2000 is raised in 4 of 6 seeds for each (`borderline_recheck_v01.json`; LB − δ from −0.0035 to +0.0019 and from −0.0009 to +0.0035). At B = 2000 the removal quantile has about 3 replicates beyond it (56 at the plan's B = 40000), so this is MC at R21's test B, not a code difference. The 7 arm-population status rows behind them (FamFlag, family flagged, valid, shown_above) are the same two cases.
2. **Comparator cell flags at the removal level near δ** (B4 and RETUNED T1 PD7; B4 transfer T1 PD7; 5 rows): LB within tolerance of δ.
3. **B1 T1 PD7 family size** (2 rows): the ambiguous recovery above; R21's own family has 8 cells, the analysis's 7.
4. **M\*'s own-power family check** (6 rows): R21's 500-dataset power against the analysis's 2000; every per-cell power agrees within the power tolerance (154 of 154 cells), the families differ only in cells near 0.80. The floor itself is compared on the analysis's power (exact, agrees).
5. **K8 flags near the threshold** (27 rows): 16 cells at 0.95 and 11 validity flags (C1 level), sweep arms, Z0-like arms and comparators, all with LB within tolerance of δ.

**The 20 info rows**: the analysis's CSV leaves the estimate empty where an arm has no record (B0a8, T3, SD1_7) or an all-zero pooled cell (B0a5, T3, SD1_7); R21 lists them and compares nothing.

**Exact weight reproduction** cannot be tested on the stand-in (R21 at B = 2000, the analysis at 40000; largest bound difference 0.013, at H4's removal level, where B = 2000 has fewer than one replicate beyond the quantile). It becomes testable on AV2, where both run at 40000 with the registered seed.

**Fixes made during the test (all before any AV2 outcome; design §7):** the K8 validity table at each arm's C1 level; comparator families recovered from the analysis's size and record share; tolerances from the Andrews–Buchinsky MC SE; H3/H4 p = 1 when the validity gate fails; empty CSV fields as info. The first B = 2000 run, before these, showed 37 disagreements, all traced to these definitions (e.g. pooled LBs compared at 0.95 against the analysis's removal level); none remained.

## 4. Run-log checker on the stand-in tree

- `dec1` (13-line log): chain intact; the decision's `run_log_sha256` and `last_line_sha256` recompute exactly from the first 5 lines; the analysis's start line is line 5; its done line lists the decision and analysis JSON with their current hashes; the decision is the first completed analysis run. Problems found are real properties of the test tree: H8's table no longer has the SHA-256 its done line recorded (the tree also holds a later H8 start line without a done line; detected twice), and the tree's lines carry two plans and two deposit records (its tests use several).
- `dec2`: also flagged as **not** the first completed analysis run (the table of record would be dec1).
- Damaged copies: one byte changed in line 3 → chain error at line 4 and the decision's prefix hash fails; the last 40 bytes cut → chain error (cut last line).
- Not exercisable on the stand-in: run records' done lines (the tree has no route runs), the seven-string environment-stop scan on a real decision (the code path ran; no hit), the stage-B log.

## 5. Monte Carlo script

Both modes ran end to end on all requested route-trackers, wrote one checkpoint per (route, tracker, set), resumed without recomputation, and wrote the summary (MC SE empirical and Andrews–Buchinsky, stability shares, family-size changes, cells with \|t − q\| < 0.2, H1 by set). At B = 500 the removal-level statistics are not meaningful (under one replicate beyond the quantile), so the stand-in numbers test code paths only. `mc_fixed_ckpt_try1/` and `mc_recompute_ckpt_try1/` are superseded outputs of an earlier code state, kept.

## 6. Projection to AV2 (375 logs, B = 40000), from the timing probe

One arm-population bootstrap at U = 375: 9.6 ms at B = 1000, 12.6 ms at 2000, so about 0.15–0.25 s at 40000 with quantiles; one power dataset at U = 375: 5.0 ms. Hence: `r21_rederive_v01` about 10–20 min (power 500 datasets: about 1 min per route-tracker; K8 tables about 1 min per route-tracker); `r21_mcse_v01 --power fixed` about 20–40 s per set and route-tracker, about 30–60 min for 20 sets on 4 route-trackers; `--power recompute` with 2000 datasets adds about 4 min per set and route-tracker, about 5–6 h in all (resumable). Peak memory: weights 30 MB (int16) plus a 120 MB float64 cache (none with `--lowmem`), run tables about 150 MB while loading, the analysis JSON; estimated 0.5–0.8 GB for the re-derivation and 0.3–0.5 GB for the MC script.

## 7. Not covered, and why

- H6a, H6b, H7, H8, H9, H10 and Form A are not re-derived (outside R21's duties in the plan; H10 needs the paired cell sup-t not specified beyond its formula). AB3DMOT is covered in the K8 tables only.
- The power rule's random draws cannot be reproduced from the plan text, so power and families are compared within tolerance (M\*'s floor exactly on the analysis's own power; comparators' families recovered from size and share).
- The run-log checker could only be exercised on the AV2-tagged stand-in tree; route run records and the seven-string rule meet real data first on AV2.
