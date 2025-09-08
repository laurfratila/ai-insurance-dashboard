from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import text
from datetime import date
from ..db import engine

router = APIRouter(prefix="/api/overview", tags=["overview"])



@router.get("/loss_ratio_by_month", tags = ["overview"])
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
@router.get("/gwp_by_period", tags = ["overview"])
def gwp_by_period(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: str = Query("month", regex="^(month|quarter|year)$")
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    # Safe mapping to PostgreSQL date_trunc arguments
    valid_groupings = {"month", "quarter", "year"}
    if group_by not in valid_groupings:
        raise HTTPException(status_code=400, detail="Invalid group_by value")

    sql = text(f"""
        SELECT
            DATE_TRUNC(:group_by, month) AS period,
            SUM(gwp_sum) AS gwp_sum
        FROM marts.gwp_by_month
        WHERE month BETWEEN :start_date AND :end_date
        GROUP BY 1
        ORDER BY 1

    """)

    with engine.begin() as conn:
        rows = conn.execute(sql, {
            "group_by": group_by,
            "start_date": start_date,
            "end_date": end_date
        }).mappings().all()

    return {
        "metric": "gwp_by_period",
        "grouping": group_by,
        "data": [{"period": r["period"].isoformat(), "value": float(r["gwp_sum"])} for r in rows]
    }


@router.get("/claims_frequency_by_period", tags = ["overview"])
def claims_frequency_by_period(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: str = Query("month", regex="^(month|quarter|year)$")
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    sql = text(f"""
        SELECT
            DATE_TRUNC(:group_by, month) AS period,
            ROUND(AVG(claims_frequency), 4) AS avg_claims_frequency
        FROM marts.claims_frequency_by_month
        WHERE month BETWEEN :start_date AND :end_date
        GROUP BY 1
        ORDER BY 1
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql, {
            "group_by": group_by,
            "start_date": start_date,
            "end_date": end_date
        }).mappings().all()

    return {
        "metric": "claims_frequency_by_period",
        "grouping": group_by,
        "data": [{"period": r["period"].isoformat(), "value": float(r["avg_claims_frequency"])} for r in rows]
    }


@router.get("/avg_settlement_time_by_period", tags = ["overview"])
def avg_settlement_time_by_period(
    start_date: date = Query(...),
    end_date: date = Query(...),
    group_by: str = Query("month", regex="^(month|quarter|year)$")
):
    if start_date > end_date:
        raise HTTPException(status_code=400, detail="start_date must be before end_date")

    sql = text(f"""
        SELECT
            DATE_TRUNC(:group_by, month) AS period,
            ROUND(AVG(avg_settlement_days), 2) AS avg_days
        FROM marts.avg_settlement_time_by_month
        WHERE month BETWEEN :start_date AND :end_date
        GROUP BY 1
        ORDER BY 1
    """)

    with engine.begin() as conn:
        rows = conn.execute(sql, {
            "group_by": group_by,
            "start_date": start_date,
            "end_date": end_date
        }).mappings().all()

    return {
        "metric": "avg_settlement_time_by_period",
        "grouping": group_by,
        "data": [{"period": r["period"].isoformat(), "value": float(r["avg_days"])} for r in rows]
    }
