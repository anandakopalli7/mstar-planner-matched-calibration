# P01 addendum v03 — closes second-pass review R02 (30 Oct 2026)

This addendum responds to `70_TESTS/R02_SECOND_PASS_v01.md`:
- R01 findings: 29 FIXED, 6 PARTLY, 0 NOT FIXED.
- New issues: 0 CRITICAL, 6 MAJOR, 10 MINOR. The 6 MAJOR are fixed here.

How to read the files:
- P01 v02 plus this addendum is the current theory text.
- S01 v02 and D01 v02 are corrected by §G below.
- The 10 MINOR items are accepted. They will be applied when P01 is consolidated into the manuscript draft; they are not re-listed here.

## A. Restored proofs (N5)

**Theorem 4.**
- (a) By Proposition 1, the risk at constraint j is Φ̄(c·√(v̂_j/(p_j + q_j))). Since Φ̄ is strictly decreasing, risk ≤ δ ⇔ c ≥ z_{1−δ}·√((p_j + q_j)/v̂_j) = m_j. Requiring this for all j gives c ≥ max_j m_j. The margin is c√v̂_j, so the excess over m_j√v̂_j is (c − m_j)√v̂_j.
- (b) With inflation s, the risk is Φ̄(z·√((s·p̂_j + q_j)/(κ_j·p̂_j + q_j))) ≤ δ ⇔ s·p̂_j ≥ κ_j·p̂_j ⇔ s ≥ κ_j. The excess is z[√(s·p̂_j + q_j) − √(κ_j·p̂_j + q_j)].
- (c) Direct evaluation; see the checks.
- (d) Let F(c) = Σ_j w_j·risk_j(c), with w_j > 0. Each term is continuous and strictly decreasing in c. At c_agg, F(c_agg) = δ. If every risk_j(c_agg) were ≤ δ and at least one were < δ, then F(c_agg) < δ, a contradiction. So max_j risk_j(c_agg) ≥ δ. Equality throughout holds iff every risk_j(c_agg) = δ, that is, iff every m_j = c_agg. ∎

**Corollary 3 (induction).** Let Ω_k be the full stack state at step k: world state, agent states, emulator state, tracker internal state, planner memory and the positions of all random-number streams.
- Under (C1), Ω_{k+1} = Φ(Ω_k, u_k) for a deterministic map Φ, and the tracker output at step k is a deterministic function of Ω_k.
- Let the two arms be (Σ̂′, θ₀) and (Σ̂, θ), and suppose Ω_k^A = Ω_k^B.
- Then the tracker outputs coincide. By Proposition 5 the intervention changes only the covariance copy.
- By representability and (G), every evaluated tuple has the same margin in both arms, to the stated tolerance (C3).
- By (C2), u_k^A = u_k^B. Hence Ω_{k+1}^A = Ω_{k+1}^B.
- Ω_0 is shared. By induction the trajectories are equal, and so is every functional of the world-state trajectory. ∎

**Proposition 5.**
- (i) For x ≠ 0, xᵀDΣ̂Dᵀx = (Dᵀx)ᵀΣ̂(Dᵀx) > 0, because D is nonsingular. The case sΣ̂ is D = √s·I.
- (ii) The intervention writes only a copy of the covariance. Means, identities, scores and the emitted set are inputs it does not write. At a fixed world-state history they are therefore unchanged, and so is any metric computed from them.
- (iii) The determinant of [[0.5, 0.9], [0.9, 1]] is −0.31 < 0. ∎

**Lemma 4.** Let π be any permutation of J that fixes the indices outside J.
- By exchangeability, (Z_{π(1)}, …, Z_{π(n+1)}) has the same law as (Z_1, …, Z_{n+1}).
- The event {𝒥 = J} = {Z_j ∈ A for all j ∈ J, Z_j ∉ A for all j ∉ J} is mapped onto itself by π.
- So for any measurable B, P((Z_{π(j)})_{j∈J} ∈ B, 𝒥 = J) = P((Z_j)_{j∈J} ∈ B, 𝒥 = J).
- Dividing by P(𝒥 = J) > 0 gives exchangeability conditional on {𝒥 = J}. ∎

**Theorem 5.**
- Condition on 𝒥 = J with the test scene in J, and let n_g = |J| − 1.
- By Lemma 4, the n_g + 1 loss functions L_j^g, j ∈ J, are exchangeable.
- Each L_j^g is non-increasing in c (indicators of {U > c}), right-continuous (because 1{U > c} → 1{U > c₀} as c ↓ c₀), and bounded by B = 1.
- L(+∞) = 0 ≤ δ, so λ_max = +∞ satisfies CRC's condition.
- CRC Theorem 1 gives E[L_test^g(ĉ_g) | 𝒥 = J] ≤ δ. Averaging over J yields the unconditional bound.
- Equivalence: let J* be uniform on the test scene's stratum-g instances, independent of everything else. Then E[L_test^g(c)] = E[(1/N)·Σ_i 1{U_i > c}] = P(U_{J*} > c). Substituting c = ĉ_g, which is fixed by the calibration scenes, gives the stated form. ∎

**Proposition 6.**
- (i) R̂_g ≥ 0, so the defining inequality needs 1/(n_g + 1) ≤ δ, that is, n_g ≥ 1/δ − 1.
- (ii) The inequality is equivalent to R̂_g(c) ≤ ((n + 1)δ − 1)/n = a(n). With n + 1 = 2/δ, this gives a(n) = (2 − 1)/(2/δ − 1) = δ/(2 − δ).
- (iii) When a(n) = 0, ĉ is the infimum over c with R̂(c) = 0, which is the largest calibration score.
- (iv) This follows from (i), for this construction. ∎

## B. How exact the H3/PC3 control can be (N2, N3, N8 of R01)

- **N2.** Bit-identical margins cannot be promised under δ-grid retuning. Computing z_{1−δ} from a stored δ reintroduces rounding, and the review found errors above 10⁻⁹ in two tested cases. The control therefore uses the archive's own criterion: **margins equal within 10⁻⁹ relative, and identical discrete choices** (S3 PC3). It also uses a **multiplier-parameterised** retuning grid for this control. The grid stores c values directly and contains c₀·2^k exactly. Exactness is claimed only for decisions: identical commands verified step by step. It is not claimed for bit patterns.
- **N3.** The set of θ that reproduce the dosed run is generally an **interval**; v03's own toy reproduces exactly over θ ∈ [1.9994, 2.0012]·c₀. It is not only the single representing value θ*. Corollary 3's statement "the effect vanishes after retuning to the representing θ" is kept. "Only" is withdrawn.
- **Revised (C3).** Margins agree within a tolerance smaller than the planner's decision resolution, and identical discrete choices are verified at every step.

## C. Check coverage (N4)

The sentence in P01 v02 and in summary v02, "every quoted number has a pass flag", is withdrawn.
- **Flagged in v03:** the numbers listed in the v02 summary table.
- **Checked in `p01_verify_v01_results.json`, where those flags passed:**
  - T4d, worst risk 0.0215 at the aggregate knob;
  - P5, PD preservation and det −0.31;
  - P6, the allowance identity;
  - the C3 v02 toy values.
- **T1i in v03 is a restatement check.** The slack identity is definitional. It is retained as a code-path test only.
- **The T5 flag is one-sided.** It detects anti-conservative bugs only. The reported E[L] = 0.030 at δ = 0.05 also shows the expected conservatism.
- **Not yet in the suite:** a covariance-dependent normal, and a non-power-of-2 dose with a continuous optimiser. These are added to the S2 code tasks.

## D. Credit (N6, N7)

- **D01 v02 reason 5 understated the credit.** The parallel reassessment (REA) also states the **19/99 conformal support floor**. P01's Proposition 6(i) is the same floor, and the article will credit REA for it. The practical-size rule in Proposition 6(ii) is this review's addition.
- **Proposition 1 ("added").** This is added relative to AARCH §1.5 and REA. It first appeared as T1a in this programme's own 30 Oct resumption review. It is a programme-internal step, not a claim against the literature.
- "First precise form" (Theorem 1) is reworded to "precise form".
- **Binding-R_j dispersion.** The archived H3 already anticipates "the residual grows with ρ at the binding horizon" (S3 l. 360), and S3 l. 272 lists binding constraints as a behaviour endpoint. The diagnostic is credited there.

## E. Schedule (N1)

X2 is the archived E2b/H9. It needs the **frozen planner** (after G4) and belongs at **G2b** in the frozen order. S01 v02's S4 placed X2 too early; that placement is withdrawn.
- **S4 = X1 only.** X1 is the open-loop audit; it needs no planner and sits outside the gate graph.
- **The binding-R_j dispersion** is computed at G2b with the frozen planner.

## G. Corrections to S01 v02 and D01 v02

- **S01 v02 §4, S4:** "X1 audit on 150 val scenes" only. Delete "X2 binding-R_j dispersion along logged trajectories". X2 runs at G2b within S6.
- **S01 v02 §2, K-X2:** add "(at G2b, with the frozen planner)".
- **S01 v02 Controls:** replace "a bitwise-determinism test" and "δ-grid closed under …" with §B's criterion: a multiplier-parameterised grid, margins within 10⁻⁹ relative, and identical choices verified.
- **D01 v02 reason 5:** add the 19/99 floor to the REA list.
