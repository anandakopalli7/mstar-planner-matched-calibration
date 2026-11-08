#!/usr/bin/env python3
"""C1 E0 v03 (Claude line, c1_e0_v03, 4 Nov 2026) = c1_e0_v02 (kept) on c1_guard_v03, with R17c m2 and m7: the seed must be
c1_e0_v01.SEED (20261114) and the mode "c1" (mode "x1", X1's reproduction, only on nuScenes exports); the export dataset is read from
x1_tracks.jsonl.gz; the log hash and versions are recorded under a plan.
C1 E0 v02 (Claude line, c1_e0_v02, 4 Nov 2026) = c1_e0_v01 (kept, imported; the E0 rule, draws and values unchanged) with D16 v13
Choice 34.2's exception and R17b m-6:
  * nuScenes exports (outcome-free dataset check: x1_per_frame scene names and the record's tag) run without a plan;
  * BEFORE the freeze, AV2 exports need --stageA-manifests: every manifest must say stage "A" (a stage-B manifest is refused) and
    every input file (x1_tracks per worker, the GT file, the horizon file) must be one of their recorded inputs; scene.json (the
    scene-to-log map, no annotation) is hashed and recorded;
  * AFTER the freeze, --plan runs the full guard (entry:c1_e0, canonical log, every module bound, inputs bound or stage-A inputs);
  * the output records every input's hash ("inputs_sha256", m-6), the code record and the mode of the check, so that c1_analyse_v05
    can tell changed inputs from a changed value.
Usage: python -B c1_e0_v02.py --workers <dirs> --gt <json> --meta <dir> --horizon <jsonl.gz> --out <json> [--mode c1|x1] [--seed s]
       [--stageA-manifests <MANIFEST.json ...>] [--plan <frozen plan>] [--hash-log <file>: nuScenes only]
"""
import argparse
import json
import os
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v03 as G  # noqa: E402
import c1_e0_v01 as E1  # noqa: E402

ROLE = "entry:c1_e0"
SEED, DECISION_CELLS, PRIMARY_SIGMA = E1.SEED, E1.DECISION_CELLS, E1.PRIMARY_SIGMA


def input_files(workers, gt, horizon):
    return [os.path.join(w, "x1_tracks.jsonl.gz") for w in workers] + [gt, horizon]


def input_hashes(workers, gt, meta, horizon):
    return {G.rel(f): G.sha(f) for f in input_files(workers, gt, horizon) + [os.path.join(meta, "scene.json")]}


def compute(workers, gt, meta, horizon, mode="c1", seed=SEED):
    return E1.compute(workers, gt, meta, horizon, mode, seed)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mode", choices=["c1", "x1"], default="c1")
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--stageA-manifests", nargs="*", default=[])
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None)
    a = ap.parse_args(argv)
    ds = G.export_dataset(a.workers)
    assert a.seed == SEED, "E0's seed is fixed at %d (R17c m2; D16 Choice 39d)" % SEED
    assert a.mode == "c1" or ds == "nuscenes", "mode x1 (X1's reproduction) on nuScenes exports only (R17c m2)"
    files = input_files(a.workers, a.gt, a.horizon)
    side = None
    if a.plan:
        side, frozen, rt = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        G.check_inputs(frozen, files)
        check = "frozen plan"
    elif ds != "nuscenes":
        assert a.stageA_manifests, "AV2 exports before the freeze: --stageA-manifests (stage A only) are required (Choice 34.2)"
        assert a.hash_log is None, "no hash log without a plan"
        ds_m, _ = G.stage_a_only(a.stageA_manifests, files)
        assert ds_m == ds, "the stage-A manifests' dataset (%s) differs from the exports' (%s)" % (ds_m, ds)
        rt = G.code_record(os.path.abspath(__file__))
        check = "pre-freeze, stage-A inputs only"
    else:
        rt = G.code_record(os.path.abspath(__file__))
        check = "nuScenes, unguarded"
    out = compute(a.workers, a.gt, a.meta, a.horizon, a.mode, a.seed)
    if a.plan:
        rt = G.verify_runtime_again(frozen, rt)
    out["inputs_sha256"] = input_hashes(a.workers, a.gt, a.meta, a.horizon)
    out["stageA_manifests_sha256"] = {G.rel(m): G.sha(m) for m in a.stageA_manifests}
    out["check"] = check
    out["dataset"] = ds
    out["plan_sha256"] = side
    out["code"] = rt
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    print(json.dumps({"H8_E0_primary": out["H8_E0_primary"], "seed": out["seed"], "check": check}))
    print("C1 E0 V03 DONE")


if __name__ == "__main__":
    main()
