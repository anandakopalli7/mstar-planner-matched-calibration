# X1 results: decision-projected calibration audit on nuScenes val (v01, 30 Oct 2026)

**Run.** Pre-registration v02 (SHA-256 `ab9b8e05…709485`, 25 files hashed, frozen before any residual). Analysis `x1_full_v02.py`. Result `x1_full_v02_result.json`.

**Integrity.**
- Q0 passes: 6,019 tokens, 381,553 records, C6 = 0.
- Q1 = 0.639: the paired share of in-path records.

**Eligible cells.** 4 per family, all cars: < 20 m and 20–40 m, longitudinal and lateral.

## Verdict on G1: NOT SHOWN, in either family

No eligible cell FAILS against its threshold under the 97.5 % simultaneous band, so conditions (a2)–(a5) and (b) are never reached.

### Family t0: the tracker's output now

| Cell | E (record-weighted) | Threshold max(0.05, E⁰) | Simultaneous 97.5 % band | Verdict |
|---|---|---|---|---|
| car < 20 m, longitudinal | 0.005 | 0.050 | [0.000, 0.010] | OVERCOVERS |
| car < 20 m, lateral | 0.042 | 0.061 | [0.001, 0.083] | CONSISTENT |
| car 20–40 m, longitudinal | 0.033 | 0.052 | [0.015, 0.050] | OVERCOVERS |
| car 20–40 m, lateral | 0.046 | 0.061 | [−0.002, 0.094] | CONSISTENT |

- CANMOT's covariance for nearby in-path cars is **conservative or consistent** at t0.
- NEES for car < 20 m is 15.1, but its CI [0.58, 50.5] is wide and heavy-tailed, giving CONSISTENT.
- K5 is not supported at t0: no cell is significantly under-covered.

### Family h2s: predicted 2 s ahead with CANMOT's own model (what a planner uses)

| Cell | E | Threshold | Band | Verdict | Predicted SD | Required variance factor s (95 % CI) |
|---|---|---|---|---|---|---|
| car < 20 m, longitudinal | 0.004 | 0.062 | [−0.002, 0.010] | OVERCOVERS | 3.34 m | 0.25 [0.18, 0.32] |
| car < 20 m, lateral | **0.135** | 0.084 | [0.040, 0.229] | CONSISTENT | 0.67 m | **5.3 [2.2, 7.4]** |
| car 20–40 m, longitudinal | 0.009 | 0.050 | [−0.002, 0.019] | OVERCOVERS | 3.34 m | 0.30 [0.25, 0.48] |
| car 20–40 m, lateral | **0.175** | 0.093 | [0.078, 0.271] | CONSISTENT | 0.67 m | **2.6 [1.5, 10.7]** |

**What h2s shows.**
- The predicted covariance has the **wrong shape**. Longitudinally it is far too wide: E ≈ 0.005, and the required variance factor is about 0.25–0.30. Laterally it is too narrow: E = 0.135–0.175, and the required factor is 2.6–5.3.
- The lateral point estimates sit above their orientation-null thresholds, and the truth-oriented exceedance is 0.095–0.107 against 0.05. But the lower band edges (0.040 and 0.078) do not clear the thresholds (0.084 and 0.093) with 52–83 scenes.
- The pattern is stable across the sensitivities: the 4 m gate, per-frame re-matching and contested exclusion all give lateral E of 0.13–0.18.
- **NEES is OVERCONFIDENT** for both car groups at 2 s (ANEES 3.2 and 3.5). That is **type II disagreement** in both longitudinal cells: NEES calls for more variance, while the longitudinal tail is already strongly over-covered. A NEES-guided scalar correction would therefore widen an already 3.3 m longitudinal SD, to fix a lateral deficit.
- **K5 is supported (pre-registered rule, at σ_a = 0.10 and at σ_a = 0).**
  - (a) Stratum-CRC held-out exceedance passes.
  - (c) On the test half, the uncalibrated and certified-global thresholds significantly under-cover car 20–40 m lateral: exceedance 0.151, one-sided 95 % lower bound 0.072, and 0.175, lower bound 0.098.
  - (b), reported as a magnitude: stratum CRC uses a total margin of 4,490 m-records, against 11,559 for the global multiplier and 11,674 for global inflation.
- Q4 is UNDERPOWERED for h2s by its pre-registered operating-characteristics check. The point estimate is H_m = 5.5 m [3.5, 8.4], reported as an estimate only.

## Why G1 was not shown

The test was **underpowered for the size of effect present**:
- the simultaneous 97.5 % band, a Bonferroni split over two families, with a simulated false-FAILS rate of 0.2 % against 2.5 % allowed;
- the orientation-null threshold, raised to 0.084–0.093 for the lateral cells at 2 s;
- only 52–83 scenes per lateral cell in the in-path subset.

**The rule did not fail by contradiction.** No lateral cell came out CONSISTENT near 0.05, or OVERCOVERS.

## Pre-registered fallback (§15) and deviation

- **All-objects analysis (done; exploratory).**
  - t0 FAILS in: car ≥ 40 m (E = 0.071 longitudinal, 0.106 lateral); pedestrian longitudinal at all ranges (0.08–0.10); large vehicle ≥ 40 m longitudinal (0.092).
  - h2s FAILS in pedestrian longitudinal, < 20 m and 20–40 m (0.093).
  - These cells lack in-path eligibility.
- **Cross-fitted tracker arm: deferred, recorded as a deviation.** It is superseded by a stronger test of the same concern: a confirmatory replication on the 700 nuScenes **train** scenes.
  - There, CANMOT's Q, tuned by Bayesian optimisation on val, is out-of-sample.
  - The detector is in-sample, which makes detections better than deployment. That makes a lateral failure *harder* to show, so the replication is conservative.

## Next step (decided now, before any train data is analysed)

Pre-register **X2**, a confirmatory replication on the 700 train scenes of the discovered effect: lateral under-coverage and longitudinal over-coverage at 2 s, which a scalar (NEES-guided) correction cannot fix. Then freeze, then run.
