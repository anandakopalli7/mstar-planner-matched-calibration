#!/usr/bin/env python3
"""C1 H8 v05 (Claude line, c1_h8_v05, 4 Nov 2026) = c1_h8_v04 (kept) on c1_guard_v04, with D16 v21 Choice 42 (R17d): on AV2 the
validated deposit record before anything is read (B1); ground truth only from the quarantine (B2); under a plan the ground truth's
scenes must EQUAL the units of the folds role "folds" (the 375 logs; M2, no subset); scene.json bound and checked against the stage-A
logs (m3); an existing output refused on AV2 and one run-log line (g); deposit_record_sha256 in the table.
C1 H8 v04 (Claude line, c1_h8_v04, 4 Nov 2026) = c1_h8_v03 (kept) on c1_guard_v03, with R17c M4: the table records its units, the
scenes of the ground-truth file (sorted, with their hash); under a plan the export's track scenes must equal them, they must all be
units of the bound folds, and the folds' dataset must equal the exports'; the log hash and versions are recorded.
C1 H8 v03 (Claude line, c1_h8_v03, 4 Nov 2026) = c1_h8_v02 (kept, imported; compute() unchanged) with D16 v13 Choice 34 and R17b m-1:
  * the plan's E0 must hold BOTH decision cells (car|<20|lat, car|20-40|lat), else refused (never a silent delta); a key that is not a
    cell of the 4-cell decision band is refused; the long cells take delta BY DESIGN (recorded in "threshold_rule");
  * the export records must pass X1's gates (as c1_h8_v01 checked; v02 had dropped the check);
  * guard as c1_mstage_v03 (entry:c1_h8; outcome-free dataset check before any ground truth; canonical log unless nuScenes); under a
    plan the folds are bound in the role "folds", the E0 file is bound by the plan and every input is bound or a stage-A input;
  * provenance for c1_analyse_v05 (Choice 34.4).
Usage: python -B c1_h8_v03.py --workers ... --gt ... --meta ... --horizon ... --e0-plan <json {cell: E0}> --out <json>
       [--plan <frozen plan> --folds <json>] [--hash-log <file>: nuScenes rehearsal only]
"""
import argparse
import json
import os
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v04 as G  # noqa: E402
import c1_h8_v02 as H2  # noqa: E402
import c1_e0_v01 as E0  # noqa: E402

ROLE = "entry:c1_h8"


def gt_scenes(gt):
    return sorted({str(x["scene"]) for x in json.load(open(gt))["samples"]})


def check_e0_plan(e0):
    dec = {"|".join(c) for c in H2.X2.DEC}
    missing = [c for c in E0.DECISION_CELLS if c not in e0 or e0[c] is None]
    assert not missing, "the plan's E0 lacks decision cells %s: refused, never delta (R17b m-1)" % missing
    extra = [c for c in e0 if c not in dec]
    assert not extra, "E0 keys that are not cells of the decision band: %s" % extra
    return True


def gates(workers):
    for w in workers:
        r = json.load(open(os.path.join(w, "x1_export_record.json")))
        assert r.get("status_X1_gates") == "PASS", "export worker failed its gates: " + w


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", nargs="+", required=True)
    ap.add_argument("--gt", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--horizon", required=True)
    ap.add_argument("--e0-plan", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--plan", default=None)
    ap.add_argument("--folds", default=None)
    ap.add_argument("--hash-log", default=None)
    a = ap.parse_args(argv)
    e0 = json.load(open(a.e0_plan))
    check_e0_plan(e0)
    ds = G.export_dataset(a.workers)
    g = G.guard(ds, a.plan, ROLE, os.path.abspath(__file__), a.hash_log)
    G.refuse_existing([a.out], ds)
    gt_path, gt_tmp = a.gt, None
    side = frozen = None
    if g:
        side, frozen, rt = g
        gt_path, gt_tmp, _ = G.resolve_gt(frozen, a.gt, ds)
    files = [os.path.join(w, "x1_tracks.jsonl.gz") for w in a.workers] + [gt_path, os.path.join(a.meta, "scene.json"), a.horizon]
    if g:
        assert a.folds, "--plan needs --folds"
        folds_sha = G.require_bound(frozen, a.folds, "folds")
        fj = json.load(open(a.folds))
        assert G.folds_dataset(fj) == ds, "the folds' dataset differs from the exports' (R17c M4)"
        G.require_bound(frozen, a.e0_plan)
        inputs, checked = G.check_inputs(frozen, files), True
    else:
        rt = G.code_record(os.path.abspath(__file__))
        folds_sha = G.sha(a.folds) if a.folds else None
        inputs, checked = {G.rel(f): G.sha(f) for f in files}, False
    inputs[G.rel(a.e0_plan)] = G.sha(a.e0_plan)
    gates(a.workers)
    scenes = gt_scenes(gt_path)
    assert G.units_dataset(scenes) == ds, "the ground truth's scenes disagree with the exports' dataset"
    if g:
        trk = sorted(set().union(*[G.track_scenes(w) for w in a.workers]))
        assert trk == scenes, "the export's track scenes differ from the ground truth's scenes (R17c M4)"
        assert scenes == sorted(fj["fold_of_log"]), "H8's units must equal the folds' units exactly (%d vs %d; R17d M2, Choice 42d)" % (len(scenes), len(fj["fold_of_log"]))
        scene_chk = G.check_scene_json(frozen, a.meta, scenes)
    else:
        scene_chk = None
    try:
        out = H2.compute(a.workers, gt_path, a.meta, a.horizon, e0)
    finally:
        G.cleanup(gt_tmp)
    if g:
        rt = G.verify_runtime_again(frozen, rt)
    out["threshold_rule"] = {"lateral decision cells": "max(delta, E0_plan) (D16 Choice 31)", "long cells": "delta unless the plan gives their E0 (by design; not used by H8)",
                           "long cells given": sorted(c for c in e0 if c not in E0.DECISION_CELLS)}
    out["provenance"] = {"plan_sha256": side, "folds_sha256": folds_sha, "entry_point": rt["entry_point"], "code_sha256": rt["code_sha256"],
                         "inputs_sha256": inputs, "inputs_checked": checked, "dataset": ds,
                         "units": G.units_record(scenes), "units_source": "ground-truth samples", "hash_log_sha256": rt.get("hash_log_sha256"),
                         "versions": rt["versions"], "deposit_record_sha256": rt.get("deposit_record_sha256", "exempt (%s)" % ds),
                         "scene_json_check": scene_chk}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "w") as f:
        json.dump(out, f, indent=1, default=float)
    os.replace(tmp, a.out)
    if g:
        G.run_log_append(ds, os.path.abspath(__file__), side, rt["deposit_record_sha256"], inputs, [a.out])
    print(json.dumps({"H8": out["H8"], "bins": out["bins"], "plan": side}))
    print("C1 H8 V05 DONE")


if __name__ == "__main__":
    main()
