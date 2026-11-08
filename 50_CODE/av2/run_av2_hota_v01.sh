#!/usr/bin/env bash
# HOTA with the official av2 evaluator (av2_hota_v02) for T1/T3 x LT3D/VoxelNeXt and T2 x LT3D, one process at a time
# (Claude line, v01, 2 Nov 2026; split out of run_av2_queue3_v01.sh, which was stopped on purpose). Tracking metrics only.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PYA="$W/50_CODE/env/av2eval310/Scripts/python.exe"; S="$W/50_CODE/av2"; LG="$W/30_DATA/av2_cache_stageA_v01/logs"; R="$W/60_RESULTS/av2_trk"
TX="$W/30_DATA/av2_trk_v01/export"; GT="$(w "$W/30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$R/hota"; cd /c/Users/anand
for combo in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext t2_lt3d; do
  "$PYA" -I -B "$(w "$S/av2_hota_v02.py")" --gt "$GT" --exports $(for i in 0 1 2 3; do w "$TX/$combo/worker$i"; done) --label $combo \
    --out "$(w "$R/hota/AV2_HOTA_$combo.json")" > "$LG/hota_$combo.log" 2>&1
  echo "hota $combo: $(grep -v -i warn "$LG/hota_$combo.log" | tail -n 2 | head -n 1 | cut -c1-250) $(date +%H:%M:%S)"
done
echo "HOTA ALL DONE $(date +%H:%M:%S)"; true
