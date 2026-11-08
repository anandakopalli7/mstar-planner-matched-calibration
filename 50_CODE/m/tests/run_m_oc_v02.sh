#!/usr/bin/env bash
# OC v02 at the real counts of one tracker setting (Claude line, v01, 31 Oct 2026): shards of test_m_oc_v02 (at most MAXJ at a
# time), then merge_oc_v02 with the plan v04 section 9 acceptance criteria. Simulated outcomes only.
# Usage: MAXJ=6 bash run_m_oc_v02.sh T1 canmot_sc
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
T=$1; TAG=$2
SZ="$(w "$W/60_RESULTS/m/m_sizes_${TAG}_v03.json")"; D="$W/70_TESTS/m_scratch/oc_v02"; mkdir -p "$D"
cd "$W/50_CODE/m/tests"
limit() { while [ "$(jobs -rp | wc -l)" -ge "${MAXJ:-6}" ]; do wait -n; done; }
job() {  # part rho effect datasets shard
  limit
  "$PY" -B test_m_oc_v02.py --sizes "$SZ" --part $1 --rho $2 --effect $3 --datasets $4 --shard $5 --refit-B 60 --e2-B 150 \
    --out "$(w "$D/${T}_$1_rho$2_eff$3_s$5.json")" > "$D/${T}_$1_rho$2_eff$3_s$5.log" 2>&1 &
}
echo "OC $T start $(date +%H:%M:%S)"
job e1null 0.5 1.0 10 0; job e1null 0.5 1.0 10 1; job e1null 0.8 1.0 5 2; job e1null 0.8 1.0 5 3
job e2null 0.5 1.0 10 0; job e2null 0.5 1.0 10 1; job e2null 0.5 1.0 10 2; job e2null 0.8 1.0 5 3; job e2null 0.8 1.0 5 4
job e2power 0.5 1.5 10 0; job e2power 0.5 1.5 10 1; job e2power 0.5 2.0 10 2; job e2power 0.5 2.0 10 3
job hm3power 0.5 1.6 10 0; job hm3power 0.5 1.6 10 1; job hm3power 0.5 2.0 10 2; job hm3power 0.5 2.0 10 3
job hm3power 0.5 2.6 10 4; job hm3power 0.5 2.6 10 5; job hm3power 0.8 2.0 5 6; job hm3power 0.8 2.0 5 7
job comp 0.5 1.0 40 0
wait
"$PY" -B merge_oc_v02.py --dir "$(w "$D")" --tracker $T --out "$(w "$W/70_TESTS/m_scratch/oc_v02_$T.json")"
echo "OC $T DONE $(date +%H:%M:%S)"
