#!/usr/bin/env bash
# pod_qcnet_setup_v03.sh (QCNet arm, 2 Nov 2026) = pod_qcnet_setup_v02.sh + torch_scatter 2.1.2 (PyG wheel for torch 2.1.0+cu118),
# which QCNet's losses/mixture_nll_loss.py imports (v02's checkpoint check stopped there). The v02 venv is reused.
# pod_qcnet_setup_v02.sh = pod_qcnet_setup_v01.sh with the venv made by python -m venv and filled by pip
# under a constraint torch==2.1.0: in v01, uv's resolver did not count the image's torch and installed torch 2.14.1 into the venv,
# which broke the torch_cluster wheel built for torch 2.1 (undefined symbol). The old venv is removed first.
# QCNet environment, code and checkpoint on the pod.
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
exec > >(tee -a "$R/logs/qcnet_setup_v03.log") 2>&1
echo "qcnet setup v03 start $(date -u +%FT%TZ)"
cd "$L"
if [ -d qcnet310 ] && [ ! -f qcnet310/.v02 ]; then rm -rf qcnet310; fi
[ -d qcnet310 ] || { /usr/bin/python3.10 -m venv --system-site-packages qcnet310 && touch qcnet310/.v02; }
source "$L/qcnet310/bin/activate"
python -V
python -c "import torch; print('torch', torch.__version__, torch.version.cuda, torch.cuda.is_available())"
echo "torch==2.1.0" > "$L/qcnet_constraints_v02.txt"
PIP="python -m pip install -q --no-cache-dir -c $L/qcnet_constraints_v02.txt"
$PIP "numpy<2" "torch_geometric==2.3.1" "pytorch-lightning==2.0.4" "torchmetrics==0.11.4"
$PIP torch_cluster==1.6.3 -f https://data.pyg.org/whl/torch-2.1.0+cu118.html
$PIP torch_scatter==2.1.2 -f https://data.pyg.org/whl/torch-2.1.0+cu118.html
$PIP --no-deps "av2==0.2.1"
$PIP pyarrow "pandas<2.2" scipy rich click joblib pyproj matplotlib "opencv-python-headless==4.10.0.84" gdown "numpy<2"
python -c "import torch; assert torch.__version__.startswith('2.1.0'), torch.__version__; print('venv torch', torch.__version__, torch.__file__)"
python -c "import torch, torch_geometric, torch_cluster, torch_scatter, pytorch_lightning, av2; print('torch', torch.__version__, 'pyg', torch_geometric.__version__, 'torch_cluster', torch_cluster.__version__, 'pl', pytorch_lightning.__version__, 'av2', av2.__version__ if hasattr(av2, '__version__') else '0.2.1')"
[ -d QCNet/.git ] || git clone -q https://github.com/ZikangZhou/QCNet.git
cd QCNet
git checkout -q "$QC_COMMIT"
git rev-parse HEAD | tee "$R/logs/qcnet_commit_v03.txt"
[ "$(git rev-parse HEAD)" = "$QC_COMMIT" ] || { echo "QCNet commit mismatch"; exit 1; }
cd "$R/ckpt_qcnet"
if [ ! -s QCNet_AV2.ckpt ]; then
  gdown "1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv" -O QCNet_AV2.ckpt || gdown --fuzzy "https://drive.google.com/file/d/1OKBytt6N6BdRa9FWmS7F1-YvF0YectBv/view" -O QCNet_AV2.ckpt
fi
ls -la QCNet_AV2.ckpt
sha256sum QCNet_AV2.ckpt | tee "$R/logs/qcnet_ckpt_sha256_v03.txt"
md5sum QCNet_AV2.ckpt | tee "$R/logs/qcnet_ckpt_md5_v03.txt"
stat -c '%s bytes' QCNet_AV2.ckpt | tee "$R/logs/qcnet_ckpt_size_v03.txt"
cd "$R"
python -I "$R/code_qcnet/qcnet_ckpt_verify_v01.py" --qcnet "$L/QCNet" --ckpt "$R/ckpt_qcnet/QCNet_AV2.ckpt" --out "$R/logs/qcnet_ckpt_verify_v03.json"
python -m pip freeze > "$R/logs/qcnet_pip_freeze_v03.txt"
echo "qcnet setup v03 end $(date -u +%FT%TZ)"
echo QCNET_SETUP_DONE
