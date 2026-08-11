"""
wsgi.py
================================================================================
Production WSGI entry point for cloud deployment (Render / Gunicorn).

This file does NOT modify app.py, config.py, backend/, ai/, templates/, or
static/ in any way. It simply imports the existing `create_app()` factory
that app.py already defines and exposes the resulting Flask app object as
`app`, which is what Gunicorn (or any WSGI server) needs to serve it.

Why this approach:
  - app.py's browser-opening Timer and app.run(...) call both live inside
    `if __name__ == "__main__":`, which only executes when app.py is run
    directly (`python app.py`), e.g. by the local launcher.py. Importing
    app.py as a module (as this file does) never triggers that block, so
    in production there is no Timer, no webbrowser.open(), and no dev
    server involved - Gunicorn serves the `app` object directly.
  - All existing startup behaviour (dataset presence check, data_cache
    init, blueprint registration, Gemini config, etc.) is preserved
    exactly as-is, because it all happens inside create_app(), which this
    file calls unchanged.

Local production-style testing (optional, not required for Render):
    waitress-serve --host=0.0.0.0 --port=5000 wsgi:app
or
    gunicorn wsgi:app --bind 0.0.0.0:5000

Render's start command (see render.yaml / Procfile) runs:
    gunicorn wsgi:app --bind 0.0.0.0:$PORT
================================================================================
"""

import logging
import os

# --------------------------------------------------------------------------
# Production logging
# --------------------------------------------------------------------------
# app.py already calls logging.basicConfig(level=INFO) at import time, which
# is what actually configures the root logger (this call site would be a
# no-op for the level/format if app.py's has already run, since
# basicConfig() only takes effect on the first call). We additionally route
# logs to stdout/stderr explicitly and honour a LOG_LEVEL env var, which is
# how Render (and most PaaS log viewers) expect apps to log - no log files
# to manage, no disk writes, everything visible in the platform's log tail.
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("wsgi")

# --------------------------------------------------------------------------
# Build the Flask app using the project's own, unmodified factory
# --------------------------------------------------------------------------
from app import create_app  # noqa: E402  (import after logging is configured)

app = create_app()

if not app.config.get("DATA_READY"):
    logger.warning(
        "DATA_READY is False - data/raw/uber.xlsx was not found at startup. "
        "The dashboard will show the setup_required.html page until the "
        "dataset is present. See README_DEPLOY.md for how to get the "
        "dataset onto the deployed instance."
    )

if not os.environ.get("GEMINI_API_KEY", "").strip():
    logger.warning(
        "GEMINI_API_KEY is not set in the environment - the AI Assistant "
        "page will report itself as not configured until it is set in "
        "the Render dashboard's Environment tab."
    )

logger.info("Flask app created and ready to be served by the WSGI server.")

# Gunicorn (and most WSGI servers) look for a module-level callable named
# `app` by default (matches the "wsgi:app" target used in the Procfile /
# render.yaml startCommand below).
