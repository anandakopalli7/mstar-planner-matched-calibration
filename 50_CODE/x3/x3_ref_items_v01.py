#!/usr/bin/env python3
"""x3_ref_items_v01 (x3-ref agent, 7 Nov 2026). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the
registered test). Plan 20_DESIGN/X3_POSTREG_EXPLORATORY_PLAN_v01.md section 2 (d) (referee concern M5).

Rebuilds the K8 calibration items of record (50_CODE/k8/k8_items_v08.py, scene_items) with the frozen enumeration, changing ONLY the
reference ego progression `lead` (the 16-vector of reference arc lengths at t_k + EVAL_T, 0.25 ... 4 s). In k8_items_v08 that
one variable plays both of its roles: (i) the leash of the candidate plans in the enforced-pair rule at margin 0
(splan = min(plan_positions, lead), hence ctrl and the enforced set) and (ii) the reference ego pose at which the gap G, the
signed separation SP (side of separation, the sign of D) and the relied-on axis (argmax G) are taken. Both roles change together.
  d0  the logged arc length, as of record: lead = s_log(t_k + EVAL_T).                     [validation: must equal the record bitwise]
  d1  the decision-mode planner's own reference plan: the arc lengths of the candidate that k8_sim_v04.plan_step chooses for arm Z0
      (margin 0) at keyframe k with the record's decision-mode settings (s = s_log(t_k), v = max(v_log(t_k), 0), vmax = v_log_max + 2,
      leash = s_log, sensor offset 0), leashed exactly as plan_step leashes it: min(plan_positions(s, v, vmax)[choice], s_log(t_k + EVAL_T)).
  d2  constant current speed along the logged path: lead = min(s_k + v_k EVAL_T, s_end), s_k = s_log(t_k), v_k = max(v_log(t_k), 0)
      (the decision state's s and v of the items code).
Everything else is k8_items_v08's (strata, D = sign(sep) a.(g - m), sd = sqrt(a' S_h a + 0.10^2), ground-truth censoring, the
hold-at-current-position test, the output layout). scene_items_x3 below is a textual copy of k8_items_v08.scene_items with three
line changes (name, job tuple, the lead line); the summary records the unified diff against the file of record.
No guard is imported or called: k8_items_v08 itself is NOT imported (it imports c1_guard_v05); k6_sim_v02 and k8_sim_v04 are imported
read-only (pure numpy, no import-time side effects).
Usage: python -B x3_ref_items_v01.py --trk t1|t3 --ref d0|d1|d2 [--workers 2]
"""
import argparse
import difflib
import inspect
import json
import math
import os
import re
import sys
import time
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import x3_ref_common_v01 as C  # noqa: E402
sys.path.insert(0, os.path.join(C.W, "50_CODE", "k6"))
sys.path.insert(0, os.path.join(C.W, "50_CODE", "k8"))
import k6_sim_v02 as S  # noqa: E402
import k8_sim_v04 as S8  # noqa: E402

ITEM = ("s", "k", "h", "g", "r", "a", "m", "inpath", "sd", "D", "l0", "gap", "pair", "ref_relied")
REC = ("s", "k", "h", "g", "r", "dx", "dy", "sxx", "sxy", "syy", "inpath",
       "yaw", "inst", "row", "m", "l0_long", "l0_lat", "sd_long", "sd_lat", "rel", "gap_long", "gap_lat", "D_long", "D_lat", "pair")
REC_INT = ("inst", "row", "m", "l0_long", "l0_lat", "rel", "pair")
ITEMS_SRC = os.path.join(C.W, "50_CODE", "k8", "k8_items_v08.py")
REFS = ("d0", "d1", "d2")
REF_TEXT = {"d0": "logged arc length s_log(t_k + t) (as of record)",
            "d1": "arm Z0's chosen candidate (k8_sim_v04.plan_step, decision mode, leash = log), leashed positions",
            "d2": "constant current speed min(s_k + v_k t, s_end), v_k = max(v_log(t_k), 0)"}


def ref_d0(sc, k, tk, s, v, vmax, aux):
    return sc.s_log(tk + S.EVAL_T)


def ref_d1(sc, k, tk, s, v, vmax, aux):
    return aux[k]


def ref_d2(sc, k, tk, s, v, vmax, aux):
    return np.minimum(s + v * S.EVAL_T, sc.s_end)


REF_FN = {"d0": ref_d0, "d1": ref_d1, "d2": ref_d2}


def scene_items_x3(job):
    path, si, counts_only, ref, aux = job
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
        lead = REF_FN[ref](sc, k, tk, s, v, vmax, aux)
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
                if counts_only:
                    e0 = e1 = float("nan")             # v04 --counts-only: no ground-truth position is read
                else:
                    e0, e1 = sc.gt["x"][row] - pred_xy[j, h, 0], sc.gt["y"][row] - pred_xy[j, h, 1]
                for key, val in (("s", si), ("k", k), ("h", h), ("g", g[j]), ("r", r[j, h]), ("dx", e0), ("dy", e1), ("sxx", pred[j, h, 2]),
                                 ("sxy", pred[j, h, 3]), ("syy", pred[j, h, 4]), ("inpath", bool(inp[j])),
                                 ("yaw", float(tr["yaw"][sel[j]])), ("inst", int(inst[j])), ("row", int(sel[j])), ("m", int(m[j])),
                                 ("l0_long", int(l0[j, h, 0])), ("l0_lat", int(l0[j, h, 1])), ("sd_long", float(sd[j, h, 0])),
                                 ("sd_lat", float(sd[j, h, 1])), ("rel", int(np.argmax(G[h, j]))), ("gap_long", float(G[h, j, 0])),
                                 ("gap_lat", float(G[h, j, 1])),
                                 ("D_long", float("nan") if counts_only else float(np.sign(SP[h, j, 0]) * (ax[j, 0, 0] * e0 + ax[j, 0, 1] * e1))),
                                 ("D_lat", float("nan") if counts_only else float(np.sign(SP[h, j, 1]) * (ax[j, 1, 0] * e0 + ax[j, 1, 1] * e1))),
                                 ("pair", st["pairs_with_gt"])):
                    rc[key].append(val)
                pid = st["pairs_with_gt"]
                rel = int(np.argmax(G[h, j]))
                for a_ in range(2):
                    if not G[h, j, a_] > 0:
                        continue
                    D = float("nan") if counts_only else float(np.sign(SP[h, j, a_]) * (ax[j, a_, 0] * e0 + ax[j, a_, 1] * e1))
                    for key, val in (("s", si), ("k", k), ("h", h), ("g", g[j]), ("r", r[j, h]), ("a", a_), ("m", m[j]),
                                     ("inpath", bool(inp[j])), ("sd", sd[j, h, a_]), ("D", D), ("l0", l0[j, h, a_]),
                                     ("gap", float(G[h, j, a_])), ("pair", pid), ("ref_relied", a_ == rel)):
                        it[key].append(val)
    return si, it, rc, st


def z0_reference(path):
    """d1: per decision state k (1 ... K - 2) the candidate k8_sim_v04.plan_step chooses for arm Z0 in decision mode (exactly the call
    of k8_sim_v04.run_decisions, minus the record and calibration sinks, which do not touch the choice), and its leashed positions."""
    sc8 = S8.Scene(path)
    aux, z = {}, {f: [] for f in ("k", "choice", "infeasible", "lam", "ds_plan", "v_chosen", "v_now", "v_log")}
    if sc8.K < 3:
        return aux, z
    vmax = sc8.v_log_max + 2.0
    for k in range(1, sc8.K - 1):
        tk = float(sc8.kf_t[k])
        s, v = float(sc8.s_log(tk)), max(sc8.v_log(tk), 0.0)
        ps = S8.plan_step(sc8, "Z0", None, k, s, v, vmax, sc8.s_log, None, 0, None, None)
        c = ps["choice"]
        pos = np.minimum(S8.plan_positions(s, v, vmax)[c], sc8.s_log(tk + S8.EVAL_T))
        assert float(pos[S8.I_05] - s) == ps["ds_plan"], "Z0 reference positions differ from plan_step's leashed plan"
        aux[k] = pos
        for f, val in (("k", k), ("choice", c), ("infeasible", int(ps["infeasible"])),
                       ("lam", S8.LAM_ESTOP if ps["lam"] is None else float(ps["lam"])), ("ds_plan", ps["ds_plan"]),
                       ("v_chosen", ps["v_chosen"]), ("v_now", ps["v_now"]), ("v_log", ps["v_log"])):
            z[f].append(val)
    return aux, z


def job_x3(job):
    path, si, ref = job
    aux, z = (z0_reference(path) if ref == "d1" else ({}, None))
    si_, it, rc, st = scene_items_x3((path, si, False, ref, aux))
    # the reference progression of every decision state, for the record (the same function the item rule calls)
    sc = S.Scene(path)
    lk, lv = [], []
    if sc.K >= 3:
        vmax = sc.v_log_max + 2.0
        for k in range(1, sc.K - 1):
            tk = float(sc.kf_t[k])
            s, v = float(sc.s_log(tk)), max(sc.v_log(tk), 0.0)
            lk.append(k)
            lv.append(REF_FN[ref](sc, k, tk, s, v, vmax, aux))
    return si_, it, rc, st, z, (np.array(lk, np.int32), np.array(lv, float).reshape(-1, S.N_EVAL))


def source_diff():
    txt = open(ITEMS_SRC, encoding="utf-8").read()
    m = re.search(r"(def scene_items\(job\):.*?)\n\n\ndef main\(", txt, re.S)
    orig = m.group(1).rstrip().splitlines()
    mine = inspect.getsource(scene_items_x3).rstrip().splitlines()
    d = list(difflib.unified_diff(orig, mine, "k8_items_v08.scene_items", "x3_ref_items_v01.scene_items_x3", lineterm="", n=0))
    changed = [ln for ln in d if (ln.startswith("+") or ln.startswith("-")) and not ln.startswith("+++") and not ln.startswith("---")]
    return d, changed


def compare_to_record(out, trk):
    """d0 validation: every item_*, rec_*, scene_* array bitwise equal to the items of record (dtype, shape, bytes)."""
    z = np.load(C.ITEMS_REC[trk])
    res, ok = {}, True
    keys = sorted(set(k for k in z.files if k != "stamp") | set(k for k in out if k.startswith(("item_", "rec_", "scene_"))))
    for k in keys:
        if k not in z.files or k not in out:
            res[k] = "missing on one side"
            ok = False
            continue
        a, b = np.asarray(out[k]), z[k]
        same = a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()
        res[k] = "bitwise equal" if same else "DIFFERENT (dtype %s/%s shape %s/%s)" % (a.dtype, b.dtype, a.shape, b.shape)
        ok &= same
    return ok, res, sorted(z.files)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trk", required=True, choices=("t1", "t3"))
    ap.add_argument("--ref", required=True, choices=REFS)
    ap.add_argument("--workers", type=int, default=2)
    a = ap.parse_args(argv)
    C.run_log_ok()
    t0 = time.time()
    out_p = os.path.join(C.D_REF, "items_x3ref_%s_%s.npz" % (a.ref, a.trk))
    sum_p = out_p.replace(".npz", "_summary.json")
    C.check_out(out_p)
    assert not os.path.exists(out_p) and not os.path.exists(sum_p), "exists (resume: skip this one): " + out_p
    # the reference-of-record items must have been reproduced before an alternative reference is built
    if a.ref != "d0":
        vp = os.path.join(C.D_REF, "VALIDATION_d0_items_%s.json" % a.trk)
        assert os.path.exists(vp) and json.load(open(vp))["pass"], "d0 validation missing or failed: d1/d2 are not built"
    diff, changed = source_diff()
    assert len(changed) == 6, "scene_items_x3 differs from k8_items_v08.scene_items in more than the 3 intended lines: %s" % changed
    assert inspect.getsource(S.Scene) == inspect.getsource(S8.Scene), "k6 and k8 Scene classes differ"
    for fn in ("sensor_ctrv", "strata", "gaps"):
        assert inspect.getsource(getattr(S, fn)) == inspect.getsource(getattr(S8, fn)), "k6 and k8 differ in " + fn
    cdir = C.CACHE[a.trk]
    man = json.load(open(os.path.join(cdir, "MANIFEST.json")))
    jobs, names, logs = [], [], {}
    for scene, info in sorted(man["scenes"].items()):
        p = os.path.join(cdir, scene + ".npz")
        assert C.sha256_path(p) == info["sha256"], "cache file differs from its manifest: " + p
        jobs.append((p, len(names), a.ref))
        names.append(scene)
        logs[scene] = info["log"]
    C.live("items %s %s" % (a.ref, a.trk), 0, len(jobs))
    its = {k: [] for k in ITEM}
    rcs = {k: [] for k in REC}
    stats, done, zs, leads = {}, {}, {}, {}
    from x3_heavylock_v01 import heavy_lock
    with heavy_lock("x3-ref: items %s %s" % (a.ref, a.trk)):
        t1 = time.time()
        with Pool(a.workers) as pool:
            for i, (si, it, rc, st, z, lk) in enumerate(pool.imap_unordered(job_x3, jobs, chunksize=1)):
                done[si] = (it, rc)
                stats[names[si]] = st
                zs[si] = z
                leads[si] = lk
                if (i + 1) % 25 == 0 or i + 1 == len(jobs):
                    print("scenes %d/%d  %.0f s" % (i + 1, len(jobs), time.time() - t1), flush=True)
                    C.live("items %s %s" % (a.ref, a.trk), i + 1, len(jobs))
    for si in sorted(done):
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
    out["stamp"] = np.array(C.STAMP)
    out["x3_reference"] = np.array(a.ref + ": " + REF_TEXT[a.ref])
    out["x3_ref_scene"] = np.concatenate([np.full(len(leads[si][0]), si, np.int32) for si in sorted(leads)])
    out["x3_ref_k"] = np.concatenate([leads[si][0] for si in sorted(leads)])
    out["x3_ref_lead"] = np.concatenate([leads[si][1] for si in sorted(leads)])
    if a.ref == "d1":
        out["x3_z0_scene"] = np.concatenate([np.full(len(zs[si]["k"]), si, np.int32) for si in sorted(zs)])
        for f in ("k", "choice", "infeasible"):
            out["x3_z0_" + f] = np.concatenate([np.asarray(zs[si][f], np.int32) for si in sorted(zs)])
        for f in ("lam", "ds_plan", "v_chosen", "v_now", "v_log"):
            out["x3_z0_" + f] = np.concatenate([np.asarray(zs[si][f], float) for si in sorted(zs)])
    C.save_npz(out_p, **out)
    tot = {k: int(sum(st[k] for st in stats.values())) for k in ("decisions", "pairs_considered", "pairs_enforced", "pairs_with_gt")}
    summ = {"stamp": C.STAMP, "reference": a.ref, "reference_text": REF_TEXT[a.ref], "tracker": a.trk, "cache": cdir,
            "manifest_sha256": C.sha256_path(os.path.join(cdir, "MANIFEST.json")), "scenes": len(names),
            "items": int(len(out["item_D"])), "records": int(len(out["rec_dx"])),
            "items_ref_relied": int(out["item_ref_relied"].sum()),
            "relied_share": float(out["item_ref_relied"].mean()) if len(out["item_D"]) else None,
            "items_inpath_share": float(out["item_inpath"].mean()) if len(out["item_D"]) else None,
            "relied_inpath_share": float(out["item_inpath"][out["item_ref_relied"]].mean()) if out["item_ref_relied"].any() else None,
            "totals": tot, "source_diff_vs_k8_items_v08": diff,
            "code_sha256": C.code_record([os.path.abspath(__file__), C.__file__, S.__file__, S8.__file__, ITEMS_SRC]),
            "out": out_p, "out_sha256": C.sha256_path(out_p), "seconds": round(time.time() - t0, 1),
            "no_guard_ran": C.no_guard_ran(), "guard_modules_loaded": sorted(m for m in sys.modules if m.startswith("c1_guard"))}
    if a.ref == "d1":
        zi = out["x3_z0_infeasible"].astype(bool)
        summ["z0"] = {"decisions": int(len(zi)), "infeasible_share": float(zi.mean()) if len(zi) else None,
                      "estop_share": float((out["x3_z0_lam"] == S8.LAM_ESTOP).mean()) if len(zi) else None}
    if a.ref == "d0":
        ok, res, rec_files = compare_to_record(out, a.trk)
        rs = json.load(open(C.ITEMS_REC[a.trk].replace(".npz", "_summary.json")))
        tot_ok = rs["totals"] == tot
        val = {"stamp": C.STAMP, "check": "d0 items rebuilt by x3_ref_items_v01 vs the items of record, every array bitwise",
               "tracker": a.trk, "record": C.ITEMS_REC[a.trk], "record_sha256": C.sha256_path(C.ITEMS_REC[a.trk]),
               "rebuilt": out_p, "rebuilt_sha256": summ["out_sha256"], "arrays": res,
               "not_compared": "stamp (the record's builder stamp vs the X3 stamp, by design) and the x3_* arrays (absent from the record)",
               "totals_rebuilt": tot, "totals_record": rs["totals"], "totals_equal": tot_ok, "pass": bool(ok and tot_ok)}
        C.save_json(os.path.join(C.D_REF, "VALIDATION_d0_items_%s.json" % a.trk), val)
        summ["validation_d0_pass"] = val["pass"]
        print("D0 VALIDATION", "PASS" if val["pass"] else "FAIL", json.dumps({k: v for k, v in res.items() if v != "bitwise equal"}))
    C.save_json(sum_p, summ)
    C.run_log_ok()
    print(json.dumps({k: v for k, v in summ.items() if k not in ("source_diff_vs_k8_items_v08", "code_sha256")}))
    if a.ref == "d0" and not summ["validation_d0_pass"]:
        raise SystemExit("d0 VALIDATION FAILED: (d) stops here")
    print("X3 REF ITEMS DONE")


if __name__ == "__main__":
    main()
