#!/usr/bin/env python3
"""K7 analysis (Claude line, v01, 1 Nov 2026). Implements K7 plan v01: planner-matched calibration.

Every statistical function is the frozen K6 analysis' (k6_analyse_v02, imported read-only): the cell family (group x
axis x motion, pooled over range), the scene-level rate, the log-cluster bootstrap (B = 2000), the one-sided simultaneous
sup-t flag (m_lib_v04._simul), evaluability (>= 39 scenes, >= 8 logs), the power rule (power >= 0.80 to be flagged at a
true rate of 0.15, beta-binomial with intra-scene correlation 0.5, 200 datasets, from M7's record counts only), paired
contrasts and the closed-loop summaries. The K7 run labels M7 as 'Mstar' (k7_fits: 'Mstar_ip').

Decision mode (confirmatory), per tracker:
  PD7 (primary)  relied-on axis, enforced, satisfied, any pair gap, steps 0.5-2 s, offset 0, in-path or not
  SD1_7          PD7 with pair gap <= 5 m (the near-binding constraints)
  PD             PD7 restricted to the method's in-path flag (the K6 primary population)
  Joint family: M7's evaluable cells of PD7, SD1_7 and PD and the three pooled cells, in ONE one-sided simultaneous
        sup-t at 0.95 (family-wise 5 % for the whole validity claim, as K6's single family was for its claim).
  HK1a  (i) no cell of the joint family flagged; (ii) at least F_MIN = 6 power-qualified PD7 cells AND at least F_MIN
        power-qualified SD1_7 cells (the K6 power rule on M7's own counts of each population, power seeds
        [20261107, i, 0] and [20261107, i, 1]), each family not flagged in its own sup-t.
  HK1b  the three pooled cells exist (evaluable) and none is flagged in the joint family.
  HK1 = HK1a and HK1b.
  HK2   (T1) a recalibrated practitioner arm (B1 or B4) is flagged in a PD7 cell at level 1 - 0.05/2 (sup-t over its
        evaluable PD7 cells), M7 is not flagged there, and the paired difference arm - M7 is positive at 1 - 0.05/2.
        B0 (fit-free; its K6 outcomes were seen) is descriptive.
  HK3   (dominance) for each of B0, B1, B4, B9, at level 1 - 0.05/4: either (a) M7's infeasible-decision rate is lower
        (per-scene paired M7 - arm, one-sided log-bootstrap upper bound below 0), or (b) the arm is flagged in a PD7 cell
        (sup-t over its evaluable PD7 cells) where M7 is not flagged and the paired difference arm - M7 is positive. That is,
        no comparator is shown to be both as valid and more operable than M7. The K6 form (route (a) for all four) is
        reported as HK3_K6_form_all_lower.
  Verdict: GO-A if HK1 and HK3 on T1 and T3 and HK2 on T1; GO-B if HK1 and HK3 on T1 and T3 without HK2; else NO-GO.
Descriptive: SD1_7 (PD7 with gap <= 5 m), NIP (PD7 not in-path), SD3_7 (relied-on, any enforcement or satisfaction), the
  pooled-M7 and B6 references, every arm's PD7 and PD cells; the closed loop as in K6 with PL7 (any in-path, offset
  <= 15 m) beside PL.
Usage: python -B k7_analyse_v01.py --runs <dir> --tags t1 t3 --manifests <...> --out <json> --prereg <plan.md>
       [--allow-dev --boot B]
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


def joint_family(tabs, cells, scene_of_ep, log_of_ep, W):
    """One-sided simultaneous sup-t (0.95) over M7's evaluable cells of every confirmatory population and their evaluable
    pooled cells. Returns {name: summary}, the flagged names and q."""
    names, ests, boots, recs = [], [], [], []
    one = np.ones((1, len(scene_of_ep)))
    for p in CONF_POPS:
        Nc, Xc, est, boot, ev = tabs[p]
        for j in np.flatnonzero(ev["Mstar"]):
            names.append("%s:%s" % (p, cells[j][0]))
            ests.append(est["Mstar"][j])
            boots.append(boot["Mstar"][:, j])
            recs.append(int(Nc["Mstar"][:, j].sum()))
        Np, Xp = Nc["Mstar"].sum(1, keepdims=True), Xc["Mstar"].sum(1, keepdims=True)
        if A.evaluable(Np, scene_of_ep, log_of_ep)[0]:
            names.append("%s:pooled" % p)
            ests.append(A.rates(Np, Xp, one)[0][0])
            boots.append(A.rates(Np, Xp, W)[:, 0])
            recs.append(int(Np.sum()))
    if not names:
        return {}, [], float("nan")
    est, boot = np.array(ests), np.column_stack(boots)
    lb, ub, se, sig, q = A.flag(est, boot, np.arange(len(est)), 0.95)
    out = {n: {"E": float(est[i]), "lb_sim": float(lb[i]), "ub_sim": float(ub[i]), "se": float(se[i]), "sig_above": bool(sig[i]),
               "records": recs[i]} for i, n in enumerate(names)}
    return out, [n for i, n in enumerate(names) if sig[i]], float(q)


def analyse_decide(eps, counts, log_of_scene, B, rng, prng):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES and o["arm"] != "LOG"]
    cells = A.cell_family()
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    res = {"scenes": len(keys), "logs": len(logs)}
    pops, tabs = A.populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_DECIDE)
    res["populations"] = pops
    Nc7, Xc7, est7, boot7, ev7 = tabs["PD7_primary"]
    # HK1a (i) and HK1b: one simultaneous family over M7's evaluable cells of PD7, SD1_7 and PD and their pooled cells
    joint, joint_flagged, joint_q = joint_family(tabs, cells, scene_of_ep, log_of_ep, W)
    res["HK1_joint_family"] = {"q": joint_q, "cells": joint, "flagged": joint_flagged, "size": len(joint)}
    # HK1a (ii): power floors on PD7 and SD1_7 (the K6 rule, from M7's own record counts), each family not flagged in its own sup-t
    res["HK1a_floors"] = {}
    for k, pname in enumerate(FLOOR_POPS):
        Nc, Xc, _, _, ev = tabs[pname]
        pw, _ = A.power_family(Nc["Mstar"], ev["Mstar"], scene_of_ep, W[:500], np.random.default_rng(list(prng) + [k]))
        fam_mask = ev["Mstar"] & (pw >= POWER_MIN)
        il_m, _, _, _ = A.inloop_population({"Mstar": Nc["Mstar"]}, {"Mstar": Xc["Mstar"]}, cells, scene_of_ep, log_of_ep, W, family_from=fam_mask)
        res["HK1a_floors"][pname] = {"power_at_%.2f" % A.POWER_P: {cells[j][0]: float(pw[j]) for j in np.flatnonzero(ev["Mstar"])},
                                     "family": [cells[j][0] for j in np.flatnonzero(fam_mask)], "family_size": int(fam_mask.sum()),
                                     "family_own_supt": il_m["Mstar"],
                                     "met": bool(fam_mask.sum() >= F_MIN and not il_m["Mstar"]["sig_above_cells"])}
    res["evaluable_cells"] = {p: int(tabs[p][4]["Mstar"].sum()) for p in CONF_POPS}
    hk2 = {}
    for b in PRACTITIONER:
        if b not in arms:
            continue
        fb = np.flatnonzero(ev7[b])
        sig_b = []
        if len(fb):
            _, _, _, sb, _ = A.flag(est7[b], boot7[b], fb, LEVEL_HK2)
            sig_b = [cells[j][0] for i, j in enumerate(fb) if sb[i]]
        pr = A.paired(est7, boot7, ev7, cells, b, "Mstar", LEVEL_HK2)
        hk2[b] = {"flagged_bonferroni": sig_b, "paired": pr,
                  "fails_where_Mstar_holds": [c for c in sig_b if c not in pops["PD7_primary"]["cells_by_arm"]["Mstar"]["sig_above_cells"]
                                              and pr.get(c, {}).get("positive", False)]}
    if "B0" in arms:
        fb = np.flatnonzero(ev7["B0"])
        _, _, _, sb, _ = A.flag(est7["B0"], boot7["B0"], fb, LEVEL_HK2)
        hk2["B0_descriptive"] = {"flagged_bonferroni": [cells[j][0] for i, j in enumerate(fb) if sb[i]]}
    res["HK2"] = hk2
    inf = {(o["scene"], o["arm"]): (o["infeasible_frames"], o["frames"]) for o in eps}
    scenes = sorted({o["scene"] for o in eps})
    lg = np.array([logs.index(log_of_scene[sc]) for sc in scenes])
    Ws = W_logs[:, lg]
    rate = {a: np.array([inf[(sc, a)][0] / max(inf[(sc, a)][1], 1) for sc in scenes]) for a in arms}
    res["infeasible_rate"] = {a: {"mean": float(rate[a].mean()),
                                  "ci95": [float(x) for x in np.quantile((Ws @ rate[a]) / Ws.sum(1), [0.025, 0.975])]} for a in arms}
    hk3 = {}
    m7_flagged = set(pops["PD7_primary"]["cells_by_arm"]["Mstar"]["sig_above_cells"])
    for b in [x for x in arms if x != "Mstar"]:
        d = rate["Mstar"] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        ub = float(np.quantile(bm, LEVEL_HK3))
        r = {"mean_diff": float(d.mean()), "ub_one_sided_bonferroni": ub, "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
             "lower": bool(ub < 0), "tested": b in HK3_ARMS}
        if b in HK3_ARMS:
            # route (b) of the dominance criterion: b is shown invalid where M7 is not (flag at 1 - 0.05/4 over b's evaluable PD7
            # cells, M7 not flagged there in its own all-evaluable PD7 sup-t, paired b - M7 positive at 1 - 0.05/4)
            fb = np.flatnonzero(ev7[b])
            sig_b = []
            if len(fb):
                _, _, _, sb, _ = A.flag(est7[b], boot7[b], fb, LEVEL_HK3)
                sig_b = [cells[j][0] for i, j in enumerate(fb) if sb[i]]
            pr = A.paired(est7, boot7, ev7, cells, b, "Mstar", LEVEL_HK3)
            r["invalid_where_M7_holds"] = [c for c in sig_b if c not in m7_flagged and pr.get(c, {}).get("positive", False)]
            r["dominated"] = bool(r["lower"] or r["invalid_where_M7_holds"])
        hk3[b] = r
    res["HK3"] = hk3
    cell_flags = [c for c in joint_flagged if not c.endswith(":pooled")]
    pooled_present = all(("%s:pooled" % p) in joint for p in CONF_POPS)
    hk1a_i = not cell_flags
    hk1a = hk1a_i and all(v["met"] for v in res["HK1a_floors"].values())
    hk1b = pooled_present and not [c for c in joint_flagged if c.endswith(":pooled")]
    res["hypotheses"] = {"HK1a_family_size_PD7": res["HK1a_floors"]["PD7_primary"]["family_size"],
                         "HK1a_family_size_SD1_7": res["HK1a_floors"]["SD1_7_gap_le_5m"]["family_size"], "HK1a_family_floor": F_MIN,
                         "HK1a_no_cell_flag_joint": bool(hk1a_i), "HK1a": bool(hk1a), "HK1b": bool(hk1b), "HK1": bool(hk1a and hk1b),
                         "HK2": bool(any(v.get("fails_where_Mstar_holds") for k, v in hk2.items() if k in PRACTITIONER)),
                         "HK3": bool(all(hk3.get(b, {}).get("dominated", False) for b in HK3_ARMS)),
                         "HK3_K6_form_all_lower": bool(all(hk3.get(b, {}).get("lower", False) for b in HK3_ARMS))}
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
    return {"verdict": verdict, "T1": h1, "T3": h3}


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
    print("K7 ANALYSIS DONE")


if __name__ == "__main__":
    main()
