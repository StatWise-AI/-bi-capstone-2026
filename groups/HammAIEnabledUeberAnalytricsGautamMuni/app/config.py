"""
config.py
================================================================================
Centralized configuration, kept separate from app.py so environment-specific
settings (paths, debug mode, future Gemini API key) never require touching
application logic. Per the approved Phase B1 architecture.
================================================================================
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    # --- Flask ---
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"
    HOST = "127.0.0.1"
    PORT = 5000

    # Prevents the browser from caching static/*.css and static/*.js across
    # app restarts - stale cached CSS/JS could otherwise make an updated
    # dashboard look like it still has old content. Combined with the
    # per-startup ASSET_VERSION cache-busting query string set in app.py.
    SEND_FILE_MAX_AGE_DEFAULT = 0
    TEMPLATES_AUTO_RELOAD = True

    ASSET_VERSION = "b4-1"  # overridden with a live timestamp in app.py at startup

    # --- Data paths ---
    RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw", "uber.xlsx")
    PROCESSED_DATA_DIR = os.path.join(BASE_DIR, "data", "processed")

    # --- AI (Phase B5) ---
    # Populated from .env (see .env.example) via python-dotenv, loaded in
    # app.py before this class is even evaluated. Never hardcoded, never
    # given a real-looking default - an empty string here is what makes
    # ai/gemini_service.is_configured() correctly report "not set up yet".
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    GEMINI_TIMEOUT_SECONDS = int(os.environ.get("GEMINI_TIMEOUT_SECONDS", "15"))

    # --- Navigation (single source of truth for both sidebar and routing) ---
    NAV_ITEMS = [
        {"key": "home",     "label": "Home",         "endpoint": "home.index",           "icon": "bi-house"},
        {"key": "overview", "label": "Overview",     "endpoint": "overview.index",        "icon": "bi-speedometer2"},
        {"key": "vehicle",  "label": "Vehicle",      "endpoint": "vehicle.index",         "icon": "bi-car-front"},
        {"key": "revenue",  "label": "Revenue",      "endpoint": "revenue.index",         "icon": "bi-currency-rupee"},
        {"key": "rider",    "label": "Rider",        "endpoint": "rider.index",           "icon": "bi-people"},
        {"key": "location", "label": "Location",     "endpoint": "location.index",        "icon": "bi-geo-alt"},
        {"key": "ai",       "label": "AI Assistant", "endpoint": "ai_insights.index",     "icon": "bi-stars"},
    ]
