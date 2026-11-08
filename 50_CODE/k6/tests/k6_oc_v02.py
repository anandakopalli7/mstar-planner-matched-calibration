#!/usr/bin/env python3
"""K6 operating characteristics v02 (Claude line, 1 Nov 2026; review R09 M3). Simulated exceedances on a
development-informed record layout; no real residual or closed-loop outcome of a confirmatory scene is used.

Layout. For each confirmatory scene and cell, the open-loop calibration items (deployed output, summed over the 8 steps)
times the cell's ratio of M*'s primary decision-mode records (population PD) per scene to open-loop items per scene,
measured on the 10 development scenes (k6_dev_check_v02). A cell without a development ratio takes the pooled ratio of
its motion class, or the overall pooled ratio. The layout is scaled by 0.5, 1 and 2; decision mode has one episode per
scene.
Simulation. Exceedance probabilities per scene and cell from a beta distribution with mean p and intra-scene correlation
rho in {0.1, 0.3}; binomial records per scene. The planted practitioner arm uses M*'s layout. The analysis functions (k6_analyse_v02) are used
unchanged: the HK1a family by the power rule, HK1a, HK1b, and HK2 at the Bonferroni level with the paired contrast.
Reported per layout: the HK1a family; A1 = P(HK1 fails | M* valid, every cell at delta); P(HK1a fails | M* at 0.15 in
one family cell); the practitioner power at 0.10, 0.15 and 0.20 in car|lat|turning.
Acceptance (plan v02 section 8), at scale 1 in every layout: A1 <= 0.10 (HK1 failing for a valid M*, a flag in ANY evaluable
cell counting, R09b MJ3), family size >= F_MIN, and on T1 the family contains car|lat|straight and car|lat|turning
(R09b m3). Zero development ratios are floored at 0.02 (R09b m4).
Usage: python -B k6_oc_v02.py --items <dir> --dev <k6_dev_check_v02.json> --out <json> [--reps R] [--boot B]
"""
import argparse
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k6_analyse_v02 as A  # noqa: E402
import k6_dev_check_v02 as DC  # noqa: E402
import k6_sim_v02 as S  # noqa: E402

TARGET = "car|lat|turning"
ZERO_FLOOR = 0.02       # a development ratio of 0 (10 scenes) is floored, not treated as a structural zero (R09b m4)
REQUIRED_T1 = ("car|lat|straight", "car|lat|turning")   # informative acceptance (R09b m3): the method-stage failure cells


def layout(items_dir, tag, ratio):
    cells = A.cell_family()
    names = []
    for sp in ("train", "val"):
        names += json.load(open(os.path.join(items_dir, "items_%s_%s_summary.json" % (tag, sp))))["scene_names"]
    conf = [s for s in names if s not in A.DEV_SCENES]
    ol = DC.open_loop_items(items_dir, ["%s_train" % tag, "%s_val" % tag], set(conf))
    r = np.array([max(ratio[c[0]]["ratio"], ZERO_FLOOR) if ratio[c[0]]["ratio"] is not None else np.nan for c in cells], float)
    pooled = np.nansum([ratio[c[0]]["inloop_records_per_episode"] for c in cells]) / max(np.nansum([ratio[c[0]]["open_loop_items_per_scene"] for c in cells]), 1e-9)
    filled = r.copy()
    for j, (nm, _) in enumerate(cells):
        if not np.isfinite(r[j]):
            mot = nm.split("|")[2]
            same = [i for i, (n2, _) in enumerate(cells) if n2.split("|")[2] == mot and np.isfinite(r[i])]
            filled[j] = float(np.mean(r[same])) if same else pooled
    base = np.array([ol[s] for s in conf]) * filled[None, :]
    return conf, base, filled


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--items", required=True)
    ap.add_argument("--dev", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--boot", type=int, default=500)
    a = ap.parse_args()
    dev = json.load(open(a.dev))
    cells = A.cell_family()
    tj = [i for i, (n, _) in enumerate(cells) if n == TARGET][0]
    man = {}
    res = {"reps": a.reps, "boot": a.boot, "layouts": {}, "acceptance": {}}
    for tag in ("t1", "t3"):
        for sp in ("train", "val"):
            for s, info in json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "..",
                                                       "30_DATA", "k6", "cache_v02_%s_%s" % (tag, sp), "MANIFEST.json")))["scenes"].items():
                man[s] = info["log"]
        conf, base0, filled = layout(a.items, tag, dev[tag]["decide"]["layout_ratio_Mstar"])
        logs = sorted(set(man[s] for s in conf))
        scene_of_ep = np.array(conf)
        log_of_ep = np.array([logs.index(man[s]) for s in conf])
        for scale in (0.5, 1.0, 2.0):
            N = np.round(base0 * scale)
            for rho in (0.1, 0.3):
                rng = np.random.default_rng([20261105, int(scale * 10), int(rho * 10), 1 if tag == "t1" else 3])
                W = A.boot_weights(log_of_ep, len(logs), a.boot, rng) if hasattr(A, "boot_weights") else \
                    rng.multinomial(len(logs), np.full(len(logs), 1.0 / len(logs)), size=a.boot).astype(float)[:, log_of_ep]
                ev = A.evaluable(N, scene_of_ep, log_of_ep)
                pw, _ = A.power_family(N, ev, scene_of_ep, W, np.random.default_rng([20261106, int(scale * 10), int(rho * 10)]))
                fam = ev & (pw >= A.POWER_MIN)
                scenes = sorted(set(conf))
                sidx = np.repeat(np.arange(len(conf)), 3)

                def draw(pcell):
                    if rho > 0:
                        al = pcell * (1 - rho) / rho
                        be = (1 - pcell) * (1 - rho) / rho
                        P = rng.beta(np.broadcast_to(al, (len(conf), len(cells))), np.broadcast_to(be, (len(conf), len(cells))))
                    else:
                        P = np.broadcast_to(pcell, (len(conf), len(cells)))
                    return rng.binomial(np.round(base0 * scale).astype(int), P).astype(float)
                hk1_fail = hk1a_fail_planted = 0
                prac = {0.10: 0, 0.15: 0, 0.20: 0}
                fam_idx = np.flatnonzero(fam)
                thin = fam_idx[np.argmin(N[:, fam_idx].astype(bool).sum(0))] if len(fam_idx) else None
                for r in range(a.reps):
                    X0 = draw(np.full(len(cells), A.DELTA))
                    il, _, _, _ = A.inloop_population({"Mstar": N}, {"Mstar": X0}, cells, scene_of_ep, log_of_ep, W, family_from=fam)
                    ila, _, _, _ = A.inloop_population({"Mstar": N.sum(1, keepdims=True)}, {"Mstar": X0.sum(1, keepdims=True)},
                                                       [("all", list(range(S.N_L0)))], scene_of_ep, log_of_ep, W)
                    il_all, _, _, _ = A.inloop_population({"Mstar": N}, {"Mstar": X0}, cells, scene_of_ep, log_of_ep, W)
                    hk1a = len(fam_idx) >= A.F_MIN and not il["Mstar"]["sig_above_cells"] and not il_all["Mstar"]["sig_above_cells"]
                    hk1b = not ila["Mstar"]["cells"]["all"]["sig_above"]
                    hk1_fail += int(not (hk1a and hk1b))
                    if thin is not None:
                        pc = np.full(len(cells), A.DELTA)
                        pc[thin] = 0.15
                        Xp = draw(pc)
                        ilp, _, _, _ = A.inloop_population({"Mstar": N}, {"Mstar": Xp}, cells, scene_of_ep, log_of_ep, W, family_from=fam)
                        hk1a_fail_planted += int(bool(ilp["Mstar"]["sig_above_cells"]))
                    if ev[tj]:
                        for pt in prac:
                            pc = np.full(len(cells), A.DELTA)
                            pc[tj] = pt
                            Xb = draw(pc)
                            Nd, Xd = {"Mstar": N, "B4": N}, {"Mstar": X0, "B4": Xb}
                            ilb, est, boot, evd = A.inloop_population(Nd, Xd, cells, scene_of_ep, log_of_ep, W)
                            fb = np.flatnonzero(evd["B4"])
                            _, _, _, sb, _ = A.flag(est["B4"], boot["B4"], fb, A.LEVEL_HK2)
                            flagged = TARGET in [cells[j][0] for i, j in enumerate(fb) if sb[i]]
                            pr = A.paired(est, boot, evd, cells, "B4", "Mstar", A.LEVEL_HK2)
                            prac[pt] += int(flagged and TARGET not in ilb["Mstar"]["sig_above_cells"] and pr.get(TARGET, {}).get("positive", False))
                key = "%s|scale%.1f|rho%.1f" % (tag, scale, rho)
                res["layouts"][key] = {"evaluable_cells": int(ev.sum()), "family": [cells[j][0] for j in fam_idx], "family_size": int(len(fam_idx)),
                                       "power_at_0.15": {cells[j][0]: round(float(pw[j]), 3) for j in np.flatnonzero(ev)},
                                       "A1_P_HK1_fails_valid_Mstar": hk1_fail / a.reps,
                                       "P_HK1a_flags_Mstar_at_0.15_in_thinnest_family_cell": (hk1a_fail_planted / a.reps) if thin is not None else None,
                                       "thinnest_family_cell": cells[thin][0] if thin is not None else None,
                                       "target_evaluable": bool(ev[tj]),
                                       "practitioner_power": {str(k): v / a.reps for k, v in prac.items()} if ev[tj] else None,
                                       "target_records_per_episode": float(N[:, tj].mean())}
                print(key, json.dumps({k: v for k, v in res["layouts"][key].items() if k != "power_at_0.15"}), flush=True)
        res["layout_ratio_filled_" + tag] = {cells[j][0]: float(filled[j]) for j in range(len(cells))}
        # HK3 (infeasible-decision rate): normal-approximation power from the development per-scene paired differences,
        # with a log-cluster design effect of 1, 2 or 3.5 on the standard error, at the effect seen and at half of it
        from scipy.stats import norm
        z = norm.ppf(A.LEVEL_HK3)
        hk3 = {}
        for b in A.HK3_ARMS:
            m_, sd_ = dev[tag]["decide"]["HK3_scene_diff_mean_sd"][b]
            hk3[b] = {"dev_mean": m_, "dev_sd": sd_}
            for deff in (1.0, 2.0, 3.5):
                se = sd_ / np.sqrt(len(conf)) * deff
                for frac in (1.0, 0.5):
                    hk3[b]["power_deff%.1f_effect%.1f" % (deff, frac)] = float(norm.cdf(-frac * m_ / se - z))
        res["HK3_power_" + tag] = hk3
    for k, v in res["layouts"].items():
        if "|scale1.0|" in k:
            res["acceptance"][k] = {"A1_le_0.10": v["A1_P_HK1_fails_valid_Mstar"] <= 0.10, "family_ge_floor": v["family_size"] >= A.F_MIN}
            if k.startswith("t1|"):
                res["acceptance"][k]["T1_family_has_moving_car_lateral_cells"] = all(c in v["family"] for c in REQUIRED_T1)
    res["acceptance_all"] = all(all(x.values()) for x in res["acceptance"].values())
    json.dump(res, open(a.out, "w"), indent=1)
    print("ACCEPTANCE", res["acceptance_all"])
    print("K6 OC V02 DONE")


if __name__ == "__main__":
    main()
