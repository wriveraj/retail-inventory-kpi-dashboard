# Retail Inventory KPI Dashboard

Synthetic dataset and interactive dashboard modeling a 4-district, 18-store retail network replenished from a distribution center over a trailing 12-month window (Aug 2025 to Jul 2026). Built to demonstrate Power BI and DAX modeling on everyday replenishment data: PAR levels, buy-online-pick-up-in-store order demand, DC-to-store allocations, and cycle counts.

**All data is synthetic.** No employer data, retailer data, real store names, or actual sales figures appear anywhere in this project. See `generate_data.py` for the full generation logic.

## Files

- `schema.sql`: relational schema (9 tables), Postgres-compatible
- `generate_data.py`: generator script (pandas/numpy, seeded for reproducibility)
- `data/*.csv`: generated output, ready to load directly into Power BI
- `validate_data.py`: re-derives the five headline findings from the CSVs
- `build_dashboard_data.py`: computes the numbers embedded in `dashboard.html`
- `dax-measures.md`: Power BI measures written against the schema's column names
- `dashboard.html`: standalone interactive dashboard, no Power BI required

## Loading into Power BI

Power BI → Get Data → Text/CSV → import each file in `data/`. Set relationships using the `*_id` columns per `schema.sql`. `districts`, `stores`, and `products` are dimension tables; the rest are fact tables keyed to them.

## Loading into Postgres (optional)

```bash
psql -d your_db -f schema.sql
psql -d your_db -c "\copy districts FROM 'data/districts.csv' CSV HEADER"
psql -d your_db -c "\copy stores FROM 'data/stores.csv' CSV HEADER"
psql -d your_db -c "\copy products FROM 'data/products.csv' CSV HEADER"
psql -d your_db -c "\copy par_levels FROM 'data/par_levels.csv' CSV HEADER"
psql -d your_db -c "\copy inventory_snapshots FROM 'data/inventory_snapshots.csv' CSV HEADER"
psql -d your_db -c "\copy pickup_orders FROM 'data/pickup_orders.csv' CSV HEADER"
psql -d your_db -c "\copy allocations FROM 'data/allocations.csv' CSV HEADER"
psql -d your_db -c "\copy cycle_counts FROM 'data/cycle_counts.csv' CSV HEADER"
psql -d your_db -c "\copy demand_history FROM 'data/demand_history.csv' CSV HEADER"
```

## Findings (validated against the generated output)

These numbers come from querying the generated CSVs directly (`python validate_data.py`), not from the assumptions designed into the generator:

1. **$18,933 in total reorder cost exposure** across the network in the most recent month (below-PAR gap × unit cost), with **78% of it ($14,736) concentrated in the Gulf Coast district alone.**
2. **Gulf Coast PAR compliance fell from 101% to 50%** over the 12-month window, while every other district held 96 to 103%. It is a widening gap, not a one-time miss.
3. **Gulf Coast DC-to-store turnaround averages 8.5 days**, nearly 3x the 3.0-day average everywhere else. The stocking gap is partly a *speed* problem, not just a *demand* problem.
4. **Wireless Earbuds have over 3x the demand variability of the next most variable SKU** (coefficient of variation 1.29 vs. 0.39), a candidate for safety-stock or PAR-formula review instead of standard reorder logic.
5. **Overall pickup order fulfillment rate: 87.4%**, with 10.4% delayed and 2.2% cancelled.

## Author

William Rivera Jr
Field Inventory Control Specialist & Data Analyst
Portfolio: [williamriverajr.com](https://williamriverajr.com)
LinkedIn: [linkedin.com/in/william-rivera-966230309](https://linkedin.com/in/william-rivera-966230309)
