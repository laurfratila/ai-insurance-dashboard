import argparse, os
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

TABLES = [
    "customers","policies","coverages","properties",
    "rental_units","vehicles","claims","loss_events","geo_features",
]

DATE_COLS = {
    "policies": ["start_date","end_date"],
    "claims": ["loss_date","report_date","close_date"],
}

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--path", required=True, help="Folder with CSVs (container path)")
    p.add_argument("--schema", default="raw", help="Target schema name (default: raw)")
    p.add_argument("--replace", action="store_true", help="Replace tables instead of append")
    args = p.parse_args()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise SystemExit("DATABASE_URL not set")

    engine = create_engine(db_url)
    base = Path(args.path)
    mode = "replace" if args.replace else "append"

    with engine.begin() as conn:
        # set schema for this session
        conn.exec_driver_sql(f"SET search_path TO {args.schema}, public;")

        for name in TABLES:
            f = base / f"{name}.csv"
            if not f.exists():
                print(f"skip: {f.name} not found"); continue
            dates = DATE_COLS.get(name, [])
            print(f"→ loading {name} from {f.name} (parse_dates={dates})")
            df = pd.read_csv(f, parse_dates=dates)
            df.columns = [c.strip().lower() for c in df.columns]
            df.to_sql(name, conn, if_exists=mode, index=False)
            print(f"   done: {name} ({len(df)} rows)")
    print("All done ✅")

if __name__ == "__main__":
    main()
