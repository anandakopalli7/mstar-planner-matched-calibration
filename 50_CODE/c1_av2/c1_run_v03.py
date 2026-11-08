#!/usr/bin/env python3
"""C1 episode runner v03 (Claude line, c1_run_v03, 4 Nov 2026) = c1_run_v02 (kept, imported; the simulation, shards, --resume and
records unchanged) with D16 v13 Choice 34. v03 runs the C1 modes only (--c1-folds, with --c1-plan or --standin):
  * the caches' dataset is read from their manifests first (tag and scene names must agree, c1_guard_v02.manifest_dataset);
    --standin accepts nuScenes caches only and no plan; a confirmatory run needs --c1-plan, a frozen plan in
    40_PROTOCOL/C1_PLAN_HASH_LOG.txt (--hash-log only for nuScenes caches), this file as entry:c1_run, every loaded module bound;
  * under the plan (Choice 34.6): the folds bound as "folds"; every cache chained (AV2: stage B under this plan, built by
    entry:stageB from a bound stage-A manifest; nuScenes: the manifest bound); within fits made by the plan's entry:c1_fit under
    this plan and these folds with bound code; transfer fits whose source is bound in the role "transfer_fits";
  * c1_run_v02's guard calls go through c1_guard_v02 (the same dataset; no other log);
  * the run record gains "provenance_v03": plan, folds, entry point, every loaded module's hash, the cache chains, the fits check.
Usage: as c1_run_v02 with --c1-folds (--hash-log only for nuScenes caches).
"""
import json
import os
import sys
import types

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v01 as G1  # noqa: E402
import c1_guard_v02 as G  # noqa: E402
import c1_run_v02 as R2  # noqa: E402

ROLE = "entry:c1_run"
STATE = {"dataset": None}


def _frozen_plan(plan, hash_log=None):
    log = None if (hash_log is None or os.path.abspath(hash_log) == os.path.abspath(G1.HASH_LOG)) else hash_log
    return G.frozen_plan(plan, STATE["dataset"], log)


R2.G = types.SimpleNamespace(HASH_LOG=G1.HASH_LOG, __file__=G.__file__, frozen_plan=_frozen_plan, dataset_of_manifest=G.manifest_dataset,
                             require_bound=lambda frozen, p: G.require_bound(frozen, p), units_dataset=G.units_dataset)


def _arg(argv, name, many=False):
    if name not in argv:
        return None
    i = argv.index(name)
    if many:
        out = []
        for x in argv[i + 1:]:
            if x.startswith("--"):
                break
            out.append(x)
        return out
    return argv[i + 1]


def check_fits(fits, side, frozen, folds_sha):
    fj = json.load(open(fits))
    assert fj.get("folds_sha256") == folds_sha, "the fits were not made for these folds"
    if fj.get("route") == "transfer":
        assert G.bound_in_role(frozen, fj.get("transfer_fit_source_sha256"), "transfer_fits"), "the transfer fit's source is not bound as transfer_fits"
        return {"route": "transfer", "source_sha256": fj["transfer_fit_source_sha256"]}
    prov = fj.get("provenance") or {}
    ep = prov.get("entry_point") or {}
    assert prov.get("plan_sha256") == side and len(ep) == 1, "the fits were not made under this frozen plan by a named entry point"
    p, h = list(ep.items())[0]
    assert (frozen.roles or {}).get("entry:c1_fit") == [p] and frozen.get(p) == h, "the fits were not made by the plan's entry:c1_fit"
    bad = [q for q, x in (prov.get("code_sha256") or {}).items() if frozen.get(q) != x]
    assert prov.get("code_sha256") and not bad, "fit code not bound: %s" % bad
    assert prov.get("inputs_checked") is True and prov.get("item_chains"), "the fits' items were not chained to the plan"
    return {"route": "within", "entry_point": p}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    caches, fits, folds = _arg(argv, "--caches", True), _arg(argv, "--fits"), _arg(argv, "--c1-folds")
    plan, log, out, tag, standin = _arg(argv, "--c1-plan"), _arg(argv, "--hash-log"), _arg(argv, "--out"), _arg(argv, "--tag"), "--standin" in argv
    assert folds, "c1_run_v03 runs the C1 modes only (--c1-folds); K8 modes are k8_run_v04's"
    dsets = {G.manifest_dataset(json.load(open(os.path.join(c, "MANIFEST.json")))) for c in caches}
    ds = dsets.pop() if len(dsets) == 1 else "mixed"
    STATE["dataset"] = ds
    prov = None
    if standin:
        assert ds == "nuscenes" and plan is None and log is None, "--standin: nuScenes caches, no plan, no log"
    else:
        side, frozen, rt = G.guard(ds, plan, ROLE, os.path.abspath(__file__), log)
        folds_sha = G.require_bound(frozen, folds, "folds")
        chains = [G.chain_cache(os.path.join(c, "MANIFEST.json"), side, frozen) for c in caches]
        fits_check = check_fits(fits, side, frozen, folds_sha)
        prov = {"plan_sha256": side, "folds_sha256": folds_sha, "cache_chains": chains, "fits_check": fits_check, "dataset": ds}
    sys.argv = [R2.__file__] + argv
    R2.main()
    rp = os.path.join(out, "run_record_%s.json" % tag)
    rec = json.load(open(rp))
    if prov is not None:
        rt = G.verify_runtime_again(frozen, rt)
        prov.update({"entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"]})
        assert rec.get("c1_plan_sha256") == side, "c1_run_v02 saw another plan"
    rec["provenance_v03"] = prov if prov is not None else {"standin": True, "dataset": ds, **G.code_record(os.path.abspath(__file__))}
    tmp = rp + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rec, f, indent=1)
    os.replace(tmp, rp)
    print("C1 RUN V03 DONE")


if __name__ == "__main__":
    main()
