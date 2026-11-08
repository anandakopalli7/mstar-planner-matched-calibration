"""C1 (Argoverse 2 confirmation): provisional power at 375 logs, the D18 option-A confirmation set. v04 (2 Nov 2026).
v01 to v03 are kept and unchanged; this file imports v01, v02 and v03 and changes none of their functions.

D18 v02 (option A): our own CenterPoint (LT3D code and configuration) trained on 475 AV2 train logs, run with both
trackers on the 225 held-out train logs plus the 150 validation logs: 375 logs, all unseen by the detector.

PROVISIONAL. The new detector and trackers do not exist yet. Everything here assumes that the 375 logs have the per-log
composition of AV2 validation under the public LT3D detector (counts v01 and v02) - the scaling model of v03 at k = 2.5.
The real stage-A counts of the 375 logs replace it before the freeze.

OUTCOME-BLIND. AV2 input: counts v01 (method-stage in-path cells) and v02 (K8 decision counts). Development input: the K8
Linux replicate and its v03 analysis (confirmed by R16). No AV2 outcome is computed or read.

Parts:
  A  K8 power-qualified families at 375 logs (v03.part_a, 4000 replicates).
  M  The method-stage in-path audit population (H6, H7, H8 and the predictor arm H9 use it) at 150 and 375 logs: evaluable
     cells and the K6 power-rule family, from counts v01's in-path, paired, horizon-available cells (log counts between the
     lower and upper bounds of v01's layout, scaled binomially as in v03).
  B  v02.run_oc at 375 units: plug-in, M* capped (v03), B6 excess halved; REPS datasets each.
  J  M*Jx's CRC allowance for the calibration-fold joint loss at the fold sizes of nuScenes (about 165 scenes), AV2
     validation alone (30 logs) and the 375-log set (75 logs).

Usage: python -B c1_power_counts_v04.py <out.json> [reps]
"""
import json
import math
import os
import sys
import time
import warnings

import numpy as np
from scipy import stats

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import c1_power_counts_v01 as V1  # noqa: E402
import c1_power_counts_v02 as V2  # noqa: E402
import c1_power_counts_v03 as V3  # noqa: E402

SEED = 20261105
K = 2.5
REPS_M = 4000


def part_m(lay1, k, rng):
    """In-path audit cells (group x axis x motion pooled over range), T1 LT3D, counts v01."""
    N = int(round(k * V2.AV2_LOGS))
    out = {}
    for bound in ('logs_lb', 'logs_ub'):
        cells = [c for c in lay1['method_stage_cells_t1_lt3d'] if c[bound] > 0]
        L = np.array([c[bound] for c in cells], float)
        n = np.array([c['items'] / c[bound] for c in cells])
        S = stats.binom.ppf(rng.random((REPS_M, len(cells))), N, np.minimum(L / V2.AV2_LOGS, 1.0)) if k != 1 else np.tile(L, (REPS_M, 1))
        ev = S >= V2.MIN_UNITS
        kev = ev.sum(1)
        q = stats.norm.ppf(0.95 ** (1.0 / np.maximum(kev, 1)))
        se = np.sqrt(V2.POWER_P * (1 - V2.POWER_P) * (V2.POWER_RHO + (1 - V2.POWER_RHO) / n)[None, :] / np.maximum(S, 1))
        fam = ((stats.norm.cdf((V2.POWER_P - V2.DELTA) / se - q[:, None]) >= V2.POWER_MIN) & ev).sum(1)
        out[bound] = {'evaluable_median': float(np.median(kev)), 'family_median': float(np.median(fam)),
                      'P_family_ge_6': float(np.mean(fam >= V2.F_MIN))}
    return {'k': k, 'logs': N, **out}


def part_j():
    out = {}
    for label, n in (('nuScenes_fold_about_165_scenes', 165), ('AV2_val_only_fold_30_logs', 30), ('AV2_375_fold_75_logs', 75)):
        allow = (V2.DELTA - 1.0 / (n + 1)) * (n + 1) / n
        out[label] = {'n_calibration_units': n, 'finite_sample_term': 1.0 / (n + 1), 'max_mean_calibration_joint_loss': allow}
    return out


def main():
    warnings.filterwarnings('ignore', category=RuntimeWarning)
    out_path = sys.argv[1]
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 300
    t0 = time.time()
    rng = np.random.default_rng(SEED)
    raw2 = open(V2.COUNTS2, 'rb').read()
    c2 = json.loads(raw2)
    raw1 = open(V1.COUNTS, 'rb').read()
    lay1 = V1.layout(json.loads(raw1))
    res = {'script': '50_CODE/c1_av2/c1_power_counts_v04.py', 'script_sha256': V2.sha256_file(__file__),
           'modules_sha256': {'v01': V2.sha256_file(V1.__file__), 'v02': V2.sha256_file(V2.__file__), 'v03': V2.sha256_file(V3.__file__)},
           'counts_v01_sha256': V2.hashlib.sha256(raw1).hexdigest(), 'counts_v02_sha256': V2.hashlib.sha256(raw2).hexdigest(),
           'analysis_sha256': V2.sha256_file(V2.ANALYSIS), 'seed': SEED, 'k': K, 'reps': reps,
           'status': 'PROVISIONAL: scaling model of AV2 validation under the public LT3D detector; replaced by the real stage-A '
                     'counts of the 375 logs (own detector, both trackers) before the freeze',
           'outcome_statement': 'AV2: counts v01 and v02 only. nuScenes development data otherwise. No AV2 outcome computed or read.'}
    res['partA_375'] = V3.part_a(c2, K, rng)
    res['partM'] = [part_m(lay1, 1.0, rng), part_m(lay1, K, rng)]
    res['partJ'] = part_j()
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
    trk_cap, caps = V3.cap_mstar(trk, rng)
    n_units = int(round(K * V2.AV2_LOGS))
    pf = res['partA_375']['P_floors_met_T1_and_T3_lt3d']
    res['partB_375'] = {}
    for name, tk, kap in (('plug_in', trk, 1.0), ('Mstar_capped', trk_cap, 1.0), ('kappa_0.5', trk, 0.5)):
        s = V3.summarise(V2.run_oc(tk, 'scene', True, theta_d, reps, rng, n_units, kappa=kap))
        s['P_H1_combined_estimate'] = pf * s['P_H1_without_floors']
        res['partB_375'][name] = s
        print(name, 'done', round(time.time() - t0, 1), 's', flush=True)
    res['wall_seconds'] = time.time() - t0
    with open(out_path, 'w') as f:
        json.dump(res, f, indent=1)
    print('done', out_path, round(res['wall_seconds'], 1), 's')


if __name__ == '__main__':
    main()
