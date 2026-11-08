#!/usr/bin/env bash
# pod_lt3d_setup_v05.sh (QCNet arm rerun, 2 Nov 2026) = pod_lt3d_setup_v04.sh with MAX_JOBS=8 for the mmdet3d build (pod qcnet2 has a
# 41 GB memory limit and 17 CPUs; v04 used 32 parallel compiler jobs on a 116 GB pod). Logs to lt3d_setup_v05.log.
# pod_lt3d_setup_v04.sh = 50_CODE/av2/pod/pod_lt3d_setup_v03.sh with three changes:
#   (1) LT3D is checked out at the detector stage's commit e33189aa09f282cf555b64dba1654eb0c14464a6 (v03 cloned HEAD and recorded it);
#   (2) filterpy 1.4.5 is installed for LT3D's AB3DMOT (tracking/ab3dmot.py imports filterpy.kalman);
#   (3) logs go to $R/logs/lt3d_setup_v04.log on the pod volume, while the venv, the repository and the checkpoint tarball live on
#       the container disk L=/root/local (the volume is a network file system with ~35 ms per file create). Everything else (versions, build flags, checkpoint folder) is unchanged.
# Build LT3D (mmdet3d fork; official AV2 detection baseline) in its own Python 3.8 venv on the pod.
# Last line LT3D_SETUP_DONE.
set -euo pipefail
R=/root/work
L=/root/local
LT3D_COMMIT=e33189aa09f282cf555b64dba1654eb0c14464a6
mkdir -p "$R/logs" "$L/ckpt_lt3d"
exec > >(tee -a "$R/logs/lt3d_setup_v05.log") 2>&1
echo "lt3d setup v05 start $(date -u +%FT%TZ)"
python -m pip install -q uv
cd "$L"
[ -d lt3d38 ] || python -m uv venv lt3d38 --python 3.8
source "$L/lt3d38/bin/activate"
python -V
command -v uv >/dev/null || python -m pip install -q uv
uv pip install -q pip
which python; python -m pip --version
uv pip install -q torch==1.10.1+cu111 torchvision==0.11.2+cu111 --extra-index-url https://download.pytorch.org/whl/cu111 --index-strategy unsafe-best-match
uv pip install -q mmcv-full==1.6.1 -f https://download.openmmlab.com/mmcv/dist/cu111/torch1.10.0/index.html
uv pip install -q mmdet==2.25.2 mmsegmentation==0.28.0 "numpy<1.24" setuptools==59.5.0 wheel ninja
[ -d LT3D/.git ] || git clone -q https://github.com/neeharperi/LT3D.git
cd LT3D
git checkout -q "$LT3D_COMMIT"
git rev-parse HEAD | tee "$R/logs/lt3d_commit_v04.txt"
[ "$(git rev-parse HEAD)" = "$LT3D_COMMIT" ] || { echo "LT3D commit mismatch"; exit 1; }
python -c "import torch; print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available())"
TORCH_CUDA_ARCH_LIST="8.0;8.6" FORCE_CUDA=1 MAX_JOBS=8 python -m pip install -v --no-build-isolation -e . > "$R/logs/lt3d_build_v04.log" 2>&1 || { tail -60 "$R/logs/lt3d_build_v04.log"; exit 1; }
uv pip install -q -r requirements/optional.txt || echo "optional requirements: some failed (non-fatal)"
uv pip install -q cumm-cu111 spconv-cu111 pyntcloud pyarrow "numpy<1.24" setuptools==59.5.0 gdown click joblib matplotlib pandas pyproj rich scipy
uv pip install -q --no-deps "av2==0.2.1"
uv pip install -q --no-deps "filterpy==1.4.5"
uv pip uninstall -q nuscenes-devkit || true
uv pip install -q --reinstall numba "numpy<1.24"
python -c "import mmcv, mmdet, mmdet3d, spconv, av2, filterpy; print('mmcv', mmcv.__version__, 'mmdet', mmdet.__version__, 'mmdet3d', mmdet3d.__version__, 'spconv', spconv.__version__, 'filterpy', filterpy.__version__)"
# the released AV2 detectors (one tarball in the LT3D 'Pre-trained Detection Models' Drive folder)
cd "$L/ckpt_lt3d"
f=$(find "$L/ckpt_lt3d" -name "av2_detectors.tar.gz" | head -1)
if [ -z "$f" ]; then gdown --folder "https://drive.google.com/drive/folders/1BVhYv-kJE_ydbvDDz8AA3pgDdVTSCHIT" -O "$L/ckpt_lt3d" || true; fi
f=$(find "$L/ckpt_lt3d" -name "av2_detectors.tar.gz" | head -1)
ls -la "$f"; sha256sum "$f" | tee "$R/logs/lt3d_tar_sha256_v04.txt"
C=centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2
[ -s "$L/ckpt_lt3d/av2_detectors/$C/epoch_20.pth" ] || tar -xzf "$f" "av2_detectors/$C"
sha256sum "$L/ckpt_lt3d/av2_detectors/$C/epoch_20.pth" | tee "$R/logs/lt3d_centerpoint_ckpt_sha256_v04.txt"
grep -q "^299cf3b741290afd18e2aab11f1dc7a199448b669d38e4418e64453ed7e2e50c " "$R/logs/lt3d_centerpoint_ckpt_sha256_v04.txt" || { echo "LT3D checkpoint hash differs from the detector stage"; exit 1; }
python -m pip freeze > "$R/logs/lt3d_pip_freeze_v04.txt"
echo "lt3d setup v05 end $(date -u +%FT%TZ)"
echo LT3D_SETUP_DONE
