#!/usr/bin/env bash
# run_k8_joint_linux_v03.sh: as v02, but with the helper's v02 fits (k8_joint_fit_v02.py: M*'s refit in K7's own scene order, joint
# lambda decided in exact rational arithmetic; the guard is unchanged). Diagnosis of v01's T3 stop: a floating-point tie at delta inside
# crc_threshold (fold 4, h2s, one L0 cell); see 70_TESTS/k8_joint_v01/diag/k8_joint_t3_refit_diag_v01.json. v02 text follows.
# (v02) the M*J full development run on a Linux CPU pod, with the M*J fits made on Windows.
# Why v02: v01 fitted on the pod. T1 passed, but T3 stopped on k8_joint_fit_v01's own guard ("the refit of M* from these items differs
# from the fits (fold 4, h2s)"). M*'s K7 fits were made on Windows, and a last-bit platform difference at a CRC grid boundary is the
# likely cause (see 70_TESTS/k8_expl_v02_linux/PLATFORM_CHECK_v01.md). The fits are therefore made on the laptop, where M*'s fits were
# made, into 60_RESULTS/k8_joint_fits_v01/ (the folder the helper's own chain uses, and which its script skips if present), and copied
# here unchanged. They are inputs, exactly as the Windows-made K7 fits were inputs to the K8 Linux replicate.
# Steps: decide runs for T1 and T3 (30 workers), the v04 analysis, and the cross-check against the K8 Linux replicate (same platform).
# EXPLORATORY: nuScenes development evidence, not a confirmation.
# Usage (on the pod, from /workspace/W/50_CODE/k8): bash pod/run_k8_joint_linux_v02.sh [workers]
set -euo pipefail
cd "$(dirname "$0")/.."
NW=${1:-30}
PY=/workspace/k8env/bin/python
export PYTHONDONTWRITEBYTECODE=1
ARMS="B0 B1 B3 B4 B6 B9 Mstar MstarJ MstarJx"
MAN="../../30_DATA/k6/cache_v02_t1_train/MANIFEST.json ../../30_DATA/k6/cache_v02_t1_val/MANIFEST.json"
FIT=../../60_RESULTS/k8_joint_fits_v01
OUT=../../70_TESTS/k8_joint_v01_linux/full_v02fits
mkdir -p "$OUT"
echo "K8 joint Linux v03 start $(date '+%F %T %Z')"
sha256sum k8_joint_fit_v01.py k8_joint_fit_v02.py k8_sim_v04.py k8_run_v04.py k8_analyse_v04.py tests/k8_joint_crosscheck_v01.py $FIT/k8_joint_fits_t1_v02.json $FIT/k8_joint_fits_t3_v02.json
for t in t1 t3; do
  $PY -B k8_run_v04.py --caches ../../30_DATA/k6/cache_v02_${t}_train ../../30_DATA/k6/cache_v02_${t}_val \
    --fits $FIT/k8_joint_fits_${t}_v02.json --tag ${t}_decide --mode decide --out $OUT/runs --exploratory --joint \
    --arms $ARMS --workers $NW --resume
  echo "joint decide ${t} done $(date '+%F %T %Z')"
done
$PY -B k8_analyse_v04.py --runs $OUT/runs --tags t1 t3 --manifests $MAN --out $OUT/k8_joint_analysis_v04.json --csv-dir $OUT/csv \
  --joint-exploratory --modes decide --fits $FIT/k8_joint_fits_t1_v02.json $FIT/k8_joint_fits_t3_v02.json
echo "analysis done $(date '+%F %T %Z')"
$PY -B tests/k8_joint_crosscheck_v01.py --joint-runs $OUT/runs --v02-runs ../../70_TESTS/k8_expl_v02_linux --tags t1 t3 \
  --out $OUT/k8_joint_crosscheck_vs_linux_replicate_v01.json
echo "K8 joint Linux v03 end $(date '+%F %T %Z')"
echo K8_JOINT_LINUX_DONE
