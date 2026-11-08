#!/usr/bin/env python3
"""Generator: k6_sim_v02.py from k6_sim_v01.py (Claude line, 1 Nov 2026; review R09 C1, C2, M1, M2, m7). Re-running it
reproduces k6_sim_v02.py byte for byte."""
import os

K = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(K, "k6_sim_v01.py"), encoding="utf-8").read()
rep = [
    ('"""K6 log-replay closed-loop harness (Claude line, v01, 31 Oct 2026). Design: 90_DECISIONS/D09_K6_HARNESS_DESIGN_v01.md.',
     '"""K6 log-replay closed-loop harness (Claude line, v02, 1 Nov 2026). Design: 90_DECISIONS/D09_K6_HARNESS_DESIGN_v04.md.\n'
     'v02 (pre-freeze review R09):\n'
     '  * C1: which constraints are exempt is decided at an arm-independent reference margin of 0 (the buffered mean\n'
     '    footprints): a (track, check time) pair is exempt if no candidate keeps the buffered mean footprints apart, or if an\n'
     '    ego held at its current position would not; every other pair is enforced at the arm\'s margin, and when no candidate\n'
     '    satisfies them all the planner takes the emergency stop. The exempt set is the same for every arm; only the margins\n'
     '    differ, so a larger margin can only make the planner stop more, never ignore more.\n'
     '  * C2: the range stratum is computed from the sensor, i.e. the logged ego\'s CTRV prediction from its keyframe poses at\n'
     '    k-1 and k (as in calibration), not from the simulated ego.\n'
     '  * M1, M2, m7: each in-loop record also carries the method\'s in-path flag, whether the pair was enforced, whether the\n'
     '    plan satisfied its relied-on axis at the margin, and the sensor-offset bin (logged ego ahead of the simulated ego by\n'
     '    at most 5, 5 to 15, or more than 15 m); annotations inside a bicycle rack at k + h are censored, as in the method.\n'
     'v01:'),
    ('GAP_BINS = (2.0, 5.0)                                       # pair-gap bins for the in-loop counts: <=2, (2,5], >5 m',
     'GAP_BINS = (2.0, 5.0)                                       # pair-gap bins for the in-loop counts: <=2, (2,5], >5 m\n'
     'OFFSET_BINS = (5.0, 15.0)                                   # sensor-offset bins: logged ego ahead by <=5, (5,15], >15 m'),
    ('N_CELL = (len(GAP_BINS) + 1) * 2 * N_STEP * N_L0',
     'N_CELL = (len(OFFSET_BINS) + 1) * 2 * 2 * 2 * (len(GAP_BINS) + 1) * 2 * N_STEP * N_L0'),
    ('def strata(sc, rows, k, ego_rear, ego_v, ego_w):\n'
     '    """Group, range bin (per step), motion state and sd (per step and axis) of the tracks in rows at keyframe k.\n'
     '    Range uses the ego centre predicted by CTRV from the simulated ego\'s state, as the method does."""',
     'def sensor_ctrv(sc, k):\n'
     '    """Rear-axle pose and CTRV speed and yaw rate of the logged ego (the sensor) at keyframe k, from its keyframe poses\n'
     '    at k-1 and k as in x1_lib_v03.build_horizon_rows; at k = 0 the logged speed and a zero yaw rate."""\n'
     '    ex, ey, eyaw = (float(q) for q in sc.kf_ego[k])\n'
     '    if k == 0:\n'
     '        return (ex, ey, eyaw), sc.v_log(float(sc.kf_t[0])), 0.0\n'
     '    px, py, pyaw = (float(q) for q in sc.kf_ego[k - 1])\n'
     '    dt = float(sc.kf_t[k] - sc.kf_t[k - 1])\n'
     '    v = ((ex - px) * math.cos(eyaw) + (ey - py) * math.sin(eyaw)) / dt\n'
     '    return (ex, ey, eyaw), v, wrap(eyaw - pyaw) / dt\n'
     '\n'
     '\n'
     'def strata(sc, rows, k, ego_rear, ego_v, ego_w):\n'
     '    """Group, range bin (per step), motion state and sd (per step and axis) of the tracks in rows at keyframe k.\n'
     '    Range uses the ego centre predicted by CTRV; v02 passes the sensor\'s (logged ego\'s) state, as the method does."""'),
    ('            g, r, m, sd, l0, ax = strata(sc, sel, k, (ex, ey, eyaw), ego_v, ego_w)',
     '            sens_pose, sens_v, sens_w = sensor_ctrv(sc, k)\n'
     '            g, r, m, sd, l0, ax = strata(sc, sel, k, sens_pose, sens_v, sens_w)'),
    ('            # enforced constraints (D09 v02 C6): the (track, check time) pairs that (i) some candidate satisfies (the\n'
     '            # speed planner can act on them) and (ii) an ego held at its current position would satisfy (a conflict the\n'
     '            # other agent brings to the ego is not the ego\'s to resolve, as in the fault rule); the others are counted\n'
     '            ctrl = (slack >= 0.0).any(axis=0)                              # (16, J)\n'
     '            ghold, _ = gaps(sc, np.full((1, N_EVAL), s), xy16, ax, half)\n'
     '            hold_ok = np.max(ghold[0] - mg16.transpose(1, 0, 2), axis=-1) >= 0.0\n',
     '            # exemptions at the arm-independent reference margin 0 (R09 C1): a (track, check time) pair is exempt if no\n'
     '            # candidate keeps the buffered mean footprints apart (no speed choice can act on it) or if an ego held at its\n'
     '            # current position would not (the conflict is brought to the ego); every other pair is enforced at the arm\'s\n'
     '            # margin. The exempt set is therefore the same for every arm.\n'
     '            ctrl = (np.max(gap, axis=-1) >= 0.0).any(axis=0)               # (16, J)\n'
     '            ghold, _ = gaps(sc, np.full((1, N_EVAL), s), xy16, ax, half)\n'
     '            hold_ok = np.max(ghold[0], axis=-1) >= 0.0\n'),
    ('            if record:\n'
     '                _record(sc, k, sel, choice, gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts)',
     '            if record:\n'
     '                off = float(sc.s_log(tk)) - s\n'
     '                ob = 0 if off <= OFFSET_BINS[0] else (1 if off <= OFFSET_BINS[1] else 2)\n'
     '                _record(sc, k, sel, choice, gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf[1::2], ob)'),
    ('        frames += 1\n        a_first = float(ACC_TABLE[choice, 0])',
     '        frames += 1\n        offs.append(float(sc.s_log(tk)) - s)\n        a_first = float(ACC_TABLE[choice, 0])'),
    ('    unctrl = unctrl_frames = brought = 0', '    unctrl = unctrl_frames = brought = 0\n    offs = []'),
    ('                "uncontrollable_pairs": unctrl, "uncontrollable_frames": unctrl_frames, "brought_to_ego_pairs": brought,',
     '                "uncontrollable_pairs": unctrl, "uncontrollable_frames": unctrl_frames, "brought_to_ego_pairs": brought,\n'
     '                "sensor_offset_median": float(np.median(offs)) if offs else None,\n'
     '                "sensor_offset_share_gt15": float(np.mean(np.array(offs) > OFFSET_BINS[1])) if offs else None,'),
]
for a, b in rep:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b, 1)
i = s.index("def _record(")
j = s.index("def decode_cell(")
RECORD = '''def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob):
    """In-loop constraint records of the executed plan: paired tracks with a ground-truth annotation (>= 1 point, not in a
    bicycle rack) at k + h; for each separating axis, D = sign(sep) a.(g - m) and the exceedance D > margin. Counted per
    (sensor-offset bin, in-path, enforced, satisfied, pair-gap bin, relied-on axis, step, L0 stratum). Satisfied: the
    executed plan kept the relied-on axis's gap at or above its margin."""
    inst = sc.tr["inst"][sel]
    inpath = sc.tr["inpath"][sel] if "inpath" in sc.tr else np.zeros(len(sel), bool)
    G = gap[choice]                        # (8, J, 2)
    S = sep[choice]
    slack_ax = G - mg.transpose(1, 0, 2)   # (8, J, 2)
    relied = np.argmax(slack_ax, axis=-1)  # (8, J)
    sat = np.take_along_axis(slack_ax, relied[..., None], -1)[..., 0] >= 0.0   # (8, J)
    pair_gap = np.max(G, axis=-1)          # (8, J)
    hh, jj, rr = [], [], []
    paired = np.nonzero(inst >= 0)[0]
    inrack = sc.gt["inrack"] if "inrack" in sc.gt else np.zeros(len(sc.gt["k"]), bool)
    for h in range(N_STEP):
        kk = k + h + 1
        if kk >= sc.K:
            break
        gat = sc.gt_at[kk]
        for j in paired:
            row = gat.get(int(inst[j]))
            if row is not None and not inrack[row]:
                hh.append(h)
                jj.append(j)
                rr.append(row)
    if not hh:
        return
    hh, jj, rr = np.array(hh), np.array(jj), np.array(rr)
    e = np.stack([sc.gt["x"][rr] - pred_xy[jj, hh, 0], sc.gt["y"][rr] - pred_xy[jj, hh, 1]], -1)   # (n, 2)
    pg = pair_gap[hh, jj]
    gb = np.where(pg <= GAP_BINS[0], 0, np.where(pg <= GAP_BINS[1], 1, 2))
    head = ((ob * 2 + inpath[jj].astype(int)) * 2 + enf[hh, jj].astype(int)) * 2 + sat[hh, jj].astype(int)
    for a_ in range(2):
        ok = G[hh, jj, a_] > 0
        if not ok.any():
            continue
        h_, j_, e_, gb_, hd_ = hh[ok], jj[ok], e[ok], gb[ok], head[ok]
        # sep = a.(c_ego - m): positive when the ego lies on the +a side; an error toward the ego has the sign of sep
        D = np.sign(S[h_, j_, a_]) * np.sum(ax[j_, a_] * e_, -1)
        exc = D > mg[j_, h_, a_]
        cell = (((hd_ * 3 + gb_) * 2 + (relied[h_, j_] == a_)) * N_STEP + h_) * N_L0 + l0[j_, h_, a_]
        for c_, x_ in zip(cell.tolist(), exc.tolist()):
            c = counts.setdefault(c_, [0, 0])
            c[0] += 1
            c[1] += int(x_)


def decode_cell(cell):
    """(sensor-offset bin, in-path, enforced, satisfied, pair-gap bin, relied-on, step, L0)."""
    rest, l0 = divmod(int(cell), N_L0)
    rest, h = divmod(rest, N_STEP)
    rest, rel = divmod(rest, 2)
    rest, gb = divmod(rest, 3)
    rest, sat = divmod(rest, 2)
    rest, enf = divmod(rest, 2)
    ob, inp = divmod(rest, 2)
    return ob, inp, enf, sat, gb, rel, h, l0
'''
s = s[:i] + RECORD
open(os.path.join(K, "k6_sim_v02.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k6_sim_v02.py written")
