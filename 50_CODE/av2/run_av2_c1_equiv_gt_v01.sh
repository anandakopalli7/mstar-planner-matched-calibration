#!/usr/bin/env bash
# AV2 port v04 equivalence tests for the ground-truth-reading tools (Claude line, v01, 5 Nov 2026; design v04 section 10).
# av2_gt_prep_v02 on the 150 val logs (no list; and --logs-file = the 150 val logs) must reproduce the SHA-256 of
# 30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json (9642db5b..., hashed only, never opened). Each test output is written to a
# temporary folder under the scratchpad, hashed, and deleted at once; the deletion is recorded. av2_ego_prep_v02 (--gt the
# v01 GT file) must reproduce the decompressed content of 30_DATA/av2_cache_stageA_v01/av2_ego10hz_v01.json.gz.
# Usage: bash run_av2_c1_equiv_gt_v01.sh <scratch tmp dir>
W=/c/Users/anand/Downloads/ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911
w() { cygpath -w "$1"; }
PY="$W/50_CODE/env/canmot310/Scripts/python.exe"; S="$W/50_CODE/av2"; E="$W/60_RESULTS/av2_trk/c1_375/equiv"
TMP="$1"; mkdir -p "$TMP" "$E"
export OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 MKL_NUM_THREADS=1
cd /c/Users/anand
REFGT="$W/30_DATA/av2_trk_v01/gt/av2_val_gt_v01.json"
REF=$(sha256sum "$REFGT" | cut -c1-64)
REC="$E/EQUIV_gt_prep_v02_record.txt"
echo "reference $REFGT sha256 $REF (hashed only) $(date -Iseconds)" > "$REC"
"$PY" -I -B -c "import json,sys; sys.path.insert(0, sys.argv[2]); import av2_common_v02 as C; json.dump(C.val_logs(), open(sys.argv[1], 'w'))" "$(w "$TMP/val150_list.json")" "$(w "$S")"
for mode in default listfile; do
  OUT="$TMP/gt_${mode}.json"
  if [ $mode = default ]; then
    "$PY" -I -B "$(w "$S/av2_gt_prep_v02.py")" --out "$(w "$OUT")" > "$TMP/gt_${mode}.log" 2>&1
  else
    "$PY" -I -B "$(w "$S/av2_gt_prep_v02.py")" --out "$(w "$OUT")" --logs-file "$(w "$TMP/val150_list.json")" > "$TMP/gt_${mode}.log" 2>&1
  fi
  H=$(sha256sum "$OUT" | cut -c1-64)
  rm -f "$OUT"
  GONE=$([ -e "$OUT" ] && echo NO || echo yes)
  echo "gt_prep_v02 $mode: sha256 $H identical $([ "$H" = "$REF" ] && echo true || echo false); temporary copy deleted: $GONE at $(date -Iseconds)" >> "$REC"
done
# ego prep v02 against v01's ego file (decompressed content)
OUT="$TMP/ego_test.json.gz"
"$PY" -I -B "$(w "$S/av2_ego_prep_v02.py")" --gt "$(w "$REFGT")" --out "$(w "$OUT")" > "$TMP/ego_test.log" 2>&1
"$PY" -I -B "$(w "$S/test_av2_port_v04_equiv_v01.py")" gz --test "$(w "$OUT")" --ref "$(w "$W/30_DATA/av2_cache_stageA_v01/av2_ego10hz_v01.json.gz")" \
  --out "$(w "$E/EQUIV_ego_prep_v02.json")"
rm -f "$OUT"
echo "ego_prep_v02: $(tail -n 2 "$TMP/ego_test.log" | head -n 1); temporary copy deleted $(date -Iseconds)" >> "$REC"
cat "$REC"
echo "EQUIV GT DONE $(date +%H:%M:%S)"; true
