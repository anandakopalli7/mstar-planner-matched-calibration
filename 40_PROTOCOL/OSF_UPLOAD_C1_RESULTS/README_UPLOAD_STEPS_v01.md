# Uploading the C1 results to OSF (for the researcher; 7 Nov 2026)

**Why.** Plan v07m §8.6 and step 30 require the run log and the stage-B log to be uploaded to the OSF project "with the results". The run notes and every run's outputs go with them. The registration itself (https://osf.io/v8qfk/) is frozen and does not change; the files go into the **project**, https://osf.io/eumj8/.

**What to upload** (this folder: `C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\OSF_UPLOAD_C1_RESULTS\`):

| File | Size | Contents | SHA-256 |
|---|---|---|---|
| `C1_RESULTS_A_v01.zip` | 24 MB | Essential: run log, stage-B log, deviation log, run notes and launcher logs, the decision and analysis of record with all tables, fits, method stage, H8, H9, the independent results review (R21), the GO decision report D19 | 4c4d10ea… (full value in `C1_RESULTS_A_v01.zip.sha256`) |
| `C1_RESULTS_B_v01.zip` | 1.9 GB | Full run outputs: items, run tables, Trajectron++ predictions | a4fd5792… (full value in `C1_RESULTS_B_v01.zip.sha256`) |
| the two `.sha256` files | tiny | checksums | – |

Each zip also contains `SHA256SUMS.txt`, with the hash of every file inside it.

**Steps** (about 10–30 minutes, mostly the upload of B):
1. Sign in at https://osf.io (ORCID, as before) and open https://osf.io/eumj8/.
2. Click **Files** → **OSF Storage**.
3. Create a folder: **Create Folder** → `C1_results_2026-11-07`.
4. Open that folder and upload `C1_RESULTS_A_v01.zip` and `C1_RESULTS_A_v01.zip.sha256`.
5. Upload `C1_RESULTS_B_v01.zip` and `C1_RESULTS_B_v01.zip.sha256`. B is 1.9 GB, under OSF's 5 GB per-file limit; keep the browser tab open until it finishes.
6. Tell me "Results uploaded" with the time. I record it in the protocol files, and the paper cites it.

**Do not:** change, withdraw or re-register the registration v8qfk; make the project public; or delete earlier files.

**Two more steps for the paper, when you are ready** (independent of this upload):
- **A view-only link for reviewers.** Project → **Settings** → **View-only Links** → **Create**. Tick the components and choose "Anonymize" only if the journal asks for it. Send me the link, and it goes into the cover letter. The plan (§8.3) keeps the embargo until after the expected publication; it may be ended earlier.
- **A public code repository** (for example GitHub, archived on Zenodo for a DOI). It is needed for the paper's code-and-data statement. I can prepare the repository contents; creating the accounts and pressing publish are yours.
