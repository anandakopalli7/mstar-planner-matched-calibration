#!/usr/bin/env bash
# run_k8_expl_v02.sh: the K8 exploratory run on the 840 nuScenes scenes (D14 v04 §5; README_K8_v02.md "Launch").
# EXPLORATORY: nuScenes development evidence, not a confirmation. Laptop CPU, no spend.
# Usage: bash run_k8_expl_v02.sh [--dry-run]     (from 50_CODE/k8)
set -euo pipefail
cd "$(dirname "$0")"
DRY=${1:-}
PY=../env/canmot310/Scripts/python.exe
OUT=../../70_TESTS/k8_expl_v02
FIT=../../60_RESULTS/k7_fits_v01
mkdir -p "$OUT"
echo "K8 exploratory run v02 start $(date '+%F %T %Z') ${DRY}"
sha256sum k8_sim_v02.py k8_run_v02.py k8_items_v02.py k8_analyse_v02.py ../k6/k6_sim_v02.py "$FIT"/k7_fits_t1_v01.json "$FIT"/k7_fits_t3_v01.json
for t in t1 t3; do
  C="../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val"
  $PY -B k8_items_v02.py --caches $C --out $OUT/items_k8_v02_expl_${t}.npz --exploratory --workers 6 $DRY
  $PY -B k8_run_v02.py --caches $C --fits $FIT/k7_fits_${t}_v01.json --tag ${t}_decide --mode decide --out $OUT --exploratory --workers 6 --resume $DRY
  echo "decide ${t} done $(date '+%F %T %Z')"
done
for t in t1 t3; do
  C="../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val"
  $PY -B k8_run_v02.py --caches $C --fits $FIT/k7_fits_${t}_v01.json --tag ${t}_loop --mode loop --out $OUT --exploratory --workers 6 --resume $DRY
  echo "loop ${t} done $(date '+%F %T %Z')"
done
if [ -z "$DRY" ]; then
  $PY -B k8_analyse_v02.py --runs $OUT --tags t1 t3 \
    --manifests ../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json \
    --out $OUT/k8_exploratory_analysis_v02.json --csv-dir $OUT/csv --exploratory \
    --fits $FIT/k7_fits_t1_v01.json $FIT/k7_fits_t3_v01.json \
    --items $OUT/items_k8_v02_expl_t1.npz $OUT/items_k8_v02_expl_t3.npz
fi
echo "K8 exploratory run v02 end $(date '+%F %T %Z')"
echo K8_EXPL_DONE
