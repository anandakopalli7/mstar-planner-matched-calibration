#!/usr/bin/env python3
"""X3 reference / Q-refit agent ("x3-ref"), common helpers (7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of
record; not part of the registered test). Plan: 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md (sha256 38e2526d...), analyses (d), (e2).

Paths, the stamp, hashing, atomic writes, the live progress line and the integrity check of 40_PROTOCOL/C1_RUN_LOG.txt.
Nothing here imports a guard or writes outside 60_RESULTS/x3_explore_v01/{d_ref,e2_qrefit}/ and 00_PROGRESS/live/x3_ref.txt.
"""
import hashlib
import json
import os
import sys
import time

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
X3 = os.path.join(W, "60_RESULTS", "x3_explore_v01")
D_REF = os.path.join(X3, "d_ref")
E2 = os.path.join(X3, "e2_qrefit")
LIVE = os.path.join(W, "00_PROGRESS", "live", "x3_ref.txt")
RUN_LOG = os.path.join(W, "40_PROTOCOL", "C1_RUN_LOG.txt")
RUN_LOG_SHA = "8bc6235d0c582f0b52952dcb86717a6ab42236a1e472582ebf8f4a10f95e2090"
STAMP = "X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test)"
TRK = {"t1": {"experiment": "paper/local/canmot/sc", "export": "t1_owncp"},
       "t3": {"experiment": "paper/baseline/poly_mot", "export": "t3_owncp"}}
ITEMS_REC = {t: os.path.join(W, "60_RESULTS", "c1_av2_v01", "items", "items_c1b_%s_own375.npz" % t) for t in TRK}
FITS_REC = {t: os.path.join(W, "60_RESULTS", "c1_av2_v01", "fits", "fits_within_%s.json" % t) for t in TRK}
CACHE = {t: os.path.join(W, "30_DATA", "av2_cache_stageB_c1b_%s_own375" % t) for t in TRK}
FOLDS = os.path.join(W, "60_RESULTS", "c1_folds_v01", "C1_FOLDS_375_v01.json")
EXPORT = {t: [os.path.join(W, "30_DATA", "av2_trk_v02", "export", TRK[t]["export"], "worker%d" % i) for i in range(8)] for t in TRK}
HORIZON = {t: os.path.join(W, "30_DATA", "av2_trk_v02", "horizon", "horizon8_%s_owncp.jsonl.gz" % t) for t in TRK}
FORBIDDEN_WORDS = ("restricted", "sealed", "do_not_open", "participant", "codex")
WRITE_ROOTS = (D_REF, E2)

for p in (os.path.join(W, "50_CODE", "x3"),):
    if p not in sys.path:
        sys.path.insert(0, p)


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def check_out(p):
    """Every X3-ref output path must lie under d_ref/ or e2_qrefit/, and must not exist yet (new files only)."""
    ap = os.path.abspath(p)
    assert any(ap.startswith(os.path.abspath(r) + os.sep) for r in WRITE_ROOTS), "x3-ref writes only under d_ref/ or e2_qrefit/: " + ap
    assert not any(w in ap.lower() for w in FORBIDDEN_WORDS), "forbidden word in an output path: " + ap
    return ap


def save_json(p, obj, overwrite_ok=False):
    ap = check_out(p) if not overwrite_ok else os.path.abspath(p)
    if not overwrite_ok:
        assert not os.path.exists(ap), "refused: exists (new files only): " + ap
    tmp = ap + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=1)
    os.replace(tmp, ap)
    return ap


def save_npz(p, **arrs):
    import numpy as np
    ap = check_out(p)
    assert not os.path.exists(ap), "refused: exists (new files only): " + ap
    tmp = ap[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, **arrs)
    os.replace(tmp, ap)
    return ap


def live(step, done, total, note=""):
    """One line, rewritten at each milestone: local time, step, done/total."""
    line = "%s  x3-ref  %s  %s/%s%s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), step, done, total, ("  " + note) if note else "")
    tmp = LIVE + ".%d.tmp" % os.getpid()
    try:                                  # progress must never stop a job (two processes may write it)
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(line)
        os.replace(tmp, LIVE)
    except OSError:
        try:
            os.remove(tmp)
        except OSError:
            pass


def run_log_ok():
    s = sha256_path(RUN_LOG)
    assert s == RUN_LOG_SHA, "40_PROTOCOL/C1_RUN_LOG.txt changed: %s" % s
    return s


def no_guard_ran():
    """True if no c1_guard module loaded in this process has recorded a guard call (LAST_GUARD empty)."""
    for name, mod in list(sys.modules.items()):
        if name.startswith("c1_guard") and getattr(mod, "LAST_GUARD", None):
            return False
    return True


def code_record(files):
    return {os.path.relpath(f, W).replace("\\", "/"): sha256_path(f) for f in files}
