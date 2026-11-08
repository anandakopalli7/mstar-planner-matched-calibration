"""av2_common_v02 (Claude line, 5 Nov 2026) = av2_common_v01 verbatim plus the 375-log additions of
AV2_TRACKER_PORT_DESIGN_v04.md sections 2, 3 and 5 (v01 is kept unchanged):
  * AV2_TRAIN225 and log_dir(log): 30_DATA/av2_val/<log> or 30_DATA/av2_train225/<log>; exactly one must exist, else raise;
  * sweep_timestamps(log): the local lidar folder when it holds .feather files (v01's rule, the 150 val logs), otherwise the
    recorded bucket listing <log_dir>/lidar_keys_v01.csv (key, size, etag; written by av2_fetch_v05); frame_timestamps as v01;
  * DET_PATHS["owncp"] = (val150 npz, held225 npz) of our own CenterPoint, DET_SHA256 from its SHA256SUMS.txt,
    DET_HAS_VELO["owncp"] = True, det_sources(name) -> tuple of source files;
  * read_logs_file(path), val_logs(), log_part(log).
Every v01 constant and function is unchanged.

av2_common_v01: constants and helpers of the Argoverse 2 tracker port (Claude line, 1 Nov 2026).

See AV2_TRACKER_PORT_DESIGN_v01.md sections 2-4. Nothing here reads ground truth; nothing here computes any outcome.
"""
import csv
import hashlib
import json
import math
import os

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
AV2_VAL = os.path.join(W_ROOT, "30_DATA", "av2_val")
AV2_TRAIN225 = os.path.join(W_ROOT, "30_DATA", "av2_train225")          # v02
DATA_ROOTS = (("val150", AV2_VAL), ("held225", AV2_TRAIN225))         # v02: part name, root
LIDAR_LISTING = "lidar_keys_v01.csv"                                   # v02: recorded bucket listing in the log folder
OWNCP_DIR = os.path.join(W_ROOT, "30_DATA", "av2_det_owncp_v01")      # v02
LOGS_375 = os.path.join(W_ROOT, "30_DATA", "av2_trk_v02", "C1_LOGS_375_v01.json")  # v02
DET_PATHS = {
    "lt3d": os.path.join(W_ROOT, "30_DATA", "av2_det_v01", "lt3d_centerpoint", "av2val_lt3d_centerpoint_dets_v01.npz"),
    "voxelnext": os.path.join(W_ROOT, "30_DATA", "av2_det_v01", "voxelnext", "av2val_voxelnext_dets_v01.npz"),
    # v02: our own CenterPoint (trained on the 475 other train logs), two parts in this order
    "owncp": (os.path.join(OWNCP_DIR, "val150", "av2val150_owncp_centerpoint_dets_v01.npz"),
              os.path.join(OWNCP_DIR, "held225", "av2held225_owncp_centerpoint_dets_v01.npz")),
}
# v02: expected SHA-256 of the own detector's npz files (30_DATA/av2_det_owncp_v01/SHA256SUMS.txt, e8dad0a8...)
DET_SHA256 = {
    "owncp": ("3ce5e3724da3998fbdbf8057f29bccb3fa15043eafab1e2899a8a78516e48073",
              "3b06178f44d08af8cbc8a63af2d1c1c641c0b998c24d43d8240602f71cbbfa80"),
}
DET_HAS_VELO = {"lt3d": True, "voxelnext": False, "owncp": True}
FRAME_STEP = 5           # every 5th lidar sweep, starting at sweep 0 (LT3D VAL_SAMPLE_RATE)
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


def sweep_timestamps_v01(log_id):
    """v01's sweep_timestamps, verbatim (kept for the equivalence test)."""
    d = os.path.join(AV2_VAL, log_id, "sensors", "lidar")
    return sorted(int(f[:-8]) for f in os.listdir(d) if f.endswith(".feather"))


# ---------------------------------------------------------------- v02: data roots, sweep lists, log lists, detectors


def log_dir(log_id):
    """30_DATA/av2_val/<log> or 30_DATA/av2_train225/<log>; exactly one must be an existing directory."""
    if not log_id or os.sep in log_id or "/" in log_id or ".." in log_id:
        raise ValueError("bad log id %r" % (log_id,))
    hits = [os.path.join(r, log_id) for _, r in DATA_ROOTS if os.path.isdir(os.path.join(r, log_id))]
    if len(hits) != 1:
        raise FileNotFoundError("log %s resolves to %d data roots (exactly one required): %s" % (log_id, len(hits), hits))
    return hits[0]


def log_part(log_id):
    """'val150' or 'held225' by the data root the log resolves to."""
    d = os.path.dirname(log_dir(log_id))
    for part, r in DATA_ROOTS:
        if os.path.normcase(os.path.abspath(r)) == os.path.normcase(os.path.abspath(d)):
            return part
    raise RuntimeError("unreachable")


def listing_timestamps(path, log_id):
    """Sweep timestamps from a recorded bucket listing (av2_fetch_v05): every key must be
    datasets/av2/sensor/<split>/<log>/sensors/lidar/<digits>.feather with size > 0; stems unique; non-empty."""
    ts = []
    with open(path, newline="") as f:
        rd = csv.reader(f)
        head = next(rd)
        if head != ["key", "size", "etag"]:
            raise ValueError("%s: unexpected header %s" % (path, head))
        for row in rd:
            if len(row) != 3:
                raise ValueError("%s: bad row %s" % (path, row))
            key, size = row[0], int(row[1])
            mid = "/%s/sensors/lidar/" % log_id
            stem = key.rsplit("/", 1)[-1][:-8]
            if not (key.startswith("datasets/av2/sensor/") and mid in key and key.endswith(".feather")
                    and key.split(mid, 1)[1] == stem + ".feather" and stem.isdigit() and size > 0):
                raise ValueError("%s: key not a lidar sweep of %s: %s" % (path, log_id, key))
            ts.append(int(stem))
    if not ts or len(set(ts)) != len(ts):
        raise ValueError("%s: empty or duplicate sweep stems" % path)
    return sorted(ts)


def sweep_timestamps(log_id):
    """v02 sweep-list rule (design v04 section 3): the local lidar folder when it holds .feather files (v01's rule),
    otherwise the recorded bucket listing in the log folder; raise if neither."""
    d = log_dir(log_id)
    lid = os.path.join(d, "sensors", "lidar")
    if os.path.isdir(lid):
        ts = sorted(int(f[:-8]) for f in os.listdir(lid) if f.endswith(".feather"))
        if ts:
            return ts
    lst = os.path.join(d, LIDAR_LISTING)
    if os.path.isfile(lst):
        return listing_timestamps(lst, log_id)
    raise FileNotFoundError("log %s: no lidar .feather files and no %s" % (log_id, LIDAR_LISTING))


def frame_timestamps(log_id):
    return sweep_timestamps(log_id)[::FRAME_STEP]


def val_logs():
    """v01's default log set: the log folders of 30_DATA/av2_val, sorted."""
    return sorted(d for d in os.listdir(AV2_VAL) if os.path.isdir(os.path.join(AV2_VAL, d)))


def read_logs_file(path, key="logs"):
    """A JSON list of log ids, or a JSON object whose `key` holds one. Returns the sorted list; refuses duplicates."""
    with open(path) as f:
        d = json.load(f)
    logs = d if isinstance(d, list) else d[key]
    logs = [str(x) for x in logs]
    if len(set(logs)) != len(logs):
        raise ValueError("duplicate log ids in %s" % path)
    return sorted(logs)


def det_sources(name):
    """Tuple of the detection npz files of a detector (one for lt3d / voxelnext, two for owncp)."""
    p = DET_PATHS[name]
    return (p,) if isinstance(p, str) else tuple(p)


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
