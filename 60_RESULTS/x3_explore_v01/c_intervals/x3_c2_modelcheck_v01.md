# X3 (c2) supplement: does the simulation reproduce the observed log-level dispersion? (v01)

**X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)**

Added, not pre-specified. Model SE (beta-binomial with the ANOVA ICC, at the cell's observed rate) against the record's bootstrap SE of the same cell, evaluable cells only. JSON: `x3_c2_modelcheck_v01.json`.

| Tracker | Arm / population | Cells | Median ratio model/record | Min | Max | Share of cells below 0.8 |
|---|---|---|---|---|---|---|
| t1 | Mstar|PD7_primary | 27 | 0.91 | 0.62 | 1.13 | 0.26 |
| t1 | Mstar|SD1_7_gap_le_5m | 16 | 0.92 | 0.74 | 1.09 | 0.19 |
| t1 | Mstar|PD_inpath | 8 | 0.96 | 0.78 | 1.13 | 0.12 |
| t1 | B0|PD7_primary | 26 | 0.90 | 0.39 | 2.31 | 0.32 |
| t1 | B1|PD7_primary | 26 | 0.92 | 0.33 | 1.87 | 0.27 |
| t1 | B4|PD7_primary | 27 | 0.92 | 0.46 | 1.52 | 0.22 |
| t1 | B6|PD7_primary | 27 | 0.89 | 0.49 | 1.12 | 0.30 |
| t1 | B9|PD7_primary | 25 | 1.04 | 0.35 | 1.92 | 0.25 |
| t1 | RETUNED|PD7_primary | 26 | 0.93 | 0.37 | 2.45 | 0.36 |
| t3 | Mstar|PD7_primary | 27 | 0.86 | 0.64 | 1.24 | 0.30 |
| t3 | Mstar|SD1_7_gap_le_5m | 16 | 0.94 | 0.74 | 1.25 | 0.12 |
| t3 | Mstar|PD_inpath | 8 | 0.95 | 0.90 | 1.18 | 0.00 |
| t3 | B1|PD7_primary | 25 | 0.92 | 0.46 | 1.41 | 0.12 |
| t3 | B4|PD7_primary | 26 | 0.85 | 0.63 | 1.34 | 0.27 |
| t3 | B6|PD7_primary | 27 | 0.88 | 0.60 | 1.22 | 0.30 |
| t3 | B9|PD7_primary | 26 | 0.94 | 0.40 | 1.63 | 0.32 |
| t3 | RETUNED|PD7_primary | 25 | 0.92 | 0.68 | 2.89 | 0.20 |

Reading: a ratio below 1 means the simulated per-log rates are less dispersed than the observed ones, so quantities that depend on the scale (power or flag rates at the observed rates) are overstated by the simulation; the false-removal rates and coverages at truth delta are computed inside the simulated world and depend mainly on the shape.

Code: `50_CODE/x3/x3_stats_c2_modelcheck_v01.py`.
