"""av2_common_v01: constants and helpers of the Argoverse 2 tracker port (Claude line, 1 Nov 2026).

See AV2_TRACKER_PORT_DESIGN_v01.md sections 2-4. Nothing here reads ground truth; nothing here computes any outcome.
"""
import hashlib
import math
import os

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AV2_VAL = os.path.join(W_ROOT, "30_DATA", "av2_val")
DET_PATHS = {
    "lt3d": os.path.join(W_ROOT, "30_DATA", "av2_det_v01", "lt3d_centerpoint", "av2val_lt3d_centerpoint_dets_v01.npz"),
    "voxelnext": os.path.join(W_ROOT, "30_DATA", "av2_det_v01", "voxelnext", "av2val_voxelnext_dets_v01.npz"),
}
DET_HAS_VELO = {"lt3d": True, "voxelnext": False}
FRAME_STEP = 5            # every 5th lidar sweep, starting at sweep 0 (LT3D VAL_SAMPLE_RATE)
RANGE_SQUARE_M = 54.0     # tracker input: ego-frame BEV square |x|, |y| <= 54 m (LT3D's range) for both detectors

# design section 4.2: AV2 category -> the nuScenes tracking class whose tracker parameters are used
TRACKER_MAP = {
    "REGULAR_VEHICLE": "car",
    "PEDESTRIAN": "pedestrian",
    "BICYCLIST": "bicycle",
    "MOTORCYCLIST": "motorcycle",
    "BUS": "bus", "ARTICULATED_BUS": "bus", "SCHOOL_BUS": "bus",
    "TRUCK": "truck", "BOX_TRUCK": "truck", "TRUCK_CAB": "truck", "LARGE_VEHICLE": "truck",
    "VEHICULAR_TRAILER": "trailer",
}
# design section 4.1: analysis groups (D15 section 3.5); the others are descriptive only
ANALYSIS_GROUP = {"car": "car", "pedestrian": "pedestrian", "bicycle": "cyclist",
                  "motorcycle": "motorcyclist_descr", "bus": "large_descr", "truck": "large_descr", "trailer": "large_descr"}
ANALYSIS_GROUPS_D15 = ("car", "pedestrian", "cyclist")
# rule RB-1 (design section 4.3): rider class -> vehicle-part class, BEV IoU threshold
RIDDEN = {"BICYCLIST": "BICYCLE", "MOTORCYCLIST": "MOTORCYCLE"}
RB_IOU = 0.10
# nuScenes tracking_nips_2019 class ranges (m), used by the tracking metrics' range filter
CLASS_RANGE = {"car": 50, "truck": 50, "bus": 50, "trailer": 50, "pedestrian": 40, "motorcycle": 40, "bicycle": 40}


def token(log_id, ts_ns):
    return "%s_%d" % (log_id, int(ts_ns))


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def sweep_timestamps(log_id):
    d = os.path.join(AV2_VAL, log_id, "sensors", "lidar")
    return sorted(int(f[:-8]) for f in os.listdir(d) if f.endswith(".feather"))


def frame_timestamps(log_id):
    return sweep_timestamps(log_id)[::FRAME_STEP]


# ---------------------------------------------------------------- quaternions (w, x, y, z), vectorised


def qmul(a, b):
    """Hamilton product a * b for arrays of shape (..., 4)."""
    aw, ax, ay, az = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    bw, bx, by, bz = b[..., 0], b[..., 1], b[..., 2], b[..., 3]
    return np.stack([aw * bw - ax * bx - ay * by - az * bz,
                     aw * bx + ax * bw + ay * bz - az * by,
                     aw * by - ax * bz + ay * bw + az * bx,
                     aw * bz + ax * by - ay * bx + az * bw], -1)


def qrot_matrix(q):
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.stack([
        np.stack([1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)], -1),
        np.stack([2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)], -1),
        np.stack([2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)], -1)], -2)


def qyaw(q):
    """Same formula as x1_lib_v03.quat_yaw, vectorised."""
    w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    return np.arctan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


class Poses:
    """city_SE3_egovehicle of one log, looked up by exact timestamp (no interpolation)."""

    def __init__(self, table):
        self.t = np.asarray(table["timestamp_ns"], dtype=np.int64)
        o = np.argsort(self.t, kind="stable")
        self.t = self.t[o]
        self.q = np.stack([table["qw"], table["qx"], table["qy"], table["qz"]], -1)[o]
        self.p = np.stack([table["tx_m"], table["ty_m"], table["tz_m"]], -1)[o]

    def index(self, ts):
        ts = np.asarray(ts, dtype=np.int64)
        i = np.searchsorted(self.t, ts)
        i = np.minimum(i, len(self.t) - 1)
        if not np.all(self.t[i] == ts):
            raise KeyError("pose missing at %d timestamp(s)" % int(np.sum(self.t[i] != ts)))
        return i

    def to_city(self, ts, t_ego, q_ego, v_ego=None):
        """Ego-frame centres (n,3), quaternions (n,4) and optional planar velocities (n,2) at timestamps ts -> city frame."""
        i = self.index(ts)
        R = qrot_matrix(self.q[i])
        t_city = np.einsum("nij,nj->ni", R, t_ego) + self.p[i]
        q_city = qmul(self.q[i], q_ego)
        v_city = None
        if v_ego is not None:
            v3 = np.concatenate([v_ego, np.zeros((len(v_ego), 1))], 1)
            v_city = np.einsum("nij,nj->ni", R, v3)[:, :2]
        return t_city, q_city, v_city


def bev_rect(cx, cy, yaw, length, width):
    from shapely.geometry import Polygon
    c, s = math.cos(yaw), math.sin(yaw)
    hl, hw = length / 2, width / 2
    return Polygon([(cx + c * dx - s * dy, cy + s * dx + c * dy) for dx, dy in ((hl, hw), (hl, -hw), (-hl, -hw), (-hl, hw))])


def bev_iou(a, b):
    inter = a.intersection(b).area
    u = a.area + b.area - inter
    return inter / u if u > 0 else 0.0


# ---------------------------------------------------------------- memory-light npz column reader


def npz_columns(path):
    import zipfile
    with zipfile.ZipFile(path) as zf:
        return [n[:-4] for n in zf.namelist() if n.endswith(".npy")]


def npz_select(path, key, keep=None, chunk_rows=1 << 20, transform=None):
    """Read one 1-D column of an .npz in chunks (no pickle: object dtypes are refused) and return
    transform(chunk)[keep[chunk]] concatenated; transform defaults to identity. Peak memory ~ one chunk."""
    import zipfile
    from numpy.lib import format as npf
    out = []
    with zipfile.ZipFile(path) as zf, zf.open(key + ".npy") as fh:
        major, minor = npf.read_magic(fh)
        shape, fortran, dtype = npf._read_array_header(fh, (major, minor))
        if dtype.hasobject or len(shape) != 1 or fortran:
            raise ValueError("refusing column %s: dtype %s shape %s" % (key, dtype, shape))
        n, done = shape[0], 0
        while done < n:
            m = min(chunk_rows, n - done)
            buf = fh.read(m * dtype.itemsize)
            a = np.frombuffer(buf, dtype=dtype, count=m)
            if transform is not None:
                a = transform(a)
            out.append(a if keep is None else a[keep[done:done + m]])
            done += m
    return np.concatenate(out) if out else np.array([], dtype)
