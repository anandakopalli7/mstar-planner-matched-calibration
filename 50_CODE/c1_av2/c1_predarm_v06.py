#!/usr/bin/env python3
"""C1 predictor arm v06 (Claude line, c1_predarm_v06, 5 Nov 2026) = c1_predarm_v05 (kept, imported: h9_rule_v05, rule_v05,
arm_results_v05, and through c1_predarm_v04 the seeds, chains, units and tables; H9 unchanged) on c1_guard_v05, with D16 v23 Choice 44:
  * 44(e) M-E: a tpp_keys_v03 wrapper record is compared with FROZEN_ENV (canmot310: python, numpy), and a tpp_run_v03 record with
    FROZEN_ENV_TPP (tpp38: python, numpy, torch), by c1_guard_v05.env_check. Under a plan both blocks are required. AV2 keys and runs
    need their wrapper records; nuScenes keys and runs made without one are recorded as "not recorded".
  * 44(d) M-D: Q1 (QCNet) is not tested in C1. --q1-only and the QCNet options are refused; the table never holds a QCNet arm.
  * 44(f) m1: the dataset is read from the folds file, and the guard (with its run-log "start" line on AV2) runs before the keys or
    any run is opened. The "done" line carries the output hash.
  * the rest as v05: the deposit record on AV2, an existing output refused on AV2, H9 by h9_rule_v05.
Usage: python -B c1_predarm_v06.py --keys <npz> --runs trk=<npz> trk@20261104=<npz> trk@20261105=<npz> [gt=<npz>] --folds <json>
         --tracker-index i --out <json> [--plan ... --hash-log ...] [--synthetic]
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v05 as G  # noqa: E402
import c1_predarm_v05 as P5  # noqa: E402

P4 = P5.P4
P3, P2, P1, TA, CA = P4.P3, P4.P2, P4.P1, P4.TA, P4.CA
ROLE = "entry:c1_predarm"
PRIMARY_SEED, ROBUST_SEEDS = P4.PRIMARY_SEED, P4.ROBUST_SEEDS
POPULATION = P5.POPULATION
Q1_REFUSED = "Q1 (QCNet) is not tested in C1 (D16 v23 Choice 44d): no QCNet input is accepted"


def wrapper_v06(path, kind, frozen):
    wp = path + ".wrapper.json"
    if not os.path.exists(wp):
        return None
    r = P4.wrapper_record(path, kind, frozen)
    r["versions"] = G.env_check(frozen, json.load(open(wp)), kind)
    return r


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--keys", required=True)
    ap.add_argument("--runs", nargs="*", default=[])
    ap.add_argument("--folds", required=True)
    ap.add_argument("--tracker-index", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cache", default=None)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--q1-only", action="store_true")
    for x in ("deployed", "gt"):
        ap.add_argument("--qcnet-%s" % x, default=None)
        ap.add_argument("--qcnet-%s-summary" % x, default=None)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--hash-log", default=None)
    a = ap.parse_args(argv)
    assert not (a.q1_only or a.qcnet_deployed or a.qcnet_gt or a.qcnet_deployed_summary or a.qcnet_gt_summary), Q1_REFUSED
    fj = json.load(open(a.folds))
    if a.synthetic:
        assert a.plan is None, "--synthetic: synthetic keys, no plan"
        ds = "synthetic"
    else:
        ds = G.folds_dataset(fj)
    G.refuse_existing([a.out], ds)
    side = frozen = None
    chains, env_rec = {}, {}
    g = None
    if ds == "synthetic":
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha, checked = G.sha(a.folds), False
    else:
        g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
    kz0 = np.load(a.keys, allow_pickle=False)
    names = [str(x) for x in kz0["scene_names"]]
    if a.synthetic:
        assert str(kz0["stamp"]) == TA.SYN_STAMP, "--synthetic: synthetic keys only"
    else:
        assert G.dataset_checked(None, names) == ds, "the keys' dataset differs from the folds' (R17c M4)"
        mp = os.path.join(a.cache or str(kz0["cache_dir"]), "MANIFEST.json")
        assert G.manifest_dataset(json.load(open(mp))) == ds, "the keys' units and their cache disagree on the dataset"
    outside = sorted(n for n in names if n not in fj["fold_of_log"])
    assert not outside, "units of the keys outside the folds (D16 Choice 35): %s" % outside[:5]
    absent = sorted(set(fj["fold_of_log"]) - set(names))
    assert not absent, "fold units without keys: %d, e.g. %s (R17c M4)" % (len(absent), absent[:3])
    runs, want = P4.parse_runs(a.runs)
    files = [a.keys] + list(runs.values())
    if ds != "synthetic":
        if g:
            side, frozen, rt = g
            folds_sha = G.require_bound(frozen, a.folds, "folds")
            missing = [l for l in ["trk"] + ["trk@%d" % s for s in ROBUST_SEEDS] if l not in runs]
            assert not missing, "under a plan all three seeds' runs are required (Choice 38b): missing %s" % missing
            ksha = G.sha(a.keys)
            chains["keys"] = P4.chain_keys_v04(kz0, a.keys, a.cache, side, frozen)
            chains["runs"] = {src: P4.chain_run_v04(p, ksha, frozen) for src, p in runs.items()}
            assert frozen.env, "the plan has no FROZEN_ENV block (R17c m5)"
            assert frozen.env_tpp, "the plan has no FROZEN_ENV_TPP block (R17d m4)"
            kw = wrapper_v06(a.keys, "tpp_keys", frozen)
            assert kw or ds == "nuscenes", "AV2 keys without their tpp_keys wrapper record"
            env_rec["keys"] = kw["versions"] if kw else "not recorded (nuScenes keys made without a wrapper)"
            for src, p in runs.items():
                rw = wrapper_v06(p, "tpp_run", frozen)
                assert rw or ds == "nuscenes", "AV2 run without its tpp_run wrapper record"
                env_rec[src] = rw["versions"] if rw else "not recorded (nuScenes run made without a wrapper)"
            checked = True
        else:
            rt = G.code_record(os.path.abspath(__file__))
            folds_sha, checked = G.sha(a.folds), False
    seeds = {lab: P4.run_seed(p, want[lab], a.synthetic) for lab, p in runs.items()}
    kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)
    kz = dict(kz)
    for lab in runs:
        k = P3.HL_KEY["TPPgt" if lab == "gt" else "TPP"]
        assert k in kz, "the keys carry no %s (history length, Choice 37)" % k
    fold_of_unit = np.array([int(fj["fold_of_log"][n]) for n in names])
    out = {"label": {"TPP": "H9 secondary (Choice 23), HL strata (37), E2 floor (39b), E2-only flags (42f m1); H9_noHL descriptive",
                     "TPPgt": "descriptive (ground-truth histories)", "H9_seed": "descriptive seed robustness (Choice 38b)",
                     "Q1": "not tested in C1 (D16 v23 Choice 44d)"},
           "population": POPULATION, "folds_sha256": folds_sha, "keys_sha256": G.sha(a.keys), "arms": {},
           "units": len(names), "seeds": seeds, "primary_seed": PRIMARY_SEED, "robustness_seeds": list(ROBUST_SEEDS), "tpp_env": env_rec}
    if "trk" in rz:
        it = TA.item_table(kz, {"trk": rz["trk"]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["TPP"] = {pop: P5.arm_results_v05(it, kz, "TPP", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
        out["H9"] = out["arms"]["TPP"]["PD"]["HL"]["H9"]
        out["H9_noHL"] = out["arms"]["TPP"]["PD"]["noHL"]["H9"]
        out["S20c_label_from_counts"] = out["arms"]["TPP"]["PD"]["HL"]["S20c_label"]
        out["H9_seed"] = {str(PRIMARY_SEED): out["H9"]}
        for s in ROBUST_SEEDS:
            lab = "trk@%d" % s
            if lab in rz:
                its = TA.item_table(kz, {"trk": rz[lab]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
                N, Xc, cells, units, info = P3.tables_hl(its, kz, "TPP", "PD", fold_of_unit, True, P3.HL_KEY["TPP"])
                r = dict(P5.rule_v05(N, Xc, cells, units, kz, a.tracker_index, len(cells) - 3), **info)
                out["arms"]["TPP_seed%d" % s] = {"PD": {"HL": r}}
                out["H9_seed"][str(s)] = r["H9"]
    if "gt" in rz:
        it = TA.item_table(kz, {"gt": rz["gt"]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["TPPgt"] = {pop: P5.arm_results_v05(it, kz, "TPPgt", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    if frozen is not None:
        rt = G.verify_runtime_again(frozen, rt)
    out["provenance"] = {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                         "inputs_sha256": {G.rel(f): G.sha(f) for f in files}, "inputs_checked": checked, "chains": chains, "dataset": ds,
                         "units": G.units_record(names), "seeds": seeds, "primary_seed": PRIMARY_SEED,
                         "hash_log_sha256": rt.get("hash_log_sha256"), "versions": rt["versions"], "tpp_env": env_rec,
                         "deposit_record_sha256": rt.get("deposit_record_sha256", "exempt (%s)" % ds)}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    if g:
        G.run_log_append(ds, os.path.abspath(__file__), side, rt["deposit_record_sha256"], out["provenance"]["inputs_sha256"], [a.out])
    print(json.dumps({"H9": out.get("H9"), "H9_noHL": out.get("H9_noHL"), "H9_seed": out.get("H9_seed"),
                      "E2_floor": (out["arms"].get("TPP") or {}).get("PD", {}).get("HL", {}).get("family_size_E2")}))
    print("C1 PREDARM V06 DONE")


if __name__ == "__main__":
    main()
