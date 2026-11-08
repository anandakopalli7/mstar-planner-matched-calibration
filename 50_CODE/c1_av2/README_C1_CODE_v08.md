# C1 code v08: R17e's fixes under D16 v23 Choice 44 and v24 Choice 45 (5 Nov 2026)

README v01 to v07 are kept unchanged. This README answers `70_TESTS/R17E_C1_CODE_V07_CHECK_v01.md` (no blockers, 5 majors, 8 minors) as D16 v23 Choice 44 decides, with v24 Choice 45(a) and (c). It lists every bound file with its role (154 files: entry 16, module 52, generator 14, source 13, builder 15, legacy 2, test 1, test_module 17, archive 24).

**Guard version.** The v08 entry points use `c1_guard_v05.py`, which imports `c1_guard_v04` and, through it, `c1_guard_v03`.
- `c1_guard_v02.py` (`00d9bc42…`) and `c1_crc_exact_v01.py` (`4919ed20…`) are unchanged.
- No file bound by the frozen X1, X2, M or D17 plans was edited (`x1_full_v02`, `x2_full_v02` and `m_run_v04` are bound here as modules, unchanged).
- No superseded file was edited again (m6). No Choice 36 edit was made in v08.

**Results.** `70_TESTS/c1_v01/C1_V08_TEST_STATUS.json` holds the test and rehearsal results. It is written after this README and records this README's hash. The rehearsal on this README is in `70_TESTS/c1_v01/rehearsal150_v08/`.

## Fixes, by item

| R17e / D16 | Fix | Test (`test_c1_v11`) |
|---|---|---|
| **M-A** every prepared ground truth (44a, 45b) | **`c1_quarantine_v02`** takes the union of the stage-A manifests passed, every AV2 stage-A `MANIFEST.json` under `30_DATA` (to 4 folder levels), and the files given with `--extra` (each recorded in the quarantine manifest as kind `extra`, with its path, hash and size). For every recorded hash it hashes every workspace file of the same size, skipping `50_CODE/env/`, the quarantine folder and banned folder names, and treats every match alike: one gzip member, verified to decompress to the recorded bytes, then every plain copy removed. **`c1_freeze_v06`** takes the same union, plus the manifest's `extra` members and its own `--extra`. It refuses a plain file at a recorded path, a plain `--extra` file, a recorded hash without a member, and any plain file anywhere in the workspace whose hash equals a recorded one. | **TREE:** R17e **E2** as a refusal: `c1_quarantine_v01` with the given manifests leaves an older manifest's ground truth plain, and `c1_freeze_v06` refuses it. Then `c1_quarantine_v02`: the dry run changes nothing; the union finds the older manifest; the `--extra` file is quarantined; a renamed stray copy is found by hash and removed; a copy under `50_CODE/env/` is left; a rerun is idempotent; a tampered file is refused; a pod path is found. The freeze then passes. R17e **E3** as a refusal: `x2_full_v02` can no longer run on the older ground truth. **Real tree, dry run** (`70_TESTS/c1_v01/quarantine_v02_real_dry_run/dry_run_v01.txt`): the five 150-log manifests and the CenterPoint detection ground truth are found, 2 hashes, nothing written. |
| **M-B** the narrowed claim (44b) | The claim below replaces Choice 42(b)'s text. | — |
| **M-C** one freeze (44c) | `c1_freeze_v06` refuses **any** freeze while the stage-B log, a stage-B manifest, or a run-log line from a role other than `entry:c1_e0`, `entry:c1_folds` and `entry:c1_freeze` exists, or while the run log's chain is broken. `--amend` is also refused when the deposit record exists or any `30_DATA/av2_cache_stageB_*` folder exists. In `test_c1_v11`, `freeze_skip()` relaxes **only** the "hash log absent" assertion and the earlier suites' real-log groups. The suite always asserts that there is no deposit record, no stage-B log and no non-exempt run-log line. The quarantine folder may exist, because it precedes the freeze. | **TREE:** `--amend` passes with only an exempt (E⁰) run-log line, and its suite passes through `C1_FREEZE_LOG_SHA256` while the same suite run directly fails. It is refused once the record exists. R17e **E7** as a refusal: after an H8 outcome, deleting the record does not reopen `--amend`. It is also refused after stage B. **FRZ6:** refused while a stage-B folder exists. |
| **M-D** Q1 not tested (44d, 45c) | **`c1_analyse_v08`** refuses a config with a `q1` entry. Its decision reports Q1 as "not tested", in its own block, with Choice 44(d)'s two reasons, not as "tables missing", and not among the missing inputs. C1_verdict, gate_H1, H9 and family S come from `c1_analyse_v06.decide_all` unchanged. **`c1_freeze_v06`** refuses a config with `q1`, a config without `h8_units = folds`, and a freeze without `data:e0_plan` or `data:scene_json`. **`c1_predarm_v06`** refuses `--q1-only` and every QCNet option. The Q1 route is not extended. | **MD:** C1_verdict, gate_H1, family_S and H9 are byte-identical to `c1_analyse_v07`'s, with a Q1 table and without one, under gate H1 passed and failed. Q1 is "not tested" with the two reasons. A `q1` config is refused (`decide_all` and `main`). The predictor arm refuses QCNet. **FRZ6:** the four config refusals. **Rehearsal:** Q1 "not tested" with the reasons. |
| **M-E** environments (44e, 45a) | `c1_guard_v05.env_check` compares a `tpp_keys_v03` record with **FROZEN_ENV** (canmot310: python, numpy) and a `tpp_run_v03` record with **FROZEN_ENV_TPP** (tpp38: python, numpy, torch). `c1_predarm_v06` uses it and requires both blocks under a plan. **`c1_tpp_envcheck_v01`** (Choice 45a) checks a *dry* wrapper record before any key or run is made, on the laptop or a pod. `--write-dry` runs under the target interpreter, Python 3.8 included. `--check` compares the record with the frozen plan. `--python` does both. | **ME**, on **real** wrapper records made in the test: one-scene keys under canmot310 and under tpp38 (byte-identical), and a run under tpp38. The canmot310 keys pass and the tpp38 keys are refused; the tpp38 run passes; a canmot310 record is refused as a run. `c1_tpp_envcheck_v01 --python` gives ok for canmot310 keys and tpp38 runs, and refuses tpp38 keys and canmot310 runs. A dry record written under tpp38 passes as a run and is refused as keys. |
| **m1** run log (44f) | `c1_guard_v05.guard()` writes a **"start"** line on AV2 before the entry point reads any ground truth or table. `run_log_append()` writes the **"done"** line with the output hashes. Every line is one JSON object whose `prev_sha256` is the SHA-256 of the previous line's bytes (64 zeros for the first). Writes are binary and fsynced, under a lock file, after the whole chain is verified. **`c1_analyse_v08`** records the run log's hash, line count and last-line hash at start. It requires a "done" line with the file's SHA-256 for every table it consumes (method stage, H8, H9, descriptive H9) and every route's run record. A table without one is not provenance-valid; a run record without one is a route problem; a broken chain refuses the analysis. | **RUNLOG:** a changed, deleted or unchained line, or a truncated last line, is refused (also for the next write); two concurrent writers keep the chain; non-exempt lines are counted; `logged_check` finds a logged table and misses another. **TREE:** H8 writes chained start and done lines, and the done line holds the output hash; a refused rerun leaves its start line; stage B writes start and done lines. `c1_analyse_v08 --c1` on the AV2 stand-in records the run log and accepts the logged H8 table; once the table's bytes change, the H8 table is no longer provenance-valid. |
| **m2** deposit (44f) | `check_deposit` refuses a `registration` equal to the project in `40_PROTOCOL/OSF_PROJECT_RECORD_v01.txt` (`eumj8`) as a URL or a DOI, in any case. It refuses a record when the plan's hash-log line has no parsable time ("frozen" or "AMENDED", then `YYYY-MM-DD HH:MM:SS UTC`). | **G5:** the project URL (with and without the slash, upper case) and the project DOI are refused. A hand-written plan line is refused, through `guard()`. PB4's cases are refused, and every refusal names `OSF_DEPOSIT_GUIDE_v02.md`. **TREE:** a record naming the project is refused. |
| **m4** AV2 `scene.json` (44f) | **`c1_av2_scene_map_v01`** (bound builder) writes `[{"name": u, "log_token": log}]` for every unit of the given AV2 stage-A manifests, where `log` is the manifest's own log. `av2_cache_stageA_v02` records log = scenario id, so on AV2 this is `[{"name": u, "log_token": u}]`. It refuses an existing output, a nuScenes manifest and two logs for one unit. On AV2, `c1_freeze_v06` checks that the map gives every fold unit its stage-A log. | **SCENEMAP**; **TREE** (the tree's `scene.json` is built by it; H8 checks 50 units). |
| **m6** stale messages (44f) | Stated here only. The Choice 36 refusals in `c1_freeze_v01` and `c1_freeze_v02` say "Use c1_freeze_v04"; the freeze tool is now `c1_freeze_v06`. `c1_analyse_v06 --standin` accepts an AV2 folds config, but it finds no AV2 run to analyse, because its stand-in route reads only nuScenes runs. These files are not edited again. | — |
| **m7** temporary ground truth (44f) | `guard()` first sweeps stale `c1_gt_*` folders from the temporary directory: a folder whose process has ended (the pid is in its name, `c1_gt_<pid>_*`, as `c1_guard_v05.materialise_quarantined` writes it), or a pid-less (v04-style) folder older than 10 minutes. | **SWEEP** |
| **m3, m8, m5** | m3 and m8 are moot under 44(d). m5 is plan text (one 375-unit ground-truth file; command order step 2). | — |
| **41(a)** blocks | As v07: only empty HASHES and ROLES blocks may be drafted, and after the freeze each of the five blocks appears once. | **FRZ6**, **TREE**; the rehearsal freezes a slot-filled copy of the plan v07b text, or of the v06 draft if v07b is not on disk, and checks its blocks. |

**Also re-run:** every group of the earlier suites v01–v10, each in its own process (`test_c1_v11` LEGACY). This includes R17c's P1–P7 (v09) and R17d's PB1 and P2b (v10 TREE). Four kinds are skipped by rule:
- groups that compare generators with the edited live files (v01 GEN, v02 GEN2/FRZ, v03 GEN3, v06 FRZ3); `c1_freeze_v06` checks every generator on the archived originals;
- v08 LEGACY and v10 LEGACY, whose suites run here directly;
- v09 FRZ4 and v10 FRZ5, which freeze README v06 and v07. Their entry points are no longer the latest versions, so the old freeze tools now refuse them (Choice 34.7). **FRZ6** runs their cases on `c1_freeze_v06`.

## The narrowed claim (Choice 44b; replaces Choice 42b's text, for plan §11 and the paper)

> The C1 pipeline's entry points refuse to compute any AV2 outcome before the freeze, and any outcome after k before the external registration is recorded. Programs of the earlier nuScenes studies, and the public AV2 annotations, were not technically barred. The prepared ground-truth files were built and hashed at stage A before the freeze, and quarantined at the freeze. The embargoed OSF registration was made after that and before stage B, the only step at which the C1 pipeline joins ground truth after k to the tracker outputs. The run log records runs of the C1 entry points only, so it is no protection against the programs this claim concedes. The stronger answer to "was the analysis run more than once" is determinism: fixed seeds and a frozen configuration.

## Command order (AV2, for the lead)

Use `../env/canmot310/Scripts/python.exe -B` (**canmot310**) from `50_CODE/c1_av2`, except where **tpp38** is named.

1. **Stage A** for the 375 logs, T1, T3 and AB3DMOT (`av2_cache_stageA_v02`), then the counts (S20a–S20c, S21, S22).
2. **One prepared ground-truth file** for exactly the 375 fold units (`av2_gt_prep_v01 --logs <375>`), named by every 375-log stage-A manifest (m5). E⁰, the quarantine, the method stage and H8 use it.
3. **Rule-0 metrics and the own detector's AP** (S20b) on the plain ground truth. These are tracker metrics only, never a C1 outcome. Every other prepared ground truth they need goes on the `--extra` list of steps 7 and 8 (Choice 45b).
4. **Folds:** `c1_folds_v03 --dataset av2 …`, then `--restrict-from` for `val` and for `held_out_train`.
5. **E⁰ before the quarantine:** `c1_e0_v05 --mode c1 --seed 20261114 --stageA-manifests …`.
6. **Scene map:** `c1_av2_scene_map_v01 --stageA-manifests <the 375-log manifests> --out <meta>/scene.json` (m4).
7. **Quarantine:** `c1_quarantine_v02 --stageA-manifests <every AV2 stage-A manifest> --extra 30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_gt_v01.feather <every other prepared ground truth> --dry-run`, then the same command without `--dry-run`. The 150-log manifests under `30_DATA` are found even if not passed.
8. **Freeze:** `c1_freeze_v06 … --folds-val150 … --folds-train225 … --extra <the same list> --data scene_json=<meta>/scene.json e0_plan=… <AV2 inputs> …`. The config holds `h8_units = folds` and no `q1`. The freeze runs `test_c1_v11` and writes the five blocks.
9. **OSF registration** (researcher, embargoed). Then the lead writes `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt`; `registration` is the registration, not the project `eumj8`.
10. **Stage B:** `av2_cache_stageB_v06 --stage-a … --gt 30_DATA/av2_gt_quarantine_v01/<member>.gz --frozen-plan … --tag <tracker>`.
11. **Items:** `k8_items_v08 --av2-stageB --plan`.
12. **Fits and runs:** `c1_fit_v06` (within, within on `folds_val150`, source), `c1_transfer_apply_v01`, `c1_run_v06` (four routes, plus `tab`).
13. **Method stage:** `c1_mstage_v06 --av2-gt <member>.gz --av2-meta <meta> --folds …`.
14. **H8:** `c1_h8_v06 --gt <member>.gz --meta <meta> --folds …`.
15. **Trajectron++ on the laptop** (Choice 45a):
    - first `c1_tpp_envcheck_v01 --python ../env/canmot310/Scripts/python.exe --kind tpp_keys --plan <plan>`, then `--python ../env/tpp38/Scripts/python.exe --kind tpp_run`;
    - then `tpp_keys_v03` under **canmot310**, and `tpp_run_v03` under **tpp38** for seeds 20261102, 20261104 and 20261105, and for gt.
    - A pod may be used only if its dry record passes first. On the pod, run `python c1_tpp_envcheck_v01.py --write-dry dry.json`; then, on the laptop, run `c1_tpp_envcheck_v01 --check dry.json --kind tpp_keys|tpp_run --plan <plan>`. The pod's keys310 environment fails this check.
16. **Predictor arm:** `c1_predarm_v06` with all three seeds (no QCNet).
17. **Analysis:** `c1_analyse_v08 --c1 --plan` (Q1 is reported "not tested").
18. **Upload** `C1_RUN_LOG.txt` and `C1_STAGE_B_LOG.txt` to the OSF project with the results.

None of these takes `--hash-log` on AV2, and no AV2 output is ever overwritten. To verify the run log at any time: `python -B -c "import c1_guard_v05 as G; print(len(G.read_run_log()[0]))"`.

## Entry points (the plan's FROZEN_ROLES)

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v08.py` |
| `entry:c1_fit` | `c1_av2/c1_fit_v06.py` |
| `entry:c1_run` | `c1_av2/c1_run_v06.py` |
| `entry:c1_mstage` | `c1_av2/c1_mstage_v06.py` |
| `entry:c1_h8` | `c1_av2/c1_h8_v06.py` |
| `entry:c1_e0` | `c1_av2/c1_e0_v05.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v06.py` |
| `entry:c1_transfer_apply` | `c1_av2/c1_transfer_apply_v01.py` (unguarded by design, R17e §5) |
| `entry:c1_folds` | `c1_av2/c1_folds_v03.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v06.py` |
| `entry:c1_quarantine` | `c1_av2/c1_quarantine_v02.py` |
| `entry:tpp_envcheck` | `c1_av2/c1_tpp_envcheck_v01.py` (outcome-free, no guard) |
| `entry:stageB` | `av2/av2_cache_stageB_v06.py` (generated by `tests/make_av2_stageB_v06.py`) |
| `entry:k8_items` | `k8/k8_items_v08.py` (generated by `tests/make_k8_items_v08.py`) |
| `entry:tpp_keys` | `tpp/tpp_keys_v03.py` (canmot310) |
| `entry:tpp_run` | `tpp/tpp_run_v03.py` (tpp38) |

**New entry versions beyond the five names the plan author was given:**
- `c1_analyse_v08`, `c1_predarm_v06`, `c1_fit_v06`, `c1_run_v06`, `c1_mstage_v06`, `c1_h8_v06`, `c1_e0_v05`, `av2_cache_stageB_v06` and `k8_items_v08`. These are needed because every guarded entry point must write the chained start line (m1).
- `c1_tpp_envcheck_v01`, the dry-record check of Choice 45(a).
- `entry:c1_qcnet_summary` is gone; Q1 is not tested. The fit, run, method-stage, H8 and E⁰ versions are their v07 predecessors with only the guard changed.

## Limits

- **Deleting the run log as well reopens `--amend` in code (44c).** What then remains is the second OSF registration and the deviation log. Hand-forged JSON tables or run-log lines with a recomputed chain also pass. The protection against deliberate forgery is the OSF registration and the uploaded logs.
- **The hash scan finds only recorded hashes.** It finds the stage-A manifests' ground truths and the `--extra` files, by any name, anywhere in the workspace except `50_CODE/env/` and banned folder names. A ground truth that was prepared but not recorded, or a modified copy, is not found; hence Choice 45(b)'s `--extra` rule. Copies outside the workspace (pods, other folders) are the lead's to delete. The public `annotations.feather` files stay outside the quarantine, as the claim states.
- **What the run log records.** It records runs of the C1 entry points only. Before the guard, an entry point reads only unit names or dataset tags, to find the dataset. A refused or killed run leaves its "start" line without a "done" line. A "done" line lists the outputs that exist at the end.
- **Q1** is not tested in C1. `c1_qcnet_summary_v01` and `c1_predarm_v05 --q1-only` remain on disk, unbound, and are refused by role under a v08 plan. Any QCNet result is exploratory and labelled so (44d).
- **The temporary ground truth.** A pid-less `c1_gt_*` folder (from v07 code) is swept only after 10 minutes. A folder whose pid has been reused by a live process is kept.
- **The rehearsal is a stand-in.** It uses nuScenes validation scenes as "AV2", T1's data as AB3DMOT's, and no run log, deposit or quarantine (nuScenes is exempt). The freeze's ground-truth scan there covers its own `--data-root`. The AV2 paths (quarantine, run log, deposit, stage B, scene map) are tested in the copy tree on R17d's AV2-tagged stand-in.

## Bound files (154; `<sha256>  <path>  <role>`)

```
8bbebcd6cd31c57bee80381edd7274326ca5edde6dd305a258617abe2cd70cef  50_CODE/c1_av2/c1_analyse_v08.py  entry:c1_analyse
82e1eb4ab52d044a7e47dcb5f4b41d84a536421523956f90c401236dce0d3190  50_CODE/c1_av2/c1_fit_v06.py  entry:c1_fit
77967094aecd19a76363569e336c359d0f697182dd343614ef8e00da761f72b6  50_CODE/c1_av2/c1_run_v06.py  entry:c1_run
1e1477ff788e708ce33a401c6916fdb4c4fd924c91ef494524bcf0a131dda89f  50_CODE/c1_av2/c1_mstage_v06.py  entry:c1_mstage
101a47acb78eb00f83ec1afa6a8ab2469d5ab32d246fa8bfb63e311f4142c026  50_CODE/c1_av2/c1_h8_v06.py  entry:c1_h8
8f1312a373a40ca82a020d37ee46c5904808c8f139683e1871868035382c438e  50_CODE/c1_av2/c1_e0_v05.py  entry:c1_e0
4e61e9553cf6973ec0e5093c29f1e2ca928b00108e1251ebd2701e17e42dda45  50_CODE/c1_av2/c1_predarm_v06.py  entry:c1_predarm
9c909b9ba27ac207aa2653ec49963403f5fe59bad51d3e5732eb97d31a118bc3  50_CODE/c1_av2/c1_transfer_apply_v01.py  entry:c1_transfer_apply
299922d21908567d1c4c4153a88da5245548fee0842eeaca46347c69806520b4  50_CODE/c1_av2/c1_folds_v03.py  entry:c1_folds
3fbcdff087f20974bff7e56088eebe6bc08c16ab677b9a0f97381b35e53dad38  50_CODE/c1_av2/c1_freeze_v06.py  entry:c1_freeze
3d6f6bf4704d75bfe94b559472684758ce6ed5f8be82c237ec12b606120cf063  50_CODE/c1_av2/c1_quarantine_v02.py  entry:c1_quarantine
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
4a1a3459f3ea219b8da65ac1c63f3e7b5369661242e22680867a337fff7db2be  50_CODE/c1_av2/c1_freeze_v01.py  legacy
e5bfbb6e5f4ce8dafd92050d5a05f1d43eb524292e07c5cc80456941c87516e7  50_CODE/c1_av2/c1_freeze_v02.py  legacy
4265359dcaf373fbe66046de415118bda19d5006f08b3c8ed2a714a124c6736d  50_CODE/c1_av2/tests/test_c1_v11.py  test
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
847d31d744bcb9da803c8fbdc5399b284e2c2ed814032796230bd55829cc4e1e  50_CODE/c1_av2/tests/c1_reproduce_check_v01.py  test_module
c79f1639b7f75912c4a4944c3cebc927be9f4a061047ce9154a3f374c76f4585  50_CODE/c1_av2/tests/c1_standin_prep_v01.py  test_module
b889f9c5af4446ed6a4ffc3c3dd846817812618ed0541ef32b7af24367bb72fa  50_CODE/c1_av2/tests/freeze_probe_pass_v01.py  test_module
5744951776eded5d0bf1f931cc7a55f9cad64a0b6c3ff8c657c1bc8a0ff7223c  50_CODE/c1_av2/tests/freeze_probe_fail_v01.py  test_module
b77ab7214b1de96aacfa0226f8b23ea9dd5a2219d6457bd6af02ef2ac0e03925  50_CODE/c1_av2/tests/freeze_probe_envcheck_v01.py  test_module
dc133766b0cc738da43394bda808c0e67e8259efe8b7ff375fffedcd133ca1fe  50_CODE/c1_av2/tests/c1_q1_standin_v01.py  test_module
b4f445d58cd5bb7270193237b09f9cecd4862f2b640a57e9baa10e891e2cfb1b  50_CODE/tpp/tests/test_tpp_analyse_v01.py  test_module
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

## Not bound (superseded; `c1_freeze_v06` refuses them in the block)

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
superseded  50_CODE/c1_av2/c1_quarantine_v01.py
superseded  50_CODE/c1_av2/c1_qcnet_summary_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v02.py
superseded  50_CODE/c1_av2/c1_rehearsal_v03.py
superseded  50_CODE/c1_av2/c1_rehearsal_v04.py
superseded  50_CODE/c1_av2/c1_rehearsal_v05.py
superseded  50_CODE/c1_av2/run_c1_standin_v01.sh
```

`c1_rehearsal_v06.py` (the rehearsal driver) and `c1_power_counts_v01`–`v04` are not bound.
