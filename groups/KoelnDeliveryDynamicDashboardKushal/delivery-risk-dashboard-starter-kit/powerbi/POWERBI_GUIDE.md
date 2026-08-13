# Power BI Companion — Delivery Risk Dashboard

The Streamlit app is your interactive AI-agent dashboard. Power BI is your
**presentation-grade** dashboard for the written report / in-class walkthrough.
Both read from the same source: `outputs/Final_Predictions.xlsx`.

## 1. Load the data

1. Power BI Desktop → **Get Data → Excel Workbook** → select
   `outputs/Final_Predictions.xlsx` → load the `Predictions` sheet.
2. In **Power Query Editor**, set correct data types:
   - `Order_Value`, `Discount_Rate`, `Profit_Margin_Ratio` → Decimal Number
   - `Predicted_Risk`, `Actual_Risk`, `Recommended_Action` → Text
   - `Correct_Prediction` → True/False
3. Close & Apply.

## 2. Build a Risk dimension table (recommended)

Create a small disconnected table for consistent color-coding across visuals:

| Risk | SortOrder | Color |
|---|---|---|
| High Risk | 1 | #DC2626 |
| Medium Risk | 2 | #F59E0B |
| Low Risk | 3 | #16A34A |

**Home → Enter Data**, paste the table above, name it `RiskLookup`. Use its
`Color` column for conditional formatting on visuals keyed by `Predicted_Risk`.

## 3. Core DAX measures

Paste these into a new measures table (**Modeling → New Table** → name it
`_Measures`, then **New Measure** for each):

```DAX
Total Orders = COUNTROWS(Predictions)

High Risk Orders =
CALCULATE([Total Orders], Predictions[Predicted_Risk] = "High Risk")

High Risk Rate =
DIVIDE([High Risk Orders], [Total Orders], 0)

Medium Risk Orders =
CALCULATE([Total Orders], Predictions[Predicted_Risk] = "Medium Risk")

Low Risk Orders =
CALCULATE([Total Orders], Predictions[Predicted_Risk] = "Low Risk")

Prediction Accuracy =
DIVIDE(
    CALCULATE([Total Orders], Predictions[Correct_Prediction] = TRUE),
    [Total Orders],
    0
)

Avg Order Value (High Risk) =
CALCULATE(
    AVERAGE(Predictions[Order_Value]),
    Predictions[Predicted_Risk] = "High Risk"
)

High Risk Rate by Region =
VAR CurrentRegion = SELECTEDVALUE(Predictions[Order Region])
RETURN
CALCULATE(
    [High Risk Rate],
    Predictions[Order Region] = CurrentRegion
)

High Risk Orders (Prior Period) =
CALCULATE(
    [High Risk Orders],
    DATEADD('Calendar'[Date], -1, MONTH)
)

High Risk Trend vs Prior Month =
DIVIDE(
    [High Risk Orders] - [High Risk Orders (Prior Period)],
    [High Risk Orders (Prior Period)],
    0
)
```

> `High Risk Trend vs Prior Month` requires a proper `Calendar` date table linked
> to an order-date column. If your `Final_Predictions.xlsx` export doesn't include
> order date, add it back in `src/train_model.py::build_predictions_workbook`
> (it's in the underlying processed dataset as `Order_Month`/`Order_Quarter`) —
> this is a good, safe place for students to extend the pipeline's *output*
> without touching any model-training code.

## 4. Suggested page layout

**Page 1 — Executive Overview**
- KPI cards: `Total Orders`, `High Risk Rate`, `Prediction Accuracy`
- Donut chart: orders by `Predicted_Risk` (colored via `RiskLookup`)
- Bar chart: `High Risk Rate` by `Order Region`

**Page 2 — Shipping & Operations**
- Bar chart: `High Risk Rate` by `Shipping Mode`
- Table: top 20 highest-value High Risk orders (sort by `Order_Value` desc,
  filter `Predicted_Risk = High Risk`) — this is the actionable "call list" for
  operations managers
- Matrix: `Order Region` × `Shipping Mode`, values = `High Risk Rate`

**Page 3 — Model Transparency**
- Import `outputs/feature_importance.png`, `outputs/confusion_matrix.png`, and
  `outputs/model_comparison.png` as static images (Insert → Image), OR
  recreate them natively as Power BI visuals for interactivity.
- Add a text box summarizing the model and its weighted F1 score (pull the
  exact number from `outputs/metrics_summary.json`).

## 5. Conditional formatting tip

For any table/matrix showing `Predicted_Risk`, use **Conditional formatting →
Font color → Field value → RiskLookup[Color]** (after merging `RiskLookup` in via
a calculated column or relationship) so High/Medium/Low always render in the same
red/amber/green regardless of which visual you're looking at.

## 6. Publishing

If your course requires a Power BI Service link: **Publish → select your
workspace**, then share the link alongside your GitHub repo and Streamlit app URL
in your final submission.
