#!/usr/bin/env bash
# K7 confirmatory run v01 (Claude line, 1 Nov 2026): for T1 and then T3, the decision mode and the closed loop on the 840
# confirmatory scenes with the frozen K7 fits (k7_run_v01, which refuses to start unless the frozen K7 plan, its file block
# and the run inputs match, and only with the fixed design), then the K7 analysis and decision (k7_analyse_v02, which checks
# the freeze record, the frozen block, the run records and the design completeness). Unattended; no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
K="$W/50_CODE/k7"; CA="$W/30_DATA/k6"; FT="$W/60_RESULTS/k7_fits_v01"; O="$W/60_RESULTS/k7_main_v01"; LG="$W/80_LOGS"
PLAN="$(w "$W/40_PROTOCOL/K7_PREREGISTRATION_v02.md")"
mkdir -p "$O"
cd "$K"
echo "start $(date -u +%H:%M:%S) UTC"
for T in t1 t3; do
  for MODE in decide loop; do
    "$PY" -B k7_run_v01.py --caches "$(w "$CA/cache_v02_${T}_train")" "$(w "$CA/cache_v02_${T}_val")" --fits "$(w "$FT/k7_fits_${T}_v01.json")" \
      --tag ${T}_$MODE --mode $MODE --out "$(w "$O")" --prereg "$PLAN" --workers 6 > "$LG/K7_main_v01_${T}_$MODE.log" 2>&1 || { echo "RUN ${T}_$MODE FAILED"; exit 1; }
    echo "${T}_$MODE done $(date -u +%H:%M:%S) UTC"
  done
done
"$PY" -B k7_analyse_v02.py --runs "$(w "$O")" --tags t1 t3 --prereg "$PLAN" \
  --manifests "$(w "$CA/cache_v02_t1_train/MANIFEST.json")" "$(w "$CA/cache_v02_t1_val/MANIFEST.json")" \
  --out "$(w "$O/k7_result_v01.json")" > "$LG/K7_main_v01_analysis.log" 2>&1 || { echo "ANALYSIS FAILED"; exit 1; }
tail -n 40 "$LG/K7_main_v01_analysis.log"
echo "K7 MAIN V01 DONE $(date -u +%H:%M:%S) UTC"
