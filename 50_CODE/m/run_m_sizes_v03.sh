#!/usr/bin/env bash
# Method stage, pre-freeze counts (Claude line, v03, 31 Oct 2026): m_sizes_v03 with outcomes off, for T1, T2 or T3.
# Usage: bash run_m_sizes_v03.sh T1|T2|T3
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
elif [ "$1" = T2 ]; then
  EXP=paper/local/sample/trainval; TAG=sampletv; O="$W/60_RESULTS/m_export_sampletv_v01"
  TRW=(); for i in $(seq 0 11); do TRW+=("$(w "$O/train/worker$i")"); done
  VAW=(); for i in 0 1 2; do VAW+=("$(w "$O/val/worker$i")"); done
  TRH="$(w "$O/horizon_train_v02.jsonl.gz")"; VAH="$(w "$O/horizon_val_v02.jsonl.gz")"
elif [ "$1" = T3 ]; then
  EXP=paper/baseline/poly_mot; TAG=polymot; O="$W/60_RESULTS/m_export_polymot_v01"
  TRW=(); for i in $(seq 0 11); do TRW+=("$(w "$O/train/worker$i")"); done
  VAW=(); for i in 0 1 2; do VAW+=("$(w "$O/val/worker$i")"); done
  TRH="$(w "$O/horizon_train_v03.jsonl.gz")"; VAH="$(w "$O/horizon_val_v03.jsonl.gz")"
else
  echo "unknown tracker $1"; exit 1
fi
cd "$W/50_CODE/m"
"$PY" -B m_sizes_v03.py --tracker "$1" --experiment "$EXP" --train-workers "${TRW[@]}" --val-workers "${VAW[@]}" \
  --train-gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --val-gt "$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")" \
  --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")" --train-horizon "$TRH" --val-horizon "$VAH" \
  --out "$(w "$W/60_RESULTS/m/m_sizes_${TAG}_v03.json")"
echo "M SIZES V03 DONE $1"
