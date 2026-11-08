#!/usr/bin/env python3
"""TPP arm analysis v03 (Claude line, 4 Nov 2026) for 90_DECISIONS/D17_TPP_ARM_PREREG_v03.md, after review R18
(70_TESTS/R18_D17_REVIEW_v01.md) and D16 v12 Choice 32. Run in canmot310. Written and tested on SYNTHETIC data only.
v01 and v02 are kept; v03 imports their unchanged helpers (inputs, item table, A6, folds, S2 pooling, the K7 floor rule).
Changes from v02:
  M1  K7 rule (iii) is split: "no power-qualified family cell shown above delta" is GATING for H2; only the count floor
      (>= 6 cells) is reported. An H2 pass is worded "no cell shown above delta (one-sided simultaneous test at 0.95)",
      with the power-qualified counts and "floor of 6 not met" where it is not met; never "valid".
  M2  Fail safe: the tracker-history run, the ground-truth run and exactly two S1 seed runs are required; each run's
      meta (source, seed, model, keys hash) must match its role; the three tracker-history runs must differ by content
      hash; NaN or inf in any analysed D, V or ground truth is an error; a missing or undecidable verdict is an error.
  M3  Binding (D16 Choice 24 architecture): on real data the plan must be frozen (c1_guard_v01.frozen_plan against
      40_PROTOCOL/D17_PLAN_HASH_LOG.txt, written only by tpp_freeze_v01), must not say DRAFT, and every code file
      (this one and every imported module), the configuration, every input (keys, runs, seed runs, cache manifests,
      SHA256SUMS lists) must have its bound hash; each run's hash must also be listed in its SHA256SUMS file. B and all
      seeds and levels come from the bound configuration (tpp_analysis_config_v01.json); --boot exists in synthetic mode only.
  M4  Every CRC decision (M*, B4, and B3 through M*) is exact (c1_crc_exact_v01.crc_threshold_exact); exact ties
      (bound = delta exactly at the chosen threshold) are counted and reported.
  M5  The constraints are the K8 tracker-planner's: relied axis, pair gap (SD1_7), object axis and toward-ego sign as K8's
      items carry them (tpp_keys_v01 copies them from k8_items_v02.scene_items; the sign is verified there against K8's own
      signed errors). Nothing is recomputed here.
  m5  Pooled-cell evaluability (>= 39 scenes, >= 8 logs) is checked, finite sup-t quantiles are asserted for the gating
      method, and an empty population is a stated NO, not a crash.
  m3  H4 breakdowns (descriptive point estimates): by history stratum and by class group, on PD7.
  One coded decision across trackers x seeds: SUPPORTED (both trackers, all three seeds), SEED_DEPENDENT_NOT_SUPPORTED
  (both trackers at the primary seed; "primary plus one S1 seed" or "primary only"), NOT_SUPPORTED.
Usage (synthetic): python -I tpp_analyse_v03.py --synthetic --tracker t1 KEYS TRK GT S04 S05 [--tracker t3 ...] --out J [--boot N]
      (real):      python -I tpp_analyse_v03.py --plan 90_DECISIONS/D17_TPP_ARM_PREREG_v03.md \
                     --tracker t1 KEYS TRK GT S04 S05 CACHE --tracker t3 KEYS TRK GT S04 S05 CACHE --out J
"""
import argparse
import json
import os
import re
import sys
import time
from fractions import Fraction

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W_ROOT = os.path.dirname(os.path.dirname(HERE))
for p in (HERE, os.path.join(W_ROOT, "50_CODE", "m"), os.path.join(W_ROOT, "50_CODE", "k6"), os.path.join(W_ROOT, "50_CODE", "c1_av2")):
    if p not in sys.path:
        sys.path.append(p)
import tpp_common_v01 as C  # noqa: E402
import tpp_analyse_v01 as A1  # noqa: E402
import tpp_analyse_v02 as A2  # noqa: E402
import k6_analyse_v02 as K6A  # noqa: E402
import c1_crc_exact_v01 as CX  # noqa: E402
import c1_guard_v01 as G  # noqa: E402

M, L = A1.M, A1.L
CONFIG_PATH = os.path.join(HERE, "tpp_analysis_config_v01.json")
CFG = json.load(open(CONFIG_PATH))
HASH_LOG = os.path.join(W_ROOT, "40_PROTOCOL", "D17_PLAN_HASH_LOG.txt")
DELTA, LEVEL, HK1C_EPS, N_MIN = CFG["delta"], CFG["level"], CFG["hk1c_eps"], CFG["n_min"]
DELTA_EXACT = Fraction(repr(float(DELTA)))
PRIMARY, S1_SEEDS = int(CFG["primary_seed"]), [int(x) for x in CFG["s1_seeds"]]
POPS = ("PD7", "SD1_7", "PD")
# the bound configuration must equal the constants of the imported code it configures
assert (A1.DELTA, A1.SIGMA_A, A1.BOOT_SEED, A1.FOLD_SEED, A1.N_FOLDS, A1.H_PRIMARY, A1.HK1C_EPS, A1.N_MIN) == \
    (CFG["delta"], CFG["sigma_a"], CFG["boot_seed"], CFG["fold_seed"], CFG["n_folds"], CFG["h"], CFG["hk1c_eps"], CFG["n_min"]), "config differs from tpp_analyse_v01"
assert (A2.POWER_SEED_TPP, A2.TAIL_TRACE_M2, A2.PRIMARY_SEED, K6A.F_MIN) == (CFG["power_seed"], CFG["tail_trace_m2"], PRIMARY, CFG["f_min"]), "config differs from v02 / K6"
assert abs(A1.Z - 1.6448536269514722) < 1e-15 and LEVEL == 0.95


BANNER = re.compile(r"(?<![A-Za-z0-9_/.\-])(DRAFT|NOT FROZEN)(?![A-Za-z0-9_])")


def unfrozen_banner(txt):
    """True if the plan text carries an unfrozen-version banner word (a whole upper-case word, not part of a file name
    such as MANUSCRIPT_DRAFT_v02.md)."""
    return bool(BANNER.search(txt))


def code_files():
    """Every code file the analysis executes, and the configuration."""
    mods = [os.path.abspath(__file__), A2.__file__, A1.__file__, C.__file__, M.__file__, L.__file__, K6A.__file__, K6A.S.__file__,
            CX.__file__, G.__file__]
    return [os.path.abspath(m) for m in mods] + [CONFIG_PATH]


TIES = {"n": 0, "decisions": 0}


def exact_stat(u, unit):
    c = CX.crc_threshold_exact(u, unit, DELTA)
    if c is not None:
        TIES["decisions"] += 1
        b, _ = CX.bound_exact(u, unit, c)
        if b == DELTA_EXACT:
            TIES["n"] += 1
    return c


def crossfit_exact(U, s, lv, folds_scene):
    """A1.crossfit with exact CRC decisions (M4): M* (per-L0 CRC with the fallback chain, n_min 19), B4 (pooled), B3."""
    n = len(U)
    thr = {k: np.full(n, np.nan) for k in ("Mstar", "B4", "B3")}
    src = np.full(n, -1)
    fits = []
    for f in range(CFG["n_folds"]):
        cal = folds_scene[s] != f
        te = ~cal
        t_m, t_src = M.fit_hier(U[cal], s[cal], [x[cal] for x in lv], 0, N_MIN, stat=exact_stat)
        b4 = exact_stat(U[cal], s[cal])
        assert b4 is not None and np.isfinite(b4), "B4 undefined in fold %d" % f
        b3 = float(np.nanmax(t_m))
        assert not np.isnan(t_m[lv[0][te]]).any(), "a held-out stratum has no threshold at any level"
        thr["Mstar"][te], thr["B4"][te], thr["B3"][te] = t_m[lv[0][te]], b4, b3
        src[te] = t_src[lv[0][te]]
        fits.append({"fold": f, "cal_scenes": int(len(np.unique(s[cal]))), "test_scenes": int(len(np.unique(s[te]))), "B4": b4, "B3": b3,
                     "own_threshold_share": float(np.mean(t_src[lv[0][te]] == 0)) if te.any() else None})
    return thr, src, fits


def h2_population(hk_mstar, floor):
    """M1: H2 holds on a population iff HK1 (i) no evaluable cell flagged, (ii) the pooled cell evaluable and not flagged,
    and (iii-a) no power-qualified family cell flagged in its own sup-t. The count floor (iii-b) is reported only."""
    if hk_mstar is None or floor is None:
        return False, "population has no analysable item or no evaluable cell: NO"
    ok = bool(hk_mstar["HK1_i_no_flagged_cell"] and hk_mstar["HK1_ii_pooled_evaluable"] and hk_mstar["HK1_ii_pooled_not_flagged"]
              and not floor["family_flagged"])
    why = [] if ok else [k for k, bad in (("a cell flagged", not hk_mstar["HK1_i_no_flagged_cell"]),
                                           ("pooled cell not evaluable", not hk_mstar["HK1_ii_pooled_evaluable"]),
                                           ("pooled cell flagged", not hk_mstar["HK1_ii_pooled_not_flagged"]),
                                           ("a power-qualified family cell flagged", bool(floor["family_flagged"]))) if bad]
    return ok, ("no cell shown above delta" if ok else "shown above delta or not testable: " + ", ".join(why))


def breakdowns(it, sel, exc, keys=("TPP_B0", "TPP_Mstar", "TRK_Mstar")):
    """m3 / H4: descriptive scene-level exceedance by history stratum and by class group on the analysed items."""
    s = it["s"][sel]
    out = {}
    for name, lab in (("history_stratum", it["hist_stratum"][sel]), ("group", it["g"][sel])):
        names = {"history_stratum": {0: "2", 1: "3-4", 2: ">=5"}, "group": {0: "car", 1: "pedestrian", 2: "two_wheeler", 3: "large"}}[name]
        out[name] = {}
        for v in sorted(set(int(x) for x in lab)):
            m = lab == v
            r = {"items": int(m.sum()), "scenes": int(len(np.unique(s[m])))}
            for k in keys:
                if k in exc:
                    e = exc[k][m]
                    us = np.unique(s[m])
                    r[k] = float(np.mean([e[s[m] == u].mean() for u in us]))
            out[name][names.get(v, str(v))] = r
    return out


def analyse_v03(kz, runs, gt_xy, trk_mu, trk_cov, variant, B, tail_cap=None):
    it = A1.item_table(kz, runs, gt_xy, trk_mu, trk_cov, CFG["h"], variant)
    names = [str(x) for x in kz["scene_names"]]
    is_dev = np.asarray(kz["scene_is_dev"], bool)
    folds = A2.scene_folds_v02(names, is_dev, CFG["fold_seed"], CFG["n_folds"])
    arms = ["TRK"] + [a for a in ("TPP", "TPPgt") if a + "_ok" in it]
    assert arms == ["TRK", "TPP", "TPPgt"], "the tracker-history and ground-truth Trajectron++ runs are both required (M2)"
    keep = ~is_dev[it["s"]]
    common = keep.copy()
    for a in arms:
        common &= it[a + "_ok"]
    tail_drop = np.zeros(len(common), bool)
    if tail_cap is not None:
        for z in runs.values():
            c3 = z["v2_cov"][it["rec"]]
            tail_drop |= np.nan_to_num(c3[:, 0] + c3[:, 2], nan=0.0) > tail_cap
        common &= ~tail_drop
    for a in arms:                                   # M2: no NaN or inf in any analysed row
        assert np.all(np.isfinite(it[a + "_D"][common])) and np.all(np.isfinite(it[a + "_V"][common])), "non-finite D or V in arm " + a
    assert np.all(np.isfinite(gt_xy[it["rec"][common]])), "non-finite ground truth in analysed rows"
    assert common.any(), "no analysable PD7 item"
    TIES["n"], TIES["decisions"] = 0, 0
    res = {"variant": variant, "h": CFG["h"], "tail_cap_m2": tail_cap,
           "folds": {str(f): sorted(np.array(names)[folds == f].tolist()) for f in range(CFG["n_folds"])},
           "excluded_dev_scenes": sorted(np.array(names)[is_dev].tolist()),
           "counts": {"relied_items_h": int(len(common)), "in_dev_scenes": int((~keep).sum()), "tail_dropped": int((tail_drop & keep).sum()),
                      "common_ok": int(common.sum()), **{a + "_ok_nondev": int((it[a + "_ok"] & keep).sum()) for a in arms}},
           "populations": {}}
    pops = {"PD7": common, "SD1_7": common & (it["gap"] <= 5.0), "PD": common & it["inpath"]}
    items7, m7, lv7 = A1.mlib_items(it, pops["PD7"], kz)
    EXC, MARG, fitinfo = {}, {}, {}
    for a in arms:
        D, V = it[a + "_D"][pops["PD7"]], it[a + "_V"][pops["PD7"]]
        sd = np.sqrt(np.maximum(V + A1.SIGMA_A ** 2, 1e-6))
        thr, src, fits = crossfit_exact(D / sd, items7["s"], lv7, folds)
        for meth, mg in (("B0", A1.Z * sd), ("B4", thr["B4"] * sd), ("B3", thr["B3"] * sd), ("Mstar", thr["Mstar"] * sd)):
            EXC[a + "_" + meth] = (D > mg).astype(float)
            MARG[a + "_" + meth] = mg
        fitinfo[a] = {"folds": fits, "Mstar_own_threshold_share": float(np.mean(src == 0))}
    res["fits"] = fitinfo
    res["exact_crc"] = {"decisions": TIES["decisions"], "exact_ties_bound_equals_delta": TIES["n"],
                        "note": "every CRC accept/reject decided in rational arithmetic (c1_crc_exact_v01); order-free"}
    idx7 = np.nonzero(pops["PD7"])[0]
    lab = "TPP_B0 - TPPgt_B0 (history-input effect)"
    for k, (pname, sel) in enumerate(pops.items()):
        if not sel.any():
            res["populations"][pname] = {"items": 0, "empty": True, "H2_population": False, "H2_reason": "empty population: NO"}
            continue
        items, m, lv = A1.mlib_items(it, sel, kz)
        sub = np.isin(idx7, np.nonzero(sel)[0])
        exc = {q: v[sub] for q, v in EXC.items()}
        marg = {q: v[sub] for q, v in MARG.items()}
        W = M.boot_scene_weights(items, B, np.random.default_rng(CFG["boot_seed"]), "log")
        cells = M.make_cells(items, m, "E2")
        pairs = [("TPP_B0", "TRK_B0", list(range(len(cells))), "TPP_B0 - TRK_B0"), ("TPP_B0", "TPPgt_B0", list(range(len(cells))), lab)]
        st = M.eval_stats(items, {"lv": lv}, marg, cells, W, exc_frac=exc, pairs=pairs) if cells else None
        pooled = M.eval_stats(items, {"lv": lv}, marg, [("pooled", list(range(M.N_L0)))], W, exc_frac=exc, pairs=[(p[0], p[1], [0], p[3]) for p in pairs])
        lay = M._layout(items, {"lv": lv}, [("pooled", list(range(M.N_L0)))], None)
        pooled_ev = bool(K6A.evaluable(lay["n_ig"], np.arange(lay["n_ig"].shape[0]), items["scene_log_idx"])[0])
        hk = {}
        for meth in marg:
            pc = pooled["methods"][meth]["cells"]["pooled"]
            hk[meth] = {"HK1_i_no_flagged_cell": bool(cells) and not st["methods"][meth]["any_sig_under"],
                        "flagged_cells": st["methods"][meth]["sig_under_cells"] if st else [],
                        "evaluable_cells": len(cells), "HK1_ii_pooled_evaluable": pooled_ev, "HK1_ii_pooled_not_flagged": not pc["sig_under"],
                        "pooled_E": pc["E_scene"], "pooled_lb": pc["lb_sim"], "pooled_ub": pc["ub_sim"],
                        "HK1c_pooled_ub_le_delta_plus_0.03": bool(pc["ub_sim"] <= DELTA + HK1C_EPS), "mean_margin_m": pc["mean_margin_m"]}
            hk[meth]["HK1"] = bool(hk[meth]["HK1_i_no_flagged_cell"] and pooled_ev and hk[meth]["HK1_ii_pooled_not_flagged"])
        if st is not None:                            # m5: finite sup-t quantile for the gating method wherever an SE is positive
            sem = [c["se"] for c in st["methods"]["TPP_Mstar"]["cells"].values()]
            assert np.isfinite(st["methods"]["TPP_Mstar"]["q_lower"]) or all(x == 0 for x in sem), "non-finite sup-t quantile: " + pname
        fl = A2.floors(items, lv, cells, exc["TPP_Mstar"], k, W) if cells else None
        if fl is not None:
            fl["role"] = "family no-flag (iii-a) GATING; count floor (iii-b) reported only (D16 v12 Choice 32 M1)"
        ok2, why2 = h2_population(hk["TPP_Mstar"] if cells else None, fl)
        res["populations"][pname] = {"items": int(sel.sum()), "scenes": int(len(np.unique(items["s"]))), "cells": [c[0] for c in cells],
                                     "validity": hk, "HK1a_iii_TPP_Mstar": fl, "H2_population": ok2, "H2_reason": why2,
                                     "cells_stats": st, "pooled_stats": pooled}
    res["H4_breakdowns_PD7"] = breakdowns(it, pops["PD7"], EXC)
    recs = np.unique(it["rec"][pops["PD7"]])
    s_rec = kz["rec_s"][recs].astype(int)
    res["A6"] = {"TRK": A1.a6(gt_xy[recs] - trk_mu[recs], trk_cov[recs], s_rec, len(names))}
    for src, z in runs.items():
        res["A6"]["TPP" if src == "trk" else "TPPgt"] = A1.a6(gt_xy[recs] - z[variant + "_mu"][recs], z[variant + "_cov"][recs], s_rec, len(names))
    P7 = res["populations"]["PD7"]
    paired = P7["pooled_stats"]["paired"]
    h2 = all(res["populations"][p]["H2_population"] for p in POPS)
    fam = {p: (res["populations"][p].get("HK1a_iii_TPP_Mstar") or {}).get("family_size") for p in POPS}
    floor_all = all((res["populations"][p].get("HK1a_iii_TPP_Mstar") or {}).get("floor_met") for p in POPS)
    res["hypotheses"] = {"H1_raw_TPP_overconfident": bool(P7["validity"]["TPP_B0"]["pooled_lb"] > DELTA),
                         "H2_no_cell_shown_above_delta_all_pops": bool(h2),
                         "H3_history_input_effect_positive": bool(paired[lab]["cells"]["pooled"]["positive"])}
    res["H2_wording"] = ("no cell shown above delta (one-sided simultaneous test at 0.95) on PD7, SD1_7 and PD; power-qualified cells %s; floor of 6 %s"
                         % (fam, "met on every population" if floor_all else "not met") if h2 else
                         "not supported: " + "; ".join("%s: %s" % (p, res["populations"][p]["H2_reason"]) for p in POPS))
    res["key_numbers"] = {"TPP_B0_pooled_E_PD7": P7["validity"]["TPP_B0"]["pooled_E"], "TPP_Mstar_pooled_E_PD7": P7["validity"]["TPP_Mstar"]["pooled_E"],
                          "TPP_Mstar_mean_margin_m_PD7": P7["validity"]["TPP_Mstar"]["mean_margin_m"],
                          "TRK_Mstar_mean_margin_m_PD7": P7["validity"]["TRK_Mstar"]["mean_margin_m"]}
    return res


def decide(per_tracker):
    """One coded decision across trackers x {primary, S1 seeds}. per_tracker: {tag: {seed: hypotheses dict}}."""
    seeds = [PRIMARY] + S1_SEEDS
    out = {}
    for h in ("H1_raw_TPP_overconfident", "H2_no_cell_shown_above_delta_all_pops", "H3_history_input_effect_positive"):
        tab = {}
        for t, by in per_tracker.items():
            assert sorted(by) == sorted(seeds), "S1 needs exactly the primary and the two S1 seeds for " + t
            for sd in seeds:
                v = by[sd][h]
                assert isinstance(v, bool), "undecidable verdict (%s, %s, %s)" % (h, t, sd)
                tab["%s|%d" % (t, sd)] = v
        prim = all(tab["%s|%d" % (t, PRIMARY)] for t in per_tracker)
        s1_ok = [all(tab["%s|%d" % (t, sd)] for t in per_tracker) for sd in S1_SEEDS]
        if prim and all(s1_ok):
            code, note = "SUPPORTED", "holds on every tracker under all three seeds"
        elif prim:
            code = "SEED_DEPENDENT_NOT_SUPPORTED"
            note = "primary plus one S1 seed" if any(s1_ok) else "primary seed only"
        else:
            code, note = "NOT_SUPPORTED", "fails on at least one tracker at the primary seed"
        out[h] = {"code": code, "note": note, "by_tracker_seed": tab}
    return out


def check_runs(keys_path, paths, synthetic):
    """M2: roles, seeds, model, keys binding and distinct content of the three tracker-history runs."""
    want = {"trk": ("trk", PRIMARY), "gt": ("gt", PRIMARY), "s1a": ("trk", S1_SEEDS[0]), "s1b": ("trk", S1_SEEDS[1])}
    assert set(paths) == set(want), "required runs: trk, gt and both S1 seed runs (M2)"
    ksha = C.sha256_path(keys_path)
    shas = {}
    for role, p in paths.items():
        assert p and os.path.exists(p), "missing run for role " + role
        z = np.load(p, allow_pickle=False)
        meta = json.loads(str(z["meta_json"]))
        src, sd = want[role]
        assert meta.get("source") == src and int(meta.get("seed")) == sd, "run %s is not the %s run of seed %d: %s" % (p, src, sd, meta.get("seed"))
        assert meta.get("model") == CFG["model"], "model is not " + CFG["model"]
        assert meta.get("keys_sha256") == ksha, "run %s was not made from these keys" % p
        shas[role] = C.sha256_path(p)
    assert len({shas["trk"], shas["s1a"], shas["s1b"]}) == 3, "the three tracker-history runs must be distinct files (content hash)"
    return shas


def check_binding_real(plan, trackers):
    """M3: frozen plan in the D17 hash log, no DRAFT, every code file, the config and every input bound; runs in SHA256SUMS."""
    txt = open(plan, encoding="utf-8").read()
    assert not unfrozen_banner(txt), "the plan carries an unfrozen-version banner: never accepted"
    side, frozen = G.frozen_plan(plan, HASH_LOG)
    bound = {}
    for f in code_files():
        bound[G.rel(f)] = G.require_bound(frozen, f)
    for tag, d in trackers.items():
        files = [d["keys"], d["trk"], d["gt"], d["s1a"], d["s1b"], os.path.join(d["cache"], "MANIFEST.json"),
                 os.path.join(os.path.dirname(d["trk"]), "SHA256SUMS_v01.txt"), os.path.join(os.path.dirname(d["s1a"]), "SHA256SUMS_seed_v01.txt")]
        for f in files:
            bound[G.rel(f)] = G.require_bound(frozen, f)
        for role, sums in (("trk", "SHA256SUMS_v01.txt"), ("gt", "SHA256SUMS_v01.txt"), ("s1a", "SHA256SUMS_seed_v01.txt"), ("s1b", "SHA256SUMS_seed_v01.txt")):
            listed = {ln.split()[0]: ln.split()[-1].lstrip("*") for ln in open(os.path.join(os.path.dirname(d[role]), sums)).read().splitlines() if ln.strip()}
            h = C.sha256_path(d[role])
            assert listed.get(h) == os.path.basename(d[role]), "run %s is not listed with its hash in %s" % (d[role], sums)
        kz = np.load(d["keys"], allow_pickle=False)
        names = np.array([str(x) for x in kz["scene_names"]])
        assert sorted(names[np.asarray(kz["scene_is_dev"], bool)].tolist()) == sorted(CFG["dev_scenes"]), "development scenes differ from the config"
    assert sorted(trackers) == sorted(CFG["trackers"]), "both trackers are required"
    return side, bound


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--tracker", nargs="+", action="append", required=True, help="TAG KEYS TRK GT S1A S1B [CACHE]")
    ap.add_argument("--out", required=True)
    ap.add_argument("--synthetic", action="store_true")
    ap.add_argument("--plan", default=None)
    ap.add_argument("--boot", type=int, default=None, help="synthetic mode only")
    a = ap.parse_args(argv)
    assert a.synthetic, ("tpp_analyse_v03 is superseded (D16 v15 Choice 36): real (non-synthetic) inputs are refused; "
                         "use 50_CODE/tpp/tpp_analyse_v04.py under the frozen D17 v04 plan")
    t0 = time.time()
    assert not os.path.exists(a.out), "the output exists: never overwritten"
    trackers = {}
    for t in a.tracker:
        assert len(t) in (6, 7), "--tracker TAG KEYS TRK GT S1A S1B [CACHE]"
        trackers[t[0]] = {"keys": t[1], "trk": t[2], "gt": t[3], "s1a": t[4], "s1b": t[5], "cache": t[6] if len(t) == 7 else None}
    if a.synthetic:
        B = a.boot or CFG["B"]
        binding = None
    else:
        assert a.boot is None, "B comes from the bound configuration on real data"
        assert a.plan, "real data need the frozen plan"
        assert all(d["cache"] for d in trackers.values()), "real data need each tracker's cache directory"
        B = CFG["B"]
        binding = check_binding_real(a.plan, trackers)
    out = {"stamp": A1.SYN_STAMP if a.synthetic else "TPP arm analysis v03 on the frozen D17 v03 plan", "analysis_sha256": C.sha256_path(os.path.abspath(__file__)),
           "code_sha256": {G.rel(f): C.sha256_path(f) for f in code_files()}, "B": B, "config": CFG,
           "plan_sidecar": binding[0] if binding else None, "trackers": {}}
    per_tracker = {}
    for tag, d in trackers.items():
        shas = check_runs(d["keys"], {k: d[k] for k in ("trk", "gt", "s1a", "s1b")}, a.synthetic)
        kz, runs, gt_xy, trk_mu, trk_cov = A1.load_inputs(d["keys"], {"trk": d["trk"], "gt": d["gt"]}, a.synthetic, d["cache"])
        seeds = {}
        for role in ("s1a", "s1b"):
            _, r1, _, _, _ = A1.load_inputs(d["keys"], {"trk": d[role]}, a.synthetic, d["cache"])
            seeds[role] = r1["trk"]
        R = {"inputs_sha256": dict(shas, keys=C.sha256_path(d["keys"]))}
        R["primary_v2"] = analyse_v03(kz, runs, gt_xy, trk_mu, trk_cov, CFG["variants"]["primary"], B)
        R["secondary_v1"] = analyse_v03(kz, runs, gt_xy, trk_mu, trk_cov, CFG["variants"]["secondary"], B)
        R["sensitivity_tail_excluded_v2"] = analyse_v03(kz, runs, gt_xy, trk_mu, trk_cov, "v2", B, tail_cap=CFG["tail_trace_m2"])
        by = {PRIMARY: R["primary_v2"]["hypotheses"]}
        R["S1"] = {}
        for role, sd in (("s1a", S1_SEEDS[0]), ("s1b", S1_SEEDS[1])):
            r = analyse_v03(kz, {"trk": seeds[role], "gt": runs["gt"]}, gt_xy, trk_mu, trk_cov, "v2", B)
            R["S1"][str(sd)] = r
            by[sd] = r["hypotheses"]
        pooled = A2.pooled_run([runs["trk"], seeds["s1a"], seeds["s1b"]], len(kz["rec_k"]))
        R["S2_seed_pooled_v2_descriptive"] = analyse_v03(kz, {"trk": pooled, "gt": runs["gt"]}, gt_xy, trk_mu, trk_cov, "v2", B)
        per_tracker[tag] = by
        out["trackers"][tag] = R
    out["decision"] = decide(per_tracker)
    out["decision_note"] = ("development-side evidence (D16 Choice 29), along the K8 tracker-planner's constraints; S1 varies the "
                            "tracker-history Trajectron++ arm, the ground-truth arm stays at seed %d; 'seed-robust' means three draws" % PRIMARY)
    out["seconds"] = round(time.time() - t0, 1)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print(json.dumps({h: v["code"] for h, v in out["decision"].items()}))
    print("TPP ANALYSE V03 DONE")
    return out


if __name__ == "__main__":
    main()
