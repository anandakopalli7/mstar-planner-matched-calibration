#!/usr/bin/env bash
# pod_openpcdet_resume_v04.sh: wait for LT3D's export (it holds ~8 GB; the container limit is 61 GB), then OpenPCDet
# test + export with pod_run_v04.sh (batch 2, 2 loader workers). Prep is already done.
set -uo pipefail
R=/root/work
exec > >(tee -a "$R/logs/resume.log") 2>&1
echo "=== resume v04 start $(date -u +%FT%TZ)"
last() { tac "$2" 2>/dev/null | sed "/$1/q" | tac; }
until last "=== lt3d stage2 v01" "$R/logs/lt3d_run.log" | grep -q -E "STEP_lt3d_export_DONE|LT3D_FAILED"; do sleep 20; done
echo "LT3D export finished or failed: memory free for OpenPCDet $(date -u +%FT%TZ)"
for s in test export; do
  grep -q "STEP_${s}_DONE" "$R/logs/run.log" && continue
  bash "$R/code/pod_run_v04.sh" "$s" || { echo "RESUME_FAILED $s"; exit 1; }
done
echo RESUME_DONE
