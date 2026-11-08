#!/usr/bin/env python3
"""Builds the public code-and-results repository for the IEEE Access paper (the lead, 7 Nov 2026). v03: the author's decisions (MIT + CC BY 4.0; CITATION; tools statement), docs_v02, paper files v06g and latex_v04. v02: adds the cited
files v01 left out (R11), drops the duplicate platform copy of the K8 analysis and the analysis checkpoints, adds the
top-level documents (docs_v01/: README, DATA, THIRD_PARTY, LICENSE_OPTIONS, REVIEW_BEFORE_PUBLISHING, CITATION.cff),
tools/verify_release_v01.py, a generated ENVIRONMENT.md (package names and versions read from the environments'
*.dist-info folder names, nothing executed) and .gitignore, and asserts that nothing from 50_CODE/env or any key file is copied.

Output: 96_REPO_RELEASE/mstar_c1_repo_v03/ (refuses to overwrite). The tree mirrors the workspace's relative paths, so every
path cited in the manuscript and supplement resolves inside the repository.

Included (rules R1-R10 below); excluded: 30_DATA (datasets and annotation-derived files), 30_PRIOR_ART (third-party papers),
00_PROGRESS, 00_CONTEXT, the Python environment, third-party code (listed in THIRD_PARTY.md instead), large derived exports
and run caches, and internal review drafts. Every frozen file of the registration (plan v07m's list of 354) that is not
included is listed in EXCLUDED_FROZEN.tsv with its SHA-256 and the reason.
Writes MANIFEST_SHA256.txt (every file), INCLUDED_BY_RULE.tsv and CITED_PATHS.tsv (each path cited in the paper or
supplement: included / excluded and why / not found)."""
import hashlib
import os
import re
import shutil
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
OUT = os.path.join(W, "96_REPO_RELEASE", "mstar_c1_repo_v03")
DOCS = os.path.join(W, "80_LOGS", "c1_repo_v01", "docs_v02")
ENVS = ("canmot310", "sim310", "av2eval310", "ab3dmot310", "tpp38")
CITED_EXTRA = ["20_DESIGN/E01_EVIDENCE_DOSSIER_v02.md", "30_DATA/av2_det_owncp_v01/SHA256SUMS.txt",
               "30_DATA/detectors/RECEIPT_val_copy.sha256", "30_DATA/av2_trk_v02/logs/q_h_t1_val150.log",
               "70_TESTS/k8_expl_v02_linux/PLATFORM_CHECK_v02.md", "90_DECISIONS/C1_CRITERIA_REGISTER_v05.md",
               "90_DECISIONS/D17_TPP_ARM_PREREG_v04.md", "90_DECISIONS/D18_S0_SAMPLE_SIZE_DECISION_v02.md"]
PLAN = os.path.join(W, "40_PROTOCOL", "C1_AV2_CONFIRMATORY_PREREG_v07m.md")
MS = os.path.join(W, "20_DESIGN", "MANUSCRIPT_DRAFT_v06g.md")
SUPP = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06g_final.md")
TEXT = {".md", ".json", ".csv", ".txt", ".tsv", ".yaml", ".yml", ".cfg", ".toml", ".sha256", ".bib", ".tex", ".py", ".sh"}
SMALL = 5 * 1024 * 1024
SKIP_DIRS = {"__pycache__", ".git", ".ipynb_checkpoints"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def walk(rel, exts=None, max_size=SMALL, skip=()):
    base = os.path.join(W, rel)
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and d not in skip]  # skip by folder name
        for fn in files:
            p = os.path.join(root, fn)
            r = os.path.relpath(p, W).replace("\\", "/")
            if exts and os.path.splitext(fn)[1].lower() not in exts:
                continue
            if max_size and os.path.getsize(p) > max_size:
                continue
            yield r


def frozen_list():
    s = open(PLAN, encoding="utf-8").read()
    i = s.index("# C1 frozen files (c1_freeze_v07")
    rows = re.findall(r"^([0-9a-f]{64})  (\S+)$", s[i:], flags=re.M)
    assert len(rows) == 354, len(rows)
    return rows


RULES = [
    ("R1 frozen code and protocol (byte-identical)", None),
    ("R2 our code (50_CODE, no env or third-party)", lambda: walk("50_CODE", TEXT, 2 * 1024 * 1024, skip=("env", "third_party", "third_party_av2"))),
    ("R3 protocols, plans, logs (40_PROTOCOL, no zips)", lambda: walk("40_PROTOCOL", TEXT | {".sha256"}, SMALL)),
    ("R4 proofs and their checks (10_PROOFS)", lambda: walk("10_PROOFS", None, SMALL)),
    ("R5 results of record and exploratory results (small text)", lambda: (r for d in [
        "c1_av2_v01", "x3_explore_v01", "av2_det", "c1_folds_v01", "c1_transfer_fits_v01", "c1_e0_v02", "c1_s22_v01",
        "c1_s20a_v01", "c1_criteria_sensitivity_v01", "c1_criteria_sensitivity_v02", "c1_criteria_sensitivity_v03",
        "k8_joint_fits_v01", "k8_joint_v01", "k7_fits_v01", "x2", "x1", "m", "qcnet_av2", "tpp_v01", "k6_main_v02"]
        for r in walk("60_RESULTS/" + d, {".md", ".json", ".csv", ".txt", ".tsv", ".sha256"}, SMALL,
                      skip=("runs", "smoke", "d_ref_runs", "loop_smoke", "ckpt")))),
    ("R5b tracker and detector notes and metrics (60_RESULTS/av2_trk: md and HOTA/metric JSON only)",
     lambda: (r for r in walk("60_RESULTS/av2_trk", {".md", ".json", ".txt"}, 1024 * 1024)
              if r.endswith(".md") or "/hota/" in r or "/metrics" in r or "/equiv/" in r)),
    ("R6 development and re-derivation outputs (70_TESTS: K8 analysis, R21, K8 joint, X3 integrity)", lambda: (r for d in [
        "k8_expl_v02_analysis_v03", "R21_c1_v01", "k8_joint_v01", "X3_INTEGRITY_v01"]
        for r in walk("70_TESTS/" + d, {".md", ".json", ".csv", ".txt", ".py", ".sha256"}, SMALL,
                      skip=("k8_exploratory_analysis_v03_checkpoints",)))),
    ("R11 further files cited in the paper or supplement", lambda: (r for r in CITED_EXTRA)),
    ("R7 decision records (90_DECISIONS: D19 GO report, the decision record D16 v61, errata)", lambda: (
        r for r in walk("90_DECISIONS", {".md"}, SMALL)
        if re.search(r"(D19_GO_DECISION_v03|D16_DELEGATED_CHOICES_v61|ERRATA_)", r))),
    ("R8 paper sources (20_DESIGN: final manuscript and supplement, X3 plan and amendments, references, pre-fixed abstract)",
     lambda: (r for r in walk("20_DESIGN", None, SMALL) if re.search(
         r"(MANUSCRIPT_DRAFT_v06g\.md|SUPPLEMENT_v06g_final\.md|X3_POSTREG_EXPLORATORY_PLAN_v01\.|X3_PLAN_AMENDMENT_A\d_v01\.|"
         r"refs_v06c_v02\.bib|ABSTRACT_FILLED_r1_v01\.md|C1_REPORTING_FRAMES_v03\.md|PROVENANCE_MAP_v06g\.md)", r))),
    ("R9 build scripts for the paper, figures and references (80_LOGS)", lambda: (
        r for d in ("c1_manuscript_v01", "c1_figs_v02", "c1_refs_v01", "c1_repo_v01") for r in walk("80_LOGS/" + d, {".py"}, SMALL))),
    ("R10 LaTeX submission source and figures (95_SUBMISSION)", lambda: (
        r for d in ("latex_v04", "figs_v02") for r in walk("95_SUBMISSION/" + d, None, 20 * 1024 * 1024))),
]


def main():
    assert not os.path.exists(OUT), OUT
    frozen = frozen_list()
    chosen = {}
    for h, r in frozen:
        if r.startswith(("50_CODE/", "40_PROTOCOL/")):
            p = os.path.join(W, r)
            assert os.path.exists(p) and sha(p) == h, ("frozen file missing or changed", r)
            chosen[r] = RULES[0][0]
    for name, gen in RULES[1:]:
        for r in gen():
            chosen.setdefault(r, name)
    for r in chosen:  # safety: nothing from the environments, no key material
        assert "/env/" not in "/" + r and not re.search(r"(^|/)(id_rsa|id_ed25519|.*\.pem|.*\.dpapi|.*\.key)$", r), r
        assert os.path.exists(os.path.join(W, r)), ("missing", r)
    os.makedirs(OUT)
    total = 0
    for r in sorted(chosen):
        src = os.path.join(W, r)
        dst = os.path.join(OUT, r)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        total += os.path.getsize(src)
    # top-level documents, tools, environment list, .gitignore
    for fn in ("README.md", "DATA.md", "THIRD_PARTY.md", "CITATION.cff", "LICENSE", "LICENSE-docs"):
        shutil.copy2(os.path.join(DOCS, fn), os.path.join(OUT, fn))
        chosen[fn] = "R12 release documents"
    os.makedirs(os.path.join(OUT, "tools"))
    shutil.copy2(os.path.join(DOCS, "verify_release_v01.py"), os.path.join(OUT, "tools", "verify_release_v01.py"))
    chosen["tools/verify_release_v01.py"] = "R12 release documents"
    env_lines = ["# Environments (package versions read from the environments' *.dist-info folder names)\n",
                 "The study ran on Windows 11 (laptop) and Linux (rented GPU machines for the detector and the learned "
                 "predictor). Python 3.10 for everything except Trajectron++ (Python 3.8).\n"]
    for e in ENVS:
        base = os.path.join(W, "50_CODE", "env", e)
        sp = os.path.join(base, "Lib", "site-packages")
        ver = ""
        cfg = os.path.join(base, "pyvenv.cfg")
        if os.path.exists(cfg):
            m = re.search(r"^version(?:_info)?\s*=\s*(\S+)", open(cfg, encoding="utf-8").read(), flags=re.M)
            ver = m.group(1) if m else ""
        pk = sorted(d[:-len(".dist-info")] for d in os.listdir(sp) if d.endswith(".dist-info")) if os.path.isdir(sp) else []
        pk = [re.sub(r"-(\d[^-]*)$", r"==\1", p) for p in pk]
        env_lines.append("\n## `%s` (Python %s)\n\n```\n%s\n```\n" % (e, ver or "?", "\n".join(pk)))
    with open(os.path.join(OUT, "ENVIRONMENT.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(env_lines))
    chosen["ENVIRONMENT.md"] = "R12 release documents"
    with open(os.path.join(OUT, ".gitignore"), "w", encoding="utf-8", newline="\n") as f:
        f.write("__pycache__/\n*.pyc\n.DS_Store\nThumbs.db\n")
    chosen[".gitignore"] = "R12 release documents"
    with open(os.path.join(OUT, "MANIFEST_SHA256.txt"), "w", encoding="utf-8", newline="\n") as f:
        for r in sorted(chosen):
            f.write("%s  %s\n" % (sha(os.path.join(OUT, r)), r))
    with open(os.path.join(OUT, "INCLUDED_BY_RULE.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("path\trule\n")
        for r in sorted(chosen):
            f.write("%s\t%s\n" % (r, chosen[r]))
    with open(os.path.join(OUT, "EXCLUDED_FROZEN.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("sha256\tpath\tsize_bytes\treason\n")
        n = 0
        for h, r in frozen:
            if r in chosen:
                continue
            p = os.path.join(W, r)
            size = os.path.getsize(p) if os.path.exists(p) else -1
            reason = ("dataset-derived (annotations, detections or tracker outputs of nuScenes / Argoverse 2); size; "
                      "regenerable with the frozen code; available in the data archive if the authors deposit one")
            f.write("%s\t%s\t%d\t%s\n" % (h, r, size, reason))
            n += 1
    cited = set()
    for doc in (MS, SUPP):
        for m in re.finditer(r"`([0-9]{2}_[A-Z_]+/[^`\s]+)`", open(doc, encoding="utf-8").read()):
            cited.add(m.group(1).rstrip(".,;:)"))
    with open(os.path.join(OUT, "CITED_PATHS.tsv"), "w", encoding="utf-8", newline="\n") as f:
        f.write("cited_path\tstatus\n")
        stats = {}
        for c in sorted(cited):
            c0 = c.split(":")[0]
            if "*" in c0 or "{" in c0:
                st = "pattern (not resolved)"
            elif c0 in chosen or any(k.startswith(c0.rstrip("/") + "/") for k in chosen):
                st = "included"
            elif os.path.exists(os.path.join(W, c0)):
                st = "excluded (exists in the workspace)"
            else:
                st = "not found"
            stats[st] = stats.get(st, 0) + 1
            f.write("%s\t%s\n" % (c, st))
    print("written", OUT)
    print("files %d, %.1f MB; frozen included %d, frozen excluded %d" % (
        len(chosen), total / 1e6, sum(1 for h, r in frozen if r in chosen), n))
    by = {}
    for r, rule in chosen.items():
        by[rule] = by.get(rule, 0) + 1
    for k, v in by.items():
        print("  %5d  %s" % (v, k))
    print("cited paths:", stats)


if __name__ == "__main__":
    sys.exit(main())
