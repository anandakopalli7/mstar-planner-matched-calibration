#!/usr/bin/env bash
# Method stage, second covariance model (Claude line, v01, 31 Oct 2026). CANMOT's sample-covariance configuration
# paper/local/sample/trainval on the same CenterPoint detections: export v05 --fast-convex on the 3 val and 12 train
# subsets (at most 5 jobs at a time), a native-vs-fast record comparison on 2 val scenes, then the 1/2/4 s propagation.
# Tracker outputs only: no ground truth is read here.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; M="$(w "$W/30_DATA/nuscenes/v1.0-trainval")"
O="$W/60_RESULTS/m_export_sampletv_v01"; LG="$W/80_LOGS"
EXP=paper/local/sample/trainval
mkdir -p "$O/val" "$O/train" "$O/equiv"
cd "$W/50_CODE/third_party/CANMOT"
job() {  # split worker
  local R="$(w "$W/30_DATA/det_subsets_$([ "$1" = val ] && echo val150 || echo train700)/split_receipt.json")"
  "$PY" -B "$(w "$X/x1_export_v05.py")" --environment my_machine --experiment $EXP --split "$1" --fast-convex --trainval-meta "$M" \
    --out "$(w "$O/$1/worker$2")" --split-receipt "$R" --worker "$2" > "$LG/M1_sampletv_$1_worker$2.log" 2>&1
}
eq() {  # mode (native|fast)
  local F=""; [ "$1" = fast ] && F="--fast-convex"
  "$PY" -B "$(w "$X/x1_export_v05.py")" --environment my_machine --experiment $EXP --split val $F --trainval-meta "$M" \
    --out "$(w "$O/equiv/$1")" --scenes scene-0003 scene-0012 > "$LG/M1_sampletv_equiv_$1.log" 2>&1
}
echo "start $(date +%H:%M:%S)"
pids=()
limit() { while [ "$(jobs -rp | wc -l)" -ge 5 ]; do wait -n; done; }
limit; eq native &
limit; eq fast &
for i in 0 1 2; do limit; job val $i & done
for i in $(seq 0 11); do limit; job train $i & done
wait
echo "exports done $(date +%H:%M:%S)"
"$PY" -B -c "
import gzip, json, sys, os
a = gzip.open(os.path.join(sys.argv[1], 'native', 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
b = gzip.open(os.path.join(sys.argv[1], 'fast', 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
d = sum(x != y for x, y in zip(a, b)) + abs(len(a) - len(b))
print(json.dumps({'records_native': len(a), 'records_fast': len(b), 'records_different': d, 'identical': d == 0 and len(a) > 0}))
" "$(w "$O/equiv")" | tee "$O/equiv/EQUIVALENCE_native_vs_fast.json"
for s in val train; do
  for f in "$O/$s"/worker*/x1_export_record.json; do
    "$PY" -B -c "import json,sys; r=json.load(open(sys.argv[1])); print(sys.argv[1][-40:], r.get('status_X1_gates'), r['criteria'].get('P6'))" "$(w "$f")"
  done
done | tee "$LG/M1_sampletv_q0.log"
if grep -q "None\|FAIL\|False" "$LG/M1_sampletv_q0.log"; then echo "Q0 FAIL"; exit 1; fi
echo "Q0 all 15 workers PASS"
WV=(); for i in 0 1 2; do WV+=("$(w "$O/val/worker$i")"); done
WT=(); for i in $(seq 0 11); do WT+=("$(w "$O/train/worker$i")"); done
"$PY" -B "$(w "$X/x1_horizon_prep_v02.py")" --environment my_machine --experiment $EXP --workers "${WV[@]}" --out "$(w "$O/horizon_val_v02.jsonl.gz")" &
"$PY" -B "$(w "$X/x1_horizon_prep_v02.py")" --environment my_machine --experiment $EXP --workers "${WT[@]}" --out "$(w "$O/horizon_train_v02.jsonl.gz")" &
wait
echo "M1 SAMPLETV CHAIN DONE $(date +%H:%M:%S)"
