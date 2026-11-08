#!/usr/bin/env bash
# AV2 tracker runs (Claude line, v01, 1 Nov 2026): T1, T3, then T2 on LT3D CenterPoint and VoxelNeXt, 4 whole-log subsets
# each, at most 4 processes at a time (a K8 job shares the laptop). Native-vs-fast hull equivalence on 2 logs for T1 and T3
# (LT3D). No ground truth is read by any job here. Usage: bash run_av2_track_v01.sh
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
A="$(w "$W/50_CODE/av2/av2_track_v01.py")"
T="$W/30_DATA/av2_trk_v01"
export NUMBA_CACHE_DIR="$(w "$T/numba_cache")"
mkdir -p "$T/export" "$T/equiv" "$T/logs"
cd /c/Users/anand
declare -A EXP=([t1]=paper/local/canmot/sc [t2]=paper/local/sample/trainval [t3]=paper/baseline/poly_mot)
job() {  # tracker detector worker
  local O="$T/export/$1_$2/worker$3"; mkdir -p "$O"
  "$PY" -I -B "$A" --experiment "${EXP[$1]}" --detector "$2" --receipt "$(w "$T/input/$2/receipt.json")" --worker "$3" \
    --fast-convex --out "$(w "$O")" > "$T/logs/track_$1_$2_worker$3.log" 2>&1
}
eq() {  # tracker mode(native|fast)
  local F=""; [ "$2" = fast ] && F="--fast-convex"
  local L=$("$PY" -I -B -c "import json,sys;print(' '.join(json.load(open(sys.argv[1]))['subsets'][0]['logs'][:2]))" "$(w "$T/input/lt3d/receipt.json")")
  "$PY" -I -B "$A" --experiment "${EXP[$1]}" --detector lt3d --receipt "$(w "$T/input/lt3d/receipt.json")" --worker 0 $F \
    --out "$(w "$T/equiv/$1_$2")" --logs $L > "$T/logs/equiv_$1_$2.log" 2>&1
}
limit() { while [ "$(jobs -rp | wc -l)" -ge "${MAXJ:-4}" ]; do wait -n; done; }
echo "start $(date +%H:%M:%S)"
for t in t1 t3; do for m in native fast; do limit; eq $t $m & done; done
for t in t1 t3 t2; do for d in lt3d voxelnext; do for i in 0 1 2 3; do limit; job $t $d $i & done; done; done
wait
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
