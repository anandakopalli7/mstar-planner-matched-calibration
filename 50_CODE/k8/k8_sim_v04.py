#!/usr/bin/env python3
"""K8 harness (Claude line, k8_sim_v04, 2 Nov 2026) = k8_sim_v02 plus the joint arms of D16 Choice 2 (b), written by
tests/make_k8_joint_v04.py (asserted text replacements; K8_V04_DIFF_NOTE_v01.md). Two changes, no other:
  * JOINT_ARMS = ("MstarJ", "MstarJx") are appended to ARMS: each takes its thresholds from its own key '<arm>_ip' of the
    fits (192 per step, index L0 + 96 x in-path, written by k8_joint_fit_v01.py), else from '<arm>' (96, the steps after
    2 s), exactly as M* does with 'Mstar_ip' / 'Mstar'; their covariance for A6 is the generic D S' D of _arm_cov;
  * JOINT_RUN_STAMP, the stamp of the k8_run_v04 --exploratory --joint runs.
Every v02 arm decides exactly as in k8_sim_v02 (test_k8_joint_fit_v01.py).
K8 harness (Claude line, k8_sim_v02, 1 Nov 2026) = k8_sim_v01 with the R15 changes, written by tests/make_k8_sim_v02.py
(90_DECISIONS/D14_K8_DESIGN_v04.md section 5 item 1). No decision changes (test T1 of tests/test_k8_v02.py).
  * Two-sided grids (D14 v04 A2, A3): alpha in {1/32, 1/16, 1/8, 1/4, 1/3, 1/2, 1, 2, 3, 4, 5, 8} (B0a<alpha>: margin
    sqrt(alpha) z_0.95 sd; the annotation term sigma_a^2 is scaled with the covariance, so the effective floor is
    sqrt(alpha) 0.10 m), delta' in {0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001} (B0d<delta'>: margin z_{1-delta'} sd).
    Both are one curve: a delta' arm is the alpha arm at alpha_eq = (z_{1-delta'} / z_0.95)^2 (CURVE_ALPHA_OF_ARM).
  * Per decision, per near x in-path cell (ST_FIELDS): n, x, n_h0, x_h0 (v01), v = relied constraints violated at the plan
    (D > G along the relied-on axis), nb / xb = binding pairs (slack G - margin <= 0.5 m) and their exceedances, ne / xe =
    records and exceedances at the executed margin lam * margin (relied-on axis at that margin, separating, enforced, any
    satisfaction; lam = 0 for the emergency stop), nd / xd = de-duplicated (one record per step and ground-truth instance,
    the first track in order kept); TRK_FIELDS = tracks with a relied-on record by in-path x (far only, near only, both).
  * Safety proxies (D14 v04 A5): ttv = time to first violation (pair gap < 0) of the buffered footprint along the chosen plan
    over the enforced tracks, all 16 check times (to 4 s), clipped at 4 s (ttv_ip, ttv_nip: in-path / not-in-path enforced
    tracks; ttv_enf: the enforced pairs only within 2 s); min_gap_ip, min_gap_nip; v01's TTC proxy as ttc_proxy_v01 (R15 M1).
  * _arm_cov floors the threshold margin / sd at 1e-3 (as m_lib_v04.deploy_covariance; R15 m6).
K8 harness (Claude line, k8_sim_v01, 1 Nov 2026) = k7_sim_v01 plus the K8 additions, written by tests/make_k8_sim_v01.py
(90_DECISIONS/D14_K8_DESIGN_v02.md section 5 item 2). The additions change no decision: geometry, candidates, exemptions, back-off,
strata and the choice are k7_sim_v01's (test T1 of tests/test_k8_v01.py: every shared arm reproduces k7_sim_v01 exactly).
The tracker does not run in the loop: the recorded tracker output (cache) is replayed from the logged ego. Decision mode is one
decision per keyframe from the logged ego's state; loop mode is the closed-loop replay with non-reactive agents (CL-NR).
  * Fit-free arms on B0's covariance: B0a<alpha> (D14 A2) scales the covariance S_h + sigma_a^2 I by alpha in
    {1/4, 1/3, 1/2, 1, 2, 3, 4, 5}, i.e. the margin by sqrt(alpha): margin = sqrt(alpha) z_0.95 sd (the annotation term
    sigma_a^2 is scaled with the covariance); B0d<delta'> (D14 A3) keeps B0's covariance and takes the quantile of the
    nominal risk delta' in {0.05, 0.02, 0.01, 0.005, 0.001}: margin = z_{1-delta'} sd. B0a1 and B0d0.05 equal B0.
  * Per decision (both modes), under out["decisions"]: k, the sensor-offset bin, the infeasibility indicator, the back-off
    level used (1 = feasible at the arm's margin, 0.75/0.5/0.25/0 = backed off, -1 = emergency stop), the ego's speed, the
    chosen speed (the chosen candidate's planned speed 0.5 s ahead, capped at the logged speed when the plan is leashed
    there), the logged ego's speed 0.5 s ahead, the leashed planned progress over 0.5 s and the logged ego's progress
    over the same 0.5 s, the minimum pair gap over the enforced pairs within 2 s, the time to collision (gap_now /
    closing rate under the chosen plan, clipped at 20 s), the number of tracks with an enforced pair, and the record and
    exceedance counts of the relied-on pairs (relied-on axis separating, enforced, satisfied: the pairs behind the PD7
    records) over all steps and at the first check time only, by near (pair gap <= 5 m) x in-path (D14 A1).
  * Per episode, under out["cal"]: the calibration table of the relied-on pairs per (near x in-path, L0 stratum of the
    relied-on axis) under the arm's covariance (see _arm_cov): records, exceedances of the standardised error along the
    relied-on axis at delta in {0.1, 0.05, 0.01, 0.001}, NEES sum and count, NEES outside and above the 95 % chi-square(2)
    interval, ellipse coverage at 50/90/95/99 %, Gaussian NLL sum, energy-score sum, margin sums along the object's long
    and lateral axes (D14 A6, A7).
  * Episode summaries of these records (mean chosen speed, progress ratio, back-off counts, mean minimum gap, mean TTC,
    replay-divergence share, ANEES, p_v, mean margins). The K7 summary fields and the counts dict are unchanged.
K7 harness (Claude line, k7_sim_v01, 1 Nov 2026) = k6_sim_v02 with one change, written by tests/make_k7_sim_v01.py:
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
ARMS_K7 = ARMS
# K8 (D14 A2, A3): fit-free arms on B0's covariance. alpha scales the covariance (S_h + sigma_a^2 I), so the margin by sqrt(alpha);
# delta' keeps B0's covariance and changes the nominal risk (the normal quantile). B0a1 and B0d0.05 are B0.
# v02 (D14 v04 A2, A3; R15 M3): two-sided grids
ALPHAS = (1.0 / 32.0, 1.0 / 16.0, 0.125, 0.25, 1.0 / 3.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0)
ALPHA_ARMS = ("B0a0.03125", "B0a0.0625", "B0a0.125", "B0a0.25", "B0a0.333", "B0a0.5", "B0a1", "B0a2", "B0a3", "B0a4", "B0a5", "B0a8")
ALPHA_OF_ARM = dict(zip(ALPHA_ARMS, ALPHAS))
DELTAS_PRIME = (0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001)
DELTA_ARMS = ("B0d0.5", "B0d0.3", "B0d0.2", "B0d0.1", "B0d0.05", "B0d0.02", "B0d0.01", "B0d0.005", "B0d0.001")
DELTA_OF_ARM = dict(zip(DELTA_ARMS, DELTAS_PRIME))
Z_OF_DELTA = {0.5: 0.0, 0.3: 0.5244005127080407, 0.2: 0.8416212335729143, 0.1: 1.2815515655446004, 0.05: 1.6448536269514722,
              0.02: 2.0537489106318225, 0.01: 2.3263478740408408, 0.005: 2.5758293035489004,
              0.001: 3.090232306167813}   # z_{1-delta} (scipy.stats.norm.ppf; test T7)
ARMS = ARMS_K7 + ALPHA_ARMS + DELTA_ARMS
# v04 (D16 Choice 2 (b)): the joint arms M*J (primary) and M*Jx (exact split), M*'s per-stratum thresholds times one scalar
JOINT_ARMS = ("MstarJ", "MstarJx")
JOINT_RUN_STAMP = "EXPLORATORY (K8 joint arm M*J, k8_run_v04 --joint): nuScenes development evidence, not a confirmation"
ARMS = ARMS + JOINT_ARMS
ALPHA_EQ_OF_DELTA = {d: (Z_OF_DELTA[d] / Z) ** 2 for d in DELTAS_PRIME}   # a delta' arm is the alpha arm at alpha_eq (one curve)
CURVE_ALPHA_OF_ARM = dict(list(ALPHA_OF_ARM.items()) + [(a, ALPHA_EQ_OF_DELTA[DELTA_OF_ARM[a]]) for a in DELTA_ARMS])
SWEEP_ARMS = ALPHA_ARMS + DELTA_ARMS
FITFREE = ("LOG", "Z0", "B0") + ALPHA_ARMS + DELTA_ARMS   # arms that take no fit dictionary
CHI2_2 = (0.05063561596857975, 7.377758908227871)         # chi-square(2) quantiles 0.025 and 0.975: the NEES 95 % interval
CHI2_2_95 = 5.991464547107979                              # chi-square(2) quantile 0.95: the 95 % circle of an isotropic Gaussian
COV_LEVELS = (0.5, 0.9, 0.95, 0.99)                        # confidence-ellipse coverage levels (D14 A6)
CHI2_2_COV = (1.3862943611198906, 4.605170185988092, 5.991464547107979, 9.210340371976184)   # chi-square(2) quantiles at COV_LEVELS
DELTA_CURVE = (0.1, 0.05, 0.01, 0.001)                     # per-axis exceedance curve (D14 A6)
ES_DRAWS, ES_SEED = 200, 20261108                          # energy score: fixed standard-normal draws, shared by every record
_ES_Z = np.random.default_rng(ES_SEED).standard_normal((2, ES_DRAWS, 2))   # [0]: X draws, [1]: X' draws
LAM_ESTOP = -1.0                                           # back-off level recorded for the emergency stop
I_05 = 1                                                   # EVAL index of the 0.5 s check time (EVAL_T[1] = 0.5)
TTC_CLIP = 20.0                                            # s (v01 TTC proxy, kept as ttc_proxy_v01)
TTV_CLIP = 4.0                                             # s: D14 v04 A5, time to first violation clipped at the 4 s plan
BINDING_SLACK = 0.5                                        # m: D14 v04 A1, V2_binding pairs (slack G - margin <= 0.5 m)
DIVERGENCE_MPS = 2.0                                       # D14 A10: |chosen speed - logged speed| above this is a replay divergence
ST_FIELDS = ("n", "x", "n_h0", "x_h0", "v", "nb", "xb", "ne", "xe", "nd", "xd")   # per decision, per cell (see the header)
N_ST = 4 * len(ST_FIELDS)                                  # 4 cells (near x in-path; index = near * 2 + inpath) x 11 fields
TRK_FIELDS = ("nip_far", "nip_near", "nip_both", "ip_far", "ip_near", "ip_both")   # tracks with a relied-on record
N_TRK = len(TRK_FIELDS)
CAL_FIELDS = ("n", "x_d0.1", "x_d0.05", "x_d0.01", "x_d0.001", "nees_sum", "nees_n", "nees_out", "nees_hi", "cov50", "cov90", "cov95",
              "cov99", "nll_sum", "es_sum", "mg_long_sum", "mg_lat_sum")
N_CAL = len(CAL_FIELDS)
DEC_FIELDS = ("k", "ob", "infeasible", "lam", "v_now", "v_chosen", "v_log", "ds_plan", "ds_log", "min_gap", "min_gap_ip", "min_gap_nip",
              "ttv", "ttv_ip", "ttv_nip", "ttv_enf", "ttc_proxy_v01", "n_enf_tracks")
DEC_INT = ("k", "ob", "infeasible", "n_enf_tracks")
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
    fit dictionaries (thresholds as plain lists).
    K8 arms (fit-free): B0a<alpha> scales B0's covariance S_h + sigma_a^2 I by alpha, which scales the margin by sqrt(alpha):
    margin = sqrt(alpha) z_0.95 sd (sd = sqrt(a' S_h a + sigma_a^2), so the annotation term is scaled with the covariance);
    B0d<delta'> keeps B0's covariance and uses the quantile of the nominal risk delta': margin = z_{1-delta'} sd."""
    if arm == "Z0":
        return np.zeros_like(sd)
    if arm == "B0":
        return Z * sd
    if arm in ALPHA_OF_ARM:
        return math.sqrt(ALPHA_OF_ARM[arm]) * Z * sd
    if arm in DELTA_OF_ARM:
        return Z_OF_DELTA[DELTA_OF_ARM[arm]] * sd
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
        elif arm in ("B6", "Mstar") + JOINT_ARMS and (arm + "_ip") in f:
            out[:, h, :] = np.asarray(f[arm + "_ip"])[L0 + N_L0 * np.asarray(inp, int)[:, None]] * s
        elif arm == "B6":
            out[:, h, :] = np.asarray(f["B6"])[L0] * s
        elif arm == "Mstar" or arm in JOINT_ARMS:
            out[:, h, :] = np.asarray(f[arm])[L0] * s
        else:
            raise ValueError(arm)
    return out


# ---------------------------------------------------------------- planner

def plan_positions_speeds(s0, v0, vmax):
    """Planned arc length and speed of every candidate at the 16 check times, every 0.25 s (before the leash). The arc
    lengths are k6_sim_v02.plan_positions' (same integration, same order of operations); the speeds are K8's addition."""
    s = np.full(N_C, float(s0))
    v = np.full(N_C, float(v0))
    out = np.empty((N_C, N_EVAL))
    outv = np.empty((N_C, N_EVAL))
    j = 0
    for i in range(ACC_TABLE.shape[1]):
        vn = np.clip(v + ACC_TABLE[:, i] * DT_FINE, 0.0, vmax)
        s = s + 0.5 * (v + vn) * DT_FINE
        v = vn
        if j < N_EVAL and i + 1 == EVAL_IDX[j]:
            out[:, j] = s
            outv[:, j] = v
            j += 1
    return out, outv


def plan_positions(s0, v0, vmax):
    """Planned arc length of every candidate at the 16 check times, every 0.25 s (before the leash)."""
    return plan_positions_speeds(s0, v0, vmax)[0]


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


def _speed_extras(out, ctx):
    """K8 per-decision speed and progress quantities of the chosen candidate (D14 A4, A10). v_chosen: the candidate's planned
    speed 0.5 s ahead, capped at the logged ego's speed there when the plan is leashed at that check time (the closed loop
    caps the speed the same way); v_log: the logged ego's speed 0.5 s ahead (the leash's); ds_plan: the leashed planned arc
    length over the first 0.5 s; ds_log: the logged ego's arc length over the same 0.5 s, lead(t + 0.5) - lead(t); v_now: the
    ego's speed at the decision. None of this changes the decision."""
    sc, tk, s, v, splan_raw, splan, vplan, lead, lead16, vlead = ctx
    c = out["choice"]
    vl = max(float(vlead(tk + EVAL_T[I_05])), 0.0)
    vc = float(vplan[c, I_05])
    if splan_raw[c, I_05] > lead16[I_05]:
        vc = min(vc, vl)
    out["v_now"], out["v_chosen"], out["v_log"] = float(v), vc, vl
    out["ds_plan"] = float(splan[c, I_05] - s)
    out["ds_log"] = float(lead16[I_05] - float(lead(tk)))
    return out


def ttv_from_pair_gaps(pg16, cols):
    """D14 v04 A5: time to first violation of the buffered footprint along the chosen plan. pg16: (N_EVAL, J) pair gaps of the
    chosen plan at the 16 check times (0.25 ... 4 s; max over the object's axes of the buffered separation between the planned
    ego footprint and the track's predicted mean, the quantity gaps() returns); cols: the tracks scanned. Returns the first
    check time EVAL_T[i] at which any of them has a pair gap < 0, TTV_CLIP (4 s) when none does, None when cols is empty."""
    cols = np.asarray(cols, int)
    if not len(cols):
        return None
    bad = (pg16[:, cols] < 0.0).any(axis=1)
    return float(EVAL_T[int(np.argmax(bad))]) if bad.any() else TTV_CLIP


def _safety_extras(out, sc, s, gap, cur, ax, half, enf, inp=None):
    """K8 safety proxies at the decision state (D14 v04 A5), over the tracks with an enforced (track, check time) pair.
    min_gap: the smallest pair gap (max over the object's axes of the buffered separation between the planned ego footprint
    and the track's predicted mean) over the enforced pairs within 2 s; min_gap_ip / min_gap_nip: over the enforced pairs of
    in-path / not-in-path tracks (the method's flag). ttv: ttv_from_pair_gaps over the enforced tracks along the chosen plan
    (all 16 check times, so violations after the 2 s enforcement horizon count), ttv_ip / ttv_nip over the in-path /
    not-in-path enforced tracks; ttv_enf: the same over the enforced pairs only within 2 s (exempt C8 pairs, which no speed
    choice or held ego keeps apart, are skipped there) and every check time after 2 s. ttc_proxy_v01: v01's quantity (gap_now / closing over the first 0.5 s, clipped at 20 s), kept
    for comparison only (R15 M1: it counts closing on roadside objects the plan passes). None when nothing is enforced."""
    if not enf.any():
        return
    c = out["choice"]
    pg16 = np.max(gap[c], axis=-1)                                # (16, J): the pair gap of the chosen plan at every check time
    pg = pg16[:CC_EVAL]                                           # (8, J): at the enforced check times
    out["min_gap"] = float(pg[enf].min())
    inp = np.zeros(enf.shape[1], bool) if inp is None else np.asarray(inp, bool)
    for lab, msk in (("min_gap_ip", inp), ("min_gap_nip", ~inp)):
        e_ = enf & msk[None, :]
        out[lab] = float(pg[e_].min()) if e_.any() else None
    jj = np.flatnonzero(enf.any(axis=0))
    out["n_enf_tracks"] = int(len(jj))
    out["ttv"] = ttv_from_pair_gaps(pg16, jj)
    out["ttv_ip"] = ttv_from_pair_gaps(pg16, jj[inp[jj]])
    out["ttv_nip"] = ttv_from_pair_gaps(pg16, jj[~inp[jj]])
    m16 = np.zeros(pg16.shape, bool)                              # ttv_enf: only the enforced (track, check time) pairs within 2 s and
    m16[:CC_EVAL] = enf                                           # every check time of the enforced tracks after 2 s (nothing is
    m16[CC_EVAL:, jj] = True                                      # enforced there): the violations a speed choice could act on
    bad = ((pg16 < 0.0) & m16).any(axis=1)
    out["ttv_enf"] = float(EVAL_T[int(np.argmax(bad))]) if bad.any() else TTV_CLIP
    gnow, _ = gaps(sc, np.full((1, 1), float(s)), cur, ax, half)   # (1, 1, J, 2): the ego at its position, the tracks at their means
    gn = np.max(gnow[0, 0], axis=-1)[jj]
    closing = (gn - pg[I_05, jj]) / EVAL_T[I_05]
    with np.errstate(divide="ignore", invalid="ignore"):
        ttc = np.where(gn <= 0.0, 0.0, np.where(closing > 0.0, np.minimum(gn / np.where(closing > 0.0, closing, 1.0), TTC_CLIP), TTC_CLIP))
    out["ttc_proxy_v01"] = float(ttc.min())


def _arm_cov(arm, axj, pcov, mg2, sd2):
    """The arm's 2-D position covariance of each relied-on pair, in the object's axis frame (D14 A6: the covariance used per arm):
      Z0          none (mean only): returns None;
      B0          S_h + sigma_a^2 I, the raw tracker covariance with the annotation term, as the margin's sd;
      B0a<alpha>  alpha (S_h + sigma_a^2 I);
      B0d<delta'> S_h + sigma_a^2 I: B0's covariance at another nominal risk (the covariance itself is unchanged);
      B1          k(group, range) (S_h + sigma_a^2 I);
      B3, B4      (c / z)^2 (S_h + sigma_a^2 I);
      B6, Mstar   A (S_h + sigma_a^2 I) A with A = (c_long / z) a_l a_l' + (c_lat / z) a_t a_t', the deployable recalibrated
                  covariance of m_lib_v04.deploy_covariance with the pair's (L0 stratum, in-path) thresholds;
      B9          (r^2 / chi2_{2,0.95}) I, the isotropic Gaussian whose 95 % circle is the norm ball of radius r.
    Every margin arm except B9 and the delta' arms is read generically as D S' D with D = diag(c_a / z), c_a = margin_a / sd_a,
    S' = R (S_h + sigma_a^2 I) R' (R = the object's axes); a threshold c_a <= 1e-3 is replaced by 1e-3, exactly as
    deploy_covariance (v02, R15 m6; v01 floored the margin). axj: (n, 2, 2) object axes; pcov: (n, 3) sxx, sxy, syy; mg2, sd2:
    (n, 2) margins and sd along the axes."""
    if arm is None or arm == "Z0":
        return None
    n = len(mg2)
    if arm == "B9":
        Sp = np.zeros((n, 2, 2))
        Sp[:, 0, 0] = Sp[:, 1, 1] = mg2[:, 0] ** 2 / CHI2_2_95
        return Sp
    S = np.empty((n, 2, 2))
    S[:, 0, 0], S[:, 0, 1], S[:, 1, 0], S[:, 1, 1] = pcov[:, 0] + SIGMA_A ** 2, pcov[:, 1], pcov[:, 1], pcov[:, 2] + SIGMA_A ** 2
    Sp = np.einsum("nax,nxy,nby->nab", axj, S, axj)
    if arm in DELTA_OF_ARM:
        return Sp
    with np.errstate(invalid="ignore", divide="ignore"):         # (n, 2) per-axis scale c_a / z, c_a = margin / sd floored at 1e-3 as
        d = np.where(mg2 / sd2 >= 1e-3, mg2 / (Z * sd2), 1e-3 / Z)   # deploy_covariance (v01's arithmetic where no floor binds)
    return Sp * d[:, :, None] * d[:, None, :]


def _cal_pairs(arm, e, axj, pcov, mg2, sd2, a_rel, D):
    """Calibration diagnostics of the relied-on pairs under the arm's covariance (D14 A6): e (n, 2) position errors g - m in the
    world frame; a_rel (n,) the relied-on axis; D (n,) the signed error along it (as the records). Returns None for Z0, else a
    dict with nees, the standardised error u = D / sigma_rel (sigma_rel^2 = the covariance's variance along the relied-on
    axis; for the margin arms z sigma_rel = margin, so u > z_0.95 is the record's exceedance), the Gaussian NLL and the energy
    score ES = mean_i |X_i - e| - 0.5 mean_i |X_i - X'_i| from ES_DRAWS fixed standard-normal draws X = L Z (L the Cholesky
    factor), the same draws for every record."""
    Sp = _arm_cov(arm, axj, pcov, mg2, sd2)
    if Sp is None:
        return None
    eo = np.einsum("nax,nx->na", axj, e)                            # the errors along the object's axes
    a, b, c = Sp[:, 0, 0], Sp[:, 0, 1], Sp[:, 1, 1]
    det = a * c - b * b
    nees = (c * eo[:, 0] ** 2 - 2 * b * eo[:, 0] * eo[:, 1] + a * eo[:, 1] ** 2) / det
    sig_rel = np.sqrt(np.where(a_rel == 0, a, c))
    u = D / sig_rel
    nll = 0.5 * (nees + np.log(det)) + math.log(2 * math.pi)
    L = np.zeros_like(Sp)                                            # Cholesky factor of Sp
    L[:, 0, 0] = np.sqrt(a)
    L[:, 1, 0] = b / L[:, 0, 0]
    L[:, 1, 1] = np.sqrt(np.maximum(c - L[:, 1, 0] ** 2, 0.0))
    X = np.einsum("nab,mb->nma", L, _ES_Z[0])                        # (n, ES_DRAWS, 2)
    X2 = np.einsum("nab,mb->nma", L, _ES_Z[1])
    es = np.mean(np.hypot(X[..., 0] - eo[:, None, 0], X[..., 1] - eo[:, None, 1]), 1) - 0.5 * np.mean(np.hypot(X[..., 0] - X2[..., 0], X[..., 1] - X2[..., 1]), 1)
    return {"nees": nees, "u": u, "nll": nll, "es": es}


def _new_decs():
    return {f: [] for f in DEC_FIELDS + ("stats", "trk")}


def _push_dec(decs, k, ob, ps):
    """Appends one decision (DEC_FIELDS; None -> NaN for the float fields) and its relied-on counts (stats, trk)."""
    fixed = {"k": int(k), "ob": int(ob), "infeasible": int(ps["infeasible"]), "lam": LAM_ESTOP if ps["lam"] is None else float(ps["lam"]),
             "n_enf_tracks": int(ps["n_enf_tracks"])}
    for f in DEC_FIELDS:
        decs[f].append(fixed[f] if f in fixed else (float("nan") if ps[f] is None else float(ps[f])))
    decs["stats"].append(list(ps["stats"]))
    decs["trk"].append(list(ps["trk"]))


def _dec_summary(decs, cal):
    """Episode summaries of the K8 per-decision records and the calibration table (D14 A4, A5, A6, A7, A10). 'relied' = the
    relied-on pairs at any sensor offset; the analysis applies the population filters."""
    n = len(decs["k"])
    none = {"mean_chosen_speed": None, "mean_logged_speed": None, "progress_ratio": None, "backoff_counts": {}, "min_gap_mean": None,
            "min_gap_ip_mean": None, "ttv_mean": None, "share_ttv_lt_2s": None, "ttc_proxy_v01_mean": None, "divergence_share": None,
            "anees_relied": None, "p_v_relied": None, "mean_margin_relied": None, "records_relied": 0}
    if n == 0:
        return none
    lam = np.array(decs["lam"], float)
    bc = {("estop" if l_ == LAM_ESTOP else "%g" % l_): int((lam == l_).sum()) for l_ in (1.0,) + BACKOFF + (LAM_ESTOP,)}
    vc, vl = np.array(decs["v_chosen"], float), np.array(decs["v_log"], float)
    dsp, dsl = float(np.sum(decs["ds_plan"])), float(np.sum(decs["ds_log"]))
    mg_, tt, mgi = np.array(decs["min_gap"], float), np.array(decs["ttv"], float), np.array(decs["min_gap_ip"], float)
    tp = np.array(decs["ttc_proxy_v01"], float)
    ct = np.sum(np.array(list(cal.values()), float), axis=0) if cal else np.zeros(N_CAL)
    ci = {f: i for i, f in enumerate(CAL_FIELDS)}
    return {"mean_chosen_speed": float(vc.mean()), "mean_logged_speed": float(vl.mean()),
            "progress_ratio": (dsp / dsl) if dsl > 0 else None, "backoff_counts": bc,
            "min_gap_mean": float(np.nanmean(mg_)) if np.isfinite(mg_).any() else None,
            "min_gap_ip_mean": float(np.nanmean(mgi)) if np.isfinite(mgi).any() else None,
            "ttv_mean": float(np.nanmean(tt)) if np.isfinite(tt).any() else None,
            "share_ttv_lt_2s": float(np.mean(tt[np.isfinite(tt)] < 2.0)) if np.isfinite(tt).any() else None,
            "ttc_proxy_v01_mean": float(np.nanmean(tp)) if np.isfinite(tp).any() else None,
            "divergence_share": float(np.mean(np.abs(vc - vl) > DIVERGENCE_MPS)),
            "anees_relied": float(ct[ci["nees_sum"]] / ct[ci["nees_n"]]) if ct[ci["nees_n"]] > 0 else None,
            "p_v_relied": float(ct[ci["nees_out"]] / ct[ci["nees_n"]]) if ct[ci["nees_n"]] > 0 else None,
            "mean_margin_relied": [float(ct[ci["mg_long_sum"]] / ct[ci["n"]]), float(ct[ci["mg_lat_sum"]] / ct[ci["n"]])] if ct[ci["n"]] > 0 else None,
            "records_relied": int(ct[ci["n"]])}


def plan_step(sc, arm, fits, k, s, v, vmax, lead, counts, ob, vlead=None, cal=None):
    """One planning cycle at keyframe k from arc length s and speed v. counts: dict to receive the in-loop records of the
    chosen plan (None: no records); ob: the sensor-offset bin of those records. Returns the chosen candidate, whether no
    candidate satisfied the enforced constraints (then the emergency stop), and the exemption counters.
    K8: vlead(t) is the logged ego's speed at the leash's time (default sc.v_log, the decision mode's); cal: dict to receive the
    calibration table (None: none); the returned dict also carries the per-decision quantities of _speed_extras, _safety_extras
    and the relied-on pair counts of _record."""
    tk = float(sc.kf_t[k])
    ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
    rows = sc.tr_by_k[k]
    splan_raw, vplan = plan_positions_speeds(s, v, vmax)
    lead16 = lead(tk + EVAL_T)
    splan = np.minimum(splan_raw, lead16[None, :])
    prog = splan.mean(axis=1)
    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0, "lam": 1.0,
           "min_gap": None, "min_gap_ip": None, "min_gap_nip": None, "ttv": None, "ttv_ip": None, "ttv_nip": None, "ttv_enf": None,
           "ttc_proxy_v01": None, "n_enf_tracks": 0, "stats": [0.0] * N_ST, "trk": [0.0] * N_TRK}
    ctx = (sc, tk, s, v, splan_raw, splan, vplan, lead, lead16, vlead if vlead is not None else sc.v_log)
    if not len(rows) or arm == "LOG":
        return _speed_extras(out, ctx)
    cxe, cye = ex + R2C * math.cos(eyaw), ey + R2C * math.sin(eyaw)
    tr = sc.tr
    dx, dy = tr["x"][rows] - cxe, tr["y"][rows] - cye
    sel = rows[(np.hypot(dx, dy) < R_CONSIDER) & (dx * math.cos(eyaw) + dy * math.sin(eyaw) >= -EGO_L / 2)]
    if not len(sel):
        return _speed_extras(out, ctx)
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
    _safety_extras(out, sc, s, gap, cur, ax, half, enf, inp_sel)
    if counts is not None:
        enf8 = np.zeros((N_STEP, len(sel)), bool)
        enf8[:CC_STEPS] = enf[1::2]
        out["stats"], out["trk"] = _record(sc, k, sel, out["choice"], gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf8, ob,
                                           arm, sd, sc.tr["pred"][sel][:, :, 2:5], cal,
                                           0.0 if out["lam"] is None else float(out["lam"]))
    return _speed_extras(out, ctx)


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
    decs, cal = _new_decs(), {}
    for k in range(1, sc.K - 1):
        tk = float(sc.kf_t[k])
        ps = plan_step(sc, arm, fits, k, float(sc.s_log(tk)), max(sc.v_log(tk), 0.0), vmax, sc.s_log, counts, 0, None, cal)
        _push_dec(decs, k, 0, ps)
        frames += 1
        infeasible += int(ps["infeasible"])
        estops += int(ps["infeasible"] and ps["lam"] is None)
        unctrl += ps["unctrl"]
        brought += ps["brought"]
        acc.append(float(ACC_TABLE[ps["choice"], 0]))
    out.update({"frames": frames, "infeasible_frames": infeasible, "emergency_stop_frames": estops, "uncontrollable_pairs": unctrl,
                "brought_to_ego_pairs": brought,
                "mean_first_accel": float(np.mean(acc)) if acc else None})
    out.update(_dec_summary(decs, cal))
    out["decisions"], out["cal"] = decs, cal
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
    vlead = lambda t: sc.v_log(t - shift)  # noqa: E731  (K8: the logged ego's speed at the leash's time)
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
    decs, cal = _new_decs(), {}
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
        ps = plan_step(sc, arm, fits, k, s, v, vmax, lead, counts if record else None, ob, vlead, cal if record else None)
        _push_dec(decs, k, ob, ps)
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
    out.update(_dec_summary(decs, cal))
    out["decisions"], out["cal"] = decs, cal
    return out, counts


def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob, arm=None, sd=None, pcov=None, cal=None, lam_exec=1.0):
    """In-loop constraint records of the executed plan: paired tracks with a ground-truth annotation (>= 1 point, not in a
    bicycle rack) at k + h; for each separating axis, D = sign(sep) a.(g - m) and the exceedance D > margin. Counted per
    (sensor-offset bin, in-path, enforced, satisfied, pair-gap bin, relied-on axis, step, L0 stratum). Satisfied: the
    executed plan kept the relied-on axis's gap at or above its margin.
    K8: returns the N_ST per-decision counts of the relied-on pairs (relied-on axis separating, enforced, satisfied: the pairs
    behind the PD7 records) by near (pair gap <= GAP_BINS[1]) x in-path: records and exceedances over all steps and at the
    first check time (step 0) only. When cal is a dict, it accumulates the calibration table per key
    (near * 2 + inpath) * N_L0 + L0 of the relied-on axis: CAL_FIELDS (see _cal_pairs; the margins along both axes). The counts
    dict is filled exactly as in k7_sim_v01.
    v02: returns (stats, trk). stats = the N_ST counts (ST_FIELDS per cell, cell-major): v01's n, x, n_h0, x_h0, then v (relied
    records violated at the plan, D > G), nb / xb (binding: slack G - margin <= BINDING_SLACK), ne / xe (at the executed
    margin lam_exec * margin: relied-on axis argmax of G - lam_exec * margin, G > 0, enforced, any satisfaction; exceedance
    D > lam_exec * margin), nd / xd (one record per (step, ground-truth instance), the first track in order kept). trk = the
    tracks with a relied-on record by TRK_FIELDS (in-path x far only / near only / both)."""
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
        return [0.0] * N_ST, [0.0] * N_TRK
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
    # K8 (D14 A1, A6, A7): the relied-on pairs, i.e. the pairs behind the PD7 records (relied-on axis with G > 0, enforced,
    # satisfied), by near x in-path so the analysis can form PD7, SD1_7, PD and NIP
    st = np.zeros((4, len(ST_FIELDS)))
    trk = np.zeros(N_TRK)
    rel_ = relied[hh, jj]
    ok = (G[hh, jj, rel_] > 0) & enf[hh, jj] & sat[hh, jj]
    if ok.any():
        h_, j_, e_, a_ = hh[ok], jj[ok], e[ok], rel_[ok]
        D = np.sign(S[h_, j_, a_]) * np.sum(ax[j_, a_] * e_, -1)
        exc = (D > mg[j_, h_, a_]).astype(float)
        c4 = (pg[ok] <= GAP_BINS[1]).astype(int) * 2 + inpath[j_].astype(int)
        np.add.at(st[:, 0], c4, 1.0)
        np.add.at(st[:, 1], c4, exc)
        f0 = h_ == 0
        np.add.at(st[:, 2], c4[f0], 1.0)
        np.add.at(st[:, 3], c4[f0], exc[f0])
        # v02 (D14 v04 A1; R15 M6): violation of the relied constraint at the plan (D > G); binding pairs (slack <= 0.5 m)
        m_rel, g_rel = mg[j_, h_, a_], G[h_, j_, a_]
        np.add.at(st[:, 4], c4, (D > g_rel).astype(float))
        bnd = (g_rel - m_rel) <= BINDING_SLACK
        np.add.at(st[:, 5], c4[bnd], 1.0)
        np.add.at(st[:, 6], c4[bnd], exc[bnd])
        # A14 (R15 m7): one record per (step, ground-truth instance), the first track in order kept
        keep = np.zeros(len(h_), bool)
        seen = set()
        for i_, key_ in enumerate(zip(h_.tolist(), inst[j_].tolist())):
            if key_ not in seen:
                seen.add(key_)
                keep[i_] = True
        np.add.at(st[:, 9], c4[keep], 1.0)
        np.add.at(st[:, 10], c4[keep], exc[keep])
        # the tracks with a relied-on record by in-path x (far only, near only, both): the V2 reference 1 - (1 - delta)^n_tracks
        near_ = pg[ok] <= GAP_BINS[1]
        for jv in np.unique(j_).tolist():
            mj = j_ == jv
            nr, fr = bool(near_[mj].any()), bool((~near_[mj]).any())
            trk[3 * int(inpath[jv]) + (2 if (nr and fr) else (1 if nr else 0))] += 1.0
        if cal is not None:
            key = c4 * N_L0 + l0[j_, h_, a_]
            cd = _cal_pairs(arm, e_, ax[j_], pcov[j_, h_], mg[j_, h_], sd[j_, h_], a_, D) if (arm is not None and sd is not None) else None
            row = np.zeros((len(key), N_CAL))
            row[:, 0] = 1.0
            row[:, 15], row[:, 16] = mg[j_, h_, 0], mg[j_, h_, 1]
            if cd is not None:
                for i_, dl in enumerate(DELTA_CURVE):
                    row[:, 1 + i_] = cd["u"] > Z_OF_DELTA[dl]
                ne = cd["nees"]
                row[:, 5], row[:, 6] = ne, 1.0
                row[:, 7], row[:, 8] = (ne < CHI2_2[0]) | (ne > CHI2_2[1]), ne > CHI2_2[1]
                for i_, q in enumerate(CHI2_2_COV):
                    row[:, 9 + i_] = ne <= q
                row[:, 13], row[:, 14] = cd["nll"], cd["es"]
            for kk_, r_ in zip(key.tolist(), row):
                acc = cal.get(kk_)
                if acc is None:
                    cal[kk_] = r_.tolist()
                else:
                    for i_ in range(N_CAL):
                        acc[i_] += r_[i_]
    # v02 (R15 m9): the executed margin lam_exec * margin (lam_exec = 0 for the emergency stop), SD3-style: the relied-on axis at
    # that margin, separating, enforced, any satisfaction; exceedance D > lam_exec * margin. At lam_exec = 1 (a feasible
    # decision) every enforced pair is satisfied, so ne / xe equal n / x.
    mg_e = lam_exec * mg
    rel_e = np.argmax(G - mg_e.transpose(1, 0, 2), axis=-1)[hh, jj]
    oke = (G[hh, jj, rel_e] > 0) & enf[hh, jj]
    if oke.any():
        h_, j_, e_, a_ = hh[oke], jj[oke], e[oke], rel_e[oke]
        De = np.sign(S[h_, j_, a_]) * np.sum(ax[j_, a_] * e_, -1)
        c4e = (pg[oke] <= GAP_BINS[1]).astype(int) * 2 + inpath[j_].astype(int)
        np.add.at(st[:, 7], c4e, 1.0)
        np.add.at(st[:, 8], c4e, (De > mg_e[j_, h_, a_]).astype(float))
    return st.ravel().tolist(), trk.tolist()


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
