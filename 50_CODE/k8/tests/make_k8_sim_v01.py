#!/usr/bin/env python3
"""Writes 50_CODE/k8/k8_sim_v01.py from 50_CODE/k7/k7_sim_v01.py (Claude line, 1 Nov 2026; D14 v02 section 5 item 2).
Every change is a text replacement asserted to match exactly once, so the derivation is reproducible (test T5).
Functional changes, none of which touches the geometry, the candidates, the exemption rule, the back-off ladder, the strata
or the decision itself (test T1: the shared arms reproduce k7_sim_v01 exactly, decision mode and closed loop):
  * two families of fit-free arms on B0's covariance (D14 A2, A3): B0a<alpha> scales the covariance (S_h + sigma_a^2 I) by
    alpha, i.e. the margin by sqrt(alpha): margin = sqrt(alpha) z_0.95 sd; B0d<delta'> keeps B0's covariance and uses the
    quantile of the nominal risk delta': margin = z_{1-delta'} sd;
  * per decision the harness records the chosen speed, the logged ego's speed, the progress increment, the back-off level
    used, the minimum pair gap and the time to collision over the enforced constraints (D14 A4, A5, A10), and the record and
    exceedance counts of the relied-on pairs (all steps, and the first check time only) by near (pair gap <= 5 m) x in-path,
    for the trajectory-level exceedance and the one-step check (D14 A1);
  * per episode a calibration table of the relied-on pairs per (near x in-path, L0 stratum of the relied-on axis) under the
    arm's covariance (D14 A6, A7): records, per-axis exceedances at delta in {0.1, 0.05, 0.01, 0.001}, NEES sum and count,
    NEES outside and above the 95 % chi-square(2) interval, ellipse coverage at 50/90/95/99 %, NLL sum, energy-score sum
    (200 fixed standard-normal draws, seed 20261108), margin sums along the object's long and lateral axes;
  * run_decisions and run_episode return these under out["decisions"] and out["cal"] (the runner writes decisions_<tag>.npz
    and cal_<tag>.npz) and add episode summaries of them. Every K7 summary field and the counts dict are unchanged."""
import os

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(os.path.dirname(K8), "k7", "k7_sim_v01.py")
s = open(SRC, encoding="utf-8").read()

HEADER_OLD = '"""K7 harness (Claude line, k7_sim_v01, 1 Nov 2026) = k6_sim_v02 with one change, written by tests/make_k7_sim_v01.py:\n'
HEADER_NEW = (
    '"""K8 harness (Claude line, k8_sim_v01, 1 Nov 2026) = k7_sim_v01 plus the K8 additions, written by tests/make_k8_sim_v01.py\n'
    '(90_DECISIONS/D14_K8_DESIGN_v02.md section 5 item 2). The additions change no decision: geometry, candidates, exemptions, back-off,\n'
    'strata and the choice are k7_sim_v01\'s (test T1 of tests/test_k8_v01.py: every shared arm reproduces k7_sim_v01 exactly).\n'
    'The tracker does not run in the loop: the recorded tracker output (cache) is replayed from the logged ego. Decision mode is one\n'
    'decision per keyframe from the logged ego\'s state; loop mode is the closed-loop replay with non-reactive agents (CL-NR).\n'
    '  * Fit-free arms on B0\'s covariance: B0a<alpha> (D14 A2) scales the covariance S_h + sigma_a^2 I by alpha in\n'
    '    {1/4, 1/3, 1/2, 1, 2, 3, 4, 5}, i.e. the margin by sqrt(alpha): margin = sqrt(alpha) z_0.95 sd (the annotation term\n'
    '    sigma_a^2 is scaled with the covariance); B0d<delta\'> (D14 A3) keeps B0\'s covariance and takes the quantile of the\n'
    '    nominal risk delta\' in {0.05, 0.02, 0.01, 0.005, 0.001}: margin = z_{1-delta\'} sd. B0a1 and B0d0.05 equal B0.\n'
    '  * Per decision (both modes), under out["decisions"]: k, the sensor-offset bin, the infeasibility indicator, the back-off\n'
    '    level used (1 = feasible at the arm\'s margin, 0.75/0.5/0.25/0 = backed off, -1 = emergency stop), the ego\'s speed, the\n'
    '    chosen speed (the chosen candidate\'s planned speed 0.5 s ahead, capped at the logged speed when the plan is leashed\n'
    '    there), the logged ego\'s speed 0.5 s ahead, the leashed planned progress over 0.5 s and the logged ego\'s progress\n'
    '    over the same 0.5 s, the minimum pair gap over the enforced pairs within 2 s, the time to collision (gap_now /\n'
    '    closing rate under the chosen plan, clipped at 20 s), the number of tracks with an enforced pair, and the record and\n'
    '    exceedance counts of the relied-on pairs (relied-on axis separating, enforced, satisfied: the pairs behind the PD7\n'
    '    records) over all steps and at the first check time only, by near (pair gap <= 5 m) x in-path (D14 A1).\n'
    '  * Per episode, under out["cal"]: the calibration table of the relied-on pairs per (near x in-path, L0 stratum of the\n'
    '    relied-on axis) under the arm\'s covariance (see _arm_cov): records, exceedances of the standardised error along the\n'
    '    relied-on axis at delta in {0.1, 0.05, 0.01, 0.001}, NEES sum and count, NEES outside and above the 95 % chi-square(2)\n'
    '    interval, ellipse coverage at 50/90/95/99 %, Gaussian NLL sum, energy-score sum, margin sums along the object\'s long\n'
    '    and lateral axes (D14 A6, A7).\n'
    '  * Episode summaries of these records (mean chosen speed, progress ratio, back-off counts, mean minimum gap, mean TTC,\n'
    '    replay-divergence share, ANEES, p_v, mean margins). The K7 summary fields and the counts dict are unchanged.\n'
    'K7 harness (Claude line, k7_sim_v01, 1 Nov 2026) = k6_sim_v02 with one change, written by tests/make_k7_sim_v01.py:\n')

ARMS_OLD = 'ARMS = ("LOG", "Z0", "B0", "B1", "B3", "B4", "B9", "B6", "Mstar")   # LOG: the delayed logged profile, no planner (reference)\n'
ARMS_NEW = ARMS_OLD + (
    'ARMS_K7 = ARMS\n'
    '# K8 (D14 A2, A3): fit-free arms on B0\'s covariance. alpha scales the covariance (S_h + sigma_a^2 I), so the margin by sqrt(alpha);\n'
    '# delta\' keeps B0\'s covariance and changes the nominal risk (the normal quantile). B0a1 and B0d0.05 are B0.\n'
    'ALPHAS = (0.25, 1.0 / 3.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0)\n'
    'ALPHA_ARMS = ("B0a0.25", "B0a0.333", "B0a0.5", "B0a1", "B0a2", "B0a3", "B0a4", "B0a5")\n'
    'ALPHA_OF_ARM = dict(zip(ALPHA_ARMS, ALPHAS))\n'
    'DELTAS_PRIME = (0.05, 0.02, 0.01, 0.005, 0.001)\n'
    'DELTA_ARMS = ("B0d0.05", "B0d0.02", "B0d0.01", "B0d0.005", "B0d0.001")\n'
    'DELTA_OF_ARM = dict(zip(DELTA_ARMS, DELTAS_PRIME))\n'
    'Z_OF_DELTA = {0.1: 1.2815515655446004, 0.05: 1.6448536269514722, 0.02: 2.0537489106318225, 0.01: 2.3263478740408408,\n'
    '              0.005: 2.5758293035489004, 0.001: 3.090232306167813}   # z_{1-delta} (scipy.stats.norm.ppf; test T7)\n'
    'ARMS = ARMS_K7 + ALPHA_ARMS + DELTA_ARMS\n'
    'FITFREE = ("LOG", "Z0", "B0") + ALPHA_ARMS + DELTA_ARMS   # arms that take no fit dictionary\n'
    'CHI2_2 = (0.05063561596857975, 7.377758908227871)         # chi-square(2) quantiles 0.025 and 0.975: the NEES 95 % interval\n'
    'CHI2_2_95 = 5.991464547107979                              # chi-square(2) quantile 0.95: the 95 % circle of an isotropic Gaussian\n'
    'COV_LEVELS = (0.5, 0.9, 0.95, 0.99)                        # confidence-ellipse coverage levels (D14 A6)\n'
    'CHI2_2_COV = (1.3862943611198906, 4.605170185988092, 5.991464547107979, 9.210340371976184)   # chi-square(2) quantiles at COV_LEVELS\n'
    'DELTA_CURVE = (0.1, 0.05, 0.01, 0.001)                     # per-axis exceedance curve (D14 A6)\n'
    'ES_DRAWS, ES_SEED = 200, 20261108                          # energy score: fixed standard-normal draws, shared by every record\n'
    '_ES_Z = np.random.default_rng(ES_SEED).standard_normal((2, ES_DRAWS, 2))   # [0]: X draws, [1]: X\' draws\n'
    'LAM_ESTOP = -1.0                                           # back-off level recorded for the emergency stop\n'
    'I_05 = 1                                                   # EVAL index of the 0.5 s check time (EVAL_T[1] = 0.5)\n'
    'TTC_CLIP = 20.0                                            # s\n'
    'DIVERGENCE_MPS = 2.0                                       # D14 A10: |chosen speed - logged speed| above this is a replay divergence\n'
    'ST_FIELDS = ("n", "x", "n_h0", "x_h0")                     # per decision, per cell: relied-on pairs and exceedances, all steps / step 0\n'
    'N_ST = 4 * len(ST_FIELDS)                                  # 4 cells (near x in-path; index = near * 2 + inpath) x 4 fields\n'
    'CAL_FIELDS = ("n", "x_d0.1", "x_d0.05", "x_d0.01", "x_d0.001", "nees_sum", "nees_n", "nees_out", "nees_hi", "cov50", "cov90", "cov95",\n'
    '              "cov99", "nll_sum", "es_sum", "mg_long_sum", "mg_lat_sum")\n'
    'N_CAL = len(CAL_FIELDS)\n'
    'DEC_FIELDS = ("k", "ob", "infeasible", "lam", "v_now", "v_chosen", "v_log", "ds_plan", "ds_log", "min_gap", "ttc", "n_enf_tracks")\n')

MARGINS_DOC_OLD = ('    """Margin (m) along each object axis for every track, step and axis. fits: list over the 8 steps of the method-stage\n'
                   '    fit dictionaries (thresholds as plain lists)."""\n')
MARGINS_DOC_NEW = ('    """Margin (m) along each object axis for every track, step and axis. fits: list over the 8 steps of the method-stage\n'
                   '    fit dictionaries (thresholds as plain lists).\n'
                   '    K8 arms (fit-free): B0a<alpha> scales B0\'s covariance S_h + sigma_a^2 I by alpha, which scales the margin by sqrt(alpha):\n'
                   '    margin = sqrt(alpha) z_0.95 sd (sd = sqrt(a\' S_h a + sigma_a^2), so the annotation term is scaled with the covariance);\n'
                   '    B0d<delta\'> keeps B0\'s covariance and uses the quantile of the nominal risk delta\': margin = z_{1-delta\'} sd."""\n')
B0_OLD = '    if arm == "B0":\n        return Z * sd\n    out = np.empty_like(sd)\n'
B0_NEW = ('    if arm == "B0":\n        return Z * sd\n'
          '    if arm in ALPHA_OF_ARM:\n        return math.sqrt(ALPHA_OF_ARM[arm]) * Z * sd\n'
          '    if arm in DELTA_OF_ARM:\n        return Z_OF_DELTA[DELTA_OF_ARM[arm]] * sd\n'
          '    out = np.empty_like(sd)\n')

PLANPOS_OLD = ('def plan_positions(s0, v0, vmax):\n'
               '    """Planned arc length of every candidate at the 16 check times, every 0.25 s (before the leash)."""\n'
               '    s = np.full(N_C, float(s0))\n'
               '    v = np.full(N_C, float(v0))\n'
               '    out = np.empty((N_C, N_EVAL))\n'
               '    j = 0\n'
               '    for i in range(ACC_TABLE.shape[1]):\n'
               '        vn = np.clip(v + ACC_TABLE[:, i] * DT_FINE, 0.0, vmax)\n'
               '        s = s + 0.5 * (v + vn) * DT_FINE\n'
               '        v = vn\n'
               '        if j < N_EVAL and i + 1 == EVAL_IDX[j]:\n'
               '            out[:, j] = s\n'
               '            j += 1\n'
               '    return out\n')
PLANPOS_NEW = ('def plan_positions_speeds(s0, v0, vmax):\n'
               '    """Planned arc length and speed of every candidate at the 16 check times, every 0.25 s (before the leash). The arc\n'
               '    lengths are k6_sim_v02.plan_positions\' (same integration, same order of operations); the speeds are K8\'s addition."""\n'
               '    s = np.full(N_C, float(s0))\n'
               '    v = np.full(N_C, float(v0))\n'
               '    out = np.empty((N_C, N_EVAL))\n'
               '    outv = np.empty((N_C, N_EVAL))\n'
               '    j = 0\n'
               '    for i in range(ACC_TABLE.shape[1]):\n'
               '        vn = np.clip(v + ACC_TABLE[:, i] * DT_FINE, 0.0, vmax)\n'
               '        s = s + 0.5 * (v + vn) * DT_FINE\n'
               '        v = vn\n'
               '        if j < N_EVAL and i + 1 == EVAL_IDX[j]:\n'
               '            out[:, j] = s\n'
               '            outv[:, j] = v\n'
               '            j += 1\n'
               '    return out, outv\n'
               '\n'
               '\n'
               'def plan_positions(s0, v0, vmax):\n'
               '    """Planned arc length of every candidate at the 16 check times, every 0.25 s (before the leash)."""\n'
               '    return plan_positions_speeds(s0, v0, vmax)[0]\n')

HELPERS = '''def _speed_extras(out, ctx):
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


def _safety_extras(out, sc, s, gap, cur, ax, half, enf):
    """K8 safety proxies at the decision state (D14 A5, S1), over the enforced (track, check time) pairs of the chosen plan.
    min_gap: the smallest pair gap (max over the object's axes of the buffered separation between the planned ego footprint
    and the track's predicted mean) over the enforced pairs within 2 s. ttc: the smallest, over the tracks with an enforced
    pair, of gap_now / closing, where gap_now is the pair gap between the ego at its current position and the track's current
    mean and closing = (gap_now - the pair gap at the 0.5 s check time under the chosen plan) / 0.5 s; a track that is not
    closing has TTC_CLIP, a track already inside the buffered footprint has 0; clipped at TTC_CLIP = 20 s. Both are None when
    no pair is enforced."""
    if not enf.any():
        return
    c = out["choice"]
    pg = np.max(gap[c], axis=-1)[:CC_EVAL]                        # (8, J): the pair gap of the chosen plan at the enforced check times
    out["min_gap"] = float(pg[enf].min())
    jj = np.flatnonzero(enf.any(axis=0))
    out["n_enf_tracks"] = int(len(jj))
    gnow, _ = gaps(sc, np.full((1, 1), float(s)), cur, ax, half)   # (1, 1, J, 2): the ego at its position, the tracks at their means
    gn = np.max(gnow[0, 0], axis=-1)[jj]
    closing = (gn - pg[I_05, jj]) / EVAL_T[I_05]
    with np.errstate(divide="ignore", invalid="ignore"):
        ttc = np.where(gn <= 0.0, 0.0, np.where(closing > 0.0, np.minimum(gn / np.where(closing > 0.0, closing, 1.0), TTC_CLIP), TTC_CLIP))
    out["ttc"] = float(ttc.min())


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
    S' = R (S_h + sigma_a^2 I) R' (R = the object's axes); a margin <= 1e-3 m is replaced by 1e-3, as deploy_covariance replaces
    a threshold <= 0. axj: (n, 2, 2) object axes; pcov: (n, 3) sxx, sxy, syy; mg2, sd2: (n, 2) margins and sd along the axes."""
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
    d = np.maximum(mg2, 1e-3) / (Z * sd2)                            # (n, 2) per-axis scale c_a / z
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
    return {f: [] for f in DEC_FIELDS + ("stats",)}


def _push_dec(decs, k, ob, ps):
    lam = LAM_ESTOP if ps["lam"] is None else float(ps["lam"])
    for f, val in (("k", int(k)), ("ob", int(ob)), ("infeasible", int(ps["infeasible"])), ("lam", lam), ("v_now", ps["v_now"]),
                   ("v_chosen", ps["v_chosen"]), ("v_log", ps["v_log"]), ("ds_plan", ps["ds_plan"]), ("ds_log", ps["ds_log"]),
                   ("min_gap", float("nan") if ps["min_gap"] is None else ps["min_gap"]),
                   ("ttc", float("nan") if ps["ttc"] is None else ps["ttc"]), ("n_enf_tracks", int(ps["n_enf_tracks"]))):
        decs[f].append(val)
    decs["stats"].append(list(ps["stats"]))


def _dec_summary(decs, cal):
    """Episode summaries of the K8 per-decision records and the calibration table (D14 A4, A5, A6, A7, A10). 'relied' = the
    relied-on pairs at any sensor offset; the analysis applies the population filters."""
    n = len(decs["k"])
    none = {"mean_chosen_speed": None, "mean_logged_speed": None, "progress_ratio": None, "backoff_counts": {}, "min_gap_mean": None,
            "ttc_mean": None, "share_ttc_lt_2s": None, "divergence_share": None, "anees_relied": None, "p_v_relied": None,
            "mean_margin_relied": None, "records_relied": 0}
    if n == 0:
        return none
    lam = np.array(decs["lam"], float)
    bc = {("estop" if l_ == LAM_ESTOP else "%g" % l_): int((lam == l_).sum()) for l_ in (1.0,) + BACKOFF + (LAM_ESTOP,)}
    vc, vl = np.array(decs["v_chosen"], float), np.array(decs["v_log"], float)
    dsp, dsl = float(np.sum(decs["ds_plan"])), float(np.sum(decs["ds_log"]))
    mg_, tt = np.array(decs["min_gap"], float), np.array(decs["ttc"], float)
    ct = np.sum(np.array(list(cal.values()), float), axis=0) if cal else np.zeros(N_CAL)
    ci = {f: i for i, f in enumerate(CAL_FIELDS)}
    return {"mean_chosen_speed": float(vc.mean()), "mean_logged_speed": float(vl.mean()),
            "progress_ratio": (dsp / dsl) if dsl > 0 else None, "backoff_counts": bc,
            "min_gap_mean": float(np.nanmean(mg_)) if np.isfinite(mg_).any() else None,
            "ttc_mean": float(np.nanmean(tt)) if np.isfinite(tt).any() else None,
            "share_ttc_lt_2s": float(np.mean(tt[np.isfinite(tt)] < 2.0)) if np.isfinite(tt).any() else None,
            "divergence_share": float(np.mean(np.abs(vc - vl) > DIVERGENCE_MPS)),
            "anees_relied": float(ct[ci["nees_sum"]] / ct[ci["nees_n"]]) if ct[ci["nees_n"]] > 0 else None,
            "p_v_relied": float(ct[ci["nees_out"]] / ct[ci["nees_n"]]) if ct[ci["nees_n"]] > 0 else None,
            "mean_margin_relied": [float(ct[ci["mg_long_sum"]] / ct[ci["n"]]), float(ct[ci["mg_lat_sum"]] / ct[ci["n"]])] if ct[ci["n"]] > 0 else None,
            "records_relied": int(ct[ci["n"]])}


'''
PLANSTEP_DEF_OLD = ('def plan_step(sc, arm, fits, k, s, v, vmax, lead, counts, ob):\n'
                    '    """One planning cycle at keyframe k from arc length s and speed v. counts: dict to receive the in-loop records of the\n'
                    '    chosen plan (None: no records); ob: the sensor-offset bin of those records. Returns the chosen candidate, whether no\n'
                    '    candidate satisfied the enforced constraints (then the emergency stop), and the exemption counters."""\n')
PLANSTEP_DEF_NEW = HELPERS + (
    'def plan_step(sc, arm, fits, k, s, v, vmax, lead, counts, ob, vlead=None, cal=None):\n'
    '    """One planning cycle at keyframe k from arc length s and speed v. counts: dict to receive the in-loop records of the\n'
    '    chosen plan (None: no records); ob: the sensor-offset bin of those records. Returns the chosen candidate, whether no\n'
    '    candidate satisfied the enforced constraints (then the emergency stop), and the exemption counters.\n'
    '    K8: vlead(t) is the logged ego\'s speed at the leash\'s time (default sc.v_log, the decision mode\'s); cal: dict to receive the\n'
    '    calibration table (None: none); the returned dict also carries the per-decision quantities of _speed_extras, _safety_extras\n'
    '    and the relied-on pair counts of _record."""\n')

SPLAN_OLD = ('    splan = np.minimum(plan_positions(s, v, vmax), lead(tk + EVAL_T)[None, :])\n'
             '    prog = splan.mean(axis=1)\n'
             '    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0, "lam": 1.0}\n'
             '    if not len(rows) or arm == "LOG":\n'
             '        return out\n')
SPLAN_NEW = ('    splan_raw, vplan = plan_positions_speeds(s, v, vmax)\n'
             '    lead16 = lead(tk + EVAL_T)\n'
             '    splan = np.minimum(splan_raw, lead16[None, :])\n'
             '    prog = splan.mean(axis=1)\n'
             '    out = {"choice": int(np.argmax(prog)), "infeasible": False, "unctrl": 0, "brought": 0, "pen": 0.0, "lam": 1.0,\n'
             '           "min_gap": None, "ttc": None, "n_enf_tracks": 0, "stats": [0.0] * N_ST}\n'
             '    ctx = (sc, tk, s, v, splan_raw, splan, vplan, lead, lead16, vlead if vlead is not None else sc.v_log)\n'
             '    if not len(rows) or arm == "LOG":\n'
             '        return _speed_extras(out, ctx)\n')
NOSEL_OLD = '    if not len(sel):\n        return out\n'
NOSEL_NEW = '    if not len(sel):\n        return _speed_extras(out, ctx)\n'
END_OLD = ('    out["pen"] = float(pen[out["choice"]])\n'
           '    if counts is not None:\n'
           '        enf8 = np.zeros((N_STEP, len(sel)), bool)\n'
           '        enf8[:CC_STEPS] = enf[1::2]\n'
           '        _record(sc, k, sel, out["choice"], gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf8, ob)\n'
           '    return out\n')
END_NEW = ('    out["pen"] = float(pen[out["choice"]])\n'
           '    _safety_extras(out, sc, s, gap, cur, ax, half, enf)\n'
           '    if counts is not None:\n'
           '        enf8 = np.zeros((N_STEP, len(sel)), bool)\n'
           '        enf8[:CC_STEPS] = enf[1::2]\n'
           '        out["stats"] = _record(sc, k, sel, out["choice"], gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf8, ob,\n'
           '                               arm, sd, sc.tr["pred"][sel][:, :, 2:5], cal)\n'
           '    return _speed_extras(out, ctx)\n')

RD_OLD = ('    frames = infeasible = unctrl = brought = estops = 0\n'
          '    acc = []\n'
          '    for k in range(1, sc.K - 1):\n'
          '        tk = float(sc.kf_t[k])\n'
          '        ps = plan_step(sc, arm, fits, k, float(sc.s_log(tk)), max(sc.v_log(tk), 0.0), vmax, sc.s_log, counts, 0)\n'
          '        frames += 1\n')
RD_NEW = ('    frames = infeasible = unctrl = brought = estops = 0\n'
          '    acc = []\n'
          '    decs, cal = _new_decs(), {}\n'
          '    for k in range(1, sc.K - 1):\n'
          '        tk = float(sc.kf_t[k])\n'
          '        ps = plan_step(sc, arm, fits, k, float(sc.s_log(tk)), max(sc.v_log(tk), 0.0), vmax, sc.s_log, counts, 0, None, cal)\n'
          '        _push_dec(decs, k, 0, ps)\n'
          '        frames += 1\n')
RD_END_OLD = ('                "mean_first_accel": float(np.mean(acc)) if acc else None})\n'
              '    return out, counts\n')
RD_END_NEW = ('                "mean_first_accel": float(np.mean(acc)) if acc else None})\n'
              '    out.update(_dec_summary(decs, cal))\n'
              '    out["decisions"], out["cal"] = decs, cal\n'
              '    return out, counts\n')

RE_LEAD_OLD = '    lead = lambda t: sc.s_log(np.asarray(t) - shift)  # noqa: E731\n'
RE_LEAD_NEW = ('    lead = lambda t: sc.s_log(np.asarray(t) - shift)  # noqa: E731\n'
               '    vlead = lambda t: sc.v_log(t - shift)  # noqa: E731  (K8: the logged ego\'s speed at the leash\'s time)\n')
RE_INIT_OLD = '    out["entered"] = True\n    counts = {}\n    trace = hashlib.sha256()\n'
RE_INIT_NEW = '    out["entered"] = True\n    counts = {}\n    decs, cal = _new_decs(), {}\n    trace = hashlib.sha256()\n'
RE_PS_OLD = '        ps = plan_step(sc, arm, fits, k, s, v, vmax, lead, counts if record else None, ob)\n'
RE_PS_NEW = ('        ps = plan_step(sc, arm, fits, k, s, v, vmax, lead, counts if record else None, ob, vlead, cal if record else None)\n'
             '        _push_dec(decs, k, ob, ps)\n')
RE_END_OLD = ('                "n_front_buffer_intrusions": len(near), "trace_sha256": trace.hexdigest()})\n'
              '    return out, counts\n')
RE_END_NEW = ('                "n_front_buffer_intrusions": len(near), "trace_sha256": trace.hexdigest()})\n'
              '    out.update(_dec_summary(decs, cal))\n'
              '    out["decisions"], out["cal"] = decs, cal\n'
              '    return out, counts\n')

REC_DEF_OLD = ('def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob):\n'
               '    """In-loop constraint records of the executed plan: paired tracks with a ground-truth annotation (>= 1 point, not in a\n'
               '    bicycle rack) at k + h; for each separating axis, D = sign(sep) a.(g - m) and the exceedance D > margin. Counted per\n'
               '    (sensor-offset bin, in-path, enforced, satisfied, pair-gap bin, relied-on axis, step, L0 stratum). Satisfied: the\n'
               '    executed plan kept the relied-on axis\'s gap at or above its margin."""\n')
REC_DEF_NEW = ('def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob, arm=None, sd=None, pcov=None, cal=None):\n'
               '    """In-loop constraint records of the executed plan: paired tracks with a ground-truth annotation (>= 1 point, not in a\n'
               '    bicycle rack) at k + h; for each separating axis, D = sign(sep) a.(g - m) and the exceedance D > margin. Counted per\n'
               '    (sensor-offset bin, in-path, enforced, satisfied, pair-gap bin, relied-on axis, step, L0 stratum). Satisfied: the\n'
               '    executed plan kept the relied-on axis\'s gap at or above its margin.\n'
               '    K8: returns the N_ST per-decision counts of the relied-on pairs (relied-on axis separating, enforced, satisfied: the pairs\n'
               '    behind the PD7 records) by near (pair gap <= GAP_BINS[1]) x in-path: records and exceedances over all steps and at the\n'
               '    first check time (step 0) only. When cal is a dict, it accumulates the calibration table per key\n'
               '    (near * 2 + inpath) * N_L0 + L0 of the relied-on axis: CAL_FIELDS (see _cal_pairs; the margins along both axes). The counts\n'
               '    dict is filled exactly as in k7_sim_v01."""\n')
REC_EMPTY_OLD = '    if not hh:\n        return\n'
REC_EMPTY_NEW = '    if not hh:\n        return [0.0] * N_ST\n'
REC_END_OLD = ('        for c_, x_ in zip(cell.tolist(), exc.tolist()):\n'
               '            c = counts.setdefault(c_, [0, 0])\n'
               '            c[0] += 1\n'
               '            c[1] += int(x_)\n'
               '\n'
               '\n'
               'def decode_cell(cell):\n')
REC_END_NEW = ('        for c_, x_ in zip(cell.tolist(), exc.tolist()):\n'
               '            c = counts.setdefault(c_, [0, 0])\n'
               '            c[0] += 1\n'
               '            c[1] += int(x_)\n'
               '    # K8 (D14 A1, A6, A7): the relied-on pairs, i.e. the pairs behind the PD7 records (relied-on axis with G > 0, enforced,\n'
               '    # satisfied), by near x in-path so the analysis can form PD7, SD1_7, PD and NIP\n'
               '    st = np.zeros((4, len(ST_FIELDS)))\n'
               '    rel_ = relied[hh, jj]\n'
               '    ok = (G[hh, jj, rel_] > 0) & enf[hh, jj] & sat[hh, jj]\n'
               '    if ok.any():\n'
               '        h_, j_, e_, a_ = hh[ok], jj[ok], e[ok], rel_[ok]\n'
               '        D = np.sign(S[h_, j_, a_]) * np.sum(ax[j_, a_] * e_, -1)\n'
               '        exc = (D > mg[j_, h_, a_]).astype(float)\n'
               '        c4 = (pg[ok] <= GAP_BINS[1]).astype(int) * 2 + inpath[j_].astype(int)\n'
               '        np.add.at(st[:, 0], c4, 1.0)\n'
               '        np.add.at(st[:, 1], c4, exc)\n'
               '        f0 = h_ == 0\n'
               '        np.add.at(st[:, 2], c4[f0], 1.0)\n'
               '        np.add.at(st[:, 3], c4[f0], exc[f0])\n'
               '        if cal is not None:\n'
               '            key = c4 * N_L0 + l0[j_, h_, a_]\n'
               '            cd = _cal_pairs(arm, e_, ax[j_], pcov[j_, h_], mg[j_, h_], sd[j_, h_], a_, D) if (arm is not None and sd is not None) else None\n'
               '            row = np.zeros((len(key), N_CAL))\n'
               '            row[:, 0] = 1.0\n'
               '            row[:, 15], row[:, 16] = mg[j_, h_, 0], mg[j_, h_, 1]\n'
               '            if cd is not None:\n'
               '                for i_, dl in enumerate(DELTA_CURVE):\n'
               '                    row[:, 1 + i_] = cd["u"] > Z_OF_DELTA[dl]\n'
               '                ne = cd["nees"]\n'
               '                row[:, 5], row[:, 6] = ne, 1.0\n'
               '                row[:, 7], row[:, 8] = (ne < CHI2_2[0]) | (ne > CHI2_2[1]), ne > CHI2_2[1]\n'
               '                for i_, q in enumerate(CHI2_2_COV):\n'
               '                    row[:, 9 + i_] = ne <= q\n'
               '                row[:, 13], row[:, 14] = cd["nll"], cd["es"]\n'
               '            for kk_, r_ in zip(key.tolist(), row):\n'
               '                acc = cal.get(kk_)\n'
               '                if acc is None:\n'
               '                    cal[kk_] = r_.tolist()\n'
               '                else:\n'
               '                    for i_ in range(N_CAL):\n'
               '                        acc[i_] += r_[i_]\n'
               '    return st.ravel().tolist()\n'
               '\n'
               '\n'
               'def decode_cell(cell):\n')

rep = [(HEADER_OLD, HEADER_NEW), (ARMS_OLD, ARMS_NEW), (MARGINS_DOC_OLD, MARGINS_DOC_NEW), (B0_OLD, B0_NEW), (PLANPOS_OLD, PLANPOS_NEW),
       (PLANSTEP_DEF_OLD, PLANSTEP_DEF_NEW), (SPLAN_OLD, SPLAN_NEW), (NOSEL_OLD, NOSEL_NEW), (END_OLD, END_NEW), (RD_OLD, RD_NEW),
       (RD_END_OLD, RD_END_NEW), (RE_LEAD_OLD, RE_LEAD_NEW), (RE_INIT_OLD, RE_INIT_NEW), (RE_PS_OLD, RE_PS_NEW), (RE_END_OLD, RE_END_NEW),
       (REC_DEF_OLD, REC_DEF_NEW), (REC_EMPTY_OLD, REC_EMPTY_NEW), (REC_END_OLD, REC_END_NEW)]
for a, b in rep:
    assert s.count(a) == 1, "anchor not found exactly once: " + a[:80]
    s = s.replace(a, b, 1)
open(os.path.join(K8, "k8_sim_v01.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k8_sim_v01.py written")
