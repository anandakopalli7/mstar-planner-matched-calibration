#!/usr/bin/env bash
# AV2 outcome-free analysis lane (Claude line, 2 Nov 2026); replaces the single queue run_av2_analysis_v04.sh (stopped on
# purpose after it had started the T1 x LT3D metrics, which kept running) so that several lanes can run once the tracker
# runs are over (never more than 4 processes in total). Usage:
#   bash run_av2_analysis_lane_v01.sh <file to wait for | none> <log to wait for "tracking done" in | none> <combo>...
# For each combo, as soon as its 4 workers have finished: counts (av2_counts_v01) unless present, then tracking metrics
# (av2_track_metrics_v03; car, pedestrian, bicycle = cyclist). Nothing here computes any outcome quantity on AV2.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; T="$W/30_DATA/av2_trk_v01"; R="$W/60_RESULTS/av2_trk"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1
cd /c/Users/anand
WAITF="$1"; WAITL="$2"; shift 2
[ "$WAITF" != none ] && while [ ! -f "$WAITF" ]; do sleep 20; done
[ "$WAITL" != none ] && while ! grep -q "tracking done" "$WAITL" 2>/dev/null; do sleep 20; done
G="$(w "$T/gt/av2_val_gt_v01.json")"
for combo in "$@"; do
  tr=${combo%%_*}; de=${combo#*_}
  while true; do n=0; for i in 0 1 2 3; do [ -f "$T/export/$combo/worker$i/x1_export_record.json" ] && n=$((n+1)); done; [ $n -eq 4 ] && break; sleep 30; done
  WK=$(for i in 0 1 2 3; do w "$T/export/$combo/worker$i"; done)
  if [ ! -f "$R/counts_parts/counts_$combo.json" ]; then
    "$PY" -I -B "$(w "$S/av2_counts_v01.py")" --gt "$G" --tracker $tr --detector $de --exports $WK \
      --out "$(w "$R/counts_parts/counts_$combo.json")" > "$T/logs/counts_$combo.log" 2>&1
    echo "$combo counts done $(date +%H:%M:%S)"
  fi
  "$PY" -I -B "$(w "$S/av2_track_metrics_v03.py")" --gt "$G" --label "AV2 val $combo" --exports $WK --classes car pedestrian bicycle \
    --out "$(w "$R/metrics/AV2_metrics_$combo.json")" > "$T/logs/metrics_$combo.log" 2>&1
  echo "$combo metrics done $(date +%H:%M:%S)"
done
echo "LANE DONE $(date +%H:%M:%S)"; true
