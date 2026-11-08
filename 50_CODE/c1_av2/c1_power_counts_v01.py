"""C1 (Argoverse 2 confirmation): counts-only power and precision simulation, v01 (2 Nov 2026).

Companion of 40_PROTOCOL/C1_AV2_CONFIRMATORY_PREREG_v01_DRAFT.md, section 6.

OUTCOME-BLIND (D15 section 4). Reads exactly one AV2 file, the counts file
60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json (item, record, log and frame counts).
Every effect size is a nuScenes development number copied from a design document,
with its source next to the constant. Computes no AV2 exceedance, margin,
infeasibility, V2, TTV, NEES/ANEES or projected error. One process, numpy/scipy,
well under 1 GB.

Usage:  python -B c1_power_counts_v01.py <out.json>
"""
import hashlib
import json
import math
import sys
import time

import numpy as np
from scipy import stats

W = r'C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911'
COUNTS = W + r'\60_RESULTS\av2_trk\AV2_TRACKER_COUNTS_v01.json'
SEED = 20261102
DELTA = 0.05
EVAL_MIN_LOGS = 39          # evaluable cell: >= 39 scenes from >= 8 logs; on AV2 a scene is a log
NMIN = 19                   # own-threshold floor (P01 Prop. 6)

# ---------------------------------------------------------------- nuScenes development numbers
# Infeasible-decision rate and pooled PD7 scene-level exceedance on the 10 development scenes.
# Mstar, B0, B4, RETUNED: 50_CODE/k8/README_K8_v02.md, "Development check" tables (k8 v02 code).
# B1, B3, B6, B9: 40_PROTOCOL/K7_PREREGISTRATION_v02.md section 9a (k7 sim, equal to k8 sim on
# shared arms by test T1 of README_K8_v02). B0 and B4 agree between the two files.
INFEAS = {
    't1': {'Mstar': 0.159, 'B0': 0.401, 'B1': 0.483, 'B3': 0.951, 'B4': 0.179,
           'B6': 0.248, 'B9': 0.520, 'RETUNED': 0.422},
    't3': {'Mstar': 0.191, 'B0': 0.945, 'B1': 0.415, 'B3': 0.968, 'B4': 0.175,
           'B6': 0.169, 'B9': 0.502, 'RETUNED': 0.527},
}
POOLED_PD7 = {
    't1': {'Mstar': 0.043, 'B0': 0.033, 'B1': 0.015, 'B3': 0.003, 'B4': 0.070,
           'B6': 0.056, 'B9': 0.021, 'RETUNED': 0.033},
    't3': {'Mstar': 0.051, 'B0': 0.005, 'B1': 0.040, 'B3': 0.004, 'B4': 0.087,
           'B6': 0.063, 'B9': 0.028, 'RETUNED': 0.047},
}
FORM_B_COMPARATORS = ['B0', 'B1', 'B3', 'B4', 'B6', 'B9', 'RETUNED']   # README_K8_v02 "Form B comparators"
FORM_A_COMPARATORS = ['B0', 'B1', 'B4', 'B9']                          # D14 v05 section 6, Form A
# PD7 records per decision on nuScenes: about 900,000 PD7 records (K7 v02 section 9a) over
# 32,449 decision states (K7 v02 section 2). Track density: nuScenes T1 val 381,553 export
# records over 6,019 keyframes (MANUSCRIPT_DRAFT_v02 V-A); AV2 from the counts file.
NUS_PD7_RECORDS = 900_000
NUS_DECISIONS = 32_449
NUS_VAL_RECORDS = 381_553
NUS_VAL_FRAMES = 6_019
# Intra-scene correlation of K6 M* exceedances: median 0.13-0.15 in PD7 cells, 0.21-0.26 in
# SD1_7, 0.31-0.32 in PD (K7 v02 section 8, from R12 r12_rho_k6.json).
RHO_E_GRID = [0.05, 0.15, 0.30]
RHO_LOG_GRID = [0.10, 0.30]   # log-level ICC of infeasibility: assumed (no source); two values
# X2 (nuScenes train, T1): in-path car cells at 2 s, scene-level E and orientation-null thresholds
# (MANUSCRIPT_DRAFT_v02 Table II); q = 2.48 two-sided sup-t over 4 cells (V-B).
X2_LAT = {'<20': {'E_scene': 0.141, 'thr': 0.0775}, '20-40': {'E_scene': 0.245, 'thr': 0.0816}}
X2_Q = 2.48
# Form C rule (D16 Choice 1): c = max(0.03, ceil_0.01(price) + 0.01); development prices on the
# 10 scenes (K7 v02 section 13 item 4; README_K8_v02): T1 -0.020, T3 +0.016.
DEV_PRICE = {'t1': 0.159 - 0.179, 't3': 0.191 - 0.175}


def sha256_file(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


def c_rule(price):
    return max(0.03, math.ceil(round(price * 100, 9)) / 100 + 0.01)


def beta_ab(p, rho):
    k = 1.0 / rho - 1.0
    return p * k, (1.0 - p) * k


def beta_q(u, p, rho):
    a, b = beta_ab(p, rho)
    return stats.beta.ppf(u, a, b)


# ---------------------------------------------------------------- A. layout from the counts
def layout(d):
    run = d['runs']['t1_lt3d']
    L = run['logs']
    frames = run['frames']
    dec = (frames - 2 * L) / L
    density_ratio = (run['export_records'] / frames) / (NUS_VAL_RECORDS / NUS_VAL_FRAMES)
    m_pd7 = dec * (NUS_PD7_RECORDS / NUS_DECISIONS) * density_ratio
    g4 = {'car': 'car', 'pedestrian': 'pedestrian', 'cyclist': 'two_wheeler',
          'motorcyclist_descr': 'two_wheeler', 'large_descr': 'large'}
    # method-stage cells: in-path, paired, horizon available; group x axis x motion pooled over range
    cells = {}
    for r in run['items_table']:
        if r['population'] != 'inpath' or r['pairing'] != 'paired' or r['horizon'] != 'available':
            continue
        key = (g4[r['group']], r['axis'], r['motion'])
        c = cells.setdefault(key, {'items': 0, 'logs_lb': 0, 'logs_sum': 0, 'rows': 0})
        c['items'] += r['n']
        c['logs_lb'] = max(c['logs_lb'], r['logs'])
        c['logs_sum'] += r['logs']
        c['rows'] += 1
    s_gam = run['summaries']['paired_items_by_group_axis_motion_population']
    paired_any = {}
    for k, v in s_gam.items():
        g, ax, mo, pop = k.split('|')
        paired_any.setdefault((g4[g], ax, mo, pop), []).append(v['logs'])
    out_m = []
    for key in sorted(cells):
        c = cells[key]
        pa = paired_any.get(key + ('inpath',), [])
        ub = min(L, c['logs_sum'], sum(pa) if pa else L)
        lb = c['logs_lb']
        status = 'yes' if lb >= EVAL_MIN_LOGS else ('no' if ub < EVAL_MIN_LOGS else 'uncertain')
        out_m.append({'group': key[0], 'axis': key[1], 'motion': key[2], 'items': c['items'],
                      'logs_lb': lb, 'logs_ub': ub, 'evaluable_ge39_logs': status})
    # planner-population upper bound: union of in-path and not-in-path paired items (any horizon)
    pd7_ub = []
    keys = sorted({(g, ax, mo) for (g, ax, mo, pop) in paired_any})
    for key in keys:
        lin = paired_any.get(key + ('inpath',), [])
        lnot = paired_any.get(key + ('not_inpath',), [])
        lb = max(lin + lnot) if (lin + lnot) else 0
        ub = min(L, sum(lin) + sum(lnot))
        pd7_ub.append({'group': key[0], 'axis': key[1], 'motion': key[2],
                       'logs_union_lb': lb, 'logs_union_ub': ub})
    return {'logs': L, 'frames': frames, 'decisions_per_log': dec,
            'density_ratio_av2_over_nus': density_ratio, 'pd7_records_per_log_assumed': m_pd7,
            'method_stage_cells_t1_lt3d': out_m, 'planner_cells_log_upper_bounds_t1_lt3d': pd7_ub}


# ---------------------------------------------------------------- B. floor feasibility
def power_flag_equal(p, L, m, rho, q, reps, rng):
    a, b = beta_ab(p, rho)
    r = rng.beta(a, b, size=(reps, L))
    x = rng.binomial(m, r)
    s = x / m
    est = s.mean(1)
    se = s.std(1, ddof=1) / np.sqrt(L)
    return float(np.mean(est - q * se > DELTA))


def floor_feasibility(rng):
    res = []
    for k in [1, 10, 20, 32]:
        q = stats.norm.ppf(1 - 0.05 / k)
        for m in [5, 20, 100]:
            lmin = None
            curve = {}
            for L in range(20, 151, 5):
                pw = power_flag_equal(0.15, L, m, 0.5, q, 2000, rng)
                curve[L] = pw
                if lmin is None and pw >= 0.80:
                    lmin = L
            res.append({'family_cells_k': k, 'q_bonferroni': q, 'records_per_log': m,
                        'min_logs_power_ge_0.80': lmin, 'power_at_150_logs': curve[150]})
    return res


# ---------------------------------------------------------------- C. method-stage component power
def method_stage_power(lay, rng):
    q = stats.norm.ppf(1 - 0.05 / 10)       # 10-cell family, as nuScenes E2 (9-10 cells)
    grid = [0.06, 0.08, 0.10, 0.12, 0.15, 0.20, 0.25, 0.30, 0.40]
    out = []
    for c in lay['method_stage_cells_t1_lt3d']:
        if c['group'] != 'car' or c['evaluable_ge39_logs'] == 'no':
            continue
        L = c['logs_ub']
        n = c['items']
        if n < L:
            continue
        alloc = 1 + rng.multinomial(n - L, rng.dirichlet(np.ones(L)))
        for rho in [0.3, 0.5]:
            pw = {}
            for p in grid:
                a, b = beta_ab(p, rho)
                reps = 1000
                r = rng.beta(a, b, size=(reps, L))
                x = rng.binomial(alloc[None, :], r)
                s = x / alloc[None, :]
                est = s.mean(1)
                se = s.std(1, ddof=1) / np.sqrt(L)
                pw[p] = float(np.mean(est - q * se > DELTA))
            mde = next((p for p in grid if pw[p] >= 0.80), None)
            out.append({'cell': f"car|{c['axis']}|{c['motion']}", 'items': n, 'logs_used': L,
                        'rho': rho, 'power_by_true_rate': pw, 'MDE80': mde})
    return {'q': q, 'note': 'fixed calibration, one-sample log bootstrap approximated by the '
                            'between-log SD; logs_used = upper bound of the cell log count',
            'cells': out}


# ---------------------------------------------------------------- D. diagnosis replication (T1)
def diagnosis_power(lay, rng):
    cells = {c['group'] + '|' + c['axis'] + '|' + c['motion']: c for c in lay['method_stage_cells_t1_lt3d']}
    run_counts = DCOUNTS['runs']['t1_lt3d']['summaries']['paired_horizon_available_items_by_group_range_axis_population']
    out = []
    for rng_bin in ['<20', '20-40']:
        v = run_counts[f'car|{rng_bin}|lat|inpath']
        n, L = v['items'], v['logs']
        alloc = 1 + rng.multinomial(n - L, rng.dirichlet(np.ones(L)))
        thr = X2_LAT[rng_bin]['thr']
        for label, p in [('X2_scene_E', X2_LAT[rng_bin]['E_scene']),
                         ('half_X2_excess', 0.05 + (X2_LAT[rng_bin]['E_scene'] - 0.05) / 2)]:
            for rho in [0.3, 0.5]:
                a, b = beta_ab(p, rho)
                r = rng.beta(a, b, size=(2000, L))
                x = rng.binomial(alloc[None, :], r)
                s = x / alloc[None, :]
                est = s.mean(1)
                se = s.std(1, ddof=1) / np.sqrt(L)
                out.append({'cell': f'car|{rng_bin}|lat', 'items': n, 'logs': L, 'assumed': label,
                            'true_E': p, 'threshold': thr, 'rho': rho,
                            'power_FAILS': float(np.mean(est - X2_Q * se > thr))})
    return out


# ---------------------------------------------------------------- E. K8 decision mode
def sim_pooled_valid(p, L, m, rho_e, reps, rng):
    a, b = beta_ab(p, rho_e)
    r = rng.beta(a, b, size=(reps, L))
    mi = int(round(m))
    s = rng.binomial(mi, r) / mi
    est = s.mean(1)
    se = s.std(1, ddof=1) / np.sqrt(L)
    flagged = est - 1.645 * se > DELTA
    return (~flagged) & (est + 1.645 * se <= DELTA + 0.03)


def infeas_rates(p, rho_log, u):
    return np.clip(beta_q(u, p, rho_log), 0, 1)


def paired_diff_counts(pm, pc, D, coupling, rng):
    if coupling == 'comonotone':
        g = np.abs(pm - pc)
        return np.sign(pm - pc) * rng.binomial(D, g)
    return rng.binomial(D, pm) - rng.binomial(D, pc)


def k8_formB(lay, rng, reps=3000):
    L = lay['logs']
    D = int(round(lay['decisions_per_log']))
    m = lay['pd7_records_per_log_assumed']
    arms = ['Mstar'] + FORM_B_COMPARATORS
    out = []
    for t in ['t1', 't3']:
        c_val = c_rule(DEV_PRICE[t])
        for rho_log in RHO_LOG_GRID:
            ul = rng.random((reps, L))          # shared log difficulty for infeasibility
            pl = {a: infeas_rates(INFEAS[t][a], rho_log, ul) for a in arms}
            for coupling in ['comonotone', 'independent']:
                zstat = {}
                for c in FORM_B_COMPARATORS:
                    dc = paired_diff_counts(pl['Mstar'], pl[c], D, coupling, rng) / D
                    zstat[c] = (dc.mean(1), dc.std(1, ddof=1) / np.sqrt(L))
                for rho_e in RHO_E_GRID:
                    valid = {a: sim_pooled_valid(POOLED_PD7[t][a], L, m, rho_e, reps, rng) for a in arms}
                    nvalid = sum(valid[c].astype(int) for c in FORM_B_COMPARATORS)
                    zb = stats.norm.ppf(1 - 0.05 / np.maximum(nvalid, 1))
                    ok = np.ones(reps, bool)
                    beats = {}
                    for c in FORM_B_COMPARATORS:
                        mu, se = zstat[c]
                        beats[c] = mu + zb * se < 0
                        ok &= (~valid[c]) | beats[c]
                    formB = valid['Mstar'] & ok
                    za = stats.norm.ppf(1 - 0.05 / 4)
                    formA = valid['Mstar'].copy()
                    for c in FORM_A_COMPARATORS:
                        mu, se = zstat[c]
                        formA &= mu + za * se < 0
                    mu4, se4 = zstat['B4']
                    out.append({
                        'tracker': t, 'rho_e': rho_e, 'rho_log': rho_log, 'coupling': coupling,
                        'P_Mstar_pooled_valid': float(valid['Mstar'].mean()),
                        'P_comparator_pooled_valid': {c: float(valid[c].mean()) for c in FORM_B_COMPARATORS},
                        'P_beats_at_bonferroni_level_given_valid': {
                            c: (float(beats[c][valid[c]].mean()) if valid[c].any() else None)
                            for c in FORM_B_COMPARATORS},
                        'P_formB_pooled_proxy': float(formB.mean()),
                        'P_formA_pooled_proxy': float(formA.mean()),
                        'c_by_rule_at_dev_price': c_val,
                        'mean_SE_paired_Mstar_minus_B4': float(se4.mean()),
                        'P_formC_at_0.05': float(np.mean(mu4 + stats.norm.ppf(0.95) * se4 <= c_val)),
                        'P_formC_at_0.01': float(np.mean(mu4 + stats.norm.ppf(0.99) * se4 <= c_val)),
                    })
    return out


def pooled_precision(lay, rng, reps=4000):
    L = lay['logs']
    m = lay['pd7_records_per_log_assumed']
    out = []
    for rho_e in RHO_E_GRID:
        a, b = beta_ab(DELTA, rho_e)
        r = rng.beta(a, b, size=(reps, L))
        x = rng.binomial(int(round(m)), r)
        s = x / int(round(m))
        se = s.std(1, ddof=1) / np.sqrt(L)
        out.append({'rho_e': rho_e, 'true_rate': DELTA, 'mean_SE': float(se.mean()),
                    'two_sided_95_halfwidth': float(1.96 * se.mean())})
    return out


# ---------------------------------------------------------------- F. M*J (joint loss) precision
def mstarj_precision(lay, rng, reps=4000):
    L = lay['logs']
    D = int(round(lay['decisions_per_log']))
    out = []
    for p in [0.03, 0.05, 0.08, 0.10]:
        for rho in RHO_E_GRID:
            a, b = beta_ab(p, rho)
            r = rng.beta(a, b, size=(reps, L))
            x = rng.binomial(D, r)
            s = x / D
            est = s.mean(1)
            se = s.std(1, ddof=1) / np.sqrt(L)
            flagged = est - 1.645 * se > DELTA
            valid = (~flagged) & (est + 1.645 * se <= DELTA + 0.03)
            out.append({'true_joint_rate': p, 'rho': rho, 'P_flagged_pointwise': float(flagged.mean()),
                        'P_valid_pooled': float(valid.mean()),
                        'two_sided_95_halfwidth': float(1.96 * se.mean())})
    return out


# ---------------------------------------------------------------- G. Form C power curve
def formC_curve(lay, rng, reps=4000):
    L = lay['logs']
    D = int(round(lay['decisions_per_log']))
    out = []
    base = INFEAS['t3']['B4']
    for d in [-0.02, 0.0, 0.016, 0.02, 0.03]:
        for rho_log in RHO_LOG_GRID:
            u = rng.random((reps, L))
            pm = infeas_rates(base + d, rho_log, u)
            pc = infeas_rates(base, rho_log, u)
            for coupling in ['comonotone', 'independent']:
                dc = paired_diff_counts(pm, pc, D, coupling, rng) / D
                mu = dc.mean(1)
                se = dc.std(1, ddof=1) / np.sqrt(L)
                for c_val in [0.03, 0.04]:
                    out.append({'true_price': d, 'c': c_val, 'rho_log': rho_log, 'coupling': coupling,
                                'mean_SE': float(se.mean()),
                                'P_ceiling_shown_0.05': float(np.mean(mu + 1.645 * se <= c_val)),
                                'P_ceiling_shown_0.01': float(np.mean(mu + 2.326 * se <= c_val))})
    return out


def main():
    global DCOUNTS
    out_path = sys.argv[1]
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    with open(COUNTS, 'rb') as f:
        raw = f.read()
    DCOUNTS = json.loads(raw)
    lay = layout(DCOUNTS)
    res = {
        'script': '50_CODE/c1_av2/c1_power_counts_v01.py',
        'script_sha256': sha256_file(__file__),
        'counts_file': '60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v01.json',
        'counts_sha256': hashlib.sha256(raw).hexdigest(),
        'seed': SEED,
        'outcome_statement': 'counts and nuScenes development effect sizes only; no AV2 exceedance, '
                             'margin, infeasibility, V2, TTV, NEES/ANEES or projected error computed or read',
        'inputs_from_design_documents': {
            'INFEAS': INFEAS, 'POOLED_PD7': POOLED_PD7, 'DEV_PRICE': DEV_PRICE,
            'X2_LAT': X2_LAT, 'X2_Q': X2_Q, 'RHO_E_GRID': RHO_E_GRID, 'RHO_LOG_GRID': RHO_LOG_GRID},
        'layout': lay,
        'floor_feasibility': floor_feasibility(rng),
        'method_stage_component_power': method_stage_power(lay, rng),
        'diagnosis_power_t1': diagnosis_power(lay, rng),
        'pooled_pd7_precision': pooled_precision(lay, rng),
        'k8_formB_pooled_proxy': k8_formB(lay, rng),
        'mstarj_precision': mstarj_precision(lay, rng),
        'formC_power_curve': formC_curve(lay, rng),
    }
    res['wall_seconds'] = time.time() - t0
    with open(out_path, 'w') as f:
        json.dump(res, f, indent=1)
    print('done', out_path, round(res['wall_seconds'], 1), 's')


if __name__ == '__main__':
    main()
