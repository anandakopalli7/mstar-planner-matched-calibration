#!/usr/bin/env python3
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
  HK1a (R09b MJ3): no cell flagged in M*'s sup-t over ALL its evaluable cells (>= 39 scenes, >= 8 logs), AND at least
  F_MIN power-qualified cells: evaluable cells whose power to be flagged at a true rate of 0.15 is >= 0.80, simulated from
  M*'s record counts only (beta-binomial, intra-scene correlation 0.5 (R09b m2), 200 datasets, seed POWER_SEED). The
  power-qualified cells are those whose non-rejection is claimed; a flag in any evaluable cell fails HK1a.
  HK1b: the pooled cell not flagged. HK1 = HK1a and HK1b.
  HK2: a practitioner arm (B0, B1, B4) flagged in a cell at the Bonferroni level 1 - 0.05/3 (sup-t over its evaluable
  cells), where M* is not flagged in its own all-evaluable sup-t at level 0.95, and the paired difference arm - M* is
  positive at level 1 - 0.05/3 (sup-t over the cells evaluable for both).
  HK3: the infeasible-decision rate (share of keyframes where no candidate satisfies the enforced constraints) of M* is
  lower than that of each of B0, B1, B4 and B9: per-scene paired differences M* - arm, log-bootstrap one-sided upper bound
  at level 1 - 0.05/4 below 0 for all four. (B3 dominates M* by construction and is reported, not tested.)
Closed loop (estimates). Progress, infeasible frames, emergency stops, hard braking, blocked time, collisions (at fault
  with tracked agents, split into fallback-related -- within 2 s of an infeasible decision, when the planner ran at a
  backed-off margin -- and not; with untracked agents; not at fault; artefacts: agents the LOG reference at the same delay
  overlaps). Closed-loop safety contrasts between arms are descriptive and are not interpreted as calibration effects:
  an arm that is infeasible more often runs more often at a backed-off margin (R09b MJ1). Front buffer
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
POWER_P, POWER_MIN, POWER_RHO, POWER_REPS = 0.15, 0.80, 0.5, 200
F_MIN = 6
PRACTITIONER = ("B0", "B1", "B4")
LEVEL_HK2 = 1 - 0.05 / len(PRACTITIONER)
HK3_ARMS = ("B0", "B1", "B4", "B9")
LEVEL_HK3 = 1 - 0.05 / len(HK3_ARMS)
N_SCENES_CONF, DELAYS = 840, [0, 2, 4]
EXPERIMENT = {"t1": "paper/local/canmot/sc", "t3": "paper/baseline/poly_mot"}
GROUPS, AXES, MOTIONS = ["car", "pedestrian", "two_wheeler", "large"], ["long", "lat"], ["static", "straight", "turning", "new"]
DEV_SCENES = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077",
              "scene-1094", "scene-1100")

def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def cell_family():
    cells = []
    for g in range(4):
        for a in range(2):
            for m in range(4):
                cells.append(("%s|%s|%s" % (GROUPS[g], AXES[a], MOTIONS[m]), [((g * 3 + r) * 2 + a) * 4 + m for r in range(3)]))
    return cells


def mask(offset=(0, 1), inpath=(1,), enforced=(1,), satisfied=(1,), gap=(0, 1), relied=(1,), steps=tuple(range(S.N_STEP))):
    keep = np.zeros(S.N_CELL, bool)
    for c in range(S.N_CELL):
        ob, inp, enf, sat, gb, rel, h, _ = S.decode_cell(c)
        keep[c] = ob in offset and inp in inpath and enf in enforced and sat in satisfied and gb in gap and rel in relied and h in steps
    return keep


STEPS_CC = tuple(range(S.CC_STEPS))
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


def episode_cell_table(counts, ep_index, n_ep, cells, pop):
    l0_to_cell = np.full(S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    ep, cell, n, x = counts["episode"], counts["cell"], counts["n"], counts["exceed"]
    sel = pop[cell] & np.isin(ep, list(ep_index))
    ep, cell, n, x = ep[sel], cell[sel], n[sel], x[sel]
    col = l0_to_cell[cell % S.N_L0]
    ok = col >= 0
    row = np.array([ep_index[e] for e in ep[ok]], int) if ok.any() else np.zeros(0, int)
    N = np.zeros((n_ep, len(cells)))
    X = np.zeros((n_ep, len(cells)))
    np.add.at(N, (row, col[ok]), n[ok])
    np.add.at(X, (row, col[ok]), x[ok])
    return N, X


def rates(N, X, W):
    p = np.divide(X, N, out=np.zeros_like(X), where=N > 0)
    pres = (N > 0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (W @ p) / (W @ pres)


def evaluable(N, scene_of_ep, log_of_ep):
    pres = N > 0
    return np.array([len(set(scene_of_ep[pres[:, j]])) >= MIN_SCENES and len(set(log_of_ep[pres[:, j]])) >= MIN_LOGS for j in range(N.shape[1])])


def flag(est, boot, fam, level):
    lb, se, q, ok = M._simul(est[fam], boot[:, fam], level, "lower")
    ub, _, qu, _ = M._simul(est[fam], boot[:, fam], level, "upper")
    sig = (ok & (lb > DELTA)) | (~ok & (est[fam] > DELTA))
    return lb, ub, se, sig, q


def power_family(N, ev, scene_of_ep, W, rng):
    """Per-cell power to be flagged at a true rate POWER_P, from record counts only (see the module docstring)."""
    fam = np.flatnonzero(ev)
    if not len(fam):
        return np.zeros(N.shape[1]), fam
    scenes = sorted(set(scene_of_ep))
    sidx = np.array([scenes.index(s) for s in scene_of_ep])
    a = POWER_P * (1 - POWER_RHO) / POWER_RHO
    b = (1 - POWER_P) * (1 - POWER_RHO) / POWER_RHO
    hits = np.zeros(N.shape[1])
    for _ in range(POWER_REPS):
        P = rng.beta(a, b, size=(len(scenes), N.shape[1]))[sidx]
        X = rng.binomial(N.astype(int), P).astype(float)
        est, boot = rates(N, X, np.ones((1, N.shape[0])))[0], rates(N, X, W)
        _, _, _, sig, _ = flag(est, boot, fam, 0.95)
        hits[fam] += sig
    return hits / POWER_REPS, fam


def inloop_population(Nc, Xc, cells, scene_of_ep, log_of_ep, W, family_from=None):
    one = np.ones((1, len(scene_of_ep)))
    est = {arm: rates(Nc[arm], Xc[arm], one)[0] for arm in Nc}
    boot = {arm: rates(Nc[arm], Xc[arm], W) for arm in Nc}
    ev = {arm: evaluable(Nc[arm], scene_of_ep, log_of_ep) for arm in Nc}
    res = {}
    for arm in Nc:
        fam = np.flatnonzero(ev[arm] if family_from is None else family_from)
        r = {"family": [cells[j][0] for j in fam], "cells": {}, "descriptive": {}}
        if len(fam):
            lb, ub, se, sig, q = flag(est[arm], boot[arm], fam, 0.95)
            for i, j in enumerate(fam):
                r["cells"][cells[j][0]] = {"E": float(est[arm][j]), "lb_sim": float(lb[i]), "ub_sim": float(ub[i]), "se": float(se[i]),
                                           "sig_above": bool(sig[i]), "records": int(Nc[arm][:, j].sum()), "exceed": int(Xc[arm][:, j].sum()),
                                           "E_rec": float(Xc[arm][:, j].sum() / max(Nc[arm][:, j].sum(), 1)),
                                           "scenes": int(len(set(scene_of_ep[Nc[arm][:, j] > 0])))}
            r["sig_above_cells"] = [cells[j][0] for i, j in enumerate(fam) if sig[i]]
            r["q"] = float(q)
        else:
            r["sig_above_cells"] = []
        for j in range(len(cells)):
            if j not in set(fam.tolist()):
                r["descriptive"][cells[j][0]] = {"E": float(est[arm][j]) if np.isfinite(est[arm][j]) else None,
                                                 "records": int(Nc[arm][:, j].sum()), "scenes": int(len(set(scene_of_ep[Nc[arm][:, j] > 0])))}
        res[arm] = r
    return res, est, boot, ev


def paired(est, boot, ev, cells, base, ref, level):
    both = ev[base] & ev[ref]
    if not both.any():
        return {}
    fam = np.flatnonzero(both)
    d = est[base][fam] - est[ref][fam]
    db = boot[base][:, fam] - boot[ref][:, fam]
    lb, se, q, ok = M._simul(d, db, level, "lower")
    pos = (ok & (lb > 0)) | (~ok & (d > 0))
    return {cells[j][0]: {"diff": float(d[i]), "lb_sim": float(lb[i]), "positive": bool(pos[i])} for i, j in enumerate(fam)}


def poisson_ci(k, n, level=0.95):
    a = 1 - level
    lo = 0.0 if k == 0 else chi2.ppf(a / 2, 2 * k) / 2
    hi = chi2.ppf(1 - a / 2, 2 * k + 2) / 2
    return [1000.0 * lo / n, 1000.0 * hi / n]


def outcome_summary(eps):
    art = defaultdict(set)
    for o in eps:
        if o["arm"] == "LOG":
            art[(o["scene"], o["delay_kf"])] |= {c["inst"] for c in o["collisions"]}
    by_arm = defaultdict(list)
    for o in eps:
        by_arm[o["arm"]].append(o)
    res = {}
    for arm, Lst in by_arm.items():
        n = len(Lst)
        prog = [o["progress"] for o in Lst if o["progress"] is not None]
        real = [c for o in Lst for c in o["collisions"] if c["inst"] not in art[(o["scene"], o["delay_kf"])]]
        aft = sum(c["at_fault"] and c["tracked"] for c in real)
        aft_fb = sum(c["at_fault"] and c["tracked"] and c.get("fallback_related", False) for c in real)
        afu = sum(c["at_fault"] and not c["tracked"] for c in real)
        res[arm] = {"episodes": n, "progress_mean": float(np.mean(prog)) if prog else None, "progress_episodes": len(prog),
                    "at_fault_tracked": aft, "at_fault_tracked_per_1000": 1000.0 * aft / n, "at_fault_tracked_ci": poisson_ci(aft, n),
                    "at_fault_tracked_fallback_related": aft_fb, "at_fault_tracked_not_fallback": aft - aft_fb,
                    "at_fault_untracked": afu, "at_fault_untracked_per_1000": 1000.0 * afu / n, "at_fault_untracked_ci": poisson_ci(afu, n),
                    "not_at_fault": sum(not c["at_fault"] for c in real), "artefact_collisions": sum(o["n_collisions"] for o in Lst) - len(real),
                    "front_buffer_intrusions_per_episode": float(np.mean([o["n_front_buffer_intrusions"] for o in Lst])),
                    "infeasible_frame_share": float(sum(o["infeasible_frames"] for o in Lst) / max(sum(o["frames"] for o in Lst), 1)),
                    "emergency_stop_frame_share": float(sum(o.get("emergency_stop_frames", 0) for o in Lst) / max(sum(o["frames"] for o in Lst), 1)),
                    "backoff_frame_share": float(sum(o["infeasible_frames"] - o.get("emergency_stop_frames", 0) for o in Lst)
                                                 / max(sum(o["frames"] for o in Lst), 1)),
                    "hard_brake_frame_share": float(sum(o["hard_brake_frames"] for o in Lst) / max(sum(o["frames"] for o in Lst), 1)),
                    "blocked_s_mean": float(np.mean([o["blocked_s"] for o in Lst])),
                    "mean_abs_acc": float(np.mean([o["mean_abs_acc"] for o in Lst])),
                    "sensor_offset_median_of_medians": float(np.median([o["sensor_offset_median"] for o in Lst if o.get("sensor_offset_median") is not None]))
                    if arm != "LOG" else None,
                    "share_frames_offset_gt15": float(np.mean([o["sensor_offset_share_gt15"] for o in Lst if o.get("sensor_offset_share_gt15") is not None]))
                    if arm != "LOG" else None}
    return res


def progress_contrasts(eps, arms, log_of_scene, logs, W_logs):
    key = {(o["scene"], o["delay_kf"], o["arm"]): o["progress"] for o in eps}
    out = {}
    for b in arms:
        if b == "Mstar":
            continue
        rows = sorted((s, d) for (s, d, arm) in key if arm == "Mstar" and key.get((s, d, b)) is not None and key[(s, d, "Mstar")] is not None)
        if not rows:
            continue
        diff = np.array([key[(s, d, "Mstar")] - key[(s, d, b)] for s, d in rows])
        lg = np.array([logs.index(log_of_scene[s]) for s, _ in rows])
        Wd = W_logs[:, lg]
        bm = (Wd @ diff) / Wd.sum(1)
        out["Mstar-%s" % b] = {"mean_diff": float(diff.mean()), "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])],
                               "lb95_one_sided": float(np.quantile(bm, 0.05)), "episodes": len(rows)}
    return out


def keys_and_weights(eps, log_of_scene, B, rng):
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
    res["HK1a_Mstar_power_qualified"] = il_m["Mstar"]
    res["HK1a_Mstar_all_evaluable"] = pops["PD_primary"]["cells_by_arm"]["Mstar"]
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
    hk1a = (len(res["HK1a_family"]) >= F_MIN and not il_m["Mstar"]["sig_above_cells"]
            and not pops["PD_primary"]["cells_by_arm"]["Mstar"]["sig_above_cells"])
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


def check_binding(prereg, runs, tags, manifests):
    import k6_run_v02 as R
    assert list(tags) == ["t1", "t3"], "the tags must be t1 t3, in this order (HK2 is read on T1)"
    side, hashes = R.frozen_hashes(prereg)
    for p in manifests:
        assert sha(p) in hashes, "a manifest passed to the analysis is not frozen: " + p
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
            assert rr["tag"] == "%s_%s" % (tag, mode), "run record %s_%s carries another tag" % (tag, mode)
            same_tracker = ("_%s_" % tag) in os.path.basename(rr["fits"]) and all(("cache_v02_%s_" % tag) in c for c in rr["caches"])
            fits_tags = json.load(open(rr["fits"]))["tags"]
            exps = {json.load(open(os.path.join(c, "MANIFEST.json")))["experiment"] for c in rr["caches"]}
            same_tracker &= fits_tags == ["%s_train" % tag, "%s_val" % tag] and exps == {EXPERIMENT[tag]}   # by content (R09c N5)
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
    a = ap.parse_args()
    global DEV_SCENES, MIN_SCENES, MIN_LOGS
    if a.allow_dev:
        DEV_SCENES, MIN_SCENES, MIN_LOGS = (), 2, 1
        side = None
    else:
        assert a.boot == B_BOOT, "the bootstrap size is fixed at %d" % B_BOOT
        assert a.prereg, "the confirmatory analysis needs --prereg"
        side = check_binding(a.prereg, a.runs, a.tags, a.manifests)
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
