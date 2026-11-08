#!/usr/bin/env bash
# X2 pre-freeze chain (Claude line, v02: lean library, decision-cell FWER, power): waits for the fast train export, checks Q0, then horizon, sizes, FWER, Q4 OC.
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; R="$W/60_RESULTS/x2"; E="$W/60_RESULTS/x2_export_train700_fast_v02"
until grep -q "X2 FAST TRAIN EXPORT DONE" "$W/80_LOGS/P8_x2_fast_train_chain.log" 2>/dev/null; do sleep 30; done
mkdir -p "$R"
WK=""; EX=""
for i in $(seq 0 11); do
  grep -q '"status_X1_gates": "PASS"' "$E/worker$i/x1_export_record.json" || { echo "Q0 FAIL worker $i"; exit 3; }
  WK="$WK $(w "$E/worker$i")"; EX="$EX $(w "$E/worker$i/x1_tracks.jsonl.gz")"
done
echo "Q0 all 12 workers PASS"
cd "$W/50_CODE/third_party/CANMOT"
"$PY" -B "$(w "$X/x1_horizon_prep_v01.py")" --environment my_machine --workers $WK --out "$(w "$R/x2_horizon_v01.jsonl.gz")"
"$PY" -B "$(w "$X/x2_prefreeze_v02.py")" --mode sizes --export $EX --gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")" --horizon "$(w "$R/x2_horizon_v01.jsonl.gz")" --out "$(w "$R/x2_sizes_v02.json")" | tail -c 400
"$PY" -B "$(w "$X/x2_prefreeze_v02.py")" --mode fwer --sizes "$(w "$R/x2_sizes_v02.json")" --out "$(w "$R/x2_fwer_v02.json")" | tail -c 600
"$PY" -B "$(w "$X/x2_prefreeze_v02.py")" --mode oc --sizes "$(w "$R/x2_sizes_v02.json")" --out "$(w "$R/x2_oc_q4_v02.json")" | tail -c 400
"$PY" -B "$(w "$X/x2_prefreeze_v02.py")" --mode power --sizes "$(w "$R/x2_sizes_v02.json")" --out "$(w "$R/x2_power_v02.json")" | tail -c 900
echo "X2 PREFREEZE DONE"
