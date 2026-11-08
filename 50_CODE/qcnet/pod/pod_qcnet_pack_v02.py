"""pod_qcnet_pack_v02 (QCNet arm, addendum A, 2 Nov 2026): counts of the rerun (design addendum A3). Outcome-blind: counts,
distributions of track and history lengths, join coverage, finiteness / positive-definiteness, and an output-against-output
comparison of the city-coordinate and re-centred GT runs. No QCNet output is compared with any ground-truth position.
Sub-commands:
  trk     --trk <dir of trk10_<log>.npz> --out <file.npz>     merge the matched tracker logs (+ log_id) and their per-log meta
  counts  --gt-rc --trk-rc --gt-city --trk-released --trk-matched --trk-released-tracks --keys-t1 --keys-t3 --out <json>
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
CLASSES3 = ("REGULAR_VEHICLE", "PEDESTRIAN", "BICYCLIST")
LEN_BINS = [("1", 1, 1), ("2-5", 2, 5), ("6-20", 6, 20), ("21-50", 21, 50), ("51-100", 51, 100), (">100", 101, 10 ** 9)]


def q(v):
    v = np.asarray(v, np.float64)
    if len(v) == 0:
        return None
    return {"p10": float(np.percentile(v, 10)), "median": float(np.median(v)), "p90": float(np.percentile(v, 90)), "p99": float(np.percentile(v, 99)), "max": float(v.max()), "mean": float(v.mean())}


def cmd_trk(a):
    acc, metas = {}, []
    for p in sorted(glob.glob(os.path.join(a.trk, "trk10_*.npz"))):
        log = os.path.basename(p)[6:-4]
        z = np.load(p, allow_pickle=False)
        for k in z.files:
            acc.setdefault(k, []).append(z[k])
        acc.setdefault("log_id", []).append(np.full(len(z["ts"]), log))
        metas.append(json.load(open(p.replace(".npz", ".json"))))
    res = {k: np.concatenate(v) for k, v in acc.items()}
    res["name"] = res["name"].astype(str); res["log_id"] = res["log_id"].astype(str)
    np.savez_compressed(a.out, **res)
    m = {"logs": len(metas), "rows": int(len(res["ts"])), "rows_held_back_by_min_hits": sum(x["rows_held_back_by_min_hits"] for x in metas),
         "topk_binding_sweeps": sum(x["topk_binding_sweeps"] for x in metas), "dets_in_3cls_after_filter": sum(x["dets_in_3cls_after_filter"] for x in metas),
         "cpu_seconds": sum(x["seconds"] for x in metas)}
    json.dump(m, open(a.out.replace(".npz", "_meta.json"), "w"), indent=1)
    print(json.dumps(m), flush=True)


def track_lengths(z):
    out = {}
    for c in CLASSES3:
        m = z["name"] == c
        key = np.char.add(np.char.add(z["log_id"][m], "|"), z["track_id"][m].astype(str))
        _, cnt = np.unique(key, return_counts=True)
        out[c] = {"rows": int(m.sum()), "tracks": int(len(cnt)), "length_sweeps": q(cnt),
                  "tracks_by_length": {lab: int(((cnt >= lo) & (cnt <= hi)).sum()) for lab, lo, hi in LEN_BINS}}
    return out


def hist_lengths(z):
    out = {}
    for c in CLASSES3 + ("ALL",):
        m = np.ones(len(z["n_hist"]), bool) if c == "ALL" else z["category"] == c
        nh = z["n_hist"][m]
        out[c] = {"items": int(m.sum()), "n_hist": q(nh), "histogram_1_to_50": np.bincount(nh, minlength=51)[1:].tolist(),
                  "full_50_share": float((nh == 50).mean()) if len(nh) else None}
    out["agents_per_scene"] = q(z["n_agents_scene"])
    return out


def cmd_counts(a):
    import pod_qcnet_pack_v01 as P1
    g = np.load(a.gt_rc, allow_pickle=False)
    t = np.load(a.trk_rc, allow_pickle=False)
    gc = np.load(a.gt_city, allow_pickle=False)
    tr = np.load(a.trk_released, allow_pickle=False)
    rec = {"gt_recentred": P1.source_counts(g), "matched_recentred": P1.source_counts(t)}
    rec["history_length"] = {"gt_recentred": hist_lengths(g), "matched_recentred": hist_lengths(t), "released_city_v01": hist_lengths(tr)}
    tm = np.load(a.trk_matched, allow_pickle=False)
    trl = np.load(a.trk_released_tracks, allow_pickle=False)
    rec["track_length"] = {"matched": track_lengths(tm), "released_v01": track_lengths(trl)}
    keys = {"gt_recentred": set(zip(g["sample_token"].tolist(), g["instance_token"].tolist())),
            "matched_recentred": set(zip(t["sample_token"].tolist(), t["instance_token"].tolist())),
            "released_city_v01": set(zip(tr["sample_token"].tolist(), tr["instance_token"].tolist()))}
    rec["join_sources"] = {"gt": len(keys["gt_recentred"]), "matched": len(keys["matched_recentred"]), "gt_and_matched": len(keys["gt_recentred"] & keys["matched_recentred"]),
                           "released": len(keys["released_city_v01"]), "gt_and_released": len(keys["gt_recentred"] & keys["released_city_v01"]),
                           "gt_and_matched_and_released": len(keys["gt_recentred"] & keys["matched_recentred"] & keys["released_city_v01"])}
    rec["join_2hz_audit"] = {}
    for tname, path in (("t1", a.keys_t1), ("t3", a.keys_t3)):
        z = np.load(path, allow_pickle=False)
        tab = {}
        for tok, inst, grp, inp, hz in zip(z["sample_token"].tolist(), z["instance_token"].tolist(), z["group"].tolist(), z["inpath"].tolist(), z["horizon"].tolist()):
            if hz != "available":
                continue
            for lab in ("ALL|all", "%s|all" % grp, "%s|%s" % (grp, "inpath" if inp else "not_inpath")):
                d = tab.setdefault(lab, {"audit": 0, "gt": 0, "matched": 0, "released": 0, "gt_and_matched": 0})
                d["audit"] += 1
                ig, im, ir = (tok, inst) in keys["gt_recentred"], (tok, inst) in keys["matched_recentred"], (tok, inst) in keys["released_city_v01"]
                d["gt"] += ig; d["matched"] += im; d["released"] += ir; d["gt_and_matched"] += ig and im
        rec["join_2hz_audit"][tname] = dict(sorted(tab.items()))
    # city-coordinate vs re-centred GT run (output against output)
    ic = {k: i for i, k in enumerate(zip(gc["sample_token"].tolist(), gc["instance_token"].tolist()))}
    pairs = [(i, ic[k]) for i, k in enumerate(zip(g["sample_token"].tolist(), g["instance_token"].tolist())) if k in ic]
    ii = np.array([p[0] for p in pairs]); jj = np.array([p[1] for p in pairs])
    dmu = np.linalg.norm(g["v2_mu"][ii] - gc["v2_mu"][jj], axis=1)
    dpi = np.abs(g["pi"][ii] - gc["pi"][jj]).max(1)
    dcov = np.abs(g["v2_cov"][ii] - gc["v2_cov"][jj]).max((1, 2))
    rec["city_vs_recentred_gt"] = {"items_compared": int(len(pairs)), "v2_mu_shift_m": q(dmu), "pi_max_abs_diff": q(dpi), "v2_cov_max_abs_diff_m2": q(dcov),
                                   "v1_mode_changed_share": float((g["v1_mode"][ii] != gc["v1_mode"][jj]).mean())}
    rec["outcome_statement"] = ("counts, distributions, join coverage, checks and an output-against-output comparison only; "
                                "no QCNet output compared with any GT position")
    json.dump(rec, open(a.out, "w"), indent=1)
    print(json.dumps({"join_sources": rec["join_sources"], "city_vs_recentred_gt": rec["city_vs_recentred_gt"]}, indent=1), flush=True)
    print("COUNTS DONE", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["trk", "counts"])
    ap.add_argument("--trk"); ap.add_argument("--out", required=True)
    ap.add_argument("--gt-rc", dest="gt_rc"); ap.add_argument("--trk-rc", dest="trk_rc"); ap.add_argument("--gt-city", dest="gt_city")
    ap.add_argument("--trk-released", dest="trk_released"); ap.add_argument("--trk-matched", dest="trk_matched")
    ap.add_argument("--trk-released-tracks", dest="trk_released_tracks"); ap.add_argument("--keys-t1", dest="keys_t1"); ap.add_argument("--keys-t3", dest="keys_t3")
    a = ap.parse_args()
    {"trk": cmd_trk, "counts": cmd_counts}[a.cmd](a)


if __name__ == "__main__":
    main()
