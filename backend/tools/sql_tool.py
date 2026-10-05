"""
SQL tool: turns a natural-language financial question into a SELECT
statement against the financial_data table, executes it, and returns
both the SQL used and the result — never a number the LLM invented.
"""
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import OPENAI_CHAT_MODEL, require_api_key
from backend.db.database import run_sql, FINANCIAL_TABLE_SCHEMA

SQL_PROMPT = ChatPromptTemplate.from_template(
    """You write SQLite SELECT queries. Given the table schema and a
question, output ONLY the SQL query — no explanation, no markdown fences,
no semicolon-separated multiple statements.

Schema:
{schema}

Question: {question}

SQL query:"""
)


def _extract_sql(raw: str) -> str:
    sql = raw.strip()
    sql = re.sub(r"^```sql|^```|```$", "", sql, flags=re.MULTILINE).strip()
    return sql.split(";")[0].strip()


def answer_with_sql(question: str) -> dict:
    require_api_key()
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)
    chain = SQL_PROMPT | llm
    raw = chain.invoke({"schema": FINANCIAL_TABLE_SCHEMA, "question": question}).content
    sql = _extract_sql(raw)

    try:
        columns, rows = run_sql(sql)
    except Exception as e:
        return {"sql": sql, "columns": [], "rows": [], "error": str(e)}

    return {"sql": sql, "columns": columns, "rows": rows, "error": None}
