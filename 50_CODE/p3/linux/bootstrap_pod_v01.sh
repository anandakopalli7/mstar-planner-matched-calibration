#!/usr/bin/env bash
# Pod setup (Claude line, v01, 31 Oct 2026): pinned CANMOT and ScenarioNet, two Python 3.10 environments, as on the laptop.
set -e
cd /workspace
apt-get update -qq && apt-get install -y -qq git > /dev/null
python3 -m pip install -q uv
export UV_CACHE_DIR=/workspace/uv_cache
git clone -q https://github.com/rst-tu-dortmund/CANMOT.git CANMOT
(cd CANMOT && git checkout -q 515d0792a4a2dddf4f3f26c2fa26c54bb1c14167 && git submodule update --init -q)
git -C CANMOT/dependencies_repos/nuscenes-devkit rev-parse HEAD
git clone -q https://github.com/metadriverse/scenarionet.git ScenarioNet
(cd ScenarioNet && git checkout -q d4acdb5f5a844744fc85cb2dc3880d7d4a6eb170)
uv python install 3.10 > /dev/null
uv venv -q --python 3.10 /workspace/canmot310
uv pip install -q --python /workspace/canmot310/bin/python -r CANMOT/requirements-lock.txt
uv pip install -q --python /workspace/canmot310/bin/python --no-deps -e CANMOT
uv venv -q --python 3.10 /workspace/sim310
uv pip install -q --python /workspace/sim310/bin/python "metadrive-simulator==0.4.3" "numpy==1.26.4" "setuptools<70" "geopandas<1.0" "nuscenes-devkit>=1.1.10" -e ScenarioNet
/workspace/sim310/bin/python -c "from metadrive.pull_asset import pull_asset; pull_asset(update=False)"
mkdir -p CANMOT/config/environment_cfg /workspace/data /workspace/logs /workspace/cache
cat > CANMOT/config/environment_cfg/my_machine.yaml <<EOF
dataset_base_path: /workspace/data
detector_base_path: /workspace/data
logging_base_path: /workspace/logs
n_processes: 0
cache_path: /workspace/cache
EOF
uv pip freeze --python /workspace/canmot310/bin/python > /workspace/pip_freeze_canmot310_linux.txt
uv pip freeze --python /workspace/sim310/bin/python > /workspace/pip_freeze_sim310_linux.txt
nproc; free -g | head -2; lscpu | grep -E "Model name|^CPU\(s\)|Thread|Core" ; python3 --version
echo BOOTSTRAP_DONE
