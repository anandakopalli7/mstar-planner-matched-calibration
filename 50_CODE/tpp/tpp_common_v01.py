#!/usr/bin/env python3
"""TPP arm shared helpers (Claude line, v01, 2 Nov 2026). Pure numpy; runs under Python 3.8 (tpp38) and 3.10 (canmot310).

Design: 90_DECISIONS/D16_DELEGATED_CHOICES_v01.md Choice 3 and 30_PRIOR_ART/P7_L5_DEPLOYED_PREDICTOR_ARM_v01.md C.1, C.3.
Contents: class mapping (cache class -> Trajectron++ node type), the scene offset rule of Trajectron++'s nuScenes
process_data.py, contiguous-history bookkeeping, the history-length strata {2, 3-4, >=5}, frame helpers (world <-> scene
offset, rotation of a 2x2 covariance into object axes and back), and the two Gaussian summaries of a 2-D Gaussian mixture:
V1 = the most likely component (largest weight), V2 = the moment-matched Gaussian
  mu = sum_k w_k mu_k,  Sigma = sum_k w_k (Sigma_k + d_k d_k^T),  d_k = mu_k - mu,
plus a summary of the mixture weights (largest weight, its index, entropy in nats, effective number 1 / sum w^2).
Nothing here touches ground truth.
"""
import hashlib

import numpy as np

CLASSES = ("car", "truck", "bus", "trailer", "pedestrian", "motorcycle", "bicycle")   # k6_cache_v02 class index order
TPP_VEHICLE, TPP_PEDESTRIAN, TPP_NONE = 0, 1, -1
TPP_TYPE_NAMES = ("VEHICLE", "PEDESTRIAN")
# car, truck, bus, trailer -> VEHICLE (Trajectron++ trained on every non-parked 'vehicle.*' category except bicycles and
# motorcycles); pedestrian -> PEDESTRIAN; motorcycle and bicycle are not covered by the ECCV 2020 models.
TPP_TYPE_OF_CLS = np.array([TPP_VEHICLE, TPP_VEHICLE, TPP_VEHICLE, TPP_VEHICLE, TPP_PEDESTRIAN, TPP_NONE, TPP_NONE], np.int8)
DT = 0.5                    # nuScenes keyframes, Trajectron++ FREQUENCY = 2
STEP_OF_H = (1, 2, 3, 4)    # K8 calibrated step index h = 0..3 -> Trajectron++ prediction step (0.5 ... 2.0 s)
PRIMARY_STEP = 4            # 2.0 s
MIN_HISTORY = 2             # P7-L5 C.3: at least 2 states (velocity undefined from one)
HIST_STRATA = ("2", "3-4", ">=5")

# status codes per record (one source)
ST_OK = 0
ST_CLASS_NOT_COVERED = 1     # motorcycle / bicycle
ST_SHORT_HISTORY = 2         # fewer than MIN_HISTORY contiguous states at k
ST_NOT_PREDICTED = 3         # the node had no model at k (should not happen)
ST_NONFINITE = 4             # V1 or V2 not finite
ST_NOT_PD = 5                # V1 or V2 covariance not positive definite
ST_NO_GT_NODE = 6            # GT source: instance not annotated at k (should not happen: items need a paired track)
STATUS_NAMES = {ST_OK: "ok", ST_CLASS_NOT_COVERED: "class_not_covered", ST_SHORT_HISTORY: "history_lt_2",
                ST_NOT_PREDICTED: "not_predicted", ST_NONFINITE: "nonfinite", ST_NOT_PD: "not_pd", ST_NO_GT_NODE: "no_gt_node"}


def hist_stratum(n):
    """History-length stratum of a contiguous history of n states: 0 -> '2', 1 -> '3-4', 2 -> '>=5', -1 below 2."""
    n = np.asarray(n)
    return np.where(n < 2, -1, np.where(n == 2, 0, np.where(n <= 4, 1, 2))).astype(np.int8)


def contiguous_run_lengths(kk):
    """For the sorted keyframe indices kk of one node, the length of the contiguous run ending at each entry."""
    kk = np.asarray(kk)
    out = np.ones(len(kk), np.int32)
    for i in range(1, len(kk)):
        if kk[i] == kk[i - 1] + 1:
            out[i] = out[i - 1] + 1
    return out


def scene_offset(xs, ys):
    """Trajectron++ nuScenes process_data.py: x_min = round(min x - 50), y_min = round(min y - 50) over the scene's
    agents and the ego; positions are fed as x - x_min, y - y_min."""
    return float(np.round(np.min(xs) - 50.0)), float(np.round(np.min(ys) - 50.0))


def to_scene(xy, off):
    return np.asarray(xy, float) - np.asarray(off, float)


def to_world(xy, off):
    return np.asarray(xy, float) + np.asarray(off, float)


def wrap(a):
    return (np.asarray(a, float) + np.pi) % (2 * np.pi) - np.pi


def rot(theta):
    c, s = np.cos(theta), np.sin(theta)
    return np.array([[c, -s], [s, c]])


def cov_to_axes(S, yaw):
    """2x2 world covariance -> object frame (longitudinal, lateral) for heading yaw: R(yaw)^T S R(yaw)."""
    R = rot(yaw)
    return R.T @ S @ R


def cov_from_axes(S_obj, yaw):
    R = rot(yaw)
    return R @ S_obj @ R.T


def cov3(S):
    """(..., 2, 2) -> (..., 3) as (xx, xy, yy)."""
    S = np.asarray(S)
    return np.stack([S[..., 0, 0], S[..., 0, 1], S[..., 1, 1]], -1)


def cov22(c3):
    c3 = np.asarray(c3)
    return np.stack([np.stack([c3[..., 0], c3[..., 1]], -1), np.stack([c3[..., 1], c3[..., 2]], -1)], -2)


def min_eig_2x2(c3):
    """Smallest eigenvalue of symmetric 2x2 matrices given as (xx, xy, yy)."""
    c3 = np.asarray(c3, float)
    a, b, d = c3[..., 0], c3[..., 1], c3[..., 2]
    return 0.5 * (a + d) - np.sqrt(0.25 * (a - d) ** 2 + b ** 2)


def v1_most_likely(w, mu, S):
    """w (..., K), mu (..., K, 2), S (..., K, 2, 2) -> component with the largest weight (first on ties)."""
    w = np.asarray(w)
    i = np.argmax(w, axis=-1)
    mu1 = np.take_along_axis(np.asarray(mu), i[..., None, None], axis=-2)[..., 0, :]
    S1 = np.take_along_axis(np.asarray(S), i[..., None, None, None], axis=-3)[..., 0, :, :]
    return mu1, S1, i


def v2_moment_match(w, mu, S):
    w = np.asarray(w, float)
    w = w / np.sum(w, axis=-1, keepdims=True)
    mu = np.asarray(mu, float)
    S = np.asarray(S, float)
    m = np.sum(w[..., None] * mu, axis=-2)
    d = mu - m[..., None, :]
    C = np.sum(w[..., None, None] * (S + d[..., :, None] * d[..., None, :]), axis=-3)
    return m, C


def weight_summary(w):
    """Largest weight, its index, entropy (nats) and effective number of components 1 / sum w^2."""
    w = np.asarray(w, float)
    w = w / np.sum(w, axis=-1, keepdims=True)
    with np.errstate(divide="ignore", invalid="ignore"):
        ent = -np.sum(np.where(w > 0, w * np.log(w), 0.0), axis=-1)
    return np.max(w, axis=-1), np.argmax(w, axis=-1), ent, 1.0 / np.sum(w ** 2, axis=-1)


def node_seed(scene, k, node_id, base):
    """Per-(scene, keyframe, node) torch seed, independent of process, worker and node iteration order."""
    h = hashlib.sha256(("%s|%d|%s|%d" % (scene, int(k), node_id, int(base))).encode()).hexdigest()
    return int(h[:8], 16)


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()
