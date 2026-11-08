"""pod_owndet_prep_v02 (own-detector job, 2 Nov 2026) = v01 + part "prof40" (the first 40 logs of train_475, for profiling only) and
--db-part (which train infos feed the GT database; outputs av2_dbinfos_<part>.pkl / av2_gt_database_<part> for prof40, v01 names for
train475). pod_owndet_prep_v01: LT3D infos and the GT database for the own CenterPoint.
Design: 50_CODE/owndet/OWN_DETECTOR_DESIGN_v01.md section 2.

infos   --part train475|held225|val150 : LT3D's own generate_info(..., 5 sweeps) for every 5th sweep of each log of the part
          (logs from AV2_TRAIN_SPLIT_v01.json; val = the 150 val logs), per-log Pool in log order -> <out>/av2_infos_<part>.pkl
gtdb    : LT3D/mmdet3d GTDatabaseCreater('AV2Dataset', ...) on av2_infos_train475.pkl only -> <out>/av2_gt_database/*.bin and
          <out>/av2_dbinfos_train.pkl (paths relative to the data root, as the db_sampler expects)
Runs in the LT3D venv from the LT3D root (put on sys.path).
"""
import argparse
import json
import os
import pickle
import sys
import time
from multiprocessing import Pool
from pathlib import Path

A = None
SAMPLE_RATE = 5


def one_log(args):
    split, log_id = args
    import mmcv
    import tools.data_converter.av2_converter as c
    name2cid = {cl: i for i, cl in enumerate(c.class_names)}
    log_dir = "{root}/{split}/{log}".format(root=A.root, split=split, log=log_id)
    lidar_paths = log_dir + "/sensors/lidar"
    annotations_path = log_dir + "/annotations.feather"
    annotations = c.read_feather(Path(annotations_path))
    mmcv.check_file_exist(annotations_path)
    names = sorted(os.listdir(lidar_paths))
    all_timestamps = sorted(int(f.split(".")[0]) for f in names)
    out = [c.generate_info(f, log_id, log_dir, annotations, name2cid, all_timestamps, 5) for i, f in enumerate(names) if i % SAMPLE_RATE == 0]
    return log_id, out


def cmd_infos():
    sp = json.load(open(A.split))
    if A.part == "train475":
        jobs = [("train", l) for l in sp["train_475"]]
    elif A.part == "prof40":
        jobs = [("train", l) for l in sp["train_475"][:40]]
    elif A.part == "held225":
        jobs = [("train", l) for l in sp["held_out_225"]]
    else:
        jobs = [("val", l) for l in sorted(os.listdir(os.path.join(A.root, "val")))]
        assert len(jobs) == 150, len(jobs)
    t0 = time.time()
    with Pool(A.procs) as pool:
        parts = pool.map(one_log, jobs, chunksize=1)
    infos = [i for _, p in parts for i in p]
    p = os.path.join(A.out, "av2_infos_%s.pkl" % A.part)
    with open(p + ".part", "wb") as f:
        pickle.dump(infos, f)
    os.replace(p + ".part", p)
    rec = {"part": A.part, "logs": len(parts), "frames": len(infos), "sample_rate": SAMPLE_RATE, "seconds": time.time() - t0,
           "frames_per_log_min": min(len(q) for _, q in parts), "frames_per_log_max": max(len(q) for _, q in parts)}
    json.dump(rec, open(p.replace(".pkl", "_summary.json"), "w"), indent=1)
    print(json.dumps(rec), flush=True)
    print("INFOS DONE", A.part, flush=True)


def cmd_gtdb():
    from tools.data_converter.create_gt_database import GTDatabaseCreater
    t0 = time.time()
    # db entries hold paths relative to the data root: "<out_rel>/av2_gt_database/<file>.bin" (info_prefix = "<out_rel>/av2")
    suf = "" if A.db_part == "train475" else "_" + A.db_part
    dbname = "av2_dbinfos_train.pkl" if A.db_part == "train475" else "av2_dbinfos_%s.pkl" % A.db_part
    GTDatabaseCreater("AV2Dataset", A.root, A.out_rel + "/av2" + suf, info_path=os.path.join(A.out, "av2_infos_%s.pkl" % A.db_part),
                      database_save_path=os.path.join(A.out, "av2%s_gt_database" % suf), db_info_save_path=os.path.join(A.out, dbname),
                      num_worker=A.procs).create()
    db = pickle.load(open(os.path.join(A.out, dbname), "rb"))
    rec = {"classes": {k: len(v) for k, v in db.items()}, "entries": sum(len(v) for v in db.values()), "seconds": time.time() - t0}
    json.dump(rec, open(os.path.join(A.out, dbname.replace(".pkl", "_summary.json")), "w"), indent=1)
    print(json.dumps(rec), flush=True)
    print("GTDB DONE", A.db_part, flush=True)


def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["infos", "gtdb"])
    ap.add_argument("--lt3d", required=True)
    ap.add_argument("--root", required=True, help=".../Sensor (holds train/ and val/)")
    ap.add_argument("--out", required=True, help="absolute info directory = <root>/<out_rel>")
    ap.add_argument("--out-rel", dest="out_rel", default="av2_owndet_infos")
    ap.add_argument("--split")
    ap.add_argument("--part", choices=["train475", "held225", "val150", "prof40"])
    ap.add_argument("--db-part", dest="db_part", default="train475", choices=["train475", "prof40"])
    ap.add_argument("--procs", type=int, default=8)
    A = ap.parse_args()
    sys.path.insert(0, A.lt3d)
    os.chdir(A.lt3d)
    os.makedirs(A.out, exist_ok=True)
    {"infos": cmd_infos, "gtdb": cmd_gtdb}[A.cmd]()


if __name__ == "__main__":
    main()
