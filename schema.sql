-- Retail Inventory KPI Dashboard: synthetic schema
-- Models a multi-district retail network replenished from a distribution center:
-- PAR levels, pickup order demand, DC-to-store allocations, and cycle counts.
-- All data is synthetic. No employer data, retailer data, or real store names
-- are used anywhere in this project.

CREATE TABLE districts (
    district_id    SERIAL PRIMARY KEY,
    district_name  VARCHAR(50) NOT NULL,
    region          VARCHAR(50) NOT NULL
);

CREATE TABLE stores (
    store_id         SERIAL PRIMARY KEY,
    store_name       VARCHAR(100) NOT NULL,
    district_id    INTEGER NOT NULL REFERENCES districts(district_id),
    store_type       VARCHAR(20) NOT NULL,   -- Supercenter, Neighborhood, Express
    state           VARCHAR(2) NOT NULL
);

CREATE TABLE products (
    product_id      SERIAL PRIMARY KEY,
    product_name    VARCHAR(100) NOT NULL,
    category        VARCHAR(30) NOT NULL,   -- Electronics, Small Appliances, Household, Grocery
    unit_cost       NUMERIC(10,2) NOT NULL
);

CREATE TABLE par_levels (
    par_id              SERIAL PRIMARY KEY,
    store_id             INTEGER NOT NULL REFERENCES stores(store_id),
    product_id          INTEGER NOT NULL REFERENCES products(product_id),
    par_qty             INTEGER NOT NULL,
    effective_start_date DATE NOT NULL,
    effective_end_date   DATE            -- NULL = currently active
);

CREATE TABLE inventory_snapshots (
    snapshot_id     SERIAL PRIMARY KEY,
    store_id         INTEGER NOT NULL REFERENCES stores(store_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    snapshot_date   DATE NOT NULL,
    on_hand_qty     INTEGER NOT NULL
);

CREATE TABLE pickup_orders (
    order_id         SERIAL PRIMARY KEY,
    store_id         INTEGER NOT NULL REFERENCES stores(store_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    order_date       DATE NOT NULL,
    qty_required    INTEGER NOT NULL,
    order_status     VARCHAR(20) NOT NULL   -- Fulfilled, Delayed, Cancelled
);

CREATE TABLE allocations (
    allocation_id       SERIAL PRIMARY KEY,
    destination_store_id INTEGER NOT NULL REFERENCES stores(store_id),
    product_id           INTEGER NOT NULL REFERENCES products(product_id),
    qty                   INTEGER NOT NULL,
    request_date          DATE NOT NULL,
    fulfilled_date        DATE            -- NULL = still open
);

CREATE TABLE cycle_counts (
    count_id        SERIAL PRIMARY KEY,
    store_id         INTEGER NOT NULL REFERENCES stores(store_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    count_date      DATE NOT NULL,
    expected_qty    INTEGER NOT NULL,
    actual_qty      INTEGER NOT NULL
);

CREATE TABLE demand_history (
    demand_id       SERIAL PRIMARY KEY,
    store_id         INTEGER NOT NULL REFERENCES stores(store_id),
    product_id      INTEGER NOT NULL REFERENCES products(product_id),
    usage_month     DATE NOT NULL,          -- first of month
    qty_used        INTEGER NOT NULL
);

CREATE INDEX idx_par_store_product ON par_levels(store_id, product_id);
CREATE INDEX idx_snapshot_store_date ON inventory_snapshots(store_id, snapshot_date);
CREATE INDEX idx_orders_store_date ON pickup_orders(store_id, order_date);
CREATE INDEX idx_allocations_dest ON allocations(destination_store_id);
CREATE INDEX idx_demand_store_month ON demand_history(store_id, usage_month);
