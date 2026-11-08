#!/usr/bin/env bash
# K7 preparation v01 (Claude line, 1 Nov 2026): the planner-matched calibration items of both trackers on all 850 trainval
# scenes (k7_items_v01), then the cross-fitted K7 fits on the K6 log folds (k7_fit_v01). No confirmatory output.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
K="$W/50_CODE/k7"; CA="$W/30_DATA/k6"; D="$W/30_DATA/k7"; FT="$W/60_RESULTS/k7_fits_v01"; LG="$W/80_LOGS"
mkdir -p "$D" "$FT"
cd "$K"
for T in t1 t3; do
  "$PY" -B k7_items_v01.py --caches "$(w "$CA/cache_v02_${T}_train")" "$(w "$CA/cache_v02_${T}_val")" --out "$(w "$D/k7_items_${T}_v01.npz")" \
    --workers 6 > "$LG/K7_items_${T}_v01.log" 2>&1 || { echo "ITEMS $T FAILED"; exit 1; }
  "$PY" -B k7_fit_v01.py --items "$(w "$D/k7_items_${T}_v01.npz")" --k6fits "$(w "$W/60_RESULTS/k6_items_v01/k6_fits_${T}_v01.json")" \
    --out "$(w "$FT/k7_fits_${T}_v01.json")" > "$LG/K7_fit_${T}_v01.log" 2>&1 || { echo "FIT $T FAILED"; exit 1; }
done
echo "K7 PREP V01 DONE"
