"""Compiled replacement for CANMOT's geometry.nusc_utils.loop_convex (Claude line, v01, 30 Oct 2026).

CANMOT builds one scipy Qhull ConvexHull per (track, detection) pair of bottom-corner sets (8 points) and takes the
shoelace area of the hull. On Windows each Qhull call also creates a temporary file. This function computes the same
hull area with Andrew's monotone chain in numba, for all pairs at once. Masked pairs (seq_mask True) receive the area of
their own hull too; CANMOT overwrites their GIoU with -inf, so their value is never used.
The hull's starting vertex differs from Qhull's, so areas can differ in the last bits. Use is accepted only after an
end-to-end export on the 150 val scenes is record-identical to the native run (x1_export_v04 --fast-convex).
"""
import numpy as np
from numba import njit


@njit(cache=True)
def _cross(ox, oy, ax, ay, bx, by):
    return (ax - ox) * (by - oy) - (ay - oy) * (bx - ox)


@njit(cache=True)
def hull_areas(pts):
    n = pts.shape[0]
    out = np.empty(n)
    idx = np.empty(8, np.int64)
    hull = np.empty(17, np.int64)
    for t in range(n):
        p = pts[t]
        # sort 8 points by (x, y)
        for i in range(8):
            idx[i] = i
        for i in range(1, 8):
            j = i
            while j > 0 and (p[idx[j], 0] < p[idx[j - 1], 0] or (p[idx[j], 0] == p[idx[j - 1], 0] and p[idx[j], 1] < p[idx[j - 1], 1])):
                tmp = idx[j]; idx[j] = idx[j - 1]; idx[j - 1] = tmp
                j -= 1
        k = 0
        for i in range(8):
            while k >= 2 and _cross(p[hull[k - 2], 0], p[hull[k - 2], 1], p[hull[k - 1], 0], p[hull[k - 1], 1], p[idx[i], 0], p[idx[i], 1]) <= 0:
                k -= 1
            hull[k] = idx[i]; k += 1
        lower = k + 1
        for i in range(6, -1, -1):
            while k >= lower and _cross(p[hull[k - 2], 0], p[hull[k - 2], 1], p[hull[k - 1], 0], p[hull[k - 1], 1], p[idx[i], 0], p[idx[i], 1]) <= 0:
                k -= 1
            hull[k] = idx[i]; k += 1
        m = k - 1
        s = 0.0
        for i in range(m):
            a = hull[i]; b = hull[(i + 1) % m]
            s += p[a, 0] * p[b, 1] - p[a, 1] * p[b, 0]
        out[t] = abs(s) * 0.5
    return out


def fast_loop_convex(bottom_corners_a, bottom_corners_b, mask):
    all_bcs = np.ascontiguousarray(np.concatenate((bottom_corners_a, bottom_corners_b), axis=2).reshape(-1, 8, 2), dtype=np.float64)
    return hull_areas(all_bcs).reshape(bottom_corners_a.shape[:2])


def install():
    """Patch the name giou_3d looks up. Returns the module patched, for the run record."""
    import canmot.geometry.nusc_distance as nd
    nd.loop_convex = fast_loop_convex
    return nd.__name__
