# X3 A4 (2): loop-mode replay on Argoverse 2 (descriptive)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A4)

k8_sim_v04.run_episode, delays 0, 2, 4 keyframes, 375 logs; endpoints by the record's loop functions; keys (log, delay); log bootstrap B = 4000, seed [20261201, i, 12]. **No ranking or claim:** descriptive: log replay with non-reactive agents (nuPlan's CL-NR); an arm that is infeasible more often runs more often at a backed-off margin (K6 R09b MJ1), so collision contrasts are not read as calibration effects (D10 section 2).

## T1

| arm | episodes | at fault, tracked (per 1000; 95 % CI) | at fault, untracked (per 1000) | progress | infeasible frames | hard braking | divergence share |
|---|---|---|---|---|---|---|---|
| Mstar | 1054 | 31 (29.41; 19.98-41.75) | 0 (0.00) | 0.8821 | 0.1834 | 0.0634 | 0.2087 |
| B0 | 1054 | 49 (46.49; 34.39-61.46) | 2 (1.90) | 0.7605 | 0.3305 | 0.1014 | 0.3357 |
| B4 | 1054 | 41 (38.90; 27.91-52.77) | 1 (0.95) | 0.8304 | 0.1849 | 0.0762 | 0.2496 |
| B6 | 1054 | 34 (32.26; 22.34-45.08) | 1 (0.95) | 0.8554 | 0.1467 | 0.0671 | 0.2206 |
| X3E1_B8 | 1054 | 23 (21.82; 13.83-32.74) | 2 (1.90) | 0.8455 | 0.2977 | 0.0779 | 0.2510 |
| A_B6_composite | 1054 | 51 (48.39; 36.03-63.62) | 5 (4.74) | 0.7223 | 0.5103 | 0.1186 | 0.4012 |

M* minus arm (key level, 95 % CI):

| arm | endpoint | M* - arm | 95 % CI |
|---|---|---|---|
| B0 | collisions_at_fault_tracked_per_episode | -0.0171 | [-0.0332, -0.0019] |
| B0 | collisions_at_fault_untracked_per_episode | -0.0019 | [-0.0048, 0.0000] |
| B0 | progress | 0.1216 | [0.1023, 0.1411] |
| B0 | infeasible_frame_share | -0.1469 | [-0.1706, -0.1243] |
| B0 | hard_brake_frame_share | -0.0380 | [-0.0438, -0.0319] |
| B0 | divergence_share | -0.1271 | [-0.1484, -0.1059] |
| B0 | progress_ratio | 0.1204 | [0.1008, 0.1391] |
| B4 | collisions_at_fault_tracked_per_episode | -0.0095 | [-0.0238, 0.0047] |
| B4 | collisions_at_fault_untracked_per_episode | -0.0009 | [-0.0029, 0.0000] |
| B4 | progress | 0.0518 | [0.0358, 0.0680] |
| B4 | infeasible_frame_share | -0.0016 | [-0.0202, 0.0165] |
| B4 | hard_brake_frame_share | -0.0128 | [-0.0182, -0.0073] |
| B4 | divergence_share | -0.0409 | [-0.0597, -0.0215] |
| B4 | progress_ratio | 0.0507 | [0.0351, 0.0665] |
| B6 | collisions_at_fault_tracked_per_episode | -0.0028 | [-0.0142, 0.0085] |
| B6 | collisions_at_fault_untracked_per_episode | -0.0009 | [-0.0029, 0.0000] |
| B6 | progress | 0.0267 | [0.0133, 0.0403] |
| B6 | infeasible_frame_share | 0.0365 | [0.0210, 0.0517] |
| B6 | hard_brake_frame_share | -0.0036 | [-0.0084, 0.0011] |
| B6 | divergence_share | -0.0119 | [-0.0278, 0.0042] |
| B6 | progress_ratio | 0.0276 | [0.0141, 0.0414] |
| X3E1_B8 | collisions_at_fault_tracked_per_episode | 0.0076 | [-0.0029, 0.0199] |
| X3E1_B8 | collisions_at_fault_untracked_per_episode | -0.0019 | [-0.0058, 0.0000] |
| X3E1_B8 | progress | 0.0367 | [0.0248, 0.0488] |
| X3E1_B8 | infeasible_frame_share | -0.1147 | [-0.1284, -0.1020] |
| X3E1_B8 | hard_brake_frame_share | -0.0145 | [-0.0181, -0.0105] |
| X3E1_B8 | divergence_share | -0.0424 | [-0.0549, -0.0302] |
| X3E1_B8 | progress_ratio | 0.0358 | [0.0242, 0.0476] |
| A_B6_composite | collisions_at_fault_tracked_per_episode | -0.0190 | [-0.0347, -0.0058] |
| A_B6_composite | collisions_at_fault_untracked_per_episode | -0.0047 | [-0.0115, 0.0000] |
| A_B6_composite | progress | 0.1598 | [0.1390, 0.1803] |
| A_B6_composite | infeasible_frame_share | -0.3268 | [-0.3535, -0.3008] |
| A_B6_composite | hard_brake_frame_share | -0.0551 | [-0.0614, -0.0486] |
| A_B6_composite | divergence_share | -0.1925 | [-0.2160, -0.1694] |
| A_B6_composite | progress_ratio | 0.1558 | [0.1357, 0.1761] |

## T3

| arm | episodes | at fault, tracked (per 1000; 95 % CI) | at fault, untracked (per 1000) | progress | infeasible frames | hard braking | divergence share |
|---|---|---|---|---|---|---|---|
| Mstar | 1054 | 26 (24.67; 16.11-36.14) | 5 (4.74) | 0.8888 | 0.2499 | 0.0683 | 0.2128 |
| B0 | 1054 | 40 (37.95; 27.11-51.68) | 3 (2.85) | 0.7810 | 0.8057 | 0.1118 | 0.3709 |
| B4 | 1054 | 34 (32.26; 22.34-45.08) | 4 (3.80) | 0.8571 | 0.2966 | 0.0845 | 0.2759 |
| B6 | 1054 | 28 (26.57; 17.65-38.39) | 3 (2.85) | 0.8824 | 0.2307 | 0.0717 | 0.2268 |
| X3E1_B8 | 1054 | 32 (30.36; 20.77-42.86) | 3 (2.85) | 0.7977 | 0.4625 | 0.1006 | 0.3263 |
| A_B6_composite | 1054 | 41 (38.90; 27.91-52.77) | 2 (1.90) | 0.8166 | 0.4674 | 0.1031 | 0.3159 |

M* minus arm (key level, 95 % CI):

| arm | endpoint | M* - arm | 95 % CI |
|---|---|---|---|
| B0 | collisions_at_fault_tracked_per_episode | -0.0133 | [-0.0274, -0.0019] |
| B0 | collisions_at_fault_untracked_per_episode | 0.0019 | [-0.0038, 0.0077] |
| B0 | progress | 0.1079 | [0.0874, 0.1284] |
| B0 | infeasible_frame_share | -0.5549 | [-0.5777, -0.5327] |
| B0 | hard_brake_frame_share | -0.0436 | [-0.0501, -0.0367] |
| B0 | divergence_share | -0.1580 | [-0.1814, -0.1344] |
| B0 | progress_ratio | 0.1048 | [0.0850, 0.1250] |
| B4 | collisions_at_fault_tracked_per_episode | -0.0076 | [-0.0199, 0.0028] |
| B4 | collisions_at_fault_untracked_per_episode | 0.0009 | [0.0000, 0.0029] |
| B4 | progress | 0.0317 | [0.0193, 0.0446] |
| B4 | infeasible_frame_share | -0.0467 | [-0.0615, -0.0321] |
| B4 | hard_brake_frame_share | -0.0162 | [-0.0210, -0.0116] |
| B4 | divergence_share | -0.0631 | [-0.0794, -0.0470] |
| B4 | progress_ratio | 0.0317 | [0.0195, 0.0444] |
| B6 | collisions_at_fault_tracked_per_episode | -0.0019 | [-0.0096, 0.0048] |
| B6 | collisions_at_fault_untracked_per_episode | 0.0019 | [0.0000, 0.0048] |
| B6 | progress | 0.0064 | [-0.0026, 0.0155] |
| B6 | infeasible_frame_share | 0.0187 | [0.0098, 0.0278] |
| B6 | hard_brake_frame_share | -0.0034 | [-0.0067, -0.0000] |
| B6 | divergence_share | -0.0140 | [-0.0243, -0.0037] |
| B6 | progress_ratio | 0.0059 | [-0.0028, 0.0147] |
| X3E1_B8 | collisions_at_fault_tracked_per_episode | -0.0057 | [-0.0133, 0.0010] |
| X3E1_B8 | collisions_at_fault_untracked_per_episode | 0.0019 | [-0.0019, 0.0057] |
| X3E1_B8 | progress | 0.0911 | [0.0744, 0.1082] |
| X3E1_B8 | infeasible_frame_share | -0.2119 | [-0.2302, -0.1947] |
| X3E1_B8 | hard_brake_frame_share | -0.0323 | [-0.0373, -0.0274] |
| X3E1_B8 | divergence_share | -0.1135 | [-0.1319, -0.0956] |
| X3E1_B8 | progress_ratio | 0.0886 | [0.0721, 0.1053] |
| A_B6_composite | collisions_at_fault_tracked_per_episode | -0.0142 | [-0.0254, -0.0047] |
| A_B6_composite | collisions_at_fault_untracked_per_episode | 0.0028 | [-0.0010, 0.0075] |
| A_B6_composite | progress | 0.0722 | [0.0585, 0.0862] |
| A_B6_composite | infeasible_frame_share | -0.2172 | [-0.2319, -0.2028] |
| A_B6_composite | hard_brake_frame_share | -0.0348 | [-0.0398, -0.0301] |
| A_B6_composite | divergence_share | -0.1030 | [-0.1187, -0.0871] |
| A_B6_composite | progress_ratio | 0.0702 | [0.0567, 0.0841] |
