

# A tiny, realistic example shown to the model to anchor format.
# Keep this minimal to avoid excessive token usage.
EXAMPLE_PLAN = [
    {
        "view": "policies",
        "select": ["policies.product_type", "policies.channel", "policies.status"],
        "filters": [
            {"col": "customers.city", "op": "ILIKE", "val": "Cluj%"},
            {"col": "policies.status", "op": "=", "val": "active"}
        ],
        "joins": ["policies->customers"],
        "group_by": ["policies.product_type", "policies.channel", "policies.status"],
        "aggregations": ["count(*) as policies", "sum(policies.gross_premium) as premium"],
        "order_by": [{"col": "premium", "dir": "desc"}],
        "limit": 50
    },
    {
        "view": "claims",
        "select": [],
        "filters": [
            {"col": "claims.loss_date", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
        ],
        "joins": [],
        "group_by": [],
        "aggregations": [
            "sum(claims.paid) as total_paid",
            "sum(claims.reserve) as total_reserved"
        ],
        "order_by": [],
        "limit": 1
    },
    {
        "view": "policies",
        "select": [],
        "filters": [
            {"col": "policies.product_type", "op": "=", "val": "auto"}
        ],
        "joins": [],
        "group_by": [],
        "aggregations": ["avg(policies.gross_premium) as avg_premium"],
        "order_by": [],
        "limit": 1
    },
    {
    "view": "customers",
    "select": [],
    "filters": [],
    "joins": [],
    "group_by": [],
    "aggregations": [
        "count(*) FILTER (WHERE customers.dob BETWEEN '1993-01-01' AND '2003-12-31') as aged_20_30",
        "count(*) as total_customers"
    ],
    "order_by": [],
    "limit": 1
    },
    {
    "view": "claims",
    "select": ["customers.full_name", "policies.policy_id"],
    "filters": [
        {"col": "claims.loss_date", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": ["claims->policies", "policies->customers"],
    "group_by": ["customers.full_name", "policies.policy_id"],
    "aggregations": ["count(*) as claim_count"],
    "order_by": [{"col": "claim_count", "dir": "desc"}],
    "limit": 50
    },
{
    "view": "avg_settlement_days_by_month",
    "select": ["month_start", "avg_days"],
    "filters": [
        {"col": "avg_settlement_days_by_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
},
{
    "view": "avg_settlement_days_by_month",
    "select": ["month_start", "p90_days"],
    "filters": [
        {"col": "avg_settlement_days_by_month.month_start", "op": "=", "val": "2024-03-01"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [],
    "limit": 1
},
{
    "view": "cat_exposure_by_region",
    "select": ["region_key", "exposure_gwp"],
    "filters": [
        {"col": "cat_exposure_by_region.month_start", "op": "BETWEEN", "val": ["2024-04-01", "2024-06-30"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "exposure_gwp", "dir": "desc"}],
    "limit": 1
},
{
    "view": "claims_by_peril_month",
    "select": ["peril", "claims_count", "month_start"],
    "filters": [
        {"col": "claims_by_peril_month.month_start", "op": "=", "val": "2024-01-01"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "claims_count", "dir": "desc"}],
    "limit": 1
},
{
    "view": "backlog_by_age_bucket",
    "select": ["region_key", "bucket_90_plus"],
    "filters": [],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "region_key", "dir": "asc"}],
    "limit": 50
},
{
    "view": "cat_exposure_by_region",
    "select": ["region_key", "peril", "claims_count", "loss_paid"],
    "filters": [
        {"col": "cat_exposure_by_region.month_start", "op": "=", "val": "2024-07-01"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "loss_paid", "dir": "desc"}],
    "limit": 50
},
{
    "view": "channel_mix_by_month",
    "select": ["channel", "gwp", "policies"],
    "filters": [
        {"col": "channel_mix_by_month.month_start", "op": "=", "val": "2024-03-01"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "gwp", "dir": "desc"}],
    "limit": 10
},
{
    "view": "claim_severity_histogram",
    "select": ["severity_band", "claim_count", "pct_share"],
    "filters": [],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "claim_count", "dir": "desc"}],
    "limit": 10
},

{
    "view": "claims_by_county",
    "select": ["county", "claims_count", "paid_sum"],
    "filters": [],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "claims_count", "dir": "desc"}],
    "limit": 50
},
{
    "view": "claims_by_month",
    "select": ["month", "claims_count", "paid_sum"],
    "filters": [
        {"col": "claims_by_month.month", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month", "dir": "asc"}],
    "limit": 12
},
{
    "view": "claims_by_peril_month",
    "select": ["month_start", "peril", "claims_count", "paid_total", "avg_severity"],
    "filters": [
        {"col": "claims_by_peril_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 50
},
{
    "view": "claims_frequency_by_month",
    "select": ["month_start", "claims_count", "policies_in_force", "claims_frequency"],
    "filters": [
        {"col": "claims_frequency_by_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
},
{
    "view": "claims_paid_vs_reserve_by_month",
    "select": ["month_start", "paid_total", "reserve_total"],
    "filters": [
        {"col": "claims_paid_vs_reserve_by_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
},
{
    "view": "cross_sell_distribution",
    "select": ["products_count", "customers", "pct_share"],
    "filters": [
        {"col": "cross_sell_distribution.products_count", "op": ">=", "val": 3}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "products_count", "dir": "asc"}],
    "limit": 10
},
{
    "view": "customer_demographics",
    "select": ["age_band", "county_name", "customers"],
    "filters": [
        {"col": "customer_demographics.age_band", "op": "=", "val": "25-34"},
        {"col": "customer_demographics.county_name", "op": "ILIKE", "val": "Cluj%"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [],
    "limit": 1
},
{
    "view": "earned_premium_by_month",
    "select": ["month_start", "earned_premium"],
    "filters": [
        {"col": "earned_premium_by_month.month_start", "op": "=", "val": "2024-06-01"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [],
    "limit": 1
},
{
    "view": "fnol_by_day",
    "select": ["day", "fnol_count"],
    "filters": [
        {"col": "fnol_by_day.day", "op": "BETWEEN", "val": ["2024-04-01", "2024-04-30"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "day", "dir": "asc"}],
    "limit": 31
},
{
    "view": "gwp_by_month",
    "select": ["month_start", "gwp"],
    "filters": [
        {"col": "gwp_by_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
},
{
    "view": "loss_ratio_by_month",
    "select": ["month_start", "claims_paid", "earned_premium", "loss_ratio"],
    "filters": [
        {"col": "loss_ratio_by_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
},

{
    "view": "open_vs_closed_ratio_by_month",
    "select": ["month_start", "opened_count", "closed_count", "closed_to_open_ratio"],
    "filters": [
        {"col": "open_vs_closed_ratio_by_month.month_start", "op": "=", "val": "2024-03-01"}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [],
    "limit": 1
},
{
    "view": "retention_by_month",
    "select": ["month_start", "up_for_renewal", "renewed", "retention_rate"],
    "filters": [
        {"col": "retention_by_month.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
},
{
    "view": "sla_breaches_simple",
    "select": ["month_start", "breaches_gt_30d", "breaches_gt_60d", "still_open", "total_reported"],
    "filters": [
        {"col": "sla_breaches_simple.month_start", "op": "BETWEEN", "val": ["2024-01-01", "2024-12-31"]}
    ],
    "joins": [],
    "group_by": [],
    "aggregations": [],
    "order_by": [{"col": "month_start", "dir": "asc"}],
    "limit": 12
}
]
