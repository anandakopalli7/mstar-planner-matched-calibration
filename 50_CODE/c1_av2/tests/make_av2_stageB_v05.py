#!/usr/bin/env python3
"""Generator of 50_CODE/av2/av2_cache_stageB_v05.py from av2_cache_stageB_v04.py (not modified), asserted replacements (D16 v21 Choice 42;
R17d B1, B2, M1, m2, (g)). v05 = v04 on c1_guard_v04, and on AV2:
  * the deposit record is checked inside guard() (validated: OSF URL or DOI, registered_utc after the plan's log line, before now and
    before every stage-B build), before any ground truth is read;
  * the ground truth is read ONLY from the quarantine 30_DATA/av2_gt_quarantine_v01/ (a .gz member), decompressed in memory and accepted
    only if its SHA-256 equals the stage-A manifest's inputs.gt_sha256 (c1_guard_v04.open_quarantined);
  * the output goes ONLY to 30_DATA/av2_cache_stageB_<--tag>/, which must not exist (never overwritten);
  * one line is appended to the append-only 40_PROTOCOL/C1_STAGE_B_LOG.txt (UTC, plan, deposit record, output manifest hash, tag) and
    one to 40_PROTOCOL/C1_RUN_LOG.txt.
nuScenes caches keep --out and a plain --gt (tests). Usage (from 50_CODE/c1_av2): python -B tests/make_av2_stageB_v05.py
"""
import hashlib
import os

C1 = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AV2 = os.path.join(os.path.dirname(C1), "av2")


def rep(s, old, new):
    assert s.count(old) == 1, "expected one occurrence of %r" % old[:90]
    return s.replace(old, new)


def make(src):
    s = src
    s = rep(s, '"""av2_cache_stageB_v04 = av2_cache_stageB_v03 (kept)',
            '"""av2_cache_stageB_v05 = av2_cache_stageB_v04 (kept) on c1_guard_v04 (D16 v21 Choice 42), written by c1_av2/tests/make_av2_stageB_v05.py.\n'
            'On AV2: the validated deposit record before any ground truth; ground truth only from the quarantine 30_DATA/av2_gt_quarantine_v01/\n'
            '(decompressed SHA-256 = the stage-A manifest\'s gt_sha256); output only to 30_DATA/av2_cache_stageB_<tag>/ (never overwritten); one\n'
            'line appended to 40_PROTOCOL/C1_STAGE_B_LOG.txt and one to 40_PROTOCOL/C1_RUN_LOG.txt. nuScenes keeps --out and a plain --gt.\n'
            'av2_cache_stageB_v04 = av2_cache_stageB_v03 (kept)')
    s = rep(s, "import c1_guard_v03 as G  # noqa: E402\n", "import c1_guard_v04 as G  # noqa: E402\n")
    s = rep(s, '    ap.add_argument("--out", required=True)\n',
            '    ap.add_argument("--out", default=None, help="nuScenes only; AV2 writes 30_DATA/av2_cache_stageB_<tag>/")\n'
            '    ap.add_argument("--tag", default=None, help="AV2: the output folder is 30_DATA/av2_cache_stageB_<tag>/")\n')
    s = rep(s, "    plan_sha, rt, deposit = None, None, None\n", "    plan_sha, rt, deposit, gt_bytes, gt_sha = None, None, None, None, None\n")
    s = rep(s, "            G.check_inputs(frozen, [a.gt])\n            deposit = G.check_deposit(plan_sha, dataset)\n",
            "            deposit = rt[\"deposit\"]\n"
            "            assert a.tag and a.out is None, \"AV2: --tag only; the output is 30_DATA/av2_cache_stageB_<tag>/ (Choice 42c)\"\n"
            "            assert all(ch.isalnum() or ch in \"_-\" for ch in a.tag), \"the tag is letters, digits, _ and - only\"\n"
            "            a.out = os.path.join(G.W, \"30_DATA\", \"av2_cache_stageB_\" + a.tag)\n"
            "            assert not os.path.exists(a.out), \"the stage-B output %s exists: never overwritten (Choice 42c, g)\" % G.rel(a.out)\n"
            "            gt_sha = (man.get(\"inputs\") or {}).get(\"gt_sha256\")\n"
            "            assert gt_sha, \"the stage-A manifest records no gt_sha256\"\n"
            "            gt_bytes = G.open_quarantined(a.gt, gt_sha)\n")
    s = rep(s, "    g = json.load(open(a.gt))\n",
            "    if dataset == \"nuscenes\":\n"
            "        assert a.out, \"nuScenes: --out is required\"\n"
            "    g = json.loads(gt_bytes) if gt_bytes is not None else json.load(open(a.gt))\n")
    s = rep(s, '"gt": os.path.abspath(a.gt), "gt_sha256": sha256_path(a.gt),',
            '"gt": os.path.abspath(a.gt), "gt_sha256": gt_sha or sha256_path(a.gt), "gt_file_sha256": sha256_path(a.gt),')
    s = rep(s, 'filled from the GT table by av2_cache_stageB_v04"\n', 'filled from the GT table by av2_cache_stageB_v05"\n')
    s = rep(s, '    json.dump(out_man, open(os.path.join(a.out, "MANIFEST.json"), "w"), indent=1)\n',
            '    json.dump(out_man, open(os.path.join(a.out, "MANIFEST.json"), "w"), indent=1)\n'
            '    if dataset != "nuscenes":\n'
            '        mh = sha256_path(os.path.join(a.out, "MANIFEST.json"))\n'
            '        line = {"utc": G.utc_now().strftime("%Y-%m-%dT%H:%M:%SZ"), "plan_sha256": plan_sha, "deposit_record_sha256": deposit["sha256"],\n'
            '                "out_manifest_sha256": mh, "tag": a.tag, "stage_a_manifest_sha256": out_man["stage_b"]["stage_a_manifest_sha256"]}\n'
            '        with open(G.STAGE_B_LOG, "a") as f:\n'
            '            f.write(json.dumps(line, sort_keys=True) + "\\n")\n'
            '            f.flush()\n'
            '            os.fsync(f.fileno())\n'
            '        G.run_log_append(dataset, os.path.abspath(__file__), plan_sha, deposit["sha256"], {"stage_a_manifest": line["stage_a_manifest_sha256"],\n'
            '                         "gt_decompressed": gt_sha}, [os.path.join(a.out, "MANIFEST.json")])\n')
    return s


def main():
    with open(os.path.join(AV2, "av2_cache_stageB_v04.py"), encoding="utf-8", newline="") as f:
        out = make(f.read())
    with open(os.path.join(AV2, "av2_cache_stageB_v05.py"), "w", encoding="utf-8", newline="") as f:
        f.write(out)
    print(hashlib.sha256(out.encode("utf-8")).hexdigest(), "av2_cache_stageB_v05.py")


if __name__ == "__main__":
    main()
