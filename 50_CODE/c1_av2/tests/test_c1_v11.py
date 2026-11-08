#!/usr/bin/env python3
"""Tests of C1 code v08 (Claude line, test_c1_v11, 5 Nov 2026): D16 v23 Choice 44 (R17e M-A, M-C, M-D, M-E, m1, m2, m4, m7) and v24 Choice
45 (a, c), with R17e's probes E2, E3 and E7 as refusal tests, plus every earlier suite. The ONLY bound "test" file of README v08
(c1_freeze_v06 runs it). Synthetic, nuScenes and dummy AV2-TAGGED fixtures only (R17c's p2 and R17d's fx_av2relab, read only); every
post-freeze probe runs in a COPY TREE under 70_TESTS/c1_v01/tests_v11/tree/, so the real tree never gets a C1 hash log, a deposit record,
a stage-B log, a run log, a quarantine folder or a stage-B manifest. No AV2 file is opened.
Real-tree assertions (Choice 44c): before and after, there is no deposit record, no stage-B log and no run-log line from a non-exempt
role; the hash log is absent unless the freeze runs this suite with C1_FREEZE_LOG_SHA256 equal to its SHA-256 (freeze_skip(), which
relaxes ONLY that assertion and the earlier suites' "real log absent" groups). The quarantine folder may exist (it precedes the freeze).
Groups:
  G5      m2: refused for the OSF project as registration (URL, DOI, other case), a plan line without a parsable time (guard on a
          hand-written log line), and R17d's PB4 cases; a registration passes; refusals name OSF_DEPOSIT_GUIDE_v02.md.
  RUNLOG  m1: chained lines; a changed, deleted or unchained line, or a truncated last line, breaks the chain (refused); two writers at
          once keep the chain (lock); non-exempt lines are counted; c1_analyse_v08.logged_check finds a logged output and misses
          another.
  SWEEP   m7: stale c1_gt_* folders (dead pid; old, pid-less) are swept; live and recent ones are kept; guard() sweeps.
  ME      44(e), 45(a): REAL wrapper records: tpp_keys_v03 under canmot310 and under tpp38, tpp_run_v03 under tpp38 (one nuScenes
          scene). keys(canmot310) pass against FROZEN_ENV, keys(tpp38) are refused; run(tpp38) passes against FROZEN_ENV_TPP; a
          canmot310 record is refused as a run. c1_predarm_v06.wrapper_v06 on the real records. c1_tpp_envcheck_v01: --python for
          both interpreters and kinds, and --write-dry then --check.
  MD      44(d), 45(c): c1_analyse_v08 reports Q1 "not tested" with the two reasons; C1_verdict, gate_H1, family_S and H9 equal
          c1_analyse_v07's with a valid Q1 table and without one; a config with q1 is refused (decide_all and main);
          c1_predarm_v06 refuses --q1-only and the QCNet options.
  SCENEMAP m4: c1_av2_scene_map_v01 writes [{"name", "log_token"}] from AV2 stage-A manifests; refuses an existing output and a
          nuScenes manifest; logs as the manifests record them.
  FRZ6    c1_freeze_v06 with README v08 (test = freeze_probe_pass_v01; nuScenes folds, own log, empty data root): first freeze, five
          blocks once each; second freeze refused; --amend appended and logged; refused: a stage-B manifest, a stage-B folder at
          --amend, a failing test, an unbound builder, a re-randomised child, a drafted FROZEN_ENV block, a config with q1, without
          h8_units = folds, a freeze without data:e0_plan or data:scene_json.
  TREE    in the copy tree, on the AV2-tagged stand-in:
          M-A: freeze refused before the quarantine; R17e E2 as refusal: c1_quarantine_v01 with the given manifests leaves an older
          manifest's ground truth plain, and c1_freeze_v06 refuses; c1_quarantine_v02 dry run changes nothing; the real run takes
          the union (older manifest found under 30_DATA), quarantines an --extra file, removes a renamed stray copy found by hash,
          leaves a copy under 50_CODE/env/ (excluded); rerun idempotent; a tampered plain file refused; a pod-recorded path found;
          the freeze then passes; a still-plain --extra refused; R17e E3 as refusal: x2_full_v02 can no longer run on the older
          ground truth.
          PB1: h8, mstage and predarm v06 refused without the deposit record; entry:c1_e0 exempt (an exempt start line).
          M-C: --amend passes with only exempt run-log lines (its probe suite through C1_FREEZE_LOG_SHA256; the same suite run
          directly fails); refused with the deposit record; R17e E7 as refusal: after an H8 outcome, deleting the record does not
          reopen --amend (non-exempt run-log lines); refused after stage B.
          m2: a record naming the OSF project is refused. m1: H8 writes start and done lines (chained; the done line holds the
          output hash); the same output is refused and leaves its start line; c1_analyse_v08 on AV2 records the run log, accepts the
          logged H8 table and rejects it once its bytes change. m4: scene.json from c1_av2_scene_map_v01, 50 units
          checked. Stage B v06: the fixed folder, one stage-B log line, refusals of the same tag, --out and a plain --gt; a deposit
          time after a stage-B build refused.
  LEGACY  every group of test_c1_v01-v10, each suite in its own process, except those skipped by rule: v01 GEN, v02 GEN2/FRZ, v03
          GEN3, v06 FRZ3 (generators vs edited files; c1_freeze_v06 checks them on the archived originals), v08 LEGACY and v10 LEGACY
          (their suites run here), v09 FRZ4 and v10 FRZ5 (README v06 and v07 can no longer be frozen: their entry points are not the
          latest; FRZ6 replaces them).
With --rehearsal <dir>: a second freeze into the rehearsal's log is refused; the rehearsal plan's five blocks appear exactly once; its
decision reports Q1 "not tested" with Choice 44(d)'s reasons.
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v11.py [<out.json>] [--rehearsal <dir>]
"""
import copy
import datetime
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import traceback

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(C1, "tests"))
sys.path.insert(0, os.path.join(W, "50_CODE", "tpp", "tests"))
import c1_guard_v05 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v11")
README = os.path.join(C1, "README_C1_CODE_v08.md")
R17C = os.path.join(W, "70_TESTS", "c1_v01", "r17c_probes")
R17D = os.path.join(W, "70_TESTS", "c1_v01", "r17d_probes")
PY = sys.executable
TPP38 = os.path.join(W, "50_CODE", "env", "tpp38", "Scripts", "python.exe")
TPP_ROOT = os.path.join(W, "50_CODE", "third_party", "Trajectron-plus-plus_eccv2020")
CANON = G.CANONICAL["C1"]
TESTED = ["c1_guard_v05.py", "c1_freeze_v06.py", "c1_quarantine_v02.py", "c1_av2_scene_map_v01.py", "c1_tpp_envcheck_v01.py", "c1_analyse_v08.py",
          "c1_predarm_v06.py", "c1_fit_v06.py", "c1_run_v06.py", "c1_mstage_v06.py", "c1_h8_v06.py", "c1_e0_v05.py", "tests/test_c1_v11.py",
          "../av2/av2_cache_stageB_v06.py", "../k8/k8_items_v08.py", "../tpp/tpp_keys_v03.py", "../tpp/tpp_run_v03.py"]
SKIP = {"test_c1_v01": ["GEN"], "test_c1_v02": ["GEN2", "FRZ"], "test_c1_v03": ["GEN3"], "test_c1_v06": ["FRZ3"], "test_c1_v08": ["LEGACY"],
        "test_c1_v09": ["FRZ4"], "test_c1_v10": ["LEGACY", "FRZ5"]}
LOG_DEPENDENT = {"test_c1_v06": ["LOG", "STAGEB"], "test_c1_v09": ["G3"]}
STATE = {}


def freeze_skip():
    """Choice 44c: relaxes ONLY the 'hash log absent' assertion, when the freeze runs this suite and passes the real log's hash."""
    return os.path.exists(CANON) and os.environ.get("C1_FREEZE_LOG_SHA256") == G.sha(CANON)


def real_state():
    return {"hash_log": os.path.exists(CANON), "deposit_record": os.path.exists(G.DEPOSIT_RECORD), "stage_B_log": os.path.exists(G.STAGE_B_LOG),
            "run_log_nonexempt_lines": len(G.nonexempt_lines()), "run_log_sha256": G.sha(G.RUN_LOG) if os.path.exists(G.RUN_LOG) else None,
            "quarantine": os.path.exists(G.QUARANTINE)}


def raises(fn, *a, **k):
    try:
        fn(*a, **k)
    except (AssertionError, SystemExit) as e:
        return str(e) or "refused"
    return None


def sub(cmd, cwd=C1, env=None, py=None):
    r = subprocess.run([py or PY, "-B"] + cmd, capture_output=True, text=True, cwd=cwd, env=env)
    return r.returncode, (r.stdout + r.stderr)


def wj(p, o):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(o, open(p, "w"), indent=1)
    return p


def utcs(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def readme_rows():
    return re.findall(r"^([0-9a-f]{64})  (50_CODE/\S+)  (\S+)$", open(README, encoding="utf-8").read(), re.M)


def readme_with(test_rel, dst, root=W):
    """README v08's rows with the bound test replaced by test_rel (the earlier test file becomes a test_module)."""
    rows = readme_rows()
    lines = ["%s  %s  %s" % (h, p, ("test_module" if r == "test" else r)) for h, p, r in rows if p != test_rel]
    lines.append("%s  %s  test" % (G.sha(os.path.join(root, test_rel)), test_rel))
    lines += ["superseded  %s" % s for s in re.findall(r"^superseded  (50_CODE/\S+)$", open(README, encoding="utf-8").read(), re.M)
              if os.path.exists(os.path.join(root, s))]
    open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")
    return dst


def mock_plan(d, name, paths, roles=(), env_tpp=None, log_line="frozen 2026-11-01 12:00:00 UTC by test"):
    os.makedirs(d, exist_ok=True)
    plan = os.path.join(d, name)
    v = G.versions()
    body = "# mock plan\n\nFROZEN_HASHES_BEGIN\n%s\nFROZEN_HASHES_END\nFROZEN_ROLES_BEGIN\n%s\nFROZEN_ROLES_END\nFROZEN_ENV_BEGIN\n%s\nFROZEN_ENV_END\n" % (
        "\n".join("%s  %s" % (G.sha(os.path.join(W, p)), p) for p in paths), "\n".join("%s  %s" % (r, p) for r, p in roles),
        "\n".join("%s  %s" % (k, v[k]) for k in ("python", "numpy", "scipy")))
    if env_tpp:
        body += "FROZEN_ENV_TPP_BEGIN\n%s\nFROZEN_ENV_TPP_END\n" % "\n".join("%s  %s" % (k, env_tpp[k]) for k in ("python", "numpy", "torch"))
    open(plan, "w", encoding="utf-8", newline="\n").write(body)
    open(plan[:-3] + ".sha256", "w").write(G.sha(plan) + "  %s\n" % name)
    log = os.path.join(d, "LOG_%s.txt" % name[:-3])
    open(log, "w").write("%s  %s  %s\n" % (G.sha(plan), name, log_line))
    return plan, log


def planted(h1=True):
    import c1_analyse_v08 as A8
    fb = {"met": h1, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False, "pops": {}} for a in A8.A6.REQUIRED_ARMS}
    return {"within_lt3d": {t: {"form_b": fb, "status": st, "form_c": None, "form_a": {}} for t in A8.TRACKERS}}


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
body = src[src.rindex("    for name, fn in ((" + chr(34)):]
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
    for i in range(1, 11):
        mod = "test_c1_v%02d" % i
        skip = list(SKIP.get(mod, [])) + (LOG_DEPENDENT.get(mod, []) if freeze_skip() else [])
        od = os.path.join(OUT, "legacy_" + mod)
        shutil.rmtree(od, ignore_errors=True)
        r = subprocess.run([PY, "-B", "-c", RUNNER, C1, os.path.join(W, "50_CODE", "tpp", "tests"), mod, od, ",".join(skip)],
                           capture_output=True, text=True, cwd=C1)
        rp = os.path.join(od, "legacy_result.json")
        res = json.load(open(rp)) if os.path.exists(rp) else {"error": r.stderr[-1500:]}
        assert r.returncode == 0 and "LEGACY_ONE PASS" in r.stdout, (mod, res, r.stderr[-800:])
        out[mod] = res
    return out


# ------------------------------------------------------------------------------------------------------------------------------ G5
def t_g5():
    d = os.path.join(OUT, "g5")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    side = "a" * 64
    planned = datetime.datetime(2026, 11, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    good_t = utcs(planned + datetime.timedelta(hours=2))

    def rec(name, lines):
        p = os.path.join(d, name)
        open(p, "w").write("\n".join(lines) + "\n")
        return p
    out = {}
    for name, reg in (("url", "https://osf.io/abcde/"), ("doi", "10.17605/OSF.IO/ABCDE")):
        G.check_deposit(side, "nuscenes", rec("ok_%s.txt" % name, ["frozen_plan_sha256: " + side, "registration: " + reg, "registered_utc: " + good_t]), planned)
        out["valid_" + name] = "pass"
    assert G.project_ids() == {"eumj8"}, G.project_ids()
    for name, reg in (("project_url", "https://osf.io/eumj8/"), ("project_url_no_slash", "https://osf.io/eumj8"),
                      ("project_doi", "10.17605/OSF.IO/EUMJ8")):
        m = raises(G.check_deposit, side, "nuscenes", rec(name + ".txt", ["frozen_plan_sha256: " + side, "registration: " + reg, "registered_utc: " + good_t]), planned)
        assert m and "is the OSF project" in m and "OSF_DEPOSIT_GUIDE_v02.md" in m, (name, m)
        out["refused_" + name] = "refused"
    m = raises(G.check_deposit, side, "nuscenes", rec("upper_url.txt", ["frozen_plan_sha256: " + side, "registration: https://osf.io/EUMJ8/",
                                                                        "registered_utc: " + good_t]), planned)
    assert m, "an upper-case project URL passed"
    out["refused_project_url_upper"] = "refused"
    m = raises(G.check_deposit, side, "nuscenes", rec("ok_url.txt", ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/",
                                                                     "registered_utc: " + good_t]), None)
    assert m and "no parsable time" in m, m
    out["refused_no_plan_time_direct"] = "refused"
    cases = {"PB4_registration_TODO": ["frozen_plan_sha256: " + side, "registration: TODO", "registered_utc: " + good_t],
             "PB4_time_not_yet": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: not yet"],
             "PB4_time_2099": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: 2099-01-01T00:00:00Z"],
             "PB4_duplicated_key": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registration: https://osf.io/zzzzz/",
                                    "registered_utc: " + good_t],
             "before_plan_line": ["frozen_plan_sha256: " + side, "registration: https://osf.io/abcde/", "registered_utc: 2026-10-01T00:00:00Z"],
             "wrong_plan": ["frozen_plan_sha256: " + "b" * 64, "registration: https://osf.io/abcde/", "registered_utc: " + good_t]}
    for name, lines in cases.items():
        m = raises(G.check_deposit, side, "nuscenes", rec(name + ".txt", lines), planned)
        assert m and "OSF_DEPOSIT_GUIDE_v02.md" in m, (name, m)
        out[name] = "refused"
    # a plan line without a parsable time, through guard() on a mock nuScenes plan (deposit_path forces the check); in a subprocess that
    # loads only the guards, so that the runtime verification sees bound modules only
    bound = ["50_CODE/c1_av2/c1_h8_v06.py", "50_CODE/c1_av2/c1_guard_v05.py", "50_CODE/c1_av2/c1_guard_v04.py", "50_CODE/c1_av2/c1_guard_v03.py"]
    probe = chr(10).join(["import sys; sys.path.insert(0, %r)" % C1, "import c1_guard_v05 as G", "try:",
                          "    g = G.guard('nuscenes', sys.argv[1], 'entry:c1_h8', %r, sys.argv[2], 'C1', sys.argv[3])" % os.path.join(C1, "c1_h8_v06.py"),
                          "    print('GUARD_OK', g[2]['deposit_record_sha256'], 'run_id' in g[2])", "except AssertionError as e:",
                          "    print('REFUSED', e)", ""])
    plan, log = mock_plan(os.path.join(d, "mp"), "MOCK_HAND.md", bound, [("entry:c1_h8", bound[0])], log_line="frozen (written by hand)")
    dep = rec("dep_mock.txt", ["frozen_plan_sha256: " + G.sha(plan), "registration: https://osf.io/abcde/", "registered_utc: " + utcs(G.utc_now())])
    rc, o = sub(["-c", probe, plan, log, dep])
    assert "REFUSED" in o and "no parsable time" in o, o[-600:]
    out["refused_hand_written_plan_line_via_guard"] = "refused"
    plan2, log2 = mock_plan(os.path.join(d, "mp2"), "MOCK_OK.md", bound, [("entry:c1_h8", bound[0])])
    dep2 = rec("dep_mock2.txt", ["frozen_plan_sha256: " + G.sha(plan2), "registration: https://osf.io/abcde/", "registered_utc: " + utcs(G.utc_now())])
    rc, o = sub(["-c", probe, plan2, log2, dep2])
    assert "GUARD_OK %s False" % G.sha(dep2) in o, o[-600:]
    out["guard_with_parsable_line"] = "pass (no run-log line on nuScenes)"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ RUNLOG
WRITER = r"""
import sys
sys.path.insert(0, sys.argv[1])
import c1_guard_v05 as G
for i in range(int(sys.argv[3])):
    G.run_log_write({"event": "start", "run_id": "w%s_%d" % (sys.argv[4], i), "role": "entry:c1_h8", "entry": "x"}, sys.argv[2])
print("WRITER DONE")
"""


def t_runlog():
    import c1_analyse_v08 as A8
    d = os.path.join(OUT, "runlog")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    p = os.path.join(d, "RUN_LOG.txt")
    out = {}
    G.run_log_write({"event": "start", "run_id": "e0", "role": "entry:c1_e0", "entry": "50_CODE/c1_av2/c1_e0_v05.py"}, p)
    assert G.nonexempt_lines(p) == []
    tab = os.path.join(d, "table.json")
    wj(tab, {"x": 1})
    other = wj(os.path.join(d, "other.json"), {"x": 2})
    G.run_log_write({"event": "start", "run_id": "h8", "role": "entry:c1_h8", "entry": "50_CODE/c1_av2/c1_h8_v06.py"}, p)
    G.run_log_write({"event": "done", "run_id": "h8", "role": "entry:c1_h8", "entry": "50_CODE/c1_av2/c1_h8_v06.py",
                     "outputs_sha256": {G.rel(tab): G.sha(tab)}}, p)
    recs, last = G.read_run_log(p)
    assert len(recs) == 3 and recs[0]["prev_sha256"] == G.GENESIS and len(G.nonexempt_lines(p)) == 2
    logged, info = G.logged_outputs(p)
    okp, missing = A8.logged_check([tab, other], logged)
    assert G.rel(tab) in okp and missing == [G.rel(other)] and info["lines"] == 3
    out["chain_and_logged_check"] = "3 chained lines; the logged table found, another missing; 2 non-exempt lines"
    raw = open(p, "rb").read().decode()
    lines = raw.split("\n")[:-1]
    for name, txt in (("changed_line", "\n".join([lines[0], lines[1].replace("c1_h8", "c1_hX"), lines[2]]) + "\n"),
                      ("deleted_line", "\n".join([lines[0], lines[2]]) + "\n"),
                      ("unchained_line_appended", raw + json.dumps({"event": "done", "role": "entry:c1_h8"}) + "\n"),
                      ("truncated_last_line", raw[:-5])):
        q = os.path.join(d, name + ".txt")
        open(q, "wb").write(txt.encode())
        m = raises(G.read_run_log, q)
        assert m and "Choice 44f m1" in m, (name, m)
        m2 = raises(G.run_log_write, {"event": "start"}, q)
        assert m2, name
        out["refused_" + name] = "refused (also for a further write)"
    pc = os.path.join(d, "RUN_LOG_concurrent.txt")
    procs = [subprocess.Popen([PY, "-B", "-c", WRITER, C1, pc, "25", str(k)], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for k in range(2)]
    outs = [pr.communicate() for pr in procs]
    assert all(pr.returncode == 0 for pr in procs), outs
    recs, _ = G.read_run_log(pc)
    assert len(recs) == 50 and not os.path.exists(pc + ".lock")
    out["two_writers"] = "50 lines, chain intact, lock released"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ SWEEP
def t_sweep():
    d = os.path.join(OUT, "sweep_tmp")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    pr = subprocess.run([PY, "-c", "import os; print(os.getpid())"], capture_output=True, text=True)
    dead = int(pr.stdout.strip())
    mk = {"dead": "c1_gt_%d_aaa" % dead, "own": "c1_gt_%d_bbb" % os.getpid(), "old_nopid": "c1_gt_oldstyle", "new_nopid": "c1_gt_newstyle",
          "other": "not_c1_gt"}
    for k, n in mk.items():
        os.makedirs(os.path.join(d, n))
        open(os.path.join(d, n, "gt.json"), "w").write("{}")
    old = time.time() - 3600
    os.utime(os.path.join(d, mk["old_nopid"]), (old, old))
    removed = G.sweep_stale_tmp(d)
    assert sorted(removed) == sorted([mk["dead"], mk["old_nopid"]]), removed
    for k in ("own", "new_nopid", "other"):
        assert os.path.isdir(os.path.join(d, mk[k])), k
    real = os.path.join(tempfile.gettempdir(), "c1_gt_%d_v11sweep" % dead)
    os.makedirs(real, exist_ok=True)
    assert G.guard("nuscenes", None, "entry:c1_h8", os.path.join(C1, "c1_h8_v06.py")) is None
    assert not os.path.exists(real), "guard() did not sweep a stale folder"
    shutil.rmtree(d, ignore_errors=True)
    return {"swept": "dead pid and old pid-less folders", "kept": "own pid, recent pid-less, unrelated", "guard_sweeps": "yes"}


# ------------------------------------------------------------------------------------------------------------------------------ ME
def t_me():
    import c1_predarm_v06 as P6
    d = os.path.join(OUT, "me")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    cache = os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val")
    scene = sorted(json.load(open(os.path.join(cache, "MANIFEST.json")))["scenes"])[0]
    tp = os.path.join(W, "50_CODE", "tpp")
    k310, k38, r38 = os.path.join(d, "keys_canmot310.npz"), os.path.join(d, "keys_tpp38.npz"), os.path.join(d, "run_tpp38.npz")
    for py, out_ in ((PY, k310), (TPP38, k38)):
        r = subprocess.run([py, "-I", "-B", "tpp_keys_v03.py", "--cache", cache, "--out", out_, "--scenes", scene], capture_output=True, text=True, cwd=tp)
        assert r.returncode == 0 and "TPP KEYS V03 DONE" in r.stdout, r.stdout[-500:] + r.stderr[-800:]
    r = subprocess.run([TPP38, "-I", "-B", "tpp_run_v03.py", "--tpp-root", TPP_ROOT, "--model", "int_ee", "--keys", k310, "--source", "trk", "--out", r38],
                       capture_output=True, text=True, cwd=tp)
    assert r.returncode == 0 and "TPP RUN V03 DONE" in r.stdout, r.stdout[-500:] + r.stderr[-800:]
    w310, w38, wr = (json.load(open(p + ".wrapper.json")) for p in (k310, k38, r38))
    assert G.sha(k310) == G.sha(k38), "the keys differ between the environments"
    code = "import platform, json, numpy, torch; print(json.dumps({'python': platform.python_version(), 'numpy': numpy.__version__, 'torch': torch.__version__}))"
    env_tpp = json.loads(subprocess.run([TPP38, "-I", "-c", code], capture_output=True, text=True).stdout.strip().splitlines()[-1])
    paths = ["50_CODE/tpp/tpp_keys_v03.py", "50_CODE/tpp/tpp_run_v03.py"]
    plan, log = mock_plan(os.path.join(d, "mp"), "MOCK_ENV.md", paths, [("entry:tpp_keys", paths[0]), ("entry:tpp_run", paths[1])], env_tpp=env_tpp)
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    out = {"records": {"keys_canmot310": w310["versions"], "keys_tpp38": w38["versions"], "run_tpp38": wr["versions"]}, "FROZEN_ENV_TPP": env_tpp}
    assert G.env_check(fr, w310, "tpp_keys") == {"python": G.versions()["python"], "numpy": G.versions()["numpy"]}
    out["keys_canmot310_vs_FROZEN_ENV"] = "pass"
    m = raises(G.env_check, fr, w38, "tpp_keys")
    assert m and "FROZEN_ENV" in m and "canmot310" in m, m
    out["keys_tpp38_vs_FROZEN_ENV"] = "refused"
    assert G.env_check(fr, wr, "tpp_run")["torch"] == env_tpp["torch"]
    out["run_tpp38_vs_FROZEN_ENV_TPP"] = "pass"
    m = raises(G.env_check, fr, w310, "tpp_run")
    assert m and "FROZEN_ENV_TPP" in m, m
    out["canmot310_record_as_run"] = "refused"
    assert P6.wrapper_v06(r38, "tpp_run", fr)["versions"]["torch"] == env_tpp["torch"]
    m = raises(P6.wrapper_v06, k310, "tpp_keys", fr)
    assert m and "subset" in m, m
    out["predarm_v06_wrapper_v06"] = "run(tpp38) passes; the one-scene keys are refused as a --scenes subset (R17c M4) before the version check"

    class NoBlock:
        env, env_tpp = None, None
    assert raises(G.env_check, NoBlock, w310, "tpp_keys") and raises(G.env_check, NoBlock, wr, "tpp_run")
    out["no_blocks"] = "refused"
    tool = os.path.join(C1, "c1_tpp_envcheck_v01.py")
    base = [tool, "--plan", plan, "--hash-log", log]
    for py, kind, want in ((PY, "tpp_keys", True), (TPP38, "tpp_keys", False), (TPP38, "tpp_run", True), (PY, "tpp_run", False)):
        rc, o = sub(base + ["--python", py, "--kind", kind])
        assert (rc == 0 and "C1 TPP ENV OK" in o) == want, (py, kind, o[-600:])
        out["envcheck_%s_%s" % (os.path.basename(os.path.dirname(os.path.dirname(py))), kind)] = "ok" if want else "refused"
    dry = os.path.join(d, "dry_tpp38.json")
    r = subprocess.run([TPP38, "-I", "-B", tool, "--write-dry", dry], capture_output=True, text=True)
    assert r.returncode == 0 and json.load(open(dry))["dry"] is True, r.stderr[-400:]
    rc, o = sub(base + ["--check", dry, "--kind", "tpp_run"])
    assert rc == 0 and "C1 TPP ENV OK" in o, o[-400:]
    rc, o = sub(base + ["--check", dry, "--kind", "tpp_keys"])
    assert rc != 0, o[-300:]
    out["dry_record_tpp38"] = "written under tpp38; passes as tpp_run, refused as tpp_keys"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ MD
def t_md():
    import c1_analyse_v07 as A7
    import c1_analyse_v08 as A8
    h9 = {t: {"H9": True, "H9_noHL": True, "arms": {"TPP": {}}, "population": "PD", "H9_seed": {"20261102": True, "20261104": True, "20261105": True}}
          for t in A8.TRACKERS}
    aux0 = {"tables": {"h9": {"ok": True, "data": h9, "checks": {}}}}
    q1tab = {"ok": True, "data": {"t1": {"arms": {"Q1_deployed": {"PD": {}}}}}, "checks": {}}
    keys = ("C1_verdict", "gate_H1", "family_S")
    out = {}
    for h1 in (True, False):
        d8 = A8.decide_all(copy.deepcopy(planted(h1)), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0))
        d7a = A7.decide_all(copy.deepcopy(planted(h1)), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0, q1=q1tab))
        d7b = A7.decide_all(copy.deepcopy(planted(h1)), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0, q1=None))
        for dd in (d7a, d7b):
            assert json.dumps({k: d8[k] for k in keys}, sort_keys=True, default=str) == json.dumps({k: dd[k] for k in keys}, sort_keys=True, default=str)
            assert d8["hypotheses"]["H9"] == dd["hypotheses"]["H9"] and d8["claims_status"]["H9"] == dd["claims_status"]["H9"]
        q = d8["hypotheses"]["Q1"]
        assert q["status"] == "not tested" and q["reasons"] == A8.Q1_REASONS and d8["claims_status"]["Q1"] == "not tested" and "Q1" in d8["not_tested"]
        assert "10 Hz matched AB3DMOT" in q["reasons"][0] and "95.7 %" in q["reasons"][1]
        assert not any("Q1" in x for x in d8["missing_inputs"]) and "tables missing" not in json.dumps(q)
        out["gate_%s" % h1] = "C1_verdict, gate_H1, family_S, H9 identical to v07's with and without a Q1 table; Q1 not tested with 44(d)'s reasons"
    m = raises(A8.decide_all, planted(), {"routes": [], "q1": {"t1": "x"}}, "smoke", dict(aux0))
    assert m and "Choice 44d" in m
    d = os.path.join(OUT, "md")
    shutil.rmtree(d, ignore_errors=True)
    cfg = wj(os.path.join(d, "cfg.json"), {"routes": [], "q1": {"t1": "x"}})
    rc, o = sub(["c1_analyse_v08.py", "--config", cfg, "--out", os.path.join(d, "a.json"), "--decision", os.path.join(d, "d.json"), "--smoke"])
    assert rc != 0 and "Choice 44d" in o and not os.path.exists(os.path.join(d, "a.json")), o[-400:]
    out["q1_config"] = "refused (decide_all and main)"
    kp = os.path.join(d, "keys_never_opened.npz")  # the refusal comes before any input is read
    for extra in (["--q1-only"], ["--qcnet-deployed", kp], ["--qcnet-gt-summary", kp]):
        rc, o = sub(["c1_predarm_v06.py", "--keys", kp, "--folds", os.path.join(d, "none.json"), "--tracker-index", "0", "--out",
                     os.path.join(d, "pa.json"), "--synthetic"] + extra)
        assert rc != 0 and "Choice 44d" in o, o[-400:]
    out["predarm_v06_qcnet"] = "refused (--q1-only, --qcnet-deployed, --qcnet-gt-summary)"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ SCENEMAP
def t_scenemap():
    d = os.path.join(OUT, "scenemap")
    shutil.rmtree(d, ignore_errors=True)
    fxm = os.path.join(R17D, "fx_av2relab", "stageA", "MANIFEST.json")
    av2m = wj(os.path.join(d, "av2_ids", "MANIFEST.json"), {"stage": "A", "dataset": "av2",
                                                            "scenes": {u: {"log": u} for u in json.load(open(fxm))["scenes"]}})
    out = {}
    o1 = os.path.join(d, "m1", "scene.json")
    rc, o = sub(["c1_av2_scene_map_v01.py", "--stageA-manifests", av2m, "--out", o1])
    assert rc == 0 and "C1 AV2 SCENE MAP V01 DONE" in o, o[-600:]
    sm = json.load(open(o1))
    assert len(sm) == 50 and all(e["name"] == e["log_token"] for e in sm) and [e["name"] for e in sm] == sorted(e["name"] for e in sm)
    out["av2_ids"] = "50 units, log_token = name (as av2_cache_stageA_v02 records)"
    o2 = os.path.join(d, "m2", "scene.json")
    rc, o = sub(["c1_av2_scene_map_v01.py", "--stageA-manifests", fxm, "--out", o2])
    man = json.load(open(fxm))["scenes"]
    assert rc == 0 and all(e["log_token"] == man[e["name"]]["log"] for e in json.load(open(o2))), o[-400:]
    out["manifest_logs"] = "log_token = the manifest's log"
    rc, o = sub(["c1_av2_scene_map_v01.py", "--stageA-manifests", av2m, "--out", o1])
    assert rc != 0 and "never overwritten" in o
    nu = os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")
    rc, o = sub(["c1_av2_scene_map_v01.py", "--stageA-manifests", nu, "--out", os.path.join(d, "m3", "scene.json")])
    assert rc != 0 and "not an AV2 manifest" in o, o[-300:]
    bad = wj(os.path.join(d, "bad", "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {sorted(man)[0]: {"log": "other"}}})
    rc, o = sub(["c1_av2_scene_map_v01.py", "--stageA-manifests", av2m, bad, "--out", os.path.join(d, "m4", "scene.json")])
    assert rc != 0 and "two logs" in o, o[-300:]
    out["refused"] = "existing output, nuScenes manifest, two logs for one unit"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ FRZ6
def t_frz6():
    d = os.path.join(OUT, "frz6")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    rp = readme_with("50_CODE/c1_av2/tests/freeze_probe_pass_v01.py", os.path.join(d, "README_probe.md"))
    rf = readme_with("50_CODE/c1_av2/tests/freeze_probe_fail_v01.py", os.path.join(d, "README_fail.md"))
    units = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val", "MANIFEST.json")))["scenes"])
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s %s" % (u, "held_out_train" if i < 60 else "val") for i, u in enumerate(units)) + "\n")
    fo, v150, t225 = (os.path.join(d, x) for x in ("folds.json", "folds_val150.json", "folds_train225.json"))
    for cmd in (["--logs", lp, "--out", fo, "--dataset", "nuscenes"], ["--restrict-from", fo, "--source", "val", "--out", v150],
                ["--restrict-from", fo, "--source", "held_out_train", "--out", t225]):
        rc, o = sub(["c1_folds_v03.py"] + cmd)
        assert rc == 0, o[-600:]
    split = wj(os.path.join(d, "split.json"), {"rule": "probe split"})
    cfg = wj(os.path.join(d, "config.json"), {"note": "probe config", "h8_units": "folds"})
    e0p = wj(os.path.join(d, "e0_plan.json"), {"car|<20|lat": 0.1})
    scj = os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval", "scene.json")
    root = os.path.join(d, "emptyroot")
    os.makedirs(root)
    TF = os.path.join(W, "60_RESULTS", "c1_transfer_fits_v01")
    man = [os.path.join(W, "30_DATA", "k6", "cache_v02_t1_%s" % p, "MANIFEST.json") for p in ("train", "val")]

    def args(plan, readme, log, extra=(), folds150=v150, droot=root, config=cfg, data=("e0_plan=" + e0p, "scene_json=" + scj)):
        return (["c1_freeze_v06.py", "--plan", plan, "--readme", readme, "--results-dir", os.path.join(d, "results"), "--folds", fo, "--split", split,
                 "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"), os.path.join(TF, "c1_transfer_fits_t3_v01.json"),
                 "--stageA-manifests"] + man + ["--config", config, "--folds-val150", folds150, "--folds-train225", t225, "--hash-log", log,
                                               "--data-root", droot, "--test-out-dir", os.path.join(d, "tests_out"), "--data"] + list(data) + list(extra))
    tmpl = "# probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n"

    def plan(k, body=None):
        q = os.path.join(d, "PLAN_%s.md" % k)
        open(q, "w").write(body or tmpl % k)
        return q
    out, log = {}, os.path.join(d, "LOG.txt")
    p1 = plan(1)
    rc, o = sub(args(p1, rp, log))
    assert rc == 0 and "C1 FREEZE V06 DONE" in o, o[-1500:]
    txt = open(p1, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    assert "ALL_PASS" in txt and "folds_val150" in txt and "Choice 44a" in txt and "data:scene_json" in txt and "data:e0_plan" in txt
    side1, _ = G.frozen_plan(p1, "nuscenes", log)
    out["first_freeze"] = "done (%s); five blocks once each" % side1[:12]
    p2 = plan(2)
    rc, o = sub(args(p2, rp, log))
    assert rc != 0 and "one freeze only" in o, o[-800:]
    out["second_freeze"] = "refused"
    sbf = os.path.join(root, "av2_cache_stageB_x")
    os.makedirs(sbf)
    rc, o = sub(args(p2, rp, log, ["--amend", "probe amendment"]))
    assert rc != 0 and "stage-B folder exists" in o, o[-800:]
    os.rmdir(sbf)
    out["amend_with_stage_B_folder"] = "refused"
    rc, o = sub(args(p2, rp, log, ["--amend", "probe amendment"]))
    assert rc == 0 and "C1 FREEZE V06 DONE" in o, o[-1500:]
    assert os.path.exists(os.path.join(d, "C1_DEVIATION_LOG_REHEARSAL.md"))
    assert raises(G.frozen_plan, p1, "nuscenes", log) and G.frozen_plan(p2, "nuscenes", log)
    out["amend"] = "appended, logged; only the new plan accepted"
    os.makedirs(os.path.join(d, "root_b", "cacheX"))
    wj(os.path.join(d, "root_b", "cacheX", "MANIFEST.json"), {"stage": "B", "dataset": "nuscenes", "scenes": {}})
    p3 = plan(3)
    rc, o = sub(args(p3, rp, os.path.join(d, "LOG3.txt"), droot=os.path.join(d, "root_b")))
    assert rc != 0 and "stage-B manifest exists" in o, o[-800:]
    out["stage_B_manifest_present"] = "refused"
    for name, kw, msg in (("q1_in_config", {"config": wj(os.path.join(d, "cfg_q1.json"), {"h8_units": "folds", "q1": {"t1": "x"}})}, "Choice 44d"),
                          ("no_h8_units", {"config": wj(os.path.join(d, "cfg_noh8.json"), {"note": "x"})}, "h8_units = folds"),
                          ("h8_units_other", {"config": wj(os.path.join(d, "cfg_h8v.json"), {"h8_units": "folds_val150"})}, "h8_units = folds"),
                          ("no_e0_plan", {"data": ("scene_json=" + scj,)}, "data:e0_plan"),
                          ("no_scene_json", {"data": ("e0_plan=" + e0p,)}, "data:scene_json")):
        rc, o = sub(args(p3, rp, os.path.join(d, "LOG_%s.txt" % name), **kw))
        assert rc != 0 and msg in o, (name, o[-600:])
        out["config_" + name] = "refused"
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


# ------------------------------------------------------------------------------------------------------------------------------ TREE
def build_tree(T):
    shutil.rmtree(T, ignore_errors=True)
    for h, p, r in readme_rows():
        dst = os.path.join(T, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(W, p), dst)
        assert G.sha(dst) == h, p
    shutil.copy2(README, os.path.join(T, "50_CODE", "c1_av2", "README_C1_CODE_v08.md"))
    shutil.copy2(os.path.join(C1, "c1_quarantine_v01.py"), os.path.join(T, "50_CODE", "c1_av2", "c1_quarantine_v01.py"))  # superseded, for E2
    for rel_ in ("60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_t1_v01.json", "60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_t3_v01.json",
                 "60_RESULTS/x2/x2_oc_q4_v02.json", "40_PROTOCOL/OSF_PROJECT_RECORD_v01.txt"):
        os.makedirs(os.path.dirname(os.path.join(T, rel_)), exist_ok=True)
        shutil.copy2(os.path.join(W, rel_), os.path.join(T, rel_))
    fx = os.path.join(T, "30_DATA", "fx_av2relab")
    shutil.copytree(os.path.join(R17D, "fx_av2relab"), fx)
    gt = os.path.join(fx, "gt.json")
    man = json.load(open(os.path.join(fx, "stageA", "MANIFEST.json")))
    man["inputs"].update({"workers": [os.path.join(fx, "worker0")], "horizon": os.path.join(fx, "horizon.jsonl.gz"), "gt": gt})
    assert man["inputs"]["gt_sha256"] == G.sha(gt)
    wj(os.path.join(fx, "stageA", "MANIFEST.json"), man)
    zero = {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": gt, "gt_sha256": G.sha(gt)}, "note": "zero-scene stage-A cache (test v11)"}
    wj(os.path.join(T, "30_DATA", "fx_stageA_zero", "MANIFEST.json"), zero)
    p2 = os.path.join(T, "70_TESTS", "fx_p2")  # outside 30_DATA: R17c p2 holds a stage-B manifest
    shutil.copytree(os.path.join(R17C, "p2"), p2, ignore=shutil.ignore_patterns("*.json.tmp"))
    # R17e E2: an OLDER stage-A manifest under 30_DATA naming its own plain prepared ground truth (other bytes), never passed explicitly
    old_gt = os.path.join(T, "30_DATA", "av2_trk_v01", "gt", "av2_val_gt_v01.json")
    os.makedirs(os.path.dirname(old_gt), exist_ok=True)
    open(old_gt, "w").write(json.dumps(json.load(open(gt)), indent=1, sort_keys=True))
    assert G.sha(old_gt) != G.sha(gt)
    wj(os.path.join(T, "30_DATA", "av2_cache_stageA_v01", "cache_stageA_t1_lt3d", "MANIFEST.json"),
       {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": old_gt, "gt_sha256": G.sha(old_gt)}, "note": "older stage-A manifest (R17e E2)"})
    extra = os.path.join(T, "30_DATA", "av2_det_v01", "lt3d_centerpoint", "fx_det_gt_v01.feather")
    os.makedirs(os.path.dirname(extra), exist_ok=True)
    open(extra, "wb").write(os.urandom(4096))
    stray = os.path.join(T, "60_RESULTS", "stray", "renamed_copy.bin")
    os.makedirs(os.path.dirname(stray), exist_ok=True)
    shutil.copy2(gt, stray)
    envc = os.path.join(T, "50_CODE", "env", "x", "gt_copy.json")
    os.makedirs(os.path.dirname(envc), exist_ok=True)
    shutil.copy2(gt, envc)
    return {"fx": fx, "gt": gt, "zero": os.path.join(T, "30_DATA", "fx_stageA_zero"), "p2": p2, "old_gt": old_gt, "extra": extra, "stray": stray, "envc": envc}


def tree_freeze(T, F, plan_name, extra=()):
    plan = os.path.join(T, "70_TESTS", plan_name)
    if not os.path.exists(plan):
        os.makedirs(os.path.dirname(plan), exist_ok=True)
        open(plan, "w").write("# tree probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n" % plan_name)
    fx = F["fx"]
    cmd = [os.path.join(T, "50_CODE", "c1_av2", "c1_freeze_v06.py"), "--plan", plan, "--readme", F["readme"], "--results-dir",
           os.path.join(T, "70_TESTS", "results_" + plan_name), "--folds", os.path.join(fx, "folds_av2.json"), "--split", F["split"],
           "--transfer-fits", os.path.join(T, "60_RESULTS", "c1_transfer_fits_v01", "c1_transfer_fits_t1_v01.json"),
           os.path.join(T, "60_RESULTS", "c1_transfer_fits_v01", "c1_transfer_fits_t3_v01.json"),
           "--stageA-manifests", os.path.join(fx, "stageA", "MANIFEST.json"), os.path.join(F["zero"], "MANIFEST.json"), "--config", F["config"],
           "--data", "scene_json=" + F["scene_json"], "e0_plan=" + os.path.join(fx, "e0_plan.json"),
           "--test-out-dir", os.path.join(T, "70_TESTS", "freeze_tests_" + plan_name),
           "--tpp-python", TPP38] + list(extra)
    return plan, sub(cmd, cwd=os.path.join(T, "50_CODE", "c1_av2"))


def t_tree():
    T = os.path.join(OUT, "tree")
    F = build_tree(T)
    TC = os.path.join(T, "50_CODE", "c1_av2")
    proto = lambda n: os.path.join(T, "40_PROTOCOL", n)  # noqa: E731
    out = {}
    probe = "50_CODE/c1_av2/tests/freeze_probe_envcheck_v01.py"
    F["readme"] = readme_with(probe, os.path.join(TC, "README_tree_probe.md"), root=T)
    F["split"] = wj(os.path.join(T, "30_DATA", "fx_split.json"), {"rule": "tree probe split"})
    F["config"] = wj(os.path.join(T, "30_DATA", "fx_config.json"), {"note": "tree probe config", "h8_units": "folds", "routes": [], "h9_label": "secondary",
                                                                    "folds": os.path.join(F["fx"], "folds_av2.json"), "c": {"t1": 0.03, "t3": 0.03},
                                                                    "h8": os.path.join(T, "70_TESTS", "h8_post.json")})
    F["scene_json"] = os.path.join(T, "30_DATA", "fx_meta", "scene.json")
    rc, o = sub([os.path.join(TC, "c1_av2_scene_map_v01.py"), "--stageA-manifests", os.path.join(F["fx"], "stageA", "MANIFEST.json"),
                 os.path.join(F["zero"], "MANIFEST.json"), "--out", F["scene_json"]], cwd=TC)
    assert rc == 0 and "SCENE MAP V01 DONE" in o, o[-600:]
    out["m4_scene_map_built"] = "c1_av2_scene_map_v01 in the tree (50 units)"
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md")
    assert rc != 0 and "quarantine it first" in o, o[-800:]
    out["freeze_before_quarantine"] = "refused"
    qv1 = [os.path.join(TC, "c1_quarantine_v01.py"), "--stageA-manifests", os.path.join(F["fx"], "stageA", "MANIFEST.json"), os.path.join(F["zero"], "MANIFEST.json")]
    rc, o = sub(qv1, cwd=TC)
    assert rc == 0 and not os.path.exists(F["gt"]) and os.path.exists(F["old_gt"]), o[-600:]
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md")
    assert rc != 0 and "quarantine it first" in o and "av2_val_gt_v01.json" in o, o[-800:]
    out["E2_refusal"] = "c1_quarantine_v01 with the given manifests left the older manifest's ground truth plain; c1_freeze_v06 refused"
    q2 = [os.path.join(TC, "c1_quarantine_v02.py"), "--stageA-manifests", os.path.join(F["fx"], "stageA", "MANIFEST.json"), "--extra", F["extra"]]
    before = sorted(os.listdir(os.path.join(T, "30_DATA", "av2_gt_quarantine_v01")))
    rc, o = sub(q2 + ["--dry-run"], cwd=TC)
    assert rc == 0 and "DRY RUN" in o and os.path.exists(F["old_gt"]) and os.path.exists(F["extra"]) and os.path.exists(F["stray"]), o[-600:]
    assert sorted(os.listdir(os.path.join(T, "30_DATA", "av2_gt_quarantine_v01"))) == before
    rc, o = sub(q2, cwd=TC)
    assert rc == 0 and "QUARANTINE V02 DONE" in o, o[-1500:]
    for k in ("old_gt", "extra", "stray"):
        assert not os.path.exists(F[k]), k
    assert os.path.exists(F["envc"]), "the copy under 50_CODE/env/ must be left (excluded from the scan)"
    qm = json.load(open(os.path.join(T, "30_DATA", "av2_gt_quarantine_v01", "QUARANTINE_MANIFEST.json")))["members"]
    kinds = {m["member"]: m.get("kinds") for m in qm}
    assert any("extra" in (k or []) for k in kinds.values()) and all(isinstance(m.get("bytes"), int) for m in qm), qm
    assert any(m["sha256_decompressed"] == G.sha_stream(F["envc"]) and any("renamed_copy.bin" in r for r in m.get("removed", [])) for m in qm)
    rc, o = sub(q2, cwd=TC)
    assert rc == 0 and "already quarantined" in o, o[-600:]
    out["M-A_quarantine_v02"] = "dry run changed nothing; union found the older manifest; --extra quarantined; renamed stray copy found by hash and " \
                                "removed; the copy under 50_CODE/env/ left; rerun idempotent; bytes recorded"
    tam = os.path.join(T, "70_TESTS", "fx_tamper")
    os.makedirs(tam, exist_ok=True)
    open(os.path.join(tam, "gt_t.json"), "w").write("{}")
    wj(os.path.join(tam, "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": os.path.join(tam, "gt_t.json"), "gt_sha256": "0" * 64}})
    rc, o = sub([os.path.join(TC, "c1_quarantine_v02.py"), "--stageA-manifests", os.path.join(tam, "MANIFEST.json")], cwd=TC)
    assert rc != 0 and "differs from the hash" in o and os.path.exists(os.path.join(tam, "gt_t.json")), o[-600:]
    pod = os.path.join(T, "30_DATA", "fx_pod")
    os.makedirs(pod, exist_ok=True)
    open(os.path.join(pod, "gt_pod.json"), "w").write('{"pod": 1}')
    podm = wj(os.path.join(T, "70_TESTS", "fx_pod_manifest", "MANIFEST.json"),
              {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": "/workspace/W/30_DATA/fx_pod/gt_pod.json",
                                                                         "gt_sha256": G.sha(os.path.join(pod, "gt_pod.json"))}})
    rc, o = sub([os.path.join(TC, "c1_quarantine_v02.py"), "--stageA-manifests", podm], cwd=TC)
    assert rc == 0 and not os.path.exists(os.path.join(pod, "gt_pod.json")), o[-600:]
    out["quarantine_refusals_and_pod"] = "a tampered plain file refused; a pod-recorded path quarantined from 30_DATA"
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", ["--extra", F["extra"]])
    assert rc == 0 and "C1 FREEZE V06 DONE" in o, o[-1500:]
    txt = open(plan1, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    assert "C1_FREEZE_LOG_SHA256=absent" in txt and "plain_matches" in txt and "scene.json (Choice 44f m4)" in txt
    out["freeze_after_quarantine"] = "done; five blocks once each; ground-truth scan and scene.json recorded"
    fx, p2 = F["fx"], F["p2"]
    meta, hz, w0, e0 = os.path.dirname(F["scene_json"]), os.path.join(fx, "horizon.jsonl.gz"), os.path.join(fx, "worker0"), os.path.join(fx, "e0_plan.json")
    folds = os.path.join(fx, "folds_av2.json")
    member = os.path.join(T, "30_DATA", "av2_gt_quarantine_v01", "gt.json.gz")
    rc, o = sub([os.path.join(T, "50_CODE", "x1", "x2_full_v02.py"), "--prereg", os.path.join(R17D, "p2b", "SELF_MADE_PREREG.md"), "--skip-bind",
                 "--expected-tokens", "2008", "--workers", w0, "--gt", F["old_gt"], "--meta", meta, "--oc", os.path.join(T, "60_RESULTS", "x2", "x2_oc_q4_v02.json"),
                 "--horizon", hz, "--out", os.path.join(T, "70_TESTS", "x2_e3.json")], cwd=os.path.join(T, "50_CODE", "x1"))
    assert rc != 0 and not os.path.exists(os.path.join(T, "70_TESTS", "x2_e3.json")), o[-600:]
    out["E3_refusal"] = "x2_full_v02 cannot run on the older ground truth after the freeze (%s)" % o.strip().splitlines()[-1][:80]
    P = ["--plan", plan1]
    pb1 = {"h8_v06": [os.path.join(TC, "c1_h8_v06.py"), "--workers", w0, "--gt", member, "--meta", meta, "--horizon", hz, "--e0-plan", e0,
                      "--folds", folds, "--out", os.path.join(T, "70_TESTS", "h8_pb1.json")] + P,
           "mstage_v06": [os.path.join(TC, "c1_mstage_v06.py"), "--tracker", "T1", "--experiment", "x", "--av2-workers", w0, "--av2-gt", member,
                          "--av2-meta", meta, "--av2-horizon", hz, "--train-workers", os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker1"),
                          "--train-gt", os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json"), "--train-meta", os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval"),
                          "--train-horizon", os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"), "--folds", folds,
                          "--out", os.path.join(T, "70_TESTS", "ms_pb1.json")] + P,
           "predarm_v06": [os.path.join(TC, "c1_predarm_v06.py"), "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", os.path.join(p2, "folds.json"),
                           "--tracker-index", "0", "--out", os.path.join(T, "70_TESTS", "pa_pb1.json")] + P}
    for name, cmd in pb1.items():
        rc, o = sub(cmd, cwd=TC)
        assert rc != 0 and "no deposit record" in o, (name, o[-700:])
        out["PB1_" + name] = "refused (no deposit record)"
    assert not os.path.exists(proto("C1_RUN_LOG.txt")), "a refused run wrote a run-log line"
    probe_e0 = ("import sys; sys.path.insert(0, %r)\nimport c1_guard_v05 as G\n"
                "s, f, rt = G.guard('av2', %r, 'entry:c1_e0', %r)\nprint('E0_GUARD', rt['deposit_record_sha256'], rt['run_id'])" % (TC, plan1, os.path.join(TC, "c1_e0_v05.py")))
    rc, o = sub(["-c", probe_e0], cwd=TC)
    assert rc == 0 and "E0_GUARD exempt (entry:c1_e0)" in o, o[-600:]
    recs, _ = G.read_run_log(proto("C1_RUN_LOG.txt"))
    assert len(recs) == 1 and recs[0]["role"] == "entry:c1_e0" and recs[0]["event"] == "start"
    out["entry:c1_e0"] = "exempt from the deposit; one exempt start line"
    plan2, (rc, o) = tree_freeze(T, F, "PLAN_2.md", ["--amend", "tree probe amendment (only exempt run-log lines)", "--extra", F["extra"]])
    assert rc == 0 and "C1 FREEZE V06 DONE" in o, o[-1500:]
    t2 = open(plan2, encoding="utf-8").read()
    assert "C1_FREEZE_LOG_SHA256=" in t2 and "C1_FREEZE_LOG_SHA256=absent" not in t2
    rc, o = sub([os.path.join(T, probe), os.path.join(T, "70_TESTS", "probe_direct.json")], cwd=TC)
    assert "FAIL" in o, o[-300:]
    assert os.path.exists(proto("C1_DEVIATION_LOG_v01.md"))
    out["M-C_amend_before_outcomes"] = "passes with only an exempt run-log line; its suite passes through C1_FREEZE_LOG_SHA256 and fails directly; logged"
    lines = [l for l in open(proto("C1_PLAN_HASH_LOG.txt")).read().splitlines() if l.strip()]
    assert re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC", lines[-1])
    time.sleep(1.5)
    side2 = G.sha(plan2)
    dep = proto("C1_PLAN_DEPOSIT_RECORD_v01.txt")
    h8o = os.path.join(T, "70_TESTS", "h8_post.json")
    h8 = [os.path.join(TC, "c1_h8_v06.py"), "--workers", w0, "--gt", member, "--meta", meta, "--horizon", hz, "--e0-plan", e0, "--folds", folds,
          "--out", h8o, "--plan", plan2]
    open(dep, "w").write("frozen_plan_sha256: %s\nregistration: https://osf.io/eumj8/\nregistered_utc: %s\n" % (side2, utcs(G.utc_now())))
    rc, o = sub(h8, cwd=TC)
    assert rc != 0 and "is the OSF project" in o and not os.path.exists(h8o), o[-600:]
    out["m2_project_as_registration"] = "refused"
    open(dep, "w").write("frozen_plan_sha256: %s\nregistration: https://osf.io/abcde/\nregistered_utc: %s\n" % (side2, utcs(G.utc_now())))
    plan3, (rc, o) = tree_freeze(T, F, "PLAN_3.md", ["--amend", "after the deposit", "--extra", F["extra"]])
    assert rc != 0 and "has been deposited" in o, o[-600:]
    out["amend_after_deposit"] = "refused"
    rc, o = sub(h8, cwd=TC)
    assert rc == 0 and "C1 H8 V06 DONE" in o, o[-1500:]
    t8 = json.load(open(h8o))
    assert t8["provenance"]["deposit_record_sha256"] == G.sha(dep) and t8["provenance"]["scene_json_check"]["units_checked"] == 50
    recs, _ = G.read_run_log(proto("C1_RUN_LOG.txt"))
    st, dn = recs[-2], recs[-1]
    assert st["event"] == "start" and dn["event"] == "done" and st["run_id"] == dn["run_id"] and st["role"] == "entry:c1_h8"
    assert list(dn["outputs_sha256"].values()) == [G.sha(h8o)]
    logged, _ = G.logged_outputs(proto("C1_RUN_LOG.txt"))
    assert G.sha(h8o) in logged
    rc, o = sub(h8, cwd=TC)
    assert rc != 0 and "never overwritten" in o, o[-500:]
    recs2, _ = G.read_run_log(proto("C1_RUN_LOG.txt"))
    assert len(recs2) == len(recs) + 1 and recs2[-1]["event"] == "start"
    out["m1_h8_after_deposit"] = "runs from the quarantine; scene.json (50 units); chained start and done lines, the done line holds the output " \
                                 "hash; the same output refused, leaving its start line"
    an = lambda k: [os.path.join(TC, "c1_analyse_v08.py"), "--config", F["config"], "--out", os.path.join(T, "70_TESTS", "an%d.json" % k),  # noqa: E731
                    "--decision", os.path.join(T, "70_TESTS", "dec%d.json" % k), "--c1", "--plan", plan2]
    rc, o = sub(an(1), cwd=TC)
    assert rc == 0 and "C1 ANALYSIS V08 DONE" in o, o[-1500:]
    d1 = json.load(open(os.path.join(T, "70_TESTS", "dec1.json")))
    assert d1["tables"]["h8"]["ok"] and "h8" in d1["binding"]["tables_in_run_log"] and d1["binding"]["run_log_at_start"]["lines"] >= 4, d1["tables"]
    assert d1["hypotheses"]["Q1"]["status"] == "not tested" and d1["binding"]["run_log_at_start"]["run_log_sha256"]
    recs3, _ = G.read_run_log(proto("C1_RUN_LOG.txt"))
    assert recs3[-1]["event"] == "done" and recs3[-1]["role"] == "entry:c1_analyse" and recs3[-2]["role"] == "entry:c1_analyse"
    t8x = dict(t8, tampered_after_the_run=True)
    json.dump(t8x, open(h8o, "w"), indent=1)
    rc, o = sub(an(2), cwd=TC)
    assert rc == 0 and "C1 ANALYSIS V08 DONE" in o, o[-1500:]
    d2 = json.load(open(os.path.join(T, "70_TESTS", "dec2.json")))
    assert d2["tables"]["h8"]["ok"] is False and "no 'done' line" in (d2["tables"]["h8"]["why"] or ""), d2["tables"]["h8"]
    out["m1_analysis"] = "on AV2 the analysis records the run log and accepts the logged H8 table; after the table's bytes change it has no " \
                         "'done' line and is not provenance-valid; Q1 not tested; chained start and done lines"
    os.remove(dep)
    plan3, (rc, o) = tree_freeze(T, F, "PLAN_3.md", ["--amend", "R17e E7: record deleted after an H8 outcome", "--extra", F["extra"]])
    assert rc != 0 and "non-exempt" in o and "Choice 44c" in o, o[-600:]
    out["E7_refusal"] = "after an H8 outcome, deleting the deposit record does not reopen --amend (non-exempt run-log lines)"
    open(dep, "w").write("frozen_plan_sha256: %s\nregistration: https://osf.io/abcde/\nregistered_utc: %s\n" % (side2, utcs(G.utc_now() - datetime.timedelta(seconds=1))))
    sb = os.path.join(T, "50_CODE", "av2", "av2_cache_stageB_v06.py")
    base = [sb, "--stage-a", F["zero"], "--frozen-plan", plan2]
    rc, o = sub(base + ["--gt", member, "--tag", "t1"], cwd=os.path.join(T, "50_CODE", "av2"))
    assert rc == 0 and os.path.exists(os.path.join(T, "30_DATA", "av2_cache_stageB_t1", "MANIFEST.json")), o[-1200:]
    assert len(open(proto("C1_STAGE_B_LOG.txt")).read().splitlines()) == 1
    mb = json.load(open(os.path.join(T, "30_DATA", "av2_cache_stageB_t1", "MANIFEST.json")))
    assert mb["stage_b"]["deposit_record_sha256"] == G.sha(dep)
    recs, _ = G.read_run_log(proto("C1_RUN_LOG.txt"))
    assert recs[-1]["event"] == "done" and recs[-1]["role"] == "entry:stageB" and recs[-2]["event"] == "start" and recs[-2]["role"] == "entry:stageB"
    for name, extra, msg in (("same_tag", ["--gt", member, "--tag", "t1"], "never overwritten"),
                             ("out_on_av2", ["--gt", member, "--tag", "t2", "--out", os.path.join(T, "30_DATA", "elsewhere")], "--tag only"),
                             ("plain_gt", ["--gt", os.path.join(tam, "gt_t.json"), "--tag", "t3"], "only from the quarantine")):
        rc, o = sub(base + extra, cwd=os.path.join(T, "50_CODE", "av2"))
        assert rc != 0 and msg in o, (name, o[-600:])
        out["stageB_" + name] = "refused"
    late = utcs(G.utc_now() + datetime.timedelta(seconds=1))
    time.sleep(2.5)
    open(dep, "w").write("frozen_plan_sha256: %s\nregistration: https://osf.io/abcde/\nregistered_utc: %s\n" % (side2, late))
    rc, o = sub(h8[:-4] + ["--out", os.path.join(T, "70_TESTS", "h8_late.json"), "--plan", plan2], cwd=TC)
    assert rc != 0 and "stage-B build" in o, o[-600:]
    out["deposit_after_stageB_build"] = "refused"
    os.remove(dep)
    plan4, (rc, o) = tree_freeze(T, F, "PLAN_4.md", ["--amend", "after stage B", "--extra", F["extra"]])
    assert rc != 0 and "a stage B has been built" in o, o[-600:]
    out["amend_after_stageB"] = "refused"
    out["stageB_v06"] = "writes only 30_DATA/av2_cache_stageB_<tag>/; one stage-B log line; chained start and done lines; deposit recorded"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ rehearsal
def t_rehearsal():
    reh = STATE.get("rehearsal")
    if not reh:
        return {"skipped": "no --rehearsal"}
    import c1_analyse_v08 as A8
    plan = os.path.join(reh, "MOCK_C1_PLAN_v06.md")
    log = os.path.join(reh, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    txt = open(plan, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    dec = json.load(open(os.path.join(reh, "c1_decision_rehearsal_v06.json")))
    assert dec["hypotheses"]["Q1"]["status"] == "not tested" and dec["hypotheses"]["Q1"]["reasons"] == A8.Q1_REASONS
    steps = [json.loads(l) for l in open(os.path.join(reh, "steps.jsonl"))]
    fz = [s["key"] for s in steps if s["key"].startswith("c1_freeze_v06.py") and "MOCK_C1_PLAN_v06" in s["key"]][0].split(" ")
    p2 = os.path.join(OUT, "SECOND_PLAN.md")
    open(p2, "w").write("# second plan\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n")
    fz[fz.index("--plan") + 1] = p2
    fz[fz.index("--results-dir") + 1] = os.path.join(OUT, "results2")
    rc, o = sub(fz)
    assert rc != 0 and "one freeze only" in o, o[-600:]
    return {"second_freeze": "refused", "rehearsal_plan_is_latest": side[:12], "blocks": "five, each once", "Q1": "not tested with 44(d)'s reasons"}


def main():
    argv = sys.argv[1:]
    if "--rehearsal" in argv:
        STATE["rehearsal"] = os.path.abspath(argv[argv.index("--rehearsal") + 1])
        argv = argv[:argv.index("--rehearsal")]
    out_path = argv[0] if argv else os.path.join(OUT, "c1_tests_v11.json")
    os.makedirs(OUT, exist_ok=True)
    skip = freeze_skip()
    before = real_state()
    assert not before["deposit_record"] and not before["stage_B_log"] and before["run_log_nonexempt_lines"] == 0, \
        "the real tree holds a deposit record, a stage-B log or a non-exempt run-log line (Choice 44c): %s" % before
    if not skip:
        assert not before["hash_log"], "the real tree holds a C1 hash log, and this suite was not run by the freeze with its hash"
    t0 = time.time()
    res, ok = {"tested_files_sha256": {f: G.sha(os.path.join(C1, f)) for f in TESTED}, "python": sys.version, "versions": G.versions(),
               "freeze_skip": skip, "C1_FREEZE_LOG_SHA256": os.environ.get("C1_FREEZE_LOG_SHA256"), "real_tree_before": before}, True
    for name, fn in (("G5", t_g5), ("RUNLOG", t_runlog), ("SWEEP", t_sweep), ("ME", t_me), ("MD", t_md), ("SCENEMAP", t_scenemap), ("FRZ6", t_frz6),
                     ("TREE", t_tree), ("REHEARSAL", t_rehearsal), ("LEGACY", t_legacy)):
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
    after = real_state()
    res["real_tree_after"] = after
    if after != before:
        ok = False
        res["real_tree_changed"] = True
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
