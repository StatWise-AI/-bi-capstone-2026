"""
refresh_all.py
================
Runs the entire weekly refresh chain in the correct order, in one command:

  1. Download the latest official data (auto_download_oil_bulletin.py)
  2. Validate last time's forecasts against whatever actual data just
     arrived (validate_forecast_accuracy.py) -- done BEFORE regenerating,
     so this week's new forecasts don't overwrite what we're checking
  3. Rebuild master_country_product_weekly.csv (extract_master.py)
  4. Rebuild SARIMAX forecasts + backtests for all 52 combinations,
     country by country (model_pipeline.py)
  5. Merge history + forecast into the file the app reads
     (build_history_and_forecast.py)
  6. Regenerate GBM forecasts for the 18 combinations that use it
     (gbm_production.py)
  7. Apply those GBM forecasts into the combined file + meta.json
     (apply_gbm_to_production.py)
  8. Snapshot the new forecasts for next week's validation
     (snapshot_forecast.py)
  9. Regenerate the full multi-country Power BI dashboard workbook
     (build_full_powerbi_export.py)

Deliberately NOT included: re-running the full 52-combination GBM-vs-SARIMAX
backtest (gbm_pipeline.py). Which model architecture to use per
country/product is a considered decision (see Model Comparison Report,
Section 8), not something that should flip-flop
week to week on one new data point -- re-run gbm_pipeline.py by hand if you
deliberately want to redo that comparison (e.g. once a semester).

Usage:
    python3 refresh_all.py
"""
import subprocess
import sys

COUNTRIES = ["DE", "FR", "IT", "ES", "NL", "BE", "PL", "AT", "CZ", "PT"]

STEPS = [
    ("Downloading latest official data", ["auto_download_oil_bulletin.py"]),
    ("Validating last week's forecasts against new actuals", ["validate_forecast_accuracy.py"]),
    ("Rebuilding master dataset from the new Excel file", ["extract_master.py"]),
]


def run(cmd, label):
    print(f"\n{'='*70}\n{label}\n{'='*70}")
    result = subprocess.run([sys.executable] + cmd)
    if result.returncode != 0:
        print(f"\nSTOPPED: '{' '.join(cmd)}' failed (see error above). "
              f"Fix that first, then re-run refresh_all.py -- it's safe to "
              f"re-run from the start.")
        sys.exit(1)


def main():
    for label, cmd in STEPS:
        run(cmd, label)

    # country_product_forecasts.csv and country_product_meta.json are built
    # incrementally by model_pipeline.py (it appends so you can run one
    # country at a time). That's correct for a one-off build, but wrong for
    # a repeated weekly refresh -- without clearing them first, every run
    # would pile duplicate rows on top of the last one. Start clean instead.
    import os
    for stale_file in ["country_product_forecasts.csv", "country_product_meta.json"]:
        if os.path.exists(stale_file):
            os.remove(stale_file)
    print("\nCleared previous intermediate forecast files (this is expected -- "
          "they get fully rebuilt fresh each refresh, not appended to).")

    for country in COUNTRIES:
        run(["model_pipeline.py", country], f"SARIMAX forecast + backtest: {country}")

    run(["build_history_and_forecast.py"], "Merging history + SARIMAX forecasts")
    run(["gbm_production.py"], "Regenerating GBM forecasts (diesel + most heating oil)")
    run(["apply_gbm_to_production.py"], "Applying GBM forecasts into the app's data files")
    run(["snapshot_forecast.py"], "Snapshotting this week's forecasts for next time")
    run(["build_full_powerbi_export.py"], "Regenerating the full Power BI dashboard workbook")

    print(f"\n{'='*70}")
    print("Refresh complete. Restart the Streamlit app (or press R in the browser tab)")
    print("to see this week's updated forecasts. In Power BI, click Home -> Refresh")
    print("to pick up the newly regenerated Barrl_PowerBI_Full_Dashboard_Data.xlsx.")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
