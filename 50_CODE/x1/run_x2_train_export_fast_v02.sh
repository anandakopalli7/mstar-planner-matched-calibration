#!/usr/bin/env bash
# X2 train export in fast-convex mode (Claude line, v02, 30 Oct 2026). Fast mode was accepted after a record-identical
# 150-scene val comparison (60_RESULTS/x1_export_val150_fast_v04/EQUIVALENCE_vs_native_v02.json). 12 subsets, 4 at a time.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; M="$(w "$W/30_DATA/nuscenes/v1.0-trainval")"; R="$(w "$W/30_DATA/det_subsets_train700/split_receipt.json")"
cd "$W/50_CODE/third_party/CANMOT"
run() { "$PY" -B "$(w "$X/x1_export_v04.py")" --environment my_machine --split train --fast-convex --trainval-meta "$M" --out "$(w "$W/60_RESULTS/x2_export_train700_fast_v02/worker$1")" --split-receipt "$R" --worker "$1" > "$W/80_LOGS/P8_x2_fast_train_worker$1.log" 2>&1; }
for start in 0 4 8; do
  run $start & run $((start+1)) & run $((start+2)) & run $((start+3)) & wait
  echo "batch from $start done $(date +%H:%M)"
done
for i in $(seq 0 11); do tail -n 1 "$W/80_LOGS/P8_x2_fast_train_worker$i.log"; done
echo "X2 FAST TRAIN EXPORT DONE"
