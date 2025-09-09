--
-- PostgreSQL database dump
--

\restrict h27QkrI3YrkQssPh7shMCu6VINBjDCvQuqtmAgxvAHu1fNL6eG7BPYZsU5d54OU

-- Dumped from database version 16.10 (Debian 16.10-1.pgdg13+1)
-- Dumped by pg_dump version 16.10 (Debian 16.10-1.pgdg13+1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: marts; Type: SCHEMA; Schema: -; Owner: appuser
--

CREATE SCHEMA marts;


ALTER SCHEMA marts OWNER TO appuser;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: avg_settlement_days_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.avg_settlement_days_by_month AS
 WITH base AS (
         SELECT (date_trunc('month'::text, (c.close_date)::timestamp with time zone))::date AS month_start,
            (c.close_date - c.report_date) AS settlement_days
           FROM core.claims c
          WHERE ((c.close_date IS NOT NULL) AND (c.report_date IS NOT NULL))
        )
 SELECT month_start,
    count(*) AS closed_claims,
    avg(settlement_days) AS avg_days,
    percentile_cont((0.5)::double precision) WITHIN GROUP (ORDER BY ((settlement_days)::double precision)) AS p50_days,
    percentile_cont((0.9)::double precision) WITHIN GROUP (ORDER BY ((settlement_days)::double precision)) AS p90_days
   FROM base
  GROUP BY month_start
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.avg_settlement_days_by_month OWNER TO appuser;

--
-- Name: backlog_by_age_bucket; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.backlog_by_age_bucket AS
 WITH open_claims AS (
         SELECT c.claim_id,
            COALESCE(NULLIF(TRIM(BOTH FROM cu.county_name), ''::text), 'UNKNOWN'::text) AS region_key,
            c.report_date,
            CURRENT_DATE AS as_of,
            (CURRENT_DATE - c.report_date) AS age_days
           FROM ((core.claims c
             LEFT JOIN core.policies p ON ((p.policy_id = c.policy_id)))
             LEFT JOIN core.customers cu ON ((cu.customer_id = p.customer_id)))
          WHERE (c.close_date IS NULL)
        )
 SELECT as_of,
    region_key,
    count(*) FILTER (WHERE ((age_days >= 0) AND (age_days <= 7))) AS bucket_0_7,
    count(*) FILTER (WHERE ((age_days >= 8) AND (age_days <= 30))) AS bucket_8_30,
    count(*) FILTER (WHERE ((age_days >= 31) AND (age_days <= 90))) AS bucket_31_90,
    count(*) FILTER (WHERE (age_days > 90)) AS bucket_90_plus,
    count(*) AS total_open
   FROM open_claims
  GROUP BY as_of, region_key
  ORDER BY as_of DESC, region_key
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.backlog_by_age_bucket OWNER TO appuser;

--
-- Name: calendar_months; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.calendar_months AS
 WITH bounds AS (
         SELECT date_trunc('month'::text, (LEAST(COALESCE(( SELECT min(policies.start_date) AS min
                   FROM core.policies), CURRENT_DATE), COALESCE(( SELECT min(claims.report_date) AS min
                   FROM core.claims), CURRENT_DATE)))::timestamp with time zone) AS min_m,
            date_trunc('month'::text, (CURRENT_DATE + '1 mon'::interval)) AS max_m
        )
 SELECT (generate_series(min_m, (max_m)::timestamp with time zone, '1 mon'::interval))::date AS month_start
   FROM bounds
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.calendar_months OWNER TO appuser;

--
-- Name: cat_exposure_by_region; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.cat_exposure_by_region AS
 WITH pol AS (
         SELECT COALESCE(NULLIF(TRIM(BOTH FROM cu.county_name), ''::text), 'UNKNOWN'::text) AS region_key,
            (date_trunc('month'::text, (p.start_date)::timestamp with time zone))::date AS month_start,
            sum(COALESCE(p.gross_premium, (0)::numeric)) AS exposure_gwp
           FROM (core.policies p
             LEFT JOIN core.customers cu ON ((cu.customer_id = p.customer_id)))
          GROUP BY COALESCE(NULLIF(TRIM(BOTH FROM cu.county_name), ''::text), 'UNKNOWN'::text), ((date_trunc('month'::text, (p.start_date)::timestamp with time zone))::date)
        ), clm AS (
         SELECT COALESCE(NULLIF(TRIM(BOTH FROM cu.county_name), ''::text), 'UNKNOWN'::text) AS region_key,
            (date_trunc('month'::text, (c.report_date)::timestamp with time zone))::date AS month_start,
            COALESCE(NULLIF(TRIM(BOTH FROM c.peril), ''::text), 'UNKNOWN'::text) AS peril,
            count(*) AS claims_count,
            sum(COALESCE(c.paid, (0)::numeric)) AS loss_paid
           FROM ((core.claims c
             LEFT JOIN core.policies p ON ((p.policy_id = c.policy_id)))
             LEFT JOIN core.customers cu ON ((cu.customer_id = p.customer_id)))
          GROUP BY COALESCE(NULLIF(TRIM(BOTH FROM cu.county_name), ''::text), 'UNKNOWN'::text), ((date_trunc('month'::text, (c.report_date)::timestamp with time zone))::date), COALESCE(NULLIF(TRIM(BOTH FROM c.peril), ''::text), 'UNKNOWN'::text)
        )
 SELECT COALESCE(clm.month_start, pol.month_start) AS month_start,
    COALESCE(clm.region_key, pol.region_key) AS region_key,
    COALESCE(clm.peril, 'ALL'::text) AS peril,
    COALESCE(pol.exposure_gwp, (0)::numeric) AS exposure_gwp,
    COALESCE(clm.claims_count, (0)::bigint) AS claims_count,
    COALESCE(clm.loss_paid, (0)::numeric) AS loss_paid
   FROM (pol
     FULL JOIN clm ON (((pol.region_key = clm.region_key) AND (pol.month_start = clm.month_start))))
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.cat_exposure_by_region OWNER TO appuser;

--
-- Name: channel_mix_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.channel_mix_by_month AS
 SELECT (date_trunc('month'::text, (start_date)::timestamp with time zone))::date AS month_start,
    COALESCE(NULLIF(TRIM(BOTH FROM channel), ''::text), 'UNKNOWN'::text) AS channel,
    sum(COALESCE(gross_premium, (0)::numeric)) AS gwp,
    count(*) AS policies
   FROM core.policies p
  GROUP BY ((date_trunc('month'::text, (start_date)::timestamp with time zone))::date), COALESCE(NULLIF(TRIM(BOTH FROM channel), ''::text), 'UNKNOWN'::text)
  ORDER BY ((date_trunc('month'::text, (start_date)::timestamp with time zone))::date), COALESCE(NULLIF(TRIM(BOTH FROM channel), ''::text), 'UNKNOWN'::text)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.channel_mix_by_month OWNER TO appuser;

--
-- Name: claim_severity_histogram; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claim_severity_histogram AS
 WITH base AS (
         SELECT COALESCE(NULLIF(TRIM(BOTH FROM claims.severity_band), ''::text), 'UNKNOWN'::text) AS severity_band
           FROM core.claims
        )
 SELECT severity_band,
    count(*) AS claim_count,
    round(((100.0 * (count(*))::numeric) / sum(count(*)) OVER ()), 2) AS pct_share
   FROM base
  GROUP BY severity_band
  ORDER BY (count(*)) DESC
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claim_severity_histogram OWNER TO appuser;

--
-- Name: claims_by_county; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_by_county AS
 SELECT COALESCE(cust.county_name, cust.county_code, 'UNKNOWN'::text) AS county,
    count(*) AS claims_count,
    COALESCE(sum(cl.paid), (0)::numeric) AS paid_sum
   FROM ((core.claims cl
     JOIN core.policies p ON ((p.policy_id = cl.policy_id)))
     JOIN core.customers cust ON ((cust.customer_id = p.customer_id)))
  GROUP BY COALESCE(cust.county_name, cust.county_code, 'UNKNOWN'::text)
  ORDER BY (count(*)) DESC
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_by_county OWNER TO appuser;

--
-- Name: claims_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_by_month AS
 SELECT (date_trunc('month'::text, (loss_date)::timestamp with time zone))::date AS month,
    count(*) AS claims_count,
    COALESCE(sum(paid), (0)::numeric) AS paid_sum
   FROM core.claims c
  GROUP BY ((date_trunc('month'::text, (loss_date)::timestamp with time zone))::date)
  ORDER BY ((date_trunc('month'::text, (loss_date)::timestamp with time zone))::date)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_by_month OWNER TO appuser;

--
-- Name: claims_by_peril_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_by_peril_month AS
 SELECT (date_trunc('month'::text, (report_date)::timestamp with time zone))::date AS month_start,
    COALESCE(NULLIF(TRIM(BOTH FROM peril), ''::text), 'UNKNOWN'::text) AS peril,
    count(*) AS claims_count,
    sum(COALESCE(paid, (0)::numeric)) AS paid_total,
    avg(NULLIF(paid, (0)::numeric)) AS avg_severity
   FROM core.claims c
  GROUP BY ((date_trunc('month'::text, (report_date)::timestamp with time zone))::date), COALESCE(NULLIF(TRIM(BOTH FROM peril), ''::text), 'UNKNOWN'::text)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_by_peril_month OWNER TO appuser;

--
-- Name: claims_count_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_count_by_month AS
 SELECT (date_trunc('month'::text, (report_date)::timestamp with time zone))::date AS month_start,
    count(*) AS claims_count
   FROM core.claims c
  GROUP BY ((date_trunc('month'::text, (report_date)::timestamp with time zone))::date)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_count_by_month OWNER TO appuser;

--
-- Name: policies_in_force_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.policies_in_force_by_month AS
 SELECT m.month_start,
    count(p.policy_id) AS policies_in_force
   FROM (marts.calendar_months m
     JOIN core.policies p ON ((daterange((date_trunc('month'::text, (p.start_date)::timestamp with time zone))::date, (((date_trunc('month'::text, (p.end_date)::timestamp with time zone))::date + '1 mon'::interval))::date, '[]'::text) @> m.month_start)))
  GROUP BY m.month_start
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.policies_in_force_by_month OWNER TO appuser;

--
-- Name: claims_frequency_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_frequency_by_month AS
 SELECT m.month_start,
    COALESCE(cc.claims_count, (0)::bigint) AS claims_count,
    COALESCE(pif.policies_in_force, (0)::bigint) AS policies_in_force,
        CASE
            WHEN (COALESCE(pif.policies_in_force, (0)::bigint) = 0) THEN NULL::numeric
            ELSE ((COALESCE(cc.claims_count, (0)::bigint))::numeric / (pif.policies_in_force)::numeric)
        END AS claims_frequency
   FROM ((marts.calendar_months m
     LEFT JOIN marts.claims_count_by_month cc ON ((cc.month_start = m.month_start)))
     LEFT JOIN marts.policies_in_force_by_month pif ON ((pif.month_start = m.month_start)))
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_frequency_by_month OWNER TO appuser;

--
-- Name: claims_paid_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_paid_by_month AS
 SELECT (date_trunc('month'::text, (close_date)::timestamp with time zone))::date AS month_start,
    sum(COALESCE(paid, (0)::numeric)) AS claims_paid
   FROM core.claims c
  WHERE (close_date IS NOT NULL)
  GROUP BY ((date_trunc('month'::text, (close_date)::timestamp with time zone))::date)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_paid_by_month OWNER TO appuser;

--
-- Name: claims_paid_vs_reserve_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.claims_paid_vs_reserve_by_month AS
 WITH paid_m AS (
         SELECT (date_trunc('month'::text, (c.close_date)::timestamp with time zone))::date AS month_start,
            sum(COALESCE(c.paid, (0)::numeric)) AS paid_total
           FROM core.claims c
          WHERE (c.close_date IS NOT NULL)
          GROUP BY ((date_trunc('month'::text, (c.close_date)::timestamp with time zone))::date)
        ), reserve_m AS (
         SELECT (date_trunc('month'::text, (c.report_date)::timestamp with time zone))::date AS month_start,
            sum(COALESCE(c.reserve, (0)::numeric)) AS reserve_total
           FROM core.claims c
          WHERE (c.report_date IS NOT NULL)
          GROUP BY ((date_trunc('month'::text, (c.report_date)::timestamp with time zone))::date)
        )
 SELECT COALESCE(p.month_start, r.month_start) AS month_start,
    COALESCE(p.paid_total, (0)::numeric) AS paid_total,
    COALESCE(r.reserve_total, (0)::numeric) AS reserve_total
   FROM (paid_m p
     FULL JOIN reserve_m r USING (month_start))
  ORDER BY COALESCE(p.month_start, r.month_start)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.claims_paid_vs_reserve_by_month OWNER TO appuser;

--
-- Name: cross_sell_distribution; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.cross_sell_distribution AS
 WITH distinct_products AS (
         SELECT p.customer_id,
            p.product_type
           FROM core.policies p
          WHERE (p.product_type IS NOT NULL)
          GROUP BY p.customer_id, p.product_type
        ), counts AS (
         SELECT distinct_products.customer_id,
            count(*) AS products_count
           FROM distinct_products
          GROUP BY distinct_products.customer_id
        )
 SELECT products_count,
    count(*) AS customers,
    round(((100.0 * (count(*))::numeric) / sum(count(*)) OVER ()), 2) AS pct_share
   FROM counts
  GROUP BY products_count
  ORDER BY products_count
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.cross_sell_distribution OWNER TO appuser;

--
-- Name: customer_demographics; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.customer_demographics AS
 WITH base AS (
         SELECT c.customer_id,
            COALESCE(NULLIF(TRIM(BOTH FROM c.county_name), ''::text), 'UNKNOWN'::text) AS county_name,
                CASE
                    WHEN (c.dob IS NOT NULL) THEN (date_part('year'::text, age((CURRENT_DATE)::timestamp with time zone, (c.dob)::timestamp with time zone)))::integer
                    ELSE NULL::integer
                END AS age_years
           FROM core.customers c
        ), banded AS (
         SELECT base.customer_id,
            base.county_name,
                CASE
                    WHEN (base.age_years IS NULL) THEN 'UNKNOWN'::text
                    WHEN (base.age_years < 25) THEN '<25'::text
                    WHEN ((base.age_years >= 25) AND (base.age_years <= 34)) THEN '25-34'::text
                    WHEN ((base.age_years >= 35) AND (base.age_years <= 44)) THEN '35-44'::text
                    WHEN ((base.age_years >= 45) AND (base.age_years <= 54)) THEN '45-54'::text
                    WHEN ((base.age_years >= 55) AND (base.age_years <= 64)) THEN '55-64'::text
                    ELSE '65+'::text
                END AS age_band
           FROM base
        )
 SELECT age_band,
    county_name,
    count(*) AS customers
   FROM banded
  GROUP BY age_band, county_name
  ORDER BY age_band, county_name
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.customer_demographics OWNER TO appuser;

--
-- Name: earned_premium_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.earned_premium_by_month AS
 WITH spans AS (
         SELECT p.policy_id,
            p.gross_premium,
            GREATEST((date_trunc('month'::text, (p.start_date)::timestamp with time zone))::date, ( SELECT min(calendar_months.month_start) AS min
                   FROM marts.calendar_months)) AS span_start,
            LEAST((date_trunc('month'::text, (p.end_date)::timestamp with time zone))::date, ( SELECT max(calendar_months.month_start) AS max
                   FROM marts.calendar_months)) AS span_end
           FROM core.policies p
        ), month_span AS (
         SELECT s.policy_id,
            m.month_start,
            s.gross_premium,
            GREATEST((1)::double precision, date_part('month'::text, age((s.span_end + '1 mon'::interval), (s.span_start)::timestamp without time zone))) AS months_in_term
           FROM (spans s
             JOIN marts.calendar_months m ON (((m.month_start >= s.span_start) AND (m.month_start <= s.span_end))))
        )
 SELECT month_start,
    sum(((gross_premium)::double precision / months_in_term)) AS earned_premium
   FROM month_span
  GROUP BY month_start
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.earned_premium_by_month OWNER TO appuser;

--
-- Name: fnol_by_day; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.fnol_by_day AS
 SELECT report_date AS day,
    count(*) AS fnol_count
   FROM core.claims c
  WHERE (report_date IS NOT NULL)
  GROUP BY report_date
  ORDER BY report_date
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.fnol_by_day OWNER TO appuser;

--
-- Name: gwp_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.gwp_by_month AS
 SELECT (date_trunc('month'::text, (start_date)::timestamp with time zone))::date AS month_start,
    sum(gross_premium) AS gwp
   FROM core.policies p
  GROUP BY ((date_trunc('month'::text, (start_date)::timestamp with time zone))::date)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.gwp_by_month OWNER TO appuser;

--
-- Name: loss_ratio_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.loss_ratio_by_month AS
 SELECT m.month_start,
    COALESCE(p.claims_paid, (0)::numeric) AS claims_paid,
    COALESCE(e.earned_premium, (0)::double precision) AS earned_premium,
        CASE
            WHEN (COALESCE(e.earned_premium, (0)::double precision) = (0)::double precision) THEN NULL::double precision
            ELSE ((COALESCE(p.claims_paid, (0)::numeric))::double precision / e.earned_premium)
        END AS loss_ratio
   FROM ((marts.calendar_months m
     LEFT JOIN marts.claims_paid_by_month p ON ((p.month_start = m.month_start)))
     LEFT JOIN marts.earned_premium_by_month e ON ((e.month_start = m.month_start)))
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.loss_ratio_by_month OWNER TO appuser;

--
-- Name: open_vs_closed_ratio_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.open_vs_closed_ratio_by_month AS
 WITH opened AS (
         SELECT (date_trunc('month'::text, (claims.report_date)::timestamp with time zone))::date AS month_start,
            count(*) AS opened_count
           FROM core.claims
          WHERE (claims.report_date IS NOT NULL)
          GROUP BY ((date_trunc('month'::text, (claims.report_date)::timestamp with time zone))::date)
        ), closed AS (
         SELECT (date_trunc('month'::text, (claims.close_date)::timestamp with time zone))::date AS month_start,
            count(*) AS closed_count
           FROM core.claims
          WHERE (claims.close_date IS NOT NULL)
          GROUP BY ((date_trunc('month'::text, (claims.close_date)::timestamp with time zone))::date)
        )
 SELECT COALESCE(o.month_start, c.month_start) AS month_start,
    COALESCE(o.opened_count, (0)::bigint) AS opened_count,
    COALESCE(c.closed_count, (0)::bigint) AS closed_count,
        CASE
            WHEN (COALESCE(o.opened_count, (0)::bigint) = 0) THEN NULL::numeric
            ELSE ((COALESCE(c.closed_count, (0)::bigint))::numeric / (o.opened_count)::numeric)
        END AS closed_to_open_ratio
   FROM (opened o
     FULL JOIN closed c USING (month_start))
  ORDER BY COALESCE(o.month_start, c.month_start)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.open_vs_closed_ratio_by_month OWNER TO appuser;

--
-- Name: retention_by_month; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.retention_by_month AS
 WITH ranked AS (
         SELECT p.customer_id,
            p.policy_id,
            p.product_type,
            p.start_date,
            p.end_date,
            lead(p.start_date) OVER (PARTITION BY p.customer_id, p.product_type ORDER BY p.start_date) AS next_start_same_type
           FROM core.policies p
        ), eligible AS (
         SELECT (date_trunc('month'::text, (ranked.end_date)::timestamp with time zone))::date AS month_start,
            count(*) AS up_for_renewal,
            count(*) FILTER (WHERE ((ranked.next_start_same_type IS NOT NULL) AND (ranked.next_start_same_type <= (ranked.end_date + '30 days'::interval)))) AS renewed
           FROM ranked
          WHERE (ranked.end_date IS NOT NULL)
          GROUP BY ((date_trunc('month'::text, (ranked.end_date)::timestamp with time zone))::date)
        )
 SELECT month_start,
    up_for_renewal,
    renewed,
        CASE
            WHEN (up_for_renewal = 0) THEN NULL::numeric
            ELSE ((renewed)::numeric / (up_for_renewal)::numeric)
        END AS retention_rate
   FROM eligible
  ORDER BY month_start
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.retention_by_month OWNER TO appuser;

--
-- Name: sla_breaches_simple; Type: MATERIALIZED VIEW; Schema: marts; Owner: appuser
--

CREATE MATERIALIZED VIEW marts.sla_breaches_simple AS
 WITH base AS (
         SELECT c.claim_id,
            c.report_date,
            c.close_date,
                CASE
                    WHEN ((c.close_date IS NULL) OR (c.report_date IS NULL)) THEN NULL::integer
                    ELSE (c.close_date - c.report_date)
                END AS settlement_days
           FROM core.claims c
          WHERE (c.report_date IS NOT NULL)
        )
 SELECT (date_trunc('month'::text, (report_date)::timestamp without time zone))::date AS month_start,
    count(*) FILTER (WHERE ((settlement_days IS NOT NULL) AND (settlement_days > 30))) AS breaches_gt_30d,
    count(*) FILTER (WHERE ((settlement_days IS NOT NULL) AND (settlement_days > 60))) AS breaches_gt_60d,
    count(*) FILTER (WHERE (settlement_days IS NULL)) AS still_open,
    count(*) AS total_reported
   FROM base
  GROUP BY ((date_trunc('month'::text, (report_date)::timestamp without time zone))::date)
  ORDER BY ((date_trunc('month'::text, (report_date)::timestamp without time zone))::date)
  WITH NO DATA;


ALTER MATERIALIZED VIEW marts.sla_breaches_simple OWNER TO appuser;

--
-- Name: idx_marts_claims_by_county_county; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX idx_marts_claims_by_county_county ON marts.claims_by_county USING btree (county);


--
-- Name: idx_marts_claims_by_month_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX idx_marts_claims_by_month_month ON marts.claims_by_month USING btree (month);


--
-- Name: ix_avg_settlement_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_avg_settlement_month ON marts.avg_settlement_days_by_month USING btree (month_start);


--
-- Name: ix_backlog_asof_region; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_backlog_asof_region ON marts.backlog_by_age_bucket USING btree (as_of, region_key);


--
-- Name: ix_calendar_months_month_start; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_calendar_months_month_start ON marts.calendar_months USING btree (month_start);


--
-- Name: ix_cat_exposure_region_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_cat_exposure_region_month ON marts.cat_exposure_by_region USING btree (region_key, month_start, peril);


--
-- Name: ix_channel_mix_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_channel_mix_month ON marts.channel_mix_by_month USING btree (month_start, channel);


--
-- Name: ix_claim_severity_band; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_claim_severity_band ON marts.claim_severity_histogram USING btree (severity_band);


--
-- Name: ix_claims_by_peril_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_claims_by_peril_month ON marts.claims_by_peril_month USING btree (month_start, peril);


--
-- Name: ix_claims_count_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_claims_count_month ON marts.claims_count_by_month USING btree (month_start);


--
-- Name: ix_claims_freq_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_claims_freq_month ON marts.claims_frequency_by_month USING btree (month_start);


--
-- Name: ix_claims_paid_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_claims_paid_month ON marts.claims_paid_by_month USING btree (month_start);


--
-- Name: ix_claims_paid_reserve_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_claims_paid_reserve_month ON marts.claims_paid_vs_reserve_by_month USING btree (month_start);


--
-- Name: ix_cross_sell_products_count; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_cross_sell_products_count ON marts.cross_sell_distribution USING btree (products_count);


--
-- Name: ix_cust_demo_age_county; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_cust_demo_age_county ON marts.customer_demographics USING btree (age_band, county_name);


--
-- Name: ix_earned_premium_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_earned_premium_month ON marts.earned_premium_by_month USING btree (month_start);


--
-- Name: ix_fnol_day; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_fnol_day ON marts.fnol_by_day USING btree (day);


--
-- Name: ix_gwp_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_gwp_month ON marts.gwp_by_month USING btree (month_start);


--
-- Name: ix_loss_ratio_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_loss_ratio_month ON marts.loss_ratio_by_month USING btree (month_start);


--
-- Name: ix_open_closed_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_open_closed_month ON marts.open_vs_closed_ratio_by_month USING btree (month_start);


--
-- Name: ix_pif_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_pif_month ON marts.policies_in_force_by_month USING btree (month_start);


--
-- Name: ix_retention_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_retention_month ON marts.retention_by_month USING btree (month_start);


--
-- Name: ix_sla_breaches_month; Type: INDEX; Schema: marts; Owner: appuser
--

CREATE INDEX ix_sla_breaches_month ON marts.sla_breaches_simple USING btree (month_start);


--
-- PostgreSQL database dump complete
--

\unrestrict h27QkrI3YrkQssPh7shMCu6VINBjDCvQuqtmAgxvAHu1fNL6eG7BPYZsU5d54OU

