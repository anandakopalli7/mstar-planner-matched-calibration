#!/usr/bin/env bash
# pod_lt3d_run_v01.sh: Argoverse 2 val -> LT3D CenterPoint (5 sweeps, velocity) detections on the pod (D15 §3: primary detector).
# The released config reads AV2 feathers from /home/ubuntu/Workspace/Data/Sensor/; a symlink to our data folder lets it run unchanged.
# Steps (argument: prep | test | export | all), logged to /root/work/logs/lt3d_run.log with STEP_lt3d_<name>_DONE markers:
#   prep    val-only infos with LT3D's own converter (train/test split lists cleared; 2-D and GT-database steps skipped)
#   test    inference with the released checkpoint; predictions saved with --out (no --eval: LT3D's evaluate imports a fork-only API)
#   export  LT3D's format_results -> standard AV2 table with velocity, pickle-free npz + feather; detector AP with the official av2 evaluator
# Outcome-blind rule (D15 §4): detector AP and counts only.
set -euo pipefail
R=/root/work
C=$R/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2
CFG=$C/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
CK=$C/epoch_20.pth
O=$R/out_lt3d
STEP=${1:-all}
mkdir -p "$R/logs" "$O" /home/ubuntu/Workspace/Data
ln -sfn "$R/OpenPCDet/data/argo2/sensor" /home/ubuntu/Workspace/Data/Sensor
exec > >(tee -a "$R/logs/lt3d_run.log") 2>&1
source "$R/lt3d38/bin/activate"
cd "$R/LT3D"
ANN=$(python -c "from mmcv import Config; c = Config.fromfile('$CFG'); print(c.data.test.ann_file)")
echo "lt3d run start $(date -u +%FT%TZ) step=$STEP ann_file=$ANN"

if [ "$STEP" = all ] || [ "$STEP" = prep ]; then
  mkdir -p "$(dirname "$ANN")"
  python - "$ANN" <<'PY'
import os, sys
sys.path.insert(0, os.getcwd())
import tools.data_converter.av2_converter as c
ann = sys.argv[1]
out_dir, base = os.path.split(ann)
assert base.endswith("_infos_val.pkl"), base
prefix = base[: -len("_infos_val.pkl")]
c.TRAIN, c.TEST = [], []
present = set(os.listdir("/home/ubuntu/Workspace/Data/Sensor/val"))
missing = [l for l in c.VAL if l not in present]
print("val logs in split list:", len(c.VAL), "present:", len(present), "missing:", len(missing), flush=True)
assert not missing, missing[:3]
c.create_av2_infos("/home/ubuntu/Workspace/Data/Sensor", prefix, out_dir, max_sweeps=5)
import pickle
infos = pickle.load(open(ann, "rb"))
print("val infos:", len(infos), "logs:", len({i["log_id"] for i in infos}), flush=True)
PY
  echo STEP_lt3d_prep_DONE
fi

if [ "$STEP" = all ] || [ "$STEP" = test ]; then
  python tools/test.py "$CFG" "$CK" --out "$O/predictions_lt3d_centerpoint_av2val_v01.pkl" > "$R/logs/lt3d_test.log" 2>&1 || { tail -40 "$R/logs/lt3d_test.log"; exit 1; }
  tail -5 "$R/logs/lt3d_test.log"
  ls -la "$O"
  echo STEP_lt3d_test_DONE
fi

if [ "$STEP" = all ] || [ "$STEP" = export ]; then
  python "$R/code/pod_lt3d_export_v01.py" --cfg "$CFG" --pred "$O/predictions_lt3d_centerpoint_av2val_v01.pkl" --out "$O" > "$R/logs/lt3d_export.log" 2>&1 || { tail -40 "$R/logs/lt3d_export.log"; exit 1; }
  tail -25 "$R/logs/lt3d_export.log"
  cp "$R/logs/lt3d_"*.log "$R/logs/lt3d_"*.txt "$O/" 2>/dev/null || true
  (cd "$O" && sha256sum *.npz *.feather *.json *.csv 2>/dev/null > SHA256SUMS.txt)
  echo STEP_lt3d_export_DONE
fi
echo "lt3d run end $(date -u +%FT%TZ)"
echo LT3D_RUN_DONE
