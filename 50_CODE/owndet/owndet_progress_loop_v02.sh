#!/usr/bin/env bash
# owndet_progress_loop_v02.sh (own-detector job, 4 Nov 2026) = v01 with the work dir and the final iteration read from the connection file
# 80_LOGS/runpod/owndet_pod_conn_v02.txt (host port pod_id start_epoch price work_dir final_iter), for the capped resume (ADDENDUM_B).
# owndet_progress_loop_v01.sh: the laptop side of the real-time saving rule (researcher, 4 Nov 2026;
# OWN_DETECTOR_DESIGN_ADDENDUM_A_v01.md A2). Every INTERVAL seconds (default 9000 = 2.5 h) it copies from the pod the latest training
# checkpoint (iter_*.pth, the newest two kept), the mmcv training logs and a progress line into 30_DATA/av2_det_owncp_v01/train_progress/,
# and appends a progress line to 80_LOGS/runpod/SPEND_LOG_OWNDET_v01.md. Pod connection: 80_LOGS/runpod/owndet_pod_conn_v01.txt
# (host port pod_id start_epoch price_per_h; one line, re-read every round). Light: ssh/scp only. Never uses the RunPod API key.
# Ends after copying the final checkpoint (iter_57838.pth) or when train_progress/STOP_PROGRESS_LOOP exists. Every ssh/scp has a timeout.
W="/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
OUT="$W/30_DATA/av2_det_owncp_v01/train_progress"
CONN="$W/80_LOGS/runpod/owndet_pod_conn_v02.txt"
SPEND="$W/80_LOGS/runpod/SPEND_LOG_OWNDET_v01.md"
K=~/.ssh/programme_a_runpod_20261030_ed25519
INTERVAL=${INTERVAL:-9000}
mkdir -p "$OUT"
echo "$(date '+%F %T %Z') progress loop v02 started, interval ${INTERVAL}s" >> "$OUT/progress_v01.txt"
while true; do
  [ -f "$OUT/STOP_PROGRESS_LOOP" ] && { echo "$(date '+%F %T %Z') stop file found; loop ends" >> "$OUT/progress_v01.txt"; exit 0; }
  read -r HOST PORT POD START PRICE WD FINAL < "$CONN"
  O="-i $K -p $PORT -o BatchMode=yes -o ConnectTimeout=20 -o StrictHostKeyChecking=accept-new"
  INFO=$(timeout 60 ssh $O root@$HOST "L=\$(ls $WD/iter_*.pth 2>/dev/null | sed 's/.*iter_\([0-9]*\)\.pth/\1/' | sort -n | tail -n 1); J=\$(ls -t $WD/*.log.json 2>/dev/null | head -n 1); T=\$(ls -t $WD/*.log 2>/dev/null | head -n 1); LAST=\$(tail -n 1 \"\$J\" 2>/dev/null | tr -d '\n' | cut -c1-300); echo \"\$L|\$J|\$T|\$LAST\"" 2>/dev/null)
  NOW=$(date +%s); H=$(awk -v n=$NOW -v s=$START 'BEGIN {printf "%.2f", (n - s) / 3600}'); COST=$(awk -v h=$H -v p=$PRICE 'BEGIN {printf "%.2f", h * p}')
  if [ -z "$INFO" ]; then
    echo "$(date '+%F %T %Z') pod unreachable ($HOST:$PORT); pod time ${H} h, cost so far about \$${COST}" >> "$OUT/progress_v01.txt"
    echo "| $(date '+%F %T %Z') | (progress loop) pod unreachable; pod time ${H} h ≈ \$${COST} | $POD | | $PRICE |" >> "$SPEND"
  else
    IFS='|' read -r LITER JS TX LASTLINE <<< "$INFO"
    if [ -n "$LITER" ] && [ ! -s "$OUT/iter_${LITER}.pth" ]; then
      timeout 3000 scp -P $PORT -i $K -o BatchMode=yes -o ConnectTimeout=20 -q root@$HOST:$WD/iter_${LITER}.pth "$OUT/iter_${LITER}.pth.part" && mv "$OUT/iter_${LITER}.pth.part" "$OUT/iter_${LITER}.pth"
      ls "$OUT"/iter_*.pth 2>/dev/null | sed 's/.*iter_\([0-9]*\)\.pth/\1/' | sort -n | head -n -2 | while read -r old; do rm -f "$OUT/iter_${old}.pth"; done
    fi
    [ -n "$JS" ] && timeout 600 scp -P $PORT -i $K -o BatchMode=yes -q root@$HOST:"$JS" "$OUT/train_log.json" 2>/dev/null
    [ -n "$TX" ] && timeout 600 scp -P $PORT -i $K -o BatchMode=yes -q root@$HOST:"$TX" "$OUT/train_log.txt" 2>/dev/null
    (cd "$OUT" && ls iter_*.pth train_log.* 2>/dev/null | xargs -r sha256sum > SHA256SUMS_latest.txt)
    echo "$(date '+%F %T %Z') latest checkpoint iter ${LITER:-none}; last log line: ${LASTLINE}; pod time ${H} h, cost so far about \$${COST}" >> "$OUT/progress_v01.txt"
    echo "| $(date '+%F %T %Z') | (progress loop) checkpoint iter ${LITER:-none} of $FINAL copied to \`30_DATA/av2_det_owncp_v01/train_progress/\`; pod time ${H} h ≈ \$${COST} | $POD | | $PRICE |" >> "$SPEND"
    [ "$LITER" = "$FINAL" ] && [ -s "$OUT/iter_${FINAL}.pth" ] && { echo "$(date '+%F %T %Z') final checkpoint copied; loop ends" >> "$OUT/progress_v01.txt"; exit 0; }
  fi
  sleep "$INTERVAL"
done
