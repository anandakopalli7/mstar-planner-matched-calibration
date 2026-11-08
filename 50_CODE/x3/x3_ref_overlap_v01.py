#!/usr/bin/env python3
"""x3_ref_overlap_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan section 2 (d): descriptive comparison of the alternative references with the record (no fit, no outcome rate):
  * the reference progression itself: lead_ref - lead_d0 (m) at 0.5, 1, 1.5 and 2 s over all decision states (quantiles);
  * the relied items: a relied item is keyed by (log, keyframe, step, track row); per reference, the share of the record's relied items
    that are also relied at that reference, on the same axis, and with the same side of separation (sign of D unchanged, i.e. D equal).
Usage: python -B x3_ref_overlap_v01.py
"""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402

TIDX = {"0.5 s": 1, "1 s": 3, "1.5 s": 5, "2 s": 7}


def relied(z):
    s, k, h, pair, a, D = (z["item_" + f] for f in ("s", "k", "h", "pair", "a", "D"))
    rel = z["item_ref_relied"]
    rk = z["rec_s"].astype(np.int64) * 10_000_000 + z["rec_pair"]
    o = np.argsort(rk)
    ik = s.astype(np.int64) * 10_000_000 + pair
    ri = o[np.searchsorted(rk[o], ik)]
    assert np.array_equal(rk[ri], ik)
    row = z["rec_row"][ri]
    key = ((s[rel].astype(np.int64) * 100 + k[rel]) * 10 + h[rel]) * 1_000_000 + row[rel]
    return key, a[rel], D[rel]


def main():
    out = {"stamp": C.STAMP, "trackers": {}}
    for t in ("t1", "t3"):
        z0 = np.load(os.path.join(C.D_REF, "items_x3ref_d0_%s.npz" % t))
        k0, a0, D0 = relied(z0)
        o0 = np.argsort(k0)
        res = {}
        for r in ("d1", "d2"):
            z = np.load(os.path.join(C.D_REF, "items_x3ref_%s_%s.npz" % (r, t)))
            assert np.array_equal(z["x3_ref_k"], z0["x3_ref_k"]) and np.array_equal(z["x3_ref_scene"], z0["x3_ref_scene"])
            dl = z["x3_ref_lead"] - z0["x3_ref_lead"]
            lead = {lab: {q: float(np.quantile(dl[:, i], qq)) for q, qq in (("q01", 0.01), ("q10", 0.1), ("median", 0.5), ("q90", 0.9), ("q99", 0.99))}
                    | {"share_equal": float(np.mean(dl[:, i] == 0.0)), "mean_abs": float(np.mean(np.abs(dl[:, i])))} for lab, i in TIDX.items()}
            k1, a1, D1 = relied(z)
            o1 = np.argsort(k1)
            pos = np.searchsorted(k1[o1], k0)
            pos = np.minimum(pos, len(k1) - 1)
            hit = k1[o1][pos] == k0
            j = o1[pos]
            same_axis = hit & (a1[j] == a0)
            same_side = same_axis & (D1[j] == D0)
            res[r] = {"reference_minus_logged_m": lead, "record_relied_items": int(len(k0)), "relied_items_at_reference": int(len(k1)),
                      "share_record_relied_also_relied": float(hit.mean()), "share_same_axis": float(same_axis.mean()),
                      "share_same_axis_and_side": float(same_side.mean()),
                      "share_same_axis_side_flipped": float((same_axis & (D1[j] == -D0) & (D0 != 0)).mean())}
        out["trackers"][t] = res
        print(t, json.dumps({r: {k: v for k, v in x.items() if k != "reference_minus_logged_m"} for r, x in res.items()}))
        print(t, json.dumps({r: x["reference_minus_logged_m"]["2 s"] for r, x in res.items()}))
    out["code_sha256"] = C.code_record([os.path.abspath(__file__), C.__file__])
    C.save_json(os.path.join(C.D_REF, "overlap_x3ref_v01.json"), out)


if __name__ == "__main__":
    main()
