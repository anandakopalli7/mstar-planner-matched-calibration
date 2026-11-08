#!/usr/bin/env python3
"""C1 QCNet run summary (Claude line, c1_qcnet_summary_v01, 4 Nov 2026; D16 v21 Choice 42e, R17d M3 §3h). Writes the run summary that
c1_predarm_v05 --q1-only requires for each QCNet file (deployed or ground-truth histories): it aligns the QCNet rows to the keys' records
by (rec_sample_token, rec_instance_token), as c1_predarm_v01.qcnet_runs does, and records
  keys_sha256, out_sha256 (the QCNet file), records, not_predicted (key records without a finite, positive-definite QCNet row),
  checkpoint_commit, recentring, history_source (given by the lead from the QCNet run's own notes), source (deployed | gt),
  and, under a plan, the plan hash, the entry point, the code record and the deposit record.
It reads no ground truth: the keys' geometry and tokens and QCNet's predictions only. On AV2 it is guarded (entry:c1_qcnet_summary; the
validated deposit record, as the keys come from the stage-B cache); an existing output is refused and one run-log line is appended.
Usage: python -B c1_qcnet_summary_v01.py --keys <npz> --qcnet <npz> --source deployed|gt --checkpoint-commit <s> --recentring <s>
       --history-source <s> --out <json> [--plan <frozen plan>] [--hash-log <file>: nuScenes only] [--synthetic]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v04 as G  # noqa: E402

ROLE = "entry:c1_qcnet_summary"
SYN_STAMP = "SYNTHETIC: generated test data, not nuScenes"


def coverage(qz, kz):
    idx = {(str(s), str(i)): r for r, (s, i) in enumerate(zip(qz["sample_token"], qz["instance_token"]))}
    miss = 0
    for key in zip(kz["rec_sample_token"], kz["rec_instance_token"]):
        r = idx.get((str(key[0]), str(key[1])))
        if r is None or not (bool(qz["finite"][r]) and bool(qz["pd_v2"][r])):
            miss += 1
    return int(len(kz["rec_sample_token"])), miss


def main(argv=None):
    ap = argparse.ArgumentParser()
    for x in ("--keys", "--qcnet", "--checkpoint-commit", "--recentring", "--history-source", "--out"):
        ap.add_argument(x, required=True)
    ap.add_argument("--source", required=True, choices=["deployed", "gt"])
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None)
    ap.add_argument("--synthetic", action="store_true")
    a = ap.parse_args(argv)
    kz = np.load(a.keys, allow_pickle=False)
    names = [str(x) for x in kz["scene_names"]]
    ds = "synthetic" if (a.synthetic and "stamp" in kz.files and str(kz["stamp"]) == SYN_STAMP) else G.dataset_checked(None, names)
    G.refuse_existing([a.out], ds)
    g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log) if ds != "synthetic" else None
    n, miss = coverage(np.load(a.qcnet, allow_pickle=False), kz)
    rt = G.verify_runtime_again(g[1], g[2]) if g else G.code_record(os.path.abspath(__file__))
    out = {"rule": "D16 v21 Choice 42e: QCNet rows aligned to the keys' records by (sample_token, instance_token)", "source": a.source,
           "keys_sha256": G.sha(a.keys), "out_sha256": G.sha(a.qcnet), "qcnet_file": G.rel(a.qcnet), "records": n, "not_predicted": miss,
           "checkpoint_commit": a.checkpoint_commit, "recentring": a.recentring, "history_source": a.history_source, "dataset": ds,
           "units": G.units_record(names), "plan_sha256": g[0] if g else None, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
           "deposit_record_sha256": rt.get("deposit_record_sha256", "exempt (%s)" % ds), "hash_log_sha256": rt.get("hash_log_sha256")}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".tmp", "w") as f:
        json.dump(out, f, indent=1)
    os.replace(a.out + ".tmp", a.out)
    if g:
        G.run_log_append(ds, os.path.abspath(__file__), g[0], rt["deposit_record_sha256"], {"keys": out["keys_sha256"], "qcnet": out["out_sha256"]}, [a.out])
    print(json.dumps({"records": n, "not_predicted": miss, "source": a.source}))
    print("C1 QCNET SUMMARY DONE")


if __name__ == "__main__":
    main()
