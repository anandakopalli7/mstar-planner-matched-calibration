# Third-party code (not included; clone at these commits)

| Component | Upstream | Commit used | Licence (upstream) | How it was used |
|---|---|---|---|---|
| CANMOT (tracker T1, and Poly-MOT as configured in CANMOT, T3) | https://github.com/rst-tu-dortmund/CANMOT | `515d0792a4a2dddf4f3f26c2fa26c54bb1c14167` | BSD 3-Clause | Unmodified. Configurations `config/experiment/paper/local/canmot/sc.yaml` (T1) and `config/experiment/paper/baseline/poly_mot.yaml` (T3), as cited in the paper. |
| LT3D (CenterPoint detector code base; AB3DMOT and evaluation on Argoverse 2) | https://github.com/neeharperi/LT3D | `e33189aa09f282cf555b64dba1654eb0c14464a6` | See the upstream repository | Unmodified; only its `data/` and `tracking/` folders were used locally. The detector training configuration and our split are described in `50_CODE/owndet/` and Supplement S9.15. |
| Trajectron++ (learned predictor arm, H9) | https://github.com/StanfordASL/Trajectron-plus-plus | `ef0165a93ee5ba8cdc14f9b999b3e00070cd8588` | MIT | Unmodified; driven by `50_CODE/tpp/`. |
| ScenarioNet (data conversion utilities in an early stage) | https://github.com/metadriverse/scenarionet | `d4acdb5f5a844744fc85cb2dc3880d7d4a6eb170` | Apache 2.0 | Unmodified. |
| QCNet (history-coverage checks only) | https://github.com/ZikangZhou/QCNet | see `50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md` | See the upstream repository | Not used for any reported result. |

The status of each clone was checked with `git status`: no tracked file modified. LT3D was a partial checkout, so its other files show as deleted locally.
