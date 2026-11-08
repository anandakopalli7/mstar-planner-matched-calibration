#!/usr/bin/env bash
# run_c1_standin_v01.sh: the C1 pipeline end to end on nuScenes development scenes treated as logs (never AV2, never evidence).
#   bash run_c1_standin_v01.sh <N scenes> <workers> <out dir> <decide|both> <standin|smoke>
#   full stand-in (pod):   bash run_c1_standin_v01.sh 375 30 ../../70_TESTS/c1_v01/standin375 both standin
#   local smoke:           bash run_c1_standin_v01.sh 60 2 ../../70_TESTS/c1_v01/smoke60 decide smoke
# Steps: draw N scenes (seed 20261114) and the C1 folds (seed 20261112); fit every arm per fold on the K8 v02 items (read only);
# decision mode (and loop mode with "both") for T1 and T3 with c1_run_v01 --standin; c1_analyse_v01 (--standin or --smoke).
# Run from 50_CODE/c1_av2 (Git Bash on Windows, bash on Linux; PY can be overridden).
set -euo pipefail
cd "$(dirname "$0")"
N=${1:?N}; WK=${2:?workers}; O=${3:?out dir}; MODES=${4:-decide}; AMODE=${5:-standin}
PY=${PY:-../env/canmot310/Scripts/python.exe}
mkdir -p "$O"
echo "C1 stand-in start $(date '+%F %T %Z') N=$N workers=$WK modes=$MODES analysis=$AMODE"
sha256sum c1_folds_v01.py c1_crc_exact_v01.py c1_fit_v01.py c1_run_v01.py c1_analyse_v01.py ../k8/k8_sim_v04.py ../k8/k8_analyse_v04.py ../k8/k8_joint_fit_v02.py
$PY -B tests/c1_standin_prep_v01.py --n "$N" --out-dir "$O"
for t in t1 t3; do
  [ -f "$O/fits_${t}.json" ] || $PY -B c1_fit_v01.py --items ../../70_TESTS/k8_expl_v02/items_k8_v02_expl_${t}.npz --folds "$O/folds.json" \
      --out "$O/fits_${t}.json" --units-subset
  echo "fit ${t} done $(date '+%F %T %Z')"
done
for t in t1 t3; do
  C="../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val"
  $PY -B c1_run_v01.py --caches $C --fits "$O/fits_${t}.json" --c1-folds "$O/folds.json" --standin --tag ${t}_within_lt3d_decide \
      --mode decide --out "$O/runs" --workers "$WK" --resume
  if [ "$MODES" = both ]; then
    $PY -B c1_run_v01.py --caches $C --fits "$O/fits_${t}.json" --c1-folds "$O/folds.json" --standin --tag ${t}_within_lt3d_loop \
        --mode loop --out "$O/runs" --workers "$WK" --resume
  fi
  echo "runs ${t} done $(date '+%F %T %Z')"
done
$PY -B c1_analyse_v01.py --config "$O/config_standin.json" --out "$O/c1_analysis_v01.json" --decision "$O/c1_decision_v01.json" \
    --csv-dir "$O/csv" --$AMODE
echo "C1 stand-in end $(date '+%F %T %Z')"
echo C1_STANDIN_DONE
