#!/usr/bin/env python3
"""TPP arm runner (Claude line, v01, 2 Nov 2026): Trajectron++ (ECCV 2020 code, OnlineTrajectron) on the K8 records of one
tracker's nuScenes validation cache. Run in the tpp38 environment with `python -I` (the Trajectron++ checkout is
untrusted third-party code: it is appended to the END of sys.path, never imported from the current directory).

Design: D16 Choice 3; P7-L5 C.1 and C.3.
  * One OnlineTrajectron per scene, streamed over every keyframe k = 0 .. K-1 with incremental_forward (the online API of
    the eccv2020 branch, as in trajectron/test_online.py); models int_ee (no map; the nuScenes map expansion is not on
    disk) or another model dir; hyperparameters = the model's config.json with test_online.py's argument defaults
    applied (they equal the config values for int_ee: checked and recorded).
  * Nodes per keyframe (source "trk", primary): every deployed track of the cache (score >= 0.4) whose class maps to a
    Trajectron++ type (car, truck, bus, trailer -> VEHICLE; pedestrian -> PEDESTRIAN; motorcycle, bicycle not fed), plus
    the logged ego as node 'ego' (VEHICLE, is_robot, as in process_data.py). Source "gt" (upper bound): every annotated
    instance of a mapped class instead of the tracks, plus the same ego.
  * State at k (P7-L5 C.1): position = box centre minus the scene offset of process_data.py; velocity and acceleration =
    Trajectron++'s own derivative_of on the node's contiguous history up to k (causal); VEHICLE heading = tracker yaw
    (gt: annotation yaw) wrapped to (-pi, pi], heading rate = derivative_of(heading, radian=True). One state per node per
    keyframe; a node absent at k is handled by OnlineTrajectron's own removal logic.
  * Prediction: at each keyframe, the encoders are advanced for every node (incremental_forward with
    prediction_horizon=0); then, for each record's node with >= 2 contiguous states, the decoder is run exactly as
    OnlineTrajectron.sample_model does (its _run_decoder, num_samples=1, z_mode=False, gmm_mode=False, full_dist=True,
    prediction horizon 6) under a torch seed fixed per (scene, k, node) so the output does not depend on worker or
    node order. The decoder conditions on sampled controls (gmm_mode=False), so the GMM is seed dependent.
  * Output at the record's step h + 1 (h = 3 is 2.0 s, the primary step): V1 (largest-weight component) mean and
    covariance, V2 (moment-matched) mean and covariance, the weight summary; the full 25-component mixture at step 4 for
    records with h = 3. World frame (offset added back). One row per K8 record, in the keys file's order.
  * Guards: the model registrar's module set must not change during the run (a missing module would otherwise be
    created with random weights); the checkpoint SHA-256 is recorded.
Only counts, shapes, finiteness and positive-definiteness are computed here; no ground-truth position is read.
Usage: python -I tpp_run_v01.py --tpp-root <checkout> --model int_ee --keys <keys npz> --source trk|gt --out <npz>
       [--workers n] [--scenes ...] [--seed 20261102] [--threads 1]
"""
import argparse
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_common_v01 as C  # noqa: E402

PH = 6
SEED_DEFAULT = 20261102
TEST_ONLINE_DEFAULTS = {"dynamic_edges": "yes", "edge_state_combine_method": "sum", "edge_influence_combine_method": "attention",
                        "edge_addition_filter": [0.25, 0.5, 0.75, 1.0], "edge_removal_filter": [1.0, 0.0], "batch_size": 256,
                        "k_eval": 25, "offline_scene_graph": "yes", "incl_robot_node": False, "edge_encoding": True,
                        "use_map_encoding": False}
# trajectron/test_online.py overrides these from argument_parser.py defaults (verified in the eccv2020 checkout)

_G = {}   # per-process Trajectron++ handles


def tpp_import(tpp_root):
    traj = os.path.join(os.path.abspath(tpp_root), "trajectron")
    if traj not in sys.path:
        sys.path.append(traj)                     # appended: stdlib and site-packages keep precedence
    import torch
    from environment import Environment, Scene, Node, derivative_of, DoubleHeaderNumpyArray
    from model.online.online_trajectron import OnlineTrajectron
    from model.model_registrar import ModelRegistrar
    return dict(torch=torch, Environment=Environment, Scene=Scene, Node=Node, derivative_of=derivative_of,
                DHNA=DoubleHeaderNumpyArray, OnlineTrajectron=OnlineTrajectron, ModelRegistrar=ModelRegistrar)


STANDARDIZATION = {   # experiments/nuScenes/process_data.py, verbatim values
    'PEDESTRIAN': {'position': {'x': {'mean': 0, 'std': 1}, 'y': {'mean': 0, 'std': 1}},
                   'velocity': {'x': {'mean': 0, 'std': 2}, 'y': {'mean': 0, 'std': 2}},
                   'acceleration': {'x': {'mean': 0, 'std': 1}, 'y': {'mean': 0, 'std': 1}}},
    'VEHICLE': {'position': {'x': {'mean': 0, 'std': 80}, 'y': {'mean': 0, 'std': 80}},
                'velocity': {'x': {'mean': 0, 'std': 15}, 'y': {'mean': 0, 'std': 15}, 'norm': {'mean': 0, 'std': 15}},
                'acceleration': {'x': {'mean': 0, 'std': 4}, 'y': {'mean': 0, 'std': 4}, 'norm': {'mean': 0, 'std': 4}},
                'heading': {'x': {'mean': 0, 'std': 1}, 'y': {'mean': 0, 'std': 1}, '°': {'mean': 0, 'std': np.pi},
                            'd°': {'mean': 0, 'std': 1}}}}


def load_hyperparams(model_dir):
    hp = json.load(open(os.path.join(model_dir, "config.json"), encoding="utf-8"))
    diff = {k: (hp.get(k), v) for k, v in TEST_ONLINE_DEFAULTS.items() if hp.get(k) != v}
    hp.update(TEST_ONLINE_DEFAULTS)
    return hp, diff


def init_process(tpp_root, model_dir, threads):
    T = tpp_import(tpp_root)
    T["torch"].set_num_threads(int(threads))
    hp, diff = load_hyperparams(model_dir)
    reg = T["ModelRegistrar"](model_dir, "cpu")
    reg.load_models(iter_num=12)
    T["hp"], T["hp_diff"], T["reg"] = hp, diff, reg
    T["reg_keys0"] = sorted(reg.model_dict.keys())
    _G.update(T)


def make_env(T, K):
    env = T["Environment"](node_type_list=['VEHICLE', 'PEDESTRIAN'], standardization=STANDARDIZATION)
    NT = env.NodeType
    env.attention_radius = {(NT.PEDESTRIAN, NT.PEDESTRIAN): 10.0, (NT.PEDESTRIAN, NT.VEHICLE): 20.0,
                            (NT.VEHICLE, NT.PEDESTRIAN): 20.0, (NT.VEHICLE, NT.VEHICLE): 30.0}
    env.robot_type = NT.VEHICLE
    scene = T["Scene"](timesteps=K, map=None, dt=C.DT, name="online")
    env.scenes = [scene]
    return env, scene


def header_of(hp, tname):
    return [(q, v) for q, vals in hp["state"][tname].items() for v in vals]


def node_tables(z, source):
    """Per node: key -> (type, id string, sorted keyframes, x, y, yaw). Ego first."""
    K = len(z["kf_t"])
    nodes = {("ego",): (C.TPP_VEHICLE, "ego", np.arange(K), z["kf_ego"][:, 0].astype(float), z["kf_ego"][:, 1].astype(float),
                        z["kf_ego"][:, 2].astype(float))}
    if source == "trk":
        kk, ids, cls = z["tr_k"].astype(int), z["tr_tid"].astype(int), z["tr_cls"].astype(int)
        xs, ys, yaws = z["tr_x"], z["tr_y"], z["tr_yaw"]
        pre = "trk"
    else:
        kk, ids, cls = z["gt_k"].astype(int), z["gt_inst"].astype(int), z["gt_cls"].astype(int)
        xs, ys, yaws = z["gt_x"], z["gt_y"], z["gt_yaw"]
        pre = "gt"
    typ = C.TPP_TYPE_OF_CLS[cls] if len(cls) else np.zeros(0, np.int8)
    for u in np.unique(ids) if len(ids) else []:
        for t in (C.TPP_VEHICLE, C.TPP_PEDESTRIAN):
            sel = np.nonzero((ids == u) & (typ == t))[0]
            if not len(sel):
                continue
            sel = sel[np.argsort(kk[sel], kind="stable")]
            assert len(np.unique(kk[sel])) == len(sel), "a node twice at one keyframe"
            nodes[(int(u), t)] = (t, "%s%d_%s" % (pre, int(u), C.TPP_TYPE_NAMES[t]), kk[sel], xs[sel].astype(float),
                                  ys[sel].astype(float), yaws[sel].astype(float))
    return nodes


def state_at(T, tname, kk, x, y, yaw, i):
    """State of a node at its i-th entry from its contiguous history up to that entry (causal)."""
    j = i
    while j > 0 and kk[j - 1] == kk[j] - 1:
        j -= 1
    xs, ys = x[j:i + 1], y[j:i + 1]
    d = T["derivative_of"]
    vx, vy = d(xs, C.DT), d(ys, C.DT)
    ax, ay = d(vx, C.DT), d(vy, C.DT)
    st = [xs[-1], ys[-1], vx[-1], vy[-1], ax[-1], ay[-1]]
    if tname == "VEHICLE":
        hd = C.wrap(yaw[j:i + 1])
        st += [hd[-1], d(hd, C.DT, radian=True)[-1]]
    return np.array([st], float), i - j + 1


def reduce_records(recs, res):
    """Per record (index j into recs = [(k, h, key), ...]): status, history, V1, V2, weight summary; mixture at step 4."""
    n = len(recs)
    o = {"status": np.full(n, -1, np.int8), "hist": np.zeros(n, np.int32), "v1_mu": np.full((n, 2), np.nan),
         "v2_mu": np.full((n, 2), np.nan), "v1_cov": np.full((n, 3), np.nan), "v2_cov": np.full((n, 3), np.nan),
         "w_max": np.full(n, np.nan), "w_entropy": np.full(n, np.nan), "w_neff": np.full(n, np.nan),
         "w_argmax": np.full(n, -1, np.int16), "v1_mineig": np.full(n, np.nan), "v2_mineig": np.full(n, np.nan)}
    mix_j, mix_w, mix_mu, mix_cov = [], [], [], []
    for j, (k, h, key) in enumerate(recs):
        if key is None:
            o["status"][j] = C.ST_CLASS_NOT_COVERED
            continue
        st, nh, out = res[(k, key)]
        o["hist"][j] = nh
        if out is None:
            o["status"][j] = st
            continue
        w, mu, S = out
        m1, S1, _ = C.v1_most_likely(w[h], mu[h], S[h])
        m2, S2 = C.v2_moment_match(w[h], mu[h], S[h])
        wm, wa, we, wn = C.weight_summary(w[h])
        o["v1_mu"][j], o["v1_cov"][j], o["v2_mu"][j], o["v2_cov"][j] = m1, C.cov3(S1), m2, C.cov3(S2)
        o["w_max"][j], o["w_argmax"][j], o["w_entropy"][j], o["w_neff"][j] = wm, wa, we, wn
        fin = bool(np.all(np.isfinite(np.concatenate([m1, m2, C.cov3(S1), C.cov3(S2)]))))
        o["v1_mineig"][j], o["v2_mineig"][j] = C.min_eig_2x2(C.cov3(S1)), C.min_eig_2x2(C.cov3(S2))
        # status refers to the primary V2; a singular V1 component (Unicycle with |dphi| <= 1e-2 has rank-1 position
        # covariance along its heading) is recorded in v1_mineig, not treated as a failure
        o["status"][j] = C.ST_OK if (fin and o["v2_mineig"][j] > 0) else (C.ST_NONFINITE if not fin else C.ST_NOT_PD)
        if h == 3:
            mix_j.append(j)
            mix_w.append(w[3])
            mix_mu.append(mu[3])
            mix_cov.append(C.cov3(S[3]))
    o["mix_j"] = np.array(mix_j, np.int64)
    o["mix_w"] = np.array(mix_w, np.float32).reshape(-1, 25)
    o["mix_mu"] = np.array(mix_mu, np.float64).reshape(-1, 25, 2)
    o["mix_cov"] = np.array(mix_cov, np.float64).reshape(-1, 25, 3)
    o["w_const_over_steps"] = all(np.allclose(v[2][0][0], v[2][0][3]) for v in res.values() if v[2] is not None)
    return o


def run_scene(job):
    t0 = time.time()
    scene_name, cache_path, source, recs, seed = job
    need = sorted({(k, key) for (k, h, key) in recs if key is not None}, key=str)
    _, res, steps, off = stream_scene(scene_name, cache_path, source, need, seed)
    return scene_name, reduce_records(recs, res), steps, off, time.time() - t0


def stream_scene(scene_name, cache_path, source, need, seed):
    T = _G
    torch = T["torch"]
    z = np.load(cache_path, allow_pickle=False)
    K = len(z["kf_t"])
    nodes = node_tables(z, source)
    allx = np.concatenate([v[3] for v in nodes.values()])
    ally = np.concatenate([v[4] for v in nodes.values()])
    off = np.array(C.scene_offset(allx, ally))
    env, scene = make_env(T, K)
    hp = T["hp"]
    NT = env.NodeType
    tobj = {C.TPP_VEHICLE: NT.VEHICLE, C.TPP_PEDESTRIAN: NT.PEDESTRIAN}
    objs, pos_index = {}, {}
    for key, (t, nid, kk, x, y, yaw) in nodes.items():
        tname = C.TPP_TYPE_NAMES[t]
        hdr = header_of(hp, tname)
        o = T["Node"](node_type=tobj[t], node_id=nid, data=T["DHNA"](np.zeros((1, len(hdr))), hdr),
                      first_timestep=int(kk[0]), is_robot=(nid == "ego"))
        objs[key] = o
        pos_index[key] = {int(kv): i for i, kv in enumerate(kk)}
    scene.robot = objs[("ego",)]
    tr = T["OnlineTrajectron"](T["reg"], hp, "cpu")
    tr.set_environment(env, 0)          # scene has no nodes: one empty fast-forward step, nothing is consumed
    # needed predictions: k -> list of node keys
    need_by_k = {}
    for (k, key) in need:
        need_by_k.setdefault(int(k), set()).add(key)
    res = {}
    steps = []
    for k in range(K):
        inp, hist = {}, {}
        for key, (t, nid, kk, x, y, yaw) in nodes.items():
            i = pos_index[key].get(k)
            if i is None:
                continue
            st, n = state_at(T, C.TPP_TYPE_NAMES[t], kk, x - off[0], y - off[1], yaw, i)
            inp[objs[key]] = st
            hist[key] = n
        ts = time.time()
        tr.incremental_forward(inp, maps=None, prediction_horizon=0, num_samples=0, full_dist=True)
        n_dec = 0
        for key in sorted(need_by_k.get(k, ()), key=str):
            if key not in objs or key not in hist:
                res[(k, key)] = (C.ST_NO_GT_NODE if source == "gt" else C.ST_NOT_PREDICTED, hist.get(key, 0), None)
                continue
            if hist[key] < C.MIN_HISTORY:
                res[(k, key)] = (C.ST_SHORT_HISTORY, hist[key], None)
                continue
            node = objs[key]
            if node not in tr.node_models_dict or node in tr.removed_nodes:
                res[(k, key)] = (C.ST_NOT_PREDICTED, hist[key], None)
                continue
            torch.manual_seed(C.node_seed(scene_name, k, node.id, seed))
            with torch.no_grad():                    # as OnlineTrajectron.sample_model
                dist, _ = tr._run_decoder(node, PH, 1, None, z_mode=False, gmm_mode=False, full_dist=True, all_z_sep=False)
                w = torch.softmax(dist.log_pis, dim=-1).numpy()[0, 0].astype(float)          # (PH, 25)
                mu = dist.mus.numpy()[0, 0].astype(float) + off[None, None, :]                # (PH, 25, 2)
                S = dist.get_covariance_matrix().numpy()[0, 0].astype(float)                  # (PH, 25, 2, 2)
            res[(k, key)] = (C.ST_OK, hist[key], (w[:4], mu[:4], S[:4]))
            n_dec += 1
        steps.append((k, len(inp), int(tr.scene_graph.get_num_edges()) if tr.scene_graph is not None and tr.scene_graph.nodes.size else 0,
                      n_dec, time.time() - ts))
    keys_after = sorted(T["reg"].model_dict.keys())
    assert keys_after == T["reg_keys0"], "the model registrar gained modules (random init) in " + scene_name
    return scene_name, res, np.array(steps, float).reshape(-1, 5), off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tpp-root", required=True)
    ap.add_argument("--model", default="int_ee")
    ap.add_argument("--keys", required=True, help="tpp_keys_v01 output for this tracker")
    ap.add_argument("--source", choices=("trk", "gt"), required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--seed", type=int, default=SEED_DEFAULT)
    ap.add_argument("--scenes", nargs="*", default=None)
    a = ap.parse_args()
    t0 = time.time()
    model_dir = os.path.join(os.path.abspath(a.tpp_root), "experiments", "nuScenes", "models", a.model)
    ckpt = os.path.join(model_dir, "model_registrar-12.pt")
    kz = np.load(a.keys, allow_pickle=False)
    names = [str(s) for s in kz["scene_names"]]
    cache_dir = str(kz["cache_dir"])
    scenes = [s for s in names if (not a.scenes or s in a.scenes)]
    rs = kz["rec_s"]
    n_rec = len(rs)
    # node key of each record for this source
    if a.source == "trk":
        rkey = [(int(t), int(ty)) if ty >= 0 else None for t, ty in zip(kz["rec_tid"], kz["rec_tpp_type"])]
    else:
        gty = C.TPP_TYPE_OF_CLS[kz["rec_gt_cls"]] if n_rec else np.zeros(0, np.int8)
        rkey = [(int(i), int(ty)) if ty >= 0 else None for i, ty in zip(kz["rec_inst"], gty)]
    jobs = []
    for si, s in enumerate(names):
        if s not in scenes:
            continue
        idx = np.nonzero(rs == si)[0]
        recs = [(int(kz["rec_k"][i]), int(kz["rec_h"][i]), rkey[i]) for i in idx]
        jobs.append((s, os.path.join(cache_dir, s + ".npz"), a.source, recs, a.seed))
    init_args = (a.tpp_root, model_dir, a.threads)
    if a.workers > 1:
        with Pool(a.workers, initializer=init_process, initargs=init_args) as pool:
            results = []
            for i, r in enumerate(pool.imap_unordered(run_scene, jobs, chunksize=1)):
                results.append(r)
                print("scenes %d/%d  %.0f s  (%s %.1f s)" % (i + 1, len(jobs), time.time() - t0, r[0], r[4]), flush=True)
    else:
        init_process(*init_args)
        results = []
        for i, j in enumerate(jobs):
            results.append(run_scene(j))
            print("scenes %d/%d  %.0f s  (%s %.1f s)" % (i + 1, len(jobs), time.time() - t0, j[0], results[-1][4]), flush=True)
    if a.workers <= 1:
        hp_diff = _G["hp_diff"]
        reg_keys = _G["reg_keys0"]
    else:
        hp_diff, reg_keys = load_hyperparams(model_dir)[1], None
    by_scene = {r[0]: r for r in results}
    # assemble one row per record (records of the requested scenes only)
    # one row per record of the scenes run, in the keys file's order (scene order, then the scene's record order)
    sel = np.concatenate([np.nonzero(rs == names.index(s))[0] for s in scenes]) if scenes else np.zeros(0, np.int64)
    assert np.all(np.diff(sel) > 0), "keys records are not grouped by scene in scene order"
    n = len(sel)
    cols = ("status", "hist", "v1_mu", "v1_cov", "v2_mu", "v2_cov", "w_max", "w_argmax", "w_entropy", "w_neff", "v1_mineig",
            "v2_mineig")
    out = {c: np.concatenate([by_scene[s][1][c] for s in scenes]) if scenes else np.zeros(0) for c in cols}
    base = np.cumsum([0] + [len(by_scene[s][1]["status"]) for s in scenes])[:-1]
    out["mix_rec"] = np.concatenate([by_scene[s][1]["mix_j"] + b for s, b in zip(scenes, base)]) if scenes else np.zeros(0, np.int64)
    for c in ("mix_w", "mix_mu", "mix_cov"):
        out[c] = np.concatenate([by_scene[s][1][c] for s in scenes]) if scenes else np.zeros((0, 25))
    status = out["status"]
    assert len(status) == n and np.all(status >= 0)
    w_const = all(by_scene[s][1]["w_const_over_steps"] for s in scenes)
    steps = {s: by_scene[s][2] for s in scenes}
    out.update({"rec_index": sel.astype(np.int64), "rec_s": rs[sel].astype(np.int32), "rec_k": kz["rec_k"][sel], "rec_h": kz["rec_h"][sel],
           "rec_pair": kz["rec_pair"][sel], "rec_row": kz["rec_row"][sel], "rec_inst": kz["rec_inst"][sel],
           "step": np.array([C.STEP_OF_H[h] for h in kz["rec_h"][sel]], np.int8),
           "scene_names": np.array(names), "scenes_run": np.array(scenes),
           "scene_offset": np.array([by_scene[s][3] for s in scenes]), "scene_seconds": np.array([by_scene[s][4] for s in scenes]),
           "steps_scene": np.concatenate([np.full(len(steps[s]), names.index(s), np.int32) for s in scenes]) if scenes else np.zeros(0, np.int32),
           "steps_k_nodes_edges_dec_sec": np.concatenate([steps[s] for s in scenes]) if scenes else np.zeros((0, 5)),
           "source": np.array(a.source), "model": np.array(a.model)})
    meta = {"source": a.source, "model": a.model, "checkpoint": ckpt, "checkpoint_sha256": C.sha256_path(ckpt),
            "weights_constant_over_steps": bool(w_const),
            "config_sha256": C.sha256_path(os.path.join(model_dir, "config.json")), "keys": os.path.abspath(a.keys),
            "keys_sha256": C.sha256_path(a.keys), "seed": a.seed, "ph": PH, "hp_overrides_differing_from_config": hp_diff,
            "registrar_modules": reg_keys, "workers": a.workers, "threads": a.threads,
            "scripts": {"tpp_run_v01": C.sha256_path(os.path.abspath(__file__)), "tpp_common_v01": C.sha256_path(C.__file__)},
            "seconds": round(time.time() - t0, 1)}
    out["meta_json"] = np.array(json.dumps(meta))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    np.savez_compressed(a.out, **out)
    cnt = {C.STATUS_NAMES[c]: int(np.sum(status == c)) for c in C.STATUS_NAMES}
    okm = status == C.ST_OK
    integ = {"v1_cov_not_pd_among_ok": int(np.sum(out["v1_mineig"][okm] <= 0)),
             "v1_cov_not_pd_among_ok_by_step": {str(s): int(np.sum(out["v1_mineig"][okm & (out["step"] == s)] <= 0)) for s in (1, 2, 3, 4)},
             "v2_mineig_min_among_ok": float(np.min(out["v2_mineig"][okm])) if okm.any() else None,
             "mixture_rows_step4": int(len(out["mix_rec"])), "all_ok_finite": bool(np.all(np.isfinite(out["v2_cov"][okm])))}
    summ = dict(meta, records=int(n), status_counts=cnt, integrity=integ, out_sha256=C.sha256_path(a.out))
    json.dump(summ, open(a.out.replace(".npz", "_summary.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "registrar_modules"}))
    print("TPP RUN V01 DONE")


if __name__ == "__main__":
    main()
