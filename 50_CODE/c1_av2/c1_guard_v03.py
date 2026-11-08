#!/usr/bin/env python3
"""C1 guards v03 (Claude line, c1_guard_v03, 4 Nov 2026) = c1_guard_v02 (kept, NOT imported and never edited: D17 v04 binds it) with
R17c's fixes (D16 v18 Choice 39):
  * M1  frozen_plan accepts a plan only if its sidecar hash is the LATEST line of the hash log (one freeze; an amendment by
        c1_freeze_v04 --amend appends a newer line, which then becomes the only accepted plan); the log's SHA-256 and path are
        recorded on the returned Frozen object (.log_sha256, .log_rel) and in every runtime record.
  * m5  the plan's FROZEN_ENV block (python, numpy, scipy; written by c1_freeze_v04) is required by guard() and the running versions
        must equal it.
  * m7  export_dataset reads the unit names from x1_tracks.jsonl.gz (the data), not x1_per_frame.json, plus the record's tag.
  * M4  units_record(names) -> sorted list and its hash; check_table(..., units=, dataset=) requires a table's units and dataset to
        equal the expected ones (and its units hash to match its list).
  * B1  guard() records LAST_GUARD = {role, entry, plan, dataset, plan_sha256}; c1_legacy_refuse_v01 lets a superseded module's main()
        (c1_fit_v02, c1_run_v02) run on AV2 data only when called by the plan's guarded entry point in the same process.
  * Choice 40 (D16 v19) deposit: check_deposit(side, dataset) requires 40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt (hard-coded; another
        path only for nuScenes or synthetic fixtures) with "frozen_plan_sha256: <the latest C1 plan line>", a non-empty "registration:"
        (OSF URL or DOI) and a "registered_utc:" line; av2_cache_stageB_v04 calls it before any ground truth is read and records the
        record's sha256 in the stage-B manifest; chain_cache requires that field and re-checks the record.
  * 38d folds roles: "folds" (375 logs), "folds_val150", "folds_train225" (child files of c1_folds_v03 --restrict-from);
        check_child_folds verifies a child against its bound parent (same labels, parent hash, no new randomness).
Everything else (roles, require_bound, verify_runtime, check_inputs, stage_a_only, chains) is c1_guard_v02's logic.
"""
import gzip
import hashlib
import json
import os
import platform
import re
import sys

W = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CODE = os.path.join(W, "50_CODE")
CANONICAL = {"C1": os.path.join(W, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt"), "D17": os.path.join(W, "40_PROTOCOL", "D17_PLAN_HASH_LOG.txt")}
NUSC = re.compile(r"^scene-\d{4}$")
SLOT = re.compile(r"\[\s*SLOT|SLOT\s*:", re.IGNORECASE)
HEX64 = re.compile(r"^[0-9a-f]{64}$")
NOT_PROJECT = ("50_CODE/env/", "50_CODE/third_party/")
FOLDS_ROLES = ("folds", "folds_val150", "folds_train225")
DEPOSIT_RECORD = os.path.join(W, "40_PROTOCOL", "C1_PLAN_DEPOSIT_RECORD_v01.txt")
DEPOSIT_GUIDE = "40_PROTOCOL/OSF_DEPOSIT_GUIDE_v01.md"
LAST_GUARD = {}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace("\\", "/")


def versions():
    import numpy
    try:
        import scipy
        sv = scipy.__version__
    except ImportError:
        sv = None
    return {"python": platform.python_version(), "numpy": numpy.__version__, "scipy": sv}


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


def folds_dataset(fj):
    return dataset_checked(fj.get("dataset"), list(fj["fold_of_log"]))


def track_scenes(worker):
    """Scene names of an x1 export from its tracks file (tracker output; no ground truth)."""
    names = set()
    p = os.path.join(worker, "x1_tracks.jsonl.gz")
    with gzip.open(p, "rt", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                names.add(str(json.loads(line)["scene"]))
    return names


def export_dataset(workers):
    tags, names = set(), set()
    for w in workers:
        rec = json.load(open(os.path.join(w, "x1_export_record.json")))
        tags.add(norm_tag(rec.get("dataset")))
        names |= track_scenes(w)
    tags.discard(None)
    assert len(tags) <= 1, "export workers with different dataset tags: %s" % sorted(tags)
    return dataset_checked(tags.pop() if tags else None, sorted(names))


def units_record(names):
    u = sorted(str(n) for n in names)
    return {"units": u, "units_sha256": hashlib.sha256("\n".join(u).encode("utf-8")).hexdigest(), "n_units": len(u)}


class Frozen(dict):
    roles = None
    env = None
    log_sha256 = None
    log_rel = None


def _section(txt, name):
    b, e = name + "_BEGIN", name + "_END"
    if b not in txt:
        return None
    assert e in txt, "unterminated %s block" % name
    return txt.split(b, 1)[1].split(e, 1)[0]


def log_lines(log):
    return [ln for ln in open(log).read().splitlines() if ln.strip() and not ln.startswith("#")]


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
    lines = log_lines(log)
    assert lines, "the plan hash log is empty"
    assert lines[-1].split()[0] == side, \
        "the plan is not the LATEST line of the hash log (one freeze; R17c M1): latest %s..., this plan %s..." % (lines[-1].split()[0][:12], side[:12])
    frozen = Frozen()
    for ln in block.strip().splitlines():
        if ln.strip() and not ln.startswith(("#", "(")):
            h, p = ln.split("  ", 1)
            frozen[p.strip()] = h
    assert frozen, "the FROZEN_HASHES block is empty"
    frozen.roles = {}
    for ln in (_section(txt, "FROZEN_ROLES") or "").strip().splitlines():
        if ln.strip() and not ln.startswith("#"):
            r, p = ln.split("  ", 1)
            assert p.strip() in frozen, "a role names a path that is not bound: " + p
            frozen.roles.setdefault(r.strip(), []).append(p.strip())
    env = _section(txt, "FROZEN_ENV")
    frozen.env = dict(ln.split("  ", 1) for ln in env.strip().splitlines() if ln.strip() and not ln.startswith("#")) if env else None
    frozen.log_sha256, frozen.log_rel = sha(log), rel(log)
    return side, frozen


def require_bound(frozen, path, role=None):
    r = rel(path)
    assert frozen.get(r) == sha(path), "not bound by the frozen plan under its own path: " + r
    if role is not None:
        assert r in (frozen.roles or {}).get(role, ()), "%s is bound, but not in the role %s (R17b M-b)" % (r, role)
    return frozen[r]


def require_folds(frozen, path, roles=FOLDS_ROLES):
    """A folds file bound in one of the folds roles; returns (role, hash)."""
    r = rel(path)
    hit = [x for x in roles if r in (frozen.roles or {}).get(x, ())]
    assert hit and frozen.get(r) == sha(path), "folds %s are not bound in any of the roles %s" % (r, list(roles))
    return hit[0], frozen[r]


def bound_in_role(frozen, h, role):
    return any(frozen.get(p) == h for p in (frozen.roles or {}).get(role, ()))


def role_hash(frozen, role):
    ps = (frozen.roles or {}).get(role, [])
    assert len(ps) == 1, "the plan binds %d files in the role %s" % (len(ps), role)
    return ps[0], frozen[ps[0]]


def project_modules(entry=None):
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
    return {"entry_point": {rel(entry): sha(entry)}, "code_sha256": {rel(f): sha(f) for f in files}, "versions": versions()}


def verify_runtime(frozen, role, entry):
    paths = (frozen.roles or {}).get(role, [])
    assert paths == [rel(entry)], "the plan names %s as its %s entry point, not %s (Choice 34.7, R17b m-4)" % (paths, role, rel(entry))
    files = project_modules(entry)
    bad = [rel(f) for f in files if frozen.get(rel(f)) != sha(f)]
    assert not bad, "entry point or imported module not bound by the frozen plan: %s (Choice 34.5)" % bad
    return {"entry_point": {rel(entry): sha(entry)}, "code_sha256": {rel(f): sha(f) for f in files}, "role": role,
            "versions": versions(), "hash_log": frozen.log_rel, "hash_log_sha256": frozen.log_sha256}


def verify_runtime_again(frozen, rt):
    entry = list(rt["entry_point"])[0]
    files = project_modules(os.path.join(W, entry))
    bad = [rel(f) for f in files if frozen.get(rel(f)) != sha(f)]
    assert not bad, "module imported during the run is not bound: %s" % bad
    rt["code_sha256"] = {rel(f): sha(f) for f in files}
    return rt


def check_env(frozen):
    assert frozen.env, "the plan has no FROZEN_ENV block (python, numpy, scipy; R17c m5)"
    now = versions()
    bad = {k: (frozen.env.get(k), now.get(k)) for k in ("python", "numpy", "scipy") if str(frozen.env.get(k)) != str(now.get(k))}
    assert not bad, "running versions differ from the plan's FROZEN_ENV: %s (R17c m5)" % bad
    return now


def guard(dataset, plan, role, entry, log=None, which="C1"):
    if plan is None:
        assert dataset in ("nuscenes", "synthetic"), \
            "%s: %s data need --plan, a frozen plan in %s (D16 Choice 34)" % (role, dataset, rel(CANONICAL[which]))
        assert log is None, "a hash log without a plan means nothing"
        return None
    side, frozen = frozen_plan(plan, dataset, log, which)
    check_env(frozen)
    rt = verify_runtime(frozen, role, entry)
    LAST_GUARD.clear()
    LAST_GUARD.update({"role": role, "entry": rel(entry), "plan": os.path.abspath(plan), "plan_sha256": side, "dataset": dataset})
    return side, frozen, rt


def stage_a_inputs(m):
    vals = set()
    for v in (m.get("inputs") or {}).values():
        for x in (v if isinstance(v, list) else [v]):
            if isinstance(x, str) and HEX64.match(x):
                vals.add(x)
    return vals


def check_deposit(side, dataset, path=None):
    """Choice 40: the external deposit of the frozen plan exists and names it. AV2: the hard-coded record only."""
    if path is not None and os.path.abspath(path) != os.path.abspath(DEPOSIT_RECORD):
        assert dataset in ("nuscenes", "synthetic"), "a deposit-record override is refused for %s data (Choice 40)" % dataset
    p = path or DEPOSIT_RECORD
    hint = " (see %s; D16 v19 Choice 40)" % DEPOSIT_GUIDE
    assert os.path.exists(p), "refused: no deposit record %s: the frozen plan has not been deposited%s" % (rel(p), hint)
    rec = {}
    for ln in open(p, encoding="utf-8").read().splitlines():
        if ":" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.split(":", 1)
            rec.setdefault(k.strip(), v.strip())
    h = rec.get("frozen_plan_sha256", "")
    assert HEX64.match(h), "refused: the deposit record has no frozen_plan_sha256 line%s" % hint
    assert h == side, "refused: the deposit record names plan %s..., not the frozen plan %s...%s" % (h[:12], side[:12], hint)
    assert rec.get("registration"), "refused: the deposit record has no registration (OSF URL or DOI)%s" % hint
    assert rec.get("registered_utc"), "refused: the deposit record has no registered_utc line%s" % hint
    return {"record": rel(p), "sha256": sha(p), "registration": rec["registration"], "registered_utc": rec["registered_utc"]}


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
    dep = sb.get("deposit_record_sha256")
    assert isinstance(dep, str) and HEX64.match(dep), "stage-B cache records no deposit record (Choice 40): " + rel(manifest_path)
    assert check_deposit(side, ds)["sha256"] == dep, "the deposit record differs from the one the stage-B cache was built under (Choice 40)"
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


def check_child_folds(child_path, frozen):
    """38d: a folds_val150 / folds_train225 file is a restriction of the bound 375-log folds: same labels, its parent's hash, no new
    randomness (c1_folds_v03 --restrict-from)."""
    ch = json.load(open(child_path))
    ppath, ph = role_hash(frozen, "folds")
    assert ch.get("parent_sha256") == ph, "child folds do not name the bound parent folds"
    par = json.load(open(os.path.join(W, ppath)))
    bad = [u for u, f in ch["fold_of_log"].items() if par["fold_of_log"].get(u) != f]
    assert not bad, "child folds differ from the parent's labels (re-randomised?): %s" % bad[:3]
    assert ch.get("dataset") == par.get("dataset"), "child folds change the dataset"
    src = ch.get("restriction", {}).get("source")
    want = {u for u, s in par.get("source_of_log", {}).items() if s == src}
    assert set(ch["fold_of_log"]) == want, "child folds are not exactly the parent's %s units" % src
    return {"parent": ppath, "source": src, "units": len(ch["fold_of_log"])}


def check_table(table, side, frozen, folds_sha, role, units=None, dataset=None, units_subset_of=None):
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
    ur = prov.get("units") or {}
    assert ur.get("units") is not None and units_record(ur["units"])["units_sha256"] == ur.get("units_sha256"), \
        "table records no unit list, or its hash does not match (R17c M4)"
    if units is not None:
        assert sorted(units) == ur["units"], "table units differ from the expected units (%d vs %d; R17c M4)" % (len(ur["units"]), len(units))
    if units_subset_of is not None:
        assert set(ur["units"]) <= set(units_subset_of) and ur["units"], "table units are not a non-empty subset of the folds' units"
    if dataset is not None:
        assert prov.get("dataset") == dataset, "table dataset %s differs from the folds' %s (R17c M4)" % (prov.get("dataset"), dataset)
    assert prov.get("hash_log_sha256") == frozen.log_sha256, "table made under another state of the hash log (R17c M1)"
    return {"entry_point": p, "sha256": h, "units": ur["n_units"] if "n_units" in ur else len(ur["units"])}
