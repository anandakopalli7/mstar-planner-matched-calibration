#!/usr/bin/env python3
"""X1 analysis (Claude line, v01, 30 Oct 2026). Implements 40_PROTOCOL/X1_PREREGISTRATION_v01.md.

Modes
  selftest : known-answer tests on synthetic data (code checks only; never evidence)
  sizes    : pairing + in-path + cells -> record/scene counts and median exported SD per cell (no ground-truth residual)
  oc       : Q4 operating characteristics by simulation at the observed sizes
  full     : the pre-registered analysis; refuses to run unless the pre-registration hash matches its .sha256 file
Run inside the CANMOT environment (numpy, scipy, shapely 1.8).
"""
import argparse
import gzip
import hashlib
import json
import math
import os
import sys
import time
from collections import defaultdict

import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.stats import norm

Z95 = float(norm.ppf(0.95))
DELTA = 0.05
SIGMA_A = 0.10
GATE = 2.0
H0 = 0.10
SEED = 20261030
CLASS_GROUP = {"car": "car", "pedestrian": "pedestrian", "truck": "other", "bus": "other", "trailer": "other",
               "motorcycle": "other", "bicycle": "other"}
GROUPS = ["car", "pedestrian", "other"]
RANGES = ["<20", "20-40", ">=40"]
AXES = ["long", "lat"]
CELLS = [(g, r, a) for g in GROUPS for r in RANGES for a in AXES]
EGO_L, EGO_W, BUFFER = 4.1, 1.8, 0.5
STEPS = np.arange(9) * 0.5
MIN_SCENES = 39


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


# ------------------------------------------------------------------ geometry
def rect(cx, cy, yaw, length, width):
    from shapely.geometry import Polygon
    c, s = math.cos(yaw), math.sin(yaw)
    hl, hw = length / 2, width / 2
    pts = [(cx + c * dx - s * dy, cy + s * dx + c * dy) for dx, dy in ((hl, hw), (hl, -hw), (-hl, -hw), (-hl, hw))]
    return Polygon(pts)


def ego_corridor(x, y, yaw, v, w):
    from shapely.ops import unary_union
    polys = []
    for t in STEPS:
        if abs(w) < 1e-4:
            xt, yt, yt_ = x + v * t * math.cos(yaw), y + v * t * math.sin(yaw), yaw
        else:
            yt_ = yaw + w * t
            xt = x + v / w * (math.sin(yt_) - math.sin(yaw))
            yt = y - v / w * (math.cos(yt_) - math.cos(yaw))
        polys.append(rect(xt, yt, yt_, EGO_L + 2 * BUFFER, EGO_W + 2 * BUFFER))
    return unary_union(polys)


def object_in_path(prepared_corridor, corridor_reach, ex, ey, ox, oy, yaw, vx, vy, w, l):
    if math.hypot(ox - ex, oy - ey) > corridor_reach + 4.0 * math.hypot(vx, vy) + max(w, l):
        return False
    for t in STEPS:
        if prepared_corridor.intersects(rect(ox + vx * t, oy + vy * t, yaw, l, w)):
            return True
    return False


# ------------------------------------------------------------------ loading
def load_export(path):
    recs = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            c = r["cov9"]
            recs.append({"scene": r["scene"], "k": r["frame_id"], "token": r["sample_token"],
                         "tid": r["tracking_id"], "name": r["tracking_name"], "pool": r["pool"],
                         "x": r["translation"][0], "y": r["translation"][1],
                         "w": r["size"][0], "l": r["size"][1], "yaw": quat_yaw(r["rotation"]),
                         "vx": r["velocity"][0], "vy": r["velocity"][1],
                         "S": (c[0][0], c[0][1], c[1][1])})
    return recs


def load_gt(path):
    g = json.load(open(path))
    samples = {s["token"]: s for s in g["samples"]}
    by_sample = defaultdict(list)
    for a in g["annotations"]:
        by_sample[a["sample_token"]].append(a)
    return samples, by_sample


# ------------------------------------------------------------------ pairing and record table
def build_table(recs, samples, gt_by_sample, gate=GATE):
    """Pair tracks to instances (persistent), compute geometry; returns a list of row dicts and pairing stats."""
    by_scene = defaultdict(lambda: defaultdict(list))
    for r in recs:
        by_scene[r["scene"]][r["k"]].append(r)
    rows, stats = [], defaultdict(int)
    scene_tokens = defaultdict(dict)
    for s in samples.values():
        scene_tokens[s["scene"]][s["index"]] = s
    for scene, frames in by_scene.items():
        pairs, owner, ever = {}, {}, defaultdict(set)
        for k in sorted(frames):
            fr = frames[k]
            smp = scene_tokens[scene][k]
            gts = gt_by_sample.get(smp["token"], [])
            ann_by_inst = {a["instance_token"]: a for a in gts}
            live = {r["tid"] for r in fr}
            for cls in CLASS_GROUP:
                trk = [r for r in fr if r["tid"] not in pairs and r["name"] == cls]
                cand = [a for a in gts if a["tracking_name"] == cls and a["num_pts"] >= 1
                        and not (a["instance_token"] in owner and owner[a["instance_token"]] in live)]
                if not trk or not cand:
                    continue
                D = np.array([[math.hypot(r["x"] - a["translation"][0], r["y"] - a["translation"][1]) for a in cand] for r in trk])
                Dg = np.where(D <= gate, D, 1e6)
                ri, ci = linear_sum_assignment(Dg)
                for i, j in zip(ri, ci):
                    if D[i, j] <= gate:
                        tid, inst = trk[i]["tid"], cand[j]["instance_token"]
                        pairs[tid] = inst
                        if inst in owner and owner[inst] != tid:
                            stats["id_switches"] += 1
                        owner[inst] = tid
                        ever[inst].add(tid)
            if k == 0:
                stats["frame0_records"] += len(fr)
                continue
            prev = scene_tokens[scene].get(k - 1)
            ex, ey, eyaw = smp["ego_xyz"][0], smp["ego_xyz"][1], smp["ego_yaw"]
            dt = 1e-6 * (smp["timestamp"] - prev["timestamp"])
            v = math.hypot(ex - prev["ego_xyz"][0], ey - prev["ego_xyz"][1]) / dt
            w = wrap(eyaw - prev["ego_yaw"]) / dt
            corridor = None
            for r in fr:
                stats["records_k_ge_1"] += 1
                if r["tid"] not in pairs:
                    stats["unpaired"] += 1
                    continue
                a = ann_by_inst.get(pairs[r["tid"]])
                if a is None or a["num_pts"] < 1:
                    stats["censored"] += 1
                    continue
                if corridor is None:
                    from shapely.prepared import prep
                    cg = ego_corridor(ex, ey, eyaw, v, w)
                    corridor = (prep(cg), v * 4.0 + EGO_L + 2 * BUFFER)
                inpath = object_in_path(corridor[0], corridor[1], ex, ey, r["x"], r["y"], r["yaw"], r["vx"], r["vy"], r["w"], r["l"])
                rng = math.hypot(r["x"] - ex, r["y"] - ey)
                rows.append({"scene": scene, "k": k, "tid": r["tid"], "group": CLASS_GROUP[r["name"]], "pool": r["pool"],
                             "range": range_bin(rng), "inpath": inpath, "ex": ex, "ey": ey,
                             "mx": r["x"], "my": r["y"], "yaw": r["yaw"], "S": r["S"],
                             "gx": a["translation"][0], "gy": a["translation"][1]})
        stats["instances_paired"] += len(ever)
    stats["rows"] = len(rows)
    return rows, dict(stats)


def axis_vectors(row):
    c, s = math.cos(row["yaw"]), math.sin(row["yaw"])
    out = {}
    for name, a in (("long", (c, s)), ("lat", (-s, c))):
        dx, dy = row["ex"] - row["mx"], row["ey"] - row["my"]
        sign = 1.0 if a[0] * dx + a[1] * dy >= 0 else -1.0
        out[name] = (sign * a[0], sign * a[1])
    return out


def projected(row, axis):
    ax, ay = axis_vectors(row)[axis]
    sxx, sxy, syy = row["S"]
    var = ax * ax * sxx + 2 * ax * ay * sxy + ay * ay * syy
    d = ax * (row["gx"] - row["mx"]) + ay * (row["gy"] - row["my"])
    return d, var


def cell_arrays(rows, sigma_a=SIGMA_A, inpath_only=True, pool=None):
    """Per cell: arrays of D (projected error, m), var (exported projected variance), scene index; U computed by caller."""
    scenes = sorted({r["scene"] for r in rows})
    sidx = {s: i for i, s in enumerate(scenes)}
    data = {c: {"D": [], "V": [], "s": []} for c in CELLS}
    for r in rows:
        if inpath_only and not r["inpath"]:
            continue
        if pool is not None and r["pool"] != pool:
            continue
        for a in AXES:
            d, v = projected(r, a)
            c = (r["group"], r["range"], a)
            data[c]["D"].append(d)
            data[c]["V"].append(v)
            data[c]["s"].append(sidx[r["scene"]])
    for c in CELLS:
        for k in ("D", "V", "s"):
            data[c][k] = np.asarray(data[c][k], dtype=float if k != "s" else int)
    return data, scenes


def sizes_only(rows):
    out = {}
    for inpath_only in (True, False):
        data, scenes = cell_arrays(rows, inpath_only=inpath_only)
        key = "inpath" if inpath_only else "all"
        out[key] = {"|".join(c): {"records": int(len(data[c]["D"])), "scenes": int(len(np.unique(data[c]["s"]))),
                                  "median_exported_sd_m": float(np.median(np.sqrt(data[c]["V"] + SIGMA_A ** 2))) if len(data[c]["V"]) else None}
                    for c in CELLS}
    return out


# ------------------------------------------------------------------ statistics
def exceed_counts(U, s, n_scenes, thr):
    exc = np.bincount(s, weights=(U > thr).astype(float), minlength=n_scenes)
    tot = np.bincount(s, minlength=n_scenes).astype(float)
    return exc, tot


def boot_weights(n_scenes, B, rng):
    return rng.multinomial(n_scenes, np.full(n_scenes, 1.0 / n_scenes), size=B).astype(float)


def simultaneous_bounds(est, boot):
    """est: (G,), boot: (B, G) -> lower, upper simultaneous (max-|t|, 95%)."""
    se = boot.std(axis=0, ddof=1)
    se = np.where(se > 0, se, np.nan)
    t = np.nanmax(np.abs(boot - est) / se, axis=1)
    q = float(np.nanquantile(t, 0.95))
    return est - q * se, est + q * se, q


def crc_threshold(U, s, delta=DELTA):
    """Scene-level CRC (P01 Thm 5): smallest observed c with n/(n+1)*mean_j L_j(c) + 1/(n+1) <= delta."""
    scenes = np.unique(s)
    n = len(scenes)
    if n == 0 or (1.0 / (n + 1)) > delta:
        return None
    idx = {sc: i for i, sc in enumerate(scenes)}
    si = np.array([idx[x] for x in s])
    tot = np.bincount(si, minlength=n).astype(float)
    order = np.sort(np.unique(U))
    lo, hi = 0, len(order) - 1
    def ok(c):
        L = np.bincount(si, weights=(U > c).astype(float), minlength=n) / tot
        return n / (n + 1) * L.mean() + 1 / (n + 1) <= delta
    if not ok(order[hi]):
        return float(order[hi]) + 1e-9
    while lo < hi:
        mid = (lo + hi) // 2
        if ok(order[mid]):
            hi = mid
        else:
            lo = mid + 1
    return float(order[lo])


def inflation_needed(D, V, sigma_a=SIGMA_A, delta=DELTA):
    def exc(sv):
        return np.mean(D > Z95 * np.sqrt(sv * V + sigma_a ** 2))
    lo, hi = 1e-3, 1e4
    if exc(lo) <= delta:
        return lo
    if exc(hi) > delta:
        return hi
    for _ in range(80):
        mid = math.sqrt(lo * hi)
        if exc(mid) <= delta:
            hi = mid
        else:
            lo = mid
    return hi


def q95_subsampled(U, s, n_star, rng, reps):
    scenes = np.unique(s)
    if len(scenes) <= n_star:
        return float(np.quantile(U, 0.95))
    vals = []
    for _ in range(reps):
        pick = rng.choice(scenes, n_star, replace=False)
        m = np.isin(s, pick)
        vals.append(np.quantile(U[m], 0.95))
    return float(np.mean(vals))


def q4_statistic(cells_U, cells_s, sd_med, n_star, rng, reps):
    m = [q95_subsampled(cells_U[g], cells_s[g], n_star, rng, reps) for g in range(len(cells_U))]
    return (max(m) - min(m)) * sd_med, m


def q4_with_bootstrap(cells_U, cells_s, n_scenes, sd_med, n_star, rng, B=500, reps_point=50, reps_boot=10):
    point, m = q4_statistic(cells_U, cells_s, sd_med, n_star, rng, reps_point)
    boots = []
    for _ in range(B):
        pick = rng.integers(0, n_scenes, n_scenes)
        cnt = np.bincount(pick, minlength=n_scenes)
        bu, bs = [], []
        for U, s in zip(cells_U, cells_s):
            rep = cnt[s]
            # expand: each record repeated by its scene's multiplicity; scene ids relabelled per copy
            idx = np.repeat(np.arange(len(U)), rep)
            copy_id = np.concatenate([np.arange(r) for r in rep]) if len(rep) else np.array([], int)
            bu.append(U[idx])
            bs.append(s[idx] * 1000 + copy_id)
        boots.append(q4_statistic(bu, bs, sd_med, n_star, rng, reps_boot)[0])
    lo, hi = np.quantile(boots, [0.025, 0.975])
    verdict = "MATERIAL" if lo > H0 else ("IMMATERIAL" if hi < H0 else "INCONCLUSIVE")
    return {"H_m": point, "ci": [float(lo), float(hi)], "verdict": verdict, "m_hat_subsampled": m, "n_star": n_star}


# ------------------------------------------------------------------ modes
def selftest():
    rng = np.random.default_rng(1)
    res = {}
    # 1. exact Gaussian errors -> exceedance ~ 0.05 and q95 ~ z
    n = 200000
    V = rng.uniform(0.05, 1.0, n)
    D = rng.normal(0, np.sqrt(V))
    U = D / np.sqrt(V)
    res["T1_exceed"] = float(np.mean(U > Z95))
    res["T1_q95"] = float(np.quantile(U, 0.95))
    res["T1_ok"] = abs(res["T1_exceed"] - 0.05) < 0.003 and abs(res["T1_q95"] - Z95) < 0.02
    # 2. inflation: errors with variance kappa*V -> s ~ kappa
    kappa = 2.5
    D2 = rng.normal(0, np.sqrt(kappa * V))
    s_hat = inflation_needed(D2, V, sigma_a=0.0)
    res["T2_s_hat"], res["T2_ok"] = s_hat, abs(s_hat / kappa - 1) < 0.03
    # 3. CRC: exchangeable scenes, held-out exceedance <= delta on average
    held = []
    for rep in range(200):
        S = 80
        eff = rng.normal(0, 0.4, S)
        cnt = rng.integers(5, 40, S)
        s = np.repeat(np.arange(S), cnt)
        Ux = eff[s] + rng.normal(0, 1, len(s))
        perm = rng.permutation(S)
        cal, test = perm[:40], perm[40:]
        mc = np.isin(s, cal)
        c = crc_threshold(Ux[mc], s[mc])
        mt = ~mc
        # scene-level loss averaged over test scenes (CRC's estimand)
        st = s[mt]
        ut = np.unique(st)
        held.append(np.mean([np.mean(Ux[mt][st == j] > c) for j in ut]))
    res["T3_mean_heldout_scene_loss"] = float(np.mean(held))
    res["T3_ok"] = res["T3_mean_heldout_scene_loss"] <= 0.05 + 0.005
    # 4. orientation: object ahead of ego, true position closer to ego -> U > 0 on the long axis
    row = {"yaw": 0.0, "ex": 0.0, "ey": 0.0, "mx": 10.0, "my": 0.0, "gx": 9.0, "gy": 0.0, "S": (0.25, 0.0, 0.25)}
    d, v = projected(row, "long")
    res["T4_d"], res["T4_ok"] = d, d > 0 and abs(d - 1.0) < 1e-12 and abs(v - 0.25) < 1e-12
    row2 = dict(row, yaw=math.pi)  # heading reversed: oriented axis must still point to ego
    d2, _ = projected(row2, "long")
    res["T4b_ok"] = abs(d2 - 1.0) < 1e-12
    # 5. in-path
    from shapely.prepared import prep
    cg = ego_corridor(0, 0, 0, 10.0, 0.0)
    pc = prep(cg)
    reach = 40 + EGO_L
    res["T5_ahead"] = object_in_path(pc, reach, 0, 0, 20, 0, 0, 0, 0, 1.8, 4.5)
    res["T5_side"] = object_in_path(pc, reach, 0, 0, 20, 30, 0, 0, 0, 1.8, 4.5)
    res["T5_crossing"] = object_in_path(pc, reach, 0, 0, 20, 15, -math.pi / 2, 0, -5.0, 1.8, 4.5)
    res["T5_ok"] = res["T5_ahead"] and not res["T5_side"] and res["T5_crossing"]
    # 6. pairing: two tracks, two instances, persistence and an ID switch
    samples = {"t0": {"token": "t0", "scene": "S", "index": 0, "timestamp": 0, "ego_xyz": [0, 0, 0], "ego_yaw": 0.0},
               "t1": {"token": "t1", "scene": "S", "index": 1, "timestamp": 500000, "ego_xyz": [1, 0, 0], "ego_yaw": 0.0},
               "t2": {"token": "t2", "scene": "S", "index": 2, "timestamp": 1000000, "ego_xyz": [2, 0, 0], "ego_yaw": 0.0}}
    ann = lambda tok, inst, x: {"sample_token": tok, "instance_token": inst, "tracking_name": "car",
                               "translation": [x, 0.0, 0.0], "num_pts": 5}
    gtb = {"t0": [ann("t0", "A", 10.0), ann("t0", "B", 20.0)], "t1": [ann("t1", "A", 10.5), ann("t1", "B", 20.5)],
           "t2": [ann("t2", "A", 11.0), ann("t2", "B", 21.0)]}
    mk = lambda k, tok, tid, x: {"scene": "S", "k": k, "token": tok, "tid": tid, "name": "car", "pool": "active",
                                 "x": x, "y": 0.0, "w": 1.8, "l": 4.5, "yaw": 0.0, "vx": 0.0, "vy": 0.0, "S": (0.1, 0.0, 0.1)}
    recs = [mk(0, "t0", "1", 10.2), mk(0, "t0", "2", 19.9),
            mk(1, "t1", "1", 13.0),            # residual 2.5 m > gate, kept (persistence)
            mk(1, "t1", "2", 20.4),
            mk(2, "t2", "3", 11.1)]            # track 1 died; new track 3 takes instance A -> ID switch
    rows, st = build_table(recs, samples, gtb)
    r1 = [r for r in rows if r["tid"] == "1"]
    res["T6_persist_resid"] = abs(r1[0]["gx"] - r1[0]["mx"]) if r1 else None
    res["T6_id_switches"] = st.get("id_switches", 0)
    res["T6_ok"] = bool(r1) and abs(r1[0]["gx"] - 10.5) < 1e-12 and st.get("id_switches", 0) == 1 and len(rows) == 3
    # 7. simultaneous bounds cover under the null (synthetic, 18 cells)
    cover = 0
    for rep in range(100):
        G, S = 18, 150
        boots_src = rng.normal(0, 1, (S, G))
        est = boots_src.mean(axis=0)
        W = boot_weights(S, 2000, rng)
        boot = (W @ boots_src) / S
        lo, hi, _ = simultaneous_bounds(est, boot)
        cover += int(np.all((lo <= 0) & (hi >= 0)))
    res["T7_simultaneous_coverage"] = cover / 100
    res["T7_ok"] = res["T7_simultaneous_coverage"] >= 0.90
    res["ALL_OK"] = all(v for k, v in res.items() if k.endswith("_ok"))
    return res


def oc_simulation(sizes, rng, reps=200, B=200, icc=0.1):
    """Q4 operating characteristics at the observed eligible-cell sizes (synthetic U; code check, not evidence)."""
    cells = [c for c, v in sizes.items() if v["scenes"] >= MIN_SCENES]
    if len(cells) < 2:
        return {"eligible_cells": len(cells), "note": "fewer than 2 eligible cells; Q4 undefined"}
    sd_med = float(np.median([sizes[c]["median_exported_sd_m"] for c in cells]))
    n_scenes = 150
    per_cell_scene_counts = []
    for c in cells:
        v = sizes[c]
        # spread the cell's records over its scenes (equal split, remainder to the first scenes)
        sc = rng.choice(n_scenes, v["scenes"], replace=False)
        base = np.full(v["scenes"], v["records"] // v["scenes"])
        base[: v["records"] % v["scenes"]] += 1
        per_cell_scene_counts.append((sc, base))
    n_star = min(v["scenes"] for v in (sizes[c] for c in cells))
    out = {"eligible_cells": len(cells), "sd_med_m": sd_med, "n_star": n_star, "reps": reps, "B": B, "icc": icc}
    for label, spread_m in (("H0_true", 0.0), ("H_2h0", 2 * H0)):
        spread_sd = spread_m / sd_med
        shifts = np.linspace(-spread_sd / 2, spread_sd / 2, len(cells))
        verdicts = []
        for rep in range(reps):
            cu, cs = [], []
            b = rng.normal(0, math.sqrt(icc), n_scenes)
            for (sc, cnt), sh in zip(per_cell_scene_counts, shifts):
                s = np.repeat(sc, cnt)
                U = b[s] + rng.normal(0, math.sqrt(1 - icc), len(s)) + sh
                cu.append(U)
                cs.append(s)
            r = q4_with_bootstrap(cu, cs, n_scenes, sd_med, n_star, rng, B=B, reps_point=10, reps_boot=3)
            verdicts.append(r["verdict"])
        out[label] = {v: verdicts.count(v) / reps for v in ("MATERIAL", "IMMATERIAL", "INCONCLUSIVE")}
    out["false_material_rate"] = out["H0_true"]["MATERIAL"]
    out["false_immaterial_rate"] = out["H_2h0"]["IMMATERIAL"]
    out["targets_met"] = out["false_material_rate"] <= 0.10 and out["false_immaterial_rate"] <= 0.10
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=["selftest", "sizes", "oc", "full"])
    ap.add_argument("--export", help="x1_tracks.jsonl.gz")
    ap.add_argument("--gt", help="x1_val_gt_v01.json")
    ap.add_argument("--prereg", help="X1_PREREGISTRATION_v01.md (full mode)")
    ap.add_argument("--sizes", help="sizes json (oc mode)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    t0 = time.time()
    if a.mode == "selftest":
        res = selftest()
    elif a.mode == "oc":
        sizes = json.load(open(a.sizes))["sizes"]["inpath"]
        res = oc_simulation(sizes, np.random.default_rng(SEED))
    else:
        recs = load_export(a.export)
        samples, gtb = load_gt(a.gt)
        rows, pstats = build_table(recs, samples, gtb)
        if a.mode == "sizes":
            res = {"pairing": pstats, "sizes": sizes_only(rows), "inputs": {"export_sha256": sha256_path(a.export),
                   "gt_sha256": sha256_path(a.gt)}}
        else:
            raise SystemExit("full mode is implemented in x1_analysis_full_v01.py after the freeze")
    res["wall_s"] = round(time.time() - t0, 1)
    with open(a.out, "w") as f:
        json.dump(res, f, indent=1, default=float)
    print(json.dumps({k: v for k, v in res.items() if k != "sizes"}, default=float)[:3000])


if __name__ == "__main__":
    sys.exit(main())
