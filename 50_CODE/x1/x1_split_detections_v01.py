#!/usr/bin/env python3
"""Split the approved CenterPoint val detection file into per-worker subsets by scene (Claude line, v01, 30 Oct 2026).
Every subset keeps the approved file's token order and copies each token's detection list unchanged. Scenes are dealt to
workers round-robin in file order. A receipt records the source hash, each subset's hash, scenes and token counts, and
checks that the subsets partition the source tokens exactly.
Usage: python x1_split_detections_v01.py --det <approved json> --meta <v1.0-trainval> --n-workers 3 --out <dir>
       [--scenes s1 s2 ...]   (restrict to these scenes, for the equivalence test)
"""
import argparse
import hashlib
import json
import os
import sys

APPROVED = "4186f748f91e071c1276287244e23a01da5908a373af85ee2dfb08ea935b903e"


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
    ap.add_argument("--n-workers", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--scenes", nargs="*", default=None)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    src_sha = sha(a.det)
    assert src_sha == APPROVED, "source detection file is not the approved one"
    from nuscenes.utils.splits import val as VAL
    names = list(a.scenes) if a.scenes else list(VAL)
    scenes = {s["name"]: s for s in json.load(open(os.path.join(a.meta, "scene.json")))}
    samples = {s["token"]: s for s in json.load(open(os.path.join(a.meta, "sample.json")))}
    tok2scene = {}
    for n in names:
        t = scenes[n]["first_sample_token"]
        while t:
            tok2scene[t] = n
            t = samples[t]["next"]
    src = json.load(open(a.det))
    order = [t for t in src["results"] if t in tok2scene]
    scene_order = []
    for t in order:
        if not scene_order or scene_order[-1] != tok2scene[t]:
            scene_order.append(tok2scene[t])
    assert len(scene_order) == len(set(scene_order)) == len(names), "scenes not contiguous or missing"
    assign = {s: i % a.n_workers for i, s in enumerate(scene_order)}
    rec = {"source": os.path.abspath(a.det), "source_sha256": src_sha, "n_workers": a.n_workers, "subsets": []}
    covered = 0
    for w in range(a.n_workers):
        res = {t: src["results"][t] for t in order if assign[tok2scene[t]] == w}
        p = os.path.join(a.out, "dets_worker%d.json" % w)
        with open(p, "w") as f:
            json.dump({"meta": src.get("meta", {}), "results": res}, f)
        covered += len(res)
        rec["subsets"].append({"worker": w, "path": p, "sha256": sha(p), "tokens": len(res),
                               "scenes": [s for s in scene_order if assign[s] == w]})
    rec["tokens_total"], rec["partition_exact"] = covered, covered == len(order) == len(tok2scene)
    with open(os.path.join(a.out, "split_receipt.json"), "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k != "subsets"}), [(s["worker"], s["tokens"], len(s["scenes"])) for s in rec["subsets"]])


if __name__ == "__main__":
    sys.exit(main())
