#!/usr/bin/env bash
# run_k8_joint_v02.sh (= v01 with k8_joint_fit_v02 and the _v02 fits; v01 kept): the joint arm M*J (D16 Choice 2 (b); k8_joint_fit_v02.py, k8_run_v04.py, k8_analyse_v04.py).
#   dev   the 10 development scenes (plumbing only: delta 0.2 in the fit, because 10 scenes cannot certify 0.05), 1 worker
#   full  nuScenes DEVELOPMENT evidence on the 840 non-development scenes, labelled EXPLORATORY: the fits from M*'s own 850 scenes
#         (the K8 v02 items of the 840 scenes, read only, plus the 10 development scenes' items; checked equal to M*'s K7 items),
#         decision mode for T1 and T3 with M*J next to M* and the Form B comparators, then the v04 analysis. 3 workers.
# Usage (from 50_CODE/k8): bash run_k8_joint_v02.sh dev|full
set -euo pipefail
cd "$(dirname "$0")"
MODE=${1:?usage: run_k8_joint_v02.sh dev|full}
PY=../env/canmot310/Scripts/python.exe
ARMS="B0 B1 B3 B4 B6 B9 Mstar MstarJ MstarJx"
MAN="../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json"
DEVI=../../70_TESTS/k8_scratch/v02/dev_v02
echo "K8 joint v02 ($MODE) start $(date '+%F %T %Z')"
sha256sum k8_joint_fit_v02.py k8_sim_v04.py k8_run_v04.py k8_analyse_v04.py k8_sim_v02.py k8_run_v02.py k8_analyse_v03.py
if [ "$MODE" = dev ]; then
  OUT=../../70_TESTS/k8_joint_v01/dev
  mkdir -p "$OUT"
  for t in t1 t3; do
    $PY -B k8_joint_fit_v02.py --fits ../../60_RESULTS/k7_fits_v01/k7_fits_${t}_v01.json --items $DEVI/items_k8_v02_dev_${t}.npz \
      --out $OUT/k8_joint_fits_dev_${t}_v02.json --dev --delta 0.2
    $PY -B k8_run_v04.py --caches ../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val \
      --fits $OUT/k8_joint_fits_dev_${t}_v02.json --tag ${t}_decide --mode decide --out $OUT/runs --dev --arms $ARMS --workers 1
    echo "dev decide ${t} done $(date '+%F %T %Z')"
  done
  $PY -B k8_analyse_v04.py --runs $OUT/runs --tags t1 t3 --manifests $MAN --out $OUT/k8_joint_dev_analysis_v04.json --csv-dir $OUT/csv \
    --allow-dev --modes decide --fits $OUT/k8_joint_fits_dev_t1_v02.json $OUT/k8_joint_fits_dev_t3_v02.json \
    --items $DEVI/items_k8_v02_dev_t1.npz $DEVI/items_k8_v02_dev_t3.npz
elif [ "$MODE" = full ]; then
  FIT=../../60_RESULTS/k8_joint_fits_v01
  OUT=../../70_TESTS/k8_joint_v01/full_v02
  mkdir -p "$FIT" "$OUT"
  for t in t1 t3; do
    if [ ! -f $FIT/k8_joint_fits_${t}_v02.json ]; then
      $PY -B k8_joint_fit_v02.py --fits ../../60_RESULTS/k7_fits_v01/k7_fits_${t}_v01.json \
        --items ../../70_TESTS/k8_expl_v02/items_k8_v02_expl_${t}.npz $DEVI/items_k8_v02_dev_${t}.npz \
        --k7-items ../../30_DATA/k7/k7_items_${t}_v01.npz --out $FIT/k8_joint_fits_${t}_v02.json
    fi
    echo "fit ${t} done $(date '+%F %T %Z')"
  done
  for t in t1 t3; do
    $PY -B k8_run_v04.py --caches ../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val \
      --fits $FIT/k8_joint_fits_${t}_v02.json --tag ${t}_decide --mode decide --out $OUT/runs --exploratory --joint \
      --arms $ARMS --workers 3 --resume
    echo "joint decide ${t} done $(date '+%F %T %Z')"
  done
  $PY -B k8_analyse_v04.py --runs $OUT/runs --tags t1 t3 --manifests $MAN --out $OUT/k8_joint_analysis_v04.json --csv-dir $OUT/csv \
    --joint-exploratory --modes decide --fits $FIT/k8_joint_fits_t1_v02.json $FIT/k8_joint_fits_t3_v02.json ${2:-}
else
  echo "unknown mode $MODE"; exit 2
fi
echo "K8 joint v02 ($MODE) end $(date '+%F %T %Z')"
echo K8_JOINT_V02_DONE
