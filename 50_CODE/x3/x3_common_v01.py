#!/usr/bin/env python3
"""X3 common helpers (x3-core agent, x3_common_v01, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record;
not part of the registered test). Plan: 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md (sha256 38e2526d...).

Paths, the stamp, seeds (plan section 0), integrity checks (the run log of record and the hash manifest of 60_RESULTS/c1_av2_v01),
atomic writes, the live progress line, and the city of every AV2 log (read-only, from the local AV2 map manifests).
Imports nothing from the frozen code; writes only under 60_RESULTS/x3_explore_v01, 70_TESTS/X3_INTEGRITY_v01 and 00_PROGRESS/live.
"""
import glob
import hashlib
import json
import os
import re
import time

import numpy as np

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
STAMP = "X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)"
PLAN = os.path.join(W, "20_DESIGN", "X3_POSTREG_EXPLORATORY_PLAN_v01.md")
PLAN_SHA = "38e2526d9f43f202fe4c8fe345be03d21421d6c7ada585022abf34a649362dc6"
RUN_LOG = os.path.join(W, "40_PROTOCOL", "C1_RUN_LOG.txt")
RUN_LOG_SHA = "8bc6235d0c582f0b52952dcb86717a6ab42236a1e472582ebf8f4a10f95e2090"
REC = os.path.join(W, "60_RESULTS", "c1_av2_v01")
REC_RUNS = os.path.join(REC, "runs")
BASELINE = os.path.join(W, "70_TESTS", "X3_INTEGRITY_v01", "BASELINE_MANIFEST_v01.txt")
OUT = os.path.join(W, "60_RESULTS", "x3_explore_v01")
INTEG = os.path.join(W, "70_TESTS", "X3_INTEGRITY_v01")
LIVE = os.path.join(W, "00_PROGRESS", "live", "x3_core.txt")
FOLDS = os.path.join(W, "60_RESULTS", "c1_folds_v01", "C1_FOLDS_375_v01.json")
CACHES = {t: os.path.join(W, "30_DATA", "av2_cache_stageB_c1b_%s_own375" % t) for t in ("t1", "t3", "tab")}
FITS_REC = {t: os.path.join(REC, "fits", "fits_within_%s.json" % t) for t in ("t1", "t3", "tab")}
ITEMS_REC = {t: os.path.join(REC, "items", "items_c1b_%s_own375.npz" % t) for t in ("t1", "t3", "tab")}
TAG_REC = {t: "%s_within_lt3d" % t for t in ("t1", "t3", "tab")}
TRACKER_I = {"t1": 0, "t3": 1, "tab": 2}
ANALYSIS_J = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5, "g": 7}
SEED_BOOT_X3, SEED_POWER_X3 = 20261201, 20261202
B_X3 = 4000
DELTA = 0.05
CITY_SOURCES = [os.path.join(W, "30_DATA", "av2_det_owncp_v01", "env", "MANIFEST_val_confirm_v06_maps.csv"),
                os.path.join(W, "30_DATA", "av2_det_owncp_v01", "env", "MANIFEST_train_confirm_v06_maps.csv"),
                os.path.join(W, "30_DATA", "av2_det_owncp_v01", "env", "MANIFEST_train475_v06_maps.csv"),
                os.path.join(W, "30_DATA", "av2_det_owncp_v01", "pilot", "env", "MANIFEST_av2_train_lidar_v06_maps.csv"),
                os.path.join(W, "30_DATA", "av2_det_owncp_v01", "pilot", "env", "MANIFEST_av2_val_lidar_v06_maps.csv"),
                os.path.join(W, "30_DATA", "av2_det_v01", "voxelnext", "MANIFEST_av2_val_lidar_v04_maps.csv")]


def x3_seeds(tracker, analysis):
    """Plan section 0: bootstrap [20261201, i, j], power [20261202, i, j]."""
    i, j = TRACKER_I[tracker], ANALYSIS_J[analysis]
    return [SEED_BOOT_X3, i, j], [SEED_POWER_X3, i, j]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def run_log_ok():
    return sha256(RUN_LOG) == RUN_LOG_SHA


def assert_run_log(where):
    h = sha256(RUN_LOG)
    if h != RUN_LOG_SHA:
        raise SystemExit("X3 STOP: 40_PROTOCOL/C1_RUN_LOG.txt changed (%s): %s" % (where, h))
    return h


def manifest_check():
    """Re-hash 60_RESULTS/c1_av2_v01 and the run log; compare with BASELINE_MANIFEST_v01.txt. Returns (ok, details)."""
    base = {}
    for ln in open(BASELINE, encoding="utf-8"):
        ln = ln.rstrip("\n")
        if not ln.strip():
            continue
        h, p = ln.split("  ", 1)
        base[p.strip()] = h
    now = {}
    for p in glob.glob(os.path.join(REC, "**", "*"), recursive=True):
        if os.path.isfile(p):
            now[os.path.relpath(p, W).replace("\\", "/")] = sha256(p)
    now["40_PROTOCOL/C1_RUN_LOG.txt"] = sha256(RUN_LOG)
    missing = sorted(set(base) - set(now))
    extra = sorted(set(now) - set(base))
    changed = sorted(p for p in set(base) & set(now) if base[p] != now[p])
    ok = not (missing or extra or changed)
    return ok, {"files_baseline": len(base), "files_now": len(now), "missing": missing, "extra": extra, "changed": changed}


def jdefault(o):
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o) if np.isfinite(o) else None
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    if isinstance(o, set):
        return sorted(o)
    raise TypeError(type(o))


def jdump(path, obj, refuse_existing=False):
    if refuse_existing and os.path.exists(path):
        raise SystemExit("refusing to overwrite " + path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1, default=jdefault)
    os.replace(tmp, path)


def wtext(path, text, refuse_existing=False):
    if refuse_existing and os.path.exists(path):
        raise SystemExit("refusing to overwrite " + path)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write(text)
    os.replace(tmp, path)


def live(step, done, total, note=""):
    line = "%s | x3-core | %s | %s/%s%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), step, done, total, (" | " + note) if note else "")
    try:
        wtext(LIVE, line)
    except Exception:
        pass


def log_of_scene_identity(scenes):
    return {s: s for s in scenes}


_CITY_RE = re.compile(r"/([0-9a-f-]{36})/map/log_map_archive_[0-9a-f-]+____([A-Z]+)_city_")


def city_of_log():
    """{log: city} from the AV2 map file names (log_map_archive_<log>____<CITY>_city_<id>.json) listed in the local manifests."""
    out, src = {}, {}
    for p in CITY_SOURCES:
        if not os.path.exists(p):
            continue
        src[os.path.relpath(p, W).replace("\\", "/")] = sha256(p)
        for ln in open(p, encoding="utf-8"):
            m = _CITY_RE.search(ln)
            if m:
                lg, c = m.group(1), m.group(2)
                assert out.get(lg, c) == c, "two cities for log " + lg
                out[lg] = c
    return out, src


def code_hashes(paths):
    return {os.path.basename(p): sha256(p) for p in paths}
