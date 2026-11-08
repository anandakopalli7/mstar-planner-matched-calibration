#!/usr/bin/env bash
# pod_lt3d_nuscenes_v01.sh (QCNet arm, 2 Nov 2026): install the public nuscenes-devkit 1.1.11 (no dependencies) into the LT3D venv.
# mmdet3d's datasets package imports nuscenes.utils.data_classes at import time (nuscenes_mono_dataset.py); the detector stage ran
# with the same package for this import only (AV2_DETECTOR_NOTE_v01.md, deviation 3), but pod_lt3d_setup_v03/v04 uninstall the
# devkit and the detector stage added it afterwards, so v04's tools/test.py stopped with "No module named 'nuscenes'".
set -euo pipefail
L=/root/local
R=/root/work
exec > >(tee -a "$R/logs/lt3d_nuscenes_v01.log") 2>&1
source "$L/lt3d38/bin/activate"
uv pip install -q --no-deps "nuscenes-devkit==1.1.11"
cd "$L/LT3D"
python -c "import mmdet3d.datasets as d; print('mmdet3d datasets import ok', d.AV2Dataset.__name__)"
python -m pip freeze > "$R/logs/lt3d_pip_freeze_v04b.txt"
echo LT3D_NUSCENES_DONE
