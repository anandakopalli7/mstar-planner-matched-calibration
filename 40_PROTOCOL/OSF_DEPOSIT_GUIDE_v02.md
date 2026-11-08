# OSF deposit of the frozen C1 plan: steps for the researcher (v02, 4 Nov 2026)

**Supersedes** `OSF_DEPOSIT_GUIDE_v01.md`, which is kept unchanged. v02 adds:
- click-by-click detail for step 1;
- the researcher's accounts (OSF via ORCID, and Zenodo, both created 4 Nov 2026);
- the 19 Feb 2027 limit on new view-only links.

**Why.** R17c (M1) found that a freeze recorded only on this laptop can be questioned, because a log file can be rewritten. A registration on OSF is timestamped by a third party. If it exists before the confirmatory ground truth (stage B) is built, reviewers can see that the plan came first. You chose an embargoed OSF registration (D16 v19, Choice 40).

**Who does what.**
- **You** do everything on OSF, because it is your account and it is published under your name. I never create accounts or submit on your behalf.
- **I** prepare one folder with every file to upload, check its hashes, and record what you report back.

**Accounts (4 Nov 2026).** You have an OSF account, signed in with ORCID, and a Zenodo account.
- Zenodo needs nothing now. It is the fallback only, in case OSF cannot take the registration. Even then, I would ask you before anything goes there.

## Step 1, now (before 16 Nov 2026): create an empty private OSF project

From 16 Nov 2026 OSF creates no new projects ([OSF Projects transition](https://help.osf.io/article/727-osf-projects-transition)). Registrations "continue to operate as they did before". The project made now is the container for step 2.

1. Go to https://osf.io and sign in. Use **Sign in with ORCID**, as you did when you created the account.
2. Check your name once. Open your name (top right) → **Settings** → **Profile information**. The full name there is the name the registration will show, so make it match the name on the paper. Your ORCID iD is already linked.
3. Open your dashboard: click **My Projects** (or the OSF logo). Then click **Create new project**.
4. Fill in the form:
   - **Title:** `Argoverse 2 confirmatory analysis plan (C1)`. You can rename the project until 19 Feb 2027, and the registration gets its own title in step 2.
   - **Affiliation:** add your institution if it is listed. Otherwise leave it empty.
   - **Storage location:** **United States**. It cannot be changed later.
   - **Description:** leave it empty.
   - **Template:** leave it empty.
5. Click **Create project**. OSF opens the new project page.
6. **Check that it is private.** Projects are private by default.
   - Near the top right you should see a **Make Public** button. That button means the project is private.
   - Do not click it.
7. **Copy the URL** from the browser's address bar. It looks like `https://osf.io/ab3cd/`; the five characters are the project's id.
8. **Leave the rest for step 2.** Do not do any of these:
   - add files, a wiki, components or contributors;
   - start a registration.
9. **Send me the URL.**
   - I write it into `40_PROTOCOL/OSF_PROJECT_RECORD_v01.txt` and set the marker `00_PROGRESS/markers/OSF_PROJECT_CREATED.txt`.
   - The URL does not go into the deposit record `C1_PLAN_DEPOSIT_RECORD_v01.txt`: that file is written only after step 2, because its existence is what unlocks stage B. (v01 of this guide said otherwise. That is corrected here.)
   - The URL of a private project shows nothing to anyone who is not signed in as a contributor.

## Step 2, at the freeze (I will tell you when): upload and register

The C1 plan is frozen first: its sha256 goes into `C1_PLAN_HASH_LOG.txt`. Then I prepare the folder `40_PROTOCOL/OSF_UPLOAD_C1_FROZEN/` with:
- the frozen plan `C1_AV2_CONFIRMATORY_PREREG_vNN.md`;
- its `.sha256` sidecar;
- the C1 hash-log line;
- README_C1_CODE (the bound-file list with hashes);
- the folds, split and transfer-fit hash files;
- a `SHA256SUMS.txt` over all of them.

No Argoverse 2 data and no outcomes go in.

1. In the project, open **Files** → **OSF Storage** and upload every file in that folder.
2. Open **Registrations** → **New registration**.
   - Choose the **Open-Ended Registration** template; it needs only a summary.
   - In the summary, paste the frozen plan's sha256 and this sentence: "Frozen pre-registration of the C1 Argoverse 2 confirmatory analysis; ground-truth stage B is built only after this registration."
3. **Embargo:** choose "Enter into embargo". Set an end date beyond the expected publication, for example two years ahead. The maximum is 4 years, and you can end it early.
4. **Submit.** OSF gives contributors 48 hours to cancel. The registration is then archived and gets a DOI.
5. **Make the view-only link.** As soon as the registration is accepted, create a view-only link to it for IEEE Access.
   - From 19 Feb 2027 OSF creates no new view-only links for private projects. Making the link at once avoids any doubt about whether that also covers registrations.
6. **Tell me:**
   - the registration's URL or DOI;
   - the date and time OSF shows for it;
   - that the sha256 in its summary matches the one I gave you;
   - the view-only link.

   I write these into the deposit record. Only then can stage B run: from code v06, the stage-B builder refuses without that record.

## Afterwards

- **For peer review:** give the view-only link to IEEE Access.
- **In the paper:** state the registration's identifier and time, and that stage B was built after it.
- **If OSF changes before the freeze** (for example, the freeze slips past 19 Feb 2027, when projects become read-only), I will propose another route, such as a Zenodo record with restricted files, and you decide.

Sources:
- [OSF is changing](https://www.cos.io/osf-changes)
- [OSF Projects transition](https://help.osf.io/article/727-osf-projects-transition)
- [Creating a project](https://help.osf.io/article/383-creating-a-project)
- [Create a Preregistration](https://osf-support.helpscoutdocs.com/article/158-create-a-preregistration)
