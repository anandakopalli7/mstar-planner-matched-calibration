#!/usr/bin/env python3
"""X1/X2 analysis library v03 (Claude line, 30 Oct 2026): v02 with memory reductions for the 700-scene train analysis
(R05 M5): build_table keeps only paired, uncensored rows unless keep_unpaired=True (unpaired and censored rows are never
used downstream; their counts are kept); load_horizon can keep only needed keys. Analysis logic is unchanged from v02.
Changes from v01 follow review R03: separating-axis filter and orientation null (C1), four class groups (M8),
bike-rack filter, contested-pair and first-record flags (M1, m7), in-path for every record (m6), ego centre offset and
signed speed (m11), zero-SE handling (m12), log-cluster bootstrap (m9), logit-scale fallback band (M3).
"""
import gzip
import hashlib
import json
import math
from collections import defaultdict

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import norm

Z95 = float(norm.ppf(0.95))
DELTA = 0.05
SIGMA_A = 0.10
H0 = 0.10
GATE = 2.0
SEED = 20261030
MIN_SCENES = 39
GROUP = {"car": "car", "pedestrian": "pedestrian", "motorcycle": "two_wheeler", "bicycle": "two_wheeler",
         "truck": "large", "bus": "large", "trailer": "large"}
GROUPS = ["car", "pedestrian", "two_wheeler", "large"]
RANGES = ["<20", "20-40", ">=40"]
AXES = ["long", "lat"]
CELLS = [(g, r, a) for g in GROUPS for r in RANGES for a in AXES]
EGO_L, EGO_W, BUFFER, REAR_AXLE_TO_CENTRE = 4.1, 1.8, 0.5, 1.39
STEPS = np.arange(9) * 0.5
N_NULL = 20


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def quat_yaw(q):
    w, x, y, z = q
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def range_bin(d):
    return "<20" if d < 20 else ("20-40" if d < 40 else ">=40")


def rect(cx, cy, yaw, length, width):
    from shapely.geometry import Polygon
    c, s = math.cos(yaw), math.sin(yaw)
    hl, hw = length / 2, width / 2
    return Polygon([(cx + c * dx - s * dy, cy + s * dx + c * dy) for dx, dy in ((hl, hw), (hl, -hw), (-hl, -hw), (-hl, hw))])


def in_rect(px, py, cx, cy, yaw, length, width):
    c, s = math.cos(yaw), math.sin(yaw)
    dx, dy = px - cx, py - cy
    return abs(c * dx + s * dy) <= length / 2 and abs(-s * dx + c * dy) <= width / 2


def ego_centre(x, y, yaw):
    return x + REAR_AXLE_TO_CENTRE * math.cos(yaw), y + REAR_AXLE_TO_CENTRE * math.sin(yaw)


def ego_corridor(x, y, yaw, v, w):
    """CTRV of the rear-axle origin; footprints centred on the ego centre, inflated by BUFFER."""
    from shapely.ops import unary_union
    polys = []
    for t in STEPS:
        if abs(w) < 1e-4:
            xt, yt, ht = x + v * t * math.cos(yaw), y + v * t * math.sin(yaw), yaw
        else:
            ht = yaw + w * t
            xt = x + v / w * (math.sin(ht) - math.sin(yaw))
            yt = y - v / w * (math.cos(ht) - math.cos(yaw))
        cx, cy = ego_centre(xt, yt, ht)
        polys.append(rect(cx, cy, ht, EGO_L + 2 * BUFFER, EGO_W + 2 * BUFFER))
    return unary_union(polys)


def object_in_path(prep_corr, reach, ex, ey, ox, oy, yaw, vx, vy, w, l):
    if math.hypot(ox - ex, oy - ey) > reach + 4.0 * math.hypot(vx, vy) + max(w, l):
        return False
    for t in STEPS:
        if prep_corr.intersects(rect(ox + vx * t, oy + vy * t, yaw, l, w)):
            return True
    return False


def load_export(path):
    recs = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            c = r["cov9"]
            recs.append({"scene": r["scene"], "k": r["frame_id"], "tid": r["tracking_id"], "name": r["tracking_name"],
                         "x": r["translation"][0], "y": r["translation"][1], "w": r["size"][0], "l": r["size"][1],
                         "yaw": quat_yaw(r["rotation"]), "vx": r["velocity"][0], "vy": r["velocity"][1],
                         "S": (c[0][0], c[0][1], c[1][1]),
                         "c6": (abs(r["translation"][0] - r["state10"][0]) + abs(r["translation"][1] - r["state10"][1])) if r.get("state10") else None})
    return recs


def load_gt(path):
    g = json.load(open(path))
    samples = {s["token"]: s for s in g["samples"]}
    by_sample, racks = defaultdict(list), defaultdict(list)
    for a in g["annotations"]:
        by_sample[a["sample_token"]].append(a)
    for r in g.get("bicycle_racks", []):
        racks[r["sample_token"]].append(r)
    return samples, by_sample, racks


def build_table(recs, samples, gt_by_sample, racks_by_sample, gate=GATE, persistent=True, scene_log=None, keep_unpaired=False):
    """All records at k >= 1 with flags. Pairing: persistent (v02 primary) or per-frame re-matching (sensitivity)."""
    by_scene = defaultdict(lambda: defaultdict(list))
    for r in recs:
        by_scene[r["scene"]][r["k"]].append(r)
    scene_tokens = defaultdict(dict)
    for s in samples.values():
        scene_tokens[s["scene"]][s["index"]] = s
    rows, st = [], defaultdict(int)
    from shapely.prepared import prep
    for scene, frames in by_scene.items():
        pairs, owner, first_k = {}, {}, {}
        for k in sorted(frames):
            fr = frames[k]
            smp = scene_tokens[scene][k]
            rk = racks_by_sample.get(smp["token"], [])
            def rack_hit(px, py):
                return any(in_rect(px, py, q["translation"][0], q["translation"][1], q["yaw"], q["size"][1], q["size"][0]) for q in rk)
            gts = [a for a in gt_by_sample.get(smp["token"], []) if a["num_pts"] >= 1
                   and not (a["tracking_name"] in ("bicycle", "motorcycle") and rack_hit(a["translation"][0], a["translation"][1]))]
            ann_by_inst = {a["instance_token"]: a for a in gts}
            for r in fr:
                first_k.setdefault(r["tid"], k)
            live = {r["tid"] for r in fr}
            frame_pairs = {} if not persistent else None
            for cls in GROUP:
                if persistent:
                    trk = [r for r in fr if r["tid"] not in pairs and r["name"] == cls]
                    cand = [a for a in gts if a["tracking_name"] == cls
                            and not (a["instance_token"] in owner and owner[a["instance_token"]] in live)]
                else:
                    trk = [r for r in fr if r["name"] == cls]
                    cand = [a for a in gts if a["tracking_name"] == cls]
                if not trk or not cand:
                    continue
                D = np.array([[math.hypot(r["x"] - a["translation"][0], r["y"] - a["translation"][1]) for a in cand] for r in trk])
                ri, ci = linear_sum_assignment(np.where(D <= gate, D, 1e6))
                for i, j in zip(ri, ci):
                    if D[i, j] <= gate:
                        tid, inst = trk[i]["tid"], cand[j]["instance_token"]
                        if persistent:
                            pairs[tid] = inst
                            if inst in owner and owner[inst] != tid:
                                st["id_switches"] += 1
                            owner[inst] = tid
                        else:
                            frame_pairs[tid] = inst
            cur = pairs if persistent else frame_pairs
            n_live_on = defaultdict(int)
            for r in fr:
                if r["tid"] in cur:
                    n_live_on[cur[r["tid"]]] += 1
            if k == 0:
                st["frame0_records"] += len(fr)
                continue
            prev = scene_tokens[scene][k - 1]
            ex, ey, eyaw = smp["ego_xyz"][0], smp["ego_xyz"][1], smp["ego_yaw"]
            dt = 1e-6 * (smp["timestamp"] - prev["timestamp"])
            dx, dy = ex - prev["ego_xyz"][0], ey - prev["ego_xyz"][1]
            v = (dx * math.cos(eyaw) + dy * math.sin(eyaw)) / dt
            w = wrap(eyaw - prev["ego_yaw"]) / dt
            cg = ego_corridor(ex, ey, eyaw, v, w)
            corr, reach = prep(cg), abs(v) * 4.0 + EGO_L + 2 * BUFFER + REAR_AXLE_TO_CENTRE
            cx, cy = ego_centre(ex, ey, eyaw)
            for r in fr:
                st["records_k_ge_1"] += 1
                if r["name"] in ("bicycle", "motorcycle") and rack_hit(r["x"], r["y"]):
                    st["track_in_rack"] += 1
                    continue
                inpath = object_in_path(corr, reach, cx, cy, r["x"], r["y"], r["yaw"], r["vx"], r["vy"], r["w"], r["l"])
                st["inpath_records"] += int(inpath)
                row = {"scene": scene, "log": scene_log.get(scene) if scene_log else None, "k": k, "tid": r["tid"], "name": r["name"],
                       "group": GROUP[r["name"]], "range": range_bin(math.hypot(r["x"] - cx, r["y"] - cy)), "inpath": inpath,
                       "cx": cx, "cy": cy, "eyaw": eyaw, "mx": r["x"], "my": r["y"], "yaw": r["yaw"], "w": r["w"], "l": r["l"],
                       "S": r["S"], "first": first_k[r["tid"]] == k, "c6": r.get("c6"), "paired": False}
                if r["tid"] not in cur:
                    st["unpaired"] += 1
                    st["unpaired_inpath"] += int(inpath)
                    if keep_unpaired:
                        rows.append(row)
                    continue
                a = ann_by_inst.get(cur[r["tid"]])
                if a is None:
                    st["censored"] += 1
                    if keep_unpaired:
                        rows.append(row)
                    continue
                d_pair = math.hypot(r["x"] - a["translation"][0], r["y"] - a["translation"][1])
                closer = any(b["tracking_name"] == r["name"] and b["instance_token"] != a["instance_token"]
                             and math.hypot(r["x"] - b["translation"][0], r["y"] - b["translation"][1]) < d_pair for b in gts)
                row.update({"paired": True, "inst": a["instance_token"], "gx": a["translation"][0], "gy": a["translation"][1],
                            "contested": bool(closer or n_live_on[cur[r["tid"]]] >= 2), "resid_gt_gate": d_pair > gate})
                st["paired_inpath"] += int(inpath)
                rows.append(row)
            for r in fr:
                dup = any(q is not r and q["name"] == r["name"] and math.hypot(q["x"] - r["x"], q["y"] - r["y"]) < 1.0 for q in fr)
                st["duplicate_records_1m"] += int(dup)
    return rows, dict(st)


def axis_candidates(row):
    """For both object axes: unit vector a, separation along a (ego centre minus estimate), and h_obj + h_ego."""
    c, s = math.cos(row["yaw"]), math.sin(row["yaw"])
    ue, ve = (math.cos(row["eyaw"]), math.sin(row["eyaw"])), (-math.sin(row["eyaw"]), math.cos(row["eyaw"]))
    dvec = (row["cx"] - row["mx"], row["cy"] - row["my"])
    out = []
    for name, a, h_obj in (("long", (c, s), row["l"] / 2), ("lat", (-s, c), row["w"] / 2)):
        h_ego = (EGO_L / 2 + BUFFER) * abs(a[0] * ue[0] + a[1] * ue[1]) + (EGO_W / 2 + BUFFER) * abs(a[0] * ve[0] + a[1] * ve[1])
        out.append((name, a, a[0] * dvec[0] + a[1] * dvec[1], h_obj + h_ego))
    return out


def cell_items(rows, sigma_a=SIGMA_A, inpath_only=True, exclude_contested=False, exclude_first=False,
               orient="estimate", sigma_fn=None, need_paired=True):
    """Per cell arrays over separating (record, axis) items. orient: 'estimate' (primary) or 'truth' (secondary)."""
    scenes = sorted({r["scene"] for r in rows})
    logs = sorted({r["log"] for r in rows if r["log"] is not None})
    sidx, lidx = {s: i for i, s in enumerate(scenes)}, {l: i for i, l in enumerate(logs)}
    acc = {c: defaultdict(list) for c in CELLS}
    for r in rows:
        if (need_paired and not r["paired"]) or (inpath_only and not r["inpath"]):
            continue
        if exclude_contested and r.get("contested"):
            continue
        if exclude_first and r["first"]:
            continue
        sa = sigma_fn(r) if sigma_fn else sigma_a
        sxx, sxy, syy = r["S"]
        for name, a, sep, hsum in axis_candidates(r):
            var = a[0] * a[0] * sxx + 2 * a[0] * a[1] * sxy + a[1] * a[1] * syy
            c = (r["group"], r["range"], name)
            item = acc[c]
            item["a0"].append(a[0]); item["a1"].append(a[1]); item["sep"].append(sep); item["hsum"].append(hsum)
            item["var"].append(var); item["sa"].append(sa); item["sxx"].append(sxx); item["sxy"].append(sxy); item["syy"].append(syy)
            item["s"].append(sidx[r["scene"]]); item["lg"].append(lidx.get(r["log"], -1))
            item["name"].append(r["name"]); item["drift"].append(bool(r.get("resid_gt_gate", False)))
            if r["paired"]:
                proj = a[0] * (r["gx"] - r["mx"]) + a[1] * (r["gy"] - r["my"])
                if orient == "estimate":
                    sep_o = sep
                else:
                    sep_o = a[0] * (r["cx"] - r["gx"]) + a[1] * (r["cy"] - r["gy"])
                keep = abs(sep_o) > hsum
                sign = 1.0 if sep_o >= 0 else -1.0
                item["keep"].append(keep); item["D"].append(sign * proj)
            else:
                item["keep"].append(abs(sep) > hsum); item["D"].append(np.nan)
    out = {}
    for c in CELLS:
        d = {k: np.asarray(v) for k, v in acc[c].items()}
        if not d:
            out[c] = {"n": 0, "n_scenes": 0, "U": np.array([]), "D": np.array([]), "V": np.array([]), "SA": np.array([]),
                      "s": np.array([], int), "lg": np.array([], int), "all": None, "names": np.array([]), "drift": np.array([], bool)}
            continue
        k = d["keep"].astype(bool)
        V = d["var"][k] + d["sa"][k] ** 2
        out[c] = {"n": int(k.sum()), "n_scenes": int(len(np.unique(d["s"][k]))), "U": d["D"][k] / np.sqrt(V), "D": d["D"][k],
                  "V": d["var"][k], "SA": d["sa"][k], "s": d["s"][k].astype(int), "lg": d["lg"][k].astype(int), "all": d,
                  "names": d["name"][k], "drift": d["drift"][k].astype(bool)}
    return out, scenes, logs


def orientation_null(cells, rng, n_draw=N_NULL):
    """E0_g and m0_g: exceedance and 0.95 quantile of U under a perfectly calibrated (fixed-truth) tracker at the observed
    geometry, with the separating filter and orientation re-evaluated on the pseudo-estimate (R03 C1). No ground truth."""
    res = {}
    for c, d in cells.items():
        A = d["all"]
        if A is None or len(A["var"]) == 0:
            res[c] = (None, None)
            continue
        n = len(A["var"])
        cov = np.stack([np.stack([A["sxx"] + A["sa"] ** 2, A["sxy"]], -1), np.stack([A["sxy"], A["syy"] + A["sa"] ** 2], -1)], -2)
        L = np.linalg.cholesky(cov)
        z = rng.standard_normal((n_draw, n, 2))
        e = np.einsum("nij,mnj->mni", L, z)
        ae = A["a0"] * e[..., 0] + A["a1"] * e[..., 1]
        sep_p = A["sep"] - ae
        keep = np.abs(sep_p) > A["hsum"]
        U0 = np.where(sep_p >= 0, 1.0, -1.0) * (-ae) / np.sqrt(A["var"] + A["sa"] ** 2)
        if keep.sum() == 0:
            res[c] = (None, None)
            continue
        res[c] = (float(np.mean(U0[keep] > Z95)), float(np.quantile(U0[keep], 0.95)))
    return res


def sums_by(idx, values, n):
    return np.bincount(idx, weights=values, minlength=n)


def boot_weights(n, B, rng):
    return rng.multinomial(n, np.full(n, 1.0 / n), size=B).astype(float)


def log_cluster_weights(scene_log_idx, n_logs, B, rng):
    """Scene weights from resampling logs with replacement."""
    lw = rng.multinomial(n_logs, np.full(n_logs, 1.0 / n_logs), size=B).astype(float)
    return lw[:, scene_log_idx]


def sup_t_band(est, boot, logit=False, level=0.95):
    """Two-sided simultaneous sup-t band (default 95 %) with bootstrap SE; optional logit scale. Zero-SE cells flagged."""
    eps = 1e-6
    if logit:
        f = lambda p: np.log(np.clip(p, eps, 1 - eps) / (1 - np.clip(p, eps, 1 - eps)))
        e, b = f(est), f(boot)
    else:
        e, b = est, boot
    se = b.std(axis=0, ddof=1)
    zero = se <= 0
    se_safe = np.where(zero, np.nan, se)
    t = np.nanmax(np.abs(b - e) / se_safe, axis=1)
    q = float(np.nanquantile(t, level)) if np.isfinite(t).any() else float("nan")
    lo, hi = e - q * se_safe, e + q * se_safe
    if logit:
        g = lambda x: 1 / (1 + np.exp(-x))
        lo, hi = g(lo), g(hi)
    return lo, hi, q, zero


def verdicts(est, lo, hi, zero, thr):
    out = []
    for e, l_, h_, z0, t in zip(est, lo, hi, zero, thr):
        if z0:
            out.append("FAILS" if e > t else ("OVERCOVERS" if e < DELTA else "CONSISTENT"))
        elif l_ > t:
            out.append("FAILS")
        elif h_ < DELTA:
            out.append("OVERCOVERS")
        else:
            out.append("CONSISTENT")
    return out


def crc_threshold(U, s, delta=DELTA):
    scenes = np.unique(s)
    n = len(scenes)
    if n == 0 or (1.0 / (n + 1)) > delta:
        return None
    idx = {sc: i for i, sc in enumerate(scenes)}
    si = np.array([idx[x] for x in s])
    tot = np.bincount(si, minlength=n).astype(float)
    order = np.sort(np.unique(U))

    def ok(c):
        L = np.bincount(si, weights=(U > c).astype(float), minlength=n) / tot
        return n / (n + 1) * L.mean() + 1 / (n + 1) <= delta
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


def inflation_needed(D, V, SA, delta=DELTA):
    """Smallest s with mean(D > z sqrt(s V + sa^2)) <= delta; returns (s, cap_hit)."""
    def exc(sv):
        return np.mean(D > Z95 * np.sqrt(sv * V + SA ** 2))
    lo, hi = 1e-3, 1e4
    if exc(lo) <= delta:
        return lo, True
    if exc(hi) > delta:
        return hi, True
    for _ in range(60):
        mid = math.sqrt(lo * hi)
        if exc(mid) <= delta:
            hi = mid
        else:
            lo = mid
    return hi, False


def expand(d, cnt):
    rep = cnt[d["s"]]
    idx = np.repeat(np.arange(d["n"]), rep)
    copy = np.concatenate([np.arange(k) for k in rep]) if d["n"] else np.array([], int)
    return {"D": d["D"][idx], "V": d["V"][idx], "SA": d["SA"][idx], "U": d["U"][idx], "s": d["s"][idx] * 1000 + copy, "n": len(idx)}


def build_horizon_rows(rows, pred, samples, gt_by_sample, racks_by_sample, key="h2s", steps=4):
    """Horizon family: predicted mean/covariance at k + steps keyframes against the paired instance's annotation at k + steps;
    ego pose at k + steps predicted by CTRV from the poses at k - 1 and k (I_k-measurable, R04 m10). Record selection (k >= 1, in-path at k, rack exclusion) is inherited from the t = 0 rows."""
    scene_tokens = defaultdict(dict)
    for s in samples.values():
        scene_tokens[s["scene"]][s["index"]] = s
    out, st = [], defaultdict(int)
    for r in rows:
        h = dict(r)
        p = pred.get((r["scene"], r["k"], r["tid"]))
        fut = scene_tokens[r["scene"]].get(r["k"] + steps)
        if p is None or fut is None:
            st["no_future_frame"] += 1
            continue
        x, y, sxx, sxy, syy = p[key]
        now, prev = scene_tokens[r["scene"]][r["k"]], scene_tokens[r["scene"]][r["k"] - 1]
        dt = 1e-6 * (now["timestamp"] - prev["timestamp"])
        ex, ey, eyaw = now["ego_xyz"][0], now["ego_xyz"][1], now["ego_yaw"]
        v = ((ex - prev["ego_xyz"][0]) * math.cos(eyaw) + (ey - prev["ego_xyz"][1]) * math.sin(eyaw)) / dt
        w = wrap(eyaw - prev["ego_yaw"]) / dt
        th = steps * 0.5
        if abs(w) < 1e-4:
            px, py, pyaw = ex + v * th * math.cos(eyaw), ey + v * th * math.sin(eyaw), eyaw
        else:
            pyaw = eyaw + w * th
            px, py = ex + v / w * (math.sin(pyaw) - math.sin(eyaw)), ey - v / w * (math.cos(pyaw) - math.cos(eyaw))
        cx, cy = ego_centre(px, py, pyaw)
        h.update({"mx": x, "my": y, "S": (sxx, sxy, syy), "cx": cx, "cy": cy, "eyaw": pyaw,
                  "range": range_bin(math.hypot(x - cx, y - cy)), "c6": None})
        if r["paired"]:
            rk = racks_by_sample.get(fut["token"], [])
            ann = next((a for a in gt_by_sample.get(fut["token"], []) if a["instance_token"] == r["inst"]), None)
            in_rack = ann is not None and ann["tracking_name"] in ("bicycle", "motorcycle") and any(
                in_rect(ann["translation"][0], ann["translation"][1], q["translation"][0], q["translation"][1], q["yaw"], q["size"][1], q["size"][0]) for q in rk)
            if ann is None or ann["num_pts"] < 1 or in_rack:
                h["paired"] = False
                st["censored_at_horizon"] += 1
            else:
                h["gx"], h["gy"] = ann["translation"][0], ann["translation"][1]
                h["resid_gt_gate"] = math.hypot(x - h["gx"], y - h["gy"]) > GATE
        out.append(h)
    return out, dict(st)


def load_horizon(path, keys=None):
    pred = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            r = json.loads(line)
            key = (r["scene"], r["k"], r["tid"])
            if keys is None or key in keys:
                pred[key] = {"h2s": r["h2s"]}
    return pred
