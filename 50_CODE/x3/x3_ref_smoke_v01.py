#!/usr/bin/env python3
"""x3_ref_smoke_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Interface smoke tests of x3-ref's artifacts on ONE log per tracker (light; no outcome is summarised):
  (d)  the d0 fits JSON (d_ref/fits_x3ref_d0_<t>.json), read exactly as c1_run_v02._scene_job reads fits (fold_of_scene, then
       fits[str(fold)][step] for the 8 steps), drives k8_sim_v04.run_decisions(sc, "Mstar", fits) to the decisions of record of arm
       Mstar on that log (infeasible, lam, ds_plan, v_chosen, stats) -- the d1 / d2 files have the same layout;
  (e2) the substitution mechanism: replacing sc.tr["pred"][:, :, 2:5] by the cache's own covariance (q = 1 everywhere) reproduces
       arm B0's decisions of record on that log, and the substitution file (e2_qrefit/subst_<t>/<log>.npz) loads, aligns (tr_k) and
       runs arm B0 (decision count only).
Usage: python -B x3_ref_smoke_v01.py --trk t1 t3 [--scene <log>]
"""
import argparse
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402
sys.path.insert(0, os.path.join(C.W, "50_CODE", "k8"))
import k8_sim_v04 as S8  # noqa: E402

STEPS = ["h0p5s", "h1s", "h1p5s", "h2s", "h2p5s", "h3s", "h3p5s", "h4s"]
FIELDS = ("infeasible", "lam", "ds_plan", "v_chosen")


def record_decisions(trk, arm, scene):
    runs = os.path.join(C.W, "60_RESULTS", "c1_av2_v01", "runs")
    ep = None
    for ln in open(os.path.join(runs, "episodes_%s_within_lt3d_decide.jsonl" % trk), encoding="utf-8"):
        r = json.loads(ln)
        if r["arm"] == arm and r["scene"] == scene:
            ep = int(r["episode"])
            break
    z = np.load(os.path.join(runs, "decisions_%s_within_lt3d_decide.npz" % trk))
    m = z["episode"] == ep
    return {f: z[f][m] for f in FIELDS + ("k", "stats")}


def compare(o, rec):
    d = o["decisions"]
    res = {}
    for f in FIELDS + ("k",):
        a = np.asarray(d[f], float)
        b = rec[f].astype(float)
        res[f] = bool(a.shape == b.shape and np.array_equal(a, b))
    st = np.asarray(d["stats"], np.float32).reshape(-1, S8.N_ST)
    res["stats"] = bool(st.shape == rec["stats"].shape and np.array_equal(st, rec["stats"]))
    return res, all(res.values())


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", nargs="+", required=True, choices=("t1", "t3"))
    ap.add_argument("--scene", default="02a00399-3857-444e-8db3-a8f58489c394")
    a = ap.parse_args(argv)
    C.run_log_ok()
    out = {"stamp": C.STAMP, "scene": a.scene, "trackers": {}}
    for trk in a.trk:
        path = os.path.join(C.CACHE[trk], a.scene + ".npz")
        fa = json.load(open(os.path.join(C.D_REF, "fits_x3ref_d0_%s.json" % trk)))
        fold = fa["fold_of_scene"][a.scene]
        fits = [fa["fits"][str(fold)][h] for h in STEPS]
        sc = S8.Scene(path)
        o, _ = S8.run_decisions(sc, "Mstar", fits)
        r_m, ok_m = compare(o, record_decisions(trk, "Mstar", a.scene))
        sc = S8.Scene(path)
        cov = sc.tr["pred"][:, :, 2:5].copy()
        sc.tr["pred"] = sc.tr["pred"].copy()
        sc.tr["pred"][:, :, 2:5] = cov
        o, _ = S8.run_decisions(sc, "B0", None)
        r_b, ok_b = compare(o, record_decisions(trk, "B0", a.scene))
        res = {"fold": fold, "d0_fits_Mstar_equals_record": ok_m, "d0_fields": r_m, "q1_substitution_B0_equals_record": ok_b, "b0_fields": r_b}
        sp = os.path.join(C.E2, "subst_%s" % trk, a.scene + ".npz")
        if os.path.exists(sp):
            zs = np.load(sp)
            sc = S8.Scene(path)
            assert np.array_equal(sc.tr["k"], zs["tr_k"]), "substitution rows misaligned"
            sc.tr["pred"] = sc.tr["pred"].copy()
            sc.tr["pred"][:, :, 2:5] = zs["pred_cov"]
            o, _ = S8.run_decisions(sc, "B0", None)
            res["subst_file_runs"] = {"rows": int(len(zs["tr_k"])), "decisions": int(o["frames"]),
                                      "q_values": sorted(set(float(x) for x in zs["q_row"]))}
        out["trackers"][trk] = res
        print(trk, json.dumps(res))
    C.save_json(os.path.join(C.E2, "SMOKE_runner_interface_%s.json" % "_".join(a.trk)), out)
    C.run_log_ok()


if __name__ == "__main__":
    main()
