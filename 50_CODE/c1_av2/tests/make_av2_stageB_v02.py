#!/usr/bin/env python3
"""Generator of 50_CODE/av2/av2_cache_stageB_v02.py from the tracker helper's av2_cache_stageB_v01.py (not modified), asserted
replacements (R17 M2; D16 v09 Choice 24). v02's guard: a stage-A cache that is AV2-tagged or not recognisably nuScenes is refused
unless --frozen-plan is FROZEN (no [SLOT, non-empty block, sidecar equal to its hash, that hash in C1_PLAN_HASH_LOG.txt) and binds
this script's own hash; a --frozen-plan-sha256 given on the command line must equal the sidecar but is never sufficient. The output
manifest records the plan's sidecar hash and carries a dataset tag. Usage (from 50_CODE/c1_av2): python -B tests/make_av2_stageB_v02.py
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
    s = rep(s, '"""av2_cache_stageB_v01: adds the later ground-truth fields',
            '"""av2_cache_stageB_v02 = av2_cache_stageB_v01 (kept) with the frozen-plan guard of R17 M2 / D16 v09 Choice 24, written by\n'
            'c1_av2/tests/make_av2_stageB_v02.py: AV2-tagged or unrecognised stage-A caches need a FROZEN plan logged in\n'
            '40_PROTOCOL/C1_PLAN_HASH_LOG.txt that binds this script; the output manifest carries the dataset tag and the plan\'s sidecar hash.\n'
            'av2_cache_stageB_v01: adds the later ground-truth fields')
    s = rep(s, "import numpy as np\n",
            "import numpy as np\n\nsys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \"c1_av2\"))\n"
            "import c1_guard_v01 as G  # noqa: E402\n")
    s = rep(s, '    ap.add_argument("--frozen-plan-sha256", default=None)\n',
            '    ap.add_argument("--frozen-plan-sha256", default=None)\n    ap.add_argument("--hash-log", default=G.HASH_LOG)\n')
    s = rep(s, '    if man.get("dataset") == "av2":\n'
               '        if not (a.frozen_plan and a.frozen_plan_sha256 and sha256_path(a.frozen_plan) == a.frozen_plan_sha256):\n'
               '            raise SystemExit("refused: stage B on an AV2 cache needs the frozen plan and its SHA-256 (D16 Choice 13)")\n',
            '    dataset = G.dataset_of_manifest(man)\n'
            '    plan_sha = None\n'
            '    if dataset != "nuscenes":\n'
            '        if not a.frozen_plan:\n'
            '            raise SystemExit("refused: stage B on an AV2 cache needs the frozen C1 plan (D16 Choice 13, v09 Choice 24)")\n'
            '        try:\n'
            '            plan_sha, frozen = G.frozen_plan(a.frozen_plan, a.hash_log)\n'
            '            G.require_bound(frozen, os.path.abspath(__file__))\n'
            '        except AssertionError as e:\n'
            '            raise SystemExit("refused: " + str(e))\n'
            '        if a.frozen_plan_sha256 and a.frozen_plan_sha256 != plan_sha:\n'
            '            raise SystemExit("refused: --frozen-plan-sha256 differs from the frozen plan\'s sidecar")\n')
    s = rep(s, '                          "frozen_plan": a.frozen_plan, "frozen_plan_sha256": a.frozen_plan_sha256}\n',
            '                          "frozen_plan": a.frozen_plan, "frozen_plan_sha256": plan_sha}\n    out_man["dataset"] = dataset\n')
    return s


def main():
    with open(os.path.join(AV2, "av2_cache_stageB_v01.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(AV2, "av2_cache_stageB_v02.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "av2_cache_stageB_v02.py")


if __name__ == "__main__":
    main()
