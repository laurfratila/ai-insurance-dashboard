# backend/AI/LLM/schema.py

"""
Central allowlists and helpers for NL→Plan→SQL.

We only permit reads against three tables under schema `core`:
  - core.customers
  - core.policies
  - core.claims

This module is imported by the DSL validator and SQL compiler.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Set, Tuple

# -------------------------
# Core configuration
# -------------------------

DB_SCHEMA = "core"  # change here if your schema name differs

# Per-view allowed columns (case-sensitive, match DB)
ALLOWED_VIEWS: Dict[str, Dict[str, object]] = {
    "customers": {
        "schema": DB_SCHEMA,
        "columns": [
            "customer_id",
            "full_name",
            "email",         # PII (masked by default)
            "phone",         # PII (masked by default)
            "county_code",
            "county_name",
            "city",
            "postal_code",
            "crime_risk",
            "hail_risk",
            "flood_risk",
            "wind_risk",
            "fire_risk",
            "dob",           # PII (masked by default)
        ],
        "pii": ["email", "phone", "dob"],
    },
    "policies": {
        "schema": DB_SCHEMA,
        "columns": [
            "policy_id",
            "customer_id",
            "product_type",
            "start_date",
            "end_date",
            "status",
            "channel",
            "discount_pct",
            "gross_premium",
        ],
        "pii": [],
    },
    "claims": {
        "schema": DB_SCHEMA,
        "columns": [
            "claim_id",
            "policy_id",
            "product_type",
            "loss_date",
            "peril",
            "status",
            "reserve",
            "paid",
            "report_date",
            "close_date",
            "severity_band",
        ],
        "pii": [],
    },
    # NON-CORE VIEWS ----> MATERIALIZED VIEWS FROM marts_schema.sql
    "avg_settlement_days_by_month": {
        "schema": "marts",
        "columns": ["month_start", "closed_claims", "avg_days", "p50_days", "p90_days"],
        "pii": []
    },
    "backlog_by_age_bucket": {
        "schema": "marts",
        "columns": ["as_of", "region_key", "bucket_0_7", "bucket_8_30", "bucket_31_90", "bucket_90_plus", "total_open"],
        "pii": []
    },
    "calendar_months": {
        "schema": "marts",
        "columns": ["month_start"],
        "pii": []
    },
    "cat_exposure_by_region": {
        "schema": "marts",
        "columns": ["month_start", "region_key", "peril", "exposure_gwp", "claims_count", "loss_paid"],
        "pii": []
    },
    "channel_mix_by_month": {
        "schema": "marts",
        "columns": ["month_start", "channel", "gwp", "policies"],
        "pii": []
    },
    "claim_severity_histogram": {
        "schema": "marts",
        "columns": ["severity_band", "claim_count", "pct_share"],
        "pii": []
    },
    "claims_by_county": {
        "schema": "marts",
        "columns": ["county", "claims_count", "paid_sum"],
        "pii": []
    },
    "claims_by_month": {
        "schema": "marts",
        "columns": ["month", "claims_count", "paid_sum"],
        "pii": []
    },
    "claims_by_peril_month": {
        "schema": "marts",
        "columns": ["month_start", "peril", "claims_count", "paid_total", "avg_severity"],
        "pii": []
    },
    "claims_count_by_month": {
        "schema": "marts",
        "columns": ["month_start", "claims_count"],
        "pii": []
    },
    "policies_in_force_by_month": {
        "schema": "marts",
        "columns": ["month_start", "policies_in_force"],
        "pii": []
    },
    "claims_frequency_by_month": {
        "schema": "marts",
        "columns": ["month_start", "claims_count", "policies_in_force", "claims_frequency"],
        "pii": []
    },
    "claims_paid_by_month": {
        "schema": "marts",
        "columns": ["month_start", "claims_paid"],
        "pii": []
    },
    "claims_paid_vs_reserve_by_month": {
        "schema": "marts",
        "columns": ["month_start", "paid_total", "reserve_total"],
        "pii": []
    },
    "cross_sell_distribution": {
        "schema": "marts",
        "columns": ["products_count", "customers", "pct_share"],
        "pii": []
    },
    "customer_demographics": {
        "schema": "marts",
        "columns": ["age_band", "county_name", "customers"],
        "pii": []
    },
    "earned_premium_by_month": {
        "schema": "marts",
        "columns": ["month_start", "earned_premium"],
        "pii": []
    },
    "fnol_by_day": {
        "schema": "marts",
        "columns": ["day", "fnol_count"],
        "pii": []
    },
    "gwp_by_month": {
        "schema": "marts",
        "columns": ["month_start", "gwp"],
        "pii": []
    },
    "loss_ratio_by_month": {
        "schema": "marts",
        "columns": ["month_start", "claims_paid", "earned_premium", "loss_ratio"],
        "pii": []
    },
    "open_vs_closed_ratio_by_month": {
        "schema": "marts",
        "columns": ["month_start", "opened_count", "closed_count", "closed_to_open_ratio"],
        "pii": []
    },
    "retention_by_month": {
        "schema": "marts",
        "columns": ["month_start", "up_for_renewal", "renewed", "retention_rate"],
        "pii": []
    },
    "sla_breaches_simple": {
        "schema": "marts",
        "columns": ["month_start", "breaches_gt_30d", "breaches_gt_60d", "still_open", "total_reported"],
        "pii": []
        
    }
}

# Allowed join edges (left.col, right.col) in fully-qualified "view.column" form
JOIN_RULES: Set[Tuple[str, str]] = {
    ("policies.customer_id", "customers.customer_id"),
    ("claims.policy_id", "policies.policy_id"),
}

# Allowed scalar operators in WHERE
ALLOWED_OPERATORS: Set[str] = {"=", "<>", ">", ">=", "<", "<=", "ILIKE", "BETWEEN", "IN"}

# Limits
DEFAULT_LIMIT: int = 50
MAX_LIMIT: int = 200

# -------------------------
# Helper utilities
# -------------------------

def list_views() -> List[str]:
    return list(ALLOWED_VIEWS.keys())


def columns_for(view: str) -> List[str]:
    _assert_view(view)
    return list(ALLOWED_VIEWS[view]["columns"])  # type: ignore[index]


def pii_for(view: str) -> Set[str]:
    _assert_view(view)
    return set(ALLOWED_VIEWS[view]["pii"])  # type: ignore[index]


def fq(view: str) -> str:
    """Return fully-qualified table reference with alias identical to view name."""
    _assert_view(view)
    schema = ALLOWED_VIEWS[view]["schema"]  # type: ignore[index]
    return f'{schema}."{view}" {view}'


def is_allowed_column(qualified_col: str) -> bool:
    """
    Validate "view.column" is allowed by the schema.
    Accepts either "view.column" or just "column" (interpreted later by compiler).
    """
    if "." not in qualified_col:
        # Not fully qualified — the compiler will resolve/validate against FROM + JOINs
        return True
    view, col = qualified_col.split(".", 1)
    if view not in ALLOWED_VIEWS:
        return False
    return col in ALLOWED_VIEWS[view]["columns"]  # type: ignore[index]


def is_allowed_join(edge: str) -> bool:
    """
    Validate join shorthand like:
      "policies->customers"
      "claims->policies"
    """
    if "->" not in edge:
        return False
    left, right = edge.split("->", 1)
    # Expand to concrete allowed pairs (order-insensitive check)
    allowed = {
        ("policies.customer_id", "customers.customer_id"),
        ("customers.customer_id", "policies.customer_id"),
        ("claims.policy_id", "policies.policy_id"),
        ("policies.policy_id", "claims.policy_id"),
    }
    # We accept the edge only if it maps to one of the allowed column pairs
    if left == "policies" and right == "customers":
        return ("policies.customer_id", "customers.customer_id") in allowed
    if left == "claims" and right == "policies":
        return ("claims.policy_id", "policies.policy_id") in allowed
    return False


def _assert_view(view: str) -> None:
    if view not in ALLOWED_VIEWS:
        raise ValueError(f"Unknown view: {view}")


# Convenience: flat set of all "view.column" combos (useful for validation)
ALL_QUALIFIED_COLUMNS: Set[str] = {
    f"{v}.{c}"
    for v, spec in ALLOWED_VIEWS.items()
    for c in spec["columns"]  # type: ignore[index]
}

