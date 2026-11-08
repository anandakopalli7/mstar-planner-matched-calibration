#!/usr/bin/env bash
# Fast-convex equivalence on all 150 val scenes (Claude line, v01, 30 Oct 2026): export v04 --fast-convex on the same three
# val subsets, then a record-by-record comparison with the native v02 export (every field except the file-order seq_id).
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; M="$(w "$W/30_DATA/nuscenes/v1.0-trainval")"; R="$(w "$W/30_DATA/det_subsets_val150/split_receipt.json")"
cd "$W/50_CODE/third_party/CANMOT"
for i in 0 1 2; do
  "$PY" -B "$(w "$X/x1_export_v04.py")" --environment my_machine --split val --fast-convex --trainval-meta "$M" --out "$(w "$W/60_RESULTS/x1_export_val150_fast_v04/worker$i")" --split-receipt "$R" --worker $i > "$W/80_LOGS/P7_fast_val_worker$i.log" 2>&1 &
done
wait
"$PY" -B -c "
import gzip, json, sys, os
base, fast = sys.argv[1], sys.argv[2]
tot = diff = 0
first = None
for i in range(3):
    a = gzip.open(os.path.join(base, 'worker%d' % i, 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
    b = gzip.open(os.path.join(fast, 'worker%d' % i, 'x1_tracks.jsonl.gz'), 'rt').read().splitlines()
    if len(a) != len(b):
        print('LENGTH MISMATCH worker', i, len(a), len(b)); diff += abs(len(a) - len(b))
    for la, lb in zip(a, b):
        tot += 1
        if la != lb:
            diff += 1
            if first is None: first = (i, la[:200], lb[:200])
print(json.dumps({'records_compared': tot, 'records_different': diff, 'identical': diff == 0, 'first_difference': first}))
" "$(w "$W/60_RESULTS/x1_export_val150_v02")" "$(w "$W/60_RESULTS/x1_export_val150_fast_v04")" | tee "$W/60_RESULTS/x1_export_val150_fast_v04/EQUIVALENCE_vs_native_v02.json"
