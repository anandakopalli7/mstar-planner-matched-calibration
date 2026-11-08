#!/usr/bin/env python3
"""C1 freeze v06 (Claude line, c1_freeze_v06, 5 Nov 2026) = c1_freeze_v05's procedure (c1_freeze_v04 and c1_freeze_v03 kept, imported:
README parser, generators on the archived originals, Choice 36 edit check, stage-B folder search, child folds, builders, five blocks,
tests with C1_FREEZE_LOG_SHA256) on c1_guard_v05, with D16 v23 Choice 44 (R17e M-A, M-C, M-D, m4):
  * 44(a) M-A, every prepared ground truth. The recorded ground-truth hashes are the union of the stage-A manifests passed, every AV2
    stage-A MANIFEST.json under 30_DATA (or under --data-root for a rehearsal's own log), the quarantine manifest's "extra" members and
    the --extra files. The freeze refuses:
      - a plain file at a recorded path (or the same path under 30_DATA);
      - a plain --extra file;
      - a recorded hash without a quarantine member;
      - ANY plain file in the workspace (or under --data-root) whose SHA-256 equals a recorded hash. The scan hashes files of a
        recorded size only and skips 50_CODE/env/ and the quarantine folder.
    Quarantine with c1_quarantine_v02 first. FROZEN_TESTS records the counts.
  * 44(c) M-C, one freeze. Every freeze is refused while 40_PROTOCOL/C1_STAGE_B_LOG.txt or a stage-B manifest exists, or while the run
    log 40_PROTOCOL/C1_RUN_LOG.txt holds a line from a role other than entry:c1_e0 / c1_folds / c1_freeze (or its chain is broken).
    --amend is also refused if the deposit record exists or if any 30_DATA/av2_cache_stageB_* folder exists.
  * 43(d), 44(d) the frozen config: it holds no "q1" entry (Q1 is not tested in C1), "h8_units" is "folds", and the data roles
    data:e0_plan and data:scene_json are bound. Any other state stops the freeze.
  * m4: on AV2, scene.json (c1_av2_scene_map_v01) must give every fold unit the log its bound stage-A manifests record.
  * required entry roles: c1_freeze_v03's, plus entry:c1_quarantine and entry:tpp_envcheck (entry:c1_qcnet_summary is no longer
    required or bound: Choice 44d). New generators: stage B v06 and items v08.
Usage: as c1_freeze_v05, plus [--extra <prepared ground-truth file ...>]
"""
import argparse
import datetime
import glob
import json
import os
import subprocess
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v05 as G  # noqa: E402
import c1_freeze_v04 as F4  # noqa: E402

F3, W = F4.F3, G.W
F3.ENTRY_REQUIRED = tuple(F3.ENTRY_REQUIRED) + ("entry:c1_quarantine", "entry:tpp_envcheck")
F4.GENS = tuple(F4.GENS) + (("50_CODE/c1_av2/tests/make_av2_stageB_v05.py", "make", "50_CODE/av2/av2_cache_stageB_v04.py", "50_CODE/av2/av2_cache_stageB_v05.py"),
                            ("50_CODE/c1_av2/tests/make_k8_items_v07.py", "make", "50_CODE/k8/k8_items_v06.py", "50_CODE/k8/k8_items_v07.py"),
                            ("50_CODE/c1_av2/tests/make_av2_stageA_v02.py", "make", "50_CODE/av2/av2_cache_stageA_v01.py", "50_CODE/av2/av2_cache_stageA_v02.py"),
                            ("50_CODE/c1_av2/tests/make_av2_stageB_v06.py", "make", "50_CODE/av2/av2_cache_stageB_v05.py", "50_CODE/av2/av2_cache_stageB_v06.py"),
                            ("50_CODE/c1_av2/tests/make_k8_items_v08.py", "make", "50_CODE/k8/k8_items_v07.py", "50_CODE/k8/k8_items_v08.py"))
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


def ground_truth_check(a, root30, scan_root):
    """44(a): the union of recorded ground truths; refused unless every one is quarantined and no plain copy exists anywhere."""
    found = G.av2_stage_a_manifests(root30)
    manifests = sorted({os.path.abspath(p) for p in a.stageA_manifests} | set(found))
    plain = G.plain_gt_files(manifests)
    assert not plain, "plain prepared ground truth named by a stage-A manifest exists: %s; quarantine it first with c1_quarantine_v02 " \
                      "(Choice 44a)" % [G.rel(p) for p in plain][:3]
    members = G.quarantine_members()
    want = {}
    for mp, gp, gs in G.stage_a_gt(manifests):
        want.setdefault(gs, set()).add("%s (stage A %s)" % (gp, G.rel(mp)))
    for m in members:
        if "extra" in (m.get("kinds") or []):
            want.setdefault(m["sha256_decompressed"], set()).add("%s (extra, quarantine manifest)" % ",".join(m.get("sources") or []))
    by_source = {os.path.abspath(s if os.path.isabs(s) else os.path.join(W, s)): m["sha256_decompressed"]
                 for m in members for s in (m.get("sources") or [m.get("source")]) if s}
    for x in a.extra:
        p = os.path.abspath(x if os.path.isabs(x) else os.path.join(W, x))
        assert not os.path.exists(p), "the --extra ground truth %s is still plain: quarantine it first with c1_quarantine_v02 (Choice 44a)" % G.rel(p)
        assert p in by_source, "the --extra ground truth %s is not recorded in the quarantine manifest (Choice 44a)" % G.rel(p)
        want.setdefault(by_source[p], set()).add("%s (--extra)" % G.rel(p))
    by_sha = {m["sha256_decompressed"]: m for m in members}
    missing = [sorted(v) for k, v in want.items() if k not in by_sha]
    assert not missing, "recorded ground truth without a quarantine member: %s; run c1_quarantine_v02 (Choice 44a)" % missing[:3]
    sizes = {G.member_size(by_sha[k]) for k in want}
    matches, hashed = G.scan_plain(scan_root, sizes, set(want))
    assert not matches, "plain copies of recorded ground truth exist: %s; run c1_quarantine_v02 (Choice 44a)" % [G.rel(p) for p, _ in matches][:5]
    return {"manifests_passed": len(a.stageA_manifests), "av2_stage_a_found": [G.rel(p) for p in found], "recorded_hashes": len(want),
            "members": len(members), "scan_root": G.rel(scan_root), "files_hashed_by_size": hashed, "plain_matches": 0}


def config_check(a):
    """43(d), 44(d): the frozen config's entries (checked before anything else is hashed)."""
    cfg = json.load(open(a.config))
    assert "q1" not in cfg, "the frozen config holds a q1 entry: Q1 is not tested in C1 (D16 v23 Choice 44d); remove it"
    assert cfg.get("h8_units") == "folds", "the frozen config must state h8_units = folds (Choice 43d), not %r" % cfg.get("h8_units")
    roles = {"data:" + x.split("=", 1)[0] for x in a.data}
    miss = [r for r in ("data:e0_plan", "data:scene_json") if r not in roles]
    assert not miss, "the freeze must bind %s (Choice 43d)" % miss
    return {"q1": "absent", "h8_units": "folds", "data": ["data:e0_plan", "data:scene_json"]}


def scene_json_check(a, data):
    """m4 on AV2: scene.json gives every fold unit the log its bound (passed) AV2 stage-A manifests record."""
    p = [q for r, q in data if r == "data:scene_json"][0]
    smap = {e["name"]: e["log_token"] for e in json.load(open(p))}
    logs = {}
    for mp in a.stageA_manifests:
        m = json.load(open(mp))
        if G.manifest_dataset(m) == "av2":
            for u, info in (m.get("scenes") or {}).items():
                logs[str(u)] = str(info["log"]) if isinstance(info, dict) and info.get("log") is not None else str(u)
    units = sorted(json.load(open(a.folds))["fold_of_log"])
    bad = [u for u in units if u not in logs or smap.get(u) != logs[u]]
    assert not bad, "scene.json does not give %d fold units their stage-A log, e.g. %s (Choice 44f m4; build it with c1_av2_scene_map_v01)" % (len(bad), bad[:3])
    return {"scene_json": G.rel(p), "units": len(units)}


def main(argv=None):
    ap = argparse.ArgumentParser()
    for x in ("--plan", "--readme", "--results-dir", "--folds", "--split", "--config"):
        ap.add_argument(x, required=True)
    ap.add_argument("--transfer-fits", nargs=2, required=True)
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--folds-val150", default=None)
    ap.add_argument("--folds-train225", default=None)
    ap.add_argument("--data", nargs="*", default=[])
    ap.add_argument("--extra", nargs="*", default=[])
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
    root30 = a.data_root or os.path.join(W, "30_DATA")
    scan_root = a.data_root or W
    assert not os.path.exists(G.STAGE_B_LOG), "a stage B has been built (%s): no freeze and no amendment (Choice 42c)" % G.rel(G.STAGE_B_LOG)
    sb = F4.stage_b_manifests(root30)
    assert not sb, "a stage-B manifest exists, so the plan can no longer be frozen or amended: %s (R17c M1; Choice 39c)" % sb[:3]
    nx = G.nonexempt_lines()
    assert not nx, "the run log %s holds %d line(s) from non-exempt entry points (first: %s): outcomes may have been read, so no freeze " \
                   "and no amendment (Choice 44c)" % (G.rel(G.RUN_LOG), len(nx), nx[0].get("entry"))
    lines = G.log_lines(log) if os.path.exists(log) else []
    if lines:
        assert a.amend, "the hash log already holds a plan line: one freeze only; an amendment needs --amend \"<reason>\" (Choice 39c)"
        assert not os.path.exists(G.DEPOSIT_RECORD), "the plan has been deposited (%s): no amendment (Choice 42a, 44c)" % G.rel(G.DEPOSIT_RECORD)
        sbf = sorted(glob.glob(os.path.join(root30, "av2_cache_stageB_*")))
        assert not sbf, "a stage-B folder exists (%s): no amendment (Choice 44c)" % [G.rel(p) for p in sbf][:3]
    cfgc = config_check(a)
    gtc = ground_truth_check(a, root30, scan_root)
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
    scc = None
    if G.folds_dataset(json.load(open(a.folds))) == "av2":
        scc = scene_json_check(a, data)
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
    hl[0] = hl[0].replace("c1_freeze_v03", "c1_freeze_v06")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    v = G.versions()
    env = ["# versions asserted by c1_guard_v03/v04/v05 (R17c m5); tpp_keys_v03 records are compared with python and numpy here (Choice 44e)"] + \
          ["%s  %s" % (k, v[k]) for k in ("python", "numpy", "scipy")]
    envt = ["# tpp38 versions compared by c1_predarm_v06 with the tpp_run_v03 wrapper records (R17d m4, Choice 44e)"] + \
           ["%s  %s" % (k, tv[k]) for k in ("python", "numpy", "torch")]
    tl = ["# every bound test run by c1_freeze_v06, %s UTC, with C1_FREEZE_LOG_SHA256=%s (R17c m4; Choice 42c): <test sha256>  <path>  <verdict>  <output sha256>" % (now, log_sha)]
    tl += ["%s  %s  %s  %s" % (t["sha256"], t["test"], t["verdict"], t["out_sha256"]) for t in tests]
    xl = ["# generators (on archived originals where edited): %d checked" % len(gens)] + ["# " + g for g in gens]
    xl += ["# Choice 36 main()-only edits verified: %s" % ", ".join("%s %s" % (f, h[:12]) for f, h in sorted(edits.items()))]
    xl += ["# stage-A builders (m8): %s" % json.dumps(m8)]
    xl += ["# ground truth (Choice 44a): %s" % json.dumps(gtc, sort_keys=True)]
    xl += ["# frozen config (Choice 43d, 44d): %s" % json.dumps(cfgc, sort_keys=True)]
    if scc:
        xl += ["# scene.json (Choice 44f m4): %s" % json.dumps(scc, sort_keys=True)]
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
        print("C1 FREEZE V06 DRY RUN: nothing written (%d hash lines, %d tests ALL_PASS)" % (len(hl), len(tests)))
        return None
    with open(a.plan, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    h = G.sha(a.plan)
    with open(a.plan[:-3] + ".sha256" if a.plan.endswith(".md") else a.plan + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.plan)))
    with open(log, "a") as f:
        f.write("%s  %s  %s %s UTC by c1_freeze_v06 (%d bound files, %d tests ALL_PASS)\n" % (h, G.rel(a.plan), "AMENDED" if a.amend else "frozen",
                                                                                       now, len(hl) - 1, len(tests)))
    if a.amend:
        dl = F4.DEV_LOG if canonical else os.path.join(os.path.dirname(os.path.abspath(log)), "C1_DEVIATION_LOG_REHEARSAL.md")
        with open(dl, "a", encoding="utf-8") as f:
            f.write("\n## Amendment %s UTC\n\n- New plan: `%s` (sha256 %s)\n- Previous latest line: `%s`\n- Reason: %s\n- Tests run with C1_FREEZE_LOG_SHA256=%s\n"
                    % (now, G.rel(a.plan), h, lines[-1][:80], a.amend, log_sha))
    print("generators reproduced: %d; Choice 36 edits verified: %d; tests ALL_PASS: %d; ground truth: %d hashes, %d files hashed, 0 plain"
          % (len(gens), len(edits), len(tests), gtc["recorded_hashes"], gtc["files_hashed_by_size"]))
    print("C1 FREEZE V06 DONE: plan sha256 " + h)
    return h


if __name__ == "__main__":
    main()
