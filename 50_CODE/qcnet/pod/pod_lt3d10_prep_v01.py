"""pod_lt3d10_prep_v01 (QCNet arm, 2 Nov 2026): LT3D val infos for EVERY lidar sweep of the 150 AV2 val logs.

The per-log loop of 50_CODE/av2/pod/pod_lt3d_stage2_v01.sh (LT3D's own generate_info, its VAL list, 5 sweeps), with the
sample-rate test removed (sample rate 1 instead of LT3D's VAL_SAMPLE_RATE = 5). Pool.map keeps c.VAL order, so the info
list is the sequential one. Runs in the LT3D venv; LT3D's repository root is put on sys.path explicitly.
Usage: python pod_lt3d10_prep_v01.py --lt3d <LT3D root> --root <.../Sensor> --out <infos.pkl> --procs N
"""
import argparse
import os
import pickle
import sys
from multiprocessing import Pool
from pathlib import Path

A = None


def one_log(log_id):
    import mmcv
    import tools.data_converter.av2_converter as c
    name2cid = {cl: i for i, cl in enumerate(c.class_names)}
    log_dir = "{root_path}/{split}/{log_id}".format(root_path=A.root, split="val", log_id=log_id)
    lidar_paths = "{log_dir}/sensors/lidar".format(log_dir=log_dir)
    annotations_path = "{log_dir}/annotations.feather".format(log_dir=log_dir)
    annotations = c.read_feather(Path(annotations_path))
    mmcv.check_file_exist(annotations_path)
    all_timestamps = sorted([int(filename.split(".")[0]) for filename in os.listdir(lidar_paths)])
    out = []
    for i, filename in enumerate(sorted(os.listdir(lidar_paths))):
        out.append(c.generate_info(filename, log_id, log_dir, annotations, name2cid, all_timestamps, 5))
    print("log done", log_id, len(out), flush=True)
    return out


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--procs", type=int, default=8)
    A = ap.parse_args()
    sys.path.insert(0, A.lt3d)
    os.chdir(A.lt3d)
    import tools.data_converter.av2_converter as c
    present = set(os.listdir(A.root + "/val"))
    missing = [l for l in c.VAL if l not in present]
    print("val logs in split list:", len(c.VAL), "present:", len(present), "missing:", len(missing), "VAL_SAMPLE_RATE (not used):", c.VAL_SAMPLE_RATE, flush=True)
    assert not missing, missing[:3]
    with Pool(A.procs) as pool:
        parts = pool.map(one_log, list(c.VAL), chunksize=1)
    infos = [info for part in parts for info in part]
    os.makedirs(os.path.dirname(A.out), exist_ok=True)
    with open(A.out + ".part", "wb") as f:
        pickle.dump(infos, f)
    os.replace(A.out + ".part", A.out)
    infos = pickle.load(open(A.out, "rb"))
    print("val infos (all sweeps):", len(infos), "logs:", len({i["log_id"] for i in infos}), flush=True)
    print("PREP10 DONE", flush=True)


if __name__ == "__main__":
    main()
