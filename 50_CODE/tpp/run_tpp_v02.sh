#!/usr/bin/env bash
# run_tpp_v02.sh: TPP arm production on the laptop (Windows, tpp38) - the ONE production platform (lead, 2 Nov).
# v02 = v01 without the wait: workers = 2 while the K8 resume runs, 6 once the newest 80_LOGS/k8_expl_v02_resume*.log
# prints "K8 resume v01 end" (checked before each step). Order: keys T1, T3; int_ee on tracker and ground-truth histories
# (seed 20261102, D17); counts; tests K1-K4 and R9; SHA256SUMS of the production files; then the pre-registered seed
# sensitivity (tracker histories, seeds 20261104 and 20261105, T1 and T3) and its own SHA256SUMS.
# Outcome-blind: counts and integrity checks only.
set -uo pipefail
W="C:/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
WB="/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
PYC="$W/50_CODE/env/canmot310/Scripts/python.exe"
PYT="$W/50_CODE/env/tpp38/Scripts/python.exe"
TPP="$W/50_CODE/third_party/Trajectron-plus-plus_eccv2020"
OUT="$W/30_DATA/tpp_v01"
TST="$W/70_TESTS/tpp_v01"
mkdir -p "$WB/30_DATA/tpp_v01" "$WB/70_TESTS/tpp_v01"
nw() { local L; L=$(ls -t "$WB"/80_LOGS/k8_expl_v02_resume*.log 2>/dev/null | head -n 1)
       if [ -n "$L" ] && grep -q "K8 resume v01 end" "$L"; then echo 6; else echo 2; fi; }
echo "TPP v02 production start $(date '+%F %T %Z')"
cd "$WB/50_CODE/tpp"
sha256sum *.py tests/*.py run_tpp_v02.sh
for t in t1 t3; do
  echo "keys $t start $(date '+%F %T') workers $(nw)"
  "$PYC" -I -B tpp_keys_v01.py --cache "$W/30_DATA/k6/cache_v02_${t}_val" --out "$OUT/keys_${t}_val_v01.npz" --workers "$(nw)" | tail -n 1 | cut -c1-300
done
for t in t1 t3; do
  for s in trk gt; do
    N=$(nw); echo "run $t $s start $(date '+%F %T') workers $N"
    "$PYT" -I -B tpp_run_v01.py --tpp-root "$TPP" --model int_ee --keys "$OUT/keys_${t}_val_v01.npz" --source $s \
      --out "$OUT/tpp_int_ee_${t}_${s}_val_v01.npz" --workers "$N" --threads 1 | grep -E "scenes (50|100|150)/|DONE|rror" | cut -c1-200
  done
done
echo "counts start $(date '+%F %T')"
"$PYT" -I -B tpp_counts_v01.py --set t1 "$OUT/keys_t1_val_v01.npz" "$OUT/tpp_int_ee_t1_trk_val_v01.npz" "$OUT/tpp_int_ee_t1_gt_val_v01.npz" \
  --set t3 "$OUT/keys_t3_val_v01.npz" "$OUT/tpp_int_ee_t3_trk_val_v01.npz" "$OUT/tpp_int_ee_t3_gt_val_v01.npz" --out "$OUT/tpp_counts_v01.json" | tail -n 1
echo "tests start $(date '+%F %T')"
for t in t1 t3; do
  "$PYC" -I -B tests/test_tpp_keys_v01.py --keys "$OUT/keys_${t}_val_v01.npz" --out "$TST/test_tpp_keys_v01_${t}_full.json" | grep -E "^(PASS|FAIL)|ALL_PASS|SOME_FAIL" | cut -c1-160
  "$PYT" -I -B tests/test_tpp_run_v01.py --tpp-root "$TPP" --out "$TST/test_tpp_run_v01_${t}_full.json" --keys "$OUT/keys_${t}_val_v01.npz" \
    --runs "$OUT/tpp_int_ee_${t}_trk_val_v01.npz" "$OUT/tpp_int_ee_${t}_gt_val_v01.npz" | grep -E "^(PASS|FAIL)|ALL_PASS|SOME_FAIL" | cut -c1-200
done
cd "$WB/30_DATA/tpp_v01" && sha256sum keys_t1_val_v01.npz keys_t3_val_v01.npz keys_t1_val_v01_summary.json keys_t3_val_v01_summary.json \
  tpp_int_ee_t?_*_val_v01.npz tpp_int_ee_t?_*_val_v01_summary.json tpp_counts_v01.json > SHA256SUMS_v01.txt
echo "production sums: $(wc -l < SHA256SUMS_v01.txt) files; $(date '+%F %T')"
echo "TPP v02 PRODUCTION DONE"
cd "$WB/50_CODE/tpp"
for sd in 20261104 20261105; do
  for t in t1 t3; do
    N=$(nw); echo "seed run $t trk $sd start $(date '+%F %T') workers $N"
    "$PYT" -I -B tpp_run_v01.py --tpp-root "$TPP" --model int_ee --keys "$OUT/keys_${t}_val_v01.npz" --source trk --seed $sd \
      --out "$OUT/seed_sensitivity/tpp_int_ee_${t}_trk_val_seed${sd}_v01.npz" --workers "$N" --threads 1 | grep -E "DONE|rror" | cut -c1-200
  done
done
cd "$WB/30_DATA/tpp_v01/seed_sensitivity" && sha256sum *.npz *.json > SHA256SUMS_seed_v01.txt
echo "TPP v02 chain end $(date '+%F %T %Z')"
