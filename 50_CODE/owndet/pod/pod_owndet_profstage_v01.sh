#!/usr/bin/env bash
# pod_owndet_profstage_v01.sh (own-detector job, D18 v03 step 1, 2 Nov 2026): profiling stage on a fresh pod.
#   A: LT3D env (setup v05 + nuscenes + nntime + yapf pin) | fetch of the profiling subset (first 40 logs of train_475, with maps)
#   B: full fetch (train 700 + val 150) in the background, while the profiling runs
#   C: infos and GT database of the subset (pod_owndet_prep_v02.py, part prof40), then pod_owndet_profile_v01.py on four configurations:
#      P1 B=4 W=11 OMP=1 (the pilot's settings) with the torch profiler; P2 B=4 W=11 OMP=4; P3 B=8 W=11 OMP=4 (lr x2); P4 B=4 W=6 OMP=4
# Train lidar on the pod volume; val, venv, infos on the container disk. Markers in $R/logs/owndet_profstage_v01.log:
# PROFILE_STAGE_DONE, FETCH_ALL_DONE, PS_STOP <reason>.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work; L=/root/local; C=$R/code_owndet; CQ=$R/code_qcnet
mkdir -p "$R/logs" "$R/owndet" "$L"
LOG=$R/logs/owndet_profstage_v01.log
exec > >(tee -a "$LOG") 2>&1
echo "owndet profstage v01 start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "PS_STOP $*"; exit 1; }
MEM=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo 0); MEMGB=$((MEM / 1024 / 1024 / 1024))
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
NCPU=$(nproc); [ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
NPROC=$((NCPU - 1)); [ $NPROC -lt 2 ] && NPROC=2
echo "memory ${MEMGB} GB, CPU quota ${NCPU}"; nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv
S=$L/av2/sensor
mkdir -p /home/ubuntu/Workspace/Data "$S" "$R/av2data/train"; ln -sfn "$S" /home/ubuntu/Workspace/Data/Sensor
[ -L "$S/train" ] || ln -s "$R/av2data/train" "$S/train"
python3 -c "import json; print('\n'.join(json.load(open('$C/AV2_TRAIN_SPLIT_v01.json'))['train_475'][:40]))" > "$R/owndet/prof40_logs.txt"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
( has LT3D_SETUP_DONE "$R/logs/lt3d_setup_v05.log" || bash "$CQ/pod_lt3d_setup_v05.sh" > "$R/logs/lt3d_setup_v05_nohup.log" 2>&1
  has LT3D_NUSCENES_DONE "$R/logs/lt3d_nuscenes_v01.log" || bash "$CQ/pod_lt3d_nuscenes_v01.sh" > /dev/null 2>&1
  has LT3D_NNTIME_DONE "$R/logs/lt3d_nntime_v01.log" || bash "$CQ/pod_lt3d_nntime_v01.sh" > /dev/null 2>&1
  has LT3D_YAPF_DONE "$R/logs/lt3d_yapf_v01.log" || bash "$C/pod_lt3d_yapf_v01.sh" > /dev/null 2>&1 ) & PE=$!
has "AV2 FETCH DONE" "$R/logs/fetch_prof40.log" || python -B "$C/pod_av2_fetch_split_v06.py" --split train --logs-file "$R/owndet/prof40_logs.txt" --out "$S/train" --threads 96 --maps > "$R/logs/fetch_prof40.log" 2>&1
has "AV2 FETCH DONE" "$R/logs/fetch_prof40.log" || stop "subset fetch"
( has "AV2 FETCH DONE" "$R/logs/fetch_train_v06.log" || python -B "$C/pod_av2_fetch_split_v06.py" --split train --out "$S/train" --threads 96 --maps > "$R/logs/fetch_train_v06.log" 2>&1
  has "AV2 FETCH DONE" "$R/logs/fetch_val_v06.log" || { mkdir -p "$S/val"; python -B "$C/pod_av2_fetch_split_v06.py" --split val --out "$S/val" --threads 64 --maps > "$R/logs/fetch_val_v06.log" 2>&1; } ) & PF=$!
wait $PE
for m in LT3D_SETUP_DONE:lt3d_setup_v05 LT3D_NUSCENES_DONE:lt3d_nuscenes_v01 LT3D_NNTIME_DONE:lt3d_nntime_v01 LT3D_YAPF_DONE:lt3d_yapf_v01; do
  has "${m%%:*}" "$R/logs/${m##*:}.log" || stop "env ${m##*:}"
done
echo "env and subset ready $(date -u +%FT%TZ)"
source "$L/lt3d38/bin/activate"
I=$S/av2_owndet_infos
PR="python $C/pod_owndet_prep_v02.py --lt3d $L/LT3D --root $S --out $I --out-rel av2_owndet_infos --split $C/AV2_TRAIN_SPLIT_v01.json --procs $NPROC"
has "INFOS DONE prof40" "$R/logs/owndet_infos_prof40.log" || $PR infos --part prof40 > "$R/logs/owndet_infos_prof40.log" 2>&1
has "INFOS DONE prof40" "$R/logs/owndet_infos_prof40.log" || stop "prof40 infos"
has "GTDB DONE prof40" "$R/logs/owndet_gtdb_prof40.log" || $PR gtdb --db-part prof40 > "$R/logs/owndet_gtdb_prof40.log" 2>&1
has "GTDB DONE prof40" "$R/logs/owndet_gtdb_prof40.log" || stop "prof40 GT database"
PUB=$L/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
cd "$L/LT3D"
for spec in P1:4:11:1:prof P2:4:11:4:noprof P3:8:11:4:noprof P4:4:6:4:noprof; do
  IFS=: read -r name B W T PF2 <<< "$spec"
  O=$R/owndet/profile/$name
  has "PROFILE DONE" "$O/run.log" && continue
  mkdir -p "$O"
  python "$C/pod_owndet_cfg_v03.py" --lt3d "$L/LT3D" --public-cfg "$PUB" --infos-dir "$I" --data-root "$S/" --batch $B --workers $W \
    --train-infos av2_infos_prof40.pkl --db-infos av2_dbinfos_prof40.pkl --max-iters 1000 --work-dir "$O" --out "$O/cfg.py" > "$O/cfg.log" 2>&1 || { echo "$name cfg failed"; continue; }
  FLAG=""; [ "$PF2" = prof ] && FLAG="--profile"
  OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T timeout 1500 python "$C/pod_owndet_profile_v01.py" --lt3d "$L/LT3D" --cfg "$O/cfg.py" --iters 40 --workers $W --out "$O" $FLAG > "$O/run.log" 2>&1
  if has "PROFILE DONE" "$O/run.log"; then echo "$name done: $(python3 -c "import json; d=json.load(open('$O/profile_summary.json')); print('B', d['batch'], 'W', d['workers'], 's/it %.3f samples/s %.2f data %.3f' % (d['s_per_it'], d['samples_per_s'], d['data_wait_s']), 'sections', {k: round(v, 3) for k, v in d['sections_s'].items()}, 'bwd %.3f' % d['backward_step_s'], 'mem %.1f GB' % d['peak_memory_gb'])")";
  else echo "$name failed: $(grep -m1 -i "out of memory\|Error" "$O/run.log" | cut -c1-200)"; fi
done
echo "PROFILE_STAGE_DONE $(date -u +%FT%TZ)"
wait $PF
has "AV2 FETCH DONE" "$R/logs/fetch_train_v06.log" && has "AV2 FETCH DONE" "$R/logs/fetch_val_v06.log" && echo "FETCH_ALL_DONE $(date -u +%FT%TZ)" || echo "PS_STOP full fetch incomplete"
