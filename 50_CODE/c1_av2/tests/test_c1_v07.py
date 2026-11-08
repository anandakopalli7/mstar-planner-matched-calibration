#!/usr/bin/env python3
"""Tests of c1_predarm_v03 (Claude line, test_c1_v07, 4 Nov 2026; D16 v16 Choice 37: history length as a DP-SCRC stratum of the
predictor arm). Synthetic data only (the tpp helper's generator); one process plus short subprocesses run one after another.
  EQV     the generic level fit without history length (levels L0..L3, exact CRC, n_min 19) gives, item for item, exactly the
          thresholds of c1_crc_exact_v01.fit_hier_exact (v01/v02's fit), on every fold; so "noHL" is D17's stratification.
  HL37    a planted short-history excess: the Trajectron++ errors of two-state records are scaled up (x2.0), so the predictor is
          over-confident on short histories only. Then
            (a) without the stratum (noHL fit) and without the HL cells (D17-style family, H9_noHL): the excess is MISSED: no HL cell is
                in the family, and the two-state exceedance is above delta + 0.02;
            (b) the noHL fit evaluated on the HL family ("noHL_on_HL_cells"): the hist=2 cell is flagged (CAUGHT by the cells);
            (c) with the stratum (H9's HL fit): the hist=2 cell is calibrated (exceedance <= delta + 0.02, not flagged).
          A control run without the planted excess: no HL cell is flagged under either fit.
  HLSRC   history length is read from the keys (rec_hist_stratum_trk for TPP), a used item with a stratum below 2 states is an error,
          and keys without the field are refused.
  P35     Choice 35 still holds in v03: units outside the folds are an error.
  DEC37   c1_analyse_v05.decide reports H9 from the HL arm and H9-noHL as a descriptive claim.
Every run records the SHA-256 of every tested file.
Usage (from 50_CODE/c1_av2): <canmot310 python> -B tests/test_c1_v07.py [<out.json>]
"""
import json
import os
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
import c1_guard_v02 as G  # noqa: E402

OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests_v07")
PY = sys.executable
TESTED = ["c1_predarm_v03.py", "c1_predarm_v02.py", "c1_analyse_v05.py", "c1_guard_v02.py", "c1_crc_exact_v01.py", "tests/test_c1_v07.py"]
STATE = {}
FACTOR = 2.0


def setup():
    if STATE:
        return STATE
    import c1_folds_v01 as F
    import test_tpp_analyse_v01 as TT
    d = os.path.join(OUT, "syn")
    os.makedirs(d, exist_ok=True)
    kp, runs, _ = TT.make_synthetic(d, seed=11, n_scenes=150)
    kz = dict(np.load(kp, allow_pickle=False))
    kz["rec_hist_stratum_gt"] = kz["rec_hist_stratum_trk"].copy()
    kp2 = os.path.join(d, "syn_keys_hl.npz")
    np.savez(kp2, **kz)
    names = [str(x) for x in kz["scene_names"]]
    lp = os.path.join(d, "units.txt")
    open(lp, "w").write("\n".join("%s syn" % n for n in names))
    F.main(["--logs", lp, "--out", os.path.join(d, "folds.json"), "--seed", "20261112"])
    rz = dict(np.load(runs["trk"], allow_pickle=False))
    import c1_predarm_v03 as P3
    ok = rz["status"] == P3.TA.C.ST_OK
    two = kz["rec_hist_stratum_trk"] == 0
    gt = kz["syn_gt_xy"]
    mu = rz["v2_mu"].copy()
    sel = ok & two
    mu[sel] = gt[sel] - FACTOR * (gt[sel] - mu[sel])
    rz_p = dict(rz, v2_mu=mu, v1_mu=mu)
    planted = os.path.join(d, "syn_run_trk_planted.npz")
    np.savez(planted, **rz_p)
    STATE.update({"d": d, "keys": kp2, "keys_orig": kp, "run": runs["trk"], "planted": planted, "folds": os.path.join(d, "folds.json"),
                  "two_share": float(two[ok].mean())})
    return STATE


def run_v03(keys, run, out, folds=None):
    s = setup()
    r = subprocess.run([PY, "-B", "c1_predarm_v03.py", "--keys", keys, "--runs", "trk=" + run, "--folds", folds or s["folds"], "--tracker-index", "0",
                        "--synthetic", "--out", out], capture_output=True, text=True, cwd=C1)
    return r


def t_eqv():
    s = setup()
    import c1_predarm_v03 as P3
    TA, X = P3.TA, P3.X
    kz, rz, gt_xy, mu, cov = TA.load_inputs(s["keys"], {"trk": s["run"]}, True, None)
    kz = dict(kz)
    it = TA.item_table(kz, rz, gt_xy, mu, cov, TA.H_PRIMARY, "v2")
    ok = it["TPP_ok"] & it["inpath"]
    U = it["TPP_D"][ok] / np.sqrt(it["TPP_V"][ok] + P3.P1.SIGMA_A ** 2)
    sc = it["s"][ok]
    mi, m, lv = TA.mlib_items(it, ok, kz)
    fj = json.load(open(s["folds"]))
    fold = np.array([int(fj["fold_of_log"][str(n)]) for n in kz["scene_names"]])
    n_eq = 0
    for f in range(5):
        cal, te = fold[sc] != f, fold[sc] == f
        t_m, _ = X.fit_hier_exact(U[cal], sc[cal], [x[cal] for x in lv], 0)
        ref = t_m[lv[0][te]]
        tabs = P3.fit_levels(U[cal], sc[cal], [x[cal] for x in lv])
        mine, _ = P3.apply_levels(tabs, [x[te] for x in lv])
        assert np.array_equal(ref, mine, equal_nan=True), "fold %d: generic noHL fit differs from fit_hier_exact" % f
        n_eq += int(te.sum())
    return {"items_compared": n_eq, "folds": 5, "equal": True}


def t_hl37():
    s = setup()
    out = {}
    for name, run in (("planted", s["planted"]), ("control", s["run"])):
        o = os.path.join(s["d"], "pred_%s.json" % name)
        r = run_v03(s["keys"], run, o)
        assert r.returncode == 0, (r.stdout + r.stderr)[-1500:]
        res = json.load(open(o))["arms"]["TPP"]["PD"]
        hl, nohl, diag = res["HL"], res["noHL"], res["noHL_on_HL_cells"]
        flag_hl = lambda rr: [c for c in rr["flagged"] + rr["family_flagged"] if c.startswith("hist")]  # noqa: E731
        out[name] = {"two_share": s["two_share"],
                     "noHL_exceed_by_hl": diag["exceed_share_by_hl"], "HL_exceed_by_hl": hl["exceed_share_by_hl"],
                     "noHL_D17_family_cells_with_hist": [c for c in nohl["cells"] if c.startswith("hist")],
                     "noHL_D17_flagged": nohl["flagged"], "noHL_on_HL_cells_flagged_hist": flag_hl(diag), "HL_flagged_hist": flag_hl(hl),
                     "H9_HL": hl["H9"], "H9_noHL": nohl["H9"], "H9_noHL_on_HL_cells": diag["H9"],
                     "HL_fallback_share_by_level": hl["fallback_share_by_level"]}
    p, c = out["planted"], out["control"]
    assert not p["noHL_D17_family_cells_with_hist"] and p["noHL_exceed_by_hl"]["hist=2"] > 0.05 + 0.02, "(a) the planted excess exists (two-state exceedance > delta + 0.02), unseen by D17's family"
    assert "hist=2" in p["noHL_on_HL_cells_flagged_hist"], "(b) the HL cells catch the noHL method's short-history excess"
    assert p["HL_exceed_by_hl"]["hist=2"] <= 0.05 + 0.02 and "hist=2" not in p["HL_flagged_hist"], "(c) the HL stratum calibrates it"
    assert not c["noHL_on_HL_cells_flagged_hist"] and not c["HL_flagged_hist"], "control: no HL cell flagged without a planted excess"
    return out


def t_hlsrc():
    s = setup()
    import c1_predarm_v03 as P3
    assert P3.HL_KEY == {"TPP": "rec_hist_stratum_trk", "TPPgt": "rec_hist_stratum_gt"}
    kz = dict(np.load(s["keys"], allow_pickle=False))
    bad = dict(kz)
    hs = bad["rec_hist_stratum_trk"].copy()
    used = bad["item_rec"][bad["item_ref_relied"] & (bad["item_h"] == P3.TA.H_PRIMARY) & bad["item_inpath"]]
    hs[used[0]] = -1
    bad["rec_hist_stratum_trk"] = hs
    kb = os.path.join(s["d"], "keys_badhl.npz")
    np.savez(kb, **bad)
    r = run_v03(kb, s["run"], os.path.join(s["d"], "o_badhl.json"))
    assert r.returncode != 0 and "fewer than 2 history states" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-600:]
    nohl = {k: v for k, v in kz.items() if k != "rec_hist_stratum_trk"}
    kn = os.path.join(s["d"], "keys_nohl.npz")
    np.savez(kn, **nohl)
    r2 = run_v03(kn, s["run"], os.path.join(s["d"], "o_nohl.json"))
    assert r2.returncode != 0, "keys without the history field must be refused"
    return {"below_2_states": "error", "missing_field": "refused"}


def t_p35():
    s = setup()
    fj = json.load(open(s["folds"]))
    names = sorted(fj["fold_of_log"])
    part = dict(fj, fold_of_log={n: f for n, f in fj["fold_of_log"].items() if n not in names[:30]})
    fp = os.path.join(s["d"], "folds_part.json")
    json.dump(part, open(fp, "w"))
    r = run_v03(s["keys"], s["run"], os.path.join(s["d"], "o_part.json"), folds=fp)
    assert r.returncode != 0 and "outside the folds" in (r.stdout + r.stderr), (r.stdout + r.stderr)[-600:]
    return {"outside_folds": "error"}


def t_dec37():
    import c1_analyse_v05 as A5
    fb = {"met": True, "missing": [], "vs": {}, "in_V_by_choice9": []}
    st = {a: {"valid": True, "shown_above": False} for a in A5.REQUIRED_ARMS}
    res = {"within_lt3d": {t: {"form_b": fb, "status": st, "form_c": None, "form_a": {}} for t in A5.TRACKERS}}
    tab = {t: {"H9": True, "H9_noHL": False, "arms": {"TPP": {}}, "population": "x"} for t in A5.TRACKERS}
    d = A5.decide(res, {"routes": [], "h9_label": "secondary"}, "smoke", {"tables": {"h9": {"ok": True, "data": tab, "checks": {}}}})
    assert d["claims_status"]["H9"] == "holds" and d["claims_status"]["H9-noHL"] == "descriptive"
    assert d["hypotheses"]["H9-noHL"]["holds_as_formula"] is False and "H9-noHL" not in d["family_S"]
    return {"H9": d["claims_status"]["H9"], "H9-noHL": "descriptive, formula False"}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v07.json")
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {"tested_files_sha256": {f: G.sha(os.path.join(C1, f)) for f in TESTED}, "python": sys.version}, True
    for name, fn in (("EQV", t_eqv), ("HL37", t_hl37), ("HLSRC", t_hlsrc), ("P35", t_p35), ("DEC37", t_dec37)):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-2000:], flush=True)
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
