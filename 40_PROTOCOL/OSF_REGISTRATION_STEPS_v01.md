# Register the frozen C1 plan on OSF: steps for the researcher (v01, 6 Nov 2026)

**Why this matters.** The plan is frozen: SHA-256 **0817e60097c2288b730044b8a38eb77de5f4e57a4b80067af6fd7c83a074e31c**, frozen 2026-11-06 20:08:13 UTC. An embargoed OSF registration archives it with a public timestamp before any Argoverse 2 outcome exists. Every outcome step (stage B onwards) refuses to run until I record this registration. This is step 2 of `40_PROTOCOL/OSF_DEPOSIT_GUIDE_v02.md`; the file list below follows the plan's section 8.3, which lists more files than the guide did.

**Time needed:** about 10 minutes, plus OSF's own approval period.

## The files

All 14 files are in `C:\Users\anand\Downloads\ProgrammeA_CLAUDE_IEEEACCESS_20261030_122911\40_PROTOCOL\OSF_UPLOAD_C1_FROZEN\`:

| File | What it is |
|---|---|
| `C1_AV2_CONFIRMATORY_PREREG_v07m.md` | the frozen plan |
| `C1_AV2_CONFIRMATORY_PREREG_v07m.sha256` | its fingerprint |
| `C1_HASH_LOG_LINE.txt` | the freeze's log line |
| `README_C1_CODE_v10.md` | the list of the 183 locked code files with fingerprints |
| `C1_FROZEN_BUNDLE_v01.zip` | the locked code, the analysis configuration and the locked data-role files (1.4 MB; no Argoverse 2 data, no outcome) |
| `C1_FREEZE_TIME_RECORD_v01.md` | what was done and seen before the freeze |
| `C1_RUN_COMMANDS_v01.txt` | every command that runs after the registration |
| `C1_CRITERIA_REGISTER_v05.md` | the source of every pass/fail criterion |
| the three `C1_FOLDS_*.sha256` files, `HASHES_FOLDS_SPLIT_TRANSFER.txt`, `SHAPE_CHECK_REFERENCE_rehearsal150_v10_config.json` | fingerprints and the reference configuration |
| `SHA256SUMS.txt` | fingerprints of all of the above, of every file in the zip, and of the 108 training and tracker files kept by fingerprint only |

## Steps

1. **Open the project.** Go to https://osf.io/eumj8/ and sign in with your ORCID, as before. Check that the **Make Public** button is still there, which means the project is still private.

2. **Upload the 14 files.**
   - Click **Files**, then **OSF Storage**.
   - Upload every file in the folder above, as you did for the text lock: use the **Upload** button, or drag them in.
   - The two text-lock files already there stay as they are.
   - Check that OSF Storage now lists 16 files: the 14 new ones and the 2 from this morning.

3. **Start the registration.**
   - Click **Registrations** in the project's top menu, then **New registration**.
   - Choose the template **Open-Ended Registration**.

4. **Fill in the summary.** Paste exactly this text:

   > Frozen pre-registration of the C1 Argoverse 2 confirmatory analysis; ground-truth stage B is built only after this registration. Frozen plan: C1_AV2_CONFIRMATORY_PREREG_v07m.md, SHA-256 0817e60097c2288b730044b8a38eb77de5f4e57a4b80067af6fd7c83a074e31c, frozen 2026-11-06 20:08:13 UTC.

   If OSF asks which files to attach, include all files in OSF Storage.

5. **Set the embargo.**
   - Choose **Enter into embargo**.
   - Set the end date to **6 November 2028** (two years ahead, beyond the expected publication).
   - The maximum is 4 years, and you can end the embargo early once the paper is out.

6. **Submit.**
   - OSF then gives the project's administrators 48 hours to cancel, and archives the registration afterwards.
   - **Do not cancel it.**
   - The registration page and its address exist from the moment you submit.

7. **Make a view-only link for IEEE Access** once OSF allows it. From 19 Feb 2027, OSF stops creating new view-only links for private projects, so make it now rather than later.

8. **Tell me four things** (replying here is fine):
   - the registration's address (`https://osf.io/xxxxx/`) or its DOI (`10.17605/OSF.IO/XXXXX`). This is not the project address `osf.io/eumj8`;
   - the date and time OSF shows for the registration, and the time zone it shows it in;
   - that the summary shows the SHA-256 above;
   - the view-only link, when you have it. This can come later.

I then write `40_PROTOCOL/C1_PLAN_DEPOSIT_RECORD_v01.txt`. Only after that can stage B and the analysis run: the code refuses every outcome step without this record.

## If something looks wrong

- **An upload fails or a file size differs:** delete only that file in OSF Storage and upload it again.
- **The project is not private, OSF shows a different template, or anything else is unexpected:** stop and tell me before you submit.
- **Do not edit or rename any file on OSF.**
