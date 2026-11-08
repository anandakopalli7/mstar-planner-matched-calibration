#!/usr/bin/env python3
"""C1 predictor arms v05 (Claude line, c1_predarm_v05, 4 Nov 2026) = c1_predarm_v04 (kept, imported: seeds, chains, units, tables) on
c1_guard_v04, with D16 v21 Choice 42 (R17d B1, M3, m1, m4, (g)):
  * B1: on AV2 the guard requires the validated deposit record (role entry:c1_predarm); the table records deposit_record_sha256.
  * m1 (h9_rule_v05; stricter): E2 cells are flagged against the E2-only sup-t family, as in D17's frozen H9; HL cells against the joint
    E2 + HL family. H9 holds only if >= 6 power-qualified E2 cells (Choice 39b), no E2 cell is flagged in the E2-only families (evaluable
    and power-qualified), no HL cell is flagged in the joint families, every HL cell is evaluable and the pooled cell is not flagged.
  * m4: under a plan the FROZEN_ENV_TPP block is required; every tpp_keys_v03 / tpp_run_v03 wrapper record must carry the same python
    and numpy (and, for runs, torch) versions. nuScenes keys and runs made without a wrapper record are recorded as "not recorded".
  * M3, --q1-only (Choice 41c, 42e): QCNet (Q1, descriptive) on the 150 validation logs: no --runs; --folds bound in the role
    folds_val150 and checked against its parent; keys whose units equal that child's units, chained to their cache (so, on AV2, to the
    deposit); every QCNet file chained to its c1_qcnet_summary_v01 summary (the keys' hash, the file's hash, not_predicted == 0, the
    checkpoint commit, re-centring and history source; made by the plan's entry:c1_qcnet_summary). The table has no "H9" key.
  * (g): an existing output is refused on AV2; one run-log line is appended.
Without --q1-only the QCNet options are refused: H9 and Q1 are separate tables (m5).
Usage: python -B c1_predarm_v05.py --keys <npz> --runs trk=<npz> trk@20261104=<npz> trk@20261105=<npz> [gt=<npz>] --folds <json>
         --tracker-index i --out <json> [--plan ... --hash-log ...] [--synthetic]
       python -B c1_predarm_v05.py --q1-only --keys <npz> --folds <folds_val150 json> --tracker-index i --out <json>
         --qcnet-deployed <npz> --qcnet-deployed-summary <json> [--qcnet-gt <npz> --qcnet-gt-summary <json>] [--plan ...]
"""
import argparse
import json
import os
import sys

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v04 as G  # noqa: E402
import c1_predarm_v04 as P4  # noqa: E402

P3, P2, P1, TA, CA = P4.P3, P4.P2, P4.P1, P4.TA, P4.CA
ROLE = "entry:c1_predarm"
PRIMARY_SEED, ROBUST_SEEDS = P4.PRIMARY_SEED, P4.ROBUST_SEEDS
POPULATION = P4.POPULATION + "; E2 cells flagged in the E2-only sup-t family, HL cells in the joint family (D16 v21 Choice 42f m1)"


def h9_rule_v05(N, X, cells, n_e2, scene_of_ep, log_of_ep, W, power_key, floor=None):
    A = CA.A
    floor = CA.F_MIN if floor is None else floor
    one = np.ones((1, N.shape[0]))
    ev = A.evaluable(N, scene_of_ep, log_of_ep)
    est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
    e2 = np.arange(N.shape[1]) < n_e2
    hl = list(range(n_e2, N.shape[1]))

    def flagged_in(fam_idx, keep):
        if not len(fam_idx):
            return []
        _, _, _, sig, _ = A.flag(est, boot, np.asarray(fam_idx), 0.95)
        return [cells[j][0] for i, j in enumerate(fam_idx) if sig[i] and keep(j)]
    fam_all, fam_e2 = np.flatnonzero(ev), np.flatnonzero(ev & e2)
    flag_e2 = flagged_in(fam_e2, lambda j: True)
    flag_hl = flagged_in(fam_all, lambda j: j >= n_e2)
    cols = hl if hl else list(range(N.shape[1]))
    Np, Xp = N[:, cols].sum(1, keepdims=True), X[:, cols].sum(1, keepdims=True)
    e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
    _, _, _, sigp, _ = A.flag(e1, b1, np.array([0]), 0.95)
    pw, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng(list(power_key)))
    qual = np.flatnonzero(ev & (pw >= A.POWER_MIN))
    qual_e2 = np.asarray([j for j in qual if j < n_e2], dtype=int)
    fflag_e2 = flagged_in(qual_e2, lambda j: True)
    fflag_hl = flagged_in(qual, lambda j: j >= n_e2)
    hl_eval = {cells[j][0]: bool(ev[j]) for j in hl}
    ok = bool(len(fam_all) and not flag_e2 and not flag_hl and not sigp[0] and len(qual_e2) >= floor and not fflag_e2 and not fflag_hl
              and all(hl_eval.values()))
    return {"H9": ok, "evaluable": int(len(fam_all)), "evaluable_E2": int(len(fam_e2)), "flagged": flag_e2 + flag_hl, "flagged_E2_family": flag_e2,
            "flagged_HL_joint_family": flag_hl, "pooled_flagged": bool(sigp[0]), "family_size": int(len(qual)), "family_size_E2": int(len(qual_e2)),
            "family_flagged": fflag_e2 + fflag_hl, "family_flagged_E2": fflag_e2, "family_flagged_HL": fflag_hl, "floor": floor,
            "floor_counts": "E2 cells only (Choice 39b)", "hl_cells_evaluable": hl_eval, "hl_cells_flagged": sorted(set(flag_hl) | set(fflag_hl)),
            "power_seed": list(power_key),
            "rule": "h9_rule_v05: >= 6 power-qualified E2 cells; E2 cells unflagged in the E2-only sup-t family; HL cells evaluable and unflagged in the joint family"}


def rule_v05(N, Xc, cells, units, kz, i, n_e2):
    logs = np.array([str(kz["scene_logs"][u]) for u in units])
    ulog = sorted(set(logs.tolist()))
    log_of_ep = np.array([ulog.index(x) for x in logs])
    scene_of_ep = np.array([str(kz["scene_names"][u]) for u in units])
    rng = np.random.default_rng([CA.SEED_BOOT, i, P1.J_PRED])
    W_logs = rng.multinomial(len(ulog), np.full(len(ulog), 1.0 / len(ulog)), size=CA.K.B_BOOT).astype(float)
    r = h9_rule_v05(N, Xc, cells, n_e2, scene_of_ep, log_of_ep, W_logs[:, log_of_ep], [CA.SEED_POWER, i, P1.J_PRED])
    r["cells"], r["units"], r["logs"] = [c[0] for c in cells], int(len(units)), len(ulog)
    return r


def arm_results_v05(it, kz, arm, pop, fold_of_unit, i):
    hk = P3.HL_KEY[arm]
    N, Xc, cells, units, info = P3.tables_hl(it, kz, arm, pop, fold_of_unit, True, hk)
    hl_r = dict(rule_v05(N, Xc, cells, units, kz, i, len(cells) - 3), **info)
    hl_r["S20c_label"] = P4.s20c_label(hl_r)
    hl_r["v04_joint_rule"] = P4.rule_v04(N, Xc, cells, units, kz, i, len(cells) - 3)["H9"]
    N0, X0, c0, u0, info0 = P3.tables_hl(it, kz, arm, pop, fold_of_unit, False, hk)
    diag = dict(rule_v05(N0, X0, c0, u0, kz, i, len(c0) - 3), **info0)
    nohl = P1.arm_result(it, kz, arm, pop, fold_of_unit, i)
    return {"HL": hl_r, "noHL": nohl, "noHL_on_HL_cells": diag}


def env_check(frozen, rec, kind):
    """m4: a wrapper record's versions against FROZEN_ENV_TPP."""
    want = frozen.env_tpp
    assert want, "the plan has no FROZEN_ENV_TPP block (R17d m4)"
    got = (rec or {}).get("versions") or {}
    keys = ("python", "numpy") + (("torch",) if kind == "tpp_run" else ())
    bad = {k: (want.get(k), got.get(k)) for k in keys if str(want.get(k)) != str(got.get(k))}
    assert not bad, "the tpp38 versions of a %s record differ from FROZEN_ENV_TPP: %s (R17d m4)" % (kind, bad)
    return {k: got.get(k) for k in keys}


def wrapper_v05(path, kind, frozen):
    wp = path + ".wrapper.json"
    if not os.path.exists(wp):
        return None
    r = P4.wrapper_record(path, kind, frozen)
    r["versions"] = env_check(frozen, json.load(open(wp)), kind)
    return r


def chain_qcnet(path, summary, keys, side, frozen):
    s = json.load(open(summary))
    assert s.get("keys_sha256") == G.sha(keys), "the QCNet summary was not made on these keys"
    assert s.get("out_sha256") == G.sha(path), "the QCNet file differs from its summary"
    assert s.get("not_predicted") == 0, "QCNet left %s key records unpredicted (Choice 42e requires 0)" % s.get("not_predicted")
    for k in ("checkpoint_commit", "recentring", "history_source"):
        assert s.get(k), "the QCNet summary records no %s" % k
    if frozen is not None:
        ep = s.get("entry_point") or {}
        p, h = list(ep.items())[0]
        assert (frozen.roles or {}).get("entry:c1_qcnet_summary") == [p] and frozen.get(p) == h, "the QCNet summary was not made by the plan's entry"
        assert s.get("plan_sha256") == side, "the QCNet summary was not made under this plan"
    return {"qcnet": G.rel(path), "summary": G.rel(summary), "summary_sha256": G.sha(summary), "source": s.get("source")}


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
    qc = {n: (getattr(a, "qcnet_" + n), getattr(a, "qcnet_%s_summary" % n)) for n in ("deployed", "gt") if getattr(a, "qcnet_" + n)}
    if a.q1_only:
        assert not a.runs and qc, "--q1-only: QCNet files, no --runs (Choice 42e)"
        assert all(s for _, s in qc.values()), "--q1-only: every QCNet file needs its run summary (c1_qcnet_summary_v01)"
    else:
        assert not qc, "QCNet goes through --q1-only: H9 and Q1 are separate tables (R17d m5)"
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
    assert not outside, "units of the keys outside the folds (D16 Choice 35): %s" % outside[:5]
    absent = sorted(set(fj["fold_of_log"]) - set(names))
    assert not absent, "fold units without keys: %d, e.g. %s (R17c M4)" % (len(absent), absent[:3])
    G.refuse_existing([a.out], ds)
    runs, want = P4.parse_runs(a.runs)
    files = [a.keys] + list(runs.values()) + [p for p, _ in qc.values()]
    side = frozen = None
    chains, env_rec = {}, {}
    g = None
    if ds == "synthetic":
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha, checked = G.sha(a.folds), False
        chains["qcnet"] = {n: chain_qcnet(p, s, a.keys, None, None) for n, (p, s) in qc.items()}
    else:
        g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
        if g:
            side, frozen, rt = g
            if a.q1_only:
                role, folds_sha = G.require_folds(frozen, a.folds, ("folds_val150",))
                G.check_child_folds(a.folds, frozen)
            else:
                folds_sha = G.require_bound(frozen, a.folds, "folds")
                missing = [l for l in ["trk"] + ["trk@%d" % s for s in ROBUST_SEEDS] if l not in runs]
                assert not missing, "under a plan all three seeds' runs are required (Choice 38b): missing %s" % missing
            ksha = G.sha(a.keys)
            chains["keys"] = P4.chain_keys_v04(kz0, a.keys, a.cache, side, frozen)
            chains["runs"] = {src: P4.chain_run_v04(p, ksha, frozen) for src, p in runs.items()}
            assert frozen.env_tpp, "the plan has no FROZEN_ENV_TPP block (R17d m4)"
            kw = wrapper_v05(a.keys, "tpp_keys", frozen)
            assert kw or ds == "nuscenes", "AV2 keys without their tpp_keys wrapper record"
            env_rec["keys"] = kw["versions"] if kw else "not recorded (nuScenes keys made without a wrapper)"
            for src, p in runs.items():
                rw = wrapper_v05(p, "tpp_run", frozen)
                assert rw or ds == "nuscenes", "AV2 run without its tpp_run wrapper record"
                env_rec[src] = rw["versions"] if rw else "not recorded (nuScenes run made without a wrapper)"
            chains["qcnet"] = {n: chain_qcnet(p, s, a.keys, side, frozen) for n, (p, s) in qc.items()}
            checked = True
        else:
            rt = G.code_record(os.path.abspath(__file__))
            folds_sha, checked = G.sha(a.folds), False
            chains["qcnet"] = {n: chain_qcnet(p, s, a.keys, None, None) for n, (p, s) in qc.items()}
    seeds = {lab: P4.run_seed(p, want[lab], a.synthetic) for lab, p in runs.items()}
    kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)
    kz = dict(kz)
    for lab in runs:
        k = P3.HL_KEY["TPPgt" if lab == "gt" else "TPP"]
        assert k in kz, "the keys carry no %s (history length, Choice 37)" % k
    fold_of_unit = np.array([int(fj["fold_of_log"][n]) for n in names])
    out = {"label": {"TPP": "H9 secondary (Choice 23), HL strata (37), E2 floor (39b), E2-only flags (42f m1); H9_noHL descriptive",
                     "TPPgt": "descriptive (ground-truth histories)", "H9_seed": "descriptive seed robustness (Choice 38b)",
                     "Q1_deployed": "Q1 descriptive (Choice 20, 41c), folds_val150", "Q1_gt": "Q1 descriptive, upper bound, folds_val150"},
           "population": POPULATION, "q1_only": bool(a.q1_only), "folds_sha256": folds_sha, "keys_sha256": G.sha(a.keys), "arms": {},
           "units": len(names), "seeds": seeds, "primary_seed": PRIMARY_SEED, "robustness_seeds": list(ROBUST_SEEDS), "tpp_env": env_rec}
    if "trk" in rz:
        it = TA.item_table(kz, {"trk": rz["trk"]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["TPP"] = {pop: arm_results_v05(it, kz, "TPP", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
        out["H9"] = out["arms"]["TPP"]["PD"]["HL"]["H9"]
        out["H9_noHL"] = out["arms"]["TPP"]["PD"]["noHL"]["H9"]
        out["S20c_label_from_counts"] = out["arms"]["TPP"]["PD"]["HL"]["S20c_label"]
        out["H9_seed"] = {str(PRIMARY_SEED): out["H9"]}
        for s in ROBUST_SEEDS:
            lab = "trk@%d" % s
            if lab in rz:
                its = TA.item_table(kz, {"trk": rz[lab]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
                N, Xc, cells, units, info = P3.tables_hl(its, kz, "TPP", "PD", fold_of_unit, True, P3.HL_KEY["TPP"])
                r = dict(rule_v05(N, Xc, cells, units, kz, a.tracker_index, len(cells) - 3), **info)
                out["arms"]["TPP_seed%d" % s] = {"PD": {"HL": r}}
                out["H9_seed"][str(s)] = r["H9"]
    if "gt" in rz:
        it = TA.item_table(kz, {"gt": rz["gt"]}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["TPPgt"] = {pop: arm_results_v05(it, kz, "TPPgt", pop, fold_of_unit, a.tracker_index) for pop in ("PD", "PD7")}
    for n, (path, _) in qc.items():
        with np.load(path, allow_pickle=False) as qz:
            qz = {k: qz[k] for k in qz.files}  # one read per array: P1.qcnet_runs indexes per row (an NpzFile re-reads each time)
        qr = P1.qcnet_runs(qz, kz)
        it = TA.item_table(kz, {"trk": qr}, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
        out["arms"]["Q1_" + n] = {pop: {"noHL": P1.arm_result(it, kz, "TPP", pop, fold_of_unit, a.tracker_index),
                                        "note": "QCNet's own input history is not in the keys: no HL stratum"} for pop in ("PD", "PD7")}
    if frozen is not None:
        rt = G.verify_runtime_again(frozen, rt)
    out["provenance"] = {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                         "inputs_sha256": {G.rel(f): G.sha(f) for f in files}, "inputs_checked": checked, "chains": chains, "dataset": ds,
                         "units": G.units_record(names), "seeds": seeds, "primary_seed": PRIMARY_SEED, "q1_only": bool(a.q1_only),
                         "hash_log_sha256": rt.get("hash_log_sha256"), "versions": rt["versions"], "tpp_env": env_rec,
                         "deposit_record_sha256": rt.get("deposit_record_sha256", "exempt (%s)" % ds)}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    if g:
        G.run_log_append(ds, os.path.abspath(__file__), side, rt["deposit_record_sha256"], out["provenance"]["inputs_sha256"], [a.out])
    print(json.dumps({"H9": out.get("H9"), "H9_noHL": out.get("H9_noHL"), "H9_seed": out.get("H9_seed"), "q1_only": bool(a.q1_only),
                      "E2_floor": (out["arms"].get("TPP") or {}).get("PD", {}).get("HL", {}).get("family_size_E2")}))
    print("C1 PREDARM V05 DONE")


if __name__ == "__main__":
    main()
