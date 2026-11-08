#!/usr/bin/env python3
"""Trajectron++ keys v02 (Claude line, tpp_keys_v02, 4 Nov 2026) = tpp_keys_v01 (kept, imported and run unchanged; D17 v04 binds it)
with R17c M4 / D16 v18 Choice 39d for C1: under C1 (a cache that is not nuScenes, read from its MANIFEST's tag and scene names) the
`--scenes` subset is REFUSED, so the keys always cover the whole cache. After tpp_keys_v01 has written the keys, this writes
<out>.wrapper.json: this file's hash (entry point), the keys' hash, the cache manifest's hash, the dataset and scenes = null.
c1_predarm_v04 requires that record for AV2 keys. Self-contained (Python 3.8; no C1 import).
Usage: as tpp_keys_v01.
"""
import hashlib
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
NUSC = re.compile(r"^scene-\d{4}$")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rel(p):
    return os.path.relpath(os.path.abspath(p), W).replace("\\", "/")


def cache_dataset(cache):
    m = json.load(open(os.path.join(cache, "MANIFEST.json")))
    names = [str(n) for n in (m.get("scenes") or {})]
    tag = str(m.get("dataset") or "").lower()
    if names and all(NUSC.match(n) for n in names) and tag in ("", "nuscenes"):
        return "nuscenes"
    return "av2" if tag.startswith("av2") or (names and not any(NUSC.match(n) for n in names)) else "unknown"


def arg(argv, name):
    return argv[argv.index(name) + 1] if name in argv else None


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    cache, out = arg(argv, "--cache"), arg(argv, "--out")
    ds = cache_dataset(cache)
    if ds != "nuscenes":
        assert "--scenes" not in argv, "refused: --scenes is refused under C1 (the keys must cover the whole cache; R17c M4)"
    import tpp_keys_v01 as K1
    sys.argv = [K1.__file__] + argv
    K1.main()
    rec = {"entry_point": {rel(__file__): sha(os.path.abspath(__file__))}, "module": {rel(K1.__file__): sha(K1.__file__)},
           "out_sha256": sha(out), "cache_manifest_sha256": sha(os.path.join(cache, "MANIFEST.json")), "dataset": ds,
           "scenes": None if "--scenes" not in argv else "subset (nuScenes only)"}
    json.dump(rec, open(out + ".wrapper.json", "w"), indent=1)
    print("TPP KEYS V02 DONE")


if __name__ == "__main__":
    main()
