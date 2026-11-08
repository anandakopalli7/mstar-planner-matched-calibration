# Errata to the decision reports D05 v03, D07 v01 and D10 v01 (v01, 1 Nov 2026)

The decision reports are kept unchanged (they are cited by frozen plans and reviews). The imprecisions below were found while writing the evidence dossier `20_DESIGN/E01_EVIDENCE_DOSSIER_v01.md` (its Appendix A) and in its adversarial review `70_TESTS/R13B_E01_REVIEW_v01.md`. The frozen result files are right; the report sentences are loose or wrong. The manuscript takes its numbers from the result files via E01 v02, never from these sentences.

| # | Report, place | Sentence as written | What the frozen file says | Source |
|---|---|---|---|---|
| E1 | D07 §2 | "On Poly-MOT every multiplier is below 1" | `60_RESULTS/m/m_result_polymot_v04.json`, `E2_h2s.fit_on_all_train.Mstar`: 5 of the 96 thresholds are above 1 (e.g. car, ≥ 40 m, longitudinal: 1.118; two-wheeler, < 20 m, longitudinal, straight: 1.108). The sentence is false; the correct statement is that most Poly-MOT multipliers are below 1 and five are above | R13b finding 1 |
| E2 | D05 v03 (NEES fix) | "leaves lateral at 13–20 %, adds 1.6–2.7 m" | X2 result JSON: lateral 0.130 / 0.172 after the NEES fix; added longitudinal margin 2.17 / 2.72 m. "1.6" appears to be R06's re-estimated lower bound (1.57 m), not the X2 value | E01 App. A item 1 |
| E3 | D07 (efficiency table) | Margin ratios given without naming the split | The table's ratios are the E2 (val) values; `m_decision_v04.json` holds the E1 fixed-rule ratios (0.161 vs 0.165 for M*/B3). Both exist; the split must be named | E01 App. A item 2 |
| E4 | D07 (Poly-MOT margins) | "16.9 m / 32 m" | These are E1 values; E2 gives 16.0 / 30.3 m. The split must be named | E01 App. A item 3 |
| E5 | D10 §HK2 | "Bonferroni lower bounds 0.13–0.16" | Not a stored field in `k6_result_v02.json`; the flags and the paired bounds are stored and reproduce. The sentence should cite the stored fields | E01 App. A item 4 |
| E6 | D10 header vs tables | Closed-loop progress means | The means are over 2,100 episodes, not the 2,371 of the header (the difference is the episodes excluded by the replay rules); the count must be stated with the mean | R13b major |
| E7 | D10 / K6 plan | Record counts | Records are defined with k ≥ 1; the counts quoted (381,553 / 1,839,331) include frame 0; the k ≥ 1 counts are 373,702 / 1,800,482. Both must be given with their definition | R13b major |

**Consequence for claims.** E1 narrows D07's wording about Poly-MOT's multipliers, not the METHOD GO-B outcome, which rests on the pre-registered tests. E2–E7 are rounding, split-naming and count-definition issues with no effect on any verdict. E01 v02 carries the corrected statements; the manuscript draft must be checked against E01 v02 before any number is kept.
