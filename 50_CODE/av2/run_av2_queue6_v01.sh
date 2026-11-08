#!/usr/bin/env bash
# AV2 queue 6 (Claude line, v01, 2 Nov 2026) = queue 5 reordered (queue 5 stopped on purpose after HOTA T1 x LT3D and the
# AB3DMOT shim test, both done, so that the four remaining HOTA runs come before the long AB3DMOT runs) and with AB3DMOT in
# 6 log-workers. Original header of queue 5: AV2 queue 5 = queue 4 plus the HOTA runs of T1/T3 x LT3D/VoxelNeXt and T2 x LT3D with
# av2_hota_v03 (v02 paired frames of different logs), under one slot control. Queue 4 and run_av2_hota_v01.sh were stopped on
# purpose (the HOTA bug). Original header of queue 4: AB3DMOT with the exact association shim (av2_ab3dmot_v04 --fast), after an
# equivalence test on one log against the unshimmed run; then its stage-A cache, K8 items (counts only), the final
# AV2_TRACKER_COUNTS_v02.json with all five runs, HOTA and nuScenes-protocol AMOTA for both AB3DMOT exports.
# Replaces run_av2_queue3_v01.sh (stopped on purpose: AB3DMOT v03 at 650 s per log). Slots: my processes in total <= 1 until
# the K8 log prints its end line, <= 3 after; run_av2_hota_v01.sh, while it runs, holds one of them.
# Nothing here reads a ground-truth position on AV2 or computes an outcome.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"; PYA="$W/50_CODE/env/av2eval310/Scripts/python.exe"; PYB="$W/50_CODE/env/ab3dmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; O="$W/30_DATA/av2_cache_stageA_v01"; LG="$O/logs"; R="$W/60_RESULTS/av2_trk"
AB="$W/30_DATA/av2_trk_v01/export_ab3dmot_v04w6"; ABT="$W/30_DATA/av2_trk_v01/test_ab3dmot_fast"; GT="$(w "$W/30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json")"
K8LOG="$W/80_LOGS/k8_expl_v02_20261101_190548.log"; HLOG="$LG/run_hota_v01.log"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR="$(w "$W/30_DATA/av2_trk_v01/numba_cache")"
mkdir -p "$R/hota" "$R/metrics" "$AB" "$ABT"
cd /c/Users/anand
maxj() { grep -q "K8 exploratory run v02 end" "$K8LOG" 2>/dev/null && echo 3 || echo 1; }
limit() { while [ "$(jobs -rp | wc -l)" -ge "$(maxj)" ]; do sleep 20; done; }
hota() { local lab=$1; shift
  "$PYA" -I -B "$(w "$S/av2_hota_v03.py")" --gt "$GT" --exports "$@" --label "$lab" --out "$(w "$R/hota/AV2_HOTA_$lab.json")" > "$LG/hota_$lab.log" 2>&1
  echo "hota $lab: $(grep -v -i warn "$LG/hota_$lab.log" | tail -n 2 | head -n 1 | cut -c1-220) $(date +%H:%M:%S)"; }
amota() { local lab=$1; shift
  "$PY" -I -B "$(w "$S/av2_track_metrics_v03.py")" --gt "$GT" --label "AV2 val $lab" --exports "$@" --classes car pedestrian bicycle \
    --out "$(w "$R/metrics/AV2_metrics_$lab.json")" > "$LG/metrics_$lab.log" 2>&1
  echo "amota $lab done $(date +%H:%M:%S)"; }
echo "queue6 start $(date +%H:%M:%S)"
TX="$W/30_DATA/av2_trk_v01/export"
for combo in t3_lt3d t1_voxelnext t3_voxelnext t2_lt3d; do
  limit; hota $combo $(for i in 0 1 2 3; do w "$TX/$combo/worker$i"; done) &
done

grep -q '"identical": true' "$R/AB3DMOT_FAST_SHIM_TEST_v01.json" || { echo "SHIM TEST MISSING OR FAILED: stopping"; exit 0; }
ABP=()
for i in 0 1 2 3 4 5; do
  limit; "$PYB" -I -B "$(w "$S/av2_ab3dmot_v04.py")" --out "$(w "$AB")" --worker $i --n-workers 6 --fast > "$LG/ab3dmot_v04_w$i.log" 2>&1 &
  ABP+=($!); echo "ab3dmot worker $i started $(date +%H:%M:%S)"
done
for p in "${ABP[@]}"; do wait $p; done
echo "ab3dmot workers: $(for i in 0 1 2 3 4 5; do tail -n 1 "$LG/ab3dmot_v04_w$i.log"; done | tr '\n' ' ') $(date +%H:%M:%S)"
"$PY" -I -B -c "
import gzip, sys
with gzip.open(sys.argv[1], 'wt') as fo:
    for p in sys.argv[2:]:
        with gzip.open(p, 'rt') as f:
            for line in f:
                fo.write(line)
" "$(w "$AB/horizon8_ab3dmot_kf.jsonl.gz")" $(for i in 0 1 2 3 4 5; do w "$AB/horizon8_ab3dmot_kf_worker$i.jsonl.gz"; done)
limit
"$PY" -I -B "$(w "$S/av2_cache_stageA_v01.py")" --dataset av2 --experiment lt3d/ab3dmot --workers $(for i in 0 1 2 3 4 5; do w "$AB/ab3dmot_kf/worker$i"; done) \
  --horizon "$(w "$AB/horizon8_ab3dmot_kf.jsonl.gz")" --gt "$GT" --ego "$(w "$O/av2_ego10hz_v01.json.gz")" \
  --out "$(w "$O/cache_stageA_ab3dmot_lt3d")" > "$LG/stageA_ab3dmot_lt3d.log" 2>&1
echo "stageA ab3dmot: $(tail -n 1 "$LG/stageA_ab3dmot_lt3d.log") $(date +%H:%M:%S)"
limit; hota ab3dmot_det $(for i in 0 1 2 3 4 5; do w "$AB/ab3dmot_det/worker$i"; done) &
limit; amota ab3dmot_det $(for i in 0 1 2 3 4 5; do w "$AB/ab3dmot_det/worker$i"; done) &
limit
"$PY" -I -B "$(w "$W/50_CODE/k8/k8_items_v04.py")" --caches "$(w "$O/cache_stageA_ab3dmot_lt3d")" \
  --out "$(w "$O/items/items_k8_v04_av2_stageA_ab3dmot_lt3d.npz")" --av2 --counts-only --workers 1 > "$LG/items_ab3dmot_lt3d.log" 2>&1
echo "items ab3dmot: $(tail -n 1 "$LG/items_ab3dmot_lt3d.log") $(date +%H:%M:%S)"
limit
"$PY" -I -B "$(w "$S/av2_counts_v02.py")" \
  --runs $(for c in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext ab3dmot_lt3d; do echo "$c=$(w "$O/items/items_k8_v04_av2_stageA_$c.npz")"; done) \
  --caches $(for c in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext ab3dmot_lt3d; do echo "$c=$(w "$O/cache_stageA_$c")"; done) \
  --out "$(w "$R/AV2_TRACKER_COUNTS_v02.json")" > "$LG/counts_v02_final.log" 2>&1
echo "counts v02 (5 runs): $(tail -n 5 "$LG/counts_v02_final.log" | cut -c1-120 | tr '\n' ' ') $(date +%H:%M:%S)"
limit; hota ab3dmot_kf $(for i in 0 1 2 3 4 5; do w "$AB/ab3dmot_kf/worker$i"; done) &
limit; amota ab3dmot_kf $(for i in 0 1 2 3 4 5; do w "$AB/ab3dmot_kf/worker$i"; done) &
wait
echo "QUEUE6 DONE $(date +%H:%M:%S)"; true
