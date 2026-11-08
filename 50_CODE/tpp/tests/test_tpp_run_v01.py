#!/usr/bin/env python3
"""Tests for the TPP arm runner (v01, 2 Nov 2026). Run in tpp38 with `python -I`; synthetic scenes only, except R9 which
reads the outputs of a tiny real run (keys + run npz given on the command line) for join and integrity checks.
  R1 identity case: straight constant-velocity vehicle / pedestrian tracks at six headings; the moment-matched 2 s mean
     lies along the track (direction, along-track and cross-track error bounds) -> the frame, x/y order, heading
     convention and offset add-back are right.
  R2 translation round trip: the same scene shifted by (+1234.5, -987.25) m gives the same world-frame outputs.
  R3 frame / rotation helpers: world <-> scene, covariance -> object axes -> world, a' S a, wrap.
  R4 V1 / V2 / weight summary on hand mixtures.
  R5 parity with Trajectron++'s own path: incremental_forward(..., full_dist=True) -> sample_model on a one-node scene
     equals our encoder step + _run_decoder under the same seed, bit for bit.
  R6 determinism: two runs of one scene are identical; the weights do not depend on the seed; the seed-to-seed spread of
     V2 at 2 s on the synthetic track is reported (the decoder conditions on sampled controls).
  R7 history bookkeeping: contiguous runs with gaps, causal derivative state equals derivative_of on the run.
  R8 registrar guard: a scene with all four edge types creates no new module.
  R9 (optional, real tiny run): one output row per keys record, keys equal, status counts, finiteness, PD of V2 for ok rows,
     npz loadable with allow_pickle=False.
Usage: python -I test_tpp_run_v01.py --tpp-root <checkout> --out <json> [--keys <keys npz> --runs <run npz> ...]
"""
import argparse
import json
import math
import os
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import tpp_common_v01 as C  # noqa: E402
import tpp_run_v01 as R  # noqa: E402

RES = {}


def check(name, cond, info=None):
    RES[name] = {"pass": bool(cond), "info": info}
    print(("PASS " if cond else "FAIL ") + name + ("  " + json.dumps(info, default=float) if info is not None else ""), flush=True)


def synth_cache(path, agents, K=12, ego=(500.0, 500.0, 0.0), shift=(0.0, 0.0)):
    """agents: list of (tid, cls, kk, x, y, yaw). Writes the fields stream_scene reads; gt = the same agents."""
    tk = np.concatenate([a[2] for a in agents]) if agents else np.zeros(0, int)
    f = lambda i: np.concatenate([np.asarray(a[i], float) for a in agents]) if agents else np.zeros(0)
    tid = np.concatenate([np.full(len(a[2]), a[0]) for a in agents]).astype(int)
    cls = np.concatenate([np.full(len(a[2]), a[1]) for a in agents]).astype(int)
    ex = np.full(K, ego[0] + shift[0]) + 0.0 * np.arange(K)
    ey = np.full(K, ego[1] + shift[1])
    z = {"kf_t": 0.5 * np.arange(K), "kf_ego": np.stack([ex, ey, np.full(K, ego[2])], -1),
         "tr_k": tk.astype(int), "tr_tid": tid, "tr_cls": cls, "tr_x": f(3) + shift[0], "tr_y": f(4) + shift[1], "tr_yaw": f(5),
         "gt_k": tk.astype(int), "gt_inst": tid, "gt_cls": cls, "gt_x": f(3) + shift[0], "gt_y": f(4) + shift[1], "gt_yaw": f(5)}
    np.savez(path, **z)
    return path


def straight(tid, cls, theta, speed, K=12, start=(100.0, 100.0), kk=None):
    kk = np.arange(K) if kk is None else np.asarray(kk)
    t = 0.5 * kk
    return (tid, cls, kk, start[0] + speed * t * math.cos(theta), start[1] + speed * t * math.sin(theta), np.full(len(kk), theta))


def predict(path, key, k, source="trk", seed=R.SEED_DEFAULT, name="synthetic"):
    _, res, steps, off = R.stream_scene(name, path, source, [(k, key)], seed)
    st, nh, out = res[(k, key)]
    return st, nh, out, off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tpp-root", required=True)
    ap.add_argument("--model", default="int_ee")
    ap.add_argument("--out", required=True)
    ap.add_argument("--keys", default=None)
    ap.add_argument("--runs", nargs="*", default=[])
    a = ap.parse_args()
    t0 = time.time()
    model_dir = os.path.join(os.path.abspath(a.tpp_root), "experiments", "nuScenes", "models", a.model)
    R.init_process(a.tpp_root, model_dir, 1)
    T = R._G
    torch = T["torch"]
    tmp = tempfile.mkdtemp(prefix="tpp_test_")
    K, kq = 12, 9

    # ---------------- R1 identity case
    rows = []
    ok_all = True
    for cls, speed, tol_dir, lo, hi, tol_x in ((0, 8.0, 10.0, 0.7, 1.3, 2.0), (4, 1.4, 25.0, 0.4, 1.6, 1.0)):
        for deg in (0, 45, 90, 135, 180, -90):
            th = math.radians(deg)
            p = synth_cache(os.path.join(tmp, "r1_%d_%d.npz" % (cls, deg)), [straight(1, cls, th, speed, K)], K)
            ty = int(C.TPP_TYPE_OF_CLS[cls])
            st, nh, out, off = predict(p, (1, ty), kq)
            w, mu, S = out
            m2, S2 = C.v2_moment_match(w[3], mu[3], S[3])
            p_k = np.array([100.0 + speed * 0.5 * kq * math.cos(th), 100.0 + speed * 0.5 * kq * math.sin(th)])
            d = m2 - p_k
            u = np.array([math.cos(th), math.sin(th)])
            along, cross = float(d @ u), float(abs(d @ np.array([-u[1], u[0]])))
            ang = math.degrees(math.atan2(d[1], d[0]) - th)
            ang = (ang + 180) % 360 - 180
            expect = 4 * 0.5 * speed
            good = st == C.ST_OK and nh == kq + 1 and abs(ang) < tol_dir and lo * expect <= along <= hi * expect and cross < tol_x \
                and C.min_eig_2x2(C.cov3(S2)) > 0
            ok_all &= good
            rows.append({"cls": C.CLASSES[cls], "heading_deg": deg, "along_m": round(along, 3), "expected_m": expect,
                         "cross_m": round(cross, 3), "dir_err_deg": round(ang, 2), "ok": bool(good)})
    check("R1_identity_straight_tracks", ok_all, rows)

    # ---------------- R2 translation round trip
    ag = [straight(1, 0, 0.3, 7.0, K), straight(2, 4, 2.0, 1.2, K, start=(110.0, 95.0)), straight(3, 1, -1.0, 4.0, K, start=(90.0, 120.0))]
    p0 = synth_cache(os.path.join(tmp, "r2a.npz"), ag, K, ego=(105.0, 80.0, 1.0))
    p1 = synth_cache(os.path.join(tmp, "r2b.npz"), ag, K, ego=(105.0, 80.0, 1.0), shift=(1234.5, -987.25))
    dm, dc = 0.0, 0.0
    for key in ((1, 0), (2, 1), (3, 0)):
        _, _, o0, off0 = predict(p0, key, kq)
        _, _, o1, off1 = predict(p1, key, kq)
        dm = max(dm, float(np.max(np.abs((o1[1] - np.array([1234.5, -987.25])) - o0[1]))))
        dc = max(dc, float(np.max(np.abs(o1[2] - o0[2])) / (np.max(np.abs(o0[2])) + 1e-9)))
    check("R2_translation_round_trip", dm < 2e-3 and dc < 2e-3, {"max_mean_diff_m": dm, "max_cov_rel_diff": dc,
                                                               "offsets": [list(off0), list(off1)]})

    # ---------------- R3 frame and rotation helpers
    rng = np.random.default_rng(1)
    err = 0.0
    for _ in range(200):
        A = rng.normal(size=(2, 2))
        S = A @ A.T + 0.1 * np.eye(2)
        yaw = rng.uniform(-4, 4)
        So = C.cov_to_axes(S, yaw)
        aL = np.array([math.cos(yaw), math.sin(yaw)])
        aT = np.array([-math.sin(yaw), math.cos(yaw)])
        err = max(err, float(np.max(np.abs(C.cov_from_axes(So, yaw) - S))), abs(So[0, 0] - aL @ S @ aL), abs(So[1, 1] - aT @ S @ aT))
        xy = rng.normal(size=(5, 2)) * 1000
        off = C.scene_offset(xy[:, 0], xy[:, 1])
        err = max(err, float(np.max(np.abs(C.to_world(C.to_scene(xy, off), off) - xy))))
        err = max(err, float(np.max(np.abs(C.cov22(C.cov3(S)) - S))))
    wr = C.wrap(np.array([3.5, -3.5, 7.0, np.pi]))
    check("R3_frame_rotation_round_trip", err < 1e-9 and np.all(wr >= -np.pi) and np.all(wr < np.pi), {"max_err": err})

    # ---------------- R4 V1 / V2 / weights
    mu = np.array([[1.0, 2.0], [1.0, 2.0]])
    S = np.array([[[2.0, 0.3], [0.3, 1.0]]] * 2)
    m2, S2 = C.v2_moment_match(np.array([0.3, 0.7]), mu, S)
    e1 = float(np.max(np.abs(m2 - mu[0])) + np.max(np.abs(S2 - S[0])))
    mu = np.array([[0.0, 0.0], [2.0, 0.0]])
    S = np.array([np.eye(2), 2 * np.eye(2)])
    w = np.array([0.25, 0.75])
    m2, S2 = C.v2_moment_match(w, mu, S)
    want_m = np.array([1.5, 0.0])
    want_S = np.array([[0.25 * 1 + 0.75 * 2 + 0.25 * 2.25 + 0.75 * 0.25, 0.0], [0.0, 0.25 + 1.5]])
    e2 = float(np.max(np.abs(m2 - want_m)) + np.max(np.abs(S2 - want_S)))
    m1, S1, i1 = C.v1_most_likely(w, mu, S)
    wm, wa, we, wn = C.weight_summary(np.full(25, 1 / 25))
    good = e1 < 1e-12 and e2 < 1e-12 and i1 == 1 and np.allclose(m1, mu[1]) and np.allclose(S1, S[1]) and abs(we - math.log(25)) < 1e-12 \
        and abs(wn - 25) < 1e-9 and abs(wm - 0.04) < 1e-12
    check("R4_v1_v2_weights", good, {"identical_components_err": e1, "two_component_err": e2})

    # ---------------- R5 parity with sample_model on a one-node scene (+ ego)
    p = synth_cache(os.path.join(tmp, "r5.npz"), [straight(1, 0, 0.7, 6.0, K)], K, ego=(400.0, 400.0, 0.0))
    z = np.load(p)
    nodes = R.node_tables(z, "trk")
    allx = np.concatenate([v[3] for v in nodes.values()])
    ally = np.concatenate([v[4] for v in nodes.values()])
    off = np.array(C.scene_offset(allx, ally))

    def build():
        env, scene = R.make_env(T, K)
        NT = env.NodeType
        objs = {}
        for key, (t, nid, kk, x, y, yaw) in nodes.items():
            hdr = R.header_of(T["hp"], C.TPP_TYPE_NAMES[t])
            objs[key] = T["Node"](node_type=NT.VEHICLE if t == 0 else NT.PEDESTRIAN, node_id=nid,
                                  data=T["DHNA"](np.zeros((1, len(hdr))), hdr), first_timestep=int(kk[0]), is_robot=(nid == "ego"))
        scene.robot = objs[("ego",)]
        tr = T["OnlineTrajectron"](T["reg"], T["hp"], "cpu")
        tr.set_environment(env, 0)
        return tr, objs

    def inputs(objs, k):
        inp = {}
        for key, (t, nid, kk, x, y, yaw) in nodes.items():
            i = list(kk).index(k)
            inp[objs[key]], _ = R.state_at(T, C.TPP_TYPE_NAMES[t], kk, x - off[0], y - off[1], yaw, i)
        return inp

    trA, oA = build()
    for k in range(kq):
        trA.incremental_forward(inputs(oA, k), maps=None, prediction_horizon=0, num_samples=0, full_dist=True)
    torch.manual_seed(123)
    dists, _ = trA.incremental_forward(inputs(oA, kq), maps=None, prediction_horizon=R.PH, num_samples=1, full_dist=True)
    dA = dists[oA[(1, 0)]]
    trB, oB = build()
    for k in range(kq + 1):
        trB.incremental_forward(inputs(oB, k), maps=None, prediction_horizon=0, num_samples=0, full_dist=True)
    torch.manual_seed(123)
    with torch.no_grad():
        dB, _ = trB._run_decoder(oB[(1, 0)], R.PH, 1, None, z_mode=False, gmm_mode=False, full_dist=True, all_z_sep=False)
    same = all(torch.equal(x, y) for x, y in ((dA.mus, dB.mus), (dA.log_pis, dB.log_pis), (dA.get_covariance_matrix(), dB.get_covariance_matrix())))
    check("R5_parity_with_sample_model", same and len(dists) == 1, {"mus_shape": list(dA.mus.shape), "nodes_predicted": len(dists)})

    # ---------------- R6 determinism and seed dependence
    ag = [straight(1, 0, 0.3, 7.0, K), straight(2, 4, 2.0, 1.2, K, start=(110.0, 95.0))]
    p = synth_cache(os.path.join(tmp, "r6.npz"), ag, K, ego=(105.0, 80.0, 1.0))
    _, ra, _, _ = R.stream_scene("s", p, "trk", [(kq, (1, 0)), (kq, (2, 1))], 7)
    _, rb, _, _ = R.stream_scene("s", p, "trk", [(kq, (2, 1)), (kq, (1, 0))], 7)
    det = all(np.array_equal(ra[q][2][i], rb[q][2][i]) for q in ra for i in range(3))
    spread, wdiff = {}, 0.0
    for key, nm in (((1, 0), "vehicle"), ((2, 1), "pedestrian")):
        vs = []
        for sd in range(8):
            _, _, out, _ = predict(p, key, kq, seed=sd)
            m2, S2 = C.v2_moment_match(out[0][3], out[1][3], out[2][3])
            vs.append((m2, S2, out[0][3]))
        tr_ = np.array([np.trace(v[1]) for v in vs])
        wdiff = max(wdiff, max(float(np.max(np.abs(v[2] - vs[0][2]))) for v in vs))
        spread[nm] = {"v2_mean_range_m": float(np.max(np.ptp(np.array([v[0] for v in vs]), axis=0))),
                      "v2_trace_cv": float(np.std(tr_) / np.mean(tr_))}
    check("R6_determinism_and_seed_dependence", det and wdiff == 0.0, {"weights_max_diff_across_seeds": wdiff, "seed_spread_synthetic": spread})

    # ---------------- R7 history bookkeeping
    kk = np.array([0, 1, 2, 4, 5, 6, 7, 9])
    runs = C.contiguous_run_lengths(kk)
    x = np.array([0.0, 1.0, 2.5, 6.0, 7.0, 8.5, 10.0, 14.0])
    y = 0.5 * x
    yaw = np.array([0.1, 0.2, 0.3, 3.1, -3.1, -3.0, 3.0, 0.0])
    good = list(runs) == [1, 2, 3, 1, 2, 3, 4, 1]
    d = T["derivative_of"]
    for i in range(len(kk)):
        st, n = R.state_at(T, "VEHICLE", kk, x, y, yaw, i)
        j = i - n + 1
        vx = d(x[j:i + 1], C.DT)
        hd = C.wrap(yaw[j:i + 1])
        want = [x[i], y[i], vx[-1], d(y[j:i + 1], C.DT)[-1], d(vx, C.DT)[-1], d(d(y[j:i + 1], C.DT), C.DT)[-1], hd[-1], d(hd, C.DT, radian=True)[-1]]
        good &= n == runs[i] and np.allclose(st[0], want)
        if n == 1:
            good &= np.all(st[0][2:6] == 0) and st[0][7] == 0
    st6, _ = R.state_at(T, "VEHICLE", kk, x, y, yaw, 5)
    hs = C.hist_stratum(np.array([1, 2, 3, 4, 5, 9]))
    good &= abs(st6[0][2] - 3.0) < 1e-12 and list(hs) == [-1, 0, 1, 1, 2, 2]
    check("R7_history_and_causal_state", good, {"runs": runs.tolist(), "heading_rate_across_pi": float(st6[0][7])})

    # ---------------- R8 registrar guard with all edge types
    ag = [straight(1, 0, 0.0, 5.0, K, start=(100.0, 100.0)), straight(2, 1, 0.1, 5.0, K, start=(100.0, 106.0)),
          straight(3, 4, 1.6, 1.3, K, start=(108.0, 103.0)), straight(4, 4, -1.5, 1.1, K, start=(104.0, 98.0))]
    p = synth_cache(os.path.join(tmp, "r8.npz"), ag, K, ego=(95.0, 100.0, 0.0))
    keys0 = sorted(T["reg"].model_dict.keys())
    _, res, steps, _ = R.stream_scene("s", p, "trk", [(kq, (1, 0)), (kq, (3, 1))], 1)
    edge_mods = sorted(k_ for k_ in keys0 if "edge_encoder" in k_)
    check("R8_registrar_guard", sorted(T["reg"].model_dict.keys()) == keys0 and all(res[q][0] == C.ST_OK for q in res)
          and len(edge_mods) == 4, {"edge_encoders": edge_mods, "max_edges": float(np.max(steps[:, 2])), "modules": len(keys0)})

    # ---------------- R9 optional: real tiny run integrity and join
    if a.keys and a.runs:
        kz = np.load(a.keys, allow_pickle=False)
        info, good = {}, True
        for rp in a.runs:
            z = np.load(rp, allow_pickle=False)
            sel = z["rec_index"]
            g = (len(np.unique(sel)) == len(sel) and np.array_equal(z["rec_k"], kz["rec_k"][sel]) and np.array_equal(z["rec_pair"], kz["rec_pair"][sel])
                 and np.array_equal(z["rec_h"], kz["rec_h"][sel]) and np.array_equal(z["rec_s"], kz["rec_s"][sel]))
            run_scenes = set(str(s) for s in z["scenes_run"])
            want = np.nonzero(np.isin(kz["scene_names"][kz["rec_s"]], list(run_scenes)))[0]
            g &= np.array_equal(np.sort(sel), want)
            ok = z["status"] == C.ST_OK
            g &= bool(np.all(np.isfinite(z["v2_mu"][ok])) and np.all(np.isfinite(z["v2_cov"][ok])) and np.all(C.min_eig_2x2(z["v2_cov"][ok]) > 0))
            g &= bool(np.all(z["status"][~ok] != C.ST_OK))
            items_in = np.isin(kz["item_rec"], sel)
            g &= bool(items_in.sum() == np.isin(kz["scene_names"][kz["item_s"]], list(run_scenes)).sum())
            info[os.path.basename(rp)] = {"records": int(len(sel)), "ok": int(ok.sum()), "items_joined": int(items_in.sum()),
                                          "status": {C.STATUS_NAMES[c]: int(np.sum(z["status"] == c)) for c in C.STATUS_NAMES}}
            good &= g
        check("R9_real_tiny_join_and_integrity", good, info)

    out = {"tests": RES, "all_pass": all(v["pass"] for v in RES.values()), "seconds": round(time.time() - t0, 1),
           "scripts": {"tpp_run_v01": C.sha256_path(R.__file__), "tpp_common_v01": C.sha256_path(C.__file__),
                       "test_tpp_run_v01": C.sha256_path(os.path.abspath(__file__))},
           "torch": torch.__version__, "numpy": np.__version__, "python": sys.version.split()[0]}
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1, default=float)
    print("ALL_PASS" if out["all_pass"] else "SOME_FAIL")


if __name__ == "__main__":
    main()
