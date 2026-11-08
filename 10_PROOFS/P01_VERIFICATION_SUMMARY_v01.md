# P01 verification summary (v01, 30 Oct 2026)

The scripts are in `checks/`. They use numpy and the Python standard library only, are seeded, and use synthetic data only.

| Statement in P01 | Check | Result |
|---|---|---|
| Lemma 1 | Monte Carlo against the closed form | pass |
| Theorem 1 (i) | 20,000 random instances: event inclusion, and equality on active constraints | pass (0 violations) |
| Theorem 1 (ii) counterexample | Marginal 0.010 against conditional 0.020 | pass |
| Proposition 1 | Formula against Monte Carlo; monotonicity; limits | pass |
| Lemma 3, Corollary 2 | 5,000 random 4-D cases; maximum ratio ≤ 1 | pass |
| Theorem 2 (b2) | Quadrature against Monte Carlo: 0.0268 / 0.0181 / 0.0121, with NEES p_v95 = 0.0500 | pass |
| Theorem 3 (iii) | The dose ratio R varies over horizons, 1.53 → 1.42 (s = 4, CV export, Q ∝ t²) | pass |
| Corollary 3 | `p01_verify_v02_c3.py` (supersedes the C3 flag in v01, see below) | pass |
| Theorem 4 (c), (d) | 2.513 / 3.150 / 0.637; 2.849 = 2.849 / 0.441; worst risk 0.0215 at the aggregate knob | pass |
| Proposition 5 | 2,000 random nonsingular D; block-replacement determinant −0.31 | pass |
| Theorem 5 | Scene-level conformal risk control (CRC), Mondrian stratum, clustered heavy-tailed scores. Mean test exceedance 0.028 (δ 0.05, n 40), 0.041 (δ 0.05, n 80), 0.067 (δ 0.10, n 25), each ≤ δ | pass |
| Proposition 6 | The allowance identity a(2/δ − 1) = δ/(2 − δ) | pass |

## The Corollary 3 checks: what went wrong in v01, and what v02 shows

The v01 check flagged Corollary 3 as failing. That failure was a fault in the test, not in the corollary. The test expected the *converse* of Corollary 3, namely that a dose a single global risk setting cannot reproduce must change outcomes. The corollary explicitly does not claim that.

In v01's toy, only one horizon ever bound. A single global multiplier reproduced the dosed commands exactly (best mismatch 0.0). So the run simply illustrated the converse failing.

`p01_verify_v02_c3.py` separates the three cases:

| Case | What it shows | Result |
|---|---|---|
| C3a | A dose a single global setting can reproduce (Q = 0, global): the trajectory is identical after retuning to c√s, and the dose does change the commands when not retuned | pass |
| C3b | A dose no single global setting can reproduce, with one binding horizon: the best global retune leaves a residual of only 0.1 (summed absolute acceleration) in this run, or 0 in the v01 variant | the converse fails, as stated |
| C3c | A braking lead makes the binding horizon switch (1, 2 and 4 s). No global multiplier on a 1,601-point grid reproduces the dosed run (minimum residual 0.4). Horizon-specific multipliers (the 𝒦₃ representation) reproduce it exactly | pass |

**What this means for A-N3.** Whether a non-representable dose matters for outcomes depends on how often the binding constraint switches across horizons or objects. This is a measurable property of the scenarios, and A-N3's design must report it. The ratio spread in this toy is mild (1.29–1.38), and the residual is correspondingly small.
