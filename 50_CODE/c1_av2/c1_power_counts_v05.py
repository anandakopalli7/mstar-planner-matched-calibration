#!/usr/bin/env python3
"""C1 power at 375 logs, slot S22 (Claude line, c1_power_counts_v05, 5 Nov 2026; D16 v26 Choice 47i, R20 M7 and B3). A bound,
outcome-free builder. v01 to v04 are kept and unchanged; this file imports v02, v03 and v04 and changes none of their functions.
S22 is REPORTED ONLY: it changes no label, rule, threshold or population. Its hash is recorded (README v09) before it runs.
What changes against v04: part M (the method-stage in-path audit population, withdrawn for H9 by plan section 7) is replaced by part
H9, the power of H9's TESTED population: the Trajectron++ PD items of the predictor arm.
  Part H9. Per tracker (T1 = index 0, T3 = index 1), from an AV2 stage-A K8 counts-only items file (k8_items_v04 --counts-only: error
  fields NaN, never read): the items H9 tests are tpp_analyse_v01.item_table's selection (ref_relied, step h = H_PRIMARY) in the
  in-path set (PD). Their E2 cells are m_lib_v04.make_cells(..., "E2"), as c1_predarm_v03.tables_hl builds them. History length is
  not in stage A (it needs the Trajectron++ keys, made after stage B), so each item gets a history stratum {2, 3-4, >= 5 states, or
  "< 2" (not predicted, dropped)} drawn from the DEVELOPMENT shares of its group: the nuScenes Trajectron++ keys' PD items
  (rec_hist_stratum_trk), per tracker. The table is units x (E2 cells + the 3 HL cells), and the floor is computed exactly as
  c1_predarm_v05.rule_v05 does: evaluable cells (>= 39 units from >= 8 logs), k6_analyse_v02.power_family over the JOINT evaluable
  family with weights from [20261110, i, 5] (first 500) and power seed [20261111, i, 5], the power-qualified E2 cells counted against
  the floor 6. Repeated over --reps-h9 history draws (seed [20261105, tracker index, draw]): the distribution of family_size_E2 and P(>= 6).
  With 150-log items (development check before stage A) the 375-log figure is also given by resampling 375 logs with replacement.
  CRITERIA (D16 v30 Choice 50; c1_rules_v01): part H9's power family uses the target-only power rule
  (c1_rules_v01.power_target: the target cell at P_PLANT 0.15, every other evaluable cell at DELTA, rho 0.5, N_DATASETS 2000 datasets,
  the first N_WEIGHTS 500 weight rows, power >= POWER_MIN 0.80; seeds unchanged), as c1_predarm_v07's H9 floor does; it also reports
  the family's share of the items. Parts A, B and J keep v02's analytic power approximation (reported only, not S22).
  PRIMARY (D16 v28 Choice 49g): the H9 projection LEAVES OUT history length (every PD item, E2 cells only), so it OVERSTATES H9's
  power; the history-share variant above is a descriptive sensitivity.
  Parts A, B and J are v04's (K8 power-qualified families, v02.run_oc at 375 units, M*Jx's CRC allowance). Part B uses the STRICTER
  comparator rule (Choices 47e, 49c): c1_power_counts_v02.validity is wrapped so that failing HK1c alone no longer removes a comparator
  from V_t; M*'s validity is unchanged. H3's comparator set is not modelled.
Inputs.
  AV2 (outcome-free): the stage-A counts-only items (--h9-items t1=<npz> t3=<npz>; default the 150-log public-LT3D items of
  30_DATA/av2_cache_stageA_v01/items/), and counts v01/v02 for parts A and B (as v04).
  Development: the K8 Linux replicate's v03 analysis (70_TESTS/k8_expl_v02_linux_analysis_v03/, confirmed by R16) for part B (as
  v04), and the nuScenes Trajectron++ keys 30_DATA/tpp_v01/keys_t{1,3}_val_v01.npz for the history shares of part H9.
  No AV2 outcome is computed or read.
Usage: python -B c1_power_counts_v05.py <out.json> [--reps 300] [--reps-h9 20] [--parts A,B,J,H9] [--h9-items t1=<npz> t3=<npz>]
"""
import argparse
import hashlib
import json
import os
import sys
import time
import warnings

import numpy as np

C1 = os.path.dirname(os.path.abspath(__file__))
W = os.path.dirname(os.path.dirname(C1))
sys.path.insert(0, C1)
sys.path.insert(0, os.path.join(W, "50_CODE", "tpp"))
import c1_power_counts_v02 as V2  # noqa: E402
import c1_power_counts_v03 as V3  # noqa: E402
import c1_power_counts_v04 as V4  # noqa: E402
import c1_analyse_v01 as CA  # noqa: E402
import c1_predarm_v01 as P1  # noqa: E402
import tpp_analyse_v01 as TA  # noqa: E402
import c1_rules_v01 as R  # noqa: E402

M, A = P1.M, CA.A
SEED_H9 = 20261105
DEFAULT_ITEMS = {t: os.path.join(W, "30_DATA", "av2_cache_stageA_v01", "items", "items_k8_v04_av2_stageA_%s_lt3d.npz" % t) for t in ("t1", "t3")}
DEV_KEYS = {t: os.path.join(W, "30_DATA", "tpp_v01", "keys_%s_val_v01.npz" % t) for t in ("t1", "t3")}
HL_NAMES = ("hist=2", "hist=3-4", "hist>=5")
INDEX = {"t1": 0, "t3": 1}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def pd_items(z):
    """The items H9 tests (tpp_analyse_v01.item_table's selection, then PD), from a K8 items file: dict of arrays."""
    sel = z["item_ref_relied"].astype(bool) & (z["item_h"] == TA.H_PRIMARY) & z["item_inpath"].astype(bool)
    return {k: np.asarray(z["item_" + k])[sel].astype(int) for k in ("s", "a", "g", "r", "m", "l0")}


def dev_hl_shares(keys_path):
    """Per group: shares of the history strata {-1: < 2 states, 0: 2, 1: 3-4, 2: >= 5} among the development PD items."""
    k = np.load(keys_path, allow_pickle=False)
    sel = k["item_ref_relied"].astype(bool) & (k["item_h"] == TA.H_PRIMARY) & k["item_inpath"].astype(bool)
    g = k["item_g"][sel].astype(int)
    hs = k["rec_hist_stratum_trk"][k["item_rec"][sel]].astype(int)
    out = {}
    for gg in sorted(set(g.tolist())):
        v = hs[g == gg]
        out[int(gg)] = {int(s): float(np.mean(v == s)) for s in (-1, 0, 1, 2)}
    allv = {int(s): float(np.mean(hs == s)) for s in (-1, 0, 1, 2)}
    return out, allv, int(sel.sum())


def h9_table(it, units_idx, n_units, hl):
    """units x (E2 cells + 3 HL cells) counts, as c1_predarm_v03.tables_hl (counts only)."""
    keep = hl >= 0
    s = units_idx[keep]
    items = {"s": s, "a": it["a"][keep], "g": it["g"][keep], "r": it["r"][keep], "D": np.zeros(int(keep.sum())),
             "scene_log_idx": np.arange(n_units), "n_scenes": n_units, "n_logs": n_units}
    m = it["m"][keep]
    lv = M.levels(items, m)
    cells = M.make_cells(items, m, "E2")
    l2c = np.full(M.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l2c[ids] = j
    cj = l2c[lv[0]]
    N = np.zeros((n_units, len(cells) + 3))
    ok = cj >= 0
    np.add.at(N, (s[ok], cj[ok]), 1.0)
    np.add.at(N, (s, len(cells) + hl[keep]), 1.0)
    return N, [c[0] for c in cells] + list(HL_NAMES)


def floor_family(N, n_e2, i):
    """c1_predarm_v07's power family (c1_rules_v01.power_target): evaluable cells, joint power family, power-qualified E2 cells."""
    nu = N.shape[0]
    scene_of_ep = np.array(["u%04d" % u for u in range(nu)])
    log_of_ep = np.arange(nu)
    rng = np.random.default_rng([CA.SEED_BOOT, i, P1.J_PRED])
    Wl = rng.multinomial(nu, np.full(nu, 1.0 / nu), size=CA.K.B_BOOT).astype(float)
    ev = A.evaluable(N, scene_of_ep, log_of_ep)
    pw, _ = R.power_target(N, ev, scene_of_ep, Wl[:R.N_WEIGHTS], np.random.default_rng([CA.SEED_POWER, i, P1.J_PRED]))
    qual = np.flatnonzero(ev & (pw >= R.POWER_MIN))
    qe2 = [j for j in qual if j < n_e2]
    return {"evaluable": int(ev.sum()), "evaluable_E2": int(ev[:n_e2].sum()), "family_size": int(len(qual)),
            "family_size_E2": int(len(qe2)), "E2_family_item_share": float(N[:, qe2].sum() / N[:, :n_e2].sum()) if N[:, :n_e2].sum() > 0 else None,
            "power_rule": "c1_rules_v01.power_target (target-only, %d datasets)" % R.N_DATASETS}


def e2_table(it, units_idx, n_units):
    """units x E2 cells counts of ALL the PD items, no history length (49g's primary projection)."""
    items = {"s": units_idx, "a": it["a"], "g": it["g"], "r": it["r"], "D": np.zeros(len(units_idx)),
             "scene_log_idx": np.arange(n_units), "n_scenes": n_units, "n_logs": n_units}
    lv = M.levels(items, it["m"])
    cells = M.make_cells(items, it["m"], "E2")
    l2c = np.full(M.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l2c[ids] = j
    cj = l2c[lv[0]]
    N = np.zeros((n_units, len(cells)))
    ok = cj >= 0
    np.add.at(N, (units_idx[ok], cj[ok]), 1.0)
    return N, [c[0] for c in cells]


def part_h9(items_paths, reps_h9):
    """Primary (D16 v28 Choice 49g): the projection LEAVES OUT history length: every PD item counts (none is dropped for a history
    below 2 states) and the power family is the E2 cells alone (no HL cells in the joint family), so it OVERSTATES H9's power.
    Sensitivity (descriptive): history strata drawn from the development shares, the joint E2 + HL family as the predictor arm."""
    out = {}
    for t, ip in items_paths.items():
        z = np.load(ip, allow_pickle=False)
        names = [str(x) for x in z["scene_names"]]
        it = pd_items(z)
        shares, allv, n_dev = dev_hl_shares(DEV_KEYS[t])
        res = {"items_file": os.path.relpath(ip, W).replace(os.sep, "/"), "items_sha256": sha(ip), "units": len(names), "pd_items": int(len(it["s"])),
               "dev_keys": os.path.relpath(DEV_KEYS[t], W).replace(os.sep, "/"), "dev_keys_sha256": sha(DEV_KEYS[t]), "dev_pd_items": n_dev,
               "dev_history_shares": {"all": allv, "by_group": shares},
               "primary": {"label": "no history length (Choice 49g): every PD item, E2 cells only; overstates H9's power"},
               "sensitivity_dev_history": {"label": "descriptive: development history shares, joint E2 + HL family"}}
        cases = [("375_logs", 375, False)] if len(names) == 375 else [("as_given", len(names), False), ("375_by_log_resampling", 375, True)]
        for label, n_units, resample in cases:
            prim, sens = [], []
            for d in range(reps_h9 if resample else max(1, reps_h9)):
                rng = np.random.default_rng([SEED_H9, INDEX[t], d])
                if resample:
                    pick = rng.integers(0, len(names), size=n_units)
                    rows = np.concatenate([np.flatnonzero(it["s"] == u) for u in pick])
                    uidx = np.concatenate([np.full(int((it["s"] == u).sum()), k) for k, u in enumerate(pick)])
                    sub = {k: v[rows] for k, v in it.items()}
                else:
                    sub, uidx = it, it["s"]
                if resample or d == 0:
                    N0, cells0 = e2_table(sub, uidx, n_units)
                    ff0 = floor_family(N0, len(cells0), INDEX[t])
                    prim.append(ff0["family_size_E2"])
                    if d == 0:
                        res["primary"].setdefault("first_draw", {})[label] = {"cells": cells0, "items_per_cell": N0.sum(0).astype(int).tolist(), **ff0}
                p = np.array([[shares.get(int(g), allv)[s_] for s_ in (-1, 0, 1, 2)] for g in range(4)])
                u = rng.random(len(sub["g"]))
                cum = np.cumsum(p[sub["g"]], axis=1)
                hl = (u[:, None] > cum).sum(1) - 1
                N, cells = h9_table(sub, uidx, n_units, hl)
                ff = floor_family(N, len(cells) - 3, INDEX[t])
                sens.append(ff["family_size_E2"])
                if d == 0:
                    res["sensitivity_dev_history"].setdefault("first_draw", {})[label] = {"cells": cells, "items_per_cell": N.sum(0).astype(int).tolist(), **ff}
            for key, arr in (("primary", np.array(prim)), ("sensitivity_dev_history", np.array(sens))):
                res[key][label] = {"units": n_units, "draws": int(len(arr)), "family_size_E2_median": float(np.median(arr)),
                                   "family_size_E2_min": int(arr.min()), "family_size_E2_max": int(arr.max()),
                                   "P_family_E2_ge_6": float(np.mean(arr >= R.F_MIN))}
        out[t] = res
    return out


_VALIDITY_V02 = V2.validity


def validity_v05(T, W_, ev_fn):
    """D16 v26 Choice 47(e), v28 49(c)/(g): the stricter comparator rule in the power model. 'shown invalid' (which removes a comparator
    from V_t) is a flagged cell, a flagged power-qualified family cell or a flagged pooled cell; failing HK1c alone no longer counts.
    'strict' (M*'s validity, HK1c included) is v02's, unchanged. H3's set is not modelled by the power model."""
    strict, shown, det = _VALIDITY_V02(T, W_, ev_fn)
    shown_v05 = any(det[p]["flagged"] > 0 or det[p]["family_flagged"] > 0 or det[p]["pooled_flagged"] for p in V2.CONF_POPS)
    return strict, bool(shown_v05), det


V2.validity = validity_v05


def main(argv=None):
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--reps", type=int, default=300)
    ap.add_argument("--reps-h9", type=int, default=20)
    ap.add_argument("--parts", default="A,B,J,H9")
    ap.add_argument("--h9-items", nargs="*", default=[])
    a = ap.parse_args(argv)
    assert not os.path.exists(a.out), "%s exists: never overwritten" % a.out
    parts = set(a.parts.split(","))
    items = dict(DEFAULT_ITEMS)
    for x in a.h9_items:
        k, p = x.split("=", 1)
        items[k] = p
    t0 = time.time()
    rng = np.random.default_rng(V4.SEED)
    res = {"script": "50_CODE/c1_av2/c1_power_counts_v05.py", "script_sha256": sha(os.path.abspath(__file__)),
           "modules_sha256": {"v02": sha(V2.__file__), "v03": sha(V3.__file__), "v04": sha(V4.__file__)},
           "status": "S22: reported only; changes no label, rule, threshold or population (D16 v26 Choice 47i)", "parts": sorted(parts),
           "development_inputs": {"part_B": os.path.relpath(V2.ANALYSIS, W).replace(os.sep, "/") + " (K8 Linux replicate, v03 analysis, R16)",
                                  "part_H9": "30_DATA/tpp_v01/keys_t{1,3}_val_v01.npz (nuScenes Trajectron++ keys: history shares)"},
           "outcome_statement": "AV2: stage-A counts-only items and counts v01/v02 only. No AV2 outcome computed or read."}
    if "H9" in parts:
        res["partH9"] = part_h9(items, a.reps_h9)
        print("H9 done", round(time.time() - t0, 1), "s", flush=True)
    if parts & {"A", "B"}:
        raw2 = open(V2.COUNTS2, "rb").read()
        c2 = json.loads(raw2)
        res["counts_v02_sha256"] = hashlib.sha256(raw2).hexdigest()
        res["partA_375"] = V3.part_a(c2, V4.K, rng)
    if "J" in parts:
        res["partJ"] = V4.part_j()
    if "B" in parts:
        an = json.load(open(V2.ANALYSIS))
        trk, dev = {}, {}
        for tag in ("t1", "t3"):
            dev[tag], aos = V2.dev_summary(an, tag)
            trk[tag] = {"aos": aos}
        del an
        res["analysis_sha256"] = sha(V2.ANALYSIS)
        for tag in ("t1", "t3"):
            scenes, tab, F = V2.load_tracker(tag, trk[tag]["aos"])
            log_idx, _ = V2.log_map(scenes)
            av2_run = c2["runs"][V2.AV2_RUN[tag]]
            trk[tag].update({"scenes": scenes, "tab": tab, "F": F, "log_idx": log_idx, "c": dev[tag]["c"],
                             "lay": V2.layout_match(tab, av2_run, len(scenes)), "av2_decisions": av2_run["decision_states_and_pairs"]["decisions"]})
        dec_per_scene = float(np.mean([Fs.shape[0] for Fs in trk["t1"]["F"]]))
        theta_d = min(1.0, (trk["t1"]["av2_decisions"] / V2.AV2_LOGS) / dec_per_scene)
        trk_cap, caps = V3.cap_mstar(trk, rng)
        n_units = int(round(V4.K * V2.AV2_LOGS))
        pf = res["partA_375"]["P_floors_met_T1_and_T3_lt3d"]
        res["partB_375"] = {}
        for name, tk, kap in (("plug_in", trk, 1.0), ("Mstar_capped", trk_cap, 1.0), ("kappa_0.5", trk, 0.5)):
            s = V3.summarise(V2.run_oc(tk, "scene", True, theta_d, a.reps, rng, n_units, kappa=kap))
            s["P_H1_combined_estimate"] = pf * s["P_H1_without_floors"]
            res["partB_375"][name] = s
            print(name, "done", round(time.time() - t0, 1), "s", flush=True)
    res["wall_seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out + ".partial", "w") as f:
        json.dump(res, f, indent=1)
    os.replace(a.out + ".partial", a.out)
    print(json.dumps({t: {k: v[k] for k in ("primary", "sensitivity_dev_history")} for t, v in (res.get("partH9") or {}).items()}, default=str)[:3000])
    print("C1 POWER COUNTS V05 DONE", a.out)


if __name__ == "__main__":
    main()
