#!/usr/bin/env bash
# AV2 outcome-free analysis queue (Claude line, v01, 1 Nov 2026): one process at a time, in the slot that
# run_av2_track_v02.sh leaves free (it runs at most 3 tracker processes). Steps:
#   1. nuScenes-only test of the horizon port (test_av2_horizon_on_nuscenes_v01.py);
#   2. nuScenes-only validation of av2_track_metrics_v01 against CANMOT's reference evaluation (T1 sc, T3 Poly-MOT, val);
#   3. per AV2 tracker x detector, as soon as its 4 workers have finished: counts (av2_counts_v01) and tracking metrics
#      (av2_track_metrics_v01); 4. merge of the counts into 60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json.
# Nothing here computes a residual or any outcome quantity on AV2 (design section 9).
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; T="$W/30_DATA/av2_trk_v01"; R="$W/60_RESULTS/av2_trk"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
mkdir -p "$R/metrics" "$R/counts_parts" "$R/horizon_nuscenes_test"
cd /c/Users/anand
while [ ! -f "$T/equiv/t1_native/x1_export_record.json" ] || [ ! -f "$T/equiv/t3_native/x1_export_record.json" ]; do sleep 20; done
echo "slot free $(date +%H:%M:%S)"
"$PY" -B "$(w "$S/test_av2_horizon_on_nuscenes_v01.py")" --out "$(w "$R/horizon_nuscenes_test")" > "$T/logs/horizon_nuscenes_test_v01.log" 2>&1
tail -n 1 "$T/logs/horizon_nuscenes_test_v01.log"; echo "horizon test done $(date +%H:%M:%S)"
NG="$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")"
REF="$W/50_CODE/third_party/CANMOT/reproducibility/reference"
"$PY" -I -B "$(w "$S/av2_track_metrics_v01.py")" --gt "$NG" --label "nuScenes val T1 (validation of the metric code)" \
  --exports $(for i in 0 1 2; do w "$W/60_RESULTS/x1_export_val150_fast_v04/worker$i"; done) \
  --check-reference "$(w "$REF/local_canmot_sc.json")" --out "$(w "$R/metrics/NUSC_VAL_T1_metric_validation_v01.json")" \
  > "$T/logs/metrics_nusc_t1_validation.log" 2>&1
tail -n 2 "$T/logs/metrics_nusc_t1_validation.log"; echo "nusc metric validation done $(date +%H:%M:%S)"
G="$(w "$T/gt/av2_val_gt_v01.json")"
for combo in t1_lt3d t3_lt3d t1_voxelnext t3_voxelnext t2_lt3d t2_voxelnext; do
  tr=${combo%%_*}; de=${combo#*_}
  while true; do n=0; for i in 0 1 2 3; do [ -f "$T/export/$combo/worker$i/x1_export_record.json" ] && n=$((n+1)); done; [ $n -eq 4 ] && break; sleep 30; done
  WK=$(for i in 0 1 2 3; do w "$T/export/$combo/worker$i"; done)
  "$PY" -I -B "$(w "$S/av2_counts_v01.py")" --gt "$G" --tracker $tr --detector $de --exports $WK \
    --out "$(w "$R/counts_parts/counts_$combo.json")" > "$T/logs/counts_$combo.log" 2>&1
  "$PY" -I -B "$(w "$S/av2_track_metrics_v01.py")" --gt "$G" --label "AV2 val $combo" --exports $WK \
    --out "$(w "$R/metrics/AV2_metrics_$combo.json")" > "$T/logs/metrics_$combo.log" 2>&1
  echo "$combo done $(date +%H:%M:%S)"
  "$PY" -I -B "$(w "$S/av2_counts_v01.py")" --merge $(for f in "$R"/counts_parts/counts_*.json; do w "$f"; done) \
    --out "$(w "$R/AV2_TRACKER_COUNTS_v01.json")" > "$T/logs/counts_merge.log" 2>&1
done
"$PY" -I -B "$(w "$S/av2_track_metrics_v01.py")" --gt "$NG" --label "nuScenes val T3 (validation of the metric code)" \
  --exports $(for i in 0 1 2; do w "$W/60_RESULTS/m_export_polymot_v01/val/worker$i"; done) \
  --check-reference "$(w "$REF/poly_mot.json")" --out "$(w "$R/metrics/NUSC_VAL_T3_metric_validation_v01.json")" \
  > "$T/logs/metrics_nusc_t3_validation.log" 2>&1
echo "ANALYSIS DONE $(date +%H:%M:%S)"
