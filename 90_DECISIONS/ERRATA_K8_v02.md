# Errata after R16: statements about the K8 development results (v02, 2 Nov 2026)

v02 = v01 plus E15, from the M*J helper's diagnosis (`70_TESTS/k8_joint_v01/diag/k8_joint_t3_refit_diag_v01.json`). v01 is kept.

Source: `70_TESTS/R16_K8_RESULTS_REVIEW_v01.md`, an independent recompute from the hashed raw arrays of the K8 Linux replicate. Every headline number reproduces. The items below correct how some were read. These errata continue `ERRATA_D05_D07_D10_v01.md` (E1 to E7).

| # | Statement | Where | Correction |
|---|---|---|---|
| E8 | "Closed-loop safety looks comparable: on CANMOT, M* about 25 at-fault collisions per 1000 episodes, close to B6 (24) and better than B4 (28)" | the lead's message to the researcher, 2 Nov, about 07:00 EST | It covers T1 only and implies an ordering. On T3, M* is 31.6 per 1000, second highest of 9 arms (B4 27.8, B6 27.4). Z0 is lowest on both trackers (22.4, 20.2). **No paired M*-minus-arm difference is resolved on either tracker.** LOG's 0 holds by construction. Collisions are low speed and largely an artefact of non-reactive agents. Allowed reading: loop mode resolves no safety difference; it stays descriptive (D14 §4). |
| E9 | "V2 ≈ 1 − 0.95^n, about 0.5 with 14 tracks"; V2_viol 1.9 % (T1) and 0 % (T3) | D14 v05 §9; D16 Choice 2 rationale | On the 840 scenes, M*'s V2 is **0.358** [0.325, 0.392] on T1 and **0.351** [0.320, 0.386] on T3, and 0.40 to 0.42 with executed margins. Constraints within a decision are strongly dependent: on average 8.35 tracks but 30 relied records, against 0.65 under independence. M*'s V2_viol is **0.0080** (T1) and **0.0087** (T3). The qualitative point stands: the certificate is per constraint, and about one decision in three breaks some margin. |
| E10 | "M* passes every validity test", "no flagged cell" | the lead's messages; the K8 summary | Correct as test outcomes, but **"valid" means "not shown above δ"**. M*'s point estimate exceeds δ in 9 of 32 PD7 cells on T1 and 11 on T3 (largest 0.085, T1 SD1_7). T1's pooled PD estimate is 0.0495, with an upper bound of 0.058. |
| E11 | "Form C's ceiling is 0.03" | D16 Choice 1; the lead's message | The arithmetic is correct, but 0.03 is the **floor** of the c rule; the measured price is negative on both trackers. Also, "price on PD7" is computed on all decisions, so the name should be "decision-mode price". |
| E12 | "Form B is met on T3" | the lead's message | Correct, but it **depends entirely on B6 being invalid**: M* − B6 on T3 is −0.005 [−0.017, +0.005], a tie. If B6 passed validity, Form B on T3 would fail. B6's invalidity is robust on nuScenes: 11 to 12 flagged PD7 cells, at t up to 10.7 against q ≈ 3.2. It is structural, since B6 is M* without the motion strata. |
| E13 | Choice 9 ("a comparator failing only a floor stays in Form B(ii)") | D16 v02 to v05 | **Not implemented in `k8_analyse_v03.py`.** `form_valid` includes the floors, so such a comparator is dropped and the Bonferroni count shrinks. It has no effect on nuScenes, but B3's T3 SD1_7 family sits exactly at the floor of 6. **This must be fixed in the AV2 analysis code before the freeze.** |
| E14 | "RETUNED is invalid" | the K8 summary | It is selected on the pooled rule but judged on the cell rule, and on T1 it equals B0. On T1, no point of the B0 α/δ′ sweep is valid even at α = 8. On T3, the cheapest valid point is B0a0.25, with an infeasible rate of 0.581. Report this as such, not as one verdict. |

| E15 | "DP-SCRC thresholds are reproducible from their items" | implicit in K7, K8 and the manuscript | Reproducible **given the scene order**. At an exact tie, where the CRC bound equals δ in rational arithmetic, the floating-point sum depends on summation order. T3, fold 4, h2s, one L0 cell (large, <20 m, long, turning, not in path; 243 items, 108 scenes): at U = 0.38665 the bound is exactly 1/20. In K7's scene order the float sum is just above δ, so U is rejected and K7 took the next grid value, 0.39570 (bound 0.041). In sorted-name order the sum is just below δ. The effect is one grid step more conservative in one cell, so validity is unaffected; T1 has no tie that flips. **The AV2 analysis and any new fit must decide the CRC rule in exact rational arithmetic, as `k8_joint_fit_v02.py` does for λ, or state the fixed scene order.** Add a line to the manuscript where reproducibility is claimed. |

Consequences for the AV2 plan (C1):
- M* against B6 is pre-registered as the motion-strata ablation.
- The power check estimates the chance that B6 passes validity at AV2 sizes.
- Loop mode stays descriptive.
- The validity wording is "not shown above δ".
- The AV2 analysis code implements Choice 9.
- The AV2 analysis code decides CRC thresholds in exact arithmetic (E15).
- The 12 overclaim sentences in R16 §5 are binding for the manuscript.
