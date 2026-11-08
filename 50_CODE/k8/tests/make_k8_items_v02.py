#!/usr/bin/env python3
"""Writes 50_CODE/k8/k8_items_v02.py from 50_CODE/k7/k7_items_v02.py (Claude line, 1 Nov 2026; D14 v04 A6, A14; R15 M4, M5, m7).
Every change is a text replacement asserted to match exactly once (test T5). The item and record enumeration is K7's, unchanged
(test T15: every K7 item and record field is reproduced exactly); each record (one per enforced pair with a ground-truth
annotation) additionally carries what the arm-independent calibration diagnostics need (R15 M4: "the items must carry yaw,
the per-axis L0 and the in-path flag"): the object yaw, the ground-truth instance and the track row (A14 duplicates), the
motion state, the L0 stratum and sd of both object axes, the relied-on axis at the reference pose (argmax of the gap), the gaps
and the signed errors D along both axes, and the pair id that links it to its items. Run modes as k8_run_v02: --dev (the 10
development scenes only), --exploratory (every non-development scene; the hashes logged before launch; stamped EXPLORATORY),
--dry-run (prints the scene list and hashes; reads and computes nothing)."""
import os

K8 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
s = open(os.path.join(os.path.dirname(K8), "k7", "k7_items_v02.py"), encoding="utf-8").read()

HEAD_OLD = '"""K7 calibration items (Claude line, v02, 1 Nov 2026): planner-matched calibration population.\n'
HEAD_NEW = ('"""K8 calibration items (Claude line, k8_items_v02, 1 Nov 2026) = k7_items_v02 plus per-record fields for the arm-independent\n'
            'calibration diagnostics (90_DECISIONS/D14_K8_DESIGN_v04.md A6, A14; written by tests/make_k8_items_v02.py). Each record also\n'
            'carries yaw (object heading), inst (ground-truth instance), row (track row in the cache), m (motion state), l0_long / l0_lat\n'
            'and sd_long / sd_lat (both object axes), rel (the relied-on axis at the reference pose: argmax of the gap), gap_long / gap_lat\n'
            'and D_long / D_lat (signed error along each axis, sign(sep) a.(g - m)), and pair (the id its items carry). The enumeration\n'
            'is unchanged. Run modes: --dev (the 10 development scenes only), --exploratory (every non-development scene, hashes logged\n'
            'before launch, stamped EXPLORATORY), --dry-run (prints the scene list and the hashes; nothing is read or computed).\n'
            'Usage: python -B k8_items_v02.py --caches <train> <val> --out <npz> (--dev | --exploratory) [--workers n] [--dry-run]\n'
            'K7 calibration items (Claude line, v02, 1 Nov 2026): planner-matched calibration population.\n')
REC_OLD = 'REC = ("s", "k", "h", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "inpath")\n'
REC_NEW = ('REC = ("s", "k", "h", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "inpath",\n'
           '       "yaw", "inst", "row", "m", "l0_long", "l0_lat", "sd_long", "sd_lat", "rel", "gap_long", "gap_lat", "D_long", "D_lat", "pair")\n'
           'REC_INT = ("inst", "row", "m", "l0_long", "l0_lat", "rel", "pair")\n'
           'DEV_SCENES = ("scene-0061", "scene-0103", "scene-0553", "scene-0655", "scene-0757", "scene-0796", "scene-0916", "scene-1077",\n'
           '              "scene-1094", "scene-1100")\n'
           'N_NONDEV = 840\n'
           'EXPLORATORY_STAMP = "EXPLORATORY: nuScenes development evidence, not a confirmation"\n'
           'DEV_STAMP = "DEV MODE (nuScenes-mini scenes only; excluded from K8)"\n')
APP_OLD = ('                for key, val in (("s", si), ("k", k), ("h", h), ("g", g[j]), ("r", r[j, h]), ("dx", e0), ("dy", e1), ("sxx", pred[j, h, 2]),\n'
           '                                 ("sxy", pred[j, h, 3]), ("syy", pred[j, h, 4]), ("inpath", bool(inp[j]))):\n'
           '                    rc[key].append(val)\n')
APP_NEW = ('                for key, val in (("s", si), ("k", k), ("h", h), ("g", g[j]), ("r", r[j, h]), ("dx", e0), ("dy", e1), ("sxx", pred[j, h, 2]),\n'
           '                                 ("sxy", pred[j, h, 3]), ("syy", pred[j, h, 4]), ("inpath", bool(inp[j])),\n'
           '                                 ("yaw", float(tr["yaw"][sel[j]])), ("inst", int(inst[j])), ("row", int(sel[j])), ("m", int(m[j])),\n'
           '                                 ("l0_long", int(l0[j, h, 0])), ("l0_lat", int(l0[j, h, 1])), ("sd_long", float(sd[j, h, 0])),\n'
           '                                 ("sd_lat", float(sd[j, h, 1])), ("rel", int(np.argmax(G[h, j]))), ("gap_long", float(G[h, j, 0])),\n'
           '                                 ("gap_lat", float(G[h, j, 1])),\n'
           '                                 ("D_long", float(np.sign(SP[h, j, 0]) * (ax[j, 0, 0] * e0 + ax[j, 0, 1] * e1))),\n'
           '                                 ("D_lat", float(np.sign(SP[h, j, 1]) * (ax[j, 1, 0] * e0 + ax[j, 1, 1] * e1))),\n'
           '                                 ("pair", st["pairs_with_gt"])):\n'
           '                    rc[key].append(val)\n')
MAIN_START = 'def main():\n'
MAIN_NEW = r'''def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--caches", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--dev", action="store_true", help="the 10 development scenes only")
    ap.add_argument("--exploratory", action="store_true", help="every non-development scene (D14 v04 section 5.1)")
    ap.add_argument("--dry-run", action="store_true", help="print the scene list and the hashes; read and compute nothing")
    a = ap.parse_args()
    assert int(a.dev) + int(a.exploratory) == 1, "exactly one of --dev, --exploratory"
    t0 = time.time()
    jobs, names, logs, man_sha, want = [], [], {}, [], []
    for cdir in a.caches:
        mp = os.path.join(cdir, "MANIFEST.json")
        man = json.load(open(mp))
        man_sha.append(sha256_path(mp))
        for scene, info in sorted(man["scenes"].items()):
            if a.dev and scene not in DEV_SCENES:
                continue
            if a.exploratory and scene in DEV_SCENES:
                continue
            want.append((os.path.join(cdir, scene + ".npz"), scene, info))
    if a.dev:
        assert len(want) == len(DEV_SCENES) and all(w[1] in DEV_SCENES for w in want), "development scenes missing or a non-development scene"
        stamp = DEV_STAMP
    else:
        assert not any(w[1] in DEV_SCENES for w in want), "a development scene in the exploratory items"
        assert len(want) == N_NONDEV, "the exploratory items need every non-development scene: %d found" % len(want)
        stamp = EXPLORATORY_STAMP
    hashes = {"items_script_sha256": sha256_path(os.path.abspath(__file__)), "k6_sim_v02_sha256": sha256_path(S.__file__),
              "manifest_sha256": man_sha}
    launch = {"out": os.path.abspath(a.out), "stamp": stamp, "exploratory": bool(a.exploratory), "dry_run": bool(a.dry_run),
              "scenes": len(want), "scene_names": sorted(w[1] for w in want), "caches": [os.path.abspath(c) for c in a.caches],
              "hashes": hashes, "launched": time.strftime("%Y-%m-%d %H:%M:%S")}
    lr = a.out.replace(".npz", "_launch%s.json" % ("_DRYRUN" if a.dry_run else ""))
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    json.dump(launch, open(lr, "w"), indent=1)
    if a.dry_run:
        print("DRY RUN (%s): %d scenes" % (stamp, len(want)))
        print("scenes: " + " ".join(sorted(w[1] for w in want)))
        print("hashes: " + json.dumps(hashes, indent=1))
        print("DRY RUN: no scene cache was read and no item was computed; launch record " + lr)
        return
    for p, scene, info in want:
        assert sha256_path(p) == info["sha256"], "cache file differs from its manifest: " + p
        jobs.append((p, len(names)))
        names.append(scene)
        logs[scene] = info["log"]
    assert len(set(names)) == len(names), "a scene appears twice"
    its = {k: [] for k in ITEM}
    rcs = {k: [] for k in REC}
    stats = {}
    done = {}
    with Pool(a.workers) as pool:
        for i, (si, it, rc, st) in enumerate(pool.imap_unordered(scene_items, jobs, chunksize=1)):
            done[si] = (it, rc)
            stats[names[si]] = st
            if (i + 1) % 50 == 0 or i + 1 == len(jobs):
                print("scenes %d/%d  %.0f s" % (i + 1, len(jobs), time.time() - t0), flush=True)
    for si in sorted(done):                      # deterministic order: the scene index (v02; K7 used the completion order)
        it, rc = done[si]
        for k in ITEM:
            its[k].append(np.asarray(it[k]))
        for k in REC:
            rcs[k].append(np.asarray(rc[k]))
    out = {}
    for k in ITEM:
        out["item_" + k] = np.concatenate([x for x in its[k] if len(x)] or [np.zeros(0)])
    for k in REC:
        out["rec_" + k] = np.concatenate([x for x in rcs[k] if len(x)] or [np.zeros(0)])
    for k in ("s", "k", "h", "g", "r", "a", "m", "l0", "pair"):
        out["item_" + k] = out["item_" + k].astype(np.int32)
    out["item_ref_relied"] = out["item_ref_relied"].astype(bool)
    for k in ("s", "k", "h", "g", "r") + REC_INT:
        out["rec_" + k] = out["rec_" + k].astype(np.int32)
    out["item_inpath"] = out["item_inpath"].astype(bool)
    out["rec_inpath"] = out["rec_inpath"].astype(bool)
    out["scene_names"] = np.array(names)
    out["scene_logs"] = np.array([logs[s] for s in names])
    out["stamp"] = np.array(stamp)
    np.savez_compressed(a.out, **out)
    summ = {"stamp": stamp, "exploratory": bool(a.exploratory), "caches": [os.path.abspath(c) for c in a.caches], "manifest_sha256": man_sha,
            "scenes": len(names), "scene_names": sorted(names),
            "items": int(len(out["item_D"])), "records": int(len(out["rec_dx"])),
            "items_inpath_share": float(out["item_inpath"].mean()) if len(out["item_D"]) else None,
            "items_ref_relied": int(out["item_ref_relied"].sum()),
            "totals": {k: int(sum(st[k] for st in stats.values())) for k in ("decisions", "pairs_considered", "pairs_enforced", "pairs_with_gt")},
            "sim_sha256": sha256_path(S.__file__), "items_script_sha256": sha256_path(os.path.abspath(__file__)), "hashes": hashes,
            "launch_record": os.path.abspath(lr), "out_sha256": sha256_path(a.out), "seconds": round(time.time() - t0, 1)}
    assert hashes == {"items_script_sha256": summ["items_script_sha256"], "k6_sim_v02_sha256": summ["sim_sha256"],
                      "manifest_sha256": [sha256_path(os.path.join(c, "MANIFEST.json")) for c in a.caches]}, "code changed during the run"
    json.dump(summ, open(a.out.replace(".npz", "_summary.json"), "w"), indent=1)
    print(json.dumps({k: v for k, v in summ.items() if k != "scene_names"}))
    print("K8 ITEMS V02 DONE")


if __name__ == "__main__":
    main()
'''
for a, b in [(HEAD_OLD, HEAD_NEW), (REC_OLD, REC_NEW), (APP_OLD, APP_NEW)]:
    assert s.count(a) == 1, "anchor not found exactly once: " + a[:80]
    s = s.replace(a, b, 1)
assert s.count(MAIN_START) == 1
s = s[:s.index(MAIN_START)] + MAIN_NEW
open(os.path.join(K8, "k8_items_v02.py"), "w", encoding="utf-8", newline="\n").write(s)
print("k8_items_v02.py written")
