# Data

No dataset files are included.

**The datasets.** Obtain them from their providers and use them under the providers' terms; both are published for non-commercial research.
- **nuScenes v1.0 (trainval),** Motional: https://www.nuscenes.org/. The development stages use it: the diagnosis, the method stage, and the planner study K8.
- **Argoverse 2 Sensor dataset,** Argo AI: https://www.argoverse.org/av2.html. The registered test uses 375 logs: the 150 validation logs, and 225 training logs held out from our detector by a seeded permutation (`50_CODE/owndet/AV2_TRAIN_SPLIT_v01.json`).

**Frozen data files not included.** The registered plan binds 354 files by SHA-256. 190 are code and protocol files, and they are here. The other 164 are data:
- annotation-derived ground truth prepared for the analysis;
- stage-A caches;
- detections and tracker outputs;
- exports of the nuScenes stages.

Of those 164, the small aggregate results (folds, fitted thresholds, tracking metrics, equivalence checks, E⁰, power counts) are included. The remaining 118 are listed with path, size and hash in `EXCLUDED_FROZEN.tsv`. They total about 2.8 GB and are derived from the datasets. They can be regenerated with the code here, and their hashes allow an exact check.

**Derived data, if deposited.** If the authors deposit them in a data archive (OSF or Zenodo), the link is given here: **[data archive: to be added, or "not deposited"]**. The licence must respect the datasets' terms.

**Results bundles of record.** The run log, the stage-B log and the results of record were uploaded to the OSF project with the registration: `C1_RESULTS_A_v01.zip` (essential) and `C1_RESULTS_B_v01.zip` (full run outputs, 1.9 GB) **[OSF link: to be added]**.
