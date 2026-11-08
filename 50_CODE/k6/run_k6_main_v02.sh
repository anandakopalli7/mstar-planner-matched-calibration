#!/usr/bin/env bash
# K6 confirmatory run v02 (Claude line, 1 Nov 2026): for T1 and then T3, the decision mode and the closed loop on the 840
# confirmatory scenes (k6_run_v02, which refuses to start unless the frozen K6 plan v02, its file block and the run inputs
# match, and only with the fixed design), then the K6 analysis and decision (k6_analyse_v02, which checks the freeze record,
# the frozen block, the run records and the design completeness). Unattended; no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
K="$W/50_CODE/k6"; CA="$W/30_DATA/k6"; IT="$W/60_RESULTS/k6_items_v01"; O="$W/60_RESULTS/k6_main_v02"; LG="$W/80_LOGS"
PLAN="$(w "$W/40_PROTOCOL/K6_PREREGISTRATION_v02.md")"
mkdir -p "$O"
cd "$K"
echo "start $(date +%H:%M:%S)"
for T in t1 t3; do
  for MODE in decide loop; do
    "$PY" -B k6_run_v02.py --caches "$(w "$CA/cache_v02_${T}_train")" "$(w "$CA/cache_v02_${T}_val")" --fits "$(w "$IT/k6_fits_${T}_v01.json")" \
      --tag ${T}_$MODE --mode $MODE --out "$(w "$O")" --prereg "$PLAN" --workers 6 > "$LG/K6_main_v02_${T}_$MODE.log" 2>&1 || { echo "RUN ${T}_$MODE FAILED"; exit 1; }
    echo "${T}_$MODE done $(date +%H:%M:%S)"
  done
done
"$PY" -B k6_analyse_v02.py --runs "$(w "$O")" --tags t1 t3 --prereg "$PLAN" \
  --manifests "$(w "$CA/cache_v02_t1_train/MANIFEST.json")" "$(w "$CA/cache_v02_t1_val/MANIFEST.json")" \
  --out "$(w "$O/k6_result_v02.json")" > "$LG/K6_main_v02_analysis.log" 2>&1 || { echo "ANALYSIS FAILED"; exit 1; }
tail -n 40 "$LG/K6_main_v02_analysis.log"
echo "K6 MAIN V02 DONE $(date +%H:%M:%S)"
