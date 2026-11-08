#!/usr/bin/env python3
"""C1 fits v06 (Claude line, c1_fit_v06, 5 Nov 2026) = c1_fit_v05 (copied) on c1_guard_v05 (D16 v23 Choice 44f): on AV2 the guard writes a chained 'start' line to 40_PROTOCOL/C1_RUN_LOG.txt before any
ground truth or table is read and the 'done' line is chained to it (m1); the deposit record must not name the OSF project and the
plan's log line must carry a parsable time (m2); stale c1_gt_* temporary folders are swept (m7). Otherwise unchanged.
C1 fits v05 (Claude line, c1_fit_v05, 4 Nov 2026) = c1_fit_v04 (kept) on c1_guard_v04 (D16 v21 Choice 42): on AV2 the validated
deposit record (guard, role entry:c1_fit), an existing output refused, one run-log line; deposit_record_sha256 in the provenance.
C1 fits v04 (Claude line, c1_fit_v04, 4 Nov 2026) = c1_fit_v03's wrapper logic on c1_guard_v03, around c1_fit_v02's fits (imported;
every fit unchanged), with R17c's fixes and D16 v17 Choice 38d:
  * guard v03: the latest line of 40_PROTOCOL/C1_PLAN_HASH_LOG.txt only, FROZEN_ENV versions asserted, the log hash recorded; this
    file as entry:c1_fit; every loaded module bound. c1_fit_v02's main() (Choice 36 rule 3) accepts AV2 data only after this guard
    has passed in this process for the same plan (c1_guard_v03.LAST_GUARD).
  * --route within: --folds bound in any folds role ("folds", or "folds_val150" for the 150-log descriptive routes), recorded.
  * --route source (Choice 38d): fitted once on the units of --folds, bound as folds_train225 (the 225 held-out AV2 train logs, items
    chained to the plan's stage-B caches), applied to the units of --apply-folds, bound as folds_val150; the two unit sets must be
    disjoint and the child folds must be restrictions of the bound parent. It runs c1_fit_v02's transfer mechanism (one fit, fold '0')
    and is labelled route "source"; the output records source_units, applied_units and both folds roles.
  * --route transfer: the pre-freeze nuScenes transfer fit, as c1_fit_v02.
  * provenance: entry point, every loaded module, item chains, inputs, dataset, folds role(s), the hash log's hash, versions.
Usage: python -B c1_fit_v04.py --items <npz ...> --folds <json> --out <json> [--route within|source|transfer --apply-folds <json>]
       [--plan <frozen plan>] [--hash-log <file>: nuScenes rehearsal only] [--units-subset]
"""
import json
import os
import sys
import types

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v01 as G1  # noqa: E402
import c1_guard_v05 as G  # noqa: E402
import c1_fit_v02 as F2  # noqa: E402

ROLE = "entry:c1_fit"
STATE = {"dataset": None}


def _frozen_plan(plan, hash_log=None):
    log = None if (hash_log is None or os.path.abspath(hash_log) == os.path.abspath(G1.HASH_LOG)) else hash_log
    return G.frozen_plan(plan, STATE["dataset"], log)


F2.G = types.SimpleNamespace(HASH_LOG=G1.HASH_LOG, __file__=G.__file__, units_dataset=G.units_dataset, frozen_plan=_frozen_plan,
                             require_bound=lambda frozen, p: G.require_bound(frozen, p), sha=G.sha)


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


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    items, folds, plan, log, out = _arg(argv, "--items", True), _arg(argv, "--folds"), _arg(argv, "--plan"), _arg(argv, "--hash-log"), _arg(argv, "--out")
    route = _arg(argv, "--route") or "within"
    apply_folds = _arg(argv, "--apply-folds")
    assert route in ("within", "source", "transfer"), "unknown route " + route
    fj = json.load(open(folds))
    item_names = []
    for p in items:
        item_names += [str(x) for x in np.load(p, allow_pickle=False)["scene_names"]]
    ds_items = G.units_dataset(item_names)
    ds_folds = G.folds_dataset(fj)
    if route in ("within", "source"):
        assert ds_items == ds_folds, "the items' units (%s) and the folds' (%s) disagree" % (ds_items, ds_folds)
    ds = ds_folds if route in ("within", "source") else ds_items
    STATE["dataset"] = ds
    G.refuse_existing([out], ds)
    g = G.guard(ds, plan, ROLE, os.path.abspath(__file__), log)
    chains, side, frozen, roles = [], None, None, {}
    if route == "source":
        assert apply_folds, "--route source needs --apply-folds (the folds_val150 units it is applied to)"
        af = json.load(open(apply_folds))
        src_u, app_u = set(fj["fold_of_log"]), set(af["fold_of_log"])
        assert not (src_u & app_u), "a source fit with validation units in training is refused: %s" % sorted(src_u & app_u)[:3]
        assert G.folds_dataset(af) == ds, "the applied folds' dataset differs"
    if g:
        side, frozen, rt = g
        if route == "within":
            roles["folds"] = G.require_folds(frozen, folds, ("folds", "folds_val150"))[0]
        elif route == "source":
            G.require_bound(frozen, folds, "folds_train225")
            G.require_bound(frozen, apply_folds, "folds_val150")
            G.check_child_folds(folds, frozen)
            G.check_child_folds(apply_folds, frozen)
            roles = {"folds": "folds_train225", "apply_folds": "folds_val150"}
        chains = [G.chain_items(p, side, frozen) for p in items]
    else:
        rt = G.code_record(os.path.abspath(__file__))
    argv2 = list(argv)
    if route == "source":
        argv2[argv2.index("--route") + 1] = "transfer"
    F2.main(argv2)
    if g:
        rt = G.verify_runtime_again(frozen, rt)
    res = json.load(open(out))
    assert res["provenance"]["plan_sha256"] == side, "c1_fit_v02 saw another plan"
    if route == "source":
        res["route"] = "source"
        res["source_units"] = sorted(fj["fold_of_log"])
        res["applied_units"] = sorted(json.load(open(apply_folds))["fold_of_log"])
        res["source_folds_sha256"] = G.sha(folds)
    res["provenance"].update({"entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"], "item_chains": chains,
                              "inputs_sha256": {G.rel(p): G.sha(p) for p in items}, "inputs_checked": bool(g), "dataset": ds,
                              "folds_roles": roles, "route": route, "hash_log_sha256": rt.get("hash_log_sha256"), "versions": rt["versions"],
                              "deposit_record_sha256": rt.get("deposit_record_sha256", "exempt (%s)" % ds)})
    res["code_sha256"]["c1_fit_v05"] = G.sha(os.path.abspath(__file__))
    tmp = out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f, indent=1)
    os.replace(tmp, out)
    if g:
        G.run_log_append(ds, os.path.abspath(__file__), side, rt["deposit_record_sha256"], {G.rel(p): G.sha(p) for p in items}, [out])
    print(json.dumps({"out": os.path.abspath(out), "sha256": G.sha(out), "plan": side, "route": route, "chains": len(chains)}))
    print("C1 FIT V06 DONE")


if __name__ == "__main__":
    main()
