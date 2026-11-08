#!/usr/bin/env python3
"""C1 freeze v03 (Claude line, c1_freeze_v03, 4 Nov 2026) = c1_freeze_v02's binding list (v01 and v02 kept, not imported) with D16 v13
Choice 34 (R17b A1, M-b, m-3, m-4, m-5) and Choice 34.7:
  * the README (v05 format) lists every bound file with its ROLE: "<sha256>  <path>  <role>", role one of entry:<name> (exactly one
    path per entry role), module, generator, test, builder, source; and "superseded  <path>" for versions that are NOT bound;
  * the plan gets the FROZEN_HASHES block (every README-bound file, the README, every data input) AND a FROZEN_ROLES block naming
    the role of each bound path: the entry points (the plan names them, m-4), modules, generators, tests, builders, and the data
    roles folds, split, transfer_fits, stageA_manifest, config, data:<name>; c1_guard_v02 makes every check role-aware;
  * refused: an entry point that is not the latest version in its directory (a higher _vNN sibling exists), a superseded file in the
    bound list, a missing required entry role, a generator that does not reproduce its target (EVERY generator: m-3), a README
    generator not covered by the check, any open slot (regex, m-5), a non-empty block, an existing sidecar or results, a test that does
    not print ALL_PASS, a post-freeze artefact given as data (fits made within AV2, stage-B manifests, run records, tables with a plan
    hash), a stage-A manifest whose tag disagrees with its names;
  * the hash log is 40_PROTOCOL/C1_PLAN_HASH_LOG.txt; another log only when the folds' units are nuScenes (a rehearsal); never the
    M, K6 or K7 logs.
Usage: python -B c1_freeze_v03.py --plan <plan.md> --readme <README_C1_CODE_v05.md> --results-dir <dir> --folds <json> --split <json>
       --transfer-fits <t1> <t3> --stageA-manifests <MANIFEST.json ...> --config <json> [--data name=path ...] [--test "..." ...]
       [--hash-log <file>] [--dry-run]
"""
import argparse
import datetime
import importlib.util
import json
import os
import re
import shlex
import subprocess
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_guard_v02 as G  # noqa: E402

W = G.W
FORBIDDEN_LOGS = ("M_PLAN_HASH_LOG.txt", "K6_PLAN_HASH_LOG.txt", "K7_PLAN_HASH_LOG.txt")
ENTRY_REQUIRED = ("entry:c1_analyse", "entry:c1_fit", "entry:c1_run", "entry:c1_mstage", "entry:c1_h8", "entry:c1_e0", "entry:c1_predarm",
                  "entry:c1_transfer_apply", "entry:c1_folds", "entry:stageB", "entry:k8_items", "entry:tpp_keys", "entry:tpp_run")
ROLES = ("module", "generator", "test", "builder", "source")
GENS = (("50_CODE/c1_av2/tests/make_c1_run_v01.py", "make", "50_CODE/k8/k8_run_v04.py", "50_CODE/c1_av2/c1_run_v01.py"),
        ("50_CODE/c1_av2/tests/make_c1_run_v02.py", "make", "50_CODE/c1_av2/c1_run_v01.py", "50_CODE/c1_av2/c1_run_v02.py"),
        ("50_CODE/c1_av2/tests/make_c1_analyse_v02.py", "make", "50_CODE/c1_av2/c1_analyse_v01.py", "50_CODE/c1_av2/c1_analyse_v02.py"),
        ("50_CODE/c1_av2/tests/make_av2_stageB_v02.py", "make", "50_CODE/av2/av2_cache_stageB_v01.py", "50_CODE/av2/av2_cache_stageB_v02.py"),
        ("50_CODE/c1_av2/tests/make_av2_stageB_v03.py", "make", "50_CODE/av2/av2_cache_stageB_v02.py", "50_CODE/av2/av2_cache_stageB_v03.py"),
        ("50_CODE/c1_av2/tests/make_k8_items_v05.py", "make", "50_CODE/k8/k8_items_v04.py", "50_CODE/k8/k8_items_v05.py"),
        ("50_CODE/k8/tests/make_k8_joint_v04.py", "make_sim", "50_CODE/k8/k8_sim_v02.py", "50_CODE/k8/k8_sim_v04.py"),
        ("50_CODE/k8/tests/make_k8_joint_v04.py", "make_run", "50_CODE/k8/k8_run_v02.py", "50_CODE/k8/k8_run_v04.py"),
        ("50_CODE/k8/tests/make_k8_joint_v04.py", "make_analysis", "50_CODE/k8/k8_analyse_v03.py", "50_CODE/k8/k8_analyse_v04.py"))
VER = re.compile(r"^(.*)_v(\d+)\.py$")


def readme_v05(readme):
    bound, superseded = [], []
    for ln in open(readme, encoding="utf-8").read().splitlines():
        m = re.match(r"^([0-9a-f]{64})  (50_CODE/\S+)  (\S+)$", ln.strip())
        if m:
            bound.append((m.group(1), m.group(2), m.group(3)))
        m = re.match(r"^superseded  (50_CODE/\S+)$", ln.strip())
        if m:
            superseded.append(m.group(1))
    assert bound, "the README holds no v05 SHA-256 block (hash, path, role)"
    paths = [p for _, p, _ in bound]
    assert len(set(paths)) == len(paths), "a path is listed twice in the README"
    for _, p, r in bound:
        assert r in ROLES or r.startswith("entry:"), "unknown role %s for %s" % (r, p)
    assert not set(paths) & set(superseded), "superseded files are listed as bound: %s" % sorted(set(paths) & set(superseded))
    return bound, superseded


def latest(path):
    m = VER.match(os.path.basename(path))
    if not m:
        return True
    d = os.path.dirname(os.path.join(W, path))
    v = int(m.group(2))
    for f in os.listdir(d):
        n = VER.match(f)
        if n and n.group(1) == m.group(1) and int(n.group(2)) > v:
            return False
    return True


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_generators(bound):
    gens_bound = {p for _, p, r in bound if r == "generator"}
    covered = {g for g, _, _, _ in GENS}
    assert gens_bound <= covered, "generators bound but not checked: %s" % sorted(gens_bound - covered)
    out = []
    for g, fn, src, dst in GENS:
        mod = _load(os.path.join(W, g), "gen_" + os.path.basename(g)[:-3])
        with open(os.path.join(W, src), encoding="utf-8", newline="") as f:
            made = getattr(mod, fn)(f.read())
        with open(os.path.join(W, dst), encoding="utf-8", newline="") as f:
            assert made == f.read(), "%s.%s does not reproduce %s" % (g, fn, dst)
        out.append("%s %s -> %s" % (os.path.basename(g), fn, dst))
    return out


def post_freeze_artefact(p):
    try:
        d = json.load(open(p))
    except (ValueError, UnicodeDecodeError, OSError):
        return False
    if not isinstance(d, dict):
        return False
    prov = d.get("provenance") if isinstance(d.get("provenance"), dict) else {}
    return ((d.get("c1") is True and d.get("route") == "within") or d.get("stage") == "B" or "episodes_sha256" in d
            or bool(prov.get("plan_sha256")) or "provenance_v03" in d)


def check(a):
    txt = open(a.plan, encoding="utf-8").read()
    m = G.SLOT.search(txt)
    assert not m, "an open slot refuses the freeze: %r" % txt[m.start():m.start() + 40]
    blk = G._section(txt, "FROZEN_HASHES")
    assert blk is not None and not blk.strip(), "the FROZEN_HASHES block is missing or not empty"
    rb = G._section(txt, "FROZEN_ROLES")
    assert rb is None or not rb.strip(), "the FROZEN_ROLES block is not empty"
    side_p = a.plan[:-3] + ".sha256" if a.plan.endswith(".md") else a.plan + ".sha256"
    assert not os.path.exists(side_p), "a .sha256 sidecar already exists"
    assert not (os.path.isdir(a.results_dir) and os.listdir(a.results_dir)), "confirmatory C1 outputs already exist: " + a.results_dir
    bound, superseded = readme_v05(a.readme)
    for h, p, r in bound:
        q = os.path.join(W, p)
        assert os.path.exists(q) and G.sha(q) == h, "bound file missing or differs from the README hash: " + p
    entries = {}
    for _, p, r in bound:
        if r.startswith("entry:"):
            assert r not in entries, "two paths for %s" % r
            entries[r] = p
            assert latest(p), "entry point %s is not the latest version in its directory (Choice 34.7)" % p
    miss = [r for r in ENTRY_REQUIRED if r not in entries]
    assert not miss, "entry roles missing from the README: %s" % miss
    gens = check_generators(bound)
    for cmd in a.test:
        r = subprocess.run(shlex.split(cmd, posix=os.name != "nt"), capture_output=True, text=True, cwd=C1)
        assert r.returncode == 0 and "ALL_PASS" in r.stdout, "test did not print ALL_PASS: %s\n%s" % (cmd, (r.stdout + r.stderr)[-1500:])
    data = [("folds", a.folds), ("split", a.split)] + [("transfer_fits", p) for p in a.transfer_fits] + \
           [("stageA_manifest", p) for p in a.stageA_manifests] + [("config", a.config)]
    for x in a.data:
        n, p = x.split("=", 1)
        data.append(("data:" + n, p))
    for role, p in data:
        assert os.path.exists(p), "data input missing: " + p
        assert not post_freeze_artefact(p), "made after the freeze, checked by provenance, never bound: " + p
    for p in a.transfer_fits:
        assert json.load(open(p)).get("route") == "transfer", "--transfer-fits must be c1_fit transfer fits: " + p
    for p in a.stageA_manifests:
        mm = json.load(open(p))
        assert mm.get("stage", "A") == "A", "a stage-B manifest is never bound: " + p
        G.manifest_dataset(mm)
    fj = json.load(open(a.folds))
    ds = G.dataset_checked(fj.get("dataset"), list(fj["fold_of_log"]))
    log = a.hash_log or G.CANONICAL["C1"]
    if os.path.abspath(log) != os.path.abspath(G.CANONICAL["C1"]):
        assert ds == "nuscenes", "another hash log only for a nuScenes rehearsal (Choice 34.1)"
    assert os.path.basename(log) not in FORBIDDEN_LOGS, "never append to " + os.path.basename(log)
    return bound, superseded, data, log, gens


def freeze(a, bound, superseded, data, log):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    hl = ["# C1 frozen files (c1_freeze_v03, %s UTC)" % now] + ["%s  %s" % (h, p) for h, p, _ in bound]
    hl.append("%s  %s" % (G.sha(a.readme), G.rel(a.readme)))
    seen = {p for _, p, _ in bound} | {G.rel(a.readme)}
    for _, p in data:
        if G.rel(p) not in seen:
            hl.append("%s  %s" % (G.sha(p), G.rel(p)))
            seen.add(G.rel(p))
    rl = ["# roles (c1_guard_v02): the entry points are the only C1 programs this plan accepts"]
    rl += ["%s  %s" % (r, p) for _, p, r in sorted(bound, key=lambda x: (not x[2].startswith("entry:"), x[2], x[1]))]
    rl.append("readme  %s" % G.rel(a.readme))
    rl += ["%s  %s" % (r, G.rel(p)) for r, p in data]
    rl += ["# not bound (superseded): %s" % p for p in superseded]
    txt = open(a.plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN", 1)
    _, tail = rest.split("FROZEN_HASHES_END", 1)
    if "FROZEN_ROLES_BEGIN" in tail:
        t0, t1 = tail.split("FROZEN_ROLES_BEGIN", 1)
        tail = t0 + "FROZEN_ROLES_BEGIN\n" + "\n".join(rl) + "\nFROZEN_ROLES_END" + t1.split("FROZEN_ROLES_END", 1)[1]
        new = head + "FROZEN_HASHES_BEGIN\n" + "\n".join(hl) + "\nFROZEN_HASHES_END" + tail
    else:
        new = head + "FROZEN_HASHES_BEGIN\n" + "\n".join(hl) + "\nFROZEN_HASHES_END\n\nFROZEN_ROLES_BEGIN\n" + "\n".join(rl) + "\nFROZEN_ROLES_END" + tail
    if a.dry_run:
        return hl, rl, None
    with open(a.plan, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    h = G.sha(a.plan)
    with open(a.plan[:-3] + ".sha256" if a.plan.endswith(".md") else a.plan + ".sha256", "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.plan)))
    with open(log, "a") as f:
        f.write("%s  %s  frozen %s UTC by c1_freeze_v03 (%d bound files)\n" % (h, G.rel(a.plan), now, len(hl) - 1))
    return hl, rl, h


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--readme", required=True)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--transfer-fits", nargs=2, required=True)
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--data", nargs="*", default=[])
    ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--hash-log", default=None)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    bound, superseded, data, log, gens = check(a)
    hl, rl, h = freeze(a, bound, superseded, data, log)
    print("generators reproduced: %d" % len(gens))
    print("\n".join(hl[:3] + ["... (%d hash lines, %d role lines)" % (len(hl), len(rl))]))
    print("C1 FREEZE V03 %s" % ("DRY RUN: nothing written" if a.dry_run else "DONE: plan sha256 " + h))
    return h


if __name__ == "__main__":
    main()
