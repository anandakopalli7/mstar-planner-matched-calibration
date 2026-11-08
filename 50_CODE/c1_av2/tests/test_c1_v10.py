#!/usr/bin/env python3
"""Tests of C1 code v07 (Claude line, test_c1_v10, 4 Nov 2026): D16 v21 Choice 42 (R17d B1, B2, M1-M3, m1-m5, (g), (h)), with R17d's
probes PB1, PB4 and P2b and the quarantine refusal, plus every earlier suite. The ONLY bound "test" file of README v07 (c1_freeze_v05 runs
it). Synthetic, nuScenes and dummy AV2-TAGGED fixtures only (R17c's p2 and R17d's fx_av2relab, read only); every post-freeze probe
runs in a COPY TREE under 70_TESTS/c1_v01/tests_v10/tree/ (the README-bound files and the fixtures), so that the real tree never gets
a C1 hash log, a deposit record, a stage-B log, a run log, a quarantine folder or a stage-B manifest. No AV2 file is opened.
The "real C1 log absent" assertions (here and in the earlier suites' LOG, STAGEB and G3 groups) are skipped ONLY when the real
40_PROTOCOL/C1_PLAN_HASH_LOG.txt exists and C1_FREEZE_LOG_SHA256 equals its SHA-256, i.e. when c1_freeze_v05 runs this suite for an
amendment (Choice 42c); otherwise they run.
Groups:
  LEGACY  every group of test_c1_v01-v09, each suite in its own process on the live files, except those that compare generators with
          the edited files (v01 GEN, v02 GEN2/FRZ, v03 GEN3, v06 FRZ3; replaced by c1_freeze_v05's archive-aware generator check, here in
          TREE), v08 LEGACY (its suites run here directly) and v09 FRZ4 (README v06 can no longer be frozen; replaced by FRZ5).
  G4      the deposit record (m2, PB4): valid; refused for a TODO registration, "not yet", a time in 2099, a duplicated key, a time before
          the plan's log line, a time after a stage-B build, a wrong plan hash; the guide named is OSF_DEPOSIT_GUIDE_v02.md (h); exempt roles.
  TREE    in the copy tree, on the AV2-tagged stand-in: c1_freeze_v05 refuses while the plain ground truth exists (B2); c1_quarantine_v01
          (dry run, quarantine, idempotent rerun, a tampered plain file refused, a
          stage A recorded with a pod path quarantines the copy under this tree's 30_DATA); the freeze then passes; PB1: c1_h8_v05, c1_mstage_v05,
          c1_predarm_v05 under the plan without the deposit record are refused, entry:c1_e0 is exempt; P2b: x2_full_v02 can no longer run
          (the plain ground truth is gone); M1: --amend runs its probe suite with C1_FREEZE_LOG_SHA256 and passes, the same suite without it
          fails; after the deposit record --amend is refused; h8_v05 runs from the quarantine, checks scene.json (m3) and writes one
          run-log line (g); the same output again is refused; stage B v05 writes only 30_DATA/av2_cache_stageB_<tag>/ and one stage-B log
          line, refuses an existing tag, --out and a plain --gt; a deposit time after a stage-B build is refused; --amend is refused once
          the stage-B log exists.
  M2      an H8 table on a subset of the fold units is not valid; the exact set is.
  Q1      c1_qcnet_summary_v01 and c1_predarm_v05 --q1-only (synthetic keys with tokens): a valid table; refused: no summary, not_predicted
          > 0, --runs with --q1-only, QCNet without --q1-only; Q1 present, failing or missing leaves C1_verdict, gate_H1, family_S and H9
          byte-identical (m5).
  M1RULE  m1: a planted E2 cell that the joint E2 + HL family does not flag but the E2-only family does: v04's rule holds, v05's does not.
  SCENE   m3: check_scene_json passes the bound map and refuses a swapped log or a missing unit.
  ENVTPP  m4: wrapper versions equal to FROZEN_ENV_TPP pass; a different torch refuses; no block refuses.
  FRZ5    test_c1_v09's FRZ4 on c1_freeze_v05 and README v07 (its test replaced by freeze_probe_pass_v01; nuScenes folds, own log, empty
          data root): a first freeze writes the five blocks once each; a second is refused; --amend appends and logs, and only the new plan
          is accepted; a stage-B manifest, a failing bound test, an unbound stage-A builder and a re-randomised child are refused; a plan
          that already holds a FROZEN_ENV block is refused (Choice 41a).
With --rehearsal <dir>: a second freeze into the rehearsal's log is refused, and the rehearsal plan's five blocks appear exactly once.
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v10.py [<out.json>] [--rehearsal <dir>]
"""
import copy
import datetime
import gzip
import hashlib
import json
import os
import re
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
import c1_guard_v04 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v10")
README = os.path.join(C1, "README_C1_CODE_v07.md")
R17C = os.path.join(W, "70_TESTS", "c1_v01", "r17c_probes")
R17D = os.path.join(W, "70_TESTS", "c1_v01", "r17d_probes")
PY = sys.executable
CANON = G.CANONICAL["C1"]
REAL_PROTOCOL_FILES = [CANON, G.DEPOSIT_RECORD, G.STAGE_B_LOG, G.RUN_LOG]
TESTED = ["c1_guard_v04.py", "c1_freeze_v05.py", "c1_analyse_v07.py", "c1_predarm_v05.py", "c1_fit_v05.py", "c1_run_v05.py", "c1_mstage_v05.py",
          "c1_h8_v05.py", "c1_e0_v04.py", "c1_quarantine_v01.py", "c1_qcnet_summary_v01.py", "tests/test_c1_v10.py", "../av2/av2_cache_stageB_v05.py",
          "../k8/k8_items_v07.py", "../tpp/tpp_keys_v03.py", "../tpp/tpp_run_v03.py", "../av2/av2_cache_stageA_v02.py"]
SKIP = {"test_c1_v01": ["GEN"], "test_c1_v02": ["GEN2", "FRZ"], "test_c1_v03": ["GEN3"], "test_c1_v06": ["FRZ3"], "test_c1_v08": ["LEGACY"],
        "test_c1_v09": ["FRZ4"]}  # v09 FRZ4 freezes README v06, whose entry points are no longer the latest (c1_freeze_v04 rightly refuses): FRZ5
LOG_DEPENDENT = {"test_c1_v06": ["LOG", "STAGEB"], "test_c1_v09": ["G3"]}
STATE = {}


def freeze_skip():
    """Choice 42c: skip the real-log-absent assertions only when the freeze runs us and passes the real log's hash."""
    return os.path.exists(CANON) and os.environ.get("C1_FREEZE_LOG_SHA256") == G.sha(CANON)


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except (AssertionError, SystemExit) as e:
        return str(e) or "refused"
    return None


def sub(cmd, cwd=C1, env=None):
    r = subprocess.run([PY, "-B"] + cmd, capture_output=True, text=True, cwd=cwd, env=env)
    return r.returncode, (r.stdout + r.stderr)


def wj(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(o, open(p, "w"), indent=1)
    return p


def utcs(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------------------------------------------------------------------ LEGACY
RUNNER = r"""
import importlib.util, json, os, re, sys, traceback
C1, TP, mod, outdir, skip = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], set(sys.argv[5].split(",")) - {""}
sys.path.insert(0, C1); sys.path.insert(0, os.path.join(C1, "tests")); sys.path.insert(0, TP)
path = os.path.join(C1, "tests", mod + ".py")
spec = importlib.util.spec_from_file_location("__mp_main__", path)
T = importlib.util.module_from_spec(spec)
sys.modules["__mp_main__"] = T
spec.loader.exec_module(T)
T.OUT = outdir
os.makedirs(outdir, exist_ok=True)
src = open(path, encoding="utf-8").read()
body = src[src.index("    for name, fn in ((" + chr(34)):]  # the main loop (test_c1_v08 also holds the runner text "for name, fn in (")
body = body[:body.index("):") + 1]
names = re.findall(r'\("([A-Za-z0-9_]+)", (?:lambda: )?(t_[a-z0-9_]+)(\(heavy\))?\)', body)
res, ok = {}, bool(names)
for name, fn, heavy in names:
    if name in skip:
        res[name] = "skipped (by rule)"
        continue
    try:
        f = getattr(T, fn)
        f(True) if heavy else f()
        res[name] = "pass"
    except Exception:
        ok = False
        res[name] = "FAIL: " + traceback.format_exc()[-1500:]
json.dump(res, open(os.path.join(outdir, "legacy_result.json"), "w"), indent=1)
print("LEGACY_ONE", "PASS" if ok else "FAIL")
"""


def t_legacy():
    out = {}
    for i in range(1, 10):
        mod = "test_c1_v%02d" % i
        skip = list(SKIP.get(mod, [])) + (LOG_DEPENDENT.get(mod, []) if freeze_skip() else [])
        od = os.path.join(OUT, "legacy_" + mod)
        r = subprocess.run([PY, "-B", "-c", RUNNER, C1, os.path.join(W, "50_CODE", "tpp", "tests"), mod, od, ",".join(skip)],
                           capture_output=True, text=True, cwd=C1)
        rp = os.path.join(od, "legacy_result.json")
        res = json.load(open(rp)) if os.path.exists(rp) else {"error": r.stderr[-1500:]}
        assert r.returncode == 0 and "LEGACY_ONE PASS" in r.stdout, (mod, res, r.stderr[-800:])
        out[mod] = res
    return out


# ------------------------------------------------------------------------------------------------------------------------------ G4
def t_g4():
    d = os.path.join(OUT, "g4")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    side = "a" * 64
    planned = datetime.datetime(2026, 11, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    good_t = utcs(planned + datetime.timedelta(hours=2))

    def rec(name, lines):
        p = os.path.join(d, name)
        open(p, "w").write("\n".join(lines) + "\n")
        return p
    ok = rec("ok.txt", ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: " + good_t])
    G.check_deposit(side, "nuscenes", ok, planned)
    ok2 = rec("ok_doi.txt", ["frozen_plan_sha256: " + side, "registration: 10.17605/OSF.IO/ABCDE", "registered_utc: " + good_t])
    G.check_deposit(side, "nuscenes", ok2, planned)
    out = {"valid_url": "pass", "valid_doi": "pass"}
    cases = {"PB4_registration_TODO": ["frozen_plan_sha256: " + side, "registration: TODO", "registered_utc: " + good_t],
             "PB4_time_not_yet": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: not yet"],
             "PB4_time_2099": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: 2099-01-01T00:00:00Z"],
             "PB4_duplicated_key": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registration: https://osf.io/zzzzz/",
                                    "registered_utc: " + good_t],
             "before_plan_line": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: 2026-10-01T00:00:00Z"],
             "wrong_plan": ["frozen_plan_sha256: " + "b" * 64, "registration: https://osf.io/abcde/", "registered_utc: " + good_t],
             "not_iso": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: 2026-11-01 14:00"]}
    for name, lines in cases.items():
        m = raises(G.check_deposit, side, "nuscenes", rec(name + ".txt", lines), planned)
        assert m and "OSF_DEPOSIT_GUIDE_v02.md" in m, (name, m)
        out[name] = "refused"
    sbl = os.path.join(d, "STAGE_B_LOG.txt")
    open(sbl, "w").write(json.dumps({"utc": utcs(planned + datetime.timedelta(hours=1))}) + "\n")
    m = raises(G.check_deposit, side, "nuscenes", ok, planned, sbl)
    assert m and "stage-B build" in m, m
    out["after_a_stage_B_build"] = "refused"
    m = raises(G.check_deposit, side, "av2", ok, planned)
    assert m and "override is refused" in m
    assert not os.path.exists(G.DEPOSIT_RECORD) or freeze_skip()
    m = raises(G.check_deposit, side, "av2", None, planned)
    assert (m and "OSF_DEPOSIT_GUIDE_v02.md" in m) or os.path.exists(G.DEPOSIT_RECORD)
    out["av2_override_and_missing"] = "refused"
    assert G.DEPOSIT_EXEMPT == ("entry:c1_e0", "entry:c1_folds", "entry:c1_freeze")
    return out


# ------------------------------------------------------------------------------------------------------------------------------ TREE
def readme_rows():
    return re.findall(r"^([0-9a-f]{64})  (50_CODE/\S+)  (\S+)$", open(README, encoding="utf-8").read(), re.M)


def build_tree(T):
    shutil.rmtree(T, ignore_errors=True)
    for h, p, r in readme_rows():
        dst = os.path.join(T, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(W, p), dst)
        assert G.sha(dst) == h, p
    shutil.copy2(README, os.path.join(T, "50_CODE", "c1_av2", "README_C1_CODE_v07.md"))
    for rel_ in ("60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_t1_v01.json", "60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_t3_v01.json",
                 "60_RESULTS/x2/x2_oc_q4_v02.json"):
        os.makedirs(os.path.dirname(os.path.join(T, rel_)), exist_ok=True)
        shutil.copy2(os.path.join(W, rel_), os.path.join(T, rel_))
    os.makedirs(os.path.join(T, "40_PROTOCOL"), exist_ok=True)
    fx = os.path.join(T, "30_DATA", "fx_av2relab")
    shutil.copytree(os.path.join(R17D, "fx_av2relab"), fx)
    gt = os.path.join(fx, "gt.json")
    man = json.load(open(os.path.join(fx, "stageA", "MANIFEST.json")))
    man["inputs"].update({"workers": [os.path.join(fx, "worker0")], "horizon": os.path.join(fx, "horizon.jsonl.gz"), "gt": gt})
    assert man["inputs"]["gt_sha256"] == G.sha(gt)
    wj(os.path.join(fx, "stageA", "MANIFEST.json"), man)
    zero = {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": gt, "gt_sha256": G.sha(gt)}, "note": "zero-scene stage-A cache (test v10)"}
    wj(os.path.join(T, "30_DATA", "fx_stageA_zero", "MANIFEST.json"), zero)
    p2 = os.path.join(T, "70_TESTS", "fx_p2")  # outside 30_DATA: R17c p2 holds a stage-B manifest, which the freeze refuses under 30_DATA
    shutil.copytree(os.path.join(R17C, "p2"), p2, ignore=shutil.ignore_patterns("*.json.tmp"))
    return {"fx": fx, "gt": gt, "zero": os.path.join(T, "30_DATA", "fx_stageA_zero"), "p2": p2}


def tree_readme(T, probe_rel):
    rows = readme_rows()
    lines = ["%s  %s  %s" % (h, p, ("test_module" if r == "test" else r)) for h, p, r in rows if p != probe_rel]
    lines.append("%s  %s  test" % (G.sha(os.path.join(T, probe_rel)), probe_rel))
    sup = re.findall(r"^superseded  (50_CODE/\S+)$", open(README, encoding="utf-8").read(), re.M)
    lines += ["superseded  %s" % s for s in sup if os.path.exists(os.path.join(T, s))]
    p = os.path.join(T, "50_CODE", "c1_av2", "README_tree_probe.md")
    open(p, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return p


def tree_freeze(T, F, plan_name, extra=()):
    plan = os.path.join(T, "70_TESTS", plan_name)
    if not os.path.exists(plan):
        os.makedirs(os.path.dirname(plan), exist_ok=True)
        open(plan, "w").write("# tree probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n" % plan_name)
    fx = F["fx"]
    cmd = [os.path.join(T, "50_CODE", "c1_av2", "c1_freeze_v05.py"), "--plan", plan, "--readme", F["readme"], "--results-dir",
           os.path.join(T, "70_TESTS", "results_" + plan_name), "--folds", os.path.join(fx, "folds_av2.json"), "--split", F["split"],
           "--transfer-fits", os.path.join(T, "60_RESULTS", "c1_transfer_fits_v01", "c1_transfer_fits_t1_v01.json"),
           os.path.join(T, "60_RESULTS", "c1_transfer_fits_v01", "c1_transfer_fits_t3_v01.json"),
           "--stageA-manifests", os.path.join(fx, "stageA", "MANIFEST.json"), os.path.join(F["zero"], "MANIFEST.json"), "--config", F["config"],
           "--data", "scene_json=" + os.path.join(fx, "meta", "scene.json"), "e0_plan=" + os.path.join(fx, "e0_plan.json"),
           "--test-out-dir", os.path.join(T, "70_TESTS", "freeze_tests_" + plan_name),
           "--tpp-python", os.path.join(W, "50_CODE", "env", "tpp38", "Scripts", "python.exe")] + list(extra)  # the copy tree has no environments
    return plan, sub(cmd, cwd=os.path.join(T, "50_CODE", "c1_av2"))


def t_tree():
    T = os.path.join(OUT, "tree")
    F = build_tree(T)
    TC = os.path.join(T, "50_CODE", "c1_av2")
    out = {}
    probe = "50_CODE/c1_av2/tests/freeze_probe_envcheck_v01.py"
    F["readme"] = tree_readme(T, probe)
    F["split"] = wj(os.path.join(T, "30_DATA", "fx_split.json"), {"rule": "tree probe split"})
    F["config"] = wj(os.path.join(T, "30_DATA", "fx_config.json"), {"note": "tree probe config"})
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md")
    assert rc != 0 and "quarantine it first" in o, o[-800:]
    out["freeze_before_quarantine"] = "refused (B2)"
    q = [os.path.join(TC, "c1_quarantine_v01.py"), "--stageA-manifests", os.path.join(F["fx"], "stageA", "MANIFEST.json"), os.path.join(F["zero"], "MANIFEST.json")]
    rc, o = sub(q + ["--dry-run"], cwd=TC)
    assert rc == 0 and os.path.exists(F["gt"]) and not os.path.exists(os.path.join(T, "30_DATA", "av2_gt_quarantine_v01")), o[-600:]
    gt_bytes = open(F["gt"], "rb").read()
    rc, o = sub(q, cwd=TC)
    member = os.path.join(T, "30_DATA", "av2_gt_quarantine_v01", "gt.json.gz")
    assert rc == 0 and not os.path.exists(F["gt"]) and gzip.open(member).read() == gt_bytes, o[-600:]
    rc, o = sub(q, cwd=TC)
    assert rc == 0 and "already quarantined" in o, o[-600:]
    tam = os.path.join(T, "30_DATA", "fx_tamper")
    os.makedirs(tam, exist_ok=True)
    open(os.path.join(tam, "gt_t.json"), "w").write("{}")
    wj(os.path.join(tam, "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": os.path.join(tam, "gt_t.json"), "gt_sha256": "0" * 64}})
    rc, o = sub([os.path.join(TC, "c1_quarantine_v01.py"), "--stageA-manifests", os.path.join(tam, "MANIFEST.json")], cwd=TC)
    assert rc != 0 and "differs from the hash" in o and os.path.exists(os.path.join(tam, "gt_t.json")), o[-600:]
    pod = os.path.join(T, "30_DATA", "fx_pod")
    os.makedirs(pod, exist_ok=True)
    open(os.path.join(pod, "gt_pod.json"), "w").write('{"pod": 1}')
    wj(os.path.join(pod, "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {},
                                            "inputs": {"gt": "/workspace/W/30_DATA/fx_pod/gt_pod.json", "gt_sha256": G.sha(os.path.join(pod, "gt_pod.json"))}})
    rc, o = sub([os.path.join(TC, "c1_quarantine_v01.py"), "--stageA-manifests", os.path.join(pod, "MANIFEST.json")], cwd=TC)
    assert rc == 0 and not os.path.exists(os.path.join(pod, "gt_pod.json")) and         gzip.open(os.path.join(T, "30_DATA", "av2_gt_quarantine_v01", "gt_pod.json.gz")).read() == b'{"pod": 1}', o[-600:]
    out["quarantine"] = "dry run changes nothing; gz verified, plain removed; idempotent; tampered plain refused; a pod path found under 30_DATA"
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md")
    assert rc == 0 and "C1 FREEZE V05 DONE" in o, o[-1500:]
    txt = open(plan1, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    assert "C1_FREEZE_LOG_SHA256=absent" in txt
    out["freeze_after_quarantine"] = "done; five blocks once each; tests run with C1_FREEZE_LOG_SHA256=absent"
    fx, p2 = F["fx"], F["p2"]
    meta, hz, w0, e0 = os.path.join(fx, "meta"), os.path.join(fx, "horizon.jsonl.gz"), os.path.join(fx, "worker0"), os.path.join(fx, "e0_plan.json")
    folds = os.path.join(fx, "folds_av2.json")
    P = ["--plan", plan1]
    pb1 = {"h8_v05": [os.path.join(TC, "c1_h8_v05.py"), "--workers", w0, "--gt", member, "--meta", meta, "--horizon", hz, "--e0-plan", e0,
                      "--folds", folds, "--out", os.path.join(T, "70_TESTS", "h8_pb1.json")] + P,
           "mstage_v05": [os.path.join(TC, "c1_mstage_v05.py"), "--tracker", "T1", "--experiment", "x", "--av2-workers", w0, "--av2-gt", member,
                          "--av2-meta", meta, "--av2-horizon", hz, "--train-workers", os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker1"),
                          "--train-gt", os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json"), "--train-meta", os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval"),
                          "--train-horizon", os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"), "--folds", folds,
                          "--out", os.path.join(T, "70_TESTS", "ms_pb1.json")] + P,
           "predarm_v05": [os.path.join(TC, "c1_predarm_v05.py"), "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", os.path.join(p2, "folds.json"),
                           "--tracker-index", "0", "--out", os.path.join(T, "70_TESTS", "pa_pb1.json")] + P}
    for name, cmd in pb1.items():
        rc, o = sub(cmd, cwd=TC)
        assert rc != 0 and ("no deposit record" in o or "fold" in o.lower() and "refused" in o), (name, o[-700:])
        out["PB1_" + name] = "refused" + (" (no deposit record)" if "no deposit record" in o else " (" + o.strip().splitlines()[-1][:80] + ")")
    probe_e0 = ("import sys; sys.path.insert(0, %r)\nimport c1_guard_v04 as G\n"
                "s, f, rt = G.guard('av2', %r, 'entry:c1_e0', %r)\nprint('E0_GUARD', rt['deposit_record_sha256'])" % (TC, plan1, os.path.join(TC, "c1_e0_v04.py")))
    rc, o = sub(["-c", probe_e0], cwd=TC)
    assert rc == 0 and "E0_GUARD exempt (entry:c1_e0)" in o, o[-600:]
    out["entry:c1_e0"] = "exempt from the deposit"
    rc, o = sub([os.path.join(T, "50_CODE", "x1", "x2_full_v02.py"), "--prereg", os.path.join(R17D, "p2b", "SELF_MADE_PREREG.md"), "--skip-bind",
                 "--expected-tokens", "2008", "--workers", w0, "--gt", F["gt"], "--meta", meta, "--oc", os.path.join(T, "60_RESULTS", "x2", "x2_oc_q4_v02.json"),
                 "--horizon", hz, "--out", os.path.join(T, "70_TESTS", "x2_p2b.json")], cwd=os.path.join(T, "50_CODE", "x1"))
    assert rc != 0 and not os.path.exists(os.path.join(T, "70_TESTS", "x2_p2b.json")) and ("No such file" in o or "gt.json" in o), o[-600:]
    out["P2b_x2_full_after_quarantine"] = "cannot run: the plain ground truth is gone (%s)" % o.strip().splitlines()[-1][:80]
    plan2, (rc, o) = tree_freeze(T, F, "PLAN_2.md", ["--amend", "tree probe amendment"])
    assert rc == 0 and "C1 FREEZE V05 DONE" in o, o[-1500:]
    log = os.path.join(T, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt")
    t2 = open(plan2, encoding="utf-8").read()
    assert "C1_FREEZE_LOG_SHA256=" in t2 and "C1_FREEZE_LOG_SHA256=absent" not in t2, "the amendment's tests were not run with the log hash"
    rc, o = sub([os.path.join(T, probe), os.path.join(T, "70_TESTS", "probe_direct.json")], cwd=TC)
    assert "FAIL" in o, o[-300:]
    assert os.path.exists(os.path.join(T, "40_PROTOCOL", "C1_DEVIATION_LOG_v01.md"))
    out["M1_amend"] = "passes its own suite through C1_FREEZE_LOG_SHA256; the same suite run directly fails; logged in C1_DEVIATION_LOG_v01.md"
    lines = [l for l in open(log).read().splitlines() if l.strip()]
    t_line = datetime.datetime.strptime(re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC", lines[-1]).group(1), "%Y-%m-%d %H:%M:%S")
    time.sleep(1.5)
    reg = utcs(datetime.datetime.now(datetime.timezone.utc))
    side2 = G.sha(plan2)
    dep = os.path.join(T, "40_PROTOCOL", "C1_PLAN_DEPOSIT_RECORD_v01.txt")
    open(dep, "w").write("frozen_plan_sha256: %s\nregistration: https://osf.io/abcde/\nregistered_utc: %s\n" % (side2, reg))
    plan3, (rc, o) = tree_freeze(T, F, "PLAN_3.md", ["--amend", "after the deposit"])
    assert rc != 0 and "has been deposited" in o, o[-600:]
    out["amend_after_deposit"] = "refused"
    h8o = os.path.join(T, "70_TESTS", "h8_post.json")
    h8 = [os.path.join(TC, "c1_h8_v05.py"), "--workers", w0, "--gt", member, "--meta", meta, "--horizon", hz, "--e0-plan", e0, "--folds", folds,
          "--out", h8o, "--plan", plan2]
    rc, o = sub(h8, cwd=TC)
    assert rc == 0 and "C1 H8 V05 DONE" in o, o[-1500:]
    t8 = json.load(open(h8o))
    assert t8["provenance"]["deposit_record_sha256"] == G.sha(dep) and t8["provenance"]["scene_json_check"]["units_checked"] == 50
    rl = os.path.join(T, "40_PROTOCOL", "C1_RUN_LOG.txt")
    assert len(open(rl).read().splitlines()) == 1
    rc, o = sub(h8, cwd=TC)
    assert rc != 0 and "never overwritten" in o, o[-500:]
    out["h8_after_deposit"] = "runs from the quarantine; scene.json checked (50 units); one run-log line; same output refused"
    sb = os.path.join(T, "50_CODE", "av2", "av2_cache_stageB_v05.py")
    base = [sb, "--stage-a", F["zero"], "--frozen-plan", plan2]
    rc, o = sub(base + ["--gt", member, "--tag", "t1"], cwd=os.path.join(T, "50_CODE", "av2"))
    assert rc == 0 and os.path.exists(os.path.join(T, "30_DATA", "av2_cache_stageB_t1", "MANIFEST.json")), o[-1200:]
    sbl = os.path.join(T, "40_PROTOCOL", "C1_STAGE_B_LOG.txt")
    assert len(open(sbl).read().splitlines()) == 1
    mb = json.load(open(os.path.join(T, "30_DATA", "av2_cache_stageB_t1", "MANIFEST.json")))
    assert mb["stage_b"]["deposit_record_sha256"] == G.sha(dep)
    for name, extra, msg in (("same_tag", ["--gt", member, "--tag", "t1"], "never overwritten"),
                             ("out_on_av2", ["--gt", member, "--tag", "t2", "--out", os.path.join(T, "30_DATA", "elsewhere")], "--tag only"),
                             ("plain_gt", ["--gt", os.path.join(T, "30_DATA", "fx_tamper", "gt_t.json"), "--tag", "t3"], "only from the quarantine")):
        rc, o = sub(base + extra, cwd=os.path.join(T, "50_CODE", "av2"))
        assert rc != 0 and msg in o, (name, o[-600:])
        out["stageB_" + name] = "refused"
    late = utcs(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=1))
    time.sleep(2.5)
    open(dep, "w").write("frozen_plan_sha256: %s\nregistration: https://osf.io/abcde/\nregistered_utc: %s\n" % (side2, late))
    rc, o = sub(h8[:-4] + ["--out", os.path.join(T, "70_TESTS", "h8_late.json"), "--plan", plan2], cwd=TC)
    assert rc != 0 and "stage-B build" in o, o[-600:]
    out["deposit_after_stageB_build"] = "refused"
    os.remove(dep)
    plan4, (rc, o) = tree_freeze(T, F, "PLAN_4.md", ["--amend", "after stage B"])
    assert rc != 0 and "a stage B has been built" in o, o[-600:]
    out["amend_after_stageB"] = "refused"
    out["stageB_v05"] = "writes only 30_DATA/av2_cache_stageB_<tag>/; one stage-B log line; deposit recorded"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ FRZ5
def t_frz5():
    d = os.path.join(OUT, "frz5")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    probe, fail = "50_CODE/c1_av2/tests/freeze_probe_pass_v01.py", "50_CODE/c1_av2/tests/freeze_probe_fail_v01.py"

    def readme_with(test_rel, name):
        rows = readme_rows()
        lines = ["%s  %s  %s" % (h, p, ("test_module" if r == "test" else r)) for h, p, r in rows if p != test_rel]
        lines.append("%s  %s  test" % (G.sha(os.path.join(W, test_rel)), test_rel))
        lines += ["superseded  %s" % x for x in re.findall(r"^superseded  (50_CODE/\S+)$", open(README, encoding="utf-8").read(), re.M)]
        q = os.path.join(d, name)
        open(q, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
        return q
    rp, rf = readme_with(probe, "README_probe.md"), readme_with(fail, "README_fail.md")
    units = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")))["scenes"])
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s %s" % (u, "held_out_train" if i < 60 else "val") for i, u in enumerate(units)) + "\n")
    fo, v150, t225 = (os.path.join(d, x) for x in ("folds.json", "folds_val150.json", "folds_train225.json"))
    for cmd in (["--logs", lp, "--out", fo, "--dataset", "nuscenes"], ["--restrict-from", fo, "--source", "val", "--out", v150],
                ["--restrict-from", fo, "--source", "held_out_train", "--out", t225]):
        rc, o = sub(["c1_folds_v03.py"] + cmd)
        assert rc == 0, o[-600:]
    split, cfg = wj(os.path.join(d, "split.json"), {"rule": "probe split"}), wj(os.path.join(d, "config.json"), {"note": "probe config"})
    root = os.path.join(d, "emptyroot")
    os.makedirs(root)
    TF = os.path.join(W, "60_RESULTS", "c1_transfer_fits_v01")
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % p, "MANIFEST.json") for p in ("train", "val")]

    def args(plan, readme, log, extra=(), folds150=v150, droot=root):
        return (["c1_freeze_v05.py", "--plan", plan, "--readme", readme, "--results-dir", os.path.join(d, "results"), "--folds", fo, "--split", split,
                 "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"), os.path.join(TF, "c1_transfer_fits_t3_v01.json"),
                 "--stageA-manifests"] + man + ["--config", cfg, "--folds-val150", folds150, "--folds-train225", t225, "--hash-log", log,
                                               "--data-root", droot, "--test-out-dir", os.path.join(d, "tests_out")] + list(extra))
    tmpl = "# probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n"

    def plan(k, body=None):
        q = os.path.join(d, "PLAN_%s.md" % k)
        open(q, "w").write(body or tmpl % k)
        return q
    out, log = {}, os.path.join(d, "LOG.txt")
    p1 = plan(1)
    rc, o = sub(args(p1, rp, log))
    assert rc == 0 and "C1 FREEZE V05 DONE" in o, o[-1500:]
    txt = open(p1, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    assert "ALL_PASS" in txt and "folds_val150" in txt
    side1, _ = G.frozen_plan(p1, "nuscenes", log)
    out["first_freeze"] = "done (%s); five blocks once each" % side1[:12]
    p2 = plan(2)
    rc, o = sub(args(p2, rp, log))
    assert rc != 0 and "one freeze only" in o, o[-800:]
    out["second_freeze"] = "refused"
    rc, o = sub(args(p2, rp, log, ["--amend", "probe amendment"]))
    assert rc == 0 and "C1 FREEZE V05 DONE" in o, o[-1500:]
    assert os.path.exists(os.path.join(d, "C1_DEVIATION_LOG_REHEARSAL.md"))
    assert raises(G.frozen_plan, p1, "nuscenes", log) and G.frozen_plan(p2, "nuscenes", log)
    out["amend"] = "appended, logged; only the new plan accepted"
    os.makedirs(os.path.join(d, "root_b", "cacheX"))
    wj(os.path.join(d, "root_b", "cacheX", "MANIFEST.json"), {"stage": "B", "dataset": "nuscenes", "scenes": {}})
    p3 = plan(3)
    rc, o = sub(args(p3, rp, os.path.join(d, "LOG3.txt"), droot=os.path.join(d, "root_b")))
    assert rc != 0 and "stage-B manifest exists" in o, o[-800:]
    out["stage_B_manifest_present"] = "refused"
    rc, o = sub(args(p3, rf, os.path.join(d, "LOG4.txt")))
    assert rc != 0 and "did not print ALL_PASS" in o, o[-800:]
    out["failing_test"] = "refused"
    ma = wj(os.path.join(d, "stageA_bad", "MANIFEST.json"), {"stage": "A", "dataset": "nuscenes", "scenes": {"scene-0001": {}}, "inputs": {"builder_sha256": "0" * 64}})
    a5 = args(p3, rp, os.path.join(d, "LOG5.txt"))
    a5.insert(a5.index("--stageA-manifests") + 1, ma)
    rc, o = sub(a5)
    assert rc != 0 and "not a bound builder" in o, o[-800:]
    out["unbound_builder"] = "refused"
    bad = json.load(open(v150))
    k = sorted(bad["fold_of_log"])[0]
    bad["fold_of_log"][k] = (bad["fold_of_log"][k] + 1) % 5
    rc, o = sub(args(p3, rp, os.path.join(d, "LOG6.txt"), folds150=wj(os.path.join(d, "folds_val150_rerandomised.json"), bad)))
    assert rc != 0 and "not a restriction" in o, o[-800:]
    out["rerandomised_child"] = "refused"
    p7 = plan(7, tmpl % 7 + "\nFROZEN_ENV_BEGIN\npython  x\nFROZEN_ENV_END\n")
    rc, o = sub(args(p7, rp, os.path.join(d, "LOG7.txt")))
    assert rc != 0 and "Choice 41a" in o, o[-800:]
    out["drafted_env_block"] = "refused (Choice 41a)"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ M2
def mock_plan(d, name, paths, roles=()):
    os.makedirs(d, exist_ok=True)
    plan = os.path.join(d, name)
    v = G.versions()
    body = "# mock plan\n\nFROZEN_HASHES_BEGIN\n%s\nFROZEN_HASHES_END\nFROZEN_ROLES_BEGIN\n%s\nFROZEN_ROLES_END\nFROZEN_ENV_BEGIN\n%s\nFROZEN_ENV_END\n" % (
        "\n".join("%s  %s" % (G.sha(os.path.join(W, p)), p) for p in paths), "\n".join("%s  %s" % (r, p) for r, p in roles),
        "\n".join("%s  %s" % (k, v[k]) for k in ("python", "numpy", "scipy")))
    open(plan, "w", encoding="utf-8", newline="\n").write(body)
    open(plan[:-3] + ".sha256", "w").write(G.sha(plan) + "  %s\n" % name)
    log = os.path.join(d, "LOG.txt")
    open(log, "w").write("%s  %s  frozen 2026-11-01 12:00:00 UTC by test\n" % (G.sha(plan), name))
    return plan, log


def t_m2():
    import c1_analyse_v07 as A7
    d = os.path.join(OUT, "m2")
    shutil.rmtree(d, ignore_errors=True)
    me, g4 = "50_CODE/c1_av2/c1_h8_v05.py", "50_CODE/c1_av2/c1_guard_v04.py"
    plan, log = mock_plan(d, "PM.md", [me, g4], roles=[("entry:c1_h8", me), ("module", g4)])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    units = ["scene-%04d" % i for i in range(1, 11)]

    def table(us):
        return {"provenance": {"plan_sha256": side, "folds_sha256": "f" * 64, "entry_point": {me: fr[me]}, "code_sha256": {me: fr[me], g4: fr[g4]},
                               "inputs_sha256": {"x": "0" * 64}, "inputs_checked": True, "units": G.units_record(us), "dataset": "nuscenes",
                               "hash_log_sha256": fr.log_sha256, "deposit_record_sha256": "exempt (nuscenes)"}}
    full, part = wj(os.path.join(d, "h8_full.json"), table(units)), wj(os.path.join(d, "h8_sub.json"), table(units[:6]))
    r = A7.load_table("h8", "entry:c1_h8", {"h8": full}, "c1", side, fr, "f" * 64, A7.TRACKERS, units, "nuscenes", "exempt (nuscenes)")
    assert r["ok"], r
    r2 = A7.load_table("h8", "entry:c1_h8", {"h8": part}, "c1", side, fr, "f" * 64, A7.TRACKERS, units, "nuscenes", "exempt (nuscenes)")
    assert not r2["ok"] and "units differ" in r2["why"], r2
    r3 = A7.load_table("h8", "entry:c1_h8", {"h8": full}, "c1", side, fr, "f" * 64, A7.TRACKERS, units, "nuscenes", "b" * 64)
    assert not r3["ok"] and "deposit" in r3["why"], r3
    return {"exact_units": "valid", "subset": "not valid (R17d M2)", "other_deposit": "not valid (Choice 42a)"}


# ------------------------------------------------------------------------------------------------------------------------------ Q1
def planted(h1=True):
    import c1_analyse_v07 as A7
    fb = {"met": h1, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False, "pops": {}} for a in A7.A6.REQUIRED_ARMS}
    return {"within_lt3d": {t: {"form_b": fb, "status": st, "form_c": None, "form_a": {}} for t in A7.TRACKERS}}


def t_q1():
    import c1_analyse_v07 as A7
    import c1_folds_v01 as F
    import test_tpp_analyse_v01 as TT
    d = os.path.join(OUT, "q1")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    kp, runs, _ = TT.make_synthetic(d, seed=5, n_scenes=150)
    kz = dict(np.load(kp, allow_pickle=False))
    n = len(kz["rec_k"])
    kz.update({"rec_sample_token": np.array(["tok%06d" % i for i in range(n)]), "rec_instance_token": np.array(["inst%06d" % i for i in range(n)]),
               "rec_hist_stratum_gt": kz["rec_hist_stratum_trk"].copy()})
    k2 = os.path.join(d, "keys_tok.npz")
    np.savez(k2, **kz)
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s syn" % x for x in kz["scene_names"]))
    F.main(["--logs", lp, "--out", os.path.join(d, "folds.json"), "--seed", "20261112"])
    rz = np.load(runs["trk"], allow_pickle=False)
    c3 = rz["v2_cov"]
    cov22 = np.stack([np.stack([c3[:, 0], c3[:, 1]], -1), np.stack([c3[:, 1], c3[:, 2]], -1)], 1)
    perm = np.random.default_rng(3).permutation(n)
    full = os.path.join(d, "qcnet_full.npz")
    mu = np.where(np.isfinite(rz["v2_mu"]), rz["v2_mu"], 0.0)
    np.savez(full, sample_token=kz["rec_sample_token"][perm], instance_token=kz["rec_instance_token"][perm], v2_mu=mu[perm], v2_cov=cov22[perm],
             finite=np.ones(n, bool), pd_v2=np.ones(n, bool))
    part = os.path.join(d, "qcnet_part.npz")
    np.savez(part, sample_token=kz["rec_sample_token"][perm][:-5], instance_token=kz["rec_instance_token"][perm][:-5], v2_mu=mu[perm][:-5],
             v2_cov=cov22[perm][:-5], finite=np.ones(n - 5, bool), pd_v2=np.ones(n - 5, bool))
    out = {}
    summ = {}
    for name, q in (("full", full), ("part", part)):
        s = os.path.join(d, "summary_%s.json" % name)
        rc, o = sub(["c1_qcnet_summary_v01.py", "--keys", k2, "--qcnet", q, "--source", "deployed", "--checkpoint-commit", "fixture", "--recentring",
                     "fixture", "--history-source", "fixture", "--out", s, "--synthetic"])
        assert rc == 0, o[-600:]
        summ[name] = s
    assert json.load(open(summ["part"]))["not_predicted"] == 5 and json.load(open(summ["full"]))["not_predicted"] == 0
    base = ["c1_predarm_v05.py", "--keys", k2, "--folds", os.path.join(d, "folds.json"), "--tracker-index", "0", "--synthetic"]
    rc, o = sub(base + ["--q1-only", "--qcnet-deployed", full, "--qcnet-deployed-summary", summ["full"], "--out", os.path.join(d, "q1.json")])
    assert rc == 0, o[-1200:]
    q1 = json.load(open(os.path.join(d, "q1.json")))
    assert q1["q1_only"] and "H9" not in q1 and "Q1_deployed" in q1["arms"]
    out["valid_q1_table"] = "written (no H9 key)"
    for name, extra, msg in (("no_summary", ["--q1-only", "--qcnet-deployed", full], "needs its run summary"),
                             ("not_predicted", ["--q1-only", "--qcnet-deployed", part, "--qcnet-deployed-summary", summ["part"]], "unpredicted"),
                             ("runs_with_q1", ["--q1-only", "--qcnet-deployed", full, "--qcnet-deployed-summary", summ["full"], "--runs", "trk=" + runs["trk"]], "no --runs"),
                             ("qcnet_without_q1", ["--qcnet-deployed", full, "--qcnet-deployed-summary", summ["full"], "--runs", "trk=" + runs["trk"]], "separate tables")):
        rc, o = sub(base + extra + ["--out", os.path.join(d, "q1_%s.json" % name)])
        assert rc != 0 and msg in o, (name, o[-600:])
        out["refused_" + name] = "refused"
    h9 = {t: {"H9": True, "H9_noHL": True, "arms": {"TPP": {}}, "population": "PD", "H9_seed": {"20261102": True, "20261104": True, "20261105": True}}
          for t in A7.TRACKERS}
    aux0 = {"tables": {"h9": {"ok": True, "data": h9, "checks": {}}}}
    keys = ("C1_verdict", "gate_H1", "family_S")
    outs = {}
    for name, q1tab in (("present", {"ok": True, "data": {"t1": q1}, "checks": {}}), ("failing", {"ok": False, "why": "planted failure"}),
                        ("broken", {"ok": True, "data": {"t1": {"arms": None}}, "checks": {}}), ("missing", None)):
        dd = A7.decide_all(copy.deepcopy(planted()), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0, q1=q1tab))
        outs[name] = (json.dumps({k: dd[k] for k in keys}, sort_keys=True, default=str), dd["claims_status"]["H9"], dd["hypotheses"]["H9"]["status"],
                      dd["claims_status"]["Q1"])
    base_ = outs["present"][:3]
    assert all(v[:3] == base_ for v in outs.values()), "Q1 changed C1_verdict, gate_H1, family_S or H9"
    assert outs["present"][3] == "descriptive" and outs["failing"][3] == outs["broken"][3] == outs["missing"][3] == "not tested"
    out["byte_identity"] = "C1_verdict, gate_H1, family_S and H9 identical with Q1 present, failing, broken or missing; Q1 alone changes"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ M1RULE
def t_m1rule():
    import c1_predarm_v04 as P4
    import c1_predarm_v05 as P5
    found = None
    for k, rate in enumerate(np.arange(0.060, 0.120, 0.002)):
        rng = np.random.default_rng(7)
        e2, hl, nu = 7, 3, 200
        N = np.full((nu, e2 + hl), 12.0)
        p = np.array([0.02] * e2)
        p[0] = rate
        X = np.zeros_like(N)
        X[:, :e2] = rng.binomial(12, p[None, :], size=(nu, e2))
        N[:, e2:] = N[:, :e2].sum(1, keepdims=True) / hl
        X[:, e2:] = np.stack([rng.binomial(N[:, e2 + j].astype(int), 0.02) for j in range(hl)], 1)
        cells = [("e2_%d" % j, []) for j in range(e2)] + [("hist=2", []), ("hist=3-4", []), ("hist>=5", [])]
        sc = np.array(["scene-%04d" % i for i in range(nu)])
        lg = np.arange(nu) % 40
        Wb = np.random.default_rng(8).multinomial(40, np.full(40, 1 / 40.0), size=2000).astype(float)[:, lg]
        r4 = P4.h9_rule_v04(N, X, cells, e2, sc, lg, Wb, [20261111, 0, 5])
        r5 = P5.h9_rule_v05(N, X, cells, e2, sc, lg, Wb, [20261111, 0, 5])
        if r4["H9"] and not r5["H9"] and "e2_0" in r5["flagged_E2_family"] + r5["family_flagged_E2"]:
            found = {"rate": round(float(rate), 3), "v04_joint_H9": r4["H9"], "v05_H9": r5["H9"], "v05_E2_only_flags": {"evaluable_family": r5["flagged_E2_family"], "power_qualified_family": r5["family_flagged_E2"]}}
            break
    assert found, "no planted rate separates the joint family from the E2-only family"
    return found


# ------------------------------------------------------------------------------------------------------------------------------ SCENE, ENVTPP
def t_scene():
    d = os.path.join(OUT, "scene")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(os.path.join(d, "meta"))
    sj = wj(os.path.join(d, "meta", "scene.json"), [{"name": "scene-0001", "log_token": "L1"}, {"name": "scene-0002", "log_token": "L2"}])
    ma = wj(os.path.join(d, "sa", "MANIFEST.json"), {"stage": "A", "scenes": {"scene-0001": {"log": "L1"}, "scene-0002": {"log": "L2"}}})
    plan, log = mock_plan(d, "PS.md", [G.rel(sj), G.rel(ma)], roles=[("data:scene_json", G.rel(sj)), ("stageA_manifest", G.rel(ma))])
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    assert G.check_scene_json(fr, os.path.join(d, "meta"), ["scene-0001", "scene-0002"])["units_checked"] == 2
    assert raises(G.check_scene_json, fr, os.path.join(d, "meta"), ["scene-0001", "scene-0003"])
    wj(sj, [{"name": "scene-0001", "log_token": "L2"}, {"name": "scene-0002", "log_token": "L1"}])
    assert raises(G.check_scene_json, fr, os.path.join(d, "meta"), ["scene-0001", "scene-0002"])
    return {"bound_map": "pass", "missing_unit": "refused", "swapped_or_changed_map": "refused"}


def t_envtpp():
    import c1_predarm_v05 as P5

    class Fr:
        env_tpp = {"python": "3.8.20", "numpy": "1.18.5", "torch": "1.4.0+cpu"}
    rec = {"versions": dict(Fr.env_tpp)}
    assert P5.env_check(Fr, rec, "tpp_run")
    assert raises(P5.env_check, Fr, {"versions": dict(Fr.env_tpp, torch="2.0")}, "tpp_run")
    assert P5.env_check(Fr, {"versions": dict(Fr.env_tpp, torch="2.0")}, "tpp_keys")

    class Fn:
        env_tpp = None
    assert raises(P5.env_check, Fn, rec, "tpp_run")
    return {"match": "pass", "torch_differs": "refused", "keys_ignore_torch": "pass", "no_block": "refused"}


# ------------------------------------------------------------------------------------------------------------------------------ rehearsal
def t_rehearsal():
    reh = STATE.get("rehearsal")
    if not reh:
        return {"skipped": "no --rehearsal"}
    plan = os.path.join(reh, "MOCK_C1_PLAN_v05.md")
    log = os.path.join(reh, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    txt = open(plan, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    steps = [json.loads(l) for l in open(os.path.join(reh, "steps.jsonl"))]
    fz = [s["key"] for s in steps if s["key"].startswith("c1_freeze_v05.py") and "MOCK_C1_PLAN_v05" in s["key"]][0].split(" ")
    p2 = os.path.join(OUT, "SECOND_PLAN.md")
    open(p2, "w").write("# second plan\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n")
    fz[fz.index("--plan") + 1] = p2
    fz[fz.index("--results-dir") + 1] = os.path.join(OUT, "results2")
    rc, o = sub(fz)
    assert rc != 0 and "one freeze only" in o, o[-600:]
    return {"second_freeze": "refused", "rehearsal_plan_is_latest": side[:12], "blocks": "five, each once"}


def main():
    argv = sys.argv[1:]
    if "--rehearsal" in argv:
        STATE["rehearsal"] = os.path.abspath(argv[argv.index("--rehearsal") + 1])
        argv = argv[:argv.index("--rehearsal")]
    out_path = argv[0] if argv else os.path.join(OUT, "c1_tests_v10.json")
    os.makedirs(OUT, exist_ok=True)
    skip = freeze_skip()
    real_before = {G.rel(p): os.path.exists(p) for p in REAL_PROTOCOL_FILES + [G.QUARANTINE]}
    if not skip:
        assert not any(real_before.values()), "the real tree holds C1 protocol files: %s" % real_before
    t0 = time.time()
    res, ok = {"tested_files_sha256": {f: G.sha(os.path.join(C1, f)) for f in TESTED}, "python": sys.version, "versions": G.versions(),
               "freeze_skip": skip, "C1_FREEZE_LOG_SHA256": os.environ.get("C1_FREEZE_LOG_SHA256")}, True
    for name, fn in (("G4", t_g4), ("M2", t_m2), ("SCENE", t_scene), ("ENVTPP", t_envtpp), ("M1RULE", t_m1rule), ("Q1", t_q1), ("TREE", t_tree), ("FRZ5", t_frz5),
                     ("REHEARSAL", t_rehearsal), ("LEGACY", t_legacy)):
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
    real_after = {G.rel(p): os.path.exists(p) for p in REAL_PROTOCOL_FILES + [G.QUARANTINE]}
    if real_after != real_before:
        ok = False
        res["real_tree_changed"] = {"before": real_before, "after": real_after}
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
