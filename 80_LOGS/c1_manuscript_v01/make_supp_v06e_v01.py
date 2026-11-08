"""make_supp_v06e_v01.py -- build the reviewer-facing supplement v06e from v06d_final.

Applies a fixed list of exact string edits (one regex edit, the algorithm label in a
fixed-width code block) to 20_DESIGN/SUPPLEMENT_v06d_final.md and writes
20_DESIGN/SUPPLEMENT_v06e.md plus a JSON record of every applied edit
(80_LOGS/c1_manuscript_v01/supp_v06e_edits_v01.json), which the checker replays.

Rules: no number, table value, result or claim is changed; every edit must match the
stated number of times or the script stops; existing files are never overwritten.
"""
import argparse
import hashlib
import json
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
IN = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06d_final.md")
IN_SHA_PREFIX = "0bf56c14"
OUT = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06e.md")
EDITS_JSON = os.path.join(W, "80_LOGS", "c1_manuscript_v01", "supp_v06e_edits_v01.json")

PAPER_TITLE = ("Planner-Matched Calibration of Tracker Covariances for Chance-Constrained "
               "Planning, with a Registered Open-Loop Log-Replay Test on Argoverse 2")
DR = "the authors' decision record"

GLOSSARY = """## Codes used in this supplement

Terms of the main text keep their main-text meaning (Section IV and Appendix C of the main text). The codes below name studies, analyses and records; they are labels, not results.

| Code | Meaning | Where |
|---|---|---|
| T1, T2, T3 | The nuScenes tracker settings: CANMOT with process noise tuned on val (T1) or set to a sample covariance (T2), and Poly-MOT (T3). T1 and T3 are the trackers of the registered test; AB3DMOT is its descriptive third tracker. | S1.2; S9.15.2 |
| X1, X2 | The two pre-specified nuScenes diagnosis studies behind main-text Section V-B (X1 on val, X2 on train). | S1.8 |
| Method stage; HM1–HM6; E1, E2 | The pre-specified nuScenes study of DP-SCRC, M\\*'s parent, on the audit population; its hypotheses; its cross-validated evaluation on train (E1) and its train-to-val transfer (E2). | S1 |
| K6 | The first planner study on nuScenes (pre-specified; NO-GO). | S2.1 |
| K8 | The exploratory planner study on nuScenes on which M\\* and the registered rules were developed (main-text Section V-C). | S2.2 |
| D17 | The pre-specified Trajectron++ study on nuScenes, named after its plan file. | S3 |
| C1; H1–H10, Q1 | The registered test on Argoverse 2 (main-text Section V-D) and its claims; Q1, the QCNet claim, was dropped before the freeze and not tested. "The C1 plan" is its frozen plan (v07m). | S4, S5, S7 |
| X3; A1–A5 | The post-registration exploratory analyses of main-text Section V-E, and the five amendments to their plan (A5 is S6.22). | S6 |
| P0–P7 (in S6) | The partitions of X3's analysis (b). | S6.3 |
| P1–P18 (in S5 and S10) | The computations made before the freeze, in time order. | S10.3 |
| V0–V2 (in S6.1) | X3's validation gates. Elsewhere V2 is the main text's share of decisions with an exceeded relied constraint. | S6.1 |
| G0–G3, W (in S10) | What a computation before the freeze read of the annotations. | S10.1 |
| R06–R21 | The project's internal reviews, checks and re-derivations, filed in `70_TESTS/` under these codes, for example R08 (method-stage results), R16 (K8 results), R17–R17g and R20 (code and plan of the registered test), R19 (Trajectron++ results) and R21 (the separate re-derivation of the registered results). | source tags; S4(g); S10.6 |
| D06–D10, D14, D17, D18; E01 | Design, decision and report files in `90_DECISIONS/`, for example D07 (the method-stage report) and D14 (the K8 design); E01 is the evidence dossier of the nuScenes stages, `20_DESIGN/E01_EVIDENCE_DOSSIER_v02.md`. | source tags |
| The authors' decision record (DR in S10) | One released file that records the authors' design and reporting decisions. | source tags |
| AV2 | Argoverse 2. | — |
"""

# Each edit: id, item (of the brief), cat (category), old, new, n (expected matches),
# ids_removed (True if the edit removes version or decision identifiers), regex (bool).
EDITS = [
    # ---- item 1: front matter -------------------------------------------------------
    dict(id="E01", item=1, cat="front matter: title",
         old="# Supplementary Material for: Planner-Matched Calibration of Tracker Covariances for Chance-Constrained Planning, with a Registered Log-Replay Test on Argoverse 2",
         new="# " + PAPER_TITLE),
    dict(id="E02", item=1, cat="front matter: draft version", ids_removed=True,
         old="**Supplement to manuscript v06c** (assembled 7 Nov 2026).",
         new="**Supplementary material** (assembled 7 Nov 2026)."),
    dict(id="E03", item=1, cat="front matter: draft version", ids_removed=True,
         old="refer to the main text of manuscript v06c.",
         new="refer to the main text."),
    dict(id="E04", item="6, 7", cat="front matter: source tags and paths",
         old="Source tags are in backticks, as in the main text, and paths are relative to the project workspace.",
         new=("The supplement's bracketed source tags point to released files, by path or by a short key; most keys are "
              "expanded in the opening tag of their section or in the glossary below, and \"" + DR + "\" is one released "
              "file that records the authors' design and reporting decisions. "
              "Paths are relative to the root of the released project files; inside S6, a path without a top-level folder is "
              "relative to `60_RESULTS/x3_explore_v01/`.")),
    dict(id="E05", item=1, cat="front matter: draft-assembly provenance", ids_removed=True,
         old=("**Sources.** This file merges `20_DESIGN/SUPPLEMENT_v06a.md` (cce7dff9…; S1–S7) and `20_DESIGN/SUPPLEMENT_v06b_add.md` "
              "(0fcf5aea…; S4.1 and S8–S10), and adds the results of X3 amendments A3 and A4 (S6.12–S6.21); the merge and every edit "
              "are logged in `20_DESIGN/SUPPLEMENT_v06c_MERGE_LOG_v01.md`. The underlying sources are `20_DESIGN/MANUSCRIPT_DRAFT_v05.md` "
              "(82dca45e…), body Sections V-C to V-F and Appendices B, C, E and F; the corrections of `20_DESIGN/V06_INTEGRATION_NOTES_v01.md`, "
              "`20_DESIGN/V06_FIXES_FROM_V05_TRACE_v01.md` and `20_DESIGN/ms_v06_parts/E_prefreeze_v01.md` §E.7; the parts "
              "`20_DESIGN/ms_v06_parts/A_proofs_v02.md`, `B_planner_v02.md`, `B_stack_v02.md` and `E_prefreeze_v02.md`; the X3 result files "
              "in `60_RESULTS/x3_explore_v01/` and the X3 reports in `70_TESTS/X3_INTEGRITY_v01/`."),
         new=("**Sources.** Source tags name the records behind the statements they follow. The X3 result files are in "
              "`60_RESULTS/x3_explore_v01/` and the X3 integrity reports in `70_TESTS/X3_INTEGRITY_v01/`.")),
    # ---- item 4: glossary of study codes ---------------------------------------------
    dict(id="E06", item=4, cat="glossary of study codes (new table)",
         old="\n## Contents\n",
         new="\n" + GLOSSARY + "\n## Contents\n"),
    # ---- item 2: five amendments -----------------------------------------------------
    dict(id="E07", item=2, cat="amendments A1–A5",
         old="- S6. Post-registration exploratory analyses (X3): full results (S6.12–S6.21: amendments A3 and A4, added after review)",
         new="- S6. Post-registration exploratory analyses (X3): full results (S6.12–S6.22: amendments A3, A4 and A5, added after review)"),
    # ---- item 1: draft-manuscript source tag ----------------------------------------
    dict(id="E08", item=1, cat="draft-manuscript source tag", ids_removed=True,
         old="**Seeds** `[MANUSCRIPT_DRAFT_v05, App. D]`: E1 folds",
         new="**Seeds**: E1 folds"),
    # ---- stale main-text cross-references (Box 1 and Appendix D no longer exist) ------
    dict(id="E09", item=1, cat="stale main-text cross-reference",
         old="The registered rule (Section V-D, Box 1) plants",
         new="The registered rule (Section V-D3) plants"),
    # ---- item 4: S4.0 decision record and internal review ----------------------------
    dict(id="E10", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="`[90_DECISIONS/D16_DELEGATED_CHOICES_v56.md, Choice 75(d); 90_DECISIONS/D16_DELEGATED_CHOICES_v57.md, Choice 76; 20_DESIGN/V06_STRUCTURE_PLAN_v01.md",
         new="`[" + DR + "; 20_DESIGN/V06_STRUCTURE_PLAN_v01.md"),
    dict(id="E11", item=4, cat="internal review wording",
         old="An internal referee read found that",
         new="An internal review found that"),
    dict(id="E12", item=4, cat="internal review wording",
         old="The same read asked that",
         new="The same review asked that"),
    dict(id="E13", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="recorded as Choice 75 (D16 v56) and kept, with the claim it states, in Choice 76 (D16 v57).",
         new="recorded, and kept with the claim it states, in " + DR + "."),
    dict(id="E14", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="`[D16 Choice 49c]`", new="`[" + DR + "]`"),
    dict(id="E15", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="`[D16 Choice 54c]`", new="`[" + DR + "]`"),
    # ---- S5 ---------------------------------------------------------------------------
    dict(id="E16", item="4, 7", cat="decision record (D16/Choice)", ids_removed=True,
         old="; D16 Choices 61–69; E_prefreeze_v01 §E.7]`",
         new="; " + DR + "; E_prefreeze_v01 = 20_DESIGN/ms_v06_parts/E_prefreeze_v01.md, §E.7]`"),
    dict(id="E17", item=1, cat="stale main-text cross-reference",
         old="Appendix D of the main text summarizes it.",
         new="Section VI-D of the main text summarizes it."),
    dict(id="E18", item=4, cat="role wording",
         old="Whether the researcher saw any pre-freeze metric",
         new="Whether the supervising author saw any pre-freeze metric"),
    dict(id="E19", item=1, cat="stale main-text cross-reference",
         old="Main-text Section V-D and Box 1 give the summary.",
         new="Main-text Section V-D gives the summary."),
    dict(id="E20", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="; D16 Choices 61, 66]`", new="; " + DR + "]`"),
    # ---- S6 ---------------------------------------------------------------------------
    dict(id="E21", item=2, cat="amendments A1–A5",
         old="A4 = 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md, ab19dd66…; outputs",
         new="A4 = 20_DESIGN/X3_PLAN_AMENDMENT_A4_v01.md, ab19dd66…; A5 = 20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md, 25f3bb65…; outputs"),
    dict(id="E22", item=2, cat="amendments A1–A5",
         old="The X3 plan and its amendments A1–A4 were hash-locked",
         new="The X3 plan and its five amendments A1–A5 were hash-locked"),
    dict(id="E23", item=2, cat="amendments A1–A5",
         old="The results of amendments A3 and A4 (S6.12–S6.21) carry the label \"added after review (amendment A3)\" or \"(amendment A4)\";",
         new="The results of amendments A3, A4 and A5 (S6.12–S6.22) carry the label \"added after review (amendment A3)\", \"(amendment A4)\" or \"(amendment A5)\";"),
    dict(id="E24", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="existed (D16 v55 Choice 74). Each analysis answers a concern raised in an internal referee read of an earlier version",
         new="existed (as recorded in " + DR + "). Each analysis answers a concern raised in an internal review of an earlier version"),
    dict(id="E25", item="2, 4", cat="amendments A1–A5",
         old="Amendments A3 (15:09 EST) and A4 (15:11 EST), written after a second internal referee read, are described in S6.12.",
         new="Amendments A3 (15:09 EST) and A4 (15:11 EST), written after a second internal review, are described in S6.12, and amendment A5 (18:21 EST), written after a third internal review, in S6.22."),
    dict(id="E26", item=3, cat="S6.3 label",
         old="### S6.3 (b) The screen on partitions no method used (plan §2(b))",
         new="### S6.3 (b) The screen on partitions no method stratifies on directly (plan §2(b))"),
    dict(id="E27", item=3, cat="S6.3 label",
         old="P0, distance to the ego, is a partition M\\*'s strata use and is reported for completeness.",
         new=("P0, distance to the ego, is a partition M\\*'s strata use and is reported for completeness. No method stratifies on "
              "P1–P7 directly, but track speed (P1) and track age (P3) are coarse functions of the variables that define M\\*'s "
              "\"static\" and \"new\" course-change states (S6.22).")),
    dict(id="E28", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="; 90_DECISIONS/D16_DELEGATED_CHOICES_v57.md, Choice 76]`", new="; " + DR + "]`"),
    dict(id="E29", item=4, cat="internal review wording",
         old="A second internal referee read of an earlier version",
         new="A second internal review of an earlier version"),
    dict(id="E30", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="`[D16 v57 Choice 76(a)]`", new="`[" + DR + "]`"),
    dict(id="E31", item=4, cat="internal review wording", ids_removed=True,
         old=("was written after the referee read of manuscript v06c and before any cross-fitted quantity below was computed. "
              "That referee had re-read A4(1)'s in-sample curve table without P1 and P3, and the lead had read that report."),
         new=("was written after a third internal review of an earlier version of the manuscript and before any cross-fitted "
              "quantity below was computed. The reviewer had re-read A4(1)'s in-sample curve table without P1 and P3, and the "
              "analyst had read that report.")),
    dict(id="E32", item=7, cat="paths",
         old="Runs: runs/a4n_<t> and core_<t> (no new run).",
         new="Runs: `a4n_<t>` and `core_<t>` in `runs/` (no new run)."),
    dict(id="E33", item=7, cat="paths",
         old="Every in-sample grid point: x3_a5_points_v01.csv (",
         new="Every in-sample grid point: `a5_review/x3_a5_points_v01.csv` ("),
    # ---- S9 ---------------------------------------------------------------------------
    dict(id="E34", item=5, cat="algorithm/table numbering",
         old="Appendix B of the main text summarizes the planner.",
         new="Appendix B of the main text summarizes the planner (Table X and Algorithm 2)."),
    dict(id="E35", item=5, cat="algorithm/table numbering",
         old="### S9.13 Algorithm B1 (one decision; every line checked against `k8_sim_v04.py`)",
         new="### S9.13 Algorithm 2 (main-text Appendix B; one decision; every line checked against `k8_sim_v04.py`)"),
    dict(id="E36", item=5, cat="algorithm/table numbering", regex=True,
         old=r"Algorithm B1  (plan_step\(arm, k, s, v\): one decision)( +)\[590–663\]",
         new=r"Algorithm 2  \1\2 [590–663]"),
    dict(id="E37", item=7, cat="paths",
         old="paths are relative to the workspace root.",
         new="paths are relative to the project root."),
    dict(id="E38", item=4, cat="role wording",
         old="with velocity, \"from the researcher's archive\" [",
         new="with velocity, from the supervising author's archive ["),
    dict(id="E39", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="[C1 plan v07m §6.4; D16 Choices 19, 37]",
         new="[C1 plan v07m §6.4; " + DR + "]"),
    # ---- S10 --------------------------------------------------------------------------
    dict(id="E40", item=1, cat="stale main-text cross-reference",
         old="Appendix D of the main text summarizes this section.",
         new="Section VI-D of the main text summarizes this section."),
    dict(id="E41", item=7, cat="paths",
         old="**Sources** (paths relative to the workspace):",
         new="**Sources** (paths relative to the project root):"),
    dict(id="E42", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="| D16 | `90_DECISIONS/D16_DELEGATED_CHOICES_v55.md`, Choices 13, 14, 15–18, 44d, 46, 61–66 |",
         new="| DR | The authors' decision record (one released file) |"),
    dict(id="E43", item=4, cat="decision record (D16/Choice)", ids_removed=True,
         old="but never its position (D16 Choice 13).", new="but never its position (DR)."),
    dict(id="E44", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="PORT3 §12–§13; D16 Choice 13 |", new="PORT3 §12–§13; DR |"),
    dict(id="E45", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="PLAN §1.3, §10 items 2–3; D16 Choices 15–18, 44d |", new="PLAN §1.3, §10 items 2–3; DR |"),
    dict(id="E46", item=4, cat="decision record (D16/Choice); role wording", ids_removed=True, table=True,
         old="**Text lock** (the researcher's OSF upload of v07m DRAFT, 3e303eee…) | | | D16 Choices 61, 62(a) |",
         new="**Text lock** (the supervising author's OSF upload of v07m DRAFT, 3e303eee…) | | | DR |"),
    dict(id="E47", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="FTR §1; D16 Choices 62(b), 64; PORT4 §6 |", new="FTR §1; DR; PORT4 §6 |"),
    dict(id="E48", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="| D16 Choice 64; PLAN §1.5; PORT3 §12.2 |", new="| DR; PLAN §1.5; PORT3 §12.2 |"),
    dict(id="E49", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="PLAN §1.6, §7; D16 Choices 62(e), 64 |", new="PLAN §1.6, §7; DR |"),
    dict(id="E50", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="| D16 Choices 62(d), 64(c) |", new="| DR |"),
    dict(id="E51", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="PLAN §6.3 (S21); D16 Choice 64(b) |", new="PLAN §6.3 (S21); DR |"),
    dict(id="E52", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="| PROV; D16 Choice 65; FTR §6.4 |", new="| PROV; DR; FTR §6.4 |"),
    dict(id="E53", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="| D16 Choice 66(a); PLAN §0 (", new="| DR; PLAN §0 ("),
    dict(id="E54", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="FTR §1, §5; D16 Choices 62(b), 64(f) |", new="FTR §1, §5; DR |"),
    dict(id="E55", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="TRK3, outcome statement; D16 Choice 46(a) |", new="TRK3, outcome statement; DR |"),
    dict(id="E56", item=4, cat="decision record (D16/Choice)", ids_removed=True, table=True,
         old="| A read-only code-review run (D16 Choice 63) | Source code only | FTR §1 |",
         new="| A read-only code-review run | Source code only | FTR §1; DR |"),
    dict(id="E57", item=4, cat="role wording", table=True,
         old=("| **The researcher** | \"Has not been sent any value\" of the Rule-0 metrics. D18 (counts only) was written "
              "\"for the researcher's decision\", and the researcher chose option A on 2 Nov. Whether the researcher saw"),
         new=("| **The supervising author** | \"Has not been sent any value\" of the Rule-0 metrics. D18 (counts only) was written "
              "for the supervising author's decision, and the supervising author chose option A on 2 Nov. Whether the supervising author saw")),
]


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def apply_edits(text, edits):
    """Apply the edits in order; return (new_text, records). Stops on any count mismatch."""
    records = []
    for e in edits:
        n_expected = e.get("n", 1)
        if e.get("regex"):
            rx = re.compile(e["old"])
            matches = list(rx.finditer(text))
            if len(matches) != n_expected:
                sys.exit(f"{e['id']}: expected {n_expected} regex match(es), found {len(matches)}")
            apps = []
            for m in matches:
                apps.append(dict(line_in_current=line_of(text, m.start()), old_actual=m.group(0),
                                 new_actual=m.expand(e["new"])))
            text = rx.sub(e["new"], text)
        else:
            cnt = text.count(e["old"])
            if cnt != n_expected:
                sys.exit(f"{e['id']}: expected {n_expected} match(es), found {cnt}: {e['old'][:80]!r}")
            apps = []
            start = 0
            for _ in range(cnt):
                p = text.find(e["old"], start)
                apps.append(dict(line_in_current=line_of(text, p), old_actual=e["old"], new_actual=e["new"]))
                start = p + len(e["old"])
            text = text.replace(e["old"], e["new"])
        rec = {k: v for k, v in e.items() if k not in ("old", "new")}
        rec["applications"] = apps
        records.append(rec)
    return text, records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--edits-json", default=EDITS_JSON)
    args = ap.parse_args()
    for p in (args.out, args.edits_json):
        if os.path.exists(p):
            sys.exit(f"refusing to overwrite existing file: {p}")
    raw = open(IN, "rb").read()
    in_sha = sha256_bytes(raw)
    if not in_sha.startswith(IN_SHA_PREFIX):
        sys.exit(f"input hash {in_sha} does not start with {IN_SHA_PREFIX}")
    text = raw.decode("utf-8")
    out_text, records = apply_edits(text, EDITS)
    out_bytes = out_text.encode("utf-8")
    with open(args.out, "xb") as f:
        f.write(out_bytes)
    meta = dict(input=os.path.relpath(IN, W).replace("\\", "/"), input_sha256=in_sha,
                output=os.path.relpath(args.out, W).replace("\\", "/") if args.out.startswith(W) else os.path.basename(args.out),
                output_sha256=sha256_bytes(out_bytes), n_edits=len(records),
                n_applications=sum(len(r["applications"]) for r in records), edits=records)
    with open(args.edits_json, "x", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("input ", in_sha)
    print("output", meta["output_sha256"], args.out)
    print("edits", meta["n_edits"], "applications", meta["n_applications"])


if __name__ == "__main__":
    main()
