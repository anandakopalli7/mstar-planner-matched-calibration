# C1 code v05: the R17b fixes (4 Nov 2026)

README v01 to v04 are kept unchanged. This README covers the fixes for `70_TESTS/R17B_C1_CODE_V02_CHECK_v01.md`, made under D16 v13 Choices 33, 34 and 35 and the 7 minors, and the design change of D16 v16 Choice 37 (history length as a calibration stratum of the predictor arm). It lists every bound file with its role.

**Guard version.** C1 v05 uses `c1_guard_v02.py` (sha256 `00d9bc42…`). That is exactly the content the D17 v04 plan binds. It has not been edited since, and will not be. Any later guard change goes in `c1_guard_v03.py`. `c1_crc_exact_v01.py` (`4919ed20…`) is also unchanged.

**Test and rehearsal results** are in `70_TESTS/c1_v01/C1_V05_TEST_STATUS.json`. It was written after this README and records this README's hash, every suite's verdict with the tested files' hashes, and the rehearsal on this README (`70_TESTS/c1_v01/rehearsal150_v05b/`). An earlier rehearsal, frozen on a draft of this README written before Choice 37, was stopped on purpose during its first runner step (`rehearsal150_v05/STOPPED_ON_PURPOSE.txt`).

## What changed, by R17b item

| R17b | Fix (file) |
|---|---|
| **A1** `--hash-log` override | `c1_guard_v02.frozen_plan(plan, dataset, log)` hard-codes `40_PROTOCOL/C1_PLAN_HASH_LOG.txt` and `D17_PLAN_HASH_LOG.txt`. Any other log is refused unless the data are nuScenes. `av2_cache_stageB_v03` has no `--hash-log` option. `c1_fit_v03`, `c1_run_v03`, `c1_analyse_v05`, `c1_mstage_v03`, `c1_h8_v03`, `c1_e0_v02` and `c1_predarm_v02`/`v03` accept one only for nuScenes data. `c1_freeze_v03` accepts one only for nuScenes folds. |
| **A2** unguarded method stage, H8 and predictor arm | All three are guarded by `c1_guard_v02.guard`. The dataset is read from outcome-free files before any ground truth: the export record's tag, `x1_per_frame` scene names, the keys' scene names and their cache manifest. nuScenes runs without a plan. Anything else needs the frozen plan, with the module as the plan's named entry point and every loaded module bound. |
| **A2** pre-freeze E⁰ (Choice 34.2) | `c1_e0_v02` on AV2 before the freeze needs `--stageA-manifests`. A stage-B manifest is refused. Every input file (`x1_tracks`, GT, horizon) must be a recorded input of those stage-A manifests. After the freeze, `--plan` runs the full guard. |
| **A3** tag trusted over names | `dataset_checked` refuses a tag that disagrees with the names: UUIDs under "nuscenes", `scene-NNNN` under "av2", or an empty "nuscenes" set. `c1_analyse_v05` refuses a run record without caches outside `--c1`, and requires caches under `--c1`. `k8_items_v05` and `av2_cache_stageB_v03` use the same rule. |
| **B** H6–H9 tables unbindable | The config names their **paths** only. `c1_mstage_v03`, `c1_h8_v03` and `c1_predarm_v02`/`v03` write a `provenance` record: plan, folds, entry point, every loaded module's hash, the inputs' hashes, and `inputs_checked`. `c1_analyse_v05` checks it with `c1_guard_v02.check_table` and the plan's entry role. The rehearsal now runs with these tables present. |
| **M-a** entry point and imports not verified | `verify_runtime` runs at start, and `verify_runtime_again` runs before any output is written. The running file must be the plan's `entry:<name>`, and every project module in `sys.modules` (under `50_CODE`, excluding environments and third-party code) must be bound **by its own path**. The method-stage checkpoint key holds every loaded module's hash, the inputs, the plan and the folds. |
| **M-b** provenance-chain gaps | The freeze writes a `FROZEN_ROLES` block, and `require_bound(frozen, path, role)` checks the role. Probe: `c1_fit` posing as the stage-B builder is refused. `chain_cache` checks an AV2 cache: it must be stage B under this plan, built by `entry:stageB`, from a bound `stageA_manifest`. A nuScenes cache must itself be bound. `chain_items` follows items through their summary to such caches and a bound builder (`entry:k8_items` for AV2). `c1_fit_v03` chains every item file, and `c1_run_v03` chains every cache. `c1_predarm_v02` (and so `v03`) chains the keys (cache, `entry:tpp_keys`) and runs (summary, `entry:tpp_run`). Newly bound: `k8_items_v05` (new `--av2-stageB` mode for the confirmatory items), `k8_items_v02`/`v04`, `tpp_keys_v01`, `tpp_run_v01` and the AV2 export and port code (as builders). |
| **M-c** inconsistent fail-safe | Choice 33 (below), `c1_analyse_v05.decide`. |
| **M-d** H9 units and NaN; population | `c1_predarm_v02` (Choice 35, below), kept in `c1_predarm_v03`. |
| m-1 | `c1_h8_v03.check_e0_plan` refuses a missing decision cell, a null value and a key outside the decision band. The label names the table's own entry point. It also restores X1's export-gate check, which `c1_h8_v02` had dropped. |
| m-2 | `c1_rehearsal_v03` runs v05's code under `--c1` with the method-stage, H8 and H9 tables present. |
| m-3 | `c1_freeze_v03.check_generators` re-runs all 9 generator functions and refuses a bound generator it does not check. |
| m-4 | The plan names the entry points in `FROZEN_ROLES`. The decision records `binding.entry_point` with its hash. |
| m-5 | The slot test is a regex: `[SLOT`, `[ slot`, `SLOT:`, `slot :`, in any case. |
| m-6 | The config's `e0.inputs_sha256` holds the hashes `c1_e0_v02` records. The analysis re-hashes the inputs first and reports changed inputs separately from a changed value. Under `--c1` the inputs must also be bound. |
| m-7 | `c1_tests_v06.json`, `c1_tests_v07.json` and the status file record the tested files' hashes. |
| Choice 34.7 | `c1_freeze_v03` refuses an entry point that has a higher `_vNN` sibling in its directory, and a superseded file listed as bound. Superseded versions imported by the latest code are bound as modules, and generator sources as sources, but never as entry points. A decision, run or table from an old entry point fails the role checks, so `c1_analyse_v05` does not accept it. |

## Choice 33 in code (`c1_analyse_v05.decide`)

- **GO ⇔ H1 holds**, with every H1 input present and provenance-valid: both trackers' within-AV2 runs, their fits, folds, caches and chains, every comparator and every arm.
  - If a within run fails `check_route_c1`, that tracker's H1 input is "not provenance-valid". The verdict is **NO-GO** with that reason.
  - `nogo_reasons`, which is also `failed_conditions`, now holds only H1's conditions.
- **Each secondary claim** (H2–H10) gets a status: *holds*, *does not hold* or *not tested*.
  - Not tested means a missing or unverifiable input. The reason goes in `missing_inputs`.
  - A not-tested claim enters family S (fixed m = 5) with p = 1. Its label reads "not tested (…)", it is never confirmed, and it **never changes GO**.
- **Assertions:** `gate_H1 == (C1_verdict == "GO")`, and no claim is confirmed unless the gate holds and the claim holds.
- **E⁰ under Choice 33.** Choice 31's NO-GO for an E⁰ problem is replaced by Choice 33's rule.
  - These make **H8 "not tested"**: a missing `e0` entry, no input hashes, changed inputs, unbound inputs, a recomputed value that differs, or an H8 table without the plan's `E0_plan`.
  - None of them changes the verdict.
  - `c1_analyse_v04`, the Choice 31 version, is superseded and not bound.

## Choice 35 in code (`c1_predarm_v02`, kept in `c1_predarm_v03`)

- **Population.** H9's population is PD: the K8 relied in-path items at 2 s, scored on the K8 tracker-planner's constraints (normal and sign from the tracker). The output records this. **C1 plan §11.4 must be corrected to say so** (plan text; not code).
- **Errors.**
  - A unit of the keys outside the folds is an error, before anything is computed. v01 counted it as no exceedance.
  - A non-finite D or variance in any used item is also an error.
- **Folds without keys.** Fold units that have no keys are listed in `fold_units_without_keys`.

## Choice 37 in code (`c1_predarm_v03`)

- **History length.** An item's history length is its predictor's own input history at decision time *k*, read from the Trajectron++ keys:
  - the TPP arm (tracker histories, H9) uses `rec_hist_stratum_trk`;
  - the TPPgt arm (descriptive) uses `rec_hist_stratum_gt`.

  Both are the contiguous states up to *k*, written by `tpp_keys_v01` and stratified by `tpp_common_v01.hist_stratum`. Nothing after *k* is read.
  - The strata are {2, 3–4, ≥ 5 states}.
  - A used item below 2 states is an error, and so are keys without the field.
- **H9's fit.** H9 uses DP-SCRC with history length as a stratum dimension.
  - The levels are L0 × HL, L1 × HL, L2 × HL and L3 × HL, then L3 (the axis) as the last fallback, so every item has a threshold.
  - At each level a cell is fitted by exact CRC (`c1_crc_exact_v01.crc_threshold_exact`) if it has at least 19 calibration units (n_min, as for M\*). Otherwise its items fall back to the next level.
  - It is cross-fitted on the C1 folds, as before.
- **H9's validity family** is the E2 cells plus the three pooled history-length cells {2, 3–4, ≥ 5}. The rule is unchanged: no evaluable cell flagged, the pooled cell not flagged, at least 6 power-qualified cells, none flagged. The seeds are unchanged.
- **H9-noHL (descriptive)** is v02's arm, unchanged: D17-style strata and E2 cells only. It is reported as `H9_noHL`, and `c1_analyse_v05` reports it as the descriptive claim "H9-noHL", outside family S.
- **Diagnostic.** `noHL_on_HL_cells` evaluates the noHL thresholds on the HL family, which shows a short-history excess of the noHL method.
- **Q1 (QCNet)** stays noHL, because QCNet's own input history is not in the keys. The output says so.
- **Tests** (`tests/test_c1_v07.py`):
  - The generic level fit without HL equals `fit_hier_exact`, item for item.
  - A planted short-history excess (two-state errors × 2.0) is **missed** by D17's family, **caught** by the HL cells, and **calibrated** by the HL stratum.
  - A control without the excess flags no HL cell.

## Entry points (the plan's `FROZEN_ROLES`)

| Role | File |
|---|---|
| `entry:c1_analyse` | `c1_av2/c1_analyse_v05.py` |
| `entry:c1_fit` | `c1_av2/c1_fit_v03.py` |
| `entry:c1_run` | `c1_av2/c1_run_v03.py` |
| `entry:c1_mstage` | `c1_av2/c1_mstage_v03.py` |
| `entry:c1_h8` | `c1_av2/c1_h8_v03.py` |
| `entry:c1_e0` | `c1_av2/c1_e0_v02.py` |
| `entry:c1_predarm` | `c1_av2/c1_predarm_v03.py` (history-length strata, Choice 37) |
| `entry:c1_transfer_apply` | `c1_av2/c1_transfer_apply_v01.py` |
| `entry:c1_folds` | `c1_av2/c1_folds_v02.py` |
| `entry:c1_freeze` | `c1_av2/c1_freeze_v03.py` |
| `entry:stageB` | `av2/av2_cache_stageB_v03.py` (generated by `tests/make_av2_stageB_v03.py`) |
| `entry:k8_items` | `k8/k8_items_v05.py` (generated by `tests/make_k8_items_v05.py`) |
| `entry:tpp_keys` | `tpp/tpp_keys_v01.py` |
| `entry:tpp_run` | `tpp/tpp_run_v01.py` |

## Commands (AV2, after the freeze; for the lead)

All commands use `../env/canmot310/Scripts/python.exe -B` from `50_CODE/c1_av2`. The system Python lacks SciPy.

- **E⁰ before the freeze:**

  ```
  c1_e0_v02.py --mode c1 --seed 20261114 --workers <AV2 T1 x1 exports> --gt <AV2 GT> --meta <dir> --horizon <AV2 T1 h2s horizon> --stageA-manifests <the stage-A MANIFEST.json files> --out <json>
  ```

  Its `H8_E0_primary` goes into the plan. Its `inputs_sha256` goes into the config as `e0.inputs_sha256`.
- **Freeze:**

  ```
  c1_freeze_v03.py --plan <C1 plan> --readme README_C1_CODE_v05.md --results-dir <60_RESULTS/c1_av2> --folds --split --transfer-fits <t1> <t3> --stageA-manifests ... --config <json> --data e0_plan=<json> <name>=<AV2 input files used by mstage/h8/e0> ... --test "<python> -B tests/test_c1_v06.py <out>" "<python> -B tests/test_c1_v07.py <out>"
  ```

- **Then, in order:**
  1. `av2_cache_stageB_v03 --frozen-plan`
  2. `k8_items_v05 --av2-stageB --plan`
  3. `c1_fit_v03 --plan`
  4. `c1_transfer_apply_v01`
  5. `c1_run_v03 --c1-plan`
  6. `c1_mstage_v03 --plan --folds`
  7. `c1_h8_v03 --plan --folds --e0-plan`
  8. `tpp_keys_v01` and `tpp_run_v01` (pod)
  9. `c1_predarm_v03 --plan`
  10. `c1_analyse_v05 --c1 --plan`

  None takes `--hash-log` on AV2.

## Limits (stated, not fixed here)

- **Forged records.** Provenance records are JSON written by bound entry points. A hand-forged table with correct fields would pass `check_table`. The guard prevents accidental and command-line bypasses, not deliberate forgery.
- **AV2 builders.** The AV2 export and port files are bound at their current hashes. Nothing here checks that these are the versions that produced the AV2 data: no AV2 file was opened. The stage-A manifests record `builder_sha256`, so the lead can compare at the freeze.
- **Stage-A inputs.** `scene.json` (the scene-to-log map) is hashed and recorded, but it is not required to be a stage-A input.
- **Untested generator.** `av2/gen/make_k8_items_v04_v01.py` writes its target when imported, so `c1_freeze_v03` does not re-run it. `k8_items_v04` is bound as a builder and as `make_k8_items_v05`'s source.
- **Plan text.** R17 m8 (stale plan text) and the §11.4 correction are left to the plan's author.
- **Rehearsal stand-in.** The rehearsal uses nuScenes validation scenes as the "AV2" units and as the method stage's training set. The method stage runs at test sizes. Its verdicts are not evidence.

## Bound files (84; `<sha256>  <path>  <role>`)

Earlier READMEs, kept and not bound by this block: v01 `d38f26d3…`, v02 `3e528986…`, v03 `914a8ba1…`, v04 `f34ed502…`.

```
f37c8fb4c1900d9a1a7fc833cee94872907fbdfe32045fe5acea65b05d98b15c  50_CODE/c1_av2/c1_analyse_v05.py  entry:c1_analyse
f89a2c0e193612084d1284b45b305c9f73591cfc02ab8f3e2ba5a8ffbbc14fcd  50_CODE/c1_av2/c1_fit_v03.py  entry:c1_fit
f91472a177d3a0fac914f66a627ec64b00bca6df2b6dc578496226a96bcd66a7  50_CODE/c1_av2/c1_run_v03.py  entry:c1_run
75196cb8749ff3f0212a0c37c3d47a12a0dd8e3cba15cc07eea18d343c73cae3  50_CODE/c1_av2/c1_mstage_v03.py  entry:c1_mstage
b85c8799e40daedbcf99423304e46adf8a9e50d0ffd290946fffc83cd8082b29  50_CODE/c1_av2/c1_h8_v03.py  entry:c1_h8
d144bb1c0cc637c4ea4b7e7a59a6940700a637fee544511979eb283d18a52fd1  50_CODE/c1_av2/c1_e0_v02.py  entry:c1_e0
997060cfeedbbdc9e29dda87931b58249639cb030ab949987d1d8f8dce8891a2  50_CODE/c1_av2/c1_predarm_v03.py  entry:c1_predarm
9c909b9ba27ac207aa2653ec49963403f5fe59bad51d3e5732eb97d31a118bc3  50_CODE/c1_av2/c1_transfer_apply_v01.py  entry:c1_transfer_apply
b38605675bdc217e8a40ab1f4deb0cfca662711b56f9d0726e5d58646a19ec1c  50_CODE/c1_av2/c1_folds_v02.py  entry:c1_folds
fa84cafc558039af9e12897601bf58025dafba6f037dbc8bb550727571367408  50_CODE/c1_av2/c1_freeze_v03.py  entry:c1_freeze
9d7994f6a60b0a77484a82883dc0d39e40b6e62ee01a543d987c09bf07dc8b77  50_CODE/av2/av2_cache_stageB_v03.py  entry:stageB
f341ac1542c3c247bae6154b58d593d33f30191bacaf6eb6efa18a1d63ef855e  50_CODE/k8/k8_items_v05.py  entry:k8_items
a5e9d761d9bd335dac1494cf31c6ba53507d09ac2f29d79aa74f618fc5871c73  50_CODE/tpp/tpp_keys_v01.py  entry:tpp_keys
8f94cdbb619a3fb2e0e6439e049df1d9a9bdc33dbba4b8a16ac2f2405dfa1eb3  50_CODE/tpp/tpp_run_v01.py  entry:tpp_run
33534de9ff6b7de62f1256e60d309b2d72d23fe60935d8adb45233ded95fa433  50_CODE/c1_av2/c1_analyse_v01.py  module
f5cd98d7d52a8cd7ee62781b42fcc05b7d93fb7d2ccc298af2cd3b30eff41e10  50_CODE/c1_av2/c1_analyse_v02.py  module
93c6fc3fa1712e229cb9f1ecc6fa6cf8bb90847cd08941ddd9e34cd59ea8a229  50_CODE/c1_av2/c1_analyse_v03.py  module
4919ed20818b46cee13c3511444cc62ba44086b329fa2b98ffc0f17508a31494  50_CODE/c1_av2/c1_crc_exact_v01.py  module
4d5e18362c9db0b001f40a094fde9dcffae517c22d8abb75836c7a7d25b16dbf  50_CODE/c1_av2/c1_e0_v01.py  module
f377b364f8a0e5556c011436498d39fde28b24ae699963e6ec9f849a45574844  50_CODE/c1_av2/c1_fit_v02.py  module
58ea4a9246ed74fee2483309e8890a348f20fe3859f4a33367bc061aa2c834d9  50_CODE/c1_av2/c1_folds_v01.py  module
edc7ba861759a6538dbfbfc390816fd59a581816c3954362607e52d402230025  50_CODE/c1_av2/c1_guard_v01.py  module
00d9bc42713ee3e58ce148d7961c5c1b73e8316628fb26166a1377281384c724  50_CODE/c1_av2/c1_guard_v02.py  module
2500fb46de3d09b3308d316bcf24250d4516e28954a62608a064ad7e4f40a683  50_CODE/c1_av2/c1_h8_v01.py  module
7936ededcaf72ef437202ef8dafb291521a6c5427c97c79344ab9851f5cc31fe  50_CODE/c1_av2/c1_h8_v02.py  module
1d050ddfaf457e0b8290050de4c941b98a88d578d70928705844433f8e6e2049  50_CODE/c1_av2/c1_mstage_v01.py  module
ce0f045834084af02edfee5a1b7675ececed754b7b20771d6d667392cbeeb668  50_CODE/c1_av2/c1_mstage_v02.py  module
3d9ee540c745171afeb31c4d2542dca07bc1ea11e085cfd3aedcb1f48bcfcbe0  50_CODE/c1_av2/c1_predarm_v01.py  module
ee6a6f36fd1cd69837afe5a48a1da4b16d7bf3835097ca8b25976f206e6fa5ce  50_CODE/c1_av2/c1_predarm_v02.py  module
cc68154adb090bab5f3c05ba23f4417f1049ddc61a76473fc75d910bbda667a0  50_CODE/c1_av2/c1_run_v02.py  module
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
25d6481dcc2c99fcb3f4d4fc355aaed382301c23785b870f03de5795b32b1c4b  50_CODE/c1_av2/tests/make_k8_items_v05.py  generator
badd72d3094a25da20b881aaeeb3ab9cc23231f29e05b78a2cf866b98ccf9e9d  50_CODE/k8/tests/make_k8_joint_v04.py  generator
98376598e3671ec96d2cdb05600dd565a021e73ec85b81330b9202ca78f1f3c8  50_CODE/k8/k8_run_v04.py  source
f2cdf07abcb8eccd7049f33f772da1806de8c406d30450c3c35f4b91be8f26e8  50_CODE/c1_av2/c1_run_v01.py  source
7957bd0ba062751f1b68df35b03665ec59e61246bbcb1aeaa14be719a8b766a7  50_CODE/av2/av2_cache_stageB_v01.py  source
3cf6073c43b174a3dbde6b1f2b222b142049788078ad6078615e05ffc6eed4be  50_CODE/av2/av2_cache_stageB_v02.py  source
d646f4205298781b49f78dad4b71a900604076e76fca7fc97b36a858c4ccf2d5  50_CODE/k8/k8_sim_v02.py  source
e5e1e03779427da30f4be190779252c8353e0854bcad82593d8c281b4fdc1183  50_CODE/k8/k8_run_v02.py  source
868e4ff028e2e04072b2508dad57c0c3b29b4c030b34f9acff350ce7083c810a  50_CODE/k8/k8_analyse_v03.py  source
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
2398714275b91e02c42031f52d3e8da1c5bd7a1bf2c9b35a649f7aa99dceaa96  50_CODE/c1_av2/tests/test_c1_v01.py  test
5560e7739adbc1908d11505f1aeaa0ac154f56e26601dfa5e39c22ed9b075cd3  50_CODE/c1_av2/tests/test_c1_v02.py  test
b8614df5785e9074de32ca778b0868745cfa595b369fd032881759fb91b45ecf  50_CODE/c1_av2/tests/test_c1_v03.py  test
ae07d6a9d9b533a7ccfa3cf1640ce46fdc0a7ebebd6d12d5f3bbb10866297b9c  50_CODE/c1_av2/tests/test_c1_v04.py  test
f53d031a82b02b171dda8879d2d0eed6f228237b8e2e16c33fde572747dce391  50_CODE/c1_av2/tests/test_c1_v05.py  test
063d70952031c9faef67171eee029fc8fb1d8befb6ede8f6610dca3012a161a1  50_CODE/c1_av2/tests/test_c1_v06.py  test
42ed65c89e246f23b6f7fa714c35e9de6b83c8f95de153f93eda6d67cd258391  50_CODE/c1_av2/tests/test_c1_v07.py  test
847d31d744bcb9da803c8fbdc5399b284e2c2ed814032796230bd55829cc4e1e  50_CODE/c1_av2/tests/c1_reproduce_check_v01.py  test
c79f1639b7f75912c4a4944c3cebc927be9f4a061047ce9154a3f374c76f4585  50_CODE/c1_av2/tests/c1_standin_prep_v01.py  test
b4f445d58cd5bb7270193237b09f9cecd4862f2b640a57e9baa10e891e2cfb1b  50_CODE/tpp/tests/test_tpp_analyse_v01.py  test
```

## Not bound (superseded; `c1_freeze_v03` refuses them in the block)

```
superseded  50_CODE/c1_av2/c1_analyse_v04.py
superseded  50_CODE/c1_av2/c1_fit_v01.py
superseded  50_CODE/c1_av2/c1_freeze_v01.py
superseded  50_CODE/c1_av2/c1_freeze_v02.py
superseded  50_CODE/c1_av2/c1_rehearsal_v01.py
superseded  50_CODE/c1_av2/c1_rehearsal_v02.py
superseded  50_CODE/c1_av2/run_c1_standin_v01.sh
```

`c1_rehearsal_v03.py` (the rehearsal driver) and `c1_power_counts_v01`–`v04` (pre-freeze counts tools) are not part of the confirmatory path and are not bound.
