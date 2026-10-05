# Original Project Brief — AI Financial Analyst

*(This is the full design document the project was scoped from, kept here for reference and interview prep.)*

## 1. What is it?

An AI application where a user uploads company financial documents and/or
financial datasets, and the application acts like an intelligent financial
analyst — deciding whether a question needs RAG, SQL, a Python calculation,
document comparison, or chart generation, rather than answering everything
from the LLM alone.

## 2. Where RAG is used

```
PDF → Extract text → Chunk documents → Create embeddings → Vector database
    → Retriever → Relevant financial information → LLM → Answer + citation
```

## 3. Where SQL is used

Example table `financial_data(company, year, revenue, expenses, profit,
assets, liabilities, cash_flow)`. A question like "What was the revenue in
2024?" becomes:

```sql
SELECT revenue FROM financial_data WHERE company = 'ABC' AND year = 2024;
```

## 4. Where Python is used

Calculations the LLM should not "guess" at: revenue growth, profit margin,
ROI, CAGR, debt ratio, current ratio — implemented as plain Python functions
the agent calls as tools.

## 5. ReAct agent (future direction)

```
Thought → Action → Observation → Thought → Action → Observation → Final Answer
```
UI shows a safe activity trace instead of raw chain-of-thought, e.g.:
```
✓ Retrieved financial data
✓ Calculated profit margin
✓ Searched annual report
✓ Found supporting evidence
✓ Generated answer
```

## 6. Multi-agent version (future direction)

```
Supervisor Agent → {RAG Agent, SQL Agent, Calculation Agent} → Analyst Agent → Final Response
```

## 7. Feature tiers

**Basic**: PDF/CSV upload, document RAG, chat interface, citations, financial
calculations, SQL querying.

**Intermediate**: multiple documents, company comparison, financial ratios,
charts, Excel support, conversation memory, metadata filtering.

**Advanced**: ReAct agent, multiple specialized agents, LangGraph workflow,
automatic report generation, trend analysis, evaluation system, hallucination
detection, Docker, auth, logging/monitoring.

## 8. Technology stack

| Component | Technology |
|---|---|
| Frontend | React (or Streamlit for a faster build) |
| Backend | FastAPI + Python |
| LLM framework | LangChain |
| Agent workflow | LangGraph (future) |
| Agent style | ReAct / tool-calling |
| RAG | LangChain retrieval |
| Embeddings | OpenAI (or another embedding model) |
| Vector DB | FAISS initially, later Chroma/Qdrant |
| Database | SQLite → PostgreSQL |
| Data processing | Pandas |
| PDF processing | PyMuPDF |
| Charts | Recharts / Plotly |
| Containerization | Docker |

## 9. Evaluation

Build a fixed test set of question → expected-answer pairs and measure:
retrieval accuracy, answer correctness, citation accuracy, response latency,
tool-selection accuracy, hallucination rate. This is what turns the project
from "a chatbot" into "a system I evaluated."

## 10. Interview framing

Don't say: *"I built a chatbot using LangChain."*

Say: *"I developed an AI financial analysis application that combines RAG,
SQL querying and Python calculation tools. An agent determines which tool is
appropriate for a user's question, retrieves evidence from financial
documents, performs calculations when required, and generates a
source-grounded response through a web interface."*

## 11. Learning roadmap this project was designed around

1. Python + financial data (Pandas, SQL, financial calculations)
2. RAG (PDF loading, chunking, embeddings, FAISS, retrieval, citations)
3. LangChain (prompts, chains, retrievers, tools, structured output)
4. Agents (tool calling, ReAct concepts, agent routing, LangGraph)
5. Application (FastAPI, frontend, database, authentication)
6. Production (evaluation, logging, Docker, deployment)
