#!/usr/bin/env python3
"""Tests of H8's E0 (Claude line, test_c1_v05, 4 Nov 2026; D16 v11 Choice 31). nuScenes validation data (X1's) only; one process.
  E0X1  c1_e0_v01 in mode "x1" on X1's own inputs (the inputs' hashes are checked against x1_sizes_v02.json) reproduces X1's frozen
        E0 (x1_sizes_v02.json, families t0 and h2s) exactly for the car lateral cells at sigma_a 0.10, from stage-A rows that read no
        ground-truth position after k; the other cells and sigma 0.20 are compared and reported.
  E0C1  mode "c1" (seed 20261114, one generator per cell and sigma): two computations agree bit for bit; another seed differs.
  H8V2  c1_h8_v02 with the plan's E0 runs, and its lateral thresholds are max(0.05, E0_plan).
  A4    c1_analyse_v04's decide: a recomputed E0 that differs from the plan, or no E0 under --c1, makes the verdict NO-GO.
Usage (from 50_CODE/c1_av2): python -B tests/test_c1_v05.py <out.json>
"""
import json
import os
import sys
import time
import traceback

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v05")
VAL = {"workers": [os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker%d" % i) for i in range(3)],
       "gt": os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json"), "meta": os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval"),
       "horizon": os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz")}
SIZES = os.path.join(W, "60_RESULTS", "x1", "x1_sizes_v02.json")
STATE = {}


def t_e0x1():
    import c1_e0_v01 as E0
    sz = json.load(open(SIZES))
    exp = [E0.L.sha256_path(os.path.join(w, "x1_tracks.jsonl.gz")) for w in VAL["workers"]]
    assert exp == sz["inputs"]["export_sha256"] and E0.L.sha256_path(VAL["gt"]) == sz["inputs"]["gt_sha256"], "not X1's inputs"
    rows, hr, info = E0.load_rows(VAL["workers"], VAL["gt"], VAL["meta"], VAL["horizon"])
    STATE["rows"], STATE["hr"] = rows, hr
    tab = E0.e0_table({"t0": rows, "h2s": hr}, "x1")
    out, ok = {}, True
    for fam in ("t0", "h2s"):
        for sa in ("0.10", "0.20"):
            for c, v in tab[fam][sa].items():
                ref = sz["families"][fam]["cells"].get(c, {}).get("E0_sigma_%s" % sa)
                eq = (ref == v["E0"]) or (ref is None and v["E0"] is None)
                if c.startswith("car|") and c.endswith("|lat"):
                    out["%s %s %s" % (fam, sa, c)] = {"c1_e0": v["E0"], "x1_frozen": ref, "equal": eq}
                    if sa == "0.10":
                        ok = ok and eq
                out.setdefault("all_cells_equal_%s_%s" % (fam, sa), True)
                out["all_cells_equal_%s_%s" % (fam, sa)] &= eq
    assert ok, out
    return out


def t_e0c1():
    import c1_e0_v01 as E0
    a = E0.e0_table({"h2s": STATE["hr"]}, "c1", 20261114)
    b = E0.e0_table({"h2s": STATE["hr"]}, "c1", 20261114)
    c = E0.e0_table({"h2s": STATE["hr"]}, "c1", 1)
    assert a == b and a["h2s"]["0.10"]["car|<20|lat"]["E0"] != c["h2s"]["0.10"]["car|<20|lat"]["E0"]
    STATE["plan"] = {k: a["h2s"]["0.10"][k]["E0"] for k in E0.DECISION_CELLS}
    return {"plan_values_seed20261114": STATE["plan"], "bit_exact": True}


def t_h8v2():
    import c1_h8_v02 as H
    r = H.compute(VAL["workers"], VAL["gt"], VAL["meta"], VAL["horizon"], STATE["plan"])
    for c in ("car|<20|lat", "car|20-40|lat"):
        assert r["thresholds"][c] == max(0.05, STATE["plan"][c])
    json.dump(r, open(os.path.join(OUT, "h8v2_nuscenes_val.json"), "w"), indent=1, default=float)
    return {"H8": r["H8"], "thresholds": {c: r["thresholds"][c] for c in ("car|<20|lat", "car|20-40|lat")}, "data_based": r["E0_data_based_reported"]}


def t_a4():
    import c1_analyse_v04 as A4
    base = {"within_lt3d": {}}
    out = {}
    for name, chk, mode, expect_nogo in (("mismatch", {"done": True, "present": True, "match": False, "recomputed": {"x": 1}, "plan": {"x": 2}}, "smoke", True),
                                         ("missing_c1", {"done": True, "present": False, "match": False}, "c1", True),
                                         ("match", {"done": True, "present": True, "match": True, "plan": {"car|<20|lat": 0.01, "car|20-40|lat": 0.02}}, "smoke", False)):
        A4.E0_CHECK.clear()
        A4.E0_CHECK.update(chk)
        dec = A4.decide(base, {"routes": []}, mode)
        e0_fail = any("E0" in x for x in dec["failed_conditions"])
        assert e0_fail == expect_nogo and dec["C1_verdict"] == "NO-GO"
        out[name] = {"E0_failed_condition": e0_fail}
    return out


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v05.json")
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {}, True
    for name, fn in (("E0X1", t_e0x1), ("E0C1", t_e0c1), ("H8V2", t_h8v2), ("A4", t_a4)):
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
