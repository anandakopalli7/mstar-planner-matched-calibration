#!/usr/bin/env python3
"""Tests of C1 code v09 (Claude line, test_c1_v12, 5 Nov 2026): D16 v26 Choice 47 (R20 B1-B3, M2, M3, m13), v27 Choice 48 (R17f M-1,
m-2 to m-6, 48c), v28 Choice 49 (b, c, g, l) and D16 v30 Choice 50, the criteria (c1_rules_v01: ICH E9 5.5 levels,
removal at 1 - 0.025/9, HK1c's level, the target-only power rule), with R17f's probes N1 and N2 as refusal tests, plus every earlier
suite. The ONLY
bound "test" file of README v09 (c1_freeze_v07 runs it); it reads README v09. Synthetic, nuScenes and dummy AV2-TAGGED fixtures only
(R17c's p2 and R17d's fx_av2relab, read only); every post-freeze probe runs in a COPY TREE under 70_TESTS/c1_v01/tests_v12/, so the
real tree never gets a C1 hash log, a deposit record, a stage-B log, a run log, a quarantine folder or a stage-B manifest. No AV2
ground-truth file is opened; the real AV2 files read are tracker exports and the trackers' own horizon files (PROV, hashes only) and the
stage-A counts-only items (PC5).
Real-tree assertions (Choice 44c): before and after, there is no deposit record, no stage-B log and no run-log line from a non-exempt
role; the hash log is absent unless the freeze runs this suite with C1_FREEZE_LOG_SHA256 equal to its SHA-256 (freeze_skip()).
Groups (v11's, re-run against README v09, then the new ones):
  G5, RUNLOG, SWEEP, ME, SCENEMAP  as test_c1_v11 (RUNLOG reads c1_analyse_v09.logged_check).
  MD      as v11 on c1_analyse_v09 (Q1 "not tested"; a q1 config refused in decide_all and main; c1_predarm_v07's QCNet options refused).
  FRZ7    v11's FRZ6 cases on c1_freeze_v07 with README v09 (nuScenes folds), and 48(c): --dry-run passes every check and writes
          nothing (the probe folder is unchanged, file by file).
  GTINV   47(b), 49(b): c1_av2_gt_inventory_v01 in a copy tree: ground-truth files listed with class, producer, deciding code line,
          date and SHA-256; an archive listed by member names (tar headers) only, never extracted, its ground-truth-database logs
          checked against the confirmation logs; identity-only, ego-pose and aggregate files listed as checked and not ground truth;
          a file no rule covers refused (nothing written); the port's file "pending" without --include-port; --include-port refused
          while the file is absent, listing it once present, refused if the port's list names a file the inventory lacks; an existing
          output refused.
  PROV    47(a), 46(d), 48(b) m-2: c1_av2_provenance_v01 on a small AV2-tagged export (R17d's stand-in tracks): the horizon RE-MADE by
          the bound builder av2_horizon_prep_v02 passes; refused (R20 B1): a track input from an unbound tool, a detection input from
          an unbound adapter, a horizon the bound builder does not make, an unbound or missing stage-A builder, a re-made ego or ground
          truth that differs (injected builder runner; the re-made ground truth is deleted unopened), a changed scene.json; the real
          150-log AB3DMOT manifest (exports and worker-order horizon concatenation) and T1 manifest (exports) pass on README v09's
          builders; the CLI writes nothing on failure and its record (written on success only) passes c1_guard_v06's check, which
          refuses a record for another README, a partial record and a record that does not cover a manifest.
  AN9     47(e), 49(c), 47(f), 47(m13), 47(c), 49(l), 48(b) m-5 on c1_analyse_v09, constructed cases: an HK1c-only comparator is
          removed by v08's rule and kept by v09's (with its reasons), flagged comparators are removed by both, M*'s own HK1c
          requirement is unchanged, a status without an HK1c-only comparator gives v08's Form B exactly; H3's set keeps a comparator
          failing only the pooled bound; M*'s simultaneous upper bounds equal k6_analyse_v02.flag's, are labelled approximate and
          are absent for comparators; an all-zero M* family raises under v08's setting and is judged and reported under v09's; h9_label missing or invalid refused (decide_all and main); H9's floor-fail status "does not hold: floor not met"
          with the H9_floor block, "does not hold" with the floor met, "descriptive" under the descriptive label, "not tested" without
          a table; Q1 never among the missing inputs in the H9 exception path.
  PC5     47(i), 49(g): c1_power_counts_v05 part H9 on the 150-log stage-A counts-only items: the primary projection leaves out history
          length (E2 cells only, labelled as overstating power), the 375-log resampling and the history-share sensitivity are
          reported (the family by c1_rules_v01's target-only power rule); part B's stricter comparator rule: failing HK1c alone no
          longer counts as shown invalid, a flag does.
  CRIT    the criteria decision (c1_rules_v01): every constant pinned, one test each (its value; a config stating it equal is accepted,
          stating it differently is refused, at top level and in a "criteria" block); a config with another c, ALPHA_FOR or
          HK1C_LEVEL refused by decide_all and main; the derived levels; the modules the rules build on carry the same values; the
          power rule (vectorised = a plain loop with m_lib_v04._simul on the same draws; nested draws; the size at DELTA is small);
          hk1_rule_criteria's flags at 0.95 for M* and descriptive arms and at 1 - 0.025/9 for comparators, HK1c's bound at 0.995,
          the families from the power rule (2000 datasets; 500 for descriptive arms), M*'s descriptive power and floors; a cell
          flagged at 0.95 but not at 1 - 0.025/9; Form A at 1 - 0.025/4, Form C at 0.975, H3 at 1 - 0.025/|V^J|; H10's B6 flag and
          paired bound at 0.975 and its NI bound at 0.975; H6b at 0.025 on the method stage's p-values; Holm's family S at 0.025;
          c1_predarm_v07's H9 floor by the power rule.
  DEVREPLAY the development replay on the K8 v03 inputs (tests/c1_devreplay_v01.py, run once, about an hour): its record was made by
          the bound c1_rules_v01 and c1_devreplay_v01 with the current constants (D16 v33 Choice 52: the lead compares its values
          with development check v03; no verdict is asserted).
  CRIT (Choice 52): removal at 1 - 0.0125/9, H3's at 1 - 0.0025/3 and its doubled p, Form B at 1 - 0.0125/|V_t|, B = 20000 with
          the power rule's 500 weight rows a prefix independent of B, the C1 run's h9_label "descriptive", the p-value governing
          family S with the bound at the Holm-assigned level reported (and H6b's p-values only), H9's descriptive path without
          "does not hold".
  Q3      49(b): c1_quarantine_v03 in a small copy tree quarantines a 64 MiB tar WHOLE (one gzip member, never unpacked) with peak
          Python memory under 16 MiB (tracemalloc), verifies it streamed, reruns idempotently, and c1_guard_v06's scan finds a plain
          copy by size and hash with the same memory bound.
  TREE    in the copy tree, on the AV2-tagged stand-in, with c1_freeze_v07 and c1_quarantine_v03, every AV2 data role of 47(j)
          (data:port_equiv given twice) and a provenance record made for the probe README:
          v11's cases (freeze refused before the quarantine; R17e E2, E3 and E7 as refusals; PB1; entry:c1_e0 exempt; --amend
          before outcomes; m1, m2, m4; stage B v06; deposit after a stage-B build; amendments after the deposit and after stage B),
          and: quarantine v03 with --gt-inventory (an inventory-only archive quarantined); R17f N1 (a gunzip -k copy inside the
          quarantine folder) refused by the freeze, then removed by the quarantine as a plain copy; any other stray entry there
          refused by both; R17f N2 (an older stage-A folder moved deeper than the search, its ground truth restored) refused, and
          refused again with the ground truth removed while the manifest stays deep; a plain copy of an inventory-only file refused;
          m-6 (no builder_sha256) refused; m-2 (a failed record, a partial record, a record for another README, a record not
          covering a manifest) refused; a missing AV2 data role refused (data:freeze_record included: D16 v32 Choice 51a, with a
          stand-in file in the copy tree); m-3 (the skipped folders named in FROZEN_TESTS); 48(c)
          --dry-run on the tree writes nothing; c1_analyse_v09 on AV2 records the run log.
  REHEARSAL (with --rehearsal <dir>): a second freeze into the rehearsal's log is refused; the rehearsal plan's five blocks appear exactly
          once; Q1 "not tested"; the v09 and criteria blocks are present (constants, levels, M*'s upper bounds and power families);
          Form B's level is 1 - 0.025/|V_t|; the analysis records the flag levels (M* 0.95, comparators 1 - 0.025/9; H3's joint flags
          0.95 and 1 - 0.025/3) and the power datasets (2000; 500 for descriptive arms); the differences from rehearsal150_v08's
          decision are listed (descriptive: the criteria change levels, families and V_t).
  LEGACY  the lead's rule (5 Nov 2026): suites v01-v10 stay skipped where test_c1_v11 already re-ran them. They are skipped because
          the lead's verified rerun of test_c1_v11 (70_TESTS/c1_v01/lead_recheck_v08/c1_tests_v11_lead.json, sha256 50a786c5...) ran
          every one of their groups (each "pass" or "skipped by rule"; checked here), and every file README v08 binds is unchanged on
          disk (checked here, file by file; code v09 adds new files only). test_c1_v11's own groups run in their own process, except
          its LEGACY (v01-v10, as above), FRZ6 (README v08 can no longer be frozen: its entry points are not the latest; FRZ7 replaces
          it) and TREE (it binds c1_freeze_v06 and c1_quarantine_v02, which README v09 supersedes; this suite's TREE re-runs its cases
          on the bound versions).
With --rehearsal <dir>: the REHEARSAL group reads <dir>.
PARALLEL (the lead's speed request, 5 Nov 2026): every group runs in its own worker process (this file --worker <group>), in its own
output folder under 70_TESTS/c1_v01/tests_v12/, with its record and log in tests_v12/parallel/. At most 3 workers run at once (8 logical
cores): G5, RUNLOG, ME, MD, SCENEMAP, FRZ7, GTINV, PROV, AN9, CRIT, DEVREPLAY, PC5, Q3, TREE (its own copy tree) and REHEARSAL,
longest first. SWEEP and
LEGACY then run alone, one after the other: both create a c1_gt_<pid>_* folder for a process that has just ended and expect guard() to
sweep it as stale, and a process spawned at that moment by another group could be given the recycled process ID. The real-tree
assertions and the tested-file hashes are taken once, before and after, in the parent process. The tests and pass criteria are those of
a serial run; --workers 1 runs the pool one group at a time.
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v12.py [<out.json>] [--rehearsal <dir>] [--groups G1,G2] [--workers N<=3]
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
import tarfile
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
import c1_guard_v06 as G6  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v12")
README = os.path.join(C1, "README_C1_CODE_v09.md")
R17C = os.path.join(W, "70_TESTS", "c1_v01", "r17c_probes")
R17D = os.path.join(W, "70_TESTS", "c1_v01", "r17d_probes")
PY = sys.executable
TPP38 = os.path.join(W, "50_CODE", "env", "tpp38", "Scripts", "python.exe")
TPP_ROOT = os.path.join(W, "50_CODE", "third_party", "Trajectron-plus-plus_eccv2020")
CANON = G.CANONICAL["C1"]
TESTED = ["c1_guard_v05.py", "c1_guard_v06.py", "c1_freeze_v07.py", "c1_quarantine_v03.py", "c1_av2_gt_inventory_v01.py", "c1_av2_provenance_v01.py",
          "c1_power_counts_v05.py", "c1_av2_scene_map_v01.py", "c1_tpp_envcheck_v01.py", "c1_analyse_v09.py", "c1_predarm_v07.py", "c1_fit_v06.py",
          "c1_run_v06.py", "c1_mstage_v06.py", "c1_h8_v06.py", "c1_e0_v05.py", "tests/test_c1_v12.py", "../av2/av2_cache_stageB_v06.py",
          "../k8/k8_items_v08.py", "../tpp/tpp_keys_v03.py", "../tpp/tpp_run_v03.py", "../av2/av2_horizon_prep_v02.py", "c1_rules_v01.py",
          "tests/c1_devreplay_v01.py"]
SKIP = {"test_c1_v01": ["GEN"], "test_c1_v02": ["GEN2", "FRZ"], "test_c1_v03": ["GEN3"], "test_c1_v06": ["FRZ3"], "test_c1_v08": ["LEGACY"],
        "test_c1_v09": ["FRZ4"], "test_c1_v10": ["LEGACY", "FRZ5", "TREE"], "test_c1_v11": ["LEGACY", "FRZ6", "TREE"]}
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
    """README v09's rows with the bound test replaced by test_rel (the earlier test file becomes a test_module)."""
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
    import c1_analyse_v09 as A9
    fb = {"met": h1, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False, "pops": {}} for a in A9.A6.REQUIRED_ARMS}
    return {"within_lt3d": {t: {"form_b": fb, "status": st, "form_c": None, "form_a": {}} for t in A9.TRACKERS}}


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


LEAD_V11 = os.path.join(W, "70_TESTS", "c1_v01", "lead_recheck_v08", "c1_tests_v11_lead.json")
LEAD_V11_SHA = "50a786c56c942825eac2e973ed952c529b879598a878dfcd0b9cb2bbf4aaf0bf"
README_V08 = os.path.join(C1, "README_C1_CODE_v08.md")
README_V08_SHA = "5649c170834dc2a5a55c6fa55a30e114f045d5a2c2b1bb2f3080d0477d2ecc78"


def t_legacy():
    """The lead's rule (5 Nov 2026): suites v01-v10 stay skipped where test_c1_v11 already re-ran them. They are skipped here because
    (i) the lead's verified rerun of test_c1_v11 (LEAD_V11, sha256 50a786c5...) ran every one of their groups in its LEGACY group,
    each "pass" or "skipped (by rule)", and (ii) every file README v08 binds is unchanged on disk (checked here, file by file): code
    v09 adds new files only, so those suites would read the same code. test_c1_v11's own groups run in their own process, except its
    LEGACY (v01-v10, as above), FRZ6 (README v08 can no longer be frozen: its entry points are not the latest; FRZ7 replaces it) and
    TREE (it binds c1_freeze_v06 and c1_quarantine_v02, superseded; this suite's TREE re-runs its cases on the bound versions)."""
    out = {}
    assert G.sha(LEAD_V11) == LEAD_V11_SHA, "the lead's verified test_c1_v11 result changed or is missing: %s" % LEAD_V11
    lead = json.load(open(LEAD_V11))
    assert lead["verdict"] == "ALL_PASS" and lead["LEGACY"]["pass"], "the lead's test_c1_v11 run did not pass"
    for i in range(1, 11):
        mod = "test_c1_v%02d" % i
        res = lead["LEGACY"]["result"][mod]
        assert res and all(v == "pass" or v == "skipped (by rule)" for v in res.values()), (mod, res)
        out[mod] = "skipped by the lead's rule: %d groups passed in the lead's test_c1_v11 rerun (%s), %d skipped there by rule" % (
            sum(v == "pass" for v in res.values()), LEAD_V11_SHA[:12], sum(v != "pass" for v in res.values()))
    assert G.sha(README_V08) == README_V08_SHA, "README v08 changed"
    rows = re.findall(r"^([0-9a-f]{64})  (50_CODE/\S+)  (\S+)$", open(README_V08, encoding="utf-8").read(), re.M)
    changed = [p for h, p, _ in rows if G.sha(os.path.join(W, p)) != h]
    assert len(rows) == 154 and not changed, "files bound by README v08 changed: %s" % changed[:5]
    out["README_v08_files_unchanged"] = "%d of %d" % (len(rows), len(rows))
    mod = "test_c1_v11"
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
    import c1_analyse_v09 as A9
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
    okp, missing = A9.logged_check([tab, other], logged)
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
    real = os.path.join(tempfile.gettempdir(), "c1_gt_%d_v12sweep" % dead)
    os.makedirs(real, exist_ok=True)
    assert G.guard("nuscenes", None, "entry:c1_h8", os.path.join(C1, "c1_h8_v06.py")) is None
    assert not os.path.exists(real), "guard() did not sweep a stale folder"
    shutil.rmtree(d, ignore_errors=True)
    return {"swept": "dead pid and old pid-less folders", "kept": "own pid, recent pid-less, unrelated", "guard_sweeps": "yes"}


# ------------------------------------------------------------------------------------------------------------------------------ ME
def t_me():
    import c1_predarm_v07 as P6
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
    out["predarm_v07_wrapper_v06"] = "run(tpp38) passes; the one-scene keys are refused as a --scenes subset (R17c M4) before the version check"

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
    import c1_analyse_v09 as A9
    h9 = {t: {"H9": True, "H9_noHL": True, "arms": {"TPP": {}}, "population": "PD", "H9_seed": {"20261102": True, "20261104": True, "20261105": True}}
          for t in A9.TRACKERS}
    aux0 = {"tables": {"h9": {"ok": True, "data": h9, "checks": {}}}}
    q1tab = {"ok": True, "data": {"t1": {"arms": {"Q1_deployed": {"PD": {}}}}}, "checks": {}}
    keys = ("C1_verdict", "gate_H1", "family_S")
    out = {}
    for h1 in (True, False):
        d8 = A9.decide_all(copy.deepcopy(planted(h1)), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0))
        d7a = A7.decide_all(copy.deepcopy(planted(h1)), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0, q1=q1tab))
        d7b = A7.decide_all(copy.deepcopy(planted(h1)), {"routes": [], "h9_label": "secondary"}, "smoke", dict(aux0, q1=None))
        for dd in (d7a, d7b):
            assert json.dumps({k: d8[k] for k in keys}, sort_keys=True, default=str) == json.dumps({k: dd[k] for k in keys}, sort_keys=True, default=str)
            assert d8["hypotheses"]["H9"] == dd["hypotheses"]["H9"] and d8["claims_status"]["H9"] == dd["claims_status"]["H9"]
        q = d8["hypotheses"]["Q1"]
        assert q["status"] == "not tested" and q["reasons"] == A9.Q1_REASONS and d8["claims_status"]["Q1"] == "not tested" and "Q1" in d8["not_tested"]
        assert "10 Hz matched AB3DMOT" in q["reasons"][0] and "95.7 %" in q["reasons"][1]
        assert not any("Q1" in x for x in d8["missing_inputs"]) and "tables missing" not in json.dumps(q)
        out["gate_%s" % h1] = "C1_verdict, gate_H1, family_S, H9 identical to v07's with and without a Q1 table; Q1 not tested with 44(d)'s reasons"
    m = raises(A9.decide_all, planted(), {"routes": [], "q1": {"t1": "x"}}, "smoke", dict(aux0))
    assert m and "Choice 44d" in m
    d = os.path.join(OUT, "md")
    shutil.rmtree(d, ignore_errors=True)
    cfg = wj(os.path.join(d, "cfg.json"), {"routes": [], "q1": {"t1": "x"}})
    rc, o = sub(["c1_analyse_v09.py", "--config", cfg, "--out", os.path.join(d, "a.json"), "--decision", os.path.join(d, "d.json"), "--smoke"])
    assert rc != 0 and "Choice 44d" in o and not os.path.exists(os.path.join(d, "a.json")), o[-400:]
    out["q1_config"] = "refused (decide_all and main)"
    kp = os.path.join(d, "keys_never_opened.npz")  # the refusal comes before any input is read
    for extra in (["--q1-only"], ["--qcnet-deployed", kp], ["--qcnet-gt-summary", kp]):
        rc, o = sub(["c1_predarm_v07.py", "--keys", kp, "--folds", os.path.join(d, "none.json"), "--tracker-index", "0", "--out",
                     os.path.join(d, "pa.json"), "--synthetic"] + extra)
        assert rc != 0 and "Choice 44d" in o, o[-400:]
    out["predarm_v07_qcnet"] = "refused (--q1-only, --qcnet-deployed, --qcnet-gt-summary)"
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


# ------------------------------------------------------------------------------------------------------------------------------ FRZ7
def t_frz7():
    d = os.path.join(OUT, "frz7")
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
        return (["c1_freeze_v07.py", "--plan", plan, "--readme", readme, "--results-dir", os.path.join(d, "results"), "--folds", fo, "--split", split,
                 "--transfer-fits", os.path.join(TF, "c1_transfer_fits_t1_v01.json"), os.path.join(TF, "c1_transfer_fits_t3_v01.json"),
                 "--stageA-manifests"] + man + ["--config", config, "--folds-val150", folds150, "--folds-train225", t225, "--hash-log", log,
                                               "--data-root", droot, "--test-out-dir", os.path.join(d, "tests_out"), "--data"] + list(data) + list(extra))
    tmpl = "# probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n"

    def plan(k, body=None):
        q = os.path.join(d, "PLAN_%s.md" % k)
        open(q, "w").write(body or tmpl % k)
        return q
    out, log = {}, os.path.join(d, "LOG.txt")
    p0 = plan(0)
    lt = listing(d)
    rc, o = sub(args(p0, rp, log, ["--dry-run"]))
    assert rc == 0 and "C1 FREEZE V07 DRY RUN" in o and "nothing written" in o, o[-1500:]
    assert listing(d) == lt and not os.path.exists(log), "the dry run wrote something"
    out["48c_dry_run"] = "every check passed (the bound tests are not run); nothing written: no plan change, sidecar, log line, test or results"
    p1 = plan(1)
    rc, o = sub(args(p1, rp, log))
    assert rc == 0 and "C1 FREEZE V07 DONE" in o, o[-1500:]
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
    assert rc == 0 and "C1 FREEZE V07 DONE" in o, o[-1500:]
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


# ------------------------------------------------------------------------------------------------------------------------------ v12 helpers
STAGEA_BUILDER = "50_CODE/av2/av2_cache_stageA_v02.py"
AV2_ROLES = ("s20a", "s22", "logs375", "rule0_metrics", "port_equiv")
UB_KEY = "descriptive_simultaneous_ub_0.95"


def listing(root):
    """{relative path: (size, mtime_ns)} of every file under root (shows that a dry run wrote nothing)."""
    out = {}
    for dp, dn, fn in os.walk(root):
        for f in fn:
            p = os.path.join(dp, f)
            st = os.stat(p)
            out[os.path.relpath(p, root)] = (st.st_size, st.st_mtime_ns)
    return out


def rel_to(p, root):
    return os.path.relpath(os.path.abspath(p), root).replace(os.sep, "/")


def inventory_fixture(path, files, root):
    """A GT inventory in c1_av2_gt_inventory_v01's format (the fields c1_guard_v06.inventory_files and the quarantine read)."""
    return wj(path, {"tool": "c1_av2_gt_inventory_v01", "files": [{"path": rel_to(p, root), "sha256": G.sha(p), "bytes": os.path.getsize(p),
                                                                   "content_class": "ground truth", "rule": "test v12 fixture"} for p in files],
                     "pending": [], "note": "test v12 fixture inventory (synthetic files)"})


def tar_fixture(path, members):
    import io
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with tarfile.open(path, "w") as tf:
        for name, data in members:
            if data is None:
                ti = tarfile.TarInfo(name)
                ti.type, ti.mtime = tarfile.DIRTYPE, 0
                tf.addfile(ti)
                continue
            ti = tarfile.TarInfo(name)
            ti.size, ti.mtime = len(data), 0
            tf.addfile(ti, io.BytesIO(data))
    return path


def gz_sha_file(p):
    h = hashlib.sha256()
    with gzip.open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


# ------------------------------------------------------------------------------------------------------------------------------ GTINV
def t_gtinv():
    TG = os.path.join(OUT, "gtinv_tree")
    shutil.rmtree(TG, ignore_errors=True)
    tool = os.path.join(TG, "50_CODE", "c1_av2", "c1_av2_gt_inventory_v01.py")
    os.makedirs(os.path.dirname(tool))
    shutil.copy2(os.path.join(C1, "c1_av2_gt_inventory_v01.py"), tool)
    D = lambda *a: os.path.join(TG, *a)  # noqa: E731

    def put(p, data):
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, "wb").write(data)
        return p
    gt = put(D("30_DATA", "av2_trk_v01", "gt", "av2_val_gt_v01.json"), b'{"synthetic": "test v12, not AV2"}')
    qn = put(D("30_DATA", "qcnet_av2_v01", "qcnet_av2_gt_v01.npz"), os.urandom(2048))
    tar = tar_fixture(D("30_DATA", "av2_det_owncp_v01", "train_progress", "infos_archive_v01b.tar"),
                      [("train_progress/av2_infos_train475.pkl", os.urandom(1000)), ("train_progress/av2_gt_database", None),
                       ("train_progress/av2_gt_database/0a1b2c3d_car_1.bin", os.urandom(700)),
                       ("train_progress/av2_gt_database/9e9e9e9e_pedestrian_2.bin", os.urandom(500))])
    os.makedirs(D("30_DATA", "av2_val", "0a1b2c3d"))  # a confirmation log (empty folder)
    put(D("30_DATA", "av2_cache_stageA_v01", "av2_ego10hz_v01.json.gz"), gzip.compress(b"{}", mtime=0))
    put(D("30_DATA", "qcnet_av2_v01", "join2hz_t1_v01.npz"), os.urandom(300))
    put(D("60_RESULTS", "av2_trk", "metrics", "m.json"), b"{}")
    before = listing(TG)
    out, o1, x1 = {}, D("out", "inv1.json"), D("out", "inv1_extra.txt")
    rc, o = sub([tool, "--out", o1, "--extra-list", x1], cwd=os.path.dirname(tool))
    assert rc == 0 and "C1 GT INVENTORY V01 DONE" in o, o[-1500:]
    inv = json.load(open(o1))
    paths = sorted(f["path"] for f in inv["files"])
    assert paths == sorted(rel_to(p, TG) for p in (gt, qn, tar)), paths
    for f in inv["files"]:
        assert f["content_class"] == "ground truth" and f["sha256"] == G.sha(D(*f["path"].split("/"))) and f["deciding_code"] and f["producer"]
        assert re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", f["date_utc"]) and f["bytes"] == os.path.getsize(D(*f["path"].split("/")))
    am = [f for f in inv["files"] if f["path"].endswith(".tar")][0]["archive_members"]
    assert am["members"] == 4 and am["gt_database_files"] == 2 and am["gt_database_logs_among_the_375"] == ["0a1b2c3d"], am
    assert am["infos_of_the_375_present"] == [] and "never extracted" in am["listing"]
    cl = {r["content_class"] for r in inv["checked_not_listed"] if r["files"]}
    assert {"ego poses", "identity only", "aggregate"} <= cl, cl
    assert len(inv["pending"]) == 1 and inv["pending"][0]["status"].startswith("pending") and inv["pending"][0]["expected_path"].endswith("av2_c1_gt375_v01.json")
    assert open(x1).read().splitlines() == paths and inv["excluded_areas"] and inv["unclassified_name_matches"] == []
    after = listing(TG)
    assert {k for k in after if k not in before} == {os.path.join("out", "inv1.json"), os.path.join("out", "inv1_extra.txt")}, \
        "the tool wrote or extracted something else"
    out["listed"] = "3 ground-truth files with class, producer, deciding code, date and SHA-256; the archive by member names (4), never " \
                    "extracted; 1 database log among the confirmation logs found; ego, identity-only and aggregate files checked, not listed"
    out["pending"] = "the port's 375-log file listed as pending by its expected path"
    rc, o = sub([tool, "--out", o1], cwd=os.path.dirname(tool))
    assert rc != 0 and "never overwritten" in o
    for name, rp in (("name_gt", ("60_RESULTS", "stray", "my_gt_copy.json")), ("pickle", ("30_DATA", "misc", "infos_extra.pkl"))):
        p = put(D(*rp), b"x" * 10)
        o2 = D("out", "inv_%s.json" % name)
        rc, o = sub([tool, "--out", o2], cwd=os.path.dirname(tool))
        assert rc != 0 and "files that no rule covers" in o and not os.path.exists(o2) and not os.path.exists(o2 + ".partial"), (name, o[-500:])
        os.remove(p)
        out["uncovered_" + name] = "refused, nothing written"
    o3 = D("out", "inv_port.json")
    rc, o = sub([tool, "--out", o3, "--include-port"], cwd=os.path.dirname(tool))
    assert rc != 0 and "does not exist" in o and not os.path.exists(o3), o[-400:]
    port = put(D("30_DATA", "av2_trk_v02", "gt", "av2_c1_gt375_v01.json"), b'{"synthetic port table": 1}')
    lst = D("30_DATA", "av2_trk_v02", "GT_FILES_FOR_QUARANTINE_v01.txt")
    open(lst, "w").write("# the port's list\n%s  %s\n" % (G.sha(port), rel_to(port, TG)))
    rc, o = sub([tool, "--out", o3, "--include-port"], cwd=os.path.dirname(tool))
    assert rc == 0, o[-800:]
    inv3 = json.load(open(o3))
    assert rel_to(port, TG) in [f["path"] for f in inv3["files"]] and inv3["pending"] == [] and inv3["include_port"] is True
    open(lst, "a").write("%s  30_DATA/av2_trk_v02/gt/another_table.json\n" % ("0" * 64))
    o4 = D("out", "inv_port2.json")
    rc, o = sub([tool, "--out", o4, "--include-port"], cwd=os.path.dirname(tool))
    assert rc != 0 and "which the inventory does not list" in o and not os.path.exists(o4), o[-400:]
    out["include_port"] = "refused while the file is absent; listed once present (pending empty); refused when the port's list names a file " \
                          "the inventory lacks; an existing output refused"
    reals = [p for p in (os.path.join(W, "40_PROTOCOL", "C1_GT_INVENTORY_v02.json"), os.path.join(W, "40_PROTOCOL", "C1_GT_INVENTORY_v01.json"))
             if os.path.exists(p)]
    if reals:
        real = reals[0]
        inv_r = json.load(open(real))
        rf = G6.inventory_files(real)
        tars = [f for f in inv_r["files"] if f["path"].endswith("infos_archive_v01b.tar")]
        assert tars and tars[0]["bytes"] == 2838906880 and tars[0].get("archive_members"), "the real inventory lacks the archive"
        assert not inv_r["unclassified_name_matches"]
        if inv_r.get("include_port"):
            assert "30_DATA/av2_trk_v02/gt/av2_c1_gt375_v01.json" in [f["path"] for f in rf] and not inv_r["pending"]
        out["real_inventory"] = "%s: %d files, read by c1_guard_v06.inventory_files; the archive listed (2,838,906,880 B); port included: %s" % (
            os.path.basename(real), len(rf), bool(inv_r.get("include_port")))
    shutil.rmtree(TG, ignore_errors=True)
    return out


# ------------------------------------------------------------------------------------------------------------------------------ PROV
def t_prov():
    import c1_av2_provenance_v01 as PV
    d = os.path.join(OUT, "prov")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    bound = PV.bound_builders(README)
    src = os.path.join(R17D, "fx_av2relab", "worker0")
    rec0 = json.load(open(os.path.join(src, "x1_export_record.json")))
    exp = rec0["resolved_config"]["experiment_id"]
    out = {}

    def make_worker(name, harness="av2_track_v02", adapter="av2_tracker_input_v02", n=3000):
        w = os.path.join(d, name, "worker0")
        os.makedirs(w)
        tp = os.path.join(w, "x1_tracks.jsonl.gz")
        with gzip.open(os.path.join(src, "x1_tracks.jsonl.gz"), "rb") as fi, open(tp, "wb") as raw:
            with gzip.GzipFile(filename="x1_tracks.jsonl", mode="wb", fileobj=raw, mtime=0) as fo:
                for k, line in enumerate(fi):
                    if k >= n:
                        break
                    fo.write(line)
        det = wj(os.path.join(d, name, "det", "dets.json"), {"fixture": "test v12"})
        wj(os.path.join(d, name, "det", "receipt.json"), {"adapter": adapter})
        rec = copy.deepcopy(rec0)
        rec.update({"harness_version": "%s (test v12 fixture: R17d's stand-in tracks, not AV2)" % harness,
                    "argv": [os.path.join(W, "50_CODE", "av2", harness + ".py")], "output_sha256": {"x1_tracks.jsonl.gz": G.sha(tp)},
                    "dataset": "av2_sensor_val_train"})
        rec["provenance"] = dict(rec["provenance"], detection_path=det)
        wj(os.path.join(w, "x1_export_record.json"), rec)
        return w

    def manifest(name, w, hz, builder="bound", **extra):
        i = {"workers": [w], "export_sha256": [G.sha(os.path.join(w, "x1_tracks.jsonl.gz"))], "horizon": hz, "horizon_sha256": G.sha(hz)}
        if builder:
            i["builder_sha256"] = bound[STAGEA_BUILDER] if builder == "bound" else builder
        i.update(extra)
        return wj(os.path.join(d, name, "stageA", "MANIFEST.json"), {"stage": "A", "dataset": "av2", "experiment": exp, "scenes": {}, "inputs": i})
    w = make_worker("ok")
    hz = os.path.join(d, "ok", "horizon.jsonl.gz")
    r = subprocess.run([PY, "-I", "-B", os.path.join(W, PV.HORIZON), "--experiment", exp, "--workers", w, "--out", hz, "--propagate-only",
                        "--allow-av2-propagation"], capture_output=True, text=True, cwd=d)
    assert r.returncode == 0 and "HORIZON PREP DONE" in r.stdout, r.stdout[-500:] + r.stderr[-800:]
    m_ok = manifest("ok", w, hz)
    k2 = ("exports", "horizon", "scene_json")
    rec = PV.run([m_ok], README, kinds=k2)
    mi = rec["manifests"][G.rel(m_ok)]["inputs"]
    assert rec["status"] == "PASS" and mi["horizon"]["method"] == "re-made" and mi["horizon"]["producer"]["tool"] == PV.HORIZON
    assert mi["exports"][0]["producer"]["tool"] == "50_CODE/av2/av2_track_v02.py" and mi["exports"][0]["detection_adapter"]["tool"] == "50_CODE/av2/av2_tracker_input_v02.py"
    out["horizon_re_made"] = "the bound av2_horizon_prep_v02 re-makes the horizon from the bound export (decompressed SHA-256 equal); the " \
                             "export's tool av2_track_v02 and its detection adapter av2_tracker_input_v02 are bound builders"
    refusals = {}
    m = manifest("unbound_track", make_worker("unbound_track", harness="av2_note_tables_v01"), hz)
    refusals["track_input_from_unbound_tool"] = (m, ("exports",), "not a bound builder")
    m = manifest("unbound_adapter", make_worker("unbound_adapter", adapter="av2_note_tables_v02"), hz)
    refusals["detection_input_from_unbound_adapter"] = (m, ("exports",), "not a bound builder")
    hz_bad = os.path.join(d, "bad_horizon.jsonl.gz")
    with gzip.open(hz, "rb") as fi:
        lines = fi.read().splitlines(True)
    with open(hz_bad, "wb") as raw:
        with gzip.GzipFile(filename="h", mode="wb", fileobj=raw, mtime=0) as fo:
            fo.write(b"".join(lines[:-1]))
    refusals["horizon_not_made_by_the_bound_builder"] = (manifest("bad_horizon", w, hz_bad), k2, "is not what the bound builder")
    refusals["unbound_stage_A_builder"] = (manifest("bad_builder", w, hz, builder="0" * 64), ("exports",), "not a bound builder")
    refusals["no_builder_sha256"] = (manifest("no_builder", w, hz, builder=None), ("exports",), "records no builder_sha256")
    sj = wj(os.path.join(d, "scene.json"), [{"name": "u1", "log_token": "u1"}])
    refusals["scene_json_changed"] = (manifest("bad_scene_json", w, hz, scene_json=sj, scene_json_sha256="0" * 64), ("scene_json",), "scene.json differs")
    for name, (mp, kinds, msg) in refusals.items():
        e = raises(PV.run, [mp], README, kinds=kinds)
        assert e and msg in e, (name, e)
        out["refused_" + name] = "refused"
    # ego and ground truth: an injected runner stands in for the bound builders (they read AV2 annotations); the comparison and the
    # deletion of the re-made ground truth are the tool's own code
    eg = os.path.join(d, "eg")
    ego = os.path.join(eg, "ego.json.gz")
    os.makedirs(eg)
    open(ego, "wb").write(gzip.compress(json.dumps({"log": {"t": [0.0], "x": [1.0], "y": [2.0], "yaw": [0.0]}}).encode(), mtime=0))
    gtf = os.path.join(eg, "gt.json")
    open(gtf, "wb").write(b'{"synthetic ground truth": "test v12, not AV2"}')
    m6 = manifest("full", w, hz, ego=ego, ego_sha256=G.sha(ego), gt=gtf, gt_sha256=G.sha(gtf), scene_json=sj, scene_json_sha256=G.sha(sj))
    made = []

    def runner_same(kind, m, bnd, tmpd, logs_file):
        tool = {"horizon": PV.HORIZON, "ego": PV.EGO, "gt": PV.GT}[kind]
        src_ = m["inputs"][kind]
        dst = os.path.join(tmpd, os.path.basename(src_))
        if kind == "ego":   # a re-made gzip differs in its header; the tool compares the decompressed bytes
            open(dst, "wb").write(gzip.compress(gzip.open(src_, "rb").read(), mtime=12345))
        else:
            shutil.copy2(src_, dst)
        made.append(dst)
        return dst, PV.require_builder(tool, bnd, kind)

    def runner_diff(kind, m, bnd, tmpd, logs_file):
        dst, prod = runner_same(kind, m, bnd, tmpd, logs_file)
        if kind in KIND_DIFF:
            open(dst, "wb").write(gzip.compress(b"{}", mtime=0) if kind == "ego" else b"{}")
        return dst, prod
    rec6 = PV.run([m6], README, runner=runner_same)
    i6 = rec6["manifests"][G.rel(m6)]["inputs"]
    assert set(rec6["kinds"]) == set(G6.PROVENANCE_KINDS) and i6["gt"]["method"].startswith("re-made, hashed, deleted")
    assert not any(os.path.exists(p) for p in made), "a re-made file was left behind"
    assert all(not os.path.abspath(p).startswith(os.path.abspath(W)) for p in made), "a re-made file lay inside the workspace"
    out["ego_gt_reproduced"] = "pass; the re-made files lay outside the workspace and are gone (the ground truth deleted unopened)"
    for kind in ("ego", "gt"):
        KIND_DIFF[:] = [kind]
        e = raises(PV.run, [m6], README, runner=runner_diff)
        assert e and "is not what the bound builder" in e, (kind, e)
        out["refused_re_made_%s_differs" % kind] = "refused"
    KIND_DIFF[:] = []
    for name, kinds in (("cache_stageA_ab3dmot_lt3d", ("exports", "horizon")), ("cache_stageA_t1_lt3d", ("exports",))):
        mp = os.path.join(W, "30_DATA", "av2_cache_stageA_v01", name, "MANIFEST.json")
        t0 = time.time()
        rr = PV.run([mp], README, kinds=kinds)
        ri = rr["manifests"][G.rel(mp)]["inputs"]
        out["real_" + name] = "pass (%s; %d exports, tools %s; %.0f s)" % (
            ", ".join(kinds), len(ri["exports"]), sorted({e_["producer"]["tool"].split("/")[-1] for e_ in ri["exports"]}), time.time() - t0)
        if "horizon" in kinds:
            assert ri["horizon"]["method"].startswith("concatenation")
    tool = os.path.join(C1, "c1_av2_provenance_v01.py")
    o_fail = os.path.join(d, "cli_fail.json")
    rc, o = sub([tool, "--readme", README, "--stageA-manifests", refusals["track_input_from_unbound_tool"][0], "--out", o_fail])
    assert rc != 0 and "not a bound builder" in o and not os.path.exists(o_fail) and not os.path.exists(o_fail + ".partial"), o[-500:]
    out["cli_failure_writes_nothing"] = "exit non-zero; no record, no partial file"
    o_ok = os.path.join(d, "cli_ok.json")
    defaults = PV.run.__defaults__
    try:
        PV.run.__defaults__ = (None, runner_same, defaults[2])
        PV.main(["--readme", README, "--stageA-manifests", m6, "--out", o_ok])
    finally:
        PV.run.__defaults__ = defaults
    chk = G6.provenance_record_check(o_ok, README, [m6])
    assert chk["manifests"] == 1 and not os.path.exists(o_ok + ".partial")
    e = raises(PV.main, ["--readme", README, "--stageA-manifests", m6, "--out", o_ok])
    assert e and "never overwritten" in e
    other = wj(os.path.join(d, "README_other.md"), {"x": 1})
    for name, path, args, msg in (("another_readme", o_ok, (other, [m6]), "made for another README"),
                                  ("not_covering", o_ok, (README, [m6, m_ok]), "does not cover"),
                                  ("partial_kinds", wj(os.path.join(d, "partial.json"), dict(rec, kinds=["exports"])), (README, [m_ok]), "made without the checks"),
                                  ("failed", wj(os.path.join(d, "failed.json"), dict(rec6, ok=False, status="FAIL")), (README, [m6]), "not a success record")):
        e = raises(G6.provenance_record_check, path, *args)
        assert e and msg in e, (name, e)
        out["record_check_refuses_" + name] = "refused"
    out["cli_success"] = "the record is written (through a temporary name) only on success, and passes c1_guard_v06's check"
    return out


KIND_DIFF = []


# ------------------------------------------------------------------------------------------------------------------------------ AN9
def an9_pop(flagged=(), fam_flagged=(), pooled_flag=False, hk1c=True, fam=8, ev=10, pooled=True):
    return {"flagged": list(flagged), "family_flagged": list(fam_flagged), "family_size": fam, "evaluable": ev,
            "pooled": ({"flagged": pooled_flag, "HK1c_ub_le_delta_plus_0.03": hk1c} if pooled else None)}


def t_an9():
    import c1_analyse_v03 as A3
    import c1_analyse_v07 as A7
    import c1_analyse_v09 as A9
    B, K, A = A9.B, A9.K, A9.A_
    P0, P1, P2 = B.POPS
    rng = np.random.default_rng(20261105)
    out = {}
    # ---- 47(e): V_t, constructed
    spec = {"Mstar": {}, "B0": {P0: {"hk1c": False}}, "B1": {P1: {"flagged": ["c1"]}}, "B3": {P2: {"pooled_flag": True}},
            "B4": {P0: {"fam_flagged": ["c2"]}}, "B6": {P0: {"fam": 2}}, "B9": {}, "RETUNED": {P2: {"hk1c": False}, P1: {"fam": 2}}}
    v = {a: {"pops": {p: an9_pop(**s.get(p, {})) for p in B.POPS}} for a, s in spec.items()}
    nl = 30
    rate = {a: rng.uniform(0.05, 0.15, nl) + (0.0 if a == "Mstar" else 0.05) for a in spec}
    Ws = rng.multinomial(nl, [1.0 / nl] * nl, size=400).astype(float)
    st8 = {a: A9._ARM_STATUS_V02(x) for a, x in v.items()}
    st9 = {a: A9.arm_status_v09(x) for a, x in v.items()}
    old, new = A3.form_b(st8, rate, Ws), A9.form_b(st9, rate, Ws)
    assert old["V"] == ["B6", "B9"] and new["V"] == ["B0", "B6", "B9", "RETUNED"], (old["V"], new["V"])
    assert new["in_V_hk1c_only"] == ["B0", "RETUNED"] and new["comparator_reasons"]["B0"]["stays_because"].startswith("HK1c only")
    for c, word in (("B1", "cell flagged"), ("B3", "pooled cell flagged"), ("B4", "family cell flagged")):
        assert not new["comparator_reasons"][c]["in_V_t"] and any(word in x for x in new["comparator_reasons"][c]["removed_by"]), c
    assert new["valid_method"] and old["valid_method"]
    out["47e_V_t"] = "v08's rule: V_t = %s; v09's: %s (B0 and RETUNED fail HK1c without a flag: kept, with reasons); B1, B3, B4 " \
                     "(flagged cell, pooled cell, family cell) removed by both" % (old["V"], new["V"])
    vm = dict(v, Mstar={"pops": {p: an9_pop(hk1c=(p != P2)) for p in B.POPS}})
    nm = A9.form_b({a: A9.arm_status_v09(x) for a, x in vm.items()}, rate, Ws)
    assert nm["valid_method"] is False and nm["met"] is False
    out["47e_Mstar_HK1c_unchanged"] = "M* failing only HK1c is not valid (Form B not met), as in v08"
    vs = dict(v, B0={"pops": {p: an9_pop() for p in B.POPS}}, RETUNED={"pops": {p: an9_pop() for p in B.POPS}})
    o8 = A3.form_b({a: A9._ARM_STATUS_V02(x) for a, x in vs.items()}, rate, Ws, alpha=A9.R.ALPHA_FORM_B)
    o9 = A9.form_b({a: A9.arm_status_v09(x) for a, x in vs.items()}, rate, Ws)
    for k in o8:
        if k != "rule":
            assert json.dumps(o8[k], sort_keys=True) == json.dumps(o9[k], sort_keys=True), k
    assert abs(o9["level"] - (1 - 0.0125 / len(o9["V"]))) < 1e-15 and o9["alpha"] == 0.0125
    out["47e_no_hk1c_only"] = "without an HK1c-only comparator, v09's Form B equals v08's (at the same alpha) in every key; its default alpha is "                               "ALPHA_FORM_B = 0.0125: level 1 - 0.0125/|V_t| (D16 v33 Choice 52c)"
    # ---- 49(c): H3's V^J
    def jv(**kw):
        base = {"E": 0.03, "evaluable": True, "flagged": False, "ub_le_delta_plus_0.03": True, "lb_one_sided_0.95": 0.01, "ub_one_sided_0.95": 0.06}
        return {"pops": {p: dict(base, **kw.get(p, {})) for p in B.POPS}}
    jspec = {"MstarJx": jv(), "Mstar": jv(**{P2: {"ub_le_delta_plus_0.03": False}}), "B0": jv(**{P0: {"flagged": True}}),
             "B1": jv(**{P1: {"evaluable": False}}), "B3": jv(), "B4": jv(), "B6": jv(), "B9": jv(), "RETUNED": jv()}
    js = {a: A3.joint_status(x) for a, x in jspec.items()}
    rj = {a: rng.uniform(0.05, 0.15, nl) + (0.0 if a == "MstarJx" else 0.05) for a in jspec}
    j8, j9 = A3.joint_b(js, rj, Ws), A9.joint_b(js, rj, Ws)
    assert "Mstar" not in j8["VJ"] and "Mstar" in j9["VJ"] and j9["VJ_hk1c_only"] == ["Mstar"], (j8["VJ"], j9["VJ"])
    assert "B0" not in j9["VJ"] and "B1" not in j9["VJ"] and j9["comparator_reasons"]["Mstar"].startswith("pooled bound only")
    out["49c_VJ"] = "v08's V^J = %s; v09's = %s (M* fails only the pooled bound: kept); B0 flagged and B1 not evaluable removed by both" % (j8["VJ"], j9["VJ"])
    # ---- 47(f) and m13: hk1_rule on a constructed table
    A9.configure_v09("c1")
    n_ep, n_c = 60, 5
    sc = np.array(["s%02d" % i for i in range(n_ep)])
    lg = np.array(["l%02d" % (i % 12) for i in range(n_ep)])
    cells = [("cell%d" % j, None) for j in range(n_c)]
    Wb = rng.multinomial(n_ep, [1.0 / n_ep] * n_ep, size=300).astype(float)
    T = {}
    for p in K.CONF_POPS:
        N = rng.integers(20, 40, size=(n_ep, n_c)).astype(float)
        T[p] = (N, rng.binomial(N.astype(int), 0.03).astype(float))
    fams = {p: np.ones(n_c, bool) for p in K.CONF_POPS}
    Rm = A9.R
    assert K.hk1_rule is Rm.hk1_rule_criteria
    got = Rm.hk1_rule_criteria(T, cells, sc, lg, Wb, (1, 2), fams=fams, arm="Mstar")
    one = np.ones((1, n_ep))
    for p in K.CONF_POPS:
        N, X = T[p]
        fam = np.flatnonzero(A.evaluable(N, sc, lg))
        _, ub, _, _, _ = A.flag(A.rates(N, X, one)[0], A.rates(N, X, Wb), fam, 0.95)
        g = got[UB_KEY]["pops"][p]
        assert g["evaluable"] == len(fam) == n_c and all(abs(g["cells"][cells[j][0]] - ub[i]) < 1e-12 for i, j in enumerate(fam))
        assert abs(g["max_ub"] - float(np.max(ub))) < 1e-12
    assert UB_KEY not in Rm.hk1_rule_criteria(T, cells, sc, lg, Wb, (1, 2), fams=fams, arm="B0")
    assert Rm.UB_APPROX_LABEL in got[UB_KEY]["label"]
    st = A9.arm_status_v09(got)
    dec = A9.add_v09_blocks({"hypotheses": {}, "claims_status": {}, "missing_inputs": []}, {"within_lt3d": {"t1": {"status": {"Mstar": st}, "form_b": {}}}})
    assert dec["Mstar_simultaneous_upper_bounds"]["by_route"]["within_lt3d"]["t1"][P0]["max_ub"] == got[UB_KEY]["pops"][P0]["max_ub"]
    out["47f_upper_bounds"] = "equal k6_analyse_v02.flag's simultaneous one-sided 95 % upper bounds, max = largest, labelled approximate; " \
                              "absent for a comparator; reported in the decision"
    T0 = dict(T)
    T0[P2] = (T[P2][0], np.zeros_like(T[P2][1]))
    K.STRICT_Q = True
    e = raises(Rm.hk1_rule_criteria, T0, cells, sc, lg, Wb, (1, 2), fams=fams, arm="Mstar")
    assert e and "non-finite" in e, e
    A9.configure_v09("c1")
    assert K.STRICT_Q is False
    z = Rm.hk1_rule_criteria(T0, cells, sc, lg, Wb, (1, 2), fams=fams, arm="Mstar")
    assert any(x.startswith(P2) for x in z["zero_se_quantiles"]) and z["pops"][P2]["flagged"] == []
    stz = A9.arm_status_v09(z)
    dz = A9.add_v09_blocks({"hypotheses": {}, "claims_status": {}, "missing_inputs": []}, {"within_lt3d": {"t1": {"status": {"Mstar": stz}, "form_b": {}}}})
    assert dz["Mstar_zero_se_families"]["within_lt3d"]["t1"]["families"] == z["zero_se_quantiles"]
    out["m13_zero_se"] = "an all-zero M* population raises under v08's setting (STRICT_Q); under v09's it is judged by E-hat > delta " \
                         "(no cell flagged) and reported: %s" % z["zero_se_quantiles"]
    # ---- 47(c): h9_label
    for cfg_, msg in (({"routes": []}, "no h9_label"), ({"routes": [], "h9_label": "primary"}, "h9_label must be one of")):
        e = raises(A9.decide_all, planted(), cfg_, "smoke", {"tables": {}})
        assert e and msg in e, e
    d = os.path.join(OUT, "an9")
    shutil.rmtree(d, ignore_errors=True)
    cfg = wj(os.path.join(d, "cfg_no_label.json"), {"routes": []})
    rc, o = sub(["c1_analyse_v09.py", "--config", cfg, "--out", os.path.join(d, "a.json"), "--decision", os.path.join(d, "d.json"), "--smoke"])
    assert rc != 0 and "no h9_label" in o and not os.path.exists(os.path.join(d, "a.json")), o[-400:]
    out["47c_h9_label"] = "a missing or other label refused (decide_all and main); no default"
    # ---- 47(c), 49(l): H9's status when the floor fails
    seeds = {"20261102": False, "20261104": False, "20261105": False}

    def h9tab(fe2, h9):
        return {"ok": True, "checks": {}, "data": {t: {"H9": h9, "H9_noHL": h9, "population": "PD", "H9_seed": seeds,
                                                       "arms": {"TPP": {"PD": {"HL": {"H9": h9, "family_size_E2": fe2[t], "floor": 6}}}}}
                                                   for t in A9.TRACKERS}}
    sec = {"routes": [], "h9_label": "secondary"}
    da = A9.decide_all(planted(), sec, "smoke", {"tables": {"h9": h9tab({"t1": 2, "t3": 7}, False)}})
    want = "floor not met (condition a: >= 6 power-qualified E2 cells): t1 family_size_E2 = 2 < 6"
    assert da["claims_status"]["H9"] == "does not hold: floor not met" == da["hypotheses"]["H9"]["status"], da["claims_status"]["H9"]
    assert want in da["hypotheses"]["H9"]["reasons"] and da["H9_floor"]["by_tracker"]["t1"]["floor_met"] is False
    assert da["H9_floor"]["by_tracker"]["t3"] == {"family_size_E2": 7, "floor": 6, "floor_met": True}
    d7 = A7.decide_all(planted(), sec, "smoke", {"tables": {"h9": h9tab({"t1": 2, "t3": 7}, False)}, "q1": None})
    assert d7["claims_status"]["H9"] == "does not hold"
    for k in ("C1_verdict", "gate_H1", "family_S"):
        assert json.dumps(da[k], sort_keys=True, default=str) == json.dumps(d7[k], sort_keys=True, default=str), k
    db = A9.decide_all(planted(), sec, "smoke", {"tables": {"h9": h9tab({"t1": 7, "t3": 8}, False)}})
    dc = A9.decide_all(planted(), sec, "smoke", {"tables": {"h9": h9tab({"t1": 7, "t3": 8}, True)}})
    dd = A9.decide_all(planted(), {"routes": [], "h9_label": "descriptive"}, "smoke", {"tables": {"h9": h9tab({"t1": 2, "t3": 2}, False)}})
    de = A9.decide_all(planted(), sec, "smoke", {"tables": {}})
    assert db["claims_status"]["H9"] == "does not hold" and dc["claims_status"]["H9"] == "holds"
    assert dd["claims_status"]["H9"] == "descriptive" and de["claims_status"]["H9"] == "not tested"
    out["49l_H9_status"] = {"floor fails on t1 (2 < 6)": da["claims_status"]["H9"], "reason": want, "floor met, H9 false": db["claims_status"]["H9"],
                            "floor met, H9 true": dc["claims_status"]["H9"], "descriptive label": dd["claims_status"]["H9"],
                            "no table": de["claims_status"]["H9"], "other keys": "C1_verdict, gate_H1, family_S equal v08's"}
    # ---- 48(b) m-5: the H9 exception path
    bad = {"ok": True, "checks": {}, "data": {t: {"H9": True} for t in A9.TRACKERS}}
    d6 = A9.add_q1_not_tested(A9.A6.decide_all(planted(), sec, "smoke", {"tables": {"h9": bad}}))
    dm = A9.decide_all(planted(), sec, "smoke", {"tables": {"h9": bad}})
    assert not any(str(x).startswith("Q1") for x in dm["missing_inputs"]) and dm["claims_status"]["Q1"] == "not tested"
    out["m5_Q1"] = "the H9 exception path: v08's path lists %d Q1 line(s) among the missing inputs, v09's none; Q1 stays not tested" % \
                   sum(str(x).startswith("Q1") for x in d6["missing_inputs"])
    return out


# ------------------------------------------------------------------------------------------------------------------------------ CRIT
# D16 v30 Choice 50 (the criteria): every constant pinned (one test each), the levels, the power rule, the forms, H6b, H10,
# Holm, H3's V^J, the config refusal, the predictor arm's H9 floor
PINNED = {"ALPHA_AGAINST": 0.05, "ALPHA_FOR": 0.025, "ALPHA_REMOVAL": 0.0125, "ALPHA_FORM_B": 0.0125, "ALPHA_REMOVAL_VJ": 0.0025,
          "H3_P_MULTIPLIER": 2, "H9_LABEL_C1": "descriptive", "N_REMOVAL_V": 9, "N_REMOVAL_VJ": 3, "HK1C_LEVEL": 0.995,
          "HK1C_MARGIN": 0.03, "DELTA": 0.05, "P_PLANT": 0.15, "RHO": 0.5, "POWER_MIN": 0.80, "N_DATASETS": 2000,
          "N_DATASETS_DESCRIPTIVE_ARMS": 500, "N_WEIGHTS": 500, "POWER_FLAG_LEVEL": 0.95, "F_MIN": 6, "PD_MIN_EVALUABLE": 1,
          "MIN_UNITS": 39, "MIN_LOGS": 8, "B_BOOT": 20000, "C_FORM_C": 0.03, "NI_MARGIN": 0.03, "FORM_A_K": 4, "HOLM_M": 5,
          "DESC_F_MIN": (4, 8), "DESC_P": (0.10, 0.12, 0.20), "DESC_N_DATASETS": 500}


def _other(v):
    if isinstance(v, str):
        return v + "_other"
    return tuple(x + 1 for x in v) if isinstance(v, tuple) else (v * 2 if v else 1)


def t_crit():
    import c1_analyse_v09 as A9
    import c1_analyse_v03 as A3
    import c1_predarm_v07 as P7
    R, B, K, A = A9.R, A9.B, A9.K, A9.A_
    out, pins = {}, {}
    # ---- one test per constant: the value, a config stating it equal (accepted) and different (refused)
    assert set(R.CONSTANTS) == set(PINNED), sorted(set(R.CONSTANTS) ^ set(PINNED))
    for name, val in PINNED.items():
        assert R.CONSTANTS[name] == val and getattr(R, name) == val, name
        assert R.config_check({"criteria": {name: val}})["stated_and_equal"] == {name: val}
        assert R.config_check({name.lower(): val})
        e = raises(R.config_check, {"criteria": {name: _other(val)}})
        assert e and name in e, (name, e)
        e = raises(R.config_check, {name.lower(): _other(val)})
        assert e and "differently from the code" in e, (name, e)
        pins[name] = val
    out["constants_pinned"] = "%d constants, each: value, stated equal (accepted), stated different (refused, top level and criteria block)" % len(pins)
    assert R.BATCH == 25
    e = raises(R.config_check, {"criteria": {"NOT_A_RULE": 1}})
    assert e and "not a rule constant" in e
    e = raises(R.config_check, {"c": {"t1": 0.03, "t3": 0.04}})
    assert e and "C_FORM_C" in e
    lv = R.levels()
    assert (lv["against"], lv["for"], lv["hk1c_ub"], lv["power_flag"]) == (0.95, 0.975, 0.995, 0.95)
    assert abs(lv["removal_V_t"] - (1 - 0.0125 / 9)) < 1e-15 and abs(lv["removal_VJ_t"] - (1 - 0.0025 / 3)) < 1e-15 and abs(lv["form_a"] - (1 - 0.025 / 4)) < 1e-15
    assert lv["holm_levels"] == [0.025 / 5, 0.025 / 4, 0.025 / 3, 0.025 / 2, 0.025] and lv["bootstrap_B"] == 20000
    # the modules the rules build on carry the same values
    B.configure("c1")
    K.STRICT_Q = False
    assert (A.MIN_SCENES, A.MIN_LOGS) == (R.MIN_UNITS, R.MIN_LOGS) and B.F_MIN == R.F_MIN and B.NI_MARGIN == R.NI_MARGIN
    # 52(d): B = 20000 in the analysis; the weights' first 500 rows (the power rule's) do not depend on B
    lgs = {"s%02d" % i: "l%02d" % (i % 12) for i in range(60)}
    eps_ = [{"scene": s_, "delay_kf": 0} for s_ in lgs]
    w500 = A.keys_and_weights(eps_, lgs, 500, np.random.default_rng([20261110, 0, 0]))[4]
    w20k = A.keys_and_weights(eps_, lgs, R.B_BOOT, np.random.default_rng([20261110, 0, 0]))[4]
    assert w20k.shape[0] == 20000 and np.array_equal(w500, w20k[:500])
    rc_, o_ = sub(["c1_analyse_v09.py", "--config", "never_read.json", "--out", "x.json", "--decision", "y.json", "--standin", "--boot", "2000"])
    assert rc_ != 0 and "B = 20000 is fixed" in o_, o_[-300:]
    # 52(b): the C1 run's h9_label
    assert R.check_h9_label_c1({"h9_label": "descriptive"}, "c1") == "descriptive" and R.check_h9_label_c1({"h9_label": "secondary"}, "smoke") == "secondary"
    e = raises(R.check_h9_label_c1, {"h9_label": "secondary"}, "c1")
    assert e and "52b" in e
    assert set(B.C_DEFAULT.values()) == {R.C_FORM_C} and len(B.FORM_A_SET) == R.FORM_A_K and len(A9.A6.FAMILY_S) == R.HOLM_M
    out["levels"] = lv
    # ---- the config refusal in decide_all and main
    cfgs = (({"routes": [], "h9_label": "secondary", "c": {"t1": 0.05, "t3": 0.03}}, "C_FORM_C"),
            ({"routes": [], "h9_label": "secondary", "criteria": {"ALPHA_FOR": 0.05}}, "ALPHA_FOR"),
            ({"routes": [], "h9_label": "secondary", "hk1c_level": 0.99}, "HK1C_LEVEL"))
    for cfg_, msg in cfgs:
        e = raises(A9.decide_all, planted(), cfg_, "smoke", {"tables": {}})
        assert e and msg in e, e
    d = os.path.join(OUT, "crit")
    shutil.rmtree(d, ignore_errors=True)
    cfgp = wj(os.path.join(d, "cfg_alpha.json"), {"routes": [], "h9_label": "secondary", "criteria": {"N_DATASETS": 200}})
    rc, o = sub(["c1_analyse_v09.py", "--config", cfgp, "--out", os.path.join(d, "a.json"), "--decision", os.path.join(d, "d.json"), "--smoke"])
    assert rc != 0 and "N_DATASETS" in o and not os.path.exists(os.path.join(d, "a.json")), o[-400:]
    dd = A9.decide_all(planted(), {"routes": [], "h9_label": "secondary", "criteria": {"alpha_for": 0.025}}, "smoke", {"tables": {}})
    assert dd["criteria"]["constants"] == R.CONSTANTS and dd["criteria"]["levels"]["removal_V_t"] == R.LEVEL_REMOVAL_V
    out["config_refusal"] = "a config stating c, ALPHA_FOR or HK1C_LEVEL differently is refused (decide_all and main); stated equal is accepted"
    # ---- the power rule: vectorised = reference loop; nested; target-only at DELTA; descriptive arms
    rng = np.random.default_rng(20261105)
    n_ep, J = 80, 6
    N = rng.integers(0, 40, size=(n_ep, J)).astype(float)
    N[rng.random(N.shape) < 0.3] = 0
    sc = np.array(["s%02d" % i for i in range(n_ep)])
    lg = np.array(["l%02d" % (i % 16) for i in range(n_ep)])
    ev = A.evaluable(N, sc, lg)
    Wp = rng.multinomial(n_ep, [1.0 / n_ep] * n_ep, size=R.N_WEIGHTS).astype(float)
    p1, _ = R.power_target(N, ev, sc, Wp, np.random.default_rng([1, 2, 3]), reps=50)
    p2, _ = R.power_target_reference(N, ev, sc, Wp, np.random.default_rng([1, 2, 3]), reps=50)
    assert ev.sum() >= 3 and np.array_equal(p1, p2), (p1, p2)
    a100, _ = R.power_target(N, ev, sc, Wp, np.random.default_rng([1, 2, 3]), reps=100)
    g = np.random.default_rng([1, 2, 3])
    b1, _ = R.power_target(N, ev, sc, Wp, g, reps=50)
    b2, _ = R.power_target(N, ev, sc, Wp, g, reps=50)
    assert np.array_equal(np.round(a100 * 100), np.round(b1 * 50 + b2 * 50))
    # target-only: with the target also at DELTA the 'power' is the size of the one-sided test (small); at 0.15 it is larger
    size, _ = R.power_target(N, ev, sc, Wp, np.random.default_rng([1, 2, 4]), p_plant=R.DELTA, reps=100)
    assert size[ev].max() <= 0.2 and a100[ev].mean() > size[ev].mean()
    out["power_rule"] = {"vectorised_equals_reference": True, "nested": "100 datasets = 50 + 50 from one generator",
                         "size_at_delta_max": float(size[ev].max()), "mean_power_at_0.15": float(a100[ev].mean())}
    # ---- hk1_rule_criteria: levels per arm role, HK1c at HK1C_LEVEL, power datasets per arm class
    n_ep, n_c = 60, 4
    sc = np.array(["s%02d" % i for i in range(n_ep)])
    lg = np.array(["l%02d" % (i % 12) for i in range(n_ep)])
    cells = [("cell%d" % j, None) for j in range(n_c)]
    Wb = rng.multinomial(n_ep, [1.0 / n_ep] * n_ep, size=R.B_BOOT).astype(float)
    Tt = {}
    for p in K.CONF_POPS:
        Nn = rng.integers(20, 40, size=(n_ep, n_c)).astype(float)
        Tt[p] = (Nn, rng.binomial(Nn.astype(int), np.array([0.03, 0.05, 0.075, 0.09])[None, :]).astype(float))
    one = np.ones((1, n_ep))
    res = {}
    for arm, lvl, reps in (("Mstar", 0.95, 2000), ("B3", 1 - 0.0125 / 9, 2000), ("B0a1", 0.95, 500)):
        v = R.hk1_rule_criteria(Tt, cells, sc, lg, Wb, [5, 6], arm=arm)
        assert abs(v["levels"]["flags"] - lvl) < 1e-15 and v["power_rule"]["datasets"] == reps, arm
        for k, p in enumerate(K.CONF_POPS):
            Nn, Xx = Tt[p]
            fam = np.flatnonzero(A.evaluable(Nn, sc, lg))
            est, boot = A.rates(Nn, Xx, one)[0], A.rates(Nn, Xx, Wb)
            _, _, _, sig, _ = A.flag(est, boot, fam, lvl)
            assert v["pops"][p]["flagged"] == [cells[j][0] for i, j in enumerate(fam) if sig[i]], (arm, p)
            Np_, Xp_ = Nn.sum(1, keepdims=True), Xx.sum(1, keepdims=True)
            e1, b1_ = A.rates(Np_, Xp_, one)[0], A.rates(Np_, Xp_, Wb)
            _, ubh, _, _, _ = A.flag(e1, b1_, np.array([0]), 0.995)
            _, ub95, _, _, _ = A.flag(e1, b1_, np.array([0]), 0.95)
            assert abs(v["pops"][p]["pooled"]["ub"] - ubh[0]) < 1e-15 and ubh[0] >= ub95[0]
            assert v["pops"][p]["pooled"]["HK1c_ub_le_delta_plus_0.03"] == bool(ubh[0] <= 0.08)
            pw, _ = R.power_target(Nn, A.evaluable(Nn, sc, lg), sc, Wb[:500], np.random.default_rng([5, 6, k]), reps=reps)
            assert v["pops"][p]["family"] == [cells[j][0] for j in np.flatnonzero(A.evaluable(Nn, sc, lg) & (pw >= 0.80))], (arm, p)
        res[arm] = {p: v["pops"][p]["flagged"] for p in K.CONF_POPS}
    vm = R.hk1_rule_criteria(Tt, cells, sc, lg, Wb, [5, 6], arm="Mstar")
    dp = vm["descriptive_power"]["pops"][K.CONF_POPS[0]]
    assert set(dp["per_cell"]["cell0"]) == {"0.10", "0.12", "0.15", "0.20"} and dp["datasets"]["0.10"] == 500 and dp["datasets"]["0.15"] == 2000
    assert set(vm["pops"][K.CONF_POPS[0]]["floor_at_F_MIN"]) == {"4", "6", "8"} and vm["pops"][K.CONF_POPS[0]]["family_record_share"] is not None
    out["hk1_rule_criteria"] = {"flags_by_arm_role": res, "rule": "M* and descriptive arms at 0.95; comparators at 1 - 0.0125/9; HK1c's UB at "
                                "0.995; families by power_target (2000 datasets; 500 for descriptive arms); M*'s descriptive power at 0.10, "
                                "0.12, 0.20 (500) and 0.15 (2000), floors at F_MIN 4, 6, 8, record shares"}
    # a comparator flagged at 0.95 but not at 1 - 0.0125/9 stays in V_t (constructed by search over seeds)
    found = None
    for s_ in range(200):
        r2 = np.random.default_rng([99, s_])
        Nn = r2.integers(20, 40, size=(n_ep, 1)).astype(float)
        Xx = r2.binomial(Nn.astype(int), 0.065).astype(float)
        est, boot = A.rates(Nn, Xx, one)[0], A.rates(Nn, Xx, Wb)
        f95 = A.flag(est, boot, np.array([0]), 0.95)[3][0]
        frm = A.flag(est, boot, np.array([0]), R.LEVEL_REMOVAL_V)[3][0]
        if f95 and not frm:
            found = s_
            break
    assert found is not None
    out["removal_level_effect"] = "a cell flagged at one-sided 0.95 but not at 1 - 0.0125/9 (seed %d): it removes M*'s validity but not a comparator" % found
    # ---- Forms A, B, C; H3; H10; H6b; Holm
    nl = 40
    Ws = rng.multinomial(nl, [1.0 / nl] * nl, size=R.B_BOOT).astype(float)
    rate = {a: rng.uniform(0.05, 0.15, nl) + (0.0 if a == "Mstar" else 0.04) for a in ("Mstar", "B0", "B1", "B3", "B4", "B6", "B9", "RETUNED")}
    st_ok = {"Mstar": {"valid": True}}
    fa = B.form_a(st_ok, rate, Ws)
    assert B.form_a is R.form_a_criteria and fa["level"] == R.LEVEL_FORM_A
    assert all(abs(fa["vs"][c]["ub"] - B.paired(rate, Ws, "Mstar", c, 1 - 0.025 / 4)["ub"]) < 1e-15 for c in B.FORM_A_SET)
    fc = B.form_c(rate, Ws, 0.03)
    assert fc["level"] == 0.975 and abs(fc["ub"] - B.paired(rate, Ws, "Mstar", "B4", 0.975)["ub"]) < 1e-15
    js = {a: A3.joint_status({"pops": {p: {"E": 0.03, "evaluable": True, "flagged": False, "ub_le_delta_plus_0.03": True} for p in B.POPS}})
          for a in ("MstarJx",) + B.KJ_SET}
    rj = dict(rate, MstarJx=rate["Mstar"] - 0.01)
    jb = A9.joint_b(js, rj, Ws)
    assert abs(jb["level"] - (1 - 0.025 / (2 * len(jb["VJ"])))) < 1e-15 and jb["removal_level"] == R.LEVEL_REMOVAL_VJ
    assert abs(jb["p_rejection_bonferroni"] - min(1.0, 2 * len(jb["VJ"]) * max(v["p_lt0"] for v in jb["vs"].values()))) < 1e-15
    assert set(jb["holm_levels"]) == {"%.6f" % a for a in R.HOLM_LEVELS}
    out["forms"] = {"A": fa["level"], "C": fc["level"], "H3_level": jb["level"], "H3_V^J": len(jb["VJ"])}
    cellsP = [("c%d" % j, None) for j in range(3)]
    estd = {"B6": np.array([0.12, 0.06, 0.02]), "Mstar": np.array([0.02, 0.02, 0.02])}
    bootd = {a: estd[a][None, :] + rng.normal(0, 0.02, size=(R.B_BOOT, 3)) for a in estd}
    evd = {a: np.ones(3, bool) for a in estd}
    h10 = B.h10_rule(cellsP, estd, bootd, evd, set(), set(), rate, Ws)
    sg = A.flag(estd["B6"], bootd["B6"], np.arange(3), 0.975)[3]
    pr = A.paired(estd, bootd, evd, cellsP, "B6", "Mstar", 0.975)
    want = [cellsP[j][0] for j in range(3) if sg[j] and pr[cellsP[j][0]]["positive"]]
    assert B.h10_rule is R.h10_rule_criteria and h10["cells_failing_B6"] == want and h10["levels"]["B6_flag"] == 0.975
    assert abs(h10["noninferiority"]["ub"] - B.paired(rate, Ws, "Mstar", "B6", 0.975)["ub"]) < 1e-15
    ms = {"E1": {"fixed": None, "refit": None}, "H6b_detail": {"cell a": 0.02, "cell b": 0.03}, "H6b_p": 0.02}
    import types
    saved = B.M
    try:
        B.M = types.SimpleNamespace(hypotheses_e1=lambda f, r: {"HM1": True, "Mstar_flagged_cells": []}, failures=lambda st, b, lab: ["cell a", "cell b"])
        h6 = B.h6_rules(ms)
        h6n = B.h6_rules(dict(ms, H6b_detail={"cell b": 0.03}))
    finally:
        B.M = saved
    assert h6["H6b"] and h6["B4_failing_cells"] == ["cell a"] and h6["H6b_level"] == 0.025 and not h6n["H6b"]
    claims = {"H2": {"p": 0.004, "gate_ok": True, "holds": True}, "H3": {"p": 0.007, "gate_ok": True, "holds": True},
              "H4": {"p": 0.03, "gate_ok": True, "holds": True}, "H6b": {"p": 0.2, "gate_ok": True, "holds": True},
              "H10": {"p": 0.5, "gate_ok": True, "holds": True}}
    sts = {c: "holds" for c in claims}
    sts["H2"] = "does not hold"   # the bound form at the nominal level disagrees; the p-value governs (52e)
    hs = A9.A6.A5.holm_v05(claims, sts, True)
    assert A9.A6.A5.holm_v05 is R.holm_v05_criteria and all(hs[c]["alpha_family"] == 0.025 for c in claims)
    assert hs["H2"]["rejected"] and abs(hs["H2"]["holm_level"] - 0.005) < 1e-15 and hs["H3"]["rejected"] is False
    assert hs["H2"]["confirmed"] is True and hs["H2"]["status"] == "holds" and hs["H2"]["status_bound_nominal"] == "does not hold"
    assert hs["H3"]["status"] == "does not hold" and hs["H3"]["status_bound_nominal"] == "holds"
    hs_closed = A9.A6.A5.holm_v05(claims, sts, False)
    assert all(v.get("confirmed") is False or v.get("confirmed") is None for v in hs_closed.values())
    fcs = {t: R.form_c_criteria(rate, Ws, 0.03) for t in ("t1", "t3")}
    dsf = {"family_S": hs, "claims_status": dict(sts), "hypotheses": {c: {"status": sts[c]} for c in claims}}
    A9.s_decision_forms(dsf, {"within_lt3d": {t: {"form_c": fcs[t]} for t in fcs}})
    h2f = dsf["S_decision_forms"]["by_claim"]["H2"]
    lvl_key = "%.6f" % hs["H2"]["holm_level"]
    assert h2f["bound_at_holm_level"]["t1"] == fcs["t1"]["holm_levels"][lvl_key] and h2f["agree"] == (all(fcs[t]["holm_levels"][lvl_key]["holds"] for t in fcs) == True)
    assert dsf["claims_status"]["H2"] == "holds" and dsf["hypotheses"]["H2"]["status_bound_nominal"] == "does not hold"
    assert "not available" in dsf["S_decision_forms"]["by_claim"]["H6b"]["bound_at_holm_level"]
    out["H10_H6b_Holm"] = {"H10_cells": want, "H6b_cells": h6["B4_failing_cells"], "Holm_H2_level": hs["H2"]["holm_level"],
                           "Holm_H3_rejected": hs["H3"]["rejected"], "note": "H3's p 0.007 > 0.025/4 after H2: not rejected at 0.025 (it would be at 0.05: 0.0125)",
                           "decision_form": "the p-value governs in S (H2 confirmed although its nominal bound form says 'does not hold'); the bound "
                                            "at the Holm-assigned level is reported with agreement; H6b: p-values only"}
    # ---- the predictor arm's H9 floor (c1_predarm_v07): the power rule, the floor F_MIN, flags at 0.95
    assert P7.P5.h9_rule_v05 is P7.h9_rule_v07
    Nh = rng.integers(0, 30, size=(n_ep, 5)).astype(float)
    Xh = rng.binomial(Nh.astype(int), 0.02).astype(float)
    cellsH = [("e2_%d" % j, None) for j in range(2)] + [(x, None) for x in ("hist=2", "hist=3-4", "hist>=5")]
    h9 = P7.h9_rule_v07(Nh, Xh, cellsH, 2, sc, lg, Wb, [20261111, 0, 5])
    pwh, _ = R.power_target(Nh, A.evaluable(Nh, sc, lg), sc, Wb[:500], np.random.default_rng([20261111, 0, 5]))
    assert h9["power_by_cell"] == {cellsH[j][0]: float(pwh[j]) for j in np.flatnonzero(A.evaluable(Nh, sc, lg))} and h9["floor"] == 6
    assert h9["power_rule"]["datasets"] == 2000 and h9["levels"]["flags"] == 0.95
    assert set(h9["cell_estimates"]) == set(h9["power_by_cell"]) == set(h9["cell_ub_0.95"])
    seeds = {"20261102": False, "20261104": False, "20261105": False}
    tab = {"ok": True, "checks": {}, "data": {t: {"H9": False, "H9_noHL": False, "population": "PD", "H9_seed": seeds,
                                                   "arms": {"TPP": {"PD": {"HL": dict(h9, family_size_E2=2 if t == "t1" else 7)}}}} for t in A9.TRACKERS}}
    dsc = A9.decide_all(planted(), {"routes": [], "h9_label": "descriptive"}, "smoke", {"tables": {"h9": tab}})
    assert dsc["claims_status"]["H9"] == "descriptive" and dsc["H9_descriptive"]["by_tracker"]["t1"]["floor_met"] is False
    assert dsc["H9_descriptive"]["by_tracker"]["t1"]["cell_estimates"] == h9["cell_estimates"]
    assert "does not hold" not in json.dumps([dsc["hypotheses"]["H9"], dsc["H9_floor"], dsc["H9_descriptive"], dsc["claims_status"]["H9"]], default=str)
    out["H9_floor_rule"] = "c1_predarm_v07.h9_rule_v07 replaces h9_rule_v05 in c1_predarm_v05; its family is power_target's (2000 datasets, seed [20261111, i, 5])"
    out["H9_descriptive"] = "status 'descriptive'; estimates, simultaneous one-sided 95 % bounds, family size and floor status reported; no 'does not hold'"
    out["tests"] = len(PINNED) + 17
    return out


# ------------------------------------------------------------------------------------------------------------------------------ DEVREPLAY
DEVREPLAY_OUT = os.path.join(W, "70_TESTS", "c1_v01", "status_v09", "c1_devreplay_v01.json")


def t_devreplay():
    """The development replay (tests/c1_devreplay_v01.py, run once and checkpointed: about an hour) under the audit's rules: the
    recorded result must have been made by the bound c1_rules_v01 and c1_devreplay_v01, with the current constants. Its values are
    compared by the lead with development check v03 (D16 v33 Choice 52); no expected verdict is asserted."""
    assert os.path.exists(DEVREPLAY_OUT), "no development replay: run tests/c1_devreplay_v01.py"
    r = json.load(open(DEVREPLAY_OUT))
    now = {"c1_rules_v01": G.sha(os.path.join(C1, "c1_rules_v01.py")), "c1_devreplay_v01": G.sha(os.path.join(C1, "tests", "c1_devreplay_v01.py"))}
    assert r["code_sha256"] == now, "the development replay was made by other code: re-run tests/c1_devreplay_v01.py (%s vs %s)" % (r["code_sha256"], now)
    verdicts = {t: v["verdict"] for t, v in r["trackers"].items()}
    import c1_rules_v01 as Rr
    assert r["constants"] == json.loads(json.dumps(Rr.CONSTANTS)) and set(r["trackers"]) == {"t1", "t3"}
    # D16 v33 Choice 52: the lead compares the replay's values with development check v03; no expected verdict is asserted here
    return {"result": os.path.relpath(DEVREPLAY_OUT, W).replace(os.sep, "/"), "sha256": G.sha(DEVREPLAY_OUT), "verdicts": verdicts,
            "levels": r["levels"], "seconds_of_the_replay": r.get("seconds")}


# ------------------------------------------------------------------------------------------------------------------------------ PC5
def t_pc5():
    d = os.path.join(OUT, "pc5")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    o = os.path.join(d, "pc5_h9.json")
    rc, so = sub(["c1_power_counts_v05.py", o, "--parts", "H9", "--reps-h9", "3"])
    assert rc == 0 and "C1 POWER COUNTS V05 DONE" in so, so[-1500:]
    r = json.load(open(o))
    out = {}
    assert "R16" in r["development_inputs"]["part_B"] and "No AV2 outcome" in r["outcome_statement"] and "reported only" in r["status"]
    for t in ("t1", "t3"):
        h = r["partH9"][t]
        assert "no history length" in h["primary"]["label"] and "overstates" in h["primary"]["label"]
        assert "descriptive" in h["sensitivity_dev_history"]["label"]
        p375 = h["primary"]["375_by_log_resampling"]
        assert p375["units"] == 375 and p375["draws"] == 3 and 0 <= p375["P_family_E2_ge_6"] <= 1
        cells = h["primary"]["first_draw"]["as_given"]["cells"]
        assert cells and not any("hist" in c for c in cells), cells[:5]
        assert any("hist" in c for c in h["sensitivity_dev_history"]["first_draw"]["as_given"]["cells"])
        out[t] = {"primary_375": {k: p375[k] for k in ("family_size_E2_median", "family_size_E2_min", "family_size_E2_max", "P_family_E2_ge_6")},
                  "sensitivity_375": {k: h["sensitivity_dev_history"]["375_by_log_resampling"][k] for k in ("family_size_E2_median", "P_family_E2_ge_6")}}
    import c1_power_counts_v05 as PC
    orig = PC._VALIDITY_V02
    try:
        det = {p: {"flagged": 0, "family_flagged": 0, "pooled_flagged": False, "hk1c": p != "PD_inpath"} for p in PC.V2.CONF_POPS}
        PC._VALIDITY_V02 = lambda T, W_, ev: (False, True, det)
        assert PC.validity_v05(None, None, None)[:2] == (False, False)
        det2 = dict(det, PD_inpath=dict(det["PD_inpath"], family_flagged=1))
        PC._VALIDITY_V02 = lambda T, W_, ev: (False, True, det2)
        assert PC.validity_v05(None, None, None)[:2] == (False, True)
    finally:
        PC._VALIDITY_V02 = orig
    out["part_B_rule"] = "failing HK1c alone no longer counts as shown invalid (v02 counted it); a flagged family cell does; M*'s strict validity unchanged"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ Q3
Q3_RUN = r"""
import sys, tracemalloc
sys.path.insert(0, sys.argv[1])
import c1_quarantine_v03 as Q
tracemalloc.start()
Q.main(sys.argv[2:])
print("Q3_PEAK", tracemalloc.get_traced_memory()[1])
"""
SCAN_RUN = r"""
import sys, tracemalloc
sys.path.insert(0, sys.argv[1])
import c1_guard_v06 as G
tracemalloc.start()
m, n, sk = G.scan_plain_v06(G.W, {int(sys.argv[2])}, {sys.argv[3]})
print("SCAN", len(m), n, tracemalloc.get_traced_memory()[1])
"""


def t_q3():
    TQ = os.path.join(OUT, "q3_tree")
    shutil.rmtree(TQ, ignore_errors=True)
    QC = os.path.join(TQ, "50_CODE", "c1_av2")
    os.makedirs(QC)
    for f in ("c1_guard_v03.py", "c1_guard_v04.py", "c1_guard_v05.py", "c1_guard_v06.py", "c1_quarantine_v03.py"):
        shutil.copy2(os.path.join(C1, f), QC)
    big = os.path.join(TQ, "30_DATA", "fx_big", "infos_archive_big.tar")
    os.makedirs(os.path.dirname(big))
    payload = os.path.join(TQ, "payload.bin")
    with open(payload, "wb") as f:
        for _ in range(64):
            f.write(os.urandom(1 << 20))
    with tarfile.open(big, "w") as tf:
        tf.add(payload, arcname="train_progress/av2_gt_database/fx_car_1.bin")
    os.remove(payload)
    size, h = os.path.getsize(big), G.sha(big)
    limit = 16 << 20
    cmd = ["-c", Q3_RUN, QC, "--extra", rel_to(big, TQ)]
    rc, o = sub(cmd, cwd=QC)
    m = re.search(r"Q3_PEAK (\d+)", o)
    assert rc == 0 and "C1 QUARANTINE V03 DONE" in o and m and not os.path.exists(big), o[-1500:]
    peak = int(m.group(1))
    assert peak < limit, "peak Python memory %d B while quarantining a %d B file" % (peak, size)
    qd = os.path.join(TQ, "30_DATA", "av2_gt_quarantine_v01")
    assert sorted(os.listdir(qd)) == ["QUARANTINE_MANIFEST.json", "infos_archive_big.tar.gz"], os.listdir(qd)
    mem = json.load(open(os.path.join(qd, "QUARANTINE_MANIFEST.json")))["members"]
    assert len(mem) == 1 and mem[0]["sha256_decompressed"] == h and mem[0]["bytes"] == size
    assert gz_sha_file(os.path.join(qd, "infos_archive_big.tar.gz")) == h
    rc, o = sub(cmd, cwd=QC)
    m2 = re.search(r"Q3_PEAK (\d+)", o)
    assert rc == 0 and "already quarantined" in o and m2 and int(m2.group(1)) < limit, o[-800:]
    cp = os.path.join(TQ, "60_RESULTS", "copy", "renamed.bin")
    os.makedirs(os.path.dirname(cp))
    with gzip.open(os.path.join(qd, "infos_archive_big.tar.gz"), "rb") as fi, open(cp, "wb") as fo:
        shutil.copyfileobj(fi, fo, 1 << 20)
    rc, o = sub(["-c", SCAN_RUN, QC, str(size), h], cwd=QC)
    s = re.search(r"SCAN (\d+) (\d+) (\d+)", o)
    assert rc == 0 and s and int(s.group(1)) == 1 and int(s.group(3)) < limit, o[-800:]
    shutil.rmtree(TQ, ignore_errors=True)
    return {"quarantine": "a %d B tar quarantined whole as one gzip member (never unpacked); peak Python memory %d B (limit %d)" % (size, peak, limit),
            "rerun": "idempotent, the member verified streamed (peak %d B)" % int(m2.group(1)),
            "scan": "c1_guard_v06.scan_plain_v06 finds a renamed plain copy by size and hash, streamed (peak %s B)" % s.group(3)}


# ------------------------------------------------------------------------------------------------------------------------------ TREE
PROV_RUN = r"""
import json, os, shutil, sys
sys.path.insert(0, sys.argv[1])
import c1_av2_provenance_v01 as PV
TOOLS = {"horizon": PV.HORIZON, "ego": PV.EGO, "gt": PV.GT}

def runner(kind, m, bound, tmpd, logs_file):
    # stands in for a bound builder that reproduces the recorded file; the real re-make is tested in PROV
    src = m["inputs"][kind]
    dst = os.path.join(tmpd, os.path.basename(src))
    shutil.copy2(src, dst)
    return dst, PV.require_builder(TOOLS[kind], bound, kind)

rec = PV.run([os.path.abspath(p) for p in sys.argv[4:]], os.path.abspath(sys.argv[2]), runner=runner)
json.dump(rec, open(sys.argv[3], "w"), indent=1)
print("PROV_RECORD", rec["readme_sha256"][:12], len(rec["manifests"]), rec["kinds"])
"""


def build_tree(T):
    shutil.rmtree(T, ignore_errors=True)
    for h, p, r in readme_rows():
        dst = os.path.join(T, p)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(os.path.join(W, p), dst)
        assert G.sha(dst) == h, p
    shutil.copy2(README, os.path.join(T, "50_CODE", "c1_av2", os.path.basename(README)))
    shutil.copy2(os.path.join(C1, "c1_quarantine_v01.py"), os.path.join(T, "50_CODE", "c1_av2", "c1_quarantine_v01.py"))  # superseded, for E2
    for rel_ in ("60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_t1_v01.json", "60_RESULTS/c1_transfer_fits_v01/c1_transfer_fits_t3_v01.json",
                 "60_RESULTS/x2/x2_oc_q4_v02.json", "40_PROTOCOL/OSF_PROJECT_RECORD_v01.txt"):
        os.makedirs(os.path.dirname(os.path.join(T, rel_)), exist_ok=True)
        shutil.copy2(os.path.join(W, rel_), os.path.join(T, rel_))
    fx = os.path.join(T, "30_DATA", "fx_av2relab")
    shutil.copytree(os.path.join(R17D, "fx_av2relab"), fx)
    gt = os.path.join(fx, "gt.json")
    bsha = G.sha(os.path.join(W, STAGEA_BUILDER))
    # the worker's receipt names a bound tracker and a bound adapter (the test's stand-in; the tracks are unchanged)
    w0 = os.path.join(fx, "worker0")
    rec = json.load(open(os.path.join(w0, "x1_export_record.json")))
    det = wj(os.path.join(fx, "det", "dets.json"), {"fixture": "test v12"})
    wj(os.path.join(fx, "det", "receipt.json"), {"adapter": "av2_tracker_input_v02"})
    rec.update({"harness_version": "av2_track_v02 (test v12 fixture: R17d's stand-in tracks, not AV2)",
                "argv": [os.path.join(T, "50_CODE", "av2", "av2_track_v02.py")],
                "output_sha256": dict(rec["output_sha256"], **{"x1_tracks.jsonl.gz": G.sha(os.path.join(w0, "x1_tracks.jsonl.gz"))})})
    rec["provenance"] = dict(rec["provenance"], detection_path=det)
    wj(os.path.join(w0, "x1_export_record.json"), rec)
    ego = os.path.join(fx, "ego.json.gz")
    open(ego, "wb").write(gzip.compress(json.dumps({"fixture": "test v12 ego poses"}).encode(), mtime=0))
    man = json.load(open(os.path.join(fx, "stageA", "MANIFEST.json")))
    man["inputs"].update({"workers": [w0], "horizon": os.path.join(fx, "horizon.jsonl.gz"), "gt": gt, "builder_sha256": bsha,
                          "ego": ego, "ego_sha256": G.sha(ego)})
    assert man["inputs"]["gt_sha256"] == G.sha(gt) and man["inputs"]["horizon_sha256"] == G.sha(man["inputs"]["horizon"])
    wj(os.path.join(fx, "stageA", "MANIFEST.json"), man)
    zero = {"stage": "A", "dataset": "av2", "scenes": {}, "note": "zero-scene stage-A cache (test v12)",
            "inputs": {k: man["inputs"][k] for k in ("workers", "export_sha256", "horizon", "horizon_sha256", "gt", "gt_sha256", "ego", "ego_sha256",
                                                      "builder_sha256")}}
    wj(os.path.join(T, "30_DATA", "fx_stageA_zero", "MANIFEST.json"), zero)
    p2 = os.path.join(T, "70_TESTS", "fx_p2")  # outside 30_DATA: R17c p2 holds a stage-B manifest
    shutil.copytree(os.path.join(R17C, "p2"), p2, ignore=shutil.ignore_patterns("*.json.tmp"))
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
    roles = {n: [wj(os.path.join(T, "30_DATA", "fx_roles", "%s.json" % n), {"role": "data:" + n, "fixture": "test v12"})] for n in AV2_ROLES}
    roles["port_equiv"].append(wj(os.path.join(T, "30_DATA", "fx_roles", "port_equiv_b.json"), {"role": "data:port_equiv", "fixture": "second file"}))
    fr = os.path.join(T, "70_TESTS", "fx_freeze_record_standin.md")   # D16 v32 Choice 51(a): a stand-in only, in the test's own copy tree
    os.makedirs(os.path.dirname(fr), exist_ok=True)
    open(fr, "w", encoding="utf-8").write("# test v12 stand-in for the lead's C1_FREEZE_TIME_RECORD (not the record)\n")
    roles["freeze_record"] = [fr]
    inv_tar = tar_fixture(os.path.join(T, "30_DATA", "fx_inv", "infos_archive_fx.tar"),
                          [("train_progress/av2_infos_train_fx.pkl", os.urandom(3000)), ("train_progress/av2_gt_database/0a1b_car_1.bin", os.urandom(2000))])
    inv = inventory_fixture(os.path.join(T, "40_PROTOCOL", "C1_GT_INVENTORY_fx.json"), [extra, inv_tar], T)
    return {"fx": fx, "gt": gt, "zero": os.path.join(T, "30_DATA", "fx_stageA_zero"), "p2": p2, "old_gt": old_gt, "extra": extra, "stray": stray,
            "envc": envc, "roles": roles, "inv_tar": inv_tar, "inventory": inv, "bsha": bsha}


def tree_freeze(T, F, plan_name, extra=(), roles=None, manifests=None, drop=()):
    plan = os.path.join(T, "70_TESTS", plan_name)
    if not os.path.exists(plan):
        os.makedirs(os.path.dirname(plan), exist_ok=True)
        open(plan, "w").write("# tree probe plan %s\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\nFROZEN_ROLES_END\n" % plan_name)
    fx = F["fx"]
    roles = dict(F["roles"], gt_inventory=[F["inventory"]], provenance=[F["prov"]]) if roles is None else roles
    data = ["scene_json=" + F["scene_json"], "e0_plan=" + os.path.join(fx, "e0_plan.json")]
    data += ["%s=%s" % (n, p) for n in sorted(roles) if n not in drop for p in roles[n]]
    mans = manifests or [os.path.join(fx, "stageA", "MANIFEST.json"), os.path.join(F["zero"], "MANIFEST.json")]
    cmd = [os.path.join(T, "50_CODE", "c1_av2", "c1_freeze_v07.py"), "--plan", plan, "--readme", F["readme"], "--results-dir",
           os.path.join(T, "70_TESTS", "results_" + plan_name), "--folds", os.path.join(fx, "folds_av2.json"), "--split", F["split"],
           "--transfer-fits", os.path.join(T, "60_RESULTS", "c1_transfer_fits_v01", "c1_transfer_fits_t1_v01.json"),
           os.path.join(T, "60_RESULTS", "c1_transfer_fits_v01", "c1_transfer_fits_t3_v01.json"),
           "--stageA-manifests"] + mans + ["--config", F["config"], "--data"] + data + \
          ["--test-out-dir", os.path.join(T, "70_TESTS", "freeze_tests_" + plan_name), "--tpp-python", TPP38] + list(extra)
    return plan, sub(cmd, cwd=os.path.join(T, "50_CODE", "c1_av2"))


def t_tree():
    T = os.path.join(OUT, "tree")
    F = build_tree(T)
    TC = os.path.join(T, "50_CODE", "c1_av2")
    QD = os.path.join(T, "30_DATA", "av2_gt_quarantine_v01")
    proto = lambda n: os.path.join(T, "40_PROTOCOL", n)  # noqa: E731
    out = {}
    probe = "50_CODE/c1_av2/tests/freeze_probe_envcheck_v01.py"
    F["readme"] = readme_with(probe, os.path.join(TC, "README_tree_probe.md"), root=T)
    F["split"] = wj(os.path.join(T, "30_DATA", "fx_split.json"), {"rule": "tree probe split"})
    F["config"] = wj(os.path.join(T, "30_DATA", "fx_config.json"), {"note": "tree probe config", "h8_units": "folds", "routes": [], "h9_label": "descriptive",
                                                                    "folds": os.path.join(F["fx"], "folds_av2.json"), "c": {"t1": 0.03, "t3": 0.03},
                                                                    "h8": os.path.join(T, "70_TESTS", "h8_post.json")})
    F["scene_json"] = os.path.join(T, "30_DATA", "fx_meta", "scene.json")
    mans = [os.path.join(F["fx"], "stageA", "MANIFEST.json"), os.path.join(F["zero"], "MANIFEST.json")]
    rc, o = sub([os.path.join(TC, "c1_av2_scene_map_v01.py"), "--stageA-manifests"] + mans + ["--out", F["scene_json"]], cwd=TC)
    assert rc == 0 and "SCENE MAP V01 DONE" in o, o[-600:]
    out["m4_scene_map_built"] = "c1_av2_scene_map_v01 in the tree (50 units)"

    def prov(name, readme, manifests):
        p = os.path.join(T, "70_TESTS", "prov", name)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        rc_, o_ = sub(["-c", PROV_RUN, TC, readme, p] + manifests, cwd=TC)
        assert rc_ == 0 and "PROV_RECORD" in o_, o_[-1200:]
        return p
    F["prov"] = prov("provenance_probe_readme.json", F["readme"], mans)
    prov_other = prov("provenance_other_readme.json", os.path.join(TC, os.path.basename(README)), mans)
    prov_fx_only = prov("provenance_fx_only.json", F["readme"], mans[:1])
    good = json.load(open(F["prov"]))
    prov_failed = wj(os.path.join(T, "70_TESTS", "prov", "provenance_failed.json"), dict(good, ok=False, status="FAIL"))
    prov_partial = wj(os.path.join(T, "70_TESTS", "prov", "provenance_partial.json"), dict(good, kinds=["exports", "horizon"]))
    out["provenance_record"] = "made for the probe README before the quarantine (kinds %s; a stand-in runner reproduces horizon, ego " \
                               "and ground truth; exports and builders checked by the tool)" % good["kinds"]
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md")
    assert rc != 0 and "quarantine it first" in o, o[-800:]
    out["freeze_before_quarantine"] = "refused"
    qv1 = [os.path.join(TC, "c1_quarantine_v01.py"), "--stageA-manifests"] + mans
    rc, o = sub(qv1, cwd=TC)
    assert rc == 0 and not os.path.exists(F["gt"]) and os.path.exists(F["old_gt"]), o[-600:]
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md")
    assert rc != 0 and "quarantine it first" in o and "av2_val_gt_v01.json" in o, o[-800:]
    out["E2_refusal"] = "c1_quarantine_v01 with the given manifests left the older manifest's ground truth plain; c1_freeze_v07 refused"
    q3 = [os.path.join(TC, "c1_quarantine_v03.py"), "--stageA-manifests", mans[0], "--extra", F["extra"], "--gt-inventory", F["inventory"]]
    before = sorted(os.listdir(QD))
    rc, o = sub(q3 + ["--dry-run"], cwd=TC)
    assert rc == 0 and "DRY RUN" in o and all(os.path.exists(F[k]) for k in ("old_gt", "extra", "stray", "inv_tar")), o[-600:]
    assert sorted(os.listdir(QD)) == before
    rc, o = sub(q3, cwd=TC)
    assert rc == 0 and "QUARANTINE V03 DONE" in o, o[-1500:]
    for k in ("old_gt", "extra", "stray", "inv_tar"):
        assert not os.path.exists(F[k]), k
    assert os.path.exists(F["envc"]), "the copy under 50_CODE/env/ must be left (excluded from the scan)"
    qm = json.load(open(os.path.join(QD, "QUARANTINE_MANIFEST.json")))["members"]
    assert any(m["sha256_decompressed"] == G6.inventory_files(F["inventory"])[1]["sha256"] for m in qm)
    assert any("renamed_copy.bin" in r for m in qm for r in m.get("removed", []))
    assert "50_CODE/env" in o, "the quarantine did not name the folders its scan skipped (m-3)"
    rc, o = sub(q3, cwd=TC)
    assert rc == 0 and "already quarantined" in o, o[-600:]
    out["quarantine_v03"] = "dry run changed nothing; union found the older manifest; --extra and the inventory-only archive quarantined " \
                            "(--gt-inventory); renamed stray copy removed; the copy under 50_CODE/env/ left; skipped folders named; rerun idempotent"
    tam = os.path.join(T, "70_TESTS", "fx_tamper")
    os.makedirs(tam, exist_ok=True)
    open(os.path.join(tam, "gt_t.json"), "w").write("{}")
    wj(os.path.join(tam, "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": os.path.join(tam, "gt_t.json"), "gt_sha256": "0" * 64}})
    rc, o = sub([os.path.join(TC, "c1_quarantine_v03.py"), "--stageA-manifests", os.path.join(tam, "MANIFEST.json")], cwd=TC)
    assert rc != 0 and "differs from the hash" in o and os.path.exists(os.path.join(tam, "gt_t.json")), o[-600:]
    pod = os.path.join(T, "30_DATA", "fx_pod")
    os.makedirs(pod, exist_ok=True)
    open(os.path.join(pod, "gt_pod.json"), "w").write('{"pod": 1}')
    podm = wj(os.path.join(T, "70_TESTS", "fx_pod_manifest", "MANIFEST.json"),
              {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {"gt": "/workspace/W/30_DATA/fx_pod/gt_pod.json",
                                                                         "gt_sha256": G.sha(os.path.join(pod, "gt_pod.json"))}})
    rc, o = sub([os.path.join(TC, "c1_quarantine_v03.py"), "--stageA-manifests", podm], cwd=TC)
    assert rc == 0 and not os.path.exists(os.path.join(pod, "gt_pod.json")), o[-600:]
    out["quarantine_refusals_and_pod"] = "a tampered plain file refused; a pod-recorded path quarantined from 30_DATA"
    X = ["--extra", F["extra"]]
    # ---- R17f N1: a gunzip -k copy inside the quarantine folder
    old_member = [m for m in json.load(open(os.path.join(QD, "QUARANTINE_MANIFEST.json")))["members"] if "av2_val_gt_v01" in m["member"]][0]["member"]
    plant = os.path.join(QD, old_member[:-3])
    with gzip.open(os.path.join(QD, old_member), "rb") as fi, open(plant, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X)
    assert rc != 0 and "not recorded members" in o and os.path.basename(plant) in o, o[-800:]
    rc, o = sub(q3, cwd=TC)
    assert rc == 0 and not os.path.exists(plant), o[-800:]
    qm = json.load(open(os.path.join(QD, "QUARANTINE_MANIFEST.json")))["members"]
    assert any("av2_gt_quarantine_v01/" + os.path.basename(plant) in r for m in qm for r in m.get("removed", []))
    note = os.path.join(QD, "notes.txt")
    open(note, "w").write("a stray entry")
    rc, o = sub(q3, cwd=TC)
    assert rc != 0 and "neither members nor plain copies" in o and os.path.exists(note), o[-600:]
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X)
    assert rc != 0 and "not recorded members" in o, o[-600:]
    os.remove(note)
    out["N1_refusal"] = "a gunzip -k copy inside the quarantine folder: the freeze refused; c1_quarantine_v03 removed it as a plain copy " \
                        "(recorded); any other stray entry there refused by both"
    # ---- R17f N2: an older stage-A folder moved deeper than the search, its ground truth restored
    src_a = os.path.join(T, "30_DATA", "av2_cache_stageA_v01")
    deep = os.path.join(T, "30_DATA", "archive", "l2", "l3", "l4", "av2_cache_stageA_v01")
    os.makedirs(os.path.dirname(deep), exist_ok=True)
    shutil.move(src_a, deep)
    with gzip.open(os.path.join(QD, old_member), "rb") as fi, open(F["old_gt"], "wb") as fo:
        shutil.copyfileobj(fi, fo)
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X)
    assert rc != 0 and "not at its recorded path" in o, o[-800:]
    os.remove(F["old_gt"])
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X)
    assert rc != 0 and "not at its recorded path" in o, o[-800:]
    shutil.move(deep, src_a)
    out["N2_refusal"] = "an older stage-A folder moved deeper than the search: refused with its ground truth restored, and refused again " \
                        "with it removed (the member's manifest is not at its recorded path)"
    # ---- a plain copy of an inventory-only file
    cp = os.path.join(T, "60_RESULTS", "stray2", "renamed_archive.bin")
    os.makedirs(os.path.dirname(cp), exist_ok=True)
    inv_member = [m for m in qm if m["sha256_decompressed"] == G6.inventory_files(F["inventory"])[1]["sha256"]][0]["member"]
    with gzip.open(os.path.join(QD, inv_member), "rb") as fi, open(cp, "wb") as fo:
        shutil.copyfileobj(fi, fo)
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X)
    assert rc != 0 and "plain copies of recorded ground truth" in o and "renamed_archive.bin" in o, o[-800:]
    os.remove(cp)
    out["inventory_copy_refusal"] = "a renamed plain copy of an inventory-only archive refused"
    # ---- m-6, m-2, 47(j)
    nob = wj(os.path.join(T, "70_TESTS", "fx_nobuilder", "MANIFEST.json"), {"stage": "A", "dataset": "av2", "scenes": {}, "inputs": {}})
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X, manifests=mans + [nob])
    assert rc != 0 and "builder_sha256" in o and "48b m-6" in o, o[-600:]
    out["m6_refusal"] = "an AV2 stage-A manifest without builder_sha256 refused"
    base_roles = dict(F["roles"], gt_inventory=[F["inventory"]])
    for name, pv, msg in (("failed", prov_failed, "not a success record"), ("partial", prov_partial, "made without the checks"),
                          ("other_readme", prov_other, "made for another README"), ("not_covering", prov_fx_only, "does not cover")):
        plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X, roles=dict(base_roles, provenance=[pv]))
        assert rc != 0 and msg in o, (name, o[-600:])
        out["m2_provenance_" + name] = "refused"
    for r_ in ("port_equiv", "provenance", "gt_inventory", "freeze_record"):
        plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X, drop=(r_,))
        assert rc != 0 and "Choice 47j" in o and "data:" + r_ in o, (r_, o[-600:])
    out["47j_missing_role"] = "a freeze without data:port_equiv, data:provenance or data:gt_inventory refused"
    out["51a_missing_freeze_record"] = "an AV2 freeze without data:freeze_record refused (D16 v32 Choice 51a; a stand-in file in the copy tree)"
    # ---- 48(c): the dry run on the tree writes nothing
    lt = listing(T)
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X + ["--dry-run"])
    assert rc == 0 and "C1 FREEZE V07 DRY RUN" in o and "nothing written" in o, o[-1500:]
    assert listing(T) == lt and not os.path.exists(proto("C1_PLAN_HASH_LOG.txt"))
    out["48c_dry_run"] = "every check passed; no file in the tree created or changed (plan, sidecar, log, tests)"
    plan1, (rc, o) = tree_freeze(T, F, "PLAN_1.md", X)
    assert rc == 0 and "C1 FREEZE V07 DONE" in o, o[-1500:]
    txt = open(plan1, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    assert "C1_FREEZE_LOG_SHA256=absent" in txt and "plain_matches" in txt and "scene.json (Choice 44f m4)" in txt
    assert "# scan skipped (Choice 48b m-3)" in txt and "50_CODE/env" in txt and '"gt_inventory_files": 2' in txt
    assert len(re.findall(r"^data:port_equiv  ", txt, re.M)) == 2 and "AV2 data roles and provenance" in txt
    assert len(re.findall(r"^data:freeze_record  ", txt, re.M)) == 1
    out["freeze_after_quarantine"] = "done; five blocks once each; ground truth (members, inventory files), skipped folders, AV2 data roles " \
                                     "(data:port_equiv twice) and the provenance check recorded"
    fx, p2 = F["fx"], F["p2"]
    meta, hz, w0, e0 = os.path.dirname(F["scene_json"]), os.path.join(fx, "horizon.jsonl.gz"), os.path.join(fx, "worker0"), os.path.join(fx, "e0_plan.json")
    folds = os.path.join(fx, "folds_av2.json")
    member = os.path.join(QD, "gt.json.gz")
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
           "predarm_v07": [os.path.join(TC, "c1_predarm_v07.py"), "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", os.path.join(p2, "folds.json"),
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
    plan2, (rc, o) = tree_freeze(T, F, "PLAN_2.md", ["--amend", "tree probe amendment (only exempt run-log lines)"] + X)
    assert rc == 0 and "C1 FREEZE V07 DONE" in o, o[-1500:]
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
    plan3, (rc, o) = tree_freeze(T, F, "PLAN_3.md", ["--amend", "after the deposit"] + X)
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
    an = lambda k: [os.path.join(TC, "c1_analyse_v09.py"), "--config", F["config"], "--out", os.path.join(T, "70_TESTS", "an%d.json" % k),  # noqa: E731
                    "--decision", os.path.join(T, "70_TESTS", "dec%d.json" % k), "--c1", "--plan", plan2]
    rc, o = sub(an(1), cwd=TC)
    assert rc == 0 and "C1 ANALYSIS V09 DONE" in o, o[-1500:]
    d1 = json.load(open(os.path.join(T, "70_TESTS", "dec1.json")))
    assert d1["tables"]["h8"]["ok"] and "h8" in d1["binding"]["tables_in_run_log"] and d1["binding"]["run_log_at_start"]["lines"] >= 4, d1["tables"]
    assert d1["hypotheses"]["Q1"]["status"] == "not tested" and d1["binding"]["run_log_at_start"]["run_log_sha256"]
    assert "H9_floor" in d1 and "V_t_reasons" in d1 and not any(str(x).startswith("Q1") for x in d1["missing_inputs"])
    recs3, _ = G.read_run_log(proto("C1_RUN_LOG.txt"))
    assert recs3[-1]["event"] == "done" and recs3[-1]["role"] == "entry:c1_analyse" and recs3[-2]["role"] == "entry:c1_analyse"
    t8x = dict(t8, tampered_after_the_run=True)
    json.dump(t8x, open(h8o, "w"), indent=1)
    rc, o = sub(an(2), cwd=TC)
    assert rc == 0 and "C1 ANALYSIS V09 DONE" in o, o[-1500:]
    d2 = json.load(open(os.path.join(T, "70_TESTS", "dec2.json")))
    assert d2["tables"]["h8"]["ok"] is False and "no 'done' line" in (d2["tables"]["h8"]["why"] or ""), d2["tables"]["h8"]
    out["m1_analysis"] = "c1_analyse_v09 on AV2 records the run log and accepts the logged H8 table; after the table's bytes change it has no " \
                         "'done' line and is not provenance-valid; Q1 not tested and never a missing input; the v09 blocks present"
    os.remove(dep)
    plan3, (rc, o) = tree_freeze(T, F, "PLAN_3.md", ["--amend", "R17e E7: record deleted after an H8 outcome"] + X)
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
    plan4, (rc, o) = tree_freeze(T, F, "PLAN_4.md", ["--amend", "after stage B"] + X)
    assert rc != 0 and "a stage B has been built" in o, o[-600:]
    out["amend_after_stageB"] = "refused"
    out["stageB_v06"] = "writes only 30_DATA/av2_cache_stageB_<tag>/; one stage-B log line; chained start and done lines; deposit recorded"
    return out


# ------------------------------------------------------------------------------------------------------------------------------ rehearsal
NEW_BLOCKS = ("Mstar_simultaneous_upper_bounds", "V_t_reasons", "Mstar_zero_se_families", "H9_floor", "Mstar_power_families",
              "comparator_power_families", "zero_se_effects", "criteria", "S_decision_forms", "H9_descriptive")


def decision_diff(d8, d9):
    """v08's decision against v09's on the same inputs: every difference in the decision fields, and whether a v09 rule explains it."""
    diffs = []
    for k in ("C1_verdict", "gate_H1", "nogo_reasons", "not_tested", "missing_inputs", "failed_conditions"):
        if json.dumps(d8.get(k), sort_keys=True, default=str) != json.dumps(d9.get(k), sort_keys=True, default=str):
            diffs.append({"key": k, "v08": d8.get(k), "v09": d9.get(k)})
    for c in sorted(set(d8["claims_status"]) | set(d9["claims_status"])):
        a, b = d8["claims_status"].get(c), d9["claims_status"].get(c)
        if a != b:
            diffs.append({"key": "claims_status." + c, "v08": a, "v09": b})
    fs8 = {k: v.get("label") for k, v in d8.get("family_S", {}).items()}
    fs9 = {k: v.get("label") for k, v in d9.get("family_S", {}).items()}
    if fs8 != fs9:
        diffs.append({"key": "family_S", "v08": fs8, "v09": fs9})
    for h in sorted(set(d8["hypotheses"]) | set(d9["hypotheses"])):
        b8 = (d8["hypotheses"].get(h) or {}).get("by_tracker") or {}
        b9 = (d9["hypotheses"].get(h) or {}).get("by_tracker") or {}
        if not isinstance(b8, dict) or not isinstance(b9, dict):
            continue
        for t in sorted(set(b8) | set(b9)):
            x8, x9 = b8.get(t), b9.get(t)
            if not isinstance(x8, dict) or not isinstance(x9, dict):
                continue
            for key, extra in (("V", "in_V_hk1c_only"), ("VJ", "VJ_hk1c_only")):
                if key in x8 or key in x9:
                    if x8.get(key) != x9.get(key):
                        added = sorted(set(x9.get(key) or []) - set(x8.get(key) or []))
                        removed = sorted(set(x8.get(key) or []) - set(x9.get(key) or []))
                        diffs.append({"key": "%s.%s.%s" % (h, t, key), "v08": x8.get(key), "v09": x9.get(key), "added": added, "removed": removed,
                                      "explained": not removed and set(added) <= set(x9.get(extra) or [])})
                    elif x8.get("met") != x9.get("met"):
                        diffs.append({"key": "%s.%s.met" % (h, t), "v08": x8.get("met"), "v09": x9.get("met"), "explained": False})
    return diffs


def explain(diffs, d9):
    """Each difference must come from 47(e)/49(c) (a comparator kept that fails only HK1c or the pooled bound, and the statuses that
    depend on it) or the H9 floor wording (49l)."""
    changed_v = {x["key"].split(".")[0] for x in diffs if x["key"].count(".") == 2 and x.get("explained")}
    bad = []
    for x in diffs:
        k = x["key"]
        if k.count(".") == 2:
            ok = x.get("explained", False)
        elif k == "claims_status.H9":
            ok = x["v08"] == "does not hold" and x["v09"] == "does not hold: floor not met" and \
                any(v.get("floor_met") is False for v in d9["H9_floor"]["by_tracker"].values())
        elif k.startswith("claims_status."):
            ok = k.split(".", 1)[1] in changed_v
        else:
            ok = bool(changed_v)   # a verdict, gate, family or reason list can move only through a changed V_t
        x["explained"] = bool(ok)
        if not ok:
            bad.append(k)
    return bad


def t_rehearsal():
    reh = STATE.get("rehearsal")
    if not reh:
        return {"skipped": "no --rehearsal"}
    import c1_analyse_v09 as A9
    plan = os.path.join(reh, "MOCK_C1_PLAN_v08.md")
    log = os.path.join(reh, "C1_PLAN_HASH_LOG_REHEARSAL.txt")
    side, fr = G.frozen_plan(plan, "nuscenes", log)
    txt = open(plan, encoding="utf-8").read()
    for b in ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS"):
        assert txt.count(b + "_BEGIN\n") == 1, b
    dec = json.load(open(os.path.join(reh, "c1_decision_rehearsal_v08.json")))
    assert dec["hypotheses"]["Q1"]["status"] == "not tested" and dec["hypotheses"]["Q1"]["reasons"] == A9.Q1_REASONS
    assert all(b in dec for b in NEW_BLOCKS) and not any(str(x).startswith("Q1") for x in dec["missing_inputs"])
    steps = [json.loads(l) for l in open(os.path.join(reh, "steps.jsonl"))]
    fz = [s["key"] for s in steps if s["key"].startswith("c1_freeze_v07.py") and "MOCK_C1_PLAN_v08" in s["key"]][0].split(" ")
    p2 = os.path.join(OUT, "SECOND_PLAN.md")
    open(p2, "w").write("# second plan\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n")
    fz[fz.index("--plan") + 1] = p2
    fz[fz.index("--results-dir") + 1] = os.path.join(OUT, "results2")
    rc, o = sub(fz)
    assert rc != 0 and "one freeze only" in o, o[-600:]
    import c1_rules_v01 as Rr
    assert dec["criteria"]["constants"] == json.loads(json.dumps(Rr.CONSTANTS)) and dec["criteria"]["levels"]["removal_V_t"] == Rr.LEVEL_REMOVAL_V
    ubw = dec["Mstar_simultaneous_upper_bounds"]["by_route"].get("within_lt3d") or {}
    assert ubw.get("t1") and ubw.get("t3"), "M*'s upper bounds are missing from the decision (47f)"
    pfw = dec["Mstar_power_families"]["by_route"].get("within_lt3d") or {}
    assert pfw.get("t1"), "M*'s descriptive power families are missing"
    fb1 = (dec["hypotheses"].get("H1") or {}).get("by_tracker") or {}
    assert all(abs(v["level"] - (1 - 0.0125 / max(len(v["V"]), 1))) < 1e-12 for v in fb1.values() if isinstance(v, dict) and "V" in v)
    assert dec["claims_status"]["H9"] == "descriptive" and "H9_descriptive" in dec and "S_decision_forms" in dec
    an = json.load(open(os.path.join(reh, "c1_analysis_rehearsal_v08.json")))
    jl = (an["k8"]["within_lt3d"]["t1"].get("joint_loss") or {}).get("validity_by_arm") or {}
    if jl:
        assert jl["MstarJx"]["levels"]["flag"] == 0.95 and abs(jl["B3"]["levels"]["flag"] - Rr.LEVEL_REMOVAL_VJ) < 1e-15
    vb = an["k8"]["within_lt3d"]["t1"]["validity_by_arm"]
    assert vb["Mstar"]["levels"]["flags"] == 0.95 and abs(vb["B0"]["levels"]["flags"] - Rr.LEVEL_REMOVAL_V) < 1e-15
    assert vb["Mstar"]["power_rule"]["datasets"] == 2000 and vb["B0a1"]["power_rule"]["datasets"] == 500
    out = {"second_freeze": "refused", "rehearsal_plan_is_latest": side[:12], "blocks": "five, each once", "Q1": "not tested with 44(d)'s reasons",
           "H9": dec["claims_status"]["H9"], "H9_floor": dec["H9_floor"]["by_tracker"], "criteria": "constants and levels recorded; M*'s upper "
           "bounds and power families present; Form B at 1 - 0.0125/|V_t|; flags at 0.95 (M*) and 1 - 0.0125/9 (comparators); H3's joint "
           "flags at 0.95 (M*Jx) and 1 - 0.0025/3 (comparators); power datasets 2000 (decision arms) and 500 (descriptive arms)",
           "V_t": {r: {t: v.get("V_t") for t, v in by.items()} for r, by in dec["V_t_reasons"]["by_route"].items()},
           "claims_status": dec["claims_status"], "C1_verdict": dec["C1_verdict"]}
    d8p = os.path.join(W, "70_TESTS", "c1_v01", "rehearsal150_v08", "c1_decision_rehearsal_v06.json")
    if os.path.exists(d8p):   # descriptive: the criteria change levels, families and V_t, so differences are expected and listed
        d8 = json.load(open(d8p))
        out["vs_rehearsal150_v08_descriptive"] = decision_diff(d8, dec)
    return out


GROUPS = (("G5", t_g5), ("RUNLOG", t_runlog), ("SWEEP", t_sweep), ("ME", t_me), ("MD", t_md), ("SCENEMAP", t_scenemap), ("FRZ7", t_frz7),
          ("GTINV", t_gtinv), ("PROV", t_prov), ("AN9", t_an9), ("CRIT", t_crit), ("DEVREPLAY", t_devreplay), ("PC5", t_pc5), ("Q3", t_q3),
          ("TREE", t_tree), ("REHEARSAL", t_rehearsal), ("LEGACY", t_legacy))
# Parallel plan (the lead's speed request of 5 Nov 2026). Every group runs in its own worker process (python -B this file --worker
# <group>), in its own output folder under OUT, exactly as in a serial run. POOL groups run at most MAX_WORKERS at a time, longest first.
# ALONE groups run afterwards, one at a time, with nothing else running: SWEEP, and LEGACY (which runs test_c1_v11's SWEEP), create a
# c1_gt_<pid>_* folder for a process that has just ended and expect guard() to sweep it as stale; a process spawned at the same moment by
# another group could be given that recycled process ID, so the folder would look live. Running them alone keeps the serial conditions.
MAX_WORKERS = 3
POOL = ("TREE", "FRZ7", "PC5", "CRIT", "PROV", "GTINV", "ME", "MD", "Q3", "AN9", "G5", "RUNLOG", "SCENEMAP", "DEVREPLAY", "REHEARSAL")
ALONE = ("SWEEP", "LEGACY")


def run_one(name):
    """One group in this process (worker mode); returns its record."""
    fn = dict(GROUPS)[name]
    t1 = time.time()
    try:
        return {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
    except Exception:
        return {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}


def spawn(name):
    """One group in its own worker process; its record and log are written under OUT/parallel/."""
    pd = os.path.join(OUT, "parallel")
    os.makedirs(pd, exist_ok=True)
    rp, lp = os.path.join(pd, name + ".json"), os.path.join(pd, name + ".log")
    for p in (rp, lp):
        if os.path.exists(p):
            os.remove(p)
    cmd = [PY, "-B", os.path.abspath(__file__), "--worker", name] + (["--rehearsal", STATE["rehearsal"]] if STATE.get("rehearsal") else [])
    t1 = time.time()
    with open(lp, "w") as lf:
        r = subprocess.run(cmd, stdout=lf, stderr=subprocess.STDOUT, text=True, cwd=C1)
    if os.path.exists(rp):
        rec = json.load(open(rp))
    else:
        rec = {"pass": False, "error": "the worker wrote no record (exit %d); see %s" % (r.returncode, G.rel(lp)), "seconds": round(time.time() - t1, 1)}
    rec["worker"] = {"exit": r.returncode, "log": G.rel(lp), "wall_seconds": round(time.time() - t1, 1)}
    return name, rec


def main():
    from concurrent.futures import ThreadPoolExecutor, as_completed
    argv = sys.argv[1:]
    if "--rehearsal" in argv:
        i = argv.index("--rehearsal")
        STATE["rehearsal"] = os.path.abspath(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if "--worker" in argv:
        name = argv[argv.index("--worker") + 1]
        rec = run_one(name)
        print(name, "PASS" if rec["pass"] else "FAIL", rec["seconds"], "s", flush=True)
        if not rec["pass"]:
            print(rec["error"][-2500:], flush=True)
        json.dump(rec, open(os.path.join(OUT, "parallel", name + ".json"), "w"), indent=1, default=str)
        return
    only = None
    if "--groups" in argv:
        i = argv.index("--groups")
        only = set(argv[i + 1].split(","))
        argv = argv[:i] + argv[i + 2:]
    workers = MAX_WORKERS
    if "--workers" in argv:
        i = argv.index("--workers")
        workers = min(MAX_WORKERS, max(1, int(argv[i + 1])))
        argv = argv[:i] + argv[i + 2:]
    out_path = argv[0] if argv else os.path.join(OUT, "c1_tests_v12.json")
    os.makedirs(OUT, exist_ok=True)
    skip = freeze_skip()
    before = real_state()
    assert not before["deposit_record"] and not before["stage_B_log"] and before["run_log_nonexempt_lines"] == 0, \
        "the real tree holds a deposit record, a stage-B log or a non-exempt run-log line (Choice 44c): %s" % before
    if not skip:
        assert not before["hash_log"], "the real tree holds a C1 hash log, and this suite was not run by the freeze with its hash"
    t0 = time.time()
    res, ok = {"tested_files_sha256": {f: G.sha(os.path.join(C1, f)) for f in TESTED}, "python": sys.version, "versions": G.versions(),
               "readme": os.path.basename(README), "readme_sha256": G.sha(README),
               "parallel": {"max_workers": workers, "pool": [g for g in POOL if only is None or g in only],
                            "alone_afterwards": [g for g in ALONE if only is None or g in only],
                            "rule": "one group per worker process, each in its own output folder; SWEEP and LEGACY alone (process-ID reuse)"},
               "freeze_skip": skip, "C1_FREEZE_LOG_SHA256": os.environ.get("C1_FREEZE_LOG_SHA256"), "real_tree_before": before}, True
    assert sorted(POOL + ALONE) == sorted(dict(GROUPS)), "every group is in exactly one phase"

    def record(name, rec):
        nonlocal ok
        res[name] = rec
        ok = ok and rec["pass"]
        print(name, "PASS" if rec["pass"] else "FAIL", rec["seconds"], "s", flush=True)
        if not rec["pass"]:
            print(str(rec.get("error"))[-2500:], flush=True)
        json.dump(res, open(out_path + ".partial", "w"), indent=1, default=str)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(spawn, g) for g in POOL if only is None or g in only]
        for f in as_completed(futs):
            record(*f.result())
    for g in ALONE:
        if only is None or g in only:
            record(*spawn(g))
    after = real_state()
    res["real_tree_after"] = after
    if after != before:
        ok = False
        res["real_tree_changed"] = True
    res["tested_files_sha256_at_end"] = {f: G.sha(os.path.join(C1, f)) for f in TESTED}
    if res["tested_files_sha256_at_end"] != res["tested_files_sha256"]:
        ok = False
        res["files_changed_during_tests"] = True
    if only is not None:
        res["verdict"] = ("PARTIAL_PASS" if ok else "FAIL") + " (groups %s only)" % sorted(only)
    else:
        res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_path, "w"), indent=1, default=str)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
