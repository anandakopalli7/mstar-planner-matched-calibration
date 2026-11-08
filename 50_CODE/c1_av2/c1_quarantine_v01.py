#!/usr/bin/env python3
"""C1 ground-truth quarantine (Claude line, c1_quarantine_v01, 4 Nov 2026; D16 v21 Choice 42b, R17d B2). A lead tool, run once after
every stage-A build for the 375 logs is complete and before the freeze. For each AV2 stage-A manifest given:
  1. the plain prepared ground-truth file it names (inputs.gt) must have exactly the recorded SHA-256 (inputs.gt_sha256);
  2. it is gzip-compressed (mtime 0) into the fixed folder 30_DATA/av2_gt_quarantine_v01/ as <name>.gz, written to a temporary name,
     flushed and renamed;
  3. the member is re-read and decompressed, and its bytes must equal the plain file's bytes and the recorded hash;
  4. only then is the plain file removed, and QUARANTINE_MANIFEST.json (member, source path, decompressed and gzip SHA-256, UTC) is
     rewritten atomically.
Idempotent and resumable: a member already present and verified is kept; if its plain file is gone it is reported "already quarantined".
The plain file is looked for where c1_freeze_v05 looks (c1_guard_v04.plain_gt_files): at the recorded path and, if that path contains
/30_DATA/, at the same path under this workspace's 30_DATA (a stage A built on a pod records the pod's path); every copy found must have
the recorded hash, and every copy is removed after the member is verified.
Nothing is read from the ground truth beyond its bytes for hashing; no record is parsed. nuScenes manifests are skipped.
After this, c1_freeze_v05 no longer finds plain prepared ground truth, and stage B v05 reads only these members (after the deposit check).
Usage: <python> -B c1_quarantine_v01.py --stageA-manifests <MANIFEST.json ...> [--dry-run]
"""
import argparse
import datetime
import gzip
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v04 as G  # noqa: E402


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def plain_copies(gp):
    """The existing plain copies of a recorded ground-truth path, as c1_guard_v04.plain_gt_files finds them."""
    cands = [gp]
    norm = gp.replace("\\", "/")
    if "/30_DATA/" in norm:
        cands.append(os.path.join(G.W, "30_DATA", *norm.split("/30_DATA/", 1)[1].split("/")))
    out = []
    for c in cands:
        if os.path.exists(c) and os.path.abspath(c) not in [os.path.abspath(x) for x in out]:
            out.append(c)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    members = {m["member"]: m for m in G.quarantine_members()}
    report = []
    for mp, gp, gs in G.stage_a_gt(a.stageA_manifests):
        name = os.path.basename(gp) + ".gz"
        dst = os.path.join(G.QUARANTINE, name)
        copies = plain_copies(gp)
        for c in copies:
            assert sha_bytes(open(c, "rb").read()) == gs, "the plain ground truth differs from the hash its stage-A manifest recorded: " + c
        if os.path.exists(dst):
            b = gzip.open(dst, "rb").read()
            assert sha_bytes(b) == gs, "an existing quarantine member differs from the stage-A hash: " + name
            if copies:
                if not a.dry_run:
                    for c in copies:
                        os.remove(c)
                report.append({"member": name, "action": "verified member; plain file removed" if not a.dry_run else "would remove the plain file"})
            else:
                report.append({"member": name, "action": "already quarantined"})
            members.setdefault(name, {"member": name, "source": gp, "sha256_decompressed": gs, "sha256_gz": G.sha(dst),
                                      "utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "stage_a_manifest": G.rel(mp)})
            continue
        assert copies, "neither the plain ground truth nor its quarantine member exists: " + gp
        raw = open(copies[0], "rb").read()
        if a.dry_run:
            report.append({"member": name, "action": "would quarantine", "bytes": len(raw)})
            continue
        os.makedirs(G.QUARANTINE, exist_ok=True)
        tmp = dst + ".tmp"
        with open(tmp, "wb") as f:
            with gzip.GzipFile(filename=os.path.basename(gp), mode="wb", fileobj=f, mtime=0) as g:
                g.write(raw)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, dst)
        back = gzip.open(dst, "rb").read()
        assert back == raw and sha_bytes(back) == gs, "the quarantine member does not decompress to the plain bytes: " + name
        members[name] = {"member": name, "source": gp, "sha256_decompressed": gs, "sha256_gz": G.sha(dst),
                         "utc": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"), "stage_a_manifest": G.rel(mp)}
        man = {"rule": "D16 v21 Choice 42b: gzip members of the prepared AV2 ground truth; decompressed SHA-256 = the stage-A manifests' gt_sha256",
               "members": sorted(members.values(), key=lambda m: m["member"])}
        with open(G.QUARANTINE_MANIFEST + ".tmp", "w") as f:
            json.dump(man, f, indent=1)
            f.flush()
            os.fsync(f.fileno())
        os.replace(G.QUARANTINE_MANIFEST + ".tmp", G.QUARANTINE_MANIFEST)
        for c in copies:
            os.remove(c)
        report.append({"member": name, "action": "quarantined; plain file removed", "bytes": len(raw), "removed": [G.rel(c) for c in copies]})
    if not a.dry_run and members:
        man = {"rule": "D16 v21 Choice 42b: gzip members of the prepared AV2 ground truth; decompressed SHA-256 = the stage-A manifests' gt_sha256",
               "members": sorted(members.values(), key=lambda m: m["member"])}
        with open(G.QUARANTINE_MANIFEST + ".tmp", "w") as f:
            json.dump(man, f, indent=1)
        os.replace(G.QUARANTINE_MANIFEST + ".tmp", G.QUARANTINE_MANIFEST)
    print(json.dumps(report, indent=1))
    print("C1 QUARANTINE %s" % ("DRY RUN" if a.dry_run else "DONE"))


if __name__ == "__main__":
    main()
