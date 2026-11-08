"""make_supp_v06e_log_v01.py -- write 20_DESIGN/SUPPLEMENT_v06e_EDIT_LOG_v01.md.

Reads the edit record (supp_v06e_edits_v01.json), the input and output supplements and the
checker's output (check_supp_v06e_v01_output.txt); the time stamp is passed in from `date`.
Never overwrites an existing file.
"""
import argparse
import collections
import hashlib
import json
import os
import re
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
L = os.path.join(W, "80_LOGS", "c1_manuscript_v01")
IN = os.path.join(D, "SUPPLEMENT_v06d_final.md")
OUT = os.path.join(D, "SUPPLEMENT_v06e.md")
LOG = os.path.join(D, "SUPPLEMENT_v06e_EDIT_LOG_v01.md")
EDITS = os.path.join(L, "supp_v06e_edits_v01.json")
REPORT = os.path.join(L, "check_supp_v06e_v01_output.txt")
SCRIPTS = ["make_supp_v06e_v01.py", "check_supp_v06e_v01.py", "make_supp_v06e_log_v01.py"]

TERMS = [("D16", r"D16"), ("Choice / Choices + number", r"Choices? \d"), ("the lead", r"\bthe lead\b"),
         ("the researcher", r"the researcher"), ("referee read", r"referee read"), ("v06c", r"v06c"),
         ("A1\u2013A4", "A1\u2013A4"), ("Algorithm B1", r"Algorithm B1"), ("Box 1", r"Box 1"),
         ("Appendix D (main text)", r"Appendix D\b"), ("MANUSCRIPT_DRAFT", r"MANUSCRIPT_DRAFT"),
         ("as in the main text", r"as in the main text"), ("no method used", r"no method used"),
         ("the supervising author", r"the supervising author"), ("the authors' decision record", r"the authors' decision record"),
         ("an internal review / internal review", r"internal review"), ("the analyst", r"\bthe analyst\b"),
         ("A1\u2013A5", "A1\u2013A5"), ("Algorithm 2", r"Algorithm 2\b"), ("S6.22", r"S6\.22")]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def diffpart(a, b, ctx=45, cap=260):
    i = 0
    while i < min(len(a), len(b)) and a[i] == b[i]:
        i += 1
    j = 0
    while j < min(len(a), len(b)) - i and a[len(a) - 1 - j] == b[len(b) - 1 - j]:
        j += 1
    s0 = max(0, i - ctx)
    pre = ("\u2026" if s0 > 0 else "") + a[s0:i]
    post = a[len(a) - j: len(a) - j + ctx] + ("\u2026" if j > ctx else "")

    def cut(s):
        return s if len(s) <= cap else s[: cap // 2] + " \u2026 " + s[-cap // 2:]
    return pre + "\u27e6" + cut(a[i:len(a) - j]) + "\u27e7" + post, pre + "\u27e6" + cut(b[i:len(b) - j]) + "\u27e7" + post


def cell(s):
    return s.replace("|", "\\|").replace("\n", "\u21b5")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True, help="output of `date`")
    ap.add_argument("--wc-in", required=True)
    ap.add_argument("--wc-out", required=True)
    a = ap.parse_args()
    if os.path.exists(LOG):
        sys.exit(f"refusing to overwrite {LOG}")
    ti = open(IN, encoding="utf-8").read()
    to = open(OUT, encoding="utf-8").read()
    E = json.load(open(EDITS, encoding="utf-8"))
    rep = open(REPORT, encoding="utf-8").read()
    o = []
    o.append("# SUPPLEMENT v06e: edit log (v01)")
    o.append("")
    o.append(f"**Written:** {a.date} (time stamp from `date`).")
    o.append("")
    o.append("**Task.** Turn `20_DESIGN/SUPPLEMENT_v06d_final.md` into a reviewer-facing supplement without changing any "
             "number, table value, result or claim, as asked by the internal review of v06d "
             "(`70_TESTS/V06D_REFEREE_REVIEW_v01.md`, new minor concerns 3 and 13). Every edit is an exact string "
             "replacement listed below; the checker replays them on the input and reproduces the output byte for byte.")
    o.append("")
    o.append("## 1. Files")
    o.append("")
    o.append("| File | SHA-256 | Note |")
    o.append("|---|---|---|")
    o.append(f"| `20_DESIGN/SUPPLEMENT_v06d_final.md` (input) | {sha(IN)} | {a.wc_in} words (`wc -w`), {ti.count(chr(10)) + 1} lines |")
    o.append(f"| `20_DESIGN/SUPPLEMENT_v06e.md` (output) | {sha(OUT)} | {a.wc_out} words (`wc -w`), {to.count(chr(10)) + 1} lines |")
    o.append(f"| `80_LOGS/c1_manuscript_v01/supp_v06e_edits_v01.json` | {sha(EDITS)} | edit record: {E['n_edits']} edits, {E['n_applications']} applications |")
    o.append(f"| `80_LOGS/c1_manuscript_v01/check_supp_v06e_v01_output.txt` | {sha(REPORT)} | checker output (pasted in Section 8) |")
    for s in SCRIPTS:
        p = os.path.join(L, s)
        o.append(f"| `80_LOGS/c1_manuscript_v01/{s}` | {sha(p)} | script |")
    o.append("")
    o.append("Nothing under `50_CODE` was run; no existing file was edited or overwritten.")
    o.append("")

    o.append("## 2. Edits by type")
    o.append("")
    cats = collections.OrderedDict()
    for e in E["edits"]:
        c = e["cat"].split(";")[0]
        cats.setdefault(c, []).append(e["id"])
    o.append("| Type | Edits | IDs |")
    o.append("|---|---|---|")
    for c, ids in cats.items():
        o.append(f"| {c} | {len(ids)} | {', '.join(ids)} |")
    o.append(f"| **Total** | **{len(E['edits'])}** | {E['n_applications']} applications, each matched exactly once |")
    o.append("")
    o.append("**Occurrences of the targeted wording, input and output:**")
    o.append("")
    o.append("| Wording | Input | Output |")
    o.append("|---|---|---|")
    for name, p in TERMS:
        o.append(f"| {name} | {len(re.findall(p, ti))} | {len(re.findall(p, to))} |")
    o.append("")
    o.append("By item of the brief: (1) front matter, draft versions and stale main-text references: E01–E05, E08, E09, "
             "E17, E19, E40; (2) five amendments A1–A5: E07, E21–E23, E25; (3) the S6.3 label: E26, E27; (4) decision "
             "references, roles, internal review and the glossary: E06, E10–E16, E18, E20, E24, E28–E31, E38, E39, "
             "E42–E57; (5) Algorithm 2 and Table X: E34–E36; (6) source tags: E04; (7) paths: E04, E16, E21, E32, E33, "
             "E37, E41.")
    o.append("")

    o.append("## 3. Every edit")
    o.append("")
    o.append("Input line numbers refer to `SUPPLEMENT_v06d_final.md`. Only the changed span is shown, in \u27e6 \u27e7, "
             "with some context; E05 and E06 are abbreviated in the middle.")
    o.append("")
    o.append("| ID | Item | Type | Input l. | Old | New |")
    o.append("|---|---|---|---|---|---|")
    for e in E["edits"]:
        for ap_ in e["applications"]:
            old, new = ap_["old_actual"], ap_["new_actual"]
            pos = ti.find(old)
            ln = ti.count("\n", 0, pos) + 1 + (1 if old.startswith("\n") else 0)
            da, db = diffpart(old, new)
            o.append(f"| {e['id']} | {e['item']} | {e['cat']} | {ln} | {cell(da)} | {cell(db)} |")
    o.append("")

    o.append("## 4. Table rows changed")
    o.append("")
    o.append("Of the input's 900 table rows, 885 are byte-identical in the output. The 15 changed rows are all in S10 and "
             "each changes only a source label: the decision-file key `D16` with its choice numbers becomes `DR` "
             "(\"the authors' decision record\", defined in the S10 key table, edit E42), and \"the researcher\" becomes "
             "\"the supervising author\". They are: input l. 3010 (E42, the key row itself), 3050 (E44), 3051 (E45), "
             "3057 (E46), 3058 (E47), 3059 (E48), 3060 (E49), 3061 (E50), 3062 (E51), 3063 (E52), 3065 (E53), "
             "3102 (E54), 3103 (E55), 3107 (E56; the choice number moved from the first to the source column as DR) "
             "and 3108 (E57). The new rows are the 18 rows of the glossary table (E06). The checker's Section C lists "
             "every changed row with its old and new span.")
    o.append("")

    o.append("## 5. Number tokens")
    o.append("")
    o.append("Every change in a number token's count equals the sum of the logged edits' changes (checker, Section D). "
             "The tokens removed are:")
    o.append("")
    o.append("- **decision and version identifiers** (edits marked \"ID removal\" in Section D): the decision file's number "
             "16 and its version numbers 55, 56 and 57, the choice numbers (13, 14, 15–18, 19, 37, 44d, 46, 49c, 54c, 61–69, "
             "74, 75, 76 and their sub-items), the draft numbers 05 and 06 in \"v05\" and \"v06c\", and the identifiers in the "
             "removed draft-assembly paragraph (E05: draft file names, their hash prefixes cce7dff9, 0fcf5aea and 82dca45e, "
             "and the draft section ranges S1–S7, S4.1, S8–S10, S6.12–S6.21, §E.7);")
    o.append("- **stale or superseded labels**: \"Box 1\" (E09, E19; the main text has no Box 1), \"B1\" in \"Algorithm B1\" "
             "(E35, E36), \"A4\" in \"A1–A4\" (E22) and \"S6.21\" in two range statements (E07, E23).")
    o.append("")
    o.append("The tokens added come only from new text: the glossary (E06), the A5 entries (E07, E21–E23, E25), the S6.3 "
             "sentence (E27), \"Section V-D3\" (E09), \"Algorithm 2\" (E34–E36), the key expansion of `E_prefreeze_v01` (E16) "
             "and the `a5_review/` folder (E33). Restricted to standalone numbers (checker, Section D2), the only changes "
             "are the choice numbers, \"1\" of \"Box 1\", \"2\" of \"Algorithm 2\" and \"18:21\" of A5's lock time; no "
             "result value changed. The line-level difference (Section D3) touches 49 of the input's 3,117 lines.")
    o.append("")

    o.append("## 6. Paths")
    o.append("")
    o.append("- The input had no drive letter, user folder, `Users` or `Downloads` (grep for `C:\\`, `Users`, the user-folder "
             "name and `Downloads`: 0 hits); neither has the output (checker, Sections F and H).")
    o.append("- **E04** front matter: \"paths are relative to the project workspace\" \u2192 \"relative to the root of the "
             "released project files\", adding the S6 rule that a path without a top-level folder is relative to "
             "`60_RESULTS/x3_explore_v01/` (as all S6 tags already were).")
    o.append("- **E37, E41** S9.15 and S10: \"relative to the workspace (root)\" \u2192 \"relative to the project root\".")
    o.append("- **E32** S6.22: `runs/a4n_<t> and core_<t>` (bare) \u2192 `` `a4n_<t>` and `core_<t>` in `runs/` `` (in backticks; "
             "the runs are file-name labels, for example `runs/decisions_a4n_t1.npz`).")
    o.append("- **E33** S6.22: bare `x3_a5_points_v01.csv` \u2192 `` `a5_review/x3_a5_points_v01.csv` `` (folder checked).")
    o.append("- **E16** S5 tag: the key `E_prefreeze_v01` is expanded to `20_DESIGN/ms_v06_parts/E_prefreeze_v01.md` (it was "
             "expanded only in the removed Sources paragraph).")
    o.append("- **E21** S6 tag: `20_DESIGN/X3_PLAN_AMENDMENT_A5_v01.md, 25f3bb65…` added beside A1–A4.")
    o.append("- **Removed** with the edits that removed them: the decision-file paths `90_DECISIONS/D16_…_v55/v56/v57.md` "
             "(E10, E28, E42) and the eleven draft-assembly paths of the old Sources paragraph (E05).")
    o.append("- **Left as they are:** 35 bare file names inside S9's bracketed `[file:line]` code references and S9.15's "
             "bracketed record references (for example `[116; k6_cache_v02.py:84]`). S9 defines that form, and they are "
             "file names, not paths; putting them in backticks would touch S9.14's table rows.")
    o.append("")

    o.append("## 7. Judgement calls, and what was not done")
    o.append("")
    o.append("- **Title.** The first line is now exactly the paper's title; the next paragraph opens with "
             "\"**Supplementary material**\".")
    o.append("- **Sources paragraph (E05).** It described how the draft supplement was merged from earlier drafts "
             "(file names, hashes, the draft main text v05); it is replaced by two sentences that keep the X3 result and "
             "report folders.")
    o.append("- **Seeds tag (E08).** The tag cited a draft of the main text (`MANUSCRIPT_DRAFT_v05, App. D`), which gives no "
             "further source; it was removed and the seeds are still stated.")
    o.append("- **Stale main-text references.** The main text no longer has Box 1 or Appendix D. \"Section V-D, Box 1\" "
             "\u2192 \"Section V-D3\" (where the main text states the planted-cell power rule); \"Main-text Section V-D and "
             "Box 1 give\" \u2192 \"Main-text Section V-D gives\"; \"Appendix D of the main text summarizes\" \u2192 "
             "\"Section VI-D of the main text summarizes\" (VI-D points to S10). The other main-text references "
             "(Sections III–VI with their subsections and V-D5/V-D6, Tables II–VI and X, Figs. 2–4, Propositions 1–5, "
             "Remark 1, Theorem 1, Algorithm 2, Appendices A and B) were checked against "
             "`20_DESIGN/MANUSCRIPT_DRAFT_v06d.md` and again against `20_DESIGN/MANUSCRIPT_DRAFT_v06e.md`, which appeared "
             "during this edit (19:27); both number them the same way, and every supplement section that v06e cites exists.")
    o.append("- **Table B1.** It does not occur in v06d_final. A pointer to main-text Table X and Algorithm 2 was added to "
             "S9's opening sentence (E34); S9.13's algorithm is line for line main-text Algorithm 2 with code references.")
    o.append("- **Decision references.** \"D16 v5x Choice N\" became \"the authors' decision record\" in prose and tags, and "
             "the key `DR` in S10, whose key table defines it; one of them (S6.0, E24) keeps it as \"as recorded in the "
             "authors' decision record\". Other decision and review files (D06–D18 except D16, R06–R21, E01) are kept "
             "as source tags and explained in the glossary.")
    o.append("- **Quotations.** Two quoted phrases contained \"the researcher\" (\"from the researcher's archive\", S9.15.1.1; "
             "\"for the researcher's decision\", S10.5). Both are now unquoted paraphrases with \"the supervising author\", "
             "so no quotation is altered.")
    o.append("- **Internal review.** \"Referee read\" became \"internal review\" (S4.0, S6.0, S6.12) and, for A5, \"a third "
             "internal review of an earlier version of the manuscript\" with \"the reviewer\" and \"the analyst\" (S5.0 "
             "defines the analyst). File names that contain `REFEREE_REVIEW` or a draft number "
             "(`70_TESTS/V05_REFEREE_REVIEW_v01.md`, `70_TESTS/V06_REFEREE_REVIEW_v01.md`, "
             "`20_DESIGN/V06_STRUCTURE_PLAN_v01.md`, `20_DESIGN/ms_v06_parts/`) were kept, because they name released "
             "files; plan versions (v07m) and tool versions (v01–v05) are not drafts of the manuscript.")
    o.append("- **Amendments.** S6's status paragraph, its tag, S6.0 and the contents line now cover A1–A5 and S6.22. "
             "S6.12's own sentences (\"S6.13–S6.21 \u2026 amendment A3 or A4\") describe A3 and A4 only and were left as "
             "they are; so was S6.12's account of the second review's question (\"a screen that no method's strata "
             "define\"), since S6.3 and S6.22 now carry the caveat.")
    o.append("- **Glossary.** A table \"Codes used in this supplement\" was added before the contents. It defines the study "
             "codes (T1–T3, X1, X2, the method stage with HM1–HM6 and E1/E2, K6, K8, D17, C1 with H1–H10 and Q1, X3 with "
             "A1–A5), the two uses of P-numbers (partitions in S6, pre-freeze computations in S5 and S10), the gates V0–V2, "
             "G0–G3, the review, decision and dossier codes, the authors' decision record and AV2. Short keys inside single "
             "tags (for example MDEC, MR-T1…MR-T3, X1R, K6R) are not expanded.")
    o.append("- **Not in scope and not done:** the other new minor concerns of the v06d review (1, 2, 4–12, 14–18) concern "
             "the main text or its figures; S6.22's ASCII forms (\"M* - composite\", \"--\") were left unchanged.")
    o.append("")
    o.append("## 8. Checker output (verbatim)")
    o.append("")
    o.append("Command: `python -I 80_LOGS/c1_manuscript_v01/check_supp_v06e_v01.py` (exit 0).")
    o.append("")
    o.append("```")
    o.append(rep.rstrip("\n"))
    o.append("```")
    o.append("")
    with open(LOG, "x", encoding="utf-8") as f:
        f.write("\n".join(o))
    print("log", sha(LOG))


if __name__ == "__main__":
    main()
