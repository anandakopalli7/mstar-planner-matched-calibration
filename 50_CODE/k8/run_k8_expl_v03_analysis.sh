#!/usr/bin/env bash
# run_k8_expl_v03_analysis.sh: the K8 v03 analysis of the v02 exploratory runs (README_K8_v03_ANALYSIS.md). Run after
# run_k8_expl_v02.sh has exited (its own final v02 analysis step is expected to abort on R15b N1; the runs stay intact).
# Usage, from 50_CODE/k8:  bash run_k8_expl_v03_analysis.sh [--resume]
set -euo pipefail
cd "$(dirname "$0")"
PY=../env/canmot310/Scripts/python.exe
OUT=../../70_TESTS/k8_expl_v02_analysis_v03
mkdir -p "$OUT"
echo "K8 v03 analysis start $(date '+%F %T %Z')"
$PY -B k8_analyse_v03.py --runs ../../70_TESTS/k8_expl_v02 --tags t1 t3 \
  --manifests ../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json \
  --out $OUT/k8_exploratory_analysis_v03.json --csv-dir $OUT/csv --exploratory \
  --fits ../../60_RESULTS/k7_fits_v01/k7_fits_t1_v01.json ../../60_RESULTS/k7_fits_v01/k7_fits_t3_v01.json \
  --items ../../70_TESTS/k8_expl_v02/items_k8_v02_expl_t1.npz ../../70_TESTS/k8_expl_v02/items_k8_v02_expl_t3.npz ${1:-}
echo "K8 v03 analysis end $(date '+%F %T %Z')"
echo K8_V03_ANALYSIS_DONE
