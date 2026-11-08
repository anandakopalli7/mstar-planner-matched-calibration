#!/usr/bin/env bash
# run_k8_expl_v02_resume_v01.sh: resumes the K8 exploratory run of record (run_k8_expl_v02.sh) after the laptop's power loss on
# 2 Nov 2026 (between about 07:05 and 08:51 EST). Items, decide t1, decide t3 and loop t1 were complete; loop t3 had 312 of 840 shards.
# 1. archive the run and launch records first, read-only (README_K8_v03_ANALYSIS.md step 1; R15b N2: re-running the runner rewrites
#    that run's launch record);
# 2. the same loop t3 command as run_k8_expl_v02.sh, with --resume (shards are reused only if scene, mode, arms, delays and the sim,
#    runner, fits and cache hashes all match);
# 3. the v03 analysis (run_k8_expl_v03_analysis.sh), instead of the v02 analysis, which aborts by R15b N1.
# Usage (from 50_CODE/k8): bash run_k8_expl_v02_resume_v01.sh
set -euo pipefail
cd "$(dirname "$0")"
PY=../env/canmot310/Scripts/python.exe
OUT=../../70_TESTS/k8_expl_v02
FIT=../../60_RESULTS/k7_fits_v01
echo "K8 resume v01 start $(date '+%F %T %Z')"
bash run_k8_expl_v03_analysis.sh --archive-only
echo "records archived $(date '+%F %T %Z')"
C="../../30_DATA/k6/cache_v02_t3_train ../../30_DATA/k6/cache_v02_t3_val"
$PY -B k8_run_v02.py --caches $C --fits $FIT/k7_fits_t3_v01.json --tag t3_loop --mode loop --out $OUT --exploratory --workers 6 --resume
echo "loop t3 done $(date '+%F %T %Z')"
bash run_k8_expl_v03_analysis.sh
echo "K8 resume v01 end $(date '+%F %T %Z')"
echo K8_RESUME_DONE
