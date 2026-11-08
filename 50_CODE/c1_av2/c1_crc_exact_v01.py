#!/usr/bin/env python3
"""Exact-arithmetic CRC for the C1 fits (Claude line, c1_crc_exact_v01, 2 Nov 2026). ERRATA_K8_v02 E15; C1 v04 section 7 item 1b.

x1_lib_v03.crc_threshold decides "n/(n+1) mean_s L_s(c) + 1/(n+1) <= delta" in floating point, where L_s(c) is scene s's share of
items with U > c. At an exact tie (the bound equals delta in rational arithmetic) the float sum depends on the scene order (nuScenes
T3, fold 4, h2s, L0 74: K7's order rejects U = 0.38665, sorted order accepts it). Here the same rule, the same candidate set (the
sorted unique U) and the same binary search, but every accept/reject is decided exactly:
    (Sum_s x_s / t_s + 1) / (n + 1) <= delta      <=>      Sum_s x_s / t_s <= delta (n + 1) - 1,
with x_s, t_s integers and delta = Fraction(repr(delta)) (0.05 -> 1/20). The answer is a function of the multiset of scenes only.
Also: fit_hier_exact (m_lib_v04.fit_hier with this statistic) and split_fit_exact (k7_fit_v01.split_fit's rule: fit_hier separately
on the not-in-path and in-path items, 192 thresholds), so M*, B6, M*Jx's base, B4 and B9 are all decided exactly.
"""
import os
import sys
from fractions import Fraction

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "m"))
import m_lib_v04 as M  # noqa: E402

DELTA = 0.05
N_MIN = M.N_CRC
N_L0 = M.N_L0


def _exact_ok(x, tot, d_exact):
    """Exact CRC decision from per-scene exceedance counts x and item counts tot (integer arrays)."""
    n = len(tot)
    s = sum((Fraction(int(x[tot == t].sum()), int(t)) for t in np.unique(tot)), Fraction(0))
    return s <= d_exact * (n + 1) - 1


def crc_threshold_exact(U, s, delta=DELTA):
    """x1_lib_v03.crc_threshold with exact decisions: the smallest sorted unique U value c with bound(c) <= delta; None if
    1/(n+1) > delta; the largest U + 1e-9 if even the largest value fails (as x1)."""
    U = np.asarray(U, float)
    scenes, si = np.unique(np.asarray(s), return_inverse=True)
    n = len(scenes)
    d_exact = Fraction(repr(float(delta)))
    if n == 0 or Fraction(1, n + 1) > d_exact:
        return None
    tot = np.bincount(si, minlength=n).astype(np.int64)
    order = np.sort(np.unique(U))

    def ok(c):
        x = np.bincount(si, weights=(U > c).astype(float), minlength=n).astype(np.int64)
        return _exact_ok(x, tot, d_exact)
    if not ok(order[-1]):
        return float(order[-1]) + 1e-9
    lo, hi = 0, len(order) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(order[mid]):
            hi = mid
        else:
            lo = mid + 1
    return float(order[lo])


def bound_exact(U, s, c):
    """The exact CRC bound (Fraction) at threshold c and n."""
    scenes, si = np.unique(np.asarray(s), return_inverse=True)
    n = len(scenes)
    tot = np.bincount(si, minlength=n).astype(np.int64)
    x = np.bincount(si, weights=(np.asarray(U) > c).astype(float), minlength=n).astype(np.int64)
    ssum = sum((Fraction(int(x[tot == t].sum()), int(t)) for t in np.unique(tot)), Fraction(0))
    return (ssum + 1) / (n + 1), n


def fit_hier_exact(U, unit, lv, start=0, n_min=N_MIN):
    return M.fit_hier(U, unit, lv, start, n_min, stat=crc_threshold_exact)


def split_fit_exact(U, s, lv, ip, start, n_min=N_MIN):
    """k7_fit_v01.split_fit with exact CRC decisions: 192 thresholds (index L0 + 96 x in-path) and their source levels."""
    out, src = np.full(2 * N_L0, np.nan), np.full(2 * N_L0, -1)
    for part in (0, 1):
        sel = ip == part
        thr, so = fit_hier_exact(U[sel], s[sel], [x[sel] for x in lv], start, n_min)
        out[part * N_L0:(part + 1) * N_L0], src[part * N_L0:(part + 1) * N_L0] = thr, so
    return out, src
