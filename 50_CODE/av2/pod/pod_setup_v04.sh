#!/usr/bin/env bash
# pod_setup_v04.sh (v03 + the final check imports torch before any compiled op, and OpenCV pinned to a NumPy-1 build; v03: clone into a side folder when OpenPCDet/ already exists because the data were fetched into OpenPCDet/data first; v02: av2 0.2.0 without its PyAV/nox dependencies, which OpenPCDet never imports and which stalled pip): build the OpenPCDet environment on the RunPod GPU pod (D15 §3 step 2).
# Image: runpod/pytorch:2.1.0-py3.10-cuda11.8.0-devel-ubuntu22.04 (torch 2.1, CUDA 11.8 toolkit with nvcc).
# Work on the container disk (/root/work), not on /workspace. Every step logs to /root/work/logs; the last line is SETUP_DONE.
set -euo pipefail
R=/root/work
mkdir -p "$R/logs" "$R/ckpt"
exec > >(tee -a "$R/logs/setup.log") 2>&1
echo "setup start $(date -u +%FT%TZ)"
nvidia-smi
python -V
python -c "import torch; print('torch', torch.__version__, 'cuda', torch.version.cuda, torch.cuda.is_available())"
df -h /root | tail -1

pip install --no-cache-dir -q "numpy<2"
pip install --no-cache-dir -q spconv-cu118
pip install --no-cache-dir -q --no-deps av2==0.2.0
pip install --no-cache-dir -q click joblib matplotlib numba pandas pyarrow pyproj rich scipy "numpy<2"
pip install --no-cache-dir -q gdown "opencv-python-headless==4.10.0.84" "numpy<2"

cd "$R"
if [ ! -d OpenPCDet/.git ]; then
  rm -rf OpenPCDet_src
  git clone -q https://github.com/open-mmlab/OpenPCDet.git OpenPCDet_src
  mkdir -p OpenPCDet
  cp -a OpenPCDet_src/. OpenPCDet/
  rm -rf OpenPCDet_src
fi
cd OpenPCDet
git rev-parse HEAD | tee "$R/logs/openpcdet_commit.txt"
# requirements without torch/torchvision (already in the image) and with the headless OpenCV
grep -v -i -E '^(torch|torchvision|opencv-python)' requirements.txt > "$R/logs/requirements_filtered.txt"
pip install --no-cache-dir -q -r "$R/logs/requirements_filtered.txt" "numpy<2"
TORCH_CUDA_ARCH_LIST="8.0;8.6;8.9" python setup.py develop > "$R/logs/build_ops.log" 2>&1 || { tail -40 "$R/logs/build_ops.log"; exit 1; }
python -c "import numpy, cv2, torch, pcdet, spconv, av2; from pcdet.ops.iou3d_nms import iou3d_nms_cuda; from pcdet.ops.roiaware_pool3d import roiaware_pool3d_cuda; print('numpy', numpy.__version__, 'cv2', cv2.__version__, 'torch', torch.__version__, 'pcdet', pcdet.__version__, 'spconv', spconv.__version__, 'cuda ops ok')"
pip freeze > "$R/logs/pip_freeze.txt"
echo "setup end $(date -u +%FT%TZ)"
echo SETUP_DONE
