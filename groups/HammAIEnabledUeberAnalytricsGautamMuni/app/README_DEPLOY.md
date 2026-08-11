# Deploying the Uber Executive Dashboard to Render

This guide covers taking the existing, working local project and putting it
online on [Render](https://render.com). **Nothing about the dashboard, the
Gemini integration, business logic, data calculations, templates, or charts
was changed to do this.** Only the files listed below were added/updated to
make the project cloud-ready:

| File | Purpose |
|---|---|
| `wsgi.py` | Production entry point. Imports `create_app()` from `app.py` unchanged and hands the resulting Flask app to Gunicorn. |
| `requirements.txt` | Same dependencies as before, plus `gunicorn` (Render/Linux) and `waitress` (optional local Windows production testing). |
| `render.yaml` | Render Blueprint config - lets Render build the whole service automatically from this repo. |
| `Procfile` | Fallback start command, used if you create the service manually instead of via Blueprint. |
| `README_DEPLOY.md` | This file. |

`app.py`, `config.py`, `backend/`, `ai/`, `templates/`, `static/` are
**untouched**.

---

## 0. Before you start: the dataset

`config.py` points at `data/raw/uber.xlsx`, and the project's `.gitignore`
deliberately excludes that file (and the processed cache under
`data/processed/`) from source control, since it's a large, user-supplied
data file rather than source code.

**This means: if you push to GitHub as-is, the deployed instance will not
have the dataset, and the dashboard will show its existing "setup required"
page (`templates/setup_required.html`) instead of data.** This is expected,
existing behaviour - not a deployment bug.

You have two options, and neither requires touching any app code:

- **Option A (simplest): commit the dataset.** Remove the
  `data/raw/uber.xlsx` line from `.gitignore` and commit the file. Fine for
  a private repo / internal tool; the file is ~12 MB, well under GitHub's
  100 MB limit.
- **Option B: upload it after deploy.** Use Render's Shell (Dashboard ->
  your service -> "Shell") to `curl`/`scp` the file into
  `data/raw/uber.xlsx` on the running instance. Note that Render's default
  filesystem is **ephemeral** - anything placed there this way is wiped out
  on the next deploy or restart, so you'd need to redo this every time
  unless you also attach a
  [Render Disk](https://render.com/docs/disks) mounted at `data/raw/`.

Pick whichever matches how sensitive the dataset is. Option A is what the
rest of this guide assumes for simplicity.

---

## 1. Create a Render account

1. Go to [render.com](https://render.com) and sign up (GitHub sign-up is
   the fastest path since you'll be connecting a GitHub repo anyway).
2. Verify your email if prompted.

## 2. Connect GitHub

1. Push this project to a GitHub repository if it isn't already there
   (include `wsgi.py`, `requirements.txt`, `render.yaml`, `Procfile` from
   this deployment package, alongside the existing project files).
2. In the Render dashboard, click **"New +"** -> **"Web Service"** (or
   **"Blueprint"** if you want Render to read `render.yaml` automatically -
   recommended, see step 3).
3. Click **"Connect GitHub"**, authorize Render, and select the
   repository (and branch) containing this project.

## 3. Create the Web Service

**Option A - Blueprint (recommended, uses `render.yaml` automatically):**

1. From the Render dashboard: **"New +"** -> **"Blueprint"**.
2. Select your repo. Render detects `render.yaml` and shows you the
   `uber-executive-dashboard` service it's about to create, with the build
   command, start command, and environment variables already filled in
   (except the secret `GEMINI_API_KEY`, which it will prompt you for - see
   step 4).
3. Click **"Apply"**.

**Option B - Manual Web Service (if you'd rather not use Blueprints):**

1. **"New +"** -> **"Web Service"**, select your repo/branch.
2. **Runtime**: `Python 3`.
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn wsgi:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120 --log-file -`
   (or simply leave the Start Command field blank - Render will
   auto-detect and run the `Procfile` in this package instead, which
   contains the same command.)
5. **Instance Type**: Starter (or Free, if available on your account - see
   the RAM note in the Testing Checklist below).
6. Click **"Create Web Service"** - then continue to step 4 for env vars
   before the first deploy finishes, or add them right after and trigger a
   manual redeploy.

## 4. Environment Variables

Whichever path you used above, open your new service -> **"Environment"**
tab and set:

| Key | Value | Required? |
|---|---|---|
| `GEMINI_API_KEY` | your real key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey) | **Yes** - the AI Assistant page won't work without it |
| `GEMINI_MODEL` | `gemini-2.5-flash` | No - this is `config.py`'s existing default |
| `GEMINI_TIMEOUT_SECONDS` | `15` | No - this is `config.py`'s existing default |
| `FLASK_DEBUG` | `0` | Recommended - keeps the Flask debugger/reloader off in production |
| `SECRET_KEY` | (Render's "Generate" button, or any random string) | Recommended |
| `LOG_LEVEL` | `INFO` | No - optional, controls `wsgi.py`'s logging verbosity |

**Never commit `GEMINI_API_KEY` (or any real secret) into `.env`,
`render.yaml`, or any file you `git push`.** `render.yaml` in this package
uses `sync: false` for that key specifically so Render always asks you to
type it into the dashboard instead of reading it from the repo. `.env` /
`.env.example` continue to work exactly as before for local development
only.

If you used the Blueprint flow, Render will have already prompted you for
`GEMINI_API_KEY` during "Apply" in step 3.

## 5. Deploy

- Render deploys automatically after you click "Apply" / "Create Web
  Service", and again on every push to the connected branch afterwards
  (`autoDeploy: true` in `render.yaml`).
- Watch the **"Logs"** tab during the first deploy. You should see the
  same startup sequence as running locally: Flask's own INFO logs, then
  `wsgi: Flask app created and ready to be served by the WSGI server.`
  from `wsgi.py`.
- The very first request after a cold start may take longer than usual
  while `data_cache.init_data()` parses `uber.xlsx` and builds the
  processed cache (the same ~20-second one-time cost that exists locally,
  per the comments in `backend/data_cache.py`) - this is existing,
  unmodified behaviour, not something the deployment setup changed.

## 6. Your URL

Render assigns a URL of the form:

```
https://uber-executive-dashboard.onrender.com
```

(`uber-executive-dashboard` matches the `name:` field in `render.yaml`;
if you used the manual flow, Render generates a name based on what you
typed in step 3, and you can customize it under **Settings**.)

Open it - it should behave exactly like `http://127.0.0.1:5000/` did
locally: same nav, same charts, same AI Assistant page, same everything.

---

## Notes on what changed vs. how it changed

- **Dev server -> production server**: locally, `app.py` calls
  `app.run(...)` when run directly (`python app.py`, e.g. via
  `launcher.py`). In production, `wsgi.py` imports `create_app()` from
  `app.py` and hands the app object to **Gunicorn** instead - Gunicorn is
  the right choice for Render specifically because Render's runtime is
  Linux (Waitress is Windows-friendly but not needed here; it's still
  listed in `requirements.txt` as an optional way to test a
  production-style server locally on Windows before pushing).
- **No browser auto-open in production**: `app.py`'s `Timer(1.0,
  _open_browser, ...)` only runs inside `if __name__ == "__main__":`,
  which never executes when `wsgi.py` imports `app.py` as a module. There
  is nothing to disable - it simply doesn't apply on a headless server.
- **Host/port**: locally, `config.py`'s `HOST`/`PORT` (`127.0.0.1:5000`)
  are what `app.run()` binds to. In production, Gunicorn binds directly to
  `0.0.0.0:$PORT` (`$PORT` is injected by Render at runtime) via the start
  command - `config.py` was **not modified** for this; Gunicorn simply
  doesn't consult those values at all.
- **Secrets**: already environment-variable-based before this change
  (`config.py` reads `GEMINI_API_KEY` via `os.environ.get(...)`, loaded
  from `.env` locally via `python-dotenv`). Render's Environment tab
  replaces the local `.env` file - same mechanism, different source.
