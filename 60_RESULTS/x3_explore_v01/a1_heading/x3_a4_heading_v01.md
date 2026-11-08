# X3 amendment A4 (4): heading error, stricter cuts and annotation axes (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

**added after review (amendment A4).** Amendment `20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md` (sha256 ab19dd66...), section (4); extends A1 (`x3_a1_heading_v01.json`) on the same rebuilt X2 items (nuScenes train, 700 scenes, T1 = CANMOT, in-path cars, 2 s, sigma_a = 0.10 m).

Reuse check: the A1 rows reloaded from the checkpoint reproduce X2's n, scenes and E_rec exactly in the four decision cells, estimate- and truth-oriented: **yes**.

## Estimate-oriented (X2 primary)

| Cell | E, all items (record) | E, heading error <= 5 deg [95 % CI] | n (scenes) | E, heading error <= 10 deg [95 % CI] | n (scenes) | E, annotation axes [95 % CI] | n (scenes) | threshold of record |
|---|---|---|---|---|---|---|---|---|
| car, < 20 m, lat | 0.194 (3396) | 0.139 [0.110, 0.171] | 1163 (322) | 0.162 [0.131, 0.194] | 1556 (352) | 0.124 [0.102, 0.146] | 3396 (442) | 0.0775 |
| car, 20–40 m, lat | 0.272 (1229) | 0.232 [0.158, 0.314] | 276 (107) | 0.233 [0.176, 0.297] | 514 (144) | 0.108 [0.074, 0.143] | 1229 (219) | 0.0816 |
| car, < 20 m, long | 0.004 (8038) | 0.004 [0.002, 0.006] | 5313 (455) | 0.004 [0.002, 0.006] | 6275 (474) | 0.007 [0.005, 0.010] | 8038 (529) | 0.0646 |
| car, 20–40 m, long | 0.011 (3522) | 0.013 [0.006, 0.021] | 2418 (255) | 0.014 [0.008, 0.020] | 2792 (287) | 0.020 [0.013, 0.028] | 3522 (345) | 0.0500 |

## Truth-oriented (X2 a5 definition)

| Cell | E, all items (record) | E, heading error <= 5 deg [95 % CI] | n (scenes) | E, heading error <= 10 deg [95 % CI] | n (scenes) | E, annotation axes [95 % CI] | n (scenes) | threshold of record |
|---|---|---|---|---|---|---|---|---|
| car, < 20 m, lat | 0.154 (3554) | 0.101 [0.078, 0.126] | 1193 (339) | 0.122 [0.095, 0.150] | 1634 (376) | 0.089 [0.070, 0.108] | 3554 (454) | 0.0500 |
| car, 20–40 m, lat | 0.228 (1248) | 0.123 [0.069, 0.182] | 285 (112) | 0.144 [0.094, 0.203] | 522 (149) | 0.064 [0.040, 0.093] | 1248 (224) | 0.0500 |
| car, < 20 m, long | 0.001 (8233) | 0.001 [0.000, 0.001] | 5417 (457) | 0.001 [0.000, 0.001] | 6398 (474) | 0.002 [0.001, 0.004] | 8233 (530) | 0.0500 |
| car, 20–40 m, long | 0.011 (3522) | 0.012 [0.006, 0.020] | 2418 (255) | 0.013 [0.007, 0.020] | 2792 (287) | 0.019 [0.012, 0.028] | 3522 (345) | 0.0500 |

## Method notes

- Same items as A1 and X2 (L.cell_items on the A1 rebuild, reloaded unchanged; n, scenes and E_rec re-checked equal to the X2 result of record in all eight cell-orientation pairs).
- Heading error as A1: |wrap(psi_track - psi_annotation)| at the decision keyframe k, folded to [0, 90] deg; (4a) keeps items with heading error <= 5 deg or <= 10 deg; E record-weighted (exceedances / items), exceedance U > z_0.95 = 1.6448536269514722.
- (4b) Annotation axes: for an item on the track's lateral (longitudinal) axis, the annotated box's lateral (longitudinal) axis b at keyframe k (the annotation paired at k, as in A1; A4 does not name the keyframe, and k keeps the analysis at decision time, swapping only the heading). Error (g - m) projected on b, signed toward the ego as X2 orients: sign of b.(c - m) estimate-oriented, of b.(c - g) truth-oriented (c = CTRV-predicted ego centre at 2 s, m = predicted mean, g = annotation centre at 2 s). sd = sqrt(b' S b + 0.10^2) from the same predicted covariance S. The item set is X2's: the separating filter is not re-evaluated along b.
- Code-path check: the (4b) computation run with the track's own yaw in place of the annotation's reproduces X2's U (max abs difference per cell in reuse_gate, tolerance 1e-9).
- Bootstrap: scene-cluster, B = 2000, numpy default_rng([20261211, cell, k]); cell = 0..3 in X2's DEC order (car <20 lat, car 20-40 lat, car <20 long, car 20-40 long); k = 1 (<= 5 deg), 2 (<= 10 deg), 3 (annotation axes); the same seed for the estimate- and truth-oriented versions. Weights L.boot_weights (multinomial over the 700 scenes, X2's convention); replicate = ratio of weighted sums; pointwise 95 % percentile interval.
- Thresholds listed for reference only (A4 (4) fixes no reading): estimate-oriented max(0.05, E0) of record; truth-oriented 0.05 of record.

Integrity: C1_RUN_LOG sha256 8bc6235d... before and after; c1_av2_v01 manifest identical before and after: True.

