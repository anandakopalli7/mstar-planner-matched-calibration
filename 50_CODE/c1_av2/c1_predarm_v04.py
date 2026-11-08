#!/usr/bin/env python3
"""C1 predictor arms v04 (Claude line, c1_predarm_v04, 4 Nov 2026) = c1_predarm_v03 (kept, imported: history-length strata, cross-fitting,
tables and Choices 35 and 37 unchanged) on c1_guard_v03, with R17c M3, M4, m1 and D16 v17 Choice 38b / v18 Choice 39b.
  * M3 / Choice 39b, H9's rule (h9_rule_v04): the floor counts E2 cells only: at least 6 power-qualified E2 cells. The 3 pooled
    history-length cells are an ADDED requirement: each evaluable and none flagged, in the same sup-t family as the E2 cells (flags,
    power and the family flag are computed over E2 + HL columns together). The pooled cell counts each item once (the HL columns
    partition the items). Everything else is c1_analyse_v01.h9_rule's. s20c_label(): S20c's label rule the same way (secondary iff >= 6
    power-qualified E2 cells).
  * Choice 38b, seeds in one call: --runs trk=<seed 20261102> trk@20261104=<...> trk@20261105=<...> [gt=<...>]. Each run's summary seed
    is read and asserted (primary 20261102; robustness 20261104 and 20261105; the ground-truth-history run 20261102). Under a plan all
    three tracker-history runs are required, so every seed's predictions exist before any H9 outcome is computed. H9 (primary) is the
    seed-20261102 table; H9_seed reports the same HL rule, same items, folds and bootstrap seeds, under each seed (descriptive).
  * M4: the keys' units must EQUAL the folds' units (v03 reported fold_units_without_keys; it is now an error), the folds' dataset must
    equal the keys'; the provenance records the sorted unit list and its hash, the log hash, the versions and every run's seed.
  * AV2 keys and runs must carry the tpp_keys_v02 / tpp_run_v02 wrapper records (no --scenes subset under C1; R17c M4).
  * m1: without a TPP run the table has no "H9" key (c1_analyse_v06 then reports H9 "not tested").
Usage: python -B c1_predarm_v04.py --keys <npz> --runs trk=<npz> trk@20261104=<npz> trk@20261105=<npz> [gt=<npz>] --folds <json>
       --tracker-index 0|1|2 --out <json> [--plan <frozen plan>] [--hash-log <file>: nuScenes only] [--synthetic] [--qcnet-deployed ...]
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v03 as G  # noqa: E402
import c1_predarm_v03 as P3  # noqa: E402

P2, P1, TA, CA = P3.P2, P3.P1, P3.TA, P3.CA
ROLE = "entry:c1_predarm"
PRIMARY_SEED = 20261102
ROBUST_SEEDS = (20261104, 20261105)
POPULATION = P3.POPULATION + "; floor on E2 cells only, HL cells an added requirement (D16 v18 Choice 39b)"


def h9_rule_v04(N, X, cells, n_e2, scene_of_ep, log_of_ep, W, power_key, floor=None):
    A = CA.A
    floor = CA.F_MIN if floor is None else floor
    one = np.ones((1, N.shape[0]))
    ev = A.evaluable(N, scene_of_ep, log_of_ep)
    fam = np.flatnonzero(ev)
    est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
    flagged = []
    if len(fam):
        _, _, _, sig, _ = A.flag(est, boot, fam, 0.95)
        flagged = [cells[j][0] for i, j in enumerate(fam) if sig[i]]
    hl = list(range(n_e2, N.shape[1]))
    cols = hl if hl else list(range(N.shape[1]))
    Np, Xp = N[:, cols].sum(1, keepdims=True), X[:, cols].sum(1, keepdims=True)
    e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
    _, _, _, sigp, _ = A.flag(e1, b1, np.array([0]), 0.95)
    pw, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng(list(power_key)))
    qual = np.flatnonzero(ev & (pw >= A.POWER_MIN))
    qual_e2 = [int(j) for j in qual if j < n_e2]
    fflag = []
    if len(qual):
        _, _, _, sigf, _ = A.flag(est, boot, qual, 0.95)
        fflag = [cells[j][0] for i, j in enumerate(qual) if sigf[i]]
    hl_eval = {cells[j][0]: bool(ev[j]) for j in hl}
    hl_flag = sorted({cells[j][0] for j in hl} & (set(flagged) | set(fflag)))
    ok = bool(len(fam) and not flagged and not sigp[0] and len(qual_e2) >= floor and not fflag and all(hl_eval.values()) and not hl_flag)
    return {"H9": ok, "evaluable": int(len(fam)), "flagged": flagged, "pooled_flagged": bool(sigp[0]), "family_size": int(len(qual)),
            "family_size_E2": len(qual_e2), "family_flagged": fflag, "floor": floor, "floor_counts": "E2 cells only (Choice 39b)",
            "hl_cells_evaluable": hl_eval, "hl_cells_flagged": hl_flag, "power_seed": list(power_key),
            "rule": "h9_rule_v04: >= 6 power-qualified E2 cells; the 3 HL cells evaluable and unflagged in the same sup-t family"}


def s20c_label(rule):
    """S20c (Choice 39b): H9 is secondary iff its power-qualified family has at least 6 E2 cells; else descriptive."""
    return "secondary" if rule["family_size_E2"] >= CA.F_MIN else "descriptive"


def rule_v04(N, Xc, cells, units, kz, i, n_e2):
    logs = np.array([str(kz["scene_logs"][u]) for u in units])
    ulog = sorted(set(logs.tolist()))
    log_of_ep = np.array([ulog.index(x) for x in logs])
    scene_of_ep = np.array([str(kz["scene_names"][u]) for u in units])
    rng = np.random.default_rng([CA.SEED_BOOT, i, P1.J_PRED])
    W_logs = rng.multinomial(len(ulog), np.full(len(ulog), 1.0 / len(ulog)), size=CA.K.B_BOOT).astype(float)
    r = h9_rule_v04(N, Xc, cells, n_e2, scene_of_ep, log_of_ep, W_logs[:, log_of_ep], [CA.SEED_POWER, i, P1.J_PRED])
    r["cells"], r["units"], r["logs"] = [c[0] for c in cells], int(len(units)), len(ulog)
    return r


def arm_results_v04(it, kz, arm, pop, fold_of_unit, i):
    hk = P3.HL_KEY[arm]
    N, Xc, cells, units, info = P3.tables_hl(it, kz, arm, pop, fold_of_unit, True, hk)
    hl_r = dict(rule_v04(N, Xc, cells, units, kz, i, len(cells) - 3), **info)
    hl_r["S20c_label"] = s20c_label(hl_r)
    N0, X0, c0, u0, info0 = P3.tables_hl(it, kz, arm, pop, fold_of_unit, False, hk)
    diag = dict(rule_v04(N0, X0, c0, u0, kz, i, len(c0) - 3), **info0)
    nohl = P1.arm_result(it, kz, arm, pop, fold_of_unit, i)
    return {"HL": hl_r, "noHL": nohl, "noHL_on_HL_cells": diag}


def parse_runs(items):
    runs, seeds = {}, {}
    for x in items:
        lab, p = x.split("=", 1)
        if lab == "trk":
            seeds[lab] = PRIMARY_SEED
        elif lab.startswith("trk@"):
            seeds[lab] = int(lab[4:])
            assert seeds[lab] in ROBUST_SEEDS, "robustness seeds are %s only (Choice 38b)" % (ROBUST_SEEDS,)
        elif lab == "gt":
            seeds[lab] = PRIMARY_SEED
        else:
            raise AssertionError("unknown run label " + lab)
        runs[lab] = p
    return runs, seeds


def run_seed(path, want, synthetic):
    sp = path[:-4] + "_summary.json"
    if not os.path.exists(sp):
        assert synthetic, "a predictor run without its summary (seed unverifiable): " + G.rel(path)
        return {"seed": want, "verified": False, "sha256": G.sha(path)}
    s = json.load(open(sp))
    assert int(s.get("seed")) == want, "run %s has seed %s, expected %d (Choice 38b; R17c M4)" % (G.rel(path), s.get("seed"), want)
    return {"seed": want, "verified": True, "sha256": G.sha(path)}


def chain_keys_v04(kz, keys, cache, side, frozen):
    """The keys' cache chains to the plan; the code the keys record (tpp_keys_v01, tpp_common_v01, k8_items_v02, k6_sim_v02) is bound.
    The entry role is checked on the wrapper record (AV2) - tpp_keys_v02 is the plan's entry:tpp_keys, tpp_keys_v01 its module."""
    hj = json.loads(str(kz["hashes_json"]))
    mp = os.path.join(cache or str(kz["cache_dir"]), "MANIFEST.json")
    assert G.sha(mp) == hj["manifest"], "the keys' cache manifest differs"
    rec = {"keys": G.rel(keys), "cache": G.chain_cache(mp, side, frozen), "code": {}}
    for name, h in hj.items():
        if name != "manifest":
            rec["code"][name] = P2.bound_name(frozen, name, h)
    return rec


def chain_run_v04(path, keys_sha, frozen):
    sp = path[:-4] + "_summary.json"
    assert os.path.exists(sp), "a predictor run without its summary: " + G.rel(path)
    s = json.load(open(sp))
    assert s.get("keys_sha256") == keys_sha, "the run was not made on these keys: " + G.rel(path)
    assert s.get("out_sha256") == G.sha(path), "the run differs from its summary: " + G.rel(path)
    assert (s.get("status_counts") or {}).get("not_predicted", 0) == 0, "the run left records unpredicted (a --scenes subset?)"
    code = {n: P2.bound_name(frozen, n, h) for n, h in (s.get("scripts") or {}).items()}
    assert "tpp_run_v01" in code, "the run names no tpp_run_v01"
    return {"run": G.rel(path), "sha256": G.sha(path), "code": code, "seed": s.get("seed")}


def wrapper_record(path, kind, frozen):
    wp = path + ".wrapper.json"
    assert os.path.exists(wp), "AV2 %s without its %s wrapper record (no --scenes check)" % (G.rel(path), kind)
    w = json.load(open(wp))
    ep = w.get("entry_point") or {}
    p, h = list(ep.items())[0]
    assert (frozen.roles or {}).get("entry:" + kind) == [p] and frozen.get(p) == h, "%s not made by the plan's entry:%s" % (G.rel(path), kind)
    assert w.get("out_sha256") == G.sha(path) and w.get("scenes") is None, "%s: a --scenes subset or another file (R17c M4)" % G.rel(path)
    return {"wrapper": G.rel(wp), "entry_point": p}


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
    if ds != "synthetic":
        assert G.folds_dataset(fj) == ds, "the folds' dataset differs from the keys' (R17c M4)"
    outside = sorted(n for n in names if n not in fj["fold_of_log"])
    assert not outside, "units of the keys outside the folds: an error, never a non-exceedance (D16 Choice 35): %s" % outside[:5]
    absent = sorted(set(fj["fold_of_log"]) - set(names))
    assert not absent, "fold units without keys: %d, e.g. %s; the keys' units must equal the folds' units (R17c M4)" % (len(absent), absent[:3])
    runs, want = parse_runs(a.runs)
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
            missing = [l for l in ["trk"] + ["trk@%d" % s for s in ROBUST_SEEDS] if l not in runs]
            assert not missing, "under a plan all three seeds' runs are required before any H9 outcome (Choice 38b): missing %s" % missing
            ksha = G.sha(a.keys)
            chains["keys"] = chain_keys_v04(kz0, a.keys, a.cache, side, frozen)
            chains["runs"] = {src: chain_run_v04(p, ksha, frozen) for src, p in runs.items()}
            if ds != "nuscenes":
                chains["keys"]["wrapper"] = wrapper_record(a.keys, "tpp_keys", frozen)
                for src, p in runs.items():
                    chains["runs"][src]["wrapper"] = wrapper_record(p, "tpp_run", frozen)
            q = [p for p in (a.qcnet_deployed, a.qcnet_gt) if p]
            if q:
                chains["qcnet"] = G.check_inputs(frozen, q)
            checked = True
        else:
            rt = G.code_record(os.path.abspath(__file__))
            folds_sha, checked = G.sha(a.folds), False
    seeds = {lab: run_seed(p, want[lab], a.synthetic) for lab, p in runs.items()}
    kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)
    kz = dict(kz)
    for lab in runs:
        k = P3.HL_KEY["TPPgt" if lab == "gt" else "TPP"]
        assert k in kz, "the keys carry no %s (history length, Choice 37)" % k
    fold_of_unit = np.array([int(fj["fold_of_log"][n]) for n in names])
    out = {"label": {"TPP": "H9 secondary (Choice 23), HL-stratified (Choice 37), E2 floor (Choice 39b); H9_noHL descriptive",
                     "TPPgt": "descriptive (ground-truth histories, upper bound)", "H9_seed": "descriptive seed robustness (Choice 38b)",
                     "Q1_deployed": "Q1 descriptive (Choice 20), noHL", "Q1_gt": "Q1 descriptive, upper bound, noHL"},
           "population": POPULATION, "history_length": {"TPP": P3.HL_KEY["TPP"], "TPPgt": P3.HL_KEY["TPPgt"], "strata": list(P3.HL_NAMES)},
           "folds_sha256": folds_sha, "keys_sha256": G.sha(a.keys), "arms": {}, "units": len(names), "seeds": seeds,
           "primary_seed": PRIMARY_SEED, "robustness_seeds": list(ROBUST_SEEDS)}
    if "trk" in rz:
        it = TA.item_table(kz, {"trk": rz["trk"]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["TPP"] = {pop: arm_results_v04(it, kz, "TPP", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
        out["H9"] = out["arms"]["TPP"]["PD"]["HL"]["H9"]
        out["H9_noHL"] = out["arms"]["TPP"]["PD"]["noHL"]["H9"]
        out["S20c_label_from_counts"] = out["arms"]["TPP"]["PD"]["HL"]["S20c_label"]
        out["H9_seed"] = {str(PRIMARY_SEED): out["H9"]}
        for s in ROBUST_SEEDS:
            lab = "trk@%d" % s
            if lab in rz:
                its = TA.item_table(kz, {"trk": rz[lab]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
                N, Xc, cells, units, info = P3.tables_hl(its, kz, "TPP", "PD", fold_of_unit, True, P3.HL_KEY["TPP"])
                r = dict(rule_v04(N, Xc, cells, units, kz, a.tracker_index, len(cells) - 3), **info)
                out["arms"]["TPP_seed%d" % s] = {"PD": {"HL": r}}
                out["H9_seed"][str(s)] = r["H9"]
    if "gt" in rz:
        it = TA.item_table(kz, {"gt": rz["gt"]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["TPPgt"] = {pop: arm_results_v04(it, kz, "TPPgt", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    for name, path in (("Q1_deployed", a.qcnet_deployed), ("Q1_gt", a.qcnet_gt)):
        if path:
            qr = P1.qcnet_runs(np.load(path, allow_pickle=False), kz)
            it = TA.item_table(kz, {"trk": qr}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
            out["arms"][name] = {pop: {"noHL": P1.arm_result(it, kz, "TPP", pop, fold_of_unit, a.tracker_index),
                                       "note": "QCNet's own input history is not in the keys: no HL stratum"} for pop in ("PD", "PD7")}
    if frozen is not None:
        rt = G.verify_runtime_again(frozen, rt)
    out["provenance"] = {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                         "inputs_sha256": {G.rel(f): G.sha(f) for f in files}, "inputs_checked": checked, "chains": chains, "dataset": ds,
                         "units": G.units_record(names), "seeds": seeds, "primary_seed": PRIMARY_SEED,
                         "hash_log_sha256": rt.get("hash_log_sha256"), "versions": rt["versions"]}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    print(json.dumps({"H9": out.get("H9"), "H9_noHL": out.get("H9_noHL"), "H9_seed": out.get("H9_seed"),
                      "E2_floor": (out["arms"].get("TPP") or {}).get("PD", {}).get("HL", {}).get("family_size_E2")}))
    print("C1 PREDARM V04 DONE")


if __name__ == "__main__":
    main()
