# backend/AI/LLM/dsl.py

"""
Plan (mini-DSL) for safe NL→SQL.

The LLM must output a JSON object that matches Plan.
We then validate and normalize it (qualify columns, clamp limits, etc.).
"""

from __future__ import annotations

from typing import List, Literal, Optional, Set, Tuple, Dict
from pydantic import BaseModel, Field, root_validator, validator # type: ignore

from .schema import (
    ALLOWED_VIEWS,
    ALLOWED_OPERATORS,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    columns_for,
    fq,
    is_allowed_column,
    is_allowed_join,
    list_views,
    pii_for,
)

# -------------------------
# Models
# -------------------------

Op = Literal["=", "<>", ">", ">=", "<", "<=", "ILIKE", "BETWEEN", "IN"]


class Filter(BaseModel):
    col: str
    op: Op
    val: object  # str | float | int | [start, end] for BETWEEN | list for IN


class Order(BaseModel):
    col: str
    dir: Literal["asc", "desc"] = "asc"


class Plan(BaseModel):
    view: Literal["customers", "policies", "claims"]
    select: List[str] = Field(default_factory=list)
    filters: List[Filter] = Field(default_factory=list)
    joins: List[str] = Field(default_factory=list)  # e.g., ["policies->customers","claims->policies"]
    group_by: List[str] = Field(default_factory=list)
    aggregations: List[str] = Field(default_factory=list)  # e.g., ["count(*) as cnt","sum(gross_premium) as premium"]
    order_by: List[Order] = Field(default_factory=list)
    limit: int = DEFAULT_LIMIT

    # Computed after validation
    qualified_select: List[str] = Field(default_factory=list)
    qualified_group_by: List[str] = Field(default_factory=list)
    qualified_order_by: List[Tuple[str, str]] = Field(default_factory=list)  # (col, dir)
    contains_pii: bool = False

    # ------------- Validators -------------

    @validator("limit", pre=True, always=True)
    def _clamp_limit(cls, v: int) -> int:
        try:
            v = int(v)
        except Exception:
            v = DEFAULT_LIMIT
        return min(max(v, 1), MAX_LIMIT)

    @validator("joins", each_item=True)
    def _check_join(cls, edge: str) -> str:
        if not is_allowed_join(edge):
            raise ValueError(f"Join not allowed: {edge}")
        return edge

    @validator("filters", each_item=True)
    def _check_filter_ops(cls, f: Filter) -> Filter:
        if f.op not in ALLOWED_OPERATORS:
            raise ValueError(f"Operator not allowed: {f.op}")
        return f

    @root_validator
    def _normalize_and_validate(cls, values):
        base: str = values.get("view")
        joins: List[str] = values.get("joins", [])
        select: List[str] = values.get("select", [])
        group_by: List[str] = values.get("group_by", [])
        order_by: List[Order] = values.get("order_by", [])
        filters: List[Filter] = values.get("filters", [])
        aggregations: List[str] = values.get("aggregations", [])

        # Determine reachable views
        reachable: Set[str] = {base}
        for j in joins:
            if j == "policies->customers":
                reachable.update({"policies", "customers"})
            elif j == "claims->policies":
                reachable.update({"claims", "policies"})

        # Helper to fully-qualify a column name
        def qualify(col: str) -> str:
            if "." in col:
                # already qualified; trust but verify
                if not is_allowed_column(col):
                    raise ValueError(f"Column not allowed: {col}")
                v, c = col.split(".", 1)
                if v not in reachable:
                    raise ValueError(f"Column {col} not reachable (missing join).")
                return col
            # Try to resolve unqualified among reachable views
            candidates = []
            for v in reachable:
                if col in columns_for(v):
                    candidates.append(f"{v}.{col}")
            if len(candidates) == 0:
                raise ValueError(f"Unknown column: {col}")
            if len(candidates) > 1:
                raise ValueError(f"Ambiguous column '{col}' across {candidates}; qualify it.")
            return candidates[0]

        # Qualify select / group_by / order_by / filters
        q_select = [qualify(c) for c in select]
        q_group = [qualify(c) for c in group_by]
        q_order = [(qualify(o.col), o.dir) for o in order_by]

        # Validate filters columns & normalize BETWEEN/IN values superficially
        for f in filters:
            _ = qualify(f.col)
            if f.op == "BETWEEN":
                if not (isinstance(f.val, list) and len(f.val) == 2):
                    raise ValueError("BETWEEN requires [start, end].")
            if f.op == "IN":
                if not (isinstance(f.val, list) and len(f.val) >= 1):
                    raise ValueError("IN requires a non-empty list.")

        # Aggregations whitelist: COUNT(*), MIN(col), MAX(col), SUM(col), AVG(col)
        def check_agg(a: str) -> None:
            low = a.lower().strip()
            if low.startswith("count("):
                return
            for fn in ("sum(", "avg(", "min(", "max("):
                if low.startswith(fn) and low.endswith(")") or " as " in low:
                    # Try to extract the column before any alias
                    inner = low.split(" as ")[0]
                    inner = inner[inner.find("(") + 1 : inner.rfind(")")]
                    _ = qualify(inner)
                    return
            # also allow "count(*) as something"
            if low == "count(*)" or low.startswith("count(*) "):
                return
            raise ValueError(f"Aggregation not allowed or unrecognized: {a}")

        for a in aggregations:
            check_agg(a)

        # PII detection
        pii_used = False
        for q in q_select + q_group + [c for c, _ in q_order] + [f.col if "." in f.col else qualify(f.col) for f in filters]:
            v, c = q.split(".", 1) if "." in q else (base, q)
            if c in pii_for(v):
                pii_used = True
                break

        # Save qualified artifacts
        values["qualified_select"] = q_select
        values["qualified_group_by"] = q_group
        values["qualified_order_by"] = q_order
        values["contains_pii"] = pii_used

        return values

    # Convenience: get all reachable views (base + joins)
    def reachable_views(self) -> Set[str]:
        r: Set[str] = {self.view}
        for j in self.joins:
            if j == "policies->customers":
                r.update({"policies", "customers"})
            elif j == "claims->policies":
                r.update({"claims", "policies"})
        return r
