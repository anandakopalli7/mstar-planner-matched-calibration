#!/usr/bin/env python3
"""K6 operating characteristics (Claude line, v01, 31 Oct 2026). Simulated exceedances on a real record layout; no real
outcome is used. The layout is each scene's count of open-loop calibration items per L0 stratum summed over the 8 planner
steps (k6_items_v01, in-path paired tracks), scaled by a factor (the relied-on near records are a subset), and repeated for
the 3 delays. Each scene draws one exceedance probability per cell from a beta distribution with mean p and
intra-scene correlation rho; records are binomial, drawn once per scene and copied to its 3 delay episodes (the delays of a
scene see the same tracker errors, so this is the conservative extreme of full correlation across delays). The K6 analysis functions
(k6_analyse_v01.inloop, paired_inloop) are applied unchanged.
Reports, per tracker layout and scale:
  A1  the M* null flag rate: any evaluable cell flagged, or the pooled cell flagged, with every cell at p = delta;
  A2  the power to flag a planted cell (car|lat|turning at 0.10, 0.15 or 0.20) for a baseline, with the paired contrast
      positive.
Usage: python -B k6_oc_v01.py --items <dir> --tags <tag...> --out <json> [--reps R] [--boot B]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import k6_analyse_v01 as A  # noqa: E402
import k6_sim_v01 as S  # noqa: E402

STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]


def layout(items_dir, tags):
    import m_lib_v04 as M
    per_scene = {}
    names, logs_of = [], {}
    for tag in tags:
        sm = json.load(open(os.path.join(items_dir, "items_%s_summary.json" % tag)))
        off = len(names)
        names += sm["scene_names"]
        logs_of.update(sm["scene_log"])
        for h in STEPS:
            z = np.load(os.path.join(items_dir, "items_%s_%s.npz" % (tag, h)))
            it = {k: z["item_" + k] for k in ("g", "r", "a", "spd", "omc", "chord")}
            m = M.motion_state(it)
            l0 = ((it["g"] * 3 + it["r"]) * 2 + it["a"]) * 4 + m
            s = z["item_s"] + off
            np.add.at(_acc(per_scene, len(names)), (s, l0), 1)
    keep = [i for i, n in enumerate(names) if n not in A.DEV_SCENES]
    cnt = per_scene["acc"][keep]
    nm = [names[i] for i in keep]
    return cnt, nm, logs_of


def _acc(d, n_sc):
    if "acc" not in d or d["acc"].shape[0] < n_sc:
        old = d.get("acc", np.zeros((0, S.N_L0)))
        new = np.zeros((n_sc, S.N_L0))
        new[: old.shape[0]] = old
        d["acc"] = new
    return d["acc"]


def simulate(cnt_cells, rng, p_cells, rho):
    """cnt_cells: (scenes, cells) record counts per episode; returns X for 3 delay episodes per scene (stacked)."""
    n_sc, n_c = cnt_cells.shape
    if rho > 0:
        a = p_cells * (1 - rho) / rho
        b = (1 - p_cells) * (1 - rho) / rho
        P = rng.beta(np.broadcast_to(a, (n_sc, n_c)), np.broadcast_to(b, (n_sc, n_c)))
    else:
        P = np.broadcast_to(p_cells, (n_sc, n_c))
    X = rng.binomial(cnt_cells.astype(int), P)
    return np.repeat(cnt_cells, 3, axis=0), np.repeat(X, 3, axis=0).astype(float)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--tags", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=200)
    ap.add_argument("--boot", type=int, default=500)
    a = ap.parse_args()
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "m"))
    res = {"reps": a.reps, "boot": a.boot, "layouts": {}}
    cells = A.cell_family()
    all_cell = [("all", list(range(S.N_L0)))]
    target = [i for i, (n, _) in enumerate(cells) if n == "car|lat|turning"][0]
    for pair in [a.tags[i:i + 2] for i in range(0, len(a.tags), 2)]:
        cnt, names, logs_of = layout(a.items, pair)
        logs = sorted(set(logs_of[s] for s in names))
        scene_of_ep = np.repeat(np.array(names), 3)
        log_of_ep = np.repeat(np.array([logs.index(logs_of[s]) for s in names]), 3)
        for scale in (0.25, 1.0):
            base = np.zeros((len(names), len(cells)))
            for j, (_, ids) in enumerate(cells):
                base[:, j] = cnt[:, ids].sum(1)
            base = np.round(base * scale)
            for rho in (0.1, 0.3):
                rng = np.random.default_rng([20261103, int(scale * 100), int(rho * 10)])
                null_flag = pooled_flag = 0
                power = {0.10: 0, 0.15: 0, 0.20: 0}
                for r in range(a.reps):
                    W = A.boot_weights(log_of_ep, len(logs), a.boot, rng)
                    pc = np.full(len(cells), A.DELTA)
                    N0, X0 = simulate(base, rng, pc, rho)
                    Nb = {"Mstar": N0}
                    Xb = {"Mstar": X0}
                    for p_t in (0.10, 0.15, 0.20):
                        pt = pc.copy()
                        pt[target] = p_t
                        N1, X1 = simulate(base, rng, pt, rho)
                        Nb["B4_%g" % p_t], Xb["B4_%g" % p_t] = N1, X1
                    il, est, boot, ev = A.inloop(Nb, Xb, cells, scene_of_ep, log_of_ep, W)
                    null_flag += int(len(il["Mstar"]["sig_above_cells"]) > 0)
                    ila, _, _, _ = A.inloop({"Mstar": N0.sum(1, keepdims=True)}, {"Mstar": X0.sum(1, keepdims=True)}, all_cell, scene_of_ep, log_of_ep, W)
                    pooled_flag += int(ila["Mstar"]["cells"].get("all", {}).get("sig_above", False))
                    for p_t in (0.10, 0.15, 0.20):
                        k = "B4_%g" % p_t
                        pr = A.paired_inloop(est, boot, ev, cells, k)
                        nm = cells[target][0]
                        power[p_t] += int(nm in il[k]["sig_above_cells"] and nm not in il["Mstar"]["sig_above_cells"] and pr.get(nm, {}).get("positive", False))
                key = "%s|scale%.2f|rho%.1f" % ("+".join(pair), scale, rho)
                ev_cells = int(sum(1 for j in range(len(cells)) if len(set(scene_of_ep[np.repeat(base[:, j] > 0, 3)])) >= A.MIN_SCENES))
                res["layouts"][key] = {"A1_null_any_cell_flag_rate": null_flag / a.reps, "A1_pooled_flag_rate": pooled_flag / a.reps,
                                       "A2_power_planted_0.10": power[0.10] / a.reps, "A2_power_planted_0.15": power[0.15] / a.reps,
                                       "A2_power_planted_0.20": power[0.20] / a.reps,
                                       "target_cell_records_per_episode_mean": float(base[:, target].mean()),
                                       "target_cell_scenes": int((base[:, target] > 0).sum()), "evaluable_cells_approx": ev_cells}
                print(key, json.dumps(res["layouts"][key]), flush=True)
    json.dump(res, open(a.out, "w"), indent=1)
    print("K6 OC DONE")


if __name__ == "__main__":
    main()
