"""
generate_data.py - synthetic data generator for the Retail Inventory KPI Dashboard.

Produces 9 CSVs (one per table in schema.sql) modeling a 4-district, 18-store
retail network replenished from a distribution center over a trailing 12-month window.

All data is synthetic. No employer data, real store names, or real retailer
data is used anywhere in this generator or its output.

Three intentional patterns are baked in so the resulting dashboard has real
findings to report (mirrors Project 01/02's "specific numbered findings"
case-study style):

  1. The "Gulf Coast" district runs chronically below PAR from month 7 onward
     (a staffing/ordering gap that widens over time).
  2. Product "Wireless Earbuds" (Electronics) has unusually high demand
     variance: promo-driven spikes rather than a steady rate.
  3. The "Gulf Coast" district also has the longest DC-to-store replenishment
     turnaround (7-10 days vs. 2-4 days elsewhere): a fulfillment-speed problem,
     not just a stocking problem.

Usage:
    pip install pandas numpy
    python generate_data.py
    # writes CSVs to ./data/
"""

import numpy as np
import pandas as pd
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta

RNG = np.random.default_rng(42)
OUT_DIR = "data"

# 12 full months trailing the current date used for this project.
START_MONTH = date(2025, 8, 1)
N_MONTHS = 12
MONTHS = [START_MONTH + relativedelta(months=i) for i in range(N_MONTHS)]

# ---------------------------------------------------------------------------
# 1. Districts
# ---------------------------------------------------------------------------
districts = pd.DataFrame([
    {"district_id": 1, "district_name": "Coastal Northeast", "region": "Northeast"},
    {"district_id": 2, "district_name": "Great Lakes",       "region": "Midwest"},
    {"district_id": 3, "district_name": "Piedmont",          "region": "Southeast"},
    {"district_id": 4, "district_name": "Gulf Coast",        "region": "South"},
])
LAGGING_DISTRICT_ID = 4  # Gulf Coast: intentionally under-PAR + slow allocations

# ---------------------------------------------------------------------------
# 2. Stores (4-5 per district, 18 total)
# ---------------------------------------------------------------------------
store_rows = []
store_id = 1
states_by_district = {1: ["CT", "MA", "NY"], 2: ["OH", "MI", "IL"], 3: ["NC", "SC", "GA"], 4: ["TX", "LA", "FL"]}
store_types = ["Supercenter", "Supercenter", "Neighborhood", "Express"]
stores_per_district = {1: 5, 2: 4, 3: 4, 4: 5}

for t_id, n_stores in stores_per_district.items():
    for i in range(n_stores):
        store_rows.append({
            "store_id": store_id,
            "store_name": f"{districts.loc[districts.district_id == t_id, 'district_name'].values[0]} Store {i+1}",
            "district_id": t_id,
            "store_type": RNG.choice(store_types),
            "state": RNG.choice(states_by_district[t_id]),
        })
        store_id += 1

stores = pd.DataFrame(store_rows)

# ---------------------------------------------------------------------------
# 3. Products
# ---------------------------------------------------------------------------
products = pd.DataFrame([
    # Electronics
    {"product_name": "Wireless Earbuds",           "category": "Electronics", "unit_cost": 68.00},
    {"product_name": "55in 4K Smart TV",           "category": "Electronics", "unit_cost": 389.00},
    {"product_name": "14in Laptop",                "category": "Electronics", "unit_cost": 342.00},
    {"product_name": "10in Tablet",                "category": "Electronics", "unit_cost": 189.00},
    {"product_name": "Soundbar",                   "category": "Electronics", "unit_cost": 118.00},
    {"product_name": "Smartwatch",                 "category": "Electronics", "unit_cost": 142.00},
    {"product_name": "Video Game Console",         "category": "Electronics", "unit_cost": 415.00},
    {"product_name": "Bluetooth Speaker",          "category": "Electronics", "unit_cost": 44.00},
    # Small appliances
    {"product_name": "Air Fryer 5qt",              "category": "Small Appliances", "unit_cost": 52.00},
    {"product_name": "Drip Coffee Maker",          "category": "Small Appliances", "unit_cost": 34.00},
    {"product_name": "Cordless Stick Vacuum",      "category": "Small Appliances", "unit_cost": 109.00},
    {"product_name": "Countertop Blender",         "category": "Small Appliances", "unit_cost": 38.00},
    {"product_name": "Microwave 1.1 cu ft",        "category": "Small Appliances", "unit_cost": 71.00},
    {"product_name": "Space Heater",               "category": "Small Appliances", "unit_cost": 29.00},
    # Household
    {"product_name": "Paper Towels 12-Roll",       "category": "Household", "unit_cost": 14.50},
    {"product_name": "Laundry Detergent 92oz",     "category": "Household", "unit_cost": 9.25},
    {"product_name": "Trash Bags 13gal 80ct",      "category": "Household", "unit_cost": 8.10},
    {"product_name": "AA Batteries 24-Pack",       "category": "Household", "unit_cost": 11.40},
    {"product_name": "LED Light Bulbs 4-Pack",     "category": "Household", "unit_cost": 6.30},
    {"product_name": "Disinfecting Wipes 75ct",    "category": "Household", "unit_cost": 4.20},
    {"product_name": "Dish Soap 24oz",             "category": "Household", "unit_cost": 2.95},
    # Grocery
    {"product_name": "Bottled Water 24-Pack",      "category": "Grocery", "unit_cost": 3.60},
    {"product_name": "Breakfast Cereal 12oz",      "category": "Grocery", "unit_cost": 2.35},
    {"product_name": "Canned Soup 10.5oz",         "category": "Grocery", "unit_cost": 0.95},
    {"product_name": "Snack Chips 8oz",            "category": "Grocery", "unit_cost": 1.70},
])
products.insert(0, "product_id", range(1, len(products) + 1))

HIGH_VARIANCE_PRODUCT_ID = int(products.loc[products.product_name == "Wireless Earbuds", "product_id"].iloc[0])
ELECTRONICS_IDS = products.loc[products.category == "Electronics", "product_id"].tolist()

# ---------------------------------------------------------------------------
# 4. PAR levels: each store carries 60-80% of the catalog
# ---------------------------------------------------------------------------
par_rows = []
par_id = 1
store_product_par = {}  # (store_id, product_id) -> par_qty, for downstream lookups

for _, s in stores.iterrows():
    n_products = RNG.integers(int(len(products) * 0.6), int(len(products) * 0.8))
    chosen = RNG.choice(products["product_id"].values, size=n_products, replace=False)
    for p_id in chosen:
        p_row = products.loc[products.product_id == p_id].iloc[0]
        base_par = {"Electronics": 4, "Small Appliances": 3, "Household": 25, "Grocery": 150}[p_row["category"]]
        par_qty = int(max(1, RNG.normal(base_par, base_par * 0.25)))
        par_rows.append({
            "par_id": par_id,
            "store_id": s["store_id"],
            "product_id": int(p_id),
            "par_qty": par_qty,
            "effective_start_date": START_MONTH,
            "effective_end_date": None,
        })
        store_product_par[(s["store_id"], int(p_id))] = par_qty
        par_id += 1

par_levels = pd.DataFrame(par_rows)

# ---------------------------------------------------------------------------
# 5. Inventory snapshots: monthly, on-hand qty around PAR with noise.
#    Gulf Coast drifts below PAR starting month 7 (index 6).
# ---------------------------------------------------------------------------
snapshot_rows = []
snapshot_id = 1

for (s_id, p_id), par_qty in store_product_par.items():
    district_id = int(stores.loc[stores.store_id == s_id, "district_id"].iloc[0])
    for i, month in enumerate(MONTHS):
        noise = RNG.normal(0, par_qty * 0.15)
        on_hand = par_qty + noise
        if district_id == LAGGING_DISTRICT_ID and i >= 6:
            # widening shortfall for the lagging district in the back half of the year
            shortfall_severity = (i - 5) * 0.08
            on_hand -= par_qty * shortfall_severity
        on_hand = int(max(0, round(on_hand)))
        snapshot_rows.append({
            "snapshot_id": snapshot_id,
            "store_id": s_id,
            "product_id": p_id,
            "snapshot_date": month,
            "on_hand_qty": on_hand,
        })
        snapshot_id += 1

inventory_snapshots = pd.DataFrame(snapshot_rows)

# ---------------------------------------------------------------------------
# 6. Pickup orders: buy-online-pick-up-in-store orders per store per month, electronics-driven
# ---------------------------------------------------------------------------
order_rows = []
order_id = 1

for _, s in stores.iterrows():
    store_products = par_levels.loc[par_levels.store_id == s["store_id"], "product_id"].tolist()
    store_electronics = [p for p in store_products if p in ELECTRONICS_IDS]
    if not store_electronics:
        continue
    district_id = int(s["district_id"])
    for month in MONTHS:
        n_orders = RNG.integers(4, 13)
        for _ in range(n_orders):
            p_id = int(RNG.choice(store_electronics))
            qty_required = int(RNG.integers(1, 4))
            order_day = month + timedelta(days=int(RNG.integers(0, 27)))

            snap = inventory_snapshots[
                (inventory_snapshots.store_id == s["store_id"]) &
                (inventory_snapshots.product_id == p_id) &
                (inventory_snapshots.snapshot_date == month)
            ]
            on_hand = int(snap["on_hand_qty"].iloc[0]) if len(snap) else 0

            if on_hand < qty_required:
                status = "Delayed" if RNG.random() < 0.85 else "Cancelled"
            else:
                status = "Fulfilled" if RNG.random() < 0.97 else "Delayed"

            order_rows.append({
                "order_id": order_id,
                "store_id": s["store_id"],
                "product_id": p_id,
                "order_date": order_day,
                "qty_required": qty_required,
                "order_status": status,
            })
            order_id += 1

pickup_orders = pd.DataFrame(order_rows)

# ---------------------------------------------------------------------------
# 7. Allocations: DC-to-store replenishment requests, longer turnaround for Gulf Coast
# ---------------------------------------------------------------------------
allocation_rows = []
allocation_id = 1

for (s_id, p_id), par_qty in store_product_par.items():
    district_id = int(stores.loc[stores.store_id == s_id, "district_id"].iloc[0])
    n_allocations = RNG.integers(3, 9)
    for _ in range(n_allocations):
        month = MONTHS[int(RNG.integers(0, N_MONTHS))]
        request_day = month + timedelta(days=int(RNG.integers(0, 27)))
        qty = int(max(1, RNG.normal(par_qty * 0.4, par_qty * 0.15)))

        if district_id == LAGGING_DISTRICT_ID:
            turnaround = int(RNG.integers(7, 11))
        else:
            turnaround = int(RNG.integers(2, 5))

        # ~6% of requests are still open (no fulfilled_date)
        fulfilled_date = None if RNG.random() < 0.06 else request_day + timedelta(days=turnaround)

        allocation_rows.append({
            "allocation_id": allocation_id,
            "destination_store_id": s_id,
            "product_id": p_id,
            "qty": qty,
            "request_date": request_day,
            "fulfilled_date": fulfilled_date,
        })
        allocation_id += 1

allocations = pd.DataFrame(allocation_rows)

# ---------------------------------------------------------------------------
# 8. Cycle counts: quarterly per store/product subset, one product noisier
# ---------------------------------------------------------------------------
cycle_count_rows = []
count_id = 1
count_months = [MONTHS[2], MONTHS[5], MONTHS[8], MONTHS[11]]  # quarterly

for (s_id, p_id), par_qty in store_product_par.items():
    if RNG.random() < 0.5:  # not every store/product gets counted every quarter
        continue
    for month in count_months:
        snap = inventory_snapshots[
            (inventory_snapshots.store_id == s_id) &
            (inventory_snapshots.product_id == p_id) &
            (inventory_snapshots.snapshot_date == month)
        ]
        expected = int(snap["on_hand_qty"].iloc[0]) if len(snap) else par_qty

        variance_pct = 0.18 if p_id == HIGH_VARIANCE_PRODUCT_ID else 0.05
        actual = int(max(0, round(expected + RNG.normal(0, max(1, expected * variance_pct)))))

        cycle_count_rows.append({
            "count_id": count_id,
            "store_id": s_id,
            "product_id": p_id,
            "count_date": month,
            "expected_qty": expected,
            "actual_qty": actual,
        })
        count_id += 1

cycle_counts = pd.DataFrame(cycle_count_rows)

# ---------------------------------------------------------------------------
# 9. Demand history: monthly units sold; high-variance product gets spiky sales
# ---------------------------------------------------------------------------
demand_rows = []
demand_id = 1

for (s_id, p_id), par_qty in store_product_par.items():
    p_row = products.loc[products.product_id == p_id].iloc[0]
    base_usage = {"Electronics": 1.5, "Small Appliances": 1.0, "Household": 8.0, "Grocery": 40.0}[p_row["category"]]
    for month in MONTHS:
        if p_id == HIGH_VARIANCE_PRODUCT_ID:
            # spiky, unpredictable usage: occasional zero months, occasional large spikes
            qty = int(max(0, RNG.choice([0, 0, base_usage, base_usage * 4, base_usage * 6])))
        else:
            qty = int(max(0, round(RNG.normal(base_usage, base_usage * 0.3))))
        demand_rows.append({
            "demand_id": demand_id,
            "store_id": s_id,
            "product_id": p_id,
            "usage_month": month,
            "qty_used": qty,
        })
        demand_id += 1

demand_history = pd.DataFrame(demand_rows)

# ---------------------------------------------------------------------------
# Write CSVs
# ---------------------------------------------------------------------------
import os
os.makedirs(OUT_DIR, exist_ok=True)

tables = {
    "districts": districts,
    "stores": stores,
    "products": products,
    "par_levels": par_levels,
    "inventory_snapshots": inventory_snapshots,
    "pickup_orders": pickup_orders,
    "allocations": allocations,
    "cycle_counts": cycle_counts,
    "demand_history": demand_history,
}

for name, df in tables.items():
    path = os.path.join(OUT_DIR, f"{name}.csv")
    df.to_csv(path, index=False)
    print(f"{name:22s} {len(df):6,d} rows -> {path}")

print("\nDone. Load these CSVs directly into Power BI (Get Data > Text/CSV),")
print("or run schema.sql against Postgres and \\copy each table in.")
