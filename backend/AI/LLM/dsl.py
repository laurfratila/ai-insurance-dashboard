# backend/AI/LLM/dsl.py
"""
Plan (mini-DSL) for safe NL→SQL (Pydantic v2 compatible).

The LLM must output a JSON object that matches Plan.
We then validate and normalize it (qualify columns, clamp limits, etc.).
"""

from __future__ import annotations

from typing import List, Literal, Set, Tuple, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator

from .schema import (
    ALLOWED_OPERATORS,
    DEFAULT_LIMIT,
    MAX_LIMIT,
    columns_for,
    is_allowed_column,
    is_allowed_join,
    pii_for,
)

# -------------------------
# Models
# -------------------------

Op = Literal["=", "<>", ">", ">=", "<", "<=", "ILIKE", "BETWEEN", "IN"]


class Filter(BaseModel):
    col: str
    op: Op
    val: Any  # str | float | int | [start, end] for BETWEEN | list for IN


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

    # ------------- Validators (Pydantic v2) -------------

    @field_validator("limit", mode="before")
    @classmethod
    def _clamp_limit(cls, v: Any) -> int:
        try:
            v = int(v)
        except Exception:
            v = DEFAULT_LIMIT
        return min(max(v, 1), MAX_LIMIT)

    @field_validator("joins", mode="before")
    @classmethod
    def _validate_joins(cls, joins: Any) -> Any:
        if joins is None:
            return []
        for edge in joins:
            if not is_allowed_join(edge):
                raise ValueError(f"Join not allowed: {edge}")
        return joins

    @field_validator("filters", mode="before")
    @classmethod
    def _validate_filters_ops(cls, filters: Any) -> Any:
        if filters is None:
            return []
        for f in filters:
            if f.get("op") not in ALLOWED_OPERATORS:
                raise ValueError(f"Operator not allowed: {f.get('op')}")
        return filters

    @model_validator(mode="after")
    def _normalize_and_validate(self) -> "Plan":
        base: str = self.view
        joins: List[str] = self.joins or []
        select: List[str] = self.select or []
        group_by: List[str] = self.group_by or []
        order_by: List[Order] = self.order_by or []
        filters: List[Filter] = self.filters or []
        aggregations: List[str] = self.aggregations or []

        # Collect aggregation aliases like "... as premium"
        def agg_aliases(aggs: list[str]) -> set[str]:
            aliases = set()
            for a in aggs:
                low = a.lower()
                if " as " in low:
                    aliases.add(low.split(" as ", 1)[1].strip())
            return aliases

        aliases = agg_aliases(aggregations)

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
                v, _ = col.split(".", 1)
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
        q_order = []
        for o in order_by:
            col = o.col.strip()
            # Allow ORDER BY on aggregation alias (leave as-is, unqualified)
            if "." not in col and col.lower() in aliases:
                q_order.append((col, o.dir))
            else:
                q_order.append((qualify(col), o.dir))

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
                # allow count(*), count(col) as alias, etc.
                return
            for fn in ("sum(", "avg(", "min(", "max("):
                if low.startswith(fn):
                    # Extract inner column up to ')' (before optional ' as ')
                    inner_part = low.split(" as ")[0]
                    inner = inner_part[inner_part.find("(") + 1 : inner_part.rfind(")")]
                    # Qualify to ensure it's allowed/reachable
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

        # Build a list of qualified columns appearing in filters
        qualified_filter_cols: list[str] = []
        for f in filters:
            qualified_filter_cols.append(f.col if "." in f.col else qualify(f.col))

        # Consider: select, group_by, order_by (may contain aliases), and filters
        scan_cols: list[str] = []
        scan_cols += q_select
        scan_cols += q_group
        scan_cols += [c for c, _ in q_order]         # may include aliases (no dot)
        scan_cols += qualified_filter_cols

        for qcol in scan_cols:
            if "." not in qcol:
                # Unqualified name (likely an aggregation alias like "premium") — skip
                continue
            v, c = qcol.split(".", 1)
            if c in pii_for(v):
                pii_used = True
                break

        # Save qualified artifacts
        self.qualified_select = q_select
        self.qualified_group_by = q_group
        self.qualified_order_by = q_order
        self.contains_pii = pii_used
        return self

    # Convenience: get all reachable views (base + joins)
    def reachable_views(self) -> Set[str]:
        r: Set[str] = {self.view}
        for j in self.joins:
            if j == "policies->customers":
                r.update({"policies", "customers"})
            elif j == "claims->policies":
                r.update({"claims", "policies"})
        return r
    

    