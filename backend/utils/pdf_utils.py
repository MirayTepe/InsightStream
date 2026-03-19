from typing import Tuple, List

import fitz  # PyMuPDF


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, int]:
    """
    Extract text from a PDF file using PyMuPDF.

    Returns:
        A tuple of (full_text, num_pages).
    """
    # `fitz.open` can open a document from bytes with the `stream` argument.
    doc = fitz.open(stream=file_bytes, filetype="pdf")
    texts: List[str] = []
    for page in doc:
        texts.append(page.get_text())
    full_text = "\n".join(texts)
    num_pages = len(doc)
    doc.close()
    return full_text, num_pages


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    """
    Very simple text chunking function.

    It splits the text into chunks of up to `max_chars` characters.
    This is enough to get a RAG-ready structure without complex logic.
    """
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    length = len(text)

    while start < length:
        end = min(start + max_chars, length)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start = end

    return chunks

