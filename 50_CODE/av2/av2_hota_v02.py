#!/usr/bin/env python3
"""av2_hota_v02 (v01 never run: v02 stores ego_translation_m as a list, as the av2 evaluator expects, so index_array_values leaves it alone): HOTA with the official av2 tracking evaluator (av2 0.3.6, av2.evaluation.tracking.eval, on TrackEval) for
exports in the x1_export_v06 format (Claude line, 2 Nov 2026; D16 Choice 14). Runs in 50_CODE/env/av2eval310.

The flow is av2.evaluation.tracking.eval.evaluate, step for step, with three documented differences:
  1. classes: the seven tracking classes of the tracker-input mapping (design v01 section 4.2: car = REGULAR_VEHICLE,
     pedestrian = PEDESTRIAN, bicycle = BICYCLIST, motorcycle = MOTORCYCLIST, bus / truck / trailer = their AV2 groups), on
     both the labels and the tracks, instead of the 26 AV2 competition categories (our trackers output those seven);
  2. no region-of-interest filter: the maps were not downloaded (evaluate's dataset_dir = None path, which the evaluator
     supports);
  3. the score-threshold tuning (av2's _tune_score_thresholds: per class 10 recall-based thresholds, objective HOTA) is run
     serially with av2's own _calculate_score_thresholds and _evaluate_single_threshold, instead of in a pool of up to 10
     processes (the laptop is shared).
As in the official evaluator: labels and tracks within 50 m of the ego (filter_max_dist), centre-distance similarity with
zero distance 2 m, HOTA and CLEAR from TrackEval at the tuned per-class thresholds (evaluate_tracking), and the mean of the
objective over the 10 thresholds (the number av2's runner prints). Labels: the annotations of the 2 Hz frames from
av2_gt_prep_v01 with >= 1 interior point (as in our AMOTA protocol), positions in the city frame. Tracking metrics only.
Usage: av2eval310/python -I -B av2_hota_v02.py --gt <av2 gt json> --exports <worker dirs> --label <tag> --out <json>
"""
import argparse
import contextlib
import gzip
import json
import math
import os
import sys
import time
from collections import defaultdict
from functools import partial

import numpy as np

from av2.evaluation.tracking import eval as E
from av2.evaluation.tracking import utils as U

CLASSES = ["car", "pedestrian", "bicycle", "motorcycle", "truck", "bus", "trailer"]
MAX_RANGE_M = 50
NUM_THRESHOLDS = 10


def frames_from(samples, by_sample, label):
    seqs = defaultdict(list)
    for s in sorted(samples.values(), key=lambda s: (s["scene"], s["index"])):
        rows = by_sample.get(s["token"], [])
        n = len(rows)
        f = {"seq_id": s["scene"], "timestamp_ns": int(s["timestamp_ns"]),
             "track_id": np.array([r[0] for r in rows], dtype=object) if n else np.zeros(0, dtype=object),
             "translation_m": np.array([r[1] for r in rows], float).reshape(n, 3),
             "size": np.array([r[2] for r in rows], float).reshape(n, 3),
             "yaw": np.array([r[3] for r in rows], float),
             "velocity_m_per_s": np.zeros((n, 3)),
             "label": np.array([CLASSES.index(r[4]) for r in rows], int),
             "name": np.array([r[4] for r in rows], dtype=object) if n else np.zeros(0, dtype=object),
             "score": np.array([r[5] for r in rows], float)}
        if label:
            f["ego_translation_m"] = [float(v) for v in s["ego_xyz"]]
        seqs[s["scene"]].append(f)
    return dict(sorted(seqs.items()))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--gt", required=True)
    ap.add_argument("--exports", nargs="+", required=True)
    ap.add_argument("--label", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    t0 = time.time()
    g = json.load(open(a.gt))
    samples = {s["token"]: s for s in g["samples"]}
    gl = defaultdict(list)
    for an in g["annotations"]:
        if an["tracking_name"] in CLASSES and an["num_pts"] >= 1:
            w_, l_, h_ = an["size"]
            gl[an["sample_token"]].append((an["instance_token"], an["translation"], [l_, w_, h_], an["yaw"], an["tracking_name"], 1.0))
    del g
    pr = defaultdict(list)
    for w in a.exports:
        rec = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert rec["status_X1_gates"] == "PASS", w
        with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "rt", encoding="utf-8") as f:
            for line in f:
                r = json.loads(line)
                if r["tracking_name"] not in CLASSES:
                    continue
                q = r["rotation"]
                yaw = math.atan2(2.0 * (q[0] * q[3] + q[1] * q[2]), 1.0 - 2.0 * (q[2] * q[2] + q[3] * q[3]))
                w_, l_, h_ = r["size"]
                pr[r["sample_token"]].append((r["tracking_id"], r["translation"], [l_, w_, h_], yaw, r["tracking_name"], float(r["tracking_score"])))
    labels = frames_from(samples, gl, True)
    preds = frames_from(samples, pr, False)
    print("loaded %.0f s" % (time.time() - t0), flush=True)
    # av2 evaluate(), dataset_dir = None
    labels = E.filter_max_dist(labels, MAX_RANGE_M)
    U.annotate_frame_metadata(U.ungroup_frames(preds), U.ungroup_frames(labels), ["ego_translation_m"])
    preds = E.filter_max_dist(preds, MAX_RANGE_M)
    # av2 _tune_score_thresholds, serial
    metrics_config = {"METRICS": ["HOTA"], "THRESHOLD": 0.5, "PRINT_CONFIG": False}
    dataset_config = {**E.TrackEvalDataset.get_default_dataset_config(), "GT_TRACKS": {"tracker": labels},
                      "PREDICTED_TRACKS": {"tracker": preds}, "SEQ_IDS_TO_EVAL": list(labels.keys()), "CLASSES_TO_EVAL": CLASSES,
                      "TRACKERS_TO_EVAL": ["tracker"], "OUTPUT_FOLDER": "tmp"}
    sim_func = partial(E._xy_center_similarity, zero_distance=2)
    thr = {n: E._calculate_score_thresholds(E._filter_by_class(labels, n), E._filter_by_class(preds, n), sim_func,
                                            num_thresholds=NUM_THRESHOLDS) for n in CLASSES}
    results = []
    for i in range(NUM_THRESHOLDS):
        results.append(E._evaluate_single_threshold((i, thr, CLASSES, preds, dataset_config, metrics_config)))
        print("threshold %d/%d %.0f s" % (i + 1, NUM_THRESHOLDS, time.time() - t0), flush=True)
    opt_thr, opt_val, mean_val = {}, {}, {}
    for n in CLASSES:
        v = [r[n]["HOTA"]["HOTA"] for r in results]
        v = [float(np.mean(x)) if isinstance(x, np.ndarray) else float(x) for x in v]
        opt_thr[n] = float(thr[n][int(np.argmax(v))])
        opt_val[n] = max(0.0, float(np.max(v)))
        mean_val[n] = float(np.nanmean(np.array(v).clip(min=0)))
    filt = U.filter_by_class_thresholds(preds, opt_thr)
    outdir = os.path.join(os.path.dirname(os.path.abspath(a.out)), "trackeval_" + a.label)
    os.makedirs(outdir, exist_ok=True)
    with contextlib.redirect_stdout(None):
        res = E.evaluate_tracking(labels, filt, CLASSES, tracker_name="TRACKER", output_dir=outdir)
    comb = res["TrackEvalDataset"]["TRACKER"]["COMBINED_SEQ"]
    per = {}
    for n in CLASSES:
        h, c = comb[n]["HOTA"], comb[n]["CLEAR"]
        per[n] = {"HOTA": float(np.mean(h["HOTA"])), "DetA": float(np.mean(h["DetA"])), "AssA": float(np.mean(h["AssA"])),
                  "LocA": float(np.mean(h["LocA"])), "MOTA_av2": float(c["MOTA"]), "IDSW_av2": int(c["IDSW"]),
                  "CLR_TP": int(c["CLR_TP"]), "CLR_FN": int(c["CLR_FN"]), "CLR_FP": int(c["CLR_FP"]),
                  "tuned_score_threshold": opt_thr[n], "HOTA_at_tuned_threshold_from_tuning": opt_val[n],
                  "HOTA_mean_over_10_thresholds": mean_val[n]}
    out = {"label": a.label, "evaluator": "av2 0.3.6 av2.evaluation.tracking.eval (TrackEval 1.0.dev1, commit 12c8791b)",
           "differences_from_official_runner": ["seven tracking classes instead of the 26 AV2 categories",
                                                 "no ROI filter (no maps)", "threshold tuning run serially"],
           "max_range_m": MAX_RANGE_M, "labels": "AV2 val 2 Hz annotations with >= 1 interior point (av2_gt_prep_v01)",
           "exports": [os.path.abspath(w) for w in a.exports], "per_class": per, "wall_seconds": round(time.time() - t0, 1)}
    json.dump(out, open(a.out, "w"), indent=1)
    print(json.dumps({n: (round(per[n]["HOTA"], 4), round(per[n]["HOTA_mean_over_10_thresholds"], 4)) for n in CLASSES}))
    print("HOTA DONE %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    sys.exit(main())
