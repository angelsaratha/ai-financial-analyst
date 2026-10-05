"""
FastAPI backend for the AI Financial Analyst.

Endpoints:
  GET  /health           - liveness check
  POST /upload            - upload a PDF/TXT report, chunks + indexes it (RAG)
  POST /ingest_csv         - (re)load a financial CSV into SQLite (SQL tool)
  GET  /companies          - list companies currently in the SQL table
  GET  /documents          - list documents currently indexed for RAG
  POST /ask                - main endpoint: ask a question, agent routes it
  POST /calculate           - call a specific financial calculation directly
"""
import os
import shutil

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.config import DOCUMENTS_DIR, SAMPLE_CSV_PATH
from backend.db.seed_db import seed_from_csv
from backend.db.database import list_companies
from backend.rag.pdf_loader import load_document
from backend.rag.chunking import chunk_pages
from backend.rag.vector_store import build_or_update_index, indexed_documents
from backend.agent.router import ask as agent_ask
from backend.tools.calc_tool import run_calculation

app = FastAPI(title="AI Financial Analyst", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    # Seed the SQL table from the sample CSV so the app is usable immediately.
    if os.path.exists(SAMPLE_CSV_PATH):
        try:
            seed_from_csv(SAMPLE_CSV_PATH)
        except Exception as e:
            print(f"Warning: could not seed sample data on startup: {e}")


@app.get("/health")
def health():
    return {"status": "ok"}


class AskRequest(BaseModel):
    question: str


@app.post("/ask")
def ask(req: AskRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(400, "question cannot be empty")
    try:
        return agent_ask(req.question)
    except RuntimeError as e:
        raise HTTPException(400, str(e))


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in (".pdf", ".txt", ".md"):
        raise HTTPException(400, "Only .pdf and .txt files are supported.")

    dest_path = os.path.join(DOCUMENTS_DIR, file.filename)
    with open(dest_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    pages = load_document(dest_path)
    chunks = chunk_pages(pages, source_file=file.filename)
    try:
        n_added = build_or_update_index(chunks)
    except RuntimeError as e:
        raise HTTPException(400, str(e))

    return {"filename": file.filename, "pages": len(pages), "chunks_indexed": n_added}


@app.post("/ingest_csv")
async def ingest_csv(file: UploadFile = File(...)):
    tmp_path = os.path.join(DOCUMENTS_DIR, f"_tmp_{file.filename}")
    with open(tmp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    try:
        n_rows = seed_from_csv(tmp_path)
    except Exception as e:
        raise HTTPException(400, str(e))
    finally:
        os.remove(tmp_path)
    return {"rows_loaded": n_rows}


@app.get("/companies")
def companies():
    return {"companies": list_companies()}


@app.get("/documents")
def documents():
    return {"indexed_documents": indexed_documents()}


class CalculateRequest(BaseModel):
    calculation: str
    inputs: dict


@app.post("/calculate")
def calculate(req: CalculateRequest):
    try:
        result = run_calculation(req.calculation, **req.inputs)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"calculation": req.calculation, "inputs": req.inputs, "result": result}
