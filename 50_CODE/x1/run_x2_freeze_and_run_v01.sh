#!/usr/bin/env bash
# After the synthetic scale test: freeze X2 v02 (only if the test passed with peak memory below 12 GB), record the hash
# outside the folder, then run the frozen X2 analysis on the real train data.
set -e
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"
X="$W/50_CODE/x1"; R="$W/60_RESULTS/x2"; E="$W/60_RESULTS/x2_export_train700_fast_v02"
until grep -q "X2 SYNTHETIC SCALE TEST DONE\|Traceback\|MemoryError" "$W/80_LOGS/P10_x2_synthetic_scale.log" 2>/dev/null; do sleep 30; done
grep -q "X2 SYNTHETIC SCALE TEST DONE" "$W/80_LOGS/P10_x2_synthetic_scale.log" || { echo "SCALE TEST FAILED: not freezing"; exit 4; }
"$PY" -B -c "
import json,sys; r=json.load(open(sys.argv[1])); pk=r.get('peak_working_set_mb') or 0
print('synthetic peak MB', pk, 'wall', r['wall_s']); assert pk < 12000, 'peak memory too high'
" "$(w "$R/x2_synthetic_scale_test_v02.json")"
"$PY" -B "$(w "$X/x2_freeze_v02.py")" --base "$(w "$W")"
H=$(cut -d' ' -f1 "$W/40_PROTOCOL/X2_PREREGISTRATION_v02.sha256")
printf '\n## X2 pre-registration v02 frozen (%s)\n\nSHA-256 **%s**. Frozen after review R05 and the pre-freeze checks, before any train residual was computed.\n' "$(date '+%Y-%m-%d %H:%M')" "$H" >> "/c/Users/anand/AppData/Local/Claude-Data/claude_pzs8sxrjxfjjc/side-session-notes/local_8e30398a-c824-4d04-a58d-489b218bff90/PROGRAMME_A_RESUME_HANDOVER_20261030.md"
printf '\n**%s: X2 pre-registration v02 frozen.** SHA-256 %s.\n' "$(date '+%Y-%m-%d %H:%M')" "$H" >> "/c/Users/anand/.claude/projects/C--Users-anand-OneDrive-Downs-Building-Evidence/memory/programme-a-no-deadline-downloads-playground.md"
echo "FROZEN $H"
WK=""; for i in $(seq 0 11); do WK="$WK $(w "$E/worker$i")"; done
"$PY" -B "$(w "$X/x2_full_v02.py")" --prereg "$(w "$W/40_PROTOCOL/X2_PREREGISTRATION_v02.md")" --workers $WK --gt "$(w "$W/30_DATA/x2_gt/x2_train_gt_v03.json")" --meta "$(w "$W/30_DATA/nuscenes/v1.0-trainval")" --oc "$(w "$R/x2_oc_q4_v02.json")" --horizon "$(w "$R/x2_horizon_v01.jsonl.gz")" --out "$(w "$R/x2_full_v02_result.json")"
echo "X2 RUN DONE"
