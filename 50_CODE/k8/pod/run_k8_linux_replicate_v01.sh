#!/usr/bin/env bash
# run_k8_linux_replicate_v01.sh: a complete, separate Linux replicate of the K8 exploratory run (run_k8_expl_v02.sh), on a RunPod CPU pod.
# Same code files (hash-checked), same caches and fits, same arguments; only the platform, the worker count and the output folder differ.
# Why: the laptop run (Windows, run of record) is slowed by CPU contention. Shards from Linux are NOT mixed into it: 8 reference scenes
# agreed only to ~1e-12 relative (last-bit rounding; no integer or boolean field differed), and the pre-set merge rule required byte identity.
# This replicate starts the analysis early. Every design decision taken from it is re-checked on the Windows run of record when that ends.
# EXPLORATORY: nuScenes development evidence, not a confirmation.
# Usage (on the pod, from /workspace/W/50_CODE/k8): bash pod/run_k8_linux_replicate_v01.sh <workers>
set -euo pipefail
cd "$(dirname "$0")/.."
NW=${1:-30}
PY=/workspace/k8env/bin/python
OUT=../../70_TESTS/k8_expl_v02_linux
FIT=../../60_RESULTS/k7_fits_v01
mkdir -p "$OUT"
export PYTHONDONTWRITEBYTECODE=1
echo "K8 Linux replicate v01 start $(date '+%F %T %Z')"
sha256sum k8_sim_v02.py k8_run_v02.py k8_items_v02.py k8_analyse_v02.py k8_analyse_v03.py ../k6/k6_sim_v02.py "$FIT"/k7_fits_t1_v01.json "$FIT"/k7_fits_t3_v01.json
for t in t1 t3; do
  C="../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val"
  $PY -B k8_items_v02.py --caches $C --out $OUT/items_k8_v02_expl_${t}.npz --exploratory --workers $NW
  $PY -B k8_run_v02.py --caches $C --fits $FIT/k7_fits_${t}_v01.json --tag ${t}_decide --mode decide --out $OUT --exploratory --workers $NW --resume
  echo "decide ${t} done $(date '+%F %T %Z')"
done
for t in t1 t3; do
  C="../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val"
  $PY -B k8_run_v02.py --caches $C --fits $FIT/k7_fits_${t}_v01.json --tag ${t}_loop --mode loop --out $OUT --exploratory --workers $NW --resume
  echo "loop ${t} done $(date '+%F %T %Z')"
done
A=../../70_TESTS/k8_expl_v02_linux_analysis_v03
mkdir -p "$A"
$PY -B k8_analyse_v03.py --runs $OUT --tags t1 t3 \
  --manifests ../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json \
  --out $A/k8_exploratory_analysis_v03.json --csv-dir $A/csv --exploratory \
  --fits $FIT/k7_fits_t1_v01.json $FIT/k7_fits_t3_v01.json \
  --items $OUT/items_k8_v02_expl_t1.npz $OUT/items_k8_v02_expl_t3.npz
echo "K8 Linux replicate v01 end $(date '+%F %T %Z')"
echo K8_LINUX_REPLICATE_DONE
