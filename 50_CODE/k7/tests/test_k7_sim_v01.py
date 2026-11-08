#!/usr/bin/env python3
"""Tests of k7_sim_v01 against the frozen k6_sim_v02 (Claude line, 1 Nov 2026). Development scenes only.
  T-K7-1  with the K6 fits (no '_ip' keys), decision mode reproduces k6_sim_v02 exactly for every arm on the 10 development
          scenes (summaries and in-loop counts), for both trackers;
  T-K7-2  with '_ip' thresholds that repeat the L0 thresholds for both in-path values, Mstar and B6 reproduce k6_sim_v02;
  T-K7-3  margins(): an in-path track takes the threshold at L0 + 96, a not-in-path track the one at L0;
  T-K7-4  closed loop (delays 0 and 2 s, arms Mstar and B6) with the K6 fits reproduces k6_sim_v02 on 3 development scenes;
  T-K7-5  the generator reproduces k7_sim_v01.py from k6_sim_v02.py;
  T-K7-6  distinct _ip thresholds take effect in plan_step: raising the in-path half (or the not-in-path half) changes
          the decisions, and in-path records then show no exceedance (R12 m6).
Usage: python -B test_k7_sim_v01.py <out json>
"""
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile

import numpy as np

K7 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W_ROOT = os.path.dirname(os.path.dirname(K7))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, K7)
import k6_sim_v02 as S6  # noqa: E402
import k7_sim_v01 as S7  # noqa: E402

DEV = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077", "scene-1094", "scene-1100")
STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        h.update(f.read())
    return h.hexdigest()


def scene_path(tag, scene):
    for sp in ("train", "val"):
        p = os.path.join(W_ROOT, "30_DATA", "k6", "cache_v02_%s_%s" % (tag, sp), scene + ".npz")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(scene)


def fits_for(F, scene):
    f = F["fold_of_scene"][scene]
    return [F["fits"][str(f)][h] for h in STEPS]


def same(a, b):
    return json.dumps(a, sort_keys=True, default=float) == json.dumps(b, sort_keys=True, default=float)


def main():
    res = {}
    ok_all = True
    for tag in ("t1", "t3"):
        F = json.load(open(os.path.join(W_ROOT, "60_RESULTS", "k6_items_v01", "k6_fits_%s_v01.json" % tag)))
        bad1, bad2, n = [], [], 0
        for scene in DEV:
            p = scene_path(tag, scene)
            sc6, sc7 = S6.Scene(p), S7.Scene(p)
            fits = fits_for(F, scene)
            fits_ip = copy.deepcopy(fits)
            for fh in fits_ip:
                fh["Mstar_ip"] = list(fh["Mstar"]) + list(fh["Mstar"])
                fh["B6_ip"] = list(fh["B6"]) + list(fh["B6"])
            for arm in [x for x in S6.ARMS if x != "LOG"]:
                fa = fits if arm not in ("Z0", "B0") else None
                o6, c6 = S6.run_decisions(sc6, arm, fa)
                o7, c7 = S7.run_decisions(sc7, arm, fa)
                n += 1
                if not (same(o6, o7) and same(c6, c7)):
                    bad1.append((scene, arm))
                if arm in ("Mstar", "B6"):
                    o7b, c7b = S7.run_decisions(sc7, arm, fits_ip)
                    if not (same(o6, o7b) and same(c6, c7b)):
                        bad2.append((scene, arm))
        res["T-K7-1_%s" % tag] = {"pass": not bad1, "compared": n, "mismatch": bad1}
        res["T-K7-2_%s" % tag] = {"pass": not bad2, "mismatch": bad2}
        ok_all &= not bad1 and not bad2
    # T-K7-3
    J = 3
    g = np.zeros(J, int)
    r = np.zeros((J, 8), int)
    sd = np.ones((J, 8, 2))
    l0 = np.tile(np.array([[5, 7]]), (J, 8, 1))
    inp = np.array([False, True, False])
    thr = np.arange(192, dtype=float)
    fits = [{"Mstar": list(range(96)), "Mstar_ip": thr.tolist()} for _ in range(8)]
    mg = S7.margins("Mstar", fits, g, r, sd, l0, inp)
    exp = np.where(inp[:, None, None], l0 + 96, l0).astype(float)
    t3 = bool(np.array_equal(mg, exp))
    res["T-K7-3"] = {"pass": t3}
    ok_all &= t3
    # T-K7-4
    F = json.load(open(os.path.join(W_ROOT, "60_RESULTS", "k6_items_v01", "k6_fits_t1_v01.json")))
    bad4 = []
    for scene in DEV[:3]:
        p = scene_path("t1", scene)
        sc6, sc7 = S6.Scene(p), S7.Scene(p)
        fits = fits_for(F, scene)
        for arm in ("Mstar", "B6"):
            for d in (0, 4):
                o6, c6 = S6.run_episode(sc6, arm, fits, d)
                o7, c7 = S7.run_episode(sc7, arm, fits, d)
                if not (same(o6, o7) and same(c6, c7)):
                    bad4.append((scene, arm, d))
    res["T-K7-4"] = {"pass": not bad4, "mismatch": bad4}
    ok_all &= not bad4
    # T-K7-6 (R12 m6): distinct '_ip' thresholds take effect in plan_step. With the in-path half of Mstar_ip set to 100 and the
    # not-in-path half equal to Mstar, the decisions must differ from K6's on scenes with in-path tracks and the in-path records
    # must see the larger margins (no in-path exceedance can remain); raising only the not-in-path half must change the
    # not-in-path records instead.
    F = json.load(open(os.path.join(W_ROOT, "60_RESULTS", "k6_items_v01", "k6_fits_t1_v01.json")))
    changed_ip, changed_nip, exc_ip_big = 0, 0, 0
    for scene in DEV[:5]:
        p = scene_path("t1", scene)
        sc7 = S7.Scene(p)
        fits = fits_for(F, scene)
        o_base, c_base = S7.run_decisions(sc7, "Mstar", fits)
        f_ip = copy.deepcopy(fits)
        f_nip = copy.deepcopy(fits)
        for a_, b_ in zip(f_ip, f_nip):
            a_["Mstar_ip"] = list(a_["Mstar"]) + [100.0] * 96
            b_["Mstar_ip"] = [100.0] * 96 + list(b_["Mstar"])
        o_ip, c_ip = S7.run_decisions(sc7, "Mstar", f_ip)
        o_nip, c_nip = S7.run_decisions(sc7, "Mstar", f_nip)
        changed_ip += int(not (same(o_base, o_ip) and same(c_base, c_ip)))
        changed_nip += int(not (same(o_base, o_nip) and same(c_base, c_nip)))
        for cell, (n, x) in c_ip.items():
            ob, inp, enf, sat, gb, rel, h, l0 = S7.decode_cell(cell)
            if inp == 1 and h < S7.CC_STEPS:
                exc_ip_big += x
    t6 = changed_ip >= 1 and changed_nip >= 1 and exc_ip_big == 0
    res["T-K7-6"] = {"pass": bool(t6), "scenes_changed_by_inpath_half": changed_ip, "scenes_changed_by_notinpath_half": changed_nip,
                     "inpath_exceedances_with_margin_100sd": int(exc_ip_big)}
    ok_all &= t6
    # T-K7-5
    with tempfile.TemporaryDirectory() as tmp:
        os.makedirs(os.path.join(tmp, "k7", "tests"))
        os.makedirs(os.path.join(tmp, "k6"))
        shutil.copy(os.path.join(W_ROOT, "50_CODE", "k6", "k6_sim_v02.py"), os.path.join(tmp, "k6"))
        shutil.copy(os.path.join(K7, "tests", "make_k7_sim_v01.py"), os.path.join(tmp, "k7", "tests"))
        subprocess.run([sys.executable, "-B", os.path.join(tmp, "k7", "tests", "make_k7_sim_v01.py")], check=True, capture_output=True)
        t5 = sha(os.path.join(tmp, "k7", "k7_sim_v01.py")) == sha(os.path.join(K7, "k7_sim_v01.py"))
    res["T-K7-5"] = {"pass": bool(t5)}
    ok_all &= t5
    res["k6_sim_sha256"] = sha(S6.__file__)
    res["k7_sim_sha256"] = sha(S7.__file__)
    json.dump(res, open(sys.argv[1], "w"), indent=1)
    print(json.dumps(res, indent=1))
    print("ALL_PASS" if ok_all else "SOME_FAIL")


if __name__ == "__main__":
    main()
