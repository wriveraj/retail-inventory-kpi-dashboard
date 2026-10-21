# Case Study: Retail Inventory KPI Dashboard

**Tools:** Power BI · DAX · Python (pandas/numpy) · PostgreSQL (optional) · HTML/SVG
**GitHub:** [github.com/wriveraj/sap-field-inventory-kpi-dashboard](https://github.com/wriveraj/sap-field-inventory-kpi-dashboard)

---

## The Problem

A replenishment team running a multi-district store network keeps coming back to the same questions. Which district is carrying the most reorder exposure right now? Is a PAR compliance drop a blip or a trend? Is a stocking gap a demand problem or a speed problem? Which SKUs are too unpredictable for a standard reorder formula?

Those answers don't sit in an ERP screen. You have to pull the data out and model it. I wanted a project that shows that modeling work end to end, on data that is entirely synthetic and mine to share.

---

## What I Built

A synthetic dataset simulating a 4-district, 18-store retail network over 12 months (Aug 2025 to Jul 2026), generated with a seeded Python script so the numbers are reproducible. Nine tables: three dimensions and six facts.

| Table | Purpose |
|---|---|
| districts | 4 districts |
| stores | 18 stores (Supercenter / Neighborhood / Express), each tied to a district |
| products | Electronics, Small Appliances, Household, and Grocery catalog with unit cost |
| par_levels | Target stocking level per store and product |
| inventory_snapshots | Monthly on-hand quantity per store and product |
| pickup_orders | Buy-online-pick-up-in-store orders with Fulfilled / Delayed / Cancelled status |
| allocations | DC-to-store replenishment requests, from request to fulfillment |
| cycle_counts | Physical count vs. system-expected quantity |
| demand_history | Monthly units sold per store and product, for variance analysis |

Every number below was confirmed by querying the generated CSVs (`validate_data.py`), not just designed in as an assumption.

---

## The DAX Measures

Six core KPIs, plus three time-intelligence measures. The time intelligence is what shows a problem *emerging* instead of just reporting a snapshot.

**Core measures:**

- **Fulfillment Rate:** fulfilled pickup orders ÷ total orders
- **PAR Compliance %:** average on-hand as a share of each store/product's PAR target
- **Demand Variance (CV):** coefficient of variation per product, to flag SKUs too unpredictable for a standard reorder formula
- **Reorder Cost Exposure:** sum of (PAR gap × unit cost), with a latest-month variant for the headline card
- **Cycle Count Accuracy %:** how close physical counts land to system-expected quantity
- **Allocation Turnaround (Days):** average days from replenishment request to fulfillment

**Time intelligence:**

- **Fulfillment Rate MoM Δ:** month-over-month change
- **Reorder Cost Exposure, Rolling 3mo Avg:** smooths noise for a trend line
- **PAR Compliance %, Change vs. Start:** current value against the starting value, the measure that catches a slow slide a snapshot would miss

Full DAX is in `dax-measures.md`, written against the exact column names in `schema.sql`.

---

## What the Data Surfaced

1. **$18,933 in total reorder cost exposure** in the most recent month, with **78% of it ($14,736) in the Gulf Coast district alone.**
2. **Gulf Coast PAR compliance fell from 101% to 50%** over 12 months, while every other district held 96 to 103%. A widening gap, not a one-time miss.
3. **Gulf Coast DC-to-store turnaround averages 8.5 days**, nearly 3x the 3.0-day average elsewhere.
4. **Wireless Earbuds have over 3x the demand variability of the next most variable SKU** (CV 1.29 vs. 0.39), a candidate for safety-stock review rather than standard reorder logic.
5. **Overall pickup order fulfillment: 87.4%**, with 10.4% delayed and 2.2% cancelled.

Findings 2 and 3 matter most together. A district can be short on stock because it isn't ordering enough, or because its orders aren't arriving fast enough, and those get fixed by different people. The data says Gulf Coast is a turnaround problem that looks like a PAR problem.

---

## The Dashboard

Built as a standalone HTML dashboard to match the portfolio's dark/yellow theme, so no Power BI is needed to view it. `build_dashboard_data.py` computes every figure from the CSVs using the same definitions as the DAX. It shows KPI cards across the top, a PAR compliance line chart by district (where Gulf Coast visibly splits off), bar charts for reorder exposure and turnaround, a product table sorted by demand variance, and a store-level drill-down filterable by district.

---

## Why I Built This

I have spent 13 years in operations, from distribution center quality control to field inventory control, and these are the questions I ask before any replenishment call. This project rebuilds that analytical spine on data anyone can inspect: the same questions, the same kind of measures, and the same pressure to explain the answer to a district manager in one sentence.

The dashboard doesn't replace judgment. It's what I'd want on screen before that call: not a guess about where the problem is, a number.
