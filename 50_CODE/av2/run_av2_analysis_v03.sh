#!/usr/bin/env bash
# AV2 outcome-free analysis queue, v03 (Claude line, 1 Nov 2026). v02 was stopped during its first AV2 metrics run (the
# v01 metric code spent > 25 min on the car class); v03 uses av2_track_metrics_v02 (two exact speed-ups) and first
# re-validates it on nuScenes val against CANMOT's reference evaluation (bicycle, bus, car, pedestrian). Then, per AV2
# tracker x detector as soon as its 4 workers have finished: counts (if not yet done) and tracking metrics (car,
# pedestrian, bicycle = cyclist); merge of the counts. One process at a time (the tracker driver uses at most 3).
# Nothing here computes a residual or any outcome quantity on AV2 (design section 9).
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; T="$W/30_DATA/av2_trk_v01"; R="$W/60_RESULTS/av2_trk"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
cd /c/Users/anand
REF="$W/50_CODE/third_party/CANMOT/reproducibility/reference"
"$PY" -I -B "$(w "$S/av2_track_metrics_v02.py")" --gt "$(w "$W/30_DATA/x1_gt/x1_val_gt_v02.json")" \
  --label "nuScenes val T1 (validation of av2_track_metrics_v02)" --classes bicycle bus car pedestrian \
  --exports $(for i in 0 1 2; do w "$W/60_RESULTS/x1_export_val150_fast_v04/worker$i"; done) \
  --check-reference "$(w "$REF/local_canmot_sc.json")" --out "$(w "$R/metrics/NUSC_VAL_T1_metric_validation_v02.json")" \
  > "$T/logs/metrics_nusc_t1_validation_v02.log" 2>&1
echo "nusc metric v02 validation done $(date +%H:%M:%S)"
G="$(w "$T/gt/av2_val_gt_v01.json")"
for combo in t1_lt3d t1_voxelnext t3_lt3d t3_voxelnext t2_lt3d t2_voxelnext; do
  tr=${combo%%_*}; de=${combo#*_}
  while true; do n=0; for i in 0 1 2 3; do [ -f "$T/export/$combo/worker$i/x1_export_record.json" ] && n=$((n+1)); done; [ $n -eq 4 ] && break; sleep 30; done
  WK=$(for i in 0 1 2 3; do w "$T/export/$combo/worker$i"; done)
  if [ ! -f "$R/counts_parts/counts_$combo.json" ]; then
    "$PY" -I -B "$(w "$S/av2_counts_v01.py")" --gt "$G" --tracker $tr --detector $de --exports $WK \
      --out "$(w "$R/counts_parts/counts_$combo.json")" > "$T/logs/counts_$combo.log" 2>&1
    "$PY" -I -B "$(w "$S/av2_counts_v01.py")" --merge $(for f in "$R"/counts_parts/counts_*.json; do w "$f"; done) \
      --out "$(w "$R/AV2_TRACKER_COUNTS_v01.json")" > "$T/logs/counts_merge.log" 2>&1
    echo "$combo counts done $(date +%H:%M:%S)"
  fi
  "$PY" -I -B "$(w "$S/av2_track_metrics_v02.py")" --gt "$G" --label "AV2 val $combo" --exports $WK --classes car pedestrian bicycle \
    --out "$(w "$R/metrics/AV2_metrics_$combo.json")" > "$T/logs/metrics_$combo.log" 2>&1
  echo "$combo metrics done $(date +%H:%M:%S)"
done
echo "ANALYSIS DONE $(date +%H:%M:%S)"
