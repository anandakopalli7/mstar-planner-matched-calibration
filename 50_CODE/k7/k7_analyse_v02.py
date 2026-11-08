#!/usr/bin/env python3
"""K7 analysis (Claude line, v02, 1 Nov 2026). Implements K7 plan v01 after the pre-freeze review R12
(70_TESTS/R12_K7_PREFREEZE_REVIEW_v01.md; v01 of this file is the superseded draft). v02 changes, all from R12:
  C2  K6's own validity tests are applied to EACH confirmatory population (no joint family): per population, no flag in
      M7's one-sided simultaneous sup-t over all its evaluable cells (0.95), and the pooled cell not flagged pointwise (0.95)
  C1  HK3 is K6's form again (M7 less often infeasible than each of B0, B1, B4, B9); the dominance form is reported only
  M1  PD's power family is computed with the K6 rule and reported (not a condition: in-path non-exceedance stays not
      power-qualified, as in K6)
  M5  HK2 is read on the near-binding population SD1_7
  m3  q must be finite; PD needs >= 1 evaluable cell; HK1c (pooled upper bound <= delta + 0.03) reported
  m4  the run's fits file must hash to its run record; each tracker's scene -> log map is asserted equal to the one used

Every statistical function is the frozen K6 analysis' (k6_analyse_v02, imported read-only): the cell family (group x
axis x motion, pooled over range), the scene-level rate, the log-cluster bootstrap (B = 2000), the one-sided simultaneous
sup-t flag (m_lib_v04._simul), evaluability (>= 39 scenes, >= 8 logs), the power rule (power >= 0.80 to be flagged at a
true rate of 0.15 in the population's all-evaluable sup-t, beta-binomial with intra-scene correlation 0.5, 200 datasets,
from M7's record counts only, first 500 bootstrap weights), paired contrasts and the closed-loop summaries. The K7 run
labels M7 as 'Mstar' (k7_fits: 'Mstar_ip').

Decision mode (confirmatory), per tracker:
  PD7 (primary)  relied-on axis, enforced, satisfied, any pair gap, steps 0.5-2 s, offset 0, in-path or not
  SD1_7          PD7 with pair gap <= 5 m (the near-binding constraints)
  PD             PD7 restricted to the method's in-path flag (K6's primary population; the non-regression check)
  HK1 (hk1_rule), for EACH of PD7, SD1_7 and PD: (i) no flag in M7's sup-t over all its evaluable cells; (ii) the pooled cell
      evaluable and not flagged pointwise; and for PD7 and SD1_7 (iii) >= F_MIN = 6 power-qualified cells (power seeds
      [20261107, i, 0] and [20261107, i, 1]), not flagged in their own sup-t; PD needs >= 1 evaluable cell.
  HK2 (T1) a recalibrated practitioner arm (B1 or B4) flagged in an SD1_7 cell at 1 - 0.05/2 (sup-t over its evaluable
      SD1_7 cells), M7 not flagged there in its own all-evaluable SD1_7 sup-t, and the paired arm - M7 positive at
      1 - 0.05/2 (sup-t over the cells evaluable for both). B0 (fit-free; K6 outcomes seen) is descriptive.
  HK3 (K6's form) M7's infeasible-decision rate lower than each of B0, B1, B4, B9: per-scene paired M7 - arm, one-sided
      log-bootstrap upper bound at 1 - 0.05/4 below 0 for all four, on both trackers.
  Verdict: GO-A if HK1 and HK3 on T1 and T3 and HK2 on T1; GO-B if HK1 and HK3 on T1 and T3 without HK2; else NO-GO,
      with the pattern of the failed conditions named.
Reported only: the dominance form of HK3 (each comparator either less operable, or its pooled SD1_7 cell flagged pointwise
  at 1 - 0.05/4 with a positive paired pooled difference); every arm's cells and pooled cells in PD7, SD1_7, PD, NIP, SD3_7;
  HK1c; PD's power family; the closed loop as in K6 with PL7 beside PL.
Usage: python -B k7_analyse_v02.py --runs <dir> --tags t1 t3 --manifests <...> --out <json> --prereg <plan.md>
       [--allow-dev --boot B --modes decide loop]
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np

K7 = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(K7))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
sys.path.insert(0, K7)
import k6_analyse_v02 as A  # noqa: E402
import k7_sim_v01 as S  # noqa: E402
import m_lib_v04 as M  # noqa: E402

DELTA, B_BOOT, SEED, POWER_SEED = A.DELTA, A.B_BOOT, 20261106, 20261107
F_MIN = A.F_MIN
POWER_MIN = A.POWER_MIN
PRACTITIONER = ("B1", "B4")
LEVEL_HK2 = 1 - 0.05 / len(PRACTITIONER)
HK3_ARMS = A.HK3_ARMS
LEVEL_HK3 = 1 - 0.05 / len(HK3_ARMS)
N_SCENES_CONF, DELAYS = A.N_SCENES_CONF, A.DELAYS
EXPERIMENT = A.EXPERIMENT
DEV_SCENES = A.DEV_SCENES
CC = A.STEPS_CC
POP_DECIDE = {
    "PD7_primary": dict(offset=(0,), inpath=(0, 1), gap=(0, 1, 2), steps=CC),
    "PD_inpath": dict(offset=(0,), inpath=(1,), gap=(0, 1, 2), steps=CC),
    "SD1_7_gap_le_5m": dict(offset=(0,), inpath=(0, 1), gap=(0, 1), steps=CC),
    "NIP_not_in_path": dict(offset=(0,), inpath=(0,), gap=(0, 1, 2), steps=CC),
    "SD3_7_all_relied_any_enforcement": dict(offset=(0,), inpath=(0, 1), enforced=(0, 1), satisfied=(0, 1), gap=(0, 1, 2), steps=CC),
}
POP_LOOP = {
    "PL7_offset_le_15m": dict(offset=(0, 1), inpath=(0, 1), gap=(0, 1, 2), steps=CC),
    "PL_offset_le_15m": dict(offset=(0, 1), gap=(0, 1, 2), steps=CC),
    "SL1_7_all_offsets": dict(offset=(0, 1, 2), inpath=(0, 1), gap=(0, 1, 2), steps=CC),
}


CONF_POPS = ("PD7_primary", "SD1_7_gap_le_5m", "PD_inpath")
FLOOR_POPS = ("PD7_primary", "SD1_7_gap_le_5m")


def sha(p):
    return A.sha(p)


def hk1_rule(T, cells, scene_of_ep, log_of_ep, W, power_key, fams=None):
    """K6's validity tests on each confirmatory population. T: {population: (N, X)} of M7 (episode x cell tables).
    fams: optional precomputed power-qualified masks {population: bool array} (the OC passes them; they depend on N only).
    Returns the per-population results and HK1a, HK1b, HK1."""
    one = np.ones((1, len(scene_of_ep)))
    out = {"pops": {}}
    hk1a = hk1b = True
    for k, p in enumerate(CONF_POPS):
        N, X = T[p]
        ev = A.evaluable(N, scene_of_ep, log_of_ep)
        fam = np.flatnonzero(ev)
        est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
        r = {"evaluable": int(len(fam)), "flagged": []}
        if len(fam):
            lb, ub, se, sig, q = A.flag(est, boot, fam, 0.95)
            assert np.isfinite(q), "non-finite sup-t quantile in " + p
            r["q"] = float(q)
            r["flagged"] = [cells[j][0] for i, j in enumerate(fam) if sig[i]]
            r["max_lb"] = float(np.nanmax(lb))
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        r["pooled"] = None
        if A.evaluable(Np, scene_of_ep, log_of_ep)[0]:
            e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
            lbp, ubp, sep, sigp, qp = A.flag(e1, b1, np.array([0]), 0.95)
            assert np.isfinite(qp), "non-finite pooled quantile in " + p
            r["pooled"] = {"E": float(e1[0]), "lb": float(lbp[0]), "ub": float(ubp[0]), "flagged": bool(sigp[0]),
                           "HK1c_ub_le_delta_plus_0.03": bool(ubp[0] <= DELTA + 0.03)}
        a_ok = (not r["flagged"]) and len(fam) >= 1
        b_ok = r["pooled"] is not None and not r["pooled"]["flagged"]
        if fams is not None and p in fams:
            qual = fams[p]
        else:
            pw, _ = A.power_family(N, ev, scene_of_ep, W[:500], np.random.default_rng(list(power_key) + [k]))
            qual = ev & (pw >= POWER_MIN)
            r["power_at_%.2f" % A.POWER_P] = {cells[j][0]: float(pw[j]) for j in fam}
        fq = np.flatnonzero(qual)
        r["family"] = [cells[j][0] for j in fq]
        r["family_size"] = int(len(fq))
        r["family_flagged"] = []
        if len(fq):
            _, _, _, sigf, qf = A.flag(est, boot, fq, 0.95)
            assert np.isfinite(qf), "non-finite family quantile in " + p
            r["family_flagged"] = [cells[j][0] for i, j in enumerate(fq) if sigf[i]]
        if p in FLOOR_POPS:
            r["floor_met"] = bool(len(fq) >= F_MIN and not r["family_flagged"])
            a_ok = a_ok and r["floor_met"]
        else:
            r["floor_note"] = "reported only: no power floor on PD (in-path non-exceedance is not power-qualified, as in K6)"
        r["HK1a_met"], r["HK1b_met"] = bool(a_ok), bool(b_ok)
        hk1a &= a_ok
        hk1b &= b_ok
        out["pops"][p] = r
    out["HK1a"], out["HK1b"], out["HK1"] = bool(hk1a), bool(hk1b), bool(hk1a and hk1b)
    return out


def analyse_decide(eps, counts, log_of_scene, B, rng, power_key):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES and o["arm"] != "LOG"]
    cells = A.cell_family()
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    res = {"scenes": len(keys), "logs": len(logs)}
    pops, tabs = A.populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_DECIDE)
    res["populations"] = pops
    T = {p: (tabs[p][0]["Mstar"], tabs[p][1]["Mstar"]) for p in CONF_POPS}
    res["HK1"] = hk1_rule(T, cells, scene_of_ep, log_of_ep, W, power_key)
    res["evaluable_cells"] = {p: res["HK1"]["pops"][p]["evaluable"] for p in CONF_POPS}
    # HK2 on the near-binding population SD1_7 (R12 M5)
    Ns, Xs, ests, boots, evs = tabs["SD1_7_gap_le_5m"]
    m7_flag_sd = set(pops["SD1_7_gap_le_5m"]["cells_by_arm"]["Mstar"]["sig_above_cells"])
    hk2 = {}
    for b in PRACTITIONER:
        if b not in arms:
            continue
        fb = np.flatnonzero(evs[b])
        sig_b = []
        if len(fb):
            _, _, _, sb, _ = A.flag(ests[b], boots[b], fb, LEVEL_HK2)
            sig_b = [cells[j][0] for i, j in enumerate(fb) if sb[i]]
        pr = A.paired(ests, boots, evs, cells, b, "Mstar", LEVEL_HK2)
        hk2[b] = {"flagged_bonferroni_SD1_7": sig_b, "paired": pr,
                  "fails_where_Mstar_holds": [c for c in sig_b if c not in m7_flag_sd and pr.get(c, {}).get("positive", False)]}
    if "B0" in arms:
        fb = np.flatnonzero(evs["B0"])
        _, _, _, sb, _ = A.flag(ests["B0"], boots["B0"], fb, LEVEL_HK2)
        hk2["B0_descriptive"] = {"flagged_bonferroni_SD1_7": [cells[j][0] for i, j in enumerate(fb) if sb[i]]}
    res["HK2"] = hk2
    # HK3 (K6's form) and the dominance form (reported only)
    inf = {(o["scene"], o["arm"]): (o["infeasible_frames"], o["frames"]) for o in eps}
    scenes = sorted({o["scene"] for o in eps})
    lg = np.array([logs.index(log_of_scene[sc]) for sc in scenes])
    Ws = W_logs[:, lg]
    rate = {a: np.array([inf[(sc, a)][0] / max(inf[(sc, a)][1], 1) for sc in scenes]) for a in arms}
    res["infeasible_rate"] = {a: {"mean": float(rate[a].mean()),
                                  "ci95": [float(x) for x in np.quantile((Ws @ rate[a]) / Ws.sum(1), [0.025, 0.975])]} for a in arms}
    one = np.ones((1, len(scene_of_ep)))
    pooled_sd = {}
    for a_ in arms:
        Np, Xp = Ns[a_].sum(1, keepdims=True), Xs[a_].sum(1, keepdims=True)
        pooled_sd[a_] = (A.rates(Np, Xp, one)[0][0], A.rates(Np, Xp, W)[:, 0])
    hk3 = {}
    for b in [x for x in arms if x != "Mstar"]:
        d = rate["Mstar"] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        ub = float(np.quantile(bm, LEVEL_HK3))
        r = {"mean_diff": float(d.mean()), "ub_one_sided_bonferroni": ub, "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
             "lower": bool(ub < 0), "tested": b in HK3_ARMS}
        if b in HK3_ARMS:
            eb, bb = pooled_sd[b]
            lbb, _, _, sgb, _ = A.flag(np.array([eb]), bb[:, None], np.array([0]), LEVEL_HK3)
            em, bmm = pooled_sd["Mstar"]
            lbd, _, _, sgd, _ = A.flag(np.array([eb - em]) + DELTA, (bb - bmm)[:, None] + DELTA, np.array([0]), LEVEL_HK3)
            r["dominance_reported_only"] = {"pooled_SD1_7_E": float(eb), "pooled_SD1_7_lb": float(lbb[0]), "pooled_SD1_7_flagged": bool(sgb[0]),
                                            "paired_pooled_diff": float(eb - em), "paired_pooled_positive": bool(sgd[0]),
                                            "dominated": bool(r["lower"] or (sgb[0] and sgd[0]))}
        hk3[b] = r
    res["HK3"] = hk3
    # PD power family (K6 rule, reported only; R12 M1) is in res["HK1"]["pops"]["PD_inpath"]
    h = res["HK1"]
    res["hypotheses"] = {"HK1a": h["HK1a"], "HK1b": h["HK1b"], "HK1": h["HK1"],
                         "family_size_PD7": h["pops"]["PD7_primary"]["family_size"], "family_size_SD1_7": h["pops"]["SD1_7_gap_le_5m"]["family_size"],
                         "family_size_PD_reported": h["pops"]["PD_inpath"]["family_size"], "family_floor": F_MIN,
                         "flagged_cells": {p: h["pops"][p]["flagged"] for p in CONF_POPS},
                         "pooled_flagged": {p: (h["pops"][p]["pooled"] or {}).get("flagged") for p in CONF_POPS},
                         "HK2": bool(any(v.get("fails_where_Mstar_holds") for k, v in hk2.items() if k in PRACTITIONER)),
                         "HK3": bool(all(hk3.get(b, {}).get("lower", False) for b in HK3_ARMS)),
                         "HK3_not_lower_against": [b for b in HK3_ARMS if not hk3.get(b, {}).get("lower", False)],
                         "HK3_dominance_reported_only": bool(all(hk3.get(b, {}).get("dominance_reported_only", {}).get("dominated", False) for b in HK3_ARMS))}
    return res

def analyse_loop(eps, counts, log_of_scene, B, rng):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES]
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights([o for o in eps if o["arm"] != "LOG"], log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    res = {"episode_keys": len(keys), "logs": len(logs)}
    res["populations"], _ = A.populations([o for o in eps if o["arm"] != "LOG"], counts, arms, keys, scene_of_ep, log_of_ep, W, POP_LOOP)
    res["progress_vs_Mstar"] = A.progress_contrasts(eps, arms, log_of_scene, logs, W_logs)
    res["outcomes"] = A.outcome_summary(eps)
    return res


def decide(d1, d3):
    h1, h3 = d1["hypotheses"], d3["hypotheses"]
    if h1["HK1"] and h3["HK1"] and h1["HK3"] and h3["HK3"]:
        verdict = "K7 GO-A" if h1["HK2"] else "K7 GO-B"
    else:
        verdict = "K7 NO-GO"
    failed = ["%s %s" % (t, k) for t, h in (("T1", h1), ("T3", h3)) for k in ("HK1a", "HK1b", "HK3") if not h[k]]
    return {"verdict": verdict, "failed_conditions": failed, "T1": h1, "T3": h3}


def check_binding(prereg, runs, tags, manifests):
    import k7_run_v01 as R
    assert list(tags) == ["t1", "t3"], "the tags must be t1 t3, in this order (HK2 is read on T1)"
    side, hashes = R.frozen_hashes(prereg)
    for p in manifests:
        assert sha(p) in hashes, "a manifest passed to the analysis is not frozen: " + p
    rec = open(os.path.join(os.path.dirname(prereg), "K7_FREEZE_RECORD_v01.txt"), encoding="utf-8").read()
    assert side in rec, "the plan sidecar differs from the freeze record"
    for p in (os.path.abspath(__file__), A.__file__, M.__file__, S.__file__):
        assert sha(p) in hashes, "analysis input not frozen: " + p
    for tag in tags:
        for mode in ("decide", "loop"):
            rr = json.load(open(os.path.join(runs, "run_record_%s_%s.json" % (tag, mode))))
            assert rr["prereg"] == side and rr["mode"] == mode, "run %s_%s was not made under the frozen K7 plan" % (tag, mode)
            for k in ("fits_sha256", "sim_sha256", "runner_sha256"):
                assert rr[k] in hashes, "%s of run %s_%s is not frozen" % (k, tag, mode)
            assert rr["sim_sha256"] == sha(S.__file__), "run %s_%s did not use k7_sim_v01" % (tag, mode)
            assert all(h in hashes for h in rr["manifest_sha256"]), "a cache manifest of run %s_%s is not frozen" % (tag, mode)
            assert rr["arms"] == list(S.ARMS) and rr["delays_kf"] == DELAYS and rr["scenes"] == N_SCENES_CONF, "incomplete design " + tag
            n_ep = N_SCENES_CONF * len(S.ARMS) * len(DELAYS) if mode == "loop" else N_SCENES_CONF * (len(S.ARMS) - 1)
            assert rr["episodes"] == n_ep, "incomplete run %s_%s" % (tag, mode)
            assert rr["tag"] == "%s_%s" % (tag, mode), "run record %s_%s carries another tag" % (tag, mode)
            assert sha(rr["fits"]) == rr["fits_sha256"], "the fits file of run %s_%s differs from its run record" % (tag, mode)
            fits = json.load(open(rr["fits"]))
            assert fits.get("k7") is True and os.path.basename(rr["fits"]) == "k7_fits_%s_v01.json" % tag, "run %s_%s did not use the K7 fits" % (tag, mode)
            exps = {json.load(open(os.path.join(c, "MANIFEST.json")))["experiment"] for c in rr["caches"]}
            same_tracker = (fits["tags"] == ["%s_train" % tag, "%s_val" % tag] and exps == {EXPERIMENT[tag]}
                            and all(("cache_v02_%s_" % tag) in c for c in rr["caches"]))
            assert same_tracker, "run %s_%s uses another tracker's fits or caches" % (tag, mode)
            for f in ("episodes", "counts"):
                ext = "jsonl" if f == "episodes" else "npz"
                assert sha(os.path.join(runs, "%s_%s_%s.%s" % (f, tag, mode, ext))) == rr["%s_sha256" % f], "%s of run %s_%s changed" % (f, tag, mode)
    return side


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tags", nargs=2, required=True)
    ap.add_argument("--manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--prereg", default=None)
    ap.add_argument("--allow-dev", action="store_true", help="development checks only: mini scenes, no plan check")
    ap.add_argument("--boot", type=int, default=B_BOOT)
    ap.add_argument("--modes", nargs="+", default=["decide", "loop"])
    a = ap.parse_args()
    global DEV_SCENES
    if a.allow_dev:
        DEV_SCENES = ()
        A.MIN_SCENES, A.MIN_LOGS = 2, 1
        side = None
    else:
        assert a.boot == B_BOOT and a.modes == ["decide", "loop"], "the confirmatory analysis is fixed: B = %d, both modes" % B_BOOT
        assert a.prereg, "the confirmatory analysis needs --prereg"
        side = check_binding(a.prereg, a.runs, a.tags, a.manifests)
    log_of_scene = {}
    for p in a.manifests:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    if not a.allow_dev:
        for tag in a.tags:
            for c in json.load(open(os.path.join(a.runs, "run_record_%s_decide.json" % tag)))["caches"]:
                for s_, info in json.load(open(os.path.join(c, "MANIFEST.json")))["scenes"].items():
                    assert log_of_scene.get(s_) == info["log"], "scene -> log map of %s differs for %s" % (tag, s_)
    out = {"delta": DELTA, "boot": a.boot, "prereg_sha256": side, "decide": {}, "loop": {}}
    for i, tag in enumerate(a.tags):
        for mode in a.modes:
            eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s_%s.jsonl" % (tag, mode)))]
            counts = dict(np.load(os.path.join(a.runs, "counts_%s_%s.npz" % (tag, mode))))
            if mode == "decide":
                out["decide"][tag] = analyse_decide(eps, counts, log_of_scene, a.boot, np.random.default_rng([SEED, i, 0]), [POWER_SEED, i])
            else:
                out["loop"][tag] = analyse_loop(eps, counts, log_of_scene, a.boot, np.random.default_rng([SEED, i, 1]))
    if "decide" in a.modes:
        out["decision"] = decide(out["decide"][a.tags[0]], out["decide"][a.tags[1]])
        print(json.dumps(out["decision"], indent=1))
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print("K7 ANALYSIS V02 DONE")


if __name__ == "__main__":
    main()
