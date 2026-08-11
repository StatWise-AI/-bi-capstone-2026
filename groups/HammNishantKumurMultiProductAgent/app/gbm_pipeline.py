"""
Gradient-boosted trees (LightGBM) evaluation, built to be directly comparable
to the existing SARIMAX backtest in model_pipeline.py -- same combinations,
same fold origins, same 12-week horizon, same MAE/RMSE scoring.

Strategy: "direct multi-horizon with horizon as a feature" -- one LightGBM
model per fold (not 12), trained on many (origin_t, horizon_h) examples
sliced from the training window, with h itself as an input feature. This is
the standard, sample-efficient way to do direct multi-step GBM forecasting
without recursive error compounding.

Features per training example (t, h):
  - lag_1, lag_4, lag_12 of the target (price_wo_tax) at t
  - rolling mean/std (4-week, 13-week) of the target at t
  - brent_now (Brent at t) and brent_future (Brent at t+h)
  - month_sin/cos at t+h (deterministic, always knowable)
  - fx_future at t+h (non-Eurozone countries only)
  - h (the horizon itself, 1..12)

Matches the SARIMAX backtest's convention of using the actual historical
exogenous values for the test window ("perfect foresight" on Brent/FX during
backtesting) rather than a held-flat assumption -- this isolates model
quality from exogenous-forecasting quality, exactly as the SARIMAX backtest
already does, so the two are comparable on the same basis.
"""
import pandas as pd
import numpy as np
import time
import json
import warnings
import lightgbm as lgb
warnings.filterwarnings("ignore")

MASTER_PATH = "master_country_product_weekly.csv"
HORIZON = 12
MIN_TRAIN_WEEKS = 100
N_ORIGINS_MAX = 4
MIN_HISTORY_FOR_LAGS = 13  # need 13 weeks of history before t to compute lag_12 / roll_mean_13


def mae(a, p):
    return float(np.mean(np.abs(np.asarray(a) - np.asarray(p))))


def rmse(a, p):
    return float(np.sqrt(np.mean((np.asarray(a) - np.asarray(p)) ** 2)))


def compute_origins(n):
    last_origin = n - HORIZON
    n_origins = min(N_ORIGINS_MAX, max(2, (last_origin - MIN_TRAIN_WEEKS) // 20))
    if last_origin - MIN_TRAIN_WEEKS < 20:
        n_origins = 2
    return sorted(set(np.linspace(MIN_TRAIN_WEEKS, last_origin, n_origins).astype(int).tolist()))


def build_direct_training_set(y, brent, month_sin, month_cos, fx, is_eurozone, origin):
    """Slide t across [MIN_HISTORY_FOR_LAGS, origin-1], generate one row per
    (t, h) pair with h=1..HORIZON, using only data within [0, origin) -- i.e.
    strictly the training window, no peeking past the fold's origin."""
    rows = []
    targets = []
    for t in range(MIN_HISTORY_FOR_LAGS, origin):
        lag_1 = y[t - 1]
        lag_4 = y[t - 4]
        lag_12 = y[t - 12]
        roll_mean_4 = y[t - 4:t].mean()
        roll_std_4 = y[t - 4:t].std() if t >= 4 else 0.0
        roll_mean_13 = y[t - 13:t].mean()
        brent_now = brent[t]
        for h in range(1, HORIZON + 1):
            tgt_idx = t + h
            if tgt_idx >= origin:
                break  # target must also stay inside the training window
            feat = [lag_1, lag_4, lag_12, roll_mean_4, roll_std_4, roll_mean_13,
                    brent_now, brent[tgt_idx], month_sin[tgt_idx], month_cos[tgt_idx], h]
            if not is_eurozone:
                feat.append(fx[tgt_idx])
            rows.append(feat)
            targets.append(y[tgt_idx])
    return np.array(rows), np.array(targets)


def build_test_features(y, brent, month_sin, month_cos, fx, is_eurozone, origin):
    """Features for forecasting origin, origin+1, ..., origin+HORIZON-1 from
    the vantage point of t = origin - 1 (last point actually observed)."""
    t = origin - 1
    lag_1 = y[t - 1]
    lag_4 = y[t - 4]
    lag_12 = y[t - 12]
    roll_mean_4 = y[t - 4:t].mean()
    roll_std_4 = y[t - 4:t].std() if t >= 4 else 0.0
    roll_mean_13 = y[t - 13:t].mean()
    brent_now = brent[t]
    rows = []
    for h in range(1, HORIZON + 1):
        tgt_idx = t + h
        feat = [lag_1, lag_4, lag_12, roll_mean_4, roll_std_4, roll_mean_13,
                brent_now, brent[tgt_idx], month_sin[tgt_idx], month_cos[tgt_idx], h]
        if not is_eurozone:
            feat.append(fx[tgt_idx])
        rows.append(feat)
    return np.array(rows)


LGB_PARAMS = dict(
    objective="regression", metric="mae", num_leaves=15, min_data_in_leaf=15,
    learning_rate=0.05, n_estimators=250, feature_fraction=0.8, bagging_fraction=0.8,
    bagging_freq=1, verbosity=-1, min_gain_to_split=0.0,
)


def fit_and_predict_gbm(y, brent, month_sin, month_cos, fx, is_eurozone, origin):
    X_train, y_train = build_direct_training_set(y, brent, month_sin, month_cos, fx, is_eurozone, origin)
    if len(X_train) < 50:
        return None
    model = lgb.LGBMRegressor(**LGB_PARAMS)
    model.fit(X_train, y_train)
    X_test = build_test_features(y, brent, month_sin, month_cos, fx, is_eurozone, origin)
    return model.predict(X_test)


def run_gbm_backtest_for_combo(country, product, sub):
    sub = sub.sort_values("date").reset_index(drop=True)
    is_eurozone = bool(sub["is_eurozone"].iloc[0])
    y = sub["price_wo_tax"].values
    brent = sub["brent_usd_per_bbl"].values
    month = sub["date"].dt.month.values
    month_sin, month_cos = np.sin(2 * np.pi * month / 12), np.cos(2 * np.pi * month / 12)
    fx = sub["exchange_rate"].values
    n = len(sub)

    origins = compute_origins(n)
    fold_results = []
    for origin in origins:
        if origin + HORIZON > n or origin < MIN_HISTORY_FOR_LAGS + HORIZON:
            continue
        y_test = y[origin:origin + HORIZON]
        pred = fit_and_predict_gbm(y, brent, month_sin, month_cos, fx, is_eurozone, origin)
        if pred is None:
            continue
        fold_results.append((mae(y_test, pred), rmse(y_test, pred)))

    if not fold_results:
        return {"mean_mae": None, "mean_rmse": None, "n_folds": 0}
    maes, rmses = zip(*fold_results)
    return {"mean_mae": float(np.mean(maes)), "mean_rmse": float(np.mean(rmses)), "n_folds": len(fold_results)}


if __name__ == "__main__":
    import sys
    country_filter = sys.argv[1] if len(sys.argv) > 1 else None

    master = pd.read_csv(MASTER_PATH, parse_dates=["date"])
    comp = pd.read_csv("completeness_report.csv")
    combos = comp[comp["included"]][["country", "product"]].values.tolist()
    if country_filter:
        combos = [c for c in combos if c[0].strip("_") == country_filter]

    results = []
    t0 = time.time()
    for i, (country, product) in enumerate(combos):
        cc = country.strip("_")
        sub = master[(master["country"] == cc) & (master["product"] == product)]
        if sub.empty:
            continue
        bt = run_gbm_backtest_for_combo(cc, product, sub)
        results.append({"country": cc, "product": product, **bt})
        print(f"[{i+1}/{len(combos)}] {cc:3s} {product:12s} "
              f"gbm_mae={bt['mean_mae']:.1f} folds={bt['n_folds']} ({time.time()-t0:.0f}s)", flush=True)

    out = pd.DataFrame(results)
    mode = "a" if country_filter and country_filter != combos[0][0].strip("_") else "w"
    import os
    if os.path.exists("gbm_backtest_results.csv") and country_filter:
        out.to_csv("gbm_backtest_results.csv", mode="a", header=False, index=False)
    else:
        out.to_csv("gbm_backtest_results.csv", index=False)
    print(f"\nTotal time: {time.time()-t0:.0f}s")
