"""pod_qcnet_pack_v01 (QCNet arm, 2 Nov 2026): pack the arm's outputs for copy-back and compute its COUNTS.

Outcome-blind (design 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_v01.md section 0): counts, timing jitter, finiteness and
positive-definiteness only. No QCNet output is compared with any ground-truth position.
Sub-commands (numpy + pandas only):
  dets    --tables <out_lt3d10/tables> --out <file.npz>   10 Hz LT3D detections of all classes with score >= 0.1 (a superset of
                                                          both trackers' inputs: AB3DMOT keeps > 0.1, the port floors at 0.1)
  trk     --trk <out_trk10/logs10> --out <file.npz>       the 10 Hz AB3DMOT outputs of all logs in one file (+ log_id), and
                                                          <file>_counts.json: rows, tracks and track lengths per class
  counts  --gt <gt npz> --trkq <trk npz> --out <json>     items per class x history-length stratum per source; join coverage
                                                          between the sources; jitter; finiteness; positive-definiteness
"""
import argparse
import glob
import json
import os

import numpy as np

CLASSES3 = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST")
STRATA = [("1", 1, 1), ("2-5", 2, 5), ("6-15", 6, 15), ("16-49", 16, 49), ("50", 50, 50)]


def save_npz(df, path):
    arrays = {}
    for c in df.columns:
        v = df[c].to_numpy()
        if v.dtype == object:
            v = v.astype(str)
        arrays[c] = v
    np.savez_compressed(path, **arrays)


def cmd_dets(a):
    import pandas as pd
    parts = []
    for p in sorted(glob.glob(os.path.join(a.tables, "*_dts.feather"))):
        df = pd.read_feather(p)
        parts.append(df[df["score"] >= 0.1])
    d = pd.concat(parts, ignore_index=True)
    save_npz(d, a.out)
    rec = {"rows": int(len(d)), "logs": int(d["log_id"].nunique()), "frames": int(d.groupby(["log_id", "timestamp_ns"]).ngroups),
           "per_category": {k: int(v) for k, v in d["category"].value_counts().items()}}
    json.dump(rec, open(a.out.replace(".npz", "_counts.json"), "w"), indent=1)
    print(json.dumps(rec), flush=True)


def cmd_trk(a):
    acc = {}
    for p in sorted(glob.glob(os.path.join(a.trk, "trk10_*.npz"))):
        log = os.path.basename(p)[6:-4]
        z = np.load(p, allow_pickle=False)
        n = len(z["ts"])
        for k in z.files:
            acc.setdefault(k, []).append(z[k])
        acc.setdefault("log_id", []).append(np.full(n, log))
    res = {k: np.concatenate(v) for k, v in acc.items()}
    res["name"] = res["name"].astype(str)
    res["log_id"] = res["log_id"].astype(str)
    np.savez_compressed(a.out, **res)
    rec = {"rows": int(len(res["ts"])), "logs": int(len(np.unique(res["log_id"])))}
    for c in CLASSES3:
        m = res["name"] == c
        key = np.char.add(np.char.add(res["log_id"][m], "|"), res["track_id"][m].astype(str))
        _, cnt = np.unique(key, return_counts=True)
        rec[c] = {"rows": int(m.sum()), "tracks": int(len(cnt)),
                  "track_length_sweeps": {"p10": float(np.percentile(cnt, 10)) if len(cnt) else None, "median": float(np.median(cnt)) if len(cnt) else None,
                                          "p90": float(np.percentile(cnt, 90)) if len(cnt) else None, "max": int(cnt.max()) if len(cnt) else None},
                  "tracks_by_length": {"1": int((cnt == 1).sum()), "2-5": int(((cnt >= 2) & (cnt <= 5)).sum()), "6-20": int(((cnt >= 6) & (cnt <= 20)).sum()),
                                       "21-50": int(((cnt >= 21) & (cnt <= 50)).sum()), ">50": int((cnt > 50).sum())}}
    json.dump(rec, open(a.out.replace(".npz", "_counts.json"), "w"), indent=1)
    print(json.dumps(rec), flush=True)


def source_counts(z):
    out = {"items": int(len(z["sample_token"])), "logs": int(len(np.unique(z["log_id"]))), "origins_with_items": int(len(np.unique(z["sample_token"])))}
    nh = z["n_hist"]
    for c in CLASSES3 + ("ALL",):
        m = np.ones(len(nh), bool) if c == "ALL" else (z["category"] == c)
        out[c] = {"items": int(m.sum()), "vec_valid_now": int((m & z["vec_valid_now"]).sum()), "visible_at_target": int((m & z["vis_target"]).sum()),
                  "by_history_steps": {s: int((m & (nh >= lo) & (nh <= hi)).sum()) for s, lo, hi in STRATA},
                  "visible_at_target_by_history_steps": {s: int((m & z["vis_target"] & (nh >= lo) & (nh <= hi)).sum()) for s, lo, hi in STRATA}}
    j = z["jitter_ms"]
    out["target_jitter_ms"] = {"min": float(j.min()), "p1": float(np.percentile(j, 1)), "median": float(np.median(j)), "p99": float(np.percentile(j, 99)),
                               "max": float(j.max()), "abs_max": float(np.abs(j).max())}
    out["checks"] = {"finite": int(z["finite"].sum()), "pd_modes": int(z["pd_modes"].sum()), "pd_v1": int(z["pd_v1"].sum()), "pd_v2": int(z["pd_v2"].sum()),
                     "rows": int(len(z["finite"])),
                     "pi_rows_sum_to_1": int((np.abs(z["pi"].sum(1) - 1) < 1e-9).sum()),
                     "cov_symmetric": int((np.abs(z["v2_cov"][:, 0, 1] - z["v2_cov"][:, 1, 0]) < 1e-9).sum())}
    na = z["n_agents_scene"]
    out["agents_per_scene_at_items"] = {"median": float(np.median(na)), "max": int(na.max())}
    return out


def cmd_counts(a):
    g = np.load(a.gt, allow_pickle=False)
    t = np.load(a.trkq, allow_pickle=False)
    rec = {"gt_source": source_counts(g), "trk_source": source_counts(t)}
    kg = set(zip(g["sample_token"].tolist(), g["instance_token"].tolist()))
    kt = set(zip(t["sample_token"].tolist(), t["instance_token"].tolist()))
    assert len(kg) == len(g["sample_token"]) and len(kt) == len(t["sample_token"]), "duplicate keys"
    cat_g = dict(zip(zip(g["sample_token"].tolist(), g["instance_token"].tolist()), g["category"].tolist()))
    cat_t = dict(zip(zip(t["sample_token"].tolist(), t["instance_token"].tolist()), t["category"].tolist()))
    both = kg & kt
    rec["join_gt_trk"] = {"gt_keys": len(kg), "trk_keys": len(kt), "both": len(both), "trk_only": len(kt - kg), "gt_only": len(kg - kt),
                          "by_class": {c: {"gt": sum(1 for k in kg if cat_g[k] == c), "trk": sum(1 for k in kt if cat_t[k] == c),
                                           "both": sum(1 for k in both if cat_g[k] == c)} for c in CLASSES3}}
    rec["outcome_statement"] = ("counts, jitter, finiteness and positive-definiteness only; no QCNet output compared with any GT position; "
                                "visible_at_target is existence with num_interior_pts >= 1 at the target sweep")
    json.dump(rec, open(a.out, "w"), indent=1)
    print(json.dumps(rec, indent=1), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["dets", "trk", "counts"])
    ap.add_argument("--tables")
    ap.add_argument("--trk")
    ap.add_argument("--gt")
    ap.add_argument("--trkq")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    {"dets": cmd_dets, "trk": cmd_trk, "counts": cmd_counts}[a.cmd](a)


if __name__ == "__main__":
    main()
