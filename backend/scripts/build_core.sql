-- Rebuild core tables from raw

-- Drop and recreate policies
DROP TABLE IF EXISTS core.policies CASCADE;
CREATE TABLE core.policies AS
SELECT
    policy_id,
    customer_id,
    product_type,
    CAST(start_date AS date)   AS start_date,
    CAST(end_date AS date)     AS end_date,
    status,
    channel,
    CAST(discount_pct AS numeric)   AS discount_pct,
    CAST(gross_premium AS numeric)  AS gross_premium
FROM raw.policies;

-- Index for performance
CREATE INDEX idx_core_policies_start_date ON core.policies(start_date);

-- Drop and recreate claims
DROP TABLE IF EXISTS core.claims CASCADE;
CREATE TABLE core.claims AS
SELECT
    claim_id,
    policy_id,
    product_type,
    CAST(loss_date AS date)    AS loss_date,
    peril,
    status,
    CAST(reserve AS numeric)   AS reserve,
    CAST(paid AS numeric)      AS paid,
    CAST(report_date AS date)  AS report_date,
    CAST(close_date AS date)   AS close_date,
    severity_band
FROM raw.claims;

CREATE INDEX idx_core_claims_loss_date ON core.claims(loss_date);

-- Drop and recreate customers
DROP TABLE IF EXISTS core.customers CASCADE;
CREATE TABLE core.customers AS
SELECT
    customer_id,
    full_name,
    email,
    phone,
    county_code,
    county_name,
    city,
    postal_code,
    CAST(crime_risk AS numeric),
    CAST(hail_risk AS numeric),
    CAST(flood_risk AS numeric),
    CAST(wind_risk AS numeric),
    CAST(fire_risk AS numeric),
    CAST(dob AS date) AS dob
FROM raw.customers;
