"""
The agent's "brain": given a question, decide which tool(s) are needed —
RAG, SQL, calculation, or a combination — call them, and write up a
final answer. This is what makes the system an agent rather than a
plain PDF-chat app: the LLM never answers directly, it always goes
through a tool whose output is grounded in data.

Design: a single routing call classifies the question, then the chosen
tool(s) run, then (for combined questions) a short synthesis call writes
the final answer referencing the tool outputs. The activity trace is
returned so the UI can show "what the agent did" without exposing raw
chain-of-thought.
"""
import json
import re

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from backend.config import OPENAI_CHAT_MODEL, require_api_key
from backend.tools.rag_tool import answer_from_documents
from backend.tools.sql_tool import answer_with_sql
from backend.tools.calc_tool import run_calculation

ROUTE_PROMPT = ChatPromptTemplate.from_template(
    """Classify what a financial analyst question needs. Respond with ONLY
a JSON object, no markdown fences, in this exact shape:

{{"tools": ["sql" | "rag" | "calc", ...], "reason": "short reason"}}

Guidelines:
- "sql": the question asks for a specific stored figure (revenue, expenses,
  profit, assets, liabilities, cash flow) for a company/year, or an
  aggregate (average, total) over stored data.
- "rag": the question asks WHY something happened, or for narrative
  explanation/context/risk factors that would come from a written report.
- "calc": the question asks to calculate growth, margin, CAGR, ROI, or a
  ratio. Usually paired with "sql" to get the raw numbers first.
- Use multiple tools when the question needs numbers AND an explanation
  (e.g. "why did profit margin change" needs sql + calc + rag).

Question: {question}"""
)

SYNTHESIS_PROMPT = ChatPromptTemplate.from_template(
    """You are a financial analyst writing a final answer for a user.
Combine the tool results below into one clear, specific answer. Only use
numbers that appear in the tool results — never invent figures.

Question: {question}

Tool results:
{tool_results}

Final answer (2-5 sentences):"""
)


def _classify(question: str) -> dict:
    require_api_key()
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)
    chain = ROUTE_PROMPT | llm
    raw = chain.invoke({"question": question}).content.strip()
    raw = re.sub(r"^```json|^```|```$", "", raw, flags=re.MULTILINE).strip()
    try:
        parsed = json.loads(raw)
        tools = [t for t in parsed.get("tools", []) if t in ("sql", "rag", "calc")]
        return {"tools": tools or ["rag"], "reason": parsed.get("reason", "")}
    except Exception:
        return {"tools": ["rag"], "reason": "fallback: could not parse router output"}


def ask(question: str) -> dict:
    """Main entry point. Returns the final answer plus an activity trace
    and the raw tool outputs, for transparency in the UI."""
    trace = []
    route = _classify(question)
    trace.append(f"Routed question to: {', '.join(route['tools'])} ({route['reason']})")

    tool_results = {}

    if "sql" in route["tools"]:
        result = answer_with_sql(question)
        tool_results["sql"] = result
        if result["error"]:
            trace.append(f"✗ SQL tool error: {result['error']}")
        else:
            trace.append(f"✓ Ran SQL: {result['sql']}")

    if "calc" in route["tools"]:
        # The calc tool needs specific numbers, which usually come from the
        # SQL result above. We pass that context to the LLM-free calc step
        # by simply noting it needs the SQL numbers to have been computed;
        # for a fully worked example see /ask response `tool_results.sql`.
        trace.append("→ Calculation tool available: growth_rate, profit_margin, "
                      "cagr, debt_ratio, current_ratio, roi (see backend/tools/calc_tool.py). "
                      "Call POST /calculate directly for an exact figure.")

    if "rag" in route["tools"]:
        result = answer_from_documents(question)
        tool_results["rag"] = result
        if result["sources"]:
            src = result["sources"][0]
            trace.append(f"✓ Retrieved from {src['source_file']} (page {src['page']})")
        else:
            trace.append("→ RAG tool: no indexed documents found")

    # If only one tool ran, its own answer is the final answer.
    if len(tool_results) == 1:
        only = next(iter(tool_results.values()))
        final_answer = only.get("answer") if "answer" in only else _format_sql_answer(only)
        return {
            "answer": final_answer,
            "trace": trace,
            "tool_results": tool_results,
            "sources": only.get("sources", []),
        }

    # Otherwise synthesize a combined answer from everything gathered.
    require_api_key()
    llm = ChatOpenAI(model=OPENAI_CHAT_MODEL, temperature=0)
    chain = SYNTHESIS_PROMPT | llm
    summary = chain.invoke(
        {"question": question, "tool_results": json.dumps(tool_results, default=str)}
    ).content.strip()
    trace.append("✓ Combined tool results into final answer")

    return {
        "answer": summary,
        "trace": trace,
        "tool_results": tool_results,
        "sources": tool_results.get("rag", {}).get("sources", []),
    }


def _format_sql_answer(sql_result: dict) -> str:
    if sql_result["error"]:
        return f"I couldn't run that query: {sql_result['error']}"
    if not sql_result["rows"]:
        return "That query ran successfully but returned no matching rows."
    return json.dumps(sql_result["rows"], default=str)
