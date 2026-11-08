#!/usr/bin/env python3
"""Streaming split of an approved CenterPoint detection file into per-worker scene subsets (Claude line, v03, 30 Oct 2026).
For files too large to load whole (train: 1.48 GB). Reads tokens in file order with ijson (floats parsed as Python floats,
identical to json.load), deals scenes to subsets round-robin in order of first appearance, writes each token's detection
list unchanged, checks scene contiguity and that the subsets partition the split's tokens exactly.
Usage: python x1_split_detections_stream_v03.py --det <json> --meta <v1.0-trainval> --split train --n-subsets 12 --out <dir>
"""
import argparse
import hashlib
import json
import os
import sys

import ijson

APPROVED = {"val": "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e",
            "train": "547fdb7dd6c401749f619a504fa37ee70dbad676d3f400b28c5176bff3327145"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--det", required=True)
    ap.add_argument("--meta", required=True)
    ap.add_argument("--split", required=True, choices=["val", "train"])
    ap.add_argument("--n-subsets", type=int, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    src_sha = sha(a.det)
    assert src_sha == APPROVED[a.split], "source detection file is not the approved one"
    from nuscenes.utils import splits as SPLITS
    names = set(getattr(SPLITS, a.split))
    scenes = {s["name"]: s for s in json.load(open(os.path.join(a.meta, "scene.json")))}
    samples = {s["token"]: s for s in json.load(open(os.path.join(a.meta, "sample.json")))}
    tok2scene = {}
    for n in names:
        t = scenes[n]["first_sample_token"]
        while t:
            tok2scene[t] = n
            t = samples[t]["next"]
    del samples
    outs = [open(os.path.join(a.out, "dets_subset%02d.json" % i), "w") for i in range(a.n_subsets)]
    first = [True] * a.n_subsets
    for f in outs:
        f.write('{"results": {')
    assign, order, last, counts, seen = {}, [], None, [0] * a.n_subsets, 0
    with open(a.det, "rb") as f:
        for tok, dets in ijson.kvitems(f, "results", use_float=True):
            sc = tok2scene.get(tok)
            if sc is None:
                continue
            if sc != last:
                assert sc not in assign, "scene %s not contiguous in the file" % sc
                assign[sc] = len(order) % a.n_subsets
                order.append(sc)
                last = sc
            i = assign[sc]
            outs[i].write(("" if first[i] else ", ") + json.dumps(tok) + ": " + json.dumps(dets))
            first[i] = False
            counts[i] += 1
            seen += 1
    for f in outs:
        f.write('}, "meta": {"use_camera": false, "use_lidar": true, "use_radar": false, "use_map": false, "use_external": false}}')
        f.close()
    assert len(order) == len(names), "missing scenes: %d of %d" % (len(order), len(names))
    rec = {"source": os.path.abspath(a.det), "source_sha256": src_sha, "split": a.split, "n_workers": a.n_subsets,
           "tokens_total": seen, "partition_exact": seen == len(tok2scene), "subsets": []}
    for i in range(a.n_subsets):
        p = os.path.join(a.out, "dets_subset%02d.json" % i)
        rec["subsets"].append({"worker": i, "path": p, "sha256": sha(p), "tokens": counts[i], "scenes": [s for s in order if assign[s] == i]})
    with open(os.path.join(a.out, "split_receipt.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k != "subsets"}), counts)


if __name__ == "__main__":
    sys.exit(main())
