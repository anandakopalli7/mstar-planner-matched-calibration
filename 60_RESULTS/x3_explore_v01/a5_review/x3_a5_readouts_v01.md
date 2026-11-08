# X3 A5 read-outs

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A5)

Read-outs of outputs of record and existing X3 files (sums of stored counts, stored values); nothing recomputed.

## (i) M*'s record-weighted pooled exceedance

Source: `60_RESULTS/c1_av2_v01/c1_analysis_csv_r1/k8_within_lt3d_t{1,3}_decide_cells.csv`, rows arm = Mstar, per population: sum of column `exceed` / sum of column `records` over the cell rows that carry both (the CSV stores `exceed` only for evaluable cells; the share of the population's records covered is given).

| tracker | P_rel | P_near | P_ip |
|---|---|---|---|
| T1 | 0.0454 (24186 / 533293; 99.7 % of records) | 0.0316 (1780 / 56403; 98.5 % of records) | 0.0355 (653 / 18385; 88.9 % of records) |
| T3 | 0.0445 (23663 / 531815; 99.7 % of records) | 0.0297 (1680 / 56523; 98.4 % of records) | 0.0349 (613 / 17562; 88.9 % of records) |

## (ii) Share of M*'s in-path relied records in fallback strata (S6 Table 13 source)

Source: `c1_analysis_r1.json`, key `k8.within_lt3d.<t>.A13_fallback_record_weighted.by_population.PD_inpath.pooled` (record-weighted from each record's fold, step, L0 and in-path flag).

- T1: 1543 of 20692 in-path relied records in fallback strata = **0.0746**
- T3: 1497 of 19754 in-path relied records in fallback strata = **0.0758**

## (iii) From c_intervals (x3-stats, analysis c2; method (i), the record's rule)

Source: `60_RESULTS/x3_explore_v01/c_intervals/x3_c2_simulation_v01.json`, keys `results.<t>."Mstar|delta".i.screen_flag_any_population` and `results.<t>."Mstar|observed".i.<population>.sim_ub_cover_all` (1000 simulated datasets).

- T1: P(M* at delta flagged in any population) = **0.113**; simultaneous coverage of the cell upper bounds at M*'s observed cell rates: P_rel 0.346 [0.317, 0.376]; P_near 0.370 [0.341, 0.400]; P_ip 0.406 [0.376, 0.437]
- T3: P(M* at delta flagged in any population) = **0.127**; simultaneous coverage of the cell upper bounds at M*'s observed cell rates: P_rel 0.271 [0.244, 0.299]; P_near 0.256 [0.230, 0.284]; P_ip 0.520 [0.489, 0.551]

## (iv) H2's bound at its Holm level

Source: `60_RESULTS/c1_av2_v01/c1_decision_r1.json`, keys `family_S.H2.holm_level`, `S_decision_forms.by_claim.H2.bound_at_holm_level` and `hypotheses.H2.by_tracker.<t>.holm_levels`.

- Holm level assigned: 0.005 (p = 2.5e-05, status holds); the bound used is UB at level 1 - 0.005 = 0.995: T1 0.01064, T3 -0.04939 (c = 0.03; both hold).
- Nominal (0.975) bound: T1 0.00452, T3 -0.05415.
