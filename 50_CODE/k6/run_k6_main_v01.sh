#!/usr/bin/env bash
# K6 confirmatory run (Claude line, v01): every episode on the 840 confirmatory scenes for T1 and then T3 (k6_run_v01, which
# refuses to start unless the frozen K6 plan, its file block and the run inputs match), then the K6 analysis and decision
# (k6_analyse_v01, which refuses runs not made under the frozen plan). Unattended; no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
K="$W/50_CODE/k6"; CA="$W/30_DATA/k6"; IT="$W/60_RESULTS/k6_items_v01"; O="$W/60_RESULTS/k6_main_v01"; LG="$W/80_LOGS"
PLAN="$(w "$W/40_PROTOCOL/K6_PREREGISTRATION_v01.md")"
mkdir -p "$O"
cd "$K"
echo "start $(date +%H:%M:%S)"
for T in t1 t3; do
  "$PY" -B k6_run_v01.py --caches "$(w "$CA/cache_${T}_train")" "$(w "$CA/cache_${T}_val")" --fits "$(w "$IT/k6_fits_${T}_v01.json")" \
    --tag $T --out "$(w "$O")" --prereg "$PLAN" --workers 6 > "$LG/K6_main_run_$T.log" 2>&1 || { echo "RUN $T FAILED"; exit 1; }
  echo "$T done $(date +%H:%M:%S)"
done
"$PY" -B k6_analyse_v01.py --runs "$(w "$O")" --tags t1 t3 --prereg "$PLAN" \
  --manifests "$(w "$CA/cache_t1_train/MANIFEST.json")" "$(w "$CA/cache_t1_val/MANIFEST.json")" \
  --out "$(w "$O/k6_result_v01.json")" > "$LG/K6_main_analysis.log" 2>&1 || { echo "ANALYSIS FAILED"; exit 1; }
tail -n 30 "$LG/K6_main_analysis.log"
echo "K6 MAIN DONE $(date +%H:%M:%S)"
