# X2 pre-registration: confirmatory replication on the 700 nuScenes train scenes (v01, 30 Oct 2026)

**Status.**
- Written after X1, which was the discovery study (`60_RESULTS/x1/X1_RESULTS_REPORT_v01.md`), and before any train-scene outcome is computed.
- Frozen with the SHA-256 of the code and inputs in §0, after the train export passes Q0. The hash is recorded outside this folder.
- The text governs.

## 0. Frozen code and inputs

```
FROZEN_HASHES_BEGIN
(filled at freeze)
FROZEN_HASHES_END
```

## 1. Hypotheses: the effect discovered in X1's h2s family

In-path cars, at the tracker's own 2 s prediction, with σ_a = 0.10 m:

- **H1 (lateral under-coverage).** At least one of the pre-specified cells *car < 20 m lateral* and *car 20–40 m lateral* **FAILS**: the lower edge of the simultaneous 95 % sup-t band is above max(0.05, E⁰_g). In that same cell:
  - (a3) it also FAILS at σ_a = 0.20 m;
  - (a4) it also FAILS with contested records excluded;
  - (a5) it also FAILS in the truth-oriented analysis;
  - (a2) the extra lateral margin Δ_g has a bootstrap one-sided 97.5 % lower bound above h₀ = 0.10 m.
- **H2 (a shape error no scalar correction can fix).** For the same range bin as an H1 cell:
  - the *longitudinal* cell OVERCOVERS: the upper band edge is below 0.05;
  - the required variance factors go in opposite directions: the 95 % bootstrap lower bound of s_lat is above 1, and the upper bound of s_long is below 1.
- **G1 (X2) holds** if and only if H1 and H2 both hold for at least one range bin.

**Single primary family, so no Bonferroni split.** The band is the two-sided 95 % sup-t band over **all** eligible h2s cells. That is more conservative than a band over the two pre-specified cells alone.

## 2. Secondary and confirmatory method claims

- **K5 at h2s.** The X1 rule is used: (a) and (c), at σ_a = 0.10 and σ_a = 0. (b) is reported as a magnitude.
- **H3 (NEES misdirection, reported).** NEES-guided scalar correction is defined per class × range as k = ANEES/2 (2-D), applied to Σ̂. After the correction, report:
  - the lateral exceedance;
  - the longitudinal median extra margin, z·(√k − 1)·SD_long.
- **t0 family.** Reported descriptively under the same machinery.
- **Pedestrians, far cars, two-wheelers and large vehicles.** Reported for any cell that becomes eligible (≥ 39 scenes). Descriptive only.
- **Q4.** Gated by its operating-characteristics check, as in X1.

## 3. Data and stack (differences from X1 only)

| Item | Value |
|---|---|
| Scenes | the devkit's 700 train scenes (`nuscenes.utils.splits.train`) |
| Detections | CenterPoint (flip) train file, SHA-256 `547fdb7d…327145`. It matches CANMOT's own `PAPER_INPUT_HASHES['train']`. The detector was trained on these scenes (in-sample), so detections are better than in deployment. **That makes H1 harder to show; the replication is conservative.** |
| Tracker | the same CANMOT commit and experiment `paper/local/canmot/sc`, with `dataset_cfg.split = train`. Q was tuned on val, so it is **out-of-sample here**. R is the trainval sample covariance, so it is in-sample. |
| Export | `x1_export_v04.py --split train --fast-convex` in 12 scene subsets (`x1_split_detections_stream_v03.py`). The streaming splitter reproduces the val file exactly (`STREAM_EQUIV`). The fast mode replaces only the GIoU convex-hull area with a compiled routine (`fast_convex_v01.py`). It was accepted after the full 150-scene val export came out **record-identical** to the native run: 381,553 of 381,553 records (`60_RESULTS/x1_export_val150_fast_v04/EQUIVALENCE_vs_native_v02.json`). |
| Ground truth | `x1_gt_prep_v03.py --split train` |
| Horizon | `x1_horizon_prep_v01.py`, unchanged |
| Analysis machinery | `x1_lib_v02.py`, with the functions of `x1_full_v02.py`, at band level 0.95, plus `x2_full_v01.py` for the H1/H2 decision. All are hashed in §0. |

Everything else follows X1 pre-registration v02, which is frozen:
- pairing, rack filter, in-path, separating axes, orientation;
- σ_a handling, orientation null, truth-oriented analysis, NEES, prices, certification;
- the sensitivities and the integrity gates Q0–Q2.

## 4. Before the freeze (allowed outputs only)

The same as X1 §12: counts, per-scene counts, median exported SD, the orientation null, the FWER simulation of the 95 % band at the train cell sizes (requirement ≤ 0.05 + 2 MC SE, with the logit fallback), and the Q4 operating characteristics.

No U value, residual, NEES or exceedance is computed before the freeze.

## 5. If G1 (X2) does not hold

Report exactly which condition failed, and why. The next steps are already decided:
1. **Pooled analysis** of val + train (850 scenes) for the same H1/H2, labelled exploratory.
2. **A second tracker covariance model** on val + train, as a generality check: CANMOT's own sample-covariance configuration.
3. **Re-examination of the problem framing.** The paper's problem becomes whichever effect replicates.

Nothing is claimed without a confirmatory pass.
