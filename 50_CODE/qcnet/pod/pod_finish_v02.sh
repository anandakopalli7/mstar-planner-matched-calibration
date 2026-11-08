#!/usr/bin/env bash
# pod_finish_v02.sh (QCNet arm, 2 Nov 2026) = pod_finish_v01.sh waiting on pod_lt3d_run_v07.sh (v06's ap step stopped on a
# log-id slice bug; v01 then stopped as designed) and logging to finish_v02.log.
# pod_finish_v01.sh: after the LT3D 10 Hz run (pod_lt3d_run_v06.sh) ends, run the tracker part
# (pod_stage3_v01.sh; the tracker note 60_RESULTS/av2_trk/AV2_TRACKER_NOTE_v01.md existed from 01:20 EST), the join coverage
# against the 2 Hz paired records of T1 and T3 x LT3D (pod_join2hz_v01.py, the helper's code read-only from /root/work/wcopy),
# the packing and counts (pod_qcnet_pack_v01.py), and assemble /root/work/deliver with SHA256SUMS.txt.
# Markers in /root/work/logs/finish_v01.log: FINISH_DONE or FINISH_STOP <reason>.
set -uo pipefail
R=/root/work
L=/root/local
exec > >(tee -a "$R/logs/finish_v02.log") 2>&1
echo "finish v02 start $(date -u +%FT%TZ)"
stop() { echo "FINISH_STOP $*"; exit 1; }
until grep -q LT3D10_RUN_DONE "$R/logs/lt3d10_run.log"; do
  if ! pgrep -f "pod_lt3d_run_v07.sh all" > /dev/null; then
    sleep 5; grep -q LT3D10_RUN_DONE "$R/logs/lt3d10_run.log" || stop "LT3D 10 Hz run ended without LT3D10_RUN_DONE"
  fi
  sleep 60
done
echo "lt3d10 done $(date -u +%FT%TZ)"
bash "$R/code_qcnet/pod_stage3_v01.sh" || stop "stage3 (see stage3_v01.log)"
G=$R/wcopy/30_DATA/av2_trk_v01
for t in t1 t3; do
  if [ ! -s "$R/out_qcnet/join2hz_${t}_v01.json" ]; then
    E=$G/export/${t}_lt3d
    OMP_NUM_THREADS=1 "$L/lt3d38/bin/python" "$R/code_qcnet/pod_join2hz_v01.py" --wroot "$R/wcopy" --tracker $t \
      --exports "$E/worker0" "$E/worker1" "$E/worker2" "$E/worker3" --gt "$G/gt/av2_val_gt_v01.json" \
      --qcnet-gt "$R/out_qcnet/qcnet_av2_gt_v01.npz" --qcnet-trk "$R/out_qcnet/qcnet_av2_trk_ab3dmot_v01.npz" \
      --out "$R/out_qcnet/join2hz_${t}_v01.json" > "$R/logs/join2hz_${t}_v01.log" 2>&1 || stop "join $t: $(tail -n 3 "$R/logs/join2hz_${t}_v01.log")"
  fi
  tail -n 2 "$R/logs/join2hz_${t}_v01.log"
done
D=$R/deliver
mkdir -p "$D/logs" "$D/env"
source "$L/qcnet310/bin/activate"
P="python -I $R/code_qcnet/pod_qcnet_pack_v01.py"
[ -s "$D/av2val10_lt3d_centerpoint_dets_s010_v01.npz" ] || $P dets --tables "$R/out_lt3d10/tables" --out "$D/av2val10_lt3d_centerpoint_dets_s010_v01.npz" || stop "pack dets"
[ -s "$D/trk10_ab3dmot_lt3d_3cls_v01.npz" ] || $P trk --trk "$R/out_trk10/logs10" --out "$D/trk10_ab3dmot_lt3d_3cls_v01.npz" || stop "pack trk"
$P counts --gt "$R/out_qcnet/qcnet_av2_gt_v01.npz" --trkq "$R/out_qcnet/qcnet_av2_trk_ab3dmot_v01.npz" --out "$D/qcnet_av2_counts_v01.json" > "$R/logs/pack_counts_v01.log" 2>&1 || stop "pack counts"
deactivate
cp -p "$R/out_qcnet/qcnet_av2_gt_v01.npz" "$R/out_qcnet/qcnet_av2_gt_v01_summary.json" "$R/out_qcnet/qcnet_av2_trk_ab3dmot_v01.npz" \
      "$R/out_qcnet/qcnet_av2_trk_ab3dmot_v01_summary.json" "$R/out_qcnet/bscheck_gt.json" \
      "$R/out_qcnet/join2hz_t1_v01.json" "$R/out_qcnet/join2hz_t1_v01_keys.npz" "$R/out_qcnet/join2hz_t3_v01.json" "$R/out_qcnet/join2hz_t3_v01_keys.npz" \
      "$R/out_qcnet/MANIFEST_av2_val_lidar_v04_maps.csv" \
      "$R/out_lt3d10/av2val10_lt3d_centerpoint_dets3_v01.npz" "$R/out_lt3d10/av2val10_lt3d_centerpoint_export_v01.json" \
      "$R/out_lt3d10/av2val10_lt3d_centerpoint_ap3_v01.csv" "$R/out_lt3d10/av2val10_lt3d_centerpoint_ap3_v01.json" \
      "$R/out_lt3d10/av2val10_lt3d_repro_2hz_v01.json" "$R/out_trk10/ab3dmot_equiv_v01.json" \
      "$R/out_qcnet/qcnet_frame_test_v01.json" "$R/out_qcnet/qcnet_frame_test_v02_float64.json" "$R/out_qcnet/qcnet_frame_test_v03.json" "$D/" || stop "copy results"
cp -p "$R/logs/qcnet_ckpt_verify_v03.json" "$R/logs/qcnet_ckpt_sha256_v03.txt" "$R/logs/qcnet_ckpt_md5_v03.txt" "$R/logs/qcnet_ckpt_size_v03.txt" \
      "$R/logs/qcnet_commit_v03.txt" "$R/logs/qcnet_pip_freeze_v03.txt" "$R/logs/lt3d_commit_v04.txt" "$R/logs/lt3d_centerpoint_ckpt_sha256_v04.txt" \
      "$R/logs/lt3d_tar_sha256_v04.txt" "$R/logs/lt3d_pip_freeze_v04c.txt" "$D/env/" || stop "copy env records"
(cd "$R/code_qcnet" && sha256sum * > "$D/env/code_qcnet_sha256_at_finish.txt")
(cd "$R/wcopy" && sha256sum -c "$R/logs/wcopy_laptop_sha256.txt" > "$D/env/wcopy_helper_files_check.txt" 2>&1 || true)
for f in finish_v01.log finish_v02.log master_v04.log master_v06.log lt3d_setup_v04.log qcnet_setup_v01.log qcnet_setup_v02.log qcnet_setup_v03.log lt3d_nuscenes_v01.log lt3d_nntime_v01.log \
         lt3d10_run.log lt3d10_prep.log lt3d10_shard_split.log lt3d10_shard_merge.log lt3d10_split.log lt3d10_export.log lt3d10_ap.log lt3d10_repro.log qcnet_frame_test_v01.log qcnet_frame_test_v02.log \
         qcnet_gt_bscheck.log qcnet_gt_infer.log qcnet_gt_merge.log stage3_v01.log ab3dmot_equiv_v01.log ab3dmot_run_v01.log qcnet_trk_infer.log qcnet_trk_merge.log \
         join2hz_t1_v01.log join2hz_t3_v01.log pack_counts_v01.log fetch_v04_maps.log; do
  [ -f "$R/logs/$f" ] && grep -v "task/s, elapsed" "$R/logs/$f" | tail -n 400 > "$D/logs/$f"
done
for i in 0 1 2 3 4 5; do [ -f "$R/logs/lt3d10_test_shard$i.log" ] && { grep -v "task/s" "$R/logs/lt3d10_test_shard$i.log" | tail -n 60; tail -c 300 "$R/logs/lt3d10_test_shard$i.log"; } > "$D/logs/lt3d10_test_shard$i.log"; done
cd "$D" && find . -type f ! -name SHA256SUMS.txt | sort | xargs sha256sum > SHA256SUMS.txt
du -sh "$D"; wc -l "$D/SHA256SUMS.txt"
echo "finish v02 end $(date -u +%FT%TZ)"
echo FINISH_DONE
