# Data Dictionary

Source: DataCo Smart Supply Chain for Big Data Analysis (Mendeley Data, 2019).
180,519 rows, 53 original columns. Full field-by-field description from the
original authors: `data/raw/DescriptionDataCoSupplyChain.csv` (fetched by
`src/download_data.py`).

## How columns are treated in this project

| Category | Columns | Treatment |
|---|---|---|
| **Target source** | `Days for shipping (real)`, `Days for shipment (scheduled)` | Used ONCE to derive `Delivery_Risk_Category`, then the real-shipping-days column is dropped (see below) |
| **Leakage (dropped)** | `Days for shipping (real)`, `Delivery Status`, `Late_delivery_risk` | Only known after the delivery outcome is observed — using these as features would let the model "cheat" |
| **PII (dropped)** | `Customer Email`, `Customer Fname`, `Customer Lname`, `Customer Password`, `Customer Street`, `Latitude`, `Longitude`, `Customer Zipcode`, `Order Zipcode`, `Product Image`, `Product Description`, `Product Status` | Personal or non-predictive identifying information — dropped for data-ethics compliance and because they don't generalize |
| **IDs (dropped)** | `Customer Id`, `Order Customer Id`, `Order Id`, `Order Item Cardprod Id`, `Order Item Id`, `Product Card Id`, `Product Name` | High-cardinality identifiers that don't generalize to new orders |
| **Kept as features** | Everything else (see below) | Used to predict delivery risk |

## Key feature columns kept for modelling

| Column | Description |
|---|---|
| `Type` | Type of transaction (DEBIT, TRANSFER, CASH, PAYMENT) |
| `Benefit per order` | Earnings per order placed |
| `Sales per customer` | Total sales per customer |
| `Category Id` / `Category Name` | Product category code / description |
| `Customer City` / `Customer Country` / `Customer State` | Store location where purchase was registered |
| `Customer Segment` | Consumer, Corporate, or Home Office |
| `Department Id` / `Department Name` | Store department |
| `Market` | Africa, Europe, LATAM, Pacific Asia, USCA |
| `Order City` / `Order Country` / `Order Region` / `Order State` | Destination of the order |
| `Order Item Discount` / `Order Item Discount Rate` | Discount value / percentage |
| `Order Item Product Price` | Price without discount |
| `Order Item Profit Ratio` | Profit ratio for the order item |
| `Order Item Quantity` | Number of units ordered |
| `Sales` / `Order Item Total` | Order value fields |
| `Order Profit Per Order` | Profit for the whole order |
| `Order Status` | COMPLETE, PENDING, CLOSED, CANCELED, SUSPECTED_FRAUD, etc. |
| `Product Category Id` / `Product Price` | Product-level attributes |
| `Shipping Mode` | Standard Class, First Class, Second Class, Same Day |

## Engineered features (added by `src/data_preprocessing.py`)

| Column | Description |
|---|---|
| `Order_Month`, `Order_Weekday`, `Order_Quarter`, `Order_Is_Weekend` | Calendar features parsed from `order date (DateOrders)` |
| `Scheduled_Shipping_Days` | Copy of `Days for shipment (scheduled)` — legitimately known at order time |
| `Order_Value` | = `Order Item Total` |
| `Discount_Rate` | = `Order Item Discount Rate` |
| `Profit_Margin_Ratio` | = `Order Item Profit Ratio` |
| `High_Value_Order` | 1 if `Order_Value` above the dataset median, else 0 |
| `Multi_Item_Order` | 1 if `Order Item Quantity` > 1, else 0 |
| `Is_Same_Day_Or_First_Class` | 1 if `Shipping Mode` is "Same Day" or "First Class" (expedited), else 0 |

## Target variable

**`Delivery_Risk_Category`** (High Risk / Medium Risk / Low Risk) — derived from
`delay_days = Days for shipping (real) - Days for shipment (scheduled)`:

- `delay_days <= 0` → **Low Risk** (on-time or early)
- `1 <= delay_days <= 2` → **Medium Risk**
- `delay_days > 2` → **High Risk**

Distribution in the full dataset: ~42.7% Low Risk, ~49.5% Medium Risk, ~7.8% High
Risk.
