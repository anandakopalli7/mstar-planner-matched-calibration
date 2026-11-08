"""C1 (Argoverse 2 confirmation): operating characteristics of H1 and H2 by resampling the 840-scene nuScenes K8
development data, rescaled to AV2's layout. v02 (2 Nov 2026). v01 (c1_power_counts_v01.py) is kept and unchanged.

Companion of 40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v02_DRAFT.md, section 6.

OUTCOME-BLIND (D15 section 4; D16 v04 Choice 13). The only AV2 input is the stage-A counts file
60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v02.json (items, logs and decisions per population and cell; its item error fields
are NaN by construction and this script never opens the items). Everything else is nuScenes development data (D16 Rule 0):
the Linux replicate of the K8 exploratory run
(70_TESTS/k8_expl_v02_linux/, decide mode) and its v03 analysis (70_TESTS/k8_expl_v02_linux_analysis_v03/), confirmed by
the independent review R16 (70_TESTS/R16_K8_RESULTS_REVIEW_v01.md). No AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected
error is computed or read.

What is simulated. One synthetic AV2 dataset = 150 units (AV2 logs). Each unit is a nuScenes development scene drawn with
replacement (an AV2 log lasts 15.5 to 20 s, about one nuScenes scene). The draw keeps, per scene, every arm's per-cell record
and exceedance counts on PD7, SD1_7 and PD and every arm's per-decision infeasibility flags, so the correlation between arms
and between cells is the real one. Decisions are thinned to AV2's decisions per log. In the layout-matched schemes each
population's cells are thinned to AV2's layout from counts v02: a cell is removed from a unit with the probability that
makes its share of units equal AV2's share of logs holding it, and its records are thinned to AV2's records per log holding
it (both capped at 1: a cell richer on AV2 is left as on nuScenes). On each dataset the coded K8 validity rule (k8_analyse_v03.hk1_rule and form_valid, via
k6_analyse_v02.rates / flag) is applied to M* and every Form B comparator, with a log bootstrap of B_OC weights, and
Forms A, B (D16 v04 Choice 9 reading) and C are evaluated. The power-qualified family (floor) uses a normal approximation
of k6_analyse_v02.power_family (validated against the analysis on the full data, section "validation").

Usage: python -B c1_power_counts_v02.py <out.json> [reps]
"""
import hashlib
import json
import math
import os
import sys
import time
import warnings

import numpy as np
from scipy import stats

W_ROOT = r'C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911'
sys.path.insert(0, os.path.join(W_ROOT, '50_CODE', 'k6'))
sys.path.insert(0, os.path.join(W_ROOT, '50_CODE', 'm'))
sys.path.insert(0, os.path.join(W_ROOT, '50_CODE', 'c1_av2'))
import k6_analyse_v02 as A  # noqa: E402

COUNTS2 = os.path.join(W_ROOT, '60_RESULTS', 'av2_trk', 'AV2_TRACKER_COUNTS_v02.json')
AV2_RUN = {'t1': 't1_lt3d', 't3': 't3_lt3d'}       # primary detector (D16 Choice 5)
POP_AV2 = {'PD7_primary': 'PD7', 'SD1_7_gap_le_5m': 'SD1_7', 'PD_inpath': 'PD'}
AV2_LOGS = 150
RUNS = os.path.join(W_ROOT, '70_TESTS', 'k8_expl_v02_linux')
ANALYSIS = os.path.join(W_ROOT, '70_TESTS', 'k8_expl_v02_linux_analysis_v03', 'k8_exploratory_analysis_v03.json')
MANIFESTS = [os.path.join(W_ROOT, '30_DATA', 'k6', 'cache_v02_t1_train', 'MANIFEST.json'),
             os.path.join(W_ROOT, '30_DATA', 'k6', 'cache_v02_t1_val', 'MANIFEST.json')]
SEED = 20261103
DELTA = 0.05
B_OC = 200                 # bootstrap weights per synthetic dataset (the run uses 2000)
B_VAL = 500                # bootstrap weights for the full-data validation
MIN_UNITS = 39             # evaluable: >= 39 scenes from >= 8 logs; on AV2 a log is a scene
F_MIN = 6
POWER_P, POWER_RHO, POWER_MIN = 0.15, 0.5, 0.80
CONF_POPS = ('PD7_primary', 'SD1_7_gap_le_5m', 'PD_inpath')
FLOOR_POPS = ('PD7_primary', 'SD1_7_gap_le_5m')
POP_SPEC = {   # k8_analyse_v03.POP_DECIDE
    'PD7_primary': dict(offset=(0,), inpath=(0, 1), gap=(0, 1, 2), steps=A.STEPS_CC),
    'PD_inpath': dict(offset=(0,), inpath=(1,), gap=(0, 1, 2), steps=A.STEPS_CC),
    'SD1_7_gap_le_5m': dict(offset=(0,), inpath=(0, 1), gap=(0, 1), steps=A.STEPS_CC),
}
ARMS = ['Mstar', 'B0', 'B1', 'B3', 'B4', 'B6', 'B9', 'RETUNED']
COMPS_B = ['B0', 'B1', 'B3', 'B4', 'B6', 'B9', 'RETUNED']     # D16 Choice 12: never changed
COMPS_A = ['B0', 'B1', 'B4', 'B9']
HOLM_WORST = 0.05 / 5                                         # family S: H2, H4, H5, H6b, H10
NI_B6 = 0.03                                                  # H10 non-inferiority margin (the Form C floor)
KAPPAS = (1.0, 0.5, 0.25)                                     # B6 excess over M* scaled by kappa (stress)
DEV_SCENES = set(A.DEV_SCENES)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def c_rule(price):
    return max(0.03, math.ceil(round(price * 100, 9)) / 100 + 0.01)


# ------------------------------------------------------------------ data
_MASKS = {}


def load_tracker(tag, arm_of_scene):
    eps = []
    with open(os.path.join(RUNS, 'episodes_%s_decide.jsonl' % tag)) as f:
        for line in f:
            o = json.loads(line)
            if o.get('entered') and o['scene'] not in DEV_SCENES and o['arm'] != 'LOG':
                eps.append((o['episode'], o['arm'], o['scene']))
    scenes = sorted({s for _, _, s in eps})
    sidx = {s: i for i, s in enumerate(scenes)}
    src_arms = sorted(set(ARMS[:-1]) | set(arm_of_scene.values()))
    aidx = {a: i for i, a in enumerate(src_arms)}
    max_ep = max(e for e, _, _ in eps) + 1
    ep_arm = np.full(max_ep, -1, np.int64)
    ep_scene = np.full(max_ep, -1, np.int64)
    for e, a, s in eps:
        if a in aidx:
            ep_arm[e], ep_scene[e] = aidx[a], sidx[s]
    cells = A.cell_family()
    l0_to_cell = np.full(A.S.N_L0, -1)
    for j, (_, ids) in enumerate(cells):
        l0_to_cell[ids] = j
    z = np.load(os.path.join(RUNS, 'counts_%s_decide.npz' % tag))
    ep, cell = z['episode'], z['cell']
    n, x = z['n'], z['exceed']
    ok = (ep < max_ep)
    ep, cell, n, x = ep[ok], cell[ok], n[ok], x[ok]
    ar = ep_arm[ep]
    keep = ar >= 0
    ep, cell, n, x, ar = ep[keep], cell[keep], n[keep], x[keep], ar[keep]
    sc = ep_scene[ep]
    col = l0_to_cell[cell % A.S.N_L0]
    T = {}
    for p in CONF_POPS:
        if p not in _MASKS:
            _MASKS[p] = A.mask(**POP_SPEC[p])
        pm = _MASKS[p][cell] & (col >= 0)
        N = np.zeros((len(src_arms), len(scenes), len(cells)))
        X = np.zeros_like(N)
        np.add.at(N, (ar[pm], sc[pm], col[pm]), n[pm])
        np.add.at(X, (ar[pm], sc[pm], col[pm]), x[pm])
        T[p] = (N, X)
    del z, ep, cell, n, x, ar, sc, col
    # per arm (ARMS order) tables, RETUNED composed per scene from its fold's selected arm
    tab = {}
    ret_idx = np.array([aidx[arm_of_scene[s]] for s in scenes])
    for p in CONF_POPS:
        N, X = T[p]
        Na = np.zeros((len(ARMS), len(scenes), len(cells)))
        Xa = np.zeros_like(Na)
        for i, a in enumerate(ARMS[:-1]):
            Na[i], Xa[i] = N[aidx[a]], X[aidx[a]]
        Na[-1] = N[ret_idx, np.arange(len(scenes))]
        Xa[-1] = X[ret_idx, np.arange(len(scenes))]
        tab[p] = (Na, Xa)
    # per-decision infeasibility, aligned by keyframe across arms
    zd = np.load(os.path.join(RUNS, 'decisions_%s_decide.npz' % tag))
    dep, dk, dinf = zd['episode'], zd['k'], zd['infeasible']
    ep_of = {}
    for e, a, s in eps:
        ep_of[(a, s)] = e
    order = np.argsort(dep, kind='stable')
    dep_s, dk_s, dinf_s = dep[order], dk[order], dinf[order]
    starts = np.searchsorted(dep_s, np.arange(max_ep))
    ends = np.searchsorted(dep_s, np.arange(max_ep), side='right')
    F = []
    for s in scenes:
        cols, ks = [], None
        for a in ARMS:
            src = arm_of_scene[s] if a == 'RETUNED' else a
            e = ep_of[(src, s)]
            kk = dk_s[starts[e]:ends[e]]
            o = np.argsort(kk)
            if ks is None:
                ks = kk[o]
            else:
                assert np.array_equal(ks, kk[o]), 'decision states differ between arms in %s' % s
            cols.append(dinf_s[starts[e]:ends[e]][o].astype(np.int8))
        F.append(np.stack(cols, 1))
    del zd, dep, dk, dinf
    return scenes, tab, F


def log_map(scenes):
    log_of_scene = {}
    for p in MANIFESTS:
        m = json.load(open(p))
        for s, v in m['scenes'].items():
            log_of_scene[s] = v['log']
    logs = sorted({log_of_scene[s] for s in scenes})
    return np.array([logs.index(log_of_scene[s]) for s in scenes]), logs


# ------------------------------------------------------------------ the coded rule (validity) with an analytic floor
def power_family_analytic(N, ev):
    """Normal approximation of k6_analyse_v02.power_family: per evaluable cell, the scene-mean estimate under a
    beta-binomial with mean 0.15 and intra-scene correlation 0.5, flagged at the Sidak critical value of the evaluable
    family (the coded rule draws independent cells, so its sup-t quantile is close to Sidak)."""
    fam = np.flatnonzero(ev)
    qual = np.zeros(N.shape[1], bool)
    if not len(fam):
        return qual
    q = stats.norm.ppf(0.95 ** (1.0 / len(fam)))
    Nf = N[:, fam]
    pres = Nf > 0
    S = pres.sum(0)
    v = np.where(pres, POWER_P * (1 - POWER_P) * (POWER_RHO + (1 - POWER_RHO) / np.where(pres, Nf, 1.0)), 0.0).sum(0) / S ** 2
    pw = stats.norm.cdf((POWER_P - DELTA) / np.sqrt(v) - q)
    qual[fam] = pw >= POWER_MIN
    return qual


def validity(T, W, ev_fn):
    """Returns (strict, shown_invalid, detail). strict = k8_analyse_v03.form_valid (HK1 and HK1c on PD7, SD1_7, PD).
    shown_invalid = a flagged cell (all-evaluable or power-qualified family), a flagged pooled cell, or HK1c failed:
    positive evidence of invalidity. A floor-only failure is strict = False and shown_invalid = False (Choice 9)."""
    U = W.shape[1]
    one = np.ones((1, U))
    strict, shown, nofloor = True, False, True
    det = {}
    for p in CONF_POPS:
        N, X = T[p]
        ev = ev_fn(N)
        fam = np.flatnonzero(ev)
        est, boot = A.rates(N, X, one)[0], A.rates(N, X, W)
        nfl = 0
        sig = np.zeros(0, bool)
        if len(fam):
            _, _, _, sig, _ = A.flag(est, boot, fam, 0.95)
            nfl = int(sig.sum())
        Np, Xp = N.sum(1, keepdims=True), X.sum(1, keepdims=True)
        evp = bool(ev_fn(Np)[0])
        pfl, hk1c = False, False
        if evp:
            e1, b1 = A.rates(Np, Xp, one)[0], A.rates(Np, Xp, W)
            _, ubp, _, sigp, _ = A.flag(e1, b1, np.array([0]), 0.95)
            pfl, hk1c = bool(sigp[0]), bool(ubp[0] <= DELTA + 0.03)
        fq = np.flatnonzero(power_family_analytic(N, ev))
        ffl = 0
        if len(fq):
            _, _, _, sigf, _ = A.flag(est, boot, fq, 0.95)
            ffl = int(sigf.sum())
        floor_ok = (len(fq) >= F_MIN) if p in FLOOR_POPS else True
        a_ok = nfl == 0 and len(fam) >= 1 and floor_ok and ffl == 0
        strict &= a_ok and evp and not pfl and hk1c
        nofloor &= nfl == 0 and len(fam) >= 1 and ffl == 0 and evp and not pfl and hk1c   # diagnostic only
        shown |= nfl > 0 or ffl > 0 or pfl or (evp and not hk1c)
        det[p] = {'evaluable': int(len(fam)), 'flagged': nfl, 'family': int(len(fq)), 'family_flagged': ffl,
                  'pooled_flagged': pfl, 'hk1c': hk1c, 'floor_ok': bool(floor_ok),
                  '_cells': (est, boot, fam, sig)}
    det['_nofloor'] = bool(nofloor)
    return bool(strict), bool(shown), det


def ablation_fails(det_b6, det_m):
    """M-PLAN section 7 'a baseline fails', on PD7: B6 flagged in a cell (its all-evaluable sup-t), M* not flagged there,
    and the paired difference B6 - M* has a simultaneous lower bound > 0 over the cells evaluable for both."""
    e6, b6, f6, s6 = det_b6['PD7_primary']['_cells']
    em, bm, fm, sm = det_m['PD7_primary']['_cells']
    if not len(f6):
        return False
    flag6 = np.zeros(len(e6), bool)
    flag6[f6] = s6
    flagm = np.zeros(len(em), bool)
    flagm[fm] = sm
    both = np.intersect1d(f6, fm)
    if not len(both):
        return False
    d = e6[both] - em[both]
    db = b6[:, both] - bm[:, both]
    lb, se, q, ok = A.M._simul(d, db, 0.95, 'lower')
    pos = (ok & (lb > 0)) | (~ok & (d > 0))
    return bool(np.any(flag6[both] & ~flagm[both] & pos))


def forms(f, W, strict, shown, c_val):
    """f: (U, arms) per-unit infeasible rates in ARMS order. Percentile log-bootstrap bounds as k8_analyse_v03.d14_forms."""
    wsum = W.sum(1)

    def ub(b, level):
        d = f[:, 0] - f[:, ARMS.index(b)]
        return float(d.mean()), float(np.quantile((W @ d) / wsum, level))
    V9 = [c for c in COMPS_B if not shown[c]]                       # Choice 9: floor-only failures stay in
    lvl = 1 - 0.05 / max(len(V9), 1)
    beats9 = {c: ub(c, lvl)[1] < 0 for c in V9}
    formB9 = strict['Mstar'] and all(beats9.values())
    Vlit = [c for c in COMPS_B if strict[c]]                         # literal D14 reading (k8_analyse_v03)
    lvl2 = 1 - 0.05 / max(len(Vlit), 1)
    formBlit = strict['Mstar'] and all(ub(c, lvl2)[1] < 0 for c in Vlit)
    formA = strict['Mstar'] and all(ub(c, 1 - 0.05 / 4)[1] < 0 for c in COMPS_A)
    d4 = ub('B4', 0.95)
    formC = d4[1] <= c_val
    formC_holm = ub('B4', 1 - HOLM_WORST)[1] <= c_val
    d6 = ub('B6', 0.95)
    return {'formB': bool(formB9), 'formB_literal': bool(formBlit), 'formA': bool(formA), 'formC': bool(formC),
            'formC_holm_worst': bool(formC_holm), 'V': V9, 'beats': beats9, 'Mstar_minus_B4': d4[0],
            'Mstar_minus_B6': d6[0], 'ni_B6_005': bool(d6[1] <= NI_B6), 'ni_B6_holm': bool(ub('B6', 1 - HOLM_WORST)[1] <= NI_B6)}


# ------------------------------------------------------------------ validation on the full development data
def validate(tag, scenes, tab, F, dev, rng):
    log_idx, logs = log_map(scenes)
    Wl = rng.multinomial(len(logs), np.full(len(logs), 1.0 / len(logs)), size=B_VAL).astype(float)
    W = Wl[:, log_idx]
    scene_arr = np.array(scenes)

    def ev_fn(N):
        return A.evaluable(N, scene_arr, log_idx)
    strict, shown, det = {}, {}, {}
    for i, a in enumerate(ARMS):
        T = {p: (tab[p][0][i], tab[p][1][i]) for p in CONF_POPS}
        strict[a], shown[a], det[a] = validity(T, W, ev_fn)
    f = np.stack([Fs.mean(0) for Fs in F], 0)
    fr = forms(f, W, strict, shown, dev['c'])
    agree = {}
    for a in ARMS:
        va = dev['validity'][a]
        agree[a] = {'strict_here': strict[a], 'valid_form_B_analysis': va['valid_form_B'], 'shown_invalid_here': shown[a],
                    'family_here': {p: det[a][p]['family'] for p in CONF_POPS},
                    'family_analysis': {p: va['pops'][p]['family_size'] for p in CONF_POPS},
                    'flagged_here': {p: det[a][p]['flagged'] for p in CONF_POPS},
                    'flagged_analysis': {p: len(va['pops'][p]['flagged']) for p in CONF_POPS}}
    return {'logs': len(logs), 'scenes': len(scenes), 'B': B_VAL, 'by_arm': agree,
            'infeasible_rate_here': {a: float(f[:, i].mean()) for i, a in enumerate(ARMS)},
            'forms_here': {k: v for k, v in fr.items() if k not in ('beats',)},
            'all_strict_verdicts_agree': all(agree[a]['strict_here'] == agree[a]['valid_form_B_analysis'] for a in ARMS)}


# ------------------------------------------------------------------ resampling to AV2
def draw_units(rng, scheme, n_units, n_scenes, log_idx):
    if scheme == 'scene':
        return rng.integers(0, n_scenes, n_units)
    logs = np.unique(log_idx)
    by_log = {l: np.flatnonzero(log_idx == l) for l in logs}
    out = []
    while len(out) < n_units:
        out.extend(by_log[rng.choice(logs)].tolist())
    return np.array(out[:n_units])


def layout_match(tab, av2_run, n_scenes):
    """Per population and cell, from M*'s nuScenes table and the AV2 stage-A counts (counts v02):
    q = presence ratio (AV2 share of logs holding the cell / nuScenes share of scenes holding it), capped at 1;
    r = records per present unit ratio (AV2 items per log holding the cell / nuScenes records per scene holding it), capped at 1.
    The uncapped ratios are reported. A cell absent on nuScenes stays absent."""
    cells = [c for c, _ in A.cell_family()]
    out = {}
    for p in CONF_POPS:
        N = tab[p][0][0]
        S = (N > 0).sum(0)
        R = N.sum(0)
        bc = av2_run['by_population'][POP_AV2[p]]['by_cell']
        q = np.zeros(len(cells))
        r = np.zeros(len(cells))
        rows = {}
        for j, c in enumerate(cells):
            a = bc.get(c, {'items': 0, 'logs': 0})
            if S[j] == 0 or a['logs'] == 0:
                rows[c] = {'av2_logs': a['logs'], 'av2_items': a['items'], 'nus_scenes': int(S[j]), 'q': 0.0, 'r': 0.0}
                continue
            q_raw = (a['logs'] / AV2_LOGS) / (S[j] / n_scenes)
            r_raw = (a['items'] / a['logs']) / (R[j] / S[j])
            q[j], r[j] = min(1.0, q_raw), min(1.0, r_raw)
            rows[c] = {'av2_logs': a['logs'], 'av2_items': a['items'], 'nus_scenes': int(S[j]), 'nus_records': float(R[j]),
                       'q_raw': q_raw, 'r_raw': r_raw}
        out[p] = {'q': q, 'r': r, 'rows': rows}
    return out


def synth(rng, idx, tab, F, lay, theta_d, kappa=1.0):
    T = {}
    for p in CONF_POPS:
        N, X = tab[p]
        Ns, Xs = N[:, idx, :], X[:, idx, :]
        if lay is not None:
            keep = (rng.random((len(idx), Ns.shape[2])) < lay[p]['q'][None, :]).astype(float)[None, :, :]   # shared by arms
            r = np.broadcast_to(lay[p]['r'][None, None, :], Ns.shape)
            Xt = rng.binomial((Xs * keep).astype(np.int64), r).astype(float)
            Nt = Xt + rng.binomial(((Ns - Xs) * keep).astype(np.int64), r)
        else:
            Xt, Nt = Xs, Ns
        if kappa != 1.0:   # stress: B6's excess over M* scaled by kappa, per unit and cell (motion effect attenuated)
            i6, i0 = ARMS.index('B6'), 0
            N6, X6, N0, X0 = Nt[i6], Xt[i6], Nt[i0], Xt[i0]
            r6 = np.divide(X6, N6, out=np.zeros_like(X6), where=N6 > 0)
            r0 = np.divide(X0, N0, out=np.zeros_like(X0), where=N0 > 0)
            rb = np.clip(np.where(N0 > 0, r0 + kappa * (r6 - r0), r6), 0.0, 1.0)
            Xt = Xt.copy()
            Xt[i6] = rng.binomial(N6.astype(np.int64), rb).astype(float)
        T[p] = (Nt, Xt)
    f = np.empty((len(idx), len(ARMS)))
    for u, s in enumerate(idx):
        Fs = F[s]
        if theta_d < 1:
            keep = rng.random(Fs.shape[0]) < theta_d
            if not keep.any():
                keep[rng.integers(Fs.shape[0])] = True
            Fs = Fs[keep]
        f[u] = Fs.mean(0)
    return T, f


def run_oc(trk, scheme, matched, theta_d, reps, rng, n_units, kappa=1.0):
    agg = {t: {'formB': 0, 'formB_literal': 0, 'formA': 0, 'formC': 0, 'formC_holm_worst': 0, 'formB_nofloor': 0,
               'Mstar_nofloor_valid': 0, 'H10_ablation_fails': 0, 'H10_ni_005': 0, 'H10_ni_holm': 0, 'H10': 0, 'H10_holm': 0,
               'strict': {a: 0 for a in ARMS}, 'shown_invalid': {a: 0 for a in ARMS}, 'in_V': {a: 0 for a in COMPS_B},
               'beats_given_in_V': {a: [0, 0] for a in COMPS_B},
               'Mstar_fail': {'cell_flag': 0, 'floor': 0, 'family_flag': 0, 'pooled': 0, 'hk1c': 0},
               'family_size_Mstar': {p: [] for p in CONF_POPS}, 'evaluable_Mstar': {p: [] for p in CONF_POPS},
               'formB_fail_only_B6': 0, 'price': [], 'price_B6': []} for t in trk}
    agg['H1'] = 0
    agg['H1_nofloor'] = 0
    agg['H2'] = 0
    agg['H2_holm_worst'] = 0
    agg['H10'] = 0
    agg['H10_holm'] = 0
    n_sc = len(trk['t1']['scenes'])
    log_idx = trk['t1']['log_idx']

    def ev_fn(N):
        return (N > 0).sum(0) >= MIN_UNITS
    for r in range(reps):
        idx = draw_units(rng, scheme, n_units, n_sc, log_idx)
        W = rng.multinomial(n_units, np.full(n_units, 1.0 / n_units), size=B_OC).astype(float)
        res = {}
        for t in ('t1', 't3'):
            d = trk[t]
            T, f = synth(rng, idx, d['tab'], d['F'], d['lay'] if matched else None, theta_d, kappa)
            strict, shown, dets = {}, {}, {}
            for i, a in enumerate(ARMS):
                Ti = {p: (T[p][0][i], T[p][1][i]) for p in CONF_POPS}
                strict[a], shown[a], det = validity(Ti, W, ev_fn)
                dets[a] = det
                g = agg[t]
                g['strict'][a] += strict[a]
                g['shown_invalid'][a] += shown[a]
                if a == 'Mstar':
                    for p in CONF_POPS:
                        g['family_size_Mstar'][p].append(det[p]['family'])
                        g['evaluable_Mstar'][p].append(det[p]['evaluable'])
                    if any(det[p]['flagged'] for p in CONF_POPS):
                        g['Mstar_fail']['cell_flag'] += 1
                    if not all(det[p]['floor_ok'] for p in CONF_POPS):
                        g['Mstar_fail']['floor'] += 1
                    if any(det[p]['family_flagged'] for p in CONF_POPS):
                        g['Mstar_fail']['family_flag'] += 1
                    if any(det[p]['pooled_flagged'] for p in CONF_POPS):
                        g['Mstar_fail']['pooled'] += 1
                    if not all(det[p]['hk1c'] for p in CONF_POPS):
                        g['Mstar_fail']['hk1c'] += 1
            fr = forms(f, W, strict, shown, d['c'])
            g = agg[t]
            for k in ('formB', 'formB_literal', 'formA', 'formC', 'formC_holm_worst'):
                g[k] += fr[k]
            for c in fr['V']:
                g['in_V'][c] += 1
                g['beats_given_in_V'][c][0] += fr['beats'][c]
                g['beats_given_in_V'][c][1] += 1
            failing = [c for c in fr['V'] if not fr['beats'][c]]
            nof = dets['Mstar']['_nofloor']
            fr['formB_nofloor'] = bool(nof and not failing)
            g['Mstar_nofloor_valid'] += nof
            g['formB_nofloor'] += fr['formB_nofloor']
            if nof and failing == ['B6']:
                g['formB_fail_only_B6'] += 1
            abl = ablation_fails(dets['B6'], dets['Mstar'])
            fr['H10'] = bool(abl and fr['ni_B6_005'])
            fr['H10_holm'] = bool(abl and fr['ni_B6_holm'])
            g['H10_ablation_fails'] += abl
            g['H10_ni_005'] += fr['ni_B6_005']
            g['H10_ni_holm'] += fr['ni_B6_holm']
            g['H10'] += fr['H10']
            g['H10_holm'] += fr['H10_holm']
            g['price'].append(fr['Mstar_minus_B4'])
            g['price_B6'].append(fr['Mstar_minus_B6'])
            res[t] = fr
        agg['H1'] += res['t1']['formB'] and res['t3']['formB']
        agg['H1_nofloor'] += res['t1']['formB_nofloor'] and res['t3']['formB_nofloor']
        agg['H2'] += res['t1']['formC'] and res['t3']['formC']
        agg['H2_holm_worst'] += res['t1']['formC_holm_worst'] and res['t3']['formC_holm_worst']
        agg['H10'] += res['t1']['H10'] and res['t3']['H10']
        agg['H10_holm'] += res['t1']['H10_holm'] and res['t3']['H10_holm']
    out = {'scheme': scheme, 'layout_matched_to_av2_counts_v02': matched, 'kappa_B6_excess': kappa, 'theta_decisions': theta_d,
           'units': n_units, 'reps': reps, 'B_OC': B_OC, 'P_H1': agg['H1'] / reps,
           'P_H1_without_floors_diagnostic': agg['H1_nofloor'] / reps,
           'P_H2': agg['H2'] / reps, 'P_H2_holm_worst': agg['H2_holm_worst'] / reps,
           'P_H10': agg['H10'] / reps, 'P_H10_holm_worst': agg['H10_holm'] / reps}
    for t in ('t1', 't3'):
        g = agg[t]
        out[t] = {
            'P_formB_without_floors_diagnostic': g['formB_nofloor'] / reps,
            'P_Mstar_valid_without_floors': g['Mstar_nofloor_valid'] / reps,
            'P_H10_ablation_fails': g['H10_ablation_fails'] / reps, 'P_H10_ni_0.05': g['H10_ni_005'] / reps,
            'P_H10_ni_holm_worst': g['H10_ni_holm'] / reps, 'P_H10': g['H10'] / reps, 'P_H10_holm_worst': g['H10_holm'] / reps,
            'Mstar_minus_B6_mean_over_datasets': float(np.mean(g['price_B6'])),
            'Mstar_minus_B6_sd_over_datasets': float(np.std(g['price_B6'], ddof=1)),
            'P_formB': g['formB'] / reps, 'P_formB_literal_D14': g['formB_literal'] / reps, 'P_formA': g['formA'] / reps,
            'P_formC': g['formC'] / reps, 'P_formC_holm_worst': g['formC_holm_worst'] / reps,
            'P_strict_valid': {a: g['strict'][a] / reps for a in ARMS},
            'P_shown_invalid': {a: g['shown_invalid'][a] / reps for a in ARMS},
            'P_in_V_choice9': {a: g['in_V'][a] / reps for a in COMPS_B},
            'P_beats_given_in_V': {a: (g['beats_given_in_V'][a][0] / g['beats_given_in_V'][a][1]
                                       if g['beats_given_in_V'][a][1] else None) for a in COMPS_B},
            'P_Mstar_failure_reason': {k: v / reps for k, v in g['Mstar_fail'].items()},
            'Mstar_family_size_median': {p: float(np.median(g['family_size_Mstar'][p])) for p in CONF_POPS},
            'Mstar_family_size_p10': {p: float(np.quantile(g['family_size_Mstar'][p], 0.1)) for p in CONF_POPS},
            'Mstar_evaluable_median': {p: float(np.median(g['evaluable_Mstar'][p])) for p in CONF_POPS},
            'P_formB_fails_only_on_B6': g['formB_fail_only_B6'] / reps,
            'Mstar_minus_B4_mean_over_datasets': float(np.mean(g['price'])),
            'Mstar_minus_B4_sd_over_datasets': float(np.std(g['price'], ddof=1)),
        }
    return out


def av2_floor_direct(c2):
    """The power-qualified family from the AV2 stage-A counts alone, by the analytic rule of power_family_analytic, with
    each cell's items spread equally over its logs. The coded rule uses the arm's own records; M*'s relied records equal the
    arm-independent ref_relied items to 99.7 % on nuScenes (K7 v02 section 3), so this predicts M*'s floors on AV2."""
    out = {}
    for run, r in c2['runs'].items():
        out[run] = {}
        for p, pa in POP_AV2.items():
            bc = r['by_population'][pa]['by_cell']
            ev = [(c, v) for c, v in bc.items() if v['logs'] >= MIN_UNITS]
            k = len(ev)
            if not k:
                out[run][p] = {'evaluable': 0, 'family': 0}
                continue
            q = stats.norm.ppf(0.95 ** (1.0 / k))
            fam = []
            pw_by = {}
            for c, v in ev:
                S, n = v['logs'], v['items'] / v['logs']
                se = math.sqrt(POWER_P * (1 - POWER_P) * (POWER_RHO + (1 - POWER_RHO) / n) / S)
                pw = float(stats.norm.cdf((POWER_P - DELTA) / se - q))
                pw_by[c] = {'logs': S, 'power': pw}
                if pw >= POWER_MIN:
                    fam.append(c)
            out[run][p] = {'evaluable': k, 'q_sidak': float(q), 'family': len(fam), 'family_cells': fam,
                           'floor_met': (len(fam) >= F_MIN) if p in FLOOR_POPS else None, 'power_by_cell': pw_by}
    return out


def floor_rule_check(trk, theta_d, rng, n_units, n_sets=3):
    """The coded k6_analyse_v02.power_family (200 simulated datasets, beta-binomial 0.5) against power_family_analytic,
    on M*'s tables of a few layout-matched synthetic AV2 datasets."""
    out = []
    for _ in range(n_sets):
        idx = draw_units(rng, 'scene', n_units, len(trk['t1']['scenes']), trk['t1']['log_idx'])
        W = rng.multinomial(n_units, np.full(n_units, 1.0 / n_units), size=B_OC).astype(float)
        for t in ('t1', 't3'):
            d = trk[t]
            T, _ = synth(rng, idx, d['tab'], d['F'], d['lay'], theta_d)
            row = {'tracker': t}
            for p in CONF_POPS:
                N = T[p][0][0]
                ev = (N > 0).sum(0) >= MIN_UNITS
                pw, _ = A.power_family(N, ev, np.arange(n_units), W, np.random.default_rng([20261111, len(out)]))
                row[p] = {'evaluable': int(ev.sum()), 'family_coded': int((ev & (pw >= POWER_MIN)).sum()),
                          'family_analytic': int(power_family_analytic(N, ev).sum())}
            out.append(row)
    return out


def dev_summary(an, tag):
    t = an['decide'][tag]
    va = {a: t['validity_by_arm'][a] for a in ARMS}
    out = {'infeasible_rate': {a: t['infeasible_rate'][a]['mean'] for a in ARMS},
           'validity': {a: {'valid_form_B': va[a]['valid_form_B'], 'HK1': va[a]['HK1'], 'HK1c_all_pops': va[a]['HK1c_all_pops'],
                            'pops': {p: {'evaluable': va[a]['pops'][p]['evaluable'], 'flagged': va[a]['pops'][p]['flagged'],
                                         'family_size': va[a]['pops'][p]['family_size'],
                                         'family_flagged': va[a]['pops'][p]['family_flagged'],
                                         'pooled_E': va[a]['pops'][p]['pooled']['E'], 'pooled_ub': va[a]['pops'][p]['pooled']['ub'],
                                         'pooled_flagged': va[a]['pops'][p]['pooled']['flagged']} for p in CONF_POPS}}
                        for a in ARMS},
           'forms': {'A_met': t['d14_forms']['A_K6_form']['met'], 'B_met': t['d14_forms']['B_literature_form']['met'],
                     'B_passing': t['d14_forms']['B_literature_form']['comparators_passing_validity'],
                     'C': t['d14_forms']['C_B_plus_price_bound']}}
    price = t['d14_forms']['C_B_plus_price_bound']['Mstar_minus_B4_infeasible']
    out['price'] = price
    out['c'] = c_rule(price)
    return out, {s: a for s, a in t['retune']['arm_of_scene'].items()}


def main():
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    out_path = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    counts_raw = open(COUNTS2, 'rb').read()
    c2 = json.loads(counts_raw)
    an = json.load(open(ANALYSIS))
    dev, trk = {}, {}
    for tag in ('t1', 't3'):
        dev[tag], aos = dev_summary(an, tag)
        trk[tag] = {'aos': aos}
    del an
    for tag in ('t1', 't3'):
        scenes, tab, F = load_tracker(tag, trk[tag]['aos'])
        log_idx, logs = log_map(scenes)
        av2_run = c2['runs'][AV2_RUN[tag]]
        assert av2_run['logs'] == AV2_LOGS
        lay = layout_match(tab, av2_run, len(scenes))
        trk[tag].update({'scenes': scenes, 'tab': tab, 'F': F, 'log_idx': log_idx, 'c': dev[tag]['c'], 'lay': lay,
                         'av2_decisions': av2_run['decision_states_and_pairs']['decisions'],
                         'av2_evaluable': {p: av2_run['by_population'][POP_AV2[p]]['evaluable_cells'] for p in CONF_POPS}})
    assert trk['t1']['scenes'] == trk['t3']['scenes']
    dec_per_scene = float(np.mean([Fs.shape[0] for Fs in trk['t1']['F']]))
    theta_d = min(1.0, (trk['t1']['av2_decisions'] / AV2_LOGS) / dec_per_scene)
    res = {
        'script': '50_CODE/c1_av2/c1_power_counts_v02.py', 'script_sha256': sha256_file(__file__),
        'counts_file': '60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v02.json (stage A, D16 v04 Choice 13)',
        'counts_sha256': hashlib.sha256(counts_raw).hexdigest(),
        'development_source': {'runs': '70_TESTS/k8_expl_v02_linux', 'analysis': '70_TESTS/k8_expl_v02_linux_analysis_v03/k8_exploratory_analysis_v03.json',
                               'analysis_sha256': sha256_file(ANALYSIS),
                               'status': 'confirmed by R16 (70_TESTS/R16_K8_RESULTS_REVIEW_v01.md); errata E8 to E14'},
        'av2_floor_direct_from_counts_v02': av2_floor_direct(c2),
        'seed': SEED,
        'outcome_statement': 'AV2: stage-A counts v02 only (items, logs, decisions). nuScenes development data otherwise. '
                             'No AV2 exceedance, margin, infeasibility, V2, TTV, NEES/ANEES or projected error computed or read.',
        'av2_layout': {t: {'decisions': trk[t]['av2_decisions'], 'evaluable_cells': trk[t]['av2_evaluable'],
                           'cells': {p: trk[t]['lay'][p]['rows'] for p in CONF_POPS}} for t in ('t1', 't3')},
        'nuscenes_decisions_per_scene': dec_per_scene, 'theta_decisions': theta_d,
        'development_840': dev,
        'validation_full_data': {t: validate(t, trk[t]['scenes'], trk[t]['tab'], trk[t]['F'], dev[t], rng) for t in ('t1', 't3')},
    }
    n_units = AV2_LOGS
    res['floor_rule_check_synthetic'] = floor_rule_check(trk, theta_d, rng, n_units)
    res['oc'] = [run_oc(trk, 'scene', True, theta_d, reps, rng, n_units),
                 run_oc(trk, 'scene', False, 1.0, reps, rng, n_units),
                 run_oc(trk, 'logblock', True, theta_d, reps, rng, n_units)]
    res['oc_B6_stress'] = [run_oc(trk, 'scene', True, theta_d, reps, rng, n_units, kappa=k) for k in KAPPAS if k != 1.0]
    res['wall_seconds'] = time.time() - t0
    with open(out_path, 'w') as f:
        json.dump(res, f, indent=1)
    print('done', out_path, round(res['wall_seconds'], 1), 's')


if __name__ == '__main__':
    main()
