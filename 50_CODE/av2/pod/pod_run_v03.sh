#!/usr/bin/env bash
# pod_run_v03.sh (v02 + the model-zoo file is a bare state dict, so test uses a copy wrapped as {'model_state': sd};
# the original is kept and both SHA-256 are recorded). v02: gdown called with the Drive file id.
# Steps, each logged to /root/work/logs and marked by a STEP_<name>_DONE line:
#   fetch   the 150 val logs (lidar, annotations, poses, calibration, maps) from the public S3 bucket with av2_fetch_v02.py
#   ckpt    the OpenPCDet VoxelNeXt Argoverse 2 checkpoint from the model-zoo Google Drive link; SHA-256 recorded
#   prep    OpenPCDet info generation (feather -> bin, argo2_infos_val.pkl, val_anno.feather)
#   test    inference on val + the official AV2 detection evaluation (detector AP only: allowed before any freeze, D15 §4)
#   export  detections -> pickle-free npz + feather in the standard AV2 detection format
# Outcome-blind rule (D15 §4): nothing here computes exceedance, margins, infeasibility or ANEES.
set -euo pipefail
R=/root/work
OP=$R/OpenPCDet
D=$OP/data/argo2
CK=$R/ckpt/voxelnext_argo2_openpcdet_modelzoo.pth
CKW=$R/ckpt/voxelnext_argo2_openpcdet_modelzoo_wrapped_model_state.pth
STEP=${1:-all}
mkdir -p "$R/logs" "$R/out" "$D/sensor/train" "$D/sensor/val"
exec > >(tee -a "$R/logs/run.log") 2>&1
echo "run start $(date -u +%FT%TZ) step=$STEP"

if [ "$STEP" = all ] || [ "$STEP" = fetch ]; then
  python -B "$R/code/av2_fetch_v02.py" --out "$D/sensor/val" --threads 32 --maps > "$R/logs/fetch.log" 2>&1
  tail -3 "$R/logs/fetch.log"
  grep -q "AV2 FETCH DONE" "$R/logs/fetch.log"
  # the manifest is not a log folder; move it so that OpenPCDet's os.listdir sees only the 150 log ids
  mv "$D/sensor/val/MANIFEST_av2_val_lidar_v02_maps.csv" "$R/out/"
  ls "$D/sensor/val" | wc -l
  echo STEP_fetch_DONE
fi

if [ "$STEP" = all ] || [ "$STEP" = ckpt ]; then
  [ -s "$CK" ] || gdown "1YP2UOz-yO-cWfYQkIqILEu6bodvCBVrR" -O "$CK"
  sha256sum "$CK" | tee "$R/out/ckpt_sha256.txt"
  ls -la "$CK"
  echo STEP_ckpt_DONE
fi

if [ "$STEP" = all ] || [ "$STEP" = prep ]; then
  cd "$OP"
  python -m pcdet.datasets.argo2.argo2_dataset --root_path data/argo2/sensor --output_dir data/argo2 > "$R/logs/prep.log" 2>&1
  tail -5 "$R/logs/prep.log"
  ls -la data/argo2/*.pkl data/argo2/val_anno.feather
  ls data/argo2/training/velodyne | wc -l
  echo STEP_prep_DONE
fi

if [ "$STEP" = all ] || [ "$STEP" = test ]; then
  if [ ! -s "$CKW" ]; then
    python -c "import torch, sys; sd = torch.load(sys.argv[1], map_location='cpu'); assert 'model_state' not in sd; torch.save({'model_state': sd, 'epoch': None, 'version': None}, sys.argv[2])" "$CK" "$CKW"
  fi
  sha256sum "$CK" "$CKW" | tee "$R/out/ckpt_sha256.txt"
  cd "$OP/tools"
  python test.py --cfg_file cfgs/argo2_models/cbgs_voxel01_voxelnext.yaml --batch_size 4 --workers 6 \
         --ckpt "$CKW" --extra_tag av2val_v01 > "$R/logs/test.log" 2>&1
  tail -60 "$R/logs/test.log"
  find "$OP/output" -name result.pkl -path "*av2val_v01*" | tee "$R/out/result_pkl_path.txt"
  echo STEP_test_DONE
fi

if [ "$STEP" = all ] || [ "$STEP" = export ]; then
  cd "$OP/tools"
  python -B "$R/code/pod_export_v01.py" --result "$(cat "$R/out/result_pkl_path.txt")" \
         --cfg cfgs/argo2_models/cbgs_voxel01_voxelnext.yaml --out "$R/out" > "$R/logs/export.log" 2>&1
  tail -10 "$R/logs/export.log"
  cp "$R/logs/"*.log "$R/logs/"*.txt "$R/out/" 2>/dev/null || true
  (cd "$R/out" && sha256sum * > SHA256SUMS.txt)
  echo STEP_export_DONE
fi
echo "run end $(date -u +%FT%TZ)"
echo RUN_DONE
