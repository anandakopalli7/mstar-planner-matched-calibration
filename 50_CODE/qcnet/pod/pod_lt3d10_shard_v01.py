"""pod_lt3d10_shard_v01 (QCNet arm, 2 Nov 2026): run LT3D's tools/test.py as K processes on one GPU, each on a contiguous
shard of the 10 Hz infos, and merge their outputs back into the single prediction list tools/test.py would have written.

Why: LT3D's CenterHead.get_task_detections builds its one-hot score matrix with a Python loop and a .item() per box, so one
test.py process runs at 0.9 sweeps/s with the RTX 3090 6-14 % busy (ETA 7.3 h for 23,547 sweeps). Inference is per sweep
(batch size 1, no state across sweeps), so K contiguous shards give the same per-sweep outputs in the same order.
  split  --infos <pkl> --k K --out-prefix P   -> P_shard<i>.pkl (contiguous; concatenation equals the input list)
  merge  --k K --pred-prefix Q --out <pkl>    -> concatenation of Q_shard<i>.pkl (mmcv.dump, as tools/test.py --out)
Runs in the LT3D venv (merge needs mmdet3d importable to unpickle the box objects of our own outputs).
"""
import argparse
import pickle


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "merge"])
    ap.add_argument("--infos")
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--out-prefix", dest="out_prefix")
    ap.add_argument("--pred-prefix", dest="pred_prefix")
    ap.add_argument("--out")
    ap.add_argument("--lt3d")
    a = ap.parse_args()
    if a.cmd == "split":
        infos = pickle.load(open(a.infos, "rb"))
        n = len(infos)
        bounds = [round(i * n / a.k) for i in range(a.k + 1)]
        tot = 0
        for i in range(a.k):
            part = infos[bounds[i]:bounds[i + 1]]
            tot += len(part)
            with open("%s_shard%d.pkl" % (a.out_prefix, i), "wb") as f:
                pickle.dump(part, f)
            print("shard", i, len(part), flush=True)
        assert tot == n
        print("SHARD SPLIT DONE", n, flush=True)
    else:
        import sys
        if a.lt3d:
            sys.path.insert(0, a.lt3d)
        import mmcv
        out = []
        for i in range(a.k):
            part = mmcv.load("%s_shard%d.pkl" % (a.pred_prefix, i))
            print("shard", i, len(part), flush=True)
            out += part
        mmcv.dump(out, a.out)
        print("SHARD MERGE DONE", len(out), flush=True)


if __name__ == "__main__":
    main()
