#!/usr/bin/env python3
"""C1 method stage v06 (Claude line, c1_mstage_v06, 5 Nov 2026) = c1_mstage_v05 (copied) on c1_guard_v05 (D16 v23 Choice 44f): on AV2 the guard writes a chained 'start' line to 40_PROTOCOL/C1_RUN_LOG.txt before any
ground truth or table is read and the 'done' line is chained to it (m1); the deposit record must not name the OSF project and the
plan's log line must carry a parsable time (m2); stale c1_gt_* temporary folders are swept (m7). Otherwise unchanged.
C1 method stage v05 (Claude line, c1_mstage_v05, 4 Nov 2026) = c1_mstage_v04 (kept) on c1_guard_v04, with D16 v21 Choice 42 (R17d):
  * B1: on AV2 the guard requires the validated deposit record before anything is read (role entry:c1_mstage is not exempt);
  * B2: the AV2 ground truth is read only from the quarantine (a member of 30_DATA/av2_gt_quarantine_v01/, decompressed to a
    temporary file outside the workspace, SHA-256 = a bound stage-A manifest's gt_sha256), removed afterwards;
  * m3: scene.json is bound as data:scene_json and every unit's log equals the stage-A manifests' log (c1_guard_v04.check_scene_json);
  * (g): an existing output is refused on AV2 (resumable checkpoints are kept); one line is appended to 40_PROTOCOL/C1_RUN_LOG.txt;
  * the table records deposit_record_sha256 (check_table requires it).
C1 method stage v04 (Claude line, c1_mstage_v04, 4 Nov 2026) = c1_mstage_v03 (kept) on c1_guard_v03, with R17c M4:
  * guard v03: the latest line of the hash log only, FROZEN_ENV versions asserted, the log hash recorded in the provenance;
  * the AV2 set's units must EQUAL the bound folds' units (v03 refused only units outside the folds, so a subset passed), and the
    folds' dataset must equal the exports' dataset; the provenance records the sorted unit list and its hash (c1_guard_v03.units_record),
    which c1_analyse_v06 checks against the folds;
  * the export dataset is read from x1_tracks.jsonl.gz (R17c m7).
Statistics, sizes, seeds and checkpointing are c1_mstage_v02's (imported unchanged).
c1_mstage_v03 (Claude line, c1_mstage_v03, 4 Nov 2026) = c1_mstage_v02 (kept, imported; statistics and checkpointing
unchanged) with D16 v13 Choice 34 (R17b A2, B, M-a):
  * guard (c1_guard_v02.guard): the dataset of the "AV2" exports is read from outcome-free files only (x1_per_frame scene names and
    the export record's tag) BEFORE any ground truth; nuScenes exports may run without a plan (tests); anything else needs --plan, a
    frozen plan in 40_PROTOCOL/C1_PLAN_HASH_LOG.txt (no other log), with this file as the plan's entry:c1_mstage and every loaded
    module bound; --test sizes are refused under a plan unless the data are nuScenes (a rehearsal);
  * under a plan: --folds must be bound in the role "folds"; every input (x1_tracks, GT, scene.json, horizon; both sets) must be
    bound by the plan or be an input of a bound stage-A manifest; every unit of the AV2 set must be a unit of the folds;
  * the checkpoint key covers every loaded project module (m_lib, m_run, m_data, x1_lib, c1_crc_exact, c1_guard, c1_mstage v01-v03,
    ...), the inputs, the plan and the folds (R17b M-a);
  * provenance (Choice 34.4): {"plan_sha256", "folds_sha256", "entry_point", "code_sha256", "inputs_sha256", "inputs_checked",
    "dataset"}; c1_analyse_v05 checks it (c1_guard_v02.check_table).
Usage: as c1_mstage_v02, plus [--plan <frozen plan> --folds <folds json>] [--hash-log <file>: nuScenes rehearsal only]
"""
import argparse
import json
import os
import sys
import time

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v05 as G  # noqa: E402
import c1_mstage_v02 as V2  # noqa: E402

V1, M, R = V2.V1, V2.M, V2.R
ROLE = "entry:c1_mstage"


def input_files(workers, gt, meta, horizon):
    return [os.path.join(w, "x1_tracks.jsonl.gz") for w in workers] + [gt, os.path.join(meta, "scene.json"), horizon]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", required=True)
    ap.add_argument("--experiment", required=True)
    for p in ("av2", "train"):
        ap.add_argument("--%s-workers" % p, nargs="+", required=True)
        ap.add_argument("--%s-gt" % p, required=True)
        ap.add_argument("--%s-meta" % p, required=True)
        ap.add_argument("--%s-horizon" % p, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--folds", default=None)
    ap.add_argument("--hash-log", default=None, help="a rehearsal's own log: nuScenes data only")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--reps", type=int, default=M.R_CV)
    ap.add_argument("--boot", type=int, default=M.B_BOOT)
    ap.add_argument("--refit-boot", type=int, default=M.B_E1R)
    ap.add_argument("--e2-boot", type=int, default=M.B_REFIT)
    a = ap.parse_args(argv)
    ds = G.export_dataset(a.av2_workers)
    assert G.export_dataset(a.train_workers) == "nuscenes", "E2-AV2's training set is the nuScenes train scenes"
    g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
    if not a.test:
        assert (a.reps, a.boot, a.refit_boot, a.e2_boot) == (M.R_CV, M.B_BOOT, M.B_E1R, M.B_REFIT), "the confirmatory sizes are fixed"
    G.refuse_existing([a.out], ds)
    gt_path, gt_tmp = a.av2_gt, None
    side = folds_sha = frozen = None
    if g:
        side, frozen, rt = g
        gt_path, gt_tmp, _ = G.resolve_gt(frozen, a.av2_gt, ds)
    files = input_files(a.av2_workers, gt_path, a.av2_meta, a.av2_horizon) + input_files(a.train_workers, a.train_gt, a.train_meta, a.train_horizon)
    if g:
        assert not a.test or ds == "nuscenes", "--test sizes under a plan: nuScenes rehearsal only"
        assert a.folds, "--plan needs --folds"
        folds_sha = G.require_bound(frozen, a.folds, "folds")
        assert G.folds_dataset(json.load(open(a.folds))) == ds, "the folds' dataset differs from the exports' (R17c M4)"
        inputs, checked = G.check_inputs(frozen, files), True
        scene_chk = G.check_scene_json(frozen, a.av2_meta, sorted(json.load(open(a.folds))["fold_of_log"]))
    else:
        scene_chk = None
        rt = G.code_record(os.path.abspath(__file__))
        inputs, checked = {G.rel(f): G.sha(f) for f in files}, False
        folds_sha = G.sha(a.folds) if a.folds else None
    V1.configure(exact=True, c1_seeds=True)
    t0 = time.time()
    try:
        av2 = V1.load(a.av2_workers, gt_path, a.av2_meta, a.av2_horizon, a.experiment)
    finally:
        G.cleanup(gt_tmp)
    train = V1.load(a.train_workers, a.train_gt, a.train_meta, a.train_horizon, a.experiment)
    names = [str(n) for n in av2["_names"]]
    assert G.units_dataset(names) == ds and G.units_dataset(train["_names"]) == "nuscenes", "the loaded units disagree with the exports' dataset"
    if a.folds:
        fold_units = set(json.load(open(a.folds))["fold_of_log"])
        outside, absent = sorted(set(names) - fold_units), sorted(fold_units - set(names))
        assert not outside, "units of the AV2 set outside the folds: %s" % outside[:5]
        assert not absent or not g, "fold units missing from the AV2 set: %s (the units must equal the folds' units; R17c M4)" % absent[:5]
    key = {"tracker": a.tracker, "experiment": a.experiment, "sizes": [a.reps, a.boot, a.refit_boot, a.e2_boot], "seed_base": M.SEED,
           "exact_crc": True, "code": rt["code_sha256"], "inputs": inputs, "plan_sha256": side, "folds_sha256": folds_sha}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    res = V2.run_resumable(av2, train, a.tracker, a.reps, a.boot, a.refit_boot, a.e2_boot, a.out, key)
    if g:
        rt = G.verify_runtime_again(frozen, rt)
    res.update({"tracker": a.tracker, "seeds": {"base": M.SEED, "e1_folds": "base + r", "refit": "base + 1000 + b"}, "exact_crc": True,
                "sizes": {"reps": a.reps, "B": a.boot, "refit_B": a.refit_boot, "e2_B": a.e2_boot}, "test_mode": bool(a.test),
                "checkpoint_key": key, "seconds": round(time.time() - t0, 1), "av2_units": len(names),
                "provenance": {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                               "inputs_sha256": inputs, "inputs_checked": checked, "dataset": ds,
                               "units": G.units_record(names), "hash_log_sha256": rt.get("hash_log_sha256"), "versions": rt["versions"],
                               "deposit_record_sha256": rt.get("deposit_record_sha256", "exempt (%s)" % ds), "scene_json_check": scene_chk}})
    V2._atomic(a.out, res)
    if g:
        G.run_log_append(ds, os.path.abspath(__file__), side, rt["deposit_record_sha256"], inputs, [a.out])
    print(json.dumps({"H6a": res["E1"]["hypotheses"]["HM1"], "H6b_p": res["H6b_p"], "H7": res["E2"]["hypotheses"]["HM6"], "plan": side}))
    print("C1 MSTAGE V06 DONE")


if __name__ == "__main__":
    main()
