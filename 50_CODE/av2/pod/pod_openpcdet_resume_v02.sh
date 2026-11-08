#!/usr/bin/env bash
# pod_openpcdet_resume_v02.sh (v01 with kornia 0.6.12: kornia 0.7 breaks the TorchScript in OpenPCDet's argo2 so3 utils): resume the OpenPCDet pipeline after it failed at prep on pod 2 (OpenPCDet's argo2 utils
# import kornia, which no step installed). Installs kornia for torch 2.1, then runs pod_run_v02.sh prep; waits for the
# LT3D inference to finish (one GPU job at a time on a 24 GB card; the master's LT3D branch already treats OpenPCDet as
# failed and will not wait); then runs test and export. Markers in /root/work/logs/resume.log: RESUME_DONE or RESUME_FAILED.
set -uo pipefail
R=/root/work
exec > >(tee -a "$R/logs/resume.log") 2>&1
echo "resume start $(date -u +%FT%TZ)"
has() { grep -q "$1" "$2" 2>/dev/null; }
pip install --no-cache-dir -q "kornia==0.6.12" "numpy<2" || { echo "RESUME_FAILED kornia install"; exit 1; }
python -c "import torch, kornia, pcdet.datasets; print('kornia', kornia.__version__, 'pcdet datasets import ok')" || { echo "RESUME_FAILED import"; exit 1; }
has STEP_prep_DONE "$R/logs/run.log" || bash "$R/code/pod_run_v02.sh" prep || { echo "RESUME_FAILED prep"; exit 1; }
until has STEP_lt3d_test_DONE "$R/logs/lt3d_run.log" || has LT3D_FAILED "$R/logs/master.log" || has MASTER_STOP "$R/logs/master.log"; do sleep 30; done
echo "GPU free for OpenPCDet $(date -u +%FT%TZ)"
for s in test export; do
  has "STEP_${s}_DONE" "$R/logs/run.log" && continue
  bash "$R/code/pod_run_v02.sh" "$s" || { echo "RESUME_FAILED $s"; exit 1; }
done
echo "resume end $(date -u +%FT%TZ)"
echo RESUME_DONE
