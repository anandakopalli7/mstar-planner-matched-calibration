#!/usr/bin/env bash
# K6 harness inputs (Claude line, v01, 31 Oct 2026): every 0.5 s planner step (x1_horizon_prep_v04) for T1 (CANMOT sc) and
# T3 (Poly-MOT), train and val, from the same exports the method stage used. Then the identity check against the method
# stage's 1/2/4 s files. No ground truth is read.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; O="$W/60_RESULTS/k6_horizon_v01"; LG="$W/80_LOGS"
cd "$W/50_CODE/third_party/CANMOT"
hp() {  # tag experiment base nworkers
  local WS=(); for i in $(seq 0 $(($4 - 1))); do WS+=("$(w "$3/worker$i")"); done
  "$PY" -B "$(w "$X/x1_horizon_prep_v04.py")" --environment my_machine --experiment $2 --workers "${WS[@]}" --out "$(w "$O/horizon8_$1.jsonl.gz")" > "$LG/K6_horizon_$1.log" 2>&1
}
echo "start $(date +%H:%M:%S)"
hp t1_train paper/local/canmot/sc "$W/60_RESULTS/x2_export_train700_fast_v02" 12 &
hp t1_val paper/local/canmot/sc "$W/60_RESULTS/x1_export_val150_v02" 3 &
hp t3_train paper/baseline/poly_mot "$W/60_RESULTS/m_export_polymot_v01/train" 12 &
hp t3_val paper/baseline/poly_mot "$W/60_RESULTS/m_export_polymot_v01/val" 3 &
wait
grep -h "HORIZON PREP DONE\|Error\|Traceback" "$LG"/K6_horizon_*.log
"$W/50_CODE/env/canmot310/Scripts/python.exe" -B "$(w "$W/50_CODE/k6/check_horizon8_v01.py")" \
  "$(w "$O/horizon8_t1_train.jsonl.gz")" "$(w "$W/60_RESULTS/x2/x2_horizon_v01.jsonl.gz")" \
  "$(w "$O/horizon8_t1_val.jsonl.gz")" "$(w "$W/60_RESULTS/x1/x1_horizon_v01.jsonl.gz")" \
  "$(w "$O/horizon8_t3_train.jsonl.gz")" "$(w "$W/60_RESULTS/m_export_polymot_v01/horizon_train_v03.jsonl.gz")" \
  "$(w "$O/horizon8_t3_val.jsonl.gz")" "$(w "$W/60_RESULTS/m_export_polymot_v01/horizon_val_v03.jsonl.gz")" \
  --out "$(w "$O/HORIZON8_IDENTITY_v01.json")"
echo "K6 HORIZON DONE $(date +%H:%M:%S)"
