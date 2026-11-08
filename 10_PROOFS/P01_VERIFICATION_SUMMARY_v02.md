# P01 v02 verification summary (30 Oct 2026)

**Reference script.** `checks/p01_verify_v03.py` (synthetic; numpy + stdlib; seed 20261031). Results are in `p01_verify_v03_results.json`, with **ALL_PASS = true** across 16 flags. Every check builds its object from first principles. None is a restatement of the claim it tests.

The older scripts are kept for history only:
- `p01_verify_v01.py`: ALL_PASS false. Its Corollary 3 test wrongly expected the converse.
- `p01_verify_v02_c3.py`: its C3b residual of 0.1 is a grid artefact. At the exact multiplier c₀R₄ the mismatch is 0.

## What each check covers

| Flag | Statement | Checked value |
|---|---|---|
| L1 | Lemma 1 | Monte Carlo vs closed form, relative error < 1 %, at a non-trivial probability |
| T1i | Theorem 1(i), slack-aware | P(a'X > b) = P(U > τ) exactly on three slacks |
| T1ii | Theorem 1(ii) counterexample, built as a half-normal mixture | marginal 0.0100; conditional 0.0200; variance 1.00 |
| P1 | Proposition 1 | formula vs Monte Carlo, including κ = 0.5 (relative error < 3 %) |
| L3, C2, chi9, C1 | Lemma 3; Corollary 2; radius 4.113; ratio 1.30 | random matrices; χ²₉ 95 % quantile simulated |
| T2a | Theorem 2(a) | E[N] computed from e (2.00); axis-2 risk 0.0288 |
| T2b2 | Theorem 2(b2) | N computed from e; p_v95 = 0.050; risks 0.0268, 0.0181, 0.0121 |
| T2d | Theorem 2(d), 2-D t₃ embedding | 0.0137 at δ = 0.01; 0.0064 at δ = 0.001 |
| T3_ccjoint | Theorem 3(iii) | best single θ misses a margin by 4.5 % (CC-joint, Q ≡ 0, s = 4) |
| T3iii | Theorem 3(iv), with cross-covariance | ρ̂ ranges 0.57–6.2 (q ∝ t²) and 0.24–51.7 (q ∝ t³) |
| C3_suite | Corollary 3 conditions | see the four rows below |
| T4c | Theorem 4(c) | 0.637 and 0.441 exported-SD units |
| T5 | Theorem 5, random stratum membership | E[L] = 0.030 ± 0.001 at δ = 0.05, n_g 33–60 |

The C3_suite flag covers four cases:

| Case | Result |
|---|---|
| Margin-only planner, Q ≡ 0, s = 4 | identical trajectories after retuning to 2c |
| Covariance enters the cost | identity breaks: summed \|Δa\| = 90.55 |
| Time-varying export, single horizon | residual 10.3 after the best global retune, with no horizon switching |
| Retuning grid lacks the representing value | residual 0.5 |

## What the checks do not cover

These are proofs, not simulations of the archive's planner:
- the full CC-joint closed loop;
- the sampler;
- reactive agents;
- GPU nondeterminism.

The C3 toys are one-dimensional illustrations of the *conditions* in Corollary 3. They are not evidence about A-N3 outcomes.
