#!/usr/bin/env bash
# run_tpp_pod_v01.sh: TPP arm phase 1 (outcome-blind) on a Linux CPU pod, from the bundle made by make_tpp_pod_bundle_v01.sh.
# Every production prediction of the arm comes from this one platform. Steps, each a hard stop on failure:
#   0 verify the bundle checksums; 1 build the pinned environments (tpp38 = the laptop's validated versions; keys310 =
#   canmot310's numpy) and check the freeze against the pins; 2 platform tests R1-R8 (synthetic) and the pickle scan;
#   3 cross-platform spot check on 4 val scenes x 2 trackers x 2 sources against the laptop reference shipped in the
#   bundle (gate: statuses identical, keys identical, step-4 V2 mean <= 0.01 m, covariance <= 1 % relative);
#   4 the full job: keys T1, T3; Trajectron++ int_ee on tracker and ground-truth histories; counts; tests K1-K4, R9;
#   5 SHA256 sums of every output, for verification on the laptop.
# Outcome-blind: counts and integrity checks only; no exceedance, coverage, NEES or calibration quantity is computed.
# Usage (on the pod, bundle unpacked at B):  WORKERS=24 bash B/50_CODE/tpp/pod/run_tpp_pod_v01.sh > run_tpp_pod_v01.log 2>&1
set -uo pipefail
B="$(cd "$(dirname "$0")/../../.." && pwd)"
NP=$(nproc); DEF=$(( NP > 4 ? NP - 2 : 2 )); [ "$DEF" -gt 24 ] && DEF=24
WORKERS=${WORKERS:-$DEF}
O="$B/30_DATA/tpp_v01"; T="$B/70_TESTS/tpp_v01/pod"; X="$T/xplat"; R="$B/70_TESTS/tpp_v01/xplat_laptop"
C="$B/50_CODE/tpp"; TPP="$B/50_CODE/third_party/Trajectron-plus-plus_eccv2020"
mkdir -p "$O" "$T" "$X"
log() { echo "[$(date '+%F %T %Z')] $*"; }
die() { log "STOP: $*"; echo "TPP POD V01 STOPPED"; exit 1; }
log "TPP POD V01 start; bundle $B; nproc $NP; workers $WORKERS"
cd "$B" && sha256sum -c --quiet 50_CODE/tpp/pod/BUNDLE_SHA256SUMS_v01.txt || die "bundle checksums"
log "bundle checksums OK"
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
command -v uv >/dev/null 2>&1 || python3 -m pip install -q "uv==0.13.6" || python3 -m pip install -q --break-system-packages "uv==0.13.6" \
  || die "uv install"
command -v uv >/dev/null 2>&1 || export PATH="$HOME/.local/bin:$PATH"
export UV_PYTHON_INSTALL_DIR="$B/env/pythons" UV_CACHE_DIR="$B/env/uv_cache" UV_HTTP_TIMEOUT=600
uv python install 3.8.20 3.10.22 || die "python install"
uv venv -q "$B/env/tpp38" --python 3.8.20 || die "venv tpp38"
uv venv -q "$B/env/keys310" --python 3.10.22 || die "venv keys310"
uv pip install -q --python "$B/env/tpp38/bin/python" --index-url https://download.pytorch.org/whl/cpu --extra-index-url https://pypi.org/simple \
  --index-strategy unsafe-best-match -r "$C/pod/requirements_tpp38_v01.txt" || die "tpp38 packages"
uv pip install -q --python "$B/env/keys310/bin/python" -r "$C/pod/requirements_keys310_v01.txt" || die "keys310 packages"
PYT="$B/env/tpp38/bin/python"; PYK="$B/env/keys310/bin/python"
{ echo "# pod $(hostname) $(uname -a)"; "$PYT" -I -c 'import sys; print("python", sys.version)'; uv pip freeze --python "$PYT"; } > "$T/pod_pip_freeze_tpp38_v01.txt"
{ "$PYK" -I -c 'import sys; print("python", sys.version)'; uv pip freeze --python "$PYK"; } > "$T/pod_pip_freeze_keys310_v01.txt"
for f in tpp38 keys310; do
  while read -r req; do req=${req%$'\r'}; [ -z "$req" ] && continue
    grep -qx "$req" "$T/pod_pip_freeze_${f}_v01.txt" || die "pin $req missing in $f freeze"; done < "$C/pod/requirements_${f}_v01.txt"
done
log "environments pinned OK"
cd "$C"
"$PYT" -I -B tpp_pickle_scan_v01.py "$TPP/experiments/nuScenes/models/int_ee/model_registrar-12.pt" > "$T/pod_pickle_scan_v01.json" || die "pickle scan"
"$PYT" -I -B tests/test_tpp_run_v01.py --tpp-root "$TPP" --out "$T/pod_test_tpp_run_v01_synthetic.json" | grep -E "^(PASS|FAIL)" | cut -c1-160
grep -q '"all_pass": true' "$T/pod_test_tpp_run_v01_synthetic.json" || die "platform tests R1-R8"
log "platform tests R1-R8 ALL_PASS"
SC="scene-0003 scene-0014 scene-0036 scene-0092"
CMP=()
for t in t1 t3; do
  "$PYK" -I -B tpp_keys_v01.py --cache "$B/30_DATA/k6/cache_v02_${t}_val" --out "$X/keys_${t}_spot.npz" --scenes $SC | tail -n 1
  for s in trk gt; do
    "$PYT" -I -B tpp_run_v01.py --tpp-root "$TPP" --model int_ee --keys "$X/keys_${t}_spot.npz" --source $s --out "$X/run_${t}_${s}_spot.npz" \
      --workers 2 --threads 1 | grep -E "DONE|rror" || die "spot run $t $s"
    CMP+=(--ref-keys "$R/keys_${t}_spot.npz" --ref-run "$R/run_${t}_${s}_spot.npz" --new-keys "$X/keys_${t}_spot.npz" --new-run "$X/run_${t}_${s}_spot.npz")
  done
done
"$PYT" -I -B tpp_xplat_compare_v01.py "${CMP[@]}" --out "$T/xplat_laptop_vs_pod_v01.json" || die "cross-platform gate (see xplat_laptop_vs_pod_v01.json)"
log "cross-platform gate PASS"
for t in t1 t3; do
  "$PYK" -I -B tpp_keys_v01.py --cache "$B/30_DATA/k6/cache_v02_${t}_val" --out "$O/keys_${t}_val_v01.npz" --workers "$WORKERS" | tail -n 1 | cut -c1-200
  [ -s "$O/keys_${t}_val_v01.npz" ] || die "keys $t"
done
for t in t1 t3; do
  for s in trk gt; do
    log "run $t $s"
    "$PYT" -I -B tpp_run_v01.py --tpp-root "$TPP" --model int_ee --keys "$O/keys_${t}_val_v01.npz" --source $s \
      --out "$O/tpp_int_ee_${t}_${s}_val_v01.npz" --workers "$WORKERS" --threads 1 | grep -E "scenes (50|100|150)/|DONE|rror" | cut -c1-200
    [ -s "$O/tpp_int_ee_${t}_${s}_val_v01.npz" ] || die "run $t $s"
  done
done
"$PYT" -I -B tpp_counts_v01.py --set t1 "$O/keys_t1_val_v01.npz" "$O/tpp_int_ee_t1_trk_val_v01.npz" "$O/tpp_int_ee_t1_gt_val_v01.npz" \
  --set t3 "$O/keys_t3_val_v01.npz" "$O/tpp_int_ee_t3_trk_val_v01.npz" "$O/tpp_int_ee_t3_gt_val_v01.npz" --out "$O/tpp_counts_v01.json" | tail -n 1 || die "counts"
for t in t1 t3; do
  "$PYK" -I -B tests/test_tpp_keys_v01.py --keys "$O/keys_${t}_val_v01.npz" --out "$T/test_tpp_keys_v01_${t}.json" | grep -E "^(PASS|FAIL)" | cut -c1-160
  "$PYT" -I -B tests/test_tpp_run_v01.py --tpp-root "$TPP" --out "$T/test_tpp_run_v01_${t}_full.json" --keys "$O/keys_${t}_val_v01.npz" \
    --runs "$O/tpp_int_ee_${t}_trk_val_v01.npz" "$O/tpp_int_ee_${t}_gt_val_v01.npz" | grep -E "^(PASS|FAIL) R9" | cut -c1-300
done
cd "$B" && sha256sum 30_DATA/tpp_v01/* 70_TESTS/tpp_v01/pod/*.json 70_TESTS/tpp_v01/pod/pod_pip_freeze_*.txt 70_TESTS/tpp_v01/pod/xplat/* > "$B/OUTPUT_SHA256SUMS.tmp" \
  && mv "$B/OUTPUT_SHA256SUMS.tmp" "$T/OUTPUT_SHA256SUMS_v01.txt"
grep -l '"all_pass": false' "$T"/*.json && log "WARNING: a test suite has a failure (listed above)"
log "outputs: $(wc -l < "$T/OUTPUT_SHA256SUMS_v01.txt") files summed in 70_TESTS/tpp_v01/pod/OUTPUT_SHA256SUMS_v01.txt"
echo "TPP POD V01 DONE"
