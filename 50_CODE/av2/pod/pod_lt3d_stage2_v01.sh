#!/usr/bin/env bash
# pod_lt3d_stage2_v01.sh: LT3D on pod 2 after the master script was stopped (its single-process prep ran at ~30 s per log).
# prep: the same per-log loop as pod_lt3d_run_v02.sh (LT3D's generate_info, VAL list, VAL_SAMPLE_RATE, 5 sweeps), run over
#       12 worker processes; Pool.map keeps c.VAL order, so the info list equals the sequential one.
# then pod_lt3d_run_v02.sh test and export. The OpenPCDet resume script waits for STEP_lt3d_test_DONE before its own
# inference, so the GPU runs one job at a time. Markers in /root/work/logs/lt3d_run.log; final LT3D_PIPELINE_DONE / LT3D_FAILED.
set -uo pipefail
R=/root/work
C=$R/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2
CFG=$C/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
mkdir -p /home/ubuntu/Workspace/Data
ln -sfn "$R/OpenPCDet/data/argo2/sensor" /home/ubuntu/Workspace/Data/Sensor
exec > >(tee -a "$R/logs/lt3d_run.log") 2>&1
echo "=== lt3d stage2 v01 start $(date -u +%FT%TZ)"
source "$R/lt3d38/bin/activate"
cd "$R/LT3D"
ANN=$(python -c "from mmcv import Config; c = Config.fromfile('$CFG'); print(c.data.test.ann_file)")
if ! grep -q STEP_lt3d_prep_DONE "$R/logs/lt3d_run.log"; then
  mkdir -p "$(dirname "$ANN")"
  python - "$ANN" <<'PY' || { echo "LT3D_FAILED at parallel prep"; exit 1; }
import os, sys, pickle
from multiprocessing import Pool
from pathlib import Path
sys.path.insert(0, os.getcwd())
import mmcv
import tools.data_converter.av2_converter as c
ann = sys.argv[1]
root_path = "/home/ubuntu/Workspace/Data/Sensor"
present = set(os.listdir(root_path + "/val"))
missing = [l for l in c.VAL if l not in present]
print("val logs in split list:", len(c.VAL), "present:", len(present), "missing:", len(missing), flush=True)
assert not missing, missing[:3]
name2cid = {cl: i for i, cl in enumerate(c.class_names)}

def one_log(log_id):
    log_dir = "{root_path}/{split}/{log_id}".format(root_path=root_path, split="val", log_id=log_id)
    lidar_paths = "{log_dir}/sensors/lidar".format(log_dir=log_dir)
    annotations_path = "{log_dir}/annotations.feather".format(log_dir=log_dir)
    annotations = c.read_feather(Path(annotations_path))
    mmcv.check_file_exist(annotations_path)
    all_timestamps = sorted([int(filename.split(".")[0]) for filename in os.listdir(lidar_paths)])
    out = []
    for i, filename in enumerate(sorted(os.listdir(lidar_paths))):
        if i % c.VAL_SAMPLE_RATE != 0:
            continue
        out.append(c.generate_info(filename, log_id, log_dir, annotations, name2cid, all_timestamps, 5))
    return out

with Pool(12) as pool:
    parts = pool.map(one_log, list(c.VAL), chunksize=1)
val_infos = [info for part in parts for info in part]
pickle.dump(val_infos, open(ann, "wb"))
infos = pickle.load(open(ann, "rb"))
print("val infos:", len(infos), "logs:", len({i["log_id"] for i in infos}), flush=True)
PY
  echo STEP_lt3d_prep_DONE
fi
for s in test export; do
  grep -q "STEP_lt3d_${s}_DONE" "$R/logs/lt3d_run.log" && continue
  bash "$R/code/pod_lt3d_run_v02.sh" "$s" || { echo "LT3D_FAILED at $s"; exit 1; }
done
echo LT3D_PIPELINE_DONE
