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

-- ─────────────────────────────────────────────────────────────
-- Gross Written Premium (GWP) by month -- Totalul banilor pe care o companie de asigurări îi primește de la 
-- clienți pentru polițele de asigurare emise într-o anumită perioadă — 
-- înainte de deducerea comisioanelor, reasigurărilor sau daunelor.
-- ─────────────────────────────────────────────────────────────
-- Totalul primelor brute subscrise (GWP) per lună calendaristică.
-- Se calculează din data de început a poliței și suma plătită.
-- Util pentru analizarea trendurilor de vânzări și venituri din prime.

CREATE MATERIALIZED VIEW IF NOT EXISTS marts.gwp_by_month AS
SELECT
    DATE_TRUNC('month', start_date) AS month,
    SUM(gross_premium) AS gwp_sum
FROM core.policies
GROUP BY 1
ORDER BY 1;

CREATE INDEX IF NOT EXISTS idx_marts_gwp_by_month_month
  ON marts.gwp_by_month (month);


-- ─────────────────────────────────────────────────────────────
-- Claims Frequency by month
-- Rata de frecvență a daunelor raportate lunar:
-- claims / polițe active
-- ─────────────────────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS marts.claims_frequency_by_month;
CREATE MATERIALIZED VIEW marts.claims_frequency_by_month AS
WITH claims AS (
  SELECT date_trunc('month', c.loss_date)::date AS month,
         COUNT(*) AS claim_count
  FROM core.claims c
  GROUP BY 1
),
policies AS (
  SELECT date_trunc('month', p.start_date)::date AS month,
         COUNT(*) AS policy_count
  FROM core.policies p
  GROUP BY 1
)
SELECT
  c.month,
  c.claim_count,
  p.policy_count,
  ROUND(c.claim_count::numeric / NULLIF(p.policy_count, 0), 4) AS claims_frequency
FROM claims c
JOIN policies p ON c.month = p.month
ORDER BY c.month;

CREATE INDEX IF NOT EXISTS idx_marts_claims_frequency_by_month
  ON marts.claims_frequency_by_month (month);


-- ─────────────────────────────────────────────────────────────
-- Average Settlement Time by month
-- Timpul mediu (în zile) necesar pentru soluționarea unui claim
-- Calculat ca diferența între settlement_date și claim_date
-- ─────────────────────────────────────────────────────────────

DROP MATERIALIZED VIEW IF EXISTS marts.avg_settlement_time_by_month;
CREATE MATERIALIZED VIEW marts.avg_settlement_time_by_month AS
SELECT
    DATE_TRUNC('month', loss_date)::date AS month,
    ROUND(AVG(close_date - loss_date), 2) AS avg_settlement_days
FROM core.claims
WHERE close_date IS NOT NULL
GROUP BY 1
ORDER BY 1;

CREATE INDEX IF NOT EXISTS idx_marts_avg_settlement_time_by_month
  ON marts.avg_settlement_time_by_month (month);
