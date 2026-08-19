"""
data_preprocessing.py
----------------------
Loads the raw DataCo Supply Chain dataset, removes PII / target-leakage
columns, engineers business-meaningful features, and builds the 3-class
target "Delivery_Risk_Category" (High / Medium / Low) -- the delivery-side
equivalent of the "Stockout_Risk_Category" target used in the reference
inventory project.

This module is fully written for the students: nothing here needs to be
edited to run the pipeline. Students may extend it later (Future Work)
but are not required to write any ML code.
"""
from __future__ import annotations

import os
import pandas as pd
import numpy as np

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "DataCoSupplyChainDataset.csv")
SAMPLE_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "sample", "DataCoSupplyChain_sample.csv")
PROCESSED_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "model_ready_data.csv")

# Columns dropped because they are Personally Identifiable Information (PII).
# Removing PII before modelling is a data-ethics requirement, not just a
# modelling choice -- point this out to students explicitly.
PII_COLUMNS = [
    "Customer Email", "Customer Fname", "Customer Lname", "Customer Password",
    "Customer Street", "Latitude", "Longitude", "Product Image", "Product Description",
    "Product Status", "Order Zipcode", "Customer Zipcode",
]

# Columns dropped because they leak the target (they are only known AFTER
# the delivery outcome is observed, or they encode the label directly).
LEAKAGE_COLUMNS = [
    "Days for shipping (real)",   # actual shipping days -> defines the label
    "Delivery Status",            # text version of the label
    "Late_delivery_risk",         # binary version of the label (we re-derive our own 3-class target)
]

# High-cardinality identifier columns that don't generalize (order/customer/product IDs)
ID_COLUMNS = [
    "Customer Id", "Order Customer Id", "Order Id", "Order Item Cardprod Id",
    "Order Item Id", "Product Card Id", "Product Name",
]


def load_raw() -> pd.DataFrame:
    """Load the full raw dataset if present, otherwise fall back to the
    committed 5,000-row stratified sample so the pipeline always runs."""
    if os.path.exists(RAW_PATH):
        print(f"Loading full dataset: {RAW_PATH}")
        df = pd.read_csv(RAW_PATH, encoding="ISO-8859-1")
    else:
        print(f"Full dataset not found. Falling back to sample: {SAMPLE_PATH}")
        print("Run `python src/download_data.py` first to use the full 180,519-row dataset.")
        df = pd.read_csv(SAMPLE_PATH, encoding="ISO-8859-1")
    return df


def build_target(df: pd.DataFrame) -> pd.DataFrame:
    """Derive the 3-class Delivery_Risk_Category business target from the
    (real - scheduled) shipping-day gap, then drop the raw columns that
    would leak it."""
    delay_days = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]

    def bucket(d):
        if d <= 0:
            return "Low Risk"
        elif d <= 2:
            return "Medium Risk"
        else:
            return "High Risk"

    df = df.copy()
    df["Delivery_Risk_Category"] = delay_days.apply(bucket)
    return df


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Create business-meaningful derived features (mirrors the
    Inventory_Buffer / Stock_to_Reorder_Ratio style features from the
    reference project, adapted to delivery risk)."""
    df = df.copy()

    order_dt = pd.to_datetime(df["order date (DateOrders)"], errors="coerce")
    df["Order_Month"] = order_dt.dt.month
    df["Order_Weekday"] = order_dt.dt.dayofweek
    df["Order_Quarter"] = order_dt.dt.quarter
    df["Order_Is_Weekend"] = (df["Order_Weekday"] >= 5).astype(int)

    # Scheduled_Shipping_Days is known at order time -> legitimate predictor
    df["Scheduled_Shipping_Days"] = df["Days for shipment (scheduled)"]

    # Order value / discount signals
    df["Order_Value"] = df["Order Item Total"]
    df["Discount_Rate"] = df["Order Item Discount Rate"]
    df["Profit_Margin_Ratio"] = df["Order Item Profit Ratio"]
    df["High_Value_Order"] = (df["Order_Value"] > df["Order_Value"].median()).astype(int)
    df["Multi_Item_Order"] = (df["Order Item Quantity"] > 1).astype(int)

    # Express/expedited shipping is a strong operational signal
    df["Is_Same_Day_Or_First_Class"] = df["Shipping Mode"].isin(
        ["Same Day", "First Class"]
    ).astype(int)

    return df


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Drop PII, leakage, and unused ID columns; drop rows with missing target."""
    df = df.copy()
    drop_cols = [c for c in PII_COLUMNS + LEAKAGE_COLUMNS + ID_COLUMNS if c in df.columns]
    df = df.drop(columns=drop_cols)
    df = df.drop(columns=["order date (DateOrders)", "shipping date (DateOrders)"], errors="ignore")
    df = df.dropna(subset=["Delivery_Risk_Category"])
    return df


def run_pipeline(save: bool = True) -> pd.DataFrame:
    df = load_raw()
    df = build_target(df)
    df = engineer_features(df)
    df = clean(df)

    if save:
        os.makedirs(os.path.dirname(PROCESSED_PATH), exist_ok=True)
        df.to_csv(PROCESSED_PATH, index=False)
        print(f"Saved model-ready dataset: {PROCESSED_PATH} ({df.shape[0]} rows, {df.shape[1]} cols)")

    return df


if __name__ == "__main__":
    run_pipeline()
