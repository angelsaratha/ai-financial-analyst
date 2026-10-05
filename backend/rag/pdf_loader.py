"""
Turns an uploaded PDF or TXT financial document into plain text, one
block per page (page number kept so citations can point back to it).
"""
import os
from typing import List, Tuple

import fitz  # PyMuPDF


def load_document(file_path: str) -> List[Tuple[int, str]]:
    """Returns a list of (page_number, page_text). Page numbers start at 1.
    For .txt files, the whole file is treated as a single 'page'."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        pages = []
        doc = fitz.open(file_path)
        for i, page in enumerate(doc):
            text = page.get_text("text")
            if text.strip():
                pages.append((i + 1, text))
        doc.close()
        return pages

    if ext in (".txt", ".md"):
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return [(1, f.read())]

    raise ValueError(f"Unsupported file type: {ext}. Use .pdf or .txt")
