"""R09b text fixes to 40_PROTOCOL/K6_PREREGISTRATION_v02.md (MJ1-MJ3, m1-m4, m7-m11). Run once (Claude line, 1 Nov 2026).
The OC table and the HK3 power table are regenerated from the final OC v02 file."""
import json
import os

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
p = os.path.join(W, "40_PROTOCOL", "K6_PREREGISTRATION_v02.md")
s = open(p, encoding="utf-8").read()
assert "R09b" not in s.split("## 13.")[0] or "§13b" not in s, "already applied"

rep = [
    ("v01 (draft `e757fbe6…`, `K6_PLAN_HASH_LOG.txt`) was reviewed by R09, never frozen, and is kept unchanged. §13 answers every R09 finding.",
     "v01 (draft `e757fbe6…`, `K6_PLAN_HASH_LOG.txt`) was reviewed by R09, never frozen, and is kept unchanged. The v02 draft `75eb7101…` was re-reviewed by R09b (`70_TESTS/R09B_K6_PREFREEZE_REREVIEW_v01.md`; 0 critical, 3 major, 11 minor; \"freeze after fixes\"). §13 answers every R09 finding and §13b every R09b finding."),
    ("   - the open-loop calibration items (their residuals are the method stage's, already analysed, D07);",
     "   - the open-loop calibration items, a new 8-step build on the deployed output (score ≥ 0.4) that includes steps D07 did not have (0.5, 1.5, 2.5, 3 and 3.5 s). Their residuals were computed and used only for the cross-fitted fits; at the steps D07 had, they are the method stage's residuals on a subset (R09b m8);"),
    ("4. **Development scenes.** Closed-loop and decision outcomes had been seen on the 10 nuScenes-mini scenes only. Seven development iterations on them fixed the planner rules (D09 v03 §0, D09 v04 §0–§1), and every K6 analysis excludes those scenes.",
     "4. **Development scenes.** Closed-loop and decision outcomes had been seen on the 10 nuScenes-mini scenes only, and every K6 analysis excludes those scenes. Nine recorded development iterations fixed the planner rules:\n"
     "   - dev v01–v05 (D09 v03 §0);\n"
     "   - dev v05b, v06 and v07 (D09 v04 §0–§1);\n"
     "   - dev v08 (D09 v05);\n"
     "   - the scratch runs `try_twolevel`, `try_h2s` and `dev_v02_t1only`.\n"
     "6. **HK3 was chosen after seeing development outcomes (R09b MJ2).** HK3's endpoint, the infeasible-decision rate, and its comparator set were chosen *after* dev v07:\n"
     "   - **Infeasibility.** In dev v07, M\\*'s infeasible-decision rate was 0.19 against 0.40–0.63 for B0, B1, B4 and B9 on T1, and 0.28 against 0.33–0.95 on T3.\n"
     "   - **Progress.** The closed-loop progress differences were small, for example T1 M\\* 0.67 against B4 0.65.\n"
     "   - **v01's HK3** was progress against B3 and B9. B3 is dominated by construction.\n"
     "   - **B6 is not an HK3 comparator.** B6 is DP-SCRC without the motion strata, a variant of the method rather than an alternative. D07 had already found the motion strata cost margin on Poly-MOT (M\\*/B6 = 1.056), and in development B6 was more often feasible than M\\* on T3 (0.24 against 0.28). M\\* against B6 is reported as the motion-state option, and no operability claim is made against it."),
    ("2. Does calibration make the planner operable, that is, less often left without a feasible plan, compared with the practitioner and certified alternatives?",
     "2. Does calibration make the planner operable, that is, less often left without a feasible plan, compared with the practitioner corrections (B0, B1, B4) and the norm-ball certified alternative (B9)?"),
    ("| **K6a** (validity on relied-on constraints) | In the decision mode, on the calibrated population, M\\*'s exceedance is not significantly above δ = 0.05 in any power-qualified cell (cells where an exceedance of 0.15 would be detected with power ≥ 0.80), nor in the pooled cell, on T1 and T3 | HK1 |",
     "| **K6a** (validity on relied-on constraints) | In the decision mode, on the calibrated population, M\\*'s exceedance is not significantly above δ = 0.05 in any evaluable cell, nor in the pooled cell, on T1 and T3. The claim of non-exceedance is made for the power-qualified cells only: those where an exceedance of 0.15 would be detected with power ≥ 0.80 under the stated model | HK1 |"),
    ("- **Dominance.** B3's multiplier is the maximum of M\\*'s thresholds, so M\\*'s margins are never larger, and its feasibility at a given state is at least B3's by construction. M\\* − B3 is reported, not tested (R09 M4).",
     "- **Dominance.** B3's multiplier is the maximum of M\\*'s thresholds, so M\\*'s margins are never larger, and its feasibility at a given state is at least B3's by construction. M\\* − B3 is reported, not tested (R09 M4).\n"
     "- **HK3 against B0 on T3 is near-implied (R09b m1).** Poly-MOT's covariance over-covers (D07). M\\*'s multiplier exceeds z in at most 0.7 % of T3's confirmatory items at 0.5–2 s, and in development M\\* was never infeasible where B0 was feasible (0 of 384 T3 decisions). The test is kept, but it adds little on T3."),
    ("- Anything about the 10 development scenes.",
     "- Anything about the 10 development scenes.\n"
     "- Operability against B6: that comparison is the motion-state option, reported only.\n"
     "- Closed-loop safety differences between arms as calibration effects. An arm that is infeasible more often runs more often at a backed-off margin (C14), and in development every tracked at-fault collision was fallback-related."),
    ("The harness is `90_DECISIONS/D09_K6_HARNESS_DESIGN_v04.md` (with v01–v03 for unchanged sections), implemented in `50_CODE/k6/k6_sim_v02.py` and tested by `tests/test_k6_sim_v02.py` (13/13 pass).",
     "The harness is `90_DECISIONS/D09_K6_HARNESS_DESIGN_v05.md` and v04 (with v01–v03 for unchanged sections), implemented in `50_CODE/k6/k6_sim_v02.py` and tested by `tests/test_k6_sim_v02.py` (13/13 pass). The simulator is generated from `k6_sim_v01.py` by `make_k6_sim_v02.py`, `_step2` and `_step3`."),
    ("- **Choice.** The feasible candidate with the largest planned progress. If none is feasible, the emergency stop.",
     "- **Choice.** The feasible candidate with the largest planned progress.\n"
     "- **Fallback (C14).** If no candidate is feasible at the arm's margin (an *infeasible decision*), the margin is backed off on the same enforced set, λ ∈ {0.75, 0.5, 0.25, 0}. The planner takes the best candidate at the largest feasible λ, and the emergency stop only if λ = 0 is infeasible.\n"
     "- **Decision-mode replay devices, shared by every arm (R09b m10).**\n"
     "  - The planner's speed is the logged speed over a centred 0.5 s window, so it reads 0.25 s of the future log: a median difference of 0.06 m/s from the CTRV speed, 95th percentile 0.30 m/s.\n"
     "  - v_max is the scene's maximum logged speed + 2 m/s.\n"
     "  - Candidates are capped at the future logged positions (the leash)."),
]
for a, b in rep:
    assert s.count(a) == 1, a[:80]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("plan part 1 patched")
