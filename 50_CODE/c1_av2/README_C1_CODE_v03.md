# C1 code v03: the AV2 confirmatory pipeline, after R17, resumable (4 Nov 2026)

v03 = v02 (`README_C1_CODE_v02.md`, kept; it maps every R17 item to its fix) plus the researcher's rule of 4 Nov ("save the work done rather restart the entire experiment"), and test results re-recorded on the current files. `README_C1_CODE_v01.md` is kept too.

Outcome-blind: nothing here has read an AV2 outcome.

## New in v03

| File | What it is |
|---|---|
| `c1_rehearsal_v02.py` | `c1_rehearsal_v01` made resumable. Every step is written to `<out>/steps.jsonl` (start, end, exit code, seconds, UTC) and flushed to disk. A rerun skips every step that finished with exit 0. The mock plan is never rewritten once it exists. The runner steps keep their per-scene shards (`--resume`). |
| `c1_mstage_v02.py` | `c1_mstage_v01` (statistics unchanged) made resumable. E1-AV2 and E2-AV2 are checkpointed separately, by atomic write, as each finishes, with a key over tracker, sizes, seeds, the exact-CRC flag, the code hashes and the input hashes. A rerun reuses matching checkpoints. Each part's start and end go to `<out>.steps.jsonl`. **Use this for the method stage** (its longest step). |
| `tests/test_c1_v04.py` | REH2 (a step runs once and is skipped on rerun; a failed step is logged and not marked done) and MS2 (checkpoints reused; a deleted part is recomputed alone; a changed key recomputes). |

Already resumable: `c1_run_v02` (per-scene shards, `--resume`) and the 850-scene transfer fits (done). `c1_analyse_v03` takes minutes; it writes its outputs at the end.

## Which file to use

| Step | Use |
|---|---|
| Folds | `c1_folds_v02` |
| Fits | `c1_fit_v02` |
| Transfer | `c1_transfer_apply_v01` and `60_RESULTS/c1_transfer_fits_v01/` |
| Freeze | `c1_freeze_v02` |
| Stage B | `50_CODE/av2/av2_cache_stageB_v02` |
| Runs | `c1_run_v02` |
| Method stage | `c1_mstage_v02` |
| H8 | `c1_h8_v01` |
| H9, Q1 | `c1_predarm_v01` |
| Analysis | `c1_analyse_v03` |
| Rehearsal | `c1_rehearsal_v02` |
| Guards | `c1_guard_v01` |

## Results on the current files

The status file `70_TESTS/c1_v01/C1_V03_TEST_STATUS.json` records each suite's verdict and checks that the files tested are the ones hashed below.

| Suite | What it covers |
|---|---|
| `tests/test_c1_v01.py` | v01 rules, Choice 9, E15 tie, folds, generator |
| `tests/test_c1_v02.py` (heavy parts included) | method stage, H8, predictor arms with the QCNet alignment, freeze, RETUNED-HK1, generators |
| `tests/test_c1_v03.py` | every R17 fix: C2, M1, m2, m3, m5, m9, NaN, guards, folds v02, discriminating E15d, C3, generators |
| `tests/test_c1_v04.py` | resumability |

**Rehearsal** (`c1_rehearsal_v01.py`, 60 nuScenes scenes as units, mock frozen plan `6b7ada61…`, its own hash log; `70_TESTS/c1_v01/rehearsal60/`). The whole `--c1` path ran end to end, with exit 0 at every step: folds v02 → freeze v02 → fit v02 with provenance → transfer apply → `c1_run_v02 --c1-plan` (within and transfer, T1 and T3) → `c1_analyse_v03 --c1`.

Its decision is NO-GO, as expected at 60 units. The failed conditions are all named:
- M*'s floors on PD7, SD1_7 and PD, and HK1c on T3 PD;
- M* not less infeasible than B6, in V_t by Choice 9;
- **M*Jx's λ did not qualify in any fold** (12-unit folds; Choice 25 flags it and fails H3);
- the method-stage and H8 inputs absent.

Family S is labelled "supportive, not confirmatory (gate H1 not passed)".

**Reference run.** The lead's 375-scene pod stand-in, on v01 code (`70_TESTS/c1_v01/standin375/`), gives H1 on T1 (V = {B3}) and T3 (V = {B0, B3}) and H2, as K8 does.

## Open (unchanged from v02)

- **E⁰_r for H8.** It must be fixed in the plan before the freeze; this needs the lead's values.
- **Plan-text corrections (R17 m8).** For the plan's author.
- **Inputs owed by other helpers:**
  - the AV2 x1-layout exports and GT;
  - the AV2 tpp keys with `rec_sample_token` and `rec_instance_token`;
  - the 375-log list (slot S20).

## SHA-256 of every file to bind (the freeze verifies each one)

```
edc7ba861759a6538dbfbfc390816fd59a581816c3954362607e52d402230025  50_CODE/c1_av2/c1_guard_v01.py
58ea4a9246ed74fee2483309e8890a348f20fe3859f4a33367bc061aa2c834d9  50_CODE/c1_av2/c1_folds_v01.py
b38605675bdc217e8a40ab1f4deb0cfca662711b56f9d0726e5d58646a19ec1c  50_CODE/c1_av2/c1_folds_v02.py
4919ed20818b46cee13c3511444cc62ba44086b329fa2b98ffc0f17508a31494  50_CODE/c1_av2/c1_crc_exact_v01.py
b04e6ab475bdbbc1c460caad7180d276fd32c67934f4ce253273d41e5da9509e  50_CODE/c1_av2/c1_fit_v01.py
f377b364f8a0e5556c011436498d39fde28b24ae699963e6ec9f849a45574844  50_CODE/c1_av2/c1_fit_v02.py
f2cdf07abcb8eccd7049f33f772da1806de8c406d30450c3c35f4b91be8f26e8  50_CODE/c1_av2/c1_run_v01.py
cc68154adb090bab5f3c05ba23f4417f1049ddc61a76473fc75d910bbda667a0  50_CODE/c1_av2/c1_run_v02.py
33534de9ff6b7de62f1256e60d309b2d72d23fe60935d8adb45233ded95fa433  50_CODE/c1_av2/c1_analyse_v01.py
f5cd98d7d52a8cd7ee62781b42fcc05b7d93fb7d2ccc298af2cd3b30eff41e10  50_CODE/c1_av2/c1_analyse_v02.py
93c6fc3fa1712e229cb9f1ecc6fa6cf8bb90847cd08941ddd9e34cd59ea8a229  50_CODE/c1_av2/c1_analyse_v03.py
d1a40967cf117fd4c5e72069a68add4d6692d301dd3967848ce57aec7d0a9f6e  50_CODE/c1_av2/c1_freeze_v01.py
d7429b1c9af8b4743eb68ba6142614597854d96bf004ff4634d68046455818c6  50_CODE/c1_av2/c1_freeze_v02.py
8850a454c75fc277b414217862ef028c73da8d375e649805f6f45a0ce6d1bacf  50_CODE/c1_av2/c1_rehearsal_v01.py
1d050ddfaf457e0b8290050de4c941b98a88d578d70928705844433f8e6e2049  50_CODE/c1_av2/c1_mstage_v01.py
2500fb46de3d09b3308d316bcf24250d4516e28954a62608a064ad7e4f40a683  50_CODE/c1_av2/c1_h8_v01.py
3d9ee540c745171afeb31c4d2542dca07bc1ea11e085cfd3aedcb1f48bcfcbe0  50_CODE/c1_av2/c1_predarm_v01.py
9c909b9ba27ac207aa2653ec49963403f5fe59bad51d3e5732eb97d31a118bc3  50_CODE/c1_av2/c1_transfer_apply_v01.py
b31c59e26c1af2d09afe56931cd3b4a134009526874b3bca375f768aa57e3f68  50_CODE/c1_av2/run_c1_standin_v01.sh
2398714275b91e02c42031f52d3e8da1c5bd7a1bf2c9b35a649f7aa99dceaa96  50_CODE/c1_av2/tests/test_c1_v01.py
5560e7739adbc1908d11505f1aeaa0ac154f56e26601dfa5e39c22ed9b075cd3  50_CODE/c1_av2/tests/test_c1_v02.py
b8614df5785e9074de32ca778b0868745cfa595b369fd032881759fb91b45ecf  50_CODE/c1_av2/tests/test_c1_v03.py
020bc1da57b78397d643785b06d7521024d8d58792dd5e68a6db90fcd37c9af5  50_CODE/c1_av2/tests/make_c1_run_v01.py
e29d7475423c77e752d61c30a09cded1dd099862a174c1b1f7c2314d990e8766  50_CODE/c1_av2/tests/make_c1_run_v02.py
8cf6ef8fbfba501c026674b451aee2a381e7c47eeffca85fe61df6b7308432a7  50_CODE/c1_av2/tests/make_c1_analyse_v02.py
7a395665c3fe2da179d9a31712214c66937eba17c26dd9c08f30edc680245c0c  50_CODE/c1_av2/tests/make_av2_stageB_v02.py
c79f1639b7f75912c4a4944c3cebc927be9f4a061047ce9154a3f374c76f4585  50_CODE/c1_av2/tests/c1_standin_prep_v01.py
847d31d744bcb9da803c8fbdc5399b284e2c2ed814032796230bd55829cc4e1e  50_CODE/c1_av2/tests/c1_reproduce_check_v01.py
3cf6073c43b174a3dbde6b1f2b222b142049788078ad6078615e05ffc6eed4be  50_CODE/av2/av2_cache_stageB_v02.py
03881acdbf28e53afbe6c5f4de8aeb352e14ddd43ad9f2feff6c67217a528e01  50_CODE/k8/k8_sim_v04.py
98376598e3671ec96d2cdb05600dd565a021e73ec85b81330b9202ca78f1f3c8  50_CODE/k8/k8_run_v04.py
edd721dac4612b023e3e77b102bd1844cd74a700be6056de68072c0ea86fad94  50_CODE/k8/k8_analyse_v04.py
473e29ba2cc8a730cc80275fd3d98ceaa1d699923b33667d2232268dee130887  50_CODE/k8/k8_joint_fit_v02.py
badd72d3094a25da20b881aaeeb3ab9cc23231f29e05b78a2cf866b98ccf9e9d  50_CODE/k8/tests/make_k8_joint_v04.py
d646f4205298781b49f78dad4b71a900604076e76fca7fc97b36a858c4ccf2d5  50_CODE/k8/k8_sim_v02.py
e5e1e03779427da30f4be190779252c8353e0854bcad82593d8c281b4fdc1183  50_CODE/k8/k8_run_v02.py
868e4ff028e2e04072b2508dad57c0c3b29b4c030b34f9acff350ce7083c810a  50_CODE/k8/k8_analyse_v03.py
257bb10f5127c05eee82b81392a76e169e1becaaeaaa7d90acdf5aac0543aea4  50_CODE/k6/k6_sim_v02.py
9afb4dd848ac5614d4d351d404edc2b820030d9dfb67eee668407cc76cdecf61  50_CODE/k6/k6_analyse_v02.py
05b835a020b809265fa75a7d1d7a2f8995fa7b04f48b9075677114c14ec2857d  50_CODE/k7/k7_fit_v01.py
6d191e5c4d476bd1684d7c52dd2ba0b4ad3030e77648147432b5251f11bb54d5  50_CODE/m/m_lib_v04.py
67bf52a950e299d3775ee9f8b357dceb674a14ac2689d087a8ef1af189ec633f  50_CODE/m/m_data_v04.py
bfe6047b48902b195361a409f38cefeb7b0c451628918488e7186cfac5a20396  50_CODE/m/m_run_v04.py
f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd  50_CODE/x1/x1_lib_v03.py
b59dd08a407b8907d93386e7b136af973a5889444c3a0c84053d3e8a4a42bf64  50_CODE/x1/x1_full_v02.py
7025ea878bff9b1b2ae8c8a0a2765e197b1d7869dd16e468b28a2f00dfe53c00  50_CODE/x1/x2_full_v02.py
7df5d5726b00f0cd3f56c26325cb86edc8c5f74e139bfc5008a4aa366b6dde41  50_CODE/tpp/tpp_analyse_v01.py
32942ff8c1c08a6c633648587102fbf2389f5b510dcc05c7d5817ae572033c7f  50_CODE/tpp/tpp_common_v01.py
6177af5123f3f5522600643790e000a3c87229a2ef3acaaae047fc87f0455760  50_CODE/c1_av2/c1_rehearsal_v02.py
ce0f045834084af02edfee5a1b7675ececed754b7b20771d6d667392cbeeb668  50_CODE/c1_av2/c1_mstage_v02.py
ae07d6a9d9b533a7ccfa3cf1640ce46fdc0a7ebebd6d12d5f3bbb10866297b9c  50_CODE/c1_av2/tests/test_c1_v04.py
d38f26d30dc108df44e69a72fcbf3be34be4561addb6cc502b592feb16699151  50_CODE/c1_av2/README_C1_CODE_v01.md
3e5289867b584c8edaa4b13812b3beed8440ce3cc09091d60ca6812310ff4dce  50_CODE/c1_av2/README_C1_CODE_v02.md
```

(The freeze script hashes this README itself and adds it to the block.)
