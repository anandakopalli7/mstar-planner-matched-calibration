# Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Open-Loop Log-Replay Test on Argoverse 2

Ananda Siva Kumar Kopalli Naga Venkata, Independent researcher (e-mail: anand.knvasks@gmail.com; ORCID: 0009-0002-5241-9922)

## Abstract

Linearized chance-constrained planners need a tracker's covariance to cover the one-sided tail along each constraint normal, which the normalized estimation error squared (NEES) check does not test. On nuScenes, a constant-velocity tracker's 2 s covariance under-covers in-path cars laterally, and NEES-guided inflation of both axes does not fix it. On the constraints a speed planner relies on, the raw covariance is mostly too wide. We propose M\*, per-stratum conformal risk control fitted on those relied constraints (a proxy at the logged ego trajectory), returned as a covariance for the unchanged planner. In a registered open-loop log-replay test on 375 Argoverse 2 logs with a speed-only planner, M\*, re-fitted there, was not shown above 5 % in any evaluable cell on two trackers; its nominal 99.5 % pooled bounds were at most 0.055, single cells up to 0.16 are not excluded, and it was less often infeasible (forced to back off its designed margin) only than comparators conservative by construction or mostly infeasible. In exploratory analyses after the verdict, with each method tuned to pass a screen on partitions no method stratifies on directly, M\* was infeasible in 3–38 percentage points fewer decisions than every comparator family matched within the grid; the smallest gain, against M\* without its course-change strata, came with more exceedance at execution on one tracker. M\* under-covered low-score and new tracks, failed its screen on a third tracker, and its nuScenes-fitted thresholds did not transfer (in-path pooled exceedance 0.070). Calibration is per constraint, not per decision.

**Index Terms** — Autonomous driving, chance-constrained planning, conformal risk control, covariance calibration, Kalman filtering, multi-object tracking, pre-registration.

---

## I. Introduction

A chance-constrained motion planner requires each nearby object to stay out of the space the ego vehicle is about to use with probability at least 1 − δ per constraint. Under a Gaussian prediction, a linear constraint becomes a margin z_{1−δ}√(aᵀV̂a) along its normal a [Blackmore2011; Ono2008], where V̂, for a tracked road user, is a Kalman-filter covariance propagated to the planning horizon [Zhu2019], a form driving-scale planners keep [Nair2025; Ren2025]. The planner thus consumes a *one-sided tail quantile* of the covariance, along directions it chooses.

A tracker's covariance is tuned for association and checked, if at all, by the whole-vector normalized estimation error squared (NEES) [BarShalom2001; Osterburg2026], whose acceptance neither implies nor is implied by the property the planner needs; a single-scalar correction over-pays when directions need different corrections (Section III). On nuScenes, a constant-velocity tracker's 2 s covariance shows both effects for in-path cars: the lateral tail is exceeded in 15–27 % of items against a nominal 5 % (15.4 % truth-oriented below 20 m to 27.2 % estimate-oriented at 20–40 m; Section V-B), the longitudinal tail is over-covered, and the NEES-guided scalar inflates both axes, leaving the lateral tail at 13–17 % and wasting meters longitudinally.

Those in-path lateral cars are 0.4 % of the constraints a speed planner actually relies on (T1, nuScenes validation split, classes covered by the learned predictor, 2 s), and on the relied constraints as a whole the raw covariance is mostly *too wide*. A calibration meant to serve a planner must therefore be fitted on the planner's own constraints, not on an audit population chosen in advance.

M\* (Section IV) is calibrated on the constraints a chance-constrained speed planner enforces and relies on, a proxy population defined with the logged ego trajectory. It scores the one-sided error along each separating object axis, fits one conformal-risk-control threshold per stratum of features the planner observes, with a count-based fallback and the log as the exchangeable unit, and returns a covariance the planner uses unchanged.

**The registered claim.** M\* and every rule of its test were developed on nuScenes (Section V-C) and then tested in a registered one-shot test on 375 Argoverse 2 logs not used to train the detector, in open-loop log replay with a speed-only planner, its plan frozen before any outcome existed (Section V-D). **The verdict was GO:** re-fitted within Argoverse 2, M\* was not shown above δ = 0.05 in any evaluable cell of the relied constraints on either registered tracker, and its nominal 99.5 % pooled upper bounds were at most 0.055. But the comparison the registered rule retained was uninformative, since only comparators conservative by construction, or infeasible (forced to back their designed margin off) in most decisions, remained; single cells up to about 0.16 cannot be excluded by the registered bounds, and up to about 0.19 by a better-calibrated interval (Section V-E(c)); M\*'s thresholds fitted on nuScenes did not carry over to Argoverse 2 (pooled in-path exceedance 0.070, upper bound 0.089, flagged mainly in longitudinal cells; H4); and on a third tracker, AB3DMOT, M\* did not pass its screen.

**Exploratory evidence, added after the verdict** (Section V-E), is not registered: it was specified after reading the registered outputs, in a plan whose hash we recorded ourselves and five amendments. Each comparator family's level, and M\*'s own, was tuned until it passed a screen on partitions that no method stratifies on directly (M\* itself had to drop from δ′ = 0.05 to 0.03). M\* was then infeasible, that is, had to back off its designed margin, in fewer decisions than every comparator family matched within the grid: by 8–38 percentage points on seven such partitions, and by 3–36 points when track speed and track age, which are related to M\*'s strata, are removed. The smallest gain, 3–4 points on that reduced screen, is against M\* without its course-change strata, and there M\* leaves more constraints exceeded at execution on one tracker (T3, +0.054 [0.043, 0.066] on the neutral screen); against the other families, exceedance at execution was similar. A fourth family, the conformal norm ball, still passes at the least conservative level we tried in most folds, so its larger gap is not a matched comparison. One-step progress differed by less than 0.02. M\* therefore keeps the planner on its designed margin more often; we do not claim that it makes the planner safer. M\* under-covers low-score and newly started tracks, up to about 0.09, an exploratory finding without family-wise control. Throughout, δ = 0.05 is a calibration level per relied constraint, not a safety target, and about half of all decisions keep some exceeded constraint (Section VI-C).

**Contributions:** (1) a *formal motivation* with elementary results: what a half-space chance-constrained planner consumes from a tracker's covariance, why NEES does not test it, and the price of single-scalar corrections (Section III); (2) *planner-matched calibration,* M\* (Section IV); (3) *a registered external test* in log replay on two trackers, with every pre-specified negative (Section V-D); and (4) *exploratory evidence* on what the calibration buys at matched validity and where it fails (Section V-E). Section II positions the work, and Section VI collects its limitations and what is not claimed.

## II. Related Work

**A. Chance-constrained planning with uncertain obstacles.** Under Gaussian uncertainty, chance-constrained control turns a linear constraint's violation probability into a margin along its normal, with risk allocated across constraints or fixed per constraint [Blackmore2011; Ono2008], also for Kalman-tracked moving obstacles with the collision region linearized to a half-space [Zhu2019]. Probabilistic collision checking and planning over uncertain obstacle predictions are treated in [DuToit2011; Hardy2013]. Driving-scale planners keep affine chance constraints under Gaussian-mixture predictions, tightened per mode by a quantile times a standard deviation [Nair2025; Ren2025], or use scenario- or risk-allocating MPC [deGroot2025; Mustafa2023]; others tighten the same constraints by a conformal radius [Lindemann2023], enforce a Mahalanobis keep-out on the whole covariance [Shah2026; Mohamed2025; Pouria2026], consume perception uncertainty through chance constraints [Li2024] or cost weights [Shi2026], or bound prediction uncertainty with reachable sets [Guo2025]. Whether the covariance supports the quantile the planner consumes is assumed, not tested.

**B. Where the covariance comes from.** Lidar 3-D multi-object tracking on nuScenes is dominated by Kalman-filter tracking-by-detection [Weng2020; Chiu2020; Li2023; Osterburg2026], with noise covariances fitted from training residuals [Chiu2020], tuned on tracking metrics [Osterburg2026], estimated from innovations in batch [Mehra1970; Zhang2020] or online [Sarkka2009; Huang2018; Jiang2024], or learned or scaled by detection confidence [Ulreich2024; LearnTrack2026]. Detector-side uncertainty is estimated [Feng2018; Meyer2020; Pan2020] but not passed to a tracker. Of the nuScenes tracker papers we found, only [Osterburg2026] reports a consistency statistic for its output covariance, and none certifies the extrapolated covariance a planner consumes.

**C. The limits of constant-velocity extrapolation.** Constant-velocity extrapolation is known in motion prediction to be biased on turning vehicles, which motivates turn-rate models, multiple-model filters [BlomBarShalom1988; Mazor1998; BarthFranke2010] and learned predictors [Djuric2020; PhanMinh2020] (survey: [Lefevre2014]), into which a tracker's state uncertainty can be propagated [Ivanovic2022]; learned models reduce cross-track error severalfold [Djuric2020].

**D. Assessing covariance consistency.** The NEES/ANEES and NIS χ² tests [BarShalom2001] penalize optimism and pessimism asymmetrically and depend on Gaussianity [Li2002], hold only for tuned filters [Chen2024], fail for mixture filters [Ahmed2024] and do not separate bias from scale [Yan2026]; a scalar test can pass while the whitened covariance is wrong [Forsling2025], and NEES-based auto-tuning optimizes the whole-vector statistic [Chen2018nees]. Forecast verification distinguishes calibration notions that do not imply one another [Gneiting2007], proposes directional checks [Ziegel2014] and makes calibration specific to the functional being forecast [GneitingResin2023].

**E. Conformal prediction and risk control.** Conformal prediction gives finite-sample marginal coverage under exchangeability, per category in its Mondrian form [Vovk2012; Bostrom2020], with conditional guarantees over richer covariate classes [Gibbs2025]; object-conditional validity is impossible in general [Vovk2012; Lei2014; Barber2021]. Conformal risk control extends it to bounded monotone losses [Angelopoulos2024; Bates2021]. Scarce classes can be pooled by clustering [Ding2023], hierarchical data handled by subsampling one observation per group [Dunn2023] or by a hierarchical form of exchangeability [LeeBarberWillett2026], and thresholds updated online [GibbsCandes2021]. Training-conditional coverage holds for split conformal but can fail for full conformal and jackknife+ [BianBarber2023]; high-probability variants bound the risk of one fitted rule [Bates2021; Angelopoulos2025LTT]. Under distribution shift, coverage needs reweighting or degrades [Tibshirani2019; Barber2023]. Items selected after seeing the data need selection-aware methods [JinCandes2023; Bao2024], which our relied-axis scoring does not have. In robotics, conformal regions around predicted trajectories drive MPC [Lindemann2023; Dixit2023; Lindemann2025], less conservatively over multiple steps in [Cleaveland2024]; conformal perception error feeds downstream planners and controllers [Yang2023; Zhang2025; DixitMei2024], conformal sets tighten state and input constraints [Natraj2026; Vlahakis2024], and [Su2024] conformalize detection noise inside a tracker.

**F. The closest methods, and what is new.** CGKF and CQKF [Weisman2026] certify joint coverage of a *filtered* state: CGKF by one conformal offset to a Kalman filter's χ² ellipsoid per time step, CQKF by one shared correction over learned quantiles along 128 random directions, with a one-sided score per direction; both are demonstrated on simulated systems without a planner. LUCCa [Marques2026a] scales a robot's one-step dynamics covariance by one Mahalanobis-score factor per learned partition for a sampling-based planner, arguing that one global factor is too coarse, which OCULAR [Marques2026b] shows in simulation. Polyhedral conformal sets [Chen2026] learn half-space orientations for a robust objective and share one radius; F-CROMS [Bao2026] selects among score models; conformal tube tightening [DSilva2026] tightens every polytopic constraint row by one conformal ellipsoidal tube radius. We instead control, per planner-observable stratum, the one-sided tail of a driving tracker's exported Gaussian along each constraint normal that a chance-constrained planner enforces and relies on, and replay the recalibrated covariance into that planner on real logs. None of the works we read does this; the conformal machinery itself is standard.

**G. Decision-aware calibration and evaluation.** Decision calibration asks that predictions be calibrated for the decisions made from them [Zhao2021; Sahoo2021; Kiyani2026; Tang2026; Noarov2025], and action-conditional guarantees condition on the chosen action [Zhu2026]. Conformal decision theory [Lekeufack2024] calibrates the decision itself, controlling a decision loss online; M\* instead calibrates offline the covariance a fixed planner consumes. Planner-centric metrics and objectives weigh detection, forecasting or training by their effect on a planner [Philion2020; IvanovicPavone2022; McAllister2022]; a better-calibrated predictor changed open-loop chance-constrained plans little on real driving data [IvanovicA2024]. nuPlan defines closed-loop non-reactive and reactive scores [Karnchanachari2024]. With ground-truth perception, [Shah2026] evaluate calibrated predictors in a chance-constrained MPC; in pedestrian replay, [Pouria2026] show that calibration, not displacement error, drives MPC success. Open-loop scores at logged states can disagree with closed-loop behavior [Dauner2023; Karnchanachari2024] and can be matched from ego status alone [Li2024Ego]. Demonstrating safety statistically needs far more driving than any study here [KalraPaddock2016]. Every nuPlan study we found uses ground-truth or noise-injected perception, not a real tracker's recorded covariance.

## III. Formal Motivation

The statements below are elementary, each with ingredients in print [Gneiting2007; Ziegel2014; Forsling2025]; they motivate the method but are not its guarantee (Section III-E). Theorem 1(b) and Propositions 3 and 4 are proved in Appendix A, the others in Supplement S8.

### A. Setting

**(M1) The planner's information.** At decision step k the planner holds I_k: the tracker's means μ̂_i and position–velocity covariances Σ̂_i ≻ 0, with class, size and yaw, and the ego state. A predictor gives mean m̂_i(t) and covariance V̂_i(t) at horizon t. For constant velocity (CV): m̂_i(t) = F_tμ̂_i and V̂_i(t) = F_tΣ̂_iF_tᵀ + Q(t), with F_t = [I₂, tI₂].

**(M2) The constraints.** For each evaluated tuple j = (candidate plan, object, horizon), the planner forms a unit normal a_j, offset b_j and multiplier c_j, and checks

  (TC)  a_jᵀm̂_j + c_j√v̂_j ≤ b_j,  v̂_j = a_jᵀV̂_ja_j,

with c_j = z_{1−δ} for a fixed per-constraint risk.

**(M3) The scores.** With X_j the realized position, U_j = a_jᵀ(X_j − m̂_j)/√v̂_j is the projected standardized error, N_j = (X_j − m̂_j)ᵀV̂_j⁻¹(X_j − m̂_j) the NEES, and τ_j = (b_j − a_jᵀm̂_j)/√v̂_j the realized threshold, with τ_j ≥ c_j when (TC) holds. The guarantee in (TC) is per step, per constraint and open loop.

### B. What a half-space planner consumes

**Remark 1 (Gaussian half-space reduction).** If Y ~ N(m, V), V ≻ 0 and a ≠ 0, then P(aᵀY > b) ≤ δ iff aᵀm + z_{1−δ}√(aᵀVa) ≤ b.

It underlies the planners of Section II-A [Blackmore2011; Ono2008; Zhu2019; Nair2025; Ren2025]. The planner's premise is that a_jᵀm̂ + z_{1−δ}√(a_jᵀV̂a_j) is a valid (1 − δ)-quantile of the true projected position, *for the normals the planner uses*; we ask whether a tracker's V̂ supports it.

**Definition 1 (decision-projected calibration).** For an I_k-measurable rule forming constraint instances, V̂ is *decision-projected calibrated at level δ* if P(U_j > z_{1−δ} | I_k) ≤ δ almost surely for every instance. For an I_k-measurable selection G with I_k-measurable instance weights, the *stratum form* is P(U > z_{1−δ} | G) ≤ δ. This is decision calibration [Zhao2021] for the loss class {1(a_jᵀy > b_j)}.

**Proposition 1 (premise).** (i) For an executed plan satisfying (TC), P(a_jᵀX_j > b_j | I_k) = P(U_j > τ_j | I_k), so the premise P(U_j > c_j | I_k) ≤ δ is sufficient for the per-constraint guarantee, and necessary only on active constraints. (ii) The stratum form is necessary for the premise, but not sufficient in general: a fair label splitting U ~ N(0, 1) into |N(0, 1)| and −|N(0, 1)| gives 0.01 marginally and 0.02 on one label at z_{0.99}.

### C. Why NEES does not test it

**Proposition 2 (plan-uniform criterion).** (aᵀe)²/(aᵀV̂a) ≤ eᵀV̂⁻¹e for every a ≠ 0. Hence P(N > c² | I_k) ≤ δ implies P(U > c | I_k) ≤ δ for every I_k-measurable direction.

Certifying through N costs a margin ratio of 1.30 in two dimensions at δ = 0.01 under Gaussian truth. It is the matched criterion for Mahalanobis keep-out planners [Shah2026; Mohamed2025; Pouria2026]; a half-space planner needs less.

**Theorem 1 (NEES and the premise do not imply each other).** At δ = 0.01:
- **(a)** Truth N(0, I) and export diag(2, 2/3) give E[N] = 2, exactly consistent in mean, yet the risk along the second axis is 0.0288.
- **(c)** Truth diag(1, 4) and export I₂ give a calibrated binding direction e₁, yet E[N] = 5. Matching the average NEES globally (×2.5) leaves a risk of 0.00012 along e₁, where 0.01 was required.

Case (b), a whole-vector χ² test passed exactly while some direction is above δ, is stated and proved in Appendix A, and case (d), heavy tails, in Supplement S8. Case (c) is the pattern of Section V-B.

### D. The price of a single scalar

Where directions need different corrections, any single multiplier or variance factor fixing the worst direction over-pays elsewhere, by an excess computable per tuple (S8-Proposition 5 and S8-Theorem 2): with lateral and longitudinal constraints, the smallest variance factor bringing the lateral tail to δ wastes longitudinal margin (the "price" of Section V-B). The claim is that one knob over-pays where needs differ, not that no scalar fixes the lateral tail.

### E. What this section licenses

Proposition 1 is conditional on I_k and per constraint. Section IV instead certifies a marginal, per-stratum exceedance rate weighting each **log** equally, on a proxy calibration population (Section IV-G). Such a rate is not measurable at an instance's information and neither implies nor is implied by the premise: under exact conditional calibration it can exceed δ (0.0625 at δ = 0.05 in an exact example, Supplement S8.2). The formal results therefore motivate *what* to calibrate, one-sided tails along the planner's constraint normals, stratified by what it observes; Sections V-C to V-E test it empirically.

## IV. Method: Planner-Matched Calibration (M\*)

M\* is a post-processor between tracker and planner (Fig. 1), fitted offline on logs with ground truth and deployed online as a recalibrated covariance that the planner consumes unchanged. Its parts are published: conformal risk control (CRC) [Angelopoulos2024], Mondrian, per-category validity [Vovk2012], one score per exchangeable unit [Dunn2023] and conformal inflation of a Kalman-filter confidence region [Weisman2026] and of a dynamics covariance consumed by a planner [Marques2026a]. **What M\* adds** is the **calibration population**, the constraints a chance-constrained planner actually enforces and relies on, rather than a fixed audit population, with **scoring in constraint coordinates** (IV-A); **strata** the planner observes, with a count-based fallback (IV-B, IV-D); and a **deployable covariance** that reproduces the calibrated margins exactly (IV-E). M\* grew out of DP-SCRC, the same machinery fitted on a fixed in-path audit population; a pre-specified planner study found that the planner relied on constraints outside that population, where DP-SCRC was significantly above δ (Supplement S1–S2).

### A. The calibration population

The planner is the chance-constrained speed planner of Appendix B (Section V-A). For a track and one of its two box axes a (longitudinal a_L or lateral a_T, from the estimated yaw), the *gap* at a check time is the clearance along a between the buffered ego footprint and the object's box; a (track, check time) pair is safe under a margin m if some axis has gap ≥ m. A pair is *enforced* if, at the arm-independent reference margin 0, some candidate plan satisfies it and so would an ego held at its current position (a conflict the other agent brings to a stopped ego is not the planner's to resolve). Only tracks with a detection score ≥ 0.4, within 60 m and not behind the ego count.

**Items.** At every decision state of a log (every keyframe but the first and the last, at the logged ego's position and speed) and every calibrated check time h ∈ {0.5, 1, 1.5, 2} s, each enforced pair whose object has an annotation at k + h (≥ 1 lidar point, not inside a bicycle rack) gives one item per object axis that separates the pair at the **reference ego pose**:

  D = s·aᵀ(X − m̂),  sd = √(aᵀΣ̂_h a + σ_a²),  U = D/sd,

with s the side of separation (positive D: the object came closer than predicted), m̂ and Σ̂_h the tracker's predicted mean and 2 × 2 covariance at h, X the annotated center and σ_a = 0.10 m an assumed annotation noise. A margin m along a is *exceeded* when D > m.

**The relied axis and the scored populations.** Fitting uses every separating axis of every enforced pair at the reference pose. Scoring (Section V) uses, per enforced pair, the *relied axis* under **each arm's own chosen plan**: the axis with the largest slack (gap minus that arm's margin), kept if it separates (gap > 0) and the plan satisfies it at the arm's full margin. P_rel holds all such records, P_near those with pair gap ≤ 5 m, P_ip those of in-path tracks and P_nip those of other tracks (scope only). The scored sets therefore differ between arms: on Argoverse 2 T1, P_rel holds 534,846 records under M\* and 356,260 under B3, against 537,924 relied items at the reference pose (Supplement S9.11).

**The reference pose: a proxy.** Fitting needs a reference ego progression before any arm has chosen a plan; M\* uses the **logged** ego pose at t_k + h, which a driver chose knowing the true object positions, so the calibration population is a proxy defined with the logged ego trajectory (Section IV-G; Section V-E(d) refits M\* at two references that use nothing after t_k).

### B. Strata

The strata use features the planner observes at decision time: **group** (car; pedestrian; two-wheeler; large vehicle); **range** of the predicted object from the ego's constant-turn-rate-and-velocity (CTRV) predicted center at k + h (< 20 m, 20–40 m, ≥ 40 m); **axis** (longitudinal or lateral); and **course-change state,** from the track's own exported positions: *static* if speed < 1.0 m/s, otherwise *new* if the turn rate is undefined, otherwise *turning* if |ω̂| ≥ 0.10 rad/s, otherwise *straight*. Level 0 has 4 × 3 × 2 × 4 = 96 strata; the coarser levels are L1 = group × range × axis, L2 = group × axis and L3 = axis. Fitted separately per check time and for in-path and other tracks, M\* has 192 thresholds per check time. The taxonomy is fixed in advance; no partition is learned.

### C. Per-stratum conformal risk control, with the log as the unit

**The exchangeable unit** on Argoverse 2 is the log, in fitting, cross-fitting and the bootstrap. The nuScenes development fits used the 20 s scene; scenes cut from one drive are dependent, so there Proposition 3 holds only as far as scenes are exchangeable, and an exact example shows it can fail (2/31 = 0.0645 at δ = 0.05; S8-Remark A.5), one reason the nuScenes evidence is development evidence (its bootstraps resample whole drives).

For stratum g and threshold c, the *log loss* L_g(Z; c) is the share of log Z's items in g with U > c: non-increasing and right-continuous in c, in [0, 1], and 0 for c ≥ max U. With n calibration logs that contain g,

  ĉ_g = inf{c : (n/(n + 1))·(1/n)Σ_i L_g(Z_i; c) + 1/(n + 1) ≤ δ},

and the deployed margin is ĉ_g·sd. The rule is evaluated in exact rational arithmetic, so the threshold depends only on the multiset of logs.

**Proposition 3 (per-stratum validity, log unit; proof in Appendix A).** Let the logs Z₁, …, Z_m and Z_test be i.i.d., the item map (tracker, predictor, strata and reference rule) fixed outside the evaluation logs, and each log contain an item in g with positive probability. If the N ≥ 19 calibration logs with an item in g are used and Z_test has an item in g, then E[L_g(Z_test; ĉ_g) | N] ≤ δ = 0.05: an item drawn uniformly from the test log's stratum-g items exceeds ĉ_g with probability at most δ. The same holds for each cross-fitted fold (Appendix A, Corollary A.4).

The bound is marginal over the calibration logs, not a bound for one fitted rule: in a simulation at 300 calibration logs the expected risk is 0.045, but the risk of a single fitted rule exceeds δ in about a quarter of calibration draws (Appendix A). **The sample floor:** a finite ĉ_g needs N ≥ 1/δ − 1 = 19 logs, and 99 at δ = 0.01; smaller levels cannot be certified by this construction with fewer logs (S8-Remark 5).

### D. Count-based fallback

A level-0 stratum with fewer than 19 calibration logs takes the threshold of the first coarser cell on its chain L0 ⊂ L1 ⊂ L2 ⊂ L3 with at least 19.

**Proposition 4 (fallback; proof in Appendix A).** (i) A stratum assigned its own threshold keeps Proposition 3, conditionally on that assignment. (ii) A stratum g assigned a coarser cell C's threshold is covered only through C: a test log's share of C-items above ĉ_C has expectation at most δ, given C's membership vector and a test log containing C. Nothing is asserted for g's own items, for the deployed loss over C, given that the test log contains g, or given g's fallback event (an exact counterexample gives 0.0481 for C overall but 0.0536 given that g falls back). (iii) The assignment depends on the data only through counts, so the deployed rule is a fixed map from tracker-observable features to thresholds.

### E. The deployable covariance

**Proposition 5 (deployable covariance).** For the estimated box axes a_l and a_t and α_l, α_t > 0, let A = α_la_la_lᵀ + α_ta_ta_tᵀ and Σ̃ = A(Σ̂ + σ_a²I)A. Then Σ̃ ≻ 0 and aᵀΣ̃a = α²(aᵀΣ̂a + σ_a²) on each axis. With α = max(ĉ, ε)/z_{1−δ}, ε = 10⁻³, a planner applying z_{1−δ}√(aᵀΣ̃a) applies exactly ĉ·sd (or ε·sd) along each object axis. A planner normal that is not an object axis receives a mixture of the two corrected axes, which no certificate covers.

### F. Algorithm

Algorithm 1 in Appendix B gives the steps. On Argoverse 2 each of 5 log folds is calibrated on the other 300 logs (cross-fitting).

### G. What the theory covers, and what it does not

No result in this paper bounds exceedance on the scored relied records; that is measured (Section V).

**Covered.** Within one dataset, cross-fitted M\* has Proposition 3's marginal per-stratum bound for its own-threshold strata *on its calibration items*, since logs are exchangeable and the item rule is the same in calibration and test. An exploratory check added after the verdict (amendment A3) agrees on Argoverse 2: on its own calibration items, cross-fitted M\* is flagged in none of its 93 (T1) and 92 (T3) evaluable own-threshold strata, with pooled exceedance 0.043 and 0.042, and 0.7 % of items in fallback strata; of the scored in-path relied records, however, 7.5 % (T1) and 7.6 % (T3) fall in fallback strata.

**Not covered** (Supplement S8.7): **relied-axis selection** (the scored records are a subset selected by gap, under each arm's own plan); **the proxy population** (Proposition 1 and S8-Proposition 3 need every ingredient of the constraint to be measurable at I_k, and the logged reference pose is not); **pooled and fallback cells** (covered only as in Proposition 4(ii)); **one deployed rule** (cross-fitting estimates the risk averaged over five fold rules, not a bound for the single rule a deployment would fit on all logs); and **the premise itself** (Section III-E). The registered test (Section V-D) and the exploratory analyses (Section V-E) check these parts empirically; they do not prove them.

### H. Comparators

All arms are margins along an object axis. **The registered comparator set K** (Section V-D) was fixed on development data: **B0**, the raw covariance, 1.645·sd; **B1**, NEES-scaled, k = ANEES/2 per group × range [BarShalom2001; Osterburg2026]; **B3**, the largest of M\*'s thresholds, at least M\*'s margin on every item; **B4**, one pooled CRC threshold per check time, the analogue of the per-time-step conformal inflation of [Weisman2026] and of a single global factor [Marques2026b]; **B6**, M\* without course-change strata; **B9**, a norm-ball CRC radius [Lindemann2023; Dixit2023]; and **RETUNED**, B0 rescaled to a pooled 5 % on the training folds. **Exploratory arms** (RETUNED-HK1, B4, B6 and B9 at stricter levels, B5, B7, B8 and a re-fitted process noise) are defined in Section V-E.

## V. Experiments

### A. Data, stack and planner

**Data.**
- **Argoverse 2** [Argoverse2], the registered test: 375 logs of the Sensor dataset, namely 225 training logs held out from our detector by a seeded permutation and the 150 validation logs. Each log is one drive segment of about 15 s with 3-D annotations, used at 2 Hz.
- **nuScenes** [Caesar2020], development only: 850 scenes of about 20 s, annotated every 0.5 s and cut from 68 drives; train and validation do not share a drive.

**Detectors.** On Argoverse 2, CenterPoint [Yin2021] in the LT3D code base [Peri2022], trained by us on the other 475 Argoverse 2 training logs with the public configuration, for 2 class-balanced epochs [Zhu2019cbgs] (set by a compute cap) against the public checkpoint's 20. On nuScenes, a CenterPoint checkpoint trained on nuScenes train, so detections on train are in-sample; its exact checkpoint is not recorded (Supplement S9.15).

**Trackers** (Table I): **T1,** CANMOT [Osterburg2026], an extended Kalman filter with a constant-velocity model for every class; **T3,** Poly-MOT [Li2023], as configured in CANMOT's `paper/baseline/poly_mot` experiment (the original Poly-MOT uses a bicycle model for bicycles and motorcycles); and **AB3DMOT** [Weng2020], the LT3D implementation with its defaults, a descriptive third tracker on Argoverse 2. All keep their nuScenes noise parameters and run at 2 Hz on Argoverse 2.

**Extrapolation.** The 2 s covariance is each tracker's own filter prediction repeated over the horizon without measurement updates: a constructed open-loop extrapolation, since the tracker's process noise was tuned for one-step association.

**Matching.** Tracks are matched to annotations by Hungarian assignment within 2 m; certificates cover matched true positives only (Section VI-F).

**The planner** (summary and Algorithm 2 in Appendix B; full specification in Supplement S9). The ego follows its logged path and chooses its speed among 32 accelerate-then-brake candidates (some never accelerate, and four are duplicates) and an emergency stop; only the ego's footprint is buffered (0.5 m). Every 0.25 s to 2 s, each tracked object must be kept apart from the ego along some box axis by at least the arm's margin; only *enforced* pairs bind (Section IV-A), and the candidate with the largest mean progress that satisfies every enforced constraint is chosen.
- **Infeasible decisions.** If no candidate satisfies them at the arm's full margin, the decision is *infeasible*: the planner backs its designed margin off, to 0.75, 0.5, 0.25 and 0 of its value, and takes the emergency stop only if even the buffered ego and the object's box cannot be kept apart. "Infeasible" therefore means "designed margin backed off", not "no progress".
- **Decision mode,** used for every comparison: one open-loop decision per keyframe from the logged ego state, with the plan leashed so that it never gets ahead of the logged ego; every arm is scored on the constraints it relied on under its own chosen plan.

**Table I. Trackers.**

| Tracker | Motion model | Noise | Tuned on |
|---|---|---|---|
| T1 CANMOT `paper/local/canmot/sc` | EKF, constant velocity, Q rotated into the box frame | Q by Bayesian optimization for AMOTA; R the sample covariance | nuScenes validation (Q), trainval (R) |
| T3 Poly-MOT `paper/baseline/poly_mot` (CANMOT config) | CTRA EKF for car, bus, pedestrian, truck; linear CA for bicycle, motorcycle, trailer | its own Q and R, hand-set (CTRA Q the identity) | association on nuScenes validation |
| AB3DMOT (LT3D) | linear constant velocity, one step per frame | LT3D defaults: Q the identity with 0.01 on velocities; R the filter library's default identity | not re-tuned (set for 10 Hz use) |

The nuScenes study also used a second CANMOT setting (T2, data-fitted Q) in the method stage (Supplement S1).

### B. Motivation: a mis-shaped extrapolated covariance

**Design.** A pre-specified study measured the one-sided tail of the error along the toward-ego box axes of in-path cars, at 2 s, under T1, a CANMOT tracker with a constant-velocity model, on the 700 nuScenes training scenes; the predictor is the tracker's own state and covariance extrapolated 2 s. Its plan was frozen with its code before its outcomes were computed (one pre-freeze check previewed the decision; Section VI-D). This is an *audit* population (Supplement S1), not the planner's relied constraints: it shows that the covariance is mis-shaped, and that the standard check sends the correction the wrong way.

**Results (Table II).** Laterally, the toward-ego margin is exceeded in 19.4 % (< 20 m) and 27.2 % (20–40 m) of items, against a nominal 5 % (estimate-oriented, record-weighted rates; Table II also gives scene-weighted ones). **Truth-oriented,** with the side of the ego taken from the true position so that the orientation artifact is removed, they are 15.4 % and 22.8 %. Longitudinally, the margin is exceeded in 0.4 % and 1.1 %: the covariance is too wide along the box. The NEES-guided scalar leaves the lateral tail at 13.0 % and 17.2 %, and any single variance factor that fixes the lateral tail adds 10–12 m of unneeded longitudinal margin (the "price" of Section III-D: 11.61 m and 10.34 m, one-sided 97.5 % lower bounds 9.81 m and 8.24 m).

**Table II. Decision cells of the nuScenes diagnosis: 2 s extrapolation, in-path cars, nuScenes train, σ_a = 0.10 m; one two-sided 95 % sup-t band over four cells.** E is record-weighted (share of items; with the band and the verdict) or scene-weighted (mean of per-scene shares); Argoverse 2 rates are log-weighted.

| Cell | E estimate-oriented, record [band] | E estimate-oriented, scene | E truth-oriented, record [band] | E truth-oriented, scene | Items / scenes (estimate-oriented) | Threshold max(0.05, E⁰) | Verdict |
|---|---|---|---|---|---|---|---|
| car < 20 m, lateral | **0.194** [0.152, 0.236] | 0.141 | 0.154 [0.116, 0.193] | 0.098 | 3,396 / 442 | 0.0775 | FAILS |
| car 20–40 m, lateral | **0.272** [0.205, 0.338] | 0.245 | 0.228 [0.162, 0.293] | 0.175 | 1,229 / 219 | 0.0816 | FAILS |
| car < 20 m, longitudinal | 0.004 [0.002, 0.007] | 0.008 | – | – | 8,038 / 529 | 0.0646 | OVERCOVERS |
| car 20–40 m, longitudinal | 0.011 [0.004, 0.017] | 0.019 | – | – | 3,522 / 345 | 0.050 | OVERCOVERS |

**What "lateral" means.** "Lateral" is the tracked box's lateral axis, from the tracker's estimated yaw, and CANMOT's box headings are often wrong: in a project audit of the nuScenes planner population, records produced by T1 but not by T3 came mostly from boxes more than 20° off the annotation (median 40° in the in-path car lateral straight cell), while Poly-MOT's headings were off by a median of about 1°. A box rotated by 40° turns part of the world's longitudinal error into "lateral" error. **In the diagnosis cells,** a post-registration check, specified before it was computed (amendment A1 of the exploratory plan, Section V-E), rebuilt the diagnosis items exactly and measured each item's heading error against its annotation: 35–39 % of lateral items come from boxes more than 20° off, and they carry 41–49 % of the lateral exceedances. **Heading error explains part of the failure, not all of it** (amendments A1 and A4; pointwise scene-bootstrap intervals; Supplement S6.10 and S6.20). Restricted to boxes within 5° of the annotation, the lateral exceedance is still 0.10–0.23, above every cell's threshold (0.05 truth-oriented; 0.0775 and 0.0816 estimate-oriented, Table II). Measured along the annotated box's own lateral axis, it stays above its threshold below 20 m (0.124 estimate-oriented, 0.089 truth-oriented), but at 20–40 m the intervals include the thresholds (0.108 [0.074, 0.143] against 0.0816; 0.064 [0.040, 0.093] against 0.05). The longitudinal cells stay at or below 0.02.

**Scope of the finding.** It is a constant-velocity effect: the extrapolation under-predicts the lateral spread of turning vehicles (Section II-C). Under T3 (Poly-MOT, CTRA for cars) the raw covariance is far too wide rather than mis-shaped (mean lateral margin 32.1 m). What is new is not the under-dispersion itself but its consequence at the tracker–planner interface: the standard NEES check sees the inflated average and recommends inflating every direction, including the already over-covered longitudinal one (Theorem 1(c)).

**Partial replication on Argoverse 2 (H8, registered).** On T1 under the raw covariance, the 20–40 m lateral cell fails in both versions (0.214 [0.122, 0.306] against E⁰ = 0.090, and truth-oriented 0.144 [0.068, 0.220]); the < 20 m lateral cell fails only estimate-oriented (0.147) and is consistent truth-oriented (0.088 [0.046, 0.130]); and the 20–40 m longitudinal cell, outside H8's definition, also fails, at 0.158 [0.106, 0.210], which the nuScenes diagnosis did not show. The lateral under-coverage thus replicated where it was largest. The longitudinal over-coverage, and with it the "price" of a lateral-fixing scalar, did not replicate at 20–40 m, where both axes under-cover; H8 is therefore a partial replication.

### C. Development on nuScenes (exploratory)

M\* and every rule of the registered test were developed on 840 nuScenes scenes (68 drives; the 850 of Section V-A less the 10 nuScenes-mini development scenes): the recorded covariances of T1 and T3 replayed into the planner of Appendix B in decision mode, with fits cross-fitted over 5 scene folds and a drive-cluster bootstrap. This is development evidence, reported in full in Supplement S2.2: the fits use the scenes M\* was built on, T1's process noise was tuned on nuScenes validation, and the gates are ours.

M\* was not shown above δ in any cell, power-qualified family or pooled cell of P_rel, P_near or P_ip, on either tracker. **The raw covariance is mostly too wide on this population:** B0's pooled P_rel exceedance is 0.026 (T1) and 0.002 (T3), and the in-path lateral cars of Section V-B are 0.4 % of relied items on the validation split (T1, classes covered by the learned predictor, 2 s). M\* therefore mostly *narrows* margins, recovering feasibility where the raw covariance is too wide while holding the exceedance near δ where it is too narrow; on T3 the narrower margins cost real violations. **Per constraint is not per decision:** about one decision in three had some relied constraint exceeded (V2 0.358 and 0.351), 0.04–0.05 above the per-track reference 1 − 0.95^{n_tracks}, and calibrating one scalar on the union loss (M\*J) brings V2 to about 0.05, at +0.31 and +0.39 in infeasible-decision rate.

The registered test was designed to check these patterns on new data (the validity of M\*, how often it backs off its margin compared with the comparators, and the cost of the strata), accepting that the comparators retained by the screen might be only conservative ones (Section V-D).

### D. The registered test on Argoverse 2

**1. Registration.** The plan was frozen on 6 Nov 2026, 20:08:13 UTC, binding 354 files by hash, and registered on OSF under embargo at 20:31 UTC (https://osf.io/v8qfk/; reviewers receive a view-only link; Supplement S7 outlines the frozen plan). Reading annotation positions after a decision time requires a deposit record naming the registration, and every guarded run is logged in a hash chain. **This blinding is procedural, not technical** (Section VI-D): the detector port was checked before the freeze on the 150 validation logs, which are part of the test set.

**2. Data, detector and trackers** are those of Section V-A (configurations in Supplement S9). Our detector's 26-class AP at 50 m is 0.425 on validation and 0.415 on the held-out logs, against 0.469 for the public checkpoint.

**3. Design.** M\* is re-fitted within Argoverse 2 by 5-fold cross-fitting over logs (Section IV); the comparators K = {B0, B1, B3, B4, B6, B9, RETUNED} were fixed on development data. **The primary claim, H1,** is Form B on both trackers: M\* passes the screen and is less often infeasible than every comparator not itself shown above δ (the comparison set V_t). The statistical design is explained after this item in plain terms, the terminology table (Appendix C) defines every label, and the secondary claims H2–H10 are listed in Section V-D8. Two properties of this design, stated before the results:
- **The comparison set may be uninformative.** B3's margin is at least M\*'s on every item, and on development the screen retained only B3 (T1) and B0 and B3 (T3).
- **The screen's cells are M\*'s own strata** (group × axis × course-change state, pooled over range). B0, B1, B4, B6, B9 and RETUNED, not stratified by course-change state, can pass a course-change cell only by being conservative there, so part of their flags follows from the choice of cells. Section V-E(b) screens every arm on partitions no method stratifies on directly.

**The statistical design of the registered test, in plain terms.**

*What is measured.* For one arm (a margin rule) on one tracker, every relied constraint of every decision gives one record: did the realized error along the relied axis exceed the arm's margin? Records are grouped by population (P_rel, P_near, P_ip) and into cells (class group × axis × course-change state, pooled over range). A cell's exceedance rate is the mean over logs of each log's share of exceeded records (logs without a record in the cell are skipped); all intervals resample whole logs (B = 40,000).

*The screen: three checks on M\*, per tracker and population.*
1. **No flag.** A cell is *flagged* ("shown above δ") when the lower end of a one-sided simultaneous 95 % sup-t log-bootstrap band over all evaluable cells (records from ≥ 39 logs) lies above δ = 0.05; the same rule applies to the power-qualified family and to the pooled cell.
2. **Floors.** ≥ 6 *power-qualified* cells (a planted rate of 0.15 in the cell alone would be flagged with probability ≥ 0.8) on P_rel and P_near; ≥ 1 evaluable cell on P_ip.
3. **HK1c.** The pooled rate's upper bound at nominal 99.5 % is ≤ δ + 0.03 = 0.08: the one check that rejects something.

*Form B, H1 and GO.* H1 spends one-sided 0.025 in two halves. A comparator leaves the comparison set V_t only if flagged in any of its 9 conditions at one-sided 1 − 0.0125/9 = 0.99861 each (the removal half, 0.0125); M\* must then be less often infeasible than every member of V_t, by a paired log-bootstrap bound at one-sided 0.0125/|V_t| each (the superiority half, 0.0125). **H1** = Form B on both trackers, an intersection–union test in which every component must reject [Berger1982]; **GO** = H1 with every input present and of verified provenance.

**What GO controls, and what it does not.** A pooled exceedance above 0.08 in some population would have to pass HK1c, at nominal 0.5 % per population (in a post-registration simulation at Argoverse 2's cell sizes, the HK1c bound missed a true pooled rate of δ in 0.9–2.7 % of data sets; Supplement S6.4). A claim that M\* backs off less often than a comparator that is truly no worse needs a false removal of that comparator (budget 1.25 %; simulated at most 0.3 %) or a false superiority decision (1.25 %, Bonferroni over V_t). Passing when a single cell is above 0.05 is not controlled: the screen detects 0.15 reliably, 0.10 often not (median power at 0.10: 0.11–0.61 by population). Passing licenses "not shown above 5 % at the stated power, with pooled bounds ≤ 0.055", never "valid" in the sense "at most 5 %"; Form B adds evidence of less back-off only against the comparators left in V_t.

*Secondary claims.* Family S (H2, H3, H4, H6b, H10) is tested by Holm's procedure [Holm1979] at 0.025 only after H1 holds, with approximate bootstrap p-values (k + 1)/(B + 1); H8 has its own 0.025; H6a and H7 are no-flag statements like the screen ("does not hold" means a cell was flagged).

**4. The verdict.** The frozen analysis ran once (7 Nov 2026, B = 40,000) and passed its completion check. **The verdict of record is GO.** The verdict sentence fixed before the run reads:

> In a registered, one-shot test on 375 Argoverse 2 logs not used to train the detector, with M\* re-fitted within Argoverse 2, no evaluable cell of M\* was shown above δ = 0.05 on either tracker (one-sided simultaneous 0.95; power ≥ 0.8 against a per-cell exceedance of 0.15 in the power-qualified cells). Its pooled 99.5 % upper bounds (nominal, approximate) were at most 0.055, and it was less often infeasible than every comparator not shown above δ; on CANMOT and Poly-MOT these were only comparators at least as conservative by construction or infeasible in most decisions.

**Three qualifications:**
- **The bounds are approximate.** The nominal "99.5 %" pooled bounds covered 0.967–0.988 on average on development, and 0.949 in the worst cell. The "95 %" simultaneous cell bounds covered 0.78–0.87 on development, and only 0.38–0.55 in a post-registration simulation at Argoverse 2's cell sizes (Section V-E(c)).
- **The retained comparators were uninformative.** On T1 the only comparator not shown above δ was B3, conservative by construction and infeasible in 0.969 of decisions (M\* − B3 = −0.783); on T3 they were B0 and B3, infeasible in 0.858 and 0.941 (M\* − B0 = −0.611; M\* − B3 = −0.694). Form B is therefore no evidence that M\* backs off less often than an informative comparator (for those, see item 6 and Section V-E).
- **The result is per relied constraint, not per decision,** and δ = 0.05 is a calibration level, not a safety target (Section VI-C).

**Table III. The registered screen for M\* on Argoverse 2** (375 logs, decision mode; HK1c bound nominal 0.995).

| Tracker | Population | Evaluable cells | Cells flagged | Power-qualified family (record share) | Pooled E [LB] | Floor | HK1c UB (≤ 0.08) |
|---|---|---|---|---|---|---|---|
| T1 | P_rel | 27 | 0 | 19 (0.987) | 0.044 [0.041] | 19 ≥ 6 | 0.048 |
| T1 | P_near | 16 | 0 | 9 (0.907) | 0.038 [0.030] | 9 ≥ 6 | 0.047 |
| T1 | P_ip | 8 | 0 | 5 (0.786) | 0.040 [0.030] | 8 ≥ 1 | 0.055 |
| T3 | P_rel | 27 | 0 | 19 (0.988) | 0.043 [0.040] | 19 ≥ 6 | 0.047 |
| T3 | P_near | 16 | 0 | 8 (0.883) | 0.032 [0.026] | 8 ≥ 6 | 0.041 |
| T3 | P_ip | 8 | 0 | 5 (0.797) | 0.040 [0.032] | 8 ≥ 1 | 0.052 |

No family cell and no pooled cell was flagged.

Weighted by record rather than by log, M\*'s pooled exceedance is 0.045 / 0.032 / 0.036 on T1 (P_rel / P_near / P_ip) and 0.044 / 0.030 / 0.035 on T3 (read from the record after review, over the records in evaluable cells: 99.7 %, 98.4–98.5 % and 89 % of those of P_rel, P_near and P_ip).

**5. What the screen can and cannot show.** The median per-cell power at a planted exceedance of 0.10 was 0.61 (T1) and 0.58 (T3) on P_rel, 0.11–0.12 on P_near and about 0.22 on P_ip: a cell at 0.10 would usually pass on P_near and P_ip, and often on P_rel. Five P_rel cells per tracker lack 0.80 power even against 0.20. M\*'s largest simultaneous cell upper bound, U_max, was 0.127 / 0.118 / 0.129 on T1 (P_rel / P_near / P_ip) and 0.122 / 0.110 / 0.157 on T3; exceedances of that size are not excluded in individual cells (Fig. 2). **The in-path population,** the one the diagnosis concerns and the most safety-relevant, has the weakest evidence: its floor is one evaluable cell, its largest point estimate, 0.099 (T3, in-path car lateral straight), is in the cell with U_max = 0.157, and its HK1c bound, 0.055 on T1, is the largest of the six (Table III). For in-path constraints the test shows no pooled excess but cannot exclude cells at two to three times δ (other interval methods: Section V-E(c)).

**6. Operability against the informative comparators** (Table IV, Fig. 3).
- **B6** (M\* without course-change strata) was shown above δ in five P_rel cells on each tracker and left V_t. Yet M\* was **more** often infeasible than B6, by +0.021 [0.003, 0.039] on T1 and +0.018 [0.009, 0.027] on T3 (two-sided 95 %): the course-change strata bought calibration in course-change cells (by design, Section V-D3) at a cost of about 0.02 in infeasibility (once tuned to pass, B6 needs more back-off than M\*: Sections V-E(a) and VI-A).
- **B4** (one pooled conformal threshold) was shown above δ in 9 (T1) and 6 (T3) P_rel cells; M\* − B4 = −0.016 on T1 (upper bound at H2's Holm level, one-sided 0.995: 0.011) and −0.069 on T3 (−0.049). H2 confirms only that M\*'s price against B4 is below 0.03, not that M\* is better.
- **Matched validity,** how often a comparator family backs off once tuned to pass a screen, was beyond Form B. Its one piece pre-specified as descriptive, B0 rescaled on the training folds until it passes (RETUNED-HK1), found no qualifying scale in any fold on either tracker; the most conservative scale, ×8, was then used, as the plan specified, and was infeasible in 0.781 (T1) and 0.977 (T3) of decisions. Section V-E(a) extends this to every family and to a neutral screen.

**Table IV. Per arm and tracker on Argoverse 2** (decision mode; P_rel cells flagged at one-sided 0.95 for M\*, 0.99861 for comparators; V2 with its per-track reference; mean margins on each arm's own relied pairs, not comparable across arms; the last four columns are read from the CSVs of record and reported after review (amendment A3): progress ratio, mean executed back-off level λ, V2_exec (some relied constraint exceeded at the executed margin) and the share of decisions whose smallest enforced gap is below 1 m).

| Tracker | Arm | Screen | P_rel | P_near | P_ip | Flagged | Infeasible | V2 (ref.) | V2_viol | Margin lat / long (m) | Progress | Mean λ | V2_exec | Min gap < 1 m |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T1 | M\* | met | 0.044 | 0.038 | 0.040 | 0 / 27 | 0.186 | 0.491 (0.441) | 0.016 | 0.57 / 1.22 | 0.972 | 0.897 | 0.551 | 0.296 |
| T1 | B0 | – | 0.034 | 0.026 | 0.050 | 3 / 26 | 0.371 | 0.395 (0.440) | 0.022 | 1.47 / 2.32 | 0.961 | 0.795 | 0.515 | 0.270 |
| T1 | B1 | – | 0.013 | 0.016 | 0.030 | 1 / 26 | 0.513 | 0.188 (0.436) | 0.019 | 3.13 / 4.34 | 0.957 | 0.700 | 0.375 | 0.272 |
| T1 | B3 | in V_t | 0.002 | 0.005 | 0.001 | 0 / 24 | 0.969 | 0.033 (0.411) | 0.007 | 10.49 / 12.29 | 0.974 | 0.128 | 0.745 | 0.321 |
| T1 | B4 | – | 0.054 | 0.038 | 0.077 | 9 / 27 | 0.202 | 0.520 (0.441) | 0.026 | 1.02 / 1.60 | 0.972 | 0.888 | 0.578 | 0.288 |
| T1 | B6 | – | 0.047 | 0.041 | 0.047 | 5 / 27 | 0.165 | 0.501 (0.441) | 0.023 | 0.54 / 1.73 | 0.971 | 0.911 | 0.548 | 0.287 |
| T1 | B9 | – | 0.012 | 0.005 | 0.020 | 1 / 25 | 0.693 | 0.158 (0.434) | 0.014 | 3.59 / 3.59 | 0.955 | 0.505 | 0.527 | 0.268 |
| T1 | RETUNED | – | 0.029 | 0.023 | 0.047 | 2 / 26 | 0.407 | 0.361 (0.440) | 0.022 | – | 0.960 | 0.771 | 0.501 | 0.270 |
| T3 | M\* | met | 0.043 | 0.032 | 0.040 | 0 / 27 | 0.247 | 0.496 (0.441) | 0.018 | 0.65 / 1.93 | 0.973 | 0.858 | 0.580 | 0.297 |
| T3 | B0 | in V_t | 0.004 | 0.003 | 0.003 | 0 / 25 | 0.858 | 0.072 (0.431) | 0.013 | 5.44 / 6.66 | 0.965 | 0.302 | 0.604 | 0.292 |
| T3 | B1 | – | 0.016 | 0.010 | 0.021 | 0 / 25 | 0.666 | 0.228 (0.433) | 0.024 | 2.95 / 3.58 | 0.968 | 0.495 | 0.575 | 0.284 |
| T3 | B3 | in V_t | 0.001 | 0.001 | 0.000 | 0 / 24 | 0.941 | 0.030 (0.409) | 0.009 | 8.83 / 10.57 | 0.972 | 0.182 | 0.678 | 0.308 |
| T3 | B4 | – | 0.061 | 0.044 | 0.112 | 6 / 26 | 0.315 | 0.572 (0.441) | 0.049 | 1.07 / 1.39 | 0.969 | 0.802 | 0.643 | 0.288 |
| T3 | B6 | – | 0.049 | 0.036 | 0.044 | 5 / 27 | 0.229 | 0.529 (0.441) | 0.023 | 0.63 / 2.08 | 0.973 | 0.866 | 0.597 | 0.295 |
| T3 | B9 | – | 0.014 | 0.005 | 0.016 | 1 / 26 | 0.663 | 0.177 (0.435) | 0.018 | 3.29 / 3.29 | 0.959 | 0.534 | 0.523 | 0.269 |
| T3 | RETUNED | – | 0.026 | 0.014 | 0.045 | 2 / 25 | 0.611 | 0.316 (0.438) | 0.028 | – | 0.960 | 0.580 | 0.568 | 0.278 |

An arm with no flagged P_rel cell can still be shown above δ, through P_near, P_ip, a family cell or a pooled cell; each comparator's conditions are in Supplement S4.

**7. The trade-off.** M\* buys feasibility with more exceeded constraints per decision. Its V2 (decisions with some relied constraint exceeded) is 0.491 (T1) and 0.496 (T3), about 0.05 above the per-track reference 1 − 0.95^{n_tracks} as on development (a yardstick, not a null: it assumes one independent constraint per track, whereas V2 spans four check times per track), and up from B0's 0.395 (T1) and 0.072 (T3). Its V2_viol (decisions with a violation at the chosen plan) falls on T1 (0.022 → 0.016) and rises on T3 (0.013 → 0.018) relative to B0. Section V-E(f) shows the infeasibility–violation trade-off for every arm and what infeasible decisions do.

**8. Secondary claims** (Table V). **H2 is confirmed:** a bound on a price, not superiority. **H4 is not confirmed: M\*'s nuScenes-fitted thresholds did not carry over.** With every arm fitted on nuScenes, M\* is shown above δ on both trackers, in longitudinal cells and in the in-path pooled cell (pooled P_ip exceedance 0.070, HK1c bound 0.089); Holm's sequence stopped at H6b, and H4 also fails its own level. The procedure re-fitted on new data passed (H1); how many Argoverse 2 logs a re-fit needs is in Section V-E(g). **H8 holds** only as a partial replication (Section V-B). The other claims, H3, H6a, H6b, H9, H10, Form A and H7 (the method-stage rule on the in-path audit items, fitted on nuScenes), are reported in full in Supplement S4.1.

**Table V. Claim statuses** (family S by Holm at 0.025, gated on H1, p = (k + 1)/(B + 1); H6a and H7 no-flag statements; H8 family P at its own 0.025; H9, H1-P, H5 and Form A descriptive; details in Supplement S4).

| Claim | What it tests | p (Holm level) | Status |
|---|---|---|---|
| H1 | Form B on T1 and T3 (primary) | – | holds |
| H2 | M\*'s price against B4 is ≤ 0.03 in infeasible-decision rate | 2.5 × 10⁻⁵ (0.005) | confirmed |
| H6b | method stage: B4 flagged where the method-stage rule is not, with a positive paired difference | 0.0199 (0.00625) | not confirmed |
| H10 | M\* against B6: B6's flags, and M\* − B6 ≤ 0.03 | 0.172 (0.00833) | not confirmed |
| H3 | the trajectory-level M\*Jx | 1.000 (0.0125) | not confirmed |
| H4 | H1 with every arm fitted on nuScenes | 1.000 (0.025) | not confirmed |
| H6a | the method-stage rule on the in-path audit items, fitted within Argoverse 2, flagged nowhere | – | holds |
| H7 | the method-stage rule on the in-path audit items, fitted on nuScenes, flagged nowhere | – | does not hold |
| H8 | the diagnosis of Section V-B replicates (T1, B0, in-path cars, lateral, 2 s) | – | holds (partially; Section V-B) |
| H9 | Trajectron++ [Salzmann2020] with DP-SCRC on the in-path relied items | – | no cell flagged; floor not met |
| H1-P | H1 on the 150 validation logs with the public LT3D detector | – | P_near floor not met |
| H5 | H1 on the 150 validation logs with the public VoxelNeXt detector [Chen2023voxelnext] | – | P_near floor not met |
| Form A | M\* less often infeasible than B0, B1, B4 and B9 | – | not met on T1 (one-sided 0.99375 upper bound +0.010 against B4); met on T3 |

**9. A third tracker, and the rest of the record.** On AB3DMOT, M\*, re-fitted within Argoverse 2 for this tracker too, does not pass the screen: pooled P_rel exceedance 0.061 (lower bound 0.057), infeasible in 0.891 of decisions. The GO therefore covers the two registered trackers only; Section V-E(h) diagnoses the failure. The three 150-log routes fail the P_near floor, loop mode was not run as registered (an exploratory replay is in Section V-E(i)), and the plan's optional question on the trajectory-level joint loss was not tested; Supplement S4 reports every pre-specified output.

**10. A separate re-derivation of the results.** A re-implementation within the project, not an independent one, re-derived the analysis from the registered plan without opening the analysis code's statistical functions: 108,059 comparisons agree and none disagrees, and H1 held in 20 of 20 alternative seed sets (Supplement S4).

**11. Deviations.** Three events were logged before the affected steps were repeated, and two transfer runs were started by hand with their frozen commands. No rule, input, seed or analysis changed (Supplement S5).

### E. Exploratory analyses added after the verdict

**Status of these analyses.** They answer questions that internal reviews of earlier drafts raised and the registered test could not. They were specified after the verdict and after reading the registered outputs, in a plan whose hash we recorded ourselves (no third-party timestamp) and five amendments (A1–A5), each hash-locked before its own outputs were computed. They are exploratory, change no registered result and carry no family-wise error control across analyses. Every output the plan or an amendment specifies is reported here or in Supplement S6, whichever way it points; quantities specified by neither are marked *(added)*. The frozen code is imported and run unchanged by a new runner, which first reproduced the runs of record exactly (decisions, back-off levels and per-cell counts); at B = 4000 its screen gives the record's status for 98 of 99 arms, the exception (sweep point B0a4 on T1) having its deciding bound 0.9 Monte Carlo standard errors from its threshold.

**(a) Back-off at matched screen status.** Each comparator family is tuned until it passes a screen, then compared with M\* there: B0 by scale (or nominal level), B4, B6 and B9 by nominal level δ′, refitted by their own rule, on a grid that ends at 0.005 (smaller levels need more calibration logs than a training split has; Supplement S6.2). Each held-out fold uses the least conservative point that passes on the other four folds; a family with no passing point in some fold has **no matched point**, and its in-sample best is reported, with no conservative substitute (Table VI). The screens are **the registered screen,** whose cells are M\*'s own strata (Section V-D3); **a neutral screen** (amendment A4): no flagged cell in P_rel, P_near or P_ip on the seven partitions of (b), plus HK1c on each population, with M\*'s own level δ′ tuned on the same grid; and **a reduced neutral screen** (amendment A5), the same without track speed (P1) and track age (P3), coarse functions of the variables that define M\*'s "static" and "new" course-change states.

**Table VI. Back-off at matched screen status** (cross-fitted; level → infeasible-decision rate; paired M\* − composite infeasible rate with 95 % log-bootstrap interval, conditional on the selected levels (the selection is not re-run in the bootstrap); V2_exec on the reduced screen. † B9 still passes at the least conservative grid point (δ′ = 0.05) in two to five of the five folds, so its matched point is censored by the grid and its contrast is not a matched comparison. The registered-screen results are in Supplement S6.2).

| Tracker | Family | Neutral screen (P1–P7): level → infeasible | M\*(0.03) − composite | Reduced screen (P2, P4–P7): level → infeasible | M\*(0.03) − composite | V2_exec (reduced) |
|---|---|---|---|---|---|---|
| T1 | M\* | 0.03 → 0.260 | – | 0.03 → 0.260 | – | 0.448 |
| T1 | B6 (no course-change strata) | 0.02 → 0.493 | −0.232 [−0.258, −0.207] | 0.03–0.04 → 0.298 | −0.038 [−0.063, −0.012] | 0.475 |
| T1 | B0 (scale or level) | ×2–3 or 0.005 → 0.562 | −0.302 [−0.330, −0.275] | 0.02 → 0.468 | −0.208 [−0.234, −0.181] | 0.476 |
| T1 | B4 (one pooled threshold) | 0.015–0.02 → 0.533 | −0.272 [−0.299, −0.246] | 0.02–0.03 → 0.447 | −0.187 [−0.214, −0.160] | 0.448 |
| T1 | B9 (norm ball), censored† | 0.04–0.05 → 0.700 | −0.439 [−0.465, −0.415] | 0.05 → 0.693 | −0.432 [−0.458, −0.406] | 0.527 |
| T3 | M\* | 0.03 → 0.351 | – | 0.03 → 0.351 | – | 0.504 |
| T3 | B6 | 0.02 → 0.430 | −0.079 [−0.092, −0.067] | 0.02–0.03 → 0.383 | −0.033 [−0.045, −0.021] | 0.465 |
| T3 | B0 | ×0.333 → 0.732 | −0.382 [−0.406, −0.360] | ×0.25–0.333 → 0.708 | −0.357 [−0.380, −0.334] | 0.559 |
| T3 | B4 | 0.01–0.015 → 0.701 | −0.350 [−0.374, −0.328] | 0.015 → 0.633 | −0.283 [−0.303, −0.262] | 0.516 |
| T3 | B9, censored† | 0.04–0.05 → 0.692 | −0.341 [−0.371, −0.313] | 0.05 → 0.663 | −0.312 [−0.341, −0.284] | 0.523 |

- **On the registered screen only B6 on T3 has a matched point** (0.015, infeasible in 0.486 of decisions against M\*'s 0.247; M\* − B6 −0.240 [−0.256, −0.224]); B0, B4 and B9 have none on either tracker, and B6 on T1 lacks one in one fold. For B4 and B9 this is mostly not a flag: once conservative enough to have no flag, they keep too few relied records to meet the floor of power-qualified near-gap cells. The most conservative grid points that the exploratory plan substituted in such folds are not matched comparisons and are not used as such (in-sample bests and substitutes: Supplement S6.2).
- **On both neutral screens M\* does not pass at its registered level:** at δ′ = 0.05 it is flagged in the five cells of (b) (on T1, four low-quality-track cells and one slow-track cell), and on the reduced screen in those that remain. From δ′ = 0.03 it passes both in every fold, and the registered screen too; every comparator composite matched on either neutral screen is flagged on the registered screen.
- **What sets the matched levels** (Supplement S6.22). M\*'s level is set on both neutral screens by detection score (P4, score 0.4–0.5), on T1's neutral screen together with a slow-track cell (P1, 0.5–3 m/s). The comparators' levels are set on the neutral screen mostly by track speed (P1, 3–8 m/s), a partition related to M\*'s strata, and on the reduced screen by detection score, ego speed, track length and lidar points (P4, P5, P2, P6). B9 passes at the least conservative grid point in every fold of the reduced screen and in four (T1) and two (T3) folds of the neutral screen; in T3's other three folds its level is set by track speed.
- **M\* at 0.03 backs off less often than every comparator family matched within the grid** (B0, B4 and B6), on both neutral screens, every interval below 0: by 0.23–0.30 (T1) and 0.08–0.38 (T3) on the neutral screen, and by 0.04–0.21 (T1) and 0.03–0.36 (T3) on the reduced one, where the advantage over B6 shrinks to 0.04 (T1) and 0.03 (T3). B9's composites back off 0.31–0.44 more often than M\*, but because B9 is censored by the grid these gaps overstate the gain at matched status.
- **Exceedance at the executed margin is similar, except against B6 on T3.** On the reduced screen M\*'s V2_exec is 0.448 against 0.448–0.527 (T1) and 0.504 against 0.465–0.559 (T3; B6 has the 0.465, with overlapping marginal intervals: M\* [0.480, 0.529], B6 [0.441, 0.490]; no paired interval was computed), and its V2_viol is the lowest of the five on both trackers (0.013 and 0.015). On the neutral screen M\*'s V2_exec is lower than, or within the interval of, each composite's except B6 on T3 (+0.054 [0.043, 0.066]): against the closest comparator, M\*'s smaller back-off comes with more exceedance at execution.
- **Points that pass both the registered and the neutral screen** cost more again: for example B6 at 0.01 (T1, infeasible 0.678) and 0.015 (T3, 0.486), B4 at 0.01 (T1, 0.695), B9 at 0.02 (0.822 and 0.817) and B0 at ×4 (T1, 0.660) and ×0.5 (T3, 0.781), against M\* at 0.03 (0.260 and 0.351). What the course-change strata buy is discussed in Section VI-A (registered-level comparison: Section V-D6).

**(b) Validity on partitions no method stratifies on directly.** Every arm is also screened, by the same flag rule, on seven partitions (Table VII): track speed, track length, track age, detection score, ego speed, annotation lidar points and city (4 bins, or 6 cities, × 2 axes). Track speed and track age are coarse functions of M\*'s course-change variables ((a)). The bins are those of the exploratory plan (§2(b)); we chose them from their physical meaning and, by our account, without first inspecting the distributions of the relied records. Each partition and population is a family at one-sided simultaneous 0.95, with no control across the 21 families per tracker.

**Table VII. Flagged cells on the seven partitions** (P_rel; summed over the partitions; no M\* cell is flagged in P_near or P_ip).

| Tracker | M\* | B0 | B1 | B3 | B4 | B6 | B9 | matched arms of (a) and B8 |
|---|---|---|---|---|---|---|---|---|
| T1 | 5 | 7 | 1 | 0 | 22 | 13 | 0 | 0 |
| T3 | 5 | 0 | 1 | 0 | 24 | 14 | 1 | 0 (B8: 1) |

**M\* does not pass on every partition, and its failures share a pattern:** its flagged cells concentrate in low-quality tracks, and 7 of the 10 are lateral:
- detection score 0.4–0.5: T1 lateral 0.093 (simultaneous upper bound 0.109) and longitudinal 0.087; T3 lateral 0.088 (0.101) and longitudinal;
- tracks one or two keyframes old: 0.065 (T1), 0.067 (T3);
- annotations with 1–10 lidar points: 0.071 (T1), 0.076 (T3), and on T3 also 11–50 points;
- one slow-track cell on T1: 0.5–3 m/s, longitudinal, 0.082.

On T3 M\* is also flagged in two lateral distance cells of P_rel, 20–40 m and ≥ 40 m (lower bounds 0.051 and 0.050), although it stratifies on distance: where its strata fall back to coarser thresholds, ranges are pooled, and the scored relied records differ from the calibration items (Section IV-G). Corrected across the seven partitions (one-sided 1 − 0.05/7; amendment A3), M\* keeps 4 flags on T1 and 3 on T3; with lower bounds of 0.050–0.074 at the uncorrected level on both trackers (T3's 11–50-point lateral cell the lowest), the low-quality-track finding is credible, though still exploratory, without family-wise control. B4 and B6 at their registered levels are flagged far more often (22–24 and 13–14 cells), the matched conservative arms of (a) and B8 in none but one long-track cell (B8, T3). A track-quality stratum (score or track age) is the obvious extension, not fitted because it would be chosen after seeing these data.

**(c) How much the screen depends on its intervals.** Every decisive quantity of the registered screen was recomputed with a studentized log bootstrap and with a design-effect Wilson interval, and each method was simulated at Argoverse 2's cell sizes (Supplement S6.4; the two new methods and M\*'s own flag rate are *(added)*). The record's flags are close to their level: with every cell at δ, M\* is flagged in a given population in 3–6 % of data sets and in some population in 11 % (T1) and 13 % (T3), and a comparator truly at δ leaves V_t in at most 0.3 %. Its cell upper bounds are weaker than their label: as a simultaneous set they cover 38–55 % of the time (26–52 % at M\*'s observed cell rates), so U_max (Section V-D5) understates the cell exceedances the data allow. With the studentized bounds no status changes, but single cells up to M\*'s largest cell bound, 0.189 (in-path cars on T3), cannot be excluded. The Wilson interval flags a population at δ in 18–33 % of data sets, so its flags carry little evidence.

**(d) M\* at a reference that uses nothing after the decision time.** Refitted at two references that use no information after the decision time except the route, **(d1)** the planner's own plan at margin 0 and **(d2)** constant current speed along the route, M\* keeps 98.7–99.8 % of relied items on the same axis and side, its thresholds change by a median ratio of 1.000, it passes the screen on both trackers, and its infeasible rate changes by at most 0.0006. Under the leash, however, the margin-0 plan coincides with the logged progression in 96 % of decisions: within log replay the hindsight reference does not drive M\*'s result, and closed loop is not tested by this check.

**(e) The obvious alternatives** (Table VIII), each fitted by its own rule, cross-fitted on the same folds and items and run like M\*: **B5,** per-axis scalars; **B7,** a learned heteroscedastic scale (speed and turn rate) with one conformal threshold; **B8,** stratified variance matching, with M\*'s strata and the Gaussian quantile of the matched variance; and **Q-refit,** a process noise re-fitted for the 2 s horizon, one factor per class group, whose pre-specified grid's floor bound, so amendment A2, locked before any run, extended the grid down to no process noise.

**Table VIII. Alternatives** (registered screen; infeasible-decision rate; M\* − arm, paired, 95 % interval).

| Arm | T1 screen | T1 infeasible | T1 M\* − arm | T3 screen | T3 infeasible | T3 M\* − arm |
|---|---|---|---|---|---|---|
| M\* | passes | 0.186 | – | passes | 0.247 | – |
| B5 per-axis scalars | shown above | 0.167 | +0.020 [0.001, 0.038] | shown above | 0.240 | +0.007 [−0.002, +0.017] |
| B7 learned scale | shown above | 0.154 | +0.033 [0.018, 0.047] | shown above | 0.263 | −0.017 [−0.030, −0.004] |
| B8 stratified variance matching | passes | 0.282 | −0.096 [−0.109, −0.084] | passes | 0.507 | −0.261 [−0.282, −0.240] |
| Q-refit (plan grid) | shown above | 0.271 | −0.085 [−0.108, −0.060] | floor only | 0.814 | −0.567 [−0.590, −0.544] |
| Q-refit (extended grid) | shown above | 0.230 | −0.044 [−0.067, −0.020] | floor only | 0.783 | −0.537 [−0.560, −0.515] |

- **The simpler fixes do not pass:** the two alternatives less often infeasible than M\* on T1, per-axis scalars and a learned scale, are shown above δ.
- **B8 passes and is more conservative:** infeasible 0.10 (T1) and 0.26 (T3) more often than M\*, it leaves fewer constraints exceeded at its executed margin (V2_exec 0.354 and 0.438, against M\*'s 0.551 and 0.580). It has M\*'s strata but sets each margin from the matched variance instead of the one-sided tail.
- **Re-fitting the process noise does not pass.** The fit asks for *less* process noise over 2 s for most class groups (T1's pedestrians get factors 1–4), and the extended grid is again at its floor, q = 0, on T3 and for T1's cars. On T1 the arm is shown above δ (in-path pooled exceedance 0.070 and 0.080); on T3 even q = 0 leaves the covariance too wide, because the tracker's posterior part already is, so the arm fails a floor and is infeasible in about 0.8 of decisions. One global scale of the raw covariance (RETUNED) is also shown above δ on both trackers (Table IV).

**(f) What an infeasible decision costs.** At an infeasible decision (λ < 1, Section V-A) the planner cannot keep its per-constraint risk statement (Proposition 1 covers feasible decisions only) and takes the candidate with the largest progress at the reduced margin; the emergency stop depends on margin 0 only and is the same for every arm (0.004 of decisions on T1, 0.002 on T3, 0.006 on AB3DMOT). Amendment A3 asked what the back-off costs (Table IV; Supplement S6.13):
- **Progress in decision mode.** Each decision restarts from the logged state, so decision-mode progress measures only the one-step cost of a back-off. It is small: every arm of record is within 0.02 of M\*'s progress ratio, A3's pre-fixed threshold for no cost, except six of the most conservative B0 sweep points on T1, RETUNED-HK1 among them (0.020–0.023 less), and the zero-margin arm Z0 (0.022–0.023 more on both trackers). B3, for example, executes λ = 0 in most decisions on T1 and still matches M\*'s one-step progress. At the neutral-screen matched points the differences are resolved but below that threshold: M\* makes 0.010–0.014 more on T1 and 0.004–0.009 more on T3, every interval above 0.
- **Progress in loop mode** (descriptive; (i) and Supplement S6.18). The replayed arms are M\*, B0, B4 and B6 at their registered levels (M\* at δ = 0.05), B8, and the exploratory plan's B6 composite; none is at a neutral-matched point, and their progress differences do not follow back-off frequency: on T1, B6 backs off less often than M\* (infeasible frames −0.037 [−0.052, −0.021] relative to M\*) yet makes 0.027 [0.013, 0.040] less progress, and B4 backs off about as often yet makes 0.052 [0.036, 0.068] less. As amendment A4 fixed, this replay ranks nothing.

- **The designed margin.** M\* keeps it in 81 % (T1) and 75 % (T3) of decisions.
- **Exceedance at the executed margin.** At the registered level, the conservative arms that pass leave fewer relied constraints exceeded at the margin they execute: V2_exec is 0.354 for B8 and 0.469 for RETUNED-HK1 on T1, against M\*'s 0.551, and 0.438 for B8 on T3, against 0.580. Arms that back off to near-zero margins leave more (B3: 0.745 on T1). At matched screen status ((a)), the difference largely disappears.
- **Close approaches.** The share of decisions whose smallest enforced gap is below 1 m is 0.27–0.32 for every arm of Table IV; M\*'s is 0.296 (T1) and 0.297 (T3).
- **Selection in the screen.** The screen scores each arm's relied records at its full margin, and the pairs a backed-off decision leaves unsatisfied at full margin drop out (Appendix B), so a conservative arm is screened on fewer records (Section IV-A), and its low exceedance partly reflects that selection.

**Reading.** M\*'s lower infeasible rate means that the planner keeps the margin rule it was designed with more often. In decision mode this comes with one-step progress differences below A3's no-cost threshold; the closed-loop replay is descriptive and ranks nothing. We do not claim that M\* makes the planner safer or more efficient.

**Fig. 4** shows the arms of record, the B0 sweep, the matched composites of (a) (B9's marked as censored) and B8 as infeasible rate against V2, V2_exec and V2_viol. *(added)* At M\*'s V2 of about 0.49, scaling the raw covariance is infeasible in about 0.28 of decisions on T1 (M\*: 0.186) and 0.44 on T3 (0.247), by linear interpolation of the sweep. No arm of record is at or below M\* on both infeasible rate and V2_viol on any tracker, and every other arm of record that passes the screen is infeasible in at least 0.66 of decisions; the exploratory B8 of (e) passes at 0.282 and 0.507.

**(g) How many logs a re-fit needs** (Supplement S6.8). M\* was refitted on n of the 300 training logs per held-out fold, with 3 seeded repeats for n < 300. From 200 logs every repeat passes, at an infeasible rate within 0.02 of the full fit (0.005–0.017); at 50–100 logs most strata fall back to coarse thresholds, and on T1 single cells are still flagged in four of six repeats; at 25 logs most fits are impossible. On this indicative evidence (3 repeats, a low-power screen), a deployment should plan for roughly 200 annotated logs of about 15 s (50 minutes of driving) per tracker and domain for M\* at δ = 0.05 judged by the registered screen, and more at smaller levels (Section IV-C): the level that passes both neutral screens, δ′ = 0.03, needs at least 33 logs per own-threshold stratum and plausibly more logs overall.

**(h) Why AB3DMOT fails** (descriptive). Of the registered cells, only the pooled P_rel cell fails (Section V-D9). On the seven partitions of (b), M\* on AB3DMOT is flagged in 16 P_rel cells (11 after the correction across partitions), spread over all seven, the low-score bin included. Unlike that of T1 and T3, AB3DMOT's planner population is dominated by weak and unmatched tracks (Table IX):

**Table IX. What AB3DMOT's planner population is made of** (descriptive; shares of relied records and of enforced pairs).

| | AB3DMOT | T1 and T3 |
|---|---|---|
| relied records from tracks with detection score below 0.5 | 0.41 | 0.08 |
| enforced pairs whose track has no annotated object (false-positive tracks) | 0.40 (35.8 per decision) | 0.12 (6.9 per decision) |

False-positive tracks are not the main cause of AB3DMOT's high infeasible rate: removing every unmatched track from the planner's input (amendment A4) lowers M\*'s infeasible rate only from 0.891 to 0.757, less than the halving that A4 fixed in advance as the threshold for a main driver, and M\* is still flagged. The low-score share is reported as description; a score-aware stratum or a filter before calibration is the natural remedy, and was not tested.

**(i) Beyond the registered harness** (amendment A4). Enlarging the ego from nuScenes' 4.1 × 1.8 m to 4.9 × 1.9 m leaves M\* passing the screen on both trackers (infeasible 0.208 on T1 and 0.270 on T3). **Loop mode** (descriptive; Supplement S6.18): each log was also replayed in closed loop with non-reactive agents (1,054 episodes per arm and tracker). At-fault collisions with tracked agents per 1,000 episodes were 29 for M\*, 46 for B0 and 48 for the B6 composite on T1, and 25, 38 and 39 on T3. Paired per episode, M\* had fewer than B0 (T1 −0.017 [−0.033, −0.002]; T3 −0.013 [−0.027, −0.002]) and the B6 composite of the exploratory plan, which on T1 has one substituted fold (−0.019 [−0.035, −0.006]; −0.014 [−0.025, −0.005]); the other intervals include 0. The harness is far from a deployable planner, non-reactive agents bias loop-mode collisions in a direction we cannot sign, and an arm that backs off more often also drives differently: these numbers are descriptive and rank nothing.

## VI. Discussion and Limitations

### A. What the evidence supports

**Registered, within one dataset.** A calibration fitted on the constraints a chance-constrained speed planner relies on was held near its level there, per stratum and pooled, on two trackers, in open-loop log replay. "Held near its level" means "not shown above δ" at the stated power, with the pooled bounds of Table III; never "at most δ" in every cell [AltmanBland1995]. No equivalence claim is made [Schuirmann1987; Wellek2010].

**Exploratory, added after the verdict.** On the relied constraints the raw covariance is mostly too wide, so M\* mainly narrows it. Tuned to pass a screen on partitions that no method stratifies on directly, M\* backs off its designed margin less often than every comparator family matched within the grid (B0, B4, B6), by 0.08–0.38 of decisions on seven partitions and by 0.03–0.36 without the two related to its strata (Section V-E(a)); B9's larger gap is censored by its grid.
- **The course-change strata.** At the registered level, B6 (M\* without course-change strata) was less often infeasible than M\* by 0.02, because it under-covers in course-change cells. Tuned to pass, it needs more back-off than M\*, but on the reduced screen only by 0.03–0.04, and on T3 it then leaves fewer constraints exceeded at execution (M\* − B6 +0.054 [0.043, 0.066] on the neutral screen). On this evidence the strata buy validity in course-change cells and little else; this is not a claim that they are necessary.
- **What the lower back-off is worth.** The planner keeps the margin rule it was designed with more often. In the leashed decision-mode replay the one-step progress differences are below 0.02, A3's pre-fixed threshold for no cost; the closed-loop replay, with non-reactive agents and none of its arms at a neutral-matched point, ranks nothing (Section V-E(f), (i)). Neither replay supports a claim about safety or efficiency.

**Not supported:** that nuScenes thresholds can be reused on Argoverse 2 (H4 failed for M\*, and H7 for the method-stage rule on the in-path audit items); that the result extends to a third tracker (AB3DMOT failed the screen); or that M\* passes on partitions it does not stratify (it under-covers low-quality tracks; Section V-E(b)). **Not tested at all:** anything per decision, any closed-loop property beyond the descriptive loop-mode replay of Section V-E(i), or safety.

### B. The proxy population and log replay

M\*'s calibration items are defined at the logged ego trajectory (Section IV-A), a proxy for the constraints a deployed planner would create with its own plan, which depend on its margins; the logged human trajectory may avoid conflicts the planner would enter. The registered test's scoring of each arm on the relied constraints of its own chosen plan checks the proxy within decision mode without proving it, and refitting M\* at two references that use nothing after the decision time changed its thresholds by a median ratio of 1.000, its validity not at all and its infeasible rate by at most 0.0006 (Section V-E(d)). Log replay still carries the logged trajectory (path, leash and decision states, for every arm alike), and the planner chooses only the speed. Open-loop scores at logged states can disagree with closed-loop behavior [Dauner2023; Karnchanachari2024]; the loop-mode replay added after the verdict uses non-reactive agents and ranks nothing (Section V-E(i)).

### C. Per constraint, per decision and the level δ

δ = 0.05 is a calibration level per relied constraint, not a safety target. On Argoverse 2 about one decision in two keeps some exceeded relied constraint (V2 0.491 and 0.496), because a decision holds about 13 tracks. A trajectory-level calibration that brings this near 0.05 costs 0.31–0.39 in infeasibility on development (Section V-C) and was not confirmed on Argoverse 2 (H3). A planner that allocates risk across constraints by Boole's inequality needs much smaller per-constraint levels, and these need more data: at δ = 0.01 an own threshold needs ≥ 99 logs per stratum (Section IV-C), and smaller levels proportionally more. Per-constraint calibration at 0.05 keeps the margin rule the planner was designed with honest on average along each constraint; it does not make a decision safe.

### D. Registration, blinding and what was seen before the freeze

**The blinding was procedural** (Section V-D1). Supplement S10 lists from the records every computation made on the 375 test logs before the freeze (18 entries), classed by the most each read of the annotations: detector AP, tracking metrics and planner-record counts on the 150 validation logs from 1 Nov; detector AP on the 225 held-out logs after training; and detection, tracking and the 2 s propagation on all 375 logs before the text lock, with the registered tracking metrics held back. By the records, no computation used an annotation position after a decision time, and no exceedance, margin, infeasibility, V2 or NEES on Argoverse 2 was computed or seen before the freeze. The records cannot show that no other analysis was run (the public annotation files were on the analysis computer, and tools outside the guarded entry points write no log line), nor whether the author saw any pre-freeze metric.

**The nuScenes stages are weaker:** their hashes are self-recorded; one pre-freeze check previewed the diagnosis study's decision; the validation split was examined before the first nuScenes study and used to tune T1's process noise; and reviews were within the project, with only one audit an independent re-implementation. The Argoverse 2 re-derivation (Section V-D10) was likewise written within the project, not by an independent team.

### E. Design defects and omissions of the registered plan

Each was in the frozen plan or its code, and none changed after the run: an ambiguous HK1c calibration rule (mean or minimum over development cells), whose margin 0.03 is our own value, motivated by the 98.4th percentile of a Beta(15, 286) law; an H6b p-value of resolution 1/201 (200 refit replicates), which, foreseeably, could pass its Holm level only with no exceedance at all; loop mode listed among the descriptive outputs but not run as registered, because the frozen commands allow decision mode only (Section V-E(i) runs it as an exploratory addition); an H9 "seed-robust" label in the frozen code stricter than the plan's wording (both readings are reported); a comparator removal step that is a plain Bonferroni split over nine conditions, at 1 − 0.0125/9 each, not a false-coverage-rate method; a comparison set, fixed on development, without B5, B7, a re-fitted process noise and the published filters' own implementations (Section V-E adds the first three as exploratory arms); screen cells that are M\*'s strata (Section V-D3), with the pairs a backed-off decision leaves unsatisfied at full margin dropped (Section V-E(f)); and nuScenes' ego footprint, smaller than Argoverse 2's vehicle, which changes no status (Section V-E(i)).

### F. Data, trackers and transfer

**The data and the trackers.** Two datasets, with one detector architecture trained separately for each (on Argoverse 2 for 2 class-balanced epochs, set by a compute cap, against the public checkpoint's 20; Supplement S9.15); three tracker settings on nuScenes, sharing detections and association; on Argoverse 2, trackers at their nuScenes parameters, at 2 Hz, with thin two-wheeler cells. **The certificate's population** is matched true-positive tracks still observable at the horizon: false-positive tracks enter the planner's constraints but not the certificate, and on AB3DMOT removing them does not explain most of the failure (Section V-E(h)).

**Transfer.** M\*'s nuScenes-fitted thresholds did not transfer to Argoverse 2, mostly in longitudinal cells (H4, Section V-D); the frame rate and the different dynamics are candidate causes, which we did not diagnose. A deployment must re-fit M\* on in-domain annotated logs (300 per fold here; with fewer, see Section V-E(g)). Under covariate shift, weighted conformal prediction [Tibshirani2019] or online threshold updates [GibbsCandes2021] are natural remedies; neither was tested here.

### G. Not claimed

**For the diagnosis:** miscalibration of the tracker's current-time output; a uniform lateral failure; that only the decision projection reveals the problem; or that no scalar can fix it. **For M\*:** that its course-change strata are necessary (Section VI-A); that it is the tightest method; that it makes the planner safer or more efficient; or any guarantee for one deployed rule, per object, per decision, in fallback strata or in closed loop. **For Argoverse 2:** validity in non-evaluable cells, along the objects' true axes, or outside the four groups; transfer; or safety. Proposition 5 certifies only along the estimated box axes, which are often wrong for T1 boxes (Section V-B).

## VII. Conclusion

A chance-constrained planner with linearized constraints consumes one-sided tails of a tracker's covariance along its constraint normals, a property the standard NEES check does not test. On nuScenes, a constant-velocity tracker's 2 s covariance is mis-shaped for in-path cars, yet on the constraints a speed planner relies on it is mostly too wide. M\* calibrates on those relied constraints, per stratum, and returns a covariance the planner uses unchanged.

**The registered claim.** In a registered test on Argoverse 2, in open-loop log replay with a speed-only planner, M\* re-fitted there was not shown above 5 % in any evaluable cell of the relied constraints, on two trackers. The registered comparison was uninformative, and single cells up to about 0.16 (0.19 by a post-registration interval) cannot be excluded.

**The exploratory evidence.** In analyses added after the verdict, with each method tuned to pass a screen on partitions no method stratifies on directly, M\* kept the planner on its designed margin in 3–38 percentage points more decisions than every comparator family matched within the grid. Against M\* without its course-change strata the gain was small, and on one tracker it came with more exceedance at execution.

**The failures.** M\* under-covers low-score and newly started tracks, failed its screen on a third tracker, AB3DMOT, and its thresholds did not transfer between datasets. What the paper offers is therefore a procedure to be re-fitted per tracker and domain, on roughly 200 annotated logs (an indicative figure), with track quality as the next stratum to add.

**Not claimed:** anything per decision, about safety, or in closed loop. δ is a calibration level per relied constraint, and about half of all decisions keep some exceeded constraint.

Code, plans, hashes, run logs and result files are released [repository reference to be added before submission].

## Tools and author responsibility

The author conceived the study, determined its direction and objectives, and made the scientific decisions. Under the author’s instructions, Claude (Anthropic) assisted with literature searches, mathematical derivations and checks, programming, analysis, and manuscript preparation. The author takes responsibility for the work.

---

# Appendices

## Appendix A. Proofs

This appendix proves Theorem 1(b), Proposition 3, with the conformal-risk-control step and the log as the unit, and Proposition 4. Every other statement of Sections III and IV is proved in Supplement S8, which reproduces the previous full appendix under its earlier labels and gives a label map (Section A.4). A tag [C: id] points to the numeric check of a statement in the released file `A_proofs_checks_v01.json`. Each check is exact (closed form or rational arithmetic), a one-dimensional quadrature, or a seeded Monte Carlo run with the stated tolerance.

Throughout, Φ and φ are the standard normal distribution and density functions, Φ̄ = 1 − Φ, and z_{1−δ} = Φ̄⁻¹(δ), with δ ∈ (0, ½). The setting (M1)–(M3) is that of Section III-A.

### A.1 Theorem 1(b): a whole-vector test passed exactly with a direction above δ

**Theorem 1(b).** As in Theorem 1, e = X − m̂ has the stated law given I_k, the export is V̂, and the risk along a is P(aᵀe/√(aᵀV̂a) > z_{1−δ}); the level is δ = 0.01 unless stated. A whole-vector χ² test can be passed exactly while the risk along some direction exceeds δ. Let R² ~ χ²₂ and let θ be an angle with any law, independent of R; set e = R(cos θ, sin θ) and export V̂ = I₂.

*Proof.*
1. **N is exactly χ²₂.** N = eᵀe = R², whose law does not involve θ. Every test that uses only the law of N, such as the χ² test with any acceptance region, the ANEES test or the p_v statistic, behaves exactly as under a calibrated Gaussian. For example, P(N > χ²_{2;0.95}) = e^{−χ²_{2;0.95}/2} = 0.0500 exactly.
2. **The risk along a direction.** Let a_φ = (cos φ, sin φ). With V̂ = I₂, U_φ = a_φᵀe = R cos(θ − φ). Since P(R > r) = P(R² > r²) = e^{−r²/2} for r ≥ 0 and z = z_{1−δ} > 0,

  P(U_φ > z | θ) = h(θ − φ),  h(ψ) = exp(−z²/(2cos²ψ))·1{cos ψ > 0},

  so the risk along a_φ is risk(φ) = E[h(θ − φ)].
3. **The direction average is exactly δ.** By Fubini's theorem and periodicity,

  (1/2π)∫₀^{2π} risk(φ)dφ = E[(1/2π)∫₀^{2π} h(θ − φ)dφ] = (1/2π)∫₀^{2π} h(ψ)dψ.

  The right-hand side is the risk when θ is uniform. Then e ~ N(0, I₂) and U_φ ~ N(0, 1), so it equals Φ̄(z) = δ. Since risk(φ) is continuous in φ (dominated convergence), max_φ risk(φ) ≥ δ, with equality iff risk(φ) = δ for every φ. So for **every** angle law whose directional risk is not constant, some direction has risk above δ, while every N-based test is passed exactly.
4. **The example.** Let θ = θ₀ + πB, with θ₀ ~ N(0, s²) and B a fair bit independent of θ₀. The symmetry θ ↦ θ + π gives E[e] = 0. For cos ψ ≠ 0 exactly one of h(ψ) and h(ψ + π) is non-zero, and h(ψ) + h(ψ + π) = exp(−z²/(2cos²ψ)); hence, along a₀ = (1, 0),

  risk(0) = ½·E[exp(−z²/(2cos²θ₀))].

  One-dimensional quadrature at z = z_{0.99} gives 0.02682, 0.01808 and 0.01214 for s = 0.3, 0.6 and 1.0. As s → 0 the risk tends to ½e^{−z²/2} = 0.0334, and as s → ∞ it tends to 0.01.
5. **What the joint test misses.** Var(e₁) = E[R²]E[cos²θ₀] = 1 + e^{−2s²}, which is 1.835 at s = 0.3: the covariance is wrong along a₀. The one-dimensional NEES along a₀, whose mean is Var(e₁), detects it; the two-dimensional test cannot. ∎ [C: T1b; the Monte Carlo check also confirms p_v95 = 0.050 and the three risks to within 5 × 10⁻⁴]

*A published example of this kind* [Forsling2025]: for Σ = [[8, 1], [1, 2]] and P = diag(8, 2), E[N] = tr(P⁻¹Σ) = 2, while the whitened covariance P^{−1/2}ΣP^{−1/2} = [[1, ¼], [¼, 1]] has eigenvalues 0.75 and 1.25. [C: T1b_forsling]

### A.2 Proposition 3: certification with the log as the unit

This section states Proposition 3 with the unit the registered test used, the log, and proves it from first principles, with the conformal-risk-control step written out.

**Setting.**
- **Logs and items.** A log Z is a random element of a measurable space. A fixed *item map* turns Z into a finite, possibly empty, multiset of items (x, U), with features x and score U ∈ ℝ. In the registered Argoverse 2 test a log is one drive segment of about 15 s. Its items are M\*'s calibration items (Section IV-A): every enforced pair at every decision state and calibrated check time, one item per object axis that separates the pair at the reference pose. The features include the check time and the in-path flag, because M\* is fitted separately for each (check time, in-path flag). A *stratum* g is therefore a (check time, in-path flag, level-0 stratum) triple, and a *cell* C a (check time, in-path flag, coarser cell) triple. Items within a log may be arbitrarily dependent: they share tracks, consecutive decision states and the ego trajectory.
- **Membership and loss.** n_g(Z) is the number of Z's items in g, and A_g(Z) = 1{n_g(Z) ≥ 1}. For A_g(Z) = 1 the *log loss* is

  L_g(Z; c) = (1/n_g(Z))·Σ_{items of Z in g} 1{U > c},  c ∈ ℝ ∪ {+∞}.

- **Calibration and threshold.** Calibration logs Z₁, …, Z_m; I_g = {i : A_g(Z_i) = 1}; N_g = |I_g|; R̂_g(c) = (1/N_g)Σ_{i∈I_g} L_g(Z_i; c);

  ĉ_g = inf{c ∈ ℝ : (N_g/(N_g + 1))·R̂_g(c) + 1/(N_g + 1) ≤ δ},  with inf ∅ = +∞.

**Assumptions.**
- **(L1) I.i.d. logs.** Z₁, …, Z_m and Z_test are independent and identically distributed. This is the modeling assumption of the test. It treats logs recorded in the same city or on the same day as independent draws from the population of logs. It is not testable from the data.
- **(L2) A fixed item map.** The item map, the stratum map and every ingredient of U are fixed without using Z₁, …, Z_m or Z_test. The ingredients include the detector, the tracker's Q and R, σ_a, the cut-points and the planner that defines enforced pairs. In the registered test the detector was not trained on the 375 logs and both trackers keep their nuScenes parameters (Section V-D). The item map may use anything inside the log, including the logged future ego pose; this matters for Section IV-G, not here. If an ingredient was fitted on the evaluation logs, only a transductive reading holds instead (S8-Remark 4).
- **(L3) Positive membership.** P(A_g(Z) = 1) > 0.

**Properties of the log loss.** For each log with A_g(Z) = 1, c ↦ L_g(Z; c):
- (F1) is non-increasing, because each 1{U > c} is;
- (F2) is right-continuous, because 1{U > c} → 1{U > c₀} as c ↓ c₀ (for U > c₀ eventually c < U; for U ≤ c₀ the indicator is always 0), and a finite average preserves this;
- (F3) takes values in [0, 1], so it is bounded by B = 1;
- (F4) satisfies L_g(Z; +∞) = 0, and L_g(Z; c) = 0 for c ≥ the log's largest g-score;
- (F5) satisfies L_g(Z; c) = 1 for c below the log's smallest g-score.

**Lemma A.1 (conformal risk control, in the form used).** [Angelopoulos2024, Thm 1] states: if L₁, …, L_{n+1} are exchangeable random functions of λ that are non-increasing and right-continuous, with L_i(λ_max) ≤ α and sup_λ L_i(λ) ≤ B < ∞ almost surely, then λ̂ = inf{λ : (n/(n + 1))R̂_n(λ) + B/(n + 1) ≤ α}, with λ̂ = λ_max if the set is empty, satisfies E[L_{n+1}(λ̂)] ≤ α. We use it with λ = c, λ_max = +∞, B = 1 and α = δ. For completeness, here is the proof in this setting.

Let α ∈ (0, 1). Let ℓ₁, …, ℓ_{n+1} be random functions on ℝ ∪ {+∞} with values in [0, 1] such that:
- (C1) (ℓ₁, …, ℓ_{n+1}) is exchangeable;
- (C2) each ℓ_i is non-increasing;
- (C3) each ℓ_i is right-continuous;
- (C4) each ℓ_i is bounded by B = 1;
- (C5) ℓ_i(+∞) ≤ α;
- (C6) ℓ_i(c) = 1 for all c below some finite random point.

Let R̂_n = (1/n)Σ_{i≤n}ℓ_i and λ̂ = inf{c : (n/(n + 1))R̂_n(c) + 1/(n + 1) ≤ α}, with λ̂ = +∞ if the set is empty. Then E[ℓ_{n+1}(λ̂)] ≤ α.

*Proof.* Let R̂_{n+1}(c) = (1/(n + 1))Σ_{i=1}^{n+1}ℓ_i(c) and λ̂′ = inf{c : R̂_{n+1}(c) ≤ α}.
1. **The oracle is attained.** By (C5) the set {c : R̂_{n+1}(c) ≤ α} contains +∞. By (C6) and α < 1 it contains no c below the smallest of the n + 1 finite points, so λ̂′ is finite or +∞. By (C2)–(C3), R̂_{n+1} is non-increasing and right-continuous, so the set is an interval [λ̂′, +∞] that contains its left end: if c_r ↓ λ̂′ with R̂_{n+1}(c_r) ≤ α, then R̂_{n+1}(λ̂′) = lim_r R̂_{n+1}(c_r) ≤ α.
2. **The oracle is below the rule.** For every c in the set that defines λ̂, (C4) gives R̂_{n+1}(c) = (n/(n + 1))R̂_n(c) + ℓ_{n+1}(c)/(n + 1) ≤ (n/(n + 1))R̂_n(c) + 1/(n + 1) ≤ α. So that set lies in [λ̂′, +∞], and λ̂ ≥ λ̂′; this also holds when the set is empty and λ̂ = +∞. This is the role of the "+ 1/(n + 1)" term: it bounds the unseen test loss by B = 1.
3. **Monotonicity.** By (C2), ℓ_{n+1}(λ̂) ≤ ℓ_{n+1}(λ̂′).
4. **Symmetry.** λ̂′ is a symmetric function of (ℓ₁, …, ℓ_{n+1}). By (C1), the pair (ℓ_i, λ̂′) has the same law for every i. Hence E[ℓ_{n+1}(λ̂′)] = (1/(n + 1))Σ_i E[ℓ_i(λ̂′)] = E[R̂_{n+1}(λ̂′)] ≤ α by step 1.

Combining steps 3 and 4, E[ℓ_{n+1}(λ̂)] ≤ α. (Measurability holds because each ℓ_i is a step function determined by finitely many scores.) ∎

If n + 1 < 1/α, the set defining λ̂ is empty, because R̂_n ≥ 0 and 1/(n + 1) > α. Then λ̂ = +∞ and the bound is trivial. For the log losses below, which vanish at and above a log's largest score (property F4), the set contains every c at or above the largest calibration score when n ≥ 1/α − 1, so λ̂ is finite. At α = 0.05 this is n ≥ 19.

**Lemma A.2 (conditioning on membership).** Assume (L1) and (L3). Conditionally on the membership vector (A_g(Z₁), …, A_g(Z_m)) = a ∈ {0, 1}^m and on A_g(Z_test) = 1, the logs {Z_i : a_i = 1} and Z_test are i.i.d. with law Q_g = Law(Z | A_g(Z) = 1). Hence the N_g + 1 loss functions L_g(Z_i; ·), i ∈ I_g, and L_g(Z_test; ·) are exchangeable.

*Proof.* Let B_i = {A_g = a_i}, B_test = {A_g = 1}, and let P_Z be the law of a log. By (L1) the joint law is the product P_Z^{⊗(m+1)}, and the conditioning event ∩_i{Z_i ∈ B_i} ∩ {Z_test ∈ B_test} has probability Π_i P_Z(B_i)·P_Z(B_test) > 0 by (L3), restricting a to vectors of positive probability. For measurable sets E_i,

  P(∩_i{Z_i ∈ E_i} | ∩_i{Z_i ∈ B_i}) = Π_i P_Z(E_i ∩ B_i)/Π_i P_Z(B_i) = Π_i P_Z(E_i | B_i),

including the test log. So, given the memberships, the logs are independent, and those with A_g = 1, the test log among them, all have law P_Z(· | A_g = 1) = Q_g. An i.i.d. sequence is exchangeable, and the loss functions are one fixed map (by (L2)) applied to each log, so they are exchangeable. ∎

If the logs are only exchangeable, not i.i.d., the same conclusion holds conditionally on the membership pattern. A permutation of the logs that maps the member set J onto itself leaves the event {members = J} unchanged, so it preserves the conditional law given that event; the member logs, the test log among them, are therefore exchangeable given the pattern.

**Lemma A.3 (the threshold is an observed score).** Let N_g = n ≥ 1, and let 𝒰 be the set of distinct scores of the calibration g-items. R̂_g is a right-continuous step function whose jumps lie in 𝒰, with R̂_g(c) = 1 below min 𝒰 and R̂_g(c) = 0 at and above max 𝒰. Hence the set {c : (n/(n + 1))R̂_g(c) + 1/(n + 1) ≤ δ} is empty if n < 1/δ − 1; otherwise it equals [u*, +∞), where u* is the smallest u ∈ 𝒰 that satisfies the inequality, so ĉ_g = u* ∈ 𝒰 is attained, and at n = 19 it is max 𝒰. The proof, and the check that the implementation computes u* in exact rational arithmetic, are in Supplement S8 (S8-Lemma A.3). [C: P6a_threshold_is_infimum]

**Proposition 3 (per-stratum validity, the log as the unit).** Assume (L1)–(L3) and δ = 0.05. Let ĉ_g be fitted on the g-items of the calibration logs in I_g. Then, for every membership vector a with Σ_i a_i = n ≥ 19,

  E[L_g(Z_test; ĉ_g) | (A_g(Z_i))_{i≤m} = a, A_g(Z_test) = 1] ≤ δ.

Consequently E[L_g(Z_test; ĉ_g) | N_g = n, A_g(Z_test) = 1] ≤ δ for every n ≥ 19, and E[L_g(Z_test; ĉ_g) | N_g ≥ 19, A_g(Z_test) = 1] ≤ δ. Equivalently, if J is drawn uniformly from the test log's g-items, independently of everything else given the logs, then P(U_J > ĉ_g | N_g = n, A_g(Z_test) = 1) ≤ δ. For N_g < 19, ĉ_g = +∞ and the loss is 0; the deployed rule then uses a fallback (Proposition 4).

*Proof.*
1. **Exchangeability.** Fix a with Σ_i a_i = n ≥ 19. By Lemma A.2, under P(· | A = a, A_g(Z_test) = 1) the n calibration loss functions L_g(Z_i; ·), i ∈ I_g, and L_g(Z_test; ·) are exchangeable.
2. **The conditions of Lemma A.1.** By (F1)–(F5) they satisfy (C2)–(C6) with B = 1 and α = δ < 1. ĉ_g is the λ̂ of Lemma A.1 computed from the n calibration losses.
3. **The bound.** Lemma A.1 gives the bound conditionally on (A = a, A_g(Z_test) = 1). Average over the vectors a with Σ_i a_i = n, by the law of total expectation, for the statement given N_g = n; then over n ≥ 19 for the last statement.
4. **The item form.** For every fixed c, E[1{U_J > c} | logs] = L_g(Z_test; c). ĉ_g is a function of the calibration logs, so E[1{U_J > ĉ_g} | logs] = L_g(Z_test; ĉ_g); take expectations. ∎

[C: P6b_validity_log_unit: i.i.d. logs with a log random effect, 300 calibration logs, membership 0.6, exact conditional risk given ĉ: mean 0.0453 (SE 0.0001) with a Gaussian log effect, 0.0452 with a t₄ log effect. C: P6c_validity_near_floor: N_g ~ Bin(300, 0.065); mean 0.0102 given N_g ≥ 19, 0.0035 at N_g = 19, where ĉ is the largest calibration score]

*What is, and is not, conditioned on.*
- The bound holds conditionally on the stratum's membership vector, and requires the test log to contain g. It is marginal over everything else: the calibration logs' scores, their item counts, the test log's item count, and the other strata's thresholds.
- It is **not** conditional on the calibration logs. The risk of the one rule fitted on a given calibration set exceeds δ with substantial probability, because conformal risk control is nearly tight: in the check above, 24 % of calibration draws gave a conditional risk above δ (26 % with the t₄ log effect).
- It holds for one stratum at a time. No simultaneous bound over the 192 strata of a check time is asserted.
- It weights logs, not items: each test log counts once, and its stratum items share its weight.

**Corollary A.4 (cross-fitting on Argoverse 2).** Let the 375 logs satisfy (L1)–(L3). The folds F₁, …, F₅ of 75 logs are fixed independently of the logs' contents; the registered test sorts the log identifiers, permutes them with a fixed seed and cuts the result into five blocks. For fold f, ĉ_g^{(f)} is fitted on the logs outside F_f (300 logs), and N_g^{(−f)} is their number of members of g.
- **(i)** For every t ∈ F_f and every membership vector a of the 375 logs with a_t = 1 and N_g^{(−f)}(a) ≥ 19, E[L_g(Z_t; ĉ_g^{(f)}) | A = a] ≤ δ.
- **(ii)** The cross-fitted, log-weighted estimate Ê_g = (1/|T_g|)Σ_{t∈T_g} L_g(Z_t; ĉ_g^{(f(t))}), with T_g = {t : a_t = 1}, satisfies E[Ê_g | A = a] ≤ δ whenever N_g^{(−f)}(a) ≥ 19 for all five folds, that is, when g has its own threshold in every fold.

*Proof.* Supplement S8 (S8-Corollary A.4). [C: P6d_crossfit: mean 0.0453, SE 0.0001, 2000 draws]

If g has its own threshold in some folds and falls back in others, Ê_g mixes Proposition 3 terms with Proposition 4(ii) terms and has no bound. The bootstrap bounds of Section V estimate E[Ê_g]; they are not part of the corollary.

### A.3 Proposition 4: the count-based fallback

**The fallback rule.** For a stratum g, let C₀(g) = g ⊂ C₁(g) ⊂ C₂(g) ⊂ C₃(g) be its chain of level-1, level-2 and level-3 cells, within the same check time and in-path flag. For each cell C:
- N_C is the number of calibration logs with at least one item in C;
- ĉ_C is the CRC threshold fitted on **all** of C's items in those logs, defined when N_C ≥ n_min = 19;
- L_C(Z; c) is the share of all of log Z's C-items with U > c.

The level used is ℓ*(g) = min{ℓ : N_{C_ℓ(g)} ≥ 19}, and the deployed threshold is ĉ(g) = ĉ_{C_{ℓ*(g)}(g)}. As implemented, a cell's count is its number of distinct units, and a coarser cell is fitted on all of its items, whether or not its sub-strata have their own thresholds. [C: P7_code_fit_hier]

**Proposition 4 (count-based hierarchical fallback).** Assume (L1)–(L3) for every cell on the chain.
- **(i) Own threshold.** O_g = {N_g ≥ 19} is a function of the calibration logs' membership vector for g. For every vector a ∈ O_g, E[L_g(Z_test; ĉ(g)) | A_g = a, A_g(Z_test) = 1] ≤ δ. Hence E[L_g(Z_test; ĉ(g)) | O_g, A_g(Z_test) = 1] ≤ δ: Proposition 3 holds conditionally on the stratum being assigned its own threshold.
- **(ii) A coarser cell.** For a cell C and every membership vector a_C of C with N_C ≥ 19, E[L_C(Z_test; ĉ_C) | A_C = a_C, A_C(Z_test) = 1] ≤ δ. The proposition asserts nothing beyond this:
  - **(a)** No bound conditional on g's fallback event F_g = {N_g < 19, …, N_{C_{ℓ*−1}(g)} < 19}. F_g depends on the membership vectors of g and of the intermediate cells, which are not functions of A_C. F_g restricts how many calibration logs of C contain g and places no restriction on the test log, so conditionally on F_g the calibration logs of C are no longer exchangeable with the test log; Lemma A.2 does not apply.
  - **(b)** No bound for g's own loss L_g at ĉ_C, even unconditionally.
  - **(c)** No bound for the deployed loss over C: sub-strata of C with their own thresholds use those, not ĉ_C.
  - **(d)** No bound conditional on the test log containing g.
- **(iii) A fixed map.** Given the calibration logs, the deployed map x ↦ ĉ(g(x)) is fixed: it depends on no test log. The level ℓ*(g) depends on the calibration logs only through the membership counts N_{C_ℓ(g)}, not on any score. At deployment the map needs only the stratum features: group, range from the ego's CTRV-predicted center, axis, course-change state, check time and in-path flag. All of these are computed from the tracker's estimates and the ego state.

*Proof.*
- (i) On O_g, ĉ(g) = ĉ_g. O_g is determined by the membership vector, so conditioning on A_g = a ∈ O_g fixes the assignment without disturbing Lemma A.2. Proposition 3 gives the bound for each such a; average over a ∈ O_g. An event that involved calibration scores or item counts, not only membership, would not have this property. The implementation uses unit counts only.
- (ii) This is Proposition 3 with C in place of g; its loss is L_C, over all of C's items at the single threshold ĉ_C. The counterexample below shows that (a) and (b) can fail.
- (iii) By construction: own versus fallback is decided by counts of distinct calibration units per cell, and every threshold is computed from calibration items only. ∎

*Counterexample to conditioning on fallback* [C: P7_fallback_conditioning]. Let C = g ∪ h, with 300 calibration logs:
- every log has 1–3 items of h with U ~ N(0, 1);
- with probability 0.06 a log also has 5–10 items of g with U ~ N(3, 1).

The conditional risk given ĉ_C is computed exactly, over 20 000 calibration draws. Then:
- unconditionally, E[L_C(ĉ_C)] = 0.0481 (SE 0.0001) ≤ δ, as (ii) states;
- given the fallback event N_g < 19 (probability 0.57), E[L_C(ĉ_C)] = 0.0536 (SE 0.0001) > δ, and 0.0595 given N_g ≤ 14;
- in the fallback case, a test log's g-loss at ĉ_C averages 0.80;
- when N_g ≥ 19, g's own threshold gives a g-loss of 0.0099 ≤ δ.

Fallback strata are therefore reported separately and carry no certificate.

### A.4 Where the other statements are proved

Supplement S8 keeps the previous labels; cited from outside it, a label carries the prefix "S8-".

| Statement in this paper | In Supplement S8 |
|---|---|
| Remark 1 and Proposition 1, with the non-sufficiency example (Section III-B) | same labels, S8.2 |
| Proposition 2 (Section III-C) | S8-Proposition 4, S8.3 |
| Theorem 1(a), (c) and (d) (Section III-C) | same label, S8.3 |
| the price of one knob (Section III-D) | S8-Proposition 5 and S8-Theorem 2, S8.4 |
| the log-weighted rate under exact calibration, 1.25δ = 0.0625 (Section III-E) | S8.2 |
| the proofs of Lemma A.3 and Corollary A.4 | S8.5 |
| the scene as the unit, 2/31 = 0.0645 (Section IV-C) | S8-Remark A.5, S8.5 |
| the sample floor (Section IV-C) | S8-Remark 5, S8.5 |
| Proposition 5 (Section IV-E) | S8-Proposition 8, S8.6 |
| what the propositions do not cover (Section IV-G) | S8.7 |

S8 also holds supporting results that no claim of the paper uses: S8-Proposition 2 (dilution of the exported share), S8-Proposition 3 (transfer to estimate-chosen separating axes), S8-Remark 2 (the orientation null E⁰ of Table II), S8-Remark 3 (Schur), S8-Remark 4 (the transductive reading) and S8-Proposition 9 (the certified single multiplier, B3).

## Appendix B. The planner in brief

Supplement S9 specifies the planner and the perception stack in full, with every statement tied to the code of record. In brief (Table X), the ego follows its logged path, and the planner chooses only its speed. At each decision it integrates 33 longitudinal candidates (32 accelerate-then-brake profiles, some of which never accelerate and four of which are duplicates, and an emergency stop), caps each candidate's planned position at the logged ego's (the leash), and scores it by its mean planned arc length over 4 s. Constraints are enforced at the 8 check times up to 2 s, on the *enforced* pairs only: those that, at margin 0, some candidate keeps apart and an ego held in place would too. A pair is kept apart at a check time if some object axis has a gap of at least the arm's margin. The planner chooses the feasible candidate with the largest score, ties going to the first in candidate order.

**Infeasible decisions.** If no candidate, the emergency stop included, satisfies every enforced constraint at the arm's full margin, the decision is *infeasible*: the margin is backed off to λ = 0.75, 0.5, 0.25 and 0 of its value on the same enforced set, and the emergency stop is taken only if even λ = 0 fails. The infeasible rate counts every such decision, backed off or stopped, as the mean over logs of each log's share.

**Scored records.** Records are taken at each arm's chosen plan, at its full margin: the relied axis is the one with the largest slack (gap minus margin), and only enforced pairs satisfied at the full margin are kept, so a backed-off decision contributes only the pairs its chosen plan satisfies at the full margin. V2 is the share, among decisions with at least one scored record, of those with some relied constraint exceeded, and V2_viol the share of those whose error exceeds the planned gap; both are means over logs of each log's share.

**Table X. Planner parameters.** They are the same on nuScenes and Argoverse 2; only the inputs differ: the ego path (20 Hz against 10 Hz) and the keyframe spacing (nominally 0.5 s; 0.4958–0.5999 s on Argoverse 2, with t_k the actual time stamp).

| Quantity | Value |
|---|---|
| Path | logged rear-axle path, decimated to poses ≥ 0.05 m apart |
| Ego footprint | 4.1 × 1.8 m, center 1.39 m ahead of the rear axle (nuScenes constants, also on Argoverse 2) |
| Buffer | 0.5 m on every side of the ego only |
| Consideration range | 60 m from the ego center; center not more than 2.05 m behind it |
| Score threshold | 0.4 (applied in the cache) |
| First-phase accelerations a₁ | −4, −2, −1, 0, 0.5, 1, 1.5, 2 m/s² |
| Hold times T₁ | 0.5, 1, 2, 4 s |
| Braking after the hold | −4 m/s² to standstill |
| Emergency stop | −6 m/s² throughout |
| Candidates | 33 listed (32 + emergency stop); 30 distinct profiles |
| Integration | DT_FINE = 0.05 s, 80 steps, midpoint acceleration, trapezoidal position |
| Speed bounds | [0, v_max], v_max = log maximum + 2 m/s |
| Logged speed | 0.5 s centered window on a 0.1 s grid |
| Check times | every 0.25 s, 16 in all (0.25–4 s) |
| Enforced horizon | 2 s (8 check times) |
| Scoring horizon | 4 s (16 check times) |
| Calibrated steps | 0.5, 1, 1.5, 2 s |
| Track motion | tracker's propagated mean; object yaw fixed at its current value |
| Margin per axis | arm's margin; B0 z₀.₉₅·sd with σ_a = 0.10 m |
| Enforced-pair rule | margin 0: some candidate clear and held ego clear |
| Choice | max mean leashed planned arc length over 16 check times; ties by candidate order |
| Back-off ladder | λ = 0.75, 0.5, 0.25, 0, then emergency stop |
| Decision states | keyframes 1 … K − 2 |
| Loop-mode delays and substeps | 0, 2, 4 keyframes; SUB = 5 |
| Near / far split | pair gap ≤ 5 m at the chosen plan (bins ≤ 2, (2, 5], > 5 m) |
| Motion strata | static < 1.0 m/s; turning \|ω̂\| ≥ 0.10 rad/s; "new" without ω̂ |
| Range strata | < 20, 20–40, ≥ 40 m from the sensor's CTRV-predicted center |

**Algorithm 1. M\*: calibration (offline) and deployment (online).**

```
Algorithm 1  M*: calibration (offline) and deployment (online)
Input : calibration logs (tracker exports + annotations); check times h ∈ {0.5, 1, 1.5, 2} s;
        δ = 0.05, z = Φ⁻¹(1−δ); σ_a = 0.10 m; chain L0 ⊂ L1 ⊂ L2 ⊂ L3; n_min = 19; ε = 1e-3
Calibration
 1  for each log, decision state k (logged ego position and speed), check time h:
 2     E ← pairs (track r, h) enforced at margin 0          # score ≥ 0.4, ≤ 60 m, not behind (IV-A)
 3     for (r, h) ∈ E whose object has an annotation X at k+h:
 4        p_ref ← reference ego pose at k+h                    # logged pose (Section V-E: alternatives)
 5        for each box axis a ∈ {a_L, a_T} separating r's box from the buffered ego at p_ref:
 6           s ← side of separation;  D ← s·aᵀ(X − m̂_h);  sd ← √(aᵀΣ̂_h a + σ_a²)
 7           append item (log, h, in-path flag, stratum x, U = D/sd)
 8  for each h and in-path flag, for level ℓ = 0..3, for each cell C at level ℓ:
 9     n_C ← number of logs with an item in C
10     if n_C ≥ n_min: ĉ_C ← smallest observed U with (n_C/(n_C+1))·mean_logs L_C(·; U) + 1/(n_C+1) ≤ δ
11  for each L0 stratum s: ĉ(s) ← ĉ of the first cell on s ⊂ L1(s) ⊂ L2(s) ⊂ L3(s) with n ≥ n_min
Deployment (per track and check time, inside the planner)
12  α_L ← max(ĉ(x_L), ε)/z;  α_T ← max(ĉ(x_T), ε)/z
13  A ← α_L a_L a_Lᵀ + α_T a_T a_Tᵀ;  Σ̃ ← A(Σ̂_h + σ_a² I)A
14  pass (m̂_h, Σ̃) to the planner, which applies z·√(aᵀΣ̃a) as usual
```

**Algorithm 2. One decision of the planner.**

```
Algorithm 2  plan_step(arm, k, s, v): one decision
input : keyframe k at time t_k; arc length s and speed v (decision mode: s_log(t_k),
        max(v_log(t_k), 0)); leash lead(t); v_max = max logged speed + 2 m/s
 1  S_plan[c, i] <- integrate candidate c over 80 steps of 0.05 s from (s, v),
                   clip v to [0, v_max]; keep s at check times t_i = 0.25 i
 2  S_plan[c, i] <- min(S_plan[c, i], lead(t_k + t_i))           # the leash
 3  prog[c] <- mean_i S_plan[c, i]           # 16 check times, scoring to 4 s
 4  J <- tracks at k with |c_track - c_ego| < 60 m and
        (c_track - c_ego) . u_ego >= -2.05 m
 5  if J is empty: return argmax_c prog[c], feasible, lambda = 1
 6  for j in J, step h = 1..8 (0.5 s): sd, L0 stratum, margin m[j, h, a]
 7  mean at check time i: tracker mean at the 0.5 s steps, average of the two
    neighbours at midpoints; margin at i = margin of the next 0.5 s step
 8  gap[c, i, j, a] <- |a.(c_ego(c, i) - mu[j, i])| - (h_obj[j, a] + h_ego(c, i, a))
                   (ego 4.1 x 1.8 m + 0.5 m per side; object not buffered)
 9  for check times i = 1..8 (to 2 s):
10     ctrl[i, j] <- exists c in all 33 candidates: max_a gap[c, i, j, a] >= 0
11     hold[i, j] <- max_a gap_held(s)[i, j, a] >= 0     # ego held at s
12     enf[i, j]  <- ctrl[i, j] and hold[i, j]     # arm-independent (margin 0)
13  slack[c, i, j] <- max_a (gap[c, i, j, a] - m[j, i, a])
14  F <- {c : slack[c, i, j] >= 0 for every enforced (i, j)}
15  if F is not empty: return argmax_{c in F} prog[c] (first in candidate order),
                      infeasible = false, lambda = 1
16  infeasible <- true
17  for lambda in (0.75, 0.5, 0.25, 0):
18     F_l <- {c : max_a (gap[c, i, j, a] - lambda m[j, i, a]) >= 0 for every
              enforced (i, j)}                    # the same enforced set
19     if F_l is not empty: return argmax_{c in F_l} prog[c], infeasible, lambda
20  return the emergency stop (-6 m/s^2), infeasible, lambda = -1 (recorded)
21  records (decision mode): at the chosen c, steps 0.5-2 s, relied axis
    a* = argmax_a (G_a - m_a), satisfied = G_a* - m_a* >= 0; one record per axis
    with G_a > 0; exceedance D > m
```

## Appendix C. Terminology

| Term | Meaning in this paper |
|---|---|
| δ | 0.05: the calibration level per relied constraint. Not a safety target. |
| item / record | One calibration score U = D/sd for a (pair, axis, check time) / one scored relied constraint of a decision. |
| enforced pair | A (track, check time) pair that, at margin 0, some candidate plan satisfies and an ego held in place would satisfy (Appendix B). |
| relied axis | In scoring: the object axis with the largest slack (gap minus the arm's margin) under the arm's own chosen plan, kept if it separates and is satisfied at full margin. Fitting uses every separating axis at the reference pose. |
| P_rel, P_near, P_ip, P_nip | Relied records: all / those with pair gap ≤ 5 m / those of in-path tracks / those of tracks not in path (scope only). |
| exceedance rate (E) | The mean over logs of each log's share of records whose error exceeds the margin. |
| cell | Group × axis × course-change state, pooled over range, within one population. |
| evaluable | A cell with records from ≥ 39 logs. |
| flagged = shown above δ | Lower end of the one-sided simultaneous 95 % sup-t band > δ. Comparators: at 0.99861. |
| not shown above δ ("valid") | Not flagged. A non-rejection, not "≤ δ". |
| power-qualified family | The cells in which a planted 0.15 would be flagged with probability ≥ 0.8. These cells are tested together. |
| floor | The minimum number of power-qualified (P_rel, P_near) or evaluable (P_ip) cells. |
| pooled cell | All records of a population as one cell. |
| HK1c | The pooled upper bound at nominal 0.995 must be ≤ 0.08. |
| U_max | M\*'s largest simultaneous 95 % cell upper bound (descriptive). |
| screen | No flag + floors + HK1c, on all three populations. |
| V_t, V^J | The comparators not shown above δ on tracker t; the same for the joint loss (H3). |
| Form A / B / C | The descriptive comparison with B0, B1, B4, B9 / the H1 comparison with V_t / H2's bound on M\* − B4. |
| family S, family P | Secondary claims under Holm at 0.025 gated on H1 / H8 alone at 0.025. |
| route | Which fits and logs an analysis uses (within Argoverse 2; nuScenes transfer; 150-log variants). |
| infeasible decision | No candidate plan, the emergency stop included, satisfies every enforced constraint at the arm's full margin. The planner then backs its designed margin off (λ = 0.75, 0.5, 0.25, 0) or stops (Appendix B); "infeasible" means "designed margin backed off", not "no progress". The infeasible rate counts every such decision, backed off or stopped, as the mean over logs of each log's share. |
| V2, V2_viol | The share of decisions with some relied constraint exceeded / violated at the plan (error larger than the planned gap). |
| E⁰ | The exceedance a calibrated tracker would show because the toward-ego orientation is chosen from the estimate (S8-Remark 2). |
| FAILS / OVERCOVERS / CONSISTENT | Diagnosis labels: the band is above max(δ, E⁰) / below δ / neither. |
| cross-fitted | Fitted on 4 of 5 log folds and applied to the 5th. A result averages 5 fold rules, not one deployed rule. |
| RETUNED, RETUNED-HK1 | B0 rescaled to a pooled 5 % on the training folds / to pass the screen on the training folds (matched validity). |
| nominal / actual error | The level a test is run at / its true error rate when its bounds are approximate. |
| decision mode / loop mode | One open-loop decision per keyframe from the logged state / closed-loop replay with non-reactive agents (not run as registered; run on Argoverse 2 as an exploratory addition, Section V-E(i)). |
| registered / pre-specified / exploratory / post-registration exploratory | Plan frozen and deposited with OSF before outcomes / planned and hashed by us before outcomes / neither / the analyses of Section V-E, after the verdict of record. |

---

## Figure captions

**Fig. 1.** M\* between tracker and planner. Offline (left), on annotated logs, each constraint the planner enforces at the logged reference ego pose gives a one-sided error $U = D/\mathrm{sd}$ of the tracker's prediction along each separating object axis. Conformal risk control then sets one threshold $\hat{c}_g$ per stratum (object group $\times$ range $\times$ axis $\times$ course-change state, fitted separately per check time and for in-path and other tracks), with a count-based fallback to coarser cells, the log as the exchangeable unit and cross-fitting over log folds. Online (right), the thresholds rescale the tracker's covariance along the box axes, $\tilde{\Sigma} = A(\hat{\Sigma}_h + \sigma_a^2 I)A$ with $\alpha = \max(\hat{c}, \varepsilon)/z$ per axis, and the unchanged chance-constrained speed planner applies its usual margin $z\sqrt{a^{\mathsf{T}}\tilde{\Sigma}a}$, which equals $\hat{c}\cdot\mathrm{sd}$ along each object axis (Proposition 5).

**Fig. 2.** M\*'s exceedance in every evaluable cell on Argoverse 2, run of record. Cells are object group $\times$ axis $\times$ course-change state, pooled over range, with records from at least 39 logs. Populations: $P_{\mathrm{rel}}$, all relied records; $P_{\mathrm{near}}$, pair gap $\leq$ 5 m; $P_{\mathrm{ip}}$, in-path tracks. Each marker is the cell's exceedance rate, the mean over logs of each log's share of exceeded records (T1, CANMOT: circles; T3, Poly-MOT: squares). Each bar runs to the upper end of the one-sided simultaneous 95 % sup-t band from the log bootstrap over the population's evaluable cells. The band's lower end decides the flags and is not drawn; the dashed line is $\delta = 0.05$, and $U_{\max}$ is the largest upper end. In a simulation at Argoverse 2's cell sizes these simultaneous bounds covered only 38–55 % of the time (Section V-E(c)), so they understate how large a cell exceedance the data allow.

**Fig. 3.** Infeasible-decision rate per arm on Argoverse 2, run of record (375 logs, decision mode), with arms in the order of Table IV, for T1 (CANMOT, circles) and T3 (Poly-MOT, squares). (a) The rate, the mean over logs of each log's share of infeasible decisions, with its two-sided 95 % log-bootstrap interval. (b) The paired per-log difference M\* $-$ arm with its two-sided 95 % percentile log-bootstrap interval, resampling whole logs. Filled markers in (b) are comparators that stayed in the comparison set $V_t$; open markers are comparators removed from $V_t$, which were flagged in one of their conditions at one-sided 0.99861. H1 compared M\* with the members of $V_t$ at one-sided $1 - 0.0125/|V_t|$, not at the 95 % level shown.

**Fig. 4.** Infeasible-decision rate, the share of decisions at which the planner backs off its margin, against three exceedance measures on Argoverse 2, for T1 (CANMOT) and T3 (Poly-MOT); log means over 375 logs, decision mode. (a) V2, the share of decisions with some relied constraint exceeded at full margin; (b) $\mathrm{V2}_{\mathrm{exec}}$, the same at the executed margin; (c) $\mathrm{V2}_{\mathrm{viol}}$, the share with some relied constraint violated at the chosen plan. Filled markers are the arms of record. The gray line joins the B0 sweep (raw covariance scaled by $\alpha$ or set at level $\delta'$) in order of V2, and its $\delta' = 0.5$ end coincides with the zero-margin arm Z0. The other markers are post-registration exploratory points, each composite picking every fold's level on the other four folds: B8; B6 matched on the registered screen, drawn for T3 only (on T1 one fold's level is substituted, so the composite is not a matched point); M\* at $\delta' = 0.03$, matched on both neutral screens (hollow star); and, in each family's color, the B0, B4, B6 and B9 composites matched on the neutral screen (seven partitions no method stratifies on directly; crosses) and on the reduced neutral screen (without track speed and track age; rings). B9 passes at the least conservative grid point ($\delta' = 0.05$) in two to five of the five folds, so its matched point is censored by the grid (arrows); its rings sit on the B9 arm of record. Drawn offsets, so that no marker is hidden: the B9 crosses, about 4 pt, in T1 (a)–(c) and T3 (a) and (b); B8 in T1 (c), 7 pt to the right; B1 in T3 (a), about 5 pt to the right; and B6 matched on the registered screen in T3 (a)–(c), 5–6 pt to the left. Elsewhere, crosses are drawn above the markers of record and these above the rings, so touching markers stay visible. Z0, the learning-curve and alternative-reference refits and the other exploratory arms are not shown; every plotted value is listed in the supplementary table.

---

## References

In order of first citation (106 entries; BibTeX in refs_v06c_v02.bib, rendered in IEEE style by the LaTeX build): Blackmore2011, Ono2008, Zhu2019, Nair2025, Ren2025, BarShalom2001, Osterburg2026, DuToit2011, Hardy2013, deGroot2025, Mustafa2023, Lindemann2023, Shah2026, Mohamed2025, Pouria2026, Li2024, Shi2026, Guo2025, Weng2020, Chiu2020, Li2023, Mehra1970, Zhang2020, Sarkka2009, Huang2018, Jiang2024, Ulreich2024, LearnTrack2026, Feng2018, Meyer2020, Pan2020, BlomBarShalom1988, Mazor1998, BarthFranke2010, Djuric2020, PhanMinh2020, Lefevre2014, Ivanovic2022, Li2002, Chen2024, Ahmed2024, Yan2026, Forsling2025, Chen2018nees, Gneiting2007, Ziegel2014, GneitingResin2023, Vovk2012, Bostrom2020, Gibbs2025, Lei2014, Barber2021, Angelopoulos2024, Bates2021, Ding2023, Dunn2023, LeeBarberWillett2026, GibbsCandes2021, BianBarber2023, Angelopoulos2025LTT, Tibshirani2019, Barber2023, JinCandes2023, Bao2024, Dixit2023, Lindemann2025, Cleaveland2024, Yang2023, Zhang2025, DixitMei2024, Natraj2026, Vlahakis2024, Su2024, Weisman2026, Marques2026a, Marques2026b, Chen2026, Bao2026, DSilva2026, Zhao2021, Sahoo2021, Kiyani2026, Tang2026, Noarov2025, Zhu2026, Lekeufack2024, Philion2020, IvanovicPavone2022, McAllister2022, IvanovicA2024, Karnchanachari2024, Dauner2023, Li2024Ego, KalraPaddock2016, Argoverse2, Caesar2020, Yin2021, Peri2022, Zhu2019cbgs, Berger1982, Holm1979, Salzmann2020, Chen2023voxelnext, AltmanBland1995, Schuirmann1987, Wellek2010.

