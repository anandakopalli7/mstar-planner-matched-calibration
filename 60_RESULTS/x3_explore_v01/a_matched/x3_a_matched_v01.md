# X3 analysis (a): matched-validity operability

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan section 2(a). B4, B6 (B6_ip) and B9 refitted by the frozen fit rule at delta' (x3_fits_v01; n_min = ceil(1/delta') - 1), cross-fitted on the C1 folds, run in decision mode (x3_run_v01). Screen: the registered screen as coded (hk1_rule_criteria, arm_status), grid points and composites judged as RETUNED-HK1 of record (flags at 0.95, power datasets 500); B = 4000; seeds [20261201, i, 1] / [20261202, i, 1]. Selection: per held-out fold, the least conservative point Valid on the other four folds (B = 4000 in the selection); else the most conservative fittable point, flagged.

## T1

M* infeasible rate 0.1864.

| family | per-fold choice (0..4) | none qualifies | composite Valid | composite shown above | composite infeasible | M* - composite (95 % CI) |
|---|---|---|---|---|---|---|
| B4 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.9106 | -0.7243 [-0.7446, -0.7032] |
| B6 | 0.015, 0.005, 0.015, 0.015, 0.015 | 1 | True | False | 0.6226 | -0.4362 [-0.4634, -0.4098] |
| B9 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.9724 | -0.7860 [-0.8047, -0.7670] |
| B0 (RETUNED-HK1 of record) | B0a8, B0a8, B0a8, B0a8, B0a8 | 0, 1, 2, 3, 4 | True | False | 0.7810 | -0.5946 [-0.6187, -0.5704] |

Whole curve (in-sample, all 375 logs):

| point | Valid | shown above | failing (per population) | infeasible (95 % CI) | M* - point |
|---|---|---|---|---|---|
| B4@0.05 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.2019 [0.1816, 0.2236] | -0.0155 |
| B4@0.04 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,HK1c,FamFlag | 0.2645 [0.2417, 0.2904] | -0.0781 |
| B4@0.03 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag | 0.3523 [0.3262, 0.3806] | -0.1660 |
| B4@0.02 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag | 0.4750 [0.4472, 0.5050] | -0.2887 |
| B4@0.015 | False | True | PD7: NoFlag,FamFlag; SD1: ,FamFlag | 0.5677 [0.5378, 0.5978] | -0.3813 |
| B4@0.01 | True | False | - | 0.6951 [0.6674, 0.7229] | -0.5088 |
| B4@0.005 | False | False | SD1: Floor | 0.9106 [0.8940, 0.9263] | -0.7243 |
| B4 at delta' 0.0025, 0.001 | not fittable (see JSON: not_fittable) | | | | |
| B6@0.05 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,FamFlag | 0.1653 [0.1484, 0.1836] | 0.0211 |
| B6@0.04 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag | 0.2337 [0.2123, 0.2569] | -0.0473 |
| B6@0.03 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag | 0.3327 [0.3070, 0.3616] | -0.1464 |
| B6@0.02 | False | True | PD7: NoFlag,FamFlag | 0.4926 [0.4627, 0.5226] | -0.3062 |
| B6@0.015 | False | True | PD7: ,FamFlag | 0.5572 [0.5266, 0.5885] | -0.3708 |
| B6@0.01 | True | False | - | 0.6784 [0.6502, 0.7065] | -0.4920 |
| B6@0.005 | False | False | SD1: Floor | 0.8631 [0.8440, 0.8819] | -0.6768 |
| B6 at delta' 0.0025, 0.001 | not fittable (see JSON: not_fittable) | | | | |
| B9@0.05 | False | True | PD7: NoFlag,FamFlag | 0.6928 [0.6659, 0.7198] | -0.5064 |
| B9@0.04 | False | True | PD7: NoFlag,FamFlag | 0.7261 [0.7005, 0.7523] | -0.5398 |
| B9@0.03 | False | True | PD7: NoFlag,FamFlag | 0.7659 [0.7419, 0.7898] | -0.5795 |
| B9@0.02 | True | False | - | 0.8216 [0.8001, 0.8420] | -0.6352 |
| B9@0.015 | False | False | SD1: Floor | 0.8546 [0.8343, 0.8730] | -0.6682 |
| B9@0.01 | False | False | SD1: Floor | 0.8956 [0.8788, 0.9111] | -0.7092 |
| B9@0.005 | False | False | SD1: NoFlag_pool,Floor,HK1c | 0.9724 [0.9638, 0.9803] | -0.7860 |
| B9 at delta' 0.0025, 0.001 | not fittable (see JSON: not_fittable) | | | | |

## T3

M* infeasible rate 0.2466.

| family | per-fold choice (0..4) | none qualifies | composite Valid | composite shown above | composite infeasible | M* - composite (95 % CI) |
|---|---|---|---|---|---|---|
| B4 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.8647 | -0.6181 [-0.6408, -0.5954] |
| B6 | 0.015, 0.015, 0.015, 0.015, 0.015 | - | True | False | 0.4862 | -0.2396 [-0.2559, -0.2237] |
| B9 | 0.005, 0.005, 0.005, 0.005, 0.005 | 0, 1, 2, 3, 4 | False | False | 0.9715 | -0.7249 [-0.7461, -0.7037] |
| B0 (RETUNED-HK1 of record) | B0a8, B0a8, B0a8, B0a8, B0a8 | 0, 1, 2, 3, 4 | False | False | 0.9770 | -0.7303 [-0.7513, -0.7091] |

Whole curve (in-sample, all 375 logs):

| point | Valid | shown above | failing (per population) | infeasible (95 % CI) | M* - point |
|---|---|---|---|---|---|
| B4@0.05 | False | True | PD7: NoFlag,NoFlag_pool,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.3152 [0.2923, 0.3382] | -0.0686 |
| B4@0.04 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.3824 [0.3575, 0.4072] | -0.1357 |
| B4@0.03 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,FamFlag | 0.4679 [0.4411, 0.4945] | -0.2213 |
| B4@0.02 | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag | 0.5659 [0.5392, 0.5925] | -0.3193 |
| B4@0.015 | False | True | PD7: NoFlag,FamFlag | 0.6331 [0.6062, 0.6588] | -0.3865 |
| B4@0.01 | False | True | PD7: NoFlag,FamFlag; SD1: Floor | 0.7206 [0.6960, 0.7442] | -0.4740 |
| B4@0.005 | False | False | SD1: Floor | 0.8647 [0.8462, 0.8823] | -0.6181 |
| B4 at delta' 0.0025, 0.001 | not fittable (see JSON: not_fittable) | | | | |
| B6@0.05 | False | True | PD7: NoFlag,FamFlag; PD: NoFlag | 0.2286 [0.2079, 0.2498] | 0.0180 |
| B6@0.04 | False | True | PD7: NoFlag,FamFlag | 0.2627 [0.2415, 0.2851] | -0.0161 |
| B6@0.03 | False | True | PD7: NoFlag,FamFlag | 0.3215 [0.2983, 0.3449] | -0.0749 |
| B6@0.02 | False | True | PD7: NoFlag,FamFlag | 0.4296 [0.4045, 0.4545] | -0.1829 |
| B6@0.015 | True | False | - | 0.4862 [0.4605, 0.5117] | -0.2396 |
| B6@0.01 | True | False | - | 0.6246 [0.5987, 0.6496] | -0.3780 |
| B6@0.005 | False | False | SD1: Floor | 0.8759 [0.8575, 0.8931] | -0.6292 |
| B6 at delta' 0.0025, 0.001 | not fittable (see JSON: not_fittable) | | | | |
| B9@0.05 | False | True | PD7: NoFlag,FamFlag | 0.6629 [0.6349, 0.6905] | -0.4163 |
| B9@0.04 | False | True | PD7: NoFlag,FamFlag | 0.7073 [0.6801, 0.7342] | -0.4607 |
| B9@0.03 | False | True | PD7: NoFlag,FamFlag | 0.7531 [0.7276, 0.7772] | -0.5064 |
| B9@0.02 | True | False | - | 0.8174 [0.7943, 0.8388] | -0.5708 |
| B9@0.015 | False | False | SD1: Floor | 0.8573 [0.8367, 0.8765] | -0.6107 |
| B9@0.01 | False | False | SD1: Floor | 0.9069 [0.8911, 0.9218] | -0.6602 |
| B9@0.005 | False | False | SD1: NoFlag_pool,Floor,HK1c | 0.9715 [0.9627, 0.9793] | -0.7249 |
| B9 at delta' 0.0025, 0.001 | not fittable (see JSON: not_fittable) | | | | |

Not fittable: the frozen CRC rule gives no threshold when the calibration logs n satisfy 1/(n + 1) > delta' (300 logs per training split: delta' = 0.0025 needs n >= 399 and 0.001 needs n >= 999); details per fold and step in the fits summaries.
