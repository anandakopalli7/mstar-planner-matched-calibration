#!/usr/bin/env python3
"""C1 guards v04 (Claude line, c1_guard_v04, 4 Nov 2026) = c1_guard_v03 (kept, imported: dataset rules, roles, runtime verification,
stage-A rules, child folds) with R17d's fixes (D16 v21 Choice 42):
  * B1  guard() on AV2 data requires the deposit record for every role except entry:c1_e0, entry:c1_folds and entry:c1_freeze, so stage
        B, items, fits, runs, method stage, H8, predictor arm, Q1 summary and analysis all wait for the external registration. The record's
        sha256 goes into every runtime record; check_table requires a table's deposit_record_sha256 to equal the current one.
  * m2  check_deposit validates the record: no duplicated key; frozen_plan_sha256 = the guarded (latest-line) plan; registration matches
        https://osf.io/<id>/ or 10.17605/OSF.IO/<ID>; registered_utc is ISO 8601 UTC, later than the plan's line in the hash log, no later
        than now, and earlier than every stage-B build in 40_PROTOCOL/C1_STAGE_B_LOG.txt. Refusals name OSF_DEPOSIT_GUIDE_v02.md (41b).
  * m3  check_scene_json: scene.json bound as data:scene_json, and for every unit its log equals the bound stage-A manifests'
        scenes[u]["log"].
  * m4  frozen_plan parses the FROZEN_ENV_TPP block (python, numpy, torch of the tpp38 environment) into Frozen.env_tpp.
  * (g) run_log_append: one JSON line per guarded AV2 run in the append-only 40_PROTOCOL/C1_RUN_LOG.txt (UTC, entry, plan, deposit,
        inputs, outputs); refuse_existing: outputs on AV2 are never overwritten.
  * B2  the ground-truth quarantine 30_DATA/av2_gt_quarantine_v01/ (gzip members and QUARANTINE_MANIFEST.json, written by
        c1_quarantine_v01): open_quarantined / materialise_quarantined return the decompressed bytes (or a temporary file OUTSIDE the
        workspace) only if their SHA-256 equals the hash the stage-A manifest recorded; plain_gt_files lists plain prepared ground-truth
        files named by AV2 stage-A manifests (c1_freeze_v05 refuses while any exists).
  * chain_cache / chain_items as v03 with this deposit check; LAST_GUARD is also set in c1_guard_v03 (the Choice 36 delegation).
"""
import datetime
import gzip
import hashlib
import json
import os
import re
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v03 as G3  # noqa: E402
from c1_guard_v03 import (W, CANONICAL, HEX64, FOLDS_ROLES, sha, rel, versions, units_dataset, dataset_checked, manifest_dataset,  # noqa: E402,F401
                          folds_dataset, track_scenes, export_dataset, units_record, require_bound, require_folds, bound_in_role,
                          role_hash, project_modules, code_record, verify_runtime, verify_runtime_again, check_env, stage_a_inputs,
                          check_inputs, stage_a_only, check_child_folds, log_lines, Frozen, _section)

DEPOSIT_RECORD = os.path.join(W, "40_PROTOCOL", "C1_PLAN_DEPOSIT_RECORD_v01.txt")
DEPOSIT_GUIDE = "40_PROTOCOL/OSF_DEPOSIT_GUIDE_v02.md"
STAGE_B_LOG = os.path.join(W, "40_PROTOCOL", "C1_STAGE_B_LOG.txt")
RUN_LOG = os.path.join(W, "40_PROTOCOL", "C1_RUN_LOG.txt")
QUARANTINE = os.path.join(W, "30_DATA", "av2_gt_quarantine_v01")
QUARANTINE_MANIFEST = os.path.join(QUARANTINE, "QUARANTINE_MANIFEST.json")
DEPOSIT_EXEMPT = ("entry:c1_e0", "entry:c1_folds", "entry:c1_freeze")
OSF_URL = re.compile(r"^https://osf\.io/[a-z0-9]{5,}/?$")
OSF_DOI = re.compile(r"^10\.17605/OSF\.IO/[A-Z0-9]{5,}$")
ISO_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
LOGLINE_UTC = re.compile(r"(?:frozen|AMENDED) (\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) UTC")
EXEMPT_DS = ("nuscenes", "synthetic")
LAST_GUARD = {}


def utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def parse_iso(s):
    assert ISO_UTC.match(s or ""), "not an ISO 8601 UTC time (YYYY-MM-DDTHH:MM:SSZ): %r" % s
    return datetime.datetime.strptime(s.split(".")[0].rstrip("Z"), "%Y-%m-%dT%H:%M:%S").replace(tzinfo=datetime.timezone.utc)


def frozen_plan(plan, dataset, log=None, which="C1"):
    side, frozen = G3.frozen_plan(plan, dataset, log, which)
    txt = open(plan, encoding="utf-8").read()
    env = _section(txt, "FROZEN_ENV_TPP")
    frozen.env_tpp = dict(ln.split("  ", 1) for ln in env.strip().splitlines() if ln.strip() and not ln.startswith("#")) if env else None
    line = [ln for ln in log_lines(log or CANONICAL[which]) if ln.split()[0] == side][-1]
    m = LOGLINE_UTC.search(line)
    frozen.plan_logged_utc = (datetime.datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.timezone.utc) if m else None)
    return side, frozen


def stage_b_times(path=None):
    p = path or STAGE_B_LOG
    if not os.path.exists(p):
        return []
    return [parse_iso(json.loads(ln)["utc"]) for ln in open(p).read().splitlines() if ln.strip()]


def check_deposit(side, dataset, path=None, plan_logged=None, stage_b_log=None):
    """Choice 40 / 42a, m2: the external registration exists, names this plan and is consistent in time."""
    if path is not None and os.path.abspath(path) != os.path.abspath(DEPOSIT_RECORD):
        assert dataset in EXEMPT_DS, "a deposit-record override is refused for %s data (Choice 40)" % dataset
    p = path or DEPOSIT_RECORD
    hint = " (see %s; D16 v19 Choice 40, v21 Choice 42)" % DEPOSIT_GUIDE
    assert os.path.exists(p), "refused: no deposit record %s: the frozen plan has not been deposited%s" % (rel(p), hint)
    rec, keys = {}, []
    for ln in open(p, encoding="utf-8").read().splitlines():
        if ":" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.split(":", 1)
            keys.append(k.strip())
            rec[k.strip()] = v.strip()
    dup = sorted({k for k in keys if keys.count(k) > 1})
    assert not dup, "refused: duplicated keys in the deposit record: %s%s" % (dup, hint)
    h = rec.get("frozen_plan_sha256", "")
    assert HEX64.match(h), "refused: the deposit record has no frozen_plan_sha256 line%s" % hint
    assert h == side, "refused: the deposit record names plan %s..., not the frozen plan %s...%s" % (h[:12], side[:12], hint)
    reg = rec.get("registration", "")
    assert OSF_URL.match(reg) or OSF_DOI.match(reg), "refused: registration %r is not an OSF URL https://osf.io/<id>/ or DOI 10.17605/OSF.IO/<ID>%s" % (reg, hint)
    try:
        t = parse_iso(rec.get("registered_utc", ""))
    except AssertionError as ex:
        raise AssertionError("refused: registered_utc: %s%s" % (ex, hint))
    assert t <= utc_now(), "refused: registered_utc %s lies in the future%s" % (rec["registered_utc"], hint)
    if plan_logged is not None:
        assert t > plan_logged, "refused: registered_utc %s is not later than the plan's hash-log line (%s UTC)%s" % (rec["registered_utc"], plan_logged, hint)
    for b in stage_b_times(stage_b_log):
        assert t < b, "refused: registered_utc %s is not earlier than a stage-B build (%s)%s" % (rec["registered_utc"], b.isoformat(), hint)
    return {"record": rel(p), "sha256": sha(p), "registration": reg, "registered_utc": rec["registered_utc"]}


def deposit_sha(dataset, side=None, frozen=None, path=None):
    """The deposit field a table or record must carry now: the record's sha256 on AV2; 'exempt (<dataset>)' otherwise."""
    if dataset in EXEMPT_DS and path is None:
        return "exempt (%s)" % dataset
    return check_deposit(side, dataset, path, getattr(frozen, "plan_logged_utc", None))["sha256"]


def guard(dataset, plan, role, entry, log=None, which="C1", deposit_path=None):
    if plan is None:
        assert dataset in EXEMPT_DS, "%s: %s data need --plan, a frozen plan in %s (D16 Choice 34)" % (role, dataset, rel(CANONICAL[which]))
        assert log is None, "a hash log without a plan means nothing"
        return None
    side, frozen = frozen_plan(plan, dataset, log, which)
    check_env(frozen)
    rt = verify_runtime(frozen, role, entry)
    if role not in DEPOSIT_EXEMPT and (dataset not in EXEMPT_DS or deposit_path is not None):
        dep = check_deposit(side, dataset, deposit_path, frozen.plan_logged_utc)
        rt["deposit"], rt["deposit_record_sha256"] = dep, dep["sha256"]
    else:
        rt["deposit"], rt["deposit_record_sha256"] = None, ("exempt (%s)" % dataset if dataset in EXEMPT_DS else "exempt (%s)" % role)
    rec = {"role": role, "entry": rel(entry), "plan": os.path.abspath(plan), "plan_sha256": side, "dataset": dataset,
           "deposit_record_sha256": rt["deposit_record_sha256"]}
    for d in (LAST_GUARD, G3.LAST_GUARD):
        d.clear()
        d.update(rec)
    return side, frozen, rt


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
    assert check_deposit(side, ds, None, frozen.plan_logged_utc)["sha256"] == dep, "the deposit record differs from the stage-B cache's (Choice 40)"
    return {"manifest": rel(manifest_path), "sha256": h, "dataset": ds, "stage_a_manifest_sha256": sb["stage_a_manifest_sha256"],
            "deposit_record_sha256": dep, "chain": "stage B under this plan from a bound stage-A manifest, after the deposit"}


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


def check_table(table, side, frozen, folds_sha, role, units=None, dataset=None, units_subset_of=None, deposit=None):
    r = G3.check_table(table, side, frozen, folds_sha, role, units=units, dataset=dataset, units_subset_of=units_subset_of)
    got = (table.get("provenance") or {}).get("deposit_record_sha256")
    assert deposit is not None and got == deposit, "table deposit record %r differs from the current one %r (Choice 42a)" % (got, deposit)
    return r


def check_scene_json(frozen, meta_dir, units):
    """m3: scene.json bound as data:scene_json, and every unit's log equal to the bound stage-A manifests' log."""
    p = os.path.join(meta_dir, "scene.json")
    require_bound(frozen, p, "data:scene_json")
    smap = {s["name"]: s["log_token"] for s in json.load(open(p))}
    logs = {}
    for mp in (frozen.roles or {}).get("stageA_manifest", []):
        for u, info in (json.load(open(os.path.join(W, mp))).get("scenes") or {}).items():
            if isinstance(info, dict) and "log" in info:
                logs[str(u)] = str(info["log"])
    bad = [u for u in units if u not in logs or smap.get(u) != logs[u]]
    assert not bad, "scene.json's log differs from the stage-A manifests' (or a unit is missing) for %d units, e.g. %s (R17d m3)" % (len(bad), bad[:3])
    return {"scene_json": rel(p), "sha256": sha(p), "units_checked": len(units)}


def refuse_existing(paths, dataset):
    if dataset in EXEMPT_DS:
        return
    there = [rel(p) for p in paths if os.path.exists(p)]
    assert not there, "outputs on AV2 are never overwritten (Choice 42g): %s exists; use a new, logged output name" % there


def run_log_append(dataset, entry, side, deposit, inputs, outputs, note=None):
    """(g) one line per guarded AV2 run, append-only, flushed."""
    if dataset in EXEMPT_DS:
        return None
    rec = {"utc": utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"), "entry": rel(entry), "plan_sha256": side, "deposit_record_sha256": deposit,
           "inputs_sha256": inputs, "outputs_sha256": {rel(p): sha(p) for p in outputs if os.path.exists(p)}, "note": note}
    os.makedirs(os.path.dirname(RUN_LOG), exist_ok=True)
    with open(RUN_LOG, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
        f.flush()
        os.fsync(f.fileno())
    return rec


def quarantine_members():
    if not os.path.exists(QUARANTINE_MANIFEST):
        return []
    return json.load(open(QUARANTINE_MANIFEST)).get("members", [])


def open_quarantined(gz_path, want_sha):
    """B2: the decompressed bytes of a quarantine member, only if their SHA-256 is the one the stage-A manifest recorded."""
    assert os.path.abspath(gz_path).startswith(os.path.abspath(QUARANTINE) + os.sep) and gz_path.endswith(".gz"), \
        "ground truth on AV2 is read only from the quarantine %s (Choice 42b): %s" % (rel(QUARANTINE), gz_path)
    b = gzip.open(gz_path, "rb").read()
    assert hashlib.sha256(b).hexdigest() == want_sha, "the quarantined ground truth differs from the stage-A manifest's hash"
    return b


def materialise_quarantined(gz_path, want_sha):
    """A temporary decompressed copy OUTSIDE the workspace (for code that reads a path); the caller removes it."""
    b = open_quarantined(gz_path, want_sha)
    d = tempfile.mkdtemp(prefix="c1_gt_")
    assert not os.path.abspath(d).startswith(os.path.abspath(W)), "the temporary ground truth must lie outside the workspace"
    p = os.path.join(d, os.path.basename(gz_path)[:-3])
    open(p, "wb").write(b)
    return p


def member_for(want_sha):
    for m in quarantine_members():
        if m.get("sha256_decompressed") == want_sha:
            return os.path.join(QUARANTINE, m["member"])
    return None


def stage_a_gt(frozen_or_paths):
    """[(manifest, recorded gt path, recorded gt sha)] of the AV2 stage-A manifests (bound ones, or the paths given)."""
    paths = frozen_or_paths if isinstance(frozen_or_paths, (list, tuple)) else \
        [os.path.join(W, p) for p in (frozen_or_paths.roles or {}).get("stageA_manifest", [])]
    out = []
    for mp in paths:
        m = json.load(open(mp))
        if manifest_dataset(m) in EXEMPT_DS:
            continue
        i = m.get("inputs") or {}
        if i.get("gt"):
            out.append((mp, i["gt"], i.get("gt_sha256")))
    return out


def plain_gt_files(manifests):
    """B2: plain prepared ground-truth files named by AV2 stage-A manifests that still exist (by the recorded path, or the same
    path under this workspace's 30_DATA)."""
    found = []
    for mp, gp, gs in stage_a_gt(list(manifests)):
        cands = [gp]
        norm = gp.replace("\\", "/")
        if "/30_DATA/" in norm:
            cands.append(os.path.join(W, "30_DATA", *norm.split("/30_DATA/", 1)[1].split("/")))
        found += [c for c in cands if os.path.exists(c)]
    return sorted(set(found))


def resolve_gt(frozen, gt_arg, dataset):
    """The ground-truth path an entry point may read: the plain file on nuScenes; on AV2 a quarantine member, decompressed to a temporary
    file outside the workspace, whose SHA-256 must be a gt_sha256 of a bound stage-A manifest. Returns (path, temporary_or_None, sha)."""
    if dataset in EXEMPT_DS:
        return gt_arg, None, sha(gt_arg)
    recs = [m for m in quarantine_members() if os.path.abspath(os.path.join(QUARANTINE, m["member"])) == os.path.abspath(gt_arg)]
    assert recs, "ground truth on AV2 is read only from a member of %s (Choice 42b): %s" % (rel(QUARANTINE), gt_arg)
    want = recs[0]["sha256_decompressed"]
    assert want in {gs for _, _, gs in stage_a_gt(frozen)}, "the quarantine member is not the ground truth of a bound stage-A manifest"
    tmp = materialise_quarantined(gt_arg, want)
    return tmp, tmp, want


def cleanup(tmp):
    if tmp and os.path.exists(tmp):
        d = os.path.dirname(tmp)
        os.remove(tmp)
        if os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
