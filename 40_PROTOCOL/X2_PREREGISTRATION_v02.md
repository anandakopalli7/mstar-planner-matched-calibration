# X2 pre-registration v02: confirmatory test on the 700 nuScenes train scenes (30 Oct 2026)

**Supersedes v01** (kept, never frozen). The changes answer review R05 (`70_TESTS/R05_X2_PREFREEZE_REVIEW_v01.md`): 0 critical, 5 major, 10 minor findings.

**Freeze.**
- This file is hashed with the code, inputs, environment listings and the X1 pre-registration in §0, after the train export passes Q0.
- The hash is also written to the session hand-over note and to memory.
- The text governs. Any later code change is a logged deviation.

## 0. Frozen code, inputs and environment

```
FROZEN_HASHES_BEGIN
setting  band=linear
9728e9f518e284e39e522c7252353f1342e7b9ffd682a742cd1eba9b646f8571  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_lib_v02.py
f78a7844ef61730d982d73cdebd690c53f190b693b426ba7fbd2106b26081cbd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_lib_v03.py
b59dd08a407b8907d93386e7b136af973a5889444c3a0c84053d3e8a4a42bf64  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_full_v02.py
a2d613f047ae09e37fb03291ef635ce6ac3055d67e49346a7fac88333a128538  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_prefreeze_v02.py
7025ea878bff9b1b2ae8c8a0a2765e197b1d7869dd16e468b28a2f00dfe53c00  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x2_full_v02.py
242714a9aace3fadf2ed5fa0bd6e340be38c3de4c6053aa838866af6233d2d76  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x2_prefreeze_v02.py
308c9457c06e2c2e2a26aef03fd9527674e156f05af04cb8991618c9cf365645  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x2_freeze_v02.py
3dfb23045fa2f8c26ed616120068886b196aa8062e3f383f0a252c95b46ce76d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_export_v04.py
d58ab11db1eeb163bc89202e8d3ec8a98cbd33956c84c5a9ec076845565268f4  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\fast_convex_v01.py
b19c4905d23cf94e6f3404d7ba950142afb9fd370805fa101ddebe88e133808c  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_split_detections_stream_v03.py
d0d3b91c30ee78c277639ecbd94b69397bf6bc4153752b3ebd070288e5894b89  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_gt_prep_v03.py
b823756f19ca23d4d36b6d97249f647182eee20a570c2f92a6149aeb2908c3e6  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\x1_horizon_prep_v01.py
8a8060ca19c400a5fe80b40fb78c07f6530ddc3d6ab565044e650dc6977a63ee  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\run_x2_train_export_fast_v02.sh
f1f12059cef7921a5c30289b8b4c66cc53cd8796a6c7a6f17286b7add2875d75  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\50_CODE\x1\run_x2_prefreeze_chain_v02.sh
ab9b8e05d1210950d06481da4cc4b202227cc859bf5b9df4a114b2d17e709485  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\X1_PREREGISTRATION_v02.md
a3e1f936218c10d75b4e1dd2104cdca7c1b982e1704f01904898fa199e38a6ea  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\X1_PREREGISTRATION_v02.sha256
d4385cd11734d039c5710a06491f1c1f89a83be801d4925a6b840f1bc3aa545d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\80_LOGS\pip_freeze_canmot310.txt
23f2d13de681963b279adbab0ff3cedabb587644cbf42bc03801b5a9be0b1bb9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\80_LOGS\pip_freeze_sim310.txt
964ea1889ad5f40dc3491989b2d37739c824dc35e2706002021a832bd07adb7d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker0\x1_tracks.jsonl.gz
a47deef7245ad50fd3da2f7af17c1084edf4ac34ed67c0990df7398c2bb57aaf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker0\x1_export_record.json
4578355659dc7d5d019f9f44a6c38ba148653d7d5ade12c24484af717581f662  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker0\x1_per_frame.json
eb25f03fb7ed1928897b3790e6eff29d86417dc8e71775a4e8ee516e66d973bf  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker1\x1_tracks.jsonl.gz
087136358a091882f58adb733ebb67c174008765de2c1fea8e7826c4754fa0eb  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker1\x1_export_record.json
a0d5d4490176a68af9544f0a7501c76bb00e68828ef7206e976b2ffbdf0b60e3  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker1\x1_per_frame.json
8ab657fc4b55e406e308dcf9c4c5bda14e2249ff5318fa93f3811bb548320eb2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker10\x1_tracks.jsonl.gz
17712c8a41832e22c0303b5e4269ef0e0bda76a0fa4d0323804c305d19ff67ec  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker10\x1_export_record.json
18068cdb08a73e56225ed428dee2c36cec436a1c143691d72f97478d4f112200  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker10\x1_per_frame.json
3846f0774e223b974b89db6892947b7f4cf72bbc2cb88097b6f6d596cab23c4b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker11\x1_tracks.jsonl.gz
c780fecdc7bc40195086b75542828d6300c75ab77f77eccd3a13558c46ff77dd  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker11\x1_export_record.json
c1197e13ea84231154e0e9220d05ba1c078c91274b843544bbcc6190e53910e5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker11\x1_per_frame.json
cc3200e39ede625b6250355fcfd0c14d534c7caca782a71a1739779851eea8ab  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker2\x1_tracks.jsonl.gz
87488c81449303353e7ac5546bac7471c4821c2e5ad48d470d20032b27a38e4a  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker2\x1_export_record.json
1412d3e19f3806a681c7c30055525f2a9f4657f0c09e82c8118a35b0602a7d85  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker2\x1_per_frame.json
684bed144db5c142855025bfd3f19934b7957549ba8dd5b6e51f27464b617073  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker3\x1_tracks.jsonl.gz
4e47d54b471c902c2db1df85813292fe1ae49f4e4277b89206f60c3c34bb05f5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker3\x1_export_record.json
c1f551e3c2379578095b8bfb23a8f87bb0a28d922a1ab56fbee32299dad5b4c7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker3\x1_per_frame.json
00a146675e7d58b586f96cc1f0563e7f461e45db4e0c00a88d3b590dde5d49f9  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker4\x1_tracks.jsonl.gz
4e6ca9470f2cea2ff7f9648144afd46e1ad08da1edbb5c5bb8d04cb75d22b332  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker4\x1_export_record.json
1c36ee1c01be04f4259045571aa9c35cbf2d4f70e7453e4f8864e1cff2f66ae8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker4\x1_per_frame.json
9aa13e330e5d12cb267b83e9b88cc196299d7ff02bda096182582aca3fe829a7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker5\x1_tracks.jsonl.gz
9cf0e1f8e43671116a343321464e6502196df0f0376fa9eef9952162422e807b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker5\x1_export_record.json
98d96b5ea04e92b56401eafb250e615c4674a09fb5dd4989d0a7721675387a31  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker5\x1_per_frame.json
052fc67cf16eba81850f88b0cf3cef96d22fa6396ffad164811427fa16665fc2  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker6\x1_tracks.jsonl.gz
f33ae2fc3296740b689bdfc99eb8c558b3e621c96ceaae8f8249d72f370ab362  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker6\x1_export_record.json
2b40513f68dcf9ea2ac60bba9044e31605253aadff94b3e4bf6aa44c677fde48  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker6\x1_per_frame.json
465efbd545734133e71a9e56db4f845f0ceec63417f274322069bb8a0cb6b521  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker7\x1_tracks.jsonl.gz
ecb6be3b3e78cea620a2274b2569ce1b646058e10eb4040f1de3dbc5972aad3d  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker7\x1_export_record.json
c9827c4cf4fe1a3a2af46b0d84f3d39ea035071b376c4f97c53d5abce36264b5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker7\x1_per_frame.json
1f5c09af8fd0fa71c34c38c4d5ce43943121c4e7d0b0d0c75ac3fa4337608326  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker8\x1_tracks.jsonl.gz
4614de1dbbc7374c517b52715c6b5971099675314e4b41ac66810762ded9b8c7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker8\x1_export_record.json
ec59b0018fa31ca4ef0bb94e9532f0c9ba75abb9353a0962f675f74930f48b35  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker8\x1_per_frame.json
c00f26f4a2d464490176946b2215a5981f7b237a014888f185c9f3b524fc93f7  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker9\x1_tracks.jsonl.gz
fbbfe86fb09a3ba35942f46cc2a4ed462d45389a4193dd444c7c28a204835a5b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker9\x1_export_record.json
4ec4cfb619647908b65303425d5fc1c42ff6fe5c077747d2d60fcc257b367819  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\worker9\x1_per_frame.json
93b4ac8b234f87ac152ce71c26e70e8bdb9eeb656242a44aa68bd654d5bf3d58  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\x2_gt\x2_train_gt_v03.json
bdc3211bfbfda652d5e9dab73c45c7132925ca84f869bf45e8e14edeafb1d20b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\nuscenes\v1.0-trainval\scene.json
1d2652e8055e26aa97f1d79a5586bb10196687856b6d8a489e1e71c580bde732  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\30_DATA\det_subsets_train700\split_receipt.json
b000cce3cc86d3552c9b06a5fd95c2313d0d820b02129941a89be00104025359  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x1_export_val150_fast_v04\EQUIVALENCE_vs_native_v02.json
d912b85d292bbedc9a96b555198a06d3da99665db80b373275be0bd434b7183f  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2_export_train700_fast_v02\EQUIVALENCE_train_partial_vs_native.json
8da9170cc0a084198fc7aa2a6fc7aa09c9834e499da1babfaa269b8ff2df72c5  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_horizon_v01.jsonl.gz
ec27cdcd4cfc9703e7eaf5ebe14df6ab339160cd4e8b72d202731d04cb32807b  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_sizes_v02.json
26d9485e7f69b56529ff14aa8d6a2ac9edb337fd7161007ea221a8ee374aa871  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_fwer_v02.json
56253dcef9eb4f0c368e9d0cc4324473908ddf6d390e564b5a69cb73bbc435f1  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_oc_q4_v02.json
690af66a729330c1cbbfc925de217aea7698d9df15e9da41904a03986850b1f8  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_power_v02.json
a1ed29933d92bc0e3fa476a9d2b353f607873b319c65a796159184b45823cb42  C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\60_RESULTS\x2\x2_synthetic_scale_test_v02.json
FROZEN_HASHES_END
```

## 1. What X2 tests, and how it differs from X1 (R05 m6)

**Origin.** X1 was pre-registered on val. Its G1 required failure of the projected tail *and* that NEES miss it. It was not shown. Descriptively, CANMOT's own **2 s prediction** for in-path cars was:
- too narrow **laterally** (E = 0.135–0.175);
- far too wide **longitudinally** (E ≈ 0.005).

X2 is a **new hypothesis generated from those descriptive results**. It is tested on fresh data: the 700 train scenes, which share no scene or log with val.

**Declaration.** Before this file, neither the calibration nor the NEES of CANMOT on train scenes was examined by this line.

**Change from X1's G1.** X1's NEES condition (b) is dropped from G1. In X1, NEES *did* flag the 2 s covariance as overconfident; it misdirected the fix rather than missing the problem. The NEES claim becomes its own gated step, H3.

## 2. Hypotheses and decision: fixed sequence at α = 0.05 (R05 M1, M2, m7)

**Decision cells (h2s family, in-path cars, σ_a = 0.10 m).** Car < 20 m and car 20–40 m, each lateral and longitudinal.

**The band.** One two-sided 95 % sup-t band, scene-cluster bootstrap with B = 2000, spanning **these 4 cells only** (R05 M3). FAILS and OVERCOVERS are as in X1 v02 §8.
- A decision cell with zero bootstrap SE counts as **not shown** (R05 m8).

**Step 1, H1 (lateral under-coverage).** For at least one range bin, the lateral cell meets all of:
- (a1) it FAILS against max(0.05, E⁰);
- (a2) the extra lateral margin Δ has a scene-bootstrap one-sided 97.5 % lower bound > h₀ = 0.10 m (B = 2000);
- (a3) it FAILS at σ_a = 0.20 m;
- (a4) it FAILS with contested records excluded;
- (a5) it FAILS in the truth-oriented analysis, with a band over the same 4 cells.

**Step 2, H2 (the price of a single scalar).** Tested only in a bin where H1 holds.
- Let s_lat be the smallest variance factor that brings the lateral cell to ≤ 0.05, and s_long the same for the longitudinal cell.
- The **price** is the median, over longitudinal records, of z₀.₉₅·[√(s_lat·V + σ_a²) − √(s_long·V + σ_a²)]. It is the extra longitudinal margin that any single scalar factor large enough to fix the lateral axis imposes, beyond what the longitudinal axis needs.
- **H2 holds** if the scene-bootstrap one-sided 97.5 % lower bound of the price is > h₀ = 0.10 m (B = 2000; the lateral and longitudinal cells are resampled jointly).
- This replaces v01's "opposite directions" test, which only restated E_lat > 0.05 and E_long < 0.05 (R05 M1).
- The claim it supports is: "a single scalar correction that fixes the lateral tail over-pays the longitudinal margin by more than 10 cm." It is **not** "no scalar can fix it".

**G1 (X2) holds** if and only if H1 and H2 both hold in at least one bin.

**Step 3, H3 (NEES misdirection).** Tested only if G1 holds, in a bin where it holds.
- The NEES-guided scalar is k = ANEES/2, from the 2-D NEES over the class × range group. It is applied to Σ̂ + σ_a² I, consistently with how ANEES is computed (R05 m2).
- **H3 holds** if, after this scaling, either:
  - the lateral exceedance has a one-sided 97.5 % lower bound > 0.05 (NEES-guided scaling still under-covers laterally); or
  - the longitudinal extra margin it adds has a one-sided 97.5 % lower bound > h₀.
- A NEES claim is made only if H3 holds. Otherwise NEES is reported descriptively.

**Error control (R05 m1).** Within a bin, the claim is an intersection–union test of level α. Across the two bins, both lateral cells are covered by the **same** 95 % simultaneous band, so P(some lateral cell falsely FAILS) ≤ P(the band misses some cell). §5 checks this by simulation and requires it to be ≤ 0.05 + 2 MC SE. Steps 2 and 3 are gated, so the sequence keeps the family-wise level at α.

**What may be claimed if only H1 holds (R05 m7).** "CANMOT's 2 s predicted covariance under-covers the lateral tail for in-path cars" (H1 is level-α on its own), but no claim about scalar corrections.

## 3. Data and stack, and the direction of bias (R05 M4)

| Item | Value |
|---|---|
| Scenes | the devkit's 700 train scenes |
| Detections | CenterPoint (flip) train file, SHA-256 `547fdb7d…327145`, which equals CANMOT's `PAPER_INPUT_HASHES['train']`. The detector was trained on these scenes, so it is **in-sample**. |
| Tracker | the same CANMOT commit and experiment `paper/local/canmot/sc`, with split = train. Q was tuned (for AMOTA) on val, so it is **out-of-sample here**. R is the trainval sample covariance, so it is **in-sample**. |
| Export | `x1_export_v04.py --fast-convex`, in 12 subsets (`x1_split_detections_stream_v03.py`). The streaming splitter reproduces the val file exactly. Fast mode is record-identical to native on all 150 val scenes (381,553 records) and on 85 train scenes the native run had finished (223,490 records): `60_RESULTS/x2_export_train700_fast_v02/EQUIVALENCE_train_partial_vs_native.json`. |
| Ground truth | `x1_gt_prep_v03.py --split train`: 28,130 samples, 725,431 tracking-class annotations, 2,439 racks |
| Analysis | `x2_full_v02.py`, using `x1_lib_v03.py` (analysis logic identical to v02; unpaired and censored rows dropped for memory) through the `x1_full_v02.py` functions. Bands at 95 %; price bootstrap B = 2000. |

**Direction of bias from in-sample detections (corrected; R05 M4).** It is **not established**:
- Better detections make filtered position errors smaller. With R unchanged, that makes the exported covariance *relatively larger*, which pushes toward over-coverage and against H1.
- But the 2 s lateral error is dominated by unmodelled motion (lane changes, curvature). That is detector-independent, and Q is out-of-sample.

So X2 tests replication on train scenes **under these conditions**, and the article states both directions.

## 4. Everything else

As in X1 pre-registration v02, which is frozen and hashed in §0:
- pairing, rack filter, in-path, separating axes, toward-ego orientation using the CTRV ego prediction;
- σ_a handling, orientation null, NEES, prices and certification (K5 at h2s), and the sensitivities.

**Differences for X2.**
- **Scene set.** It is all 700 train scenes, including any scene with no paired record.
- **t0 family.** It is reported descriptively, without the gate-4 m and re-matching sensitivities.
- **X1-rule output.** The X1-rule `G1_family` in the output is labelled for reference only. The key `lo_bonf` means the 2.5 % quantile (R05 m5).

## 5. Before the freeze (allowed outputs only)

**Allowed:**
- the export and its integrity records;
- pairing counts;
- per-cell and per-scene counts and the median SD;
- the orientation null;
- the **FWER** simulation: logit-scale scene effects, τ = 0.5 and τ = 1.0, E = 0.05, 4 decision cells, B = 2000, 500 replicates;
- the **power** simulation for (a1) (R05 M3): lateral E = 0.05 + f·(E_X1 − 0.05), f ∈ {0.6, 0.8, 1.0}, longitudinal cells at X1 values, thresholds from the train E⁰;
- the Q4 operating characteristics;
- a synthetic run of `x2_full_v02.py` at train scale, to check memory and time (R05 M5).

**Not allowed:** any U value, residual, NEES or exceedance on train.

## 6. Binding and records (R05 m3, m4)

- The run's inputs (ground truth, horizon file, OC file, every worker's export) must each match a hash in §0, or the run refuses to start.
- The frozen list includes:
  - the X1 pre-registration;
  - the run scripts;
  - the `pip freeze` output of both environments.

## 7. If G1 (X2) does not hold

Report exactly which step and which condition failed. The next steps are decided now:
1. A pooled val + train analysis, labelled exploratory.
2. A second tracker covariance model (CANMOT's sample-covariance configuration).
3. Re-framing the problem around whatever replicates.

Nothing is claimed without a confirmatory pass.
