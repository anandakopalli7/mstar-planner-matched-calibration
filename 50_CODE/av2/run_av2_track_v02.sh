#!/usr/bin/env bash
# AV2 tracker runs, driver v02 (Claude line, 1 Nov 2026). v01's loop was stopped after it had started its first four jobs
# (equivalence native T1/T3 on 2 logs; T1 LT3D workers 0-1), which kept running. v02 waits for those, then runs the rest
# with at most MAXJ=3 tracker processes (one slot left for the outcome-free analysis steps; never more than 4 processes in
# total), single-threaded BLAS/OpenMP (less contention with the K8 job). Order: T1/T3 LT3D, T1/T3 VoxelNeXt, T2 LT3D,
# T2 VoxelNeXt. Same per-job command as v01. No ground truth is read by any job here.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
A="$(w "$W/50_CODE/av2/av2_track_v01.py")"
T="$W/30_DATA/av2_trk_v01"
export NUMBA_CACHE_DIR="$(w "$T/numba_cache")" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
cd /c/Users/anand
declare -A EXP=([t1]=paper/local/canmot/sc [t2]=paper/local/sample/trainval [t3]=paper/baseline/poly_mot)
PENDING_V01=("$T/equiv/t1_native" "$T/equiv/t3_native" "$T/export/t1_lt3d/worker0" "$T/export/t1_lt3d/worker1")
v01_running() { local n=0; for d in "${PENDING_V01[@]}"; do [ -f "$d/x1_export_record.json" ] || n=$((n+1)); done; echo $n; }
job() {  # tracker detector worker
  local O="$T/export/$1_$2/worker$3"; mkdir -p "$O"
  "$PY" -I -B "$A" --experiment "${EXP[$1]}" --detector "$2" --receipt "$(w "$T/input/$2/receipt.json")" --worker "$3" \
    --fast-convex --out "$(w "$O")" > "$T/logs/track_$1_$2_worker$3.log" 2>&1
}
limit() { while [ $(( $(jobs -rp | wc -l) + $(v01_running) )) -ge "${MAXJ:-3}" ]; do sleep 20; done; }
echo "v02 start $(date +%H:%M:%S)"
for t in t1 t3; do for d in lt3d voxelnext; do for i in 0 1 2 3; do
  [ "$t$d$i" = "t1lt3d0" ] || [ "$t$d$i" = "t1lt3d1" ] && continue
  limit; echo "start $t $d $i $(date +%H:%M:%S)"; job $t $d $i &
done; done; done
for d in lt3d voxelnext; do for i in 0 1 2 3; do limit; echo "start t2 $d $i $(date +%H:%M:%S)"; job t2 $d $i & done; done
wait
while [ "$(v01_running)" -gt 0 ]; do sleep 20; done
echo "tracking done $(date +%H:%M:%S)"
for t in t1 t3; do
  "$PY" -I -B -c "
import gzip, json, sys, os
a = gzip.open(os.path.join(sys.argv[1], sys.argv[2] + '_native', 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
b = gzip.open(os.path.join(sys.argv[1], sys.argv[2] + '_fast', 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
d = sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))
print(json.dumps({'tracker': sys.argv[2], 'records_native': len(a), 'records_fast': len(b), 'records_different': d, 'identical': d == 0 and len(a) > 0}))
" "$(w "$T/equiv")" $t | tee "$T/equiv/EQUIVALENCE_native_vs_fast_$t.json"
done
for f in "$T"/export/*/worker*/x1_export_record.json; do
  "$PY" -I -B -c "import json,sys; r=json.load(open(sys.argv[1])); print(sys.argv[1].split('export')[-1], r['status'], r['failed_criteria'], r['stats'].get('tracks'), r.get('wall_seconds_tracking'))" "$(w "$f")"
done
echo "ALL DONE $(date +%H:%M:%S)"
