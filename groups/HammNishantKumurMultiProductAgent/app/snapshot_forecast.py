"""
snapshot_forecast.py
=====================
Saves a copy of the CURRENT forecast rows (the 12-week-ahead predictions
sitting in country_product_history_and_forecast.csv right now) into a
running log, forecast_snapshots.csv, before you refresh the pipeline with
new official data and overwrite them.

Run this BEFORE you download new data / re-run extract_master.py,
model_pipeline.py, or gbm_production.py.

Design choice, worth understanding: if a (country, product, target_date)
combination is already in the snapshot log, this script does NOT overwrite
it. The first prediction ever made for a given future week is kept -- the
one with the longest lead time -- rather than being replaced by a fresher,
shorter-horizon re-forecast every time you refresh. This is what makes a
genuine "how good are we at forecasting 12 weeks out" answer possible later,
rather than quietly grading the model on easier, short-horizon predictions.

Usage:
    python3 snapshot_forecast.py
"""
import pandas as pd
import os
from datetime import date

COMBINED_PATH = "country_product_history_and_forecast.csv"
META_PATH = "country_product_meta.json"
SNAPSHOT_PATH = "forecast_snapshots.csv"


def load_model_used_lookup():
    import json
    if not os.path.exists(META_PATH):
        return {}
    meta = json.load(open(META_PATH))
    return {(m["country"], m["product"]): m.get("model_used", "sarimax") for m in meta}


def main():
    combined = pd.read_csv(COMBINED_PATH, parse_dates=["date"])
    forecast_rows = combined[combined["is_forecast"] == True].copy()
    if forecast_rows.empty:
        print("No forecast rows found in", COMBINED_PATH, "-- nothing to snapshot.")
        return

    model_lookup = load_model_used_lookup()
    forecast_rows["model_used"] = forecast_rows.apply(
        lambda r: model_lookup.get((r["country"], r["product"]), "sarimax"), axis=1
    )
    forecast_rows["snapshot_taken_on"] = date.today().isoformat()
    forecast_rows["horizon_weeks"] = (
        (forecast_rows["date"] - pd.Timestamp(date.today())).dt.days / 7
    ).round().astype(int)

    new_snapshot = forecast_rows.rename(columns={
        "date": "target_date",
        "price_with_tax": "price_with_tax_forecast",
        "price_wo_tax": "price_wo_tax_forecast",
    })[[
        "country", "product", "target_date", "snapshot_taken_on", "horizon_weeks",
        "model_used", "price_with_tax_forecast", "price_wo_tax_forecast",
        "price_with_tax_lower80", "price_with_tax_upper80",
    ]]

    if os.path.exists(SNAPSHOT_PATH):
        existing = pd.read_csv(SNAPSHOT_PATH, parse_dates=["target_date"])
        existing_keys = set(zip(existing["country"], existing["product"], existing["target_date"]))
        new_only = new_snapshot[
            ~new_snapshot.apply(lambda r: (r["country"], r["product"], r["target_date"]) in existing_keys, axis=1)
        ]
        combined_out = pd.concat([existing, new_only], ignore_index=True)
        added = len(new_only)
    else:
        combined_out = new_snapshot
        added = len(new_snapshot)

    combined_out = combined_out.sort_values(["country", "product", "target_date"]).reset_index(drop=True)
    combined_out.to_csv(SNAPSHOT_PATH, index=False)

    print(f"Snapshot taken on {date.today().isoformat()}.")
    print(f"Added {added} new (country, product, target_date) predictions "
          f"not already in the log (existing ones were left untouched).")
    print(f"Total predictions now tracked: {len(combined_out)}")
    print(f"Saved: {SNAPSHOT_PATH}")


if __name__ == "__main__":
    main()
