#!/usr/bin/env python3
"""K8 episode runner (Claude line, k8_run_v01, 1 Nov 2026) = k7_run_v01 running k8_sim_v01 (tests/make_k8_run_v01.py), with the
fit-free arms S.FITFREE (Z0, B0, B0a<alpha>, B0d<delta'>), the per-decision records written to decisions_<tag>.npz and the
per-episode calibration tables to cal_<tag>.npz.
K7 episode runner (Claude line, k7_run_v01, 1 Nov 2026) = k6_run_v02 running k7_sim_v01 (tests/make_k7_run_v01.py).
K6 episode runner (Claude line, v02, 1 Nov 2026). v02 (review R09 M6): runs k6_sim_v02; under --prereg the design is
fixed (every arm in S.ARMS, delays 0 2 4 keyframes, every non-development scene of the caches, 6 workers allowed to vary
only), and the run record carries the plan, fits, simulator, runner and manifest hashes. --mode decide runs
k6_sim_v02.run_decisions (one decision per keyframe from the logged ego's state; one "episode" per scene and arm) instead
of the closed loop; under --prereg both modes are run, each with the fixed arms.
v01: runs every (scene, arm, delay) episode of one tracker setting, in parallel over scenes, and writes:
  episodes_<tag>.jsonl   one summary per episode, sorted by (scene, arm, delay);
  counts_<tag>.npz       the in-loop constraint counts: episode index, cell, n, exceed (sparse).
Development mode (--dev) runs only the 10 nuScenes-mini scenes, which are excluded from every K6 analysis. Any other scene
needs --prereg: the K6 plan's sidecar hash, its frozen file block and the binding of the run inputs are checked first.
Usage: python -B k6_run_v02.py --caches <dir...> --fits <json> --tag <t> --out <dir> [--dev | --prereg <plan.md>]
       [--arms ...] [--delays-kf 0 2 4] [--workers n] [--scenes ...]
"""
import argparse
import hashlib
import json
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import k8_sim_v01 as S  # noqa: E402

DEV_SCENES = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077",
              "scene-1094", "scene-1100")
_G = {}


def sha256_path(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def frozen_hashes(prereg):
    side = open(prereg.replace(".md", ".sha256")).read().split()[0]
    if sha256_path(prereg) != side:
        raise SystemExit("K8 plan hash mismatch")
    txt = open(prereg, encoding="utf-8").read()
    block = txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0]
    hashes = {}
    for ln in block.strip().splitlines():
        if not ln.strip() or ln.startswith(("#", "(")):
            continue
        h, p = ln.split("  ", 1)
        if sha256_path(p.strip()) != h:
            raise SystemExit("frozen file changed: " + p)
        hashes[h] = p.strip()
    assert len(hashes) > 10, "frozen block is empty"
    return side, hashes


def _init(fits_path):
    _G["fits"] = json.load(open(fits_path)) if fits_path else None


def _scene_job(job):
    path, scene, arms, delays, mode = job
    sc = S.Scene(path)
    fits_all = _G["fits"]
    fold = None
    if fits_all is not None:
        fold = fits_all["fold_of_scene"][scene]
        steps = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
        fits = [fits_all["fits"][str(fold)][h] for h in steps]
    else:
        fits = None
    out = []
    t0 = time.perf_counter()
    for arm in arms:
        if mode == "decide":
            if arm == "LOG":
                continue
            o, c = S.run_decisions(sc, arm, fits if arm not in S.FITFREE else None)
            o["scene"], o["fold"], o["delay_kf"] = scene, fold, 0
            out.append((o, c))
            continue
        for d in delays:
            o, c = S.run_episode(sc, arm, fits if arm not in S.FITFREE else None, d)
            o["scene"], o["fold"] = scene, fold
            out.append((o, c))
    return scene, out, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caches", nargs="+", required=True)
    ap.add_argument("--fits", default=None)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--prereg", default=None)
    ap.add_argument("--arms", nargs="+", default=list(S.ARMS))
    ap.add_argument("--delays-kf", nargs="+", type=int, default=[0, 2, 4])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--scenes", nargs="*", default=None)
    ap.add_argument("--mode", choices=["loop", "decide"], default="loop")
    a = ap.parse_args()
    t0 = time.time()
    jobs = []
    for cdir in a.caches:
        man = json.load(open(os.path.join(cdir, "MANIFEST.json")))
        for scene, info in sorted(man["scenes"].items()):
            jobs.append((os.path.join(cdir, scene + ".npz"), scene, info["sha256"]))
    if a.scenes:
        jobs = [j for j in jobs if j[1] in set(a.scenes)]
    if a.dev:
        jobs = [j for j in jobs if j[1] in DEV_SCENES]
        assert len(jobs) == len(DEV_SCENES) or a.scenes, "development scenes missing from the caches"
        pre = "DEV MODE (nuScenes-mini scenes only; excluded from K8)"
    else:
        assert a.prereg, "confirmatory scenes need --prereg"
        assert list(a.arms) == list(S.ARMS) and list(a.delays_kf) == [0, 2, 4] and not a.scenes,             "under --prereg the design is fixed: all arms, delays 0 2 4, every scene"
        pre, hashes = frozen_hashes(a.prereg)
        jobs = [j for j in jobs if j[1] not in DEV_SCENES]
        need = [a.fits, os.path.abspath(S.__file__), os.path.abspath(__file__)] + [os.path.join(c, "MANIFEST.json") for c in a.caches]
        for p in need:
            assert sha256_path(p) in hashes, "run input not frozen: " + p
    for p, scene, h in jobs:
        assert sha256_path(p) == h, "cache file differs from its manifest: " + p
    os.makedirs(a.out, exist_ok=True)
    results = {}
    times = []
    with Pool(a.workers, initializer=_init, initargs=(a.fits,)) as pool:
        for i, (scene, out, dt) in enumerate(pool.imap_unordered(_scene_job, [(p, s, a.arms, a.delays_kf, a.mode) for p, s, _ in jobs], chunksize=1)):
            results[scene] = out
            times.append(dt)
            if (i + 1) % 25 == 0 or i + 1 == len(jobs):
                print("scenes %d/%d  %.0f s" % (i + 1, len(jobs), time.time() - t0), flush=True)
    arm_rank = {x: i for i, x in enumerate(a.arms)}
    eps, ce, cc, cn, cx = [], [], [], [], []
    dec = {f: [] for f in S.DEC_FIELDS + ("stats", "episode")}
    cal_e, cal_k, cal_v = [], [], []
    for scene in sorted(results):
        for o, c in sorted(results[scene], key=lambda oc: (arm_rank[oc[0]["arm"]], oc[0]["delay_kf"])):
            idx = len(eps)
            o["episode"] = idx
            decs = o.pop("decisions", None)
            if decs is not None:
                for f_ in S.DEC_FIELDS + ("stats",):
                    dec[f_].extend(decs[f_])
                dec["episode"].extend([idx] * len(decs["k"]))
            cal = o.pop("cal", None) or {}
            for key in sorted(cal):
                cal_e.append(idx)
                cal_k.append(key)
                cal_v.append(cal[key])
            eps.append(o)
            for cell in sorted(c):
                ce.append(idx)
                cc.append(cell)
                cn.append(c[cell][0])
                cx.append(c[cell][1])
    ep_path, ct_path = os.path.join(a.out, "episodes_%s.jsonl" % a.tag), os.path.join(a.out, "counts_%s.npz" % a.tag)
    with open(ep_path, "w") as f:
        for o in eps:
            f.write(json.dumps(o) + "\n")
    np.savez_compressed(ct_path, episode=np.array(ce, np.int32), cell=np.array(cc, np.int32),
                        n=np.array(cn, np.int32), exceed=np.array(cx, np.int32))
    dc_path = os.path.join(a.out, "decisions_%s.npz" % a.tag)
    np.savez_compressed(dc_path, episode=np.array(dec["episode"], np.int32), k=np.array(dec["k"], np.int32), ob=np.array(dec["ob"], np.int8),
                        infeasible=np.array(dec["infeasible"], np.int8), lam=np.array(dec["lam"], float), v_now=np.array(dec["v_now"], float),
                        v_chosen=np.array(dec["v_chosen"], float), v_log=np.array(dec["v_log"], float), ds_plan=np.array(dec["ds_plan"], float),
                        ds_log=np.array(dec["ds_log"], float), min_gap=np.array(dec["min_gap"], float), ttc=np.array(dec["ttc"], float),
                        n_enf_tracks=np.array(dec["n_enf_tracks"], np.int32), stats=np.array(dec["stats"], float).reshape(-1, S.N_ST))
    cl_path = os.path.join(a.out, "cal_%s.npz" % a.tag)
    np.savez_compressed(cl_path, episode=np.array(cal_e, np.int32), key=np.array(cal_k, np.int32),
                        values=np.array(cal_v, float).reshape(-1, S.N_CAL), fields=np.array(S.CAL_FIELDS))
    rec = {"tag": a.tag, "mode": a.mode, "prereg": pre, "arms": a.arms, "delays_kf": a.delays_kf, "scenes": len(results), "episodes": len(eps),
           "fits": a.fits, "fits_sha256": sha256_path(a.fits) if a.fits else None, "sim_sha256": sha256_path(S.__file__),
           "runner_sha256": sha256_path(__file__), "manifest_sha256": [sha256_path(os.path.join(c, "MANIFEST.json")) for c in a.caches],
           "caches": [os.path.abspath(c) for c in a.caches], "episodes_sha256": sha256_path(ep_path), "counts_sha256": sha256_path(ct_path),
           "decisions_sha256": sha256_path(dc_path), "decisions": len(dec["k"]), "cal_sha256": sha256_path(cl_path),
           "scene_names": sorted(results), "numpy": np.__version__, "seconds": round(time.time() - t0, 1),
           "scene_seconds_median": float(np.median(times)) if times else None}
    json.dump(rec, open(os.path.join(a.out, "run_record_%s.json" % a.tag), "w"), indent=1)
    print(json.dumps(rec))
    print("K8 RUN DONE")


if __name__ == "__main__":
    main()
