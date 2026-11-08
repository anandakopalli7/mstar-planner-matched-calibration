#!/usr/bin/env bash
# pod_owndet_profstage_v02.sh (own-detector job, 2 Nov 2026): the profiling loop of pod_owndet_profstage_v01.sh rerun with
# pod_owndet_profile_v02.py --no-cbgs (v01's runs stopped on CBGS's division by zero for classes absent from the 40-log subset).
# Same four configurations. Outputs in $R/owndet/profile2/. Marker in owndet_profstage_v02.log: PROFILE2_DONE.
set -uo pipefail
R=/root/work; L=/root/local; C=$R/code_owndet
exec > >(tee -a "$R/logs/owndet_profstage_v02.log") 2>&1
has() { grep -q "$1" "$2" 2>/dev/null; }
S=$L/av2/sensor; I=$S/av2_owndet_infos
source "$L/lt3d38/bin/activate"
PUB=$L/ckpt_lt3d/av2_detectors/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2/centerpoint_0075voxel_second_secfpn_dcn_4x8_cyclic_50m_wide_hierarchy_tta_20e_av2.py
cd "$L/LT3D"
for spec in P1:4:11:1:prof P2:4:11:4:noprof P3:8:11:4:noprof P4:4:6:4:noprof; do
  IFS=: read -r name B W T PF2 <<< "$spec"
  O=$R/owndet/profile2/$name
  has "PROFILE DONE" "$O/run.log" && continue
  mkdir -p "$O"
  python "$C/pod_owndet_cfg_v03.py" --lt3d "$L/LT3D" --public-cfg "$PUB" --infos-dir "$I" --data-root "$S/" --batch $B --workers $W \
    --train-infos av2_infos_prof40.pkl --db-infos av2_dbinfos_prof40.pkl --max-iters 1000 --work-dir "$O" --out "$O/cfg.py" > "$O/cfg.log" 2>&1 || { echo "$name cfg failed"; continue; }
  FLAG=""; [ "$PF2" = prof ] && FLAG="--profile"
  OMP_NUM_THREADS=$T MKL_NUM_THREADS=$T OPENBLAS_NUM_THREADS=$T timeout 1500 python "$C/pod_owndet_profile_v02.py" --lt3d "$L/LT3D" --cfg "$O/cfg.py" --iters 40 --workers $W --out "$O" --no-cbgs $FLAG > "$O/run.log" 2>&1
  if has "PROFILE DONE" "$O/run.log"; then echo "$name done: $(python3 -c "import json; d=json.load(open('$O/profile_summary.json')); print('B', d['batch'], 'W', d['workers'], 's/it %.3f samples/s %.2f data %.3f' % (d['s_per_it'], d['samples_per_s'], d['data_wait_s']), 'sections', {k: round(v, 3) for k, v in d['sections_s'].items()}, 'bwd %.3f' % d['backward_step_s'], 'mem %.1f GB' % d['peak_memory_gb'])")";
  else echo "$name failed: $(grep -m1 -i "out of memory\|Error" "$O/run.log" | cut -c1-200)"; fi
done
echo "PROFILE2_DONE $(date -u +%FT%TZ)"
