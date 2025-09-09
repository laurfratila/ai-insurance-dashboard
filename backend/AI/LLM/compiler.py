# backend/AI/LLM/compiler.py

"""
Compile a validated Plan into parameterized SQL.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .dsl import Plan, Filter
from .schema import fq, DEFAULT_LIMIT


# -------------------------
# Public API
# -------------------------

def compile_sql(plan: Plan) -> Tuple[str, Dict[str, object]]:
    """
    Turn a validated Plan into a parameterized SQL string and params dict.
    Assumes Plan has passed dsl.Plan validation (columns/joins/operators).
    """
    params: Dict[str, object] = {}

    # FROM + JOINS
    from_clause = f"FROM {fq(plan.view)}"
    join_sql = _compile_joins(plan.joins)

    # SELECT
    select_sql = _compile_select(plan)

    # WHERE
    where_sql, where_params = _compile_where(plan.filters)
    params.update(where_params)

    # GROUP BY
    group_sql = _compile_group_by(plan)

    # ORDER BY
    order_sql = _compile_order_by(plan)

    # LIMIT
    limit_val = plan.limit or DEFAULT_LIMIT
    limit_sql = f"LIMIT {int(limit_val)}"

    sql = f"{select_sql} {from_clause} {join_sql} {where_sql} {group_sql} {order_sql} {limit_sql};".strip()
    return sql, params


# -------------------------
# Helpers
# -------------------------

def _compile_joins(joins: List[str]) -> str:
    parts: List[str] = []
    for j in joins:
        if j == "policies->customers":
            parts.append('JOIN core."customers" customers ON policies.customer_id = customers.customer_id')
        elif j == "claims->policies":
            parts.append('JOIN core."policies" policies ON claims.policy_id = policies.policy_id')
        else:
            raise ValueError(f"Unsupported join: {j}")
    return " ".join(parts)


def _compile_select(plan: Plan) -> str:
    cols: List[str] = []
    if plan.qualified_select:
        cols.extend(plan.qualified_select)
    if plan.aggregations:
        cols.extend(plan.aggregations)
    # Fallback to base.* if nothing selected
    if not cols:
        cols = [f"{plan.view}.*"]
    return "SELECT " + ", ".join(cols)


def _compile_where(filters: List[Filter]) -> Tuple[str, Dict[str, object]]:
    if not filters:
        return "", {}

    clauses: List[str] = []
    params: Dict[str, object] = {}

    for i, f in enumerate(filters):
        p = f"p{i}"
        op = f.op
        col = f.col if "." in f.col else f.col  # already validated; can be unqualified if resolved later
        if op == "BETWEEN":
            clauses.append(f"{col} BETWEEN :{p}a AND :{p}b")
            if not isinstance(f.val, list) or len(f.val) != 2:
                raise ValueError("BETWEEN requires [start, end]")
            params[f"{p}a"] = f.val[0]
            params[f"{p}b"] = f.val[1]
        elif op == "IN":
            clauses.append(f"{col} = ANY(:{p})")
            if not isinstance(f.val, list) or len(f.val) == 0:
                raise ValueError("IN requires a non-empty list")
            params[p] = list(f.val)
        else:
            clauses.append(f"{col} {op} :{p}")
            params[p] = f.val

    return "WHERE " + " AND ".join(clauses), params


def _compile_group_by(plan: Plan) -> str:
    if not plan.qualified_group_by:
        return ""
    return "GROUP BY " + ", ".join(plan.qualified_group_by)


def _compile_order_by(plan: Plan) -> str:
    if not plan.qualified_order_by:
        return ""
    parts = [f"{col} {direction.upper()}" for col, direction in plan.qualified_order_by]
    return "ORDER BY " + ", ".join(parts)
