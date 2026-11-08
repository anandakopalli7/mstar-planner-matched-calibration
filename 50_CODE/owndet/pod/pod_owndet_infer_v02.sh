#!/usr/bin/env bash
# pod_owndet_infer_v02.sh (own-detector job, 4 Nov 2026) = pod_owndet_infer_v01.sh (never run) for the iteration-based run: the work dir,
# config and checkpoint come from WD, CFG and CKPT (pod_owndet_full_v01.sh); log owndet_infer_v02.log; the deliver dir also holds the
# training configuration and the run's logs. pod_owndet_infer_v01.sh: inference of the own CenterPoint (final epoch, config test pipeline with TTA)
# on the 225 held-out train logs and the 150 val logs, every 5th sweep; SHARDS concurrent tools/test.py processes on contiguous
# shards, merged in order (code_qcnet/pod_lt3d10_shard_v01.py); export + AP per part (pod_owndet_export_v01.py); deliver dir with
# SHA256SUMS. Usage: WD=<dir> CFG=<cfg> CKPT=<pth> bash pod_owndet_infer_v02.sh. Markers in owndet_infer_v02.log: OD_INFER_DONE / OD_INFER_FAILED.
set -uo pipefail
R=/root/work; L=/root/local; C=$R/code_owndet; CQ=$R/code_qcnet
S=$L/av2/sensor; I=$S/av2_owndet_infos
LOG=$R/logs/owndet_infer_v02.log
exec > >(tee -a "$LOG") 2>&1
: "${WD:?}" "${CFG:?}" "${CKPT:?}"
K=${SHARDS:-6}; NP=${NPROC:-12}
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "owndet infer v02 start $(date -u +%FT%TZ) ckpt=$CKPT shards=$K"
has() { grep -q "$1" "$2" 2>/dev/null; }
fail() { echo "OD_INFER_FAILED $*"; exit 1; }
mkdir -p /home/ubuntu/Workspace/Data; ln -sfn "$S" /home/ubuntu/Workspace/Data/Sensor
source "$L/lt3d38/bin/activate"
cd "$L/LT3D"
[ -s "$CKPT" ] || fail "checkpoint missing"
for part in held225 val150; do
  O=$R/owndet/infer/$part; SH=$O/shards; mkdir -p "$SH"
  case $part in held225) DD=$S/train ;; val150) DD=$S/val ;; esac
  if ! has "MERGED $part" "$LOG"; then
    python "$CQ/pod_lt3d10_shard_v01.py" split --infos "$I/av2_infos_$part.pkl" --k $K --out-prefix "$SH/infos" > "$R/logs/owndet_shard_$part.log" 2>&1 || fail "shard split $part"
    pids=()
    for i in $(seq 0 $((K - 1))); do
      [ -s "$SH/pred_shard$i.pkl" ] && continue
      OMP_NUM_THREADS=2 python tools/test.py "$CFG" "$CKPT" --out "$SH/pred_shard$i.pkl" --cfg-options "data.test.ann_file=$SH/infos_shard$i.pkl" "data.test_dataloader.workers_per_gpu=2" > "$R/logs/owndet_test_${part}_shard$i.log" 2>&1 &
      pids+=($!); echo "$part shard $i pid $!"
    done
    for p in "${pids[@]}"; do wait $p; done
    for i in $(seq 0 $((K - 1))); do [ -s "$SH/pred_shard$i.pkl" ] || fail "test $part shard $i: $(tail -n 3 "$R/logs/owndet_test_${part}_shard$i.log")"; done
    python "$CQ/pod_lt3d10_shard_v01.py" merge --k $K --pred-prefix "$SH/pred" --out "$O/predictions_owncp_$part.pkl" --lt3d "$L/LT3D" > "$R/logs/owndet_merge_$part.log" 2>&1 || fail "merge $part"
    echo "MERGED $part $(date -u +%FT%TZ)"
  fi
  if ! has "OWN EXPORT DONE $part" "$R/logs/owndet_export_$part.log"; then
    python "$C/pod_owndet_export_v01.py" --lt3d "$L/LT3D" --pred "$O/predictions_owncp_$part.pkl" --infos "$I/av2_infos_$part.pkl" --part $part \
      --dataset-dir "$DD" --out "$O" --procs $NP > "$R/logs/owndet_export_$part.log" 2>&1
  fi
  has "OWN EXPORT DONE $part" "$R/logs/owndet_export_$part.log" || fail "export $part: $(tail -n 5 "$R/logs/owndet_export_$part.log")"
  tail -n 6 "$R/logs/owndet_export_$part.log"
done
DL=$R/deliver_owndet; mkdir -p "$DL/held225" "$DL/val150" "$DL/env" "$DL/logs"
for part in held225 val150; do cp -p "$R/owndet/infer/$part"/av2${part}_owncp_centerpoint_* "$DL/$part/"; done
cp -p "$R/owndet/"*_summary.json "$R/owndet/"*sha256*.txt "$CFG" "$R/owndet/"MANIFEST_* "$DL/env/" 2>/dev/null
cp -p "$CKPT" "$DL/env/own_centerpoint_$(basename "$CKPT")"
(cd "$C" && sha256sum * > "$DL/env/code_owndet_sha256.txt"); (cd "$CQ" && sha256sum * > "$DL/env/code_qcnet_used_sha256.txt")
cp -p "$R/logs/lt3d_pip_freeze_v04c.txt" "$DL/env/" 2>/dev/null
for f in owndet_full_v01.log owndet_infer_v02.log owndet_cfg_train.log lt3d_setup_v05.log fetch_val_v06.log fetch_train_v06.log owndet_infos_train475.log owndet_infos_held225.log \
         owndet_infos_val150.log owndet_gtdb.log owndet_export_held225.log owndet_export_val150.log; do
  [ -f "$R/logs/$f" ] && grep -v "task/s\|Warning\|warn(" "$R/logs/$f" | tail -n 300 > "$DL/logs/$f"
done
grep -v "Warning\|warn(" "$R/logs/owndet_train_run.log" | grep -v "^\s*$" | tail -n 400 > "$DL/logs/owndet_train_run_tail.log"
ls "$WD"/*.log.json > /dev/null 2>&1 && cp -p "$WD"/*.log.json "$DL/logs/"
cd "$DL" && find . -type f ! -name SHA256SUMS.txt | sort | xargs sha256sum > SHA256SUMS.txt
du -sh "$DL"; wc -l "$DL/SHA256SUMS.txt"
echo "owndet infer v02 end $(date -u +%FT%TZ)"
echo OD_INFER_DONE
