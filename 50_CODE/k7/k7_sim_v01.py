#!/usr/bin/env python3
"""K7 harness (Claude line, k7_sim_v01, 1 Nov 2026) = k6_sim_v02 with one change, written by tests/make_k7_sim_v01.py:
  an arm whose fit dictionary has the key '<arm>_ip' (192 thresholds, index L0 + 96 x in-path) takes its threshold
  from the track's L0 stratum and the method's in-path flag (planner-matched calibration, K7); otherwise unchanged.
K6 log-replay closed-loop harness (Claude line, v02, 1 Nov 2026). Design: 90_DECISIONS/D09_K6_HARNESS_DESIGN_v04.md.
v02 (pre-freeze review R09):
  * C1: which constraints are exempt is decided at an arm-independent reference margin of 0 (the buffered mean
    footprints): a (track, check time) pair is exempt if no candidate keeps the buffered mean footprints apart, or if an
    ego held at its current position would not; every other pair is enforced at the arm's margin, and when no candidate
    satisfies them all the planner takes the emergency stop. The exempt set is the same for every arm; only the margins
    differ, so a larger margin can only make the planner stop more, never ignore more.
  * C2: the range stratum is computed from the sensor, i.e. the logged ego's CTRV prediction from its keyframe poses at
    k-1 and k (as in calibration), not from the simulated ego.
  * M1, M2, m7: each in-loop record also carries the method's in-path flag, whether the pair was enforced, whether the
    plan satisfied its relied-on axis at the margin, and the sensor-offset bin (logged ego ahead of the simulated ego by
    at most 5, 5 to 15, or more than 15 m); annotations inside a bicycle rack at k + h are censored, as in the method.
  * Development iteration (D09 v04): the chance constraints are enforced at the check times up to 2 s (CC_EVAL), the
    method's decision horizon; with them enforced to 4 s every margin arm was infeasible in 51-81 % of development frames.
    The plan is still scored over 4 s. In-loop records are taken at the enforced calibrated steps (0.5 to 2 s).
  * Two modes share plan_step: run_episode (closed loop, as before) and run_decisions (at every keyframe k >= 1 the
    planner decides from the logged ego's own position and speed, leash = the log, sensor offset 0; one decision per
    keyframe, no dynamics). The decision mode scores the constraints each arm's planner relies on with exact replayed
    perception; the closed loop gives the operational outcomes.
  * R09b MJ1: when no candidate satisfies the enforced constraints at the arm's margin (an infeasible decision), the
    margin is backed off on the same enforced set, lambda in BACKOFF, and the max-progress candidate at the largest
    feasible lambda is taken; the emergency stop only if even lambda = 0 (the buffered mean footprints) is infeasible.
    An immediate emergency stop could brake the ego into a crossing agent's path where a smaller margin kept going.
    A closed-loop collision within FALLBACK_WINDOW of an infeasible decision is flagged fallback_related.
v01:

One episode = one scene x one delay x one margin arm. The world is the nuScenes log: annotated agents follow their
keyframe annotations (linear interpolation, shortest-arc yaw) and do not react. The planner sees the recorded output of
the real stack at each keyframe (cache from k6_cache_v01): track means and xy covariances at the 8 planner steps from each
class's own filter. The ego moves along its logged path (20 Hz poses) at a speed the planner chooses:
  * candidates: a1 in A1 held for T1 seconds, then braking at A_BRAKE to a stop; plus an emergency stop;
  * leash: s(t) <= s_log(t - delay); planned positions are capped at it;
  * constraints: for each track, step and object axis, gap = |a.(c_ego - m)| - (object half extent + ego projected half
    extent + BUFFER); a pair is safe if some axis has gap >= margin; margins come from the arm (method-stage functions);
  * constraints are checked every 0.25 s: at the 8 calibrated steps, and at the midpoints with interpolated means and the
    margin of the next step;
  * enforced constraints: the (track, check time) pairs that some candidate satisfies (the speed planner can act on
    them) and that an ego held at its current position would satisfy (a conflict the other agent brings to the ego is
    not the ego's to resolve, as in the fault rule); the others are counted, not enforced;
  * choice: the candidate satisfying every enforced constraint with the largest mean planned position over the 16 check
    times (ties: candidate order); if none does, the emergency stop (the minimum-risk manoeuvre).
Outcomes per episode: progress, lag, blocked stop time, infeasible frames, hard braking, collisions (exact rectangle
overlap at every substep; at fault when the ego moves and the agent overlaps the ego's front half), front buffer
intrusions, and the in-loop constraint records of the executed plans (aggregated counts per cell).
Pure numpy; no simulator, no tracker in the loop. Deterministic.
"""
import hashlib
import json
import math

import numpy as np

EGO_L, EGO_W, BUFFER, R2C = 4.1, 1.8, 0.5, 1.39          # x1_lib_v03 constants
Z = 1.6448536269514722                                      # z_0.95
SIGMA_A = 0.10
N_STEP, DT_STEP = 8, 0.5
SUB = 5                                                     # substeps per keyframe interval
DT_FINE = 0.05                                              # candidate integration step
A1 = (-4.0, -2.0, -1.0, 0.0, 0.5, 1.0, 1.5, 2.0)
T1 = (0.5, 1.0, 2.0, 4.0)
A_BRAKE, A_ESTOP = -4.0, -6.0
W_PEN = 1000.0                                              # scales the recorded violation only (diagnostic)
R_CONSIDER = 60.0
V_STATIC, W_TURN = 1.0, 0.10
V_MOVING = 0.1
SCORE_MIN = 0.4                                             # deployed tracker output: tracks with score >= 0.4 (D09 v02 section 2)
HARD_BRAKE = -4.0
GAP_BRIDGE = 3                                              # bridge annotation gaps of up to 3 keyframes
DS_KEEP = 0.05                                              # path decimation: keep poses at least 5 cm apart
GAP_BINS = (2.0, 5.0)                                       # pair-gap bins for the in-loop counts: <=2, (2,5], >5 m
OFFSET_BINS = (5.0, 15.0)                                   # sensor-offset bins: logged ego ahead by <=5, (5,15], >15 m
GROUP_OF_CLS = np.array([0, 3, 3, 3, 1, 2, 2])              # car truck bus trailer pedestrian motorcycle bicycle
ARMS = ("LOG", "Z0", "B0", "B1", "B3", "B4", "B9", "B6", "Mstar")   # LOG: the delayed logged profile, no planner (reference)
N_L0 = 96
N_CELL = (len(OFFSET_BINS) + 1) * 2 * 2 * 2 * (len(GAP_BINS) + 1) * 2 * N_STEP * N_L0


def candidates():
    """Candidate list in preference order for ties: smaller |a1| first, then positive before negative, then longer T1;
    the emergency stop last."""
    c = sorted(((a, t) for a in A1 for t in T1), key=lambda x: (abs(x[0]), -x[0], -x[1]))
    return c + [(A_ESTOP, 4.0)]


CANDS = candidates()
N_C = len(CANDS)
_TAU = (np.arange(int(round(4.0 / DT_FINE))) + 0.5) * DT_FINE
ACC_TABLE = np.array([[a if (tau < t or a == A_ESTOP) else A_BRAKE for tau in _TAU] for a, t in CANDS])  # (N_C, 80)
N_EVAL = 2 * N_STEP                                                                                  # checks every 0.25 s
EVAL_IDX = [int(round(0.5 * DT_STEP * i / DT_FINE)) for i in range(1, N_EVAL + 1)]                    # 5, 10, ..., 80
EVAL_T = 0.5 * DT_STEP * np.arange(1, N_EVAL + 1)
MARGIN_OF_EVAL = np.array([(i + 1) // 2 - 1 for i in range(1, N_EVAL + 1)])                          # next calibrated step
CC_EVAL = 8                                                                                          # constraints enforced to 2 s
CC_STEPS = CC_EVAL // 2                                                                              # calibrated steps recorded
BACKOFF = (0.75, 0.5, 0.25, 0.0)                                                                     # margin back-off (R09b MJ1)
FALLBACK_WINDOW = 2.0                                                                                # s: collisions this soon after an infeasible decision


# ---------------------------------------------------------------- geometry

def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def rect_overlap(c, yaw, L, W, oc, oyaw, oL, oW):
    """Separating-axis test of one rectangle (centre c, yaw, length L, width W) against n rectangles. True = overlap
    (touching is not overlap)."""
    ue = np.array([math.cos(yaw), math.sin(yaw)])
    ve = np.array([-math.sin(yaw), math.cos(yaw)])
    uo = np.stack([np.cos(oyaw), np.sin(oyaw)], -1)
    vo = np.stack([-np.sin(oyaw), np.cos(oyaw)], -1)
    d = oc - c
    ok = np.ones(len(oc), bool)
    for ax in (np.broadcast_to(ue, uo.shape), np.broadcast_to(ve, uo.shape), uo, vo):
        dist = np.abs(np.sum(ax * d, -1))
        re = 0.5 * L * np.abs(ax @ ue) + 0.5 * W * np.abs(ax @ ve)
        ro = 0.5 * oL * np.abs(np.sum(ax * uo, -1)) + 0.5 * oW * np.abs(np.sum(ax * vo, -1))
        ok &= dist < re + ro
    return ok


# ---------------------------------------------------------------- scene

class Scene:
    def __init__(self, npz):
        z = np.load(npz)
        self.kf_t = z["kf_t"]
        self.K = len(self.kf_t)
        self.kf_ego = z["kf_ego"]
        self.tr = {k[3:]: z[k] for k in z.files if k.startswith("tr_")}
        self.gt = {k[3:]: z[k] for k in z.files if k.startswith("gt_")}
        self._path(z["ego_t"], z["ego_x"], z["ego_y"], z["ego_yaw"])
        self.tr_by_k = [np.nonzero(self.tr["k"] == k)[0] for k in range(self.K)] if len(self.tr.get("k", [])) else [np.zeros(0, int)] * self.K
        self._gt_index()
        self._paired_by_k()

    def _path(self, t, x, y, yaw):
        keep = [0]
        for i in range(1, len(t)):
            if math.hypot(x[i] - x[keep[-1]], y[i] - y[keep[-1]]) >= DS_KEEP:
                keep.append(i)
        keep = np.array(keep)
        px, py = x[keep], y[keep]
        s = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(px), np.diff(py)))])
        self.ps, self.px, self.py, self.pyaw = s, px, py, np.unwrap(yaw[keep])
        self.pt = t[keep]
        self.t0, self.t_end = float(t[0]), float(t[-1])
        self.s_end = float(s[-1])
        # logged speed: arc length over a 0.5 s window (for v_max and the initial speed)
        tt = np.arange(self.t0, self.t_end + 1e-9, 0.1)
        sl = self.s_log(tt)
        win = 5
        v = (sl[win:] - sl[:-win]) / (tt[win:] - tt[:-win]) if len(tt) > win else np.zeros(1)
        self.v_log_max = float(np.max(v)) if len(v) else 0.0
        self._v_tt, self._v_val = (0.5 * (tt[win:] + tt[:-win]), v) if len(tt) > win else (np.array([self.t0]), np.zeros(1))

    def s_log(self, t):
        return np.interp(t, self.pt, self.ps, left=0.0, right=self.s_end)

    def v_log(self, t):
        return float(np.interp(t, self._v_tt, self._v_val))

    def pose(self, s):
        """Rear-axle pose (x, y, yaw) on the logged path at arc length s (vectorised)."""
        s = np.clip(s, 0.0, self.s_end)
        return np.interp(s, self.ps, self.px), np.interp(s, self.ps, self.py), np.interp(s, self.ps, self.pyaw)

    def _gt_index(self):
        g = self.gt
        self.segments = []   # (k_a, k_b, rows a, rows b) per interval list
        self.gt_by_k = [np.nonzero(g["k"] == k)[0] for k in range(self.K)] if len(g["k"]) else [np.zeros(0, int)] * self.K
        by_inst = {}
        for i in np.argsort(g["k"], kind="stable") if len(g["k"]) else []:
            by_inst.setdefault(int(g["inst"][i]), []).append(int(i))
        pairs = [[] for _ in range(max(self.K - 1, 0))]
        for inst, rows in by_inst.items():
            for ra, rb in zip(rows, rows[1:]):
                ka, kb = int(g["k"][ra]), int(g["k"][rb])
                if 0 < kb - ka <= GAP_BRIDGE:
                    for k in range(ka, kb):
                        pairs[k].append((ra, rb))
        self.interval_rows = [(np.array([p[0] for p in pr], int), np.array([p[1] for p in pr], int)) for pr in pairs]
        self.gt_inst_rows = by_inst

    def agents_at(self, k, t):
        """Annotated agents present inside keyframe interval [k, k+1] at time t: centres, yaw, length, width, instance."""
        ra, rb = self.interval_rows[k]
        if not len(ra):
            return np.zeros((0, 2)), np.zeros(0), np.zeros(0), np.zeros(0), np.zeros(0, int)
        g = self.gt
        ta, tb = self.kf_t[g["k"][ra]], self.kf_t[g["k"][rb]]
        f = np.clip((t - ta) / (tb - ta), 0.0, 1.0)
        x = g["x"][ra] + f * (g["x"][rb] - g["x"][ra])
        y = g["y"][ra] + f * (g["y"][rb] - g["y"][ra])
        dyaw = (g["yaw"][rb] - g["yaw"][ra] + np.pi) % (2 * np.pi) - np.pi
        yaw = g["yaw"][ra] + f * dyaw
        return np.stack([x, y], -1), yaw, g["l"][ra], g["w"][ra], g["inst"][ra]

    def _paired_by_k(self):
        self.paired_inst_k = [set(self.tr["inst"][self.tr_by_k[k]].tolist()) - {-1} for k in range(self.K)] if len(self.tr.get("k", [])) else [set()] * self.K
        g = self.gt
        self.gt_at = [{int(g["inst"][i]): int(i) for i in self.gt_by_k[k] if g["pts"][i] >= 1} for k in range(self.K)]


# ---------------------------------------------------------------- margins

def sensor_ctrv(sc, k):
    """Rear-axle pose and CTRV speed and yaw rate of the logged ego (the sensor) at keyframe k, from its keyframe poses
    at k-1 and k as in x1_lib_v03.build_horizon_rows; at k = 0 the logged speed and a zero yaw rate."""
    ex, ey, eyaw = (float(q) for q in sc.kf_ego[k])
    if k == 0:
        return (ex, ey, eyaw), sc.v_log(float(sc.kf_t[0])), 0.0
    px, py, pyaw = (float(q) for q in sc.kf_ego[k - 1])
    dt = float(sc.kf_t[k] - sc.kf_t[k - 1])
    v = ((ex - px) * math.cos(eyaw) + (ey - py) * math.sin(eyaw)) / dt
    return (ex, ey, eyaw), v, wrap(eyaw - pyaw) / dt


def strata(sc, rows, k, ego_rear, ego_v, ego_w):
    """Group, range bin (per step), motion state and sd (per step and axis) of the tracks in rows at keyframe k.
    Range uses the ego centre predicted by CTRV; v02 passes the sensor's (logged ego's) state, as the method does."""
    tr = sc.tr
    g = GROUP_OF_CLS[tr["cls"][rows]]
    spd, om = tr["spd"][rows], tr["omc"][rows]
    m = np.where(spd < V_STATIC, 0, np.where(~np.isfinite(om), 3, np.where(np.abs(np.nan_to_num(om)) >= W_TURN, 2, 1)))
    ex, ey, eyaw = ego_rear
    th = DT_STEP * np.arange(1, N_STEP + 1)
    if abs(ego_w) < 1e-4:
        px, py, pyaw = ex + ego_v * th * math.cos(eyaw), ey + ego_v * th * math.sin(eyaw), np.full(N_STEP, eyaw)
    else:
        pyaw = eyaw + ego_w * th
        px = ex + ego_v / ego_w * (np.sin(pyaw) - math.sin(eyaw))
        py = ey - ego_v / ego_w * (np.cos(pyaw) - math.cos(eyaw))
    cx, cy = px + R2C * np.cos(pyaw), py + R2C * np.sin(pyaw)
    pred = tr["pred"][rows]                              # (J, 8, 5)
    dist = np.hypot(pred[:, :, 0] - cx[None], pred[:, :, 1] - cy[None])
    r = np.where(dist < 20, 0, np.where(dist < 40, 1, 2))
    yaw = tr["yaw"][rows]
    ax = np.stack([np.stack([np.cos(yaw), np.sin(yaw)], -1), np.stack([-np.sin(yaw), np.cos(yaw)], -1)], 1)  # (J, 2, 2)
    sxx, sxy, syy = pred[:, :, 2], pred[:, :, 3], pred[:, :, 4]
    var = (ax[:, None, :, 0] ** 2 * sxx[:, :, None] + 2 * ax[:, None, :, 0] * ax[:, None, :, 1] * sxy[:, :, None]
           + ax[:, None, :, 1] ** 2 * syy[:, :, None])                                                        # (J, 8, 2)
    sd = np.sqrt(np.maximum(var + SIGMA_A ** 2, 1e-6))
    l0 = ((g[:, None, None] * 3 + r[:, :, None]) * 2 + np.arange(2)[None, None, :]) * 4 + m[:, None, None]    # (J, 8, 2)
    return g, r, m, sd, l0, ax


def margins(arm, fits, g, r, sd, l0, inp=None):
    """Margin (m) along each object axis for every track, step and axis. fits: list over the 8 steps of the method-stage
    fit dictionaries (thresholds as plain lists)."""
    if arm == "Z0":
        return np.zeros_like(sd)
    if arm == "B0":
        return Z * sd
    out = np.empty_like(sd)
    for h in range(N_STEP):
        f = fits[h]
        s, L0 = sd[:, h, :], l0[:, h, :]
        if arm == "B1":
            k = np.asarray(f["B1"])[(g[:, None] * 3 + r[:, h][:, None])]
            out[:, h, :] = Z * np.sqrt(k) * s
        elif arm == "B3":
            out[:, h, :] = f["B3"] * s
        elif arm == "B4":
            out[:, h, :] = f["B4"] * s
        elif arm == "B9":
            out[:, h, :] = f["B9"]
        elif arm in ("B6", "Mstar") and (arm + "_ip") in f:
            out[:, h, :] = np.asarray(f[arm + "_ip"])[L0 + N_L0 * np.asarray(inp, int)[:, None]] * s
        elif arm == "B6":
            out[:, h, :] = np.asarray(f["B6"])[L0] * s
        elif arm == "Mstar":
            out[:, h, :] = np.asarray(f["Mstar"])[L0] * s
        else:
            raise ValueError(arm)
    return out


# ---------------------------------------------------------------- planner

def plan_positions(s0, v0, vmax):
    """Planned arc length of every candidate at the 16 check times, every 0.25 s (before the leash)."""
    s = np.full(N_C, float(s0))
    v = np.full(N_C, float(v0))
    out = np.empty((N_C, N_EVAL))
    j = 0
    for i in range(ACC_TABLE.shape[1]):
        vn = np.clip(v + ACC_TABLE[:, i] * DT_FINE, 0.0, vmax)
        s = s + 0.5 * (v + vn) * DT_FINE
        v = vn
        if j < N_EVAL and i + 1 == EVAL_IDX[j]:
            out[:, j] = s
            j += 1
    return out


def gaps(sc, splan, pred_xy, ax, half):
    """gap[c, h, j, a] = |a.(c_ego - m)| - (object half extent + ego projected half extent + BUFFER), and the signed sep."""
    ex, ey, eyaw = sc.pose(splan)                                     # (N_C, 16)
    cx, cy = ex + R2C * np.cos(eyaw), ey + R2C * np.sin(eyaw)
    ue = np.stack([np.cos(eyaw), np.sin(eyaw)], -1)                   # (N_C, 8, 2)
    ve = np.stack([-np.sin(eyaw), np.cos(eyaw)], -1)
    d = np.stack([cx, cy], -1)[:, :, None, :] - pred_xy[None, :, :, :].transpose(0, 2, 1, 3)  # (N_C, 8, J, 2)
    sep = np.einsum("chjx,jax->chja", d, ax)                          # (N_C, 8, J, 2)
    he = (EGO_L / 2 + BUFFER) * np.abs(np.einsum("chx,jax->chja", ue, ax)) + (EGO_W / 2 + BUFFER) * np.abs(np.einsum("chx,jax->chja", ve, ax))
    return np.abs(sep) - (half[None, None] + he), sep


def plan_step(sc, arm, fits, k, s, v, vmax, lead, counts, ob):
    """One planning cycle at keyframe k from arc length s and speed v. counts: dict to receive the in-loop records of the
    chosen plan (None: no records); ob: the sensor-offset bin of those records. Returns the chosen candidate, whether no
    candidate satisfied the enforced constraints (then the emergency stop), and the exemption counters."""
    tk = float(sc.kf_t[k])
    ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
    rows = sc.tr_by_k[k]
    splan = np.minimum(plan_positions(s, v, vmax), lead(tk + EVAL_T)[None, :])
    prog = splan.mean(axis=1)
    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0, "lam": 1.0}
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
    assert "inpath" in sc.tr, "cache without the method's in-path flag"   # R12 m5: no silent default
    inp_sel = sc.tr["inpath"][sel]
    mg = margins(arm, fits, g, r, sd, l0, inp_sel)                # (J, 8, 2)
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
        out["infeasible"] = True          # infeasible at the arm's margin (the HK3 indicator)
        out["choice"], out["lam"] = N_C - 1, None
        for lam in BACKOFF:               # back the margin off on the same enforced set (R09b MJ1)
            sl = np.max(gap - lam * mg16.transpose(1, 0, 2)[None], axis=-1)[:, :CC_EVAL]
            fl = (np.maximum(0.0, -sl) * enf[None]).sum(axis=(1, 2)) == 0.0
            if fl.any():
                out["choice"], out["lam"] = int(np.argmax(np.where(fl, prog, -np.inf))), lam
                break                     # else: the emergency stop (fail-safe)
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
    frames = infeasible = unctrl = brought = estops = 0
    acc = []
    for k in range(1, sc.K - 1):
        tk = float(sc.kf_t[k])
        ps = plan_step(sc, arm, fits, k, float(sc.s_log(tk)), max(sc.v_log(tk), 0.0), vmax, sc.s_log, counts, 0)
        frames += 1
        infeasible += int(ps["infeasible"])
        estops += int(ps["infeasible"] and ps["lam"] is None)
        unctrl += ps["unctrl"]
        brought += ps["brought"]
        acc.append(float(ACC_TABLE[ps["choice"], 0]))
    out.update({"frames": frames, "infeasible_frames": infeasible, "emergency_stop_frames": estops, "uncontrollable_pairs": unctrl,
                "brought_to_ego_pairs": brought,
                "mean_first_accel": float(np.mean(acc)) if acc else None})
    return out, counts


def run_episode(sc, arm, fits, delay_kf, record=True, debug=None):
    """Run one episode. delay_kf: the ego enters at keyframe delay_kf (0, 2 or 4 for 0, 1 or 2 s). fits: 8 per-step fit dicts
    (ignored for Z0 and B0). Returns (summary dict, in-loop counts as {flat cell: [n, exceed]})."""
    K = sc.K
    out = {"arm": arm, "delay_kf": delay_kf, "keyframes": K}
    if K < delay_kf + 2:
        out.update({"entered": False, "reason": "too_short"})
        return out, {}
    t_entry = float(sc.kf_t[delay_kf])
    shift = t_entry - float(sc.kf_t[0])
    lead = lambda t: sc.s_log(np.asarray(t) - shift)  # noqa: E731
    vmax = sc.v_log_max + 2.0
    s, v = 0.0, sc.v_log(sc.t0)
    x0, y0, yaw0 = sc.pose(np.array(s))
    c0 = np.array([float(x0) + R2C * math.cos(float(yaw0)), float(y0) + R2C * math.sin(float(yaw0))])
    oc, oyaw, oL, oW, oinst = sc.agents_at(delay_kf, t_entry) if delay_kf < K - 1 else sc.agents_at(K - 2, t_entry)
    if len(oc) and rect_overlap(c0, float(yaw0), EGO_L, EGO_W, oc, oyaw, oL, oW).any():
        out.update({"entered": False, "reason": "entry_conflict"})
        return out, {}
    out["entered"] = True
    counts = {}
    trace = hashlib.sha256()
    frames = infeasible = hard = 0
    lag_sum, blocked_t, n_subs, t_run = 0.0, 0.0, 0, 0.0
    unctrl = unctrl_frames = brought = estops = 0
    t_last_inf = -1e9
    offs = []
    collided, near = {}, set()
    acc_abs = 0.0
    for k in range(delay_kf, K - 1):
        tk = float(sc.kf_t[k])
        off = float(sc.s_log(tk)) - s
        ob = 0 if off <= OFFSET_BINS[0] else (1 if off <= OFFSET_BINS[1] else 2)
        ps = plan_step(sc, arm, fits, k, s, v, vmax, lead, counts if record else None, ob)
        choice, pen_chosen = ps["choice"], ps["pen"]
        infeasible += int(ps["infeasible"])
        estops += int(ps["infeasible"] and ps["lam"] is None)
        if ps["infeasible"]:
            t_last_inf = tk
        unctrl += ps["unctrl"]
        unctrl_frames += int(ps["unctrl"] > 0)
        brought += ps["brought"]
        frames += 1
        offs.append(float(sc.s_log(tk)) - s)
        a_first = float(ACC_TABLE[choice, 0])
        hard += int(a_first <= HARD_BRAKE)
        trace.update(json.dumps([k, round(s, 9), round(v, 9), choice, round(pen_chosen, 9)]).encode())
        if debug is not None:
            debug.append((k, s, v, float(lead(tk)), CANDS[choice], pen_chosen))
        # execute until the next keyframe
        t_next = float(sc.kf_t[k + 1])
        dt = (t_next - tk) / SUB
        for i in range(SUB):
            tau = (i + 0.5) * dt
            a = float(ACC_TABLE[choice, min(int(tau / DT_FINE), ACC_TABLE.shape[1] - 1)])
            vn = min(max(v + a * dt, 0.0), vmax)
            sn = s + 0.5 * (v + vn) * dt
            t = tk + (i + 1) * dt
            sl = float(lead(t))
            if arm == "LOG":
                sn, vn = max(s, sl), max(sc.v_log(t - shift), 0.0)
            elif sn > sl:
                sn = max(s, sl)
                vn = min(vn, max(sc.v_log(t - shift), 0.0))
            acc_abs += abs(vn - v)
            t_run += dt
            s, v = sn, vn
            lag_sum += sl - s
            n_subs += 1
            if v < V_MOVING and sl - s >= 5.0:
                blocked_t += dt
            # collisions
            oc, oyaw, oL, oW, oinst = sc.agents_at(k, t)
            if len(oc):
                xr, yr, yw = (float(q) for q in sc.pose(np.array(s)))
                ce = np.array([xr + R2C * math.cos(yw), yr + R2C * math.sin(yw)])
                close = np.hypot(oc[:, 0] - ce[0], oc[:, 1] - ce[1]) < 15.0
                if close.any():
                    idx = np.nonzero(close)[0]
                    hit = rect_overlap(ce, yw, EGO_L, EGO_W, oc[idx], oyaw[idx], oL[idx], oW[idx])
                    cf = ce + 0.25 * EGO_L * np.array([math.cos(yw), math.sin(yw)])
                    front = rect_overlap(cf, yw, EGO_L / 2, EGO_W, oc[idx], oyaw[idx], oL[idx], oW[idx])
                    cfb = ce + (0.25 * EGO_L + 0.25) * np.array([math.cos(yw), math.sin(yw)])
                    front_buf = rect_overlap(cfb, yw, EGO_L / 2 + 0.5, EGO_W + 2 * BUFFER, oc[idx], oyaw[idx], oL[idx], oW[idx])
                    for q, h_, f_, fb_ in zip(idx, hit, front, front_buf):
                        inst = int(oinst[q])
                        if h_ and inst not in collided:
                            tracked = inst in sc.paired_inst_k[k] or (k > 0 and inst in sc.paired_inst_k[k - 1])
                            collided[inst] = {"inst": inst, "t": round(t - sc.t0, 3), "k": k, "ego_v": round(v, 3),
                                              "at_fault": bool(v >= V_MOVING and f_), "front": bool(f_), "tracked": bool(tracked),
                                              "cls": int(sc.gt["cls"][sc.gt_inst_rows[inst][0]]),
                                              "fallback_related": bool(t - t_last_inf <= FALLBACK_WINDOW)}
                        if fb_ and v >= V_MOVING and inst not in near:
                            near.add(inst)
    s_lead_end = float(lead(float(sc.kf_t[K - 1])))
    out.update({"frames": frames, "infeasible_frames": infeasible, "hard_brake_frames": hard, "s_end": round(s, 4),
                "uncontrollable_pairs": unctrl, "uncontrollable_frames": unctrl_frames, "brought_to_ego_pairs": brought,
                "emergency_stop_frames": estops,
                "sensor_offset_median": float(np.median(offs)) if offs else None,
                "sensor_offset_share_gt15": float(np.mean(np.array(offs) > OFFSET_BINS[1])) if offs else None,
                "s_lead_end": round(s_lead_end, 4), "progress": (s / s_lead_end) if s_lead_end >= 10.0 else None,
                "lag_mean": lag_sum / max(n_subs, 1), "blocked_s": round(blocked_t, 3), "mean_abs_acc": acc_abs / max(t_run, 1e-9),
                "collisions": list(collided.values()), "n_collisions": len(collided),
                "n_at_fault": sum(c["at_fault"] for c in collided.values()),
                "n_at_fault_tracked": sum(c["at_fault"] and c["tracked"] for c in collided.values()),
                "n_front_buffer_intrusions": len(near), "trace_sha256": trace.hexdigest()})
    return out, counts


def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob):
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
    for h in range(CC_STEPS):
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
