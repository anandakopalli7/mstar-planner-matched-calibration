# P01 — Theory layer for the Programme A article: statements and proofs (v01, 30 Oct 2026)

**Status.** Written proofs. This is step 1, as the researcher asked. Every quantitative statement is checked numerically in `10_PROOFS/checks/p01_verify_v01.py`, with results in `p01_verify_v01_results.json`. No real data are used here.

**Lineage.** The statements consolidate and correct T1–T5 of the 30 Oct resumption review (`00_CONTEXT/resume_review_20261030/40_chains/02_C1_THEOREMS_AND_MAPPING_v02.md`, `50_verification/04_CORRIGENDA_v03.md`). Theorem 3 and Corollary 3 are added here. They tie the theory to A-N3's hypotheses H1, H3, H4a and H4b.

**Overlap.** The researcher's parallel reassessment derives the scalar-compensation identity behind Theorem 3(i) and an equal-NEES directional example like Theorem 2(b). It also states the 19/99 conformal support floor of Proposition 6 (OneDrive `Reassessment_2026-10-30/03_IDENTIFICATION_AND_NUMERICAL_RESULTS.md`). The article must cite those derivations as the programme's own earlier record. They are not independent discoveries.

---

## 0. Setting and assumptions

- **(S1) Planner.** At each decision step k the planner holds information I_k: the tracker's exported mean μ̂_i and covariance Σ̂_i (position–velocity block, ≻ 0) for each tracked object i, plus the ego state. A constant-velocity (CV) predictor gives, at horizon t,
  - m̂_i(t) = F_t μ̂_i, with F_t = [I₂, tI₂];
  - V̂_i(t) = F_t Σ̂_i F_tᵀ + Q(t), with Q(t) ⪰ 0.
- **(S2) Constraints.** For each obstacle–horizon pair j = (i, t), the planner chooses I_k-measurable data: a unit normal a_j, an offset b_j (the separating half-space between the object centre and the inflated ego footprint), and a multiplier c_j > 0. It enforces the tightened constraint

  (TC) a_jᵀ m̂_j + c_j √(v̂_j) ≤ b_j, where v̂_j := a_jᵀ V̂_j a_j.

  Under the Gaussian premise, c_j = z_{1−δ_j} with Σ_j δ_j ≤ Δ. The margin of constraint j is M_j := c_j √(v̂_j).
- **(S3) Notation along a_j.**
  - p̂_j := a_jᵀ F_t Σ̂_i F_tᵀ a_j (exported perception variance) and q_j := a_jᵀ Q(t) a_j (predictor variance), so v̂_j = p̂_j + q_j.
  - Exported share: ρ̂_j := p̂_j / q_j, with ρ̂_j := ∞ when q_j = 0.
  - Under a stated truth, p_j is the true perception variance along a_j, κ_j := p_j / p̂_j, and ρ_j := p_j / q_j = κ_j ρ̂_j.
- **(S4) Statistics.** X_j is the true object position at the horizon.
  - Decision-projected standardised error: U_j := a_jᵀ(X_j − m̂_j)/√(v̂_j).
  - Mahalanobis (NEES) statistic: N_j := (X_j − m̂_j)ᵀ V̂_j⁻¹ (X_j − m̂_j).
- Φ̄ is the standard normal upper tail and z_{1−δ} := Φ̄⁻¹(δ).

---

## 1. The chance-constraint premise

**Lemma 1 (Gaussian half-space reformulation).** Let Y ~ N(m, V) with V ≻ 0, a ≠ 0, b ∈ ℝ, δ ∈ (0, 1). Then P(aᵀY > b) = Φ̄((b − aᵀm)/√(aᵀVa)). Hence P(aᵀY > b) ≤ δ ⇔ aᵀm + z_{1−δ}√(aᵀVa) ≤ b.

*Proof.* aᵀY ~ N(aᵀm, aᵀVa), and Φ̄ is continuous and strictly decreasing. ∎

**Lemma 2 (Boole allocation).** For events E_1, …, E_K, P(∪E_j) ≤ Σ_j P(E_j). In particular, P(E_j) ≤ δ_j with Σ_j δ_j ≤ Δ implies P(∪E_j) ≤ Δ. ∎

**Theorem 1 (the per-constraint premise, two layers).** Assume (S1)–(S4).

- **(i) Exact layer.** For any plan satisfying (TC), {a_jᵀX_j > b_j} ⊆ {U_j > c_j}. The two events coincide when (TC) is active (holds with equality). Hence P(a_jᵀX_j > b_j | I_k) ≤ P(U_j > c_j | I_k) almost surely, with equality on active constraints. So the per-constraint guarantee "P(a_jᵀX_j > b_j | I_k) ≤ δ_j for every active constraint" holds **iff** P(U_j > z_{1−δ_j} | I_k) ≤ δ_j on active constraints, at each allocated level δ_j.
- **(ii) Auditable layer.** Let G be an I_k-measurable stratum with P(G) > 0 on which δ_j ≡ δ is constant. Suppose (i)'s condition holds almost surely on G for every constraint. Then P(U_j > z_{1−δ} | G) ≤ δ. If δ_j varies with I_k, averaging gives instead P(U_j > z_{1−δ_j} | G) ≤ E[δ_j | G]. The stratum inequality is necessary for (i), and it is not sufficient.

*Proof.*
- (i) Since a_j, b_j, c_j, m̂_j and v̂_j are I_k-measurable and v̂_j > 0:

  a_jᵀX_j > b_j ⇔ U_j > (b_j − a_jᵀm̂_j)/√(v̂_j).

  The right-hand threshold is ≥ c_j under (TC), with equality when (TC) is active. Take conditional probabilities.
- (ii) Take expectations of the conditional inequality over G (tower property). For non-sufficiency, let I carry a fair binary label L, with U | L=1 ~ |N(0,1)| and U | L=2 ~ −|N(0,1)|. Taking G to be the whole space, P(U > z_{0.99}) = 0.01, yet P(U > z_{0.99} | L=1) = 2·0.01 = 0.020. ∎

*Remarks.*
- Layer (i) is object-conditional. By Vovk's impossibility result (2012, Prop. 4) it cannot be certified distribution-free at non-atoms of the information. The audit therefore tests layer (ii).
- Layer (ii) is implied by group-conditional calibration of a_jᵀX_j within G. It is **not** implied by average calibration (the counterexample above), and it is not ordered against threshold calibration (Sahoo et al. 2021), whose conditioning events are forecast-defined.

**Proposition 1 (dilution; generalises the PC3 identity).** Suppose that, given I_k, X_j − m̂_j ~ N(0, V_j) with V_j = F_tΣ_iF_tᵀ + Q(t). That is, only the perception covariance is misstated, and q_j > 0. Then
- P(U_j > c | I_k) = Φ̄(c√(r_j)), where r_j = v̂_j/(p_j + q_j) = (ρ̂_j + 1)/(κ_jρ̂_j + 1).
- r_j = 1 iff κ_j = 1. For κ_j > 1, r_j is strictly decreasing in ρ̂_j, from 1 (as ρ̂_j → 0) to 1/κ_j (as ρ̂_j → ∞).
- If Q ≡ 0, then r_j = 1/κ_j.
- **Global dose.** Replacing Σ̂ by sΣ̂ (s > 0) changes the margin to c√(s p̂_j + q_j) = c′_j √(v̂_j), with c′_j = c·√((sρ̂_j + 1)/(ρ̂_j + 1)). This equals c√s for every j iff Q ≡ 0 (PC3).

*Proof.* a_jᵀ(X_j − m̂_j) ~ N(0, p_j + q_j), so U_j ~ N(0, (p_j + q_j)/v̂_j), which gives the first item. The remaining items are algebra: dr/dρ̂ = (1 − κ)/(κρ̂ + 1)², and the limits follow directly. ∎

---

## 2. What NEES tests, and what it does not

**Lemma 3 (Cauchy–Schwarz).** For V̂ ≻ 0, e ∈ ℝ^d and a ≠ 0, (aᵀe)²/(aᵀV̂a) ≤ eᵀV̂⁻¹e, with equality iff a ∝ V̂⁻¹e.

*Proof.* aᵀe = (V̂^{1/2}a)ᵀ(V̂^{−1/2}e). Apply Cauchy–Schwarz, with equality iff V̂^{1/2}a ∝ V̂^{−1/2}e. ∎

**Corollary 1 (plan-uniform sufficient condition).** If P(N_j > c² | I_k) ≤ δ, then for every I_k-measurable direction a_j, P(U_j > c | I_k) ≤ δ. Under a Gaussian truth, the price of plan-uniformity in two dimensions is the multiplier ratio √χ²_{2,1−δ}/z_{1−δ}; at δ = 0.01 this is 3.035/2.326 = 1.30. The calibrated Mahalanobis ellipsoid behind this corollary is known (Johnstone & Cox 2021; A-M24), so Corollary 1 is a lemma, not a contribution.

**Corollary 2 (sub-vector).** Partition e = (e₁, e₂) and V̂ ≻ 0 conformally. Then e₁ᵀ V̂₁₁⁻¹ e₁ ≤ eᵀ V̂⁻¹ e.

*Proof.* By Lemma 3, the left side is the maximum of (aᵀe)²/(aᵀV̂a) over a = (a₁, 0); the right side is the maximum over all a. ∎

*Consequence.* A pass of a 9-D measurement-space NEES tail test at 95 % (radius √χ²_{9,0.95} = 4.113) implies only P(U > 4.113) ≤ 0.05 along any position direction, which is uninformative at the planner's multiplier (2.33 at δ = 0.01). A 9-D failure can be driven by size or yaw errors, which the centre-position constraint treats as known.

**Theorem 2 (NEES consistency is neither necessary nor sufficient for the premise).** Each construction below is in d = 2, with a fixed direction a₀ and the exported covariance normalised so that the claimed NEES property holds exactly.

- **(a) Mean-consistent, direction-miscalibrated.** Truth N(0, I), export Σ̂ = diag(2, 2/3). Then E[N] = tr(Σ̂⁻¹) = 2 = d. Along axis 2, P(U > z_{1−δ}) = Φ̄(z_{1−δ}√(2/3)): 0.0896, 0.0288 and 0.0058 at δ = 0.05, 0.01 and 0.001.
- **(b) Exact χ² law of NEES, direction-miscalibrated.** Let e = R(cos θ, sin θ) with R² ~ χ²₂ independent of θ, and export I₂.
  - Then N = R² ~ χ²₂ exactly, whatever the law of θ. ANEES and every p_v test at every level therefore pass.
  - Along a₀ = (1, 0), P(U > c) = E[exp(−c²/(2cos²θ)) · 1{cos θ > 0}].
  - (b1) Rank-1 case, θ ∈ {0, π} equiprobable: P(U > c) = ½e^{−c²/2}, which is 0.0334 at δ = 0.01.
  - (b2) Non-degenerate case, θ = θ₀ + πB with θ₀ ~ N(0, s²) and B ~ Bernoulli(½): 0.0269, 0.0181 and 0.0121 at δ = 0.01 for s = 0.3, 0.6 and 1.0 (quadrature and Monte Carlo agree, see the checks).
- **(c) Not necessary.** Truth diag(1, 4), export I₂, binding direction e₁. The binding direction is exactly calibrated, yet E[N] = 5 ≠ 2. The ANEES-matching repair (inflate the export by 2.5) multiplies the binding margin by √2.5 = 1.58 and drives the realised risk to 0.00012 at nominal 0.01.
- **(d) Exact second moment, wrong tail.** If U = T/√3 with T ~ t₃, then Var U = 1, yet P(U > z_{1−δ}) is 0.0326, 0.0137 and 0.0064 at δ = 0.05, 0.01 and 0.001. The sign of the error flips with δ.

*Proof.* (a) and (c) are Gaussian projections evaluated with Lemma 1. For (b), N = R² by construction, and the formula conditions on θ and uses P(R > r) = e^{−r²/2} for R² ~ χ²₂. For (d), use the closed-form t₃ CDF. ∎

*Prior art.* Yan & Hsu (2025) show that NEES and NCI can mislead as credibility diagnostics; A-M24 shows that NLL is insufficient for predictors. Theorem 2 is the decision-premise form for tracker exports. The parallel reassessment has an equal-NEES-distribution example of type (b).

---

## 3. Which interventions a planner's risk setting can absorb

A **risk-setting family** 𝒦 maps a parameter θ to multipliers c_j(θ) that may depend only on information the planner is allowed to use. Three families matter:
- **𝒦₁, global.** c_j(θ) = θ for all j: one risk level, with uniform allocation.
- **𝒦₂, observable groups.** c_j(θ) = θ_{g(j)}, where g(j) is an I_k-measurable group from a pre-declared finite set.
- **𝒦₃, per constraint.** c_j(θ) = θ_j: unrestricted. This is an oracle when θ_j uses the injected dose, and is labelled a mechanism control.

An **intervention** replaces the export Σ̂ by Σ̂′ and leaves means, identities and scores unchanged (Proposition 5). It turns v̂_j into v̂′_j = p̂′_j + q_j.

**Theorem 3 (representability).** Fix the planner's baseline multiplier c. An intervention is **representable** by 𝒦 if there is a parameter θ such that

 θ-multipliers on the original export reproduce every margin of the intervened export:
 c_j(θ)√(v̂_j) = c√(v̂′_j) for every constraint j at every decision step that can occur.

Under this definition:
- **(i) Global family 𝒦₁.** The intervention is representable iff the ratio R_j := √(v̂′_j/v̂_j) takes one value over all such j. The representing parameter is then θ = cR.
- **(ii) Global dose.** For p̂′_j = s p̂_j, R_j² = (sρ̂_j + 1)/(ρ̂_j + 1). If s ≠ 1, this is constant across j iff ρ̂_j is constant across j; the case Q ≡ 0 (all ρ̂_j = ∞) is the special case R_j = √s.
- **(iii) Horizon dependence under CV prediction.** Suppose the CV predictor has independent position and velocity export blocks, p̂_j(t) = σ̂_{p,a}² + t² σ̂_{v,a}², and Q(t) is not proportional to p̂_j(t) as a function of t. Then ρ̂_j varies with the horizon. A global dose is therefore **not** a global risk-level change, even for a single object.
- **(iv) Observable groups 𝒦₂.** The intervention is representable iff R_j is constant within every group.
- **(v) Per constraint 𝒦₃.** Every intervention that preserves v̂′_j > 0 is representable.

*Proof.*
- (i) Representability means θ√(v̂_j) = c√(v̂′_j), that is θ = cR_j for all j, which holds iff R_j is constant.
- (ii) d/dρ̂ [(sρ̂ + 1)/(ρ̂ + 1)] = (s − 1)/(ρ̂ + 1)² ≠ 0 when s ≠ 1, so the map is injective in ρ̂. When Q ≡ 0, R_j = √(s p̂_j/p̂_j) = √s.
- (iii) Under the stated form, ρ̂_j(t) = (σ̂_p² + t²σ̂_v²)/q(t) is constant in t only if q(t) ∝ σ̂_p² + t²σ̂_v², which is excluded. Then apply (ii).
- (iv) and (v) follow as in (i), group by group and constraint by constraint. ∎

**Corollary 3 (closed-loop consequence; the formal content of H3 and H4a).** Assume:
- (C1) the simulator is deterministic given its seed (common random numbers across arms);
- (C2) the planner's command at each step is a deterministic function of the ego state, the exported means and identities, and the margins {M_j}. Call such a planner **margin-sufficient**; the archive's Gaussian CC planners are of this kind;
- (C3) the intervention leaves means and identities unchanged at any given world state (Proposition 5).

Then:
- If the intervention is representable by 𝒦 with parameter θ, the closed-loop trajectory under (intervened export, multiplier c) is identical, step by step, to the trajectory under (original export, multipliers c_j(θ)). Every outcome (S, N, progress) is therefore equal.
- Consequently, after retuning within 𝒦 to the representing θ, the residual effect of a representable intervention is exactly zero. A nonzero residual after optimal retuning within 𝒦 can arise only from a **non-representable** intervention.
- The converse fails: a non-representable intervention may change no outcome, for example when its constraints are never active.

*Proof.* Induction on k. At k = 0 the world states are equal. If they are equal at step k, then (C3) gives equal means and identities, and representability gives equal margins. By (C2) the commands are equal, and by (C1) the next world states are equal. ∎

*Implications for A-N3.*
- **H1.** By (ii)–(iii), a global covariance dose with Q ≢ 0 is a heterogeneous risk reallocation, not a pure operating-point change. This sharpens the archive's own caveat that the dose equals a risk-level change "exactly only with Q(t) ≡ 0".
- **H3/H4b.** Retuning within 𝒦₁ (H3) or within 𝒦₂ (H4b) removes the effect of exactly the interventions representable in that family. H4a's "structured cost not compensable by one risk parameter" is the statement that the transplant is non-representable by 𝒦₁ *and* that this matters for outcomes.
- **Measurement.** The theorem says what to measure before any closed-loop run: the dispersion of R_j across active constraints for each planned dose.
- **Grid caveat.** The representing θ must be reachable by the retuning grid. A T-matched progress grid that misses θ leaves a grid-induced residual. This must be reported as such, not as an effect of the intervention.

**Theorem 4 (compensating a miscalibration: the two single knobs).** Assume Proposition 1's Gaussian truth, with constraint-specific (κ_j, ρ̂_j), and let the target be the premise at level δ for every constraint.

- **(a) Multiplier knob** (one c for all j). The premise holds for all j iff c ≥ m* := max_j m_j, where m_j = z_{1−δ}√((κ_jρ̂_j + 1)/(ρ̂_j + 1)). The excess margin at constraint j is (c − m_j)√(v̂_j) ≥ (m* − m_j)√(v̂_j).
- **(b) Inflation knob** (export sΣ̂, multiplier z_{1−δ}). The premise holds for all j iff s ≥ max_j κ_j. The excess margin is z_{1−δ}[√(s p̂_j + q_j) − √(κ_j p̂_j + q_j)].
- **(c) The knobs are not equivalent when Q ≢ 0.**
  - Equal κ = 2 with ρ̂ ∈ {0.2, 5}: inflation s = 2 is exact for both constraints (zero excess). The multiplier knob needs 2.513 and 3.150, so it leaves 0.637 SD of excess on the first.
  - Conversely, (κ, ρ̂) ∈ {(2, 1), (3, 1/3)} need the same multiplier 2.849 (zero excess for the multiplier knob). Inflation must use s = 3, which leaves 0.441 SD of excess on the first.
- **(d) Aggregate tuning.** With positive weights, if c is set so that the weighted average risk equals δ, then max_j risk ≥ δ, with equality iff all m_j are equal.

*Proof.*
- (a) By Proposition 1, the risk is Φ̄(c√(v̂_j/(p_j + q_j))) ≤ δ ⇔ c ≥ z_{1−δ}√((p_j + q_j)/v̂_j) = m_j.
- (b) The risk at inflation s is Φ̄(z√((s p̂_j + q_j)/(κ_j p̂_j + q_j))) ≤ δ ⇔ s ≥ κ_j.
- (c) Direct computation (checks).
- (d) The weighted average of strictly decreasing functions equals δ at c_agg. If every risk at c_agg were ≤ δ with at least one strict, the average would be < δ. So some risk is ≥ δ, and all equal δ iff every m_j = c_agg. ∎

*Prior art.* The mathematics is monotonicity (cf. Prop. 5 of conformal risk control: the worst member sets a single λ). Context-specific temperatures beating a universal scaler for planning (A-M25/CCTR) and Mondrian versus global CP in closed loop (A-M30) are precedents. What is added here is the knob distinction under predictor dilution, and its later measurement on a real export.

---

## 4. Integrity of interventions

**Proposition 5 (dose integrity).** Let the intervention act on a copy of the export by Σ̂ ↦ sΣ̂ (s > 0) or Σ̂ ↦ DΣ̂Dᵀ with D nonsingular. Then:
- (i) Σ̂′ ≻ 0.
- (ii) Means, identities, scores, births, deaths and the emitted set are unchanged. Every metric that depends only on these (AMOTA, AP, identity switches) is unchanged.
- (iii) Replacing a sub-block of Σ̂ without its cross-covariances need not preserve (i).

*Proof.*
- (i) xᵀDΣ̂Dᵀx = (Dᵀx)ᵀΣ̂(Dᵀx) > 0 for x ≠ 0, because Dᵀx ≠ 0.
- (ii) The intervention reads only Σ̂.
- (iii) Counterexample: Σ̂ = [[1, 0.9], [0.9, 1]]; replacing the (1,1) entry by 0.5 gives determinant 0.5 − 0.81 < 0. ∎

---

## 5. What can be certified from driving logs

Calibration data come in **scenes**. A scene is a 20 s nuScenes sequence; scenes are grouped in logs, and objects within a scene are dependent. Take the exchangeable unit to be the scene. This is an assumption: scenes from the same log share conditions.

**Lemma 4 (Mondrian conditioning preserves exchangeability).** Let Z_1, …, Z_{n+1} be exchangeable, and let A be a measurable property of a single scene ("contains a stratum-g instance"). Let 𝒥 := {j : Z_j ∈ A}. Conditionally on 𝒥 = J, with n + 1 ∈ J, the family (Z_j)_{j∈J} is exchangeable.

*Proof.* Let π permute J and fix every index outside J. Exchangeability gives (Z_{π(1)}, …, Z_{π(n+1)}) =ᵈ (Z_1, …, Z_{n+1}). The event {𝒥 = J} is invariant under π, because π maps J onto J and its complement onto itself. Hence the conditional law given {𝒥 = J} is π-invariant. ∎

**Theorem 5 (scene-level certification by conformal risk control).**
- For a scene j containing stratum g, define the loss L_j^g(c) := (1/N_j^g) Σ_{i∈g in scene j} 1{U_i > c}, for c ∈ ℝ ∪ {+∞}. It is non-increasing and right-continuous in c, bounded by 1, and satisfies L(+∞) = 0.
- Given n_g calibration scenes containing g, set ĉ_g := inf{c : n_g/(n_g + 1)·R̂_g(c) + 1/(n_g + 1) ≤ δ}, with ĉ_g := +∞ if the set is empty.
- Under scene exchangeability, E[L_{test}^g(ĉ_g)] ≤ δ for a new scene containing g.
- Equivalently, P(U_{test,J} > ĉ_g) ≤ δ, where J is drawn uniformly from the new scene's stratum-g instances, independently of everything else. The guarantee is scene-weighted.

*Proof.* Condition on the membership pattern; by Lemma 4 the stratum-g scenes are exchangeable. Apply Theorem 1 of conformal risk control (Angelopoulos et al., ICLR 2024; conditions read in full, `00_CONTEXT/.../30_prior_art/30_CRC_READ_BY_LEAD_v01.md`), then average over patterns. For the equivalence, E[L(c)] = E[(1/N)Σ1{U_i > c}] = P(U_J > c). ∎

*Status.* This is an application of conformal risk control (its §3.1 uses a per-image false-negative rate with images exchangeable and pixels not). A-M30 calibrates per group over exchangeable trajectories. Lemma 4 is the only step to be proved in the article.

**Proposition 6 (floor and practical size).**
- (i) ĉ_g < ∞ requires n_g ≥ 1/δ − 1. This means 19 scenes at δ = 0.05 and 99 at δ = 0.01.
- (ii) The empirical allowance is a(n) := ((n + 1)δ − 1)/n. At n = 2/δ − 1, a(n) = δ/(2 − δ) ≈ δ/2. That means 39 scenes at δ = 0.05 and 199 at δ = 0.01.
- (iii) At the floor, a(n) = 0, so ĉ_g is the largest calibration score: the certificate is valid but maximally conservative.
- (iv) With a union-bound planner, per-constraint levels are about Δ/K. Levels below 1/(n + 1) can be estimated from n scenes but not certified distribution-free.

*Proof.*
- (i) R̂ ≥ 0, so the defining inequality needs 1/(n + 1) ≤ δ.
- (ii) Substitute n + 1 = 2/δ into a(n): ((2/δ)δ − 1)/(2/δ − 1) = 1/(2/δ − 1) = δ/(2 − δ).
- (iii) With a(n) = 0, ĉ is the smallest c at which R̂(c) = 0.
- (iv) This follows from (i). ∎

*Data consequence (nuScenes val: 150 scenes in 18 logs).*
- Log-level certification is infeasible. Holding out one log leaves ≤ 17 units, a floor of 1/18 > 0.05.
- With a 75/75 scene split, δ = 0.05 is certifiable only in cells present in ≥ 39 calibration scenes. δ = 0.01 is not certifiable in any cell.

---

## 6. Summary map: statement → hypothesis it serves → what it predicts or requires

| Statement | Serves | Prediction or requirement |
|---|---|---|
| Thm 1, Prop 1 | Premise (A-N1 role); dose definition (A-N3 E1) | Doses and the reference are defined on projected tails at allocated levels, not on ANEES |
| Thm 2, Cor 2 | Why the reference cannot be "ANEES = d" | The real audit must report projected stratum tails; the 9-D test is uninformative for the planner |
| Thm 3, Cor 3 | H1, H3, H4a, H4b | Before closed loop: measure the dispersion of R_j over active constraints per dose. After closed loop: zero residual after optimal 𝒦₁ retuning for representable doses, a possible nonzero residual only for non-representable ones |
| Thm 4 | Interpreting H4a's transplant; choosing the knob in H3 | Which single knob fails on the real export's (κ, ρ̂) structure, and by how many metres |
| Prop 5 | H-I1 integrity | Hash-level invariance checks; DΣ̂Dᵀ form only |
| Lemma 4, Thm 5, Prop 6 | Any certified recalibration arm (A-N7) | Scene-level certification at δ = 0.05 only; planners' allocated levels can be estimated, not certified |
