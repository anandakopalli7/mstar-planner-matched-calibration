#!/usr/bin/env bash
# Method stage, frozen run (Claude line, v03, 31 Oct 2026): m_run_v03 for T1, T2 and T3 in parallel, then the plan v04
# section 8 decision (m_decide_v03), but only if all three runs exit cleanly (R07b N-m8). Each run refuses to start unless
# the plan's hash block, every input and the numpy/scipy versions match. It runs unattended and has no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
PLAN="$(w "$W/40_PROTOCOL/M_PREREGISTRATION_v04.md")"
GT=(--train-gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --val-gt "$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")" --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")"
    --pip-freeze "$(w "$W/80_LOGS/pip_freeze_canmot310.txt")" --prereg "$PLAN")
cd "$W/50_CODE/m"
run() {  # tag tracker experiment train_base val_base train_horizon val_horizon
  local TAG=$1 T=$2 EXP=$3 TRB=$4 VAB=$5 TRH=$6 VAH=$7
  local TW=() VW=()
  for i in $(seq 0 11); do TW+=("$(w "$TRB/worker$i")"); done
  for i in 0 1 2; do VW+=("$(w "$VAB/worker$i")"); done
  "$PY" -B m_run_v03.py --tracker $T --experiment $EXP "${GT[@]}" --train-workers "${TW[@]}" --val-workers "${VW[@]}" \
    --train-horizon "$(w "$TRH")" --val-horizon "$(w "$VAH")" --sizes "$(w "$W/60_RESULTS/m/m_sizes_${TAG}_v03.json")" \
    --out "$(w "$W/60_RESULTS/m/m_result_${TAG}_v03.json")" > "$W/80_LOGS/M7_run_v03_$T.log" 2>&1
}
echo "start $(date +%H:%M:%S)"
O2="$W/60_RESULTS/m_export_sampletv_v01"; O3="$W/60_RESULTS/m_export_polymot_v01"
run canmot_sc T1 paper/local/canmot/sc "$W/60_RESULTS/x2_export_train700_fast_v02" "$W/60_RESULTS/x1_export_val150_v02" \
    "$W/60_RESULTS/x2/x2_horizon_v01.jsonl.gz" "$W/60_RESULTS/x1/x1_horizon_v01.jsonl.gz" & P1=$!
run sampletv T2 paper/local/sample/trainval "$O2/train" "$O2/val" "$O2/horizon_train_v02.jsonl.gz" "$O2/horizon_val_v02.jsonl.gz" & P2=$!
run polymot T3 paper/baseline/poly_mot "$O3/train" "$O3/val" "$O3/horizon_train_v03.jsonl.gz" "$O3/horizon_val_v03.jsonl.gz" & P3=$!
fail=0
for p in $P1 $P2 $P3; do wait $p || fail=1; done
if [ $fail = 1 ]; then echo "A RUN FAILED: no decision written; see 80_LOGS/M7_run_v03_T*.log"; exit 1; fi
"$PY" -B m_decide_v03.py --prereg "$PLAN" --t1 "$(w "$W/60_RESULTS/m/m_result_canmot_sc_v03.json")" \
  --t2 "$(w "$W/60_RESULTS/m/m_result_sampletv_v03.json")" --t3 "$(w "$W/60_RESULTS/m/m_result_polymot_v03.json")" \
  --out "$(w "$W/60_RESULTS/m/m_decision_v03.json")"
echo "M MAIN V03 DONE $(date +%H:%M:%S)"
