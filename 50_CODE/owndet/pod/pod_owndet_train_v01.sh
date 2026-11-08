#!/usr/bin/env bash
# pod_owndet_train_v01.sh (own-detector job, 2 Nov 2026): the full training run of OWN_DETECTOR_DESIGN_v01.md section 4, with the
# epoch count E and batch B recorded in 50_CODE/owndet/OWN_DETECTOR_PILOT_v01.md before this run. From scratch; resumes from the last
# epoch checkpoint after a container restart. Usage: EPOCHS=E BATCH=B bash pod_owndet_train_v01.sh. Marker: OD_TRAIN_DONE.
set -uo pipefail
R=/root/work; L=/root/local; C=$R/code_owndet
S=$L/av2/sensor; I=$S/av2_owndet_infos
LOG=$R/logs/owndet_train_v01.log
exec > >(tee -a "$LOG") 2>&1
: "${EPOCHS:?}" "${BATCH:?}"
WK=${WORKERS:-11}
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
echo "owndet train v01 start $(date -u +%FT%TZ) epochs=$EPOCHS batch=$BATCH workers=$WK"
mkdir -p /home/ubuntu/Workspace/Data; ln -sfn "$S" /home/ubuntu/Workspace/Data/Sensor
source "$L/lt3d38/bin/activate"
cd "$L/LT3D"
PUB=$L/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
WD=$R/owndet/train_e${EPOCHS}_b${BATCH}
CFG=$R/owndet/cfg_train_e${EPOCHS}_b${BATCH}.py
[ -s "$CFG" ] || python "$C/pod_owndet_cfg_v01.py" --lt3d "$L/LT3D" --public-cfg "$PUB" --infos-dir "$I" --data-root "$S/" --batch $BATCH --workers $WK \
    --epochs $EPOCHS --work-dir "$WD" --out "$CFG" --dataset-len > "$R/logs/owndet_cfg_train.log" 2>&1 || { tail -n 5 "$R/logs/owndet_cfg_train.log"; echo OD_TRAIN_FAILED; exit 1; }
sha256sum "$CFG" | tee "$R/owndet/cfg_train_sha256.txt"
RES=""
[ -f "$WD/latest.pth" ] && RES="--resume-from $WD/latest.pth" && echo "resuming from $(readlink -f "$WD/latest.pth")"
python tools/train.py "$CFG" --work-dir "$WD" --seed 0 $RES > "$R/logs/owndet_train_run.log" 2>&1
if [ -s "$WD/epoch_${EPOCHS}.pth" ]; then
  sha256sum "$WD/epoch_${EPOCHS}.pth" | tee "$R/owndet/own_ckpt_sha256.txt"
  echo "owndet train v01 end $(date -u +%FT%TZ)"
  echo OD_TRAIN_DONE
else
  tail -n 20 "$R/logs/owndet_train_run.log"
  echo OD_TRAIN_FAILED
fi
