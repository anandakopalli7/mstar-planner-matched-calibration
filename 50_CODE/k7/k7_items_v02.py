#!/usr/bin/env python3
"""K7 calibration items (Claude line, v02, 1 Nov 2026): planner-matched calibration population.
v02: every item also carries its pair gap at the reference pose (gap) and a pair id (pair), and the flag ref_relied:
the item is the pair's axis with the largest gap at the reference pose (margin 0), i.e. the axis the planner relies on at
the reference. K7 calibrates on the ref_relied items (one per pair), matching the in-loop records' relied-on selection.
v01:

K6 found that DP-SCRC, calibrated on the method's in-path population (objects whose constant-velocity footprint meets the
logged ego's CTRV corridor), exceeds delta on constraints the planner relies on outside that population. K7 calibrates on
the constraints the planner itself evaluates. For every decision state of the K6 decision mode (keyframe 1 <= k <= K - 2,
the logged ego's position and speed) and every calibrated step h = 0.5, 1, 1.5, 2 s, the population is the planner's
ENFORCED (track, check time) pairs, decided exactly as in k6_sim_v02.plan_step at the arm-independent reference margin 0
(some candidate keeps the buffered mean footprints apart, and an ego held at its position would too). For each such pair
with a ground-truth annotation at k + h (>= 1 point, not in a bicycle rack), each object axis that separates the pair at
the reference ego pose -- the logged pose at t_k + h, which is the decision mode's leash -- gives one item:
  D = sign(sep) a.(g - m), sd = sqrt(a' S_h a + 0.10^2), U = D / sd,
with the K6 strata (group, range from the sensor's CTRV, axis, motion state). Every quantity except D is computed by the
frozen K6 simulator's own functions (k6_sim_v02: Scene, sensor_ctrv, strata, plan_positions, gaps), imported read-only;
D is computed exactly as in k6_sim_v02._record. Each enforced pair also gives one record (dx, dy, S_h) for the NEES and
norm-ball baselines. Nothing here depends on an arm, a margin or a plan choice.
Usage: python -B k7_items_v01.py --caches <dir...> --out <npz> [--workers n] [--scenes ...]
"""
import argparse
import hashlib
import json
import math
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(W_ROOT, "50_CODE", "k6"))
import k6_sim_v02 as S  # noqa: E402

ITEM = ("s", "k", "h", "g", "r", "a", "m", "inpath", "sd", "D", "l0", "gap", "pair", "ref_relied")
REC = ("s", "k", "h", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "inpath")


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def scene_items(job):
    path, si = job
    sc = S.Scene(path)
    it = {k: [] for k in ITEM}
    rc = {k: [] for k in REC}
    st = {"decisions": 0, "pairs_considered": 0, "pairs_enforced": 0, "pairs_with_gt": 0}
    if sc.K < 3 or not len(sc.tr.get("k", [])):
        return si, it, rc, st
    vmax = sc.v_log_max + 2.0
    tr = sc.tr
    inpath_all = tr["inpath"] if "inpath" in tr else np.zeros(len(tr["k"]), bool)
    inrack = sc.gt["inrack"] if "inrack" in sc.gt else np.zeros(len(sc.gt["k"]), bool)
    for k in range(1, sc.K - 1):                       # the decision states of k6_sim_v02.run_decisions
        st["decisions"] += 1
        tk = float(sc.kf_t[k])
        s, v = float(sc.s_log(tk)), max(sc.v_log(tk), 0.0)
        ex, ey, eyaw = (float(q) for q in sc.pose(np.array(s)))
        rows = sc.tr_by_k[k]
        if not len(rows):
            continue
        cxe, cye = ex + S.R2C * math.cos(eyaw), ey + S.R2C * math.sin(eyaw)
        dx, dy = tr["x"][rows] - cxe, tr["y"][rows] - cye
        sel = rows[(np.hypot(dx, dy) < S.R_CONSIDER) & (dx * math.cos(eyaw) + dy * math.sin(eyaw) >= -S.EGO_L / 2)]
        if not len(sel):
            continue
        sens_pose, sens_v, sens_w = S.sensor_ctrv(sc, k)
        g, r, m, sd, l0, ax = S.strata(sc, sel, k, sens_pose, sens_v, sens_w)
        pred = tr["pred"][sel]
        pred_xy = pred[:, :, :2]
        cur = np.stack([tr["x"][sel], tr["y"][sel]], -1)[:, None, :]
        prev = np.concatenate([cur, pred_xy[:, :-1]], 1)
        xy16 = np.empty((len(sel), S.N_EVAL, 2))
        xy16[:, 1::2] = pred_xy
        xy16[:, 0::2] = 0.5 * (prev + pred_xy)
        half = np.stack([0.5 * tr["l"][sel], 0.5 * tr["w"][sel]], -1)
        lead = sc.s_log(tk + S.EVAL_T)
        splan = np.minimum(S.plan_positions(s, v, vmax), lead[None, :])
        gap, _ = S.gaps(sc, splan, xy16, ax, half)
        ctrl = (np.max(gap, axis=-1) >= 0.0).any(axis=0)[:S.CC_EVAL]
        ghold, _ = S.gaps(sc, np.full((1, S.N_EVAL), s), xy16, ax, half)
        hold_ok = (np.max(ghold[0], axis=-1) >= 0.0)[:S.CC_EVAL]
        enf = (ctrl & hold_ok)[1::2]                   # (CC_STEPS, J): the keyframe-aligned checks 0.5 ... 2 s
        glog, slog = S.gaps(sc, lead[None, :], xy16, ax, half)
        G, SP = glog[0][1::2], slog[0][1::2]           # (8, J, 2) at the reference (logged) pose
        inst, inp = tr["inst"][sel], inpath_all[sel]
        for h in range(S.CC_STEPS):
            kk = k + h + 1
            if kk >= sc.K:
                break
            gat = sc.gt_at[kk]
            for j in np.nonzero(inst >= 0)[0]:
                st["pairs_considered"] += 1
                if not enf[h, j]:
                    continue
                st["pairs_enforced"] += 1
                row = gat.get(int(inst[j]))
                if row is None or inrack[row]:
                    continue
                st["pairs_with_gt"] += 1
                e0, e1 = sc.gt["x"][row] - pred_xy[j, h, 0], sc.gt["y"][row] - pred_xy[j, h, 1]
                for key, val in (("s", si), ("k", k), ("h", h), ("g", g[j]), ("r", r[j, h]), ("dx", e0), ("dy", e1), ("sxx", pred[j, h, 2]),
                                 ("sxy", pred[j, h, 3]), ("syy", pred[j, h, 4]), ("inpath", bool(inp[j]))):
                    rc[key].append(val)
                pid = st["pairs_with_gt"]
                rel = int(np.argmax(G[h, j]))
                for a_ in range(2):
                    if not G[h, j, a_] > 0:
                        continue
                    D = float(np.sign(SP[h, j, a_]) * (ax[j, a_, 0] * e0 + ax[j, a_, 1] * e1))
                    for key, val in (("s", si), ("k", k), ("h", h), ("g", g[j]), ("r", r[j, h]), ("a", a_), ("m", m[j]),
                                     ("inpath", bool(inp[j])), ("sd", sd[j, h, a_]), ("D", D), ("l0", l0[j, h, a_]),
                                     ("gap", float(G[h, j, a_])), ("pair", pid), ("ref_relied", a_ == rel)):
                        it[key].append(val)
    return si, it, rc, st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caches", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--scenes", nargs="*", default=None)
    a = ap.parse_args()
    t0 = time.time()
    jobs, names, logs, man_sha = [], [], {}, []
    for cdir in a.caches:
        mp = os.path.join(cdir, "MANIFEST.json")
        man = json.load(open(mp))
        man_sha.append(sha256_path(mp))
        for scene, info in sorted(man["scenes"].items()):
            if a.scenes and scene not in set(a.scenes):
                continue
            p = os.path.join(cdir, scene + ".npz")
            assert sha256_path(p) == info["sha256"], "cache file differs from its manifest: " + p
            jobs.append((p, len(names)))
            names.append(scene)
            logs[scene] = info["log"]
    assert len(set(names)) == len(names), "a scene appears twice"
    its = {k: [] for k in ITEM}
    rcs = {k: [] for k in REC}
    stats = {}
    with Pool(a.workers) as pool:
        for i, (si, it, rc, st) in enumerate(pool.imap_unordered(scene_items, jobs, chunksize=1)):
            for k in ITEM:
                its[k].append(np.asarray(it[k]))
            for k in REC:
                rcs[k].append(np.asarray(rc[k]))
            stats[names[si]] = st
            if (i + 1) % 50 == 0 or i + 1 == len(jobs):
                print("scenes %d/%d  %.0f s" % (i + 1, len(jobs), time.time() - t0), flush=True)
    out = {}
    for k in ITEM:
        out["item_" + k] = np.concatenate([x for x in its[k] if len(x)] or [np.zeros(0)])
    for k in REC:
        out["rec_" + k] = np.concatenate([x for x in rcs[k] if len(x)] or [np.zeros(0)])
    for k in ("s", "k", "h", "g", "r", "a", "m", "l0", "pair"):
        out["item_" + k] = out["item_" + k].astype(np.int32)
    out["item_ref_relied"] = out["item_ref_relied"].astype(bool)
    for k in ("s", "k", "h", "g", "r"):
        out["rec_" + k] = out["rec_" + k].astype(np.int32)
    out["item_inpath"] = out["item_inpath"].astype(bool)
    out["rec_inpath"] = out["rec_inpath"].astype(bool)
    out["scene_names"] = np.array(names)
    out["scene_logs"] = np.array([logs[s] for s in names])
    np.savez_compressed(a.out, **out)
    summ = {"caches": [os.path.abspath(c) for c in a.caches], "manifest_sha256": man_sha, "scenes": len(names),
            "items": int(len(out["item_D"])), "records": int(len(out["rec_dx"])),
            "items_inpath_share": float(out["item_inpath"].mean()) if len(out["item_D"]) else None,
            "items_ref_relied": int(out["item_ref_relied"].sum()),
            "totals": {k: int(sum(st[k] for st in stats.values())) for k in ("decisions", "pairs_considered", "pairs_enforced", "pairs_with_gt")},
            "sim_sha256": sha256_path(S.__file__), "items_script_sha256": sha256_path(os.path.abspath(__file__)),
            "out_sha256": sha256_path(a.out), "seconds": round(time.time() - t0, 1)}
    json.dump(summ, open(a.out.replace(".npz", "_summary.json"), "w"), indent=1)
    print(json.dumps(summ))
    print("K7 ITEMS V02 DONE")


if __name__ == "__main__":
    main()
