#!/usr/bin/env bash
# R05 M5: synthetic run of x2_full_v02 at train scale (memory and time), after the X2 pre-freeze chain. Code check only.
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; T="$X/tests/e2e"; R="$W/60_RESULTS/x2"
until grep -q "X2 PREFREEZE DONE" "$W/80_LOGS/P9_x2_prefreeze_chain_v02.log" 2>/dev/null; do sleep 30; done
"$PY" -B "$(w "$X/tests/make_synthetic_export_v01.py")" --gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --mode calibrated --out "$(w "$T/syn_train_cal")"
cd "$W/50_CODE/third_party/CANMOT"
"$PY" -B "$(w "$X/x1_horizon_prep_v01.py")" --environment my_machine --workers "$(w "$T/syn_train_cal")" --out "$(w "$T/syn_train_cal/horizon.jsonl.gz")"
"$PY" -B "$(w "$X/x2_full_v02.py")" --prereg "$(w "$T/test_prereg.md")" --workers "$(w "$T/syn_train_cal")" --gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")" --oc "$(w "$T/oc_stub.json")" --horizon "$(w "$T/syn_train_cal/horizon.jsonl.gz")" --skip-bind --out "$(w "$T/syn_train_cal_result.json")"
"$PY" -B -c "
import json,sys
r=json.load(open(sys.argv[1]))
out={'synthetic':True,'records':r['Q0']['records'],'peak_working_set_mb':r['peak_working_set_mb'],'wall_s':r['wall_s'],'G1_X2':r['G1_X2']['G1_holds'],'eligible':r['family_h2s']['eligible']}
json.dump(out,open(sys.argv[2],'w'),indent=1); print(out)
" "$(w "$T/syn_train_cal_result.json")" "$(w "$R/x2_synthetic_scale_test_v02.json")"
echo "X2 SYNTHETIC SCALE TEST DONE"
