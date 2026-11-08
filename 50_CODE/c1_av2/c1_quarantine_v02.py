#!/usr/bin/env python3
"""C1 ground-truth quarantine v02 (Claude line, c1_quarantine_v02, 5 Nov 2026; D16 v23 Choice 44a, v24 Choice 45b; R17e M-A). A lead tool, run
after every prepared AV2 ground-truth file exists (stage A for the 375 logs, the detection and tracker-metric ground truths), after E0
and the Rule-0 metrics, and before the freeze. c1_quarantine_v01 is kept unchanged (superseded, not bound).
What it covers, as a union:
  1. the stage-A manifests passed with --stageA-manifests;
  2. every AV2 stage-A MANIFEST.json under this workspace's 30_DATA (to 4 folder levels), whether passed or not;
  3. the prepared ground-truth files listed with --extra (paths relative to the workspace or absolute), e.g.
     30_DATA/av2_det_v01/lt3d_centerpoint/av2val_lt3d_centerpoint_gt_v01.feather. Each is recorded in the quarantine manifest (kind
     "extra", its path and hash), so that c1_freeze_v06 knows its hash after the plain file is gone.
For every recorded ground-truth hash:
  * every plain copy at the recorded path (and at the same path under this workspace's 30_DATA) must have exactly that hash;
  * a hash scan of the whole workspace (files of the same size only; 50_CODE/env/, the quarantine folder and folders named restricted,
    sealed, do_not_open, participant or codex are skipped) finds every other plain copy, whatever its name;
  * the bytes go into one gzip member (mtime 0) in 30_DATA/av2_gt_quarantine_v01/, written to a temporary name, flushed and renamed;
    the member is re-read and must decompress to exactly those bytes (the recorded hash);
  * only then is every plain copy removed. The bytes are always kept in the member.
QUARANTINE_MANIFEST.json (rewritten atomically) lists per member: member, sha256_decompressed, sha256_gz, bytes, kinds, sources,
stage-A manifests, removed copies, UTC. Members written by c1_quarantine_v01 are kept and completed (bytes, kinds).
Idempotent and resumable. --dry-run hashes files and reports what it would do; it writes, creates and removes nothing. No record is
parsed: ground-truth files are read only as bytes, for hashing and compression.
Usage: <canmot310 python> -B c1_quarantine_v02.py [--stageA-manifests <MANIFEST.json ...>] [--extra <file ...>] [--dry-run]
"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v05 as G  # noqa: E402

RULE = ("D16 v21 Choice 42b, v23 Choice 44a: gzip members of every prepared AV2 ground-truth file (stage-A manifests passed or found under "
        "30_DATA, and --extra files); decompressed SHA-256 = the recorded hash; every plain copy found by path or by hash removed after "
        "verification")


def now():
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def abs_w(p):
    return p if os.path.isabs(p) else os.path.join(G.W, p)


def targets(manifests, extras, members):
    """{sha: {"kinds", "sources", "manifests", "copies"}} for every recorded ground truth."""
    t = {}
    for mp, gp, gs in G.stage_a_gt(manifests):
        assert gs and G.HEX64.match(gs), "stage-A manifest %s records no gt_sha256" % G.rel(mp)
        e = t.setdefault(gs, {"kinds": set(), "sources": set(), "manifests": set(), "copies": set()})
        e["kinds"].add("stage_a")
        e["sources"].add(gp)
        e["manifests"].add(G.rel(mp))
        for c in G.local_copies(gp):
            got = G.sha_stream(c)
            assert got == gs, "the plain ground truth %s differs from the hash its stage-A manifest %s recorded" % (G.rel(c), G.rel(mp))
            e["copies"].add(os.path.abspath(c))
    by_source = {}
    for m in members.values():
        for s in m.get("sources") or [m.get("source")]:
            if s:
                by_source[os.path.abspath(abs_w(s))] = m["sha256_decompressed"]
    for x in extras:
        p = os.path.abspath(abs_w(x))
        if os.path.isfile(p):
            gs = G.sha_stream(p)
        else:
            gs = by_source.get(p)
            assert gs, "--extra %s is neither a plain file nor recorded in the quarantine manifest" % x
        e = t.setdefault(gs, {"kinds": set(), "sources": set(), "manifests": set(), "copies": set()})
        e["kinds"].add("extra")
        e["sources"].add(G.rel(p))
        if os.path.isfile(p):
            e["copies"].add(p)
    return t


def member_name(src, gs, members):
    base = os.path.basename(src.replace("\\", "/")) + ".gz"
    m = members.get(base)
    if m is None or m.get("sha256_decompressed") == gs:
        return base
    stem = base[:-3]
    return "%s_%s.gz" % (stem, gs[:12])


def write_manifest(members):
    man = {"rule": RULE, "members": sorted(members.values(), key=lambda m: m["member"])}
    tmp = G.QUARANTINE_MANIFEST + ".tmp"
    with open(tmp, "w") as f:
        json.dump(man, f, indent=1, default=sorted)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, G.QUARANTINE_MANIFEST)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stageA-manifests", nargs="*", default=[])
    ap.add_argument("--extra", nargs="*", default=[])
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    found = G.av2_stage_a_manifests(os.path.join(G.W, "30_DATA"))
    manifests = sorted({os.path.abspath(p) for p in a.stageA_manifests} | set(found))
    members = {m["member"]: dict(m) for m in G.quarantine_members()}
    for m in members.values():
        m.setdefault("sources", [m["source"]] if m.get("source") else [])
        m.setdefault("kinds", ["stage_a"])
        m.setdefault("stage_a_manifests", [m["stage_a_manifest"]] if m.get("stage_a_manifest") else [])
        m.setdefault("removed", [])
    t = targets(manifests, a.extra, members)
    by_sha = {m["sha256_decompressed"]: m for m in members.values()}
    sizes, unknown = {}, []
    for gs, e in t.items():
        if e["copies"]:
            sizes[gs] = os.path.getsize(sorted(e["copies"])[0])
        elif gs in by_sha:
            sizes[gs] = G.member_size(by_sha[gs])
        else:
            unknown.append(gs)
    assert not unknown, "recorded ground truth with neither a plain copy nor a quarantine member: %s" % \
        [sorted(t[g]["sources"]) for g in unknown][:3]
    matches, hashed = G.scan_plain(G.W, set(sizes.values()), set(t))
    for p, gs in matches:
        t[gs]["copies"].add(p)
    report = {"manifests_passed": [G.rel(p) for p in a.stageA_manifests], "manifests_found": [G.rel(p) for p in found],
              "extras": a.extra, "recorded_hashes": len(t), "files_hashed_by_size": hashed, "actions": []}
    for gs in sorted(t):
        e = t[gs]
        copies = sorted(e["copies"])
        m = by_sha.get(gs)
        act = {"sha256": gs, "kinds": sorted(e["kinds"]), "sources": sorted(e["sources"]), "copies": [G.rel(c) for c in copies]}
        if a.dry_run:
            act["action"] = ("member exists; would remove %d plain copies" % len(copies)) if m else \
                            ("would quarantine and remove %d plain copies" % len(copies))
            report["actions"].append(act)
            continue
        if m is not None:
            b = gzip.open(os.path.join(G.QUARANTINE, m["member"]), "rb").read()
            assert hashlib.sha256(b).hexdigest() == gs, "an existing quarantine member differs from its recorded hash: " + m["member"]
            nbytes = len(b)
        else:
            raw = open(copies[0], "rb").read()
            assert hashlib.sha256(raw).hexdigest() == gs, "a plain copy changed while it was read: " + G.rel(copies[0])
            os.makedirs(G.QUARANTINE, exist_ok=True)
            name = member_name(sorted(e["sources"])[0], gs, members)
            dst = os.path.join(G.QUARANTINE, name)
            tmp = dst + ".tmp"
            with open(tmp, "wb") as f:
                with gzip.GzipFile(filename=name[:-3], mode="wb", fileobj=f, mtime=0) as g:
                    g.write(raw)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, dst)
            back = gzip.open(dst, "rb").read()
            assert back == raw and hashlib.sha256(back).hexdigest() == gs, "the quarantine member does not decompress to the plain bytes: " + name
            nbytes = len(raw)
            m = {"member": name, "sha256_decompressed": gs, "sha256_gz": G.sha(dst), "utc": now(), "sources": [], "kinds": [],
                 "stage_a_manifests": [], "removed": []}
            members[name] = by_sha[gs] = m
        m["bytes"] = nbytes
        m["sources"] = sorted(set(m.get("sources") or []) | set(e["sources"]))
        m["kinds"] = sorted(set(m.get("kinds") or []) | e["kinds"])
        m["stage_a_manifests"] = sorted(set(m.get("stage_a_manifests") or []) | e["manifests"])
        write_manifest(members)
        for c in copies:
            assert G.sha_stream(c) == gs, "a plain copy changed before removal: " + G.rel(c)
            os.remove(c)
            m["removed"] = sorted(set(m["removed"]) | {"%s %s" % (now(), G.rel(c))})
        write_manifest(members)
        act["action"] = "quarantined in %s; %d plain copies removed" % (m["member"], len(copies)) if copies else "already quarantined"
        report["actions"].append(act)
    print(json.dumps(report, indent=1))
    print("C1 QUARANTINE V02 %s" % ("DRY RUN" if a.dry_run else "DONE"))


if __name__ == "__main__":
    main()
