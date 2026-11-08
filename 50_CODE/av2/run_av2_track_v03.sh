#!/usr/bin/env bash
# AV2 tracker runs, driver v03 (Claude line, 2 Nov 2026). Driver v02 was stopped on purpose after it had dispatched T1 and T3
# on both detectors and T2 LT3D workers 0-1 (those kept running). v03 runs T2 LT3D workers 2-3 only: T2 on VoxelNeXt is
# dropped for time (T2 is the optional Q-sensitivity arm; it is kept on the primary detector). Then the native-vs-fast
# comparison and the per-worker summary that v02 would have printed. At most 3 tracker processes in total.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
A="$(w "$W/50_CODE/av2/av2_track_v01.py")"
T="$W/30_DATA/av2_trk_v01"
export NUMBA_CACHE_DIR="$(w "$T/numba_cache")" OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
cd /c/Users/anand
PENDING=("$T/export/t3_voxelnext/worker3" "$T/export/t2_lt3d/worker0" "$T/export/t2_lt3d/worker1")
pending() { local n=0; for d in "${PENDING[@]}"; do [ -f "$d/x1_export_record.json" ] || n=$((n+1)); done; echo $n; }
job() {
  local O="$T/export/t2_lt3d/worker$1"; mkdir -p "$O"
  "$PY" -I -B "$A" --experiment paper/local/sample/trainval --detector lt3d --receipt "$(w "$T/input/lt3d/receipt.json")" --worker "$1" \
    --fast-convex --out "$(w "$O")" > "$T/logs/track_t2_lt3d_worker$1.log" 2>&1
}
limit() { while [ $(( $(jobs -rp | wc -l) + $(pending) )) -ge 3 ]; do sleep 20; done; }
echo "v03 start $(date +%H:%M:%S)"
for i in 2 3; do limit; echo "start t2 lt3d $i $(date +%H:%M:%S)"; job $i & done
wait
while [ "$(pending)" -gt 0 ]; do sleep 20; done
echo "tracking done $(date +%H:%M:%S)"
for t in t1 t3; do
  "$PY" -I -B -c "
import gzip, json, sys, os
a = gzip.open(os.path.join(sys.argv[1], sys.argv[2] + '_native', 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
b = gzip.open(os.path.join(sys.argv[1], sys.argv[2] + '_fast', 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
d = sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))
print(json.dumps({'tracker': sys.argv[2], 'records_native': len(a), 'records_fast': len(b), 'records_different': d, 'identical': d == 0 and len(a) > 0}))
" "$(w "$T/equiv")" $t > "$T/equiv/EQUIVALENCE_native_vs_fast_$t.json"
  cat "$T/equiv/EQUIVALENCE_native_vs_fast_$t.json"
done
for f in "$T"/export/*/worker*/x1_export_record.json; do
  "$PY" -I -B -c "import json,sys; r=json.load(open(sys.argv[1])); print(sys.argv[2], r['status'], r['failed_criteria'], r['stats'].get('tracks'), r.get('wall_seconds_tracking'))" "$(w "$f")" "$f"
done
echo "ALL DONE $(date +%H:%M:%S)"; true
