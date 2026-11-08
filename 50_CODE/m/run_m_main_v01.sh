#!/usr/bin/env bash
# Method stage, frozen run (Claude line, v01, 31 Oct 2026): m_run_v01 for T1 and T2 in parallel (each refuses to run unless
# the plan's hash block and every input match), then the section 7 decision. Unattended; no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
PLAN="$(w "$W/40_PROTOCOL/M_PREREGISTRATION_v02.md")"
GT=(--train-gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --val-gt "$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")" --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")")
cd "$W/50_CODE/m"
T1W=(); for i in $(seq 0 11); do T1W+=("$(w "$W/60_RESULTS/x2_export_train700_fast_v02/worker$i")"); done
T1V=(); for i in 0 1 2; do T1V+=("$(w "$W/60_RESULTS/x1_export_val150_v02/worker$i")"); done
O="$W/60_RESULTS/m_export_sampletv_v01"
T2W=(); for i in $(seq 0 11); do T2W+=("$(w "$O/train/worker$i")"); done
T2V=(); for i in 0 1 2; do T2V+=("$(w "$O/val/worker$i")"); done
echo "start $(date +%H:%M:%S)"
"$PY" -B m_run_v01.py --prereg "$PLAN" --tracker T1 --experiment paper/local/canmot/sc "${GT[@]}" \
  --train-workers "${T1W[@]}" --val-workers "${T1V[@]}" \
  --train-horizon "$(w "$W/60_RESULTS/x2/x2_horizon_v01.jsonl.gz")" --val-horizon "$(w "$W/60_RESULTS/x1/x1_horizon_v01.jsonl.gz")" \
  --sizes "$(w "$W/60_RESULTS/m/m_sizes_canmot_sc_v01.json")" --out "$(w "$W/60_RESULTS/m/m_result_canmot_sc_v01.json")" \
  > "$W/80_LOGS/M7_run_T1.log" 2>&1 &
"$PY" -B m_run_v01.py --prereg "$PLAN" --tracker T2 --experiment paper/local/sample/trainval "${GT[@]}" \
  --train-workers "${T2W[@]}" --val-workers "${T2V[@]}" \
  --train-horizon "$(w "$O/horizon_train_v02.jsonl.gz")" --val-horizon "$(w "$O/horizon_val_v02.jsonl.gz")" \
  --sizes "$(w "$W/60_RESULTS/m/m_sizes_sampletv_v01.json")" --out "$(w "$W/60_RESULTS/m/m_result_sampletv_v01.json")" \
  > "$W/80_LOGS/M7_run_T2.log" 2>&1 &
wait
"$PY" -B m_decide_v01.py --t1 "$(w "$W/60_RESULTS/m/m_result_canmot_sc_v01.json")" --t2 "$(w "$W/60_RESULTS/m/m_result_sampletv_v01.json")" \
  --out "$(w "$W/60_RESULTS/m/m_decision_v01.json")"
echo "M MAIN DONE $(date +%H:%M:%S)"
