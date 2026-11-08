#!/usr/bin/env bash
# pod_chain_v01.sh: wait for the v04 fetch and the OpenPCDet setup, then run pod_run_v01.sh ckpt -> prep -> test -> export.
# The fetch step of pod_run_v01.sh is not used (it calls fetcher v02); fetcher v04 ran separately into the same folder.
set -euo pipefail
R=/root/work
D=$R/OpenPCDet/data/argo2/sensor/val
exec > >(tee -a "$R/logs/chain.log") 2>&1
echo "chain start $(date -u +%FT%TZ)"
until grep -q -E "AV2 FETCH (DONE|INCOMPLETE)" "$R/logs/fetch_v04.log" 2>/dev/null; do sleep 30; done
grep -q "AV2 FETCH DONE" "$R/logs/fetch_v04.log" || { echo "CHAIN STOP: fetch incomplete"; tail -5 "$R/logs/fetch_v04.log"; exit 1; }
mkdir -p "$R/out"
mv "$D/MANIFEST_av2_val_lidar_v04_maps.csv" "$R/out/"
n=$(ls "$D" | wc -l); echo "val log folders: $n"; [ "$n" -eq 150 ] || { echo "CHAIN STOP: expected 150 log folders"; exit 1; }
echo STEP_fetch_DONE | tee -a "$R/logs/run.log"
until grep -q "SETUP_DONE" "$R/logs/setup.log" 2>/dev/null; do
  if ! pgrep -f "[p]od_setup_v02.sh" >/dev/null; then grep -q "SETUP_DONE" "$R/logs/setup.log" || { echo "CHAIN STOP: setup exited without SETUP_DONE"; tail -20 "$R/logs/setup.log"; exit 1; }; fi
  sleep 30
done
for s in ckpt prep test export; do
  echo "chain: step $s $(date -u +%FT%TZ)"
  bash "$R/code/pod_run_v01.sh" "$s"
done
echo "chain end $(date -u +%FT%TZ)"
echo CHAIN_DONE
