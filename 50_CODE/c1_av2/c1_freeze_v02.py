#!/usr/bin/env python3
"""C1 freeze v02 (Claude line, c1_freeze_v02, 2 Nov 2026) = c1_freeze_v01 (kept, imported) with D16 v09 Choice 24's binding list:
the plan binds, by named argument, every C1 code file (the README's SHA-256 block), the folds file, the 225 + 150 split file, the
transfer fits, the stage-A cache manifests, the analysis configuration and the stage-B builder (av2_cache_stageB_v02); nothing made
after the freeze is ever bound: a within-AV2 fit, a stage-B manifest or a run record given to --bind is refused (they are checked by
provenance instead, R17 C1). The block's paths are relative to W, which c1_guard_v01, c1_run_v02 and c1_analyse_v03 all resolve
the same way. Then, as v01: refuses any [SLOT, a non-empty block, an existing sidecar or results; checks the README hashes, the
generators and the --test commands; writes the block, the .sha256 sidecar and a line in 40_PROTOCOL/C1_PLAN_HASH_LOG.txt.
Usage: python -B c1_freeze_v02.py --plan <plan.md> --readme <README> --results-dir <dir> --folds <json> --split <json>
       --transfer-fits <t1> <t3> --stageA-manifests <MANIFEST.json ...> --config <json> [--stageB <py>] [--test "..."] [--hash-log]
"""
import argparse
import json
import os
import sys

C1 = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, C1)
import c1_freeze_v01 as F1  # noqa: E402

W = F1.W
STAGEB = os.path.join(W, "50_CODE", "av2", "av2_cache_stageB_v02.py")


def post_freeze_artefact(p):
    """True for files made after the freeze, which are never bound: within-AV2 fits, stage-B manifests, run records."""
    try:
        d = json.load(open(p))
    except (ValueError, UnicodeDecodeError, OSError):
        return False
    if not isinstance(d, dict):
        return False
    return (d.get("c1") is True and d.get("route") == "within") or d.get("stage") == "B" or "episodes_sha256" in d


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--readme", required=True)
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--folds", required=True)
    ap.add_argument("--split", required=True)
    ap.add_argument("--transfer-fits", nargs=2, required=True)
    ap.add_argument("--stageA-manifests", nargs="+", required=True)
    ap.add_argument("--config", required=True)
    ap.add_argument("--stageB", default=STAGEB)
    ap.add_argument("--extra-bind", nargs="*", default=[])
    ap.add_argument("--test", nargs="*", default=[])
    ap.add_argument("--hash-log", default=F1.os.path.join(W, "40_PROTOCOL", "C1_PLAN_HASH_LOG.txt"))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3
    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only
    LEGACY.check("c1_freeze_v02", "c1_freeze_v04", dict(LEGACY.ds_bind_files([a.folds, a.split] + list(a.extra_bind)),
                                                        folds=LEGACY.ds_folds(a.folds)))
    for p in a.transfer_fits:
        assert json.load(open(p)).get("route") == "transfer", "--transfer-fits must be c1_fit transfer fits: " + p
    for p in a.stageA_manifests:
        assert json.load(open(p)).get("stage", "A") == "A", "a stage-B manifest is never bound (it carries the plan hash): " + p
    bind = [a.folds, a.split] + list(a.transfer_fits) + list(a.stageA_manifests) + [a.config, a.stageB] + list(a.extra_bind)
    for p in bind:
        assert not post_freeze_artefact(p), "made after the freeze, checked by provenance, never bound: " + p
    v1 = argparse.Namespace(plan=a.plan, readme=a.readme, results_dir=a.results_dir, bind=bind, test=a.test, hash_log=a.hash_log, dry_run=a.dry_run)
    bound = F1.check(v1)
    lines, h = F1.freeze(v1, bound)
    print("\n".join(lines[:4] + ["... (%d lines)" % len(lines)]))
    print("C1 FREEZE V02 %s" % ("DRY RUN: nothing written" if a.dry_run else "DONE: plan sha256 " + h))
    return h


if __name__ == "__main__":
    main()
