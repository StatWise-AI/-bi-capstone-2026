"""
apply_gbm_to_production.py
=============================
Takes gbm_production_forecasts.csv / gbm_production_meta.json (just produced
by gbm_production.py) and merges them into country_product_history_and_forecast.csv
and country_product_meta.json -- replacing the SARIMAX forecast rows with
GBM ones for the 18 combinations where GBM won (Model Comparison Report,
Section 8), and flagging model_used accordingly.

Run this LAST in the refresh chain, after build_history_and_forecast.py and
gbm_production.py.
"""
import pandas as pd
import json

# --- Merge into country_product_history_and_forecast.csv ---
combined = pd.read_csv("country_product_history_and_forecast.csv", parse_dates=["date"])
gbm_fc = pd.read_csv("gbm_production_forecasts.csv", parse_dates=["date"])

gbm_combos = set(zip(gbm_fc["country"], gbm_fc["product"]))
mask_remove = combined.apply(lambda r: (r["country"], r["product"]) in gbm_combos and r["is_forecast"], axis=1)
kept = combined[~mask_remove]
new_combined = pd.concat([kept, gbm_fc[combined.columns.tolist()]], ignore_index=True)
new_combined = new_combined.sort_values(["country", "product", "date"]).reset_index(drop=True)
new_combined.to_csv("country_product_history_and_forecast.csv", index=False)
print(f"Updated country_product_history_and_forecast.csv: replaced "
      f"{mask_remove.sum()} SARIMAX forecast rows with {len(gbm_fc)} GBM forecast rows "
      f"across {len(gbm_combos)} combinations.")

# --- Update country_product_meta.json ---
meta = json.load(open("country_product_meta.json"))
gbm_meta = json.load(open("gbm_production_meta.json"))
gbm_meta_lookup = {(m["country"], m["product"]): m for m in gbm_meta}

# Need the actual backtest MAE numbers to record alongside the switch --
# these came from the original Section 8 evaluation (gbm_pipeline.py), not
# regenerated every routine refresh (that's a separate, deliberate exercise
# -- see README). We keep whatever comparison numbers are already in
# gbm_vs_sarimax_comparison.csv from the last time that was run.
try:
    gbm_bt = pd.read_csv("gbm_vs_sarimax_comparison.csv")
    gbm_bt_lookup = {(r["country"], r["product"]): r for _, r in gbm_bt.iterrows()}
except FileNotFoundError:
    gbm_bt_lookup = {}

updated = 0
for m in meta:
    key = (m["country"], m["product"])
    if key in gbm_meta_lookup:
        m["model_used"] = "gbm"
        m["model_switch_reason"] = gbm_meta_lookup[key].get(
            "model_reason",
            "Section 8 of the Model Comparison Report: GBM beat SARIMAX on the identical backtest for this country/product."
        )
        if key in gbm_bt_lookup:
            row = gbm_bt_lookup[key]
            m["backtest"]["gbm"] = {
                "mean_mae": float(row["gbm_mae"]), "mean_rmse": float(row["gbm_rmse"]), "n_folds": int(row["gbm_folds"])
            }
        updated += 1
    else:
        m["model_used"] = "sarimax"

json.dump(meta, open("country_product_meta.json", "w"), indent=2)
print(f"Updated country_product_meta.json: {updated} combinations flagged model_used='gbm'.")
