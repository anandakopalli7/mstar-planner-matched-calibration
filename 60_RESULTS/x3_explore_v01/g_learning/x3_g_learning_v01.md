# X3 analysis (g): the learning curve of M*

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Screen: the registered screen as coded, each arm judged like RETUNED-HK1 of record (flags at 0.95, power datasets 500); B = 4000; M* of record screened with the same seeds as the reference row. Infeasible rate: mean over logs of the per-log share; M* - arm: per-log paired difference, percentile log bootstrap. Pooled exceedance: the relied-item exceedance per population.

## T1

| arm | Valid | shown above | failing | infeasible (95 % CI) | M* - arm (95 % CI) | pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|
| Mstar (M* of record) | True | False | - | 0.1864 [0.1682, 0.2053] | - | 0.0440 / 0.0376 / 0.0404 |
| X3G_n25_r1 (n = 25 training logs per fold, repeat 1) | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag | 0.4316 [0.4034, 0.4603] | -0.2452 [-0.2672, -0.2239] | 0.0158 / 0.0160 / 0.0292 |
| X3G_n50_r0 (n = 50 training logs per fold, repeat 0) | False | True | PD7: NoFlag; PD: NoFlag | 0.3018 [0.2779, 0.3260] | -0.1154 [-0.1298, -0.1013] | 0.0313 / 0.0288 / 0.0418 |
| X3G_n50_r1 (n = 50 training logs per fold, repeat 1) | False | True | PD7: NoFlag | 0.2690 [0.2467, 0.2917] | -0.0826 [-0.0957, -0.0695] | 0.0298 / 0.0250 / 0.0348 |
| X3G_n50_r2 (n = 50 training logs per fold, repeat 2) | True | False | - | 0.2797 [0.2562, 0.3030] | -0.0933 [-0.1074, -0.0796] | 0.0298 / 0.0255 / 0.0304 |
| X3G_n100_r0 (n = 100 training logs per fold, repeat 0) | False | True | PD7: NoFlag | 0.2323 [0.2113, 0.2541] | -0.0459 [-0.0556, -0.0365] | 0.0376 / 0.0313 / 0.0436 |
| X3G_n100_r1 (n = 100 training logs per fold, repeat 1) | False | True | PD7: NoFlag | 0.2028 [0.1844, 0.2221] | -0.0165 [-0.0232, -0.0097] | 0.0393 / 0.0355 / 0.0380 |
| X3G_n100_r2 (n = 100 training logs per fold, repeat 2) | True | False | - | 0.2214 [0.2022, 0.2413] | -0.0350 [-0.0428, -0.0277] | 0.0383 / 0.0307 / 0.0410 |
| X3G_n200_r0 (n = 200 training logs per fold, repeat 0) | True | False | - | 0.1955 [0.1770, 0.2151] | -0.0092 [-0.0144, -0.0038] | 0.0417 / 0.0358 / 0.0396 |
| X3G_n200_r1 (n = 200 training logs per fold, repeat 1) | True | False | - | 0.1911 [0.1728, 0.2106] | -0.0047 [-0.0098, 0.0002] | 0.0428 / 0.0342 / 0.0373 |
| X3G_n200_r2 (n = 200 training logs per fold, repeat 2) | True | False | - | 0.1980 [0.1792, 0.2178] | -0.0116 [-0.0165, -0.0068] | 0.0425 / 0.0363 / 0.0346 |

Fallback (share of the 192 x 4 thresholds per fold whose source is coarser than the own L0 stratum, mean over folds; n = 300 = the fit of record, identical: True, share 0.484):

| composite | fallback share | undefined share |
|---|---|---|
| X3G_n25_r0 | 0.907 | 0.013 |
| X3G_n25_r1 | 0.913 | 0.000 |
| X3G_n25_r2 | 0.802 | 0.138 |
| X3G_n50_r0 | 0.752 | 0.000 |
| X3G_n50_r1 | 0.760 | 0.000 |
| X3G_n50_r2 | 0.754 | 0.000 |
| X3G_n100_r0 | 0.653 | 0.000 |
| X3G_n100_r1 | 0.649 | 0.000 |
| X3G_n100_r2 | 0.645 | 0.000 |
| X3G_n200_r0 | 0.567 | 0.000 |
| X3G_n200_r1 | 0.563 | 0.000 |
| X3G_n200_r2 | 0.560 | 0.000 |

Not fittable (a threshold with no level of 19 logs), not run: X3G_n25_r0, X3G_n25_r2.

## T3

| arm | Valid | shown above | failing | infeasible (95 % CI) | M* - arm (95 % CI) | pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|
| Mstar (M* of record) | True | False | - | 0.2466 [0.2255, 0.2680] | - | 0.0430 / 0.0324 / 0.0405 |
| X3G_n50_r0 (n = 50 training logs per fold, repeat 0) | True | False | - | 0.3651 [0.3411, 0.3897] | -0.1185 [-0.1305, -0.1069] | 0.0315 / 0.0263 / 0.0300 |
| X3G_n50_r1 (n = 50 training logs per fold, repeat 1) | True | False | - | 0.3762 [0.3523, 0.4001] | -0.1296 [-0.1426, -0.1172] | 0.0304 / 0.0221 / 0.0279 |
| X3G_n50_r2 (n = 50 training logs per fold, repeat 2) | True | False | - | 0.3764 [0.3517, 0.4015] | -0.1298 [-0.1420, -0.1170] | 0.0285 / 0.0232 / 0.0235 |
| X3G_n100_r0 (n = 100 training logs per fold, repeat 0) | False | True | PD7: NoFlag | 0.3010 [0.2788, 0.3238] | -0.0543 [-0.0618, -0.0471] | 0.0370 / 0.0275 / 0.0370 |
| X3G_n100_r1 (n = 100 training logs per fold, repeat 1) | True | False | - | 0.2919 [0.2696, 0.3144] | -0.0453 [-0.0533, -0.0377] | 0.0389 / 0.0306 / 0.0372 |
| X3G_n100_r2 (n = 100 training logs per fold, repeat 2) | True | False | - | 0.3025 [0.2799, 0.3250] | -0.0558 [-0.0624, -0.0491] | 0.0376 / 0.0273 / 0.0376 |
| X3G_n200_r0 (n = 200 training logs per fold, repeat 0) | True | False | - | 0.2641 [0.2429, 0.2857] | -0.0175 [-0.0223, -0.0128] | 0.0411 / 0.0315 / 0.0389 |
| X3G_n200_r1 (n = 200 training logs per fold, repeat 1) | True | False | - | 0.2538 [0.2325, 0.2755] | -0.0072 [-0.0113, -0.0033] | 0.0425 / 0.0307 / 0.0394 |
| X3G_n200_r2 (n = 200 training logs per fold, repeat 2) | True | False | - | 0.2608 [0.2396, 0.2822] | -0.0141 [-0.0191, -0.0091] | 0.0424 / 0.0336 / 0.0400 |

Fallback (share of the 192 x 4 thresholds per fold whose source is coarser than the own L0 stratum, mean over folds; n = 300 = the fit of record, identical: True, share 0.483):

| composite | fallback share | undefined share |
|---|---|---|
| X3G_n25_r0 | 0.847 | 0.062 |
| X3G_n25_r1 | 0.859 | 0.050 |
| X3G_n25_r2 | 0.797 | 0.138 |
| X3G_n50_r0 | 0.748 | 0.000 |
| X3G_n50_r1 | 0.758 | 0.000 |
| X3G_n50_r2 | 0.753 | 0.000 |
| X3G_n100_r0 | 0.653 | 0.000 |
| X3G_n100_r1 | 0.647 | 0.000 |
| X3G_n100_r2 | 0.643 | 0.000 |
| X3G_n200_r0 | 0.560 | 0.000 |
| X3G_n200_r1 | 0.562 | 0.000 |
| X3G_n200_r2 | 0.555 | 0.000 |

Not fittable (a threshold with no level of 19 logs), not run: X3G_n25_r0, X3G_n25_r1, X3G_n25_r2.
