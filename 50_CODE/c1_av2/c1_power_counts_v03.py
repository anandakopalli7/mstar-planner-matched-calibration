"""C1 (Argoverse 2 confirmation): scaling scenario for slot S0 (the SD1_7 floor). v03 (2 Nov 2026).
v01 and v02 are kept and unchanged; this file imports v02's functions and changes none of them.

Question (the lead, 2 Nov): if the external set held k x 150 logs with the same per-log composition as AV2 validation,
what would the floors, P(H1) and B6's chance of passing validity on T3 be, for k in {2, 2.5, 3, 3.33, 4.67}?

OUTCOME-BLIND. AV2 input: the stage-A counts 60_RESULTS/av2_trk/AV2_TRACKER_COUNTS_v02.json only. Development input: the
K8 Linux replicate and its v03 analysis (confirmed by R16), as in v02. No AV2 outcome is computed or read.

Part A (counts only; the floors). Resampling k x 150 logs with replacement from AV2 validation: the number of logs holding
cell c is Binomial(k x 150, L_c / 150), with L_c the cell's logs in counts v02 and its items per present log unchanged. One
uniform per cell and replicate is shared by T1 and T3 (their cell layouts are nearly identical), so the trackers' floors
are drawn jointly. The power-qualified family is computed by v02's analytic rule (Sidak critical value over the evaluable
cells; beta-binomial 0.15 / 0.5; power >= 0.80), as v02.av2_floor_direct does at k = 1.

Part B (development effect sizes). v02.run_oc with n_units = round(k x 150), layout-matched scene draws, in three variants:
  plug-in      M* and every comparator with their nuScenes per-scene counts (as v02);
  Mstar_capped M*'s exceedances thinned, in every cell whose 840-scene estimate exceeds delta, to a scene-level rate of
               delta (the point estimates above delta are treated as noise; a bracket for the plug-in);
  kappa_0.5    plug-in with B6's per-cell excess over M* halved (v02's stress).
P(H1) with floors from Part B is pessimistic, because the layout match caps cells richer on AV2 (v02 section 6.5); the
combined estimate P(floors met, Part A) x P(H1 without floors, Part B) is also reported, as an approximation that treats the
count-driven floors as independent of the outcome-driven conditions.

Usage: python -B c1_power_counts_v03.py <out.json> [reps_partB]
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

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_power_counts_v02 as V2  # noqa: E402

SEED = 20261104
KS = (2.0, 2.5, 3.0, 3.33, 4.67)
KS_FINE = tuple(round(1.0 + 0.25 * i, 2) for i in range(17))   # 1.00 to 5.00 for the smallest-k search
RUNS_A = ('t1_lt3d', 't3_lt3d', 't1_voxelnext', 't3_voxelnext')
REPS_A = 4000


def part_a(c2, k, rng):
    N = int(round(k * V2.AV2_LOGS))
    cells = sorted({c for r in RUNS_A for p in V2.POP_AV2.values() for c in c2['runs'][r]['by_population'][p]['by_cell']})
    U = rng.random((REPS_A, len(cells)))
    out = {'k': k, 'logs': N}
    fam = {}
    for run in RUNS_A:
        out[run] = {}
        for pname, pa in V2.POP_AV2.items():
            bc = c2['runs'][run]['by_population'][pa]['by_cell']
            sizes = np.zeros(REPS_A, int)
            evals = np.zeros(REPS_A, int)
            cols = [(cells.index(c), v) for c, v in bc.items() if v['logs'] > 0]
            S = np.stack([stats.binom.ppf(U[:, j], N, v['logs'] / V2.AV2_LOGS) for j, v in cols], 1)
            n = np.array([v['items'] / v['logs'] for _, v in cols])
            ev = S >= V2.MIN_UNITS
            kev = ev.sum(1)
            q = stats.norm.ppf(0.95 ** (1.0 / np.maximum(kev, 1)))
            se = np.sqrt(V2.POWER_P * (1 - V2.POWER_P) * (V2.POWER_RHO + (1 - V2.POWER_RHO) / n)[None, :] / np.maximum(S, 1))
            pw = stats.norm.cdf((V2.POWER_P - V2.DELTA) / se - q[:, None])
            sizes = ((pw >= V2.POWER_MIN) & ev).sum(1)
            evals = kev
            fam[(run, pname)] = sizes
            out[run][pname] = {'family_median': float(np.median(sizes)), 'family_p10': float(np.quantile(sizes, 0.1)),
                               'evaluable_median': float(np.median(evals)),
                               'P_family_ge_6': float(np.mean(sizes >= V2.F_MIN))}
        out[run]['P_floors_met'] = float(np.mean((fam[(run, 'PD7_primary')] >= V2.F_MIN) & (fam[(run, 'SD1_7_gap_le_5m')] >= V2.F_MIN)))
    for det in ('lt3d', 'voxelnext'):
        both = np.ones(REPS_A, bool)
        for t in ('t1', 't3'):
            both &= (fam[(t + '_' + det, 'PD7_primary')] >= V2.F_MIN) & (fam[(t + '_' + det, 'SD1_7_gap_le_5m')] >= V2.F_MIN)
        out['P_floors_met_T1_and_T3_' + det] = float(both.mean())
    return out


def cap_mstar(trk, rng):
    """M*'s exceedances thinned in cells whose 840-scene scene-level estimate exceeds delta (per population)."""
    out = {}
    for t, d in trk.items():
        tab = {}
        caps = {}
        for p in V2.CONF_POPS:
            N, X = d['tab'][p]
            N0, X0 = N[0], X[0]
            pres = N0 > 0
            r = np.divide(X0, N0, out=np.zeros_like(X0), where=pres)
            est = np.where(pres.sum(0) > 0, (r * pres).sum(0) / np.maximum(pres.sum(0), 1), 0.0)
            f = np.where(est > V2.DELTA, V2.DELTA / np.where(est > 0, est, 1.0), 1.0)
            Xc = X.copy()
            Xc[0] = rng.binomial(X0.astype(np.int64), np.broadcast_to(f[None, :], X0.shape)).astype(float)
            tab[p] = (N, Xc)
            caps[p] = int((est > V2.DELTA).sum())
        dd = dict(d)
        dd['tab'] = tab
        out[t] = dd
        out[t + '_caps'] = caps
    return {t: out[t] for t in trk}, {t: out[t + '_caps'] for t in trk}


def summarise(o):
    r = {'P_H1_with_floors_synthetic': o['P_H1'], 'P_H1_without_floors': o['P_H1_without_floors_diagnostic'],
         'P_H2': o['P_H2'], 'P_H10': o['P_H10']}
    for t in ('t1', 't3'):
        g = o[t]
        r[t] = {'P_formB_without_floors': g['P_formB_without_floors_diagnostic'],
                'P_Mstar_failure_reason': g['P_Mstar_failure_reason'],
                'P_B6_not_shown_above_delta': 1.0 - g['P_shown_invalid']['B6'],
                'P_B6_strict_valid': g['P_strict_valid']['B6'],
                'P_beats_B6_given_in_V': g['P_beats_given_in_V']['B6'],
                'synthetic_family_median': g['Mstar_family_size_median'],
                'P_in_V': g['P_in_V_choice9']}
    return r


def main():
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    out_path = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 100
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    raw = open(V2.COUNTS2, 'rb').read()
    c2 = json.loads(raw)
    res = {'script': '50_CODE/c1_av2/c1_power_counts_v03.py', 'script_sha256': V2.sha256_file(__file__),
           'v02_module_sha256': V2.sha256_file(V2.__file__), 'counts_sha256': hashlib.sha256(raw).hexdigest(),
           'analysis_sha256': V2.sha256_file(V2.ANALYSIS), 'seed': SEED, 'reps_partB': reps, 'reps_partA': REPS_A,
           'outcome_statement': 'AV2: stage-A counts v02 only. nuScenes development data otherwise. No AV2 outcome computed or read.'}
    # Part A
    res['partA_fine'] = [part_a(c2, k, rng) for k in KS_FINE]
    res['partA'] = [part_a(c2, k, rng) for k in KS]
    smallest = {}
    for det in ('lt3d', 'voxelnext'):
        for crit in ('sd17', 'floors_both_trackers'):
            kk = None
            for a in res['partA_fine']:
                if crit == 'sd17':
                    ok = all(a['%s_%s' % (t, det)]['SD1_7_gap_le_5m']['P_family_ge_6'] >= 0.95 for t in ('t1', 't3'))
                else:
                    ok = a['P_floors_met_T1_and_T3_' + det] >= 0.95
                if ok:
                    kk = a['k']
                    break
            smallest['%s_%s' % (det, crit)] = kk
    res['smallest_k_P_ge_0.95'] = smallest
    # Part B
    an = json.load(open(V2.ANALYSIS))
    trk, dev = {}, {}
    for tag in ('t1', 't3'):
        dev[tag], aos = V2.dev_summary(an, tag)
        trk[tag] = {'aos': aos}
    del an
    for tag in ('t1', 't3'):
        scenes, tab, F = V2.load_tracker(tag, trk[tag]['aos'])
        log_idx, _ = V2.log_map(scenes)
        av2_run = c2['runs'][V2.AV2_RUN[tag]]
        trk[tag].update({'scenes': scenes, 'tab': tab, 'F': F, 'log_idx': log_idx, 'c': dev[tag]['c'],
                         'lay': V2.layout_match(tab, av2_run, len(scenes)),
                         'av2_decisions': av2_run['decision_states_and_pairs']['decisions']})
    dec_per_scene = float(np.mean([Fs.shape[0] for Fs in trk['t1']['F']]))
    theta_d = min(1.0, (trk['t1']['av2_decisions'] / V2.AV2_LOGS) / dec_per_scene)
    trk_cap, caps = cap_mstar(trk, rng)
    res['Mstar_cells_capped'] = caps
    res['partB'] = []
    for k in KS:
        n_units = int(round(k * V2.AV2_LOGS))
        row = {'k': k, 'units': n_units}
        row['plug_in'] = summarise(V2.run_oc(trk, 'scene', True, theta_d, reps, rng, n_units))
        row['Mstar_capped'] = summarise(V2.run_oc(trk_cap, 'scene', True, theta_d, reps, rng, n_units))
        row['kappa_0.5'] = summarise(V2.run_oc(trk, 'scene', True, theta_d, reps, rng, n_units, kappa=0.5))
        a = next(x for x in res['partA'] if x['k'] == k)
        pf = a['P_floors_met_T1_and_T3_lt3d']
        row['P_floors_met_T1_and_T3_lt3d_partA'] = pf
        for v in ('plug_in', 'Mstar_capped', 'kappa_0.5'):
            row[v]['P_H1_combined_estimate'] = pf * row[v]['P_H1_without_floors']
        res['partB'].append(row)
        print('k', k, 'done', round(time.time() - t0, 1), 's', flush=True)
    res['wall_seconds'] = time.time() - t0
    with open(out_path, 'w') as f:
        json.dump(res, f, indent=1)
    print('done', out_path, round(res['wall_seconds'], 1), 's')


if __name__ == '__main__':
    main()
