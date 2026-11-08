# P02 v03: propositions for the method stage (31 Oct 2026)

**v03** follows review R07b. It adds the pooled-cell remark (N-m5) and states that PM1 holds per own-threshold stratum under i.i.d. scenes (N-m11). Otherwise it is v02.

**v02** followed review R07. Changes from v01: PM3 is scoped to strata with their own threshold (m1); a new section on the estimand and the population (M7, M9); related work extended (M8). The propositions and proofs are otherwise unchanged.

These are the proof obligations PM1–PM3 of `40_PROTOCOL/M_PREREGISTRATION` §10. Notation follows P01 and the plan. The guarantees below are about **toward-ego exceedance on the object axes** at the planning horizon, for one stratum at a time.

## Setting

- A **scene** Z is a random finite set of items. Each item has I_k-measurable features x and a score U = D / sd, where D is the toward-ego projected error and sd = √(V + σ_a²).
- The stratum map g(x) is fixed in advance (plan §4) and uses features only.
- For stratum g and threshold c, the scene loss is L_g(Z; c) = share of Z's items in g with U > c. It is defined when Z has at least one item in g.
- L_g(Z; ·) is non-increasing and right-continuous in c, with values in [0, 1], and L_g(Z; c) = 0 for c ≥ max U.
- **CRC threshold** on calibration scenes Z_1..Z_n (all with items in g): ĉ_g = inf{c : n/(n+1)·(1/n)Σ L_g(Z_i; c) + 1/(n+1) ≤ δ}.

## PM1: per-stratum validity

**Proposition.** Let Z_1, …, Z_m, Z_test be i.i.d. scenes. Let I = {i : Z_i has an item in g}, N = |I|, and suppose Z_test has an item in g. If N ≥ 19 (so that 1/(N+1) ≤ δ = 0.05), then E[L_g(Z_test; ĉ_g) | N] ≤ δ, where ĉ_g is fitted on {Z_i : i ∈ I}.

**Proof.**
1. **Conditioning.** Write A_i = 1{Z_i has an item in g}. The scenes are independent, so conditional on (A_1, …, A_m, A_test) the scenes are independent. Each Z_i with A_i = 1 has the conditional law Q_g = Law(Z | A = 1). So given N = n and A_test = 1, the n calibration scenes in I and Z_test are i.i.d. from Q_g, hence exchangeable.
2. **CRC.** The losses L_g(·; c) are non-increasing in c and bounded by B = 1. Conformal risk control (Angelopoulos et al., ICLR 2024, Thm 1) gives E[L_g(Z_test; ĉ_g)] ≤ δ for exchangeable losses with these properties, provided the constraint is attainable. At c ≥ max U the empirical term is 0 and 1/(n+1) ≤ δ holds for n ≥ 19, so it is attainable.
3. **Computation.** The empirical risk is a step function that changes only at observed scores, and it is right-continuous. So the infimum is attained at an observed score. `crc_threshold` returns the smallest observed score that satisfies the constraint, by bisection on a non-increasing predicate. That is exactly ĉ_g.
4. **Conditioning on N.** The bound holds for every fixed n ≥ 19. The choice between the stratum's own threshold and a fallback depends on the calibration data only through N, so the bound also holds conditional on the own threshold being used. ∎

**What PM1 does not give.**
- **Fallback thresholds.** For a fallback (N < 19, threshold from a coarser cell C), the analogous bound holds for the coarser cell's loss L_C, which averages over C's sub-strata. It does not hold for stratum g. It also holds only unconditionally, because the event {N_g < 19} depends on the calibration scenes. Fallback strata are therefore reported separately.
- **Dependence between scenes in a log.** If scenes in one log are dependent and logs are i.i.d., apply PM1 with the log as the unit: L_g(log; c) = share of the log's items in g with U > c. This is arm M\*-log. Under log-level dependence, the scene-unit guarantee for a scene from an unseen log is not implied. E1's held-out-log design tests exactly this.
- **Planner directions.** The guarantee concerns the toward-ego exceedance on the object axis that separates. Other directions follow only under condition (M) of addendum v04.

## PM2: the deployable covariance

**Proposition.** For an object with estimated yaw ψ, let a_l = (cos ψ, sin ψ) and a_t = (−sin ψ, cos ψ). Let α_l, α_t > 0, A = α_l a_l a_l′ + α_t a_t a_t′, M = Σ̂ + σ_a² I, and Σ̃ = A M A. Then:
- Σ̃ is symmetric positive-definite;
- a′Σ̃a = α²(a′Σ̂a + σ_a²) for (a, α) ∈ {(a_l, α_l), (a_t, α_t)}.

So with α = ĉ/z, a planner that uses z·√(a′Σ̃a) applies the margin ĉ·sd on each object axis.

**Proof.**
- **Symmetry.** a_l and a_t are orthonormal, so A is symmetric with eigenpairs (α_l, a_l) and (α_t, a_t), and it is invertible.
- **Positive-definite.** M is positive-definite. Σ̃ = A M A = A′MA is a congruence by an invertible matrix, so it is also positive-definite.
- **Projected variance.** a_l′Σ̃a_l = (A a_l)′M(A a_l) = α_l² a_l′M a_l = α_l²(a_l′Σ̂a_l + σ_a²). The same holds for a_t. Then z·√(a′Σ̃a) = z·α·sd = ĉ·sd. ∎

**Remark.** If a fitted ĉ is ≤ 0, set α = max(ĉ, ε)/z. The deployed margin is then at least ĉ·sd, and because L is non-increasing in c, validity is kept. In the evaluation the margin is ĉ·sd as fitted.

## PM3: certified single multiplier and its price

**Proposition.**
- Let c̄ = max_g ĉ_g over the strata that have their own threshold, under PM1's assumptions. Then E[L_g(Z_test; c̄)] ≤ δ for every such stratum g.
- The extra margin over the stratified rule is Σ_items (c̄ − ĉ_g(item))·sd_item ≥ 0. It is zero only when every item's stratum has threshold c̄.
- The same holds for B6c, the maximum over the motion strata within an L1 cell, in every motion stratum that has its own threshold.
- **Scope (v02).** The code takes the maximum over all 96 thresholds, fallbacks included. The resulting multiplier is still at least ĉ_g for every own-threshold stratum, so the bound holds there. It carries no guarantee for fallback strata, where PM1 itself gives none.

**Proof.**
- c̄ ≥ ĉ_g holds pointwise, and L_g(Z; ·) is non-increasing. So L_g(Z_test; c̄) ≤ L_g(Z_test; ĉ_g) pointwise, and taking expectations with PM1 gives the bound.
- The margin identity is immediate from m = c·sd.

This is the stratified instance of the single-knob price in P01 Thm 4. ∎

## The estimand and the population (v02)

**Estimand.**
- PM1 bounds the **marginal** risk E[L_test] over the draw of the calibration scenes and the test scene. It does not bound the risk of one deployed rule given its calibration set. That conditional risk exceeds δ with substantial probability, because CRC is nearly tight.
- The evaluation estimates the marginal quantity:
  - in E1 by averaging over 20 repeated log splits;
  - in E2 by a refit bootstrap that resamples the calibration logs.

  The paper states it as such.
- **Why marginal control is the right target for a CC planner.** The chance constraint P(collision) ≤ δ is itself a probability over the joint randomness of the world and of the planner's inputs. A calibrated rule that is drawn once, then deployed over many scenes, meets it on average.
- **Training-conditional alternatives.** RCPS and Learn-then-Test (Bates et al., JACM 2021; Angelopoulos et al., 2021) give a (δ, α) training-conditional guarantee. At the stratum sizes here (tens to a few hundred scenes) they would need a far larger margin. They are discussed, not run.

**Population.**
- The guarantee and every evaluation refer to the items defined in plan §3: track records at k that are persistently paired with a ground-truth object, and whose object is still annotated and visible at k + h.
- This selection uses ground truth, so the planner cannot reproduce it. The certificate therefore covers tracked real objects that remain observable. It does not cover false-positive tracks or objects that become fully occluded.
- The share of in-path paired items censored at the horizon is reported per stratum, from counts.

## Pooled evaluation cells (v03)

- Some evaluation cells pool several strata: E2's range- and motion-pooled cells, the remainder cells, and the pooled val cell.
- A pooled cell's scene loss is the share of exceeded items over the union. Within each scene it weights the strata by their item counts.
- PM1 bounds each own-threshold stratum's conditional scene loss. It does not bound the union's loss, because the weights vary with the scene, so E[L_union] can exceed δ even when every component meets PM1. Remainders also contain fallback strata, which carry no guarantee.
- So a pooled cell's null value is only approximately δ. A significant flag in a pooled cell is evidence against the method, read with this caveat.

## Relation to known results

- PM1 is Mondrian (group-conditional) conformal validity (Vovk 2012), applied to the CRC loss of Angelopoulos et al. with the scene, or the log, as the exchangeable unit.
- Rare classes are often handled by pooling scarce groups instead of a hierarchy. The closest work is clustered conformal prediction (Ding et al., NeurIPS 2023), which pools classes with similar score distributions. Our fixed hierarchical fallback (L0 to L1, L2, L3) is a simpler, pre-specified version, with the fallback caveat of PM1.
- Conformal prediction with conditional guarantees (Gibbs, Cherian and Candès, 2023) gives guarantees over richer covariate classes. Mondrian strata are its finite-partition special case.
- Conformal motion planning (Lindemann et al., RA-L 2023) calibrates a Euclidean norm ball on the prediction error. That is baseline B9 here. It is axis-blind by construction, which is what Thm 1 of P01 says can fail.
- **Adaptive conformal inference** (Gibbs and Candès, NeurIPS 2021; Dixit et al., L4DC 2023) updates the threshold online. Our setting is offline calibration of a fixed tracker, so ACI is out of scope. Its online updates could be layered on DP-SCRC's strata.
- PM2 and PM3 are elementary.
- The contribution these propositions support is not the inequalities themselves. It is that they are applied in the planner's own constraint coordinates (object axes, toward-ego side, horizon covariance), which is what Thm 1 of P01 requires and what NEES-based or pooled corrections do not deliver (Thm 2, Thm 4).
