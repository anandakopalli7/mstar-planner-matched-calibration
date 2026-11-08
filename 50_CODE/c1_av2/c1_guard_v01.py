#!/usr/bin/env python3
"""C1 guards (Claude line, c1_guard_v01, 2 Nov 2026): the outcome-blind boundary and the binding of D16 v09 Choices 24 and 25
(R17 C1, M2). Used by c1_fit_v02, c1_run_v02, c1_analyse_v03, av2_cache_stageB_v02 and c1_freeze_v02.
  frozen_plan(plan, hash_log)  a plan is FROZEN only if: no "[SLOT" remains, its FROZEN_HASHES block is non-empty, its .sha256
                               sidecar equals its SHA-256, and that hash is a line of the hash log (40_PROTOCOL/C1_PLAN_HASH_LOG.txt,
                               written only by c1_freeze). A hash passed on a command line is never enough. Returns (sidecar
                               hash, {relative path: hash} of the block). Block paths are relative to the work root W.
  require_bound(frozen, path)  the file's current hash is in the block (paths resolved against W).
  dataset_of_manifest(m, names) a cache manifest's dataset: its "dataset" tag; untagged manifests are "nuscenes" only if every scene
                               name has the nuScenes form scene-NNNN, else "unknown" (treated as AV2-derived: refused without a plan).
  units_dataset(names)         the same rule for a list of unit names (fits, items, runs).
"""
import hashlib
import os
import re

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
HASH_LOG = os.path.join(W, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt")
NUSC = re.compile(r"^scene-\d{4}$")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace("\\", "/")


def frozen_plan(plan, hash_log=HASH_LOG):
    txt = open(plan, encoding="utf-8").read()
    assert "[SLOT" not in txt, "the plan still has an open [SLOT: it is not frozen"
    assert "FROZEN_HASHES_BEGIN" in txt and "FROZEN_HASHES_END" in txt, "the plan has no FROZEN_HASHES block"
    block = txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
    side_p = plan[:-3] + ".sha256" if plan.endswith(".md") else plan + ".sha256"
    assert os.path.exists(side_p), "no .sha256 sidecar: the plan is not frozen"
    side = open(side_p).read().split()[0]
    assert sha(plan) == side, "the plan differs from its sidecar hash"
    assert os.path.exists(hash_log), "no C1 plan hash log: nothing is frozen"
    logged = {ln.split()[0] for ln in open(hash_log).read().splitlines() if ln.strip()}
    assert side in logged, "the plan's hash is not in the C1 plan hash log (a draft is never accepted)"
    frozen = {}
    for ln in block.strip().splitlines():
        if not ln.strip() or ln.startswith(("#", "(")):
            continue
        h, p = ln.split("  ", 1)
        frozen[p.strip()] = h
    assert frozen, "the FROZEN_HASHES block is empty"
    return side, frozen


def require_bound(frozen, path):
    h = sha(path)
    assert h in frozen.values(), "not bound by the frozen plan: " + rel(path)
    return h


def units_dataset(names):
    names = list(names)
    return "nuscenes" if names and all(NUSC.match(str(n)) for n in names) else "unknown"


def dataset_of_manifest(m):
    tag = m.get("dataset")
    if tag:
        return str(tag)
    return units_dataset(m.get("scenes", {}).keys())
