#!/usr/bin/env python3
"""D17 freeze v02 (Claude line, tpp_freeze_v02, 4 Nov 2026) = tpp_freeze_v01 (archived byte-exact in superseded_originals/; its
live copy refuses any plan under 90_DECISIONS) with R18b n2 and n3 (D16 v15 Choice 36):
  * the hash log: for a plan under 90_DECISIONS only the canonical 40_PROTOCOL/D17_PLAN_HASH_LOG.txt (c1_guard_v02.CANONICAL)
    is accepted, and there is no override; another log is allowed only for a plan outside 90_DECISIONS (a sandbox rehearsal);
  * it binds tpp_analyse_v04.code_files() (the analysis, every imported module incl. c1_guard_v02 and k8_items_v02, the config);
  * the slot test is c1_guard_v02's (not literal); the banner test is tpp_analyse_v04.unfrozen_banner;
  * the runs pass tpp_analyse_v04.check_runs (roles, seeds, model, keys, and three tracker-history runs whose 2-s predictions differ).
Otherwise as v01: refuses a filled block, an existing sidecar, existing results, a missing file, a run missing from its SHA256SUMS
list, a test that does not print ALL_PASS; then writes the FROZEN_HASHES block, the .sha256 sidecar and one line in the log.
Usage: python -I tpp_freeze_v02.py --plan 90_DECISIONS/D17_TPP_ARM_PREREG_v04.md --production [--test "<cmd>" ...] [--dry-run]
"""
import argparse
import datetime
import os
import shlex
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import tpp_analyse_v04 as T  # noqa: E402

G, C = T.G, T.C
W = T.W_ROOT
CANONICAL = G.CANONICAL["D17"]
FORBIDDEN_LOGS = ("M_PLAN_HASH_LOG.txt", "K6_PLAN_HASH_LOG.txt", "K7_PLAN_HASH_LOG.txt", "C1_PLAN_HASH_LOG.txt")


def check_log_policy(plan, hash_log):
    """R18b n2: a plan under 90_DECISIONS is frozen only into the canonical D17 log; another log only for a sandbox plan."""
    under = os.path.abspath(plan).startswith(os.path.abspath(os.path.join(W, "90_DECISIONS")))
    if under:
        assert os.path.abspath(hash_log) == os.path.abspath(CANONICAL), "a plan under 90_DECISIONS is frozen only into " + G.rel(CANONICAL)
    assert os.path.basename(hash_log) not in FORBIDDEN_LOGS, "never append to " + os.path.basename(hash_log)
    return under


def production_trackers():
    D = os.path.join(W, "30_DATA", "tpp_v01")
    S = os.path.join(D, "seed_sensitivity")
    return {t: {"keys": os.path.join(D, "keys_%s_val_v01.npz" % t), "trk": os.path.join(D, "tpp_int_ee_%s_trk_val_v01.npz" % t),
                "gt": os.path.join(D, "tpp_int_ee_%s_gt_val_v01.npz" % t),
                "s1a": os.path.join(S, "tpp_int_ee_%s_trk_val_seed%d_v01.npz" % (t, T.S1_SEEDS[0])),
                "s1b": os.path.join(S, "tpp_int_ee_%s_trk_val_seed%d_v01.npz" % (t, T.S1_SEEDS[1])),
                "cache": os.path.join(W, "30_DATA", "k6", "cache_v02_%s_val" % t)} for t in ("t1", "t3")}


def input_files(trackers):
    files, seen = [], set()
    for d in trackers.values():
        for f in [d["keys"], d["trk"], d["gt"], d["s1a"], d["s1b"], os.path.join(d["cache"], "MANIFEST.json"),
                  os.path.join(os.path.dirname(d["trk"]), "SHA256SUMS_v01.txt"), os.path.join(os.path.dirname(d["s1a"]), "SHA256SUMS_seed_v01.txt")]:
            if os.path.abspath(f) not in seen:
                seen.add(os.path.abspath(f))
                files.append(f)
    return files


def check(plan, trackers, results_dir, tests, hash_log, extra_modules=()):
    under = check_log_policy(plan, hash_log)
    assert not (under and extra_modules), "extra modules are bound only for a sandbox plan"
    txt = open(plan, encoding="utf-8").read()
    assert not G.SLOT.search(txt), "an open slot refuses the freeze"
    assert not T.unfrozen_banner(txt), "a plan carrying an unfrozen-version banner word is never frozen"
    for blk in ("FROZEN_HASHES", "FROZEN_ROLES"):
        assert txt.count(blk + "_BEGIN") == 1 and txt.count(blk + "_END") == 1, "the plan needs exactly one %s block" % blk
        assert not txt.split(blk + "_BEGIN")[1].split(blk + "_END")[0].strip(), "the %s block is not empty: already frozen" % blk
    side = plan[:-3] + ".sha256" if plan.endswith(".md") else plan + ".sha256"
    assert not os.path.exists(side), "a .sha256 sidecar already exists"
    assert not (os.path.isdir(results_dir) and os.listdir(results_dir)), "Trajectron++ arm results already exist: " + results_dir
    code = T.code_files()
    for f in code:
        assert os.path.exists(f), "code file missing: " + f
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


def freeze(plan, code, files, hash_log, dry_run=False, roles=(), extra_modules=()):
    now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    lines = ["# D17 frozen files (tpp_freeze_v02, %s UTC): code, configuration, inputs" % now]
    lines += ["%s  %s" % (G.sha(f), G.rel(f)) for f in list(code) + list(files) + list(extra_modules)]
    role_lines = ["# roles (c1_guard_v02): entry point, modules, configuration, inputs"] + ["%s  %s" % (r, G.rel(f)) for r, f in roles]
    role_lines += ["module  %s" % G.rel(f) for f in extra_modules]
    txt = open(plan, encoding="utf-8").read()
    for blk, body in (("FROZEN_HASHES", lines), ("FROZEN_ROLES", role_lines)):
        head, rest = txt.split(blk + "_BEGIN", 1)
        _, tail = rest.split(blk + "_END", 1)
        txt = head + blk + "_BEGIN\n" + "\n".join(body) + "\n" + blk + "_END" + tail
    new = txt
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
        f.write("%s  %s  frozen %s UTC by tpp_freeze_v02 (%d bound files)\n" % (h, G.rel(plan), now, len(lines) - 1))
    return lines, h


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--production", action="store_true", help="bind the standard 30_DATA/tpp_v01 inputs of T1 and T3")
    ap.add_argument("--tracker", nargs=7, action="append", default=[], metavar=("TAG", "KEYS", "TRK", "GT", "S1A", "S1B", "CACHE"))
    ap.add_argument("--results-dir", default=os.path.join(W, "60_RESULTS", "tpp_v01"))
    ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--sandbox-hash-log", default=None, help="only for a plan outside 90_DECISIONS (rehearsal)")
    ap.add_argument("--sandbox-extra-module", nargs="*", default=[], help="sandbox only: extra modules loaded by a test process")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    assert a.production != bool(a.tracker), "exactly one of --production or --tracker"
    hash_log = a.sandbox_hash_log or CANONICAL
    trackers = production_trackers() if a.production else {t[0]: dict(zip(("keys", "trk", "gt", "s1a", "s1b", "cache"), t[1:])) for t in a.tracker}
    code, files = check(a.plan, trackers, a.results_dir, a.test, hash_log, a.sandbox_extra_module)
    lines, h = freeze(a.plan, code, files, hash_log, a.dry_run, T.roles_of(trackers), a.sandbox_extra_module)
    print("\n".join(lines[:4] + ["... (%d lines)" % len(lines)]))
    print("TPP FREEZE V02 %s" % ("DRY RUN: nothing written" if a.dry_run else "DONE: plan sha256 " + h))
    return h


if __name__ == "__main__":
    main()
