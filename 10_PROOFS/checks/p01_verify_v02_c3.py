"""Corollary 3 checks, v02 (supersedes the C3 flag of p01_verify_v01, whose test wrongly expected the
converse of Corollary 3). Deterministic 1-D following; margin-sufficient planner; numpy + stdlib.
C3a: representable dose (Q = 0, global) -> identical trajectory after retuning to c*sqrt(s).
C3b: non-representable dose (Q > 0) whose binding horizon never changes -> a single global c' still
     reproduces the commands (converse of Cor. 3 fails; recorded in v01 as best_mismatch = 0).
C3c: non-representable dose with a lead that brakes, so the binding horizon switches -> no single global c'
     on a fine grid reproduces the dosed trajectory (nonzero residual), while per-horizon multipliers (K3) do."""
import json, math, os
from statistics import NormalDist
import numpy as np

c0 = NormalDist().inv_cdf(0.99)
HS = [0.5, 1.0, 2.0, 4.0]


def sim(sp2, sv2, qcoef, cmult, brake, steps=120, dt=0.1):
    ex, ev, ox, ov = 0.0, 14.0, 45.0, 12.0
    grid = np.round(np.arange(-8.0, 2.0001, 0.05), 2)
    errs = np.random.default_rng(11).normal(0, 0.25, (steps, 2)); traj, binding = [], []
    for k in range(steps):
        if brake and 40 <= k < 70:
            ov = max(0.0, ov - 0.6)  # lead decelerates 6 m/s^2
        mx, mv = ox + errs[k, 0], ov + 0.2 * errs[k, 1]
        best, bh = float(grid[0]), None
        for acc in grid[::-1]:
            feas, slack_min, hmin = True, 1e9, None
            for j, t in enumerate(HS):
                vh = sp2 + t * t * sv2 + qcoef * t * t
                cm = cmult[j] if isinstance(cmult, (list, tuple)) else cmult
                slack = (mx + mv * t - cm * math.sqrt(vh)) - (ex + ev * t + 0.5 * acc * t * t + 4.5)
                if slack < 0:
                    feas = False; break
                if slack < slack_min:
                    slack_min, hmin = slack, t
            if feas:
                best, bh = float(acc), hmin; break
        traj.append(best); binding.append(bh)
        ev = max(0.0, ev + best * dt); ex += ev * dt; ox += ov * dt
    return traj, binding


s = 3.0; sp2, sv2, q = 0.04, 0.25, 0.5
res = {}
d0, _ = sim(s * sp2, s * sv2, 0.0, c0, brake=True); r0, _ = sim(sp2, sv2, 0.0, c0 * math.sqrt(s), brake=True)
b0, _ = sim(sp2, sv2, 0.0, c0, brake=True)
res["C3a_Q0_identical_after_retune"] = d0 == r0; res["C3a_dose_changes_commands"] = d0 != b0
dq, _ = sim(s * sp2, s * sv2, q, c0, brake=False)
mm_nb = min(sum(abs(x - y) for x, y in zip(dq, sim(sp2, sv2, q, cc, brake=False)[0])) for cc in np.linspace(c0, 3 * c0, 1601))
res["C3b_no_brake_min_global_mismatch"] = mm_nb
dqb, bind = sim(s * sp2, s * sv2, q, c0, brake=True)
mm_b = min(sum(abs(x - y) for x, y in zip(dqb, sim(sp2, sv2, q, cc, brake=True)[0])) for cc in np.linspace(c0, 3 * c0, 1601))
per_c = [c0 * math.sqrt((s * (sp2 + t * t * sv2) + q * t * t) / ((sp2 + t * t * sv2) + q * t * t)) for t in HS]
k3, _ = sim(sp2, sv2, q, per_c, brake=True)
res["C3c_binding_horizons_seen"] = sorted({h for h in bind if h is not None})
res["C3c_min_global_mismatch_sum_abs_accel"] = mm_b
res["C3c_K3_identical"] = k3 == dqb
res["ratio_R_by_horizon"] = [c / c0 for c in per_c]
ok = {"C3a": bool(res["C3a_Q0_identical_after_retune"] and res["C3a_dose_changes_commands"]),
      "C3c": bool(len(res["C3c_binding_horizons_seen"]) >= 2 and mm_b > 0 and res["C3c_K3_identical"])}
res["pass_flags"] = ok; res["ALL_PASS"] = all(ok.values())
json.dump(res, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "p01_verify_v02_c3_results.json"), "w"), indent=1)
print(json.dumps(res, indent=1))
