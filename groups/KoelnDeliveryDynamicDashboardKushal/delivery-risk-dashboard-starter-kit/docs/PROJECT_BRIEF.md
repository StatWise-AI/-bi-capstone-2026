# Project Brief: Delivery Risk Dashboard & AI Agent

*Template business report — students should adapt Sections 6 onward with their
own dashboard screenshots, insights, and business narrative before submission.*

## 1. Introduction

On-time delivery is one of the clearest signals of supply chain health. When
shipments consistently run late, companies lose customer trust, absorb the cost of
expedited re-shipments, and struggle to plan warehouse and carrier capacity. Most
distribution operations only find out a shipment is late once it has already
happened — a reactive posture that leaves no room to intervene.

This project builds a predictive, proactive alternative: a classification model
that flags each order's delivery risk *before* it ships, so operations managers can
expedite, monitor, or leave alone accordingly.

## 2. Problem Statement and Business Objective

**Problem.** A global distribution company (DataCo Global) processes orders across
multiple markets, shipping modes, and carriers. Actual delivery performance varies
widely: some orders arrive early, some exactly on schedule, and a meaningful share
arrive significantly late. Without an early-warning system, the operations team can
only react after a delay has already occurred — the customer has already noticed.

**Objective.** Build and deploy a classification model that predicts
`Delivery_Risk_Category` (High / Medium / Low) for every order at the time it is
placed, using only information legitimately available at that point (order
attributes, product, customer segment, shipping mode chosen, calendar features) —
never information only known after the fact (actual shipping days, delivery
status).

## 3. Dataset Description

**Source:** DataCo Smart Supply Chain for Big Data Analysis (Mendeley Data, 2019) —
180,519 order-line records, 53 original columns, spanning 2015–2018 across
multiple countries, markets (Africa, Europe, LATAM, Pacific Asia, USCA), and
product categories (clothing, sports, electronics).

**Target engineering.** The raw dataset includes `Days for shipping (real)` and
`Days for shipment (scheduled)`. We define:

```
delay_days = Days for shipping (real) - Days for shipment (scheduled)

delay_days <= 0        -> Low Risk     (on-time or early)
1 <= delay_days <= 2    -> Medium Risk  (minor delay)
delay_days > 2          -> High Risk    (significant delay)
```

Resulting distribution: ~42.7% Low Risk, ~49.5% Medium Risk, ~7.8% High Risk — a
realistic class imbalance, with High Risk (the operationally critical class) being
the minority, exactly as in the stockout-risk project last semester.

**Leakage & PII removal.** Before modelling, we drop:
- **Leakage columns**: `Days for shipping (real)`, `Delivery Status`,
  `Late_delivery_risk` — all directly encode or reveal the outcome we're
  predicting, and are only known *after* delivery.
- **PII columns**: customer name, email, password, street address, exact
  lat/long, zip codes — required for data-ethics compliance; a real deployment
  must never train on personal data it doesn't need.
- **High-cardinality ID columns**: order/customer/product IDs — these don't
  generalize to new orders.

## 4. Methodology (Implementation in Python)

Implemented in `src/`, matching the reference project's five-step process:

1. **EDA** — class balance, correlation structure, missingness (see
   `notebooks/` if your team adds exploratory notebooks).
2. **Feature Engineering** (`src/data_preprocessing.py::engineer_features`) —
   `Order_Month`, `Order_Weekday`, `Order_Quarter`, `Order_Is_Weekend`,
   `Scheduled_Shipping_Days`, `Order_Value`, `Discount_Rate`,
   `Profit_Margin_Ratio`, `High_Value_Order`, `Multi_Item_Order`,
   `Is_Same_Day_Or_First_Class`.
3. **Preprocessing** (`src/train_model.py::encode_features`) — label encoding
   for categoricals, standard scaling for Logistic Regression, 70/30 stratified
   train/test split.
4. **Model Training** (`src/train_model.py::train_all_models`) — Logistic
   Regression (baseline), Decision Tree (interpretable), Random Forest
   (ensemble/feature importance), XGBoost (nonlinear boosting) — same four
   algorithms as the reference stockout-risk project.
5. **Model Evaluation** — weighted F1 as the primary metric (accuracy alone is
   misleading given class imbalance), plus precision/recall and a confusion
   matrix per class.

## 5. Results

See `outputs/metrics_summary.json` for the exact numbers from your training run,
and `outputs/model_comparison.png`, `outputs/confusion_matrix.png`,
`outputs/feature_importance.png` for the charts. In our reference run, **XGBoost**
was the best-performing model (weighted F1 ≈ 0.71), with `Shipping Mode` and
`Days for shipment (scheduled)` as the dominant risk drivers — i.e. the shipping
mode chosen at order time is the single biggest lever operations has over
delivery risk.

## 6. Decision Support System

| Risk Level | Recommended Action |
|---|---|
| High Risk | Expedite shipment / notify customer proactively |
| Medium Risk | Monitor closely / consider upgraded shipping mode |
| Low Risk | Standard processing |

This mapping is implemented in `src/predict.py::ACTION_MAP` and surfaced directly
in both the Streamlit dashboard and the AI agent's recommendations.

## 7. Business Impact *(students: replace with your own analysis)*

- Fewer customer complaints and expedite costs from catching high-risk orders early
- Better carrier/shipping-mode selection at order time, informed by real risk data
- A conversational AI agent lets non-technical managers query risk drivers and
  get recommendations without needing to read a model report

## 8. Conclusion *(students: write your own)*

## 9. Future Work *(students: write your own — ideas: real-time scoring via API,
retraining cadence, incorporating weather/carrier-performance data, expanding the
AI agent with more tools)*
