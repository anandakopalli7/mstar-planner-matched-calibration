#!/usr/bin/env bash
# AV2 C1 375-log tracker step, production queue (Claude line, v01, 5 Nov 2026; AV2_TRACKER_PORT_DESIGN_v04.md sections 7, 8,
# 12). Resumable: a job whose output exists (and verifies) is skipped; the tracker jobs resume per log from their checkpoints;
# single-file outputs are written under a .partial name and renamed only on success. At most LIMIT processes at a time, of
# which at most HEAVY memory-heavy (GT prep, ego, metrics, HOTA). A job that fails twice is left FAILED and reported.
# Stops everything when C: has less than 8 GB free. Nothing here computes an outcome; no stage A, no counts.
# A job starts only after its tool's equivalence test (60_RESULTS/av2_trk/c1_375/equiv/) has passed. The file
# 30_DATA/av2_trk_v02/QUEUE_LIMIT ("LIMIT HEAVY"), when present, overrides the limits at every loop.
# Usage: bash run_av2_c1_queue_v01.sh [LIMIT] [HEAVY]
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"; PYA="$W/50_CODE/env/av2eval310/Scripts/python.exe"; PYB="$W/50_CODE/env/ab3dmot310/Scripts/python.exe"
S="$W/50_CODE/av2"; T="$W/30_DATA/av2_trk_v02"; R="$W/60_RESULTS/av2_trk/c1_375"; LG="$T/logs"
LOGS="$T/C1_LOGS_375_v01.json"; GT="$T/gt/av2_c1_gt375_v01.json"; EGO="$T/ego/av2_c1_ego10hz_v01.json.gz"
LIMIT=${1:-3}; HEAVY=${2:-2}
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1 NUMBA_NUM_THREADS=1 NUMBA_CACHE_DIR="$(w "$T/numba_cache")"
mkdir -p "$LG" "$T/gt" "$T/ego" "$T/horizon" "$T/export" "$R/metrics" "$R/hota"
cd /c/Users/anand
declare -A EXP=([t1]=paper/local/canmot/sc [t3]=paper/baseline/poly_mot)
declare -a NAMES; declare -A KIND PIDS FAILS
add() { NAMES+=("$1"); KIND[$1]=$2; FAILS[$1]=0; }

# ---------------------------------------------------------------- done / ready tests
rec_pass() { [ -f "$1/x1_export_record.json" ] && grep -q '"status_X1_gates": "PASS"' "$1/x1_export_record.json"; }
done_job() { local n=$1
  case $n in
    input) [ -f "$T/input/owncp/receipt.json" ] ;;
    gt) [ -f "$GT" ] ;;
    ego) [ -f "$EGO" ] ;;
    t1_w*|t3_w*) rec_pass "$T/export/${n%%_w*}_owncp/worker${n##*_w}" ;;
    tab_w*) local i=${n##*_w}; [ -f "$T/export_tab_owncp/ab3dmot_det/worker$i/x1_export_record.json" ] && [ -f "$T/export_tab_owncp/ab3dmot_kf/worker$i/x1_export_record.json" ] ;;
    prop_*) [ -f "$T/horizon/horizon8_${n#prop_}_owncp.jsonl.gz" ] ;;
    m_*) [ -f "$R/metrics/AV2_C1_metrics_${n#m_}.json" ] ;;
    h_*) [ -f "$R/hota/AV2_C1_HOTA_${n#h_}.json" ] ;;
  esac; }
all_done() { local p=$1 k=$2 i; for i in $(seq 0 $((k-1))); do done_job ${p}_w$i || return 1; done; }
E="$R/equiv"
eq() { [ -f "$E/$1" ] && tail -n 2 "$E/$1" | grep -q '"identical": true'; }    # a passed equivalence test (design v04 section 10)
eq_gt() { [ -f "$E/EQUIV_gt_prep_v02_record.txt" ] && [ "$(grep -c 'identical true' "$E/EQUIV_gt_prep_v02_record.txt")" -eq 2 ]; }
ready_job() { local n=$1
  case $n in
    input) eq EQUIV_tracker_input_v02.json ;;
    gt) eq_gt ;;
    tab_w*) eq EQUIV_ab3dmot_v05_w1.json ;;
    ego) done_job gt && eq EQUIV_ego_prep_v02.json ;;
    t1_w*|t3_w*) done_job input && eq EQUIV_track_v02_t1_lt3d_w3.json && eq EQUIV_track_v02_t3_lt3d_w1.json ;;
    prop_t1) all_done t1 8 && eq EQUIV_horizon_prep_v02_t1_lt3d_w0.json ;;
    prop_t3) all_done t3 8 && eq EQUIV_horizon_prep_v02_t3_lt3d_w0.json ;;
    prop_tab) all_done tab 6 ;;
    m_*|h_*) local x=${n#?_}; x=${x%_*}; x=${x%_*}
      case $n in m_*) eq EQUIV_track_metrics_v04_t3_voxelnext.json || return 1 ;; h_*) eq EQUIV_hota_v04_t3_voxelnext.json || return 1 ;; esac
      done_job gt && case $x in t1) all_done t1 8 ;; t3) all_done t3 8 ;; tab*) all_done tab 6 ;; esac ;;
  esac; }

# ---------------------------------------------------------------- job bodies
exports_of() { case $1 in t1|t3) for i in 0 1 2 3 4 5 6 7; do w "$T/export/$1_owncp/worker$i"; done ;;
                        tab_kf|tab_det) for i in 0 1 2 3 4 5; do w "$T/export_tab_owncp/ab3dmot_${1#tab_}/worker$i"; done ;; esac; }
run_job() { local n=$1
  case $n in
    input)
      [ -d "$T/input/owncp" ] && [ ! -f "$T/input/owncp/receipt.json" ] && rm -rf "$T/input/owncp"
      "$PY" -I -B "$(w "$S/av2_tracker_input_v02.py")" --detector owncp --logs-file "$(w "$LOGS")" --workers 8 --out "$(w "$T/input/owncp")" ;;
    gt)
      rm -f "$GT.partial"
      "$PY" -I -B "$(w "$S/av2_gt_prep_v02.py")" --logs-file "$(w "$LOGS")" --out "$(w "$GT.partial")" && mv "$GT.partial" "$GT" ;;
    ego)
      rm -f "$EGO.partial"
      "$PY" -I -B "$(w "$S/av2_ego_prep_v02.py")" --gt "$(w "$GT")" --out "$(w "$EGO.partial")" && mv "$EGO.partial" "$EGO" ;;
    t1_w*|t3_w*)
      local tr=${n%%_w*} i=${n##*_w}
      "$PY" -I -B "$(w "$S/av2_track_v02.py")" --experiment ${EXP[$tr]} --detector owncp --receipt "$(w "$T/input/owncp/receipt.json")" \
        --worker $i --fast-convex --out "$(w "$T/export/${tr}_owncp/worker$i")" ;;
    tab_w*)
      "$PYB" -I -B "$(w "$S/av2_ab3dmot_v05.py")" --detector owncp --logs-file "$(w "$LOGS")" --fast --worker ${n##*_w} --n-workers 6 \
        --out "$(w "$T/export_tab_owncp")" ;;
    prop_t1|prop_t3)
      local tr=${n#prop_} H="$T/horizon/horizon8_${n#prop_}_owncp.jsonl.gz"
      rm -f "$H.partial"
      "$PY" -I -B "$(w "$S/av2_horizon_prep_v02.py")" --experiment ${EXP[$tr]} --propagate-only --allow-av2-propagation \
        --workers $(exports_of $tr) --out "$(w "$H.partial")" && mv "$H.partial" "$H" ;;
    prop_tab)
      local H="$T/horizon/horizon8_tab_owncp.jsonl.gz"
      rm -f "$H.partial"
      "$PY" -I -B -c "
import gzip, sys
with gzip.open(sys.argv[1], 'wt') as fo:
    for p in sys.argv[2:]:
        with gzip.open(p, 'rt') as f:
            for line in f:
                fo.write(line)
print('merged', len(sys.argv) - 2, 'worker files')
" "$(w "$H.partial")" $(for i in 0 1 2 3 4 5; do w "$T/export_tab_owncp/horizon8_ab3dmot_kf_worker$i.jsonl.gz"; done) && mv "$H.partial" "$H" ;;
    m_*)
      local x=${n#m_} tr part key; part=${x##*_}; tr=${x%_*}
      key=$(case $part in val150) echo val_150 ;; held225) echo held_out_225 ;; pooled) echo logs ;; esac)
      "$PY" -I -B "$(w "$S/av2_track_metrics_v04.py")" --gt "$(w "$GT")" --label "AV2 C1 375 $tr owncp $part" --exports $(exports_of $tr) \
        --classes car pedestrian bicycle --logs-file "$(w "$LOGS")" --logs-key $key --out "$(w "$R/metrics/AV2_C1_metrics_$x.json")" ;;
    h_*)
      local x=${n#h_} tr part key; part=${x##*_}; tr=${x%_*}
      key=$(case $part in val150) echo val_150 ;; held225) echo held_out_225 ;; pooled) echo logs ;; esac)
      "$PYA" -I -B "$(w "$S/av2_hota_v04.py")" --gt "$(w "$GT")" --exports $(exports_of $tr) --label "c1_$x" \
        --logs-file "$(w "$LOGS")" --logs-key $key --out "$(w "$R/hota/AV2_C1_HOTA_$x.json")" ;;
  esac; }

# ---------------------------------------------------------------- the job list (priority order)
add input light; add gt heavy
for i in 0 1 2 3 4 5 6 7; do add t1_w$i light; add t3_w$i light; [ $i -lt 6 ] && add tab_w$i light; done
add ego heavy; add prop_t1 light; add prop_t3 light; add prop_tab light
for tr in t1 t3 tab_kf tab_det; do for part in val150 held225 pooled; do add h_${tr}_$part heavy; add m_${tr}_$part heavy; done; done

echo "queue v01 start $(date +%H:%M:%S) LIMIT=$LIMIT HEAVY=$HEAVY jobs=${#NAMES[@]}"
while true; do
  [ -f "$T/QUEUE_LIMIT" ] && read LIMIT HEAVY < "$T/QUEUE_LIMIT"    # concurrency can be changed while the queue runs
  free=$(df -k /c | tail -n 1 | awk '{print $4}')
  if [ "$free" -lt $((8*1024*1024)) ]; then echo "DISK BELOW 8 GB ($free kB): stopping queue $(date +%H:%M:%S)"; for n in "${NAMES[@]}"; do [ -n "${PIDS[$n]}" ] && kill ${PIDS[$n]} 2>/dev/null; done; exit 2; fi
  pending=0; running=0; heavy=0
  for n in "${NAMES[@]}"; do
    if [ -n "${PIDS[$n]}" ]; then
      if kill -0 ${PIDS[$n]} 2>/dev/null; then running=$((running+1)); [ ${KIND[$n]} = heavy ] && heavy=$((heavy+1)); continue; fi
      wait ${PIDS[$n]} 2>/dev/null; PIDS[$n]=""
      if done_job $n; then echo "done $n $(date +%H:%M:%S)"; else FAILS[$n]=$((FAILS[$n]+1)); echo "ended without output: $n (failure ${FAILS[$n]}) $(date +%H:%M:%S)"; fi
    fi
  done
  for n in "${NAMES[@]}"; do
    done_job $n && continue
    [ ${FAILS[$n]} -ge 2 ] && continue
    pending=$((pending+1))
    [ -n "${PIDS[$n]}" ] && continue
    [ $running -ge $LIMIT ] && continue
    [ ${KIND[$n]} = heavy ] && [ $heavy -ge $HEAVY ] && continue
    ready_job $n || continue
    run_job $n > "$LG/q_$n.log" 2>&1 &
    PIDS[$n]=$!; running=$((running+1)); [ ${KIND[$n]} = heavy ] && heavy=$((heavy+1))
    echo "start $n pid ${PIDS[$n]} $(date +%H:%M:%S)"
  done
  if [ $pending -eq 0 ] && [ $running -eq 0 ]; then break; fi
  sleep 30
done
for n in "${NAMES[@]}"; do done_job $n || echo "NOT DONE: $n (failures ${FAILS[$n]})"; done
echo "QUEUE V01 DONE $(date +%H:%M:%S)"; true
