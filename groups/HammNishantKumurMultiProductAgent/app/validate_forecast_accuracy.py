"""
validate_forecast_accuracy.py
===============================
Compares every snapshotted forecast in forecast_snapshots.csv against real
data, for whichever (country, product, target_date) rows now have an actual
observation available in master_country_product_weekly.csv -- i.e. weeks
that were "the future" when the snapshot was taken and have since actually
happened and been published by the European Commission.

Run this AFTER you've downloaded new official data and re-run
extract_master.py (so master_country_product_weekly.csv is up to date).

Usage:
    python3 validate_forecast_accuracy.py
"""
import pandas as pd
import numpy as np

SNAPSHOT_PATH = "forecast_snapshots.csv"
MASTER_PATH = "master_country_product_weekly.csv"
OUT_DETAIL = "forecast_validation_detail.csv"
OUT_SUMMARY = "forecast_validation_summary.csv"


def main():
    try:
        snap = pd.read_csv(SNAPSHOT_PATH, parse_dates=["target_date"])
    except FileNotFoundError:
        print(f"No {SNAPSHOT_PATH} found yet. Run snapshot_forecast.py first, "
              f"before your next data refresh, so there's something to check later.")
        return

    master = pd.read_csv(MASTER_PATH, parse_dates=["date"])
    actual = master.rename(columns={
        "date": "target_date",
        "price_with_tax": "price_with_tax_actual",
        "price_wo_tax": "price_wo_tax_actual",
    })[["country", "product", "target_date", "price_with_tax_actual", "price_wo_tax_actual"]]

    merged = snap.merge(actual, on=["country", "product", "target_date"], how="left")
    validated = merged[merged["price_with_tax_actual"].notna()].copy()
    still_pending = merged["price_with_tax_actual"].isna().sum()

    if validated.empty:
        print(f"{len(merged)} predictions are being tracked, but none of their target dates "
              f"have actual data yet in {MASTER_PATH}. Nothing to validate yet -- "
              f"re-run this after your next data refresh.")
        return

    validated["error_with_tax"] = validated["price_with_tax_forecast"] - validated["price_with_tax_actual"]
    validated["abs_error_with_tax"] = validated["error_with_tax"].abs()
    validated["pct_error_with_tax"] = (validated["error_with_tax"] / validated["price_with_tax_actual"]) * 100
    validated["within_80pct_interval"] = (
        (validated["price_with_tax_actual"] >= validated["price_with_tax_lower80"]) &
        (validated["price_with_tax_actual"] <= validated["price_with_tax_upper80"])
    )

    validated.to_csv(OUT_DETAIL, index=False)

    summary = validated.groupby(["country", "product"]).agg(
        n_validated=("abs_error_with_tax", "size"),
        mae=("abs_error_with_tax", "mean"),
        mean_pct_error=("pct_error_with_tax", lambda x: x.abs().mean()),
        pct_within_80pct_interval=("within_80pct_interval", "mean"),
        model_used=("model_used", "first"),
    ).round(2).reset_index()
    summary["pct_within_80pct_interval"] = (summary["pct_within_80pct_interval"] * 100).round(0)
    summary.to_csv(OUT_SUMMARY, index=False)

    by_horizon = validated.groupby("horizon_weeks").agg(
        n=("abs_error_with_tax", "size"), mae=("abs_error_with_tax", "mean"),
    ).round(2)

    print(f"Validated {len(validated)} predictions against real published data "
          f"({still_pending} more are still waiting on future actuals).")
    print()
    print("Overall accuracy:")
    print(f"  Mean absolute error (with-tax price): EUR {validated['abs_error_with_tax'].mean():.1f} /1000L")
    print(f"  Mean absolute % error: {validated['pct_error_with_tax'].abs().mean():.1f}%")
    print(f"  Actual price fell within the stated 80% interval: "
          f"{validated['within_80pct_interval'].mean()*100:.0f}% of the time "
          f"(a well-calibrated interval should be close to 80%)")
    print()
    print("Accuracy by forecast horizon (does error grow the further out we predicted?):")
    print(by_horizon.to_string())
    print()
    print("Per country/product summary:")
    print(summary.to_string(index=False))
    print()
    print(f"Saved: {OUT_DETAIL} (every validated prediction) and {OUT_SUMMARY} (aggregated)")


if __name__ == "__main__":
    main()
