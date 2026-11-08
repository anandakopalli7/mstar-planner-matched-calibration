#!/usr/bin/env python3
"""Tests of the resumable versions (Claude line, test_c1_v04, 4 Nov 2026; researcher rule of 4 Nov). One process, tiny inputs.
  REH2  c1_rehearsal_v02.run: a step runs once, is logged (start, end, exit 0) in steps.jsonl, and is skipped on a rerun; a failing step
        is logged with its exit code and is not marked done.
  MS2   c1_mstage_v02.run_resumable with stub E1 / E2 functions: the first call computes both parts and checkpoints them; a second call
        reuses both (no computation); after the E2 checkpoint is deleted, a third call recomputes E2 only; a changed key recomputes.
Usage (from 50_CODE/c1_av2): python -B tests/test_c1_v04.py <out.json>
"""
import json
import os
import shutil
import sys
import time
import traceback

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v04")


def t_reh2():
    import c1_rehearsal_v02 as RH
    d = os.path.join(OUT, "reh2")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    RH.STEPS = os.path.join(d, "steps.jsonl")
    log = os.path.join(d, "log.txt")
    RH.run(["c1_guard_v01.py"], log)
    RH.run(["c1_guard_v01.py"], log)
    recs = [json.loads(l) for l in open(RH.STEPS)]
    assert [r["event"] for r in recs] == ["start", "end"] and recs[1]["exit"] == 0, recs
    assert "skipped" in open(log).read()
    try:
        RH.run(["c1_guard_v01.py", "--no-such-arg-but-ignored", "&&", "x"], log)   # exits 0 too (the module ignores argv)
    except AssertionError:
        pass
    try:
        RH.run(["-c", "import sys; sys.exit(3)"], log)
        failed = False
    except AssertionError:
        failed = True
    recs = [json.loads(l) for l in open(RH.STEPS)]
    assert failed and recs[-1]["exit"] == 3 and "-c import sys; sys.exit(3)" not in RH._done()
    return {"records": len(recs), "skip_works": True, "failure_not_done": True}


def t_ms2():
    import c1_mstage_v02 as MS
    V1, M, R = MS.V1, MS.M, MS.R
    calls = {"E1": 0, "E2": 0}
    saved = (R.run_e1, R.run_e2, V1.h6b_pvalue, M.motion_state, M.make_cells)

    def e1(*a, **k):
        calls["E1"] += 1
        V1.CAPTURE["cells"] = {"B4": None, "Mstar": None}
        return {"refit": {}, "hypotheses": {"HM1": True}}

    def e2(*a, **k):
        calls["E2"] += 1
        return {"hypotheses": {"HM6": True}}
    R.run_e1, R.run_e2 = e1, e2
    V1.h6b_pvalue = lambda refit, boots: (0.5, {})
    M.motion_state = lambda items: None
    M.make_cells = lambda items, m, kind: [("c", [0])]
    try:
        d = os.path.join(OUT, "ms2")
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
        out = os.path.join(d, "ms.json")
        data = {"h2s": ({}, {}), "_names": [], "_slog": {}}
        key = {"k": 1}
        r1 = MS.run_resumable(data, data, "T1", 1, 1, 1, 1, out, key)
        r2 = MS.run_resumable(data, data, "T1", 1, 1, 1, 1, out, key)
        assert calls == {"E1": 1, "E2": 1} and r1 == r2 and r1["H6b_p"] == 0.5
        os.remove(out + ".E2.ckpt.json")
        MS.run_resumable(data, data, "T1", 1, 1, 1, 1, out, key)
        assert calls == {"E1": 1, "E2": 2}
        MS.run_resumable(data, data, "T1", 1, 1, 1, 1, out, {"k": 2})
        assert calls == {"E1": 2, "E2": 3}
        ev = [json.loads(l)["event"] for l in open(out + ".steps.jsonl")]
        return {"calls": calls, "events": ev}
    finally:
        R.run_e1, R.run_e2, V1.h6b_pvalue, M.motion_state, M.make_cells = saved


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v04.json")
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {}, True
    for name, fn in (("REH2", t_reh2), ("MS2", t_ms2)):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-1500:], flush=True)
    res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_path, "w"), indent=1, default=str)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
