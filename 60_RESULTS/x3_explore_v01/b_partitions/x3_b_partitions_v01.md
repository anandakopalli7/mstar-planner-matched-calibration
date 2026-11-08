# X3 analysis (b): the screen on partitions no method used

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Plan section 2(b). Cells = bin x relied-on axis; populations P_rel (PD7), P_near (SD1_7), P_ip (PD); evaluable with >= 39 logs; flag = one-sided simultaneous sup-t lower bound at 0.95 over the partition's evaluable cells above delta = 0.05; log bootstrap B = 4000, seed [20261201, i, 2]. Runs: x3_run_v01 core runs (fits of record; V0 and V2 passed). P0 (distance to the ego) is a partition M*'s strata use, reported for completeness; P1-P7 are used by no method.

## T1

Flagged cells per arm and partition (P_rel / P_near / P_ip); '-' = none flagged; (n) = evaluable cells.

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| Mstar | - (6) / - (2) / - (5) | [0.5,3)|long (8) / - (8) / - (7) | - (8) / - (8) / - (6) | 1-2|lat (8) / - (8) / - (8) | [0.4,0.5)|long, [0.4,0.5)|lat (8) / - (8) / - (6) | - (8) / - (8) / - (7) | 1-10|lat (8) / - (6) / - (5) | - (8) / - (8) / - (5) |
| B0 | - (6) / - (2) / <20 m|lat (5) | [0.5,3)|long, [3,8)|long, [3,8)|lat, >=8|long (8) / - (8) / [3,8)|lat (7) | <2|long (8) / - (8) / - (6) | 1-2|long (8) / - (8) / - (8) | [0.4,0.5)|long (8) / - (8) / [0.5,0.7)|lat (6) | - (8) / - (8) / [1,5)|lat (7) | - (8) / - (6) / >200|lat (5) | - (8) / - (7) / - (5) |
| B1 | - (6) / - (2) / - (5) | - (8) / - (8) / [3,8)|lat (7) | >=8|long (8) / - (8) / - (6) | - (8) / - (8) / - (8) | - (8) / - (8) / - (6) | - (8) / - (8) / - (6) | - (8) / - (5) / - (5) | - (8) / - (7) / - (5) |
| B3 | - (6) / - (2) / - (5) | - (8) / - (6) / - (7) | - (8) / - (3) / - (5) | - (8) / - (8) / - (8) | - (8) / - (7) / - (5) | - (8) / - (8) / - (6) | - (8) / - (4) / - (5) | - (8) / - (4) / - (4) |
| B4 | <20 m|long, 20-40 m|long (6) / - (2) / <20 m|lat, 20-40 m|long (5) | [0.5,3)|long, [3,8)|long, [3,8)|lat, >=8|long, >=8|lat (8) / [0.5,3)|long, [3,8)|lat (8) / [3,8)|long, [3,8)|lat, >=8|long (8) | <2|long, [5.5,8)|long, >=8|long (8) / <2|long (8) / [2,5.5)|lat (6) | 1-2|long, 3-5|long (8) / 1-2|long, 3-5|long (8) / 1-2|long (8) | [0.4,0.5)|long, [0.5,0.7)|long (8) / [0.4,0.5)|long (8) / [0.5,0.7)|long, [0.5,0.7)|lat (6) | <1|long, [1,5)|long, [5,10)|long, >=10|long (8) / - (8) / [1,5)|lat (7) | 1-10|long, 11-50|long, 51-200|long, >200|long (8) / 51-200|long (6) / 51-200|long, >200|long, >200|lat (5) | MIA|long, PIT|long (8) / - (7) / - (5) |
| B6 | - (6) / - (2) / - (5) | [0.5,3)|long, [0.5,3)|lat, [3,8)|long, [3,8)|lat, >=8|long, >=8|lat (8) / [3,8)|lat, >=8|lat (8) / - (7) | - (8) / - (8) / - (6) | 1-2|long, 1-2|lat (8) / - (8) / - (8) | [0.4,0.5)|long, [0.4,0.5)|lat, [0.5,0.7)|long, [0.5,0.7)|lat (8) / - (8) / - (6) | <1|lat (8) / - (8) / - (7) | - (8) / - (6) / - (5) | - (8) / - (7) / - (5) |
| B9 | - (6) / - (2) / - (5) | - (8) / - (8) / - (7) | - (8) / - (8) / - (6) | - (8) / - (8) / - (8) | - (8) / - (8) / - (6) | - (8) / - (8) / - (7) | - (8) / - (5) / - (5) | - (8) / - (8) / - (5) |

Largest evaluable cell estimate with its simultaneous upper bound (P_rel):

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| Mstar | 20-40 m|lat 0.060 (UB 0.069) | [0.5,3)|long 0.082 (UB 0.097) | [5.5,8)|lat 0.061 (UB 0.081) | 1-2|lat 0.065 (UB 0.075) | [0.4,0.5)|lat 0.093 (UB 0.109) | <1|lat 0.067 (UB 0.084) | 1-10|lat 0.071 (UB 0.087) | PIT|lat 0.057 (UB 0.067) |
| B0 | 20-40 m|long 0.047 (UB 0.054) | [3,8)|long 0.105 (UB 0.126) | <2|long 0.068 (UB 0.080) | 1-2|long 0.089 (UB 0.102) | [0.4,0.5)|long 0.069 (UB 0.080) | <1|long 0.051 (UB 0.066) | 1-10|long 0.045 (UB 0.054) | PIT|long 0.043 (UB 0.052) |
| B1 | <20 m|lat 0.018 (UB 0.024) | [3,8)|lat 0.053 (UB 0.068) | >=8|long 0.120 (UB 0.154) | 1-2|long 0.025 (UB 0.031) | [0.4,0.5)|long 0.034 (UB 0.041) | <1|lat 0.023 (UB 0.035) | >200|long 0.019 (UB 0.024) | PIT|long 0.015 (UB 0.023) |
| B3 | <20 m|long 0.002 (UB 0.003) | >=8|lat 0.003 (UB 0.007) | <2|long 0.002 (UB 0.003) | >10|long 0.003 (UB 0.005) | >=0.85|long 0.003 (UB 0.005) | <1|long 0.003 (UB 0.005) | >200|long 0.002 (UB 0.004) | PIT|long 0.003 (UB 0.004) |
| B4 | 20-40 m|long 0.076 (UB 0.085) | [3,8)|long 0.167 (UB 0.193) | <2|long 0.116 (UB 0.133) | 1-2|long 0.133 (UB 0.147) | [0.4,0.5)|long 0.099 (UB 0.111) | <1|long 0.077 (UB 0.094) | 1-10|long 0.080 (UB 0.095) | MIA|long 0.072 (UB 0.083) |
| B6 | 20-40 m|lat 0.060 (UB 0.069) | [3,8)|long 0.150 (UB 0.176) | [5.5,8)|long 0.070 (UB 0.090) | 1-2|long 0.102 (UB 0.116) | [0.4,0.5)|lat 0.083 (UB 0.100) | <1|lat 0.081 (UB 0.100) | 1-10|lat 0.063 (UB 0.078) | PIT|lat 0.057 (UB 0.069) |
| B9 | 20-40 m|long 0.020 (UB 0.024) | [3,8)|long 0.072 (UB 0.089) | >=8|long 0.060 (UB 0.085) | 1-2|long 0.052 (UB 0.063) | [0.4,0.5)|long 0.037 (UB 0.046) | >=10|long 0.027 (UB 0.038) | >200|long 0.028 (UB 0.034) | WDC|long 0.021 (UB 0.030) |

M*: every cell with estimate above delta (all partitions and populations):

| partition | population | cell | E | simultaneous LB | simultaneous UB | logs | evaluable | flagged |
|---|---|---|---|---|---|---|---|---|
| P0_distance_range | P_rel (PD7) | 20-40 m|lat | 0.0598 | 0.0500 | 0.0688 | 370 | yes | no |
| P0_distance_range | P_rel (PD7) | >=40 m|lat | 0.0568 | 0.0418 | 0.0704 | 360 | yes | no |
| P0_distance_range | P_ip (PD) | 20-40 m|lat | 0.0520 | 0.0057 | 0.0889 | 99 | yes | no |
| P1_track_speed | P_rel (PD7) | [0,0.5)|lat | 0.0508 | 0.0405 | 0.0598 | 373 | yes | no |
| P1_track_speed | P_rel (PD7) | [0.5,3)|lat | 0.0634 | 0.0471 | 0.0776 | 356 | yes | no |
| P1_track_speed | P_rel (PD7) | [0.5,3)|long | 0.0818 | 0.0639 | 0.0974 | 365 | yes | yes |
| P1_track_speed | P_rel (PD7) | [3,8)|lat | 0.0532 | 0.0349 | 0.0691 | 312 | yes | no |
| P1_track_speed | P_rel (PD7) | [3,8)|long | 0.0516 | 0.0363 | 0.0649 | 346 | yes | no |
| P1_track_speed | P_near (SD1_7) | >=8|long | 0.0507 | 0.0042 | 0.0885 | 110 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0.5,3)|lat | 0.0562 | 0.0311 | 0.0767 | 249 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0.5,3)|long | 0.0752 | 0.0425 | 0.1019 | 219 | yes | no |
| P1_track_speed | P_ip (PD) | >=8|long | 0.0590 | 0.0160 | 0.0915 | 137 | yes | no |
| P1_track_speed | P_ip (PD) | [3,8)|lat | 0.0721 | 0.0064 | 0.1217 | 93 | yes | no |
| P1_track_speed | P_ip (PD) | [3,8)|long | 0.0575 | 0.0240 | 0.0829 | 222 | yes | no |
| P2_track_length | P_rel (PD7) | [2,5.5)|lat | 0.0520 | 0.0415 | 0.0610 | 374 | yes | no |
| P2_track_length | P_rel (PD7) | [5.5,8)|lat | 0.0608 | 0.0370 | 0.0810 | 282 | yes | no |
| P2_track_length | P_rel (PD7) | [5.5,8)|long | 0.0540 | 0.0309 | 0.0738 | 298 | yes | no |
| P2_track_length | P_near (SD1_7) | [5.5,8)|lat | 0.0662 | 0.0265 | 0.0960 | 185 | yes | no |
| P2_track_length | P_ip (PD) | [2,5.5)|lat | 0.0539 | 0.0173 | 0.0802 | 172 | yes | no |
| P2_track_length | P_ip (PD) | [5.5,8)|lat | 0.0799 | (marginal 0.0174) | (marginal 0.1573) | 26 | no (< 39 logs) | n/a |
| P2_track_length | P_ip (PD) | [5.5,8)|long | 0.0790 | 0.0030 | 0.1337 | 66 | yes | no |
| P3_track_age | P_rel (PD7) | 1-2|lat | 0.0655 | 0.0540 | 0.0752 | 374 | yes | yes |
| P3_track_age | P_rel (PD7) | 1-2|long | 0.0567 | 0.0476 | 0.0644 | 375 | yes | no |
| P3_track_age | P_rel (PD7) | 3-5|lat | 0.0509 | 0.0417 | 0.0588 | 374 | yes | no |
| P3_track_age | P_rel (PD7) | 6-10|lat | 0.0512 | 0.0382 | 0.0623 | 373 | yes | no |
| P3_track_age | P_near (SD1_7) | 1-2|long | 0.0766 | 0.0306 | 0.1145 | 191 | yes | no |
| P3_track_age | P_ip (PD) | 1-2|lat | 0.0508 | -0.0187 | 0.1016 | 64 | yes | no |
| P3_track_age | P_ip (PD) | 3-5|lat | 0.0511 | 0.0006 | 0.0881 | 95 | yes | no |
| P3_track_age | P_ip (PD) | 3-5|long | 0.0508 | 0.0188 | 0.0743 | 215 | yes | no |
| P4_detection_score | P_rel (PD7) | [0.4,0.5)|lat | 0.0926 | 0.0736 | 0.1090 | 363 | yes | yes |
| P4_detection_score | P_rel (PD7) | [0.4,0.5)|long | 0.0868 | 0.0723 | 0.0995 | 374 | yes | yes |
| P4_detection_score | P_rel (PD7) | [0.5,0.7)|lat | 0.0567 | 0.0484 | 0.0640 | 375 | yes | no |
| P4_detection_score | P_rel (PD7) | [0.5,0.7)|long | 0.0505 | 0.0429 | 0.0572 | 375 | yes | no |
| P4_detection_score | P_near (SD1_7) | [0.4,0.5)|lat | 0.0759 | 0.0286 | 0.1150 | 158 | yes | no |
| P4_detection_score | P_near (SD1_7) | [0.4,0.5)|long | 0.0617 | 0.0082 | 0.1060 | 117 | yes | no |
| P4_detection_score | P_near (SD1_7) | [0.5,0.7)|lat | 0.0530 | 0.0316 | 0.0706 | 364 | yes | no |
| P4_detection_score | P_ip (PD) | [0.4,0.5)|lat | 0.0690 | (marginal 0.0000) | (marginal 0.1538) | 29 | no (< 39 logs) | n/a |
| P4_detection_score | P_ip (PD) | [0.4,0.5)|long | 0.0758 | 0.0099 | 0.1266 | 83 | yes | no |
| P4_detection_score | P_ip (PD) | [0.5,0.7)|lat | 0.0562 | 0.0168 | 0.0865 | 157 | yes | no |
| P5_ego_speed | P_rel (PD7) | <1|lat | 0.0666 | 0.0458 | 0.0844 | 198 | yes | no |
| P5_ego_speed | P_rel (PD7) | <1|long | 0.0584 | 0.0435 | 0.0710 | 197 | yes | no |
| P5_ego_speed | P_rel (PD7) | [1,5)|lat | 0.0589 | 0.0452 | 0.0707 | 294 | yes | no |
| P5_ego_speed | P_near (SD1_7) | <1|long | 0.0870 | 0.0325 | 0.1300 | 134 | yes | no |
| P5_ego_speed | P_ip (PD) | <1|lat | 0.1579 | (marginal 0.0417) | (marginal 0.2941) | 19 | no (< 39 logs) | n/a |
| P5_ego_speed | P_ip (PD) | [1,5)|lat | 0.0561 | 0.0090 | 0.0904 | 120 | yes | no |
| P5_ego_speed | P_ip (PD) | [1,5)|long | 0.0617 | 0.0258 | 0.0878 | 215 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 1-10|lat | 0.0715 | 0.0537 | 0.0870 | 343 | yes | yes |
| P6_gt_lidar_points | P_rel (PD7) | 1-10|long | 0.0562 | 0.0417 | 0.0689 | 352 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 11-50|lat | 0.0611 | 0.0485 | 0.0720 | 367 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 51-200|lat | 0.0529 | 0.0424 | 0.0621 | 371 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | 1-10|lat | 0.0571 | (marginal 0.0108) | (marginal 0.1111) | 35 | no (< 39 logs) | n/a |
| P6_gt_lidar_points | P_near (SD1_7) | 11-50|lat | 0.0592 | 0.0002 | 0.1041 | 68 | yes | no |
| P6_gt_lidar_points | P_ip (PD) | 1-10|long | 0.1979 | (marginal 0.0513) | (marginal 0.3590) | 16 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | ATX|long | 0.0600 | (marginal 0.0293) | (marginal 0.1027) | 9 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | PIT|lat | 0.0568 | 0.0445 | 0.0673 | 127 | yes | no |
| P7_city | P_near (SD1_7) | PAO|lat | 0.0684 | (marginal 0.0023) | (marginal 0.1759) | 9 | no (< 39 logs) | n/a |
| P7_city | P_near (SD1_7) | WDC|lat | 0.0664 | -0.0099 | 0.1218 | 45 | yes | no |
| P7_city | P_ip (PD) | ATX|lat | 0.1406 | (marginal 0.0000) | (marginal 0.3750) | 4 | no (< 39 logs) | n/a |
| P7_city | P_ip (PD) | ATX|long | 0.0549 | (marginal 0.0119) | (marginal 0.0991) | 6 | no (< 39 logs) | n/a |
| P7_city | P_ip (PD) | PAO|lat | 0.1289 | (marginal 0.0000) | (marginal 0.3385) | 4 | no (< 39 logs) | n/a |
| P7_city | P_ip (PD) | PIT|lat | 0.0561 | 0.0043 | 0.0927 | 82 | yes | no |
| P7_city | P_ip (PD) | PIT|long | 0.0548 | 0.0159 | 0.0823 | 117 | yes | no |
| P7_city | P_ip (PD) | WDC|lat | 0.1026 | (marginal 0.0137) | (marginal 0.2115) | 22 | no (< 39 logs) | n/a |

## T3

Flagged cells per arm and partition (P_rel / P_near / P_ip); '-' = none flagged; (n) = evaluable cells.

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| Mstar | 20-40 m|lat, >=40 m|lat (6) / - (2) / - (5) | - (8) / - (8) / - (7) | - (8) / - (8) / - (6) | 1-2|lat (8) / - (8) / - (8) | [0.4,0.5)|long, [0.4,0.5)|lat (8) / - (8) / - (6) | - (8) / - (8) / - (7) | 1-10|lat, 11-50|lat (8) / - (7) / - (5) | - (8) / - (7) / - (4) |
| B0 | - (6) / - (2) / - (5) | - (8) / - (8) / - (7) | - (8) / - (7) / - (6) | - (8) / - (8) / - (8) | - (8) / - (8) / - (6) | - (8) / - (8) / - (5) | - (8) / - (5) / - (5) | - (8) / - (6) / - (4) |
| B1 | - (6) / - (2) / - (5) | - (8) / - (7) / - (7) | >=8|long (8) / - (8) / - (6) | - (8) / - (8) / - (8) | - (8) / - (8) / - (6) | - (8) / - (8) / - (5) | - (8) / - (6) / - (5) | - (8) / - (8) / - (4) |
| B3 | - (6) / - (2) / - (5) | - (8) / - (4) / - (7) | - (8) / - (4) / - (6) | - (8) / - (6) / - (8) | - (8) / - (6) / - (6) | - (8) / - (5) / - (5) | - (8) / - (3) / - (5) | - (8) / - (4) / - (4) |
| B4 | <20 m|long, 20-40 m|long, >=40 m|long (6) / <20 m|long (2) / <20 m|long, 20-40 m|long (5) | [0.5,3)|long, [3,8)|long, >=8|long (8) / [3,8)|long, >=8|long (8) / [0.5,3)|long, [3,8)|long, >=8|long (7) | [2,5.5)|long, [5.5,8)|long, >=8|long (8) / [2,5.5)|long, [5.5,8)|long, >=8|long (8) / [2,5.5)|long, [5.5,8)|long, >=8|long (6) | 1-2|long, 3-5|long, 6-10|long, >10|long (8) / 1-2|long, 3-5|long, 6-10|long (8) / 1-2|long, 3-5|long, 6-10|long, >10|long (8) | [0.4,0.5)|long, [0.5,0.7)|long, [0.7,0.85)|long (8) / [0.4,0.5)|long, [0.5,0.7)|long, [0.7,0.85)|long (8) / [0.4,0.5)|long, [0.5,0.7)|long, [0.7,0.85)|long (6) | <1|long, [1,5)|long, [5,10)|long, >=10|long (8) / <1|long, [1,5)|long, [5,10)|long, >=10|long (8) / [1,5)|long, [5,10)|long, >=10|long (7) | 1-10|long, 51-200|long, >200|long (8) / >200|long (7) / 51-200|long, >200|long (5) | DTW|long, MIA|long, PIT|long, WDC|long (8) / MIA|long, PIT|long (8) / MIA|long, PIT|long (4) |
| B6 | 20-40 m|lat, >=40 m|lat (6) / - (2) / - (5) | [0.5,3)|long, [0.5,3)|lat, [3,8)|long, [3,8)|lat, >=8|long (8) / >=8|long (8) / [3,8)|lat (7) | - (8) / - (8) / - (6) | 1-2|long, 1-2|lat (8) / - (8) / - (8) | [0.4,0.5)|long, [0.4,0.5)|lat, [0.5,0.7)|long, [0.5,0.7)|lat (8) / - (8) / - (6) | <1|lat (8) / - (8) / - (7) | 1-10|lat, 11-50|lat (8) / - (7) / - (5) | - (8) / - (7) / - (4) |
| B9 | - (6) / - (2) / - (5) | [3,8)|long (8) / - (8) / - (7) | - (8) / - (8) / - (6) | - (8) / - (8) / - (8) | - (8) / - (8) / - (6) | - (8) / - (8) / - (7) | - (8) / - (6) / - (5) | - (8) / - (8) / - (4) |

Largest evaluable cell estimate with its simultaneous upper bound (P_rel):

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| Mstar | >=40 m|lat 0.068 (UB 0.085) | [0.5,3)|lat 0.065 (UB 0.079) | >=8|long 0.066 (UB 0.089) | 1-2|lat 0.067 (UB 0.075) | [0.4,0.5)|lat 0.088 (UB 0.101) | <1|lat 0.064 (UB 0.080) | 1-10|lat 0.076 (UB 0.095) | MIA|lat 0.052 (UB 0.062) |
| B0 | 20-40 m|long 0.006 (UB 0.008) | [3,8)|long 0.018 (UB 0.026) | >=8|long 0.016 (UB 0.025) | 1-2|long 0.012 (UB 0.015) | [0.4,0.5)|long 0.014 (UB 0.019) | <1|long 0.007 (UB 0.010) | >200|long 0.008 (UB 0.010) | WDC|long 0.008 (UB 0.013) |
| B1 | >=40 m|long 0.025 (UB 0.030) | [3,8)|long 0.065 (UB 0.078) | >=8|long 0.115 (UB 0.145) | 1-2|long 0.041 (UB 0.047) | [0.4,0.5)|long 0.040 (UB 0.048) | <1|long 0.031 (UB 0.040) | >200|long 0.026 (UB 0.031) | WDC|long 0.023 (UB 0.031) |
| B3 | 20-40 m|long 0.002 (UB 0.003) | [3,8)|long 0.005 (UB 0.009) | >=8|long 0.002 (UB 0.005) | >10|long 0.004 (UB 0.008) | [0.4,0.5)|long 0.005 (UB 0.007) | <1|long 0.003 (UB 0.005) | 1-10|long 0.004 (UB 0.007) | WDC|long 0.002 (UB 0.003) |
| B4 | <20 m|long 0.084 (UB 0.094) | [3,8)|long 0.225 (UB 0.248) | >=8|long 0.236 (UB 0.279) | 1-2|long 0.108 (UB 0.121) | [0.4,0.5)|long 0.112 (UB 0.126) | <1|long 0.095 (UB 0.113) | >200|long 0.109 (UB 0.122) | MIA|long 0.084 (UB 0.096) |
| B6 | >=40 m|lat 0.077 (UB 0.092) | [3,8)|long 0.121 (UB 0.141) | [5.5,8)|long 0.072 (UB 0.091) | 1-2|lat 0.080 (UB 0.089) | [0.4,0.5)|lat 0.093 (UB 0.106) | <1|lat 0.073 (UB 0.092) | 1-10|lat 0.083 (UB 0.103) | PIT|lat 0.058 (UB 0.068) |
| B9 | 20-40 m|long 0.022 (UB 0.025) | [3,8)|long 0.079 (UB 0.097) | >=8|long 0.061 (UB 0.084) | 1-2|long 0.051 (UB 0.060) | [0.4,0.5)|long 0.040 (UB 0.048) | >=10|long 0.027 (UB 0.036) | >200|long 0.029 (UB 0.035) | WDC|long 0.022 (UB 0.031) |

M*: every cell with estimate above delta (all partitions and populations):

| partition | population | cell | E | simultaneous LB | simultaneous UB | logs | evaluable | flagged |
|---|---|---|---|---|---|---|---|---|
| P0_distance_range | P_rel (PD7) | 20-40 m|lat | 0.0613 | 0.0510 | 0.0707 | 372 | yes | yes |
| P0_distance_range | P_rel (PD7) | >=40 m|lat | 0.0683 | 0.0500 | 0.0847 | 359 | yes | yes |
| P0_distance_range | P_near (SD1_7) | 20-40 m|lat | 0.1364 | (marginal 0.0000) | (marginal 0.3000) | 11 | no (< 39 logs) | n/a |
| P0_distance_range | P_near (SD1_7) | 20-40 m|long | 0.0769 | (marginal 0.0000) | (marginal 0.2308) | 13 | no (< 39 logs) | n/a |
| P0_distance_range | P_ip (PD) | 20-40 m|lat | 0.0976 | 0.0280 | 0.1546 | 95 | yes | no |
| P0_distance_range | P_ip (PD) | <20 m|lat | 0.0617 | 0.0297 | 0.0880 | 218 | yes | no |
| P1_track_speed | P_rel (PD7) | [0.5,3)|lat | 0.0655 | 0.0490 | 0.0793 | 360 | yes | no |
| P1_track_speed | P_rel (PD7) | [0.5,3)|long | 0.0606 | 0.0473 | 0.0717 | 362 | yes | no |
| P1_track_speed | P_rel (PD7) | [3,8)|lat | 0.0586 | 0.0406 | 0.0738 | 319 | yes | no |
| P1_track_speed | P_rel (PD7) | [3,8)|long | 0.0524 | 0.0360 | 0.0662 | 344 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0.5,3)|lat | 0.0701 | 0.0410 | 0.0928 | 251 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0.5,3)|long | 0.0513 | 0.0250 | 0.0719 | 231 | yes | no |
| P1_track_speed | P_ip (PD) | >=8|long | 0.0627 | 0.0227 | 0.0937 | 140 | yes | no |
| P1_track_speed | P_ip (PD) | [0.5,3)|lat | 0.0754 | 0.0221 | 0.1169 | 116 | yes | no |
| P1_track_speed | P_ip (PD) | [3,8)|lat | 0.1069 | 0.0335 | 0.1641 | 98 | yes | no |
| P2_track_length | P_rel (PD7) | >=8|long | 0.0658 | 0.0383 | 0.0889 | 200 | yes | no |
| P2_track_length | P_rel (PD7) | [2,5.5)|lat | 0.0537 | 0.0435 | 0.0623 | 373 | yes | no |
| P2_track_length | P_rel (PD7) | [5.5,8)|lat | 0.0554 | 0.0314 | 0.0756 | 280 | yes | no |
| P2_track_length | P_near (SD1_7) | [5.5,8)|lat | 0.0594 | 0.0218 | 0.0872 | 186 | yes | no |
| P2_track_length | P_ip (PD) | <2|lat | 0.0764 | 0.0007 | 0.1324 | 66 | yes | no |
| P2_track_length | P_ip (PD) | [2,5.5)|lat | 0.0725 | 0.0283 | 0.1053 | 175 | yes | no |
| P2_track_length | P_ip (PD) | [5.5,8)|lat | 0.1018 | (marginal 0.0367) | (marginal 0.1813) | 32 | no (< 39 logs) | n/a |
| P2_track_length | P_ip (PD) | [5.5,8)|long | 0.0596 | -0.0127 | 0.1131 | 58 | yes | no |
| P3_track_age | P_rel (PD7) | 1-2|lat | 0.0667 | 0.0574 | 0.0748 | 374 | yes | yes |
| P3_track_age | P_ip (PD) | 1-2|lat | 0.1017 | 0.0202 | 0.1653 | 79 | yes | no |
| P3_track_age | P_ip (PD) | 6-10|lat | 0.0501 | 0.0058 | 0.0846 | 135 | yes | no |
| P3_track_age | P_ip (PD) | >10|lat | 0.0523 | 0.0097 | 0.0856 | 125 | yes | no |
| P4_detection_score | P_rel (PD7) | [0.4,0.5)|lat | 0.0878 | 0.0722 | 0.1012 | 362 | yes | yes |
| P4_detection_score | P_rel (PD7) | [0.4,0.5)|long | 0.0780 | 0.0650 | 0.0892 | 374 | yes | yes |
| P4_detection_score | P_rel (PD7) | [0.5,0.7)|lat | 0.0555 | 0.0482 | 0.0617 | 375 | yes | no |
| P4_detection_score | P_near (SD1_7) | [0.4,0.5)|lat | 0.0604 | 0.0158 | 0.0947 | 158 | yes | no |
| P4_detection_score | P_ip (PD) | [0.4,0.5)|lat | 0.0565 | (marginal 0.0000) | (marginal 0.1290) | 31 | no (< 39 logs) | n/a |
| P4_detection_score | P_ip (PD) | [0.4,0.5)|long | 0.0713 | 0.0145 | 0.1154 | 76 | yes | no |
| P4_detection_score | P_ip (PD) | [0.5,0.7)|lat | 0.1024 | 0.0492 | 0.1437 | 152 | yes | no |
| P5_ego_speed | P_rel (PD7) | <1|lat | 0.0641 | 0.0442 | 0.0804 | 198 | yes | no |
| P5_ego_speed | P_rel (PD7) | <1|long | 0.0610 | 0.0454 | 0.0737 | 197 | yes | no |
| P5_ego_speed | P_rel (PD7) | [1,5)|lat | 0.0540 | 0.0425 | 0.0633 | 294 | yes | no |
| P5_ego_speed | P_near (SD1_7) | <1|long | 0.0573 | 0.0144 | 0.0905 | 133 | yes | no |
| P5_ego_speed | P_ip (PD) | <1|lat | 0.0694 | (marginal 0.0000) | (marginal 0.1765) | 18 | no (< 39 logs) | n/a |
| P5_ego_speed | P_ip (PD) | <1|long | 0.1140 | 0.0033 | 0.2032 | 43 | yes | no |
| P5_ego_speed | P_ip (PD) | >=10|lat | 0.0686 | 0.0024 | 0.1219 | 55 | yes | no |
| P5_ego_speed | P_ip (PD) | [1,5)|lat | 0.0621 | 0.0185 | 0.0973 | 118 | yes | no |
| P5_ego_speed | P_ip (PD) | [1,5)|long | 0.0540 | 0.0228 | 0.0791 | 211 | yes | no |
| P5_ego_speed | P_ip (PD) | [5,10)|lat | 0.0695 | 0.0244 | 0.1059 | 159 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 1-10|lat | 0.0759 | 0.0538 | 0.0948 | 343 | yes | yes |
| P6_gt_lidar_points | P_rel (PD7) | 1-10|long | 0.0546 | 0.0418 | 0.0656 | 351 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 11-50|lat | 0.0695 | 0.0505 | 0.0858 | 369 | yes | yes |
| P6_gt_lidar_points | P_rel (PD7) | 51-200|lat | 0.0546 | 0.0443 | 0.0635 | 372 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | 1-10|long | 0.0679 | (marginal 0.0000) | (marginal 0.1600) | 23 | no (< 39 logs) | n/a |
| P6_gt_lidar_points | P_ip (PD) | 1-10|long | 0.2111 | (marginal 0.0606) | (marginal 0.3778) | 15 | no (< 39 logs) | n/a |
| P6_gt_lidar_points | P_ip (PD) | 11-50|lat | 0.0714 | (marginal 0.0122) | (marginal 0.1487) | 37 | no (< 39 logs) | n/a |
| P6_gt_lidar_points | P_ip (PD) | 51-200|lat | 0.0853 | 0.0141 | 0.1411 | 87 | yes | no |
| P6_gt_lidar_points | P_ip (PD) | >200|lat | 0.0637 | 0.0304 | 0.0900 | 208 | yes | no |
| P7_city | P_rel (PD7) | ATX|long | 0.0574 | (marginal 0.0323) | (marginal 0.0836) | 9 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | MIA|lat | 0.0521 | 0.0406 | 0.0621 | 139 | yes | no |
| P7_city | P_rel (PD7) | PIT|lat | 0.0511 | 0.0424 | 0.0589 | 127 | yes | no |
| P7_city | P_ip (PD) | ATX|lat | 0.0693 | (marginal 0.0000) | (marginal 0.1429) | 6 | no (< 39 logs) | n/a |
| P7_city | P_ip (PD) | MIA|lat | 0.0567 | 0.0113 | 0.0918 | 91 | yes | no |
| P7_city | P_ip (PD) | PAO|lat | 0.2083 | (marginal 0.0000) | (marginal 0.6250) | 3 | no (< 39 logs) | n/a |
| P7_city | P_ip (PD) | PIT|lat | 0.0507 | 0.0039 | 0.0870 | 82 | yes | no |
| P7_city | P_ip (PD) | PIT|long | 0.0589 | 0.0243 | 0.0857 | 117 | yes | no |
| P7_city | P_ip (PD) | WDC|lat | 0.1784 | (marginal 0.0830) | (marginal 0.2919) | 26 | no (< 39 logs) | n/a |

## TAB (AB3DMOT, descriptive)

Flagged cells per arm and partition (P_rel / P_near / P_ip); '-' = none flagged; (n) = evaluable cells.

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| Mstar | <20 m|lat, 20-40 m|long (6) / <20 m|long (2) / - (5) | [0.5,3)|long, [0.5,3)|lat (8) / [0.5,3)|long (8) / - (7) | [5.5,8)|long (8) / - (8) / - (6) | 6-10|long, 6-10|lat, >10|long, >10|lat (8) / - (8) / - (8) | [0.4,0.5)|long, [0.4,0.5)|lat (6) / [0.4,0.5)|long, [0.4,0.5)|lat (6) / - (5) | <1|long, [1,5)|long, [1,5)|lat (8) / <1|long (8) / - (5) | 1-10|long, >200|long (8) / - (7) / - (5) | MIA|long, MIA|lat (8) / - (7) / - (4) |

Largest evaluable cell estimate with its simultaneous upper bound (P_rel):

| arm | P0 | P1 | P2 | P3 | P4 | P5 | P6 | P7 |
|---|---|---|---|---|---|---|---|---|
| Mstar | <20 m|lat 0.065 (UB 0.075) | [0.5,3)|long 0.109 (UB 0.123) | [5.5,8)|long 0.088 (UB 0.116) | >10|lat 0.075 (UB 0.090) | [0.4,0.5)|lat 0.079 (UB 0.088) | <1|long 0.076 (UB 0.090) | 1-10|long 0.067 (UB 0.083) | MIA|lat 0.065 (UB 0.077) |

M*: every cell with estimate above delta (all partitions and populations):

| partition | population | cell | E | simultaneous LB | simultaneous UB | logs | evaluable | flagged |
|---|---|---|---|---|---|---|---|---|
| P0_distance_range | P_rel (PD7) | 20-40 m|lat | 0.0556 | 0.0468 | 0.0634 | 371 | yes | no |
| P0_distance_range | P_rel (PD7) | 20-40 m|long | 0.0624 | 0.0526 | 0.0710 | 375 | yes | yes |
| P0_distance_range | P_rel (PD7) | <20 m|lat | 0.0645 | 0.0531 | 0.0745 | 375 | yes | yes |
| P0_distance_range | P_rel (PD7) | <20 m|long | 0.0570 | 0.0455 | 0.0670 | 372 | yes | no |
| P0_distance_range | P_rel (PD7) | >=40 m|long | 0.0582 | 0.0477 | 0.0674 | 372 | yes | no |
| P0_distance_range | P_near (SD1_7) | 20-40 m|long | 0.1429 | (marginal 0.0000) | (marginal 0.4000) | 7 | no (< 39 logs) | n/a |
| P0_distance_range | P_near (SD1_7) | <20 m|lat | 0.0574 | 0.0452 | 0.0679 | 362 | yes | no |
| P0_distance_range | P_near (SD1_7) | <20 m|long | 0.0681 | 0.0508 | 0.0830 | 345 | yes | yes |
| P0_distance_range | P_ip (PD) | 20-40 m|long | 0.0527 | 0.0282 | 0.0710 | 266 | yes | no |
| P1_track_speed | P_rel (PD7) | [0,0.5)|lat | 0.0544 | 0.0464 | 0.0611 | 370 | yes | no |
| P1_track_speed | P_rel (PD7) | [0,0.5)|long | 0.0515 | 0.0425 | 0.0591 | 375 | yes | no |
| P1_track_speed | P_rel (PD7) | [0.5,3)|lat | 0.0745 | 0.0614 | 0.0856 | 370 | yes | yes |
| P1_track_speed | P_rel (PD7) | [0.5,3)|long | 0.1090 | 0.0923 | 0.1230 | 374 | yes | yes |
| P1_track_speed | P_rel (PD7) | [3,8)|long | 0.0550 | 0.0365 | 0.0705 | 316 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0,0.5)|lat | 0.0547 | 0.0390 | 0.0670 | 321 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0,0.5)|long | 0.0626 | 0.0357 | 0.0838 | 309 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0.5,3)|lat | 0.0687 | 0.0394 | 0.0918 | 273 | yes | no |
| P1_track_speed | P_near (SD1_7) | [0.5,3)|long | 0.0977 | 0.0592 | 0.1281 | 242 | yes | yes |
| P1_track_speed | P_near (SD1_7) | [3,8)|long | 0.0821 | 0.0219 | 0.1296 | 121 | yes | no |
| P1_track_speed | P_ip (PD) | [0.5,3)|lat | 0.0539 | 0.0119 | 0.0848 | 115 | yes | no |
| P1_track_speed | P_ip (PD) | [0.5,3)|long | 0.0709 | 0.0320 | 0.0996 | 196 | yes | no |
| P2_track_length | P_rel (PD7) | <2|lat | 0.0589 | 0.0453 | 0.0705 | 320 | yes | no |
| P2_track_length | P_rel (PD7) | <2|long | 0.0548 | 0.0434 | 0.0646 | 336 | yes | no |
| P2_track_length | P_rel (PD7) | >=8|lat | 0.0526 | 0.0188 | 0.0816 | 124 | yes | no |
| P2_track_length | P_rel (PD7) | >=8|long | 0.0695 | 0.0358 | 0.0983 | 154 | yes | no |
| P2_track_length | P_rel (PD7) | [2,5.5)|lat | 0.0506 | 0.0418 | 0.0582 | 371 | yes | no |
| P2_track_length | P_rel (PD7) | [2,5.5)|long | 0.0551 | 0.0469 | 0.0621 | 375 | yes | no |
| P2_track_length | P_rel (PD7) | [5.5,8)|lat | 0.0552 | 0.0320 | 0.0751 | 256 | yes | no |
| P2_track_length | P_rel (PD7) | [5.5,8)|long | 0.0881 | 0.0552 | 0.1164 | 289 | yes | yes |
| P2_track_length | P_near (SD1_7) | <2|lat | 0.0542 | 0.0287 | 0.0745 | 206 | yes | no |
| P2_track_length | P_near (SD1_7) | >=8|lat | 0.0705 | 0.0052 | 0.1227 | 64 | yes | no |
| P2_track_length | P_near (SD1_7) | >=8|long | 0.1307 | 0.0103 | 0.2269 | 46 | yes | no |
| P2_track_length | P_near (SD1_7) | [2,5.5)|lat | 0.0601 | 0.0384 | 0.0774 | 334 | yes | no |
| P2_track_length | P_near (SD1_7) | [2,5.5)|long | 0.0628 | 0.0380 | 0.0825 | 316 | yes | no |
| P2_track_length | P_near (SD1_7) | [5.5,8)|lat | 0.0636 | 0.0247 | 0.0947 | 159 | yes | no |
| P2_track_length | P_ip (PD) | >=8|lat | 0.0815 | (marginal 0.0000) | (marginal 0.2037) | 15 | no (< 39 logs) | n/a |
| P3_track_age | P_rel (PD7) | 3-5|lat | 0.0580 | 0.0471 | 0.0676 | 373 | yes | no |
| P3_track_age | P_rel (PD7) | 3-5|long | 0.0572 | 0.0498 | 0.0638 | 375 | yes | no |
| P3_track_age | P_rel (PD7) | 6-10|lat | 0.0710 | 0.0594 | 0.0812 | 372 | yes | yes |
| P3_track_age | P_rel (PD7) | 6-10|long | 0.0648 | 0.0551 | 0.0734 | 375 | yes | yes |
| P3_track_age | P_rel (PD7) | >10|lat | 0.0750 | 0.0580 | 0.0899 | 351 | yes | yes |
| P3_track_age | P_rel (PD7) | >10|long | 0.0707 | 0.0571 | 0.0826 | 353 | yes | yes |
| P3_track_age | P_near (SD1_7) | 6-10|lat | 0.0561 | 0.0367 | 0.0710 | 336 | yes | no |
| P3_track_age | P_near (SD1_7) | 6-10|long | 0.0684 | 0.0413 | 0.0893 | 313 | yes | no |
| P3_track_age | P_near (SD1_7) | >10|lat | 0.0581 | 0.0365 | 0.0748 | 295 | yes | no |
| P3_track_age | P_near (SD1_7) | >10|long | 0.0691 | 0.0398 | 0.0916 | 289 | yes | no |
| P3_track_age | P_ip (PD) | >10|lat | 0.0823 | 0.0168 | 0.1313 | 88 | yes | no |
| P3_track_age | P_ip (PD) | >10|long | 0.0584 | 0.0252 | 0.0831 | 198 | yes | no |
| P4_detection_score | P_rel (PD7) | >=0.85|lat | 0.2500 | (marginal 0.0000) | (marginal 0.6667) | 4 | no (< 39 logs) | n/a |
| P4_detection_score | P_rel (PD7) | [0.4,0.5)|lat | 0.0789 | 0.0688 | 0.0879 | 375 | yes | yes |
| P4_detection_score | P_rel (PD7) | [0.4,0.5)|long | 0.0784 | 0.0694 | 0.0865 | 375 | yes | yes |
| P4_detection_score | P_near (SD1_7) | >=0.85|lat | 1.0000 | (marginal 1.0000) | (marginal 1.0000) | 1 | no (< 39 logs) | n/a |
| P4_detection_score | P_near (SD1_7) | [0.4,0.5)|lat | 0.0810 | 0.0606 | 0.0981 | 331 | yes | yes |
| P4_detection_score | P_near (SD1_7) | [0.4,0.5)|long | 0.0827 | 0.0546 | 0.1062 | 308 | yes | yes |
| P4_detection_score | P_near (SD1_7) | [0.5,0.7)|long | 0.0567 | 0.0350 | 0.0749 | 314 | yes | no |
| P4_detection_score | P_ip (PD) | [0.4,0.5)|long | 0.0502 | 0.0275 | 0.0674 | 261 | yes | no |
| P5_ego_speed | P_rel (PD7) | <1|lat | 0.0642 | 0.0437 | 0.0823 | 195 | yes | no |
| P5_ego_speed | P_rel (PD7) | <1|long | 0.0763 | 0.0605 | 0.0902 | 196 | yes | yes |
| P5_ego_speed | P_rel (PD7) | >=10|lat | 0.0528 | 0.0319 | 0.0714 | 139 | yes | no |
| P5_ego_speed | P_rel (PD7) | [1,5)|lat | 0.0626 | 0.0502 | 0.0734 | 294 | yes | yes |
| P5_ego_speed | P_rel (PD7) | [1,5)|long | 0.0710 | 0.0573 | 0.0831 | 294 | yes | yes |
| P5_ego_speed | P_rel (PD7) | [5,10)|lat | 0.0534 | 0.0449 | 0.0609 | 303 | yes | no |
| P5_ego_speed | P_near (SD1_7) | <1|long | 0.1252 | 0.0627 | 0.1756 | 124 | yes | yes |
| P5_ego_speed | P_near (SD1_7) | >=10|lat | 0.0685 | 0.0229 | 0.1052 | 109 | yes | no |
| P5_ego_speed | P_near (SD1_7) | >=10|long | 0.0791 | 0.0226 | 0.1247 | 93 | yes | no |
| P5_ego_speed | P_near (SD1_7) | [1,5)|lat | 0.0593 | 0.0358 | 0.0783 | 243 | yes | no |
| P5_ego_speed | P_near (SD1_7) | [1,5)|long | 0.0606 | 0.0310 | 0.0845 | 227 | yes | no |
| P5_ego_speed | P_near (SD1_7) | [5,10)|lat | 0.0506 | 0.0327 | 0.0651 | 274 | yes | no |
| P5_ego_speed | P_near (SD1_7) | [5,10)|long | 0.0544 | 0.0282 | 0.0756 | 256 | yes | no |
| P5_ego_speed | P_ip (PD) | <1|lat | 0.0635 | (marginal 0.0033) | (marginal 0.1346) | 14 | no (< 39 logs) | n/a |
| P5_ego_speed | P_ip (PD) | <1|long | 0.0568 | (marginal 0.0148) | (marginal 0.1085) | 37 | no (< 39 logs) | n/a |
| P5_ego_speed | P_ip (PD) | [1,5)|lat | 0.0606 | 0.0110 | 0.0996 | 103 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 1-10|lat | 0.0525 | 0.0360 | 0.0674 | 323 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 1-10|long | 0.0674 | 0.0506 | 0.0825 | 339 | yes | yes |
| P6_gt_lidar_points | P_rel (PD7) | 11-50|lat | 0.0571 | 0.0463 | 0.0668 | 362 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 11-50|long | 0.0550 | 0.0453 | 0.0637 | 371 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 51-200|lat | 0.0572 | 0.0476 | 0.0659 | 372 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | 51-200|long | 0.0514 | 0.0436 | 0.0584 | 375 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | >200|lat | 0.0550 | 0.0461 | 0.0632 | 375 | yes | no |
| P6_gt_lidar_points | P_rel (PD7) | >200|long | 0.0658 | 0.0544 | 0.0761 | 372 | yes | yes |
| P6_gt_lidar_points | P_near (SD1_7) | 1-10|lat | 0.0624 | -0.0224 | 0.1295 | 49 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | 11-50|lat | 0.0770 | 0.0130 | 0.1278 | 71 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | 11-50|long | 0.0913 | 0.0030 | 0.1614 | 49 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | 51-200|lat | 0.0863 | 0.0450 | 0.1190 | 178 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | 51-200|long | 0.0646 | 0.0248 | 0.0961 | 149 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | >200|lat | 0.0580 | 0.0410 | 0.0715 | 361 | yes | no |
| P6_gt_lidar_points | P_near (SD1_7) | >200|long | 0.0639 | 0.0428 | 0.0806 | 339 | yes | no |
| P6_gt_lidar_points | P_ip (PD) | 1-10|lat | 0.1111 | (marginal 0.0000) | (marginal 0.3333) | 9 | no (< 39 logs) | n/a |
| P6_gt_lidar_points | P_ip (PD) | 1-10|long | 0.1316 | (marginal 0.0227) | (marginal 0.2647) | 19 | no (< 39 logs) | n/a |
| P6_gt_lidar_points | P_ip (PD) | 11-50|lat | 0.0655 | (marginal 0.0095) | (marginal 0.1389) | 28 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | ATX|lat | 0.0619 | (marginal 0.0340) | (marginal 0.0923) | 9 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | ATX|long | 0.0700 | (marginal 0.0279) | (marginal 0.1147) | 9 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | DTW|lat | 0.0519 | 0.0344 | 0.0672 | 44 | yes | no |
| P7_city | P_rel (PD7) | DTW|long | 0.0508 | 0.0250 | 0.0734 | 44 | yes | no |
| P7_city | P_rel (PD7) | MIA|lat | 0.0649 | 0.0512 | 0.0769 | 139 | yes | yes |
| P7_city | P_rel (PD7) | MIA|long | 0.0622 | 0.0505 | 0.0725 | 139 | yes | yes |
| P7_city | P_rel (PD7) | PAO|lat | 0.0631 | (marginal 0.0264) | (marginal 0.1155) | 10 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | PAO|long | 0.0532 | (marginal 0.0302) | (marginal 0.0838) | 10 | no (< 39 logs) | n/a |
| P7_city | P_rel (PD7) | PIT|lat | 0.0605 | 0.0496 | 0.0701 | 127 | yes | no |
| P7_city | P_rel (PD7) | PIT|long | 0.0599 | 0.0484 | 0.0699 | 127 | yes | no |
| P7_city | P_rel (PD7) | WDC|long | 0.0587 | 0.0367 | 0.0780 | 46 | yes | no |
| P7_city | P_near (SD1_7) | ATX|long | 0.1544 | (marginal 0.0000) | (marginal 0.3317) | 9 | no (< 39 logs) | n/a |
| P7_city | P_near (SD1_7) | DTW|lat | 0.0521 | -0.0019 | 0.0933 | 44 | yes | no |
| P7_city | P_near (SD1_7) | DTW|long | 0.0676 | (marginal 0.0187) | (marginal 0.1280) | 35 | no (< 39 logs) | n/a |
| P7_city | P_near (SD1_7) | MIA|lat | 0.0721 | 0.0376 | 0.0984 | 133 | yes | no |
| P7_city | P_near (SD1_7) | MIA|long | 0.0745 | 0.0373 | 0.1029 | 128 | yes | no |
| P7_city | P_near (SD1_7) | PIT|lat | 0.0540 | 0.0365 | 0.0672 | 124 | yes | no |
| P7_city | P_near (SD1_7) | PIT|long | 0.0561 | 0.0320 | 0.0744 | 124 | yes | no |
| P7_city | P_near (SD1_7) | WDC|long | 0.0734 | -0.0177 | 0.1427 | 42 | yes | no |
| P7_city | P_ip (PD) | ATX|lat | 0.0583 | (marginal 0.0000) | (marginal 0.1667) | 5 | no (< 39 logs) | n/a |
| P7_city | P_ip (PD) | MIA|lat | 0.0601 | 0.0127 | 0.0963 | 83 | yes | no |
| P7_city | P_ip (PD) | WDC|lat | 0.0625 | (marginal 0.0042) | (marginal 0.1500) | 21 | no (< 39 logs) | n/a |

Missing-bin records (non-finite partition value) and detection scores below 0.4 are listed in the JSON (missing_bin_records, score_below_0.4_records).
