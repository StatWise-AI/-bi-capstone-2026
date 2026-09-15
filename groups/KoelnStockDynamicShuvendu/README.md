# Stock Dynamics Dashboard - Project Documentation

This document explains what this Power BI dashboard is, what data it uses, what was built, and why. It is written so that someone who has never used Power BI can understand it and present it confidently.

---

## 1. The Business Problem (Use Case)

A regional distribution center manages **500 products (SKUs)** across 8 categories: Electronics, Apparel, Food & Beverage, Home & Garden, Automotive, Sports, Health & Beauty, and Books & Media.

The center has two opposite problems happening at the same time:
- **Stockouts**: some products run out, causing lost sales and unhappy customers.
- **Excess inventory**: other products are overstocked, tying up money and warehouse space.

**Goal:** classify every product by its risk of running out of stock (High Risk, Medium Risk, or Low Risk), and use that classification to decide things like: which products to reorder first, which suppliers to renegotiate with, and where to adjust safety stock.

The source data already includes a computed "Risk Score" and risk category for each product (this would normally come from a machine learning model trained on historical patterns; the dashboard's job is to make that information usable for day-to-day decisions, not to build the model itself).

---

## 2. The Data

**Source file:** `Stock_Dynamics_Dataset.xlsx`, one row per product (500 rows), 28 columns covering:
- **Product info**: SKU ID, category, supplier, unit cost/price
- **Stock levels**: current stock, reorder point, safety stock, max stock
- **Demand patterns**: average daily demand, demand variability, trend (increasing/decreasing/stable), seasonality
- **Historical performance**: stockouts last year, service level %, turnover rate, ABC classification (value-based tiering)
- **Operational metrics**: storage space needed, holding cost %, order cost, lead time
- **Risk indicators**: stock coverage days, Risk Score (0-100), and the final Stockout Risk Category

This data was loaded into Power BI once (a snapshot), so the dashboard always shows this same 500-row picture unless someone reconnects it to a refreshed file.

---

## 3. What "Measures" Are and Why They Matter

In Power BI, a **measure** is a calculation you define once and then reuse on any chart or card. Think of it like a formula in Excel that Power BI can recalculate instantly no matter how you slice or filter the data.

We wrote these calculations in **DAX** (Data Analysis Expressions - Power BI's formula language). Below is every measure created for this dashboard, explained in plain English.

| Measure Name | What It Calculates | In Plain English |
|---|---|---|
| Total SKUs | `COUNTROWS(Stock_Data)` | Counts how many products are in the table (500). |
| High Risk SKUs | Counts rows where risk category = "High Risk" | How many products are at high risk of running out. |
| Medium Risk SKUs / Low Risk SKUs | Same idea, for the other two categories | Splits the 500 products into risk buckets. |
| Avg Service Level % | `AVERAGE` of the service level column | On average, what % of demand is met without running out. |
| Avg Risk Score | `AVERAGE` of the Risk Score column | The average riskiness across all products (0-100 scale). |
| Avg Turnover Rate | `AVERAGE` of turnover rate | How many times, on average, inventory is sold and replaced per year. |
| Total Stock Value | Current stock x unit cost, summed across all products | The total dollar value of everything sitting in the warehouse. |
| High Risk % | High Risk SKUs divided by Total SKUs | What share of the catalog is high risk, as a percentage. |
| Below Reorder Point | Counts products where current stock is already below the reorder trigger | How many products need to be reordered right now. |
| Excess Inventory SKUs | Counts products with more than 90 days of stock on hand | How many products are overstocked. |
| Avg Coverage Days | `AVERAGE` of how many days current stock will last | On average, how long the current stock will last before running out. |
| Top Priority Escalations | Counts products that are BOTH "High Risk" AND top-value ("A" tier) | The most urgent products: valuable items that are also at risk. |
| Root Cause Review SKUs | Counts products with more than 5 stockouts last year | Products with a repeated stockout problem worth investigating. |
| Secondary Supplier Candidates | Counts products with a lead time over 30 days AND above-average demand | Products where relying on one slow supplier is risky, so a backup supplier should be found. |
| Avg Lead Time Days | `AVERAGE` of supplier lead time | How long, on average, it takes for a reorder to arrive. |
| Avg Daily Demand / Avg Demand Volatility | Averages of daily demand and its variability | How much of a product sells per day, and how unpredictable that demand is. |
| Total Storage Space SqFt | Sum of storage space needed across all products | Total warehouse floor space required. |
| Avg Holding Cost % / Avg Order Cost | Averages of cost columns | The average cost of holding stock and the average cost per reorder. |
| Service Level Target | A fixed value of 98 | The company's target service level, used for comparison against the actual average. |
| Avg Stockout Incidents | `AVERAGE` of stockouts last year | The current baseline for how often products run out, so progress toward the "under 3 per year" goal can be tracked. |

We also added one calculated column, **Reorder_Gap** (Reorder Point minus Current Stock), so the "how urgently does this need reordering" list could be sorted from most to least urgent.

---

## 4. The Dashboard: Page by Page

The report has **4 pages**, navigated with tabs at the bottom of the screen in Power BI Desktop.

### Page 1: Overview
The "at a glance" summary page.
- **4 KPI cards** across the top: Total SKUs (500), Avg Service Level % (85.2), Avg Risk Score (49.4), Below Reorder Point (204).
- **Donut chart** ("Total SKUs by Stockout Risk Category"): shows the split between High/Medium/Low risk products as proportions of a circle. Good for seeing the overall risk mix at a glance.
- **Bar chart** ("Avg Risk Score by Product Category"): horizontal bars comparing average riskiness across the 8 product categories, so you can immediately see which category is most concerning.
- **Column chart** ("Total SKUs by ABC Classification"): vertical bars showing how many products fall into value tier A, B, or C.
- **Column chart** ("Avg Coverage Days by Warehouse Zone"): compares how many days of stock coverage each warehouse zone typically has.
- **Two slicers** (filter panels) on the left for Product Category and Warehouse Zone, so anyone viewing the report can click a category or zone and have every chart on the page instantly filter to match.

### Page 2: Risk & Action Center
The "what do we do about it" page, focused on immediate action.
- **5 KPI cards**: High Risk SKUs (194), Top Priority Escalations (30), Excess Inventory SKUs (0), Avg Coverage Days (26.7), Avg Stockout Incidents (6.6).
- **Action list table**: every product, sorted from highest Risk Score to lowest, with its category, value tier, warehouse zone, coverage days, lead time, and risk label all in one row. This is the table someone would actually work down when deciding what to reorder or escalate first.
- **Two slicers**: Stockout Risk Category and ABC Classification, so you can, for example, filter to just "High Risk" + "A" tier products.

### Page 3: Inventory Health
The financial and operational health page.
- **4 KPI cards**: Total Stock Value ($78M), Avg Turnover Rate (16.5), Total Storage Space SqFt (8,345), Avg Holding Cost % (25.1).
- **Gauge chart**: shows Avg Service Level % (85.2) against the company's target of 98, visualized as a dial filling up toward the goal. This makes the gap between "where we are" and "where we want to be" immediately visible.
- **Below Reorder Point table**: every product currently below its reorder trigger, sorted by how far below (the Reorder_Gap column), so the most urgent restocks float to the top.
- **Excess Inventory table**: every product sorted by stock coverage days (highest first), surfacing the most overstocked items so they can be addressed (discounted, redistributed, or reordering paused).

### Page 4: Supplier & Demand Insights
The page connecting risk back to root causes and suppliers.
- **3 KPI cards**: Root Cause Review SKUs (245), Secondary Supplier Candidates (54), Avg Lead Time Days (22.9).
- **Column chart** ("Total SKUs by Demand Trend"): how many products have increasing, decreasing, or stable demand.
- **Matrix table** ("Demand & Risk by Product Category"): a small pivot-style table showing average daily demand, demand volatility, and average risk score side by side for each of the 8 categories, making it easy to spot which categories combine high demand with high unpredictability and high risk.
- **Matrix table** (by Supplier): every one of the 50 suppliers with their SKU count, average risk score, average lead time, and high-risk SKU count, so underperforming suppliers (long lead times, many high-risk products) are easy to identify.

---

## 5. Business Rules Built Into the Dashboard

These come directly from the distribution center's documented decision framework, and are now automated as measures rather than something someone has to calculate by hand:

- **High Risk (Score >= 60)**: needs immediate action, larger safety stock, daily monitoring.
- **Medium Risk (35-60)**: needs proactive, routine reorder management.
- **Low Risk (< 35)**: routine handling, monthly review is enough.
- **High Risk + Top Value (ABC tier A)**: escalated as top priority (the "Top Priority Escalations" card).
- **More than 5 stockouts last year**: flagged for root cause investigation (the "Root Cause Review SKUs" card).
- **Lead time over 30 days + above-average demand**: flagged as a candidate for a backup supplier (the "Secondary Supplier Candidates" card).

---

## 6. Key Numbers to Mention When Presenting

- 500 products tracked across 8 categories and 50 suppliers.
- 194 products (38.8%) are currently High Risk.
- Average service level is 85.2%, against a target of 98%, a meaningful gap.
- 204 products are already below their reorder point.
- 0 products currently qualify as "excess inventory" (over 90 days of coverage) in this snapshot, meaning the overstock problem described in the use case is not currently showing up in the data, worth calling out as a finding.
- 245 products have had more than 5 stockouts in the past year and warrant a root-cause look.
- 54 products are candidates for a second supplier due to long lead times combined with strong demand.
- Average stockout incidents currently sit at 6.6 per product per year, against the company's goal of fewer than 3.

---

## 7. How to Open and Explore It

This dashboard is shared as a single `.pbix` file. To open it:
1. Install Power BI Desktop (free, from the Microsoft Store or powerbi.microsoft.com). No license or sign-in is required to open and explore a local file.
2. Double-click the `.pbix` file, or open it from within Power BI Desktop.
3. Use the tabs at the bottom of the window to move between the 4 pages.
4. Click any value in a slicer (the filter panels) to see every chart on that page update instantly. Click it again to clear the filter.
5. Hover over any chart or bar to see exact numbers in a tooltip.

No internet connection or extra setup is needed since all the data is already contained inside the file.
