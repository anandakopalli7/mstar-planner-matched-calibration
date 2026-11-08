# C1 criteria: final check of rule set R* on nuScenes development data (v02, 5 Nov 2026)

**Scope.** These are the lead's computations A to E on the final rule set R*.

**Data.** nuScenes development data only:
- the K8 Linux replicate, with 840 scenes and 68 logs, decision mode, T1 and T3;
- its v03 analysis (ec85ce12…);
- the K8 joint run (`k8_joint_analysis_v04`, 264f7551…), for H3.

**Rules followed.**
- No Argoverse 2 file of any kind was read.
- Only new files were written: code in `50_CODE/c1_criteria/c1crit_rstar_*_v02.py`, outputs in `60_RESULTS/c1_criteria_sensitivity_v02/`. v01's caches are read and never written.
- At most 3 compute processes ran at once. Every long job was checkpointed. C: kept ≥ 41 GB free.

**Checks.** The new R* functions were checked before use:
- the joint loss recomputed here reproduces the stored 0.95 bounds to 1e-15;
- `validity_rstar` reproduces `c1_power_counts_v02.validity` at the old levels on the 840 scenes (asserted).

**Every number below is development evidence, not a confirmation.**

## The value of L

**L = 0.995.**
- On the means over the cells in the band (the reading I applied), 0.975 and 0.99 fail and 0.995 is the smallest level that meets 0.9625 for all six population × tracker combinations. The lowest of those means is 0.967 (T3 SD1_7).
- On the per-cell minima, no level meets 0.9625: the worst is 0.949, T3 SD1_7, cell `B0a0.0625`. So the rule's fallback also gives 0.995.

## A. HK1c level: coverage of the coded pooled UB at 375 units

**Method.** Every decision-mode arm's pooled cell (30 arms) with a scene-level truth in [0.02, 0.10). Each simulated set draws 375 development scenes i.i.d., each scene its own log. 2000 sets, B = 2000. The bound is A.flag's upper form, 2·est − Q_{1−L}. Seeds [20261301, i, 375].

**Coverage, mean (minimum) over cells:**

| Tracker, population (cells) | 0.95 | 0.975 | 0.99 | 0.995 |
|---|---|---|---|---|
| T1 PD7 (13) | 0.933 (0.923) | 0.961 (0.951) | 0.980 (0.971) | 0.988 (0.980) |
| T1 SD1_7 (14) | 0.916 (0.901) | 0.945 (0.930) | 0.966 (0.951) | 0.976 (0.962) |
| T1 PD (20) | 0.911 (0.892) | 0.938 (0.924) | 0.960 (0.947) | 0.970 (0.955) |
| T3 PD7 (8) | 0.934 (0.927) | 0.961 (0.954) | 0.979 (0.972) | 0.988 (0.981) |
| T3 SD1_7 (5) | 0.898 (0.874) | 0.930 (0.905) | 0.955 (0.934) | 0.967 (0.949) |
| T3 PD (8) | 0.907 (0.893) | 0.935 (0.920) | 0.957 (0.942) | 0.968 (0.957) |

**The 8 Form B arms alone** give the same choice. At 0.995 their means are 0.968–0.987.

**M\*'s own pooled cells at 0.995**: 0.988 / 0.983 / 0.974 (T1 PD7 / SD1_7 / PD) and 0.988 / 0.970 / 0.966 (T3).

**Truth in [0.06, 0.10), near the HK1c boundary.** Few real cells fall here:

| | Cells | Coverage at 0.975 / 0.99 / 0.995 |
|---|---|---|
| T1 PD7 | 3 | 0.965 / 0.983 / 0.990 |
| T1 SD1_7 | 2 | 0.960 / 0.979 / 0.987 |
| T1 PD | 5 | 0.952 / 0.973 / 0.981 |
| T3 PD7, T3 SD1_7 | 0 | none |
| T3 PD | 1 | 0.947 / 0.968 / 0.974 |

**Supplement: every band cell rescaled to truth exactly 0.08** (`c1crit_rstar_hk1c_v02`). Each cell keeps its zero inflation and skew; only its level moves. Mean (minimum) coverage over the six combinations:

| Level | Mean | Minimum |
|---|---|---|
| 0.975 | 0.950–0.962 | 0.943–0.951 |
| 0.99 | 0.970–0.981 | 0.963–0.972 |
| 0.995 | 0.979–0.988 | 0.973–0.983 |

## B. The paired percentile UB at 375 units (Form B, Form C, H10)

**Method.** Δ = f_M\* − f_c per scene. The truth is the 840-scene mean. 375 scenes are drawn i.i.d., 4000 sets, B = 2000.

| Tracker, comparator | Truth | Coverage at 0.975 | Coverage at 0.9875 | P(UB < 0) at 0.975 |
|---|---|---|---|---|
| T1 B3 | −0.752 | 0.968 | 0.984 | 1.00 |
| T1 B4 | −0.084 | 0.981 | 0.992 | 1.00 |
| T1 B6 | −0.062 | 0.983 | 0.993 | 1.00 |
| T3 B0 | −0.603 | 0.973 | 0.988 | 1.00 |
| T3 B3 | −0.709 | 0.973 | 0.982 | 1.00 |
| T3 B4 | −0.047 | 0.980 | 0.992 | 1.00 |
| T3 B6 | −0.005 | 0.980 | 0.991 | 0.14 |

- Every coverage is ≥ 0.9625, Bradley's liberal limit at α = 0.025.
- B3 is slightly below nominal: 0.968 at 0.975 on T1, and 0.982 at 0.9875 on T3. The others are at or above nominal.

## C. Development verdict under R* (`C_verdict_rstar_v02.json`)

**The verdicts are unchanged from v07c and v07d on both trackers:**

| | T1 | T3 |
|---|---|---|
| Valid(M\*) | yes | yes |
| V_t | {B3} | {B0, B3} |
| Form A (descriptive) | met | met |
| Form B | met | met |
| Form C | met | met |
| H10 | holds | holds |
| H3 | holds | holds |

Only the bounds move.

**M\*'s families under R\*** (target-only planting, others at δ, 2000 datasets, 500 weights):

| | PD7 | SD1_7 | PD |
|---|---|---|---|
| T1: family (record share) | 27 (0.997) | 18 (0.983) | 5 (0.655) |
| T3: family (record share) | 26 (0.994) | 18 (0.984) | 5 (0.671) |

**M\*'s conditions** (flags at 0.95):
- No cell flag and no family flag.
- The pooled lower bounds are ≤ δ. The pooled estimates are 0.042 / 0.032 / 0.049 on T1 and 0.040 / 0.031 / 0.042 on T3.
- **HK1c at L = 0.995**: the pooled UBs are 0.046 / 0.039 / 0.063 (T1) and 0.044 / 0.037 / 0.053 (T3), all ≤ 0.08.
- The floors are met: 27 or 26 cells on PD7 and 18 on SD1_7, against 6; PD has 18 evaluable cells.

**Comparators, removal at 1 − 0.025/9 per condition:**
- **T1:** B0 is removed by PD7 and SD1_7 cell and family flags. B1, B6, B9 and RETUNED are removed by cell flags. B4 is removed by cell flags and PD's pooled lower bound.
- **T3:** B1, B6, B9 and RETUNED are removed by cell flags. B4 is removed by cell flags and PD's pooled lower bound.
- **B3 (both trackers) and B0 (T3)** meet no condition. Their pooled lower bounds are ≤ 0.0013, and their R\* families are B3 25/7/5 (T1), 25/6/4 (T3) and B0 26/11/4 (T3).
- I computed families only for the arms whose removal could depend on them: M\*, B0 and B3. The others are removed by cell flags, which do not depend on families.

**Form B:**
- T1: UB^{0.975}(M\* − B3) = −0.725.
- T3: UB^{0.9875} = −0.571 (B0) and −0.680 (B3).

**Form A:** met at 1 − 0.05/4, and also at 1 − 0.025/4 (T3 B4 bound −0.029).

**Form C:** UB^{0.975}(M\* − B4) = −0.066 (T1) and −0.033 (T3).

**H10:** the ablation part holds on both trackers. The NI bound UB^{0.975}(M\* − B6) is −0.043 (T1) and +0.005 (T3), both ≤ 0.03.

**H3:**
- ValidJ(M\*Jx): not flagged, and UB_{0.995} is PD7 0.056 / 0.060, SD1_7 0.011 / 0.013, PD 0.005 / 0.008 (T1 / T3), all ≤ 0.08.
- V^J at 1 − 0.025/3: {B3} on T1 and {B0, B3} on T3. RETUNED is absent from the joint run, as in K8.
- Superiority: −0.381 (T1, B3); −0.160 (B0) and −0.263 (B3) on T3 at 0.9875.

## D. OC at 375 units under R* (`D_ckpt/`)

**Method.** 375 development scenes per set, 300 sets per variant, with `c1_power_counts_v02.run_oc` and the R\* validity and forms. "Capped" thins M\*'s cells that sit above δ down to δ, so M\* is valid at cell level.

**How target-only planting with the others at δ is represented.** The OC uses the analytic family: each cell's normal power at P against the Šidák critical value of its evaluable family. The other cells' means do not enter that formula, so all-cells and target-only planting are identical in it, and "2000 datasets" has no meaning there. On the 840 scenes the analytic family **equals R\*'s simulated family for M\* in all six combinations** (27/18/5 and 26/18/5). For B0 and B3 it differs by 0–2 cells (`D_analytic_vs_simulated_v02.json`).

**Results:**

| Variant | P(H1) | P(H1 fails) | Main reasons |
|---|---|---|---|
| Plug-in, P 0.15 | **0.870** | 0.130 | T1: HK1c 0.090, pooled 0.023, family flag 0.017. T3: family flag 0.040, cell flag 0.020 |
| Capped, P 0.15 | **0.940** | 0.060 | T1: HK1c 0.053, pooled 0.013, family flag 0.010. T3: family flag 0.003 |
| Plug-in, P 0.12 (descriptive) | **0.000** | 1.000 | the SD1_7 floor fails in every set (and HK1c 0.057 on T1) |
| Capped, P 0.12 (descriptive) | **0.000** | 1.000 | the SD1_7 floor fails in every set |

**M\*'s families at 375 units**, median (p10), with the record share median (p10):

| | PD7 | SD1_7 | PD |
|---|---|---|---|
| P 0.15 | 23 (22–23); share 0.988 (0.984–0.985) | 11 (9–10); share 0.90–0.91 (0.865–0.88); P(≥ 6) = 1.00 | 3–4 (2–3); share 0.51–0.61 |
| P 0.12 | 18 (17–18); share 0.95 | 3 (2); share 0.57–0.58; P(≥ 6) = 0 | 0 |

- H2 and H10 hold in every set.
- B6 never stays in V_t. B9 stays in V_t in 2–4 % of sets, and B1 on T1 in 3–5 %.

## E. MC accuracy of Form B's bound (B = 2000, level 1 − 0.025/|V_t|)

**Method.** 500 independent log-bootstrap seed sets ([20261305, i, s]), plus the Andrews–Buchinsky order-statistic formula, SE ≈ √(τ(1 − τ)/B)/f̂(q).

| Tracker, comparator (level) | Bound (K8 seed) | MC SE: seed sets / A–B formula | Distance from 0 in MC SEs | Seed sets with UB ≥ 0 |
|---|---|---|---|---|
| T1 B3 (0.975) | −0.7250 | 0.0008 / 0.0009 | 880 | none |
| T3 B0 (0.9875) | −0.5713 | 0.0012 / 0.0011 | 473 | none |
| T3 B3 (0.9875) | −0.6802 | 0.0010 / 0.0011 | 695 | none |

## Surprises, reported plainly

1. **L = 0.995 makes HK1c the main way H1 fails at 375 units, through T1's PD cell.**
   - M\*'s pooled PD exceedance on T1 is 0.049, close to δ.
   - P(HK1c fails on T1) rises from 0.030 (plug-in) and 0.013 (capped) under v07d's 0.95 bound, in v01's OC, to **0.090 and 0.053**.
   - **P(H1 fails | M\* valid at cell level) rises from 0.020 to 0.060**, and plug-in P(H1) falls from 0.903 to 0.870.
   - The v07d figures come from v01's OC (`c1crit_oc375_v01`) with the same draws machinery. Those runs also differ in the removal and superiority levels, but on development data those changes do not move any verdict, so HK1c is the dominant difference.
2. **At the HK1c boundary itself (truth 0.08), 0.99 would already meet 0.9625 everywhere** (minimum 0.963). Rule 6 selects 0.995 because its band [0.02, 0.10) includes lower-truth, more zero-inflated cells, whose bounds are wider. For example, T1 PD at 0.99 has a mean of 0.960 over [0.02, 0.10).
3. **At P = 0.12 the SD1_7 floor fails in every 375-unit development set.** The family median is 3, against 11 at 0.15. On the full 840 scenes the family at 0.12 was 12–15. With 375 units per cell the power curve is steep between 0.12 and 0.15. This is descriptive only, and it uses development record counts, not AV2's.
4. **B3's paired bound slightly under-covers** at 0.975 (0.968, T1). It is within the band, and the bound is 0.73 from 0 with an MC SE below 0.001.

## Files and hashes (SHA-256)

**Code** (`50_CODE/c1_criteria/`):

| File | SHA-256 |
|---|---|
| `c1crit_rstar_v02.py` | 687870d60bcc6d48b7905f2fc06caf3253063427c511d43216f96791ecdc4886 |
| `c1crit_rstar_extra_v02.py` | 5d68ac8010ff78b2e5b76c3262a61789103f6336c704334afef570e1b804fa62 |
| `c1crit_rstar_hk1c_v02.py` | 583c234bf6c0d99b8fe3a3c48885331cee6c2a614862be189669c9ca820aaaa4 |
| `c1crit_common_v01.py` (imported, unchanged) | 627a433d84a6c095008cc527dbc737b5e0f3c8b79fff61b324b3ec8670c28cd4 |

**Outputs** (`60_RESULTS/c1_criteria_sensitivity_v02/`):

| File | SHA-256 |
|---|---|
| `A_hk1c_level_v02.json` | 9a7c56bee3f50da9dee6a6ce25b61710441d639f95a1ec1dd9fabe293f186bfa |
| `A2_hk1c_boundary_v02.json` | 77ed95ee88d73f087c23cf6f1f547532b1a1ef387989c298886605172a4596ec |
| `B_paired_coverage_v02.json` | cb75cc66f492bfb7d5378ded5591d850f02dc3d803e20234595d5d7e41965671 |
| `C_verdict_rstar_v02.json` | e3c58376cc0694446f41349d7f4c614eb3a3ab538f210251555cc3b9e7b4e71a |
| `D_analytic_vs_simulated_v02.json` | 77606e3a7f96d12d69c1185e9ae4ffa5ea732df05887ab9c482cb632030be775 |
| `E_formB_mc_v02.json` | 6a47eee80f39e137998bda97c8ea7de623e13e6c646e1237d101d05c0aa28c65 |
| `cache/pooled_all_arms_t1_v02.npz` | ea4e9280c10c3687ca68e6e31dd9e28790f41e1dc5426cd6cbc67707c0b9e6df |
| `cache/pooled_all_arms_t3_v02.npz` | d27a00ebc53075f825570455accb70127cb6294f79effb8583a5f9722c9f54c6 |

**Checkpoints:** `A_ckpt/` (2), `B_ckpt/` (7), `CP_ckpt/` (18), `D_ckpt/` (4). Logs are in `logs/`. Every file of this folder and the three v02 scripts is hashed in `SHA256SUMS_v02.txt`, this note included.

**Seeds:**

| Part | Seed |
|---|---|
| A | [20261301, i, 375] |
| A2 | [20261306, i, 375] |
| B | [20261302, i, arm] |
| Power families (CP) | [20261303, i, arm, k] |
| D | [20261304, variant] (cap [.., 7]) |
| E | [20261305, i, s] |
| K8 weights | [20261106, i, 0] |
