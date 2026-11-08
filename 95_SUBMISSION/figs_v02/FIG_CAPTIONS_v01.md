# Proposed captions for Figs. 1 and 4 (figs_v02)

Written 2026-11-07 17:38 EST, for the v06c manuscript. Math is in LaTeX form for paper_v02.tex. Fig. 1 follows 20_DESIGN/ms_v06_parts/04_method_v04.md, Sections IV-A to IV-F. Every number in the Fig. 4 caption comes from the source files listed in figs_v02_manifest.json.

## Fig. 1 (single column; fig01_pipeline.pdf)

**Fig. 1.** M\* between tracker and planner. Offline (left), on annotated logs, each constraint the planner enforces at the logged reference ego pose gives a one-sided error $U = D/\mathrm{sd}$ of the tracker's prediction along each separating object axis. Conformal risk control then sets one threshold $\hat{c}_g$ per stratum (object group $\times$ range $\times$ axis $\times$ course-change state, fitted separately per check time and for in-path and other tracks), with a count-based fallback to coarser cells, the log as the exchangeable unit and cross-fitting over log folds. Online (right), the thresholds rescale the tracker's covariance along the box axes, $\tilde{\Sigma} = A(\hat{\Sigma}_h + \sigma_a^2 I)A$ with $\alpha = \max(\hat{c}, \varepsilon)/z$ per axis, and the unchanged chance-constrained speed planner applies its usual margin $z\sqrt{a^{\mathsf{T}}\tilde{\Sigma}a}$, which equals $\hat{c}\cdot\mathrm{sd}$ along each object axis (Proposition 5).

## Fig. 4 (double column; fig04_tradeoff.pdf)

**Fig. 4.** Infeasible-decision rate (share of decisions at which the planner backs off its margin) against three exceedance measures on Argoverse 2, for T1 (CANMOT) and T3 (Poly-MOT); log means over 375 logs, decision mode. (a) V2, the share of decisions with some relied constraint exceeded at full margin; (b) $\mathrm{V2}_{\mathrm{exec}}$, the same at the executed margin; (c) $\mathrm{V2}_{\mathrm{viol}}$, the share with some relied constraint violated at the chosen plan. Filled markers are the arms of record; the grey line joins the B0 sweep (raw covariance scaled by $\alpha$ or set at level $\delta'$) in order of V2, and its $\delta' = 0.5$ end coincides with the zero-margin arm Z0; hollow markers are post-registration exploratory arms: the B6 composite matched on the registered screen, B8, and, in (b) only because only its $\mathrm{V2}_{\mathrm{exec}}$ is available, M\* at $\delta' = 0.03$ matched on the neutral screen. Z0, the learning-curve and alternative-reference ($d_1$, $d_2$) refits and the other exploratory arms are not shown; every plotted value is listed in the supplementary table (fig04_points_v01.csv).

## Notes for the lead (not caption text)

- Section V-E (05E_x3_v04.md, line 126) still says "Fig. 4 shows every arm as infeasible rate against V2 and against V2_viol". The new Fig. 4 has a third row ($\mathrm{V2}_{\mathrm{exec}}$) and omits Z0, the learning-curve, d1/d2, q-refit, B5, B7 and the B4/B9 composites, so that sentence needs a matching edit.
- The legend is shortened to "B6 composite (matched)" and "B8 (variance matching)"; the caption carries the full wording.
- The neutral-matched comparator composites (B4, B6, B9 and B0 families on the neutral screen) have only infeasible rate and $\mathrm{V2}_{\mathrm{exec}}$ in x3_a4_1_neutral_v01.json. They are not drawn, because the design list names only M\*(0.03) from the neutral screen. They could be added to row (b) on request.
