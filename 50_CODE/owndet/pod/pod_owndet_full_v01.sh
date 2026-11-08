#!/usr/bin/env bash
# pod_owndet_full_v01.sh (own-detector job, 4 Nov 2026): the whole run of OWN_DETECTOR_DESIGN_v01.md + ADDENDUM_A_v01.md on a fresh pod,
# resumable at every stage (each step is skipped when its DONE line is in its own log; training resumes from the highest checkpoint).
#   1 (parallel): LT3D env (setup v05 + nuscenes + nntime + yapf) | train fetch, 700 logs with maps, to the pod volume | val fetch to disk
#   2: infos train475 / held225 / val150 and the GT database (pod_owndet_prep_v02.py), archived to the volume (restored if present)
#   3: training, 57,838 iterations, B 4, lr 5e-5, CBGS, cyclic over the run, checkpoints every 1,000 iterations on the volume (keep 3)
#   4: inference + export + AP on held225 and val150, deliver dir with SHA256SUMS (pod_owndet_infer_v02.sh)
# Markers in $R/logs/owndet_full_v01.log: OD_TRAIN_DONE, OD_INFER_DONE, OD_FULL_DONE or OD_FULL_STOP <reason>.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work; L=/root/local; C=$R/code_owndet; CQ=$R/code_qcnet
mkdir -p "$R/logs" "$R/owndet" "$L"
LOG=$R/logs/owndet_full_v01.log
exec > >(tee -a "$LOG") 2>&1
echo "owndet full v01 start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "OD_FULL_STOP $*"; exit 1; }
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
NCPU=$(nproc); [ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
if [ -f /sys/fs/cgroup/cpu.max ]; then read -r q2 p2 < /sys/fs/cgroup/cpu.max; [ "$q2" != max ] && NCPU=$((q2 / p2)); fi
MEM=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo max)
[ "$MEM" = max ] && MEM=$(awk '/MemTotal/ {print $2*1024}' /proc/meminfo); MEMGB=$((MEM / 1024 / 1024 / 1024))
NPROC=$((NCPU - 1)); [ $NPROC -gt $((MEMGB / 3)) ] && NPROC=$((MEMGB / 3)); [ $NPROC -lt 2 ] && NPROC=2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "CPU quota ${NCPU}, memory ${MEMGB} GB, prep workers ${NPROC}"; nvidia-smi --query-gpu=name,memory.total --format=csv,noheader; lscpu | grep "Model name"
S=$L/av2/sensor; I=$S/av2_owndet_infos
mkdir -p /home/ubuntu/Workspace/Data "$S" "$R/av2data/train"; ln -sfn "$S" /home/ubuntu/Workspace/Data/Sensor
[ -L "$S/train" ] || ln -s "$R/av2data/train" "$S/train"

# ---- 1
( has LT3D_SETUP_DONE "$R/logs/lt3d_setup_v05.log" || bash "$CQ/pod_lt3d_setup_v05.sh" > "$R/logs/lt3d_setup_v05_nohup.log" 2>&1
  has LT3D_NUSCENES_DONE "$R/logs/lt3d_nuscenes_v01.log" || bash "$CQ/pod_lt3d_nuscenes_v01.sh" > /dev/null 2>&1
  has LT3D_NNTIME_DONE "$R/logs/lt3d_nntime_v01.log" || bash "$CQ/pod_lt3d_nntime_v01.sh" > /dev/null 2>&1
  has LT3D_YAPF_DONE "$R/logs/lt3d_yapf_v01.log" || bash "$C/pod_lt3d_yapf_v01.sh" > /dev/null 2>&1 ) & PE=$!
( has "AV2 FETCH DONE" "$R/logs/fetch_train_v06.log" || python -B "$C/pod_av2_fetch_split_v06.py" --split train --out "$S/train" --threads 128 --maps > "$R/logs/fetch_train_v06.log" 2>&1 ) & PT=$!
( has "AV2 FETCH DONE" "$R/logs/fetch_val_v06.log" || { mkdir -p "$S/val"; python -B "$C/pod_av2_fetch_split_v06.py" --split val --out "$S/val" --threads 64 --maps > "$R/logs/fetch_val_v06.log" 2>&1; } ) & PV=$!
wait $PE $PT $PV
for m in LT3D_SETUP_DONE:lt3d_setup_v05 LT3D_NUSCENES_DONE:lt3d_nuscenes_v01 LT3D_NNTIME_DONE:lt3d_nntime_v01 LT3D_YAPF_DONE:lt3d_yapf_v01; do
  has "${m%%:*}" "$R/logs/${m##*:}.log" || stop "env ${m##*:}"
done
has "AV2 FETCH DONE" "$R/logs/fetch_train_v06.log" || stop "train fetch: $(tail -n 2 "$R/logs/fetch_train_v06.log")"
has "AV2 FETCH DONE" "$R/logs/fetch_val_v06.log" || stop "val fetch: $(tail -n 2 "$R/logs/fetch_val_v06.log")"
for sp in val train; do f=$(ls "$S/$sp"/MANIFEST_av2_${sp}_lidar_v06_maps.csv 2>/dev/null); [ -n "$f" ] && mv "$f" "$R/owndet/"; done
[ "$(ls "$S/val" | wc -l)" -eq 150 ] || stop "val logs != 150"
[ "$(ls "$S/train" | wc -l)" -eq 700 ] || stop "train logs != 700"
echo "stage 1 done $(date -u +%FT%TZ)"

# ---- 2
source "$L/lt3d38/bin/activate"
if [ ! -s "$I/av2_dbinfos_train.pkl" ] && [ -s "$R/owndet/infos_archive_v01.tar" ]; then
  mkdir -p "$S" && tar -xf "$R/owndet/infos_archive_v01.tar" -C "$S" && echo "infos and GT database restored from the volume archive"
fi
PR="python $C/pod_owndet_prep_v02.py --lt3d $L/LT3D --root $S --out $I --out-rel av2_owndet_infos --split $C/AV2_TRAIN_SPLIT_v01.json --procs $NPROC"
for part in train475 held225 val150; do
  [ -s "$I/av2_infos_$part.pkl" ] && continue
  $PR infos --part $part > "$R/logs/owndet_infos_$part.log" 2>&1
  has "INFOS DONE $part" "$R/logs/owndet_infos_$part.log" || stop "infos $part: $(tail -n 3 "$R/logs/owndet_infos_$part.log")"
done
if [ ! -s "$I/av2_dbinfos_train.pkl" ]; then
  $PR gtdb --db-part train475 > "$R/logs/owndet_gtdb.log" 2>&1
  has "GTDB DONE train475" "$R/logs/owndet_gtdb.log" || stop "GT database: $(tail -n 3 "$R/logs/owndet_gtdb.log")"
fi
if [ ! -s "$R/owndet/infos_archive_v01.tar" ]; then
  (cd "$S" && tar -cf "$R/owndet/infos_archive_v01.tar.part" av2_owndet_infos/av2_infos_train475.pkl av2_owndet_infos/av2_infos_held225.pkl av2_owndet_infos/av2_infos_val150.pkl \
     av2_owndet_infos/av2_dbinfos_train.pkl av2_owndet_infos/av2_gt_database) && mv "$R/owndet/infos_archive_v01.tar.part" "$R/owndet/infos_archive_v01.tar" && echo "infos archived to the volume"
fi
cp -p "$I"/*_summary.json "$R/owndet/" 2>/dev/null
echo "stage 2 done $(date -u +%FT%TZ)"

# ---- 3
PUB=$L/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
ITERS=57838; B=4; WK=11
WD=$R/owndet/train_i${ITERS}_b${B}; CFG=$R/owndet/cfg_train_i${ITERS}_b${B}.py
cd "$L/LT3D"
if [ ! -s "$WD/iter_${ITERS}.pth" ]; then
  [ -s "$CFG" ] || python "$C/pod_owndet_cfg_v03.py" --lt3d "$L/LT3D" --public-cfg "$PUB" --infos-dir "$I" --data-root "$S/" --batch $B --workers $WK \
      --max-iters $ITERS --ckpt-interval 1000 --work-dir "$WD" --out "$CFG" --dataset-len > "$R/logs/owndet_cfg_train.log" 2>&1 || stop "train cfg: $(tail -n 5 "$R/logs/owndet_cfg_train.log")"
  sha256sum "$CFG" > "$R/owndet/cfg_train_sha256.txt"
  RES=""; LAST=$(ls "$WD"/iter_*.pth 2>/dev/null | sed 's/.*iter_\([0-9]*\)\.pth/\1/' | sort -n | tail -n 1)
  [ -n "$LAST" ] && RES="--resume-from $WD/iter_${LAST}.pth" && echo "resuming from iteration $LAST"
  echo "training start $(date -u +%FT%TZ) $RES"
  OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 python tools/train.py "$CFG" --work-dir "$WD" --seed 0 --no-validate $RES >> "$R/logs/owndet_train_run.log" 2>&1
fi
[ -s "$WD/iter_${ITERS}.pth" ] || stop "training ended without iter_${ITERS}.pth: $(tail -n 5 "$R/logs/owndet_train_run.log")"
sha256sum "$WD/iter_${ITERS}.pth" > "$R/owndet/own_ckpt_sha256.txt"
echo "OD_TRAIN_DONE $(date -u +%FT%TZ)"

# ---- 4
WD=$WD CFG=$CFG CKPT=$WD/iter_${ITERS}.pth NPROC=$NPROC bash "$C/pod_owndet_infer_v02.sh" || stop "inference (see owndet_infer_v02.log)"
has OD_INFER_DONE "$R/logs/owndet_infer_v02.log" || stop "inference not done"
echo "OD_INFER_DONE $(date -u +%FT%TZ)"
echo "OD_FULL_DONE $(date -u +%FT%TZ)"
