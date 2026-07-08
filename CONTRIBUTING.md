# Contributing to the Course Repository

Everyone's work lives in **one shared repository**, each group in its own
folder under `groups/`. You'll never push directly to `main` — you'll work
on a branch and open a Pull Request, which is standard practice on real
engineering teams.

## Step 1 — Get access

1. **Create a free GitHub account** if you don't already have one:
   https://github.com/join
2. **Join the course organization** using the invite link posted in the
   root [README.md](./README.md) (or shared via your course platform).
   Clicking it sends a request to join — this is not automatic.
3. **Wait for approval.** Your instructor reviews and approves join
   requests individually; this usually happens within a day or two, not
   instantly.
4. Once approved, you'll see this repository under the organization in your
   GitHub account.

## Step 2 — Get assigned to your group

Being a member of the organization does not automatically give you a
folder or write access — that's a separate, deliberate step so the
instructor can keep group assignments accurate.

1. Go to the **Issues** tab of this repository → **New Issue** → choose
   **"Request Group Assignment."**
2. Fill in your name, GitHub username, and your team members' names (if
   you're the first from your group to request).
3. Submit it. The instructor will then:
   - create your group's folder under `groups/` (or confirm it exists),
   - add you as a collaborator with write access,
   - list you as an owner of your folder in `.github/CODEOWNERS`.
4. You'll get a notification when your folder is ready — check the
   `groups/` folder in the repo, or the table in the root README.

## ⚠️ The one rule that matters

**Only add, edit, or delete files inside your own `groups/<your-folder>/`
directory.** Never touch another group's folder, and don't edit anything
at the repo root unless the instructor asks you to. Reviewers will reject
pull requests that touch files outside your folder.

## Step 3 — Every time you work on the project

1. **Install Git** if you don't have it: https://git-scm.com/downloads
2. **Install Git LFS** (handles the Power BI `.pbix` file — one-time setup
   on each machine you use):
   ```bash
   git lfs install
   ```
3. **Clone the repo** (only needed once):
   ```bash
   git clone https://github.com/<org-name>/bi-capstone-2026.git
   cd bi-capstone-2026
   ```
4. **Make sure you're up to date** before starting any work session:
   ```bash
   git checkout main
   git pull origin main
   ```
5. **Create a branch** for your work (name it after your group):
   ```bash
   git checkout -b group-03-work
   ```
   If the branch already exists from last time, just check it out instead:
   `git checkout group-03-work` then `git pull origin group-03-work`.
6. **Do your work** inside `groups/group-03-lastname/` only:
   - `app/` — your `companion_app.py`, `requirements.txt`, etc.
   - `powerbi/` — your `.pbix` file (see note below)
   - `data/` — your dataset (CSV/XLSX)
   - `README.md` — your project summary, the deployed app URL, and your
     Power BI report link (public or share link, per what you chose)
7. **Commit your changes** with a clear message:
   ```bash
   git add groups/group-03-lastname/
   git commit -m "Add KPI cards and slicers to Power BI report"
   ```
8. **Push your branch:**
   ```bash
   git push origin group-03-work
   ```
9. **Open a Pull Request:** GitHub will show a banner with a "Compare &
   pull request" button after you push — click it, fill in the template
   (what you changed, links to your live deployment), and request review
   from your teammates and the instructor.
10. **Respond to review comments** if you get any, push more commits to
    the same branch (they'll show up in the same PR automatically), and
    wait for approval + merge.

Repeat steps 4–10 throughout the project — small, frequent PRs are easier
to review than one giant PR at the deadline.

## Uploading your Power BI report

Yes — put your `.pbix` file directly in `groups/<your-folder>/powerbi/`.
A few things to know:

- The repo is already configured with **Git LFS** for `.pbix` files, so as
  long as you ran `git lfs install` once (see Step 3 above), this works
  exactly like committing any other file — no special commands needed.
- Commit your **final** version, not every autosave — every commit of a
  `.pbix` file adds to the repo's storage, and the course has a shared
  quota.
- Remember your `.pbix` contains a full copy of your data model, including
  the underlying dataset. If your team used real (not synthetic) data,
  confirm with the instructor that it's OK to commit before you push it.

## Common issues

- **Can't see the repo / "Permission denied"** — you either haven't been
  approved into the organization yet, or you haven't been assigned to a
  group yet (see Step 2). You do not need to email the instructor directly
  for this — use the Request Group Assignment issue.
- **"Permission denied" pushing to `main`** — that's expected; branch
  protection blocks direct pushes on purpose. Push your branch and open a
  PR instead.
- **PR shows changes outside your folder** — you probably branched from an
  out-of-date `main`, or an editor auto-formatted a file it shouldn't have
  touched. Run `git status` before committing and double-check the file
  list.
- **Merge conflicts** — very unlikely if everyone stays in their own
  folder; if it happens, ask the instructor rather than guessing.
- **`.pbix` push seems to hang or is very slow** — that's Git LFS
  uploading the binary; let it finish. If it fails, confirm `git lfs
  install` was run and try again.
