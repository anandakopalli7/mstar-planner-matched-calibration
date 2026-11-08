# X3 A3 (iii): M*'s cross-fitted exceedance on its own calibration items

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)** -- added after review (amendment A3)

Items of record (every separating axis at the reference pose); each held-out fold's fits_within thresholds applied to that fold's items, exceedance U = D / sd > c. Strata: own-threshold L0 stratum (the item's threshold is its stratum's own fit) x in-path part, check times pooled; log-weighted rate; one-sided simultaneous sup-t at 0.95 over the evaluable strata (>= 39 logs); B = 4000, seed [20261201, i, 9]. A consistency check of the theory on the data, not a test of the planner-facing claim.

## T1

- items 947306; evaluable own-threshold strata 93; flagged 0: none
- pooled own-threshold items: 0.0429 [0.0402, 0.0459] (940940 items); fallback items: share 0.007, pooled 0.0396 [0.0255, 0.0567]
- fallback by level (share of items): {"0": 0.993, "1": 0.005, "2": 0.001, "3": 0.0}; pooled rate by level: {"1": 0.0379, "2": 0.0504, "3": 0.0}
- largest stratum estimate: large|<20|long|turning|not_inpath 0.0714 (UB 0.1679)

## T3

- items 947746; evaluable own-threshold strata 92; flagged 0: none
- pooled own-threshold items: 0.0418 [0.0392, 0.0445] (941556 items); fallback items: share 0.007, pooled 0.0429 [0.0280, 0.0599]
- fallback by level (share of items): {"0": 0.993, "1": 0.005, "2": 0.001, "3": 0.0}; pooled rate by level: {"1": 0.0444, "2": 0.0285, "3": 0.0887}
- largest stratum estimate: car|<20|long|turning|inpath 0.0567 (UB 0.1031)
