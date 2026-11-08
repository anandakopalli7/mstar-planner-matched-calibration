#!/usr/bin/env python3
"""Generator of c1_analyse_v02.py from c1_analyse_v01.py (Claude line, 2 Nov 2026), asserted replacements; v01 is not modified.
v02 adds: RETUNED-HK1 (slot S1c, descriptive), H8 from c1_h8_v01's output, H9 and Q1 from c1_predarm_v01's outputs (H6a, H6b,
H7 from c1_mstage_v01's output already fit v01's rules). Usage (from 50_CODE/c1_av2): python -B tests/make_c1_analyse_v02.py
"""
import hashlib
import os

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RHK1 = r'''
def retuned_hk1(tabs, cells, keys, scene_of_ep, log_of_ep, W, fold_of_key, sweep, power_key):
    """RETUNED-HK1 (slot S1c, descriptive; R16 M4): for each fold f, the least conservative point of the merged alpha/delta' curve
    (ordered by alpha_eq) that is Valid by Form B's own rule (arm_status: HK1 with the floors, and HK1c) on the training folds
    (the keys of the other folds; the log-bootstrap weights restricted to them), applied to fold f's keys. If no point qualifies,
    the most conservative point is used and flagged. Returns the per-fold choice and the composite's per-key tables."""
    curve = sorted(sweep, key=lambda a: (S.CURVE_ALPHA_OF_ARM[a], a))
    choice = {}
    for f in sorted(set(fold_of_key.tolist())):
        tr = fold_of_key != f
        pick, tried = None, 0
        for a in curve:
            T = {p: (tabs[p][0][a][tr], tabs[p][1][a][tr]) for p in POPS}
            v = K.hk1_rule(T, cells, scene_of_ep[tr], log_of_ep[tr], W[:, tr], list(power_key) + [200 + K.ARM_INDEX[a], int(f)], arm=a)
            tried += 1
            if arm_status(v)["valid"]:
                pick = a
                break
        choice[int(f)] = {"arm": pick or curve[-1], "none_qualifies": pick is None, "points_tried": tried,
                          "alpha_eq": S.CURVE_ALPHA_OF_ARM[pick or curve[-1]]}
    arm_of_key = [choice[int(f)]["arm"] for f in fold_of_key]
    T = {}
    for p in POPS:
        N = np.stack([tabs[p][0][a][i] for i, a in enumerate(arm_of_key)])
        Xx = np.stack([tabs[p][1][a][i] for i, a in enumerate(arm_of_key)])
        T[p] = (N, Xx)
    return choice, arm_of_key, T

'''

BLOCK = r'''    # RETUNED-HK1 (slot S1c, descriptive): cross-fitted on Form B's validity rule
    if route == "within_lt3d" and fits is not None and sweep:
        cells_ = A.cell_family()
        _, tabs_s = A.populations(eps_f, counts, sweep, keys, scene_of_ep, log_of_ep, W, {p: K.POP_DECIDE[p] for p in POPS})
        fold_of_key = np.array([int(fits["fold_of_scene"][k[0]]) for k in keys])
        choice, arm_of_key, Tc = retuned_hk1(tabs_s, cells_, keys, scene_of_ep, log_of_ep, W, fold_of_key, sweep, sp)
        vc = K.hk1_rule(Tc, cells_, scene_of_ep, log_of_ep, W, list(sp) + [300], arm="RETUNED_HK1")
        aok = {k[0]: arm_of_key[ii] for ii, k in enumerate(keys)}
        rate["RETUNED_HK1"] = np.array([rate[aok[sc]][ii] for ii, sc in enumerate(scenes)])
        st_c = arm_status(vc)
        pr = paired(rate, Ws, "Mstar", "RETUNED_HK1", 0.95)
        pr.pop("_bm")
        out["RETUNED_HK1"] = {"label": "descriptive (slot S1c; R16 M4)", "choice_by_fold": choice, "status": st_c,
                              "infeasible_rate": float(rate["RETUNED_HK1"].mean()), "Mstar_minus_RETUNED_HK1": pr,
                              "rule": "least conservative merged-curve point Valid by Form B's rule on the training folds, applied to the held-out fold"}
'''


def rep(s, old, new):
    assert s.count(old) == 1, "expected one occurrence of %r" % old[:90]
    return s.replace(old, new)


def make(src):
    s = src
    s = rep(s, '"""C1 analysis (Claude line, c1_analyse_v01, 2 Nov 2026)',
            '"""C1 analysis (Claude line, c1_analyse_v02, 2 Nov 2026) = c1_analyse_v01 (kept) plus, written by tests/make_c1_analyse_v02.py:\n'
            'RETUNED-HK1 (slot S1c, descriptive: cross-fitted on Form B\'s validity rule); H8 from c1_h8_v01\'s output (its "H8"); H9 and Q1\n'
            'from c1_predarm_v01\'s outputs (config "h9": {t: path}); H6a, H6b, H7 from c1_mstage_v01\'s outputs (config "method_stage").\n'
            'C1 analysis (Claude line, c1_analyse_v01, 2 Nov 2026)')
    s = rep(s, "\n# ---------------------------------------------------------------- one route x tracker (decision mode)\n",
            RHK1 + "\n# ---------------------------------------------------------------- one route x tracker (decision mode)\n")
    s = rep(s, '    out["power_family_seeds"] = {', BLOCK + '    out["power_family_seeds"] = {')
    s = rep(s, '    if cfg.get("_h8"):\n        dec["hypotheses"]["H8"] = dict(h8_rule(cfg["_h8"]), label="secondary, family P at 0.05")\n',
            '    if cfg.get("_h8"):\n'
            '        h8 = cfg["_h8"]\n'
            '        dec["hypotheses"]["H8"] = (dict(h8, label="secondary, family P at 0.05 (c1_h8_v01)") if "H8" in h8\n'
            '                                   else dict(h8_rule(h8), label="secondary, family P at 0.05"))\n')
    s = rep(s, '        dec["hypotheses"]["H9"] = {"label": "secondary (no-flag, floor 6)", "holds": all(v["H9"] for v in cfg["_h9"].values()), "by_tracker": cfg["_h9"]}\n',
            '        dec["hypotheses"]["H9"] = {"label": "secondary (no-flag, floor 6)", "holds": all(v["H9"] for v in cfg["_h9"].values()),\n'
            '                                   "by_tracker": {t: v["arms"].get("TPP") for t, v in cfg["_h9"].items()}}\n'
            '        q1 = {t: {k: v["arms"][k] for k in ("Q1_deployed", "Q1_gt") if k in v["arms"]} for t, v in cfg["_h9"].items()}\n'
            '        if any(q1.values()):\n'
            '            dec["hypotheses"]["Q1"] = {"label": "descriptive (Choice 20)", "by_tracker": q1}\n')
    s = rep(s, '    if cfg.get("h8"):\n        cfg["_h8"] = json.load(open(cfg["h8"]))\n',
            '    if cfg.get("h8"):\n        cfg["_h8"] = json.load(open(cfg["h8"]))\n'
            '    if cfg.get("h9"):\n        cfg["_h9"] = {t: json.load(open(p)) for t, p in cfg["h9"].items()}\n')
    s = rep(s, '    print("C1 ANALYSIS V01 DONE")\n', '    print("C1 ANALYSIS V02 DONE")\n')
    return s


def main():
    with open(os.path.join(C1, "c1_analyse_v01.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(C1, "c1_analyse_v02.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "c1_analyse_v02.py")


if __name__ == "__main__":
    main()
