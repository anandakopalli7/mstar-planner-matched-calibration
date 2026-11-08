# C1 code v09: R20, R17f and R20's re-check, under D16 v26 Choice 47, v27 Choice 48 and v28 Choice 49, with D16 v30 Choice 50 (the criteria), v32 Choice 51(a) and v33 Choice 52 (5 Nov 2026)

README v01 to v08 are kept unchanged. This README answers three reviews and three decisions:
- `70_TESTS/R20_C1_PLAN_REVIEW_v01.md` (B1–B3, M2, M3, m13), as D16 v26 Choice 47 decides;
- `70_TESTS/R17F_C1_CODE_V08_CHECK_v01.md` (M-1, m-2 to m-6), as D16 v27 Choice 48 decides;
- `70_TESTS/R20_C1_PLAN_RECHECK_v01.md` (N3, N4, N8), as D16 v28 Choice 49(b), (c), (f) and (g) decide;
- D16 v30 Choice 50, the criteria after the researcher's evidence audit (section "The criteria" below);
- D16 v32 Choice 51(a): the freeze binds `data:freeze_record` on AV2;
- D16 v33 Choice 52 (`90_DECISIONS/D16_DELEGATED_CHOICES_v33.md`, `c55c6267…`): H1's budget split, H3's removal level and doubled p, B = 20000, H9 descriptive, one decision form per hypothesis (section "The criteria").

It binds the AV2 port's builders. It lists every bound file with its role (180 files: entry 16, module 58, generator 14, source 16, builder 29, legacy 2, test 1, test_module 20, archive 24).

**Guard versions.**
- The guarded entry points still use `c1_guard_v05.py`.
- `c1_freeze_v07` and `c1_quarantine_v03` use `c1_guard_v06.py`, which imports v05 and adds only the freeze's and the quarantine's helpers.
- `c1_guard_v02.py` (`00d9bc42…`) and `c1_crc_exact_v01.py` (`4919ed20…`) are unchanged, and so are `x1_full_v02`, `x2_full_v02` and `m_run_v04`.
- No existing file was edited.

**Results.** `70_TESTS/c1_v01/C1_V09_TEST_STATUS.json`; the rehearsal on this README is `70_TESTS/c1_v01/rehearsal150_v09b/` (driver `c1_rehearsal_v08`). `rehearsal150_v09/` is the rehearsal of the pre-criteria draft of this README, kept as a record. `rehearsal150_v09b_stopped_early/` and `rehearsal150_v09b_stopped_early2/` are deliberate stops minutes after their start, before this README's final text (notes inside); they are not results.

## What changed, and what tests it (`test_c1_v12`)

| Item | Change | Test |
|---|---|---|
| **47(a), B1** the port is bound | The port is final (the lead, 5 Nov 2026; note `60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v03.md` `0d24c2d4…`, design `50_CODE/av2/AV2_TRACKER_PORT_DESIGN_v04.md` `c97ba992…`). Its tools that write a stage-A input, the log list, the frame check or the GT list are bound as `builder`: `av2_common_v02`, `av2_fetch_v05`, `av2_c1_logs_v01`, `av2_gt_prep_v02`, `av2_ego_prep_v02`, `av2_tracker_input_v02`, `av2_track_v02`, `av2_ab3dmot_v05`, `av2_horizon_prep_v02`, `av2_c1_frame_check_v01` and `av2_c1_gt_list_v01`. Its equivalence test `test_av2_port_v04_equiv_v01.py` is bound as `test_module`, and its run scripts `run_av2_c1_equiv_gt_v01.sh`, `run_av2_c1_equiv_trk_v01.sh` and `run_av2_c1_queue_v01.sh` as `source`. The equivalence records (`60_RESULTS/av2_trk/c1_375/equiv/`) are bound as `data:port_equiv`. The v01-era builders stay bound, because the 150-log public LT3D and VoxelNeXt manifests (H1-P, H5) were built with them. The only bound test is `test_c1_v12`, which reads **this** README, so FROZEN_TESTS certifies the README the freeze binds. | every group below; **LEGACY** |
| **Unbound, outcome-free tools** | Named here, not bound: the Rule-0 metric tools `av2_track_metrics_v04` (`981db2a6…`) and `av2_hota_v04` (`26944dc2…`), whose outputs are aggregates (`data:rule0_metrics`); the tables tool `av2_c1_tables_v01` (`481fdc20…`); and the descriptive detector-against-detector check `av2_c1_velocity_probe_v01` (`1286d358…`). | — |
| **47(b), 49(b), B2, N3** GT inventory | **`c1_av2_gt_inventory_v01`** (bound builder) writes the inventory: path, bytes, SHA-256, date, content class, producer (tool, hash now, and the hash recorded at run time where a pod record exists) and the producing code line that decides it, for every file that holds per-object AV2 annotation positions, boxes, sizes, yaws or velocities of **any** AV2 log, derived per-object quantities and archive members included. Archives are listed by member names (tar headers) only, never unpacked. Not listed (with reason and class): identity-only data, ego poses, aggregates. A name sweep refuses any uncovered `*gt*`, `*infos*`, archive or pickle under `30_DATA` and `60_RESULTS`. The port's 375-log file is "pending" until `--include-port`; with it, every path of the port's GT list must be listed, and the name sweep also covers the port folder. The real inventory is `40_PROTOCOL/C1_GT_INVENTORY_v02.json`. | **GTINV** (copy tree: classes, an archive by member names, an uncovered file refused, pending, `--include-port`); the real inventory `40_PROTOCOL/C1_GT_INVENTORY_v02.json` (the newest present: archive, port included, nothing pending) |
| **49(b)** large archives | **`c1_quarantine_v03`** streams everything in 1 MiB chunks (hash, gzip at level 6, verify): a multi-GB archive is quarantined whole, never unpacked, never read into memory. It takes `--gt-inventory`. Its recorded set is the union of the stage-A manifests (passed and found), the extras and inventory files, and **every** member already recorded. A plain copy inside the quarantine folder is quarantined; any other stray entry there is refused. `c1_freeze_v07` also hashes in chunks. | **Q3:** peak Python memory under 16 MiB while quarantining a 64 MiB file; an archive kept whole (`tracemalloc`) |
| **48(a), M-1** the freeze's full set | **`c1_freeze_v07`** (on `c1_guard_v06`): the recorded hashes are the union of every quarantine member (all kinds), every GT-inventory file, the found and passed stage-A manifests' ground truth, and `--extra`. Each must have a member, and no plain file anywhere in the scan root may carry one. The quarantine folder may hold only its manifest and the members. A recorded stage-A member whose manifest is no longer at its recorded path is refused. | **TREE:** R17f **N1** (a `gunzip -k` copy inside the quarantine folder) and **N2** (an older stage-A folder moved deeper than the search, its ground truth restored) are refusals; a plain copy of an inventory file is refused |
| **48(b) m-2** provenance enforced | **`c1_av2_provenance_v01`** (bound builder) writes its record only if every check passes, and exits non-zero otherwise. **`c1_freeze_v07`** requires, on AV2, a `data:provenance` file that is a success record of that tool, made for **the README being bound**, made with every check (exports, horizon, ego, ground truth, scene.json: the CLI's set), and covering every AV2 stage-A manifest passed as it is now. | **PROV**, **TREE** (a failed, partial, other-README or non-covering record is refused) |
| **47(a), 46(d)** provenance | For every AV2 stage-A manifest: `builder_sha256` must be a bound builder. Each tracker export's receipt must match the recorded hash and name a bound builder, and its detection input's receipt a bound adapter. The tools that write no receipt are checked by re-making their file with the bound builder outside the workspace and comparing hashes: the T1/T3 horizon by `av2_horizon_prep_v02 --propagate-only`, the ego file by `av2_ego_prep_v02`, the ground truth by `av2_gt_prep_v02` (hashed and deleted unopened). The AB3DMOT horizon is checked as the worker-order concatenation of the bound AB3DMOT builder's worker files. | **PROV:** the real 150-log manifests' exports and AB3DMOT horizon pass; a horizon re-made by the bound builder passes; refused (R20 B1's refusal test): a track input from an unbound tool, a detection input from an unbound adapter, a horizon the bound builder does not make, an unbound or missing stage-A builder; a re-made ego or ground truth that differs is refused (a stand-in runner, since the real builders read AV2 annotations); nothing is written on failure. Development check, not a test: `av2_horizon_prep_v02 --propagate-only` re-makes the real 150-log T1 and T3 (public LT3D) horizons, which `av2_horizon_prep_v01` made, exactly (decompressed SHA-256 equal; 740 s and 537 s). |
| **47(e), M2** ShownAbove | **`c1_analyse_v09`**: a comparator leaves V_t only through a flagged cell, family cell or pooled cell. Failing HK1c alone keeps it in V_t. M\*'s own HK1c requirement is unchanged. The decision lists, per route, tracker and comparator, why it left V_t or why it stays (`V_t_reasons`). | **AN9:** a constructed HK1c-only comparator is removed by v08's rule and kept by v09's, and its reason is listed |
| **49(c), N4** H3's set | `c1_analyse_v09`: H3's comparator set V^J also keeps a comparator that fails only the pooled bound on the joint loss (`VJ_hk1c_only`). | **AN9:** a constructed case |
| **47(f), M3** upper bounds | `c1_analyse_v09`, descriptive and never gated: for M\*, per route, tracker and population, the simultaneous one-sided 95 % upper bound of every evaluable cell and their maximum (`Mstar_simultaneous_upper_bounds`). | **AN9:** equals `k6_analyse_v02.flag`'s upper bound on a constructed table; nothing is computed for comparators |
| **47(m) m13** zero-SE family | `c1_analyse_v09` sets `STRICT_Q` false in every mode. A family in which M\* has zero exceedance in every draw is judged by Ê > δ and reported (`Mstar_zero_se_families`), not raised. | **AN9:** v08's setting raises on a constructed all-zero table; v09's does not |
| **47(c), 49(l), B3** H9's label and floor | `c1_analyse_v09` refuses a config without `h9_label`, or with a value other than "secondary" or "descriptive" (no default). If the floor (condition a: ≥ 6 power-qualified E2 cells) fails on a tracker, the predictor arm sets H9 false there, and H9's status is **"does not hold: floor not met"**, with an `H9_floor` block (`family_size_E2`, `floor`, `floor_met` per tracker) and the reason "floor not met (condition a: >= 6 power-qualified E2 cells): <tracker> family_size_E2 = n < 6". If H9 fails with the floor met on both trackers, the status stays "does not hold". **In C1 this wording is not used:** `c1_analyse_v09 --c1` accepts only "descriptive" (D16 v33 Choice 52b; section "H9 in C1"). | **AN9**; **REHEARSAL**; **CRIT** (another label refused with `--c1`) |
| **48(b) m-5** Q1 | `c1_analyse_v09` never lists Q1 among the missing inputs, in any path. | **AN9:** the H9 exception path |
| **47(i), 49(g), S22** | **`c1_power_counts_v05`** (bound builder, reported only), part H9: the power of H9's **tested** population, the Trajectron++ PD items, from the stage-A counts-only items. **The primary projection leaves out history length** (every PD item, E2 cells only), so it **overstates** H9's power. The development history shares give a descriptive sensitivity. Part B uses the stricter comparator rule (47e, 49c: HK1c alone no longer removes a comparator); H3's set is not modelled. Development inputs: the K8 Linux replicate's v03 analysis (R16) and the nuScenes Trajectron++ keys. Criteria: part H9's power family uses the target-only rule (`c1_rules_v01.power_target`, 2000 datasets); parts A, B and J keep v02's analytic approximation (reported only). | **PC5** |
| **48(b) m-3** skipped folders | The freeze and the quarantine print, and the freeze writes into FROZEN_TESTS, the folders the scan skipped, by name: `50_CODE/env/`, the quarantine folder (checked by name instead), and names holding a banned word. The skip itself stays. | **TREE** |
| **48(b) m-6** | `c1_freeze_v07` refuses an AV2 stage-A manifest without `builder_sha256`. | **TREE** |
| **47(j), 51(a)** data roles | On AV2, `c1_freeze_v07` requires `data:s20a`, `data:s22`, `data:logs375`, `data:gt_inventory`, `data:rule0_metrics`, `data:provenance`, `data:port_equiv` and, by D16 v32 Choice 51(a), `data:freeze_record` (the lead's `40_PROTOCOL/C1_FREEZE_TIME_RECORD_v01.md`: the Rule-0 metrics' run times and readers, and the off-workspace scans; the lead writes it at step 18.5, and this code never creates it). A role may name several files (`port_equiv=a port_equiv=b`). `data:e0_plan` and `data:scene_json` stay required everywhere. | **TREE** (all eight, two files for `port_equiv`, a stand-in for `freeze_record`; a freeze without `freeze_record` is refused); **FRZ7** |
| **48(c)** dry run | `c1_freeze_v07 --dry-run` runs every check except the bound tests and writes nothing. | **FRZ7:** the plan, its sidecar, the log and the test folder are untouched |

## The criteria (D16 v30 Choice 50, after the researcher's evidence audit)

Source: `90_DECISIONS/D16_DELEGATED_CHOICES_v30.md` Choice 50 (v29 with the wording corrected; v29 is kept) and the criteria register `90_DECISIONS/C1_CRITERIA_REGISTER_v02.md`.

**Principle (ICH E9 section 5.5).** Evidence **against** M\* is judged at one-sided 0.05, the strict direction for M\*. Every bound or flag whose passing **supports** a claim in M\*'s favour is judged at one-sided 0.025 (two-sided 95 %).

**One place.** Every value is a named constant in **`c1_rules_v01.py`** (bound module), with a one-line source comment, and `test_c1_v12` (group CRIT) pins each one. A frozen config that states one of them (at top level or under `"criteria"`, any case), or a Form C `c`, with another value is refused by `c1_analyse_v09` (`c1_rules_v01.config_check`, in `decide_all` and `main`). `c1_rules_v01` asserts on import that `k6_analyse_v02`'s and `k8_analyse_v04`'s own constants (not edited) carry the same values.

| Constant | Value | Line in `c1_rules_v01.py` | What it governs |
|---|---|---|---|
| `ALPHA_AGAINST` | 0.05 | 49 | M\*'s cell, family and pooled flags (Valid in H1, H3, H4); H6a, H7, H9 (Choice 50) |
| `ALPHA_FOR` | 0.025 | 50 | Form C (H2) and H10's NI part at `UB^{0.975}`; H6b's and H10's cell parts at 0.975; Holm's family S (m = 5, gated on H1); Form A at 0.025/4 (Choice 50) |
| `ALPHA_REMOVAL`, `ALPHA_FORM_B` | 0.0125, 0.0125 | 51–52 | **H1's 0.025 split (Choice 52c):** each of V_t's 9 removal conditions at 1 − 0.0125/9; Form B `UB^{1 − 0.0125/\|V_t\|}(Δ) < 0` (was 0.025 each) |
| `ALPHA_REMOVAL_VJ`, `H3_P_MULTIPLIER` | 0.0025, 2 | 53–54 | **H3 (Choice 52c):** each of V^J's 3 removal conditions at 1 − 0.0025/3; H3's p-value doubled (capped at 1) before Holm |
| `N_REMOVAL_V`, `N_REMOVAL_VJ` | 9, 3 | 55–56 | the removal conditions' counts |
| `HK1C_LEVEL` | **0.995** | 57 | HK1c's (Valid) and ValidJ's (H3) pooled upper bound; D16 v30 Choice 50(c), Loh 1987 calibration rule, development coverage at 375 units (`60_RESULTS/c1_criteria_sensitivity_v02`, note `2e69fae6…`, `A_hk1c_level_v02.json`) |
| `HK1C_MARGIN`, `DELTA` | 0.03, 0.05 | 58–59 | unchanged: the bound must be ≤ δ + 0.03 |
| `P_PLANT`, `RHO`, `POWER_MIN` | 0.15, 0.5, 0.80 | 60–62 | the power rule |
| `N_DATASETS`, `N_WEIGHTS`, `POWER_FLAG_LEVEL` | 2000, 500, 0.95 | 63, 65, 66 | the power rule (was 200 datasets) |
| `N_DATASETS_DESCRIPTIVE_ARMS` | 500 | 64 | power datasets for the arms whose validity is descriptive only (the 21 sweep points, Z0, M\*J, M\*Jx, RETUNED_HK1), for cost; M\* and the comparators of K use 2000 (Choice 52g item 4) |
| `B_BOOT` | **20000** | 71 | **Choice 52(d):** every bootstrap of the analysis (flags, pooled and paired bounds, HK1c, p-values); the weights are drawn so that their first 500 rows (the power rule's) do not depend on B |
| `H9_LABEL_C1` | "descriptive" | 72 | **Choice 52(b):** `c1_analyse_v09 --c1` refuses a config with another `h9_label` |
| `F_MIN`, `PD_MIN_EVALUABLE`, `MIN_UNITS`, `MIN_LOGS` | 6, 1, 39, 8 | 67–70 | unchanged |
| `C_FORM_C`, `NI_MARGIN`, `FORM_A_K`, `HOLM_M` | 0.03, 0.03, 4, 5 | 73–76 | unchanged; Form A's Bonferroni count; family S's size |
| `DESC_F_MIN`, `DESC_P`, `DESC_N_DATASETS` | (4, 8), (0.10, 0.12, 0.20), 500 | 77–79 | descriptive outputs |
| `BATCH` | 25 | 163 | the power datasets are drawn in batches of 25; a run's datasets are a prefix of a longer run's |

Derived: `HOLM_LEVELS` = 0.005, 0.00625, 0.00833, 0.0125, 0.025, the levels Holm can assign.

**One decision form per hypothesis (Choice 52e).**
- **H1** (outside Holm): the bound decides. V_t is formed at 1 − 0.0125/9 per condition, and Form B at `UB^{1 − 0.0125/|V_t|}`. Form B's Bonferroni p (`|V_t|` × the largest share of replicates ≥ 0) is reported, and its threshold is 0.0125.
- **Family S** (H2, H3, H4, H6b, H10): the p-value decides. It is the share of bootstrap replicates on the null side, and it enters Holm at 0.025 (m = 5, gated on H1).
  - `holm_v05_criteria` confirms a claim when Holm rejects it. The claim's status follows the p-value; the bound-form status at the nominal level is kept as `status_bound_nominal`.
  - The decision's `S_decision_forms` block reports, per claim, the bound at the level Holm assigned, computed from the same replicates (`holm_levels` of `form_c`, `H3`, the transfer route's `form_b` and `H10`), and whether it agrees with the p-value. Disagreements are listed.
  - The p-values are: H2, the share of replicates with Δ > c; H3, min(1, 2·|V^J|·max share ≥ 0); H4, min(1, |V_t|·max share ≥ 0); H10, the larger of the cell part's sup-t p and the NI share; H6b, the method stage's smallest per-cell p (B4's sup-t p and the paired p, the larger of the two).
  - **H6b's bound is not available:** the method stage records p-values only, so the p-value decides H6b.
  - With the gate closed, Holm is not run, and the statuses stay the bound form's, labelled supportive (as before).
- **H4** has a data-selected V_t inside family S. Choice 52(c) treats only H1 and H3. Here H4's V_t uses the same comparator statuses (removal at 1 − 0.0125/9), and its p is not doubled. **For the lead to confirm.**

**The power rule (target-only).** For each evaluable cell, that cell is drawn at `P_PLANT` and every other evaluable cell at exactly δ = 0.05, with the same beta-binomial ρ (one rate per scene and cell) and the arm's real record counts. The target counts if it is flagged in the all-evaluable one-sided sup-t at 0.95. It is outcome-free: no observed exceedance enters. `c1_rules_v01.power_target` computes it, vectorised over the targets and the datasets of a batch; `power_target_reference` writes the same rule as a plain loop with `m_lib_v04._simul`, and CRIT checks that both agree exactly on the same draws. The seeds are unchanged at every call site. The rule is applied to the analysis's families (`hk1_rule_criteria`), to H9's floor (`c1_predarm_v07.h9_rule_v07`) and to S22 (`c1_power_counts_v05` part H9).

**Where the rules are installed.**
- `c1_rules_v01.apply_analysis` installs them in the analysis chain, in the namespaces of the modules it imports and never edits:
  - `k8_analyse_v04`: `hk1_rule` → `hk1_rule_criteria`, `analyse_decide` → `analyse_decide_criteria`, `joint_section` → `joint_section_criteria`;
  - `c1_analyse_v02`: `form_a`, `form_c`, `h10_rule`, `h6_rules`;
  - `c1_analyse_v05`: `holm_v05`.
- `c1_analyse_v09` sets Form B's alpha to `ALPHA_FORM_B` (level 1 − 0.0125/|V_t|) and H3's bound to 1 − `ALPHA_FOR`/(2·|V^J|), the dual of the doubled p (`H3_P_MULTIPLIER`); it states the level in every removal reason and adds the descriptive blocks.
- `analyse_decide_criteria` also fixes a defect of the v09 draft: `k8_analyse_v04` keeps only a fixed list of keys in `validity_by_arm`, so 47(f)'s upper bounds did not reach the decision on real runs. The rehearsal now checks that they do.

**H6b** is judged from the method stage's per-cell p-values (`H6b_detail`: per cell, the larger of B4's sup-t p-value and the paired B4 − M\* p-value, where M\* is not flagged). Its nominal status holds if one is ≤ 0.025; inside family S its p-value (the smallest) decides through Holm (Choice 52e). This is the p-value form of "B4 flagged and the paired sup-t lower bound > 0 at one-sided 0.975", so `c1_mstage_v06` is unchanged. The two forms can differ only through the bootstrap quantile's interpolation.

**Descriptive outputs, never gated** (decision blocks):
- `Mstar_power_families`: per route, tracker and population, M\*'s per-cell power at P 0.10, 0.12, 0.15 and 0.20 (500 datasets; 2000 at 0.15) and MDE80, the family's share of the population's records, and the floor at F_MIN 4, 6 and 8;
- `comparator_power_families`: each comparator's family size, record share and floors;
- `zero_se_effects`: every comparator with a zero-SE (non-finite quantile) case, and whether it changed V_t;
- `Mstar_simultaneous_upper_bounds`: U_max and the cell upper bounds, labelled "approximate (development coverage 0.78 at 39 units, 0.87 at 150, near δ)";
- `criteria`: the constants and the levels;
- `S_decision_forms` (Choice 52e) and `H9_descriptive` (Choice 52b), described above.

**Development replay** (`tests/c1_devreplay_v01.py` on the K8 v03 inputs: 840 nuScenes scenes; checked by DEVREPLAY):
`70_TESTS/c1_v01/status_v09/c1_devreplay_v01.json` (`72438495…`):

| | T1 | T3 |
|---|---|---|
| Valid(M\*) | true | true |
| M\*'s pooled UB at 0.995 (PD7 / SD1_7 / PD) | 0.0463 / 0.0386 / 0.0627 | 0.0440 / 0.0376 / 0.0526 |
| M\*'s power families (PD7 / SD1_7 / PD) | 26 / 18 / 5 | 26 / 18 / 5 |
| V_t (removal at 1 − 0.0125/9) | {B3} | {B0, B3} |
| Form B UB | M\*−B3 -0.722 (at 0.9875) | M\*−B0 -0.566, M\*−B3 -0.677 (at 0.9938) |
| Form A (1 − 0.025/4), met | true | true |
| Form C UB^{0.975}(M\*−B4) | -0.066 | -0.034 |
| H10 NI UB^{0.975}(M\*−B6) | -0.043 | +0.005 |
| same verdict as at Choice 50's levels | true | true |

The replay runs at D16 v33 Choice 52's levels: removal at 1 − 0.0125/9, Form B at 1 − 0.0125/|V_t|, HK1c at 0.995 and B = 20000 (the power rule on the first 500 weight rows, which do not depend on B).

**Against the lead's development check v03** (`60_RESULTS/c1_criteria_sensitivity_v03/C3_verdict_rstar2_v03.json`, `3ac58810…`; the same levels, B = 20000; compared by `70_TESTS/c1_v01/status_v09/dev_compare_replay_v03.py` → `dev_compare_replay_v03.json`, `3357a33e…`; tolerance 0.002 on bounds, 1 cell on families):
- 26 of 33 values agree within tolerance: Valid(M\*), V_t, the Form B level, M\*'s pooled bounds at 0.995 and power families, Form B's bounds, Form C and H10's NI bound, on both trackers.
- **Larger, reported and not adjusted (7 values, all Form A at 1 − 0.025/4):** T1 M\*−B0 replay -0.1939, reference -0.1968; T1 M\*−B1 replay -0.2406, reference -0.2439; T1 M\*−B4 replay -0.0615, reference -0.0637; T1 M\*−B9 replay -0.2915, reference -0.2953; T3 M\*−B0 replay -0.5656, reference -0.5696; T3 M\*−B1 replay -0.1806, reference -0.1843; T3 M\*−B9 replay -0.2289, reference -0.2337.
- The replay's Form A bounds recomputed at 1 − 0.05/4 (the level before Choice 50) match all 8 reference values within 0.0005. So the reference's Form A appears to sit at 0.05/4, while the code follows Choice 50 and the register v02 (Form A, descriptive, 0.05/4 → 0.025/4). On T3 the replay's Form A bound for B0 equals its Form B bound for B0 at the same level (−0.5656), as it should. Form A is descriptive, so no verdict moves. **For the lead.**

**Context from the lead's development check v03** (not recomputed here): over 100 seed sets at B = 20000, V_t and V^J were identical in 100 of 100; every decisive bound's Monte Carlo SE was at most 0.0006; at 375 units, P(H1) was 0.870 (plug-in) and 0.933 (capped).

H3 is not replayed: the K8 replicate's episodes hold no M\*J or M\*Jx arm (the reference takes H3 from K8's joint v04). H3's rules are tested on constructed cases (AN9, CRIT) and in the rehearsal.

**Cost.** The power rule takes about 8 to 15 ms per dataset at 150 units and 12 cells on this laptop under load, so about 15 to 30 s per arm and population. The analysis computes it for about 32 arms × 3 populations per route and tracker: M\* and the 7 comparators with 2000 datasets, the 24 descriptive arms with 500. A 375-log table costs about 2.5 times as much per dataset. The rehearsal's step times (`rehearsal150_v09b/steps.jsonl`) show the real cost.

**B = 20000 (Choice 52d), the extra runtime.** On rehearsal150_v08's stand-in, one route and tracker (150 units, 32 arms; `70_TESTS/c1_v01/status_v09/dev_bootstrap_B_timing.json`) took 152 s at B = 2000 and 386 s at B = 20000, without the power rule (whose cost does not depend on B). That is **+234 s per table at 150 units**. Peak Python memory was 0.56 GB at B = 2000 and **1.9 GB** at B = 20000. A 375-log table should take about 2.5 times the extra (roughly +10 min per table; AV2 has about 11 route-tracker tables) and more memory. This was measured on a laptop shared with other jobs.

**Re-run:** v11's groups, against this README: G5, RUNLOG, SWEEP, ME, MD, SCENEMAP, FRZ7 (FRZ6's cases on `c1_freeze_v07`), TREE and REHEARSAL. **New:** GTINV, PROV, AN9, CRIT, DEVREPLAY, PC5 and Q3.

**Parallel run** (the lead's speed request of 5 Nov 2026). `test_c1_v12` runs its groups in parallel, with **at most 3 worker processes** (the laptop has 8 logical cores):
- Each group runs in its own worker process (`test_c1_v12.py --worker <group>`) and its own output folder under `70_TESTS/c1_v01/tests_v12/`. Its record and log go to `tests_v12/parallel/`.
- The pool holds G5, RUNLOG, ME, MD, SCENEMAP, FRZ7, GTINV, PROV, AN9, CRIT, DEVREPLAY, PC5, Q3, TREE (in its own copy tree) and REHEARSAL, started longest first.
- SWEEP and LEGACY then run alone, one after the other. Both create a `c1_gt_<pid>_*` folder for a process that has just ended and expect `guard()` to sweep it as stale (LEGACY through `test_c1_v11`'s SWEEP). A process spawned at that moment by another group could be given the recycled process ID, and the folder would then look live. Running them alone keeps the serial conditions.
- The real-tree assertions and the tested-file hashes are taken once, before and after, in the parent process. The tests and the pass criteria are those of a serial run.

**LEGACY** (the lead's rule of 5 Nov 2026: keep LEGACY affordable; suites v01–v10 stay skipped where `test_c1_v11` already re-ran them, and the rule is stated):
- Suites v01–v10 are skipped. The lead's verified rerun of `test_c1_v11` (`70_TESTS/c1_v01/lead_recheck_v08/c1_tests_v11_lead.json`, `50a786c5…`) ran every one of their groups, each "pass" or "skipped by rule"; LEGACY checks that record. LEGACY also checks that every one of the 154 files README v08 binds is unchanged on disk. v09 adds new files only, so those suites would read the same code.
- `test_c1_v11`'s own groups run in their own process. Three are skipped: its LEGACY (v01–v10, as above); FRZ6 (README v08 can no longer be frozen, because its entry points are not the latest; FRZ7 replaces it); and TREE (it binds `c1_freeze_v06` and `c1_quarantine_v02`, which this README supersedes; this suite's TREE re-runs its cases on the bound versions).

## H9 in C1: descriptive (D16 v33 Choice 52b; for the plan, verbatim)

> With h9_label "descriptive" (the C1 config's value, which `c1_analyse_v09 --c1` requires), H9's status is "descriptive". The decision's H9_descriptive block reports, per tracker, the Trajectron++ PD cells' estimates and simultaneous one-sided 95 % bounds, the power-qualified E2 family size, the floor (6) and whether it is met, and states: "H9 is descriptive (D16 v33 Choice 52b): the decision reports, per tracker, the Trajectron++ PD cells' estimates and simultaneous one-sided 95 % bounds, the power-qualified E2 family size, the floor (6) and whether it is met; no confirmatory claim is made about a learned predictor". The H9_floor block lists family_size_E2, floor and floor_met per tracker. No H9 output says "does not hold".

The secondary-label wording (Choice 47c, 49l), kept in the code but not used in C1: with h9_label "secondary", if the floor fails on a tracker, H9's status is "does not hold: floor not met", with the reason "floor not met (condition a: >= 6 power-qualified E2 cells): <tracker> family_size_E2 = <n> < 6".

S22 (development check, `c1_power_counts_v05` part H9 on the 150-log public-LT3D stage-A items, resampled to 375 logs, 20 draws, with the criteria's target-only power rule; `70_TESTS/c1_v01/status_v09/dev_s22_power_counts_v05_rules.json`):
- The power-qualified E2 family has 2 cells in every draw (range 2–2) per tracker, with P(≥ 6) = 0. This holds even though the projection leaves out history length and so overstates the power.
- The family covers about 58 % (T1) and 63 % (T3) of the items. On the 150 logs as given it has 0 cells.
- The history-share sensitivity also gives 2 cells.
- The earlier rule (`k6_analyse_v02.power_family`, 200 datasets; `dev_s22_power_counts_v05.json`) gave a median of 2 (range 2–4).

At the planned size, H9's floor is therefore expected not to be met (`floor_met` false on both trackers). With the descriptive label this is reported in `H9_descriptive` and `H9_floor`, and it changes nothing.

**The stricter comparator rule on the rehearsal inputs** (47e and 49c alone, at the pre-criteria levels; development fact; `70_TESTS/c1_v01/status_v09/dev_comparator_rule_v01.py` on rehearsal150_v08's analysis, the same nuScenes stand-in inputs as rehearsal150_v09): it changes no comparator's V_t membership, no H3 V^J membership and no H1 or H3 status. Every comparator that fails HK1c there is also flagged (T3: B1 and B4 within AV2, B4 in transfer, B1 and B4 on the public and source routes), so both rules remove it. No comparator of H3's set fails only the pooled bound (B0a3 does on the public and source routes, but it is not in H3's set, and H3 reads the within-AV2 route only). Under the criteria the levels, families and V_t change, so the REHEARSAL group lists its decision's differences from rehearsal150_v08's descriptively (`vs_rehearsal150_v08_descriptive`) and does not assert this.

## Resuming after an environment stop (Choice 49f): what v09 does

v09 adds no automatic rename-and-resume. The reasons:
- It would rename files inside the confirmatory pipeline.
- It needs new versions of all nine guarded entry points, after R17f's check of them. Several call `refuse_existing` before the guard, and would have to call it after.

What the frozen code already allows:
- **Same command re-runs** for the entry points whose output is written only at the end, through a temporary name and a rename: `c1_fit_v06`, `c1_mstage_v06`, `c1_h8_v06`, `c1_e0_v05`, `c1_predarm_v07` and `c1_analyse_v09`. After an environment stop, nothing exists at their output path, so `refuse_existing` does not block the same frozen command.
- **Resume from checkpoints:**
  - `c1_run_v06`'s final run record is written last, so the same command with `--resume` continues from its shards;
  - `c1_mstage_v06` resumes from its step checkpoints (`<out>.E1.ckpt.json`, `<out>.E2.ckpt.json`), which lie beside the output path.
- **New output name:** `av2_cache_stageB_v06` (a folder filled progressively) and `k8_items_v08` (the npz written in place) leave a partial output. The same tag or path is refused, so the lead re-runs under a new tag or output name.

In every case the run log keeps the stopped run's "start" line without a "done" line. The table of record is the first output with a "done" line (Choice 49f, P6).

## The narrowed claim

R20's P1 wording (Choice 47d) is the claim of record. This README does not restate it.

## Command order (AV2, for the lead)

Each step names its environment: **canmot310** is `50_CODE/env/canmot310/Scripts/python.exe -B`; **ab3dmot310**, **av2eval310** and **tpp38** are the port's and Trajectron++'s environments.

1. **Text lock** (researcher, OSF; Choice 47i, 49a).
2. **Rule-0 metrics, after the lock** (Choice 49e): `av2_track_metrics_v04` (canmot310) and `av2_hota_v04` (av2eval310). These are unbound tools; their outputs go to `data:rule0_metrics`.
3. **Log list:** `av2_c1_logs_v01` → `30_DATA/av2_trk_v02/C1_LOGS_375_v01.json` (`data:logs375`).
4. **Prepared ground truth, before stage A:** `av2_gt_prep_v02 --logs-file C1_LOGS_375_v01.json` (canmot310) → one 375-unit file (m5).
5. **Port runs** (already made, under the port's queue): tracker input `av2_tracker_input_v02`; T1 and T3 `av2_track_v02`; AB3DMOT `av2_ab3dmot_v05` (ab3dmot310); ego `av2_ego_prep_v02`; frame check `av2_c1_frame_check_v01`.
6. **2 s propagation:** `av2_horizon_prep_v02 --propagate-only --allow-av2-propagation` for T1 and T3 (canmot310); AB3DMOT's own horizon, its worker files merged in worker order.
7. **Stage A** for the 375 logs, T1, T3 and `tab`: `av2_cache_stageA_v02` (canmot310). Then the counts: S20a, and S22 with `c1_power_counts_v05 <out> --h9-items t1=<375-log items> t3=<…>`.
8. **Folds:** `c1_folds_v03`, then `--restrict-from` for `val` and for `held_out_train`.
9. **Scene map:** `c1_av2_scene_map_v01`.
10. **E⁰:** `c1_e0_v05 --stageA-manifests …` (before the quarantine).
11. **Provenance:** `c1_av2_provenance_v01 --readme README_C1_CODE_v09.md --stageA-manifests <every AV2 stage-A manifest to bind> --logs-file C1_LOGS_375_v01.json --out <record>` (canmot310), before the quarantine. A failure stops the freeze; on failure no record is written.
12. **GT inventory:** `c1_av2_gt_inventory_v01 --include-port --out 40_PROTOCOL/C1_GT_INVENTORY_v0N.json --extra-list <txt>`. Done once for this README: `40_PROTOCOL/C1_GT_INVENTORY_v02.json` (8 files, 3,567,314,110 B, the port included, nothing pending). The lead re-runs it with a new number if any ground-truth file is made or changed later. (`C1_GT_INVENTORY_v01.json` is the earlier, port-pending inventory, written by a draft of the tool before its `--include-port` sweep of the port folder; superseded by v02.)
13. **Quarantine:** `c1_quarantine_v03 --stageA-manifests … --gt-inventory <inventory> --extra <the port's GT_FILES_FOR_QUARANTINE_v01.txt paths> --dry-run`, then the same command without `--dry-run`.
14. **Freeze dry run on the real tree** (Choice 48c): `c1_freeze_v07 … --dry-run`. It writes nothing.
15. **Freeze:** `c1_freeze_v07 … --data scene_json=… e0_plan=… s20a=… s22=… logs375=… gt_inventory=… rule0_metrics=… provenance=… port_equiv=<each equivalence record> freeze_record=40_PROTOCOL/C1_FREEZE_TIME_RECORD_v01.md …` (the record written by the lead first, Choice 51a). The config holds `h8_units = folds`, `h9_label = "descriptive"` (D16 v33 Choice 52b; `c1_analyse_v09 --c1` refuses another value) and no `q1`. The lead checks `h9_label`.
16. **OSF registration** (researcher), then the deposit record (lead).
17. **Stage B:** `av2_cache_stageB_v06 --tag`. **Items:** `k8_items_v08`. **Fits and runs:** `c1_fit_v06`, `c1_transfer_apply_v01`, `c1_run_v06`. **Method stage:** `c1_mstage_v06`. **H8:** `c1_h8_v06`.
18. **Trajectron++** as README v08: `c1_tpp_envcheck_v01`, then `tpp_keys_v03` under canmot310 and `tpp_run_v03` under tpp38.
19. **Predictor arm:** `c1_predarm_v07`. **Analysis:** `c1_analyse_v09 --c1` (with the criteria; the frozen config may restate the constants only with the code's values).
20. **Upload** the run log and the stage-B log.

## Entry points (the plan's FROZEN_ROLES)

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v09.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v07.py` |
| `entry:c1_quarantine` | `c1_av2/c1_quarantine_v03.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v07.py` (H9's floor by the target-only power rule) |
| `entry:c1_fit`, `c1_run`, `c1_mstage`, `c1_h8`, `c1_e0` | as README v08: `c1_fit_v06`, `c1_run_v06`, `c1_mstage_v06`, `c1_h8_v06`, `c1_e0_v05` |
| `entry:c1_transfer_apply`, `c1_folds`, `tpp_envcheck`, `stageB`, `k8_items`, `tpp_keys`, `tpp_run` | as README v08 |

New builders: `c1_av2_gt_inventory_v01`, `c1_av2_provenance_v01`, `c1_power_counts_v05` and the port's builders. New module: `c1_rules_v01` (the criteria). New test module: `tests/c1_devreplay_v01.py` (the development replay).

**The port's stage-A inputs** (from the lead): `--gt 30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json` (`e5c390aa…`), `--ego 30_DATA/av2_trk_v02/ego/av2_c1_ego10hz_v01.json.gz` (`3e4acb4a…`); T1 `export/t1_owncp/worker0…7` with `horizon/horizon8_t1_owncp.jsonl.gz` (`paper/local/canmot/sc`); T3 `export/t3_owncp/worker0…7` with `horizon/horizon8_t3_owncp.jsonl.gz` (`paper/baseline/poly_mot`); AB3DMOT `export_tab_owncp/ab3dmot_kf/worker0…5` with `horizon/horizon8_tab_owncp.jsonl.gz` (`lt3d/ab3dmot`). Output hash list `30_DATA/av2_trk_v02/SHA256SUMS_v01.txt` (`b8c732f7…`, 108 files); GT list `GT_FILES_FOR_QUARANTINE_v01.txt` (`874d4cbd…`). The new exports carry the dataset tag `av2_sensor_val_train`: the guard maps every tag starting with `av2` to AV2 (`c1_guard_v03.norm_tag`), `av2_cache_stageA_v02` writes `"dataset": "av2"`, `c1_av2_provenance_v01` accepts any AV2 tag and re-makes the horizons with `av2_horizon_prep_v02`, which recognises it (`av2_horizon_prep_v01` does not, and is not used). Development check, not a test (`70_TESTS/c1_v01/status_v09/dev_provenance_port375_inputs.json`): on these inputs, every T1 and T3 export's receipt names `av2_track_v02` and its detection input's receipt `av2_tracker_input_v02`; every AB3DMOT export's receipt names `av2_ab3dmot_v05`; and the AB3DMOT horizon is the worker-order concatenation of its six worker files.

## Limits

- **The run log.** Deleting or truncating the run log (cutting it back after its last exempt line) reopens `--amend` in code. What then remains is the second OSF registration and the deviation log (Choice 44c, 48b m-4).
- **The scan, as it really is** (49a):
  - The freeze and the quarantine hash every file whose size equals a recorded ground truth's, under the workspace (or a rehearsal's `--data-root`).
  - They skip `50_CODE/env/` and folders whose names hold a banned word. These are listed by name, not opened.
  - The quarantine folder is not hashed. It is checked by name: only its manifest and the recorded members may be there.
  - The recorded set is every member, every inventory file, the found and passed stage-A manifests' ground truth, and `--extra`.
  - Stage-A manifests are found down to 4 folder levels below `30_DATA`. A deeper or moved manifest is not found, but a recorded member whose manifest is no longer at its recorded path is refused.
  - A ground-truth file that is in none of these, a modified copy, or a copy outside the workspace is not found.
- **Provenance** proves that the bound builders, on the bound inputs, write the recorded bytes. It does not prove what ran on the pod or the laptop when the files were first made. Its ego and ground-truth re-makes read AV2 annotations, so the tests use a stand-in runner for them: the lead's run is their first real use. The 150-log manifests were made by the v01-era tools; their re-make by the v02 builders is shown for the horizons only (development check above).
- **The rehearsal is a stand-in.** It uses nuScenes validation scenes as "AV2", T1's data as AB3DMOT's, and no run log, deposit, quarantine or AV2 data role (nuScenes is exempt). The AV2 paths (quarantine, inventory, provenance, data roles, run log, deposit, stage B, scene map) are tested in the copy tree on R17d's AV2-tagged stand-in.
- **Two in-place corrections in the port** (07:07:05 on 5 Nov 2026, before any 375-log output): `av2_track_v02` and `av2_ab3dmot_v05` were corrected in place for a checkpoint-hash bug, in which Windows newline translation made a resume recompute; their outputs were unaffected (the lead's record). The bound hashes are the corrected files'.
- **AB3DMOT's detection input** is not checked through a receipt: its export receipts record no detection path. Its tracker and its horizon are checked.
- **The 375-log T1 and T3 horizons** were not re-made in development (about 30 to 40 minutes each); the lead's provenance run is the first. `av2_horizon_prep_v02` made them, and it re-makes the 150-log horizons exactly.
- **The inventory** covers the workspace only. The public annotation folders are conceded; nuScenes folders are excluded by name.
- **Criteria.** `HK1C_LEVEL` is the lead's final 0.995 (D16 v30 Choice 50(c)); a later change would change `c1_rules_v01`, this README, the development replay (re-run) and the rehearsal. The 24 descriptive arms use 500 power datasets, not 2000, for cost (`N_DATASETS_DESCRIPTIVE_ARMS`). H9-noHL and the "v04 joint rule" comparison inside the predictor arm stay on `k6_analyse_v02.power_family` (descriptive, unchanged). H6b uses the p-value form of the 0.975 flag (see above). Parts A, B and J of `c1_power_counts_v05` keep the analytic power approximation.
- **Choice 52, what v09 does not do:**
  - **The method stage's bootstraps are unchanged** (`c1_mstage_v06` on the frozen `m_run_v04`: B 2000 for the fixed rule, 200 for refit-CV). H6b's p-value comes from the refit-CV bootstrap, so its smallest non-zero value is 1/200 = 0.005, the smallest Holm level. Changing this needs a `c1_mstage_v07`. **For the lead.**
  - The predictor arm (H9, now descriptive) keeps B 2000.
  - The Monte Carlo SE of each decisive bound (Choice 52d) is not computed by the code.
  - The resource-exhaustion rule (Choice 52g item 11) is **plan-only** in v09. The run-log code does not classify stops: a stopped run leaves its "start" line without a "done" line, whatever the cause (MemoryError, ENOSPC or any other). The rerun of the same frozen code on the same inputs and seeds writes its own start and done lines (see "Resuming after an environment stop").
- **Q1** is not tested in C1. **Forged records** still pass.

## Bound files (180; `<sha256>  <path>  <role>`)

```
dd6fe7324dfcf8c8f136f2fb117eab840e3f742049a317a9769c48e90a6c23fc  50_CODE/c1_av2/c1_analyse_v09.py  entry:c1_analyse
82e1eb4ab52d044a7e47dcb5f4b41d84a536421523956f90c401236dce0d3190  50_CODE/c1_av2/c1_fit_v06.py  entry:c1_fit
77967094aecd19a76363569e336c359d0f697182dd343614ef8e00da761f72b6  50_CODE/c1_av2/c1_run_v06.py  entry:c1_run
1e1477ff788e708ce33a401c6916fdb4c4fd924c91ef494524bcf0a131dda89f  50_CODE/c1_av2/c1_mstage_v06.py  entry:c1_mstage
101a47acb78eb00f83ec1afa6a8ab2469d5ab32d246fa8bfb63e311f4142c026  50_CODE/c1_av2/c1_h8_v06.py  entry:c1_h8
8f1312a373a40ca82a020d37ee46c5904808c8f139683e1871868035382c438e  50_CODE/c1_av2/c1_e0_v05.py  entry:c1_e0
b5227e659a309dd137c34527bfa55440f56ed23314a4605f76c0f93179c6c36f  50_CODE/c1_av2/c1_predarm_v07.py  entry:c1_predarm
9c909b9ba27ac207aa2653ec49963403f5fe59bad51d3e5732eb97d31a118bc3  50_CODE/c1_av2/c1_transfer_apply_v01.py  entry:c1_transfer_apply
299922d21908567d1c4c4153a88da5245548fee0842eeaca46347c69806520b4  50_CODE/c1_av2/c1_folds_v03.py  entry:c1_folds
6b1a156da8086fa02441796f97faea1737b5cb5884148b0426b38ced5056b736  50_CODE/c1_av2/c1_freeze_v07.py  entry:c1_freeze
8f00f5358aa60c5d654a1aa95bcf39e8bde34400db20d9ccb1c439af9d6675cd  50_CODE/c1_av2/c1_quarantine_v03.py  entry:c1_quarantine
00c193343c9a542bbf722247e9a1fdba8cc436a04d1bb8f82c44f7da86d34f12  50_CODE/c1_av2/c1_tpp_envcheck_v01.py  entry:tpp_envcheck
c3056518897a7d4d8728c5db5db1bccb87db174721b395fca5a1b9ebb7c47d41  50_CODE/av2/av2_cache_stageB_v06.py  entry:stageB
dfc7b8cface55b2234e6173a96eb68ecf2b906b6cba808d74c482faa551a65e3  50_CODE/k8/k8_items_v08.py  entry:k8_items
1cf461361a717e03ef84fbec5767d3573a2558d633464ee79239f9626e2331ca  50_CODE/tpp/tpp_keys_v03.py  entry:tpp_keys
1c640a8b1d72d4d070f22f53b3f687525f2c74f92c905f726075a857acfc6442  50_CODE/tpp/tpp_run_v03.py  entry:tpp_run
a6d4254e10fafd20fb03f02f7a0ce1ee8b45555de2499998d56e4d6a4766b7e5  50_CODE/c1_av2/c1_analyse_v01.py  module
1765b2cb0f5859ba8f28d65c9a6554e91902d7877ba0f3f5a8072f4baf06ed9d  50_CODE/c1_av2/c1_analyse_v02.py  module
8981e11ebdaf89839ae727c9356355141d33b41421b0d4e3a32350fd95288bc6  50_CODE/c1_av2/c1_analyse_v03.py  module
f37c8fb4c1900d9a1a7fc833cee94872907fbdfe32045fe5acea65b05d98b15c  50_CODE/c1_av2/c1_analyse_v05.py  module
bda232b92a1af7256b8680c6c9f799631802954ccb6a67540908e26a894b0788  50_CODE/c1_av2/c1_analyse_v06.py  module
d9699f39b058202155d26cd436be46ced72157bb367b7c0a6e5e58fc6d8bc3de  50_CODE/c1_av2/c1_analyse_v07.py  module
4919ed20818b46cee13c3511444cc62ba44086b329fa2b98ffc0f17508a31494  50_CODE/c1_av2/c1_crc_exact_v01.py  module
d706a5e2969e17a7ecb232019f0fe478cab97316a2563bbd828725a48655bd7a  50_CODE/c1_av2/c1_e0_v01.py  module
d144bb1c0cc637c4ea4b7e7a59a6940700a637fee544511979eb283d18a52fd1  50_CODE/c1_av2/c1_e0_v02.py  module
3a2057849767fb32da6a793d53fa61a6eea0b47068319631030d9005a09d0d92  50_CODE/c1_av2/c1_e0_v03.py  module
420cf639fc92f3f087f9a39d97981a96b5e3e10d431193a915fa97f3e2e5dcbf  50_CODE/c1_av2/c1_fit_v02.py  module
58ea4a9246ed74fee2483309e8890a348f20fe3859f4a33367bc061aa2c834d9  50_CODE/c1_av2/c1_folds_v01.py  module
b38605675bdc217e8a40ab1f4deb0cfca662711b56f9d0726e5d58646a19ec1c  50_CODE/c1_av2/c1_folds_v02.py  module
fa84cafc558039af9e12897601bf58025dafba6f037dbc8bb550727571367408  50_CODE/c1_av2/c1_freeze_v03.py  module
48bc6bcd4f6d500e0831917dcfdd2a5f402d8bad880745efa939309bb3f41f47  50_CODE/c1_av2/c1_freeze_v04.py  module
edc7ba861759a6538dbfbfc390816fd59a581816c3954362607e52d402230025  50_CODE/c1_av2/c1_guard_v01.py  module
00d9bc42713ee3e58ce148d7961c5c1b73e8316628fb26166a1377281384c724  50_CODE/c1_av2/c1_guard_v02.py  module
ec6e7390e02fc357224d83329eee5f5267294bf053083d903b51e9aefb152408  50_CODE/c1_av2/c1_guard_v03.py  module
56b65e908b5007eff4039fb5d265c231828effc8b05dccba982c8cf6d0c3cd4c  50_CODE/c1_av2/c1_guard_v04.py  module
cd40e98ac1d6d4f559ea3a95075dcb361f4779e688947356e66e880853a87608  50_CODE/c1_av2/c1_guard_v05.py  module
c5e3f8f1d51a1ea8ad63b84de8f3310e087af15730381eb7d88b75300bdb197f  50_CODE/c1_av2/c1_guard_v06.py  module
c882a61f00ad4b7d91c57c4698cb1009718d3985101be7ad7bb35e597cbf9a0d  50_CODE/c1_av2/c1_h8_v01.py  module
429658bb5165b9977f6a90be4a708aefc32f992815f94dac4bc1831055a09ca7  50_CODE/c1_av2/c1_h8_v02.py  module
0976db441e19fd80ce4f9d72e1a22b0ff4d10d69ab90d74e3109ad21129b7877  50_CODE/c1_av2/c1_legacy_refuse_v01.py  module
bffabac46c40d637f5af649649c3b0f41e73cc47e31f2f858a5b30bdd6985e84  50_CODE/c1_av2/c1_mstage_v01.py  module
0485fd7dc2323cc28f18fb171d6d9a70db2af11cda924d43f6447f6798785c03  50_CODE/c1_av2/c1_mstage_v02.py  module
392202b178e7b756bbb13970024831e42837fd545adf23f8084d40dff2ce96f7  50_CODE/c1_av2/c1_predarm_v01.py  module
6fdebcb5a6de6dea362ee55192fa0c2b941435ae8f459144de38434aabdaecad  50_CODE/c1_av2/c1_predarm_v02.py  module
997060cfeedbbdc9e29dda87931b58249639cb030ab949987d1d8f8dce8891a2  50_CODE/c1_av2/c1_predarm_v03.py  module
3751b773c7d267e5c20003cddf9efc843a6a0263c2a97972bc84b8dd1ab5c6aa  50_CODE/c1_av2/c1_predarm_v04.py  module
e8f38acfc054596d073261802dd97a8f7db4b456f442ed093e366a9c85997a3f  50_CODE/c1_av2/c1_predarm_v05.py  module
9e39a4aba822fdf74181adc9b2e92f97886cbf497640d3df586462abb571bec8  50_CODE/c1_av2/c1_run_v02.py  module
22c7c50947cd5ca9633b194303f8579b68910a8a868d505a05331cbf66fd5dd3  50_CODE/c1_av2/c1_power_counts_v01.py  module
8f78393519d80572730c6babcb52e8133faaaab03981aa44d9e82f0cfb536b6b  50_CODE/c1_av2/c1_power_counts_v02.py  module
38fdb281815185e8ccb53fcc6d505fee364452c00be2dfa3fcb1ea4b12696270  50_CODE/c1_av2/c1_power_counts_v03.py  module
8dd60b800d490584737c0c40a5d68a934897884761c837392584afbb06868d42  50_CODE/c1_av2/c1_power_counts_v04.py  module
074cf798e563189fe0c0db77edf099317014d37e6bc89771b3036f9e7b597215  50_CODE/c1_av2/c1_rules_v01.py  module
9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61  50_CODE/k6/k6_analyse_v02.py  module
2821511f35e51520fc7b724dd5dc9b9ab7d02c50ac9acd38c98d79b64a982cf3  50_CODE/k6/k6_run_v02.py  module
257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4  50_CODE/k6/k6_sim_v02.py  module
05b835a020b809265fa75a7d1d7a2f8995fa7b04f48b9075677114c14ec2857d  50_CODE/k7/k7_fit_v01.py  module
edd721dac4612b023e3e77b102bd1844cd74a700be6056de68072c0ea86fad94  50_CODE/k8/k8_analyse_v04.py  module
473e29ba2cc8a730cc80275fd3d98ceaa1d699923b33667d2232268dee130887  50_CODE/k8/k8_joint_fit_v02.py  module
03881acdbf28e53afbe6c5f4de8aeb352e14ddd43ad9f2feff6c67217a528e01  50_CODE/k8/k8_sim_v04.py  module
67bf52a950e299d3775ee9f8b357dceb674a14ac2689d087a8ef1af189ec633f  50_CODE/m/m_data_v04.py  module
6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5  50_CODE/m/m_lib_v04.py  module
bfe6047b48902b195361a409f38cefeb7b0c451628918488e7186cfac5a20396  50_CODE/m/m_run_v04.py  module
5c044afb346d17ea5f38d5399c1f19732aa005d877203e84e54b8f4ab810cc92  50_CODE/tpp/tpp_analyse_v01.py  module
32942ff8c1c08a6c633648587102fbf2389f5b510dcc05c7d5817ae572033c7f  50_CODE/tpp/tpp_common_v01.py  module
a5e9d761d9bd335dac1494cf31c6ba53507d09ac2f29d79aa74f618fc5871c73  50_CODE/tpp/tpp_keys_v01.py  module
8f94cdbb619a3fb2e0e6439e049df1d9a9bdc33dbba4b8a16ac2f2405dfa1eb3  50_CODE/tpp/tpp_run_v01.py  module
abb60897e1bb3ed7446d5bd93ce5ad94845a8bb47b055026ded17036c1af5cbb  50_CODE/tpp/tpp_keys_v02.py  module
2204a6cefda73c4461ac3bf609a3fd219c1aea51d1861b981d7ffba545257bc9  50_CODE/tpp/tpp_run_v02.py  module
b59dd08a407b8907d93386e7b136af973a5889444c3a0c84053d3e8a4a42bf64  50_CODE/x1/x1_full_v02.py  module
9728e9f518e284e39e522c7252353f1342e7b9ffd682a742cd1eba9b646f8571  50_CODE/x1/x1_lib_v02.py  module
f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd  50_CODE/x1/x1_lib_v03.py  module
a2d613f047ae09e37fb03291ef635ce6ac3055d67e49346a7fac88333a128538  50_CODE/x1/x1_prefreeze_v02.py  module
7025ea878bff9b1b2ae8c8a0a2765e197b1d7869dd16e468b28a2f00dfe53c00  50_CODE/x1/x2_full_v02.py  module
020bc1da57b78397d643785b06d7521024d8d58792dd5e68a6db90fcd37c9af5  50_CODE/c1_av2/tests/make_c1_run_v01.py  generator
e29d7475423c77e752d61c30a09cded1dd099862a174c1b1f7c2314d990e8766  50_CODE/c1_av2/tests/make_c1_run_v02.py  generator
8cf6ef8fbfba501c026674b451aee2a381e7c47eeffca85fe61df6b7308432a7  50_CODE/c1_av2/tests/make_c1_analyse_v02.py  generator
7a395665c3fe2da179d9a31712214c66937eba17c26dd9c08f30edc680245c0c  50_CODE/c1_av2/tests/make_av2_stageB_v02.py  generator
03dde4862f34ff3c6e6403135be78b4e12eef30022fb3d342e87034a4edc7762  50_CODE/c1_av2/tests/make_av2_stageB_v03.py  generator
2ad212cedc8c81ffb913a25fbfcc50bc43a3f48fc3a53d450bcd6c84ae2a36cd  50_CODE/c1_av2/tests/make_av2_stageB_v04.py  generator
fb7ba0539153636e989c8aa63779445d2a28abc15fe0a6b6e061708e1f50761d  50_CODE/c1_av2/tests/make_av2_stageB_v05.py  generator
2f64fc0446aafcec93d6d66f420bccdd68b4b85017dc22be9b5aae14491b1e65  50_CODE/c1_av2/tests/make_av2_stageB_v06.py  generator
25d6481dcc2c99fcb3f4d4fc355aaed382301c23785b870f03de5795b32b1c4b  50_CODE/c1_av2/tests/make_k8_items_v05.py  generator
ad1dc93a19f7cd4f94b9f6cedb1faba487fe478fd7fa2c455962f485172b9092  50_CODE/c1_av2/tests/make_k8_items_v06.py  generator
56cda451a5d51e3e8bd7f4f42b5a48f87dee384c9eb29614d4dab548a6e6ce8b  50_CODE/c1_av2/tests/make_k8_items_v07.py  generator
0f4a8cefe493cab2d09fc12e5aa84c29c10c4b7bd7580afbb23f00ebc4679471  50_CODE/c1_av2/tests/make_k8_items_v08.py  generator
da55af73d271b46c6cd9c08e537874df60acea01e213943c2fcdb47f48da3213  50_CODE/c1_av2/tests/make_av2_stageA_v02.py  generator
badd72d3094a25da20b881aaeeb3ab9cc23231f29e05b78a2cf866b98ccf9e9d  50_CODE/k8/tests/make_k8_joint_v04.py  generator
98376598e3671ec96d2cdb05600dd565a021e73ec85b81330b9202ca78f1f3c8  50_CODE/k8/k8_run_v04.py  source
3c5b064d61aa7fa36529537346248e690846a68d5fbacf0ac221b7a5a7d98541  50_CODE/c1_av2/c1_run_v01.py  source
03cd1108353a9e68ab8da074455ba9eef742f0baa880455d4c996741cc885f50  50_CODE/av2/av2_cache_stageB_v01.py  source
49771f4356dc1677b5347fd26470a1ee433a41c2a44e8c4d924386bdd9efb111  50_CODE/av2/av2_cache_stageB_v02.py  source
9d7994f6a60b0a77484a82883dc0d39e40b6e62ee01a543d987c09bf07dc8b77  50_CODE/av2/av2_cache_stageB_v03.py  source
69c6d1f456052d8a7df17ddce4c87df5eeaa914c1bca4aa1a8500f69e6fb08c8  50_CODE/av2/av2_cache_stageB_v04.py  source
b81ab3eb052dcd3de54d60ac5a022d247a71b72a8bc0a69a0a8f21078ce48de7  50_CODE/av2/av2_cache_stageB_v05.py  source
d646f4205298781b49f78dad4b71a900604076e76fca7fc97b36a858c4ccf2d5  50_CODE/k8/k8_sim_v02.py  source
e5e1e03779427da30f4be190779252c8353e0854bcad82593d8c281b4fdc1183  50_CODE/k8/k8_run_v02.py  source
868e4ff028e2e04072b2508dad57c0c3b29b4c030b34f9acff350ce7083c810a  50_CODE/k8/k8_analyse_v03.py  source
f341ac1542c3c247bae6154b58d593d33f30191bacaf6eb6efa18a1d63ef855e  50_CODE/k8/k8_items_v05.py  source
c03fd53e7c9c00d39aa776405aada656827372ca4e4ebec7ad337fc42c38eff5  50_CODE/k8/k8_items_v06.py  source
8fd76c0964227d1095c4db4882df3f9c078f0388781aefa6969c12ee2b25f999  50_CODE/k8/k8_items_v07.py  source
dcb13120d067f57f4c5be46bc9f7f0b8ef4b5bfe9597a326cbfd62d64f1c9ce5  50_CODE/av2/run_av2_c1_equiv_gt_v01.sh  source
f03b0130570278486df8b5cb9418da83fc4145139472846b38e033682cb945eb  50_CODE/av2/run_av2_c1_equiv_trk_v01.sh  source
e7cff37d159e5c811ab12c7f28323007072963cb87ec28f81625e8ab3d26d327  50_CODE/av2/run_av2_c1_queue_v01.sh  source
bc48d28801af1036b0118d2e1580ffa03ee8ac7f5f23133822e416a8fc0de437  50_CODE/k8/k8_items_v02.py  builder
55f1625a0a2e9052e25dd2eb6f1f8c448921d55a41282411e1c4d806fecfa3cd  50_CODE/k8/k8_items_v04.py  builder
79b6f44104a09a5b685723552e5484138290669483124509ffbac1369a26da16  50_CODE/av2/av2_track_v01.py  builder
8cd2fac9aebdbcc353098e41afa59277d819e2c611ab1ca595c1b61a8f364b8e  50_CODE/av2/av2_tracker_input_v01.py  builder
d1b76f547759548fa7c474f94e7f14482704347633a50bd9091b1c387d02a127  50_CODE/av2/av2_common_v01.py  builder
97e3ea8264483594b2437bc983573eae93d6721b51cd410a1759ce87245214f0  50_CODE/av2/av2_ab3dmot_v04.py  builder
69a8dd85f1b48cc5cb3f83e2ba750013beb568723d745b3510f4dafdace8a7da  50_CODE/av2/av2_gt_prep_v01.py  builder
9b28fad0303476c403ff89b439bedcef2283ca0db830e45b784a5e2d0c7d5bca  50_CODE/av2/av2_horizon_prep_v01.py  builder
13b8344b81d1cbea66b2b7fba8664973455062eb2adec9abfeb30b3ddd6f5658  50_CODE/av2/av2_ego_prep_v01.py  builder
88e1848bd27c2dce8d93e0123376749b07fe8e5fc6375d35f057db5ba3acb3bf  50_CODE/av2/av2_cache_stageA_v01.py  builder
e4495fe9ade9dadc8bf35ee9513642ec71317568bed4aa4315ad4823167fe986  50_CODE/av2/av2_cache_stageA_v02.py  builder
ea8180e73e80c69108763b95d32143f2adb0fcbba56953dd8ab0476b3b5de36b  50_CODE/av2/av2_feather_v01.py  builder
34319316aaea4bf1352345fbb8e556c8e7df7fe28c38148b27d83e72ee62e56b  50_CODE/av2/av2_counts_v02.py  builder
b55f767cc533f1f3b526535d96a8387838545eacef054a54b772066c60fdf675  50_CODE/x1/x1_export_v06.py  builder
56f6d883810c997879360d963adb18b095c5b365211608b8b7b800180b8d1877  50_CODE/c1_av2/c1_av2_scene_map_v01.py  builder
ae4a95a186573e1310e9f862c2afb0a2dfd606bc8af0e874a627c561411d95e6  50_CODE/c1_av2/c1_av2_gt_inventory_v01.py  builder
df9b0400cdbd4df59f1f3983add9e72e494762cd3cf20a91ee25fcdb7614bc0b  50_CODE/c1_av2/c1_av2_provenance_v01.py  builder
d2b9907cd6ffd503bf2b45ab2fde19c0c3a8eab4cecf6ec3a386e1cadeac6bdc  50_CODE/c1_av2/c1_power_counts_v05.py  builder
cfee915dce66c30915bc657a6147998ee67b995064ddab391f411566af3db686  50_CODE/av2/av2_common_v02.py  builder
7d6baf5b90df399d3e5bd9176cafd337b8fa6596acdf229148444f2de70ab564  50_CODE/av2/av2_fetch_v05.py  builder
efda01cbc02942bc96f4ba03608c931b21790fab3d774314cf7d72e0baa7069a  50_CODE/av2/av2_c1_logs_v01.py  builder
10fc4964ac04eaf2a7e2585e38f7900af6f1166dbc584165a52c0dc38013a961  50_CODE/av2/av2_c1_frame_check_v01.py  builder
5cba8fb9d190ed39b45f1376192cf5eeea24205efac3bc8ff30bc7f4eef8ba77  50_CODE/av2/av2_gt_prep_v02.py  builder
037015f21dae83729725e097271ddf037cbea7ab054e62a596e48ea8b384089a  50_CODE/av2/av2_ego_prep_v02.py  builder
b236804f30864c9bceac8a72cd999b240045009bc3f7c7f96c4439091e5813af  50_CODE/av2/av2_tracker_input_v02.py  builder
0a9a0eb300de4cd58ddcddf661547953688a8cf639e81bf45eafa74ceee25eed  50_CODE/av2/av2_track_v02.py  builder
e4ea995048402403c7a553bd49e2ffe3a2f26e44238e83825972349a4aa59d54  50_CODE/av2/av2_ab3dmot_v05.py  builder
76cc6a9aa7f7ad0992ab3f449298755feb1eef413e7e83f8c8979ba9bc02e540  50_CODE/av2/av2_horizon_prep_v02.py  builder
75bac8577bf51b5d06f2a15391952765334f5c064309944fb2565c9286bef7a9  50_CODE/av2/av2_c1_gt_list_v01.py  builder
4a1a3459f3ea219b8da65ac1c63f3e7b5369661242e22680867a337fff7db2be  50_CODE/c1_av2/c1_freeze_v01.py  legacy
e5bfbb6e5f4ce8dafd92050d5a05f1d43eb524292e07c5cc80456941c87516e7  50_CODE/c1_av2/c1_freeze_v02.py  legacy
1afe6d595f998de16237f8fc9fd2363da37baa11c6595a82ee6279cb248deab5  50_CODE/c1_av2/tests/test_c1_v12.py  test
2398714275b91e02c42031f52d3e8da1c5bd7a1bf2c9b35a649f7aa99dceaa96  50_CODE/c1_av2/tests/test_c1_v01.py  test_module
5560e7739adbc1908d11505f1aeaa0ac154f56e26601dfa5e39c22ed9b075cd3  50_CODE/c1_av2/tests/test_c1_v02.py  test_module
b8614df5785e9074de32ca778b0868745cfa595b369fd032881759fb91b45ecf  50_CODE/c1_av2/tests/test_c1_v03.py  test_module
ae07d6a9d9b533a7ccfa3cf1640ce46fdc0a7ebebd6d12d5f3bbb10866297b9c  50_CODE/c1_av2/tests/test_c1_v04.py  test_module
f53d031a82b02b171dda8879d2d0eed6f228237b8e2e16c33fde572747dce391  50_CODE/c1_av2/tests/test_c1_v05.py  test_module
063d70952031c9faef67171eee029fc8fb1d8befb6ede8f6610dca3012a161a1  50_CODE/c1_av2/tests/test_c1_v06.py  test_module
42ed65c89e246f23b6f7fa714c35e9de6b83c8f95de153f93eda6d67cd258391  50_CODE/c1_av2/tests/test_c1_v07.py  test_module
025363ad29a0e9b03eb05a6b338840322c8351731ac29a53c629699da0d7654e  50_CODE/c1_av2/tests/test_c1_v08.py  test_module
7c455b02f7f4cc97ae93cff48eb19bb5f92f39fea56445ce970e69c725507bd8  50_CODE/c1_av2/tests/test_c1_v09.py  test_module
e5097c2fabed18cf46f75448ab20795548741e692c5b1a4abccbea2e445d4c0f  50_CODE/c1_av2/tests/test_c1_v10.py  test_module
4265359dcaf373fbe66046de415118bda19d5006f08b3c8ed2a714a124c6736d  50_CODE/c1_av2/tests/test_c1_v11.py  test_module
847d31d744bcb9da803c8fbdc5399b284e2c2ed814032796230bd55829cc4e1e  50_CODE/c1_av2/tests/c1_reproduce_check_v01.py  test_module
c79f1639b7f75912c4a4944c3cebc927be9f4a061047ce9154a3f374c76f4585  50_CODE/c1_av2/tests/c1_standin_prep_v01.py  test_module
b889f9c5af4446ed6a4ffc3c3dd846817812618ed0541ef32b7af24367bb72fa  50_CODE/c1_av2/tests/freeze_probe_pass_v01.py  test_module
5744951776eded5d0bf1f931cc7a55f9cad64a0b6c3ff8c657c1bc8a0ff7223c  50_CODE/c1_av2/tests/freeze_probe_fail_v01.py  test_module
b77ab7214b1de96aacfa0226f8b23ea9dd5a2219d6457bd6af02ef2ac0e03925  50_CODE/c1_av2/tests/freeze_probe_envcheck_v01.py  test_module
dc133766b0cc738da43394bda808c0e67e8259efe8b7ff375fffedcd133ca1fe  50_CODE/c1_av2/tests/c1_q1_standin_v01.py  test_module
7673eb7dd2c8e537ccea976acf8ba6a14a45c70c2603c7fbfc07ffc73c14b278  50_CODE/c1_av2/tests/c1_devreplay_v01.py  test_module
b4f445d58cd5bb7270193237b09f9cecd4862f2b640a57e9baa10e891e2cfb1b  50_CODE/tpp/tests/test_tpp_analyse_v01.py  test_module
6ad5652800828855cdeac725841d3b5575396092187f3c4f05d411932a949c82  50_CODE/av2/test_av2_port_v04_equiv_v01.py  test_module
4c85dbfdbad9ee1581567da264a31c3f7fee916ab88d2b9d2f649b1796e360b6  50_CODE/c1_av2/superseded_originals/README_ARCHIVE_v01.txt  archive
05664f204bd1d4971b98b797f2c7e75117e7ac1afc41269fb29035c77023e71c  50_CODE/c1_av2/superseded_originals/SHA256SUMS_gz_v01.txt  archive
d8adfe57a7ffc76d8ade159dc8b4147e8e022501defe9829911f157e4f834d83  50_CODE/c1_av2/superseded_originals/SHA256SUMS_superseded_originals_v01.txt  archive
6b764a26f2b2ce894b873b12b557c2e37d85c2612820909d8bf655f798b0ad4e  50_CODE/c1_av2/superseded_originals/apply_choice36_main_edits_v01.py  archive
2bd49b778311b0e7ad0fc1c51e962d2d900cad2d374309050e2b547d5f01c746  50_CODE/c1_av2/superseded_originals/c1_analyse_v01.py.gz  archive
e0e09ac57e9a19afd01911820e68209bd72ff1bef72bc8317dd495a1f75da33b  50_CODE/c1_av2/superseded_originals/c1_analyse_v02.py.gz  archive
8718095867a7858878a83055e795ecffbe770cdb68c54f976149994d53bc3ccb  50_CODE/c1_av2/superseded_originals/c1_analyse_v03.py.gz  archive
08e027db1c84f8ddaf4b607d8957d4a9aab8f013ca5199b6caf703b5ff41e307  50_CODE/c1_av2/superseded_originals/c1_e0_v01.py.gz  archive
f6e8f3479a1eae977e1bb062d6e2f3f1e7baf3df9e875f3cb504aeb0f2e10176  50_CODE/c1_av2/superseded_originals/c1_fit_v02.py.gz  archive
362649a23392dacb37cccf402ba9c9fc436a7588ee8cbe4ba3fda5704c88e4a3  50_CODE/c1_av2/superseded_originals/c1_freeze_v01.py.gz  archive
ba9762cdcb8306fe46f07de0764717e2fc0ece4a61caf075d064d0d533d63437  50_CODE/c1_av2/superseded_originals/c1_freeze_v02.py.gz  archive
79378d151fb193ae0c1b95266346859d0f1c5a4615ad26472c88cdb99adc728b  50_CODE/c1_av2/superseded_originals/c1_h8_v01.py.gz  archive
f0daf14b5826ff7482eb0ee251da4cbd3b7fed568f206d2389c44c49125661f5  50_CODE/c1_av2/superseded_originals/c1_h8_v02.py.gz  archive
27e88430081d014f8224a322cb861c47919892a9ef67616c4ff3b853894153b1  50_CODE/c1_av2/superseded_originals/c1_mstage_v01.py.gz  archive
a8ba39124aac84e782692d7984f64f5cdc0d0516ad86adc0ec4402a2f24cfa1c  50_CODE/c1_av2/superseded_originals/c1_mstage_v02.py.gz  archive
563a03533193f35d3dc218333b09c7cfdaa929bfbc151a99fd1d9347d8c72a98  50_CODE/c1_av2/superseded_originals/c1_predarm_v01.py.gz  archive
60da25dc6b1716dff04dc3523979be735b0c94c9e2a7c4f67d6f60327c430195  50_CODE/c1_av2/superseded_originals/c1_predarm_v02.py.gz  archive
8d1a219c5c13a6cb427595005625997f3acd47da82eb6a258c0405407760c937  50_CODE/c1_av2/superseded_originals/c1_run_v01.py.gz  archive
2aa66a9581eda83f83e16d78c273f150a0a335af9adca476ae8f233c48ffdcfe  50_CODE/c1_av2/superseded_originals/c1_run_v02.py.gz  archive
4c85dbfdbad9ee1581567da264a31c3f7fee916ab88d2b9d2f649b1796e360b6  50_CODE/av2/superseded_originals/README_ARCHIVE_v01.txt  archive
d0ebe0957bd1d78e0ecf07b285869ae400e53ccbffa60e4625937c08680c3b67  50_CODE/av2/superseded_originals/SHA256SUMS_gz_v01.txt  archive
9fcaee78f18f97c64a32aa703fdd82e05d5a624db932edeecb8d9d56cbbc8fd3  50_CODE/av2/superseded_originals/SHA256SUMS_superseded_originals_v01.txt  archive
d78ce5924611b074aee4e8fabe8d17e2d640c34b1e73f60caae61f1f1f047556  50_CODE/av2/superseded_originals/av2_cache_stageB_v01.py.gz  archive
3eb9b9e81110a2bf7ccbf17b36488b7870be60edc322aa3fa0acf82a6e0e5557  50_CODE/av2/superseded_originals/av2_cache_stageB_v02.py.gz  archive
```

## Not bound (superseded; `c1_freeze_v07` refuses them in the block)

```
superseded  50_CODE/c1_av2/c1_analyse_v04.py
superseded  50_CODE/c1_av2/c1_fit_v01.py
superseded  50_CODE/c1_av2/c1_fit_v03.py
superseded  50_CODE/c1_av2/c1_fit_v04.py
superseded  50_CODE/c1_av2/c1_fit_v05.py
superseded  50_CODE/c1_av2/c1_run_v03.py
superseded  50_CODE/c1_av2/c1_run_v04.py
superseded  50_CODE/c1_av2/c1_run_v05.py
superseded  50_CODE/c1_av2/c1_mstage_v03.py
superseded  50_CODE/c1_av2/c1_mstage_v04.py
superseded  50_CODE/c1_av2/c1_mstage_v05.py
superseded  50_CODE/c1_av2/c1_h8_v03.py
superseded  50_CODE/c1_av2/c1_h8_v04.py
superseded  50_CODE/c1_av2/c1_h8_v05.py
superseded  50_CODE/c1_av2/c1_e0_v04.py
superseded  50_CODE/c1_av2/c1_freeze_v05.py
superseded  50_CODE/c1_av2/c1_freeze_v06.py
superseded  50_CODE/c1_av2/c1_quarantine_v01.py
superseded  50_CODE/c1_av2/c1_quarantine_v02.py
superseded  50_CODE/c1_av2/c1_analyse_v08.py
superseded  50_CODE/c1_av2/c1_qcnet_summary_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v02.py
superseded  50_CODE/c1_av2/c1_rehearsal_v03.py
superseded  50_CODE/c1_av2/c1_rehearsal_v04.py
superseded  50_CODE/c1_av2/c1_rehearsal_v05.py
superseded  50_CODE/c1_av2/c1_rehearsal_v06.py
superseded  50_CODE/c1_av2/c1_rehearsal_v07.py
superseded  50_CODE/c1_av2/c1_predarm_v06.py
superseded  50_CODE/c1_av2/run_c1_standin_v01.sh
```

`c1_rehearsal_v08.py` (the rehearsal driver), `c1_power_counts_v01`–`v04` (bound as modules of `c1_power_counts_v05`) and the unbound tools `av2_track_metrics_v04`, `av2_hota_v04`, `av2_c1_tables_v01` and `av2_c1_velocity_probe_v01` complete the picture.
