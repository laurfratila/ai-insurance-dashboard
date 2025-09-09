# backend/AI/LLM/dsl.py
"""
Plan (mini-DSL) for safe NL→SQL (Pydantic v2 compatible).

The LLM must output a JSON object that matches Plan.
We then validate and normalize it (qualify columns, clamp limits, etc.).
"""

from __future__ import annotations

from typing import List, Literal, Set, Tuple, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator # type: ignore

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

        def is_agg_expr(s: str) -> bool:
                s = s.lower().strip()
                return any(s.startswith(f) for f in ("sum(", "avg(", "min(", "max(", "count("))
        # Move aggregation expressions from select[] to aggregations[]
        agg_in_select = [s for s in select if is_agg_expr(s)]
        if agg_in_select:
            existing = set(a.lower().strip() for a in aggregations)
            for a in agg_in_select:
                if a.lower().strip() not in existing:
                    aggregations.append(a)
            select = [s for s in select if not is_agg_expr(s)]

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
        q_select = []
        for c in select:
            # Aggregation expressions should not be qualified
            if any(c.lower().strip().startswith(f) for f in ("sum(", "avg(", "min(", "max(", "count(")):
                q_select.append(c)  # leave as-is
            else:
                q_select.append(qualify(c))
        q_group = []
        for c in group_by:
            if any(c.lower().strip().startswith(f) for f in ("sum(", "avg(", "min(", "max(", "count(")):
                q_group.append(c)
            else:
                q_group.append(qualify(c))
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
            # Allow case-insensitive matching and handle aliasing like "SUM(x) as total"
            expr = a.strip()
            low = expr.lower()

            allowed_funcs = ("sum(", "avg(", "min(", "max(", "count(")

            if not any(f in low for f in allowed_funcs):
                raise ValueError(f"Aggregation function not allowed: {a}")

            # Split "sum(col) as alias"
            if " as " in low:
                expr_part, _alias = low.split(" as ", 1)
            else:
                expr_part = low

            # Check if it's properly formed like "sum(x)"
            if not any(expr_part.startswith(f) and expr_part.endswith(")") for f in allowed_funcs):
                raise ValueError(f"Malformed aggregation: {a}")

            # Extract the column between (...) — e.g., claims.paid
            inner = expr_part[expr_part.find("(") + 1 : expr_part.rfind(")")].strip()

            # Allow count(*) without qualification
            if inner == "*":
                return

            # Qualify and validate the column inside
            _ = qualify(inner)

        if aggregations:
            group_set = set(q_group)
            missing = [c for c in q_select if c not in group_set]
            if missing:
                raise ValueError(
                    f"When using aggregations, all selected columns must be in group_by. Missing: {missing}"
                )

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
            if is_agg_expr(qcol) or "." not in qcol:
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
    

    