#!/usr/bin/env python3
"""C1 guards v02 (Claude line, c1_guard_v02, 4 Nov 2026) = c1_guard_v01 (kept) with D16 v13 Choice 34 (R17b A, B, M-a, M-b; m-4, m-5).
  CANONICAL          one hash log per plan, hard-coded: 40_PROTOCOL/C1_PLAN_HASH_LOG.txt (C1), 40_PROTOCOL/D17_PLAN_HASH_LOG.txt (D17).
  frozen_plan(plan, dataset, log=None)  as v01, but another log is accepted ONLY for a nuScenes dataset (a rehearsal); for "av2",
                     "mixed" or "unknown" data an override is refused (R17b A1). The slot test is a regex ("[SLOT", "[ slot", "SLOT:",
                     any case; m-5). The plan's FROZEN_ROLES block (written by c1_freeze_v03) names the role of each bound path:
                     entry points ("entry:<name>", exactly one path each), "module", "generator", "folds", "split", "transfer_fits",
                     "stageA_manifest", "config", "builder" and "data:<name>". Returns (sidecar hash, Frozen: {path: hash} + .roles).
  dataset_checked(tag, names)   the dataset of a set of units; a tag must agree with the names (R17b A3): "nuscenes" needs every name
                     scene-NNNN, "av2" needs none; an untagged set takes the names' dataset ("mixed" or "unknown" otherwise).
  export_dataset(workers)       the dataset of x1 export directories from outcome-free files only (x1_per_frame.json scene names and
                     the export record's tag), read before any ground truth.
  guard(dataset, plan, role, entry, log=None)   the one entry check of every guarded module: nuScenes data without --plan run
                     unguarded (tests, development); anything else needs a frozen plan (canonical log unless nuScenes) AND the running
                     entry point must be the plan's named entry for its role AND every project module loaded must be bound by path
                     (verify_runtime; Choice 34.5, R17b M-a). Returns None or (sidecar, frozen, runtime record).
  require_bound(frozen, path, role)   role-aware (R17b M-b): the block holds this file's own W-relative path with its current hash,
                     and, with a role, the roles block lists that path under that role.
  check_inputs(frozen, files)   every input file is bound by path, or its hash is an input of a bound stage-A manifest.
  stage_a_only(manifests, files)  the pre-freeze E0 / counts exception (Choice 34.2): every manifest says stage A, never B, and every
                     file's hash is one of their recorded inputs.
  chain_cache, chain_items      Choice 34.6: an AV2 cache must be stage B, built under this plan by the bound stage-B entry point from a
                     bound stage-A manifest; items must come (by their summary) from such caches through the bound item builder.
                     A nuScenes cache must itself be bound (a rehearsal binds the nuScenes caches as its stage-A manifests).
  check_table(table, side, frozen, folds_sha, role)   Choice 34.4 (R17b B): an H6-H9 table made after the freeze is valid only if its
                     provenance names this plan, these folds, the plan's entry point for its role, and code bound by path.
"""
import hashlib
import json
import os
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE = os.path.join(W, "50_CODE")
CANONICAL = {"C1": os.path.join(W, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt"), "D17": os.path.join(W, "40_PROTOCOL", "D17_PLAN_HASH_LOG.txt")}
NUSC = re.compile(r"^scene-\d{4}$")
SLOT = re.compile(r"\[\s*SLOT|SLOT\s*:", re.IGNORECASE)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NOT_PROJECT = ("50_CODE/env/", "50_CODE/third_party/")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace("\\", "/")


def norm_tag(tag):
    if not tag:
        return None
    t = str(tag).lower()
    return "av2" if t.startswith("av2") else "nuscenes" if t.startswith("nuscenes") else t


def units_dataset(names):
    names = [str(n) for n in names]
    if not names:
        return "unknown"
    if all(NUSC.match(n) for n in names):
        return "nuscenes"
    if not any(NUSC.match(n) for n in names):
        return "av2"
    return "mixed"


def dataset_checked(tag, names):
    by_names, t = units_dataset(names), norm_tag(tag)
    if t:
        assert by_names == t or (by_names == "unknown" and t == "av2"), \
            "dataset tag %r disagrees with the unit names (%s): refused (R17b A3)" % (tag, by_names)
        return t
    return by_names


def manifest_dataset(m):
    return dataset_checked(m.get("dataset"), list((m.get("scenes") or {}).keys()))


def export_dataset(workers):
    tags, names = set(), set()
    for w in workers:
        rec = json.load(open(os.path.join(w, "x1_export_record.json")))
        tags.add(norm_tag(rec.get("dataset")))
        names |= {str(p["scene"]) for p in json.load(open(os.path.join(w, "x1_per_frame.json"))) if "scene" in p}
    tags.discard(None)
    assert len(tags) <= 1, "export workers with different dataset tags: %s" % sorted(tags)
    return dataset_checked(tags.pop() if tags else None, sorted(names))


class Frozen(dict):
    roles = None


def _section(txt, name):
    b, e = name + "_BEGIN", name + "_END"
    if b not in txt:
        return None
    assert e in txt, "unterminated %s block" % name
    return txt.split(b, 1)[1].split(e, 1)[0]


def frozen_plan(plan, dataset, log=None, which="C1"):
    canon = CANONICAL[which]
    if log is not None and os.path.abspath(log) != os.path.abspath(canon):
        assert dataset == "nuscenes", "a hash-log override is refused for %s data (R17b A1; D16 v13 Choice 34.1)" % dataset
    log = log or canon
    txt = open(plan, encoding="utf-8").read()
    m = SLOT.search(txt)
    assert not m, "the plan still has an open slot (%r): it is not frozen" % txt[m.start():m.start() + 12]
    block = _section(txt, "FROZEN_HASHES")
    assert block is not None, "the plan has no FROZEN_HASHES block"
    side_p = plan[:-3] + ".sha256" if plan.endswith(".md") else plan + ".sha256"
    assert os.path.exists(side_p), "no .sha256 sidecar: the plan is not frozen"
    side = open(side_p).read().split()[0]
    assert sha(plan) == side, "the plan differs from its sidecar hash"
    assert os.path.exists(log), "no plan hash log (%s): nothing is frozen" % rel(log)
    assert side in {ln.split()[0] for ln in open(log).read().splitlines() if ln.strip()}, "the plan's hash is not in the hash log"
    frozen = Frozen()
    for ln in block.strip().splitlines():
        if ln.strip() and not ln.startswith(("#", "(")):
            h, p = ln.split("  ", 1)
            frozen[p.strip()] = h
    assert frozen, "the FROZEN_HASHES block is empty"
    frozen.roles = {}
    rb = _section(txt, "FROZEN_ROLES")
    for ln in (rb or "").strip().splitlines():
        if ln.strip() and not ln.startswith("#"):
            r, p = ln.split("  ", 1)
            assert p.strip() in frozen, "a role names a path that is not bound: " + p
            frozen.roles.setdefault(r.strip(), []).append(p.strip())
    return side, frozen


def require_bound(frozen, path, role=None):
    r = rel(path)
    assert frozen.get(r) == sha(path), "not bound by the frozen plan under its own path: " + r
    if role is not None:
        assert r in (frozen.roles or {}).get(role, ()), "%s is bound, but not in the role %s (R17b M-b)" % (r, role)
    return frozen[r]


def bound_in_role(frozen, h, role):
    return any(frozen.get(p) == h for p in (frozen.roles or {}).get(role, ()))


def project_modules(entry=None):
    """Every project module loaded now (files under 50_CODE, not the environments or third-party code), plus the entry point."""
    out = set()
    main_file = getattr(sys.modules.get("__main__"), "__file__", None)
    for name, mod in list(sys.modules.items()):
        f = getattr(mod, "__file__", None)
        if not f or not f.endswith(".py"):
            continue
        f = os.path.abspath(f)
        if name in ("__main__", "__mp_main__") and entry and f != os.path.abspath(entry):
            continue
        if main_file and f == os.path.abspath(main_file) and entry and f != os.path.abspath(entry):
            continue
        r = rel(f)
        if r.startswith("50_CODE/") and not r.startswith(NOT_PROJECT):
            out.add(f)
    if entry:
        out.add(os.path.abspath(entry))
    return sorted(out)


def code_record(entry):
    files = project_modules(entry)
    return {"entry_point": {rel(entry): sha(entry)}, "code_sha256": {rel(f): sha(f) for f in files}}


def verify_runtime(frozen, role, entry):
    paths = (frozen.roles or {}).get(role, [])
    assert paths == [rel(entry)], "the plan names %s as its %s entry point, not %s (Choice 34.7, R17b m-4)" % (paths, role, rel(entry))
    files = project_modules(entry)
    bad = [rel(f) for f in files if frozen.get(rel(f)) != sha(f)]
    assert not bad, "entry point or imported module not bound by the frozen plan: %s (Choice 34.5)" % bad
    return {"entry_point": {rel(entry): sha(entry)}, "code_sha256": {rel(f): sha(f) for f in files}, "role": role}


def verify_runtime_again(frozen, rt):
    """Before outputs are written: modules imported since the start (lazy imports) must be bound too."""
    entry = list(rt["entry_point"])[0]
    files = project_modules(os.path.join(W, entry))
    bad = [rel(f) for f in files if frozen.get(rel(f)) != sha(f)]
    assert not bad, "module imported during the run is not bound: %s" % bad
    rt["code_sha256"] = {rel(f): sha(f) for f in files}
    return rt


def guard(dataset, plan, role, entry, log=None, which="C1"):
    if plan is None:
        assert dataset == "nuscenes", "%s: %s data need --plan, a frozen plan in %s (D16 Choice 34)" % (role, dataset, rel(CANONICAL[which]))
        assert log is None, "a hash log without a plan means nothing"
        return None
    side, frozen = frozen_plan(plan, dataset, log, which)
    rt = verify_runtime(frozen, role, entry)
    return side, frozen, rt


def stage_a_inputs(m):
    vals = set()
    for v in (m.get("inputs") or {}).values():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str) and HEX64.match(x):
                vals.add(x)
    return vals


def check_inputs(frozen, files):
    listed = set()
    for p in (frozen.roles or {}).get("stageA_manifest", []):
        listed |= stage_a_inputs(json.load(open(os.path.join(W, p))))
    out = {}
    for f in files:
        h = sha(f)
        assert frozen.get(rel(f)) == h or h in listed, "input neither bound by the plan nor an input of a bound stage-A manifest: " + rel(f)
        out[rel(f)] = h
    return out


def stage_a_only(manifests, files):
    listed, ds = set(), set()
    for mp in manifests:
        m = json.load(open(mp))
        assert m.get("stage") == "A", "the pre-freeze step reads stage-A files only; %s is stage %s (Choice 34.2)" % (rel(mp), m.get("stage"))
        ds.add(manifest_dataset(m))
        listed |= stage_a_inputs(m)
    assert len(ds) == 1, "stage-A manifests of different datasets: %s" % sorted(ds)
    out = {}
    for f in files:
        h = sha(f)
        assert h in listed, "not an input of the stage-A manifests: " + rel(f)
        out[rel(f)] = h
    return ds.pop(), out


def chain_cache(manifest_path, side, frozen):
    m = json.load(open(manifest_path))
    ds = manifest_dataset(m)
    h = sha(manifest_path)
    if ds == "nuscenes":
        require_bound(frozen, manifest_path, "stageA_manifest")
        return {"manifest": rel(manifest_path), "sha256": h, "dataset": ds, "chain": "nuScenes cache bound by the plan"}
    sb = m.get("stage_b") or {}
    assert m.get("stage") == "B", "an AV2 cache must be stage B: " + rel(manifest_path)
    assert sb.get("frozen_plan_sha256") == side, "stage-B cache not built under this plan: " + rel(manifest_path)
    assert bound_in_role(frozen, sb.get("stage_a_manifest_sha256"), "stageA_manifest"), "its stage-A manifest is not bound: " + rel(manifest_path)
    assert bound_in_role(frozen, sb.get("script_sha256"), "entry:stageB"), "not built by the plan's stage-B entry point: " + rel(manifest_path)
    return {"manifest": rel(manifest_path), "sha256": h, "dataset": ds, "stage_a_manifest_sha256": sb["stage_a_manifest_sha256"],
            "chain": "stage B under this plan from a bound stage-A manifest"}


def chain_items(items_path, side, frozen):
    sp = items_path[:-4] + "_summary.json"
    assert os.path.exists(sp), "items without their summary (no chain): " + rel(items_path)
    s = json.load(open(sp))
    assert s.get("out_sha256") == sha(items_path), "items differ from their summary: " + rel(items_path)
    caches = s.get("caches") or []
    assert caches and len(caches) == len(s.get("manifest_sha256") or []), "items record no caches: " + rel(items_path)
    ch = []
    for c, mh in zip(caches, s["manifest_sha256"]):
        mp = os.path.join(c, "MANIFEST.json")
        assert sha(mp) == mh, "a cache manifest differs from the items' record: " + rel(mp)
        ch.append(chain_cache(mp, side, frozen))
    role = "entry:k8_items" if any(x["dataset"] != "nuscenes" for x in ch) else "builder"
    assert bound_in_role(frozen, s.get("items_script_sha256"), role) or bound_in_role(frozen, s.get("items_script_sha256"), "entry:k8_items"), \
        "items not built by a bound item builder (%s): %s" % (role, rel(items_path))
    return {"items": rel(items_path), "sha256": sha(items_path), "caches": ch, "builder_sha256": s.get("items_script_sha256")}


def check_table(table, side, frozen, folds_sha, role):
    prov = table.get("provenance") or {}
    assert prov.get("plan_sha256") == side, "table not made under this frozen plan"
    assert prov.get("folds_sha256") == folds_sha, "table made on other folds"
    ep = prov.get("entry_point") or {}
    assert len(ep) == 1, "table names no entry point"
    p, h = list(ep.items())[0]
    assert (frozen.roles or {}).get(role) == [p] and frozen.get(p) == h, "table not made by the plan's %s entry point: %s" % (role, p)
    code = prov.get("code_sha256") or {}
    assert code, "table records no code hashes"
    bad = [q for q, x in code.items() if frozen.get(q) != x]
    assert not bad, "table code not bound by the plan: %s" % bad
    assert prov.get("inputs_checked") is True and prov.get("inputs_sha256"), "table records no checked inputs"
    return {"entry_point": p, "sha256": h}
