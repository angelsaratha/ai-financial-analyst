# 🏦 AI Financial Analyst

An AI application that reads company financial documents (annual reports, balance
sheets, CSV/Excel transaction data) and answers analyst-style questions by
routing each question to the right tool — document retrieval (RAG), SQL, or
Python calculations — instead of asking an LLM to guess an answer.

> "I developed an AI financial analysis application that combines RAG, SQL
> querying and Python calculation tools. An agent determines which tool is
> appropriate for a user's question, retrieves evidence from financial
> documents, performs calculations when required, and generates a
> source-grounded response."

---

## 1. What it does

You upload:
- Annual / quarterly reports (PDF or TXT)
- A CSV of financial data (company, year, revenue, expenses, profit, assets, liabilities, cash_flow)

Then you can ask things like:

- "What caused the decrease in profit?" → **RAG** (searches the report text, returns an answer + source page)
- "What was ABC Corp's revenue in 2024?" → **SQL agent** (generates and runs SQL against the financial_data table)
- "Calculate the revenue growth between 2024 and 2025" → **Python calculation tool** (exact math, not LLM arithmetic)
- "Why did profit margin decrease in 2025?" → **Multi-step**: SQL for the numbers, Python for the ratio, RAG for the narrative explanation, combined into one answer

The key design idea: **the LLM never does the arithmetic and never answers from
memory** — it only decides which tool to call and writes up the result. This
is what separates this project from a plain "PDF chatbot."

## 2. Architecture

```
                 Streamlit Frontend
                        │
                        ▼
                 FastAPI Backend
                        │
                        ▼
                  Agent Router  ── decides which tool(s) a question needs
                        │
        ┌───────────────┼────────────────┐
        ▼               ▼                ▼
    RAG Tool         SQL Tool       Calculation Tool
   (FAISS vector    (SQLite via    (pure Python: growth,
    search over      LangChain      margin, CAGR, ratios)
    report chunks)   SQL chain)
        │
        ▼
  PDF → text → chunks → embeddings → FAISS index
```

Full technical breakdown, per-component design, and the ReAct / multi-agent
extension are in [`docs/PROJECT_DETAILS.md`](docs/PROJECT_DETAILS.md) (this is
the original project brief you were given, kept for reference).

## 3. Project structure

```
ai-financial-analyst/
├── backend/
│   ├── app.py                 # FastAPI app: /upload, /ask, /companies, /ingest_csv
│   ├── config.py              # settings, reads .env
│   ├── agent/
│   │   └── router.py          # decides RAG vs SQL vs calc vs combined
│   ├── tools/
│   │   ├── rag_tool.py        # retrieval + cited answer
│   │   ├── sql_tool.py        # NL → SQL → execute (LangChain SQL chain)
│   │   └── calc_tool.py       # growth, margin, CAGR, ratios — plain Python
│   ├── rag/
│   │   ├── pdf_loader.py      # PDF/TXT → raw text
│   │   ├── chunking.py        # text → overlapping chunks
│   │   └── vector_store.py    # embeddings + FAISS index, build/load/save
│   └── db/
│       ├── database.py        # SQLite engine/session
│       └── seed_db.py         # loads data/sample_financial_data.csv into SQLite
├── frontend/
│   └── streamlit_app.py       # upload + chat UI, calls the FastAPI backend
├── data/
│   ├── sample_financial_data.csv     # 5 companies x 5 years, for the SQL tool
│   └── documents/
│       └── sample_annual_report.txt  # demo report for the RAG tool
├── eval/
│   ├── test_questions.csv     # expected answers, for measuring accuracy
│   └── run_eval.py            # runs the test set against /ask and scores it
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── docs/
    └── PROJECT_DETAILS.md
```

## 4. Setup

```bash
cd ai-financial-analyst
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and add your OPENAI_API_KEY
```

## 5. Run it

**Backend (FastAPI):**
```bash
uvicorn backend.app:app --reload --port 8000
```
This seeds SQLite from `data/sample_financial_data.csv` on first run and
exposes docs at `http://localhost:8000/docs`.

**Frontend (Streamlit):**
```bash
streamlit run frontend/streamlit_app.py
```
Open the URL it prints, upload `data/documents/sample_annual_report.txt`
(or your own PDF), and start asking questions.

**Docker (both together):**
```bash
docker compose up --build
```

## 6. Try these questions against the sample data

| Question | Tool used |
|---|---|
| What was ABC Corp's revenue in 2024? | SQL |
| Show me the average revenue from 2021 to 2025 for ABC Corp | SQL |
| Calculate the revenue growth for ABC Corp between 2024 and 2025 | Calculation |
| What is ABC Corp's profit margin in 2025? | Calculation |
| Why did operating profit decline in 2025? | RAG (needs the report uploaded) |
| Why did ABC Corp's profit margin change in 2025? | SQL + Calculation + RAG combined |

## 7. Evaluation

`eval/test_questions.csv` has expected answers for a fixed question set.
`eval/run_eval.py` sends each question to the running backend and reports:
tool-selection accuracy, numeric answer correctness, and whether a citation
was returned for RAG questions. This is the piece to talk about in an
interview — it shows you're thinking about whether the system is *correct*,
not just whether it produces an answer.

```bash
python eval/run_eval.py
```

## 8. How this maps to an interview story

- **RAG**: PDF → chunking → embeddings → FAISS → retriever → cited answer
- **SQL agent / tool calling**: natural language → generated SQL → executed against SQLite
- **Python tool use**: growth, margin, CAGR, current ratio, debt ratio computed exactly, not guessed by the LLM
- **Agent routing**: one function decides, per question, which of the three tools (or which combination) to call
- **Evaluation**: a fixed test set with expected answers, scored automatically

## 9. Where to go next (roadmap from the original brief)

1. Swap the router for a real LangGraph ReAct agent with a visible tool trace
2. Add a Supervisor → {RAG, SQL, Calculation} → Analyst multi-agent pipeline
3. Add company-comparison and multi-document support
4. Replace FAISS with Chroma/Qdrant and SQLite with Postgres for production
5. Add auth, logging, and a proper React frontend in place of Streamlit
6. Add hallucination detection to the eval harness

See `docs/PROJECT_DETAILS.md` for the full original design notes on all of these.
