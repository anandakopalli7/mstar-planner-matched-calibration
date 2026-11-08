#!/usr/bin/env python3
"""av2_cache_stageB_v04 = av2_cache_stageB_v03 (kept) on c1_guard_v03 (R17c M1, m5), written by c1_av2/tests/make_av2_stageB_v04.py:
the latest line of 40_PROTOCOL/C1_PLAN_HASH_LOG.txt only; FROZEN_ENV versions asserted; the log hash recorded; and D16 v19 Choice 40:
an AV2 cache needs the deposit record 40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt naming the frozen plan (no override), checked
before any ground truth is read; its sha256 goes into stage_b.deposit_record_sha256. nuScenes is exempt.
av2_cache_stageB_v03 = av2_cache_stageB_v02 (kept) with D16 v13 Choice 34, written by c1_av2/tests/make_av2_stageB_v03.py:
no hash-log override (AV2: 40_PROTOCOL/C1_PLAN_HASH_LOG.txt only); tag and scene names must agree; c1_guard_v02.guard (entry:stageB,
every loaded module bound); the stage-A manifest bound as stageA_manifest; the GT file bound or a stage-A input.
av2_cache_stageB_v02 = av2_cache_stageB_v01 (kept) with the frozen-plan guard of R17 M2 / D16 v09 Choice 24, written by
c1_av2/tests/make_av2_stageB_v02.py: AV2-tagged or unrecognised stage-A caches need a FROZEN plan logged in
40_PROTOCOL/C1_PLAN_HASH_LOG.txt that binds this script; the output manifest carries the dataset tag and the plan's sidecar hash.
av2_cache_stageB_v01: adds the later ground-truth fields to a stage-A cache (Claude line, 2 Nov 2026). Design:
AV2_TRACKER_PORT_DESIGN_v02.md section 12.3; D16_DELEGATED_CHOICES_v03.md Choice 13 ("Stage B adds those fields by a script
that is hash-bound in the frozen plan, and runs only after the freeze").

For every scene of a stage-A cache it rebuilds the ground-truth row order of k6_cache_v02 / av2_cache_stageA_v01 (keyframes in
order, annotations in the GT file's order, instance index = rank of the instance token among the scene's tokens), asserts that
gt_k, gt_inst, gt_cls and gt_pts equal the stage-A values row for row, fills gt_x, gt_y, gt_yaw, gt_w, gt_l from the GT table
(translation[0], translation[1], yaw, size[0], size[1]), copies every other array unchanged, and writes a new cache with
stage "B" in its manifest. Guard: on a stage-A cache whose manifest says dataset "av2" it refuses to run unless
--frozen-plan is given and its SHA-256 equals --frozen-plan-sha256. Tested on nuScenes only
(test_av2_stageAB_on_nuscenes_v01.py: the result equals 30_DATA/k6/cache_v02_* field for field).
Usage: python -B av2_cache_stageB_v01.py --stage-a <dir> --gt <gt json> --out <dir> [--frozen-plan <file> --frozen-plan-sha256 <hex>]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "c1_av2"))
import c1_guard_v03 as G  # noqa: E402

CLASSES = ["car", "truck", "bus", "trailer", "pedestrian", "motorcycle", "bicycle"]


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage-a", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--frozen-plan", default=None)
    ap.add_argument("--frozen-plan-sha256", default=None)
    a = ap.parse_args()
    t0 = time.time()
    man = json.load(open(os.path.join(a.stage_a, "MANIFEST.json")))
    assert man.get("stage") == "A", "not a stage-A cache"
    dataset = G.manifest_dataset(man)
    plan_sha, rt, deposit = None, None, None
    if dataset != "nuscenes":
        if not a.frozen_plan:
            raise SystemExit("refused: stage B on an AV2 cache needs the frozen C1 plan (D16 Choice 13, v09 Choice 24)")
        try:
            plan_sha, frozen, rt = G.guard(dataset, a.frozen_plan, "entry:stageB", os.path.abspath(__file__))
            G.require_bound(frozen, os.path.join(a.stage_a, "MANIFEST.json"), "stageA_manifest")
            G.check_inputs(frozen, [a.gt])
            deposit = G.check_deposit(plan_sha, dataset)
        except AssertionError as e:
            raise SystemExit("refused: " + str(e))
        if a.frozen_plan_sha256 and a.frozen_plan_sha256 != plan_sha:
            raise SystemExit("refused: --frozen-plan-sha256 differs from the frozen plan's sidecar")
    g = json.load(open(a.gt))
    kf = defaultdict(dict)
    for s in g["samples"]:
        kf[s["scene"]][s["index"]] = s
    by_sample = defaultdict(list)
    for an in g["annotations"]:
        by_sample[an["sample_token"]].append(an)
    os.makedirs(a.out, exist_ok=True)
    out_man = dict(man)
    out_man["scenes"] = {}
    for scene, info in sorted(man["scenes"].items()):
        p = os.path.join(a.stage_a, scene + ".npz")
        assert sha256_path(p) == info["sha256"], "stage-A file differs from its manifest: " + p
        z = np.load(p)
        arr = {k: z[k] for k in z.files}
        K = len(arr["kf_t"])
        assert sorted(kf[scene]) == list(range(K))
        insts = sorted({an["instance_token"] for k in range(K) for an in by_sample.get(kf[scene][k]["token"], [])})
        iidx = {t: i for i, t in enumerate(insts)}
        rows = [an for k in range(K) for an in by_sample.get(kf[scene][k]["token"], [])]
        kk = [k for k in range(K) for _ in by_sample.get(kf[scene][k]["token"], [])]
        n = len(rows)
        assert n == len(arr["gt_k"]), "row count differs: " + scene
        assert np.array_equal(arr["gt_k"], np.array(kk, dtype=arr["gt_k"].dtype)), scene
        assert np.array_equal(arr["gt_inst"], np.array([iidx[an["instance_token"]] for an in rows], dtype=arr["gt_inst"].dtype)), scene
        assert np.array_equal(arr["gt_cls"], np.array([CLASSES.index(an["tracking_name"]) for an in rows], dtype=arr["gt_cls"].dtype)), scene
        assert np.array_equal(arr["gt_pts"], np.array([an["num_pts"] for an in rows], dtype=arr["gt_pts"].dtype)), scene
        if n:
            arr["gt_x"] = np.array([an["translation"][0] for an in rows], dtype=float)
            arr["gt_y"] = np.array([an["translation"][1] for an in rows], dtype=float)
            arr["gt_yaw"] = np.array([an["yaw"] for an in rows], dtype=float)
            arr["gt_w"] = np.array([an["size"][0] for an in rows], dtype=float)
            arr["gt_l"] = np.array([an["size"][1] for an in rows], dtype=float)
        q = os.path.join(a.out, scene + ".npz")
        np.savez_compressed(q, **arr)
        d = dict(info)
        d["sha256"] = sha256_path(q)
        out_man["scenes"][scene] = d
    out_man["stage"] = "B"
    out_man["stage_note"] = "stage B: gt_x, gt_y, gt_yaw, gt_w, gt_l filled from the GT table by av2_cache_stageB_v04"
    out_man["stage_b"] = {"stage_a": os.path.abspath(a.stage_a), "stage_a_manifest_sha256": sha256_path(os.path.join(a.stage_a, "MANIFEST.json")),
                          "gt": os.path.abspath(a.gt), "gt_sha256": sha256_path(a.gt), "script_sha256": sha256_path(os.path.abspath(__file__)),
                          "frozen_plan": a.frozen_plan, "frozen_plan_sha256": plan_sha}
    out_man["dataset"] = dataset
    out_man["stage_b"]["deposit_record_sha256"] = deposit["sha256"] if deposit else "exempt (%s)" % dataset
    out_man["stage_b"]["deposit"] = deposit
    out_man["stage_b"]["code"] = G.verify_runtime_again(frozen, rt) if rt else G.code_record(os.path.abspath(__file__))
    json.dump(out_man, open(os.path.join(a.out, "MANIFEST.json"), "w"), indent=1)
    print("STAGE B DONE", len(out_man["scenes"]), "scenes %.0f s" % (time.time() - t0))


if __name__ == "__main__":
    sys.exit(main())
