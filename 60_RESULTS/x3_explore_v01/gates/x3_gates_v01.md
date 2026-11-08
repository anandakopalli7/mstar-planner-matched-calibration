# X3 validation gates V0, V1, V2

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan section 1. Overall: **PASSED**.

## V0: the runner reproduces the runs of record

| tracker | arm | decisions | counts | cal | episode summaries | equal |
|---|---|---|---|---|---|---|
| t1 | Mstar | True (11288 rows) | True (106587 rows) | True | True | True |
| t1 | B0 | True (11288 rows) | True (106537 rows) | True | True | True |
| t1 | B4 | True (11288 rows) | True (106068 rows) | True | True | True |
| t1 | B6 | True (11288 rows) | True (105904 rows) | True | True | True |
| t1 | B9 | True (11288 rows) | True (109952 rows) | True | True | True |
| t1 | B1 | True (11288 rows) | True (108970 rows) | True | True | True |
| t1 | B3 | True (11288 rows) | True (109948 rows) | True | True | True |
| t3 | Mstar | True (11288 rows) | True (108294 rows) | True | True | True |
| t3 | B0 | True (11288 rows) | True (119567 rows) | True | True | True |
| t3 | B4 | True (11288 rows) | True (107763 rows) | True | True | True |
| t3 | B6 | True (11288 rows) | True (106973 rows) | True | True | True |
| t3 | B9 | True (11288 rows) | True (108465 rows) | True | True | True |
| t3 | B1 | True (11288 rows) | True (113007 rows) | True | True | True |
| t3 | B3 | True (11288 rows) | True (123985 rows) | True | True | True |
| tab | Mstar | True (11288 rows) | True (118840 rows) | True | True | True |

V0 gate arms: M*, B0, B4, B6, B9 on T1 and T3; B1, B3 (T1, T3) and M* (tab) are compared the same way (reported).

## V2: partition sums equal the counts of record

| tracker | arm | partitions x populations x logs equal | records (PD7) |
|---|---|---|---|
| t1 | Mstar | True | 534846 |
| t1 | B0 | True | 527372 |
| t1 | B1 | True | 512072 |
| t1 | B3 | True | 356260 |
| t1 | B4 | True | 533554 |
| t1 | B6 | True | 534861 |
| t1 | B9 | True | 497127 |
| t3 | Mstar | True | 533331 |
| t3 | B0 | True | 472380 |
| t3 | B1 | True | 503289 |
| t3 | B3 | True | 413292 |
| t3 | B4 | True | 531363 |
| t3 | B6 | True | 534025 |
| t3 | B9 | True | 501968 |
| tab | Mstar | True | 524152 |

## V1: the X3 screen (B = 4000) against the statuses of record (B = 40000)

### T1: status (Valid, shown above, removal) agrees for 32 of 33 arms; every component for 28

| arm | Valid (X3 / record) | shown above (X3 / record) | status disagreement (gating) | differing component | statistic (LB - delta, or UB - 0.08) | z (primary) | z (R21 x sqrt 10) | z (X3 own) | within 3 |
|---|---|---|---|---|---|---|---|---|---|
| B4 | [False, False] | [True, True] | no | PD7_primary/flagged_cells car|long|straight | 0.00007 | 0.03 | 0.03 | 0.05 | True |
| B4 | [False, False] | [True, True] | no | PD_inpath/NoFlag_pool (pooled) | 0.00071 | 0.27 | 0.27 | 0.42 | True |
| B9 | [False, False] | [True, True] | no | PD7_primary/flagged_cells large|long|new | 0.00786 | 3.09 | 3.09 | 1.15 | False |
| B6 | [False, False] | [True, True] | no | SD1_7_gap_le_5m/NoFlag (car|lat|turning) | 0.00358 | 1.31 | 1.31 | 0.21 | True |
| B6 | [False, False] | [True, True] | no | SD1_7_gap_le_5m/flagged_cells car|lat|turning | 0.00358 | 1.31 | 1.31 | 0.21 | True |
| B0a4 | [False, True] | [True, False] | yes | PD_inpath/NoFlag (car|lat|turning) | 0.00116 | 0.92 | n/a | 0.92 | True |
| B0a4 | [False, True] | [True, False] | yes | PD_inpath/flagged_cells car|lat|turning | 0.00116 | 0.92 | n/a | 0.92 | True |
| B0a4 | [False, True] | [True, False] | yes | removal (flags only): X3 ['PD_inpath cells'], record [] | | | | | see above |
| B0d0.02 | [False, False] | [True, True] | no | PD7_primary/flagged_cells large|long|new | -0.00008 | 0.04 | n/a | 0.04 | True |

RETUNED-HK1: composite status agrees: True; selection re-run at B = 4000 reproduces the record's per-fold choice: True (0: B0a8, 1: B0a8, 2: B0a8, 3: B0a8, 4: B0a8).

### T3: status (Valid, shown above, removal) agrees for 33 of 33 arms; every component for 29

| arm | Valid (X3 / record) | shown above (X3 / record) | status disagreement (gating) | differing component | statistic (LB - delta, or UB - 0.08) | z (primary) | z (R21 x sqrt 10) | z (X3 own) | within 3 |
|---|---|---|---|---|---|---|---|---|---|
| B1 | [False, False] | [True, True] | no | PD7_primary/NoFlag (car|long|new) | 0.00071 | 0.57 | 0.57 | 0.41 | True |
| B1 | [False, False] | [True, True] | no | PD7_primary/flagged_cells car|long|new | 0.00071 | 0.57 | 0.57 | 0.41 | True |
| B4 | [False, False] | [True, True] | no | SD1_7_gap_le_5m/flagged_cells large|long|straight | -0.01821 | 9.18 | 9.18 | 0.56 | False |
| B9 | [False, False] | [True, True] | no | PD7_primary/flagged_cells large|long|new | 0.00040 | 0.21 | 0.21 | 0.02 | True |
| B6 | [False, False] | [True, True] | no | PD7_primary/flagged_cells car|lat|new | -0.00336 | 2.02 | 2.02 | 1.07 | True |

### TAB: status (Valid, shown above, removal) agrees for 33 of 33 arms; every component for 32

| arm | Valid (X3 / record) | shown above (X3 / record) | status disagreement (gating) | differing component | statistic (LB - delta, or UB - 0.08) | z (primary) | z (R21 x sqrt 10) | z (X3 own) | within 3 |
|---|---|---|---|---|---|---|---|---|---|
| B4 | [False, False] | [True, True] | no | PD7_primary/flagged_cells large|long|new | 0.00054 | 0.05 | n/a | 0.05 | True |
| B4 | [False, False] | [True, True] | no | SD1_7_gap_le_5m/flagged_cells car|long|new | -0.00280 | 0.19 | n/a | 0.19 | True |
| B4 | [False, False] | [True, True] | no | PD_inpath/flagged_cells car|long|new | 0.00289 | 0.81 | n/a | 0.81 | True |

Infeasible rates recomputed from the outputs of record equal the record's (every arm): True.

## Timing

One hk1_rule call on the 375 logs at B = 4000: {'B4': 13.1, 'Mstar': 24.4, 'B0a8': 3.0} s (B = 2000 inside the selection only if > 60 s: 4000).
