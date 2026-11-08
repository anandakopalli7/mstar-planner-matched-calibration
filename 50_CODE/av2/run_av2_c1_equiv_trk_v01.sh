#!/usr/bin/env bash
# AV2 port v04 equivalence tests for the tracker-side tools (Claude line, v01, 5 Nov 2026; design v04 section 10), on the 150
# val logs with the public LT3D detections; all test outputs go to <scratch tmp dir> and are deleted after the comparison.
#   1. av2_tracker_input_v02 --detector lt3d --workers 4 vs 30_DATA/av2_trk_v01/input/lt3d
#   2. av2_track_v02 T1 worker 3 (stopped on purpose after 5 logs by --test-stop-after, then resumed) and T3 worker 1, both on
#      the v01 receipt with --fast-convex, vs 30_DATA/av2_trk_v01/export/{t1,t3}_lt3d/worker{3,1}
#   3. av2_ab3dmot_v05 --detector lt3d --fast --worker 1 --n-workers 6 (stopped on purpose after 3 logs, then resumed) vs
#      30_DATA/av2_trk_v01/export_ab3dmot_v04w6 worker 1
#   4. av2_horizon_prep_v02 on the v01 T1 / T3 LT3D worker 0 exports vs the first n lines of horizon8_{t1,t3}_lt3d.jsonl.gz
#   5. av2_track_metrics_v04 and av2_hota_v04 with --logs-file = the 150 val logs on the v01 T3 VoxelNeXt exports and the v01
#      GT file vs 60_RESULTS/av2_trk/metrics/AV2_metrics_t3_voxelnext.json and hota/AV2_HOTA_t3_voxelnext.json
# At most 2 processes at a time. Nothing here computes an outcome.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"; PYA="$W/50_CODE/env/av2eval310/Scripts/python.exe"; PYB="$W/50_CODE/env/ab3dmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; E="$W/60_RESULTS/av2_trk/c1_375/equiv"; T1="$W/30_DATA/av2_trk_v01"; R1="$W/60_RESULTS/av2_trk"
TMP="$1"; mkdir -p "$TMP" "$E"
TST="$(w "$S/test_av2_port_v04_equiv_v01.py")"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR="$(w "$TMP/numba_cache")"
cd /c/Users/anand
STEP="${2:-all}"
if [ "$STEP" = all ] || [ "$STEP" = adapter ]; then
  echo "1 adapter start $(date +%H:%M:%S)"
  "$PY" -I -B "$(w "$S/av2_tracker_input_v02.py")" --detector lt3d --workers 4 --out "$(w "$TMP/adapter_lt3d")" > "$TMP/adapter_lt3d.log" 2>&1
  "$PY" -I -B "$TST" adapter --test "$(w "$TMP/adapter_lt3d")" --ref "$(w "$T1/input/lt3d")" --out "$(w "$E/EQUIV_tracker_input_v02.json")"
  rm -rf "$TMP/adapter_lt3d"; echo "adapter test copy deleted $(date +%H:%M:%S)"
fi
if [ "$STEP" = all ] || [ "$STEP" = track ]; then
  echo "2 track start $(date +%H:%M:%S)"
  RC="$(w "$T1/input/lt3d/receipt.json")"
  ( "$PY" -I -B "$(w "$S/av2_track_v02.py")" --experiment paper/local/canmot/sc --detector lt3d --receipt "$RC" --worker 3 --fast-convex \
      --out "$(w "$TMP/t1_w3")" --test-stop-after 5 > "$TMP/t1_w3_part1.log" 2>&1
    echo "t1 w3 first process exit $? (3 = stopped on purpose) $(date +%H:%M:%S)"
    "$PY" -I -B "$(w "$S/av2_track_v02.py")" --experiment paper/local/canmot/sc --detector lt3d --receipt "$RC" --worker 3 --fast-convex \
      --out "$(w "$TMP/t1_w3")" > "$TMP/t1_w3_part2.log" 2>&1
    "$PY" -I -B "$TST" export --test "$(w "$TMP/t1_w3")" --ref "$(w "$T1/export/t1_lt3d/worker3")" --out "$(w "$E/EQUIV_track_v02_t1_lt3d_w3.json")" --expect-reused 5 ) &
  ( "$PY" -I -B "$(w "$S/av2_track_v02.py")" --experiment paper/baseline/poly_mot --detector lt3d --receipt "$RC" --worker 1 --fast-convex \
      --out "$(w "$TMP/t3_w1")" > "$TMP/t3_w1.log" 2>&1
    "$PY" -I -B "$TST" export --test "$(w "$TMP/t3_w1")" --ref "$(w "$T1/export/t3_lt3d/worker1")" --out "$(w "$E/EQUIV_track_v02_t3_lt3d_w1.json")" --expect-reused 0 ) &
  wait
  rm -rf "$TMP/t1_w3" "$TMP/t3_w1"; echo "track test copies deleted $(date +%H:%M:%S)"
fi
if [ "$STEP" = all ] || [ "$STEP" = ab3dmot ]; then
  echo "3 ab3dmot start $(date +%H:%M:%S)"
  "$PYB" -I -B "$(w "$S/av2_ab3dmot_v05.py")" --detector lt3d --fast --worker 1 --n-workers 6 --out "$(w "$TMP/ab")" --test-stop-after 3 > "$TMP/ab_part1.log" 2>&1
  echo "ab3dmot first process exit $? (3 = stopped on purpose) $(date +%H:%M:%S)"
  "$PYB" -I -B "$(w "$S/av2_ab3dmot_v05.py")" --detector lt3d --fast --worker 1 --n-workers 6 --out "$(w "$TMP/ab")" > "$TMP/ab_part2.log" 2>&1
  "$PY" -I -B "$TST" ab3dmot --test "$(w "$TMP/ab")" --ref "$(w "$T1/export_ab3dmot_v04w6")" --worker 1 --out "$(w "$E/EQUIV_ab3dmot_v05_w1.json")" --expect-reused 3
  rm -rf "$TMP/ab"; echo "ab3dmot test copy deleted $(date +%H:%M:%S)"
fi
if [ "$STEP" = all ] || [ "$STEP" = horizon ]; then
  echo "4 horizon start $(date +%H:%M:%S)"
  declare -A EXP=([t1]=paper/local/canmot/sc [t3]=paper/baseline/poly_mot)
  for tr in t1 t3; do
    N=$("$PY" -I -B -c "import json,sys; print(json.load(open(sys.argv[1]))['stats']['tracks'])" "$(w "$T1/export/${tr}_lt3d/worker0/x1_export_record.json")")
    "$PY" -I -B "$(w "$S/av2_horizon_prep_v02.py")" --experiment ${EXP[$tr]} --propagate-only --allow-av2-propagation \
      --workers "$(w "$T1/export/${tr}_lt3d/worker0")" --out "$(w "$TMP/h_$tr.jsonl.gz")" > "$TMP/h_$tr.log" 2>&1
    "$PY" -I -B "$TST" horizon_prefix --test "$(w "$TMP/h_$tr.jsonl.gz")" --ref "$(w "$W/30_DATA/av2_cache_stageA_v01/horizon8_${tr}_lt3d.jsonl.gz")" --n $N \
      --out "$(w "$E/EQUIV_horizon_prep_v02_${tr}_lt3d_w0.json")"
    rm -f "$TMP/h_$tr.jsonl.gz"
  done
  # guard: v02 must refuse an AV2 export without --allow-av2-propagation (writes nothing)
  "$PY" -I -B "$(w "$S/av2_horizon_prep_v02.py")" --experiment paper/local/canmot/sc --propagate-only \
    --workers "$(w "$T1/export/t1_lt3d/worker0")" --out "$(w "$TMP/h_guard.jsonl.gz")" > "$TMP/h_guard.log" 2>&1
  echo "horizon guard exit $? ($(tail -n 1 "$TMP/h_guard.log")); output exists: $([ -e "$TMP/h_guard.jsonl.gz" ] && echo yes || echo no)"
fi
if [ "$STEP" = all ] || [ "$STEP" = metrics ]; then
  echo "5 metrics start $(date +%H:%M:%S)"
  "$PY" -I -B -c "import json,sys; sys.path.insert(0, sys.argv[2]); import av2_common_v02 as C; json.dump(C.val_logs(), open(sys.argv[1], 'w'))" "$(w "$TMP/val150_list.json")" "$(w "$S")"
  GT="$(w "$T1/gt/av2_val_gt_v01.json")"; WK=$(for i in 0 1 2 3; do w "$T1/export/t3_voxelnext/worker$i"; done)
  ( "$PY" -I -B "$(w "$S/av2_track_metrics_v04.py")" --gt "$GT" --label "AV2 val t3_voxelnext" --exports $WK --classes car pedestrian bicycle \
      --logs-file "$(w "$TMP/val150_list.json")" --out "$(w "$TMP/m_t3vx.json")" > "$TMP/m_t3vx.log" 2>&1
    "$PY" -I -B "$TST" metrics --test "$(w "$TMP/m_t3vx.json")" --ref "$(w "$R1/metrics/AV2_metrics_t3_voxelnext.json")" --out "$(w "$E/EQUIV_track_metrics_v04_t3_voxelnext.json")" ) &
  ( "$PYA" -I -B "$(w "$S/av2_hota_v04.py")" --gt "$GT" --exports $WK --label t3_voxelnext --logs-file "$(w "$TMP/val150_list.json")" \
      --out "$(w "$TMP/hota/h_t3vx.json")" > "$TMP/h_t3vx.log" 2>&1
    "$PY" -I -B "$TST" hota --test "$(w "$TMP/hota/h_t3vx.json")" --ref "$(w "$R1/hota/AV2_HOTA_t3_voxelnext.json")" --out "$(w "$E/EQUIV_hota_v04_t3_voxelnext.json")" ) &
  wait
fi
echo "EQUIV TRK DONE $(date +%H:%M:%S)"; true
