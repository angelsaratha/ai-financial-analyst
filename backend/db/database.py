"""
SQLite engine + session used by the SQL tool. Also exposes a helper to
run a raw SQL string and get back rows, which is what the SQL tool needs
after the LLM generates a SELECT statement.
"""
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from backend.config import DATABASE_URL

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

FINANCIAL_TABLE_SCHEMA = """
Table: financial_data
Columns:
  company     TEXT   -- company name, e.g. 'ABC Corp'
  year        INTEGER
  revenue     REAL
  expenses    REAL
  profit      REAL
  assets      REAL
  liabilities REAL
  cash_flow   REAL
"""


def run_sql(query: str):
    """Execute a read-only SQL query and return (columns, rows). Blocks
    anything that isn't a SELECT, since the LLM only ever needs to read."""
    stripped = query.strip().lower()
    if not stripped.startswith("select"):
        raise ValueError("Only SELECT statements are allowed.")
    with engine.connect() as conn:
        result = conn.execute(text(query))
        columns = list(result.keys())
        rows = [dict(zip(columns, row)) for row in result.fetchall()]
    return columns, rows


def list_companies():
    _, rows = run_sql("SELECT DISTINCT company FROM financial_data ORDER BY company;")
    return [r["company"] for r in rows]
