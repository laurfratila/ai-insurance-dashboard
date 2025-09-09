from backend.AI.LLM.dsl import Plan, Filter, Order
from backend.AI.LLM.compiler import compile_sql

def test_compile_sql_basic_select_where_order_limit():
    plan = Plan(
        view="policies",
        select=["policies.product_type", "policies.status"],
        filters=[
            Filter(col="policies.status", op="=", val="active"),
            Filter(col="customers.city", op="ILIKE", val="Cluj%"),
        ],
        joins=["policies->customers"],
        order_by=[Order(col="policies.product_type", dir="asc")],
        limit=25,
    )
    sql, params = compile_sql(plan)
    assert "FROM core.\"policies\" policies" in sql
    assert "JOIN core.\"customers\" customers" in sql
    assert "WHERE policies.status = :p0 AND customers.city ILIKE :p1" in sql
    assert "ORDER BY policies.product_type ASC" in sql
    assert "LIMIT 25" in sql
    assert params == {"p0": "active", "p1": "Cluj%"}
