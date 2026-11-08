#!/usr/bin/env python3
"""Generator of 50_CODE/av2/av2_cache_stageB_v03.py from av2_cache_stageB_v02.py (not modified), asserted replacements (D16 v13
Choice 34; R17b A1, A3, M-a, M-b). v03: no --hash-log (an AV2 cache is checked against 40_PROTOCOL/C1_PLAN_HASH_LOG.txt only; a
nuScenes cache needs no plan); the dataset tag must agree with the scene names (c1_guard_v02.manifest_dataset); the guard is
c1_guard_v02.guard (this file must be the plan's entry:stageB and every loaded module bound); the stage-A manifest must be bound in
the role stageA_manifest and the GT file bound or a stage-A input; the output manifest records the entry point and code hashes.
Usage (from 50_CODE/c1_av2): python -B tests/make_av2_stageB_v03.py
"""
import hashlib
import os

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AV2 = os.path.join(os.path.dirname(C1), "av2")


def rep(s, old, new):
    assert s.count(old) == 1, "expected one occurrence of %r" % old[:90]
    return s.replace(old, new)


def make(src):
    s = src
    s = rep(s, '"""av2_cache_stageB_v02 = av2_cache_stageB_v01 (kept)',
            '"""av2_cache_stageB_v03 = av2_cache_stageB_v02 (kept) with D16 v13 Choice 34, written by c1_av2/tests/make_av2_stageB_v03.py:\n'
            'no hash-log override (AV2: 40_PROTOCOL/C1_PLAN_HASH_LOG.txt only); tag and scene names must agree; c1_guard_v02.guard (entry:stageB,\n'
            'every loaded module bound); the stage-A manifest bound as stageA_manifest; the GT file bound or a stage-A input.\n'
            'av2_cache_stageB_v02 = av2_cache_stageB_v01 (kept)')
    s = rep(s, "import c1_guard_v01 as G  # noqa: E402\n", "import c1_guard_v02 as G  # noqa: E402\n")
    s = rep(s, '    ap.add_argument("--hash-log", default=G.HASH_LOG)\n', "")
    s = rep(s, "    dataset = G.dataset_of_manifest(man)\n    plan_sha = None\n", "    dataset = G.manifest_dataset(man)\n    plan_sha, rt = None, None\n")
    s = rep(s, "            plan_sha, frozen = G.frozen_plan(a.frozen_plan, a.hash_log)\n"
               "            G.require_bound(frozen, os.path.abspath(__file__))\n",
            '            plan_sha, frozen, rt = G.guard(dataset, a.frozen_plan, "entry:stageB", os.path.abspath(__file__))\n'
            '            G.require_bound(frozen, os.path.join(a.stage_a, "MANIFEST.json"), "stageA_manifest")\n'
            "            G.check_inputs(frozen, [a.gt])\n")
    s = rep(s, '    out_man["stage_note"] = "stage B: gt_x, gt_y, gt_yaw, gt_w, gt_l filled from the GT table by av2_cache_stageB_v01"\n',
            '    out_man["stage_note"] = "stage B: gt_x, gt_y, gt_yaw, gt_w, gt_l filled from the GT table by av2_cache_stageB_v03"\n')
    s = rep(s, '    out_man["dataset"] = dataset\n',
            '    out_man["dataset"] = dataset\n'
            '    out_man["stage_b"]["code"] = G.verify_runtime_again(frozen, rt) if rt else G.code_record(os.path.abspath(__file__))\n')
    return s


def main():
    with open(os.path.join(AV2, "av2_cache_stageB_v02.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(AV2, "av2_cache_stageB_v03.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "av2_cache_stageB_v03.py")


if __name__ == "__main__":
    main()
