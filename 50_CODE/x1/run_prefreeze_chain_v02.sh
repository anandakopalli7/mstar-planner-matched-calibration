#!/usr/bin/env bash
# X1 pre-freeze chain (Claude line, v02, 30 Oct 2026): horizon predictions, self-tests, sizes, FWER, Q4 OC.
# No ground-truth residual is computed in any of these steps.
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
w() { cygpath -w "$1"; }
X="$W/50_CODE/x1"; R="$W/60_RESULTS/x1"; E="$W/60_RESULTS/x1_export_val150_v02"
mkdir -p "$R"
for i in 0 1 2; do grep -q "status_X1_gates\": \"PASS\"" "$E/worker$i/x1_export_record.json"; done
echo "Q0 workers PASS"
cd "$W/50_CODE/third_party/CANMOT"
"$PY" -B "$(w "$X/x1_horizon_prep_v01.py")" --environment my_machine --workers "$(w "$E/worker0")" "$(w "$E/worker1")" "$(w "$E/worker2")" --out "$(w "$R/x1_horizon_v01.jsonl.gz")"
"$PY" -B "$(w "$X/x1_prefreeze_v02.py")" --mode selftest --out "$(w "$R/x1_selftest_v02.json")" | tail -c 300
"$PY" -B "$(w "$X/x1_prefreeze_v02.py")" --mode sizes --export "$(w "$E/worker0/x1_tracks.jsonl.gz")" "$(w "$E/worker1/x1_tracks.jsonl.gz")" "$(w "$E/worker2/x1_tracks.jsonl.gz")" --gt "$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")" --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")" --horizon "$(w "$R/x1_horizon_v01.jsonl.gz")" --out "$(w "$R/x1_sizes_v02.json")" | tail -c 600
"$PY" -B "$(w "$X/x1_prefreeze_v02.py")" --mode fwer --sizes "$(w "$R/x1_sizes_v02.json")" --out "$(w "$R/x1_fwer_v02.json")" | tail -c 1200
"$PY" -B "$(w "$X/x1_prefreeze_v02.py")" --mode oc --sizes "$(w "$R/x1_sizes_v02.json")" --out "$(w "$R/x1_oc_q4_v02.json")" | tail -c 800
echo "CHAIN DONE"
