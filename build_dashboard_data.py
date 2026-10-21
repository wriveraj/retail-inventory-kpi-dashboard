"""
build_dashboard_data.py - computes the JSON block embedded in dashboard.html
from the generated CSVs, using the same definitions as dax-measures.md.

Usage:
    python build_dashboard_data.py            # prints the JSON
    python build_dashboard_data.py --write    # replaces the block in dashboard.html
"""
import json
import re
import sys

import pandas as pd

D = "data/"
districts = pd.read_csv(D + "districts.csv")
stores = pd.read_csv(D + "stores.csv")
products = pd.read_csv(D + "products.csv")
par = pd.read_csv(D + "par_levels.csv")
inv = pd.read_csv(D + "inventory_snapshots.csv")
orders = pd.read_csv(D + "pickup_orders.csv")
alloc = pd.read_csv(D + "allocations.csv", parse_dates=["request_date", "fulfilled_date"])
cc = pd.read_csv(D + "cycle_counts.csv")
dem = pd.read_csv(D + "demand_history.csv")

sd = stores.merge(districts, on="district_id")[["store_id", "store_name", "district_name"]]

inv = inv.merge(par[["store_id", "product_id", "par_qty"]], on=["store_id", "product_id"])
inv = inv.merge(products[["product_id", "unit_cost"]], on="product_id").merge(sd, on="store_id")
inv["ratio"] = inv["on_hand_qty"] / inv["par_qty"]
inv["exposure"] = (inv["par_qty"] - inv["on_hand_qty"]).clip(lower=0) * inv["unit_cost"]
months = sorted(inv["snapshot_date"].unique())
first, last = months[0], months[-1]
latest = inv[inv.snapshot_date == last]

orders = orders.merge(sd, on="store_id")
orders["month"] = orders["order_date"].str.slice(0, 7)
om = sorted(orders["month"].unique())
rate = lambda df: (df["order_status"] == "Fulfilled").mean()

alloc = alloc.merge(sd, left_on="destination_store_id", right_on="store_id")
alloc["turn"] = (alloc["fulfilled_date"] - alloc["request_date"]).dt.days

cc = cc.merge(sd, on="store_id")
cc["acc"] = 1 - (cc["actual_qty"] - cc["expected_qty"]).abs() / cc["expected_qty"].where(cc["expected_qty"] > 0)

dv = dem.groupby("product_id")["qty_used"].agg(avg="mean", stdev=lambda s: s.std(ddof=0)).reset_index()
dv["cv"] = dv["stdev"] / dv["avg"].replace(0, 1)
dv = dv.merge(products[["product_id", "product_name", "category"]], on="product_id").sort_values("cv", ascending=False)

order = ["Gulf Coast", "Coastal Northeast", "Great Lakes", "Piedmont"]
out = {
    "kpi": {
        "fulfillmentRate": round(rate(orders), 4),
        "fulfillmentRateMoM": round(rate(orders[orders.month == om[-1]]) - rate(orders[orders.month == om[-2]]), 4),
        "parComplianceLatest": round(latest["ratio"].mean(), 4),
        "parComplianceStart": round(inv[inv.snapshot_date == first]["ratio"].mean(), 4),
        "reorderCostLatest": round(latest["exposure"].sum(), 2),
        "turnaroundDays": round(alloc["turn"].mean(), 2),
        "cycleCountAccuracy": round(cc["acc"].mean(), 4),
        "statusMix": {k: round(v, 4) for k, v in orders["order_status"].value_counts(normalize=True).items()},
    },
    "parComplianceByMonth": {
        "months": [str(m) for m in months],
        "districts": {t: [round(inv[(inv.district_name == t) & (inv.snapshot_date == m)]["ratio"].mean(), 4) for m in months] for t in order},
    },
    "reorderCostByDistrict": sorted(
        [{"district": t, "value": round(v, 2)} for t, v in latest.groupby("district_name")["exposure"].sum().items()],
        key=lambda r: -r["value"]),
    "turnaroundByDistrict": sorted(
        [{"district": t, "value": round(v, 2)} for t, v in alloc.groupby("district_name")["turn"].mean().items()],
        key=lambda r: -r["value"]),
    "demandVariance": [
        {"product": r.product_name, "category": r.category, "avg": round(r.avg, 1), "stdev": round(r.stdev, 1), "cv": round(r.cv, 2)}
        for r in dv.itertuples()],
    "stores": [],
}
for s in sd.itertuples():
    li = latest[latest.store_id == s.store_id]
    o = orders[orders.store_id == s.store_id]
    a = alloc[alloc.store_id == s.store_id]
    c = cc[cc.store_id == s.store_id]
    out["stores"].append({
        "store": s.store_name, "district": s.district_name,
        "parCompliance": round(li["ratio"].mean(), 4),
        "fulfillmentRate": round(rate(o), 4) if len(o) else None,
        "cycleAccuracy": round(c["acc"].mean(), 4) if len(c) else None,
        "turnaroundDays": round(a["turn"].mean(), 2),
        "reorderCost": round(li["exposure"].sum(), 2),
    })
out["stores"].sort(key=lambda r: r["parCompliance"])

blob = json.dumps(out, separators=(",", ":"))
if "--write" in sys.argv:
    p = "dashboard.html"
    h = open(p, encoding="utf-8").read()
    h2, n = re.subn(r'(<script[^>]*id="dashboard-data"[^>]*>)(.*?)(</script>)', lambda m: m.group(1) + blob + m.group(3), h, flags=re.S)
    assert n == 1
    open(p, "w", encoding="utf-8").write(h2)
    print("dashboard.html updated")
else:
    print(json.dumps(out, indent=1))
