# X3 (c2): simulated false removal and coverage at Argoverse 2's cell sizes (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan 2(c2) (sha256 38e2526d...); referee concern M4. 1000 datasets per scenario, inner log bootstrap of 1000, seeds [20261201, i, 3, s, d]. Method (i) is the record's rule (pre-specified); (ii) and (iii) are the (c1) alternatives, added and not pre-specified. JSON: `x3_c2_simulation_v01.json`.

## False removal of each comparator removed in r1 (truth 0.05 in every cell, its own layout)

Removal level 1 - 0.0125/9. '9 conditions' = a cell, family or pooled flag in P_rel, P_near or P_ip (plan 6.2); 'code' adds the HK1c failure that c1_analyse_v02.arm_status also counts. 95 % Wilson intervals over datasets in brackets.

| Tracker | Comparator | (i) 9 conditions | (i) code | (ii) 9 conditions | (iii) 9 conditions |
|---|---|---|---|---|---|
| t1 | B0 | 0.003 [0.001, 0.009] | 0.003 | 0.014 [0.008, 0.023] | 0.166 [0.144, 0.190] |
| t1 | B1 | 0.001 [0.000, 0.006] | 0.001 | 0.012 [0.007, 0.021] | 0.212 [0.188, 0.238] |
| t1 | B4 | 0.003 [0.001, 0.009] | 0.003 | 0.011 [0.006, 0.020] | 0.159 [0.138, 0.183] |
| t1 | B6 | 0.002 [0.001, 0.007] | 0.002 | 0.014 [0.008, 0.023] | 0.129 [0.110, 0.151] |
| t1 | B9 | 0.001 [0.000, 0.006] | 0.001 | 0.009 [0.005, 0.017] | 0.225 [0.200, 0.252] |
| t1 | RETUNED | 0.002 [0.001, 0.007] | 0.003 | 0.014 [0.008, 0.023] | 0.209 [0.185, 0.235] |
| t3 | B1 | 0.000 [0.000, 0.004] | 0.000 | 0.006 [0.003, 0.013] | 0.240 [0.215, 0.267] |
| t3 | B4 | 0.001 [0.000, 0.006] | 0.001 | 0.011 [0.006, 0.020] | 0.204 [0.180, 0.230] |
| t3 | B6 | 0.000 [0.000, 0.004] | 0.000 | 0.011 [0.006, 0.020] | 0.179 [0.156, 0.204] |
| t3 | B9 | 0.001 [0.000, 0.006] | 0.001 | 0.010 [0.005, 0.018] | 0.239 [0.214, 0.266] |
| t3 | RETUNED | 0.000 [0.000, 0.004] | 0.000 | 0.009 [0.005, 0.017] | 0.235 [0.210, 0.262] |

## M*: coverage at true rates = 0.05 in every cell

Simultaneous coverage of the one-sided '95 %' upper bounds over the evaluable cells (mean and worst per-cell coverage in brackets) and coverage of the HK1c '99.5 %' pooled upper bound.

| Tracker | Population | (i) simultaneous | (i) HK1c | (ii) simultaneous | (ii) HK1c | (iii) simultaneous | (iii) HK1c |
|---|---|---|---|---|---|---|---|
| t1 | PD7_primary | 0.395 (0.966; 0.899) | 0.991 | 0.942 (0.998; 0.990) | 0.993 | 0.732 (0.988; 0.957) | 0.992 |
| t1 | SD1_7_gap_le_5m | 0.414 (0.944; 0.899) | 0.986 | 0.937 (0.996; 0.991) | 0.995 | 0.729 (0.980; 0.968) | 0.990 |
| t1 | PD_inpath | 0.524 (0.924; 0.876) | 0.973 | 0.913 (0.989; 0.952) | 0.988 | 0.795 (0.973; 0.934) | 0.985 |
| t3 | PD7_primary | 0.433 (0.969; 0.921) | 0.991 | 0.953 (0.998; 0.990) | 0.994 | 0.733 (0.989; 0.967) | 0.994 |
| t3 | SD1_7_gap_le_5m | 0.376 (0.943; 0.880) | 0.980 | 0.941 (0.996; 0.991) | 0.987 | 0.713 (0.980; 0.956) | 0.982 |
| t3 | PD_inpath | 0.547 (0.928; 0.903) | 0.976 | 0.942 (0.992; 0.978) | 0.988 | 0.834 (0.977; 0.957) | 0.987 |

## M*: coverage at true rates = M*'s observed cell rates

Simultaneous coverage of the one-sided '95 %' upper bounds over the evaluable cells (mean and worst per-cell coverage in brackets) and coverage of the HK1c '99.5 %' pooled upper bound.

| Tracker | Population | (i) simultaneous | (i) HK1c | (ii) simultaneous | (ii) HK1c | (iii) simultaneous | (iii) HK1c |
|---|---|---|---|---|---|---|---|
| t1 | PD7_primary | 0.346 (0.963; 0.868) | 0.994 | 0.964 (0.999; 0.993) | 0.997 | 0.718 (0.987; 0.956) | 0.996 |
| t1 | SD1_7_gap_le_5m | 0.370 (0.937; 0.857) | 0.978 | 0.951 (0.997; 0.991) | 0.987 | 0.739 (0.980; 0.954) | 0.986 |
| t1 | PD_inpath | 0.406 (0.896; 0.671) | 0.969 | 0.958 (0.994; 0.984) | 0.984 | 0.667 (0.953; 0.774) | 0.983 |
| t3 | PD7_primary | 0.271 (0.955; 0.712) | 0.991 | 0.958 (0.998; 0.992) | 0.993 | 0.766 (0.990; 0.964) | 0.994 |
| t3 | SD1_7_gap_le_5m | 0.256 (0.919; 0.850) | 0.978 | 0.963 (0.997; 0.989) | 0.987 | 0.672 (0.976; 0.955) | 0.985 |
| t3 | PD_inpath | 0.520 (0.922; 0.849) | 0.970 | 0.933 (0.991; 0.982) | 0.984 | 0.814 (0.975; 0.932) | 0.981 |

## M*'s own flag rate when every cell is at 0.05 (size of the screen against M*; added, not pre-specified)

| Tracker | Population | (i) | (ii) | (iii) |
|---|---|---|---|---|
| t1 | PD7_primary | 0.053 | 0.101 | 0.267 |
| t1 | SD1_7_gap_le_5m | 0.037 | 0.099 | 0.304 |
| t1 | PD_inpath | 0.029 | 0.092 | 0.183 |
| t1 | any population | 0.113 | 0.267 | 0.589 |
| t3 | PD7_primary | 0.056 | 0.107 | 0.308 |
| t3 | SD1_7_gap_le_5m | 0.040 | 0.114 | 0.333 |
| t3 | PD_inpath | 0.035 | 0.091 | 0.180 |
| t3 | any population | 0.127 | 0.281 | 0.629 |

## Notes

- rho_c is the ANOVA ICC of the observed cell (truncated to [0, 1]; 0 where undefined, which gives binomial data); its values are in the JSON (meta.rho_used).
- With an inner bootstrap of 1000 the removal quantile 0.998611 sits between the 2nd and 3rd largest max-t replicates; the record used 40000. The simulated false-removal rate therefore carries this extra Monte Carlo noise in the quantile (it is part of what is simulated, as the plan specifies 1000).
- Evaluable sets and power families are fixed at the record's (they depend only on the record counts, which the simulation keeps).
- The comparator scenarios share one per-log rate per cell across the four record blocks, so the 9 conditions are correlated as in the data; the M* coverage scenarios draw each population on its own layout (coverage is a per-population property).
- Pooled truth = mean over logs with records of sum_c N_uc r_c / sum_c N_uc (the expectation of the record's pooled estimator given the layout); cell truth = r_c.

Code: `50_CODE/x3/x3_stats_c2_v01.py` (sha256 in the JSON).
