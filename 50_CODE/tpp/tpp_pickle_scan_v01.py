#!/usr/bin/env python3
"""TPP arm (v01, 2 Nov 2026): static scan of a legacy torch checkpoint before it is unpickled.

A torch < 1.6 checkpoint (torch.save with the legacy serializer) is a sequence of pickles: magic number, protocol
version, sys info, the object, the storage keys, then raw storage bytes. This script walks the first five pickles with
pickletools.genops (no object is constructed, nothing is executed) and lists every GLOBAL / STACK_GLOBAL reference, so
that a checkpoint referring to anything outside torch, collections, the Trajectron++ model classes or a short list of
builtins is refused before torch.load runs. It also prints the SHA-256 of the file.
Usage: python -I tpp_pickle_scan_v01.py <checkpoint.pt> [<checkpoint.pt> ...]
"""
import hashlib
import io
import json
import pickletools
import sys

ALLOWED_PREFIXES = ("torch.", "torch._utils", "collections.", "model.", "builtins.set", "builtins.dict", "builtins.list",
                    "builtins.tuple", "builtins.int", "builtins.float", "builtins.bool", "numpy.core.multiarray._reconstruct",
                    "numpy.ndarray", "numpy.dtype")


def scan(path):
    raw = open(path, "rb").read()
    out = {"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(), "zip": raw[:2] == b"PK",
           "globals": [], "pickles_read": 0, "persistent_ids": 0}
    if out["zip"]:
        out["error"] = "zip-format checkpoint: scan data.pkl instead (not expected for torch 1.4)"
        return out
    f = io.BytesIO(raw)
    found = set()
    for _ in range(5):
        start = f.tell()
        if start >= len(raw):
            break
        try:
            strings = []
            for op, arg, pos in pickletools.genops(f):
                if op.name in ("SHORT_BINUNICODE", "BINUNICODE", "UNICODE", "BINUNICODE8"):
                    strings.append(arg)
                if op.name == "GLOBAL":
                    found.add(arg.replace(" ", "."))
                elif op.name == "STACK_GLOBAL":
                    found.add("%s.%s" % (strings[-2], strings[-1]) if len(strings) >= 2 else "?STACK_GLOBAL")
                elif op.name in ("BINPERSID", "PERSID"):
                    out["persistent_ids"] += 1
                if op.name == "STOP":
                    break
            out["pickles_read"] += 1
        except Exception as e:  # raw storage bytes follow the pickles
            out["stopped_at"] = "%s at offset %d" % (type(e).__name__, start)
            break
    out["globals"] = sorted(found)
    out["disallowed"] = [g for g in out["globals"] if not g.startswith(ALLOWED_PREFIXES)]
    return out


def main():
    res = [scan(p) for p in sys.argv[1:]]
    print(json.dumps(res, indent=1))
    bad = [r["path"] for r in res if r.get("disallowed") or r.get("error")]
    print("PICKLE SCAN: " + ("REFUSED " + " ".join(bad) if bad else "all references are torch / collections / model classes"))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
