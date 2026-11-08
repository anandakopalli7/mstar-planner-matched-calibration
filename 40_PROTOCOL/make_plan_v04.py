"""Turn the copy of plan v03 into plan v04 (Claude line, 31 Oct 2026; review R07b). Kept as the record of the edits."""
import os

P = os.path.join(os.path.dirname(os.path.abspath(__file__)), "M_PREREGISTRATION_v04.md")
t = open(P, encoding="utf-8").read()
R = []
R.append(("""# M pre-registration v03: the method stage (31 Oct 2026)

**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v02.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v03.txt`. v01 (`173bca05…`) and v02 are kept unchanged. v02 was never frozen.""",
"""# M pre-registration v04: the method stage (31 Oct 2026)

**Status.** This is the version to be frozen. It becomes binding when its hash block is filled and its `.sha256` sidecar is written by `50_CODE/m/m_freeze_v03.py`. The freeze hash is recorded in `M_FREEZE_RECORD_v04.txt`, which is not itself frozen. v01, v02 and v03 are kept unchanged; none of them was frozen. `M_PLAN_HASH_LOG.txt` lists the draft hashes. Its last v03 entry (`cec106ed…`) is the text that R07b reviewed.

**Why v04.** A second pre-freeze review, R07b (`70_TESTS/R07B_M_PREFREEZE_REREVIEW_v01.md`), checked v03 against R07 and found new problems: 1 critical, 3 major and 15 minor.
- **The critical one (N-C1).** Poly-MOT's CTRA model writes (speed, acceleration) into the exported velocity field. T3's in-path selection and motion states would have been built on it.
- **The majors.**
  - The motion-state claim had no clean confirmatory test (N-M1).
  - The E1 refit-CV bootstrap is still far too wide for M\* (N-M2).
  - The OC study measured the wrong E2 test and had no acceptance criteria (N-M3).

v04 fixes all of them. The table is in §13. No real outcome had been computed when any change was made."""))
R.append(("""| **K5** (validity) | DP-SCRC has a per-stratum finite-sample guarantee on the toward-ego exceedance of tracked, still-observable objects (P02 PM1, marginal over calibration). Empirically, its exceedance is **consistent with δ = 0.05** in every evaluated cell on held-out logs (E1, a consistency check) and **after transfer to the log-disjoint val split** (E2), on three tracker settings. | PM1; HM1 (E1); HM6 (E2) |""",
"""| **K5** (validity) | DP-SCRC has a finite-sample guarantee on the toward-ego exceedance of tracked, still-observable objects. It holds for each stratum with its own threshold, under i.i.d. scenes (P02 PM1, marginal over calibration). Empirically, its exceedance is **consistent with δ = 0.05** in every evaluated cell on held-out logs (E1, a consistency check) and **after transfer to the log-disjoint val split** (E2), on three tracker settings. The best-powered check is HM6b, the pooled val exceedance, which detects a pooled exceedance of about 0.06 or more (§9). | PM1; HM1 (E1); HM6 (E2) |"""))
R.append(("""| K5b (motion state) | Without motion-state strata (B6), at least one car turning stratum is significantly under-covered where DP-SCRC is not, with a significant paired difference | HM3 |""",
"""| K5b (motion state) | Without motion-state strata (B6), at least one car turning stratum is significantly under-covered where DP-SCRC is not, with a significant paired difference. **Confirmatory on T3 only.** On T1 it is foreknown (R06 found turning cars carry 68 % of exceedances, and the strata were designed from that), so T1 and T2 are reported but carry no weight. | HM3 |"""))
R.append(("""- **E1 is pinned for conformal methods.** On held-out logs, a conformal method's pooled held-out exceedance stays near δ by construction. R07's simulation S3 found its across-dataset SD to be about 0.11 of the bootstrap SE. HM1 is therefore a consistency check and not evidence of validity under shift. Validity rests on PM1, on the transfer test E2, and on the replication across settings.""",
"""- **E1 is pinned for conformal methods.** On held-out logs, a conformal method's pooled held-out exceedance stays near δ by construction.
  - R07 S3 found the fixed-rule bootstrap SE for M\* to be about 9 times its true SD.
  - R07b S1 found the refit-CV SE still 4.6–7.7 times too wide, with replicates biased upwards.
  - HM1 is therefore a consistency check under both inferences, not evidence of validity under shift.
  - Validity rests on PM1, the transfer test E2 (HM6b best of all) and the replication across settings."""))
R.append(("""- **Power is limited.** The smallest exceedance each cell can detect with 80 % power is measured by the operating-characteristic simulation at the real counts (§9) and reported with every claim. "Not significantly above δ" is never written as "at most δ".""",
"""- **Power is limited.** §9 measures:
  - the per-cell power of the "significantly under-covered" component;
  - the power of the actual E2 rule against planted val shifts;
  - the power of the actual HM3 rule.

  These are reported with every claim. "Not significantly above δ" is never written as "at most δ"."""))
R.append(("""| **T3** | Poly-MOT (Li et al., IROS 2023), CANMOT's `paper/baseline/poly_mot`: an EKF with a constant-turn-rate-and-acceleration model (CTRA) for cars, buses, pedestrians and trucks, and a linear KF with constant acceleration (CA) for bicycles, motorcycles and trailers. Poly-MOT's own Q and R (the CTRA Q is the identity). | **Different motion models, filter, Q and R, so the residuals differ.** T3 is the independent setting. |""",
"""| **T3** | Poly-MOT (Li et al., IROS 2023), CANMOT's `paper/baseline/poly_mot`: an EKF with a constant-turn-rate-and-acceleration model (CTRA) for cars, buses, pedestrians and trucks, and a linear KF with constant acceleration (CA) for bicycles, motorcycles and trailers. Poly-MOT's own Q and R (the CTRA Q is the identity). | **A different motion-model family, filter, Q and R, on the same detections, association and life cycle** (R07b N-m4). Its residuals differ, so it is the most independent of the three settings, though not fully independent. |"""))
R.append(("""**Shared by all three settings.** The CenterPoint detections, the scenes, logs and ground truth, the pairing code, and the item definition.""",
"""**Shared by all three settings.** These are the same in T1, T2 and T3:
- the CenterPoint detections;
- the preprocessing (score filter, NMS);
- the association metrics, thresholds and life cycle (Poly-MOT's published values; `nusc_config_poly_mot.yaml` differs from `nusc_config_rotate_cov_cv.yaml` only in filter and motion model);
- the scenes, logs and ground truth;
- the pairing code and the item definition.

**T3's velocity (R07b N-C1).** Poly-MOT's CTRA `getOutputInfo` writes state slots 6–7, which are (speed, acceleration), into the exported velocity field.
- **Correction.** The loader `m_data_v03` sets (vx, vy) = v·(cos θ, sin θ) from each CTRA record's own state (v = state[6], θ = state[8]), births included, before anything uses velocity: the in-path test, speed and heading rates. CA records and T1/T2 are unchanged.
- **Check, on tracker output only** (`tests/test_export_velocity_v01.py`; `70_TESTS/m_scratch/export_velocity_v01.json`). For moving cars, the median |velocity − displacement/time| is 7.22 m/s uncorrected and 0.74 m/s corrected, against 0.71 m/s on T1. Every CTRA class is within 0.5 m/s of T1. On T1 and T2 the loader is identical, field for field, to the X2 loader."""))
R.append(("""- **T3's** Q and R are fixed defaults.""",
"""- **T3's** Q and R are fixed defaults.
- **Shared by all three:** the association, life-cycle, score-filter and NMS thresholds are Poly-MOT's published values, selected on nuScenes val (R07b N-m4)."""))
R.append(("""- **T1's results for B0, B1 and B4 are largely foreknown** (X2 H1, H3 and K5; R07 m18).""",
"""- **T1's results for B0, B1 and B4 are largely foreknown** (X2 H1, H3 and K5; R07 m18). **So is HM3 on T1** (R06; R07b N-M1). HM3 is confirmatory on T3 only."""))
R.append(("""  - heading rate ω̂ = Δθ / Δt over j = 2 keyframes if the track has a record at k − 2, else over j = 1.
    - **θ is the velocity direction for pedestrians** (their detector yaw is mostly noise; R07 m13) **and the yaw for every other group**.
    - Yaw differences are wrapped to [−π/2, π/2), so a 180° flip does not read as a turn. Velocity-direction differences are wrapped to [−π, π).""",
"""  - **heading rate ω̂: the course-over-ground turn rate, for every group** (R07b N-M1).
    - It is the change in the direction of the track's own displacement between [k−4, k−2] and [k−2, k], divided by the time between the midpoints of the two intervals (about 1 s).
    - Without the record at k−4, it uses [k−2, k−1] and [k−1, k].
    - The exported positions are the tracker's estimates, so ω̂ is I_k-measurable. It does not depend on each tracker's yaw noise. On the same two scenes, the yaw rule labelled 49 % of Poly-MOT's moving cars "turning", against 4 % on CANMOT.
    - Directions are wrapped to [−π, π).
    - The yaw rate (yaw at k against k−2, else k−1, wrapped to [−π/2, π/2)) and the velocity-direction rate are kept as sensitivities (§10)."""))
R.append(("""  - **static** if ŝ < 1.0 m/s; otherwise **new** if there is no record at k − 1 or k − 2; otherwise **turning** if |ω̂| ≥ 0.10 rad/s; otherwise **straight**.""",
"""  - **static** if ŝ < 1.0 m/s; otherwise **new** if ω̂ is undefined (no history for either interval pair); otherwise **turning** if |ω̂| ≥ 0.10 rad/s; otherwise **straight**.
  - The turning share of moving cars is reported per setting and split from counts (`car_moving_turning_share` in the counts files)."""))
R.append(("""  - **refit-CV** (2 s only; R07 M4): B = 200 replicates. Each replicate resamples the 50 logs, assigns every copy of a log to the same fold, re-runs one 5-fold CV of every method, and recomputes the cell estimates. The replicates are centred at the fixed-rule point estimate.""",
"""  - **refit-CV** (2 s only): B = 200 replicates. Each replicate resamples the 50 logs, assigns every copy of a log to the same fold, re-runs one 5-fold CV of every method, and recomputes the cell estimates. The replicates are centred at the 20-repetition point estimate.
  - **Character of the refit-CV.** It carries calibration randomness. It is conservative:
    - about 5× for M\* (R07b S1);
    - about 1.4× for B6 under the null (R07b S2).

    Its replicate means run high, because duplicated logs act as distinct calibration units, and that also makes it conservative for flags. **Baseline failures are judged on the refit-CV inference** (§7); the fixed rule is reported beside it."""))
R.append(("""**Evaluation cells** (fixed from counts before the freeze; `60_RESULTS/m/m_sizes_*_v02.json`).""",
"""**Evaluation cells** (fixed from counts before the freeze; `60_RESULTS/m/m_sizes_*_v03.json`)."""))
R.append(("""- Per cell, the NaN share of replicates and the bootstrap bias are reported. Ē is the mean over cells that are present in every replicate (R07 m2, m17).""",
"""- Per cell, the NaN share of replicates and the bootstrap bias are reported. Ē is the mean over cells that are present in every replicate (R07 m2, m17).
- **Pooled cells (R07b N-m5).** A range-pooled, motion-pooled or remainder cell, or the pooled val cell, averages strata within each scene by item counts. Its null value is only approximately δ, even when every stratum meets PM1, and remainders include fallback strata. A flag in a pooled cell is evidence against the method, read with that caveat."""))
R.append(("""**A baseline b fails in cell c** when, in E1 at 2 s and under **both** the fixed-rule and the refit-CV inference, all three hold:""",
"""**A baseline b fails in cell c** when, in E1 at 2 s and on the **refit-CV inference** (R07b N-M2), all three hold:"""))
R.append(("""- **HM6 (transfer):** **(a)** M\\* is significantly under-covered in no E2 cell; and **(b)** the pooled val exceedance of M\\* has UB ≤ δ + 0.02.""",
"""- **HM6 (transfer):** **(a)** M\\* is significantly under-covered in no E2 cell; and **(b)** the pooled val exceedance of M\\* has a **bias-corrected** UB ≤ δ + 0.02 (UB + max(bootstrap bias, 0); R07b N-m6)."""))
R.append(("""- **HM3:** B6 fails in at least one cell of the pre-specified family, the single-stratum E1 cells of cars with motion state *turning*.""",
"""- **HM3:** B6 fails in at least one cell of the pre-specified family, the single-stratum E1 cells of cars with motion state *turning*.
  - If the family is empty, HM3 is recorded as untestable, not as false (R07b N-m2).
  - Confirmatory on T3 only (§1)."""))
R.append(("""## 8. Decision on the method stage (written into D07; script `m_decide_v02.py`)

- **METHOD GO-A:**
  - on T1 and on T3: HM1, HM6, HM2 for at least one of B1, B4, B9, and HM3;
  - on T2: HM1 and HM6.
- **METHOD GO-B:** as GO-A except HM3. The paper then presents motion strata as an option and makes no claim that they are needed.
- **NO-GO:** anything else.
  - If HM1 fails, the M\\*-log consistency is reported as the pre-registered remedy, labelled post hoc.
  - If HM6 fails, the diagnosis distinguishes log shift from detector shift (§2).""",
"""## 8. Decision on the method stage (written into D07; script `m_decide_v03.py`)

- **METHOD GO-A:** all of these hold:
  - HM1 and HM6 on T1, T2 and T3;
  - **the same** practitioner baseline (B1, B4 or B9) fails (HM2) on T1 and on T3 (R07b N-m1);
  - HM3 on T3.
- **METHOD GO-B:** as GO-A without HM3 on T3. The paper then presents motion strata as an option and does not claim they are needed. If T3 has no car-turning cell, the label is "GO-B (HM3 untestable)".
- **NO-GO:** anything else.
  - If HM1 fails, the M\\*-log consistency is reported as a pre-registered *diagnostic*. Adopting M\\*-log would need a new plan version, and any such claim is labelled exploratory (R07b N-m11).
  - If HM6 fails, the diagnosis distinguishes log shift from detector shift (§2).
- **Inputs are verified.** m_decide_v03 decides only if the results carry the frozen plan's hash, none is from test mode, each carries its own tracker label, and all three runs completed. `run_m_main_v03.sh` decides only if all three runs exit cleanly (R07b N-m8)."""))
R.append(("""- Each of K5a, K5a′ and K5b is claimed for a baseline only if it holds on T1 and on T3. T2 is reported beside them.""",
"""- K5a and K5a′ are claimed for a baseline only if it holds on T1 and on T3.
- K5b is claimed only if HM3 holds on T3.
- T2, and T1 for K5b, are reported beside them."""))
R.append(("""## 9. Operating characteristics at the real counts (computed before the freeze)

`50_CODE/m/tests/test_m_oc_v01.py` rebuilds the real item layout of T1 and of T3 (per scene and stratum counts, scenes in their real logs) with simulated, within-scene-correlated scores (ρ = 0.5, log effects of SD 0.1). It then runs `run_e1` and `run_e2` themselves and reports:
- (a) how often HM1 fails for a valid M\\* (fixed-rule and refit-CV);
- (b) how often HM6 fails for a valid M\\*;
- (c) per E1 and E2 cell, the power of the fixed-rule test against true exceedances of 0.10, 0.15, 0.20 and 0.30, and the minimum detectable exceedance at 80 % power;
- (d) the power of HM3's paired contrast.

The results are frozen with this plan (`70_TESTS/m_scratch/oc_v01_T1.json`, `oc_v01_T3.json`) and summarised in `70_TESTS/M_SYNTHETIC_TESTS_v02.md`. The paper quotes the minimum detectable exceedance beside every validity statement.""",
"""## 9. Operating characteristics at the real counts (computed before the freeze)

**Procedure.** `tests/test_m_oc_v02.py`, run by `run_m_oc_v02.sh` and merged by `merge_oc_v02.py`.
- It rebuilds the real item layout of T1 and of T3 (per scene and stratum counts, scenes in their real logs, records per scene) with simulated scores, correlated within each scene and stratum (ρ = 0.5 and 0.8), and log effects of SD 0.1.
- It runs the actual rules (`run_e1`, `run_e2`, `hypotheses_e1`, `hypotheses_e2`), fitting only the methods each part needs (R07b N-M3).
- The parts:
  - **e1null:** the HM1 failure rate for a valid M\\*, fixed rule and refit-CV;
  - **e2null:** the HM6 failure rate for a valid M\\*;
  - **e2power:** every val turning item's scale × 1.5 or × 2.0; the HM6a flag rate in the val turning cell and the HM6 failure rate;
  - **hm3power:** car lateral turning τ = 1.6, 2.0 or 2.6 against straight 1.2; the HM3 rate under the frozen rule, with the realised B6 exceedance;
  - **comp:** the per-cell power of the "significantly under-covered" component alone, against planted exceedances of 0.10–0.30 (labelled as component power; R07b N-m14).
- The E2 parts use B = 150, against 1000 in the run, and the refit-CV parts use B = 60, against 200.

**Acceptance criteria, fixed before the OC results were seen.** All at ρ = 0.5, per tracker layout.
- **A1:** M\\* is flagged by HM1 in at most 10 % of null datasets, under the fixed rule and under the refit-CV rule.
- **A2:** HM6 fails in at most 10 % of null datasets.

If A1 or A2 fails for T1 or T3, the plan is revised before the freeze: ε, the cell-size rule or the bound is changed, and the OC study is re-run. That revision and its reason go into v05. The OC results (`70_TESTS/m_scratch/oc_v02_T1.json`, `oc_v02_T3.json`) are frozen with this plan and summarised in `70_TESTS/M_SYNTHETIC_TESTS_v03.md`. Every validity statement in the paper quotes the relevant power."""))
R.append(("""2. Heading rate from the velocity direction for every group; from the yaw for every group.""",
"""2. Heading rate from the velocity direction for every group; from the yaw for every group (the default is course over ground)."""))
R.append(("""- **Code:** `50_CODE/m/` (m_lib_v02, m_data_v02, m_sizes_v02, m_run_v02, m_decide_v02, m_freeze_v02, run scripts) and its `tests/`. Also `50_CODE/x1/x1_lib_v03.py`, the export and propagation code of T2 and T3, and the v01 files, which are kept as the pre-review record.
- **Run:** `run_m_main_v02.sh` runs T1, T2 and T3 in parallel (memory per run is about 2–3 GB after the in-path filter of m_data_v02), then `m_decide_v02.py`. It runs unattended and has no branch on any result.
  - Each run refuses to start unless the plan hash, the frozen files, the input binding and the numpy/scipy versions match.
- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v02.json` and `m_decision_v02.json`.""",
"""- **Code:** `50_CODE/m/` and its `tests/`.
  - The v03 modules: m_lib_v03, m_data_v03, m_sizes_v03, m_run_v03, m_decide_v03, m_freeze_v03, run scripts.
  - They are generated from v02 by the recorded patch scripts `tests/make_m_lib_v03.py` and `tests/make_m_run_v03.py`.
  - Also `50_CODE/x1/x1_lib_v03.py`, and the export and propagation code of T2 and T3.
  - The CANMOT files that define T3's predictions (motion model, filter, class constants, Poly-MOT configs).
  - v01 and v02 are kept as the pre-review record.
- **Run:**
  - `run_m_main_v03.sh` runs T1, T2 and T3 in parallel. The peak working set of each loading step is logged in the counts files; with 15.7 GB of RAM, three parallel runs fit if each stays below about 4.5 GB, and otherwise they are run in turn.
  - It then runs `m_decide_v03.py`, but only if every run exited cleanly.
  - Partial results are written after every section, and a failing sensitivity is recorded, not fatal (R07b N-m7).
  - Each run refuses to start unless the plan hash, the frozen files, the input binding and the numpy/scipy versions match.
- **Outputs:** `60_RESULTS/m/m_result_{canmot_sc,sampletv,polymot}_v03.json` and `m_decision_v03.json`."""))
R.append(("""FROZEN_HASHES_BEGIN""", """**Changes from v03 (R07b; all made before any real outcome was computed)**

| R07b finding | Change |
|---|---|
| N-C1 | T3 velocity rebuilt from the CTRA state in `m_data_v03`. Export-level velocity check on tracker output. T3 counts and OC built only after the fix. |
| N-M1 | Course-over-ground turn rate for every group. HM3 confirmatory on T3 only; T1 foreknown. Turning shares reported. |
| N-M2 | Refit-CV described as conservative (about 5× for M\\*). Baseline failures judged on refit-CV alone; the fixed rule reported. |
| N-M3 | OC v02 runs the actual E2 and HM3 rules, at ρ = 0.5 and 0.8, with acceptance criteria A1 and A2 (§9). |
| N-m1 | The same practitioner baseline must fail on T1 and T3. |
| N-m2 | HM3 untestable is recorded and labelled. |
| N-m3 | The simulated dataset v02 has lateral cars, so HM3 has a known answer (end-to-end criterion 5). The v02 relaxation of criterion 3 is disclosed. |
| N-m4 | T3 wording; shared association, life-cycle and preprocessing values added to the tuning list. |
| N-m5 | Pooled-cell caveat (§7). |
| N-m6 | Bias-corrected UB for HM6b. |
| N-m7 | Partial saves; fault-tolerant sensitivities; sd floor. |
| N-m8 | m_decide_v03 verifies its inputs; the main script checks exit codes. |
| N-m9 | m_freeze_v03 asserts all_ok for every test output and freezes the CANMOT T3 files, the split receipts and T1's equivalence file. |
| N-m10 | Peak memory logged; parallel run conditional on it. |
| N-m11 | Wording of K5, the remedy and §13. |
| N-m12 | The hash log is not appended after the freeze; the freeze record is a separate file. |
| N-m13 | The B2 cap flag is reported. |
| N-m14 | OC component power labelled as such. |
| N-m15 | HM6b named the best-powered validity check (§1). |

FROZEN_HASHES_BEGIN"""))
for a, b in R:
    assert t.count(a) == 1, a[:100]
    t = t.replace(a, b)
open(P, "w", encoding="utf-8", newline="\n").write(t)
print("plan v04 written,", len(R), "edits")
