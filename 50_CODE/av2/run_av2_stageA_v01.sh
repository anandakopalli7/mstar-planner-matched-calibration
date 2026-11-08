#!/usr/bin/env bash
# AV2 stage A (Claude line, v01, 2 Nov 2026): after run_av2_propagate_v01.sh, one process at a time (the K8 run shares the
# laptop): AV2 ego path; stage-A caches for T1/T3 x LT3D/VoxelNeXt; the nuScenes-only tests (stage-A builder and stage B
# against the K6 caches; k8_items_v04 --counts-only against k8_items_v02 on the development scenes); K8 items in counts-only
# mode on the AV2 stage-A caches; AV2_TRACKER_COUNTS_v02.json. No ground-truth position is read on AV2; stage B is never run
# on AV2.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; O="$W/30_DATA/av2_cache_stageA_v01"; LG="$O/logs"; R="$W/60_RESULTS/av2_trk"; NT="$R/stageAB_nuscenes_test"
TX="$W/30_DATA/av2_trk_v01/export"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
mkdir -p "$NT" "$O/items"
cd /c/Users/anand
declare -A EXP=([t1]=paper/local/canmot/sc [t3]=paper/baseline/poly_mot)
while ! grep -q "PROPAGATION DONE" "$LG/run_propagate_v01.log" 2>/dev/null; do sleep 20; done
echo "start $(date +%H:%M:%S)"
"$PY" -I -B "$(w "$S/av2_ego_prep_v01.py")" --gt "$(w "$W/30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json")" --out "$(w "$O/av2_ego10hz_v01.json.gz")" > "$LG/ego_prep.log" 2>&1
tail -n 2 "$LG/ego_prep.log"
for combo in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext; do
  tr=${combo%%_*}
  "$PY" -I -B "$(w "$S/av2_cache_stageA_v01.py")" --dataset av2 --experiment ${EXP[$tr]} \
    --workers $(for i in 0 1 2 3; do w "$TX/$combo/worker$i"; done) --horizon "$(w "$O/horizon8_$combo.jsonl.gz")" \
    --gt "$(w "$W/30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json")" --ego "$(w "$O/av2_ego10hz_v01.json.gz")" \
    --out "$(w "$O/cache_stageA_$combo")" > "$LG/stageA_$combo.log" 2>&1
  echo "$combo $(tail -n 1 "$LG/stageA_$combo.log") $(date +%H:%M:%S)"
done
# nuScenes-only tests: the stage-A builder and stage B against the K6 caches (val, T1 and T3)
META="$(w "$W/30_DATA/nuscenes/v1.0-trainval")"; GTVA="$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")"; EGO="$(w "$W/30_DATA/k6/k6_ego20hz_v01.json.gz")"
declare -A NWK=([t1]="$W/60_RESULTS/x1_export_val150_v02" [t3]="$W/60_RESULTS/m_export_polymot_v01/val")
for tr in t1 t3; do
  "$PY" -B "$(w "$S/av2_cache_stageA_v01.py")" --dataset nuscenes --experiment ${EXP[$tr]} \
    --workers $(for i in 0 1 2; do w "${NWK[$tr]}/worker$i"; done) --horizon "$(w "$W/60_RESULTS/k6_horizon_v01/horizon8_${tr}_val.jsonl.gz")" \
    --gt "$GTVA" --ego "$EGO" --meta "$META" --out "$(w "$NT/${tr}_val_A")" > "$LG/nusc_stageA_$tr.log" 2>&1
  "$PY" -B "$(w "$S/test_av2_stageAB_on_nuscenes_v01.py")" --mode A --test "$(w "$NT/${tr}_val_A")" --ref "$(w "$W/30_DATA/k6/cache_v02_${tr}_val")" \
    --out "$(w "$NT/STAGE_A_TEST_${tr}_val_v01.json")" > "$LG/nusc_testA_$tr.log" 2>&1
  "$PY" -B "$(w "$S/av2_cache_stageB_v01.py")" --stage-a "$(w "$NT/${tr}_val_A")" --gt "$GTVA" --out "$(w "$NT/${tr}_val_B")" > "$LG/nusc_stageB_$tr.log" 2>&1
  "$PY" -B "$(w "$S/test_av2_stageAB_on_nuscenes_v01.py")" --mode B --test "$(w "$NT/${tr}_val_B")" --ref "$(w "$W/30_DATA/k6/cache_v02_${tr}_val")" \
    --out "$(w "$NT/STAGE_B_TEST_${tr}_val_v01.json")" > "$LG/nusc_testB_$tr.log" 2>&1
  echo "nuscenes $tr A: $(grep -o '"identical": [a-z]*' "$NT/STAGE_A_TEST_${tr}_val_v01.json") B: $(grep -o '"identical": [a-z]*' "$NT/STAGE_B_TEST_${tr}_val_v01.json") $(date +%H:%M:%S)"
done
# stage-B guard on an AV2 stage-A cache (must refuse; writes nothing)
"$PY" -B "$(w "$S/av2_cache_stageB_v01.py")" --stage-a "$(w "$O/cache_stageA_t1_lt3d")" --gt "$(w "$W/30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json")" \
  --out "$(w "$NT/must_not_exist_av2_stageB")" > "$LG/stageB_guard_av2.log" 2>&1
echo "stage-B AV2 guard: $(tail -n 1 "$LG/stageB_guard_av2.log")"
# k8_items_v04 --counts-only against k8_items_v02 on the nuScenes development scenes
K8="$W/50_CODE/k8"; C1="$(w "$W/30_DATA/k6/cache_v02_t1_train") $(w "$W/30_DATA/k6/cache_v02_t1_val")"
"$PY" -B "$(w "$K8/k8_items_v02.py")" --caches $C1 --out "$(w "$NT/items_v02_dev_t1.npz")" --dev --workers 1 > "$LG/items_v02_dev.log" 2>&1
"$PY" -B "$(w "$K8/k8_items_v04.py")" --caches $C1 --out "$(w "$NT/items_v04co_dev_t1.npz")" --dev --counts-only --workers 1 > "$LG/items_v04_dev.log" 2>&1
"$PY" -B "$(w "$S/test_k8_items_v04_v01.py")" --v02 "$(w "$NT/items_v02_dev_t1.npz")" --v04 "$(w "$NT/items_v04co_dev_t1.npz")" \
  --out "$(w "$NT/K8_ITEMS_V04_TEST_v01.json")" > "$LG/items_v04_test.log" 2>&1
echo "k8_items_v04 test: $(grep -o '"identical": [a-z]*' "$NT/K8_ITEMS_V04_TEST_v01.json") $(date +%H:%M:%S)"
# K8 items, counts only, on AV2 stage A
for combo in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext; do
  "$PY" -I -B "$(w "$K8/k8_items_v04.py")" --caches "$(w "$O/cache_stageA_$combo")" --out "$(w "$O/items/items_k8_v04_av2_stageA_$combo.npz")" \
    --av2 --counts-only --workers 1 > "$LG/items_$combo.log" 2>&1
  echo "items $combo $(tail -n 1 "$LG/items_$combo.log") $(date +%H:%M:%S)"
done
"$PY" -I -B "$(w "$S/av2_counts_v02.py")" \
  --runs $(for c in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext; do echo "$c=$(w "$O/items/items_k8_v04_av2_stageA_$c.npz")"; done) \
  --caches $(for c in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext; do echo "$c=$(w "$O/cache_stageA_$c")"; done) \
  --out "$(w "$R/AV2_TRACKER_COUNTS_v02.json")" > "$LG/counts_v02.log" 2>&1
tail -n 6 "$LG/counts_v02.log"
echo "STAGE A ALL DONE $(date +%H:%M:%S)"; true
