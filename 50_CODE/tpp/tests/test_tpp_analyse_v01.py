#!/usr/bin/env python3
"""Tests for the proposed TPP arm analysis (v01, 2 Nov 2026) on SYNTHETIC data only. Run in canmot310 with `python -I`.
The generator writes keys and run files in the real formats (stamped synthetic): 150 scenes, 18 logs of unequal size,
records at h = 0..3, one or two items per record, strata over car / pedestrian / large x range x axis x motion, a
predicted covariance per record and a 2-D error drawn from N(0, kappa * Sigma) with a known kappa per arm:
TRK kappa = 1 (calibrated), TPP kappa = 4 on the longitudinal axis and 9 on the lateral one (overconfident, stratum
dependent), TPPgt kappa = 2; 3 % of TPP records carry a non-ok status.
  A1 folds: 5 disjoint folds of 30 scenes, deterministic, covering the 150 scenes.
  A2 the raw (B0) pooled exceedance of each arm equals its analytic value within Monte-Carlo error.
  A3 H1 is detected for TPP (pooled lower bound > delta); TRK's raw rate is not flagged.
  A4 H2: cross-fitted M* is valid (HK1, HK1c) for TPP and for TRK; its pooled held-out rate is near delta.
  A5 H3: the paired TPP - TPPgt raw difference is positive.
  A6 non-ok records are excluded from the common item set and counted.
  A7 the ANEES ordering TPP > TPPgt > TRK; TRK's median NEES is near the chi-square(2) median.
  A8 guards: real-data mode refuses without a freeze record; synthetic mode refuses unstamped inputs; V1 runs too.
Usage: python -I test_tpp_analyse_v01.py --out <json> [--boot 2000]
"""
import argparse
import json
import math
import os
import sys
import tempfile
import time

import numpy as np
from scipy.stats import norm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tpp_analyse_v01 as A  # noqa: E402
import tpp_common_v01 as C  # noqa: E402

RES = {}


def check(name, cond, info=None):
    RES[name] = {"pass": bool(cond), "info": info}
    print(("PASS " if cond else "FAIL ") + name + ("  " + json.dumps(info, default=float) if info is not None else ""), flush=True)


KAPPA = {"TRK": (1.0, 1.0), "TPP": (4.0, 9.0), "TPPgt": (2.0, 2.0)}


def make_synthetic(d, seed=5, n_scenes=150, rec_per_scene=(40, 90), bad_share=0.03):
    rng = np.random.default_rng(seed)
    log_sizes = np.array([12, 11, 10, 10, 9, 9, 9, 8, 8, 8, 8, 8, 8, 7, 7, 7, 6, 5])
    assert log_sizes.sum() == n_scenes
    logs = np.repeat(["log%02d" % i for i in range(18)], log_sizes)
    names = ["scene-%04d" % (i * 7 + 3) for i in range(n_scenes)]
    R = {k: [] for k in ("s", "k", "h", "pair", "yaw", "sign_long", "sign_lat", "gap_long", "gap_lat", "hist_stratum_trk", "rel")}
    I = {k: [] for k in ("rec", "a", "s", "g", "r", "m", "l0", "inpath", "h", "ref_relied")}
    Sig, errs = [], {a: [] for a in KAPPA}
    n = 0
    for si in range(n_scenes):
        nr = rng.integers(*rec_per_scene)
        for p in range(nr):
            h = int(rng.integers(0, 4)) if rng.random() < 0.4 else 3
            yaw = rng.uniform(-np.pi, np.pi)
            g = int(rng.choice([0, 1, 3], p=[0.6, 0.25, 0.15]))
            r = int(rng.integers(0, 3))
            m = int(rng.choice([0, 1, 2, 3], p=[0.4, 0.4, 0.15, 0.05]))
            gaps = rng.uniform(-1, 12, 2)
            if not (gaps > 0).any():
                gaps[rng.integers(0, 2)] = rng.uniform(0.1, 12)
            rel = int(np.argmax(gaps))
            sg = rng.choice([-1.0, 1.0], 2)
            R["s"].append(si); R["k"].append(int(rng.integers(1, 38))); R["h"].append(h); R["pair"].append(p + 1)
            R["yaw"].append(yaw); R["sign_long"].append(sg[0]); R["sign_lat"].append(sg[1])
            R["gap_long"].append(gaps[0]); R["gap_lat"].append(gaps[1]); R["hist_stratum_trk"].append(int(rng.integers(0, 3))); R["rel"].append(rel)
            ax = np.array([[math.cos(yaw), math.sin(yaw)], [-math.sin(yaw), math.cos(yaw)]])
            sl, st = rng.uniform(0.3, 2.0), rng.uniform(0.2, 1.2)
            S = ax.T @ np.diag([sl ** 2, st ** 2]) @ ax
            Sig.append(C.cov3(S))
            for arm, (kl, kt) in KAPPA.items():
                Sk = ax.T @ np.diag([kl * sl ** 2, kt * st ** 2]) @ ax
                errs[arm].append(rng.multivariate_normal(np.zeros(2), Sk))
            for a_ in range(2):
                if gaps[a_] > 0:
                    I["rec"].append(n); I["a"].append(a_); I["s"].append(si); I["g"].append(g); I["r"].append(r); I["m"].append(m)
                    I["l0"].append(((g * 3 + r) * 2 + a_) * 4 + m); I["inpath"].append(bool(rng.random() < 0.3)); I["h"].append(h)
                    I["ref_relied"].append(a_ == rel)
            n += 1
    Sig = np.array(Sig)
    gt = rng.normal(size=(n, 2)) * 50 + 500
    kz = {"rec_" + k: np.array(v) for k, v in R.items()}
    kz.update({"item_" + k: np.array(v) for k, v in I.items()})
    kz.update({"scene_names": np.array(names), "scene_logs": logs, "stamp": np.array(A.SYN_STAMP), "syn_gt_xy": gt,
               "syn_trk_mu": gt - np.array(errs["TRK"]), "syn_trk_cov": Sig, "cache_dir": np.array("none")})
    kp = os.path.join(d, "syn_keys.npz")
    np.savez(kp, **kz)
    runs = {}
    for src, arm in (("trk", "TPP"), ("gt", "TPPgt")):
        mu = gt - np.array(errs[arm])
        status = np.zeros(n, np.int8)
        if arm == "TPP":
            bad = rng.random(n) < bad_share
            status[bad] = C.ST_SHORT_HISTORY
            mu = np.where(bad[:, None], np.nan, mu)
        z = {"rec_index": np.arange(n), "rec_pair": kz["rec_pair"], "rec_s": kz["rec_s"], "status": status, "v2_mu": mu, "v2_cov": Sig,
             "v1_mu": mu, "v1_cov": Sig, "stamp": np.array(A.SYN_STAMP)}
        runs[src] = os.path.join(d, "syn_run_%s.npz" % src)
        np.savez(runs[src], **z)
    return kp, runs, {"items": len(I["rec"]), "records": n}


def analytic_raw(kz, arm, sel_items):
    """Expected raw exceedance per item: P(a*.e > z sd) with a*.e ~ N(0, kappa_a a' S a), sd^2 = a' S a + sigma_a^2."""
    j = kz["item_rec"][sel_items]
    a = kz["item_a"][sel_items]
    S = kz["syn_trk_cov"][j]
    yaw = kz["rec_yaw"][j]
    ax = np.where(a[:, None] == 0, np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1))
    v = ax[:, 0] ** 2 * S[:, 0] + 2 * ax[:, 0] * ax[:, 1] * S[:, 1] + ax[:, 1] ** 2 * S[:, 2]
    kap = np.where(a == 0, KAPPA[arm][0], KAPPA[arm][1])
    p = norm.sf(A.Z * np.sqrt(v + A.SIGMA_A ** 2) / np.sqrt(kap * v))
    s = kz["item_s"][sel_items]
    per = np.bincount(s, weights=p, minlength=150) / np.maximum(np.bincount(s, minlength=150), 1)
    return float(np.mean(per[np.bincount(s, minlength=150) > 0]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=A.B_BOOT)
    a = ap.parse_args()
    t0 = time.time()
    d = tempfile.mkdtemp(prefix="tpp_syn_")
    kp, runs, sz = make_synthetic(d)
    kz, rz, gt_xy, trk_mu, trk_cov = A.load_inputs(kp, runs, True)
    names = [str(x) for x in kz["scene_names"]]
    f1, f2 = A.scene_folds(names), A.scene_folds(names)
    cnt = np.bincount(f1, minlength=5)
    check("A1_folds_5x30_deterministic", np.array_equal(f1, f2) and list(cnt) == [30] * 5,
          {"fold_sizes": cnt.tolist(), "fold0_first": sorted(np.array(names)[f1 == 0].tolist())[:3]})
    res = A.analyse(kz, rz, gt_xy, trk_mu, trk_cov, "v2", A.H_PRIMARY, a.boot)
    v = res["populations"]["PD7"]["validity"]
    it = A.item_table(kz, rz, gt_xy, trk_mu, trk_cov)
    common = it["TRK_ok"] & it["TPP_ok"] & it["TPPgt_ok"]
    sel_items = np.nonzero(kz["item_ref_relied"] & (kz["item_h"] == A.H_PRIMARY))[0][common]
    want = {arm: analytic_raw(kz, arm, sel_items) for arm in KAPPA}
    got = {arm: v[arm + "_B0"]["pooled_E"] for arm in KAPPA}
    check("A2_raw_exceedance_matches_analytic", all(abs(got[k] - want[k]) < 0.012 for k in KAPPA), {"got": got, "analytic": want})
    check("A3_H1_detected_TRK_not_flagged", res["hypotheses"]["H1_raw_TPP_overconfident"] is True and v["TRK_B0"]["pooled_not_flagged"],
          {"TPP_B0_lb": v["TPP_B0"]["pooled_lb"], "TRK_B0": v["TRK_B0"]["pooled_E"]})
    ms = {arm: (v[arm + "_Mstar"]["HK1"], v[arm + "_Mstar"]["HK1c_pooled_ub_le_delta_plus_0.03"], v[arm + "_Mstar"]["pooled_E"]) for arm in ("TPP", "TRK")}
    check("A4_H2_crossfit_Mstar_valid", all(x[0] and x[1] and 0.025 <= x[2] <= 0.06 for x in ms.values()) and res["hypotheses"]["H2_Mstar_TPP_valid_HK1"],
          {"Mstar(HK1, HK1c, pooled E)": ms, "TPP_B4": v["TPP_B4"]["pooled_E"], "TPP_B3": v["TPP_B3"]["pooled_E"],
           "margin_m": {k: v[k]["mean_margin_m"] for k in ("TPP_B0", "TPP_Mstar", "TRK_Mstar", "TPP_B3")}})
    check("A5_H3_paired_positive", res["hypotheses"]["H3_gt_history_less_exceedance"] is True)
    nbad = int(np.sum(~it["TPP_ok"]))
    check("A6_non_ok_excluded", res["counts"]["common_ok"] == int(common.sum()) and nbad > 0 and res["counts"]["TPP_ok"] == len(common) - nbad,
          res["counts"])
    a6 = res["A6"]
    check("A7_A6_ordering", a6["TPP"]["ANEES_scene"] > a6["TPPgt"]["ANEES_scene"] > a6["TRK"]["ANEES_scene"]
          and abs(a6["TRK"]["median_NEES"] - 1.386) < 0.15, {k: (a6[k]["ANEES_scene"], a6[k]["median_NEES"], a6[k]["coverage"]["0.95"]) for k in a6})
    # guards and V1 via main()
    out = os.path.join(d, "syn_out.json")
    ok_guard = True
    for argv in (["--keys", kp, "--runs", "trk=" + runs["trk"], "--out", out],                      # real mode, no freeze record
                 ["--keys", kp, "--runs", "trk=" + runs["trk"], "--out", out, "--plan", kp, "--freeze-record", kp + ".json"]):
        if argv[-1].endswith(".json"):
            json.dump({"analysis_sha256": "0" * 64, "plan_sha256": C.sha256_path(kp)}, open(kp + ".json", "w"))
        sys.argv = ["tpp_analyse_v01.py"] + argv
        try:
            A.main()
            ok_guard = False
        except AssertionError:
            pass
    zr = dict(np.load(kp))
    zr.pop("stamp")
    np.savez(os.path.join(d, "unstamped.npz"), **zr)
    sys.argv = ["tpp_analyse_v01.py", "--synthetic", "--keys", os.path.join(d, "unstamped.npz"), "--runs", "trk=" + runs["trk"], "--out", out]
    try:
        A.main()
        ok_guard = False
    except AssertionError:
        pass
    sys.argv = ["tpp_analyse_v01.py", "--synthetic", "--keys", kp, "--runs", "trk=" + runs["trk"], "gt=" + runs["gt"], "--out", out,
                "--boot", "300"]
    A.main()
    o = json.load(open(out))
    check("A8_guards_and_v1", ok_guard and set(o["results"]) == {"v1", "v2"}, {"v1_hypotheses": o["results"]["v1"]["hypotheses"]})
    summ = {"tests": RES, "all_pass": all(x["pass"] for x in RES.values()), "synthetic_size": sz, "boot": a.boot,
            "seconds": round(time.time() - t0, 1), "data": "SYNTHETIC ONLY",
            "scripts": {"tpp_analyse_v01": C.sha256_path(A.__file__), "test_tpp_analyse_v01": C.sha256_path(os.path.abspath(__file__))}}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(summ, open(a.out, "w"), indent=1, default=float)
    print("ALL_PASS" if summ["all_pass"] else "SOME_FAIL")


if __name__ == "__main__":
    main()
