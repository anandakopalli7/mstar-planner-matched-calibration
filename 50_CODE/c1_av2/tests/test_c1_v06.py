#!/usr/bin/env python3
"""Tests of the R17b fixes (Claude line, test_c1_v06, 4 Nov 2026; D16 v13 Choices 33-35). Planted, synthetic and fake inputs only: the
only AV2-tagged objects are FAKE manifests, export records and keys with zero data rows, written under 70_TESTS/c1_v01/tests_v06/;
no AV2 file is opened. 40_PROTOCOL/C1_PLAN_HASH_LOG.txt must not exist before or after (asserted). One process plus short
subprocesses run one after another (at most 2 processes).
  SLOT    m-5: the slot regex refuses "[SLOT", "[ slot", "SLOT:" and "slot :"; a frozen plan without them passes.
  LOG     A1 / Choice 34.1: a private hash log is accepted for nuScenes data only; refused for av2, mixed and unknown; with no override
          the canonical log is used (absent here, so refused).
  TAG     A3 / Choice 34.3: tags must agree with names (UUIDs under "nuscenes", scene-NNNN under "av2", an empty "nuscenes" set refused).
  ROLE    M-b: require_bound is role-aware (a bound file asked for another role, or a copy under another path, is refused: R17b's probe
          "c1_fit as the stage-B builder").
  RT      M-a / Choice 34.5 and 34.7: verify_runtime refuses an entry point the plan does not name for its role and an unbound module.
  STAGEB  A1 probe re-run: av2_cache_stageB_v03 on a fake AV2-tagged stage-A manifest (zero scenes) with a private plan and log
          refuses (no --hash-log option; the canonical log is absent); a "nuscenes" tag with AV2 names is refused.
  GUARDED A2 / Choice 34.2: c1_mstage_v03, c1_h8_v03, c1_e0_v02 and c1_predarm_v02 refuse fake AV2 inputs without a frozen plan, and
          with a private log, before reading anything else; c1_e0_v02 refuses a stage-B manifest and files not listed as stage-A inputs.
  STAGEA  c1_guard_v02.stage_a_only and check_inputs on fake manifests: stage A with listed hashes passes; stage B or unlisted refused.
  H8M1    m-1: c1_h8_v03.check_e0_plan refuses a missing decision cell and a key outside the decision band.
  PRED35  Choice 35 / M-d: c1_predarm_v02 on the tpp helper's synthetic keys: units outside the folds are an error (v01 tabled them as
          no exceedance); a NaN in a used prediction is an error; with all units in the folds it runs and records its population.
  DEC33   Choice 33 / M-c: c1_analyse_v05.decide on planted results: H1 holds and every secondary input missing -> GO, gate True, every
          secondary "not tested", nothing confirmed; an E0 mismatch -> H8 not tested, still GO; an H8 table without E0_plan -> not
          tested; a missing within run -> NO-GO with the reason, gate False; gate_H1 == (verdict == GO) everywhere.
  TABLE   B / Choice 34.4: check_table accepts a table with this plan, folds, the named entry point and bound code; refuses each fault.
  RUNREC  A3: c1_analyse_v05 --smoke refuses a run record without caches.
  FRZ3    m-3, m-4, Choice 34.7: every generator reproduces its target (9 checks); an entry point with a higher sibling version is not
          the latest; a superseded file listed as bound is refused; tables with a plan hash are post-freeze artefacts.
Every run records the SHA-256 of every tested file (m-7).
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v06.py [<out.json>]
"""
import json
import os
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(C1, "tests"))
sys.path.insert(0, os.path.join(W, "50_CODE", "tpp", "tests"))
import c1_guard_v02 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v06")
PY = sys.executable
UUID = "0b86f508-5df9-4a46-bc59-5b9536dbde9f"
TESTED = ["c1_guard_v02.py", "c1_mstage_v03.py", "c1_h8_v03.py", "c1_e0_v02.py", "c1_predarm_v02.py", "c1_fit_v03.py", "c1_run_v03.py",
          "c1_analyse_v05.py", "c1_freeze_v03.py", "c1_rehearsal_v03.py", "tests/test_c1_v06.py", "tests/make_av2_stageB_v03.py",
          "tests/make_k8_items_v05.py", "../av2/av2_cache_stageB_v03.py", "../k8/k8_items_v05.py"]


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except (AssertionError, SystemExit) as e:
        return str(e) or "refused"
    return None


def mock_plan(d, lines, roles=(), slot_text="", logged=True):
    os.makedirs(d, exist_ok=True)
    plan = os.path.join(d, "PLAN.md")
    body = "# mock plan\n%s\nFROZEN_HASHES_BEGIN\n%s\nFROZEN_HASHES_END\n" % (slot_text, "\n".join("%s  %s" % (G.sha(os.path.join(W, p)), p) for p in lines))
    if roles:
        body += "FROZEN_ROLES_BEGIN\n%s\nFROZEN_ROLES_END\n" % "\n".join("%s  %s" % (r, p) for r, p in roles)
    open(plan, "w", encoding="utf-8", newline="\n").write(body)
    open(plan[:-3] + ".sha256", "w").write(G.sha(plan) + "  PLAN.md\n")
    log = os.path.join(d, "LOG.txt")
    open(log, "w").write((G.sha(plan) + "  x\n") if logged else "")
    return plan, log


def fake_av2_exports(d, tag="av2_sensor_val", scene=UUID):
    os.makedirs(d, exist_ok=True)
    json.dump({"dataset": tag, "status_X1_gates": "PASS"}, open(os.path.join(d, "x1_export_record.json"), "w"))
    json.dump([{"scene": scene, "token": scene + "_0"}], open(os.path.join(d, "x1_per_frame.json"), "w"))
    open(os.path.join(d, "x1_tracks.jsonl.gz"), "wb").write(b"")
    return d


def t_slot():
    d = os.path.join(OUT, "slot")
    f = "50_CODE/c1_av2/c1_guard_v02.py"
    out = {}
    for txt in ("[SLOT S20: x]", "[ slot x]", "SLOT: open", "slot : open"):
        plan, log = mock_plan(os.path.join(d, str(abs(hash(txt)) % 10 ** 6)), [f], slot_text=txt)
        out[txt] = raises(G.frozen_plan, plan, "nuscenes", log)
        assert out[txt] and "open slot" in out[txt], txt
    plan, log = mock_plan(os.path.join(d, "clean"), [f], slot_text="slots were filled (S20) and the plan is frozen")
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    return {"refused": sorted(out), "clean_passes": bool(side)}


def t_log():
    assert not os.path.exists(G.CANONICAL["C1"]), "the real C1 hash log exists: the tests must not run after a real freeze"
    plan, log = mock_plan(os.path.join(OUT, "log"), ["50_CODE/c1_av2/c1_guard_v02.py"])
    G.frozen_plan(plan, "nuscenes", log)
    out = {ds: raises(G.frozen_plan, plan, ds, log) for ds in ("av2", "mixed", "unknown")}
    assert all(v and "override is refused" in v for v in out.values()), out
    canon = raises(G.frozen_plan, plan, "av2")
    assert canon and "no plan hash log" in canon
    g = raises(G.guard, "av2", None, "entry:c1_fit", __file__)
    assert g and "need --plan" in g
    return {"override_refused": sorted(out), "canonical_absent_refused": True, "no_plan_refused": True}


def t_tag():
    bad = [("nuscenes", [UUID]), ("av2", ["scene-0001"]), ("nuscenes", []), ("av2", ["scene-0001", UUID])]
    for tag, names in bad:
        assert raises(G.dataset_checked, tag, names), (tag, names)
    assert G.dataset_checked(None, [UUID]) == "av2" and G.dataset_checked(None, ["scene-0001"]) == "nuscenes"
    assert G.dataset_checked("av2", []) == "av2" and G.dataset_checked(None, ["scene-0001", UUID]) == "mixed"
    assert G.manifest_dataset({"dataset": "av2_sensor_val", "scenes": {UUID: {}}}) == "av2"
    return {"refused": len(bad)}


def t_role():
    fit, stb = "50_CODE/c1_av2/c1_fit_v03.py", "50_CODE/av2/av2_cache_stageB_v03.py"
    plan, log = mock_plan(os.path.join(OUT, "role"), [fit, stb], roles=[("entry:c1_fit", fit), ("entry:stageB", stb)])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    G.require_bound(fr, os.path.join(W, fit), "entry:c1_fit")
    probe = raises(G.require_bound, fr, os.path.join(W, fit), "entry:stageB")
    assert probe and "not in the role" in probe, "R17b probe: c1_fit must not pass as the stage-B builder"
    cp = os.path.join(OUT, "role", "c1_fit_v03_copy.py")
    shutil.copy(os.path.join(W, fit), cp)
    assert raises(G.require_bound, fr, cp), "a copy under another path is not bound"
    return {"role_probe_refused": probe}


def t_rt():
    me = "50_CODE/c1_av2/c1_guard_v02.py"
    entry = "50_CODE/c1_av2/c1_freeze_v03.py"
    plan, log = mock_plan(os.path.join(OUT, "rt"), [me, entry], roles=[("entry:c1_freeze_test", entry)])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    r1 = raises(G.verify_runtime, fr, "entry:c1_analyse", os.path.join(W, entry))
    assert r1 and "names" in r1, "an entry the plan does not name for the role"
    import c1_freeze_v03  # noqa: F401  (loads c1_guard_v02 and itself: both bound)
    G.verify_runtime(fr, "entry:c1_freeze_test", os.path.join(W, entry))
    import make_k8_items_v05  # noqa: F401  (a project module the mock plan does not bind)
    r2 = raises(G.verify_runtime, fr, "entry:c1_freeze_test", os.path.join(W, entry))
    assert r2 and "not bound" in r2 and "make_k8_items_v05" in r2, "a loaded, unbound project module must be refused"
    return {"unnamed_entry": r1[:80], "unbound_module": r2[:120]}


def t_stageb():
    d = os.path.join(OUT, "stageb")
    sa = os.path.join(d, "stageA_fake")
    os.makedirs(sa, exist_ok=True)
    json.dump({"stage": "A", "dataset": "av2", "scenes": {}}, open(os.path.join(sa, "MANIFEST.json"), "w"))
    stb = "50_CODE/av2/av2_cache_stageB_v03.py"
    plan, log = mock_plan(os.path.join(d, "plan"), [stb, G.rel(os.path.join(sa, "MANIFEST.json"))],
                          roles=[("entry:stageB", stb), ("stageA_manifest", G.rel(os.path.join(sa, "MANIFEST.json")))])
    gt = os.path.join(d, "gt_fake.json")
    json.dump({"samples": [], "annotations": []}, open(gt, "w"))
    base = [PY, "-B", os.path.join(W, stb), "--stage-a", sa, "--gt", gt, "--out", os.path.join(d, "outB"), "--frozen-plan", plan]
    r1 = subprocess.run(base + ["--hash-log", log], capture_output=True, text=True)
    r2 = subprocess.run(base, capture_output=True, text=True)
    assert r1.returncode != 0 and "unrecognized arguments: --hash-log" in r1.stderr, r1.stderr[-400:]
    assert r2.returncode != 0 and "refused" in (r2.stdout + r2.stderr) and "no plan hash log" in (r2.stdout + r2.stderr), (r2.stdout + r2.stderr)[-400:]
    assert not os.path.exists(os.path.join(d, "outB", "MANIFEST.json")), "stage B must write nothing"
    sb = os.path.join(d, "stageA_badtag")
    os.makedirs(sb, exist_ok=True)
    json.dump({"stage": "A", "dataset": "nuscenes", "scenes": {UUID: {"sha256": "0" * 64, "log": UUID}}}, open(os.path.join(sb, "MANIFEST.json"), "w"))
    r3 = subprocess.run([PY, "-B", os.path.join(W, stb), "--stage-a", sb, "--gt", gt, "--out", os.path.join(d, "outC")], capture_output=True, text=True)
    assert r3.returncode != 0 and "disagrees" in (r3.stdout + r3.stderr), (r3.stdout + r3.stderr)[-400:]
    return {"hash_log_option": "absent", "canonical_absent": "refused", "tag_mismatch": "refused"}


def t_guarded():
    d = os.path.join(OUT, "guarded")
    ex = fake_av2_exports(os.path.join(d, "exp_av2"))
    nus = [os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker0")]
    gt = os.path.join(d, "gt_fake.json")
    json.dump({"samples": [], "annotations": []}, open(gt, "w"))
    meta = os.path.join(d, "meta")
    os.makedirs(meta, exist_ok=True)
    json.dump([], open(os.path.join(meta, "scene.json"), "w"))
    hz = os.path.join(d, "hz_fake.jsonl.gz")
    open(hz, "wb").write(b"")
    e0p = os.path.join(d, "e0.json")
    json.dump({"car|<20|lat": 0.08, "car|20-40|lat": 0.09}, open(e0p, "w"))
    plan, log = mock_plan(os.path.join(d, "plan"), ["50_CODE/c1_av2/c1_guard_v02.py"])
    out = {}
    cmds = {"mstage": ["c1_mstage_v03.py", "--tracker", "T1", "--experiment", "x", "--av2-workers", ex, "--av2-gt", gt, "--av2-meta", meta,
                       "--av2-horizon", hz, "--train-workers"] + nus + ["--train-gt", gt, "--train-meta", meta, "--train-horizon", hz,
                       "--out", os.path.join(d, "ms.json"), "--test"],
            "h8": ["c1_h8_v03.py", "--workers", ex, "--gt", gt, "--meta", meta, "--horizon", hz, "--e0-plan", e0p, "--out", os.path.join(d, "h8.json")],
            "e0": ["c1_e0_v02.py", "--workers", ex, "--gt", gt, "--meta", meta, "--horizon", hz, "--out", os.path.join(d, "e0out.json")]}
    for name, cmd in cmds.items():
        for extra, key in (([], "no_plan"), (["--plan", plan, "--hash-log", log], "private_log")):
            if name == "e0" and key == "private_log":
                extra = ["--plan", plan, "--hash-log", log]
            r = subprocess.run([PY, "-B"] + cmd + extra, capture_output=True, text=True, cwd=C1)
            msg = (r.stdout + r.stderr)[-600:]
            assert r.returncode != 0 and ("need --plan" in msg or "override is refused" in msg or "--stageA-manifests" in msg), (name, key, msg)
            out["%s_%s" % (name, key)] = "refused"
    sm = os.path.join(d, "stageB_manifest.json")
    json.dump({"stage": "B", "dataset": "av2", "scenes": {}, "inputs": {}}, open(sm, "w"))
    r = subprocess.run([PY, "-B"] + cmds["e0"] + ["--stageA-manifests", sm], capture_output=True, text=True, cwd=C1)
    assert r.returncode != 0 and "stage-A files only" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-500:]
    out["e0_stageB_manifest"] = "refused"
    sa = os.path.join(d, "stageA_manifest.json")
    json.dump({"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt_sha256": G.sha(gt)}}, open(sa, "w"))
    r = subprocess.run([PY, "-B"] + cmds["e0"] + ["--stageA-manifests", sa], capture_output=True, text=True, cwd=C1)
    assert r.returncode != 0 and "not an input of the stage-A manifests" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-500:]
    out["e0_unlisted_input"] = "refused"
    kd = os.path.join(d, "keys")
    os.makedirs(kd, exist_ok=True)
    json.dump({"dataset": "av2", "stage": "B", "scenes": {UUID: {}}}, open(os.path.join(kd, "MANIFEST.json"), "w"))
    kp = os.path.join(d, "keys_fake.npz")
    np.savez(kp, scene_names=np.array([UUID]), cache_dir=np.array(kd), hashes_json=np.array("{}"))
    fp = os.path.join(d, "folds_fake.json")
    json.dump({"fold_of_log": {UUID: 0}, "dataset": "av2", "k": 5}, open(fp, "w"))
    r = subprocess.run([PY, "-B", "c1_predarm_v02.py", "--keys", kp, "--folds", fp, "--tracker-index", "0", "--out", os.path.join(d, "p.json")],
                       capture_output=True, text=True, cwd=C1)
    assert r.returncode != 0 and "need --plan" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-500:]
    out["predarm_no_plan"] = "refused"
    for f in ("ms.json", "h8.json", "e0out.json", "p.json"):
        assert not os.path.exists(os.path.join(d, f)), "a refused module wrote " + f
    return out


def t_stagea():
    d = os.path.join(OUT, "stagea")
    os.makedirs(d, exist_ok=True)
    f1, f2 = os.path.join(d, "a.bin"), os.path.join(d, "b.bin")
    open(f1, "wb").write(b"a")
    open(f2, "wb").write(b"b")
    ma = os.path.join(d, "MA.json")
    json.dump({"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"export_sha256": [G.sha(f1)], "gt_sha256": G.sha(f2)}}, open(ma, "w"))
    ds, rec = G.stage_a_only([ma], [f1, f2])
    assert ds == "av2" and len(rec) == 2
    mb = os.path.join(d, "MB.json")
    json.dump({"stage": "B", "dataset": "av2", "scenes": {}, "inputs": {"gt_sha256": G.sha(f2)}}, open(mb, "w"))
    assert raises(G.stage_a_only, [mb], [f2])
    f3 = os.path.join(d, "c.bin")
    open(f3, "wb").write(b"c")
    assert raises(G.stage_a_only, [ma], [f3])
    plan, log = mock_plan(os.path.join(d, "plan"), [G.rel(ma)], roles=[("stageA_manifest", G.rel(ma))])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    assert len(G.check_inputs(fr, [f1, f2])) == 2 and raises(G.check_inputs, fr, [f3])
    return {"stage_a_listed": "pass", "stage_b": "refused", "unlisted": "refused", "check_inputs": "pass/refused"}


def t_h8m1():
    import c1_h8_v03 as H8
    assert H8.check_e0_plan({"car|<20|lat": 0.08, "car|20-40|lat": 0.09})
    assert raises(H8.check_e0_plan, {"car|<20|lat": 0.08})
    assert raises(H8.check_e0_plan, {"car|<20|lat": 0.08, "car|20-40|lat": None})
    assert raises(H8.check_e0_plan, {"car|<20|lat": 0.08, "car|20-40|lat": 0.09, "ped|<20|lat": 0.1})
    return {"missing_cell": "refused", "extra_key": "refused"}


def t_pred35():
    import c1_folds_v01 as F
    import test_tpp_analyse_v01 as TT
    d = os.path.join(OUT, "pred")
    os.makedirs(d, exist_ok=True)
    kp, runs, _ = TT.make_synthetic(d, seed=5, n_scenes=150)
    kz = dict(np.load(kp, allow_pickle=False))
    names = [str(x) for x in kz["scene_names"]]
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s syn" % n for n in names))
    F.main(["--logs", lp, "--out", os.path.join(d, "folds.json"), "--seed", "20261112"])
    fj = json.load(open(os.path.join(d, "folds.json")))
    fj_part = dict(fj, fold_of_log={n: f for n, f in fj["fold_of_log"].items() if n not in names[:50]})
    json.dump(fj_part, open(os.path.join(d, "folds_part.json"), "w"))
    base = [PY, "-B", "c1_predarm_v02.py", "--keys", kp, "--runs", "trk=" + runs["trk"], "--tracker-index", "0", "--synthetic"]
    r = subprocess.run(base + ["--folds", os.path.join(d, "folds_part.json"), "--out", os.path.join(d, "o_part.json")], capture_output=True, text=True, cwd=C1)
    assert r.returncode != 0 and "outside the folds" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-600:]
    rz = dict(np.load(runs["trk"], allow_pickle=False))
    mu = rz["v2_mu"].copy()
    ok = np.nonzero(rz["status"] == 0)[0] if "status" in rz else np.arange(len(mu))
    import tpp_analyse_v01 as TA
    ok = np.nonzero(rz["status"] == TA.C.ST_OK)[0]
    used = set(kz["item_rec"][kz["item_ref_relied"] & (kz["item_h"] == TA.H_PRIMARY) & kz["item_inpath"]].tolist())
    j = sorted(set(ok.tolist()) & used)[0]
    mu[j, 0] = np.nan
    rz["v2_mu"] = mu
    nanp = os.path.join(d, "run_nan.npz")
    np.savez(nanp, **rz)
    r2 = subprocess.run([PY, "-B", "c1_predarm_v02.py", "--keys", kp, "--runs", "trk=" + nanp, "--tracker-index", "0", "--synthetic",
                         "--folds", os.path.join(d, "folds.json"), "--out", os.path.join(d, "o_nan.json")], capture_output=True, text=True, cwd=C1)
    assert r2.returncode != 0 and "non-finite" in (r2.stdout + r2.stderr), (r2.stdout + r2.stderr)[-600:]
    r3 = subprocess.run(base + ["--folds", os.path.join(d, "folds.json"), "--out", os.path.join(d, "o_full.json")], capture_output=True, text=True, cwd=C1)
    assert r3.returncode == 0, (r3.stdout + r3.stderr)[-800:]
    o = json.load(open(os.path.join(d, "o_full.json")))
    assert "Choice 35" in o["population"] and o["provenance"]["dataset"] == "synthetic" and o["units"] == 150
    return {"outside_folds": "error", "nan": "error", "full": {"H9": o.get("H9"), "PD_exceed_share": o["arms"]["TPP"]["PD"]["exceed_share"]}}


def planted(h1=True, with_h3=False):
    import c1_analyse_v05 as A5
    fb = {"met": h1, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False} for a in A5.REQUIRED_ARMS}
    w = {"form_b": fb, "status": st, "form_c": None, "form_a": {}}
    return {"within_lt3d": {t: dict(w) for t in A5.TRACKERS}}


def t_dec33():
    import c1_analyse_v05 as A5
    out = {}
    d1 = A5.decide(planted(True), {"routes": []}, "smoke", {})
    assert d1["C1_verdict"] == "GO" and d1["gate_H1"] and not d1["nogo_reasons"], d1["nogo_reasons"]
    sec = ("H2", "H3", "H4", "H6a", "H6b", "H7", "H8", "H9", "H10")
    assert all(d1["claims_status"][c] == "not tested" for c in sec), d1["claims_status"]
    assert all(not v.get("confirmed") and v["label"].startswith("not tested") for v in d1["family_S"].values()), d1["family_S"]
    assert d1["failed_conditions"] == [] and len(d1["missing_inputs"]) >= 9
    out["all_secondary_missing"] = {"verdict": d1["C1_verdict"], "not_tested": d1["not_tested"]}
    t8 = {"ok": True, "data": {"H8": True, "E0_plan": {"car|<20|lat": 0.08, "car|20-40|lat": 0.09}}, "checks": {"entry_point": "x"}}
    e_bad = {"ok": False, "reason": "the recomputed E0 differs"}
    d2 = A5.decide(planted(True), {"routes": []}, "smoke", {"tables": {"h8": t8}, "e0": e_bad})
    assert d2["C1_verdict"] == "GO" and d2["claims_status"]["H8"] == "not tested" and "E0" in d2["hypotheses"]["H8"]["reasons"][0]
    e_ok = {"ok": True, "plan": {"car|<20|lat": 0.08, "car|20-40|lat": 0.09}}
    d3 = A5.decide(planted(True), {"routes": []}, "smoke", {"tables": {"h8": t8}, "e0": e_ok})
    assert d3["claims_status"]["H8"] == "holds"
    t8b = {"ok": True, "data": {"H8": True}, "checks": {"entry_point": "x"}}
    d4 = A5.decide(planted(True), {"routes": []}, "smoke", {"tables": {"h8": t8b}, "e0": e_ok})
    assert d4["claims_status"]["H8"] == "not tested", "an H8 table without E0_plan is not tested (R17b M-c)"
    res = planted(True)
    del res["within_lt3d"]["t3"]
    d5 = A5.decide(res, {"routes": []}, "smoke", {"route_problems": {"within_lt3d": {"t3": "not provenance-valid: probe"}}})
    assert d5["C1_verdict"] == "NO-GO" and not d5["gate_H1"] and any("probe" in x for x in d5["nogo_reasons"])
    assert all(not v.get("confirmed") for v in d5["family_S"].values())
    d6 = A5.decide(planted(False), {"routes": []}, "smoke", {})
    for dd in (d1, d2, d3, d4, d5, d6):
        assert dd["gate_H1"] == (dd["C1_verdict"] == "GO")
    out.update({"E0_mismatch": d2["claims_status"]["H8"], "E0_ok": d3["claims_status"]["H8"], "no_E0_plan": d4["claims_status"]["H8"],
                "within_missing": d5["C1_verdict"], "H1_fails": d6["C1_verdict"]})
    return out


def t_table():
    me = "50_CODE/c1_av2/c1_h8_v03.py"
    g2 = "50_CODE/c1_av2/c1_guard_v02.py"
    plan, log = mock_plan(os.path.join(OUT, "table"), [me, g2], roles=[("entry:c1_h8", me), ("module", g2)])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    good = {"provenance": {"plan_sha256": side, "folds_sha256": "f" * 64, "entry_point": {me: fr[me]}, "code_sha256": {me: fr[me], g2: fr[g2]},
                           "inputs_sha256": {"x": "0" * 64}, "inputs_checked": True}}
    G.check_table(good, side, fr, "f" * 64, "entry:c1_h8")
    faults = {"plan": ("plan_sha256", "0" * 64), "folds": ("folds_sha256", "e" * 64), "entry": ("entry_point", {g2: fr[g2]}),
              "code": ("code_sha256", {me: fr[me], "50_CODE/x.py": "1" * 64}), "inputs": ("inputs_checked", False)}
    out = {}
    for n, (k, v) in faults.items():
        bad = json.loads(json.dumps(good))
        bad["provenance"][k] = v
        out[n] = raises(G.check_table, bad, side, fr, "f" * 64, "entry:c1_h8")
        assert out[n], n
    assert raises(G.check_table, good, side, fr, "f" * 64, "entry:c1_mstage")
    return {k: v[:60] for k, v in out.items()}


def t_runrec():
    d = os.path.join(OUT, "runrec")
    os.makedirs(d, exist_ok=True)
    json.dump({"c1": False, "caches": []}, open(os.path.join(d, "run_record_x_decide.json"), "w"))
    fp = os.path.join(d, "folds.json")
    json.dump({"fold_of_log": {"scene-0001": 0}, "dataset": "nuscenes", "source_of_log": {}}, open(fp, "w"))
    cfg = os.path.join(d, "cfg.json")
    json.dump({"routes": [{"name": "within_lt3d", "runs": d, "tags": {"t1": "x"}}], "folds": fp}, open(cfg, "w"))
    r = subprocess.run([PY, "-B", "c1_analyse_v05.py", "--config", cfg, "--out", os.path.join(d, "o.json"), "--decision", os.path.join(d, "dec.json"),
                        "--smoke", "--boot", "10"], capture_output=True, text=True, cwd=C1)
    assert r.returncode != 0 and "without caches" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-600:]
    return {"run_record_without_caches": "refused"}


def t_frz3():
    import c1_freeze_v03 as F3
    gens = F3.check_generators([])
    assert len(gens) == 9, gens
    assert not F3.latest("50_CODE/c1_av2/c1_analyse_v04.py") and F3.latest("50_CODE/c1_av2/c1_analyse_v05.py")
    assert not F3.latest("50_CODE/c1_av2/c1_run_v02.py") and F3.latest("50_CODE/c1_av2/c1_run_v03.py")
    d = os.path.join(OUT, "frz3")
    os.makedirs(d, exist_ok=True)
    rd = os.path.join(d, "README_bad.md")
    p = "50_CODE/c1_av2/c1_analyse_v04.py"
    open(rd, "w").write("%s  %s  module\nsuperseded  %s\n" % (G.sha(os.path.join(W, p)), p, p))
    assert raises(F3.readme_v05, rd)
    tp = os.path.join(d, "table.json")
    json.dump({"provenance": {"plan_sha256": "a" * 64}}, open(tp, "w"))
    assert F3.post_freeze_artefact(tp)
    unbound_gen = raises(F3.check_generators, [("0" * 64, "50_CODE/c1_av2/tests/make_unknown.py", "generator")])
    assert unbound_gen and "not checked" in unbound_gen
    return {"generators": gens, "latest_rule": True, "superseded_bound": "refused"}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v06.json")
    os.makedirs(OUT, exist_ok=True)
    canon_before = os.path.exists(G.CANONICAL["C1"])
    t0 = time.time()
    res, ok = {}, True
    res["tested_files_sha256"] = {f: G.sha(os.path.join(C1, f)) for f in TESTED}
    res["python"] = sys.version
    for name, fn in (("SLOT", t_slot), ("LOG", t_log), ("TAG", t_tag), ("ROLE", t_role), ("RT", t_rt), ("STAGEB", t_stageb),
                     ("GUARDED", t_guarded), ("STAGEA", t_stagea), ("H8M1", t_h8m1), ("PRED35", t_pred35), ("DEC33", t_dec33),
                     ("TABLE", t_table), ("RUNREC", t_runrec), ("FRZ3", t_frz3)):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-1500:], flush=True)
    assert not canon_before and not os.path.exists(G.CANONICAL["C1"]), "the real C1 hash log must not exist"
    res["tested_files_sha256_at_end"] = {f: G.sha(os.path.join(C1, f)) for f in TESTED}
    if res["tested_files_sha256_at_end"] != res["tested_files_sha256"]:
        ok = False
        res["files_changed_during_tests"] = True
    res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_path, "w"), indent=1, default=str)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
