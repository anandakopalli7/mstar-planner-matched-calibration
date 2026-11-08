# C1 pre-registration v07e (DRAFT): the external confirmation on Argoverse 2 (5 Nov 2026)

**Status.** Draft v07e, the text-lock draft: R20 re-checks it before the researcher uploads it. Not frozen. v01 to v06 and v07a to v07d are kept unchanged. v07e = v07d (8217b6b9…) plus D16 v31 (`90_DECISIONS/D16_DELEGATED_CHOICES_v31.md`, 52ff35fa…): Choice 48 (R17f), Choice 49 (R20's re-check of v07d, `70_TESTS/R20_C1_PLAN_RECHECK_v01.md`, 8f0299de…) and Choice 50 (the criteria audit's rule set R\*, with its corrections in 50(k) and 50(l)). The basis, class and confidence of every pass/fail criterion are in `90_DECISIONS/C1_CRITERIA_REGISTER_v03.md` (8d2be6c5…). Places that depend on code v09 are marked `[[V09: …]]`; every one is replaced before the text lock. The change table is section 11.1 (v07e: rows 89 to 120); the claim and its scope are section 11.3; the sources are section 6.8; the limits in the paper's voice are section 6.9. The numbers that need the confirmation data are left as marked slots: the freeze refuses this file while any slot is open (its slot test is the regex `\[\s*SLOT|SLOT\s*:`, case-insensitive, defined in `c1_guard_v03`). The frozen file will be a copy without "DRAFT" in its name, `40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_vNN.md` (Choice 38e).

## Open slots (every one blocks the freeze)

| # | Slot | Filled from | When | Where used |
|---|---|---|---|---|
| S20a | Stage-A counts of the 375 logs, own detector, T1 and T3: K8 decision and item counts (PD7, SD1_7, PD per cell and log; PD's per-cell items are H9's population before history length is known), method-stage in-path counts; AB3DMOT's counts (descriptive) | `k8_items_v04 --av2 --counts-only` (the K8 counts) and `av2_counts_v02` (the method-stage counts), both bound builders, on the 375-log stage-A caches built by `av2_cache_stageA_v02`; outcome-free (Choice 13); output bound as `data:s20a` | after stage A | sections 1.6, 7 |
| S21 | E⁰ for the two H8 cells (`H8_E0_primary`) and the hashes of its inputs (`inputs_sha256`, copied into the analysis config as `e0.inputs_sha256`) | `c1_e0_v05 --mode c1 --seed 20261114 --stageA-manifests …` on the stage-A fields of the 375 logs, T1, with the one prepared ground-truth file | after stage A, **before the quarantine** and the freeze | section 6.3 (H8) |
| S22 | Power and operating characteristics on the real counts, under R\*: the floors, P(H1), P(B6 passes on T3), H9's E2 floor on its PD population, and M\*Jx's λ and price at 75-log folds. **Reported only:** it changes no label, rule, threshold or population (Choices 47i, 49g) | `c1_power_counts_v05` (README v09; R\*'s levels and Choice 47(e)'s and 49(c)'s stricter comparator rules; H9's PD population, not the method-stage audit population; its hash is recorded before it runs) on the S20a counts, with development inputs from the K8 Linux replicate's v03 analysis (R16); output bound as `data:s22`. Its H9 figure leaves out history length, so it overstates H9's power | after S20a | section 7 |

The slot markers in the text are:
- `[SLOT: S20a stage-A counts of the 375 logs, T1 and T3, own detector]`
- `[SLOT: S21 H8_E0_primary for car|<20|lat and car|20-40|lat, and e0 inputs_sha256]`
- `[SLOT: S22 power on the real counts]`

**Filled:** S20b in v07c (the detector AP and the final iteration count, section 1.2); S20c in v07d (H9's label is fixed as secondary, Choice 47c; sections 2 and 6.4). Three slots remain open: S20a, S21 and S22.

**The text lock** (Choices 47i, 49a; R20 P7). Before the first 375-log stage-A build, the SHA-256 of this draft as approved after R20's re-check (slots open, every `[[V09: …]]` mark replaced) is recorded in D16, and the researcher uploads it as a plain file to the private OSF project (https://osf.io/eumj8/); the lead does not upload. Its upload time becomes tamper-evident when the embargoed registration archives the project's files at the freeze (Choice 49h). README v09 is final and R17g-checked before the lock, and its name, SHA-256 and role counts are written here before it.
- **What may change after the lock, exhaustively:** the fills of the three slots (S20a in section 1.6, S21 in section 6.3, S22 in section 7, and their three lines in the slot list above) and the provenance line (section 8.1). Nothing else.
- **Any other change** to this text, or to any bound code file, needs a D16 choice that names every changed line or file and states that it was made after the confirmation-set counts were seen, and the paper discloses it.
- [[LEAD: Choice 49(b) and 49(e) ask section 10 to record at the freeze the time and readers of the Rule-0 metrics and the result of the off-workspace hash scan. Choice 49(a) does not list these among the post-lock changes. Section 10 therefore points to a freeze-time record for them; please confirm where that record lives, or add these two records to the allowed list.]]

**Process items before the freeze (not plan text):**
- **Done:** code v08 (README v08, 5649c170…, 154 files), verified by the lead (`C1_CODE_V08_VERIFIED.txt`); the own detector (S20b); R20 and its re-check of v07d (Choices 47, 49); R17f (Choice 48); the criteria audit (Choice 50; register v03).
- **Running:** code v09 (Choices 47 a, b, e, f, i, m13; 48 a, b; 49 b, c, g; 50's constants as named constants with source comments and pinning tests); the port's tracker runs.
- **Next:** the lead's verification of code v09, then R17g (README v09's delta, the provenance refusal test, R17f's N1 and N2, m-2 and m-6, the infos archive's member names and the GT-inventory boundary); then R20's re-check of this draft; then the text lock.
- **Then the data steps** of section 8.5, in that order. The freeze and the registration must both happen before 19 Feb 2027 (Choice 41f).
- **After the freeze and before stage B:** the researcher's embargoed OSF registration and the lead's deposit record (section 8.3).
- **Descriptive, after the lock-critical work:** the planner sensitivities of Choice 50(g), on nuScenes development (section 5).

---

## 0. What C1 is, and what kind of evidence

**Role.** One frozen plan for the method stage and the closed loop on external data (D13 Phase 4); the external run is "the same study" as K8 (D14 section 1).

**Development evidence.** K6 was a pre-registered NO-GO (power floor on T3). K7 was never frozen. K8 on the 840 nuScenes scenes is exploratory; its numbers below are from the Linux replicate and its v03 analysis, confirmed by the independent review R16 (`70_TESTS/R16_K8_RESULTS_REVIEW_v01.md`; errata E8 to E16). Decision mode: infeasible-decision rate T1 M\* 0.114, B4 0.198, B6 0.176; T3 M\* 0.161, B4 0.208, B6 0.167. Comparators not shown above δ: B3 on T1; B0 and B3 on T3. B4 and B6 are shown above δ on both trackers. Forms A, B and C are met on both trackers. On T3, Form B turns on B6: M\* − B6 = −0.005 [−0.017, +0.005] (E12). **Under R\*** (Choice 50h; final check v02, part C), the development verdict is unchanged on both trackers: Valid(M\*) holds; V_t is {B3} on T1 and {B0, B3} on T3; Forms A, B and C are met; H10 and H3 hold. Form B's bounds are −0.725 (T1, B3), −0.571 (T3, B0) and −0.680 (T3, B3); Form C's −0.066 (T1) and −0.033 (T3); H10's NI −0.043 (T1) and +0.005 (T3).

**What "valid" means (E10).** "Not shown above δ" by a one-sided simultaneous test at 0.95, never "at most δ". M\*'s point estimate exceeds δ in 9 of 32 PD7 cells on T1 and 11 on T3 on development data, none near a flag.

**What the primary test adds (Choice 6; R20 P2, Choice 47f).** Within-AV2 cross-fitting gives M\*'s own-threshold strata the marginal CRC bound (P02 PM1). The tested cells pool strata over range and include fallback strata, for which the bound is only approximate or absent (P02 v03, pooled cells), and the test holds the fitted thresholds fixed, so it tests the risk of the fitted rule. The test adds: no group × axis × motion cell shown above δ, with power 0.8 against a true 0.15; the pooled upper bound within δ + 0.03; the operability price on new data; the ranking against every comparator not shown above δ; and the premise's replication (H8).
- **What is reported beside it** (descriptive, never gated; `c1_analyse_v09`). For M\*, per tracker and population: the simultaneous one-sided 95 % upper bound of every evaluable cell, and their maximum, read as "M\*'s exceedance is at most U in every evaluable cell, simultaneously at 95 %". These bounds are **approximate**: their development coverage near δ is 0.78 at 39 units and 0.87 at 150 (Choice 50f).
- **No equivalence claim is added**, and family S keeps m = 5. Following Schuirmann's critique of reading a non-rejection as evidence, the paper reports U_max and HK1c's bound instead (section 6.8).
- **The paper's sentence:** "not shown above δ in any cell, with power 0.8 against a true 0.15".

**What a design choice may use (D16 Rule 0).** The literature; nuScenes development results; AV2 detector AP, tracker metrics and counts. No AV2 outcome. Section 10 lists what of this was seen on the confirmation logs. Every pass/fail criterion has its basis, class (PROVEN, STANDARD, PRACTICE, DEV or OWN) and confidence in register v03.

**One-shot commitment.** The 375-log AV2 set is used once for the claim family "validity and operability of DP-SCRC in the planner". A NO-GO leads to diagnosis and new work on new data, never to a re-run (section 9). Every run of a guarded C1 entry point on AV2 is recorded in the chained, append-only run log, which is uploaded with the results (section 8.6). Re-running the frozen analysis on the frozen inputs reproduces every table; this shows that the reported tables are the frozen analysis's, not that no other analysis was run (section 11.3).

**Outcome-blind attestation for this draft.** No code was run on AV2 data for v05 to v07e, and no AV2 file was opened. For v07e the author read decision, review, register and results-note text only: D16 v27, v28 and v31, R20's re-check of v07d, the criteria register v03, the final check note v02 (part D values, and one value of `C_verdict_rstar_v02.json`, nuScenes development), and the v07d sources. This file's frozen-block layout was checked on a text copy (section 11.1, row 120). The AV2 facts used are those already in v01 to v04, the own detector's note, and file-level facts (paths, sizes, dates and hashes) from R17e, R17f, R20 and the lead.

**Stand-ins are not evidence.** Every rehearsal of the confirmatory path (`70_TESTS/c1_v01/rehearsal150_v05b/` to `rehearsal150_v08/`, and the final rehearsal on README v09) uses nuScenes validation scenes as "AV2" units and T1's data as AB3DMOT's. The AV2 paths (quarantine, run log, deposit, stage B, scene map, provenance) are tested in a copy tree on R17d's AV2-tagged stand-in. Their verdicts exercise the code only; none is quoted as a result.

---

## 1. Data and sets

### 1.1 The confirmation set (D18 v02 and v03, option A)

- **Split.** The 700 AV2 Sensor train log ids, sorted, permuted with NumPy `default_rng(20261102)`; the first 225 are held out, the other 475 train the detector. Split file `50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json` (3771664f…), city composition in `AV2_TRAIN_SPLIT_v01_CITIES.json`; bound at the freeze as role `split`.
- **Detector.** Our own CenterPoint from LT3D's code (commit e33189aa…) with the public checkpoint's configuration (`centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2`), trained from scratch on the 475 logs at every 5th sweep, batch 4, learning rate 5e-5, CBGS sampler, cyclic schedule over the iterations that fit the cap (`50_CODE/owndet/OWN_DETECTOR_DESIGN_ADDENDUM_A_v01.md`, `_B_v01.md`: 2 CBGS epochs if the projected total stays within $34, otherwise the largest count of at least 50,500 iterations). **No checkpoint or setting is selected on any of the 375 confirmation logs.** As run: section 1.2.
- **Confirmation set.** The own detector on the 225 held-out train logs plus the 150 validation logs, every 5th sweep: **375 logs, all unseen by the detector**. T1 (CANMOT `paper/local/canmot/sc`) and T3 (Poly-MOT `paper/baseline/poly_mot`) run on its detections with their nuScenes parameters, re-tuned on nothing. **AB3DMOT** (LT3D's, tracker label `tab`) runs on the same 2 Hz detections with LT3D's defaults, as a descriptive third tracker (Choice 38c; section 2).
- **The log list.** `av2_c1_logs_v01` writes `30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` (the 225 held-out and the 150 validation ids, checked disjoint, 375 in all) and its `.sha256`; it is bound as `data:logs375`.
- **The AV2 port** (Choices 46a, 47a; README v09). The v01 AV2 builders read only `30_DATA/av2_val`, so they cannot read the 225 held-out train logs, and the laptop has too little disk for their lidar. README v09 binds as builders every tool that writes a stage-A input, the log list or the GT inventory (environments as in section 8.5):
  - `av2_common_v02` (a log-root resolver over `av2_val` and `av2_train225`; a sweep list from the recorded bucket listing when there is no local lidar) and `av2_fetch_v05` (no lidar contents);
  - `av2_c1_logs_v01` (the log list) and `av2_c1_frame_check_v01` (the frame-time check);
  - `av2_gt_prep_v02`, `av2_ego_prep_v02` and `av2_tracker_input_v02`;
  - `av2_track_v02` (T1, T3), `av2_ab3dmot_v05` (AB3DMOT) and `av2_horizon_prep_v02` (the 2 s propagation);
  - the new tools: `c1_av2_provenance_v01`, `c1_power_counts_v05` and the GT-inventory builder [[V09: final names, in particular the GT-inventory builder's (planned `c1_av2_gt_inventory_v01`)]].

  The Rule-0 tools `av2_track_metrics_v04` and `av2_hota_v04` are unbound, outcome-free metric tools. Stage A stays `av2_cache_stageA_v02`, which reads paths only and does not import `av2_common` (Choice 46e).
- **The port's acceptance rule** (Choice 46a, fixed before any 375-log output). On the 150 validation logs with the public LT3D detections, each new builder reproduces its v01 output byte for byte (port design v04 section 10). The listing-derived frame times of the 225 logs equal the own detector's frames (`av2_c1_frame_check_v01`). The equivalence records (`60_RESULTS/av2_trk/c1_375/equiv/`) are bound as `data:port_equiv`.
- **Disclosed** (Choice 49i; R20 N10). `av2_track_v02` and `av2_ab3dmot_v05` were corrected in place on 5 Nov at 07:07 EST, after their first resume test reused no checkpoint (records kept in `equiv/superseded_checkpoint_hash_bug/`), before any 375-log output and before Choice 46's acceptance rule; they were then re-tested and passed. The unbound metric tool `av2_hota_v04` agrees with v03 to a relative 1e-12, not bit for bit (v03 itself is not bit-reproducible; register C16c). From now on port tools are versioned, never corrected in place.
- **A port failure** (Choice 47i; R20 P7). If a port builder fails its acceptance test, it is replaced only by a new versioned builder that passes the same test on the 150 validation logs; no 375-log output of the failed builder is read. If the 225 held-out logs cannot be built, the researcher decides, and this plan is redone; there is no silent fallback to 150 logs.
- **One prepared ground-truth file** (Choices 44f m5, 46b). `av2_gt_prep_v02 --logs-file 30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` writes one prepared ground-truth file covering exactly the 375 fold units, `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json`, **before** stage A. Every 375-log stage-A manifest names it with its hash, and E⁰, the quarantine, stage B, the method stage and H8 use it.
- **Training data are not confirmation data.** The 475 training logs' annotations train the detector only.

### 1.2 Detector AP (reported, never gated; S20b, filled in v07c)

From `60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md` (4f014ae1…): the official av2 0.2.1 evaluator, 50 m, ROI-filtered, all 26 competition categories, ground truth restricted to the evaluated frames, every 5th sweep. The public checkpoint's row is from `AV2_DETECTOR_NOTE_v01.md`.

| AP at 50 m | Vehicle | Pedestrian | Bicyclist | 26-class average |
|---|---|---|---|---|
| Own detector, 150 validation logs (4,806 frames) | 0.857 | 0.777 | 0.403 | 0.425 |
| Own detector, 225 held-out logs (7,232 frames) | 0.854 | 0.800 | 0.495 | 0.415 |
| Public checkpoint, 150 validation logs | 0.875 | 0.795 | 0.543 | 0.469 |

"Vehicle" is the regular-vehicle class.

- **Training as run.** The final iteration count is **57,838**: 2 CBGS epochs ran, because the speed check projected $31.44, within the $34 cap (addendum B). The run was two segments on two hosts, joined by an exact resume at iteration 1,000 (optimiser, learning rate and schedule restored from the checkpoint); the data order after the resume is not the order an unbroken run would have drawn. The final checkpoint is `iter_57838.pth` (68369a71…). Every frame has predictions (4,806 of 4,806 validation frames, 7,232 of 7,232 held-out frames), with no non-finite values.
- **The bicyclist gap.** On the 150 validation logs the own detector's bicyclist AP is 0.403, against the public checkpoint's 0.543, a gap of 0.140; its 26-class average is 0.425 against 0.469. Vehicle and pedestrian are within 0.02. The own detector had a much shorter schedule (2 epochs against 20) on about two thirds of the data (475 logs against 700). The validation ground truth is byte-identical for the two detectors, so both validation rows use the same frames and labels. Other disclosures from the note: the sparse-convolution kernels printed a GPU-architecture warning on every call, without any error; training used every 5th sweep, against probably every 10th for the public checkpoint.
- **Nothing was selected on the confirmation logs** (R20 m9). D18 v02 (2 Nov 2026, 10:25 EST) fixed the assignment, the own detector on the 225 held-out and the 150 validation logs, before any AP of the own detector existed. There was no evaluation during training; AP was computed on the final checkpoint only, after training ended; the progress copy `iter_51000.pth` was never evaluated; and no checkpoint, setting or threshold was chosen on any of the 375 logs. The sentence in `AV2_DETECTOR_NOTE_v02.md` that the choice of detector "is the lead's" was written after AP and decided nothing. AP is reported, never gated: the study tests calibration given a deployed detector (D18 v03), so a weaker two-wheeler detector is a condition of the test, not a reason to change it. Its effect on the two-wheeler cells can show only through the S20a counts and the floors, which are fixed by rule.
- **Seen before the lock** (Choice 49e). The detector AP was computed and seen before the text lock; it is disclosed here and changed no rule. Its detection-evaluation ground-truth feathers are in the GT inventory (section 8.4).

### 1.3 Descriptive data on the 150 validation logs

- **H1-P** (route `public_lt3d_val`): the public LT3D checkpoint (299cf3b7…) on the 150 validation logs, folds role `folds_val150`. Descriptive: its SD1_7 floor fails at 150 logs (power-qualified family 4, counts v02).
- **H5** (route `voxelnext_val`): the public VoxelNeXt checkpoint (8641d838…) on the same logs, folds role `folds_val150`. Descriptive: its checkpoint saw all 700 train logs, so it can only run on validation, where the floor fails.
- **Whether H1-P and H5 can run** is decided by the final rehearsal on README v09, before the text lock, and stated in section 10 (R20 open choice 13; Choice 47m). If the frozen code cannot run them, they are "not tested" (Choice 38d); they are descriptive in any case.
- **Q1 (QCNet) is "not tested" in C1** (Choice 44d, the fallback of Choice 41c; decided before any outcome, and replacing Choice 43(a)'s route). The reasons (R17e section 4):
  - **No C1 tracker index shares QCNet's history source.** QCNet's deployed histories come from a 10 Hz matched AB3DMOT run with T1's SF thresholds (`30_DATA/qcnet_av2_v03/`); C1's AB3DMOT is the 2 Hz run of Choice 11, and T1 and T3 are other trackers.
  - **The frozen coverage condition cannot hold.** In R17e's definition (the share of T1's, or T3's, LT3D 2 Hz audit records that QCNet predicted; QCNet note v03 section 3), QCNet predicted 95.7 % of T1's records (88,182 of 92,166) and 88,170 of T3's 92,124, so the route's `not_predicted == 0` fails under either tracker. QCNet note v01 section 6's 97.4 % (89,778 "in both") uses another definition (R20 m15).
  - **What follows.** The frozen config has no `q1` entry (Choice 43d as amended by 44d). No QCNet outcome is computed for the C1 report; if one is ever computed, it is exploratory and labelled so. Q1 never changed GO, H9 or family S. The QCNet notes v01 to v03 stay as records.
  - **In the code** (Choices 45c, 48b m-5). `c1_analyse_v09` refuses a config with a `q1` entry, prints Q1 as "not tested" with these two reasons in its own block, and never lists Q1 among the missing inputs; `c1_predarm_v06` refuses `--q1-only` and every QCNet option. `entry:c1_qcnet_summary` is no longer a role, and `c1_qcnet_summary_v01` is unbound. `c1_predarm_v05` is bound only as a module, and is refused as an entry point by role (R20 m1).

### 1.4 Classes, groups, items, populations

- **Four groups** (Choice 8): car := `REGULAR_VEHICLE`; pedestrian := `PEDESTRIAN`; two-wheeler := `BICYCLIST` (ridden-two-wheeler rule RB-1) and `MOTORCYCLIST`; large := bus, truck and trailer categories (port design section 4.2).
- **K8 items** (H1 to H4, H9, H10): enforced (track, check time) pairs at decision states, considered tracks within 60 m and not behind, every separating axis at the reference pose (the logged pose at t_k + h, the decision mode's leash), split by the in-path flag (`k8_items_v08 --av2-stageB`).
- **Method-stage items** (H6a, H6b, H7, H8 only): M-PLAN section 3 (in-path, persistently paired, uncensored at k + h, separating axis, toward the ego), h = 2 s. H9 does **not** use them (section 6.4).
- **Strata**: group × range (from the sensor's CTRV-predicted ego) × axis × motion state; L1 to L3; n_min = 19 units (Angelopoulos et al. 2024, Thm 1: a finite threshold needs 1/(n + 1) ≤ δ; register C4).
- **Populations** (D14 section 4): PD7, SD1_7 (gap ≤ 5 m), PD (in-path), NIP (reported).
- **Cells**: group × axis × motion pooled over range (32) plus the pooled cell; **evaluable** at ≥ 39 logs (on AV2 a log is a scene; basis in section 6.1).
- **Scene-to-log map** (Choices 41d, 44f m4). The bound builder `c1_av2_scene_map_v01` writes `[{"name": u, "log_token": log}]` for every unit of the given stage-A manifests, `log` being the manifest's own log. On AV2, `av2_cache_stageA_v02` records log = scenario id, so the map is the identity, `[{"name": u, "log_token": u}]`. The builder refuses an existing output, a nuScenes manifest and two logs for one unit. The map is bound at the freeze as `data:scene_json` (an AV2 freeze requires it), and the freeze checks that it gives every fold unit its stage-A log. For every unit, `c1_mstage_v06` and `c1_h8_v06` check that its log in the map equals the stage-A manifests' `scenes[u]["log"]`, so the check confirms the unit set and names.

### 1.5 The outcome-blind boundary, and its scope (Choices 13, 34, 42, 44, 47d, 48, 49)

- **Allowed before the freeze:** the tracker's propagation of its mean and covariance; the ego's logged poses; the toward-ego normal; predicted-range strata; planner decision construction; K8 decision-mode item counts; existence of the ground-truth `track_uuid` at the target sweep; E⁰ from stage-A fields (Choice 31); the detector AP (seen before the text lock) and the tracker metrics (HOTA, AMOTA, MOTA, IDS; computed after the text lock), which use ground truth at the same sweep (Rule 0). The last three are computed before the quarantine.
- **Forbidden until the freeze and the external registration:** any ground-truth position, velocity or box at a sweep later than k; any residual, projected error, U, exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or coverage.
- **Two stages.** Stage-A caches (`av2_cache_stageA_v02`) carry no annotation position, box, size or yaw at any frame (tracker note v02, "Not computed"; identity and existence only); they serve the counts, E⁰ and the freeze, and their manifests record the hash of the one prepared ground-truth file. The C1 steps that read ground truth after k are stage B (`av2_cache_stageB_v06`, entry `stageB`, which joins it to the tracker outputs), the method stage, H8 and the analysis's E⁰ recompute. All of them run only after the freeze **and** the external deposit, and read the ground truth only from a quarantine member, verifying its decompressed SHA-256. Stage B writes only `30_DATA/av2_cache_stageB_<tag>/` and logs each build to `40_PROTOCOL/C1_STAGE_B_LOG.txt` (section 8.6).
- **What the C1 entry points refuse** (`c1_guard_v05` [[V09: or `c1_guard_v06`, if bound]], which imports `c1_guard_v04` and `c1_guard_v03`; the scope of this statement is section 11.3):
  - one hard-coded hash log, `40_PROTOCOL/C1_PLAN_HASH_LOG.txt`, of which only the latest line is accepted, with no command-line override on AV2;
  - **every C1 entry point that reads ground truth after k, or a table built from it, requires the validated deposit record** (Choice 42a): stage B, items, fits, runs, method stage, H8, predictor arm and analysis. Only `entry:c1_e0`, `entry:c1_folds` and `entry:c1_freeze` are exempt. The folds and the freeze read no ground truth; `c1_e0_v05` uses only outcome-free fields (existence and identity) of a file that also holds later positions (R20 m7). Every runtime record and every table carries `deposit_record_sha256`, which must equal the current record;
  - a dataset tag must agree with the unit names;
  - run-time hash checks of the entry point and every loaded project module; the running Python, NumPy and SciPy versions must equal the plan's FROZEN_ENV block; the Trajectron++ keys wrapper's versions must equal FROZEN_ENV and the run wrapper's FROZEN_ENV_TPP (Choice 44e), checked first on a dry record by `c1_tpp_envcheck_v01` before any key or run is made (Choice 45a);
  - on AV2 an existing output is never overwritten, and every guarded run writes a "start" and a "done" line to the chained, append-only run log (section 8.6).
- **Quarantine before the freeze** (Choices 42b, 44a, 47b, 48a, 49b, 49d). Every file of the GT inventory (every workspace file that holds per-object AV2 annotation geometry, by the content rule of section 8.4), and **each AV2 stage-A manifest's ground-truth file**, is moved into a verified gzip quarantine before the freeze. The freeze refuses while any recorded ground-truth hash has a plain copy in the workspace outside the skipped folders, while the quarantine folder holds anything but recorded members and its manifest, or while a recorded stage-A member's manifest is missing from its recorded path (section 8.4).
- **Superseded entry points cannot compute AV2 outcomes** (Choices 36, 39a). Byte-exact originals are archived as gzip members in `superseded_originals/`; in each superseded file only `main()` was edited, to refuse any input whose dataset, read from outcome-free tags and names, is not nuScenes or synthetic. Older entry points are refused for want of a plan hash log before the freeze, and by role after it (section 8.8).
- **Scope** (Choice 47d; R20 P1). These are properties of the C1 entry points. Not technically barred were: the programs of the earlier nuScenes studies; the public AV2 annotation files of all 375 logs, which are on the analysis computer (`30_DATA/av2_val/` and `30_DATA/av2_train225/`); the AV2 data tools, bound and unbound, which can rebuild a prepared ground-truth file from those annotations; and copies outside the workspace. The embargoed OSF registration is made after the freeze and before any C1 step that reads ground truth after k. The claim is stated verbatim in section 11.3, and the words "outcome-blind boundary enforced by code" are not used without that scope.

### 1.6 Counts

`[SLOT: S20a stage-A counts of the 375 logs, T1 and T3, own detector]`

To be reported: decisions, items per population, per cell and per log; evaluable cells; power-qualified families and their record coverage; method-stage in-path cells; H9's PD items per cell; AB3DMOT's counts; per-fold source and city composition. H9's history-length counts need the Trajectron++ keys, which are built from the stage-B cache; they are reported by the frozen predictor arm at analysis (Choice 47c; section 6.4). The counts of the 150 validation logs under the public detectors (counts v01, v02) stay as reported in v02 to v04; they are not the H1 layout.

---

## 2. Claims under test

δ = 0.05 throughout: a calibration level for each relied constraint, not a safety target (register C1). Formulas and levels in sections 6.2 and 6.3. "Secondary" claims are pre-registered; "descriptive" ones are reported in full and never claimed.

| ID | Label | Data | Statement |
|---|---|---|---|
| **H1** | **Primary** | 375 logs, own detector, T1 and T3 | **Form B**: no cell, family cell or pooled cell of M\* is shown above δ on PD7, SD1_7 or PD, the floors and HK1c hold, and M\* is less often infeasible than every comparator not shown above δ (Choices 9, 47e, 50b). Expected to turn on B6 on T3 (E12) |
| H2 | Secondary | as H1 | **Form C**: the decision-mode price, M\* − B4 infeasible rate, is ≤ c_t on T1 and T3, tested at UB^{0.975}; c_T1 = c_T3 = 0.03 (development prices −0.084 and −0.047; E11; register C10a) |
| H3 | Secondary | as H1 | **M\*Jx**, the trajectory-level certificate (Choice 21): its joint loss is not shown above δ on PD7, SD1_7 and PD, and Form B holds on the joint loss, with the stricter comparator rule (Choices 49c, 50b) |
| H4 | Secondary | as H1, transfer fits | **Transfer in the loop**: H1's formula with every fitted arm from the all-850-scene nuScenes fit (Choices 6, 7) |
| H6a | Secondary | 375 logs | **Method stage within AV2 (E1-AV2)**: M\* shown above δ in no E1-AV2 cell, fixed-rule and refit-CV, T1 and T3 |
| H6b | Secondary | 375 logs | **Practitioner failure**: B4 fails (flagged at 0.975, M\* not flagged, paired difference positive at 0.975; refit-CV) in at least one E1-AV2 cell on T1 and on T3 |
| H7 | Secondary | 375 logs | **Method stage, transfer (E2-AV2)**: the M-stage M\* fitted on the 700 nuScenes train scenes is shown above δ in no AV2 cell and not in the pooled cell, T1 and T3 |
| H8 | Secondary (family P) | exactly the units of the `folds` role (the 375 logs), T1 | **Diagnosis replicates**: an in-path car lateral 2 s cell (< 20 m or 20 to 40 m) FAILS under B0, and its truth-oriented exceedance also FAILS |
| H9 | Secondary (fixed now; S20c filled in v07d, Choice 47c) | 375 logs, own-detector T1 and T3 histories, K8 relied in-path items (PD) | **Trajectron++ `int_ee`** (Choices 23, 35, 37, 39b, 42f m1, 43b, 47c): DP-SCRC with history-length strata, cross-fitted on the C1 folds, along the K8 tracker-planner's constraints: (a) at least 6 power-qualified **E2** cells, power computed in the joint evaluable E2 + HL family, judged by the frozen predictor arm on the population actually tested; (b) the three pooled history-length cells each evaluable; (c) no E2 cell flagged in the **E2-only** sup-t families; (d) no history-length cell flagged in the **joint** E2 + HL sup-t families; and (e) the pooled cell (each item once) not flagged. Primary forward-pass seed 20261102 |
| H10 | Secondary | as H1 | **Motion-strata ablation, M\* against B6**: B6 fails (flagged at 0.975, paired difference positive at 0.975) in at least one PD7 cell where M\* is not flagged, and M\*'s infeasible rate is at most 0.03 above B6's at UB^{0.975} |

**What GO establishes** (Choice 47g; R20 P3). GO establishes, per tracker on 375 AV2 logs: M\* is not shown above δ in any evaluable cell, family or pooled cell of PD7, SD1_7 and PD; the floors hold; and M\* is less often infeasible than every comparator not shown above δ. B3's margin is at least M\*'s on every item (P02 PM3), so its infeasible rate cannot fall below M\*'s wherever infeasibility is monotone in the margin. A comparison with B3, and with RETUNED where it equals B0, is reported but is not evidence of operability. On T3 the development data predict that GO requires B6 to be shown above δ (E12; R16 M2). The decision states, for each comparator, why it is in or out of V_t. PD validity is claimed for PD's power-qualified cells only (register C7b). Validity is claimed against per-cell excesses of about 0.15 and above, not smaller ones (sections 6.9, 7).

**Descriptive.** Form A; H1-P and H5 (section 1.3); M\*'s simultaneous one-sided 95 % cell upper bounds and their maximum, labelled approximate (section 0); the criteria audit's outputs of Choice 50(f) (section 7); the source heterogeneity check and the train-to-validation source-transfer reading (Choice 22), which change no claim whatever they show (R20 open choice 18); **AB3DMOT (`tab`)** as a third tracker on the 375 logs with the same items, folds and entry points as T1 and T3, reported in the validity and trade-off tables, outside H1 and outside family S (Choice 38c); **H9's seed robustness** (S1-AV2, Choice 38b): the same H9 analysis with forward-pass seeds 20261104 and 20261105, labelled "seed-robust" only if H9 holds under all three seeds, outside family S, never changing H9's status, family S or GO (Choice 41e); the predictor arm's `S20c_label_from_counts`, beside H9's fixed label (section 6.4); loop mode (section 6.6); V2 and its variants for every arm (section 6.6); RETUNED and RETUNED-HK1 (section 6.6); M\*J (Choice 21); H9-noHL (Choice 37); H9-T, the nuScenes-fitted Trajectron++ transfer (Choices 19, 23); TPPgt, Trajectron++ with ground-truth histories (upper bound); A6 calibration diagnostics; A7 sharpness; the α-sweep and δ′ arms; A13; A14; NIP; margin ratios; HOTA, AMOTA, MOTA and IDS; the AV2 pairing rate by score bin (register C15h); how often v_max binds (C15f); the share of relied constraints at 50 to 60 m (C15d).

**Not tested in C1:** Q1 (QCNet), for the two reasons in section 1.3 (Choice 44d).

**Not run in this plan** (outside the bound path of README v09): the 10 Hz protocol; the Ford Fusion footprint sensitivity; T2 on the 375 logs; any QCNet outcome; D17's sensitivities S2 (seed-pooled V2, Choice 27) and the trace > 100 m² sensitivity (Choice 28) (R20 m11). C1's H9 uses `int_ee`, whatever map data arrive; `int_ee_me` is not used in C1 (Choices 3, 30; R20 m12).

**Not claimed.** A closed-loop guarantee; a safety ranking from loop-mode collisions; validity in non-evaluable cells; validity against per-cell excesses smaller than about 0.15; validity along an object's true axes; an equivalence bound on any cell; anything outside the four groups; anything about the AV2 test split; that no early look at the AV2 annotations was technically possible outside the C1 entry points (section 11.3).

---

## 3. Calibration: what is calibrated where

### 3.1 Folds (Choice 22)

- **375 logs: 5 folds of 75** (role `folds`), from `c1_folds_v03 --dataset av2 --split … --val …` (entry `c1_folds`): the 375 log ids sorted, permuted by NumPy `default_rng(20261112)`, cut into 5 consecutive blocks (`np.array_split`). The tool checks that the ids are exactly the split's 225 held-out logs plus the 150 validation logs, and records the NumPy version and a permutation probe. Not stratified by source; source is reported.
- **Why.** Split CRC is applied per fold, so PM1 applies per fold (Angelopoulos et al. 2024; register C14). A uniformly random partition keeps every test log exchangeable with every calibration log, which is the certificate's assumption (P02 PM1; S02 v03 D4, D5; the transductive guarantee of P01 Thm 5 on the pooled set). Stratifying by source would add an assumption for little balance: the validation share per fold is 0.40 ± 0.05, the ± being the hypergeometric standard deviation (0.051; R20 m10). Source as a stratum would split the logs again and bring back the floor problem.
- **Two child fold files, no new randomness** (Choice 38d). `c1_folds_v03 --restrict-from <375-log folds> --source val` writes role `folds_val150`, and `--source held_out_train` writes role `folds_train225`. Each keeps its parent's fold labels restricted to that source and records `parent_sha256`. The freeze and the guard's `check_child_folds` check that each child is exactly the parent's units of its source, with the parent's labels.
- **Which folds each route uses** (`c1_analyse_v09`):

| Route | Folds role | Claims |
|---|---|---|
| `within_lt3d` (own detector) | `folds` | H1, H2, H3, H10 (and H6, H9 on the same folds) |
| H8 (`c1_h8_v06`) | exactly the `folds` units (config `h8_units` = `folds`; Choice 42d) | H8 |
| `transfer_lt3d` | `folds` | H4 |
| `public_lt3d_val` | `folds_val150` | H1-P, descriptive |
| `voxelnext_val` | `folds_val150` | H5, descriptive |
| `source_transfer` | fit on `folds_train225`'s units (a `source` fit by `entry:c1_fit`), applied to `folds_val150`'s units, which must be disjoint | descriptive |
| AB3DMOT (`tab`) | `folds` | descriptive |
| Q1 (QCNet) | none: not tested (section 1.3) | none |

- **Source reported** (descriptive, pre-specified; it changes no claim): per-fold source and city composition; M\*'s pooled V1 on PD7, SD1_7 and PD and its infeasible rate by source, with a log-bootstrap interval for the difference; the source-transfer reading above (route index 4).

### 3.2 Routes

| Arm | Within AV2 (primary; H1, H2, H3, H6, H8 to H10) | Transfer (H4, H7) |
|---|---|---|
| K8 M\* (`Mstar_ip`), B1, B3, B4, B6, B9 | each log's thresholds from the fit on the other 4 folds (`c1_fit_v06 --route within`, entry `c1_fit`), exact CRC | the all-850-scene nuScenes fit, `60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_{t1,t3}_v01.json` (97f4b78c…, ac4cbda2…), applied by `c1_transfer_apply_v01` |
| RETUNED | cross-fitted selection on the merged α/δ′ curve (21 points) over the AV2 folds (D14 A3's pooled rule; register A4) | the nuScenes point chosen by the same rule: B0a1 (T1), B0d0.3 (T3) (`retuned_transfer_{t1,t3}.txt`); required for H4 (Choice 25) |
| M\*Jx (H3) | for test fold f (0 to 4), λ is fitted on fold g = (f + 1) mod 5 and the base is refitted by M\*'s rule on the other three folds (225 logs); λ is applied to fold f; exact λ decision (`c1_fit_v02`'s rule, used by `c1_fit_v06`; R20 m8) | descriptive |
| M\*J | M\*'s base, λ on its 4 calibration folds; descriptive | descriptive |
| Method-stage M\* and baselines | E1-AV2: 20 repetitions of a 5-fold split of the 375 logs (seeds 20261113 + r), exact CRC in every fit and refit; the repetitions' MC SE is reported (register A6) | the 700-scene nuScenes train fits (M-PLAN E2), two-sample refit log bootstrap |
| Trajectron++ (H9) | DP-SCRC with history-length strata on the C1 folds (`folds`; section 6.4) | H9-T: the nuScenes val fit, descriptive |
| QCNet (Q1) | not run in C1 (Q1 not tested; section 1.3) | none |
| B0, Z0, α-sweep, δ′ arms, LOG | fit-free | fit-free |

**Two transfer sources** (R20 m14). H7 is the method stage's own transfer test (M-PLAN E2), whose frozen definition fits on the 700 nuScenes train scenes; H4 transfers K8's decision-mode arms, fitted on all 850 nuScenes scenes (Choice 7). The two claims keep their own frozen definitions.

**Exact arithmetic (E15).** Every CRC accept/reject decision (every fit, refit and λ) is decided in exact rational arithmetic (`c1_crc_exact_v01.crc_threshold_exact`).

**Ordering.** The transfer fits, the split and the folds exist and are hashed before the freeze; every within-AV2 fit is made after the freeze and the deposit, by frozen code, from stage-B items, and is checked by provenance (Choice 24).

**`c1_transfer_apply_v01` is unguarded by design** (Choice 43c; R17e section 5). It imports only the standard library, reads only the nuScenes transfer fit and the units of the folds file, copies the fit unchanged (asserted), and computes no statistic. Given ground truth as the fit it refuses, and given it as the folds it fails before writing anything. Its output is checked by hash downstream: `c1_run_v06` requires the source fit bound as `transfer_fits`, and the analysis checks that the applied fit equals its source.

---

## 4. Comparators and arms

| Arm | Label |
|---|---|
| **M\*** (`Mstar_ip`), per-constraint DP-SCRC | primary certificate |
| K = {B0, B1, B3, B4, B6, B9, RETUNED} | Form B comparators; never changed (Choice 12) |
| B4 | also the Form C reference |
| K_J = {M\*, B0, B1, B3, B4, B6, B9, RETUNED} | joint-loss comparators for H3 |
| M\*Jx | secondary (H3) |
| M\*J, RETUNED-HK1, Z0, α-sweep, δ′ arms, LOG | descriptive; never comparators |
| Trajectron++ `int_ee` (ECCV 2020 branch, commit ef0165a9…; tracker histories; covariance V2 primary; forward-pass seed 20261102, torch seed fixed per scene, k and node, Choice 27); `int_ee` whatever map data arrive (R20 m12) | H9 (secondary, fixed) |
| Trajectron++ with forward-pass seeds 20261104 and 20261105 (all three seeds' predictions made before any H9 outcome) | descriptive seed-robustness label (Choice 38b) |
| Trajectron++ noHL; H9-T; TPPgt | descriptive |
| AB3DMOT (`tab`) as a third tracker, with every arm above | descriptive (Choice 38c) |
| QCNet (AV2 checkpoint, commit 55cacb41…) | not run in C1: Q1 is not tested (Choice 44d; section 1.3) |

---

## 5. Modes and endpoints (D14 sections 2 and 4, unchanged)

- **Decision mode** carries H1 to H4 and H10: one decision per keyframe from the logged ego's state, identical states for every arm, leash to the log, v_max = log maximum + 2 m/s, 32 accelerate-then-brake candidates and the emergency stop, object-axis half-spaces with a 0.5 m buffer every 0.25 s to 2 s, exemption rule C8, back-off ladder λ ∈ {0.75, 0.5, 0.25, 0}, recorded tracks at score ≥ 0.4, deployable covariance with σ_a = 0.10 m. The bases of these settings are register rows C15a to C15h and C12c.
- **Planner sensitivities** (Choice 50g; register C15c to C15e). Descriptive only, and they block nothing: the buffer at 0.25 and 1.0 m, a denser candidate set, and the shares reported by range and horizon. They run on nuScenes development after the lock-critical work, and they cannot change a frozen setting.
- **Loop mode**: non-reactive closed-loop replay, delays 0, 1, 2 s; descriptive (section 6.6).
- **Endpoints**: V1 per-constraint exceedance; O1 infeasible-decision rate (O2 progress and speed, O3 back-off, descriptive); S1 V2_viol, collisions, front-buffer intrusions; S2 TTV < 4 s and `ttv_enf`, with TTV < 2 s labelled "arm-invariant by construction"; the joint loss J_P; C1 to C4 calibration and sharpness; method-stage cell exceedance and margins.

---

## 6. Statistics, GO condition and multiplicity

### 6.1 Units, bootstrap, seeds, the power rule and the frozen configuration (Choices 47j, 47k, 50d, 50e)

- **Unit and estimand.** The log; the log-level mean of each log's rate (P01 Thm 5, P02 PM1; register A1). The log is the bootstrap unit (Davison and Hinkley 1997 section 3.8; Field and Welsh 2007; register C3a).
- **Bootstrap.** Log bootstrap B = 2000, weights shared by every arm (fixed outside the smoke mode of `c1_analyse_v09`). Form B's decisive bounds have a Monte Carlo SE of 0.0008 to 0.0012 on development and lie 473 to 880 MC SEs below 0; no seed set out of 500 gives a bound ≥ 0 (Choice 50e; register C3b). Form B's bound is reported with its MC error.
- **Inference is conditional on the fitted thresholds** (Choice 47k; R20 P9). The log bootstrap holds each route's fitted thresholds fixed, so it tests the risk of the fitted rule; the method stage's refit-CV estimates the marginal quantity. The pre-registered seeds decide every status. The independent results review (R21) reports, descriptively, the share of 20 alternative seed sets under which each H1 flag, floor and Form B bound holds, every cell with |t − q| < 0.2, and every change of a power-family size; it changes no status.

| Use | Seed |
|---|---|
| Folds, 375 logs; the child files `folds_val150` and `folds_train225` are restrictions of it, with no new randomness | 20261112 |
| K8 log bootstrap, decision mode | [20261110, i, j], i = 0 T1, 1 T3, 2 AB3DMOT (descriptive) |
| K8 power rule (floors) | [20261111, i, j] |
| Loop mode | [20261110, i, j, 1] |
| Route index j | 0 within AV2 (H1, H2, H3, H10); 1 transfer (H4); 2 VoxelNeXt on validation (H5); 3 public LT3D on validation (H1-P); 4 source transfer; 5 predictor arm (H9, H9-noHL) |
| Method stage (H6, H7) | 20261113: E1 folds 20261113 + r (r = 0 to 19), refit-CV 20261113 + 1000 + b, bootstrap generators [20261113, crc32(label)] |
| H8 bootstrap | [20261113, 8], B = 2000 |
| E⁰ (H8) | 20261114 (asserted by `c1_e0_v05` and by the analysis's recompute) |
| Trajectron++ forward pass | 20261102 (primary; the H9 table must come from it); 20261104 and 20261105 (seed robustness, descriptive) |
| H9 bootstrap and power | [20261110, i, 5] and [20261111, i, 5], i the tracker index (0 T1, 1 T3) |
| Detector split | 20261102 |

- **Cell flag**: one-sided simultaneous sup-t over the arm's evaluable cells, at the level section 6.2 gives for its use; zero SE with Ê > δ flags. A comparator's non-finite quantile is recorded as q = None and its cells are judged by Ê > δ. **A family in which M\* has zero exceedance in every bootstrap draw** (a non-finite quantile) is judged the same way, by Ê > δ; it no longer raises (`c1_analyse_v09`; R20 m13). Every zero-SE case, and its effect on V_t, is reported (Choice 50f; register A3).
- **The power rule** (Choices 50d, 50e; register C5 to C7). A cell is power-qualified if its simulated power to flag a true per-cell exceedance of **0.15** in its population's all-evaluable sup-t family is **≥ 0.80**. The power family is the set of power-qualified cells; the floors count them.
  - **0.80:** the conventional type II error of 10 to 20 % (ICH E9 section 3.5; Cohen 1988).
  - **0.15, kept and anchored:** the median exceedance of the comparator cells flagged on development (0.151 over 116 cells); ICH E9 section 3.5 names the anticipated effect as a basis for power. **Caveat:** flagged cells are selected for size; over all evaluable cells of B4 and B6 above δ on PD7 the medians are 0.11 to 0.14. P = 0.10 is the only value that flips a development verdict on the 840 scenes (M\*'s SD1_7 floor fails on T1, and on T3 with more datasets); at 375 units and P = 0.12 the SD1_7 floor fails in every development set (section 7).
  - **Target-only planting:** the tested cell is planted at 0.15 and every other evaluable cell at exactly δ, so no observed outcome enters the rule. This is individual power, the quantity the sentence "power 0.8 against 0.15" states (Senn and Bretz 2007). Development families under it: 27 / 18 / 5 (T1) and 26 / 18 / 5 (T3) on PD7 / SD1_7 / PD.
  - **Beta-binomial ρ = 0.5, kept and now derived:** it is at or above the upper 80 % limit of every pooled development ANOVA ICC (Ridout, Demétrio and Firth 1999) on PD7 and SD1_7 for M\*, B4 and B6 (largest 0.341), following the upper-limit planning practice of Browne 1995 and Turner, Prevost and Thompson 2004. **Caveats:** the scene-unweighted moment estimate reaches 0.448 (B6, T1 SD1_7; M\*'s largest is 0.423), still below 0.5; per-cell ICCs at exceedances of 0.10 to 0.20 have medians 0.42 to 0.48 but a 90th percentile of 0.67 to 0.71, so 0.5 is not conservative for every single cell. Over ρ 0.2 to 0.7 at P ≥ 0.125, no development verdict changes.
  - **2000 simulated datasets** (was 200; Morris, White and Crowther 2019): the MC SE at power 0.8 falls from 0.028 to 0.009, and a cell at true power 0.78 qualifies with probability ≈ 0.02 instead of ≈ 0.28. **Caveat:** near the floor (P 0.10) 200 datasets had decided by chance; at 0.15 the choice changes no development verdict.
  - **The first 500 bootstrap weights** (500 and 2000 give identical development families; register C6e), and **nested seeds [20261111, i, j]**.
  - **F_MIN = 6** power-qualified cells on PD7 and SD1_7: our own value; F_MIN 4 to 8 changes no development verdict, and at 375 development units and P = 0.15 the floor holds in every set (SD1_7 family median 11, 10th percentile 9 to 10). No source sets a minimum count of powered strata (register C7a).
  - **PD:** at least one evaluable cell and no flag in its own power-qualified family; our own rule, and PD validity is claimed for its power-qualified cells only (register C7b).
  - **Evaluable at ≥ 39 logs:** our own value, taken from P01 Prop 6(ii), a calibration-size result; no coverage or size criterion derives it. The development check shows the flag is conservative at every count from 10 to 150 units (size 0.004 to 0.026), so 39 does not inflate false flags; it is not a coverage claim for upper bounds (register C5).
- **Paired operability**: per-log differences at identical decision states; percentile log-bootstrap bounds (Efron and Tibshirani 1993; register C3c). Development coverage at 375 units is 0.968 to 0.983 at 0.975 and 0.982 to 0.993 at 0.9875, every contrast at or above Bradley's lower limit of 0.9625; three bounds are slightly below nominal (section 6.9).
- **p-values for Holm**: from the same bootstrap replicates. A Form B part: |V_t| times the largest per-comparator p (the share of bootstrap means ≥ 0), capped at 1. Form C: the share of bootstrap Δ(B4) > c. H6b: per tracker, the minimum over E1-AV2 cells where M\* is not flagged of max(sup-t p of B4's flag, sup-t p of the paired difference). H10: per tracker, max(the same cell-part p for B6 on PD7, the share of bootstrap Δ(B6) > 0.03). A claim's p is the maximum over trackers. Holm compares them with 0.025 (section 6.5).
- **R\*'s constants in code.** Code v09 carries R\*'s levels and power-rule values as named constants with source comments and pinning tests [[V09: the constants' names, and confirmation that the lead verified them against the development replay values]].

**Frozen analysis configuration** (Choice 47j; R20 P8). The config file is bound as role `config`. It holds exactly the keys the analysis reads [[V09: `c1_analyse_v09`'s key list; the block below is `c1_analyse_v08`'s]]. File references are to the files bound under the named roles, whose hashes the freeze writes into FROZEN_HASHES; `e0` is S21's fill.

```
{
  "c":               {"t1": 0.03, "t3": 0.03},
  "e0":              S21's H8_E0_primary and inputs_sha256 (the e0_plan inputs),
  "folds":           the file bound as role folds,
  "folds_val150":    the file bound as role folds_val150,
  "h8_units":        "folds",
  "h9_label":        "secondary",
  "manifests":       the stage-A manifests bound as role stageA_manifest, each by route and tracker (section 8.1),
  "routes":          within_lt3d, transfer_lt3d, public_lt3d_val, voxelnext_val, source_transfer
                     (each with its tracker tags, fits and run records), plus tab on within_lt3d,
  "units_are_logs":  true,
  "method_stage", "h8", "h9", "method_stage_descriptive", "h9_descriptive":
                     the output paths of the tables of record (section 8.6)
}
no "q1" entry
```

- **Who checks it.** The freeze refuses a `q1` entry, an `h8_units` other than `folds`, and a freeze without `data:e0_plan` or `data:scene_json`. The lead checks every entry at the freeze, `h9_label` = "secondary" included (Choices 43d, 44d, 47c). A missing or extra entry stops the freeze.
- **Stated, not defaulted** (Choice 49j; R20 N11). `c` has a code default (0.03); `h9_label` has none in `c1_analyse_v09`; both are stated.

### 6.2 Definitions and levels (Choice 50; register C2, C8, C9, C10, C11)

Per tracker t; P ∈ {PD7, SD1_7, PD}; f_{a,l} is arm a's infeasible-decision rate in log l.

```
Levels (one-sided; section 6.5 gives the principle)
  γ_M   = 0.95            evidence against M* or M*Jx: cell, family and pooled-LB flags in Valid and ValidJ;
                          M*'s "not flagged" in H6b and H10; H6a, H7, H9
  γ_rm  = 1 − 0.025/9     each of a comparator's 9 removal conditions from V_t (3 conditions × 3 populations)
  γ_rmJ = 1 − 0.025/3     each of a comparator's 3 removal conditions from V^J_t
  L     = 0.995           HK1c's and ValidJ's pooled upper bound (calibrated; see below)
  γ_for = 0.975           evidence for M*: Form C, H10's NI part, and the cell parts of H6b and H10
                          (the comparator's flag and the paired lower bound)

Flag_cell^γ(a,P,c)  := LB^{sup-t,γ}_{a,P}(c) > δ,  or  SE = 0 and Ê_{a,P}(c) > δ
NoFlag^γ(a,P)       := no evaluable cell of P flagged at γ (all-evaluable family)
FamFlag^γ(a,P)      := some cell of a's power-qualified family flagged at γ in that family's own sup-t
NoFlag_pool^γ(a,P)  := pooled cell of P evaluable and LB^{γ}(pooled) ≤ δ
Floor(a,P)          := F_{a,P} ≥ 6 for P ∈ {PD7, SD1_7};  ≥ 1 evaluable cell for P = PD
HK1c(a,P)           := UB^{L}(pooled) ≤ δ + 0.03,  L = 0.995

Valid(a,t)          := AND over P of [ NoFlag^{γ_M} ∧ ¬FamFlag^{γ_M} ∧ NoFlag_pool^{γ_M} ∧ Floor ∧ HK1c ]
ShownAbove(c,t)     := OR over P of [ ¬NoFlag^{γ_rm} ∨ FamFlag^{γ_rm} ∨ (pooled evaluable ∧ ¬NoFlag_pool^{γ_rm}) ]
                       (9 conditions, each at γ_rm; no HK1c term, Choice 47e)
V_t                 := { c ∈ K : ¬ShownAbove(c,t) }      (Choices 9, 47e: a floor-only or HK1c-only failure stays in)
Δ_t(c)              := mean over logs of ( f_{M*,l} − f_{c,l} )

FormB(t)            := Valid(M*,t) ∧ ∀ c ∈ V_t : UB^{1 − 0.025/|V_t|}(Δ_t(c)) < 0      (V_t empty: part (ii) vacuous)
FormA(t)            := Valid(M*,t) ∧ ∀ c ∈ {B0,B1,B4,B9} : UB^{1 − 0.025/4}(Δ_t(c)) < 0  (descriptive)
FormC(t)            := UB^{γ_for}(Δ_t(B4)) ≤ c_t,   c_T1 = c_T3 = 0.03

U_max(M*,t,P)       := max over evaluable cells c of P of UB^{sup-t,0.95}_{M*,P}(c)    (descriptive, approximate; section 0)

J_P(a)              := log-level mean share of a's decisions with some relied constraint of P exceeded over the 4
                       calibrated steps and all tracks, at the reference pose and full margin
ValidJ(a,t)         := AND over P of [ pooled joint population evaluable (≥ 39 logs) ∧ LB^{γ_M}(J_P(a)) ≤ δ ∧ UB^{L}(J_P(a)) ≤ δ + 0.03 ]
V^J_t               := { c ∈ K_J : for every P, ¬( pooled joint population evaluable ∧ LB^{γ_rmJ}(J_P(c)) > δ ) }
                       (3 conditions, each at γ_rmJ; imprecision never removes a comparator, Choice 49c)
```

**ShownAbove, HK1c and an asymmetry** (Choices 47e, 49c, 50b; R20 P13, the stricter branch). ShownAbove is the condition for leaving V_t, and V^J_t's removal rule plays the same part for H3. Failing HK1c (pooled upper bound above δ + 0.03) can reflect imprecision rather than evidence above δ, so it is not a removal condition, for H1 or for H3: a comparator that fails only HK1c stays in, like a floor-only failure, and M\* (or M\*Jx) must still beat it on operability (Choice 9's logic). M\*'s own HK1c requirement, inside Valid, and M\*Jx's ValidJ are unchanged. A comparator leaves only on familywise evidence: each of its removal conditions is tested at 1 − 0.025/9 (V^J: 1 − 0.025/3), because V_t is selected from the data (section 6.5). The same flag test is applied to every arm, at the level its use calls for. An error that makes flags too easy makes M\* fail more often but removes comparators more often; the decision therefore lists, per tracker and comparator, the condition that removed it (cell flag, family flag or pooled lower bound, with its population), or that it stayed in.
- **On development** (final check v02, part C), the stricter rules change neither V_t ({B3} on T1, {B0, B3} on T3) nor H1 nor H3: every other comparator is still removed by a cell flag at 1 − 0.025/9, and V^J is {B3} on T1 and {B0, B3} on T3. [[V09: one sentence with the code author's own replay of `c1_analyse_v09` on the nuScenes rehearsal inputs]]

**HK1c: margin and level** (Choice 50c; register C8).
- **The margin, δ + 0.03, is our own value (class OWN), supported by an approximate derivation.** For split conformal with indicator losses, the realised risk of a correctly calibrated rule follows a Beta(l, n + 1 − l) law (Vovk 2012; Angelopoulos and Bates, arXiv 2107.07511, section 3.2). At n = 300 that law is Beta(15, 286), and δ + 0.03 is its 98.4th percentile. For C1's fraction losses, stratified thresholds and fallback strata the law is an approximation, and the paper says so. It is not a theorem about C1's rule.
- **The level is calibrated** (Loh 1987). At 375 units the 0.95 bootstrap bound covered only 0.915 to 0.920 near δ when pooled (0.898 to 0.934 by population and tracker). **The rule, and its timing.** It was stated in the lead's request to the check's analyst at 13:37 EST on 5 Nov, before the check ran: L is the smallest of {0.975, 0.99, 0.995} whose development coverage at 375 units, for truth in [0.02, 0.10), is ≥ 0.9625 in each of PD7, SD1_7 and PD on both trackers; 0.9625 is Bradley's liberal limit at α = 0.025; if no level qualifies, L = 0.995.
- **Its open reading.** The rule did not say whether coverage meant the mean over a population's cells or each cell's minimum. The analyst applied the mean: 0.930 to 0.961 at 0.975, 0.955 to 0.980 at 0.99 and 0.967 to 0.988 at 0.995, so L = 0.995. On per-cell minima no level qualifies (worst 0.949, T3 SD1_7), and the fallback gives the same answer.
- **The boundary-only reading, disclosed.** With every band cell rescaled to truth exactly 0.08, the HK1c boundary, 0.99 would already reach ≥ 0.963 everywhere. The rule is applied as it was stated, because it was fixed before the result, AV2's zero inflation is unknown and the band covers the more zero-inflated cells, and the cost is power, not validity.
- **The cost.** At 375 development units, P(H1 fails | M\* valid at cell level) rises from 0.020 (v07d's levels) to 0.060, mostly through HK1c on T1's PD cell; plug-in P(H1) falls from 0.903 to 0.870, and capped P(H1) is 0.940 (section 7). On development, M\*'s largest pooled UB at 0.995 is 0.062 (T1 PD), against 0.08.

**An empty V_t (or V^J_t) is vacuous (Choice 25; R17c).** If no comparator remains, Form B's part (ii) holds vacuously, so FormB(t) holds whenever Valid(M\*, t) holds. This matches K8 and Choice 1: Form B asks for operability among valid methods, and there is then none to beat. The decision reports the part as "vacuous", never as a rejection with p = 0. For H1 a vacuous part counts as holding. For a family-S member (H3, H4) a vacuous part gives no p-value; it enters Holm with p = 1 and is not confirmed (section 6.5).

### 6.3 Hypotheses and the GO condition (Choice 33)

```
H1 (primary) := FormB(T1) ∧ FormB(T3)        within AV2, own detector, 375 logs, decision mode
C1 GO        :⇔ H1 holds, with every input H1 needs present and provenance-valid. H1's inputs (R20 m6) are, on the
                within_lt3d route for T1 and for T3: the runs and fits of M*, B0, B1, B3, B4, B6, B9 and RETUNED,
                with the 21 merged α/δ′ points RETUNED selects from; the folds; the split; the stage-A to stage-B chain;
                and the deposit record. Otherwise NO-GO, with H1's failed or missing conditions named (and nothing else).
                A missing secondary or descriptive arm never changes GO.

H2  := FormC(T1) ∧ FormC(T3)
H3  := ∀ t: ValidJ(M*Jx,t) ∧ ∀ c ∈ V^J_t : UB^{1 − 0.025/|V^J_t|}(f_{M*Jx} − f_c) < 0 ; a fold whose λ does not qualify fails H3 for that tracker
H4  := H1's formula with every fitted arm from the transfer fits; RETUNED's transfer point required
H6a := ∀ t: M* flagged at γ_M in no E1-AV2 cell, fixed-rule and refit-CV
H6b := ∀ t: ∃ E1-AV2 cell c: B4 flagged at 0.975 (refit-CV) ∧ M* not flagged at γ_M ∧ LB^{sup-t,0.975}(Ê_B4(c) − Ê_M*(c)) > 0
H7  := ∀ t: M-stage M*_NS flagged at γ_M in no E2-AV2 cell ∧ pooled E2-AV2 cell LB^{sup-t,0.95} ≤ δ
H8  := T1, on exactly the units of the folds role (375 logs):
       ∃ r ∈ {<20, 20-40}: lateral in-path car cell r has LB > max(δ, E⁰_r) under B0
       ∧ its truth-oriented exceedance has LB > δ
       (X2's FAILS rule; the band is X1's two-sided 95 % sup-t band over the 4 decision cells, `x1_lib_v03.sup_t_band`,
        so each LB is one-sided 0.975; register C12a)
H9  := ∀ t: for Trajectron++ DP-SCRC (history-length strata), over the evaluable E2 cells and the three pooled
       history-length cells HL = {2, 3–4, ≥5} (Choice 39b, amended by Choice 42f m1 in the stricter direction; Choices 43b, 47c):
         (a) floor: ≥ 6 power-qualified E2 cells (HL cells do not count); power computed in the joint
             evaluable E2 + HL family; judged by the frozen predictor arm on the tested population (the keys)
         (b) every HL cell evaluable
         (c) no E2 cell flagged in the E2-only sup-t family (over the evaluable E2 cells), and no power-qualified
             E2 cell flagged in the power-qualified E2 family
         (d) no HL cell flagged in the joint E2 + HL sup-t family (over all evaluable cells), and no power-qualified
             HL cell flagged in the joint power-qualified family
         (e) the pooled cell (each item counted once) not flagged
       all flags at γ_M; primary table from forward-pass seed 20261102; label fixed as secondary (section 6.4)
H10 := ∀ t: [ ∃ PD7 cell c evaluable for both: Flag_cell^{0.975}(B6,PD7,c) ∧ ¬Flag_cell^{γ_M}(M*,PD7,c)
                                              ∧ LB^{sup-t,0.975}(Ê_B6(c) − Ê_M*(c)) > 0 ]
            ∧ UB^{0.975}(Δ_t(B6)) ≤ 0.03
```

**E⁰ for H8** (Choice 31, X1's frozen definition): E⁰_r = P(U⁰ > z₀.₉₅ | kept), a plug-in with truth := m̂ over all (record, axis) candidates before the separating filter, 20 perturbation draws (MC SE ≈ 0.0015, reported; register C12b), σ_a = 0.10 m, computed from stage-A fields of the 375 logs (own detector, T1), with the one prepared ground-truth file, before the quarantine and the freeze:

`[SLOT: S21 H8_E0_primary for car|<20|lat and car|20-40|lat, and e0 inputs_sha256]`

The analysis re-hashes the E⁰ inputs, recomputes E⁰ with the same code and seed, and compares bit for bit. After the quarantine it reads the ground-truth input from its quarantine member, through a temporary file outside the workspace, and checks the decompressed SHA-256 against the recorded hash.

**What a missing or unverifiable input does (Choice 33; Choice 31's NO-GO clause is superseded, Choice 38a).**
- An input H1 needs (the `within_lt3d` route of T1 or T3, or H1's own block), missing, not provenance-valid, made under another deposit record, without a "done" line in the run log, or raising an exception from the entry point: **NO-GO**, with the reason, even if a fix exists later (section 9). An environment stop is not an exception (section 9).
- An input or route a secondary claim needs (H2 to H10), missing, not provenance-valid, made under another deposit record, without a "done" line in the run log, or raising an exception: that claim is **"not tested"**, with the reason or the exception text recorded in `missing_inputs`; it enters family S with p = 1 (if it is a family-S member), is never confirmed, and **never changes GO** (Choice 39d, M2). Only a guard breach (an outcome-blindness or binding violation) aborts the analysis.
- **"Not tested" only for a route without a table of record** (Choice 47h; R20 P6). A route is "not tested" only if it has no "done" line or its run raised; a logged table that exists but was not consumed is a deviation (section 8.6). An output without a "done" line is never a table of record (Choice 49f).
- **Q1** is "not tested" by decision (Choice 44d): the frozen config has no `q1` entry, and the analysis reports Q1 with the two reasons of section 1.3, never among the missing inputs. Q1 has its own block, so it cannot change H9, family S, `gate_H1` or GO (Choice 42f m5).
- **Unit lists and seeds** (Choices 39d M4, 42d). Every table records its sorted unit list and its hash. The method stage and the predictor arm must use exactly the bound folds' units; **H8 exactly the units of the `folds` role** (the frozen config's `h8_units` is `folds`; a table on a subset of the 375 logs is not valid); each table the folds' dataset, the current hash log and the current deposit record. The primary H9 table must come from forward-pass seed 20261102. Under C1, `--scenes` is refused.
- **E⁰ problems make H8 "not tested"**: a missing `e0` entry, missing input hashes, changed or unbound inputs, a recomputed value that differs, or an H8 table without the plan's `E0_plan`. None changes the verdict.
- Every claim gets one status: holds, does not hold, not tested (or descriptive). `gate_H1` equals (verdict = GO), and no claim is confirmed unless the gate holds and the claim holds.

### 6.4 H9 (Choices 23, 35, 37, 38b, 39b, 42f m1, 43b, 44e, 47c, 49l)

- **Population (Choice 35).** PD: the K8 relied in-path items at 2 s, **scored on the K8 tracker-planner's constraints** (the relied axis, the gap and the toward-ego normal and sign taken from the K8 items, which evaluate them at the reference pose, the logged pose at t_k + h), not recomputed from Trajectron++'s own mean. The claim is worded "along the K8 tracker-planner's constraints". The items are paired with the tracker arm item for item, joined by (log, track, k). **This corrects v04 section 11.4**, which described H9's items as the method-stage in-path audit population; that population serves H6 to H8 only, and v04's 150-log cell counts for H9 were counts of it.
- **One keys file.** `c1_predarm_v06` needs one Trajectron++ keys file whose units are exactly the 375 fold units (one stage-B cache for the 375 logs, or keys built over both caches); fold units without keys are refused.
- **Errors.** A unit of the keys outside the folds is an error, before anything is computed; a non-finite D or variance in a used item is an error.
- **History length (Choice 37; register C13a).** Each item's history length is its predictor's own input history at decision time k, read from the Trajectron++ keys (`rec_hist_stratum_trk`: contiguous tracker states up to k, written by `tpp_keys_v03`, which keeps v02's key code); strata {2, 3–4, ≥ 5 states} (category-conditional calibration, Vovk 2012; Monti et al. 2022). Nothing after k is read. A used item below 2 states, or keys without the field, is an error. The cut-points were chosen after D17's outcomes; AV2 is new data.
- **Fit.** DP-SCRC on L0 × HL, L1 × HL, L2 × HL, L3 × HL, then L3 as the last fallback, so every item has a threshold; a cell gets its own exact-CRC threshold with at least 19 calibration units, otherwise its items fall back; cross-fitted on the C1 folds.
- **Validity rule (Choice 39b, amended by Choice 42f m1; Choices 43b, 47c; `h9_rule_v05`).**
  - **Floor, condition (a).** At least 6 power-qualified **E2** cells (register C13b, an own value as C7a). The three history-length cells do not count toward the 6. The floor is computed by the frozen predictor arm from outcome-free counts on the population actually tested, the Trajectron++ keys, with the power rule of section 6.1.
  - **Power** is computed in the joint evaluable E2 + HL family (`power_family`, with Šidák's critical value for that family). A larger family has a larger critical value, so a cell's power can only fall; counting power-qualified E2 cells under the joint family is therefore at least as strict as under the E2-only family (Choice 43b, kept as coded).
  - **E2 cells are flagged against the E2-only sup-t families** (the evaluable E2 cells; and, for the family flag, the power-qualified E2 cells), as in D17's frozen H9.
  - **HL cells are flagged against the joint E2 + HL sup-t families** (all evaluable cells; and, for the family flag, all power-qualified cells). Each HL cell must be evaluable, and none may be flagged.
  - **The pooled cell** counts each item once and must not be flagged.
  - Seeds [20261110, i, 5] and [20261111, i, 5].
  - **Why E2 only, for the floor.** Each history-length cell holds about a third of the items and overlaps the E2 cells, so it is almost always power-qualified. Counting them would let 3 qualified E2 cells meet a floor of 6, which is what the floor exists to prevent (R17c M3).
  - **Why E2-only flags (an amendment to Choice 39b in the stricter direction).** v06 flagged the E2 cells in one family over E2 + HL. The larger family raises the sup-t quantile (2.50 to 2.64 at 7 E2 cells, synthetic; R17d m1), which makes an E2 flag harder to reach. The E2-only family is the smaller one, so an E2 cell above δ is flagged at least as readily as under v06's rule. Development data must not ease a standard; this reading is the stricter one, decided before any outcome.
- **H9's label: fixed as secondary (S20c, filled in v07d; Choice 47c, R20 B3 option b).** H9 is secondary. The frozen config states `h9_label` = "secondary", and the lead checks it at the freeze; `c1_analyse_v09` has no default for it. There is no relabelling before or after the freeze. Choice 39b's floor is H9's condition (a), judged at analysis as above; this amends Choice 23 (as amended by Choice 39b) only as to **when** the floor is judged, and leaves the floor itself unchanged.
  - **If the floor fails,** H9 does not hold for that tracker, with the status text **"does not hold: floor not met"** and the `H9_floor` block recording `family_size_E2` and the floor; the paper says "floor not met", not "fails" (Choice 49l). A power shortfall is thus a failure of H9, not a reason to make it descriptive; H9 affects neither GO nor family S. [[V09: confirm that `c1_analyse_v09` writes exactly "does not hold: floor not met" with the `H9_floor` block; any other wording needs R20's re-check]]
  - **The frozen label governs.** The predictor arm's `S20c_label_from_counts` is reported beside it; a disagreement is reported, never acted on.
  - **Why option (b).** Both options fixed the rule before any outcome and both use outcome-free counts. Option (b) needs no new code, judges the floor on the population actually tested rather than a stage-A proxy, and stops the label from defaulting silently.
- **Seed robustness (Choice 38b).** `c1_predarm_v06` takes the three forward-pass runs (20261102, 20261104, 20261105) in one call, asserts each run's summary seed, and under the plan requires all three before any H9 outcome is computed. The predictions use histories only. H9 is called "seed-robust" only if it holds under all three seeds. The label is descriptive (`H9_seed_robustness`: "seed-robust", "not seed-robust" or "not tested"), outside family S; it never reads or changes H9's status, family S or GO (Choice 41e). No seed is promoted after outcomes.
- **Trajectron++ environments (Choices 44e, 45a).** Each wrapper is checked against the environment it is meant to run in, and both run **on the laptop**. `tpp_keys_v03` runs under **canmot310**, the environment its builder names, and its wrapper record (python, numpy) is compared with FROZEN_ENV. `tpp_run_v03` runs under **tpp38**, and its wrapper record (python, numpy, torch) is compared with FROZEN_ENV_TPP. Before any key or run is made, `c1_tpp_envcheck_v01` (entry `tpp_envcheck`, outcome-free) writes a dry wrapper record under each interpreter and checks it against the frozen plan. Under the plan, `c1_predarm_v06` requires both blocks and makes both comparisons (`env_check`); a mismatch makes H9 "not tested". A pod may be used only if a dry record written on it (`--write-dry`) passes `--check` against the frozen plan first; the pod's keys310 environment (Python 3.10.22, numpy 1.26.4) fails that check and is not used for C1.
- **Why history length.** On the frozen nuScenes D17 run, items with only two tracker states stayed above δ after M\* (0.079, lower bound 0.062, on T1; 0.072 [0.063] on T3), offset by items with five or more (Choice 37, from R19). History length is observable at decision time, so stratifying on it is the method's own principle. It was found on development data and fixed before the freeze.
- **Descriptive companions.** H9-noHL (D17-style strata, E2 cells only); the diagnostic `noHL_on_HL_cells`; H9-T; TPPgt. Q1 (QCNet) is not tested (section 1.3).

### 6.5 Multiplicity (Choices 26, 33, 47g, 50a, 50b; R20 P4)

- **The principle** (Choice 50a; ICH E9 section 5.5). **Evidence against M\*** is judged at one-sided 0.05, the strict direction for M\*: the cell, family and pooled-LB flags, H6a, H7 and H9. **Evidence for M\*** is judged at one-sided 0.025, which equals the conventional two-sided 95 %: Form B at 0.025/|V_t|; H3's superiority at 0.025/|V^J_t|; Form C and H10's NI part at UB^{0.975}; the cell parts of H6b and H10 (the comparator's flag and the paired lower bound) at 0.975; Holm over family S at 0.025; and Form A (descriptive) at 0.025/4. **The exception is HK1c:** its level is calibrated rather than set at 0.975, so that its development coverage meets Bradley's liberal limit for 0.025, which allows an actual error of up to 0.0375 (section 6.2).
- **H1** is an intersection-union test over trackers and conditions. An intersection-union test needs each component only at its level (Berger 1982); the Bonferroni split across V_t (D14 section 4) is kept as a deliberate, conservative choice, and so is "|V_t| times the largest p" for Holm.
- **A comparator leaves the comparison set only on familywise evidence** (Choice 50b). Berger's level assumes a fixed set of components, but V_t is selected from the data, so P(false Form B) ≤ α + P(a valid comparator is removed) (Benjamini and Yekutieli 2005; Bonferroni). Each of the 9 removal conditions is therefore tested at 1 − 0.025/9 (for H3's V^J, 3 conditions at 1 − 0.025/3). **Form B's total error is at most 0.025 + 0.025 = 0.05 at nominal levels.** On development, the paired bound's actual error was up to 0.032 at nominal 0.025 (T1, B3), within Bradley's band; and a comparator planted at δ was removed with probability 0.09 to 0.14 under the old rule (0.95 per condition), against ≤ 0.018 at 0.05/9; 0.025/9 is stricter still.
- **No-flag validity tests are not corrected across populations or claims;** within a population the sup-t family is simultaneous (R20 m5; register A2: a correction would make a non-rejection claim easier). This covers H6a, H7, H9 and the validity parts of H1, H3 and H4; each population at γ_M.
- **H9** is an uncorrected no-flag claim with no p-value and belongs to no family (R20 m18). Its label is "secondary" because it is pre-registered with a fixed rule, not because it is in a multiplicity family.
- **Family S = {H2, H3, H4, H6b, H10}, m = 5 fixed.** Tested only if H1 holds; then **Holm at family-wise one-sided 0.025** (Holm 1979; Dmitrienko and Tamhane 2007; ICH E9 section 5.6). A member that cannot be tested (gate failed, route absent, input missing, no p-value) enters with p = 1. A vacuous Form B part gives no p-value and enters with p = 1. A member is confirmed only if its bound-based verdict holds **and** Holm rejects at its level. If H1 fails, the members are reported unadjusted as "supportive, not confirmatory (gate H1 not passed)".
- **Family P = {H8}** has its own level, not gated on H1: X2's two-sided 95 % band, that is one-sided 0.025 per bound. **Why no adjustment** (register C11b; ICH E9 section 5.6): H8 replicates a premise about B0, not a claim about M\*. The study-wise error over {H1 → S} and P is at most 0.05 + 0.025.
- **Outside every family:** every descriptive claim, including AB3DMOT's rows, H9's seed-robustness label, M\*'s descriptive upper bounds and the criteria audit's outputs; and Q1, which is not tested. The code passes only T1 and T3 to the decision, so AB3DMOT cannot reach `gate_H1` or family S (Choice 38c).

### 6.6 Reading rules (E8, E9, E14; R16)

- **Loop mode (E8).** Descriptive only; no ordering of arms; T1 is never quoted without T3. LOG's zero holds by construction (the artefact filter removes every collision LOG has at the same scene and delay) and LOG is never a reference. Allowed sentence: "In closed-loop log replay with non-reactive agents, no difference in at-fault collisions between M\* and any comparator was resolved on either tracker."
- **V2 (E9).** Reported at its development level with the dependence stated: M\*'s V2 is 0.358 [0.325, 0.392] (T1) and 0.351 [0.320, 0.386] (T3), against the track reference 0.308; a decision holds about 8.35 tracks but 30 relied records. The per-constraint certificate leaves about one decision in three with some margin broken; M\*Jx (H3) is the pre-registered remedy.
- **RETUNED (E14).** Selected by the pooled rule, judged by the cell rule; reported with the arm chosen per fold and whether any α/δ′ point passes Form B's rule in sample. RETUNED-HK1, cross-fitted on Form B's rule, is descriptive and never in K.
- **Validity in the paper** (Choice 47f): "not shown above δ in any cell, with power 0.8 against a true 0.15", with the descriptive upper bounds beside it, labelled approximate.
- **The 12 overclaim sentences of R16 section 5 bind the write-up.**
- **The outcome-blindness statement** is made only in the scoped form of section 11.3.

### 6.7 H3's caveats (Choice 21)

Point estimates just under δ, validity resting on the +0.03 tolerance; certification at the reference pose and full margin, the executed-margin joint exceedance not certified; decision mode only; the held-out joint loss varied by fold (0.030 to 0.075 on development), so the guarantee holds in expectation. With λ fitted on 75 logs the CRC allows a calibration-fold joint loss of at most 0.037 (0.044 on nuScenes folds), so λ and the price will sit somewhat above development's (+0.34 on T1, +0.42 on T3). Under R\*, M\*Jx's ValidJ upper bounds at 0.995 on development are PD7 0.056 / 0.060, SD1_7 0.011 / 0.013 and PD 0.005 / 0.008 (T1 / T3), all ≤ 0.08; its superiority bounds are −0.381 (T1, B3), −0.160 (T3, B0) and −0.263 (T3, B3) (final check v02, part C).

### 6.8 Sources of the design choices (Choices 47l, 50i; register v03 sections 2 and 4)

**The full basis table** is `90_DECISIONS/C1_CRITERIA_REGISTER_v03.md` (SHA-256 8d2be6c583c2078fad574ce4b0bdbbd3055db9fc92c8667157d73ace59dd6162): all 46 criteria with their decided value, basis, class (PROVEN, STANDARD, PRACTICE, DEV, OWN) and confidence. The table below lists the sources behind the plan's design choices, with register v03 section 4's corrections and additions applied. Bian and Barber 2023 and Bao et al. 2024 were checked on the web on 5 Nov 2026; Loh 1987, Browne 1995 and Turner, Prevost and Thompson 2004 were checked at abstract level on 5 Nov; the other entries are as R20 and the evidence review (`90_DECISIONS/C1_CRITERIA_EVIDENCE_REVIEW_v01.md`, d24bfe63…, section 7) give them, and are checked again before the manuscript cites them. R20's novelty-risk list (R20 v01, "Literature gaps (b)") belongs to the manuscript and is carried in D16 v31 Choice 49(k).

| Choice in this plan | Source |
|---|---|
| Error levels: against M\* at 0.05, for M\* at 0.025; why some families are not adjusted | ICH E9 sections 5.5 and 5.6; ICH E9(R1) |
| One-sided simultaneous sup-t bound across cells | Montiel Olea and Plagborg-Møller, *J. Applied Econometrics* 2019 (sup-t bands); Hothorn, Bretz and Westfall, *Biometrical J.* 2008 (max-t) |
| Log-cluster bootstrap, B = 2000, percentile bounds | Davison and Hinkley 1997 section 3.8; Field and Welsh, *JRSS-B* 2007; Efron and Tibshirani 1993; Andrews and Buchinsky 2000 (MC error of the bound); Cameron, Gelbach and Miller, *REStat* 2008, who favour bootstrap-t with few clusters (C1's flags are studentised, and the paired percentile bounds use 375 logs); Cameron and Miller 2015 |
| HK1c's level calibrated by development coverage; Bradley's liberal limit | Loh, W.-Y. (1987). Calibrating confidence coefficients. *JASA* 82(397):155–162, doi 10.1080/01621459.1987.10478400; Bradley 1978 (from secondary sources) |
| HK1c's margin δ + 0.03 (own value, approximate derivation) | Vovk 2012 (conditional validity; the Beta law); Angelopoulos and Bates, arXiv 2107.07511, section 3.2 |
| H1 as an intersection-union test | Berger, *Technometrics* 1982; Berger and Hsu, *Stat. Sci.* 1996 |
| Removal from V_t only on familywise evidence | Benjamini and Yekutieli, *JASA* 2005; Bonferroni |
| Holm within family S, gated on H1 | Holm, *Scand. J. Stat.* 1979; Dmitrienko, A. and Tamhane, A. C. (2007). Gatekeeping procedures with clinical trial applications. *Pharmaceutical Statistics* 6(3):171–180, doi 10.1002/pst.291 |
| Form C and H10's NI part: pre-specified margin at one-sided 0.025 | ICH E9 section 3.3.2; ICH E10; FDA 2016 (non-inferiority; its text not opened) |
| "Not shown above δ"; U_max and HK1c reported, no equivalence claimed | E10 (own); Schuirmann 1987, cited as the reason U_max is reported and no equivalence is claimed (he is not a source for "not shown above δ", which would invert his conclusion); Wellek 2010; Altman and Bland, *BMJ* 1995 (absence of evidence) |
| Power rule: power 0.80 against 0.15 | ICH E9 section 3.5; Cohen 1988; development anchor (register C6a) |
| Target-only planting (individual power) | Senn and Bretz 2007 |
| ρ = 0.5 | development ICCs (Ridout, Demétrio and Firth 1999); the upper-limit planning practice of Browne, R. H. (1995), On the use of a pilot sample for sample size determination, *Statistics in Medicine* 14(17):1933–1940, doi 10.1002/sim.4780141709, and Turner, R. M., Prevost, A. T. and Thompson, S. G. (2004), Allowing for imprecision of the intracluster correlation coefficient in the design of cluster randomized trials, *Statistics in Medicine* 23(8):1195–1214, doi 10.1002/sim.1721; Donner and Klar 2000 for the design-effect concept only |
| 2000 simulated datasets; MC SEs reported | Morris, White and Crowther 2019 |
| F_MIN = 6; evaluable at ≥ 39 logs | own values with development checks (register C7a, C5); the origin of 39 is P01 Prop 6(ii), a calibration-size result |
| n_min = 19 | Angelopoulos et al., ICLR 2024, Thm 1 ((n + 1)δ ≥ 1 at δ = 0.05); P02 PM1 |
| Hierarchical fallback L0 to L3 | Ding et al., NeurIPS 2023 (clustered conformal), the nearest pooling scheme |
| The log as the exchangeable unit | P02 PM1; Lee, Barber and Willett, arXiv 2306.06342 (hierarchical conformal); Dunn, Wasserman and Ramdas, *JASA* 2023 |
| Marginal against fitted-rule risk (sections 0, 6.1) | P02 "Estimand"; Vovk 2012; Bian and Barber, *Electron. J. Statist.* 17(2):2044–2066, 2023 (training-conditional coverage; verified); Bates et al., *JACM* 2021 (RCPS) |
| Cross-fitted calibration on 5 folds | split CRC per fold, so P02 PM1 applies per fold (Angelopoulos et al. 2024); Vovk 2015 (cross-conformal) and Barber et al., *Ann. Stat.* 2021 (jackknife+, CV+), cited as practice only |
| Evaluation on the planner's relied set (selection) | Benjamini and Yekutieli, *JASA* 2005 (FCR); Jin and Candès, *JMLR* 2023; Bao, Huo, Ren and Zou, *Biometrika* 111(3):727–742, 2024 (selective conformal; verified) |
| History-length strata {2, 3–4, ≥ 5} | development-derived (D17, R19, Choice 37); category-conditional calibration (Vovk 2012); Monti et al. 2022 |
| Stage A/stage B and the quarantine (blind analysis) | Klein and Roodman, *Annu. Rev. Nucl. Part. Sci.* 2005; MacCoun and Perlmutter, *Nature* 2015; Nosek et al., *PNAS* 2018 |
| Binding by hash | NIST FIPS 180-4 |
| Data, detector, metrics, predictors | Wilson et al., NeurIPS Datasets and Benchmarks 2021 (Argoverse 2); Peri et al., CoRL 2022 (LT3D); Zhu et al. 2019, arXiv 1908.09492 (CBGS); Chen et al., CVPR 2023 (VoxelNeXt); Luiten et al., *IJCV* 2021 (HOTA); Salzmann et al., ECCV 2020 (Trajectron++); Zhou et al., CVPR 2023 (QCNet) |
| δ = 0.05; per-constraint risk | Blackmore, Ono and Williams 2011 (D16 Choice 2); Angelopoulos et al. 2024, Thm 1 (n ≥ 1/δ − 1). Lindemann et al., RA-L 2023 set each step's level to δ/T so that the whole trajectory holds at 1 − δ; C1 allocates per constraint instead, and H3 is its trajectory-level claim |
| Sampled candidate set | Werling et al. 2010 (values own) |
| One forward-pass seed as the deployed condition | none: an argument (Choice 27), with the seed-robustness label beside it |
| Trackers transferred with nuScenes parameters; two detector epochs set by budget | none possible: design constraints (D18 v03) |

### 6.9 Limits, as the paper states them (register v03 section 5)

1. **The detectable effect.** Our power rule gives each cell power 0.80 against an excess of 0.15, an anchor taken from comparator cells that were flagged, and so selected for size. On the 840 development scenes the SD1_7 floor fails at 0.10, and at 375 units with development record counts it fails at 0.12. We therefore claim validity against per-cell excesses of about 0.15 and above, not smaller ones, and we report MDE80 per cell.
2. **HK1c's coverage is approximate.** At L = 0.995 its development coverage averages 0.967 to 0.988, and the worst single cell is 0.949. The Beta-law margin is exact for split conformal with indicator losses; for our fraction losses and fallback strata it is an approximation.
3. **U_max and the cell upper bounds are approximate.** Their development coverage near δ is 0.78 at 39 units and 0.87 at 150.
4. **Three paired bounds under-cover slightly:** B3 at 0.975 (0.9678 on T1, 0.9725 on T3) and at 0.9875 (0.9835 on T1, 0.9815 on T3), and B0 on T3 at 0.975 (0.9728). All are above Bradley's lower limit of 0.9625, and every Form B bound is far from 0 (−0.725 on T1; −0.571 and −0.680 on T3).
5. **Some values are our own judgement:** F_MIN 6 and PD ≥ 1; MIN_UNITS 39; HK1c's margin of 0.03; c = 0.03 for Form C and H10; H9's floor; E⁰'s 20 draws; σ_a = 0.10 m; the planner's buffer, range, candidates and v_max; the zero-SE rule, the method stage's repetitions, and the rule that a missing H1 input gives NO-GO. Over its plausible range none of them changes the development verdict, or the value cannot affect GO. The planner sensitivities are descriptive.
6. **All development evidence is nuScenes.** AV2's record counts, zero inflation and within-log correlation may differ. The counts (S20a, S22) are computed from AV2 inputs before stage B, without outcomes, and the frozen rules apply to them as written.
7. **The confidence grades are judgement** about a referee, not a measurement.
8. **Some sources were checked only partly:** some bibliographically or at abstract level only; FDA 2016's text was not opened; Bradley's band comes from secondary sources; the clauses of ISO 21448 and ICH E10 were not read in the primary documents.

---

## 7. Power and operating characteristics

`[SLOT: S22 power on the real counts]`

**S22 is reported only** (Choices 47i, 49g). It changes no label, rule, threshold or population. Its tool is `c1_power_counts_v05` (bound in README v09; R\*'s levels, target-only planting and 2000 datasets; Choice 47(e)'s and 49(c)'s stricter comparator rules; H9's PD population, not the method-stage audit population; its hash is recorded before it runs), and its development inputs are the K8 Linux replicate's v03 analysis (R16). Its output is bound as `data:s22`. **S22's H9 figure leaves out history length** (history-length counts need the keys), so it overstates H9's power.

**Development operating characteristics at 375 units under R\*** (Choice 50h; final check v02, part D; nuScenes development record counts, 375 development scenes per set, 300 sets per variant; replaced for AV2 by S22):

| Variant | P(H1) | P(H1 fails) | Main reasons |
|---|---|---|---|
| Plug-in rates, P = 0.15 | **0.870** | 0.130 | T1: HK1c 0.090, pooled 0.023, family flag 0.017; T3: family flag 0.040, cell flag 0.020 |
| M\* capped at δ (valid at cell level), P = 0.15 | **0.940** | 0.060 | T1: HK1c 0.053, pooled 0.013, family flag 0.010; T3: family flag 0.003 |
| Plug-in or capped, P = 0.12 (descriptive) | 0.000 | 1.000 | the SD1_7 floor fails in every set |

- **P(H1 fails | M\* valid at cell level) is 0.060 under R\*, against 0.020 at v07d's levels,** mostly through HK1c on T1's PD cell: M\*'s pooled PD exceedance on T1 is 0.049, close to δ, and its pooled UB at 0.995 on the 840 scenes is 0.062 (section 6.2). Plug-in P(H1) falls from 0.903 to 0.870. Both P(H1) figures stay above 0.80.
- **M\*'s families at 375 units**, median (10th percentile), with the median record share:

| | PD7 | SD1_7 | PD |
|---|---|---|---|
| P = 0.15 | 23 (22–23); share 0.988 | 11 (9–10); share 0.90–0.91; P(≥ 6) = 1.00 | 3–4 (2–3); share 0.51–0.61 |
| P = 0.12 | 18 (17–18); share 0.95 | 3 (2); share 0.57–0.58; P(≥ 6) = 0 | 0 |

- **A stated limit, not a footnote.** At P = 0.12 the SD1_7 floor fails in every development set (family median 3, against 11 at 0.15), so **the study is powered for per-cell excesses of about 0.15**. With 375 units per cell the power curve is steep between 0.12 and 0.15 (on the full 840 scenes the family at 0.12 was 12 to 15). This uses development record counts, not AV2's (section 6.9).
- H2 and H10 hold in every set. B6 never stays in V_t; B9 stays in V_t in 2 to 4 % of sets, and B1 on T1 in 3 to 5 %.
- **The OC uses the analytic family** (each cell's normal power at P against the Šidák critical value of its evaluable family), in which target-only and all-cells planting coincide and the dataset count has no role; on the 840 scenes it equals R\*'s simulated family for M\* in all six combinations (27/18/5 and 26/18/5), and differs by 0 to 2 cells for B0 and B3.
- **These figures supersede** v07d's provisional values (`c1_power_375_v04.json`: P(H1) 0.91, 0.97 capped) and D18 v03's (P(H1) 0.94; P(B6 passes on T3) 0.02), which used the old levels (R20 m4). v05's "a family of 6 to 7 cells" for H9 was computed on the method-stage in-path audit population and is withdrawn. H9's floor is judged at analysis (section 6.4).

**Descriptive outputs of the criteria audit** (Choice 50f; they decide nothing), reported with S20a and S22 before the freeze and, where they need outcomes, at analysis:
- the record coverage of each power family;
- the families at F_MIN 4 and 8;
- per-cell power at P = 0.10, 0.12 and 0.20, from which MDE80 (the per-cell excess detected with power 0.80) is read;
- every zero-SE case and its effect on V_t;
- U_max and the cell UBs, labelled "approximate" (development coverage near δ 0.78 at 39 units, 0.87 at 150).

The power tools `c1_power_counts_v01` to `v04` are pre-freeze tools, not part of the confirmatory path, and are not bound (README v06 to v08); their outputs are cited by hash.

---

## 8. Code, binding, freeze, deposit and run order (README_C1_CODE_v09)

### 8.1 Entry points, data roles and frozen blocks

**README v09:** [[V09: README v09's final name, SHA-256 and role counts; final before the text lock (Choice 49a)]]. README v08 listed 154 files (entry 16, module 52, generator 14, source 13, builder 15, legacy 2, test 1, test_module 17, archive 24).

The roles the freeze writes into the FROZEN_ROLES block [[V09: confirm against README v09]]:

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v09.py` |
| `entry:c1_fit` | `c1_av2/c1_fit_v06.py` |
| `entry:c1_run` | `c1_av2/c1_run_v06.py` |
| `entry:c1_mstage` | `c1_av2/c1_mstage_v06.py` |
| `entry:c1_h8` | `c1_av2/c1_h8_v06.py` |
| `entry:c1_e0` | `c1_av2/c1_e0_v05.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v06.py` |
| `entry:c1_transfer_apply` | `c1_av2/c1_transfer_apply_v01.py` (unguarded by design, section 3.2) |
| `entry:c1_folds` | `c1_av2/c1_folds_v03.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v07.py` (Choice 48) |
| `entry:c1_quarantine` | `c1_av2/c1_quarantine_v02.py` |
| `entry:tpp_envcheck` | `c1_av2/c1_tpp_envcheck_v01.py` (outcome-free, no guard; Choice 45a) |
| `entry:stageB` | `av2/av2_cache_stageB_v06.py` (generated by `tests/make_av2_stageB_v06.py`) |
| `entry:k8_items` | `k8/k8_items_v08.py` (generated by `tests/make_k8_items_v08.py`) |
| `entry:tpp_keys` | `tpp/tpp_keys_v03.py` (canmot310) |
| `entry:tpp_run` | `tpp/tpp_run_v03.py` (tpp38) |

- **Builders bound in README v09:** the port's tools of section 1.1, `c1_av2_scene_map_v01`, `c1_av2_provenance_v01`, `c1_power_counts_v05` and the GT-inventory builder. `c1_freeze_v07` requires every entry role above, `entry:c1_quarantine` and `entry:tpp_envcheck` included. `entry:c1_qcnet_summary` is no longer a role.
- **The bound test** is `tests/test_c1_v12.py`, which reads README v09, so FROZEN_TESTS certifies the README the freeze binds (Choice 47a; R20 B1). It covers the new tools of Choices 47 to 50, R17f's N1 and N2 as copy-tree refusal tests, R\*'s constants as pinning tests, and re-runs `test_c1_v11`'s groups against README v09 [[V09: confirm the test's name and scope]]. The port's builders are also covered by their equivalence records (`data:port_equiv`) and by the provenance check.
- **The guard** is `c1_guard_v05` [[V09: or `c1_guard_v06`, if README v09 binds it as the guard the entry points import]], which imports `c1_guard_v04` and, through it, `c1_guard_v03`; `c1_guard_v02` and `c1_crc_exact_v01` are unchanged, because D17 v04 binds them. `x1_full_v02`, `x2_full_v02` and `m_run_v04` are bound as modules, unchanged. No file bound by the frozen X1, X2, M or D17 plans was edited.
- **Bound only as a module or source; refused as an entry point by role** (R20 m1): among the v07-era files, `c1_predarm_v05` and `c1_analyse_v07` (modules) and `av2_cache_stageB_v05` and `k8_items_v07` (sources).

**Data roles** (Choice 47j). `folds`, `folds_val150`, `folds_train225`, `split`, `transfer_fits`, `config`, `stageA_manifest`, and, as `data:<name>`:

| Data role | File |
|---|---|
| `data:scene_json` | the scene map written by `c1_av2_scene_map_v01` |
| `data:e0_plan` | E⁰'s plan inputs (S21) |
| `data:s20a` | the S20a counts |
| `data:s22` | the S22 power file |
| `data:logs375` | `30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` |
| `data:gt_inventory` | `40_PROTOCOL/C1_GT_INVENTORY_v01.json` |
| `data:rule0_metrics` | the Rule-0 metric files of the 375 logs (`60_RESULTS/av2_trk/c1_375/metrics/`, `hota/`) |
| `data:provenance` | the success record written by `c1_av2_provenance_v01` |
| `data:port_equiv` | the port's equivalence records (`60_RESULTS/av2_trk/c1_375/equiv/`) |

`data:s20c` is dropped (Choice 47c).

**The bound stage-A manifests, by role** (`stageA_manifest`; their paths and hashes are recorded in FROZEN_HASHES; every stage-A manifest stays in place until stage B, Choice 48a):
- route `within_lt3d` (and `transfer_lt3d`, `source_transfer`): the 375-log own-detector manifests of T1, T3 and AB3DMOT (`tab`), built by `av2_cache_stageA_v02`;
- route `public_lt3d_val` (H1-P): `30_DATA/av2_cache_stageA_v01/cache_stageA_t1_lt3d/` and `cache_stageA_t3_lt3d/`;
- route `voxelnext_val` (H5): `30_DATA/av2_cache_stageA_v01/cache_stageA_t1_voxelnext/` and `cache_stageA_t3_voxelnext/`.

`30_DATA/av2_cache_stageA_v01/cache_stageA_ab3dmot_lt3d/` serves no route; the quarantine and the freeze find it with every other AV2 stage-A manifest under `30_DATA`.

**The provenance line** (Choices 46d, 48b m-2; filled at the freeze, the only post-lock change outside the slots): the success record of `c1_av2_provenance_v01`, bound as `data:provenance`, SHA-256 recorded at the freeze. For each 375-log stage-A manifest, the tool follows every input hash (tracker outputs, horizon file, ground-truth file, ego file, scene map) to its producing tool's receipt, and requires that tool's hash to be a bound builder of README v09. It writes its output only on success, and `c1_freeze_v07` refuses a `data:provenance` file that is not a success record for the README being bound. The freeze itself checks only the stage-A manifests' own `builder_sha256` (and refuses an AV2 stage-A manifest without one, m-6); the upstream builders are covered by the provenance check alone.

**The blocks at the end of this file are written by the freeze, not by hand (Choice 41a).** The draft carries only the empty FROZEN_HASHES and FROZEN_ROLES blocks. `c1_freeze_v07` fills those two and inserts three more after them, in this order:
- FROZEN_ENV: the Python, NumPy and SciPy versions of canmot310, asserted at run time by the guard, and compared with the `tpp_keys_v03` wrapper records (Choice 44e);
- FROZEN_ENV_TPP: the python, numpy and torch versions of the `tpp38` environment, read by running its interpreter or given by `--tpp-env`, and compared with the `tpp_run_v03` wrapper records (Choices 42f m4, 44e);
- FROZEN_TESTS: `test_c1_v12`'s hash, verdict and output hash, run with `C1_FREEZE_LOG_SHA256`; the generator checks; the Choice 36 edit checks; the stage-A builder comparison; the quarantine check and the workspace hash scan, with the skipped folders listed by name (section 8.4); the frozen-config check; the scene-map check; and the provenance-record check.

The freeze refuses a plan that already holds a FROZEN_ENV, FROZEN_ENV_TPP or FROZEN_TESTS block, and asserts that each of the five blocks appears exactly once in the frozen file (Choice 41a; `c1_freeze_v07` keeps v05's check and block layout [[V09: confirm]]).

### 8.2 One freeze, the stage-B log, and amendments (Choices 39c, 42a, 42c, 44c, 48)

- **One freeze.** The plan is frozen once, by `c1_freeze_v07`. It refuses if the canonical log `40_PROTOCOL/C1_PLAN_HASH_LOG.txt` already holds a C1 line, unless `--amend "<reason>"` is given.
- **No freeze and no amendment after an outcome run.** The freeze refuses **any** freeze or amendment while the append-only stage-B log `40_PROTOCOL/C1_STAGE_B_LOG.txt` exists, while any stage-B manifest is found under `30_DATA` (the depth-limited folder search, depth ≤ 3, stays as an extra check), while the run log holds a line from a role other than `entry:c1_e0`, `entry:c1_folds` and `entry:c1_freeze`, or while the run log's chain is broken. The stage-B log and the run log, not a folder search, are the record (Choices 42c, 44c).
- **When `--amend` is refused** (Choice 44c). In every case above, and also if the deposit record exists or any `30_DATA/av2_cache_stageB_*` folder exists. So deleting the deposit record does not reopen amendments once a method-stage, H8 or other outcome run has been logged. In practice an amendment is possible only between the freeze and the deposit record, before any non-exempt run.
- **The remaining limit** (Choices 44c, 48b m-4; stated again in section 8.8). Deleting or truncating the run log as well would still reopen `--amend` in code. What then remains is the second OSF registration and the deviation log.
- **Amendments** are logged in `40_PROTOCOL/C1_DEVIATION_LOG_v01.md` with their reason and appended to the hash log as an AMENDED line. The guard accepts only the **latest** line of the log, so an amendment replaces the plan; every output records the log's hash. The deposit record must name the latest line, and its registration time must be later than that line (section 8.3), so an amended plan needs its own registration.
- **Tests at the freeze.** The freeze runs the bound test (`test_c1_v12`, on README v09) with `C1_FREEZE_LOG_SHA256` set to the hash of the log it freezes into (`absent` for the first freeze), and writes the value into FROZEN_TESTS. The suite's `freeze_skip()` relaxes only the "hash log absent" assertion and the earlier suites' real-log groups; the suite always asserts that there is no deposit record, no stage-B log and no non-exempt run-log line (Choice 44c). The quarantine folder may exist, because it precedes the freeze. Run directly after the freeze, the suites fail their real-log checks by design; FROZEN_TESTS is the record, and it can be reproduced in a copy tree (README v07 m7).
- **The freeze also refuses** (Choices 44a, 48a, 48b): any of the ground-truth conditions of section 8.4; an AV2 stage-A manifest without `builder_sha256`, or one whose recorded `builder_sha256` is not a bound builder (R17c m8; R17f m-6); a `data:provenance` file that is not a success record for the README being bound (m-2); a missing `entry:c1_quarantine` or `entry:tpp_envcheck`; a config with a `q1` entry or without `h8_units` = `folds`; a bound test that does not print ALL_PASS; a generator that does not reproduce its target (checked on the archived originals where a Choice 36 edit was made); an entry point that is not the latest version; a child fold file that is not a restriction of the parent; an AV2 freeze without `data:scene_json` and `data:e0_plan`, or a scene map that does not give every fold unit its stage-A log; a plan already holding a FROZEN_ENV, FROZEN_ENV_TPP or FROZEN_TESTS block; or an open slot. The lead stops the freeze if a config entry is wrong (section 6.1).
- **A dry run first** (Choice 48c). After the quarantine and before the freeze, the lead runs `c1_freeze_v07 --dry-run` on the real tree, and lists the quarantine folder (names only) just before the freeze.
- **What it writes:** the five blocks, the `.sha256` sidecar, and one line in the canonical log.

### 8.3 External deposit before every AV2 outcome (Choices 40, 41b, 42a, 42f m2, 42h, 44f m2, 47j, 49h)

- **What is deposited.** After the freeze and before stage B, the researcher registers the frozen plan on OSF under embargo, on their own account, in the private project https://osf.io/eumj8/ (created 4 Nov 2026; `40_PROTOCOL/OSF_PROJECT_RECORD_v01.txt`). The upload folder `40_PROTOCOL/OSF_UPLOAD_C1_FROZEN/` holds: the frozen plan `C1_AV2_CONFIRMATORY_PREREG_vNN.md`; its `.sha256` sidecar; the C1 hash-log line; README v09 with the bound-file list and hashes; the folds, split and transfer-fit hash files; **a zip of every bound code file, the frozen config, the data-role files, the GT inventory and `30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt`** (Choices 46c, 47j); the criteria register v03; and a `SHA256SUMS.txt` over them. The text-locked draft is already in the project (header); the registration archives it, which makes its upload time tamper-evident (Choice 49h).
- **No Argoverse 2 data and no outcome is deposited.** The plan's counts and E⁰ values (S20a, S21) are outcome-free stage-A quantities; the GT inventory and the list file hold paths, producers, content classes, dates and hashes only.
- **How.** OSF's Open-Ended Registration template, with the frozen plan's sha256 and the sentence "Frozen pre-registration of the C1 Argoverse 2 confirmatory analysis; ground-truth stage B is built only after this registration." in the summary; embargo end beyond the expected publication (at most 4 years, endable early); a view-only link for IEEE Access made as soon as the registration is accepted. The guide is `40_PROTOCOL/OSF_DEPOSIT_GUIDE_v02.md`, which supersedes v01 (Choice 41b); every deposit refusal of the code names v02 (Choice 42h).
- **The record.** The lead then writes `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt` with the lines `frozen_plan_sha256: <64 hex>` (equal to the latest C1 line of the canonical log), `registration: <OSF registration URL or DOI>` and `registered_utc: <time OSF shows>`. It is written only after the registration exists, because its existence unlocks every AV2 outcome route.
- **How the record is validated** (the guard's `check_deposit`; Choices 42f m2, 44f m2):
  - duplicated keys are refused;
  - `registration` must match `https://osf.io/<id>/` or the OSF DOI form `10.17605/OSF.IO/<ID>` (upper case), and must **not** be the project recorded in `OSF_PROJECT_RECORD_v01.txt` (`eumj8`, as a URL or a DOI, in any case): the line names the registration, not the project;
  - `registered_utc` must be ISO 8601 UTC ending in `Z`, later than the plan's line in the hash log, no later than the time of the check, and earlier than every stage-B build in the stage-B log; the plan's hash-log line must carry a parsable time ("frozen" or "AMENDED", then `YYYY-MM-DD HH:MM:SS UTC`), otherwise the record is refused, not the check skipped;
  - `frozen_plan_sha256` must equal the latest C1 line.
- **Which routes wait for it** (Choice 42a; R17d B1). Under this plan on AV2, every entry point that reads ground truth after k, or a table built from it, refuses to run without the validated record: stage B, items, fits, runs, method stage (H6, H7), H8, predictor arm (H9) and analysis. Only `entry:c1_e0`, `entry:c1_folds` and `entry:c1_freeze` are exempt (section 1.5). Stage B checks the record after the guard and before reading any ground truth. Every runtime record and every table carries `deposit_record_sha256`; `check_table` and the analysis's run check require it to equal the current record. `c1_transfer_apply_v01` reads only the nuScenes transfer fit and the folds and computes no AV2 quantity (section 3.2); the runs that use its output are guarded.
- **After the results:** `C1_RUN_LOG.txt` and `C1_STAGE_B_LOG.txt` are uploaded to the same project (section 8.6).
- **In the paper:** the registration's identifier and time, the text-locked draft's upload time (tamper-evident once the registration archived it), and that stage B and every table were made after the registration, as the stage-B log and the run log show. If OSF cannot take the registration (for example after 19 Feb 2027), the route goes back to the researcher (Choice 41f).

### 8.4 Ground truth: one prepared file, Rule 0 metrics, the GT inventory and the quarantine (Choices 42b, 44a, 44f m5, 45b, 46c, 46f, 47b, 48a, 49b, 49d, 49e)

- **One prepared file** (Choice 44f m5). `av2_gt_prep_v02 --logs-file 30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` writes one prepared ground-truth file covering exactly the 375 fold units, `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json`, before stage A (Choice 46b). Every 375-log stage-A manifest names it (with its SHA-256), and E⁰, the quarantine, stage B, the method stage and H8 use it.
- **Rule 0 metrics after the text lock** (Choice 49e). The tracker metrics (HOTA, AMOTA, MOTA, IDS) on the 375 logs are computed after the text lock and before the quarantine; when they were computed, and who read them, is recorded at the freeze (header). The detector AP (S20b) was seen before the lock (section 1.2). They are tracker and detector metrics only, never a C1 outcome. After the quarantine, no step reads plain ground truth.
- **What counts as a ground-truth file: a content rule** (Choice 49b; R20 N3 and its open point 1). A file is a ground-truth file if it holds any per-object AV2 annotation position, box, size, yaw or velocity at any frame, of any AV2 log, training logs included. That includes quantities derived per object from these (such as QCNet's per-item `p0`, per-object errors, matched-pair distances, per-object ground-truth speeds, interpolated positions) and members of archives (tar, zip, npz, pkl, feather, parquet). It does **not** include identity-only data (track ids, existence and point counts at a frame, visibility flags: the stage-A caches, the K8 count items, the QCNet join keys `join2hz_t{1,3}_v01_keys.npz`), ego poses (they come from `city_SE3_egovehicle.feather`, not from annotations), or purely aggregate files without per-object rows (AP, metric and count tables).
- **The GT inventory** (Choices 47b, 49b). `40_PROTOCOL/C1_GT_INVENTORY_v01.json` records, for each candidate file, its path, producer, date, SHA-256, **content class**, and the producing code line (file and line) that decides the class. Producers only find candidates; the content rule decides. The code author traces every producer in the code [[V09: the inventory builder's final name]], and R17g checks it independently, by finding every tool that reads `annotations.feather` or a prepared file, and every file they wrote. No file is opened to decide. Among the ground-truth files:
  - the prepared files: `30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json` (9642db5b…) and `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json`, and every other file in any `30_DATA/**/gt/` folder;
  - the detection-evaluation ground-truth feathers: `30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_gt_v01.feather`, `30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_gt_v01.feather` (a9d85a54…) and `30_DATA/av2_det_owncp_v01/held225/av2held225_owncp_centerpoint_gt_v01.feather` (8cb86154…);
  - **the two QCNet ground-truth-history files:** `30_DATA/qcnet_av2_v01/qcnet_av2_gt_v01.npz` and `30_DATA/qcnet_av2_v02/qcnet_av2_gt_recentred_v02.npz` (QCNet on ground-truth histories, 2 Nov). Each item stores the annotation centre at its origin, and origins are every 2 Hz frame, so together they hold positions after k for the 150 validation logs (R20 B2; the lead read the producing code, not the files);
  - **the own detector's infos archive** `30_DATA/av2_det_owncp_v01/train_progress/infos_archive_v01b.tar` (2,838,906,880 B, Choice 50j; SHA-256 [[V09: ada2146d…, only if the code author's inventory confirms it]]), if its member names (listed by the code author and again by R17g; names only) show the held-out or validation infos, which carry per-object boxes; and any other infos pickle of the 375 logs, anywhere in the workspace;
  - every file listed in the port's `30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt`.

  The inventory lists identity-only and aggregate candidates too, with their class and code line, so that R17g can check each exclusion. It is expanded into `--extra` arguments, one per ground-truth file, bound as `data:gt_inventory`, and uploaded. The port's list file holds only paths and hashes; it is not quarantined, and it is uploaded (Choice 46c).
- **Large archives** (Choice 49b). An archive that holds ground-truth members is quarantined whole, as one verified gzip member, and is never unpacked in the workspace.
- **What is quarantined** (`c1_quarantine_v02`). The union of: **each AV2 stage-A manifest's ground-truth file**, for the manifests passed to it (the 375-log ones) and for **every** AV2 stage-A `MANIFEST.json` under `30_DATA` (to 4 folder levels), the five 150-log manifests in `30_DATA/av2_cache_stageA_v01/` included; and every ground-truth file of the GT inventory, passed with `--extra` and recorded in the quarantine manifest as kind `extra`, with its path, hash and size (Choice 49d restores this wording: the quarantine takes each manifest's ground-truth file, not every file a manifest names).
- **How.** The lead runs it with `--dry-run` first, then without. For every recorded hash, the tool hashes every workspace file of the same size, skipping `50_CODE/env/`, the quarantine folder and folders whose names contain a banned word, and treats every match alike: one gzip member in `30_DATA/av2_gt_quarantine_v01/`, verified to decompress to the recorded bytes, and only then every plain copy removed. Two files with the same bytes under different names are both quarantined (Choice 46f: the own detector's validation feather equals the public run's, a9d85a54…). It writes `QUARANTINE_MANIFEST.json`. The bytes are always kept. It computes nothing.
- **Copies outside the workspace** (Choice 49b). Just before the quarantine, the lead runs a size-filtered hash scan, for the recorded ground-truth hashes, of `Downloads` (excluding `ProgrammeA_RESUME_20261030_v01`) and of this session's temporary folders. Any match is moved into the workspace and passed on `--extra`, so that the quarantine records and compresses it; nothing is deleted. The result is recorded at the freeze (header). OneDrive and the other agent's folders are not scanned.
- **The freeze's check** (`c1_freeze_v07`; Choice 48a). Its hash set is the union of every quarantine member's recorded decompressed hash (from `QUARANTINE_MANIFEST.json`, of every kind), every GT-inventory hash, and the ground-truth hashes of the stage-A manifests it finds. It refuses:
  - a plain file at a recorded path, a plain `--extra` file, or an `--extra` file not recorded in the quarantine manifest;
  - a recorded hash without a member;
  - any plain file in the workspace whose SHA-256 is in the hash set, outside the skipped folders;
  - **any file in the quarantine folder that is not a recorded member or the manifest itself**, so a plain or extracted copy beside the members refuses;
  - **a recorded stage-A member whose manifest is no longer at its recorded path**, so moving a manifest no longer opens a route.

  **The skipped folders** are `50_CODE/env/` and folders whose names contain a banned word; the freeze lists them by name in its output (R17f m-3). The banned-word skip stays, because the standing rule forbids opening such folders; its limit is stated in section 8.8. **A second line of defence:** every stage-A manifest stays in place until stage B, and the lead lists the quarantine folder (names only) just before the freeze (section 8.2).
- **Reading after the quarantine.** Stage B v06 reads ground truth only from a quarantine member, after the deposit check, and verifies the decompressed SHA-256 against the stage-A manifest. `c1_h8_v06`, `c1_mstage_v06` and the analysis's E⁰ recompute do the same, through a temporary file outside the workspace that is removed afterwards. The guard sweeps stale temporary folders (`c1_gt_<pid>_*` whose process has ended, or pid-less ones older than 10 minutes) at guard time (Choice 44f m7).
- **Outside the quarantine** (section 11.3). The public `annotations.feather` files of all 375 logs (`30_DATA/av2_val/`, `30_DATA/av2_train225/`); copies outside this workspace that the scan above does not reach (pods and their volumes, OneDrive, other machines), which section 10 records; and a ground truth rebuilt after the quarantine from the public annotations by an AV2 data tool, or a member decompressed by hand.
- **What it closes.** The one-command route of R17d's probe P2b between the freeze and the deposit, also for prepared files named only by the older 150-log manifests (R17e M-A), for the QCNet ground-truth-history files (R20 B2), for a plain copy beside a quarantine member and for a moved manifest (R17f M-1).

### 8.5 Order of operations (AV2; environments named per step; `../env/<env>/Scripts/python.exe -B`, from `50_CODE/c1_av2` for the C1 tools)

**The port** (README v09; port design v04 section 8). Steps 1 to 8 may run before the text lock; they are builders and compute nothing on outcomes.
1. **Fetch** (canmot310, `-I`): `av2_fetch_v05` for the 225 held-out train logs into `30_DATA/av2_train225/` (no lidar contents; sweep lists from the recorded bucket listing through `av2_common_v02`).
2. **Log list** (canmot310): `av2_c1_logs_v01` writes `30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` and its `.sha256` (`data:logs375`).
3. **Frame check** (canmot310): `av2_c1_frame_check_v01`: every log's listing-derived frame times equal the own detector's frames (7,232 held-out, 4,806 validation); a mismatch stops the port (Choice 46a).
4. **Tracker input** (canmot310): `av2_tracker_input_v02 --detector owncp --logs-file …`.
5. **Prepared ground truth** (canmot310): `av2_gt_prep_v02 --logs-file 30_DATA/av2_trk_v02/C1_LOGS_375_v01.json`, writing `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json` (if it is not yet built at the lock, it is built after it).
6. **Tracking:** T1 and T3 with `av2_track_v02 --detector owncp` (canmot310; `paper/local/canmot/sc` and `paper/baseline/poly_mot`, nuScenes parameters); AB3DMOT with `av2_ab3dmot_v05 --detector owncp` (**ab3dmot310**, LT3D's defaults).
7. **Ego** (canmot310): `av2_ego_prep_v02 --gt 30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json`.
8. **2 s propagation** (canmot310): `av2_horizon_prep_v02 --propagate-only --allow-av2-propagation` for T1 and T3 (Choice 13); AB3DMOT's own horizon files, merged in worker order.

**The text lock** (header; Choices 47i, 49a), before step 9 and before the first 375-log stage-A build.

**After the lock, to the freeze:**

9. **Rule 0 metrics** (**av2eval310**; unbound, outcome-free): `av2_track_metrics_v04` and `av2_hota_v04` on the 375 logs, written to `60_RESULTS/av2_trk/c1_375/metrics/` and `hota/` (`data:rule0_metrics`). Their time and readers are recorded (Choice 49e).
10. **Stage A** (canmot310): `av2_cache_stageA_v02` for the 375 logs, T1, T3 and AB3DMOT; each manifest names the one prepared file.
11. **Counts:** S20a with `k8_items_v04 --av2 --counts-only` and `av2_counts_v02` (`data:s20a`), with the descriptive outputs of section 7 that need no outcome; then S22 with `c1_power_counts_v05`, its hash recorded before it runs (`data:s22`; reported only).
12. **Folds:** `c1_folds_v03 --dataset av2 --split … --val …`, then `--restrict-from` for `val` (`folds_val150`) and for `held_out_train` (`folds_train225`).
13. **E⁰ before the quarantine:** `c1_e0_v05 --mode c1 --seed 20261114 --stageA-manifests …` (its `H8_E0_primary` fills S21; its `inputs_sha256` goes into the config as `e0.inputs_sha256`).
14. **Scene map:** `c1_av2_scene_map_v01 --stageA-manifests <the 375-log manifests> --out <meta>/scene.json` (`data:scene_json`).
15. **Provenance:** `c1_av2_provenance_v01` on every 375-log stage-A manifest (`data:provenance`, written only on success); a failure stops the freeze (Choice 46d).
16. **GT inventory:** `40_PROTOCOL/C1_GT_INVENTORY_v01.json` (`data:gt_inventory`), by the content rule of section 8.4, checked by R17g.
17. **Off-workspace scan:** the size-filtered hash scan of `Downloads` (excluding `ProgrammeA_RESUME_20261030_v01`) and of this session's temporary folders; any match moved into the workspace and added to `--extra` (section 8.4).
18. **Quarantine** (canmot310): `c1_quarantine_v02 --stageA-manifests <every AV2 stage-A manifest> --extra <every ground-truth file of the GT inventory, one argument each> --dry-run`, then the same command without `--dry-run`.
19. **Freeze dry run and listing** (Choice 48c): `c1_freeze_v07 --dry-run` with the arguments of step 20, on the real tree; then the lead lists the quarantine folder (names only).
20. **Freeze:** `c1_freeze_v07 … --folds-val150 … --folds-train225 … --extra <the same list> --data scene_json=… e0_plan=… s20a=… s22=… logs375=… gt_inventory=… rule0_metrics=… provenance=… port_equiv=… <the stage-A manifests of section 8.1> …`. The lead first checks the config (section 6.1). The freeze runs `test_c1_v12` and writes the five blocks.

**After the freeze:**

21. **External deposit** (Choice 40): the researcher registers on OSF, embargoed, and uploads the folder of section 8.3; then the lead writes `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt` (guide v02), whose `registration` is the registration, not the project `eumj8`.
22. **Stage B** (canmot310): `av2_cache_stageB_v06 --stage-a … --gt 30_DATA/av2_gt_quarantine_v01/<member>.gz --frozen-plan … --tag <tracker>`, writing only `30_DATA/av2_cache_stageB_<tag>/` and one line of the stage-B log.
23. **Items:** `k8_items_v08 --av2-stageB --plan`.
24. **Fits and runs:** `c1_fit_v06` (within on `folds`; within on `folds_val150`; source), `c1_transfer_apply_v01`, `c1_run_v06` (the four routes, plus `tab`).
25. **Method stage:** `c1_mstage_v06 --av2-gt <member>.gz --av2-meta <meta> --folds …`.
26. **H8:** `c1_h8_v06 --gt <member>.gz --meta <meta> --folds …` (exactly the `folds` units).
27. **Trajectron++, on the laptop** (Choice 45a):
    - first the dry-record checks: `c1_tpp_envcheck_v01 --python ../env/canmot310/Scripts/python.exe --kind tpp_keys --plan <plan>`, then `--python ../env/tpp38/Scripts/python.exe --kind tpp_run --plan <plan>`;
    - then `tpp_keys_v03` under **canmot310** on the 375-log stage-B cache (wrapper record compared with FROZEN_ENV), and `tpp_run_v03` under **tpp38** for seeds 20261102, 20261104 and 20261105, and for the ground-truth run (wrapper records compared with FROZEN_ENV_TPP);
    - a pod is used only if its dry record passes first: on the pod, `python c1_tpp_envcheck_v01.py --write-dry dry.json`; then, on the laptop, `c1_tpp_envcheck_v01 --check dry.json --kind tpp_keys|tpp_run --plan <plan>`. The pod's keys310 environment fails this check and is not used for C1.
28. **Predictor arm:** `c1_predarm_v06` with all three seeds (H9 only; it refuses every QCNet option).
29. **Analysis:** `c1_analyse_v09 --c1 --plan` (Q1 is reported "not tested" with Choice 44(d)'s reasons).
30. **Upload** `C1_RUN_LOG.txt` and `C1_STAGE_B_LOG.txt` to the OSF project with the results.

None of these takes `--hash-log` on AV2, and no AV2 output is ever overwritten. The run log can be verified at any time with `python -B -c "import c1_guard_v05 as G; print(len(G.read_run_log()[0]))"` [[V09: the guard module to import, if `c1_guard_v06` is bound]]. **Descriptive and outside this order:** the planner sensitivities of Choice 50(g), on nuScenes development, after the lock-critical work (section 5).

### 8.6 The run log, the stage-B log and the tables of record (Choices 42c, 42g, 44f m1, 47h, 49f)

- **Run log** (`40_PROTOCOL/C1_RUN_LOG.txt`, append-only, chained). The guard writes a **"start"** line on AV2 before the entry point reads any ground truth or table, and `run_log_append()` writes the **"done"** line with the output hashes. Every line is one JSON object (UTC, entry point, plan hash, deposit-record hash, input hashes and, on "done", output paths and hashes) whose `prev_sha256` is the SHA-256 of the previous line's bytes (64 zeros for the first). Writes are binary and fsynced, under a lock file, after the whole chain is verified. It is written by stage B, items, fits, runs, method stage, H8, E⁰ under the plan, predictor arm and analysis.
- **The analysis checks it.** The analysis records the run log's hash, line count and last-line hash at start. It requires a "done" line with the file's SHA-256 for every table it consumes (method stage, H8, H9, descriptive H9) and every route's run record. A table without one is not provenance-valid; a run record without one is a route problem; a broken chain refuses the analysis.
- **Table of record** (Choice 47h; R20 P6). For every entry point and output role, the table of record is the output of the first run with a "done" line under the current deposit record. Every such table is passed to the analysis. A route is "not tested" only if it has no "done" line or its run raised; a table that exists but was not consumed is a deviation. **An output without a "done" line is never a table of record** (Choice 49f). The decision lists every "done" line and whether its output was consumed; the independent results review checks this against the uploaded run log. (The frozen config names each table's output path, and on AV2 an existing output is never overwritten, so a later run cannot take that path.)
- **A resumed run** (Choice 49f). After an environment stop (section 9), the run log shows a "start" line with no "done" line; the same frozen code resumes from its checkpoints and writes the "done" line. [[V09: how `c1_guard_v06` or the entry points treat an output left without a "done" line on resume; the planned rule renames it to `<name>.interrupted_<UTC>`, logs the rename, and requires the resumed run's output to equal it byte for byte where both exist]]
- **Stage-B log** (`40_PROTOCOL/C1_STAGE_B_LOG.txt`). Stage B v06 appends one line per build (UTC, plan hash, deposit-record hash, output hash), and writes only under the fixed folder `30_DATA/av2_cache_stageB_<tag>/`, never over an existing one; `--out` and a plain `--gt` are refused, and so is a second build with the same tag.
- **No overwrite.** On AV2 an existing output, or a final run record, is refused (`refuse_existing`); a rerun needs a new output name and is itself logged. Checkpoints and shards are kept, so a crashed run resumes rather than restarts; a refused or killed run leaves its "start" line without a "done" line.
- **Upload.** Both logs are uploaded to the OSF project with the results. They show that every stage-B build and every table came after the registration.
- **Limits.** The logs record runs of the C1 entry points only, so they are no protection against the programs the claim concedes (section 11.3). Before the guard, an entry point reads only unit names or dataset tags, to find the dataset. The chain shows a changed, deleted or unchained line inside the log, and a truncated last line; it cannot show a log deleted, or truncated cleanly after a complete line, and hand-written lines with a recomputed chain pass. Re-running the frozen analysis on the frozen inputs reproduces every table; that shows the reported tables are the frozen analysis's, not that no other analysis was run.

### 8.7 How later artefacts are checked (Choices 24, 34, 36, 39, 40, 42, 44)

Everything made after the freeze is checked by provenance, not listed: each within-AV2 fit records its code, folds and plan hashes; each run record carries the plan, folds and deposit-record hashes and its folds role; the H6 to H9 tables carry their entry point, every loaded module's hash, the plan, the folds, the deposit record, their sorted unit list and its hash, and their inputs; every consumed table must have a "done" line in the run log; caches must be stage B under this plan, built by `entry:stageB` from a bound stage-A manifest and a quarantine member, with the deposit record's hash; items must chain to such caches through `entry:k8_items`; the method stage and H8 check the scene map unit by unit against the stage-A manifests. On AV2 no output is overwritten. The analysis refuses anything whose provenance does not match. Superseded entry points refuse real input (Choices 36, 39a) and fail the role checks. The whole path is rehearsed end to end on a mock frozen plan with nuScenes stand-in data (the final rehearsal on README v09 [[V09: its folder and status file]]; v08's were `70_TESTS/c1_v01/rehearsal150_v08/` and `C1_V08_TEST_STATUS.json`). The rehearsal has no run log, deposit or quarantine, because nuScenes is exempt; the AV2 paths (quarantine, run log, deposit, stage B, scene map, provenance) are tested in `test_c1_v12`'s copy tree on R17d's AV2-tagged stand-in, with R17c's probes P1 to P7, R17d's PB1 and P2b, R17e's E2, E3 and E7, R17f's N1 and N2, and R17g's provenance refusal as refusal tests. **The verdicts are stand-ins, not evidence.**

### 8.8 Limits of the binding (for the methods section)

- **Scope** (Choice 47d; section 11.3). The refusals are properties of the C1 entry points. Not technically barred are: the programs of the completed nuScenes studies (`x1_full_v02`, `x2_full_v02`, `m_run_v04`), bound by their own frozen plans and not edited (Choice 42b); the public AV2 annotation files of all 375 logs, which are on the analysis computer; the AV2 data tools, bound (`av2_gt_prep_v01`, `av2_gt_prep_v02`) and unbound (`av2_hota_v04`, `av2_track_metrics_v04`), which can rebuild a prepared ground-truth file from those annotations or read one; a quarantine member decompressed by hand; and copies outside the workspace.
- **Provenance records can be forged by hand.** They are JSON files written by bound entry points, and a hand-made table with correct fields, and hand-written run-log lines with a recomputed chain, would pass the checks. The pipeline refuses accidental and command-line bypasses; it does not prove the absence of deliberate forgery. The protections against that are external: the text-locked draft's OSF upload time, which the embargoed registration preserves when it archives the project's files at the freeze (Choice 49h); the registration itself before stage B; the run log and stage-B log uploaded with the results; and the independent results review, which re-derives the headline results from the raw arrays.
- **The quarantine depends on its order, its list and its scan.** The freeze's hash set holds the quarantine members' hashes, the GT inventory's hashes and the ground-truth hashes of the stage-A manifests it finds. A file made after the quarantine, one the inventory missed, or a modified copy is not found; hence the content rule and R17g's independent completeness check. The scan skips `50_CODE/env/` and folders whose names contain a banned word, which the standing rule forbids opening; a copy placed in such a folder would not be found, and the freeze lists those folders by name (R17f m-3). Copies outside the workspace are scanned only in `Downloads` (without `ProgrammeA_RESUME_20261030_v01`) and this session's temporary folders; the others are recorded in section 10.
- **The amendment rule's remaining limit** (Choices 44c, 48b m-4). Deleting or truncating the run log as well as deleting the deposit record would reopen `--amend` in code. What then remains is the second OSF registration and the deviation log.
- **The run log** records runs of the C1 entry points only; its chain cannot show a deleted log or a clean truncation after a complete line (section 8.6).
- **The temporary ground truth.** A pid-less `c1_gt_*` folder left by v07 code is swept only after 10 minutes, and a folder whose pid has been reused by a live process is kept. Such copies exist only after the deposit, so outcome-blindness is not affected.
- **The AV2 export and port builders are bound at their hashes.** The freeze compares each stage-A manifest's recorded `builder_sha256` with the bound builders, and refuses a missing or unbound one; the provenance check alone follows every stage-A input to a bound producer (Choices 46d, 48b m-2). No AV2 file was opened in writing the code or this plan.
- **The scene map is the identity on AV2.** `c1_av2_scene_map_v01` writes it from the bound stage-A manifests; the per-unit checks in the freeze, the method stage and H8 confirm the unit set and names, and nothing more (Choice 44f m4).
- **One keys file.** The predictor arm needs one Trajectron++ keys file whose units are exactly the 375 fold units.
- **Trajectron++ environments** (Choices 44e, 45a). The keys and runs execute on the laptop, under canmot310 and tpp38. A pod is used only if its dry record passes `c1_tpp_envcheck_v01 --check` against the frozen plan; otherwise, and on any mismatch at the predictor arm, H9 is "not tested".
- **Q1 is not tested** (Choice 44d; section 1.3). `c1_qcnet_summary_v01` is unbound; `c1_predarm_v05` is bound only as a module and is refused as an entry point by role. Any QCNet result is exploratory and labelled so.
- **Unguarded by design.** `c1_transfer_apply_v01` (section 3.2); `c1_tpp_envcheck_v01`, which is outcome-free; `c1_quarantine_v02`, which reads bytes only to hash and compress them; `c1_av2_scene_map_v01`, which reads only the stage-A manifests' units and logs; `c1_av2_provenance_v01` and the GT-inventory builder, which read manifests, receipts, code, names and hashes only; the Trajectron++ wrappers, which read no outcome (keys are geometry and tokens, checked against the ground truth only for consistency on a stage-B cache that already needs the deposit; runs use histories up to k); the data builders (the port's tools of README v09 and `av2_gt_prep_v01`); and the Rule-0 metric tools `av2_track_metrics_v04` and `av2_hota_v04`, which the claim concedes.
- **Superseded entry points.** Under this plan every entry point other than those of section 8.1 is refused by role, among them the v07-era `c1_h8_v05`, `c1_mstage_v05`, `c1_e0_v04`, `c1_fit_v05`, `c1_run_v05`, `c1_freeze_v05`, `c1_quarantine_v01` and `c1_qcnet_summary_v01` (superseded and unbound), `c1_freeze_v06` and `c1_analyse_v08` (superseded by v07 and v09 [[V09: confirm their status in README v09]]), and `c1_predarm_v05`, `c1_analyse_v07`, `av2_cache_stageB_v05` and `k8_items_v07`, which are bound only as modules or sources (R20 m1). The v04- to v06-era entry points (`c1_h8_v03`/`v04`, `c1_mstage_v03`/`v04`, `c1_e0_v02`/`v03`, `c1_predarm_v03`/`v04`, `c1_fit_v03`/`v04`, `c1_run_v03`/`v04`, `c1_analyse_v05`/`v06`, `av2_cache_stageB_v03`/`v04`, `k8_items_v05`/`v06`) are also refused on AV2 before the freeze for want of a plan hash log (`c1_e0_v03` runs before the freeze only on stage-A fields, outcome-free), as R17e checked (section 2, E5). The old freeze tools refuse the current README (Choice 34.7; R17e PB3 for README v07; R17f for README v08; R17g for README v09). The Choice 36 refusals in `c1_freeze_v01` and `c1_freeze_v02` still say "Use c1_freeze_v04", and `c1_analyse_v06 --standin` accepts an AV2 folds config but finds no AV2 run to analyse; these files are not edited again (Choice 44f m6). `c1_fit_v01` (not bound, no guard) and `c1_analyse_v04` (not bound, not edited) stay runnable, but neither gives a route to outcomes before the deposit or into the decision (README v07 m6).
- **Test reruns.** The bound suites can be rerun in the real tree after the freeze only by the freeze itself (README v07 m7).
- **Deadline.** The freeze and the registration must both happen before 19 Feb 2027, when OSF projects become read-only (Choice 41f).

---

## 9. Deviation policy and failure

- **After the freeze nothing in this file changes.** Between the freeze and the deposit record, and before any non-exempt run, the only route to a change is `c1_freeze_v07 --amend "<reason>"` (section 8.2), logged in `40_PROTOCOL/C1_DEVIATION_LOG_v01.md`, followed by a registration of the amended plan. `--amend` is refused once the deposit record, the stage-B log, a stage-B folder, or a run-log line from a non-exempt entry point exists (Choice 44c). After that, deviations are recorded in the same log with their reason, and the frozen analysis is reported beside any deviating one. (D19 is reserved for the GO decision report; Choice 38e.)
- **Verdict of record** (Choice 47h; R20 P5). The verdict is that of the first completed run of the frozen code under the deposit record.
- **Environment stop against exception** (Choice 49f; R20 N7).
  - An **environment stop** is a process that ends without a Python exception from the entry point: power loss, a killed process, an OS restart. The run log then shows a "start" line with no "done" line. The same frozen code resumes from its checkpoints and writes the "done" line (section 8.6). This is not a deviation.
  - An **exception** is an exception raised by the entry point. On an H1 input it is NO-GO (section 6.3), even if a fix exists later; on a secondary input it makes that claim "not tested".
  - An output without a "done" line is never a table of record.
- **Fixes.** A code fix after the deposit is a new versioned file outside the frozen binding; its output is a deviation, logged in `C1_DEVIATION_LOG_v01.md` and reported beside the verdict of record, never replacing it. Bound files are never edited.
- **Results review.** If the independent re-derivation disagrees with the frozen code on any claim, the frozen verdict stands; the discrepancy is diagnosed and reported, and a confirmed code error is published as an erratum showing both verdicts.
- **Never allowed:** re-running with other seeds, folds, thresholds, floors, levels, populations, comparator sets, detectors or logs; selecting among repeated runs of the same step (the table of record is fixed by section 8.6); selecting a detector checkpoint on the confirmation logs; promoting a secondary or descriptive result; demoting a failed primary; adding AV2 data after any outcome is seen; computing a QCNet outcome for the C1 report; letting a descriptive output (section 7) or a planner sensitivity change a frozen setting.
- **If H1 fails (NO-GO):** reported as NO-GO with H1's failed or missing conditions; a pre-specified diagnosis (M\* shown above δ in a cell, family or pooled cell; a floor; HK1c; a comparator in V_t not beaten; per tracker; within against transfer; by source; A13 fallback shares; A6 diagnostics; margins by stratum); no re-run; any method change is new work on new data. Wording: "not shown above δ, operability not shown" when Valid(M\*, t) holds on both trackers and part (ii) fails; "floor not met" when M\* is shown above δ nowhere but a floor fails; and HK1c named when it is the failed condition (section 7: on development it is the main route to a failure of a valid M\*).
- **After the run:** the independent results review (R21) re-derives H1 and the K8 tables with separate code, checks the tables of record against the uploaded run log (section 8.6), and reports the Monte Carlo sensitivity of section 6.1.

---

## 10. What was seen before the freeze (completed at the freeze)

1. **nuScenes:** every K6 output; the K7 and K8 development checks; the K8 840-scene exploratory analysis and its review R16; the M\*J and M\*Jx development runs; the frozen D17 Trajectron++ run and its review R19; the criteria audit's development checks (`60_RESULTS/c1_criteria_sensitivity_v01/` and `_v02/`; Choice 50) (development evidence).
2. **AV2, metrics and counts (Rule 0; R20 m17; Choice 49e):**
   - public-detector AP on the 150 validation logs, and the own detector's AP on the 150 validation and 225 held-out logs (S20b, section 1.2), **seen before the text lock**; disclosed, and it changed no rule;
   - AV2 tracker metrics (HOTA, AMOTA, MOTA, IDS) on the 150 validation logs, computed with ground truth at the same sweep. **HOTA used per-class score thresholds tuned on the validation ground truth** (tracker note v02 section 3), for evaluation only, never a C1 input;
   - **the tracker metrics on all 375 logs**, computed after the text lock and before the quarantine (section 8.5 step 9). When they were computed, and who read them, is recorded at the freeze (header);
   - counts v01 and v02 of the 150 validation logs. **These counts set the sample size** (D18 v03) and moved H9 to the 375 logs (Choice 23);
   - QCNet counts, integrity checks and ground-truth visibility counts, including its coverage of T1's and T3's 2 Hz records (section 1.3);
   - the own detector's training logs, pilot and integrity checks; S20a, S21 and S22 when filled.

   No stage-B data, and no QCNet outcome.
3. **AV2, files holding ground-truth positions** (their existence, paths, sizes, producers, dates and hashes only; their contents were read by code and never displayed to the analyst; all are in the GT inventory and quarantined before the freeze, section 8.4):

| File | Producer | Date |
|---|---|---|
| `30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json` (9642db5b…; named by the five 150-log stage-A manifests) | `av2_gt_prep_v01` | 1 Nov 2026 |
| `30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_gt_v01.feather` | the public detectors' export and AP job on pod u8amwctmaq26np (`SPEND_LOG_AV2_DET_v01.md`) | 1 Nov 2026 |
| `30_DATA/qcnet_av2_v01/qcnet_av2_gt_v01.npz` | `qcnet_av2_infer_v01.py` on pod j48im9254i0na5 | 2 Nov 2026 |
| `30_DATA/qcnet_av2_v02/qcnet_av2_gt_recentred_v02.npz` | `qcnet_av2_infer_v03.py`, run by `pod_qcnet2_master_v02.sh` on pod lq459c84r42q2k | 2 Nov 2026 |
| `30_DATA/av2_det_owncp_v01/train_progress/infos_archive_v01b.tar` (2,838,906,880 B; held-out and validation infos, if its member names show them) | the own-detector pod scripts (`50_CODE/owndet/pod/`) | 4 Nov 2026, 11:50 |
| `30_DATA/av2_det_owncp_v01/val150/av2val150_owncp_centerpoint_gt_v01.feather` (a9d85a54…) and `held225/av2held225_owncp_centerpoint_gt_v01.feather` (8cb86154…) | the own detector's export (`pod_owndet_export_v01.py`) on pod 8peoqsmqm9exjw | 5 Nov 2026 |
| `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json` | `av2_gt_prep_v02` (the port) | at its build, before stage A |
| every other ground-truth file of the GT inventory | as the inventory records | as recorded |

4. **Copies outside the workspace** (R20 m16; from the spend logs in `80_LOGS/runpod/`). **No RunPod network volume was ever used:** `runpod_claude_v03.ps1` creates only a pod volume, mounted at `/workspace`, which RunPod deletes with the pod (Choice 49, the lead's check). Pods that held AV2 annotation data, and when each was terminated (local time, EST):
   - detector inference, 1 Nov: apxubol79e8yoq (terminated 18:27:27; container disk only) and u8amwctmaq26np (terminated 20:39:04);
   - QCNet, 2 Nov: j48im9254i0na5 (05:53:33), lq459c84r42q2k (about 08:58) and twtoo6fyhfzxo8 (09:21:14);
   - own detector: 1nh5mu31ztk945 (2 Nov, 13:12:41), xbiqlg7n9x0iiy (stopped 2 Nov, terminated 4 Nov 10:20:29, volume lost), 78zv5c7fe7xrnx (4 Nov, about 11:46 to 11:51; the log has both times) and 8peoqsmqm9exjw (5 Nov, 06:22:38, after the held-out and validation logs were fetched);
   - **unverified:** whether kn87rysovakahr (4 Nov, terminated after 2.8 min, "nothing had run beyond setup") and 0hwfp53zh5a2as (4 Nov, rejected after about 1 min) received any AV2 data.

   The CPU pods of `SPEND_LOG_K8CPU_v01.md`, `SPEND_LOG_C1STANDIN_v01.md` and `SPEND_LOG_TPP_v01.md` ran nuScenes jobs. **On this computer outside the workspace,** the size-filtered hash scan of `Downloads` (without `ProgrammeA_RESUME_20261030_v01`) and of this session's temporary folders is run before the quarantine, and its result is recorded at the freeze (header; section 8.4). OneDrive, the other agent's folders and other machines are not scanned, and remain **unverified**.
5. **Code reviews and rehearsals:** R17, R17b to R17g, R20 and its re-checks of v07d and v07e on the C1 code and plan; the criteria audit; the rehearsals on nuScenes stand-in data (verdicts not evidence). **H1-P and H5:** whether the frozen code runs them, as the final rehearsal on README v09 shows [[V09: the final rehearsal's result, before the text lock]].
6. **The port's records** (Choice 49i): the in-place corrections of `av2_track_v02` and `av2_ab3dmot_v05` on 5 Nov at 07:07 EST (before any 375-log output and before Choice 46's acceptance rule), and `av2_hota_v04`'s equivalence at rtol 1e-12 (section 1.1).
7. **The provenance check:** its result and output hash (section 8.1; the provenance line).
8. **The OSF project** https://osf.io/eumj8/ exists, private (`OSF_PROJECT_RECORD_v01.txt`). Before the freeze it holds only the text-locked draft, uploaded by the researcher before the first 375-log stage-A build; no registration is made before the freeze.
9. **Not seen by anyone, to the author's knowledge:** any AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error. Attested and timestamped at the freeze. Every prepared ground-truth file and every file holding ground-truth positions that existed in the workspace before the freeze (item 3 and the GT inventory) was hashed and moved into a verified quarantine before the freeze; the embargoed OSF registration is made after the freeze and before any C1 step that reads ground truth after k; the run log and the stage-B log, uploaded with the results, show when each run of a C1 entry point computed an AV2 outcome.

---

## 11. Changes

### 11.1 Change table (v05 to v06: rows 1 to 17; v06 to v07a: rows 18 to 31; v07a to v07b: rows 32 to 47; v07b to v07c: rows 48 to 56; v07c to v07d: rows 57 to 88; v07d to v07e: rows 89 to 120)

| # | Change | Where | Source |
|---|---|---|---|
| 1 | H9's floor counts E2 cells only (≥ 6 power-qualified); the 3 HL cells each evaluable and unflagged, in one sup-t family over E2 + HL; the pooled cell counts each item once; S20c's rule changed the same way | sections 2, 6.3, 6.4; slot table | D16 v18 Choice 39b; R17c M3; README v06 M3 |
| 2 | v04 section 11.4's population statement for H9 explicitly corrected (PD on the K8 tracker-planner's constraints; the method-stage audit population serves H6 to H8 only); v05's provisional "6 to 7 cells" for H9 withdrawn | sections 1.4, 6.4, 7 | D16 Choice 35; R17c plan-text items |
| 3 | The vacuous V_t (V^J_t) case stated: FormB holds whenever Valid(M\*) holds; reported as "vacuous"; for family-S members no p-value, p = 1 | section 6.2 | R17c plan-text items; D16 Choice 25; README v05 (`c1_analyse_v03`) |
| 4 | R17 m8 re-checked: no "folds of 30" for M\*Jx, no E1-AV2 on 150 logs; every seed in section 6.1, now with AB3DMOT's tracker index and the three Trajectron++ seeds; the 150-log folds are child files with no new randomness | sections 3, 6.1 | `70_TESTS/R17_C1_CODE_REVIEW_v01.md` m8; Choice 38d |
| 5 | One freeze by `c1_freeze_v04`; amendments only by `--amend "<reason>"`, logged in `C1_DEVIATION_LOG_v01.md`, only before any stage-B manifest; guard v03 accepts the latest log line only; the freeze runs every bound test and writes FROZEN_ENV and FROZEN_TESTS | sections 8.1, 8.2, 9 | D16 v18 Choice 39c; R17c M1, m4, m5; README v06 M1 |
| 6 | External deposit: embargoed OSF registration (Open-Ended template, sha256 in the summary) after the freeze and before stage B; the deposit record and its three fields; stage B v04 refuses without it; every later table chains it; what is and is not deposited; the OSF project https://osf.io/eumj8/ | sections 0 process items, 1.5, 8.3, 8.4, 10 | D16 v19 Choice 40; README v06 "Choice 40"; `OSF_DEPOSIT_GUIDE_v02.md`; `OSF_PROJECT_RECORD_v01.txt` |
| 7 | H9 seed robustness: all three seeds in one call; "seed-robust" label descriptive, outside family S, never changing H9 or GO | sections 2, 4, 6.1, 6.4, 6.5 | D16 v17 Choice 38b; README v06 "Choice 38" (b) |
| 8 | AB3DMOT (`tab`) as a descriptive third tracker on the 375 logs, outside H1 and family S (was "not run" in v05) | sections 1.1, 2, 3.1, 4, 6.1, 6.5 | Choice 38c; README v06 (c) |
| 9 | The 150-log routes: child folds `folds_val150` and `folds_train225` (seed 20261112, no new randomness), the `source` fit route, and the folds role per route; H1-P and H5 "not tested" if the frozen code cannot run them | sections 1.3, 3.1 | Choice 38d; README v06 (d) |
| 10 | Entry points and data roles from README v06; the freeze writes all four blocks | section 8.1 | README v06 "Entry points"; `c1_freeze_v04` source |
| 11 | Order of operations from README v06, with the deposit step | section 8.4 | README v06 "Commands" |
| 12 | Choice 39d's implementation rules stated (any exception on a secondary input: "not tested"; on an H1 input: NO-GO; unit lists; primary H9 seed; `--scenes` refused; E⁰ seed asserted) | sections 6.1, 6.3 | D16 v18 Choice 39d; README v06 M2, M4, m2 |
| 13 | Superseded entry points cannot compute AV2 outcomes (archived originals; `main()`-only edits) | sections 1.5, 8.5, 8.6 | Choices 36, 39a; README v06 B1 |
| 14 | Limits re-worded from README v06 (forged records and the external deposit; builder check at the freeze; one keys file; v05-era entry points); the `scene.json` limit dropped, as README v06 no longer lists it | section 8.6 | README v06 "Limits and open points" |
| 15 | Stand-ins stated as not evidence | sections 0, 8.5 | README v06 "Rehearsal stand-in" |
| 16 | Deviation log renamed `C1_DEVIATION_LOG_v01.md`; D19 reserved; frozen copy named without "DRAFT" | header, section 9 | Choice 38e |
| 17 | The five slots kept unfilled, in the same bracketed form as v05 (matched by the guard's slot regex); slot-table cross-references corrected (sections 1.2, 1.6) | slot table | `c1_guard_v03.SLOT`; `c1_freeze_v04` |
| 18 | (v07a) Q1 (QCNet): descriptive route `c1_predarm_v05 --q1-only` on folds role `folds_val150`, keys chained to the 150-log stage-B cache, QCNet files chained to `c1_qcnet_summary_v01` summaries (`not_predicted` = 0), read from the config's `q1` entry into its own block; "not tested" if the route is not checked before the freeze or its inputs fail; never changes GO, H9 or family S | sections 1.3, 2, 3.1, 3.2, 4, 6.1, 6.3, 6.5, 8.5, 8.8 | Choices 41c, 42e, 42f m5; README v07 M3, m5 |
| 19 | (v07a) `scene.json` bound as `data:scene_json`, checked per unit by the method stage and H8 against the stage-A manifests; its hash recorded by `av2_cache_stageA_v02`; v06's dropped limit restored and closed | header slot table, sections 1.4, 8.1, 8.2, 8.7, 8.8 | Choices 41d, 42f m3; README v07 m3 |
| 20 | (v07a) Every AV2 outcome route waits for the validated deposit record (stage B, items, fits, runs, method stage, H8, predictor arm, Q1, analysis); only `entry:c1_e0`, `entry:c1_folds` and `entry:c1_freeze` exempt; `deposit_record_sha256` in every record and table; `--amend` refused once the record exists; the deposit order for H6 to H8 stated in section 11.3 | sections 1.5, 6.3, 8.2, 8.3, 11.3 | Choice 42a; R17d B1 and plan-text item; README v07 B1 |
| 21 | (v07a) The outcome-blindness statement narrowed: Choice 42b's claim quoted verbatim in section 11.3, with the rule on the words "outcome-blind boundary enforced by code"; section 1.5 rewritten as what the C1 entry points refuse, with its scope; "Enforced by code" headings removed | sections 1.5, 2 (not claimed), 6.6, 8.8, 11.3 | Choice 42b; R17d B2 and plan-text item; README v07 "The narrowed claim" |
| 22 | (v07a) Ground-truth quarantine (`c1_quarantine_v01`) after stage A, the folds and E⁰, before the freeze; the freeze refuses while plain prepared ground truth exists; stage B, H8, method stage and the E⁰ recompute read quarantine members; E⁰ moved before the quarantine | header process items, slot table (S21), sections 1.5, 6.3, 8.4, 8.5, 10 | Choice 42b; README v07 B2 and command order |
| 23 | (v07a) One freeze with the stage-B log: stage B writes only the fixed folder `30_DATA/av2_cache_stageB_<tag>/` and appends to `C1_STAGE_B_LOG.txt`; the freeze and `--amend` are refused once that log exists; tests run with `C1_FREEZE_LOG_SHA256`; an amended plan needs its own registration | sections 8.2, 8.6, 9 | Choice 42c; README v07 M1, m7 |
| 24 | (v07a) H8 on exactly the `folds` units (375 logs, T1), not a subset; the config's `h8_units` is `folds` | sections 2, 3.1, 6.3 | Choice 42d; R17d M2; README v07 M2 |
| 25 | (v07a) H9's stricter flag rule: E2 cells flagged against the E2-only sup-t family, HL cells against the joint family, stated as an amendment to Choice 39b in the stricter direction; the S20c rule unchanged (counts power-qualified E2 cells); replaces row 1's single shared family for the E2 cells | sections 2, 6.3, 6.4, 7; slot table (S20c) | Choice 42f m1; R17d m1 and plan-text item; README v07 m1 |
| 26 | (v07a) The deposit record's validation stated (duplicated keys, registration pattern, `registered_utc` ordering) | section 8.3 | Choice 42f m2; README v07 m2 |
| 27 | (v07a) FROZEN_ENV_TPP: the `tpp38` versions recorded by `tpp_keys_v03` and `tpp_run_v03`, written by the freeze, compared by the predictor arm; H9 and Q1 in separate tables and blocks | sections 1.5, 6.4, 8.1 | Choice 42f m4, m5; README v07 m4, m5 |
| 28 | (v07a) Append-only run log `C1_RUN_LOG.txt` and stage-B log, both uploaded to OSF with the results; no AV2 output overwritten; reruns visible | sections 0, 8.6, 9, 10 | Choice 42g; R17d section 5 item 4; README v07 (g) |
| 29 | (v07a) Deposit guide named as `OSF_DEPOSIT_GUIDE_v02.md` (supersedes v01; code v07's refusals name v02) | section 8.3 | Choices 41b, 42h; README v07 (h) |
| 30 | (v07a) Every code name updated to README v07 (`c1_freeze_v05`, `c1_guard_v04`, `c1_analyse_v07`, the v05 entry points, `c1_e0_v04`, `av2_cache_stageB_v05`, `k8_items_v07`, `tpp_keys_v03`, `tpp_run_v03`, `c1_quarantine_v01`, `c1_qcnet_summary_v01`, `test_c1_v10`, 145 bound files); section 8 restructured (8.4 quarantine, 8.5 README v07's 16-step command order, 8.6 logs, 8.7 checks, 8.8 limits); rows 1 to 17 keep v06's names as the record of v06 | header, sections 1 to 10 | README v07 "Command order", "Entry points"; D16 v21 Choice 42i |
| 31 | (v07a) Frozen blocks: only the empty FROZEN_HASHES and FROZEN_ROLES blocks are drafted; `c1_freeze_v05` inserts FROZEN_ENV, FROZEN_ENV_TPP and FROZEN_TESTS and refuses a plan already holding any of them; the five slots and their regex are unchanged. Checked by a text-level replication of the freeze's block transform on a copy of this draft | section 8.1; "Frozen files" | Choice 41a; `c1_freeze_v05` source |
| 32 | (v07b) The narrowed claim reworded: "made before the confirmatory ground truth was built" was false (the prepared ground truth exists since 1 Nov, and the 375-unit file is built at stage A); the new text, verbatim in section 11.3, states that the files were built and hashed at stage A and quarantined at the freeze, that the registration came after that and before stage B, that the run log covers C1 entry points only, and that determinism answers "was the analysis run more than once"; sections 0, 1.5, 8.8 and 10 follow it | sections 0, 1.5, 8.6, 8.8, 10, 11.3 | Choice 44b; R17e M-B, items 1 and 14 |
| 33 | (v07b) Quarantine and freeze cover every prepared ground-truth file: the union of the given manifests, every AV2 stage-A manifest under `30_DATA` (the five 150-log ones included) and an extra list starting with the detection-evaluation `.feather`; a workspace hash scan at the freeze; Rule 0 metrics computed before the quarantine; what stays outside stated | header process items, slot table (S20b), sections 1.2, 1.5, 8.2, 8.4, 8.5, 8.8 | Choice 44a; R17e M-A, item 2 |
| 34 | (v07b) `--amend` refused also when a stage-B folder exists or the run log holds a non-exempt line; test v11's `freeze_skip()` keeps its other assertions; the remaining limit (deleting the run log too) stated | sections 8.2, 8.8, 9 | Choice 44c; R17e M-C, items 8 and 13 |
| 35 | (v07b) Q1 (QCNet) "not tested" in C1, decided now, with its two reasons; no `q1` config entry; no QCNet outcome for the C1 report; Q1 rows removed from seeds and routes; supersedes row 18 and Choice 43(a)'s route | sections 1.3, 2, 3.1, 3.2, 4, 6.1, 6.3, 6.4, 6.5, 8.1, 8.3, 8.5, 8.8, 9, 10 | Choice 44d (amends 43a, 43d); R17e M-D, item 3 |
| 36 | (v07b) Trajectron++ environments: keys under canmot310, compared with FROZEN_ENV; runs under tpp38, compared with FROZEN_ENV_TPP; the command order names each step's environment; supersedes row 27's single comparison | sections 1.5, 6.4, 8.1, 8.5, 8.8 | Choice 44e; R17e M-E, item 5 |
| 37 | (v07b) Run log with chained "start" and "done" lines; the analysis records its hash and requires a "done" line for every consumed table; its limits stated | sections 0, 1.5, 6.3, 8.6, 8.7, 8.8 | Choice 44f m1; R17e m1, items 11 and 12 |
| 38 | (v07b) Deposit-record checks: the project id refused as a registration; an unparsable plan-line time refused; DOI in upper case and UTC with `Z` | section 8.3 | Choice 44f m2; R17e m2, item 9 |
| 39 | (v07b) Scene map built by the bound `c1_av2_scene_map_v01` and bound as `data:scene_json`; on AV2 it is the identity map, so the check confirms the unit set and names; replaces row 19's "recorded by stage A" for AV2 | sections 1.4, 8.1, 8.5, 8.8 | Choice 44f m4; R17e m4, item 10 |
| 40 | (v07b) One prepared ground-truth file for exactly the 375 fold units (`av2_gt_prep_v01 --logs <375>`), named by every 375-log stage-A manifest and used by E⁰, the quarantine, stage B, the method stage and H8 | sections 1.1, 6.3, 8.4, 8.5 | Choice 44f m5; R17e m5, item 6 |
| 41 | (v07b) H9's power family stated: power in the joint evaluable E2 + HL family, at least as strict as the E2-only family; floor counts power-qualified E2 cells; flags as in row 25 | sections 2, 6.3, 6.4; slot table (S20c) | Choice 43b; R17e item 4 |
| 42 | (v07b) `c1_transfer_apply_v01` stays unguarded, with the reason; the list of components unguarded by design | sections 3.2, 8.3, 8.8 | Choice 43c; R17e section 5, item 12 |
| 43 | (v07b) Frozen config entries checked at the freeze: `h8_units` = `folds`, no `q1`, `data:e0_plan`, `data:scene_json`; a missing or extra entry stops the freeze | header process items, section 8.1 | Choices 43d, 44d; R17e item 7 |
| 44 | (v07b) What was seen: tracker metrics on the 150 validation logs, the prepared ground-truth files' existence and hashes, QCNet's ground-truth visibility and coverage counts, and the corrected attestation wording | section 10 | R17e item 14; Choice 44b |
| 45 | (v07b) Code names moved to code v08 (`c1_freeze_v06`, `c1_quarantine_v02`, `c1_av2_scene_map_v01`, `c1_guard_v05`, `test_c1_v11`, `rehearsal150_v08`, `C1_V08_TEST_STATUS.json`), with README v07's names for the other entry points; command order of 19 steps; counts and flags marked "(README v08)" to be synced with README v08 | header, sections 0, 1.5, 3.1, 6.1, 8, 9 | D16 v23 Choice 44g; the lead's v08 name list; R17e items 7, 10, 11 |
| 46 | (v07b) Superseded entry points named (v04- to v06-era), refused before the freeze for want of a plan hash log and by role after it; older freeze tools refuse the current README; stale refusal messages stated, not edited | sections 1.5, 8.8 | R17e section 2, item 12; Choice 44f m6 |
| 47 | (v07b) Frozen blocks and slots unchanged: only the empty FROZEN_HASHES and FROZEN_ROLES blocks; the five slots and their regex. Checked again by a text-level replication of the freeze's block transform on a copy of this draft | section 8.1; "Frozen files" | Choice 41a; `c1_freeze_v05` source (v06 to be confirmed, README v08) |
| 48 | (v07c) README v08's names and counts everywhere outside rows 1 to 47: `c1_analyse_v08`, `c1_predarm_v06`, `c1_fit_v06`, `c1_run_v06`, `c1_mstage_v06`, `c1_h8_v06`, `c1_e0_v05`, `c1_freeze_v06`, `c1_quarantine_v02`, `av2_cache_stageB_v06`, `k8_items_v08`; the new `entry:tpp_envcheck` (`c1_tpp_envcheck_v01`); `entry:c1_qcnet_summary` removed, and section 1.3's sentence that it "stays bound" corrected; the freeze requires `entry:c1_quarantine` and `entry:tpp_envcheck`; `test_c1_v11`; 154 files by role; the guard's import chain; the config checks now made by the freeze; the "(README v08)" markers of v07b resolved | header, sections 1.3, 1.5, 3.1, 6.1, 6.4, 8.1, 8.2, 8.5, 8.7, 8.8, 11.3 | README v08 (5649c170…), "Entry points", "Command order", "Fixes" |
| 49 | (v07c) Trajectron++ keys (canmot310) and runs (tpp38) execute on the laptop; a pod is used only after `c1_tpp_envcheck_v01 --write-dry` on it and `--check` on the laptop pass; the pod's keys310 environment is not used; v07b's "(pod)" at the run step removed | sections 6.4, 8.1, 8.5, 8.8 | Choice 45a; README v08 M-E |
| 50 | (v07c) Every prepared ground-truth file goes on `--extra`: the public and the own detector's detection-evaluation feathers (`av2_det_owncp_v01/val150/`, `held225/`), every file in the port's list `30_DATA/av2_trk_v02/GT_FILES_FOR_QUARANTINE_v01.txt`, and any tracker-metrics file; the quarantine records them as kind `extra` | sections 1.2, 8.4, 8.5, 8.8, 10 | Choice 45b; README v08 M-A |
| 51 | (v07c) Q1's "not tested" is printed by `c1_analyse_v08` with Choice 44(d)'s two reasons, in its own block, not among the missing inputs; the analysis refuses a `q1` config, and `c1_predarm_v06` refuses every QCNet option | sections 1.3, 8.5, 8.8 | Choice 45c; README v08 M-D |
| 52 | (v07c) The AV2 port, new: the v01 builders read only `30_DATA/av2_val` and cannot read the 225 held-out train logs, and the laptop has too little disk for their lidar; new builders `av2_common_v02` (log-root resolver over `av2_val` and `av2_train225`; sweep list from the recorded bucket listing without local lidar), `av2_fetch_v05`, `av2_gt_prep_v02`, `av2_ego_prep_v02`, `av2_tracker_input_v02`, `av2_ab3dmot_v05`, `av2_track_v02`, each byte-identical with the v01 path on the 150 validation logs; bound by README v09 (builder-only); the freeze refuses an unbound stage-A builder; the ground truth is `av2_gt_prep_v02 --logs <the 375 fold units>` at `30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json`; final names and hashes confirmed by the lead at the last sync | header, sections 1.1, 8.4, 8.5, 8.8, 10 | the lead's port instruction (5 Nov 2026); README v09 pending |
| 53 | (v07c) Slot S20b filled: AP of the own detector on the 150 validation and 225 held-out logs beside the public checkpoint's; 57,838 iterations (2 CBGS epochs, projection $31.44 within $34); two segments joined by an exact resume at iteration 1,000; every frame has predictions; the bicyclist gap (0.403 against 0.543 on validation) disclosed; nothing selected on the 375 logs. The S20b marker and its slot-table row are removed; four slots remain (S20a, S20c, S21, S22) | slot table, sections 1.1, 1.2, 10 | `60_RESULTS/av2_det/AV2_OWN_DETECTOR_NOTE_v01.md` (4f014ae1…) |
| 54 | (v07c) Process items: code v08 verified; R17f running; README v09 pending; R20 next; then the data steps | header | the lead's status (5 Nov 2026) |
| 55 | (v07c) README v08's details stated: the "start" line written by `guard()`, the `prev_sha256` chain, lock and fsync, and the analysis's run-log checks; the freeze refuses any freeze while a non-exempt run-log line exists or the chain is broken; the quarantine's search depth and `extra` records; the temporary-folder sweep; the limits (hand-written chains, a clean cut, pid reuse); the rehearsal's scope and the copy-tree tests | sections 0, 8.2, 8.4, 8.6, 8.7, 8.8 | README v08 m1, M-A, M-C, m6, m7, "Limits" |
| 56 | (v07c) Frozen blocks and the four remaining slots: only the empty FROZEN_HASHES and FROZEN_ROLES blocks are drafted. Checked by replaying `c1_freeze_v06`'s block transform as text on a slot-filled copy of this draft | section 8.1; "Frozen files" | Choice 41a; `c1_freeze_v06` source (3fbcdff0…) |
| 57 | (v07d) README v09 binds the whole port as builders (`av2_common_v02`, `av2_fetch_v05`, `av2_c1_logs_v01`, `av2_c1_frame_check_v01`, `av2_gt_prep_v02`, `av2_ego_prep_v02`, `av2_tracker_input_v02`, `av2_track_v02`, `av2_ab3dmot_v05`, `av2_horizon_prep_v02`) and Choice 47's new tools; the Rule-0 tools named as unbound; FROZEN_TESTS is `test_c1_v12` on README v09; the port's equivalence records bound as `data:port_equiv`; R17g checks v09's delta before the freeze; README v09's hash and counts at the final sync | header, sections 1.1, 8.1, 8.2, 8.7 | Choice 47a; R20 B1, P11 |
| 58 | (v07d) Every port and C1 step names its environment (canmot310, ab3dmot310, av2eval310, tpp38); the order gains the log list, the frame check, the 2 s propagation, the provenance check and the GT inventory | section 8.5 | Choice 47a; R20 m2, P11 |
| 59 | (v07d) Choice 46 carried: the port's acceptance rule; the prepared ground truth before stage A; stage A stays `av2_cache_stageA_v02`; the port's list file expanded into `--extra`, not quarantined, uploaded; `c1_av2_provenance_v01` before the quarantine, bound as `data:provenance`, a failure stopping the freeze; identical-byte copies both quarantined | sections 1.1, 8.1, 8.3, 8.4, 8.5 | D16 v25 Choice 46 (a) to (f); R20 B1 |
| 60 | (v07d) The producer-based GT inventory `40_PROTOCOL/C1_GT_INVENTORY_v01.json` (path, producer, date, SHA-256), with the two QCNet ground-truth-history files named; it replaces "any file built for the tracker metrics"; expanded into `--extra`, bound as `data:gt_inventory`, uploaded, checked by R17g | sections 1.5, 8.1, 8.3, 8.4, 8.5, 8.8, 10 | Choice 47b; R20 B2, P10 |
| 61 | (v07d) S20c filled: H9's label fixed as secondary; the config states `h9_label` = "secondary", checked by the lead; the floor is condition (a), judged by the frozen predictor arm on the tested population; a marked placeholder for the floor-fail status wording (code v09); `S20c_label_from_counts` reported beside the fixed label; `data:s20c` dropped. Three slots remain | slot table, sections 1.6, 2, 6.1, 6.3, 6.4, 8.1 | Choice 47c (amends Choice 23 as to when the floor is judged); R20 B3 |
| 62 | (v07d) R20's P1 claim replaces Choice 44b's, verbatim in section 11.3; sections 0, 1.5, 8.6, 8.8 and 10 follow it (the "only step" phrase removed; the concessions completed; determinism worded as R20 gives it) | sections 0, 1.5, 8.6, 8.8, 10, 11.3 | Choice 47d; R20 M1, P1 |
| 63 | (v07d) ShownAbove loses the ¬HK1c term (stricter): a comparator failing only HK1c stays in V_t; M\*'s own HK1c unchanged; the asymmetry stated; the decision lists each comparator's exit condition; needs `c1_analyse_v09` | sections 2, 6.2 | Choice 47e; R20 M2, P13 (stricter branch) |
| 64 | (v07d) Section 0's "What the primary test adds" rewritten as R20's P2; M\*'s simultaneous one-sided 95 % cell upper bounds and their maximum reported, never gated; the paper's sentence; no equivalence claim, m = 5 | sections 0, 2, 6.2, 6.5, 6.6 | Choice 47f; R20 M3, P2 |
| 65 | (v07d) "What GO establishes" (P3: B3 and RETUNED = B0 comparisons are not evidence of operability; on T3 GO needs B6 shown above δ); multiplicity worded as P4 (the Bonferroni split kept as a deliberate, conservative choice; H9 an uncorrected no-flag claim) | sections 2, 6.5 | Choice 47g; R20 M4, P3, P4 |
| 66 | (v07d) The verdict of record, fixes and the results review (P5); the table of record (P6), with "not tested" only for a route with no "done" line or a raised run | sections 6.3, 8.6, 9 | Choice 47h; R20 M5, M6, P5, P6 |
| 67 | (v07d) The text lock (the researcher uploads the R20-checked draft to OSF before the first 375-log stage-A build; the allowed diff is the slot fills S20a, S21, S22, README v09's name, hash and counts, and the provenance line); S22 "reported only" with `c1_power_counts_v05`; the port-failure rule | header, slot table, sections 1.1, 7, 8.5, 10 | Choice 47i; R20 M7, P7 |
| 68 | (v07d) The frozen configuration printed (every key the analysis reads; no `q1`; `c` and `h9_label` stated); the data roles `data:s20a`, `data:s22`, `data:logs375`, `data:gt_inventory`, `data:rule0_metrics`, `data:provenance`, `data:port_equiv`; the stage-A manifests by role; the OSF upload's zip; "the lead checks these entries at the freeze" | sections 6.1, 8.1, 8.3, 8.5 | Choice 47j; R20 M8, P8 |
| 69 | (v07d) Inference stated as conditional on the fitted thresholds; the pre-registered seeds decide every status; R21's descriptive Monte Carlo sensitivity (20 alternative seed sets) | sections 6.1, 9 | Choice 47k; R20 M9, P9 |
| 70 | (v07d) A source table for the design choices, from R20's literature section; the two starred items verified on the web (Bao et al. is *Biometrika* 2024, not ICML 2024) | section 6.8 | Choice 47l; R20 M10 |
| 71 | (v07d) Files bound only as modules or sources (`c1_predarm_v05`, `c1_analyse_v07`, `av2_cache_stageB_v05`, `k8_items_v07`) no longer called unbound; "refused as an entry point by role" | sections 1.3, 8.1, 8.8 | Choice 47m; R20 m1 |
| 72 | (v07d) S20a's tools named: `k8_items_v04 --av2 --counts-only` and `av2_counts_v02`; H9's history-length counts moved to the predictor arm at analysis | slot table, section 1.6 | Choice 47m; R20 m3 |
| 73 | (v07d) Section 7's power figures stated to supersede D18 v03's | section 7 | Choice 47m; R20 m4 |
| 74 | (v07d) "Not corrected across populations or claims" (the sup-t family is simultaneous within a population); H9's error control stated | section 6.5 | Choice 47m; R20 m5, m18 |
| 75 | (v07d) GO's inputs enumerated (the eight arms, RETUNED's 21 points, on the within route for T1 and T3); a missing secondary or descriptive arm never changes GO | section 6.3 | Choice 47m; R20 m6 |
| 76 | (v07d) E⁰'s exemption reworded: outcome-free fields of a file that also holds later positions | section 1.5 | Choice 47m; R20 m7 |
| 77 | (v07d) M\*Jx's λ fold stated: g = (f + 1) mod 5, base on the other three folds | section 3.2 | Choice 47m; R20 m8; `c1_fit_v02` |
| 78 | (v07d) The detector assignment fixed by D18 v02 on 2 Nov before any AP; `iter_51000.pth` never evaluated | section 1.2 | Choice 47m; R20 m9 |
| 79 | (v07d) The fold share's ± stated as the hypergeometric standard deviation (0.051) | section 3.1 | Choice 47m; R20 m10 |
| 80 | (v07d) D17's S2 and trace sensitivities not run in C1; C1's H9 uses `int_ee` whatever arrives | sections 2, 4 | Choice 47m; R20 m11, m12 |
| 81 | (v07d) A family in which M\* has zero exceedance in every bootstrap draw is judged by Ê > δ and reported; it no longer raises (`c1_analyse_v09`) | section 6.1 | Choice 47m (m13); R20 m13 |
| 82 | (v07d) Why H4 and H7 use different transfer sources | section 3.2 | Choice 47m; R20 m14 |
| 83 | (v07d) QCNet's coverage given in R17e's definition, with note v01's other definition named | section 1.3 | Choice 47m; R20 m15 |
| 84 | (v07d) Pods that held AV2 annotation data, and their termination times, recorded from the spend logs; two pods marked unverified | section 10 | Choice 47m; R20 m16 |
| 85 | (v07d) Disclosures: HOTA's thresholds tuned on the validation ground truth; the 150-log counts set the sample size and moved H9; the tracker metrics on all 375 logs seen before the freeze | section 10 | Choice 47m; R20 m17 |
| 86 | (v07d) H1-P's and H5's runnability decided by the final rehearsal and stated in section 10; the source-heterogeneity check descriptive, changing no claim | sections 1.3, 2, 3.1, 10 | Choice 47m; R20 open choices 13 and 18 |
| 87 | (v07d) Code v09's planned names (`c1_analyse_v09`, `c1_av2_provenance_v01`, `c1_power_counts_v05`, `test_c1_v12`, the GT-inventory builder) and README v09's hash and counts marked "at the final sync"; section 8's header names README v09 | header, sections 1.1, 6.1, 8 | D16 v26 Choice 47(n); the lead's v09 name list |
| 88 | (v07d) Frozen blocks and the three remaining slots (S20a, S21, S22): only the empty FROZEN_HASHES and FROZEN_ROLES blocks are drafted. Checked by replaying `c1_freeze_v06`'s block transform as text on a slot-filled copy of this draft | section 8.1; "Frozen files" | Choice 41a; `c1_freeze_v06` source (3fbcdff0…) |
| 89 | (v07e) `c1_freeze_v07`: its hash set is the union of every quarantine member's recorded hash, every GT-inventory hash and the stage-A manifests' ground-truth hashes; it refuses any file in the quarantine folder that is not a recorded member or the manifest, and a recorded stage-A member whose manifest has moved; R17f's N1 and N2 as copy-tree refusal tests; every stage-A manifest stays in place until stage B | sections 1.5, 8.1, 8.2, 8.4, 8.7, 8.8 | Choice 48a; R17f M-1; R20 re-check N1 |
| 90 | (v07e) `c1_av2_provenance_v01` writes only on success, and the freeze refuses a `data:provenance` file that is not a success record for the README bound; the freeze checks only the stage-A manifests' own `builder_sha256`, and the upstream builders are covered by the provenance check alone | sections 8.1, 8.2, 8.5, 8.8 | Choice 48b m-2 |
| 91 | (v07e) The scan's skipped folders (`50_CODE/env/`, folders with a banned word in the name) are listed by name in the freeze's output, and the limit is stated | sections 8.1, 8.4, 8.8 | Choice 48b m-3 |
| 92 | (v07e) "Deleting or truncating the run log" replaces "deleting" in the amendment limit and the run-log limits | sections 8.2, 8.6, 8.8 | Choice 48b m-4 |
| 93 | (v07e) Q1 is never listed among the missing inputs, by `c1_analyse_v09` | sections 1.3, 6.3 | Choice 48b m-5 |
| 94 | (v07e) The freeze refuses an AV2 stage-A manifest without `builder_sha256` | sections 8.1, 8.2, 8.8 | Choice 48b m-6 |
| 95 | (v07e) A run-order step after the quarantine and before the freeze: `c1_freeze_v07 --dry-run` on the real tree; the lead lists the quarantine folder (names only) | sections 8.2, 8.5 | Choice 48c |
| 96 | (v07e) README v09 is final and R17g-checked before the lock, and its name, hash and counts are written into this draft; after the lock only S20a, S21, S22 and the provenance line may change, listed exhaustively; any later text or code change needs a D16 choice and disclosure; a lead note on where the freeze-time records of 49(b) and 49(e) go | header, section 8.1 | Choice 49a; R20 re-check N2, section 4 |
| 97 | (v07e) The GT boundary is a content rule (per-object annotation position, box, size, yaw or velocity at any frame of any AV2 log; derived per-object quantities and archive members included; identity-only data, ego poses and aggregate files excluded); producers only find candidates; the inventory records the content class and the deciding code line; `infos_archive_v01b.tar` named; archives quarantined whole; a size-filtered hash scan of `Downloads` and the session's temporary folders before the quarantine | sections 1.5, 8.4, 8.5, 8.8, 10 | Choice 49b; R20 re-check N3 and open point 1 |
| 98 | (v07e) H3's comparator set gets the stricter rule: imprecision never removes a comparator from V^J_t; M\*Jx's ValidJ unchanged | sections 2, 6.2, 6.3 | Choice 49c; R20 re-check N4 |
| 99 | (v07e) v07c's wording restored: the quarantine and the freeze take each stage-A manifest's ground-truth file, not every file it names | sections 1.5, 8.4, 11.3 | Choice 49d; R20 re-check N5 |
| 100 | (v07e) The Rule-0 tracker metrics move after the text lock (before the quarantine), with their time and readers recorded; the detector AP disclosed as seen before the lock, changing no rule | header, sections 1.2, 1.5, 8.4, 8.5, 10 | Choice 49e; R20 re-check N6 |
| 101 | (v07e) Environment stop against exception defined; an output without a "done" line is never a table of record; the resumed-run behaviour marked for code v09 | sections 6.3, 8.6, 9 | Choice 49f; R20 re-check N7 |
| 102 | (v07e) S22: `c1_power_counts_v05` uses R\* and the stricter comparator rules; its H9 projection leaves out history length and overstates H9's power; reported only | slot table, section 7 | Choice 49g; R20 re-check N8 |
| 103 | (v07e) The text-lock file's upload time becomes tamper-evident when the registration archives the project | header, sections 8.3, 8.8 | Choice 49h; R20 re-check N9 |
| 104 | (v07e) Disclosed: the port's in-place corrections of `av2_track_v02` and `av2_ab3dmot_v05` (5 Nov, 07:07 EST) and HOTA's equivalence at rtol 1e-12; port tools versioned from now on | sections 1.1, 10 | Choice 49i; R20 re-check N10 |
| 105 | (v07e) "`c` has a code default (0.03); `h9_label` has none in `c1_analyse_v09`; both are stated" | section 6.1 | Choice 49j; R20 re-check N11 |
| 106 | (v07e) A pointer to R20's novelty-risk list, carried to the manuscript stage | section 6.8 | Choice 49k; R20 re-check N12 |
| 107 | (v07e) H9's floor-fail wording: "does not hold: floor not met", with the `H9_floor` block, marked for confirmation against code v09 | section 6.4 | Choice 49l; R20 re-check section 3 |
| 108 | (v07e) Error levels follow one principle (ICH E9 section 5.5): against M\* at one-sided 0.05; for M\* at one-sided 0.025 (Form B at 0.025/\|V_t\|, H3's superiority at 0.025/\|V^J\|, Form C and H10's NI part at 0.975, H6b's and H10's cell parts at 0.975, Holm at 0.025, Form A at 0.025/4); HK1c the stated exception; the definitions written with their levels | sections 2, 6.2, 6.3, 6.5 | Choice 50a; register C2, C9b, C10, C11a |
| 109 | (v07e) A comparator leaves V_t only on familywise evidence: each of 9 removal conditions at 1 − 0.025/9 (V^J: 3 at 1 − 0.025/3); Form B's total error ≤ 0.05 at nominal levels, with the development actual error and removal rates | sections 6.2, 6.5 | Choice 50b; register C9c |
| 110 | (v07e) HK1c at L = 0.995 (and ValidJ's UB); the margin δ + 0.03 our own value with an approximate Beta-law derivation, not a theorem; the level rule with its timing (13:37 EST, before the check), its open reading (mean or per-cell minimum), the boundary-only reading and the power cost | sections 6.2, 6.5, 6.7, 7 | Choice 50c (as corrected in 50k, 50l); register C8 |
| 111 | (v07e) The power rule written in full with each value's basis: power ≥ 0.80 against 0.15 (anchored, with the selection caveat and the limits at 0.10 and 0.12), target-only planting with the others at δ, ρ = 0.5 (derived, with the moment-estimate and per-cell caveats), 2000 datasets (was 200), 500 weights, nested seeds | section 6.1 | Choice 50d; register C6a to C6f |
| 112 | (v07e) Values kept with their stated bases: F_MIN 6, PD ≥ 1, evaluable at ≥ 39 logs (own value from P01 Prop 6(ii)), B = 2000 (MC error of Form B), c = 0.03 at 0.975; H8's band stated as two-sided 95 % | sections 2, 6.1, 6.3 | Choice 50e; register C3b, C5, C7a, C7b, C10a, C12a |
| 113 | (v07e) New descriptive outputs: record coverage of each power family, families at F_MIN 4 and 8, per-cell power at P 0.10, 0.12 and 0.20 with MDE80, every zero-SE case and its effect on V_t, U_max and the cell UBs labelled approximate | sections 0, 2, 6.1, 7 | Choice 50f |
| 114 | (v07e) Planner sensitivities (buffer 0.25 and 1.0 m, a denser candidate set, range and horizon shares): descriptive, on nuScenes development after the lock-critical work, unable to change a frozen setting | header, sections 5, 8.5, 9 | Choice 50g; register C15c to C15e |
| 115 | (v07e) Development verdict under R\* stated (unchanged); section 7 replaced by the operating characteristics at 375 units under R\* (P(H1) 0.870 plug-in and 0.940 capped; P(H1 fails \| M\* valid) 0.060 against 0.020; families and record shares; the P = 0.12 limit); M\*'s T1 PD pooled UB given as 0.062 (the JSON value 0.0625) | sections 0, 6.2, 6.7, 7 | Choice 50h; final check v02, parts C and D |
| 116 | (v07e) Section 6.8 rebuilt with register v03 section 4's fixes (Dmitrienko and Tamhane in *Pharm. Stat.*; Schuirmann's role; Lindemann's per-step allocation; Vovk 2015 and Barber et al. as practice; Cameron, Gelbach and Miller's bootstrap-t; Donner and Klar for the design effect only; the origin of 39; Ding et al. as the nearest pooling scheme; Lee et al. as arXiv) and additions (ICH E9, E9(R1), E10; FDA 2016; Morris et al.; Andrews and Buchinsky; Senn and Bretz; Vovk 2012; Angelopoulos and Bates; Bradley; Ridout et al.; Benjamini and Yekutieli for removal; Cameron and Miller; Monti et al.; NIST FIPS 180-4; Loh 1987; Browne 1995; Turner, Prevost and Thompson 2004); the register cited by path and SHA-256 as the full basis table | section 6.8 | Choice 50i; register v03 section 4 |
| 117 | (v07e) A limits section in the paper's voice, from register v03 section 5 | section 6.9 | Choice 50i; register v03 section 5 |
| 118 | (v07e) The infos archive's size given as 2,838,906,880 B (erratum to Choice 49's figure) | sections 8.4, 10 | Choice 50j |
| 119 | (v07e) Every place that depends on code v09 marked `[[V09: …]]` (README v09's name, hash and counts; the guard version; tool names; config keys; the floor-fail wording; the resumed-run rule; the code author's development replay; the archive's hash; the final rehearsal) | header, sections 1.1, 1.5, 6.1, 6.2, 6.4, 8.1, 8.4, 8.5, 8.6, 8.7, 8.8, 10 | the lead's v07e instruction (5 Nov 2026) |
| 120 | (v07e) Frozen blocks and the three remaining slots (S20a, S21, S22): only the empty FROZEN_HASHES and FROZEN_ROLES blocks are drafted. Checked by replaying `c1_freeze_v06`'s block transform as text on a slot-filled copy of this draft (to be repeated on `c1_freeze_v07` when it is final) | section 8.1; "Frozen files" | Choice 41a; `c1_freeze_v06` source (3fbcdff0…) |

### 11.2 From v04 to v05 (kept for the record)

- **Consolidated:** v04's section 11 is folded into sections 1 to 8; nothing in this file is overridden by a later section.
- **Choice 33** replaces the GO text and Choice 31's E⁰ rule (section 6.3).
- **Choice 35** corrects v04 section 11.4: H9's population is PD on the K8 tracker-planner's constraints (section 6.4).
- **Choice 37** adds history-length strata to H9, the three history-length cells to its family, H9-noHL as descriptive, and Q1's noHL reason (sections 4, 6.4).
- **Choices 22 to 27, 34 and 36** are stated where they act (sections 1.5, 3, 6.1, 6.5, 8.3).
- **R17 m8, stale text removed or corrected:** v04 section 1.3's "folds of 30 logs" for M\*Jx (now 3 + 1 folds of 75, section 3.2); v04 section 3's E1-AV2 "of the 150 AV2 logs" (now 375, section 3.2); the seeds for route indices 3 (public LT3D) and 4 (source transfer), the loop seeds and the seed of the 150-log descriptive folds, now in section 6.1. Also removed: v04 section 6.1 to 6.7's 150-log power and scaling tables as the plan's power (kept in v04 and in the cited JSON files), the 150-log fold rule for the primary routes, H5 as secondary, and the claim that the power tools are bound.
- **R17 m5:** ValidJ requires an evaluable pooled joint population, as the code does (section 6.2).
- **README v05 items:** the FROZEN_ROLES entry points, the order of operations, the limits (section 8; replaced in v06 by README v06's, in v07a by README v07's, in v07b by code v08's as announced, in v07c by README v08's, and in v07d and v07e by README v09's).

### 11.3 The outcome-blindness claim, its scope, and the deposit order (Choices 42a, 47d; R17d, R17e and R20 plan-text items)

**The claim, as the plan and the paper state it** (R20 P1, verbatim, adopted by D16 v26 Choice 47(d); it replaces Choice 44(b)'s text):

> The C1 pipeline's entry points refuse to compute any AV2 outcome before the freeze, and any outcome after k before the external registration is recorded. Not technically barred were: the programs of the earlier nuScenes studies; the public AV2 annotation files of all 375 logs, which were on the analysis computer; the AV2 data tools, bound and unbound, which can rebuild a prepared ground-truth file from those annotations; and copies outside the workspace. Every prepared ground-truth file and every file holding ground-truth positions that existed in the workspace before the freeze (listed with producer and date in section 10) was hashed and moved into a verified quarantine before the freeze. The embargoed OSF registration was made after the freeze and before any C1 step that reads ground truth after k (stage B, the method stage, H8 and the E⁰ recompute). The run log records runs of the C1 entry points only, so it is no protection against the programs this claim concedes. Re-running the frozen analysis on the frozen inputs reproduces every table (fixed seeds, frozen configuration); this shows that the reported tables are the frozen analysis's, not that no other analysis was run.

**Wording rule.** The words "outcome-blind boundary enforced by code" are not used, in this plan, the paper or any report on C1, without this scope.

**What the code adds to the claim** (code v08 and v09). The quarantine and the freeze cover each AV2 stage-A manifest's ground-truth file and every ground-truth file of the GT inventory, decided by the content rule (section 8.4). The freeze's hash set holds every quarantine member's hash, every inventory hash and the manifests' ground-truth hashes; it refuses any plain copy with a recorded hash outside the skipped folders, anything in the quarantine folder that is not a recorded member, and a recorded member whose manifest has moved (`c1_freeze_v07`, Choice 48a). This closes R17d's one-command route P2b between the freeze and the deposit, also for the 150-log file named only by the older manifests (R17e M-A), for the QCNet ground-truth-history files (R20 B2) and for R17f's M-1 routes. `--amend` cannot be reopened by deleting the deposit record once a non-exempt run is logged (section 8.2). The text-locked draft on OSF dates the plan before the confirmation-set stage A (header).

**The deposit order for H6 to H8 (R17d B1).** The method-stage tables (H6a, H6b, H7) and the H8 table read ground truth after k. Under this plan on AV2 they are computed only after the deposit record exists and validates (section 8.3): `c1_mstage_v06` and `c1_h8_v06` refuse without it, read the ground truth only from the quarantine, record `deposit_record_sha256`, and write "start" and "done" lines to the run log; the analysis refuses an H6 to H8 table made under another deposit record, with another unit set, or without a "done" line. The same order holds for every other outcome route (section 8.3). Only E⁰ (outcome-free fields, before the quarantine), the folds and the freeze run before the deposit.

---

## Frozen files

The two empty blocks below are filled by `c1_freeze_v07`, which also inserts the FROZEN_ENV, FROZEN_ENV_TPP and FROZEN_TESTS blocks after the FROZEN_ROLES block. Those three are deliberately not drafted here: the freeze refuses a plan that already holds any of them, and asserts that each of the five blocks appears exactly once in the frozen file (Choice 41a).

FROZEN_HASHES_BEGIN
FROZEN_HASHES_END

FROZEN_ROLES_BEGIN
FROZEN_ROLES_END
