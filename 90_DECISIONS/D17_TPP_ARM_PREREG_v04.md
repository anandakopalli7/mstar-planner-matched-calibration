# D17: pre-registration of the deployed-predictor arm (Trajectron++ on nuScenes val), v04

**Status.** Pre-registration v04, 4 Nov 2026, for freezing by `50_CODE/tpp/tpp_freeze_v02.py`. The plan counts as frozen only when its FROZEN_HASHES block (end of file) is filled, its `.sha256` sidecar matches, and that hash is a line of `40_PROTOCOL/D17_PLAN_HASH_LOG.txt`. Those three are written only by `tpp_freeze_v02`, into the canonical log only (no override for a plan under 90_DECISIONS), and `c1_guard_v02.frozen_plan` checks them.

**What v04 is.** v04 = v03 (kept unchanged) with the fixes of check R18b (`70_TESTS/R18B_D17_V03_CHECK_v01.md`):
- N1 (D16 v15 Choice 36): the superseded analysis entry points `tpp_analyse_v01`, `v02` and `v03` and the superseded `tpp_freeze_v01` are archived byte-exact in `50_CODE/tpp/superseded_originals/` (with SHA256SUMS). Their live copies refuse real inputs, or any plan under 90_DECISIONS, in `main()` only, naming `tpp_analyse_v04` and `tpp_freeze_v02`. Their imported functions are unchanged, and their test suites reproduce the earlier synthetic outputs exactly.
- n2: the freeze writes the real plan into the canonical D17 log only. n3: the code uses `c1_guard_v02`. n4: seed-run distinctness compares predictions. n5: §9 item 3 is settled. n6: the tracker arm's sd is checked against K8's item sd. n7: trivial ties are labelled.

**What v03 was.** v03 = v02 with the fixes of review R18 (`70_TESTS/R18_D17_REVIEW_v01.md`), as decided in `D16_DELEGATED_CHOICES_v12.md` Choice 32. v01 and v02 are kept unchanged.
- M1: K7 rule (iii) is split. Its family no-flag test is gating; its count floor is reported only.
- M2: the analysis fails safe.
- M3: every code file, input and configuration value is bound by hash, and checked against the hash log.
- M4: every CRC decision is exact.
- M5: scoring is along the K8 tracker-planner's constraints.
- The minors m1–m9 (§9).

**Outcome-blind statement.** Before the freeze, the only quantities computed on the real Trajectron++ outputs are:
- counts, array shapes, finiteness and positive-definiteness checks (§3; `30_DATA/tpp_v01/tpp_counts_v01.json`);
- the predictor's self-consistency across runs, seeds and platforms (`tpp_xplat_compare_v01.py`, `tpp_spread_v01.py`): the same records predicted twice and compared with each other, with no ground truth.

No exceedance, coverage, NEES/ANEES, projected-error quantile, residual-to-sigma comparison or calibration multiplier has been computed on them. R18 reproduced the analysis on synthetic data only.

**Sources.**
- `D16_DELEGATED_CHOICES_v02.md` Choice 3;
- `D16_DELEGATED_CHOICES_v10.md` Choices 23 and 27–30;
- `D16_DELEGATED_CHOICES_v12.md` Choice 32;
- `30_PRIOR_ART/P7_L5_DEPLOYED_PREDICTOR_ARM_v01.md` §B.1, §B.4, §C.1, §C.3;
- `20_DESIGN/MANUSCRIPT_DRAFT_v02.md` §III–IV;
- `D14_K8_DESIGN_v05.md` (populations);
- `40_PROTOCOL/K7_PREREGISTRATION_v02.md` §5 (HK1);
- `ERRATA_K8_v02` E15 (exact CRC).

## 1. Question and role

**Question.** Along **the K8 tracker-planner's constraints** — its relied object axis, pair gap and toward-ego sign on its own items — does the covariance of a deployed, public, learned motion predictor support the linearised chance-constraint premise? If not, does the decision-projected recalibration (DP-SCRC, manuscript §IV) remove every detectable excess on held-out scenes, and at what margin?

A planner that derived its constraints from Trajectron++'s own mean would rely on other constraints and signs. That is a different question, outside this plan.

This answers reviewer item R14 O1 ("a predictor nobody deploys").

**Role** (D16 v10 Choice 29).
- This nuScenes arm is **development-side evidence** under this plan, frozen before any outcome.
- The confirmatory test of a deployed learned predictor is **H9 on the 375 AV2 logs** (D16 v10 Choice 23), with the floor of 6.

## 2. Hypotheses

**Expected direction** (PSU-TF, arXiv 2110.03267). With CenterPoint + AB3DMOT tracks, Table IV reports for Trajectron++ vehicle predictions at 2 s:
- ΔESV₂ = −0.72: about 0.14 of outcomes fall inside the 2σ region, against an ideal 0.865;
- ΔESV₁ = −0.35.

With EKF-tracked ground-truth inputs (Table III), ΔESV₂ = −0.45.

So, before any outcome, we expect **residuals larger than the predicted spread**. Magnitudes are not predicted.

The hypotheses below are stated per tracker (T1 and T3), on the analysis set of §3 at 2.0 s, with V2 and tracker histories, at the primary seed and at each S1 seed.

| ID | Statement | Test | Role |
|---|---|---|---|
| **H1** | Raw Trajectron++ (B0, margin z₀.₉₅·sd) is overconfident along a*: the pooled scene-level exceedance is above δ = 0.05 | Pooled cell flagged pointwise: one-sided log-bootstrap lower bound > δ | Primary (directional) |
| **H2** | Cross-fitted DP-SCRC (M\*) on Trajectron++ V2 shows **no cell above δ** on held-out scenes | On each of PD7, SD1_7 and PD (§6): (i) no evaluable cell flagged in the one-sided simultaneous sup-t at 0.95; (ii) the pooled cell is evaluable and not flagged; (iii-a) no power-qualified family cell flagged in its own sup-t. The count floor (iii-b, ≥ 6 cells) and HK1c are reported, not gating | Primary (method) |
| **H3** | **History-input effect:** raw exceedance with tracker histories exceeds raw exceedance with ground-truth histories | Paired pooled difference TPP_B0 − TPPgt_B0, one-sided 0.95 simultaneous lower bound > 0 | Secondary |
| H4 | Shape and cost: stratum dependence of the needed inflation; M\* margin against B3 and B4; TPP_M\* margin against TRK_M\* margin on the same items; V1 against V2; scene-level exceedance of TPP_B0, TPP_M\* and TRK_M\* by history stratum {2, 3–4, ≥5} and by class group | Point estimates, with intervals where `eval_stats` gives them; no decision | Descriptive |

**Wording of an H2 pass.** "No cell shown above δ (one-sided simultaneous test at 0.95); k power-qualified cells per population; floor of 6 met or not met", with the counts. It is never worded "valid".

**Wording of an H2 failure.** "DP-SCRC not shown free of excess for this predictor on 146 scenes", with the failing condition. It is never reported as a pass of a weaker form.

**Multiplicity.** H1–H3 are tested separately, each at one-sided 0.95, on 2 trackers × 3 seeds × (for H2) 3 populations, with no correction across hypotheses. This is acceptable for development-side evidence. A claim needs the conjunction over both trackers and all three seeds (§7), which is stricter than any single test. No familywise error rate is claimed.

## 3. Data, items and counts

**Scenes.** The 150 official nuScenes val scenes (18 logs), in the caches `30_DATA/k6/cache_v02_{t1,t3}_val`. Trajectron++ was trained on all 700 train scenes, so val is out-of-sample and no train scene is used.

**Development scenes are excluded** (D16 v10 Choice 29): scene-0103, scene-0553, scene-0796 and scene-0916, as in every K8 analysis. 146 scenes remain.

**Items.** These are the K8 records and items, as `50_CODE/k8/k8_items_v02.scene_items` builds them. `50_CODE/tpp/tpp_keys_v01.py` imports it read-only and unchanged, and copies its fields:
- scene, k, h, row and inst;
- `pair`;
- strata g, r, m and l0;
- the relied axis `rel`;
- the per-axis pair gaps;
- the item axis `a` and `ref_relied`.

**Join.** Records join on (scene name, pair) and items on (scene name, pair, axis). Both are 1:1 with K8's enumeration (test K1, full val, both trackers).

**Constraint geometry: the K8 tracker-planner's** (Choice 32 M5). Nothing is recomputed in the analysis.
- **Object axis:** from the tracker yaw, as K8.
- **Relied axis and pair gap:** K8's, copied. SD1_7 uses K8's gap of the relied axis.
- **Toward-ego sign:** the sign K8's own signed errors carry. `tpp_keys_v01` stores it, and test K3 verifies that it reproduces K8's D on every record of both trackers (max error 1.4×10⁻¹⁴).
- **Reference ego pose:** K8's items evaluate the relied axis, the gap and the sign at K8's reference ego pose: the **logged** ego pose at t_k + h (the decision mode's leash), with the rear axle moved R2C forward. The range strata come from the sensor's CTRV. This plan uses those values unchanged, as `D16_DELEGATED_CHOICES_v14.md` (correction to Choice 32 M5) rules and `ERRATA_K8_v03.md` E16 records (§9 item 3).

**Score.** For each arm:
- D = a*ᵀ(g − μ), with g the annotated centre at k + 4;
- sd = √(a*ᵀΣa* + σ_a²), with σ_a = 0.10 m;
- an exceedance means D > margin.

**Populations.** These are K8's definitions (D14 v05) restricted to this arm's coverage.

This plan's **"PD7"** is:
- K8's relied (`ref_relied`) items at h = 3;
- restricted to classes Trajectron++ covers (car, truck, bus, trailer, pedestrian; no two-wheelers);
- restricted to records with ≥ 2 contiguous tracker states at k;
- restricted to records with status ok in both Trajectron++ arms;
- with the development scenes excluded.

It is a subset of K8's PD7. On it:
- **SD1_7** = PD7 items with pair gap ≤ 5 m;
- **PD** = PD7 items that are in-path.

**Coverage rules** (P7-L5 C.3).
- car, truck, bus and trailer map to VEHICLE; pedestrian maps to PEDESTRIAN.
- Trailers follow Trajectron++'s training categories and are counted separately.
- motorcycle and bicycle are not covered: they are excluded and counted.

**Counts** (`30_DATA/tpp_v01/tpp_counts_v01.json`, listed in `SHA256SUMS_v01.txt`; counts only; all 150 scenes):

| Quantity | T1 | T3 |
|---|---|---|
| Scenes / logs / development scenes | 150 / 18 / 4 | 150 / 18 / 4 |
| K8 records, all steps / at 2 s | 146,167 / 34,552 | 146,323 / 34,579 |
| K8 items, all steps / at 2 s | 247,432 / 58,386 | 247,761 / 58,618 |
| K8 PD7 / SD1_7 / PD items at 2 s | 34,440 / 5,323 / 1,681 | 34,518 / 5,352 / 1,636 |
| Records at 2 s: car / truck / bus / trailer / pedestrian / motorcycle / bicycle | 18,574 / 3,023 / 861 / 728 / 10,322 / 602 / 442 | 18,605 / 3,024 / 860 / 747 / 10,307 / 596 / 440 |
| Join: records with a run row / total | 146,167 / 146,167 | 146,323 / 146,323 |
| Status at 2 s, tracker histories: ok / not covered / history < 2 / other | 28,861 / 1,044 / 4,647 / 0 | 28,883 / 1,036 / 4,660 / 0 |
| Status at 2 s, GT histories: ok / not covered / history < 2 / other | 32,719 / 1,044 / 789 / 0 | 32,755 / 1,036 / 788 / 0 |
| PD7 at 2 s ok, tracker histories, by history stratum 2 / 3–4 / ≥5 | 4,158 / 6,363 / 18,244 | 4,186 / 6,389 / 18,259 |

**Analysis set** (development scenes excluded; PD7 at 2 s, ok in both arms):
- **T1: 27,044** items (SD1_7 4,499; PD 1,512);
- **T3: 27,119** items (SD1_7 4,533; PD 1,463).

Both sets come from 144 of the 146 scenes.

Items whose V2 trace exceeds 100 m² in either Trajectron++ arm: T1 49, T3 83. They are dropped only in the tail sensitivity (§6).

**Integrity.**
- Every ok row is finite, and its V2 is positive definite.
- Non-ok rows are NaN.
- One step-4 mixture is stored per predicted 2-s row, with weights summing to 1.
- No not-PD, non-finite, not-predicted or missing-node status occurred.

## 4. Predictor and variants

**Model.**
- Trajectron++ ECCV 2020, branch `eccv2020`, commit `ef0165a93ee5ba8cdc14f9b999b3e00070cd8588`.
- `int_ee`, `model_registrar-12.pt`, SHA-256 `3fcc65cd8f48b70fce4965813e503e03c664e027f1f83f8a27d317773a138028`.
- `int_ee` stays primary unless the nuScenes map expansion v1.3 arrives before the freeze (D16 v10 Choice 30). `int_ee_me` would then need a new version of this plan.

**Inference** (`50_CODE/tpp/tpp_run_v01.py`; our online adaptation, §9 items 4–6).
- One `OnlineTrajectron` per scene, streamed over every keyframe.
- Per node, one causal state per keyframe from its contiguous history.
- Nodes: every deployed track of a covered class, plus the logged ego as `ego`.
- Positions are offset by the `process_data.py` rule.
- Decoder: `_run_decoder` as `sample_model` calls it, with `full_dist=True`, `num_samples=1`, `gmm_mode=False` and horizon 6.

**Platform.** Every production output comes from one platform: the laptop (Windows 11, `50_CODE/env/tpp38`: Python 3.8.20, torch 1.4.0+cpu, numpy 1.18.5).
- The Linux pod attempt stopped at its cross-platform gate (`70_TESTS/tpp_v01/pod_attempt1`).
- The laptop-to-pod gap: V2 mean 0.26 mm; per-row V2 Σ relative difference p99 1.6–2.5 %, max 14.5 %; sd along a*, p99 0.4–0.7 %.
- That gap is one to two orders of magnitude below the seed-to-seed spread on full val: sd along a*, p99 44–45 %; V2 mean up to 2.83 m. The gap is the decoder's sampling, amplified, not a platform effect.
- Files: `70_TESTS/tpp_v01/seed_laptop/spread_seed_full_val_v01.json` and `spread_seed_and_platform_v01.json`.

**Seed.**
- The decoder conditions on sampled controls, so one forward pass is one random draw. The seed is fixed per (scene, keyframe, node): SHA-256 of `scene|k|node|<base>`.
- **Primary: base seed 20261102**, a single pre-stated draw (D16 v10 Choice 27). A deployed planner consumes one forward pass per agent, and DP-SCRC treats the draw's randomness as part of the predictor.
- S1 seeds: 20261104 and 20261105, tracker histories only (§6b).

**Extreme-covariance tail.**
- 0.10 % (T1) and 0.23 % (T3) of 2-s rows have V2 trace > 100 m², with a maximum of 4.5×10⁵ m². They are finite and PD.
- They are **kept as published**, with no cap (D16 v10 Choice 28). A pre-stated sensitivity excludes them (§6).

**Variants.**
- **V2 (primary):** moment-matched, μ = Σπₖμₖ, Σ = Σπₖ(Σₖ + dₖdₖᵀ).
- **V1 (secondary):** the largest-π component. It can be singular: Unicycle components with |dφ| ≤ 0.01 carry rank-1 position covariance. σ_a keeps sd > 0.
- **S2 (descriptive):** the seed-pooled V2 (§6b).
- V3 (the exact mixture tail) is not analysed; the step-4 mixtures are stored.

**Inputs.**
- Tracker histories (primary).
- Raw ground-truth histories (upper bound), at seed 20261102 only.
- Stated limitations, not run (D16 v10 Choice 30): Σ + Σ_track (the caches hold no current-state covariance), and Trajectron++'s EKF-smoothed GT input.

## 5. Calibration and comparators

**Folds.**
- The sorted names of the 146 non-development scenes are permuted with `numpy.random.default_rng(20261102).permutation`.
- `numpy.array_split` cuts them into **5 folds of 30, 29, 29, 29 and 29 scenes**.
- Each method is fitted on 4 folds and applied to the 5th. The fold lists are written into the output.

**Methods.** All margins are along a*. Each is fitted once, on this plan's PD7 items at h = 3, and evaluated on PD7, SD1_7 and PD. The same methods are applied identically to TPP, TPPgt and TRK (the tracker's own propagated prediction on the same items and folds).

| Method | Margin |
|---|---|
| B0 | z₀.₉₅·sd (raw) |
| B4 | One pooled scene-level CRC threshold ĉ·sd |
| B3 | Certified single multiplier: the maximum of M\*'s thresholds |
| **M\*** | Per-L0 scene-level CRC (δ = 0.05) with the count-based fallback chain L0 ⊂ L1 ⊂ L2 ⊂ L3, n_min = 19 (`m_lib_v04.fit_hier`) |

**Exact CRC** (E15, Choice 32 M4).
- Every CRC accept/reject decision — M\*, B4, and B3 through M\* — is made in rational arithmetic (`c1_crc_exact_v01.crc_threshold_exact`).
- The result depends on the multiset of scenes only, not their order.
- Exact ties (bound = δ exactly at the chosen threshold) are counted and reported.

**Definitions that differ from K8** (m6). These must be stated wherever K8 is cited.
- **M\*** here is the method-stage 96-stratum fit, fitted on relied items at 2 s only. It is **not** K8's `Mstar_ip` (192 thresholds, in-path split, all steps).
- **Cells** are E2 cells (`make_cells(kind="E2")`), not K8's 32-cell family.
- **Folds** split scenes, so scenes of one log can fall into different folds, unlike K8's log folds. This is a stated limitation.
- **"PD7"** is restricted as defined in §3.

## 6. Endpoints and tests

All statistics come from `50_CODE/m/m_lib_v04.py`, imported unchanged.

**Evaluation cells.** `make_cells(kind="E2")`. A cell needs ≥ 39 scenes from ≥ 8 logs.

**Estimand.** Scene-level exceedance: the mean over scenes of each scene's share of items with D > margin.

**Inference.**
- Log-cluster bootstrap, B = 2000, seed 20261103.
- One-sided simultaneous sup-t at 0.95 over the evaluable cells.
- A cell is flagged when its lower bound > δ, or when its SE is zero and its estimate > δ.
- The pooled cell is tested pointwise.

**Checks, per population, for TPP_M\* and every comparator.**
- (i) No evaluable cell is flagged.
- (ii) The pooled cell is evaluable — **checked**: ≥ 39 scenes and ≥ 8 logs (`k6_analyse_v02.evaluable`) — and not flagged.
- **HK1c:** the pooled one-sided 0.95 upper bound ≤ δ + 0.03 is reported.
- The sup-t quantile of TPP_M\* must be finite wherever an SE is positive (asserted).
- An empty population is a stated NO for H2, never a crash.

**K7 rule (iii) for TPP_M\*** (Choice 32 M1).
- **(iii-a), gating:** no cell of the power-qualified family is flagged in the family's own sup-t.
- **(iii-b), reported only:** the family size against F_MIN = 6.
- The power rule is K7's, `k6_analyse_v02.power_family`, imported unchanged: power ≥ 0.80 to be flagged at a true rate of 0.15; beta-binomial with intra-scene correlation 0.5; 200 datasets; the first 500 bootstrap weights; seed [20261108, population index].

**Tail sensitivity** (pre-stated, D16 v10 Choice 28 as amended by Choice 32).
- The primary analysis is repeated without the records whose V2 trace exceeds 100 m² in either Trajectron++ arm. The set stays paired.
- **Exceedance, the checks and mean margins** are reported. This arm measures no planner outcome, so there is no infeasibility endpoint.

**A6-type diagnostics** (descriptive, pooled). On the relied records' 2-D position block, with σ_a²I added:
- scene-level and record ANEES;
- median NEES;
- χ²₂ ellipse coverage at 50/90/95/99 %.

**H4 breakdowns** (descriptive). On PD7, the scene-level exceedance of TPP_B0, TPP_M\* and TRK_M\*, with item and scene counts:
- by history stratum {2, 3–4, ≥5};
- by class group.

**Fail-safe rules** (Choice 32 M2). Each of these is an error that stops the analysis:
- A missing tracker-history run, ground-truth run or S1 seed run.
- A run whose meta (source, seed, model, keys hash) does not match its role.
- Fewer than three distinct tracker-history runs, by content hash.
- NaN or inf in any analysed D, V or ground truth.
- An undecidable verdict.

S1 is never skipped silently.

### 6b. Secondary pre-registered analysis S: seed sensitivity (D16 v10 Choice 27)

**S1.** `tpp_analyse_v04.analyse_v04`, the same function as the primary, is run once per S1 seed.
- It uses that seed's tracker-history run in place of the primary one: `30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_<t>_trk_val_seed<seed>_v01.npz`.
- Everything else is held at the primary: the same ground-truth run (seed 20261102), the same folds, the same bootstrap seed.
- S1 therefore varies the **tracker-history Trajectron++ arm only**. For H3 it varies TPP_B0 against the primary-seed TPPgt_B0.
- "Seed-robust" means: holds under these three draws. It is not a statement about the decoder's whole sampling distribution.

**S2 (descriptive).**
- At 2 s, the equal-weight mixture of the three seeds' stored 25-component mixtures (75 components, weights w/3), moment-matched (`tpp_analyse_v02.pooled_run`).
- Analysed through `analyse_v04`. No hypothesis is decided on S2.

## 7. Decision and reporting rules

One coded decision is made per hypothesis, across T1 × T3 × the three seeds (`tpp_analyse_v04.decide`):

| Code | When |
|---|---|
| **SUPPORTED** | The hypothesis holds on both trackers under the primary seed and both S1 seeds |
| **SEED_DEPENDENT_NOT_SUPPORTED** | It holds on both trackers at the primary seed but not under every S1 seed. The note names the case: "primary plus one S1 seed" or "primary seed only" |
| **NOT_SUPPORTED** | It fails on at least one tracker at the primary seed |

**Fixed choices, whatever the outcomes:**
- V2 stays primary whatever V1 shows.
- Tracker histories stay primary whatever the upper bound shows.
- `int_ee` stays primary (§4).
- No seed is promoted after outcomes.
- No swaps.

**Every result is reported:** every arm, method, variant, population, the sensitivity, S1 and S2.

**What the certificate is.** It is development-side and scene-level, transductive within val, and on this plan's "PD7" population. It holds along the K8 tracker-planner's constraints, for `int_ee` with our online adaptation.

## 8. Analysis, freeze and tests

**Code bound by the freeze.** `tpp_analyse_v04.code_files()` lists every file the analysis executes. The freeze writes a FROZEN_HASHES block, and a FROZEN_ROLES block (`tpp_analyse_v04.roles_of`):
- `entry:tpp_analyse` names `tpp_analyse_v04.py` as the one entry point;
- `module` covers the imported files;
- `config` covers the configuration;
- `data:<tracker>:<role>` covers each input.

On real data, `c1_guard_v02.verify_runtime` requires the running entry point to be the plan's named one, and every loaded project module to be bound under its own W-relative path. `verify_runtime_again` repeats the check before the output is written.

| File | Role |
|---|---|
| `50_CODE/tpp/tpp_analyse_v04.py` | The analysis |
| `50_CODE/tpp/tpp_analyse_v02.py` | Folds, S2 pooling, the K7 floor rule (live copy; `main()` refuses real inputs) |
| `50_CODE/tpp/tpp_analyse_v01.py` | Inputs, item table, A6 (live copy; `main()` refuses real inputs) |
| `50_CODE/tpp/tpp_common_v01.py` | Shared helpers |
| `50_CODE/m/m_lib_v04.py` | Statistics |
| `50_CODE/x1/x1_lib_v03.py` | Imported by `m_lib_v04` |
| `50_CODE/k6/k6_analyse_v02.py` | K7 power rule, evaluability |
| `50_CODE/k6/k6_sim_v02.py` | Imported by `k6_analyse_v02` and `k8_items_v02` |
| `50_CODE/c1_av2/c1_crc_exact_v01.py` | Exact CRC |
| `50_CODE/c1_av2/c1_guard_v02.py` | Frozen-plan guard (canonical logs, role-aware binding) |
| `50_CODE/k8/k8_items_v02.py` | K8's items, for the sd check (n6) |
| `50_CODE/tpp/tpp_analysis_config_v01.json` | Configuration |

The configuration holds B = 2000, every seed, δ, the level, n_min, F_MIN, the tail cap, the development scenes and the trackers. The analysis asserts that it equals the constants of the code it configures.

**Inputs bound by the freeze.** Per tracker:
- the keys;
- the primary tracker-history and GT runs;
- the two S1 seed runs;
- the cache MANIFEST;
- `30_DATA/tpp_v01/SHA256SUMS_v01.txt` and `seed_sensitivity/SHA256SUMS_seed_v01.txt`.

Each is bound under its own path and checked in its role (`c1_guard_v02.require_bound(frozen, path, role)`). Every run must also be listed with its hash in its SHA256SUMS file.

**`c1_guard_v02` is the C1 author's file and was still being edited on 4 Nov.** This plan was tested against its version `00d9bc42713ee3e5…`. The freeze binds whatever version exists at that moment, so the freeze should follow the C1 author's final version, and the v04 suite should be re-run on it (the freeze's `--test` does this).

**Superseded entry points** (D16 v15 Choice 36).
- `superseded_originals/` holds the byte-exact originals: `tpp_analyse_v01` `7df5d572…`, `v02` `67b42458…`, `v03` `1d5645b6…` and `tpp_freeze_v01` `d16cb925…`, with `SHA256SUMS_superseded_originals_v01.txt`.
- The live copies differ only in `main()`.
- Their suites, re-run, give identical synthetic outputs: `70_TESTS/tpp_v01/choice36_rerun/compare_before_after_v01.json`, all identical.
- `c1_predarm`'s guard belongs to the C1 author (Choice 34.2). It is not part of this plan's code.

**Freeze.** `python -I 50_CODE/tpp/tpp_freeze_v02.py --plan 90_DECISIONS/D17_TPP_ARM_PREREG_v04.md --production --test "<canmot310 python> -I -B tests/test_tpp_analyse_v04.py <out.json>"`

`tpp_freeze_v02` refuses the freeze if:
- the plan is under 90_DECISIONS and the log is not the canonical `40_PROTOCOL/D17_PLAN_HASH_LOG.txt` (there is no override);
- an open slot marker is present (`c1_guard_v02`'s pattern);
- the text carries an unfrozen-version banner word (`tpp_analyse_v04.unfrozen_banner`; a file name such as the manuscript draft's is not a banner);
- the hash block is non-empty or not unique, or a sidecar exists;
- results already exist in `60_RESULTS/tpp_v01`;
- any bound file is missing;
- a run fails `check_runs`, or is not in its SHA256SUMS file;
- a test does not print ALL_PASS.

It then writes the block, the sidecar and a line in the canonical log.

**Analysis after the freeze.**

`python -I 50_CODE/tpp/tpp_analyse_v04.py --plan 90_DECISIONS/D17_TPP_ARM_PREREG_v04.md --tracker t1 <keys_t1> <trk_t1> <gt_t1> <seed20261104_t1> <seed20261105_t1> 30_DATA/k6/cache_v02_t1_val --tracker t3 … --out 60_RESULTS/tpp_v01/tpp_analysis_v04.json`

On real data the analysis:
- checks the plan with `c1_guard_v02.frozen_plan(..., which="D17")` against the canonical log;
- refuses a plan that carries an unfrozen-version banner word;
- verifies every bound code, configuration and input hash under its own path;
- checks the runs (`check_runs`).

`check_runs` requires:
- the role, seed, model and keys hash in each run's meta;
- three distinct tracker-history files;
- three distinct **prediction digests** over the 2-s rows and the mixtures (n4);
- a positive share of 2-s rows whose V2 covariance differs from the primary's.

It also asserts that the tracker arm's sd equals K8's own item sd (`k8_items_v02.scene_items`) on every analysed item, to 1e-9 (n6). B comes from the configuration (`--boot` is refused), and an output is never overwritten.

**Hashes at the time of writing** (the freeze re-hashes everything):
- `tpp_analyse_v04.py` `7b6d1e711b5a43502f0f415a89ff3735fe4521a308013b0062fd87d40d6016fc`
- `tpp_freeze_v02.py` `2433aef71eb0e5e42d92cc9558fdaea50c042b32f154dc30969e6bc5d450ccb4`
- `tests/test_tpp_analyse_v04.py` `5f6caf1958fd24e3fe83f1b9ed568e8220c4d0825137ef16de622a16a2032f3c`
- `tpp_analysis_config_v01.json` `da946b3f1cc1f2c737fe0ecadd450ff369e5acbf1e08edd3237907a333b5f179`
- `c1_guard_v02.py (C1 author, at test time)` `00d9bc42713ee3e58ce148d7961c5c1b73e8316628fb26166a1377281384c724`
- `tpp_analyse_v01.py (live)` `5c044afb346d17ea5f38d5399c1f19732aa005d877203e84e54b8f4ab810cc92`
- `tpp_analyse_v02.py (live)` `f8c2912476005d59dcb5b674e1703da1234e1e0188ffef22322cbb7abb587154`
- `tpp_analyse_v03.py (live, superseded)` `637eae74161fb6dc31125663935593ad8bd968ee13a1fbf15ff49439777d2c0c`
- `tpp_freeze_v01.py (live, superseded)` `e302a83d3fb0d2664781628774ca2cebabfe31fb148ac85c81c3274b21c1677a`

**Synthetic tests.** `tests/test_tpp_analyse_v04.py`, E1–E11, ALL_PASS (`70_TESTS/tpp_v01/test_tpp_analyse_v04_synthetic.json`):

| Test | What it checks |
|---|---|
| E1 | Exact CRC equals the float decisions where there is no tie. Ties are labelled: 1215 decisions, 53 exact ties = 6 trivial (n = 19, no exceedance, bound 1/20) + 47 non-trivial |
| E2 | Fail safe: NaN, a missing GT run, a duplicate or mislabelled seed run, a run from other keys, and a relabelled copy of the primary (identical predictions) are all refused |
| E3 | A flagged power-qualified family cell fails H2; the H2 wording |
| E4 | An empty population and a non-evaluable pooled cell are NO |
| E5 | The coded decision, including "primary plus one S1 seed" |
| E6 | S1 refits M\* on the seed run, and detects a seed-dependent H1 |
| E7 | The H4 breakdowns cover PD7 |
| E8 | Binding in a sandbox, through `c1_guard_v02`'s rehearsal log: the freeze with its roles block, guard acceptance with `verify_runtime`, every bound hash verified; a loaded but unbound module is refused, and extra modules are refused for a real plan; and refusal of a bannered plan, a tampered input, a log without the plan, an edited plan, a run missing from SHA256SUMS and `--boot` in real mode. A plan under 90_DECISIONS is frozen only into the canonical log, and a log override for non-nuScenes units is refused |
| E9 | End to end, two trackers, B = 2000, one coded decision, no overwrite |
| E10 | The tracker arm's sd equals K8's item sd; a 10⁻⁶ difference or a missing item is refused |
| E11 | The superseded entry points refuse real inputs and name `tpp_analyse_v04` / `tpp_freeze_v02` |

The earlier suites (`test_tpp_keys_v01` and `test_tpp_run_v01` on full val; the v01–v03 analysis tests) are ALL_PASS.

## 9. Deviations, limitations and open items

1. **Model.** `int_ee` is primary because the map expansion is absent. `int_ee_me` waits for the researcher's file.
2. **Development-side role** (§1). The confirmatory predictor test is H9 on AV2.
3. **Reference ego pose. Settled** by `D16_DELEGATED_CHOICES_v14.md` (correction to Choice 32 M5) and `ERRATA_K8_v03.md` E16, and confirmed by R18b. Trajectron++ is scored on exactly the constraints of the K8 items, taken from those items and not recomputed. They are evaluated at K8's reference ego pose, the logged pose at t_k + h (decision mode), so the pairing with the tracker arm is exact item for item. Manuscript §III's CTRV ego applies to the method-stage audit, not to K8's planner-matched items. That difference is a stated, accepted deviation.
4. **Online semantics.** Streaming per scene. The history LSTM carries state for the whole track life, while training used 8 steps.
5. **Causal velocity.** Training data used central differences over the full track. At track birth the velocity is 0.
6. **Ego pose source.** The keyframe ego pose of the cache, not the CAM_FRONT sample pose of `process_data.py`. Parked vehicles cannot be identified and are fed.
7. **Stated limitations, not run** (Choice 30). Σ_track and the EKF-smoothed GT input.
8. **Folds split logs** (§5).
9. **Worker-count equivalence** (R18 m9). The primary runs used 2 workers and the S1 seed runs 6. Bit-identity was tested for 1 against 2 workers only; the seed is per (scene, keyframe, node). A stated limitation.
10. **The hash log trusts its lines** (R18b n1). Writing the log only through `tpp_freeze_v02` is a procedural rule. A copy of the freeze line held outside the agents' reach is for the lead.
11. **Join against the K8 exploratory items file.** By construction: the same function on the same caches, verified afresh in K1. The sd check (n6) re-derives K8's items at analysis time.
12. **Removed from this plan:** log-grouped folds, the trailer and CTRV-sign sensitivities, V3, and the A6 breakdowns by stratum.

FROZEN_HASHES_BEGIN
# D17 frozen files (tpp_freeze_v02, 2026-11-04 16:31:13 UTC): code, configuration, inputs
7b6d1e711b5a43502f0f415a89ff3735fe4521a308013b0062fd87d40d6016fc  50_CODE/tpp/tpp_analyse_v04.py
f8c2912476005d59dcb5b674e1703da1234e1e0188ffef22322cbb7abb587154  50_CODE/tpp/tpp_analyse_v02.py
5c044afb346d17ea5f38d5399c1f19732aa005d877203e84e54b8f4ab810cc92  50_CODE/tpp/tpp_analyse_v01.py
32942ff8c1c08a6c633648587102fbf2389f5b510dcc05c7d5817ae572033c7f  50_CODE/tpp/tpp_common_v01.py
6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5  50_CODE/m/m_lib_v04.py
f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd  50_CODE/x1/x1_lib_v03.py
9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61  50_CODE/k6/k6_analyse_v02.py
257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4  50_CODE/k6/k6_sim_v02.py
4919ed20818b46cee13c3511444cc62ba44086b329fa2b98ffc0f17508a31494  50_CODE/c1_av2/c1_crc_exact_v01.py
00d9bc42713ee3e58ce148d7961c5c1b73e8316628fb26166a1377281384c724  50_CODE/c1_av2/c1_guard_v02.py
bc48d28801af1036b0118d2e1580ffa03ee8ac7f5f23133822e416a8fc0de437  50_CODE/k8/k8_items_v02.py
da946b3f1cc1f2c737fe0ecadd450ff369e5acbf1e08edd3237907a333b5f179  50_CODE/tpp/tpp_analysis_config_v01.json
6a2a3df9f053ea06ae3c2cb8b543c81a8c5ae50d7c202e8be4e3c1510b34352a  30_DATA/tpp_v01/keys_t1_val_v01.npz
74c658dc1dfa18e7d5787121c4bfdb3b629ebe286051ae900bdd2d28dc5247e6  30_DATA/tpp_v01/tpp_int_ee_t1_trk_val_v01.npz
cf85f3f23b9d85f3121239bfdbd6ea7869a25ab0e374b12a5e85dcaca0a847fd  30_DATA/tpp_v01/tpp_int_ee_t1_gt_val_v01.npz
7d1579bc625ae9fffbe134ae4c912d3f7acc73a507104d8fce6cade15fb7f08e  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t1_trk_val_seed20261104_v01.npz
f75ac97bc97e598c73587295162b7cfbe275b96791b2ae3de1d7579f671ad3e8  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t1_trk_val_seed20261105_v01.npz
3fce4b25729a666b7b5e645369dc434fc44b97233b57c0c19df5b23e24259cc7  30_DATA/k6/cache_v02_t1_val/MANIFEST.json
44def45b11e559fec9286f5cd247685d6627fc458349ce1288ffc15f1f88dc24  30_DATA/tpp_v01/SHA256SUMS_v01.txt
481345dd5550aae5311fa95a2f1b6e5231d71b66f8e43fa205e90b1c2ec7b0f5  30_DATA/tpp_v01/seed_sensitivity/SHA256SUMS_seed_v01.txt
05f4d6ff3ca2dd211884912d44dcdc7a1d4f42941cd649ae922f6d9aec4284c1  30_DATA/tpp_v01/keys_t3_val_v01.npz
8ff54efb2fa5c68181a0b7821c3c8c8546e8a5369162d056e3f686bb51079601  30_DATA/tpp_v01/tpp_int_ee_t3_trk_val_v01.npz
dfe2f24cfe40181f405060c88a6f1f39aee22ae91a9217fe4653960eaa5c36c9  30_DATA/tpp_v01/tpp_int_ee_t3_gt_val_v01.npz
1ca10345762d8dbe98b9e3c10152f4ac105e7e727da44830d5213cb706095b42  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t3_trk_val_seed20261104_v01.npz
7f53b7ee00350ca0165bfdf249411bc8e5e6305629edfdc20d2409af9fd2701b  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t3_trk_val_seed20261105_v01.npz
f0be2a92bea3edd35bd9af82624e9aea1c2f996930f90a8165e3e8d298db2a8b  30_DATA/k6/cache_v02_t3_val/MANIFEST.json
FROZEN_HASHES_END

FROZEN_ROLES_BEGIN
# roles (c1_guard_v02): entry point, modules, configuration, inputs
entry:tpp_analyse  50_CODE/tpp/tpp_analyse_v04.py
module  50_CODE/tpp/tpp_analyse_v02.py
module  50_CODE/tpp/tpp_analyse_v01.py
module  50_CODE/tpp/tpp_common_v01.py
module  50_CODE/m/m_lib_v04.py
module  50_CODE/x1/x1_lib_v03.py
module  50_CODE/k6/k6_analyse_v02.py
module  50_CODE/k6/k6_sim_v02.py
module  50_CODE/c1_av2/c1_crc_exact_v01.py
module  50_CODE/c1_av2/c1_guard_v02.py
module  50_CODE/k8/k8_items_v02.py
config  50_CODE/tpp/tpp_analysis_config_v01.json
data:t1:keys  30_DATA/tpp_v01/keys_t1_val_v01.npz
data:t1:trk  30_DATA/tpp_v01/tpp_int_ee_t1_trk_val_v01.npz
data:t1:gt  30_DATA/tpp_v01/tpp_int_ee_t1_gt_val_v01.npz
data:t1:s1a  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t1_trk_val_seed20261104_v01.npz
data:t1:s1b  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t1_trk_val_seed20261105_v01.npz
data:t1:manifest  30_DATA/k6/cache_v02_t1_val/MANIFEST.json
data:t1:sums  30_DATA/tpp_v01/SHA256SUMS_v01.txt
data:t1:seed_sums  30_DATA/tpp_v01/seed_sensitivity/SHA256SUMS_seed_v01.txt
data:t3:keys  30_DATA/tpp_v01/keys_t3_val_v01.npz
data:t3:trk  30_DATA/tpp_v01/tpp_int_ee_t3_trk_val_v01.npz
data:t3:gt  30_DATA/tpp_v01/tpp_int_ee_t3_gt_val_v01.npz
data:t3:s1a  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t3_trk_val_seed20261104_v01.npz
data:t3:s1b  30_DATA/tpp_v01/seed_sensitivity/tpp_int_ee_t3_trk_val_seed20261105_v01.npz
data:t3:manifest  30_DATA/k6/cache_v02_t3_val/MANIFEST.json
data:t3:sums  30_DATA/tpp_v01/SHA256SUMS_v01.txt
data:t3:seed_sums  30_DATA/tpp_v01/seed_sensitivity/SHA256SUMS_seed_v01.txt
FROZEN_ROLES_END
