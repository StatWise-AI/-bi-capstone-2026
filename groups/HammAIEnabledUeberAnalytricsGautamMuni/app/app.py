"""
app.py
================================================================================
Flask application entry point.
================================================================================
"""

import logging
import os
import time
import webbrowser
from threading import Timer

# Ensures INFO-level logs (every Gemini request/response, per the AI
# integration's logging requirement) actually show up in the console -
# Flask's default logger level is WARNING otherwise.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# Must run BEFORE `from config import Config` - Config reads GEMINI_API_KEY
# (and other secrets) from os.environ at class-definition time, so the .env
# file has to be loaded into the environment first. python-dotenv never
# overwrites a variable that's already set in the real environment, so this
# is safe to call even if the key was set another way (e.g. a real env var
# in a production deployment).
from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, url_for, render_template

from config import Config
from backend import data_cache
from backend.routes.home import home_bp
from backend.routes.overview import overview_bp
from backend.routes.vehicle import vehicle_bp
from backend.routes.revenue import revenue_bp
from backend.routes.rider import rider_bp
from backend.routes.location import location_bp
from backend.routes.ai_insights import ai_insights_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # A fresh value every time the server starts, appended as ?v=... on every
    # static asset URL (see base.html) - guarantees the browser can never
    # serve a stale cached CSS/JS file from a previous run of this app.
    app.config["ASSET_VERSION"] = str(int(time.time()))

    # --- Dataset presence check (never crash - show a setup page instead) ---
    # The dataset path is read from config.py, never hardcoded here. If the
    # file isn't there yet, we do NOT call data_cache.init_data() at all -
    # we just record that data isn't ready, and a before_request hook below
    # intercepts every page with a friendly setup screen until it is.
    raw_path = app.config["RAW_DATA_PATH"]
    os.makedirs(os.path.dirname(raw_path), exist_ok=True)  # ensures data/raw/ always exists
    os.makedirs(app.config["PROCESSED_DATA_DIR"], exist_ok=True)

    app.config["DATA_READY"] = os.path.exists(raw_path)
    if app.config["DATA_READY"]:
        try:
            data_cache.init_data(raw_path)
        except Exception as exc:
            # Even a corrupt/unreadable file must not crash the app - fall
            # back to the setup page and show the actual error there.
            app.config["DATA_READY"] = False
            app.config["DATA_LOAD_ERROR"] = str(exc)

    # One blueprint per dashboard page, matching the approved architecture.
    app.register_blueprint(home_bp, url_prefix="/")
    app.register_blueprint(overview_bp, url_prefix="/overview")
    app.register_blueprint(vehicle_bp, url_prefix="/vehicle")
    app.register_blueprint(revenue_bp, url_prefix="/revenue")
    app.register_blueprint(rider_bp, url_prefix="/rider")
    app.register_blueprint(location_bp, url_prefix="/location")
    app.register_blueprint(ai_insights_bp, url_prefix="/ai-insights")

    @app.before_request
    def require_dataset():
        if app.config["DATA_READY"] or request.endpoint == "static":
            return None
        return render_template(
            "setup_required.html",
            raw_path=app.config["RAW_DATA_PATH"],
            load_error=app.config.get("DATA_LOAD_ERROR"),
        )

    # Makes NAV_ITEMS available to every template without passing it in
    # every single render_template() call.
    @app.context_processor
    def inject_nav():
        return {"nav_items": app.config["NAV_ITEMS"]}

    # --- Filter URL builders (the query-string filter mechanism documented
    # in backend/view_helpers.py) - registered once here so every template
    # can call them directly without each route passing them explicitly. ---
    @app.template_global()
    def vehicle_filter_url(vehicle_type: str) -> str:
        args = request.args.to_dict()
        if vehicle_type == "All":
            args.pop("vehicle", None)
        else:
            args["vehicle"] = vehicle_type
        return url_for(request.endpoint, **args)

    @app.template_global()
    def granularity_url(granularity: str) -> str:
        args = request.args.to_dict()
        args["granularity"] = granularity
        return url_for(request.endpoint, **args)

    @app.template_global()
    def reason_filter_url(reason: str) -> str:
        args = request.args.to_dict()
        if reason == "All":
            args.pop("reason", None)
        else:
            args["reason"] = reason
        return url_for(request.endpoint, **args)

    return app


def _open_browser(port: int):
    webbrowser.open(f"http://127.0.0.1:{port}/")


if __name__ == "__main__":
    app = create_app()
    # Opens the browser automatically ~1 second after the server starts,
    # matching the "runs via run.bat and opens in the browser" requirement.
    Timer(1.0, _open_browser, args=[app.config["PORT"]]).start()
    app.run(host=app.config["HOST"], port=app.config["PORT"], debug=app.config["DEBUG"], use_reloader=False)
