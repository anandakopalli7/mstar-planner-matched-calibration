#!/usr/bin/env bash
# Method stage, pre-freeze counts (Claude line, v01, 31 Oct 2026): m_sizes_v01 with outcomes off, for one tracker setting.
# Usage: bash run_m_sizes_v01.sh T1|T2
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
mkdir -p "$W/60_RESULTS/m"
if [ "$1" = T1 ]; then
  EXP=paper/local/canmot/sc; TAG=canmot_sc
  TRW=(); for i in $(seq 0 11); do TRW+=("$(w "$W/60_RESULTS/x2_export_train700_fast_v02/worker$i")"); done
  VAW=(); for i in 0 1 2; do VAW+=("$(w "$W/60_RESULTS/x1_export_val150_v02/worker$i")"); done
  TRH="$(w "$W/60_RESULTS/x2/x2_horizon_v01.jsonl.gz")"; VAH="$(w "$W/60_RESULTS/x1/x1_horizon_v01.jsonl.gz")"
else
  EXP=paper/local/sample/trainval; TAG=sampletv; O="$W/60_RESULTS/m_export_sampletv_v01"
  TRW=(); for i in $(seq 0 11); do TRW+=("$(w "$O/train/worker$i")"); done
  VAW=(); for i in 0 1 2; do VAW+=("$(w "$O/val/worker$i")"); done
  TRH="$(w "$O/horizon_train_v02.jsonl.gz")"; VAH="$(w "$O/horizon_val_v02.jsonl.gz")"
fi
cd "$W/50_CODE/m"
"$PY" -B m_sizes_v01.py --tracker "$1" --experiment "$EXP" --train-workers "${TRW[@]}" --val-workers "${VAW[@]}" \
  --train-gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --val-gt "$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")" \
  --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")" --train-horizon "$TRH" --val-horizon "$VAH" \
  --out "$(w "$W/60_RESULTS/m/m_sizes_${TAG}_v01.json")"
echo "M SIZES DONE $1"
