"""
Streamlit frontend for the AI Financial Analyst.
Talks to the FastAPI backend over HTTP — run the backend first.
"""
import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Financial Analyst", page_icon="🏦", layout="wide")
st.title("🏦 AI Financial Analyst")
st.caption("Upload a financial report, ask questions. The agent decides whether "
           "to search the document, query the database, or run a calculation.")

# ---------- Sidebar: upload + status ----------
with st.sidebar:
    st.header("📄 Documents")
    uploaded = st.file_uploader("Upload annual report (.pdf or .txt)", type=["pdf", "txt"])
    if uploaded and st.button("Index document"):
        with st.spinner("Chunking and embedding..."):
            files = {"file": (uploaded.name, uploaded.getvalue())}
            r = requests.post(f"{BACKEND_URL}/upload", files=files)
        if r.ok:
            data = r.json()
            st.success(f"Indexed {data['chunks_indexed']} chunks from "
                       f"{data['pages']} page(s) of {data['filename']}.")
        else:
            st.error(r.text)

    try:
        docs = requests.get(f"{BACKEND_URL}/documents", timeout=5).json()["indexed_documents"]
        st.write("**Indexed:**", docs if docs else "none yet")
    except Exception:
        st.warning("Backend not reachable. Start it with:\n`uvicorn backend.app:app --reload`")

    st.divider()
    st.header("🗄️ Financial data (SQL)")
    try:
        companies = requests.get(f"{BACKEND_URL}/companies", timeout=5).json()["companies"]
        st.write("**Companies loaded:**")
        for c in companies:
            st.write(f"- {c}")
    except Exception:
        pass

    csv_file = st.file_uploader("Replace with your own CSV", type=["csv"], key="csv")
    if csv_file and st.button("Load CSV into database"):
        files = {"file": (csv_file.name, csv_file.getvalue())}
        r = requests.post(f"{BACKEND_URL}/ingest_csv", files=files)
        if r.ok:
            st.success(f"Loaded {r.json()['rows_loaded']} rows.")
        else:
            st.error(r.text)

# ---------- Main: chat ----------
if "history" not in st.session_state:
    st.session_state.history = []

for turn in st.session_state.history:
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        st.write(turn["answer"])
        if turn.get("sources"):
            with st.expander("Sources"):
                for s in turn["sources"]:
                    st.write(f"📄 {s['source_file']} — page {s['page']}")
        if turn.get("trace"):
            with st.expander("Agent activity"):
                for step in turn["trace"]:
                    st.write(step)

question = st.chat_input("Ask a financial question, e.g. 'Why did profit margin decline in 2025?'")
if question:
    st.session_state.history.append({"question": question, "answer": "…"})
    with st.chat_message("user"):
        st.write(question)
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                r = requests.post(f"{BACKEND_URL}/ask", json={"question": question}, timeout=60)
                r.raise_for_status()
                result = r.json()
            except Exception as e:
                result = {"answer": f"Error calling backend: {e}", "trace": [], "sources": []}

        st.write(result["answer"])
        if result.get("sources"):
            with st.expander("Sources"):
                for s in result["sources"]:
                    st.write(f"📄 {s['source_file']} — page {s['page']}")
        if result.get("trace"):
            with st.expander("Agent activity"):
                for step in result["trace"]:
                    st.write(step)

    st.session_state.history[-1] = {
        "question": question,
        "answer": result["answer"],
        "sources": result.get("sources", []),
        "trace": result.get("trace", []),
    }

st.divider()
st.subheader("🧮 Quick calculator")
col1, col2 = st.columns(2)
with col1:
    calc_name = st.selectbox(
        "Calculation",
        ["growth_rate", "profit_margin", "cagr", "debt_ratio", "current_ratio", "roi"],
    )
with col2:
    st.caption("Enter inputs as they map to backend/tools/calc_tool.py, e.g. "
               "growth_rate needs old_value and new_value.")

inputs_raw = st.text_input("Inputs (JSON)", value='{"old_value": 12400000, "new_value": 13100000}')
if st.button("Calculate"):
    import json
    try:
        inputs = json.loads(inputs_raw)
        r = requests.post(f"{BACKEND_URL}/calculate",
                           json={"calculation": calc_name, "inputs": inputs})
        r.raise_for_status()
        st.success(f"Result: {r.json()['result']}")
    except Exception as e:
        st.error(str(e))
