#!/usr/bin/env python3
"""K6 analysis (Claude line, v01, 31 Oct 2026). Implements the K6 plan's endpoints, inference and decision rule.

In-loop exceedance (HK1, HK2). Records of the executed plans (k6_sim_v01._record) in the primary population: the
relied-on axis of each (track, step) pair whose footprint gap to the planned ego is <= 5 m (gap bins 0 and 1), all 8
steps. Per cell (union of L0 strata), the episode-level rate is the mean over episodes with records in the cell of the
episode's exceedance fraction (the method stage's scene-level estimand, with episodes in place of scenes). Inference: log
cluster bootstrap (weights per log, shared by every arm and both inferences), one-sided simultaneous sup-t bounds over the
cells evaluable for that arm (m_lib_v04._simul), zero-SE cells flagged when the estimate exceeds delta. A cell is
evaluable for an arm when it has records in >= 39 scenes from >= 8 logs. Paired contrasts (baseline - M*) use the same
bootstrap weights, simultaneous over the cells evaluable for both arms.

Price (HK3). Mean progress ratio over episodes with progress defined (entered, logged travel >= 10 m); paired differences
per (scene, delay) with log-bootstrap one-sided 95 % lower bounds.

Safety outcomes (descriptive). At-fault collisions (all, and with tracked agents) per 1000 episodes with exact Poisson
intervals; front buffer intrusions, infeasible frames, hard braking, blocked time. A collision with an agent that the LOG
reference (the logged ego itself, delay 0) also overlaps is a geometry artefact (box sizes, annotation noise): such
collisions are counted separately and left out of the at-fault counts.
Usage: python -B k6_analyse_v01.py --runs <dir> --tags <t1 tag> <t3 tag> --manifests <manifest...> --out <json>
       [--prereg <plan.md>] [--boot B]
"""
import argparse
import json
import math
import os
import sys
from collections import defaultdict

import numpy as np
from scipy.stats import chi2

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "m"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m_lib_v04 as M  # noqa: E402
import k6_sim_v01 as S  # noqa: E402

DELTA = 0.05
B_BOOT = 2000
SEED = 20261102
MIN_SCENES, MIN_LOGS = 39, 8
PRACTITIONER = ("B0", "B1", "B4")
CERTIFIED = ("B3", "B9")
GROUPS, AXES, MOTIONS = ["car", "pedestrian", "two_wheeler", "large"], ["long", "lat"], ["static", "straight", "turning", "new"]
DEV_SCENES = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077",
              "scene-1094", "scene-1100")


def cell_family():
    cells = []
    for g in range(4):
        for a in range(2):
            for m in range(4):
                cells.append(("%s|%s|%s" % (GROUPS[g], AXES[a], MOTIONS[m]), [((g * 3 + r) * 2 + a) * 4 + m for r in range(3)]))
    return cells


def population_mask(gap_bins=(0, 1), relied=(1,), steps=tuple(range(S.N_STEP))):
    keep = np.zeros(S.N_CELL, bool)
    for c in range(S.N_CELL):
        gb, rel, h, _ = S.decode_cell(c)
        keep[c] = gb in gap_bins and rel in relied and h in steps
    return keep


def episode_cell_table(counts, ep_index, n_ep, cells, pop):
    """n[e, j] and x[e, j]: records and exceedances of episode e in cell j, over the population mask."""
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
    """Episode-level rate per cell for every row of W (B x episodes)."""
    p = np.divide(X, N, out=np.zeros_like(X), where=N > 0)
    pres = (N > 0).astype(float)
    with np.errstate(invalid="ignore", divide="ignore"):
        return (W @ p) / (W @ pres)


def boot_weights(log_of_ep, n_logs, B, rng):
    m = rng.multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=B).astype(float)
    return m[:, log_of_ep]


def inloop(N_by_arm, X_by_arm, cells, scene_of_ep, log_of_ep, W, level=0.95):
    out = {}
    one = np.ones((1, len(scene_of_ep)))
    est, boot, evaluable = {}, {}, {}
    for arm in N_by_arm:
        N, X = N_by_arm[arm], X_by_arm[arm]
        pres = N > 0
        ev = np.array([len(set(scene_of_ep[pres[:, j]])) >= MIN_SCENES and len(set(log_of_ep[pres[:, j]])) >= MIN_LOGS
                       for j in range(len(cells))])
        evaluable[arm] = ev
        est[arm] = rates(N, X, one)[0]
        boot[arm] = rates(N, X, W)
        res = {"cells": {}, "evaluable": [cells[j][0] for j in np.flatnonzero(ev)]}
        if ev.any():
            lb, se, q, ok = M._simul(est[arm][ev], boot[arm][:, ev], level, "lower")
            ub, _, qu, _ = M._simul(est[arm][ev], boot[arm][:, ev], level, "upper")
            sig = (ok & (lb > DELTA)) | (~ok & (est[arm][ev] > DELTA))
            for i, j in enumerate(np.flatnonzero(ev)):
                res["cells"][cells[j][0]] = {"E": float(est[arm][j]), "lb_sim": float(lb[i]), "ub_sim": float(ub[i]), "se": float(se[i]),
                                             "sig_above": bool(sig[i]), "records": int(N[:, j].sum()), "exceed": int(X[:, j].sum()),
                                             "E_rec": float(X[:, j].sum() / max(N[:, j].sum(), 1)),
                                             "episodes": int(pres[:, j].sum()), "scenes": int(len(set(scene_of_ep[pres[:, j]]))),
                                             "logs": int(len(set(log_of_ep[pres[:, j]])))}
            res["q_lower"], res["q_upper"] = float(q), float(qu)
            res["sig_above_cells"] = [cells[j][0] for i, j in enumerate(np.flatnonzero(ev)) if sig[i]]
        else:
            res["sig_above_cells"] = []
        res["descriptive_cells"] = {cells[j][0]: {"E": float(est[arm][j]) if np.isfinite(est[arm][j]) else None, "records": int(N[:, j].sum()),
                                                  "scenes": int(len(set(scene_of_ep[pres[:, j]])))} for j in np.flatnonzero(~ev)}
        out[arm] = res
    return out, est, boot, evaluable


def paired_inloop(est, boot, evaluable, cells, base, ref="Mstar", level=0.95):
    both = evaluable[base] & evaluable[ref]
    if not both.any():
        return {}
    d = est[base][both] - est[ref][both]
    db = boot[base][:, both] - boot[ref][:, both]
    lb, se, q, ok = M._simul(d, db, level, "lower")
    pos = (ok & (lb > 0)) | (~ok & (d > 0))
    return {cells[j][0]: {"diff": float(d[i]), "lb_sim": float(lb[i]), "positive": bool(pos[i])} for i, j in enumerate(np.flatnonzero(both))}


def poisson_ci(k, n, level=0.95):
    a = 1 - level
    lo = 0.0 if k == 0 else chi2.ppf(a / 2, 2 * k) / 2
    hi = chi2.ppf(1 - a / 2, 2 * k + 2) / 2
    return [1000.0 * lo / n, 1000.0 * hi / n]


def artefacts(eps):
    """Per scene, the agents the logged ego (LOG arm, delay 0) overlaps."""
    art = defaultdict(set)
    for o in eps:
        if o["arm"] == "LOG" and o["delay_kf"] == 0:
            art[o["scene"]] |= {c["inst"] for c in o["collisions"]}
    return art


def outcome_summary(eps, art):
    by_arm = defaultdict(list)
    for o in eps:
        by_arm[o["arm"]].append(o)
    res = {}
    for arm, L in by_arm.items():
        n = len(L)
        prog = [o["progress"] for o in L if o["progress"] is not None]
        real = [c for o in L for c in o["collisions"] if c["inst"] not in art[o["scene"]]]
        af = sum(c["at_fault"] for c in real)
        aft = sum(c["at_fault"] and c["tracked"] for c in real)
        res[arm] = {"episodes": n, "progress_mean": float(np.mean(prog)) if prog else None, "progress_episodes": len(prog),
                    "share_progress_below_0.9": float(np.mean(np.array(prog) < 0.9)) if prog else None,
                    "blocked_s_mean": float(np.mean([o["blocked_s"] for o in L])),
                    "infeasible_frame_share": float(sum(o["infeasible_frames"] for o in L) / max(sum(o["frames"] for o in L), 1)),
                    "hard_brake_frame_share": float(sum(o["hard_brake_frames"] for o in L) / max(sum(o["frames"] for o in L), 1)),
                    "mean_abs_acc": float(np.mean([o["mean_abs_acc"] for o in L])),
                    "at_fault": af, "at_fault_per_1000": 1000.0 * af / n, "at_fault_ci": poisson_ci(af, n),
                    "at_fault_tracked": aft, "at_fault_tracked_per_1000": 1000.0 * aft / n, "at_fault_tracked_ci": poisson_ci(aft, n),
                    "collisions_all": sum(o["n_collisions"] for o in L), "collisions_artefact": sum(o["n_collisions"] for o in L) - len(real),
                    "collisions_not_at_fault": len(real) - af,
                    "front_buffer_intrusions_per_episode": float(np.mean([o["n_front_buffer_intrusions"] for o in L]))}
    return res


def progress_contrasts(eps, pairs, log_of_scene, logs, W_logs):
    key = {(o["scene"], o["delay_kf"], o["arm"]): o["progress"] for o in eps}
    out = {}
    for a, b in pairs:
        rows = [(s, d) for (s, d, arm) in key if arm == a and key.get((s, d, b)) is not None and key[(s, d, a)] is not None]
        rows.sort()
        if not rows:
            continue
        diff = np.array([key[(s, d, a)] - key[(s, d, b)] for s, d in rows])
        lg = np.array([logs.index(log_of_scene[s]) for s, _ in rows])
        Wd = W_logs[:, lg]
        bm = (Wd @ diff) / Wd.sum(1)
        out["%s-%s" % (a, b)] = {"mean_diff": float(diff.mean()), "lb95_one_sided": float(np.quantile(bm, 0.05)),
                                 "ci95": [float(x) for x in np.quantile(bm, [0.025, 0.975])], "episodes": len(rows),
                                 "positive": bool(np.quantile(bm, 0.05) > 0)}
    return out


def analyse_tracker(eps, counts, log_of_scene, B, rng):
    eps = [o for o in eps if o["entered"] and o["scene"] not in DEV_SCENES]
    cells = cell_family()
    pop = population_mask()
    all_cell = [("all", list(range(S.N_L0)))]
    arms = sorted({o["arm"] for o in eps if o["arm"] != "LOG"}, key=lambda x: S.ARMS.index(x))
    keys = sorted({(o["scene"], o["delay_kf"]) for o in eps})
    kidx = {k: i for i, k in enumerate(keys)}
    scene_of_ep = np.array([k[0] for k in keys])
    logs = sorted(set(log_of_scene[s] for s in scene_of_ep))
    log_of_ep = np.array([logs.index(log_of_scene[s]) for s in scene_of_ep])
    W_logs = rng.multinomial(len(logs), np.full(len(logs), 1.0 / len(logs)), size=B).astype(float)
    W = W_logs[:, log_of_ep]
    Nc, Xc, Na, Xa = {}, {}, {}, {}
    for arm in arms:
        epi = {o["episode"]: kidx[(o["scene"], o["delay_kf"])] for o in eps if o["arm"] == arm}
        Nc[arm], Xc[arm] = episode_cell_table(counts, epi, len(keys), cells, pop)
        Na[arm], Xa[arm] = episode_cell_table(counts, epi, len(keys), all_cell, pop)
    il, est, boot, ev = inloop(Nc, Xc, cells, scene_of_ep, log_of_ep, W)
    il_all, est_a, boot_a, ev_a = inloop(Na, Xa, all_cell, scene_of_ep, log_of_ep, W)
    paired = {b: paired_inloop(est, boot, ev, cells, b) for b in arms if b not in ("Mstar",)}
    prog = progress_contrasts(eps, [("Mstar", b) for b in arms if b != "Mstar"], log_of_scene, logs, W_logs)
    res = {"episodes": len(eps), "episode_keys": len(keys), "scenes": int(len(set(scene_of_ep))), "logs": len(logs),
           "inloop_cells": il, "inloop_all": il_all, "paired_vs_Mstar": paired, "progress_vs_Mstar": prog,
           "outcomes": outcome_summary(eps, artefacts(eps)), "artefact_agents": int(sum(len(v) for v in artefacts(eps).values()))}
    # hypotheses
    m = il.get("Mstar", {})
    hk1a = len(m.get("sig_above_cells", ["missing"])) == 0 if "Mstar" in il else False
    ma = il_all.get("Mstar", {}).get("cells", {}).get("all")
    hk1b = ma is not None and not ma["sig_above"]
    fails = {}
    for b in PRACTITIONER:
        if b not in il:
            continue
        fails[b] = [c for c in il[b].get("sig_above_cells", []) if c not in m.get("sig_above_cells", [])
                    and paired.get(b, {}).get(c, {}).get("positive", False)]
    hk3 = {b: prog.get("Mstar-%s" % b, {}).get("positive", False) for b in CERTIFIED}
    res["hypotheses"] = {"HK1a_no_Mstar_cell_above_delta": hk1a, "HK1b_Mstar_pooled_not_above_delta": hk1b,
                         "HK1": bool(hk1a and hk1b), "HK2_practitioner_failures": fails, "HK2": bool(any(fails.values())),
                         "HK3_progress_gain_vs_certified": hk3, "HK3": bool(all(hk3.values()) and len(hk3) == len(CERTIFIED))}
    return res


def decide(r1, r3):
    h1, h3 = r1["hypotheses"], r3["hypotheses"]
    go = h1["HK1"] and h3["HK1"] and h1["HK3"] and h3["HK3"]
    if go and h1["HK2"]:
        verdict = "K6 GO-A"
    elif go:
        verdict = "K6 GO-B"
    else:
        verdict = "K6 NO-GO"
    return {"verdict": verdict, "T1": h1, "T3": h3}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", required=True)
    ap.add_argument("--tags", nargs=2, required=True)
    ap.add_argument("--manifests", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--boot", type=int, default=B_BOOT)
    ap.add_argument("--allow-dev", action="store_true", help="development check only: analyse the mini scenes")
    ap.add_argument("--prereg", default=None, help="the frozen K6 plan; every run record must carry its hash")
    a = ap.parse_args()
    if not a.allow_dev:
        assert a.prereg, "the confirmatory analysis needs --prereg"
        side = open(a.prereg.replace(".md", ".sha256")).read().split()[0]
        for tag in a.tags:
            rr = json.load(open(os.path.join(a.runs, "run_record_%s.json" % tag)))
            assert rr["prereg"] == side, "run %s was not made under the frozen K6 plan" % tag
    log_of_scene = {}
    for p in a.manifests:
        for s, info in json.load(open(p))["scenes"].items():
            log_of_scene[s] = info["log"]
    if a.allow_dev:
        global DEV_SCENES
        DEV_SCENES = ()
    out = {"delta": DELTA, "boot": a.boot, "prereg_sha256": None if a.allow_dev else side}
    res = {}
    for i, tag in enumerate(a.tags):
        eps = [json.loads(l) for l in open(os.path.join(a.runs, "episodes_%s.jsonl" % tag))]
        counts = dict(np.load(os.path.join(a.runs, "counts_%s.npz" % tag)))
        rng = np.random.default_rng([SEED, i])
        res[tag] = analyse_tracker(eps, counts, log_of_scene, a.boot, rng)
    out["trackers"] = res
    out["decision"] = decide(res[a.tags[0]], res[a.tags[1]])
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps(out["decision"], indent=1))
    print("K6 ANALYSIS DONE")


if __name__ == "__main__":
    main()
