#!/usr/bin/env python3
"""Tests of the R17 fixes (Claude line, test_c1_v03, 2 Nov 2026). Synthetic data and nuScenes development data only; one process.
  C2     a missing comparator fails Form B and H3, and decide() returns NO-GO with the reason; RETUNED missing from the transfer route
         is a failed condition of H4; an arm missing in a log is an error (per_scene_rates).
  M1     Holm with m = 5: a failed gate, a missing p-value and an absent claim all enter with p = 1 (planted p's that v02 would confirm
         are not confirmed); "confirmed" needs the bound-based verdict too (m6).
  m2     an M*Jx lambda that did not qualify fails H3.   m3  an empty V_t is vacuous (p None), never p = 0.   m5  ValidJ needs
         evaluability.   m9  no B4: a failed condition, no crash.   NaN  NaN rates are an error.
  GUARD  c1_guard_v01: a slot, a missing sidecar, a sidecar mismatch and an unlogged hash each refuse a plan; a logged plan passes;
         dataset tags. Stage-B v02 refuses an AV2-tagged cache without a logged frozen plan, and with a draft plan whose hash is passed
         on the command line. c1_fit_v02 refuses NaN items and non-nuScenes units without a plan. c1_run_v02 --standin refuses an
         AV2-tagged cache (dry run). c1_analyse_v03 --smoke refuses a C1 confirmatory run record.
  FOLD2  c1_folds_v02: duplicates refused, NumPy version recorded, no absolute path, the 225 + 150 split check.
  E15d   discriminating: on nuScenes T3 fold 4 h2s cell L0 74 the FLOAT rule gives different thresholds in K7's order and in sorted
         order (0.39570 and 0.38665), the exact rule gives 0.38665 in both.
  C3     on a development scene, changing every threshold at the 2.5-4 s steps changes no decision, count or calibration record.
  GEN3   the generators reproduce c1_run_v02.py and av2_cache_stageB_v02.py.
Usage (from 50_CODE/c1_av2): python -B tests/test_c1_v03.py <out.json>
"""
import copy
import json
import os
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
sys.path.insert(0, os.path.join(W, "50_CODE", "k8"))
import c1_analyse_v03 as CA  # noqa: E402
import c1_guard_v01 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v03")
PY = sys.executable
B = CA.B


def entry(**kw):
    import test_c1_v01 as T1
    return T1.entry(**kw)


def weights(n=80, B_=2000, seed=1):
    return np.random.default_rng(seed).multinomial(n, np.full(n, 1.0 / n), size=B_).astype(float)


def rates(rng, means, n=80, sd=0.03):
    return {a: np.clip(m + sd * rng.standard_normal(n), 0, 1) for a, m in means.items()}


def t_c2():
    rng = np.random.default_rng(2)
    Ws = weights()
    st = {a: B.arm_status(entry(flagged=["c"]) if a in ("B0", "B1", "B4", "B9", "RETUNED") else entry()) for a in ("Mstar",) + B.K_SET}
    r = rates(rng, {"Mstar": 0.10, "B0": 0.3, "B1": 0.3, "B3": 0.8, "B4": 0.2, "B6": 0.05, "B9": 0.4, "RETUNED": 0.4})
    full = CA.form_b(st, r, Ws)
    assert not full["met"] and "B6" in full["V"], "a valid, more operable B6 must fail Form B"
    st2 = {k: v for k, v in st.items() if k != "B6"}
    r2 = {k: v for k, v in r.items() if k != "B6"}
    fb = CA.form_b(st2, r2, Ws)
    assert not fb["met"] and fb["missing"] == ["B6"], "R17's probe: removing B6 must not turn Form B into met"
    res = {"within_lt3d": {t: {"form_b": fb, "status": st2, "form_c": None, "form_a": {}} for t in B.TRACKERS}}
    dec = CA.decide(res, {"routes": []}, "smoke")
    assert dec["C1_verdict"] == "NO-GO" and any("comparators missing" in x for x in dec["failed_conditions"])
    assert any("B4 is missing" in x for x in dec["failed_conditions"]), "m9: no B4 must be a failed condition, not a crash"
    try:
        CA.per_scene_rates([{"scene": "s1", "arm": "B4", "entered": True, "infeasible_frames": 1, "frames": 10}], None, ["s1", "s2"])
        raised = False
    except AssertionError:
        raised = True
    assert raised, "an arm missing in a log must be an error"
    return {"form_b_with_B6_absent": {"met": fb["met"], "missing": fb["missing"]}, "verdict": dec["C1_verdict"]}


def t_m1():
    claims = {"H2": {"p": 0.012, "gate_ok": True, "holds": True}, "H3": {"p": 0.001, "gate_ok": False, "holds": False},
              "H10": {"p": 0.03, "gate_ok": True, "holds": True}}
    h = CA.holm(claims, 0.05, gate=True)
    assert set(h) == set(CA.FAMILY_S) and all(v["m"] == 5 for v in h.values())
    assert not h["H2"]["confirmed"] and not h["H10"]["confirmed"], "R17's probe: with m = 5 neither H2 (0.012) nor H10 (0.03) is confirmed"
    assert h["H4"]["p"] == 1.0 and h["H6b"]["p"] == 1.0 and h["H3"]["p"] == 1.0
    h2 = CA.holm({"H2": {"p": 0.001, "gate_ok": True, "holds": False}}, 0.05, gate=True)
    assert h2["H2"]["rejected"] and not h2["H2"]["confirmed"], "m6: p alone never confirms"
    return {"levels": {c: round(v["holm_level"], 4) for c, v in h.items()}}


def t_minor():
    rng = np.random.default_rng(3)
    Ws = weights()
    st = {a: B.arm_status(entry(flagged=["c"])) for a in B.K_SET}
    st["Mstar"] = B.arm_status(entry())
    r = rates(rng, {a: 0.3 for a in ("Mstar",) + B.K_SET})
    fb = CA.form_b(st, r, Ws)
    assert fb["vacuous"] and fb["p_rejection_bonferroni"] is None and fb["met"], "m3: empty V_t is vacuous, never p = 0"
    jv = {"pops": {p: {"E": 0.03, "lb_one_sided_0.95": 0.02, "ub_one_sided_0.95": 0.04, "flagged": False, "ub_le_delta_plus_0.03": True,
                       "evaluable": p != "PD_inpath"} for p in B.POPS}}
    assert not CA.joint_status(jv)["validJ"], "m5: a non-evaluable joint population fails ValidJ"
    d = os.path.join(OUT, "minor")
    os.makedirs(d, exist_ok=True)
    fp = os.path.join(d, "fits_lambda_bad.json")
    json.dump({"joint": {"fit": {"folds": {"0": {"MstarJx": {"none_qualifies_grid_max_used": True}}, "1": {"MstarJx": {"none_qualifies_grid_max_used": False}}}}}},
              open(fp, "w"))
    ok_, bad = CA.lambda_qualified(fp)
    assert not ok_ and bad == ["0"], "m2: an unqualified lambda is flagged"
    try:
        CA.per_scene_rates([{"scene": "s1", "arm": "B4", "entered": True, "infeasible_frames": float("nan"), "frames": 10}], None, ["s1"])
        nan_raised = False
    except AssertionError:
        nan_raised = True
    assert nan_raised, "NaN outcomes are an error"
    return {"vacuous": True, "validJ_needs_evaluable": True, "lambda_flag": bad, "nan_error": nan_raised}


def mock_plan(d, logged=True, slot=False, sidecar=True, body_extra=""):
    os.makedirs(d, exist_ok=True)
    plan = os.path.join(d, "PLAN.md")
    f1 = os.path.join(C1, "c1_guard_v01.py")
    txt = "# plan %s\n%s\nFROZEN_HASHES_BEGIN\n%s  %s\nFROZEN_HASHES_END\n" % ("[SLOT: x]" if slot else "", body_extra, G.sha(f1), G.rel(f1))
    open(plan, "w").write(txt)
    if sidecar:
        open(plan[:-3] + ".sha256", "w").write(G.sha(plan) + "  PLAN.md\n")
    log = os.path.join(d, "LOG.txt")
    open(log, "w").write((G.sha(plan) + "  x\n") if logged else "")
    return plan, log


def t_guard():
    out = {}
    base = os.path.join(OUT, "guard")
    shutil.rmtree(base, ignore_errors=True)
    for name, kw in (("slot", {"slot": True}), ("no_sidecar", {"sidecar": False}), ("not_logged", {"logged": False})):
        plan, log = mock_plan(os.path.join(base, name), **kw)
        try:
            G.frozen_plan(plan, log)
            out[name] = "accepted"
        except AssertionError as e:
            out[name] = "refused"
        assert out[name] == "refused", name
    plan, log = mock_plan(os.path.join(base, "ok"))
    side, frozen = G.frozen_plan(plan, log)
    open(plan, "a").write("tamper\n")
    try:
        G.frozen_plan(plan, log)
        out["sidecar_mismatch"] = "accepted"
    except AssertionError:
        out["sidecar_mismatch"] = "refused"
    assert out["sidecar_mismatch"] == "refused"
    assert G.units_dataset(["scene-0001", "scene-1100"]) == "nuscenes" and G.units_dataset(["0c6e62d7-bdfa-3061-8d3d-03b13aa21f68"]) == "unknown"
    # stage-B v02 on a tiny AV2-tagged stage-A cache: refused without a logged frozen plan, and with a draft plus its own hash
    sa = os.path.join(base, "stageA")
    os.makedirs(sa, exist_ok=True)
    json.dump({"dataset": "av2", "stage": "A", "scenes": {}}, open(os.path.join(sa, "MANIFEST.json"), "w"))
    gt = os.path.join(base, "gt.json")
    json.dump({"samples": [], "annotations": []}, open(gt, "w"))
    sb = os.path.join(W, "50_CODE", "av2", "av2_cache_stageB_v02.py")
    draft, dlog = mock_plan(os.path.join(base, "draft"), logged=False)
    for name, extra in (("no_plan", []), ("draft_with_its_hash", ["--frozen-plan", draft, "--frozen-plan-sha256", G.sha(draft), "--hash-log", dlog])):
        r = subprocess.run([PY, "-B", sb, "--stage-a", sa, "--gt", gt, "--out", os.path.join(base, "stageB_" + name)] + extra, capture_output=True, text=True)
        assert r.returncode != 0 and "refused" in (r.stdout + r.stderr), (name, r.stdout[-300:], r.stderr[-300:])
        out["stageB_" + name] = "refused"
    # c1_run_v02 --standin on an AV2-tagged cache directory: refused (dry run, manifests only)
    av = os.path.join(base, "cacheA")
    os.makedirs(av, exist_ok=True)
    json.dump({"dataset": "av2", "scenes": {"logX": {"sha256": "0", "log": "logX"}}}, open(os.path.join(av, "MANIFEST.json"), "w"))
    fo = os.path.join(base, "folds.json")
    json.dump({"fold_of_log": {"logX": 0}}, open(fo, "w"))
    ff = os.path.join(base, "fits.json")
    json.dump({"folds_sha256": G.sha(fo)}, open(ff, "w"))
    r = subprocess.run([PY, "-B", os.path.join(C1, "c1_run_v02.py"), "--caches", av, "--fits", ff, "--c1-folds", fo, "--standin", "--tag", "x",
                        "--mode", "decide", "--out", os.path.join(base, "runout"), "--dry-run"], capture_output=True, text=True)
    assert r.returncode != 0 and "--standin refuses" in r.stderr, r.stderr[-400:]
    out["run_standin_av2"] = "refused"
    # c1_analyse_v03 --smoke refuses a C1 confirmatory run record
    rd = os.path.join(base, "runs")
    os.makedirs(rd, exist_ok=True)
    json.dump({"c1": True, "standin": False, "caches": []}, open(os.path.join(rd, "run_record_t1_x_decide.json"), "w"))
    cfg = os.path.join(base, "cfg.json")
    json.dump({"routes": [{"name": "within_lt3d", "runs": rd, "tags": {"t1": "t1_x"}}]}, open(cfg, "w"))
    try:
        CA.main(["--config", cfg, "--out", os.path.join(base, "a.json"), "--decision", os.path.join(base, "d.json"), "--smoke"])
        out["analyse_smoke_c1_record"] = "accepted"
    except AssertionError:
        out["analyse_smoke_c1_record"] = "refused"
    assert out["analyse_smoke_c1_record"] == "refused"
    return out


def t_fit_guard():
    import c1_fit_v02 as FT
    d = os.path.join(OUT, "fitguard")
    os.makedirs(d, exist_ok=True)
    z = np.load(os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_t1.npz"))
    arrs = {k: z[k] for k in z.files}
    names = [str(x) for x in arrs["scene_names"]]
    arrs["item_D"] = arrs["item_D"].copy()
    arrs["item_D"][5] = np.nan
    pn = os.path.join(d, "items_nan.npz")
    np.savez(pn, **arrs)
    fo = os.path.join(d, "folds.json")
    json.dump({"fold_of_log": {n: i % 5 for i, n in enumerate(names)}, "k": 5, "seed": 1, "dataset": "nuscenes"}, open(fo, "w"))
    out = {}
    try:
        FT.main(["--items", pn, "--folds", fo, "--out", os.path.join(d, "f.json")])
        out["nan"] = "accepted"
    except AssertionError as e:
        out["nan"] = "refused" if "NaN" in str(e) else "other: " + str(e)[:80]
    assert out["nan"] == "refused", out
    fo2 = os.path.join(d, "folds_av2.json")
    json.dump({"fold_of_log": {n: i % 5 for i, n in enumerate(names)}, "k": 5, "seed": 1, "dataset": "av2"}, open(fo2, "w"))
    try:
        FT.main(["--items", os.path.join(W, "70_TESTS", "k8_scratch", "v02", "dev_v02", "items_k8_v02_dev_t1.npz"), "--folds", fo2, "--out", os.path.join(d, "f2.json")])
        out["av2_without_plan"] = "accepted"
    except AssertionError as e:
        out["av2_without_plan"] = "refused"
    assert out["av2_without_plan"] == "refused"
    return out


def t_fold2():
    import c1_folds_v02 as F2
    d = os.path.join(OUT, "fold2")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "dup.txt")
    open(p, "w").write("a val\nb val\na val\n")
    try:
        F2.main(["--logs", p, "--out", os.path.join(d, "x.json"), "--dataset", "nuscenes"])
        dup = "accepted"
    except AssertionError:
        dup = "refused"
    assert dup == "refused"
    held = ["h%03d" % i for i in range(225)]
    val = ["v%03d" % i for i in range(150)]
    json.dump({"held_out_225": held, "train_475": []}, open(os.path.join(d, "split.json"), "w"))
    open(os.path.join(d, "val.txt"), "w").write("\n".join(val))
    open(os.path.join(d, "ids.txt"), "w").write("\n".join(held + val))
    F2.main(["--logs", os.path.join(d, "ids.txt"), "--out", os.path.join(d, "f.json"), "--dataset", "av2", "--split", os.path.join(d, "split.json"),
             "--val", os.path.join(d, "val.txt")])
    f = json.load(open(os.path.join(d, "f.json")))
    txt = open(os.path.join(d, "f.json")).read()
    assert f["numpy_version"] == np.__version__ and ":\\\\" not in txt and W.replace("\\", "/") not in txt.replace("\\\\", "/")
    assert [f["by_fold"][str(j)]["logs"] for j in range(5)] == [75] * 5 and set(f["source_of_log"].values()) == {"held_out_train", "val"}
    open(os.path.join(d, "ids_bad.txt"), "w").write("\n".join(held[:-1] + val + ["zzz"]))
    try:
        F2.main(["--logs", os.path.join(d, "ids_bad.txt"), "--out", os.path.join(d, "g.json"), "--dataset", "av2", "--split", os.path.join(d, "split.json"),
                 "--val", os.path.join(d, "val.txt")])
        bad = "accepted"
    except AssertionError:
        bad = "refused"
    assert bad == "refused"
    return {"duplicates": dup, "split_mismatch": bad, "numpy": f["numpy_version"]}


def t_e15d():
    import c1_crc_exact_v01 as X
    fits = json.load(open(os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_t3_v01.json")))
    z = np.load(os.path.join(W, "30_DATA", "k7", "k7_items_t3_v01.npz"))
    names = [str(x) for x in z["scene_names"]]
    it = {k[5:]: z[k] for k in z.files if k.startswith("item_")}
    fold = np.array([fits["fold_of_scene"][n] for n in names], int)
    M = X.M
    lv = M.levels(it, it["m"])
    U = it["D"] / it["sd"]
    sel = (it["h"] == 3) & (fold[it["s"]] != 4) & (lv[0] == 74) & (it["inpath"] == 0)
    s_k7 = it["s"][sel]
    s_sorted = np.array([sorted(names).index(n) for n in names])[it["s"]][sel]
    fl = {"k7": M.L.crc_threshold(U[sel], s_k7), "sorted": M.L.crc_threshold(U[sel], s_sorted)}
    ex = {"k7": X.crc_threshold_exact(U[sel], s_k7), "sorted": X.crc_threshold_exact(U[sel], s_sorted)}
    assert fl["k7"] != fl["sorted"], "the float rule should depend on the order here (discriminating)"
    assert ex["k7"] == ex["sorted"] == 0.38664953418894527
    return {"float": fl, "exact": ex}


def t_c3():
    import k8_sim_v04 as S
    fits = json.load(open(os.path.join(W, "60_RESULTS", "k8_joint_fits_v01", "k8_joint_fits_t1_v02.json")))
    sc = S.Scene(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_train", "scene-0757.npz"))
    steps = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
    f0 = [fits["fits"][str(fits["fold_of_scene"]["scene-0757"])][h] for h in steps]
    f1 = copy.deepcopy(f0)
    for h in range(4, 8):
        for k, v in f1[h].items():
            if isinstance(v, list) and v and isinstance(v[0], float):
                f1[h][k] = [x * 7.0 for x in v]
            elif isinstance(v, float):
                f1[h][k] = v * 7.0
    out = {}
    for arm in ("Mstar", "MstarJ", "B4", "B6"):
        a_, ca = S.run_decisions(sc, arm, f0)
        b_, cb = S.run_decisions(sc, arm, f1)
        for k in ("decisions", "cal"):
            assert json.dumps(a_[k], sort_keys=True, default=float) == json.dumps(b_[k], sort_keys=True, default=float), (arm, k)
        assert ca == cb, arm
        out[arm] = "unchanged"
    return out


def t_gen3():
    import make_c1_run_v02 as MR
    import make_av2_stageB_v02 as MS
    assert MR.make(open(os.path.join(C1, "c1_run_v01.py"), encoding="utf-8", newline="").read()) == \
        open(os.path.join(C1, "c1_run_v02.py"), encoding="utf-8", newline="").read()
    av2 = os.path.join(W, "50_CODE", "av2")
    assert MS.make(open(os.path.join(av2, "av2_cache_stageB_v01.py"), encoding="utf-8", newline="").read()) == \
        open(os.path.join(av2, "av2_cache_stageB_v02.py"), encoding="utf-8", newline="").read()
    return {"reproduced": ["c1_run_v02.py", "av2_cache_stageB_v02.py"]}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v03.json")
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {}, True
    for name, fn in (("C2", t_c2), ("M1", t_m1), ("MINOR", t_minor), ("GUARD", t_guard), ("FITGUARD", t_fit_guard), ("FOLD2", t_fold2),
                     ("E15d", t_e15d), ("C3", t_c3), ("GEN3", t_gen3)):
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
