"""
Loads data/sample_financial_data.csv (or any CSV with the same columns)
into the financial_data SQLite table. Safe to call repeatedly — it
replaces the table each time.
"""
import pandas as pd

from backend.config import SAMPLE_CSV_PATH
from backend.db.database import engine


def seed_from_csv(csv_path: str = SAMPLE_CSV_PATH, table_name: str = "financial_data"):
    df = pd.read_csv(csv_path)

    expected = {"company", "year", "revenue", "expenses", "profit",
                "assets", "liabilities", "cash_flow"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing required columns: {missing}")

    df.to_sql(table_name, engine, if_exists="replace", index=False)
    return len(df)


if __name__ == "__main__":
    n = seed_from_csv()
    print(f"Seeded {n} rows into financial_data.")
