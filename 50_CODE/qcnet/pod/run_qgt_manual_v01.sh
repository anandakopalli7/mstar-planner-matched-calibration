#!/usr/bin/env bash
# run_qgt_manual_v01.sh (QCNet arm rerun): the QCNet GT branch of pod_qcnet2_master_v02.sh, started by hand while master v01 finishes its
# tracker branch (master v01's own GT step failed in the scene transport). Same commands and log names as master v02, which then skips them.
R=/root/work; L=/root/local; C=$R/code_qcnet; D=$L/av2/sensor/val; W2=$R/work2
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 NUMBA_NUM_THREADS=1
source "$L/qcnet310/bin/activate"
QI="python -I $C/qcnet_av2_infer_v03.py --qcnet $L/QCNet --ckpt $R/ckpt_qcnet/QCNet_AV2.ckpt --data $D --sweeps $W2/sweeps_by_log.json --out $R/out2/qcnet3"
$QI --source gt --batch 4 --workers 3 > "$R/logs/qcnet3_gt_infer.log" 2>&1
grep -q "INFER DONE" "$R/logs/qcnet3_gt_infer.log" && $QI --merge --source gt --name qcnet_av2_gt_recentred_v02.npz > "$R/logs/qcnet3_gt_merge.log" 2>&1
grep -q "MERGE DONE" "$R/logs/qcnet3_gt_merge.log" && python -I "$C/qcnet_frame_test_v05.py" --qcnet "$L/QCNet" --ckpt "$R/ckpt_qcnet/QCNet_AV2.ckpt" --data "$D" --sweeps "$W2/sweeps_by_log.json" --out "$R/out2/qcnet_frame_test_v05.json" > "$R/logs/qcnet_frame_test_v05.log" 2>&1
echo QGT_MANUAL_END
