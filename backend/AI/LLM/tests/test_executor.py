from backend.AI.LLM.executor import run_query, make_citations

class DummyConn:
    """Minimal SQLAlchemy-like connection returning mappings().all() rows."""
    class DummyResult:
        def __init__(self, rows):
            self._rows = rows
        def mappings(self):
            class M:
                def __init__(self, rows): self._rows = rows
                def all(self): 
                    # mimic RowMapping dicts
                    return [type("R", (), {"_mapping": r}) for r in self._rows]
            return M(self._rows)

    def __init__(self, rows):
        self._rows = rows
    def execute(self, *_args, **_kwargs):
        return self.DummyResult(self._rows)

def test_run_query_masks_pii():
    rows = [
        {"customers.email": "a@b.com", "customers.phone": "123", "customers.city": "Cluj"},
    ]
    conn = DummyConn(rows)
    out = run_query(conn, "SELECT 1", {}, allow_pii=False)
    assert out[0]["customers.email"] == "[redacted]"
    assert out[0]["customers.phone"] == "[redacted]"
    assert out[0]["customers.city"] == "Cluj"

def test_citations_count():
    cites = make_citations("SELECT 1", {"p0": "x"})
    assert len(cites) >= 2
    ids = {c["id"] for c in cites}
    assert "sql-compiled" in ids
