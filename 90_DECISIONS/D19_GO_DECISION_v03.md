# D19: C1 Argoverse 2 confirmation, GO decision report (v03, 7 Nov 2026)

v03 = v02 (kept) plus R21 step 4. The results review is complete; nothing in it changes the verdict or any status.

v02 = v01 (kept, d22f34c6…) with every finding of the independent number trace `70_TESTS/D19_NUMBER_TRACE_v01.md` (about 205 values match; 7 mismatches, 3 unsupported phrases and 5 omissions, all fixed below) and R21's Monte Carlo step 3.

## Verdict: **GO**

- **The test.** The frozen plan is `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v07m.md` (SHA-256 0817e600…), frozen 6 Nov 2026 at 20:08:13Z and registered under embargo at 20:31Z (https://osf.io/v8qfk/; deposit record 1911afcf…).
- **The verdict of record** is r1, the first and only completed run of the frozen analysis.
- **What GO means here** (plan §2, "What GO establishes"; reporting frames v02 §3): on 375 Argoverse 2 logs not used to train the detector, with M\* re-fitted within Argoverse 2, the following holds on both trackers, CANMOT (T1) and Poly-MOT (T3):
  - no evaluable cell, power-family cell or pooled cell of M\* was shown above δ = 0.05 (one-sided simultaneous 0.95; power ≥ 0.8 against a per-cell exceedance of 0.15 in the power-qualified cells);
  - the floors were met;
  - its pooled 99.5 % upper bounds (nominal, approximate) were at most 0.055, against the registered tolerance of 0.08;
  - it was less often infeasible than every comparator not shown above δ.
- **The registered qualifier (Q-construct, both trackers).** The comparators not shown above δ were only B3, which is at least as conservative as M\* by construction (Proposition 9), and, on T3, B0, which was infeasible in 0.858 of decisions. So Form B adds little to the screen, as manuscript Section V-F4 (written before the outcome) anticipated for exactly this comparison set. What the result shows is that M\* passed the registered screen and the floors.
- **Sources and records.**
  - Every Argoverse 2 number below is read from `60_RESULTS/c1_av2_v01/c1_decision_r1.json` (ff976904…), `c1_analysis_r1.json` (1100bbf7…), its CSV folder and the method-stage tables (`mstage/mstage_t*.json`). R21's numbers come from its own outputs, run times from the run notes, and development numbers from manuscript v04b (Section V-D).
  - The results tool's output is `80_LOGS/c1_manuscript_v01/C1_RESULTS_MATERIAL_r1_v01.md`.
  - The independent re-derivation R21 is in `70_TESTS/R21_c1_v01/real/`.
  - D16 v53 Choice 72 records the verdict.

## 1. The run of record

- **The run.** Line 67 of the frozen command list (`c1_analyse_v10.py`) ran once on this laptop: 2026-11-07 10:33:42Z to 12:22:57Z, 6540 s, exit 0, at B = 40,000. The orchestrator ended with 59 of 59 lines done. The analysis rerun lines (_r2 to _r4) were never needed.
- **Earlier line failures.** Lines 24 and 25 (transfer fits) first failed because their output folder did not exist, and were rerun with their frozen commands (deviation log entry 3; D16 Choice 68). Lines 26 and 27 were run by hand (Choice 69). No rule, input or seed changed.
- **Completion check** (plan §9, R21 run-log check `r21_runlog_check_r1.json`): 96 checks, 0 problems.
  - The run log's hash chain is intact (82 lines).
  - Run ed69b9e4… is a completed run: both outputs are present, and none of the seven memory or disk strings occurs.
  - Every table of record has its done line and still hashes as recorded.
  - Every line carries the frozen plan's hash and the single deposit record.
- **Bindings.** The decision binds the plan, the config (9f1f9d14…), the folds and the deposit record. The E⁰ check is ok, there are no route problems, and Q1 is "not tested", as registered.
- **Before the run.** The wording of every branch (frames v02, d1b57da5…; v03, 3484a82d…), the results tools and R21's code and tolerances were hashed in D16 v51 and v52 before the decision existed.

## 2. The primary hypothesis H1

**The registered screen of M\*** (within Argoverse 2; decision mode; P_rel = relied constraints, P_near = gap ≤ 5 m, P_ip = in-path):

| Tracker | Population | Evaluable cells | Flagged cells / family cells / pooled | Power-qualified family (floor) | Pooled exceedance | Pooled 99.5 % UB (HK1c ≤ 0.08) | Largest simultaneous 95 % UB (approximate) |
|---|---|---|---|---|---|---|---|
| T1 | P_rel | 27 | 0 / 0 / no | 19 (≥ 6) | 0.044 | 0.048 | 0.127 |
| T1 | P_near | 16 | 0 / 0 / no | 9 (≥ 6) | 0.038 | 0.047 | 0.118 |
| T1 | P_ip | 8 | 0 / 0 / no | 5 (≥ 1 evaluable) | 0.040 | 0.055 | 0.129 |
| T3 | P_rel | 27 | 0 / 0 / no | 19 (≥ 6) | 0.043 | 0.047 | 0.122 |
| T3 | P_near | 16 | 0 / 0 / no | 8 (≥ 6) | 0.032 | 0.041 | 0.110 |
| T3 | P_ip | 8 | 0 / 0 / no | 5 (≥ 1 evaluable) | 0.040 | 0.052 | 0.157 |

- **Power.** It is a pre-data property and licenses no "at most" statement. Per-cell power at a planted exceedance of 0.10 ranges 0.00–0.96 (median about 0.6 on P_rel, 0.1 on P_near and 0.2 on P_ip). Five P_rel cells per tracker are not reached by 0.20. The power-qualified families hold 98.7 % (T1) and 98.8 % (T3) of P_rel records.

**V_t and Form B** (removal at 1 − 0.0125/9; Form B at 1 − 0.0125/|V_t|; M\* − comparator, log-mean infeasible-decision rate):

| Tracker | V_t | Comparison | Mean | Upper bound | Level |
|---|---|---|---|---|---|
| T1 | {B3} | M\* − B3 | −0.783 | −0.760 | 0.9875 |
| T3 | {B0, B3} | M\* − B0 | −0.611 | −0.582 | 0.99375 |
| T3 | | M\* − B3 | −0.694 | −0.666 | 0.99375 |

- **Removed comparators.** Every other comparator (B0 and B1 on T1, B4, B6, B9 and RETUNED on both trackers, and B1 on T3) left V_t on a cell or power-family flag at one-sided 0.99861. Zero-SE removals changed no V_t, so H1 is the same with and without them.
- **The informative comparison on T3, B6.** The plan expected a GO on T3 to turn on B6. B6 was shown above δ (flagged in 5 P_rel cells on each tracker) and so left V_t.
- **Descriptively** (Table XII; not a claim of the registered test): every arm infeasible in fewer than half of decisions was shown above δ, except M\*. Those arms are B4 (0.20 on T1 / 0.32 on T3), B6 (0.17 / 0.23), B0 on T1 (0.37) and RETUNED on T1 (0.41). M\*'s infeasible-decision rate was 0.186 (T1) and 0.247 (T3); its mean margins 0.57 / 1.22 m (T1) and 0.65 / 1.93 m (T3), lateral / longitudinal.

**The per-decision reading** (plan §6.6; frames v02 §2). The result is per relied constraint.
- **V2**, the share of decisions with some relied constraint exceeded, is 0.491 (T1) and 0.496 (T3) for M\*. Its per-track reference is 0.441, at 13.07 tracks per decision.
- **Against development.** V2 was 0.358 and 0.351 against a reference of 0.308 (8.35 tracks). The excess over the reference is about the same on both datasets: +0.049 and +0.055 on Argoverse 2, +0.050 and +0.043 on development. The higher V2 reflects more tracks per decision.
- **V2_viol** is 0.016 and 0.018.

## 3. Secondary claims

**Family S** (Holm at 0.025, m = 5, opened because H1 holds; p = (k + 1)/(B + 1)):

| Claim | What it tests | Result | p | Status |
|---|---|---|---|---|
| H2 | Price of M\* against B4 (single global factor) ≤ 0.03 in infeasible-decision rate | T1: −0.016, UB 0.005; T3: −0.069, UB −0.054 | 2.50e-05 | **confirmed** |
| H6b | Method stage: B4 shown above δ in a cell where M\* is not flagged, with paired B4 − M\* > 0, on T1 and T3 | T1 car < 20 m lateral turning; T3 car 20–40 m longitudinal straight; p 0.0199 (200 refit-CV replicates, so only k = 0 could reach Holm's smallest level, plan §6.1) | 0.0199 | not confirmed (Holm level 0.00625) |
| H10 | Cell part: B6 flagged at 0.975 where M\* is not, paired lower bound > 0; non-inferiority part: M\* − B6 infeasible rate ≤ 0.03 | Cell part held on both trackers; NI part T1 +0.021, UB 0.039 (fails); T3 +0.018, UB 0.027 | 0.172 | not confirmed |
| H3 | Trajectory-level M\*Jx: ValidJ and less infeasible than V^J | ValidJ on both; T1 vs B3 −0.111 (UB −0.092); T3 vs B0 +0.040 (UB 0.055, fails) | 1.000 | not confirmed |
| H4 | H1's formula with every arm fitted on the 850 nuScenes scenes (transfer route) | M\* shown above δ on both trackers (T1: car and large longitudinal P_rel cells, a large longitudinal static P_near cell, the in-path pooled cell, and in-path HK1c fails; T3: car and large longitudinal P_rel cells, the in-path family and pooled cells, and in-path HK1c fails) | 1.000 | not confirmed |

**Other secondary claims:**
- **H6a holds:** the method stage's DP-SCRC, re-fitted within Argoverse 2, is not shown above δ on the audit population.
- **H7 does not hold:** DP-SCRC with the nuScenes-fitted thresholds is shown above δ on both trackers. This holds in the car longitudinal straight-motion cell (all ranges; lower bounds 0.106 on T1, 0.101 on T3) and in the pooled cell (exceedance 0.123 and 0.116; lower bounds 0.098 and 0.095; `mstage_t*.json` E2).
- **Family P, H8 holds: the diagnosis replicates.** On T1 under B0 (the raw covariance), the in-path car lateral 2 s cell at 20–40 m fails: 0.214, band [0.122, 0.306], against the threshold max(δ, E⁰) = 0.090. Its truth-oriented exceedance also fails: 0.144 [0.068, 0.220]. The < 20 m lateral cell fails on the primary version (0.147 [0.093, 0.201]) but is consistent on the truth-oriented one. Descriptively (outside H8's definition, which is lateral), the 20–40 m longitudinal cell also fails on both versions (0.158 and 0.154).

**The reading of the secondary claims together.** The procedure, re-fitted on new data, passes (H1, H6a). The nuScenes-fitted thresholds do not transfer (H4, H7), and their failures are mostly in longitudinal cells of cars and large vehicles, including new tracks. The paper therefore claims a procedure, not transferable thresholds.

## 4. The independent results review R21

- **Step 1 (run log and tables of record):** 96 / 96, as in §1.
- **Step 2 (re-derivation with separate code, B = 40,000):**
  - R21 reproduced the analysis's bootstrap weights exactly (480 bounds, largest difference 4 × 10⁻¹⁶).
  - 108,059 comparisons agree; 0 disagreements; 2 MC-borderline; 48 informational.
  - H1 holds on both trackers with the same V_t and Form B bounds, with and without zero-SE removals. H2, H3 and H4 agree.
- **The two borderline rows change no status.**
  - R21's own power check (500 datasets) puts one more cell in T3's P_near power family (9 against 8; both ≥ 6).
  - On the transfer route (T1, B6, P_ip, "shown above"), neither computation has a family flag, and both find HK1c failing (upper bound 0.089). The difference is one of definition: the analysis's "shown above" includes an HK1c failure, while plan §6.2 has no HK1c term. B6 leaves V_t on other conditions in both, and H4 fails on Valid(M\*) in both.
- **What R21 does not re-derive:** H6a, H6b, H7, H8, H9, H10 and Form A (D16 Choice 71c). Those rest on the frozen code alone.
- **Step 3 (Monte Carlo SE and seed stability, 20 alternative seed sets, families fixed; descriptive; `r21_mcse_fixed_r1.md`).**
  - H1 holds in 20 of 20 sets.
  - V_t and V^J membership is identical in all 20.
  - Every status of M\* is identical in all 20.
  - The Monte Carlo SE of the Form B bounds is at most 0.0004, and of M\*'s HK1c bounds at most 0.00013.
  - The only statuses that vary belong to comparators removed on other conditions: B4's P_near no-flag on T1 (same in 16 of 20 sets) and B1's P_rel no-flag on T3 (19 of 20).
- **Step 4 (the power rule redrawn in each of the 20 sets; `r21_mcse_recompute_r1.md`).**
  - H1 holds in 20 of 20 sets.
  - V_t and V^J are identical in all 20.
  - No status and no power-family size of M\* changes.
  - Only some comparators' family sizes move, by ±1 cell (for example B0's P_near family on T1: 9 or 10), with no effect on V_t.
- **Status.** The verdict of record stands whatever R21 shows (plan §9).

## 4b. Descriptive results that bear on the reading

These are descriptive (plan §7) and change no status. They are reported because they limit the reading.
- **AB3DMOT** (the third tracker, same 375 logs). M\*'s pooled P_rel cell is shown above δ: exceedance 0.061, pointwise lower bound 0.057. Valid(M\*) is therefore false on that tracker.
- **The 150-log routes** (H1-P with the public LT3D detector, H5 with VoxelNeXt, the train-to-validation source transfer). Valid(M\*) is false on both trackers in each, only through the P_near power floor (fewer logs give fewer power-qualified cells). No M\* cell is shown above δ there.
- **Form A** fails on T1: against B4, the upper bound is +0.010.
- **H9** (Trajectron++). It has 2 power-qualified E2 cells against the floor of 6, so the floor is not met, and its label is "not seed-robust".

## 5. What may and may not be claimed

**May be claimed** (frames v02 §3, v03 §6):
- in a registered, one-shot test, the planner-matched procedure re-fitted on Argoverse 2 passed its validity screen on both trackers at the stated power, with the floors and HK1c met;
- it was less often infeasible than every comparator not shown above δ, with the Q-construct qualifier;
- H2 is confirmed;
- the nuScenes diagnosis replicated (H8);
- the nuScenes-fitted thresholds were not supported on Argoverse 2 (H4 and H7 not confirmed);
- with the descriptive limits of §4b stated beside it: AB3DMOT, the 150-log routes, Form A and H9.

**Never written:**
- for M\* on Argoverse 2: "valid", "calibrated", "certified" or "safe(r)", beyond "not shown above δ" with its power statement;
- "at most δ" in any cell. M\*'s largest simultaneous upper bounds are 0.110–0.157 per population, so exceedances of that size cannot be excluded in individual cells;
- "transfers";
- anything per decision. About half of decisions have some exceeded relied constraint;
- safety, or a ranking from loop mode;
- superiority over methods outside K;
- any item of the plan's §2 "Not claimed" list.

**δ = 0.05 is a calibration level per constraint, not a safety target.**

## 6. Where this leaves the paper, and the next steps

**The paper now has its confirmatory result.** It rests on:
- the criterion and its theory;
- the pre-specified nuScenes diagnosis, replicated on Argoverse 2;
- DP-SCRC and its certificate;
- the planner-matched procedure, passing a registered external test;
- an honest negative on threshold transfer.

**Next steps:**
1. R21 steps 3 and 4 (running), then v02 of this report.
2. Manuscript v05: V-F7 and Tables IX–XIII from the results material in frames v02/v03 wording; the abstract as filled (`20_DESIGN/ABSTRACT_FILLED_r1_v01.md`, 248 words); conclusion and contribution 6 per frames §3; the length cut; the fixes in `20_DESIGN/V05_TODO_FROM_LATEX_v01.md`.
3. A final number trace and an independent referee pass on v05; then the LaTeX package (template and compile, with the researcher).
4. **The researcher:** upload the run log (`40_PROTOCOL/C1_RUN_LOG.txt`) and the stage-B log (`40_PROTOCOL/C1_STAGE_B_LOG.txt`) to the OSF registration's project, as plan §8.6 requires. Plan §8.3 sets the embargo to end after the expected publication; it may be ended earlier, and reviewers get a view-only link meanwhile.
