#!/usr/bin/env bash
# run_tpp_v01.sh: TPP arm phase 1 (outcome-blind) on the 150 nuScenes val scenes, trackers T1 and T3.
# Waits until the newest 80_LOGS/k8_expl_v02_*.log prints "K8 exploratory run v02 end" (the K8 run owns the CPU until
# then), then runs with at most 2 worker processes: join keys (canmot310), Trajectron++ int_ee on tracker and on
# ground-truth histories (tpp38, python -I), counts and integrity checks, and the three test suites.
# No exceedance / coverage / NEES / calibration quantity is computed on real data here.
# Usage: bash run_tpp_v01.sh [deadline_epoch_seconds]
set -uo pipefail
W="C:/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
WB="/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
DEADLINE=${1:-0}
PYC="$W/50_CODE/env/canmot310/Scripts/python.exe"
PYT="$W/50_CODE/env/tpp38/Scripts/python.exe"
TPP="$W/50_CODE/third_party/Trajectron-plus-plus_eccv2020"
CODE="$W/50_CODE/tpp"
OUT="$W/30_DATA/tpp_v01"
TST="$W/70_TESTS/tpp_v01"
mkdir -p "$WB/30_DATA/tpp_v01" "$WB/70_TESTS/tpp_v01"
echo "TPP v01 chain start $(date '+%F %T %Z'); waiting for the K8 end line"
while true; do
  LOG=$(ls -t "$WB"/80_LOGS/k8_expl_v02_*.log 2>/dev/null | head -n 1)
  if [ -n "$LOG" ] && grep -q "K8 exploratory run v02 end" "$LOG"; then echo "K8 end line found in $LOG at $(date '+%F %T %Z')"; break; fi
  if [ "$DEADLINE" -gt 0 ] && [ "$(date +%s)" -gt "$DEADLINE" ]; then echo "DEADLINE reached without the K8 end line; nothing run"; exit 3; fi
  sleep 120
done
sha256sum "$WB"/50_CODE/tpp/*.py "$WB"/50_CODE/tpp/tests/*.py "$WB"/50_CODE/tpp/run_tpp_v01.sh
cd "$WB/50_CODE/tpp"
for t in t1 t3; do
  echo "keys $t start $(date '+%F %T')"
  "$PYC" -I -B "$CODE/tpp_keys_v01.py" --cache "$W/30_DATA/k6/cache_v02_${t}_val" --out "$OUT/keys_${t}_val_v01.npz" --workers 2 | tail -n 2
done
for t in t1 t3; do
  for s in trk gt; do
    echo "run $t $s start $(date '+%F %T')"
    "$PYT" -I -B "$CODE/tpp_run_v01.py" --tpp-root "$TPP" --model int_ee --keys "$OUT/keys_${t}_val_v01.npz" --source $s \
      --out "$OUT/tpp_int_ee_${t}_${s}_val_v01.npz" --workers 2 --threads 1 | grep -E "scenes (25|50|75|100|125|150)/|DONE|Error|error" | cut -c1-300
  done
done
echo "counts start $(date '+%F %T')"
"$PYT" -I -B "$CODE/tpp_counts_v01.py" --set t1 "$OUT/keys_t1_val_v01.npz" "$OUT/tpp_int_ee_t1_trk_val_v01.npz" "$OUT/tpp_int_ee_t1_gt_val_v01.npz" \
  --set t3 "$OUT/keys_t3_val_v01.npz" "$OUT/tpp_int_ee_t3_trk_val_v01.npz" "$OUT/tpp_int_ee_t3_gt_val_v01.npz" --out "$OUT/tpp_counts_v01.json" | tail -n 1
echo "tests start $(date '+%F %T')"
for t in t1 t3; do
  "$PYC" -I -B "$CODE/tests/test_tpp_keys_v01.py" --keys "$OUT/keys_${t}_val_v01.npz" --out "$TST/test_tpp_keys_v01_${t}.json" | grep -E "PASS|FAIL" | cut -c1-200
done
"$PYT" -I -B "$CODE/tests/test_tpp_run_v01.py" --tpp-root "$TPP" --out "$TST/test_tpp_run_v01.json" --keys "$OUT/keys_t1_val_v01.npz" \
  --runs "$OUT/tpp_int_ee_t1_trk_val_v01.npz" "$OUT/tpp_int_ee_t1_gt_val_v01.npz" | grep -E "PASS|FAIL" | cut -c1-200
"$PYT" -I -B "$CODE/tests/test_tpp_run_v01.py" --tpp-root "$TPP" --out "$TST/test_tpp_run_v01_t3join.json" --keys "$OUT/keys_t3_val_v01.npz" \
  --runs "$OUT/tpp_int_ee_t3_trk_val_v01.npz" "$OUT/tpp_int_ee_t3_gt_val_v01.npz" | grep -E "R9|ALL_PASS|SOME_FAIL" | cut -c1-200
"$PYC" -I -B "$CODE/tests/test_tpp_analyse_v01.py" --out "$TST/test_tpp_analyse_v01_synthetic.json" | grep -E "PASS|FAIL" | cut -c1-200
sha256sum "$WB"/30_DATA/tpp_v01/*.npz
echo "TPP v01 chain end $(date '+%F %T %Z')"
