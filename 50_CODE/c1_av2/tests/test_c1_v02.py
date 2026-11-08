#!/usr/bin/env python3
"""Tests of the C1 v02 additions (Claude line, test_c1_v02, 2 Nov 2026). Synthetic data and nuScenes development data only.
  MS     c1_mstage_v01: the substitutions (C1 seed base, exact CRC, the capture wrapper) are in place; on planted refit summaries
         H6b's p-value is <= 0.05 exactly when B4's sup-t flag and the paired flag hold in a cell where M* is not flagged; a smoke run
         of E1-AV2 and E2-AV2 on the nuScenes validation exports (as the AV2 set and as the training set; 1 repetition, tiny B) runs
         and gives the summaries c1_analyse consumes, with H6b <=> (H6b_p <= 0.05).
  H8     c1_h8_v01 on the nuScenes validation exports (a stand-in for AV2 T1): runs, reports the 4 decision cells, both bands, H8.
  PRED   c1_predarm_v01 on the tpp helper's synthetic keys and runs (150 scenes as units, C1 folds of 30): H9 for PD and PD7; a QCNet
         file built from the same predictions with shuffled rows and (sample_token, instance_token) keys gives exactly the same
         result as the Trajectron++ arm (the alignment is exact).
  RHK1   RETUNED-HK1 on planted sweep tables: the least conservative point valid on the training folds is chosen in every fold.
  FRZ    c1_freeze_v01: refuses an open slot, a hash mismatch against the README, a non-empty block; a dry run writes nothing; a real
         freeze (in a scratch copy) writes the block, the sidecar and the log line, and the plan then refuses a second freeze.
  GEN2   tests/make_c1_analyse_v02.py reproduces c1_analyse_v02.py.   APPLY  c1_transfer_apply_v01 keeps the fit content.
Usage (from 50_CODE/c1_av2): python -B tests/test_c1_v02.py <out.json> [--skip-heavy]
"""
import json
import os
import shutil
import sys
import time
import traceback

import numpy as np

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(C1, "tests"))
sys.path.insert(0, os.path.join(W, "50_CODE", "tpp", "tests"))
OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v02")
VAL = {"workers": [os.path.join(W, "60_RESULTS", "x1_export_val150_v02", "worker%d" % i) for i in range(3)],
       "gt": os.path.join(W, "30_DATA", "x1_gt", "x1_val_gt_v02.json"), "meta": os.path.join(W, "30_DATA", "nuscenes", "v1.0-trainval"),
       "horizon": os.path.join(W, "60_RESULTS", "x1", "x1_horizon_v01.jsonl.gz"), "experiment": "paper/local/canmot/sc"}


def t_ms(heavy):
    import c1_mstage_v01 as MS
    MS.configure()
    M = MS.M
    assert M.SEED == 20261113 and M.L.crc_threshold is MS.X.crc_threshold_exact and M.eval_stats_replicates is MS.eval_stats_replicates_capture
    rng = np.random.default_rng(1)
    out = {}
    cells = ["c0", "c1", "c2", "c3"]
    for name, eB, eM, expect in (("pass", [0.04, 0.15, 0.04, 0.04], [0.04, 0.04, 0.04, 0.04], True),
                                 ("Mstar_flagged_there", [0.04, 0.15, 0.04, 0.04], [0.04, 0.14, 0.04, 0.04], False),
                                 ("B4_fine", [0.04, 0.05, 0.04, 0.04], [0.04, 0.04, 0.04, 0.04], False)):
        bB = np.array(eB)[None] + 0.01 * rng.standard_normal((300, 4))
        bM = np.array(eM)[None] + 0.01 * rng.standard_normal((300, 4))
        sigM = M._simul(np.array(eM), bM, 0.95, "lower")
        refit = {"cells": cells, "methods": {"B4": {"cells": {c: {"E_scene": eB[j]} for j, c in enumerate(cells)}},
                                             "Mstar": {"cells": {c: {"E_scene": eM[j], "sig_under": bool(sigM[0][j] > 0.05)} for j, c in enumerate(cells)}}}}
        p, per = MS.h6b_pvalue(refit, {"B4": bB, "Mstar": bM})
        assert (p <= 0.05) == expect, (name, p)
        out[name] = p
    if heavy:
        t0 = time.time()
        MS.configure()
        av2 = MS.load(VAL["workers"], VAL["gt"], VAL["meta"], VAL["horizon"], VAL["experiment"])
        res = MS.run(av2, av2, "T1", reps=1, B=40, BR=3, B2=3)
        h = res["E1"]["hypotheses"]
        b4 = M.failures([res["E1"]["refit"]], "B4", "B4-Mstar")
        assert set(res) >= {"E1", "E2", "H6b_p"} and "fixed" in res["E1"] and "refit" in res["E1"] and "cells" in res["E2"]
        out["smoke"] = {"HM1": h["HM1"], "B4_failing": b4, "H6b_p": res["H6b_p"], "HM6": res["E2"]["hypotheses"]["HM6"],
                        "cells_E1": len(res["cells_E1"]), "seconds": round(time.time() - t0, 1)}
        json.dump(res, open(os.path.join(OUT, "ms_smoke_t1.json"), "w"), indent=1, default=float)
    return out


def t_h8(heavy):
    if not heavy:
        return {"skipped": True}
    import c1_h8_v01 as H8
    r = H8.compute(VAL["workers"], VAL["gt"], VAL["meta"], VAL["horizon"])
    assert set(r["bins"]) == {"<20", "20-40"} and len(r["cells"]) == 4 and isinstance(r["H8"], bool)
    json.dump(r, open(os.path.join(OUT, "h8_nuscenes_val.json"), "w"), indent=1, default=float)
    return {"H8": r["H8"], "bins": r["bins"], "seconds": r["seconds"]}


def t_pred():
    import c1_predarm_v01 as P
    import c1_folds_v01 as F
    import test_tpp_analyse_v01 as TT
    d = os.path.join(OUT, "pred")
    os.makedirs(d, exist_ok=True)
    kp, runs, _ = TT.make_synthetic(d, seed=5, n_scenes=150)
    kz = dict(np.load(kp, allow_pickle=False))
    names = [str(x) for x in kz["scene_names"]]
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s syn" % n for n in names))
    F.main(["--logs", lp, "--out", os.path.join(d, "folds.json"), "--seed", "20261112"])
    out_t = os.path.join(d, "pred_tpp.json")
    P.main(["--keys", kp, "--runs", "trk=" + runs["trk"], "--folds", os.path.join(d, "folds.json"), "--tracker-index", "0", "--out", out_t, "--synthetic"])
    rt = json.load(open(out_t))
    # QCNet: the same predictions as a QCNet file, rows shuffled, keyed by (sample_token, instance_token)
    rz = np.load(runs["trk"], allow_pickle=False)
    n = len(kz["rec_k"])
    st_tok = np.array(["tok%06d" % i for i in range(n)])
    in_tok = np.array(["inst%06d" % i for i in range(n)])
    kz2 = dict(kz, rec_sample_token=st_tok, rec_instance_token=in_tok)
    kp2 = os.path.join(d, "keys_with_tokens.npz")
    np.savez(kp2, **kz2)
    perm = np.random.default_rng(3).permutation(n)
    c3 = rz["v2_cov"]
    cov22 = np.stack([np.stack([c3[:, 0], c3[:, 1]], -1), np.stack([c3[:, 1], c3[:, 2]], -1)], 1)
    ok = rz["status"] == P.TA.C.ST_OK
    qn = os.path.join(d, "qcnet_syn.npz")
    np.savez(qn, sample_token=st_tok[perm], instance_token=in_tok[perm], v2_mu=rz["v2_mu"][perm], v2_cov=cov22[perm], finite=ok[perm], pd_v2=ok[perm])
    out_q = os.path.join(d, "pred_qcnet.json")
    P.main(["--keys", kp2, "--folds", os.path.join(d, "folds.json"), "--tracker-index", "0", "--out", out_q, "--synthetic", "--qcnet-deployed", qn])
    rq = json.load(open(out_q))
    for pop in ("PD", "PD7"):
        a_, b_ = rt["arms"]["TPP"][pop], rq["arms"]["Q1_deployed"][pop]
        for k in ("H9", "family_size", "flagged", "pooled_flagged", "items", "exceed_share"):
            assert a_[k] == b_[k], ("QCNet alignment", pop, k, a_[k], b_[k])
    return {"TPP": {p: {k: rt["arms"]["TPP"][p][k] for k in ("H9", "family_size", "evaluable", "flagged", "items")} for p in ("PD", "PD7")},
            "QCNet_alignment_exact": True}


def t_rhk1():
    import c1_analyse_v02 as CA
    A, K = CA.A, CA.K
    rng = np.random.default_rng(4)
    n_keys = 120
    cells = A.cell_family()
    nc = len(cells)
    keys = [("s%03d" % i, 0) for i in range(n_keys)]
    scene_of_ep = np.array([k[0] for k in keys])
    log_of_ep = np.arange(n_keys)
    Wl = rng.multinomial(n_keys, np.full(n_keys, 1.0 / n_keys), size=300).astype(float)
    fold = np.arange(n_keys) % 5
    sweep = ["B0a0.25", "B0a1", "B0a8"]
    rate = {"B0a0.25": 0.15, "B0a1": 0.02, "B0a8": 0.002}
    tabs = {}
    for p in CA.POPS:
        Ns, Xs = {}, {}
        for a in sweep:
            N = rng.integers(30, 80, (n_keys, nc)).astype(float)
            Ns[a], Xs[a] = N, rng.binomial(N.astype(int), rate[a]).astype(float)
        tabs[p] = (Ns, Xs)
    old = (A.MIN_SCENES, A.MIN_LOGS)
    A.MIN_SCENES, A.MIN_LOGS = 39, 8
    try:
        choice, arm_of_key, T = CA.retuned_hk1(tabs, cells, keys, scene_of_ep, log_of_ep, Wl, fold, sweep, [1, 2])
    finally:
        A.MIN_SCENES, A.MIN_LOGS = old
    assert all(v["arm"] == "B0a1" and not v["none_qualifies"] for v in choice.values()), choice
    return {"choice": {k: v["arm"] for k, v in choice.items()}}


def t_frz():
    import c1_freeze_v01 as FZ
    d = os.path.join(OUT, "freeze")
    shutil.rmtree(d, ignore_errors=True)
    os.makedirs(d)
    files = ["50_CODE/c1_av2/c1_folds_v01.py", "50_CODE/c1_av2/c1_crc_exact_v01.py"]
    readme = os.path.join(d, "README_test.md")
    open(readme, "w").write("```\n" + "\n".join("%s  %s" % (FZ.sha(os.path.join(W, f)), f) for f in files) + "\n```\n")
    plan = os.path.join(d, "PLAN_test.md")
    body = "# plan\ntext\n\nFROZEN_HASHES_BEGIN\nFROZEN_HASHES_END\n"
    res_dir = os.path.join(d, "results")
    log = os.path.join(d, "C1_PLAN_HASH_LOG_test.txt")
    base = ["--plan", plan, "--readme", readme, "--results-dir", res_dir, "--hash-log", log, "--bind", files and os.path.join(W, files[0])]
    out = {}
    open(plan, "w").write(body.replace("text", "text [SLOT: open]"))
    try:
        FZ.main(base + ["--dry-run"])
        out["slot_refused"] = False
    except AssertionError as e:
        out["slot_refused"] = "open slots" in str(e)
    open(plan, "w").write(body)
    bad = os.path.join(d, "README_bad.md")
    open(bad, "w").write("%s  %s\n" % ("0" * 64, files[0]))
    try:
        FZ.main(["--plan", plan, "--readme", bad, "--results-dir", res_dir, "--hash-log", log, "--dry-run"])
        out["hash_mismatch_refused"] = False
    except AssertionError as e:
        out["hash_mismatch_refused"] = "differs from the README" in str(e)
    FZ.main(base + ["--dry-run"])
    assert open(plan).read() == body and not os.path.exists(plan.replace(".md", ".sha256")) and not os.path.exists(log)
    FZ.main(base)
    txt = open(plan).read()
    assert all(f in txt for f in files) and os.path.exists(plan.replace(".md", ".sha256")) and len(open(log).read().splitlines()) == 1
    assert open(plan.replace(".md", ".sha256")).read().split()[0] == FZ.sha(plan)
    try:
        FZ.main(base)
        out["second_freeze_refused"] = False
    except AssertionError:
        out["second_freeze_refused"] = True
    assert out["slot_refused"] and out["hash_mismatch_refused"] and out["second_freeze_refused"]
    return out


def t_gen2():
    import make_c1_analyse_v02 as MK
    with open(os.path.join(C1, "c1_analyse_v01.py"), encoding="utf-8", newline="") as f:
        g = MK.make(f.read())
    assert g == open(os.path.join(C1, "c1_analyse_v02.py"), encoding="utf-8", newline="").read()
    return {"reproduced": True}


def t_apply():
    import c1_transfer_apply_v01 as TA_
    d = os.path.join(OUT, "apply")
    os.makedirs(d, exist_ok=True)
    src = {"route": "transfer", "fits": {"0": {"h0p5s": {"Mstar_ip": [1.0] * 192}}}, "joint": {"x": 1}, "retuned_transfer_arm": "B0a1",
           "scenes": ["a"], "fold_of_scene": {"a": 0}, "folds_sha256": "old"}
    sp = os.path.join(d, "src.json")
    json.dump(src, open(sp, "w"))
    fp = os.path.join(d, "folds.json")
    json.dump({"fold_of_log": {"L1": 0, "L2": 3}}, open(fp, "w"))
    TA_.main(["--transfer-fit", sp, "--folds", fp, "--out", os.path.join(d, "out.json")])
    o = json.load(open(os.path.join(d, "out.json")))
    assert o["fold_of_scene"] == {"L1": 0, "L2": 0} and o["fits"] == src["fits"] and o["folds_sha256"] == TA_.sha(fp)
    return {"ok": True}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else os.path.join(OUT, "c1_tests_v02.json")
    heavy = "--skip-heavy" not in sys.argv
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {}, True
    for name, fn in (("GEN2", t_gen2), ("APPLY", t_apply), ("FRZ", t_frz), ("RHK1", t_rhk1), ("PRED", t_pred), ("MS", lambda: t_ms(heavy)),
                     ("H8", lambda: t_h8(heavy))):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-1800:], flush=True)
    res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["heavy"] = heavy
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_path, "w"), indent=1, default=str)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
