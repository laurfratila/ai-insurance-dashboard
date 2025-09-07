-- ─────────────────────────────────────────────────────────────
-- Claims per month (count + paid sum)
-- ─────────────────────────────────────────────────────────────
DROP MATERIALIZED VIEW IF EXISTS marts.claims_by_month;
CREATE MATERIALIZED VIEW marts.claims_by_month AS
SELECT
  date_trunc('month', c.loss_date)::date AS month,
  COUNT(*)                             AS claims_count,
  COALESCE(SUM(c.paid), 0)::numeric    AS paid_sum
FROM core.claims c
GROUP BY 1
ORDER BY 1;

CREATE INDEX IF NOT EXISTS idx_marts_claims_by_month_month
  ON marts.claims_by_month (month);

-- ─────────────────────────────────────────────────────────────
-- Premium per month (from policy start) + loss ratio
-- ─────────────────────────────────────────────────────────────
DROP MATERIALIZED VIEW IF EXISTS marts.loss_ratio_by_month;
CREATE MATERIALIZED VIEW marts.loss_ratio_by_month AS
WITH prem AS (
  SELECT date_trunc('month', p.start_date)::date AS month,
         SUM(p.gross_premium)::numeric          AS premium_sum
  FROM core.policies p
  GROUP BY 1
),
paid AS (
  SELECT date_trunc('month', c.loss_date)::date AS month,
         SUM(c.paid)::numeric                   AS paid_sum
  FROM core.claims c
  GROUP BY 1
)
SELECT
  prem.month,
  prem.premium_sum,
  COALESCE(paid.paid_sum, 0) AS paid_sum,
  CASE
    WHEN prem.premium_sum > 0
      THEN ROUND((COALESCE(paid.paid_sum, 0) / prem.premium_sum) * 100, 1)
    ELSE NULL
  END AS loss_ratio_pct
FROM prem
LEFT JOIN paid USING (month)
ORDER BY prem.month;

CREATE INDEX IF NOT EXISTS idx_marts_loss_ratio_by_month_month
  ON marts.loss_ratio_by_month (month);

-- ─────────────────────────────────────────────────────────────
-- Claims by county (topline for a choropleth)
-- ─────────────────────────────────────────────────────────────
-- Adjust join/field names if your generator uses a different county field.
-- Here we assume claims has a county_name or county_code via policies/customers if needed.
DROP MATERIALIZED VIEW IF EXISTS marts.claims_by_county;
CREATE MATERIALIZED VIEW marts.claims_by_county AS
SELECT
  COALESCE(cust.county_name, cust.county_code, 'UNKNOWN') AS county,
  COUNT(*)                                                AS claims_count,
  COALESCE(SUM(cl.paid), 0)::numeric                      AS paid_sum
FROM core.claims cl
JOIN core.policies p  ON p.policy_id = cl.policy_id
JOIN core.customers cust ON cust.customer_id = p.customer_id
GROUP BY 1
ORDER BY 2 DESC;

CREATE INDEX IF NOT EXISTS idx_marts_claims_by_county_county
  ON marts.claims_by_county (county);
