#!/usr/bin/env python3
"""Tests of C1 code v06 (Claude line, test_c1_v09, 4 Nov 2026): R17c's M1-M4, m1-m8 and D16 Choices 38b-d and 39b-c, plus R17c's P1-P7
probes re-run as refusal tests. Synthetic and nuScenes data and dummy AV2-TAGGED fixtures only (R17c's p1/p2/p5/p7 folders, read
only, and fixtures written under 70_TESTS/c1_v01/tests_v09/); no AV2 file is opened; 40_PROTOCOL/C1_PLAN_HASH_LOG.txt must not exist.
Groups:
  G3     guard v03: only the latest log line is accepted (M1); the log hash is recorded; FROZEN_ENV is required and a version mismatch
         is refused (m5); export_dataset reads the track file's scenes (m7).
  FRZ4   c1_freeze_v04 with README v06's files (its "test" files replaced by a probe suite): a freeze writes FROZEN_ENV and FROZEN_TESTS;
         a second freeze into the same log is refused; --amend appends, is logged, and only the new plan is accepted; a stage-B
         manifest under the data root refuses; a test that does not print ALL_PASS refuses; an unbound stage-A builder refuses (m8);
         a re-randomised child folds file refuses.
  M2     an exception on a secondary input or route makes that claim "not tested" with the exception text (P3: a moved E0 input; P4e:
         a malformed method-stage table; a raising H9 table); an exception on an H1 input gives NO-GO with the reason; through main()
         (--smoke): a broken within run and a missing transfer run still write a decision.
  M3     h9_rule_v04 on planted tables: 3 E2 + 3 HL cells fail the floor (v01's rule would count 6); >= 6 clean E2 cells and clean HL
         cells hold; a flagged HL cell fails H9 despite >= 6 clean E2 cells. Powered synthetic pipeline (c1_predarm_v04): the HL-stratified
         H9 holds; with a planted short-history excess, H9_noHL holds with >= 6 qualified E2 cells (missed with power), the HL cells flag
         it under the noHL fit, and the HL-stratified H9 holds (m6).
  M4     check_table refuses another unit list, a units hash mismatch and another dataset; c1_predarm_v04 refuses keys covering a subset of
         the folds (P7) and a run whose summary seed is not its label's; the primary table must be seed 20261102 (load_table);
         tpp_keys_v02 / tpp_run_v02 refuse --scenes on AV2-named inputs.
  MINOR  m1 (no TPP arm -> H9 not tested), m2 (c1_e0_v03 refuses another seed and mode x1 on AV2), m3 (a run whose cache dataset differs
         from the folds' is refused by check_route_c1).
  S38B   flipping or removing the robustness seeds changes nothing in the decision but H9_seed_robustness.
  S38C   AB3DMOT ("tab") passing, failing or missing leaves C1_verdict, gate_H1, family_S and every claim status byte-identical.
  S38D   c1_folds_v03 --restrict-from children pass check_child_folds; a re-randomised child is refused; c1_fit_v04 --route source refuses
         a validation unit in training.
  DEPOSIT  D16 v19 Choice 40: c1_guard_v03.check_deposit passes a fixture record naming the plan on the nuScenes route and refuses a
         wrong plan hash, a missing registration or time; on AV2 a missing record and a fixture override are refused; chain_cache refuses an
         AV2 stage-B manifest without deposit_record_sha256, and without the real record; stage B v04 checks it before the ground truth.
  P1P7   R17c's probes as refusal tests on v06: P1 stage B v01, v02 (edited) and v04 on an AV2-tagged stage-A cache; P2 c1_h8_v02/v04,
         c1_mstage_v02/v04, c1_predarm_v01/v04, c1_e0_v01/v03 on AV2-tagged exports or keys; P5 the floor counts E2 cells only; P6 one freeze
         (see FRZ4); P7 (see M4). With --rehearsal <dir>: a second freeze into the rehearsal's log is refused and its plan is the latest.
Every run records the SHA-256 of every tested file (m-7).
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v09.py [<out.json>] [--rehearsal <dir>]
"""
import copy
import gzip
import json
import math
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
import c1_guard_v03 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v09")
R17C = os.path.join(W, "70_TESTS", "c1_v01", "r17c_probes")
README = os.path.join(C1, "README_C1_CODE_v06.md")
PY = sys.executable
UUID = "00000000-0000-4000-8000-000000000001"
TESTED = ["c1_guard_v03.py", "c1_freeze_v04.py", "c1_analyse_v06.py", "c1_predarm_v04.py", "c1_fit_v04.py", "c1_run_v04.py", "c1_mstage_v04.py",
          "c1_h8_v04.py", "c1_e0_v03.py", "c1_folds_v03.py", "c1_legacy_refuse_v01.py", "tests/test_c1_v09.py", "../tpp/tpp_keys_v02.py",
          "../tpp/tpp_run_v02.py", "../av2/av2_cache_stageB_v04.py", "../k8/k8_items_v06.py"]
STATE = {}


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except (AssertionError, SystemExit) as e:
        return str(e) or "refused"
    return None


def sub(cmd, cwd=C1):
    r = subprocess.run([PY, "-B"] + cmd, capture_output=True, text=True, cwd=cwd)
    return r.returncode, (r.stdout + r.stderr)


def wj(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(o, open(p, "w"), indent=1)
    return p


def env_block():
    v = G.versions()
    return "FROZEN_ENV_BEGIN\n%s\nFROZEN_ENV_END\n" % "\n".join("%s  %s" % (k, v[k]) for k in ("python", "numpy", "scipy"))


def mock_plan(d, name, paths, roles=(), env=True, log=None):
    os.makedirs(d, exist_ok=True)
    plan = os.path.join(d, name)
    body = "# mock plan %s\n\nFROZEN_HASHES_BEGIN\n%s\nFROZEN_HASHES_END\n" % (name, "\n".join("%s  %s" % (G.sha(os.path.join(W, p)), p) for p in paths))
    if roles:
        body += "FROZEN_ROLES_BEGIN\n%s\nFROZEN_ROLES_END\n" % "\n".join("%s  %s" % (r, p) for r, p in roles)
    if env:
        body += env_block()
    open(plan, "w", encoding="utf-8", newline="\n").write(body)
    open(plan[:-3] + ".sha256", "w").write(G.sha(plan) + "  %s\n" % name)
    log = log or os.path.join(d, "LOG.txt")
    open(log, "a").write(G.sha(plan) + "  %s\n" % name)
    return plan, log


# ---------------------------------------------------------------------------------------------------------------- G3
def t_g3():
    assert not os.path.exists(G.CANONICAL["C1"]), "the real C1 hash log exists"
    d = os.path.join(OUT, "g3")
    shutil.rmtree(d, ignore_errors=True)
    f = "50_CODE/c1_av2/c1_guard_v03.py"
    pa, log = mock_plan(d, "PA.md", [f])
    side, fr = G.frozen_plan(pa, "nuscenes", log)
    assert fr.log_sha256 == G.sha(log) and fr.env
    pb, _ = mock_plan(d, "PB.md", [f], log=log)
    r = raises(G.frozen_plan, pa, "nuscenes", log)
    assert r and "LATEST" in r, "an older line must be refused (R17c M1)"
    G.frozen_plan(pb, "nuscenes", log)
    pc, logc = mock_plan(os.path.join(d, "noenv"), "PC.md", [f], env=False)
    side, frc = G.frozen_plan(pc, "nuscenes", logc)
    assert raises(G.check_env, frc) and "FROZEN_ENV" in raises(G.check_env, frc)
    frc.env = {"python": "0.0", "numpy": "0", "scipy": "0"}
    assert "differ" in raises(G.check_env, frc)
    w = os.path.join(d, "exp_fake")
    os.makedirs(w, exist_ok=True)
    json.dump({"status_X1_gates": "PASS"}, open(os.path.join(w, "x1_export_record.json"), "w"))
    json.dump([{"scene": "scene-0001"}], open(os.path.join(w, "x1_per_frame.json"), "w"))
    with gzip.open(os.path.join(w, "x1_tracks.jsonl.gz"), "wt") as fh:
        fh.write(json.dumps({"scene": UUID}) + "\n")
    assert G.export_dataset([w]) == "av2", "m7: the names come from the tracks file"
    assert G.export_dataset([os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker0")]) == "nuscenes"
    return {"older_line": "refused", "no_env": "refused", "version_mismatch": "refused", "m7_tracks_names": "av2 from tracks"}


# ---------------------------------------------------------------------------------------------------------------- FRZ4
def readme_with_test(test_rel, dst):
    lines = open(README, encoding="utf-8").read().splitlines()
    keep = [l for l in lines if not l.strip().endswith("  test") and ("  %s  " % test_rel) not in l]
    p = os.path.join(W, test_rel)
    keep.append("%s  %s  test" % (G.sha(p), test_rel))
    open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(keep) + "\n")
    return dst


def frz_args(d, plan, readme, log, extra=()):
    reh = STATE.get("frz_data")
    if not reh:
        units = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")))["scenes"])
        lp = os.path.join(d, "units.txt")
        open(lp, "w").write("\n".join("%s %s" % (u, "held_out_train" if i < 60 else "val") for i, u in enumerate(units)) + "\n")
        fo = os.path.join(d, "folds.json")
        subprocess.run([PY, "-B", "c1_folds_v03.py", "--logs", lp, "--out", fo, "--dataset", "nuscenes"], cwd=C1, check=True, capture_output=True)
        subprocess.run([PY, "-B", "c1_folds_v03.py", "--restrict-from", fo, "--source", "val", "--out", os.path.join(d, "folds_val150.json")], cwd=C1, check=True, capture_output=True)
        subprocess.run([PY, "-B", "c1_folds_v03.py", "--restrict-from", fo, "--source", "held_out_train", "--out", os.path.join(d, "folds_train225.json")],
                       cwd=C1, check=True, capture_output=True)
        wj(os.path.join(d, "split.json"), {"rule": "probe split"})
        wj(os.path.join(d, "config.json"), {"note": "probe config"})
        os.makedirs(os.path.join(d, "emptyroot"), exist_ok=True)
        reh = STATE["frz_data"] = {"folds": fo, "v150": os.path.join(d, "folds_val150.json"), "t225": os.path.join(d, "folds_train225.json"),
                                   "split": os.path.join(d, "split.json"), "config": os.path.join(d, "config.json"), "root": os.path.join(d, "emptyroot")}
    TF = os.path.join(W, "60_RESULTS", "c1_transfer_fits_v01")
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % p, "MANIFEST.json") for p in ("train", "val")]
    return (["c1_freeze_v04.py", "--plan", plan, "--readme", readme, "--results-dir", os.path.join(d, "results"), "--folds", reh["folds"],
             "--split", reh["split"], "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"), os.path.join(TF, "c1_transfer_fits_t3_v01.json"),
             "--stageA-manifests"] + man + ["--config", reh["config"], "--folds-val150", reh["v150"], "--folds-train225", reh["t225"],
             "--hash-log", log, "--data-root", reh["root"], "--test-out-dir", os.path.join(d, "tests_out")] + list(extra))


def t_frz4():
    d = os.path.join(OUT, "frz4")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    rp = readme_with_test("50_CODE/c1_av2/tests/freeze_probe_pass_v01.py", os.path.join(d, "README_probe.md"))
    log = os.path.join(d, "LOG.txt")
    tmpl = "# probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n"
    out = {}
    p1 = os.path.join(d, "PLAN_1.md")
    open(p1, "w").write(tmpl % 1)
    rc, o = sub(frz_args(d, p1, rp, log))
    assert rc == 0 and "C1 FREEZE V04 DONE" in o, o[-1500:]
    txt = open(p1, encoding="utf-8").read()
    assert "FROZEN_ENV_BEGIN" in txt and "FROZEN_TESTS_BEGIN" in txt and "ALL_PASS" in txt and "folds_val150" in txt
    side1, fr1 = G.frozen_plan(p1, "nuscenes", log)
    out["first_freeze"] = "done (%s)" % side1[:12]
    p2 = os.path.join(d, "PLAN_2.md")
    open(p2, "w").write(tmpl % 2)
    rc, o = sub(frz_args(d, p2, rp, log))
    assert rc != 0 and "one freeze only" in o, o[-800:]
    out["second_freeze"] = "refused (P6)"
    rc, o = sub(frz_args(d, p2, rp, log, ["--amend", "probe amendment"]))
    assert rc == 0, o[-1500:]
    assert os.path.exists(os.path.join(d, "C1_DEVIATION_LOG_REHEARSAL.md"))
    assert raises(G.frozen_plan, p1, "nuscenes", log) and G.frozen_plan(p2, "nuscenes", log)
    out["amend"] = "appended, logged; only the new plan accepted"
    os.makedirs(os.path.join(d, "root_b", "cacheX"), exist_ok=True)
    wj(os.path.join(d, "root_b", "cacheX", "MANIFEST.json"), {"stage": "B", "dataset": "nuscenes", "scenes": {}})
    p3 = os.path.join(d, "PLAN_3.md")
    open(p3, "w").write(tmpl % 3)
    a3 = frz_args(d, p3, rp, os.path.join(d, "LOG3.txt"))
    a3[a3.index("--data-root") + 1] = os.path.join(d, "root_b")
    rc, o = sub(a3)
    assert rc != 0 and "stage-B manifest exists" in o, o[-800:]
    out["stage_B_present"] = "refused"
    rf = readme_with_test("50_CODE/c1_av2/tests/freeze_probe_fail_v01.py", os.path.join(d, "README_fail.md"))
    rc, o = sub(frz_args(d, p3, rf, os.path.join(d, "LOG4.txt")))
    assert rc != 0 and "did not print ALL_PASS" in o, o[-800:]
    out["failing_test"] = "refused"
    ma = wj(os.path.join(d, "stageA_bad", "MANIFEST.json"), {"stage": "A", "dataset": "nuscenes", "scenes": {"scene-0001": {}}, "inputs": {"builder_sha256": "0" * 64}})
    a5 = frz_args(d, p3, rp, os.path.join(d, "LOG5.txt"))
    i = a5.index("--stageA-manifests")
    a5.insert(i + 1, ma)
    rc, o = sub(a5)
    assert rc != 0 and "not a bound builder" in o, o[-800:]
    out["m8_unbound_builder"] = "refused"
    bad = json.load(open(STATE["frz_data"]["v150"]))
    k = sorted(bad["fold_of_log"])[0]
    bad["fold_of_log"][k] = (bad["fold_of_log"][k] + 1) % 5
    bp = wj(os.path.join(d, "folds_val150_rerandomised.json"), bad)
    a6 = frz_args(d, p3, rp, os.path.join(d, "LOG6.txt"))
    a6[a6.index("--folds-val150") + 1] = bp
    rc, o = sub(a6)
    assert rc != 0 and "not a restriction" in o, o[-800:]
    out["rerandomised_child"] = "refused"
    STATE["frz_plan"] = (p2, log)
    return out


# ---------------------------------------------------------------------------------------------------------------- M2
def planted(h1=True):
    import c1_analyse_v06 as A6
    fb = {"met": h1, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False, "pops": {}} for a in A6.REQUIRED_ARMS}
    return {"within_lt3d": {t: {"form_b": fb, "status": st, "form_c": None, "form_a": {}} for t in A6.TRACKERS}}


class Boom(dict):
    def __getitem__(self, k):
        raise RuntimeError("planted failure in a secondary table")

    def get(self, k, d=None):
        raise RuntimeError("planted failure in a secondary table")

    def __contains__(self, k):
        raise RuntimeError("planted failure in a secondary table")


def t_m2():
    import c1_analyse_v06 as A6
    out = {}
    cfg = json.load(open(os.path.join(W, "70_TESTS", "c1_v01", "rehearsal150_v05b", "config.json")))
    c2 = copy.deepcopy(cfg)
    c2["e0"]["inputs"]["gt"] = os.path.join(OUT, "m2", "moved_gt.json")
    r = A6.e0_check(c2, "c1", None)
    assert r["ok"] is False and r["reason"], "P3: a moved E0 input must not raise"
    out["P3_e0_moved_input"] = r["reason"][:100]
    t = A6.load_table("method_stage", "entry:c1_mstage", {"method_stage": {"t1": os.path.join(OUT, "nope.json"), "t3": os.path.join(OUT, "nope.json")}},
                      "smoke", None, None, None, A6.TRACKERS, None, "nuscenes")
    assert t["ok"] is False
    d = A6.decide(planted(), {"routes": []}, "smoke", {"tables": {"method_stage": {"ok": True, "data": {x: {} for x in A6.TRACKERS}, "checks": {}}}})
    assert d["C1_verdict"] == "GO" and all(d["claims_status"][c] == "not tested" for c in ("H6a", "H6b", "H7"))
    assert "exception" in d["hypotheses"]["H6a"]["reasons"][0]
    out["P4e_malformed_method_stage"] = d["hypotheses"]["H6a"]["reasons"][0][:90]
    d2 = A6.decide(planted(), {"routes": [], "h9_label": "secondary"}, "smoke",
                   {"tables": {"h9": {"ok": True, "data": {x: Boom() for x in A6.TRACKERS}, "checks": {}}}})
    assert d2["C1_verdict"] == "GO" and d2["claims_status"]["H9"] == "not tested" and "planted failure" in d2["hypotheses"]["H9"]["reasons"][0]
    res = planted()
    res["within_lt3d"]["t3"] = Boom()
    d3 = A6.decide(res, {"routes": []}, "smoke", {})
    assert d3["C1_verdict"] == "NO-GO" and any("exception on an H1 input" in x for x in d3["nogo_reasons"])
    out["H1_input_exception"] = d3["nogo_reasons"][0][:90]
    m = os.path.join(OUT, "m2", "main")
    shutil.rmtree(m, ignore_errors=True)
    runs = os.path.join(m, "runs")
    cache = os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val")
    wj(os.path.join(runs, "run_record_t1_w_decide.json"), {"c1": False, "caches": [cache]})
    wj(os.path.join(runs, "run_record_t3_w_decide.json"), {"c1": False, "caches": [cache]})
    fp = wj(os.path.join(m, "folds.json"), {"fold_of_log": {"scene-0001": 0}, "dataset": "nuscenes", "source_of_log": {}})
    cf = wj(os.path.join(m, "cfg.json"), {"routes": [{"name": "within_lt3d", "runs": runs, "tags": {"t1": "t1_w", "t3": "t3_w"}},
                                                     {"name": "transfer_lt3d", "runs": runs, "tags": {"t1": "t1_x", "t3": "t3_x"}}], "folds": fp})
    rc, o = sub(["c1_analyse_v06.py", "--config", cf, "--out", os.path.join(m, "o.json"), "--decision", os.path.join(m, "dec.json"), "--smoke", "--boot", "10"])
    assert rc == 0, o[-1500:]
    dm = json.load(open(os.path.join(m, "dec.json")))
    assert dm["C1_verdict"] == "NO-GO" and dm["claims_status"]["H4"] == "not tested" and dm["route_problems"]["within_lt3d"]
    out["main_broken_within_and_missing_transfer"] = {"verdict": dm["C1_verdict"], "H4": dm["claims_status"]["H4"], "decision_written": True}
    return out


# ---------------------------------------------------------------------------------------------------------------- M3
def table_case(n_units=200, e2=6, hl=3, rates_e2=0.02, rates_hl=(0.02, 0.02, 0.02), n_per=12, seed=1):
    rng = np.random.default_rng(seed)
    nc = e2 + hl
    N = np.full((n_units, nc), float(n_per))
    p = np.array([rates_e2] * e2 + list(rates_hl))
    X = rng.binomial(N.astype(int), p[None, :]).astype(float)
    if hl:
        N[:, e2:] = N[:, :e2].sum(1, keepdims=True) / hl
        X[:, e2:] = np.stack([rng.binomial(N[:, e2 + j].astype(int), rates_hl[j]) for j in range(hl)], 1)
    cells = [("e2_%d" % j, []) for j in range(e2)] + [("hist=2", []), ("hist=3-4", []), ("hist>=5", [])][:hl]
    scene = np.array(["scene-%04d" % i for i in range(n_units)])
    logs = np.arange(n_units) % 40
    Wb = np.random.default_rng(seed + 1).multinomial(40, np.full(40, 1 / 40.0), size=2000).astype(float)[:, logs]
    return N, X, cells, e2, scene, logs, Wb


def t_m3():
    import c1_predarm_v04 as P4
    out = {}
    N, X, cells, e2, sc, lg, Wb = table_case(e2=3)
    r = P4.h9_rule_v04(N, X, cells, e2, sc, lg, Wb, [20261111, 0, 5])
    r01 = P4.CA.h9_rule(N, X, cells, sc, lg, Wb, [20261111, 0, 5])
    assert r["family_size_E2"] == 3 and not r["H9"] and r01["family_size"] >= 6, (r, r01["family_size"])
    out["3E2_3HL"] = {"v04": r["H9"], "E2_qualified": r["family_size_E2"], "v01_family_size": r01["family_size"], "v01_H9": r01["H9"]}
    N, X, cells, e2, sc, lg, Wb = table_case(e2=7)
    r = P4.h9_rule_v04(N, X, cells, e2, sc, lg, Wb, [20261111, 0, 5])
    assert r["H9"] and r["family_size_E2"] >= 6, r
    out["7E2_clean"] = {"H9": r["H9"], "E2_qualified": r["family_size_E2"]}
    N, X, cells, e2, sc, lg, Wb = table_case(e2=7, rates_hl=(0.20, 0.02, 0.02))
    r = P4.h9_rule_v04(N, X, cells, e2, sc, lg, Wb, [20261111, 0, 5])
    assert not r["H9"] and "hist=2" in r["hl_cells_flagged"] and r["family_size_E2"] >= 6, r
    out["flagged_HL_cell"] = {"H9": r["H9"], "hl_cells_flagged": r["hl_cells_flagged"], "E2_qualified": r["family_size_E2"]}
    assert P4.s20c_label({"family_size_E2": 5}) == "descriptive" and P4.s20c_label({"family_size_E2": 6}) == "secondary"
    out["powered_pipeline"] = powered()
    return out


def make_powered(d, seed=21, n_scenes=200, n_logs=25, rec=(50, 80), inpath=0.9, factor=None):
    import test_tpp_analyse_v01 as TT
    C, A, KAPPA = TT.C, TT.A, TT.KAPPA
    rng = np.random.default_rng(seed)
    logs = np.array(["log%02d" % (i % n_logs) for i in range(n_scenes)])
    names = ["scene-%04d" % (i + 1) for i in range(n_scenes)]
    R = {k: [] for k in ("s", "k", "h", "pair", "yaw", "sign_long", "sign_lat", "gap_long", "gap_lat", "hist_stratum_trk", "rel")}
    I = {k: [] for k in ("rec", "a", "s", "g", "r", "m", "l0", "inpath", "h", "ref_relied")}
    Sig, errs, n = [], {a: [] for a in KAPPA}, 0
    for si in range(n_scenes):
        for p in range(int(rng.integers(*rec))):
            yaw = rng.uniform(-np.pi, np.pi)
            g, r, m = int(rng.choice([0, 1, 3], p=[0.6, 0.25, 0.15])), int(rng.integers(0, 3)), int(rng.choice([0, 1, 2, 3], p=[0.4, 0.4, 0.15, 0.05]))
            gaps = rng.uniform(0.1, 12, 2)
            rel = int(np.argmax(gaps))
            sg = rng.choice([-1.0, 1.0], 2)
            hs = int(rng.integers(0, 3))
            for k_, v in (("s", si), ("k", int(rng.integers(1, 38))), ("h", 3), ("pair", p + 1), ("yaw", yaw), ("sign_long", sg[0]), ("sign_lat", sg[1]),
                          ("gap_long", gaps[0]), ("gap_lat", gaps[1]), ("hist_stratum_trk", hs), ("rel", rel)):
                R[k_].append(v)
            ax = np.array([[math.cos(yaw), math.sin(yaw)], [-math.sin(yaw), math.cos(yaw)]])
            sl, st = rng.uniform(0.3, 2.0), rng.uniform(0.2, 1.2)
            Sig.append(C.cov3(ax.T @ np.diag([sl ** 2, st ** 2]) @ ax))
            for arm, (kl, kt) in KAPPA.items():
                f = (factor if (factor and arm == "TPP" and hs == 0) else 1.0)
                errs[arm].append(f * rng.multivariate_normal(np.zeros(2), ax.T @ np.diag([kl * sl ** 2, kt * st ** 2]) @ ax))
            for a_ in range(2):
                I["rec"].append(n); I["a"].append(a_); I["s"].append(si); I["g"].append(g); I["r"].append(r); I["m"].append(m)
                I["l0"].append(((g * 3 + r) * 2 + a_) * 4 + m); I["inpath"].append(bool(rng.random() < inpath)); I["h"].append(3)
                I["ref_relied"].append(a_ == rel)
            n += 1
    gt = rng.normal(size=(n, 2)) * 50 + 500
    kz = {"rec_" + k: np.array(v) for k, v in R.items()}
    kz.update({"item_" + k: np.array(v) for k, v in I.items()})
    kz["rec_hist_stratum_gt"] = kz["rec_hist_stratum_trk"].copy()
    kz.update({"scene_names": np.array(names), "scene_logs": logs, "stamp": np.array(A.SYN_STAMP), "syn_gt_xy": gt,
               "syn_trk_mu": gt - np.array(errs["TRK"]), "syn_trk_cov": np.array(Sig), "cache_dir": np.array("none")})
    os.makedirs(d, exist_ok=True)
    kp = os.path.join(d, "keys.npz")
    np.savez(kp, **kz)
    mu = gt - np.array(errs["TPP"])
    z = {"rec_index": np.arange(n), "rec_pair": kz["rec_pair"], "rec_s": kz["rec_s"], "status": np.zeros(n, np.int8), "v2_mu": mu,
         "v2_cov": np.array(Sig), "v1_mu": mu, "v1_cov": np.array(Sig), "stamp": np.array(A.SYN_STAMP)}
    rp = os.path.join(d, "run_trk.npz")
    np.savez(rp, **z)
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s syn" % x for x in names))
    subprocess.run([PY, "-B", "c1_folds_v02.py", "--logs", lp, "--out", os.path.join(d, "folds.json"), "--dataset", "nuscenes"], cwd=C1, check=True,
                   capture_output=True)
    return kp, rp, os.path.join(d, "folds.json")


def powered():
    out = {}
    for name, factor in (("control", None), ("planted_x2_short_history", 2.0)):
        d = os.path.join(OUT, "powered", name)
        kp, rp, fp = make_powered(d, factor=factor)
        o = os.path.join(d, "pa.json")
        rc, txt = sub(["c1_predarm_v04.py", "--keys", kp, "--runs", "trk=" + rp, "--folds", fp, "--tracker-index", "0", "--synthetic", "--out", o])
        assert rc == 0, txt[-1500:]
        r = json.load(open(o))["arms"]["TPP"]["PD"]
        out[name] = {"HL_H9": r["HL"]["H9"], "HL_E2_qualified": r["HL"]["family_size_E2"], "HL_flagged": r["HL"]["flagged"] + r["HL"]["family_flagged"],
                     "noHL_H9": r["noHL"]["H9"], "noHL_family_size": r["noHL"]["family_size"], "noHL_flagged": r["noHL"]["flagged"],
                     "noHL_on_HL_cells_hist_flagged": r["noHL_on_HL_cells"]["hl_cells_flagged"],
                     "noHL_exceed_by_hl": r["noHL_on_HL_cells"]["exceed_share_by_hl"], "HL_exceed_by_hl": r["HL"]["exceed_share_by_hl"]}
    c, p = out["control"], out["planted_x2_short_history"]
    assert c["HL_H9"] and c["HL_E2_qualified"] >= 6, "a powered synthetic case where the HL-stratified H9 holds (Choice 39b): %s" % c
    assert p["noHL_family_size"] >= 6 and p["noHL_H9"], "the D17-style family, with power, misses the short-history excess: %s" % p
    assert "hist=2" in p["noHL_on_HL_cells_hist_flagged"], "the HL cells catch it under the noHL fit: %s" % p
    assert p["HL_H9"], "the HL stratum calibrates it: %s" % p
    return out


# ---------------------------------------------------------------------------------------------------------------- M4
def t_m4():
    out = {}
    me, g3, pa = "50_CODE/c1_av2/c1_h8_v04.py", "50_CODE/c1_av2/c1_guard_v03.py", "50_CODE/c1_av2/c1_predarm_v04.py"
    plan, log = mock_plan(os.path.join(OUT, "m4"), "PM.md", [me, g3, pa], roles=[("entry:c1_h8", me), ("module", g3), ("entry:c1_predarm", pa)])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    u = G.units_record(["scene-0001", "scene-0002"])
    good = {"provenance": {"plan_sha256": side, "folds_sha256": "f" * 64, "entry_point": {me: fr[me]}, "code_sha256": {me: fr[me], g3: fr[g3]},
                           "inputs_sha256": {"x": "0" * 64}, "inputs_checked": True, "units": u, "dataset": "nuscenes", "hash_log_sha256": fr.log_sha256}}
    G.check_table(good, side, fr, "f" * 64, "entry:c1_h8", units=u["units"], dataset="nuscenes")
    assert raises(G.check_table, good, side, fr, "f" * 64, "entry:c1_h8", units=["scene-0001"], dataset="nuscenes")
    assert raises(G.check_table, good, side, fr, "f" * 64, "entry:c1_h8", units=u["units"], dataset="av2")
    bad = copy.deepcopy(good)
    bad["provenance"]["units"]["units_sha256"] = "0" * 64
    assert raises(G.check_table, bad, side, fr, "f" * 64, "entry:c1_h8")
    out["check_table"] = "units, units hash and dataset enforced"
    p7 = os.path.join(R17C, "p7")
    o = os.path.join(OUT, "m4", "p7_out.json")
    kp = os.path.join(OUT, "m4", "keys_hl.npz")
    kz = dict(np.load(os.path.join(R17C, "p5", "syn_keys.npz"), allow_pickle=False))
    kz["rec_hist_stratum_gt"] = kz["rec_hist_stratum_trk"].copy()
    np.savez(kp, **kz)
    rc, txt = sub(["c1_predarm_v04.py", "--keys", kp, "--runs", "trk=" + os.path.join(R17C, "p5", "syn_run_trk.npz"), "--folds",
                   os.path.join(p7, "folds_plus40.json"), "--tracker-index", "0", "--synthetic", "--out", o])
    assert rc != 0 and "fold units without keys" in txt and not os.path.exists(o), txt[-600:]
    out["P7_keys_subset_of_folds"] = "refused"
    import c1_predarm_v04 as P4
    d = os.path.join(OUT, "m4", "seed")
    os.makedirs(d, exist_ok=True)
    rpath = os.path.join(d, "run.npz")
    open(rpath, "wb").write(b"x")
    wj(rpath[:-4] + "_summary.json", {"seed": 20261104})
    assert raises(P4.run_seed, rpath, 20261102, False) and P4.run_seed(rpath, 20261104, False)["verified"]
    assert raises(P4.parse_runs, ["trk@20261199=x"])
    out["run_seed"] = "a summary seed other than the label's is refused"
    import c1_analyse_v06 as A6
    pv = dict(good["provenance"], entry_point={pa: fr[pa]}, code_sha256={pa: fr[pa], g3: fr[g3]})
    tb = {"provenance": dict(pv, seeds={"trk": {"seed": 20261104, "verified": True}}, chains={"runs": {"trk": {"seed": 20261104}}})}
    tp = wj(os.path.join(d, "h9_wrongseed.json"), tb)
    r = A6.load_table("h9", "entry:c1_predarm", {"h9": {"t1": tp, "t3": tp}}, "c1", side, fr, "f" * 64, A6.TRACKERS, u["units"], "nuscenes")
    assert r["ok"] is False and "20261102" in r["why"], r
    tg = {"provenance": dict(pv, seeds={"trk": {"seed": 20261102, "verified": True}}, chains={"runs": {"trk": {"seed": 20261102}}})}
    tq = wj(os.path.join(d, "h9_rightseed.json"), tg)
    r2 = A6.load_table("h9", "entry:c1_predarm", {"h9": {"t1": tq, "t3": tq}}, "c1", side, fr, "f" * 64, A6.TRACKERS, u["units"], "nuscenes")
    assert r2["ok"] is True, r2
    out["primary_seed"] = "a primary table from another seed is not valid"
    cd = wj(os.path.join(OUT, "m4", "cache_av2", "MANIFEST.json"), {"dataset": "av2", "stage": "B", "scenes": {UUID: {}}})
    rc, txt = sub([os.path.join(W, "50_CODE", "tpp", "tpp_keys_v02.py"), "--cache", os.path.dirname(cd), "--out", os.path.join(OUT, "m4", "k.npz"),
                   "--scenes", UUID])
    assert rc != 0 and "--scenes is refused" in txt, txt[-500:]
    kav = os.path.join(OUT, "m4", "keys_av2.npz")
    np.savez(kav, scene_names=np.array([UUID]))
    rc, txt = sub([os.path.join(W, "50_CODE", "tpp", "tpp_run_v02.py"), "--tpp-root", "x", "--keys", kav, "--source", "trk", "--out",
                   os.path.join(OUT, "m4", "r.npz"), "--scenes", UUID])
    assert rc != 0 and "--scenes is refused" in txt, txt[-500:]
    out["tpp_scenes_on_av2"] = "refused (keys and run)"
    return out


# ---------------------------------------------------------------------------------------------------------------- MINOR
def t_minor():
    import c1_analyse_v06 as A6
    out = {}
    tab = {t: {"arms": {}, "population": "PD"} for t in A6.TRACKERS}
    d = A6.decide(planted(), {"routes": [], "h9_label": "secondary"}, "smoke", {"tables": {"h9": {"ok": True, "data": tab, "checks": {}}}})
    assert d["claims_status"]["H9"] == "not tested", d["claims_status"]
    out["m1_no_TPP_arm"] = "not tested"
    p2 = os.path.join(R17C, "p2")
    rc, txt = sub(["c1_e0_v03.py", "--workers", os.path.join(p2, "worker_av2"), "--gt", os.path.join(p2, "gt.json"), "--meta", os.path.join(p2, "meta"),
                   "--horizon", os.path.join(p2, "horizon.jsonl.gz"), "--out", os.path.join(OUT, "e0x.json"), "--seed", "1"])
    assert rc != 0 and "seed is fixed" in txt, txt[-400:]
    rc, txt = sub(["c1_e0_v03.py", "--workers", os.path.join(p2, "worker_av2"), "--gt", os.path.join(p2, "gt.json"), "--meta", os.path.join(p2, "meta"),
                   "--horizon", os.path.join(p2, "horizon.jsonl.gz"), "--out", os.path.join(OUT, "e0x.json"), "--mode", "x1"])
    assert rc != 0 and "mode x1" in txt, txt[-400:]
    out["m2_e0_seed_mode"] = "refused"
    e = A6.e0_check({"e0": {"seed": 7, "inputs": {}}}, "c1", None)
    assert e["ok"] is False and "20261114" in e["reason"]
    me = "50_CODE/c1_av2/c1_run_v04.py"
    f = "50_CODE/c1_av2/c1_guard_v03.py"
    fo = wj(os.path.join(OUT, "minor", "folds.json"), {"fold_of_log": {"scene-0001": 0}, "dataset": "nuscenes"})
    plan, log = mock_plan(os.path.join(OUT, "minor"), "PN.md", [me, f, G.rel(fo)], roles=[("entry:c1_run", me), ("folds", G.rel(fo))])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    rr = {"c1": True, "c1_plan_sha256": side, "c1_folds_sha256": fr[G.rel(fo)], "caches": ["x"], "fits_sha256": "0",
          "provenance_v04": {"plan_sha256": side, "entry_point": {me: fr[me]}, "code_sha256": {me: fr[me]}, "cache_chains": [{"dataset": "av2"}],
                             "hash_log_sha256": fr.log_sha256}}
    r = raises(A6.check_route_c1, rr, {"name": "within_lt3d", "tags": {"t1": "x"}, "fits": {"t1": fo}}, "t1", side, fr, "nuscenes")
    assert r and "R17c m3" in r, r
    out["m3_cache_dataset"] = "refused"
    return out


# ---------------------------------------------------------------------------------------------------------------- 38b / 38c
def full_aux(seeds):
    import c1_analyse_v06 as A6
    d9 = {t: {"H9": True, "H9_noHL": True, "arms": {"TPP": {}}, "population": "PD", "H9_seed": dict(seeds)} for t in A6.TRACKERS}
    return {"tables": {"h9": {"ok": True, "data": d9, "checks": {}}}}


def strip(dec, drop=()):
    keep = {k: dec[k] for k in ("C1_verdict", "gate_H1", "family_S", "claims_status", "nogo_reasons")}
    keep["claims_status"] = {c: v for c, v in keep["claims_status"].items() if c not in drop}
    return json.dumps(keep, sort_keys=True, default=str)


def t_s38b():
    import c1_analyse_v06 as A6
    base = {"20261102": True, "20261104": True, "20261105": True}
    d0 = A6.decide(planted(), {"routes": [], "h9_label": "secondary"}, "smoke", full_aux(base))
    d1 = A6.decide(planted(), {"routes": [], "h9_label": "secondary"}, "smoke", full_aux(dict(base, **{"20261104": False, "20261105": False})))
    d2 = A6.decide(planted(), {"routes": [], "h9_label": "secondary"}, "smoke", full_aux({"20261102": True}))
    assert d0["hypotheses"]["H9_seed_robustness"]["label_value"] == "seed-robust" and d1["hypotheses"]["H9_seed_robustness"]["label_value"] == "not seed-robust"
    assert d2["claims_status"]["H9_seed_robustness"] == "not tested"
    drop = ("H9_seed_robustness",)
    assert strip(d0, drop) == strip(d1, drop) == strip(d2, drop), "the robustness seeds changed something else"
    assert d0["claims_status"]["H9"] == d1["claims_status"]["H9"] == "holds" and "H9_seed_robustness" not in d0["family_S"]
    return {"flip": "only H9_seed_robustness changes", "remove": "not tested; nothing else changes"}


def t_s38c():
    import c1_analyse_v06 as A6
    fb_ok = {"met": True, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False, "pops": {}} for a in A6.REQUIRED_ARMS}
    base = planted()
    outs = {}
    for name, tab in (("passing", {"form_b": fb_ok, "status": st, "form_c": None, "form_a": {}}),
                      ("failing", {"form_b": dict(fb_ok, met=False), "status": {"Mstar": {"valid": False}}, "form_c": None, "form_a": {}}),
                      ("missing", None)):
        res = copy.deepcopy(base)
        if tab is not None:
            res["within_lt3d"]["tab"] = tab
        d = A6.decide_all(res, {"routes": []}, "smoke", {})
        outs[name] = d
    s = {k: strip(v) for k, v in outs.items()}
    assert s["passing"] == s["failing"] == s["missing"], "AB3DMOT reached the primary decision"
    assert outs["passing"]["descriptive_trackers"]["routes"]["within_lt3d"]["tab"]["form_b"]["met"] is True
    assert outs["failing"]["descriptive_trackers"]["routes"]["within_lt3d"]["tab"]["form_b"]["met"] is False
    assert "within_lt3d" not in outs["missing"]["descriptive_trackers"]["routes"]
    assert raises(A6.decide, {"within_lt3d": {"tab": {}}}, {"routes": []}, "smoke", {})
    return {"byte_identical": True, "descriptive_block": "differs as expected", "decide_refuses_tab": True}


def t_s38d():
    d = os.path.join(OUT, "s38d")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    lp = os.path.join(d, "units.txt")
    names = ["scene-%04d" % i for i in range(1, 41)]
    open(lp, "w").write("\n".join("%s %s" % (n, "held_out_train" if i < 15 else "val") for i, n in enumerate(names)) + "\n")
    fo = os.path.join(d, "folds.json")
    subprocess.run([PY, "-B", "c1_folds_v03.py", "--logs", lp, "--out", fo, "--dataset", "nuscenes"], cwd=C1, check=True, capture_output=True)
    for src, nm in (("val", "folds_val150.json"), ("held_out_train", "folds_train225.json")):
        subprocess.run([PY, "-B", "c1_folds_v03.py", "--restrict-from", fo, "--source", src, "--out", os.path.join(d, nm)], cwd=C1, check=True, capture_output=True)
    v150, t225 = os.path.join(d, "folds_val150.json"), os.path.join(d, "folds_train225.json")
    par, ch = json.load(open(fo)), json.load(open(v150))
    assert all(par["fold_of_log"][u] == f for u, f in ch["fold_of_log"].items()) and len(ch["fold_of_log"]) == 25 and "permutation" not in ch
    rr = [G.rel(p) for p in (fo, v150, t225)]
    plan, log = mock_plan(d, "PD.md", rr, roles=[("folds", rr[0]), ("folds_val150", rr[1]), ("folds_train225", rr[2])])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    G.check_child_folds(v150, fr)
    G.check_child_folds(t225, fr)
    bad = dict(ch, fold_of_log=dict(ch["fold_of_log"]))
    k = sorted(bad["fold_of_log"])[0]
    bad["fold_of_log"][k] = (bad["fold_of_log"][k] + 1) % 5
    bp = wj(os.path.join(d, "rerand.json"), bad)
    r = raises(G.check_child_folds, bp, fr)
    assert r and "re-randomised" in r
    ov = dict(json.load(open(t225)))
    ov["fold_of_log"] = dict(ov["fold_of_log"], **{sorted(ch["fold_of_log"])[0]: 0})
    op = wj(os.path.join(d, "train_overlap.json"), ov)
    items = os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_t1.npz")
    rc, txt = sub(["c1_fit_v04.py", "--items", items, "--folds", op, "--apply-folds", v150, "--route", "source", "--out", os.path.join(d, "fit.json"),
                   "--units-subset"])
    assert rc != 0 and "validation units in training" in txt, txt[-600:]
    return {"child_valid": True, "rerandomised": "refused", "source_overlap": "refused"}


# ---------------------------------------------------------------------------------------------------------------- Choice 40
def t_deposit():
    """D16 v19 Choice 40: the deposit record. The real record (40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt) is never created here; the
    passing cases use fixture records in a scratch folder on the nuScenes route only; the AV2-tagged cases are refused."""
    out = {}
    d = os.path.join(OUT, "deposit")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    assert not os.path.exists(G.DEPOSIT_RECORD), "the real deposit record exists; this test never writes it"
    side = "a" * 64
    good = os.path.join(d, "REC_good.txt")
    NL = chr(10)
    open(good, "w").write(NL.join(["frozen_plan_sha256: " + side, "registration: https://osf.io/xxxxx (fixture)", "registered_utc: 2026-11-04T00:00:00Z", ""]))
    r = G.check_deposit(side, "nuscenes", good)
    assert r["sha256"] == G.sha(good)
    for name, body in (("wrong_plan", NL.join(["frozen_plan_sha256: " + "b" * 64, "registration: x", "registered_utc: y", ""])),
                       ("no_registration", NL.join(["frozen_plan_sha256: " + side, "registration:", "registered_utc: y", ""])),
                       ("no_time", NL.join(["frozen_plan_sha256: " + side, "registration: x", ""]))):
        p = os.path.join(d, "REC_%s.txt" % name)
        open(p, "w").write(body)
        m = raises(G.check_deposit, side, "nuscenes", p)
        assert m and "OSF_DEPOSIT_GUIDE" in m, (name, m)
        out["nuscenes_fixture_" + name] = "refused"
    m = raises(G.check_deposit, side, "av2")
    assert m and "no deposit record" in m and "OSF_DEPOSIT_GUIDE_v01.md" in m, m
    out["av2_missing_record"] = "refused"
    m = raises(G.check_deposit, side, "av2", good)
    assert m and "override is refused" in m, m
    out["av2_fixture_override"] = "refused"
    stb = "50_CODE/av2/av2_cache_stageB_v04.py"
    ma = wj(os.path.join(d, "stageA", "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {}})
    plan, log = mock_plan(d, "PDEP.md", [stb, G.rel(ma)], roles=[("entry:stageB", stb), ("stageA_manifest", G.rel(ma))])
    sidep, fr = G.frozen_plan(plan, "nuscenes", log)
    sbm = {"stage": "B", "dataset": "av2", "scenes": {}, "stage_b": {"frozen_plan_sha256": sidep, "stage_a_manifest_sha256": G.sha(ma),
                                                                      "script_sha256": fr[stb]}}
    p1 = wj(os.path.join(d, "stageB_nodep", "MANIFEST.json"), sbm)
    m = raises(G.chain_cache, p1, sidep, fr)
    assert m and "deposit" in m, m
    sbm2 = dict(sbm, stage_b=dict(sbm["stage_b"], deposit_record_sha256=G.sha(good)))
    p2 = wj(os.path.join(d, "stageB_dep", "MANIFEST.json"), sbm2)
    m = raises(G.chain_cache, p2, sidep, fr)
    assert m and "no deposit record" in m, m
    out["chain_cache_av2"] = "refused without the field, and without the real record"
    src = open(os.path.join(W, stb), encoding="utf-8").read()
    i_dep, i_gt = src.index("deposit = G.check_deposit(plan_sha, dataset)"), src.index("g = json.load(open(a.gt))")
    assert i_dep < i_gt and "deposit_record_sha256" in src, "the stage-B builder must check the deposit before reading the ground truth"
    out["stageB_v04_order"] = "deposit checked before the ground truth is read; sha256 recorded in the manifest"
    return out


# ---------------------------------------------------------------------------------------------------------------- P1-P7
def t_p1p7():
    out = {}
    p1, p2 = os.path.join(R17C, "p1"), os.path.join(R17C, "p2")
    sa, gt = os.path.join(p1, "fake_stageA"), os.path.join(p1, "fake_gt.json")
    av2 = os.path.join(W, "50_CODE", "av2")
    o = os.path.join(OUT, "p1p7")
    shutil.rmtree(o, ignore_errors=True)
    os.makedirs(o)
    for v, extra in (("v01", ["--frozen-plan", os.path.join(p1, "any_file.txt"), "--frozen-plan-sha256", G.sha(os.path.join(p1, "any_file.txt"))]),
                     ("v02", ["--frozen-plan", os.path.join(p1, "PRIVATE_PLAN.md"), "--hash-log", os.path.join(p1, "private_log.txt")]),
                     ("v04", ["--frozen-plan", os.path.join(p1, "PRIVATE_PLAN.md")])):
        rc, txt = sub(["av2_cache_stageB_%s.py" % v, "--stage-a", sa, "--gt", gt, "--out", os.path.join(o, "outB_" + v)] + extra, cwd=av2)
        assert rc != 0 and "refused" in txt and not os.path.exists(os.path.join(o, "outB_" + v, "MANIFEST.json")), (v, txt[-500:])
        out["P1_stageB_" + v] = "refused"
    w, meta, hz, e0 = os.path.join(p2, "worker_av2"), os.path.join(p2, "meta"), os.path.join(p2, "horizon.jsonl.gz"), os.path.join(p2, "e0.json")
    gt2 = os.path.join(p2, "gt.json")
    ms = ["--tracker", "T1", "--experiment", "paper/local/canmot/sc", "--av2-workers", w, "--av2-gt", gt2, "--av2-meta", meta, "--av2-horizon", hz,
          "--train-workers", w, "--train-gt", gt2, "--train-meta", meta, "--train-horizon", hz, "--test"]
    cmds = {"h8_v02": ["c1_h8_v02.py", "--workers", w, "--gt", gt2, "--meta", meta, "--horizon", hz, "--e0-plan", e0, "--out", os.path.join(o, "h8_v02.json")],
            "h8_v04": ["c1_h8_v04.py", "--workers", w, "--gt", gt2, "--meta", meta, "--horizon", hz, "--e0-plan", e0, "--out", os.path.join(o, "h8_v04.json")],
            "mstage_v02": ["c1_mstage_v02.py"] + ms + ["--out", os.path.join(o, "ms_v02.json")],
            "mstage_v04": ["c1_mstage_v04.py"] + ms + ["--out", os.path.join(o, "ms_v04.json")],
            "e0_v01": ["c1_e0_v01.py", "--workers", w, "--gt", gt2, "--meta", meta, "--horizon", hz, "--out", os.path.join(o, "e0_v01.json")],
            "e0_v03": ["c1_e0_v03.py", "--workers", w, "--gt", gt2, "--meta", meta, "--horizon", hz, "--out", os.path.join(o, "e0_v03.json")],
            "predarm_v01": ["c1_predarm_v01.py", "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", os.path.join(p2, "folds.json"), "--tracker-index", "0",
                            "--out", os.path.join(o, "pa_v01.json")],
            "predarm_v04": ["c1_predarm_v04.py", "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", os.path.join(p2, "folds.json"), "--tracker-index", "0",
                            "--out", os.path.join(o, "pa_v04.json")]}
    for name, cmd in cmds.items():
        rc, txt = sub(cmd)
        assert rc != 0 and any(x in txt for x in ("refused", "need --plan", "--stageA-manifests", "training set is the nuScenes")), (name, txt[-600:])
        out["P2_" + name] = "refused"
    for f in os.listdir(o):
        assert not f.endswith(".json"), "a refused module wrote " + f
    import c1_predarm_v04 as P4
    import c1_predarm_v03 as P3
    kz = dict(np.load(os.path.join(R17C, "p5", "syn_keys.npz"), allow_pickle=False))
    kz["rec_hist_stratum_gt"] = kz["rec_hist_stratum_trk"].copy()
    TA = P3.TA
    fj = json.load(open(os.path.join(R17C, "p5", "folds.json")))
    kz2, rz, gxy, mu, cov = TA.load_inputs(os.path.join(R17C, "p5", "syn_keys.npz"), {"trk": os.path.join(R17C, "p5", "syn_run_trk.npz")}, True, None)
    kz2 = dict(kz2)
    it = TA.item_table(kz2, rz, gxy, mu, cov, TA.H_PRIMARY, "v2")
    fou = np.array([int(fj["fold_of_log"][str(n)]) for n in kz2["scene_names"]])
    N, Xc, cells, units, info = P3.tables_hl(it, kz2, "TPP", "PD", fou, True, "rec_hist_stratum_trk")
    r = P4.rule_v04(N, Xc, cells, units, kz2, 0, len(cells) - 3)
    assert r["family_size_E2"] < 6 and not r["H9"], r
    out["P5_floor_counts_E2_only"] = {"E2_qualified": r["family_size_E2"], "all_qualified": r["family_size"], "H9": r["H9"]}
    out["P6_one_freeze"] = "see FRZ4 (second freeze refused; --amend; latest line only)"
    out["P7_keys_subset"] = "see M4 (refused)"
    reh = STATE.get("rehearsal")
    if reh:
        plan = os.path.join(reh, "MOCK_C1_PLAN_v04.md")
        log = os.path.join(reh, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
        side, fr = G.frozen_plan(plan, "nuscenes", log)
        steps = [json.loads(l) for l in open(os.path.join(reh, "steps.jsonl"))]
        fz = [s["key"] for s in steps if s["key"].startswith("c1_freeze_v04.py")][0].split(" ")
        p2b = os.path.join(o, "SECOND_PLAN.md")
        open(p2b, "w").write("# second plan\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n")
        fz[fz.index("--plan") + 1] = p2b
        fz[fz.index("--results-dir") + 1] = os.path.join(o, "results2")
        rc, txt = sub(fz)
        assert rc != 0 and "one freeze only" in txt, txt[-600:]
        out["P6_rehearsal_log"] = {"second_freeze": "refused", "rehearsal_plan_is_latest": side[:12]}
    return out


def main():
    argv = sys.argv[1:]
    if "--rehearsal" in argv:
        STATE["rehearsal"] = os.path.abspath(argv[argv.index("--rehearsal") + 1])
        argv = argv[:argv.index("--rehearsal")]
    out_path = argv[0] if argv else os.path.join(OUT, "c1_tests_v09.json")
    os.makedirs(OUT, exist_ok=True)
    canon = os.path.exists(G.CANONICAL["C1"])
    t0 = time.time()
    res, ok = {"tested_files_sha256": {f: G.sha(os.path.join(C1, f)) for f in TESTED}, "python": sys.version, "versions": G.versions()}, True
    for name, fn in (("G3", t_g3), ("FRZ4", t_frz4), ("M2", t_m2), ("M3", t_m3), ("M4", t_m4), ("MINOR", t_minor), ("S38B", t_s38b), ("S38C", t_s38c),
                     ("S38D", t_s38d), ("DEPOSIT", t_deposit), ("P1P7", t_p1p7)):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-2500:], flush=True)
        json.dump(res, open(out_path + ".partial", "w"), indent=1, default=str)
    assert not canon and not os.path.exists(G.CANONICAL["C1"]), "the real C1 hash log must not exist"
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
