# C1 code v07: R17d's fixes under D16 v21 Choice 42 (4 Nov 2026)

README v01 to v06 are kept unchanged. This README answers `70_TESTS/R17D_C1_CODE_V06_CHECK_v01.md` (2 blockers, 3 majors, 9 minors) as D16 v21 Choice 42 decides, together with Choice 41(b), (c) and (d). It lists every bound file with its role (145 files: entry 16, module 49, generator 12, source 11, builder 14, legacy 2, test 1, test_module 16, archive 24).

**Guard version.** C1 v07 uses `c1_guard_v04.py`, which imports `c1_guard_v03`.
- `c1_guard_v02.py` (`00d9bc42…`) and `c1_crc_exact_v01.py` (`4919ed20…`) are unchanged, since D17 v04 binds them.
- Older modules still import `c1_guard_v01`, `v02` and `v03` (m8, below).
- No file bound by the frozen X1, X2, M or D17 plans was edited.

**Results.** `70_TESTS/c1_v01/C1_V07_TEST_STATUS.json` holds the test and rehearsal results. It is written after this README and records this README's hash. The rehearsal on this README is in `70_TESTS/c1_v01/rehearsal150_v07/`.

## Fixes, by R17d item

| R17d / Choice 42 | Fix | Test (`test_c1_v10`) |
|---|---|---|
| **B1** deposit before every AV2 outcome (42a) | `c1_guard_v04.guard()` requires the validated deposit record on AV2 for every role except `entry:c1_e0`, `entry:c1_folds` and `entry:c1_freeze`. This covers stage B, items, fits, runs, method stage, H8, predictor arm, Q1 summary and analysis. Every runtime record and every table carries `deposit_record_sha256`; `check_table` and the analysis's run check require it to equal the current record. `c1_freeze_v05 --amend` is refused once the record exists. | **TREE (PB1).** In a copy tree under a frozen plan with no record, `c1_h8_v05`, `c1_mstage_v05` and `c1_predarm_v05` are refused and `entry:c1_e0` is exempt. After the record: `--amend` is refused, and H8 runs. **M2:** a table with another deposit is not valid. |
| **B2** quarantine, not edits (42b) | `x1_full_v02`, `x2_full_v02` and `m_run_v04` are **not** edited. **`c1_quarantine_v01`** (lead tool) gzips each plain prepared ground-truth file named by an AV2 stage-A manifest into `30_DATA/av2_gt_quarantine_v01/`: it verifies the recorded hash first, verifies the member decompresses to the same bytes, then removes the plain file and writes `QUARANTINE_MANIFEST.json`. **`c1_freeze_v05`** refuses while such a plain file exists. **Reading after the quarantine:** stage B v05 reads ground truth only from a quarantine member, after the deposit check, and verifies the decompressed SHA-256 against the stage-A manifest. `c1_h8_v05`, `c1_mstage_v05` and the analysis's E⁰ recompute do the same, through a temporary file outside the workspace that is removed afterwards. | **TREE:** the freeze is refused before the quarantine; the quarantine dry run changes nothing; a real run gzips, verifies and removes, and a rerun is idempotent; a tampered plain file is refused; a ground-truth path recorded on a pod is found under `30_DATA` and quarantined. **P2b:** `x2_full_v02` cannot run once the plain ground truth is gone. |
| **M1** one freeze, stage B logged (42c) | **Stage B v05** writes only `30_DATA/av2_cache_stageB_<tag>/`, never over an existing folder, and appends one line to the append-only `40_PROTOCOL/C1_STAGE_B_LOG.txt`. **`c1_freeze_v05`** refuses any freeze while that log exists; it refuses `--amend` once the log or the deposit record exists; the folder search stays. **Tests:** the freeze runs every bound test with `C1_FREEZE_LOG_SHA256` (the frozen-into log's hash, or `absent`). `test_c1_v10` skips its own, v06's LOG/STAGEB and v09's G3 "real log absent" checks only when that variable equals the real log's hash. The value is written into FROZEN_TESTS. | **TREE:** `--amend` passes its probe suite through the variable, the same suite run directly fails, and the amendment is logged in `C1_DEVIATION_LOG_v01.md`. Stage B writes the fixed folder plus one log line. A second run on the same tag is refused, and so are `--out` and a plain `--gt`. `--amend` is refused after stage B. |
| **M2** H8 units pinned (42d) | `c1_h8_v05` under a plan: the ground truth's scenes must **equal** the `folds` role's units. `c1_analyse_v07` checks H8 with `units ==` the role named by `h8_units` (default `folds`). | **M2:** a subset table is not valid; the exact set is. |
| **M3** Q1 (41c, 42e) | **`c1_predarm_v05 --q1-only`:** no `--runs`; folds bound as `folds_val150` and checked against the parent; keys whose units equal that child's, chained to their cache (so on AV2 to the deposit). Each QCNet file must be chained to a **`c1_qcnet_summary_v01`** summary: keys hash, file hash, `not_predicted == 0`, checkpoint commit, re-centring and history source, made by `entry:c1_qcnet_summary` under the plan. **`c1_analyse_v07`** reads Q1 only from config key `q1` (units = `folds_val150`'s) into its own descriptive block, outside H1 and family S. QCNet options without `--q1-only` are refused. | **Q1:** a valid table; refused without a summary, with `not_predicted` > 0, with `--runs`, and QCNet without `--q1-only`. With Q1 present, failing, broken or missing, C1_verdict, gate_H1, family_S and H9 are byte-identical. **Rehearsal:** Q1 on a nuScenes stand-in. |
| **m1** stricter H9 flags (42f) | `h9_rule_v05`: E2 cells are flagged against the E2-only sup-t family, as D17's frozen H9 was; HL cells against the joint E2 + HL family. H9 needs: ≥ 6 power-qualified E2 cells, no E2 cell flagged (E2-only), no HL cell flagged (joint), every HL cell evaluable, and the pooled cell not flagged. The S20c rule is unchanged (E2 cells). | **M1RULE:** at a planted E2 rate, the joint family does not flag the cell (v04's rule holds) but the E2-only family does (v05's fails). |
| **m2** deposit validation (42f) | `check_deposit`: duplicated keys refused; `registration` must match `https://osf.io/<id>/` or `10.17605/OSF.IO/<ID>`; `registered_utc` must be ISO 8601 UTC, after the plan's hash-log line, no later than now, and before every stage-B build in the stage-B log. | **G4 (PB4):** refused for TODO, "not yet", 2099, a duplicated key, a time before the plan line, a time after a stage-B build, a wrong plan, a non-ISO time. **TREE:** a deposit time after a stage-B build is refused. |
| **m3** `scene.json` (41d, 42f) | Bound as `data:scene_json` (an AV2 freeze requires it). `c1_mstage_v05` and `c1_h8_v05` assert, for every unit, that `scene.json`'s log equals the bound stage-A manifests' `scenes[u]["log"]` (`check_scene_json`). `av2_cache_stageA_v02` (generator `make_av2_stageA_v02`) records `scene_json_sha256` among the stage-A inputs for future builds. | **SCENE:** a bound map passes; a missing unit or a swapped map is refused. **TREE:** H8 checks 50 units. |
| **m4** tpp38 versions (42f) | `tpp_keys_v03` and `tpp_run_v03` (v01 and v02 kept, imported) record python, numpy and torch in their wrapper records. `c1_freeze_v05` writes `FROZEN_ENV_TPP` by running the tpp38 interpreter, or from `--tpp-env`. Under a plan, `c1_predarm_v05` requires the block and compares every wrapper record with it (torch for runs only). | **ENVTPP:** a match passes; a different torch is refused; a missing block is refused. |
| **m5** separate blocks | The H9 and Q1 tables are separate, and so are their blocks in the analysis. | **Q1** byte identity |
| **(g)** run log | `run_log_append`: one JSON line per guarded AV2 run in the append-only `40_PROTOCOL/C1_RUN_LOG.txt` (UTC, entry, plan, deposit, inputs, outputs), written by stage B, items, fits, runs, method stage, H8, E⁰ under a plan, predictor arm, Q1 summary and analysis. `refuse_existing`: on AV2 an existing output (or final run record) is refused. Checkpoints and shards are kept, so a crashed run resumes. | **TREE:** one line from H8; the same output is refused. |
| **(h)** guide | Every deposit refusal names `40_PROTOCOL/OSF_DEPOSIT_GUIDE_v02.md`. | **G4** |
| **41(a)** blocks | `c1_freeze_v05` refuses a plan that already holds ENV, ENV_TPP or TESTS blocks, and asserts that each of the five blocks appears exactly once. | **TREE** and **FRZ5** (five blocks once each; a drafted FROZEN_ENV block is refused); the rehearsal freezes a copy of plan v06 draft (slots filled) and checks the blocks. |

**Also re-run:** every group of the earlier suites v01–v09, each in its own process (`test_c1_v10` LEGACY). This includes R17c's P1–P7 (v09) and the Choice 36 refusals (v08). Three kinds are skipped by rule:
- groups that compare generators with the edited live files (v01 GEN, v02 GEN2/FRZ, v03 GEN3, v06 FRZ3); `c1_freeze_v05` checks all 14 generators on the archived originals instead;
- v08 LEGACY, whose suites run here directly;
- v09 FRZ4, which freezes README v06: its entry points are no longer the latest versions, so `c1_freeze_v04` now refuses them, as Choice 34.7 requires. **FRZ5** runs the same cases on `c1_freeze_v05` and README v07: a first freeze, a refused second freeze, an amendment, a stage-B manifest, a failing bound test, an unbound stage-A builder, a re-randomised child, and a drafted FROZEN_ENV block.

## The narrowed claim (Choice 42b, for plan §11 and the paper)

> The C1 pipeline's entry points refuse to compute any AV2 outcome before the freeze, and any outcome after k before the external registration is recorded. Programs of the earlier nuScenes studies, and the public AV2 annotations, were not technically barred. The protection against a deliberate early look is the embargoed OSF registration, made before the confirmatory ground truth was built, together with the append-only run log.

**What the code adds.** The prepared ground truth is quarantined before the freeze, and the freeze refuses otherwise. This closes R17d's one-command route P2b between the freeze and the deposit. Before the freeze, the narrowed claim applies.

## Command order (AV2, for the lead)

Use `../env/canmot310/Scripts/python.exe -B` from `50_CODE/c1_av2`; the Trajectron++ wrappers run in `tpp38`.

1. **Stage A** for the 375 logs, T1, T3 and AB3DMOT (`av2_cache_stageA_v02`, with `--meta`, so `scene.json` is recorded), then the counts (S20a–S20c, S21, S22).
2. **Folds:** `c1_folds_v03 --dataset av2 …`, then `--restrict-from` for `val` and for `held_out_train`.
3. **E⁰ before the freeze:** `c1_e0_v04 --mode c1 --seed 20261114 --stageA-manifests …`. It reads the plain ground truth, so it must run **before the quarantine**.
4. **Quarantine:** `c1_quarantine_v01 --stageA-manifests <every AV2 stage-A manifest>`. Run `--dry-run` first.
5. **Freeze:** `c1_freeze_v05 … --folds-val150 … --folds-train225 … --data scene_json=<meta>/scene.json e0_plan=… <AV2 inputs> …`. It refuses plain ground truth, a stage-B log or a stage-B manifest. It runs `test_c1_v10` and writes the five blocks.
6. **OSF registration** (researcher, embargoed), then the lead writes `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt` (Choice 40, guide v02).
7. **Stage B:** `av2_cache_stageB_v05 --stage-a … --gt 30_DATA/av2_gt_quarantine_v01/<member>.gz --frozen-plan … --tag <tracker>`.
8. **Items:** `k8_items_v07 --av2-stageB --plan`.
9. **Fits and runs:** `c1_fit_v05` (within, within on `folds_val150`, source), `c1_transfer_apply_v01`, `c1_run_v05` (four routes, plus `tab`).
10. **Method stage:** `c1_mstage_v05 --av2-gt <member>.gz --folds …`.
11. **H8:** `c1_h8_v05 --gt <member>.gz --folds …`.
12. **Trajectron++** (pod): `tpp_keys_v03`, then `tpp_run_v03` for seeds 20261102, 20261104, 20261105 and gt.
13. **Predictor arm:** `c1_predarm_v05` with all three seeds.
14. **QCNet:** keys on the 150-log cache, `c1_qcnet_summary_v01` per QCNet file, then `c1_predarm_v05 --q1-only` on `folds_val150`.
15. **Analysis:** `c1_analyse_v07 --c1 --plan`.
16. **Upload** `C1_RUN_LOG.txt` and `C1_STAGE_B_LOG.txt` to the OSF project with the results.

None of these takes `--hash-log` on AV2, and no AV2 output is ever overwritten.

## Entry points (the plan's FROZEN_ROLES)

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v07.py` |
| `entry:c1_fit` | `c1_av2/c1_fit_v05.py` |
| `entry:c1_run` | `c1_av2/c1_run_v05.py` |
| `entry:c1_mstage` | `c1_av2/c1_mstage_v05.py` |
| `entry:c1_h8` | `c1_av2/c1_h8_v05.py` |
| `entry:c1_e0` | `c1_av2/c1_e0_v04.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v05.py` |
| `entry:c1_transfer_apply` | `c1_av2/c1_transfer_apply_v01.py` |
| `entry:c1_folds` | `c1_av2/c1_folds_v03.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v05.py` |
| `entry:c1_quarantine` | `c1_av2/c1_quarantine_v01.py` |
| `entry:c1_qcnet_summary` | `c1_av2/c1_qcnet_summary_v01.py` |
| `entry:stageB` | `av2/av2_cache_stageB_v05.py` (generated by `tests/make_av2_stageB_v05.py`) |
| `entry:k8_items` | `k8/k8_items_v07.py` (generated by `tests/make_k8_items_v07.py`) |
| `entry:tpp_keys` | `tpp/tpp_keys_v03.py` |
| `entry:tpp_run` | `tpp/tpp_run_v03.py` |

## m6, m7, m8 and other limits

- **m6.** `c1_fit_v01` (not bound, no guard) and `c1_analyse_v04` (not bound, not edited) stay runnable, but neither gives a route to outcomes before the deposit or into the decision. `c1_fit_v01` needs AV2 items, which need stage B, which needs the deposit; its fits are refused by `check_route_c1`. `c1_analyse_v04` recomputes E⁰ (outcome-free) and then calls the edited `c1_analyse_v03.main`, which refuses AV2 configs. The v05- and v06-era entry points are refused by role under a v07 plan.
- **m7.** The suites can now be rerun in the real tree after a freeze, but only by the freeze (`C1_FREEZE_LOG_SHA256`). Run directly after the freeze, they fail their real-log checks by design. FROZEN_TESTS remains the record; outside the freeze it can be reproduced in a copy tree, as R17d did.
- **m8 (corrections to README v06).**
  - Guard v01 is also imported through `c1_fit_v04`/`v05` and `c1_run_v04`/`v05` (for its `HASH_LOG` constant).
  - Guard v02 is also imported through `c1_freeze_v04` → `c1_freeze_v03` and through `c1_analyse_v05` (E⁰).
  - `c1_freeze_v01`/`v02` match README **v04**'s hashes, not v05's.
  - README v06's line "every fit, run and table on AV2 data inherits the check" was false for the H6–H8 tables. With `guard_v04` it is now true.
- **m9.** The archived originals are gzip members, and the SHA-256 of the decompressed bytes equals the earlier README's hash (Choice 42f m9).
- **Forged records.** Hand-forged JSON still passes. The protection against deliberate forgery is the OSF registration and the uploaded logs.
- **The quarantine depends on its order.** Ground truth prepared after the freeze, or outside the stage-A manifests, is not covered. The freeze checks only the files the bound stage-A manifests name. It looks at the recorded path and, for a path containing `/30_DATA/` (for example one recorded on a pod), at the same path under this workspace's `30_DATA`; `c1_quarantine_v01` looks in the same two places and removes every copy it finds. Any other copy (on a pod's volume, or elsewhere on the laptop) is the lead's to delete.
- **Q1 needs a new summary.** Q1 requires a `c1_qcnet_summary_v01` summary per QCNet file, made after the 150-log keys exist. The existing QCNet outputs (made 1–2 Nov) have no such summary, so the lead runs the tool at step 14. If any key record lacks a QCNet row, Q1 is refused (`not_predicted` must be 0) and reported "not tested" (Choice 41c).
- **The rehearsal is a stand-in.** It uses nuScenes validation scenes as "AV2", T1's data as AB3DMOT's, and the tracker's own predictions as a QCNet stand-in. Its verdicts are not evidence.

## Bound files (145; `<sha256>  <path>  <role>`)

```
d9699f39b058202155d26cd436be46ced72157bb367b7c0a6e5e58fc6d8bc3de  50_CODE/c1_av2/c1_analyse_v07.py  entry:c1_analyse
57742775d7904430ece8aab1917976b7f23cf6a8a410acfe20d725ff2a874303  50_CODE/c1_av2/c1_fit_v05.py  entry:c1_fit
314b9799759e0855c5f8d88339c6d13a746622728c0c544bc13ce3e449da5b70  50_CODE/c1_av2/c1_run_v05.py  entry:c1_run
8cd95a680cf8cdd37172987e095ab4074d3ec484c26ea2341b1e7f766afa214b  50_CODE/c1_av2/c1_mstage_v05.py  entry:c1_mstage
d3b29a40978c208c78a00074552ffcefc0719feb056797a0bbd391bade62714d  50_CODE/c1_av2/c1_h8_v05.py  entry:c1_h8
99de140ab7f74a501c2e4dd1cea62c543f8c68da60c6db59db373235a73d6ea4  50_CODE/c1_av2/c1_e0_v04.py  entry:c1_e0
e8f38acfc054596d073261802dd97a8f7db4b456f442ed093e366a9c85997a3f  50_CODE/c1_av2/c1_predarm_v05.py  entry:c1_predarm
9c909b9ba27ac207aa2653ec49963403f5fe59bad51d3e5732eb97d31a118bc3  50_CODE/c1_av2/c1_transfer_apply_v01.py  entry:c1_transfer_apply
299922d21908567d1c4c4153a88da5245548fee0842eeaca46347c69806520b4  50_CODE/c1_av2/c1_folds_v03.py  entry:c1_folds
5550db0b456ef2df399a61e4a48cdfcf1c2f85920ee866266db50a9f47694f42  50_CODE/c1_av2/c1_freeze_v05.py  entry:c1_freeze
c010e8c0191c2d46f27c50a629c08751c371ef3984000a2c3dca7907d8345072  50_CODE/c1_av2/c1_quarantine_v01.py  entry:c1_quarantine
72ce0040570cb3c95b1d98a1d1be8a111c13c81545d7ee4d77cb655837978249  50_CODE/c1_av2/c1_qcnet_summary_v01.py  entry:c1_qcnet_summary
b81ab3eb052dcd3de54d60ac5a022d247a71b72a8bc0a69a0a8f21078ce48de7  50_CODE/av2/av2_cache_stageB_v05.py  entry:stageB
8fd76c0964227d1095c4db4882df3f9c078f0388781aefa6969c12ee2b25f999  50_CODE/k8/k8_items_v07.py  entry:k8_items
1cf461361a717e03ef84fbec5767d3573a2558d633464ee79239f9626e2331ca  50_CODE/tpp/tpp_keys_v03.py  entry:tpp_keys
1c640a8b1d72d4d070f22f53b3f687525f2c74f92c905f726075a857acfc6442  50_CODE/tpp/tpp_run_v03.py  entry:tpp_run
a6d4254e10fafd20fb03f02f7a0ce1ee8b45555de2499998d56e4d6a4766b7e5  50_CODE/c1_av2/c1_analyse_v01.py  module
1765b2cb0f5859ba8f28d65c9a6554e91902d7877ba0f3f5a8072f4baf06ed9d  50_CODE/c1_av2/c1_analyse_v02.py  module
8981e11ebdaf89839ae727c9356355141d33b41421b0d4e3a32350fd95288bc6  50_CODE/c1_av2/c1_analyse_v03.py  module
f37c8fb4c1900d9a1a7fc833cee94872907fbdfe32045fe5acea65b05d98b15c  50_CODE/c1_av2/c1_analyse_v05.py  module
bda232b92a1af7256b8680c6c9f799631802954ccb6a67540908e26a894b0788  50_CODE/c1_av2/c1_analyse_v06.py  module
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
c882a61f00ad4b7d91c57c4698cb1009718d3985101be7ad7bb35e597cbf9a0d  50_CODE/c1_av2/c1_h8_v01.py  module
429658bb5165b9977f6a90be4a708aefc32f992815f94dac4bc1831055a09ca7  50_CODE/c1_av2/c1_h8_v02.py  module
0976db441e19fd80ce4f9d72e1a22b0ff4d10d69ab90d74e3109ad21129b7877  50_CODE/c1_av2/c1_legacy_refuse_v01.py  module
bffabac46c40d637f5af649649c3b0f41e73cc47e31f2f858a5b30bdd6985e84  50_CODE/c1_av2/c1_mstage_v01.py  module
0485fd7dc2323cc28f18fb171d6d9a70db2af11cda924d43f6447f6798785c03  50_CODE/c1_av2/c1_mstage_v02.py  module
392202b178e7b756bbb13970024831e42837fd545adf23f8084d40dff2ce96f7  50_CODE/c1_av2/c1_predarm_v01.py  module
6fdebcb5a6de6dea362ee55192fa0c2b941435ae8f459144de38434aabdaecad  50_CODE/c1_av2/c1_predarm_v02.py  module
997060cfeedbbdc9e29dda87931b58249639cb030ab949987d1d8f8dce8891a2  50_CODE/c1_av2/c1_predarm_v03.py  module
3751b773c7d267e5c20003cddf9efc843a6a0263c2a97972bc84b8dd1ab5c6aa  50_CODE/c1_av2/c1_predarm_v04.py  module
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
25d6481dcc2c99fcb3f4d4fc355aaed382301c23785b870f03de5795b32b1c4b  50_CODE/c1_av2/tests/make_k8_items_v05.py  generator
ad1dc93a19f7cd4f94b9f6cedb1faba487fe478fd7fa2c455962f485172b9092  50_CODE/c1_av2/tests/make_k8_items_v06.py  generator
56cda451a5d51e3e8bd7f4f42b5a48f87dee384c9eb29614d4dab548a6e6ce8b  50_CODE/c1_av2/tests/make_k8_items_v07.py  generator
da55af73d271b46c6cd9c08e537874df60acea01e213943c2fcdb47f48da3213  50_CODE/c1_av2/tests/make_av2_stageA_v02.py  generator
badd72d3094a25da20b881aaeeb3ab9cc23231f29e05b78a2cf866b98ccf9e9d  50_CODE/k8/tests/make_k8_joint_v04.py  generator
98376598e3671ec96d2cdb05600dd565a021e73ec85b81330b9202ca78f1f3c8  50_CODE/k8/k8_run_v04.py  source
3c5b064d61aa7fa36529537346248e690846a68d5fbacf0ac221b7a5a7d98541  50_CODE/c1_av2/c1_run_v01.py  source
03cd1108353a9e68ab8da074455ba9eef742f0baa880455d4c996741cc885f50  50_CODE/av2/av2_cache_stageB_v01.py  source
49771f4356dc1677b5347fd26470a1ee433a41c2a44e8c4d924386bdd9efb111  50_CODE/av2/av2_cache_stageB_v02.py  source
9d7994f6a60b0a77484a82883dc0d39e40b6e62ee01a543d987c09bf07dc8b77  50_CODE/av2/av2_cache_stageB_v03.py  source
69c6d1f456052d8a7df17ddce4c87df5eeaa914c1bca4aa1a8500f69e6fb08c8  50_CODE/av2/av2_cache_stageB_v04.py  source
d646f4205298781b49f78dad4b71a900604076e76fca7fc97b36a858c4ccf2d5  50_CODE/k8/k8_sim_v02.py  source
e5e1e03779427da30f4be190779252c8353e0854bcad82593d8c281b4fdc1183  50_CODE/k8/k8_run_v02.py  source
868e4ff028e2e04072b2508dad57c0c3b29b4c030b34f9acff350ce7083c810a  50_CODE/k8/k8_analyse_v03.py  source
f341ac1542c3c247bae6154b58d593d33f30191bacaf6eb6efa18a1d63ef855e  50_CODE/k8/k8_items_v05.py  source
c03fd53e7c9c00d39aa776405aada656827372ca4e4ebec7ad337fc42c38eff5  50_CODE/k8/k8_items_v06.py  source
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
4a1a3459f3ea219b8da65ac1c63f3e7b5369661242e22680867a337fff7db2be  50_CODE/c1_av2/c1_freeze_v01.py  legacy
e5bfbb6e5f4ce8dafd92050d5a05f1d43eb524292e07c5cc80456941c87516e7  50_CODE/c1_av2/c1_freeze_v02.py  legacy
e5097c2fabed18cf46f75448ab20795548741e692c5b1a4abccbea2e445d4c0f  50_CODE/c1_av2/tests/test_c1_v10.py  test
2398714275b91e02c42031f52d3e8da1c5bd7a1bf2c9b35a649f7aa99dceaa96  50_CODE/c1_av2/tests/test_c1_v01.py  test_module
5560e7739adbc1908d11505f1aeaa0ac154f56e26601dfa5e39c22ed9b075cd3  50_CODE/c1_av2/tests/test_c1_v02.py  test_module
b8614df5785e9074de32ca778b0868745cfa595b369fd032881759fb91b45ecf  50_CODE/c1_av2/tests/test_c1_v03.py  test_module
ae07d6a9d9b533a7ccfa3cf1640ce46fdc0a7ebebd6d12d5f3bbb10866297b9c  50_CODE/c1_av2/tests/test_c1_v04.py  test_module
f53d031a82b02b171dda8879d2d0eed6f228237b8e2e16c33fde572747dce391  50_CODE/c1_av2/tests/test_c1_v05.py  test_module
063d70952031c9faef67171eee029fc8fb1d8befb6ede8f6610dca3012a161a1  50_CODE/c1_av2/tests/test_c1_v06.py  test_module
42ed65c89e246f23b6f7fa714c35e9de6b83c8f95de153f93eda6d67cd258391  50_CODE/c1_av2/tests/test_c1_v07.py  test_module
025363ad29a0e9b03eb05a6b338840322c8351731ac29a53c629699da0d7654e  50_CODE/c1_av2/tests/test_c1_v08.py  test_module
7c455b02f7f4cc97ae93cff48eb19bb5f92f39fea56445ce970e69c725507bd8  50_CODE/c1_av2/tests/test_c1_v09.py  test_module
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

## Not bound (superseded; `c1_freeze_v05` refuses them in the block)

```
superseded  50_CODE/c1_av2/c1_analyse_v04.py
superseded  50_CODE/c1_av2/c1_fit_v01.py
superseded  50_CODE/c1_av2/c1_fit_v03.py
superseded  50_CODE/c1_av2/c1_fit_v04.py
superseded  50_CODE/c1_av2/c1_run_v03.py
superseded  50_CODE/c1_av2/c1_run_v04.py
superseded  50_CODE/c1_av2/c1_mstage_v03.py
superseded  50_CODE/c1_av2/c1_mstage_v04.py
superseded  50_CODE/c1_av2/c1_h8_v03.py
superseded  50_CODE/c1_av2/c1_h8_v04.py
superseded  50_CODE/c1_av2/c1_rehearsal_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v02.py
superseded  50_CODE/c1_av2/c1_rehearsal_v03.py
superseded  50_CODE/c1_av2/c1_rehearsal_v04.py
superseded  50_CODE/c1_av2/run_c1_standin_v01.sh
```

`c1_rehearsal_v05.py` (the rehearsal driver) and `c1_power_counts_v01`–`v04` are not bound.
