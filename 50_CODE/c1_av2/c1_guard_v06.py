#!/usr/bin/env python3
"""C1 guards v06 (Claude line, c1_guard_v06, 5 Nov 2026) = c1_guard_v05 (kept, imported: everything; the v08/v09 entry points keep
using c1_guard_v05) plus the helpers c1_freeze_v07 needs for D16 v27 Choice 48 (R17f M-1, m-3):
  * scan_plain_v06: c1_guard_v05.scan_plain, and it also returns the folders it skipped, by path and reason (50_CODE/env/, the
    quarantine folder, a name holding a banned word), read from the parent listing without opening them (m-3).
  * quarantine_folder_unexpected: every entry of 30_DATA/av2_gt_quarantine_v01/ that is neither QUARANTINE_MANIFEST.json nor a
    recorded member (a plain or extracted copy, a .tmp, a subfolder) (48a ii, R17f N1).
  * member_manifests_missing: recorded stage-A members whose stage-A manifest is no longer at its recorded path (48a iii, R17f N2).
  * inventory_files: the files of a GT inventory written by c1_av2_gt_inventory_v01 (path, sha256, bytes) (48a i).
  * provenance_record_check: a data:provenance file must be a success record of c1_av2_provenance_v01 for the README being bound,
    made with every check (exports, horizon, ego, gt, scene_json; the CLI's set), and cover the AV2 stage-A manifests given (48b m-2).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v05 as G5  # noqa: E402
from c1_guard_v05 import *  # noqa: E402,F401,F403
from c1_guard_v05 import W, QUARANTINE, QUARANTINE_MANIFEST, ENV_DIR, SKIP_DIR_WORDS, rel, sha, sha_stream, quarantine_members  # noqa: E402,F401


def scan_plain_v06(root, sizes, wanted, excludes=()):
    """As c1_guard_v05.scan_plain; returns (matches, files hashed, skipped folders [(path, reason)])."""
    excl = {os.path.abspath(ENV_DIR): "50_CODE/env/ (environments)", os.path.abspath(QUARANTINE): "the quarantine folder (checked by name)"}
    for x in excludes:
        excl[os.path.abspath(x)] = "excluded by the caller"
    matches, hashed, skipped = [], 0, []
    for dp, dn, fn in os.walk(root):
        keep = []
        for d in dn:
            p = os.path.abspath(os.path.join(dp, d))
            low = d.lower()
            word = [w for w in SKIP_DIR_WORDS if w in low]
            if p in excl:
                skipped.append((rel(p), excl[p]))
            elif word:
                skipped.append((rel(p), "name holds a banned word (%s); not opened" % word[0]))
            else:
                keep.append(d)
        dn[:] = keep
        if not sizes:
            continue
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
    return sorted(matches), hashed, sorted(skipped)


def quarantine_folder_unexpected(members=None):
    """Entries of the quarantine folder that are neither its manifest nor a recorded member."""
    if not os.path.isdir(QUARANTINE):
        return []
    members = quarantine_members() if members is None else members
    allowed = {os.path.basename(QUARANTINE_MANIFEST)} | {m["member"] for m in members}
    out = []
    for n in sorted(os.listdir(QUARANTINE)):
        p = os.path.join(QUARANTINE, n)
        if os.path.isdir(p) or n not in allowed:
            out.append(rel(p) + ("/" if os.path.isdir(p) else ""))
    return out


def member_manifests_missing(members=None):
    """Recorded stage-A members whose stage-A manifest is not at its recorded path: [(member, manifest)]."""
    members = quarantine_members() if members is None else members
    out = []
    for m in members:
        kinds = m.get("kinds") or ["stage_a"]
        if "stage_a" not in kinds:
            continue
        mans = m.get("stage_a_manifests") or ([m["stage_a_manifest"]] if m.get("stage_a_manifest") else [])
        if not mans:
            out.append((m["member"], "(none recorded)"))
        for mp in mans:
            q = mp if os.path.isabs(mp) else os.path.join(W, mp)
            if not os.path.isfile(q):
                out.append((m["member"], mp))
    return out


def inventory_files(path):
    """The files of a c1_av2_gt_inventory_v01 inventory: [{"path", "sha256", "bytes", ...}] (pending entries carry no hash)."""
    inv = json.load(open(path))
    assert inv.get("tool") == "c1_av2_gt_inventory_v01", "%s is not a GT inventory of c1_av2_gt_inventory_v01" % rel(path)
    return [f for f in inv.get("files", []) if f.get("sha256")]


PROVENANCE_KINDS = ("exports", "horizon", "ego", "gt", "scene_json")


def provenance_record_check(path, readme, av2_manifests):
    """48(b) m-2: a success record of c1_av2_provenance_v01, for this README, covering every AV2 stage-A manifest given (by hash)."""
    r = json.load(open(path))
    assert r.get("tool") == "c1_av2_provenance_v01", "%s is not a record of c1_av2_provenance_v01 (Choice 48b m-2)" % rel(path)
    assert r.get("ok") is True and r.get("status") == "PASS", "%s is not a success record (Choice 48b m-2)" % rel(path)
    lack = [k for k in PROVENANCE_KINDS if k not in (r.get("kinds") or [])]
    assert not lack, "%s was made without the checks %s (the CLI makes every check; Choice 48b m-2)" % (rel(path), lack)
    assert r.get("readme_sha256") == sha(readme), "%s was made for another README (%s...), not %s (Choice 48b m-2)" % (
        rel(path), str(r.get("readme_sha256"))[:12], rel(readme))
    cov = r.get("manifests") or {}
    miss = [rel(m) for m in av2_manifests if (cov.get(rel(m)) or {}).get("sha256") != sha(m)]
    assert not miss, "the provenance record does not cover these AV2 stage-A manifests as they are now: %s (Choice 48b m-2)" % miss[:3]
    return {"record": rel(path), "sha256": sha(path), "manifests": len(cov)}
