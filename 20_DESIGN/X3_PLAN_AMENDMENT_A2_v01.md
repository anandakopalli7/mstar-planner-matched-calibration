# X3 plan amendment A2: the Q-refit grid extended below its floor (7 Nov 2026, 12:51 EST)

**Status.** It amends `X3_POSTREG_EXPLORATORY_PLAN_v01.md` §2(e2) (38e2526d…).
- **When.** Written after the x3-ref agent's q-fit tables, `60_RESULTS/x3_explore_v01/e2_qrefit/qfit_table_{t1,t3}.json` (160706ee… / 73c82fdf…), and **before any decision-mode run, screen or infeasibility of a Q-refit arm.**
- **What was seen.** Only the training-fold exceedances that select q. No outcome of the arm was seen.

**Trigger.** The plan's grid {0.25, 0.5, 1, 2, 4, 8, 16, 32} hit its floor:
- q = 0.25 was chosen in 17 of 20 (fold, group) cells on T1 and in 20 of 20 on T3;
- on T3 the training exceedance at q = 0.25 is already 0.000–0.0095.

The plan's Q-refit arm therefore sits at the grid floor, not at δ. As specified, it cannot answer the question it was meant to answer: what a process noise matched to the 2 s horizon would do.

**Change.**
- **(e2-ext)** repeats §2(e2) exactly, with the grid extended downward to {0, 1/64, 1/32, 1/16, 1/8, 0.25, 0.5, 1, 2, 4, 8, 16, 32}, under the same selection rule: the smallest q whose B0-type exceedance on the training folds' relied items is ≤ 0.05.
- **q = 0** means no process noise over the horizon: the propagated posterior alone.
- **Both arms are run and reported:** "Q-refit (plan grid)" and "Q-refit (extended grid)".
- **If q = 0 is selected in a cell,** the text states that in that cell even no process noise over-covers the relied constraints.

**Unchanged.** Folds, seeds, the B0 margin rule on the substituted covariances, the decision-mode run, the screen and every report rule of the plan.
