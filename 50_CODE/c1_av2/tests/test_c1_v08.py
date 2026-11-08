#!/usr/bin/env python3
"""Tests of the Choice 36 rule 3 / 39a edits (Claude line, test_c1_v08, 4 Nov 2026; R17c B1). nuScenes, synthetic and dummy AV2-TAGGED
fixtures only (R17c's p1/p2 folders, read only); outputs under 70_TESTS/c1_v01/tests_v08/. One process plus subprocesses run in turn.
  ARCH     the archives hold the byte-exact originals: decompressed SHA-256 = SHA256SUMS = README v05's hashes of those 17 files.
  MAINONLY every edited file equals its archived original plus the recorded main()-only insertion (apply_choice36_main_edits_v01 logic),
           and everything before "def main" and from 'if __name__' is byte-identical; so every imported function is unchanged.
  GENORIG  the 11 generator checks of c1_freeze_v04, on the archived originals where a file was edited, all reproduce.
  REFUSE   every edited superseded main() refuses R17c's P1/P2 fixtures (AV2-tagged stage-A cache, exports, keys, folds, caches) and
           names its replacement; nothing is written; c1_fit_v02 and c1_run_v02 refuse AV2 inputs unless the guard v03 delegation
           (same process, same plan) is present, and accept it when it is.
  LEGACY   nuScenes / synthetic behaviour unchanged where the old files are imported as modules: every group of the earlier suites
           test_c1_v01-v06 is re-run in this process on the live files, except GEN, GEN2, GEN3, v02's FRZ (c1_freeze_v01's own generator
           check) and v06's FRZ3, which compare generators with the live (edited) files and are replaced by GENORIG (and by v09 FRZ4 for
           the freeze); each must pass as before.
Every run records the SHA-256 of every tested file.
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v08.py [<out.json>]
"""
import gzip
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import traceback

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(C1, "tests"))
sys.path.insert(0, os.path.join(W, "50_CODE", "tpp", "tests"))
import c1_guard_v03 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v08")
R17C = os.path.join(W, "70_TESTS", "c1_v01", "r17c_probes")
PY = sys.executable
UUID = "00000000-0000-4000-8000-000000000000"
EDITED = {"c1_av2": ["c1_analyse_v01.py", "c1_analyse_v02.py", "c1_analyse_v03.py", "c1_fit_v02.py", "c1_run_v01.py", "c1_run_v02.py",
                     "c1_mstage_v01.py", "c1_mstage_v02.py", "c1_h8_v01.py", "c1_h8_v02.py", "c1_e0_v01.py", "c1_predarm_v01.py",
                     "c1_predarm_v02.py", "c1_freeze_v01.py", "c1_freeze_v02.py"], "av2": ["av2_cache_stageB_v01.py", "av2_cache_stageB_v02.py"]}
TESTED = ["c1_legacy_refuse_v01.py", "superseded_originals/apply_choice36_main_edits_v01.py", "tests/test_c1_v08.py", "c1_freeze_v04.py"] + \
         EDITED["c1_av2"] + ["../av2/" + f for f in EDITED["av2"]]
SKIP_LEGACY = {"test_c1_v01": ("GEN",), "test_c1_v02": ("GEN2", "FRZ"), "test_c1_v03": ("GEN3",), "test_c1_v06": ("FRZ3",)}


def sub(cmd, cwd=C1):
    r = subprocess.run([PY, "-B"] + cmd, capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr


def t_arch():
    rd = open(os.path.join(C1, "README_C1_CODE_v05.md"), encoding="utf-8").read()
    v05 = {m.group(2): m.group(1) for m in re.finditer(r"^([0-9a-f]{64})  (50_CODE/\S+)  \S+$", rd, re.M)}
    r4 = open(os.path.join(C1, "README_C1_CODE_v04.md"), encoding="utf-8").read()       # c1_freeze_v01/v02 were last bound in README v04
    for m in re.finditer(r"^([0-9a-f]{64})  (50_CODE/\S+)$", r4, re.M):
        v05.setdefault(m.group(2), m.group(1))
    out = {}
    for area, files in EDITED.items():
        arch = os.path.join(W, "50_CODE", area, "superseded_originals")
        sums = dict(l.split(" *")[::-1] for l in open(os.path.join(arch, "SHA256SUMS_superseded_originals_v01.txt")).read().splitlines() if l.strip())
        for f in files:
            h = hashlib.sha256(gzip.open(os.path.join(arch, f + ".gz"), "rb").read()).hexdigest()
            assert h == sums[f] == v05["50_CODE/%s/%s" % (area, f)], "archive of %s is not the README v05 original" % f
            out[f] = h[:12]
    return out


def t_mainonly():
    import importlib.util
    spec = importlib.util.spec_from_file_location("apply36", os.path.join(C1, "superseded_originals", "apply_choice36_main_edits_v01.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    out = {}
    for f, (d, anchor, where, ins) in mod.EDITS.items():
        orig = mod.original(d, f)
        live = open(os.path.join(d, f), encoding="utf-8", newline="").read()
        assert live == mod.edited(orig, anchor, where, ins), f
        a0, m0, c0 = mod.split3(orig.replace("\r\n", "\n"))
        a1, m1, c1 = mod.split3(live.replace("\r\n", "\n"))
        assert a0 == a1 and c0 == c1 and len(m1) > len(m0), f
        out[f] = "main() only (+%d lines)" % (m1.count("\n") - m0.count("\n"))
    return out


def t_genorig():
    import c1_freeze_v04 as F4
    return F4.check_generators([])


def t_refuse():
    p1, p2 = os.path.join(R17C, "p1"), os.path.join(R17C, "p2")
    o = os.path.join(OUT, "refuse")
    shutil.rmtree(o, ignore_errors=True)
    os.makedirs(o)
    av2 = os.path.join(W, "50_CODE", "av2")
    w, gt, meta, hz, e0 = (os.path.join(p2, x) for x in ("worker_av2", "gt.json", "meta", "horizon.jsonl.gz", "e0.json"))
    folds = os.path.join(p2, "folds.json")
    items = os.path.join(o, "items_av2.npz")
    np.savez(items, scene_names=np.array([UUID]))
    cfg = os.path.join(o, "cfg.json")
    json.dump({"routes": [], "folds": folds}, open(cfg, "w"))
    ff = os.path.join(o, "fits.json")
    json.dump({"folds_sha256": G.sha(folds)}, open(ff, "w"))
    ms = ["--tracker", "T1", "--experiment", "x", "--av2-workers", w, "--av2-gt", gt, "--av2-meta", meta, "--av2-horizon", hz, "--train-workers", w,
          "--train-gt", gt, "--train-meta", meta, "--train-horizon", hz, "--test", "--out", os.path.join(o, "ms.json")]
    plan, log = os.path.join(p1, "PRIVATE_PLAN.md"), os.path.join(p1, "private_log.txt")
    cmds = {
        "av2_cache_stageB_v01": (["av2_cache_stageB_v01.py", "--stage-a", os.path.join(p1, "fake_stageA"), "--gt", os.path.join(p1, "fake_gt.json"), "--out",
                                  os.path.join(o, "B1"), "--frozen-plan", os.path.join(p1, "any_file.txt"), "--frozen-plan-sha256",
                                  G.sha(os.path.join(p1, "any_file.txt"))], av2),
        "av2_cache_stageB_v02": (["av2_cache_stageB_v02.py", "--stage-a", os.path.join(p1, "fake_stageA"), "--gt", os.path.join(p1, "fake_gt.json"), "--out",
                                  os.path.join(o, "B2"), "--frozen-plan", plan, "--hash-log", log], av2),
        "c1_h8_v01": (["c1_h8_v01.py", "--workers", w, "--gt", gt, "--meta", meta, "--horizon", hz, "--out", os.path.join(o, "h8a.json")], C1),
        "c1_h8_v02": (["c1_h8_v02.py", "--workers", w, "--gt", gt, "--meta", meta, "--horizon", hz, "--e0-plan", e0, "--out", os.path.join(o, "h8b.json")], C1),
        "c1_mstage_v01": (["c1_mstage_v01.py"] + ms, C1),
        "c1_mstage_v02": (["c1_mstage_v02.py"] + ms, C1),
        "c1_e0_v01": (["c1_e0_v01.py", "--workers", w, "--gt", gt, "--meta", meta, "--horizon", hz, "--out", os.path.join(o, "e0.json")], C1),
        "c1_predarm_v01": (["c1_predarm_v01.py", "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", folds, "--tracker-index", "0", "--out",
                            os.path.join(o, "pa1.json")], C1),
        "c1_predarm_v02": (["c1_predarm_v02.py", "--keys", os.path.join(p2, "keys_av2.npz"), "--folds", folds, "--tracker-index", "0", "--out",
                            os.path.join(o, "pa2.json"), "--plan", plan, "--hash-log", log], C1),
        "c1_fit_v02": (["c1_fit_v02.py", "--items", items, "--folds", folds, "--out", os.path.join(o, "fit.json"), "--plan", plan, "--hash-log", log], C1),
        "c1_run_v01": (["c1_run_v01.py", "--caches", os.path.join(p2, "cache_av2"), "--fits", ff, "--c1-folds", folds, "--c1-plan", plan, "--tag", "x",
                        "--mode", "decide", "--out", os.path.join(o, "run1")], C1),
        "c1_run_v02": (["c1_run_v02.py", "--caches", os.path.join(p2, "cache_av2"), "--fits", ff, "--c1-folds", folds, "--c1-plan", plan, "--hash-log", log,
                        "--tag", "x", "--mode", "decide", "--out", os.path.join(o, "run2")], C1),
        "c1_analyse_v01": (["c1_analyse_v01.py", "--config", cfg, "--out", os.path.join(o, "a1.json"), "--decision", os.path.join(o, "d1.json"), "--smoke"], C1),
        "c1_analyse_v02": (["c1_analyse_v02.py", "--config", cfg, "--out", os.path.join(o, "a2.json"), "--decision", os.path.join(o, "d2.json"), "--smoke"], C1),
        "c1_analyse_v03": (["c1_analyse_v03.py", "--config", cfg, "--out", os.path.join(o, "a3.json"), "--decision", os.path.join(o, "d3.json"), "--c1",
                            "--plan", plan, "--hash-log", log], C1),
        "c1_freeze_v01": (["c1_freeze_v01.py", "--plan", os.path.join(o, "P.md"), "--readme", os.path.join(o, "R.md"), "--results-dir", os.path.join(o, "res"),
                           "--bind", folds, "--hash-log", os.path.join(o, "L.txt")], C1),
        "c1_freeze_v02": (["c1_freeze_v02.py", "--plan", os.path.join(o, "P.md"), "--readme", os.path.join(o, "R.md"), "--results-dir", os.path.join(o, "res"),
                           "--folds", folds, "--split", os.path.join(o, "S.json"), "--transfer-fits", ff, ff, "--stageA-manifests", os.path.join(p1, "fake_stageA", "MANIFEST.json"),
                           "--config", cfg, "--hash-log", os.path.join(o, "L.txt")], C1)}
    out = {}
    for name, (cmd, cwd) in cmds.items():
        rc, txt = sub(cmd, cwd)
        ok = rc != 0 and ("is superseded" in txt or (name == "c1_predarm_v02" and "override is refused" in txt))
        assert ok, (name, txt[-700:])
        out[name] = "refused" + (" (names its replacement)" if "Use " in txt else " (guard)")
    written = [f for f in os.listdir(o) if f.endswith(".json") and f not in ("cfg.json", "fits.json")] + \
              [d for d in os.listdir(o) if os.path.isdir(os.path.join(o, d))]
    assert not written, "a refused main() wrote %s" % written
    import c1_legacy_refuse_v01 as LR
    G.LAST_GUARD.clear()
    assert "superseded" in str(_raises(LR.check, "c1_fit_v02", "c1_fit_v04", {"folds": "av2"}, "entry:c1_fit", plan))
    G.LAST_GUARD.update({"role": "entry:c1_fit", "plan": os.path.abspath(plan), "dataset": "av2"})
    assert LR.check("c1_fit_v02", "c1_fit_v04", {"folds": "av2"}, "entry:c1_fit", plan)
    assert _raises(LR.check, "c1_fit_v02", "c1_fit_v04", {"folds": "av2"}, "entry:c1_run", plan)
    assert _raises(LR.check, "c1_fit_v02", "c1_fit_v04", {"folds": "av2"}, "entry:c1_fit", os.path.join(o, "other.md"))
    G.LAST_GUARD.clear()
    out["delegation"] = "accepted only for the guarded role, plan and dataset of this process"
    return out


def _raises(fn, *a):
    try:
        fn(*a)
    except AssertionError as e:
        return e
    return None


LEGACY_RUNNER = r"""
import importlib.util, json, os, re, sys, traceback
C1, TP, mod, outdir, skip = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], set(sys.argv[5].split(",")) - {""}
sys.path.insert(0, C1); sys.path.insert(0, os.path.join(C1, "tests")); sys.path.insert(0, TP)
path = os.path.join(C1, "tests", mod + ".py")
spec = importlib.util.spec_from_file_location("__mp_main__", path)      # as the suite's own process saw it: the suite is not a bound module
T = importlib.util.module_from_spec(spec)
sys.modules["__mp_main__"] = T
spec.loader.exec_module(T)
T.OUT = outdir
os.makedirs(outdir, exist_ok=True)
src = open(path, encoding="utf-8").read()
body = src[src.index("    for name, fn in ("):]
body = body[:body.index("):") + 1]
names = re.findall(r'\("([A-Za-z0-9_]+)", (?:lambda: )?(t_[a-z0-9_]+)(\(heavy\))?\)', body)
res, ok = {}, bool(names)
for name, fn, heavy in names:
    if name in skip:
        res[name] = "replaced by GENORIG"
        continue
    try:
        f = getattr(T, fn)
        f(True) if heavy else f()
        res[name] = "pass"
    except Exception:
        ok = False
        res[name] = "FAIL: " + traceback.format_exc()[-1500:]
json.dump(res, open(os.path.join(outdir, "legacy_result.json"), "w"), indent=1)
print("LEGACY_ONE", "PASS" if ok else "FAIL")
"""


def t_legacy():
    out = {}
    for mod in ("test_c1_v01", "test_c1_v02", "test_c1_v03", "test_c1_v04", "test_c1_v05", "test_c1_v06"):
        od = os.path.join(OUT, "legacy_" + mod)            # the earlier suites' outputs are not overwritten
        r = subprocess.run([PY, "-B", "-c", LEGACY_RUNNER, C1, os.path.join(W, "50_CODE", "tpp", "tests"), mod, od, ",".join(SKIP_LEGACY.get(mod, ()))],
                           capture_output=True, text=True, cwd=C1)
        res = json.load(open(os.path.join(od, "legacy_result.json"))) if os.path.exists(os.path.join(od, "legacy_result.json")) else {"error": r.stderr[-1500:]}
        assert r.returncode == 0 and "LEGACY_ONE PASS" in r.stdout, (mod, res, r.stderr[-800:])
        out[mod] = res
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v08.json")
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {"tested_files_sha256": {f: G.sha(os.path.join(C1, f)) for f in TESTED}, "python": sys.version}, True
    for name, fn in (("ARCH", t_arch), ("MAINONLY", t_mainonly), ("GENORIG", t_genorig), ("REFUSE", t_refuse), ("LEGACY", t_legacy)):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-2500:], flush=True)
        json.dump(res, open(out_path + ".partial", "w"), indent=1, default=str)
    res["tested_files_sha256_at_end"] = {f: G.sha(os.path.join(C1, f)) for f in TESTED}
    if res["tested_files_sha256_at_end"] != res["tested_files_sha256"]:
        ok = False
        res["files_changed_during_tests"] = True
    res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_path, "w"), indent=1, default=str)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
