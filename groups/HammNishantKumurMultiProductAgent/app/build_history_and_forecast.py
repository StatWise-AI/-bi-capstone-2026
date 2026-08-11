"""
build_history_and_forecast.py
================================
Combines master_country_product_weekly.csv (actual history) with
country_product_forecasts.csv (the SARIMAX forecast model_pipeline.py just
produced) into country_product_history_and_forecast.csv -- the single file
country_product_agent.py actually reads.

Run this AFTER model_pipeline.py and BEFORE gbm_production.py, since
gbm_production.py's job is to overwrite a subset of these forecast rows
(diesel + most heating_oil) with the better-performing GBM forecast.
"""
import pandas as pd

master = pd.read_csv("master_country_product_weekly.csv", parse_dates=["date"])
forecasts = pd.read_csv("country_product_forecasts.csv", parse_dates=["date"])

history = master[["country", "product", "date", "price_with_tax", "price_wo_tax"]].copy()
history["is_forecast"] = False
history["price_with_tax_lower80"] = None
history["price_with_tax_upper80"] = None

fc = forecasts.rename(columns={
    "price_wo_tax_forecast": "price_wo_tax",
    "price_with_tax_forecast": "price_with_tax",
})[["country", "product", "date", "price_with_tax", "price_wo_tax",
    "price_with_tax_lower80", "price_with_tax_upper80"]].copy()
fc["is_forecast"] = True

combined = pd.concat([history, fc], ignore_index=True)
combined = combined.sort_values(["country", "product", "date"]).reset_index(drop=True)
combined = combined[["country", "product", "date", "price_with_tax", "price_wo_tax",
                      "is_forecast", "price_with_tax_lower80", "price_with_tax_upper80"]]

combined.to_csv("country_product_history_and_forecast.csv", index=False)
print(f"Saved country_product_history_and_forecast.csv: {len(combined)} rows "
      f"({(~combined['is_forecast']).sum()} history, {combined['is_forecast'].sum()} forecast)")
