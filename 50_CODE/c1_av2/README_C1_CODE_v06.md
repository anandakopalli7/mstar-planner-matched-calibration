# C1 code v06: R17c's fixes and the Choice 38 items (4 Nov 2026)

README v01 to v05 are kept unchanged. This README covers:
- the fixes for `70_TESTS/R17C_C1_CODE_V05_CHECK_v01.md` (1 blocker, 4 major, 8 minor);
- D16 v17 Choice 38 (b), (c) and (d);
- D16 v18 Choice 39;
- D16 v19 Choice 40 (the embargoed OSF deposit, enforced by the stage-B builder).

It lists every bound file with its role (127 files: entry 14, module 42, generator 9, source 9, builder 13, legacy 2, test 3, test_module 11, archive 24).

**Guard version.** C1 v06 uses `c1_guard_v03.py` everywhere. `c1_guard_v02.py` (`00d9bc42…`) and `c1_crc_exact_v01.py` (`4919ed20…`) are unchanged, as D17 v04 binds them. v06 imports `c1_guard_v02` only through older modules: `c1_analyse_v05` for its E⁰ recompute, and `c1_predarm_v02`/`v03`.

**Test and rehearsal results** are in `70_TESTS/c1_v01/C1_V06_TEST_STATUS.json`. It is written after this README and records this README's hash, every suite's verdict with the tested files' hashes, and the rehearsal on this README (`70_TESTS/c1_v01/rehearsal150_v06/`).

## B1 (blocker): the superseded entry points no longer compute AV2 outcomes (Choice 36 rule 3, Choice 39a)

1. **Archived first.** Byte-exact originals of the 17 files are in `50_CODE/c1_av2/superseded_originals/` and `50_CODE/av2/superseded_originals/`.
   - They are stored gzip-compressed (mtime 0), so the unguarded originals cannot be run from the archive by accident.
   - `SHA256SUMS_superseded_originals_v01.txt` holds the SHA-256 of the decompressed bytes. These equal README v05's hashes of the same files (test v08 ARCH).
2. **Then `main()` only.** The edit was made by `superseded_originals/apply_choice36_main_edits_v01.py`.
   - Each file gets one call to `c1_legacy_refuse_v01.check()` inserted at one anchor inside `main()`, before any data is read.
   - The call refuses any input whose dataset is not nuScenes or synthetic, read from outcome-free tags and names only: manifests, folds, export track names, key names, item names, run records' caches and tables' provenance. It names the replacement.
   - Everything before `def main` and from `if __name__` is byte-identical to the original, so every imported function is unchanged (test v08 MAINONLY).
3. **Files:**
   - `c1_analyse_v01`–`v03`, `c1_fit_v02`, `c1_run_v01`/`v02`;
   - `c1_mstage_v01`/`v02`, `c1_h8_v01`/`v02`, `c1_e0_v01`;
   - `c1_predarm_v01`/`v02`, `c1_freeze_v01`/`v02` (AV2 folds refused);
   - `av2_cache_stageB_v01`/`v02`.
4. **Placement.** Where a file already refused AV2 input with a message a bound test expects, the new call sits after that refusal. `c1_run_v0x --standin` keeps its own refusal; `c1_predarm_v02` keeps its guard refusal.
5. **Delegation.** `c1_fit_v02` and `c1_run_v02` remain the bodies of the guarded `c1_fit_v04` and `c1_run_v04`.
   - Their `main()` accepts AV2 data only after `c1_guard_v03.guard()` has passed in the same process, for the same plan file, the same dataset and the role `entry:c1_fit` or `entry:c1_run` (`LAST_GUARD`).
   - The superseded `c1_fit_v03` and `c1_run_v03` therefore refuse AV2 too.
6. **Re-bound.** The new hashes are in the block below.
   - The generators are checked on the archived originals where a file was edited (11 checks; `c1_freeze_v04.check_generators`).
   - The freeze also re-verifies every edit (`check_main_edits`).
7. **Tests.**
   - v08 REFUSE runs every edited `main()` on R17c's P1 and P2 fixtures and expects a refusal with nothing written.
   - v08 LEGACY re-runs every group of the earlier suites v01–v06, each in its own process on the live files. Only GEN, GEN2, GEN3 and v06's FRZ3 are excluded: they compare generators with the live, edited files, and GENORIG replaces them.

## Majors

| R17c | Fix | Test |
|---|---|---|
| **M1** repeatable freeze | `c1_freeze_v04` makes one freeze:<br>– it refuses when the log already holds a plan line, unless `--amend "<reason>"`;<br>– an amendment is refused once a stage-B manifest exists, and is logged in `40_PROTOCOL/C1_DEVIATION_LOG_v01.md`, or beside a rehearsal's log;<br>– it refuses if any stage-B manifest exists under `30_DATA` (depth ≤ 3);<br>– it runs **every** README file in the role `test` and requires ALL_PASS, writing the verdicts, test hashes and output hashes into a `FROZEN_TESTS` block;<br>– it writes `FROZEN_ENV` (python, numpy, scipy).<br>`c1_guard_v03.frozen_plan` accepts only the **latest** line of the log, and records the log's hash in every runtime record and table. External deposit (Choice 39c) is the researcher's decision; the plan must state it. | v09 FRZ4: a second freeze is refused (P6); `--amend` appends and is logged, after which only the new plan is accepted; a stage-B manifest refuses the freeze, and so do a failing test, an unbound builder and a re-randomised child. v09 G3: an older line is refused. |
| **M2** exceptions abort the decision | In `c1_analyse_v06`, every secondary input, route and claim block runs under `except Exception`:<br>– a secondary failure makes that claim "not tested", with the exception text;<br>– a failure on an H1 input (the `within_lt3d` route of T1 or T3, or H1's own block) gives NO-GO with the reason;<br>– `e0_check` and every table load are wrapped the same way;<br>– only guard breaches (`GUARD:` assertions) still abort. | v09 M2:<br>– P3: a moved E⁰ input is "not ok", without an exception;<br>– P4e: a malformed method-stage table makes H6a, H6b and H7 "not tested";<br>– a raising H9 table makes H9 "not tested";<br>– an exception on an H1 input gives NO-GO;<br>– through `main()`, a broken within run and a missing transfer run still write a decision (NO-GO, H4 "not tested"). |
| **M3** HL cells counted in the floor | `c1_predarm_v04.h9_rule_v04`, per Choice 39b:<br>– the floor counts **E2 cells only** (≥ 6 power-qualified);<br>– the 3 HL cells are an added requirement: each evaluable and none flagged, with flags, power and the family flag computed over E2 + HL in one sup-t family;<br>– the pooled cell counts each item once (the HL columns).<br>`s20c_label()` applies the S20c rule the same way, and the table reports `S20c_label_from_counts`. `c1_power_counts_v04` counts no HL cells, so it is unchanged. | v09 M3, on planted tables:<br>– 3 E2 + 3 HL cells fail (v01's rule would count 6);<br>– 7 clean E2 cells hold;<br>– a flagged HL cell fails H9 despite ≥ 6 clean E2 cells.<br>On the powered synthetic pipeline: HL H9 holds (≥ 6 qualified E2); with a planted two-state excess, H9_noHL holds with ≥ 6 qualified cells (missed, with power), the HL cells flag it under the noHL fit, and HL H9 holds. |
| **M4** units and seed unchecked | **Unit lists.** Tables record their sorted unit list and its hash (`units_record`). `check_table` (guard v03) requires:<br>– method stage and predictor arm: the bound folds' units, exactly;<br>– H8: a non-empty subset of them (its ground-truth scenes; `c1_h8_v04` asserts that the export's track scenes equal them);<br>– the folds' dataset, and the current log hash.<br>`c1_mstage_v04` refuses a subset of the folds; `c1_predarm_v04` refuses fold units without keys (P7).<br>**Seed.** The primary H9 table must come from the verified seed 20261102: the run summary's seed, chained.<br>**`--scenes`.** `tpp_keys_v02` and `tpp_run_v02` (new entry points; v01 kept, imported) refuse `--scenes` on AV2 inputs and write a `.wrapper.json` record, which `c1_predarm_v04` requires for AV2. Runs with unpredicted records are refused. | v09 M4: another unit list, units hash or dataset is refused; P7 is refused; a run whose summary seed is not its label's is refused; a primary table from seed 20261104 is not valid; `--scenes` on AV2 keys or runs is refused. |

## Minors

| R17c | Fix | Test |
|---|---|---|
| m1 | An H9 table without a TPP arm gives H9 "not tested". | v09 MINOR |
| m2 | `c1_e0_v03` asserts seed 20261114, and mode c1 (mode x1 only on nuScenes). The analysis's `e0_check` refuses another seed. The superseded `c1_e0_v02` still accepts any seed, but a plan value from another draw cannot pass the analysis's recompute with 20261114. | v09 MINOR |
| m3 | `check_route_c1` requires every run cache's dataset to equal the folds' dataset. `c1_run_v04` asserts the same. | v09 MINOR |
| m4 | No test means no freeze; the verdicts and hashes go into the plan (M1). | v09 FRZ4 |
| m5 | `FROZEN_ENV` is written by the freeze and asserted by `c1_guard_v03.guard()` under any plan. Versions are recorded in every record. | v09 G3 |
| m6 | The powered synthetic case (M3) shows the noHL miss with power and an HL H9 that holds. The guarded HL path runs in the rehearsal, three seeds included. | v09 M3, rehearsal |
| m7 | `export_dataset` reads the unit names from `x1_tracks.jsonl.gz`. | v09 G3 |
| m8 | The freeze compares each stage-A manifest's `inputs.builder_sha256`, when recorded, with the README's `builder` files. | v09 FRZ4 |

## Choice 38

- **(b) Seeds.** `c1_predarm_v04 --runs trk=<20261102> trk@20261104=<…> trk@20261105=<…> [gt=<…>]` takes all three seeds in one call.
  - It reads and asserts each run's summary seed.
  - Under a plan, all three runs are required before any H9 outcome is computed.
  - The table gives `H9` (primary), `H9_noHL` and `H9_seed`.
  - `c1_analyse_v06` reports `H9_seed_robustness` as descriptive: "seed-robust", "not seed-robust" or "not tested". It is outside family S and never reads or changes `claims["H9"]`.
  - Test v09 S38B: flipping or removing the robustness seeds changes nothing else.
- **(c) AB3DMOT.**
  - `DESCRIPTIVE_TRACKERS = ("tab",)`. Its routes run with tracker index 2.
  - `decide()` receives T1 and T3 only, and asserts this. `descriptive_block()` gives AB3DMOT's Form B, validity and trade-off rows under "descriptive (Choice 38c; outside H1 and family S)".
  - Its tables use `method_stage_descriptive` and `h9_descriptive`, checked by `check_table`.
  - `family_S` is asserted to be exactly H2, H3, H4, H6b and H10.
  - Test v09 S38C: with AB3DMOT passing, failing or missing, `C1_verdict`, `gate_H1`, `family_S` and every claim status are byte-identical.
- **(d) 150-log routes.**
  - `c1_folds_v03 --restrict-from <375 folds> --source val|held_out_train` writes child files: the parent's labels restricted, `parent_sha256`, no new randomness. They are bound as `folds_val150` and `folds_train225`, and checked against the parent by the freeze and by `c1_guard_v03.check_child_folds`.
  - `c1_fit_v04`:
    - `--route within` accepts `folds` or `folds_val150`;
    - `--route source` is fitted on `folds_train225`'s units, with chained items, and applied to `folds_val150`'s units, which must be disjoint from them.
  - `c1_run_v04` accepts any folds role and records it.
  - `c1_analyse_v06` expects a folds role per route:
    - within and transfer: `folds`;
    - `voxelnext_val`, `public_lt3d_val` and `source_transfer`: `folds_val150`.
  - The `source_transfer` fit must be a "source" fit by `entry:c1_fit`, trained on exactly the `folds_train225` units. H5 and H1-P are "not tested" when missing.
  - Test v09 S38D: a valid child passes, a re-randomised child is refused, and a source fit with a validation unit in training is refused. The rehearsal runs `public_lt3d_val` and `source_transfer`.

## Choice 40: stage B needs the deposit record

- **The check.** `av2_cache_stageB_v04` (`entry:stageB`) calls `c1_guard_v03.check_deposit` on an AV2 cache, after the guard and before any ground truth is read. The record is `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt`; the path is hard-coded, and an override is accepted only for nuScenes or synthetic fixtures.
- **The record must have:**
  - a line `frozen_plan_sha256: <64 hex>` equal to the guard's plan, which is the latest C1 line of the canonical log;
  - a non-empty `registration:` line (OSF URL or DOI);
  - a `registered_utc:` line.

  Otherwise stage B refuses, naming `40_PROTOCOL/OSF_DEPOSIT_GUIDE_v01.md`.
- **The chain.** The record's sha256 goes into the stage-B manifest (`stage_b.deposit_record_sha256`). `chain_cache` requires that field and re-checks the record, so every fit, run and table on AV2 data inherits the check.
- **Exemption.** nuScenes caches are exempt, and the rehearsal runs no stage B.
- **The real record is not created here.** The lead writes it after the researcher registers.
- **Test** v09 DEPOSIT:
  - a fixture record passes on the nuScenes route;
  - a wrong plan hash, a missing registration and a missing time are each refused;
  - on AV2, a missing record and a fixture override are refused;
  - `chain_cache` refuses an AV2 stage-B manifest without the field, and without the real record;
  - the builder checks the record before reading the ground truth.

## R17c's probes P1–P7 as refusal tests

Test v09 P1P7, also run by the rehearsal with `--rehearsal`:

- **P1.** Stage B v01, v02 (edited) and v04 refuse an AV2-tagged stage-A cache and write nothing.
- **P2.** `c1_h8_v02`/`v04`, `c1_mstage_v02`/`v04`, `c1_predarm_v01`/`v04` and `c1_e0_v01`/`v03` refuse AV2-tagged exports or keys.
- **P3 and P4.** See M2.
- **P5.** The floor counts E2 cells only.
- **P6.** One freeze. In the rehearsal, a second freeze into its own log is refused.
- **P7.** See M4.

## Entry points (the plan's FROZEN_ROLES)

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v06.py` |
| `entry:c1_fit` | `c1_av2/c1_fit_v04.py` |
| `entry:c1_run` | `c1_av2/c1_run_v04.py` |
| `entry:c1_mstage` | `c1_av2/c1_mstage_v04.py` |
| `entry:c1_h8` | `c1_av2/c1_h8_v04.py` |
| `entry:c1_e0` | `c1_av2/c1_e0_v03.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v04.py` |
| `entry:c1_transfer_apply` | `c1_av2/c1_transfer_apply_v01.py` |
| `entry:c1_folds` | `c1_av2/c1_folds_v03.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v04.py` |
| `entry:stageB` | `av2/av2_cache_stageB_v04.py` (generated by `tests/make_av2_stageB_v04.py`) |
| `entry:k8_items` | `k8/k8_items_v06.py` (generated by `tests/make_k8_items_v06.py`) |
| `entry:tpp_keys` | `tpp/tpp_keys_v02.py` |
| `entry:tpp_run` | `tpp/tpp_run_v02.py` |

## Commands (AV2, for the lead)

Use `../env/canmot310/Scripts/python.exe -B` from `50_CODE/c1_av2`; the TPP wrappers run in `tpp38`.

1. **Before the freeze:**
   - `c1_folds_v03 --dataset av2 --split … --val …`, then `--restrict-from` twice;
   - `c1_e0_v03 --mode c1 --seed 20261114 --stageA-manifests …`.
2. **The freeze:** `c1_freeze_v04 … --folds-val150 … --folds-train225 … --data …`. It runs tests v07, v08 and v09 itself and refuses if a stage-B manifest exists.
3. **External deposit** (Choice 40): the researcher registers on OSF, embargoed. The lead writes `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt`, and stage B refuses without it.
4. **Stage B:** `av2_cache_stageB_v04 --frozen-plan` (checks the deposit record).
5. **Items:** `k8_items_v06 --av2-stageB --plan`.
6. **Fits:** `c1_fit_v04` (within; within on `folds_val150`; source).
7. **Transfer:** `c1_transfer_apply_v01`.
8. **Runs:** `c1_run_v04` (four routes, plus `tab`).
9. **Method stage:** `c1_mstage_v04 --folds`.
10. **H8:** `c1_h8_v04 --e0-plan --folds`.
11. **Trajectron++ keys and runs** (pod): `tpp_keys_v02`, then `tpp_run_v02` for seeds 20261102, 20261104 and 20261105, plus the gt run.
12. **Predictor arm:** `c1_predarm_v04` with all three seeds.
13. **Analysis:** `c1_analyse_v06 --c1 --plan`.

None of these takes `--hash-log` on AV2.

## Limits and open points

- **Forged records.** Hand-forged provenance JSON still passes. The pipeline refuses accidental and command-line bypasses, and the external deposit (39c) is the protection against deliberate forgery.
- **AV2 builders.** They are bound at their current hashes. m8 checks the stage-A builder hash at the freeze. The export code is checked through the stage-A manifests' recorded inputs, and no AV2 file was opened here.
- **One keys file.** `c1_predarm_v04` needs one keys file whose units are exactly the 375 fold units: one stage-B cache for the 375 logs, or keys built over both caches.
- **Superseded v05-era entry points** (`c1_fit_v03`, `c1_run_v03`, `c1_mstage_v03`, `c1_h8_v03`, `c1_e0_v02`, `c1_predarm_v03`, `c1_analyse_v05`, `av2_cache_stageB_v03`, `k8_items_v05`) were not edited. They use `c1_guard_v02`:
  - before the freeze, they refuse AV2 without a plan and refuse a private log;
  - after the freeze, the v06 plan's roles name other entry points, so they are refused;
  - `c1_fit_v03` and `c1_run_v03` also hit the edited v02 bodies.
- **Plan text.** §6.4 and the S20c rule must state the E2-only floor (Choice 39b). The §11.4 population correction and R17 m8 are left to the plan's author.
- **Rehearsal stand-in.** The rehearsal uses nuScenes validation scenes as "AV2" and T1's data as AB3DMOT's. Its verdicts are not evidence.

## Bound files (127; `<sha256>  <path>  <role>`)

```
bda232b92a1af7256b8680c6c9f799631802954ccb6a67540908e26a894b0788  50_CODE/c1_av2/c1_analyse_v06.py  entry:c1_analyse
9829678d163bf60620f90d4e0b959f61d1463b613ff01895d7850654451f1a08  50_CODE/c1_av2/c1_fit_v04.py  entry:c1_fit
0244e416397f7bdaab911df04b0f71e1897a4f202f5adda3292eb421ce2f580a  50_CODE/c1_av2/c1_run_v04.py  entry:c1_run
d371e08915fec7086cbffcdd1afca0e4d124bc5f5f61f9179b4120e5abe64971  50_CODE/c1_av2/c1_mstage_v04.py  entry:c1_mstage
0686326554adb5d7e69140c5bfd78ddf2f9ce89cbac70c1827c43fc64100dfed  50_CODE/c1_av2/c1_h8_v04.py  entry:c1_h8
3a2057849767fb32da6a793d53fa61a6eea0b47068319631030d9005a09d0d92  50_CODE/c1_av2/c1_e0_v03.py  entry:c1_e0
3751b773c7d267e5c20003cddf9efc843a6a0263c2a97972bc84b8dd1ab5c6aa  50_CODE/c1_av2/c1_predarm_v04.py  entry:c1_predarm
9c909b9ba27ac207aa2653ec49963403f5fe59bad51d3e5732eb97d31a118bc3  50_CODE/c1_av2/c1_transfer_apply_v01.py  entry:c1_transfer_apply
299922d21908567d1c4c4153a88da5245548fee0842eeaca46347c69806520b4  50_CODE/c1_av2/c1_folds_v03.py  entry:c1_folds
48bc6bcd4f6d500e0831917dcfdd2a5f402d8bad880745efa939309bb3f41f47  50_CODE/c1_av2/c1_freeze_v04.py  entry:c1_freeze
69c6d1f456052d8a7df17ddce4c87df5eeaa914c1bca4aa1a8500f69e6fb08c8  50_CODE/av2/av2_cache_stageB_v04.py  entry:stageB
c03fd53e7c9c00d39aa776405aada656827372ca4e4ebec7ad337fc42c38eff5  50_CODE/k8/k8_items_v06.py  entry:k8_items
abb60897e1bb3ed7446d5bd93ce5ad94845a8bb47b055026ded17036c1af5cbb  50_CODE/tpp/tpp_keys_v02.py  entry:tpp_keys
2204a6cefda73c4461ac3bf609a3fd219c1aea51d1861b981d7ffba545257bc9  50_CODE/tpp/tpp_run_v02.py  entry:tpp_run
a6d4254e10fafd20fb03f02f7a0ce1ee8b45555de2499998d56e4d6a4766b7e5  50_CODE/c1_av2/c1_analyse_v01.py  module
1765b2cb0f5859ba8f28d65c9a6554e91902d7877ba0f3f5a8072f4baf06ed9d  50_CODE/c1_av2/c1_analyse_v02.py  module
8981e11ebdaf89839ae727c9356355141d33b41421b0d4e3a32350fd95288bc6  50_CODE/c1_av2/c1_analyse_v03.py  module
f37c8fb4c1900d9a1a7fc833cee94872907fbdfe32045fe5acea65b05d98b15c  50_CODE/c1_av2/c1_analyse_v05.py  module
4919ed20818b46cee13c3511444cc62ba44086b329fa2b98ffc0f17508a31494  50_CODE/c1_av2/c1_crc_exact_v01.py  module
d706a5e2969e17a7ecb232019f0fe478cab97316a2563bbd828725a48655bd7a  50_CODE/c1_av2/c1_e0_v01.py  module
d144bb1c0cc637c4ea4b7e7a59a6940700a637fee544511979eb283d18a52fd1  50_CODE/c1_av2/c1_e0_v02.py  module
420cf639fc92f3f087f9a39d97981a96b5e3e10d431193a915fa97f3e2e5dcbf  50_CODE/c1_av2/c1_fit_v02.py  module
58ea4a9246ed74fee2483309e8890a348f20fe3859f4a33367bc061aa2c834d9  50_CODE/c1_av2/c1_folds_v01.py  module
b38605675bdc217e8a40ab1f4deb0cfca662711b56f9d0726e5d58646a19ec1c  50_CODE/c1_av2/c1_folds_v02.py  module
fa84cafc558039af9e12897601bf58025dafba6f037dbc8bb550727571367408  50_CODE/c1_av2/c1_freeze_v03.py  module
edc7ba861759a6538dbfbfc390816fd59a581816c3954362607e52d402230025  50_CODE/c1_av2/c1_guard_v01.py  module
00d9bc42713ee3e58ce148d7961c5c1b73e8316628fb26166a1377281384c724  50_CODE/c1_av2/c1_guard_v02.py  module
ec6e7390e02fc357224d83329eee5f5267294bf053083d903b51e9aefb152408  50_CODE/c1_av2/c1_guard_v03.py  module
c882a61f00ad4b7d91c57c4698cb1009718d3985101be7ad7bb35e597cbf9a0d  50_CODE/c1_av2/c1_h8_v01.py  module
429658bb5165b9977f6a90be4a708aefc32f992815f94dac4bc1831055a09ca7  50_CODE/c1_av2/c1_h8_v02.py  module
0976db441e19fd80ce4f9d72e1a22b0ff4d10d69ab90d74e3109ad21129b7877  50_CODE/c1_av2/c1_legacy_refuse_v01.py  module
bffabac46c40d637f5af649649c3b0f41e73cc47e31f2f858a5b30bdd6985e84  50_CODE/c1_av2/c1_mstage_v01.py  module
0485fd7dc2323cc28f18fb171d6d9a70db2af11cda924d43f6447f6798785c03  50_CODE/c1_av2/c1_mstage_v02.py  module
392202b178e7b756bbb13970024831e42837fd545adf23f8084d40dff2ce96f7  50_CODE/c1_av2/c1_predarm_v01.py  module
6fdebcb5a6de6dea362ee55192fa0c2b941435ae8f459144de38434aabdaecad  50_CODE/c1_av2/c1_predarm_v02.py  module
997060cfeedbbdc9e29dda87931b58249639cb030ab949987d1d8f8dce8891a2  50_CODE/c1_av2/c1_predarm_v03.py  module
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
25d6481dcc2c99fcb3f4d4fc355aaed382301c23785b870f03de5795b32b1c4b  50_CODE/c1_av2/tests/make_k8_items_v05.py  generator
ad1dc93a19f7cd4f94b9f6cedb1faba487fe478fd7fa2c455962f485172b9092  50_CODE/c1_av2/tests/make_k8_items_v06.py  generator
badd72d3094a25da20b881aaeeb3ab9cc23231f29e05b78a2cf866b98ccf9e9d  50_CODE/k8/tests/make_k8_joint_v04.py  generator
98376598e3671ec96d2cdb05600dd565a021e73ec85b81330b9202ca78f1f3c8  50_CODE/k8/k8_run_v04.py  source
3c5b064d61aa7fa36529537346248e690846a68d5fbacf0ac221b7a5a7d98541  50_CODE/c1_av2/c1_run_v01.py  source
03cd1108353a9e68ab8da074455ba9eef742f0baa880455d4c996741cc885f50  50_CODE/av2/av2_cache_stageB_v01.py  source
49771f4356dc1677b5347fd26470a1ee433a41c2a44e8c4d924386bdd9efb111  50_CODE/av2/av2_cache_stageB_v02.py  source
9d7994f6a60b0a77484a82883dc0d39e40b6e62ee01a543d987c09bf07dc8b77  50_CODE/av2/av2_cache_stageB_v03.py  source
d646f4205298781b49f78dad4b71a900604076e76fca7fc97b36a858c4ccf2d5  50_CODE/k8/k8_sim_v02.py  source
e5e1e03779427da30f4be190779252c8353e0854bcad82593d8c281b4fdc1183  50_CODE/k8/k8_run_v02.py  source
868e4ff028e2e04072b2508dad57c0c3b29b4c030b34f9acff350ce7083c810a  50_CODE/k8/k8_analyse_v03.py  source
f341ac1542c3c247bae6154b58d593d33f30191bacaf6eb6efa18a1d63ef855e  50_CODE/k8/k8_items_v05.py  source
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
ea8180e73e80c69108763b95d32143f2adb0fcbba56953dd8ab0476b3b5de36b  50_CODE/av2/av2_feather_v01.py  builder
34319316aaea4bf1352345fbb8e556c8e7df7fe28c38148b27d83e72ee62e56b  50_CODE/av2/av2_counts_v02.py  builder
b55f767cc533f1f3b526535d96a8387838545eacef054a54b772066c60fdf675  50_CODE/x1/x1_export_v06.py  builder
4a1a3459f3ea219b8da65ac1c63f3e7b5369661242e22680867a337fff7db2be  50_CODE/c1_av2/c1_freeze_v01.py  legacy
e5bfbb6e5f4ce8dafd92050d5a05f1d43eb524292e07c5cc80456941c87516e7  50_CODE/c1_av2/c1_freeze_v02.py  legacy
42ed65c89e246f23b6f7fa714c35e9de6b83c8f95de153f93eda6d67cd258391  50_CODE/c1_av2/tests/test_c1_v07.py  test
025363ad29a0e9b03eb05a6b338840322c8351731ac29a53c629699da0d7654e  50_CODE/c1_av2/tests/test_c1_v08.py  test
7c455b02f7f4cc97ae93cff48eb19bb5f92f39fea56445ce970e69c725507bd8  50_CODE/c1_av2/tests/test_c1_v09.py  test
2398714275b91e02c42031f52d3e8da1c5bd7a1bf2c9b35a649f7aa99dceaa96  50_CODE/c1_av2/tests/test_c1_v01.py  test_module
5560e7739adbc1908d11505f1aeaa0ac154f56e26601dfa5e39c22ed9b075cd3  50_CODE/c1_av2/tests/test_c1_v02.py  test_module
b8614df5785e9074de32ca778b0868745cfa595b369fd032881759fb91b45ecf  50_CODE/c1_av2/tests/test_c1_v03.py  test_module
ae07d6a9d9b533a7ccfa3cf1640ce46fdc0a7ebebd6d12d5f3bbb10866297b9c  50_CODE/c1_av2/tests/test_c1_v04.py  test_module
f53d031a82b02b171dda8879d2d0eed6f228237b8e2e16c33fde572747dce391  50_CODE/c1_av2/tests/test_c1_v05.py  test_module
063d70952031c9faef67171eee029fc8fb1d8befb6ede8f6610dca3012a161a1  50_CODE/c1_av2/tests/test_c1_v06.py  test_module
847d31d744bcb9da803c8fbdc5399b284e2c2ed814032796230bd55829cc4e1e  50_CODE/c1_av2/tests/c1_reproduce_check_v01.py  test_module
c79f1639b7f75912c4a4944c3cebc927be9f4a061047ce9154a3f374c76f4585  50_CODE/c1_av2/tests/c1_standin_prep_v01.py  test_module
b889f9c5af4446ed6a4ffc3c3dd846817812618ed0541ef32b7af24367bb72fa  50_CODE/c1_av2/tests/freeze_probe_pass_v01.py  test_module
5744951776eded5d0bf1f931cc7a55f9cad64a0b6c3ff8c657c1bc8a0ff7223c  50_CODE/c1_av2/tests/freeze_probe_fail_v01.py  test_module
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

## Not bound (superseded; `c1_freeze_v04` refuses them in the block)

```
superseded  50_CODE/c1_av2/c1_analyse_v04.py
superseded  50_CODE/c1_av2/c1_fit_v01.py
superseded  50_CODE/c1_av2/c1_fit_v03.py
superseded  50_CODE/c1_av2/c1_run_v03.py
superseded  50_CODE/c1_av2/c1_mstage_v03.py
superseded  50_CODE/c1_av2/c1_h8_v03.py
superseded  50_CODE/c1_av2/c1_rehearsal_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v02.py
superseded  50_CODE/c1_av2/c1_rehearsal_v03.py
superseded  50_CODE/c1_av2/run_c1_standin_v01.sh
```

`c1_rehearsal_v04.py` (the rehearsal driver) and `c1_power_counts_v01`–`v04` (pre-freeze counts tools) are not bound.
