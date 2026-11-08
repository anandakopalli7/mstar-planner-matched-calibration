# QCNet AV2 arm: design addendum B (v01, 2 Nov 2026, about 09:15 EST), D16 v05 Choice 18

**Status.** Written before the threshold is applied, before any pod for this step exists, and before any QCNet output on the thresholded histories. It adds to the design (`QCNET_AV2_ARM_DESIGN_v01.md`, `aa6e3ec0…`) and to addendum A (`8b249c56…`), both unchanged. The outcome-blind boundary is unchanged. The only AV2 facts used are the v02 counts cited in D16 v05 Choice 18.

## B1. Labels (D16 v05 Choice 18)

| Label | History source | Runs |
|---|---|---|
| **Primary deployed** | Matched AB3DMOT with T1's published-track threshold ("matched + SF") | v03 |
| Secondary | Matched AB3DMOT without the threshold | v02 |
| Descriptive | Released defaults | v01 |
| Upper bound | GT histories | — |

All of these use the re-centred QCNet runs. The v01 city-coordinate runs are kept as a record only.

## B2. The threshold: T1's SF_thre, cited

- **Selection.** T1 is `paper/local/canmot/sc`. That experiment selects `nusc_config_rotate_cov_cv` (`config/experiment/paper/local/canmot/sc.yaml`, line 6), which loads `preprocessing: centerpoint_nusc` (`config/poly_mot/nusc_config_rotate_cov_cv.yaml`, line 4).
- **Values.** `config/poly_mot/preprocessing/centerpoint_nusc.yaml`, line 1: `SF_thre: {0: 0.14, 3: 0.16, 1: 0, 2: 0.16, 5: 0.1, 6: 0, 4: 0.16}`. These are CANMOT @ `515d0792`, and the T1 × LT3D export record confirms them (`resolved_config.preprocessing.SF_thre`).
- **Per analysis class** (the port's labels):

  | Class | Label | SF_thre |
  |---|---|---|
  | car (`REGULAR_VEHICLE`) | 2 | **0.16** |
  | pedestrian | 4 | **0.16** |
  | cyclist (`BICYCLIST`) | bicycle, 0 | **0.14** |

## B3. Which score is thresholded

**What T1 thresholds.**
- The **detection score**: `src/canmot/dataloader/nusc_loader.py`, line 72, keeps a detection only if `score > SF_thre[class]`.
- The score of a track **updated in a frame** is that detection's score: `src/canmot/tracking/nusc_score_manage.py`, line 80, `update_score = final_score = raw_det score`.
- So every box T1 publishes for an updated track carries a score above SF_thre.

**AB3DMOT track score, defined to match.**
- The matched AB3DMOT publishes only tracks updated in the sweep (LT3D's `active`).
- Its row carries the matched detection's score: LT3D's `track_id_to_detection`, the `score` column of `trk10_ab3dmot_matched_3cls_v02.npz`.
- The track score of a published row is therefore that detection score, the same quantity T1 outputs for an updated track. It is causal; LT3D's non-causal `average_scores_across_track` is not used.

**Rule.**
- A matched row is published iff `score ≥ SF_thre[class]`. Compared in float64, this is the decision's "at or above".
- T1's loader uses strict `>`. Rows whose score equals the threshold are counted. If there are none, the two forms coincide.

## B4. Implementation and its one difference from T1

**Post-filter.** The rule is applied as a post-filter to `30_DATA/qcnet_av2_v02/trk10_ab3dmot_matched_3cls_v02.npz` (SHA-256 `8a616f9b4b756268d70b25fd5df793f68bf6b3831cff3cf652c466f4565feb73`). It is done on the laptop with one light process (`50_CODE/qcnet/qcnet_trk_sf_filter_v01.py`), writing `trk10_ab3dmot_matched_sf_3cls_v03.npz`. The tracker is not re-run.

**Difference from T1.**
- T1 drops sub-threshold detections **before** tracking.
- Here, those detections still update the matched tracker's state, hits and life, as in v02. They only are not published.
- This is the "published-track threshold" of Choice 18. The tracker's association is the v02 one.

**Histories and items.**
- Histories are the published rows only.
- Items use the same matching as v01 and v02: per-class Hungarian on published tracks at t₀, 2 m gate, visible GT.
- Agents are the tracks with at least one published row in the 50-step window.

## B5. QCNet run and counts

**QCNet run.**
- `qcnet_av2_infer_v03.py`, re-centred (addendum A2), unchanged, on pod `claude-programmeA-qcnet3`.
- The pod uses `runpod_claude_v03.ps1`, a volume, `-MaxCostPerHr 1.0`, and AV2 annotations, poses and maps only (`pod_av2_fetch_nolidar_v05.py`).
- The environment is built by `pod_qcnet_setup_v03.sh`; the checkpoint SHA-256 must be `b9f852ec…`.
- Jobs are started with `setsid nohup`. Uploads run in the background.

**Counts** (`pod_qcnet_pack_v03.py`), for matched + SF against GT, matched (v02) and released (v01):
- items per class × history stratum;
- `n_hist` distributions;
- agents per scene;
- track lengths;
- rows removed by the threshold;
- join coverage between sources and against the 2 Hz audit keys;
- finiteness and positive-definiteness.

**Budget and outputs.**
- Stop before a projected $13 total of Claude spend since 2 Nov, counting the lead's K8 CPU pod.
- Outputs: `30_DATA/qcnet_av2_v03/` and `60_RESULTS/qcnet_av2/QCNET_AV2_NOTE_v03.md`.
