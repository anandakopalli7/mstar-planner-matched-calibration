#!/usr/bin/env python3
"""Refusal helper for the superseded C1 entry points (Claude line, c1_legacy_refuse_v01, 4 Nov 2026; D16 Choice 36 rule 3 and
Choice 39a; R17c B1). The main() of every superseded entry-capable file (c1_analyse_v01-v03, c1_fit_v02, c1_run_v01/v02,
c1_mstage_v01/v02, c1_h8_v01/v02, c1_e0_v01, c1_predarm_v01/v02, c1_freeze_v01/v02, av2_cache_stageB_v01/v02) calls check() before it
reads any data: every input whose dataset - read from outcome-free tags and names only (manifests, folds, export track names, key
names, item names, run records' cache manifests, tables' provenance) - is not nuScenes or synthetic is refused, naming the replacement.
The originals are archived byte-exact in 50_CODE/c1_av2/superseded_originals/ and 50_CODE/av2/superseded_originals/.
Delegation: c1_fit_v02 and c1_run_v02 are still the bodies of the guarded c1_fit_v04 and c1_run_v04. Their main() accepts AV2 data
only when c1_guard_v03.guard() has passed IN THIS PROCESS for the same plan file, the same dataset and the role entry:c1_fit /
entry:c1_run (c1_guard_v03.LAST_GUARD), i.e. only when called by the plan's named entry point after its full guard.
"""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_guard_v03 as G3  # noqa: E402

OK = ("nuscenes", "synthetic")
SYN_STAMP = "SYNTHETIC: generated test data, not nuScenes"


def delegated(role, plan, ds):
    lg = G3.LAST_GUARD
    return bool(role and plan and lg.get("role") == role and lg.get("plan") == os.path.abspath(plan) and lg.get("dataset") == ds)


def check(entry, replacement, datasets, delegate_role=None, plan=None):
    for what, ds in datasets.items():
        if ds in OK or delegated(delegate_role, plan, ds):
            continue
        raise AssertionError("refused: %s is superseded (D16 Choice 36 rule 3, Choice 39a): its main() runs on nuScenes or synthetic "
                             "inputs only, and the %s are %s. Use %s." % (entry, what, ds, replacement))
    return True


def ds_manifest_obj(m):
    return G3.manifest_dataset(m)


def ds_manifests(dirs):
    ds = {G3.manifest_dataset(json.load(open(os.path.join(d, "MANIFEST.json")))) for d in dirs}
    return ds.pop() if len(ds) == 1 else ("unknown" if not ds else "mixed")


def ds_folds_obj(fj):
    return G3.folds_dataset(fj)


def ds_folds(path):
    return G3.folds_dataset(json.load(open(path)))


def ds_exports(workers):
    return G3.export_dataset(workers)


def ds_keys(path):
    z = np.load(path, allow_pickle=False)
    if "stamp" in z.files and str(z["stamp"]) == SYN_STAMP:
        return "synthetic"
    return G3.dataset_checked(None, [str(x) for x in z["scene_names"]])


def ds_items(paths):
    names = []
    for p in paths:
        z = np.load(p, allow_pickle=False)
        if "stamp" in z.files and str(z["stamp"]) == SYN_STAMP:
            return "synthetic"
        names += [str(x) for x in z["scene_names"]]
    return G3.units_dataset(names)


def ds_bind_files(paths):
    out = {}
    for p in paths or []:
        try:
            d = json.load(open(p))
        except (ValueError, UnicodeDecodeError, OSError):
            continue
        if isinstance(d, dict) and "fold_of_log" in d:
            out["folds %s" % os.path.basename(p)] = G3.folds_dataset(d)
    return out


def ds_config(cfg):
    out = {}
    if cfg.get("folds"):
        out["folds"] = ds_folds(cfg["folds"])
    for p in cfg.get("manifests", []) or []:
        out["manifest %s" % p] = G3.manifest_dataset(json.load(open(p)))
    for r in cfg.get("routes", []) or []:
        for t, tag in (r.get("tags") or {}).items():
            rp = os.path.join(r["runs"], "run_record_%s_decide.json" % tag)
            if os.path.exists(rp):
                caches = json.load(open(rp)).get("caches") or []
                out["run caches %s %s" % (r.get("name"), t)] = ds_manifests(caches) if caches else "unknown (no caches)"
    for key in ("method_stage", "h8", "h9"):
        ent = cfg.get(key)
        if not ent:
            continue
        ents = {"_": ent} if (isinstance(ent, str) or "path" in ent) else ent
        for t, e in ents.items():
            p = e if isinstance(e, str) else e["path"]
            ds = "unknown (missing)"
            if os.path.exists(p):
                ds = (json.load(open(p)).get("provenance") or {}).get("dataset") or "unknown (no provenance)"
            out["%s table %s" % (key, t)] = ds
    return out
