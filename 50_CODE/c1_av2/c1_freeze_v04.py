#!/usr/bin/env python3
"""C1 freeze v04 (Claude line, c1_freeze_v04, 4 Nov 2026) = c1_freeze_v03 (kept, imported for its README parser and checks) with R17c
M1, m4, m8, B1 and D16 v18 Choice 39c:
  * ONE freeze: refused if the hash log already holds a plan line, unless --amend "<reason>"; an amendment is refused once any stage-B
    manifest exists under the data root, and is recorded in the deviation log (40_PROTOCOL/C1_DEVIATION_LOG_v01.md for the canonical
    log; a file beside a rehearsal's own log otherwise). c1_guard_v03 accepts only the latest line, so an amendment replaces the plan.
  * refused if any stage-B manifest (a MANIFEST.json saying stage "B") exists under the data root (30_DATA; another root only for a
    rehearsal's own log).
  * every README file in the role "test" is run here (`<python> -B <test> <out>`), must exit 0 and print ALL_PASS; the verdicts, the
    test files' hashes and their outputs' hashes go into a FROZEN_TESTS block of the plan (m4). No test means no freeze.
  * FROZEN_ENV block: the python, numpy and scipy versions (asserted by c1_guard_v03 at run time; m5).
  * m8: each stage-A manifest's inputs.builder_sha256, when recorded, must be the hash of a README file in the role "builder".
  * B1 (Choice 36 rule 3): the generators are checked on the byte-exact ARCHIVED originals where a file was edited, and every edited
    superseded file must equal its archived original plus the recorded main()-only edit (superseded_originals/apply_choice36_main_edits_v01
    --check logic).
  * 38d: optional --folds-val150 / --folds-train225 child files, bound in those roles, verified as restrictions of --folds.
Everything else (roles, README v05 format, latest-version entry points, slot regex, post-freeze artefacts, the 375-log hash-log rule) is
c1_freeze_v03's.
Usage: python -B c1_freeze_v04.py --plan <plan.md> --readme <README_C1_CODE_v06.md> --results-dir <dir> --folds <json> --split <json>
       --transfer-fits <t1> <t3> --stageA-manifests <MANIFEST.json ...> --config <json> [--folds-val150 <json> --folds-train225 <json>]
       [--data name=path ...] [--hash-log <file> [--data-root <dir>]] [--amend "<reason>"] [--test-out-dir <dir>] [--dry-run]
"""
import argparse
import datetime
import gzip
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v03 as G  # noqa: E402
import c1_freeze_v03 as F3  # noqa: E402

W = G.W
ENTRY_REQUIRED = F3.ENTRY_REQUIRED
ROLES = ("module", "generator", "test", "test_module", "builder", "source", "archive", "legacy")
F3.ROLES = ROLES
ARCH = {"50_CODE/c1_av2/": "50_CODE/c1_av2/superseded_originals/", "50_CODE/av2/": "50_CODE/av2/superseded_originals/"}
GENS = F3.GENS + (("50_CODE/c1_av2/tests/make_av2_stageB_v04.py", "make", "50_CODE/av2/av2_cache_stageB_v03.py", "50_CODE/av2/av2_cache_stageB_v04.py"),
                  ("50_CODE/c1_av2/tests/make_k8_items_v06.py", "make", "50_CODE/k8/k8_items_v05.py", "50_CODE/k8/k8_items_v06.py"))
DEV_LOG = os.path.join(W, "40_PROTOCOL", "C1_DEVIATION_LOG_v01.md")


def archived(path):
    """The byte-exact original of an edited superseded file (decompressed in memory), else None."""
    for live, arch in ARCH.items():
        if path.startswith(live) and path.count("/") == live.count("/"):
            gp = os.path.join(W, arch, os.path.basename(path) + ".gz")
            if os.path.exists(gp):
                b = gzip.open(gp, "rb").read()
                sums = dict(l.split(" *")[::-1] for l in open(os.path.join(W, arch, "SHA256SUMS_superseded_originals_v01.txt")).read().splitlines() if l.strip())
                assert hashlib.sha256(b).hexdigest() == sums[os.path.basename(path)], "archive damaged: " + path
                return b.decode("utf-8")
    return None


def text_of(path):
    a = archived(path)
    if a is not None:
        return a
    with open(os.path.join(W, path), encoding="utf-8", newline="") as f:
        return f.read()


def check_generators(bound):
    gens_bound = {p for _, p, r in bound if r == "generator"}
    covered = {g for g, _, _, _ in GENS}
    assert gens_bound <= covered, "generators bound but not checked: %s" % sorted(gens_bound - covered)
    out = []
    for g, fn, src, dst in GENS:
        mod = F3._load(os.path.join(W, g), "gen4_" + os.path.basename(g)[:-3])
        assert getattr(mod, fn)(text_of(src)) == text_of(dst), "%s.%s does not reproduce %s (on the archived originals where edited)" % (g, fn, dst)
        out.append("%s %s -> %s%s" % (os.path.basename(g), fn, dst, " (archived original)" if archived(dst) is not None else ""))
    return out


def check_main_edits():
    spec = importlib.util.spec_from_file_location("apply36", os.path.join(C1, "superseded_originals", "apply_choice36_main_edits_v01.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    res = {}
    for f, (d, anchor, where, ins) in mod.EDITS.items():
        orig = mod.original(d, f)
        live = open(os.path.join(d, f), encoding="utf-8", newline="").read()
        assert live == mod.edited(orig, anchor, where, ins), "a superseded file is not its archived original plus the main()-only edit: " + f
        res[f] = G.sha(os.path.join(d, f))
    return res


def stage_b_manifests(root, max_depth=3):
    """MANIFEST.json files saying stage "B" under root, down to max_depth directory levels (cache directories sit at depth 1-2)."""
    found = []
    base = os.path.abspath(root).rstrip("\/").count(os.sep)
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not any(x in d.lower() for x in ("restricted", "sealed", "do_not_open", "participant"))]
        if os.path.abspath(dp).count(os.sep) - base >= max_depth:
            dn[:] = []
        if "MANIFEST.json" in fn:
            try:
                if json.load(open(os.path.join(dp, "MANIFEST.json"))).get("stage") == "B":
                    found.append(G.rel(os.path.join(dp, "MANIFEST.json")))
            except (ValueError, OSError, UnicodeDecodeError, AttributeError):
                continue
    return found


def run_tests(bound, out_dir):
    res = []
    os.makedirs(out_dir, exist_ok=True)
    for h, p, r in bound:
        if r != "test":
            continue
        out = os.path.join(out_dir, os.path.basename(p)[:-3] + "_freeze.json")
        t0 = datetime.datetime.utcnow()
        x = subprocess.run([sys.executable, "-B", os.path.join(W, p), out], capture_output=True, text=True, cwd=C1)
        ok = x.returncode == 0 and "ALL_PASS" in x.stdout
        open(out[:-5] + ".log", "w").write(x.stdout[-20000:] + "\n" + x.stderr[-5000:])
        assert ok, "a bound test did not print ALL_PASS: %s\n%s" % (p, (x.stdout + x.stderr)[-1500:])
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
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    a.test = []
    log = a.hash_log or G.CANONICAL["C1"]
    canonical = os.path.abspath(log) == os.path.abspath(G.CANONICAL["C1"])
    if a.data_root is not None:
        assert not canonical, "--data-root only for a rehearsal's own log"
    root = a.data_root or os.path.join(W, "30_DATA")
    sb = stage_b_manifests(root)
    assert not sb, "a stage-B manifest exists, so the plan can no longer be frozen or amended: %s (R17c M1; Choice 39c)" % sb[:3]
    lines = G.log_lines(log) if os.path.exists(log) else []
    if lines:
        assert a.amend, "the hash log already holds a plan line: one freeze only; an amendment needs --amend \"<reason>\" (Choice 39c)"
    F3.check_generators = check_generators          # v03's check, on the archived originals where a file was edited (B1)
    bound, superseded, data, log3, gens = F3.check(a)
    edits = check_main_edits()
    for role, p in (("folds_val150", a.folds_val150), ("folds_train225", a.folds_train225)):
        if p:
            ch, par = json.load(open(p)), json.load(open(a.folds))
            assert ch.get("parent_sha256") == G.sha(a.folds), "%s does not name the --folds file as its parent" % role
            assert all(par["fold_of_log"].get(u) == f for u, f in ch["fold_of_log"].items()), "%s is not a restriction of --folds" % role
            src = "val" if role == "folds_val150" else "held_out_train"
            assert set(ch["fold_of_log"]) == {u for u, s in par["source_of_log"].items() if s == src}, "%s is not the parent's %s units" % (role, src)
            data.append((role, p))
    builders = {h for h, p, r in bound if r == "builder"}
    m8 = {}
    for p in a.stageA_manifests:
        bh = (json.load(open(p)).get("inputs") or {}).get("builder_sha256")
        assert bh is None or bh in builders, "stage-A manifest %s was built by %s..., not a bound builder (R17c m8)" % (G.rel(p), str(bh)[:12])
        m8[G.rel(p)] = bh or "not recorded (nuScenes cache)"
    tests = run_tests(bound, a.test_out_dir or os.path.join(os.path.dirname(os.path.abspath(a.plan)), "freeze_tests"))
    hl, rl, _ = F3.freeze(argparse.Namespace(plan=a.plan, readme=a.readme, dry_run=True), bound, superseded, data, log)
    hl[0] = hl[0].replace("c1_freeze_v03", "c1_freeze_v04")
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    v = G.versions()
    env = ["# versions asserted by c1_guard_v03 (R17c m5)"] + ["%s  %s" % (k, v[k]) for k in ("python", "numpy", "scipy")]
    tl = ["# every bound test run by c1_freeze_v04, %s UTC (R17c m4): <test sha256>  <path>  <verdict>  <output sha256>" % now]
    tl += ["%s  %s  %s  %s" % (t["sha256"], t["test"], t["verdict"], t["out_sha256"]) for t in tests]
    xl = ["# generators (on archived originals where edited): %d checked" % len(gens)] + ["# " + g for g in gens]
    xl += ["# Choice 36 main()-only edits verified: %s" % ", ".join("%s %s" % (f, h[:12]) for f, h in sorted(edits.items()))]
    xl += ["# stage-A builders (m8): %s" % json.dumps(m8)]
    if a.amend:
        xl += ["# AMENDMENT of the frozen plan (%s UTC): %s" % (now, a.amend)]
    txt = open(a.plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN", 1)
    _, tail = rest.split("FROZEN_HASHES_END", 1)
    blocks = "FROZEN_HASHES_BEGIN\n%s\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\n%s\nFROZEN_ROLES_END\n\nFROZEN_ENV_BEGIN\n%s\nFROZEN_ENV_END\n\nFROZEN_TESTS_BEGIN\n%s\n%s\nFROZEN_TESTS_END" % (
        "\n".join(hl), "\n".join(rl), "\n".join(env), "\n".join(tl), "\n".join(xl))
    if "FROZEN_ROLES_BEGIN" in tail:
        tail = tail.split("FROZEN_ROLES_BEGIN", 1)[0] + tail.split("FROZEN_ROLES_END", 1)[1]
    new = head + blocks + tail
    if a.dry_run:
        print("C1 FREEZE V04 DRY RUN: nothing written (%d hash lines, %d tests ALL_PASS)" % (len(hl), len(tests)))
        return None
    with open(a.plan, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    h = G.sha(a.plan)
    with open(a.plan[:-3] + ".sha256" if a.plan.endswith(".md") else a.plan + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.plan)))
    with open(log, "a") as f:
        f.write("%s  %s  %s %s UTC by c1_freeze_v04 (%d bound files, %d tests ALL_PASS)\n" % (h, G.rel(a.plan), "AMENDED" if a.amend else "frozen",
                                                                                       now, len(hl) - 1, len(tests)))
    if a.amend:
        dl = DEV_LOG if canonical else os.path.join(os.path.dirname(os.path.abspath(log)), "C1_DEVIATION_LOG_REHEARSAL.md")
        with open(dl, "a", encoding="utf-8") as f:
            f.write("\n## Amendment %s UTC\n\n- New plan: `%s` (sha256 %s)\n- Previous latest line: `%s`\n- Reason: %s\n" % (now, G.rel(a.plan), h, lines[-1][:80], a.amend))
    print("generators reproduced: %d; Choice 36 edits verified: %d; tests ALL_PASS: %d" % (len(gens), len(edits), len(tests)))
    print("C1 FREEZE V04 DONE: plan sha256 " + h)
    return h


if __name__ == "__main__":
    main()
