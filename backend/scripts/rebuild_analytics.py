import os
from sqlalchemy import create_engine, text

DB = os.getenv("DATABASE_URL")
if not DB:
    raise SystemExit("DATABASE_URL is not set")

def run_sql_file(engine, path):
    with open(path, "r", encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        conn.execute(text(sql))

def main():
    engine = create_engine(DB)
    run_sql_file(engine, "/app/scripts/build_core.sql")
    run_sql_file(engine, "/app/scripts/build_marts.sql")
    print("Rebuilt core + marts ✅")

if __name__ == "__main__":
    main()
