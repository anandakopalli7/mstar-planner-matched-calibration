#!/usr/bin/env bash
# Freeze K6 plan v02 (k6_freeze_v02.py with the canonical OC and dev check), then the confirmatory run (run_k6_main_v02.sh).
# The main run starts only if the freeze succeeded. Unattended; no branch on any result.
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
cd "$W/50_CODE/k6"
echo "freeze start $(date +%H:%M:%S)"
"$PY" -B k6_freeze_v02.py --plan "$(w "$W/40_PROTOCOL/K6_PREREGISTRATION_v02.md")" --oc "$(w "$W/70_TESTS/k6_scratch/k6_oc_v02.json")" \
  --dev "$(w "$W/70_TESTS/k6_scratch/k6_dev_check_v02.json")" || { echo "FREEZE FAILED"; exit 1; }
echo "freeze done $(date +%H:%M:%S)"
bash "$W/50_CODE/k6/run_k6_main_v02.sh"
