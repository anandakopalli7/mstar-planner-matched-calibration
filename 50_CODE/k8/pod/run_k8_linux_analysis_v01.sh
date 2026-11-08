#!/usr/bin/env bash
# run_k8_linux_analysis_v01.sh: the v03 analysis of the Linux replicate (run_k8_linux_replicate_v01.sh stopped at its last step because
# k8_analyse_v03 requires --archive-dir for a run directory other than 70_TESTS/k8_expl_v02; README_K8_v03_ANALYSIS.md line 38).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=/workspace/k8env/bin/python; OUT=../../70_TESTS/k8_expl_v02_linux; FIT=../../60_RESULTS/k7_fits_v01; A=../../70_TESTS/k8_expl_v02_linux_analysis_v03
export PYTHONDONTWRITEBYTECODE=1
$PY -B k8_analyse_v03.py --runs $OUT --tags t1 t3 --manifests ../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json --out $A/k8_exploratory_analysis_v03.json --csv-dir $A/csv --exploratory --fits $FIT/k7_fits_t1_v01.json $FIT/k7_fits_t3_v01.json --items $OUT/items_k8_v02_expl_t1.npz $OUT/items_k8_v02_expl_t3.npz --archive-dir ../../70_TESTS/k8_expl_v02_linux_records_archive
echo K8_LINUX_ANALYSIS_DONE
