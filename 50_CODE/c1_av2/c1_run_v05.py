#!/usr/bin/env python3
"""C1 episode runner v05 (Claude line, c1_run_v05, 4 Nov 2026) = c1_run_v04 (kept) on c1_guard_v04 (D16 v21 Choice 42): on AV2 the
validated deposit record (guard, role entry:c1_run), an existing final run record refused (shards are kept, so a crashed run resumes),
one run-log line; the record's "provenance_v05" adds deposit_record_sha256.
C1 episode runner v04 (Claude line, c1_run_v04, 4 Nov 2026) = c1_run_v03's wrapper logic on c1_guard_v03, around c1_run_v02's runner
(imported; simulation, shards, --resume and records unchanged), with R17c's fixes and D16 v17 Choice 38d:
  * guard v03 (latest log line, FROZEN_ENV, log hash recorded); this file as entry:c1_run; c1_run_v02's main() (Choice 36 rule 3) accepts
    AV2 caches only after this guard has passed in this process for the same plan (c1_guard_v03.LAST_GUARD);
  * --c1-folds may be bound in any folds role (folds, folds_val150, folds_train225), recorded; a child folds file must be a
    restriction of the bound parent (c1_guard_v03.check_child_folds);
  * every cache chained to the plan, and (R17c m3) every cache's dataset must equal the folds' dataset;
  * fits: within or source fits made by the plan's entry:c1_fit under this plan (source fits: source units = folds_train225's,
    applied units = these folds' units); transfer fits whose source is bound as transfer_fits;
  * the run record gains "provenance_v04".
Usage: as c1_run_v02 with --c1-folds (--hash-log only for nuScenes caches).
"""
import json
import os
import sys
import types

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v01 as G1  # noqa: E402
import c1_guard_v04 as G  # noqa: E402
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


def check_fits(fits, side, frozen, folds_sha, folds_path):
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
    if fj.get("route") == "source":
        tp, _ = G.role_hash(frozen, "folds_train225")
        train = sorted(json.load(open(os.path.join(G.W, tp)))["fold_of_log"])
        assert fj.get("source_units") == train, "source fit not trained on the folds_train225 units"
        assert fj.get("applied_units") == sorted(json.load(open(folds_path))["fold_of_log"]), "source fit not applied to these folds' units"
        assert not set(train) & set(fj["applied_units"]), "a source fit with validation units in training"
    return {"route": fj.get("route"), "entry_point": p}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    caches, fits, folds = _arg(argv, "--caches", True), _arg(argv, "--fits"), _arg(argv, "--c1-folds")
    plan, log, out, tag, standin = _arg(argv, "--c1-plan"), _arg(argv, "--hash-log"), _arg(argv, "--out"), _arg(argv, "--tag"), "--standin" in argv
    assert folds, "c1_run_v04 runs the C1 modes only (--c1-folds); K8 modes are k8_run_v04's"
    dsets = {G.manifest_dataset(json.load(open(os.path.join(c, "MANIFEST.json")))) for c in caches}
    ds = dsets.pop() if len(dsets) == 1 else "mixed"
    STATE["dataset"] = ds
    prov = None
    if standin:
        assert ds == "nuscenes" and plan is None and log is None, "--standin: nuScenes caches, no plan, no log"
    else:
        G.refuse_existing([os.path.join(out, "run_record_%s.json" % tag)], ds)
        side, frozen, rt = G.guard(ds, plan, ROLE, os.path.abspath(__file__), log)
        role, folds_sha = G.require_folds(frozen, folds)
        child = G.check_child_folds(folds, frozen) if role != "folds" else None
        fds = G.folds_dataset(json.load(open(folds)))
        chains = [G.chain_cache(os.path.join(c, "MANIFEST.json"), side, frozen) for c in caches]
        assert all(c["dataset"] == fds for c in chains), "a cache's dataset differs from the folds' dataset (R17c m3)"
        fits_check = check_fits(fits, side, frozen, folds_sha, folds)
        prov = {"plan_sha256": side, "folds_sha256": folds_sha, "folds_role": role, "child_folds": child, "cache_chains": chains,
                "fits_check": fits_check, "dataset": ds, "hash_log_sha256": rt["hash_log_sha256"], "versions": rt["versions"],
                "deposit_record_sha256": rt["deposit_record_sha256"]}
    sys.argv = [R2.__file__] + argv
    R2.main()
    rp = os.path.join(out, "run_record_%s.json" % tag)
    rec = json.load(open(rp))
    if prov is not None:
        rt = G.verify_runtime_again(frozen, rt)
        prov.update({"entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"]})
        assert rec.get("c1_plan_sha256") == side, "c1_run_v02 saw another plan"
    rec["provenance_v05"] = prov if prov is not None else {"standin": True, "dataset": ds, **G.code_record(os.path.abspath(__file__))}
    tmp = rp + ".tmp"
    with open(tmp, "w") as f:
        json.dump(rec, f, indent=1)
    os.replace(tmp, rp)
    if prov is not None:
        G.run_log_append(ds, os.path.abspath(__file__), side, rt["deposit_record_sha256"], {"fits": G.sha(fits), "folds": G.sha(folds)}, [rp])
    print("C1 RUN V05 DONE")


if __name__ == "__main__":
    main()
