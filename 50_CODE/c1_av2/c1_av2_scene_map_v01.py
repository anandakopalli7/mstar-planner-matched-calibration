#!/usr/bin/env python3
"""AV2 scene map for C1 (Claude line, c1_av2_scene_map_v01, 5 Nov 2026; D16 v23 Choice 44f m4; R17e m4). A bound builder, run after the
stage-A builds and before the freeze. It writes the scene.json that the freeze binds as data:scene_json and that c1_mstage_v06 and
c1_h8_v06 check (c1_guard_v04.check_scene_json): [{"name": u, "log_token": log}] for every unit u of the given AV2 stage-A manifests,
sorted by name, where log is the manifest's scenes[u]["log"]. On AV2, av2_cache_stageA_v02 records log = the scenario id, so the map is
[{"name": u, "log_token": u}]. Two manifests that give one unit different logs are refused. nuScenes manifests are refused (nuScenes
has its own scene.json). Reads only the manifests' unit and log fields; no ground truth, no outcome. An existing --out is refused.
Usage: <canmot310 python> -B c1_av2_scene_map_v01.py --stageA-manifests <MANIFEST.json ...> --out <dir>/scene.json
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v05 as G  # noqa: E402


def scene_map(manifests):
    logs = {}
    for p in manifests:
        m = json.load(open(p))
        assert G.manifest_dataset(m) == "av2", "not an AV2 manifest (nuScenes has its own scene.json): %s" % G.rel(p)
        assert m.get("stage", "A") == "A", "not a stage-A manifest: %s" % G.rel(p)
        for u, info in (m.get("scenes") or {}).items():
            log = str(info["log"]) if isinstance(info, dict) and info.get("log") is not None else str(u)
            assert logs.get(str(u), log) == log, "unit %s has two logs in the stage-A manifests (%s, %s)" % (u, logs[str(u)], log)
            logs[str(u)] = log
    assert logs, "the stage-A manifests hold no unit"
    return [{"name": u, "log_token": logs[u]} for u in sorted(logs)]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    assert os.path.basename(a.out) == "scene.json", "--out must be <dir>/scene.json (check_scene_json reads <meta>/scene.json)"
    assert not os.path.exists(a.out), "%s exists: never overwritten" % a.out
    sm = scene_map(a.stageA_manifests)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    txt = json.dumps(sm, indent=1, sort_keys=True) + "\n"
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(txt)
    same = sum(1 for e in sm if e["name"] == e["log_token"])
    print(json.dumps({"out": G.rel(a.out), "sha256": hashlib.sha256(txt.encode("utf-8")).hexdigest(), "units": len(sm),
                      "log_equals_name": same, "manifests": [G.rel(p) for p in a.stageA_manifests]}))
    print("C1 AV2 SCENE MAP V01 DONE")


if __name__ == "__main__":
    main()
