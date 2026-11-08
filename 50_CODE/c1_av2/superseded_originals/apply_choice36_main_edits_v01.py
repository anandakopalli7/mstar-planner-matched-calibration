#!/usr/bin/env python3
"""Applies the D16 Choice 36 rule 3 / Choice 39a main()-only edits (R17c B1) to the 17 superseded C1 entry points, once, after their
byte-exact originals were archived here (gzip, SHA256SUMS of the decompressed bytes). For every file: the original must equal the
archive; exactly one anchor line inside main() gets the refusal call inserted after (or before) it; afterwards everything before
"def main" and everything from 'if __name__ == "__main__":' is byte-identical to the original, and the file compiles.
Usage: <canmot310 python> -B apply_choice36_main_edits_v01.py [--check]   (--check: verify only, write nothing)
"""
import gzip
import hashlib
import os
import py_compile
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
C1 = os.path.dirname(HERE)
AV2 = os.path.join(os.path.dirname(C1), "av2")
PRE = "    import c1_legacy_refuse_v01 as LEGACY  # D16 Choice 36 rule 3 / Choice 39a (R17c B1): superseded; nuScenes or synthetic inputs only\n"
PRE_AV2 = ("    sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), \"c1_av2\"))  # Choice 36 rule 3\n" + PRE)
PRE_C1 = "    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))  # Choice 36 rule 3\n" + PRE
CFG = '    cfg = json.load(open(a.config))\n'
PARSE = '    a = ap.parse_args(argv)\n'
EDITS = {
    "c1_analyse_v01.py": (C1, CFG, "after", PRE_C1 + '    LEGACY.check("c1_analyse_v01", "c1_analyse_v06", LEGACY.ds_config(cfg))\n'),
    "c1_analyse_v02.py": (C1, CFG, "after", PRE_C1 + '    LEGACY.check("c1_analyse_v02", "c1_analyse_v06", LEGACY.ds_config(cfg))\n'),
    "c1_analyse_v03.py": (C1, CFG, "after", PRE_C1 + '    LEGACY.check("c1_analyse_v03", "c1_analyse_v06", LEGACY.ds_config(cfg))\n'),
    "c1_fit_v02.py": (C1, '    fj = json.load(open(a.folds))\n', "after", PRE_C1 +
                      '    LEGACY.check("c1_fit_v02", "c1_fit_v04", {"folds": LEGACY.ds_folds_obj(fj), "items": LEGACY.ds_items(a.items)},\n'
                      '                 "entry:c1_fit", a.plan)\n'),
    "c1_run_v01.py": (C1, '    hashes = code_hashes(a.fits, a.caches)\n', "after", PRE_C1 +
                      '    if not a.standin:\n        LEGACY.check("c1_run_v01", "c1_run_v04", {"caches": LEGACY.ds_manifests(a.caches)})\n'),
    "c1_run_v02.py": (C1, '    hashes = code_hashes(a.fits, a.caches)\n', "after", PRE_C1 +
                      '    if not a.standin:\n        LEGACY.check("c1_run_v02", "c1_run_v04", {"caches": LEGACY.ds_manifests(a.caches)}, "entry:c1_run", a.c1_plan)\n'),
    "c1_mstage_v01.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_mstage_v01", "c1_mstage_v04", {"AV2-set exports": LEGACY.ds_exports(a.av2_workers),\n'
                         '                                                  "training exports": LEGACY.ds_exports(a.train_workers)})\n'),
    "c1_mstage_v02.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_mstage_v02", "c1_mstage_v04", {"AV2-set exports": LEGACY.ds_exports(a.av2_workers),\n'
                         '                                                  "training exports": LEGACY.ds_exports(a.train_workers)})\n'),
    "c1_h8_v01.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_h8_v01", "c1_h8_v04", {"exports": LEGACY.ds_exports(a.workers)})\n'),
    "c1_h8_v02.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_h8_v02", "c1_h8_v04", {"exports": LEGACY.ds_exports(a.workers)})\n'),
    "c1_e0_v01.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_e0_v01", "c1_e0_v03", {"exports": LEGACY.ds_exports(a.workers)})\n'),
    "c1_predarm_v01.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_predarm_v01", "c1_predarm_v04", {"keys": LEGACY.ds_keys(a.keys)})\n'),
    "c1_predarm_v02.py": (C1, '    kz, rz, gt_xy, mu, cov = TA.load_inputs(a.keys, runs, a.synthetic, a.cache)\n', "before", PRE_C1 +
                          '    LEGACY.check("c1_predarm_v02", "c1_predarm_v04", {"keys": ds})\n'),
    "c1_freeze_v01.py": (C1, PARSE, "after", PRE_C1 + '    LEGACY.check("c1_freeze_v01", "c1_freeze_v04", LEGACY.ds_bind_files(a.bind))\n'),
    "c1_freeze_v02.py": (C1, PARSE, "after", PRE_C1 +
                         '    LEGACY.check("c1_freeze_v02", "c1_freeze_v04", dict(LEGACY.ds_bind_files([a.folds, a.split] + list(a.extra_bind)),\n'
                         '                                                        folds=LEGACY.ds_folds(a.folds)))\n'),
    "av2_cache_stageB_v01.py": (AV2, '    man = json.load(open(os.path.join(a.stage_a, "MANIFEST.json")))\n', "after", PRE_AV2 +
                                '    LEGACY.check("av2_cache_stageB_v01", "av2_cache_stageB_v04", {"stage-A cache": LEGACY.ds_manifest_obj(man)})\n'),
    "av2_cache_stageB_v02.py": (AV2, '    man = json.load(open(os.path.join(a.stage_a, "MANIFEST.json")))\n', "after", PRE_AV2 +
                                '    LEGACY.check("av2_cache_stageB_v02", "av2_cache_stageB_v04", {"stage-A cache": LEGACY.ds_manifest_obj(man)})\n'),
}


def original(d, f):
    arch = os.path.join(d, "superseded_originals")
    sums = dict(l.split(" *")[::-1] for l in open(os.path.join(arch, "SHA256SUMS_superseded_originals_v01.txt")).read().splitlines() if l.strip())
    b = gzip.open(os.path.join(arch, f + ".gz"), "rb").read()
    assert hashlib.sha256(b).hexdigest() == sums[f], "archive damaged: " + f
    return b.decode("utf-8")


def split3(txt):
    i = txt.index("\ndef main(") + 1
    j = txt.index('\nif __name__ == "__main__":') + 1
    return txt[:i], txt[i:j], txt[j:]


def edited(orig, anchor, where, ins):
    crlf = "\r\n" in orig
    t = orig.replace("\r\n", "\n")
    pre, main, post = split3(t)
    assert main.count(anchor) == 1, "anchor not exactly once in main(): %r" % anchor[:60]
    main2 = main.replace(anchor, anchor + ins) if where == "after" else main.replace(anchor, ins + anchor)
    out = pre + main2 + post
    return out.replace("\n", "\r\n") if crlf else out


def main():
    check_only = "--check" in sys.argv
    res = {}
    for f, (d, anchor, where, ins) in EDITS.items():
        orig = original(d, f)
        new = edited(orig, anchor, where, ins)
        live_p = os.path.join(d, f)
        live = open(live_p, encoding="utf-8", newline="").read()
        if check_only:
            assert live == new, "live file is not the archived original plus the recorded main() edit: " + f
        else:
            assert live == orig, "live file is not the archived original: " + f
            with open(live_p, "w", encoding="utf-8", newline="") as fh:
                fh.write(new)
        a0, _, c0 = split3(orig.replace("\r\n", "\n"))
        a1, _, c1 = split3(open(live_p, encoding="utf-8", newline="").read().replace("\r\n", "\n"))
        assert a0 == a1 and c0 == c1, "an edit outside main(): " + f
        py_compile.compile(live_p, doraise=True, cfile=os.devnull) if os.name != "nt" else compile(open(live_p, encoding="utf-8").read(), live_p, "exec")
        res[f] = hashlib.sha256(open(live_p, "rb").read()).hexdigest()
    for f, h in res.items():
        print(h, f)
    print("CHOICE 36 MAIN EDITS %s: %d files" % ("CHECKED" if check_only else "APPLIED", len(res)))


if __name__ == "__main__":
    main()
