from typing import List, Tuple

import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.core.exceptions import PDFProcessingError


class PDFService:
    def __init__(self, chunk_size: int = 800, chunk_overlap: int = 200) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text(self, file_bytes: bytes) -> Tuple[str, int]:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
        except Exception as exc:  # pragma: no cover - defensive
            raise PDFProcessingError(f"Failed to open PDF: {exc}") from exc

        texts: List[str] = []
        for page in doc:
            texts.append(page.get_text())
        num_pages = len(doc)
        doc.close()

        full_text = "\n".join(texts).strip()
        if not full_text:
            raise PDFProcessingError("No text found in PDF.")
        return full_text, num_pages

    def chunk_text(self, text: str) -> List[str]:
        return self.splitter.split_text(text)

