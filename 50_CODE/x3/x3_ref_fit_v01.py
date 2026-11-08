#!/usr/bin/env python3
"""x3_ref_fit_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md section 2 (d).

Refits M* per fold on a reference's items by the frozen fit rule: exactly the M* part of c1_fit_v02.fit_arms (route within), i.e.
for every held-out fold f and calibrated step h (0.5 ... 2 s), on the items of the other folds' units with item_h == h:
  'Mstar_ip', 'Mstar_ip_src' = c1_crc_exact_v01.split_fit_exact(U, s, levels, inpath, 0)   (192 = L0 + 96 x in-path; DP-SCRC per L0
                                                                                            with >= 19 units, else L1, L2, L3)
  'Mstar'                    = c1_crc_exact_v01.fit_hier_exact(U, s, levels, 0)              (pooled 96, as of record)
with U = D / sd, levels = m_lib_v04.levels(items, items.m), the items loaded by k8_joint_fit_v02.load_items, and the 2.5 ... 4 s step
dicts copied from the 2 s dict with '_copied_from' (as of record). Only the M* keys are written (no comparator is refitted here).
c1_fit_v02.fit_arms asserts every M* threshold > 0 (a requirement of the joint arms, which X3 (d) does not run); here a threshold
<= 0 is recorded and flagged instead of stopping the fit.
Imports (read-only; no guard is called: c1_fit_v02 is not imported, c1_crc_exact_v01 / k8_joint_fit_v02 / m_lib_v04 have no guard).
Modes:
  --validate --trk t     fit the items of record and compare Mstar_ip, Mstar_ip_src, Mstar and _copied_from with fits_within of record
  --ref d0|d1|d2 --trk t fit d_ref/items_x3ref_<ref>_<t>.npz -> d_ref/fits_x3ref_<ref>_<t>.json (fits[fold][step][key], fold_of_scene,
                         folds_sha256), plus the threshold comparison against the record
Usage: python -B x3_ref_fit_v01.py (--validate | --ref d0|d1|d2) --trk t1|t3
"""
import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402
sys.path.insert(0, os.path.join(C.W, "50_CODE", "c1_av2"))
sys.path.insert(0, os.path.join(C.W, "50_CODE", "k8"))
import c1_crc_exact_v01 as X  # noqa: E402
import k8_joint_fit_v02 as J  # noqa: E402

M = X.M
STEPS = J.STEPS
CC = J.CC_STEPS
N_L0 = M.N_L0
POPS = J.POPS


def fit_mstar(items_path, folds_path):
    fj = json.load(open(folds_path))
    fold_of = {u: int(f) for u, f in fj["fold_of_log"].items()}
    k = int(fj["k"])
    it, names, info = J.load_items([items_path])
    assert set(names) == set(fold_of), "the items' units differ from the folds' units"
    fold_unit = np.array([fold_of.get(n, -1) for n in names], int)
    lv = M.levels(it, it["m"])
    assert np.array_equal(lv[0], it["l0"]), "L0 from the items differs from the simulator's L0"
    assert np.all(np.isfinite(it["D"])) and np.all(np.isfinite(it["sd"])) and np.all(it["sd"] > 0), "NaN or non-positive sd in the items"
    U = it["D"] / it["sd"]
    ip = it["inpath"].astype(int)
    fits, flags = {}, []
    for f in range(k):
        cal = (fold_unit != f) & (fold_unit >= 0)
        fd = {}
        for h in range(CC):
            sel = (it["h"] == h) & cal[it["s"]]
            Us, ss, lvs, ips = U[sel], it["s"][sel], [x[sel] for x in lv], ip[sel]
            mip, mip_src = X.split_fit_exact(Us, ss, lvs, ips, 0)
            mpool, _ = X.fit_hier_exact(Us, ss, lvs, 0)
            for arr, nm in ((mip, "Mstar_ip"), (mpool, "Mstar")):
                assert np.all(np.isfinite(arr)), "non-finite threshold: " + nm
            if not np.all(mip > 0):
                flags.append({"fold": f, "step": STEPS[h], "n_le_0": int((mip <= 0).sum()), "min": float(mip.min())})
            fd[STEPS[h]] = {"Mstar": mpool.tolist(), "Mstar_ip": mip.tolist(), "Mstar_ip_src": mip_src.astype(int).tolist()}
        for h in range(CC, len(STEPS)):
            fd[STEPS[h]] = dict(fd[STEPS[CC - 1]], _copied_from=STEPS[CC - 1])
        fits[str(f)] = fd
        print("fold %d fitted" % f, flush=True)
    return {"fits": fits, "fold_of_scene": fold_of, "scenes": sorted(fold_of), "k": k, "seed": fj.get("seed"),
            "fold_scene_counts": [int((fold_unit == f).sum()) for f in range(k)], "items": info, "nonpositive_flags": flags}, it, names


def compare_fits(mine, rec):
    res, ok = {}, True
    for f in sorted(rec["fits"]):
        for st in STEPS:
            for key in ("Mstar_ip", "Mstar_ip_src", "Mstar", "_copied_from"):
                a, b = mine["fits"][f][st].get(key), rec["fits"][f][st].get(key)
                same = a == b
                ok &= same
                if not same:
                    res["%s/%s/%s" % (f, st, key)] = "DIFFERENT"
    ok &= mine["fold_of_scene"] == rec["fold_of_scene"]
    return ok, res


def threshold_change(mine, rec, it_rec, names_rec):
    """Ratio of the reference's M* thresholds to the record's, per step: (i) over the 96 thresholds of each in-path part and the 5
    folds (thresholds > 0 in the record), (ii) weighted by the record's relied items of each screen population (k8_joint_fit_v02
    POPS), each item at its own fold, L0 stratum and in-path part."""
    out = {"per_part": {}, "per_population_item_weighted": {}}
    fold_of = rec["fold_of_scene"]
    fs = np.array([int(fold_of[n]) for n in names_rec])[it_rec["s"]]
    for h in range(CC):
        st = STEPS[h]
        A = np.array([mine["fits"][str(f)][st]["Mstar_ip"] for f in range(5)])     # (5, 192)
        B = np.array([rec["fits"][str(f)][st]["Mstar_ip"] for f in range(5)])
        for part, sl in (("not_inpath", slice(0, N_L0)), ("inpath", slice(N_L0, 2 * N_L0))):
            a, b = A[:, sl].ravel(), B[:, sl].ravel()
            ok = b > 0
            r = a[ok] / b[ok]
            out["per_part"]["%s/%s" % (st, part)] = {"median_ratio": float(np.median(r)), "q10": float(np.quantile(r, 0.1)),
                                                    "q90": float(np.quantile(r, 0.9)), "share_changed": float(np.mean(a != b)),
                                                    "n": int(len(r)), "n_record_le_0": int((~ok).sum())}
        sel_h = it_rec["h"] == h
        idx = it_rec["l0"] + N_L0 * it_rec["inpath"].astype(int)
        ra = A[fs, idx]
        rb = B[fs, idx]
        for p in POPS:
            m = J.pop_mask(it_rec, p) & sel_h & (rb > 0)
            r = ra[m] / rb[m]
            out["per_population_item_weighted"]["%s/%s" % (st, p)] = {"median_ratio": float(np.median(r)) if len(r) else None,
                                                                     "q10": float(np.quantile(r, 0.1)) if len(r) else None,
                                                                     "q90": float(np.quantile(r, 0.9)) if len(r) else None,
                                                                     "items": int(m.sum())}
    src = {}
    for name, F in (("reference", mine), ("record", rec)):
        s = np.array([F["fits"][str(f)][STEPS[h]]["Mstar_ip_src"] for f in range(5) for h in range(CC)]).ravel()
        src[name] = {"L%d" % lvl: float(np.mean(s == lvl)) for lvl in range(4)}
    out["fallback_level_shares"] = src
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", required=True, choices=("t1", "t3"))
    ap.add_argument("--ref", choices=("d0", "d1", "d2"))
    ap.add_argument("--validate", action="store_true")
    a = ap.parse_args(argv)
    assert a.validate != bool(a.ref), "exactly one of --validate, --ref"
    C.run_log_ok()
    t0 = time.time()
    rec = json.load(open(C.FITS_REC[a.trk]))
    assert rec["folds_sha256"] == C.sha256_path(C.FOLDS), "the fits of record were made for other folds"
    from x3_heavylock_v01 import heavy_lock
    code = C.code_record([os.path.abspath(__file__), C.__file__, X.__file__, J.__file__, M.__file__])
    if a.validate:
        vp = os.path.join(C.D_REF, "VALIDATION_fit_record_%s.json" % a.trk)
        C.check_out(vp)
        C.live("fit validate %s" % a.trk, 0, 5)
        with heavy_lock("x3-ref: M* fit validation %s" % a.trk):
            mine, _, _ = fit_mstar(C.ITEMS_REC[a.trk], C.FOLDS)
        ok, res = compare_fits(mine, rec)
        val = {"stamp": C.STAMP, "check": "x3_ref_fit_v01 on the items of record vs fits_within of record: Mstar_ip, Mstar_ip_src, Mstar and "
               "_copied_from for every fold and all 8 steps (Python list equality of the JSON values), and fold_of_scene",
               "tracker": a.trk, "items": C.ITEMS_REC[a.trk], "items_sha256": C.sha256_path(C.ITEMS_REC[a.trk]), "fits_record": C.FITS_REC[a.trk],
               "fits_record_sha256": C.sha256_path(C.FITS_REC[a.trk]), "differences": res, "nonpositive_flags": mine["nonpositive_flags"],
               "pass": bool(ok), "code_sha256": code, "seconds": round(time.time() - t0, 1)}
        C.save_json(vp, val)
        C.run_log_ok()
        print("FIT VALIDATION", "PASS" if ok else "FAIL", json.dumps(res)[:500])
        if not ok:
            raise SystemExit("fit validation FAILED")
        print("X3 REF FIT DONE")
        return
    vp = os.path.join(C.D_REF, "VALIDATION_fit_record_%s.json" % a.trk)
    assert os.path.exists(vp) and json.load(open(vp))["pass"], "the fit rule has not reproduced the record: no reference fit"
    items = os.path.join(C.D_REF, "items_x3ref_%s_%s.npz" % (a.ref, a.trk))
    isum = json.load(open(items.replace(".npz", "_summary.json")))
    assert isum["out_sha256"] == C.sha256_path(items), "items differ from their summary"
    out_p = os.path.join(C.D_REF, "fits_x3ref_%s_%s.json" % (a.ref, a.trk))
    C.check_out(out_p)
    assert not os.path.exists(out_p), "exists: " + out_p
    C.live("fit %s %s" % (a.ref, a.trk), 0, 5)
    with heavy_lock("x3-ref: M* fit %s %s" % (a.ref, a.trk)):
        mine, it_ref, names = fit_mstar(items, C.FOLDS)
    it_rec, names_rec, _ = J.load_items([C.ITEMS_REC[a.trk]])
    assert list(names_rec) == list(names), "scene order differs from the record's"
    res = {"stamp": C.STAMP, "c1": False, "x3": "(d) M* refitted at reference %s: %s" % (a.ref, isum["reference_text"]),
           "route": "within", "folds": C.FOLDS, "folds_sha256": C.sha256_path(C.FOLDS), "k": mine["k"], "seed": mine["seed"],
           "items": mine["items"], "exact_crc": "c1_crc_exact_v01 (E15)", "fits": mine["fits"], "scenes": mine["scenes"],
           "fold_of_scene": mine["fold_of_scene"], "fold_scene_counts": mine["fold_scene_counts"],
           "keys_written": ["Mstar_ip", "Mstar_ip_src", "Mstar", "_copied_from (2.5 ... 4 s)"],
           "nonpositive_flags": mine["nonpositive_flags"], "code_sha256": code,
           "fit_rule": "c1_fit_v02.fit_arms' M* part (split_fit_exact / fit_hier_exact on U = D / sd of the other folds' items, per step)"}
    if a.ref == "d0":
        ok, diff = compare_fits(mine, rec)
        res["equals_record_mstar_keys"] = bool(ok)
        assert ok, "d0 fits differ from the record: %s" % list(diff)[:5]
    C.save_json(out_p, res)
    rel = it_ref["ref_relied"]
    rep = {"stamp": C.STAMP, "reference": a.ref, "reference_text": isum["reference_text"], "tracker": a.trk, "fits": out_p,
           "fits_sha256": C.sha256_path(out_p), "items": items, "items_sha256": isum["out_sha256"],
           "item_counts": {"items": int(len(it_ref["D"])), "records": isum["records"], "relied_items": int(rel.sum()),
                           "relied_share": float(rel.mean()), "inpath_share": float(it_ref["inpath"].mean()),
                           "relied_inpath_share": float(it_ref["inpath"][rel].mean()),
                           "relied_near_share": float((it_ref["gap"][rel] <= J.GAP_NEAR).mean()), "totals": isum["totals"],
                           "per_population": {p: int(J.pop_mask(it_ref, p).sum()) for p in POPS}},
           "record_item_counts": {"items": int(len(it_rec["D"])), "relied_items": int(it_rec["ref_relied"].sum()),
                                  "relied_share": float(it_rec["ref_relied"].mean()), "inpath_share": float(it_rec["inpath"].mean()),
                                  "per_population": {p: int(J.pop_mask(it_rec, p).sum()) for p in POPS}},
           "threshold_change_vs_record": threshold_change(mine, rec, it_rec, names_rec),
           "nonpositive_flags": mine["nonpositive_flags"], "seconds": round(time.time() - t0, 1)}
    C.save_json(os.path.join(C.D_REF, "fit_report_x3ref_%s_%s.json" % (a.ref, a.trk)), rep)
    C.run_log_ok()
    print(json.dumps({"out": out_p, "sha256": rep["fits_sha256"], "counts": rep["item_counts"]}))
    print("X3 REF FIT DONE")


if __name__ == "__main__":
    main()
