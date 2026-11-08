#!/usr/bin/env python3
"""Tests for the proposed TPP arm analysis v02 (4 Nov 2026) on SYNTHETIC data only. Run in canmot310 with `python -I`.
Uses test_tpp_analyse_v01's generator (150 scenes, 18 logs, known kappa per arm) and adds: 4 development scenes,
stored step-4 mixtures (25 equal components equal to the run's V2, so the mixture moment-matches to V2 exactly),
re-seeded tracker-history runs, and an injected extreme-covariance tail.
  C1 folds: development scenes get -1; the other 146 form 5 folds of 30/29/29/29/29, deterministic.
  C2 development-scene items are excluded from every analysed set and counted.
  C3 primary hypotheses as designed (H1, H2 on PD7 / SD1_7 / PD, H3).
  C4 HK1a (iii) floors are reported for TPP_Mstar per population (K7's power rule) and do not gate H2.
  C5 tail sensitivity drops exactly the non-development common items whose V2 trace exceeds 100 m^2 in either arm.
  C6 S1: seeds with covariances x1.05 / x0.95 leave every hypothesis seed-robust; a seed whose covariance is x9
     (no longer overconfident) makes H1 not seed-robust.
  C7 S2: the pooled V2 of three identical seeds equals the primary V2 (and the S2 hypotheses equal the primary's);
     the pooled mean and covariance of two one-hot mixtures equal the analytic moment match.
  C8 end to end through main(), and the real-data guard refuses without a freeze record.
Usage: python -I test_tpp_analyse_v02.py --out <json> [--boot 300]
"""
import argparse
import json
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(1, HERE)
import tpp_analyse_v02 as A2  # noqa: E402
import tpp_common_v01 as C  # noqa: E402
import test_tpp_analyse_v01 as T1  # noqa: E402

RES = {}


def check(name, cond, info=None):
    RES[name] = {"pass": bool(cond), "info": info}
    print(("PASS " if cond else "FAIL ") + name + ("  " + json.dumps(info, default=float) if info is not None else ""), flush=True)


def extend(d, kp, runs, rng):
    """Add development scenes, step-4 mixtures, seed runs and a tail to the v01 synthetic files (rewritten in place)."""
    kz = dict(np.load(kp))
    names = list(kz["scene_names"])
    dev = np.zeros(len(names), bool)
    dev[[10, 50, 90, 130]] = True
    kz["scene_is_dev"] = dev
    np.savez(kp, **kz)
    h3 = np.nonzero(kz["rec_h"] == 3)[0]
    out = {}
    for src, p in runs.items():
        z = dict(np.load(p))
        ok3 = h3[z["status"][h3] == C.ST_OK]
        z["mix_rec"] = ok3
        z["mix_w"] = np.full((len(ok3), 25), 1.0 / 25, np.float32)
        z["mix_mu"] = np.repeat(z["v2_mu"][ok3][:, None, :], 25, 1)
        z["mix_cov"] = np.repeat(z["v2_cov"][ok3][:, None, :], 25, 1)
        np.savez(p, **z)
        out[src] = z
    seeds = {}
    for name, f in (("s104", 1.05), ("s105", 0.95), ("s_cal", 9.0)):
        z = dict(out["trk"])
        z["v2_cov"] = z["v2_cov"] * f
        z["v1_cov"] = z["v1_cov"] * f
        z["mix_cov"] = z["mix_cov"] * f
        seeds[name] = os.path.join(d, "syn_run_trk_%s.npz" % name)
        np.savez(seeds[name], **z)
    # tail: a separate primary run with 0.2 % of ok h3 rows given a huge covariance
    z = dict(out["trk"])
    ok3 = h3[z["status"][h3] == C.ST_OK]
    tail = rng.choice(ok3, size=max(3, len(ok3) // 500), replace=False)
    z["v2_cov"] = z["v2_cov"].copy()
    z["v2_cov"][tail] = np.array([150.0, 0.0, 80.0])
    tp = os.path.join(d, "syn_run_trk_tail.npz")
    np.savez(tp, **z)
    return dev, seeds, tp, tail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=300)
    a = ap.parse_args()
    t0 = time.time()
    rng = np.random.default_rng(11)
    d = tempfile.mkdtemp(prefix="tpp_syn2_")
    kp, runs, sz = T1.make_synthetic(d)
    dev, seeds, tail_path, tail_rows = extend(d, kp, runs, rng)
    kz, rz, gt_xy, trk_mu, trk_cov = A2.A1.load_inputs(kp, runs, True)
    names = [str(x) for x in kz["scene_names"]]
    f1, f2 = A2.scene_folds_v02(names, dev), A2.scene_folds_v02(names, dev)
    sizes = sorted(np.bincount(f1[f1 >= 0], minlength=5).tolist(), reverse=True)
    check("C1_folds_146_dev_excluded", np.array_equal(f1, f2) and np.all(f1[dev] == -1) and sizes == [30, 29, 29, 29, 29], {"sizes": sizes})
    P = A2.analyse_v02(kz, rz, gt_xy, trk_mu, trk_cov, "v2", a.boot)
    cnt = P["counts"]
    scen = {p: P["populations"][p]["scenes"] for p in A2.POPS}
    check("C2_dev_items_excluded", cnt["in_dev_scenes"] > 0 and max(scen.values()) <= 146 and cnt["common_ok"] < cnt["relied_items_h"] - cnt["in_dev_scenes"] + 1,
          {"counts": cnt, "scenes": scen})
    h = P["hypotheses"]
    check("C3_primary_hypotheses", h["H1_raw_TPP_overconfident"] is True and h["H2_Mstar_TPP_valid_HK1_all_pops"] is True and h["H3_gt_history_less_exceedance"] is True, h)
    fl = {p: P["populations"][p]["HK1a_iii_floor_TPP_Mstar"] for p in A2.POPS}
    ok4 = all(f is not None and isinstance(f["family_size"], int) and isinstance(f["floor_met"], bool) and "not gating" in f["role"] for f in fl.values())
    check("C4_floors_reported_not_gating", ok4 and h["H2_Mstar_TPP_valid_HK1_all_pops"] is True,
          {p: (f["evaluable_cells"], f["family_size"], f["floor_met"]) for p, f in fl.items()})
    # C5 tail
    _, rt, _, _, _ = A2.A1.load_inputs(kp, {"trk": tail_path, "gt": runs["gt"]}, True)
    PT = A2.analyse_v02(kz, rt, gt_xy, trk_mu, trk_cov, "v2", a.boot, tail_cap=A2.TAIL_TRACE_M2)
    PN = A2.analyse_v02(kz, rt, gt_xy, trk_mu, trk_cov, "v2", a.boot)
    it = A2.A1.item_table(kz, rt, gt_xy, trk_mu, trk_cov)
    keep = ~dev[it["s"]] & it["TRK_ok"] & it["TPP_ok"] & it["TPPgt_ok"]
    want = int(np.sum(keep & np.isin(it["rec"], tail_rows)))
    check("C5_tail_sensitivity", PT["counts"]["tail_dropped"] == want > 0 and PT["counts"]["common_ok"] == PN["counts"]["common_ok"] - want,
          {"dropped": PT["counts"]["tail_dropped"], "expected": want, "common_without": PT["counts"]["common_ok"], "common_with": PN["counts"]["common_ok"]})
    # C6 S1
    by = {}
    for nm in ("s104", "s105"):
        _, r1, _, _, _ = A2.A1.load_inputs(kp, {"trk": seeds[nm]}, True)
        by[nm] = A2.analyse_v02(kz, {"trk": r1["trk"], "gt": rz["gt"]}, gt_xy, trk_mu, trk_cov, "v2", a.boot)
    sr = A2.seed_robust(P, by)
    _, rc, _, _, _ = A2.A1.load_inputs(kp, {"trk": seeds["s_cal"]}, True)
    by_cal = dict(by, s_cal=A2.analyse_v02(kz, {"trk": rc["trk"], "gt": rz["gt"]}, gt_xy, trk_mu, trk_cov, "v2", a.boot))
    sr2 = A2.seed_robust(P, by_cal)
    check("C6_S1_seed_robustness", all(sr[k]["seed_robust"] for k in ("H1_raw_TPP_overconfident", "H2_Mstar_TPP_valid_HK1_all_pops", "H3_gt_history_less_exceedance"))
          and sr2["H1_raw_TPP_overconfident"]["seed_robust"] is False,
          {"robust": {k: v["seed_robust"] for k, v in sr.items() if isinstance(v, dict) and "seed_robust" in v},
           "with_calibrated_seed_H1": sr2["H1_raw_TPP_overconfident"]["by_seed"], "ranges": sr["key_number_ranges"]})
    # C7 S2
    same = [rz["trk"], rz["trk"], rz["trk"]]
    pooled = A2.pooled_run(same, len(kz["rec_k"]))
    okp = pooled["status"] == C.ST_OK
    h3ok = (kz["rec_h"] == 3) & (rz["trk"]["status"] == C.ST_OK)
    e7 = float(np.max(np.abs(pooled["v2_mu"][okp] - rz["trk"]["v2_mu"][okp])) + np.max(np.abs(pooled["v2_cov"][okp] - rz["trk"]["v2_cov"][okp])))
    PS = A2.analyse_v02(kz, {"trk": pooled, "gt": rz["gt"]}, gt_xy, trk_mu, trk_cov, "v2", a.boot)
    za = {"mix_rec": np.array([0]), "mix_w": np.eye(25, dtype=np.float32)[[0]], "mix_mu": np.zeros((1, 25, 2)),
          "mix_cov": np.tile([1.0, 0.0, 1.0], (1, 25, 1)), "status": np.array([0], np.int8)}
    zb = dict(za, mix_mu=np.tile([2.0, 0.0], (1, 25, 1)), mix_w=np.eye(25, dtype=np.float32)[[3]])
    pr = A2.pooled_run([za, zb], 1)
    analytic = np.allclose(pr["v2_mu"][0], [1.0, 0.0]) and np.allclose(pr["v2_cov"][0], [2.0, 0.0, 1.0])
    check("C7_S2_pooled_helper", okp.sum() == h3ok.sum() and e7 < 1e-9 and analytic and PS["hypotheses"] == P["hypotheses"],
          {"pooled_rows": int(okp.sum()), "max_diff": e7, "two_seed_analytic": bool(analytic)})
    # C8 main end to end and guard
    out = os.path.join(d, "syn_out_v02.json")
    sys.argv = ["tpp_analyse_v02.py", "--synthetic", "--keys", kp, "--runs", "trk=" + runs["trk"], "gt=" + runs["gt"],
                "--seed-runs", "20261104=" + seeds["s104"], "20261105=" + seeds["s105"], "--out", out, "--boot", "200"]
    A2.main()
    o = json.load(open(out))
    want_keys = {"primary_v2", "secondary_v1", "sensitivity_tail_excluded_v2", "S1_seed_robustness", "S2_seed_pooled_v2_descriptive"}
    guard = False
    sys.argv = ["tpp_analyse_v02.py", "--keys", kp, "--runs", "trk=" + runs["trk"], "--out", out + ".x"]
    try:
        A2.main()
    except AssertionError:
        guard = True
    check("C8_main_and_guard", set(o["results"]) == want_keys and guard, {"results": sorted(o["results"])})
    summ = {"tests": RES, "all_pass": all(x["pass"] for x in RES.values()), "boot": a.boot, "data": "SYNTHETIC ONLY",
            "seconds": round(time.time() - t0, 1),
            "scripts": {"tpp_analyse_v02": C.sha256_path(A2.__file__), "tpp_analyse_v01": C.sha256_path(A2.A1.__file__),
                        "test_tpp_analyse_v02": C.sha256_path(os.path.abspath(__file__))}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(summ, open(a.out, "w"), indent=1, default=float)
    print("ALL_PASS" if summ["all_pass"] else "SOME_FAIL")


if __name__ == "__main__":
    main()
