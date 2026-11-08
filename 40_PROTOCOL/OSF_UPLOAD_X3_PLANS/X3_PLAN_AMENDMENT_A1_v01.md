# X3 plan amendment A1: heading error behind the "lateral" diagnosis (7 Nov 2026, 11:18 EST)

**Status.** It amends `X3_POSTREG_EXPLORATORY_PLAN_v01.md` (38e2526d…) and was written and hash-locked before any of its numbers was computed. Everything in the plan's §0 applies (stamp, integrity checks, no edits to frozen files, imports only).

**Why.** Referee M9 asks how many diagnosis items are affected by the tracker's heading error. "Lateral" is the tracked box's lateral axis, and on nuScenes a project audit (R11B O1) found CANMOT box headings often wrong (median 40° among T1-only planner records). That audit was on the planner population, not on the X2 diagnosis cells.

## (i) The analysis

- **Data.** X2's four decision cells: in-path cars, < 20 m and 20–40 m, lateral and longitudinal, at 2 s, on the 700 nuScenes training scenes, under T1, with σ_a = 0.10 m.
- **The rule.** X2's items are rebuilt by importing the frozen X2 code read-only. The rebuild must reproduce the X2 result of record's item counts and E (record-weighted) per cell exactly; if it does not, A1 is not done, and that is reported.
- **Per item:** the heading error |wrap(ψ_track − ψ_annotation)| at the decision keyframe k, with the annotation of the paired object at k, folded to [0°, 90°] because a box's axes are symmetric under a 180° turn.

**Outputs, per cell:**
- the shares of items with heading error ≤ 10°, (10°, 20°] and > 20°;
- the share of exceedances (U > 1.645) from items with error > 20°;
- E recomputed on items with error ≤ 20°, with a scene-cluster bootstrap 95 % interval (B = 2000, seed [20261211, cell]), against X2's threshold max(0.05, E⁰) of record;
- the same three numbers truth-oriented.

## (ii) Reading, fixed now

- If E on items with heading error ≤ 20° still exceeds the threshold in a lateral cell, the lateral under-coverage there is not explained by heading error.
- If it falls below the threshold, the text says that the cell's lateral failure is largely a heading-error effect.

Either result is reported in Section V-B.
