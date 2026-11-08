# P01 — Theory layer for the Programme A article (v02, 30 Oct 2026)

This version supersedes v01, which is kept as reviewed. It answers the adversarial review `70_TESTS/R01_ADVERSARIAL_REVIEW_P01_S01_v01.md` (3 critical, 16 major and 16 minor findings, all accepted; disposition in `70_TESTS/R01_FIX_LOG_v01.md`).

**Checks.** Reference checks are in `checks/p01_verify_v03.py` and `p01_verify_v03_results.json`. They are constructive, every quoted number has a pass flag, and ALL_PASS is true. The v01/v02 check scripts are kept as history only; v01's ALL_PASS is false because its Corollary 3 test was wrong.

**Abbreviations.**
- **AARCH:** 10 Oct archive master report.
- **S3:** Stage 3 blueprint.
- **REA:** the researcher's parallel reassessment, `OneDrive …/Reassessment_2026-10-30/03_IDENTIFICATION_AND_NUMERICAL_RESULTS.md`.

## What is new here and what is not (stated first)

| Statement | Status |
|---|---|
| Lemmas 1–2 (Gaussian half-space; Boole) | Textbook. Blackmore et al. 2011 is cited only once its equation numbers are checked; it is unread (W2 §9). |
| Lemma 3, Corollaries 1–2 | Textbook: Cauchy–Schwarz and the Schur complement. The Mahalanobis-ellipsoid route is in Johnstone & Cox 2021 and A-M24. |
| Theorem 1 (two layers, slack-aware) | Formal statement of the planner's premise. This is the first precise form in the programme's record. |
| Proposition 1 (κ/ρ̂ dilution and monotonicity) | **Added.** It generalises the PC3 identity of AARCH §1.5. |
| Theorem 2 (NEES neither necessary nor sufficient) | Related work: Yan & Hsu 2025 (partial); REA's equal-pooled-diagnostics example; A-M24; Serfling et al. 2026 (NEES check alongside risk calibration). Constructions (b2) and (c) and the decision-premise form are added. |
| Theorem 3 and Corollary 3 (representability; closed-loop identity and its converse) | **Restated** from AARCH §1.5, S3 l. 213/285/362 and REA, with conditions made explicit and adapted to the archive's existence-weighted planner. Not new. |
| Theorem 4 (two single knobs and their prices) | **Added**: the inflation-versus-risk-level comparison under predictor dilution. Its mathematics is monotonicity (cf. CRC Prop. 5). |
| Proposition 5 | AARCH §1.5 ("doses as injective transforms") plus a positive-definiteness remark. |
| Lemma 4, Theorem 5, Proposition 6 | An application of conformal risk control (CRC, §3.1). Conditioning arguments as in Vovk 2012 Prop. 3. Hierarchical and environment-unit precedents: Lee–Barber–Willett; Dunn–Wasserman–Ramdas; Mei et al. 2025. The practical-size rule is added. |

**Consequence for the article.** The theory layer is a precise formalisation section. Its own contributions are modest: Proposition 1, Theorem 4, the slack-aware Theorem 1 and the practical certification size. **The article's contribution must come from the measurements and the closed-loop study.**

---

## 0. Setting

- **(S1) Prediction.** At step k the planner holds information I_k:
  - tracker means μ̂_i and position–velocity covariances Σ̂_i ≻ 0;
  - existence probabilities p_i, class, size and yaw;
  - the ego state.

  The constant-velocity (CV) predictor gives m̂_i(t) = F_tμ̂_i and V̂_i(t) = F_tΣ̂_iF_tᵀ + Q(t), with F_t = [I₂, tI₂].
- **(S2) Constraints.** For each evaluated tuple j = (candidate plan, object, horizon t ∈ H), the planner forms a unit normal a_j, an offset b_j and a multiplier c_j, and checks the tightened constraint

  (TC) a_jᵀm̂_j + c_j√v̂_j ≤ b_j, with v̂_j = a_jᵀV̂_ja_j = p̂_j + q_j,

  where p̂_j = a_jᵀF_tΣ̂F_tᵀa_j = σ̂_p² + 2tσ̂_pv + t²σ̂_v² along a_j, and q_j = a_jᵀQ(t)a_j.
- **(S2′) The archive's primary planner (CC-joint, S3 l. 257).** p_i·P(overlap_i(t)) ≤ δ_obj per object and step, which gives c_j = z_{1−δ_obj/p_i}. A union-bound planner with Σδ_j ≤ Δ is the other common case. The archive also has an Expected-cost planner, which adds a covariance-dependent cost term.
- **(S3) Variance ratios.**
  - ρ̂_j = p̂_j/q_j is the exported share (∞ if q_j = 0).
  - Under a stated truth, κ_j = p_j/p̂_j and ρ_j = κ_jρ̂_j.
- **(S4) Error statistics.**
  - U_j = a_jᵀ(X_j − m̂_j)/√v̂_j.
  - N_j = (X_j − m̂_j)ᵀV̂_j⁻¹(X_j − m̂_j).
  - The realised threshold is τ_j = (b_j − a_jᵀm̂_j)/√v̂_j, with τ_j ≥ c_j when (TC) holds.

The guarantee in (TC) is per step, per constraint and open loop. Under receding-horizon re-planning and fallback, even a calibrated premise does not bound the closed-loop collision rate.

## 1. The premise

**Lemma 1.** Let Y ~ N(m, V), V ≻ 0, a ≠ 0. Then P(aᵀY > b) = Φ̄((b − aᵀm)/√(aᵀVa)). Hence P(aᵀY > b) ≤ δ ⇔ aᵀm + z_{1−δ}√(aᵀVa) ≤ b. ∎

**Lemma 2 (Boole).** P(∪E_j) ≤ Σ_j P(E_j). ∎

**Theorem 1 (premise, slack-aware).**
- **(i)** For any executed plan satisfying (TC), P(a_jᵀX_j > b_j | I_k) = P(U_j > τ_j | I_k) almost surely. So the per-constraint guarantee at level δ_j holds iff P(U_j > τ_j | I_k) ≤ δ_j. The premise P(U_j > c_j | I_k) ≤ δ_j is sufficient because τ_j ≥ c_j. It is necessary only on active constraints, where τ_j = c_j. For a sampling planner with a finite candidate set, executed constraints are almost never exactly active. Fallback steps that violate (TC) are outside the theorem.
- **(ii)** Let G be a set of executed constraint instances selected by an I_k-measurable rule, and let P(· | G) be taken under an explicit I_k-measurable instance weighting. Suppose δ_j ≡ δ on G and the conditional premise holds for every instance in G. Then P(U > z_{1−δ} | G) ≤ δ.
  - The stratum inequality is therefore necessary for (i) when G lies in the active set, and necessary for the per-constraint premise on all of G.
  - It is never sufficient.
  - If δ_j varies with I_k, the bound is E[δ_j | G].

*Proof.*
- (i) Since a_j, b_j and v̂_j are I_k-measurable, a_jᵀX_j > b_j ⇔ U_j > τ_j.
- (ii) Apply the tower property.
- Non-sufficiency: U | L=1 ~ |N(0,1)| and U | L=2 ~ −|N(0,1)| with a fair label L. Then U ~ N(0,1) marginally, with P(U > z_{0.99}) = 0.0100, yet P(U > z_{0.99} | L=1) = 0.0200 (check T1ii, constructed). ∎

*Remarks.*
- Layer (i) is conditional on the information. Exact object-conditional coverage cannot be certified distribution-free at non-atoms (a consequence of the impossibility argument in Vovk 2012, Prop. 4, there for prediction sets).
- **Audit strata are outcome-dependent.** They are matched true positives (first association within 2 m) and are censored at t > 0. An open-loop audit therefore estimates (ii) only up to these selection effects.
- In a stratum that fails at c, the guarantee failure is overstated wherever τ_j > c.

**Proposition 1 (dilution).** Assume X_j − m̂_j | I_k ~ N(0, p_j + q_j) along a_j, with Q correct and q_j > 0. Then

P(U_j > c | I_k) = Φ̄(c√r_j), with r_j = (ρ̂_j + 1)/(κ_jρ̂_j + 1).

- If κ_j > 1, r_j decreases from 1 to 1/κ_j as ρ̂_j goes from 0 to ∞.
- If κ_j < 1, r_j increases from 1 to 1/κ_j.
- If q_j = 0, direct computation gives r_j = 1/κ_j.

*Global dose.* Replace Σ̂ by sΣ̂ with s ≠ 1. The margin becomes c′_j√v̂_j with c′_j = c√((sρ̂_j + 1)/(ρ̂_j + 1)). This equals c√s for every j iff q_j = 0 for every evaluated j (the PC3 identity).

*Proof.* Algebra: dr/dρ̂ = (1 − κ)/(κρ̂ + 1)². ∎ (Check P1, which includes κ = 0.5.)

## 2. NEES versus the premise

**Lemma 3.** For e ≠ 0, (aᵀe)²/(aᵀV̂a) ≤ eᵀV̂⁻¹e, with equality iff a ∝ V̂⁻¹e. ∎

**Corollary 1 (plan-uniform).** P(N > c² | I_k) ≤ δ implies P(U > c | I_k) ≤ δ for every I_k-measurable a. Under a Gaussian truth in 2-D the price ratio is 1.30 at δ = 0.01. ∎

**Corollary 2 (Schur).** e₁ᵀV̂₁₁⁻¹e₁ ≤ eᵀV̂⁻¹e. At t = 0, V̂ is the position block of CANMOT's measurement-space HPHᵀ. A population pass of the 9-D 95 % test (radius 4.113, computed in the checks) bounds only P(U > 4.113) ≤ 0.05 along position directions. ∎

**Theorem 2 (NEES ⇏ premise and premise ⇏ NEES, in 2-D).** Values are at δ = 0.01 unless stated.
- **(a)** Truth N(0, I), export diag(2, 2/3). Then E[N] = 2 (checked: 2.00), yet the risk along axis 2 is 0.0288.
- **(b)** Take e = R(cos θ, sin θ) with R² ~ χ²₂ independent of θ, and export I₂. Then N = R² ~ χ²₂ exactly, whatever the law of θ. With θ = θ₀ + πB, θ₀ ~ N(0, s²) and a fair bit B, the risk along a₀ is 0.0268, 0.0181 and 0.0121 for s = 0.3, 0.6 and 1.0. The checks compute N from e: p_v95 = 0.050.
  - A population p_v test is passed (a level-α test still rejects with probability α).
  - The 1-D NEES along a₀ does detect the problem. That is the point: the joint test cannot see a direction-specific failure.
- **(c)** Truth diag(1, 4), export I₂, binding direction e₁. This direction is calibrated, yet E[N] = 5. Global ANEES-matching (×2.5) gives the risk 0.00012 at nominal 0.01.
- **(d)** e = (T₁, T₂)/√3 with independent T_i ~ t₃. Each component has unit variance (the second moment is exact), yet the risk along e₁ is 0.0137 at δ = 0.01 and 0.0064 at δ = 0.001. At δ = 0.05 it is 0.0326, conservative.

∎ (Checks T2a, T2b2, T2d.)

## 3. Representability by the planner's own risk parameter (restated from AARCH §1.5, S3 and REA)

A **retuning family** is the planner's own parameterisation θ ↦ {c_j(θ)}. The cases that matter are:
- 𝒦_c: one multiplier, c_j(θ) = θ (the PC3 configuration: covariance-only planner, fixed allocation);
- 𝒦_δ for CC-joint: c_j(θ) = z_{1−θ/p_{i(j)}};
- 𝒦_Δ for union-bound allocation: c_j(θ) = z_{1−θ/K_k};
- group versions of each, for H4b;
- an unrestricted per-tuple family, labelled an oracle or mechanism control.

**Hypotheses for Theorem 3.**
- **(G) Geometry.** The tuples evaluated and their geometry (a_j, b_j, linearisation point, candidate set) are functions of means, identities, existence, class, size, yaw and ego state only, not of the covariance.
- **Intervention.** An intervention Σ̂ ↦ Σ̂′ writes only a copy of the covariance (Proposition 5).

**Definition.** The intervention (applied with baseline parameter θ₀) is **𝒦-representable** if some θ satisfies

c_j(θ)·√v̂_j = c_j(θ₀)·√v̂′_j

for every evaluated tuple j, at every information state reachable under the intervened arm.

**Theorem 3.**
- **(i)** Under 𝒦_c, representable ⇔ the ratio R_j = √(v̂′_j/v̂_j) is constant over all evaluated tuples. The group family requires this within each group. The unrestricted family represents every intervention with v̂′_j > 0.
- **(ii)** Under 𝒦_c, a global dose s ≠ 1 is representable iff ρ̂_j is constant over the evaluated tuples. This holds in particular when q_j = 0 for all j.
- **(iii)** Under 𝒦_δ (CC-joint), with heterogeneous p_i, a global dose is generically **not** representable even when Q ≡ 0. Example: s = 4, δ_obj = 0.01, p ∈ {0.5, 0.8, 1.0}; the best single θ misses one required margin by 4.5 % (check T3_ccjoint). S3 l. 213 already states this.
- **(iv)** With position–velocity cross-covariance, ρ̂_j(t) is constant on the horizon set H iff q_j(t) ∝ σ̂_p² + 2tσ̂_pv + t²σ̂_v² on H. Example, with correlated export blocks: ρ̂ ranges over 0.57–6.2 when q ∝ t², and over 0.24–51.7 when q ∝ t³ (check T3iii).

*Proof.* Representability means equality of the margins for every evaluated tuple. Under 𝒦_c this gives θ = θ₀R_j for all j. Then (ii) follows because the map ρ̂ ↦ (sρ̂ + 1)/(ρ̂ + 1) is injective when s ≠ 1. Part (iii) is by computation. Part (iv) is algebra on the finite set H. ∎

**Corollary 3 (closed-loop identity; restated from REA with explicit conditions).**

*Conditions.*
- **(C1)** The full stack — simulator, agents, emulator, tracker and planner — is a deterministic function of the seed and the history, with every random draw keyed to the state.
- **(C2)** The planner is **margin-sufficient**. Its command is a deterministic function of:
  - the ego state;
  - means, identities, existence, class, size and yaw;
  - the margins of **all evaluated** tuples.

  It has no other covariance dependence: none in its cost, normals, fallback trigger or tie-breaking.
- **(C3)** Margins are bit-identical between the arms (use doses s = 2^{2k} and the archive's 10⁻⁹ tolerance check).
- **(G)** holds.

*Statement.* If the intervention is 𝒦-representable with θ, then the closed-loop trajectories under (Σ̂′, θ₀) and (Σ̂, θ) are identical. Therefore every **world-state** outcome (S, N, progress) is equal. Covariance-derived endpoints, such as decision-level risk calibration or margin-based behaviour descriptors, need not be equal.

*Proof.* By induction on the full stack state. ∎

*Limits.*
- The effect vanishes only after retuning to the representing θ. A T-matched grid that does not contain θ leaves a grid-induced residual (check C3_suite: a grid without the representing value gives a mismatch of 0.5).
- The converse fails: a non-representable intervention may change nothing, for example when its constraints never bind.
- Residuals do **not** require binding-horizon switching. A time-varying export with a single horizon leaves a mismatch of 10.3 after the best global retune (C3_suite).
- **Which archive planners satisfy (C2):** the covariance-only (PC3) configuration does. The Expected-cost planner does not; a covariance-dependent cost breaks the identity, with summed |Δa| = 90.55 in the toy. CC-joint does only if its linearisation is covariance-free. Under CC-joint, (iii) says even Q ≡ 0 doses are not δ-representable.

*Role in A-N3.*
- The archived H3 positive control ("in the PC3 configuration, Δ_F = 0 up to δ-grid interpolation error", S3 l. 362) and PC3 (S3 l. 285) are the instances where Corollary 3 applies. Corollary 3 states their conditions precisely: grid closure under δ ↦ Φ̄(√s·z_{1−δ}), powers-of-two doses, and bitwise determinism.
- For non-representable doses, including H4a's transplant under CC-joint, the theory **predicts nothing** about outcomes. H4a remains an empirical test.
- The quantity worth measuring is the **dispersion of R_j over the tuples that bind along each episode** (over time, objects and horizons). It needs a planner, so it belongs with H9 on logged trajectories.

## 4. Two single knobs (added)

**Theorem 4.** Assume Proposition 1's truth, with tuple-specific (κ_j, ρ̂_j) and target level δ.
- **(a) Multiplier knob.** It meets the premise for all j iff c ≥ m* = max_j z_{1−δ}√((κ_jρ̂_j + 1)/(ρ̂_j + 1)). The excess margin in metres is (c − m_j)√v̂_j.
- **(b) Inflation knob.** It meets the premise iff s ≥ max_j κ_j. The excess in metres is z_{1−δ}[√(s·p̂_j + q_j) − √(κ_j·p̂_j + q_j)].
- **(c) The knobs are not equivalent when q ≢ 0.** Excess below is in units of the exported SD √v̂_j.
  - (κ, ρ̂) ∈ {(2, 0.2), (2, 5)}: inflation is exact for both, while the multiplier knob costs 0.637.
  - (κ, ρ̂) ∈ {(2, 1), (3, 1/3)}: the multiplier knob is exact for both (2.849 each), while inflation costs 0.441.
- **(d) Aggregate tuning.** With positive weights, setting c so that the weighted risk equals δ gives max_j risk ≥ δ, with equality iff all m_j are equal.

∎ (Monotonicity; check T4c.)

## 5. Dose integrity

**Proposition 5.** Let the intervention write a copy Σ̂′ = sΣ̂ (s > 0) or Σ̂′ = DΣ̂Dᵀ (D nonsingular).
- Then Σ̂′ ≻ 0.
- At a fixed world-state history (open loop), means, identities, scores and the emitted set are unchanged, and so is any metric of them.
- Replacing a sub-block without its cross-terms can break positive definiteness (example determinant −0.31).

Structured doses may *read* class, range or occlusion; they write only the covariance copy. ∎

## 6. Certification from driving logs (application of CRC)

**Lemma 4.** Let scenes Z_1, …, Z_{n+1} be exchangeable. Conditionally on the membership pattern 𝒥 of a single-scene property ("contains stratum g"), with the test scene in 𝒥, the members are exchangeable. This is the conditioning argument behind Vovk 2012, Prop. 3. ∎

**Theorem 5.**
- Let L_j^g(c) = (1/N_j^g)·Σ_{i∈g in scene j} 1{U_i > c}, and let R̂_g(c) be its mean over the n_g calibration scenes.
- Set ĉ_g = inf{c : n_g/(n_g+1)·R̂_g(c) + 1/(n_g+1) ≤ δ}, or +∞ if no such c exists.
- Then E[L_test^g(ĉ_g)] ≤ δ, and this equals P(U_{test,J} > ĉ_g) for an instance J drawn uniformly from the test scene's stratum-g instances. The guarantee is scene-weighted.

*Scope.* With a random split of the 150 val scenes, the guarantee is **transductive**. It holds for a test scene drawn from the val scenes not used for calibration. A superpopulation ("new scene") reading needs every ingredient of the score to be fitted outside val: the tracker's Q and R, Q_c, cut-points and filters. That fails for CANMOT-SC. For the cross-fitted arm it means certifying within one fold, which leaves about 37 calibration scenes.

*What it certifies.* It certifies the audited, axis-projected exceedance on matched instances at logged states. A closed-loop recalibration arm inherits **no** certificate unless calibration is redone on its own induced states and directions.

∎ (Check T5 with random membership: E[L] = 0.030 ± 0.001 at δ = 0.05, n_g from 33 to 60.)

**Proposition 6.**
- (i) A finite ĉ_g needs n_g ≥ 1/δ − 1: 19 at δ = 0.05, 99 at δ = 0.01.
- (ii) At n = 2/δ − 1 the allowance is δ/(2 − δ): 39 at δ = 0.05, 199 at δ = 0.01. This is the practical size.
- (iii) At the floor the certificate is valid but maximally conservative.
- (iv) For deterministic finite thresholds with scenes as the units, levels below 1/(n + 1) cannot be certified by this construction. This is not an impossibility result for every calibration method.

∎

## 7. Map to A-N3

| Statement | Use in A-N3 |
|---|---|
| Thm 1, Prop 1 | Define the reference and doses on projected tails at the planner's levels. Report slack τ_j − c_j. |
| Thm 2, Cor 2 | Justify not using ANEES as the reference criterion. |
| Thm 3, Cor 3 | Engineering specification of the archived H3 positive control and PC3: PC3 configuration, powers-of-two doses, δ-grid closed under the representing map, bitwise determinism. Report the binding-R_j dispersion from H9 runs. No outcome prediction for H4a. |
| Thm 4 | Which single knob the real (κ, ρ̂) structure defeats, and at what margin cost: an open-loop descriptor. |
| Thm 5, Prop 6 | Only for an open-loop audit of the axis-projected exceedance, transductively, at δ = 0.05. |
