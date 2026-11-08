# X3 stats agent (x3-stats): analyses (c), (f), (h), choices, checks and integrity (v01, 7 Nov 2026)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

- **Plan.** `20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md`, sha256 38e2526d9f43f202… (checked by every script before it ran). Sections 0, 2(c), 2(f), 2(h). Referee concerns M4, M10 and M7 (`70_TESTS/V05_REFEREE_REVIEW_v01.md`).
- **Nothing here changes the verdict of record (r1 = GO), a claim status or a table of record.**

## 1. Integrity

- **Run log.** `40_PROTOCOL/C1_RUN_LOG.txt` hashed 8bc6235d0c582f0b52952dcb86717a6ab42236a1e472582ebf8f4a10f95e2090 at every check below.
- **Record folder.** All 3090 files of `60_RESULTS/c1_av2_v01/` were re-hashed against `BASELINE_MANIFEST_v01.txt` at each check: identical every time, with no file missing, added or changed. The checker is `50_CODE/x3/x3_stats_integrity_v01.py`.

| Check (file) | Time | Run log | Manifest |
|---|---|---|---|
| `c_intervals/x3_stats_integrity_pre_start.json` (before (c1)) | 11:21:06 | equal | identical |
| `f_tradeoff/x3_stats_integrity_pre_f.json` (after (c1), before (f)) | 11:43:16 | equal | identical |
| `f_tradeoff/x3_stats_integrity_post_f.json` | 11:44:06 | equal | identical |
| `h_ab3dmot/x3_stats_integrity_pre_h.json` (after the (h4) count, before (h)) | 11:59:24 | equal | identical |
| `h_ab3dmot/x3_stats_integrity_post_h.json` | 12:00:09 | equal | identical |
| `c_intervals/x3_stats_integrity_post_c1_c2.json` (after (c2)) | 12:33:07 | equal | identical |
| `c_intervals/x3_stats_integrity_final.json` | 12:34:07 | equal | identical |

- **No guarded entry point was run.**
  - Nothing from `50_CODE/c1_av2`, `50_CODE/k8` or `50_CODE/av2` was imported or executed.
  - The imports were:
    - the R21 library `70_TESTS/R21_c1_v01/r21_lib_v01.py`, which is standalone numpy;
    - the frozen simulator `50_CODE/k6/k6_sim_v02.py`, for the (h4) count only. It imports only numpy and the standard library and has no entry point.
  - The items script `k8_items_v08.py` was read, not imported, because it imports `c1_guard_v05`.
- **Writes.**
  - New files only, under `60_RESULTS/x3_explore_v01/{c_intervals,f_tradeoff,h_ab3dmot}/`, `50_CODE/x3/x3_stats_*` and this report.
  - Every output writer refuses to overwrite an existing file.
  - The live line `00_PROGRESS/live/x3_stats.txt` was rewritten at each milestone.
- **Heavy lock.** Only (c1) (34 s) and (c2) took the lock:
  - (c2) waited 36 min for the lock while other agents' steps held it;
  - it then held the lock 12:13–12:25 for T1 and 12:25–12:32 for T3.

  The light steps ((f), (h), the (h4) count and the (c2) model check: no bootstrap, under 300 MB each) ran outside the lock.
- **Deliberate stop.** I stopped my own smoke test of (c2) (background task b226dmmju) at 11:36 because it was waiting on the heavy lock. It had written nothing; its target was the scratchpad. No other process was touched.

## 2. Choices where the plan was silent (closest to the code of record)

**(c1)**
- **Method (i)** is the record's bound exactly: sup-t on the bootstrap SE (`k6_analyse_v02.flag` / `m_lib_v04._simul`, through R21). For one cell this is the basic bootstrap bound 2E − Q_{1−L}(E*). The pure percentile HK1c UB is also in the JSON.
- **Methods (ii) and (iii)**:
  - (ii) uses the record's estimator, the mean over logs of the per-log rate (a ratio of two log totals in the bootstrap), with its cluster delta-method SE.
  - (ii)'s SE floor √(δ(1−δ)/N_eff) uses N_eff = N/deff from (iii), recomputed on each replicate.
  - (iii) is centred on the record's estimate. The ANOVA ICC (unbalanced: MSB, MSW, n0) is truncated to [0, 1], and m̄ = N/(logs with records).
  - Both use Bonferroni over the record's sup-t sets.
  - Families and evaluable sets are the record's.
- **Status rules** are `c1_analyse_v02.arm_status`, where ShownAbove includes an HK1c failure. The 9-condition reading of plan §6.2 is reported alongside.
- **Extra columns.**
  - Method (i) is shown at X3's B = 4000.
  - Method (ii) is also shown on the record's weights (B = 40000), because 0.998611 at B = 4000 leaves about 5.6 replicates in the tail.
  - A variant of (iii) centred on x/n is shown, labelled as a different estimand.

**(c2)**
- **Model.**
  - ρ̂_c is the (iii) ANOVA ICC of the observed cell: the comparator's P_rel cell, or M*'s cell in each population.
  - The comparator datasets are drawn jointly on the four disjoint record blocks, so the 9 conditions are correlated as in the data.
  - The M* coverage datasets are drawn per population.
  - Truth is r_c per cell. The pooled truth is the estimator's expectation given the layout.
- **Seeds.** `[20261201, i, 3, s, d]` per scenario and dataset, so a resume is exact. The inner bootstrap is 1000 fresh multinomial rows per dataset.
- **Added and labelled "not pre-specified"**:
  - methods (ii) and (iii);
  - M*'s own flag rate at truth δ;
  - a model-fidelity check, `x3_c2_modelcheck_v01.*`.

**(f)**
- V2 and V2_viol are on P_rel.
- The status is the record's arm_status, so comparators of K are judged at the removal level and every other arm at 0.95.
- RETUNED-HK1 chose B0a8 in every fold on all three trackers, so its point equals B0a8's.
- Back-off shares are given both pooled over decisions (the record's `backoff_distribution`) and as log means.

**(h)**
- **(h4): the items summaries cannot give the false-positive share.** `k8_items_v08.scene_items` enumerates only GT-matched tracks (`for j in np.nonzero(inst >= 0)`). So pairs_enforced − pairs_with_gt counts GT-matched tracks that lack an annotation at k+h.
- **I therefore counted directly** (`x3_stats_h_fpcount_v01.py`), using the items' own enumeration over every track. On the GT-matched tracks it reproduces the summaries' decisions, pairs_considered, pairs_enforced and pairs_with_gt **exactly** on all three trackers.
- **"Relied records"** are the items' records whose reference-relied item exists, joined on (scene, keyframe, step, pair).
- **In-path split.** The cache's in-path flag is set only for GT-matched tracks, so false-positive tracks cannot be split by in path.
- **M*'s exceedance by score bin** needs per-record margins and is left to (b).

## 3. Checks

- **(c1) reproduction.** Method (i) on the record's weights matches the record:
  - largest difference 3.1e-15 over 194 numeric checks on T1 and 5.3e-15 over 195 on T3;
  - 0 mismatches in flagged lists or statuses;
  - the RETUNED composite matches the record's `arm_of_scene` on all 375 logs.
- **(c1)/(c2) helpers.** Unit-tested on synthetic data (scratchpad):
  - the studentised pivots equal a direct recomputation on an expanded replicate;
  - the ANOVA ICC equals an explicit one-way ANOVA;
  - the (c2) per-dataset draws reproduce exactly from the seed.
- **(c2) blocks.** Block sums equal R21's population tables exactly, for every arm and population.
- **(f).** 449 checks per tracker against `*_v2.csv`, `*_tradeoff.csv`, `*_arms.csv` and the c1 JSON, with largest differences 3.3e-16 (T1), 1.1e-16 (T3) and 2.2e-16 (tab).
  - Infeasible ⇔ λ < 1 with no exception (0 of 349,928 decisions per tracker).
  - The episodes' own back-off counts equal the decision rows for all 31 arms.
- **(h).**
  - The fallback entry shares equal the record's `fallback_strata_fits_entries` (difference 0).
  - The cache join had 0 keyframe and 0 GT-instance mismatches.
  - The (h4) direct count is validated exactly, as described above.
- **MC precision.** The MC SE of the decisive (ii) bounds at B = 4000 is at most 0.0011. No (ii) status sits within 3 MC SE of a threshold.

## 4. Results (details in each MD)

**(c1), on T1 and T3.**
- **HK1c.** Every M* HK1c UB passes under every method. The largest is 0.0606 (ii, T1 P_ip), against 0.0546 of record.
- **(ii): no M* or V_t status changes.**
  - M* stays valid and V_t is unchanged ({B3}; {B0, B3}), so H1 holds.
  - M*'s largest simultaneous UBs rise to 0.156–0.162 (T1) and 0.162–0.189 (T3), from 0.118–0.129 and 0.110–0.157 of record.
  - Comparators gain flags, but all of them were already removed.
- **(iii): M* is flagged on both trackers**, in T1 P_rel car|lat|static (LB 0.0522) and T3 P_ip car|lat|straight (LB 0.0521). Valid(M*) is therefore false, so **H1 would not be met under (iii)**. V_t is unchanged.
- **No r1 removal is reversed by any method.**

**(c2), method (i) of record.**
- **False removal.** 0.000–0.003 per comparator, against the 0.0125 removal budget.
- **Coverage of M*'s simultaneous "95 %" UBs.**
  - At δ: 0.38–0.55.
  - At observed rates: 0.26–0.52.
  - Per-cell mean 0.90–0.97; worst cell 0.67–0.92.
- **Coverage of the HK1c "99.5 %" bound.** 0.973–0.991 at δ and 0.969–0.994 at observed rates.
- **M*'s own flag rate at δ.** 0.03–0.06 per population, and 0.11–0.13 for any of the three populations.

**(c2), the added methods.**
- **(ii).**
  - Simultaneous coverage 0.91–0.96.
  - False removal 0.006–0.014.
  - M*'s flag rate 0.09–0.11 per population.
- **(iii).**
  - Simultaneous coverage 0.67–0.83.
  - False removal 0.13–0.24.
  - M*'s flag rate 0.18–0.33 per population.
  - So (iii) is strongly anti-conservative at Argoverse 2's cell sizes.
- **Model check.** The model's SE is a median 0.85–1.04 of the record's bootstrap SE (range 0.33–2.9). Power-like numbers at observed rates are therefore somewhat overstated.

**(f).** The figures and tables are in `f_tradeoff/`.
- **M\***: infeasible 0.186 / 0.247 / 0.891 (T1 / T3 / tab), V2 0.491 / 0.496 / 0.520, V2_viol 0.016 / 0.018 / 0.038.
- **No arm of any status is at or below M* on both infeasible rate and V2_viol** (all three trackers).
- **Every valid arm other than M* is infeasible in ≥ 0.66 of decisions.**
- **The emergency-stop share is identical across arms**: 0.0043 (T1), 0.0024 (T3), 0.0064 (tab).
- **M*'s infeasible decisions on T1** back off to λ 0.75 / 0.5 / 0.25 / 0 / e-stop in 0.32 / 0.30 / 0.21 / 0.14 / 0.02 of them. On tab, 0.74 go to λ = 0.

**(h), AB3DMOT (tab).**
- **M\*'s screen.** M* fails only on the pooled P_rel cell (E 0.0609, LB 0.0570); no cell or family cell is flagged.
  - 16 P_rel cells have E > δ, and they hold 80 % of P_rel records. They include the large car|long|static (0.057; 187k records) and pedestrian static cells (0.059–0.060).
  - The two_wheeler cells with E 0.20–0.31 are not evaluable and are fallback-only.
- **Fallback.** Threshold entries from a coarser level: 0.520 on tab against 0.484 (T1) and 0.483 (T3). Record-weighted on P_rel: 0.0042 against 0.0066 and 0.0065.
- **Low-score tracks.** Relied records with score < 0.5: 0.413 on tab against 0.080 on both T1 and T3; < 0.7: 0.915 against 0.446.
- **Enforced pairs whose track has no GT match.** 0.398 on tab (35.8 per decision; 92.6 % of decisions have at least one) against 0.122 on T1/T3 (6.9 per decision; 64 %).

## 5. Caveats

- **(iii) is mismatched to the estimand.** The design-effect Wilson uses deff for a record-pooled ratio with equal cluster sizes, applied here to a log-mean estimator with very unequal cluster sizes. Its (c1) flags of M* (LBs 0.0522 and 0.0521) should be read with its simulated size of 0.18–0.33.
- **(c2) depends on the beta-binomial model with the ANOVA ICC** (see the model check).
- **(c2) inner bootstrap.** With B = 1000, the 0.998611 quantile sits between the 2nd and 3rd largest replicates.
- **AB3DMOT's score scale may differ from the LT3D detector's.** The P4 bins are the plan's fixed bins.

## 6. Files written (sha256, first 12 hex)

- **Code** (`50_CODE/x3/`):
  - `x3_stats_common_v01.py` def79e85212f
  - `x3_stats_c1_v01.py` dbaffb1641d4
  - `x3_stats_c2_v01.py` f228213467d6
  - `x3_stats_c2_modelcheck_v01.py` 40407f7cc777
  - `x3_stats_f_v01.py` bbb98f105d7f
  - `x3_stats_h_v01.py` 3758f225d3a5
  - `x3_stats_h_fpcount_v01.py` a6b9d27a2a6f
  - `x3_stats_integrity_v01.py` 34c9d411cca3
- **`c_intervals/`**:
  - `x3_c1_intervals_v01.json` f907de1ccf74 and `.md` d32bae289874
  - `x3_c2_simulation_v01.json` e3c11d86dc0d and `.md` c2493faf895f
  - `x3_c2_modelcheck_v01.json` 7434eb0dbdee and `.md` e695e8899b98
  - logs `x3_c1_run_v01.log` 85ce02d7beb5, `x3_c2_run_v01.log` d89c1aff1d0c, `x3_c2_run_v01.err` (empty) e3b0c44298fc
  - `c2_ckpt_v01/` (300 chunk files; sha256 of their concatenation a5013a6cacd8)
  - integrity JSONs: pre_start 2e20d3342b2f, post_c1_c2 549109f4a3f1, final 173e08752a7f
- **`f_tradeoff/`**:
  - `x3_f_tradeoff_v01.json` c24e964a8ac9 and `.md` 4534155c6545
  - `x3_f_infeasible_vs_V2_v01.pdf` 170096bfb491 and `.png` 538e87ccaf58
  - `x3_f_infeasible_vs_V2viol_v01.pdf` 6785c0dce833 and `.png` b2d680f5e111
  - `x3_f_run_v01.log` 661b802b9504
  - integrity pre_f 0b0d6990c03b, post_f 66336da5ae10
- **`h_ab3dmot/`**:
  - `x3_h_ab3dmot_v01.json` f5f05134d958 and `.md` d532b488bbaa
  - `x3_h_fpcount_t1_v01.json` ac0207a25308, `_t3_` 10a5ec8fbf4f, `_tab_` 9688525f54bb
  - logs `x3_h_fpcount_run_v01.log` 45b9d11d3eb5, `x3_h_run_v01.log` eb8216b1a7e8
  - integrity pre_h 3f298414132b, post_h 5ad9c4c92f5c
- **This report**: `70_TESTS/X3_INTEGRITY_v01/X3_STATS_REPORT_v01.md`.
