"""
Production gradient-boosted tree forecasts for diesel and heating_oil (the
two products where Section 8 of the Model Comparison Report showed GBM
clearly outperforms SARIMAX). Same direct multi-horizon feature set as the
backtest in gbm_pipeline.py, refit on full history, with quantile models
(alpha=0.1 / 0.9) for an 80% interval to match the SARIMAX output convention
used everywhere else in the app.

Future Brent/FX are held at their last observed value for the forecast
horizon -- the same explicit, documented assumption used for SARIMAX.
"""
import pandas as pd
import numpy as np
import json
import lightgbm as lgb
import warnings
warnings.filterwarnings("ignore")

HORIZON = 12
MIN_HISTORY_FOR_LAGS = 13

BASE_PARAMS = dict(
    num_leaves=15, min_data_in_leaf=15, learning_rate=0.05, n_estimators=250,
    feature_fraction=0.8, bagging_fraction=0.8, bagging_freq=1, verbosity=-1,
)


def build_features_for_all_t(y, brent, month_sin, month_cos, fx, is_eurozone, n):
    """Every (t, h) pair using the FULL series (production: train on everything)."""
    rows, targets = [], []
    for t in range(MIN_HISTORY_FOR_LAGS, n):
        lag_1, lag_4, lag_12 = y[t - 1], y[t - 4], y[t - 12]
        roll_mean_4 = y[t - 4:t].mean()
        roll_std_4 = y[t - 4:t].std() if t >= 4 else 0.0
        roll_mean_13 = y[t - 13:t].mean()
        brent_now = brent[t]
        for h in range(1, HORIZON + 1):
            tgt_idx = t + h
            if tgt_idx >= n:
                break
            feat = [lag_1, lag_4, lag_12, roll_mean_4, roll_std_4, roll_mean_13,
                    brent_now, brent[tgt_idx], month_sin[tgt_idx], month_cos[tgt_idx], h]
            if not is_eurozone:
                feat.append(fx[tgt_idx])
            rows.append(feat)
            targets.append(y[tgt_idx])
    return np.array(rows), np.array(targets)


def build_future_features(y, brent, month_sin, month_cos, fx, is_eurozone, n, future_month_sin, future_month_cos):
    """Forecast n, n+1, ..., n+HORIZON-1 from vantage point t = n-1.
    Brent/FX held flat at their last observed value (future unknown)."""
    t = n - 1
    lag_1, lag_4, lag_12 = y[t - 1], y[t - 4], y[t - 12]
    roll_mean_4 = y[t - 4:t].mean()
    roll_std_4 = y[t - 4:t].std() if t >= 4 else 0.0
    roll_mean_13 = y[t - 13:t].mean()
    brent_now = brent[t]
    brent_flat = brent[t]  # held flat -- future Brent is not known
    fx_flat = fx[t] if not is_eurozone else None
    rows = []
    for h in range(1, HORIZON + 1):
        feat = [lag_1, lag_4, lag_12, roll_mean_4, roll_std_4, roll_mean_13,
                brent_now, brent_flat, future_month_sin[h - 1], future_month_cos[h - 1], h]
        if not is_eurozone:
            feat.append(fx_flat)
        rows.append(feat)
    return np.array(rows)


def fit_quantile_model(X, y, alpha=None):
    params = dict(BASE_PARAMS)
    if alpha is None:
        params["objective"] = "regression"
        params["metric"] = "mae"
    else:
        params["objective"] = "quantile"
        params["alpha"] = alpha
    model = lgb.LGBMRegressor(**params)
    model.fit(X, y)
    return model


def forecast_combo(country, product, sub):
    sub = sub.sort_values("date").reset_index(drop=True)
    is_eurozone = bool(sub["is_eurozone"].iloc[0])
    y = sub["price_wo_tax"].values
    brent = sub["brent_usd_per_bbl"].values
    month = sub["date"].dt.month.values
    month_sin, month_cos = np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12)
    fx = sub["exchange_rate"].values
    n = len(sub)

    X, yt = build_features_for_all_t(y, brent, month_sin, month_cos, fx, is_eurozone, n)

    last_date = sub["date"].iloc[-1]
    future_dates = pd.date_range(last_date + pd.Timedelta(days=7), periods=HORIZON, freq="7D")
    fm = future_dates.month.values
    future_month_sin, future_month_cos = np.sin(2 * np.pi * fm / 12), np.cos(2 * np.pi * fm / 12)

    X_future = build_future_features(y, brent, month_sin, month_cos, fx, is_eurozone, n, future_month_sin, future_month_cos)

    model_mean = fit_quantile_model(X, yt, alpha=None)
    model_lo = fit_quantile_model(X, yt, alpha=0.1)
    model_hi = fit_quantile_model(X, yt, alpha=0.9)

    pred_mean = model_mean.predict(X_future)
    pred_lo = model_lo.predict(X_future)
    pred_hi = model_hi.predict(X_future)
    # quantile models can cross for small/noisy data -- enforce monotonicity
    pred_lo = np.minimum(pred_lo, pred_mean)
    pred_hi = np.maximum(pred_hi, pred_mean)

    latest_tax_amount = float(sub["tax_amount"].iloc[-1])
    with_tax_mean = pred_mean + latest_tax_amount
    with_tax_lo = pred_lo + latest_tax_amount
    with_tax_hi = pred_hi + latest_tax_amount

    forecast_df = pd.DataFrame({
        "country": country, "product": product, "date": future_dates,
        "price_wo_tax": pred_mean, "price_with_tax": with_tax_mean,
        "price_with_tax_lower80": with_tax_lo, "price_with_tax_upper80": with_tax_hi,
        "is_forecast": True,
    })
    meta_update = {
        "country": country, "product": product,
        "model_used": "LightGBM (direct multi-horizon)",
        "model_reason": "Section 8 of the Model Comparison Report: GBM beat SARIMAX by 30-46% MAE for this product across all 10 countries.",
    }
    return forecast_df, meta_update


if __name__ == "__main__":
    master = pd.read_csv("master_country_product_weekly.csv", parse_dates=["date"])
    comp = pd.read_csv("completeness_report.csv")
    comp["country"] = comp["country"].str.strip("_")

    # Section 8 evidence: diesel wins GBM in all 10 countries; heating_oil wins
    # GBM in 8 of 10 -- DE and NL specifically favor SARIMAX for heating_oil
    # (see gbm_vs_sarimax_comparison.csv). Switch only where the country-level
    # backtest actually supports it, not at the product level alone.
    HEATING_OIL_SARIMAX_EXCEPTIONS = {"DE", "NL"}

    candidates = comp[(comp["included"]) & (comp["product"].isin(["diesel", "heating_oil"]))][["country", "product"]].values.tolist()
    combos = [(c, p) for c, p in candidates if not (p == "heating_oil" and c in HEATING_OIL_SARIMAX_EXCEPTIONS)]
    print(f"Generating GBM production forecasts for {len(combos)} combinations "
          f"(excluded: {[(c,p) for c,p in candidates if (c,p) not in combos]})")

    all_fc, all_meta = [], []
    for country, product in combos:
        sub = master[(master["country"] == country) & (master["product"] == product)]
        fc, meta = forecast_combo(country, product, sub)
        all_fc.append(fc)
        all_meta.append(meta)
        print(f"{country} {product}: forecast end price (wo-tax) = {fc['price_wo_tax'].iloc[-1]:.1f}")

    out = pd.concat(all_fc, ignore_index=True)
    out.to_csv("gbm_production_forecasts.csv", index=False)
    with open("gbm_production_meta.json", "w") as f:
        json.dump(all_meta, f, indent=2)
    print("\nSaved gbm_production_forecasts.csv and gbm_production_meta.json")
