#!/usr/bin/env python3
"""C1 fits v03 (Claude line, c1_fit_v03, 4 Nov 2026) = c1_fit_v02 (kept, imported; every fit unchanged) with D16 v13 Choice 34:
  * the dataset of the data read is decided before any item is loaded, from the folds' units (tag and names must agree) and the item
    files' scene names; nuScenes data may run without a plan; anything else needs --plan, a frozen plan in
    40_PROTOCOL/C1_PLAN_HASH_LOG.txt (no override; --hash-log only for a nuScenes rehearsal), with this file as entry:c1_fit and every
    loaded module bound (c1_guard_v02.guard);
  * under a plan (Choice 34.6): the within folds are bound in the role "folds", and every item file must chain to the plan: its
    summary names caches that are stage B under this plan from a bound stage-A manifest (AV2; built by entry:k8_items), or bound
    nuScenes caches (a rehearsal; built by a bound builder) (c1_guard_v02.chain_items);
  * c1_fit_v02's own guard calls go through c1_guard_v02 (the same dataset, no other log);
  * the output's provenance gains the entry point, every loaded module's hash, the item chains and "inputs_checked".
Usage: as c1_fit_v02 (--hash-log only for nuScenes).
"""
import json
import os
import sys
import types

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v01 as G1  # noqa: E402
import c1_guard_v02 as G  # noqa: E402
import c1_fit_v02 as F2  # noqa: E402

ROLE = "entry:c1_fit"
STATE = {"dataset": None}


def _frozen_plan(plan, hash_log=None):
    log = None if (hash_log is None or os.path.abspath(hash_log) == os.path.abspath(G1.HASH_LOG)) else hash_log
    return G.frozen_plan(plan, STATE["dataset"], log)


SHIM = types.SimpleNamespace(HASH_LOG=G1.HASH_LOG, __file__=G.__file__, units_dataset=G.units_dataset, frozen_plan=_frozen_plan,
                             require_bound=lambda frozen, p: G.require_bound(frozen, p), sha=G.sha)
F2.G = SHIM


def _arg(argv, name, n=1):
    if name not in argv:
        return None
    i = argv.index(name)
    if n == "+":
        out = []
        for x in argv[i + 1:]:
            if x.startswith("--"):
                break
            out.append(x)
        return out
    return argv[i + 1]


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    items, folds, plan, log, out = _arg(argv, "--items", "+"), _arg(argv, "--folds"), _arg(argv, "--plan"), _arg(argv, "--hash-log"), _arg(argv, "--out")
    route = _arg(argv, "--route") or "within"
    fj = json.load(open(folds))
    item_names = []
    for p in items:
        item_names += [str(x) for x in np.load(p, allow_pickle=False)["scene_names"]]
    ds_items = G.units_dataset(item_names)
    ds = G.dataset_checked(fj.get("dataset"), list(fj["fold_of_log"])) if route == "within" else ds_items
    assert ds_items == ds or route != "within", "the items' units (%s) and the folds' (%s) disagree" % (ds_items, ds)
    STATE["dataset"] = ds
    g = G.guard(ds, plan, ROLE, os.path.abspath(__file__), log)
    chains, side, frozen = [], None, None
    if g:
        side, frozen, rt = g
        if route == "within":
            G.require_bound(frozen, folds, "folds")
        chains = [G.chain_items(p, side, frozen) for p in items]
    else:
        rt = G.code_record(os.path.abspath(__file__))
    F2.main(argv)
    if g:
        rt = G.verify_runtime_again(frozen, rt)
    res = json.load(open(out))
    assert res["provenance"]["plan_sha256"] == side, "c1_fit_v02 saw another plan"
    res["provenance"].update({"entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"], "item_chains": chains,
                              "inputs_sha256": {G.rel(p): G.sha(p) for p in items}, "inputs_checked": bool(g), "dataset": ds})
    res["code_sha256"]["c1_fit_v03"] = G.sha(os.path.abspath(__file__))
    tmp = out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(res, f, indent=1)
    os.replace(tmp, out)
    print(json.dumps({"out": os.path.abspath(out), "sha256": G.sha(out), "plan": side, "chains": len(chains)}))
    print("C1 FIT V03 DONE")


if __name__ == "__main__":
    main()
