#!/usr/bin/env bash
# pod_owndet_master_v02.sh (own-detector job, 2 Nov 2026) = pod_owndet_master_v01.sh + pod_lt3d_yapf_v01.sh before the pilot (v01 stopped at
# the pilot config: mmcv's Config.dump needs yapf < 0.40). Stages 1-2 are skipped by their DONE lines. Log: owndet_master_v02.log.
# pod_owndet_master_v01.sh (own-detector job, 2 Nov 2026): stages 1-3 of 50_CODE/owndet/OWN_DETECTOR_DESIGN_v01.md on pod
# claude-programmeA-owndet; stops after the pilot (the epoch choice is recorded on the laptop before the full run).
#   stage 1 (parallel): AV2 val (150 logs) and train (700 logs) with maps (pod_av2_fetch_split_v06.py) | LT3D env
#                       (50_CODE/qcnet/pod: pod_lt3d_setup_v05.sh, pod_lt3d_nuscenes_v01.sh, pod_lt3d_nntime_v01.sh)
#   stage 2: infos train475 / held225 / val150 (every 5th sweep), GT database from train475 (pod_owndet_prep_v01.py)
#   stage 3: pilot (300 iterations; B = 4, then 2, then 1 on CUDA OOM) and its summary (pod_owndet_pilot_v01.py)
# Val data, venv, infos and GT database on the container disk (L=/root/local); train lidar, logs, configs and work dirs on the volume.
# Each step is skipped when its DONE line is in its own log. Markers in $R/logs/owndet_master_v01.log: OD_PILOT_DONE / OD_STOP.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work; L=/root/local; C=$R/code_owndet; CQ=$R/code_qcnet
mkdir -p "$R/logs" "$R/owndet" "$L"
LOG=$R/logs/owndet_master_v02.log
exec > >(tee -a "$LOG") 2>&1
echo "owndet master v02 start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "OD_STOP $*"; exit 1; }
MEM=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup/memory.max 2>/dev/null || echo max)
[ "$MEM" = max ] && MEM=$(awk '/MemTotal/ {print $2*1024}' /proc/meminfo)
MEMGB=$((MEM / 1024 / 1024 / 1024)); NCPU=$(nproc)
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
[ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
if [ -f /sys/fs/cgroup/cpu.max ]; then read -r q2 p2 < /sys/fs/cgroup/cpu.max; [ "$q2" != max ] && NCPU=$((q2 / p2)); fi
NPROC=$(( MEMGB / 3 )); [ $NPROC -gt $((NCPU - 1)) ] && NPROC=$((NCPU - 1)); [ $NPROC -lt 2 ] && NPROC=2
WK=$((NCPU - 2)); [ $WK -gt 12 ] && WK=12; [ $WK -lt 2 ] && WK=2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "memory ${MEMGB} GB, CPU quota ${NCPU}, worker processes ${NPROC}, loader workers ${WK}"
nvidia-smi --query-gpu=name,memory.total --format=csv; df -h /root | tail -n 1
S=$L/av2/sensor
mkdir -p /home/ubuntu/Workspace/Data "$S"; ln -sfn "$S" /home/ubuntu/Workspace/Data/Sensor
# train lidar (~110 GB) on the pod volume, everything else on the 150 GB container disk (no larger disk was available)
mkdir -p "$R/av2data/train"; [ -L "$S/train" ] || ln -s "$R/av2data/train" "$S/train"

# ---- stage 1
( has "AV2 FETCH DONE" "$R/logs/fetch_val_v06.log" || { mkdir -p "$S/val"; python -B "$C/pod_av2_fetch_split_v06.py" --split val --out "$S/val" --threads 96 --maps > "$R/logs/fetch_val_v06.log" 2>&1; } ) & PV=$!
( has "AV2 FETCH DONE" "$R/logs/fetch_train_v06.log" || { python -B "$C/pod_av2_fetch_split_v06.py" --split train --out "$S/train" --threads 128 --maps > "$R/logs/fetch_train_v06.log" 2>&1; } ) & PT=$!
( has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup_v05.log" || bash "$CQ/pod_lt3d_setup_v05.sh" > "$R/logs/lt3d_setup_v05_nohup.log" 2>&1
  has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup_v05.log" && { has LT3D_NUSCENES_DONE "$R/logs/lt3d_nuscenes_v01.log" || bash "$CQ/pod_lt3d_nuscenes_v01.sh" > /dev/null 2>&1; }
  has LT3D_NUSCENES_DONE "$R/logs/lt3d_nuscenes_v01.log" && { has LT3D_NNTIME_DONE "$R/logs/lt3d_nntime_v01.log" || bash "$CQ/pod_lt3d_nntime_v01.sh" > /dev/null 2>&1; } ) & PE=$!
wait $PV $PT $PE
has "AV2 FETCH DONE" "$R/logs/fetch_val_v06.log" || stop "fetch val: $(tail -n 2 "$R/logs/fetch_val_v06.log")"
has "AV2 FETCH DONE" "$R/logs/fetch_train_v06.log" || stop "fetch train: $(tail -n 2 "$R/logs/fetch_train_v06.log")"
has LT3D_NNTIME_DONE "$R/logs/lt3d_nntime_v01.log" || stop "LT3D env"
for sp in val train; do f=$(ls "$S/$sp"/MANIFEST_av2_${sp}_lidar_v06_maps.csv 2>/dev/null); [ -n "$f" ] && mv "$f" "$R/owndet/"; done
[ "$(ls "$S/val" | wc -l)" -eq 150 ] || stop "val logs != 150"
[ "$(ls "$S/train" | wc -l)" -eq 700 ] || stop "train logs != 700"
CK=$L/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2
PUB=$CK/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
[ -s "$PUB" ] || stop "shipped config missing"
sha256sum "$PUB" | tee "$R/owndet/public_cfg_sha256.txt"
echo "stage 1 done $(date -u +%FT%TZ)"

# ---- stage 2
source "$L/lt3d38/bin/activate"
I=$S/av2_owndet_infos
PR="python $C/pod_owndet_prep_v01.py --lt3d $L/LT3D --root $S --out $I --out-rel av2_owndet_infos --split $C/AV2_TRAIN_SPLIT_v01.json --procs $NPROC"
for part in train475 held225 val150; do
  has "INFOS DONE $part" "$R/logs/owndet_infos_$part.log" || $PR infos --part $part > "$R/logs/owndet_infos_$part.log" 2>&1
  has "INFOS DONE $part" "$R/logs/owndet_infos_$part.log" || stop "infos $part: $(tail -n 3 "$R/logs/owndet_infos_$part.log")"
  tail -n 2 "$R/logs/owndet_infos_$part.log" | head -n 1
done
has "GTDB DONE" "$R/logs/owndet_gtdb.log" || $PR gtdb > "$R/logs/owndet_gtdb.log" 2>&1
has "GTDB DONE" "$R/logs/owndet_gtdb.log" || stop "GT database: $(tail -n 3 "$R/logs/owndet_gtdb.log")"
cp -p "$I"/*_summary.json "$R/owndet/"; du -sh "$I"; df -h /root | tail -n 1
echo "stage 2 done $(date -u +%FT%TZ)"

# ---- stage 3: pilot
has LT3D_YAPF_DONE "$R/logs/lt3d_yapf_v01.log" || bash "$C/pod_lt3d_yapf_v01.sh" > /dev/null 2>&1
has LT3D_YAPF_DONE "$R/logs/lt3d_yapf_v01.log" || stop "yapf pin"
cd "$L/LT3D"
for B in 4 2 1; do
  PW=$R/owndet/pilot_b$B
  if ! has "PILOT_OK_B$B" "$LOG"; then
    python "$C/pod_owndet_cfg_v01.py" --lt3d "$L/LT3D" --public-cfg "$PUB" --infos-dir "$I" --data-root "$S/" --batch $B --workers $WK \
      --pilot-iters 300 --work-dir "$PW" --out "$R/owndet/cfg_pilot_b$B.py" --dataset-len > "$R/logs/owndet_cfg_pilot_b$B.log" 2>&1 || stop "pilot cfg B=$B: $(tail -n 5 "$R/logs/owndet_cfg_pilot_b$B.log")"
    python tools/train.py "$R/owndet/cfg_pilot_b$B.py" --work-dir "$PW" --seed 0 > "$R/logs/owndet_pilot_b$B.log" 2>&1
    if grep -q "out of memory" "$R/logs/owndet_pilot_b$B.log"; then echo "pilot B=$B: CUDA OOM"; continue; fi
    ls "$PW"/*.log.json > /dev/null 2>&1 || stop "pilot B=$B produced no log: $(tail -n 8 "$R/logs/owndet_pilot_b$B.log")"
    echo "PILOT_OK_B$B"
  fi
  python "$C/pod_owndet_pilot_v01.py" --work-dir "$PW" --cfg-summary "$R/owndet/cfg_pilot_b${B}_summary.json" --h-train 18 --price "${PRICE:-0.89}" --out "$R/owndet/pilot_summary_b$B.json" || stop "pilot summary"
  echo "OD_PILOT_DONE B=$B $(date -u +%FT%TZ)"
  exit 0
done
stop "pilot failed at every batch size"
