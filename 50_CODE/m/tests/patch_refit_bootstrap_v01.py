"""Pre-freeze patch (31 Oct 2026): m_lib_v01 statistics refactor with the two-sample refit bootstrap for E2 and
log resampling; replaces the E2 subsample averaging. Applied once; kept as a record."""
import os

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(HERE, "m_lib_v01.py")
t = open(p, encoding="utf-8").read()
start = t.index("def eval_stats(")
end = t.index("def hypotheses(")
new = r'''def resample_logs(items, recs, mult):
    """Log-cluster bootstrap copy of a split: log l enters mult[l] times; every copy of a scene (and of its log) gets
    its own id, so duplicated scenes count as distinct calibration units."""
    sm = mult[items["scene_log_idx"]].astype(int)
    soff = np.concatenate([[0], np.cumsum(sm)[:-1]]).astype(int)
    loff = np.concatenate([[0], np.cumsum(mult)[:-1]]).astype(int)
    out = {"n_scenes": int(sm.sum()), "n_logs": int(mult.sum())}
    out["scene_log_idx"] = np.concatenate([loff[items["scene_log_idx"][i]] + np.arange(sm[i]) for i in range(len(sm))]).astype(int)

    def rep(sidx):
        r = sm[sidx]
        idx = np.repeat(np.arange(len(sidx)), r)
        copy = np.arange(len(idx)) - np.repeat(np.cumsum(r) - r, r)
        return idx, copy
    idx, copy = rep(items["s"])
    for k in ("g", "r", "a", "spd", "om", "omv", "V", "contested", "D"):
        out[k] = items[k][idx]
    out["s"] = soff[items["s"][idx]] + copy
    out["lg"] = loff[items["lg"][idx]] + copy
    ridx, rcopy = rep(recs["s"])
    rc = {k: recs[k][ridx] for k in ("g", "r", "dx", "dy", "sxx", "sxy", "syy", "contested")}
    rc["s"] = soff[recs["s"][ridx]] + rcopy
    return out, rc


def _layout(items, P, eval_strata, sel):
    if sel is None:
        sel = np.ones(len(items["D"]), bool)
    S = items["n_scenes"]
    s, l0, a, D = items["s"][sel], P["lv"][0][sel], items["a"][sel], items["D"][sel]
    G = list(eval_strata)
    gpos = {g: j for j, g in enumerate(G)}
    in_eval = np.isin(l0, G)
    col = np.array([gpos.get(int(x), -1) for x in l0])
    n_ig = np.zeros((S, len(G)))
    np.add.at(n_ig, (s[in_eval], col[in_eval]), 1.0)
    return {"S": S, "sel": sel, "s": s, "l0": l0, "a": a, "D": D, "G": G, "col": col, "in_eval": in_eval, "n_ig": n_ig,
            "pres": (n_ig > 0).astype(float)}


def _tables(lay, mg, exc):
    S, s, ie, col, n_ig = lay["S"], lay["s"], lay["in_eval"], lay["col"], lay["n_ig"]
    e_ig = np.zeros_like(n_ig)
    np.add.at(e_ig, (s[ie], col[ie]), exc[ie])
    tab = {"e": e_ig, "p": np.divide(e_ig, n_ig, out=np.zeros_like(e_ig), where=n_ig > 0), "mg": mg,
           "msum": np.bincount(s[ie], weights=mg[ie], minlength=S), "cnt": np.bincount(s[ie], minlength=S).astype(float), "ax": []}
    for ax in (0, 1):
        k = ie & (lay["a"] == ax)
        tab["ax"].append((np.bincount(s[k], weights=mg[k], minlength=S), np.bincount(s[k], minlength=S).astype(float)))
    return tab


def _boot_rows(lay, tab, W):
    with np.errstate(invalid="ignore", divide="ignore"):
        est = (W @ tab["p"]) / (W @ lay["pres"])
        mb = (W @ tab["msum"]) / (W @ tab["cnt"])
        ax = [(W @ ms) / (W @ cn) for ms, cn in tab["ax"]]
    return est, mb, ax


def _summary(lay, tabs, boots, delta, level):
    G, n_ig, pres = lay["G"], lay["n_ig"], lay["pres"]
    res = {}
    for meth, tab in tabs.items():
        boot, mb, axb = boots[meth]
        est = tab["p"].sum(0) / pres.sum(0)
        se = np.nanstd(boot, axis=0, ddof=1)
        ok = se > 0
        with np.errstate(invalid="ignore", divide="ignore"):
            T = np.nanmax(np.where(ok, (boot - est) / np.where(ok, se, 1.0), np.nan), axis=1) if ok.any() else np.full(len(boot), np.nan)
        q = float(np.nanquantile(T, level)) if np.isfinite(T).any() else float("nan")
        lb = np.where(ok, est - q * se, est)
        sig = ok & (lb > delta)
        rec_share = tab["e"].sum(0) / n_ig.sum(0)
        mg, ie = tab["mg"], lay["in_eval"]
        by_axis = {AXES[i]: {"mean_margin_m": float(tab["ax"][i][0].sum() / tab["ax"][i][1].sum()),
                             "ci": [float(x) for x in np.nanquantile(axb[i], [0.025, 0.975])]} for i in (0, 1)}
        res[meth] = {
            "strata": {l0_name(g): {"E_scene": float(est[j]), "E_rec": float(rec_share[j]), "lb_sim": float(lb[j]), "se": float(se[j]),
                                    "sig_under": bool(sig[j]), "n_items": int(n_ig[:, j].sum()), "n_scenes": int(pres[:, j].sum()),
                                    "mean_margin_m": float(np.sum(mg[ie & (lay["l0"] == g)]) / max(n_ig[:, j].sum(), 1))}
                       for j, g in enumerate(G)},
            "q_sim": q, "any_sig_under": bool(sig.any()), "sig_under_strata": [l0_name(G[j]) for j in np.flatnonzero(sig)],
            "E_bar": float(np.mean(est)), "E_bar_ub95": float(np.nanquantile(np.nanmean(boot, axis=1), level)),
            "max_E_scene": float(np.max(est)),
            "mean_margin_m": float(tab["msum"].sum() / tab["cnt"].sum()), "mean_margin_ci": [float(x) for x in np.nanquantile(mb, [0.025, 0.975])],
            "mean_margin_by_axis": by_axis}
    ratios = {}
    for num, den in (("Mstar", "B3"), ("Mstar", "B6c"), ("MLS", "Mstar"), ("Mstar", "B7"), ("Mstar", "B6"), ("Mstar", "B2"), ("MLS", "B3")):
        if num in tabs and den in tabs:
            rb = boots[num][1] / boots[den][1]
            ratios["%s/%s" % (num, den)] = {"point": res[num]["mean_margin_m"] / res[den]["mean_margin_m"],
                                            "ci": [float(x) for x in np.nanquantile(rb, [0.025, 0.975])]}
    return {"methods": res, "ratios": ratios, "evaluated_strata": [l0_name(g) for g in G], "n_items_eval": int(lay["in_eval"].sum()),
            "n_boot": int(len(next(iter(boots.values()))[1]))}


def eval_stats(items, P, marg, eval_strata, W, sel=None, delta=DELTA, level=0.95, exc_frac=None):
    """Exceedance (scene mean, primary; record share), one-sided simultaneous lower bounds, mean-exceedance upper bound,
    and mean margins with paired bootstrap ratios, the fitted rules held fixed. W: (B, n_scenes) bootstrap scene weights
    shared by all methods. exc_frac: optional per-item exceedance fractions (average over repeated fits)."""
    lay = _layout(items, P, eval_strata, sel)
    tabs, boots = {}, {}
    for meth, mg in marg.items():
        mg = mg[lay["sel"]]
        exc = (lay["D"] > mg).astype(float) if exc_frac is None else exc_frac[meth][lay["sel"]]
        tabs[meth] = _tables(lay, mg, exc)
        boots[meth] = _boot_rows(lay, tabs[meth], W)
    return _summary(lay, tabs, boots, delta, level)


def eval_stats_refit(items, P, marg_point, eval_strata, replicates, delta=DELTA, level=0.95):
    """As eval_stats, but every bootstrap replicate refits every rule: replicates yields (margins of the replicate's
    refitted rules on all evaluation items, the replicate's evaluation scene weights). The point estimate uses marg_point."""
    lay = _layout(items, P, eval_strata, None)
    tabs = {m: _tables(lay, mg, (lay["D"] > mg).astype(float)) for m, mg in marg_point.items()}
    acc = {m: ([], [], [], []) for m in marg_point}
    for marg_b, w_b in replicates:
        for m, mg in marg_b.items():
            est, mb, ax = _boot_rows(lay, _tables(lay, mg, (lay["D"] > mg).astype(float)), w_b[None, :])
            acc[m][0].append(est[0])
            acc[m][1].append(mb[0])
            acc[m][2].append(ax[0][0])
            acc[m][3].append(ax[1][0])
    boots = {m: (np.array(v[0]), np.array(v[1]), [np.array(v[2]), np.array(v[3])]) for m, v in acc.items()}
    return _summary(lay, tabs, boots, delta, level)


'''
t = t[:start] + new + t[end:]
a = ("R_SUB = 20  # calibration subsamples of SUB_FRAC of the train logs (E2)\n"
     "SUB_FRAC = 0.8  # share of train logs per E2 subsample: 40 of 50\n")
b = "B_REFIT = 1000  # E2: replicates of the two-sample log bootstrap that refits every rule on resampled train logs\n"
assert t.count(a) == 1
t = t.replace(a, b)
open(p, "w", encoding="utf-8", newline="\n").write(t)

p = os.path.join(HERE, "m_run_v01.py")
t = open(p, encoding="utf-8").read()
start = t.index("def run_e2(")
end = t.index("def compact(")
new = r'''def run_e2(tr, trr, va, var, cfg, ev, label, B=M.B_REFIT):
    """E2: every rule fitted on all train scenes (the deployable rule) and evaluated on val. Inference by a two-sample
    log bootstrap: each replicate resamples train logs and val logs, refits every rule on the resampled train, and
    evaluates it on the resampled val, so calibration and test randomness both enter."""
    Pt, Pv = M.prepare(tr, trr, cfg), M.prepare(va, var, cfg)
    allv = np.ones(len(va["D"]), bool)
    fit = M.fit_methods(tr, trr, Pt, np.ones(tr["n_scenes"], bool), cfg)
    rng = rng_for(label)

    def replicates():
        for _ in range(B):
            mt = rng.multinomial(tr["n_logs"], np.full(tr["n_logs"], 1.0 / tr["n_logs"]))
            mv = rng.multinomial(va["n_logs"], np.full(va["n_logs"], 1.0 / va["n_logs"]))
            tb, tbr = M.resample_logs(tr, trr, mt)
            fb = M.fit_methods(tb, tbr, M.prepare(tb, tbr, cfg), np.ones(tb["n_scenes"], bool), cfg)
            yield M.margins(va, Pv, fb, allv), mv[va["scene_log_idx"]].astype(float)
    st = M.eval_stats_refit(va, Pv, M.margins(va, Pv, fit, allv), ev, replicates())
    st["hypotheses"] = M.hypotheses(st, ub_margin=0.03)
    st["fit_on_all_train"] = fit_summary(fit, full=True)
    st["config"] = cfg
    return st


'''
t = t[:start] + new + t[end:]
open(p, "w", encoding="utf-8", newline="\n").write(t)
print("patched")
