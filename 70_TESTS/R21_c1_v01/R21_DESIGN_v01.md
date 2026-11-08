# R21 design v01: independent results review of C1 (written outcome-blind, 7 Nov 2026)

Written before any R21 code, while `c1_analyse_v10` runs on AV2. No real outcome was opened: R21 has read only the frozen plan
(`40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md`), the frozen config and command list, README v10, the criteria library
`50_CODE/c1_criteria/`, and the nuScenes rehearsal stand-in `70_TESTS/c1_v01/rehearsal150_v10/` (plus the AV2-tagged stand-in run
log of `70_TESTS/c1_v01/tests_v13/tree/`). Everything R21 computes on AV2 is computed only after the decision of record exists.

## 1. Duties and plan sections

| Duty | Plan | R21 file |
|---|---|---|
| D1 Re-derive H1 with separate code: M\*'s cell estimates, simultaneous 0.95 bounds and flags; power-family flags; pooled evaluability, LB and flag; floors; HK1c; each comparator's 9 removal conditions at 1 − 0.0125/9; V_t; zero-SE removals; Form B at 1 − 0.0125/\|V_t\| | §6.1, §6.2, §6.3, §6.5 | `r21_rederive_v01.py` |
| D2 H1 with and without zero-SE removals | §6.2 (Zero-SE removals), §6.9 item 5 | `r21_rederive_v01.py` |
| D3 Re-derive the K8 tables (per arm: pooled V1 per population, flagged cells, infeasibility, mean margins, V2 against its reference, V2_viol) | §5 endpoints, §6.6, §9 | `r21_rederive_v01.py` |
| D4 Tables of record against the uploaded run log; the decision names the run-log hash it recorded; stop classification (seven strings, one-output runs) | §8.6, §9 | `r21_runlog_check_v01.py` |
| D5 MC SE of the decisive bounds (removal statistics, Form B, HK1c, p of H3 and H4) by 20 seed sets and Andrews–Buchinsky; share of seed sets under which each H1 flag, floor and Form B bound holds; cells with \|t − q\| < 0.2; every power-family size change; V_t and V^J stability | §6.1 | `r21_mcse_v01.py` |
| Needed for D5 (re-derived, compared too): H3 (ValidJ, V^J, bound, p), H4 (transfer route, removal 1 − 0.0025/9, doubled p), H2 (Form C) | §6.2, §6.3 | `r21_rederive_v01.py` |
| Not re-derived (outside R21's list): H6a/H6b/H7 (method stage), H8, H9, H10, Form A, loop mode | — | reported as "not covered" |

## 2. Definitions R21 implements (from the plan text; criteria library and R16 conventions where the plan is silent)

- **Inputs** (only the run tables the analysis consumes, per route and tracker tag): `run_record_<tag>_decide.json`, `episodes_<tag>_decide.jsonl`, `counts_<tag>_decide.npz`, `decisions_<tag>_decide.npz`, `cal_<tag>_decide.npz`, the fits file (fold of each unit; transfer RETUNED arm; M\*Jx λ qualification), the folds file. Their SHA-256 are checked against the run record.
- **Units.** Sorted unique scene names of entered, non-LOG episodes; `units_are_logs` = true, so a unit is its own log (no nuScenes DEV exclusion: the rehearsal analysis kept all 150 units, verified from its counts table).
- **Cell decoding** (counts `cell`): `l0 = cell % 96`, then step h (8), relied (2), gap bin (3), satisfied (2), enforced (2), in-path (2), offset bin. Base = offset 0, enforced, satisfied, relied, h < 4. PD7 = base; SD1_7 = base and gap bin ≤ 1; PD = base and in-path; NIP = base and not in-path. Cell column j = g·8 + axis·4 + motion with g = l0 // 24, axis = (l0 // 4) % 2, motion = l0 % 4 (range pooled). Pooled cell = all 32 columns. Verified exactly against the rehearsal's `counts.csv` and `cells.csv` (records, exceedances, units, Ê).
- **Estimator** (§6.1 "the log-level mean of each log's rate"): Ê_c = mean over units with N_uc > 0 of X_uc / N_uc.
- **Log bootstrap**: weights W (B × U) multinomial(U, 1/U); Ê\*_bc = Σ_u W_bu p_uc / Σ_u W_bu 1[N_uc > 0]; SE_c = SD over b (ddof 1, NaN-ignoring).
- **Lower sup-t** (flags, removal, pooled LB): T_b = max over family cells with SE > 0 of (Ê\*_bc − Ê_c)/SE_c; q = γ-quantile of T (linear interpolation); LB_c = Ê_c − q·SE_c; flag iff LB_c > δ; a cell with SE = 0 flags iff Ê_c > δ; a non-finite q (every SE = 0) judges every cell by Ê > δ.
- **Upper sup-t** (U_max, HK1c, ValidJ): UB_c = Ê_c + q′·SE_c, q′ the level quantile of max (Ê_c − Ê\*_bc)/SE_c. For the single pooled cell this is the studentised (basic) bound; the percentile bound Q_L(Ê\*) is computed beside it as a diagnostic only.
- **Evaluable**: ≥ 39 units with records (and ≥ 8 logs, implied). Pooled cell evaluable by the same count.
- **Power rule** (§6.1): per evaluable cell, target-only planting (target at 0.15, every other evaluable cell at δ), beta-binomial per (unit, cell) with ρ = 0.5 (Beta(P(1−ρ)/ρ, (1−P)(1−ρ)/ρ), then Binomial(N_uc)), the arm's own N; flagged in the all-evaluable lower sup-t at 0.95 on the first 500 weight rows; qualified iff power ≥ 0.80. R21 shares one background draw across targets per dataset (the target's marginal law is unchanged). R21 runs it with a reduced count (default 500 datasets) as a check; **the exact floor comparison for M\* uses the analysis's own per-cell power at 0.15** (`status.Mstar.descriptive_power`), whose count of cells ≥ 0.80 must equal the analysis's `family_size`. For comparators, whose per-cell power the analysis does not publish, FamFlag uses R21's own family, and family sizes are compared with `comparator_power_families`.
- **Valid, ShownAbove, V_t, Form B, HK1c, floors**: exactly §6.2's formulas (levels 0.95; 1 − 0.0125/9; 0.995 and δ + 0.03 with ≤; F_MIN 6; PD ≥ 1 evaluable cell). A floor-only or HK1c-only failure never removes a comparator.
- **Zero-SE removal**: a removal condition whose only flagged cells (or pooled cell) have SE = 0 and Ê > δ. H1 "without zero-SE removals" recomputes V_t ignoring such flags, then Form B at 1 − 0.0125/\|V_t\| on that set.
- **Infeasible rate**: per unit, infeasible decisions / decisions (decisions npz), checked equal to the episode's `infeasible_frames / frames`; RETUNED per unit from its fold's selected arm. Δ_t(c) = mean over units of (f_M\* − f_c). **Paired bounds are percentile** (§6.1): bm_b = Σ_u W_bu d_u / Σ_u W_bu; UB^γ = γ-quantile of bm; p_c = (k_c + 1)/(B + 1), k_c = #{bm_b ≥ 0}; H1's Form B p = min(1, \|V_t\|·max p_c).
- **RETUNED** (§3.2, D14 A3, register A4): within each route with fitted folds, for held-out fold f, the 21 merged-curve points ordered by α_eq (α itself; δ′ → (z_{1−δ′}/z_{0.95})², ties by name), the first whose training-fold pooled PD7, SD1_7 and PD (unit-level mean of pooled rates) are all ≤ δ; if none qualifies, the last point. Transfer route: the fit's `retuned_transfer_arm`. R21's per-fold choice is compared with the analysis's `RETUNED_E14.arm_of_fold`.
- **V2 and J_P** (decisions `stats` = 4 blocks × 11 fields; blocks 0 NIP-far, 1 IP-far, 2 NIP-near, 3 IP-near; PD7 all, SD1_7 = 2,3, PD = 1,3, NIP = 0,2; `trk` columns nip_far, nip_near, nip_both, ip_far, ip_near, ip_both): a decision counts if ob = 0 and n_P > 0; exceeded if x_P > 0 (V2), v_P > 0 (V2_viol), n_h0/x_h0 (one step), ne/xe (exec), nb/xb (binding); per-unit share, then unit-level mean; reference = unit-level mean of the per-unit mean of 1 − (1 − δ)^{tracks_P}. J_P = V2. Verified exactly on the rehearsal (decision counts, E, reference, mean tracks).
- **Mean margins**: Σ `mg_long_sum` / Σ `n` (and lat) over the cal rows of the population (cal `key // 96` = the same 4 blocks). Verified exactly.
- **H3**: ValidJ(M\*Jx) per P: pooled joint evaluable (≥ 39 units) ∧ LB^{0.95} ≤ δ ∧ UB^{0.995} ≤ δ + 0.03; every fold's M\*Jx λ qualified (fits `joint`); V^J over K_J at 1 − 0.0025/3; bound UB^{1 − 0.025/(2\|V^J\|)}(f_{M\*Jx} − f_c) < 0; p = max_t min(1, 2\|V^J\| max p_c). **H4**: H1's formula on `transfer_lt3d`, removal at 1 − 0.0025/9, nominal bound 1 − 0.025/(2\|V_t\|), p = max_t min(1, 2\|V_t\| max p_c). **H2**: UB^{0.975}(Δ(B4)) ≤ 0.03, p = (k + 1)/(B + 1), k = #{Δ\* > 0.03}.

## 3. Weights: exact reproduction or MC tolerance

The plan fixes the seeds ([20261110, i, j] for the bootstrap, [20261111, i, j] for the power rule, B = 40000, one weight set shared by every arm, power on its first 500 rows) but **not the generator, the log order or the draw scheme**. R21 therefore compares within MC tolerance. Its primary run uses the registered seed with the criteria library's documented scheme (`numpy.random.default_rng(seed).multinomial(U, 1/U, size=B)` over the sorted units, drawn in row chunks, which numpy 1.26.4 reproduces exactly; checked). If the analysis used the same scheme, every R21 bootstrap bound equals the analysis's to floating-point precision; R21 records this ("exact reproduction": all compared bounds within 1e-9) and then treats every status difference as real, with no borderline allowance. The power rule's dataset RNG is not reproducible from the plan; it is always compared within tolerance. R21's own seeds are disjoint from every registered seed: power check [20261122, i, j, arm, pop]; MC seed sets [20261121, i, j, s] and power [20261122, i, j, s, arm, pop], s = 1..20 (arm 0..7 in the order M\*, B0, B1, B3, B4, B6, B9, RETUNED; pop 0..2 in the order PD7, SD1_7, PD).

## 4. Comparison rules (fixed now)

| Quantity | Rule |
|---|---|
| Counts (records, exceedances, units, decisions, evaluable cells), memberships (flagged cells, V_t, V^J, families' sizes), flags, statuses (Valid, ShownAbove, Floor, HK1c, Form B met/vacuous, H1, H2/H3/H4 bound form) | exact |
| Deterministic point estimates (Ê, pooled E, Δ means, infeasible rates, V2, reference, margins) | \|Δ\| ≤ 1e-9 (absolute) |
| Bootstrap bounds (cell LB/UB, pooled LB/UB, U_max, paired UB) | \|Δ\| ≤ tol(B) = 4 · 0.0006 · √(20000/B_R21 + 20000/B_an); 0.0024 at B_R21 = B_an = 40000 (0.0006 = development MC SE at B = 20000, check v03 part E3); 0.0078 at B_R21 = 2000 |
| p-values (k + 1)/(B + 1) | \|Δ\| ≤ 4·√(p(1 − p)(1/B_R21 + 1/B_an)) + 2/B_an |
| Per-cell power (analysis 2000 datasets, R21 N) | \|Δ\| ≤ 4·√(0.16·(1/N + 1/2000)) (0.08 at N = 500) |

**Borderline.** A status difference is classified "MC-borderline" (not a code disagreement) only if R21's deciding bound lies within tol(B) of its threshold (LB vs δ, UB vs δ + 0.03, Form B UB vs 0, a power vs 0.80 within the power tolerance), and only when exact reproduction is not established. Every borderline case is listed, and `r21_mcse_v01.py` reports the share of seed sets under which it holds. Any other difference is a **disagreement**.

## 5. What a disagreement leads to (§9)

The frozen verdict stands whatever R21 finds. Each disagreement is listed in the output JSON with both values, and diagnosed: (a) recomputed a second way (percentile against studentised bound; R21's family against the analysis's; the analysis's RETUNED fold choice against R21's; both weight schemes), (b) traced to an input (hash) or to a definition the plan leaves open. A confirmed code error is reported to the lead for an erratum showing both verdicts; R21 never re-runs or edits anything bound.

## 6. Looks into code other than the criteria library (rule 4 record)

| File, lines | Why | What was taken |
|---|---|---|
| `50_CODE/k6/k6_analyse_v02.py` l.54–128 (grep for `cell_family`, `mask`, `N_L0`, `STEPS_CC`, `MIN_LOGS`) | decode the counts `cell` column (format) | cell names and L0 ids, population masks, MIN_SCENES 39 / MIN_LOGS 8; the range shown also held `rates` (l.121–128), identical to the criteria library's `rates_log` |
| `50_CODE/k6/k6_sim_v02.py` l.70–96, 555–564 (producer of the run tables) | the same column | `decode_cell` field order, `N_L0` 96, `CC_STEPS` 4 |
| `50_CODE/c1_av2/c1_power_counts_v02.py` l.59–184 (S22 builder imported by the criteria library) | loader of the same tables | population specs, RETUNED composition per unit |
| `70_TESTS/r16/r16_decide_recompute.py` (R16's independent K8 recompute, not analysis code) | precedent for the `stats` blocks and RETUNED rule | layouts were then verified against the rehearsal CSVs, not taken on trust |

No statistical function of `c1_analyse_*`, `c1_rules_*` or `k8_analyse_*` was opened. Any later look is appended here. No grep into the analysis code was needed: every format question was settled from the rehearsal's own outputs or the producers above.

## 7. Amendments after the rehearsal test, before any AV2 outcome (7 Nov 2026, 06:00–06:25 local)

Made while testing on the nuScenes stand-in only (`R21_TEST_ON_REHEARSAL_v01.md`); they change how R21 compares, never a C1 rule.

1. **Tolerance per quantity.** A bootstrap bound's tolerance is max(tol(B), 4 × its combined Andrews–Buchinsky MC SE), the MC SE being √(τ(1 − τ)/B)/f̂(q_τ) on R21's own bootstrap distribution (Siddiqui–Bloch–Gastwirth density, scaled by √(1 + B_R21/B_an) for the analysis's own error); for a sup-t bound, the quantile's MC SE times the cell's SE. A bound at a level with fewer than 10 replicates beyond it at R21's B (B(1 − τ) < 10, plan 6.1's own rule for B) is not estimable and gets 0.05; at B = 40000 every C1 level has ≥ 11. p-values: |Δ| ≤ m(4√(p(1 − p)(1/B_R21 + 1/B_an)) + 1/(B_R21 + 1) + 1/(B_an + 1)), m the doubling multiplier 2\|V\| (H3, H4) or 1.
2. **Comparator families.** The analysis publishes each comparator family's size and record share but not its cells. R21 recovers the family as the unique subset of evaluable cells of that size whose record share equals the published one to 1e-12 (searched among cells R21's own power ranks near 0.80); if several subsets match, the one with the largest R21 power sum is used and the case is treated as R21-own (power borderline allowed). FamFlag is then computed on that family. The fully independent variant (every family from R21's power rule) is reported beside it. M\*'s family is the analysis's per-cell power ≥ 0.80, checked against its published size and share.
3. **K8 validity table levels.** The analysis's `validity.csv` reports each arm at its C1 level (comparators of K at the route's removal level, every other arm at 0.95), while `cells.csv` is at 0.95 for every arm; R21's K8 table computes both.
4. **Family-S p-values.** H3's and H4's p are set to 1 when ValidJ(M\*Jx), or Valid(M\*) on the transfer route, fails on a tracker (H1's formula includes Valid; the rehearsal decision shows p = 1 with `validity_gate` false). The plan's p formula on its own is reported beside it.
5. **Bound form confirmed on the stand-in.** The analysis's pooled LB and UB are the studentised sup-t (basic) bounds of section 2, not percentile bounds (rehearsal: B0 PD pooled UB 0.03515 analysis, 0.03526 R21 studentised, 0.0493 percentile); the paired bounds are percentile.
6. Empty analysis CSV fields (an arm with no records in a population) are listed as "info", not compared.
