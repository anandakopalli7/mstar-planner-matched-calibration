#!/usr/bin/env python3
"""Step 3 of k6_sim_v02 (Claude line, 1 Nov 2026; review R09b MJ1), applied after make_k6_sim_v02_step2.py: when no
candidate satisfies the enforced constraints at the arm's margin, the planner no longer brakes at once. It backs the
margin off on the same enforced set, lambda in BACKOFF = (0.75, 0.5, 0.25, 0), and takes the max-progress feasible
candidate at the largest feasible lambda; the emergency stop only if no candidate is feasible even at lambda = 0 (the
buffered mean footprints). "infeasible" still means infeasible at the full margin, so the HK3 indicator is unchanged; the
lambda used is recorded. A closed-loop collision within FALLBACK_WINDOW of an infeasible decision is flagged
fallback_related. Run once."""
import os

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(K, "k6_sim_v02.py")
s = open(p, encoding="utf-8").read()
assert "BACKOFF" not in s, "step 3 already applied"
NL = "\n"
rep = [
    ("    keyframe, no dynamics). The decision mode scores the constraints each arm's planner relies on with exact replayed" + NL
     + "    perception; the closed loop gives the operational outcomes.",
     "    keyframe, no dynamics). The decision mode scores the constraints each arm's planner relies on with exact replayed" + NL
     + "    perception; the closed loop gives the operational outcomes." + NL
     + "  * R09b MJ1: when no candidate satisfies the enforced constraints at the arm's margin (an infeasible decision), the" + NL
     + "    margin is backed off on the same enforced set, lambda in BACKOFF, and the max-progress candidate at the largest" + NL
     + "    feasible lambda is taken; the emergency stop only if even lambda = 0 (the buffered mean footprints) is infeasible." + NL
     + "    An immediate emergency stop could brake the ego into a crossing agent's path where a smaller margin kept going." + NL
     + "    A closed-loop collision within FALLBACK_WINDOW of an infeasible decision is flagged fallback_related."),
    ("CC_STEPS = CC_EVAL // 2" + " " * 78 + "# calibrated steps recorded",
     "CC_STEPS = CC_EVAL // 2" + " " * 78 + "# calibrated steps recorded" + NL
     + "BACKOFF = (0.75, 0.5, 0.25, 0.0)" + " " * 69 + "# margin back-off (R09b MJ1)" + NL
     + "FALLBACK_WINDOW = 2.0" + " " * 80 + "# s: collisions this soon after an infeasible decision"),
    ('    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0}',
     '    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0, "lam": 1.0}'),
    ('    if feas.any():' + NL
     + '        out["choice"] = int(np.argmax(np.where(feas, prog, -np.inf)))' + NL
     + '    else:' + NL
     + '        out["choice"] = N_C - 1          # no plan satisfies the enforced constraints: the emergency stop (fail-safe)' + NL
     + '        out["infeasible"] = True',
     '    if feas.any():' + NL
     + '        out["choice"] = int(np.argmax(np.where(feas, prog, -np.inf)))' + NL
     + '    else:' + NL
     + '        out["infeasible"] = True          # infeasible at the arm\'s margin (the HK3 indicator)' + NL
     + '        out["choice"], out["lam"] = N_C - 1, None' + NL
     + '        for lam in BACKOFF:               # back the margin off on the same enforced set (R09b MJ1)' + NL
     + '            sl = np.max(gap - lam * mg16.transpose(1, 0, 2)[None], axis=-1)[:, :CC_EVAL]' + NL
     + '            fl = (np.maximum(0.0, -sl) * enf[None]).sum(axis=(1, 2)) == 0.0' + NL
     + '            if fl.any():' + NL
     + '                out["choice"], out["lam"] = int(np.argmax(np.where(fl, prog, -np.inf))), lam' + NL
     + '                break                     # else: the emergency stop (fail-safe)'),
    # closed loop: counters, last infeasible time, fallback flag on collisions
    ('        infeasible += int(ps["infeasible"])' + NL
     + '        unctrl += ps["unctrl"]' + NL
     + '        unctrl_frames += int(ps["unctrl"] > 0)',
     '        infeasible += int(ps["infeasible"])' + NL
     + '        estops += int(ps["infeasible"] and ps["lam"] is None)' + NL
     + '        if ps["infeasible"]:' + NL
     + '            t_last_inf = tk' + NL
     + '        unctrl += ps["unctrl"]' + NL
     + '        unctrl_frames += int(ps["unctrl"] > 0)'),
    ('    unctrl = unctrl_frames = brought = 0' + NL + '    offs = []',
     '    unctrl = unctrl_frames = brought = estops = 0' + NL + '    t_last_inf = -1e9' + NL + '    offs = []'),
    ('                                              "cls": int(sc.gt["cls"][sc.gt_inst_rows[inst][0]])}',
     '                                              "cls": int(sc.gt["cls"][sc.gt_inst_rows[inst][0]]),' + NL
     + '                                              "fallback_related": bool(t - t_last_inf <= FALLBACK_WINDOW)}'),
    ('                "uncontrollable_pairs": unctrl, "uncontrollable_frames": unctrl_frames, "brought_to_ego_pairs": brought,' + NL
     + '                "sensor_offset_median"',
     '                "uncontrollable_pairs": unctrl, "uncontrollable_frames": unctrl_frames, "brought_to_ego_pairs": brought,' + NL
     + '                "emergency_stop_frames": estops,' + NL
     + '                "sensor_offset_median"'),
    # decision mode counters
    ('    frames = infeasible = unctrl = brought = 0' + NL + '    acc = []',
     '    frames = infeasible = unctrl = brought = estops = 0' + NL + '    acc = []'),
    ('        infeasible += int(ps["infeasible"])' + NL
     + '        unctrl += ps["unctrl"]' + NL
     + '        brought += ps["brought"]' + NL
     + '        acc.append(float(ACC_TABLE[ps["choice"], 0]))',
     '        infeasible += int(ps["infeasible"])' + NL
     + '        estops += int(ps["infeasible"] and ps["lam"] is None)' + NL
     + '        unctrl += ps["unctrl"]' + NL
     + '        brought += ps["brought"]' + NL
     + '        acc.append(float(ACC_TABLE[ps["choice"], 0]))'),
    ('    out.update({"frames": frames, "infeasible_frames": infeasible, "uncontrollable_pairs": unctrl, "brought_to_ego_pairs": brought,',
     '    out.update({"frames": frames, "infeasible_frames": infeasible, "emergency_stop_frames": estops, "uncontrollable_pairs": unctrl,' + NL
     + '                "brought_to_ego_pairs": brought,'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("step 3 applied")
