#!/usr/bin/env python3
"""X3 amendment A4 (2): loop-mode replay on Argoverse 2, descriptive (x3-core agent, x3_a4loop_v01, 7 Nov 2026). Added after
review (amendment A4). X3 POST-REGISTRATION EXPLORATORY (after the verdict of record; not part of the registered test).

k8_sim_v04.run_episode through x3_run_v03 --mode loop (delays 0, 2, 4 keyframes; every log of the 375), arms M*, B0, B4, B6 (fits of
record), B8 ((e1) fit), the (a) B6 composite (per fold the chosen delta' point's B6_ip, one fits file), and LOG (the delayed logged
profile, the record's reference for artefact collisions). Endpoints by k8_analyse_v04's / k6_analyse_v02's loop functions:
A.outcome_summary (collisions at fault with tracked and untracked agents per 1000 episodes with Poisson intervals, LOG-reference
artefacts removed; progress; infeasible, emergency-stop and hard-braking frame shares), K.arm_endpoints(mode "loop") (per key:
progress ratio, infeasible rate, divergence share), K.loop_safety_vectors (per key collisions); per-arm log-bootstrap 95 % intervals
(K.wmean_ci) and M* minus arm paired (K.paired_rows), keys (log, delay), B = 4000, seed [20261201, i, 12]. No ranking or claim:
non-reactive agents make loop-mode collisions an optimistic and confounded measure (K.LOOP_CONFOUND_NOTE).
Usage: python -B x3_a4loop_v01.py [--trackers t1 t3] [--tag-prefix a4loop]
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "3")

import argparse  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402

import numpy as np  # noqa: E402

X3 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, X3)
import x3_common_v01 as C  # noqa: E402
import x3_screen_v01 as SC  # noqa: E402

K, A = SC.K, SC.A
LABEL = "added after review (amendment A4)"
OUT = os.path.join(C.OUT, "a4_review")
RUN_DIR = os.path.join(C.OUT, "runs")
ENDPOINTS = ("collisions_at_fault_tracked_per_episode", "collisions_at_fault_untracked_per_episode", "progress", "infeasible_frame_share",
             "hard_brake_frame_share", "divergence_share", "progress_ratio")


def write_specs():
    """Loop specs: group 'first' = LOG, M*, B0, B6; group 'rest' = B4, B8, the (a) B6 composite (fits merged per fold)."""
    am = json.load(open(os.path.join(C.OUT, "a_matched", "x3_a_matched_v01.json")))["by_tracker"]
    for t in ("t1", "t3"):
        ch = {f: c["point"] for f, c in am[t]["families"]["B6"]["choice_by_fold"].items()}
        merged = {"stamp": C.STAMP, "label": LABEL, "what": "(a) B6 composite: fold f takes the B6 fits of its chosen delta' point", "choice_by_fold": ch,
                  "fold_of_scene": None, "fits": {}}
        for f, pnt in ch.items():
            src = json.load(open(os.path.join(C.OUT, "a_matched", "fits", "fits_x3a_%s_d%s.json" % (t, pnt.split("@")[1]))))
            merged["fold_of_scene"] = src["fold_of_scene"]
            merged["fits"][f] = src["fits"][f]
        fp = os.path.join(OUT, "fits", "fits_x3a4_B6composite_%s.json" % t)
        C.jdump(fp, merged)
        first = [{"label": "LOG", "base": "LOG", "fits": None, "cov_dir": None},
                 {"label": "Mstar", "base": "Mstar", "fits": C.FITS_REC[t], "cov_dir": None},
                 {"label": "B0", "base": "B0", "fits": None, "cov_dir": None},
                 {"label": "B6", "base": "B6", "fits": C.FITS_REC[t], "cov_dir": None}]
        rest = [{"label": "B4", "base": "B4", "fits": C.FITS_REC[t], "cov_dir": None},
                {"label": "X3E1_B8", "base": "Mstar", "fits": os.path.join(C.OUT, "e_alternatives", "fits", "fits_x3e1_B8_%s.json" % t), "cov_dir": None},
                {"label": "A_B6_composite", "base": "B6", "fits": fp, "cov_dir": None}]
        for g, vs in (("first", first), ("rest", rest)):
            C.jdump(os.path.join(RUN_DIR, "specs", "spec_a4loop_%s_%s_v01.json" % (g, t)), {"stamp": C.STAMP, "label": LABEL,
                    "purpose": "A4 (2) loop mode, group %s" % g, "variants": vs})
    print("loop specs written")


def per_key(eps, arm, kidx, n, f):
    v = np.full(n, np.nan)
    for o in eps:
        if o["arm"] == arm and o.get("entered") and (o["scene"], o["delay_kf"]) in kidx:
            x = f(o)
            if x is not None:
                v[kidx[(o["scene"], o["delay_kf"])]] = float(x)
    return v


def analyse(t, tags):
    eps, Ds = [], []
    for tag in tags:
        e = [json.loads(l) for l in open(os.path.join(RUN_DIR, "episodes_%s.jsonl" % tag))]
        off = (max(o["episode"] for o in eps) + 1) if eps else 0
        for o in e:
            o["episode"] += off
        D = dict(np.load(os.path.join(RUN_DIR, "decisions_%s.npz" % tag)))
        D["episode"] = D["episode"].astype(np.int64) + off
        eps += e
        Ds.append(D)
    D = {k: np.concatenate([d[k] for d in Ds]) for k in Ds[0] if isinstance(Ds[0][k], np.ndarray) and Ds[0][k].ndim >= 1 and len(Ds[0][k]) == len(Ds[0]["episode"])}
    eps = [o for o in eps if o["entered"]]     # as analyse_loop: entered episodes only (LOG included, the artefact reference)
    eps_p = [o for o in eps if o["arm"] != "LOG"]
    los = {o["scene"]: o["scene"] for o in eps}
    sb = [C.SEED_BOOT_X3, C.TRACKER_I[t], 12]
    keys, scene_of_ep, logs, log_of_ep, W_logs = A.keys_and_weights(eps_p, los, C.B_X3, np.random.default_rng(sb))
    W = W_logs[:, log_of_ep]
    n = len(keys)
    kidx = {k: i for i, k in enumerate(keys)}
    arms = [a for a in ("Mstar", "B0", "B4", "B6", "X3E1_B8", "A_B6_composite") if any(o["arm"] == a for o in eps_p)]
    outcomes = A.outcome_summary(eps)
    by_delay = {str(d): A.outcome_summary([o for o in eps if o["delay_kf"] == d]) for d in sorted({o["delay_kf"] for o in eps})}
    rows = K.dec_rows(D, eps_p, kidx)
    svecs = K.loop_safety_vectors(eps, arms, kidx, n)
    vecs, per_arm = {}, {}
    for a in arms:
        ep, v = K.arm_endpoints(*rows[a], n, W, "loop")
        v = dict(v)
        v.update(svecs[a])
        v["progress"] = per_key(eps, a, kidx, n, lambda o: o.get("progress"))
        v["infeasible_frame_share"] = per_key(eps, a, kidx, n, lambda o: o["infeasible_frames"] / max(o["frames"], 1))
        v["hard_brake_frame_share"] = per_key(eps, a, kidx, n, lambda o: o["hard_brake_frames"] / max(o["frames"], 1))
        vecs[a] = v
        oc = outcomes[a]
        per_arm[a] = {"episodes": oc["episodes"], "entered_keys": int(np.isfinite(v["infeasible_frame_share"]).sum()),
                      "at_fault_tracked": oc["at_fault_tracked"], "at_fault_tracked_per_1000": oc["at_fault_tracked_per_1000"],
                      "at_fault_tracked_ci": oc["at_fault_tracked_ci"], "at_fault_tracked_fallback_related": oc["at_fault_tracked_fallback_related"],
                      "at_fault_untracked": oc["at_fault_untracked"], "at_fault_untracked_per_1000": oc["at_fault_untracked_per_1000"],
                      "at_fault_untracked_ci": oc["at_fault_untracked_ci"], "artefact_collisions": oc["artefact_collisions"],
                      "progress_mean": oc["progress_mean"], "infeasible_frame_share": oc["infeasible_frame_share"],
                      "emergency_stop_frame_share": oc["emergency_stop_frame_share"], "hard_brake_frame_share": oc["hard_brake_frame_share"],
                      "key_level": {e: K.wmean_ci(v[e], W) for e in ENDPOINTS}}
    pairs = [("Mstar", b) for b in arms if b != "Mstar"]
    paired = K.paired_rows(vecs, arms, W, pairs, ENDPOINTS)
    return {"tracker": t, "runs": tags, "seed_bootstrap": sb, "B": C.B_X3, "keys": n, "arms": per_arm,
            "by_delay": {d: {a: {k: od[a].get(k) for k in ("episodes", "at_fault_tracked", "at_fault_untracked", "progress_mean", "infeasible_frame_share",
                                                          "hard_brake_frame_share")} for a in od if a in arms} for d, od in by_delay.items()},
            "Mstar_minus_arm": [{k: r[k] for k in ("endpoint", "arm_b", "mean_diff", "ci95_lo", "ci95_hi", "n_scenes")} for r in paired],
            "confound_note": K.LOOP_CONFOUND_NOTE}


def md(r):
    L = ["# X3 A4 (2): loop-mode replay on Argoverse 2 (descriptive)", "", "**%s** -- %s" % (C.STAMP, LABEL), "",
         "k8_sim_v04.run_episode, delays 0, 2, 4 keyframes, 375 logs; endpoints by the record's loop functions; keys (log, delay); "
         "log bootstrap B = 4000, seed [20261201, i, 12]. **No ranking or claim:** " + K.LOOP_CONFOUND_NOTE + ".", ""]
    for t, x in r["by_tracker"].items():
        L += ["## %s" % t.upper(), "", "| arm | episodes | at fault, tracked (per 1000; 95 % CI) | at fault, untracked (per 1000) | progress | infeasible frames | hard braking | divergence share |",
              "|---|---|---|---|---|---|---|---|"]
        for a, v in x["arms"].items():
            kl = v["key_level"]
            L.append("| %s | %d | %d (%.2f; %.2f-%.2f) | %d (%.2f) | %.4f | %.4f | %.4f | %.4f |" % (
                a, v["episodes"], v["at_fault_tracked"], v["at_fault_tracked_per_1000"], v["at_fault_tracked_ci"][0], v["at_fault_tracked_ci"][1],
                v["at_fault_untracked"], v["at_fault_untracked_per_1000"], v["progress_mean"] if v["progress_mean"] is not None else float("nan"),
                v["infeasible_frame_share"], v["hard_brake_frame_share"], kl["divergence_share"]["mean"] if kl["divergence_share"]["mean"] is not None else float("nan")))
        L += ["", "M* minus arm (key level, 95 % CI):", "", "| arm | endpoint | M* - arm | 95 % CI |", "|---|---|---|---|"]
        for p in x["Mstar_minus_arm"]:
            if p["mean_diff"] is not None:
                L.append("| %s | %s | %.4f | [%.4f, %.4f] |" % (p["arm_b"], p["endpoint"], p["mean_diff"], p["ci95_lo"], p["ci95_hi"]))
        L.append("")
    return "\n".join(L)


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--trackers", nargs="+", default=["t1", "t3"])
    ap.add_argument("--groups", nargs="+", default=["first", "rest"])
    ap.add_argument("--suffix", default="v01")
    ap.add_argument("--specs", action="store_true")
    a = ap.parse_args(argv)
    if a.specs:
        write_specs()
        return
    C.assert_run_log("A4 loop analysis start")
    SC.setup()
    t0 = time.time()
    r = {"stamp": C.STAMP, "label": LABEL, "part": "(2) loop mode, descriptive", "by_tracker": {}}
    for t in a.trackers:
        tags = [("a4loop_%s_%s" % (g, t)) for g in a.groups if os.path.exists(os.path.join(RUN_DIR, "run_record_a4loop_%s_%s.json" % (g, t)))]
        r["by_tracker"][t] = analyse(t, tags)
        print("(A4 2) %s done (%s)" % (t, tags), flush=True)
    r["seconds"] = round(time.time() - t0, 1)
    C.jdump(os.path.join(OUT, "x3_a4_2_loop_%s.json" % a.suffix), r)
    C.wtext(os.path.join(OUT, "x3_a4_2_loop_%s.md" % a.suffix), md(r))
    C.assert_run_log("A4 loop analysis end")


if __name__ == "__main__":
    main()
