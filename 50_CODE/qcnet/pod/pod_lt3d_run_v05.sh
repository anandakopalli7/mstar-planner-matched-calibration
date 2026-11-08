#!/usr/bin/env bash
# pod_lt3d_run_v05.sh (QCNet arm, 2 Nov 2026) = pod_lt3d_run_v04.sh with the test step's data loading widened: tools/test.py
# defaults to 2 loader workers (0.9 sweeps/s, GPU 14 % busy on the RTX 3090, ETA 7 h), so the test step now passes
# data.test_dataloader.workers_per_gpu=$TEST_WORKERS (default 20) and runs with OMP_NUM_THREADS=2. No model, data or output change.
# pod_lt3d_run_v04.sh = 50_CODE/av2/pod/pod_lt3d_run_v02.sh + pod_lt3d_stage2_v01.sh, changed for 10 Hz:
#   prep10  infos for EVERY sweep (sample rate 1) with LT3D's generate_info, 5 sweeps, parallel per log (pod_lt3d10_prep_v01.py)
#   test    the released checkpoint on those infos (tools/test.py --out; the config's ann_file overridden by --cfg-options)
#   split   one pickle per log (pod_lt3d10_export_v01.py split)
#   export  LT3D's format_results per log -> AV2 tables; three-class npz
#   ap      official av2 AP at 50 m, ROI-filtered, three analysis classes, all sweeps
#   repro   2 Hz subset against the detector stage's 2 Hz detections
# Data, LT3D venv and checkpoint on the container disk L=/root/local; outputs and logs on the pod volume R=/root/work.
# Data: $L/av2/sensor/val (fetched with maps); /home/ubuntu/Workspace/Data/Sensor -> $L/av2/sensor so the config runs unchanged.
# Markers STEP10_<name>_DONE in $R/logs/lt3d10_run.log. Argument: one step name or all. NPROC: worker processes (env).
set -euo pipefail
R=/root/work
L=/root/local
C=$L/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2
CFG=$C/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
CK=$C/epoch_20.pth
O=$R/out_lt3d10
STEP=${1:-all}
NPROC=${NPROC:-8}
mkdir -p "$R/logs" "$O" /home/ubuntu/Workspace/Data
ln -sfn "$L/av2/sensor" /home/ubuntu/Workspace/Data/Sensor
exec > >(tee -a "$R/logs/lt3d10_run.log") 2>&1
source "$L/lt3d38/bin/activate"
cd "$L/LT3D"
ANN10=$O/av2_infos_val_10hz_v04.pkl
echo "lt3d10 run v05 start $(date -u +%FT%TZ) step=$STEP nproc=$NPROC test_workers=${TEST_WORKERS:-20}"
has() { grep -q "$1" "$R/logs/lt3d10_run.log" 2>/dev/null; }
run() { [ "$STEP" = all ] || [ "$STEP" = "$1" ]; }

if run prep10 && ! has STEP10_prep10_DONE; then
  python "$R/code_qcnet/pod_lt3d10_prep_v01.py" --lt3d "$L/LT3D" --root /home/ubuntu/Workspace/Data/Sensor --out "$ANN10" --procs "$NPROC" > "$R/logs/lt3d10_prep.log" 2>&1 || { tail -30 "$R/logs/lt3d10_prep.log"; exit 1; }
  tail -3 "$R/logs/lt3d10_prep.log"
  echo STEP10_prep10_DONE
fi
if run test && ! has STEP10_test_DONE; then
  OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python tools/test.py "$CFG" "$CK" --out "$O/predictions_lt3d_centerpoint_av2val10_v01.pkl" --cfg-options "data.test.ann_file=$ANN10" "data.test_dataloader.workers_per_gpu=${TEST_WORKERS:-20}" > "$R/logs/lt3d10_test.log" 2>&1 || { tail -40 "$R/logs/lt3d10_test.log"; exit 1; }
  tail -c 2000 "$R/logs/lt3d10_test.log" | tail -n 5
  ls -la "$O"
  echo STEP10_test_DONE
fi
for s in split export ap repro; do
  if run $s && ! has "STEP10_${s}_DONE"; then
    case $s in
      split)  args=(--pred "$O/predictions_lt3d_centerpoint_av2val10_v01.pkl" --infos "$ANN10") ;;
      export) args=(--procs "$NPROC") ;;
      ap)     args=(--data /home/ubuntu/Workspace/Data/Sensor/val --procs "$NPROC") ;;
      repro)  args=(--ref "$R/ref/av2val_lt3d_centerpoint_dets_v01.npz") ;;
    esac
    python "$R/code_qcnet/pod_lt3d10_export_v01.py" $s --lt3d "$L/LT3D" --out "$O" "${args[@]}" > "$R/logs/lt3d10_$s.log" 2>&1 || { tail -40 "$R/logs/lt3d10_$s.log"; exit 1; }
    tail -n 8 "$R/logs/lt3d10_$s.log"
    echo "STEP10_${s}_DONE"
  fi
done
echo "lt3d10 run end $(date -u +%FT%TZ)"
echo LT3D10_RUN_DONE
