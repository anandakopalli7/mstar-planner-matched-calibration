#!/usr/bin/env bash
# OC v03 at the real counts of one tracker setting (Claude line, v01, 31 Oct 2026; R07c X-M1). Fresh seeds, E2 parts only,
# with the v04 rules:
#   null at rho 0.5 and log SD 0.1: 100 datasets (the A2 confirmation);
#   null at rho 0.8: 20;
#   null at log SD 0.05 and 0.2: 40 each;
#   val turning shifts x1.5 and x2.0: 40 each.
# The E1 parts (A1, HM3 power, component power) are taken from the OC v02 shards; the E1 rules are unchanged in v04.
# Usage: MAXJ=4 bash run_m_oc_v03.sh T1 canmot_sc
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
T=$1; TAG=$2
SZ="$(w "$W/60_RESULTS/m/m_sizes_${TAG}_v03.json")"; D="$W/70_TESTS/m_scratch/oc_v03"; mkdir -p "$D"
cd "$W/50_CODE/m/tests"
limit() { while [ "$(jobs -rp | wc -l)" -ge "${MAXJ:-4}" ]; do wait -n; done; }
job() {  # part rho effect log_sd datasets shard
  limit
  "$PY" -B test_m_oc_v03.py --sizes "$SZ" --part $1 --rho $2 --effect $3 --log-sd $4 --datasets $5 --shard $6 --e2-B 150 \
    --out "$(w "$D/${T}_$1_rho$2_eff$3_log$4_s$6.json")" > "$D/${T}_$1_rho$2_eff$3_log$4_s$6.log" 2>&1 &
}
echo "OC3 $T start $(date +%H:%M:%S)"
for s in 0 1 2 3; do job e2null 0.5 1.0 0.1 25 $s; done
job e2null 0.8 1.0 0.1 20 4
job e2null 0.5 1.0 0.05 20 5; job e2null 0.5 1.0 0.05 20 6
job e2null 0.5 1.0 0.2 20 7; job e2null 0.5 1.0 0.2 20 8
job e2power 0.5 1.5 0.1 20 9; job e2power 0.5 1.5 0.1 20 10
job e2power 0.5 2.0 0.1 20 11; job e2power 0.5 2.0 0.1 20 12
wait
echo "OC3 $T DONE $(date +%H:%M:%S)"
