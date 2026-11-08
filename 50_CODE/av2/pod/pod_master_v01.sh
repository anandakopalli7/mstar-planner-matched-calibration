#!/usr/bin/env bash
# pod_master_v01.sh: one resumable driver for the AV2 detection job (D15 §3 step 2) on a pod with a /workspace volume.
# The first pod (apxubol79e8yoq) lost its host after the download and both builds; its container disk held everything.
# Here all work lives on the pod volume (/workspace/work, reached as /root/work so every script runs unchanged), and each
# step is skipped when its done-marker is already in its log, so a container restart resumes instead of starting over.
# Order: [fetch v04 | OpenPCDet setup v04 | LT3D setup v03] in parallel -> checks -> [OpenPCDet ckpt/prep/test/export |
#        LT3D extract/prep/test/export] in parallel. Markers: MASTER_STOP <reason> or MASTER_DONE in /root/work/logs/master.log.
set -uo pipefail
mkdir -p /workspace/work
if [ ! -L /root/work ]; then [ -e /root/work ] && mv /root/work "/root/work_old_$(date +%s)"; ln -s /workspace/work /root/work; fi
R=/root/work
mkdir -p "$R/logs" "$R/out" "$R/code"
exec > >(tee -a "$R/logs/master.log") 2>&1
echo "master start $(date -u +%FT%TZ)"
D=$R/OpenPCDet/data/argo2/sensor/val
has() { grep -q "$1" "$2" 2>/dev/null; }
stop() { echo "MASTER_STOP $*"; exit 1; }

# ---- stage 1: data and environments, in parallel
( if ! has "AV2 FETCH DONE" "$R/logs/fetch_v04.log"; then
    mkdir -p "$D" "$R/OpenPCDet/data/argo2/sensor/train"
    python -B "$R/code/av2_fetch_v04.py" --out "$D" --threads 128 --maps > "$R/logs/fetch_v04.log" 2>&1
  fi ) & PA=$!
( has "SETUP_DONE" "$R/logs/setup.log" || bash "$R/code/pod_setup_v04.sh" > "$R/logs/setup_nohup.log" 2>&1 ) & PB=$!
( has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup.log" || bash "$R/code/pod_lt3d_setup_v03.sh" > "$R/logs/lt3d_setup_nohup.log" 2>&1 ) & PC=$!
wait $PA $PB $PC
has "AV2 FETCH DONE" "$R/logs/fetch_v04.log" || stop "fetch: $(tail -2 "$R/logs/fetch_v04.log")"
has "SETUP_DONE" "$R/logs/setup.log" || stop "OpenPCDet setup: $(tail -3 "$R/logs/setup.log")"
has "LT3D_SETUP_DONE" "$R/logs/lt3d_setup.log" || stop "LT3D setup: $(tail -3 "$R/logs/lt3d_setup.log")"
[ -f "$D/MANIFEST_av2_val_lidar_v04_maps.csv" ] && mv "$D/MANIFEST_av2_val_lidar_v04_maps.csv" "$R/out/"
[ -s "$R/out/MANIFEST_av2_val_lidar_v04_maps.csv" ] || stop "manifest missing"
n=$(ls "$D" | wc -l); [ "$n" -eq 150 ] || stop "expected 150 log folders, found $n"
echo "stage 1 done $(date -u +%FT%TZ): 150 logs, both environments built"

# ---- stage 2: both detectors, in parallel
( for s in ckpt prep test export; do
    has "STEP_${s}_DONE" "$R/logs/run.log" && continue
    echo "openpcdet: step $s $(date -u +%FT%TZ)"
    bash "$R/code/pod_run_v02.sh" "$s" || { echo "OPENPCDET_FAILED at $s"; exit 1; }
  done; echo OPENPCDET_PIPELINE_DONE ) & PD=$!
( C=$R/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2
  if [ ! -s "$C/epoch_20.pth" ]; then
    f=$(find "$R/ckpt_lt3d" -name av2_detectors.tar.gz | head -1); [ -n "$f" ] || { echo "LT3D_FAILED: tarball missing"; exit 1; }
    (cd "$R/ckpt_lt3d" && tar -xzf "$f" "av2_detectors/$(basename "$C")")
  fi
  sha256sum "$C/epoch_20.pth" | tee "$R/logs/lt3d_centerpoint_ckpt_sha256.txt"
  for s in prep test export; do
    has "STEP_lt3d_${s}_DONE" "$R/logs/lt3d_run.log" && continue
    if [ "$s" = test ]; then  # one GPU job at a time (24 GB cards): wait for the OpenPCDet inference to finish or fail
      until has "STEP_test_DONE" "$R/logs/run.log" || has "OPENPCDET_FAILED" "$R/logs/master.log"; do sleep 30; done
    fi
    echo "lt3d: step $s $(date -u +%FT%TZ)"
    bash "$R/code/pod_lt3d_run_v02.sh" "$s" || { echo "LT3D_FAILED at $s"; exit 1; }
  done; echo LT3D_PIPELINE_DONE ) & PL=$!
wait $PD; a=$?
wait $PL; b=$?
echo "stage 2 exit codes: openpcdet=$a lt3d=$b"
[ $a -eq 0 ] && [ $b -eq 0 ] || stop "a detector pipeline failed (see run.log / lt3d_run.log)"
echo "master end $(date -u +%FT%TZ)"
echo MASTER_DONE
