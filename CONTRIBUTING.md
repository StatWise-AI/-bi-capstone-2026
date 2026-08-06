# How to Submit Your Project

Everyone's work lives in **one shared repository**, each group in its own
folder under `groups/`. You don't need to install Git or use the command
line — everything below happens in your browser.

## Step 1 — Accept the invite

You'll receive an invite link from the instructor (by email or posted in
class). Click it and sign in with (or create) a free GitHub account. Once
accepted, you'll be able to open and edit files in the repository.

## Step 2 — Find your group's folder name

The instructor will tell you your folder name, e.g. `group-03-mueller`.
**Your folder doesn't exist yet — you create it yourself the first time you
upload.** Don't guess a different name than the one you were given, and
don't create a second folder for your group later — reuse the same one.

## Step 3 — Upload your files

1. Go to the repository: **https://github.com/StatWise-AI/-bi-capstone-2026**
2. Click into the `groups/` folder.
3. Click **Add file → Upload files** (top right of the file list).
4. Drag and drop your file(s) using paths like:
   - `group-03-mueller/app/companion_app.py`
   - `group-03-mueller/powerbi/dashboard.pbix`
   - `group-03-mueller/data/dataset.csv`
   - `group-03-mueller/README.md`

   You can either type the folder path into the box GitHub shows above the
   drop area before uploading, or drag a whole folder from your computer
   named `group-03-mueller` containing your files — either way works, and
   GitHub creates the folder the moment your files land in it.
5. Scroll down, write a short message describing what you're adding (e.g.
   *"Add Streamlit companion app"*), and click **Commit changes** — commit
   directly to `main`.

After your first upload, `groups/group-03-mueller/` exists — from then on
just open it directly and keep adding files to it.

Repeat for each subfolder as your work is ready. You can upload as many
times as you like throughout the project — small, frequent uploads are
easier for the instructor to follow than one giant upload at the deadline.

## ⚠️ The one rule that matters

**Only add, edit, or delete files inside your own `groups/<your-folder>/`
directory.** Never touch another group's folder, and don't edit anything at
the repo root unless the instructor asks you to.

## Uploading your Power BI report

Yes — put your `.pbix` file directly in `groups/<your-folder>/powerbi/`
using the same **Add file → Upload files** flow. A couple of things to
know:

- `.pbix` files can be tens of MB. The repo is configured to handle this
  (Git LFS), so uploading through the browser works the same as any other
  file — no extra setup needed on your end.
- Upload your **final** version rather than every autosave.
- Your `.pbix` contains a full copy of your data model, including the
  underlying dataset. If your team used real (not synthetic) data, confirm
  with the instructor that it's okay to upload before you do.

## Common issues

- **Can't see an "Add file" button / uploads are rejected** — you probably
  haven't accepted the invite yet, or the invite hasn't given you write
  access. Message the instructor.
- **Uploaded to the wrong folder** — open the file, click the trash-can
  icon to delete it, and re-upload it in the right place.
- **File is too large to upload in the browser (>25 MB)** — split it, or
  ask the instructor; very large `.pbix` files may need a local Git
  install instead (ask and the instructor can walk you through it).
- **Not sure if you have access** — try opening
  https://github.com/StatWise-AI/-bi-capstone-2026 while signed in; if you
  see a 404, the invite hasn't gone through yet.
