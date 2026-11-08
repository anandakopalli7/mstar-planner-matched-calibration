# X3 (h): the AB3DMOT diagnosis (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan 2(h) (sha256 38e2526d...); referee concern M7. Outputs of record only (within_lt3d, decision mode); AB3DMOT (tab) is descriptive in the registered test; T1 and T3 are shown for comparison. JSON: `x3_h_ab3dmot_v01.json`.

## (h1) M*'s screen by population

| Tracker | Population | Valid | Shown above | Flagged cells | Family flagged | Pooled E | Pooled LB 0.95 | Pooled flag | HK1c UB 0.995 | Cells with E > 0.05 (records share) |
|---|---|---|---|---|---|---|---|---|---|---|
| t1 | PD7_primary | True | False | - | - | 0.0440 | 0.0411 | False | 0.0482 | 11 (0.215) |
| t1 | SD1_7_gap_le_5m | True | False | - | - | 0.0376 | 0.0302 | False | 0.0473 | 9 (0.065) |
| t1 | PD_inpath | True | False | - | - | 0.0404 | 0.0296 | False | 0.0546 | 7 (0.063) |
| t3 | PD7_primary | True | False | - | - | 0.0430 | 0.0402 | False | 0.0471 | 12 (0.260) |
| t3 | SD1_7_gap_le_5m | True | False | - | - | 0.0324 | 0.0255 | False | 0.0412 | 9 (0.040) |
| t3 | PD_inpath | True | False | - | - | 0.0405 | 0.0322 | False | 0.0521 | 14 (0.157) |
| tab | PD7_primary | False | True | - | - | 0.0609 | 0.0570 | True | 0.0666 | 16 (0.800) |
| tab | SD1_7_gap_le_5m | True | False | - | - | 0.0592 | 0.0498 | False | 0.0720 | 21 (0.837) |
| tab | PD_inpath | True | False | - | - | 0.0409 | 0.0314 | False | 0.0536 | 5 (0.084) |

### tab: M*'s cells with a point estimate above 0.05 (record's per-cell table; simultaneous 0.95 bounds)

| Population | Cell | E | LB | UB | Flag | Records | Logs | Fallback share | Coarser bound only |
|---|---|---|---|---|---|---|---|---|---|
| PD7_primary | two_wheeler|lat|straight | 0.3067 | - | - | False | 136 | 9 | 1.000 | True |
| PD7_primary | two_wheeler|long|turning | 0.2452 | - | - | False | 79 | 14 | 1.000 | True |
| PD7_primary | two_wheeler|lat|turning | 0.2321 | - | - | False | 104 | 9 | 1.000 | True |
| PD7_primary | two_wheeler|long|straight | 0.2007 | - | - | False | 143 | 12 | 1.000 | True |
| PD7_primary | two_wheeler|lat|static | 0.1134 | - | - | False | 607 | 27 | 0.096 | False |
| PD7_primary | large|lat|turning | 0.0766 | - | - | False | 150 | 32 | 0.533 | True |
| PD7_primary | large|lat|static | 0.0755 | 0.0150 | 0.1222 | False | 3170 | 111 | 0.013 | False |
| PD7_primary | large|long|turning | 0.0702 | -0.0126 | 0.1341 | False | 542 | 61 | 0.424 | False |
| PD7_primary | car|long|new | 0.0662 | 0.0320 | 0.0927 | False | 4242 | 322 | 0.005 | False |
| PD7_primary | large|long|static | 0.0598 | 0.0142 | 0.0951 | False | 4071 | 156 | 0.047 | False |
| PD7_primary | pedestrian|long|static | 0.0596 | 0.0438 | 0.0718 | False | 61104 | 322 | 0.001 | False |
| PD7_primary | pedestrian|lat|static | 0.0590 | 0.0439 | 0.0707 | False | 50615 | 305 | 0.001 | False |
| PD7_primary | car|long|static | 0.0573 | 0.0452 | 0.0666 | False | 187026 | 373 | 0.000 | False |
| PD7_primary | large|long|straight | 0.0541 | 0.0045 | 0.0925 | False | 1258 | 84 | 0.316 | False |
| PD7_primary | car|lat|static | 0.0533 | 0.0412 | 0.0627 | False | 97215 | 367 | 0.000 | False |
| PD7_primary | pedestrian|lat|turning | 0.0529 | 0.0242 | 0.0751 | False | 8835 | 229 | 0.001 | False |
| SD1_7_gap_le_5m | large|long|new | 0.4000 | - | - | False | 14 | 5 | 1.000 | True |
| SD1_7_gap_le_5m | two_wheeler|lat|straight | 0.3333 | - | - | False | 26 | 3 | 1.000 | True |
| SD1_7_gap_le_5m | two_wheeler|lat|static | 0.2010 | - | - | False | 223 | 11 | 0.094 | False |
| SD1_7_gap_le_5m | large|long|straight | 0.1684 | - | - | False | 64 | 19 | 0.453 | False |
| SD1_7_gap_le_5m | two_wheeler|long|static | 0.1548 | - | - | False | 33 | 7 | 0.000 | False |
| SD1_7_gap_le_5m | large|long|turning | 0.1429 | - | - | False | 22 | 7 | 1.000 | True |
| SD1_7_gap_le_5m | large|lat|turning | 0.1333 | - | - | False | 61 | 15 | 0.820 | True |
| SD1_7_gap_le_5m | two_wheeler|long|turning | 0.1250 | - | - | False | 6 | 4 | 1.000 | True |
| SD1_7_gap_le_5m | two_wheeler|lat|turning | 0.1250 | - | - | False | 33 | 4 | 1.000 | True |
| SD1_7_gap_le_5m | pedestrian|long|new | 0.0833 | - | - | False | 49 | 22 | 0.041 | False |
| SD1_7_gap_le_5m | car|lat|new | 0.0779 | 0.0134 | 0.1264 | False | 570 | 123 | 0.000 | False |
| SD1_7_gap_le_5m | large|long|static | 0.0669 | -0.0227 | 0.1345 | False | 408 | 46 | 0.081 | False |
| SD1_7_gap_le_5m | large|lat|static | 0.0664 | -0.0149 | 0.1275 | False | 1200 | 54 | 0.020 | False |
| SD1_7_gap_le_5m | car|long|static | 0.0664 | 0.0345 | 0.0904 | False | 11059 | 290 | 0.000 | False |
| SD1_7_gap_le_5m | car|long|turning | 0.0616 | 0.0043 | 0.1047 | False | 398 | 106 | 0.000 | False |
| SD1_7_gap_le_5m | car|lat|static | 0.0590 | 0.0362 | 0.0762 | False | 30807 | 301 | 0.000 | False |
| SD1_7_gap_le_5m | pedestrian|long|static | 0.0556 | 0.0234 | 0.0799 | False | 3610 | 165 | 0.000 | False |
| SD1_7_gap_le_5m | pedestrian|lat|straight | 0.0530 | 0.0023 | 0.0911 | False | 1750 | 101 | 0.022 | False |
| SD1_7_gap_le_5m | pedestrian|lat|turning | 0.0519 | 0.0168 | 0.0783 | False | 1457 | 103 | 0.000 | False |
| SD1_7_gap_le_5m | pedestrian|long|straight | 0.0515 | 0.0004 | 0.0900 | False | 682 | 86 | 0.012 | False |
| SD1_7_gap_le_5m | car|long|straight | 0.0504 | 0.0058 | 0.0840 | False | 710 | 126 | 0.000 | False |
| PD_inpath | large|lat|static | 0.1667 | - | - | False | 41 | 9 | 1.000 | True |
| PD_inpath | large|lat|turning | 0.1429 | - | - | False | 22 | 7 | 1.000 | True |
| PD_inpath | two_wheeler|lat|turning | 0.1250 | - | - | False | 16 | 2 | 1.000 | True |
| PD_inpath | car|lat|static | 0.0636 | 0.0201 | 0.0947 | False | 1237 | 109 | 0.001 | False |
| PD_inpath | large|long|straight | 0.0535 | - | - | False | 290 | 22 | 1.000 | True |

## (h2) Fallback shares of M*'s fits (threshold entries from a coarser level; calibrated steps <= 2 s)

| Tracker | Entries | Coarser share | By level | Not in path / in path | Record-weighted (A13) P_rel / P_near / P_ip | Check vs record |
|---|---|---|---|---|---|---|
| t1 | 20 x 192 | 0.484 | 0: 0.516, 1: 0.202, 2: 0.157, 3: 0.125 | 0.222 / 0.746 | 0.0066 / 0.0077 / 0.0746 | 0.0e+00 |
| t3 | 20 x 192 | 0.483 | 0: 0.517, 1: 0.207, 2: 0.151, 3: 0.125 | 0.222 / 0.744 | 0.0065 / 0.0092 / 0.0758 | 0.0e+00 |
| tab | 20 x 192 | 0.520 | 0: 0.480, 1: 0.206, 2: 0.190, 3: 0.125 | 0.266 / 0.774 | 0.0042 / 0.0054 / 0.0676 | 0.0e+00 |

## (h3) Relied records by track score (plan P4 bins)

| Tracker | Relied records | <0.4 | [0.4,0.5) | [0.5,0.7) | [0.7,0.85) | >=0.85 | below 0.5 | below 0.7 | Join mismatches (k / inst) |
|---|---|---|---|---|---|---|---|---|---|
| t1 | 537924 | 0.000 | 0.080 | 0.366 | 0.519 | 0.035 | 0.080 | 0.446 | 0 / 0 |
| t3 | 537754 | 0.000 | 0.080 | 0.366 | 0.519 | 0.035 | 0.080 | 0.446 | 0 / 0 |
| tab | 587133 | 0.000 | 0.413 | 0.501 | 0.084 | 0.001 | 0.413 | 0.915 | 0 / 0 |

In-path relied records only:

| Tracker | Records | <0.4 | [0.4,0.5) | [0.5,0.7) | [0.7,0.85) | >=0.85 |
|---|---|---|---|---|---|---|
| t1 | 21442 | 0.000 | 0.038 | 0.297 | 0.641 | 0.024 |
| t3 | 20645 | 0.000 | 0.038 | 0.301 | 0.638 | 0.023 |
| tab | 23227 | 0.000 | 0.485 | 0.446 | 0.068 | 0.000 |

## (h4) Enforced pairs whose track has no ground-truth match

Counted directly (items' enumeration over every track; validated: reproduces the items summaries' decisions, pairs_considered, pairs_enforced and pairs_with_gt exactly on the GT-matched tracks). Pairs = (track, calibrated step) at the 11288 decision states of the reference run.

| Tracker | Enforced pairs (all tracks) | Without GT match | Share | Per decision | Decisions with >= 1 | share in [0.4,0.5) | share in [0.5,0.7) | share in [0.7,0.85) | share in >=0.85 | Items: GT-matched pairs without usable annotation at k+h |
|---|---|---|---|---|---|---|---|---|---|---|
| t1 | 637896 | 77490 | 0.1215 | 6.865 | 0.643 | 0.448 | 0.140 | 0.018 | 0.007 | 0.0392 |
| t3 | 638036 | 77839 | 0.1220 | 6.896 | 0.647 | 0.448 | 0.140 | 0.019 | 0.010 | 0.0394 |
| tab | 1013537 | 403577 | 0.3982 | 35.753 | 0.926 | 0.473 | 0.343 | 0.239 | 0.478 | 0.0364 |

The cache's in-path flag is set only for GT-matched tracks (verified on the caches: no unmatched track row is flagged in path), so false-positive tracks cannot be split by in-path.

Track rows in the cache (every track at every keyframe, not only enforced pairs): share of rows and share without a GT match, by score bin.

| Tracker | <0.4 rows / no GT | [0.4,0.5) rows / no GT | [0.5,0.7) rows / no GT | [0.7,0.85) rows / no GT | >=0.85 rows / no GT |
|---|---|---|---|---|---|
| t1 | 0.000 / - | 0.135 / 0.474 | 0.385 / 0.165 | 0.453 / 0.037 | 0.028 / 0.013 |
| t3 | 0.000 / - | 0.135 / 0.474 | 0.385 / 0.164 | 0.453 / 0.038 | 0.028 / 0.015 |
| tab | 0.000 / - | 0.471 / 0.468 | 0.460 / 0.330 | 0.067 / 0.235 | 0.001 / 0.500 |

## Reading

- tab: M* is not valid; shown above delta in PD7_primary (flagged cells: {'PD7_primary': [], 'SD1_7_gap_le_5m': [], 'PD_inpath': []}; family flagged: {'PD7_primary': [], 'SD1_7_gap_le_5m': [], 'PD_inpath': []}; pooled flagged: {'PD7_primary': True, 'SD1_7_gap_le_5m': False, 'PD_inpath': False}).
- t1: coarser-level threshold entries 0.484 (record-weighted on P_rel 0.0066); relied records below score 0.5: 0.080, below 0.7: 0.446; enforced pairs whose track has no GT match 0.1215 (6.86 per decision).
- t3: coarser-level threshold entries 0.483 (record-weighted on P_rel 0.0065); relied records below score 0.5: 0.080, below 0.7: 0.446; enforced pairs whose track has no GT match 0.1220 (6.90 per decision).
- tab: coarser-level threshold entries 0.520 (record-weighted on P_rel 0.0042); relied records below score 0.5: 0.413, below 0.7: 0.915; enforced pairs whose track has no GT match 0.3982 (35.75 per decision).

## Choices

- (h1) reads the record's own validity entry and per-cell table; nothing is recomputed (the per-cell bounds are the record's simultaneous 0.95 bounds over the evaluable cells, the flag rule of the screen for M*).
- (h2) 'fallback share' = share of M*'s in-path-split threshold entries (Mstar_ip_src > 0) over folds x the 4 calibrated steps x 192 strata, the record's fallback_strata_fits_entries definition (recomputed and checked); the record-weighted A13 share is read from the record.
- (h3) 'relied records' = the items' records whose reference-relied item is present (joined on scene, keyframe, step, pair); the items are the arm-independent reference-relied records of every enforced pair with a GT match, so they are the certificate's outcome set. Scores come from the cache row rec_row of the record's scene; the join is checked on keyframe and GT instance.
- (h4) the items summaries' pairs_enforced - pairs_with_gt is NOT the false-positive share (the items enumerate GT-matched tracks only); the false-positive share is counted directly by x3_stats_h_fpcount_v01.py with the items' own enumeration (k6_sim_v02's functions, read-only) over every track, validated exactly against the summaries on the GT-matched tracks. The cache-wide share of track rows without GT is added as context (all tracks, not only enforced).
- The exceedance of M* by score bin (partition P4 of analysis (b)) is not computed here: it needs M*'s per-record margins, which (b)'s partition-tagged re-run provides.

Code: `50_CODE/x3/x3_stats_h_v01.py` (sha256 in the JSON). Nothing here changes a status or table of record.
