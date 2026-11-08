#!/usr/bin/env python3
"""Writes 50_CODE/k8/k8_sim_v02.py from 50_CODE/k8/k8_sim_v01.py (Claude line, 1 Nov 2026; 90_DECISIONS/D14_K8_DESIGN_v04.md
section 5 item 1, applying review 70_TESTS/R15_K8_CODE_AND_DEV_REVIEW_v01.md). Every change is a text replacement asserted to match
exactly once (test T5 of tests/test_k8_v02.py reproduces the file byte for byte). None of the changes touches the geometry, the
candidates, the exemption rule, the back-off ladder, the strata or the choice (test T1: every shared arm reproduces k7_sim_v01
and k8_sim_v01 exactly):
  * two-sided grids (D14 v04 A2, A3; R15 M3): alpha in {1/32, 1/16, 1/8, 1/4, 1/3, 1/2, 1, 2, 3, 4, 5, 8}, delta' in {0.5, 0.3,
    0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001}; ALPHA_EQ_OF_DELTA = (z_{1-delta'} / z_0.95)^2 places every delta' arm on the alpha
    curve (CURVE_ALPHA_OF_ARM);
  * per-decision relied-on counts (D14 v04 A1, A14; R15 M6, m7, m9): per near x in-path cell, besides n, x, n_h0, x_h0 of v01,
    v (relied constraints violated at the plan, D > G), nb / xb (binding pairs, slack G - margin <= 0.5 m, and their
    exceedances), ne / xe (records and exceedances at the executed margin lam * margin, SD3-style: relied-on axis at the
    executed margin, separating, enforced, any satisfaction; lam = 0 for the emergency stop), nd / xd (one record per step and
    ground-truth instance, the first track kept); and the number of tracks with a relied-on record by in-path x near/far
    (TRK_FIELDS: the V2 reference 1 - (1 - delta)^n_tracks);
  * safety proxies (D14 v04 A5; R15 M1): the time to first violation (TTV) of the buffered footprint along the chosen plan over
    the enforced tracks, all 16 check times, clipped at 4 s (also over the in-path and the not-in-path enforced tracks); the
    minimum pair gap split by in-path / not in-path; v01's TTC proxy kept as ttc_proxy_v01 for comparison only;
  * _arm_cov floors the threshold c_a = margin_a / sd_a at 1e-3, as m_lib_v04.deploy_covariance (R15 m6; no effect on the
    development scenes: the smallest threshold there is 0.032)."""
import os

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(K8, "k8_sim_v01.py")
s = open(SRC, encoding="utf-8").read()

HEADER_OLD = '"""K8 harness (Claude line, k8_sim_v01, 1 Nov 2026) = k7_sim_v01 plus the K8 additions, written by tests/make_k8_sim_v01.py\n'
HEADER_NEW = (
    '"""K8 harness (Claude line, k8_sim_v02, 1 Nov 2026) = k8_sim_v01 with the R15 changes, written by tests/make_k8_sim_v02.py\n'
    '(90_DECISIONS/D14_K8_DESIGN_v04.md section 5 item 1). No decision changes (test T1 of tests/test_k8_v02.py).\n'
    '  * Two-sided grids (D14 v04 A2, A3): alpha in {1/32, 1/16, 1/8, 1/4, 1/3, 1/2, 1, 2, 3, 4, 5, 8} (B0a<alpha>: margin\n'
    '    sqrt(alpha) z_0.95 sd; the annotation term sigma_a^2 is scaled with the covariance, so the effective floor is\n'
    '    sqrt(alpha) 0.10 m), delta\' in {0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001} (B0d<delta\'>: margin z_{1-delta\'} sd).\n'
    '    Both are one curve: a delta\' arm is the alpha arm at alpha_eq = (z_{1-delta\'} / z_0.95)^2 (CURVE_ALPHA_OF_ARM).\n'
    '  * Per decision, per near x in-path cell (ST_FIELDS): n, x, n_h0, x_h0 (v01), v = relied constraints violated at the plan\n'
    '    (D > G along the relied-on axis), nb / xb = binding pairs (slack G - margin <= 0.5 m) and their exceedances, ne / xe =\n'
    '    records and exceedances at the executed margin lam * margin (relied-on axis at that margin, separating, enforced, any\n'
    '    satisfaction; lam = 0 for the emergency stop), nd / xd = de-duplicated (one record per step and ground-truth instance,\n'
    '    the first track in order kept); TRK_FIELDS = tracks with a relied-on record by in-path x (far only, near only, both).\n'
    '  * Safety proxies (D14 v04 A5): ttv = time to first violation (pair gap < 0) of the buffered footprint along the chosen plan\n'
    '    over the enforced tracks, all 16 check times (to 4 s), clipped at 4 s (ttv_ip, ttv_nip: in-path / not-in-path enforced\n'
    '    tracks; ttv_enf: the enforced pairs only within 2 s); min_gap_ip, min_gap_nip; v01\'s TTC proxy as ttc_proxy_v01 (R15 M1).\n'
    '  * _arm_cov floors the threshold margin / sd at 1e-3 (as m_lib_v04.deploy_covariance; R15 m6).\n'
    'K8 harness (Claude line, k8_sim_v01, 1 Nov 2026) = k7_sim_v01 plus the K8 additions, written by tests/make_k8_sim_v01.py\n')

GRID_OLD = ('ALPHAS = (0.25, 1.0 / 3.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0)\n'
            'ALPHA_ARMS = ("B0a0.25", "B0a0.333", "B0a0.5", "B0a1", "B0a2", "B0a3", "B0a4", "B0a5")\n'
            'ALPHA_OF_ARM = dict(zip(ALPHA_ARMS, ALPHAS))\n'
            'DELTAS_PRIME = (0.05, 0.02, 0.01, 0.005, 0.001)\n'
            'DELTA_ARMS = ("B0d0.05", "B0d0.02", "B0d0.01", "B0d0.005", "B0d0.001")\n'
            'DELTA_OF_ARM = dict(zip(DELTA_ARMS, DELTAS_PRIME))\n'
            'Z_OF_DELTA = {0.1: 1.2815515655446004, 0.05: 1.6448536269514722, 0.02: 2.0537489106318225, 0.01: 2.3263478740408408,\n'
            '              0.005: 2.5758293035489004, 0.001: 3.090232306167813}   # z_{1-delta} (scipy.stats.norm.ppf; test T7)\n'
            'ARMS = ARMS_K7 + ALPHA_ARMS + DELTA_ARMS\n')
GRID_NEW = ('# v02 (D14 v04 A2, A3; R15 M3): two-sided grids\n'
            'ALPHAS = (1.0 / 32.0, 1.0 / 16.0, 0.125, 0.25, 1.0 / 3.0, 0.5, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0)\n'
            'ALPHA_ARMS = ("B0a0.03125", "B0a0.0625", "B0a0.125", "B0a0.25", "B0a0.333", "B0a0.5", "B0a1", "B0a2", "B0a3", "B0a4", "B0a5", "B0a8")\n'
            'ALPHA_OF_ARM = dict(zip(ALPHA_ARMS, ALPHAS))\n'
            'DELTAS_PRIME = (0.5, 0.3, 0.2, 0.1, 0.05, 0.02, 0.01, 0.005, 0.001)\n'
            'DELTA_ARMS = ("B0d0.5", "B0d0.3", "B0d0.2", "B0d0.1", "B0d0.05", "B0d0.02", "B0d0.01", "B0d0.005", "B0d0.001")\n'
            'DELTA_OF_ARM = dict(zip(DELTA_ARMS, DELTAS_PRIME))\n'
            'Z_OF_DELTA = {0.5: 0.0, 0.3: 0.5244005127080407, 0.2: 0.8416212335729143, 0.1: 1.2815515655446004, 0.05: 1.6448536269514722,\n'
            '              0.02: 2.0537489106318225, 0.01: 2.3263478740408408, 0.005: 2.5758293035489004,\n'
            '              0.001: 3.090232306167813}   # z_{1-delta} (scipy.stats.norm.ppf; test T7)\n'
            'ARMS = ARMS_K7 + ALPHA_ARMS + DELTA_ARMS\n'
            'ALPHA_EQ_OF_DELTA = {d: (Z_OF_DELTA[d] / Z) ** 2 for d in DELTAS_PRIME}   # a delta\' arm is the alpha arm at alpha_eq (one curve)\n'
            'CURVE_ALPHA_OF_ARM = dict(list(ALPHA_OF_ARM.items()) + [(a, ALPHA_EQ_OF_DELTA[DELTA_OF_ARM[a]]) for a in DELTA_ARMS])\n'
            'SWEEP_ARMS = ALPHA_ARMS + DELTA_ARMS\n')

TTC_OLD = 'TTC_CLIP = 20.0                                            # s\n'
TTC_NEW = ('TTC_CLIP = 20.0                                            # s (v01 TTC proxy, kept as ttc_proxy_v01)\n'
           'TTV_CLIP = 4.0                                             # s: D14 v04 A5, time to first violation clipped at the 4 s plan\n'
           'BINDING_SLACK = 0.5                                        # m: D14 v04 A1, V2_binding pairs (slack G - margin <= 0.5 m)\n')
ST_OLD = ('ST_FIELDS = ("n", "x", "n_h0", "x_h0")                     # per decision, per cell: relied-on pairs and exceedances, all steps / step 0\n'
          'N_ST = 4 * len(ST_FIELDS)                                  # 4 cells (near x in-path; index = near * 2 + inpath) x 4 fields\n')
ST_NEW = ('ST_FIELDS = ("n", "x", "n_h0", "x_h0", "v", "nb", "xb", "ne", "xe", "nd", "xd")   # per decision, per cell (see the header)\n'
          'N_ST = 4 * len(ST_FIELDS)                                  # 4 cells (near x in-path; index = near * 2 + inpath) x 11 fields\n'
          'TRK_FIELDS = ("nip_far", "nip_near", "nip_both", "ip_far", "ip_near", "ip_both")   # tracks with a relied-on record\n'
          'N_TRK = len(TRK_FIELDS)\n')
DEC_OLD = 'DEC_FIELDS = ("k", "ob", "infeasible", "lam", "v_now", "v_chosen", "v_log", "ds_plan", "ds_log", "min_gap", "ttc", "n_enf_tracks")\n'
DEC_NEW = ('DEC_FIELDS = ("k", "ob", "infeasible", "lam", "v_now", "v_chosen", "v_log", "ds_plan", "ds_log", "min_gap", "min_gap_ip", "min_gap_nip",\n'
           '              "ttv", "ttv_ip", "ttv_nip", "ttv_enf", "ttc_proxy_v01", "n_enf_tracks")\n'
           'DEC_INT = ("k", "ob", "infeasible", "n_enf_tracks")\n')

SAFETY_OLD = '''def _safety_extras(out, sc, s, gap, cur, ax, half, enf):
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
'''
SAFETY_NEW = '''def ttv_from_pair_gaps(pg16, cols):
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
'''

ARMCOV_DOC_OLD = ('    S\' = R (S_h + sigma_a^2 I) R\' (R = the object\'s axes); a margin <= 1e-3 m is replaced by 1e-3, as deploy_covariance replaces\n'
                  '    a threshold <= 0. axj: (n, 2, 2) object axes; pcov: (n, 3) sxx, sxy, syy; mg2, sd2: (n, 2) margins and sd along the axes."""\n')
ARMCOV_DOC_NEW = ('    S\' = R (S_h + sigma_a^2 I) R\' (R = the object\'s axes); a threshold c_a <= 1e-3 is replaced by 1e-3, exactly as\n'
                  '    deploy_covariance (v02, R15 m6; v01 floored the margin). axj: (n, 2, 2) object axes; pcov: (n, 3) sxx, sxy, syy; mg2, sd2:\n'
                  '    (n, 2) margins and sd along the axes."""\n')
ARMCOV_OLD = '    d = np.maximum(mg2, 1e-3) / (Z * sd2)                            # (n, 2) per-axis scale c_a / z\n'
ARMCOV_NEW = ('    with np.errstate(invalid="ignore", divide="ignore"):         # (n, 2) per-axis scale c_a / z, c_a = margin / sd floored at 1e-3 as\n'
              '        d = np.where(mg2 / sd2 >= 1e-3, mg2 / (Z * sd2), 1e-3 / Z)   # deploy_covariance (v01\'s arithmetic where no floor binds)\n')

DECS_OLD = '''def _new_decs():
    return {f: [] for f in DEC_FIELDS + ("stats",)}


def _push_dec(decs, k, ob, ps):
    lam = LAM_ESTOP if ps["lam"] is None else float(ps["lam"])
    for f, val in (("k", int(k)), ("ob", int(ob)), ("infeasible", int(ps["infeasible"])), ("lam", lam), ("v_now", ps["v_now"]),
                   ("v_chosen", ps["v_chosen"]), ("v_log", ps["v_log"]), ("ds_plan", ps["ds_plan"]), ("ds_log", ps["ds_log"]),
                   ("min_gap", float("nan") if ps["min_gap"] is None else ps["min_gap"]),
                   ("ttc", float("nan") if ps["ttc"] is None else ps["ttc"]), ("n_enf_tracks", int(ps["n_enf_tracks"]))):
        decs[f].append(val)
    decs["stats"].append(list(ps["stats"]))
'''
DECS_NEW = '''def _new_decs():
    return {f: [] for f in DEC_FIELDS + ("stats", "trk")}


def _push_dec(decs, k, ob, ps):
    """Appends one decision (DEC_FIELDS; None -> NaN for the float fields) and its relied-on counts (stats, trk)."""
    fixed = {"k": int(k), "ob": int(ob), "infeasible": int(ps["infeasible"]), "lam": LAM_ESTOP if ps["lam"] is None else float(ps["lam"]),
             "n_enf_tracks": int(ps["n_enf_tracks"])}
    for f in DEC_FIELDS:
        decs[f].append(fixed[f] if f in fixed else (float("nan") if ps[f] is None else float(ps[f])))
    decs["stats"].append(list(ps["stats"]))
    decs["trk"].append(list(ps["trk"]))
'''
SUMM_OLD = ('    none = {"mean_chosen_speed": None, "mean_logged_speed": None, "progress_ratio": None, "backoff_counts": {}, "min_gap_mean": None,\n'
            '            "ttc_mean": None, "share_ttc_lt_2s": None, "divergence_share": None, "anees_relied": None, "p_v_relied": None,\n'
            '            "mean_margin_relied": None, "records_relied": 0}\n')
SUMM_NEW = ('    none = {"mean_chosen_speed": None, "mean_logged_speed": None, "progress_ratio": None, "backoff_counts": {}, "min_gap_mean": None,\n'
            '            "min_gap_ip_mean": None, "ttv_mean": None, "share_ttv_lt_2s": None, "ttc_proxy_v01_mean": None, "divergence_share": None,\n'
            '            "anees_relied": None, "p_v_relied": None, "mean_margin_relied": None, "records_relied": 0}\n')
SUMM2_OLD = ('    mg_, tt = np.array(decs["min_gap"], float), np.array(decs["ttc"], float)\n')
SUMM2_NEW = ('    mg_, tt, mgi = np.array(decs["min_gap"], float), np.array(decs["ttv"], float), np.array(decs["min_gap_ip"], float)\n'
             '    tp = np.array(decs["ttc_proxy_v01"], float)\n')
SUMM3_OLD = ('            "ttc_mean": float(np.nanmean(tt)) if np.isfinite(tt).any() else None,\n'
             '            "share_ttc_lt_2s": float(np.mean(tt[np.isfinite(tt)] < 2.0)) if np.isfinite(tt).any() else None,\n')
SUMM3_NEW = ('            "min_gap_ip_mean": float(np.nanmean(mgi)) if np.isfinite(mgi).any() else None,\n'
             '            "ttv_mean": float(np.nanmean(tt)) if np.isfinite(tt).any() else None,\n'
             '            "share_ttv_lt_2s": float(np.mean(tt[np.isfinite(tt)] < 2.0)) if np.isfinite(tt).any() else None,\n'
             '            "ttc_proxy_v01_mean": float(np.nanmean(tp)) if np.isfinite(tp).any() else None,\n')

INIT_OLD = '           "min_gap": None, "ttc": None, "n_enf_tracks": 0, "stats": [0.0] * N_ST}\n'
INIT_NEW = ('           "min_gap": None, "min_gap_ip": None, "min_gap_nip": None, "ttv": None, "ttv_ip": None, "ttv_nip": None, "ttv_enf": None,\n'
            '           "ttc_proxy_v01": None, "n_enf_tracks": 0, "stats": [0.0] * N_ST, "trk": [0.0] * N_TRK}\n')
CALL_OLD = ('    _safety_extras(out, sc, s, gap, cur, ax, half, enf)\n'
            '    if counts is not None:\n'
            '        enf8 = np.zeros((N_STEP, len(sel)), bool)\n'
            '        enf8[:CC_STEPS] = enf[1::2]\n'
            '        out["stats"] = _record(sc, k, sel, out["choice"], gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf8, ob,\n'
            '                               arm, sd, sc.tr["pred"][sel][:, :, 2:5], cal)\n')
CALL_NEW = ('    _safety_extras(out, sc, s, gap, cur, ax, half, enf, inp_sel)\n'
            '    if counts is not None:\n'
            '        enf8 = np.zeros((N_STEP, len(sel)), bool)\n'
            '        enf8[:CC_STEPS] = enf[1::2]\n'
            '        out["stats"], out["trk"] = _record(sc, k, sel, out["choice"], gap[:, 1::2], sep[:, 1::2], mg, l0, ax, pred_xy, counts, enf8, ob,\n'
            '                                           arm, sd, sc.tr["pred"][sel][:, :, 2:5], cal,\n'
            '                                           0.0 if out["lam"] is None else float(out["lam"]))\n')

REC_DEF_OLD = 'def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob, arm=None, sd=None, pcov=None, cal=None):\n'
REC_DEF_NEW = 'def _record(sc, k, sel, choice, gap, sep, mg, l0, ax, pred_xy, counts, enf, ob, arm=None, sd=None, pcov=None, cal=None, lam_exec=1.0):\n'
REC_DOC_OLD = ('    (near * 2 + inpath) * N_L0 + L0 of the relied-on axis: CAL_FIELDS (see _cal_pairs; the margins along both axes). The counts\n'
               '    dict is filled exactly as in k7_sim_v01."""\n')
REC_DOC_NEW = ('    (near * 2 + inpath) * N_L0 + L0 of the relied-on axis: CAL_FIELDS (see _cal_pairs; the margins along both axes). The counts\n'
               '    dict is filled exactly as in k7_sim_v01.\n'
               '    v02: returns (stats, trk). stats = the N_ST counts (ST_FIELDS per cell, cell-major): v01\'s n, x, n_h0, x_h0, then v (relied\n'
               '    records violated at the plan, D > G), nb / xb (binding: slack G - margin <= BINDING_SLACK), ne / xe (at the executed\n'
               '    margin lam_exec * margin: relied-on axis argmax of G - lam_exec * margin, G > 0, enforced, any satisfaction; exceedance\n'
               '    D > lam_exec * margin), nd / xd (one record per (step, ground-truth instance), the first track in order kept). trk = the\n'
               '    tracks with a relied-on record by TRK_FIELDS (in-path x far only / near only / both)."""\n')
REC_EMPTY_OLD = '    if not hh:\n        return [0.0] * N_ST\n'
REC_EMPTY_NEW = '    if not hh:\n        return [0.0] * N_ST, [0.0] * N_TRK\n'
REC_ST_OLD = '    st = np.zeros((4, len(ST_FIELDS)))\n    rel_ = relied[hh, jj]\n'
REC_ST_NEW = '    st = np.zeros((4, len(ST_FIELDS)))\n    trk = np.zeros(N_TRK)\n    rel_ = relied[hh, jj]\n'
REC_MID_OLD = ('        np.add.at(st[:, 3], c4[f0], exc[f0])\n'
               '        if cal is not None:\n')
REC_MID_NEW = ('        np.add.at(st[:, 3], c4[f0], exc[f0])\n'
               '        # v02 (D14 v04 A1; R15 M6): violation of the relied constraint at the plan (D > G); binding pairs (slack <= 0.5 m)\n'
               '        m_rel, g_rel = mg[j_, h_, a_], G[h_, j_, a_]\n'
               '        np.add.at(st[:, 4], c4, (D > g_rel).astype(float))\n'
               '        bnd = (g_rel - m_rel) <= BINDING_SLACK\n'
               '        np.add.at(st[:, 5], c4[bnd], 1.0)\n'
               '        np.add.at(st[:, 6], c4[bnd], exc[bnd])\n'
               '        # A14 (R15 m7): one record per (step, ground-truth instance), the first track in order kept\n'
               '        keep = np.zeros(len(h_), bool)\n'
               '        seen = set()\n'
               '        for i_, key_ in enumerate(zip(h_.tolist(), inst[j_].tolist())):\n'
               '            if key_ not in seen:\n'
               '                seen.add(key_)\n'
               '                keep[i_] = True\n'
               '        np.add.at(st[:, 9], c4[keep], 1.0)\n'
               '        np.add.at(st[:, 10], c4[keep], exc[keep])\n'
               '        # the tracks with a relied-on record by in-path x (far only, near only, both): the V2 reference 1 - (1 - delta)^n_tracks\n'
               '        near_ = pg[ok] <= GAP_BINS[1]\n'
               '        for jv in np.unique(j_).tolist():\n'
               '            mj = j_ == jv\n'
               '            nr, fr = bool(near_[mj].any()), bool((~near_[mj]).any())\n'
               '            trk[3 * int(inpath[jv]) + (2 if (nr and fr) else (1 if nr else 0))] += 1.0\n'
               '        if cal is not None:\n')
REC_END_OLD = '    return st.ravel().tolist()\n\n\ndef decode_cell(cell):\n'
REC_END_NEW = ('    # v02 (R15 m9): the executed margin lam_exec * margin (lam_exec = 0 for the emergency stop), SD3-style: the relied-on axis at\n'
               '    # that margin, separating, enforced, any satisfaction; exceedance D > lam_exec * margin. At lam_exec = 1 (a feasible\n'
               '    # decision) every enforced pair is satisfied, so ne / xe equal n / x.\n'
               '    mg_e = lam_exec * mg\n'
               '    rel_e = np.argmax(G - mg_e.transpose(1, 0, 2), axis=-1)[hh, jj]\n'
               '    oke = (G[hh, jj, rel_e] > 0) & enf[hh, jj]\n'
               '    if oke.any():\n'
               '        h_, j_, e_, a_ = hh[oke], jj[oke], e[oke], rel_e[oke]\n'
               '        De = np.sign(S[h_, j_, a_]) * np.sum(ax[j_, a_] * e_, -1)\n'
               '        c4e = (pg[oke] <= GAP_BINS[1]).astype(int) * 2 + inpath[j_].astype(int)\n'
               '        np.add.at(st[:, 7], c4e, 1.0)\n'
               '        np.add.at(st[:, 8], c4e, (De > mg_e[j_, h_, a_]).astype(float))\n'
               '    return st.ravel().tolist(), trk.tolist()\n'
               '\n\ndef decode_cell(cell):\n')

rep = [(HEADER_OLD, HEADER_NEW), (GRID_OLD, GRID_NEW), (TTC_OLD, TTC_NEW), (ST_OLD, ST_NEW), (DEC_OLD, DEC_NEW), (SAFETY_OLD, SAFETY_NEW),
       (ARMCOV_DOC_OLD, ARMCOV_DOC_NEW), (ARMCOV_OLD, ARMCOV_NEW), (DECS_OLD, DECS_NEW), (SUMM_OLD, SUMM_NEW), (SUMM2_OLD, SUMM2_NEW),
       (SUMM3_OLD, SUMM3_NEW), (INIT_OLD, INIT_NEW), (CALL_OLD, CALL_NEW), (REC_DEF_OLD, REC_DEF_NEW), (REC_DOC_OLD, REC_DOC_NEW),
       (REC_EMPTY_OLD, REC_EMPTY_NEW), (REC_ST_OLD, REC_ST_NEW), (REC_MID_OLD, REC_MID_NEW), (REC_END_OLD, REC_END_NEW)]
for a, b in rep:
    assert s.count(a) == 1, "anchor not found exactly once: " + a[:80]
    s = s.replace(a, b, 1)
open(os.path.join(K8, "k8_sim_v02.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k8_sim_v02.py written")
