# P01 addendum v04: closes the third proof review R04 (30 Oct 2026)

**How to read the theory now.** The current theory text is P01 v02 + addendum v03 + this addendum.

**What R04 found** (`70_TESTS/R04_THIRD_PROOF_REVIEW_v01.md`):
- 0 critical issues; every P01 proof holds; every quoted number recomputes.
- Three major items, all about how X1 applies the theory, not about the proofs: M1, M2 and M3, fixed in X1 pre-registration v02 §2, §11, §15 and §17.
- Eleven minor items. Items m1–m8 are fixed below; m9–m11 are fixed in X1 v02.

## A. New results carried into P01 (R04 §4–§6, proofs there)

**Proposition A (transfer to the separating-axis, toward-ego projection).** Assume condition (M): the axis, the variance, the selection and the weights are all measurable at I_{k(i)}.
- **(A1)** K1 transfers. With b := a*ᵀc_e − h_obj − h_ego, footprint overlap implies a*ᵀX ≥ b, provided the true yaw and extents equal the estimates.
- **(A2)** Under the projected premise, the record-weighted pooled exceedance over any selection satisfying (M) is ≤ δ. Under a Gaussian posterior with known σ_a it equals Φ̄(z) **exactly**. Monte Carlo check: 0.0503.
- **(A3)** K2 transfers, axis by axis.
- **(A4)** K3 transfers in a distribution-free, cell-level form: a global multiplier pays (c − m_g)·SD_g in every cell. Thm 4(c), that the two knobs differ, transfers only under the mapping q ↦ σ_a².

**What is not preserved** (N1–N6): fixed-truth calibration; selection that depends on outcomes (matched true positives, censoring); weights that are not measurable at I_{k(i)}, such as scene weights; a misspecified σ_a; necessity only at cell level; and proxy normals in place of the planner's.

**Proposition B (exchangeability with tuning on val).**
- Assume condition (P): the tracker runs per scene with no state carried across scenes, and nothing is fitted on one half of the split.
- **(B1)** Then the transductive certificate holds conditional on the data, using only that the split is independent of the data.
- **(B2)** If, in addition, the tuning T is a symmetric function of the scene set, Lemma 4 applies to the per-scene losses.
- **(B3)** There is no new-scene guarantee.

**Proposition C (the orientation null).**
- The weak form holds: under I_k-conditional calibration the threshold 0.05 is exact, so max(0.05, E⁰) is conservative.
- The strong form, that E⁰ bounds the fixed-truth artefact, is **refuted**: a truth 1 SD inside the boundary gives 0.315 against E⁰ = 0.175.
- X1 therefore adds condition (a5), truth-oriented FAILS.

## B. Minor items fixed

- **m1 (Thm 1(ii)).** The pooled probability is defined as the ratio of expectations E[Σ wᵢ 1_G(i) 1{Uᵢ > z}] / E[Σ wᵢ 1_G(i)], with each wᵢ 1_G(i) measurable at I_{k(i)}.
  - Scene weights 1/N_j^g do not satisfy this. The scene-weighted exceedance is descriptive only; R04's toy shows it at 0.0591 under exact calibration.
  - With varying δ_j, the statement is P(U > c_J | G) ≤ E_w[δ_J | G].
- **m2 (Cor 3).** (C2) now requires verified identical feasibility outcomes on **every evaluated tuple**, not only margins equal within tolerance. (G) is restated to allow early-termination planners, provided the sequence of evaluated tuples is identical in both arms; that condition is implied by identical outcomes up to that point.
- **m3 (Thm 3(iii)).** "Generically not representable" is strengthened to "**never** representable when two existence values differ, for s ≠ 1 and δ_obj < p_i/2". Proof: θ_i = δ_obj·Φ̄(√s·x_i)/Φ̄(x_i) is strictly monotone in p_i, because d/dx log[Φ̄(√s x)/Φ̄(x)] = λ(x) − √s·λ(√s x), with λ the increasing inverse Mills ratio (R04 verified this numerically).
- **m4 (Thm 4(d)).** "Weighted average risk" (Σ w_j = 1).
- **m5 (Thm 5).** The bound is conditional on the test scene containing g. If n_g < 19, then ĉ = +∞ and L = 0. The extension to the average over many test scenes is (B1).
- **m6–m8.** These are P5 wording items, applied in P5 v03.
