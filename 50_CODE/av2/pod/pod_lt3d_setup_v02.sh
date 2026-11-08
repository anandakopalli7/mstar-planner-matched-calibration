#!/usr/bin/env bash
# pod_lt3d_setup_v02.sh (v01 + every install inside the venv via uv; v01 resolved `pip` to the system Python): build LT3D (the official AV2 detection baseline; mmdet3d fork) in its own Python 3.8 venv on the pod.
# Its AV2 CenterPoint uses 5 sweeps and regresses velocity (code_size 9), as the nuScenes CenterPoint our trackers consume
# (D15 §3: CenterPoint primary if it loads). Versions follow LT3D's setup.sh: torch 1.10.1+cu111, mmcv-full 1.6.1,
# mmdet 2.25.2, mmsegmentation 0.28.0, spconv-cu111, setuptools 59.5.0. The image's nvcc is 11.8 (same major as 11.1).
# Logs to /root/work/logs/lt3d_setup.log; last line LT3D_SETUP_DONE.
set -euo pipefail
R=/root/work
mkdir -p "$R/logs" "$R/ckpt_lt3d"
exec > >(tee -a "$R/logs/lt3d_setup.log") 2>&1
echo "lt3d setup start $(date -u +%FT%TZ)"
python -m pip install -q uv
cd "$R"
[ -d lt3d38 ] || python -m uv venv lt3d38 --python 3.8
source "$R/lt3d38/bin/activate"
python -V
command -v uv >/dev/null || python -m pip install -q uv
uv pip install -q pip
which python; python -m pip --version
uv pip install -q torch==1.10.1+cu111 torchvision==0.11.2+cu111 --extra-index-url https://download.pytorch.org/whl/cu111 --index-strategy unsafe-best-match
uv pip install -q mmcv-full==1.6.1 -f https://download.openmmlab.com/mmcv/dist/cu111/torch1.10.0/index.html
uv pip install -q mmdet==2.25.2 mmsegmentation==0.28.0 "numpy<1.24" setuptools==59.5.0 wheel ninja
[ -d LT3D ] || git clone -q https://github.com/neeharperi/LT3D.git
cd LT3D
git rev-parse HEAD | tee "$R/logs/lt3d_commit.txt"
python -c "import torch; print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available())"
TORCH_CUDA_ARCH_LIST="8.0;8.6" FORCE_CUDA=1 MAX_JOBS=32 python -m pip install -v --no-build-isolation -e . > "$R/logs/lt3d_build.log" 2>&1 || { tail -60 "$R/logs/lt3d_build.log"; exit 1; }
uv pip install -q -r requirements/optional.txt || echo "optional requirements: some failed (non-fatal)"
uv pip install -q cumm-cu111 spconv-cu111 pyntcloud pyarrow "av2==0.2.1" "numpy<1.24" setuptools==59.5.0 gdown
uv pip uninstall -q nuscenes-devkit || true
uv pip install -q --reinstall numba "numpy<1.24"
python -c "import mmcv, mmdet, mmdet3d, spconv, av2; print('mmcv', mmcv.__version__, 'mmdet', mmdet.__version__, 'mmdet3d', mmdet3d.__version__, 'spconv', spconv.__version__)"
# the released AV2 detectors (one tarball in the LT3D 'Pre-trained Detection Models' Drive folder)
cd "$R/ckpt_lt3d"
[ -s av2_detectors.tar.gz ] || gdown --folder "https://drive.google.com/drive/folders/1BVhYv-kJE_ydbvDDz8AA3pgDdVTSCHIT" -O "$R/ckpt_lt3d" || true
f=$(find "$R/ckpt_lt3d" -name "av2_detectors.tar.gz" | head -1)
ls -la "$f"; sha256sum "$f" | tee "$R/logs/lt3d_tar_sha256.txt"
tar -tzf "$f" | head -50 | tee "$R/logs/lt3d_tar_listing.txt"
python -m pip freeze > "$R/logs/lt3d_pip_freeze.txt"
echo "lt3d setup end $(date -u +%FT%TZ)"
echo LT3D_SETUP_DONE
