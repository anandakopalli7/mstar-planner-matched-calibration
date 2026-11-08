# X3 analysis (e): the obvious alternatives (e2 Q-refit, e1 B5 / B8 / B7)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Screen: the registered screen as coded, each arm judged like RETUNED-HK1 of record (flags at 0.95, power datasets 500); B = 4000; M* of record screened with the same seeds as the reference row. Infeasible rate: mean over logs of the per-log share; M* - arm: per-log paired difference, percentile log bootstrap. Pooled exceedance: the relied-item exceedance per population.

e2: B0's margin rule (z_0.95 sd) on the substituted covariances A + q (S - A) of x3-ref (plan grid; amendment A2's extended grid with q = 0). e1: B5, B8, B7 fitted by m_lib_v04's rules (exact CRC; per step and in-path part as M*); B5 and B8 run through k8_sim_v04's per-(L0, in-path) threshold x sd form, B7 through x3_run_v02's margin rule B7.

## T1

Check: B0 on the cache's own covariance reproduces B0 of record exactly (375 logs): **True**. B7 runner margins equal the fit's item-level margins: **True**.

q (fold x group car / pedestrian / two-wheeler / large), plan grid: {"0": {"0": 0.25, "1": 2.0, "2": 0.25, "3": 0.25}, "1": {"0": 0.25, "1": 1.0, "2": 0.25, "3": 0.25}, "2": {"0": 0.25, "1": 2.0, "2": 0.25, "3": 0.25}, "3": {"0": 0.25, "1": 2.0, "2": 0.25, "3": 0.25}, "4": {"0": 0.25, "1": 4.0, "2": 0.25, "3": 0.25}}; extended grid: {"0": {"0": 0.0, "1": 2.0, "2": 0.125, "3": 0.25}, "1": {"0": 0.0, "1": 1.0, "2": 0.0625, "3": 0.25}, "2": {"0": 0.0, "1": 2.0, "2": 0.125, "3": 0.0625}, "3": {"0": 0.0, "1": 2.0, "2": 0.125, "3": 0.25}, "4": {"0": 0.0, "1": 4.0, "2": 0.125, "3": 0.25}}.

| arm | Valid | shown above | failing | infeasible (95 % CI) | M* - arm (95 % CI) | pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|
| Mstar (M* of record) | True | False | - | 0.1864 [0.1678, 0.2050] | - | 0.0440 / 0.0376 / 0.0404 |
| X3E2_B0_cache_cov (B0 on the cache's own covariance (check)) | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,FamFlag | 0.3711 [0.3435, 0.3990] | -0.1847 [-0.2097, -0.1594] | 0.0337 / 0.0258 / 0.0502 |
| X3E2_B0_qrefit (Q-refit, plan grid) | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.2709 [0.2459, 0.2952] | -0.0846 [-0.1085, -0.0596] | 0.0431 / 0.0318 / 0.0696 |
| X3E2_B0_qrefit_ext (Q-refit, extended grid (amendment A2)) | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,NoFlag_pool,HK1c,FamFlag | 0.2299 [0.2072, 0.2530] | -0.0436 [-0.0668, -0.0199] | 0.0488 / 0.0367 / 0.0803 |
| X3E1_B5 (B5: per-axis CRC scalars) | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag,FamFlag | 0.1668 [0.1493, 0.1840] | 0.0196 [0.0009, 0.0384] | 0.0471 / 0.0473 / 0.0534 |
| X3E1_B8 (B8: stratified variance matching) | True | False | - | 0.2822 [0.2587, 0.3064] | -0.0959 [-0.1091, -0.0836] | 0.0157 / 0.0177 / 0.0291 |
| X3E1_B7 (B7: learned scale) | False | True | PD7: NoFlag,FamFlag | 0.1538 [0.1367, 0.1712] | 0.0325 [0.0180, 0.0471] | 0.0463 / 0.0314 / 0.0485 |

## T3

Check: B0 on the cache's own covariance reproduces B0 of record exactly (375 logs): **True**. B7 runner margins equal the fit's item-level margins: **True**.

q (fold x group car / pedestrian / two-wheeler / large), plan grid: {"0": {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}, "1": {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}, "2": {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}, "3": {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}, "4": {"0": 0.25, "1": 0.25, "2": 0.25, "3": 0.25}}; extended grid: {"0": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0}, "1": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0}, "2": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0}, "3": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0}, "4": {"0": 0.0, "1": 0.0, "2": 0.0, "3": 0.0}}.

| arm | Valid | shown above | failing | infeasible (95 % CI) | M* - arm (95 % CI) | pooled exceedance P_rel / P_near / P_ip |
|---|---|---|---|---|---|---|
| Mstar (M* of record) | True | False | - | 0.2466 [0.2263, 0.2681] | - | 0.0430 / 0.0324 / 0.0405 |
| X3E2_B0_cache_cov (B0 on the cache's own covariance (check)) | False | False | SD1: Floor | 0.8575 [0.8397, 0.8748] | -0.6109 [-0.6341, -0.5888] | 0.0041 / 0.0031 / 0.0030 |
| X3E2_B0_qrefit (Q-refit, plan grid) | False | False | SD1: Floor | 0.8136 [0.7933, 0.8335] | -0.5669 [-0.5902, -0.5443] | 0.0064 / 0.0046 / 0.0065 |
| X3E2_B0_qrefit_ext (Q-refit, extended grid (amendment A2)) | False | False | SD1: Floor | 0.7835 [0.7626, 0.8042] | -0.5369 [-0.5601, -0.5145] | 0.0078 / 0.0060 / 0.0080 |
| X3E1_B5 (B5: per-axis CRC scalars) | False | True | PD7: NoFlag,FamFlag; SD1: NoFlag,FamFlag; PD: NoFlag | 0.2395 [0.2188, 0.2607] | 0.0071 [-0.0023, 0.0166] | 0.0507 / 0.0346 / 0.0534 |
| X3E1_B8 (B8: stratified variance matching) | True | False | - | 0.5074 [0.4818, 0.5339] | -0.2607 [-0.2817, -0.2404] | 0.0148 / 0.0144 / 0.0298 |
| X3E1_B7 (B7: learned scale) | False | True | PD7: NoFlag,FamFlag | 0.2634 [0.2422, 0.2859] | -0.0168 [-0.0296, -0.0040] | 0.0485 / 0.0276 / 0.0532 |
