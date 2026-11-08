#!/usr/bin/env python3
"""D17 freeze (Claude line, tpp_freeze_v01, 4 Nov 2026), modelled on 50_CODE/c1_av2/c1_freeze_v01.py and c1_freeze_v02.py
(D16 Choice 24 architecture; D16 v12 Choice 32 M3). Conditions, every one checked before anything is written:
  1. the plan holds no "[SLOT", never says DRAFT or NOT FROZEN, and has an empty FROZEN_HASHES block; no .sha256 sidecar exists;
  2. no Trajectron++ arm result exists (--results-dir absent or empty);
  3. every code file the analysis executes (tpp_analyse_v03.code_files(): the analysis, every imported module, the
     configuration) exists and is hashed; the configuration is the one the analysis loads;
  4. every input exists: per tracker the keys, the primary tracker-history and ground-truth runs, the two S1 seed runs,
     the cache MANIFEST and the two SHA256SUMS lists; every run is listed with its hash in its SHA256SUMS file; the runs
     pass tpp_analyse_v03.check_runs (roles, seeds, model, keys, three distinct tracker-history files);
  5. each --test command prints ALL_PASS;
  6. the hash log is never one of the M / K6 / K7 / C1 logs.
Then: the FROZEN_HASHES block ("<sha256>  <path relative to W>"), the plan's .sha256 sidecar, and one line appended to
40_PROTOCOL/D17_PLAN_HASH_LOG.txt (created if absent), with UTC times. c1_guard_v01.frozen_plan then accepts the plan.
Usage: python -I tpp_freeze_v01.py --plan 90_DECISIONS/D17_TPP_ARM_PREREG_v03.md --production [--test "<cmd>" ...] [--dry-run]
       (--production binds the standard 30_DATA/tpp_v01 inputs of T1 and T3; or give --tracker TAG KEYS TRK GT S1A S1B CACHE)
"""
import argparse
import datetime
import os
import re
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_analyse_v03 as T  # noqa: E402

G, C = T.G, T.C
W = T.W_ROOT
FORBIDDEN_LOGS = ("M_PLAN_HASH_LOG.txt", "K6_PLAN_HASH_LOG.txt", "K7_PLAN_HASH_LOG.txt", "C1_PLAN_HASH_LOG.txt")


def production_trackers():
    D = os.path.join(W, "30_DATA", "tpp_v01")
    S = os.path.join(D, "seed_sensitivity")
    out = {}
    for t in ("t1", "t3"):
        out[t] = {"keys": os.path.join(D, "keys_%s_val_v01.npz" % t), "trk": os.path.join(D, "tpp_int_ee_%s_trk_val_v01.npz" % t),
                  "gt": os.path.join(D, "tpp_int_ee_%s_gt_val_v01.npz" % t),
                  "s1a": os.path.join(S, "tpp_int_ee_%s_trk_val_seed%d_v01.npz" % (t, T.S1_SEEDS[0])),
                  "s1b": os.path.join(S, "tpp_int_ee_%s_trk_val_seed%d_v01.npz" % (t, T.S1_SEEDS[1])),
                  "cache": os.path.join(W, "30_DATA", "k6", "cache_v02_%s_val" % t)}
    return out


def input_files(trackers):
    files = []
    for d in trackers.values():
        files += [d["keys"], d["trk"], d["gt"], d["s1a"], d["s1b"], os.path.join(d["cache"], "MANIFEST.json"),
                  os.path.join(os.path.dirname(d["trk"]), "SHA256SUMS_v01.txt"), os.path.join(os.path.dirname(d["s1a"]), "SHA256SUMS_seed_v01.txt")]
    seen, out = set(), []
    for f in files:
        if os.path.abspath(f) not in seen:
            seen.add(os.path.abspath(f))
            out.append(f)
    return out


def check(plan, trackers, results_dir, tests, hash_log):
    txt = open(plan, encoding="utf-8").read()
    slots = sorted(set(re.findall(r"\[SLOT[^\]]*\]", txt)))
    assert not slots, "open slots refuse the freeze: %s" % slots[:3]
    assert not T.unfrozen_banner(txt), "a plan carrying an unfrozen-version banner word is never frozen"
    assert "FROZEN_HASHES_BEGIN" in txt and "FROZEN_HASHES_END" in txt, "the plan has no FROZEN_HASHES block"
    assert not txt.split("FROZEN_HASHES_BEGIN")[1].split("FROZEN_HASHES_END")[0].strip(), "the FROZEN_HASHES block is not empty: already frozen"
    side = plan[:-3] + ".sha256" if plan.endswith(".md") else plan + ".sha256"
    assert not os.path.exists(side), "a .sha256 sidecar already exists"
    assert not (os.path.isdir(results_dir) and os.listdir(results_dir)), "Trajectron++ arm results already exist: " + results_dir
    assert os.path.basename(hash_log) not in FORBIDDEN_LOGS, "never append to " + os.path.basename(hash_log)
    code = T.code_files()
    for f in code:
        assert os.path.exists(f), "code file missing: " + f
    assert os.path.abspath(T.CONFIG_PATH) in [os.path.abspath(f) for f in code]
    for tag, d in trackers.items():
        T.check_runs(d["keys"], {k: d[k] for k in ("trk", "gt", "s1a", "s1b")}, synthetic=False)
        for role, sums in (("trk", "SHA256SUMS_v01.txt"), ("gt", "SHA256SUMS_v01.txt"), ("s1a", "SHA256SUMS_seed_v01.txt"), ("s1b", "SHA256SUMS_seed_v01.txt")):
            listed = {ln.split()[0]: ln.split()[-1].lstrip("*") for ln in open(os.path.join(os.path.dirname(d[role]), sums)).read().splitlines() if ln.strip()}
            assert listed.get(C.sha256_path(d[role])) == os.path.basename(d[role]), "%s is not listed with its hash in %s" % (d[role], sums)
    files = input_files(trackers)
    for f in files:
        assert os.path.exists(f), "input missing: " + f
    for cmd in tests:
        r = subprocess.run(shlex.split(cmd, posix=os.name != "nt"), capture_output=True, text=True, cwd=HERE)
        assert r.returncode == 0 and "ALL_PASS" in r.stdout, "test did not print ALL_PASS: %s\n%s" % (cmd, (r.stdout + r.stderr)[-1500:])
    return code, files


def freeze(plan, code, files, hash_log, dry_run=False):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["# D17 frozen files (tpp_freeze_v01, %s UTC): code, configuration, inputs" % now]
    lines += ["%s  %s" % (G.sha(f), G.rel(f)) for f in code + files]
    txt = open(plan, encoding="utf-8").read()
    head, rest = txt.split("FROZEN_HASHES_BEGIN", 1)
    _, tail = rest.split("FROZEN_HASHES_END", 1)
    new = head + "FROZEN_HASHES_BEGIN\n" + "\n".join(lines) + "\nFROZEN_HASHES_END" + tail
    if dry_run:
        return lines, None
    with open(plan, "w", encoding="utf-8", newline="\n") as f:
        f.write(new)
    h = G.sha(plan)
    side = plan[:-3] + ".sha256" if plan.endswith(".md") else plan + ".sha256"
    with open(side, "w") as f:
        f.write("%s  %s\n" % (h, os.path.basename(plan)))
    os.makedirs(os.path.dirname(os.path.abspath(hash_log)), exist_ok=True)
    with open(hash_log, "a") as f:
        f.write("%s  %s  frozen %s UTC by tpp_freeze_v01 (%d bound files)\n" % (h, G.rel(plan), now, len(lines) - 1))
    return lines, h


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--production", action="store_true", help="bind the standard 30_DATA/tpp_v01 inputs of T1 and T3")
    ap.add_argument("--tracker", nargs=7, action="append", default=[], metavar=("TAG", "KEYS", "TRK", "GT", "S1A", "S1B", "CACHE"))
    ap.add_argument("--results-dir", default=os.path.join(W, "60_RESULTS", "tpp_v01"))
    ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--hash-log", default=T.HASH_LOG)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    assert a.production != bool(a.tracker), "exactly one of --production or --tracker"
    trackers = production_trackers() if a.production else {t[0]: dict(zip(("keys", "trk", "gt", "s1a", "s1b", "cache"), t[1:])) for t in a.tracker}
    code, files = check(a.plan, trackers, a.results_dir, a.test, a.hash_log)
    lines, h = freeze(a.plan, code, files, a.hash_log, a.dry_run)
    print("\n".join(lines[:4] + ["... (%d lines)" % len(lines)]))
    print("TPP FREEZE V01 %s" % ("DRY RUN: nothing written" if a.dry_run else "DONE: plan sha256 " + h))
    return h


if __name__ == "__main__":
    main()
