#!/usr/bin/env python3
"""Tests of the C1 code (Claude line, test_c1_v01, 2 Nov 2026). Synthetic data, nuScenes development data and M*'s K7 items only;
nothing reads an AV2 outcome. One process.
  C9   Choice 9 (E13): a comparator failing only the SD1_7 floor stays in V_t, is logged, raises |V_t| (the Bonferroni level) and must
       be beaten (Form B fails when M* does not beat it); a comparator with a flagged cell is removed. arm_status equals
       k8_analyse_v04.form_valid on every planted entry.
  E15  (a) a constructed cell whose CRC bound is exactly 1/20 gives one threshold under 200 scene permutations, equal to the exact
       answer (the float rule's answers over the same permutations are reported); (b) nuScenes T3, fold 4, h2s, from M*'s own K7 v01 items: the exact
       split fit gives 0.38665 in L0 74 (the exact answer) and equals k7_fits in every other entry, in both scene orders.
  H1   Form B pass; fail by a flagged M* cell; fail by M* not beating a valid comparator; fail by a floor (M* "floor not met").
  H2   Form C with c as a parameter: c = 0.03 fails and c = 0.04 passes on the same planted case.
  H3   the joint rule: pass; fail by M*Jx's UB above delta + 0.03; fail by not beating a joint-valid comparator.
  H10  pass; fail by non-inferiority; fail when B6 is not flagged; fail when M* is flagged in B6's only failing cell.
  H6a/H6b/H7  on planted m_lib_v04 summaries, pass and fail.   H8  X2's FAILS rule, pass and fail.   H9  no-flag with the floor of 6.
  HOLM the gate (H1 failed: every family-S claim labelled supportive), step-down on known p-values, a failed validity gate.
  SRC  source heterogeneity: a planted infeasibility difference between sources is resolved; none is resolved when absent.
  FOLD 375 ids -> 5 x 75, deterministic, seed-dependent, every id once; sha256 sidecar.
  GEN  tests/make_c1_run_v01.py reproduces c1_run_v01.py; c1_run_v01 --standin --dry-run on the nuScenes caches reads only manifests.
Usage (from 50_CODE/c1_av2): python -B tests/test_c1_v01.py <out.json>
"""
import itertools
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
import c1_analyse_v01 as CA  # noqa: E402
import c1_crc_exact_v01 as X  # noqa: E402
import c1_folds_v01 as F  # noqa: E402

K, A, M = CA.K, CA.A, CA.M
OUT = os.path.join(W, "70_TESTS", "c1_v01", "tests")
PY = os.path.join(W, "50_CODE", "env", "canmot310", "Scripts", "python.exe")


def entry(flagged=(), fam_flag=(), fam_size=(10, 10, 3), pooled_flag=False, hk1c=True, evaluable=(20, 12, 5), pooled_none=False):
    """A k8 validity_by_arm entry (the fields arm_status and form_valid read)."""
    pops = {}
    for k_, p in enumerate(CA.POPS):
        pooled = None if pooled_none else {"E": 0.04, "lb": 0.03, "ub": 0.06, "flagged": bool(pooled_flag and k_ == 0),
                                            "HK1c_ub_le_delta_plus_0.03": bool(hk1c or k_ != 0), "q": 2.0}
        pops[p] = {"evaluable": evaluable[k_], "flagged": list(flagged) if k_ == 0 else [], "pooled": pooled,
                   "family_size": fam_size[k_], "family_flagged": list(fam_flag) if k_ == 0 else []}
    hk1a = all((not pops[p]["flagged"]) and pops[p]["evaluable"] >= 1 and not pops[p]["family_flagged"]
               and (pops[p]["family_size"] >= 6 if p in CA.FLOOR_POPS else True) for p in CA.POPS)
    hk1b = all(pops[p]["pooled"] is not None and not pops[p]["pooled"]["flagged"] for p in CA.POPS)
    return {"pops": pops, "HK1a": hk1a, "HK1b": hk1b, "HK1": hk1a and hk1b}


def weights(n_logs=80, B=2000, seed=1):
    rng = np.random.default_rng(seed)
    return rng.multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=B).astype(float)


def rates(rng, means, n=80, sd=0.05):
    return {a: np.clip(m + sd * rng.standard_normal(n), 0, 1) for a, m in means.items()}


# ---------------------------------------------------------------- tests

def t_c9():
    rng = np.random.default_rng(2)
    Ws = weights()
    st = {"Mstar": CA.arm_status(entry()), "B3": CA.arm_status(entry(fam_size=(10, 4, 3))),          # floor only (SD1_7 family 4)
          "B4": CA.arm_status(entry(flagged=["car|long|static"])), "B0": CA.arm_status(entry(pooled_flag=True)),
          "B1": CA.arm_status(entry(hk1c=False)), "B6": CA.arm_status(entry(fam_flag=["ped|lat|new"])), "B9": CA.arm_status(entry()),
          "RETUNED": CA.arm_status(entry(fam_size=(3, 2, 0), evaluable=(20, 12, 0)))}                  # floors only, PD empty
    out = {"floor_only": {a: s["floor_only"] for a, s in st.items()}}
    for a, e in (("Mstar", entry()), ("B3", entry(fam_size=(10, 4, 3))), ("B4", entry(flagged=["x"])), ("B1", entry(hk1c=False))):
        assert CA.arm_status(e)["valid"] == K.form_valid(e), "arm_status differs from form_valid: " + a
    r = rates(rng, {"Mstar": 0.10, "B3": 0.80, "B4": 0.20, "B0": 0.3, "B1": 0.3, "B6": 0.15, "B9": 0.4, "RETUNED": 0.5})
    fb = CA.form_b(st, r, Ws)
    assert set(fb["V"]) == {"B3", "B9", "RETUNED"} and set(fb["in_V_by_choice9"]) == {"B3", "RETUNED"}, fb["V"]
    assert set(fb["removed_shown_above"]) == {"B4", "B0", "B1", "B6"} and abs(fb["level"] - (1 - 0.05 / 3)) < 1e-12 and fb["met"]
    r2 = dict(r, B3=np.clip(r["Mstar"] - 0.05, 0, 1))                                                    # the floor-only comparator wins
    fb2 = CA.form_b(st, r2, Ws)
    assert not fb2["met"] and not fb2["vs"]["B3"]["lower"], "a floor-only comparator that M* does not beat must fail Form B"
    out.update({"V": fb["V"], "by_choice9": fb["in_V_by_choice9"], "met": fb["met"], "met_when_floor_only_wins": fb2["met"]})
    return out


def t_e15():
    out = {}
    rng = np.random.default_rng(3)
    # 59 scenes; at c = 0.5 six scenes have losses 1/2, 1/3, 1/6, 1/2, 1/3, 1/6 (sum 2), the rest 0, so the bound is
    # (2 + 1) / 60 = 1/20 exactly; the float sum of the fractions depends on their order
    n = 59
    sizes = [2, 3, 6, 2, 3, 6] + [3] * (n - 6)
    s = np.repeat(np.arange(n), sizes)
    U = np.full(len(s), 0.5)
    for sc in range(6):
        U[np.flatnonzero(s == sc)[0]] = 5.0
    ans = set()
    fl = set()
    for _ in range(200):
        perm = rng.permutation(n)
        ans.add(X.crc_threshold_exact(U, perm[s]))
        fl.add(M.L.crc_threshold(U, perm[s]))
    b, nn = X.bound_exact(U, s, 0.5)
    assert b == __import__("fractions").Fraction(1, 20) and len(ans) == 1, (b, ans)
    out["tie"] = {"exact_bound": str(b), "exact_threshold": sorted(ans), "float_thresholds_over_permutations": sorted(fl)}
    # nuScenes T3 fold 4 h2s from M*'s own K7 v01 items
    fits = json.load(open(os.path.join(W, "60_RESULTS", "k7_fits_v01", "k7_fits_t3_v01.json")))
    z = np.load(os.path.join(W, "30_DATA", "k7", "k7_items_t3_v01.npz"))
    names = [str(x) for x in z["scene_names"]]
    it = {k[5:]: z[k] for k in z.files if k.startswith("item_")}
    fold = np.array([fits["fold_of_scene"][n_] for n_ in names], int)
    lv = M.levels(it, it["m"])
    U = it["D"] / it["sd"]
    sel = (it["h"] == 3) & (fold[it["s"]] != 4)
    ref = np.asarray(fits["fits"]["4"]["h2s"]["Mstar_ip"], float)
    res = {}
    for order_name, sidx in (("k7_order", it["s"]), ("sorted_names", np.array([sorted(names).index(n_) for n_ in names])[it["s"]])):
        thr, _ = X.split_fit_exact(U[sel], sidx[sel], [x[sel] for x in lv], it["inpath"][sel].astype(int), 0)
        diff = np.flatnonzero(thr != ref)
        res[order_name] = {"differing_entries": diff.tolist(), "entry74": float(thr[74])}
        assert diff.tolist() == [74] and abs(thr[74] - 0.38664953418894527) < 1e-15, res
    out["nuscenes_t3_fold4_h2s"] = res
    return out


def t_h1():
    rng = np.random.default_rng(4)
    Ws = weights()
    base = {"B0": entry(pooled_flag=True), "B1": entry(flagged=["c"]), "B3": entry(), "B4": entry(flagged=["c"]), "B6": entry(flagged=["c"]),
            "B9": entry(flagged=["c"]), "RETUNED": entry(flagged=["c"])}
    r = rates(rng, {"Mstar": 0.10, "B3": 0.8, "B0": 0.3, "B1": 0.3, "B4": 0.2, "B6": 0.15, "B9": 0.4, "RETUNED": 0.4})
    cases = {"pass": (entry(), r, True), "Mstar_flagged_cell": (entry(flagged=["car|lat|new"]), r, False),
             "not_beating_valid_B3": (entry(), dict(r, B3=np.clip(r["Mstar"] - 0.02, 0, 1)), False),
             "Mstar_floor": (entry(fam_size=(10, 5, 3)), r, False)}
    out = {}
    for name, (em, rr, expect) in cases.items():
        st = {a: CA.arm_status(e) for a, e in dict(base, Mstar=em).items()}
        fb = CA.form_b(st, rr, Ws)
        assert fb["met"] == expect, name
        out[name] = {"met": fb["met"], "V": fb["V"], "valid_M": fb["valid_method"]}
    st = {a: CA.arm_status(e) for a, e in dict(base, Mstar=entry(fam_size=(10, 5, 3))).items()}
    assert st["Mstar"]["floor_only"], "a floor-only M* must read 'floor not met'"
    return out


def t_h2():
    rng = np.random.default_rng(5)
    Ws = weights()
    r = {"Mstar": np.clip(0.235 + 0.01 * rng.standard_normal(80), 0, 1), "B4": np.clip(0.20 + 0.01 * rng.standard_normal(80), 0, 1)}
    c3, c4 = CA.form_c(r, Ws, 0.03), CA.form_c(r, Ws, 0.04)
    assert (not c3["met"]) and c4["met"], (c3["ub"], c4["ub"])
    return {"ub": c3["ub"], "met_c0.03": c3["met"], "met_c0.04": c4["met"], "p_c0.03": c3["p"], "p_c0.04": c4["p"]}


def jv(E, lb, ub, flagged=False):
    return {"pops": {p: {"E": E, "lb_one_sided_0.95": lb, "ub_one_sided_0.95": ub, "flagged": flagged,
                         "ub_le_delta_plus_0.03": ub <= 0.08, "evaluable": True} for p in CA.POPS}}


def t_h3():
    rng = np.random.default_rng(6)
    Ws = weights()
    J0 = {"MstarJx": jv(0.045, 0.035, 0.055), "Mstar": jv(0.35, 0.32, 0.38, True), "B3": jv(0.03, 0.02, 0.04), "B0": jv(0.2, 0.18, 0.22, True),
          "B1": jv(0.15, 0.13, 0.17, True), "B4": jv(0.37, 0.34, 0.4, True), "B6": jv(0.33, 0.3, 0.36, True), "B9": jv(0.13, 0.11, 0.15, True),
          "RETUNED": jv(0.2, 0.18, 0.22, True)}
    r = rates(rng, {"MstarJx": 0.45, "Mstar": 0.11, "B3": 0.87, "B0": 0.3, "B1": 0.39, "B4": 0.2, "B6": 0.18, "B9": 0.45, "RETUNED": 0.34})
    out = {}
    for name, (jj, rr, expect) in {"pass": (J0, r, True), "MstarJx_ub_above": (dict(J0, MstarJx=jv(0.07, 0.06, 0.09)), r, False),
                                   "not_beating_B3": (J0, dict(r, B3=np.clip(r["MstarJx"] - 0.05, 0, 1)), False)}.items():
        js = {a: CA.joint_status(v) for a, v in jj.items()}
        h = CA.joint_b(js, rr, Ws)
        assert h["met"] == expect and h["VJ"] == ["B3"], (name, h["VJ"])
        out[name] = {"met": h["met"], "VJ": h["VJ"]}
    return out


def h10_case(rng, b6_bad=True, m_bad=False, ni_ok=True, n=80, B=2000):
    cells = [("c%d" % j, [j]) for j in range(4)]
    ests = {"Mstar": np.array([0.04, 0.045, 0.05, 0.03]), "B6": np.array([0.04, 0.12 if b6_bad else 0.05, 0.05, 0.03])}
    if m_bad:
        ests["Mstar"][1] = 0.11
    boots = {a: e[None, :] + 0.008 * rng.standard_normal((B, 4)) for a, e in ests.items()}
    evs = {a: np.ones(4, bool) for a in ests}
    sig = {a: [cells[j][0] for j in np.flatnonzero(A.flag(ests[a], boots[a], np.arange(4), 0.95)[3])] for a in ests}
    r = rates(rng, {"Mstar": 0.16, "B6": 0.165 if ni_ok else 0.10}, n=n, sd=0.01)
    return CA.h10_rule(cells, ests, boots, evs, sig["B6"], sig["Mstar"], r, weights(n, B, 7))


def t_h10():
    rng = np.random.default_rng(8)
    out = {}
    for name, kw, expect in (("pass", {}, True), ("ni_fails", {"ni_ok": False}, False), ("b6_not_flagged", {"b6_bad": False}, False),
                             ("mstar_flagged_there", {"m_bad": True}, False)):
        h = h10_case(rng, **kw)
        assert h["met"] == expect, (name, h["cells_failing_B6"], h["noninferiority"]["ub"])
        out[name] = {"met": h["met"], "cells": h["cells_failing_B6"], "p": h["p"], "ni_ub": h["noninferiority"]["ub"]}
    return out


def msum(flag_m=(), flag_b4=(), pos=("c1",), pooled_sig=False):
    cells = ["c0", "c1", "c2"]
    meth = lambda fl: {"any_sig_under": bool(fl), "sig_under_cells": list(fl),  # noqa: E731
                       "cells": {c: {"sig_under": c in fl, "E_scene": 0.04, "lb_sim": 0.03, "ub_sim": 0.06, "boot_bias": 0.0} for c in cells}}
    st = {"methods": {"Mstar": meth(flag_m), "B4": meth(flag_b4)}, "paired": {"B4-Mstar": {"cells": {c: {"positive": c in pos} for c in cells}}}}
    allc = {"methods": {"Mstar": {"cells": {"all val items": {"E_scene": 0.04, "lb_sim": 0.06 if pooled_sig else 0.03, "ub_sim": 0.06, "boot_bias": 0.0,
                                                               "sig_under": pooled_sig}}}}}
    return {"E1": {"fixed": st, "refit": st}, "E2": {"cells": st, "all": allc}, "H6b_p": 0.01}


def t_h6_h7():
    out = {}
    for name, ms, e in (("pass", msum(flag_b4=("c1",)), (True, True, True)), ("Mstar_flagged", msum(flag_m=("c2",), flag_b4=("c1",)), (False, True, False)),
                        ("B4_not_failing", msum(), (True, False, True)), ("pooled_flagged", msum(flag_b4=("c1",), pooled_sig=True), (True, True, False))):
        h6, h7 = CA.h6_rules(ms), CA.h7_rule(ms)
        got = (h6["H6a"], h6["H6b"], h7["H7"])
        assert got == e, (name, got)
        out[name] = got
    return out


def t_h8():
    rng = np.random.default_rng(9)
    out = {}
    cells = ["car|lat|<20", "car|lat|20-40", "car|long|<20", "car|long|20-40"]
    for name, e0, truth, expect in (("pass", 0.05, 0.12, True), ("E0_high", 0.20, 0.12, False), ("truth_low", 0.05, 0.04, False)):
        est = np.array([0.15, 0.06, 0.04, 0.04])
        d = {"cells": cells, "target_cells": cells[:2], "est_B0": est, "boot_B0": est + 0.01 * rng.standard_normal((2000, 4)),
             "E0": [e0, 0.05, 0.05, 0.05], "est_truth": np.array([truth, 0.05, 0.04, 0.04]),
             "boot_truth": np.array([truth, 0.05, 0.04, 0.04]) + 0.01 * rng.standard_normal((2000, 4))}
        h = CA.h8_rule(d)
        assert h["H8"] == expect, name
        out[name] = h["H8"]
    return out


def t_h9():
    rng = np.random.default_rng(10)
    out = {}
    for name, n_logs, bad, expect in (("pass", 300, None, True), ("flagged_cell", 300, 2, False), ("floor_fails", 45, None, False)):
        nc = 8
        N = rng.integers(20, 60, (n_logs, nc)).astype(float)
        p = np.full(nc, 0.02)
        if bad is not None:
            p[bad] = 0.25
        Xm = rng.binomial(N.astype(int), p).astype(float)
        scene_of_ep = np.array(["s%d" % i for i in range(n_logs)])
        log_of_ep = np.arange(n_logs)
        W = weights(n_logs, 2000, 11)
        h = CA.h9_rule(N, Xm, [("k%d" % j, [j]) for j in range(nc)], scene_of_ep, log_of_ep, W, [20261111, 0, 9])
        assert h["H9"] == expect, (name, h)
        out[name] = {k: h[k] for k in ("H9", "family_size", "flagged", "pooled_flagged")}
    return out


def t_holm():
    claims = {"H2": {"p": 0.001, "gate_ok": True}, "H3": {"p": 0.004, "gate_ok": True}, "H4": {"p": 0.03, "gate_ok": False},
              "H6b": {"p": 0.012, "gate_ok": True}, "H10": {"p": 0.2, "gate_ok": True}}
    g = CA.holm(claims, 0.05, gate=True)
    assert g["H2"]["rejected"] and g["H3"]["rejected"] and g["H6b"]["rejected"] and not g["H10"]["rejected"]
    assert g["H4"]["label"].startswith("not confirmed (validity gate")
    assert abs(g["H2"]["holm_level"] - 0.05 / 4) < 1e-12 and abs(g["H6b"]["holm_level"] - 0.05 / 2) < 1e-12
    ng = CA.holm(claims, 0.05, gate=False)
    assert all(v["label"] == CA.GATE_NOTE and v["rejected"] is None for v in ng.values())
    return {"gate_open": {c: v["rejected"] for c, v in g.items()}, "gate_closed_label": CA.GATE_NOTE}


def t_src():
    rng = np.random.default_rng(12)
    Ws = weights(150, 2000, 13)
    src = np.array(["val"] * 60 + ["train_heldout"] * 90)
    v_diff = np.where(src == "val", 0.20, 0.10) + 0.02 * rng.standard_normal(150)
    v_same = 0.15 + 0.02 * rng.standard_normal(150)
    a, b = CA.by_source(v_diff, src, Ws, ["train_heldout", "val"]), CA.by_source(v_same, src, Ws, ["train_heldout", "val"])
    assert a["difference"]["ci95"][1] < 0 and b["difference"]["ci95"][0] < 0 < b["difference"]["ci95"][1]
    return {"planted": a["difference"], "none": b["difference"]}


def t_fold():
    logs = {"log%04d" % i: ("val" if i % 5 < 2 else "train_heldout") for i in range(375)}
    f1, f2, f3 = F.make_folds(logs), F.make_folds(logs), F.make_folds(logs, seed=1)
    sizes = [sum(1 for v in f1["fold_of_log"].values() if v == j) for j in range(5)]
    assert sizes == [75] * 5 and f1 == f2 and f1["fold_of_log"] != f3["fold_of_log"] and set(f1["fold_of_log"]) == set(logs)
    p = os.path.join(OUT, "fold_test_logs.json")
    json.dump({"logs": logs}, open(p, "w"))
    F.main(["--logs", p, "--out", os.path.join(OUT, "fold_test_folds.json")])
    h = open(os.path.join(OUT, "fold_test_folds.json.sha256")).read().split()[0]
    assert h == CA.sha(os.path.join(OUT, "fold_test_folds.json"))
    return {"sizes": sizes, "val_share_by_fold": [f1["by_fold"][str(j)]["sources"]["val"] / 75 for j in range(5)]}


def t_gen():
    import make_c1_run_v01 as MK
    with open(os.path.join(os.path.dirname(C1), "k8", "k8_run_v04.py"), encoding="utf-8", newline="") as f:
        gen = MK.make(f.read())
    with open(os.path.join(C1, "c1_run_v01.py"), encoding="utf-8", newline="") as f:
        assert f.read() == gen, "the generator does not reproduce c1_run_v01.py"
    # a stand-in dry run on the nuScenes caches: manifests only (k8_run_v02 T12's instrumented check is inherited unchanged)
    names = sorted(json.load(open(os.path.join(W, "30_DATA", "k6", "cache_v02_t1_train", "MANIFEST.json")))["scenes"])[:40]
    lp = os.path.join(OUT, "gen_units.txt")
    open(lp, "w").write("\n".join("%s train" % n for n in names))
    F.main(["--logs", lp, "--out", os.path.join(OUT, "gen_folds.json")])
    fake = {"folds_sha256": CA.sha(os.path.join(OUT, "gen_folds.json"))}
    fp = os.path.join(OUT, "gen_fake_fits.json")
    json.dump(fake, open(fp, "w"))
    cmd = [PY, "-B", os.path.join(C1, "c1_run_v01.py"), "--caches", os.path.join(W, "30_DATA", "k6", "cache_v02_t1_train"),
           os.path.join(W, "30_DATA", "k6", "cache_v02_t1_val"), "--fits", fp, "--c1-folds", os.path.join(OUT, "gen_folds.json"), "--standin",
           "--tag", "t1_decide", "--mode", "decide", "--out", os.path.join(OUT, "gen_dryrun"), "--dry-run"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    assert r.returncode == 0 and "DRY RUN (C1 STAND-IN" in r.stdout and "40 scenes" in r.stdout, r.stdout[-800:] + r.stderr[-800:]
    bad = subprocess.run(cmd[:-1] + ["--c1-plan", "x.md", "--dry-run"], capture_output=True, text=True)
    assert bad.returncode != 0, "--standin with a plan must be refused"
    return {"generator": True, "dry_run": r.stdout.splitlines()[0][:160]}


def main():
    out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(OUT, "c1_tests_v01.json")
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    res, ok = {}, True
    for name, fn in (("C9", t_c9), ("H1", t_h1), ("H2", t_h2), ("H3", t_h3), ("H10", t_h10), ("H6_H7", t_h6_h7), ("H8", t_h8), ("H9", t_h9),
                     ("HOLM", t_holm), ("SRC", t_src), ("FOLD", t_fold), ("GEN", t_gen), ("E15", t_e15)):
        t1 = time.time()
        try:
            res[name] = {"pass": True, "result": fn(), "seconds": round(time.time() - t1, 1)}
        except Exception:
            ok = False
            res[name] = {"pass": False, "error": traceback.format_exc(), "seconds": round(time.time() - t1, 1)}
        print(name, "PASS" if res[name]["pass"] else "FAIL", res[name]["seconds"], "s", flush=True)
        if not res[name]["pass"]:
            print(res[name]["error"][-1500:], flush=True)
    res["code_sha256"] = {f: CA.sha(os.path.join(C1, f)) for f in ("c1_analyse_v01.py", "c1_crc_exact_v01.py", "c1_fit_v01.py", "c1_folds_v01.py",
                                                                    "c1_run_v01.py")}
    res["verdict"] = "ALL_PASS" if ok else "FAIL"
    res["seconds"] = round(time.time() - t0, 1)
    json.dump(res, open(out_path, "w"), indent=1, default=str)
    print(res["verdict"], res["seconds"], "s")


if __name__ == "__main__":
    main()
