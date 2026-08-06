# Instructor Setup Guide — Central Course Repository

**Repo:** https://github.com/StatWise-AI/-bi-capstone-2026

Architecture: **one repository, one folder per group, students upload
directly through the browser.** No Git installation, no command line, no
Pull Requests required from students — you're already using the
`StatWise-AI` GitHub Organization, which is what makes the "one link,
click, accept" flow possible.

```
-bi-capstone-2026/
├── README.md
├── CONTRIBUTING.md            <- student-facing instructions (provided)
├── groups.csv                 <- roster: folder name + GitHub usernames
├── .gitattributes             <- Git LFS tracking for .pbix / .xlsx
└── groups/
    ├── group-01-lastname/
    │   ├── README.md
    │   ├── app/
    │   ├── powerbi/
    │   └── data/
    ├── group-02-lastname/
    │   └── ...
    └── ...
```

## 1. Confirm the repo

The repo already exists at the link above, under the `StatWise-AI`
organization. You (or whoever created it) should have Owner or Admin
access — check under the repo's **Settings** tab.

## 2. Collect your roster

Decide each group's **folder name** (e.g. `group-01-mueller`) — using an
existing group number/roster from class is easiest. Record it in
`groups.csv`, one row per group:

```csv
folder_name,github_usernames
group-01-mueller,alice-dev,bob-codes
group-02-santos,carla-gh,dan-h
```

(GitHub usernames are optional for this workflow — they're only needed if
you later want per-folder ownership reviews. Skip that column if you don't
need it.) This file is just your own reference; students don't need to see
it, they just need their own folder name, e.g. from
`STUDENT_INVITE_MESSAGE.md`.

## 3. You don't need to create the group folders

Skip this. GitHub creates a folder automatically the moment someone
uploads a file to a path that doesn't exist yet — so when Group 3 uploads
their first file to `groups/group-03-mueller/app/companion_app.py`, the
`group-03-mueller/` folder is created on the spot. Nothing for you to
scaffold in advance.

The only thing that needs to exist ahead of time is the **folder-name
assignment** — which group gets which folder name — so two groups don't
collide or improvise conflicting names. Put that assignment in
`groups.csv` (folder name only, one row per group) and share each group's
folder name with them (in `STUDENT_INVITE_MESSAGE.md`, in class, or on your
LMS). Students create the folder themselves the first time they upload —
see `CONTRIBUTING.md`, Step 2.

*(`scaffold_repo.sh` is still in this kit if you'd ever rather pre-create
the folders yourself from `groups.csv` in one shot — e.g. if you want every
group to see an identical starting structure on day one — but it's
entirely optional with this workflow.)*

## 4. Give students one-click access (the invite link)

Since the repo lives under the **StatWise-AI organization**, you can use
GitHub's organization invite link instead of inviting each student one by
one:

1. Go to **https://github.com/orgs/StatWise-AI/people**.
2. Click **Invite member → Invite link** (or **Member privileges** →
   depending on GitHub's current UI, look for "Invite link" — it's a
   single shareable URL).
3. Under **Organization → Settings → Member privileges**, set **Base
   permissions** to **Write**. This means anyone who joins the org through
   the invite link automatically gets Write access to every org repo —
   including this one — so they can upload files straight away.
   ⚠️ Only do this if `-bi-capstone-2026` is the only repo in the
   organization, or if you're fine with all members having Write access to
   your other org repos too. If not, create a **Team**, add the repo to
   that Team with Write access, and add new members to that Team instead
   of using Base permissions.
4. Copy the invite link and send it to students (see
   `STUDENT_INVITE_MESSAGE.md` for ready-to-send wording).

Once a student clicks the link and accepts, they can go straight to the
repo and upload files into their group's folder — no separate per-student
invite needed.

*(If you'd rather not use an organization-wide invite link, the fallback is
inviting each student individually: repo → **Settings → Collaborators →
Add people** → their GitHub username or email, with **Write** access. This
works but means one invite per student instead of one link for everyone.)*

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

Send every group:
- The organization invite link (step 4)
- The repo link: https://github.com/StatWise-AI/-bi-capstone-2026
- A pointer to `CONTRIBUTING.md` (it's shown automatically when they
  browse the repo)

`STUDENT_INVITE_MESSAGE.md` in this kit has ready-to-send text combining
all three.

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
