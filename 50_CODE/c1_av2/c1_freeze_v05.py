#!/usr/bin/env python3
"""C1 freeze v05 (Claude line, c1_freeze_v05, 4 Nov 2026) = c1_freeze_v04 (kept, imported: generators on the archived originals, the
Choice 36 edit check, the stage-B folder search, the child-folds and builder checks; c1_freeze_v03's README parser and checks) with D16
v21 Choice 42 (R17d B1, B2, M1, m3, m4) and Choice 41(a):
  * B2 quarantine: refused while any plain prepared ground-truth file named by a given AV2 stage-A manifest exists (by its recorded path
    or the same path under this workspace's 30_DATA): quarantine it first with c1_quarantine_v01.
  * M1 one freeze: refused if 40_PROTOCOL/C1_STAGE_B_LOG.txt exists (a stage B was built); --amend is also refused once the deposit
    record 40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt exists. The depth-limited folder search for stage-B manifests stays.
  * M1 tests: every README "test" file is run with C1_FREEZE_LOG_SHA256 = the SHA-256 of the hash log being frozen into ("absent" if it
    does not exist yet); the suites skip their "real C1 log absent" assertions only when that variable equals the real log's hash, so a
    legitimate pre-stage-B amendment can pass its own tests. FROZEN_TESTS records the variable's value.
  * m3: an AV2 freeze must bind scene.json as data:scene_json.
  * m4: FROZEN_ENV_TPP (python, numpy, torch of the tpp38 environment, read by running --tpp-python, or given by --tpp-env).
  * 41(a): the plan may hold only the empty FROZEN_HASHES and FROZEN_ROLES blocks; after the freeze each of the five blocks
    (HASHES, ROLES, ENV, ENV_TPP, TESTS) appears exactly once (asserted).
  * the new generators (stage B v05, items v07, stage A v02) and entry roles (entry:c1_quarantine, entry:c1_qcnet_summary) are required.
Usage: as c1_freeze_v04, plus [--tpp-python <tpp38 python>] [--tpp-env python=..,numpy=..,torch=..]
"""
import argparse
import datetime
import json
import os
import subprocess
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v04 as G  # noqa: E402
import c1_freeze_v04 as F4  # noqa: E402

F3, W = F4.F3, G.W
F3.ENTRY_REQUIRED = tuple(F3.ENTRY_REQUIRED) + ("entry:c1_quarantine", "entry:c1_qcnet_summary")
F4.GENS = tuple(F4.GENS) + (("50_CODE/c1_av2/tests/make_av2_stageB_v05.py", "make", "50_CODE/av2/av2_cache_stageB_v04.py", "50_CODE/av2/av2_cache_stageB_v05.py"),
                            ("50_CODE/c1_av2/tests/make_k8_items_v07.py", "make", "50_CODE/k8/k8_items_v06.py", "50_CODE/k8/k8_items_v07.py"),
                            ("50_CODE/c1_av2/tests/make_av2_stageA_v02.py", "make", "50_CODE/av2/av2_cache_stageA_v01.py", "50_CODE/av2/av2_cache_stageA_v02.py"))
BLOCKS = ("FROZEN_HASHES", "FROZEN_ROLES", "FROZEN_ENV", "FROZEN_ENV_TPP", "FROZEN_TESTS")
TPP_PY = os.path.join(W, "50_CODE", "env", "tpp38", "Scripts", "python.exe")


def tpp_versions(a):
    if a.tpp_env:
        d = dict(x.split("=", 1) for x in a.tpp_env.split(","))
        return {k: d[k] for k in ("python", "numpy", "torch")}
    code = "import platform, json, numpy\ntry:\n import torch; t = torch.__version__\nexcept ImportError:\n t = None\n" \
           "print(json.dumps({'python': platform.python_version(), 'numpy': numpy.__version__, 'torch': t}))"
    r = subprocess.run([a.tpp_python, "-I", "-c", code], capture_output=True, text=True)
    assert r.returncode == 0, "cannot read the tpp38 versions from %s: %s" % (a.tpp_python, r.stderr[-400:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def run_tests(bound, out_dir, log_sha):
    res = []
    os.makedirs(out_dir, exist_ok=True)
    env = dict(os.environ, C1_FREEZE_LOG_SHA256=log_sha)
    for h, p, r in bound:
        if r != "test":
            continue
        out = os.path.join(out_dir, os.path.basename(p)[:-3] + "_freeze.json")
        t0 = datetime.datetime.utcnow()
        x = subprocess.run([sys.executable, "-B", os.path.join(W, p), out], capture_output=True, text=True, cwd=C1, env=env)
        open(out[:-5] + ".log", "w").write(x.stdout[-20000:] + "\n" + x.stderr[-5000:])
        assert x.returncode == 0 and "ALL_PASS" in x.stdout, "a bound test did not print ALL_PASS: %s\n%s" % (p, (x.stdout + x.stderr)[-1500:])
        res.append({"test": p, "sha256": h, "verdict": "ALL_PASS", "out_sha256": G.sha(out) if os.path.exists(out) else None,
                    "seconds": round((datetime.datetime.utcnow() - t0).total_seconds(), 1)})
    assert res, "no bound test file: no freeze (R17c m4)"
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    for x in ("--plan", "--readme", "--results-dir", "--folds", "--split", "--config"):
        ap.add_argument(x, required=True)
    ap.add_argument("--transfer-fits", nargs=2, required=True)
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--folds-val150", default=None)
    ap.add_argument("--folds-train225", default=None)
    ap.add_argument("--data", nargs="*", default=[])
    ap.add_argument("--hash-log", default=None)
    ap.add_argument("--data-root", default=None)
    ap.add_argument("--amend", default=None)
    ap.add_argument("--test-out-dir", default=None)
    ap.add_argument("--tpp-python", default=TPP_PY)
    ap.add_argument("--tpp-env", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    a.test = []
    log = a.hash_log or G.CANONICAL["C1"]
    canonical = os.path.abspath(log) == os.path.abspath(G.CANONICAL["C1"])
    if a.data_root is not None:
        assert not canonical, "--data-root only for a rehearsal's own log"
    assert not os.path.exists(G.STAGE_B_LOG), "a stage B has been built (%s): no freeze and no amendment (Choice 42c)" % G.rel(G.STAGE_B_LOG)
    sb = F4.stage_b_manifests(a.data_root or os.path.join(W, "30_DATA"))
    assert not sb, "a stage-B manifest exists, so the plan can no longer be frozen or amended: %s (R17c M1; Choice 39c)" % sb[:3]
    lines = G.log_lines(log) if os.path.exists(log) else []
    if lines:
        assert a.amend, "the hash log already holds a plan line: one freeze only; an amendment needs --amend \"<reason>\" (Choice 39c)"
        assert not os.path.exists(G.DEPOSIT_RECORD), "the plan has been deposited (%s): no amendment (Choice 42a)" % G.rel(G.DEPOSIT_RECORD)
    plain = G.plain_gt_files(a.stageA_manifests)
    assert not plain, "plain prepared ground truth named by a stage-A manifest exists: %s; quarantine it first with c1_quarantine_v01 (Choice 42b)" % plain[:3]
    txt0 = open(a.plan, encoding="utf-8").read()
    extra = [b for b in BLOCKS[2:] if b + "_BEGIN" in txt0]
    assert not extra, "the plan already holds %s: only the empty FROZEN_HASHES and FROZEN_ROLES blocks may be drafted (Choice 41a)" % extra
    F3.check_generators = F4.check_generators
    bound, superseded, data, log3, gens = F3.check(a)
    edits = F4.check_main_edits()
    for role, p in (("folds_val150", a.folds_val150), ("folds_train225", a.folds_train225)):
        if p:
            ch, par = json.load(open(p)), json.load(open(a.folds))
            assert ch.get("parent_sha256") == G.sha(a.folds), "%s does not name the --folds file as its parent" % role
            assert all(par["fold_of_log"].get(u) == f for u, f in ch["fold_of_log"].items()), "%s is not a restriction of --folds" % role
            src = "val" if role == "folds_val150" else "held_out_train"
            assert set(ch["fold_of_log"]) == {u for u, s in par["source_of_log"].items() if s == src}, "%s is not the parent's %s units" % (role, src)
            data.append((role, p))
    if G.folds_dataset(json.load(open(a.folds))) == "av2":
        assert any(r == "data:scene_json" for r, _ in data), "an AV2 freeze binds scene.json as data:scene_json (R17d m3)"
    builders = {h for h, p, r in bound if r == "builder"}
    m8 = {}
    for p in a.stageA_manifests:
        bh = (json.load(open(p)).get("inputs") or {}).get("builder_sha256")
        assert bh is None or bh in builders, "stage-A manifest %s was built by %s..., not a bound builder (R17c m8)" % (G.rel(p), str(bh)[:12])
        m8[G.rel(p)] = bh or "not recorded (nuScenes cache)"
    tv = tpp_versions(a)
    log_sha = G.sha(log) if os.path.exists(log) else "absent"
    tests = run_tests(bound, a.test_out_dir or os.path.join(os.path.dirname(os.path.abspath(a.plan)), "freeze_tests"), log_sha)
    hl, rl, _ = F3.freeze(argparse.Namespace(plan=a.plan, readme=a.readme, dry_run=True), bound, superseded, data, log)
    hl[0] = hl[0].replace("c1_freeze_v03", "c1_freeze_v05")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    v = G.versions()
    env = ["# versions asserted by c1_guard_v03/v04 (R17c m5)"] + ["%s  %s" % (k, v[k]) for k in ("python", "numpy", "scipy")]
    envt = ["# tpp38 versions compared by c1_predarm_v05 with the tpp_keys_v03 / tpp_run_v03 wrapper records (R17d m4)"] + \
           ["%s  %s" % (k, tv[k]) for k in ("python", "numpy", "torch")]
    tl = ["# every bound test run by c1_freeze_v05, %s UTC, with C1_FREEZE_LOG_SHA256=%s (R17c m4; Choice 42c): <test sha256>  <path>  <verdict>  <output sha256>" % (now, log_sha)]
    tl += ["%s  %s  %s  %s" % (t["sha256"], t["test"], t["verdict"], t["out_sha256"]) for t in tests]
    xl = ["# generators (on archived originals where edited): %d checked" % len(gens)] + ["# " + g for g in gens]
    xl += ["# Choice 36 main()-only edits verified: %s" % ", ".join("%s %s" % (f, h[:12]) for f, h in sorted(edits.items()))]
    xl += ["# stage-A builders (m8): %s" % json.dumps(m8), "# plain prepared ground truth named by the stage-A manifests: none (Choice 42b)"]
    if a.amend:
        xl += ["# AMENDMENT of the frozen plan (%s UTC): %s" % (now, a.amend)]
    head, rest = txt0.split("FROZEN_HASHES_BEGIN", 1)
    _, tail = rest.split("FROZEN_HASHES_END", 1)
    if "FROZEN_ROLES_BEGIN" in tail:
        tail = tail.split("FROZEN_ROLES_BEGIN", 1)[0] + tail.split("FROZEN_ROLES_END", 1)[1]
    blocks = ("FROZEN_HASHES_BEGIN\n%s\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\n%s\nFROZEN_ROLES_END\n\nFROZEN_ENV_BEGIN\n%s\nFROZEN_ENV_END\n\n"
              "FROZEN_ENV_TPP_BEGIN\n%s\nFROZEN_ENV_TPP_END\n\nFROZEN_TESTS_BEGIN\n%s\n%s\nFROZEN_TESTS_END") % (
        "\n".join(hl), "\n".join(rl), "\n".join(env), "\n".join(envt), "\n".join(tl), "\n".join(xl))
    new = head + blocks + tail
    for b in BLOCKS:
        assert new.count(b + "_BEGIN\n") == 1 and new.count(b + "_END") == 1, "block %s does not appear exactly once (Choice 41a)" % b
    if a.dry_run:
        print("C1 FREEZE V05 DRY RUN: nothing written (%d hash lines, %d tests ALL_PASS)" % (len(hl), len(tests)))
        return None
    with open(a.plan, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    h = G.sha(a.plan)
    with open(a.plan[:-3] + ".sha256" if a.plan.endswith(".md") else a.plan + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.plan)))
    with open(log, "a") as f:
        f.write("%s  %s  %s %s UTC by c1_freeze_v05 (%d bound files, %d tests ALL_PASS)\n" % (h, G.rel(a.plan), "AMENDED" if a.amend else "frozen",
                                                                                       now, len(hl) - 1, len(tests)))
    if a.amend:
        dl = F4.DEV_LOG if canonical else os.path.join(os.path.dirname(os.path.abspath(log)), "C1_DEVIATION_LOG_REHEARSAL.md")
        with open(dl, "a", encoding="utf-8") as f:
            f.write("\n## Amendment %s UTC\n\n- New plan: `%s` (sha256 %s)\n- Previous latest line: `%s`\n- Reason: %s\n- Tests run with C1_FREEZE_LOG_SHA256=%s\n"
                    % (now, G.rel(a.plan), h, lines[-1][:80], a.amend, log_sha))
    print("generators reproduced: %d; Choice 36 edits verified: %d; tests ALL_PASS: %d" % (len(gens), len(edits), len(tests)))
    print("C1 FREEZE V05 DONE: plan sha256 " + h)
    return h


if __name__ == "__main__":
    main()
