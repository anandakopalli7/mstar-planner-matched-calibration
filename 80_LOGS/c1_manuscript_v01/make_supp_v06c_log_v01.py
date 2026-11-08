# -*- coding: utf-8 -*-
"""make_supp_v06c_log_v01.py -- write 20_DESIGN/SUPPLEMENT_v06c_MERGE_LOG_v01.md (new file only).

Reads the edit manifest written by make_supp_v06c_v01.py, the saved output of check_supp_v06c_v01.py and the
hashes of every file involved. The time stamp is the machine clock at the moment of writing.
"""
import datetime
import hashlib
import json
import os
import re

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
L = os.path.join(W, "80_LOGS", "c1_manuscript_v01")
OUT = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06c_MERGE_LOG_v01.md")
SUPP = os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06c.md")
MAN = os.path.join(L, "supp_v06c_edits_v01.json")
CHK_OUT = os.path.join(L, "check_supp_v06c_v01_output.txt")
R = os.path.join(W, "60_RESULTS", "x3_explore_v01")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rel(p):
    return os.path.relpath(p, W).replace("\\", "/")


if os.path.exists(OUT):
    raise SystemExit("refusing to overwrite " + OUT)
man = json.load(open(MAN, encoding="utf-8"))
chk = open(CHK_OUT, encoding="utf-8").read()
supp = open(SUPP, encoding="utf-8").read()
now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") + " EST"

files = [SUPP, MAN, CHK_OUT,
         os.path.join(L, "make_supp_v06c_v01.py"), os.path.join(L, "check_supp_v06c_v01.py"),
         os.path.join(L, "make_supp_v06c_log_v01.py"),
         os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06a.md"), os.path.join(W, "20_DESIGN", "SUPPLEMENT_v06b_add.md"),
         os.path.join(W, "20_DESIGN", "X3_PLAN_AMENDMENT_A3_v01.md"), os.path.join(W, "20_DESIGN", "X3_PLAN_AMENDMENT_A4_v01.md"),
         os.path.join(W, "20_DESIGN", "ABSTRACT_FILLED_r1_v01.md"), os.path.join(W, "70_TESTS", "V06_REFEREE_REVIEW_v01.md")]
RES = ["a3_review/x3_a3_i_infeasible_cost_v01.md", "a3_review/x3_a3_ii_iv_partitions_v01.md",
       "a3_review/x3_a3_iii_own_items_v01.md", "a3_review/x3_a3_sweep_at_Mstar_V2_v01.md",
       "a4_review/x3_a4_1_neutral_v01.md", "a4_review/x3_a4_2_loop_v01.md",
       "a4_review/x3_a4_3_ego_footprint_v01.md", "a1_heading/x3_a4_heading_v01.md",
       "a4_review/x3_a4_5_ab3dmot_matched_only_v01.md"]
files += [os.path.join(R, *r.split("/")) for r in RES]

o = []
a = o.append
a("# SUPPLEMENT_v06c merge log (v01)")
a("")
a("Written %s by `80_LOGS/c1_manuscript_v01/make_supp_v06c_log_v01.py`. Paths are relative to the workspace." % now)
a("")
a("**Output.** `20_DESIGN/SUPPLEMENT_v06c.md`, SHA-256 %s, %d words (Python whitespace split; `wc -w` counts a few more), %d lines, sections S1–S10 with S4.1 inside S4 and the amendment A3/A4 results as S6.12–S6.21." % (sha(SUPP), len(supp.split()), len(supp.split("\n"))))
a("")
a("**How it was made.** `make_supp_v06c_v01.py` reads the two inputs and the nine result files, applies the %d logged edits below (each must match exactly once in its source block, or the script stops), places S4.1, inserts S6.12–S6.21 and appends S8–S10. It wrote the supplement and the edit manifest `supp_v06c_edits_v01.json` once, as new files. `check_supp_v06c_v01.py` then ran on the final file; its output is pasted in section 7 and saved as `check_supp_v06c_v01_output.txt`. Nothing under `50_CODE` was run or imported, and no existing file was edited." % len(man["edits"]))
a("")
a("## 1. Files and hashes")
a("")
a("| File | SHA-256 |")
a("|---|---|")
for p in files:
    a("| `%s` | %s |" % (rel(p), sha(p)))
a("")
a("## 2. What came from where")
a("")
a("| Part of SUPPLEMENT_v06c.md | Source | Notes |")
a("|---|---|---|")
rows = [
    ("Title, preface, Sources, Contents", "SUPPLEMENT_v06a.md l. 1–15", "edited: A01–A04"),
    ("(removed) v05 label map and section map", "SUPPLEMENT_v06a.md l. 17–38", "A05: revision history"),
    ("S1, S2, S3", "SUPPLEMENT_v06a.md l. 41–350", "cross-references and captions edited (A06–A24)"),
    ("S4: S4.0 to S4(i)", "SUPPLEMENT_v06a.md l. 352–655", "A25–A46"),
    ("S4.1 Secondary claims in full", "SUPPLEMENT_v06b_add.md l. 6–19", "placed at the end of S4, before 'What the verdict establishes', as its merge note (l. 2) asks; B01a, B01b, B01"),
    ("S4 'What the verdict establishes'", "SUPPLEMENT_v06a.md l. 656–661", "unchanged"),
    ("S5", "SUPPLEMENT_v06a.md l. 665–869", "A47–A62"),
    ("S6 heading, status paragraph, S6.0–S6.11", "SUPPLEMENT_v06a.md l. 872–1238", "A63–A81; the status paragraph is A64"),
    ("S6.12–S6.21 (amendments A3 and A4)", "new text; tables and verbatim lines from the nine result files of section 4", "S6-Tables 16–36"),
    ("S7", "SUPPLEMENT_v06a.md l. 1241–1243", "unchanged"),
    ("S8, S9, S10", "SUPPLEMENT_v06b_add.md l. 23–1057", "B02–B12"),
    ("(removed) merge-instruction comments", "SUPPLEMENT_v06b_add.md l. 1–4", "B00: notes to the editor, applied through the edits"),
]
for r in rows:
    a("| %s | %s | %s |" % r)
a("")
a("## 3. Every edit, old → new")
a("")
a("Each entry gives the edit id, the source file, the section it falls in (as in the source), the reason, and the full old and new text. An empty new text is a removal.")
a("")
for e in man["edits"]:
    a("### %s — %s" % (e["id"], e["source"]))
    a("")
    a("- **Section:** %s" % (e["section"] or "(file head)"))
    a("- **Why:** %s" % e["why"])
    a("- **Old:**")
    a("")
    a("````text")
    a(e["old"].rstrip("\n"))
    a("````")
    a("")
    a("- **New:**%s" % (" (removed)" if not e["new"] else ""))
    if e["new"]:
        a("")
        a("````text")
        a(e["new"].rstrip("\n"))
        a("````")
    a("")
a("## 4. New text: amendments A3 and A4 (S6.12–S6.21)")
a("")
a("Every table below is copied from its result file row by row (line terminators CRLF → LF). In the three A3 (ii) tables a bar inside a cell (`[0.5,3)|long`) is escaped as `\\|` so that the table typesets; check (c) shows this is the only difference (4 rows). Each subsection carries the result file's stamp line and its \"added after review (amendment A3/A4)\" label; S6.12 states the status (self-recorded hash locks after the verdict and after reading the registered outputs; not a registration; no family-wise control).")
a("")
a("| Subsection | Source (60_RESULTS/x3_explore_v01/) | S6-Tables | Source table (heading in the result file) | Verbatim lines |")
a("|---|---|---|---|---|")
newmap = [
    ("S6.12 status of A3 and A4", "X3_PLAN_AMENDMENT_A3_v01.md (009a0aad…), X3_PLAN_AMENDMENT_A4_v01.md (ab19dd66…); file times; D16 v57 Choice 76; a4_review/x3_a4_chain_part1_status_v01.json", "–", "–", "–"),
    ("S6.13 A3 (i) cost of infeasibility", "a3_review/x3_a3_i_infeasible_cost_v01.md", "16, 17", "## T1 (50 arms), ## T3 (50 arms)", "stamp"),
    ("S6.14 A3 (ii)/(iv) partitions, multiplicity", "a3_review/x3_a3_ii_iv_partitions_v01.md", "18–23", "T1 (ii), T1 (iv), T3 (ii), T3 (iv), TAB (ii), TAB (iv)", "stamp"),
    ("S6.15 A3 (iii) own calibration items", "a3_review/x3_a3_iii_own_items_v01.md", "–", "–", "stamp; 8 result bullets (T1, T3)"),
    ("S6.16 B0 sweep at M*'s V2 (added)", "a3_review/x3_a3_sweep_at_Mstar_V2_v01.md", "–", "–", "stamp; 2 bullets (T1 0.2755, T3 0.4403)"),
    ("S6.17 A4 (1) neutral screen", "a4_review/x3_a4_1_neutral_v01.md", "24–27", "## T1 per family, every point; ## T3 per family, every point", "stamp; 6 re-read bullets of (a) on the registered screen"),
    ("S6.18 A4 (2) loop mode", "a4_review/x3_a4_2_loop_v01.md", "28–31", "## T1 arms, M* minus arm; ## T3 arms, M* minus arm", "stamp"),
    ("S6.19 A4 (3) ego footprint", "a4_review/x3_a4_3_ego_footprint_v01.md", "32, 33", "## T1, ## T3", "stamp"),
    ("S6.20 A4 (4) heading error", "a1_heading/x3_a4_heading_v01.md", "34, 35", "## Estimate-oriented, ## Truth-oriented", "stamp; label line; reuse check; 6 method notes; integrity line"),
    ("S6.21 A4 (5) AB3DMOT matched only", "a4_review/x3_a4_5_ab3dmot_matched_only_v01.md", "36", "the one table", "stamp; the fixed reading"),
]
for r in newmap:
    a("| %s | %s | %s | %s | %s |" % r)
a("")
a("Also added, as edits (section 3): S6 status paragraph (A64); A3/A4 pointers in S6.0 (A66), S6.3 (A70), S6.7 (A75, A76), S6.9 (A79), S6.10 (A81), S4(f) (A42, A44), S9.5 (B09) and S9.10 (B10); the A4 reading of S6-Table 2 (A69).")
a("")
a("## 5. S-numbers cited by the body (ms_v06_parts/*_v04.md) and the headings they resolve to")
a("")
a("From check (a). References inside HTML comments and the setting labels (S1)–(S3) of Section III-A are listed by the check as skipped.")
a("")
a("| Cited | Resolves to | Cited in |")
a("|---|---|---|")
for line in chk.split("\n"):
    m = re.match(r"^  (S\S+(?: [A-Z.0-9]+)?)\s+-> (.*?)\s+\[cited in: (.*)\]$", line)
    if m:
        a("| %s | %s | %s |" % (m.group(1), m.group(2).replace("|", "\\|"), m.group(3)))
a("")
a("Content probes: for each cited section the check also confirms that the content the body attributes to it is there (for example S9.11: 534,846 / 356,260 / 537,924; S8.2: 1.25δ = 0.0625; S8-Remark A.5: 2/31 = 0.0645; S9.15: the unrecorded nuScenes checkpoint and the 2 CBGS epochs set by the compute cap; S4: the frames-v03 abstract quote), and that every S8 label in the main text's Appendix A.4 table sits in the S8 subsection that table names.")
a("")
a("## 6. The consistency fixes asked for, and what was found")
a("")
fixes = [
    ("S4(d) 'Every comparator infeasible in fewer than half of decisions was shown above δ'", "Qualified: 'among the arms of record'; the exploratory B8 passes at 0.282 / 0.507 (A35). The same scope was added to S6.7's 'every valid arm other than M*' sentence (A75)."),
    ("RETUNED-HK1 '(none)' on T1 as well as T3", "S4(f) (A43) and S6.2 (A68) now say that no scale qualified in any fold on either tracker and that ×8 was substituted as specified; S6-Table 2 rows are unchanged (their 'Folds where none qualifies' column already reads 0, 1, 2, 3, 4 on both trackers) and a note reads the table with A4's reporting rule (A69)."),
    ("'single-knob' → 'single-level'", "No 'single-knob' occurs in either input. S8 uses 'single knobs' (Proposition 5's title and its label-map row) for the theory's scalar multiplier and covariance inflation, not for the comparator families; it was left unchanged, as is the main text's own 'the price of one knob' (A_proofs_v04.md, A.4)."),
    ("T3 sweep reading 0.42 → 0.44", "No 0.42 sweep reading occurs in either input. The A3 values 0.2755 (T1) and 0.4403 (T3) were added to S6.7 (A76) and in S6.16; every remaining '0.42' in the file is another quantity (listed by check (e))."),
    ("False-positive tracks as the plausible cause of AB3DMOT's infeasibility", "No such statement occurs in either input. S6.9 now reports A4(5): removing unmatched tracks lowers M*'s infeasible rate only from 0.891 to 0.757, so the explanation is dropped (A79); S4(f) points to S6.9 and S6.21 (A42); S6.21 gives the table and the fixed reading."),
    ("'operability' → 'backs off its designed margin less often'", "A21 (S2.2), A29 and A31 (S4(b)), A59 and A61 (S5.7), A67 (S6.2 heading). One occurrence is kept on purpose: S4.0's 'the operability clause', which names the clause of the pre-fixed abstract that the referee read found misleading."),
    ("Internal, not independent, referee read; the re-derivation is not independent", "S4.0 (A26), S6.0 (A65), S6.12; S4(g) heading and status sentence (A45); S5.8 (A62)."),
    ("Tool or agent names, pod IDs", "None in either input or in the result files (check (d): 0 for every pattern). 'The lead: the analysis session that ran C1' became a role (A48). File paths that contain 'pod' (`50_CODE/owndet/pod/`, `pod_owndet_*`) are provenance file names, not machine IDs, and were kept."),
    ("Revision-history notes", "Removed: the v05 label and section maps (A05), '(v05 Table …)' in 12 captions, 'previous draft' sentences (A16, A18, A47, A49, A55), '(the previous Appendix A/B/D)' and the old-label maps of S8–S10 (B02–B07, B11, B12), 'moved from Section V-D' (B01a), internal referee labels in S6 headings (A67, A69, A71–A74, A77, A78, A80). Kept as provenance: file names and hashes, including MANUSCRIPT_DRAFT_v05.md and V05_REFEREE_REVIEW_v01.md in source tags."),
    ("Cross-references for the merged structure", "Applied the merge notes of SUPPLEMENT_v06b_add.md l. 3–4: Appendix A → S8 / S8-labels (A06–A10, A22, A30, A61), main-text Propositions 3–4 (A08, A58), Appendix D → S10 (A47–A60), Appendix B → S9 (A19, A20), the method-stage rule in H6a/H6b/H7 (A37–A40), S4(g) renamed (A45). Main-text table numbers follow the v04 body parts: Table VII (registered screen; B08), Table VIII (per arm; A33, A34), Table IX (claims; B01)."),
    ("S4.0 frames-v03 abstract", "Current: identical to ABSTRACT_FILLED_r1_v01.md line 5 except the markdown escape of M* (`M\\*`) in 3 places (check (e)). The reason for its replacement now cites D16 v56 Choice 75 and D16 v57 Choice 76 and says 'internal referee read' (A26)."),
]
a("| Asked for | Done |")
a("|---|---|")
for f in fixes:
    a("| %s | %s |" % (f[0].replace("|", "\\|"), f[1].replace("|", "\\|")))
a("")
a("**Inconsistencies between supplement and body noticed but not fixed** (for the lead):")
a("")
for t in [
    "Body V-D1 (05D_registered_v04.md l. 7) says 'the frozen plan is Supplement S7', but S7 gives only the plan's hash, OSF link and structure and says it 'is not reproduced here'.",
    "Figure numbers: S4(c) cites 'main-text Fig. 2' for M*'s cell bounds and S4(d) 'main-text Fig. 3' for the infeasible rates, while the body cites the cell bounds as 'Fig. 9' (05D l. 43) and no body part cites a Fig. 2 or Fig. 3. Left as in v06a until the body's figure numbers are fixed.",
    "Main-text tables in the v04 parts are numbered I, II and VII–XIV (no III–VI). The supplement now cites VII, VIII, IX and XI; if tables are renumbered at assembly, S4(d), S4.1, S9.11 and the S6-Table 2 note must follow.",
    "S4.0's rule list (D16 v56 Choice 75) says the replacement abstract 'removes no registered result' and 'names the proxy population'. The v06c abstract (00_title_abstract_v04.md) no longer states H1's Form B clause (M* less often infeasible than every comparator not shown above δ) and does not use the word 'proxy'. The lead should confirm the list still describes the v06c abstract.",
    "05C_development_v04.md's HTML comment says the full K8 table goes to 'Supplement S4/S5'; it is S2-Table 1 in S2.2 (comment only).",
    "03_formal_motivation_v04.md and A_proofs_v04.md label the setting assumptions (S1)–(S3), the same strings as Supplement S1–S3; a reader may confuse them.",
    "A_proofs_v04.md A.4 says 'Supplement S8 keeps the previous labels' (revision-history wording in the body).",
]:
    a("- " + t)
a("")
a("## 7. Output of check_supp_v06c_v01.py on the final file")
a("")
a("````text")
a(chk.rstrip("\n"))
a("````")
a("")
with open(OUT, "x", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(o))
print("wrote", OUT, sha(OUT))
