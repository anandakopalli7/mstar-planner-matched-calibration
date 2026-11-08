# C1 criteria sensitivity on nuScenes development data (v01, 5 Nov 2026)

**Question.** Are the pass/fail thresholds of the C1 plan draft v07d (§2, §6) supported by development evidence, and do the development verdicts depend on them? This is the empirical half of the audit. The literature half is `90_DECISIONS/C1_CRITERIA_EVIDENCE_REVIEW_v01.md` (d24bfe63…). Its §6 lists eight development computations; they are folded in here (§9 maps them).

**Data.** nuScenes development data only: the K8 Linux replicate (`70_TESTS/k8_expl_v02_linux/`; 840 scenes, 68 logs, decision mode, T1 and T3) and its v03 analysis (`70_TESTS/k8_expl_v02_linux_analysis_v03/k8_exploratory_analysis_v03.json`, ec85ce12…, confirmed by R16). The K8 joint run (`70_TESTS/k8_joint_v01_linux/full_v02fits/k8_joint_analysis_v04.json`, 264f7551…) is used for H3's comparator set.
- **No Argoverse 2 file was read.** That includes `60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v02.json`, which the lead allowed for item 3: it was not needed.
- The power tools were called with `matched = False`. That path never opens the AV2 counts.
- No file outside `50_CODE/c1_criteria/` and `60_RESULTS/c1_criteria_sensitivity_v01/` was written, and no existing file was edited.

**Method.** The existing code was reused by import:
- `k8_analyse_v03.hk1_rule` for validity;
- `k6_analyse_v02` for `rates`, `flag`, `evaluable` and `power_family`, with `m_lib_v04._simul`;
- `c1_power_counts_v02` for `load_tracker`, `run_oc`, `validity` and `forms`, and `c1_power_counts_v03.cap_mstar`;
- `c1_analyse_v02` for `arm_status`, `paired`, `form_a`, `form_c` and `joint_status`.

Power settings were changed only through module globals inside each process. Two small pieces are new code, and each was checked:
- **Target-only planting** (`c1crit_power2_v01.power_target`). With every base cell set to the effect, it agrees with `power_family` within Monte Carlo error: the largest cell difference is 0.083 or 0.073, against an MC SE of 0.041 for a difference.
- **The v07d removal rule.** It is the 3-line wrapper of `c1_power_counts_v05.validity_v05` and the logic of `c1_analyse_v09.comparator_reasons`, re-stated rather than imported, because importing them would pull in the guard and the Trajectron++ tools.

Every seed is recorded in its checkpoint. At most 3 compute processes ran at once, every long job was checkpointed, and C: kept ≥ 38 GB free.

**Reproduction first** (`repro_v01.json`). With the K8 seeds (bootstrap `[20261106, i, 0]`, power `[20261107, i, …]`), the reused code reproduces every stored development number exactly, on both trackers:
- the validity tables of all 8 arms: flags, families, quantiles, pooled E/lb/ub and HK1c;
- M\*'s power values;
- the infeasible rates;
- Form A's bounds, Form B's V_t and bounds, and Form C's bound.

`c1_analyse_v02.arm_status` and `k8_analyse_v03.form_valid` agree with the parametrised status function at F_MIN = 6 and HK1c = 0.03.

The development verdict is:

| | T1 | T3 |
|---|---|---|
| Valid(M\*) | yes | yes |
| Not shown above δ (V_t) | B3 | B0, B3 |
| Form A, Form B, Form C | met, met, met | met, met, met |

**Every number below is nuScenes development evidence, not a confirmation.** Full tables are in `C1_CRITERIA_SENSITIVITY_TABLES_v01.md` (T1 to T9).

---

## 0. Answers and recommendations at a glance

| Threshold | What the development data say | Recommendation | Confidence |
|---|---|---|---|
| ρ = 0.5 (power rule) | The beta-binomial fits per cell. The ICC estimates vary by population and estimator. PD7: 0.10–0.31. SD1_7: 0.22–0.45. PD: 0.21–0.53. Cells near the 0.15 alternative: median 0.42–0.48. The observed variance is 67–78 % (PD7) and 87–96 % (SD1_7) of what ρ = 0.5 implies, and 96–110 % for PD; 0.5 is about right at the alternative's prevalence. No verdict changes for ρ in [0.2, 0.7] at an effect of 0.15 | **Keep 0.5, with a written derivation** (§2): it is at or above the upper 80 % limit of every pooled ICC on PD7 and SD1_7 (largest 0.341), and close to the per-cell median at the alternative's prevalence | medium-high |
| 200 simulated datasets | MC SE 0.028 at power 0.80. Cells within 2 MC SE of the cut: 40 of 571 arm-population cells on T1 (M\*: 2), 35 of 578 on T3 (M\*: 4). Going to 2000 datasets changes 7 cells per tracker, M\*'s T1 PD7 family 28 → 27, no floor and no verdict. **But at an effect of 0.10 the SD1_7 floor is decided by MC noise** (T1: 4 at 200 datasets, 6 at 1000; T3: 8 and 5) | **Change to 2000 datasets** (MC SE 0.009). 500 or 2000 weights give identical families, so either is fine | high |
| Sup-t quantile, B = 2000 | MC SE of q: 0.03–0.08. Five other bootstrap seed sets: 0 flag changes on T1; 2–3 per set on T3, every one a comparator cell with \|t − q\| < 0.2. M\* never changes, and no Form verdict changes | **Keep B = 2000**. R21's 20-seed-set report is the right check | high |
| Evaluable at ≥ 39 logs | The flag's lower bound is conservative at every count from 10 to 150 units. The actual size at a true δ is 0.004–0.026 for one cell and ≤ 0.003 for families of 8–32 cells, under Bradley's 0.025 at all but one point. Upper bounds under-cover at every count: near δ 0.78–0.82 at 39 units, 0.87–0.90 at 150; pooled cells at 375 units 0.915–0.920. Power-qualified cells have ≥ 110 (PD7) or ≥ 139 (SD1_7) scenes | **Keep 39, but re-justify it.** It is P01 Prop 6(ii)'s calibration result, and the flag is valid (conservative) at any count ≥ 10. It is **not** a coverage threshold. State that cell upper bounds (U_max) under-cover for zero-inflated cells, or replace them by a bound that handles all-zero samples (§4) | medium-high |
| Planted effect 0.15 | B4 and B6 flagged cells (72): median 0.158 [IQR 0.113, 0.184]. PD7 only: 0.145. All comparators shown above δ: 0.151. But B6 on T3, which decides Form B there, fails at 0.113 (PD7) and 0.101 (SD1_7). At 0.10 M\*'s SD1_7 floor fails (T1; T3 with ≥ 1000 datasets); at 0.12–0.125 both trackers pass | **Keep 0.15 with its anchor**: "the median exceedance of the comparator cells flagged on development". Report the family at 0.12 (the lower-quartile anchor) beside it. **Do not move to 0.10**: development data say the floor then fails on T1 | medium |
| All cells planted vs target only | At 0.15 the families barely move: PD7 by ≤ 1 cell, SD1_7 unchanged except at ρ 0.7 (18 → 15 on T1, 18 → 17 on T3). At 0.10 SD1_7 on T1 drops 6 → 3 | **Use target-only planting** (individual power, which is what the paper's sentence says). At 0.15 it changes no development verdict | high |
| F_MIN = 6 | F_MIN 4 to 8 changes nothing: M\*'s families are 18 (SD1_7) and 27–28 (PD7). The families cover 98.3–98.4 % (SD1_7) and 99.6–99.7 % (PD7) of M\*'s records. The 6 most powerful cells cover 66 % (PD7) and 75–76 % (SD1_7). M\*'s SD1_7 family lacks `car\|long\|new` on both trackers | **Keep F_MIN = 6**, or replace it by a coverage floor of 0.85–0.90 of records (a 6-cell family could not pass it by itself). **Do not adopt "contains every moving-car cell"**: M\* would fail it on development | medium |
| HK1c margin 0.03 | 0.02 / 0.03 / 0.05: no flip (M\*'s largest pooled UB is 0.058, T1 PD). The pooled UB covers 0.915–0.920 near δ at 375 units | **Keep 0.03** with the review's Beta(l, n + 1 − l) derivation; note the 3-point under-coverage of the pooled bound | high |
| c = 0.03 | 0.02 / 0.03 / 0.05: no flip (UB of M\* − B4: −0.068 T1, −0.036 T3) | **Keep** (secondary only) | high |
| Leaving V_t (9 conditions at 0.05 each) | P(a comparator truly at δ everywhere is removed) = 0.094–0.142, mostly from the three pooled lower bounds. At 1 − 0.05/9 per condition it is 0.002–0.018, and on development V_t and Form B are unchanged | **Adopt familywise removal** (each condition at 1 − 0.05/9). Otherwise state Form B's false-pass bound as ≈ α + 0.14 | medium-high |
| New comparator rule (D16 Choices 47e, 49c) | No comparator fails HK1c only, on either tracker, in any setting, on the per-constraint or the joint loss. V_t, V^J_t and every Form are identical to v07c's | No action | high |

**Where the development verdict flips.** Only through the planted effect:
- At **P = 0.10**: T1 fails at ρ ≥ 0.5, and at ρ = 0.4 with F_MIN = 8. T3 fails at ρ = 0.7 with 200 datasets, and at ρ = 0.5 with 1000 datasets or target planting.
- The failure is always **M\*'s SD1_7 floor**, which makes Valid(M\*) false and so Forms A and B fail. Form C holds.
- Nothing else flips: ρ in {0.2, 0.3, 0.4, 0.5, 0.7} at P ≥ 0.125; F_MIN 4–8; HK1c 0.02–0.05; c 0.02–0.05; MC seeds; the comparator rules.
- Which comparators are shown above δ never changes.

---

## 1. Q1: the intra-scene correlation ρ (and lead item 1)

**What ρ is.** In `power_family` each (scene, cell) draws a rate P ~ Beta(mean 0.15, ICC ρ), and records are Binomial(n, P). So ρ is the ICC of the exceedance indicators of one scene's records in one cell.

**How it was estimated** (`c1crit_rho_v01`, `c1crit_bbcheck_v01`, `c1crit_summary_v01.q1_moment`). Per arm, population and cell, with pooling over each population's evaluable cells that have exceedances. Four estimators:
- **ANOVA ICC for binary data** (Ridout, Demétrio and Firth 1999; stratified by cell for pooling). It is record-weighted.
- **Beta-binomial maximum likelihood**, with a common ρ and cell-specific means: the rule's model.
- **The scene-unweighted moment estimator.** This is the dispersion the rule's estimand, the scene mean, actually sees.
- **The implied ρ.** The ρ at which the model's variance of the cell estimate equals the real log-bootstrap variance.

Intervals are 95 % log-cluster bootstrap intervals (seed `[20261205, i, 1]`; B = 1000 for ANOVA, 200 for ML).

**Pooled estimates, M\*** (Tables T1, T1b):

| | PD7 T1 | PD7 T3 | SD1_7 T1 | SD1_7 T3 | PD T1 | PD T3 |
|---|---|---|---|---|---|---|
| ANOVA ICC [95 %] | 0.117 [0.105, 0.127] | 0.103 [0.091, 0.117] | 0.242 [0.205, 0.269] | 0.270 [0.214, 0.339] | 0.321 [0.265, 0.370] | 0.274 [0.218, 0.325] |
| ANOVA, upper 80 % limit | 0.123 | 0.111 | 0.258 | 0.310 | 0.353 | 0.305 |
| Beta-binomial ML [95 %] | 0.185 [0.172, 0.200] | 0.149 [0.135, 0.163] | 0.306 [0.265, 0.342] | 0.276 [0.247, 0.302] | 0.411 [0.352, 0.476] | 0.323 [0.244, 0.391] |
| Moment (scene-unweighted) | 0.278 | 0.266 | 0.423 | 0.369 | 0.520 | 0.429 |
| Per-cell BB, 75th percentile | 0.342 | 0.258 | 0.542 | 0.484 | 0.611 | 0.404 |

**B4 and B6, which have more exceedances.** ANOVA gives 0.11–0.18 on PD7, 0.23–0.32 on SD1_7 (largest upper 80 % limit 0.341) and 0.21–0.44 on PD. Beta-binomial ML gives 0.17–0.25 (PD7), 0.22–0.38 (SD1_7) and 0.35–0.53 (PD).

**ρ rises with the cell's exceedance level** (all arms, populations and trackers; Table T1b):

| Cell exceedance | Cells | BB median | Moment median |
|---|---|---|---|
| < 0.03 | 499 | 0.14 | 0.18 |
| 0.03 to 0.08 | 321 | 0.30 | 0.38 |
| 0.08 to 0.30 | 201 | 0.39 | 0.46 |
| **0.10 to 0.20** (the alternative) | 124 | **0.42** (q90 0.67) | **0.48** (q75 0.57, q90 0.71) |

**Fit check** (item 1). Per cell, the beta-binomial ML fit reproduces the observed between-scene variance of the per-scene rates (median ratio 1.01–1.23) and the number of scenes with no exceedance (1.00–1.03). At ρ = 0.5 the observed / model variance is:
- PD7: 0.67–0.78, so 0.5 overstates the dispersion;
- SD1_7: 0.87–0.96;
- PD: 0.96–1.10.

**Log design effect.** The K8 log-bootstrap variance over the scene-i.i.d. variance of a cell estimate has a median of 0.94–1.15. Scenes within a nuScenes log are nearly independent, so the scene-level ICC is the right analogue of an AV2 log, as the review assumed.

**Which ρ the data support.**
- About 0.10–0.31 pooled on PD7, 0.22–0.45 on SD1_7 and 0.21–0.53 on PD, depending on the estimator.
- About 0.42–0.48 in cells whose exceedance is near the 0.15 alternative.
- So 0.5 is **conservative** for PD7 and, mildly, for SD1_7 in aggregate, and **about right** for PD and at the alternative's prevalence.
- It is **anti-conservative only in the upper tail of single cells**: q90 0.67–0.71 at prevalence 0.10–0.20, and PD's per-cell 75th percentile reaches 0.61.

**Recommendation.** Keep ρ = 0.5 and replace "a design choice of D14" by this derivation: 0.5 is at or above the upper 80 % limit of every pooled ANOVA ICC on the floor populations PD7 and SD1_7 for M\*, B4 and B6 (largest 0.341), and close to the median per-cell ICC at exceedances of 0.10–0.20 (0.42–0.48). The planning-value advice is Donner and Klar's. The verdict does not depend on it (§5).

## 2. Q2: Monte Carlo error (lead item 3, first two settings)

**The power rule's 200 datasets** (`c1crit_mc_v01`, Tables T2 and T6):
- **MC SE at 0.80**: √(0.8 × 0.2 / 200) = 0.028. The 2-SE band is [0.743, 0.857].
- **Cells in the band at 200 datasets**: 40 of 571 evaluable arm × population cells on T1 (M\*: 2 of 75: PD7 `two_wheeler|long|new` 0.815, PD `car|lat|straight` 0.75), and 35 of 578 on T3 (M\*: 4 of 74).
- **Rerun at 1000 and 2000 datasets** (the same seeds, nested draws):
  - status changes: 7 cells on T1 at both counts; 6 and 7 on T3;
  - M\*'s T1 PD7 family 28 → 27, because `two_wheeler|long|new` drops from 0.815 to 0.776;
  - comparator families move by ±1–2;
  - **no floor changes and no verdict changes.**
- **5 alternative power seed sets** at 200 datasets: M\*'s families range PD7 27–28 (T1) and 27–29 (T3), SD1_7 18 (both), PD 5–6 (T1) and 5 (T3). No verdict changes.
- **Weights.** 500 against all 2000 bootstrap weights (2000 datasets) gives identical families on both trackers: PD7 27, SD1_7 18. The 500-weight run equals `c1crit_mc_v01`'s P2000 exactly, which cross-checks the code.
- **Where MC error does decide.** At P = 0.10 M\*'s SD1_7 family is:
  - T1: 4 with 200 datasets, 6 with 1000 (target-only 3);
  - T3: 8 with 200 datasets, 5 with 1000.

  So near the floor the 200-dataset rule can flip the verdict either way.

**The sup-t quantile, B = 2000** (5 alternative bootstrap seed sets `[20261106, i, 0, s]`, s = 1 to 5; Table T2b):
- **MC SE of q**: 0.03–0.08 from resampling the 2000 max-t draws, and 0.02–0.08 as the SD over the 6 seed sets. M\*'s q is 3.16–3.22, with SE about 0.03–0.05.
- **Flag changes against the K8 seeds**: T1 has 0 all-evaluable flag changes in 5 sets. T3 has 2–3 per set, all in comparator cells within 0.2 of q:
  - B1 SD1_7 `large|long|turning` (t 3.41, q 3.40) is flagged only at the K8 seed;
  - B6 PD7 `two_wheeler|lat|new` and `two_wheeler|lat|straight`;
  - B6 SD1_7 `car|long|new`.
- **Family sizes** move by ±1. **Valid(M\*), V_t and Forms A, B, C are unchanged in all 10 sets**, both with the families recomputed and with the families held fixed.

**Recommendation.**
- Use **2000 datasets** for the power rule (MC SE 0.009). A cell at true power 0.78 then qualifies with probability about 0.02, against about 0.28 at 200 (the review's figure).
- 500 weights are enough.
- Keep **B = 2000** for the flags.

## 3. Q3: the minimum number of logs for an evaluable cell (and lead item 5)

**Coverage** (`c1crit_cover_v01`, `c1crit_cover2_v01`, Tables T3 and T3b). The cells used are the 423 development cells with ≥ 300 scenes, across all 8 arms, 3 populations and both trackers; the truth is the cell's scene-level mean. Each simulated cell draws n whole scenes i.i.d., each its own log as on AV2. There are 2000 simulated cells per n, with B = 2000 unit-bootstrap draws each. Coverage of the one-sided 95 % bounds, near δ (truth in [0.02, 0.10)):

| Units n | 10 | 20 | 30 | 39 | 50 | 75 | 100 | 150 |
|---|---|---|---|---|---|---|---|---|
| Lower, percentile | 0.986 | 0.983 | 0.982 | 0.981 | 0.978 | 0.976 | 0.973 | 0.971 |
| Lower, coded (the flag's form for one cell) | 0.994 | 0.994 | 0.993 | 0.992 | 0.990 | 0.988 | 0.986 | 0.983 |
| Upper, percentile | 0.671 | 0.754 | 0.794 | 0.817 | 0.837 | 0.866 | 0.882 | 0.899 |
| Upper, coded (HK1c's and U_max's form) | 0.621 | 0.709 | 0.754 | 0.780 | 0.803 | 0.836 | 0.853 | 0.874 |
| Samples with zero SE (all cells) | 0.338 | 0.233 | 0.183 | 0.155 | 0.132 | 0.101 | 0.082 | 0.062 |

- **The lower bound is never within 1–2 points of nominal; it over-covers.** At every n from 10 to 150 it is conservative (a single-cell false flag of 1–3 %).
- **The upper bound never reaches 0.93 by 150 units.** The cause is zero inflation: most scenes have no exceedance in a cell, a few have many, and a sample with no exceedance has an upper bound of 0.
- **Pooled cells, as HK1c uses them.** At 375 units the coded upper bound covers 0.920 (T1) and 0.915 (T3) near δ, with a minimum of 0.886–0.902. It is 0.83 at 39 units.
- **At the per-cell strength of the sup-t bound** (Šidák over 32 cells, level 0.9984), the upper bound covers only 0.85 near δ at 39 units and 0.94–0.95 at 150, against a nominal 0.998.

**The actual size of the flag at a true δ** (`c1crit_size_v01`; item 5; Table T4). Cells were planted at exactly δ, either by rescaling the empirical scene-rate shapes of the 128 large development cells with exceedance 0.03–0.08 or by beta-binomial draws with ρ = 0.3 or 0.5. The flag is the rule's: one-sided sup-t at 0.95, B = 2000, 2000 families per point.

| | G = 10 | 20 | 30 | 39 | 50 | 80 | 150 |
|---|---|---|---|---|---|---|---|
| One cell, empirical shapes | 0.004 | 0.005 | 0.006 | 0.008 | 0.013 | 0.010 | 0.026 |
| One cell, BB ρ 0.5 | 0.004 | 0.005 | 0.007 | 0.012 | 0.012 | 0.015 | 0.013 |
| Family of 8 cells, any flag, empirical | 0.001 | 0 | 0 | 0 | 0.001 | 0 | 0.003 |
| Family of 32 cells, any flag, empirical | 0.001 | 0 | 0 | 0 | 0 | 0 | 0 |

**Against Bradley's liberal band [0.025, 0.075]**, the flag is below the band, i.e. conservative, at every G. The single-cell empirical case at G = 150 (0.026) is the only point inside it. No minimum count is needed to keep the flag's size at or below 0.075.

**Power, not size, is what small cells lack.** On development, every power-qualified M\* cell has ≥ 110 scenes (PD7) or ≥ 139 (SD1_7). Evaluable cells go down to 42–68 scenes, with power 0.07–0.34.

**Is 39 supported?** Not by a coverage or size criterion:
- the flag is conservative at any count ≥ 10;
- the upper bounds do not reach nominal even at 150.

**Recommendation.**
- **Keep 39**, re-justified as P01 Prop 6(ii)'s calibration-size result, with the development finding that the flag is conservative at any count ≥ 10 (so 39 is harmless for the flag).
- Do not cite it as making the bounds accurate.
- For the descriptive U_max (Choice 47f) and the cell upper bounds, either label them "approximate: development coverage 0.78 at 39 units and 0.87 at 150 near δ", or use a bound that handles all-zero samples (for example a bootstrap-t with an SE floor, or a beta-binomial bound on the pooled records with the design effect).
- HK1c at 375 units under-covers by about 3 points. Its +0.03 margin absorbs that, and should be stated.

## 4. Q4: verdict stability (and the comparator rules)

**How the sweep was run** (`c1crit_sweep_v01`, then `c1crit_summary_v01`; Table T5):
- The power rule was rerun for M\*, B0 and B3 on a ρ × P grid at the rule's settings (200 datasets, K8 seeds).
- Every other comparator is shown above δ by a cell flag in its all-evaluable family, which does not depend on ρ or P. This was asserted on every setting, and their families were held at the baseline.
- F_MIN, the HK1c margin and c were applied afterwards.
- The intervals of the ρ estimates (0.09–0.48 over estimators and populations) is bracketed by the grid's values 0.2, 0.3, 0.4 and 0.5.

**One at a time** (both trackers):

| Setting | T1 | T3 |
|---|---|---|
| ρ 0.2 / 0.3 / 0.4 / 0.5 / 0.7 (P 0.15) | no flip; M\* SD1_7 family 18 throughout | no flip; 19 / 18 / 18 / 18 / 17 |
| P 0.10 | **flips**: SD1_7 family 4 < 6, so Valid(M\*) and Forms A, B fail | holds (8) at 200 datasets; fails (5) at 1000 datasets and with target planting |
| P 0.125 / 0.20 | no flip (13 / 22) | no flip (13 / 22) |
| F_MIN 4 to 8 | no flip | no flip |
| HK1c 0.02 / 0.03 / 0.05 | no flip | no flip |
| c 0.02 / 0.03 / 0.05 | no flip | no flip |

**The (ρ, P, F_MIN) grid.** M\*'s SD1_7 family at F_MIN = 6 (200 datasets):

| ρ \ P | 0.10 (T1 / T3) | 0.125 | 0.15 | 0.20 |
|---|---|---|---|---|
| 0.2 | 12 / 12 | 18 / 17 | 18 / 19 | 23 / 22 |
| 0.3 | 11 / 10 | 18 / 18 | 18 / 18 | 22 / 22 |
| 0.4 | 7 / 9 | 16 / 15 | 18 / 18 | 22 / 22 |
| 0.5 | **4** / 8 | 13 / 13 | 18 / 18 | 22 / 22 |
| 0.7 | **3** / **3** | 12 / 13 | 18 / 17 | 20 / 21 |

The verdict flips only where the family falls below F_MIN, all at P = 0.10:
- T1 at ρ ≥ 0.5 (any F_MIN ≥ 5; ρ 0.7 at any F_MIN);
- T1 at ρ 0.4 with F_MIN = 8;
- T3 at ρ 0.7.

PD7's family never comes near the floor (≥ 17).

**The comparator rules.**
- **v07d against v07c** (D16 Choice 47e: ShownAbove without ¬HK1c). The sets are identical in every setting on both trackers. No comparator fails HK1c only: B3, and B0 on T3, pass HK1c, and the others are removed by cell flags.
- **H3's set, Choice 49c** (`k8_joint_analysis_v04`). No comparator fails only the pooled bound on the joint loss. V^J stays {B3} on T1 and {B0, B3} on T3.
- **The stricter familywise removal** (each condition at 1 − 0.05/9; `c1crit_fwcheck_v01`). V_t is the same (B3; B0, B3) and Form B holds, with bounds −0.730 (T1), and −0.575 and −0.684 (T3). Every other comparator is still removed by PD7 cell flags at 0.9944.

None of these rules changes any development verdict.

## 5. Q5: the effect size for power (and lead item 2)

**Flagged comparator cells** (exceedance of every comparator cell flagged in K8 v03; Table T9):
- **B4 and B6, all populations, both trackers**: 72 cells, median **0.158** [IQR 0.113, 0.184], 10th–90th percentile 0.092–0.240. PD7 only: 47 cells, median 0.145.
- **Every comparator shown above δ**: 116 cells, median 0.151. PD7 only: 0.125.
- **Per comparator, PD7:**

| Comparator | T1 | T3 |
|---|---|---|
| B6 | 0.143 (12 cells) | **0.113** (12 cells) |
| B4 | 0.134 (12 cells) | 0.230 (11 cells) |

- **B6 on SD1_7**: 0.163 (T1, 2 cells), **0.101** (T3, 2 cells).
- **All evaluable cells with E > δ** (not only the flagged ones): medians 0.11–0.14 for B4 and B6 on PD7.

**Smaller or larger than 0.15?**
- 0.15 is about the **median of all flagged B4 and B6 cells** (0.158), and of all flagged comparator cells (0.151).
- It is **larger than the typical failing exceedance of the comparator that decides Form B on T3**, B6, at 0.10–0.11.
- A target set at B6's typical failing exceedance (about 0.11) would therefore be **smaller than 0.15**.
- At 0.10 the development floor fails on T1 (and on T3 with more datasets). At 0.12 it passes on both trackers with margin: SD1_7 families 12–15 with all cells planted, and 10–14 target-only (Table T6).

## 6. Lead items 3 and 4: the power family under the alternative settings, and record coverage

**The grid** (`c1crit_power2_v01`; M\*; PD7 and SD1_7; 1000 datasets, 500 weights; Table T6), SD1_7 families, all cells / target only:

| | P 0.15 | P 0.12 | P 0.10 |
|---|---|---|---|
| T1, ρ 0.3 | 18 / 18 | 14 / 13 | 11 / 9 |
| T1, ρ 0.5 | 18 / 18 | 12 / 12 | 6 / **3** |
| T1, ρ 0.7 | 18 / 15 | 12 / 10 | **3** / **2** |
| T3, ρ 0.3 | 18 / 18 | 15 / 14 | 10 / 9 |
| T3, ρ 0.5 | 18 / 18 | 13 / 13 | **5** / **5** |
| T3, ρ 0.7 | 18 / 17 | 13 / 10 | **3** / **2** |

- PD7's families are 17–30 in every setting.
- Target-only planting matters only near the floor (P 0.10) or at ρ 0.7.

**Record coverage** (item 4; rule settings, 2000 datasets):
- M\*'s families cover **98.3–98.4 %** of SD1_7's relied records and **99.6–99.7 %** of PD7's.
- The k most powerful cells cover:

| k | 5 | 6 | 10 | 15 | 20 |
|---|---|---|---|---|---|
| PD7 | 0.61–0.62 | 0.66–0.67 | 0.83 | 0.92–0.93 | 0.97 |
| SD1_7 | 0.70–0.71 | 0.75–0.76 | 0.88 | 0.95–0.96 | 0.99 |

- At P 0.10 and ρ 0.5 (T1), the SD1_7 family of 6 covers 0.75.
- Moving-car cells hold 8.4–10.7 % of the records.
- M\*'s SD1_7 family contains 5 of the 6 moving-car cells on both trackers. It lacks `car|long|new`, with power 0.13 on T1 and 0.55 on T3 at 2000 datasets, from 56 and 110 scenes.

**Implication.** A coverage floor of s = 0.85–0.90 would pass on development (0.98) and could not be met by a 6-cell family alone (≤ 0.76). It is stricter than F_MIN = 6 where it matters: at P 0.10 a 6-cell family passes F_MIN but covers 0.75. The review's extra condition "contains every moving-car cell" **would fail M\* on development**; a version restricted to moving-car cells with at least about 150 scenes would pass.

## 7. Lead item 6: P(removal from V_t) for a comparator at δ

**Simulation** (`c1crit_removal_v01`; Table T7). Each comparator's own development counts were split into the four near/far × in-path quadrants, which were checked to add up exactly to PD7, SD1_7 and PD. Every cell was planted at exactly δ with beta-binomial ρ 0.3 or 0.5, and the nine removal conditions were applied with the comparator's development families and the K8 weights. 500 datasets were run per arm, tracker and ρ.

**Results:**
- **P(removed) at the rule's 0.95 per condition**: 0.094–0.142 over B0, B3, B4, B6 and M\*, both trackers and both ρ.
- **Where it comes from.** Each pooled lower-bound condition contributes 0.028–0.056, about nominal, because pooled cells have about 840 scenes. Cell and family flags contribute 0.000–0.024, being conservative.
- **At 1 − 0.05/9 per condition**: 0.002–0.018.
- **The same figure for M\*** is the chance that M\* exactly at δ is "shown above δ": 0.094–0.120.

**Implication.** Form B's false-pass bound under the rule is about α + 0.14. With familywise removal it is about α + 0.02, and that leaves the development verdict unchanged (§4).

## 8. Lead item 7: P(H1 fails | M\* marginally valid) at 375-log layouts

**Simulation** (`c1crit_oc375_v01`; Table T8). The synthetic sets are 375 development scenes drawn with replacement, each its own log, with every arm's counts and decision flags kept together. The rule is `c1_power_counts_v02.run_oc`: 200 bootstrap weights, the analytic power family and the v07d comparator rule. 300 sets per variant, so the MC SE of P(H1) is ≤ 0.017.

| Variant | P(H1) | P(H1 fails) | Main failure reasons |
|---|---|---|---|
| Plug-in development rates | 0.903 | 0.097 | T1: HK1c 0.030, pooled 0.027, family flag 0.023. T3: family flag 0.050, cell flag 0.030 |
| M\* capped at δ in every cell above δ (M\* marginally valid) | **0.980** | **0.020** | T1: HK1c 0.013, pooled 0.010 |
| Capped, analytic power at ρ 0.3 | 0.983 | 0.017 | T1: HK1c 0.010 |

- The floors never failed at 375 units: the SD1_7 family median is 11, with a 10th percentile of 9–10.
- **Not simulated:** new threshold fits per fold. Each development scene keeps its own cross-fitted fold fit. A refit simulation needs one decision-mode planner run per refit; the cost is in §9.

## 9. Lead item 8 (planner sensitivities): cost only, not run

**Cost.**
- The laptop K8 decision run took 20,700 CPU-s per tracker for 30 arms: 3,544 s wall with 6 workers (`70_TESTS/k8_expl_v02/run_record_t*_decide.json`). That is about 690 CPU-s per arm.
- A one-at-a-time sensitivity on the 7 Form B arms is about 4,800 CPU-s per tracker and setting.
- 10 settings × 2 trackers is about 27 CPU-h: about 9 h wall at 3 workers on an idle laptop. Today the laptop was at 100 % load from other jobs.

**Further obstacles.**
- `R_CONSIDER` (60 m) and `SCORE_MIN` (0.4) also define the K7 calibration items. Changing them needs the items rebuilt and the K7 fits refitted first.
- v_max (log maximum + 2 m/s) is an inline expression in `k8_sim_v02` (l. 663), so it needs a new sim version.
- `BUFFER`, `R_CONSIDER`, `SCORE_MIN` and the candidate tables `A1` and `T1` are module constants, which a new runner can set without editing files.

Items 1 to 7 were done first, as asked. Item 8 is left for the lead's decision.

## 10. Recommendations, in order of what they change

1. **Planted effect (C6a).** Keep 0.15 and write its anchor: the median exceedance of the comparator cells flagged on development, 0.158 for B4 and B6 and 0.151 over all comparators shown above δ. Report beside it the family at 0.12 (the lower quartile, 0.113) and the per-cell MDE80. **Do not adopt 0.10**: the development floor fails there. This is the only threshold whose change flips a development verdict.
2. **Monte Carlo (C6d).** 2000 datasets. Near the floor, 200 datasets decide the verdict by chance.
3. **Planting (C6f).** Target-only (individual power). This matches the paper's sentence and changes nothing at 0.15.
4. **V_t removal (C9c).** Familywise over the nine conditions (each at 1 − 0.05/9). On development P(removal at δ) falls from 0.09–0.14 to ≤ 0.02, and the verdict is unchanged. If this is not adopted, state Form B's level as about α + 0.14.
5. **ρ (C6c).** Keep 0.5, with the derivation in §1.
6. **Evaluable minimum (C5).** Keep 39, re-justified (§3). Label U_max and the cell upper bounds as approximate (coverage 0.78–0.87 near δ), or replace them by a zero-robust bound. State HK1c's 3-point under-coverage at 375 units.
7. **F_MIN (C7a).** Keep 6, or move to a records-coverage floor of 0.85–0.90. Do not require every moving-car cell.
8. **HK1c 0.03, c 0.03, B = 2000.** Keep.

## 11. Confidence (split)

- **Reproduction and the post-hoc sweeps** (F_MIN, HK1c, c, comparator rules): **high**. Every stored number was reproduced exactly; the rest is deterministic.
- **ρ:** **medium-high**. The fit checks are good and the intervals narrow. But the estimators disagree by about a factor of 2 (record-weighted against scene-unweighted). Per-cell values are noisy, and the moment estimator's bootstrap intervals are biased, so its point values are given without intervals. Transfer to AV2 rests on the design effect of about 1 and on the assumption that AV2's error dispersion resembles nuScenes'.
- **Monte Carlo findings:** **high**.
- **Coverage and size:** **medium-high**. They resample whole scenes of large development cells. Small or rare AV2 cells may be more zero-inflated, which makes the upper bounds worse. The family size simulation treats cells as independent.
- **Effect sizes:** **high** as numbers. **Which anchor to use is a judgement**: the median flagged cell against the decisive comparator.
- **P(removal) and P(H1 | M\* valid):** **medium**. Planting is parametric (beta-binomial) with fixed families. There are 300–500 sets each (MC SE ±0.015). The OC uses 200 weights and the analytic floor, and no threshold refits.

## 12. Files and hashes (SHA-256)

**Code** (`50_CODE/c1_criteria/`, new):

| File | SHA-256 |
|---|---|
| `c1crit_common_v01.py` | 627a433d84a6c095008cc527dbc737b5e0f3c8b79fff61b324b3ec8670c28cd4 |
| `c1crit_repro_v01.py` | 0494a1a4f709db91e1e27c7c95fc209ff68124d3c65a3e890c750a12d26d7105 |
| `c1crit_rho_v01.py` | d987bd92b613d65c25f9a9b92ef5d48d4d30218492ef59504a6fc47b6fe3ea54 |
| `c1crit_bbcheck_v01.py` | e61e08dbf1cad5b8b1a6b6ac3ae112a6e14c8525e65828f7572b18cdb8ac802c |
| `c1crit_mc_v01.py` | 1026716403f54808c8a77029c8d88249655688afdcee62138d0cfbea41fade1a |
| `c1crit_cover_v01.py` | d4247bec81a7b4e0bee0df98041f552ec285dfd0a5b1b01d7a74d4512ad3f5b3 |
| `c1crit_cover2_v01.py` | fe4c6697d4f9e16f45968bf09207628193fa96a983c59e739bc90b101a42389a |
| `c1crit_size_v01.py` | 7287d37770e03356937fa4b7bd3bba98d4ade6aed231f88263b541e321afbc69 |
| `c1crit_sweep_v01.py` | 9178c50dd5579fd42a7e445bf90016f9c72b49db7678ff04505bac6c890e648b |
| `c1crit_power2_v01.py` | ac5b7ecf581fb757faaf8af1bfda379e6d2d28c2005a16fd1b6038eb7672dfbc |
| `c1crit_removal_v01.py` | d8c366dc129600d1015d4aeea2dda2bec733531f48047d73dd620af6794e57f0 |
| `c1crit_oc375_v01.py` | 2a49e8d425e53f8d4af0fae26e8c99a83242246e7c4b5db2ccfe2fc7bc38ec08 |
| `c1crit_fwcheck_v01.py` | 0385d7231840fc2aafa92ace9d861795522f013f120ac037ce130fd8e62692be |
| `c1crit_summary_v01.py` | ff1946c5eabd3704fb1b15fb1261fff7653ee6b59c193028730c8d374ad50de1 |
| `c1crit_tables_v01.py` | c6eefae77a6af4fe2e7a1eafa9cd2d24ca7f483f20b6b5f3a355b21c7bbdf4ef |

**Outputs** (`60_RESULTS/c1_criteria_sensitivity_v01/`):

| File | SHA-256 |
|---|---|
| `repro_v01.json` | 3c316cd9cba50aadfff47571af75bba73083d160f6f43cfc7fedd8984a1d2df3 |
| `bbcheck_v01.json` | 73277136a69a313563e316e0d29b957044fcf000707106b348e8607ff067f651 |
| `fwcheck_v01.json` | d0408164d4ea809945a374f3c60e7f2151e2e8f28517d71de055823442b5bb04 |
| `c1crit_summary_v01.json` | 8574d6794596e0dc928daa819348e3817f3140cf662167d4e8ed2bbd03190171 |
| `C1_CRITERIA_SENSITIVITY_TABLES_v01.md` | 6893deb55111d1c61636b8308691883a87bb97ab9385b8ca2c97f4b1dc64a306 |
| `cache/dev_tables_t1_v01.npz` | b4f9c0f73ebc290fcb94e03d476c4c0d0a082993a8ec011c0dbe9f6bddee9b63 |
| `cache/dev_tables_t3_v01.npz` | 44cf90536fa9610a5d498af094dfc02756b21c0ccebde41e6d27955e7c957cf8 |
| `cache/dev_quadrants_t1_v01.npz` | 4fe81392711a22be07ea8ecd6bc58bdb01b281888733b3c0838d492c0099e6a1 |
| `cache/dev_quadrants_t3_v01.npz` | c1db56504459f2bd05973937e6aff5369ea1421f0b46464cf057412320bd9c79 |

**Checkpoints**, one JSON per unit with its seed: `rho_ckpt/` (16), `mc_ckpt/` (26), `cover_ckpt/` (16), `cover2_ckpt/` (14), `sweep_ckpt/` (40), `power2_ckpt/` (108), `size_ckpt/` (22), `removal_ckpt/` (20) and `oc375_ckpt/` (3). Run logs are in `logs/`.

**Every file** in both folders, this note included, is hashed in `SHA256SUMS_v01.txt` (same folder). Inputs read: the K8 v03 analysis JSON (ec85ce12…), the K8 Linux replicate's decision-mode run outputs, the K8 joint analysis JSON (264f7551…) and the evidence review (d24bfe63…).

**Seeds** (all recorded in the checkpoints):

| Use | Seed |
|---|---|
| K8 bootstrap | [20261106, i, 0] |
| K8 power | [20261107, i, …] |
| ρ CI bootstrap | [20261205, i, 1] |
| Coverage | [20261206, i, n] |
| q's MC SE | [20261207, i(, s)] |
| Pooled and Šidák coverage | [20261208, i, n, part] |
| Power grid | [20261209, i, k, s] |
| Size | [20261210, v, G] |
| Removal | [20261211, i, arm, ρ] |
| OC at 375 | [20261212, variant(, ρ)] |
| Alternative power seeds | 20261301–20261305 |
| Alternative bootstrap seeds | [20261106, i, 0, s] |
