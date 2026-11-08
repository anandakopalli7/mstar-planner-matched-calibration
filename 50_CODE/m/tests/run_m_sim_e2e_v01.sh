#!/usr/bin/env bash
# End-to-end test of the method-stage pipeline on a fully simulated dataset (Claude line, v01, 31 Oct 2026):
# make_sim_dataset_v01 -> m_sizes_v01 (outcomes off) -> m_run_v01 --test-mode (B = 300) -> m_decide_v01 (T1 = T2 = sim).
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
C="$W/50_CODE/m"; S="$W/70_TESTS/m_scratch/sim_e2e_v01"
rm -rf "$S"; mkdir -p "$S"
cd "$C"
"$PY" -B tests/make_sim_dataset_v01.py --out "$(w "$S")"
common=(--tracker SIM --experiment sim --train-gt "$(w "$S/gt_train.json")" --val-gt "$(w "$S/gt_val.json")" --meta "$(w "$S/meta")"
        --train-horizon "$(w "$S/horizon_train.jsonl.gz")" --val-horizon "$(w "$S/horizon_val.jsonl.gz")"
        --train-workers "$(w "$S/train/worker0")" "$(w "$S/train/worker1")" --val-workers "$(w "$S/val/worker0")")
"$PY" -B m_sizes_v01.py "${common[@]}" --out "$(w "$S/sizes.json")"
"$PY" -B m_run_v01.py "${common[@]}" --prereg none --sizes "$(w "$S/sizes.json")" --out "$(w "$S/result.json")" --test-mode --boot 300
"$PY" -B m_decide_v01.py --t1 "$(w "$S/result.json")" --t2 "$(w "$S/result.json")" --out "$(w "$S/decision.json")"
echo "SIM E2E DONE"
