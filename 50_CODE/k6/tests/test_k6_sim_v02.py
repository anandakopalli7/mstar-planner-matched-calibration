#!/usr/bin/env python3
"""Known-answer tests for the K6 harness v02 (Claude line, 1 Nov 2026). Synthetic scenes only; no nuScenes outcome is read.
v02 (review R09): tests k6_sim_v02; T10 re-specified for the reference-margin exemptions; new T11 (dose monotonicity
with late-appearing crossing agents, after R09's C1 check) and T12 (record bits: in-path, enforced, satisfied,
sensor offset, rack censoring).
T1 geometry: rect_overlap against shapely on 20,000 random rectangle pairs.
T2 leash: with nothing around, the ego reproduces the logged profile (constant speed, and stop-and-go).
T3 static obstacle on the path: the ego stops short of it with at least the buffer (+ margin), no collision.
T4 crossing agent with exact predictions: no collision; the ego yields.
T5 dose monotonicity: a parked car beside the path; progress does not increase with the margin.
T6 determinism: two runs give the same trace hash; M* with every threshold = z equals B0 exactly.
T7 in-loop exceedance: Gaussian errors with known covariance and exact B0 margins give a rate near delta = 0.05.
T8 sign of D: errors pushed toward the ego are exceedances, errors pushed away are not.
T9 entry conflict and at-fault rule: an agent at the entry pose excludes a delayed episode; a stopped ego hit from behind
   is not at fault.
T10 enforcement rules: an oncoming car passing within its margin is infeasible at the margin, and the ego passes it by the
    margin back-off without an emergency stop or a collision; a static car ahead stops it.
T11 margin never creates a collision (R09b's widened grid, 576 late-crossing cases x 9 margin doses): a case free of
    at-fault collisions at dose 0 has none at any larger dose; some cases collide (the test is informative); very late
    detections that already collide at dose 0 are reported.
T13 decision mode: one decision per keyframe from the logged state; records in offset bin 0; with exact Gaussian margins
    the decision-mode rate is near delta.
T12 record bits: in-path, enforced and satisfied bits, the sensor-offset bin, and rack censoring decode as constructed.
"""
import json
import math
import os
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import k6_sim_v02 as S  # noqa: E402

RES = {}


def check(name, cond, detail):
    RES[name] = {"pass": bool(cond), "detail": detail}
    print(("PASS " if cond else "FAIL ") + name, json.dumps(detail, default=float))


def ego_log(profile, T=20.0, t0=1000.0):
    """20 Hz logged ego along +x: profile(t) -> speed."""
    t = t0 + np.arange(int(T / 0.05) + 1) * 0.05
    v = np.array([profile(x - t0) for x in t])
    x = np.concatenate([[0.0], np.cumsum(0.5 * (v[1:] + v[:-1]) * 0.05)])
    return t, x, np.zeros_like(x), np.zeros_like(x)


def make_scene(path, ego, tracks, gts):
    """tracks: list of dicts with k, tid, cls, x, y, yaw, w, l, vx, vy, spd, omc, inst, pred (8x5); gts: k, inst, cls, x, y, yaw, w, l, pts."""
    et, ex, ey, eyaw = ego
    kf_t = et[0] + 0.5 * np.arange(int((et[-1] - et[0]) / 0.5) + 1)
    kf_ego = np.stack([np.interp(kf_t, et, ex), np.interp(kf_t, et, ey), np.interp(kf_t, et, eyaw)], -1)
    arr = {"kf_t": kf_t, "kf_ego": kf_ego, "ego_t": et, "ego_x": ex, "ego_y": ey, "ego_yaw": eyaw}
    keys_i = ("k", "tid", "cls", "inst")
    if tracks:
        for key in ("k", "tid", "cls", "x", "y", "yaw", "w", "l", "vx", "vy", "spd", "om", "omv", "omc", "chord", "inst", "contested"):
            vals = [t.get(key, 0.0 if key not in ("contested",) else False) for t in tracks]
            arr["tr_" + key] = np.array(vals, dtype=int if key in keys_i else (bool if key == "contested" else float))
        arr["tr_pred"] = np.array([t["pred"] for t in tracks], float)
    for key in ("k", "inst", "cls", "x", "y", "yaw", "w", "l", "pts"):
        arr["gt_" + key] = np.array([g[key] for g in gts], dtype=int if key in ("k", "inst", "cls", "pts") else float)
    np.savez(path, **arr)
    return S.Scene(path)


def static_track(k, tid, x, y, inst, cov=(0.0, 0.0, 0.0), yaw=0.0, w=1.8, l=4.5, cls=0, mean_err=(0.0, 0.0)):
    mx, my = x + mean_err[0], y + mean_err[1]
    return {"k": k, "tid": tid, "cls": cls, "x": mx, "y": my, "yaw": yaw, "w": w, "l": l, "vx": 0.0, "vy": 0.0, "spd": 0.0,
            "omc": float("nan"), "inst": inst, "pred": [[mx, my, cov[0], cov[1], cov[2]]] * 8}


def t1_geometry():
    from shapely.geometry import Polygon
    rng = np.random.default_rng(1)
    bad = 0
    n = 20000
    for _ in range(n):
        c = rng.uniform(-3, 3, 2)
        yaw = rng.uniform(-math.pi, math.pi)
        L, W = rng.uniform(1, 6), rng.uniform(0.5, 3)
        oc = rng.uniform(-6, 6, (1, 2))
        oyaw = rng.uniform(-math.pi, math.pi, 1)
        oL, oW = rng.uniform(0.5, 12, 1), rng.uniform(0.5, 3, 1)
        mine = bool(S.rect_overlap(c, yaw, L, W, oc, oyaw, oL, oW)[0])

        def poly(cx, cy, y_, l_, w_):
            cc, ss = math.cos(y_), math.sin(y_)
            return Polygon([(cx + cc * dx - ss * dy, cy + ss * dx + cc * dy) for dx, dy in ((l_ / 2, w_ / 2), (l_ / 2, -w_ / 2), (-l_ / 2, -w_ / 2), (-l_ / 2, w_ / 2))])
        ref = poly(c[0], c[1], yaw, L, W).intersection(poly(oc[0, 0], oc[0, 1], oyaw[0], oL[0], oW[0])).area > 1e-9
        bad += int(mine != ref)
    check("T1_geometry_vs_shapely", bad == 0, {"pairs": n, "disagreements": bad})


def t2_leash(tmp):
    sc = make_scene(os.path.join(tmp, "t2a.npz"), ego_log(lambda t: 10.0), [], [])
    o, _ = S.run_episode(sc, "B0", None, 0)
    sc2 = make_scene(os.path.join(tmp, "t2b.npz"), ego_log(lambda t: 8.0 if t < 5 else (max(0.0, 8.0 - 2.0 * (t - 5)) if t < 9 else (0.0 if t < 13 else min(8.0, 2.0 * (t - 13))))), [], [])
    o2, _ = S.run_episode(sc2, "B0", None, 0)
    o3, _ = S.run_episode(sc2, "B0", None, 4)
    check("T2_leash_reproduces_log", o["progress"] > 0.995 and o2["progress"] > 0.98 and o3["progress"] > 0.98 and o["n_collisions"] == 0,
          {"const": o["progress"], "stop_go": o2["progress"], "stop_go_delay2s": o3["progress"], "lag_const": o["lag_mean"]})


def t3_static(tmp):
    ego = ego_log(lambda t: 8.0)
    xo = 60.0
    tracks = [static_track(k, 0, xo, 0.0, 0) for k in range(41)]
    gts = [{"k": k, "inst": 0, "cls": 0, "x": xo, "y": 0.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10} for k in range(41)]
    sc = make_scene(os.path.join(tmp, "t3.npz"), ego, tracks, gts)
    res = {}
    ok = True
    for arm, cov in (("Z0", (0.0, 0.0, 0.0)), ("B0", (0.25, 0.0, 0.25))):
        for t in tracks:
            t["pred"] = [[xo, 0.0, cov[0], cov[1], cov[2]]] * 8
        sc = make_scene(os.path.join(tmp, "t3_%s.npz" % arm), ego, tracks, gts)
        o, _ = S.run_episode(sc, arm, None, 0)
        front = o["s_end"] + S.R2C + S.EGO_L / 2
        gap = (xo - 4.5 / 2) - front
        need = S.BUFFER + (S.Z * math.sqrt(cov[0] + S.SIGMA_A ** 2) if arm == "B0" else 0.0)
        res[arm] = {"s_end": o["s_end"], "gap_m": round(gap, 3), "needed_m": round(need, 3), "collisions": o["n_collisions"]}
        ok &= o["n_collisions"] == 0 and gap >= need - 1e-6 and gap <= need + 4.0
    check("T3_static_obstacle_stop", ok, res)


def t4_crossing(tmp):
    ego = ego_log(lambda t: 8.0)
    tracks, gts = [], []
    # a car crossing the path (along +y) at x = 50, reaching the path at t = 6 s, speed 6 m/s
    for k in range(41):
        t = 0.5 * k
        y = -36.0 + 6.0 * t
        gts.append({"k": k, "inst": 0, "cls": 0, "x": 50.0, "y": y, "yaw": math.pi / 2, "w": 1.8, "l": 4.5, "pts": 10})
        pred = [[50.0, y + 6.0 * 0.5 * h, 0.0, 0.0, 0.0] for h in range(1, 9)]
        tracks.append({"k": k, "tid": 0, "cls": 0, "x": 50.0, "y": y, "yaw": math.pi / 2, "w": 1.8, "l": 4.5, "vx": 0.0, "vy": 6.0,
                       "spd": 6.0, "omc": 0.0, "inst": 0, "pred": pred})
    sc = make_scene(os.path.join(tmp, "t4.npz"), ego, tracks, gts)
    o, _ = S.run_episode(sc, "Z0", None, 0)
    check("T4_crossing_yield", o["n_collisions"] == 0 and o["lag_mean"] > 0.5, {"collisions": o["n_collisions"], "progress": o["progress"],
                                                                                 "lag_mean": o["lag_mean"], "buffer_intrusions": o["n_front_buffer_intrusions"]})


def t5_dose(tmp):
    ego = ego_log(lambda t: 8.0)
    yo = S.EGO_W / 2 + S.BUFFER + 1.8 / 2 + 0.8      # 0.8 m beyond the buffered footprints
    prog = []
    for dose in (0.0, 0.25, 1.0, 4.0, 16.0):
        tracks = [static_track(k, 0, 70.0, yo, 0, cov=(0.04 * dose, 0.0, 0.04 * dose)) for k in range(41)]
        gts = [{"k": k, "inst": 0, "cls": 0, "x": 70.0, "y": yo, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10} for k in range(41)]
        sc = make_scene(os.path.join(tmp, "t5_%g.npz" % dose), ego, tracks, gts)
        o, _ = S.run_episode(sc, "B0", None, 0)
        prog.append(o["progress"])
    check("T5_dose_monotone", all(b <= a + 1e-9 for a, b in zip(prog, prog[1:])) and prog[0] > 0.99 and prog[-1] < 0.9,
          {"doses": [0, 0.25, 1, 4, 16], "progress": prog})


def t6_determinism(tmp):
    ego = ego_log(lambda t: 8.0)
    rng = np.random.default_rng(7)
    tracks, gts = [], []
    for i in range(12):
        x, y = rng.uniform(20, 150), rng.choice([-1, 1]) * rng.uniform(2.5, 8)
        for k in range(41):
            tracks.append(static_track(k, i, x, y, i, cov=(0.3, 0.05, 0.2), mean_err=tuple(rng.normal(0, 0.3, 2))))
            gts.append({"k": k, "inst": i, "cls": 0, "x": x, "y": y, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10})
    sc = make_scene(os.path.join(tmp, "t6.npz"), ego, tracks, gts)
    a, ca = S.run_episode(sc, "B0", None, 0)
    b, cb = S.run_episode(sc, "B0", None, 0)
    fits = [{"Mstar": [S.Z] * 96, "B6": [S.Z] * 96, "B4": S.Z, "B3": S.Z, "B9": 1.0, "B1": [1.0] * 12} for _ in range(8)]
    m, cm = S.run_episode(sc, "Mstar", fits, 0)
    b1, _ = S.run_episode(sc, "B1", fits, 0)
    check("T6_determinism_and_lookup", a["trace_sha256"] == b["trace_sha256"] == m["trace_sha256"] == b1["trace_sha256"] and ca == cb == cm,
          {"trace": a["trace_sha256"][:16], "mstar_equals_b0": m["trace_sha256"] == a["trace_sha256"], "cells": len(ca)})


def t7_inloop(tmp):
    ego = ego_log(lambda t: 6.0)
    rng = np.random.default_rng(11)
    Sig = np.array([[0.30, 0.08], [0.08, 0.15]])
    Ch = np.linalg.cholesky(Sig + S.SIGMA_A ** 2 * np.eye(2))
    tracks, gts = [], []
    n_obj = 40
    for i in range(n_obj):
        x, y = rng.uniform(0, 140), rng.choice([-1, 1]) * rng.uniform(6, 12)
        yaw = rng.uniform(-math.pi, math.pi)
        for k in range(41):
            e = Ch @ rng.normal(size=2)
            tracks.append(static_track(k, i, x, y, i, cov=(Sig[0, 0], Sig[0, 1], Sig[1, 1]), yaw=yaw, mean_err=(e[0], e[1])))
            gts.append({"k": k, "inst": i, "cls": 0, "x": x, "y": y, "yaw": yaw, "w": 1.8, "l": 4.5, "pts": 10})
    sc = make_scene(os.path.join(tmp, "t7.npz"), ego, tracks, gts)
    n = x_ = 0
    for d in (0, 2, 4):
        _, c = S.run_episode(sc, "B0", None, d)
        for cell, (cn, cx) in c.items():
            n += cn
            x_ += cx
    rate = x_ / max(n, 1)
    # records share the per-keyframe error across steps and axes, so use a generous band (about 4 binomial SE at the
    # number of independent errors)
    n_ind = n_obj * 41
    se = math.sqrt(0.05 * 0.95 / n_ind)
    check("T7_inloop_rate_at_delta", abs(rate - 0.05) < 4 * se + 0.005, {"records": n, "exceed": x_, "rate": rate, "band": 4 * se + 0.005})


def t8_sign(tmp):
    ego = ego_log(lambda t: 5.0)
    res = {}
    for side, push, expect in ((1, -1.5, 0), (1, +1.5, 1), (-1, +1.5, 0), (-1, -1.5, 1)):
        # object at y = side * 6; the estimate is shifted by push in y; the truth is at y = side * 6
        # error g - m = -push: toward the ego (y = 0) when -push has the sign of -side
        y_true = side * 6.0
        tracks = [static_track(k, 0, 40.0, y_true, 0, cov=(0.01, 0.0, 0.01), mean_err=(0.0, push)) for k in range(41)]
        gts = [{"k": k, "inst": 0, "cls": 0, "x": 40.0, "y": y_true, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10} for k in range(41)]
        sc = make_scene(os.path.join(tmp, "t8.npz"), ego, tracks, gts)
        _, c = S.run_episode(sc, "B0", None, 0)
        lat = [(v[0], v[1]) for cell, v in c.items() if S.decode_cell(cell)[7] % 8 // 4 == 1]   # axis bit of L0: (l1 % 2)
        n = sum(a for a, _ in lat)
        e = sum(b for _, b in lat)
        res["side%+d_push%+.1f" % (side, push)] = {"lat_records": n, "lat_exceed": e}
        toward = (-push) * (-side) > 0
        res["side%+d_push%+.1f" % (side, push)]["toward_ego"] = toward
        ok = n > 0 and ((e == n) if expect else (e == 0))
        res["side%+d_push%+.1f" % (side, push)]["ok"] = ok
    check("T8_sign_toward_ego", all(v["ok"] for v in res.values()), res)


def t9_entry_and_fault(tmp):
    ego = ego_log(lambda t: 8.0)
    # an agent parked exactly on the entry pose: the delayed episode is excluded
    gts = [{"k": k, "inst": 0, "cls": 0, "x": S.R2C, "y": 0.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10} for k in range(41)]
    sc = make_scene(os.path.join(tmp, "t9a.npz"), ego, [], gts)
    o, _ = S.run_episode(sc, "B0", None, 2)
    # a stopped ego (log stops at t = 0) hit from behind by an agent at 5 m/s: not at fault
    ego2 = ego_log(lambda t: 0.0)
    gts2 = [{"k": k, "inst": 0, "cls": 0, "x": -20.0 + 5.0 * 0.5 * k, "y": 0.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10} for k in range(41)]
    sc2 = make_scene(os.path.join(tmp, "t9b.npz"), ego2, [], gts2)
    o2, _ = S.run_episode(sc2, "B0", None, 0)
    ok = (not o["entered"]) and o["reason"] == "entry_conflict" and o2["n_collisions"] == 1 and o2["n_at_fault"] == 0
    check("T9_entry_conflict_and_fault_rule", ok, {"delayed": o.get("reason"), "rear_collisions": o2["n_collisions"], "at_fault": o2["n_at_fault"]})


def t10_enforcement_rules(tmp):
    """An oncoming car in the adjacent lane passes with lateral clearance (1.0 m beyond the buffered footprints) below its
    lateral margin (about 1.65 m). Its buffered mean footprint never meets the ego, so under the reference-margin rule
    (v02) the pair is enforced at the arm's margin: the decisions of the encounter are infeasible at the margin (counted),
    and the margin back-off (R09b MJ1) lets the ego pass at a reduced margin instead of an emergency stop, with no
    collision. A static car on the path ahead, with the same covariance, stops the ego."""
    ego = ego_log(lambda t: 8.0)
    yo = 3.3                                            # lateral clearance 3.3 - 2.3 = 1.0 m beyond the buffered footprints
    tracks, gts = [], []
    for k in range(41):
        t = 0.5 * k
        x = 150.0 - 10.0 * t
        gts.append({"k": k, "inst": 0, "cls": 0, "x": x, "y": yo, "yaw": math.pi, "w": 1.8, "l": 4.5, "pts": 10})
        pred = [[x - 10.0 * 0.5 * h, yo, 1.0, 0.0, 1.0] for h in range(1, 9)]   # sd ~1 m: lateral margin ~1.65 m > 1.0 m
        tracks.append({"k": k, "tid": 0, "cls": 0, "x": x, "y": yo, "yaw": math.pi, "w": 1.8, "l": 4.5, "vx": -10.0, "vy": 0.0,
                       "spd": 10.0, "omc": 0.0, "inst": 0, "pred": pred})
    sc = make_scene(os.path.join(tmp, "t10a.npz"), ego, tracks, gts)
    o, _ = S.run_episode(sc, "B0", None, 0)
    tracks2 = [static_track(k, 0, 90.0, 0.0, 0, cov=(1.0, 0.0, 1.0)) for k in range(41)]
    gts2 = [{"k": k, "inst": 0, "cls": 0, "x": 90.0, "y": 0.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10} for k in range(41)]
    sc2 = make_scene(os.path.join(tmp, "t10b.npz"), ego, tracks2, gts2)
    o2, _ = S.run_episode(sc2, "B0", None, 0)
    ok = (o["infeasible_frames"] > 0 and o.get("emergency_stop_frames", 0) == 0 and o["n_collisions"] == 0
          and o2["progress"] < 0.6 and o2["n_collisions"] == 0)
    check("T10_oncoming_within_margin_backoff", ok, {"oncoming_progress": o["progress"], "oncoming_blocked_s": o["blocked_s"],
                                                             "oncoming_infeasible_frames": o["infeasible_frames"],
                                                             "oncoming_brought_to_ego": o["brought_to_ego_pairs"],
                                                             "static_ahead_progress": o2["progress"], "collisions": o["n_collisions"] + o2["n_collisions"]})


def t11_dose_monotone(tmp):
    """R09b's widened late-crossing grid: ego 8, 12 or 15 m/s; crossing at 30 or 60 m; track lead 0.5-2.5 s; crossing
    speed 3, 6 or 10 m/s (cars; pedestrians at 3 m/s); delay 1 or 2 s; crossing-time offset -0.75, 0 or +0.75 s; margin
    multiplier 0 to 16 (M* with every threshold = c, sd about 1 m). Property (strict): a case free of at-fault collisions
    at dose 0 has none at any larger dose (the margin never turns a safe encounter into a collision). Informative: some
    cases collide. Cases that already collide at dose 0 but not at every dose are reported (very late detections)."""
    import itertools
    doses = [0.0, 1.0, 1.645, 2.5, 4.0, 6.0, 8.0, 12.0, 16.0]
    grid = list(itertools.product((8.0, 12.0, 15.0), (30.0, 60.0), (0.5, 1.0, 1.5, 2.5), (3.0, 6.0, 10.0), (2, 4), (-0.75, 0.0, 0.75), ("car", "ped")))
    bad, late, n_cases, n_coll = [], [], 0, 0
    for ve, x0, lead_s, vc, dkf, off, kind in grid:
        if kind == "ped" and vc > 3.0:
            continue
        L_, W_ = (4.5, 1.8) if kind == "car" else (0.7, 0.7)
        cls = 0 if kind == "car" else 4
        ego = ego_log(lambda t: ve)
        t_c = x0 / ve + 0.5 * dkf + off
        k_app = max(0, int(math.ceil((t_c - lead_s) / 0.5)))
        tracks, gts = [], []
        for k in range(41):
            y = vc * (0.5 * k - t_c)
            gts.append({"k": k, "inst": 0, "cls": cls, "x": x0, "y": y, "yaw": math.pi / 2, "w": W_, "l": L_, "pts": 10})
            if k >= k_app:
                tracks.append({"k": k, "tid": 0, "cls": cls, "x": x0, "y": y, "yaw": math.pi / 2, "w": W_, "l": L_, "vx": 0.0, "vy": vc,
                               "spd": vc, "omc": 0.0, "inst": 0, "pred": [[x0, y + vc * 0.5 * h, 1.0, 0.0, 1.0] for h in range(1, 9)]})
        sc = make_scene(os.path.join(tmp, "t11.npz"), ego, tracks, gts)
        af = []
        for c in doses:
            fits = [{"Mstar": [c] * 96, "B6": [c] * 96, "B4": c, "B3": c, "B9": c, "B1": [1.0] * 12} for _ in range(8)]
            o, _ = S.run_episode(sc, "Mstar", fits, dkf, record=False)
            if not o["entered"]:
                af = None
                break
            af.append(o["n_at_fault"])
        if af is None:
            continue
        n_cases += 1
        n_coll += int(any(af))
        case = [ve, x0, lead_s, vc, dkf, off, kind]
        if af[0] == 0 and any(af[1:]):
            bad.append({"case": case, "at_fault": af})
        elif af[0] > 0 and not all(af):
            late.append({"case": case, "at_fault": af})
    check("T11_margin_never_creates_collision", not bad and n_coll > 0,
          {"cases": n_cases, "cases_with_any_at_fault": n_coll, "violations": bad[:5], "late_detection_non_monotone": late[:5],
           "n_late_detection_non_monotone": len(late)})


def t12_record_bits(tmp):
    """Every value of every record bit is produced and asserted: in-path 1 (car A) and 0 (car B, not in a rack);
    enforced 0 (an in-lane head-on car whose mean footprint reaches the held ego) and 1; satisfied 0 (decisions with no
    feasible plan at the margin) and 1; offset bin 0 at delay 0 and 2 at a 2 s delay; the bicycle inside a rack is never
    recorded."""
    ego = ego_log(lambda t: 8.0)
    tracks, gts = [], []
    for k in range(41):
        t = 0.5 * k
        a = static_track(k, 0, 120.0, 4.0, 0, cov=(0.01, 0.0, 0.01))
        a["inpath"] = True
        b = static_track(k, 1, 125.0, -4.0, 1, cov=(0.01, 0.0, 0.01))
        b["inpath"] = False
        bk = static_track(k, 2, 70.0, -5.0, 2, cov=(0.01, 0.0, 0.01), cls=6, w=0.6, l=1.7)
        bk["inpath"] = False
        xc = 150.0 - 6.0 * t
        c = {"k": k, "tid": 3, "cls": 0, "x": xc, "y": 0.0, "yaw": math.pi, "w": 1.8, "l": 4.5, "vx": -6.0, "vy": 0.0, "spd": 6.0,
             "omc": 0.0, "inst": 3, "inpath": True, "pred": [[xc - 6.0 * 0.5 * h, 0.0, 0.5, 0.0, 0.5] for h in range(1, 9)]}
        tracks += [a, b, bk, c]
        gts.append({"k": k, "inst": 0, "cls": 0, "x": 120.0, "y": 4.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10, "inrack": False})
        gts.append({"k": k, "inst": 1, "cls": 0, "x": 125.0, "y": -4.0, "yaw": 0.0, "w": 1.8, "l": 4.5, "pts": 10, "inrack": False})
        gts.append({"k": k, "inst": 2, "cls": 6, "x": 70.0, "y": -5.0, "yaw": 0.0, "w": 0.6, "l": 1.7, "pts": 10, "inrack": True})
        gts.append({"k": k, "inst": 3, "cls": 0, "x": xc, "y": 0.0, "yaw": math.pi, "w": 1.8, "l": 4.5, "pts": 10, "inrack": False})
    path = os.path.join(tmp, "t12.npz")
    make_scene(path, ego, tracks, gts)
    z = dict(np.load(path))
    z["tr_inpath"] = np.array([t_["inpath"] for t_ in tracks], bool)
    z["gt_inrack"] = np.array([g["inrack"] for g in gts], bool)
    np.savez(path, **z)
    sc = S.Scene(path)
    res, ok = {}, True
    for d, want_ob in ((0, 0), (4, 2)):
        _, cnt = S.run_episode(sc, "B0", None, d)
        bits = [S.decode_cell(cell) for cell in cnt]
        got = {"offset": sorted({x[0] for x in bits}), "inpath": sorted({x[1] for x in bits}), "enforced": sorted({x[2] for x in bits}),
               "satisfied": sorted({x[3] for x in bits}), "groups": sorted({x[7] // 24 for x in bits})}
        res["delay_kf%d" % d] = got
        ok &= 2 not in got["groups"] and want_ob in got["offset"]
        if d == 0:
            ok &= 0 in got["offset"] and got["inpath"] == [0, 1] and got["enforced"] == [0, 1] and got["satisfied"] == [0, 1]
    check("T12_record_bits", ok, res)


def t13_decision_mode(tmp):
    ego = ego_log(lambda t: 6.0)
    rng = np.random.default_rng(13)
    Sig = np.array([[0.30, 0.08], [0.08, 0.15]])
    Ch = np.linalg.cholesky(Sig + S.SIGMA_A ** 2 * np.eye(2))
    tracks, gts = [], []
    for i in range(40):
        x, y = rng.uniform(0, 140), rng.choice([-1, 1]) * rng.uniform(6, 12)
        yaw = rng.uniform(-math.pi, math.pi)
        for k in range(41):
            e = Ch @ rng.normal(size=2)
            tracks.append(static_track(k, i, x, y, i, cov=(Sig[0, 0], Sig[0, 1], Sig[1, 1]), yaw=yaw, mean_err=(e[0], e[1])))
            gts.append({"k": k, "inst": i, "cls": 0, "x": x, "y": y, "yaw": yaw, "w": 1.8, "l": 4.5, "pts": 10})
    sc = make_scene(os.path.join(tmp, "t13.npz"), ego, tracks, gts)
    o, c = S.run_decisions(sc, "B0", None)
    n = sum(v[0] for v in c.values())
    x = sum(v[1] for v in c.values())
    obs = {S.decode_cell(cell)[0] for cell in c}
    steps = {S.decode_cell(cell)[6] for cell in c}
    se = math.sqrt(0.05 * 0.95 / (40 * 39))
    ok = o["frames"] == sc.K - 2 and obs == {0} and max(steps) < S.CC_STEPS and abs(x / max(n, 1) - 0.05) < 4 * se + 0.005
    check("T13_decision_mode", ok, {"frames": o["frames"], "records": n, "rate": x / max(n, 1), "offset_bins": sorted(obs),
                                    "steps": sorted(steps), "band": 4 * se + 0.005})


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else None
    with tempfile.TemporaryDirectory() as tmp:
        t1_geometry()
        t2_leash(tmp)
        t3_static(tmp)
        t4_crossing(tmp)
        t5_dose(tmp)
        t6_determinism(tmp)
        t7_inloop(tmp)
        t8_sign(tmp)
        t9_entry_and_fault(tmp)
        t10_enforcement_rules(tmp)
        t11_dose_monotone(tmp)
        t12_record_bits(tmp)
        t13_decision_mode(tmp)
    allok = all(v["pass"] for v in RES.values())
    print("ALL_PASS" if allok else "SOME_FAIL")
    if out:
        json.dump({"tests": RES, "all_pass": allok}, open(out, "w"), indent=1, default=float)


if __name__ == "__main__":
    main()
