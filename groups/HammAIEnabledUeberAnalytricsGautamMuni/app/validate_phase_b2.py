"""
Validation script for Phase B2 review - NOT part of the permanent application
structure. Runs the full data_loader pipeline against the real uber.xlsx and
checks every measures.py function's output against the KPI values already
established and verified in the Power BI phase of this project.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backend import data_loader, measures, models

print("=" * 70)
print("STEP 1: Loading and cleaning data via data_loader.py")
print("=" * 70)
tables = data_loader.load_and_clean_data(path="data/raw/uber.xlsx")
fact = tables["fact_bookings"]
dim_date = tables["dim_date"]

for name, df in tables.items():
    print(f"  {name}: {df.shape[0]:,} rows x {df.shape[1]} cols")

print()
print("=" * 70)
print("STEP 2: Schema validation (backend/models.py)")
print("=" * 70)
schema_map = {
    "fact_bookings": models.FACT_BOOKINGS_SCHEMA,
    "dim_date": models.DIM_DATE_SCHEMA,
    "dim_vehicle": models.DIM_VEHICLE_SCHEMA,
    "dim_location": models.DIM_LOCATION_SCHEMA,
    "dim_customer": models.DIM_CUSTOMER_SCHEMA,
    "dim_status": models.DIM_STATUS_SCHEMA,
    "dim_payment": models.DIM_PAYMENT_SCHEMA,
}
all_problems = []
for name, schema in schema_map.items():
    problems = models.validate_table_against_schema(tables[name], schema)
    all_problems.extend(problems)
if all_problems:
    for p in all_problems:
        print(f"  SCHEMA ISSUE: {p}")
else:
    print("  All 7 tables match their documented schema exactly.")

print()
print("=" * 70)
print("STEP 3: KPI validation against known Phase 1 / approved values")
print("=" * 70)

checks = []


def check(label, actual, expected, tolerance=0.5):
    ok = abs(actual - expected) <= tolerance if isinstance(expected, (int, float)) else actual == expected
    checks.append(ok)
    status = "PASS" if ok else "FAIL"
    print(f"  [{status}] {label}: got {actual}, expected ~{expected}")


check("Total rows in fact table", len(fact), 150000, tolerance=0)
check("Completed Bookings", measures.completed_bookings(fact), 93000, tolerance=50)
check("Lost Bookings", measures.lost_bookings(fact), 57000, tolerance=50)
check("Revenue (total)", round(measures.revenue(fact)), 51846183, tolerance=1000)
check("Total Distance", round(measures.total_distance(fact)), 2510000, tolerance=5000)
check("Average Distance", round(measures.average_distance(fact), 2), 24.64, tolerance=0.05)
check("Avg Driver Rating", round(measures.avg_driver_rating(fact), 2), 4.23, tolerance=0.02)
check("Avg Customer Rating", round(measures.avg_customer_rating(fact), 2), 4.40, tolerance=0.02)
check("Distinct customers", measures.customer_count(fact), 104114, tolerance=0)
check("Distinct pickup+drop locations (Dim_Location)", len(tables["dim_location"]), 176, tolerance=0)
check("Vehicle types (Dim_Vehicle, incl. corrected eBike)", len(tables["dim_vehicle"]), 7, tolerance=0)
check("Duplicate Booking ID rows flagged", int(fact["Flag_DuplicateBookingID"].sum()), 2457, tolerance=5)

# Vehicle-level cross-check against the exact table validated in the Power BI phase
print()
print("  Vehicle Contribution %% breakdown (cross-check vs. approved Vehicle page table):")
vc = measures.vehicle_contribution_pct(fact)
print(vc.to_string(index=False))

print()
print("  Cancellation rate by vehicle (cross-check vs. Gemini AI integration example numbers):")
for vtype in fact["Vehicle Type"].dropna().unique():
    sub = fact[fact["Vehicle Type"] == vtype]
    total = measures.total_bookings(sub)
    lost = measures.lost_bookings(sub)
    print(f"    {vtype}: {lost}/{total} = {lost/total*100:.2f}% lost")

print()
print("=" * 70)
result = "ALL CHECKS PASSED" if all(checks) else f"{checks.count(False)} CHECK(S) FAILED"
print(f"RESULT: {result} ({checks.count(True)}/{len(checks)})")
print("=" * 70)
