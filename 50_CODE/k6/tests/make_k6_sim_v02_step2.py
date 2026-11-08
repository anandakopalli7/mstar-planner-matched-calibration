#!/usr/bin/env python3
"""Step 2 of k6_sim_v02 (Claude line, 1 Nov 2026), applied to the output of make_k6_sim_v02.py (step 1). Development
iteration dev v06/v07 (D09 v04 section 0): chance constraints are enforced to 2 s, the method's decision horizon; the
planning step becomes a function shared by the closed loop (run_episode) and a new decision mode (run_decisions), in which
the planner decides at every keyframe from the logged ego's own state, so the replayed perception is exact. Run once."""
import os

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
p = os.path.join(K, "k6_sim_v02.py")
s = open(p, encoding="utf-8").read()
assert "def plan_step(" not in s, "step 2 already applied"

old_head = '''  * M1, M2, m7: each in-loop record also carries the method\'s in-path flag, whether the pair was enforced, whether the
    plan satisfied its relied-on axis at the margin, and the sensor-offset bin (logged ego ahead of the simulated ego by
    at most 5, 5 to 15, or more than 15 m); annotations inside a bicycle rack at k + h are censored, as in the method.'''
new_head = old_head + '''
  * Development iteration (D09 v04): the chance constraints are enforced at the check times up to 2 s (CC_EVAL), the
    method's decision horizon; with them enforced to 4 s every margin arm was infeasible in 51-81 % of development frames.
    The plan is still scored over 4 s. In-loop records are taken at the enforced calibrated steps (0.5 to 2 s).
  * Two modes share plan_step: run_episode (closed loop, as before) and run_decisions (at every keyframe k >= 1 the
    planner decides from the logged ego's own position and speed, leash = the log, sensor offset 0; one decision per
    keyframe, no dynamics). The decision mode scores the constraints each arm's planner relies on with exact replayed
    perception; the closed loop gives the operational outcomes.'''
assert s.count(old_head) == 1
s = s.replace(old_head, new_head, 1)

old_c = 'MARGIN_OF_EVAL = np.array([(i + 1) // 2 - 1 for i in range(1, N_EVAL + 1)])                          # next calibrated step'
new_c = old_c + '''
CC_EVAL = 8                                                                                          # constraints enforced to 2 s
CC_STEPS = CC_EVAL // 2                                                                              # calibrated steps recorded'''
assert s.count(old_c) == 1
s = s.replace(old_c, new_c, 1)

# ---- extract the planning block into plan_step
start = s.index("        rows = sc.tr_by_k[k]\n        splan = np.minimum(plan_positions(s, v, vmax), lead(tk + EVAL_T)[None, :])")
end = s.index("        frames += 1\n        offs.append(float(sc.s_log(tk)) - s)")
block = s[start:end]
call = '''        off = float(sc.s_log(tk)) - s
        ob = 0 if off <= OFFSET_BINS[0] else (1 if off <= OFFSET_BINS[1] else 2)
        ps = plan_step(sc, arm, fits, k, s, v, vmax, lead, counts if record else None, ob)
        choice, pen_chosen = ps["choice"], ps["pen"]
        infeasible += int(ps["infeasible"])
        unctrl += ps["unctrl"]
        unctrl_frames += int(ps["unctrl"] > 0)
        brought += ps["brought"]
'''
s = s[:start] + call + s[end:]

PLAN_STEP = '''def plan_step(sc, arm, fits, k, s, v, vmax, lead, counts, ob):
    """One planning cycle at keyframe k from arc length s and speed v. counts: dict to receive the in-loop records of the
    chosen plan (None: no records); ob: the sensor-offset bin of those records. Returns the chosen candidate, whether no
    candidate satisfied the enforced constraints (then the emergency stop), and the exemption counters."""
    tk = float(sc.kf_t[k])
    ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
    rows = sc.tr_by_k[k]
    splan = np.minimum(plan_positions(s, v, vmax), lead(tk + EVAL_T)[None, :])
    prog = splan.mean(axis=1)
    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0}
    if not len(rows) or arm == "LOG":
        return out
    cxe, cye = ex + R2C * math.cos(eyaw), ey + R2C * math.sin(eyaw)
    tr = sc.tr
    dx, dy = tr["x"][rows] - cxe, tr["y"][rows] - cye
    sel = rows[(np.hypot(dx, dy) < R_CONSIDER) & (dx * math.cos(eyaw) + dy * math.sin(eyaw) >= -EGO_L / 2)]
    if not len(sel):
        return out
    sens_pose, sens_v, sens_w = sensor_ctrv(sc, k)
    g, r, m, sd, l0, ax = strata(sc, sel, k, sens_pose, sens_v, sens_w)
    mg = margins(arm, fits, g, r, sd, l0)                         # (J, 8, 2)
    pred_xy = sc.tr["pred"][sel][:, :, :2]                        # (J, 8, 2) at the calibrated steps
    cur = np.stack([sc.tr["x"][sel], sc.tr["y"][sel]], -1)[:, None, :]
    prev = np.concatenate([cur, pred_xy[:, :-1]], 1)
    xy16 = np.empty((len(sel), N_EVAL, 2))
    xy16[:, 1::2] = pred_xy                                       # the 8 steps
    xy16[:, 0::2] = 0.5 * (prev + pred_xy)                        # midpoints, with the margin of the next step
    mg16 = mg[:, MARGIN_OF_EVAL, :]
    half = np.stack([0.5 * sc.tr["l"][sel], 0.5 * sc.tr["w"][sel]], -1)   # (J, 2): long axis -> l/2, lat axis -> w/2
    gap, sep = gaps(sc, splan, xy16, ax, half)                     # (N_C, 16, J, 2)
    slack = np.max(gap - mg16.transpose(1, 0, 2)[None], axis=-1)[:, :CC_EVAL]   # (N_C, 8, J): enforced to 2 s
    # exemptions at the arm-independent reference margin 0 (R09 C1): a (track, check time) pair is exempt if no candidate
    # keeps the buffered mean footprints apart (no speed choice can act on it) or if an ego held at its current position
    # would not (the conflict is brought to the ego); every other pair is enforced at the arm's margin, so the exempt set
    # is the same for every arm
    ctrl = (np.max(gap, axis=-1) >= 0.0).any(axis=0)[:CC_EVAL]    # (8, J)
    ghold, _ = gaps(sc, np.full((1, N_EVAL), s), xy16, ax, half)
    hold_ok = (np.max(ghold[0], axis=-1) >= 0.0)[:CC_EVAL]
    enf = ctrl & hold_ok
    out["unctrl"] = int((~ctrl).sum())
    out["brought"] = int((ctrl & ~hold_ok).sum())
    viol = np.maximum(0.0, -slack) * enf[None]
    pen = W_PEN * np.sum(viol ** 2, axis=(1, 2))
    feas = pen == 0.0
    if feas.any():
        out["choice"] = int(np.argmax(np.where(feas, prog, -np.inf)))
    else:
        out["choice"] = N_C - 1          # no plan satisfies the enforced constraints: the emergency stop (fail-safe)
        out["infeasible"] = True
    out["pen"] = float(pen[out["choice"]])
    if counts is not None:
        enf8 = np.zeros((N_STEP, len(sel)), bool)
        enf8[:CC_STEPS] = enf[1::2]
        _record(sc, k, sel, out["choice"], gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf8, ob)
    return out


def run_decisions(sc, arm, fits):
    """Decision mode: at every keyframe 1 <= k <= K - 2 the planner decides once from the logged ego's own position and
    speed (leash = the log; sensor offset 0). Returns (summary, in-loop counts)."""
    out = {"arm": arm, "mode": "decide", "keyframes": sc.K, "entered": sc.K >= 3}
    counts = {}
    if arm == "LOG" or sc.K < 3:
        out.update({"frames": 0, "infeasible_frames": 0})
        return out, counts
    vmax = sc.v_log_max + 2.0
    frames = infeasible = unctrl = brought = 0
    acc = []
    for k in range(1, sc.K - 1):
        tk = float(sc.kf_t[k])
        ps = plan_step(sc, arm, fits, k, float(sc.s_log(tk)), max(sc.v_log(tk), 0.0), vmax, sc.s_log, counts, 0)
        frames += 1
        infeasible += int(ps["infeasible"])
        unctrl += ps["unctrl"]
        brought += ps["brought"]
        acc.append(float(ACC_TABLE[ps["choice"], 0]))
    out.update({"frames": frames, "infeasible_frames": infeasible, "uncontrollable_pairs": unctrl, "brought_to_ego_pairs": brought,
                "mean_first_accel": float(np.mean(acc)) if acc else None})
    return out, counts


'''
i = s.index("def run_episode(")
s = s[:i] + PLAN_STEP + s[i:]

# remove the now unused locals in run_episode (prev_state, ego_v, ego_w were only used by the old block)
old_prev = '''        ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
        if prev_state is None:
            ego_v, ego_w = v, 0.0
        else:
            dt = tk - prev_state[3]
            ego_v = ((ex - prev_state[0]) * math.cos(eyaw) + (ey - prev_state[1]) * math.sin(eyaw)) / dt
            ego_w = wrap(eyaw - prev_state[2]) / dt
        prev_state = (ex, ey, eyaw, tk)
'''
assert s.count(old_prev) == 1
s = s.replace(old_prev, "", 1)
s = s.replace("    prev_state = None                   # (rear x, y, yaw, t) at the previous keyframe\n", "", 1)

# records only at the enforced calibrated steps
old_r = '''    for h in range(N_STEP):
        kk = k + h + 1
        if kk >= sc.K:
            break
        gat = sc.gt_at[kk]'''
new_r = '''    for h in range(CC_STEPS):
        kk = k + h + 1
        if kk >= sc.K:
            break
        gat = sc.gt_at[kk]'''
assert s.count(old_r) == 1
s = s.replace(old_r, new_r, 1)
open(p, "w", encoding="utf-8", newline="\n").write(s)
print("step 2 applied")
