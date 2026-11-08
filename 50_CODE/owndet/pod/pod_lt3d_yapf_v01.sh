#!/usr/bin/env bash
# pod_lt3d_yapf_v01.sh (own-detector job, 2 Nov 2026): pin yapf 0.32.0 (no dependencies) in the LT3D venv. mmcv 1.6.1's
# Config.pretty_text calls yapf's FormatCode(..., verify=True); the installed newer yapf dropped `verify`, so Config.dump and
# tools/train.py (which logs cfg.pretty_text) stop with "FormatCode() got an unexpected keyword argument 'verify'".
set -euo pipefail
L=/root/local; R=/root/work
exec > >(tee -a "$R/logs/lt3d_yapf_v01.log") 2>&1
source "$L/lt3d38/bin/activate"
python -m pip show yapf 2>/dev/null | grep -i "^version" || true
uv pip install -q --no-deps "yapf==0.32.0"
cd "$L/LT3D"
python -c "from mmcv import Config; c = Config(dict(a=1)); print(c.pretty_text.strip())"
python -m pip freeze > "$R/logs/lt3d_pip_freeze_owndet.txt"
echo LT3D_YAPF_DONE
