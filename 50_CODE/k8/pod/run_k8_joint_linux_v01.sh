#!/usr/bin/env bash
# run_k8_joint_linux_v01.sh: the M*J full development run (run_k8_joint_v01.sh "full", unchanged in substance) on a Linux RunPod CPU pod,
# run by the lead under the researcher's direct spend approval. The helper's own laptop chain (Windows) stays armed and writes elsewhere.
# Differences from run_k8_joint_v01.sh full: the pod's python; 30 workers; separate output folders (…_linux) so nothing collides with the
# laptop chain; the cross-check compares against the K8 Linux replicate (same platform), where exact equality is expected.
# Inputs are the same files: K7 fits, the Windows K8 items (read only), the development items, the K7 items.
# EXPLORATORY: nuScenes development evidence, not a confirmation.
# Usage (on the pod, from /workspace/W/50_CODE/k8): bash pod/run_k8_joint_linux_v01.sh [workers]
set -euo pipefail
cd "$(dirname "$0")/.."
NW=${1:-30}
PY=/workspace/k8env/bin/python
export PYTHONDONTWRITEBYTECODE=1
ARMS="B0 B1 B3 B4 B6 B9 Mstar MstarJ MstarJx"
MAN="../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json"
DEVI=../../70_TESTS/k8_scratch/v02/dev_v02
FIT=../../60_RESULTS/k8_joint_fits_v01_linux
OUT=../../70_TESTS/k8_joint_v01_linux/full
mkdir -p "$FIT" "$OUT"
echo "K8 joint Linux v01 start $(date '+%F %T %Z')"
sha256sum k8_joint_fit_v01.py k8_sim_v04.py k8_run_v04.py k8_analyse_v04.py k8_sim_v02.py k8_run_v02.py k8_analyse_v03.py tests/k8_joint_crosscheck_v01.py
for t in t1 t3; do
  $PY -B k8_joint_fit_v01.py --fits ../../60_RESULTS/k7_fits_v01/k7_fits_${t}_v01.json \
    --items ../../70_TESTS/k8_expl_v02/items_k8_v02_expl_${t}.npz $DEVI/items_k8_v02_dev_${t}.npz \
    --k7-items ../../30_DATA/k7/k7_items_${t}_v01.npz --out $FIT/k8_joint_fits_${t}_v01.json
  echo "fit ${t} done $(date '+%F %T %Z')"
done
for t in t1 t3; do
  $PY -B k8_run_v04.py --caches ../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val \
    --fits $FIT/k8_joint_fits_${t}_v01.json --tag ${t}_decide --mode decide --out $OUT/runs --exploratory --joint \
    --arms $ARMS --workers $NW --resume
  echo "joint decide ${t} done $(date '+%F %T %Z')"
done
$PY -B k8_analyse_v04.py --runs $OUT/runs --tags t1 t3 --manifests $MAN --out $OUT/k8_joint_analysis_v04.json --csv-dir $OUT/csv \
  --joint-exploratory --modes decide --fits $FIT/k8_joint_fits_t1_v01.json $FIT/k8_joint_fits_t3_v01.json
echo "analysis done $(date '+%F %T %Z')"
$PY -B tests/k8_joint_crosscheck_v01.py --joint-runs $OUT/runs --v02-runs ../../70_TESTS/k8_expl_v02_linux --tags t1 t3 \
  --out $OUT/k8_joint_crosscheck_vs_linux_replicate_v01.json
echo "K8 joint Linux v01 end $(date '+%F %T %Z')"
echo K8_JOINT_LINUX_DONE
