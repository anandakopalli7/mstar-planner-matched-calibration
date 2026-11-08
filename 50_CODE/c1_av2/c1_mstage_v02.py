#!/usr/bin/env python3
"""C1 method stage v02 (Claude line, c1_mstage_v02, 4 Nov 2026) = c1_mstage_v01 (kept, imported; statistics unchanged) made resumable
(researcher rule of 4 Nov: save the work as it is done, never restart a whole experiment). The method stage is the longest C1 step
(E1-AV2: 20 repetitions and 200 refit-CV replicates; E2-AV2: 1000 two-sample refits), so:
  * E1 and E2 are checkpointed separately as soon as each finishes: <out>.E1.ckpt.json and <out>.E2.ckpt.json, written to a temporary
    file, flushed and renamed atomically; each carries a key (tracker, sizes, seeds, exact-CRC flag, the code hash, the input-file
    hashes); a rerun with the same arguments reuses a checkpoint whose key matches and computes only what is missing;
  * a step log <out>.steps.jsonl records each part's start and end (UTC, seconds);
  * the final JSON is assembled from the checkpoints and equals v01's output for the same inputs (E1 holds H6b's p-value).
Usage: as c1_mstage_v01 (same arguments).
"""
import hashlib
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_mstage_v01 as V1  # noqa: E402

M, R = V1.M, V1.R


def _sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _atomic(path, obj):
    tmp = path + ".tmp"
    with open(tmp, "w") as f:
        json.dump(obj, f, indent=1, default=float)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def _step(path, rec):
    with open(path, "a") as f:
        f.write(json.dumps(dict(rec, utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))) + "\n")
        f.flush()
        os.fsync(f.fileno())


def run_resumable(av2, train, tracker, reps, B, BR, B2, out, key, h="h2s"):
    ai, arc = av2[h]
    ti, trc = train[h]
    m_a = M.motion_state(ai)
    c1, c2 = M.make_cells(ai, m_a, "E1"), M.make_cells(ai, m_a, "E2")
    steps = out + ".steps.jsonl"
    parts = {}
    for part in ("E1", "E2"):
        ck = "%s.%s.ckpt.json" % (out, part)
        if os.path.exists(ck):
            d = json.load(open(ck))
            if d.get("key") == key and d.get("complete") is True:
                parts[part] = d["result"]
                _step(steps, {"part": part, "event": "reused"})
                continue
        _step(steps, {"part": part, "event": "start"})
        t0 = time.time()
        if part == "E1":
            V1.CAPTURE.clear()
            e1 = R.run_e1(ai, arc, {}, av2["_names"], av2["_slog"], c1, "%s|E1-AV2|%s" % (tracker, h), B=B, reps=reps, refit_B=BR)
            p, per = V1.h6b_pvalue(e1["refit"], {m: V1.CAPTURE["cells"][m] for m in ("B4", "Mstar")})
            res = {"E1": e1, "H6b_p": p, "H6b_detail": per, "cells_E1": [n for n, _ in c1]}
        else:
            res = {"E2": R.run_e2(ti, trc, ai, arc, {}, c2, "%s|E2-AV2|%s" % (tracker, h), B=B2), "cells_E2": [n for n, _ in c2]}
        _atomic(ck, {"key": key, "complete": True, "result": res})
        _step(steps, {"part": part, "event": "end", "seconds": round(time.time() - t0, 1)})
        parts[part] = res
    out_d = dict(parts["E1"])
    out_d.update(parts["E2"])
    return out_d


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--experiment", required=True)
    for p in ("av2", "train"):
        ap.add_argument("--%s-workers" % p, nargs="+", required=True)
        ap.add_argument("--%s-gt" % p, required=True)
        ap.add_argument("--%s-meta" % p, required=True)
        ap.add_argument("--%s-horizon" % p, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--reps", type=int, default=M.R_CV)
    ap.add_argument("--boot", type=int, default=M.B_BOOT)
    ap.add_argument("--refit-boot", type=int, default=M.B_E1R)
    ap.add_argument("--e2-boot", type=int, default=M.B_REFIT)
    ap.add_argument("--float-crc", action="store_true")
    ap.add_argument("--m-seeds", action="store_true")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_mstage_v02", "c1_mstage_v04", {"AV2-set exports": LEGACY.ds_exports(a.av2_workers),
                                                  "training exports": LEGACY.ds_exports(a.train_workers)})
    if not a.test:
        assert (a.reps, a.boot, a.refit_boot, a.e2_boot) == (M.R_CV, M.B_BOOT, M.B_E1R, M.B_REFIT) and not (a.float_crc or a.m_seeds), \
            "the confirmatory sizes and seeds are fixed"
    V1.configure(exact=not a.float_crc, c1_seeds=not a.m_seeds)
    inputs = [a.av2_gt, a.av2_horizon, a.train_gt, a.train_horizon] + [os.path.join(w, "x1_export_record.json") for w in a.av2_workers + a.train_workers]
    key = {"tracker": a.tracker, "experiment": a.experiment, "sizes": [a.reps, a.boot, a.refit_boot, a.e2_boot], "seed_base": M.SEED,
           "exact_crc": not a.float_crc, "code": {"v02": _sha(os.path.abspath(__file__)), "v01": _sha(V1.__file__)},
           "inputs": {os.path.basename(p): _sha(p) for p in inputs}}
    t0 = time.time()
    av2 = V1.load(a.av2_workers, a.av2_gt, a.av2_meta, a.av2_horizon, a.experiment)
    train = V1.load(a.train_workers, a.train_gt, a.train_meta, a.train_horizon, a.experiment)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    res = run_resumable(av2, train, a.tracker, a.reps, a.boot, a.refit_boot, a.e2_boot, a.out, key)
    res.update({"tracker": a.tracker, "seeds": {"base": M.SEED, "e1_folds": "base + r", "refit": "base + 1000 + b"}, "exact_crc": not a.float_crc,
                "sizes": {"reps": a.reps, "B": a.boot, "refit_B": a.refit_boot, "e2_B": a.e2_boot}, "test_mode": bool(a.test),
                "checkpoint_key": key, "seconds": round(time.time() - t0, 1)})
    _atomic(a.out, res)
    print(json.dumps({"H6a": res["E1"]["hypotheses"]["HM1"], "H6b_p": res["H6b_p"], "H7": res["E2"]["hypotheses"]["HM6"]}))
    print("C1 MSTAGE V02 DONE")


if __name__ == "__main__":
    main()
