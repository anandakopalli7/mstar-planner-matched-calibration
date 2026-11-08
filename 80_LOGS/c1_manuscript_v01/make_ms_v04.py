#!/usr/bin/env python3
"""Assembles 20_DESIGN/MANUSCRIPT_DRAFT_v04.md from v03b (kept unchanged) and the parts in 20_DESIGN/ms_v04_parts/ (the lead, 7 Nov 2026).
v04 is the length pass asked for by the v03 referee review (M8): Sections I, IV-K, V-D, V-E, V-F and VI are rewritten shorter
(parts), and detail paragraphs of Sections III, IV-B, V-A, V-B and V-C are moved verbatim to the appendices, leaving pointers.
Related Work gains the verified references of 20_DESIGN/REF_CHECK_v03b.md. Every anchor is asserted to occur once.
Refuses an existing output. Usage: python -B make_ms_v04.py <out.md>
"""
import os
import sys

W = r"C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911"
D = os.path.join(W, "20_DESIGN")
P = os.path.join(D, "ms_v04_parts")
part = lambda n: open(os.path.join(P, n), encoding="utf-8").read().strip("\n")  # noqa: E731

HEADER = """# MANUSCRIPT_DRAFT_v04 — IEEE Access article for Programme A (7 Nov 2026; results of the Argoverse 2 confirmation pending)

**Status.** v04 supersedes v03b (`20_DESIGN/MANUSCRIPT_DRAFT_v03b.md`), which is kept, as are v03 and v02.
- **The length pass.** v04 is the length pass of the v03 referee review (M8):
  - Sections I, IV-K, V-D, V-E, V-F and VI are rewritten shorter;
  - detail paragraphs of Sections III, IV-B, V-A, V-B and V-C are moved word for word to Appendices A and B, with pointers left in place;
  - the Argoverse 2 protocol detail is the new Appendix E;
  - Related Work gains the references verified in `20_DESIGN/REF_CHECK_v03b.md`.
- **No number changes.** No number changes from v03b except where a moved paragraph now sits in an appendix.
- **Built mechanically.** v04 is assembled by `80_LOGS/c1_manuscript_v01/make_ms_v04.py` from v03b and `20_DESIGN/ms_v04_parts/`.
- **Written outcome-blind.** No C1 outcome was opened. V-F7, the abstract and the conclusion are filled after the decision of record exists, in the wording fixed by `20_DESIGN/C1_REPORTING_FRAMES_v01.md` (c46e301b…, D16 v50).
- **Still to come:**
  - the results;
  - the abstract (150–250 words) and conclusion;
  - stripping source tags and internal IDs;
  - US spelling;
  - a notation and population table;
  - the LaTeX build.

**Source-tag key.** As v03b.

---
"""


def main():
    out = sys.argv[1]
    assert not os.path.exists(out), "%s exists" % out
    s = open(os.path.join(D, "MANUSCRIPT_DRAFT_v03b.md"), encoding="utf-8").read()
    app_a, app_b = [], []

    def rep(a, b):
        nonlocal s
        assert s.count(a) == 1, (s.count(a), a[:90])
        s = s.replace(a, b)

    def span(start, end, inclusive_end=True):
        i = s.index(start)
        assert s.count(start) == 1, start[:80]
        j = s.index(end, i) + (len(end) if inclusive_end else 0)
        return s[i:j]

    def move_par(start, pointer, bucket):
        """Move the paragraph beginning with `start` (to the next blank line) into an appendix bucket."""
        par = span(start, "\n\n", inclusive_end=False)
        bucket.append(par)
        rep(par, pointer)

    # header
    i = s.index("\n---\n\n# Decision-Projected")
    s = HEADER + s[i + len("\n---\n"):]
    # I. Introduction (rewritten)
    rep(span("## I. Introduction", "\n---\n\n## II. Related Work", inclusive_end=False), part("01_intro.md") + "\n\n")
    # II. Related Work: verified additions
    rep("which could be layered on our strata `[P02 Relation to known results]`.",
        "which could be layered on our strata `[P02 Relation to known results]`. Training-conditional and high-probability variants "
        "[BianBarber2023; Bates2021; Angelopoulos2025LTT] bound the risk of one fitted rule, the quantity the registered test of "
        "Section V-F checks empirically; under distribution shift, coverage needs reweighting or degrades with the shift "
        "[Tibshirani2019; Barber2023]; and choosing which items to score after seeing the data calls for selective guarantees "
        "[JinCandes2023; Bao2024], which the relied-axis scoring of Section IV-K does not have.")
    rep("conformal regions around predicted trajectories drive MPC [Lindemann2023; Dixit2023; Cleaveland2024; Lindemann2025]",
        "conformal regions around predicted trajectories drive MPC [Lindemann2023; Dixit2023; Cleaveland2024; Lindemann2025; Tumu2023]")
    rep("Every nuPlan study we found uses ground-truth or noise-injected perception; we replay a real tracker's recorded covariance (Section V-D).",
        "Every nuPlan study we found uses ground-truth or noise-injected perception; we replay a real tracker's recorded covariance (Section V-D). "
        "Open-loop scores at logged states can disagree with closed-loop behaviour [Dauner2023; Li2024Ego], and our decision mode is of that "
        "kind; demonstrating safety statistically needs far more driving than any study here [KalraPaddock2016].")
    # III: verbatim moves to Appendix A
    move_par("Exact object-conditional coverage cannot be certified", "", app_a)
    move_par("**Remark 2 (orientation null).**",
             "Estimate-based toward-ego orientation inflates exceedance even for a calibrated tracker; Remark 2 (Appendix A) defines "
             "this orientation null, E⁰, which Section V-B uses.", app_a)
    move_par("**Remark 3 (Schur).**", "", app_a)
    # IV-B: the turning-share detail to Appendix B
    sent = span("Position noise reads as a course change at low speed", "validity does not depend on its meaning.")
    app_b.append("**Course-change shares (Section IV-B).** " + sent)
    rep(sent, "\"Turning\" is a state, not a manoeuvre label (its shares by speed are in Appendix B).")
    # IV-K (rewritten)
    rep(span("### K. The planner-matched variant M\\* (Sections V-D and V-F)", "\n\n---\n\n## V. Experiments", inclusive_end=False),
        part("04K_mstar.md"))
    # V-A: verbatim moves to Appendix B
    move_par("**Records, pairing and items.**",
             "**Records and pairing.** A *record* is one exported track at one keyframe. Tracks are matched to same-class annotations by "
             "Hungarian assignment within 2 m, so every analysis covers matched true positives only (counts in Appendix B).", app_b)
    move_par("**Pre-specification and checks.**",
             "**Pre-specification.** Each nuScenes stage was planned in a document whose SHA-256 was fixed, with code, inputs and "
             "environment listings, before its outcomes were computed. These hashes are self-recorded, so we call the stages "
             "*pre-specified*; only the Argoverse 2 test is *registered* (Section V-F1). Operating characteristics, reviews and "
             "re-derivations are in Appendix B.", app_b)
    move_par("**What was seen before, and what is in-sample.**",
             "**In-sample elements.** Val had been examined before X1 and T1's Q was tuned on it; the detector is in-sample on train; "
             "and one pre-freeze check previewed X2's decision (D06). Details are in Appendix B.", app_b)
    # V-B: Reading (4)-(7) to Appendix B
    tail = span(" (4) *Both lateral tails*", "verified all 65 frozen hashes `[E01 §6 / R06]`.")
    app_b.append("**Reading of X2, continued (Section V-B).**" + tail)
    rep(tail, " Items (4)–(7) (both lateral tails, concentration in turning cars, composition, robustness and reproduction) are in Appendix B.")
    # V-C: verbatim moves to Appendix B
    oc = span(" OC: a valid DP-SCRC fails HM1", "`[E01 §5.3, §7 item 3 / M-OC-T1, M-OC-T3]`")
    app_b.append("**Method-stage operating characteristics (Section V-C).**" + oc)
    rep(oc, " Operating characteristics are in Appendix B.")
    prop = span("*Properties of the inference.*", "`[R08 m7, m8]`. ")
    app_b.append("**Method-stage inference (Section V-C).** " + prop.strip())
    rep(prop, "*Properties of the inference* (Appendix B): E1 is pinned by construction for conformal methods, and the refit-CV is conservative. ")
    move_par("**E4, E5 and deviations.**",
             "**Horizons, sensitivities and deviations** (E4, E5; Appendix B). No val cell or pooled cell is flagged at 1, 2 or 4 s, "
             "and no deviation occurred after the freeze.", app_b)
    # V-D, V-E, V-F (rewritten)
    rep(span("### D. Planner study on nuScenes (development evidence, exploratory)", "### E. A learned predictor", inclusive_end=False),
        part("05D_planner.md") + "\n\n")
    rep(span("### E. A learned predictor", "### F. External confirmation", inclusive_end=False), part("05E_tpp.md") + "\n\n")
    rep(span("### F. External confirmation on Argoverse 2 (registered, run once)", "---\n\n## VI. Limitations", inclusive_end=False),
        part("05F_av2.md") + "\n\n")
    # VI (rewritten)
    rep(span("## VI. Limitations", "---\n\n## VII. Conclusion", inclusive_end=False), part("06_limits.md") + "\n\n")
    # appendices
    rep("- *Proposition 9.* c̄ ≥ ĉ_g pointwise and L_g is non-increasing.",
        "- *Proposition 9.* c̄ ≥ ĉ_g pointwise and L_g is non-increasing.\n\n*Moved from Section III.*\n\n" + "\n\n".join(app_a))
    rep("**C. Full per-stratum tables.**",
        "*Moved from Sections IV-B, V-A, V-B and V-C.*\n\n" + "\n\n".join(app_b) + "\n\n" + part("AB_k8.md") + "\n\n**C. Full per-stratum tables.**")
    rep("**D. Reproducibility.**", "**D. Reproducibility.**")
    k = s.index("**D. Reproducibility.**")
    j = s.index("\n\n---\n\n## Figures and tables", k)
    s = s[:j] + "\n\n" + part("AE_av2_protocol.md") + s[j:]
    rep("*End of draft v03b.*", "*End of draft v04.*")
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)
    print("written", out, len(s.split()), "words;", len(app_a), "paragraphs to A,", len(app_b), "to B")


if __name__ == "__main__":
    sys.exit(main())
