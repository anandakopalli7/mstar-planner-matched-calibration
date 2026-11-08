"""pod_qcnet_pack_v03 (QCNet arm, addendum B, 2 Nov 2026): inputs and counts for the matched + SF run.
Outcome-blind: counts, distributions, join coverage, finiteness / positive-definiteness only.
Sub-commands:
  split   --trk <trk10_ab3dmot_matched_sf_3cls_v03.npz> --out <dir>      one trk10_<log>.npz per log (log_id dropped)
  sweeps  --manifest <v01 fetch manifest csv> --out <sweeps_by_log.json>   lidar sweep timestamps per log (as pod_ab3dmot10_v02 prep)
  counts  --sf-rc <QCNet npz> --gt-rc <v02 GT npz> --matched-rc <v02 matched npz> --trk-sf <trk npz> --keys-t1 --keys-t3 --out <json>
"""
import argparse
import csv
import json
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def cmd_split(a):
    z = np.load(a.trk, allow_pickle=False)
    d = {k: z[k] for k in z.files}
    os.makedirs(a.out, exist_ok=True)
    logs = np.unique(d["log_id"])
    for lg in logs:
        m = d["log_id"] == lg
        np.savez(os.path.join(a.out, "trk10_%s.npz" % lg), **{k: v[m] for k, v in d.items() if k != "log_id"})
    print("logs", len(logs), "rows", int(len(d["ts"])), "SPLIT DONE", flush=True)


def cmd_sweeps(a):
    sweeps = {}
    with open(a.manifest) as f:
        for row in csv.DictReader(f):
            k = row["key"]
            if "/sensors/lidar/" in k and k.endswith(".feather"):
                sweeps.setdefault(k.split("/")[4], []).append(int(os.path.basename(k).split(".")[0]))
    sweeps = {lg: sorted(v) for lg, v in sweeps.items()}
    json.dump(sweeps, open(a.out, "w"))
    print("logs", len(sweeps), "sweeps", sum(len(v) for v in sweeps.values()), "SWEEPS DONE", flush=True)


def cmd_counts(a):
    import pod_qcnet_pack_v01 as P1
    import pod_qcnet_pack_v02 as P2
    s = np.load(a.sf_rc, allow_pickle=False)
    g = np.load(a.gt_rc, allow_pickle=False)
    m = np.load(a.matched_rc, allow_pickle=False)
    t = np.load(a.trk_sf, allow_pickle=False)
    rec = {"matched_sf_recentred": P1.source_counts(s), "history_length_matched_sf": P2.hist_lengths(s), "track_length_matched_sf": P2.track_lengths(t)}
    ks = set(zip(s["sample_token"].tolist(), s["instance_token"].tolist()))
    kg = set(zip(g["sample_token"].tolist(), g["instance_token"].tolist()))
    km = set(zip(m["sample_token"].tolist(), m["instance_token"].tolist()))
    rec["join_sources"] = {"matched_sf": len(ks), "gt": len(kg), "matched": len(km), "gt_and_matched_sf": len(kg & ks),
                           "matched_and_matched_sf": len(km & ks), "matched_sf_not_in_matched": len(ks - km), "gt_and_matched_and_matched_sf": len(kg & km & ks)}
    rec["join_2hz_audit"] = {}
    for tname, path in (("t1", a.keys_t1), ("t3", a.keys_t3)):
        z = np.load(path, allow_pickle=False)
        tab = {}
        for tok, inst, grp, inp, hz in zip(z["sample_token"].tolist(), z["instance_token"].tolist(), z["group"].tolist(), z["inpath"].tolist(), z["horizon"].tolist()):
            if hz != "available":
                continue
            for lab in ("ALL|all", "%s|all" % grp, "%s|%s" % (grp, "inpath" if inp else "not_inpath")):
                d = tab.setdefault(lab, {"audit": 0, "matched_sf": 0, "gt_and_matched_sf": 0})
                d["audit"] += 1
                isf = (tok, inst) in ks
                d["matched_sf"] += isf
                d["gt_and_matched_sf"] += isf and ((tok, inst) in kg)
        rec["join_2hz_audit"][tname] = dict(sorted(tab.items()))
    rec["outcome_statement"] = "counts, distributions, join coverage and checks only; no QCNet output compared with any GT position"
    json.dump(rec, open(a.out, "w"), indent=1)
    print(json.dumps({"items": rec["matched_sf_recentred"]["items"], "join_sources": rec["join_sources"]}), flush=True)
    print("COUNTS DONE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["split", "sweeps", "counts"])
    ap.add_argument("--trk"); ap.add_argument("--out", required=True); ap.add_argument("--manifest")
    ap.add_argument("--sf-rc", dest="sf_rc"); ap.add_argument("--gt-rc", dest="gt_rc"); ap.add_argument("--matched-rc", dest="matched_rc")
    ap.add_argument("--trk-sf", dest="trk_sf"); ap.add_argument("--keys-t1", dest="keys_t1"); ap.add_argument("--keys-t3", dest="keys_t3")
    a = ap.parse_args()
    {"split": cmd_split, "sweeps": cmd_sweeps, "counts": cmd_counts}[a.cmd](a)


if __name__ == "__main__":
    main()
