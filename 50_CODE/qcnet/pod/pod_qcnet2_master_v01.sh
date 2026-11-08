#!/usr/bin/env bash
# pod_qcnet2_master_v01.sh (QCNet arm rerun, design addendum A, 2 Nov 2026): resumable driver on pod claude-programmeA-qcnet2.
# Outputs and logs on the pod volume (R=/root/work = /workspace/work); data and venvs on the container disk (L=/root/local).
#   stage 1 (parallel): AV2 val annotations + poses + maps, no lidar (pod_av2_fetch_nolidar_v05.py) | LT3D env (pod_lt3d_setup_v05.sh,
#                       pod_lt3d_nuscenes_v01.sh, pod_lt3d_nntime_v01.sh) | QCNet env + checkpoint (pod_qcnet_setup_v03.sh; SHA-256 must
#                       equal b9f852ec...)
#   stage 2 (parallel): tracker [prep -> replay (released, 10 logs) -> equivalence (matched, 3 logs) -> matched run (150 logs)]
#                       | QCNet on GT histories, re-centred, then frame test v04
#   stage 3: QCNet on matched-AB3DMOT histories, re-centred; stage 4: packing, counts, deliver + SHA256SUMS.
# Uploaded inputs in $R/in: av2val10_lt3d_centerpoint_dets_s010_v01.npz, MANIFEST_av2_val_lidar_v04_maps.csv,
#   trk10_ab3dmot_lt3d_3cls_v01.npz, qcnet_av2_gt_v01.npz, qcnet_av2_trk_ab3dmot_v01.npz, join2hz_t{1,3}_v01_keys.npz.
# Steps are skipped when their DONE line is in their own log (resumable). Markers in $R/logs/qcnet2_master_v01.log:
# Q2_*_OK, Q2_*_FAILED, Q2_MASTER_DONE or Q2_MASTER_STOP <reason>.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work
L=/root/local
C=$R/code_qcnet
mkdir -p "$R/logs" "$R/out2" "$L"
LOG=$R/logs/qcnet2_master_v01.log
exec > >(tee -a "$LOG") 2>&1
echo "qcnet2 master v01 start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "Q2_MASTER_STOP $*"; exit 1; }
MEM=$(cat /sys/fs/cgroup/memory/memory.limit_in_bytes 2>/dev/null || cat /sys/fs/cgroup/memory.max 2>/dev/null || echo max)
[ "$MEM" = max ] && MEM=$(awk '/MemTotal/ {print $2*1024}' /proc/meminfo)
MEMGB=$((MEM / 1024 / 1024 / 1024)); NCPU=$(nproc)
Q=$(cat /sys/fs/cgroup/cpu/cpu.cfs_quota_us 2>/dev/null || echo -1); P=$(cat /sys/fs/cgroup/cpu/cpu.cfs_period_us 2>/dev/null || echo 100000)
[ "$Q" -gt 0 ] 2>/dev/null && NCPU=$((Q / P))
if [ -f /sys/fs/cgroup/cpu.max ]; then read -r q2 p2 < /sys/fs/cgroup/cpu.max; [ "$q2" != max ] && NCPU=$((q2 / p2)); fi
NPROC=$(( MEMGB / 3 )); [ $NPROC -gt $((NCPU - 1)) ] && NPROC=$((NCPU - 1)); [ $NPROC -lt 2 ] && NPROC=2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NPROC
QW=3; TP=$((NPROC - QW)); [ $TP -lt 2 ] && TP=2
echo "memory ${MEMGB} GB, CPU quota ${NCPU}, worker processes ${NPROC} (tracker ${TP} while QCNet builds with ${QW})"
nvidia-smi --query-gpu=name,memory.total --format=csv
D=$L/av2/sensor/val
IN=$R/in
W2=$R/work2
mkdir -p "$W2"

# ---- stage 1
( has "AV2 FETCH DONE" "$R/logs/fetch_nolidar_v05.log" || { mkdir -p "$D"; python -B "$C/pod_av2_fetch_nolidar_v05.py" --out "$D" --threads 64 --maps > "$R/logs/fetch_nolidar_v05.log" 2>&1; } ) & PA=$!
( has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup_v05.log" || bash "$C/pod_lt3d_setup_v05.sh" > "$R/logs/lt3d_setup_v05_nohup.log" 2>&1
  has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup_v05.log" && { has LT3D_NUSCENES_DONE "$R/logs/lt3d_nuscenes_v01.log" || bash "$C/pod_lt3d_nuscenes_v01.sh" > /dev/null 2>&1; }
  has LT3D_NUSCENES_DONE "$R/logs/lt3d_nuscenes_v01.log" && { has LT3D_NNTIME_DONE "$R/logs/lt3d_nntime_v01.log" || bash "$C/pod_lt3d_nntime_v01.sh" > /dev/null 2>&1; } ) & PC=$!
( has "QCNET_SETUP_DONE" "$R/logs/qcnet_setup_v03.log" || bash "$C/pod_qcnet_setup_v03.sh" > "$R/logs/qcnet_setup_v03_nohup.log" 2>&1 ) & PQ=$!
wait $PA $PC $PQ
has "AV2 FETCH DONE" "$R/logs/fetch_nolidar_v05.log" || stop "fetch: $(tail -n 2 "$R/logs/fetch_nolidar_v05.log")"
has LT3D_NNTIME_DONE "$R/logs/lt3d_nntime_v01.log" || stop "LT3D env: $(tail -n 3 "$R/logs/lt3d_setup_v05.log")"
has "QCNET_SETUP_DONE" "$R/logs/qcnet_setup_v03.log" || stop "QCNet setup: $(tail -n 3 "$R/logs/qcnet_setup_v03.log")"
grep -q "^b9f852ec888d6fb966a38e3e307af231145b8e1e69cf7b0b9dddd1ae33120f21 " "$R/logs/qcnet_ckpt_sha256_v03.txt" || stop "QCNet checkpoint hash differs from v01"
[ -f "$D/MANIFEST_av2_val_nolidar_v05.csv" ] && mv "$D/MANIFEST_av2_val_nolidar_v05.csv" "$R/out2/"
n=$(ls "$D" | wc -l); [ "$n" -eq 150 ] || stop "expected 150 log folders, found $n"
nm=$(ls "$D"/*/map/log_map_archive_*.json | wc -l); [ "$nm" -eq 150 ] || stop "expected 150 maps, found $nm"
echo "stage 1 done $(date -u +%FT%TZ)"

# ---- stage 2
T="$L/lt3d38/bin/python $C/pod_ab3dmot10_v02.py --lt3d $L/LT3D --data $D --work $W2 --out $R/out2/trk"
( F=$R/out2/trk
  if ! has "PREP DONE" "$R/logs/ab3dmot_v02_prep.log"; then
    $T prep --dets "$IN/av2val10_lt3d_centerpoint_dets_s010_v01.npz" --manifest "$IN/MANIFEST_av2_val_lidar_v04_maps.csv" > "$R/logs/ab3dmot_v02_prep.log" 2>&1
  fi
  has "PREP DONE" "$R/logs/ab3dmot_v02_prep.log" || { echo "Q2_TRACK_FAILED prep"; exit 1; }
  if ! has "REPLAY DONE" "$R/logs/ab3dmot_v02_replay.log"; then
    $T replay --ref "$IN/trk10_ab3dmot_lt3d_3cls_v01.npz" --logs 10 --procs 10 --shim > "$R/logs/ab3dmot_v02_replay.log" 2>&1
  fi
  has "REPLAY DONE" "$R/logs/ab3dmot_v02_replay.log" || { echo "Q2_TRACK_FAILED replay"; exit 1; }
  grep -q '"all_same_rows_ids": true' "$F/ab3dmot_v02_replay_released.json" || { echo "Q2_TRACK_FAILED replay differs: A1 stops, lead to be told"; exit 1; }
  if ! has "EQUIV DONE\|EQUIV FAILED" "$R/logs/ab3dmot_v02_equiv.log"; then
    $T equiv --mode matched --logs 3 --procs 6 > "$R/logs/ab3dmot_v02_equiv.log" 2>&1
  fi
  SH=""; grep -q '"identical": true' "$F/ab3dmot_v02_equiv_matched.json" 2>/dev/null && SH="--shim"
  echo "tracker association: ${SH:-native}"
  if ! has "TRACK10 DONE" "$R/logs/ab3dmot_v02_matched.log"; then
    $T run --mode matched --procs $TP $SH > "$R/logs/ab3dmot_v02_matched.log" 2>&1
  fi
  has "TRACK10 DONE" "$R/logs/ab3dmot_v02_matched.log" || { echo "Q2_TRACK_FAILED matched"; exit 1; }
  echo Q2_MATCHED_OK ) & PT=$!
( source "$L/qcnet310/bin/activate"
  QI="python -I $C/qcnet_av2_infer_v02.py --qcnet $L/QCNet --ckpt $R/ckpt_qcnet/QCNet_AV2.ckpt --data $D --sweeps $W2/sweeps_by_log.json --out $R/out2/qcnet"
  until [ -s "$W2/sweeps_by_log.json" ] || has Q2_TRACK_FAILED "$LOG"; do sleep 10; done
  [ -s "$W2/sweeps_by_log.json" ] || { echo "Q2_QGT_FAILED no sweep list"; exit 1; }
  has "INFER DONE" "$R/logs/qcnet2_gt_infer.log" || $QI --source gt --batch 4 --workers $QW > "$R/logs/qcnet2_gt_infer.log" 2>&1
  has "INFER DONE" "$R/logs/qcnet2_gt_infer.log" || { echo "Q2_QGT_FAILED infer"; exit 1; }
  has "MERGE DONE" "$R/logs/qcnet2_gt_merge.log" || $QI --merge --source gt --name qcnet_av2_gt_recentred_v02.npz > "$R/logs/qcnet2_gt_merge.log" 2>&1
  has "MERGE DONE" "$R/logs/qcnet2_gt_merge.log" || { echo "Q2_QGT_FAILED merge"; exit 1; }
  has "FRAME TEST DONE" "$R/logs/qcnet_frame_test_v04.log" || python -I "$C/qcnet_frame_test_v04.py" --qcnet "$L/QCNet" --ckpt "$R/ckpt_qcnet/QCNet_AV2.ckpt" --data "$D" --sweeps "$W2/sweeps_by_log.json" --out "$R/out2/qcnet_frame_test_v04.json" > "$R/logs/qcnet_frame_test_v04.log" 2>&1
  has "FRAME TEST DONE" "$R/logs/qcnet_frame_test_v04.log" || echo "Q2_FRAME_FAILED (continuing)"
  echo Q2_QGT_OK ) & PG=$!
wait $PT; a=$?
wait $PG; b=$?
[ $a -eq 0 ] || stop "tracker branch failed (see ab3dmot_v02_*.log)"
[ $b -eq 0 ] || stop "QCNet GT branch failed (see qcnet2_gt_*.log)"

# ---- stage 3
source "$L/qcnet310/bin/activate"
QI="python -I $C/qcnet_av2_infer_v02.py --qcnet $L/QCNet --ckpt $R/ckpt_qcnet/QCNet_AV2.ckpt --data $D --sweeps $W2/sweeps_by_log.json --out $R/out2/qcnet"
has "INFER DONE" "$R/logs/qcnet2_trk_infer.log" || $QI --source trk --trk "$R/out2/trk/matched" --batch 4 --workers $((NPROC > 16 ? 16 : NPROC)) > "$R/logs/qcnet2_trk_infer.log" 2>&1
has "INFER DONE" "$R/logs/qcnet2_trk_infer.log" || stop "QCNet matched infer failed (see qcnet2_trk_infer.log)"
has "MERGE DONE" "$R/logs/qcnet2_trk_merge.log" || $QI --merge --source trk --name qcnet_av2_trk_matched_recentred_v02.npz > "$R/logs/qcnet2_trk_merge.log" 2>&1
has "MERGE DONE" "$R/logs/qcnet2_trk_merge.log" || stop "QCNet matched merge failed"
echo Q2_QTRK_OK

# ---- stage 4
DL=$R/deliver2
mkdir -p "$DL/logs" "$DL/env"
PK="python -I $C/pod_qcnet_pack_v02.py"
[ -s "$DL/trk10_ab3dmot_matched_3cls_v02.npz" ] || $PK trk --trk "$R/out2/trk/matched" --out "$DL/trk10_ab3dmot_matched_3cls_v02.npz" > "$R/logs/pack2_trk.log" 2>&1 || stop "pack trk"
$PK counts --gt-rc "$R/out2/qcnet/qcnet_av2_gt_recentred_v02.npz" --trk-rc "$R/out2/qcnet/qcnet_av2_trk_matched_recentred_v02.npz" \
    --gt-city "$IN/qcnet_av2_gt_v01.npz" --trk-released "$IN/qcnet_av2_trk_ab3dmot_v01.npz" --trk-matched "$DL/trk10_ab3dmot_matched_3cls_v02.npz" \
    --trk-released-tracks "$IN/trk10_ab3dmot_lt3d_3cls_v01.npz" --keys-t1 "$IN/join2hz_t1_v01_keys.npz" --keys-t3 "$IN/join2hz_t3_v01_keys.npz" \
    --out "$DL/qcnet_av2_counts_v02.json" > "$R/logs/pack2_counts.log" 2>&1 || stop "pack counts: $(tail -n 5 "$R/logs/pack2_counts.log")"
cp -p "$R/out2/qcnet/qcnet_av2_gt_recentred_v02.npz" "$R/out2/qcnet/qcnet_av2_gt_recentred_v02_summary.json" \
      "$R/out2/qcnet/qcnet_av2_trk_matched_recentred_v02.npz" "$R/out2/qcnet/qcnet_av2_trk_matched_recentred_v02_summary.json" \
      "$R/out2/trk/ab3dmot_v02_replay_released.json" "$R/out2/trk/ab3dmot_v02_equiv_matched.json" "$R/out2/MANIFEST_av2_val_nolidar_v05.csv" "$DL/" || stop "copy results"
[ -f "$R/out2/qcnet_frame_test_v04.json" ] && cp -p "$R/out2/qcnet_frame_test_v04.json" "$DL/"
cp -p "$R/logs/qcnet_ckpt_verify_v03.json" "$R/logs/qcnet_ckpt_sha256_v03.txt" "$R/logs/qcnet_commit_v03.txt" "$R/logs/qcnet_pip_freeze_v03.txt" \
      "$R/logs/lt3d_commit_v04.txt" "$R/logs/lt3d_pip_freeze_v04c.txt" "$DL/env/" 2>/dev/null
(cd "$C" && sha256sum *.py *.sh > "$DL/env/code_qcnet_sha256_rerun.txt")
(cd "$IN" && sha256sum * > "$DL/env/uploaded_inputs_sha256.txt")
for f in qcnet2_master_v01.log fetch_nolidar_v05.log lt3d_setup_v05.log lt3d_nuscenes_v01.log lt3d_nntime_v01.log qcnet_setup_v03.log ab3dmot_v02_prep.log \
         ab3dmot_v02_replay.log ab3dmot_v02_equiv.log ab3dmot_v02_matched.log qcnet2_gt_infer.log qcnet2_gt_merge.log qcnet_frame_test_v04.log \
         qcnet2_trk_infer.log qcnet2_trk_merge.log pack2_trk.log pack2_counts.log; do
  [ -f "$R/logs/$f" ] && grep -v "Warning\|warn(" "$R/logs/$f" | tail -n 400 > "$DL/logs/$f"
done
cd "$DL" && find . -type f ! -name SHA256SUMS.txt | sort | xargs sha256sum > SHA256SUMS.txt
du -sh "$DL"; wc -l "$DL/SHA256SUMS.txt"
echo "qcnet2 master v01 end $(date -u +%FT%TZ)"
echo Q2_MASTER_DONE
