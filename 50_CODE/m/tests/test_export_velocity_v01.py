#!/usr/bin/env python3
"""Export-level velocity check (Claude line, v01, 31 Oct 2026; R07b N-C1). Tracker output only: no ground truth is read.
For each setting's val export, with the velocity as m_data_v03 uses it:
- per class, the median |velocity - displacement / time| over moving records is reported. Moving means a displacement
  speed of at least 3 m/s to the next keyframe of the same track. For pedestrians and trailers that set is dominated by
  position jumps in every setting (CANMOT included), so no absolute limit is used.
- criterion 1: the corrected loader equals x1_lib_v03.load_export field for field on the CANMOT settings;
- criterion 2: for the CTRA classes (car, bus, truck, pedestrian), T3's corrected error is at most T1's error + 0.5 m/s;
- criterion 3: for cars, T3's uncorrected error exceeds 2 m/s (the bug is real) and the corrected one is below 1.5 m/s.
Usage: python test_export_velocity_v01.py --setting T1 <val worker dirs...> --setting T3 <...> --out <json>
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import m_data_v03 as MD  # noqa: E402

EXP = {"T1": "paper/local/canmot/sc", "T2": "paper/local/sample/trainval", "T3": "paper/baseline/poly_mot"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--setting", nargs="+", action="append", required=True, help="tag followed by worker directories")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out, ok = {}, {}
    specs = [(s[0], s[1:], EXP[s[0]]) for s in a.setting] + [("T3raw", s[1:], None) for s in a.setting if s[0] == "T3"]
    for tag, workers, exp in specs:
        recs, fixed = [], 0
        for w in workers:
            rw, fw = MD.load_export_v2(os.path.join(w, "x1_tracks.jsonl.gz"), exp)
            recs += rw
            fixed += fw
            if tag in ("T1", "T2"):
                ref = MD.L.load_export(os.path.join(w, "x1_tracks.jsonl.gz"))
                ok["%s_identical_to_x1_loader_%s" % (tag, os.path.basename(w))] = ref == rw
        by = {(r["scene"], r["tid"], r["k"]): r for r in recs}
        err = defaultdict(list)
        for (sc, tid, k), r in by.items():
            n = by.get((sc, tid, k + 1))
            if n is None:
                continue
            dvx, dvy = (n["x"] - r["x"]) / 0.5, (n["y"] - r["y"]) / 0.5
            if math.hypot(dvx, dvy) >= 3.0:
                err[r["name"]].append(math.hypot(r["vx"] - dvx, r["vy"] - dvy))
        med = {c: float(np.median(v)) for c, v in err.items() if len(v) >= 20}
        out[tag] = {"records": len(recs), "ctra_corrected": fixed, "median_abs_error_mps_by_class": med,
                    "n_moving_by_class": {c: len(v) for c, v in err.items()}}
    m1, m3, m3r = (out[t]["median_abs_error_mps_by_class"] for t in ("T1", "T3", "T3raw"))
    ok["T3_ctra_classes_as_consistent_as_T1"] = all(m3[c] <= m1[c] + 0.5 for c in ("car", "bus", "truck", "pedestrian"))
    ok["T3_car_bug_real_and_fixed"] = m3r["car"] > 2.0 and m3["car"] < 1.5
    ok = {k: bool(v) for k, v in ok.items()}
    out["ok"], out["all_ok"] = ok, all(ok.values())
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    sys.exit(main())
