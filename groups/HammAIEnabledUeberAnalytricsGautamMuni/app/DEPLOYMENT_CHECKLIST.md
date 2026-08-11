# Deployment Verification Checklist

Use this after every deploy to Render (first deploy and any redeploy) to
confirm the cloud version behaves exactly like the local version.

## Before deploying

- [ ] `wsgi.py`, `requirements.txt`, `render.yaml`, `Procfile` are committed
      at the repo root, alongside the existing project files.
- [ ] `data/raw/uber.xlsx` is either committed to the repo, or you have a
      plan to place it on the instance after deploy (see README_DEPLOY.md
      section 0).
- [ ] `.env` (with your real `GEMINI_API_KEY`) is **not** committed - check
      `.gitignore` still lists it.
- [ ] `GEMINI_API_KEY` is set in Render's Environment tab (not in any
      committed file).

## Build & startup

- [ ] Render's **Logs** tab shows the build succeeding
      (`pip install -r requirements.txt` with no errors).
- [ ] Logs show the app starting: Flask's own startup INFO lines, followed
      by `wsgi: Flask app created and ready to be served by the WSGI
      server.`
- [ ] No `DATA_READY is False` warning in the logs (if you see it, the
      dataset isn't on the instance yet - see README_DEPLOY.md section 0).
- [ ] No `GEMINI_API_KEY is not set` warning in the logs (if you see it,
      double check the Environment tab).
- [ ] Service status shows **"Live"** in the Render dashboard.

## Functional parity with local

Open the deployed URL and compare against the local version page by page:

- [ ] **Home** page loads, nav sidebar renders identically to local.
- [ ] **Overview** page: KPIs and charts render with real numbers (not the
      "setup required" screen).
- [ ] **Vehicle** page: vehicle-type filter works, charts update.
- [ ] **Revenue** page: granularity toggle (day/week/month/etc.) works,
      charts update.
- [ ] **Rider** page loads and renders correctly.
- [ ] **Location** page loads and renders correctly.
- [ ] **AI Assistant** page:
  - [ ] Loads without error.
  - [ ] Submitting a question returns a real Gemini response (confirms
        `GEMINI_API_KEY` is correctly picked up from Render's environment).
  - [ ] If you intentionally remove `GEMINI_API_KEY` to test, the page
        shows the existing "not configured" messaging rather than a crash
        (this is existing `ai/gemini_service.py` behaviour, unchanged).
- [ ] Static assets (CSS, JS, icons/images under `static/`) load correctly
      - open browser dev tools -> Network tab and confirm no 404s.
- [ ] No Flask debugger page / stack trace is ever shown to the browser
      (confirms `FLASK_DEBUG=0` took effect - if you do see one, check the
      env var and redeploy).

## Performance / stability

- [ ] First request after a cold start completes within a reasonable time
      (this is the one-time dataset parse - see README_DEPLOY.md section
      5). Subsequent requests should be fast, matching local behaviour.
- [ ] Refreshing the page a few times in a row doesn't error out or slow
      down progressively (rules out a per-request memory/data leak).
- [ ] Leave the AI Assistant page open and idle, then submit a question
      after a few minutes - confirms the Gunicorn worker didn't time out
      or get recycled unexpectedly (the `--timeout 120` flag in
      `render.yaml`/`Procfile` covers slow Gemini responses).
- [ ] If you're on a memory-constrained Render plan: check the **Metrics**
      tab for memory usage after the app has been up for a few minutes.
      The dataset is loaded once per Gunicorn worker (`--workers 1` by
      default in this setup specifically to avoid multiplying that memory
      cost) - if you increase `--workers`, re-check memory usage here
      before assuming it's safe.

## Rollback readiness

- [ ] You know how to redeploy a previous commit from Render's "Deploys"
      tab (click any earlier successful deploy -> "Redeploy") in case a
      future change breaks production.
