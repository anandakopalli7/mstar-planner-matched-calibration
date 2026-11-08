#!/usr/bin/env python3
"""P3 closed-loop timing and determinism probe (Claude line, v03, 31 Oct 2026). One episode per process.
v03: optional --fast-convex passed to the tracker worker.
v02: objects ordered by their scenario id (MetaDrive object names are random UUIDs per run; v01 sorted by them).

Loop at 10 Hz in MetaDrive's ScenarioEnv (nuScenes scenes converted by the pinned ScenarioNet; logged, non-reactive
traffic; rendering off; no lidar). Every 0.5 s: emulated detections of the true objects within 50 m (seeded Gaussian
noise; parametric stand-in for the archive's empirical emulator) -> CANMOT worker process (approved experiment
paper/local/canmot/sc) -> covariance dose (copy scaled by s) -> CC-joint speed planner along the logged ego path
(per object and step: margin c * sqrt(n' Sigma_h n), c = z_{1 - delta_obj / p}) -> ego moved kinematically.

Records timing and a trace hash only. Collision or progress outcomes are NOT computed (outcomes stay sealed until GO).
Usage (simulator environment):
  python closed_loop_probe_v01.py --db <scenarionet db> --scenario-index i --dose s --seed n --out <json>
         --tracker-python <canmot python> --canmot-repo <repo> --worker <tracker_worker_v01.py>
"""
import argparse
import hashlib
import json
import math
import os
import subprocess
import sys
import time

T_PROC0 = time.perf_counter()
import numpy as np  # noqa: E402
from scipy.stats import norm  # noqa: E402

DT_SIM, PERC_EVERY = 0.1, 5
HORIZON_STEPS, H_DT = 8, 0.5
ACCELS = [-6.0, -3.0, -1.5, 0.0, 0.75, 1.5]
DELTA_OBJ = 0.01
R_EGO = 2.0
NOISE = {"car": (0.30, 0.20, 0.05), "truck": (0.40, 0.25, 0.05), "bus": (0.45, 0.25, 0.05),
         "pedestrian": (0.15, 0.25, 0.30), "bicycle": (0.25, 0.25, 0.15)}
SCORE = {"car": 0.7, "truck": 0.6, "bus": 0.6, "pedestrian": 0.6, "bicycle": 0.5}


def quat_from_yaw(y):
    return [math.cos(y / 2), 0.0, 0.0, math.sin(y / 2)]


def obj_class(obj):
    n = type(obj).__name__.lower()
    if "pedestrian" in n:
        return "pedestrian"
    if "cyclist" in n or "bicycle" in n:
        return "bicycle"
    if "vehicle" in n:
        L = float(getattr(obj, "LENGTH", 4.5))
        return "bus" if L > 10 else ("truck" if L > 6 else "car")
    return None


class Path:
    def __init__(self, xy):
        self.xy = np.asarray(xy, dtype=float)
        seg = np.linalg.norm(np.diff(self.xy, axis=0), axis=1)
        self.s = np.concatenate([[0.0], np.cumsum(seg)])

    def at(self, s):
        s = float(np.clip(s, 0.0, self.s[-1]))
        i = int(np.clip(np.searchsorted(self.s, s) - 1, 0, len(self.s) - 2))
        L = self.s[i + 1] - self.s[i]
        t = 0.0 if L <= 1e-9 else (s - self.s[i]) / L
        p = self.xy[i] + t * (self.xy[i + 1] - self.xy[i])
        d = self.xy[i + 1] - self.xy[i]
        return p, math.atan2(d[1], d[0]) if L > 1e-9 else 0.0


def plan(path, s0, v0, tracks, dose, vmax):
    best, best_cost, fallback, fb_slack, n_checks = None, None, None, -1e9, 0
    objs = []
    for t in tracks:
        C = np.asarray(t["cov9"], dtype=float) * dose
        p = min(max(t["tracking_score"], 0.05), 1.0)
        a = DELTA_OBJ / p
        c = float(norm.ppf(1 - a)) if a < 0.5 else 0.0
        w, l = t["size"][0], t["size"][1]
        objs.append((np.array(t["translation"][:2]), np.array(t["velocity"]), C, c, 0.5 * math.hypot(w, l)))
    for acc in ACCELS:
        s, v, slack_min, feasible = s0, v0, 1e9, True
        for h in range(1, HORIZON_STEPS + 1):
            v_new = min(max(v + acc * H_DT, 0.0), vmax)
            s += 0.5 * (v + v_new) * H_DT
            v = v_new
            e, _ = path.at(s)
            th = h * H_DT
            for m, vel, C, c, r in objs:
                mh = m + vel * th
                d = e - mh
                dist = float(np.linalg.norm(d))
                if dist > 60.0:
                    continue
                n = d / max(dist, 1e-6)
                Spp, Spv, Svv = C[0:2, 0:2], C[0:2, 6:8], C[6:8, 6:8]
                Sh = Spp + th * (Spv + Spv.T) + th * th * Svv
                slack = dist - (R_EGO + r) - c * math.sqrt(max(float(n @ Sh @ n), 0.0))
                n_checks += 1
                slack_min = min(slack_min, slack)
                if slack < 0:
                    feasible = False
        cost = -s + 2.0 * abs(acc)
        if feasible and (best_cost is None or cost < best_cost):
            best, best_cost = acc, cost
        if slack_min > fb_slack:
            fallback, fb_slack = acc, slack_min
    return (best if best is not None else fallback), best is None, n_checks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", required=True)
    ap.add_argument("--scenario-index", type=int, required=True)
    ap.add_argument("--dose", type=float, required=True)
    ap.add_argument("--seed", type=int, default=20261030)
    ap.add_argument("--out", required=True)
    ap.add_argument("--tracker-python", required=True)
    ap.add_argument("--canmot-repo", required=True)
    ap.add_argument("--worker", required=True)
    ap.add_argument("--fast-convex", action="store_true")
    a = ap.parse_args()
    from metadrive.envs.scenario_env import ScenarioEnv
    t_setup0 = time.perf_counter()
    worker = subprocess.Popen([a.tracker_python, "-B", a.worker, "my_machine"] + (["--fast-convex"] if a.fast_convex else []), cwd=a.canmot_repo,
                              stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, bufsize=1)
    env = ScenarioEnv(dict(data_directory=a.db, start_scenario_index=a.scenario_index, num_scenarios=1, use_render=False,
                           log_level=50, reactive_traffic=False,
                           vehicle_config=dict(lidar=dict(num_lasers=0, distance=0), side_detector=dict(num_lasers=0, distance=0),
                                               lane_line_detector=dict(num_lasers=0, distance=0))))
    env.reset(seed=a.scenario_index)
    sc = env.engine.data_manager.current_scenario
    sdc = sc["metadata"]["sdc_id"]
    st = sc["tracks"][sdc]["state"]
    valid = np.asarray(st["valid"], dtype=bool)
    path = Path(np.asarray(st["position"])[valid][:, :2])
    vlog = np.linalg.norm(np.asarray(st["velocity"])[valid][:, :2], axis=1)
    n_steps = int(valid.sum()) - 1
    s_ego, v_ego, vmax = 0.0, float(vlog[0]), float(vlog.max()) + 2.0
    setup_s = time.perf_counter() - t_setup0
    rng_base = np.random.SeedSequence([a.seed, a.scenario_index])
    tim = {"sim_step_s": 0.0, "perception_s": 0.0, "tracker_rpc_s": 0.0, "tracker_compute_s": 0.0, "planner_s": 0.0}
    trace = hashlib.sha256()
    acc, frame, n_tracks, infeasible, checks = 0.0, 0, [], 0, 0
    t_loop0 = time.perf_counter()
    for k in range(n_steps):
        if k % PERC_EVERY == 0:
            t0 = time.perf_counter()
            ego_p, _ = path.at(s_ego)
            rng = np.random.default_rng(np.random.SeedSequence([a.seed, a.scenario_index, frame]))
            dets = []
            o2s = env.engine.traffic_manager.obj_id_to_scenario_id
            for oid, obj in sorted(env.engine.get_objects().items(), key=lambda kv: (str(o2s.get(kv[0], "")), round(float(kv[1].position[0]), 3), round(float(kv[1].position[1]), 3))):
                if obj is env.agent:
                    continue
                cls = obj_class(obj)
                if cls is None:
                    continue
                pos = np.asarray(obj.position, dtype=float)
                if np.linalg.norm(pos - ego_p) > 50.0:
                    continue
                sp, sv, sy = NOISE[cls]
                vel = np.asarray(obj.velocity, dtype=float)[:2]
                yaw = float(obj.heading_theta) + rng.normal(0, sy)
                dets.append({"translation": [float(pos[0] + rng.normal(0, sp)), float(pos[1] + rng.normal(0, sp)), 1.0],
                             "size": [float(getattr(obj, "WIDTH", 1.8)), float(getattr(obj, "LENGTH", 4.5)), float(getattr(obj, "HEIGHT", 1.6))],
                             "velocity": [float(vel[0] + rng.normal(0, sv)), float(vel[1] + rng.normal(0, sv))],
                             "rotation": quat_from_yaw(yaw), "detection_score": SCORE[cls], "detection_name": cls})
            t1 = time.perf_counter()
            worker.stdin.write(json.dumps({"cmd": "frame", "frame_id": frame, "dets": dets}) + "\n")
            worker.stdin.flush()
            resp = json.loads(worker.stdout.readline())
            t2 = time.perf_counter()
            acc, inf, nc = plan(path, s_ego, v_ego, resp["tracks"], a.dose, vmax)
            t3 = time.perf_counter()
            tim["perception_s"] += t1 - t0
            tim["tracker_rpc_s"] += t2 - t1
            tim["tracker_compute_s"] += resp["t_s"]
            tim["planner_s"] += t3 - t2
            infeasible += int(inf)
            checks += nc
            n_tracks.append(len(resp["tracks"]))
            trace.update(json.dumps([frame, round(s_ego, 9), round(v_ego, 9), acc, len(resp["tracks"]),
                                     [round(x, 9) for t in resp["tracks"] for x in t["translation"][:2]]]).encode())
            frame += 1
        v_new = min(max(v_ego + acc * DT_SIM, 0.0), vmax)
        s_ego += 0.5 * (v_ego + v_new) * DT_SIM
        v_ego = v_new
        p, h = path.at(s_ego)
        t0 = time.perf_counter()
        env.agent.set_position([float(p[0]), float(p[1])])
        env.agent.set_heading_theta(h)
        env.agent.set_velocity([v_ego * math.cos(h), v_ego * math.sin(h)])
        env.step([0.0, 0.0])
        tim["sim_step_s"] += time.perf_counter() - t0
    loop_s = time.perf_counter() - t_loop0
    worker.stdin.write(json.dumps({"cmd": "quit"}) + "\n")
    worker.stdin.flush()
    worker.wait(timeout=30)
    env.close()
    rec = {"scenario_index": a.scenario_index, "scenario_id": sc["metadata"].get("scenario_id", sc["metadata"].get("id")),
           "dose": a.dose, "seed": a.seed, "steps": n_steps, "perception_frames": frame, "setup_s": setup_s, "loop_s": loop_s,
           "process_wall_s": time.perf_counter() - T_PROC0, **tim, "mean_tracks": float(np.mean(n_tracks)) if n_tracks else 0.0,
           "planner_fallback_frames": infeasible, "constraint_checks": checks, "trace_sha256": trace.hexdigest(),
           "outcomes_computed": False, "fast_convex": bool(a.fast_convex)}
    with open(a.out, "w") as f:
        json.dump(rec, f, indent=1)
    print(json.dumps(rec))


if __name__ == "__main__":
    main()
