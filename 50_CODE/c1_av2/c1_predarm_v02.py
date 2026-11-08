#!/usr/bin/env python3
"""C1 predictor arms v02 (Claude line, c1_predarm_v02, 4 Nov 2026) = c1_predarm_v01 (kept, imported; join, scoring, cross-fitting and
H9's rule unchanged) with D16 v13 Choices 34 and 35 (R17b A2, B, M-d):
  * Choice 35: H9's population is the K8 relied in-path items (PD), scored on the K8 tracker-planner's constraints (the item's
    toward-ego normal and sign from the tracker, as K8 and D17; plan section 11.4 is to be corrected to say so). A unit of the keys
    outside the folds is an ERROR (v01 tabled it with NaN thresholds, counted as no exceedance), and so is a non-finite D or variance
    of any used item (v01 inherited tpp_analyse_v01's silent NaN);
  * guard (c1_guard_v02): the keys' units (scene names) and the cache manifest the keys name are read first (no outcome); nuScenes or
    synthetic keys run without a plan; anything else needs --plan (canonical log, entry:c1_predarm, every module bound);
  * chain under a plan (Choice 34.6): the keys' cache manifest chains to the plan (c1_guard_v02.chain_cache), the keys' code hashes are
    bound (tpp_keys_v01 as entry:tpp_keys), each run's summary names these keys, its own hash and bound scripts (tpp_run_v01 as
    entry:tpp_run); QCNet files (Q1, descriptive) must be bound by the plan;
  * provenance for c1_analyse_v05 (Choice 34.4).
Usage: as c1_predarm_v01, plus [--plan <frozen plan>] [--hash-log <file>: nuScenes rehearsal only]
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v02 as G  # noqa: E402
import c1_predarm_v01 as P1  # noqa: E402

TA = P1.TA
ROLE = "entry:c1_predarm"
POPULATION = ("PD: the K8 relied in-path items at 2 s, scored on the K8 tracker-planner's constraints (normal and sign from the "
              "tracker); D16 v13 Choice 35; C1 plan section 11.4 correction pending")
_tables_v01 = P1.tables


def tables_v02(it, kz, arm, pop, fold_of_unit):
    ok = it[arm + "_ok"].copy()
    if pop == "PD":
        ok &= it["inpath"]
    D, V = it[arm + "_D"][ok], it[arm + "_V"][ok]
    assert np.all(np.isfinite(D)) and np.all(np.isfinite(V)) and np.all(V >= 0), \
        "%s %s: non-finite D or variance in a used item: an error (D16 Choice 35)" % (arm, pop)
    assert np.all(fold_of_unit[it["s"][ok]] >= 0), "%s %s: an item of a unit outside the folds (D16 Choice 35)" % (arm, pop)
    return _tables_v01(it, kz, arm, pop, fold_of_unit)


P1.tables = tables_v02


def bound_name(frozen, name, h, role=None):
    paths = [p for p in frozen if os.path.basename(p) == name + ".py" and frozen[p] == h]
    if role:
        paths = [p for p in paths if p in (frozen.roles or {}).get(role, ())]
    assert paths, "code %s (%s...) is not bound%s" % (name, str(h)[:12], " as " + role if role else "")
    return paths[0]


def chain_keys(kz, keys, cache, side, frozen):
    hj = json.loads(str(kz["hashes_json"]))
    mp = os.path.join(cache or str(kz["cache_dir"]), "MANIFEST.json")
    assert G.sha(mp) == hj["manifest"], "the keys' cache manifest differs"
    rec = {"keys": G.rel(keys), "cache": G.chain_cache(mp, side, frozen), "code": {}}
    for name, h in hj.items():
        if name != "manifest":
            rec["code"][name] = bound_name(frozen, name, h, "entry:tpp_keys" if name == "tpp_keys_v01" else None)
    return rec


def chain_run(path, keys_sha, frozen):
    sp = path[:-4] + "_summary.json"
    assert os.path.exists(sp), "a predictor run without its summary: " + G.rel(path)
    s = json.load(open(sp))
    assert s.get("keys_sha256") == keys_sha, "the run was not made on these keys: " + G.rel(path)
    assert s.get("out_sha256") == G.sha(path), "the run differs from its summary: " + G.rel(path)
    code = {n: bound_name(frozen, n, h, "entry:tpp_run" if n == "tpp_run_v01" else None) for n, h in (s.get("scripts") or {}).items()}
    assert "tpp_run_v01" in code, "the run names no tpp_run_v01"
    return {"run": G.rel(path), "sha256": G.sha(path), "code": code}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--folds", required=True)
    ap.add_argument("--tracker-index", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--qcnet-deployed", default=None)
    ap.add_argument("--qcnet-gt", default=None)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None)
    a = ap.parse_args(argv)
    kz0 = np.load(a.keys, allow_pickle=False)
    names = [str(x) for x in kz0["scene_names"]]
    if a.synthetic:
        assert str(kz0["stamp"]) == TA.SYN_STAMP and a.plan is None, "--synthetic: synthetic keys, no plan"
        ds = "synthetic"
    else:
        ds = G.dataset_checked(None, names)
        mp = os.path.join(a.cache or str(kz0["cache_dir"]), "MANIFEST.json")
        assert G.manifest_dataset(json.load(open(mp))) == ds, "the keys' units and their cache disagree on the dataset"
    fj = json.load(open(a.folds))
    outside = sorted(n for n in names if n not in fj["fold_of_log"])
    assert not outside, "units of the keys outside the folds: an error, never a non-exceedance (D16 Choice 35): %s" % outside[:5]
    runs = dict(x.split("=", 1) for x in a.runs)
    files = [a.keys] + list(runs.values()) + [p for p in (a.qcnet_deployed, a.qcnet_gt) if p]
    side = frozen = None
    chains = {}
    if ds == "synthetic":
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha, checked = G.sha(a.folds), False
    else:
        g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        if g:
            side, frozen, rt = g
            folds_sha = G.require_bound(frozen, a.folds, "folds")
            ksha = G.sha(a.keys)
            chains["keys"] = chain_keys(kz0, a.keys, a.cache, side, frozen)
            chains["runs"] = {src: chain_run(p, ksha, frozen) for src, p in runs.items()}
            q = [p for p in (a.qcnet_deployed, a.qcnet_gt) if p]
            if q:
                chains["qcnet"] = G.check_inputs(frozen, q)
            checked = True
        else:
            rt = G.code_record(os.path.abspath(__file__))
            folds_sha, checked = G.sha(a.folds), False
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_predarm_v02", "c1_predarm_v04", {"keys": ds})
    kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)
    kz = dict(kz)
    fold_of_unit = np.array([int(fj["fold_of_log"][n]) for n in names])
    out = {"label": {"TPP": "H9 secondary (Choice 23)", "TPPgt": "descriptive (ground-truth histories, upper bound)",
                     "Q1_deployed": "Q1 descriptive (Choice 20)", "Q1_gt": "Q1 descriptive, upper bound"},
           "population": POPULATION, "folds_sha256": folds_sha, "keys_sha256": G.sha(a.keys), "arms": {},
           "units": len(names), "fold_units_without_keys": sorted(set(fj["fold_of_log"]) - set(names))}
    if rz:
        it = TA.item_table(kz, rz, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        for arm in ("TPP", "TPPgt"):
            if arm + "_D" in it:
                out["arms"][arm] = {pop: P1.arm_result(it, kz, arm, pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    for name, path in (("Q1_deployed", a.qcnet_deployed), ("Q1_gt", a.qcnet_gt)):
        if path:
            qr = P1.qcnet_runs(np.load(path, allow_pickle=False), kz)
            it = TA.item_table(kz, {"trk": qr}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
            out["arms"][name] = {pop: P1.arm_result(it, kz, "TPP", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    if "TPP" in out["arms"]:
        out["H9"] = out["arms"]["TPP"]["PD"]["H9"]
    if frozen is not None:
        rt = G.verify_runtime_again(frozen, rt)
    out["provenance"] = {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                         "inputs_sha256": {G.rel(f): G.sha(f) for f in files}, "inputs_checked": checked, "chains": chains, "dataset": ds}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    print(json.dumps({k: {p: (v[p]["H9"], v[p]["family_size"], v[p]["flagged"]) for p in v} for k, v in out["arms"].items()}))
    print("C1 PREDARM V02 DONE")


if __name__ == "__main__":
    main()
