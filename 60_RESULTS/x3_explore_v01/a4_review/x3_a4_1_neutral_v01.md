# X3 A4 (1): matched validity on the neutral screen

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

Neutral screen: no flagged cell of P1-P7 in P_rel, P_near or P_ip (one-sided simultaneous 0.95 per partition and population, >= 39 logs) and HK1c (pooled upper bound at 0.995 <= 0.08) on each population; no power floor (evaluable partition cells counted). Selection per held-out fold on the other four folds; no point -> 'no matched point' (no conservative substitute). Seeds [20261201, i, 11] / [20261202, i, 11]; B = 4000.

## T1

| family | per-fold choice | result | in-sample best | composite neutral | composite registered | infeasible | progress | mean back-off | V2_exec | M* - composite infeasible (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | matched | Mstar@0.03 | True | Valid | 0.2603 | 0.9657 | 0.8480 | 0.4480 | - |
| B4 | B4@0.015, B4@0.02, B4@0.02, B4@0.015, B4@0.015 | matched | B4@0.015 | True | flagged | 0.5327 | 0.9537 | 0.6836 | 0.4295 | -0.2723 [-0.2992, -0.2457] |
| B6 | B6@0.02, B6@0.02, B6@0.02, B6@0.02, B6@0.02 | matched | B6@0.02 | True | flagged | 0.4926 | 0.9554 | 0.6974 | 0.4607 | -0.2323 [-0.2579, -0.2075] |
| B9 | B9@0.05, B9@0.05, B9@0.05, B9@0.04, B9@0.05 | matched | B9@0.05 | True | flagged | 0.6998 | 0.9555 | 0.4987 | 0.5256 | -0.4395 [-0.4649, -0.4146] |
| B0 | B0d0.005, B0a2, B0a2, B0d0.005, B0a3 | matched | B0d0.005 | True | flagged | 0.5624 | 0.9522 | 0.6615 | 0.4538 | -0.3021 [-0.3296, -0.2753] |

Every point (in-sample, all 375 logs): neutral pass / flagged cells / HK1c by population / evaluable partition cells; endpoints.

| point | neutral pass | flagged cells | HK1c P_rel / P_near / P_ip (UB) | evaluable cells | infeasible | progress | mean back-off | V2_exec |
|---|---|---|---|---|---|---|---|---|
| Mstar@0.05 | False | 5 | True (0.048) / True (0.047) / True (0.054) | 154 | 0.1864 | 0.9723 | 0.8967 | 0.5509 |
| Mstar@0.04 | False | 3 | True (0.038) / True (0.036) / True (0.041) | 154 | 0.2181 | 0.9687 | 0.8762 | 0.5024 |
| Mstar@0.03 | True | 0 | True (0.029) / True (0.027) / True (0.033) | 154 | 0.2603 | 0.9657 | 0.8480 | 0.4480 |
| Mstar@0.02 | True | 0 | True (0.018) / True (0.016) / True (0.020) | 153 | 0.3429 | 0.9599 | 0.7902 | 0.4088 |
| Mstar@0.015 | True | 0 | True (0.013) / True (0.012) / True (0.018) | 153 | 0.3809 | 0.9570 | 0.7639 | 0.3760 |
| Mstar@0.01 | True | 0 | True (0.008) / True (0.010) / True (0.010) | 152 | 0.5059 | 0.9547 | 0.6811 | 0.3733 |
| Mstar@0.005 | True | 0 | True (0.003) / True (0.006) / True (0.002) | 145 | 0.8330 | 0.9551 | 0.3676 | 0.4980 |
| B4@0.05 | False | 39 | True (0.059) / True (0.046) / False (0.098) | 154 | 0.2019 | 0.9725 | 0.8885 | 0.5783 |
| B4@0.04 | False | 16 | True (0.047) / True (0.038) / False (0.080) | 154 | 0.2645 | 0.9669 | 0.8562 | 0.5312 |
| B4@0.03 | False | 8 | True (0.034) / True (0.032) / True (0.060) | 153 | 0.3523 | 0.9630 | 0.8048 | 0.4836 |
| B4@0.02 | False | 1 | True (0.022) / True (0.024) / True (0.041) | 153 | 0.4750 | 0.9574 | 0.7250 | 0.4393 |
| B4@0.015 | True | 0 | True (0.016) / True (0.018) / True (0.031) | 152 | 0.5677 | 0.9526 | 0.6576 | 0.4251 |
| B4@0.01 | True | 0 | True (0.010) / True (0.015) / True (0.017) | 148 | 0.6951 | 0.9495 | 0.5367 | 0.4457 |
| B4@0.005 | True | 0 | True (0.003) / True (0.009) / True (0.005) | 137 | 0.9106 | 0.9567 | 0.2802 | 0.5472 |
| B6@0.05 | False | 15 | True (0.053) / True (0.052) / True (0.062) | 153 | 0.1653 | 0.9711 | 0.9114 | 0.5484 |
| B6@0.04 | False | 8 | True (0.042) / True (0.042) / True (0.050) | 153 | 0.2337 | 0.9660 | 0.8790 | 0.4984 |
| B6@0.03 | False | 2 | True (0.031) / True (0.032) / True (0.040) | 153 | 0.3327 | 0.9615 | 0.8236 | 0.4528 |
| B6@0.02 | True | 0 | True (0.020) / True (0.018) / True (0.024) | 153 | 0.4926 | 0.9554 | 0.6974 | 0.4607 |
| B6@0.015 | True | 0 | True (0.014) / True (0.014) / True (0.021) | 152 | 0.5572 | 0.9543 | 0.6205 | 0.4589 |
| B6@0.01 | True | 0 | True (0.009) / True (0.010) / True (0.011) | 150 | 0.6784 | 0.9539 | 0.5271 | 0.4763 |
| B6@0.005 | True | 0 | True (0.003) / True (0.008) / True (0.002) | 139 | 0.8631 | 0.9567 | 0.3368 | 0.5082 |
| B9@0.05 | True | 0 | True (0.014) / True (0.008) / True (0.030) | 153 | 0.6928 | 0.9552 | 0.5048 | 0.5266 |
| B9@0.04 | True | 0 | True (0.011) / True (0.007) / True (0.020) | 152 | 0.7261 | 0.9538 | 0.4725 | 0.5226 |
| B9@0.03 | True | 0 | True (0.008) / True (0.005) / True (0.015) | 152 | 0.7659 | 0.9538 | 0.4328 | 0.5284 |
| B9@0.02 | True | 0 | True (0.005) / True (0.004) / True (0.008) | 150 | 0.8216 | 0.9571 | 0.3762 | 0.5435 |
| B9@0.015 | True | 0 | True (0.004) / True (0.004) / True (0.004) | 148 | 0.8546 | 0.9575 | 0.3389 | 0.5511 |
| B9@0.01 | True | 0 | True (0.002) / True (0.004) / True (0.002) | 141 | 0.8956 | 0.9604 | 0.2853 | 0.5650 |
| B9@0.005 | False | 0 | True (0.000) / n.e. / True (0.000) | 84 | 0.9724 | 0.9747 | 0.1248 | 0.7121 |
| B0d0.5 | False | 155 | False (0.505) / False (0.505) / False (0.496) | 155 | 0.0042 | 0.9941 | 0.9958 | 0.9756 |
| B0a0.03125 | False | 146 | False (0.196) / False (0.181) / False (0.276) | 155 | 0.0373 | 0.9885 | 0.9776 | 0.8956 |
| B0a0.0625 | False | 137 | False (0.157) / False (0.137) / False (0.234) | 155 | 0.0581 | 0.9860 | 0.9658 | 0.8501 |
| B0d0.3 | False | 122 | False (0.130) / False (0.107) / False (0.200) | 155 | 0.0765 | 0.9835 | 0.9553 | 0.8057 |
| B0a0.125 | False | 111 | False (0.120) / False (0.097) / False (0.187) | 155 | 0.0846 | 0.9822 | 0.9501 | 0.7815 |
| B0a0.25 | False | 80 | False (0.088) / True (0.070) / False (0.143) | 155 | 0.1358 | 0.9766 | 0.9230 | 0.6955 |
| B0d0.2 | False | 77 | False (0.086) / True (0.068) / False (0.139) | 155 | 0.1404 | 0.9762 | 0.9207 | 0.6898 |
| B0a0.333 | False | 70 | True (0.076) / True (0.060) / False (0.122) | 155 | 0.1695 | 0.9732 | 0.9059 | 0.6550 |
| B0a0.5 | False | 43 | True (0.061) / True (0.049) / False (0.103) | 154 | 0.2323 | 0.9695 | 0.8743 | 0.6000 |
| B0d0.1 | False | 30 | True (0.054) / True (0.042) / False (0.093) | 154 | 0.2714 | 0.9665 | 0.8544 | 0.5726 |
| B0a1 | False | 11 | True (0.038) / True (0.033) / True (0.067) | 153 | 0.3711 | 0.9609 | 0.7949 | 0.5153 |
| B0d0.05 | False | 11 | True (0.038) / True (0.033) / True (0.067) | 153 | 0.3711 | 0.9609 | 0.7949 | 0.5153 |
| B0d0.02 | False | 1 | True (0.026) / True (0.026) / True (0.049) | 153 | 0.4682 | 0.9572 | 0.7313 | 0.4761 |
| B0a2 | False | 1 | True (0.021) / True (0.021) / True (0.041) | 153 | 0.5250 | 0.9544 | 0.6900 | 0.4609 |
| B0d0.01 | False | 1 | True (0.021) / True (0.021) / True (0.041) | 153 | 0.5250 | 0.9544 | 0.6900 | 0.4608 |
| B0d0.005 | True | 0 | True (0.018) / True (0.019) / True (0.035) | 153 | 0.5701 | 0.9519 | 0.6552 | 0.4484 |
| B0a3 | True | 0 | True (0.015) / True (0.017) / True (0.031) | 152 | 0.6061 | 0.9519 | 0.6219 | 0.4458 |
| B0d0.001 | True | 0 | True (0.013) / True (0.019) / True (0.026) | 151 | 0.6375 | 0.9515 | 0.5936 | 0.4429 |
| B0a4 | True | 0 | True (0.012) / True (0.017) / True (0.024) | 150 | 0.6603 | 0.9507 | 0.5701 | 0.4490 |
| B0a5 | True | 0 | True (0.010) / True (0.015) / True (0.020) | 149 | 0.7010 | 0.9495 | 0.5307 | 0.4529 |
| B0a8 | True | 0 | True (0.007) / True (0.012) / True (0.015) | 146 | 0.7810 | 0.9495 | 0.4445 | 0.4686 |

## T3

| family | per-fold choice | result | in-sample best | composite neutral | composite registered | infeasible | progress | mean back-off | V2_exec | M* - composite infeasible (95 % CI) |
|---|---|---|---|---|---|---|---|---|---|---|
| Mstar | Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03, Mstar@0.03 | matched | Mstar@0.03 | True | Valid | 0.3505 | 0.9663 | 0.7843 | 0.5044 | - |
| B4 | B4@0.01, B4@0.01, B4@0.015, B4@0.01, B4@0.01 | matched | B4@0.01 | True | flagged | 0.7010 | 0.9618 | 0.4878 | 0.5172 | -0.3505 [-0.3739, -0.3284] |
| B6 | B6@0.02, B6@0.02, B6@0.02, B6@0.02, B6@0.02 | matched | B6@0.02 | True | flagged | 0.4296 | 0.9615 | 0.7430 | 0.4499 | -0.0790 [-0.0921, -0.0669] |
| B9 | B9@0.05, B9@0.04, B9@0.05, B9@0.04, B9@0.04 | matched | B9@0.04 | True | flagged | 0.6919 | 0.9578 | 0.5093 | 0.5257 | -0.3414 [-0.3713, -0.3132] |
| B0 | B0a0.333, B0a0.333, B0a0.333, B0a0.333, B0a0.333 | matched | B0a0.333 | True | flagged | 0.7324 | 0.9596 | 0.4656 | 0.5566 | -0.3818 [-0.4056, -0.3595] |

Every point (in-sample, all 375 logs): neutral pass / flagged cells / HK1c by population / evaluable partition cells; endpoints.

| point | neutral pass | flagged cells | HK1c P_rel / P_near / P_ip (UB) | evaluable cells | infeasible | progress | mean back-off | V2_exec |
|---|---|---|---|---|---|---|---|---|
| Mstar@0.05 | False | 5 | True (0.047) / True (0.041) / True (0.052) | 153 | 0.2466 | 0.9731 | 0.8585 | 0.5805 |
| Mstar@0.04 | False | 2 | True (0.038) / True (0.033) / True (0.040) | 153 | 0.2948 | 0.9708 | 0.8256 | 0.5429 |
| Mstar@0.03 | True | 0 | True (0.028) / True (0.024) / True (0.032) | 153 | 0.3505 | 0.9663 | 0.7843 | 0.5044 |
| Mstar@0.02 | True | 0 | True (0.018) / True (0.014) / True (0.019) | 153 | 0.4429 | 0.9631 | 0.7208 | 0.4665 |
| Mstar@0.015 | True | 0 | True (0.014) / True (0.011) / True (0.016) | 152 | 0.5188 | 0.9601 | 0.6730 | 0.4538 |
| Mstar@0.01 | True | 0 | True (0.008) / True (0.006) / True (0.007) | 150 | 0.6148 | 0.9582 | 0.5802 | 0.4611 |
| Mstar@0.005 | True | 0 | True (0.003) / True (0.003) / True (0.001) | 136 | 0.8813 | 0.9674 | 0.2902 | 0.5826 |
| B4@0.05 | False | 62 | True (0.067) / True (0.052) / False (0.135) | 154 | 0.3152 | 0.9694 | 0.8018 | 0.6425 |
| B4@0.04 | False | 40 | True (0.055) / True (0.036) / False (0.099) | 153 | 0.3824 | 0.9660 | 0.7566 | 0.5995 |
| B4@0.03 | False | 21 | True (0.042) / True (0.029) / True (0.075) | 154 | 0.4679 | 0.9642 | 0.6950 | 0.5627 |
| B4@0.02 | False | 4 | True (0.027) / True (0.019) / True (0.047) | 152 | 0.5659 | 0.9614 | 0.6107 | 0.5252 |
| B4@0.015 | False | 1 | True (0.019) / True (0.015) / True (0.031) | 152 | 0.6331 | 0.9608 | 0.5536 | 0.5164 |
| B4@0.01 | True | 0 | True (0.011) / True (0.007) / True (0.017) | 150 | 0.7206 | 0.9615 | 0.4711 | 0.5152 |
| B4@0.005 | True | 0 | True (0.003) / True (0.004) / True (0.002) | 141 | 0.8647 | 0.9684 | 0.2909 | 0.5892 |
| B6@0.05 | False | 16 | True (0.053) / True (0.046) / True (0.056) | 153 | 0.2286 | 0.9734 | 0.8657 | 0.5969 |
| B6@0.04 | False | 6 | True (0.042) / True (0.038) / True (0.043) | 153 | 0.2627 | 0.9688 | 0.8419 | 0.5488 |
| B6@0.03 | False | 2 | True (0.032) / True (0.029) / True (0.033) | 153 | 0.3215 | 0.9657 | 0.8058 | 0.4984 |
| B6@0.02 | True | 0 | True (0.020) / True (0.021) / True (0.019) | 152 | 0.4296 | 0.9615 | 0.7430 | 0.4499 |
| B6@0.015 | True | 0 | True (0.015) / True (0.016) / True (0.015) | 151 | 0.4862 | 0.9591 | 0.7027 | 0.4307 |
| B6@0.01 | True | 0 | True (0.009) / True (0.008) / True (0.007) | 150 | 0.6246 | 0.9556 | 0.5966 | 0.4406 |
| B6@0.005 | True | 0 | True (0.003) / True (0.003) / True (0.001) | 134 | 0.8759 | 0.9640 | 0.3110 | 0.5472 |
| B9@0.05 | False | 1 | True (0.016) / True (0.007) / True (0.022) | 153 | 0.6629 | 0.9587 | 0.5338 | 0.5230 |
| B9@0.04 | True | 0 | True (0.013) / True (0.006) / True (0.018) | 150 | 0.7073 | 0.9579 | 0.4929 | 0.5242 |
| B9@0.03 | True | 0 | True (0.009) / True (0.004) / True (0.013) | 148 | 0.7531 | 0.9576 | 0.4447 | 0.5295 |
| B9@0.02 | True | 0 | True (0.006) / True (0.004) / True (0.007) | 148 | 0.8174 | 0.9602 | 0.3792 | 0.5429 |
| B9@0.015 | True | 0 | True (0.005) / True (0.003) / True (0.006) | 146 | 0.8573 | 0.9605 | 0.3348 | 0.5536 |
| B9@0.01 | True | 0 | True (0.003) / True (0.002) / True (0.002) | 138 | 0.9069 | 0.9662 | 0.2707 | 0.5749 |
| B9@0.005 | False | 0 | True (0.001) / n.e. / True (0.000) | 85 | 0.9715 | 0.9771 | 0.1277 | 0.7094 |
| B0d0.5 | False | 155 | False (0.509) / False (0.492) / False (0.506) | 155 | 0.0024 | 0.9956 | 0.9976 | 0.9785 |
| B0a0.03125 | False | 64 | True (0.073) / True (0.051) / False (0.145) | 154 | 0.3287 | 0.9666 | 0.7943 | 0.6797 |
| B0a0.0625 | False | 35 | True (0.052) / True (0.034) / False (0.098) | 154 | 0.4476 | 0.9632 | 0.7128 | 0.6157 |
| B0d0.3 | False | 16 | True (0.039) / True (0.025) / True (0.073) | 152 | 0.5275 | 0.9602 | 0.6477 | 0.5835 |
| B0a0.125 | False | 10 | True (0.034) / True (0.021) / True (0.063) | 152 | 0.5647 | 0.9601 | 0.6184 | 0.5717 |
| B0a0.25 | False | 2 | True (0.020) / True (0.013) / True (0.032) | 152 | 0.6936 | 0.9592 | 0.5099 | 0.5578 |
| B0d0.2 | False | 2 | True (0.020) / True (0.013) / True (0.032) | 152 | 0.7004 | 0.9590 | 0.5028 | 0.5577 |
| B0a0.333 | True | 0 | True (0.016) / True (0.011) / True (0.025) | 151 | 0.7324 | 0.9596 | 0.4656 | 0.5566 |
| B0a0.5 | True | 0 | True (0.011) / True (0.010) / True (0.015) | 150 | 0.7806 | 0.9613 | 0.4040 | 0.5630 |
| B0d0.1 | True | 0 | True (0.009) / True (0.008) / True (0.012) | 150 | 0.8012 | 0.9606 | 0.3745 | 0.5753 |
| B0a1 | True | 0 | True (0.005) / True (0.006) / True (0.005) | 147 | 0.8575 | 0.9652 | 0.3020 | 0.6042 |
| B0d0.05 | True | 0 | True (0.005) / True (0.006) / True (0.005) | 147 | 0.8575 | 0.9652 | 0.3020 | 0.6042 |
| B0d0.02 | True | 0 | True (0.003) / True (0.006) / True (0.003) | 146 | 0.9041 | 0.9678 | 0.2449 | 0.6351 |
| B0a2 | True | 0 | True (0.003) / True (0.006) / True (0.003) | 145 | 0.9217 | 0.9703 | 0.2151 | 0.6548 |
| B0d0.01 | True | 0 | True (0.003) / True (0.006) / True (0.003) | 145 | 0.9217 | 0.9703 | 0.2151 | 0.6548 |
| B0d0.005 | True | 0 | True (0.002) / True (0.004) / True (0.001) | 142 | 0.9363 | 0.9710 | 0.1909 | 0.6779 |
| B0a3 | True | 0 | True (0.002) / True (0.004) / True (0.001) | 139 | 0.9469 | 0.9731 | 0.1688 | 0.6975 |
| B0d0.001 | True | 0 | True (0.002) / True (0.002) / True (0.001) | 135 | 0.9530 | 0.9751 | 0.1528 | 0.7159 |
| B0a4 | True | 0 | True (0.002) / True (0.003) / True (0.000) | 128 | 0.9567 | 0.9765 | 0.1404 | 0.7295 |
| B0a5 | True | 0 | True (0.001) / True (0.020) / True (0.000) | 106 | 0.9657 | 0.9786 | 0.1203 | 0.7498 |
| B0a8 | False | 0 | True (0.001) / n.e. / True (0.000) | 93 | 0.9770 | 0.9825 | 0.0897 | 0.7903 |

## (a) re-read on the registered screen (classes: Valid / flagged / fails HK1c only / fails a floor only; contrasts only for passing composites)

- T1 B4: composite {'0': 'B4@0.005', '1': 'B4@0.005', '2': 'B4@0.005', '3': 'B4@0.005', '4': 'B4@0.005'} -> fails a floor only (infeasible 0.9106); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 flagged, 0.01 Valid, 0.005 fails a floor only
- T1 B6: composite {'0': 'B6@0.015', '1': 'B6@0.005', '2': 'B6@0.015', '3': 'B6@0.015', '4': 'B6@0.015'} -> Valid (infeasible 0.6226); M* - composite -0.4362 [-0.4634, -0.4098]; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 flagged, 0.01 Valid, 0.005 fails a floor only
- T1 B9: composite {'0': 'B9@0.005', '1': 'B9@0.005', '2': 'B9@0.005', '3': 'B9@0.005', '4': 'B9@0.005'} -> fails HK1c and a floor (infeasible 0.9724); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 Valid, 0.015 fails a floor only, 0.01 fails a floor only, 0.005 fails HK1c and a floor
- T3 B4: composite {'0': 'B4@0.005', '1': 'B4@0.005', '2': 'B4@0.005', '3': 'B4@0.005', '4': 'B4@0.005'} -> fails a floor only (infeasible 0.8647); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 flagged, 0.01 flagged, 0.005 fails a floor only
- T3 B6: composite {'0': 'B6@0.015', '1': 'B6@0.015', '2': 'B6@0.015', '3': 'B6@0.015', '4': 'B6@0.015'} -> Valid (infeasible 0.4862); M* - composite -0.2396 [-0.2559, -0.2237]; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 flagged, 0.015 Valid, 0.01 Valid, 0.005 fails a floor only
- T3 B9: composite {'0': 'B9@0.005', '1': 'B9@0.005', '2': 'B9@0.005', '3': 'B9@0.005', '4': 'B9@0.005'} -> fails HK1c and a floor (infeasible 0.9715); no contrast: the composite does not pass; curve: 0.05 flagged, 0.04 flagged, 0.03 flagged, 0.02 Valid, 0.015 fails a floor only, 0.01 fails a floor only, 0.005 fails HK1c and a floor
