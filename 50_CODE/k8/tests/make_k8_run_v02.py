#!/usr/bin/env python3
"""Writes 50_CODE/k8/k8_run_v02.py from 50_CODE/k8/k8_run_v01.py (Claude line, 1 Nov 2026; 90_DECISIONS/D14_K8_DESIGN_v04.md
section 5 item 1, applying 70_TESTS/R15_K8_CODE_AND_DEV_REVIEW_v01.md C1, m12, m13). Every change is a text replacement asserted to
match exactly once (test T5 reproduces the file). Changes:
  * it runs k8_sim_v02 (decisions_<tag>.npz carries the v02 fields, the 44 relied-on counts and the 6 track counts);
  * C1: a third run mode --exploratory (D14 v04 section 5.1): the full design (every arm, delays 0 2 4 keyframes in loop mode,
    every non-development scene of the caches, no --scenes), the development scenes asserted absent, the 840 non-development
    scenes asserted present; the hashes of the sim, the runner, the fits, the manifests, k6_sim_v02 and the analysis (with
    k6_analyse_v02 and m_lib_v04, which it imports) are written to launch_record_<tag>.json BEFORE any scene is simulated and
    re-checked at the end; every output is stamped "EXPLORATORY: nuScenes development evidence, not a confirmation";
  * --dry-run (with --exploratory or --dev): prints the scene list, the hashes and the run record, writes the launch record
    marked dry_run, and exits before any scene cache is read or simulated;
  * m12: --dev asserts that every scene run is a development scene (also those named by --scenes) and the record says DEV MODE;
  * m13: each worker converts its scene's episodes to numpy and writes a per-scene shard (shards_<tag>/<scene>.npz) instead of
    returning Python lists; the main process keeps only the episode summaries and merges the shards in (scene, arm, delay)
    order at the end, so the outputs have v01's layout; --resume reuses shards whose code, fits and cache hashes match;
  * the frozen-plan path (--prereg) is v01's (design lock, frozen-file block, binding of the run inputs)."""
import os

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(K8, "k8_run_v01.py"), encoding="utf-8").read()

HEAD_OLD = ('"""K8 episode runner (Claude line, k8_run_v01, 1 Nov 2026) = k7_run_v01 running k8_sim_v01 (tests/make_k8_run_v01.py), with the\n')
HEAD_NEW = ('"""K8 episode runner (Claude line, k8_run_v02, 1 Nov 2026) = k8_run_v01 with the R15 changes (tests/make_k8_run_v02.py;\n'
            '90_DECISIONS/D14_K8_DESIGN_v04.md section 5.1):\n'
            '  * runs k8_sim_v02; three run modes, exactly one of them: --dev (the 10 development scenes only; asserted), --exploratory\n'
            '    (the full design on every non-development scene, hash-logged before launch; outputs stamped EXPLORATORY), --prereg (a\n'
            '    frozen K8 plan, v01\'s path); --dry-run with --dev or --exploratory stops before any scene is read or simulated;\n'
            '  * per-scene shards written by the workers (numpy, shards_<tag>/), merged in (scene, arm, delay) order; --resume.\n'
            'Exploratory usage: python -B k8_run_v02.py --caches <train> <val> --fits <k7_fits_<t>_v01.json> --tag <t>_<mode>\n'
            '       --mode decide|loop --out <dir> --exploratory [--workers n] [--resume] [--dry-run]\n'
            'K8 episode runner (Claude line, k8_run_v01, 1 Nov 2026) = k7_run_v01 running k8_sim_v01 (tests/make_k8_run_v01.py), with the\n')
IMP_OLD = 'import k8_sim_v01 as S  # noqa: E402\n'
IMP_NEW = 'import k8_sim_v02 as S  # noqa: E402\n'
DEV_OLD = ('              "scene-1094", "scene-1100")\n'
           '_G = {}\n')
DEV_NEW = ('              "scene-1094", "scene-1100")\n'
           '_G = {}\n'
           'EXPLORATORY_STAMP = "EXPLORATORY: nuScenes development evidence, not a confirmation"\n'
           'DEV_STAMP = "DEV MODE (nuScenes-mini scenes only; excluded from K8)"\n'
           'N_NONDEV = 840                       # the non-development scenes of the 850 nuScenes trainval scenes in the caches\n'
           'W_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))\n'
           'CODE_FILES = {"sim": os.path.abspath(S.__file__), "runner": os.path.abspath(__file__),\n'
           '              "k6_sim_v02": os.path.join(W_ROOT, "50_CODE", "k6", "k6_sim_v02.py"),\n'
           '              "analysis": os.path.join(W_ROOT, "50_CODE", "k8", "k8_analyse_v02.py"),\n'
           '              "k6_analyse_v02": os.path.join(W_ROOT, "50_CODE", "k6", "k6_analyse_v02.py"),\n'
           '              "m_lib_v04": os.path.join(W_ROOT, "50_CODE", "m", "m_lib_v04.py")}\n')

TAIL_START = 'def _init(fits_path):\n'
assert s.count(TAIL_START) == 1
TAIL_NEW = r'''def code_hashes(fits, caches):
    """The hashes logged before launch and asserted equal at analysis time (D14 v04 section 5.1)."""
    h = {k + "_sha256": sha256_path(p) for k, p in CODE_FILES.items()}
    h["fits_sha256"] = sha256_path(fits) if fits else None
    h["manifest_sha256"] = [sha256_path(os.path.join(c, "MANIFEST.json")) for c in caches]
    return h


def _init(fits_path):
    _G["fits"] = json.load(open(fits_path)) if fits_path else None


def _shard_path(shard_dir, scene):
    return os.path.join(shard_dir, scene + ".npz")


def _scene_job(job):
    """Runs every (arm, delay) episode of one scene and writes them to one shard (m13): the episode summaries (JSON), the counts,
    the per-decision rows and the calibration tables as numpy arrays, with a local episode index. Returns only the shard path."""
    path, scene, arms, delays, mode, shard_dir, meta = job
    sc = S.Scene(path)
    fits_all = _G["fits"]
    fold = None
    if fits_all is not None:
        fold = fits_all["fold_of_scene"][scene]
        steps = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
        fits = [fits_all["fits"][str(fold)][h] for h in steps]
    else:
        fits = None
    t0 = time.perf_counter()
    eps_l = []
    dec = {f: [] for f in S.DEC_FIELDS}
    dec_ep, stats, trk = [], [], []
    ce, cc, cn, cx = [], [], [], []
    ke, kk, kv = [], [], []

    def add(o, c):
        li = len(eps_l)
        decs = o.pop("decisions", None)
        cal = o.pop("cal", None) or {}
        o["_local"] = li
        eps_l.append(o)
        if decs is not None and len(decs["k"]):
            for f_ in S.DEC_FIELDS:
                dec[f_].append(np.asarray(decs[f_], np.int32 if f_ in S.DEC_INT else float))
            stats.append(np.asarray(decs["stats"], np.float32).reshape(-1, S.N_ST))
            trk.append(np.asarray(decs["trk"], np.float32).reshape(-1, S.N_TRK))
            dec_ep.append(np.full(len(decs["k"]), li, np.int32))
        for cell in sorted(c):
            ce.append(li)
            cc.append(cell)
            cn.append(c[cell][0])
            cx.append(c[cell][1])
        for key in sorted(cal):
            ke.append(li)
            kk.append(key)
            kv.append(cal[key])

    for arm in arms:
        if mode == "decide":
            if arm == "LOG":
                continue
            o, c = S.run_decisions(sc, arm, fits if arm not in S.FITFREE else None)
            o["scene"], o["fold"], o["delay_kf"] = scene, fold, 0
            add(o, c)
            continue
        for d in delays:
            o, c = S.run_episode(sc, arm, fits if arm not in S.FITFREE else None, d)
            o["scene"], o["fold"] = scene, fold
            add(o, c)
    cat = lambda L, dt, shape: np.concatenate(L) if L else np.zeros(shape, dt)  # noqa: E731
    arrs = {"dec_" + f_: cat(dec[f_], np.int32 if f_ in S.DEC_INT else float, (0,)) for f_ in S.DEC_FIELDS}
    arrs.update({"dec_episode": cat(dec_ep, np.int32, (0,)), "dec_stats": cat(stats, np.float32, (0, S.N_ST)),
                 "dec_trk": cat(trk, np.float32, (0, S.N_TRK)),
                 "cnt_episode": np.array(ce, np.int32), "cnt_cell": np.array(cc, np.int32), "cnt_n": np.array(cn, np.int32),
                 "cnt_exceed": np.array(cx, np.int32), "cal_episode": np.array(ke, np.int32), "cal_key": np.array(kk, np.int32),
                 "cal_values": np.array(kv, float).reshape(-1, S.N_CAL)})
    dt = time.perf_counter() - t0
    meta = dict(meta, scene=scene, seconds=dt)
    out = _shard_path(shard_dir, scene)
    tmp = out[:-4] + ".tmp.npz"
    np.savez_compressed(tmp, meta=np.array(json.dumps(meta)), episodes=np.array(json.dumps(eps_l)), **arrs)
    os.replace(tmp, out)
    return scene, out, len(eps_l), dt


def _shard_ok(p, meta):
    """--resume: a shard is reused only if its scene, mode, arms, delays and every code, fits and cache hash equal the current run's."""
    try:
        z = np.load(p)
        m = json.loads(str(z["meta"]))
    except Exception:
        return False
    return all(m.get(k) == v for k, v in meta.items())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caches", nargs="+", required=True)
    ap.add_argument("--fits", default=None)
    ap.add_argument("--tag", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--dev", action="store_true")
    ap.add_argument("--exploratory", action="store_true", help="D14 v04 section 5.1: the full design on every non-development scene")
    ap.add_argument("--prereg", default=None)
    ap.add_argument("--dry-run", action="store_true", help="print the scene list, hashes and run record; simulate nothing")
    ap.add_argument("--resume", action="store_true", help="reuse per-scene shards whose hashes match")
    ap.add_argument("--arms", nargs="+", default=list(S.ARMS))
    ap.add_argument("--delays-kf", nargs="+", type=int, default=[0, 2, 4])
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--scenes", nargs="*", default=None)
    ap.add_argument("--mode", choices=["loop", "decide"], default="loop")
    a = ap.parse_args()
    assert int(a.dev) + int(a.exploratory) + int(a.prereg is not None) == 1, "exactly one of --dev, --exploratory, --prereg"
    assert not (a.dry_run and a.prereg), "--dry-run is for --dev and --exploratory"
    t0 = time.time()
    jobs = []
    for cdir in a.caches:
        man = json.load(open(os.path.join(cdir, "MANIFEST.json")))
        for scene, info in sorted(man["scenes"].items()):
            jobs.append((os.path.join(cdir, scene + ".npz"), scene, info["sha256"]))
    assert len({j[1] for j in jobs}) == len(jobs), "a scene appears in two caches"
    hashes = code_hashes(a.fits, a.caches)
    exploratory = False
    if a.dev:
        if a.scenes:
            assert set(a.scenes) <= set(DEV_SCENES), "--dev runs development scenes only (R15 m12): " + ", ".join(sorted(set(a.scenes) - set(DEV_SCENES)))
            jobs = [j for j in jobs if j[1] in set(a.scenes)]
        jobs = [j for j in jobs if j[1] in DEV_SCENES]
        assert len(jobs) == len(DEV_SCENES) or a.scenes, "development scenes missing from the caches"
        assert all(j[1] in DEV_SCENES for j in jobs), "a non-development scene in a --dev run (R15 m12)"
        pre = DEV_STAMP
    elif a.exploratory:
        assert list(a.arms) == list(S.ARMS) and list(a.delays_kf) == [0, 2, 4] and not a.scenes, \
            "under --exploratory the design is fixed: all arms, delays 0 2 4, every non-development scene (no --scenes)"
        assert a.fits, "--exploratory needs the fits"
        jobs = [j for j in jobs if j[1] not in DEV_SCENES]
        assert not any(j[1] in DEV_SCENES for j in jobs), "a development scene in the exploratory run"
        assert len(jobs) == N_NONDEV, "the exploratory run needs every non-development scene: %d found, %d expected" % (len(jobs), N_NONDEV)
        pre = EXPLORATORY_STAMP
        exploratory = True
    else:
        assert list(a.arms) == list(S.ARMS) and list(a.delays_kf) == [0, 2, 4] and not a.scenes,             "under --prereg the design is fixed: all arms, delays 0 2 4, every scene"
        pre, frozen = frozen_hashes(a.prereg)
        jobs = [j for j in jobs if j[1] not in DEV_SCENES]
        need = [a.fits, os.path.abspath(S.__file__), os.path.abspath(__file__)] + [os.path.join(c, "MANIFEST.json") for c in a.caches]
        for p in need:
            assert sha256_path(p) in frozen, "run input not frozen: " + p
    scene_names = sorted(j[1] for j in jobs)
    launch = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "dry_run": bool(a.dry_run), "stamp": pre,
              "arms": a.arms, "delays_kf": a.delays_kf, "scenes": len(jobs), "scene_names": scene_names,
              "dev_scenes_present": sorted(set(scene_names) & set(DEV_SCENES)), "fits": a.fits, "caches": [os.path.abspath(c) for c in a.caches],
              "hashes": hashes, "code_files": CODE_FILES, "workers": a.workers, "numpy": np.__version__,
              "launched": time.strftime("%Y-%m-%d %H:%M:%S")}
    os.makedirs(a.out, exist_ok=True)
    lr_path = os.path.join(a.out, "launch_record_%s%s.json" % (a.tag, "_DRYRUN" if a.dry_run else ""))
    json.dump(launch, open(lr_path, "w"), indent=1)
    if a.dry_run:
        print("DRY RUN (%s): %d scenes, mode %s, %d arms, delays %s" % (pre, len(scene_names), a.mode, len(a.arms), a.delays_kf))
        print("scenes: " + " ".join(scene_names))
        print("hashes: " + json.dumps(hashes, indent=1))
        print("run record (launch): " + json.dumps({k: v for k, v in launch.items() if k != "scene_names"}, indent=1))
        print("DRY RUN: no scene cache was read and no scene was simulated; launch record " + lr_path)
        return
    for p, scene, h in jobs:
        assert sha256_path(p) == h, "cache file differs from its manifest: " + p
    shard_dir = os.path.join(a.out, "shards_%s" % a.tag)
    os.makedirs(shard_dir, exist_ok=True)
    meta0 = {"tag": a.tag, "mode": a.mode, "arms": list(a.arms), "delays_kf": list(a.delays_kf), "prereg": pre,
             "sim_sha256": hashes["sim_sha256"], "runner_sha256": hashes["runner_sha256"], "fits_sha256": hashes["fits_sha256"]}
    todo, reused = [], []
    for p, scene, h in jobs:
        meta = dict(meta0, cache_sha256=h)
        if a.resume and os.path.exists(_shard_path(shard_dir, scene)) and _shard_ok(_shard_path(shard_dir, scene), dict(meta, scene=scene)):
            reused.append(scene)
            continue
        todo.append((p, scene, a.arms, a.delays_kf, a.mode, shard_dir, meta))
    times = []
    if todo:
        with Pool(a.workers, initializer=_init, initargs=(a.fits,)) as pool:
            for i, (scene, sp, n_ep, dt) in enumerate(pool.imap_unordered(_scene_job, todo, chunksize=1)):
                times.append(dt)
                if (i + 1) % 25 == 0 or i + 1 == len(todo):
                    print("scenes %d/%d  %.0f s" % (i + 1, len(todo), time.time() - t0), flush=True)
    # merge the shards in (scene, arm, delay) order: v01's layout
    arm_rank = {x: i for i, x in enumerate(a.arms)}
    eps = []
    parts = {}
    shard_times = []
    for scene in scene_names:
        z = np.load(_shard_path(shard_dir, scene))
        m = json.loads(str(z["meta"]))
        assert m["scene"] == scene and m["sim_sha256"] == hashes["sim_sha256"] and m["runner_sha256"] == hashes["runner_sha256"], \
            "shard of %s made by other code" % scene
        shard_times.append(float(m["seconds"]))
        eps_l = json.loads(str(z["episodes"]))
        order = sorted(range(len(eps_l)), key=lambda i: (arm_rank[eps_l[i]["arm"]], eps_l[i]["delay_kf"]))
        remap = np.zeros(len(eps_l), np.int64)
        for i in order:
            o = eps_l[i]
            o.pop("_local", None)
            o["episode"] = len(eps)
            o["stamp"] = pre
            remap[i] = len(eps)
            eps.append(o)
        for pre_, fields in (("dec_", ["episode"] + list(S.DEC_FIELDS) + ["stats", "trk"]), ("cnt_", ["episode", "cell", "n", "exceed"]),
                             ("cal_", ["episode", "key", "values"])):
            ep_new = remap[z[pre_ + "episode"]] if len(z[pre_ + "episode"]) else np.zeros(0, np.int64)
            perm = np.argsort(ep_new, kind="stable")
            for f_ in fields:
                v = ep_new if f_ == "episode" else z[pre_ + f_]
                parts.setdefault(pre_ + f_, []).append(v[perm])
    cat = lambda k, dt: np.concatenate(parts[k]).astype(dt) if parts.get(k) else np.zeros(0, dt)  # noqa: E731
    ep_path, ct_path = os.path.join(a.out, "episodes_%s.jsonl" % a.tag), os.path.join(a.out, "counts_%s.npz" % a.tag)
    with open(ep_path, "w") as f:
        for o in eps:
            f.write(json.dumps(o) + "\n")
    np.savez_compressed(ct_path, episode=cat("cnt_episode", np.int32), cell=cat("cnt_cell", np.int32),
                        n=cat("cnt_n", np.int32), exceed=cat("cnt_exceed", np.int32), stamp=np.array(pre))
    dc_path = os.path.join(a.out, "decisions_%s.npz" % a.tag)
    darr = {"episode": cat("dec_episode", np.int32)}
    for f_ in S.DEC_FIELDS:
        darr[f_] = cat("dec_" + f_, np.int32 if f_ in S.DEC_INT else float)
    darr["ob"] = darr["ob"].astype(np.int8)
    darr["infeasible"] = darr["infeasible"].astype(np.int8)
    darr["stats"] = np.concatenate(parts["dec_stats"]).astype(np.float32).reshape(-1, S.N_ST) if parts.get("dec_stats") else np.zeros((0, S.N_ST), np.float32)
    darr["trk"] = np.concatenate(parts["dec_trk"]).astype(np.float32).reshape(-1, S.N_TRK) if parts.get("dec_trk") else np.zeros((0, S.N_TRK), np.float32)
    np.savez_compressed(dc_path, st_fields=np.array(S.ST_FIELDS), trk_fields=np.array(S.TRK_FIELDS), stamp=np.array(pre), **darr)
    cl_path = os.path.join(a.out, "cal_%s.npz" % a.tag)
    np.savez_compressed(cl_path, episode=cat("cal_episode", np.int32), key=cat("cal_key", np.int32),
                        values=(np.concatenate(parts["cal_values"]) if parts.get("cal_values") else np.zeros((0, S.N_CAL))).reshape(-1, S.N_CAL),
                        fields=np.array(S.CAL_FIELDS), stamp=np.array(pre))
    hashes_end = code_hashes(a.fits, a.caches)
    assert hashes_end == hashes, "code, fits or manifests changed during the run"
    rec = {"tag": a.tag, "mode": a.mode, "prereg": pre, "exploratory": exploratory, "dry_run": False, "stamp": pre, "arms": a.arms,
           "delays_kf": a.delays_kf, "scenes": len(scene_names), "episodes": len(eps),
           "fits": a.fits, "fits_sha256": hashes["fits_sha256"], "sim_sha256": hashes["sim_sha256"],
           "runner_sha256": hashes["runner_sha256"], "manifest_sha256": hashes["manifest_sha256"], "hashes": hashes,
           "launch_record": os.path.abspath(lr_path), "launch_record_sha256": sha256_path(lr_path), "hashes_equal_at_end": True,
           "caches": [os.path.abspath(c) for c in a.caches], "episodes_sha256": sha256_path(ep_path), "counts_sha256": sha256_path(ct_path),
           "decisions_sha256": sha256_path(dc_path), "decisions": int(len(darr["k"])), "cal_sha256": sha256_path(cl_path),
           "scene_names": scene_names, "shards_reused": len(reused), "numpy": np.__version__, "seconds": round(time.time() - t0, 1),
           "scene_seconds_median": float(np.median(shard_times)) if shard_times else None,
           "scene_seconds_sum": float(np.sum(shard_times)) if shard_times else None}
    json.dump(rec, open(os.path.join(a.out, "run_record_%s.json" % a.tag), "w"), indent=1)
    print(json.dumps({k: v for k, v in rec.items() if k != "scene_names"}))
    print("K8 RUN DONE")


if __name__ == "__main__":
    main()
'''
s = s[:s.index(TAIL_START)]
rep = [(HEAD_OLD, HEAD_NEW), (IMP_OLD, IMP_NEW), (DEV_OLD, DEV_NEW)]
for a, b in rep:
    assert s.count(a) == 1, "anchor not found exactly once: " + a[:80]
    s = s.replace(a, b, 1)
s = s + TAIL_NEW
open(os.path.join(K8, "k8_run_v02.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k8_run_v02.py written")
