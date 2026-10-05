"""
Splits page text into overlapping chunks small enough to embed well and
large enough to keep an answer's supporting sentences together.
"""
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class Chunk:
    text: str
    source_file: str
    page: int
    chunk_id: str


def chunk_pages(
    pages: List[Tuple[int, str]],
    source_file: str,
    chunk_size: int = 900,
    overlap: int = 150,
) -> List[Chunk]:
    chunks = []
    counter = 0
    for page_num, text in pages:
        text = " ".join(text.split())  # normalize whitespace
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            piece = text[start:end]
            if piece.strip():
                counter += 1
                chunks.append(
                    Chunk(
                        text=piece,
                        source_file=source_file,
                        page=page_num,
                        chunk_id=f"{source_file}-p{page_num}-{counter}",
                    )
                )
            if end == len(text):
                break
            start = end - overlap
    return chunks
