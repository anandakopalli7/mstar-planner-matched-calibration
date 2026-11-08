#!/usr/bin/env bash
# X2 replication data on nuScenes train (Claude line, v01, 30 Oct 2026): equivalence check of the streaming splitter on val,
# streaming split of train into 12 subsets, ground-truth prep for train, then the CANMOT export with 3 concurrent workers.
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
SP="$W/50_CODE/env/sim310/Scripts/python.exe"
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; D="$W/30_DATA"; M="$(w "$D/nuscenes/v1.0-trainval")"
# 1. streaming splitter equivalence on val (one subset = the whole split, re-serialised)
"$SP" -B "$(w "$X/x1_split_detections_stream_v03.py")" --det "$(w "$D/detectors/centerpoint_flip/infos_val_10sweeps_withvelo_filter_True.json")" --meta "$M" --split val --n-subsets 1 --out "$(w "$D/det_stream_equiv_val")"
"$SP" -B -c "
import json,sys
a=json.load(open(sys.argv[1]))['results']; b=json.load(open(sys.argv[2]))['results']
print('STREAM_EQUIV', list(a.keys())==list(b.keys()) and a==b, len(a), len(b))
assert list(a.keys())==list(b.keys()) and a==b
" "$(w "$D/detectors/centerpoint_flip/infos_val_10sweeps_withvelo_filter_True.json")" "$(w "$D/det_stream_equiv_val/dets_subset00.json")"
# 2. train split
"$SP" -B "$(w "$X/x1_split_detections_stream_v03.py")" --det "$(w "$D/detectors/centerpoint_flip/infos_train_10sweeps_withvelo_filter_True.json")" --meta "$M" --split train --n-subsets 12 --out "$(w "$D/det_subsets_train700")"
# 3. ground truth for train
PYTHONPATH="$(w "$W/50_CODE/third_party/CANMOT/dependencies_repos/nuscenes-devkit/python-sdk")" "$PY" -B "$(w "$X/x1_gt_prep_v03.py")" --meta "$M" --out "$(w "$D/x2_gt")" --split train
# 4. export, 3 concurrent workers over 12 subsets
cd "$W/50_CODE/third_party/CANMOT"
R="$(w "$D/det_subsets_train700/split_receipt.json")"
run() { "$PY" -B "$(w "$X/x1_export_v03.py")" --environment my_machine --split train --trainval-meta "$M" --out "$(w "$W/60_RESULTS/x2_export_train700_v01/worker$1")" --split-receipt "$R" --worker "$1" > "$W/80_LOGS/P6_x2_export_train_worker$1.log" 2>&1; }
for start in 0 3 6 9; do
  run $start & run $((start+1)) & run $((start+2)) & wait
  echo "batch from $start done $(date +%H:%M)"
done
echo "X2 TRAIN EXPORT DONE"
