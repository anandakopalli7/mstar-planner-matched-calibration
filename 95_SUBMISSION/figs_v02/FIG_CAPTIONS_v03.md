# Proposed captions for Figs. 1–4 (figs_v02, captions v03)

Written 2026-11-07 19:18 EST for the v06d manuscript. Math is in LaTeX form. The Fig. 1–3 captions are copied unchanged from FIG_CAPTIONS_v02.md. The Fig. 4 caption is revised for fig04_tradeoff_v03, following referee review V06D minor 4 and 18. The caption text contains no file names.

## Fig. 1 (single column; fig01_pipeline.pdf); unchanged

**Fig. 1.** M\* between tracker and planner. Offline (left), on annotated logs, each constraint the planner enforces at the logged reference ego pose gives a one-sided error $U = D/\mathrm{sd}$ of the tracker's prediction along each separating object axis. Conformal risk control then sets one threshold $\hat{c}_g$ per stratum (object group $\times$ range $\times$ axis $\times$ course-change state, fitted separately per check time and for in-path and other tracks), with a count-based fallback to coarser cells, the log as the exchangeable unit and cross-fitting over log folds. Online (right), the thresholds rescale the tracker's covariance along the box axes, $\tilde{\Sigma} = A(\hat{\Sigma}_h + \sigma_a^2 I)A$ with $\alpha = \max(\hat{c}, \varepsilon)/z$ per axis, and the unchanged chance-constrained speed planner applies its usual margin $z\sqrt{a^{\mathsf{T}}\tilde{\Sigma}a}$, which equals $\hat{c}\cdot\mathrm{sd}$ along each object axis (Proposition 5).

## Fig. 2 (double column; fig02_mstar_cells.pdf); unchanged

**Fig. 2.** M\*'s exceedance in every evaluable cell on Argoverse 2, run of record. Cells are object group $\times$ axis $\times$ course-change state, pooled over range, with records from at least 39 logs. Populations: $P_{\mathrm{rel}}$, all relied records; $P_{\mathrm{near}}$, pair gap $\leq$ 5 m; $P_{\mathrm{ip}}$, in-path tracks. Each marker is the cell's exceedance rate, the mean over logs of each log's share of exceeded records (T1, CANMOT: circles; T3, Poly-MOT: squares). Each bar runs to the upper end of the one-sided simultaneous 95 % sup-t band from the log bootstrap over the population's evaluable cells. The band's lower end decides the flags and is not drawn; the dashed line is $\delta = 0.05$, and $U_{\max}$ is the largest upper end. In a simulation at Argoverse 2's cell sizes these simultaneous bounds covered only 38–55 % of the time (Section V-E(c)), so they understate how large a cell exceedance the data allow.

## Fig. 3 (single column; fig03_infeasible_arms.pdf); unchanged

**Fig. 3.** Infeasible-decision rate per arm on Argoverse 2, run of record (375 logs, decision mode), with arms in the order of Table IV, for T1 (CANMOT, circles) and T3 (Poly-MOT, squares). (a) The rate, the mean over logs of each log's share of infeasible decisions, with its two-sided 95 % log-bootstrap interval. (b) The paired per-log difference M\* $-$ arm with its two-sided 95 % percentile log-bootstrap interval, resampling whole logs. Filled markers in (b) are comparators that stayed in the comparison set $V_t$; open markers are comparators removed from $V_t$, which were flagged in one of their conditions at one-sided 0.99861. H1 compared M\* with the members of $V_t$ at one-sided $1 - 0.0125/|V_t|$, not at the 95 % level shown.

## Fig. 4 (double column; fig04_tradeoff_v03.pdf); revised

**Fig. 4.** Infeasible-decision rate, the share of decisions at which the planner backs off its margin, against three exceedance measures on Argoverse 2, for T1 (CANMOT) and T3 (Poly-MOT); log means over 375 logs, decision mode. (a) V2, the share of decisions with some relied constraint exceeded at full margin; (b) $\mathrm{V2}_{\mathrm{exec}}$, the same at the executed margin; (c) $\mathrm{V2}_{\mathrm{viol}}$, the share with some relied constraint violated at the chosen plan. Filled markers are the arms of record. The grey line joins the B0 sweep (raw covariance scaled by $\alpha$ or set at level $\delta'$) in order of V2, and its $\delta' = 0.5$ end coincides with the zero-margin arm Z0. The other markers are post-registration exploratory points, each composite picking every fold's level on the other four folds: B8; B6 matched on the registered screen, drawn for T3 only (on T1 one fold's level is substituted, so the composite is not a matched point); M\* at $\delta' = 0.03$, matched on both neutral screens (hollow star); and, in each family's colour, the B0, B4, B6 and B9 composites matched on the neutral screen (seven partitions no method stratifies on directly; crosses) and on the reduced neutral screen (without track speed and track age; rings). B9 passes at the least conservative grid point ($\delta' = 0.05$) in two to five of the five folds, so its matched point is censored by the grid (arrows); its rings sit on the B9 arm of record. Where markers would coincide, two markers are drawn about 4–7 pt beside their values. These are the B9 crosses (T1, all rows; T3, (a) and (b)) and, in T1 (c), B8, which is moved clear of M\* at $\delta' = 0.03$. Z0, the learning-curve and alternative-reference refits and the other exploratory arms are not shown; every plotted value is listed in the supplementary table.

## Notes for the lead (not caption text)

- **Offsets** (data units, in the points table v03, column `x_drawn_offset`):
  - B9 neutral-screen cross: T1 −0.020 (a), −0.013 (b), −0.0012 (c); T3 −0.020 (a), +0.013 (b).
  - B8: T1 (c) +0.0020.
  - Two of these go beyond the referee's list. T3 (a) is needed because the B9 cross sat exactly on the B4 cross; T3 (b) because they nearly coincided.
- **Folds at B9@0.05:**
  - T1: neutral 4/5, reduced 5/5.
  - T3: neutral 2/5, reduced 5/5. On T3's neutral screen the composite is only partly at the grid end, and the referee notes that P1 sets B9's level in folds 1, 3 and 4. The caption therefore says "two to five of the five folds" rather than "every fold".
- **Registered-screen B6 composite:**
  - T1 folds: B6@0.015 / B6@0.005 / B6@0.015 / B6@0.015 / B6@0.015 (fold 1 substituted). Not drawn.
  - T3: B6@0.015 in every fold. Drawn.
