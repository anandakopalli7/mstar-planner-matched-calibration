#!/usr/bin/env python3
"""test_av2_horizon_on_nuscenes_v01: av2_horizon_prep_v01 reproduces x1_horizon_prep_v04 exactly, on nuScenes ONLY
(Claude line, 1 Nov 2026). Nothing here touches Argoverse 2.

For each tracker setting (T1 x1_export_val150_fast_v04, T2 m_export_sampletv_v01, T3 m_export_polymot_v01; val worker 0):
  1. a test worker with the first N scenes of the existing export (lines copied unchanged, export record copied);
  2. x1_horizon_prep_v04 run on it (subprocess, from the CANMOT root, as the original runs were);
  3. av2_horizon_prep_v01 --propagate-only run on it (subprocess);
  4. line-by-line string equality of the two outputs (all 8 steps), and equality of h1s/h2s/h4s with the stored horizon
     file of the original study (x1_horizon_v01, horizon_val_v02, horizon_val_v03);
  5. the residual step on nuScenes: av2_horizon_prep_v01.horizon_rows vs x1_lib_v03.build_horizon_rows on the
     x1_lib_v03.build_table rows of those scenes with x1_val_gt_v02 (h1s, h2s, h4s): rows identical.
Usage: python -B test_av2_horizon_on_nuscenes_v01.py --out <dir> [--scenes 3]
"""
import argparse
import gzip
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
CANMOT = os.path.join(W, "50_CODE", "third_party", "CANMOT")
PY = sys.executable
SETTINGS = {
    "t1": ("paper/local/canmot/sc", os.path.join(W, "60_RESULTS", "x1_export_val150_fast_v04", "worker0"),
           os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz")),
    "t2": ("paper/local/sample/trainval", os.path.join(W, "60_RESULTS", "m_export_sampletv_v01", "val", "worker0"),
           os.path.join(W, "60_RESULTS", "m_export_sampletv_v01", "horizon_val_v02.jsonl.gz")),
    "t3": ("paper/baseline/poly_mot", os.path.join(W, "60_RESULTS", "m_export_polymot_v01", "val", "worker0"),
           os.path.join(W, "60_RESULTS", "m_export_polymot_v01", "horizon_val_v03.jsonl.gz")),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--scenes", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    sys.path.insert(0, os.path.join(W, "50_CODE", "x1"))
    import x1_lib_v03 as L
    sys.path.insert(0, HERE)
    import av2_horizon_prep_v01 as H
    samples, gtb, racks = L.load_gt(os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json"))
    report = {"scenes_per_setting": a.scenes, "settings": {}}
    for name, (exp, src, stored) in SETTINGS.items():
        tw = os.path.join(a.out, name, "worker_test")
        os.makedirs(tw, exist_ok=True)
        shutil.copyfile(os.path.join(src, "x1_export_record.json"), os.path.join(tw, "x1_export_record.json"))
        keep, lines = [], []
        with gzip.open(os.path.join(src, "x1_tracks.jsonl.gz"), "rt", encoding="utf-8") as f:
            for line in f:
                sc = json.loads(line)["scene"]
                if sc not in keep:
                    if len(keep) == a.scenes:
                        break
                    keep.append(sc)
                lines.append(line)
        with gzip.open(os.path.join(tw, "x1_tracks.jsonl.gz"), "wt", encoding="utf-8") as f:
            f.writelines(lines)
        ref = os.path.join(a.out, name, "ref_x1_horizon_prep_v04.jsonl.gz")
        mine = os.path.join(a.out, name, "av2_horizon_prep_v01.jsonl.gz")
        r1 = subprocess.run([PY, "-B", os.path.join(W, "50_CODE", "x1", "x1_horizon_prep_v04.py"), "--environment", "my_machine",
                             "--experiment", exp, "--workers", tw, "--out", ref], cwd=CANMOT, capture_output=True, text=True)
        r2 = subprocess.run([PY, "-B", os.path.join(HERE, "av2_horizon_prep_v01.py"), "--experiment", exp, "--workers", tw,
                             "--out", mine, "--propagate-only"], capture_output=True, text=True)
        assert "HORIZON PREP DONE" in r1.stdout and "HORIZON PREP DONE" in r2.stdout, (r1.stderr[-2000:], r2.stderr[-2000:])
        A = gzip.open(ref, "rt").read().splitlines()
        B = gzip.open(mine, "rt").read().splitlines()
        diff = sum(x != y for x, y in zip(A, B)) + abs(len(A) - len(B))
        # stored file of the original study: h1s/h2s/h4s
        keys = {(json.loads(x)["scene"], json.loads(x)["k"], json.loads(x)["tid"]) for x in B}
        stored_map = {}
        with gzip.open(stored, "rt") as f:
            for line in f:
                r = json.loads(line)
                kk = (r["scene"], r["k"], r["tid"])
                if kk in keys:
                    stored_map[kk] = r
        sdiff, scomp = 0, 0
        pred = {}
        for x in B:
            r = json.loads(x)
            kk = (r["scene"], r["k"], r["tid"])
            pred[kk] = r
            s = stored_map.get(kk)
            if s is None:
                sdiff += 1
                continue
            for h in ("h1s", "h2s", "h4s"):
                scomp += 1
                sdiff += int(s[h] != r[h])
        # residual step on nuScenes: horizon_rows (port) vs build_horizon_rows (original) with the reference predictions
        recs = L.load_export(os.path.join(tw, "x1_tracks.jsonl.gz"))
        samp = {t: s for t, s in samples.items() if s["scene"] in keep}
        rows, _ = L.build_table(recs, samp, gtb, racks)
        pred_ref = {}
        for x in A:
            r = json.loads(x)
            pred_ref[(r["scene"], r["k"], r["tid"])] = r
        rdiff, rcount = 0, 0
        for h, steps in (("h1s", 2), ("h2s", 4), ("h4s", 8)):
            ra, sa = H.horizon_rows(rows, pred, samp, gtb, racks, key=h, steps=steps)
            rb, sb = L.build_horizon_rows(rows, pred_ref, samp, gtb, racks, key=h, steps=steps)
            rcount += len(rb)
            rdiff += int(sa != sb) + sum(json.dumps(x, sort_keys=True, default=str) != json.dumps(y, sort_keys=True, default=str)
                                         for x, y in zip(ra, rb)) + abs(len(ra) - len(rb))
        report["settings"][name] = {"experiment": exp, "source_export": src, "scenes": keep, "records": len(B),
                                    "x1_horizon_prep_v04_vs_port_lines_different": diff,
                                    "stored_file": stored, "stored_values_compared": scomp, "stored_values_different": sdiff,
                                    "horizon_rows_compared": rcount, "horizon_rows_different": rdiff,
                                    "identical": diff == 0 and sdiff == 0 and rdiff == 0 and len(B) > 0}
        print(name, report["settings"][name], flush=True)
    report["all_identical"] = all(v["identical"] for v in report["settings"].values())
    with open(os.path.join(a.out, "HORIZON_PORT_TEST_NUSCENES_v01.json"), "w") as f:
        json.dump(report, f, indent=1)
    print("ALL IDENTICAL:", report["all_identical"])


if __name__ == "__main__":
    sys.exit(main())
