#!/usr/bin/env bash
# AV2 2 s propagation (Claude line, v01, 2 Nov 2026): av2_horizon_prep_v01 --propagate-only --allow-av2-propagation for T1, T3
# on LT3D and VoxelNeXt (D16 Choice 13: the tracker's own propagation is allowed before the freeze). Tracker output only; no
# ground truth is read. One process at a time (the K8 run shares the laptop).
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
O="$W/30_DATA/av2_cache_stageA_v01"; T="$W/30_DATA/av2_trk_v01/export"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /c/Users/anand
declare -A EXP=([t1]=paper/local/canmot/sc [t3]=paper/baseline/poly_mot)
for combo in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext; do
  tr=${combo%%_*}
  "$PY" -I -B "$(w "$W/50_CODE/av2/av2_horizon_prep_v01.py")" --experiment ${EXP[$tr]} --propagate-only --allow-av2-propagation \
    --workers $(for i in 0 1 2 3; do w "$T/$combo/worker$i"; done) --out "$(w "$O/horizon8_$combo.jsonl.gz")" > "$O/logs/propagate_$combo.log" 2>&1
  echo "$combo $(tail -n 2 "$O/logs/propagate_$combo.log" | tr '\n' ' ') $(date +%H:%M:%S)"
done
echo "PROPAGATION DONE $(date +%H:%M:%S)"; true
