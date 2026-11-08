#!/usr/bin/env bash
# pod_qcnet3_master_v01.sh (QCNet arm, design addendum B, 2 Nov 2026): QCNet, re-centred, on the matched + SF histories, pod
# claude-programmeA-qcnet3. Outputs and logs on the pod volume (R=/root/work = /workspace/work); data and venv on the container disk.
#   stage 1 (parallel): AV2 val annotations + poses + maps, no lidar (pod_av2_fetch_nolidar_v05.py) | QCNet env (pod_qcnet_setup_v03.sh;
#                       checkpoint SHA-256 must equal b9f852ec...)
#   stage 2: wait for the uploads ($R/in3/UPLOAD_DONE), split the tracker file per log, sweep list, qcnet_av2_infer_v03 (source trk),
#            merge, counts (pod_qcnet_pack_v03.py), deliver3 + SHA256SUMS.txt
# Each step is skipped when its DONE line is in its own log. Markers in $R/logs/qcnet3_master_v01.log: Q3_MASTER_DONE / Q3_MASTER_STOP.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work
L=/root/local
C=$R/code_qcnet
IN=$R/in3
mkdir -p "$R/logs" "$R/out3" "$L"
LOG=$R/logs/qcnet3_master_v01.log
exec > >(tee -a "$LOG") 2>&1
echo "qcnet3 master v01 start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "Q3_MASTER_STOP $*"; exit 1; }
MEM=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup/memory.max 2>/dev/null || echo max)
[ "$MEM" = max ] && MEM=$(awk '/MemTotal/ {print $2*1024}' /proc/meminfo)
MEMGB=$((MEM / 1024 / 1024 / 1024)); NCPU=$(nproc)
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
[ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
if [ -f /sys/fs/cgroup/cpu.max ]; then read -r q2 p2 < /sys/fs/cgroup/cpu.max; [ "$q2" != max ] && NCPU=$((q2 / p2)); fi
QW=$(( MEMGB / 3 )); [ $QW -gt $((NCPU - 2)) ] && QW=$((NCPU - 2)); [ $QW -gt 16 ] && QW=16; [ $QW -lt 2 ] && QW=2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "memory ${MEMGB} GB, CPU quota ${NCPU}, QCNet scene workers ${QW}"
nvidia-smi --query-gpu=name,memory.total --format=csv
D=$L/av2/sensor/val

( has "AV2 FETCH DONE" "$R/logs/fetch_nolidar_v05.log" || { mkdir -p "$D"; python -B "$C/pod_av2_fetch_nolidar_v05.py" --out "$D" --threads 64 --maps > "$R/logs/fetch_nolidar_v05.log" 2>&1; } ) & PA=$!
( has "QCNET_SETUP_DONE" "$R/logs/qcnet_setup_v03.log" || bash "$C/pod_qcnet_setup_v03.sh" > "$R/logs/qcnet_setup_v03_nohup.log" 2>&1 ) & PQ=$!
wait $PA $PQ
has "AV2 FETCH DONE" "$R/logs/fetch_nolidar_v05.log" || stop "fetch: $(tail -n 2 "$R/logs/fetch_nolidar_v05.log")"
has "QCNET_SETUP_DONE" "$R/logs/qcnet_setup_v03.log" || stop "QCNet setup: $(tail -n 3 "$R/logs/qcnet_setup_v03.log")"
grep -q "^b9f852ec888d6fb966a38e3e307af231145b8e1e69cf7b0b9dddd1ae33120f21 " "$R/logs/qcnet_ckpt_sha256_v03.txt" || stop "QCNet checkpoint hash differs"
[ -f "$D/MANIFEST_av2_val_nolidar_v05.csv" ] && mv "$D/MANIFEST_av2_val_nolidar_v05.csv" "$R/out3/"
[ "$(ls "$D" | wc -l)" -eq 150 ] || stop "expected 150 log folders"
[ "$(ls "$D"/*/map/log_map_archive_*.json | wc -l)" -eq 150 ] || stop "expected 150 maps"
echo "stage 1 done $(date -u +%FT%TZ)"

until [ -f "$IN/UPLOAD_DONE" ]; do sleep 15; done
(cd "$IN" && sha256sum -c UPLOAD_SHA256SUMS.txt > "$R/logs/upload_check.log" 2>&1) || stop "uploaded inputs fail their checksums"
source "$L/qcnet310/bin/activate"
PK="python -I $C/pod_qcnet_pack_v03.py"
has "SPLIT DONE" "$R/logs/pack3_split.log" || $PK split --trk "$IN/trk10_ab3dmot_matched_sf_3cls_v03.npz" --out "$R/out3/trk_sf" > "$R/logs/pack3_split.log" 2>&1
has "SPLIT DONE" "$R/logs/pack3_split.log" || stop "split"
has "SWEEPS DONE" "$R/logs/pack3_sweeps.log" || $PK sweeps --manifest "$IN/MANIFEST_av2_val_lidar_v04_maps.csv" --out "$R/out3/sweeps_by_log.json" > "$R/logs/pack3_sweeps.log" 2>&1
has "SWEEPS DONE" "$R/logs/pack3_sweeps.log" || stop "sweeps"
QI="python -I $C/qcnet_av2_infer_v03.py --qcnet $L/QCNet --ckpt $R/ckpt_qcnet/QCNet_AV2.ckpt --data $D --sweeps $R/out3/sweeps_by_log.json --out $R/out3/qcnet"
has "INFER DONE" "$R/logs/qcnet3_sf_infer.log" || $QI --source trk --trk "$R/out3/trk_sf" --batch 4 --workers $QW > "$R/logs/qcnet3_sf_infer.log" 2>&1
has "INFER DONE" "$R/logs/qcnet3_sf_infer.log" || stop "QCNet matched+SF infer failed"
has "MERGE DONE" "$R/logs/qcnet3_sf_merge.log" || $QI --merge --source trk --name qcnet_av2_trk_matched_sf_recentred_v03.npz > "$R/logs/qcnet3_sf_merge.log" 2>&1
has "MERGE DONE" "$R/logs/qcnet3_sf_merge.log" || stop "QCNet matched+SF merge failed"
DL=$R/deliver3
mkdir -p "$DL/logs" "$DL/env"
has "COUNTS DONE" "$R/logs/pack3_counts.log" || $PK counts --sf-rc "$R/out3/qcnet/qcnet_av2_trk_matched_sf_recentred_v03.npz" --gt-rc "$IN/qcnet_av2_gt_recentred_v02.npz" \
    --matched-rc "$IN/qcnet_av2_trk_matched_recentred_v02.npz" --trk-sf "$IN/trk10_ab3dmot_matched_sf_3cls_v03.npz" \
    --keys-t1 "$IN/join2hz_t1_v01_keys.npz" --keys-t3 "$IN/join2hz_t3_v01_keys.npz" --out "$DL/qcnet_av2_counts_v03.json" > "$R/logs/pack3_counts.log" 2>&1
has "COUNTS DONE" "$R/logs/pack3_counts.log" || stop "counts: $(tail -n 5 "$R/logs/pack3_counts.log")"
cp -p "$R/out3/qcnet/qcnet_av2_trk_matched_sf_recentred_v03.npz" "$R/out3/qcnet/qcnet_av2_trk_matched_sf_recentred_v03_summary.json" "$R/out3/MANIFEST_av2_val_nolidar_v05.csv" \
      "$IN/trk10_ab3dmot_matched_sf_3cls_v03.npz" "$IN/trk10_ab3dmot_matched_sf_3cls_v03_filter.json" "$DL/" || stop "copy results"
cp -p "$R/logs/qcnet_ckpt_verify_v03.json" "$R/logs/qcnet_ckpt_sha256_v03.txt" "$R/logs/qcnet_commit_v03.txt" "$R/logs/qcnet_pip_freeze_v03.txt" "$DL/env/" 2>/dev/null
(cd "$C" && sha256sum *.py *.sh > "$DL/env/code_qcnet_sha256_v03run.txt")
cp -p "$IN/UPLOAD_SHA256SUMS.txt" "$DL/env/uploaded_inputs_sha256.txt"
for f in qcnet3_master_v01.log fetch_nolidar_v05.log qcnet_setup_v03.log upload_check.log pack3_split.log pack3_sweeps.log qcnet3_sf_infer.log qcnet3_sf_merge.log pack3_counts.log; do
  [ -f "$R/logs/$f" ] && grep -v "Warning\|warn(" "$R/logs/$f" | tail -n 400 > "$DL/logs/$f"
done
cd "$DL" && find . -type f ! -name SHA256SUMS.txt | sort | xargs sha256sum > SHA256SUMS.txt
du -sh "$DL"; wc -l "$DL/SHA256SUMS.txt"
echo "qcnet3 master v01 end $(date -u +%FT%TZ)"
echo Q3_MASTER_DONE
