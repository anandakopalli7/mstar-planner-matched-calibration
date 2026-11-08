# OSF deposit of the frozen C1 plan: steps for the researcher (v01, 4 Nov 2026)

**Why.** R17c (M1) found that a freeze recorded only on this laptop can be questioned: a log file can be rewritten. A registration on OSF, timestamped by a third party before the confirmatory ground truth (stage B) is built, shows reviewers that the plan existed first. You chose an embargoed OSF registration (D16 v19, Choice 40).

**Who does what.**
- **You:** everything on OSF, because it is your account and it is published under your name. I never create accounts or submit on your behalf.
- **Me:** I prepare one folder with every file to upload, check its hashes, and record what you report back.

## Step 1, now (before 16 Nov 2026): create an empty private OSF project

OSF will stop creating new projects on 16 Nov 2026 ([OSF is changing](https://www.cos.io/osf-changes); [OSF Projects transition](https://help.osf.io/article/727-osf-projects-transition)). Registrations are stated to be unaffected. OSF does not say whether files can be added to a registration made without a project, so a project made now is the safe container.

1. Sign in at https://osf.io (create an account if you have none).
2. **Create project.** Use a neutral title, for example "Programme A: C1 confirmatory plan". It stays **private**.
3. Add nothing else yet.
4. Tell me the project's URL. I record it in `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt`. The URL of a private project reveals nothing.

Existing projects can be updated until 19 Feb 2027. After that they become read-only.

## Step 2, at the freeze (I will tell you when): upload and register

I will prepare `40_PROTOCOL/OSF_UPLOAD_C1_FROZEN/` with:
- the frozen plan `C1_AV2_CONFIRMATORY_PREREG_vNN.md`;
- its `.sha256` sidecar;
- the C1 hash-log line;
- README_C1_CODE (the bound-file list with hashes);
- the folds, split and transfer-fit hash files;
- a `SHA256SUMS.txt` over all of them.

No Argoverse 2 data and no outcomes go in.

1. In the project, open **Files → OSF Storage** and upload every file in that folder.
2. Click **Registrations → New registration**. Choose the **Open-Ended Registration** template; it needs only a summary. In the summary, paste the frozen plan's sha256 and one sentence: "Frozen pre-registration of the C1 Argoverse 2 confirmatory analysis; ground-truth stage B is built only after this registration."
3. **Embargo:** choose "Enter into embargo". Set an end date beyond the expected publication, for example two years ahead. The maximum is 4 years, and you can end it early.
4. Submit. OSF gives contributors 48 hours to cancel. The registration is then archived and gets a DOI.
5. Tell me:
   - the registration's URL or DOI;
   - the date and time OSF shows for it;
   - that the sha256 in its summary matches the one I gave you.

   I write these into the deposit record. Only then can stage B run: from code v06, the stage-B builder refuses without that record.

## Afterwards

- **For peer review:** create a view-only link to the embargoed registration and give it to IEEE Access. OSF states that view-only links on embargoed registrations continue to work.
- **In the paper:** the registration's identifier and time, and the statement that stage B was built after it.
- **If OSF changes before the freeze** (for example, the freeze slips past 19 Feb 2027), I will propose another repository, such as a Zenodo record with restricted files, and you decide.
