#!/usr/bin/env python3
"""c1crit_fwcheck_v01 (5 Nov 2026): the development verdict under the stricter removal rule the evidence review proposes (section
3.3 option ii; D16 Choice 47e direction): a comparator leaves V_t only if one of the nine removal conditions (PD7, SD1_7, PD x
{all-evaluable cell flag, power-family cell flag, pooled lower bound > delta}) holds at the familywise level, each condition at
1 - 0.05 / 9 (Bonferroni). nuScenes K8 development data only; K8 v03 weights ([20261106, i, 0], B = 2000); the power-qualified
families are each arm's development families (c1crit_sweep_v01 baseline). Forms B (and A, C) via c1crit_common_v01.forms with the
removal status replaced. Also lists M*'s 'moving-car' power (the review's proposed floor condition). Deterministic; one JSON.
Usage: python -B c1crit_fwcheck_v01.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1crit_common_v01 as C  # noqa: E402
import numpy as np  # noqa: E402

A = C.A
LEVEL = 1 - 0.05 / 9


def main():
    out = {"level_each": LEVEL, "trackers": {}}
    for tag in C.TAGS:
        dev = C.Dev(tag)
        W, _ = dev.weights()
        with open(os.path.join(C.OUT, "sweep_ckpt", "sweep_%s_rho0.5000_p0.1500.json" % tag)) as f:
            base = json.load(f)["hk1"]
        one = np.ones((1, len(dev.scenes)))
        status, det = {}, {}
        for arm in C.ARMS:
            removed, why = False, []
            for p in C.POPS:
                lab = C.LAB[p]
                N, X = dev.T(arm)[p]
                ev = np.flatnonzero(A.evaluable(N, dev.scenes, dev.log_idx))
                est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
                if len(ev):
                    sig = A.flag(est, boot, ev, LEVEL)[3]
                    if sig.any():
                        removed = True
                        why.append("%s cells %s" % (lab, [C.CELL_NAMES[ev[i]] for i in np.flatnonzero(sig)]))
                fam = np.array([C.CELL_NAMES.index(c) for c in base[arm]["pops"][lab]["family"]], int)
                if len(fam):
                    sig = A.flag(est, boot, fam, LEVEL)[3]
                    if sig.any():
                        removed = True
                        why.append("%s family %s" % (lab, [C.CELL_NAMES[fam[i]] for i in np.flatnonzero(sig)]))
                Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
                if A.evaluable(Np, dev.scenes, dev.log_idx)[0]:
                    e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
                    if A.flag(e1, b1, np.array([0]), LEVEL)[3][0]:
                        removed = True
                        why.append("%s pooled" % lab)
            st = C.status_from_hk1({"pops": {p: {"flagged": base[arm]["pops"][C.LAB[p]]["flagged"],
                                                 "family_flagged": base[arm]["pops"][C.LAB[p]]["family_flagged"],
                                                 "pooled": base[arm]["pops"][C.LAB[p]]["pooled"],
                                                 "family_size": base[arm]["pops"][C.LAB[p]]["family_size"],
                                                 "evaluable": base[arm]["pops"][C.LAB[p]]["evaluable"]} for p in C.POPS}})
            st["shown_v07d"] = removed           # the familywise removal replaces the v07d removal
            status[arm], det[arm] = st, why
        fm = C.forms(dev, W, status)
        v = C.verdict_summary(status, fm)
        mc = {c: base["Mstar"]["pops"][lab]["power"].get(c) for lab in ("PD7", "SD1_7")
              for c in C.CELL_NAMES if c.startswith("car|") and not c.endswith("static")}
        out["trackers"][tag] = {"V_t_familywise": v["not_shown_v07d"], "formB_familywise": v["formB_v07d"],
                                "formB_ub": fm["B_v07d_flags_only"]["ub"], "removal_reasons": det,
                                "Mstar_moving_car_power_200": {lab: {c: base["Mstar"]["pops"][lab]["power"].get(c)
                                                                     for c in C.CELL_NAMES if c.startswith("car|") and not c.endswith("static")}
                                                               for lab in ("PD7", "SD1_7")},
                                "Mstar_family_SD1_7": base["Mstar"]["pops"]["SD1_7"]["family"]}
        print(tag, "V_t familywise", v["not_shown_v07d"], "Form B", v["formB_v07d"], fm["B_v07d_flags_only"]["ub"], flush=True)
    C.jdump(os.path.join(C.OUT, "fwcheck_v01.json"), out)
    print("FWCHECK DONE")


if __name__ == "__main__":
    main()
