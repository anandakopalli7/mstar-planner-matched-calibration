#!/usr/bin/env bash
# pod_chain_v04.sh (v03 calling pod_run_v02.sh): the fetch is done (fetcher v04, manifest already in /root/work/out); wait for setup v03, pin OpenCV to a
# NumPy-1 build (opencv-python-headless 5.x needs numpy>=2), then run pod_run_v01.sh ckpt -> prep -> test -> export.
set -euo pipefail
R=/root/work
D=$R/OpenPCDet/data/argo2/sensor/val
exec > >(tee -a "$R/logs/chain.log") 2>&1
echo "chain v03 start $(date -u +%FT%TZ)"
[ -s "$R/out/MANIFEST_av2_val_lidar_v04_maps.csv" ] || { echo "CHAIN STOP: manifest missing"; exit 1; }
n=$(ls "$D" | wc -l); echo "val log folders: $n"; [ "$n" -eq 150 ] || { echo "CHAIN STOP: expected 150 log folders"; exit 1; }
until grep -q "SETUP_DONE" "$R/logs/setup.log" 2>/dev/null; do
  if ! pgrep -f "[p]od_setup_v03.sh" >/dev/null; then grep -q "SETUP_DONE" "$R/logs/setup.log" || { echo "CHAIN STOP: setup v03 exited without SETUP_DONE"; tail -20 "$R/logs/setup.log"; exit 1; }; fi
  sleep 30
done
pip install --no-cache-dir -q "opencv-python-headless==4.10.0.84" "numpy<2"
python -c "import numpy, cv2, torch, pcdet; print('numpy', numpy.__version__, 'cv2', cv2.__version__, 'torch', torch.__version__)"
for s in ckpt prep test export; do
  echo "chain: step $s $(date -u +%FT%TZ)"
  bash "$R/code/pod_run_v02.sh" "$s"
done
echo "chain end $(date -u +%FT%TZ)"
echo CHAIN_DONE
