#!/usr/bin/env python3
"""C1 freeze (Claude line, c1_freeze_v01, 2 Nov 2026), modelled on 50_CODE/k7/k7_freeze_v01.py. C1 v04 section 7 ("c1_freeze_v01.py
refuses any [SLOT, writes the hash block, the .sha256 sidecar and a new 40_PROTOCOL/C1_PLAN_HASH_LOG.txt").
Conditions, every one checked before anything is written:
  1. the plan holds no "[SLOT" (any open slot refuses the freeze) and an empty FROZEN_HASHES block;
  2. no confirmatory C1 output exists (--results-dir absent or empty);
  3. every file in the README's SHA-256 block exists and has exactly that hash ("verifies every bound code hash against the README");
  4. the generators reproduce c1_run_v01.py (tests/make_c1_run_v01.py) and the k8 v04 copies (50_CODE/k8/tests/make_k8_joint_v04.py)
     in memory, byte for byte;
  5. the C1 tests pass: each --test command is re-run here and must print ALL_PASS;
  6. every --bind input (data manifests, fits, folds, counts, ...) exists.
Then: the FROZEN_HASHES block (README-bound files, the README itself, every --bind input; "<sha256>  <path relative to W>"), the plan's
.sha256 sidecar, and one line appended to --hash-log (created if absent; never one of the M/K6/K7 hash logs), with UTC times.
Usage: python -B c1_freeze_v01.py --plan <C1 plan .md> --readme <README_C1_CODE_v0x.md> --results-dir <60_RESULTS/c1_av2>
       [--bind <file> ...] [--test "<python> -B <test.py> <out.json>" ...] [--hash-log <file>] [--dry-run]
"""
import argparse
import datetime
import hashlib
import importlib.util
import os
import re
import shlex
import subprocess
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(C1))
K8 = os.path.join(W, "50_CODE", "k8")
FORBIDDEN_LOGS = ("M_PLAN_HASH_LOG.txt", "K6_PLAN_HASH_LOG.txt", "K7_PLAN_HASH_LOG.txt")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace("\\", "/")


def readme_hashes(readme):
    out = []
    for ln in open(readme, encoding="utf-8").read().splitlines():
        m = re.match(r"^([0-9a-f]{64})  (50_CODE/\S+)$", ln.strip())
        if m:
            out.append((m.group(1), m.group(2)))
    assert out, "the README holds no SHA-256 block"
    return out


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def check_generators():
    mk = _load(os.path.join(C1, "tests", "make_c1_run_v01.py"), "make_c1_run_v01")
    with open(os.path.join(K8, "k8_run_v04.py"), encoding="utf-8", newline="") as f:
        assert mk.make(f.read()) == open(os.path.join(C1, "c1_run_v01.py"), encoding="utf-8", newline="").read(), "c1_run_v01.py is not reproduced"
    mj = _load(os.path.join(K8, "tests", "make_k8_joint_v04.py"), "make_k8_joint_v04")
    for src, dst, fn in (("k8_sim_v02.py", "k8_sim_v04.py", mj.make_sim), ("k8_run_v02.py", "k8_run_v04.py", mj.make_run),
                         ("k8_analyse_v03.py", "k8_analyse_v04.py", mj.make_analysis)):
        with open(os.path.join(K8, src), encoding="utf-8", newline="") as f:
            assert fn(f.read()) == open(os.path.join(K8, dst), encoding="utf-8", newline="").read(), dst + " is not reproduced"
    return True


def check(a):
    txt = open(a.plan, encoding="utf-8").read()
    slots = sorted(set(re.findall(r"\[SLOT[^\]]*\]", txt)))
    assert not slots, "open slots refuse the freeze: %d, e.g. %s" % (len(slots), slots[:3])
    assert "FROZEN_HASHES_BEGIN" in txt and "FROZEN_HASHES_END" in txt, "the plan has no FROZEN_HASHES block"
    block = txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
    assert not block.strip(), "the FROZEN_HASHES block is not empty: the plan is already frozen"
    assert not os.path.exists(a.plan.replace(".md", ".sha256")), "a .sha256 sidecar already exists"
    assert not (os.path.isdir(a.results_dir) and os.listdir(a.results_dir)), "confirmatory C1 outputs already exist: " + a.results_dir
    bound = readme_hashes(a.readme)
    for h, p in bound:
        q = os.path.join(W, p)
        assert os.path.exists(q), "bound file missing: " + p
        assert sha(q) == h, "bound file differs from the README hash: " + p
    check_generators()
    for cmd in a.test:
        r = subprocess.run(shlex.split(cmd, posix=os.name != "nt"), capture_output=True, text=True, cwd=C1)
        assert r.returncode == 0 and "ALL_PASS" in r.stdout, "test did not print ALL_PASS: %s\n%s" % (cmd, (r.stdout + r.stderr)[-1500:])
    for p in a.bind:
        assert os.path.exists(p), "bind input missing: " + p
    assert os.path.basename(a.hash_log) not in FORBIDDEN_LOGS, "never append to " + os.path.basename(a.hash_log)
    return bound


def freeze(a, bound):
    lines = ["# C1 frozen files (c1_freeze_v01, %s UTC)" % datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")]
    lines += ["%s  %s" % (h, p) for h, p in bound]
    lines.append("%s  %s" % (sha(a.readme), rel(a.readme)))
    lines += ["%s  %s" % (sha(p), rel(p)) for p in a.bind]
    txt = open(a.plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN", 1)
    _, tail = rest.split("FROZEN_HASHES_END", 1)
    new = head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail
    if a.dry_run:
        return lines, None
    with open(a.plan, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    h = sha(a.plan)
    with open(a.plan.replace(".md", ".sha256"), "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(a.plan)))
    with open(a.hash_log, "a") as f:
        f.write("%s  %s  frozen %s UTC by c1_freeze_v01 (%d bound files)\n" % (h, rel(a.plan), datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                                                                             len(lines) - 1))
    return lines, h


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--readme", required=True)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--bind", nargs="*", default=[])
    ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--hash-log", default=os.path.join(W, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_freeze_v01", "c1_freeze_v04", LEGACY.ds_bind_files(a.bind))
    bound = check(a)
    lines, h = freeze(a, bound)
    print("\n".join(lines[:5] + ["... (%d lines)" % len(lines)]))
    print("C1 FREEZE %s" % ("DRY RUN: nothing written" if a.dry_run else "DONE: plan sha256 " + h))


if __name__ == "__main__":
    main()
