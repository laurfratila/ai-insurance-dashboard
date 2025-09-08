from fastapi import APIRouter
from sqlalchemy import text
from app.db import engine

router = APIRouter(prefix="/api/admin", tags=["admin"])

MARTS = [
  "marts.calendar_months",
  "marts.policies_in_force_by_month",
  "marts.earned_premium_by_month",
  "marts.gwp_by_month",
  "marts.claims_paid_by_month",
  "marts.loss_ratio_by_month",
  "marts.claims_count_by_month",
  "marts.claims_frequency_by_month",
  "marts.avg_settlement_days_by_month",
  "marts.claims_paid_vs_reserve_by_month",
  "marts.claim_severity_histogram",
  "marts.open_vs_closed_ratio_by_month",
  "marts.claims_by_peril_month",
  "marts.cat_exposure_by_region",
  "marts.fnol_by_day",
  "marts.sla_breaches_simple",
  "marts.backlog_by_age_bucket",
  "marts.retention_by_month",
  "marts.cross_sell_distribution",
  "marts.channel_mix_by_month",
  "marts.customer_demographics",
]

@router.post("/refresh_marts")
def refresh_marts():
    with engine.begin() as conn:
        for v in MARTS:
            conn.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {v};"))
    return {"status": "refreshed", "views": MARTS}
