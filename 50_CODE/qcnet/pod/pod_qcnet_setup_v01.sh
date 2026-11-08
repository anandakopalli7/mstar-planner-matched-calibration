#!/usr/bin/env bash
# pod_qcnet_setup_v01.sh (QCNet arm, 2 Nov 2026): QCNet environment, code and checkpoint on the pod.
# Design: 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md section 4.
#   venv qcnet310 (Python 3.10, sees the image's torch 2.1.0+cu118 through --system-site-packages):
#     torch_geometric 2.3.1 (QCNet's environment.yml pins pyg 2.3.0 for torch 2.0; 2.3.1 is its patch release),
#     torch_cluster from the PyG wheel index for torch 2.1.0+cu118, pytorch-lightning 2.0.4 and torchmetrics 0.11.4
#     (environment.yml), av2 0.2.1 without PyAV (as in the detector stage), gdown for the Drive checkpoint.
#   QCNet code: ZikangZhou/QCNet at 55cacb418cbbce3753119c1f157360e66993d0d0, in its own folder (untrusted code).
#   Checkpoint QCNet_AV2: Drive id 1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv; SHA-256, MD5 and size recorded; verified by
#   qcnet_ckpt_verify_v01.py (restricted unpickling, model built from the checkpoint's hyper-parameters, strict load).
# venv and QCNet code on the container disk L=/root/local; logs and the checkpoint on the pod volume R=/root/work.
# Last line QCNET_SETUP_DONE.
set -euo pipefail
R=/root/work
L=/root/local
QC_COMMIT=55cacb418cbbce3753119c1f157360e66993d0d0
mkdir -p "$R/logs" "$R/ckpt_qcnet" "$L"
exec > >(tee -a "$R/logs/qcnet_setup_v01.log") 2>&1
echo "qcnet setup v01 start $(date -u +%FT%TZ)"
python -m pip install -q uv
cd "$L"
[ -d qcnet310 ] || python -m uv venv qcnet310 --python "$(command -v python3.10 || command -v python3)" --system-site-packages
source "$L/qcnet310/bin/activate"
python -V
python -c "import torch; print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available())"
uv pip install -q "numpy<2" "torch_geometric==2.3.1" "pytorch-lightning==2.0.4" "torchmetrics==0.11.4"
uv pip install -q torch_cluster -f https://data.pyg.org/whl/torch-2.1.0+cu118.html
uv pip install -q --no-deps "av2==0.2.1"
uv pip install -q pyarrow "pandas<2.2" scipy rich click joblib pyproj matplotlib "opencv-python-headless==4.10.0.84" gdown "numpy<2"
python -c "import torch, torch_geometric, torch_cluster, pytorch_lightning, av2; print('torch', torch.__version__, 'pyg', torch_geometric.__version__, 'torch_cluster', torch_cluster.__version__, 'pl', pytorch_lightning.__version__, 'av2', av2.__version__ if hasattr(av2, '__version__') else '0.2.1')"
[ -d QCNet/.git ] || git clone -q https://github.com/ZikangZhou/QCNet.git
cd QCNet
git checkout -q "$QC_COMMIT"
git rev-parse HEAD | tee "$R/logs/qcnet_commit_v01.txt"
[ "$(git rev-parse HEAD)" = "$QC_COMMIT" ] || { echo "QCNet commit mismatch"; exit 1; }
cd "$R/ckpt_qcnet"
if [ ! -s QCNet_AV2.ckpt ]; then
  gdown "1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv" -O QCNet_AV2.ckpt || gdown --fuzzy "https://drive.google.com/file/d/1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv/view" -O QCNet_AV2.ckpt
fi
ls -la QCNet_AV2.ckpt
sha256sum QCNet_AV2.ckpt | tee "$R/logs/qcnet_ckpt_sha256_v01.txt"
md5sum QCNet_AV2.ckpt | tee "$R/logs/qcnet_ckpt_md5_v01.txt"
stat -c '%s bytes' QCNet_AV2.ckpt | tee "$R/logs/qcnet_ckpt_size_v01.txt"
cd "$R"
python -I "$R/code_qcnet/qcnet_ckpt_verify_v01.py" --qcnet "$L/QCNet" --ckpt "$R/ckpt_qcnet/QCNet_AV2.ckpt" --out "$R/logs/qcnet_ckpt_verify_v01.json"
python -m pip freeze > "$R/logs/qcnet_pip_freeze_v01.txt" 2>/dev/null || uv pip freeze > "$R/logs/qcnet_pip_freeze_v01.txt"
echo "qcnet setup v01 end $(date -u +%FT%TZ)"
echo QCNET_SETUP_DONE
