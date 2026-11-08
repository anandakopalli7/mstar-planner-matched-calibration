#!/usr/bin/env bash
# pod_stage3_v01.sh (QCNet arm, 2 Nov 2026): the tracker part (design 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md section 8),
# started only after 60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v01.md exists (lead's brief).
#   1. AB3DMOT equivalence: native vs exact-zero IoU shim on the first 3 logs (must be identical)
#   2. AB3DMOT 10 Hz on all 150 logs (shim), CPU worker pool, LT3D venv
#   3. QCNet on tracker histories (QCNet venv), then merge -> qcnet_av2_trk_ab3dmot_v01.npz
# Markers in /root/work/logs/stage3_v01.log: EQUIV_OK, TRACK10_OK, QCNET_TRK_OK, STAGE3_DONE or STAGE3_STOP <reason>.
set -uo pipefail
R=/root/work
L=/root/local
exec > >(tee -a "$R/logs/stage3_v01.log") 2>&1
echo "stage3 v01 start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$R/logs/stage3_v01.log" 2>/dev/null; }
stop() { echo "STAGE3_STOP $*"; exit 1; }
MEM=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || awk '/MemTotal/ {print $2*1024}' /proc/meminfo)
MEMGB=$((MEM / 1024 / 1024 / 1024))
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
NCPU=$(nproc); [ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
NPROC=$(( MEMGB / 5 )); [ $NPROC -gt $((NCPU - 2)) ] && NPROC=$((NCPU - 2)); [ $NPROC -lt 2 ] && NPROC=2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "memory ${MEMGB} GB, CPU quota ${NCPU}, workers ${NPROC}"
O=$R/out_trk10
D=$L/av2/sensor/val
T="python $R/code_qcnet/pod_ab3dmot10_v01.py --lt3d $L/LT3D --per-log $R/out_lt3d10/per_log --data $D --out $O --procs $NPROC"
source "$L/lt3d38/bin/activate"
if ! has EQUIV_OK; then
  $T --equiv 3 > "$R/logs/ab3dmot_equiv_v01.log" 2>&1
  grep -q "EQUIV DONE" "$R/logs/ab3dmot_equiv_v01.log" || stop "equivalence: $(tail -n 3 "$R/logs/ab3dmot_equiv_v01.log")"
  echo EQUIV_OK
fi
if ! has TRACK10_OK; then
  $T --shim > "$R/logs/ab3dmot_run_v01.log" 2>&1
  grep -q "TRACK10 DONE" "$R/logs/ab3dmot_run_v01.log" || stop "tracker: $(tail -n 3 "$R/logs/ab3dmot_run_v01.log")"
  n=$(ls "$O/logs10"/trk10_*.npz | wc -l); [ "$n" -eq 150 ] || stop "expected 150 tracker logs, found $n"
  echo TRACK10_OK
fi
deactivate
source "$L/qcnet310/bin/activate"
if ! has QCNET_TRK_OK; then
  python -I "$R/code_qcnet/qcnet_av2_infer_v01.py" --qcnet "$L/QCNet" --ckpt "$R/ckpt_qcnet/QCNet_AV2.ckpt" --data "$D" --out "$R/out_qcnet" --source trk --trk "$O/logs10" --batch 4 > "$R/logs/qcnet_trk_infer.log" 2>&1
  grep -q "INFER DONE" "$R/logs/qcnet_trk_infer.log" || stop "qcnet trk: $(tail -n 5 "$R/logs/qcnet_trk_infer.log")"
  python -I "$R/code_qcnet/qcnet_av2_infer_v01.py" --merge --source trk --out "$R/out_qcnet" --name qcnet_av2_trk_ab3dmot_v01.npz > "$R/logs/qcnet_trk_merge.log" 2>&1
  grep -q "MERGE DONE" "$R/logs/qcnet_trk_merge.log" || stop "qcnet trk merge: $(tail -n 5 "$R/logs/qcnet_trk_merge.log")"
  echo QCNET_TRK_OK
fi
echo "stage3 v01 end $(date -u +%FT%TZ)"
echo STAGE3_DONE
