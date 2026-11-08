# X3 core report (x3-core agent)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan: 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md (sha256 38e2526d9f43f202fe4c8fe345be03d21421d6c7ada585022abf34a649362dc6), sections 0, 1, 2(a), 2(b). Code: 50_CODE/x3/; outputs: 60_RESULTS/x3_explore_v01/{gates, a_matched, b_partitions, runs}.

## Gates

- V0 (runner reproduces the record exactly; M*, B0, B4, B6, B9 on T1 and T3; B1, B3 and tab M* also compared): **True**
- V2 (partition sums = counts of record per arm, population, log): **True**
- V1 (screen at B = 4000 vs statuses of record): **True** (details in gates/x3_gates_v01.md)
- Overall: **PASSED**

V1 detail: status (Valid, shown above, removal) agrees for t1 32/33, t3 33/33, tab 33/33 arms of record. The one status disagreement is T1's sweep point B0a4 (X3 not Valid: PD_inpath car|lat|turning flagged, LB - delta = +0.0012, 0.92 MC SE; record Valid), within the rule. Component-only differences (statuses unchanged) are listed in gates/x3_gates_v01.md; two exceed 3 MC SE on the R21-scaled yardstick (T1 B9 PD7 large|long|new z 3.09; T3 B4 SD1_7 large|long|straight z 9.18) but are 1.15 and 0.56 MC SE on X3's own MC SE of that exact cell (R21 measured each comparator's largest removal statistic, a different cell); they change no status and do not gate. RETUNED-HK1's composite status agrees on all three trackers; its selection, re-run at B = 4000 on T1 (105 training screens), reproduces the record's choice (B0a8, none qualifies, every fold). Infeasible rates recomputed from the outputs of record equal the record's.

## Choices (where the plan is silent or the code needed a decision)

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

## Timings

| run | variants | episodes | wall s | worker s | partition checks |
|---|---|---|---|---|---|
| a_t1 | 18 | 6750 | 570.4 | 1656 | None |
| a_t3 | 18 | 6750 | 559.9 | 1627 | None |
| core_t1 | 7 | 2625 | 451.0 | 940 | 78484 |
| core_t3 | 7 | 2625 | 560.8 | 915 | 78484 |
| core_tab | 1 | 375 | 305.1 | 163 | 11180 |

One hk1_rule call at B = 4000 on 375 logs: {'B4': 13.1, 'Mstar': 24.4, 'B0a8': 3.0} s; selection B: 4000.
Analysis (a) screen: 703.1 s; (b) screen: 2.4 s.

Shards (per-scene, resumable): {"shards_a_t1": 375, "shards_a_t3": 375, "shards_core_t1": 375, "shards_core_t3": 375, "shards_core_tab": 375, "shards_smoke_t1": 3}

## Integrity checks

| time | event | run log | manifest of 60_RESULTS/c1_av2_v01 |
|---|---|---|---|
| 2026-11-07 11:23:34 | start manifest check | True | True |
| 2026-11-07 12:47:48 | chain start | True | True |
| 2026-11-07 12:48:12 | after b | True | (quick) |
| 2026-11-07 12:57:58 | after runa_t1 | True | (quick) |
| 2026-11-07 13:07:33 | after runa_t3 | True | (quick) |
| 2026-11-07 13:19:35 | after a | True | (quick) |
| 2026-11-07 13:19:51 | chain end | True | True |
| 2026-11-07 13:20:55 | final (x3-core end) | True | True |

Every X3 script also asserts the run log's sha256 at its start and end (x3_common_v01.assert_run_log).

## Files written

Every file with its sha256: 70_TESTS/X3_INTEGRITY_v01/X3_CORE_FILES_v01.txt (95 files; shards excluded).
