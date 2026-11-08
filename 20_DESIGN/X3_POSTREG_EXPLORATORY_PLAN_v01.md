# X3: post-registration exploratory analyses for the v06 revision (plan v01, 7 Nov 2026, 11:10 EST)

**Status.** Written and hash-locked (sidecar `.sha256`, D16 v55 Choice 74) **before any X3 output exists**. The researcher chose D20 option A ("Option A: full revision", 7 Nov 2026). Every analysis here answers a named concern of the referee read `70_TESTS/V05_REFEREE_REVIEW_v01.md`.

**What X3 is and is not.**
- **Post-registration and exploratory.** It comes after the verdict of record (r1 = GO, `60_RESULTS/c1_av2_v01/c1_decision_r1.json`, ff976904…), and nothing in it changes that verdict, a claim status, or any table of record.
- **Every pre-specified output is reported**, whichever way it points, in the manuscript section "Post-registration exploratory analyses" and in full in the supplement. An analysis that cannot be completed is reported as such, with the reason.
- **Every output carries the stamp** `X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)`.

## 0. Common rules

- **Data.** The 375 Argoverse 2 logs; the frozen stage-B caches (`30_DATA/av2_cache_stageB_c1b_{t1,t3,tab}_own375`); the frozen folds (`60_RESULTS/c1_folds_v01/C1_FOLDS_375_v01.json`, 5 folds of 75 logs); the frozen items (`60_RESULTS/c1_av2_v01/items/`) and fits of record (`60_RESULTS/c1_av2_v01/fits/fits_within_{t1,t3,tab}.json`).
  - T1 (CANMOT) and T3 (Poly-MOT) are reported in every analysis.
  - AB3DMOT (`tab`) is reported where stated, descriptively.
  - The route is `within_lt3d`, the route of H1.
- **Mode.** Decision mode only, as the runs of record. Loop mode is not run.
- **Code.**
  - New code goes in `50_CODE/x3/`; outputs go in `60_RESULTS/x3_explore_v01/`.
  - The frozen modules are imported read-only, never edited and never run as entry points: `k8_sim_v04`, `c1_run_v02`'s scene job, `c1_fit_v02`, `c1_crc_exact_v01`, `k8_analyse_v04`, `c1_analyse_v02`/`v10` and the R21 library `70_TESTS/R21_c1_v01/r21_lib*`.
  - No X3 tool writes under `60_RESULTS/c1_av2_v01/` or `40_PROTOCOL/`.
- **Integrity checks around every X3 step.** `40_PROTOCOL/C1_RUN_LOG.txt` keeps sha256 8bc6235d…, and a hash manifest of `60_RESULTS/c1_av2_v01/` is identical before and after. A difference stops X3 and is reported.
- **Screen.**
  - "Passes the screen" means the arm is Valid by the registered screen as coded (`c1_analyse_v02.arm_status` on `k8_analyse_v04.hk1_rule` with the frozen constants: δ = 0.05, the power-qualified families and floors, HK1c at 0.995 with margin 0.03, MIN_LOGS 8, MIN_SCENES 39). "Shown above δ" is that code's ShownAbove.
  - **Bootstrap.** Log-cluster bootstrap with B = 4000 for X3, against 40000 of record. If one `hk1_rule` call on the 375 logs takes more than 60 s, B = 2000 is used inside the cross-fitted selection steps only; the final status of every arm or composite is always computed at B = 4000.
  - **Seeds.** Bootstrap [20261201, i, j]; power [20261202, i, j]. Here i = 0 for T1, 1 for T3 and 2 for tab, and j is the analysis index: (a) 1, (b) 2, (c) 3, (d) 4, (e) 5, (g) 7.
- **Infeasibility.** The arm's per-log infeasible-decision share, averaged over logs, as of record (`per_scene_rates`). Paired differences against M\* use the per-log differences with a percentile log bootstrap: a 95 % interval and B = 4000.
- **Cross-fitted selection ("matched validity").** Order a family's grid from least to most conservative. For each held-out fold f:
  - take the first grid point that passes the screen on the other four folds' logs (`c1_analyse_v02.retuned_hk1`'s rule, with an explicit ordering in place of `CURVE_ALPHA_OF_ARM`);
  - apply it to fold f's logs; if no point passes, use the most conservative point and flag it.

  The composite arm is then screened and its infeasibility computed on all 375 logs, exactly as RETUNED-HK1 of record.

## 1. Validation gates (before any new output is read)

- **V0, the runner.** The X3 runner, run on the fits of record for the arms M\*, B0, B4, B6 and B9 (T1 and T3), reproduces the runs of record exactly for those arms: the decision arrays (`infeasible`, `lam`, `stats`, `trk`) and the counts (`cell`, `n`, `exceed`), after re-indexing episodes. A mismatch stops X3.
- **V1, the screen.** The X3 screen code at B = 4000, on the outputs of record, gives each arm of record a status. Its agreement with the statuses of record (B = 40000) is reported arm by arm. A disagreement is acceptable only for a decisive quantity within about 3 MC SE of its threshold (R21 step 3's MC SE as the yardstick); otherwise X3 stops.
- **V2, the partitions.** The partition-tagged counts of analysis (b), summed over the bins, equal the counts of record per arm, population and log.

## 2. The analyses (priority order: V0–V2, f, c, a, b, e1, d, g, e2)

### (a) Matched-validity operability (M2)

- **Families.** Each comparator is refitted at a grid of nominal levels δ′ by the frozen fit rule (`c1_crc_exact_v01`, with `delta = δ′` and n_min = ⌈1/δ′⌉ − 1 per stratum), cross-fitted on the same folds:
  - **B4:** one pooled CRC threshold per step;
  - **B6:** hierarchical CRC from L1, no motion strata, split by in-path;
  - **B9:** the norm-ball radius.
- **Grid.** δ′ ∈ {0.05, 0.04, 0.03, 0.02, 0.015, 0.01, 0.005, 0.0025, 0.001}, least conservative first. δ′ = 0.05 is the arm of record.
- **The B0 family.** The scale of B0 is the merged α/δ′ curve of record, so RETUNED-HK1 of record is its matched-validity point (T1 infeasible 0.781; T3 0.977). It is reported from the record and not re-run.
- **Outputs, per family and tracker:**
  - the per-fold choice;
  - the composite's screen status;
  - its infeasible rate;
  - M\* minus the composite (paired, 95 % interval);
  - the whole curve: each grid point's in-sample status and infeasible rate on all 375 logs.

### (b) The screen on partitions no method used (M3)

- **Partitions, with bins fixed now** (no method's strata use them):
  - **P1 track speed** `tr_spd`: [0, 0.5), [0.5, 3), [3, 8), ≥ 8 m/s;
  - **P2 track length** `tr_l`: < 2, [2, 5.5), [5.5, 8), ≥ 8 m;
  - **P3 track age**, keyframes since the track id first appeared in the log, at that keyframe: 1–2, 3–5, 6–10, > 10;
  - **P4 detection score** `tr_score`: [0.4, 0.5), [0.5, 0.7), [0.7, 0.85), ≥ 0.85;
  - **P5 ego speed at the decision** (`v_now`): < 1, [1, 5), [5, 10), ≥ 10 m/s;
  - **P6 annotation lidar points** `gt_pts` at k + h, a visibility proxy: 1–10, 11–50, 51–200, > 200;
  - **P7 city** of the log, if the city is recorded in local AV2 metadata. Otherwise P7 is omitted, and that is reported.
- **Cells and rule.**
  - Cells are bin × relied-on axis (long, lat), on each population P_rel (PD7_primary), P_near (SD1_7) and P_ip (PD_inpath).
  - A cell is evaluable with ≥ 39 logs holding records in it.
  - A cell is flagged when its one-sided simultaneous sup-t lower bound at 0.95, over the evaluable cells of that partition and population (the record's flag rule), exceeds δ = 0.05.
- **Arms:** M\*, B0, B1, B3, B4, B6 and B9 on T1 and T3, and M\* on tab (descriptive). The counts come from a re-run of these arms with partition-tagged counts; V2 holds for them.
- **Outputs, per arm, partition and population:**
  - the flagged cells;
  - the largest cell estimate with its simultaneous upper bound;
  - for M\*, every cell whose point estimate exceeds δ, with its interval and log count.
- **Also reported:** distance to the ego, a partition M\*'s strata do use, for completeness.

### (c) Interval sensitivity and false removal (M4)

- **(c1) Alternative intervals** for the quantities that decided H1:
  - M\*'s pooled HK1c upper bounds (3 populations × 2 trackers);
  - M\*'s largest simultaneous cell upper bound per population;
  - the lower bound of every comparator cell flag that removed a comparator from V_t.

  Each is recomputed by:
  - (i) the percentile log bootstrap, as of record;
  - (ii) a studentised log bootstrap: the cluster delta-method SE of the ratio estimator, with the SE floored at √(δ(1 − δ)/N_eff);
  - (iii) a design-effect Wilson interval: n_eff = N / deff, deff = 1 + (m̄ − 1)ρ̂, with ρ̂ the ANOVA intraclass estimate across logs. Multiplicity is handled as of record, by Bonferroni where the record uses sup-t.

  **Reported:** the status changes (pass, flag, removal) under (ii) and (iii).
- **(c2) Simulated false removal and coverage** at Argoverse 2's cell sizes.
  - **Simulation.** 1000 datasets per tracker. Each has the observed per-log record counts per cell, the true rate of every cell set to δ = 0.05, and per-log rates drawn from Beta(δ, ρ̂) per cell (beta-binomial).
  - **Applied to each dataset:** the record's comparator flag rule at the removal level 1 − 0.0125/9, by sup-t with an inner log bootstrap of 1000.
  - **False removal:** the share of datasets in which a comparator with that cell layout is flagged in ≥ 1 cell, for every comparator removed from V_t in r1.
  - **Coverage:** the coverage of M\*'s simultaneous "95 %" upper bounds and of the HK1c "99.5 %" pooled bound under the same simulation, at true rates δ and at M\*'s observed cell rates.

### (d) M\* at a reference that is I_k-measurable (M5)

- **Items rebuilt** with the frozen items rule, changing only the reference ego progression that defines the enforced pairs, relied-on axis and side of separation. Of record it is the logged arc length at t_k + h. The two alternatives use no information after t_k except the route, which a planner has:
  - **(d1) the planner's own reference plan:** the candidate the decision-mode planner chooses at margin 0 (arm Z0) at keyframe k;
  - **(d2) constant current speed** along the logged path: s_k + v_k·t, capped at the path's end.
- **Then**, for each reference, M\* is refitted on those items by the frozen fit rule and folds, and run in decision mode. The relied constraints of the screen are, as of record, those of each arm's own chosen plan.
- **Outputs:** screen status, infeasible rate, the paired difference against M\* of record, and the relied-item exceedance by population. AV2 T1 and T3 only. The nuScenes development re-run is not made, because AV2 is the larger and external set.

### (e) The obvious alternatives (M8)

Each alternative is fitted on the items by its rule, cross-fitted on the same folds, run in decision mode, screened and compared with M\*, like (a).

- **(e1) Fitted by a frozen rule:**
  - **B5, per-axis scalars:** one pooled CRC threshold per step and object axis.
  - **B8, stratified variance matching:** `m_lib_v04`'s rule, threshold z_0.95·√(mean U²) per L0 stratum with its fallback.
  - **B7, learned scale:** `m_lib_v04`'s rule, ported unchanged: a scale model on a seeded half of the calibration logs, CRC on the other half.
- **(e2) A process noise re-fitted for the 2 s horizon (Q-refit).**
  - **The decomposition.** The tracker's propagation is linear in Q. So the predicted covariance at step h is S_h(q) = A_h + q (S_h − A_h), where A_h is one re-propagation of the frozen tracker exports with Q = 0 (the frozen propagation functions of `av2_horizon_prep_v02`, imported).
  - **The fit.** For each training split, q per class group comes from the grid {0.25, 0.5, 1, 2, 4, 8, 16, 32}. It is the smallest q whose B0-type margin z_0.95·sd(q) has a pooled exceedance ≤ 0.05 on the training logs' relied items.
  - **The run.** The arm runs B0's margin rule on the substituted covariances.
  - **If not done.** If the exports or the propagation cannot reproduce S_h to 1e-9 on a check log, (e2) is not done and the reason is reported.

### (f) The infeasibility–violation trade-off (M10), from the outputs of record

- **The figure.** For every arm of record (sweep points and RETUNED-HK1 included), on T1, T3 and tab:
  - the infeasible rate against V2 (the share of decisions with an exceeded relied constraint);
  - the infeasible rate against V2_viol;
  - the marker shows the arm's screen status.
- **What infeasible decisions do.** For M\* and each comparator, the shares of decisions by executed back-off level λ ∈ {1, 0.75, 0.5, 0.25, 0} and the emergency stop (λ = −1), from `decisions_*` `lam`.

### (g) Learning curve (M6)

- **Design.** M\* is refitted on n ∈ {25, 50, 100, 200, 300} training logs: per held-out fold, a seeded subsample of the 300 training logs, with 3 repeats for n < 300 (seeds [20261207, n, r, f]). It is applied to the held-out fold.
- **Outputs, per n and repeat:**
  - the composite's screen status;
  - the infeasible rate;
  - the pooled exceedance per population;
  - the share of M\*'s thresholds that fell back to a coarser level.

### (h) The AB3DMOT diagnosis (M7), from the outputs of record and (b)

- Which cells and populations are flagged for M\* on tab.
- The fallback shares of tab's fits.
- The share of relied records from low-score tracks (P4).
- The share of enforced pairs whose track has no ground-truth match (false-positive tracks): these enter the planner's constraints but not the certificate.

## 3. What each analysis can and cannot show

- **(a) and (e)** compare operability at matched validity, which Form B could not do.
- **(b)** tests validity on partitions no method used, but at lower power per cell than the registered screen.
- **(c)** measures how much the labels and the removals depend on the interval method.
- **(d)** shows whether M\*'s validity and operability depend on the hindsight reference.
- **(g)** gives the re-fit cost in logs.

None of them is confirmatory: the registered result is r1 alone.
