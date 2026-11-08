# X3 amendment A1: heading error behind the lateral diagnosis (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Amendment `20_DESIGN/X3_PLAN_AMENDMENT_A1_v01.md` (sha256 a5cc3261...). Data: X2 (nuScenes train, 700 scenes, T1 = CANMOT, in-path cars, 2 s, sigma_a = 0.10 m). Items rebuilt by importing the frozen X2 code read-only (no main, no guard).

## Reproduction gate

| Cell | n (rebuilt / record) | scenes | E_rec (rebuilt / record) | equal |
|---|---|---|---|---|
| car, < 20 m, lat | 3396 / 3396 | 442 / 442 | 0.19405182567726736 / 0.19405182567726736 | yes |
| car, 20–40 m, lat | 1229 / 1229 | 219 / 219 | 0.27176566314076483 / 0.27176566314076483 | yes |
| car, < 20 m, long | 8038 / 8038 | 529 / 529 | 0.004354316994277184 / 0.004354316994277184 | yes |
| car, 20–40 m, long | 3522 / 3522 | 345 / 345 | 0.010789324247586598 / 0.010789324247586598 | yes |

Gate: **PASSED**. Additional checks: truth-oriented decision cells equal; all other h2s cells equal; pairing counts equal.

## Estimate-oriented (X2 primary)

| Cell | n | <= 10 deg | (10, 20] deg | > 20 deg | exceedances from > 20 deg | E (<= 20 deg) [95 % CI] | n (<= 20 deg) | threshold of record | E (all, record) |
|---|---|---|---|---|---|---|---|---|---|
| car, < 20 m, lat | 3396 | 0.458 | 0.155 | 0.387 | 0.411 (271 of 659) | 0.186 [0.154, 0.223] | 2081 | 0.0775 | 0.194 |
| car, 20–40 m, lat | 1229 | 0.418 | 0.229 | 0.352 | 0.419 (140 of 334) | 0.244 [0.185, 0.306] | 796 | 0.0816 | 0.272 |
| car, < 20 m, long | 8038 | 0.781 | 0.092 | 0.128 | 0.057 (2 of 35) | 0.005 [0.003, 0.007] | 7013 | 0.0646 | 0.004 |
| car, 20–40 m, long | 3522 | 0.793 | 0.089 | 0.119 | 0.000 (0 of 38) | 0.012 [0.007, 0.018] | 3104 | 0.0500 | 0.011 |

## Truth-oriented (X2 a5 definition)

| Cell | n | <= 10 deg | (10, 20] deg | > 20 deg | exceedances from > 20 deg | E (<= 20 deg) [95 % CI] | n (<= 20 deg) | threshold of record | E (all, record) |
|---|---|---|---|---|---|---|---|---|---|
| car, < 20 m, lat | 3554 | 0.460 | 0.157 | 0.383 | 0.444 (244 of 549) | 0.139 [0.111, 0.170] | 2193 | 0.0500 | 0.154 |
| car, 20–40 m, lat | 1248 | 0.418 | 0.234 | 0.348 | 0.493 (140 of 284) | 0.177 [0.122, 0.237] | 814 | 0.0500 | 0.228 |
| car, < 20 m, long | 8233 | 0.777 | 0.090 | 0.132 | 0.100 (1 of 10) | 0.001 [0.001, 0.002] | 7143 | 0.0500 | 0.001 |
| car, 20–40 m, long | 3522 | 0.793 | 0.089 | 0.119 | 0.000 (0 of 37) | 0.012 [0.007, 0.018] | 3104 | 0.0500 | 0.011 |

## Reading (fixed in A1 section ii)

- car|<20|lat, estimate-oriented: E on items with heading error <= 20 deg is 0.186 [0.154, 0.223] against the threshold 0.0775; it still exceeds the threshold, so by A1 (ii) the lateral under-coverage there is not explained by heading error (the 95 % interval lies entirely above the threshold).
- car|<20|lat, truth-oriented: E on items with heading error <= 20 deg is 0.139 [0.111, 0.170] against the threshold 0.0500; it still exceeds the threshold, so by A1 (ii) the lateral under-coverage there is not explained by heading error (the 95 % interval lies entirely above the threshold).
- car|20-40|lat, estimate-oriented: E on items with heading error <= 20 deg is 0.244 [0.185, 0.306] against the threshold 0.0816; it still exceeds the threshold, so by A1 (ii) the lateral under-coverage there is not explained by heading error (the 95 % interval lies entirely above the threshold).
- car|20-40|lat, truth-oriented: E on items with heading error <= 20 deg is 0.177 [0.122, 0.237] against the threshold 0.0500; it still exceeds the threshold, so by A1 (ii) the lateral under-coverage there is not explained by heading error (the 95 % interval lies entirely above the threshold).
- Longitudinal cells are reported for completeness; A1 (ii) states its reading for the lateral cells.

## Method notes

- Heading error = |wrap(psi_track - psi_annotation)| at the decision keyframe k, folded to [0, 90] deg (min(d, 180 - d)). psi_track is the record's box yaw at k (quat_yaw of the exported rotation), which defines the item's axes at 2 s; psi_annotation is the yaw of the annotation build_table paired at k (its centre equals the row's gx, gy exactly). Both are global-frame yaws from the same quat_yaw formula.
- Exceedance: U > z_0.95 = 1.6448536269514722 (L.Z95, the value X2 used; the amendment writes 1.645).
- E is record-weighted as X2's E_rec: exceedances / items, items pooled over scenes.
- Bootstrap: scene-cluster, B = 2000, numpy default_rng([20261211, cell]) with cell = 0..3 in X2's DEC order (car <20 lat, car 20-40 lat, car <20 long, car 20-40 long); the same seed (hence the same scene weights) is used for the estimate- and truth-oriented versions of a cell. Weights: L.boot_weights (multinomial over the 700 scenes, X2's convention); replicate = ratio of weighted sums; pointwise 95 % percentile interval (not X2's simultaneous sup-t band).
- Thresholds: estimate-oriented = max(0.05, E0) of record (family_h2s.primary); truth-oriented = the threshold of record in truth_oriented_decision_band (0.05, as X2 ran a5 with thr = {}). The estimate-oriented E0 threshold is listed for reference.
- Truth orientation is X2's (cell_items orient='truth'): the same track axes; the separating filter and sign use the annotation's centre at 2 s in place of the estimate. The heading error of an item is the same in both orientations (it belongs to the record at k).
- Memory-lean rebuild (about 2 GB free): lean streaming ground-truth loader (same samples, same per-sample annotation order, only the keys the frozen functions read, plus yaw); build_table per export worker (scenes disjoint across workers, asserted); only paired, in-path rows at k kept for the horizon step (the only rows cell_items uses). The reproduction gate checks the result end to end.

Integrity: C1_RUN_LOG sha256 8bc6235d... before and after; c1_av2_v01 manifest identical before and after: True.

