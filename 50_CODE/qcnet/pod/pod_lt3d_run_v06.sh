#!/usr/bin/env bash
# pod_lt3d_run_v06.sh (QCNet arm, 2 Nov 2026) = pod_lt3d_run_v05.sh with the test step run as K=$SHARDS (default 6) concurrent
# tools/test.py processes on contiguous shards of the infos, merged in order (pod_lt3d10_shard_v01.py): v05's 20 loader
# workers did not help (0.9 sweeps/s), because the bottleneck is a per-box Python loop in LT3D's CenterHead in the main
# process. Per-sweep inference (batch size 1) makes the merged output the single-process one. Each process: 3 loader workers.
# pod_lt3d_run_v05.sh = pod_lt3d_run_v04.sh with the test step's data loading widened: tools/test.py
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
echo "lt3d10 run v06 start $(date -u +%FT%TZ) step=$STEP nproc=$NPROC shards=${SHARDS:-6}"
has() { grep -q "$1" "$R/logs/lt3d10_run.log" 2>/dev/null; }
run() { [ "$STEP" = all ] || [ "$STEP" = "$1" ]; }

if run prep10 && ! has STEP10_prep10_DONE; then
  python "$R/code_qcnet/pod_lt3d10_prep_v01.py" --lt3d "$L/LT3D" --root /home/ubuntu/Workspace/Data/Sensor --out "$ANN10" --procs "$NPROC" > "$R/logs/lt3d10_prep.log" 2>&1 || { tail -30 "$R/logs/lt3d10_prep.log"; exit 1; }
  tail -3 "$R/logs/lt3d10_prep.log"
  echo STEP10_prep10_DONE
fi
if run test && ! has STEP10_test_DONE; then
  K=${SHARDS:-6}
  SH=$O/shards
  mkdir -p "$SH"
  python "$R/code_qcnet/pod_lt3d10_shard_v01.py" split --infos "$ANN10" --k $K --out-prefix "$SH/infos10" > "$R/logs/lt3d10_shard_split.log" 2>&1 || { tail -n 20 "$R/logs/lt3d10_shard_split.log"; exit 1; }
  pids=()
  for i in $(seq 0 $((K - 1))); do
    if [ -s "$SH/pred10_shard$i.pkl" ]; then continue; fi
    OMP_NUM_THREADS=2 MKL_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 python tools/test.py "$CFG" "$CK" --out "$SH/pred10_shard$i.pkl" --cfg-options "data.test.ann_file=$SH/infos10_shard$i.pkl" "data.test_dataloader.workers_per_gpu=3" > "$R/logs/lt3d10_test_shard$i.log" 2>&1 &
    pids+=($!)
    echo "shard $i pid $!"
  done
  fail=0
  for p in "${pids[@]}"; do wait $p || fail=1; done
  [ $fail -eq 0 ] || { for i in $(seq 0 $((K - 1))); do tail -n 5 "$R/logs/lt3d10_test_shard$i.log"; done; exit 1; }
  python "$R/code_qcnet/pod_lt3d10_shard_v01.py" merge --k $K --pred-prefix "$SH/pred10" --out "$O/predictions_lt3d_centerpoint_av2val10_v01.pkl" --lt3d "$L/LT3D" > "$R/logs/lt3d10_shard_merge.log" 2>&1 || { tail -n 20 "$R/logs/lt3d10_shard_merge.log"; exit 1; }
  tail -n 2 "$R/logs/lt3d10_shard_merge.log"
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
