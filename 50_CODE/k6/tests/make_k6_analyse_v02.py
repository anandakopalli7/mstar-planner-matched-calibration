#!/usr/bin/env python3
"""Rewrites the top (docstring, constants) and bottom (per-mode analyses, decision, binding, main) of k6_analyse_v02.py for
the two-mode design of K6 plan v02 (decision mode for HK1-HK3, closed loop for the operational estimates). The helper
functions in between (cell_family .. progress_contrasts) are kept. Run once (Claude line, 1 Nov 2026)."""
import os

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(K, "k6_analyse_v02.py")
s = open(p, encoding="utf-8").read()
assert "def analyse_decide(" not in s, "already applied"

TOP = '''#!/usr/bin/env python3
"""K6 analysis (Claude line, v02, 1 Nov 2026). Implements K6 plan v02: endpoints, inference and decision rule.
v02 follows review R09 (C1, C2, M1-M6, m1, m4, m10) and the development iterations of D09 v04.

Two run modes per tracker (k6_run_v02 --mode): "decide" (one planner decision per keyframe from the logged ego's own
state: exact replayed perception, sensor offset 0) and "loop" (the closed loop with delays 0, 1, 2 s).

Decision mode (confirmatory).
  In-loop records (k6_sim_v02._record): primary population PD: the method's in-path flag, relied-on axis, enforced, plan
  satisfied the relied-on axis at its margin; any pair gap; the enforced calibrated steps 0.5-2 s. Per cell (group x axis x
  motion), the rate is the mean over scenes with records in the cell of the scene's exceedance fraction. Inference: log
  cluster bootstrap (weights per log, shared by all arms), one-sided simultaneous sup-t bounds (m_lib_v04._simul) over the
  cells of a family; zero-SE cells are flagged when the estimate exceeds delta.
  HK1a family: cells with M* records in >= 39 scenes from >= 8 logs whose power to be flagged at a true rate of 0.15 is
  >= 0.80, simulated from M*'s record counts only (beta-binomial, intra-scene correlation 0.3, 200 datasets, seed
  POWER_SEED). HK1a: at least F_MIN family cells and none flagged. HK1b: the pooled cell not flagged. HK1 = HK1a and HK1b.
  HK2: a practitioner arm (B0, B1, B4) flagged in a cell at the Bonferroni level 1 - 0.05/3, where M* is not flagged and
  the paired difference arm - M* is positive at the same level.
  HK3: the infeasible-decision rate (share of keyframes where no candidate satisfies the enforced constraints) of M* is
  lower than that of each of B0, B1, B4 and B9: per-scene paired differences M* - arm, log-bootstrap one-sided upper bound
  at level 1 - 0.05/4 below 0 for all four. (B3 dominates M* by construction and is reported, not tested.)
Closed loop (estimates). Progress, infeasible frames, hard braking, blocked time, collisions (at fault with tracked and
  with untracked agents, not at fault, artefacts: agents the LOG reference at the same delay overlaps), front buffer
  intrusions and sensor offset per arm; progress contrasts M* - arm with log-bootstrap intervals; in-loop records with
  sensor offset <= 15 m as a secondary consistency check.
Usage: python -B k6_analyse_v02.py --runs <dir> --tags <t1> <t3> --manifests <...> --out <json> --prereg <plan.md>
       [--allow-dev --boot B]   (development checks only). Runs are read as <tag>_decide and <tag>_loop.
"""
import argparse
import hashlib
import json
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import chi2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m_lib_v04 as M  # noqa: E402
import k6_sim_v02 as S  # noqa: E402

DELTA = 0.05
B_BOOT = 2000
SEED = 20261102
POWER_SEED = 20261104
MIN_SCENES, MIN_LOGS = 39, 8
POWER_P, POWER_MIN, POWER_RHO, POWER_REPS = 0.15, 0.80, 0.3, 200
F_MIN = 4
PRACTITIONER = ("B0", "B1", "B4")
LEVEL_HK2 = 1 - 0.05 / len(PRACTITIONER)
HK3_ARMS = ("B0", "B1", "B4", "B9")
LEVEL_HK3 = 1 - 0.05 / len(HK3_ARMS)
N_SCENES_CONF, DELAYS = 840, [0, 2, 4]
GROUPS, AXES, MOTIONS = ["car", "pedestrian", "two_wheeler", "large"], ["long", "lat"], ["static", "straight", "turning", "new"]
DEV_SCENES = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077",
              "scene-1094", "scene-1100")

'''
i = s.index("def sha(p):")
s = TOP + s[i:]

old_pop = s[s.index("POPULATIONS = {"):s.index("def episode_cell_table(")]
new_pop = '''STEPS_CC = tuple(range(S.CC_STEPS))
POP_DECIDE = {
    "PD_primary": dict(offset=(0,), gap=(0, 1, 2), steps=STEPS_CC),
    "SD1_gap_le_5m": dict(offset=(0,), gap=(0, 1), steps=STEPS_CC),
    "SD2_not_in_path": dict(offset=(0,), inpath=(0,), gap=(0, 1, 2), steps=STEPS_CC),
    "SD3_all_relied_any_enforcement": dict(offset=(0,), inpath=(0, 1), enforced=(0, 1), satisfied=(0, 1), gap=(0, 1, 2), steps=STEPS_CC),
}
POP_LOOP = {
    "PL_offset_le_15m": dict(offset=(0, 1), gap=(0, 1, 2), steps=STEPS_CC),
    "SL1_all_offsets": dict(offset=(0, 1, 2), gap=(0, 1, 2), steps=STEPS_CC),
}


'''
s = s.replace(old_pop, new_pop, 1)

j = s.index("def analyse_tracker(")
BOTTOM = '''def keys_and_weights(eps, log_of_scene, B, rng):
    keys = sorted({(o["scene"], o["delay_kf"]) for o in eps})
    scene_of_ep = np.array([k[0] for k in keys])
    logs = sorted(set(log_of_scene[s] for s in scene_of_ep))
    log_of_ep = np.array([logs.index(log_of_scene[s]) for s in scene_of_ep])
    W_logs = rng.multinomial(len(logs), np.full(len(logs), 1.0 / len(logs)), size=B).astype(float)
    return keys, scene_of_ep, logs, log_of_ep, W_logs


def populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W, pops):
    cells = cell_family()
    kidx = {k: i for i, k in enumerate(keys)}
    epi = {arm: {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps if o["arm"] == arm} for arm in arms}
    out = {}
    tabs = {}
    for pname, spec in pops.items():
        pop = mask(**spec)
        Nc, Xc = {}, {}
        for arm in arms:
            Nc[arm], Xc[arm] = episode_cell_table(counts, epi[arm], len(keys), cells, pop)
        il, est, boot, ev = inloop_population(Nc, Xc, cells, scene_of_ep, log_of_ep, W)
        ila, _, _, _ = inloop_population({a: Nc[a].sum(1, keepdims=True) for a in arms}, {a: Xc[a].sum(1, keepdims=True) for a in arms},
                                         [("all", list(range(S.N_L0)))], scene_of_ep, log_of_ep, W)
        out[pname] = {"cells_by_arm": il, "pooled_by_arm": {a: ila[a]["cells"].get("all") for a in arms}}
        tabs[pname] = (Nc, Xc, est, boot, ev)
    return out, tabs


def analyse_decide(eps, counts, log_of_scene, B, rng, prng):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES and o["arm"] != "LOG"]
    cells = cell_family()
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    keys, scene_of_ep, logs, log_of_ep, W_logs = keys_and_weights(eps, log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    res = {"scenes": len(keys), "logs": len(logs)}
    pops, tabs = populations(eps, counts, arms, keys, scene_of_ep, log_of_ep, W, POP_DECIDE)
    res["populations"] = pops
    Nc, Xc, est, boot, ev = tabs["PD_primary"]
    ev_m = ev["Mstar"]
    pw, _ = power_family(Nc["Mstar"], ev_m, scene_of_ep, W[:500], prng)
    fam_mask = ev_m & (pw >= POWER_MIN)
    il_m, _, _, _ = inloop_population({"Mstar": Nc["Mstar"]}, {"Mstar": Xc["Mstar"]}, cells, scene_of_ep, log_of_ep, W, family_from=fam_mask)
    res["HK1a_family_power_at_%.2f" % POWER_P] = {cells[j][0]: float(pw[j]) for j in np.flatnonzero(ev_m)}
    res["HK1a_family"] = [cells[j][0] for j in np.flatnonzero(fam_mask)]
    res["HK1a_Mstar"] = il_m["Mstar"]
    hk2 = {}
    for b in PRACTITIONER:
        if b not in arms:
            continue
        fb = np.flatnonzero(ev[b])
        sig_b = []
        if len(fb):
            _, _, _, sb, _ = flag(est[b], boot[b], fb, LEVEL_HK2)
            sig_b = [cells[j][0] for i, j in enumerate(fb) if sb[i]]
        pr = paired(est, boot, ev, cells, b, "Mstar", LEVEL_HK2)
        hk2[b] = {"flagged_bonferroni": sig_b, "paired": pr,
                  "fails_where_Mstar_holds": [c for c in sig_b if c not in pops["PD_primary"]["cells_by_arm"]["Mstar"]["sig_above_cells"]
                                              and pr.get(c, {}).get("positive", False)]}
    res["HK2"] = hk2
    # HK3: infeasible-decision rate, paired by scene
    inf = {(o["scene"], o["arm"]): (o["infeasible_frames"], o["frames"]) for o in eps}
    scenes = sorted({o["scene"] for o in eps})
    lg = np.array([logs.index(log_of_scene[sc]) for sc in scenes])
    Ws = W_logs[:, lg]
    rate = {a: np.array([inf[(sc, a)][0] / max(inf[(sc, a)][1], 1) for sc in scenes]) for a in arms}
    res["infeasible_rate"] = {a: {"mean": float(rate[a].mean()),
                                  "ci95": [float(x) for x in np.quantile((Ws @ rate[a]) / Ws.sum(1), [0.025, 0.975])]} for a in arms}
    hk3 = {}
    for b in [x for x in arms if x != "Mstar"]:
        d = rate["Mstar"] - rate[b]
        bm = (Ws @ d) / Ws.sum(1)
        ub = float(np.quantile(bm, LEVEL_HK3))
        hk3[b] = {"mean_diff": float(d.mean()), "ub_one_sided_bonferroni": ub, "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
                  "lower": bool(ub < 0), "tested": b in HK3_ARMS}
    res["HK3"] = hk3
    pooled = pops["PD_primary"]["pooled_by_arm"].get("Mstar")
    hk1a = len(res["HK1a_family"]) >= F_MIN and not il_m["Mstar"]["sig_above_cells"]
    hk1b = pooled is not None and not pooled["sig_above"]
    res["hypotheses"] = {"HK1a_family_size": len(res["HK1a_family"]), "HK1a_family_floor": F_MIN, "HK1a": bool(hk1a), "HK1b": bool(hk1b),
                         "HK1": bool(hk1a and hk1b), "HK1c_pooled_ub_le_delta_plus_0.03": bool(pooled is not None and pooled["ub_sim"] <= DELTA + 0.03),
                         "HK2": bool(any(v["fails_where_Mstar_holds"] for v in hk2.values())),
                         "HK3": bool(all(hk3.get(b, {}).get("lower", False) for b in HK3_ARMS))}
    return res


def analyse_loop(eps, counts, log_of_scene, B, rng):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES]
    arms = [a for a in S.ARMS if a != "LOG" and any(o["arm"] == a for o in eps)]
    keys, scene_of_ep, logs, log_of_ep, W_logs = keys_and_weights([o for o in eps if o["arm"] != "LOG"], log_of_scene, B, rng)
    W = W_logs[:, log_of_ep]
    res = {"episode_keys": len(keys), "logs": len(logs)}
    res["populations"], _ = populations([o for o in eps if o["arm"] != "LOG"], counts, arms, keys, scene_of_ep, log_of_ep, W, POP_LOOP)
    res["progress_vs_Mstar"] = progress_contrasts(eps, arms, log_of_scene, logs, W_logs)
    res["outcomes"] = outcome_summary(eps)
    return res


def decide(d1, d3):
    h1, h3 = d1["hypotheses"], d3["hypotheses"]
    if h1["HK1"] and h3["HK1"] and h1["HK3"] and h3["HK3"]:
        verdict = "K6 GO-A" if h1["HK2"] else "K6 GO-B"
    else:
        verdict = "K6 NO-GO"
    return {"verdict": verdict, "T1": h1, "T3": h3}


def check_binding(prereg, runs, tags):
    import k6_run_v02 as R
    side, hashes = R.frozen_hashes(prereg)
    rec = open(os.path.join(os.path.dirname(prereg), "K6_FREEZE_RECORD_v02.txt"), encoding="utf-8").read()
    assert side in rec, "the plan sidecar differs from the freeze record"
    for p in (os.path.abspath(__file__), M.__file__, S.__file__):
        assert sha(p) in hashes, "analysis input not frozen: " + p
    for tag in tags:
        for mode in ("decide", "loop"):
            rr = json.load(open(os.path.join(runs, "run_record_%s_%s.json" % (tag, mode))))
            assert rr["prereg"] == side and rr["mode"] == mode, "run %s_%s was not made under the frozen K6 plan" % (tag, mode)
            for k in ("fits_sha256", "sim_sha256", "runner_sha256"):
                assert rr[k] in hashes, "%s of run %s_%s is not frozen" % (k, tag, mode)
            assert all(h in hashes for h in rr["manifest_sha256"]), "a cache manifest of run %s_%s is not frozen" % (tag, mode)
            assert rr["arms"] == list(S.ARMS) and rr["delays_kf"] == DELAYS and rr["scenes"] == N_SCENES_CONF, "incomplete design " + tag
            n_ep = N_SCENES_CONF * len(S.ARMS) * len(DELAYS) if mode == "loop" else N_SCENES_CONF * (len(S.ARMS) - 1)
            assert rr["episodes"] == n_ep, "incomplete run %s_%s" % (tag, mode)
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
    a = ap.parse_args()
    global DEV_SCENES, MIN_SCENES, MIN_LOGS
    if a.allow_dev:
        DEV_SCENES, MIN_SCENES, MIN_LOGS = (), 2, 1
        side = None
    else:
        assert a.boot == B_BOOT, "the bootstrap size is fixed at %d" % B_BOOT
        assert a.prereg, "the confirmatory analysis needs --prereg"
        side = check_binding(a.prereg, a.runs, a.tags)
    log_of_scene = {}
    for p in a.manifests:
        for s_, info in json.load(open(p))["scenes"].items():
            log_of_scene[s_] = info["log"]
    out = {"delta": DELTA, "boot": a.boot, "prereg_sha256": side, "decide": {}, "loop": {}}
    for i, tag in enumerate(a.tags):
        for mode in ("decide", "loop"):
            eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s_%s.jsonl" % (tag, mode)))]
            counts = dict(np.load(os.path.join(a.runs, "counts_%s_%s.npz" % (tag, mode))))
            if mode == "decide":
                out["decide"][tag] = analyse_decide(eps, counts, log_of_scene, a.boot, np.random.default_rng([SEED, i, 0]),
                                                    np.random.default_rng([POWER_SEED, i]))
            else:
                out["loop"][tag] = analyse_loop(eps, counts, log_of_scene, a.boot, np.random.default_rng([SEED, i, 1]))
    out["decision"] = decide(out["decide"][a.tags[0]], out["decide"][a.tags[1]])
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(out["decision"], indent=1))
    print("K6 ANALYSIS DONE")


if __name__ == "__main__":
    main()
'''
s = s[:j] + BOTTOM
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("analysis v02 rewritten")
