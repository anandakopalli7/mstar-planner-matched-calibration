# X3 A5: the neutral screen without P1 and P3

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A5)

Reduced screen = A4(1)'s neutral screen on P2, P4, P5, P6, P7 (P1 track speed, P3 track age dropped) + HK1c per population; seeds [20261201, i, 21] / [20261202, i, 21]; B = 4000. Runs: runs/a4n_<t> and core_<t> (no new run). A4(1)'s selection is recomputed with its own seeds and checked equal to the A4 output: {"t1": {"Mstar": true, "B4": true, "B6": true, "B9": true, "B0": true}, "t3": {"Mstar": true, "B4": true, "B6": true, "B9": true, "B0": true}}.

## (1) Matched validity on the reduced screen

| tracker | family | per-fold choice | composite reduced | composite registered | infeasible | progress | mean back-off | V2 | V2_exec | V2_viol | M* - composite infeasible (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | True | Valid | 0.2603 | 0.9657 | 0.8480 | 0.3412 | 0.4480 | 0.0128 | - |
| T1 | B4 | B4@0.02, B4@0.02, B4@0.03, B4@0.02, B4@0.02 | True | flagged | 0.4472 | 0.9583 | 0.7424 | 0.2804 | 0.4478 | 0.0212 | -0.1869 [-0.2144, -0.1595] |
| T1 | B6 | B6@0.03, B6@0.03, B6@0.03, B6@0.04, B6@0.04 | True | flagged | 0.2982 | 0.9635 | 0.8446 | 0.3767 | 0.4747 | 0.0183 | -0.0379 [-0.0634, -0.0118] |
| T1 | B9 | B9@0.05, B9@0.05, B9@0.05, B9@0.05, B9@0.05 | True | flagged | 0.6928 | 0.9552 | 0.5048 | 0.1582 | 0.5266 | 0.0143 | -0.4325 [-0.4580, -0.4055] |
| T1 | B0 | B0d0.02, B0d0.02, B0d0.02, B0d0.02, B0d0.02 | True | flagged | 0.4682 | 0.9572 | 0.7313 | 0.3027 | 0.4761 | 0.0202 | -0.2079 [-0.2341, -0.1805] |
| T3 | Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | True | Valid | 0.3505 | 0.9663 | 0.7843 | 0.3480 | 0.5044 | 0.0149 | - |
| T3 | B4 | B4@0.015, B4@0.015, B4@0.015, B4@0.015, B4@0.015 | True | flagged | 0.6331 | 0.9608 | 0.5536 | 0.2209 | 0.5164 | 0.0271 | -0.2826 [-0.3033, -0.2622] |
| T3 | B6 | B6@0.03, B6@0.02, B6@0.02, B6@0.03, B6@0.02 | True | flagged | 0.3832 | 0.9635 | 0.7692 | 0.3046 | 0.4651 | 0.0160 | -0.0327 [-0.0453, -0.0206] |
| T3 | B9 | B9@0.05, B9@0.05, B9@0.05, B9@0.05, B9@0.05 | True | flagged | 0.6629 | 0.9587 | 0.5338 | 0.1774 | 0.5230 | 0.0180 | -0.3124 [-0.3409, -0.2840] |
| T3 | B0 | B0a0.25, B0a0.333, B0a0.25, B0a0.25, B0a0.333 | True | flagged | 0.7076 | 0.9587 | 0.4930 | 0.2179 | 0.5587 | 0.0214 | -0.3571 [-0.3799, -0.3344] |

Reading fixed by A5: every M* - composite interval lies below 0 on both trackers: the back-off advantage on the neutral screen survives removing P1 and P3

## (2) The flags that stop each family one grid point before its matched point

- T1 Mstar A4: matched in sample at Mstar@0.03; at Mstar@0.04: P1 [0.5,3)|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P1 [0.5,3)|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T1 Mstar A5: matched in sample at Mstar@0.03; at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T1 B4 A4: matched in sample at B4@0.015; at B4@0.02: P1 [3,8)|lat PD
  - fold 0 (matched B4@0.015): at B4@0.02: P1 [3,8)|lat PD
  - fold 1 (matched B4@0.02): at B4@0.03: P1 [0.5,3)|long PD7; P1 [3,8)|long PD7; P1 [3,8)|lat PD; P3 1-2|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 2 (matched B4@0.02): at B4@0.03: P1 [0.5,3)|long PD7; P1 [3,8)|long PD7; P1 [3,8)|lat PD7; P1 [3,8)|lat PD; P3 1-2|long PD7; P4 [0.4,0.5)|long PD7
  - fold 3 (matched B4@0.015): at B4@0.02: P1 [3,8)|lat PD
  - fold 4 (matched B4@0.015): at B4@0.02: P1 [3,8)|lat PD
- T1 B4 A5: matched in sample at B4@0.02; at B4@0.03: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 0 (matched B4@0.02): at B4@0.03: P2 [2,5.5)|lat PD; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 1 (matched B4@0.02): at B4@0.03: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 2 (matched B4@0.03): at B4@0.04: P2 <2|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|long PD7; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 3 (matched B4@0.02): at B4@0.03: P4 [0.4,0.5)|long PD7
  - fold 4 (matched B4@0.02): at B4@0.03: P4 [0.4,0.5)|long PD7
- T1 B6 A4: matched in sample at B6@0.02; at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 0 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 1 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 2 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 3 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
  - fold 4 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P1 [3,8)|lat PD7
- T1 B6 A5: matched in sample at B6@0.03; at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 0 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 1 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 2 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 3 (matched B6@0.04): at B6@0.05: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7; P4 [0.5,0.7)|long PD7; P4 [0.5,0.7)|lat PD7; P5 <1|lat PD7
  - fold 4 (matched B6@0.04): at B6@0.05: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7; P4 [0.5,0.7)|long PD7; P4 [0.5,0.7)|lat PD7
- T1 B9 A4: matched in sample at B9@0.05; at None: matched at the least conservative grid point
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
  - fold 4 (matched B9@0.05): at None: matched at the least conservative grid point
- T1 B9 A5: matched in sample at B9@0.05; at None: matched at the least conservative grid point
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 4 (matched B9@0.05): at None: matched at the least conservative grid point
- T1 B0 A4: matched in sample at B0d0.005; at B0d0.01: P1 [3,8)|lat PD
  - fold 0 (matched B0d0.005): at B0d0.01: P1 [3,8)|lat PD
  - fold 1 (matched B0a2): at B0d0.02: P1 [3,8)|lat PD
  - fold 2 (matched B0a2): at B0d0.02: P1 [3,8)|lat PD
  - fold 3 (matched B0d0.005): at B0d0.01: P1 [3,8)|lat PD
  - fold 4 (matched B0a3): at B0d0.005: P1 [3,8)|lat PD
- T1 B0 A5: matched in sample at B0d0.02; at B0d0.05: P2 <2|long PD7; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 0 (matched B0d0.02): at B0d0.05: P2 <2|long PD7; P2 [2,5.5)|lat PD; P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD; P6 >200|lat PD
  - fold 1 (matched B0d0.02): at B0d0.05: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD; P5 [1,5)|lat PD
  - fold 2 (matched B0d0.02): at B0d0.05: P2 <2|long PD7; P4 [0.4,0.5)|long PD7
  - fold 3 (matched B0d0.02): at B0d0.05: P4 [0.4,0.5)|long PD7; P4 [0.5,0.7)|lat PD
  - fold 4 (matched B0d0.02): at B0d0.05: P2 <2|long PD7; P4 [0.4,0.5)|long PD7
- T3 Mstar A4: matched in sample at Mstar@0.03; at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T3 Mstar A5: matched in sample at Mstar@0.03; at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 1 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 3 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|lat PD7
  - fold 4 (matched Mstar@0.03): at Mstar@0.04: P4 [0.4,0.5)|long PD7; P4 [0.4,0.5)|lat PD7
- T3 B4 A4: matched in sample at B4@0.01; at B4@0.015: P1 [3,8)|long PD7
  - fold 0 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
  - fold 1 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
  - fold 2 (matched B4@0.015): at B4@0.02: P1 [3,8)|long PD7; P1 >=8|long PD7; P2 >=8|long PD7
  - fold 3 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
  - fold 4 (matched B4@0.01): at B4@0.015: P1 [3,8)|long PD7
- T3 B4 A5: matched in sample at B4@0.015; at B4@0.02: P2 >=8|long PD7
  - fold 0 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 1 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 2 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 3 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
  - fold 4 (matched B4@0.015): at B4@0.02: P2 >=8|long PD7
- T3 B6 A4: matched in sample at B6@0.02; at B6@0.03: P1 [3,8)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 0 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7
  - fold 1 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7; P4 [0.4,0.5)|lat PD7
  - fold 2 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 3 (matched B6@0.02): at B6@0.03: P1 [3,8)|long PD7
  - fold 4 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
- T3 B6 A5: matched in sample at B6@0.02; at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 0 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 1 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 2 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
  - fold 3 (matched B6@0.03): at B6@0.04: P4 [0.4,0.5)|lat PD7
  - fold 4 (matched B6@0.02): at B6@0.03: P4 [0.4,0.5)|lat PD7
- T3 B9 A4: matched in sample at B9@0.04; at B9@0.05: P1 [3,8)|long PD7
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
  - fold 4 (matched B9@0.04): at B9@0.05: P1 [3,8)|long PD7
- T3 B9 A5: matched in sample at B9@0.05; at None: matched at the least conservative grid point
  - fold 0 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 1 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 2 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 3 (matched B9@0.05): at None: matched at the least conservative grid point
  - fold 4 (matched B9@0.05): at None: matched at the least conservative grid point
- T3 B0 A4: matched in sample at B0a0.333; at B0d0.2: P1 [3,8)|long PD7; P2 >=8|long PD7
  - fold 0 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7
  - fold 1 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7; P2 >=8|long PD7
  - fold 2 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7
  - fold 3 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7
  - fold 4 (matched B0a0.333): at B0d0.2: P1 [3,8)|long PD7; P2 >=8|long PD7
- T3 B0 A5: matched in sample at B0d0.2; at B0a0.25: P2 >=8|long PD7
  - fold 0 (matched B0a0.25): at B0a0.125: P2 [5.5,8)|long PD7; P2 >=8|long PD7; P2 >=8|long SD1; P6 >200|long PD7
  - fold 1 (matched B0a0.333): at B0d0.2: P2 >=8|long PD7
  - fold 2 (matched B0a0.25): at B0a0.125: P2 >=8|long PD7
  - fold 3 (matched B0a0.25): at B0a0.125: P2 [5.5,8)|long PD7; P2 >=8|long PD7; P2 >=8|long SD1
  - fold 4 (matched B0a0.333): at B0d0.2: P2 >=8|long PD7

## (3) Six exceedance and operability measures of the matched composites (k8_analyse_v04's definitions)

| tracker | family | screen | V2 | V2_exec | V2_viol | infeasible | progress | min gap < 1 m |
|---|---|---|---|---|---|---|---|---|
| T1 | Mstar | A4 | 0.3412 | 0.4480 | 0.0128 | 0.2603 | 0.9657 | 0.2865 |
| T1 | Mstar | A5 | 0.3412 | 0.4480 | 0.0128 | 0.2603 | 0.9657 | 0.2865 |
| T1 | B4 | A4 | 0.2207 | 0.4295 | 0.0187 | 0.5327 | 0.9537 | 0.2725 |
| T1 | B4 | A5 | 0.2804 | 0.4478 | 0.0212 | 0.4472 | 0.9583 | 0.2682 |
| T1 | B6 | A4 | 0.2440 | 0.4607 | 0.0141 | 0.4926 | 0.9554 | 0.2689 |
| T1 | B6 | A5 | 0.3767 | 0.4747 | 0.0183 | 0.2982 | 0.9635 | 0.2739 |
| T1 | B9 | A4 | 0.1530 | 0.5256 | 0.0137 | 0.6998 | 0.9555 | 0.2685 |
| T1 | B9 | A5 | 0.1582 | 0.5266 | 0.0143 | 0.6928 | 0.9552 | 0.2676 |
| T1 | B0 | A4 | 0.2251 | 0.4538 | 0.0189 | 0.5624 | 0.9522 | 0.2771 |
| T1 | B0 | A5 | 0.3027 | 0.4761 | 0.0202 | 0.4682 | 0.9572 | 0.2683 |
| T3 | Mstar | A4 | 0.3480 | 0.5044 | 0.0149 | 0.3505 | 0.9663 | 0.2913 |
| T3 | Mstar | A5 | 0.3480 | 0.5044 | 0.0149 | 0.3505 | 0.9663 | 0.2913 |
| T3 | B4 | A4 | 0.1566 | 0.5172 | 0.0215 | 0.7010 | 0.9618 | 0.2777 |
| T3 | B4 | A5 | 0.2209 | 0.5164 | 0.0271 | 0.6331 | 0.9608 | 0.2772 |
| T3 | B6 | A4 | 0.2673 | 0.4499 | 0.0158 | 0.4296 | 0.9615 | 0.2894 |
| T3 | B6 | A5 | 0.3046 | 0.4651 | 0.0160 | 0.3832 | 0.9635 | 0.2896 |
| T3 | B9 | A4 | 0.1569 | 0.5257 | 0.0167 | 0.6919 | 0.9578 | 0.2716 |
| T3 | B9 | A5 | 0.1774 | 0.5230 | 0.0180 | 0.6629 | 0.9587 | 0.2693 |
| T3 | B0 | A4 | 0.1915 | 0.5566 | 0.0200 | 0.7324 | 0.9596 | 0.2792 |
| T3 | B0 | A5 | 0.2179 | 0.5587 | 0.0214 | 0.7076 | 0.9587 | 0.2795 |

Every in-sample grid point: x3_a5_points_v01.csv (the same six measures, and the in-sample pass under each screen).
