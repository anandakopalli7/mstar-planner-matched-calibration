#!/usr/bin/env python3
"""C1 guards v05 (Claude line, c1_guard_v05, 5 Nov 2026) = c1_guard_v04 (kept, imported: deposit record, quarantine readers, scene.json
check, check_table, refuse_existing; and through it c1_guard_v03) with R17e's fixes as D16 v23 Choice 44 decides:
  * 44(f) m1, the run log 40_PROTOCOL/C1_RUN_LOG.txt is chained and has two lines per run. guard() writes a "start" line on AV2, before
        the entry point reads any ground truth or table (the entry point has read only unit names or dataset tags before it).
        run_log_append() writes the "done" line with the output hashes. Each line is one JSON object with prev_sha256 = the SHA-256 of
        the previous line's bytes (64 zeros for the first). Lines are written in binary under a lock file, and the whole chain is
        verified before every write. read_run_log() verifies it; logged_outputs() returns the output hashes of the "done" lines.
  * 44(c) nonexempt_lines(): run-log lines whose role is not entry:c1_e0, entry:c1_folds or entry:c1_freeze. c1_freeze_v06 refuses
        --amend while any exists.
  * 44(f) m2, check_deposit: the registration must not be the OSF project in 40_PROTOCOL/OSF_PROJECT_RECORD_v01.txt (osf_project_id,
        osf_project_url), as a URL or a DOI, in any case. The plan's hash-log line must carry a parsable time ("frozen|AMENDED
        YYYY-MM-DD HH:MM:SS UTC"); otherwise the record is refused, not passed unchecked.
  * 44(f) m7: guard() first sweeps stale c1_gt_* folders from the temporary directory. A folder is stale if the process that made it
        has ended (the pid is in the name: c1_gt_<pid>_*), or, for a v04-style name without a pid, if it is older than 10 minutes.
        materialise_quarantined() writes c1_gt_<pid>_* folders.
  * 44(a) helpers for c1_quarantine_v02 and c1_freeze_v06: av2_stage_a_manifests() finds every AV2 stage-A MANIFEST.json under a root.
        local_copies() returns the plain copies of a recorded path. member_size() gives the decompressed size of a quarantine member.
        scan_plain() hashes every file whose size equals a ground truth's size; it skips 50_CODE/env/, the quarantine folder, and any
        folder whose name holds "restricted", "sealed", "do_not_open", "participant" or "codex".
  * chain_cache, chain_items and deposit_sha call this module's check_deposit. LAST_GUARD is set here and in c1_guard_v04 and
    c1_guard_v03.
"""
import contextlib
import datetime
import gzip
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v03 as G3  # noqa: E402
import c1_guard_v04 as G4  # noqa: E402
from c1_guard_v04 import (W, CANONICAL, HEX64, FOLDS_ROLES, sha, rel, versions, units_dataset, dataset_checked, manifest_dataset,  # noqa: E402,F401
                          folds_dataset, track_scenes, export_dataset, units_record, require_bound, require_folds, bound_in_role,
                          role_hash, project_modules, code_record, verify_runtime, verify_runtime_again, check_env, stage_a_inputs,
                          check_inputs, stage_a_only, check_child_folds, log_lines, Frozen, _section, DEPOSIT_RECORD, DEPOSIT_GUIDE,
                          STAGE_B_LOG, RUN_LOG, QUARANTINE, QUARANTINE_MANIFEST, DEPOSIT_EXEMPT, OSF_URL, OSF_DOI, ISO_UTC, LOGLINE_UTC,
                          EXEMPT_DS, utc_now, parse_iso, stage_b_times, frozen_plan, check_table, check_scene_json, refuse_existing,
                          quarantine_members, open_quarantined, member_for, stage_a_gt, plain_gt_files, cleanup)

SLOT = G3.SLOT
OSF_PROJECT_RECORD = os.path.join(W, "40_PROTOCOL", "OSF_PROJECT_RECORD_v01.txt")
GENESIS = "0" * 64
RUN_LOCK_STALE_S = 600
TMP_STALE_S = 600
SKIP_DIR_WORDS = ("restricted", "sealed", "do_not_open", "participant", "codex")
ENV_DIR = os.path.join(W, "50_CODE", "env")
LAST_GUARD = {}


# ---------------------------------------------------------------------------------------------------------------- m2: deposit record
def project_ids(path=None):
    """The OSF project id(s) of the C1 deposit, from OSF_PROJECT_RECORD_v01.txt (osf_project_id and osf_project_url), lower case."""
    p = path or OSF_PROJECT_RECORD
    assert os.path.exists(p), "refused: no OSF project record %s, so a project cannot be told from a registration (Choice 44f m2)" % rel(p)
    ids = set()
    for ln in open(p, encoding="utf-8").read().splitlines():
        if ":" not in ln:
            continue
        k, v = ln.split(":", 1)
        k, v = k.strip(), v.strip()
        if k == "osf_project_id" and v:
            ids.add(v.lower())
        elif k == "osf_project_url":
            m = re.match(r"^https://osf\.io/([A-Za-z0-9]+)/?", v)
            if m:
                ids.add(m.group(1).lower())
    assert ids, "refused: the OSF project record names no project id (Choice 44f m2)"
    return ids


def registration_id(reg):
    m = re.match(r"^https://osf\.io/([A-Za-z0-9]+)/?$", reg or "")
    if m:
        return m.group(1).lower()
    m = re.match(r"^10\.17605/OSF\.IO/([A-Za-z0-9]+)$", reg or "", re.IGNORECASE)
    return m.group(1).lower() if m else None


def check_deposit(side, dataset, path=None, plan_logged=None, stage_b_log=None, project_record=None):
    """c1_guard_v04.check_deposit, plus Choice 44(f) m2: a parsable plan-line time is required, and the registration is not the project."""
    hint = " (see %s; D16 v23 Choice 44f m2)" % DEPOSIT_GUIDE
    assert plan_logged is not None, "refused: the plan's line in the hash log has no parsable time ('frozen|AMENDED YYYY-MM-DD HH:MM:SS UTC'), " \
                                    "so registered_utc cannot be checked against it%s" % hint
    r = G4.check_deposit(side, dataset, path, plan_logged, stage_b_log)
    rid = registration_id(r["registration"])
    assert rid and rid not in project_ids(project_record), \
        "refused: registration %r is the OSF project, not the registration of the frozen plan%s" % (r["registration"], hint)
    return r


def deposit_sha(dataset, side=None, frozen=None, path=None):
    if dataset in EXEMPT_DS and path is None:
        return "exempt (%s)" % dataset
    return check_deposit(side, dataset, path, getattr(frozen, "plan_logged_utc", None))["sha256"]


# ---------------------------------------------------------------------------------------------------------------- m7: stale temporary ground truth
def _pid_alive(pid):
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, int(pid))  # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259  # STILL_ACTIVE
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False


def sweep_stale_tmp(tmp_root=None):
    """m7: remove c1_gt_* folders (decompressed ground truth) left by a killed run. Returns the folders removed."""
    root = tmp_root or tempfile.gettempdir()
    removed = []
    try:
        names = os.listdir(root)
    except OSError:
        return removed
    for n in names:
        p = os.path.join(root, n)
        if not (n.startswith("c1_gt_") and os.path.isdir(p)):
            continue
        m = re.match(r"^c1_gt_(\d+)_", n)
        try:
            stale = (not _pid_alive(int(m.group(1)))) if m else (time.time() - os.path.getmtime(p) > TMP_STALE_S)
        except (OSError, ValueError):
            continue
        if stale:
            shutil.rmtree(p, ignore_errors=True)
            if not os.path.exists(p):
                removed.append(n)
    return removed


def materialise_quarantined(gz_path, want_sha):
    """As c1_guard_v04's, in a c1_gt_<pid>_* folder OUTSIDE the workspace (so that a later guard can tell a live folder from a stale one)."""
    b = open_quarantined(gz_path, want_sha)
    d = tempfile.mkdtemp(prefix="c1_gt_%d_" % os.getpid())
    assert not os.path.abspath(d).startswith(os.path.abspath(W)), "the temporary ground truth must lie outside the workspace"
    p = os.path.join(d, os.path.basename(gz_path)[:-3])
    with open(p, "wb") as f:
        f.write(b)
    return p


def resolve_gt(frozen, gt_arg, dataset):
    """c1_guard_v04.resolve_gt with this module's materialise_quarantined."""
    if dataset in EXEMPT_DS:
        return gt_arg, None, sha(gt_arg)
    recs = [m for m in quarantine_members() if os.path.abspath(os.path.join(QUARANTINE, m["member"])) == os.path.abspath(gt_arg)]
    assert recs, "ground truth on AV2 is read only from a member of %s (Choice 42b): %s" % (rel(QUARANTINE), gt_arg)
    want = recs[0]["sha256_decompressed"]
    assert want in {gs for _, _, gs in stage_a_gt(frozen)}, "the quarantine member is not the ground truth of a bound stage-A manifest"
    tmp = materialise_quarantined(gt_arg, want)
    return tmp, tmp, want


# ---------------------------------------------------------------------------------------------------------------- m1: the chained run log
def _line_sha(line):
    return hashlib.sha256(line.encode("utf-8")).hexdigest()


def read_run_log(path=None):
    """Every line of the run log, its chain verified. Returns (records, SHA-256 of the last line or GENESIS)."""
    p = path or RUN_LOG
    if not os.path.exists(p):
        return [], GENESIS
    raw = open(p, "rb").read().decode("utf-8")
    assert raw == "" or raw.endswith("\n"), "the run log %s does not end with a complete line (truncated or edited; Choice 44f m1)" % rel(p)
    prev, recs = GENESIS, []
    for i, ln in enumerate(raw.split("\n")[:-1]):
        try:
            rec = json.loads(ln)
        except ValueError:
            raise AssertionError("line %d of the run log %s is not one JSON object (Choice 44f m1)" % (i + 1, rel(p)))
        assert isinstance(rec, dict) and rec.get("prev_sha256") == prev, \
            "the run log %s is broken at line %d: prev_sha256 is not the previous line's hash (Choice 44f m1)" % (rel(p), i + 1)
        recs.append(rec)
        prev = _line_sha(ln)
    return recs, prev


@contextlib.contextmanager
def _run_lock(p):
    lk = p + ".lock"
    t0 = time.time()
    while True:
        try:
            fd = os.open(lk, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            break
        except FileExistsError:
            try:
                if time.time() - os.path.getmtime(lk) > RUN_LOCK_STALE_S:
                    os.remove(lk)
                    continue
            except OSError:
                continue
            assert time.time() - t0 < 300, "the run log is locked by %s" % rel(lk)
            time.sleep(0.2)
    try:
        yield
    finally:
        try:
            os.remove(lk)
        except OSError:
            pass


def run_log_write(rec, path=None):
    """Append one chained line (binary, flushed, fsynced) after verifying the whole chain."""
    p = path or RUN_LOG
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with _run_lock(p):
        _, prev = read_run_log(p)
        rec = dict(rec, utc=utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"), prev_sha256=prev)
        line = json.dumps(rec, sort_keys=True, default=str)
        assert "\n" not in line
        with open(p, "ab") as f:
            f.write((line + "\n").encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
    return rec


def run_log_append(dataset, entry, side, deposit, inputs, outputs, note=None, path=None):
    """The "done" line of the run whose "start" line guard() wrote in this process (c1_guard_v04's signature)."""
    if dataset in EXEMPT_DS:
        return None
    rid = LAST_GUARD.get("run_id")
    assert rid and LAST_GUARD.get("entry") == rel(entry), "a run-log 'done' line without this run's 'start' line (Choice 44f m1)"
    return run_log_write({"event": "done", "run_id": rid, "role": LAST_GUARD.get("role"), "entry": rel(entry), "plan_sha256": side,
                          "deposit_record_sha256": deposit, "inputs_sha256": inputs,
                          "outputs_sha256": {rel(p): sha(p) for p in outputs if os.path.exists(p)}, "note": note}, path)


def logged_outputs(path=None):
    """{output sha256: [(path, entry, run_id)]} from the "done" lines of the verified run log, and the log's own record."""
    p = path or RUN_LOG
    recs, last = read_run_log(p)
    out = {}
    for r in recs:
        if r.get("event") == "done":
            for q, h in (r.get("outputs_sha256") or {}).items():
                out.setdefault(h, []).append((q, r.get("entry"), r.get("run_id")))
    return out, {"run_log": rel(p), "run_log_sha256": sha(p) if os.path.exists(p) else None, "lines": len(recs), "last_line_sha256": last}


def nonexempt_lines(path=None):
    """44(c): run-log lines from any role other than entry:c1_e0, entry:c1_folds and entry:c1_freeze (a line without a role counts)."""
    recs, _ = read_run_log(path)
    return [r for r in recs if r.get("role") not in DEPOSIT_EXEMPT]


# ---------------------------------------------------------------------------------------------------------------- 44(e): Trajectron++ environments
def env_check(frozen, rec, kind):
    """44(e): a tpp_keys_v03 record is compared with FROZEN_ENV (canmot310: python, numpy), a tpp_run_v03 record with FROZEN_ENV_TPP
    (tpp38: python, numpy, torch). rec is a wrapper record or a dry record (c1_tpp_envcheck_v01 --write-dry)."""
    assert kind in ("tpp_keys", "tpp_run"), "kind is tpp_keys or tpp_run, not %r" % kind
    if kind == "tpp_keys":
        want, keys, block, env = getattr(frozen, "env", None), ("python", "numpy"), "FROZEN_ENV", "canmot310"
    else:
        want, keys, block, env = getattr(frozen, "env_tpp", None), ("python", "numpy", "torch"), "FROZEN_ENV_TPP", "tpp38"
    assert want, "the plan has no %s block (Choice 44e)" % block
    got = (rec or {}).get("versions") or {}
    bad = {k: (want.get(k), got.get(k)) for k in keys if str(want.get(k)) != str(got.get(k))}
    assert not bad, "the versions of a %s record differ from %s: %s (Choice 44e: %s runs under %s)" % (kind, block, bad, kind, env)
    return {k: got.get(k) for k in keys}


# ---------------------------------------------------------------------------------------------------------------- the guard
def guard(dataset, plan, role, entry, log=None, which="C1", deposit_path=None):
    swept = sweep_stale_tmp()
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
    rt["swept_tmp"] = swept
    rec = {"role": role, "entry": rel(entry), "plan": os.path.abspath(plan), "plan_sha256": side, "dataset": dataset,
           "deposit_record_sha256": rt["deposit_record_sha256"]}
    if dataset not in EXEMPT_DS:
        rid = uuid.uuid4().hex
        run_log_write({"event": "start", "run_id": rid, "role": role, "entry": rel(entry), "plan_sha256": side,
                       "deposit_record_sha256": rt["deposit_record_sha256"], "argv": [str(x) for x in sys.argv[1:]], "pid": os.getpid()})
        rt["run_id"] = rec["run_id"] = rid
    for d in (LAST_GUARD, G4.LAST_GUARD, G3.LAST_GUARD):
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


# ---------------------------------------------------------------------------------------------------------------- 44(a): finding ground truth
def _skip_dir(path, name, excludes):
    low = name.lower()
    return any(w in low for w in SKIP_DIR_WORDS) or any(os.path.abspath(path) == e for e in excludes)


def av2_stage_a_manifests(root, max_depth=4):
    """Every AV2 stage-A MANIFEST.json (with inputs.gt) under root, down to max_depth folder levels; the quarantine folder is skipped."""
    found = []
    if not os.path.isdir(root):
        return found
    base = os.path.abspath(root).rstrip("\\/").count(os.sep)
    excl = [os.path.abspath(QUARANTINE), os.path.abspath(ENV_DIR)]
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not _skip_dir(os.path.join(dp, d), d, excl)]
        if os.path.abspath(dp).count(os.sep) - base >= max_depth:
            dn[:] = []
        if "MANIFEST.json" in fn:
            p = os.path.join(dp, "MANIFEST.json")
            try:
                m = json.load(open(p))
                if m.get("stage", "A") == "A" and manifest_dataset(m) == "av2" and (m.get("inputs") or {}).get("gt"):
                    found.append(os.path.abspath(p))
            except (ValueError, OSError, UnicodeDecodeError, AttributeError, AssertionError, KeyError, TypeError):
                continue
    return sorted(found)


def local_copies(recorded):
    """The existing plain copies of a recorded ground-truth path: the path itself and, if it contains /30_DATA/, the same path under this
    workspace's 30_DATA (a stage A built on a pod records the pod's path)."""
    cands = [recorded if os.path.isabs(recorded) else os.path.join(W, recorded)]
    norm = recorded.replace("\\", "/")
    if "/30_DATA/" in norm or norm.startswith("30_DATA/"):
        tail = norm.split("30_DATA/", 1)[1]
        cands.append(os.path.join(W, "30_DATA", *tail.split("/")))
    out = []
    for c in cands:
        if os.path.isfile(c) and os.path.abspath(c) not in [os.path.abspath(x) for x in out]:
            out.append(c)
    return out


def member_size(m):
    """The decompressed size of a quarantine member (recorded by c1_quarantine_v02; computed for a v01 member)."""
    if isinstance(m.get("bytes"), int):
        return m["bytes"]
    n = 0
    with gzip.open(os.path.join(QUARANTINE, m["member"]), "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            n += len(b)
    return n


def sha_stream(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def scan_plain(root, sizes, wanted, excludes=()):
    """Every file under root whose size is in sizes and whose SHA-256 is in wanted: [(path, sha)]. Skips 50_CODE/env/, the quarantine
    folder, the given folders and folders named restricted / sealed / do_not_open / participant / codex. Returns (matches, files hashed)."""
    excl = [os.path.abspath(x) for x in (ENV_DIR, QUARANTINE) + tuple(excludes)]
    matches, hashed = [], 0
    if not sizes:
        return matches, hashed
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if not _skip_dir(os.path.join(dp, d), d, excl)]
        for f in fn:
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) not in sizes:
                    continue
                hashed += 1
                h = sha_stream(p)
            except OSError:
                continue
            if h in wanted:
                matches.append((os.path.abspath(p), h))
    return sorted(matches), hashed
