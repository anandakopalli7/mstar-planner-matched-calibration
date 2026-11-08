#!/usr/bin/env bash
# pod_master_v05.sh (QCNet arm, 2 Nov 2026) = pod_master_v04.sh with the QCNet environment from pod_qcnet_setup_v02.sh (v01's uv
# resolver replaced the image's torch); otherwise unchanged. pod_master_v04.sh = 50_CODE/av2/pod/pod_master_v01.sh adapted to the QCNet arm
# (design 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md section 9). Outputs, logs and checkpoints on the pod volume (/workspace/work =
# /root/work); the AV2 data and the two venvs on the container disk L=/root/local (the volume is a network file system, ~35 ms
# per file create; they are rebuilt in < 1 h if the container restarts);
# every step is skipped when its done-marker is in its log, so a container restart resumes.
#   stage 1 (parallel): AV2 val fetch WITH maps (50_CODE/av2/av2_fetch_v04.py, unchanged copy) | LT3D env v04 | QCNet env v01
#   stage 2 (parallel): LT3D 10 Hz run v04 (prep10 test split export ap repro) | QCNet on GT histories (after prep10)
# The tracker stage (AB3DMOT 10 Hz, QCNet on tracker histories) is pod_stage3_v01.sh, started separately.
# Markers: MASTER_STOP <reason> or MASTER_DONE in /root/work/logs/master_v05.log.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work
L=/root/local
mkdir -p "$R/logs" "$R/out_qcnet" "$R/code_qcnet" "$L"
exec > >(tee -a "$R/logs/master_v05.log") 2>&1
echo "master v05 start $(date -u +%FT%TZ)"
D=$L/av2/sensor/val
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "MASTER_STOP $*"; exit 1; }
# worker count from the cgroup memory limit (an OOM kill hit at 61 GB on an earlier pod) and the CPU count
MEM=$(cat /sys/fs/cgroup/memory.max 2>/dev/null || cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || echo max)
[ "$MEM" = max ] && MEM=$(awk '/MemTotal/ {print $2*1024}' /proc/meminfo)
MEMGB=$((MEM / 1024 / 1024 / 1024)); NCPU=$(nproc)
# the CPU quota, not nproc (nproc shows the host's 256 CPUs on RunPod; the cgroup quota is what the pod gets)
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
[ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
NPROC=$(( MEMGB / 5 )); [ $NPROC -gt $((NCPU - 2)) ] && NPROC=$((NCPU - 2)); [ $NPROC -lt 2 ] && NPROC=2
export NPROC
# one BLAS/OpenMP/numba thread per process, so NPROC processes do not oversubscribe the quota
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "cgroup memory ${MEMGB} GB, CPU quota ${NCPU}, worker processes ${NPROC}"
nvidia-smi --query-gpu=name,memory.total --format=csv

# ---- stage 1
( if ! has "AV2 FETCH DONE" "$R/logs/fetch_v04_maps.log"; then
    mkdir -p "$D"
    python -B "$R/code_qcnet/av2_fetch_v04.py" --out "$D" --threads 128 --maps > "$R/logs/fetch_v04_maps.log" 2>&1
  fi ) & PA=$!
( has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup_v04.log" || bash "$R/code_qcnet/pod_lt3d_setup_v04.sh" > "$R/logs/lt3d_setup_v04_nohup.log" 2>&1 ) & PC=$!
( has "QCNET_SETUP_DONE" "$R/logs/qcnet_setup_v02.log" || bash "$R/code_qcnet/pod_qcnet_setup_v02.sh" > "$R/logs/qcnet_setup_v02_nohup.log" 2>&1 ) & PQ=$!
wait $PA $PC $PQ
has "AV2 FETCH DONE" "$R/logs/fetch_v04_maps.log" || stop "fetch: $(tail -n 2 "$R/logs/fetch_v04_maps.log")"
has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup_v04.log" || stop "LT3D setup: $(tail -n 3 "$R/logs/lt3d_setup_v04.log")"
has "QCNET_SETUP_DONE" "$R/logs/qcnet_setup_v02.log" || stop "QCNet setup: $(tail -n 3 "$R/logs/qcnet_setup_v02.log")"
[ -f "$D/MANIFEST_av2_val_lidar_v04_maps.csv" ] && mv "$D/MANIFEST_av2_val_lidar_v04_maps.csv" "$R/out_qcnet/"
[ -s "$R/out_qcnet/MANIFEST_av2_val_lidar_v04_maps.csv" ] || stop "manifest missing"
n=$(ls "$D" | wc -l); [ "$n" -eq 150 ] || stop "expected 150 log folders, found $n"
nm=$(ls "$D"/*/map/log_map_archive_*.json 2>/dev/null | wc -l); [ "$nm" -eq 150 ] || stop "expected 150 log maps, found $nm"
echo "stage 1 done $(date -u +%FT%TZ): 150 logs with maps, both environments built"

# ---- stage 2
( bash "$R/code_qcnet/pod_lt3d_run_v04.sh" all || { echo "LT3D10_FAILED"; exit 1; } ) & PL=$!
( until has STEP10_prep10_DONE "$R/logs/lt3d10_run.log" || has LT3D10_FAILED "$R/logs/master_v05.log"; do sleep 30; done
  source "$L/qcnet310/bin/activate"
  Q="python -I $R/code_qcnet/qcnet_av2_infer_v01.py --qcnet $L/QCNet --ckpt $R/ckpt_qcnet/QCNet_AV2.ckpt --data $D --out $R/out_qcnet"
  if ! has BSCHECK "$R/logs/qcnet_gt_bscheck.log"; then $Q --source gt --batch 4 --bscheck > "$R/logs/qcnet_gt_bscheck.log" 2>&1 || { tail -n 30 "$R/logs/qcnet_gt_bscheck.log"; echo QCNET_GT_FAILED; exit 1; }; fi
  if ! has "INFER DONE" "$R/logs/qcnet_gt_infer.log"; then $Q --source gt --batch 4 > "$R/logs/qcnet_gt_infer.log" 2>&1 || { tail -n 30 "$R/logs/qcnet_gt_infer.log"; echo QCNET_GT_FAILED; exit 1; }; fi
  python -I "$R/code_qcnet/qcnet_av2_infer_v01.py" --merge --source gt --out "$R/out_qcnet" --name qcnet_av2_gt_v01.npz > "$R/logs/qcnet_gt_merge.log" 2>&1 || { tail -n 30 "$R/logs/qcnet_gt_merge.log"; echo QCNET_GT_FAILED; exit 1; }
  echo QCNET_GT_DONE ) & PG=$!
wait $PL; a=$?
wait $PG; b=$?
echo "stage 2 exit codes: lt3d10=$a qcnet_gt=$b"
[ $a -eq 0 ] && [ $b -eq 0 ] || stop "a stage-2 pipeline failed (see lt3d10_run.log / qcnet_gt_*.log)"
echo "master v05 end $(date -u +%FT%TZ)"
echo MASTER_DONE
