#!/usr/bin/env bash
# pod_openpcdet_resume_v03.sh: OpenPCDet test + export with pod_run_v03.sh (wrapped checkpoint); prep already done (v02).
set -uo pipefail
R=/root/work
exec > >(tee -a "$R/logs/resume.log") 2>&1
echo "=== resume v03 start $(date -u +%FT%TZ)"
for s in test export; do
  grep -q "STEP_${s}_DONE" "$R/logs/run.log" && continue
  bash "$R/code/pod_run_v03.sh" "$s" || { echo "RESUME_FAILED $s"; exit 1; }
done
echo RESUME_DONE
