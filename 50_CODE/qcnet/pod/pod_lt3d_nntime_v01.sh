#!/usr/bin/env bash
# pod_lt3d_nntime_v01.sh (QCNet arm, 2 Nov 2026): install nntime 0.1.1 (no dependencies) into the LT3D venv.
# LT3D's own setup.sh line 23 runs "pip install nntime" (mmdet3d/models/detectors/base.py imports nntime.time_this);
# pod_lt3d_setup_v03/v04 omitted it, so tools/test.py stopped with "No module named 'nntime'" after pod_lt3d_nuscenes_v01.sh.
# Then the full mmdet3d model and dataset imports are checked.
set -euo pipefail
L=/root/local
R=/root/work
exec > >(tee -a "$R/logs/lt3d_nntime_v01.log") 2>&1
source "$L/lt3d38/bin/activate"
uv pip install -q --no-deps "nntime==0.1.1"
cd "$L/LT3D"
python -c "import nntime, mmdet3d.models, mmdet3d.datasets, mmdet3d.apis; print('mmdet3d models/datasets/apis import ok')"
python -m pip freeze > "$R/logs/lt3d_pip_freeze_v04c.txt"
echo LT3D_NNTIME_DONE
