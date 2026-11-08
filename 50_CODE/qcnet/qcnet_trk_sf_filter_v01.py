"""qcnet_trk_sf_filter_v01 (QCNet arm, addendum B, 2 Nov 2026): T1's published-track threshold on the matched AB3DMOT rows.

Design: 50_CODE/qcnet/QCNET_AV2_ARM_DESIGN_ADDENDUM_B_v01.md (B2-B4). A matched row (a track updated in that sweep, carrying the
matched detection's score) is kept iff score >= SF_thre[class] in float64, with T1's values (CANMOT config/poly_mot/preprocessing/
centerpoint_nusc.yaml line 1): REGULAR_VEHICLE (car, 2) 0.16, PEDESTRIAN (4) 0.16, BICYCLIST (bicycle, 0) 0.14.
Counts only (rows kept / removed per class, rows exactly at a threshold). Pickle-free in and out. One light process.
Usage: python -I qcnet_trk_sf_filter_v01.py --inp <trk10_ab3dmot_matched_3cls_v02.npz> --out <trk10_ab3dmot_matched_sf_3cls_v03.npz>
"""
import argparse
import json

import numpy as np

SF = {"REGULAR_VEHICLE": 0.16, "PEDESTRIAN": 0.16, "BICYCLIST": 0.14}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    z = np.load(a.inp, allow_pickle=False)
    d = {k: z[k] for k in z.files}
    s = d["score"].astype(np.float64)
    thr = np.full(len(s), np.nan)
    for c, t in SF.items():
        thr[d["name"] == c] = t
    assert not np.isnan(thr).any(), "unexpected class"
    keep = s >= thr
    rec = {"input_rows": int(len(s)), "kept_rows": int(keep.sum()), "removed_rows": int((~keep).sum()), "sf_thre": SF,
           "rows_exactly_at_threshold": int((s == thr).sum()),
           "rows_with_float32_score_equal_to_float32_threshold": int((d["score"] == thr.astype(np.float32)).sum()), "by_class": {}}
    for c in SF:
        m = d["name"] == c
        rec["by_class"][c] = {"input_rows": int(m.sum()), "kept_rows": int((m & keep).sum())}
    np.savez_compressed(a.out, **{k: v[keep] for k, v in d.items()})
    json.dump(rec, open(a.out.replace(".npz", "_filter.json"), "w"), indent=1)
    print(json.dumps(rec), flush=True)


if __name__ == "__main__":
    main()
