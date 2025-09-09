# Analytics Glossary & Table Notes
_Last updated: 2025-09-09 · Version: 0.1_

This document defines common fields/metrics used by the RAG API and serves as a human-readable citation source.

---

## Schemas & Join Keys
- **Schema:** `core`
- **Tables:**
  - `core.customers(customer_id, full_name, email, phone, county_code, county_name, city, postal_code, crime_risk, hail_risk, flood_risk, wind_risk, fire_risk, dob)`
  - `core.policies(policy_id, customer_id, product_type, start_date, end_date, status, channel, discount_pct, gross_premium)`
  - `core.claims(claim_id, policy_id, product_type, loss_date, peril, status, reserve, paid, report_date, close_date, severity_band)`
- **Approved joins:**
  - `policies.customer_id = customers.customer_id`
  - `claims.policy_id = policies.policy_id`

> **PII:** `customers.email`, `customers.phone`, `customers.dob` are masked by default in API responses.

---

## Definitions (KPIs / Terms)

### Active Policy
A row in `core.policies` where `status = 'active'`.  
Time-bounded “active on date D” means `start_date <= D <= end_date`.

### Gross Premium
`policies.gross_premium` — premium amount before any claims.  
For aggregates, use `SUM(policies.gross_premium)`.

### Discount %
`policies.discount_pct` — decimal fraction (e.g., 0.034 = 3.4%).

### Policy Count
Number of rows in `core.policies` meeting filters.  
For unique customers with a policy, use `COUNT(DISTINCT policies.customer_id)`.

### Claim Status
`claims.status` — typically `open`/`closed`.  
An **open claim** is any row where `status <> 'closed'`.

### Paid Amount
`claims.paid` — total paid so far on the claim (currency).

### Reserve
`claims.reserve` — outstanding reserved amount for the claim (currency).

### Severity Band
`claims.severity_band` — categorical bucket (`low`/`medium`/`high`) derived upstream.

### Risks (Customer-level)
`crime_risk`, `hail_risk`, `flood_risk`, `wind_risk`, `fire_risk` are numeric risk indicators on `core.customers`.  
Aggregations typically use `AVG(...)` or `PERCENTILE` (percentiles not exposed in phase-1).

---

## Common Aggregations (SQL hints)

- Policies by city and product:
  ```sql
  SELECT customers.city, policies.product_type, COUNT(*) AS policies
  FROM core.policies policies
  JOIN core.customers customers ON policies.customer_id = customers.customer_id
  WHERE policies.status = 'active'
  GROUP BY customers.city, policies.product_type;
