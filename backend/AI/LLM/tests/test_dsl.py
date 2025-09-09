from backend.AI.LLM.dsl import Plan, Filter

def test_plan_validates_and_qualifies_columns():
    plan = Plan(
        view="policies",
        select=["product_type", "channel", "status"],
        filters=[Filter(col="customers.city", op="ILIKE", val="Cluj%")],
        joins=["policies->customers"],
        group_by=["product_type", "channel", "status"],
        aggregations=["count(*) as policies", "sum(gross_premium) as premium"],
        order_by=[],
        limit=50,
    )
    # Columns should be qualified after validation
    assert all("." in c for c in plan.qualified_select)
    assert all("." in c for c in plan.qualified_group_by)
    # No PII in selection, so contains_pii False
    assert plan.contains_pii is False

def test_ambiguous_column_raises():
    # 'status' exists in policies and claims; without join, it's OK here (policies)
    _ = Plan(
        view="policies",
        select=["status"],
        filters=[],
        joins=[],
    )
    # With join to claims, using bare 'status' should be ambiguous and flagged
    try:
        Plan(
            view="claims",
            select=["status"],
            joins=["claims->policies"],
        )
        raised = False
    except ValueError:
        raised = True
    assert raised, "Ambiguous bare column should raise when multiple sources reachable"
