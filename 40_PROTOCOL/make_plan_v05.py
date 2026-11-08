"""Make plan v05 from v04 (Claude line, 31 Oct 2026; R07c). Kept as the record of the edits. Numbers are read from the OC merges
(70_TESTS/m_scratch/oc_v04_T1.json, oc_v04_T3.json) and eps_v01.json, so the text cannot drift from the files.
Why v05:
- v04 section 9's criterion A2 failed at eps = 0.02 (OC v02, T1);
- R07c X-M1: an in-sample eps would pass A2 by construction, and HM6b's size hinged on a simulated variance.
So HM6b becomes the pooled cell's significance check, eps = 0.03 (derived from OC v02) is kept as a descriptive equivalence
margin, A2 is confirmed on fresh seeds (OC v03), and the R07c minor items are applied.
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
P4, P5 = os.path.join(HERE, "M_PREREGISTRATION_v04.md"), os.path.join(HERE, "M_PREREGISTRATION_v05.md")
S = os.path.join(os.path.dirname(HERE), "70_TESTS", "m_scratch")
eps = json.load(open(os.path.join(S, "eps_v01.json")))
oc = {t: json.load(open(os.path.join(S, "oc_v04_%s.json" % t))) for t in ("T1", "T3")}
old = {t: json.load(open(os.path.join(S, "oc_v03_%s.json" % t))) for t in ("T1", "T3")}


def p(t, k):
    return oc[t]["parts"][k]


def f(x):
    return "%.2f" % x


NULL, NULL8 = "e2null|rho0.5|effect1.00|logsd0.10", "e2null|rho0.8|effect1.00|logsd0.10"
L05, L20 = "e2null|rho0.5|effect1.00|logsd0.05", "e2null|rho0.5|effect1.00|logsd0.20"
P15, P20 = "e2power|rho0.5|effect1.50|logsd0.10", "e2power|rho0.5|effect2.00|logsd0.10"
E1N = "e1null|rho0.5|effect1.00|logsd0.10"
H16, H20, H26 = ("hm3power|rho0.5|effect%s|logsd0.10" % e for e in ("1.60", "2.00", "2.60"))
rT1, rT3 = p("T1", NULL)["HM6_fail"]["rate"], p("T3", NULL)["HM6_fail"]["rate"]
false_nogo = 1 - (1 - rT1) ** 2 * (1 - rT3)
t = open(P4, encoding="utf-8").read()
R = []
R.append(("# M pre-registration v04: the method stage (31 Oct 2026)", "# M pre-registration v05: the method stage (31 Oct 2026)"))
R.append(("""**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v03.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v04.txt`, which is not itself frozen. v01, v02 and v03 are kept unchanged; none of them was frozen.""",
          """**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v05.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v05.txt`, which is not itself frozen. v01–v04 are kept unchanged; none of them was frozen.

**Why v05.**
1. v04 §9 fixed acceptance criteria for the OC study. On the T1 layout **A2 failed at ε = 0.02**: a valid M\\* failed HM6 in 27 %% of null datasets, all through HM6b, the equivalence bound on the pooled val exceedance.
2. The third check, R07c (`70_TESTS/R07C_M_PREFREEZE_CHECK_v01.md`), found two further problems:
   - choosing ε from those same simulated datasets would pass A2 by construction;
   - the pass rate of an equivalence bound depends on a between-log variance that the simulation sets arbitrarily.
3. v05 therefore:
   - makes **HM6b the pooled val cell's significance check** (it fails if the pooled cell is significantly above δ). Its false-failure rate is the test's size, not a simulated variance;
   - keeps the equivalence bound UB_bc ≤ δ + ε with ε = %s (derived from OC v02) as a **reported, not decided** statement;
   - **confirms A2 on fresh seeds** (OC v03: 100 new null datasets per layout), with between-log SD 0.05 and 0.2 as sensitivities;
   - applies R07c's minor items (§13).
4. No real outcome had been computed.""" % eps["eps"]))
R.append(("""The best-powered check is HM6b, the pooled val exceedance, which detects a pooled exceedance of about 0.06 or more (§9).""",
          """The pooled val cell is checked for significant exceedance (HM6b), and its bias-corrected 95 %% upper bound is reported against δ + %s.
  - **Power at the real val layout (OC v03):** a planted val turning shift giving a turning-cell exceedance of about %s is caught by HM6 in %s of datasets on T1 and %s on T3; one of about %s in %s and %s.""" % (
              eps["eps"], f(p("T1", P20)["mean_turn_cell_E"]), f(p("T1", P20)["HM6_fail"]["rate"]), f(p("T3", P20)["HM6_fail"]["rate"]),
              f(p("T1", P15)["mean_turn_cell_E"]), f(p("T1", P15)["HM6_fail"]["rate"]), f(p("T3", P15)["HM6_fail"]["rate"]))))
R.append(("""**Confirmatory on T3 only.** On T1 it is foreknown (R06 found turning cars carry 68 % of exceedances, and the strata were designed from that), so T1 and T2 are reported but carry no weight. | HM3 |""",
          """**Confirmatory on T3 only.** On T1 it is foreknown (R06 found turning cars carry 68 %% of exceedances, and the strata were designed from that), so T1 and T2 are reported but carry no weight. **Power (OC v02, the frozen refit rule):**

| B6 lateral-turning exceedance about | 0.10 | 0.125 | 0.17 |
|---|---|---|---|
| T1 | %s | %s | %s |
| T3 | %s | %s | %s |

HM3 therefore detects only a motion-state effect of about 0.14 or more. The refit-CV inference is used because it carries calibration randomness, not for power. | HM3 |""" % (
              f(p("T1", H16)["HM3_holds"]["rate"]), f(p("T1", H20)["HM3_holds"]["rate"]), f(p("T1", H26)["HM3_holds"]["rate"]),
              f(p("T3", H16)["HM3_holds"]["rate"]), f(p("T3", H20)["HM3_holds"]["rate"]), f(p("T3", H26)["HM3_holds"]["rate"]))))
R.append(("""  - The turning share of moving cars is reported per setting and split from counts (`car_moving_turning_share` in the counts files).""",
          """  - The turning share of moving cars is reported per setting and split from counts (`car_moving_turning_share`), and by speed band in each run (`turning_share_by_speed_band`).
  - **"Turning" is a course-change state, not a manoeuvre label at low speed (R07c X-m5).** Position noise in a short chord reads as a course change. R07c measured, on tracker output, that 41–45 % of moving cars at 1–3 m/s are "turning", against 8–11 % at ≥ 8 m/s, and 52–59 % of moving pedestrians. The method's validity does not depend on it: strata are only a partition. The paper uses the term "course-change state" and reports the speed bands. E5 adds a minimum-chord sensitivity (§10)."""))
R.append(("""- **HM6 (transfer):** **(a)** M\\* is significantly under-covered in no E2 cell; and **(b)** the pooled val exceedance of M\\* has a **bias-corrected** UB ≤ δ + 0.02 (UB + max(bootstrap bias, 0); R07b N-m6).""",
          """- **HM6 (transfer):** **(a)** M\\* is significantly under-covered in no E2 cell; and **(b)** the pooled val cell ("all val items") is not significantly under-covered (its simultaneous LB ≤ δ; R07c X-M1).
  - Reported beside it: the bias-corrected UB (UB + max(bootstrap bias, 0); R07b N-m6) and whether UB_bc ≤ δ + %s (`pooled_equivalence_at_eps`).""" % eps["eps"]))
R.append(("""- **Inputs are verified.**""", """- **Probability of a false NO-GO.** Assume a valid method in all three settings, the OC null rates, and independence (T2 shares T1's layout). This is an upper bound, since T1 and T2 are positively correlated. HM6 alone then gives a false NO-GO with probability 1 − (1 − %s)²(1 − %s) = %s. HM1's null rate is 0 at these sizes (A1).
- **Inputs are verified.**""" % (f(rT1), f(rT3), f(false_nogo))))
R.append(("""- **Run:**
  - `run_m_main_v03.sh` runs T1, T2 and T3 in parallel. The peak working set of each loading step is logged in the counts files; with 15.7 GB of RAM, three parallel runs fit if each stays below about 4.5 GB, and otherwise they are run in turn.
  - It then runs `m_decide_v03.py`, but only if every run exited cleanly.""",
          """- **Run:**
  - `run_m_main_v04.sh` runs T1 and T2 in parallel and starts T3 once both have passed their loading peak, so the measured peaks (3.7, 3.3 and 4.4 GB) never overlap. No other job runs at the same time (R07c X-m8).
  - It then runs `m_decide_v04.py`, but only if every run exited cleanly, and checks the decision script's own exit code (R07c X-m9).
  - The 1 s and 4 s sections are fault-tolerant like E5."""))
R.append(("""- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v03.json` and `m_decision_v03.json`.""",
          """- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v04.json` and `m_decision_v04.json`."""))
R.append(("""  - The v03 modules: m_lib_v03, m_data_v03, m_sizes_v03, m_run_v03, m_decide_v03, m_freeze_v03, run scripts.
  - They are generated from v02 by the recorded patch scripts `tests/make_m_lib_v03.py` and `tests/make_m_run_v03.py`.""",
          """  - **The v04 modules run the study:** m_lib_v04, m_data_v04, m_sizes_v04, m_run_v04, m_decide_v04, m_freeze_v05, and `run_m_main_v04.sh`.
    - They are generated by the recorded patch scripts `tests/make_m_lib_v03.py` then `make_m_lib_v04.py`, and `make_m_run_v03.py` then `make_m_run_v04.py`.
    - Each generator reproduces its module byte for byte (R07c X-m12).
  - **The real counts files** were made by m_sizes_v03. m_sizes_v04 differs from it only in its imports. The run re-derives every stratum count and cell with the v04 code and stops if any differs."""))
R.append(("""2. Heading rate from the velocity direction for every group; from the yaw for every group (the default is course over ground).""",
          """2. Heading rate from the velocity direction for every group; from the yaw for every group (the default is course over ground); and course over ground counted as 0 when either chord is shorter than 1 m (`cog_min_chord_1m`; R07c X-m5)."""))
R.append(("""| M4 | Refit-CV bootstrap for E1 at 2 s; a baseline fails only if both inferences agree. |""",
          """| M4 | Refit-CV bootstrap for E1 at 2 s. *Superseded by v04 (R07b N-M2):* baseline failures are judged on refit-CV alone. |"""))
# section 9 rewrite
i9, i10 = t.index("## 9. Operating characteristics at the real counts"), t.index("## 10. Sensitivities")
sec9 = """## 9. Operating characteristics at the real counts (computed before the freeze)

**Procedure.**
- The OC study rebuilds the real item layout of T1 and of T3: per scene and stratum counts, scenes in their real logs, and records per scene.
- It simulates scores correlated within each scene and stratum (ρ = 0.5 and 0.8), with between-log effects of SD 0.1, and 0.05 and 0.2 as sensitivities.
- It runs the actual rules (`run_e1`, `run_e2`, `hypotheses_e1`, `hypotheses_e2`), fitting only the methods each part needs.
- The `only=` path equals the full path for M\\* and B6 (R07c S1).
- **Settings, disclosed (R07c X-m2):**
  - the E1 parts use 3 CV repetitions, fixed-rule B = 300 and refit-CV B = 60;
  - the E2 parts use B = 150;
  - the run uses 20, 2000, 200 and 1000.

**Two rounds.**
- **OC v02** (`tests/test_m_oc_v02.py`, shards in `70_TESTS/m_scratch/oc_v02/`) provides the E1 parts: e1null (A1), hm3power and component power.
- **OC v03** (`tests/test_m_oc_v03.py`, fresh seed labels "oc3", v04 rules, shards in `oc_v03/`) provides the E2 parts:
  - 100 null datasets at ρ 0.5 and log SD 0.1 (A2);
  - 20 at ρ 0.8;
  - 40 each at log SD 0.05 and 0.2;
  - 40 each with the val turning items scaled by 1.5 or 2.0.
- Merged by `merge_oc_v04.py`, which asserts the expected number of datasets per part, into `oc_v04_T1.json` and `oc_v04_T3.json`.

**Acceptance criteria.** All at ρ = 0.5, per layout.
- **A1:** M\\* is flagged by HM1 in at most 10 %% of null datasets, under the fixed rule and under the refit-CV rule.
- **A2:** HM6 fails in at most 10 %% of the 100 fresh null datasets at log SD 0.1.
- When they were fixed (v04, 14:55), the OC v02 results had not been seen. OC v01, which used a different, fixed-rule E2 test, had shown a 15 %% HM6 null failure rate (R07c X-m1).
- **History.** A2 failed in OC v02 under v04's equivalence-type HM6b (T1: 27 %% at ε = 0.02). The tolerance rule in `tests/derive_eps_v01.py` gave ε = %s (`eps_v01.json`), which is kept as the descriptive margin. HM6b was redefined (see "Why v05"), and A2 was then checked on fresh seeds.

**Results**

| Quantity | T1 (CANMOT layout) | T3 (Poly-MOT layout) |
|---|---|---|
| A1: M\\* flagged by HM1, null (fixed / refit-CV) | %s / %s | %s / %s |
| **A2: HM6 fails, 100 fresh null datasets** | **%s** (CI %s) | **%s** (CI %s) |
| HM6 fails, null, ρ 0.8 | %s | %s |
| HM6 fails, null, log SD 0.05 / 0.2 | %s / %s | %s / %s |
| Equivalence bound UB_bc ≤ δ + %s fails, null (descriptive) | %s | %s |
| HM6 fails, val turning ×1.5 (turning-cell E ≈ %s / %s) | %s | %s |
| HM6 fails, val turning ×2.0 (turning-cell E ≈ %s / %s) | %s | %s |
| HM3 holds, B6 lateral-turning E ≈ 0.10 / 0.125 / 0.17 | %s / %s / %s | %s / %s / %s |
| E1 component MDE80 per cell (range) | 0.10–0.30 | 0.10–0.30 |
| E2 component MDE80 per cell (range) | 0.15–0.30 | 0.15–0.30 |
| Acceptance A1 and A2 | %s | %s |

"Component" means the "significantly under-covered" component alone, under the fixed rule. Every validity statement in the paper is worded within these limits.

""" % (eps["eps"],
       f(p("T1", E1N)["Mstar_flag_fixed"]["rate"]), f(p("T1", E1N)["Mstar_flag_refit"]["rate"]), f(p("T3", E1N)["Mstar_flag_fixed"]["rate"]), f(p("T3", E1N)["Mstar_flag_refit"]["rate"]),
       f(rT1), p("T1", NULL)["HM6_fail"]["ci95"], f(rT3), p("T3", NULL)["HM6_fail"]["ci95"],
       f(p("T1", NULL8)["HM6_fail"]["rate"]), f(p("T3", NULL8)["HM6_fail"]["rate"]),
       f(p("T1", L05)["HM6_fail"]["rate"]), f(p("T1", L20)["HM6_fail"]["rate"]), f(p("T3", L05)["HM6_fail"]["rate"]), f(p("T3", L20)["HM6_fail"]["rate"]),
       eps["eps"], f(p("T1", NULL)["pooled_equivalence_at_eps_fails"]["rate"]), f(p("T3", NULL)["pooled_equivalence_at_eps_fails"]["rate"]),
       f(p("T1", P15)["mean_turn_cell_E"]), f(p("T3", P15)["mean_turn_cell_E"]), f(p("T1", P15)["HM6_fail"]["rate"]), f(p("T3", P15)["HM6_fail"]["rate"]),
       f(p("T1", P20)["mean_turn_cell_E"]), f(p("T3", P20)["mean_turn_cell_E"]), f(p("T1", P20)["HM6_fail"]["rate"]), f(p("T3", P20)["HM6_fail"]["rate"]),
       f(p("T1", H16)["HM3_holds"]["rate"]), f(p("T1", H20)["HM3_holds"]["rate"]), f(p("T1", H26)["HM3_holds"]["rate"]),
       f(p("T3", H16)["HM3_holds"]["rate"]), f(p("T3", H20)["HM3_holds"]["rate"]), f(p("T3", H26)["HM3_holds"]["rate"]),
       oc["T1"]["acceptance"]["all"], oc["T3"]["acceptance"]["all"])
t = t[:i9] + sec9 + t[i10:]
R.append(("""FROZEN_HASHES_BEGIN""", """**Changes from v04 (R07c; all made before any real outcome was computed)**

| R07c finding | Change |
|---|---|
| X-C1 | A2 failed at ε = 0.02 (OC v02). Plan revised (this version). |
| X-M1 | HM6b is now the pooled significance check. ε = %s is descriptive. A2 confirmed on 100 fresh null datasets per layout, with log-SD sensitivities and power. The K5 power sentence comes from OC v03. A false NO-GO bound is given (§8). |
| X-m1 | Qualifier on when the criteria were fixed (§9). |
| X-m2 | OC settings disclosed. Expected dataset counts asserted in the merge. |
| X-m3 | HM3 power in §1 and §9. Refit-only justified by calibration randomness. |
| X-m4 | `fixed_rule_alone` and `both_inferences` reported under their own names (m_lib_v04). |
| X-m5 | "Course-change state" wording, speed-band shares, and the E5 minimum-chord sensitivity. |
| X-m6 | Simulated dataset v03 docstring corrected; criterion 5 counts any car-turning cell; both tries disclosed in M_SYNTHETIC_TESTS v04. |
| X-m7 | §13 row M4 marked superseded. |
| X-m8 | Staggered T3 start (run_m_main_v04). |
| X-m9 | Fault-tolerant 1 s and 4 s sections; the decision's exit code is checked. |
| X-m10 | `tests/test_m_decide_checks_v01.py` (10 checks) frozen. |
| X-m11 | m_data_v04 asserts that the 10-dimensional state coincides with the CTRA classes for Poly-MOT. |
| X-m12 | v03 generators reproduce v03 byte for byte (the EPS edit was reverted). v04 changes are in new modules. |
| X-m13 | Stale texts corrected in the v04 files. |

FROZEN_HASHES_BEGIN""" % eps["eps"]))
for a, b in R:
    assert t.count(a) == 1, a[:100]
    t = t.replace(a, b)
open(P5, "w", encoding="utf-8", newline="\n").write(t)
print("plan v05 written,", len(R), "edits + section 9; false NO-GO bound %.3f" % false_nogo)
