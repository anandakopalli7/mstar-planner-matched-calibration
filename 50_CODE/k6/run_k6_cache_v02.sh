#!/usr/bin/env bash
# K6 caches v02 (Claude line, 1 Nov 2026): k6_cache_v02 (in-path and rack flags, review R09 M1/m7); items and fits unchanged from v01.
# Originally: K6 inputs (Claude line, v01, 31 Oct 2026): calibration items at the 8 planner steps (k6_items_v01), the per-scene caches
# (k6_cache_v01) and the cross-fitted arm fits (k6_fit_v01), for T1 (CANMOT sc) and T3 (Poly-MOT). Two jobs at a time
# (memory). Reads ground truth for the open-loop items and pairing only; no closed-loop episode is run here.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
K="$W/50_CODE/k6"; HZ="$W/60_RESULTS/k6_horizon_v01"; LG="$W/80_LOGS"
IT="$W/60_RESULTS/k6_items_v01"; CA="$W/30_DATA/k6"
META="$(w "$W/30_DATA/nuscenes/v1.0-trainval")"
GTTR="$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")"; GTVA="$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")"
EGO="$(w "$CA/k6_ego20hz_v01.json.gz")"
mkdir -p "$IT"
ws() { local o=(); for i in $(seq 0 $(($2 - 1))); do o+=("$(w "$1/worker$i")"); done; echo "${o[@]}"; }
T1TR=$(ws "$W/60_RESULTS/x2_export_train700_fast_v02" 12); T1VA=$(ws "$W/60_RESULTS/x1_export_val150_v02" 3)
T3TR=$(ws "$W/60_RESULTS/m_export_polymot_v01/train" 12); T3VA=$(ws "$W/60_RESULTS/m_export_polymot_v01/val" 3)
E1=paper/local/canmot/sc; E3=paper/baseline/poly_mot
items() { "$PY" -B "$(w "$K/k6_items_v01.py")" --experiment $2 --workers $3 --gt "$4" --meta "$META" --horizon "$(w "$HZ/horizon8_$1.jsonl.gz")" \
          --out "$(w "$IT")" --tag $1 > "$LG/K6_items_$1.log" 2>&1; }
cache() { "$PY" -B "$(w "$K/k6_cache_v02.py")" --experiment $2 --workers $3 --horizon "$(w "$HZ/horizon8_$1.jsonl.gz")" --gt "$4" --meta "$META" \
          --ego "$EGO" --out "$(w "$CA/cache_v02_$1")" > "$LG/K6_cache_v02_$1.log" 2>&1; }
cd "$K"
echo "start $(date +%H:%M:%S)"
cache t1_train $E1 "$T1TR" "$GTTR" & cache t1_val $E1 "$T1VA" "$GTVA" & wait
cache t3_train $E3 "$T3TR" "$GTTR" & cache t3_val $E3 "$T3VA" "$GTVA" & wait
grep -h "K6 CACHE DONE\|Error\|Traceback" "$LG"/K6_cache_v02_*.log
echo "K6 CACHE V02 DONE $(date +%H:%M:%S)"
