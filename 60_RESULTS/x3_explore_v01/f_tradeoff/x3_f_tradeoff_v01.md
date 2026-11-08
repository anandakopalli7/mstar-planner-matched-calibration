# X3 (f): the infeasibility-violation trade-off (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan 2(f) (sha256 38e2526d...); referee concern M10. Outputs of record only: within_lt3d, decision mode, 375 logs. V2 = log-mean share of decisions (with a P_rel record) in which some relied constraint is exceeded; V2_viol = the same with a relied constraint violated (D > G); infeasible = log-mean infeasible-decision share. Status of record: comparators of K (B0, B1, B3, B4, B6, B9, RETUNED) judged at their removal level 1 - 0.0125/9, every other arm at 0.95 (c1_analyse_v02.arm_status).

Figures: `x3_f_infeasible_vs_V2_v01.pdf/.png`, `x3_f_infeasible_vs_V2viol_v01.pdf/.png`. JSON: `x3_f_tradeoff_v01.json`.

## Checks against the record

- t1: 449 checks, largest absolute difference 3.33e-16, 0 unchecked (no record value); decision cross-tab: {'infeasible_and_lam1': 0, 'feasible_and_lam_lt1': 0, 'lam_outside_levels': 0, 'decisions': 349928}; episode back-off counts vs decision rows: 0 mismatching levels over 31 arms.
- t3: 449 checks, largest absolute difference 1.11e-16, 0 unchecked (no record value); decision cross-tab: {'infeasible_and_lam1': 0, 'feasible_and_lam_lt1': 0, 'lam_outside_levels': 0, 'decisions': 349928}; episode back-off counts vs decision rows: 0 mismatching levels over 31 arms.
- tab: 449 checks, largest absolute difference 2.22e-16, 0 unchecked (no record value); decision cross-tab: {'infeasible_and_lam1': 0, 'feasible_and_lam_lt1': 0, 'lam_outside_levels': 0, 'decisions': 349928}; episode back-off counts vs decision rows: 0 mismatching levels over 31 arms.

## T1 (CANMOT): every arm

| Arm | Status | Infeasible | V2 | V2_viol |
|---|---|---|---|---|
| Z0 | shown_above | 0.004 | 0.976 | 0.057 |
| B6 | shown_above | 0.165 | 0.501 | 0.023 |
| Mstar | valid | 0.186 | 0.491 | 0.016 |
| B4 | shown_above | 0.202 | 0.520 | 0.026 |
| B0 | shown_above | 0.371 | 0.395 | 0.022 |
| RETUNED | shown_above | 0.407 | 0.361 | 0.022 |
| B1 | shown_above | 0.513 | 0.188 | 0.019 |
| B9 | shown_above | 0.693 | 0.158 | 0.014 |
| RETUNED-HK1 (= B0a8) | valid | 0.781 | 0.095 | 0.014 |
| MstarJ | valid | 0.823 | 0.047 | 0.006 |
| MstarJx | floor_only | 0.858 | 0.038 | 0.006 |
| B3 | floor_only | 0.969 | 0.033 | 0.007 |
| B0d0.5 | shown_above | 0.004 | 0.976 | 0.057 |
| B0a0.03125 | shown_above | 0.037 | 0.894 | 0.042 |
| B0a0.0625 | shown_above | 0.058 | 0.845 | 0.039 |
| B0d0.3 | shown_above | 0.076 | 0.796 | 0.036 |
| B0a0.125 | shown_above | 0.085 | 0.768 | 0.035 |
| B0a0.25 | shown_above | 0.136 | 0.667 | 0.030 |
| B0d0.2 | shown_above | 0.140 | 0.659 | 0.030 |
| B0a0.333 | shown_above | 0.169 | 0.616 | 0.028 |
| B0a0.5 | shown_above | 0.232 | 0.537 | 0.026 |
| B0d0.1 | shown_above | 0.271 | 0.495 | 0.026 |
| B0a1 | shown_above | 0.371 | 0.395 | 0.022 |
| B0d0.05 | shown_above | 0.371 | 0.395 | 0.022 |
| B0d0.02 | shown_above | 0.468 | 0.303 | 0.020 |
| B0a2 | shown_above | 0.525 | 0.254 | 0.019 |
| B0d0.01 | shown_above | 0.525 | 0.254 | 0.019 |
| B0d0.005 | shown_above | 0.570 | 0.220 | 0.019 |
| B0a3 | shown_above | 0.606 | 0.189 | 0.018 |
| B0d0.001 | shown_above | 0.637 | 0.168 | 0.018 |
| B0a4 | valid | 0.660 | 0.155 | 0.017 |
| B0a5 | valid | 0.701 | 0.132 | 0.016 |
| B0a8 | valid | 0.781 | 0.095 | 0.014 |

## T3 (Poly-MOT): every arm

| Arm | Status | Infeasible | V2 | V2_viol |
|---|---|---|---|---|
| Z0 | shown_above | 0.002 | 0.978 | 0.053 |
| B6 | shown_above | 0.229 | 0.529 | 0.023 |
| Mstar | valid | 0.247 | 0.496 | 0.018 |
| B4 | shown_above | 0.315 | 0.572 | 0.049 |
| RETUNED | shown_above | 0.611 | 0.316 | 0.028 |
| B9 | shown_above | 0.663 | 0.177 | 0.018 |
| B1 | shown_above | 0.666 | 0.228 | 0.024 |
| B0 | floor_only | 0.858 | 0.072 | 0.013 |
| MstarJ | valid | 0.862 | 0.047 | 0.009 |
| MstarJx | floor_only | 0.897 | 0.038 | 0.009 |
| B3 | floor_only | 0.941 | 0.030 | 0.009 |
| RETUNED-HK1 (= B0a8) | floor_only | 0.977 | 0.015 | 0.005 |
| B0d0.5 | shown_above | 0.002 | 0.978 | 0.053 |
| B0a0.03125 | shown_above | 0.329 | 0.615 | 0.046 |
| B0a0.0625 | shown_above | 0.448 | 0.489 | 0.038 |
| B0d0.3 | shown_above | 0.527 | 0.398 | 0.033 |
| B0a0.125 | shown_above | 0.565 | 0.360 | 0.031 |
| B0a0.25 | shown_above | 0.694 | 0.235 | 0.022 |
| B0d0.2 | shown_above | 0.700 | 0.228 | 0.022 |
| B0a0.333 | shown_above | 0.732 | 0.191 | 0.020 |
| B0a0.5 | valid | 0.781 | 0.136 | 0.017 |
| B0d0.1 | floor_only | 0.801 | 0.114 | 0.015 |
| B0a1 | floor_only | 0.858 | 0.072 | 0.013 |
| B0d0.05 | floor_only | 0.858 | 0.072 | 0.013 |
| B0d0.02 | floor_only | 0.904 | 0.048 | 0.011 |
| B0a2 | floor_only | 0.922 | 0.039 | 0.011 |
| B0d0.01 | floor_only | 0.922 | 0.039 | 0.011 |
| B0d0.005 | floor_only | 0.936 | 0.034 | 0.010 |
| B0a3 | floor_only | 0.947 | 0.030 | 0.009 |
| B0d0.001 | floor_only | 0.953 | 0.027 | 0.008 |
| B0a4 | floor_only | 0.957 | 0.026 | 0.008 |
| B0a5 | floor_only | 0.966 | 0.023 | 0.007 |
| B0a8 | floor_only | 0.977 | 0.015 | 0.005 |

## AB3DMOT (tab, descriptive): every arm

| Arm | Status | Infeasible | V2 | V2_viol |
|---|---|---|---|---|
| Z0 | shown_above | 0.006 | 0.977 | 0.183 |
| B6 | shown_above | 0.891 | 0.493 | 0.052 |
| Mstar | shown_above | 0.891 | 0.520 | 0.038 |
| B4 | shown_above | 0.896 | 0.517 | 0.059 |
| RETUNED | valid | 0.934 | 0.180 | 0.040 |
| B1 | floor_only | 0.935 | 0.233 | 0.041 |
| B0 | floor_only | 0.950 | 0.117 | 0.034 |
| MstarJ | floor_only | 0.963 | 0.045 | 0.015 |
| B9 | floor_only | 0.968 | 0.111 | 0.043 |
| MstarJx | floor_only | 0.969 | 0.036 | 0.013 |
| RETUNED-HK1 (= B0a8) | floor_only | 0.982 | 0.024 | 0.017 |
| B3 | floor_only | 0.988 | 0.009 | 0.007 |
| B0d0.5 | shown_above | 0.006 | 0.977 | 0.183 |
| B0a0.03125 | shown_above | 0.892 | 0.582 | 0.060 |
| B0a0.0625 | shown_above | 0.900 | 0.464 | 0.058 |
| B0d0.3 | shown_above | 0.907 | 0.383 | 0.055 |
| B0a0.125 | shown_above | 0.910 | 0.351 | 0.054 |
| B0a0.25 | shown_above | 0.921 | 0.259 | 0.049 |
| B0d0.2 | shown_above | 0.922 | 0.253 | 0.049 |
| B0a0.333 | shown_above | 0.926 | 0.225 | 0.046 |
| B0a0.5 | shown_above | 0.934 | 0.180 | 0.040 |
| B0d0.1 | shown_above | 0.938 | 0.160 | 0.039 |
| B0a1 | floor_only | 0.950 | 0.117 | 0.034 |
| B0d0.05 | floor_only | 0.950 | 0.117 | 0.034 |
| B0d0.02 | floor_only | 0.959 | 0.087 | 0.031 |
| B0a2 | floor_only | 0.965 | 0.070 | 0.029 |
| B0d0.01 | floor_only | 0.965 | 0.070 | 0.029 |
| B0d0.005 | floor_only | 0.968 | 0.058 | 0.026 |
| B0a3 | floor_only | 0.971 | 0.047 | 0.023 |
| B0d0.001 | floor_only | 0.973 | 0.041 | 0.022 |
| B0a4 | floor_only | 0.975 | 0.038 | 0.021 |
| B0a5 | floor_only | 0.977 | 0.033 | 0.020 |
| B0a8 | floor_only | 0.982 | 0.024 | 0.017 |

## T1 (CANMOT): back-off levels executed (share of decisions, pooled over decisions; log mean in brackets)

| Arm | Infeasible | lambda 1 | 0.75 | 0.5 | 0.25 | 0 | e-stop (-1) | among infeasible: 0.75 / 0.5 / 0.25 / 0 / e-stop |
|---|---|---|---|---|---|---|---|---|
| M* | 0.186 | 0.814 (0.814) | 0.060 (0.060) | 0.056 (0.056) | 0.040 (0.040) | 0.026 (0.026) | 0.004 (0.004) |  0.323 / 0.302 / 0.212 / 0.140 / 0.023 |
| B0 | 0.371 | 0.629 (0.629) | 0.116 (0.115) | 0.120 (0.120) | 0.078 (0.078) | 0.054 (0.054) | 0.004 (0.004) |  0.311 / 0.323 / 0.209 / 0.145 / 0.011 |
| B1 | 0.513 | 0.486 (0.487) | 0.125 (0.124) | 0.165 (0.164) | 0.151 (0.151) | 0.069 (0.069) | 0.004 (0.004) |  0.242 / 0.321 / 0.294 / 0.134 / 0.008 |
| B3 | 0.969 | 0.031 (0.031) | 0.028 (0.028) | 0.062 (0.062) | 0.180 (0.180) | 0.695 (0.695) | 0.004 (0.004) |  0.029 / 0.064 / 0.185 / 0.718 / 0.004 |
| B4 | 0.202 | 0.798 (0.798) | 0.071 (0.071) | 0.053 (0.053) | 0.044 (0.044) | 0.030 (0.030) | 0.004 (0.004) |  0.349 / 0.263 / 0.216 / 0.151 / 0.021 |
| B6 | 0.165 | 0.835 (0.835) | 0.063 (0.063) | 0.043 (0.043) | 0.033 (0.034) | 0.022 (0.022) | 0.004 (0.004) |  0.379 / 0.259 / 0.202 / 0.135 / 0.026 |
| B9 | 0.693 | 0.307 (0.307) | 0.105 (0.105) | 0.154 (0.155) | 0.166 (0.166) | 0.263 (0.263) | 0.004 (0.004) |  0.151 / 0.223 / 0.240 / 0.380 / 0.006 |
| RETUNED | 0.407 | 0.593 (0.593) | 0.116 (0.115) | 0.134 (0.134) | 0.095 (0.094) | 0.058 (0.058) | 0.004 (0.004) |  0.284 / 0.329 / 0.232 / 0.144 / 0.010 |

## T3 (Poly-MOT): back-off levels executed (share of decisions, pooled over decisions; log mean in brackets)

| Arm | Infeasible | lambda 1 | 0.75 | 0.5 | 0.25 | 0 | e-stop (-1) | among infeasible: 0.75 / 0.5 / 0.25 / 0 / e-stop |
|---|---|---|---|---|---|---|---|---|
| M* | 0.247 | 0.753 (0.753) | 0.069 (0.069) | 0.074 (0.074) | 0.066 (0.066) | 0.036 (0.036) | 0.002 (0.002) |  0.281 / 0.299 / 0.266 / 0.145 / 0.010 |
| B0 | 0.858 | 0.142 (0.142) | 0.064 (0.064) | 0.099 (0.099) | 0.246 (0.246) | 0.446 (0.445) | 0.002 (0.002) |  0.075 / 0.116 / 0.287 / 0.520 / 0.003 |
| B1 | 0.666 | 0.334 (0.334) | 0.080 (0.080) | 0.104 (0.104) | 0.197 (0.196) | 0.283 (0.283) | 0.002 (0.002) |  0.120 / 0.156 / 0.295 / 0.425 / 0.004 |
| B3 | 0.941 | 0.059 (0.059) | 0.040 (0.040) | 0.089 (0.089) | 0.190 (0.191) | 0.619 (0.618) | 0.002 (0.002) |  0.043 / 0.095 / 0.202 / 0.658 / 0.003 |
| B4 | 0.315 | 0.685 (0.685) | 0.077 (0.077) | 0.078 (0.078) | 0.081 (0.081) | 0.077 (0.077) | 0.002 (0.002) |  0.245 / 0.247 / 0.255 / 0.245 / 0.008 |
| B6 | 0.229 | 0.771 (0.771) | 0.062 (0.062) | 0.068 (0.068) | 0.057 (0.057) | 0.040 (0.040) | 0.002 (0.002) |  0.269 / 0.297 / 0.249 / 0.174 / 0.010 |
| B9 | 0.663 | 0.337 (0.337) | 0.115 (0.116) | 0.136 (0.136) | 0.168 (0.168) | 0.241 (0.241) | 0.002 (0.002) |  0.174 / 0.205 / 0.253 / 0.364 / 0.004 |
| RETUNED | 0.611 | 0.389 (0.389) | 0.102 (0.102) | 0.139 (0.139) | 0.179 (0.179) | 0.189 (0.189) | 0.002 (0.002) |  0.167 / 0.227 / 0.293 / 0.309 / 0.004 |

## AB3DMOT (tab, descriptive): back-off levels executed (share of decisions, pooled over decisions; log mean in brackets)

| Arm | Infeasible | lambda 1 | 0.75 | 0.5 | 0.25 | 0 | e-stop (-1) | among infeasible: 0.75 / 0.5 / 0.25 / 0 / e-stop |
|---|---|---|---|---|---|---|---|---|
| M* | 0.891 | 0.109 (0.109) | 0.014 (0.014) | 0.035 (0.035) | 0.177 (0.178) | 0.658 (0.658) | 0.006 (0.006) |  0.016 / 0.039 / 0.199 / 0.739 / 0.007 |
| B0 | 0.950 | 0.050 (0.050) | 0.014 (0.014) | 0.015 (0.015) | 0.021 (0.021) | 0.894 (0.894) | 0.006 (0.006) |  0.015 / 0.016 / 0.022 / 0.941 / 0.007 |
| B1 | 0.935 | 0.065 (0.065) | 0.012 (0.012) | 0.013 (0.013) | 0.030 (0.030) | 0.874 (0.874) | 0.006 (0.006) |  0.013 / 0.013 / 0.032 / 0.935 / 0.007 |
| B3 | 0.988 | 0.012 (0.012) | 0.003 (0.003) | 0.008 (0.008) | 0.024 (0.024) | 0.947 (0.947) | 0.006 (0.006) |  0.003 / 0.008 / 0.024 / 0.958 / 0.006 |
| B4 | 0.896 | 0.104 (0.104) | 0.007 (0.007) | 0.009 (0.009) | 0.084 (0.084) | 0.789 (0.789) | 0.006 (0.006) |  0.008 / 0.010 / 0.094 / 0.881 / 0.007 |
| B6 | 0.891 | 0.109 (0.109) | 0.010 (0.010) | 0.025 (0.025) | 0.070 (0.070) | 0.779 (0.779) | 0.006 (0.006) |  0.012 / 0.028 / 0.079 / 0.874 / 0.007 |
| B9 | 0.968 | 0.032 (0.032) | 0.021 (0.021) | 0.064 (0.063) | 0.194 (0.194) | 0.683 (0.683) | 0.006 (0.006) |  0.022 / 0.066 / 0.200 / 0.706 / 0.007 |
| RETUNED | 0.934 | 0.066 (0.066) | 0.011 (0.011) | 0.013 (0.013) | 0.018 (0.018) | 0.885 (0.885) | 0.006 (0.006) |  0.012 / 0.014 / 0.019 / 0.948 / 0.007 |

## Reading

- t1: M* (valid) infeasible 0.186, V2 0.491, V2_viol 0.016. Arms with status valid besides M*: B0a4 (0.660 / 0.155 / 0.017), B0a5 (0.701 / 0.132 / 0.016), B0a8 (0.781 / 0.095 / 0.014), MstarJ (0.823 / 0.047 / 0.006), RETUNED-HK1 (0.781 / 0.095 / 0.014); of these, less often infeasible than M*: none. M*'s infeasible decisions: e-stop share 0.023, lambda 0 share 0.140 of them.
- t1: arms at or below M* on both infeasible rate and V2_viol: none; on both infeasible rate and V2: none. Comparators of K with lower V2_viol than M*: B3, B9. Emergency-stop share of decisions across M* and the comparators: [0.004252] (the same for every arm when a single value).
- t3: M* (valid) infeasible 0.247, V2 0.496, V2_viol 0.018. Arms with status valid besides M*: B0a0.5 (0.781 / 0.136 / 0.017), MstarJ (0.862 / 0.047 / 0.009); of these, less often infeasible than M*: none. M*'s infeasible decisions: e-stop share 0.010, lambda 0 share 0.145 of them.
- t3: arms at or below M* on both infeasible rate and V2_viol: none; on both infeasible rate and V2: none. Comparators of K with lower V2_viol than M*: B0, B3. Emergency-stop share of decisions across M* and the comparators: [0.002392] (the same for every arm when a single value).
- tab: M* (shown_above) infeasible 0.891, V2 0.520, V2_viol 0.038. Arms with status valid besides M*: RETUNED (0.934 / 0.180 / 0.040); of these, less often infeasible than M*: none. M*'s infeasible decisions: e-stop share 0.007, lambda 0 share 0.739 of them.
- tab: arms at or below M* on both infeasible rate and V2_viol: none; on both infeasible rate and V2: B6. Comparators of K with lower V2_viol than M*: B0, B3. Emergency-stop share of decisions across M* and the comparators: [0.006378] (the same for every arm when a single value).

## Choices

- V2 and V2_viol are read on P_rel (PD7_primary), the population of the record's headline V2 (D19 section 2; referee M10's numbers).
- The screen status is the record's own arm_status (c1 section), so comparators of K carry their removal-level status and the sweep, Z0 and the joint arms their 0.95 status; RETUNED-HK1's status is the record's RETUNED_HK1.status.
- RETUNED-HK1 chose B0a8 in every fold on all three trackers (record choice_by_fold), so its point coincides with B0a8's; it is drawn and labelled separately.
- The sweep arms are joined in order of infeasible rate (the merged alpha / delta' curve is monotone in the margin scale); the line is a visual guide only.
- Back-off shares: pooled over decisions (the record's backoff_distribution, checked against arms.csv) and log means; lambda = -1 is the emergency stop. 'Among infeasible' divides by the arm's infeasible decisions.

Code: `50_CODE/x3/x3_stats_f_v01.py` (sha256 in the JSON). Nothing here changes a status or table of record.
