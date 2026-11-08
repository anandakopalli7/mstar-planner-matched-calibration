# C1 criteria register (v05, 6 Nov 2026, 03:40 EST)

v05 = v04 with R20's re-check v03 points applied (D16 v37 Choice 56): every operating figure is labelled with its check (v02 at Choice 50's levels, v03 at the final levels); C3b's p-value statement is narrowed; Form B's smallest tail count is stated; and a limit on H1's actual error is added. No value changes. v01 to v04 are kept.

**What this is.** The decided value, basis and confidence of every pass/fail criterion of the C1 confirmation, after the two-part audit the researcher asked for on 5 Nov:
- the literature half, `90_DECISIONS/C1_CRITERIA_EVIDENCE_REVIEW_v01.md` (d24bfe63…), 46 rows;
- the development half on nuScenes, `60_RESULTS/c1_criteria_sensitivity_v01/C1_CRITERIA_SENSITIVITY_NOTE_v01.md` (a0e1e223…) and the final rule-set check `60_RESULTS/c1_criteria_sensitivity_v02/C1_CRITERIA_FINAL_CHECK_NOTE_v02.md` (2e69fae6…), and the check of the final levels `60_RESULTS/c1_criteria_sensitivity_v03/C1_CRITERIA_RULESET2_CHECK_NOTE_v03.md` (6867dc22…).

The decisions are recorded in D16 v37, Choices 50 to 56 (`90_DECISIONS/D16_DELEGATED_CHOICES_v37.md`, 4cf3893a…). No Argoverse 2 outcome was seen; every number below is nuScenes development evidence, a closed-form result, or a published source.

**Classes.** PROVEN = follows from a theorem. STANDARD = a published standard or regulatory guideline (ICH, FDA, NIST). PRACTICE = established practice in the peer-reviewed literature. DEV = derived from or checked on our nuScenes development data. OWN = our judgement; for every OWN row the register states whether the development verdict changes across its plausible range.

**Software checks are not scientific criteria.** Hash equality, byte identity and refusal tests (C16a–c, A7) verify the software; they are listed for completeness.

## 1. Summary

| Confidence after the audit | Rows | IDs |
|---|---|---|
| high | 26 | C1, C2, C3a, C3b, C3c, C4, C6b, C6d, C6e, C6f, C9a, C9b, C9c, C11a, C11b, C12a, C12b, C14, C15b, C15g, C16a, C16b, C16c, A1, A2, A7 |
| medium-high | 3 | C5, C6c, C8 |
| medium | 17 | C6a, C7a, C7b, C10a, C10b, C12c, C13a, C13b, C15a, C15c, C15d, C15e, C15f, C15h, A3, A4, A6 |

**No criterion remains at low confidence.** Before the audit 8 rows were low: C6a, C6c, C6d, C6f, C7a, C10a, C10b, C13b.

**Rows that rest wholly or partly on own judgement (17), and whether the development verdict depends on them:**

- C3b: no
- C5: no (the flag is valid at any count ≥ 10)
- C7a: no, over 4–8 on development and at 375 logs
- C7b: no
- C8: no on development (M\*'s largest pooled UB is 0.062, against 0.08). At 375 units L = 0.995 costs power: P(H1 fails \| M\* valid) rises from 0.020 to 0.060 (check v02, at Choice 50's levels; 0.067 at the final levels, check v03)
- C10a: no: 0.02–0.05 changes nothing; secondary
- C10b: no; secondary
- C12b: no
- C12c: not for M\*'s validity
- C13b: none: H9 is descriptive and never entered GO
- C15c: descriptive development sensitivity (0.25 / 1.0 m) scheduled; cannot change the frozen setting
- C15d: as C15c
- C15e: as C15c (denser set)
- C15f: reported
- A3: reported
- A6: secondary
- A7: software/process rule

**The governing principle for error levels** (new; ICH E9 §5.5):
- evidence **against** M\* (its flags) is judged at one-sided 0.05, the strict direction for M\*;
- every bound or flag whose passing **supports** a claim in M\*'s favour is judged at one-sided 0.025, which equals the conventional two-sided 95 %. The exception is HK1c: its level is calibrated (L = 0.995) so that its development coverage meets Bradley's liberal limit for 0.025, which allows an actual error of up to 0.0375 (row C8);
- the 0.025 of a claim in M\*'s favour covers the choice of the comparators it must beat as well as the test against them. For H1, removal uses 0.0125 over its 9 conditions and superiority 0.0125, so H1's false-pass probability is at most 0.025 at nominal levels (Bonferroni over selection and test). Inside Holm's family S, H3's and H4's selection uses 0.0025 and their p-values are doubled (row C9c). On development, the paired bound's actual error was up to 0.032 at nominal 0.025 (T1, B3, check v02), within Bradley's band.

## 2. Register

| ID | Criterion: decided value | Change | Basis (source; development evidence) | Class | Confidence before → after | Does the development verdict depend on it? |
|---|---|---|---|---|---|---|
| C1 | δ = 0.05 per-constraint exceedance level | none | Blackmore, Ono and Williams 2011 (per-constraint structure); 0.05 targets in the CRC planning literature; CRC needs n ≥ 1/δ − 1 (Angelopoulos et al. 2024, Thm 1). The paper calls δ a calibration level, not a safety target (ISO 21448 residual-risk rates are far smaller) | PRACTICE | high → high | not varied (it defines the study) |
| C2 | Flags against M\*: one-sided 0.05, simultaneous sup-t over a population's cells; populations uncorrected | none | Montiel Olea and Plagborg-Møller 2019; Hothorn, Bretz and Westfall 2008; ICH E9 §5.5. A flag is evidence against M\*, so 0.05 is the strict direction. Development: actual size at a true δ 0.004–0.026 for one cell, ≤ 0.003 per family, at 10–150 units (below Bradley's 0.075) | STANDARD + DEV | high → high | no |
| C3a | The log is the bootstrap unit | none | Davison and Hinkley 1997 §3.8; Field and Welsh 2007; Abadie et al. 2023. Development design effect of scenes within a nuScenes log 0.94–1.15, so a scene is the right analogue of an AV2 log | PRACTICE + DEV | high → high | no |
| C3b | B = 40,000 bootstrap draws; every Monte Carlo p-value is (k + 1)/(B + 1) | **2000 → 40,000; k/B → (k + 1)/(B + 1)** (Choices 52d, 53c, 53d) | Our rule: every decision quantile has at least 10 replicates beyond it. The most extreme, H4's removal at 0.0025/9, needs B ≥ 36,000; Form B's tail holds at least 71 replicates for up to 7 kept comparators (Andrews and Buchinsky 2000 treat B as a Monte Carlo accuracy choice). The (k + 1)/(B + 1) Monte Carlo p-value is never 0 and is conservative for the Monte Carlo step at any B; the bootstrap p-value itself is valid only approximately (Davison and Hinkley 1997, ch. 4; Phipson and Smyth 2010). Development, check v03 at B = 20,000: V_t and V^J identical in 100 of 100 seed sets, decisive MC SE ≤ 0.0006. At B = 2000 (check v02) Form B's MC SE was 0.0008–0.0012, 473–880 MC SEs from 0; R21 reports it at B = 40,000 from 20 seed sets (Choice 53e). Cost: about +9 min per 375-log table, peak 4.9 GB | OWN (B rule) + PRACTICE + DEV | medium → high | no |
| C3c | Percentile log-bootstrap bounds for paired operability | none | Efron and Tibshirani 1993; Cameron, Gelbach and Miller 2008 (their few-cluster warning does not apply at 375 logs). Development coverage at 375 units: 0.968–0.983 at 0.975 and 0.982–0.993 at 0.9875 for every Form B, Form C and H10 contrast, all at or above Bradley's lower limit of 0.9625 at α = 0.025 (coverage above nominal is conservative). Three bounds are slightly below nominal: B3 at 0.975 (0.9678 T1, 0.9725 T3) and at 0.9875 (0.9835 T1, 0.9815 T3), and B0 on T3 at 0.975 (0.9728) | PRACTICE + DEV | high → high | no |
| C4 | n_min = 19 calibration units per stratum | none | Angelopoulos et al. 2024, Thm 1: a finite threshold needs 1/(n + 1) ≤ δ | PROVEN | high → high | no |
| C5 | A cell is evaluable at ≥ 39 logs | none; re-justified | Origin: P01 Prop 6(ii), a calibration-size result (n = 2/δ − 1); no coverage or size criterion derives it. Development: the flag is conservative at every count from 10 to 150 units (size 0.004–0.026), so 39 does not inflate false flags; it is **not** a coverage claim for upper bounds | OWN (value) + DEV (flag safety) | medium → medium-high | no (the flag is valid at any count ≥ 10) |
| C6a | Power rule: planted effect 0.15 | none; anchored | ICH E9 §3.5 (the effect for power is the smallest effect that matters or the anticipated effect). Anchor: the median exceedance of the comparator cells flagged on development, 0.151 (116 cells; 0.158 for B4 and B6). Caveat: flagged cells are selected for size; over all evaluable cells of B4 and B6 above δ on PD7 the medians are 0.11–0.14. So the family at 0.12 is reported beside it, and per-cell power at 0.10, 0.12, 0.20 | STANDARD framing + DEV | low → medium | **yes.** On the 840 scenes, at 0.10 only: M\*'s SD1_7 floor fails on T1 (and on T3 with more datasets); at 0.12 and above both trackers pass. At 375 units the SD1_7 floor fails in every development set at 0.12 (family median 3, against 11 at 0.15), so the study is powered for per-cell excesses of about 0.15. Both are stated as limits |
| C6b | Power ≥ 0.80 | none | ICH E9 §3.5 (type II error conventionally 10–20 %); Cohen 1988 | STANDARD | high → high | no |
| C6c | Beta-binomial intra-log correlation ρ = 0.5 | none; derived | Estimated on development (Ridout, Demétrio and Firth 1999 ANOVA ICC; beta-binomial ML; fit checked, variance ratio 1.01–1.23): pooled 0.10–0.31 (PD7), 0.22–0.45 (SD1_7), 0.21–0.53 (PD) across estimators; per-cell medians 0.42–0.48 at exceedances of 0.10–0.20, with a 90th percentile of 0.67–0.71 (so 0.5 is not conservative for every single cell). 0.5 is at or above the upper 80 % limit of every pooled ANOVA ICC on PD7 and SD1_7 for M\*, B4 and B6 (largest 0.341; the scene-unweighted moment estimate reaches 0.448, B6 on T1 SD1_7), the conservative planning value of Browne 1995 and Turner, Prevost and Thompson 2004; Donner and Klar 2000 | DEV + PRACTICE | low → medium-high | no: ρ 0.2–0.7 at P ≥ 0.125 changes nothing |
| C6d | 2000 simulated datasets | **200 → 2000** | Morris, White and Crowther 2019 (choose repetitions for a target MC SE): SE at power 0.8 falls from 0.028 to 0.009; a cell at true power 0.78 qualifies with probability ≈ 0.02 instead of ≈ 0.28 | PRACTICE | low → high | no at 0.15; near the floor (P 0.10) 200 datasets decided by chance |
| C6e | The power rule's first 500 bootstrap weight rows (a prefix that does not depend on B) | wording (B is now 40,000) | Development: 500 and 2000 weights give identical families on both trackers | DEV | medium → high | no |
| C6f | Target-only planting; the other evaluable cells at exactly δ | **all cells at 0.15 → target only, others at δ** | Senn and Bretz 2007 (individual power is the quantity the sentence "power 0.8 against 0.15" states). Others at δ keeps the rule outcome-free (no observed exceedance enters). Development: M\*'s families are 27 / 18 / 5 (T1) and 26 / 18 / 5 (T3), covering 99.7 / 98.3 % and 99.4 / 98.4 % of PD7 / SD1_7 records; the analytic family used in the OC equals the simulated one in all six combinations | PRACTICE | low → high | no at 0.15 |
| C7a | F_MIN = 6 power-qualified cells on PD7 and SD1_7 | none; record coverage now reported | No source sets a minimum count of powered strata. Development: F_MIN 4–8 changes nothing (families 18 and 27–28; coverage 98–99.7 % of records). At 375 logs the floor never failed (SD1_7 family median 11, 10th percentile 9–10; P(family ≥ 6) = 1.00 at P 0.15). Two alternatives were rejected: a coverage floor (its share is equally a judgement, and its 375-log behaviour is untested) and "every moving-car cell" (M\* fails it on development through one 56-scene cell with power 0.13) | OWN | low → medium | no, over 4–8 on development and at 375 logs |
| C7b | PD: ≥ 1 evaluable cell, no flag in its power-qualified family | none; wording | The paper states that PD validity is claimed for its power-qualified cells only | OWN | medium → medium | no |
| C8 | HK1c: pooled one-sided UB at level L ≤ δ + 0.03, L = 0.995 | **level 0.95 → 0.995**; margin kept | Margin: a correctly calibrated rule's fitted risk is Beta(l, n + 1 − l) (Vovk 2012; Angelopoulos and Bates §3.2); at n = 300 this is Beta(15, 286), and δ + 0.03 is its 98.4th percentile; for C1's fraction losses, stratified thresholds and fallback strata the law is an approximation. Level: the 0.95 bootstrap bound covered only 0.915–0.920 near δ at 375 units when pooled (0.898–0.934 by population and tracker; below Bradley's band); L is the smallest level whose development coverage is ≥ 0.9625 in every population (Loh 1987, calibrating confidence coefficients). At B = 20,000 M\*'s own coverage at 0.995 is 0.966–0.992 (check v03, A3). Mean coverage over cells with truth in [0.02, 0.10) at 375 units: 0.930–0.961 at 0.975, 0.955–0.980 at 0.99, 0.967–0.988 at 0.995, so L = 0.995 (the fallback agrees; worst single cell 0.949). With truth exactly at the 0.08 boundary, 0.99 would suffice. The rule was stated in the lead's request at 13:37 EST, before the check ran, and is applied as stated; it left open whether coverage meant the mean or the per-cell minimum, and both give 0.995. HK1c is the part of the validity claim that shows M\*'s pooled risk is *not far above* δ, which answers Schuirmann's critique of a non-rejection claim | OWN (margin value, with an approximate derivation) + PRACTICE + DEV (level) | medium → medium-high (mean coverage at or above Bradley's lower limit of 0.9625; worst single development cell 0.949; the Beta-law margin is approximate for fraction losses) | no on development (M\*'s largest pooled UB is 0.062, against 0.08). At 375 units L = 0.995 costs power: P(H1 fails \| M\* valid) rises from 0.020 to 0.060 (check v02, at Choice 50's levels; 0.067 at the final levels, check v03) |
| C9a | H1 as an intersection-union test over trackers and conditions | none | Berger 1982; Berger and Hsu 1996 | PROVEN | high → high | no |
| C9b | Form B superiority: UB^{1 − 0.0125/\|V_t\|}(Δ) < 0 (H1); on H4's route at 1 − 0.025/(2\|V_t\|), its p doubled | **0.05 → 0.0125** (Choices 50, 52c, 53b) | ICH E9 §5.5: the claim in M\*'s favour totals one-sided 0.025, split by Bonferroni between the selection of the comparators (0.0125) and superiority over them (0.0125); Bonferroni across V_t | STANDARD + PROVEN (Bonferroni) | high → high | no: development bounds −0.72 (T1), −0.57 and −0.68 (T3) |
| C9c | A comparator leaves V_t only if one of its 9 removal conditions holds at 1 − 0.0125/9 (H1); at 1 − 0.0025/9 on H4's route; V^J's 3 conditions at 1 − 0.0025/3 (H3) | **0.95 each → 0.0125/9 (H1), 0.0025/9 (H4), 0.0025/3 (H3)** (Choices 50, 52c, 53b) | Berger's IUT level assumes fixed components; with a data-selected V_t, P(false Form B) ≤ α_selection + α_superiority (Benjamini and Yekutieli 2005; Bonferroni), so H1 totals 0.0125 + 0.0125 = 0.025 at nominal levels. Inside Holm, H3's and H4's selection uses half the smallest Holm level (0.0025) and their p is doubled, so P(p ≤ α) ≤ 0.0025 + α/2 ≤ α for every Holm level α ≥ 0.005. Development: a comparator at δ was removed with probability 0.09–0.14 under the old rule and ≤ 0.018 at 0.05/9 | PROVEN (Bonferroni) + DEV | medium → high | no: V_t and V^J unchanged under the final levels ({B3} on T1, {B0, B3} on T3 (check v03); every other comparator is removed by a cell flag at 1 − 0.0125/9, the weakest at t − q = 3.3) |
| C10a | Form C ceiling c = 0.03 (H2), UB^{0.975} | level 0.95 → 0.975 | Non-inferiority convention: the margin is pre-specified and tested at one-sided 0.025 (ICH E9 §3.3.2, §5.5; ICH E10; FDA 2016). c = 0.03 is about 15 % of B4's development infeasible rate (0.198 T1, 0.208 T3) | OWN (value) + STANDARD (level) | low → medium | no: 0.02–0.05 changes nothing; secondary |
| C10b | H10: M\*'s infeasible rate ≤ B6's + 0.03, UB^{0.975} | level 0.95 → 0.975 | As C10a. Development upper limits of M\* − B6: −0.043 (T1), +0.005 (T3) | OWN + STANDARD | low → medium | no; secondary |
| C11a | Holm, m = 5, family S gated on H1, at one-sided 0.025; within S the Monte Carlo p-value decides and the bound at the Holm level is reported; H3's and H4's p doubled | **0.05 → 0.025; one decision form per hypothesis** (Choices 50, 52c, 52e, 53b) | Holm 1979; Dmitrienko and Tamhane 2007 (*Pharm. Stat.*); ICH E9 §5.6. Holm needs p-values, so the p decides; H3 and H4 as in C9c | STANDARD | high → high | no |
| C11b | Family P = {H8} at its own level, not gated | none; reason added | ICH E9 §5.6 (explain why no adjustment): H8 replicates a premise about B0, not a claim about M\*. X2's two-sided 95 % band is one-sided 0.025. Study-wise: {H1 → S} by serial gatekeeping (H1 at 0.025; S under Holm at 0.025 only if H1 holds) controls its error at one-sided 0.025 nominal (Dmitrienko and Tamhane 2007); with P at its own 0.025, every confirmatory statement together is at most 0.05 nominal | PRACTICE | medium → high | no |
| C12a | H8 FAILS: LB > max(δ, E⁰_r) and truth-oriented LB > δ | text fix | X1 v02 (false FAILS ≤ 0.025 + 2 MC SE). The band is two-sided 95 % (`x1_lib_v03.sup_t_band`), not "95 % sup-t" | DEV | high → high | no |
| C12b | E⁰: 20 perturbation draws per item | none; MC SE reported | Morris et al. 2019; the MC SE is ≈ 0.0015, far below the band's width | OWN (value) + PRACTICE (MC SE reported) | high → high | no |
| C12c | σ_a = 0.10 m annotation floor | none | No published AV2 value; CRC validity holds for any fixed σ_a (P02 PM1), so M\*'s certificate does not depend on it. X2's 0.20 m condition carried as a descriptive H8 check | OWN | medium → medium | not for M\*'s validity |
| C13a | H9 history-length strata {2, 3–4, ≥ 5} (H9 is descriptive) | none; disclosed | Monti et al. 2022; category-conditional calibration (Vovk 2012). Cut-points chosen after D17 outcomes; AV2 is new data | DEV | medium → medium | none: H9 is descriptive (Choice 52b) |
| C13b | H9's floor of ≥ 6 power-qualified E2 cells, reported; H9 is descriptive | **H9 secondary → descriptive** (Choice 52b) | The outcome-free projection (AV2 validation counts resampled to 375 logs, 20 draws) gives 2 of 6 cells in every draw, P(≥ 6) = 0, although it overstates power; a test that cannot meet its own floor cannot support a confirmatory claim (ICH E9 §3.5). The floor's value follows C7a | OWN (floor) + STANDARD (designation) + DEV | low → medium | none: H9 is descriptive and never entered GO |
| C14 | Folds: 5 random folds of 75 logs | none; §6.8 reworded | Split CRC per fold, so PM1 applies per fold (Angelopoulos et al. 2024); Vovk 2015 and Barber et al. 2021 cited as practice only | PRACTICE | high → high | no |
| C15a | Planner: constraints enforced to 2 s | none | D09 v04: at 4 s every margin arm was infeasible in 51–81 % of development frames | DEV | medium → medium | descriptive sensitivity scheduled |
| C15b | Checks every 0.25 s | none | Geometric sampling argument (20 m/s × 0.25 s = 5 m) | DEV | high → high | no |
| C15c | 0.5 m buffer | none | No source for the value; arm-invariant (it enters every arm equally) | OWN | medium → medium | descriptive development sensitivity (0.25 / 1.0 m) scheduled; cannot change the frozen setting |
| C15d | 60 m consideration range | none | Closing distance at 2 s ≈ (15 + 15) m/s × 2 s = 60 m. Outcome-free share of relied constraints at 50–60 m reported | OWN | medium → medium | as C15c |
| C15e | 32 candidates + e-stop | none | Sampled candidate sets are standard (Werling et al. 2010); values own | OWN | medium → medium | as C15c (denser set) |
| C15f | v_max = log maximum + 2 m/s | none | A replay device shared by every arm; how often it binds is reported | OWN | medium → medium | reported |
| C15g | Back-off ladder λ ∈ {0.75, 0.5, 0.25, 0} | none | D09 v05 (0 non-monotone collision cases against 16 with an immediate e-stop) | DEV | high → high | no |
| C15h | Recorded tracks at score ≥ 0.4 | none | D09 v02 (nuScenes pairing rate by score bin); the AV2 pairing rate is a Rule-0 descriptive after the lock | DEV | medium → medium | not re-tuned |
| C16a | SHA-256 equality for binding | none | NIST FIPS 180-4 | STANDARD | high → high | software check |
| C16b | Port acceptance: byte-identical outputs | none | Strictest equivalence | PRACTICE | high → high | software check |
| C16c | HOTA equivalence at rtol 1e-12 | none | IEEE 754 binary64 rounding (Higham 2002); HOTA is never gated | PRACTICE | high → high | software check |
| A1 | Estimand: log-level mean of each log's rate | none | P01 Thm 5 / P02 PM1 bound the expected loss of a test unit (unit-weighted) | PROVEN | high → high | no |
| A2 | M\*'s validity: no flag in the all-evaluable family, power family and pooled cell, uncorrected | none | A correction would make a non-rejection claim easier; IUT logic (Berger 1982). P(H1 fails \| M\* marginally valid) at 375 logs: 0.067 at the final levels (capped, P(H1) 0.933; plug-in P(H1) 0.870; check v03), against 0.020 at v07d's levels | PRACTICE + DEV | high → high | no |
| A3 | Zero SE or non-finite quantile judged by Ê > δ | none; every case reported | Conservative for M\*; for a comparator it removes on a point estimate, so each case and its effect on V_t is reported | OWN | medium → medium | reported |
| A4 | RETUNED: least conservative point of the merged α/δ′ curve meeting pooled validity | none | Parallel-ε planners (Mustafa et al. 2023), α-sweeps (Shah et al. 2026) | PRACTICE | medium → medium | reported per fold |
| A6 | Method stage: 20 repetitions of a 5-fold split | none; MC SE reported | Repeated cross-validation practice | OWN | medium → medium | secondary |
| A7 | Any missing or unverifiable H1 input gives NO-GO | none | Pre-specified, conservative | OWN | high → high | software/process rule |

## 3. What changed, in one place

1. **Error levels follow ICH E9 §5.5** (Choices 50, 52, 53).
   - Evidence against M\* stays at one-sided 0.05.
   - Each claim in M\*'s favour totals one-sided 0.025:
     - H1: comparator removal at 1 − 0.0125/9 per condition and Form B at 1 − 0.0125/|V_t| (was 0.05/|V_t|);
     - H3: V^J removal at 1 − 0.0025/3 and its p doubled; H4: removal at 1 − 0.0025/9 on its route and its p doubled;
     - Form C, H10's NI part, and the cell parts of H6b and H10: 0.95 → 0.975;
     - Holm over family S: 0.05 → 0.025, the p-value deciding;
     - Form A (descriptive): 0.05/4 → 0.025/4.
2. **HK1c level:** 0.95 → 0.995, also for ValidJ. The margin δ + 0.03 is unchanged.
3. **Bootstrap and p-values:** B 2000 → 40,000; every Monte Carlo p-value (k + 1)/(B + 1).
4. **Power rule:** 200 → 2000 simulated datasets; all-cells planting → target-only planting with the other cells at δ.
5. **H9:** secondary → descriptive (its floor is projected not to be met).
6. **New descriptive outputs:**
   - record coverage of each power family;
   - families at F_MIN 4 and 8;
   - per-cell power at P 0.10, 0.12 and 0.20 (MDE80);
   - zero-SE cases;
   - U_max and cell UBs labelled approximate;
   - the MC SE of the decisive bounds and the seed stability of V_t and V^J (R21).
7. **Wording:**
   - H8's band is two-sided 95 %;
   - PD validity is claimed for power-qualified cells only;
   - the §6.8 fixes of section 4.
8. **Kept, with new derivations or development checks:**
   - P = 0.15 (development anchor);
   - ρ = 0.5 (development ICCs and the upper-limit planning practice);
   - MIN_UNITS = 39 (an own value from P01 Prop 6(ii); the development check shows the flag is conservative at 10–150 units);
   - F_MIN = 6 (an own value; the verdict is unchanged over 4–8).
9. **Planner sensitivities** (buffer, candidate density, range): descriptive, after the lock-critical work. They cannot change a frozen setting.

The development verdict under the final levels is unchanged on both trackers (check v03, part C).

## 4. Citation corrections for the plan's source table (§6.8) and the manuscript

**Fixes to existing entries:**
1. **Dmitrienko and Tamhane 2007.** "Gatekeeping procedures with clinical trial applications" is in *Pharmaceutical Statistics* 6(3):171–180, doi 10.1002/pst.291, not *Stat. Med.*
2. **Schuirmann 1987.** Cite him as the reason U_max is reported and no equivalence is claimed. He is not a source for "not shown above δ", which inverts his conclusion.
3. **Lindemann et al., RA-L 2023.** They set each step's level to δ/T so that the whole trajectory holds at 1 − δ. Cite them for that contrast with C1's per-constraint allocation, and point to H3.
4. **Vovk 2015 and Barber et al. 2021.** Cite them as practice only. C1's folds are split CRC per fold, whose exact guarantee is PM1.
5. **Cameron, Gelbach and Miller 2008.** Add that they favour bootstrap-t with few clusters. The flags are studentised, and the paired percentile bounds use 375 logs.
6. **Donner and Klar 2000.** Cite them for the design-effect concept only. ρ's value comes from the development ICCs (Ridout et al. 1999) and the upper-limit practice (Browne 1995; Turner et al. 2004).
7. **The origin of 39.** Add P01 Prop 6(ii), a calibration-size result.
8. **Ding et al. 2023.** Call it the "nearest pooling scheme".
9. **Lee, Barber and Willett.** Cite as arXiv 2306.06342.
10. **Added in v04:** Davison, A. C., Hinkley, D. V. (1997). *Bootstrap Methods and Their Application*, ch. 4 (Monte Carlo p-values); Phipson, B., Smyth, G. K. (2010). Permutation p-values should never be zero: calculating exact p-values when permutations are randomly drawn. *Statistical Applications in Genetics and Molecular Biology* 9(1), Article 39, doi:10.2202/1544-6115.1585 (bibliographic check only).

**Sources to add** (full entries in the evidence review's section 7, unless given here):
- ICH E9 §3.3.2, §3.5, §5.5 and §5.6; ICH E9(R1); ICH E10; FDA 2016 (non-inferiority);
- Morris, White and Crowther 2019; Andrews and Buchinsky 2000;
- Senn and Bretz 2007;
- Vovk 2012 and Angelopoulos and Bates (arXiv 2107.07511 §3.2);
- Bradley 1978; Ridout, Demétrio and Firth 1999;
- Benjamini and Yekutieli 2005 (now also for removal from V_t);
- Cameron and Miller 2015; Monti et al. 2022; NIST FIPS 180-4;
- Loh, W.-Y. (1987). Calibrating confidence coefficients. *JASA* 82(397):155–162. doi:10.1080/01621459.1987.10478400 (checked at abstract level, 5 Nov);
- Browne, R. H. (1995). On the use of a pilot sample for sample size determination. *Statistics in Medicine* 14(17):1933–1940. doi:10.1002/sim.4780141709 (checked at abstract level, 5 Nov);
- Turner, R. M., Prevost, A. T., Thompson, S. G. (2004). Allowing for imprecision of the intracluster correlation coefficient in the design of cluster randomized trials. *Statistics in Medicine* 23(8):1195–1214. doi:10.1002/sim.1721 (checked at abstract level, 5 Nov).

## 5. Limits stated in the paper

1. **The detectable effect.**
   - Per-cell power is 0.80 against an excess of 0.15. The anchor comes from flagged, hence size-selected, comparator cells.
   - On the 840 development scenes the SD1_7 floor fails at 0.10.
   - At 375 units with development record counts it fails at 0.12.
   - Validity is therefore claimed against per-cell excesses of about 0.15 and above, not smaller ones. MDE80 is reported per cell.
2. **HK1c's coverage is approximate.**
   - At L = 0.995 the development mean is 0.967–0.988, and the worst single cell is 0.949.
   - The Beta-law margin is exact for split conformal with indicator losses. For C1's fraction losses and fallback strata it is an approximation.
3. **U_max and the cell UBs are approximate.** Development coverage near δ is 0.78 at 39 units and 0.87 at 150.
4. **Three paired bounds under-cover slightly:**
   - B3 at 0.975: 0.9678 (T1) and 0.9725 (T3);
   - B3 at 0.9875: 0.9835 (T1) and 0.9815 (T3);
   - B0 on T3 at 0.975: 0.9728.

   All are above Bradley's lower limit of 0.9625, and every Form B bound is far from 0: −0.725 on T1, −0.571 and −0.680 on T3 (check v02, at Choice 50's levels); −0.722, −0.566 and −0.677 at the final levels (check v03).
5. **Own-judgement values remain:**
   - F_MIN 6 and PD ≥ 1;
   - MIN_UNITS 39 (C5);
   - HK1c's margin of 0.03 (C8);
   - c = 0.03 for Form C and H10 (C10a, C10b);
   - H9's floor (C13b);
   - E⁰'s 20 draws (C12b);
   - σ_a 0.10 m;
   - the planner's buffer, range, candidates and v_max;
   - A3's zero-SE rule, A6's repetitions and A7.

   Over its plausible range, none of them changes the development verdict, or the value cannot affect GO. The planner sensitivities are descriptive.
6. **All development evidence is nuScenes.**
   - AV2's record counts, zero inflation and within-log correlation may differ.
   - The counts (S20a, S22) are computed from AV2 inputs before stage B, without outcomes, and the frozen rules apply to them as written.
7. **The grades are judgement.** Confidence grades are a judgement about a referee, not a measurement.
8. **Some sources were checked only partly.**
   - Some were checked bibliographically or at abstract level only.
   - FDA 2016's text was not opened.
   - Bradley's band comes from secondary sources.
   - The clauses of ISO 21448 and ICH E10 were not read in the primary documents.
9. **H9 is descriptive.** Its floor is projected not to be met at 375 logs, so the study makes no confirmatory claim about a learned predictor.
10. **H6b's resolution.** The method stage's 200 refits give a smallest p of 1/201 ≈ 0.004975. H6b can pass at Holm's smallest level only with no refit on the null side; this costs power, not validity.
11. **H3 and H4 have no development replay.** Development has no M\*J or transfer arm, so their rules are tested on constructed cases and in the rehearsal.
12. **H1's actual error.** Its selection-and-superiority part is 0.025 nominal. Its HK1c part is a separate component of the intersection-union test; at L = 0.995 its development coverage is 0.967–0.988 on population means (actual error 0.012–0.033) and 0.949 in the worst single cell (about 0.05). Where HK1c's null holds, H1's actual error can therefore exceed 0.025.
