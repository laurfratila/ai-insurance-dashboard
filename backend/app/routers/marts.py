from fastapi import APIRouter
from sqlalchemy import text
from ..db import engine

router = APIRouter(prefix="/api/marts", tags=["marts"])

@router.get("/claims_by_month")
def claims_by_month():
    sql = text("""
        SELECT month, claims_count, paid_sum
        FROM marts.claims_by_month
        ORDER BY month
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    # Convert date to ISO for JSON
    return [
        {"month": r["month"].isoformat(), "claims_count": int(r["claims_count"]), "paid_sum": float(r["paid_sum"])}
        for r in rows
    ]

@router.get("/loss_ratio_by_month")
def loss_ratio_by_month():
    sql = text("""
        SELECT month, premium_sum, paid_sum, loss_ratio_pct
        FROM marts.loss_ratio_by_month
        ORDER BY month
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    return [
        {
            "month": r["month"].isoformat(),
            "premium_sum": float(r["premium_sum"] or 0),
            "paid_sum": float(r["paid_sum"] or 0),
            "loss_ratio_pct": float(r["loss_ratio_pct"]) if r["loss_ratio_pct"] is not None else None
        }
        for r in rows
    ]

@router.get("/claims_by_county")
def claims_by_county():
    sql = text("""
        SELECT county, claims_count, paid_sum
        FROM marts.claims_by_county
        ORDER BY claims_count DESC, county
    """)
    with engine.begin() as conn:
        rows = conn.execute(sql).mappings().all()
    return [
        {"county": r["county"], "claims_count": int(r["claims_count"]), "paid_sum": float(r["paid_sum"])}
        for r in rows
    ]
