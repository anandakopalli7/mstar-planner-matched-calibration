# C1 reporting frames v03: the paper's wording for every outcome, fixed before the decision exists (7 Nov 2026)

**Status.**
- **v03 (7 Nov 2026, EST) = v02 (kept, d1b57da5…) plus §6, the abstract's exact text.** Written by the lead while line 67 (the analysis) was running and before any C1 decision or analysis file existed, without opening any C1 outcome. Why: the LaTeX conversion of draft v04b showed that v04b's abstract (248 words) predates these frames, and that v02's GO sentence (§3) is about 77 words against its own 65-word budget, so the assembled abstract could exceed IEEE Access's 250-word limit. §6 fixes S1–S4 and S6 word for word, a shorter S5 for every branch, and a mechanical overflow rule. The longer v02 sentences of §3 and §4 stay as the lead sentences of Section V-F7. No rule, level or claim of the frozen plan changes; §1's branch rule is unchanged.
- **When and how written.** Written by the lead on 6 Nov 2026 (EST), before any C1 decision or analysis file existed and without opening any C1 outcome.
- **What it supersedes.** It supersedes v01 (`20_DESIGN/C1_REPORTING_FRAMES_v01.md`, c46e301b…, kept). v02 answers the referee re-read of manuscript v04: mixed-tracker branches; an unevaluable pooled cell; no verdict of record; a results-review disagreement; GO with an empty or zero-SE-dependent comparison set; H8 in the abstract either way; "no evaluable cell"; the abstract word budget; and the plan's "Not claimed" list.
- **Its hash.** The SHA-256 of v02 is recorded in `90_DECISIONS/D16_DELEGATED_CHOICES_v51.md` before the analysis (line 67 of `40_PROTOCOL/C1_RUN_COMMANDS_v01.txt`) runs.
- **Its scope.** It changes no rule, level or claim of the frozen plan. It fixes only the manuscript's wording, so that the framing is chosen by the decision file's fields and not by the outcome's appeal.
- **The tool.** `80_LOGS/c1_manuscript_v01/make_c1_results_v02.py` applies §1 mechanically.

## 1. How the branch is chosen (mechanical, per tracker)

**What is read.** Read from the decision of record (plan §9) its `C1_verdict`, `nogo_reasons` (equal to `failed_conditions`), `missing_inputs`, the H1 block per tracker (`V`, `n_V`, `comparator_reasons`, Form B bounds) and `zero_se_effects`. `hypotheses.H1.wording_by_tracker` is **not** used: it labels an HK1c-only failure "floor not met".

For each tracker t, set these flags from the verbatim reason strings of the frozen code (`c1_analyse_v06` l. 79–112, reached by v10 through v07):

| Flag | Set when a reason for t reads … |
|---|---|
| **E_t** (procedural) | a `missing_inputs` entry starting "H1 t"; "arms missing from the run"; "comparators missing" |
| **A_t** (M\* shown above δ) | "M\* NoFlag fails"; "M\*'s pooled cell is shown above delta"; "M\* family cell flagged" |
| **B_t** (floor or evaluability) | "M\* Floor fails"; "M\*'s pooled cell is not evaluable" |
| **C_t** (HK1c) | "M\* HK1c fails" |
| **D_t** (operability) | "M\* not less infeasible than c" (for any c) |

**The branch label.** Every flag that holds is reported, per tracker, in the fixed order E, A, B, C, D. A tracker with no flag passes. The paper's branch label is GO if `C1_verdict` = GO; otherwise it is the ordered union of the flags (for example "NG-A (T1) + NG-D (T3)").

**Three further cases.**
- **NG-X, no verdict of record.** The rerun ladder of plan §9 ends without a completed run, or the analysis aborts on a guard breach. The paper then reports "no verdict of record", the D16 choice that decided it and every stopped run. It makes no substantive reading.
- **Results-review disagreement.** If R21's re-derivation disagrees with the frozen decision, the frozen verdict stands (plan §9). The paper states the verdict of record, the disagreement and its diagnosis. A confirmed code error is published as an erratum showing both verdicts.
- **GO qualifiers,** each named in the abstract sentence when it applies:
  - **Q-empty:** V_t is empty on a tracker, so the operability part is vacuous there;
  - **Q-zse:** a zero-SE removal changed V_t;
  - **Q-construct:** every member of V_t on a tracker is B3, or a comparator infeasible in more than half of decisions.

## 2. Common to every branch

**Title (neutral):**
> Decision-Projected Calibration of Tracker Covariances for Chance-Constrained Planning: Diagnosis on nuScenes, a Stratified Conformal Correction, and a Registered Test on Argoverse 2

**Abstract** (at most 250 words, no citations). Sentences, with budgets (v03: the exact text is in §6; the budgets below are v02's guides, §6's counts govern):

| # | Content | Budget (words) |
|---|---|---|
| S1 | The criterion. NEES is neither necessary nor sufficient for it. | ≤ 35 |
| S2 | The pre-specified nuScenes diagnosis (lateral 0.194 / 0.272; NEES scalar misdirects; one scalar costs 10–12 m), and whether it replicated on Argoverse 2 (H8: "replicated" / "did not replicate") | ≤ 50 |
| S3 | DP-SCRC and its certificate's scope; not shown above δ on three tracker settings | ≤ 35 |
| S4 | The exploratory planner evidence: M\* not shown above δ, mostly narrowing a too-wide raw covariance; per constraint, not per decision | ≤ 40 |
| S5 | The registered verdict, in the plan's words (§3 or §4) | ≤ 65 |
| S6 | What remains open | ≤ 25 |

**Always reported:** every item (a)–(i) of manuscript Section V-F7. That list is the authority, and every number in it is the tool's output.

**Never written, in any branch:**
- for M\* on Argoverse 2: "valid", "calibrated", "certified" or "safe(r)", beyond "not shown above δ" with its power statement; "at most δ" in any cell;
- "GO on one tracker", or a rescue by a secondary, descriptive or post-hoc result;
- "transfers" without H4 and H7;
- "outcome-blind" without a pointer to the plan's §11.3 scope (manuscript Appendix E);
- "outcome-blind boundary enforced by code";
- a safety ranking from loop mode, whose only sentence is plan §6.6's;
- "Trajectron++ is calibrated / certified";
- any of R16 §5's twelve overclaims;
- the plan's §2 "Not claimed" items:
  - a closed-loop guarantee;
  - validity in non-evaluable cells;
  - power outside the power families;
  - validity against exceedances below about 0.15;
  - validity along true axes;
  - an equivalence bound;
  - anything outside the four groups;
  - anything about the test split;
  - that no early look at the annotations was technically possible.

**Always added after the verdict sentence (both branches):**
- the result is per relied constraint, not per decision;
- δ = 0.05 is a calibration level, not a safety target;
- the primary test re-fits M\* within Argoverse 2; transfer is H4 and H7.

**Terminology:** "registered" for the Argoverse 2 study and its hypotheses and diagnosis; "pre-specified" only for the nuScenes stages.

## 3. GO branch

**S5 (fill from the tool's output; k, x, y, z per tracker and population):**
> In a registered, one-shot test on 375 Argoverse 2 logs not used to train the detector, with M\* re-fitted within Argoverse 2, no evaluable cell of M\* was shown above δ = 0.05 on either tracker (one-sided simultaneous 0.95; power ≥ 0.8 against a per-cell exceedance of 0.15 in the power-qualified cells), its pooled 99.5 % upper bounds (nominal, approximate) were at most u, and it was less often infeasible than every comparator not shown above δ.

**Qualifiers, appended to S5 when they apply** (§1):
- **Q-construct:** ", which on [tracker] were only comparators at least as conservative by construction or infeasible in most decisions";
- **Q-empty:** "; on [tracker] no comparator remained, so operability was not tested there";
- **Q-zse:** "; [comparator] was removed on a zero-SE estimate, and H1 without that removal [holds / does not hold]".

**Main text (V-F7), immediately after the verdict:**
- V_t per tracker, with every removal reason;
- the informative comparison (B6 on T3) and its outcome;
- family S's Holm statuses: H2, H3, H4, H6b, H10;
- H7 and H8;
- the per-decision reading;
- per-cell power at 0.10 and U_max beside the verdict.

**Conclusion:**
- the planner-matched procedure, re-fitted on new data, passed its registered screen at the stated power;
- whether nuScenes-fitted thresholds generalise rests on H4 and H7, with their statuses;
- nothing is claimed per decision or about safety.

**Contribution 6:**
> a registered, outcome-blind (in the scope of Appendix E) test on Argoverse 2 whose primary hypothesis held on both trackers; what it does and does not establish is stated in Section V-F6.

## 4. NO-GO branches

**Common to every NO-GO:**
- **Title.** Unchanged.
- **S5** names every failed condition per tracker in the plan's words, and nothing else.
- **S6:**
  > The registered test therefore does not confirm the planner-matched correction on new data; the development evidence of S4 remains exploratory.
- **Contribution 6:**
  > a registered, outcome-blind (in the scope of Appendix E) external test that did not confirm the planner-matched correction, with its failed conditions and registered diagnosis.
- **What the paper then rests on:**
  - the criterion;
  - the pre-specified nuScenes diagnosis and its H8 status, reported whatever it is;
  - the method stage;
  - the exploratory planner evidence;
  - the registered negative result.
- **Family S** is reported unadjusted, labelled "supportive, not confirmatory (gate H1 not passed)", and never quoted as support for M\*.
- **The registered diagnosis** (plan §9) is reported in V-F7(i) by its categories only:
  - per tracker;
  - within against transfer;
  - by source;
  - fallback shares;
  - calibration diagnostics;
  - margins by stratum.

  No mechanism beyond those categories is asserted, and no re-run or method change is reported as a result.

| Flag | S5 clause (per tracker, in this order) |
|---|---|
| **E** | "a procedural NO-GO on [tracker]: [input] required by H1 was [missing / not provenance-valid / raised …]" |
| **A** | "M\* was shown above δ = 0.05 on [tracker] in [cell(s) / family / pooled cell, population] (estimate e, simultaneous lower bound l)" |
| **B** | "on [tracker] M\* was shown above δ nowhere, but the registered power floor was not met on [population] (k power-qualified cells against 6) [or: its pooled cell was not evaluable], so the test was inconclusive for validity there" |
| **C** | "on [tracker] M\* was shown above δ nowhere, but its pooled 99.5 % upper bound on [population] was u, above the registered tolerance of 0.08" |
| **D** | "on [tracker] M\* was not shown above δ, but operability was not shown: it was not less often infeasible than [comparator] (paired upper bound b)". On T3 with B6, the plan's expectation that GO turned on B6 is stated in V-F7, not in S5. |

**What stays out of the abstract.** No quoted rate of failure under a valid M\* (such as the plan's 0.067), and no mechanism.

## 5. What the outcome never changes

- the neutral title, S1, S3 and S4, Sections I–IV and V-A to V-E, and Section VI-E, all written before the decision;
- S2's wording, except its H8 clause;
- the order of reporting: primary, then family S or its supportive reading, then H6a, H7 and H8, then the descriptive results.

## 6. The abstract's exact text (v03; fixed before the decision)

**Word count.** Words are counted by splitting on white space (so "19.4–27.2%", "M*," and "(nominal" are one word each). The assembled abstract (S1–S6, one paragraph, no citations, no equations) must be at most 250 words. Percent signs are written without a space in the abstract only; the body keeps "19.4 %". Tracker names: T1 = CANMOT, T3 = Poly-MOT. Population names: P_rel = "relied-constraint", P_near = "near-constraint", P_ip = "in-path".

**S1 (fixed):**
> Chance-constrained planners with linearised half-space constraints need tracker covariances covering the one-sided error tail along each constraint normal (decision-projected calibration); passing the normalised estimation error squared (NEES) test is neither necessary nor sufficient.

**S2 (only the H8 clause depends on the outcome):**
> In a pre-specified nuScenes study, a tracker's 2 s extrapolation exceeds the toward-ego lateral margin of in-path cars in 19.4–27.2% of items (nominal 5%); the NEES-guided scalar leaves this tail at 13.0–17.2%, and lateral-fixing scalars add 10–12 m of longitudinal margin; on Argoverse 2 the diagnosis {H8}.

{H8} is, from the decision's H8 status: "replicated" if H8 holds at its own 0.025; "did not replicate" if it was tested and does not hold; "was not tested" if its inputs are missing or invalid.

**S3 (fixed):**
> We propose DP-SCRC, stratified conformal risk control in constraint coordinates delivered as a recalibrated covariance, with a scene-level, stratum-marginal certificate on audited objects; on three nuScenes tracker settings no validation cell was shown above 5%.

**S4 (fixed):**
> In an exploratory planner study, the planner-matched variant M*, which mostly narrows over-wide raw covariances, was shown above 5% in no cell; the result is per constraint, not per decision: about one decision in three has an exceeded constraint.

**S5 and S6, GO branch.**
> S5 (before qualifiers): In a registered test on 375 held-out Argoverse 2 logs, with M* re-fitted there, no evaluable M* cell was shown above 5% on either tracker (simultaneous 95% bounds; power at least 0.8 against 15% in power-qualified cells), its approximate pooled 99.5% upper bounds were at most {u}, and it was less often infeasible than every comparator not shown above 5%{Q}.

> S6: Here 5% is a calibration level, not a safety target; transfer of the nuScenes-fitted rule was supported {X}.

- {u} = the largest of M*'s six HK1c pooled upper bounds at 0.995 (T1, T3 × P_rel, P_near, P_ip), rounded **up** to three decimals.
- {X} = "in both secondary tests" if H4 and H7 both hold (H4 by its Holm status in family S, H7 by its own status in the decision); "in one of two secondary tests" if exactly one holds; "in neither secondary test" if neither holds.
- {Q}, the qualifiers of §1, each appended as a clause before the final period:
  - Q-construct: "; on {T} those comparators were conservative by construction or mostly infeasible";
  - Q-empty: "; on {T} no comparator remained, so operability was untested there";
  - Q-zse: "; one removal rested on a zero-SE estimate (H1 without it: {holds / fails})".

**S5 and S6, NO-GO branches.**
> S5: In a registered test on 375 held-out Argoverse 2 logs, with M* re-fitted there, the primary hypothesis failed: {clauses}.

> S6 (fixed): The registered test therefore does not confirm the planner-matched correction on new data; the planner-study evidence remains exploratory, and 5% is a calibration level, not a safety target.

{clauses}: one per (flag, tracker) of §1, in the order E, A, B, C, D and T1 before T3, joined by "; ". When the same clause with the same numbers holds on both trackers it is written once with "on CANMOT and Poly-MOT". Full forms (numbers from the decision file, three decimals):
- **E:** "on {T}, a required input was {missing / not provenance-valid}";
- **A:** "on {T}, M* was shown above 5% in {n} {population} cell(s) (largest estimate {e}, its simultaneous lower bound {l})"; for a family or pooled cell: "in its {population} {power family / pooled cell} (estimate {e}, lower bound {l})";
- **B:** "on {T}, no M* cell was shown above 5%, but the {population} power floor was not met ({k} of 6 qualified cells)"; for P_ip: "but no in-path cell was evaluable"; for an unevaluable pooled cell: "but its pooled {population} cell was not evaluable";
- **C:** "on {T}, no M* cell was shown above 5%, but its pooled 99.5% bound on {population} was {u}, above the registered 0.08";
- **D:** "on {T}, M* was not shown above 5%, but it was not less often infeasible than {comparator} (paired bound {b})".

With an A, B or C clause naming more than one population, the populations are listed in one clause ("relied-constraint and in-path").

**NG-X:** S5 = "In a registered test on 375 held-out Argoverse 2 logs, no verdict of record was obtained ({reason, as in the D16 choice that decided it})." S6 as in NO-GO.

**Overflow rule** (mechanical; applied in this order only until the abstract is at most 250 words; each step used is recorded in the D16 choice of the results):
1. GO: S6's transfer clause is dropped ("Here 5% is a calibration level, not a safety target."); the statuses stay in the conclusion and V-F7(e). NO-GO: every clause's parenthesis is dropped (the numbers stay in V-F7).
2. GO: the qualifiers that apply are merged into one clause "; qualified on {T}: {names}" with the names "comparators conservative by construction or mostly infeasible", "no comparator left", "a zero-SE removal (H1 without it: {holds / fails})". NO-GO: clauses of the same flag on both trackers are merged even when their numbers differ.
3. Both: "held-out" is dropped from S5.

S1–S4, S5's opening and S6's fixed text are never shortened, and nothing else is ever added to the abstract.

**Index terms (fixed):** Autonomous driving, chance-constrained planning, conformal risk control, covariance calibration, Kalman filtering, multi-object tracking, normalised estimation error squared, pre-registration (as in v04b).
