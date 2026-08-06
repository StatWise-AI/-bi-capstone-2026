# Instructor Setup Guide — Central Course Repository

**Repo:** https://github.com/StatWise-AI/-bi-capstone-2026

Architecture: **one repository, one folder per group, students upload
directly through the browser.** No Git installation, no command line, no
Pull Requests required from students. Your `StatWise-AI` organization
doesn't expose a shareable "invite link," so access is granted per person
by username, name, or email — see Step 4.

```
-bi-capstone-2026/
├── README.md
├── CONTRIBUTING.md            <- student-facing instructions (provided)
├── groups.csv                 <- roster: folder name + GitHub usernames/emails
├── .gitattributes             <- Git LFS tracking for .pbix / .xlsx
└── groups/
    ├── HammPOSReportChandan/
    │   ├── README.md
    │   ├── app/
    │   ├── powerbi/
    │   └── data/
    ├── KoelnGupta/
    │   └── ...
    └── ...
```

## 1. Confirm the repo

The repo already exists at the link above, under the `StatWise-AI`
organization. You (or whoever created it) should have Owner or Admin
access — check under the repo's **Settings** tab.

## 2. Decide your roster

You already have the 14 group names — record their **folder names** in
`groups.csv`, one row per group (already filled in). If you're inviting by
**email**, you can skip the `github_usernames` column entirely — GitHub
accepts a plain email address for an invite (Step 4), no username needed
ahead of time.

## 3. You don't need to create the group folders

Skip this. GitHub creates a folder automatically the moment someone
uploads a file to a path that doesn't exist yet — so when
`HammPOSReportChandan` uploads their first file to
`groups/HammPOSReportChandan/app/companion_app.py`, that folder is created
on the spot. Nothing for you to scaffold in advance.

The only thing that needs to exist ahead of time is the folder-name
assignment (Step 2). Students create the folder themselves the first time
they upload — see `CONTRIBUTING.md`, Step 3.

*(`scaffold_repo.sh` is still in this kit if you'd ever rather pre-create
the folders yourself from `groups.csv` in one shot — e.g. if you want every
group to see an identical starting structure on day one — but it's
entirely optional with this workflow.)*

## 4. Invite each student (by username or email)

GitHub's organization "invite link" isn't available on `StatWise-AI` — so
access has to be granted person by person instead. Two ways to do it,
either works:

**Option A — from the Organization (recommended, grants access to all org repos):**
1. Go to **https://github.com/orgs/StatWise-AI/people**.
2. Click **Invite member**.
3. Enter their **university/personal email address** (or GitHub username
   or full name if you happen to know it) and send the invite. If they
   don't have a GitHub account yet, accepting the emailed invite prompts
   them to create one with that email — no extra step for you.
4. Under **Organization → Settings → Member privileges → Base
   permissions**, set this to **Write** so that once a student accepts,
   they can push to the repo without any extra per-repo step.
   ⚠️ Only do this if `-bi-capstone-2026` is the only repo in the
   organization — Base permissions apply org-wide. If you have other repos
   you don't want students writing to, instead create a **Team**, give
   that Team Write access to just this repo, and add each new member to
   the Team after they accept (Organization → Teams → your team →
   **Add a member**).

**Option B — directly on the repo (simpler, one repo only):**
1. Go to **https://github.com/StatWise-AI/-bi-capstone-2026/settings/access**.
2. Click **Add people**.
3. Enter their email address, choose **Write** as the role, and send the
   invite.

Either way, the student gets an email/notification, clicks **Accept
invitation**, and can then upload straight into their group's folder — no
further setup on their end, and no need to collect usernames from them
beforehand.

This means one invite per student rather than one link for everyone — with
14 groups (~2 students each) that's roughly 25–30 invites, each a quick
"paste email → Write → send."

## 5. Set up Git LFS for Power BI files (already configured)

`.pbix` and `.xlsx` files are tracked with Git LFS via the provided
`.gitattributes`, so large files uploaded through the browser are handled
automatically — students don't need to do anything extra. GitHub's free
tier includes 1 GB of LFS storage and 1 GB/month of bandwidth per
repository; with ~15–20 groups each uploading a handful of revisions, keep
an eye on usage (Settings → repository → look for storage/bandwidth under
the organization's billing page) and ask groups to upload only their final
`.pbix`, not every autosave.

## 6. Send students their instructions

Once you've sent a group's invite (Step 4), send them the message in
`STUDENT_INVITE_MESSAGE.md` — it tells them to accept the invite, points
to the repo, and gives their folder name.

## 7. Grading

Since students upload straight to `main`, each commit's timestamp and
author give you a simple activity trail: `git log groups/group-03-lastname/`
(or the "History" button on that folder in the GitHub web UI) shows exactly
what each group uploaded and when. If you'd prefer a review checkpoint
before anything lands on `main` (e.g. for a specific milestone), turn on
branch protection later and have students use the "create a new branch and
start a pull request" option that GitHub's upload UI offers automatically
when they don't have direct push access — `pull_request_template.md` is
included for that scenario, but it isn't required for the default flow
described above.
